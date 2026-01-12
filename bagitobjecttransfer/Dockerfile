FROM python:3.12-slim

# Don't generate .pyc files or __pycache__ folders
ENV PYTHONDONTWRITEBYTECODE=1
# Don't buffer stdout and stderr
ENV PYTHONUNBUFFERED=1

# defaults
ENV GUNICORN_WORKERS=2
ENV GUNICORN_THREADS=4
ENV GUNICORN_BIND=0.0.0.0:8000
ENV GUNICORN_WORKER_CLASS=gevent
ENV RQ_QUEUES=default
ENV DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
