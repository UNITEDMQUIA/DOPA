"""Auditoría Automatizada de Seguridad (SecOps) y Pruebas de Rendimiento — Proyecto DOPA.

Agente Responsable: 4.3. Agente de Seguridad y Rendimiento (SecOps & Perf Agent)
Verifica:
- RNF-06: Cifrado irreversible bcrypt de contraseñas en base de datos y no exposición en JSON.
- RNF-07: Rechazo HTTP 401 ante ausencias de token, tokens corruptos, refresh usado como access o revocados.
- RNF-08 y RNF-09: Aislamiento estricto y privacidad total entre usuarios (`Fred` vs `Paula`).
- Prevención de Inyección SQL (SQLi) mediante consultas parametrizadas de SQLAlchemy ORM.
- Idempotencia bajo múltiples reintentos repetidos (`Idempotency-Key` / `X-Transaction-Id`).
- RNF-04: Rendimiento promedio `< 50 ms` por operación CRUD y Dashboard.
"""

import time
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token
from app.domain.models import Usuario


def test_rnf06_password_never_stored_or_exposed_in_plaintext(
    client: TestClient,
    db_session: Session,
    registered_user: dict[str, Any],
) -> None:
    """RNF-06: La contraseña jamás se guarda en texto plano en `usuario` ni se filtra en respuestas JSON."""
    user_db = db_session.query(Usuario).filter(Usuario.id == registered_user["id"]).first()
    assert user_db is not None
    assert user_db.contrasenahash != registered_user["contrasena"]
    assert user_db.contrasenahash.startswith("$2b$12$")

    me_resp = client.get("/api/v1/auth/me", headers=registered_user["headers"])
    assert me_resp.status_code == 200
    raw_json_text = me_resp.text
    assert registered_user["contrasena"] not in raw_json_text
    assert "contrasenahash" not in raw_json_text


def test_rnf07_jwt_authentication_boundaries_and_401_rejections(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """RNF-07: Endpoints protegidos rechazan con 401 peticiones sin token, malformadas o con tipo incorrecto."""
    protected_endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/dashboard"),
        ("GET", "/api/v1/tasks"),
        ("GET", "/api/v1/routines"),
        ("GET", "/api/v1/pomodoro/sessions"),
        ("GET", "/api/v1/reminders"),
        ("GET", "/api/v1/gamification/summary"),
        ("GET", "/api/v1/personal-records"),
        ("GET", "/api/v1/financial-goals"),
    ]

    for method, url in protected_endpoints:
        # 1. Sin header Authorization
        r_no_auth = client.request(method, url)
        assert r_no_auth.status_code == 401

        # 2. Con token malformado
        r_bad_token = client.request(
            method,
            url,
            headers={"Authorization": "Bearer token.falso.manipulado"},
        )
        assert r_bad_token.status_code == 401

    # 3. Usar refresh_token como si fuera access_token -> 401
    refresh_as_access = client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {registered_user['refresh_token']}"},
    )
    assert refresh_as_access.status_code == 401

    # 4. Token firmado para un usuario que ya no existe en BD -> 401
    ghost_token = create_access_token(user_id=99999, correo="fantasma@dopa.app")
    ghost_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {ghost_token}"},
    )
    assert ghost_resp.status_code == 401

    ghost_refresh = create_refresh_token(user_id=99999, correo="fantasma@dopa.app")
    ghost_refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ghost_refresh},
    )
    assert ghost_refresh_resp.status_code == 401


def test_rnf08_rnf09_strict_cross_user_privacy_isolation(
    client: TestClient,
    registered_user: dict[str, Any],
    second_user: dict[str, Any],
) -> None:
    """RNF-08 y RNF-09: Paula no puede ver, editar, completar ni borrar ningún dato privado de Fred."""
    fred_headers = registered_user["headers"]
    paula_headers = second_user["headers"]

    # Fred crea recursos privados en todos los módulos
    task_id = client.post(
        "/api/v1/tasks",
        headers=fred_headers,
        json={"titulo": "Tarea privada de Fred", "subtareas": ["Micro-paso privado"]},
    ).json()["id"]

    routine_id = client.post(
        "/api/v1/routines",
        headers=fred_headers,
        json={"nombre": "Rutina privada de Fred", "recurrencia": "Diaria"},
    ).json()["id"]

    pomo_id = client.post(
        "/api/v1/pomodoro/sessions",
        headers=fred_headers,
        json={"duracionconcentracion": 5, "duraciondescanso": 5},
    ).json()["id"]

    rem_id = client.post(
        "/api/v1/reminders",
        headers=fred_headers,
        json={"fechahora": "2026-11-06T12:00:00", "mensaje": "Cita médica Fred", "tipo": "Compromiso"},
    ).json()["id"]

    rec_id = client.post(
        "/api/v1/personal-records",
        headers=fred_headers,
        json={"nombre": "Sueño privado Fred", "valorobjetivo": 8.0, "valoractual": 7.0},
    ).json()["id"]

    goal_id = client.post(
        "/api/v1/financial-goals",
        headers=fred_headers,
        json={"nombre": "Ahorro privado Fred", "valorobjetivo": 500.0, "valoractual": 100.0},
    ).json()["id"]

    # Paula consulta sus propios listados -> todos deben estar vacíos (0 elementos de Fred)
    assert client.get("/api/v1/tasks", headers=paula_headers).json()["total"] == 0
    assert client.get("/api/v1/routines", headers=paula_headers).json()["total"] == 0
    assert client.get("/api/v1/pomodoro/sessions", headers=paula_headers).json()["total"] == 0
    assert client.get("/api/v1/reminders", headers=paula_headers).json()["total"] == 0
    assert client.get("/api/v1/personal-records", headers=paula_headers).json()["total"] == 0
    assert client.get("/api/v1/financial-goals", headers=paula_headers).json()["total"] == 0

    # Paula intenta acceder, modificar, completar o eliminar los recursos de Fred por ID -> 404
    assert client.get(f"/api/v1/tasks/{task_id}", headers=paula_headers).status_code == 404
    assert (
        client.put(f"/api/v1/tasks/{task_id}", headers=paula_headers, json={"titulo": "Hack"}).status_code
        == 404
    )
    assert client.post(f"/api/v1/tasks/{task_id}/complete", headers=paula_headers).status_code == 404
    assert client.delete(f"/api/v1/tasks/{task_id}", headers=paula_headers).status_code == 404

    assert client.get(f"/api/v1/routines/{routine_id}", headers=paula_headers).status_code == 404
    assert client.post(f"/api/v1/routines/{routine_id}/complete-today", headers=paula_headers).status_code == 404
    assert client.post(f"/api/v1/routines/{routine_id}/resume", headers=paula_headers).status_code == 404
    assert client.delete(f"/api/v1/routines/{routine_id}", headers=paula_headers).status_code == 404

    assert client.post(f"/api/v1/pomodoro/sessions/{pomo_id}/complete", headers=paula_headers).status_code == 404
    assert client.post(f"/api/v1/pomodoro/sessions/{pomo_id}/cancel", headers=paula_headers).status_code == 404

    assert (
        client.put(
            f"/api/v1/reminders/{rem_id}",
            headers=paula_headers,
            json={"completadahoy": True},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/reminders/{rem_id}", headers=paula_headers).status_code == 404

    assert (
        client.put(
            f"/api/v1/personal-records/{rec_id}",
            headers=paula_headers,
            json={"valoractual": 1.0},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/personal-records/{rec_id}", headers=paula_headers).status_code == 404

    assert (
        client.patch(
            f"/api/v1/financial-goals/{goal_id}/progress",
            headers=paula_headers,
            json={"monto_avance": 50.0},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/financial-goals/{goal_id}", headers=paula_headers).status_code == 404


def test_sql_injection_payloads_are_safely_neutralized(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """Verifica que vectores de Inyección SQL (SQLi) no vulneren la autenticación ni corrompan tablas."""
    headers = registered_user["headers"]

    # Intento de bypass de login con SQLi
    sqli_login = client.post(
        "/api/v1/auth/login",
        json={
            "correo": "admin@dopa.app",
            "contrasena": "' OR '1'='1' --",
        },
    )
    assert sqli_login.status_code == 401

    # Creación de tarea con payload SQLi -> se almacena como literal inocuo parametrizado
    sqli_title = "Tarea'; DROP TABLE usuario; SELECT * FROM tarea WHERE '1'='1"
    create_resp = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"titulo": sqli_title, "prioridad": "Media"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["titulo"] == sqli_title

    # Verificar que la tabla `usuario` y el perfil siguen intactos
    me_check = client.get("/api/v1/auth/me", headers=headers)
    assert me_check.status_code == 200
    assert me_check.json()["nombre"] == "Fred"


def test_idempotency_under_repeated_network_retries(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """Garantiza que 10 reintentos seguidos con `X-Transaction-Id` otorguen puntos una única vez."""
    headers = registered_user["headers"]
    task_id = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"titulo": "Tarea para prueba de estrés de idempotencia"},
    ).json()["id"]

    tx_headers = {**headers, "X-Transaction-Id": "tx-mobile-retry-999"}
    responses = [
        client.post(f"/api/v1/tasks/{task_id}/complete", headers=tx_headers).json()
        for _ in range(10)
    ]

    assert responses[0]["puntos_ganados"] == 10
    assert responses[0]["idempotente"] is False
    for retry_resp in responses[1:]:
        assert retry_resp["puntos_ganados"] == 0
        assert retry_resp["idempotente"] is True
        assert retry_resp["puntos_totales"] == 10


def test_rnf04_crud_and_dashboard_performance_under_50ms(
    client: TestClient,
    registered_user: dict[str, Any],
) -> None:
    """RNF-04: Verifica que el tiempo promedio de respuesta por petición sea `< 50 ms`."""
    headers = registered_user["headers"]
    latencies_ms: list[float] = []

    for i in range(15):
        t0 = time.perf_counter()
        r_create = client.post(
            "/api/v1/tasks",
            headers=headers,
            json={"titulo": f"Micro-tarea rápida #{i}", "prioridad": "Baja"},
        )
        t1 = time.perf_counter()
        assert r_create.status_code == 201
        latencies_ms.append((t1 - t0) * 1000.0)

        t2 = time.perf_counter()
        r_dash = client.get("/api/v1/dashboard", headers=headers)
        t3 = time.perf_counter()
        assert r_dash.status_code == 200
        latencies_ms.append((t3 - t2) * 1000.0)

    avg_latency_ms = sum(latencies_ms) / len(latencies_ms)
    assert avg_latency_ms < 50.0, f"Latencia promedio demasiado alta: {avg_latency_ms:.2f} ms"
