/// Modelo que representa la entidad 'Usuario' para la base de datos local y la app.
class Usuario {
  final int? id;
  final String nombre;
  final int dopaminaActual;
  final int dopaminaMeta;
  final int rachaDias;
  final double energiaNivel; // 0.0 (poquita) a 1.0 (a tope)

  Usuario({
    this.id,
    required this.nombre,
    this.dopaminaActual = 32,
    this.dopaminaMeta = 50,
    this.rachaDias = 4,
    this.energiaNivel = 0.45,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'nombre': nombre,
      'dopamina_actual': dopaminaActual,
      'dopamina_meta': dopaminaMeta,
      'racha_dias': rachaDias,
      'energia_nivel': energiaNivel,
    };
  }

  factory Usuario.fromMap(Map<String, dynamic> map) {
    return Usuario(
      id: map['id'] as int?,
      nombre: map['nombre'] as String? ?? 'Fred',
      dopaminaActual: map['dopamina_actual'] as int? ?? 32,
      dopaminaMeta: map['dopamina_meta'] as int? ?? 50,
      rachaDias: map['racha_dias'] as int? ?? 4,
      energiaNivel: (map['energia_nivel'] as num?)?.toDouble() ?? 0.45,
    );
  }
}
