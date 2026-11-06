/// Modelo de entidad 'Recompensa' (Motor de gamificación / dopamina y logros).
class Recompensa {
  final int? id;
  final String titulo;
  final int puntosDopamina;
  final DateTime fechaObtenida;
  final String tipo; // 'tarea', 'break', 'diario'

  Recompensa({
    this.id,
    required this.titulo,
    required this.puntosDopamina,
    DateTime? fechaObtenida,
    this.tipo = 'tarea',
  }) : fechaObtenida = fechaObtenida ?? DateTime.now();

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'titulo': titulo,
      'puntos_dopamina': puntosDopamina,
      'fecha_obtenida': fechaObtenida.toIso8601String(),
      'tipo': tipo,
    };
  }

  factory Recompensa.fromMap(Map<String, dynamic> map) {
    return Recompensa(
      id: map['id'] as int?,
      titulo: map['titulo'] as String,
      puntosDopamina: map['puntos_dopamina'] as int? ?? 10,
      fechaObtenida: map['fecha_obtenida'] != null
          ? DateTime.parse(map['fecha_obtenida'] as String)
          : DateTime.now(),
      tipo: map['tipo'] as String? ?? 'tarea',
    );
  }
}
