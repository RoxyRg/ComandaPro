#!/usr/bin/env bash
set -euo pipefail

# Comprueba que el volumen PostgreSQL conserva conteos tras reiniciar solo este stack.
# No borra volúmenes ni filas. Ejecutar desde la carpeta raíz del proyecto con Compose levantado.
COMPOSE=(docker compose --env-file .env -f docker-compose.yml)
OUT="evidencias/pruebas"
mkdir -p "$OUT"

read_counts() {
  "${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F '|' \
    -c "SELECT (SELECT COUNT(*) FROM sucursales),
               (SELECT COUNT(*) FROM usuarios),
               (SELECT COUNT(*) FROM productos),
               (SELECT COUNT(*) FROM inventario),
               (SELECT COUNT(*) FROM ordenes),
               (SELECT COUNT(*) FROM pagos);"
}

# POSTGRES_USER y POSTGRES_DB se cargan desde el .env de Compose.
set -a
# shellcheck disable=SC1091
source .env
set +a

echo "Conteos antes del reinicio:"
read_counts | tee "$OUT/persistencia_antes.txt"
"${COMPOSE[@]}" restart
"${COMPOSE[@]}" ps -a

for attempt in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1 && \
     "${COMPOSE[@]}" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Conteos después del reinicio:"
read_counts | tee "$OUT/persistencia_despues.txt"
diff -u "$OUT/persistencia_antes.txt" "$OUT/persistencia_despues.txt"
echo "CORRECTO: los conteos se conservaron tras reiniciar el stack."
