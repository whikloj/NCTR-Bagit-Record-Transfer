#!/bin/bash

echo "Creating migrations..."
python3 manage.py makemigrations --no-input --settings=${DJANGO_SETTINGS_MODULE}

echo "Applying migrations..."
python3 manage.py migrate --no-input --settings=${DJANGO_SETTINGS_MODULE}

echo "Running Django RQ worker"
python3 manage.py rqworker default --settings=${DJANGO_SETTINGS_MODULE}
