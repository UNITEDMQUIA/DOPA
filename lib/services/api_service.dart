import '../models/wellness_record_model.dart';

/// Modelo de respuesta del Agente de IA proveniente de FastAPI.
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
      recommendation: json['recommendation'] as String? ??
          'Empieza por la tarea que te dé más alivio, no por la más grande.',
      suggestedFocusMinutes: json['suggested_focus_minutes'] as int? ?? 5,
      tone: json['tone'] as String? ?? 'gentle',
      shouldTakeBreak: json['should_take_break'] as bool? ?? false,
    );
  }
}

/// Servicio de Comunicación con el Backend en Python (FastAPI) y el Agente de IA.
///
/// Prepara la integración futura con peticiones HTTP (`package:http` o `dio`).
/// Endpoints previstos en FastAPI:
/// - POST /api/v1/agent/recommendation
/// - POST /api/v1/wellness/analyze
/// - POST /api/v1/sync/push
class ApiService {
  static final ApiService instance = ApiService._init();
  ApiService._init();

  // URL base configurable para desarrollo local con FastAPI
  // En emulador Android: 'http://10.0.2.2:8000'
  // En iOS Simulator o Web: 'http://localhost:8000'
  final String baseUrl = 'http://10.0.2.2:8000/api/v1';

  /// Método asíncrono para obtener la recomendación contextual del Agente de IA.
  ///
  /// El agente analiza:
  /// - Nivel de energía del usuario (0.0 a 1.0)
  /// - Estado de humor reportado (abrumado, inquieto, etc.)
  /// - Historial reciente de tareas
  ///
  /// En producción, reemplázalo con:
  /// ```dart
  /// final response = await http.post(
  ///   Uri.parse('$baseUrl/agent/recommendation'),
  ///   headers: {'Content-Type': 'application/json'},
  ///   body: jsonEncode({
  ///     'energy_level': nivelEnergia,
  ///     'current_mood': humor?.name,
  ///   }),
  /// );
  /// return AIRecommendationResponse.fromJson(jsonDecode(response.body));
  /// ```
  Future<AIRecommendationResponse> fetchAIRecommendation({
    double? nivelEnergia,
    TipoHumor? humor,
    String? tareaActual,
  }) async {
    // Simulación de latencia de red hacia FastAPI
    await Future.delayed(const Duration(milliseconds: 300));

    // Lógica simulada del agente según la imagen de diseño
    return AIRecommendationResponse(
      recommendation: 'Empieza por la tarea que te dé más alivio, no por la más grande.',
      suggestedFocusMinutes: 5,
      tone: 'gentle',
      shouldTakeBreak: (nivelEnergia != null && nivelEnergia < 0.2),
    );
  }

  /// Envía datos del diario de bienestar al backend FastAPI para análisis cognitivo.
  /// Reemplazar con: `http.post('$baseUrl/wellness/analyze', body: jsonEncode(registro.toMap()))`
  Future<Map<String, dynamic>> sendWellnessAnalysis(RegistroBienestar registro) async {
    await Future.delayed(const Duration(milliseconds: 250));
    return {
      'status': 'success',
      'insight': 'Tu energía se mantiene estable. Mantén los bloques cortos.',
      'adjusted_pomodoro_minutes': 5,
    };
  }
}
