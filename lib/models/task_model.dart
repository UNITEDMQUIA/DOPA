enum EstadoTarea { ahora, despues, hecho }

class MicroPaso {
  final int? id;
  final int? tareaId;
  final String descripcion;
  bool completado;

  MicroPaso({
    this.id,
    this.tareaId,
    required this.descripcion,
    this.completado = false,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'tarea_id': tareaId,
      'descripcion': descripcion,
      'completado': completado ? 1 : 0,
    };
  }

  factory MicroPaso.fromMap(Map<String, dynamic> map) {
    return MicroPaso(
      id: map['id'] as int?,
      tareaId: map['tarea_id'] as int?,
      descripcion: map['descripcion'] as String,
      completado: (map['completado'] as int? ?? 0) == 1,
    );
  }
}

/// Modelo de entidad 'Tarea_Bloque' para el CRUD local.
class TareaBloque {
  final int? id;
  final String titulo;
  final String subtitulo;
  final int duracionMinutos;
  final EstadoTarea estado;
  final int puntosDopamina;
  final double estresNivel; // 0.0 (bajito) a 1.0 (alto)
  final List<MicroPaso> microPasos;

  TareaBloque({
    this.id,
    required this.titulo,
    required this.subtitulo,
    required this.duracionMinutos,
    this.estado = EstadoTarea.despues,
    this.puntosDopamina = 5,
    this.estresNivel = 0.2,
    this.microPasos = const [],
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'titulo': titulo,
      'subtitulo': subtitulo,
      'duracion_minutos': duracionMinutos,
      'estado': estado.name,
      'puntos_dopamina': puntosDopamina,
      'estres_nivel': estresNivel,
    };
  }

  factory TareaBloque.fromMap(Map<String, dynamic> map, {List<MicroPaso> pasos = const []}) {
    return TareaBloque(
      id: map['id'] as int?,
      titulo: map['titulo'] as String,
      subtitulo: map['subtitulo'] as String? ?? '',
      duracionMinutos: map['duracion_minutos'] as int? ?? 5,
      estado: EstadoTarea.values.firstWhere(
        (e) => e.name == map['estado'],
        orElse: () => EstadoTarea.despues,
      ),
      puntosDopamina: map['puntos_dopamina'] as int? ?? 5,
      estresNivel: (map['estres_nivel'] as num?)?.toDouble() ?? 0.2,
      microPasos: pasos,
    );
  }
}
