"""Controlador REST de Autenticación y Preferencias (`/api/v1/auth`) — Proyecto DOPA."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.services import AuthService
from app.data.database import get_db
from app.domain.models import Usuario
from app.presentation.dependencies import get_current_token, get_current_user
from app.transfer.dtos import (
    AuthTokensResponseDTO,
    LoginRequestDTO,
    LogoutResponseDTO,
    RefreshTokenRequestDTO,
    RegisterRequestDTO,
    UserPreferencesDTO,
    UserResponseDTO,
)

router = APIRouter(prefix="/api/v1/auth", tags=["1. Autenticación y Preferencias"])


@router.post(
    "/register",
    response_model=AuthTokensResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario en DOPA (HU-01, RF-01)",
)
def register(
    dto: RegisterRequestDTO,
    db: Session = Depends(get_db),
) -> AuthTokensResponseDTO:
    return AuthService(db).register(dto)


@router.post(
    "/login",
    response_model=AuthTokensResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión con correo y contraseña (HU-01, RF-02)",
)
def login(
    dto: LoginRequestDTO,
    db: Session = Depends(get_db),
) -> AuthTokensResponseDTO:
    return AuthService(db).login(dto)


@router.post(
    "/refresh",
    response_model=AuthTokensResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Renovar Access Token usando Refresh Token (Stateless JWT)",
)
def refresh_token(
    dto: RefreshTokenRequestDTO,
    db: Session = Depends(get_db),
) -> AuthTokensResponseDTO:
    return AuthService(db).refresh(dto)


@router.post(
    "/logout",
    response_model=LogoutResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión activa e invalidar Access Token (HU-01)",
)
def logout(
    token: str = Depends(get_current_token),
    _usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponseDTO:
    return AuthService(db).logout(token)


@router.get(
    "/me",
    response_model=UserResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obtener perfil, puntos de dopamina, nivel y preferencias del usuario autenticado",
)
def get_me(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponseDTO:
    return AuthService(db).get_profile(usuario)


@router.put(
    "/preferences",
    response_model=UserResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Configurar preferencias de concentración, descanso y notificaciones (HU-12, RF-23)",
)
def update_preferences(
    dto: UserPreferencesDTO,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponseDTO:
    return AuthService(db).update_preferences(usuario, dto)
