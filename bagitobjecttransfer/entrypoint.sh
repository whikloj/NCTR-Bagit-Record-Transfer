#!/bin/sh
set -e

ROLE=${ROLE:-web}

# ---------- defaults ----------
GUNICORN_BIND=${GUNICORN_BIND:-0.0.0.0:8000}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}
GUNICORN_THREADS=${GUNICORN_THREADS:-8}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}
GUNICORN_GRACEFUL_TIMEOUT=${GUNICORN_GRACEFUL_TIMEOUT:-30}
GUNICORN_WORKER_CLASS=${GUNICORN_WORKER_CLASS:-gthread}
GUNICORN_PIDFILE=${GUNICORN_PIDFILE:-/var/run/nginx/gunicorn.pid}
RQ_QUEUES=${RQ_QUEUES:-default}

# ---------- db readiness check ----------
MAX_RETRIES=${DB_MAX_RETRIES:-10}
RETRY_INTERVAL=${DB_RETRY_INTERVAL:-5}

wait_for_db() {
  local retries=0

  echo "Waiting for database to be ready..."
  # Wait for MySQL to be ready
  while ! nc -z ${MYSQL_HOST:-db} ${MYSQL_PORT:-3306}; do
    retries=$((retries + 1))
    if [ "$retries" -ge "$MAX_RETRIES" ]; then
      echo "ERROR: Database port not available after $MAX_RETRIES attempts. Exiting."
      exit 1
    fi
    echo "  TCP check failed (attempt $retries/$MAX_RETRIES), retrying in ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
  done
  echo "Database is ready!"
}

if [ "$ROLE" = "web" ]; then
  wait_for_db

  echo "[web] Collecting static files..."
  python manage.py collectstatic --clear --no-input -v0

  echo "Running migrations..."
  python manage.py migrate --noinput

  echo "[web] Starting Gunicorn"
  exec gunicorn bagitobjecttransfer.wsgi:application \
    --bind "${GUNICORN_BIND}" \
    --umask 007 \
    --timeout "${GUNICORN_TIMEOUT}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT}" \
    --access-logfile - \
    --error-logfile - \
    --pid "${GUNICORN_PIDFILE}"

elif [ "$ROLE" = "worker" ]; then
  wait_for_db

  echo "[worker] Starting RQ worker on queues: ${RQ_QUEUES}"
  exec python manage.py rqworker ${RQ_QUEUES}

else
  echo "ERROR: Unknown ROLE='${ROLE}' (expected 'web' or 'worker')"
  exit 1
fi
