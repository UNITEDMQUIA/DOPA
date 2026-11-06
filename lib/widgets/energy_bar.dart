import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'dopa_card.dart';

/// Componente visual del medidor de energía y nivel de dopamina.
/// Representa fielmente la tarjeta rosa de la Pantalla de Inicio.
class EnergyDopamineCard extends StatelessWidget {
  final double energyLevel; // 0.0 (poquita) a 1.0 (a tope)
  final String emoji;
  final ValueChanged<double>? onEnergyChanged;

  const EnergyDopamineCard({
    super.key,
    this.energyLevel = 0.45,
    this.emoji = '😌',
    this.onEnergyChanged,
  });

  @override
  Widget build(BuildContext context) {
    // [INYECCIÓN DE DATOS - SQLite / FastAPI]:
    // Reemplazar energyLevel por el valor cargado de:
    //   final usuario = await DBService.instance.getUsuario();
    //   usuario.energiaNivel;

    return DopaCard(
      backgroundColor: AppTheme.pastelPink,
      padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Título y emoji de estado
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '¿Cómo está tu energía?',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w800,
                    ),
              ),
              Text(
                emoji,
                style: const TextStyle(fontSize: 26),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            'Dopamina',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textPrimary,
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 8),

          // Barra multicolor segmentada con borde oscuro
          Container(
            height: 16,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: AppTheme.borderDark,
                width: 1.5,
              ),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8.5),
              child: Row(
                children: [
                  Expanded(flex: 2, child: Container(color: const Color(0xFFE57388))),
                  Expanded(flex: 2, child: Container(color: const Color(0xFFF6C8A4))),
                  Expanded(flex: 3, child: Container(color: const Color(0xFFFDF08E))),
                  Expanded(flex: 3, child: Container(color: const Color(0xFF75CEA6))),
                  Expanded(flex: 3, child: Container(color: const Color(0xFFA5D8F2))),
                  Expanded(flex: 2, child: Container(color: const Color(0xFFD3B6ED))),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),

          // Etiquetas de los extremos
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'poquita',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: AppTheme.textPrimary.withValues(alpha: 0.7),
                      fontWeight: FontWeight.w600,
                    ),
              ),
              Text(
                'a tope',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: AppTheme.textPrimary.withValues(alpha: 0.7),
                      fontWeight: FontWeight.w600,
                    ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
