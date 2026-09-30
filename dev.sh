#!/usr/bin/env bash
# Run the whole SafarChin stack locally: Postgres + Redis (Docker), Django,
# Celery worker, and the Next.js frontend. Ctrl+C stops everything.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.dev-logs"
mkdir -p "$LOG_DIR"

PIDS=()

cleanup() {
  echo ""
  echo "Stopping..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Starting Postgres + Redis (docker compose)"
(cd "$ROOT_DIR" && docker compose up -d --wait db redis)

echo "==> Applying Django migrations"
(cd "$BACKEND_DIR" && .venv/bin/python manage.py migrate --noinput)

echo "==> Starting Django dev server (:8000)"
(cd "$BACKEND_DIR" && exec .venv/bin/python manage.py runserver 0.0.0.0:8000) \
  >"$LOG_DIR/backend.log" 2>&1 &
PIDS+=($!)

echo "==> Starting Celery worker"
(cd "$BACKEND_DIR" && exec .venv/bin/celery -A config worker -l info --pool=solo) \
  >"$LOG_DIR/celery.log" 2>&1 &
PIDS+=($!)

echo "==> Starting Next.js dev server (:3000)"
# Call the `next` binary directly (not `npm run dev`) so `exec` replaces this subshell
# with the actual server process -- npm forks a child instead of exec-ing it, which left
# orphaned `next dev` processes behind after a plain `kill` of the wrapper in the past.
(cd "$FRONTEND_DIR" && exec ./node_modules/.bin/next dev) \
  >"$LOG_DIR/frontend.log" 2>&1 &
PIDS+=($!)

cat <<EOF

All services starting:
  frontend  -> http://localhost:3000   (log: .dev-logs/frontend.log)
  backend   -> http://localhost:8000   (log: .dev-logs/backend.log)
  celery    -> (log: .dev-logs/celery.log)
  db/redis  -> docker compose (postgres:5433, redis:6380)

Tailing logs below. Press Ctrl+C to stop everything.
EOF

tail -f "$LOG_DIR/backend.log" "$LOG_DIR/celery.log" "$LOG_DIR/frontend.log" &
PIDS+=($!)

# Plain `wait` (not `wait -n`, a bash 4.3+ feature -- macOS ships bash 3.2) blocks until
# every job above exits. That's fine here: the normal exit path is Ctrl+C, which the
# `trap` above turns into killing everything at once anyway.
wait
