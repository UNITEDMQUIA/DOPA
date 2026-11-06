import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/task_model.dart';
import '../models/focus_session_model.dart';
import '../models/reward_model.dart';
import '../widgets/dopa_card.dart';
import '../services/db_service.dart';
import 'session_success_screen.dart';

/// Pantalla 3: Enfoque suave (Temporizador Pomodoro y Micro-pasos).
///
/// Principio UX: Reducción drástica del estrés ejecutivo.
/// Desglosa la tarea en pasos atómicos de 1-2 minutos y utiliza un temporizador
/// amigable sin cuenta regresiva agresiva.
class SoftFocusScreen extends StatefulWidget {
  final String taskTitle;
  final List<MicroPaso> microSteps;
  final int durationMinutes;

  const SoftFocusScreen({
    super.key,
    this.taskTitle = 'Hacer la cama',
    this.microSteps = const [],
    this.durationMinutes = 5,
  });

  @override
  State<SoftFocusScreen> createState() => _SoftFocusScreenState();
}

class _SoftFocusScreenState extends State<SoftFocusScreen> {
  late int _remainingSeconds;
  bool _isRunning = false;
  Timer? _timer;

  late bool _step1Done;
  late bool _step2Done;

  @override
  void initState() {
    super.initState();
    _remainingSeconds = widget.durationMinutes * 60;
    _step1Done = true; // Simulado según diseño
    _step2Done = false;
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _toggleTimer() {
    if (_isRunning) {
      _timer?.cancel();
      setState(() => _isRunning = false);
    } else {
      setState(() => _isRunning = true);
      _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
        if (_remainingSeconds > 0) {
          setState(() => _remainingSeconds--);
        } else {
          _timer?.cancel();
          setState(() => _isRunning = false);
          _completarSesion();
        }
      });
    }
  }

  void _completarSesion() async {
    // [INYECCIÓN SQLITE]:
    // 1. Guardar la sesión de enfoque completada
    await DBService.instance.registrarSesion(
      SesionEnfoque(
        duracionSegundos: widget.durationMinutes * 60,
        completada: true,
      ),
    );

    // 2. Otorgar recompensa de dopamina
    await DBService.instance.agregarRecompensa(
      Recompensa(
        titulo: widget.taskTitle,
        puntosDopamina: 10,
        tipo: 'tarea',
      ),
    );

    if (!mounted) return;

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => SessionSuccessScreen(
          taskTitle: widget.taskTitle,
          dopamineGained: 10,
          totalDopamineToday: 32,
        ),
      ),
    );
  }

  String _formatTime(int seconds) {
    final mins = (seconds ~/ 60).toString().padLeft(2, '0');
    final secs = (seconds % 60).toString().padLeft(2, '0');
    return '$mins:$secs';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // -------------------------------------------------------------
              // ENCABEZADO: Volver, Título y Salir
              // -------------------------------------------------------------
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      GestureDetector(
                        onTap: () => Navigator.maybePop(context),
                        child: Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppTheme.borderDark,
                              width: AppTheme.borderWidth,
                            ),
                          ),
                          child: const Icon(
                            Icons.chevron_left_rounded,
                            color: AppTheme.borderDark,
                            size: 26,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Enfoque suave',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ],
                  ),
                  GestureDetector(
                    onTap: () => Navigator.maybePop(context),
                    child: Text(
                      'Salir',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // -------------------------------------------------------------
              // TARJETA DE TAREA ACTUAL (Verde Lima Pastel)
              // -------------------------------------------------------------
              DopaCard(
                backgroundColor: AppTheme.pastelLime,
                padding: const EdgeInsets.all(18.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.album_outlined,
                          size: 16,
                          color: AppTheme.borderDark,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'TAREA ACTUAL',
                          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                color: AppTheme.borderDark,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.8,
                              ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      widget.taskTitle,
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Solo mira el siguiente paso. Lo demás puede esperar.',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textPrimary.withValues(alpha: 0.8),
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 22),

              // -------------------------------------------------------------
              // SECCIÓN: MICRO-PASOS
              // -------------------------------------------------------------
              Text(
                'Micro-pasos',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 12),

              // Paso 1 (Listo / Interactivo)
              DopaCard(
                backgroundColor: AppTheme.surfaceWhite,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                onTap: () {
                  setState(() {
                    _step1Done = !_step1Done;
                  });
                },
                child: Row(
                  children: [
                    Container(
                      width: 26,
                      height: 26,
                      decoration: BoxDecoration(
                        color: _step1Done ? const Color(0xFF6DC89E) : Colors.white,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(
                          color: AppTheme.borderDark,
                          width: 1.5,
                        ),
                      ),
                      child: _step1Done
                          ? const Icon(Icons.check, size: 18, color: Colors.white)
                          : null,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        '1. Estirar las sábanas',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                    ),
                    if (_step1Done)
                      Text(
                        'listo',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(
                              color: const Color(0xFF5BAA86),
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 10),

              // Paso 2 (En curso con fondo amarillo)
              DopaCard(
                backgroundColor: AppTheme.pastelYellow,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                onTap: () {
                  setState(() {
                    _step2Done = !_step2Done;
                  });
                },
                child: Row(
                  children: [
                    Container(
                      width: 26,
                      height: 26,
                      decoration: BoxDecoration(
                        color: _step2Done ? const Color(0xFF6DC89E) : Colors.white,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(
                          color: AppTheme.borderDark,
                          width: 1.5,
                        ),
                      ),
                      child: _step2Done
                          ? const Icon(Icons.check, size: 18, color: Colors.white)
                          : null,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        '2. Colocar almohadas',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ),
                    const Icon(Icons.auto_awesome, size: 20, color: AppTheme.borderDark),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // -------------------------------------------------------------
              // TEMPORIZADOR POMODORO AMIGABLE
              // -------------------------------------------------------------
              DopaCard(
                backgroundColor: AppTheme.surfaceWhite,
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Círculo ícono brote 🌱
                        Container(
                          width: 64,
                          height: 64,
                          decoration: BoxDecoration(
                            color: AppTheme.coralRed,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppTheme.borderDark,
                              width: AppTheme.borderWidth,
                            ),
                          ),
                          child: const Center(
                            child: Text('🌱', style: TextStyle(fontSize: 28)),
                          ),
                        ),
                        const SizedBox(width: 18),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Enfoque',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.textSecondary,
                                  ),
                            ),
                            Text(
                              _formatTime(_remainingSeconds),
                              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                    fontSize: 34,
                                    fontWeight: FontWeight.w900,
                                    letterSpacing: 1.0,
                                    color: AppTheme.textPrimary,
                                  ),
                            ),
                            Text(
                              'minutos · sin notificaciones',
                              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                    color: AppTheme.textMuted,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),

                    // Botón Rosa: Iniciar / Pausar
                    DopaCard(
                      backgroundColor: AppTheme.pastelPink,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      borderRadius: AppTheme.radiusLarge,
                      onTap: _toggleTimer,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            _isRunning ? Icons.pause_rounded : Icons.play_arrow_outlined,
                            color: AppTheme.borderDark,
                            size: 22,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _isRunning ? 'Pausar temporizador' : 'Iniciar temporizador',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  color: AppTheme.textPrimary,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // -------------------------------------------------------------
              // BANNER INFERIOR DE RECOMPENSA DIRECTA
              // -------------------------------------------------------------
              DopaCard(
                backgroundColor: AppTheme.pastelMint,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                borderRadius: AppTheme.radiusLarge,
                onTap: _completarSesion,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Text(
                          '¡Conseguido!',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                              ),
                        ),
                        const SizedBox(width: 6),
                        const Text('✨', style: TextStyle(fontSize: 18)),
                      ],
                    ),
                    Text(
                      '(+10 dopamina)',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                            color: AppTheme.textPrimary,
                          ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}
