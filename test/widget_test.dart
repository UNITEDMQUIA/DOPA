import 'package:flutter_test/flutter_test.dart';
import 'package:dopa_app/main.dart';

void main() {
  testWidgets('DopaApp renders Home Dashboard cleanly', (WidgetTester tester) async {
    await tester.pumpWidget(const DopaApp());
    await tester.pumpAndSettle();

    expect(find.text('¡Hola, Fred!'), findsOneWidget);
    expect(find.text('Vamos un paso a la vez'), findsOneWidget);
  });
}
