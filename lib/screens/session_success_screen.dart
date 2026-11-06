import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/dopa_card.dart';
import 'main_navigation_screen.dart';

/// Pantalla 4: ¡Tiempo! / Celebración Libre de Culpa.
///
/// Principio UX: Refuerzo positivo inmediato.
/// No exige continuar trabajando; valida el esfuerzo realizado ("Esto ya cuenta")
/// y permite descansar o revisar el avance acumulado.
class SessionSuccessScreen extends StatelessWidget {
  final String taskTitle;
  final int dopamineGained;
  final int totalDopamineToday;
  final VoidCallback? onGoToDopamine;
  final VoidCallback? onGoHome;

  const SessionSuccessScreen({
    super.key,
    this.taskTitle = 'Hacer la cama',
    this.dopamineGained = 10,
    this.totalDopamineToday = 32,
    this.onGoToDopamine,
    this.onGoHome,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 22.0, vertical: 14.0),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight - 28.0,
                ),
                child: IntrinsicHeight(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // -------------------------------------------------------------
                      // ENCABEZADO: Título y Cerrar
                      // -------------------------------------------------------------
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '¡Tiempo!',
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                          ),
                          GestureDetector(
                            onTap: () => Navigator.maybePop(context),
                            child: Text(
                              'Cerrar',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: AppTheme.textSecondary,
                                    fontWeight: FontWeight.w700,
                                  ),
                            ),
                          ),
                        ],
                      ),
                      const Spacer(flex: 1),
                      const SizedBox(height: 16),

                      // -------------------------------------------------------------
                      // ILUSTRACIÓN CENTRAL: Medalla con brote y carita feliz
                      // -------------------------------------------------------------
                      Container(
                        width: 150,
                        height: 150,
                        decoration: BoxDecoration(
                          color: AppTheme.pastelYellow,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: AppTheme.borderDark,
                            width: AppTheme.borderWidth,
                          ),
                        ),
                        child: Center(
                          child: Container(
                            width: 90,
                            height: 90,
                            decoration: BoxDecoration(
                              color: AppTheme.coralRed,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: AppTheme.borderDark,
                                width: AppTheme.borderWidth,
                              ),
                            ),
                            child: const Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text('🌱', style: TextStyle(fontSize: 22)),
                                Text(
                                  '‿',
                                  style: TextStyle(
                                    fontSize: 22,
                                    height: 0.7,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // -------------------------------------------------------------
                      // MENSAJE DE VALIDACIÓN Y ALIVIO
                      // -------------------------------------------------------------
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            '¡Lo hiciste, Fred!',
                            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(width: 6),
                          const Text('✨', style: TextStyle(fontSize: 22)),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16.0),
                        child: Text(
                          'El temporizador terminó y «$taskTitle» quedó lista.\nRespira ese pequeño alivio.',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: AppTheme.textSecondary,
                                fontWeight: FontWeight.w600,
                                height: 1.4,
                                fontSize: 14,
                              ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // -------------------------------------------------------------
                      // TARJETA RESUMEN DE DOPAMINA GANADA (Verde Menta Pastel)
                      // -------------------------------------------------------------
                      DopaCard(
                        backgroundColor: AppTheme.pastelMint,
                        padding: const EdgeInsets.all(18.0),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Text(
                                            '¡Conseguido!',
                                            style: Theme.of(context)
                                                .textTheme
                                                .titleMedium
                                                ?.copyWith(
                                                  fontWeight: FontWeight.w800,
                                                ),
                                          ),
                                          const SizedBox(width: 4),
                                          const Text('✨', style: TextStyle(fontSize: 14)),
                                        ],
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        '$taskTitle · 2 pasos',
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodyMedium
                                            ?.copyWith(
                                              color: AppTheme.textSecondary,
                                              fontWeight: FontWeight.w600,
                                            ),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                // Badge con la dopamina ganada
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 6,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AppTheme.pastelYellow,
                                    borderRadius: BorderRadius.circular(16),
                                    border: Border.all(
                                      color: AppTheme.borderDark,
                                      width: 1.2,
                                    ),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(
                                        Icons.auto_awesome,
                                        size: 14,
                                        color: AppTheme.borderDark,
                                      ),
                                      const SizedBox(width: 4),
                                      Text(
                                        '+$dopamineGained',
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleMedium
                                            ?.copyWith(
                                              fontWeight: FontWeight.w900,
                                            ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            const Divider(color: Color(0xFF88CCA9), thickness: 1),
                            const SizedBox(height: 6),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'Dopamina de hoy',
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                        color: AppTheme.textPrimary,
                                        fontWeight: FontWeight.w700,
                                      ),
                                ),
                                Text(
                                  '$totalDopamineToday puntos',
                                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                        fontWeight: FontWeight.w800,
                                      ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 18),

                      // -------------------------------------------------------------
                      // BOTONES DE NAVEGACIÓN
                      // -------------------------------------------------------------
                      // Botón 1: Ver Mi Dopamina
                      DopaCard(
                        backgroundColor: AppTheme.pastelLime,
                        padding: const EdgeInsets.symmetric(vertical: 16.0),
                        onTap: onGoToDopamine ??
                            () {
                              MainNavigationScreen.tabNotifier.value = 2;
                              Navigator.of(context).popUntil((route) => route.isFirst);
                            },
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(
                              Icons.bar_chart_rounded,
                              color: AppTheme.borderDark,
                              size: 22,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Ver Mi Dopamina hoy',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w800,
                                  ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Botón 2: Volver al inicio
                      DopaCard(
                        backgroundColor: AppTheme.pastelBlue,
                        padding: const EdgeInsets.symmetric(vertical: 16.0),
                        onTap: onGoHome ??
                            () {
                              MainNavigationScreen.tabNotifier.value = 0;
                              Navigator.of(context).popUntil((route) => route.isFirst);
                            },
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(
                              Icons.home_outlined,
                              color: AppTheme.borderDark,
                              size: 22,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Volver al inicio',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w800,
                                  ),
                            ),
                          ],
                        ),
                      ),
                      const Spacer(flex: 1),
                      const SizedBox(height: 16),

                      // Texto tranquilizador al pie
                      Text(
                        'No hace falta hacer otra cosa ahora. Esto ya cuenta.',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppTheme.textMuted,
                              fontWeight: FontWeight.w600,
                              fontSize: 12,
                            ),
                      ),
                      const SizedBox(height: 10),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
