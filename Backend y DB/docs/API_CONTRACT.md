# Contrato de la API y Especificación Técnica — Proyecto DOPA (TDAH)

> **Emitido por:** `1. Agente Orquestador (Tech Lead / Product Manager Agent)`  
> **Regla Clave Aplicada:** *"Nunca permitas que el Frontend o el Backend comiencen a programar sin antes haber acordado y documentado el contrato de la API."*  
> **Documentos Base:** `PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf` y `Parcial 2.pdf`

---

## 1. Visión General y Reglas de Arquitectura

La aplicación **DOPA** está orientada a personas con TDAH para disminuir la fricción ejecutiva diaria ("Vamos un paso a la vez", "Poquito a poquito"). El Backend se construye en **Python + FastAPI** conectado a **PostgreSQL**, respetando estrictamente la **Arquitectura en 5 Capas** definida en la Sección 4.2 del documento de Planeación y Diseño:

1. **Capa de Presentación (`app/presentation/`)**: Controladores REST versionados bajo `/api/v1/*` y `Security Middleware / Dependency` con autenticación **Stateless JWT** (Access Token de corta duración + Refresh Token de larga duración).
2. **Capa de Transferencia y Mapeo (`app/transfer/`)**: `RequestDTO` y `ResponseDTO` optimizados para payloads móviles ligeros y `Mappers` bidireccionales entre `Entities` y `DTOs`.
3. **Capa de Lógica de Negocio (`app/core/`)**: Contratos/Interfaces e implementaciones de `Services` con **idempotencia** (evitando duplicar puntos de dopamina ante reintentos por microcortes de red) y **gamificación libre de culpa** (nunca se restan puntos ni niveles por inactividad: `RF-16`, `HU-11`).
4. **Capa de Acceso a Datos (`app/data/`)**: `Repositories` transaccionales con soporte de **paginación** (`limit` / `offset`).
5. **Capa de Dominio (`app/domain/`)**: `Entities` SQLAlchemy que mapean exactamente las 10 tablas y los 2 tipos `ENUM` del esquema relacional en PostgreSQL (`Sección 4.3`).

---

## 2. Mapeo de Historias de Usuario, Requerimientos y Pantallas (`Parcial 2.pdf`)

| Módulo | Historias / RF | Pantallas (`Parcial 2.pdf`) | Tablas PostgreSQL | Prefijo Endpoint |
| :--- | :--- | :--- | :--- | :--- |
| **Autenticación y Perfil** | HU-01, HU-12, RF-01, RF-02, RF-23 | Fig. 1 (Wireframe Login DOPA) | `usuario` | `/api/v1/auth` |
| **Panel Principal (Inicio)** | HU-10, RF-22 | Fig. 2 (Dashboard), Fig. 7 (Mockup Inicio "¡Hola, Fred!") | `panelprincipal`, `usuario`, `tarea`, `rutina`, `recordatorio` | `/api/v1/dashboard` |
| **Tareas y Micro-pasos** | HU-02, HU-03, RF-03, RF-04, RF-05 | Fig. 3 (Prepara práctica), Fig. 8 (Mis tareas "Poquito a poquito"), Fig. 9 (Enfoque suave / Micro-pasos), Fig. 10 ("¡Lo hiciste, Fred!") | `tarea`, `subtarea` | `/api/v1/tasks` |
| **Rutinas Libres de Culpa** | HU-04, HU-11, RF-06, RF-07, RF-24 | Fig. 2 ("Mi rutina de hoy"), Fig. 5 ("Volver a la rutina") | `rutina`, `tarea` | `/api/v1/routines` |
| **Enfoque Pomodoro y Pausa** | HU-06, RF-10, RF-11, RF-12 | Fig. 4 (Rutina 5 min), Fig. 9 (Temporizador 05:00), Fig. 12 y 13 ("Un break suave: 5 min / 10 min, Respiración 4-4, Estiramiento") | `sesionpomodoro` | `/api/v1/pomodoro` |
| **Recordatorios** | HU-05, RF-08, RF-09 | Fig. 2 (Icono campana / alertas) | `recordatorio` | `/api/v1/reminders` |
| **Gamificación (Dopamina)** | HU-07, RF-13, RF-14, RF-15, RF-16 | Fig. 5, Fig. 6 (Historial bienestar 32 pts), Fig. 10 (+10 dopamina), Fig. 11 ("Mi Dopamina hoy", Rachas) | `usuario`, `recompensa` | `/api/v1/gamification` |
| **Seguimiento Personal** | HU-08, RF-17, RF-18, RF-19 | Fig. 6 (Energía, Ánimo, Sueño 6.8h), Fig. 11 ("Mi humor": Abrumado, Inquieto, Con foco, Tranquilo) | `registropersonal` | `/api/v1/personal-records` |
| **Metas Financieras** | HU-09, RF-20, RF-21 | Módulo de Metas Financieras | `metafinanciera` | `/api/v1/financial-goals` |

---

## 3. Especificación de Endpoints (`/api/v1`)

### 3.1. Módulo de Autenticación y Preferencias (`/api/v1/auth`)
- `POST /api/v1/auth/register` (`201 Created`): Registra un nuevo usuario (`nombre`, `correo`, `contrasena`). Valida unicidad de correo y almacena hash seguro (`RNF-06`). Inicializa `puntos=0`, `nivel=1`.
- `POST /api/v1/auth/login` (`200 OK`): Autentica con `correo` y `contrasena`. Retorna `access_token`, `refresh_token`, `token_type="bearer"` y resumen del usuario.
- `POST /api/v1/auth/refresh` (`200 OK`): Recibe `refresh_token` y emite un nuevo `access_token`.
- `POST /api/v1/auth/logout` (`200 OK`): Cierra la sesión activa.
- `GET /api/v1/auth/me` (`200 OK`): Retorna el perfil del usuario autenticado (`id`, `nombre`, `correo`, `puntos`, `nivel`, `preferencias`).
- `PUT /api/v1/auth/preferences` (`200 OK`): Actualiza preferencias de usuario (`HU-12`, `RF-23`: duración de concentración/descanso por defecto, notificaciones activas, tema visual).

### 3.2. Módulo de Panel Principal / Inicio (`/api/v1/dashboard`)
- `GET /api/v1/dashboard` (`200 OK`): Registra/actualiza el snapshot diario en `panelprincipal` (`fechaactual`) y retorna el payload consolidado para la pantalla de Inicio (Figuras 2 y 7):
  - Saludo personalizado (`¡Hola, {nombre}!`), `puntos` de dopamina y `nivel`.
  - Estado de energía del día (`poquita`, `media`, `a tope`).
  - Micro-tareas pendientes prioritarias y contador (`pendientes`, `completadas_hoy`, `total_hoy`).
  - Rutinas programadas para hoy y recordatorios próximos.
- `POST /api/v1/dashboard/energy-checkin` (`201 Created`): Registra el chequeo diario "¿Cómo está tu energía hoy?" (Figuras 2 y 7) guardando la métrica en `registropersonal`.
- `GET /api/v1/dashboard/quick-task` (`200 OK`): Botón "¡Hacer algo fácil!" / "Haz la tarea más corta" (Figuras 3 y 7). Retorna la tarea pendiente de menor fricción para empezar de inmediato.

### 3.3. Módulo de Gestión de Tareas y Micro-pasos (`/api/v1/tasks`)
- `GET /api/v1/tasks` (`200 OK`): Lista tareas del usuario autenticado con paginación (`limit`, `offset`) y filtros opcionales (`completada`, `prioridad`, `id_rutina`). Incluye resumen `"Poquito a poquito"` (`completadas / total`, Figura 8).
- `POST /api/v1/tasks` (`201 Created`): Crea una tarea (`titulo`, `descripcion`, `prioridad` [`Alta`, `Media`, `Baja`], `fechavencimiento`, `id_rutina` opcional, y lista opcional de `subtareas`).
- `GET /api/v1/tasks/{task_id}` (`200 OK`): Obtiene el detalle de la tarea con sus `subtareas` (micro-pasos, Figura 9).
- `PUT /api/v1/tasks/{task_id}` (`200 OK`): Edita campos de una tarea.
- `DELETE /api/v1/tasks/{task_id}` (`204 No Content`): Elimina la tarea y sus subtareas en cascada (`ON DELETE CASCADE`).
- `POST /api/v1/tasks/{task_id}/complete` (`200 OK`): Marca la tarea como completada (`Figura 10: ¡Lo hiciste! +10 dopamina`). **Operación idempotente**: si la tarea ya estaba completada o se envía el mismo `Idempotency-Key`, retorna el estado actual sin duplicar los puntos de dopamina. Desbloquea automáticamente recompensas vinculadas a la tarea o al nuevo puntaje.
- `POST /api/v1/tasks/{task_id}/subtasks` (`201 Created`): Crea un micro-paso (`subtarea`) dentro de la tarea (`HU-03`, `RF-05`).
- `GET /api/v1/tasks/{task_id}/subtasks` (`200 OK`): Lista los micro-pasos de la tarea y el porcentaje de avance de pasos.
- `PATCH /api/v1/tasks/{task_id}/subtasks/{subtask_id}` (`200 OK`): Actualiza o marca como completado (`completada=true/false`) un micro-paso individual (Figura 9).
- `DELETE /api/v1/tasks/{task_id}/subtasks/{subtask_id}` (`204 No Content`): Elimina un micro-paso.

### 3.4. Módulo de Rutinas y Hábitos (`/api/v1/routines`)
- `GET /api/v1/routines` (`200 OK`): Lista paginada de rutinas del usuario.
- `POST /api/v1/routines` (`201 Created`): Crea una rutina (`nombre`, `recurrencia`, `hora`).
- `GET /api/v1/routines/{routine_id}` (`200 OK`): Consulta una rutina con sus tareas asociadas.
- `PUT /api/v1/routines/{routine_id}` (`200 OK`): Edita una rutina.
- `DELETE /api/v1/routines/{routine_id}` (`204 No Content`): Elimina una rutina.
- `POST /api/v1/routines/{routine_id}/complete-today` (`200 OK`): Marca `completadahoy=true` y otorga puntos de dopamina (idempotente).
- `POST /api/v1/routines/{routine_id}/resume` (`200 OK`): Retoma una rutina tras días de inactividad (`HU-11`, `RF-16`, `RF-24`), reiniciando únicamente la bandera diaria `completadahoy=false` para el nuevo día **sin restar puntos, nivel ni recompensas**.

### 3.5. Módulo de Enfoque Pomodoro y Descanso (`/api/v1/pomodoro`)
- `POST /api/v1/pomodoro/sessions` (`201 Created`): Crea una sesión en `sesionpomodoro` (`id_tarea` opcional, `duracionconcentracion` ej. 5 o 25 min, `duraciondescanso` ej. 5 o 10 min).
- `GET /api/v1/pomodoro/sessions` (`200 OK`): Lista sesiones de enfoque del usuario.
- `POST /api/v1/pomodoro/sessions/{session_id}/complete` (`200 OK`): Registra un ciclo completado (`sesionescompletadas += 1`) y otorga `+5` puntos de dopamina (`RF-12`, `RF-13`). Soporta `Idempotency-Key`.
- `POST /api/v1/pomodoro/sessions/{session_id}/cancel` (`200 OK`): Cancela la sesión en curso sin incrementar `sesionescompletadas` ni otorgar puntos (`HU-06` comportamiento adverso).
- `GET /api/v1/pomodoro/low-stimulus-activities` (`200 OK`): Retorna las actividades guiadas de bajo estímulo para el panel de descanso ("Un break suave", Figuras 4 y 13: *Respiración 4-4*, *Estiramiento suave*, *Cierra con gratitud*).

### 3.6. Módulo de Recordatorios (`/api/v1/reminders`)
- `GET /api/v1/reminders` (`200 OK`): Lista recordatorios del usuario (filtrables por `tipo` [`Tarea`, `Rutina`, `Compromiso`] y `completadahoy`).
- `POST /api/v1/reminders` (`201 Created`): Crea un recordatorio (`fechahora`, `mensaje`, `tipo`, `id_tarea` opcional).
- `PUT /api/v1/reminders/{reminder_id}` (`200 OK`): Actualiza un recordatorio o lo marca como `completadahoy=true` (desactivado para no seguir enviando notificaciones, `HU-05`).
- `DELETE /api/v1/reminders/{reminder_id}` (`204 No Content`): Elimina un recordatorio.

### 3.7. Módulo de Gamificación y Dopamina (`/api/v1/gamification`)
- `GET /api/v1/gamification/summary` (`200 OK`): Datos para la pantalla `"Mi Dopamina hoy"` y `"Historial de bienestar"` (Figuras 6 y 11):
  - `puntos_totales`, `nivel`, `meta_diaria_puntos` (ej. 50 pts), `porcentaje_meta`.
  - Progreso hacia el siguiente nivel (`1 nivel cada 50 puntos`).
  - Resumen semanal libre de culpa y conteo de recompensas desbloqueadas.
- `GET /api/v1/gamification/rewards` (`200 OK`): Lista todas las recompensas (`recompensa`) y su estado `desbloqueada`.
- `POST /api/v1/gamification/rewards` (`201 Created`): Registra una nueva recompensa (`nombre`, `costopuntos`, `id_tarea` opcional).
- `POST /api/v1/gamification/rewards/{reward_id}/unlock` (`200 OK`): Desbloquea una recompensa si el usuario cumple el requisito de puntos o completó la tarea asociada (`RF-15`).

### 3.8. Módulo de Seguimiento Personal: Sueño y Humor (`/api/v1/personal-records`)
- `GET /api/v1/personal-records` (`200 OK`): Lista los registros personales (`registropersonal`) del usuario autenticado (`RNF-09` privacidad estricta) y devuelve tendencias básicas sin emitir diagnósticos médicos (`HU-08` comportamiento adverso).
- `POST /api/v1/personal-records` (`201 Created`): Crea un registro personal (ej. `nombre="Horas de sueño"`, `valorobjetivo=8.0`, `valoractual=6.8` o `nombre="Estado emocional: Con foco"`, `valorobjetivo=5`, `valoractual=4`). Calcula automáticamente `progresoporcentaje = (valoractual / valorobjetivo) * 100`.
- `PUT /api/v1/personal-records/{record_id}` (`200 OK`): Actualiza `valoractual` / `valorobjetivo` y recalcula `progresoporcentaje`.
- `DELETE /api/v1/personal-records/{record_id}` (`204 No Content`): Elimina un registro personal.

### 3.9. Módulo de Metas Financieras (`/api/v1/financial-goals`)
- `GET /api/v1/financial-goals` (`200 OK`): Lista las metas financieras (`metafinanciera`) del usuario autenticado (`RNF-09`).
- `POST /api/v1/financial-goals` (`201 Created`): Crea una meta financiera (`nombre`, `valorobjetivo`, `valoractual` opcional) calculando `progresoporcentaje`. Incluye aviso explícito de que no constituye asesoría financiera (`Límites 1.5`).
- `PATCH /api/v1/financial-goals/{goal_id}/progress` (`200 OK`): Registra un avance (`monto_avance` o nuevo `valoractual`) y recalcula automáticamente `progresoporcentaje = min(100, (valoractual / valorobjetivo) * 100)` (`RF-21`).
- `DELETE /api/v1/financial-goals/{goal_id}` (`204 No Content`): Elimina una meta financiera.
