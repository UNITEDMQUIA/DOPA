"""Configuración global de PyTest y Fixtures aisladas — Proyecto DOPA.

Agente Responsable: 4. Stack de Agentes de QA (Unit, Integration, E2E & SecOps)
Provee una base de datos SQLite en memoria aislada por cada prueba (`StaticPool` + `PRAGMA foreign_keys=ON`),
limpieza de cachés en memoria y clientes autenticados para `Fred` y `Paula`.
"""

from typing import Any, Generator

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import security, services
from app.data.database import Base, get_db
from app.main import app

TEST_SQLITE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Crea un esquema limpio por test y reinicia los almacenes en memoria."""
    security._REVOKED_TOKENS.clear()
    security._USER_PREFERENCES.clear()
    services._IDEMPOTENCY_CACHE.clear()
    services._USER_ENERGY_TODAY.clear()

    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP de pruebas con override transaccional de `get_db`."""

    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client: TestClient) -> dict[str, Any]:
    """Usuario principal de pruebas (`Fred`) registrado y autenticado."""
    payload = {
        "nombre": "Fred",
        "correo": "fred@dopa.app",
        "contrasena": "FredPassword2026!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "id": data["usuario"]["id"],
        "nombre": data["usuario"]["nombre"],
        "correo": data["usuario"]["correo"],
        "contrasena": payload["contrasena"],
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "usuario": data["usuario"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


@pytest.fixture()
def second_user(client: TestClient) -> dict[str, Any]:
    """Segundo usuario de pruebas (`Paula`) para validar aislamiento de privacidad (RNF-08, RNF-09)."""
    payload = {
        "nombre": "Paula",
        "correo": "paula@dopa.app",
        "contrasena": "PaulaPassword2026!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "id": data["usuario"]["id"],
        "nombre": data["usuario"]["nombre"],
        "correo": data["usuario"]["correo"],
        "contrasena": payload["contrasena"],
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "usuario": data["usuario"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }
