"""Contratos e Interfaces de la Capa de Lógica de Negocio — Proyecto DOPA.

Agente Responsable: 3.2. Agente de API y Lógica de Negocio (Backend Core Agent)
Referencia Arquitectónica: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf — Sección 4.2.3:
"Interfaces (Contratos): Definen la firma de los casos de uso, aplicando el principio
de Inversión de Dependencias para facilitar las pruebas unitarias."
"""

from abc import ABC, abstractmethod
from typing import Optional

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


class IAuthService(ABC):
    """Contrato para autenticación, sesiones JWT y preferencias de usuario (HU-01, HU-12)."""

    @abstractmethod
    def register(self, dto: RegisterRequestDTO) -> AuthTokensResponseDTO:
        ...

    @abstractmethod
    def login(self, dto: LoginRequestDTO) -> AuthTokensResponseDTO:
        ...

    @abstractmethod
    def refresh(self, dto: RefreshTokenRequestDTO) -> AuthTokensResponseDTO:
        ...

    @abstractmethod
    def logout(self, token: str) -> LogoutResponseDTO:
        ...

    @abstractmethod
    def get_profile(self, usuario: Usuario) -> UserResponseDTO:
        ...

    @abstractmethod
    def update_preferences(self, usuario: Usuario, dto: UserPreferencesDTO) -> UserResponseDTO:
        ...


class IDashboardService(ABC):
    """Contrato para el Panel Principal, chequeo de energía y tarea rápida (HU-10)."""

    @abstractmethod
    def get_dashboard(self, usuario: Usuario) -> DashboardResponseDTO:
        ...

    @abstractmethod
    def register_energy_checkin(
        self,
        usuario: Usuario,
        dto: EnergyCheckinRequestDTO,
    ) -> EnergyCheckinResponseDTO:
        ...

    @abstractmethod
    def get_quick_task(self, usuario: Usuario) -> TaskResponseDTO:
        ...


class ITaskService(ABC):
    """Contrato para gestión de tareas, micro-pasos y completado idempotente (HU-02, HU-03)."""

    @abstractmethod
    def list_tasks(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
        completada: Optional[bool] = None,
        prioridad: Optional[PrioridadTareaEnum] = None,
        id_rutina: Optional[int] = None,
    ) -> TaskListResponseDTO:
        ...

    @abstractmethod
    def create_task(self, usuario: Usuario, dto: TaskCreateRequestDTO) -> TaskResponseDTO:
        ...

    @abstractmethod
    def get_task(self, usuario: Usuario, task_id: int) -> TaskResponseDTO:
        ...

    @abstractmethod
    def update_task(self, usuario: Usuario, task_id: int, dto: TaskUpdateRequestDTO) -> TaskResponseDTO:
        ...

    @abstractmethod
    def delete_task(self, usuario: Usuario, task_id: int) -> None:
        ...

    @abstractmethod
    def complete_task(
        self,
        usuario: Usuario,
        task_id: int,
        idempotency_key: Optional[str] = None,
    ) -> TaskCompleteResponseDTO:
        ...

    @abstractmethod
    def create_subtask(
        self,
        usuario: Usuario,
        task_id: int,
        dto: SubtaskCreateRequestDTO,
    ) -> SubtaskResponseDTO:
        ...

    @abstractmethod
    def list_subtasks(self, usuario: Usuario, task_id: int) -> SubtaskListResponseDTO:
        ...

    @abstractmethod
    def update_subtask(
        self,
        usuario: Usuario,
        task_id: int,
        subtask_id: int,
        dto: SubtaskUpdateRequestDTO,
    ) -> SubtaskResponseDTO:
        ...

    @abstractmethod
    def delete_subtask(self, usuario: Usuario, task_id: int, subtask_id: int) -> None:
        ...


class IRoutineService(ABC):
    """Contrato para rutinas recurrentes libres de culpa (HU-04, HU-11)."""

    @abstractmethod
    def list_routines(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> RoutineListResponseDTO:
        ...

    @abstractmethod
    def create_routine(self, usuario: Usuario, dto: RoutineCreateRequestDTO) -> RoutineResponseDTO:
        ...

    @abstractmethod
    def get_routine(self, usuario: Usuario, routine_id: int) -> RoutineDetailResponseDTO:
        ...

    @abstractmethod
    def update_routine(
        self,
        usuario: Usuario,
        routine_id: int,
        dto: RoutineUpdateRequestDTO,
    ) -> RoutineResponseDTO:
        ...

    @abstractmethod
    def delete_routine(self, usuario: Usuario, routine_id: int) -> None:
        ...

    @abstractmethod
    def complete_today(
        self,
        usuario: Usuario,
        routine_id: int,
        idempotency_key: Optional[str] = None,
    ) -> RoutineCompleteResponseDTO:
        ...

    @abstractmethod
    def resume_routine(self, usuario: Usuario, routine_id: int) -> RoutineResumeResponseDTO:
        ...


class IPomodoroService(ABC):
    """Contrato para sesiones Pomodoro y catálogo de actividades de bajo estímulo (HU-06)."""

    @abstractmethod
    def create_session(self, usuario: Usuario, dto: PomodoroCreateRequestDTO) -> PomodoroResponseDTO:
        ...

    @abstractmethod
    def list_sessions(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> PomodoroListResponseDTO:
        ...

    @abstractmethod
    def complete_session(
        self,
        usuario: Usuario,
        session_id: int,
        idempotency_key: Optional[str] = None,
    ) -> PomodoroActionResponseDTO:
        ...

    @abstractmethod
    def cancel_session(self, usuario: Usuario, session_id: int) -> PomodoroActionResponseDTO:
        ...

    @abstractmethod
    def get_low_stimulus_activities(self) -> LowStimulusCatalogResponseDTO:
        ...


class IReminderService(ABC):
    """Contrato para recordatorios programados (HU-05)."""

    @abstractmethod
    def list_reminders(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
        tipo: Optional[TipoRecordatorioEnum] = None,
        completadahoy: Optional[bool] = None,
    ) -> ReminderListResponseDTO:
        ...

    @abstractmethod
    def create_reminder(self, usuario: Usuario, dto: ReminderCreateRequestDTO) -> ReminderResponseDTO:
        ...

    @abstractmethod
    def update_reminder(
        self,
        usuario: Usuario,
        reminder_id: int,
        dto: ReminderUpdateRequestDTO,
    ) -> ReminderResponseDTO:
        ...

    @abstractmethod
    def delete_reminder(self, usuario: Usuario, reminder_id: int) -> None:
        ...


class IGamificationService(ABC):
    """Contrato para el motor de gamificación libre de culpa y recompensas (HU-07, HU-11)."""

    @abstractmethod
    def get_summary(self, usuario: Usuario) -> GamificationSummaryResponseDTO:
        ...

    @abstractmethod
    def list_rewards(
        self,
        usuario: Usuario,
        limit: int = 50,
        offset: int = 0,
    ) -> RewardListResponseDTO:
        ...

    @abstractmethod
    def create_reward(self, usuario: Usuario, dto: RewardCreateRequestDTO) -> RewardResponseDTO:
        ...

    @abstractmethod
    def unlock_reward(self, usuario: Usuario, reward_id: int) -> RewardResponseDTO:
        ...


class IPersonalRecordService(ABC):
    """Contrato para seguimiento personal de sueño, humor y energía (HU-08)."""

    @abstractmethod
    def list_records(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> PersonalRecordListResponseDTO:
        ...

    @abstractmethod
    def create_record(
        self,
        usuario: Usuario,
        dto: PersonalRecordCreateRequestDTO,
    ) -> PersonalRecordResponseDTO:
        ...

    @abstractmethod
    def update_record(
        self,
        usuario: Usuario,
        record_id: int,
        dto: PersonalRecordUpdateRequestDTO,
    ) -> PersonalRecordResponseDTO:
        ...

    @abstractmethod
    def delete_record(self, usuario: Usuario, record_id: int) -> None:
        ...


class IFinancialGoalService(ABC):
    """Contrato para metas financieras con cálculo automático de progreso (HU-09)."""

    @abstractmethod
    def list_goals(
        self,
        usuario: Usuario,
        limit: int = 20,
        offset: int = 0,
    ) -> FinancialGoalListResponseDTO:
        ...

    @abstractmethod
    def create_goal(
        self,
        usuario: Usuario,
        dto: FinancialGoalCreateRequestDTO,
    ) -> FinancialGoalResponseDTO:
        ...

    @abstractmethod
    def update_progress(
        self,
        usuario: Usuario,
        goal_id: int,
        dto: FinancialGoalProgressRequestDTO,
    ) -> FinancialGoalResponseDTO:
        ...

    @abstractmethod
    def delete_goal(self, usuario: Usuario, goal_id: int) -> None:
        ...
