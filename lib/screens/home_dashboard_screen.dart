import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/dopa_card.dart';
import '../widgets/energy_bar.dart';
import '../services/db_service.dart';
import '../services/api_service.dart';
import '../models/task_model.dart';
import 'soft_focus_screen.dart';

/// Pantalla 1: Inicio (Dashboard de Cero Fricción Cognitiva).
///
/// Principio UX: "Single Source of Truth".
/// Conectada con `/api/v1/dashboard`, `/api/v1/dashboard/energy-checkin` y `/api/v1/dashboard/quick-task`.
class HomeDashboardScreen extends StatefulWidget {
  final VoidCallback onNavigateToTasks;
  final VoidCallback onNavigateToBreak;

  const HomeDashboardScreen({
    super.key,
    required this.onNavigateToTasks,
    required this.onNavigateToBreak,
  });

  @override
  State<HomeDashboardScreen> createState() => _HomeDashboardScreenState();
}

class _HomeDashboardScreenState extends State<HomeDashboardScreen> {
  String _saludo = '¡Hola, Fred!';
  String _subtitulo = 'Vamos un paso a la vez';
  double _energyLevel = 0.45;
  int _pendientesCount = 2;
  String _quickTaskTitle = 'Poner un vaso de agua cerca';
  int? _quickTaskId = 2;
  List<MicroPaso> _quickTaskSteps = const [];

  @override
  void initState() {
    super.initState();
    _sincronizarDashboard();
  }

  Future<void> _sincronizarDashboard() async {
    try {
      final dashboard = await ApiService.instance.getDashboard();
      if (!mounted) return;
      setState(() {
        if (dashboard['saludo'] is String) {
          _saludo = dashboard['saludo'] as String;
        }
        if (dashboard['subtitulo_amigable'] is String) {
          _subtitulo = dashboard['subtitulo_amigable'] as String;
        }
        final resumen = dashboard['resumen_tareas'] as Map<String, dynamic>?;
        if (resumen != null && resumen['pendientes'] is int) {
          _pendientesCount = resumen['pendientes'] as int;
        }
        final microTareas = dashboard['micro_tareas_hoy'] as List<dynamic>?;
        if (microTareas != null && microTareas.isNotEmpty) {
          final first = microTareas.first;
          if (first is Map<String, dynamic>) {
            final mapped = TareaBloque.fromBackendJson(first, isFirstPending: true);
            _quickTaskTitle = mapped.titulo;
            _quickTaskId = mapped.id;
            _quickTaskSteps = mapped.microPasos;
          }
        }
      });
    } catch (_) {
      final usuario = await DBService.instance.getUsuario();
      if (!mounted) return;
      setState(() {
        _energyLevel = usuario.energiaNivel;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // -------------------------------------------------------------
              // ENCABEZADO: Saludo empático y logo dopa
              // -------------------------------------------------------------
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        Flexible(
                          child: Text(
                            _saludo,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        const Text('✨', style: TextStyle(fontSize: 22)),
                      ],
                    ),
                  ),
                  // Logo / Tag "• dopa"
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: Color(0xFF6BC69B),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'dopa',
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
              const SizedBox(height: 4),
              Text(
                _subtitulo,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.textSecondary,
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                    ),
              ),
              const SizedBox(height: 20),

              // -------------------------------------------------------------
              // 1. MEDIDOR DE ENERGÍA Y DOPAMINA (Card Rosa Pastel)
              // -------------------------------------------------------------
              EnergyDopamineCard(
                energyLevel: _energyLevel,
                emoji: '😌',
              ),
              const SizedBox(height: 18),

              // -------------------------------------------------------------
              // 2. ACCIONES RÁPIDAS BINARIAS (Baja Fricción Cognitiva)
              // -------------------------------------------------------------
              Row(
                children: [
                  // Botón Rosa: "¡Hacer algo fácil!"
                  Expanded(
                    child: DopaCard(
                      backgroundColor: AppTheme.pastelPink,
                      padding: const EdgeInsets.symmetric(vertical: 22.0, horizontal: 12.0),
                      onTap: widget.onNavigateToTasks,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.auto_awesome, color: AppTheme.borderDark, size: 28),
                          const SizedBox(height: 12),
                          Text(
                            '¡Hacer algo fácil!',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  color: AppTheme.textPrimary,
                                  fontSize: 15,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),

                  // Botón Celeste: "¡Tomar un break!"
                  Expanded(
                    child: DopaCard(
                      backgroundColor: AppTheme.pastelBlue,
                      padding: const EdgeInsets.symmetric(vertical: 22.0, horizontal: 12.0),
                      onTap: widget.onNavigateToBreak,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.nightlight_round_outlined, color: AppTheme.borderDark, size: 28),
                          const SizedBox(height: 12),
                          Text(
                            '¡Tomar un break!',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  color: AppTheme.textPrimary,
                                  fontSize: 15,
                                ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 22),

              // -------------------------------------------------------------
              // 3. SECCIÓN: MIS MICRO-TAREAS (Siguiente paso sin abrumar)
              // -------------------------------------------------------------
              DopaCard(
                backgroundColor: AppTheme.surfaceWhite,
                padding: const EdgeInsets.all(18.0),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => SoftFocusScreen(
                        taskId: _quickTaskId,
                        taskTitle: _quickTaskTitle,
                        microSteps: _quickTaskSteps,
                      ),
                    ),
                  );
                },
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Título de la sección y contador de pendientes
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            'Mis micro-tareas',
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  color: AppTheme.textPrimary,
                                ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Flexible(
                          child: Text(
                            '$_pendientesCount pendientes',
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: AppTheme.textSecondary,
                                  fontWeight: FontWeight.w700,
                                ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // Micro-tarea inmediata
                    Row(
                      children: [
                        Container(
                          width: 18,
                          height: 18,
                          decoration: BoxDecoration(
                            color: AppTheme.pastelYellow,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppTheme.borderDark,
                              width: 1.2,
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            _quickTaskTitle,
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.textPrimary,
                                ),
                          ),
                        ),
                        Text(
                          '1 min',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: AppTheme.textSecondary,
                                fontWeight: FontWeight.w600,
                              ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // Indicador de nivel de estrés bajito
                    Row(
                      children: [
                        Text(
                          'Estrés: bajito',
                          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.w700,
                              ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Container(
                            height: 8,
                            decoration: BoxDecoration(
                              color: const Color(0xFFE5EDE8),
                              borderRadius: BorderRadius.circular(5),
                            ),
                            child: FractionallySizedBox(
                              alignment: Alignment.centerLeft,
                              widthFactor: 0.35, // Bajito
                              child: Container(
                                decoration: BoxDecoration(
                                  color: const Color(0xFF67C297),
                                  borderRadius: BorderRadius.circular(5),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
