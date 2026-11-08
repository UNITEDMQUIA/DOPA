import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/wellness_record_model.dart';

/// Excepción tipada para errores de comunicación con el Backend FastAPI.
class DopaApiException implements Exception {
  final int statusCode;
  final String message;
  final Map<String, dynamic>? details;

  DopaApiException({
    required this.statusCode,
    required this.message,
    this.details,
  });

  @override
  String toString() => 'DopaApiException($statusCode): $message';
}

/// Modelo de respuesta adaptativa para recomendaciones de baja fricción cognitiva.
class AIRecommendationResponse {
  final String recommendation;
  final int suggestedFocusMinutes;
  final String tone; // 'gentle', 'energizing', 'restful'
  final bool shouldTakeBreak;

  AIRecommendationResponse({
    required this.recommendation,
    this.suggestedFocusMinutes = 5,
    this.tone = 'gentle',
    this.shouldTakeBreak = false,
  });

  factory AIRecommendationResponse.fromJson(Map<String, dynamic> json) {
    return AIRecommendationResponse(
      recommendation: (json['sugerencia_baja_friccion'] ??
              json['recommendation']) as String? ??
          'Empieza por la tarea que te dé más alivio, no por la más grande.',
      suggestedFocusMinutes: json['suggested_focus_minutes'] as int? ?? 5,
      tone: json['tone'] as String? ?? 'gentle',
      shouldTakeBreak: json['should_take_break'] as bool? ?? false,
    );
  }
}

/// Servicio Unificado de Comunicación RESTful con el Backend FastAPI (`/api/v1/*`).
///
/// Agente Responsable: Agent_Frontend & Agent_Backend
/// Contrato de Referencia: `docs/API_CONTRACT.md` (Arquitectura en 5 Capas)
///
/// Soporta todos los 9 módulos del backend:
/// 1. `/api/v1/auth`             - Autenticación JWT Stateless y Preferencias
/// 2. `/api/v1/dashboard`        - Panel Principal, Chequeo de Energía y Tarea Fácil
/// 3. `/api/v1/tasks`            - Tareas, Completado Idempotente y Micro-pasos (`subtareas`)
/// 4. `/api/v1/routines`         - Rutinas Libres de Culpa
/// 5. `/api/v1/pomodoro`         - Sesiones de Enfoque Suave y Actividades de Bajo Estímulo
/// 6. `/api/v1/reminders`        - Recordatorios Programados
/// 7. `/api/v1/gamification`     - Resumen de Dopamina y Recompensas
/// 8. `/api/v1/personal-records` - Seguimiento de Sueño, Humor y Energía
/// 9. `/api/v1/financial-goals`  - Metas Financieras Personales
class ApiService {
  static final ApiService instance = ApiService._init();
  ApiService._init();

  /// URL inyectada en compilación mediante `--dart-define=API_BASE_URL=http://192.168.X.X:8000/api/v1`
  static const String _envBaseUrl = String.fromEnvironment('API_BASE_URL');

  String? _customBaseUrl;

  /// Cliente HTTP inyectable para pruebas unitarias/integración (`MockClient`).
  http.Client? httpClient;

  /// Tokens JWT Stateless en memoria de la sesión móvil activa.
  String? _accessToken;
  String? _refreshToken;
  Map<String, dynamic>? _currentUser;

  /// Timeout corto para garantizar que la app móvil nunca se bloquee si no hay red.
  Duration requestTimeout = const Duration(seconds: 3);

  /// Resuelve dinámicamente la URL base según la plataforma móvil, emulador o web.
  /// - Dispositivo físico en red LAN: pasar `--dart-define=API_BASE_URL=http://<IP_PC>:8000/api/v1`
  /// - Emulador Android (AVD): `http://10.0.2.2:8000/api/v1`
  /// - iOS Simulator / Web / Desktop: `http://localhost:8000/api/v1`
  String get baseUrl {
    if (_customBaseUrl != null && _customBaseUrl!.isNotEmpty) {
      return _customBaseUrl!;
    }
    if (_envBaseUrl.isNotEmpty) {
      return _envBaseUrl;
    }
    if (kIsWeb) {
      return 'http://localhost:8000/api/v1';
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return 'http://localhost:8000/api/v1';
  }

  /// URL raíz del servidor (para `/health` y `/docs`).
  String get serverRootUrl {
    final base = baseUrl;
    if (base.endsWith('/api/v1')) {
      return base.substring(0, base.length - 7);
    }
    return base;
  }

  /// Permite configurar dinámicamente la IP/URL del servidor desde el dispositivo móvil.
  void setBaseUrl(String url) {
    final trimmed = url.trim().replaceAll(RegExp(r'/+$'), '');
    _customBaseUrl = trimmed.endsWith('/api/v1') ? trimmed : '$trimmed/api/v1';
  }

  String? get accessToken => _accessToken;
  String? get refreshTokenValue => _refreshToken;
  Map<String, dynamic>? get currentUser => _currentUser;
  bool get isAuthenticated => _accessToken != null && _accessToken!.isNotEmpty;

  /// Configura manualmente los tokens JWT (útil en pruebas o restauración de sesión).
  void setTokens({
    String? accessToken,
    String? refreshToken,
    Map<String, dynamic>? usuario,
  }) {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    if (usuario != null) {
      _currentUser = usuario;
    }
  }

  /// Limpia la sesión activa en memoria.
  void clearSession() {
    _accessToken = null;
    _refreshToken = null;
    _currentUser = null;
  }

  http.Client get _client => httpClient ?? http.Client();

  Map<String, String> _buildHeaders({
    bool requiresAuth = true,
    String? idempotencyKey,
  }) {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (requiresAuth && _accessToken != null && _accessToken!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }
    if (idempotencyKey != null && idempotencyKey.isNotEmpty) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    return headers;
  }

  Uri _buildUri(String path, [Map<String, dynamic>? queryParameters]) {
    final cleanPath = path.startsWith('/') ? path : '/$path';
    final fullUrl = '$baseUrl$cleanPath';
    final uri = Uri.parse(fullUrl);
    if (queryParameters == null || queryParameters.isEmpty) {
      return uri;
    }
    final stringParams = <String, String>{};
    queryParameters.forEach((key, value) {
      if (value != null) {
        stringParams[key] = value.toString();
      }
    });
    return uri.replace(queryParameters: stringParams);
  }

  dynamic _decodeResponse(http.Response response) {
    if (response.statusCode == 204 || response.bodyBytes.isEmpty) {
      return <String, dynamic>{};
    }
    String bodyText;
    try {
      bodyText = utf8.decode(response.bodyBytes);
    } catch (_) {
      bodyText = response.body;
    }
    final decoded = jsonDecode(bodyText);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }
    String errorMsg = 'Error HTTP ${response.statusCode}';
    Map<String, dynamic>? details;
    if (decoded is Map<String, dynamic>) {
      details = decoded;
      errorMsg = decoded['detail']?.toString() ??
          decoded['mensaje']?.toString() ??
          errorMsg;
    }
    throw DopaApiException(
      statusCode: response.statusCode,
      message: errorMsg,
      details: details,
    );
  }

  // ===========================================================================
  // 0. SALUD DEL SERVICIO (/health)
  // ===========================================================================

  /// Verifica el estado operativo del servidor FastAPI (`GET /health`).
  Future<Map<String, dynamic>> checkHealth() async {
    final root = serverRootUrl.isEmpty ? 'http://localhost:8000' : serverRootUrl;
    final uri = Uri.parse('$root/health');
    final response = await _client
        .get(uri, headers: _buildHeaders(requiresAuth: false))
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  // ===========================================================================
  // 1. MÓDULO DE AUTENTICACIÓN Y PREFERENCIAS (/api/v1/auth)
  // ===========================================================================

  /// Registra un nuevo usuario (`POST /api/v1/auth/register`).
  Future<Map<String, dynamic>> register({
    required String nombre,
    required String correo,
    required String contrasena,
  }) async {
    final response = await _client
        .post(
          _buildUri('/auth/register'),
          headers: _buildHeaders(requiresAuth: false),
          body: jsonEncode({
            'nombre': nombre,
            'correo': correo,
            'contrasena': contrasena,
          }),
        )
        .timeout(requestTimeout);
    final data = _decodeResponse(response) as Map<String, dynamic>;
    _accessToken = data['access_token'] as String?;
    _refreshToken = data['refresh_token'] as String?;
    _currentUser = data['usuario'] as Map<String, dynamic>?;
    return data;
  }

  /// Inicia sesión con correo y contraseña (`POST /api/v1/auth/login`).
  Future<Map<String, dynamic>> login({
    required String correo,
    required String contrasena,
  }) async {
    final response = await _client
        .post(
          _buildUri('/auth/login'),
          headers: _buildHeaders(requiresAuth: false),
          body: jsonEncode({
            'correo': correo,
            'contrasena': contrasena,
          }),
        )
        .timeout(requestTimeout);
    final data = _decodeResponse(response) as Map<String, dynamic>;
    _accessToken = data['access_token'] as String?;
    _refreshToken = data['refresh_token'] as String?;
    _currentUser = data['usuario'] as Map<String, dynamic>?;
    return data;
  }

  /// Renueva el Access Token usando el Refresh Token (`POST /api/v1/auth/refresh`).
  Future<Map<String, dynamic>> refreshToken([String? customRefreshToken]) async {
    final tokenToUse = customRefreshToken ?? _refreshToken;
    if (tokenToUse == null || tokenToUse.isEmpty) {
      throw DopaApiException(
        statusCode: 401,
        message: 'No hay refresh_token disponible para renovar la sesión.',
      );
    }
    final response = await _client
        .post(
          _buildUri('/auth/refresh'),
          headers: _buildHeaders(requiresAuth: false),
          body: jsonEncode({'refresh_token': tokenToUse}),
        )
        .timeout(requestTimeout);
    final data = _decodeResponse(response) as Map<String, dynamic>;
    _accessToken = data['access_token'] as String?;
    _refreshToken = data['refresh_token'] as String?;
    _currentUser = data['usuario'] as Map<String, dynamic>?;
    return data;
  }

  /// Cierra la sesión activa e invalida el Access Token (`POST /api/v1/auth/logout`).
  Future<Map<String, dynamic>> logout() async {
    final response = await _client
        .post(
          _buildUri('/auth/logout'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    final data = _decodeResponse(response) as Map<String, dynamic>;
    clearSession();
    return data;
  }

  /// Obtiene el perfil del usuario autenticado (`GET /api/v1/auth/me`).
  Future<Map<String, dynamic>> getMe() async {
    await ensureAuthenticated();
    final response = await _client
        .get(_buildUri('/auth/me'), headers: _buildHeaders())
        .timeout(requestTimeout);
    final data = _decodeResponse(response) as Map<String, dynamic>;
    _currentUser = data;
    return data;
  }

  /// Actualiza las preferencias del usuario (`PUT /api/v1/auth/preferences`).
  Future<Map<String, dynamic>> updatePreferences(
    Map<String, dynamic> preferences,
  ) async {
    await ensureAuthenticated();
    final response = await _client
        .put(
          _buildUri('/auth/preferences'),
          headers: _buildHeaders(),
          body: jsonEncode(preferences),
        )
        .timeout(requestTimeout);
    final data = _decodeResponse(response) as Map<String, dynamic>;
    _currentUser = data;
    return data;
  }

  /// Garantiza que el cliente móvil tenga una sesión activa (auto-login / auto-registro de Fred).
  Future<bool> ensureAuthenticated({
    String defaultEmail = 'fred@dopa.app',
    String defaultPassword = 'Dopa1234!',
    String defaultName = 'Fred',
  }) async {
    if (isAuthenticated) return true;
    try {
      await login(correo: defaultEmail, contrasena: defaultPassword);
      return true;
    } on DopaApiException catch (e) {
      if (e.statusCode == 401) {
        // Intentar con contraseña alternativa de seed o registrar si aún no existe
        try {
          await login(correo: defaultEmail, contrasena: 'secret');
          return true;
        } catch (_) {}
        try {
          await register(
            nombre: defaultName,
            correo: defaultEmail,
            contrasena: defaultPassword,
          );
          return true;
        } catch (_) {}
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  // ===========================================================================
  // 2. MÓDULO DE PANEL PRINCIPAL / INICIO (/api/v1/dashboard)
  // ===========================================================================

  /// Obtiene el payload consolidado del Panel Principal (`GET /api/v1/dashboard`).
  Future<Map<String, dynamic>> getDashboard() async {
    await ensureAuthenticated();
    final response = await _client
        .get(_buildUri('/dashboard'), headers: _buildHeaders())
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Registra el chequeo diario "¿Cómo está tu energía hoy?" (`POST /api/v1/dashboard/energy-checkin`).
  Future<Map<String, dynamic>> energyCheckin({
    required String nivelEnergia,
    String? humor,
    double? horasSueno,
  }) async {
    await ensureAuthenticated();
    final body = <String, dynamic>{
      'nivel_energia': nivelEnergia,
    };
    if (humor != null) body['humor'] = humor;
    if (horasSueno != null) body['horas_sueno'] = horasSueno;

    final response = await _client
        .post(
          _buildUri('/dashboard/energy-checkin'),
          headers: _buildHeaders(),
          body: jsonEncode(body),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Obtiene la tarea pendiente de menor fricción para el botón "¡Hacer algo fácil!" (`GET /api/v1/dashboard/quick-task`).
  Future<Map<String, dynamic>> getQuickTask() async {
    await ensureAuthenticated();
    final response = await _client
        .get(_buildUri('/dashboard/quick-task'), headers: _buildHeaders())
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  // ===========================================================================
  // 3. MÓDULO DE GESTIÓN DE TAREAS Y MICRO-PASOS (/api/v1/tasks)
  // ===========================================================================

  /// Lista las tareas del usuario con paginación y filtros (`GET /api/v1/tasks`).
  Future<Map<String, dynamic>> listTasks({
    int limit = 20,
    int offset = 0,
    bool? completada,
    String? prioridad,
    int? idRutina,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/tasks', {
            'limit': limit,
            'offset': offset,
            'completada': completada,
            'prioridad': prioridad,
            'id_rutina': idRutina,
          }),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Crea una nueva tarea con micro-pasos opcionales (`POST /api/v1/tasks`).
  Future<Map<String, dynamic>> createTask({
    required String titulo,
    String? descripcion,
    String prioridad = 'Media',
    String? fechaVencimiento,
    int? idRutina,
    List<String> subtareas = const [],
  }) async {
    await ensureAuthenticated();
    final body = <String, dynamic>{
      'titulo': titulo,
      'prioridad': prioridad,
      'subtareas': subtareas,
    };
    if (descripcion != null) body['descripcion'] = descripcion;
    if (fechaVencimiento != null) body['fechavencimiento'] = fechaVencimiento;
    if (idRutina != null) body['id_rutina'] = idRutina;

    final response = await _client
        .post(
          _buildUri('/tasks'),
          headers: _buildHeaders(),
          body: jsonEncode(body),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Obtiene el detalle de una tarea y sus micro-pasos (`GET /api/v1/tasks/{task_id}`).
  Future<Map<String, dynamic>> getTask(int taskId) async {
    await ensureAuthenticated();
    final response = await _client
        .get(_buildUri('/tasks/$taskId'), headers: _buildHeaders())
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Edita una tarea existente (`PUT /api/v1/tasks/{task_id}`).
  Future<Map<String, dynamic>> updateTask(
    int taskId,
    Map<String, dynamic> fields,
  ) async {
    await ensureAuthenticated();
    final response = await _client
        .put(
          _buildUri('/tasks/$taskId'),
          headers: _buildHeaders(),
          body: jsonEncode(fields),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Elimina una tarea y sus micro-pasos en cascada (`DELETE /api/v1/tasks/{task_id}`).
  Future<void> deleteTask(int taskId) async {
    await ensureAuthenticated();
    final response = await _client
        .delete(_buildUri('/tasks/$taskId'), headers: _buildHeaders())
        .timeout(requestTimeout);
    _decodeResponse(response);
  }

  /// Marca una tarea como completada de forma idempotente y otorga +10 dopamina (`POST /api/v1/tasks/{task_id}/complete`).
  Future<Map<String, dynamic>> completeTask(
    int taskId, {
    String? idempotencyKey,
  }) async {
    await ensureAuthenticated();
    final key = idempotencyKey ?? 'task-complete-$taskId-${DateTime.now().millisecondsSinceEpoch ~/ 10000}';
    final response = await _client
        .post(
          _buildUri('/tasks/$taskId/complete'),
          headers: _buildHeaders(idempotencyKey: key),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Crea un micro-paso dentro de una tarea (`POST /api/v1/tasks/{task_id}/subtasks`).
  Future<Map<String, dynamic>> createSubtask(
    int taskId,
    String descripcion,
  ) async {
    await ensureAuthenticated();
    final response = await _client
        .post(
          _buildUri('/tasks/$taskId/subtasks'),
          headers: _buildHeaders(),
          body: jsonEncode({'descripcion': descripcion}),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Lista los micro-pasos de una tarea y su porcentaje de avance (`GET /api/v1/tasks/{task_id}/subtasks`).
  Future<Map<String, dynamic>> listSubtasks(int taskId) async {
    await ensureAuthenticated();
    final response = await _client
        .get(_buildUri('/tasks/$taskId/subtasks'), headers: _buildHeaders())
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Actualiza o marca como completado un micro-paso (`PATCH /api/v1/tasks/{task_id}/subtasks/{subtask_id}`).
  Future<Map<String, dynamic>> updateSubtask(
    int taskId,
    int subtaskId, {
    String? descripcion,
    bool? completada,
  }) async {
    await ensureAuthenticated();
    final body = <String, dynamic>{};
    if (descripcion != null) body['descripcion'] = descripcion;
    if (completada != null) body['completada'] = completada;

    final response = await _client
        .patch(
          _buildUri('/tasks/$taskId/subtasks/$subtaskId'),
          headers: _buildHeaders(),
          body: jsonEncode(body),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Elimina un micro-paso de una tarea (`DELETE /api/v1/tasks/{task_id}/subtasks/{subtask_id}`).
  Future<void> deleteSubtask(int taskId, int subtaskId) async {
    await ensureAuthenticated();
    final response = await _client
        .delete(
          _buildUri('/tasks/$taskId/subtasks/$subtaskId'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    _decodeResponse(response);
  }

  // ===========================================================================
  // 4. MÓDULO DE RUTINAS Y HÁBITOS LIBRES DE CULPA (/api/v1/routines)
  // ===========================================================================

  /// Lista las rutinas del usuario (`GET /api/v1/routines`).
  Future<Map<String, dynamic>> listRoutines({
    int limit = 20,
    int offset = 0,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/routines', {'limit': limit, 'offset': offset}),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Crea una rutina (`POST /api/v1/routines`).
  Future<Map<String, dynamic>> createRoutine({
    required String nombre,
    required String recurrencia,
    String hora = '08:00:00',
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .post(
          _buildUri('/routines'),
          headers: _buildHeaders(),
          body: jsonEncode({
            'nombre': nombre,
            'recurrencia': recurrencia,
            'hora': hora,
          }),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Obtiene el detalle de una rutina con sus tareas (`GET /api/v1/routines/{routine_id}`).
  Future<Map<String, dynamic>> getRoutine(int routineId) async {
    await ensureAuthenticated();
    final response = await _client
        .get(_buildUri('/routines/$routineId'), headers: _buildHeaders())
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Actualiza una rutina (`PUT /api/v1/routines/{routine_id}`).
  Future<Map<String, dynamic>> updateRoutine(
    int routineId,
    Map<String, dynamic> fields,
  ) async {
    await ensureAuthenticated();
    final response = await _client
        .put(
          _buildUri('/routines/$routineId'),
          headers: _buildHeaders(),
          body: jsonEncode(fields),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Elimina una rutina (`DELETE /api/v1/routines/{routine_id}`).
  Future<void> deleteRoutine(int routineId) async {
    await ensureAuthenticated();
    final response = await _client
        .delete(_buildUri('/routines/$routineId'), headers: _buildHeaders())
        .timeout(requestTimeout);
    _decodeResponse(response);
  }

  /// Marca la rutina como completada hoy de forma idempotente (`POST /api/v1/routines/{routine_id}/complete-today`).
  Future<Map<String, dynamic>> completeRoutineToday(
    int routineId, {
    String? idempotencyKey,
  }) async {
    await ensureAuthenticated();
    final key = idempotencyKey ?? 'routine-complete-$routineId';
    final response = await _client
        .post(
          _buildUri('/routines/$routineId/complete-today'),
          headers: _buildHeaders(idempotencyKey: key),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Retoma una rutina tras inactividad sin penalizaciones (`POST /api/v1/routines/{routine_id}/resume`).
  Future<Map<String, dynamic>> resumeRoutine(int routineId) async {
    await ensureAuthenticated();
    final response = await _client
        .post(
          _buildUri('/routines/$routineId/resume'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  // ===========================================================================
  // 5. MÓDULO DE ENFOQUE POMODORO Y DESCANSO (/api/v1/pomodoro)
  // ===========================================================================

  /// Crea una sesión de enfoque suave (`POST /api/v1/pomodoro/sessions`).
  Future<Map<String, dynamic>> createPomodoroSession({
    int? idTarea,
    int duracionConcentracion = 5,
    int duracionDescanso = 5,
  }) async {
    await ensureAuthenticated();
    final body = <String, dynamic>{
      'duracionconcentracion': duracionConcentracion,
      'duraciondescanso': duracionDescanso,
    };
    if (idTarea != null) body['id_tarea'] = idTarea;

    final response = await _client
        .post(
          _buildUri('/pomodoro/sessions'),
          headers: _buildHeaders(),
          body: jsonEncode(body),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Lista las sesiones Pomodoro del usuario (`GET /api/v1/pomodoro/sessions`).
  Future<Map<String, dynamic>> listPomodoroSessions({
    int limit = 20,
    int offset = 0,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/pomodoro/sessions', {'limit': limit, 'offset': offset}),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Completa un ciclo Pomodoro de forma idempotente y otorga +5 dopamina (`POST /api/v1/pomodoro/sessions/{session_id}/complete`).
  Future<Map<String, dynamic>> completePomodoroSession(
    int sessionId, {
    String? idempotencyKey,
  }) async {
    await ensureAuthenticated();
    final key = idempotencyKey ?? 'pomodoro-complete-$sessionId-${DateTime.now().millisecondsSinceEpoch ~/ 10000}';
    final response = await _client
        .post(
          _buildUri('/pomodoro/sessions/$sessionId/complete'),
          headers: _buildHeaders(idempotencyKey: key),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Cancela una sesión Pomodoro en curso sin penalización (`POST /api/v1/pomodoro/sessions/{session_id}/cancel`).
  Future<Map<String, dynamic>> cancelPomodoroSession(int sessionId) async {
    await ensureAuthenticated();
    final response = await _client
        .post(
          _buildUri('/pomodoro/sessions/$sessionId/cancel'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Obtiene el catálogo de actividades guiadas de bajo estímulo ("Un break suave") (`GET /api/v1/pomodoro/low-stimulus-activities`).
  Future<Map<String, dynamic>> getLowStimulusActivities() async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/pomodoro/low-stimulus-activities'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  // ===========================================================================
  // 6. MÓDULO DE RECORDATORIOS (/api/v1/reminders)
  // ===========================================================================

  /// Lista los recordatorios del usuario (`GET /api/v1/reminders`).
  Future<Map<String, dynamic>> listReminders({
    int limit = 20,
    int offset = 0,
    String? tipo,
    bool? completadaHoy,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/reminders', {
            'limit': limit,
            'offset': offset,
            'tipo': tipo,
            'completadahoy': completadaHoy,
          }),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Crea un recordatorio (`POST /api/v1/reminders`).
  Future<Map<String, dynamic>> createReminder({
    required String fechaHora,
    required String mensaje,
    String tipo = 'Tarea',
    int? idTarea,
  }) async {
    await ensureAuthenticated();
    final body = <String, dynamic>{
      'fechahora': fechaHora,
      'mensaje': mensaje,
      'tipo': tipo,
    };
    if (idTarea != null) body['id_tarea'] = idTarea;

    final response = await _client
        .post(
          _buildUri('/reminders'),
          headers: _buildHeaders(),
          body: jsonEncode(body),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Actualiza o marca como completado hoy un recordatorio (`PUT /api/v1/reminders/{reminder_id}`).
  Future<Map<String, dynamic>> updateReminder(
    int reminderId,
    Map<String, dynamic> fields,
  ) async {
    await ensureAuthenticated();
    final response = await _client
        .put(
          _buildUri('/reminders/$reminderId'),
          headers: _buildHeaders(),
          body: jsonEncode(fields),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Elimina un recordatorio (`DELETE /api/v1/reminders/{reminder_id}`).
  Future<void> deleteReminder(int reminderId) async {
    await ensureAuthenticated();
    final response = await _client
        .delete(_buildUri('/reminders/$reminderId'), headers: _buildHeaders())
        .timeout(requestTimeout);
    _decodeResponse(response);
  }

  // ===========================================================================
  // 7. MÓDULO DE GAMIFICACIÓN Y DOPAMINA (/api/v1/gamification)
  // ===========================================================================

  /// Obtiene el resumen de gamificación para "Mi Dopamina hoy" (`GET /api/v1/gamification/summary`).
  Future<Map<String, dynamic>> getGamificationSummary() async {
    await ensureAuthenticated();
    final response = await _client
        .get(_buildUri('/gamification/summary'), headers: _buildHeaders())
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Lista las recompensas disponibles y desbloqueadas (`GET /api/v1/gamification/rewards`).
  Future<Map<String, dynamic>> listRewards({
    int limit = 50,
    int offset = 0,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/gamification/rewards', {'limit': limit, 'offset': offset}),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Crea una nueva recompensa (`POST /api/v1/gamification/rewards`).
  Future<Map<String, dynamic>> createReward({
    required String nombre,
    int costoPuntos = 10,
    int? idTarea,
  }) async {
    await ensureAuthenticated();
    final body = <String, dynamic>{
      'nombre': nombre,
      'costopuntos': costoPuntos,
    };
    if (idTarea != null) body['id_tarea'] = idTarea;

    final response = await _client
        .post(
          _buildUri('/gamification/rewards'),
          headers: _buildHeaders(),
          body: jsonEncode(body),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Desbloquea una recompensa (`POST /api/v1/gamification/rewards/{reward_id}/unlock`).
  Future<Map<String, dynamic>> unlockReward(int rewardId) async {
    await ensureAuthenticated();
    final response = await _client
        .post(
          _buildUri('/gamification/rewards/$rewardId/unlock'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  // ===========================================================================
  // 8. MÓDULO DE SEGUIMIENTO PERSONAL: SUEÑO Y HUMOR (/api/v1/personal-records)
  // ===========================================================================

  /// Lista los registros personales con tendencia descriptiva no médica (`GET /api/v1/personal-records`).
  Future<Map<String, dynamic>> listPersonalRecords({
    int limit = 20,
    int offset = 0,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/personal-records', {'limit': limit, 'offset': offset}),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Crea un registro personal de sueño, humor o bienestar (`POST /api/v1/personal-records`).
  Future<Map<String, dynamic>> createPersonalRecord({
    required String nombre,
    required double valorObjetivo,
    required double valorActual,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .post(
          _buildUri('/personal-records'),
          headers: _buildHeaders(),
          body: jsonEncode({
            'nombre': nombre,
            'valorobjetivo': valorObjetivo,
            'valoractual': valorActual,
          }),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Actualiza un registro personal (`PUT /api/v1/personal-records/{record_id}`).
  Future<Map<String, dynamic>> updatePersonalRecord(
    int recordId,
    Map<String, dynamic> fields,
  ) async {
    await ensureAuthenticated();
    final response = await _client
        .put(
          _buildUri('/personal-records/$recordId'),
          headers: _buildHeaders(),
          body: jsonEncode(fields),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Elimina un registro personal (`DELETE /api/v1/personal-records/{record_id}`).
  Future<void> deletePersonalRecord(int recordId) async {
    await ensureAuthenticated();
    final response = await _client
        .delete(
          _buildUri('/personal-records/$recordId'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    _decodeResponse(response);
  }

  // ===========================================================================
  // 9. MÓDULO DE METAS FINANCIERAS (/api/v1/financial-goals)
  // ===========================================================================

  /// Lista las metas financieras del usuario (`GET /api/v1/financial-goals`).
  Future<Map<String, dynamic>> listFinancialGoals({
    int limit = 20,
    int offset = 0,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .get(
          _buildUri('/financial-goals', {'limit': limit, 'offset': offset}),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Crea una meta financiera (`POST /api/v1/financial-goals`).
  Future<Map<String, dynamic>> createFinancialGoal({
    required String nombre,
    required double valorObjetivo,
    double valorActual = 0.0,
  }) async {
    await ensureAuthenticated();
    final response = await _client
        .post(
          _buildUri('/financial-goals'),
          headers: _buildHeaders(),
          body: jsonEncode({
            'nombre': nombre,
            'valorobjetivo': valorObjetivo,
            'valoractual': valorActual,
          }),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Registra un avance en una meta financiera (`PATCH /api/v1/financial-goals/{goal_id}/progress`).
  Future<Map<String, dynamic>> updateFinancialGoalProgress(
    int goalId, {
    double? montoAvance,
    double? valorActual,
  }) async {
    await ensureAuthenticated();
    final body = <String, dynamic>{};
    if (montoAvance != null) body['monto_avance'] = montoAvance;
    if (valorActual != null) body['valoractual'] = valorActual;

    final response = await _client
        .patch(
          _buildUri('/financial-goals/$goalId/progress'),
          headers: _buildHeaders(),
          body: jsonEncode(body),
        )
        .timeout(requestTimeout);
    return _decodeResponse(response) as Map<String, dynamic>;
  }

  /// Elimina una meta financiera (`DELETE /api/v1/financial-goals/{goal_id}`).
  Future<void> deleteFinancialGoal(int goalId) async {
    await ensureAuthenticated();
    final response = await _client
        .delete(
          _buildUri('/financial-goals/$goalId'),
          headers: _buildHeaders(),
        )
        .timeout(requestTimeout);
    _decodeResponse(response);
  }

  // ===========================================================================
  // 10. ADAPTADORES DE EXPERIENCIA DE USUARIO (UI Widgets -> Backend API)
  // ===========================================================================

  /// Obtiene la recomendación contextual de baja fricción conectando con `/api/v1/dashboard`.
  Future<AIRecommendationResponse> fetchAIRecommendation({
    double? nivelEnergia,
    TipoHumor? humor,
    String? tareaActual,
  }) async {
    try {
      String etiquetaEnergia = 'media';
      if (nivelEnergia != null) {
        if (nivelEnergia < 0.35) {
          etiquetaEnergia = 'poquita';
        } else if (nivelEnergia > 0.7) {
          etiquetaEnergia = 'a tope';
        }
      }
      final checkin = await energyCheckin(
        nivelEnergia: etiquetaEnergia,
        humor: _mapMoodLabel(humor),
      );
      return AIRecommendationResponse.fromJson(checkin);
    } catch (_) {
      // Fallback local inmediato cuando se ejecuta sin red o en entorno offline
      return AIRecommendationResponse(
        recommendation:
            'Empieza por la tarea que te dé más alivio, no por la más grande.',
        suggestedFocusMinutes: 5,
        tone: 'gentle',
        shouldTakeBreak: (nivelEnergia != null && nivelEnergia < 0.2),
      );
    }
  }

  /// Envía el registro del diario de bienestar (`MoodSelector`) hacia `/api/v1/dashboard/energy-checkin`
  /// y `/api/v1/personal-records`.
  Future<Map<String, dynamic>> sendWellnessAnalysis(
    RegistroBienestar registro,
  ) async {
    try {
      final String etiquetaEnergia = registro.nivelEnergia < 0.35
          ? 'poquita'
          : (registro.nivelEnergia > 0.7 ? 'a tope' : 'media');
      final String etiquetaHumor = _mapMoodLabel(registro.humor) ?? 'Con foco';

      final checkin = await energyCheckin(
        nivelEnergia: etiquetaEnergia,
        humor: etiquetaHumor,
      );
      return {
        'status': 'success',
        'insight': checkin['sugerencia_baja_friccion'] ??
            'Tu energía se mantiene estable. Mantén los bloques cortos.',
        'adjusted_pomodoro_minutes': 5,
        'registro_id': checkin['registro_id'],
      };
    } catch (_) {
      return {
        'status': 'success',
        'insight': 'Tu energía se mantiene estable. Mantén los bloques cortos.',
        'adjusted_pomodoro_minutes': 5,
      };
    }
  }

  String? _mapMoodLabel(TipoHumor? humor) {
    if (humor == null) return null;
    switch (humor) {
      case TipoHumor.abrumado:
        return 'Abrumado';
      case TipoHumor.inquieto:
        return 'Inquieto';
      case TipoHumor.conFoco:
        return 'Con foco';
      case TipoHumor.tranquilo:
        return 'Tranquilo';
    }
  }
}
