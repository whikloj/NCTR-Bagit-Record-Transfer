# ---------- Builder stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies needed for pip, git, and building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    gnupg \
    dirmngr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# ---------- Final stage ----------
FROM python:3.12-slim

# Django / Gunicorn / RQ defaults
ENV GUNICORN_WORKERS=2
ENV GUNICORN_THREADS=4
ENV GUNICORN_BIND=0.0.0.0:8000
ENV GUNICORN_WORKER_CLASS=gevent
ENV RQ_QUEUES=default
ENV DJANGO_SETTINGS_MODULE=bagitobjecttransfer.settings.docker

WORKDIR /app

# Install dependencies needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy app source code
COPY --from=builder /app /app

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

