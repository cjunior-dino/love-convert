# syntax=docker/dockerfile:1.7

FROM python:3.12-slim-bookworm AS backend

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=false \
    DJANGO_DB_PATH=/app/data/db.sqlite3 \
    DJANGO_MEDIA_ROOT=/app/media \
    DJANGO_STATIC_ROOT=/app/staticfiles

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fontconfig \
        fonts-crosextra-caladea \
        fonts-crosextra-carlito \
        fonts-dejavu-core \
        fonts-liberation2 \
        libreoffice-writer \
        pandoc \
    && rm -rf /var/lib/apt/lists/*

COPY docker/fontconfig-local.conf /etc/fonts/local.conf
COPY docker/fonts/ /usr/local/share/fonts/custom/
RUN fc-cache -f

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

RUN python manage.py collectstatic --noinput \
    && mkdir -p /app/data /app/media \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 180 --access-logfile - --error-logfile -"]

FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine AS frontend

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /frontend/dist/love-converter/browser/ /usr/share/nginx/html/

EXPOSE 80
