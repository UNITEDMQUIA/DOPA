"""Pruebas End-to-End (E2E) de Flujos Completos de Usuario — Proyecto DOPA.

Agente Responsable: 4.2. Agente de Automatización E2E (End-to-End Flow Agent)
Simula de principio a fin el recorrido real de `Fred` en los prototipos móviles (Parcial 2.pdf, Figuras 1-13):
Registro -> Login -> Chequeo de energía -> Crear rutina y tareas ("Hacer la cama" con 2 micro-pasos,
"Responder a Ana") -> Botón "¡Hacer algo fácil!" -> Marcar micro-pasos 1 y 2 -> Temporizador 05:00 ->
Completar tarea (+10 dopamina) -> Reintento con Idempotency-Key (sin duplicar puntos) ->
"Mi Dopamina hoy" y Humor -> "Un break suave" (Respiración 4-4) -> Retomar rutina sin penalización ->
Meta Financiera y avance.
"""

from fastapi.testclient import TestClient


def test_e2e_complete_fred_journey_figures_1_to_13(client: TestClient) -> None:
    """Ejecuta el viaje E2E completo de Fred validando estado, gamificación e idempotencia."""
    # ------------------------------------------------------------------
    # PASO 1: Registro y Login (Figura 1 - HU-01)
    # ------------------------------------------------------------------
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "nombre": "Fred",
            "correo": "fred.e2e@dopa.app",
            "contrasena": "FredE2EPassword2026!",
        },
    )
    assert reg_resp.status_code == 201

    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "correo": "fred.e2e@dopa.app",
            "contrasena": "FredE2EPassword2026!",
        },
    )
    assert login_resp.status_code == 200
    auth_data = login_resp.json()
    headers = {"Authorization": f"Bearer {auth_data['access_token']}"}
    assert auth_data["usuario"]["puntos"] == 0
    assert auth_data["usuario"]["nivel"] == 1

    # ------------------------------------------------------------------
    # PASO 2: Chequeo de Energía Diario y Dashboard (Figuras 2 y 7 - HU-10)
    # ------------------------------------------------------------------
    checkin_resp = client.post(
        "/api/v1/dashboard/energy-checkin",
        headers=headers,
        json={
            "nivel_energia": "media",
            "humor": "Con foco",
            "horas_sueno": 6.8,
        },
    )
    assert checkin_resp.status_code == 201
    assert checkin_resp.json()["nivel_energia"] == "media"
    assert checkin_resp.json()["humor"] == "Con foco"

    dash_initial = client.get("/api/v1/dashboard", headers=headers)
    assert dash_initial.status_code == 200
    assert dash_initial.json()["saludo"] == "¡Hola, Fred!"
    assert dash_initial.json()["subtitulo_amigable"] == "Vamos un paso a la vez"

    # ------------------------------------------------------------------
    # PASO 3: Crear Rutina y Tareas con Micro-pasos (Figuras 3, 8 y 9 - HU-02, HU-03, HU-04)
    # ------------------------------------------------------------------
    routine_resp = client.post(
        "/api/v1/routines",
        headers=headers,
        json={
            "nombre": "Mañana en calma",
            "recurrencia": "Todos los días",
            "hora": "08:00:00",
        },
    )
    assert routine_resp.status_code == 201
    routine_id = routine_resp.json()["id"]

    # Tarea 1: "Hacer la cama" con 2 micro-pasos (Figura 9)
    task_cama_resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "titulo": "Hacer la cama",
            "descripcion": "Dividida en micro-pasos suaves",
            "prioridad": "Media",
            "id_rutina": routine_id,
            "subtareas": [
                "Sacudir las sábanas",
                "Acomodar la almohada",
            ],
        },
    )
    assert task_cama_resp.status_code == 201
    task_cama = task_cama_resp.json()
    cama_id = task_cama["id"]
    assert task_cama["etiqueta_esfuerzo"] == "Suave"
    assert task_cama["progreso_subtareas"] == "0/2 pasos"

    # Crear recompensa vinculada a completar "Hacer la cama"
    rew_resp = client.post(
        "/api/v1/gamification/rewards",
        headers=headers,
        json={
            "nombre": "Insignia Cama Lista",
            "costopuntos": 10,
            "id_tarea": cama_id,
        },
    )
    assert rew_resp.status_code == 201

    # Tarea 2: "Responder a Ana" (Fácil, sin micro-pasos)
    task_ana_resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "titulo": "Responder a Ana",
            "descripcion": "Enviar audio corto",
            "prioridad": "Baja",
            "subtareas": [],
        },
    )
    assert task_ana_resp.status_code == 201
    assert task_ana_resp.json()["etiqueta_esfuerzo"] == "Fácil"

    # ------------------------------------------------------------------
    # PASO 4: Botón "¡Hacer algo fácil!" (Figuras 3 y 7 - HU-10)
    # ------------------------------------------------------------------
    quick_resp = client.get("/api/v1/dashboard/quick-task", headers=headers)
    assert quick_resp.status_code == 200
    assert quick_resp.json()["titulo"] == "Responder a Ana"

    # ------------------------------------------------------------------
    # PASO 5: Marcar Micro-pasos 1 y 2 de "Hacer la cama" (Figura 9 - HU-03)
    # ------------------------------------------------------------------
    subtasks = task_cama["subtareas"]
    sub1_id = subtasks[0]["id"]
    sub2_id = subtasks[1]["id"]

    p1 = client.patch(
        f"/api/v1/tasks/{cama_id}/subtasks/{sub1_id}",
        headers=headers,
        json={"completada": True},
    )
    assert p1.status_code == 200
    assert p1.json()["completada"] is True

    p2 = client.patch(
        f"/api/v1/tasks/{cama_id}/subtasks/{sub2_id}",
        headers=headers,
        json={"completada": True},
    )
    assert p2.status_code == 200
    assert p2.json()["completada"] is True

    sub_progress = client.get(f"/api/v1/tasks/{cama_id}/subtasks", headers=headers)
    assert sub_progress.status_code == 200
    assert sub_progress.json()["progreso_pasos_porcentaje"] == 100.0

    # ------------------------------------------------------------------
    # PASO 6: Iniciar y Completar Temporizador Pomodoro 05:00 (Figuras 4 y 9 - HU-06)
    # ------------------------------------------------------------------
    pomo_create = client.post(
        "/api/v1/pomodoro/sessions",
        headers=headers,
        json={
            "id_tarea": cama_id,
            "duracionconcentracion": 5,
            "duraciondescanso": 5,
        },
    )
    assert pomo_create.status_code == 201
    session_id = pomo_create.json()["id"]

    pomo_complete = client.post(
        f"/api/v1/pomodoro/sessions/{session_id}/complete",
        headers={**headers, "Idempotency-Key": "e2e-pomo-0500"},
    )
    assert pomo_complete.status_code == 200
    assert pomo_complete.json()["puntos_ganados"] == 5
    assert pomo_complete.json()["puntos_totales"] == 5
    assert pomo_complete.json()["sesion"]["sesionescompletadas"] == 1

    # ------------------------------------------------------------------
    # PASO 7: Completar Tarea (+10 dopamina) y Reintentar con Idempotency-Key (Figura 10)
    # ------------------------------------------------------------------
    idem_headers = {**headers, "Idempotency-Key": "e2e-complete-cama-001"}
    complete_1 = client.post(
        f"/api/v1/tasks/{cama_id}/complete",
        headers=idem_headers,
    )
    assert complete_1.status_code == 200
    c1_data = complete_1.json()
    assert c1_data["mensaje_celebracion"] == "¡Lo hiciste, Fred!"
    assert c1_data["puntos_ganados"] == 10
    assert c1_data["puntos_totales"] == 15
    assert c1_data["idempotente"] is False
    assert len(c1_data["recompensas_desbloqueadas"]) == 1

    # Reintento ante microcorte de red con la misma Idempotency-Key -> NO duplica puntos
    complete_retry = client.post(
        f"/api/v1/tasks/{cama_id}/complete",
        headers=idem_headers,
    )
    assert complete_retry.status_code == 200
    c_retry_data = complete_retry.json()
    assert c_retry_data["idempotente"] is True
    assert c_retry_data["puntos_ganados"] == 0
    assert c_retry_data["puntos_totales"] == 15

    # ------------------------------------------------------------------
    # PASO 8: Consultar "Mi Dopamina hoy" y Registrar Humor (Figuras 6 y 11 - HU-07, HU-08)
    # ------------------------------------------------------------------
    gam_summary = client.get("/api/v1/gamification/summary", headers=headers)
    assert gam_summary.status_code == 200
    g_data = gam_summary.json()
    assert g_data["encabezado"] == "Mi Dopamina hoy"
    assert g_data["puntos_totales"] == 15
    assert g_data["tareas_completadas_total"] == 1
    assert g_data["sesiones_enfoque_completadas"] == 1
    assert g_data["recompensas_desbloqueadas_count"] == 1

    humor_rec = client.post(
        "/api/v1/personal-records",
        headers=headers,
        json={
            "nombre": "Estado de ánimo: Tranquilo",
            "valorobjetivo": 5.0,
            "valoractual": 4.5,
        },
    )
    assert humor_rec.status_code == 201
    assert humor_rec.json()["progresoporcentaje"] == 90.0

    # ------------------------------------------------------------------
    # PASO 9: Tomar "Un break suave" (Respiración 4-4) (Figuras 12 y 13 - HU-06)
    # ------------------------------------------------------------------
    break_resp = client.get("/api/v1/pomodoro/low-stimulus-activities", headers=headers)
    assert break_resp.status_code == 200
    break_data = break_resp.json()
    assert break_data["encabezado"] == "Un break suave"
    assert any(a["id"] == "respiracion-4-4" for a in break_data["actividades"])

    # ------------------------------------------------------------------
    # PASO 10: Completar y Retomar Rutina sin Penalización (HU-04, HU-11, RF-16)
    # ------------------------------------------------------------------
    rout_comp = client.post(f"/api/v1/routines/{routine_id}/complete-today", headers=headers)
    assert rout_comp.status_code == 200
    assert rout_comp.json()["puntos_totales"] == 25

    rout_resume = client.post(f"/api/v1/routines/{routine_id}/resume", headers=headers)
    assert rout_resume.status_code == 200
    assert rout_resume.json()["penalizacion_aplicada"] is False
    assert rout_resume.json()["puntos_conservados"] == 25
    assert rout_resume.json()["nivel_conservado"] == 1

    # ------------------------------------------------------------------
    # PASO 11: Registrar Meta Financiera y Avance (HU-09, RF-20, RF-21)
    # ------------------------------------------------------------------
    goal_create = client.post(
        "/api/v1/financial-goals",
        headers=headers,
        json={
            "nombre": "Fondo para taller creativo",
            "valorobjetivo": 100.0,
            "valoractual": 25.0,
        },
    )
    assert goal_create.status_code == 201
    goal_id = goal_create.json()["id"]
    assert goal_create.json()["progresoporcentaje"] == 25.0

    goal_prog = client.patch(
        f"/api/v1/financial-goals/{goal_id}/progress",
        headers=headers,
        json={"monto_avance": 50.0},
    )
    assert goal_prog.status_code == 200
    assert goal_prog.json()["valoractual"] == 75.0
    assert goal_prog.json()["progresoporcentaje"] == 75.0
