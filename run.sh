#!/usr/bin/env bash
# run.sh: start, reset, stop and inspect every service, in dependency order (TECHNICAL §5).
# Order: Postgres → Toolbox → (Judge → Masker → Phoenix → CLI or web, added in later stages).
set -euo pipefail
cd "$(dirname "$0")"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
mkdir -p .logs .pids

PG_CONTAINER=support-postgres
PG_DB=support
PG_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
TOOLBOX_PORT=5000
TOOLBOX_URL="http://127.0.0.1:${TOOLBOX_PORT}"

# ---------- Postgres ----------
pg_running() { docker ps --filter "name=^${PG_CONTAINER}$" --format '{{.Names}}' | grep -q .; }
pg_exists()  { docker ps -a --filter "name=^${PG_CONTAINER}$" --format '{{.Names}}' | grep -q .; }
pg_ready()   { docker exec "$PG_CONTAINER" pg_isready -U postgres -d "$PG_DB" >/dev/null 2>&1; }

start_postgres() {
  if pg_running; then
    echo "postgres: already running"
  elif pg_exists; then
    docker start "$PG_CONTAINER" >/dev/null
    echo "postgres: starting"
  else
    docker run -d --name "$PG_CONTAINER" \
      -e POSTGRES_PASSWORD="$PG_PASSWORD" -e POSTGRES_DB="$PG_DB" \
      -p 5432:5432 postgres:16 >/dev/null
    echo "postgres: starting (new container)"
  fi
  for _ in $(seq 1 30); do
    if pg_ready; then echo "postgres: ready"; return; fi
    sleep 1
  done
  echo "postgres: not ready after 30s" >&2
  exit 1
}

# Stage 1 decision: reset = drop and recreate inside the running container (option 1).
reset_db() {
  start_postgres
  docker exec -i "$PG_CONTAINER" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$PG_DB" < db/seed.sql
  # The Toolbox role's password lives in .env, not in seed.sql.
  docker exec "$PG_CONTAINER" psql -q -U postgres -d "$PG_DB" \
    -c "ALTER ROLE support_toolbox PASSWORD '${TOOLBOX_DB_PASSWORD:?set TOOLBOX_DB_PASSWORD in .env}';"
  echo "postgres: seeded from db/seed.sql"
}

# psql shortcut so checks run without a local client: ./run.sh psql -c "select 1;"
run_psql() { docker exec -i "$PG_CONTAINER" psql -U postgres -d "$PG_DB" "$@"; }

# ---------- MCP Toolbox ----------
toolbox_up() { curl -s -o /dev/null -w '%{http_code}' "$TOOLBOX_URL/" 2>/dev/null | grep -q '^200$'; }

start_toolbox() {
  if toolbox_up; then echo "toolbox: already running"; return; fi
  : "${TOOLBOX_DB_PASSWORD:?set TOOLBOX_DB_PASSWORD in .env}"
  nohup npx -y @toolbox-sdk/server --config mcp_toolbox/tools.yaml --enable-api \
    --address 127.0.0.1 --port "$TOOLBOX_PORT" > .logs/toolbox.log 2>&1 &
  echo $! > .pids/toolbox.pid
  echo "toolbox: starting"
  for _ in $(seq 1 60); do
    if toolbox_up; then echo "toolbox: ready at $TOOLBOX_URL"; return; fi
    sleep 1
  done
  echo "toolbox: not ready after 60s; see .logs/toolbox.log" >&2
  exit 1
}

stop_port() {  # $1 = service name, $2 = port. npx forks a child, so kill whoever listens.
  local pids
  pids=$(netstat -ano 2>/dev/null | grep -E ":$2 .*LISTEN" | awk '{print $NF}' | sort -u)
  if [ -n "$pids" ]; then
    for pid in $pids; do taskkill //PID "$pid" //T //F >/dev/null 2>&1 || kill "$pid" 2>/dev/null || true; done
    echo "$1: stopped"
  else
    echo "$1: not running"
  fi
  rm -f ".pids/$1.pid"
}

# ---------- commands ----------
start_all() {
  start_postgres
  start_toolbox
}

status() {
  if pg_running && pg_ready; then echo "postgres   up    (docker: $PG_CONTAINER, db: $PG_DB)"; else echo "postgres   DOWN"; fi
  if toolbox_up; then echo "toolbox    up    ($TOOLBOX_URL)"; else echo "toolbox    DOWN"; fi
}

stop_all() {
  stop_port toolbox "$TOOLBOX_PORT"
  if pg_running; then docker stop "$PG_CONTAINER" >/dev/null && echo "postgres: stopped"; else echo "postgres: not running"; fi
}

case "${1:-}" in
  start)    start_all ;;
  postgres) start_postgres ;;
  toolbox)  start_toolbox ;;
  reset)    reset_db ;;
  psql)     shift; run_psql "$@" ;;
  status)   status ;;
  stop)     stop_all ;;
  *) echo "usage: ./run.sh {start|postgres|toolbox|reset|psql ...|status|stop}"; exit 1 ;;
esac
