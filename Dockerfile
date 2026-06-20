# Étape 1 : build du frontend React
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY web/frontend/package.json ./
RUN npm install
COPY web/frontend/ ./
RUN npm run build

# Étape 2 : image Python (API + moteur + UI statique)
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
COPY web/backend/requirements.txt ./web/backend/
RUN pip install --no-cache-dir -r requirements.txt -r web/backend/requirements.txt

COPY chess_engine/ ./chess_engine/
COPY web/backend/ ./web/backend/
COPY --from=frontend-build /app/frontend/dist ./web/backend/static

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
