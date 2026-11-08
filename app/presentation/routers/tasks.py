"""Controlador REST de Gestión de Tareas y Micro-pasos (`/api/v1/tasks`) — Proyecto DOPA."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.services import TaskService
from app.data.database import get_db
from app.domain.models import PrioridadTareaEnum, Usuario
from app.presentation.dependencies import get_current_user, get_idempotency_key
from app.transfer.dtos import (
    SubtaskCreateRequestDTO,
    SubtaskListResponseDTO,
    SubtaskResponseDTO,
    SubtaskUpdateRequestDTO,
    TaskCompleteResponseDTO,
    TaskCreateRequestDTO,
    TaskListResponseDTO,
    TaskResponseDTO,
    TaskUpdateRequestDTO,
)

router = APIRouter(prefix="/api/v1/tasks", tags=["3. Tareas y Micro-pasos"])


@router.get(
    "",
    response_model=TaskListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar tareas 'Poquito a poquito' con paginación y filtros (HU-02, RF-03)",
)
def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    completada: Optional[bool] = Query(default=None),
    prioridad: Optional[PrioridadTareaEnum] = Query(default=None),
    id_rutina: Optional[int] = Query(default=None, gt=0),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskListResponseDTO:
    return TaskService(db).list_tasks(
        usuario=usuario,
        limit=limit,
        offset=offset,
        completada=completada,
        prioridad=prioridad,
        id_rutina=id_rutina,
    )


@router.post(
    "",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una tarea con prioridad y micro-pasos opcionales (HU-02, HU-03)",
)
def create_task(
    dto: TaskCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponseDTO:
    return TaskService(db).create_task(usuario, dto)


@router.get(
    "/{task_id}",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalle de una tarea y sus micro-pasos 'Enfoque suave' (Figura 9)",
)
def get_task(
    task_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponseDTO:
    return TaskService(db).get_task(usuario, task_id)


@router.put(
    "/{task_id}",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Editar una tarea existente (RF-04)",
)
def update_task(
    task_id: int,
    dto: TaskUpdateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponseDTO:
    return TaskService(db).update_task(usuario, task_id, dto)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una tarea y sus micro-pasos en cascada (RF-04)",
)
def delete_task(
    task_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    TaskService(db).delete_task(usuario, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{task_id}/complete",
    response_model=TaskCompleteResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Completar tarea de forma idempotente y otorgar +10 dopamina (Figura 10, RF-13)",
)
def complete_task(
    task_id: int,
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskCompleteResponseDTO:
    return TaskService(db).complete_task(
        usuario=usuario,
        task_id=task_id,
        idempotency_key=idempotency_key,
    )


@router.post(
    "/{task_id}/subtasks",
    response_model=SubtaskResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar un micro-paso (`subtarea`) a una tarea (HU-03, RF-05)",
)
def create_subtask(
    task_id: int,
    dto: SubtaskCreateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubtaskResponseDTO:
    return TaskService(db).create_subtask(usuario, task_id, dto)


@router.get(
    "/{task_id}/subtasks",
    response_model=SubtaskListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar micro-pasos de una tarea y su porcentaje de avance (Figura 9)",
)
def list_subtasks(
    task_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubtaskListResponseDTO:
    return TaskService(db).list_subtasks(usuario, task_id)


@router.patch(
    "/{task_id}/subtasks/{subtask_id}",
    response_model=SubtaskResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Marcar o editar un micro-paso individual (HU-03, RF-05)",
)
def update_subtask(
    task_id: int,
    subtask_id: int,
    dto: SubtaskUpdateRequestDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubtaskResponseDTO:
    return TaskService(db).update_subtask(usuario, task_id, subtask_id, dto)


@router.delete(
    "/{task_id}/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un micro-paso de una tarea",
)
def delete_subtask(
    task_id: int,
    subtask_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    TaskService(db).delete_subtask(usuario, task_id, subtask_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
