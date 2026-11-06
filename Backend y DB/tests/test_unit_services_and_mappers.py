"""Pruebas Unitarias de Seguridad, Mappers, Repositorios y Servicios — Proyecto DOPA.

Agente Responsable: 4.1. Agente de Pruebas Unitarias e Integración (Unit & Integration Test Agent)
Valida aisladamente las funciones criptográficas, conversión Entity <-> DTO, reglas de negocio
libres de culpa, cálculo de porcentajes, paginación y borrado en cascada (ON DELETE CASCADE).
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_preferences,
    hash_password,
    is_token_revoked,
    revoke_token,
    set_user_preferences,
    verify_password,
)
from app.core.services import calculate_progress_percentage
from app.data.database import get_db
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
from app.transfer.dtos import UserPreferencesDTO
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


# =====================================================================
# 1. PRUEBAS UNITARIAS DE SEGURIDAD (security.py)
# =====================================================================


def test_password_hashing_and_verification() -> None:
    """Verifica que bcrypt genere hashes seguros y valide contraseñas correctamente (RNF-06)."""
    raw_pass = "MiClaveSecretaTDAH2026!"
    hashed = hash_password(raw_pass)

    assert hashed != raw_pass
    assert hashed.startswith("$2b$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("ClaveIncorrecta", hashed) is False
    assert verify_password(raw_pass, "hash-invalido-no-bcrypt") is False


def test_jwt_access_and_refresh_token_lifecycle(db_session: Session) -> None:
    """Valida creación, decodificación, validación de tipo y revocación de JWT."""
    access = create_access_token(user_id=42, correo="fred@dopa.app")
    refresh = create_refresh_token(user_id=42, correo="fred@dopa.app")

    payload_access = decode_token(access, expected_type="access")
    assert payload_access["sub"] == "42"
    assert payload_access["email"] == "fred@dopa.app"
    assert payload_access["type"] == "access"

    payload_refresh = decode_token(refresh, expected_type="refresh")
    assert payload_refresh["sub"] == "42"
    assert payload_refresh["type"] == "refresh"

    # Rechazo cuando se usa refresh_token esperando access_token
    with pytest.raises(ValueError, match="Se esperaba un token de tipo 'access'"):
        decode_token(refresh, expected_type="access")

    # Revocación de token en logout
    assert is_token_revoked(access) is False
    revoke_token(access)
    assert is_token_revoked(access) is True
    with pytest.raises(ValueError, match="cerrado o revocado"):
        decode_token(access, expected_type="access")


def test_jwt_expired_and_invalid_tokens() -> None:
    """Valida el rechazo de tokens expirados o con firma corrupta."""
    expired_token = create_access_token(
        user_id=7,
        correo="expired@dopa.app",
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(ValueError, match="expirado"):
        decode_token(expired_token, expected_type="access")

    with pytest.raises(ValueError, match="inválido"):
        decode_token("token.malformado.invalido", expected_type="access")


def test_user_preferences_store(db_session: Session) -> None:
    """Verifica lectura por defecto y actualización de preferencias de usuario (HU-12)."""
    default_prefs = get_user_preferences(99)
    assert default_prefs.duracion_concentracion_min == 5
    assert default_prefs.modo_bajo_estimulo is True

    new_prefs = UserPreferencesDTO(
        duracion_concentracion_min=25,
        duracion_descanso_min=10,
        notificaciones_activas=False,
        sonidos_suaves=True,
        modo_bajo_estimulo=True,
        meta_diaria_dopamina=80,
        tema_visual="Menta Calma",
    )
    saved = set_user_preferences(99, new_prefs)
    assert saved.duracion_concentracion_min == 25
    assert get_user_preferences(99).tema_visual == "Menta Calma"


# =====================================================================
# 2. PRUEBAS UNITARIAS DE MAPPERS (mappers.py)
# =====================================================================


def test_usuario_mapper_excludes_password_hash() -> None:
    """Garantiza que UsuarioMapper nunca exponga `contrasenahash` en el DTO de salida."""
    user = Usuario(
        id=1,
        nombre="Fred",
        correo="fred@dopa.app",
        contrasenahash="$2b$12$secretHashValueNeverExpose",
        puntos=35,
        nivel=1,
    )
    dto = UsuarioMapper.to_dto(user)
    dumped = dto.model_dump()

    assert dto.id == 1
    assert dto.nombre == "Fred"
    assert dto.puntos == 35
    assert "contrasenahash" not in dumped
    assert "contrasena" not in dumped


def test_tarea_mapper_effort_labels_and_subtask_progress() -> None:
    """Verifica etiquetas 'Fácil', 'Suave', 'Sin prisa' y conteo de micro-pasos."""
    t_baja = Tarea(
        id=10,
        id_usuario=1,
        titulo="Responder a Ana",
        prioridad=PrioridadTareaEnum.Baja,
        completada=False,
    )
    t_baja.subtareas = []
    dto_baja = TareaMapper.to_dto(t_baja)
    assert dto_baja.etiqueta_esfuerzo == "Fácil"
    assert dto_baja.progreso_subtareas == "1 paso suave"

    t_completada_sin_sub = Tarea(
        id=11,
        id_usuario=1,
        titulo="Tomar agua",
        prioridad=PrioridadTareaEnum.Media,
        completada=True,
    )
    t_completada_sin_sub.subtareas = []
    dto_media = TareaMapper.to_dto(t_completada_sin_sub)
    assert dto_media.etiqueta_esfuerzo == "Suave"
    assert dto_media.progreso_subtareas == "Lista"

    t_alta = Tarea(
        id=12,
        id_usuario=1,
        titulo="Hacer la cama",
        prioridad=PrioridadTareaEnum.Alta,
        completada=False,
    )
    t_alta.subtareas = [
        Subtarea(id=1, id_tarea=12, descripcion="Sacudir sábanas", completada=True),
        Subtarea(id=2, id_tarea=12, descripcion="Acomodar almohada", completada=False),
    ]
    dto_alta = TareaMapper.to_dto(t_alta)
    assert dto_alta.etiqueta_esfuerzo == "Sin prisa"
    assert dto_alta.total_subtareas == 2
    assert dto_alta.subtareas_completadas == 1
    assert dto_alta.progreso_subtareas == "1/2 pasos"


def test_rutina_pomodoro_recordatorio_recompensa_mappers() -> None:
    """Verifica la transformación de Rutina, Pomodoro, Recordatorio y Recompensa a DTO."""
    rutina = Rutina(
        id=1,
        id_usuario=1,
        nombre="Mañana tranquila",
        recurrencia="Diaria",
        hora=time(8, 30),
        completadahoy=False,
    )
    rutina.tareas = []
    r_dto = RutinaMapper.to_dto(rutina)
    assert "sin castigos" in r_dto.mensaje_libre_de_culpa

    rutina.completadahoy = True
    r_detail = RutinaMapper.to_detail_dto(rutina)
    assert "+10 dopamina" in r_detail.mensaje_libre_de_culpa

    pomo_corto = SesionPomodoro(
        id=1,
        id_usuario=1,
        duracionconcentracion=5,
        duraciondescanso=5,
        sesionescompletadas=2,
    )
    assert PomodoroMapper.to_dto(pomo_corto).modo_etiqueta == "Micro-enfoque 5 min"

    pomo_largo = SesionPomodoro(
        id=2,
        id_usuario=1,
        duracionconcentracion=25,
        duraciondescanso=5,
        sesionescompletadas=1,
    )
    assert PomodoroMapper.to_dto(pomo_largo).modo_etiqueta == "Enfoque suave 25 min"

    rec_activo = Recordatorio(
        id=1,
        id_usuario=1,
        fechahora=datetime(2026, 5, 10, 9, 0),
        mensaje="Beber agua",
        tipo=TipoRecordatorioEnum.Rutina,
        completadahoy=False,
    )
    assert RecordatorioMapper.to_dto(rec_activo).notificacion_activa is True

    rec_completado = Recordatorio(
        id=2,
        id_usuario=1,
        fechahora=datetime(2026, 5, 10, 10, 0),
        mensaje="Tomar pausa",
        tipo=TipoRecordatorioEnum.Tarea,
        completadahoy=True,
    )
    assert RecordatorioMapper.to_dto(rec_completado).notificacion_activa is False

    recompensa = Recompensa(id=5, id_tarea=None, nombre="Sticker Estrella", costopuntos=20, desbloqueada=True)
    rew_dto = RecompensaMapper.to_dto(recompensa)
    assert rew_dto.nombre == "Sticker Estrella"
    assert rew_dto.desbloqueada is True


def test_registro_personal_meta_financiera_and_dashboard_mappers() -> None:
    """Verifica unidades sugeridas en RegistroPersonal, meta alcanzada en MetaFinanciera y saludo en Dashboard."""
    reg_sueno = RegistroPersonal(
        id=1,
        id_usuario=1,
        nombre="Horas de sueño",
        valorobjetivo=Decimal("8.00"),
        valoractual=Decimal("6.80"),
        progresoporcentaje=Decimal("85.00"),
    )
    assert RegistroPersonalMapper.to_dto(reg_sueno).unidad_sugerida == "horas"

    reg_humor = RegistroPersonal(
        id=2,
        id_usuario=1,
        nombre="Estado de humor diario",
        valorobjetivo=Decimal("5.00"),
        valoractual=Decimal("4.00"),
        progresoporcentaje=Decimal("80.00"),
    )
    assert RegistroPersonalMapper.to_dto(reg_humor).unidad_sugerida == "nivel (1-5)"

    reg_otro = RegistroPersonal(
        id=3,
        id_usuario=1,
        nombre="Vasos de agua",
        valorobjetivo=Decimal("8.00"),
        valoractual=Decimal("6.00"),
        progresoporcentaje=Decimal("75.00"),
    )
    assert RegistroPersonalMapper.to_dto(reg_otro).unidad_sugerida == "unidades"

    meta_parcial = MetaFinanciera(
        id=1,
        id_usuario=1,
        nombre="Fondo emergencia",
        valorobjetivo=Decimal("100.00"),
        valoractual=Decimal("40.00"),
        progresoporcentaje=Decimal("40.00"),
    )
    assert MetaFinancieraMapper.to_dto(meta_parcial).meta_alcanzada is False

    meta_completa = MetaFinanciera(
        id=2,
        id_usuario=1,
        nombre="Audífonos cancelación ruido",
        valorobjetivo=Decimal("100.00"),
        valoractual=Decimal("100.00"),
        progresoporcentaje=Decimal("100.00"),
    )
    assert MetaFinancieraMapper.to_dto(meta_completa).meta_alcanzada is True

    panel = PanelPrincipal(id=1, id_usuario=1, fechaactual=date.today())
    usuario = Usuario(id=1, nombre="Fred Salas", correo="fred@dopa.app", contrasenahash="hash", puntos=20, nivel=1)
    dash_dto = DashboardMapper.to_dto(
        panel=panel,
        usuario=usuario,
        estado_energia_hoy="media",
        humor_hoy="Con foco",
        pendientes=2,
        completadas_hoy=1,
        total_hoy=3,
        tareas_prioritarias=[],
        rutinas_hoy=[],
        recordatorios_proximos=[],
        meta_diaria_puntos=50,
    )
    assert dash_dto.saludo == "¡Hola, Fred!"
    assert dash_dto.resumen_tareas["texto_progreso"] == "1 de 3 listas"


# =====================================================================
# 3. PRUEBAS UNITARIAS DE SERVICIOS Y REPOSITORIOS (services.py / repositories.py)
# =====================================================================


def test_calculate_progress_percentage_edge_cases() -> None:
    """Verifica el cálculo exacto y acotado a [0.00, 100.00] de `progresoporcentaje`."""
    assert calculate_progress_percentage(Decimal("6.8"), Decimal("8.0")) == Decimal("85.00")
    assert calculate_progress_percentage(Decimal("150.0"), Decimal("100.0")) == Decimal("100.00")
    assert calculate_progress_percentage(Decimal("0.0"), Decimal("100.0")) == Decimal("0.00")
    assert calculate_progress_percentage(Decimal("-5.0"), Decimal("100.0")) == Decimal("0.00")
    assert calculate_progress_percentage(Decimal("50.0"), Decimal("0.0")) == Decimal("0.00")


def test_gamification_level_up_and_reward_auto_unlock(db_session: Session) -> None:
    """Verifica subida de nivel cada 50 puntos y desbloqueo automático de recompensas."""
    user_repo = UsuarioRepository(db_session)
    rew_repo = RecompensaRepository(db_session)
    tarea_repo = TareaRepository(db_session)

    fred = user_repo.create("Fred", "fred@dopa.app", hash_password("Clave1234!"))
    assert fred.puntos == 0
    assert fred.nivel == 1

    tarea = tarea_repo.create(id_usuario=fred.id, titulo="Organizar escritorio")
    rec_puntos = rew_repo.create(nombre="Medalla 50 pts", costopuntos=50, id_tarea=None)
    rec_tarea = rew_repo.create(nombre="Logro Escritorio", costopuntos=100, id_tarea=tarea.id)

    # Sumar 50 puntos -> Sube a nivel 2
    fred = user_repo.add_points_and_update_level(fred, 50)
    assert fred.puntos == 50
    assert fred.nivel == 2

    # Intento con delta 0 no altera ni resta puntos
    fred = user_repo.add_points_and_update_level(fred, 0)
    assert fred.puntos == 50

    desbloqueadas = rew_repo.auto_unlock_eligible(
        id_usuario=fred.id,
        puntos_usuario=fred.puntos,
        id_tarea_completada=tarea.id,
    )
    ids_desbloqueados = {r.id for r in desbloqueadas}
    assert rec_puntos.id in ids_desbloqueados
    assert rec_tarea.id in ids_desbloqueados


def test_repositories_pagination_quick_task_and_cascade_delete(db_session: Session) -> None:
    """Verifica paginación (`limit`/`offset`), selección de tarea fácil y borrado `ON DELETE CASCADE`."""
    user_repo = UsuarioRepository(db_session)
    tarea_repo = TareaRepository(db_session)
    sub_repo = SubtareaRepository(db_session)
    rec_repo = RecordatorioRepository(db_session)
    panel_repo = PanelPrincipalRepository(db_session)

    user = user_repo.create("Fred", "fred_cascade@dopa.app", hash_password("Clave1234!"))

    # Crear 3 tareas con distintas prioridades y micro-pasos
    t_alta = tarea_repo.create(
        id_usuario=user.id,
        titulo="Tarea compleja",
        prioridad=PrioridadTareaEnum.Alta,
        subtareas_descripciones=["Paso 1", "Paso 2"],
    )
    t_facil = tarea_repo.create(
        id_usuario=user.id,
        titulo="Responder mensaje corto",
        prioridad=PrioridadTareaEnum.Baja,
        subtareas_descripciones=[],
    )
    t_media = tarea_repo.create(
        id_usuario=user.id,
        titulo="Tarea media",
        prioridad=PrioridadTareaEnum.Media,
        subtareas_descripciones=["Paso único"],
    )

    # Paginación limit=2, offset=0
    pagina_1, total = tarea_repo.list_by_user(user.id, limit=2, offset=0)
    pagina_2, _ = tarea_repo.list_by_user(user.id, limit=2, offset=2)
    assert total == 3
    assert len(pagina_1) == 2
    assert len(pagina_2) == 1

    # Tarea más rápida para "¡Hacer algo fácil!" debe ser `t_facil` (0 subtareas pendientes y prioridad Baja)
    quick = tarea_repo.get_quickest_pending_task(user.id)
    assert quick is not None
    assert quick.id == t_facil.id

    # Asociar un recordatorio a `t_alta` y probar borrado en cascada (ON DELETE CASCADE)
    recordatorio = rec_repo.create(
        id_usuario=user.id,
        fechahora=datetime.now(timezone.utc),
        mensaje="Alerta de tarea compleja",
        tipo=TipoRecordatorioEnum.Tarea,
        id_tarea=t_alta.id,
    )
    rutina_repo = RutinaRepository(db_session)
    rut = rutina_repo.create(id_usuario=user.id, nombre="Rutina filtro", recurrencia="Diaria")
    items_rut, _ = rutina_repo.list_by_user(user.id, completadahoy=False)
    assert len(items_rut) == 1
    assert rut.id == items_rut[0].id
    assert len(sub_repo.list_by_task(t_alta.id)) == 2
    assert rec_repo.get_by_id_and_user(recordatorio.id, user.id) is not None

    # Eliminar tarea principal -> debe borrar subtareas y recordatorio en cascada
    tarea_repo.delete(t_alta)
    assert sub_repo.list_by_task(t_alta.id) == []
    assert rec_repo.get_by_id_and_user(recordatorio.id, user.id) is None

    # PanelPrincipal idempotente por día
    p1 = panel_repo.register_or_get_today(user.id)
    p2 = panel_repo.register_or_get_today(user.id)
    assert p1.id == p2.id
    assert len(panel_repo.list_by_user(user.id)) == 1


def test_get_db_dependency_generator() -> None:
    """Verifica que el generador `get_db` entregue una sesión SQLAlchemy válida y cierre limpiamente."""
    gen = get_db()
    session = next(gen)
    assert session is not None
    gen.close()
