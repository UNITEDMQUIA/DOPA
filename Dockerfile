# =============================================================================
# DOCKERFILE UNIFICADO MULTI-STAGE — PROYECTO DOPA (TDAH)
# Agente Responsable: Agent_DevOps (SRE & Contenedorización)
# Targets disponibles:
#   - backend  : Servidor API RESTful en Python 3.12 + FastAPI + SQLAlchemy
#   - frontend : Aplicación Flutter Web servida en Nginx 1.27 Alpine con Proxy API
# =============================================================================

# -----------------------------------------------------------------------------
# TARGET 1: BACKEND FASTAPI (Python 3.12 Slim)
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS backend

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY database ./database

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# -----------------------------------------------------------------------------
# ETAPA INTERMEDIA: COMPILACIÓN DE FLUTTER WEB
# -----------------------------------------------------------------------------
FROM ghcr.io/cirruslabs/flutter:stable AS frontend-build

WORKDIR /app

ARG API_BASE_URL=/api/v1

# Copiar definición de dependencias primero para aprovechar caché de capas Docker
COPY pubspec.* ./
RUN flutter pub get

# Copiar código fuente de la aplicación Flutter y recursos web
COPY analysis_options.yaml ./
COPY lib ./lib
COPY web ./web

# Asegurar soporte web y compilar bundle optimizado de producción inyectando API_BASE_URL
RUN ([ -d web ] || flutter create . --platforms=web) && \
    flutter build web --release --dart-define=API_BASE_URL=${API_BASE_URL}


# -----------------------------------------------------------------------------
# TARGET 2: FRONTEND SERVIDOR WEB DE PRODUCCIÓN (Nginx Alpine)
# -----------------------------------------------------------------------------
FROM nginx:1.27-alpine AS frontend

# Configuración Nginx optimizada para SPA Flutter Web + Reverse Proxy a FastAPI
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar artefactos compilados desde la etapa de build
COPY --from=frontend-build /app/build/web /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
