import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'dopa_card.dart';

/// Componente visual del "Motor de Gamificación" (Rachas amables sin culpa).
/// Representa el gráfico semanal de rachas (L, M, X, J, V, S, D).
class StreakChart extends StatelessWidget {
  final int streakDays;

  const StreakChart({
    super.key,
    this.streakDays = 4,
  });

  @override
  Widget build(BuildContext context) {
    final List<Map<String, dynamic>> days = [
      {'day': 'L', 'height': 38.0, 'active': true},
      {'day': 'M', 'height': 50.0, 'active': true},
      {'day': 'X', 'height': 58.0, 'active': true},
      {'day': 'J', 'height': 45.0, 'active': true},
      {'day': 'V', 'height': 60.0, 'active': false},
      {'day': 'S', 'height': 28.0, 'active': false},
      {'day': 'D', 'height': 42.0, 'active': false},
    ];

    return DopaCard(
      backgroundColor: AppTheme.surfaceWhite,
      padding: const EdgeInsets.all(18.0),
      borderRadius: AppTheme.radiusLarge,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  'Rachas',
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.pastelLilac,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: AppTheme.borderDark.withValues(alpha: 0.3),
                    width: 1.0,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('⭐', style: TextStyle(fontSize: 12)),
                    const SizedBox(width: 4),
                    Text(
                      '$streakDays días',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textPrimary,
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Barras semanales
          SizedBox(
            height: 92,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: days.map((item) {
                final bool isActive = item['active'] as bool;
                final double barHeight = item['height'] as double;
                final String label = item['day'] as String;

                return Column(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Container(
                      width: 22,
                      height: barHeight,
                      decoration: BoxDecoration(
                        color: isActive ? AppTheme.pastelPink : const Color(0xFFE4ECE8),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppTheme.borderDark,
                          width: AppTheme.borderWidth,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      label,
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: AppTheme.textPrimary,
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                  ],
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}
