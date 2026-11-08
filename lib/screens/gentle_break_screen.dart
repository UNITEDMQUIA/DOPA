import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/dopa_card.dart';
import '../services/db_service.dart';
import '../models/reward_model.dart';

/// Pantalla 6: Un break suave (Pausa y Actividades de Bajo Estímulo).
class GentleBreakScreen extends StatefulWidget {
  final VoidCallback? onBack;
  final VoidCallback? onGoHome;

  const GentleBreakScreen({
    super.key,
    this.onBack,
    this.onGoHome,
  });

  @override
  State<GentleBreakScreen> createState() => _GentleBreakScreenState();
}

class _GentleBreakScreenState extends State<GentleBreakScreen> {
  int _selectedMinutes = 5;
  late int _remainingSeconds;
  bool _isRunning = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _remainingSeconds = _selectedMinutes * 60;
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _seleccionarMinutos(int minutos) {
    if (_isRunning) _timer?.cancel();
    setState(() {
      _selectedMinutes = minutos;
      _remainingSeconds = minutos * 60;
      _isRunning = false;
    });
  }

  void _toggleBreakTimer() {
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
          _registrarPausaCompletada();
        }
      });
    }
  }

  void _registrarPausaCompletada() async {
    await DBService.instance.agregarRecompensa(
      Recompensa(
        titulo: 'Pausa completada',
        puntosDopamina: 5,
        tipo: 'break',
      ),
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Tu energía también merece espacio ✨'),
        duration: Duration(seconds: 2),
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
              // ENCABEZADO: Volver, Título y Omitir
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        GestureDetector(
                          onTap: widget.onBack ?? () => Navigator.maybePop(context),
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
                        Flexible(
                          child: Text(
                            'Un break suave',
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: widget.onGoHome ?? () => Navigator.maybePop(context),
                    child: Text(
                      'Omitir',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),

              // TÍTULO Y SUBTÍTULO CALMADO
              Row(
                children: [
                  Flexible(
                    child: Text(
                      'Bajemos el volumen',
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text('☁️', style: TextStyle(fontSize: 24)),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                'Elige cuánto necesitas. No hay nada que completar perfecto.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.textSecondary,
                      fontWeight: FontWeight.w600,
                      height: 1.35,
                    ),
              ),
              const SizedBox(height: 18),

              // SELECTOR DE DURACIÓN RÁPIDA: [ 5 minutos | 10 minutos ]
              Row(
                children: [
                  Expanded(
                    child: _buildDurationPill('5 minutos', 5),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildDurationPill('10 minutos', 10),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // TARJETA DE TEMPORIZADOR DE DESCANSO
              DopaCard(
                backgroundColor: AppTheme.pastelLilac,
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 22.0),
                borderRadius: AppTheme.radiusLarge,
                child: Column(
                  children: [
                    Container(
                      width: 58,
                      height: 58,
                      decoration: BoxDecoration(
                        color: AppTheme.surfaceWhite,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppTheme.borderDark,
                          width: AppTheme.borderWidth,
                        ),
                      ),
                      child: const Center(
                        child: Icon(
                          Icons.cloud_outlined,
                          color: AppTheme.borderDark,
                          size: 30,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _formatTime(_remainingSeconds),
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontSize: 42,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 1.0,
                          ),
                    ),
                    Text(
                      'listo cuando tú estés',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textPrimary.withValues(alpha: 0.7),
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                    const SizedBox(height: 18),
                    DopaCard(
                      backgroundColor: AppTheme.pastelYellow,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      borderRadius: AppTheme.radiusLarge,
                      onTap: _toggleBreakTimer,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            _isRunning ? Icons.pause_rounded : Icons.play_arrow_outlined,
                            color: AppTheme.borderDark,
                            size: 24,
                          ),
                          const SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              _isRunning ? 'Pausar descanso' : 'Empezar descanso',
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w800,
                                    color: AppTheme.textPrimary,
                                  ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 22),

              // ACTIVIDADES DE BAJO ESTÍMULO
              Text(
                'Actividades de bajo estímulo',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 12),

              _buildLowStimulusCard(
                icon: Icons.air_rounded,
                title: 'Respiración 4–4',
                subtitle: 'Inhala 4 · suelta 4',
                duration: '1 min',
                backgroundColor: AppTheme.pastelMint,
              ),
              const SizedBox(height: 10),

              _buildLowStimulusCard(
                icon: Icons.accessibility_new_rounded,
                title: 'Estiramiento suave',
                subtitle: 'Hombros y manos',
                duration: '2 min',
                backgroundColor: AppTheme.pastelPeach,
              ),
              const SizedBox(height: 10),

              DopaCard(
                backgroundColor: AppTheme.pastelLime,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(
                        color: Colors.transparent,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppTheme.borderDark,
                          width: 1.5,
                        ),
                      ),
                      child: const Icon(Icons.check, size: 16, color: AppTheme.borderDark),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  'Pausa completada',
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                        fontWeight: FontWeight.w800,
                                      ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              const Text('✨', style: TextStyle(fontSize: 14)),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Tu energía también merece espacio.',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: AppTheme.textSecondary,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 12,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // BOTÓN: Volver al inicio
              DopaCard(
                backgroundColor: AppTheme.pastelBlue,
                padding: const EdgeInsets.symmetric(vertical: 16.0),
                onTap: widget.onGoHome ?? () => Navigator.maybePop(context),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.home_outlined, color: AppTheme.borderDark, size: 22),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        'Volver al inicio',
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDurationPill(String title, int minutes) {
    final bool isSelected = _selectedMinutes == minutes;
    return DopaCard(
      backgroundColor: isSelected ? AppTheme.pastelBlue : AppTheme.surfaceWhite,
      padding: const EdgeInsets.symmetric(vertical: 12),
      borderRadius: AppTheme.radiusLarge,
      onTap: () => _seleccionarMinutos(minutes),
      child: Center(
        child: Text(
          title,
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildLowStimulusCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required String duration,
    required Color backgroundColor,
  }) {
    return DopaCard(
      backgroundColor: backgroundColor,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Icon(icon, color: AppTheme.borderDark, size: 26),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppTheme.textSecondary,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            duration,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textSecondary,
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}
