# 🧠 DOPA — Gestión de Energía, Enfoque Suave y Bienestar Diario

**DOPA** es una plataforma integral (Móvil Android/iOS + Web/PWA + API RESTful en FastAPI + PostgreSQL 16) diseñada para personas con TDAH y perfiles neurodivergentes que buscan gestionar sus tareas diarias según su nivel de energía, mantener sesiones de enfoque suave (*Soft Focus* / Pomodoro) y celebrar su progreso mediante gamificación libre de culpa.

---

## 📚 Documentación Principal del Proyecto

Toda la documentación técnica, arquitectónica y operativa se encuentra organizada en los siguientes documentos:

1. 🏗️ **[Estructura del Proyecto (`ESTRUCTURA_DEL_PROYECTO.md`)](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/ESTRUCTURA_DEL_PROYECTO.md)**
   Explicación detallada del árbol de directorios unificado, arquitectura por capas del Frontend (Flutter) y Backend (FastAPI), modelo de base de datos PostgreSQL (11 tablas), mapeo completo de endpoints y flujos de integración.
2. 🚀 **[Guía de Inicio, Ejecución Móvil y Despliegue (`GUIA_INICIO_Y_DESPLIEGUE.md`)](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/GUIA_INICIO_Y_DESPLIEGUE.md)**
   Instrucciones paso a paso para levantar el proyecto en local (con Docker o manual), las **6 opciones para correr el aplicativo en un celular**, ejecución de pruebas (PyTest + Flutter Test) y despliegue en servidor de producción.
3. 📡 **[Contrato de API REST (`docs/API_CONTRACT.md`)](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/docs/API_CONTRACT.md)**
   Especificación de los endpoints `/api/v1/*`, payloads JSON y códigos de respuesta.
4. 🤖 **[Configuración del Equipo de Agentes SDLC (`AGENTS.md`)](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/AGENTS.md)**
   Definición de los 9 agentes especializados (`Agent_Orchestrator`, `Agent_PM`, `Agent_Architect`, `Agent_UXUI`, `Agent_Backend`, `Agent_Frontend`, `Agent_QA`, `Agent_SecOps`, `Agent_DevOps`).

---

## ⚡ Inicio Rápido

### Con Docker Compose (Base de Datos + Backend + Frontend Web)
```powershell
cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
docker compose up -d --build
```
- **Frontend Web / PWA:** http://localhost:3000
- **API Backend (Swagger UI):** http://localhost:8000/docs
- **pgAdmin 4:** http://localhost:5050
- **Credenciales Demo:** `fred@dopa.app` / `Dopa1234!`

### Ejecutar en un Celular Android (Conectado a la misma red Wi-Fi)
```powershell
cd "C:\Users\Santiago Orjuela\Documents\Proyecto\dopa"
flutter run --dart-define=API_BASE_URL=http://<IP_LOCAL_DE_TU_PC>:8000/api/v1
```
*(Consulta [`GUIA_INICIO_Y_DESPLIEGUE.md`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/GUIA_INICIO_Y_DESPLIEGUE.md) para ver todas las opciones móviles: USB/ADB, generación de APK instalable, Emulador Android `10.0.2.2`, Túnel HTTPS Ngrok y PWA en Android/iPhone).*

### Ejecutar Suite de Pruebas (Testing)
```powershell
# Backend (PyTest + Coverage)
.\.venv\Scripts\python.exe -m pytest -v

# Frontend (Análisis estático + Widget/API Tests)
flutter analyze
flutter test
```
