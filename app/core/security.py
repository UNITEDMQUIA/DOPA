"""Seguridad Criptográfica y Autenticación JWT Stateless — Proyecto DOPA.

Agente Responsable: 3.2. Agente de API y Lógica de Negocio (Backend Core Agent)
Cumple RNF-06 (hashing bcrypt de contraseñas), RNF-08 (sesiones seguras JWT) y Sección 4.2.1.
"""

from datetime import datetime, timedelta, timezone
import os
from typing import Any
import uuid

import bcrypt
import jwt

from app.transfer.dtos import UserPreferencesDTO

SECRET_KEY = os.getenv("DOPA_JWT_SECRET_KEY", "dopa-super-secret-jwt-key-2026-tdah-safe-backend")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Almacén en memoria para tokens revocados en logout y preferencias de usuario (HU-12, RF-23)
_REVOKED_TOKENS: set[str] = set()
_USER_PREFERENCES: dict[int, UserPreferencesDTO] = {}


def hash_password(plain_password: str) -> str:
    """Genera un hash seguro con bcrypt (RNF-06: nunca almacenar texto plano)."""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash bcrypt almacenado."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    user_id: int,
    correo: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Emite un Access Token JWT Stateless de corta duración."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": correo,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: int,
    correo: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Emite un Refresh Token JWT Stateless de larga duración."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": correo,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Decodifica y valida un token JWT, verificando expiración, tipo y revocación."""
    if is_token_revoked(token):
        raise ValueError("El token de sesión ha sido cerrado o revocado.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("El token de sesión ha expirado.") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("El token de sesión es inválido.") from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise ValueError(f"Se esperaba un token de tipo '{expected_type}', pero se recibió '{token_type}'.")
    return payload


def revoke_token(token: str) -> None:
    """Registra el token en la lista de revocación al cerrar sesión."""
    if token:
        _REVOKED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    """Indica si el token fue revocado explícitamente."""
    return token in _REVOKED_TOKENS


def get_user_preferences(user_id: int) -> UserPreferencesDTO:
    """Obtiene las preferencias configurables del usuario (HU-12, RF-23)."""
    if user_id not in _USER_PREFERENCES:
        _USER_PREFERENCES[user_id] = UserPreferencesDTO()
    return _USER_PREFERENCES[user_id]


def set_user_preferences(user_id: int, prefs: UserPreferencesDTO) -> UserPreferencesDTO:
    """Actualiza las preferencias configurables del usuario."""
    _USER_PREFERENCES[user_id] = prefs
    return prefs
