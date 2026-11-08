"""Controlador REST del Panel Principal / Inicio (`/api/v1/dashboard`) — Proyecto DOPA."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.services import DashboardService
from app.data.database import get_db
from app.domain.models import Usuario
from app.presentation.dependencies import get_current_user
from app.transfer.dtos import (
    DashboardResponseDTO,
    EnergyCheckinRequestDTO,
    EnergyCheckinResponseDTO,
    TaskResponseDTO,
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["2. Panel Principal (Dashboard)"])


@router.get(
    "",
    response_model=DashboardResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener resumen diario del Panel Principal '¡Hola, {nombre}!' (HU-10, RF-22)",
)
def get_dashboard(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponseDTO:
    return DashboardService(db).get_dashboard(usuario)


@router.post(
    "/energy-checkin",
    response_model=EnergyCheckinResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar chequeo diario '¿Cómo está tu energía hoy?' (Figuras 2 y 7)",
)
def energy_checkin(
    dto: EnergyCheckinRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnergyCheckinResponseDTO:
    return DashboardService(db).register_energy_checkin(usuario, dto)


@router.get(
    "/quick-task",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Botón '¡Hacer algo fácil!': obtener la tarea pendiente de menor fricción (Figuras 3 y 7)",
)
def get_quick_task(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponseDTO:
    return DashboardService(db).get_quick_task(usuario)
