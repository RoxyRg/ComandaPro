# Índice de evidencias de ComandaPro

Aquí organicé los archivos que respaldan el desarrollo, las pruebas, el monitoreo y el despliegue.

## Capturas almacenadas

- [Pruebas de backend y frontend](capturas/01-pruebas-backend.png) y [frontend](capturas/02-pruebas-frontend.png).
- [Login](capturas/04-login.png), [mesas](capturas/05-mesero-mesas.png), [toma de orden](capturas/06-toma-orden.png).
- [Cocina en vivo](capturas/07-cocina-tiempo-real.png), [preparando](capturas/08-cocina-preparando.png), [listo](capturas/08-cocina-listos.png), [servido](capturas/08-mesero-servido.png).
- [Pago parcial](capturas/09-caja-pago-parcial.png), [cobro total](capturas/10-caja-pago-total.png).
- [Inventario](capturas/11-inventario.png), [permisos](capturas/12-matriz-permisos.png), [recetas](capturas/13-productos-recetas.png), [reportes](capturas/14-reportes.png), [bitácora](capturas/15-bitacora.png).
- [Swagger](capturas/17-swagger.png), [movimientos](capturas/18-movimientos-inventario.png), [métricas](capturas/20-prometheus-metricas.png).
- [Prueba de carga](capturas/22-prueba-carga.png), [persistencia](capturas/23-persistencia.png), [docker stats](capturas/24-docker-stats.png), [historial de commits](capturas/26-historial-commits.png), [estructura del repositorio](capturas/27-repositorio.png).

## Evidencias finales de infraestructura y CI/CD

El 30 de octubre de 2026 comprobé las capturas de Docker, Prometheus, Grafana, GitHub Actions y Render. Para documentar cada parte de la instalación utilicé:

| Captura | Evidencia que muestra |
|---|---|
| [03-docker-compose-ps.png](capturas/03-docker-compose-ps.png) | Seis contenedores en ejecución, incluyendo cAdvisor |
| [19-prometheus-targets.png](capturas/19-prometheus-targets.png) | Dos objetivos de monitoreo en estado `UP` |
| [21-grafana-dashboard.png](capturas/21-grafana-dashboard.png) | Seis paneles de métricas de FastAPI y contenedores |
| [25-github-actions.png](capturas/25-github-actions.png) | Ejecución #13 exitosa: FastAPI, React, Docker Compose y GHCR |
| [28-render-despliegue.png](capturas/28-render-despliegue.png) | Aplicación Docker desplegada y PostgreSQL 16 disponible en Render |

Los primeros archivos de Docker y monitoreo están respaldados por el [commit `1fad740`](https://github.com/RoxyRg/ComandaPro/commit/1fad740cc3e480c3da59dc81c89224c43dff09bc). El resultado de la automatización puede comprobarse también directamente en la [ejecución #13](https://github.com/RoxyRg/ComandaPro/actions/runs/41112524663).

## Evidencia remota comprobable

- [Registro de prueba integral por roles en Render](pruebas/validacion_render_2026-10-30.md).
- [Código de la prueba remota](../scripts/smoke_render_roles.py).
- [Resultado CI/CD en GitHub Actions](https://github.com/RoxyRg/ComandaPro/actions/runs/41112524663).
- [ComandaPro publicado](https://comandapro-demo.onrender.com).
- [Guía y Blueprint de Render](../docs/RENDER.md).

Debo completar la parte gráfica del despliegue remoto con una captura del servicio `Live`, la base `Available` y el acceso a ComandaPro; el registro del script ya está guardado en texto.
