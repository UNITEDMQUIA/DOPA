/// Modelo de entidad 'Sesion_Enfoque' para registrar bloques Pomodoro o sesiones suaves.
class SesionEnfoque {
  final int? id;
  final int? tareaId;
  final int duracionSegundos;
  final bool completada;
  final DateTime fechaInicio;

  SesionEnfoque({
    this.id,
    this.tareaId,
    required this.duracionSegundos,
    this.completada = false,
    DateTime? fechaInicio,
  }) : fechaInicio = fechaInicio ?? DateTime.now();

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'tarea_id': tareaId,
      'duracion_segundos': duracionSegundos,
      'completada': completada ? 1 : 0,
      'fecha_inicio': fechaInicio.toIso8601String(),
    };
  }

  factory SesionEnfoque.fromMap(Map<String, dynamic> map) {
    return SesionEnfoque(
      id: map['id'] as int?,
      tareaId: map['tarea_id'] as int?,
      duracionSegundos: map['duracion_segundos'] as int? ?? 300,
      completada: (map['completada'] as int? ?? 0) == 1,
      fechaInicio: map['fecha_inicio'] != null
          ? DateTime.parse(map['fecha_inicio'] as String)
          : DateTime.now(),
    );
  }
}
