"""Controlador REST de Metas Financieras (`/api/v1/financial-goals`) — Proyecto DOPA."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.services import FinancialGoalService
from app.data.database import get_db
from app.domain.models import Usuario
from app.presentation.dependencies import get_current_user
from app.transfer.dtos import (
    FinancialGoalCreateRequestDTO,
    FinancialGoalListResponseDTO,
    FinancialGoalProgressRequestDTO,
    FinancialGoalResponseDTO,
)

router = APIRouter(prefix="/api/v1/financial-goals", tags=["9. Metas Financieras"])


@router.get(
    "",
    response_model=FinancialGoalListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar metas financieras del usuario autenticado (HU-09, RNF-09)",
)
def list_financial_goals(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialGoalListResponseDTO:
    return FinancialGoalService(db).list_goals(usuario, limit=limit, offset=offset)


@router.post(
    "",
    response_model=FinancialGoalResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una meta financiera con cálculo automático de porcentaje (HU-09, RF-20)",
)
def create_financial_goal(
    dto: FinancialGoalCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialGoalResponseDTO:
    return FinancialGoalService(db).create_goal(usuario, dto)


@router.patch(
    "/{goal_id}/progress",
    response_model=FinancialGoalResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Registrar avance financiero y recalcular progresoporcentaje automáticamente (RF-21)",
)
def update_financial_goal_progress(
    goal_id: int,
    dto: FinancialGoalProgressRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialGoalResponseDTO:
    return FinancialGoalService(db).update_progress(usuario, goal_id, dto)


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una meta financiera",
)
def delete_financial_goal(
    goal_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    FinancialGoalService(db).delete_goal(usuario, goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
