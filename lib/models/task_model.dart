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
    final rawCompletado = map['completado'] ?? map['completada'];
    final isCompletado = rawCompletado is bool
        ? rawCompletado
        : (rawCompletado as int? ?? 0) == 1;
    return MicroPaso(
      id: map['id'] as int?,
      tareaId: (map['tarea_id'] ?? map['id_tarea']) as int?,
      descripcion: map['descripcion'] as String? ?? '',
      completado: isCompletado,
    );
  }

  /// Convierte un `SubtaskResponseDTO` del backend FastAPI (`/api/v1/tasks`) a `MicroPaso`.
  factory MicroPaso.fromBackendJson(Map<String, dynamic> json) {
    return MicroPaso(
      id: json['id'] as int?,
      tareaId: (json['id_tarea'] ?? json['tarea_id']) as int?,
      descripcion: json['descripcion'] as String? ?? '',
      completado: json['completada'] == true || json['completado'] == true,
    );
  }
}

/// Modelo de entidad 'Tarea_Bloque' para el CRUD local y sincronización con FastAPI (`/api/v1/tasks`).
class TareaBloque {
  final int? id;
  final String titulo;
  final String subtitulo;
  final int duracionMinutos;
  final EstadoTarea estado;
  final int puntosDopamina;
  final double estresNivel; // 0.0 (bajito) a 1.0 (alto)
  final List<MicroPaso> microPasos;
  final String prioridad; // 'Baja', 'Media', 'Alta'

  TareaBloque({
    this.id,
    required this.titulo,
    required this.subtitulo,
    required this.duracionMinutos,
    this.estado = EstadoTarea.despues,
    this.puntosDopamina = 5,
    this.estresNivel = 0.2,
    this.microPasos = const [],
    this.prioridad = 'Media',
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
      'prioridad': prioridad,
    };
  }

  factory TareaBloque.fromMap(
    Map<String, dynamic> map, {
    List<MicroPaso> pasos = const [],
  }) {
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
      prioridad: map['prioridad'] as String? ?? 'Media',
    );
  }

  /// Convierte un `TaskResponseDTO` del backend FastAPI (`/api/v1/tasks`) a `TareaBloque`.
  factory TareaBloque.fromBackendJson(
    Map<String, dynamic> json, {
    bool isFirstPending = false,
  }) {
    final bool completada = json['completada'] == true;
    final String prioridad = json['prioridad'] as String? ?? 'Media';
    final String etiqueta = json['etiqueta_esfuerzo'] as String? ?? 'Suave';
    final int puntos = json['puntos_recompensa'] as int? ?? 10;

    final rawSubtareas = json['subtareas'] as List<dynamic>? ?? const [];
    final pasos = rawSubtareas
        .whereType<Map<String, dynamic>>()
        .map(MicroPaso.fromBackendJson)
        .toList();

    int duracion;
    double estres;
    switch (prioridad) {
      case 'Baja':
        duracion = 3;
        estres = 0.1;
        break;
      case 'Alta':
        duracion = 8;
        estres = 0.3;
        break;
      case 'Media':
      default:
        duracion = 5;
        estres = 0.2;
        break;
    }

    final EstadoTarea estado = completada
        ? EstadoTarea.hecho
        : (isFirstPending ? EstadoTarea.ahora : EstadoTarea.despues);

    final String subtitulo = completada
        ? '¡Hecho! · +$puntos dopamina'
        : (pasos.isNotEmpty
            ? '$etiqueta · ${pasos.length} micro-pasos · $duracion min'
            : '$etiqueta · $duracion min');

    return TareaBloque(
      id: json['id'] as int?,
      titulo: json['titulo'] as String? ?? 'Micro-tarea',
      subtitulo: subtitulo,
      duracionMinutos: duracion,
      estado: estado,
      puntosDopamina: puntos,
      estresNivel: estres,
      microPasos: pasos,
      prioridad: prioridad,
    );
  }
}
