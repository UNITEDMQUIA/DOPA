import '../models/user_model.dart';
import '../models/task_model.dart';
import '../models/focus_session_model.dart';
import '../models/wellness_record_model.dart';
import '../models/reward_model.dart';

/// Servicio de Base de Datos Local (SQLite).
///
/// Prepara la interfaz y métodos CRUD para persistir datos locales utilizando
/// el paquete 'sqflite'.
///
/// NOTA DE ARQUITECTURA:
/// Actualmente contiene implementaciones simuladas (Mock In-Memory) listas
/// para ser reemplazadas por consultas directas:
///   final db = await database;
///   db.query(...), db.insert(...), db.update(...), db.delete(...)
class DBService {
  static final DBService instance = DBService._init();
  DBService._init();

  // ===========================================================================
  // 1. CRUD: USUARIO
  // ===========================================================================

  /// Obtiene los datos del perfil del usuario (nombre, nivel de dopamina, racha actual).
  /// Reemplazar con: `await db.query('usuarios', limit: 1)`
  Future<Usuario> getUsuario() async {
    await Future.delayed(const Duration(milliseconds: 150));
    return Usuario(
      id: 1,
      nombre: 'Fred',
      dopaminaActual: 32,
      dopaminaMeta: 50,
      rachaDias: 4,
      energiaNivel: 0.45,
    );
  }

  /// Actualiza métricas o estado del usuario.
  /// Reemplazar con: `await db.update('usuarios', usuario.toMap(), where: 'id = ?', whereArgs: [usuario.id])`
  Future<int> updateUsuario(Usuario usuario) async {
    await Future.delayed(const Duration(milliseconds: 100));
    // SQL: UPDATE usuarios SET ... WHERE id = ?
    return 1;
  }

  // ===========================================================================
  // 2. CRUD: TAREA_BLOQUE & MICRO_PASOS
  // ===========================================================================

  /// Inserta una nueva micro-tarea en SQLite.
  /// Reemplazar con: `await db.insert('tareas_bloque', tarea.toMap())`
  Future<int> insertarTarea(TareaBloque tarea) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return 101; // ID simulado
  }

  /// Obtiene la lista de tareas del día.
  /// Reemplazar con: `await db.query('tareas_bloque', orderBy: 'estado ASC, id ASC')`
  Future<List<TareaBloque>> obtenerTareas() async {
    await Future.delayed(const Duration(milliseconds: 200));
    return [
      TareaBloque(
        id: 1,
        titulo: 'Hacer la cama',
        subtitulo: 'Fácil · 2 micro-pasos · 5 min',
        duracionMinutos: 5,
        estado: EstadoTarea.ahora,
        puntosDopamina: 10,
        estresNivel: 0.1,
        microPasos: [
          MicroPaso(id: 1, tareaId: 1, descripcion: 'Estirar las sábanas', completado: true),
          MicroPaso(id: 2, tareaId: 1, descripcion: 'Colocar almohadas', completado: false),
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
          MicroPaso(id: 3, tareaId: 2, descripcion: 'Abrir el chat', completado: false),
          MicroPaso(id: 4, tareaId: 2, descripcion: 'Enviar audio o texto corto', completado: false),
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
  }

  /// Actualiza el estado o datos de una tarea.
  /// Reemplazar con: `await db.update('tareas_bloque', tarea.toMap(), where: 'id = ?', whereArgs: [tarea.id])`
  Future<int> actualizarTarea(TareaBloque tarea) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return 1;
  }

  /// Elimina una tarea por ID.
  /// Reemplazar con: `await db.delete('tareas_bloque', where: 'id = ?', whereArgs: [id])`
  Future<int> eliminarTarea(int id) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return 1;
  }

  // ===========================================================================
  // 3. CRUD: SESION_ENFOQUE (Pomodoro / Temporizador)
  // ===========================================================================

  /// Registra una sesión de enfoque suave completada o pausada.
  /// Reemplazar con: `await db.insert('sesiones_enfoque', sesion.toMap())`
  Future<int> registrarSesion(SesionEnfoque sesion) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return 201;
  }

  /// Obtiene el historial de sesiones de enfoque de una fecha o rango.
  /// Reemplazar con: `await db.query('sesiones_enfoque', where: 'fecha_inicio LIKE ?', whereArgs: ['...%'])`
  Future<List<SesionEnfoque>> obtenerSesiones() async {
    await Future.delayed(const Duration(milliseconds: 150));
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
  // 4. CRUD: REGISTRO_BIENESTAR (Diario / Humor / Energía)
  // ===========================================================================

  /// Guarda el estado de ánimo y nivel de energía del usuario en la base de datos local.
  /// Reemplazar con: `await db.insert('registros_bienestar', registro.toMap())`
  Future<int> guardarRegistroBienestar(RegistroBienestar registro) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return 301;
  }

  /// Obtiene los registros de bienestar del día o semana.
  /// Reemplazar con: `await db.query('registros_bienestar', orderBy: 'fecha DESC')`
  Future<List<RegistroBienestar>> obtenerRegistrosBienestar(DateTime fecha) async {
    await Future.delayed(const Duration(milliseconds: 150));
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
  // 5. CRUD: RECOMPENSA (Gamificación / Dopamina acumulada)
  // ===========================================================================

  /// Agrega una recompensa ganada al completar tareas o pausas.
  /// Reemplazar con: `await db.insert('recompensas', recompensa.toMap())`
  Future<int> agregarRecompensa(Recompensa recompensa) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return 401;
  }

  /// Calcula la dopamina total reunida hoy.
  /// Reemplazar con: `SELECT SUM(puntos_dopamina) FROM recompensas WHERE fecha_obtenida LIKE ?`
  Future<int> obtenerTotalDopaminaHoy() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return 32; // Conforme a la pantalla de la imagen
  }
}
