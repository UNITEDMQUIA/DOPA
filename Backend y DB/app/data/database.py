"""Configuración de conexión a PostgreSQL y sesión transaccional de SQLAlchemy.

Agente Responsable: 3.1. Agente Arquitecto de Datos (Database & ORM Agent)
Soporta PostgreSQL en producción/Docker y SQLite en memoria para pruebas aisladas.
"""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DATABASE_URL = "postgresql+psycopg://dopa_user:dopa_pass@localhost:5432/dopa_db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool if ":memory:" in DATABASE_URL else None,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """ Proveedor de sesión de base de datos por petición (FastAPI Dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
