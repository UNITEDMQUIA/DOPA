# Arquitectura de Datos y Diagrama Entidad-Relación (PostgreSQL) — Proyecto DOPA

> **Agente Responsable:** `3.1. Agente Arquitecto de Datos (Database & ORM Agent)`  
> **Fuente de Verdad:** `PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf` — Sección 4.3 (Páginas 50-56) y `Parcial 2.pdf`

---

## 1. Diagrama Entidad-Relación (Mermaid.js)

El esquema relacional consta exactamente de **10 tablas** y **2 tipos `ENUM` personalizados** en PostgreSQL (`prioridad_tarea` y `tipo_recordatorio`), manteniendo total fidelidad con los nombres de tablas y columnas definidos en el documento de Planeación y Diseño.

```mermaid
erDiagram
    USUARIO ||--o{ RUTINA : "crea y gestiona (1:N)"
    USUARIO ||--o{ TAREA : "asigna y completa (1:N)"
    USUARIO ||--o{ SESIONPOMODORO : "ejecuta enfoque (1:N)"
    USUARIO ||--o{ RECORDATORIO : "programa alertas (1:N)"
    USUARIO ||--o{ REGISTROPERSONAL : "registra bienestar (1:N)"
    USUARIO ||--o{ METAFINANCIERA : "define metas (1:N)"
    USUARIO ||--o{ PANELPRINCIPAL : "consulta resumen (1:N)"

    RUTINA |o--o{ TAREA : "agrupa hábitos (0..1:N)"
    TAREA ||--o{ SUBTAREA : "divide en micro-pasos (1:N)"
    TAREA |o--o{ SESIONPOMODORO : "vincula temporizador (0..1:N)"
    TAREA |o--o{ RECORDATORIO : "notifica vencimiento (0..1:N)"
    TAREA |o--o{ RECOMPENSA : "otorga dopamina (0..1:N)"

    USUARIO {
        int4 id PK "SERIAL PRIMARY KEY"
        varchar(120) nombre "NOT NULL"
        varchar(150) correo "UNIQUE NOT NULL"
        varchar(255) contrasenahash "NOT NULL"
        int4 puntos "NOT NULL DEFAULT 0"
        int4 nivel "NOT NULL DEFAULT 1"
    }

    RUTINA {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_usuario FK "NOT NULL -> usuario.id"
        varchar(150) nombre "NOT NULL"
        varchar(100) recurrencia "NOT NULL"
        time hora "NOT NULL"
        bool completadahoy "NOT NULL DEFAULT FALSE"
    }

    TAREA {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_usuario FK "NOT NULL -> usuario.id"
        int4 id_rutina FK "NULL -> rutina.id"
        varchar(200) titulo "NOT NULL"
        text descripcion "NULL"
        prioridad_tarea prioridad "ENUM('Alta','Media','Baja')"
        date fechavencimiento "NULL"
        bool completada "NOT NULL DEFAULT FALSE"
    }

    SUBTAREA {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_tarea FK "NOT NULL -> tarea.id"
        varchar(255) descripcion "NOT NULL"
        bool completada "NOT NULL DEFAULT FALSE"
    }

    SESIONPOMODORO {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_usuario FK "NOT NULL -> usuario.id"
        int4 id_tarea FK "NULL -> tarea.id"
        int4 duracionconcentracion "NOT NULL"
        int4 duraciondescanso "NOT NULL"
        int4 sesionescompletadas "NOT NULL DEFAULT 0"
    }

    RECORDATORIO {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_usuario FK "NOT NULL -> usuario.id"
        int4 id_tarea FK "NULL -> tarea.id"
        timestamp fechahora "NOT NULL"
        varchar(255) mensaje "NOT NULL"
        tipo_recordatorio tipo "ENUM('Tarea','Rutina','Compromiso')"
        bool completadahoy "NOT NULL DEFAULT FALSE"
    }

    RECOMPENSA {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_tarea FK "NULL -> tarea.id"
        varchar(150) nombre "NOT NULL"
        int4 costopuntos "NOT NULL DEFAULT 10"
        bool desbloqueada "NOT NULL DEFAULT FALSE"
    }

    REGISTROPERSONAL {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_usuario FK "NOT NULL -> usuario.id"
        varchar(120) nombre "NOT NULL"
        numeric(10_2) valorobjetivo "NOT NULL"
        numeric(10_2) valoractual "NOT NULL"
        numeric(5_2) progresoporcentaje "NOT NULL DEFAULT 0"
    }

    METAFINANCIERA {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_usuario FK "NOT NULL -> usuario.id"
        varchar(150) nombre "NOT NULL"
        numeric(12_2) valorobjetivo "NOT NULL"
        numeric(12_2) valoractual "NOT NULL DEFAULT 0"
        numeric(5_2) progresoporcentaje "NOT NULL DEFAULT 0"
    }

    PANELPRINCIPAL {
        int4 id PK "SERIAL PRIMARY KEY"
        int4 id_usuario FK "NOT NULL -> usuario.id"
        date fechaactual "NOT NULL DEFAULT CURRENT_DATE"
    }
```

---

## 2. Tipos Enumerados (`ENUM`) en PostgreSQL

| Tipo PostgreSQL | Valores Permitidos | Tabla y Columna Destino | Requerimiento Asociado |
| :--- | :--- | :--- | :--- |
| `prioridad_tarea` | `'Alta'`, `'Media'`, `'Baja'` | `tarea.prioridad` | `RF-03`, `HU-02` |
| `tipo_recordatorio` | `'Tarea'`, `'Rutina'`, `'Compromiso'` | `recordatorio.tipo` | `RF-08`, `HU-05` |

---

## 3. Reglas de Integridad Referencial y Normalización (3FN)

1. **Eliminación en Cascada (`ON DELETE CASCADE`)**:
   - Cuando se elimina un `usuario`, se eliminan sus registros dependientes (`rutina`, `tarea`, `sesionpomodoro`, `recordatorio`, `registropersonal`, `metafinanciera`, `panelprincipal`).
   - Cuando se elimina una `tarea`, se eliminan automáticamente todas sus `subtarea` (micro-pasos) y sus `recordatorio` asociados.
2. **Desvinculación Segura (`ON DELETE SET NULL`)**:
   - Si se elimina una `rutina`, las tareas asociadas (`tarea.id_rutina`) permanecen en el sistema como tareas independientes (`id_rutina = NULL`).
   - Si se elimina una `tarea`, el historial de `sesionpomodoro` y las `recompensa` desbloqueadas conservan su validez histórica poniendo `id_tarea = NULL`, protegiendo los puntos y logros del usuario (`RF-16`, gamificación libre de culpa).
3. **Restricciones de Dominio (`CHECK`)**:
   - `usuario.puntos >= 0` y `usuario.nivel >= 1`: garantiza a nivel de motor de base de datos que jamás se resten puntos por debajo de cero ni se degrade el nivel del usuario (`HU-11`, `RF-16`).

---

## 4. Estrategia de Indexación y Rendimiento (`RNF-04` y `RNF-17`)

- `idx_usuario_correo`: Acelera el inicio de sesión (`POST /api/v1/auth/login`) en tiempo $O(\log n)$.
- `idx_tarea_usuario_estado_prioridad`: Índice compuesto sobre `(id_usuario, completada, prioridad)` para alimentar instantáneamente el Dashboard (`GET /api/v1/dashboard`) y el botón *"¡Hacer algo fácil!"* (`GET /api/v1/dashboard/quick-task`).
- `idx_subtarea_tarea`: Optimiza la carga de micro-pasos (`GET /api/v1/tasks/{id}`) para la pantalla *"Enfoque suave"*.
- `idx_recordatorio_usuario_fechahora`: Optimiza la consulta de próximas alertas activas ordenadas cronológicamente.
- `idx_panelprincipal_usuario_fecha`: Optimiza la consulta y actualización del snapshot diario del panel principal.
