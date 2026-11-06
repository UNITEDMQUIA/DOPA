"""Pruebas de Integración de los 33 Endpoints RESTful (`/api/v1` y `/health`) — Proyecto DOPA.

Agente Responsable: 4.1. Agente de Pruebas Unitarias e Integración (Unit & Integration Test Agent)
Verifica todos los casos de éxito y comportamientos adversos de las Historias de Usuario HU-01 a HU-12.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient) -> None:
    """Verifica el endpoint de disponibilidad `/health` (RNF-10)."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "DOPA API" in body["service"]


def test_hu01_auth_register_login_refresh_and_logout(client: TestClient) -> None:
    """HU-01 (RF-01, RF-02): Registro, rechazo de duplicados/inválidos, login, refresh y logout."""
    # 1. Registro exitoso
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Fred Salas",
            "correo": "fred.hu01@dopa.app",
            "contrasena": "ClaveSegura2026!",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["usuario"]["nombre"] == "Fred Salas"
    assert reg_data["usuario"]["puntos"] == 0
    assert reg_data["usuario"]["nivel"] == 1
    assert "contrasenahash" not in reg_data["usuario"]

    # 2. Comportamiento adverso HU-01: Correo duplicado -> 409 Conflict
    dup_resp = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Fred Duplicado",
            "correo": "FRED.HU01@dopa.app",
            "contrasena": "ClaveSegura2026!",
        },
    )
    assert dup_resp.status_code == 409

    # 3. Comportamiento adverso HU-01: Correo inválido o nombre vacío -> 422
    invalid_email_resp = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "   ",
            "correo": "correo-sin-arroba",
            "contrasena": "ClaveSegura2026!",
        },
    )
    assert invalid_email_resp.status_code == 422
    assert "errores" in invalid_email_resp.json()

    # 4. Login exitoso
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "correo": "fred.hu01@dopa.app",
            "contrasena": "ClaveSegura2026!",
        },
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 5. Comportamiento adverso HU-01: Credenciales erróneas -> 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={
            "correo": "fred.hu01@dopa.app",
            "contrasena": "PasswordIncorrecto",
        },
    )
    assert bad_login.status_code == 401

    bad_email_format_login = client.post(
        "/api/v1/auth/login",
        json={"correo": "invalido", "contrasena": "123"},
    )
    assert bad_email_format_login.status_code == 422

    # 6. Perfil /me y Refresh Token válido e inválido
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["correo"] == "fred.hu01@dopa.app"

    refresh_ok = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_ok.status_code == 200
    assert "access_token" in refresh_ok.json()

    refresh_bad = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert refresh_bad.status_code == 401

    # 7. Logout e invalidación inmediata del token
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["sesion_cerrada"] is True

    after_logout = client.get("/api/v1/auth/me", headers=headers)
    assert after_logout.status_code == 401


def test_hu12_user_preferences_configuration(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-12 (RF-23): Lectura y modificación de preferencias válidas e inválidas."""
    headers = registered_user["headers"]

    # Actualizar preferencias válidas
    update_resp = client.put(
        "/api/v1/auth/preferences",
        headers=headers,
        json={
            "duracion_concentracion_min": 15,
            "duracion_descanso_min": 5,
            "notificaciones_activas": True,
            "sonidos_suaves": True,
            "modo_bajo_estimulo": True,
            "meta_diaria_dopamina": 60,
            "tema_visual": "Lavanda Suave",
        },
    )
    assert update_resp.status_code == 200
    prefs = update_resp.json()["preferencias"]
    assert prefs["duracion_concentracion_min"] == 15
    assert prefs["meta_diaria_dopamina"] == 60

    # Comportamiento adverso HU-12: Duración negativa o fuera de rango -> 422
    invalid_resp = client.put(
        "/api/v1/auth/preferences",
        headers=headers,
        json={
            "duracion_concentracion_min": -5,
            "duracion_descanso_min": 0,
            "notificaciones_activas": True,
            "sonidos_suaves": True,
            "modo_bajo_estimulo": True,
            "meta_diaria_dopamina": 0,
            "tema_visual": "X",
        },
    )
    assert invalid_resp.status_code == 422


def test_hu10_dashboard_energy_checkin_and_quick_task(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-10 (RF-22): Panel principal '¡Hola, Fred!', chequeo de energía y botón '¡Hacer algo fácil!'."""
    headers = registered_user["headers"]

    # Sin tareas pendientes, /quick-task retorna 404 amigable
    empty_quick = client.get("/api/v1/dashboard/quick-task", headers=headers)
    assert empty_quick.status_code == 404

    # Chequeo de energía con alias 'baja' -> 'poquita' y 'alta' -> 'a tope'
    checkin_poquita = client.post(
        "/api/v1/dashboard/energy-checkin",
        headers=headers,
        json={"nivel_energia": "baja", "humor": "Abrumado", "horas_sueno": 6.5},
    )
    assert checkin_poquita.status_code == 201
    assert checkin_poquita.json()["nivel_energia"] == "poquita"

    checkin_tope = client.post(
        "/api/v1/dashboard/energy-checkin",
        headers=headers,
        json={"nivel_energia": "alta", "humor": "Con foco"},
    )
    assert checkin_tope.status_code == 201
    assert checkin_tope.json()["nivel_energia"] == "a tope"

    # Nivel de energía inválido -> 422
    bad_checkin = client.post(
        "/api/v1/dashboard/energy-checkin",
        headers=headers,
        json={"nivel_energia": "super_extrema"},
    )
    assert bad_checkin.status_code == 422

    # Crear una tarea fácil y consultar dashboard y quick-task
    client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"titulo": "Responder a Ana", "prioridad": "Baja"},
    )

    dash_resp = client.get("/api/v1/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    dash = dash_resp.json()
    assert dash["saludo"] == "¡Hola, Fred!"
    assert dash["subtitulo_amigable"] == "Vamos un paso a la vez"
    assert dash["estado_energia_hoy"] == "a tope"
    assert dash["humor_hoy"] == "Con foco"
    assert dash["accion_rapida_etiqueta"] == "¡Hacer algo fácil!"
    assert len(dash["micro_tareas_hoy"]) == 1

    quick_resp = client.get("/api/v1/dashboard/quick-task", headers=headers)
    assert quick_resp.status_code == 200
    assert quick_resp.json()["titulo"] == "Responder a Ana"


def test_hu02_hu03_tasks_and_subtasks_crud_and_completion(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-02 y HU-03 (RF-03 a RF-05, RF-13): CRUD de tareas, micro-pasos y completado con dopamina."""
    headers = registered_user["headers"]

    # Comportamiento adverso HU-02: Título en blanco -> 422
    blank_task = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"titulo": "   ", "prioridad": "Media"},
    )
    assert blank_task.status_code == 422

    # Comportamiento adverso: Rutina inexistente -> 404
    missing_routine_task = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"titulo": "Tarea con rutina fantasma", "id_rutina": 9999},
    )
    assert missing_routine_task.status_code == 404

    # Crear tarea con 2 micro-pasos iniciales
    create_resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "titulo": "Hacer la cama",
            "descripcion": "Dividida en pasos pequeños",
            "prioridad": "Media",
            "subtareas": ["Sacudir las sábanas", "Acomodar la almohada"],
        },
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    task_id = task["id"]
    assert task["etiqueta_esfuerzo"] == "Suave"
    assert task["total_subtareas"] == 2
    assert task["progreso_subtareas"] == "0/2 pasos"

    # Agregar un 3er micro-paso y validar adverso de descripción vacía
    bad_sub = client.post(
        f"/api/v1/tasks/{task_id}/subtasks",
        headers=headers,
        json={"descripcion": "   "},
    )
    assert bad_sub.status_code == 422

    sub3_resp = client.post(
        f"/api/v1/tasks/{task_id}/subtasks",
        headers=headers,
        json={"descripcion": "Estirar el cubrecama"},
    )
    assert sub3_resp.status_code == 201
    sub3_id = sub3_resp.json()["id"]

    # Listar micro-pasos y marcar el primero como completado
    sub_list = client.get(f"/api/v1/tasks/{task_id}/subtasks", headers=headers)
    assert sub_list.status_code == 200
    assert sub_list.json()["total_pasos"] == 3
    first_sub_id = sub_list.json()["items"][0]["id"]

    patch_sub = client.patch(
        f"/api/v1/tasks/{task_id}/subtasks/{first_sub_id}",
        headers=headers,
        json={"descripcion": "Sacudir bien las sábanas", "completada": True},
    )
    assert patch_sub.status_code == 200
    assert patch_sub.json()["completada"] is True

    # Adversos en micro-pasos (descripción en blanco 422, inexistente 404)
    assert (
        client.patch(
            f"/api/v1/tasks/{task_id}/subtasks/{first_sub_id}",
            headers=headers,
            json={"descripcion": "  "},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/tasks/{task_id}/subtasks/9999",
            headers=headers,
            json={"completada": True},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            "/api/v1/tasks/9999/subtasks/1",
            headers=headers,
            json={"completada": True},
        ).status_code
        == 404
    )
    assert (
        client.get("/api/v1/tasks/9999/subtasks", headers=headers).status_code == 404
    )
    assert (
        client.post(
            "/api/v1/tasks/9999/subtasks",
            headers=headers,
            json={"descripcion": "Paso"},
        ).status_code
        == 404
    )

    # Eliminar el 3er micro-paso
    del_sub = client.delete(f"/api/v1/tasks/{task_id}/subtasks/{sub3_id}", headers=headers)
    assert del_sub.status_code == 204
    assert (
        client.delete(f"/api/v1/tasks/{task_id}/subtasks/{sub3_id}", headers=headers).status_code
        == 404
    )
    assert (
        client.delete("/api/v1/tasks/9999/subtasks/1", headers=headers).status_code == 404
    )

    # Editar tarea principal y verificar listado "Poquito a poquito"
    upd_resp = client.put(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"titulo": "Hacer la cama hoy", "prioridad": "Baja"},
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["etiqueta_esfuerzo"] == "Fácil"

    # Adversos de edición de tarea
    assert (
        client.put(
            f"/api/v1/tasks/{task_id}",
            headers=headers,
            json={"titulo": "   "},
        ).status_code
        == 422
    )
    assert (
        client.put(
            f"/api/v1/tasks/{task_id}",
            headers=headers,
            json={"id_rutina": 9999},
        ).status_code
        == 404
    )
    assert (
        client.put("/api/v1/tasks/9999", headers=headers, json={"titulo": "X"}).status_code
        == 404
    )

    list_resp = client.get("/api/v1/tasks?completada=false&prioridad=Baja", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["encabezado"] == "Poquito a poquito"
    assert list_resp.json()["total"] == 1

    # Completar tarea principal -> +10 dopamina y todos sus micro-pasos quedan completados
    comp_resp = client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["puntos_ganados"] == 10
    assert comp_data["puntos_totales"] == 10
    assert comp_data["idempotente"] is False
    assert comp_data["tarea"]["completada"] is True
    assert all(s["completada"] for s in comp_data["tarea"]["subtareas"])

    # Reintento de completar tarea ya completada -> idempotente (0 puntos extra)
    comp_retry = client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
    assert comp_retry.status_code == 200
    assert comp_retry.json()["puntos_ganados"] == 0
    assert comp_retry.json()["idempotente"] is True

    assert client.post("/api/v1/tasks/9999/complete", headers=headers).status_code == 404

    # Detalle y eliminación de la tarea
    assert client.get(f"/api/v1/tasks/{task_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/tasks/9999", headers=headers).status_code == 404

    del_task = client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert del_task.status_code == 204
    assert client.delete(f"/api/v1/tasks/{task_id}", headers=headers).status_code == 404


def test_hu04_hu11_routines_crud_complete_and_guilt_free_resume(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-04 y HU-11 (RF-06, RF-07, RF-16, RF-24): Rutinas y retomado sin penalizaciones."""
    headers = registered_user["headers"]

    # Adverso: nombre en blanco -> 422
    assert (
        client.post(
            "/api/v1/routines",
            headers=headers,
            json={"nombre": "   ", "recurrencia": "Diaria"},
        ).status_code
        == 422
    )

    # Crear rutina
    r_resp = client.post(
        "/api/v1/routines",
        headers=headers,
        json={"nombre": "Rutina Matutina Suave", "recurrencia": "Lunes a Viernes", "hora": "08:00:00"},
    )
    assert r_resp.status_code == 201
    routine_id = r_resp.json()["id"]

    # Listar y obtener detalle
    assert client.get("/api/v1/routines", headers=headers).json()["total"] == 1
    detail = client.get(f"/api/v1/routines/{routine_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["nombre"] == "Rutina Matutina Suave"
    assert client.get("/api/v1/routines/9999", headers=headers).status_code == 404

    # Actualizar rutina
    upd = client.put(
        f"/api/v1/routines/{routine_id}",
        headers=headers,
        json={"nombre": "Rutina de Inicio Suave", "recurrencia": "Diaria"},
    )
    assert upd.status_code == 200
    assert upd.json()["nombre"] == "Rutina de Inicio Suave"
    assert (
        client.put(
            f"/api/v1/routines/{routine_id}",
            headers=headers,
            json={"nombre": "   "},
        ).status_code
        == 422
    )
    assert (
        client.put("/api/v1/routines/9999", headers=headers, json={"nombre": "X"}).status_code
        == 404
    )

    # Completar rutina hoy (+10 dopamina) y verificar idempotencia con Idempotency-Key
    comp = client.post(
        f"/api/v1/routines/{routine_id}/complete-today",
        headers={**headers, "Idempotency-Key": "routine-idem-001"},
    )
    assert comp.status_code == 200
    assert comp.json()["puntos_ganados"] == 10
    puntos_tras_completar = comp.json()["puntos_totales"]

    comp_again = client.post(
        f"/api/v1/routines/{routine_id}/complete-today",
        headers={**headers, "Idempotency-Key": "routine-idem-001"},
    )
    assert comp_again.status_code == 200
    assert comp_again.json()["puntos_ganados"] == 0
    assert comp_again.json()["idempotente"] is True
    assert client.post("/api/v1/routines/9999/complete-today", headers=headers).status_code == 404

    # HU-11 / RF-16: Retomar rutina tras días de inactividad SIN perder puntos ni nivel
    resume = client.post(f"/api/v1/routines/{routine_id}/resume", headers=headers)
    assert resume.status_code == 200
    res_data = resume.json()
    assert res_data["penalizacion_aplicada"] is False
    assert res_data["puntos_conservados"] == puntos_tras_completar
    assert res_data["rutina"]["completadahoy"] is False
    assert "intactos" in res_data["mensaje_bienvenida"]
    assert client.post("/api/v1/routines/9999/resume", headers=headers).status_code == 404

    # Eliminar rutina
    assert client.delete(f"/api/v1/routines/{routine_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/routines/{routine_id}", headers=headers).status_code == 404


def test_hu06_pomodoro_focus_cancel_and_low_stimulus_breaks(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-06 (RF-10 a RF-12): Sesiones de enfoque, cancelación sin puntos y pausas de bajo estímulo."""
    headers = registered_user["headers"]

    # Adverso: Tarea inexistente -> 404
    assert (
        client.post(
            "/api/v1/pomodoro/sessions",
            headers=headers,
            json={"id_tarea": 9999, "duracionconcentracion": 5, "duraciondescanso": 5},
        ).status_code
        == 404
    )

    # Crear sesión de enfoque corto (5 min / 5 min)
    s_resp = client.post(
        "/api/v1/pomodoro/sessions",
        headers=headers,
        json={"duracionconcentracion": 5, "duraciondescanso": 5},
    )
    assert s_resp.status_code == 201
    session_id = s_resp.json()["id"]
    assert s_resp.json()["modo_etiqueta"] == "Micro-enfoque 5 min"

    # Comportamiento adverso HU-06: Cancelar sesión antes de finalizar NO suma ciclos ni puntos
    cancel_resp = client.post(f"/api/v1/pomodoro/sessions/{session_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200
    cancel_data = cancel_resp.json()
    assert cancel_data["estado"] == "cancelada"
    assert cancel_data["puntos_ganados"] == 0
    assert cancel_data["sesion"]["sesionescompletadas"] == 0
    assert client.post("/api/v1/pomodoro/sessions/9999/cancel", headers=headers).status_code == 404

    # Completar sesión -> +5 dopamina e incrementa `sesionescompletadas` a 1
    comp_resp = client.post(
        f"/api/v1/pomodoro/sessions/{session_id}/complete",
        headers={**headers, "Idempotency-Key": "pomo-key-001"},
    )
    assert comp_resp.status_code == 200
    assert comp_resp.json()["puntos_ganados"] == 5
    assert comp_resp.json()["sesion"]["sesionescompletadas"] == 1

    # Reintento con misma Idempotency-Key -> no duplica puntos
    comp_dup = client.post(
        f"/api/v1/pomodoro/sessions/{session_id}/complete",
        headers={**headers, "Idempotency-Key": "pomo-key-001"},
    )
    assert comp_dup.status_code == 200
    assert comp_dup.json()["puntos_ganados"] == 0
    assert comp_dup.json()["idempotente"] is True
    assert client.post("/api/v1/pomodoro/sessions/9999/complete", headers=headers).status_code == 404

    # Listar sesiones y consultar actividades de bajo estímulo ("Un break suave")
    assert client.get("/api/v1/pomodoro/sessions", headers=headers).json()["total"] == 1

    breaks_resp = client.get("/api/v1/pomodoro/low-stimulus-activities", headers=headers)
    assert breaks_resp.status_code == 200
    breaks = breaks_resp.json()
    assert breaks["encabezado"] == "Un break suave"
    titulos = [a["titulo"] for a in breaks["actividades"]]
    assert "Respiración 4-4" in titulos
    assert "Estiramiento suave" in titulos


def test_hu05_reminders_crud_and_deactivation(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-05 (RF-08, RF-09): Programar, listar, desactivar al completarse y eliminar recordatorios."""
    headers = registered_user["headers"]

    # Adversos al crear recordatorio
    assert (
        client.post(
            "/api/v1/reminders",
            headers=headers,
            json={"fechahora": datetime.now(timezone.utc).isoformat(), "mensaje": "   ", "tipo": "Tarea"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/reminders",
            headers=headers,
            json={
                "fechahora": datetime.now(timezone.utc).isoformat(),
                "mensaje": "Recordatorio",
                "tipo": "Tarea",
                "id_tarea": 9999,
            },
        ).status_code
        == 404
    )

    # Crear recordatorio activo
    rem_resp = client.post(
        "/api/v1/reminders",
        headers=headers,
        json={
            "fechahora": "2026-11-06T10:00:00",
            "mensaje": "Tomar pausa de hidratación",
            "tipo": "Rutina",
        },
    )
    assert rem_resp.status_code == 201
    rem = rem_resp.json()
    rem_id = rem["id"]
    assert rem["completadahoy"] is False
    assert rem["notificacion_activa"] is True

    # Listar con filtros
    list_rem = client.get("/api/v1/reminders?tipo=Rutina&completadahoy=false", headers=headers)
    assert list_rem.status_code == 200
    assert list_rem.json()["total"] == 1

    # Comportamiento adverso HU-05: Si ya fue completado (`completadahoy=true`), se desactiva la notificación
    deact_resp = client.put(
        f"/api/v1/reminders/{rem_id}",
        headers=headers,
        json={"completadahoy": True, "mensaje": "Hidratación lista"},
    )
    assert deact_resp.status_code == 200
    assert deact_resp.json()["completadahoy"] is True
    assert deact_resp.json()["notificacion_activa"] is False

    # Adversos en actualización y borrado
    assert (
        client.put(
            f"/api/v1/reminders/{rem_id}",
            headers=headers,
            json={"mensaje": "   "},
        ).status_code
        == 422
    )
    assert (
        client.put(
            f"/api/v1/reminders/{rem_id}",
            headers=headers,
            json={"id_tarea": 9999},
        ).status_code
        == 404
    )
    assert (
        client.put(
            "/api/v1/reminders/9999",
            headers=headers,
            json={"completadahoy": True},
        ).status_code
        == 404
    )

    assert client.delete(f"/api/v1/reminders/{rem_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/reminders/{rem_id}", headers=headers).status_code == 404


def test_hu07_gamification_summary_and_rewards(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-07 (RF-13 a RF-15): Resumen 'Mi Dopamina hoy', creación y desbloqueo de recompensas."""
    headers = registered_user["headers"]

    # Adversos al crear recompensa
    assert (
        client.post(
            "/api/v1/gamification/rewards",
            headers=headers,
            json={"nombre": "   ", "costopuntos": 10},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/gamification/rewards",
            headers=headers,
            json={"nombre": "Logro", "costopuntos": 10, "id_tarea": 9999},
        ).status_code
        == 404
    )

    # Crear recompensa costosa (100 puntos) y verificar rechazo por puntos insuficientes
    rew_costosa = client.post(
        "/api/v1/gamification/rewards",
        headers=headers,
        json={"nombre": "Tema Dorado Calma", "costopuntos": 100},
    )
    assert rew_costosa.status_code == 201
    rew_costosa_id = rew_costosa.json()["id"]

    unlock_fail = client.post(
        f"/api/v1/gamification/rewards/{rew_costosa_id}/unlock",
        headers=headers,
    )
    assert unlock_fail.status_code == 400
    assert "faltan" in unlock_fail.json()["detail"]

    # Crear recompensa de 10 puntos, ganar +10 completando una tarea y verificar desbloqueo
    rew_10 = client.post(
        "/api/v1/gamification/rewards",
        headers=headers,
        json={"nombre": "Insignia Primer Paso", "costopuntos": 0},
    )
    rew_10_id = rew_10.json()["id"]

    unlock_ok = client.post(f"/api/v1/gamification/rewards/{rew_10_id}/unlock", headers=headers)
    assert unlock_ok.status_code == 200
    assert unlock_ok.json()["desbloqueada"] is True

    # Desbloqueo repetido es idempotente
    unlock_again = client.post(f"/api/v1/gamification/rewards/{rew_10_id}/unlock", headers=headers)
    assert unlock_again.status_code == 200
    assert unlock_again.json()["desbloqueada"] is True
    assert client.post("/api/v1/gamification/rewards/9999/unlock", headers=headers).status_code == 404

    # Crear recompensa vinculada a una tarea y verificar rechazo mientras la tarea está pendiente
    t_rew = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"titulo": "Tarea para recompensa"},
    ).json()
    rew_tarea = client.post(
        "/api/v1/gamification/rewards",
        headers=headers,
        json={"nombre": "Premio Tarea", "costopuntos": 500, "id_tarea": t_rew["id"]},
    ).json()
    assert (
        client.post(
            f"/api/v1/gamification/rewards/{rew_tarea['id']}/unlock",
            headers=headers,
        ).status_code
        == 400
    )
    assert (
        client.get(f"/api/v1/tasks?id_rutina=1", headers=headers).status_code == 200
    )

    # Resumen y listado de gamificación
    summary_resp = client.get("/api/v1/gamification/summary", headers=headers)
    assert summary_resp.status_code == 200
    assert summary_resp.json()["encabezado"] == "Mi Dopamina hoy"
    assert "Abrumado" in summary_resp.json()["opciones_humor"]

    rewards_list = client.get("/api/v1/gamification/rewards", headers=headers)
    assert rewards_list.status_code == 200
    assert rewards_list.json()["total"] == 3


def test_hu08_personal_records_sleep_mood_and_non_medical_disclaimer(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-08 (RF-17 a RF-19): Registro de sueño y humor, cálculo de progreso y aviso no médico."""
    headers = registered_user["headers"]

    # Listado inicialmente vacío
    empty_list = client.get("/api/v1/personal-records", headers=headers)
    assert empty_list.status_code == 200
    assert empty_list.json()["total"] == 0
    assert "no constituye un diagnóstico médico" in empty_list.json()["aviso_no_medico"]

    # Adverso: nombre vacío -> 422
    assert (
        client.post(
            "/api/v1/personal-records",
            headers=headers,
            json={"nombre": "   ", "valorobjetivo": 8.0, "valoractual": 6.8},
        ).status_code
        == 422
    )

    # Crear registro de sueño (6.8 / 8.0 -> 85.0%)
    rec_resp = client.post(
        "/api/v1/personal-records",
        headers=headers,
        json={"nombre": "Horas de sueño", "valorobjetivo": 8.0, "valoractual": 6.8},
    )
    assert rec_resp.status_code == 201
    rec = rec_resp.json()
    rec_id = rec["id"]
    assert rec["progresoporcentaje"] == 85.0
    assert rec["unidad_sugerida"] == "horas"

    # Actualizar a 8.0 horas -> 100.0%
    upd_resp = client.put(
        f"/api/v1/personal-records/{rec_id}",
        headers=headers,
        json={"valoractual": 8.0},
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["progresoporcentaje"] == 100.0

    # Adversos en actualización
    assert (
        client.put(
            f"/api/v1/personal-records/{rec_id}",
            headers=headers,
            json={"nombre": "   "},
        ).status_code
        == 422
    )
    assert (
        client.put(
            "/api/v1/personal-records/9999",
            headers=headers,
            json={"valoractual": 7.0},
        ).status_code
        == 404
    )

    # Verificar tendencia descriptiva con registros
    non_empty = client.get("/api/v1/personal-records", headers=headers)
    assert non_empty.status_code == 200
    assert "Promedio general de bienestar" in non_empty.json()["tendencia_descriptiva"]

    # Eliminar registro
    assert client.delete(f"/api/v1/personal-records/{rec_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/personal-records/{rec_id}", headers=headers).status_code == 404


def test_hu09_financial_goals_auto_progress_and_non_banking_disclaimer(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """HU-09 (RF-20, RF-21, Límites 1.5): Metas financieras, cálculo de porcentaje y aviso no bancario."""
    headers = registered_user["headers"]

    # Adverso: nombre en blanco -> 422
    assert (
        client.post(
            "/api/v1/financial-goals",
            headers=headers,
            json={"nombre": "   ", "valorobjetivo": 200.0, "valoractual": 0.0},
        ).status_code
        == 422
    )

    # Crear meta financiera ($50 de $200 -> 25.0%)
    goal_resp = client.post(
        "/api/v1/financial-goals",
        headers=headers,
        json={"nombre": "Ahorro Audífonos Antirruido", "valorobjetivo": 200.0, "valoractual": 50.0},
    )
    assert goal_resp.status_code == 201
    goal = goal_resp.json()
    goal_id = goal["id"]
    assert goal["progresoporcentaje"] == 25.0
    assert goal["meta_alcanzada"] is False
    assert "No realiza conexiones bancarias" in goal["aviso_alcance"]

    # Registrar avance incremental (+$100 -> $150 / $200 = 75.0%)
    prog_1 = client.patch(
        f"/api/v1/financial-goals/{goal_id}/progress",
        headers=headers,
        json={"monto_avance": 100.0},
    )
    assert prog_1.status_code == 200
    assert prog_1.json()["valoractual"] == 150.0
    assert prog_1.json()["progresoporcentaje"] == 75.0

    # Registrar nuevo valor actual directo ($200 -> 100.0%, meta alcanzada)
    prog_2 = client.patch(
        f"/api/v1/financial-goals/{goal_id}/progress",
        headers=headers,
        json={"valoractual": 200.0},
    )
    assert prog_2.status_code == 200
    assert prog_2.json()["progresoporcentaje"] == 100.0
    assert prog_2.json()["meta_alcanzada"] is True

    # Comportamientos adversos HU-09: monto_avance negativo o vacío -> 422, meta inexistente -> 404
    assert (
        client.patch(
            f"/api/v1/financial-goals/{goal_id}/progress",
            headers=headers,
            json={"monto_avance": -20.0},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/api/v1/financial-goals/{goal_id}/progress",
            headers=headers,
            json={},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            "/api/v1/financial-goals/9999/progress",
            headers=headers,
            json={"monto_avance": 10.0},
        ).status_code
        == 404
    )

    # Listar y eliminar meta financiera
    goals_list = client.get("/api/v1/financial-goals", headers=headers)
    assert goals_list.status_code == 200
    assert goals_list.json()["total"] == 1
    assert "asesoría financiera" in goals_list.json()["aviso_alcance"]

    assert client.delete(f"/api/v1/financial-goals/{goal_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/financial-goals/{goal_id}", headers=headers).status_code == 404
