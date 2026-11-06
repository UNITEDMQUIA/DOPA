# Proyecto DOPA — Backend FastAPI, PostgreSQL & QA (TDAH)

Backend completo diseñado y construido mediante el ecosistema multi-agente especificado en [stack_de_agentes_de_desarrollo_front_back_qa.md](file:///C:/Users/salas/Desktop/Proyecto/stack_de_agentes_de_desarrollo_front_back_qa.md), implementando el modelo de datos y arquitectura de 5 capas de [PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf](file:///C:/Users/salas/Desktop/Proyecto/PLANEACI%C3%93N%20Y%20DISE%C3%91O%20DE%20SOFTWARE%20(1).pdf) y los flujos y pantallas de [Parcial 2.pdf](file:///C:/Users/salas/Desktop/Proyecto/Parcial%202.pdf).

---

## 1. Arquitectura Multi-Agente Ejecutada

| Agente | Rol | Entregables Principales |
| :--- | :--- | :--- |
| **1. Agente Orquestador** | Tech Lead / Product Manager | [API_CONTRACT.md](file:///C:/Users/salas/Desktop/Proyecto/docs/API_CONTRACT.md) |
| **3.1. Agente Arquitecto de Datos** | Database & ORM (PostgreSQL + SQLAlchemy) | [docker-compose.yml](file:///C:/Users/salas/Desktop/Proyecto/docker-compose.yml), [init.sql](file:///C:/Users/salas/Desktop/Proyecto/database/init.sql), [ER_DIAGRAM.md](file:///C:/Users/salas/Desktop/Proyecto/database/ER_DIAGRAM.md), [models.py](file:///C:/Users/salas/Desktop/Proyecto/app/domain/models.py), [database.py](file:///C:/Users/salas/Desktop/Proyecto/app/data/database.py) |
| **3.2. Agente de API y Lógica Backend** | FastAPI 5-Layer Architecture | [main.py](file:///C:/Users/salas/Desktop/Proyecto/app/main.py), [services.py](file:///C:/Users/salas/Desktop/Proyecto/app/core/services.py), [security.py](file:///C:/Users/salas/Desktop/Proyecto/app/core/security.py), [repositories.py](file:///C:/Users/salas/Desktop/Proyecto/app/data/repositories.py), [dtos.py](file:///C:/Users/salas/Desktop/Proyecto/app/transfer/dtos.py), [mappers.py](file:///C:/Users/salas/Desktop/Proyecto/app/transfer/mappers.py), [routers](file:///C:/Users/salas/Desktop/Proyecto/app/presentation/routers) |
| **4. Stack de Agentes de QA y SecOps** | Unit, Integration, E2E & Security Testing | [test_unit_services_and_mappers.py](file:///C:/Users/salas/Desktop/Proyecto/tests/test_unit_services_and_mappers.py), [test_api_endpoints.py](file:///C:/Users/salas/Desktop/Proyecto/tests/test_api_endpoints.py), [test_e2e_user_flows.py](file:///C:/Users/salas/Desktop/Proyecto/tests/test_e2e_user_flows.py), [test_security_and_perf.py](file:///C:/Users/salas/Desktop/Proyecto/tests/test_security_and_perf.py), [QA_SECURITY_REPORT.md](file:///C:/Users/salas/Desktop/Proyecto/docs/QA_SECURITY_REPORT.md) |

---

## 2. Levantar Base de Datos PostgreSQL y Backend con Docker Compose

Con **Docker Desktop** activo, ejecuta en la raíz del proyecto:

```powershell
# Levantar PostgreSQL 16 (con init.sql montado automáticamente), pgAdmin y el Backend FastAPI
docker compose up -d --build

# Si deseas levantar únicamente la base de datos PostgreSQL:
docker compose up -d db
```

### Servicios Expuestos en Docker:
- **PostgreSQL 16 (`dopa_postgres_db`)**: `localhost:5432`
  - Base de datos: `dopa_db`
  - Usuario: `dopa_user`
  - Contraseña: `dopa_pass`
  - Script de inicialización automático: `database/init.sql` (crea los tipos ENUM `prioridad_tarea` y `tipo_recordatorio`, las 10 tablas relacionales, los 14 índices y los seeders de `Fred` y `Paula`).
- **Backend FastAPI (`dopa_fastapi_backend`)**: `http://localhost:8000`
  - Documentación interactiva Swagger UI: `http://localhost:8000/docs`
  - Documentación ReDoc: `http://localhost:8000/redoc`
- **pgAdmin 4 (`dopa_pgadmin`)**: `http://localhost:5050` (`admin@dopa.app` / `admin123`)

---

## 3. Ejecución Local del Backend y Suite de Pruebas QA

```powershell
# 1. Ejecutar el servidor FastAPI localmente
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# 2. Ejecutar la suite completa de QA (Unitarias, Integración, E2E y Seguridad) con reporte de cobertura
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing -v
```
