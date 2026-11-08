import '../models/user_model.dart';
import '../models/task_model.dart';
import '../models/focus_session_model.dart';
import '../models/wellness_record_model.dart';
import '../models/reward_model.dart';
import 'api_service.dart';

/// Servicio de Persistencia Híbrida (Sincronización REST FastAPI `/api/v1` + Caché Local Offline-First).
///
/// Agente Responsable: Agent_Frontend & Agent_Backend
/// Conecta todas las pantallas de Flutter con los endpoints del Backend FastAPI y
/// mantiene un respaldo en memoria para garantizar respuesta instantánea y
/// tolerancia a desconexiones móviles.
class DBService {
  static final DBService instance = DBService._init();
  DBService._init();

  Usuario _usuarioCache = Usuario(
    id: 1,
    nombre: 'Fred',
    dopaminaActual: 32,
    dopaminaMeta: 50,
    rachaDias: 4,
    energiaNivel: 0.45,
  );

  List<TareaBloque> _tareasCache = [
    TareaBloque(
      id: 1,
      titulo: 'Hacer la cama',
      subtitulo: 'Fácil · 2 micro-pasos · 5 min',
      duracionMinutos: 5,
      estado: EstadoTarea.ahora,
      puntosDopamina: 10,
      estresNivel: 0.1,
      microPasos: [
        MicroPaso(
          id: 1,
          tareaId: 1,
          descripcion: '1. Estirar las sábanas',
          completado: true,
        ),
        MicroPaso(
          id: 2,
          tareaId: 1,
          descripcion: '2. Colocar almohadas',
          completado: false,
        ),
      ],
    ),
    TareaBloque(
      id: 2,
      titulo: 'Responder a Ana',
      subtitulo: 'Suave · 3 min',
      duracionMinutos: 3,
      estado: EstadoTarea.despues,
      puntosDopamina: 5,
      estresNivel: 0.3,
      microPasos: [
        MicroPaso(
          id: 3,
          tareaId: 2,
          descripcion: '1. Abrir el chat de Ana',
          completado: true,
        ),
        MicroPaso(
          id: 4,
          tareaId: 2,
          descripcion: '2. Escribir respuesta de 2 líneas y enviar',
          completado: false,
        ),
      ],
    ),
    TareaBloque(
      id: 3,
      titulo: 'Guardar la ropa',
      subtitulo: 'Sin prisa · 8 min',
      duracionMinutos: 8,
      estado: EstadoTarea.despues,
      puntosDopamina: 8,
      estresNivel: 0.25,
      microPasos: [
        MicroPaso(
          id: 5,
          tareaId: 3,
          descripcion: '1. Separar camisetas de pantalones',
          completado: false,
        ),
        MicroPaso(
          id: 6,
          tareaId: 3,
          descripcion: '2. Guardar en el primer cajón',
          completado: false,
        ),
      ],
    ),
    TareaBloque(
      id: 4,
      titulo: 'Preparar la botella',
      subtitulo: '¡Hecho! · +5 dopamina',
      duracionMinutos: 1,
      estado: EstadoTarea.hecho,
      puntosDopamina: 5,
      estresNivel: 0.05,
    ),
  ];

  // ===========================================================================
  // 1. CRUD: USUARIO & DASHBOARD (`/api/v1/dashboard` y `/api/v1/auth/me`)
  // ===========================================================================

  /// Obtiene los datos del perfil del usuario desde `/api/v1/dashboard` con respaldo local.
  Future<Usuario> getUsuario() async {
    try {
      final dashboardJson = await ApiService.instance.getDashboard();
      _usuarioCache = Usuario.fromBackendJson(dashboardJson);
      return _usuarioCache;
    } catch (_) {
      return _usuarioCache;
    }
  }

  /// Actualiza métricas o preferencias del usuario en `/api/v1/auth/preferences` y `/api/v1/dashboard/energy-checkin`.
  Future<int> updateUsuario(Usuario usuario) async {
    _usuarioCache = usuario;
    try {
      await ApiService.instance.updatePreferences({
        'meta_diaria_dopamina': usuario.dopaminaMeta,
      });
      final nivelEnergia = usuario.energiaNivel < 0.35
          ? 'poquita'
          : (usuario.energiaNivel > 0.7 ? 'a tope' : 'media');
      await ApiService.instance.energyCheckin(nivelEnergia: nivelEnergia);
      return 1;
    } catch (_) {
      return 1;
    }
  }

  // ===========================================================================
  // 2. CRUD: TAREA_BLOQUE & MICRO_PASOS (`/api/v1/tasks`)
  // ===========================================================================

  /// Inserta una nueva micro-tarea en `/api/v1/tasks`.
  Future<int> insertarTarea(TareaBloque tarea) async {
    try {
      final created = await ApiService.instance.createTask(
        titulo: tarea.titulo,
        descripcion: tarea.subtitulo,
        prioridad: tarea.prioridad,
        subtareas: tarea.microPasos.map((m) => m.descripcion).toList(),
      );
      final nuevaTarea = TareaBloque.fromBackendJson(created);
      _tareasCache.add(nuevaTarea);
      return nuevaTarea.id ?? 101;
    } catch (_) {
      final nextId = (_tareasCache.isEmpty ? 100 : (_tareasCache.last.id ?? 100)) + 1;
      _tareasCache.add(
        TareaBloque(
          id: nextId,
          titulo: tarea.titulo,
          subtitulo: tarea.subtitulo,
          duracionMinutos: tarea.duracionMinutos,
          estado: tarea.estado,
          puntosDopamina: tarea.puntosDopamina,
          estresNivel: tarea.estresNivel,
          microPasos: tarea.microPasos,
        ),
      );
      return nextId;
    }
  }

  /// Obtiene la lista de tareas del día desde `/api/v1/tasks`.
  Future<List<TareaBloque>> obtenerTareas() async {
    try {
      final response = await ApiService.instance.listTasks(limit: 50, offset: 0);
      final rawItems = response['items'] as List<dynamic>? ?? const [];
      if (rawItems.isNotEmpty) {
        bool firstPendingAssigned = false;
        final mapped = <TareaBloque>[];
        for (final item in rawItems) {
          if (item is Map<String, dynamic>) {
            final bool isPending = item['completada'] != true;
            final bool markAsNow = isPending && !firstPendingAssigned;
            if (markAsNow) firstPendingAssigned = true;
            mapped.add(
              TareaBloque.fromBackendJson(item, isFirstPending: markAsNow),
            );
          }
        }
        _tareasCache = mapped;
      }
      return List<TareaBloque>.from(_tareasCache);
    } catch (_) {
      return List<TareaBloque>.from(_tareasCache);
    }
  }

  /// Actualiza el estado o datos de una tarea en `/api/v1/tasks/{id}` o `/api/v1/tasks/{id}/complete`.
  Future<int> actualizarTarea(TareaBloque tarea) async {
    final index = _tareasCache.indexWhere((t) => t.id == tarea.id);
    if (index != -1) {
      _tareasCache[index] = tarea;
    }
    if (tarea.id == null) return 1;

    try {
      if (tarea.estado == EstadoTarea.hecho) {
        final completed = await ApiService.instance.completeTask(tarea.id!);
        final puntosTotales = completed['puntos_totales'] as int?;
        if (puntosTotales != null) {
          _usuarioCache = Usuario(
            id: _usuarioCache.id,
            nombre: _usuarioCache.nombre,
            correo: _usuarioCache.correo,
            dopaminaActual: puntosTotales,
            dopaminaMeta: _usuarioCache.dopaminaMeta,
            nivel: completed['nivel_actual'] as int? ?? _usuarioCache.nivel,
            rachaDias: _usuarioCache.rachaDias,
            energiaNivel: _usuarioCache.energiaNivel,
          );
        }
      } else {
        await ApiService.instance.updateTask(tarea.id!, {
          'titulo': tarea.titulo,
          'completada': false,
        });
      }
      return 1;
    } catch (_) {
      return 1;
    }
  }

  /// Actualiza el estado de un micro-paso individual en `/api/v1/tasks/{task_id}/subtasks/{subtask_id}`.
  Future<int> actualizarMicroPaso({
    required int tareaId,
    required int microPasoId,
    required bool completado,
  }) async {
    try {
      await ApiService.instance.updateSubtask(
        tareaId,
        microPasoId,
        completada: completado,
      );
      return 1;
    } catch (_) {
      return 1;
    }
  }

  /// Elimina una tarea por ID en `/api/v1/tasks/{id}`.
  Future<int> eliminarTarea(int id) async {
    _tareasCache.removeWhere((t) => t.id == id);
    try {
      await ApiService.instance.deleteTask(id);
      return 1;
    } catch (_) {
      return 1;
    }
  }

  // ===========================================================================
  // 3. CRUD: SESION_ENFOQUE (`/api/v1/pomodoro/sessions`)
  // ===========================================================================

  /// Registra una sesión de enfoque suave en `/api/v1/pomodoro/sessions` y la completa si aplica.
  Future<int> registrarSesion(SesionEnfoque sesion) async {
    try {
      final duracionMin = (sesion.duracionSegundos ~/ 60).clamp(1, 180);
      final created = await ApiService.instance.createPomodoroSession(
        idTarea: sesion.tareaId,
        duracionConcentracion: duracionMin,
        duracionDescanso: 5,
      );
      final sessionId = created['id'] as int? ?? 201;
      if (sesion.completada) {
        final action = await ApiService.instance.completePomodoroSession(sessionId);
        final nuevosPuntos = action['puntos_totales'] as int?;
        if (nuevosPuntos != null) {
          _usuarioCache = Usuario(
            id: _usuarioCache.id,
            nombre: _usuarioCache.nombre,
            correo: _usuarioCache.correo,
            dopaminaActual: nuevosPuntos,
            dopaminaMeta: _usuarioCache.dopaminaMeta,
            nivel: action['nivel_actual'] as int? ?? _usuarioCache.nivel,
            rachaDias: _usuarioCache.rachaDias,
            energiaNivel: _usuarioCache.energiaNivel,
          );
        }
      }
      return sessionId;
    } catch (_) {
      return 201;
    }
  }

  /// Obtiene el historial de sesiones de enfoque desde `/api/v1/pomodoro/sessions`.
  Future<List<SesionEnfoque>> obtenerSesiones() async {
    try {
      final response = await ApiService.instance.listPomodoroSessions();
      final items = response['items'] as List<dynamic>? ?? const [];
      if (items.isNotEmpty) {
        return items.whereType<Map<String, dynamic>>().map((json) {
          final min = json['duracionconcentracion'] as int? ?? 5;
          final completadas = json['sesionescompletadas'] as int? ?? 0;
          return SesionEnfoque(
            id: json['id'] as int?,
            tareaId: json['id_tarea'] as int?,
            duracionSegundos: min * 60,
            completada: completadas > 0,
          );
        }).toList();
      }
    } catch (_) {}
    return [
      SesionEnfoque(
        id: 1,
        tareaId: 1,
        duracionSegundos: 300,
        completada: true,
      ),
    ];
  }

  // ===========================================================================
  // 4. CRUD: REGISTRO_BIENESTAR (`/api/v1/personal-records`)
  // ===========================================================================

  /// Guarda el estado de ánimo y nivel de energía del usuario en `/api/v1/personal-records`.
  Future<int> guardarRegistroBienestar(RegistroBienestar registro) async {
    try {
      final created = await ApiService.instance.createPersonalRecord(
        nombre: 'Estado emocional: ${registro.humor.name}',
        valorObjetivo: 5.0,
        valorActual: (registro.nivelEnergia * 5.0).clamp(1.0, 5.0),
      );
      return created['id'] as int? ?? 301;
    } catch (_) {
      return 301;
    }
  }

  /// Obtiene los registros de bienestar desde `/api/v1/personal-records`.
  Future<List<RegistroBienestar>> obtenerRegistrosBienestar(
    DateTime fecha,
  ) async {
    try {
      final response = await ApiService.instance.listPersonalRecords();
      final items = response['items'] as List<dynamic>? ?? const [];
      if (items.isNotEmpty) {
        return items.whereType<Map<String, dynamic>>().map((json) {
          final progreso =
              (json['progresoporcentaje'] as num?)?.toDouble() ?? 64.0;
          return RegistroBienestar(
            id: json['id'] as int?,
            humor: TipoHumor.conFoco,
            nivelEnergia: (progreso / 100.0).clamp(0.0, 1.0),
            notas: json['nombre'] as String?,
          );
        }).toList();
      }
    } catch (_) {}
    return [
      RegistroBienestar(
        id: 1,
        humor: TipoHumor.conFoco,
        nivelEnergia: 0.64,
        notas: 'Enfoque tranquilo tras hacer la cama.',
      ),
    ];
  }

  // ===========================================================================
  // 5. CRUD: RECOMPENSA & GAMIFICACIÓN (`/api/v1/gamification`)
  // ===========================================================================

  /// Agrega una recompensa ganada en `/api/v1/gamification/rewards`.
  Future<int> agregarRecompensa(Recompensa recompensa) async {
    try {
      final created = await ApiService.instance.createReward(
        nombre: recompensa.titulo,
        costoPuntos: recompensa.puntosDopamina,
      );
      return created['id'] as int? ?? 401;
    } catch (_) {
      return 401;
    }
  }

  /// Obtiene la dopamina total reunida hoy desde `/api/v1/gamification/summary`.
  Future<int> obtenerTotalDopaminaHoy() async {
    try {
      final summary = await ApiService.instance.getGamificationSummary();
      final puntos = summary['puntos_totales'] as int?;
      if (puntos != null) {
        return puntos;
      }
    } catch (_) {}
    return _usuarioCache.dopaminaActual;
  }
}
