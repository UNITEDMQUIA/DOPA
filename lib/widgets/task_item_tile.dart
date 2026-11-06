import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/task_model.dart';
import 'dopa_card.dart';

/// Item visual de lista para cada micro-tarea.
/// Replica la estética de las tarjetas de tareas con estados:
/// - 'ahora' (fondo verde-lima o blanco con indicador rosa)
/// - 'después' (blanco con indicador amarillo/celeste)
/// - 'hecho' (check verde completado y texto de dopamina)
class TaskItemTile extends StatelessWidget {
  final TareaBloque tarea;
  final bool isSelected;
  final ValueChanged<bool?>? onToggle;
  final VoidCallback? onTap;

  const TaskItemTile({
    super.key,
    required this.tarea,
    this.isSelected = false,
    this.onToggle,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final bool isDone = tarea.estado == EstadoTarea.hecho;

    // Fondo: lima pastel si está seleccionada para 'ahora', o blanco
    final Color bgColor = isSelected ? AppTheme.pastelLime : AppTheme.surfaceWhite;

    // Color del indicador lateral según estado
    Color statusDotColor;
    switch (tarea.estado) {
      case EstadoTarea.ahora:
        statusDotColor = AppTheme.pastelPink;
        break;
      case EstadoTarea.despues:
        statusDotColor = const Color(0xFF90D0EE);
        break;
      case EstadoTarea.hecho:
        statusDotColor = const Color(0xFF6DC89E);
        break;
    }

    return DopaCard(
      backgroundColor: bgColor,
      padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 12.0),
      borderRadius: AppTheme.radiusMedium,
      onTap: onTap,
      child: Row(
        children: [
          // Checkbox redondeado con contorno oscuro
          GestureDetector(
            onTap: () {
              if (onToggle != null) {
                onToggle!(!isDone);
              }
            },
            child: Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: isDone ? const Color(0xFF6DC89E) : Colors.transparent,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: AppTheme.borderDark,
                  width: AppTheme.borderWidth,
                ),
              ),
              child: isDone
                  ? const Icon(
                      Icons.check,
                      size: 20,
                      color: AppTheme.surfaceWhite,
                    )
                  : null,
            ),
          ),
          const SizedBox(width: 14),

          // Título y detalles de micro-pasos / tiempo
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tarea.titulo,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppTheme.textPrimary,
                        fontWeight: FontWeight.w800,
                        decoration: isDone ? TextDecoration.lineThrough : null,
                      ),
                ),
                const SizedBox(height: 3),
                Text(
                  tarea.subtitulo,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: isDone ? AppTheme.textSecondary : AppTheme.textSecondary,
                        fontWeight: FontWeight.w600,
                      ),
                ),
              ],
            ),
          ),

          // Indicador circular de estado
          Container(
            width: 14,
            height: 14,
            decoration: BoxDecoration(
              color: statusDotColor,
              shape: BoxShape.circle,
              border: Border.all(
                color: AppTheme.borderDark,
                width: 1.2,
              ),
            ),
          ),

          // Chevron si la tarea tiene micro-pasos o es la activa
          if (isSelected) ...[
            const SizedBox(width: 8),
            const Icon(
              Icons.chevron_right_rounded,
              color: AppTheme.borderDark,
              size: 22,
            ),
          ],
        ],
      ),
    );
  }
}
