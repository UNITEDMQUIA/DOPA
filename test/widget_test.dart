import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:dopa_app/main.dart';
import 'package:dopa_app/screens/main_navigation_screen.dart';
import 'package:dopa_app/services/api_service.dart';
import 'package:dopa_app/services/db_service.dart';
import 'package:dopa_app/models/task_model.dart';
import 'package:dopa_app/models/focus_session_model.dart';
import 'package:dopa_app/models/wellness_record_model.dart';
import 'package:dopa_app/models/reward_model.dart';

void main() {
  setUp(() {
    MainNavigationScreen.tabNotifier.value = 0;
    ApiService.instance.clearSession();
    ApiService.instance.httpClient = null;
  });

  group('1. Pruebas de UI y Navegación Móvil (Flutter Widgets)', () {
    testWidgets('Renderiza el Dashboard Principal y navega por las pestañas',
        (WidgetTester tester) async {
      await tester.pumpWidget(const DopaApp());
      await tester.pumpAndSettle();

      // Verificar elementos de Inicio (HomeDashboardScreen)
      expect(find.text('¡Hola, Fred!'), findsOneWidget);
      expect(find.text('Vamos un paso a la vez'), findsOneWidget);
      expect(find.text('¡Hacer algo fácil!'), findsOneWidget);
      expect(find.text('¡Tomar un break!'), findsOneWidget);
      expect(find.text('Mis micro-tareas'), findsOneWidget);

      // Navegar a Tareas tocando "¡Hacer algo fácil!"
      await tester.tap(find.text('¡Hacer algo fácil!'));
      await tester.pumpAndSettle();

      expect(find.text('Poquito a poquito'), findsOneWidget);
      expect(find.text('Elige solo una para empezar'), findsOneWidget);

      // Navegar a Dopamina desde la barra inferior
      await tester.tap(find.text('Dopamina'));
      await tester.pumpAndSettle();

      expect(find.text('Mi Dopamina hoy'), findsOneWidget);
      expect(find.text('Dopamina reunida'), findsOneWidget);
      expect(find.text('Mi humor'), findsOneWidget);
      expect(find.text('Rachas'), findsOneWidget);

      // Navegar a Pausa / Break desde la barra inferior
      await tester.tap(find.text('Pausa'));
      await tester.pumpAndSettle();

      expect(find.text('Un break suave'), findsOneWidget);
      expect(find.text('Bajemos el volumen'), findsOneWidget);
      expect(find.text('Actividades de bajo estímulo'), findsOneWidget);
    });

    testWidgets('Abre la pantalla de Enfoque Suave desde Inicio',
        (WidgetTester tester) async {
      await tester.pumpWidget(const DopaApp());
      await tester.pumpAndSettle();

      await tester.drag(
        find.byType(SingleChildScrollView).first,
        const Offset(0, -250),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Poner un vaso de agua cerca'));
      await tester.pumpAndSettle();

      expect(find.text('Enfoque suave'), findsOneWidget);
      expect(find.text('TAREA ACTUAL'), findsOneWidget);
      expect(find.text('Micro-pasos'), findsOneWidget);
      expect(find.text('05:00'), findsOneWidget);
    });
  });

  group('2. Pruebas de Integración de Endpoints FastAPI (/api/v1/*)', () {
    test('Autenticación JWT, Dashboard, Tareas, Pomodoro, Gamificación y Metas',
        () async {
      String? capturedIdempotencyKey;
      String? capturedAuthHeader;

      final mockClient = MockClient((http.Request request) async {
        final path = request.url.path;
        final method = request.method;
        capturedAuthHeader = request.headers['Authorization'];

        if (path.endsWith('/health') && method == 'GET') {
          return http.Response(
            jsonEncode({'status': 'ok', 'version': '1.0.0'}),
            200,
          );
        }

        if (path.endsWith('/api/v1/auth/login') && method == 'POST') {
          return http.Response(
            jsonEncode({
              'access_token': 'jwt-access-fred-2026',
              'refresh_token': 'jwt-refresh-fred-2026',
              'token_type': 'bearer',
              'expires_in': 1800,
              'usuario': {
                'id': 1,
                'nombre': 'Fred',
                'correo': 'fred@dopa.app',
                'puntos': 32,
                'nivel': 1,
                'preferencias': {
                  'duracion_concentracion_min': 5,
                  'duracion_descanso_min': 5,
                  'meta_diaria_dopamina': 50,
                },
              },
            }),
            200,
          );
        }

        if (path.endsWith('/api/v1/dashboard') && method == 'GET') {
          return http.Response(
            jsonEncode({
              'panel_id': 1,
              'fecha_actual': '2026-11-08',
              'saludo': '¡Hola, Fred!',
              'subtitulo_amigable': 'Vamos un paso a la vez',
              'puntos_dopamina': 42,
              'meta_diaria_puntos': 50,
              'nivel': 1,
              'estado_energia_hoy': 'a tope',
              'resumen_tareas': {
                'pendientes': 2,
                'completadas_hoy': 2,
                'total_hoy': 4,
              },
              'micro_tareas_hoy': [
                {
                  'id': 1,
                  'id_usuario': 1,
                  'titulo': 'Hacer la cama',
                  'prioridad': 'Baja',
                  'etiqueta_esfuerzo': 'Fácil',
                  'completada': false,
                  'puntos_recompensa': 10,
                  'subtareas': [
                    {
                      'id': 1,
                      'id_tarea': 1,
                      'descripcion': '1. Estirar las sábanas',
                      'completada': true,
                    },
                  ],
                },
              ],
              'rutinas_hoy': [],
              'recordatorios_proximos': [],
            }),
            200,
          );
        }

        if (path.endsWith('/api/v1/dashboard/energy-checkin') &&
            method == 'POST') {
          return http.Response(
            jsonEncode({
              'mensaje': '¡Gracias por escuchar cómo te sientes hoy!',
              'nivel_energia': 'media',
              'humor': 'Con foco',
              'puntos_dopamina': 42,
              'sugerencia_baja_friccion':
                  'Buen ritmo para avanzar Poquito a poquito.',
              'registro_id': 10,
            }),
            201,
          );
        }

        if (path.endsWith('/api/v1/tasks') && method == 'GET') {
          return http.Response(
            jsonEncode({
              'encabezado': 'Poquito a poquito',
              'total': 1,
              'pendientes': 1,
              'completadas': 0,
              'resumen_progreso': '0 de 1 listas',
              'limit': 50,
              'offset': 0,
              'items': [
                {
                  'id': 1,
                  'id_usuario': 1,
                  'titulo': 'Hacer la cama',
                  'prioridad': 'Baja',
                  'etiqueta_esfuerzo': 'Fácil',
                  'completada': false,
                  'puntos_recompensa': 10,
                  'subtareas': [
                    {
                      'id': 1,
                      'id_tarea': 1,
                      'descripcion': '1. Estirar las sábanas',
                      'completada': true,
                    },
                  ],
                },
              ],
            }),
            200,
          );
        }

        if (path.endsWith('/api/v1/tasks/1/complete') && method == 'POST') {
          capturedIdempotencyKey = request.headers['Idempotency-Key'];
          return http.Response(
            jsonEncode({
              'mensaje_celebracion': '¡Lo hiciste, Fred!',
              'puntos_ganados': 10,
              'puntos_totales': 52,
              'nivel_actual': 2,
              'idempotente': false,
              'tarea': {
                'id': 1,
                'id_usuario': 1,
                'titulo': 'Hacer la cama',
                'prioridad': 'Baja',
                'etiqueta_esfuerzo': 'Fácil',
                'completada': true,
                'puntos_recompensa': 10,
                'subtareas': [],
              },
              'recompensas_desbloqueadas': [],
            }),
            200,
          );
        }

        if (path.endsWith('/api/v1/pomodoro/sessions') && method == 'POST') {
          return http.Response(
            jsonEncode({
              'id': 77,
              'id_usuario': 1,
              'id_tarea': 1,
              'duracionconcentracion': 5,
              'duraciondescanso': 5,
              'sesionescompletadas': 0,
            }),
            201,
          );
        }

        if (path.endsWith('/api/v1/pomodoro/sessions/77/complete') &&
            method == 'POST') {
          return http.Response(
            jsonEncode({
              'mensaje': 'Ciclo completado',
              'estado': 'completada',
              'puntos_ganados': 5,
              'puntos_totales': 57,
              'nivel_actual': 2,
              'idempotente': false,
              'sugerencia_descanso': 'Toma un break suave',
              'sesion': {
                'id': 77,
                'id_usuario': 1,
                'id_tarea': 1,
                'duracionconcentracion': 5,
                'duraciondescanso': 5,
                'sesionescompletadas': 1,
              },
            }),
            200,
          );
        }

        if (path.endsWith('/api/v1/gamification/summary') && method == 'GET') {
          return http.Response(
            jsonEncode({
              'encabezado': 'Mi Dopamina hoy',
              'puntos_totales': 57,
              'nivel': 2,
              'meta_diaria_puntos': 50,
              'porcentaje_meta_diaria': 100.0,
            }),
            200,
          );
        }

        if (path.endsWith('/api/v1/gamification/rewards') && method == 'POST') {
          return http.Response(
            jsonEncode({
              'id': 9,
              'nombre': 'Pausa completada',
              'costopuntos': 5,
              'desbloqueada': true,
            }),
            201,
          );
        }

        if (path.endsWith('/api/v1/personal-records') && method == 'POST') {
          return http.Response(
            jsonEncode({
              'id': 15,
              'id_usuario': 1,
              'nombre': 'Estado emocional: conFoco',
              'valorobjetivo': 5.0,
              'valoractual': 4.0,
              'progresoporcentaje': 80.0,
            }),
            201,
          );
        }

        if (path.endsWith('/api/v1/financial-goals') && method == 'GET') {
          return http.Response(
            jsonEncode({
              'total': 1,
              'limit': 20,
              'offset': 0,
              'items': [
                {
                  'id': 1,
                  'id_usuario': 1,
                  'nombre': 'Fondo de tranquilidad',
                  'valorobjetivo': 500.0,
                  'valoractual': 200.0,
                  'progresoporcentaje': 40.0,
                  'meta_alcanzada': false,
                },
              ],
            }),
            200,
          );
        }

        return http.Response(jsonEncode({'detail': 'Not Found'}), 404);
      });

      ApiService.instance.httpClient = mockClient;

      // 1. Verificar Health Check
      final health = await ApiService.instance.checkHealth();
      expect(health['status'], equals('ok'));

      // 2. Verificar Auto-Autenticación y Dashboard via DBService
      final usuario = await DBService.instance.getUsuario();
      expect(ApiService.instance.isAuthenticated, isTrue);
      expect(capturedAuthHeader, equals('Bearer jwt-access-fred-2026'));
      expect(usuario.nombre, equals('Fred'));
      expect(usuario.dopaminaActual, equals(42));
      expect(usuario.energiaNivel, greaterThan(0.7));

      // 3. Verificar listado y mapeo de tareas con micro-pasos
      final tareas = await DBService.instance.obtenerTareas();
      expect(tareas, isNotEmpty);
      expect(tareas.first.titulo, equals('Hacer la cama'));
      expect(tareas.first.microPasos.length, equals(1));

      // 4. Verificar completado idempotente de tarea
      await DBService.instance.actualizarTarea(
        TareaBloque(
          id: 1,
          titulo: 'Hacer la cama',
          subtitulo: '¡Hecho!',
          duracionMinutos: 5,
          estado: EstadoTarea.hecho,
        ),
      );
      expect(capturedIdempotencyKey, isNotNull);
      expect(capturedIdempotencyKey, startsWith('task-complete-1-'));

      // 5. Verificar sesión Pomodoro completada
      final sessionId = await DBService.instance.registrarSesion(
        SesionEnfoque(tareaId: 1, duracionSegundos: 300, completada: true),
      );
      expect(sessionId, equals(77));

      // 6. Verificar resumen de gamificación y recompensas
      final totalDopamina = await DBService.instance.obtenerTotalDopaminaHoy();
      expect(totalDopamina, equals(57));

      final rewardId = await DBService.instance.agregarRecompensa(
        Recompensa(titulo: 'Pausa completada', puntosDopamina: 5),
      );
      expect(rewardId, equals(9));

      // 7. Verificar registro personal y recomendación IA
      final recordId = await DBService.instance.guardarRegistroBienestar(
        RegistroBienestar(humor: TipoHumor.conFoco, nivelEnergia: 0.8),
      );
      expect(recordId, equals(15));

      final aiRec = await ApiService.instance.fetchAIRecommendation(
        nivelEnergia: 0.5,
        humor: TipoHumor.conFoco,
      );
      expect(aiRec.recommendation, contains('Poquito a poquito'));

      // 8. Verificar metas financieras
      final goals = await ApiService.instance.listFinancialGoals();
      expect(goals['total'], equals(1));
    });
  });
}
