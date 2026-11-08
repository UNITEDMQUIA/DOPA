"""Capa de Acceso a Datos (Repositories) — Proyecto DOPA.

Agente Responsable: 3.2. Agente de API y Lógica de Negocio (Backend Core Agent)
Referencia Arquitectónica: PLANEACIÓN Y DISEÑO DE SOFTWARE (1).pdf — Sección 4.2.4.
Encapsula las consultas SQL mediante SQLAlchemy ORM, garantizando transacciones seguras,
aislamiento estricto por `id_usuario` (RNF-08, RNF-09) y paginación (`limit` / `offset`).
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

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
    TipoRecordatorioEnum,
    Usuario,
)


class UsuarioRepository:
    """Repositorio transaccional para la entidad `Usuario`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, id_usuario: int) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.id == id_usuario).first()

    def get_by_email(self, correo: str) -> Optional[Usuario]:
        correo_norm = correo.strip().lower()
        return (
            self.db.query(Usuario)
            .filter(func.lower(Usuario.correo) == correo_norm)
            .first()
        )

    def create(self, nombre: str, correo: str, contrasenahash: str) -> Usuario:
        usuario = Usuario(
            nombre=nombre.strip(),
            correo=correo.strip().lower(),
            contrasenahash=contrasenahash,
            puntos=0,
            nivel=1,
        )
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def add_points_and_update_level(self, usuario: Usuario, puntos_delta: int) -> Usuario:
        """Incrementa puntos de dopamina y recalcula el nivel (Libre de culpa: nunca resta)."""
        if puntos_delta > 0:
            usuario.puntos = int(usuario.puntos or 0) + puntos_delta
            nuevo_nivel = 1 + (usuario.puntos // 50)
            if nuevo_nivel > (usuario.nivel or 1):
                usuario.nivel = nuevo_nivel
            self.db.add(usuario)
            self.db.commit()
            self.db.refresh(usuario)
        return usuario


class TareaRepository:
    """Repositorio transaccional con paginación para `Tarea` y sus `Subtarea`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(
        self,
        id_usuario: int,
        limit: int = 20,
        offset: int = 0,
        completada: Optional[bool] = None,
        prioridad: Optional[PrioridadTareaEnum] = None,
        id_rutina: Optional[int] = None,
    ) -> tuple[list[Tarea], int]:
        query = (
            self.db.query(Tarea)
            .options(joinedload(Tarea.subtareas))
            .filter(Tarea.id_usuario == id_usuario)
        )
        if completada is not None:
            query = query.filter(Tarea.completada == completada)
        if prioridad is not None:
            query = query.filter(Tarea.prioridad == prioridad)
        if id_rutina is not None:
            query = query.filter(Tarea.id_rutina == id_rutina)

        total = query.count()
        items = (
            query.order_by(Tarea.completada.asc(), Tarea.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total

    def count_stats_by_user(self, id_usuario: int) -> tuple[int, int, int]:
        """Retorna (pendientes, completadas, total) del usuario."""
        total = self.db.query(func.count(Tarea.id)).filter(Tarea.id_usuario == id_usuario).scalar() or 0
        completadas = (
            self.db.query(func.count(Tarea.id))
            .filter(Tarea.id_usuario == id_usuario, Tarea.completada.is_(True))
            .scalar()
            or 0
        )
        pendientes = max(0, total - completadas)
        return pendientes, completadas, total

    def get_by_id_and_user(self, id_tarea: int, id_usuario: int) -> Optional[Tarea]:
        return (
            self.db.query(Tarea)
            .options(joinedload(Tarea.subtareas))
            .filter(Tarea.id == id_tarea, Tarea.id_usuario == id_usuario)
            .first()
        )

    def get_quickest_pending_task(self, id_usuario: int) -> Optional[Tarea]:
        """Obtiene la tarea pendiente de menor fricción para el botón '¡Hacer algo fácil!'."""
        tareas_pendientes = (
            self.db.query(Tarea)
            .options(joinedload(Tarea.subtareas))
            .filter(Tarea.id_usuario == id_usuario, Tarea.completada.is_(False))
            .all()
        )
        if not tareas_pendientes:
            return None

        prioridad_orden = {
            PrioridadTareaEnum.Baja: 0,
            PrioridadTareaEnum.Media: 1,
            PrioridadTareaEnum.Alta: 2,
        }
        tareas_ordenadas = sorted(
            tareas_pendientes,
            key=lambda t: (
                len([s for s in t.subtareas if not s.completada]),
                prioridad_orden.get(t.prioridad, 1),
                t.id,
            ),
        )
        return tareas_ordenadas[0]

    def create(
        self,
        id_usuario: int,
        titulo: str,
        descripcion: Optional[str] = None,
        prioridad: PrioridadTareaEnum = PrioridadTareaEnum.Media,
        fechavencimiento: Optional[date] = None,
        id_rutina: Optional[int] = None,
        subtareas_descripciones: Optional[list[str]] = None,
    ) -> Tarea:
        tarea = Tarea(
            id_usuario=id_usuario,
            id_rutina=id_rutina,
            titulo=titulo.strip(),
            descripcion=descripcion.strip() if descripcion else None,
            prioridad=prioridad,
            fechavencimiento=fechavencimiento,
            completada=False,
        )
        self.db.add(tarea)
        self.db.flush()

        if subtareas_descripciones:
            for desc in subtareas_descripciones:
                if desc and desc.strip():
                    sub = Subtarea(
                        id_tarea=tarea.id,
                        descripcion=desc.strip(),
                        completada=False,
                    )
                    self.db.add(sub)

        self.db.commit()
        self.db.refresh(tarea)
        return tarea

    def update(self, tarea: Tarea, **kwargs) -> Tarea:
        for campo, valor in kwargs.items():
            if hasattr(tarea, campo) and valor is not None:
                setattr(tarea, campo, valor)
        self.db.add(tarea)
        self.db.commit()
        self.db.refresh(tarea)
        return tarea

    def delete(self, tarea: Tarea) -> None:
        self.db.delete(tarea)
        self.db.commit()


class SubtareaRepository:
    """Repositorio transaccional para `Subtarea` (micro-pasos de enfoque suave)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_task(self, id_tarea: int, limit: int = 50, offset: int = 0) -> list[Subtarea]:
        return (
            self.db.query(Subtarea)
            .filter(Subtarea.id_tarea == id_tarea)
            .order_by(Subtarea.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_id_and_task(self, id_subtarea: int, id_tarea: int) -> Optional[Subtarea]:
        return (
            self.db.query(Subtarea)
            .filter(Subtarea.id == id_subtarea, Subtarea.id_tarea == id_tarea)
            .first()
        )

    def create(self, id_tarea: int, descripcion: str, completada: bool = False) -> Subtarea:
        subtarea = Subtarea(
            id_tarea=id_tarea,
            descripcion=descripcion.strip(),
            completada=completada,
        )
        self.db.add(subtarea)
        self.db.commit()
        self.db.refresh(subtarea)
        return subtarea

    def update(
        self,
        subtarea: Subtarea,
        descripcion: Optional[str] = None,
        completada: Optional[bool] = None,
    ) -> Subtarea:
        if descripcion is not None:
            subtarea.descripcion = descripcion.strip()
        if completada is not None:
            subtarea.completada = completada
        self.db.add(subtarea)
        self.db.commit()
        self.db.refresh(subtarea)
        return subtarea

    def delete(self, subtarea: Subtarea) -> None:
        self.db.delete(subtarea)
        self.db.commit()


class RutinaRepository:
    """Repositorio transaccional con paginación para `Rutina`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(
        self,
        id_usuario: int,
        limit: int = 20,
        offset: int = 0,
        completadahoy: Optional[bool] = None,
    ) -> tuple[list[Rutina], int]:
        query = (
            self.db.query(Rutina)
            .options(joinedload(Rutina.tareas))
            .filter(Rutina.id_usuario == id_usuario)
        )
        if completadahoy is not None:
            query = query.filter(Rutina.completadahoy == completadahoy)

        total = query.count()
        items = query.order_by(Rutina.hora.asc(), Rutina.id.asc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id_and_user(self, id_rutina: int, id_usuario: int) -> Optional[Rutina]:
        return (
            self.db.query(Rutina)
            .options(joinedload(Rutina.tareas))
            .filter(Rutina.id == id_rutina, Rutina.id_usuario == id_usuario)
            .first()
        )

    def create(
        self,
        id_usuario: int,
        nombre: str,
        recurrencia: str,
        hora: time = time(8, 0),
    ) -> Rutina:
        rutina = Rutina(
            id_usuario=id_usuario,
            nombre=nombre.strip(),
            recurrencia=recurrencia.strip(),
            hora=hora,
            completadahoy=False,
        )
        self.db.add(rutina)
        self.db.commit()
        self.db.refresh(rutina)
        return rutina

    def update(self, rutina: Rutina, **kwargs) -> Rutina:
        for campo, valor in kwargs.items():
            if hasattr(rutina, campo) and valor is not None:
                setattr(rutina, campo, valor)
        self.db.add(rutina)
        self.db.commit()
        self.db.refresh(rutina)
        return rutina

    def delete(self, rutina: Rutina) -> None:
        self.db.delete(rutina)
        self.db.commit()


class SesionPomodoroRepository:
    """Repositorio transaccional con paginación para `SesionPomodoro`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(
        self,
        id_usuario: int,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SesionPomodoro], int]:
        query = self.db.query(SesionPomodoro).filter(SesionPomodoro.id_usuario == id_usuario)
        total = query.count()
        items = query.order_by(SesionPomodoro.id.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id_and_user(self, id_sesion: int, id_usuario: int) -> Optional[SesionPomodoro]:
        return (
            self.db.query(SesionPomodoro)
            .filter(SesionPomodoro.id == id_sesion, SesionPomodoro.id_usuario == id_usuario)
            .first()
        )

    def create(
        self,
        id_usuario: int,
        duracionconcentracion: int = 5,
        duraciondescanso: int = 5,
        id_tarea: Optional[int] = None,
    ) -> SesionPomodoro:
        sesion = SesionPomodoro(
            id_usuario=id_usuario,
            id_tarea=id_tarea,
            duracionconcentracion=duracionconcentracion,
            duraciondescanso=duraciondescanso,
            sesionescompletadas=0,
        )
        self.db.add(sesion)
        self.db.commit()
        self.db.refresh(sesion)
        return sesion

    def increment_completed(self, sesion: SesionPomodoro) -> SesionPomodoro:
        sesion.sesionescompletadas = int(sesion.sesionescompletadas or 0) + 1
        self.db.add(sesion)
        self.db.commit()
        self.db.refresh(sesion)
        return sesion


class RecordatorioRepository:
    """Repositorio transaccional con paginación para `Recordatorio`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(
        self,
        id_usuario: int,
        limit: int = 20,
        offset: int = 0,
        tipo: Optional[TipoRecordatorioEnum] = None,
        completadahoy: Optional[bool] = None,
    ) -> tuple[list[Recordatorio], int]:
        query = self.db.query(Recordatorio).filter(Recordatorio.id_usuario == id_usuario)
        if tipo is not None:
            query = query.filter(Recordatorio.tipo == tipo)
        if completadahoy is not None:
            query = query.filter(Recordatorio.completadahoy == completadahoy)

        total = query.count()
        items = query.order_by(Recordatorio.fechahora.asc(), Recordatorio.id.asc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id_and_user(self, id_recordatorio: int, id_usuario: int) -> Optional[Recordatorio]:
        return (
            self.db.query(Recordatorio)
            .filter(Recordatorio.id == id_recordatorio, Recordatorio.id_usuario == id_usuario)
            .first()
        )

    def create(
        self,
        id_usuario: int,
        fechahora: datetime,
        mensaje: str,
        tipo: TipoRecordatorioEnum = TipoRecordatorioEnum.Tarea,
        id_tarea: Optional[int] = None,
    ) -> Recordatorio:
        recordatorio = Recordatorio(
            id_usuario=id_usuario,
            id_tarea=id_tarea,
            fechahora=fechahora,
            mensaje=mensaje.strip(),
            tipo=tipo,
            completadahoy=False,
        )
        self.db.add(recordatorio)
        self.db.commit()
        self.db.refresh(recordatorio)
        return recordatorio

    def update(self, recordatorio: Recordatorio, **kwargs) -> Recordatorio:
        for campo, valor in kwargs.items():
            if hasattr(recordatorio, campo) and valor is not None:
                setattr(recordatorio, campo, valor)
        self.db.add(recordatorio)
        self.db.commit()
        self.db.refresh(recordatorio)
        return recordatorio

    def delete(self, recordatorio: Recordatorio) -> None:
        self.db.delete(recordatorio)
        self.db.commit()


class RecompensaRepository:
    """Repositorio transaccional para `Recompensa`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(
        self,
        id_usuario: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Recompensa], int]:
        query = (
            self.db.query(Recompensa)
            .outerjoin(Tarea, Recompensa.id_tarea == Tarea.id)
            .filter(
                or_(
                    Recompensa.id_tarea.is_(None),
                    Tarea.id_usuario == id_usuario,
                )
            )
        )
        total = query.count()
        items = query.order_by(Recompensa.costopuntos.asc(), Recompensa.id.asc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id_for_user(self, id_recompensa: int, id_usuario: int) -> Optional[Recompensa]:
        return (
            self.db.query(Recompensa)
            .outerjoin(Tarea, Recompensa.id_tarea == Tarea.id)
            .filter(
                Recompensa.id == id_recompensa,
                or_(
                    Recompensa.id_tarea.is_(None),
                    Tarea.id_usuario == id_usuario,
                ),
            )
            .first()
        )

    def create(
        self,
        nombre: str,
        costopuntos: int = 10,
        id_tarea: Optional[int] = None,
        desbloqueada: bool = False,
    ) -> Recompensa:
        recompensa = Recompensa(
            id_tarea=id_tarea,
            nombre=nombre.strip(),
            costopuntos=costopuntos,
            desbloqueada=desbloqueada,
        )
        self.db.add(recompensa)
        self.db.commit()
        self.db.refresh(recompensa)
        return recompensa

    def unlock(self, recompensa: Recompensa) -> Recompensa:
        if not recompensa.desbloqueada:
            recompensa.desbloqueada = True
            self.db.add(recompensa)
            self.db.commit()
            self.db.refresh(recompensa)
        return recompensa

    def auto_unlock_eligible(
        self,
        id_usuario: int,
        puntos_usuario: int,
        id_tarea_completada: Optional[int] = None,
    ) -> list[Recompensa]:
        """Desbloquea recompensas elegibles por puntos o por completar su tarea asociada."""
        pendientes = (
            self.db.query(Recompensa)
            .outerjoin(Tarea, Recompensa.id_tarea == Tarea.id)
            .filter(
                Recompensa.desbloqueada.is_(False),
                or_(
                    Recompensa.id_tarea.is_(None),
                    Tarea.id_usuario == id_usuario,
                ),
            )
            .all()
        )
        recien_desbloqueadas: list[Recompensa] = []
        for rec in pendientes:
            por_tarea = id_tarea_completada is not None and rec.id_tarea == id_tarea_completada
            por_puntos = rec.id_tarea is None and puntos_usuario >= int(rec.costopuntos or 0)
            if por_tarea or por_puntos:
                rec.desbloqueada = True
                self.db.add(rec)
                recien_desbloqueadas.append(rec)

        if recien_desbloqueadas:
            self.db.commit()
            for rec in recien_desbloqueadas:
                self.db.refresh(rec)
        return recien_desbloqueadas


class RegistroPersonalRepository:
    """Repositorio transaccional con paginación para `RegistroPersonal`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(
        self,
        id_usuario: int,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[RegistroPersonal], int]:
        query = self.db.query(RegistroPersonal).filter(RegistroPersonal.id_usuario == id_usuario)
        total = query.count()
        items = query.order_by(RegistroPersonal.id.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id_and_user(self, id_registro: int, id_usuario: int) -> Optional[RegistroPersonal]:
        return (
            self.db.query(RegistroPersonal)
            .filter(RegistroPersonal.id == id_registro, RegistroPersonal.id_usuario == id_usuario)
            .first()
        )

    def create(
        self,
        id_usuario: int,
        nombre: str,
        valorobjetivo: Decimal,
        valoractual: Decimal,
        progresoporcentaje: Decimal,
    ) -> RegistroPersonal:
        registro = RegistroPersonal(
            id_usuario=id_usuario,
            nombre=nombre.strip(),
            valorobjetivo=valorobjetivo,
            valoractual=valoractual,
            progresoporcentaje=progresoporcentaje,
        )
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def update(self, registro: RegistroPersonal, **kwargs) -> RegistroPersonal:
        for campo, valor in kwargs.items():
            if hasattr(registro, campo) and valor is not None:
                setattr(registro, campo, valor)
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def delete(self, registro: RegistroPersonal) -> None:
        self.db.delete(registro)
        self.db.commit()


class MetaFinancieraRepository:
    """Repositorio transaccional con paginación para `MetaFinanciera`."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(
        self,
        id_usuario: int,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MetaFinanciera], int]:
        query = self.db.query(MetaFinanciera).filter(MetaFinanciera.id_usuario == id_usuario)
        total = query.count()
        items = query.order_by(MetaFinanciera.id.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id_and_user(self, id_meta: int, id_usuario: int) -> Optional[MetaFinanciera]:
        return (
            self.db.query(MetaFinanciera)
            .filter(MetaFinanciera.id == id_meta, MetaFinanciera.id_usuario == id_usuario)
            .first()
        )

    def create(
        self,
        id_usuario: int,
        nombre: str,
        valorobjetivo: Decimal,
        valoractual: Decimal,
        progresoporcentaje: Decimal,
    ) -> MetaFinanciera:
        meta = MetaFinanciera(
            id_usuario=id_usuario,
            nombre=nombre.strip(),
            valorobjetivo=valorobjetivo,
            valoractual=valoractual,
            progresoporcentaje=progresoporcentaje,
        )
        self.db.add(meta)
        self.db.commit()
        self.db.refresh(meta)
        return meta

    def update(self, meta: MetaFinanciera, **kwargs) -> MetaFinanciera:
        for campo, valor in kwargs.items():
            if hasattr(meta, campo) and valor is not None:
                setattr(meta, campo, valor)
        self.db.add(meta)
        self.db.commit()
        self.db.refresh(meta)
        return meta

    def delete(self, meta: MetaFinanciera) -> None:
        self.db.delete(meta)
        self.db.commit()


class PanelPrincipalRepository:
    """Repositorio transaccional para `PanelPrincipal` (accesos diarios al Dashboard)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def register_or_get_today(self, id_usuario: int, fecha: Optional[date] = None) -> PanelPrincipal:
        hoy = fecha or date.today()
        panel = (
            self.db.query(PanelPrincipal)
            .filter(PanelPrincipal.id_usuario == id_usuario, PanelPrincipal.fechaactual == hoy)
            .first()
        )
        if not panel:
            panel = PanelPrincipal(id_usuario=id_usuario, fechaactual=hoy)
            self.db.add(panel)
            self.db.commit()
            self.db.refresh(panel)
        return panel

    def list_by_user(self, id_usuario: int, limit: int = 30, offset: int = 0) -> list[PanelPrincipal]:
        return (
            self.db.query(PanelPrincipal)
            .filter(PanelPrincipal.id_usuario == id_usuario)
            .order_by(PanelPrincipal.fechaactual.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
