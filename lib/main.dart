import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'theme/app_theme.dart';
import 'screens/main_navigation_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Configuración de barra de estado translúcida acorde al estilo pastel
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: AppTheme.surfaceWhite,
      systemNavigationBarIconBrightness: Brightness.dark,
    ),
  );

  runApp(const DopaApp());
}

class DopaApp extends StatelessWidget {
  const DopaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dopa',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.themeData,
      // En pantallas anchas (Web / Desktop), enmarca la app con proporciones móviles
      // fieles al diseño original (396x860); en dispositivos móviles ocupa el 100%.
      builder: (context, child) {
        return LayoutBuilder(
          builder: (context, constraints) {
            if (constraints.maxWidth <= 500) {
              return child ?? const SizedBox.shrink();
            }

            return Container(
              color: const Color(0xFFE7EFEA),
              alignment: Alignment.center,
              padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: 400,
                  maxHeight: 868,
                ),
                child: Container(
                  decoration: BoxDecoration(
                    color: AppTheme.background,
                    borderRadius: BorderRadius.circular(36),
                    border: Border.all(
                      color: AppTheme.borderDark,
                      width: 2.5,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x1F1E3830),
                        blurRadius: 28,
                        offset: Offset(0, 12),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(33.5),
                    child: MediaQuery(
                      data: MediaQuery.of(context).copyWith(
                        size: Size(
                          400,
                          constraints.maxHeight > 908
                              ? 868
                              : (constraints.maxHeight - 40).clamp(480, 868),
                        ),
                      ),
                      child: child ?? const SizedBox.shrink(),
                    ),
                  ),
                ),
              ),
            );
          },
        );
      },
      home: const MainNavigationScreen(),
    );
  }
}
