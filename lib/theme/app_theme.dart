import 'package:flutter/material.dart';

/// Sistema de diseño "Soft Neo-Brutalism" para Dopa App.
/// Caracterizado por:
/// - Fondos suaves y colores pastel relajantes (baja sobrecarga sensorial)
/// - Bordes oscuros bien definidos pero amigables (~1.5 a 2.0 dp)
/// - Esquinas muy redondeadas (16 - 28 dp)
/// - Tipografía limpia, empática y de alto contraste
class AppTheme {
  // Paleta de colores base
  static const Color background = Color(0xFFF7F9F5);
  static const Color surfaceWhite = Color(0xFFFFFFFF);
  static const Color borderDark = Color(0xFF1E3830); // Verde petróleo oscuro característico
  static const Color textPrimary = Color(0xFF16332C);
  static const Color textSecondary = Color(0xFF6B8079);
  static const Color textMuted = Color(0xFF8FA39D);

  // Paleta Pastel Neuro-inclusiva
  static const Color pastelPink = Color(0xFFF8BAC7);     // Energía, "ahora", acentos
  static const Color pastelPeach = Color(0xFFFFD5AF);    // Inquieto, estiramiento
  static const Color pastelYellow = Color(0xFFFFF199);   // Tips IA, pasos activos, botones foco
  static const Color pastelLime = Color(0xFFD6F57B);     // Tarea activa, Empezar, Conseguido
  static const Color pastelMint = Color(0xFFB4EBD5);     // Tareas hechas, resumen día
  static const Color pastelBlue = Color(0xFFBCE5F6);     // "Tomar break", "después", volver
  static const Color pastelLilac = Color(0xFFDDD4F9);    // Card de descanso y pausa
  static const Color coralRed = Color(0xFFEE6A62);       // Círculo ícono temporizador

  // Bordes y esquinas redondeadas
  static const double borderWidth = 1.8;
  static const double radiusSmall = 14.0;
  static const double radiusMedium = 20.0;
  static const double radiusLarge = 26.0;

  static Border standardBorder = Border.all(
    color: borderDark,
    width: borderWidth,
  );

  static ThemeData get themeData {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: background,
      fontFamily: 'Inter', // Fallback estándar del sistema, compatible con Outfit/Nunito
      colorScheme: ColorScheme.fromSeed(
        seedColor: pastelLime,
        surface: surfaceWhite,
      ),
      textTheme: const TextTheme(
        headlineMedium: TextStyle(
          color: textPrimary,
          fontSize: 24,
          fontWeight: FontWeight.w800,
          letterSpacing: -0.5,
        ),
        titleLarge: TextStyle(
          color: textPrimary,
          fontSize: 20,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.3,
        ),
        titleMedium: TextStyle(
          color: textPrimary,
          fontSize: 16,
          fontWeight: FontWeight.w700,
        ),
        bodyLarge: TextStyle(
          color: textPrimary,
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
        bodyMedium: TextStyle(
          color: textSecondary,
          fontSize: 13,
          fontWeight: FontWeight.w500,
        ),
        labelSmall: TextStyle(
          color: textSecondary,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
