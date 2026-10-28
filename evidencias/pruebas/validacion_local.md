# Registro de validación local — ComandaPro

**Fecha:** 27 de octubre de 2026.

## Comprobaciones ejecutadas

- Backend: `pytest -q` en `backend/` con las dependencias de `requirements.txt` y `python-socketio` real: 14 pruebas aprobadas.
- Frontend: `npm install`, `npm test` (3 pruebas de Vitest aprobadas) y `npm run build` (TypeScript y Vite) completados sin errores.
- `docker compose config --quiet` con `.env.example`: configuración válida.

## Corrección realizada durante la revisión

El build de React fallaba con `error TS2769` en `vite.config.ts` porque `vitest` 2.x traía su propia copia de `vite`. Se actualizó `vitest` a la versión `^3.2.4` en `frontend/package.json` y se agregó `package-lock.json`.

## Pendiente de comprobar en el equipo con Docker

`docker compose up -d --build`, el estado `healthy` de los servicios, el flujo con dos navegadores (mesero y cocina) y el resultado verde de GitHub Actions. Las capturas de esas pruebas se guardan en `evidencias/`.
