# ComandaPro en Render (demostración gratuita)

El archivo `render.yaml` define un servicio Docker que sirve React, FastAPI y Socket.IO desde un mismo dominio, junto con PostgreSQL 16 de Render. El despliegue se conecta a GitHub y se actualiza cuando pasan las comprobaciones de `main`.

## Crear el despliegue

1. Inicia sesión en [Render](https://dashboard.render.com/).
2. Selecciona **New → Blueprint** y conecta `RoxyRg/ComandaPro` desde tu cuenta de GitHub.
3. Selecciona la rama `main` y el archivo `render.yaml`.
4. Comprueba que **ambos recursos** tengan plan `Free`: `comandapro-demo` y `comandapro-demo-db`. No aceptes una conversión a un plan de pago sin revisar el precio.
5. Cuando Render solicite `COMANDAPRO_ADMIN_PASSWORD`, establece una contraseña fuerte que no hayas usado antes. No la subas a Git ni la compartas en capturas.
6. Aplica el Blueprint y espera hasta comprobar que los servicios aparecen saludables. Abre la dirección pública `https://...onrender.com` que Render asigne y comprueba `/api/health`.

La contraseña para usuarios de ejemplo se genera automáticamente. La interfaz pública oculta los datos de acceso de demostración, a diferencia de la instalación académica local.

## Consideraciones técnicas

- Render construye la imagen con `Dockerfile.render` usando la raíz del repositorio como contexto: compila React y ejecuta FastAPI, que entrega los archivos estáticos y la API por el mismo puerto, conservando Socket.IO.
- Render facilita la URL interna de PostgreSQL en `DATABASE_URL`; el backend la adapta al controlador `psycopg`.
- `JWT_SECRET` y la contraseña de demostración se generan en Render; `COOKIE_SECURE=true` solo permite cookies seguras bajo HTTPS.
- GitHub Actions sigue realizando las pruebas y publicando imágenes en GHCR de forma independiente. Render construye directamente desde GitHub y espera comprobaciones correctas para iniciar nuevos despliegues.
- **Render Free no ejecuta el Docker Compose de seis servicios.** Prometheus, Grafana y cAdvisor continúan funcionando mediante `docker-compose.yml` en el entorno local. Render ofrece logs y métricas básicos para su servicio.
- Render Free suspende el servicio web tras 15 minutos de inactividad. El siguiente acceso lo reactiva con demora.
- PostgreSQL Free **expira después de 30 días**. El plan gratuito no proporciona respaldos administrados; exporta datos o migra a otra base antes de esa fecha. No es un entorno de disponibilidad permanente ni producción.
- Las credenciales de administración y los tokens deben permanecer fuera del repositorio. Para acceso público prolongado conviene revisar la seguridad de usuarios, limitar solicitudes, configurar respaldos y utilizar almacenamiento persistente.

El entorno local y sus capturas existentes no se alteran con estos cambios.
