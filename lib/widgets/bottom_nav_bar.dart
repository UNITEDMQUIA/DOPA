import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Barra de navegación inferior personalizada.
/// Muestra las 4 secciones fundamentales con indicador activo en línea verde.
class DopaBottomNavBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const DopaBottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final navItems = [
      _NavItem(icon: Icons.home_outlined, activeIcon: Icons.home_rounded, label: 'Inicio'),
      _NavItem(icon: Icons.checklist_rounded, activeIcon: Icons.checklist_rounded, label: 'Tareas'),
      _NavItem(icon: Icons.auto_awesome_outlined, activeIcon: Icons.auto_awesome, label: 'Dopamina'),
      _NavItem(icon: Icons.coffee_outlined, activeIcon: Icons.coffee_rounded, label: 'Pausa'),
    ];

    return Container(
      decoration: const BoxDecoration(
        color: AppTheme.surfaceWhite,
        border: Border(
          top: BorderSide(
            color: Color(0xFFE2EBE5),
            width: 1.5,
          ),
        ),
      ),
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: SafeArea(
        top: false,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: List.generate(navItems.length, (index) {
            final isSelected = index == currentIndex;
            final item = navItems[index];

            return GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: () => onTap(index),
              child: SizedBox(
                width: 70,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isSelected ? item.activeIcon : item.icon,
                      color: isSelected ? AppTheme.textPrimary : AppTheme.textMuted,
                      size: 24,
                    ),
                    const SizedBox(height: 3),
                    Text(
                      item.label,
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: isSelected ? AppTheme.textPrimary : AppTheme.textMuted,
                            fontWeight: isSelected ? FontWeight.w800 : FontWeight.w500,
                          ),
                    ),
                    const SizedBox(height: 4),

                    // Línea indicadora inferior para pestaña activa
                    Container(
                      width: 28,
                      height: 3,
                      decoration: BoxDecoration(
                        color: isSelected ? const Color(0xFF5CB78F) : Colors.transparent,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ),
      ),
    );
  }
}

class _NavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;

  _NavItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
}
