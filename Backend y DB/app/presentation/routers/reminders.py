"""Controlador REST de Recordatorios (`/api/v1/reminders`) — Proyecto DOPA."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.services import ReminderService
from app.data.database import get_db
from app.domain.models import TipoRecordatorioEnum, Usuario
from app.presentation.dependencies import get_current_user
from app.transfer.dtos import (
    ReminderCreateRequestDTO,
    ReminderListResponseDTO,
    ReminderResponseDTO,
    ReminderUpdateRequestDTO,
)

router = APIRouter(prefix="/api/v1/reminders", tags=["6. Recordatorios"])


@router.get(
    "",
    response_model=ReminderListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar recordatorios del usuario con paginación y filtros (HU-05, RF-08)",
)
def list_reminders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tipo: Optional[TipoRecordatorioEnum] = Query(default=None),
    completadahoy: Optional[bool] = Query(default=None),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderListResponseDTO:
    return ReminderService(db).list_reminders(
        usuario=usuario,
        limit=limit,
        offset=offset,
        tipo=tipo,
        completadahoy=completadahoy,
    )


@router.post(
    "",
    response_model=ReminderResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Programar un nuevo recordatorio de Tarea, Rutina o Compromiso (HU-05, RF-08)",
)
def create_reminder(
    dto: ReminderCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponseDTO:
    return ReminderService(db).create_reminder(usuario, dto)


@router.put(
    "/{reminder_id}",
    response_model=ReminderResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Actualizar o desactivar un recordatorio al completarse (HU-05, RF-09)",
)
def update_reminder(
    reminder_id: int,
    dto: ReminderUpdateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponseDTO:
    return ReminderService(db).update_reminder(usuario, reminder_id, dto)


@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un recordatorio",
)
def delete_reminder(
    reminder_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    ReminderService(db).delete_reminder(usuario, reminder_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
