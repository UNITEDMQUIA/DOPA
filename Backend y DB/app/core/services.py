"""Implementación de Servicios de Lógica de Negocio — Proyecto DOPA.

Agente Responsable: 3.2. Agente de API y Lógica de Negocio (Backend Core Agent)
Referencia Arquitectónica: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf — Sección 4.2.3.
Incluye:
- Operaciones idempotentes ante microcortes de red móvil (`Idempotency-Key` y validación de estado).
- Motor de gamificación de dopamina libre de culpa (`HU-07`, `HU-11`, `RF-13` a `RF-16`).
- Cálculo automático de porcentaje de progreso en registros personales y metas financieras (`RF-21`).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.interfaces import (
    IAuthService,
    IDashboardService,
    IFinancialGoalService,
    IGamificationService,
    IPersonalRecordService,
    IPomodoroService,
    IReminderService,
    IRoutineService,
    ITaskService,
)
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_preferences,
    hash_password,
    revoke_token,
    set_user_preferences,
    verify_password,
)
from app.data.repositories import (
    MetaFinancieraRepository,
    PanelPrincipalRepository,
    RecordatorioRepository,
    RecompensaRepository,
    RegistroPersonalRepository,
    RutinaRepository,
    SesionPomodoroRepository,
    SubtareaRepository,
    TareaRepository,
    UsuarioRepository,
)
from app.domain.models import PrioridadTareaEnum, TipoRecordatorioEnum, Usuario
from app.transfer.dtos import (
    AuthTokensResponseDTO,
    DashboardResponseDTO,
    EnergyCheckinRequestDTO,
    EnergyCheckinResponseDTO,
    FinancialGoalCreateRequestDTO,
    FinancialGoalListResponseDTO,
    FinancialGoalProgressRequestDTO,
    FinancialGoalResponseDTO,
    GamificationSummaryResponseDTO,
    LoginRequestDTO,
    LogoutResponseDTO,
    LowStimulusActivityDTO,
    LowStimulusCatalogResponseDTO,
    PersonalRecordCreateRequestDTO,
    PersonalRecordListResponseDTO,
    PersonalRecordResponseDTO,
    PersonalRecordUpdateRequestDTO,
    PomodoroActionResponseDTO,
    PomodoroCreateRequestDTO,
    PomodoroListResponseDTO,
    PomodoroResponseDTO,
    RefreshTokenRequestDTO,
    RegisterRequestDTO,
    ReminderCreateRequestDTO,
    ReminderListResponseDTO,
    ReminderResponseDTO,
    ReminderUpdateRequestDTO,
    RewardCreateRequestDTO,
    RewardListResponseDTO,
    RewardResponseDTO,
    RoutineCompleteResponseDTO,
    RoutineCreateRequestDTO,
    RoutineDetailResponseDTO,
    RoutineListResponseDTO,
    RoutineResponseDTO,
    RoutineResumeResponseDTO,
    RoutineUpdateRequestDTO,
    SubtaskCreateRequestDTO,
    SubtaskListResponseDTO,
    SubtaskResponseDTO,
    SubtaskUpdateRequestDTO,
    TaskCompleteResponseDTO,
    TaskCreateRequestDTO,
    TaskListResponseDTO,
    TaskResponseDTO,
    TaskUpdateRequestDTO,
    UserPreferencesDTO,
    UserResponseDTO,
)
from app.transfer.mappers import (
    DashboardMapper,
    MetaFinancieraMapper,
    PomodoroMapper,
    RecordatorioMapper,
    RecompensaMapper,
    RegistroPersonalMapper,
    RutinaMapper,
    TareaMapper,
    UsuarioMapper,
)

# Caché en memoria de claves de idempotencia móvil para evitar duplicar puntos ante reintentos
_IDEMPOTENCY_CACHE: dict[str, Any] = {}
_USER_ENERGY_TODAY: dict[int, dict[str, Optional[str]]] = {}


def calculate_progress_percentage(valor_actual: Decimal, valor_objetivo: Decimal) -> Decimal:
    """Calcula `min(100.00, round((valoractual / valorobjetivo) * 100, 2))`."""
    if valor_objetivo <= Decimal("0"):
        return Decimal("0.00")
    if valor_actual <= Decimal("0"):
        return Decimal("0.00")
    raw = (valor_actual / valor_objetivo) * Decimal("100")
    bounded = min(Decimal("100.00"), raw)
    return bounded.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# =====================================================================
# 1. SERVICIO DE AUTENTICACIÓN Y PREFERENCIAS
# =====================================================================


class AuthService(IAuthService):
    """Gestiona registro, login, renovación JWT, cierre de sesión y preferencias (HU-01, HU-12)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UsuarioRepository(db)

    def register(self, dto: RegisterRequestDTO) -> AuthTokensResponseDTO:
        existente = self.user_repo.get_by_email(dto.correo)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo electrónico ya se encuentra registrado en DOPA.",
            )

        hashed = hash_password(dto.contrasena)
        usuario = self.user_repo.create(
            nombre=dto.nombre,
            correo=dto.correo,
            contrasenahash=hashed,
        )
        prefs = get_user_preferences(usuario.id)
        access_token = create_access_token(usuario.id, usuario.correo)
        refresh_token = create_refresh_token(usuario.id, usuario.correo)

        return AuthTokensResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            usuario=UsuarioMapper.to_dto(usuario, prefs),
        )

    def login(self, dto: LoginRequestDTO) -> AuthTokensResponseDTO:
        usuario = self.user_repo.get_by_email(dto.correo)
        if not usuario or not verify_password(dto.contrasena, usuario.contrasenahash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo electrónico o contraseña incorrectos.",
            )

        prefs = get_user_preferences(usuario.id)
        access_token = create_access_token(usuario.id, usuario.correo)
        refresh_token = create_refresh_token(usuario.id, usuario.correo)

        return AuthTokensResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            usuario=UsuarioMapper.to_dto(usuario, prefs),
        )

    def refresh(self, dto: RefreshTokenRequestDTO) -> AuthTokensResponseDTO:
        try:
            payload = decode_token(dto.refresh_token, expected_type="refresh")
            user_id = int(payload["sub"])
        except (ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        usuario = self.user_repo.get_by_id(user_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El usuario asociado al token ya no existe.",
            )

        prefs = get_user_preferences(usuario.id)
        new_access_token = create_access_token(usuario.id, usuario.correo)
        new_refresh_token = create_refresh_token(usuario.id, usuario.correo)

        return AuthTokensResponseDTO(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            usuario=UsuarioMapper.to_dto(usuario, prefs),
        )

    def logout(self, token: str) -> LogoutResponseDTO:
        revoke_token(token)
        return LogoutResponseDTO(
            mensaje="Sesión cerrada correctamente. ¡Descansa, te esperamos pronto!",
            sesion_cerrada=True,
        )

    def get_profile(self, usuario: Usuario) -> UserResponseDTO:
        prefs = get_user_preferences(usuario.id)
        return UsuarioMapper.to_dto(usuario, prefs)

    def update_preferences(self, usuario: Usuario, dto: UserPreferencesDTO) -> UserResponseDTO:
        prefs = set_user_preferences(usuario.id, dto)
        return UsuarioMapper.to_dto(usuario, prefs)


# =====================================================================
# 2. SERVICIO DE PANEL PRINCIPAL / DASHBOARD
# =====================================================================


class DashboardService(IDashboardService):
    """Consolida la vista principal '¡Hola, {nombre}!', chequeo de energía y tarea fácil (HU-10)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.panel_repo = PanelPrincipalRepository(db)
        self.tarea_repo = TareaRepository(db)
        self.rutina_repo = RutinaRepository(db)
        self.recordatorio_repo = RecordatorioRepository(db)
        self.registro_repo = RegistroPersonalRepository(db)
        self.user_repo = UsuarioRepository(db)

    def get_dashboard(self, usuario: Usuario) -> DashboardResponseDTO:
        panel = self.panel_repo.register_or_get_today(usuario.id)
        pendientes, completadas, total = self.tarea_repo.count_stats_by_user(usuario.id)
        tareas_prioritarias, _ = self.tarea_repo.list_by_user(
            id_usuario=usuario.id,
            limit=5,
            offset=0,
            completada=False,
        )
        rutinas_hoy, _ = self.rutina_repo.list_by_user(
            id_usuario=usuario.id,
            limit=5,
            offset=0,
        )
        recordatorios_proximos, _ = self.recordatorio_repo.list_by_user(
            id_usuario=usuario.id,
            limit=5,
            offset=0,
            completadahoy=False,
        )

        estado_cache = _USER_ENERGY_TODAY.get(usuario.id, {})
        energia_hoy = estado_cache.get("energia") or "media"
        humor_hoy = estado_cache.get("humor")
        prefs = get_user_preferences(usuario.id)

        return DashboardMapper.to_dto(
            panel=panel,
            usuario=usuario,
            estado_energia_hoy=energia_hoy,
            humor_hoy=humor_hoy,
            pendientes=pendientes,
            completadas_hoy=completadas,
            total_hoy=total,
            tareas_prioritarias=tareas_prioritarias,
            rutinas_hoy=rutinas_hoy,
            recordatorios_proximos=recordatorios_proximos,
            meta_diaria_puntos=prefs.meta_diaria_dopamina,
        )

    def register_energy_checkin(
        self,
        usuario: Usuario,
        dto: EnergyCheckinRequestDTO,
    ) -> EnergyCheckinResponseDTO:
        mapa_valor = {
            "poquita": Decimal("2.00"),
            "media": Decimal("3.50"),
            "a tope": Decimal("5.00"),
        }
        valor_actual = mapa_valor.get(dto.nivel_energia, Decimal("3.50"))
        valor_objetivo = Decimal("5.00")
        progreso = calculate_progress_percentage(valor_actual, valor_objetivo)

        etiqueta_nombre = f"Energía diaria: {dto.nivel_energia}"
        if dto.humor:
            etiqueta_nombre += f" | Humor: {dto.humor}"

        registro = self.registro_repo.create(
            id_usuario=usuario.id,
            nombre=etiqueta_nombre,
            valorobjetivo=valor_objetivo,
            valoractual=valor_actual,
            progresoporcentaje=progreso,
        )

        if dto.horas_sueno is not None:
            sueno_actual = Decimal(str(dto.horas_sueno))
            sueno_obj = Decimal("8.00")
            sueno_prog = calculate_progress_percentage(sueno_actual, sueno_obj)
            self.registro_repo.create(
                id_usuario=usuario.id,
                nombre="Horas de sueño",
                valorobjetivo=sueno_obj,
                valoractual=sueno_actual,
                progresoporcentaje=sueno_prog,
            )

        _USER_ENERGY_TODAY[usuario.id] = {
            "energia": dto.nivel_energia,
            "humor": dto.humor,
        }

        sugerencias = {
            "poquita": "Está bien ir despacio hoy. Elige una sola micro-tarea de 5 minutos o toma un break suave.",
            "media": "Buen ritmo para avanzar 'Poquito a poquito' con tus tareas suaves de hoy.",
            "a tope": "¡Qué buena energía! Aprovecha un bloque de enfoque suave y recuerda hacer pausas.",
        }

        return EnergyCheckinResponseDTO(
            mensaje="¡Gracias por escuchar cómo te sientes hoy!",
            nivel_energia=dto.nivel_energia,
            humor=dto.humor,
            puntos_dopamina=int(usuario.puntos or 0),
            sugerencia_baja_friccion=sugerencias.get(dto.nivel_energia, sugerencias["media"]),
            registro_id=registro.id,
        )

    def get_quick_task(self, usuario: Usuario) -> TaskResponseDTO:
        tarea = self.tarea_repo.get_quickest_pending_task(usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="¡No tienes tareas pendientes por ahora! Disfruta tu descanso libre de culpa.",
            )
        return TareaMapper.to_dto(tarea)


# =====================================================================
# 3. SERVICIO DE TAREAS Y MICRO-PASOS
# =====================================================================


class TaskService(ITaskService):
    """Gestiona tareas principales, micro-pasos y completado idempotente con dopamina (HU-02, HU-03)."""

    PUNTOS_POR_TAREA = 10

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tarea_repo = TareaRepository(db)
        self.subtarea_repo = SubtareaRepository(db)
        self.rutina_repo = RutinaRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.recompensa_repo = RecompensaRepository(db)

    def list_tasks(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
        completada: Optional[bool] = None,
        prioridad: Optional[PrioridadTareaEnum] = None,
        id_rutina: Optional[int] = None,
    ) -> TaskListResponseDTO:
        items, total = self.tarea_repo.list_by_user(
            id_usuario=usuario.id,
            limit=limit,
            offset=offset,
            completada=completada,
            prioridad=prioridad,
            id_rutina=id_rutina,
        )
        pendientes, completadas_count, total_global = self.tarea_repo.count_stats_by_user(usuario.id)
        return TaskListResponseDTO(
            encabezado="Poquito a poquito",
            total=total,
            pendientes=pendientes,
            completadas=completadas_count,
            resumen_progreso=f"{completadas_count} de {total_global} listas",
            limit=limit,
            offset=offset,
            items=[TareaMapper.to_dto(t) for t in items],
        )

    def create_task(self, usuario: Usuario, dto: TaskCreateRequestDTO) -> TaskResponseDTO:
        if dto.id_rutina is not None:
            rutina = self.rutina_repo.get_by_id_and_user(dto.id_rutina, usuario.id)
            if not rutina:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="La rutina asociada no existe o no pertenece al usuario.",
                )

        tarea = self.tarea_repo.create(
            id_usuario=usuario.id,
            titulo=dto.titulo,
            descripcion=dto.descripcion,
            prioridad=dto.prioridad,
            fechavencimiento=dto.fechavencimiento,
            id_rutina=dto.id_rutina,
            subtareas_descripciones=dto.subtareas,
        )
        return TareaMapper.to_dto(tarea)

    def get_task(self, usuario: Usuario, task_id: int) -> TaskResponseDTO:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea solicitada no existe.",
            )
        return TareaMapper.to_dto(tarea)

    def update_task(
        self,
        usuario: Usuario,
        task_id: int,
        dto: TaskUpdateRequestDTO,
    ) -> TaskResponseDTO:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea solicitada no existe.",
            )

        if dto.id_rutina is not None:
            rutina = self.rutina_repo.get_by_id_and_user(dto.id_rutina, usuario.id)
            if not rutina:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="La rutina asociada no existe o no pertenece al usuario.",
                )

        campos = dto.model_dump(exclude_unset=True)
        actualizada = self.tarea_repo.update(tarea, **campos)
        return TareaMapper.to_dto(actualizada)

    def delete_task(self, usuario: Usuario, task_id: int) -> None:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea solicitada no existe.",
            )
        self.tarea_repo.delete(tarea)

    def complete_task(
        self,
        usuario: Usuario,
        task_id: int,
        idempotency_key: Optional[str] = None,
    ) -> TaskCompleteResponseDTO:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea solicitada no existe.",
            )

        primer_nombre = (usuario.nombre or "Usuario").split()[0]
        cache_key = f"task_complete:{usuario.id}:{task_id}:{idempotency_key}" if idempotency_key else None

        # Verificación de idempotencia (por clave de transacción o porque la tarea ya fue completada)
        if (cache_key and cache_key in _IDEMPOTENCY_CACHE) or tarea.completada:
            return TaskCompleteResponseDTO(
                mensaje_celebracion=f"¡Lo hiciste, {primer_nombre}!",
                puntos_ganados=0,
                puntos_totales=int(usuario.puntos or 0),
                nivel_actual=int(usuario.nivel or 1),
                idempotente=True,
                tarea=TareaMapper.to_dto(tarea),
                recompensas_desbloqueadas=[],
            )

        # Marcar todos los micro-pasos como completados junto con la tarea principal
        for sub in list(tarea.subtareas or []):
            if not sub.completada:
                sub.completada = True
                self.db.add(sub)

        tarea = self.tarea_repo.update(tarea, completada=True)
        usuario = self.user_repo.add_points_and_update_level(usuario, self.PUNTOS_POR_TAREA)
        recompensas_nuevas = self.recompensa_repo.auto_unlock_eligible(
            id_usuario=usuario.id,
            puntos_usuario=int(usuario.puntos or 0),
            id_tarea_completada=tarea.id,
        )

        respuesta = TaskCompleteResponseDTO(
            mensaje_celebracion=f"¡Lo hiciste, {primer_nombre}!",
            puntos_ganados=self.PUNTOS_POR_TAREA,
            puntos_totales=int(usuario.puntos or 0),
            nivel_actual=int(usuario.nivel or 1),
            idempotente=False,
            tarea=TareaMapper.to_dto(tarea),
            recompensas_desbloqueadas=[RecompensaMapper.to_dto(r) for r in recompensas_nuevas],
        )
        if cache_key:
            _IDEMPOTENCY_CACHE[cache_key] = respuesta
        return respuesta

    def create_subtask(
        self,
        usuario: Usuario,
        task_id: int,
        dto: SubtaskCreateRequestDTO,
    ) -> SubtaskResponseDTO:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea principal no existe.",
            )
        subtarea = self.subtarea_repo.create(
            id_tarea=tarea.id,
            descripcion=dto.descripcion,
            completada=False,
        )
        return TareaMapper.subtask_to_dto(subtarea)

    def list_subtasks(self, usuario: Usuario, task_id: int) -> SubtaskListResponseDTO:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea principal no existe.",
            )
        subtareas = self.subtarea_repo.list_by_task(tarea.id)
        total = len(subtareas)
        completadas = sum(1 for s in subtareas if s.completada)
        porcentaje = round((completadas / total) * 100.0, 2) if total > 0 else 0.0
        return SubtaskListResponseDTO(
            id_tarea=tarea.id,
            total_pasos=total,
            pasos_completados=completadas,
            progreso_pasos_porcentaje=porcentaje,
            items=[TareaMapper.subtask_to_dto(s) for s in subtareas],
        )

    def update_subtask(
        self,
        usuario: Usuario,
        task_id: int,
        subtask_id: int,
        dto: SubtaskUpdateRequestDTO,
    ) -> SubtaskResponseDTO:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea principal no existe.",
            )
        subtarea = self.subtarea_repo.get_by_id_and_task(subtask_id, tarea.id)
        if not subtarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El micro-paso solicitado no existe.",
            )
        actualizada = self.subtarea_repo.update(
            subtarea,
            descripcion=dto.descripcion,
            completada=dto.completada,
        )
        return TareaMapper.subtask_to_dto(actualizada)

    def delete_subtask(self, usuario: Usuario, task_id: int, subtask_id: int) -> None:
        tarea = self.tarea_repo.get_by_id_and_user(task_id, usuario.id)
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La tarea principal no existe.",
            )
        subtarea = self.subtarea_repo.get_by_id_and_task(subtask_id, tarea.id)
        if not subtarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El micro-paso solicitado no existe.",
            )
        self.subtarea_repo.delete(subtarea)


# =====================================================================
# 4. SERVICIO DE RUTINAS LIBRES DE CULPA
# =====================================================================


class RoutineService(IRoutineService):
    """Gestiona rutinas recurrentes y retomado libre de culpa (HU-04, HU-11, RF-16, RF-24)."""

    PUNTOS_POR_RUTINA = 10

    def __init__(self, db: Session) -> None:
        self.db = db
        self.rutina_repo = RutinaRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.recompensa_repo = RecompensaRepository(db)

    def list_routines(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> RoutineListResponseDTO:
        items, total = self.rutina_repo.list_by_user(
            id_usuario=usuario.id,
            limit=limit,
            offset=offset,
        )
        return RoutineListResponseDTO(
            total=total,
            limit=limit,
            offset=offset,
            items=[RutinaMapper.to_dto(r) for r in items],
        )

    def create_routine(self, usuario: Usuario, dto: RoutineCreateRequestDTO) -> RoutineResponseDTO:
        rutina = self.rutina_repo.create(
            id_usuario=usuario.id,
            nombre=dto.nombre,
            recurrencia=dto.recurrencia,
            hora=dto.hora,
        )
        return RutinaMapper.to_dto(rutina)

    def get_routine(self, usuario: Usuario, routine_id: int) -> RoutineDetailResponseDTO:
        rutina = self.rutina_repo.get_by_id_and_user(routine_id, usuario.id)
        if not rutina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La rutina solicitada no existe.",
            )
        return RutinaMapper.to_detail_dto(rutina)

    def update_routine(
        self,
        usuario: Usuario,
        routine_id: int,
        dto: RoutineUpdateRequestDTO,
    ) -> RoutineResponseDTO:
        rutina = self.rutina_repo.get_by_id_and_user(routine_id, usuario.id)
        if not rutina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La rutina solicitada no existe.",
            )
        campos = dto.model_dump(exclude_unset=True)
        actualizada = self.rutina_repo.update(rutina, **campos)
        return RutinaMapper.to_dto(actualizada)

    def delete_routine(self, usuario: Usuario, routine_id: int) -> None:
        rutina = self.rutina_repo.get_by_id_and_user(routine_id, usuario.id)
        if not rutina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La rutina solicitada no existe.",
            )
        self.rutina_repo.delete(rutina)

    def complete_today(
        self,
        usuario: Usuario,
        routine_id: int,
        idempotency_key: Optional[str] = None,
    ) -> RoutineCompleteResponseDTO:
        rutina = self.rutina_repo.get_by_id_and_user(routine_id, usuario.id)
        if not rutina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La rutina solicitada no existe.",
            )

        cache_key = f"routine_complete:{usuario.id}:{routine_id}:{idempotency_key}" if idempotency_key else None
        if (cache_key and cache_key in _IDEMPOTENCY_CACHE) or rutina.completadahoy:
            return RoutineCompleteResponseDTO(
                mensaje="¡Tu rutina de hoy ya estaba marcada como completada!",
                puntos_ganados=0,
                puntos_totales=int(usuario.puntos or 0),
                nivel_actual=int(usuario.nivel or 1),
                idempotente=True,
                rutina=RutinaMapper.to_dto(rutina),
            )

        rutina = self.rutina_repo.update(rutina, completadahoy=True)
        usuario = self.user_repo.add_points_and_update_level(usuario, self.PUNTOS_POR_RUTINA)
        self.recompensa_repo.auto_unlock_eligible(
            id_usuario=usuario.id,
            puntos_usuario=int(usuario.puntos or 0),
        )

        respuesta = RoutineCompleteResponseDTO(
            mensaje=f"¡Rutina '{rutina.nombre}' completada hoy! +{self.PUNTOS_POR_RUTINA} dopamina.",
            puntos_ganados=self.PUNTOS_POR_RUTINA,
            puntos_totales=int(usuario.puntos or 0),
            nivel_actual=int(usuario.nivel or 1),
            idempotente=False,
            rutina=RutinaMapper.to_dto(rutina),
        )
        if cache_key:
            _IDEMPOTENCY_CACHE[cache_key] = respuesta
        return respuesta

    def resume_routine(self, usuario: Usuario, routine_id: int) -> RoutineResumeResponseDTO:
        """Retoma una rutina tras inactividad sin penalizar puntos ni nivel (HU-11, RF-16, RF-24)."""
        rutina = self.rutina_repo.get_by_id_and_user(routine_id, usuario.id)
        if not rutina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La rutina solicitada no existe.",
            )

        rutina = self.rutina_repo.update(rutina, completadahoy=False)
        primer_nombre = (usuario.nombre or "Usuario").split()[0]

        return RoutineResumeResponseDTO(
            mensaje_bienvenida=(
                f"¡Qué alegría verte de vuelta, {primer_nombre}! "
                "Tus puntos y nivel están intactos. Vamos un paso a la vez desde hoy."
            ),
            penalizacion_aplicada=False,
            puntos_conservados=int(usuario.puntos or 0),
            nivel_conservado=int(usuario.nivel or 1),
            rutina=RutinaMapper.to_dto(rutina),
        )


# =====================================================================
# 5. SERVICIO DE ENFOQUE POMODORO Y PAUSAS DE BAJO ESTÍMULO
# =====================================================================


class PomodoroService(IPomodoroService):
    """Gestiona sesiones de enfoque corto (5/25 min) y pausas suaves (HU-06, RF-10 a RF-12)."""

    PUNTOS_POR_SESION = 5

    def __init__(self, db: Session) -> None:
        self.db = db
        self.pomodoro_repo = SesionPomodoroRepository(db)
        self.tarea_repo = TareaRepository(db)
        self.user_repo = UsuarioRepository(db)
        self.recompensa_repo = RecompensaRepository(db)

    def create_session(self, usuario: Usuario, dto: PomodoroCreateRequestDTO) -> PomodoroResponseDTO:
        if dto.id_tarea is not None:
            tarea = self.tarea_repo.get_by_id_and_user(dto.id_tarea, usuario.id)
            if not tarea:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="La tarea asociada a la sesión Pomodoro no existe.",
                )

        sesion = self.pomodoro_repo.create(
            id_usuario=usuario.id,
            duracionconcentracion=dto.duracionconcentracion,
            duraciondescanso=dto.duraciondescanso,
            id_tarea=dto.id_tarea,
        )
        return PomodoroMapper.to_dto(sesion)

    def list_sessions(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> PomodoroListResponseDTO:
        items, total = self.pomodoro_repo.list_by_user(
            id_usuario=usuario.id,
            limit=limit,
            offset=offset,
        )
        return PomodoroListResponseDTO(
            total=total,
            limit=limit,
            offset=offset,
            items=[PomodoroMapper.to_dto(s) for s in items],
        )

    def complete_session(
        self,
        usuario: Usuario,
        session_id: int,
        idempotency_key: Optional[str] = None,
    ) -> PomodoroActionResponseDTO:
        sesion = self.pomodoro_repo.get_by_id_and_user(session_id, usuario.id)
        if not sesion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La sesión Pomodoro solicitada no existe.",
            )

        cache_key = f"pomodoro_complete:{usuario.id}:{session_id}:{idempotency_key}" if idempotency_key else None
        if cache_key and cache_key in _IDEMPOTENCY_CACHE:
            return PomodoroActionResponseDTO(
                mensaje="Este ciclo de enfoque ya fue contabilizado.",
                estado="completada",
                puntos_ganados=0,
                puntos_totales=int(usuario.puntos or 0),
                nivel_actual=int(usuario.nivel or 1),
                idempotente=True,
                sesion=PomodoroMapper.to_dto(sesion),
                sugerencia_descanso=f"Un break suave de {sesion.duraciondescanso} min: Respiración 4-4 o Estiramiento suave.",
            )

        sesion = self.pomodoro_repo.increment_completed(sesion)
        usuario = self.user_repo.add_points_and_update_level(usuario, self.PUNTOS_POR_SESION)
        self.recompensa_repo.auto_unlock_eligible(
            id_usuario=usuario.id,
            puntos_usuario=int(usuario.puntos or 0),
        )

        respuesta = PomodoroActionResponseDTO(
            mensaje=f"¡Ciclo de enfoque completado! +{self.PUNTOS_POR_SESION} dopamina.",
            estado="completada",
            puntos_ganados=self.PUNTOS_POR_SESION,
            puntos_totales=int(usuario.puntos or 0),
            nivel_actual=int(usuario.nivel or 1),
            idempotente=False,
            sesion=PomodoroMapper.to_dto(sesion),
            sugerencia_descanso=f"Un break suave de {sesion.duraciondescanso} min: Respiración 4-4 o Estiramiento suave.",
        )
        if cache_key:
            _IDEMPOTENCY_CACHE[cache_key] = respuesta
        return respuesta

    def cancel_session(self, usuario: Usuario, session_id: int) -> PomodoroActionResponseDTO:
        """Cancela la sesión en curso sin incrementar `sesionescompletadas` ni otorgar puntos (HU-06)."""
        sesion = self.pomodoro_repo.get_by_id_and_user(session_id, usuario.id)
        if not sesion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La sesión Pomodoro solicitada no existe.",
            )

        return PomodoroActionResponseDTO(
            mensaje="Sesión detenida sin problema. No se contabilizó el ciclo incompleto, toma aire y vuelve cuando quieras.",
            estado="cancelada",
            puntos_ganados=0,
            puntos_totales=int(usuario.puntos or 0),
            nivel_actual=int(usuario.nivel or 1),
            idempotente=False,
            sesion=PomodoroMapper.to_dto(sesion),
            sugerencia_descanso="Respira 4-4 antes de decidir tu siguiente paso.",
        )

    def get_low_stimulus_activities(self) -> LowStimulusCatalogResponseDTO:
        """Retorna las actividades de bajo estímulo de Figuras 4, 12 y 13 ('Un break suave')."""
        actividades = [
            LowStimulusActivityDTO(
                id="respiracion-4-4",
                titulo="Respiración 4-4",
                subtitulo="Inhala 4s, exhala 4s",
                duracion_sugerida_min=5,
                icono="wind",
                pasos=[
                    "Inhala suave por la nariz durante 4 segundos.",
                    "Exhala despacio por la boca durante 4 segundos.",
                    "Repite a tu ritmo sin forzar tu atención.",
                ],
            ),
            LowStimulusActivityDTO(
                id="estiramiento-suave",
                titulo="Estiramiento suave",
                subtitulo="Mueve hombros y cuello despacio",
                duracion_sugerida_min=5,
                icono="sparkles",
                pasos=[
                    "Suelta la mandíbula y baja los hombros.",
                    "Gira suavemente el cuello hacia un lado y luego al otro.",
                    "Estira los brazos hacia arriba y toma un sorbo de agua.",
                ],
            ),
            LowStimulusActivityDTO(
                id="cierra-con-gratitud",
                titulo="Cierra con gratitud",
                subtitulo="Reconoce tu pequeño avance de hoy",
                duracion_sugerida_min=10,
                icono="heart",
                pasos=[
                    "Cierra los ojos 30 segundos lejos de notificaciones.",
                    "Reconoce que empezar ya fue un logro importante.",
                ],
            ),
        ]
        return LowStimulusCatalogResponseDTO(
            encabezado="Un break suave",
            mensaje="Respira. No tienes que hacer nada ahora.",
            opciones_duracion_min=[5, 10],
            actividades=actividades,
        )


# =====================================================================
# 6. SERVICIO DE RECORDATORIOS
# =====================================================================


class ReminderService(IReminderService):
    """Gestiona recordatorios por fecha/hora y desactivación al completarse (HU-05, RF-08, RF-09)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.recordatorio_repo = RecordatorioRepository(db)
        self.tarea_repo = TareaRepository(db)

    def list_reminders(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
        tipo: Optional[TipoRecordatorioEnum] = None,
        completadahoy: Optional[bool] = None,
    ) -> ReminderListResponseDTO:
        items, total = self.recordatorio_repo.list_by_user(
            id_usuario=usuario.id,
            limit=limit,
            offset=offset,
            tipo=tipo,
            completadahoy=completadahoy,
        )
        return ReminderListResponseDTO(
            total=total,
            limit=limit,
            offset=offset,
            items=[RecordatorioMapper.to_dto(r) for r in items],
        )

    def create_reminder(self, usuario: Usuario, dto: ReminderCreateRequestDTO) -> ReminderResponseDTO:
        if dto.id_tarea is not None:
            tarea = self.tarea_repo.get_by_id_and_user(dto.id_tarea, usuario.id)
            if not tarea:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="La tarea asociada al recordatorio no existe.",
                )

        recordatorio = self.recordatorio_repo.create(
            id_usuario=usuario.id,
            fechahora=dto.fechahora,
            mensaje=dto.mensaje,
            tipo=dto.tipo,
            id_tarea=dto.id_tarea,
        )
        return RecordatorioMapper.to_dto(recordatorio)

    def update_reminder(
        self,
        usuario: Usuario,
        reminder_id: int,
        dto: ReminderUpdateRequestDTO,
    ) -> ReminderResponseDTO:
        recordatorio = self.recordatorio_repo.get_by_id_and_user(reminder_id, usuario.id)
        if not recordatorio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El recordatorio solicitado no existe.",
            )

        if dto.id_tarea is not None:
            tarea = self.tarea_repo.get_by_id_and_user(dto.id_tarea, usuario.id)
            if not tarea:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="La tarea asociada al recordatorio no existe.",
                )

        campos = dto.model_dump(exclude_unset=True)
        actualizado = self.recordatorio_repo.update(recordatorio, **campos)
        return RecordatorioMapper.to_dto(actualizado)

    def delete_reminder(self, usuario: Usuario, reminder_id: int) -> None:
        recordatorio = self.recordatorio_repo.get_by_id_and_user(reminder_id, usuario.id)
        if not recordatorio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El recordatorio solicitado no existe.",
            )
        self.recordatorio_repo.delete(recordatorio)


# =====================================================================
# 7. SERVICIO DE GAMIFICACIÓN Y RECOMPENSAS
# =====================================================================


class GamificationService(IGamificationService):
    """Gestiona la pantalla 'Mi Dopamina hoy', niveles y desbloqueo de recompensas (HU-07)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.recompensa_repo = RecompensaRepository(db)
        self.tarea_repo = TareaRepository(db)
        self.pomodoro_repo = SesionPomodoroRepository(db)
        self.panel_repo = PanelPrincipalRepository(db)

    def get_summary(self, usuario: Usuario) -> GamificationSummaryResponseDTO:
        puntos = int(usuario.puntos or 0)
        nivel = int(usuario.nivel or 1)
        prefs = get_user_preferences(usuario.id)
        meta_diaria = prefs.meta_diaria_dopamina

        porcentaje_meta = min(100.0, round((puntos / meta_diaria) * 100.0, 2)) if meta_diaria > 0 else 100.0
        puntos_en_nivel_actual = puntos % 50
        puntos_para_siguiente = 50 - puntos_en_nivel_actual
        progreso_nivel = round((puntos_en_nivel_actual / 50.0) * 100.0, 2)

        _, completadas_total, _ = self.tarea_repo.count_stats_by_user(usuario.id)
        sesiones, _ = self.pomodoro_repo.list_by_user(usuario.id, limit=200, offset=0)
        total_ciclos_pomodoro = sum(int(s.sesionescompletadas or 0) for s in sesiones)

        recompensas, _ = self.recompensa_repo.list_for_user(usuario.id, limit=50, offset=0)
        desbloqueadas = [r for r in recompensas if r.desbloqueada]
        paneles = self.panel_repo.list_by_user(usuario.id, limit=365, offset=0)

        return GamificationSummaryResponseDTO(
            encabezado="Mi Dopamina hoy",
            puntos_totales=puntos,
            nivel=nivel,
            meta_diaria_puntos=meta_diaria,
            porcentaje_meta_diaria=porcentaje_meta,
            puntos_para_siguiente_nivel=puntos_para_siguiente,
            progreso_nivel_porcentaje=progreso_nivel,
            tareas_completadas_total=completadas_total,
            sesiones_enfoque_completadas=total_ciclos_pomodoro,
            recompensas_desbloqueadas_count=len(desbloqueadas),
            dias_activos_registrados=max(1, len(paneles)),
            recompensas_recientes=[RecompensaMapper.to_dto(r) for r in recompensas[:6]],
        )

    def list_rewards(
        self,
        usuario: Usuario,
        limit: int = 50,
        offset: int = 0,
    ) -> RewardListResponseDTO:
        items, total = self.recompensa_repo.list_for_user(usuario.id, limit=limit, offset=offset)
        return RewardListResponseDTO(
            total=total,
            puntos_disponibles=int(usuario.puntos or 0),
            nivel_actual=int(usuario.nivel or 1),
            items=[RecompensaMapper.to_dto(r) for r in items],
        )

    def create_reward(self, usuario: Usuario, dto: RewardCreateRequestDTO) -> RewardResponseDTO:
        if dto.id_tarea is not None:
            tarea = self.tarea_repo.get_by_id_and_user(dto.id_tarea, usuario.id)
            if not tarea:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="La tarea asociada a la recompensa no existe.",
                )

        recompensa = self.recompensa_repo.create(
            nombre=dto.nombre,
            costopuntos=dto.costopuntos,
            id_tarea=dto.id_tarea,
            desbloqueada=False,
        )
        return RecompensaMapper.to_dto(recompensa)

    def unlock_reward(self, usuario: Usuario, reward_id: int) -> RewardResponseDTO:
        recompensa = self.recompensa_repo.get_by_id_for_user(reward_id, usuario.id)
        if not recompensa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La recompensa solicitada no existe.",
            )

        if recompensa.desbloqueada:
            return RecompensaMapper.to_dto(recompensa)

        puntos_usuario = int(usuario.puntos or 0)
        costo = int(recompensa.costopuntos or 0)

        # Verificar condición por tarea completada o por puntos acumulados (RF-15)
        cumple_tarea = False
        if recompensa.id_tarea is not None:
            tarea = self.tarea_repo.get_by_id_and_user(recompensa.id_tarea, usuario.id)
            cumple_tarea = bool(tarea and tarea.completada)

        if not cumple_tarea and puntos_usuario < costo:
            faltantes = costo - puntos_usuario
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Aún te faltan {faltantes} puntos de dopamina para desbloquear '{recompensa.nombre}'. "
                    "¡Vamos paso a paso!"
                ),
            )

        desbloqueada = self.recompensa_repo.unlock(recompensa)
        return RecompensaMapper.to_dto(desbloqueada)


# =====================================================================
# 8. SERVICIO DE SEGUIMIENTO PERSONAL (SUEÑO, HUMOR Y BIENESTAR)
# =====================================================================


class PersonalRecordService(IPersonalRecordService):
    """Gestiona registros personales con cálculo automático de progreso y sin diagnósticos médicos (HU-08)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registro_repo = RegistroPersonalRepository(db)

    def list_records(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> PersonalRecordListResponseDTO:
        items, total = self.registro_repo.list_by_user(
            id_usuario=usuario.id,
            limit=limit,
            offset=offset,
        )
        if items:
            promedio = round(
                sum(float(r.progresoporcentaje or 0.0) for r in items) / len(items),
                1,
            )
            tendencia = (
                f"Promedio general de bienestar registrado: {promedio}%. "
                "Tus registros muestran constancia a tu propio ritmo."
            )
        else:
            tendencia = "Aún no tienes registros personales. Registra hoy tu sueño o energía cuando te sientas listo."

        return PersonalRecordListResponseDTO(
            total=total,
            limit=limit,
            offset=offset,
            tendencia_descriptiva=tendencia,
            items=[RegistroPersonalMapper.to_dto(r) for r in items],
        )

    def create_record(
        self,
        usuario: Usuario,
        dto: PersonalRecordCreateRequestDTO,
    ) -> PersonalRecordResponseDTO:
        objetivo = Decimal(str(dto.valorobjetivo))
        actual = Decimal(str(dto.valoractual))
        progreso = calculate_progress_percentage(actual, objetivo)

        registro = self.registro_repo.create(
            id_usuario=usuario.id,
            nombre=dto.nombre,
            valorobjetivo=objetivo,
            valoractual=actual,
            progresoporcentaje=progreso,
        )
        return RegistroPersonalMapper.to_dto(registro)

    def update_record(
        self,
        usuario: Usuario,
        record_id: int,
        dto: PersonalRecordUpdateRequestDTO,
    ) -> PersonalRecordResponseDTO:
        registro = self.registro_repo.get_by_id_and_user(record_id, usuario.id)
        if not registro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El registro personal solicitado no existe.",
            )

        nuevo_nombre = dto.nombre if dto.nombre is not None else registro.nombre
        nuevo_objetivo = (
            Decimal(str(dto.valorobjetivo))
            if dto.valorobjetivo is not None
            else Decimal(str(registro.valorobjetivo))
        )
        nuevo_actual = (
            Decimal(str(dto.valoractual))
            if dto.valoractual is not None
            else Decimal(str(registro.valoractual))
        )
        nuevo_progreso = calculate_progress_percentage(nuevo_actual, nuevo_objetivo)

        actualizado = self.registro_repo.update(
            registro,
            nombre=nuevo_nombre,
            valorobjetivo=nuevo_objetivo,
            valoractual=nuevo_actual,
            progresoporcentaje=nuevo_progreso,
        )
        return RegistroPersonalMapper.to_dto(actualizado)

    def delete_record(self, usuario: Usuario, record_id: int) -> None:
        registro = self.registro_repo.get_by_id_and_user(record_id, usuario.id)
        if not registro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El registro personal solicitado no existe.",
            )
        self.registro_repo.delete(registro)


# =====================================================================
# 9. SERVICIO DE METAS FINANCIERAS
# =====================================================================


class FinancialGoalService(IFinancialGoalService):
    """Gestiona metas financieras básicas con cálculo automático de porcentaje (HU-09, RF-20, RF-21)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.meta_repo = MetaFinancieraRepository(db)

    def list_goals(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> FinancialGoalListResponseDTO:
        items, total = self.meta_repo.list_by_user(
            id_usuario=usuario.id,
            limit=limit,
            offset=offset,
        )
        return FinancialGoalListResponseDTO(
            total=total,
            limit=limit,
            offset=offset,
            items=[MetaFinancieraMapper.to_dto(m) for m in items],
        )

    def create_goal(
        self,
        usuario: Usuario,
        dto: FinancialGoalCreateRequestDTO,
    ) -> FinancialGoalResponseDTO:
        objetivo = Decimal(str(dto.valorobjetivo))
        actual = Decimal(str(dto.valoractual))
        progreso = calculate_progress_percentage(actual, objetivo)

        meta = self.meta_repo.create(
            id_usuario=usuario.id,
            nombre=dto.nombre,
            valorobjetivo=objetivo,
            valoractual=actual,
            progresoporcentaje=progreso,
        )
        return MetaFinancieraMapper.to_dto(meta)

    def update_progress(
        self,
        usuario: Usuario,
        goal_id: int,
        dto: FinancialGoalProgressRequestDTO,
    ) -> FinancialGoalResponseDTO:
        meta = self.meta_repo.get_by_id_and_user(goal_id, usuario.id)
        if not meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La meta financiera solicitada no existe.",
            )

        objetivo = Decimal(str(meta.valorobjetivo))
        actual_previo = Decimal(str(meta.valoractual or 0))

        if dto.valoractual is not None:
            nuevo_actual = Decimal(str(dto.valoractual))
        else:
            avance = Decimal(str(dto.monto_avance or 0))
            nuevo_actual = actual_previo + avance

        nuevo_progreso = calculate_progress_percentage(nuevo_actual, objetivo)
        actualizada = self.meta_repo.update(
            meta,
            valoractual=nuevo_actual,
            progresoporcentaje=nuevo_progreso,
        )
        return MetaFinancieraMapper.to_dto(actualizada)

    def delete_goal(self, usuario: Usuario, goal_id: int) -> None:
        meta = self.meta_repo.get_by_id_and_user(goal_id, usuario.id)
        if not meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La meta financiera solicitada no existe.",
            )
        self.meta_repo.delete(meta)
