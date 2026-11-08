"""Mappers entre Entidades de Dominio y DTOs — Proyecto DOPA.

Agente Responsable: 3.2. Agente de API y Lógica de Negocio (Backend Core Agent)
Referencia Arquitectónica: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf — Sección 4.2.2.
Realiza la conversión bidireccional entre `Entities` (SQLAlchemy) y `DTOs` (Pydantic),
garantizando que nunca se expongan entidades crudas ni `contrasenahash` hacia la red móvil.
"""

from typing import Optional

from app.domain.models import (
    MetaFinanciera,
    PanelPrincipal,
    PrioridadTareaEnum,
    Recordatorio,
    Recompensa,
    RegistroPersonal,
    Rutina,
    SesionPomodoro,
    Subtarea,
    Tarea,
    Usuario,
)
from app.transfer.dtos import (
    DashboardResponseDTO,
    FinancialGoalResponseDTO,
    PersonalRecordResponseDTO,
    PomodoroResponseDTO,
    ReminderResponseDTO,
    RewardResponseDTO,
    RoutineDetailResponseDTO,
    RoutineResponseDTO,
    SubtaskResponseDTO,
    TaskResponseDTO,
    UserPreferencesDTO,
    UserResponseDTO,
)


class UsuarioMapper:
    """Convierte `Usuario` a `UserResponseDTO` excluyendo siempre `contrasenahash`."""

    @staticmethod
    def to_dto(
        entity: Usuario,
        preferencias: Optional[UserPreferencesDTO] = None,
    ) -> UserResponseDTO:
        return UserResponseDTO(
            id=entity.id,
            nombre=entity.nombre,
            correo=entity.correo,
            puntos=int(entity.puntos or 0),
            nivel=int(entity.nivel or 1),
            preferencias=preferencias or UserPreferencesDTO(),
        )


class TareaMapper:
    """Convierte `Tarea` y `Subtarea` a DTOs con etiquetas de baja fricción ('Fácil', 'Suave', 'Sin prisa')."""

    ETIQUETAS_ESFUERZO = {
        PrioridadTareaEnum.Baja: "Fácil",
        PrioridadTareaEnum.Media: "Suave",
        PrioridadTareaEnum.Alta: "Sin prisa",
    }

    @staticmethod
    def subtask_to_dto(entity: Subtarea) -> SubtaskResponseDTO:
        return SubtaskResponseDTO(
            id=entity.id,
            id_tarea=entity.id_tarea,
            descripcion=entity.descripcion,
            completada=bool(entity.completada),
        )

    @classmethod
    def to_dto(cls, entity: Tarea) -> TaskResponseDTO:
        subtareas_list = list(entity.subtareas or [])
        subtareas_dto = [cls.subtask_to_dto(s) for s in subtareas_list]
        total_sub = len(subtareas_dto)
        completadas_sub = sum(1 for s in subtareas_dto if s.completada)
        etiqueta = cls.ETIQUETAS_ESFUERZO.get(entity.prioridad, "Suave")
        progreso_str = (
            f"{completadas_sub}/{total_sub} pasos"
            if total_sub > 0
            else ("Lista" if entity.completada else "1 paso suave")
        )

        return TaskResponseDTO(
            id=entity.id,
            id_usuario=entity.id_usuario,
            id_rutina=entity.id_rutina,
            titulo=entity.titulo,
            descripcion=entity.descripcion,
            prioridad=entity.prioridad,
            etiqueta_esfuerzo=etiqueta,
            fechavencimiento=entity.fechavencimiento,
            completada=bool(entity.completada),
            puntos_recompensa=10,
            total_subtareas=total_sub,
            subtareas_completadas=completadas_sub,
            progreso_subtareas=progreso_str,
            subtareas=subtareas_dto,
        )


class RutinaMapper:
    """Convierte `Rutina` a `RoutineResponseDTO` y `RoutineDetailResponseDTO`."""

    @staticmethod
    def to_dto(entity: Rutina) -> RoutineResponseDTO:
        tareas_list = list(entity.tareas or [])
        return RoutineResponseDTO(
            id=entity.id,
            id_usuario=entity.id_usuario,
            nombre=entity.nombre,
            recurrencia=entity.recurrencia,
            hora=entity.hora,
            completadahoy=bool(entity.completadahoy),
            total_tareas_asociadas=len(tareas_list),
            mensaje_libre_de_culpa=(
                "¡Rutina de hoy lista! +10 dopamina."
                if entity.completadahoy
                else "A tu propio ritmo, sin castigos si hoy necesitas descansar."
            ),
        )

    @classmethod
    def to_detail_dto(cls, entity: Rutina) -> RoutineDetailResponseDTO:
        base = cls.to_dto(entity)
        tareas_dto = [TareaMapper.to_dto(t) for t in (entity.tareas or [])]
        return RoutineDetailResponseDTO(
            **base.model_dump(),
            tareas=tareas_dto,
        )


class PomodoroMapper:
    """Convierte `SesionPomodoro` a `PomodoroResponseDTO`."""

    @staticmethod
    def to_dto(entity: SesionPomodoro) -> PomodoroResponseDTO:
        duracion = int(entity.duracionconcentracion or 5)
        etiqueta = "Micro-enfoque 5 min" if duracion <= 10 else f"Enfoque suave {duracion} min"
        return PomodoroResponseDTO(
            id=entity.id,
            id_usuario=entity.id_usuario,
            id_tarea=entity.id_tarea,
            duracionconcentracion=duracion,
            duraciondescanso=int(entity.duraciondescanso or 5),
            sesionescompletadas=int(entity.sesionescompletadas or 0),
            modo_etiqueta=etiqueta,
        )


class RecordatorioMapper:
    """Convierte `Recordatorio` a `ReminderResponseDTO`."""

    @staticmethod
    def to_dto(entity: Recordatorio) -> ReminderResponseDTO:
        completada = bool(entity.completadahoy)
        return ReminderResponseDTO(
            id=entity.id,
            id_usuario=entity.id_usuario,
            id_tarea=entity.id_tarea,
            fechahora=entity.fechahora,
            mensaje=entity.mensaje,
            tipo=entity.tipo,
            completadahoy=completada,
            notificacion_activa=not completada,
        )


class RecompensaMapper:
    """Convierte `Recompensa` a `RewardResponseDTO`."""

    @staticmethod
    def to_dto(entity: Recompensa) -> RewardResponseDTO:
        return RewardResponseDTO(
            id=entity.id,
            id_tarea=entity.id_tarea,
            nombre=entity.nombre,
            costopuntos=int(entity.costopuntos or 0),
            desbloqueada=bool(entity.desbloqueada),
        )


class RegistroPersonalMapper:
    """Convierte `RegistroPersonal` a `PersonalRecordResponseDTO`."""

    @staticmethod
    def to_dto(entity: RegistroPersonal) -> PersonalRecordResponseDTO:
        nombre_lower = (entity.nombre or "").lower()
        if "sueño" in nombre_lower or "sueno" in nombre_lower or "hora" in nombre_lower:
            unidad = "horas"
        elif "ánimo" in nombre_lower or "animo" in nombre_lower or "humor" in nombre_lower or "energ" in nombre_lower:
            unidad = "nivel (1-5)"
        else:
            unidad = "unidades"

        return PersonalRecordResponseDTO(
            id=entity.id,
            id_usuario=entity.id_usuario,
            nombre=entity.nombre,
            valorobjetivo=float(entity.valorobjetivo or 0.0),
            valoractual=float(entity.valoractual or 0.0),
            progresoporcentaje=float(entity.progresoporcentaje or 0.0),
            unidad_sugerida=unidad,
        )


class MetaFinancieraMapper:
    """Convierte `MetaFinanciera` a `FinancialGoalResponseDTO`."""

    @staticmethod
    def to_dto(entity: MetaFinanciera) -> FinancialGoalResponseDTO:
        progreso = float(entity.progresoporcentaje or 0.0)
        objetivo = float(entity.valorobjetivo or 0.0)
        actual = float(entity.valoractual or 0.0)
        return FinancialGoalResponseDTO(
            id=entity.id,
            id_usuario=entity.id_usuario,
            nombre=entity.nombre,
            valorobjetivo=objetivo,
            valoractual=actual,
            progresoporcentaje=progreso,
            meta_alcanzada=progreso >= 100.0 or (objetivo > 0 and actual >= objetivo),
        )


class DashboardMapper:
    """Construye el `DashboardResponseDTO` consolidado para la pantalla principal."""

    @staticmethod
    def to_dto(
        panel: PanelPrincipal,
        usuario: Usuario,
        estado_energia_hoy: str,
        humor_hoy: Optional[str],
        pendientes: int,
        completadas_hoy: int,
        total_hoy: int,
        tareas_prioritarias: list[Tarea],
        rutinas_hoy: list[Rutina],
        recordatorios_proximos: list[Recordatorio],
        meta_diaria_puntos: int = 50,
    ) -> DashboardResponseDTO:
        primer_nombre = (usuario.nombre or "Usuario").split()[0]
        return DashboardResponseDTO(
            panel_id=panel.id,
            fecha_actual=panel.fechaactual,
            saludo=f"¡Hola, {primer_nombre}!",
            subtitulo_amigable="Vamos un paso a la vez",
            puntos_dopamina=int(usuario.puntos or 0),
            meta_diaria_puntos=meta_diaria_puntos,
            nivel=int(usuario.nivel or 1),
            estado_energia_hoy=estado_energia_hoy,
            humor_hoy=humor_hoy,
            resumen_tareas={
                "pendientes": pendientes,
                "completadas_hoy": completadas_hoy,
                "total_hoy": total_hoy,
                "texto_progreso": f"{completadas_hoy} de {total_hoy} listas",
            },
            micro_tareas_hoy=[TareaMapper.to_dto(t) for t in tareas_prioritarias],
            rutinas_hoy=[RutinaMapper.to_dto(r) for r in rutinas_hoy],
            recordatorios_proximos=[RecordatorioMapper.to_dto(rec) for rec in recordatorios_proximos],
            accion_rapida_etiqueta="¡Hacer algo fácil!",
        )
