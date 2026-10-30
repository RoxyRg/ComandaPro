# Validación del despliegue público de ComandaPro — 30 de octubre de 2026

## Objetivo

Ejecuté una prueba completa contra la aplicación desplegada en Render para comprobar que las tres cuentas operativas realizan las funciones que corresponden a su rol y comparten la misma base PostgreSQL. Los datos generados son solamente de demostración.

- Dirección comprobada: https://comandapro-demo.onrender.com
- Rama de código: `main`
- Versión del código: commit `001b1c7`
- Herramienta de prueba: `scripts/smoke_render_roles.py`
- Contraseña de prueba: la definida en el README para los tres roles operativos
- Resultado: **EXITOSO**

## Salida de la prueba (registrada en mi terminal)

```text
OK FastAPI y PostgreSQL
OK inicio de sesion: MESERO
OK inicio de sesion: COCINA
OK inicio de sesion: CAJERO
OK aislamiento de permisos por rol
OK mesero: orden #3 creada, mesa 1
OK pedido enviado y recibido por cocina
OK cocina preparo, entrego, mesero sirvio
OK cajero cobro dividido y orden pagada
OK mesa liberada y venta registrada
RESULTADO: EXITO - flujo por roles completado en Render.
```

## Interpretación del resultado

Comprobé que los usuarios pudieron autenticarse y que la API impidió operaciones no autorizadas. Después generé una orden en la mesa 1, la envié a cocina y cambié el estado de preparación. Una vez servida, registré dos pagos desde la cuenta de caja. El script verificó que la orden quedó pagada, la mesa se liberó y la venta quedó registrada.

Esta prueba **sí se ejecutó en la base pública de Render**, a diferencia de los tests aislados de FastAPI en SQLite. No sustituyo las pruebas visuales entre dos navegadores por esta prueba: cada herramienta valida una parte distinta del comportamiento.

## Integración continua

- [GitHub Actions — ejecución #13 aprobada](https://github.com/RoxyRg/ComandaPro/actions/runs/41112524663)
- [Script reproducible de la prueba](../../scripts/smoke_render_roles.py)
- [README y registro general](../../README.md)

La prueba creó una orden y pagos simulados de forma intencional. No hay integración con un banco ni información real de clientes.
