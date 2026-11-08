# 🚀 Guía de Inicio, Ejecución Móvil y Despliegue — Proyecto DOPA

Esta guía detalla paso a paso cómo iniciar el ecosistema **DOPA** en entorno local, todas las opciones disponibles para ejecutar la aplicación en un **dispositivo móvil (celular)**, cómo correr las pruebas automatizadas (QA) y cómo desplegar la plataforma en un **servidor de producción**.

---

## 📋 1. Requisitos Previos

| Herramienta | Uso | Versión Recomendada |
|---|---|---|
| **Docker & Docker Compose** | Ejecución unificada de Base de Datos, Backend y Web | Docker Desktop 4.x+ / Docker Engine 24+ |
| **Flutter SDK** | Desarrollo, pruebas y compilación móvil (Android / iOS) | Flutter 3.24+ / Dart 3.5+ |
| **Python** | Desarrollo y pruebas nativas del Backend FastAPI | Python 3.12+ |
| **PostgreSQL** | Base de datos relacional (solo si se ejecuta sin Docker) | PostgreSQL 16+ |
| **Android Studio / SDK** | Compilación de APK y depuración USB / Emulador Android | Android SDK 34+ |

---

## 💻 2. Cómo Iniciar el Proyecto en Local

Existen dos formas de levantar el proyecto localmente: **Opción A (Con Docker Compose — Recomendada)** o **Opción B (Manual / Nativa)**.

### Opción A: Inicio Rápido Unificado con Docker Compose (Recomendado)

El archivo [`docker-compose.yml`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/docker-compose.yml) en la raíz de `dopa/` levanta automáticamente PostgreSQL (con el esquema y datos semilla de [`database/init.sql`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/database/init.sql)), pgAdmin, el Backend FastAPI y el Frontend Web con Nginx.

1. Abre una terminal en la carpeta del proyecto:
   ```powershell
   cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
   ```
2. (Opcional) Crea tu archivo `.env` a partir de la plantilla [`.env.example`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/.env.example):
   ```powershell
   Copy-Item .env.example .env
   ```
3. Construye e inicia todos los contenedores:
   ```powershell
   docker compose up -d --build
   ```
4. Verifica que los contenedores estén saludables:
   ```powershell
   docker compose ps
   ```

#### Servicios disponibles al iniciar con Docker:
- **Aplicación Web (Flutter + Nginx Proxy):** http://localhost:3000
- **API Backend (FastAPI):** http://localhost:8000
- **Documentación Interactiva Swagger UI:** http://localhost:8000/docs
- **Healthcheck API:** http://localhost:8000/health
- **pgAdmin 4 (Gestor visual de BD):** http://localhost:5050 (`admin@dopa.local` / `admin123`)
- **PostgreSQL 16:** `localhost:5432` (BD: `dopa_db`, Usuario: `dopa_user`, Password: `dopa_password`)
- **Usuario Demostración Precargado:** `fred@dopa.app` / Contraseña: `Dopa1234!`

---

### Opción B: Inicio Manual (Sin Docker o Híbrido para Desarrollo)

Si deseas correr el Backend y el Frontend de forma nativa en tu máquina:

#### Paso 1: Base de Datos PostgreSQL
Puedes levantar **únicamente la base de datos** en Docker:
```powershell
cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
docker compose up -d db
```
*(O bien crear una base de datos `dopa_db` en tu PostgreSQL local y ejecutar el script [`database/init.sql`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/database/init.sql)).*

#### Paso 2: Iniciar el Backend (FastAPI)
```powershell
cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"

# Crear entorno virtual (solo la primera vez)
python -m venv .venv

# Activar entorno virtual en PowerShell
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor escuchando en todas las interfaces (0.0.0.0) para permitir conexión desde el celular
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Paso 3: Iniciar el Frontend (Flutter)
```powershell
cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
flutter pub get
flutter run -d chrome
```

---

## 📱 3. Opciones para Ejecutar el Aplicativo en un Dispositivo Móvil (Celular)

El aplicativo DOPA está configurado con soporte nativo para **Android** ([`android/`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/android/app/src/main/AndroidManifest.xml)), **iOS** (`ios/`) y **PWA Móvil**, e incluye configuración de red dinámica mediante `--dart-define=API_BASE_URL=...` en [`lib/services/api_service.dart`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/lib/services/api_service.dart).

A continuación se presentan las **6 opciones disponibles** para correr la aplicación en un celular, ordenadas según tu caso de uso:

---

### Opción 1: Celular Físico Android por Cable USB o Depuración Inalámbrica (Wi-Fi) — *Recomendada para Desarrollo y Pruebas Reales*

Permite instalar y ejecutar la app directamente en tu teléfono Android con *Hot Reload*, consumiendo el Backend que corre en tu computador a través de la misma red Wi-Fi.

1. **Activa las Opciones de Desarrollador en tu celular Android:**
   - Ve a *Ajustes > Acerca del teléfono* y toca 7 veces en **Número de compilación**.
   - Entra a *Ajustes > Sistema > Opciones para desarrolladores* y activa **Depuración por USB** (o **Depuración inalámbrica** en Android 11+).
2. **Conecta tu celular al PC** por cable USB y acepta el permiso de depuración en la pantalla del teléfono.
3. **Obtén la dirección IP local (LAN) de tu PC:**
   ```powershell
   ipconfig
   ```
   Busca el adaptador Wi-Fi o Ethernet y anota la **Dirección IPv4** (por ejemplo: `192.168.1.50`).
4. **Asegúrate de que el Backend esté corriendo** en el puerto `8000` (con `docker compose up -d db backend` o con `uvicorn app.main:app --host 0.0.0.0 --port 8000`).
5. **Ejecuta la app en tu celular inyectando la IP de tu PC:**
   ```powershell
   cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
   flutter devices
   flutter run -d <ID_DE_TU_CELULAR> --dart-define=API_BASE_URL=http://192.168.1.50:8000/api/v1
   ```
   > **Nota:** Si conectas el celular por cable USB y prefieres no depender del Wi-Fi o firewall de Windows, puedes usar redirección de puertos ADB:
   > ```powershell
   > adb reverse tcp:8000 tcp:8000
   > flutter run -d <ID_DE_TU_CELULAR> --dart-define=API_BASE_URL=http://localhost:8000/api/v1
   > ```

---

### Opción 2: Generar e Instalar un Archivo `.APK` Independiente en el Celular Android

Ideal para compartir la aplicación instalable con otros usuarios o instalarla en el celular sin necesidad de tener Flutter abierto.

1. **Compila el APK de producción** apuntando a la IP de tu servidor o de tu PC:
   ```powershell
   cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
   flutter build apk --release --dart-define=API_BASE_URL=http://192.168.1.50:8000/api/v1
   ```
   *(Si el backend ya está en un servidor público o túnel HTTPS, reemplaza la URL por `https://tu-dominio.com/api/v1`).*
2. **Ubica el archivo APK generado:**
   ```text
   dopa/build/app/outputs/flutter-apk/app-release.apk
   ```
3. **Instálalo en el celular:**
   - **Por cable USB (ADB):** `adb install build/app/outputs/flutter-apk/app-release.apk`
   - **Por WhatsApp / Google Drive / Cable:** Envía el archivo `app-release.apk` al teléfono, ábrelo y acepta *"Instalar aplicaciones de orígenes desconocidos"*.

---

### Opción 3: Emulador Android (Android Virtual Device - AVD)

Si deseas probar la experiencia móvil desde tu PC sin conectar un teléfono físico:

1. Abre **Android Studio > Device Manager** e inicia cualquier emulador Android (o créalo desde el panel Android Device Hub).
2. En Android, la IP especial `10.0.2.2` apunta automáticamente al `localhost` de tu computador. El archivo [`lib/services/api_service.dart`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/lib/services/api_service.dart) **ya está preconfigurado por defecto** para usar `http://10.0.2.2:8000/api/v1` cuando detecta Android.
3. Ejecuta:
   ```powershell
   cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
   flutter run
   ```

---

### Opción 4: Conexión desde Cualquier Red Móvil (4G/5G) usando un Túnel HTTPS (Ngrok o Cloudflare Tunnel)

Si tu celular usa datos móviles (4G/5G) o está en una red Wi-Fi distinta a la de tu PC (o con aislamiento de clientes AP), puedes exponer tu backend local mediante un túnel seguro HTTPS:

1. Con el backend corriendo en el puerto `8000`, abre otra terminal y ejecuta:
   ```powershell
   ngrok http 8000
   ```
   *(O con Cloudflare: `cloudflared tunnel --url http://localhost:8000`)*.
2. Copia la URL HTTPS generada (ej. `https://a1b2-c3d4.ngrok-free.app`).
3. Ejecuta o compila la app para el celular apuntando a esa URL:
   ```powershell
   flutter run --dart-define=API_BASE_URL=https://a1b2-c3d4.ngrok-free.app/api/v1
   ```

---

### Opción 5: Progressive Web App (PWA) Instalable en Android e iOS (iPhone) — *Sin Cables ni Compilación*

Dado que el contenedor `frontend` en Docker sirve Flutter Web optimizado con manifiesto PWA y proxy inverso Nginx hacia el backend:

1. Levanta el stack con Docker (`docker compose up -d --build`).
2. Desde el navegador de tu celular (**Chrome en Android** o **Safari en iPhone**) conectado al mismo Wi-Fi, entra a:
   ```text
   http://<IP_DE_TU_PC>:3000
   ```
   *(Ejemplo: `http://192.168.1.50:3000`)*.
3. En el menú del navegador móvil, selecciona **"Agregar a la pantalla de inicio"** (*Add to Home Screen*).
4. Se instalará el ícono de **DOPA** en tu celular y abrirá a pantalla completa como una aplicación nativa. Además, gracias al proxy inverso en [`nginx.conf`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/nginx.conf), todas las peticiones a `/api/v1` se enrutan automáticamente al backend sin problemas de CORS ni configuración adicional.

---

### Opción 6: Dispositivo Físico iPhone (iOS) Nativo

Para compilar un binario nativo `.ipa` para iPhone:
1. Se requiere un equipo con **macOS y Xcode** (restricción oficial de Apple para firmar binarios iOS).
2. Abre `ios/Runner.xcworkspace` en Xcode, selecciona tu cuenta gratuita de Apple ID en *Signing & Capabilities*, y ejecuta:
   ```bash
   flutter run --dart-define=API_BASE_URL=http://<IP_MAC>:8000/api/v1
   ```
   *(Si trabajas desde Windows y tienes un iPhone, utiliza la **Opción 5 (PWA en Safari)** o un servicio CI/CD como Codemagic).*

---

## 🧪 4. Ejecución de Pruebas Automatizadas (Testing & QA)

### 4.1 Pruebas del Backend (PyTest + Cobertura)
El backend cuenta con **30 pruebas automatizadas** (unitarias de seguridad JWT/Bcrypt y de integración para los 9 módulos REST) con **99% de cobertura**.

```powershell
cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
.\.venv\Scripts\python.exe -m pytest -v
```

### 4.2 Análisis Estático y Pruebas del Frontend (Flutter Test)
El frontend cuenta con pruebas de integración de widgets y cliente HTTP simulado (`MockClient`) en [`test/widget_test.dart`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/test/widget_test.dart):

```powershell
cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"

# Análisis estático de código (0 errores / 0 warnings)
flutter analyze

# Ejecución de pruebas de UI e integración con API
flutter test --reporter expanded
```

---

## 🌐 5. Despliegue en Servidor de Producción (VPS / Cloud)

El proyecto está listo para desplegarse en cualquier servidor Linux (Ubuntu/Debian en AWS EC2, DigitalOcean, Google Cloud, Hetzner o Azure) utilizando Docker Compose.

### Paso 1: Preparar el Servidor e Instalar Docker
Conéctate por SSH a tu servidor e instala Docker y Git:
```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

### Paso 2: Clonar el Proyecto en el Servidor
```bash
git clone <URL_DE_TU_REPOSITORIO> dopa
cd dopa
```

### Paso 3: Configurar Variables de Entorno Seguras (`.env`)
Crea el archivo `.env` de producción a partir de `.env.example`:
```bash
cp .env.example .env
nano .env
```
Asegúrate de personalizar las credenciales críticas para producción:
```env
APP_ENV=production
POSTGRES_USER=dopa_prod_user
POSTGRES_PASSWORD=UnaPasswordMuySegura2026!
POSTGRES_DB=dopa_db
DATABASE_URL=postgresql+psycopg://dopa_prod_user:UnaPasswordMuySegura2026!@db:5432/dopa_db
JWT_SECRET_KEY=genera_una_clave_hexadecimal_de_64_caracteres_con_openssl_rand_hex_32
CORS_ORIGINS=["https://tu-dominio.com"]
```

### Paso 4: Desplegar los Servicios con Docker Compose
Levanta únicamente los servicios de producción (`db`, `backend` y `frontend`, omitiendo `pgadmin` si no se requiere públicamente):
```bash
docker compose up -d --build db backend frontend
```

### Paso 5: Configurar Dominio y Certificado SSL/HTTPS (Opcional pero Recomendado)
Si cuentas con un dominio (ej. `app.tudominio.com`), puedes colocar **Caddy** o **Nginx + Certbot (Let's Encrypt)** en el puerto `80`/`443` del host redirigiendo a `http://127.0.0.1:3000`:

Con **Caddy** (SSL automático en 2 líneas en `/etc/caddy/Caddyfile`):
```caddyfile
app.tudominio.com {
    reverse_proxy localhost:3000
}
```
Como el contenedor `frontend` ya tiene configurado el bloque `location /api/` en [`nginx.conf`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/nginx.conf) hacia `http://backend:8000`, tanto la aplicación Web/PWA como tu aplicación móvil compilada con:
```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://app.tudominio.com/api/v1
```
funcionarán bajo el mismo dominio seguro HTTPS (`https://app.tudominio.com`).

---

## 🛠️ 6. Comandos Útiles de Mantenimiento

| Acción | Comando |
|---|---|
| Ver logs en tiempo real del Backend | `docker compose logs -f backend` |
| Ver logs de la Base de Datos | `docker compose logs -f db` |
| Reiniciar servicios tras cambios de código | `docker compose up -d --build` |
| Detener contenedores conservando datos | `docker compose down` |
| Reiniciar la Base de Datos desde cero (`init.sql`) | `docker compose down -v && docker compose up -d --build` |
