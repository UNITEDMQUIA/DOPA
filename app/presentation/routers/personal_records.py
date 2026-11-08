"""Controlador REST de Seguimiento Personal: Sueño y Humor (`/api/v1/personal-records`) — Proyecto DOPA."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.services import PersonalRecordService
from app.data.database import get_db
from app.domain.models import Usuario
from app.presentation.dependencies import get_current_user
from app.transfer.dtos import (
    PersonalRecordCreateRequestDTO,
    PersonalRecordListResponseDTO,
    PersonalRecordResponseDTO,
    PersonalRecordUpdateRequestDTO,
)

router = APIRouter(prefix="/api/v1/personal-records", tags=["8. Seguimiento Personal (Sueño y Humor)"])


@router.get(
    "",
    response_model=PersonalRecordListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar registros personales con tendencia descriptiva no médica (HU-08, RNF-09)",
)
def list_personal_records(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonalRecordListResponseDTO:
    return PersonalRecordService(db).list_records(usuario, limit=limit, offset=offset)


@router.post(
    "",
    response_model=PersonalRecordResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear registro personal de sueño, energía o humor con cálculo automático de progreso (HU-08)",
)
def create_personal_record(
    dto: PersonalRecordCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonalRecordResponseDTO:
    return PersonalRecordService(db).create_record(usuario, dto)


@router.put(
    "/{record_id}",
    response_model=PersonalRecordResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Actualizar registro personal y recalcular porcentaje de progreso (RF-18, RF-19)",
)
def update_personal_record(
    record_id: int,
    dto: PersonalRecordUpdateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PersonalRecordResponseDTO:
    return PersonalRecordService(db).update_record(usuario, record_id, dto)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un registro personal",
)
def delete_personal_record(
    record_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    PersonalRecordService(db).delete_record(usuario, record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
