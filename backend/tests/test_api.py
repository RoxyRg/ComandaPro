from fastapi.testclient import TestClient
from sqlalchemy import func

from app.main import create_app
from app.models import DetalleOrden, Inventario, Mesa, Orden, Pago, Usuario

ADMIN_EMAIL = "admin@comandapro.local"
ADMIN_PASSWORD = "CambiaComanda2026!"


def make_client():
    return TestClient(create_app("sqlite://", initialize=True))


def login(client, correo=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    response = client.post("/api/auth/login", json={"correo": correo, "password": password})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["expires_in"] == 900
    return data["access_token"]


def test_health_and_demo_seed():
    with make_client() as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["estado"] == "ok"
        token = login(client)
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["rol"] == "ADMIN"
        assert len(client.get("/api/admin/sucursales", headers={"Authorization": f"Bearer {token}"}).json()) == 3


def test_refresh_rotates_and_revokes_old_token():
    with make_client() as client:
        login(client)
        old = client.cookies.get("comandapro_refresh")
        assert old
        rotated = client.post("/api/auth/refresh")
        assert rotated.status_code == 200, rotated.text
        new = client.cookies.get("comandapro_refresh")
        assert new and new != old
        reused = client.post("/api/auth/refresh", cookies={"comandapro_refresh": old})
        assert reused.status_code == 401


def test_password_change_requires_current_password_and_revokes_refresh_tokens():
    with make_client() as client:
        token = login(client)
        headers = {"Authorization": f"Bearer {token}"}
        old_refresh = client.cookies.get("comandapro_refresh")
        assert old_refresh
        wrong = client.post("/api/auth/change-password", headers=headers, json={
            "actual": "contraseña-equivocada", "nueva": "NuevaClaveSegura2026*",
        })
        assert wrong.status_code == 401
        weak = client.post("/api/auth/change-password", headers=headers, json={
            "actual": ADMIN_PASSWORD, "nueva": "corta",
        })
        assert weak.status_code == 422
        same = client.post("/api/auth/change-password", headers=headers, json={
            "actual": ADMIN_PASSWORD, "nueva": ADMIN_PASSWORD,
        })
        assert same.status_code == 400

        changed = client.post("/api/auth/change-password", headers=headers, json={
            "actual": ADMIN_PASSWORD, "nueva": "NuevaClaveSegura2026*",
        })
        assert changed.status_code == 200, changed.text
        assert client.post("/api/auth/login", json={
            "correo": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
        }).status_code == 401
        assert client.post("/api/auth/refresh", cookies={
            "comandapro_refresh": old_refresh,
        }).status_code == 401
        assert login(client, ADMIN_EMAIL, "NuevaClaveSegura2026*")


def test_branch_scoping_for_operational_tables():
    with make_client() as client:
        admin = login(client)
        h = {"Authorization": f"Bearer {admin}"}
        roles = client.get("/api/admin/roles", headers=h).json()
        mesero_role = next(r["id"] for r in roles if r["nombre"] == "MESERO")
        created = client.post("/api/admin/usuarios", headers=h, json={
            "nombre": "Mesero Norte", "correo": "mesero.norte@example.test",
            "password": "PasswordNorte2026!", "rol_id": mesero_role, "sucursal_id": 2,
        })
        assert created.status_code == 201, created.text
        visible_users = client.get("/api/admin/usuarios", headers=h)
        assert visible_users.status_code == 200, visible_users.text
        assert any(x["correo"] == "mesero.norte@example.test" and x["sucursal_id"] == 2 for x in visible_users.json())
        branch2_token = login(client, "mesero.norte@example.test", "PasswordNorte2026!")
        branch2_tables = client.get("/api/mesas", headers={"Authorization": f"Bearer {branch2_token}"})
        assert branch2_tables.status_code == 200
        assert branch2_tables.json()
        assert {x["sucursal_id"] for x in branch2_tables.json()} == {2}


def test_order_stock_kitchen_and_split_payment_lifecycle():
    with make_client() as client:
        token = login(client)
        h = {"Authorization": f"Bearer {token}"}
        products = client.get("/api/productos", headers=h).json()
        hamburger = next(p for p in products if p["nombre"] == "Hamburguesa Comanda")
        tables = client.get("/api/mesas", headers=h).json()
        table = next(t for t in tables if t["estado"] == "LIBRE")
        stock_before = client.get("/api/inventario", headers=h).json()
        beef_before = next(i["existencia"] for i in stock_before if i["insumo"] == "Carne de res")

        created = client.post("/api/ordenes", headers=h, json={"mesa_id": table["id"], "detalles": [{"producto_id": hamburger["id"], "cantidad": 1, "notas": "Sin cebolla"}]})
        assert created.status_code == 201, created.text
        order_id = created.json()["id"]
        detail_id = created.json()["detalles"][0]["id"]

        sent = client.post(f"/api/ordenes/{order_id}/enviar-cocina", headers=h)
        assert sent.status_code == 200, sent.text
        assert sent.json()["estado"] == "EN_COCINA"
        stock_after = client.get("/api/inventario", headers=h).json()
        beef_after = next(i["existencia"] for i in stock_after if i["insumo"] == "Carne de res")
        assert abs(float(beef_before) - float(beef_after) - 0.18) < 0.000001

        started = client.patch(f"/api/cocina/detalles/{detail_id}/estado", headers=h, json={"estado": "PREPARANDO"})
        assert started.status_code == 200, started.text
        ready = client.patch(f"/api/cocina/detalles/{detail_id}/estado", headers=h, json={"estado": "LISTO"})
        assert ready.status_code == 200, ready.text
        served = client.post(f"/api/ordenes/{order_id}/servir", headers=h)
        assert served.status_code == 200, served.text
        total = float(served.json()["total"])
        assert served.json()["estado"] == "SERVIDA"

        first_payment = client.post(f"/api/ordenes/{order_id}/pagos", headers=h, json={"metodo": "EFECTIVO", "monto": round(total / 2, 2)})
        assert first_payment.status_code == 201, first_payment.text
        assert first_payment.json()["cerrada"] is False
        remainder = round(total - round(total / 2, 2), 2)
        second_payment = client.post(f"/api/ordenes/{order_id}/pagos", headers=h, json={"metodo": "TARJETA", "monto": remainder})
        assert second_payment.status_code == 201, second_payment.text
        assert second_payment.json()["cerrada"] is True
        assert second_payment.json()["orden"]["estado"] == "PAGADA"
        refreshed_tables = client.get("/api/mesas", headers=h).json()
        assert next(t for t in refreshed_tables if t["id"] == table["id"])["estado"] == "LIBRE"


def test_insufficient_stock_does_not_send_order_to_kitchen():
    with make_client() as client:
        token = login(client); h = {"Authorization": f"Bearer {token}"}
        product = next(p for p in client.get("/api/productos", headers=h).json() if p["nombre"] == "Hamburguesa Comanda")
        table = next(t for t in client.get("/api/mesas", headers=h).json() if t["estado"] == "LIBRE")
        before = client.get("/api/inventario", headers=h).json()
        beef = next(i for i in before if i["insumo"] == "Carne de res")
        result = client.post(f"/api/inventario/{beef['id']}/movimientos", headers=h, json={"tipo":"AJUSTE_NEGATIVO","cantidad":float(beef["existencia"])-0.01,"nota":"Prueba de control de stock"})
        assert result.status_code == 201
        order = client.post("/api/ordenes", headers=h, json={"mesa_id":table["id"],"detalles":[{"producto_id":product["id"],"cantidad":1}]})
        assert order.status_code == 201
        send = client.post(f"/api/ordenes/{order.json()['id']}/enviar-cocina",headers=h)
        assert send.status_code == 409
        again = client.get(f"/api/ordenes/{order.json()['id']}",headers=h)
        assert again.json()["estado"] == "ABIERTA"


def test_cancel_order_reintegrates_recipe_stock_and_releases_table():
    with make_client() as client:
        token = login(client)
        h = {"Authorization": f"Bearer {token}"}
        product = next(p for p in client.get("/api/productos", headers=h).json() if p["nombre"] == "Hamburguesa Comanda")
        table = next(t for t in client.get("/api/mesas", headers=h).json() if t["estado"] == "LIBRE")
        before = client.get("/api/inventario", headers=h).json()
        beef_before = next(x["existencia"] for x in before if x["insumo"] == "Carne de res")
        created = client.post("/api/ordenes", headers=h, json={"mesa_id": table["id"], "detalles": [{"producto_id": product["id"], "cantidad": 2}]})
        assert created.status_code == 201, created.text
        order_id = created.json()["id"]
        sent = client.post(f"/api/ordenes/{order_id}/enviar-cocina", headers=h)
        assert sent.status_code == 200, sent.text
        after_send = client.get("/api/inventario", headers=h).json()
        beef_after = next(x["existencia"] for x in after_send if x["insumo"] == "Carne de res")
        assert round(float(beef_before) - float(beef_after), 3) == 0.360
        cancelled = client.post(f"/api/ordenes/{order_id}/cancelar", headers=h, json={"motivo": "Prueba de reintegro"})
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["estado"] == "CANCELADA"
        after_cancel = client.get("/api/inventario", headers=h).json()
        beef_restored = next(x["existencia"] for x in after_cancel if x["insumo"] == "Carne de res")
        assert round(float(beef_restored), 3) == round(float(beef_before), 3)
        updated_tables = client.get("/api/mesas", headers=h).json()
        assert next(x for x in updated_tables if x["id"] == table["id"])["estado"] == "LIBRE"


def test_payment_cannot_exceed_remaining_balance():
    with make_client() as client:
        token = login(client)
        h = {"Authorization": f"Bearer {token}"}
        product = next(p for p in client.get("/api/productos", headers=h).json() if p["nombre"] == "Hamburguesa Comanda")
        table = next(t for t in client.get("/api/mesas", headers=h).json() if t["estado"] == "LIBRE")
        created = client.post("/api/ordenes", headers=h, json={"mesa_id": table["id"], "detalles": [{"producto_id": product["id"], "cantidad": 1}]})
        order_id = created.json()["id"]
        assert client.post(f"/api/ordenes/{order_id}/enviar-cocina", headers=h).status_code == 200
        detail_id = created.json()["detalles"][0]["id"]
        assert client.patch(f"/api/cocina/detalles/{detail_id}/estado", headers=h, json={"estado": "PREPARANDO"}).status_code == 200
        assert client.patch(f"/api/cocina/detalles/{detail_id}/estado", headers=h, json={"estado": "LISTO"}).status_code == 200
        served = client.post(f"/api/ordenes/{order_id}/servir", headers=h)
        total = round(float(served.json()["total"]), 2)
        overpayment = client.post(f"/api/ordenes/{order_id}/pagos", headers=h, json={"metodo": "EFECTIVO", "monto": round(total + 0.01, 2)})
        assert overpayment.status_code == 409
        unchanged = client.get(f"/api/ordenes/{order_id}", headers=h).json()
        assert unchanged["estado"] == "SERVIDA"
        assert unchanged["pagado"] == 0


def test_sales_excel_export_has_valid_xlsx_signature():
    with make_client() as client:
        token = login(client)
        response = client.get("/api/reportes/ventas.xlsx", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert response.content.startswith(b"PK\x03\x04")


def test_mesero_cannot_access_admin_user_management():
    with make_client() as client:
        token = login(client, "mesero@comandapro.local", "DemoComanda2026!")
        response = client.get("/api/admin/usuarios", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403


def test_schema_contains_all_case_tables():
    from app.models import Base

    expected = {
        "sucursales", "roles", "permisos", "rol_permiso", "usuarios",
        "refresh_tokens", "mesas", "categorias", "productos", "insumos",
        "recetas", "inventario", "movimientos_inventario", "ordenes",
        "detalle_orden", "pagos", "bitacora",
    }
    assert set(Base.metadata.tables) == expected
