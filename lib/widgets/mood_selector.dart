import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/wellness_record_model.dart';
import '../services/db_service.dart';
import '../services/api_service.dart';

/// Selector interactivo para el "Diario de Bienestar" / Registro de humor.
/// Muestra las 4 opciones emocionales con diseño neo-brutalist.
class MoodSelector extends StatefulWidget {
  final TipoHumor selectedMood;
  final ValueChanged<TipoHumor>? onMoodChanged;

  const MoodSelector({
    super.key,
    this.selectedMood = TipoHumor.conFoco,
    this.onMoodChanged,
  });

  @override
  State<MoodSelector> createState() => _MoodSelectorState();
}

class _MoodSelectorState extends State<MoodSelector> {
  late TipoHumor _currentMood;

  @override
  void initState() {
    super.initState();
    _currentMood = widget.selectedMood;
  }

  void _handleMoodSelect(TipoHumor humor) {
    setState(() {
      _currentMood = humor;
    });

    if (widget.onMoodChanged != null) {
      widget.onMoodChanged!(humor);
    }

    // [INYECCIÓN DE DATOS - SQLite]:
    // Guarda el registro diario en la base de datos local
    final registro = RegistroBienestar(humor: humor);
    DBService.instance.guardarRegistroBienestar(registro);

    // [INYECCIÓN FASTAPI]:
    // Envía el evento al Agente de IA para adaptar los tiempos sugeridos
    ApiService.instance.sendWellnessAnalysis(registro);
  }

  @override
  Widget build(BuildContext context) {
    final items = [
      _MoodOption(
        humor: TipoHumor.abrumado,
        label: 'Abrumado',
        emoji: '😫',
        bgColor: AppTheme.pastelPink,
      ),
      _MoodOption(
        humor: TipoHumor.inquieto,
        label: 'Inquieto',
        emoji: '😟',
        bgColor: AppTheme.pastelPeach,
      ),
      _MoodOption(
        humor: TipoHumor.conFoco,
        label: 'Con foco',
        emoji: '🙂',
        bgColor: AppTheme.pastelYellow,
      ),
      _MoodOption(
        humor: TipoHumor.tranquilo,
        label: 'Tranquilo',
        emoji: '😌',
        bgColor: AppTheme.pastelMint,
      ),
    ];

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: items.map((item) {
        final isSelected = item.humor == _currentMood;
        return GestureDetector(
          onTap: () => _handleMoodSelect(item.humor),
          child: Column(
            children: [
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(
                  color: item.bgColor,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: AppTheme.borderDark,
                    width: isSelected ? 2.8 : AppTheme.borderWidth,
                  ),
                ),
                child: Center(
                  child: Text(
                    item.emoji,
                    style: const TextStyle(fontSize: 26),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                item.label,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

class _MoodOption {
  final TipoHumor humor;
  final String label;
  final String emoji;
  final Color bgColor;

  _MoodOption({
    required this.humor,
    required this.label,
    required this.emoji,
    required this.bgColor,
  });
}
