# =============================================================================
# ETAPA 1: Compilación de Flutter Web
# =============================================================================
FROM ghcr.io/cirruslabs/flutter:stable AS build

WORKDIR /app

# Copiar definición de dependencias primero para aprovechar caché de capas Docker
COPY pubspec.* ./
RUN flutter pub get

# Copiar código fuente de la aplicación y recursos web
COPY . .

# Asegurar soporte web y compilar bundle optimizado de producción
RUN ([ -d web ] || flutter create . --platforms=web) && \
    flutter build web --release

# =============================================================================
# ETAPA 2: Servidor Web Ligero de Producción (Nginx Alpine)
# =============================================================================
FROM nginx:1.27-alpine AS production

# Configuración Nginx optimizada para SPA Flutter Web
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar artefactos compilados desde la etapa de build
COPY --from=build /app/build/web /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
