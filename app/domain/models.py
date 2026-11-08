"""Modelos de Dominio (Entities SQLAlchemy) — Proyecto DOPA.

Agente Responsable: 3.1. Agente Arquitecto de Datos (Database & ORM Agent)
Fuente de Verdad: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf — Sección 4.3 (Páginas 50-56).
Mapea exactamente las 10 tablas y los 2 tipos ENUM del esquema PostgreSQL.
"""

from datetime import date, datetime, time
from decimal import Decimal
import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship

from app.data.database import Base


class PrioridadTareaEnum(str, enum.Enum):
    """Tipo ENUM `prioridad_tarea` en PostgreSQL."""

    Alta = "Alta"
    Media = "Media"
    Baja = "Baja"


class TipoRecordatorioEnum(str, enum.Enum):
    """Tipo ENUM `tipo_recordatorio` en PostgreSQL."""

    Tarea = "Tarea"
    Rutina = "Rutina"
    Compromiso = "Compromiso"


class Usuario(Base):
    """Tabla 1: `usuario` — Perfil, credenciales y progreso de dopamina (puntos/nivel)."""

    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("puntos >= 0", name="ck_usuario_puntos_no_negativos"),
        CheckConstraint("nivel >= 1", name="ck_usuario_nivel_minimo"),
        Index("idx_usuario_correo", "correo"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(120), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    contrasenahash = Column(String(255), nullable=False)
    puntos = Column(Integer, nullable=False, default=0)
    nivel = Column(Integer, nullable=False, default=1)

    # Relaciones bidireccionales 1:N
    rutinas = relationship(
        "Rutina",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    tareas = relationship(
        "Tarea",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    sesiones_pomodoro = relationship(
        "SesionPomodoro",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    recordatorios = relationship(
        "Recordatorio",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    registros_personales = relationship(
        "RegistroPersonal",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    metas_financieras = relationship(
        "MetaFinanciera",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    paneles_principales = relationship(
        "PanelPrincipal",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )


class Rutina(Base):
    """Tabla 2: `rutina` — Hábitos recurrentes libres de culpa (HU-04, HU-11)."""

    __tablename__ = "rutina"
    __table_args__ = (
        Index("idx_rutina_usuario", "id_usuario"),
        Index("idx_rutina_usuario_completada", "id_usuario", "completadahoy"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = Column(String(150), nullable=False)
    recurrencia = Column(String(100), nullable=False)
    hora = Column(Time, nullable=False, default=time(8, 0))
    completadahoy = Column(Boolean, nullable=False, default=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="rutinas")
    tareas = relationship("Tarea", back_populates="rutina")


class Tarea(Base):
    """Tabla 3: `tarea` — Actividades principales con prioridad y vencimiento (HU-02)."""

    __tablename__ = "tarea"
    __table_args__ = (
        Index("idx_tarea_usuario", "id_usuario"),
        Index("idx_tarea_rutina", "id_rutina"),
        Index("idx_tarea_usuario_estado_prioridad", "id_usuario", "completada", "prioridad"),
        Index("idx_tarea_fechavencimiento", "fechavencimiento"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    id_rutina = Column(
        Integer,
        ForeignKey("rutina.id", ondelete="SET NULL"),
        nullable=True,
    )
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    prioridad = Column(
        SAEnum(
            PrioridadTareaEnum,
            name="prioridad_tarea",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=PrioridadTareaEnum.Media,
    )
    fechavencimiento = Column(Date, nullable=True)
    completada = Column(Boolean, nullable=False, default=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="tareas")
    rutina = relationship("Rutina", back_populates="tareas")
    subtareas = relationship(
        "Subtarea",
        back_populates="tarea",
        cascade="all, delete-orphan",
        order_by="Subtarea.id",
    )
    sesiones_pomodoro = relationship("SesionPomodoro", back_populates="tarea")
    recordatorios = relationship(
        "Recordatorio",
        back_populates="tarea",
        cascade="all, delete-orphan",
    )
    recompensas = relationship("Recompensa", back_populates="tarea")


class Subtarea(Base):
    """Tabla 4: `subtarea` — Micro-pasos de una tarea para evitar bloqueo ejecutivo (HU-03)."""

    __tablename__ = "subtarea"
    __table_args__ = (Index("idx_subtarea_tarea", "id_tarea"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_tarea = Column(
        Integer,
        ForeignKey("tarea.id", ondelete="CASCADE"),
        nullable=False,
    )
    descripcion = Column(String(255), nullable=False)
    completada = Column(Boolean, nullable=False, default=False)

    # Relaciones
    tarea = relationship("Tarea", back_populates="subtareas")


class SesionPomodoro(Base):
    """Tabla 5: `sesionpomodoro` — Ciclos cortos de enfoque y pausas de bajo estímulo (HU-06)."""

    __tablename__ = "sesionpomodoro"
    __table_args__ = (
        CheckConstraint("duracionconcentracion > 0", name="ck_pomodoro_concentracion_positiva"),
        CheckConstraint("duraciondescanso >= 0", name="ck_pomodoro_descanso_no_negativo"),
        CheckConstraint("sesionescompletadas >= 0", name="ck_pomodoro_sesiones_no_negativas"),
        Index("idx_sesionpomodoro_usuario", "id_usuario"),
        Index("idx_sesionpomodoro_tarea", "id_tarea"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    id_tarea = Column(
        Integer,
        ForeignKey("tarea.id", ondelete="SET NULL"),
        nullable=True,
    )
    duracionconcentracion = Column(Integer, nullable=False, default=5)
    duraciondescanso = Column(Integer, nullable=False, default=5)
    sesionescompletadas = Column(Integer, nullable=False, default=0)

    # Relaciones
    usuario = relationship("Usuario", back_populates="sesiones_pomodoro")
    tarea = relationship("Tarea", back_populates="sesiones_pomodoro")


class Recordatorio(Base):
    """Tabla 6: `recordatorio` — Alertas programadas por fecha/hora y tipo (HU-05)."""

    __tablename__ = "recordatorio"
    __table_args__ = (
        Index("idx_recordatorio_usuario_fechahora", "id_usuario", "fechahora"),
        Index("idx_recordatorio_tarea", "id_tarea"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    id_tarea = Column(
        Integer,
        ForeignKey("tarea.id", ondelete="CASCADE"),
        nullable=True,
    )
    fechahora = Column(DateTime, nullable=False, default=datetime.utcnow)
    mensaje = Column(String(255), nullable=False)
    tipo = Column(
        SAEnum(
            TipoRecordatorioEnum,
            name="tipo_recordatorio",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=TipoRecordatorioEnum.Tarea,
    )
    completadahoy = Column(Boolean, nullable=False, default=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="recordatorios")
    tarea = relationship("Tarea", back_populates="recordatorios")


class Recompensa(Base):
    """Tabla 7: `recompensa` — Logros y recompensas de dopamina (HU-07)."""

    __tablename__ = "recompensa"
    __table_args__ = (
        CheckConstraint("costopuntos >= 0", name="ck_recompensa_costo_no_negativo"),
        Index("idx_recompensa_tarea", "id_tarea"),
        Index("idx_recompensa_desbloqueada", "desbloqueada"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_tarea = Column(
        Integer,
        ForeignKey("tarea.id", ondelete="SET NULL"),
        nullable=True,
    )
    nombre = Column(String(150), nullable=False)
    costopuntos = Column(Integer, nullable=False, default=10)
    desbloqueada = Column(Boolean, nullable=False, default=False)

    # Relaciones
    tarea = relationship("Tarea", back_populates="recompensas")


class RegistroPersonal(Base):
    """Tabla 8: `registropersonal` — Seguimiento de sueño, humor y energía diaria (HU-08)."""

    __tablename__ = "registropersonal"
    __table_args__ = (
        CheckConstraint("valorobjetivo > 0", name="ck_registropersonal_objetivo_positivo"),
        Index("idx_registropersonal_usuario", "id_usuario"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = Column(String(120), nullable=False)
    valorobjetivo = Column(Numeric(10, 2), nullable=False, default=Decimal("8.00"))
    valoractual = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    progresoporcentaje = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    # Relaciones
    usuario = relationship("Usuario", back_populates="registros_personales")


class MetaFinanciera(Base):
    """Tabla 9: `metafinanciera` — Metas de ahorro y control de gastos (HU-09)."""

    __tablename__ = "metafinanciera"
    __table_args__ = (
        CheckConstraint("valorobjetivo > 0", name="ck_metafinanciera_objetivo_positivo"),
        Index("idx_metafinanciera_usuario", "id_usuario"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = Column(String(150), nullable=False)
    valorobjetivo = Column(Numeric(12, 2), nullable=False)
    valoractual = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    progresoporcentaje = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    # Relaciones
    usuario = relationship("Usuario", back_populates="metas_financieras")


class PanelPrincipal(Base):
    """Tabla 10: `panelprincipal` — Registro de acceso diario al Dashboard (HU-10)."""

    __tablename__ = "panelprincipal"
    __table_args__ = (
        Index("idx_panelprincipal_usuario_fecha", "id_usuario", "fechaactual"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    fechaactual = Column(Date, nullable=False, default=date.today)

    # Relaciones
    usuario = relationship("Usuario", back_populates="paneles_principales")
