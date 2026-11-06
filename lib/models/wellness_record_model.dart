enum TipoHumor { abrumado, inquieto, conFoco, tranquilo }

/// Modelo de entidad 'Registro_Bienestar' (Diario de bienestar / estado de ánimo).
class RegistroBienestar {
  final int? id;
  final DateTime fecha;
  final TipoHumor humor;
  final double nivelEnergia; // 0.0 a 1.0
  final String? notas;

  RegistroBienestar({
    this.id,
    DateTime? fecha,
    required this.humor,
    this.nivelEnergia = 0.5,
    this.notas,
  }) : fecha = fecha ?? DateTime.now();

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'fecha': fecha.toIso8601String(),
      'humor': humor.name,
      'nivel_energia': nivelEnergia,
      'notas': notas,
    };
  }

  factory RegistroBienestar.fromMap(Map<String, dynamic> map) {
    return RegistroBienestar(
      id: map['id'] as int?,
      fecha: map['fecha'] != null
          ? DateTime.parse(map['fecha'] as String)
          : DateTime.now(),
      humor: TipoHumor.values.firstWhere(
        (h) => h.name == map['humor'],
        orElse: () => TipoHumor.conFoco,
      ),
      nivelEnergia: (map['nivel_energia'] as num?)?.toDouble() ?? 0.5,
      notas: map['notas'] as String?,
    );
  }
}
