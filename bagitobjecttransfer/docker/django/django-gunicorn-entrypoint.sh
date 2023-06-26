#!/bin/bash

echo "Creating job directory"
mkdir -p /app/media/jobs

echo "Collecting static files..."
python3 manage.py collectstatic --clear --no-input -v0 --settings=${DJANGO_SETTINGS_MODULE}

echo "Running Django app"
# --reload is only useful for development, remove for a production setup.
exec gunicorn --workers=3 --bind unix:/run/rsds-gunicorn.sock --capture-output --enable-stdio-inheritance bagitobjecttransfer.wsgi --reload
