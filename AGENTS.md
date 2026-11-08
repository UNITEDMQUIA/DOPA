# Ecosistema Multi-Agente DOPA (SDLC)

Este proyecto cuenta con un ecosistema multi-agente para el ciclo de vida del desarrollo de software (SDLC), documentado en detalle en [`framework_multi_agente_para_sdlc.md`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/framework_multi_agente_para_sdlc.md) y [`stack_de_agentes_de_desarrollo_front_back_qa.md`](file:///c:/Users/Santiago%20Orjuela/Documents/Proyecto/dopa/stack_de_agentes_de_desarrollo_front_back_qa.md).

## Agentes Configurados

1. **`Agent_Orchestrator`** (Tech Lead & Gobernanza Técnica)
   - Supervisa el flujo DAG, compuertas de calidad (Quality Gates) y dependencias entre agentes.
2. **`Agent_PM`** (Product Manager & Business Analyst)
   - Transforma requerimientos en PRDs, Historias de Usuario y Criterios Gherkin.
3. **`Agent_Architect`** (Arquitecto de Software)
   - Diseña especificaciones OpenAPI, modelos de base de datos (PostgreSQL), diagramas C4 y ADRs.
4. **`Agent_UXUI`** (Diseñador UI/UX)
   - Flujos de navegación, máquinas de estado de pantalla, diseño atómico y accesibilidad (WCAG).
5. **`Agent_Backend`** (Ingeniero Backend)
   - FastAPI, SQLAlchemy, PostgreSQL, Clean Architecture (5 capas), principios SOLID y cobertura >85%.
6. **`Agent_Frontend`** (Ingeniero Frontend)
   - Flutter, widgets accesibles, manejo de estado y consumo de contratos de API.
7. **`Agent_QA`** (Aseguramiento de Calidad)
   - PyTest, contratos de API, pruebas unitarias, de integración, E2E y Quality Gates.
8. **`Agent_SecOps`** (Seguridad de Aplicaciones)
   - Análisis OWASP Top 10, detección de secretos y análisis de vulnerabilidades en dependencias.
9. **`Agent_DevOps`** (DevOps & SRE)
   - Docker, docker-compose, CI/CD y despliegue.

## Protocolo de Comunicación
Los agentes interactúan a través de artefactos estandarizados en el repositorio (`docs/`, `database/`, `app/`, `lib/`, `tests/` y `test/`).
