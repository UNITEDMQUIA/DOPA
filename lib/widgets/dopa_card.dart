import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Contenedor base de estilo "Soft Neo-Brutalism".
/// Aplica el borde oscuro característico, radio amplio y fondo pastel.
class DopaCard extends StatelessWidget {
  final Widget child;
  final Color backgroundColor;
  final double borderRadius;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final double borderWidth;
  final Color borderColor;

  const DopaCard({
    super.key,
    required this.child,
    this.backgroundColor = AppTheme.surfaceWhite,
    this.borderRadius = AppTheme.radiusMedium,
    this.padding = const EdgeInsets.all(16.0),
    this.onTap,
    this.borderWidth = AppTheme.borderWidth,
    this.borderColor = AppTheme.borderDark,
  });

  @override
  Widget build(BuildContext context) {
    final container = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.all(
          color: borderColor,
          width: borderWidth,
        ),
      ),
      child: child,
    );

    if (onTap != null) {
      return GestureDetector(
        onTap: onTap,
        child: container,
      );
    }

    return container;
  }
}
