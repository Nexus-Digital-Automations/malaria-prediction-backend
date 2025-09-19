/// Test Helper Functions and Utilities
///
/// Provides common test setup functions, widget wrappers, and utility methods
/// for consistent testing across the malaria prediction Flutter application.

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:malaria_frontend/core/theme/bloc/theme_bloc.dart';
import 'package:malaria_frontend/app/routes/app_router.dart';
import 'package:malaria_frontend/injection_container.dart' as di;

/// Creates a testable widget wrapped with necessary providers and routing
Widget createTestWidget({
  required Widget child,
  List<BlocProvider>? providers,
  bool includeRouter = false,
  ThemeMode themeMode = ThemeMode.light,
}) {
  final widget = MediaQuery(
    data: const MediaQueryData(
      size: Size(375, 667), // iPhone SE size
      devicePixelRatio: 2.0,
      textScaleFactor: 1.0,
    ),
    child: MaterialApp(
      home: Scaffold(body: child),
      theme: ThemeData.light(),
      darkTheme: ThemeData.dark(),
      themeMode: themeMode,
    ),
  );

  if (providers != null && providers.isNotEmpty) {
    return MultiBlocProvider(
      providers: providers,
      child: widget,
    );
  }

  return widget;
}

/// Creates a testable widget with full app context including routing
Widget createAppTestWidget({
  required Widget child,
  List<BlocProvider>? providers,
  String initialRoute = '/',
}) {
  final appRouter = AppRouter();

  final widget = MaterialApp.router(
    routerConfig: appRouter.router,
    theme: ThemeData.light(),
    darkTheme: ThemeData.dark(),
    themeMode: ThemeMode.light,
  );

  if (providers != null && providers.isNotEmpty) {
    return MultiBlocProvider(
      providers: providers,
      child: widget,
    );
  }

  return widget;
}

/// Pumps and settles widget with common test setup
Future<void> pumpAndSettleWidget(
  WidgetTester tester,
  Widget widget, {
  Duration? duration,
  EnginePhase phase = EnginePhase.sendSemanticsUpdate,
}) async {
  await tester.pumpWidget(widget);
  await tester.pumpAndSettle(duration, phase);
}

/// Helper for testing BLoC states with multiple pumps
Future<void> pumpMultipleFrames(
  WidgetTester tester, {
  int frames = 3,
  Duration duration = const Duration(milliseconds: 100),
}) async {
  for (int i = 0; i < frames; i++) {
    await tester.pump(duration);
  }
}

/// Creates a mock HTTP client response
String createMockResponse(Map<String, dynamic> data) {
  return '''
{
  "success": true,
  "data": ${data.toString()},
  "message": "Success",
  "timestamp": "${DateTime.now().toIso8601String()}"
}
''';
}

/// Test data generators for consistent mock data
class TestDataGenerator {
  /// Generates test risk data with realistic values
  static Map<String, dynamic> generateRiskData({
    String? region,
    double? riskScore,
    String? riskLevel,
    DateTime? timestamp,
  }) {
    return {
      'id': 'risk-${DateTime.now().millisecondsSinceEpoch}',
      'region': region ?? 'Nairobi',
      'riskScore': riskScore ?? 0.65,
      'riskLevel': riskLevel ?? 'medium',
      'environmentalFactors': {
        'temperature': 25.5,
        'rainfall': 150.0,
        'humidity': 75.0,
        'vegetation': 0.8,
      },
      'timestamp': (timestamp ?? DateTime.now()).toIso8601String(),
      'coordinates': {
        'latitude': -1.2921,
        'longitude': 36.8219,
      },
    };
  }

  /// Generates test prediction data
  static Map<String, dynamic> generatePredictionData({
    String? region,
    int? daysAhead,
    double? confidence,
  }) {
    return {
      'id': 'prediction-${DateTime.now().millisecondsSinceEpoch}',
      'region': region ?? 'Nairobi',
      'daysAhead': daysAhead ?? 7,
      'predictedRiskLevel': 'high',
      'confidence': confidence ?? 0.87,
      'factors': [
        {'name': 'temperature_trend', 'impact': 0.3},
        {'name': 'rainfall_pattern', 'impact': 0.4},
        {'name': 'population_density', 'impact': 0.2},
        {'name': 'vector_activity', 'impact': 0.1},
      ],
      'createdAt': DateTime.now().toIso8601String(),
    };
  }

  /// Generates test alert data
  static Map<String, dynamic> generateAlertData({
    String? severity,
    String? region,
    String? type,
  }) {
    return {
      'id': 'alert-${DateTime.now().millisecondsSinceEpoch}',
      'severity': severity ?? 'high',
      'type': type ?? 'outbreak_risk',
      'region': region ?? 'Nairobi',
      'title': 'High Malaria Risk Alert',
      'description': 'Increased malaria risk detected in the region.',
      'actionRequired': true,
      'recommendations': [
        'Increase vector control measures',
        'Enhance community awareness',
        'Monitor health facility capacity',
      ],
      'issuedAt': DateTime.now().toIso8601String(),
      'expiresAt': DateTime.now().add(const Duration(days: 7)).toIso8601String(),
    };
  }

  /// Generates test user data
  static Map<String, dynamic> generateUserData({
    String? role,
    String? region,
  }) {
    return {
      'id': 'user-${DateTime.now().millisecondsSinceEpoch}',
      'email': 'test@example.com',
      'name': 'Test User',
      'role': role ?? 'healthcare_worker',
      'region': region ?? 'Nairobi',
      'permissions': ['view_data', 'create_reports'],
      'lastLogin': DateTime.now().toIso8601String(),
      'isActive': true,
    };
  }

  /// Generates test analytics data
  static Map<String, dynamic> generateAnalyticsData({
    String? timeframe,
    String? region,
  }) {
    return {
      'timeframe': timeframe ?? 'last_30_days',
      'region': region ?? 'Nairobi',
      'metrics': {
        'total_predictions': 156,
        'accuracy_rate': 0.89,
        'alerts_issued': 12,
        'interventions_triggered': 8,
      },
      'trends': {
        'risk_trend': 'increasing',
        'prediction_accuracy': 'stable',
        'alert_frequency': 'decreasing',
      },
      'comparisons': {
        'previous_period': {
          'total_predictions': 142,
          'accuracy_rate': 0.85,
        },
      },
      'generatedAt': DateTime.now().toIso8601String(),
    };
  }
}

/// Extension methods for common test assertions
extension TestExtensions on WidgetTester {
  /// Finds widget by type and optional matcher
  Finder findWidgetByType<T extends Widget>({Finder? matcher}) {
    return matcher != null ? find.descendant(of: matcher, matching: find.byType(T)) : find.byType(T);
  }

  /// Finds text widget with exact text
  Finder findTextExact(String text) {
    return find.text(text);
  }

  /// Finds text widget containing partial text
  Finder findTextContaining(String text) {
    return find.textContaining(text);
  }

  /// Taps and settles
  Future<void> tapAndSettle(Finder finder, {Duration? settleDuration}) async {
    await tap(finder);
    await pumpAndSettle(settleDuration);
  }

  /// Enters text and settles
  Future<void> enterTextAndSettle(Finder finder, String text) async {
    await enterText(finder, text);
    await pumpAndSettle();
  }

  /// Scrolls until visible and taps
  Future<void> scrollToAndTap(
    Finder finder, {
    Finder? scrollable,
    double delta = 100.0,
    AxisDirection scrollDirection = AxisDirection.down,
  }) async {
    await scrollUntilVisible(
      finder,
      delta,
      scrollable: scrollable ?? find.byType(Scrollable).first,
    );
    await tapAndSettle(finder);
  }
}

/// Mock class registration helper
void registerTestMocks() {
  // Register fallback values for mocktail
  registerFallbackValue(Uri.parse('https://test.example.com'));
  registerFallbackValue(const Duration(seconds: 1));
  registerFallbackValue(DateTime.now());
  registerFallbackValue(<String, dynamic>{});
  registerFallbackValue(<String>[]);
}

/// Performance test helper
class PerformanceTestHelper {
  static Future<Duration> measureExecutionTime(Future<void> Function() action) async {
    final stopwatch = Stopwatch()..start();
    await action();
    stopwatch.stop();
    return stopwatch.elapsed;
  }

  static Future<void> expectExecutionTime(
    Future<void> Function() action,
    Duration maxDuration, {
    String? description,
  }) async {
    final duration = await measureExecutionTime(action);
    expect(
      duration,
      lessThan(maxDuration),
      reason: description ?? 'Execution time should be less than $maxDuration, but was $duration',
    );
  }
}

/// Memory usage test helper (for integration/performance tests)
class MemoryTestHelper {
  static int getCurrentMemoryUsage() {
    // Note: This is a simplified approach for testing
    // In real scenarios, you'd use more sophisticated memory profiling
    return ProcessInfo.currentRss;
  }

  static Future<void> expectMemoryUsageBelow(
    int maxBytes,
    Future<void> Function() action, {
    String? description,
  }) async {
    final initialMemory = getCurrentMemoryUsage();
    await action();
    final finalMemory = getCurrentMemoryUsage();
    final memoryIncrease = finalMemory - initialMemory;

    expect(
      memoryIncrease,
      lessThan(maxBytes),
      reason: description ?? 'Memory increase should be less than $maxBytes bytes, but was $memoryIncrease bytes',
    );
  }
}

/// Process info helper for performance testing
class ProcessInfo {
  static int get currentRss {
    // This is a mock implementation for testing
    // In real scenarios, you'd use platform-specific APIs
    return 50 * 1024 * 1024; // 50MB mock value
  }
}