"""Controlador REST de Enfoque Pomodoro y Descanso (`/api/v1/pomodoro`) — Proyecto DOPA."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.services import PomodoroService
from app.data.database import get_db
from app.domain.models import Usuario
from app.presentation.dependencies import get_current_user, get_idempotency_key
from app.transfer.dtos import (
    LowStimulusCatalogResponseDTO,
    PomodoroActionResponseDTO,
    PomodoroCreateRequestDTO,
    PomodoroListResponseDTO,
    PomodoroResponseDTO,
)

router = APIRouter(prefix="/api/v1/pomodoro", tags=["5. Enfoque Pomodoro y Descanso Suave"])


@router.post(
    "/sessions",
    response_model=PomodoroResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear e iniciar una sesión de enfoque corto (5 min / 25 min) (HU-06, RF-10)",
)
def create_session(
    dto: PomodoroCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PomodoroResponseDTO:
    return PomodoroService(db).create_session(usuario, dto)


@router.get(
    "/sessions",
    response_model=PomodoroListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar sesiones Pomodoro del usuario autenticado (RF-12)",
)
def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PomodoroListResponseDTO:
    return PomodoroService(db).list_sessions(usuario, limit=limit, offset=offset)


@router.post(
    "/sessions/{session_id}/complete",
    response_model=PomodoroActionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Registrar ciclo Pomodoro completado de forma idempotente y otorgar +5 dopamina (RF-12)",
)
def complete_session(
    session_id: int,
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PomodoroActionResponseDTO:
    return PomodoroService(db).complete_session(
        usuario=usuario,
        session_id=session_id,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/sessions/{session_id}/cancel",
    response_model=PomodoroActionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Cancelar sesión en curso sin contabilizar ciclo ni restar puntos (HU-06)",
)
def cancel_session(
    session_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PomodoroActionResponseDTO:
    return PomodoroService(db).cancel_session(usuario, session_id)


@router.get(
    "/low-stimulus-activities",
    response_model=LowStimulusCatalogResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener catálogo 'Un break suave' con Respiración 4-4 y Estiramiento (Figuras 12 y 13)",
)
def get_low_stimulus_activities(
    _usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LowStimulusCatalogResponseDTO:
    return PomodoroService(db).get_low_stimulus_activities()
