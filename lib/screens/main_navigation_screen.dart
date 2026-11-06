import 'package:flutter/material.dart';
import '../widgets/bottom_nav_bar.dart';
import 'home_dashboard_screen.dart';
import 'tasks_screen.dart';
import 'dopamine_stats_screen.dart';
import 'gentle_break_screen.dart';

/// Pantalla contenedora de la barra de navegación inferior.
/// Controla el flujo entre las 4 secciones principales de App Dopa.
class MainNavigationScreen extends StatefulWidget {
  /// Notificador global ligero para permitir saltos de pestaña desde sub-rutas
  /// (por ejemplo, desde SessionSuccessScreen hacia 'Dopamina' o 'Inicio').
  static final ValueNotifier<int> tabNotifier = ValueNotifier<int>(0);

  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  @override
  void initState() {
    super.initState();
    MainNavigationScreen.tabNotifier.addListener(_handleExternalTabChange);
  }

  @override
  void dispose() {
    MainNavigationScreen.tabNotifier.removeListener(_handleExternalTabChange);
    super.dispose();
  }

  void _handleExternalTabChange() {
    if (mounted) {
      setState(() {});
    }
  }

  void _onTabTapped(int index) {
    MainNavigationScreen.tabNotifier.value = index;
  }

  @override
  Widget build(BuildContext context) {
    final currentIndex = MainNavigationScreen.tabNotifier.value;

    final screens = [
      // Tab 0: Inicio / Dashboard
      HomeDashboardScreen(
        onNavigateToTasks: () => _onTabTapped(1),
        onNavigateToBreak: () => _onTabTapped(3),
      ),
      // Tab 1: Tareas
      TasksScreen(
        onBack: () => _onTabTapped(0),
      ),
      // Tab 2: Dopamina
      DopamineStatsScreen(
        onBack: () => _onTabTapped(0),
      ),
      // Tab 3: Pausa / Break
      GentleBreakScreen(
        onBack: () => _onTabTapped(0),
        onGoHome: () => _onTabTapped(0),
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: currentIndex,
        children: screens,
      ),
      bottomNavigationBar: DopaBottomNavBar(
        currentIndex: currentIndex,
        onTap: _onTabTapped,
      ),
    );
  }
}
