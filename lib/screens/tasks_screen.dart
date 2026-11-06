import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/task_model.dart';
import '../widgets/ai_recommendation_card.dart';
import '../widgets/task_item_tile.dart';
import '../widgets/dopa_card.dart';
import '../services/db_service.dart';
import 'soft_focus_screen.dart';

/// Pantalla 2: Mis tareas ("Poquito a poquito").
///
/// Principio UX: Priorización suave y no intrusiva.
/// El usuario selecciona sólo una tarea para empezar, eliminando la sensación
/// de montaña de pendientes. El Agente de IA sugiere el orden de menor fricción.
class TasksScreen extends StatefulWidget {
  final VoidCallback? onBack;

  const TasksScreen({super.key, this.onBack});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  // [MOCK DATA]: Inicialmente vacío mientras resuelve DBService.obtenerTareas()
  List<TareaBloque> _tareas = [];
  int _selectedTaskId = 1;

  @override
  void initState() {
    super.initState();
    _cargarTareas();
  }

  void _cargarTareas() async {
    // [INYECCIÓN SQLITE]:
    // Reemplazar con consulta real en DBService.instance.obtenerTareas()
    final tareasDB = await DBService.instance.obtenerTareas();
    if (!mounted) return;
    setState(() {
      _tareas = tareasDB;
    });
  }

  void _iniciarTareaActual() {
    if (_tareas.isEmpty) return;

    final tareaActual = _tareas.firstWhere(
      (t) => t.id == _selectedTaskId,
      orElse: () => _tareas.first,
    );

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SoftFocusScreen(
          taskTitle: tareaActual.titulo,
          microSteps: tareaActual.microPasos,
          durationMinutes: tareaActual.duracionMinutos,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final int completadas =
        _tareas.where((t) => t.estado == EstadoTarea.hecho).length;
    final String contadorTexto =
        _tareas.isEmpty ? '1/4' : '$completadas/${_tareas.length}';

    final String tituloSeleccionado = _tareas.isEmpty
        ? 'Hacer la cama'
        : _tareas
            .firstWhere(
              (t) => t.id == _selectedTaskId,
              orElse: () => _tareas.first,
            )
            .titulo;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // -------------------------------------------------------------
              // ENCABEZADO: Botón atrás, Título y filtro 'Hoy'
              // -------------------------------------------------------------
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
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
                      Text(
                        'Mis tareas',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ],
                  ),
                  Text(
                    'Hoy',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppTheme.textSecondary,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ],
              ),
              const SizedBox(height: 18),

              // -------------------------------------------------------------
              // TÍTULO PRINCIPAL Y CONTADOR CIRCULAR (1/4)
              // -------------------------------------------------------------
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Poquito a poquito',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: AppTheme.textPrimary,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Elige solo una para empezar',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppTheme.textSecondary,
                              fontWeight: FontWeight.w600,
                            ),
                      ),
                    ],
                  ),
                  // Contador circular 1/4
                  Container(
                    width: 52,
                    height: 52,
                    decoration: BoxDecoration(
                      color: AppTheme.pastelMint,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppTheme.borderDark,
                        width: AppTheme.borderWidth,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        contadorTexto,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: AppTheme.textPrimary,
                            ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // -------------------------------------------------------------
              // CONTENEDOR DEL AGENTE DE IA (FastAPI / Sugerencia Adaptativa)
              // -------------------------------------------------------------
              const AIRecommendationCard(
                customMessage:
                    'Empieza por la tarea que te dé más alivio, no por la más grande.',
              ),
              const SizedBox(height: 16),

              // -------------------------------------------------------------
              // LISTA DE TAREAS (Bloques)
              // -------------------------------------------------------------
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _tareas.length,
                separatorBuilder: (context, index) => const SizedBox(height: 10),
                itemBuilder: (context, index) {
                  final tarea = _tareas[index];
                  final isSelected = tarea.id == _selectedTaskId;

                  return TaskItemTile(
                    tarea: tarea,
                    isSelected: isSelected,
                    onTap: () {
                      setState(() {
                        _selectedTaskId = tarea.id!;
                      });
                    },
                    onToggle: (nuevoValor) {
                      // [INYECCIÓN SQLITE]:
                      // Actualizar estado en base de datos local via DBService.instance.actualizarTarea(...)
                      setState(() {
                        _tareas[index] = TareaBloque(
                          id: tarea.id,
                          titulo: tarea.titulo,
                          subtitulo: nuevoValor == true
                              ? '¡Hecho! · +${tarea.puntosDopamina} dopamina'
                              : tarea.subtitulo,
                          duracionMinutos: tarea.duracionMinutos,
                          estado: nuevoValor == true
                              ? EstadoTarea.hecho
                              : EstadoTarea.despues,
                          puntosDopamina: tarea.puntosDopamina,
                          microPasos: tarea.microPasos,
                        );
                      });
                    },
                  );
                },
              ),
              const SizedBox(height: 14),

              // -------------------------------------------------------------
              // LEYENDA DE ESTADOS
              // -------------------------------------------------------------
              const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _StatusLegend(color: AppTheme.pastelPink, label: 'ahora'),
                  SizedBox(width: 16),
                  _StatusLegend(color: Color(0xFF90D0EE), label: 'después'),
                  SizedBox(width: 16),
                  _StatusLegend(color: Color(0xFF6DC89E), label: 'hecho'),
                ],
              ),
              const SizedBox(height: 20),

              // -------------------------------------------------------------
              // BOTÓN DE ACCIÓN PRIMARIO: Empezar Tarea
              // -------------------------------------------------------------
              DopaCard(
                backgroundColor: AppTheme.pastelLime,
                padding: const EdgeInsets.symmetric(vertical: 18.0),
                onTap: _iniciarTareaActual,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.play_arrow_outlined,
                      color: AppTheme.borderDark,
                      size: 26,
                    ),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        'Empezar «$tituloSeleccionado»',
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: AppTheme.textPrimary,
                              fontSize: 16,
                            ),
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

class _StatusLegend extends StatelessWidget {
  final Color color;
  final String label;

  const _StatusLegend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: AppTheme.textSecondary,
                fontWeight: FontWeight.w600,
              ),
        ),
      ],
    );
  }
}
