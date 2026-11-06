"""Controlador REST de Rutinas Libres de Culpa (`/api/v1/routines`) — Proyecto DOPA."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.services import RoutineService
from app.data.database import get_db
from app.domain.models import Usuario
from app.presentation.dependencies import get_current_user, get_idempotency_key
from app.transfer.dtos import (
    RoutineCompleteResponseDTO,
    RoutineCreateRequestDTO,
    RoutineDetailResponseDTO,
    RoutineListResponseDTO,
    RoutineResponseDTO,
    RoutineResumeResponseDTO,
    RoutineUpdateRequestDTO,
)

router = APIRouter(prefix="/api/v1/routines", tags=["4. Rutinas Libres de Culpa"])


@router.get(
    "",
    response_model=RoutineListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar rutinas del usuario autenticado con paginación (HU-04, RF-06)",
)
def list_routines(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineListResponseDTO:
    return RoutineService(db).list_routines(usuario, limit=limit, offset=offset)


@router.post(
    "",
    response_model=RoutineResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una rutina recurrente (HU-04, RF-06)",
)
def create_routine(
    dto: RoutineCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineResponseDTO:
    return RoutineService(db).create_routine(usuario, dto)


@router.get(
    "/{routine_id}",
    response_model=RoutineDetailResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Consultar una rutina y sus tareas asociadas (RF-07)",
)
def get_routine(
    routine_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineDetailResponseDTO:
    return RoutineService(db).get_routine(usuario, routine_id)


@router.put(
    "/{routine_id}",
    response_model=RoutineResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Editar una rutina existente (RF-07)",
)
def update_routine(
    routine_id: int,
    dto: RoutineUpdateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineResponseDTO:
    return RoutineService(db).update_routine(usuario, routine_id, dto)


@router.delete(
    "/{routine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una rutina",
)
def delete_routine(
    routine_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    RoutineService(db).delete_routine(usuario, routine_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{routine_id}/complete-today",
    response_model=RoutineCompleteResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Marcar rutina completada hoy de forma idempotente y otorgar +10 dopamina",
)
def complete_routine_today(
    routine_id: int,
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineCompleteResponseDTO:
    return RoutineService(db).complete_today(
        usuario=usuario,
        routine_id=routine_id,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/{routine_id}/resume",
    response_model=RoutineResumeResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Retomar rutina tras inactividad sin penalizaciones ni pérdida de puntos (HU-11, RF-16, RF-24)",
)
def resume_routine(
    routine_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineResumeResponseDTO:
    return RoutineService(db).resume_routine(usuario, routine_id)
