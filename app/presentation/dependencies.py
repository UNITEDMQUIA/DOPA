"""Filtro de Seguridad JWT Stateless y Dependencias de Presentación — Proyecto DOPA.

Agente Responsable: 3.2. Agente de API y Lógica de Negocio (Backend Core Agent)
Referencia Arquitectónica: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf — Sección 4.2.1.
Intercepta las peticiones entrantes desde el cliente móvil, valida la firma criptográfica
y expiración del Access Token y rechaza con HTTP 401 accesos inválidos o revocados.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.data.database import get_db
from app.data.repositories import UsuarioRepository
from app.domain.models import Usuario

security_scheme = HTTPBearer(auto_error=False)


def get_current_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> str:
    """Extrae el token Bearer del encabezado Authorization o lanza HTTP 401."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Debe enviar un Bearer Access Token válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_current_token),
    db: Session = Depends(get_db),
) -> Usuario:
    """Valida el JWT Stateless y recupera la entidad del usuario autenticado."""
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    repo = UsuarioRepository(db)
    usuario = repo.get_by_id(user_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario asociado a la sesión no existe.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def get_idempotency_key(
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    x_transaction_id: Optional[str] = Header(default=None, alias="X-Transaction-Id"),
) -> Optional[str]:
    """Extrae la clave de idempotencia enviada por el cliente móvil ante reintentos de red."""
    return idempotency_key or x_transaction_id
