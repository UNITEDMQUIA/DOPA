"""Objetos de Transferencia de Datos (RequestDTO / ResponseDTO) — Proyecto DOPA.

Agente Responsable: 3.2. Agente de API y Lógica de Negocio (Backend Core Agent)
Referencia Arquitectónica: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf — Sección 4.2.2.
Optimiza los payloads JSON hacia la aplicación móvil y valida las entradas según HU-01 a HU-12.
"""

from datetime import date, datetime, time
import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.models import PrioridadTareaEnum, TipoRecordatorioEnum

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


# =====================================================================
# 1. AUTENTICACIÓN Y PREFERENCIAS (/api/v1/auth)
# =====================================================================


class UserPreferencesDTO(BaseModel):
    """Preferencias configurables del usuario (HU-12, RF-23)."""

    duracion_concentracion_min: int = Field(default=5, gt=0, le=180)
    duracion_descanso_min: int = Field(default=5, ge=1, le=60)
    notificaciones_activas: bool = Field(default=True)
    sonidos_suaves: bool = Field(default=True)
    modo_bajo_estimulo: bool = Field(default=True)
    meta_diaria_dopamina: int = Field(default=50, gt=0, le=500)
    tema_visual: str = Field(default="Lavanda Suave", min_length=2, max_length=60)


class RegisterRequestDTO(BaseModel):
    """DTO de entrada para registro de nuevo usuario (HU-01, RF-01)."""

    nombre: str = Field(..., min_length=2, max_length=120)
    correo: str = Field(..., min_length=5, max_length=150)
    contrasena: str = Field(..., min_length=8, max_length=128)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El nombre no puede estar vacío.")
        return limpio

    @field_validator("correo")
    @classmethod
    def validate_correo(cls, value: str) -> str:
        limpio = value.strip().lower()
        if not EMAIL_REGEX.match(limpio):
            raise ValueError("El formato del correo electrónico no es válido.")
        return limpio


class LoginRequestDTO(BaseModel):
    """DTO de entrada para inicio de sesión (HU-01, RF-02)."""

    correo: str = Field(..., min_length=5, max_length=150)
    contrasena: str = Field(..., min_length=1, max_length=128)

    @field_validator("correo")
    @classmethod
    def validate_correo(cls, value: str) -> str:
        limpio = value.strip().lower()
        if not EMAIL_REGEX.match(limpio):
            raise ValueError("El formato del correo electrónico no es válido.")
        return limpio


class RefreshTokenRequestDTO(BaseModel):
    """DTO para renovación de Access Token mediante Refresh Token."""

    refresh_token: str = Field(..., min_length=10)


class UserResponseDTO(BaseModel):
    """DTO de salida seguro del perfil de usuario (sin exponer contrasenahash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
    puntos: int
    nivel: int
    preferencias: UserPreferencesDTO = Field(default_factory=UserPreferencesDTO)


class AuthTokensResponseDTO(BaseModel):
    """Respuesta de autenticación con JWT Stateless (Access + Refresh Token)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    usuario: UserResponseDTO


class LogoutResponseDTO(BaseModel):
    """Confirmación de cierre de sesión (HU-01)."""

    mensaje: str
    sesion_cerrada: bool = True


# =====================================================================
# 2. TAREAS Y MICRO-PASOS (/api/v1/tasks)
# =====================================================================


class SubtaskCreateRequestDTO(BaseModel):
    """Creación de un micro-paso dentro de una tarea (HU-03, RF-05)."""

    descripcion: str = Field(..., min_length=1, max_length=255)

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("La descripción del micro-paso no puede estar vacía.")
        return limpio


class SubtaskUpdateRequestDTO(BaseModel):
    """Actualización de estado o texto de un micro-paso (Figura 9)."""

    descripcion: Optional[str] = Field(default=None, min_length=1, max_length=255)
    completada: Optional[bool] = None

    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            limpio = value.strip()
            if not limpio:
                raise ValueError("La descripción del micro-paso no puede estar vacía.")
            return limpio
        return value


class SubtaskResponseDTO(BaseModel):
    """Representación de un micro-paso (`subtarea`)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_tarea: int
    descripcion: str
    completada: bool


class SubtaskListResponseDTO(BaseModel):
    """Listado de micro-pasos con progreso de avance (Figura 9)."""

    id_tarea: int
    total_pasos: int
    pasos_completados: int
    progreso_pasos_porcentaje: float
    items: list[SubtaskResponseDTO]


class TaskCreateRequestDTO(BaseModel):
    """Creación de tarea principal con soporte de micro-pasos iniciales (HU-02, HU-03)."""

    titulo: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(default=None, max_length=2000)
    prioridad: PrioridadTareaEnum = Field(default=PrioridadTareaEnum.Media)
    fechavencimiento: Optional[date] = None
    id_rutina: Optional[int] = Field(default=None, gt=0)
    subtareas: list[str] = Field(default_factory=list)

    @field_validator("titulo")
    @classmethod
    def validate_titulo(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El título de la tarea es obligatorio y no puede estar en blanco.")
        return limpio


class TaskUpdateRequestDTO(BaseModel):
    """Edición de una tarea existente (RF-04)."""

    titulo: Optional[str] = Field(default=None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(default=None, max_length=2000)
    prioridad: Optional[PrioridadTareaEnum] = None
    fechavencimiento: Optional[date] = None
    id_rutina: Optional[int] = Field(default=None, gt=0)
    completada: Optional[bool] = None

    @field_validator("titulo")
    @classmethod
    def validate_titulo(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            limpio = value.strip()
            if not limpio:
                raise ValueError("El título de la tarea no puede estar en blanco.")
            return limpio
        return value


class TaskResponseDTO(BaseModel):
    """DTO de tarea optimizado para las pantallas 'Mis tareas: Poquito a poquito' y 'Enfoque suave'."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_usuario: int
    id_rutina: Optional[int] = None
    titulo: str
    descripcion: Optional[str] = None
    prioridad: PrioridadTareaEnum
    etiqueta_esfuerzo: str
    fechavencimiento: Optional[date] = None
    completada: bool
    puntos_recompensa: int = 10
    total_subtareas: int = 0
    subtareas_completadas: int = 0
    progreso_subtareas: str = "0/0 pasos"
    subtareas: list[SubtaskResponseDTO] = Field(default_factory=list)


class TaskListResponseDTO(BaseModel):
    """Listado paginado de tareas con resumen amigable (Figura 8)."""

    encabezado: str = "Poquito a poquito"
    total: int
    pendientes: int
    completadas: int
    resumen_progreso: str
    limit: int
    offset: int
    items: list[TaskResponseDTO]


class RewardResponseDTO(BaseModel):
    """DTO de salida para una recompensa de dopamina (HU-07)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_tarea: Optional[int] = None
    nombre: str
    costopuntos: int
    desbloqueada: bool


class TaskCompleteResponseDTO(BaseModel):
    """Respuesta al completar una tarea (Figura 10: '¡Lo hiciste! +10 dopamina')."""

    mensaje_celebracion: str
    subtitulo_celebracion: str = "Cada pequeño paso cuenta. Tu cerebro merece celebrar."
    puntos_ganados: int
    puntos_totales: int
    nivel_actual: int
    idempotente: bool = False
    tarea: TaskResponseDTO
    recompensas_desbloqueadas: list[RewardResponseDTO] = Field(default_factory=list)


# =====================================================================
# 3. RUTINAS LIBRES DE CULPA (/api/v1/routines)
# =====================================================================


class RoutineCreateRequestDTO(BaseModel):
    """DTO de entrada para crear una rutina (HU-04, RF-06)."""

    nombre: str = Field(..., min_length=1, max_length=150)
    recurrencia: str = Field(..., min_length=1, max_length=100)
    hora: time = Field(default=time(8, 0))

    @field_validator("nombre", "recurrencia")
    @classmethod
    def validate_no_vacio(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El campo no puede estar en blanco.")
        return limpio


class RoutineUpdateRequestDTO(BaseModel):
    """DTO para actualizar una rutina existente."""

    nombre: Optional[str] = Field(default=None, min_length=1, max_length=150)
    recurrencia: Optional[str] = Field(default=None, min_length=1, max_length=100)
    hora: Optional[time] = None
    completadahoy: Optional[bool] = None

    @field_validator("nombre", "recurrencia")
    @classmethod
    def validate_no_vacio(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            limpio = value.strip()
            if not limpio:
                raise ValueError("El campo no puede estar en blanco.")
            return limpio
        return value


class RoutineResponseDTO(BaseModel):
    """DTO de salida de una rutina con mensaje libre de culpa."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_usuario: int
    nombre: str
    recurrencia: str
    hora: time
    completadahoy: bool
    total_tareas_asociadas: int = 0
    mensaje_libre_de_culpa: str = "A tu propio ritmo, sin castigos si hoy necesitas descansar."


class RoutineDetailResponseDTO(RoutineResponseDTO):
    """Detalle de rutina incluyendo sus tareas asociadas."""

    tareas: list[TaskResponseDTO] = Field(default_factory=list)


class RoutineListResponseDTO(BaseModel):
    """Listado paginado de rutinas del usuario."""

    total: int
    limit: int
    offset: int
    items: list[RoutineResponseDTO]


class RoutineCompleteResponseDTO(BaseModel):
    """Respuesta idempotente al completar una rutina hoy."""

    mensaje: str
    puntos_ganados: int
    puntos_totales: int
    nivel_actual: int
    idempotente: bool = False
    rutina: RoutineResponseDTO


class RoutineResumeResponseDTO(BaseModel):
    """Respuesta libre de culpa al retomar una rutina tras inactividad (HU-11, RF-16, RF-24)."""

    mensaje_bienvenida: str
    penalizacion_aplicada: bool = False
    puntos_conservados: int
    nivel_conservado: int
    rutina: RoutineResponseDTO


# =====================================================================
# 4. ENFOQUE POMODORO Y PAUSAS DE BAJO ESTÍMULO (/api/v1/pomodoro)
# =====================================================================


class PomodoroCreateRequestDTO(BaseModel):
    """Configuración e inicio de sesión de enfoque (HU-06, RF-10)."""

    id_tarea: Optional[int] = Field(default=None, gt=0)
    duracionconcentracion: int = Field(default=5, gt=0, le=180)
    duraciondescanso: int = Field(default=5, ge=0, le=60)


class PomodoroResponseDTO(BaseModel):
    """Representación de una sesión de enfoque (`sesionpomodoro`)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_usuario: int
    id_tarea: Optional[int] = None
    duracionconcentracion: int
    duraciondescanso: int
    sesionescompletadas: int
    modo_etiqueta: str = "Enfoque suave"


class PomodoroListResponseDTO(BaseModel):
    """Listado paginado de sesiones Pomodoro del usuario."""

    total: int
    limit: int
    offset: int
    items: list[PomodoroResponseDTO]


class PomodoroActionResponseDTO(BaseModel):
    """Respuesta al completar o cancelar un ciclo de enfoque (RF-11, RF-12)."""

    mensaje: str
    estado: str
    puntos_ganados: int
    puntos_totales: int
    nivel_actual: int
    idempotente: bool = False
    sesion: PomodoroResponseDTO
    sugerencia_descanso: str


class LowStimulusActivityDTO(BaseModel):
    """Actividad guiada de bajo estímulo para el descanso (Figuras 4, 12 y 13)."""

    id: str
    titulo: str
    subtitulo: str
    duracion_sugerida_min: int
    icono: str
    pasos: list[str]


class LowStimulusCatalogResponseDTO(BaseModel):
    """Catálogo para la pantalla 'Un break suave' (Figuras 12 y 13)."""

    encabezado: str = "Un break suave"
    mensaje: str = "Respira. No tienes que hacer nada ahora."
    opciones_duracion_min: list[int] = Field(default_factory=lambda: [5, 10])
    actividades: list[LowStimulusActivityDTO]


# =====================================================================
# 5. RECORDATORIOS (/api/v1/reminders)
# =====================================================================


class ReminderCreateRequestDTO(BaseModel):
    """Creación de un recordatorio programado (HU-05, RF-08)."""

    fechahora: datetime
    mensaje: str = Field(..., min_length=1, max_length=255)
    tipo: TipoRecordatorioEnum = Field(default=TipoRecordatorioEnum.Tarea)
    id_tarea: Optional[int] = Field(default=None, gt=0)

    @field_validator("mensaje")
    @classmethod
    def validate_mensaje(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El mensaje del recordatorio no puede estar vacío.")
        return limpio


class ReminderUpdateRequestDTO(BaseModel):
    """Actualización o desactivación de un recordatorio (HU-05)."""

    fechahora: Optional[datetime] = None
    mensaje: Optional[str] = Field(default=None, min_length=1, max_length=255)
    tipo: Optional[TipoRecordatorioEnum] = None
    id_tarea: Optional[int] = Field(default=None, gt=0)
    completadahoy: Optional[bool] = None

    @field_validator("mensaje")
    @classmethod
    def validate_mensaje(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            limpio = value.strip()
            if not limpio:
                raise ValueError("El mensaje del recordatorio no puede estar vacío.")
            return limpio
        return value


class ReminderResponseDTO(BaseModel):
    """Representación de un recordatorio con indicador de alerta activa."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_usuario: int
    id_tarea: Optional[int] = None
    fechahora: datetime
    mensaje: str
    tipo: TipoRecordatorioEnum
    completadahoy: bool
    notificacion_activa: bool


class ReminderListResponseDTO(BaseModel):
    """Listado paginado de recordatorios del usuario."""

    total: int
    limit: int
    offset: int
    items: list[ReminderResponseDTO]


# =====================================================================
# 6. GAMIFICACIÓN Y DOPAMINA (/api/v1/gamification)
# =====================================================================


class RewardCreateRequestDTO(BaseModel):
    """Creación de una recompensa de dopamina (HU-07, RF-15)."""

    nombre: str = Field(..., min_length=1, max_length=150)
    costopuntos: int = Field(default=10, ge=0, le=10000)
    id_tarea: Optional[int] = Field(default=None, gt=0)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El nombre de la recompensa no puede estar vacío.")
        return limpio


class RewardListResponseDTO(BaseModel):
    """Listado de recompensas y saldo actual del usuario."""

    total: int
    puntos_disponibles: int
    nivel_actual: int
    items: list[RewardResponseDTO]


class GamificationSummaryResponseDTO(BaseModel):
    """Payload consolidado para la pantalla 'Mi Dopamina hoy' (Figuras 6 y 11)."""

    encabezado: str = "Mi Dopamina hoy"
    puntos_totales: int
    nivel: int
    meta_diaria_puntos: int
    porcentaje_meta_diaria: float
    puntos_para_siguiente_nivel: int
    progreso_nivel_porcentaje: float
    tareas_completadas_total: int
    sesiones_enfoque_completadas: int
    recompensas_desbloqueadas_count: int
    dias_activos_registrados: int
    opciones_humor: list[str] = Field(
        default_factory=lambda: ["Abrumado", "Inquieto", "Con foco", "Tranquilo"]
    )
    mensaje_libre_de_culpa: str = (
        "Tu progreso nunca se pierde. Si un día descansas, tus puntos y nivel te esperan intactos."
    )
    recompensas_recientes: list[RewardResponseDTO] = Field(default_factory=list)


# =====================================================================
# 7. SEGUIMIENTO PERSONAL: SUEÑO, HUMOR Y ENERGÍA (/api/v1/personal-records)
# =====================================================================


class PersonalRecordCreateRequestDTO(BaseModel):
    """Creación de registro personal de sueño, humor o bienestar (HU-08, RF-17)."""

    nombre: str = Field(..., min_length=1, max_length=120)
    valorobjetivo: float = Field(..., gt=0)
    valoractual: float = Field(..., ge=0)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El nombre del indicador personal no puede estar vacío.")
        return limpio


class PersonalRecordUpdateRequestDTO(BaseModel):
    """Actualización de valores de un registro personal (RF-18, RF-19)."""

    nombre: Optional[str] = Field(default=None, min_length=1, max_length=120)
    valorobjetivo: Optional[float] = Field(default=None, gt=0)
    valoractual: Optional[float] = Field(default=None, ge=0)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            limpio = value.strip()
            if not limpio:
                raise ValueError("El nombre del indicador personal no puede estar vacío.")
            return limpio
        return value


class PersonalRecordResponseDTO(BaseModel):
    """DTO de salida para un registro personal con porcentaje autocalculado."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_usuario: int
    nombre: str
    valorobjetivo: float
    valoractual: float
    progresoporcentaje: float
    unidad_sugerida: str = "unidades"


class PersonalRecordListResponseDTO(BaseModel):
    """Listado de registros personales con tendencia descriptiva no médica (HU-08)."""

    total: int
    limit: int
    offset: int
    tendencia_descriptiva: str
    aviso_no_medico: str = (
        "Este seguimiento muestra únicamente tendencias descriptivas de bienestar diario y no constituye un diagnóstico médico ni psicológico."
    )
    items: list[PersonalRecordResponseDTO]


# =====================================================================
# 8. METAS FINANCIERAS (/api/v1/financial-goals)
# =====================================================================


class FinancialGoalCreateRequestDTO(BaseModel):
    """Creación de una meta financiera básica (HU-09, RF-20)."""

    nombre: str = Field(..., min_length=1, max_length=150)
    valorobjetivo: float = Field(..., gt=0)
    valoractual: float = Field(default=0.0, ge=0)

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        limpio = value.strip()
        if not limpio:
            raise ValueError("El nombre de la meta financiera no puede estar vacío.")
        return limpio


class FinancialGoalProgressRequestDTO(BaseModel):
    """Actualización de progreso de una meta financiera (RF-21)."""

    monto_avance: Optional[float] = None
    valoractual: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_al_menos_un_valor(self) -> "FinancialGoalProgressRequestDTO":
        if self.monto_avance is None and self.valoractual is None:
            raise ValueError("Debe proporcionar `monto_avance` o el nuevo `valoractual`.")
        if self.monto_avance is not None and self.monto_avance <= 0:
            raise ValueError("El monto de avance debe ser un valor numérico positivo.")
        return self


class FinancialGoalResponseDTO(BaseModel):
    """DTO de salida para una meta financiera con cálculo automático de porcentaje."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    id_usuario: int
    nombre: str
    valorobjetivo: float
    valoractual: float
    progresoporcentaje: float
    meta_alcanzada: bool
    aviso_alcance: str = (
        "Registro informativo de ahorro personal. No realiza conexiones bancarias ni representa asesoría financiera profesional."
    )


class FinancialGoalListResponseDTO(BaseModel):
    """Listado paginado de metas financieras del usuario."""

    total: int
    limit: int
    offset: int
    aviso_alcance: str = (
        "Registro informativo de ahorro personal. No realiza conexiones bancarias ni representa asesoría financiera profesional."
    )
    items: list[FinancialGoalResponseDTO]


# =====================================================================
# 9. PANEL PRINCIPAL / DASHBOARD (/api/v1/dashboard)
# =====================================================================


class EnergyCheckinRequestDTO(BaseModel):
    """Chequeo diario '¿Cómo está tu energía hoy?' (Figuras 2, 7 y 11)."""

    nivel_energia: str = Field(..., description="Ej. 'poquita', 'media', 'a tope'")
    humor: Optional[str] = Field(
        default=None,
        description="Ej. 'Abrumado', 'Inquieto', 'Con foco', 'Tranquilo'",
    )
    horas_sueno: Optional[float] = Field(default=None, ge=0, le=24)

    @field_validator("nivel_energia")
    @classmethod
    def validate_nivel_energia(cls, value: str) -> str:
        limpio = value.strip().lower()
        permitidos = {"poquita", "media", "a tope", "baja", "alta"}
        if limpio not in permitidos:
            raise ValueError("El nivel de energía debe ser 'poquita', 'media' o 'a tope'.")
        if limpio == "baja":
            return "poquita"
        if limpio == "alta":
            return "a tope"
        return limpio


class EnergyCheckinResponseDTO(BaseModel):
    """Respuesta al registrar el chequeo diario de energía/humor."""

    mensaje: str
    nivel_energia: str
    humor: Optional[str] = None
    puntos_dopamina: int
    sugerencia_baja_friccion: str
    registro_id: int


class DashboardResponseDTO(BaseModel):
    """Payload consolidado para la pantalla principal de Inicio (Figuras 2 y 7)."""

    panel_id: int
    fecha_actual: date
    saludo: str
    subtitulo_amigable: str = "Vamos un paso a la vez"
    puntos_dopamina: int
    meta_diaria_puntos: int = 50
    nivel: int
    estado_energia_hoy: str
    humor_hoy: Optional[str] = None
    resumen_tareas: dict
    micro_tareas_hoy: list[TaskResponseDTO]
    rutinas_hoy: list[RoutineResponseDTO]
    recordatorios_proximos: list[ReminderResponseDTO]
    accion_rapida_etiqueta: str = "¡Hacer algo fácil!"
