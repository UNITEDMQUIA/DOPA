"""Controlador REST de Gamificación y Dopamina (`/api/v1/gamification`) — Proyecto DOPA."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.services import GamificationService
from app.data.database import get_db
from app.domain.models import Usuario
from app.presentation.dependencies import get_current_user
from app.transfer.dtos import (
    GamificationSummaryResponseDTO,
    RewardCreateRequestDTO,
    RewardListResponseDTO,
    RewardResponseDTO,
)

router = APIRouter(prefix="/api/v1/gamification", tags=["7. Gamificación y Dopamina"])


@router.get(
    "/summary",
    response_model=GamificationSummaryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener resumen 'Mi Dopamina hoy', nivel, progreso y rachas libres de culpa (Figuras 6 y 11)",
)
def get_gamification_summary(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GamificationSummaryResponseDTO:
    return GamificationService(db).get_summary(usuario)


@router.get(
    "/rewards",
    response_model=RewardListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar recompensas de dopamina disponibles y desbloqueadas (HU-07, RF-15)",
)
def list_rewards(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RewardListResponseDTO:
    return GamificationService(db).list_rewards(usuario, limit=limit, offset=offset)


@router.post(
    "/rewards",
    response_model=RewardResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva recompensa de dopamina (RF-15)",
)
def create_reward(
    dto: RewardCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RewardResponseDTO:
    return GamificationService(db).create_reward(usuario, dto)


@router.post(
    "/rewards/{reward_id}/unlock",
    response_model=RewardResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Desbloquear una recompensa al cumplir puntos o completar tarea asociada (HU-07, RF-15)",
)
def unlock_reward(
    reward_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RewardResponseDTO:
    return GamificationService(db).unlock_reward(usuario, reward_id)
