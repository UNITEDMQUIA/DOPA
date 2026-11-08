/// Modelo que representa la entidad 'Usuario' para la base de datos local y el backend FastAPI.
class Usuario {
  final int? id;
  final String nombre;
  final String correo;
  final int dopaminaActual;
  final int dopaminaMeta;
  final int nivel;
  final int rachaDias;
  final double energiaNivel; // 0.0 (poquita) a 1.0 (a tope)

  Usuario({
    this.id,
    required this.nombre,
    this.correo = 'fred@dopa.app',
    this.dopaminaActual = 32,
    this.dopaminaMeta = 50,
    this.nivel = 1,
    this.rachaDias = 4,
    this.energiaNivel = 0.45,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'nombre': nombre,
      'correo': correo,
      'dopamina_actual': dopaminaActual,
      'dopamina_meta': dopaminaMeta,
      'nivel': nivel,
      'racha_dias': rachaDias,
      'energia_nivel': energiaNivel,
    };
  }

  factory Usuario.fromMap(Map<String, dynamic> map) {
    return Usuario(
      id: map['id'] as int?,
      nombre: map['nombre'] as String? ?? 'Fred',
      correo: map['correo'] as String? ?? 'fred@dopa.app',
      dopaminaActual: (map['dopamina_actual'] ?? map['puntos']) as int? ?? 32,
      dopaminaMeta: (map['dopamina_meta'] ?? map['meta_diaria_puntos']) as int? ?? 50,
      nivel: map['nivel'] as int? ?? 1,
      rachaDias: map['racha_dias'] as int? ?? 4,
      energiaNivel: (map['energia_nivel'] as num?)?.toDouble() ?? 0.45,
    );
  }

  /// Construye un `Usuario` a partir de `UserResponseDTO` (`/api/v1/auth/me`) o `DashboardResponseDTO` (`/api/v1/dashboard`).
  factory Usuario.fromBackendJson(Map<String, dynamic> json) {
    final prefs = json['preferencias'] as Map<String, dynamic>?;
    final int meta = (json['meta_diaria_puntos'] as int?) ??
        (prefs?['meta_diaria_dopamina'] as int?) ??
        50;
    final int puntos =
        (json['puntos_dopamina'] ?? json['puntos']) as int? ?? 32;

    final String estadoEnergia =
        (json['estado_energia_hoy'] as String? ?? 'media').toLowerCase();
    double energia;
    if (estadoEnergia == 'poquita' || estadoEnergia == 'baja') {
      energia = 0.25;
    } else if (estadoEnergia == 'a tope' || estadoEnergia == 'alta') {
      energia = 0.85;
    } else {
      energia = 0.45;
    }

    String nombre = json['nombre'] as String? ?? 'Fred';
    if (json['saludo'] is String) {
      final saludo = json['saludo'] as String;
      final limpio = saludo.replaceAll('¡Hola,', '').replaceAll('!', '').trim();
      if (limpio.isNotEmpty) {
        nombre = limpio;
      }
    }

    return Usuario(
      id: (json['id'] ?? json['panel_id']) as int? ?? 1,
      nombre: nombre,
      correo: json['correo'] as String? ?? 'fred@dopa.app',
      dopaminaActual: puntos,
      dopaminaMeta: meta,
      nivel: json['nivel'] as int? ?? 1,
      rachaDias: json['dias_activos_registrados'] as int? ?? 4,
      energiaNivel: energia,
    );
  }
}
