#!/usr/bin/env python3
"""Prueba integral no destructiva del prototipo: genera una orden y un pago de demostracion.

Uso: COMANDAPRO_DEMO_PASSWORD='...' python3 scripts/smoke_render_roles.py
No requiere contrasena de administrador. Modifica datos de demostracion en la nube.
"""
from __future__ import annotations
import json
import os
import ssl
import sys
import urllib.error
import urllib.request

BASE = os.getenv("COMANDAPRO_URL", "https://comandapro-demo.onrender.com").rstrip("/")
PASSWORD = os.getenv("COMANDAPRO_DEMO_PASSWORD", "")
if not PASSWORD:
    sys.exit("Configura COMANDAPRO_DEMO_PASSWORD; no pongas la clave en argumentos ni logs")

def request(method: str, path: str, token: str | None = None, data=None, expected=(200,)):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = None
    if data is not None:
        payload = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, payload, headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=65) as response:
            code = response.status
            body = response.read()
    except urllib.error.HTTPError as err:
        code = err.code
        body = err.read()
    if code not in expected:
        raise AssertionError(f"{method} {path}: se esperaba {expected}, resultado {code}, cuerpo {body[:220]!r}")
    return json.loads(body) if body else None, code

def login(role: str):
    email = f"{role.lower()}@comandapro.local"
    data, _ = request("POST", "/api/auth/login", data={"correo": email, "password": PASSWORD})
    token = data["access_token"]
    me, _ = request("GET", "/api/auth/me", token)
    assert me["rol"] == role, f"Rol de {email} incorrecto"
    print(f"OK inicio de sesion: {role}")
    return token

def run():
    if not BASE.startswith("https://"):
        sys.exit("La prueba remota exige una URL HTTPS")
    health, _ = request("GET", "/api/health")
    assert health["estado"] == "ok" and health["baseDatos"] == "conectada", health
    print("OK FastAPI y PostgreSQL")

    mesero = login("MESERO")
    cocina = login("COCINA")
    cajero = login("CAJERO")
    _, code = request("GET", "/api/admin/usuarios", mesero, expected=(403,))
    assert code == 403
    _, code = request("GET", "/api/inventario", cocina, expected=(403,))
    assert code == 403
    print("OK aislamiento de permisos por rol")

    products, _ = request("GET", "/api/productos", mesero)
    product = next(p for p in products if p["nombre"] == "Hamburguesa Comanda")
    mesas, _ = request("GET", "/api/mesas", mesero)
    mesa = next(m for m in mesas if m["estado"] == "LIBRE")
    create, _ = request("POST", "/api/ordenes", mesero, {
        "mesa_id": mesa["id"], "detalles": [{"producto_id": product["id"], "cantidad": 1,
        "notas": "Validacion automatizada Render"}],
    }, expected=(201,))
    order_id = create["id"]
    detail = create["detalles"][0]["id"]
    print(f"OK mesero: orden #{order_id} creada, mesa {mesa['numero']}")

    sent, _ = request("POST", f"/api/ordenes/{order_id}/enviar-cocina", mesero)
    assert sent["estado"] == "EN_COCINA"
    kitchen_orders, _ = request("GET", "/api/cocina/ordenes", cocina)
    assert order_id in [o["id"] for o in kitchen_orders]
    print("OK pedido enviado y recibido por cocina")

    preparing, _ = request("PATCH", f"/api/cocina/detalles/{detail}/estado", cocina, {"estado": "PREPARANDO"})
    ready, _ = request("PATCH", f"/api/cocina/detalles/{detail}/estado", cocina, {"estado": "LISTO"})
    served, _ = request("POST", f"/api/ordenes/{order_id}/servir", mesero)
    assert served["estado"] == "SERVIDA"
    print("OK cocina preparo, entrego, mesero sirvio")

    pending, _ = request("GET", "/api/pagos/ordenes-abiertas", cajero)
    assert order_id in [o["id"] for o in pending]
    total_cents = round(float(served["total"]) * 100)
    partial_cents = total_cents // 2
    first, _ = request("POST", f"/api/ordenes/{order_id}/pagos", cajero,
        {"metodo": "EFECTIVO", "monto": round(partial_cents / 100, 2)}, expected=(201,))
    assert first["cerrada"] is False
    second, _ = request("POST", f"/api/ordenes/{order_id}/pagos", cajero,
        {"metodo": "TARJETA", "monto": round((total_cents - partial_cents) / 100, 2)}, expected=(201,))
    assert second["cerrada"] is True and second["orden"]["estado"] == "PAGADA"
    print("OK cajero cobro dividido y orden pagada")

    final_mesas, _ = request("GET", "/api/mesas", mesero)
    assert next(m for m in final_mesas if m["id"] == mesa["id"])["estado"] == "LIBRE"
    report, _ = request("GET", "/api/reportes/ventas", cajero)
    assert any(float(x["ventas"]) >= float(served["total"]) for x in report)
    print("OK mesa liberada y venta registrada")
    print("RESULTADO: EXITO - flujo por roles completado en Render.")

if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"RESULTADO: FALLO - {exc}", file=sys.stderr)
        sys.exit(1)
