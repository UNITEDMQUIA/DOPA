import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/dopa_card.dart';
import '../widgets/mood_selector.dart';
import '../widgets/streak_chart.dart';
import '../models/wellness_record_model.dart';
import '../services/db_service.dart';

/// Pantalla 5: Mi Dopamina hoy (Gamificación libre de culpa y Diario de Bienestar).
class DopamineStatsScreen extends StatefulWidget {
  final VoidCallback? onBack;

  const DopamineStatsScreen({super.key, this.onBack});

  @override
  State<DopamineStatsScreen> createState() => _DopamineStatsScreenState();
}

class _DopamineStatsScreenState extends State<DopamineStatsScreen> {
  int _selectedFilter = 0; // 0: Día, 1: Semana, 2: Mes
  TipoHumor _currentMood = TipoHumor.conFoco;
  int _dopaminaHoy = 32;
  final int _metaHoy = 50;

  @override
  void initState() {
    super.initState();
    _cargarDatosGamificacion();
  }

  void _cargarDatosGamificacion() async {
    final total = await DBService.instance.obtenerTotalDopaminaHoy();
    if (!mounted) return;
    setState(() {
      _dopaminaHoy = total;
    });
  }

  @override
  Widget build(BuildContext context) {
    final double progreso = (_dopaminaHoy / _metaHoy).clamp(0.0, 1.0);
    final int porcentaje = (progreso * 100).toInt();

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ENCABEZADO: Volver, Título y logo dopa
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
                            'Mi Dopamina hoy',
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
                  Row(
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
                            ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 18),

              // SELECTOR DE PERIODO: [ Día | Semana | Mes ]
              Container(
                height: 42,
                decoration: BoxDecoration(
                  color: const Color(0xFFE5EDE8),
                  borderRadius: BorderRadius.circular(22),
                ),
                padding: const EdgeInsets.all(4),
                child: Row(
                  children: [
                    _buildFilterItem('Día', 0),
                    _buildFilterItem('Semana', 1),
                    _buildFilterItem('Mes', 2),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // SELECTOR DE FECHA CON NAVEGACIÓN
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildNavArrow(Icons.chevron_left_rounded, () {}),
                  const SizedBox(width: 12),
                  Flexible(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppTheme.pastelYellow,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: AppTheme.borderDark,
                          width: AppTheme.borderWidth,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.calendar_today_outlined, size: 16, color: AppTheme.borderDark),
                          const SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              'Jue, 1 de octubre',
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                    fontWeight: FontWeight.w800,
                                  ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  _buildNavArrow(Icons.chevron_right_rounded, () {}),
                ],
              ),
              const SizedBox(height: 20),

              // TARJETA PRINCIPAL: DOPAMINA REUNIDA
              DopaCard(
                backgroundColor: AppTheme.pastelMint,
                padding: const EdgeInsets.all(20.0),
                borderRadius: AppTheme.radiusLarge,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Dopamina reunida',
                                overflow: TextOverflow.ellipsis,
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                      fontWeight: FontWeight.w700,
                                      color: AppTheme.textPrimary,
                                    ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '$_dopaminaHoy pts',
                                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                      fontSize: 34,
                                      fontWeight: FontWeight.w900,
                                      letterSpacing: -0.5,
                                    ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          width: 72,
                          height: 72,
                          decoration: BoxDecoration(
                            color: AppTheme.pastelYellow,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppTheme.borderDark,
                              width: AppTheme.borderWidth,
                            ),
                          ),
                          child: Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  '$porcentaje%',
                                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                        fontWeight: FontWeight.w900,
                                        fontSize: 15,
                                      ),
                                ),
                                Text(
                                  'de tu meta',
                                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                        fontSize: 9,
                                        fontWeight: FontWeight.w700,
                                        height: 1.1,
                                      ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Container(
                      height: 14,
                      decoration: BoxDecoration(
                        color: AppTheme.surfaceWhite,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: AppTheme.borderDark,
                          width: 1.4,
                        ),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8.5),
                        child: FractionallySizedBox(
                          alignment: Alignment.centerLeft,
                          widthFactor: progreso,
                          child: Container(
                            color: AppTheme.pastelPink,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // DIARIO DE BIENESTAR ("Mi humor")
              Text(
                'Mi humor',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 14),
              MoodSelector(
                selectedMood: _currentMood,
                onMoodChanged: (nuevoHumor) {
                  setState(() {
                    _currentMood = nuevoHumor;
                  });
                },
              ),
              const SizedBox(height: 24),

              // MOTOR DE GAMIFICACIÓN ("Rachas")
              const StreakChart(streakDays: 4),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFilterItem(String title, int index) {
    final bool isSelected = _selectedFilter == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedFilter = index),
        child: Container(
          decoration: BoxDecoration(
            color: isSelected ? AppTheme.surfaceWhite : Colors.transparent,
            borderRadius: BorderRadius.circular(18),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.06),
                      blurRadius: 4,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : null,
          ),
          child: Center(
            child: Text(
              title,
              style: TextStyle(
                color: AppTheme.textPrimary,
                fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavArrow(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: AppTheme.borderDark,
            width: AppTheme.borderWidth,
          ),
        ),
        child: Icon(icon, color: AppTheme.borderDark, size: 22),
      ),
    );
  }
}
