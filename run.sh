#!/usr/bin/env bash
# Run the whole SafarChin stack in production mode, under Docker Compose, on a
# server. Builds real images (no bind-mounted source, no dev servers: gunicorn
# for the backend, a built `next start` for the frontend), and does not
# publish Postgres/Redis to the host. See docker-compose.prod.yml.
#
# For local development use ./dev.sh instead -- this script assumes a real
# server environment and real secrets in backend/.env / frontend/.env.local.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ENV="$ROOT_DIR/backend/.env"
FRONTEND_ENV="$ROOT_DIR/frontend/.env.local"
export BACKEND_HOST_PORT=8025
export FRONTEND_HOST_PORT=3025

env_value() {
  # env_value VAR FILE -- last matching line wins, same as a real env file load.
  grep -E "^$1=" "$2" 2>/dev/null | tail -n1 | cut -d'=' -f2-
}

echo "==> Checking env files"
if [ ! -f "$BACKEND_ENV" ]; then
  echo "Missing $BACKEND_ENV -- copy backend/.env.example, fill in real production secrets" \
       "(DJANGO_SECRET_KEY, DJANGO_DEBUG=False, DJANGO_ALLOWED_HOSTS, DB/API keys), then rerun." >&2
  exit 1
fi
if [ ! -f "$FRONTEND_ENV" ]; then
  echo "Missing $FRONTEND_ENV -- copy frontend/.env.local.example, set it to this server's" \
       "real public URL/keys, then rerun." >&2
  exit 1
fi

debug_value="$(env_value DJANGO_DEBUG "$BACKEND_ENV")"
if [ -z "$debug_value" ] || [ "$(echo "$debug_value" | tr '[:upper:]' '[:lower:]')" != "false" ]; then
  echo "WARNING: DJANGO_DEBUG in backend/.env is '${debug_value:-<unset>}', not 'False'." >&2
  echo "         Running with DEBUG on in production leaks stack traces. Fix before relying on this." >&2
fi

hosts_value="$(env_value DJANGO_ALLOWED_HOSTS "$BACKEND_ENV")"
if [ "$hosts_value" = "localhost,127.0.0.1" ] || [ -z "$hosts_value" ]; then
  echo "WARNING: DJANGO_ALLOWED_HOSTS in backend/.env is still the local-dev default" \
       "('${hosts_value:-<unset>}'). Django will reject every request to this server's real" \
       "domain/IP until you set it." >&2
fi

api_base_value="$(env_value NEXT_PUBLIC_API_BASE_URL "$FRONTEND_ENV")"
if [ "${api_base_value#*:$BACKEND_HOST_PORT}" = "$api_base_value" ]; then
  echo "WARNING: NEXT_PUBLIC_API_BASE_URL in frontend/.env.local is '${api_base_value:-<unset>}'," >&2
  echo "         which doesn't reference :$BACKEND_HOST_PORT (the backend's port below). This gets baked" >&2
  echo "         into the frontend build -- the browser will call the wrong place until it's fixed." >&2
fi

echo "==> Loading frontend/.env.local (NEXT_PUBLIC_* values are baked into the build)"
set -a
# shellcheck disable=SC1090
source "$FRONTEND_ENV"
set +a

echo "==> Building and starting (docker compose -f docker-compose.prod.yml)"
cd "$ROOT_DIR"
docker compose -f docker-compose.prod.yml up -d --build

cat <<EOF

Stack is up:
  frontend -> http://localhost:$FRONTEND_HOST_PORT  (or this server's real domain, once DNS/proxy point here)
  backend  -> http://localhost:$BACKEND_HOST_PORT
  db/redis -> internal only, not published to the host

  docker compose -f docker-compose.prod.yml ps        # status
  docker compose -f docker-compose.prod.yml logs -f    # logs
  docker compose -f docker-compose.prod.yml down       # stop

Not set up by this script: TLS/a reverse proxy in front of ports $FRONTEND_HOST_PORT/$BACKEND_HOST_PORT, and
a backup strategy for the pgdata volume. Put a reverse proxy (nginx/Caddy/Traefik)
in front for real public traffic.
EOF
