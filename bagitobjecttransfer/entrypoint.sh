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
RQ_QUEUES=${RQ_QUEUES:-default}

if [ "$ROLE" = "web" ]; then
  echo "[web] Collecting static files..."
  python manage.py collectstatic --clear --no-input -v0

  echo "[web] Starting Gunicorn"
  exec gunicorn bagitobjecttransfer.wsgi:application \
    --bind "${GUNICORN_BIND}" \
    --workers "${GUNICORN_WORKERS}" \
    --threads "${GUNICORN_THREADS}" \
    --worker-class "${GUNICORN_WORKER_CLASS}" \
    --timeout "${GUNICORN_TIMEOUT}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT}" \
    --access-logfile - \
    --error-logfile -

elif [ "$ROLE" = "worker" ]; then
  echo "[worker] Starting RQ worker on queues: ${RQ_QUEUES}"
  exec python manage.py rqworker ${RQ_QUEUES}

else
  echo "ERROR: Unknown ROLE='${ROLE}' (expected 'web' or 'worker')"
  exit 1
fi
