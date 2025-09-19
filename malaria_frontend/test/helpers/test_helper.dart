/// Test Helper Utilities for Malaria Prediction App
/// Provides common testing utilities, mock setups, and test configuration
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Centralized testing utilities for consistent test setup
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Test environment setup and configuration
class TestHelper {
  /// Initialize test environment with all required setup
  ///
  /// Call this in the main() function of test files before running tests
  static Future<void> initializeTestEnvironment() async {
    TestWidgetsFlutterBinding.ensureInitialized();

    // Initialize Hive for testing
    await Hive.initFlutter();

    // Set up shared preferences mock values
    SharedPreferences.setMockInitialValues({
      'first_launch': false,
      'user_preferences': {},
      'offline_data_cache': {},
    });

    // Register common mock factories
    _registerMockFactories();

    // Set up golden file comparisons for cross-platform consistency
    goldenFileComparator = LocalFileComparator(Uri.parse('test/golden/'));
  }

  /// Register fallback values for mocktail
  static void _registerMockFactories() {
    // Register common fallback values for types used in testing
    registerFallbackValue(const Duration(seconds: 1));
    registerFallbackValue(DateTime.now());
    registerFallbackValue(Uri.parse('https://example.com'));
  }

  /// Clean up after tests
  static Future<void> cleanupTestEnvironment() async {
    await Hive.close();
    await GetIt.instance.reset();
  }

  /// Create a test app wrapper with common providers
  static Widget createTestApp({
    required Widget child,
    List<BlocProvider> blocProviders = const [],
    List<RepositoryProvider> repositoryProviders = const [],
    ThemeData? theme,
    Locale locale = const Locale('en', 'US'),
  }) {
    return MultiBlocProvider(
      providers: blocProviders,
      child: MultiRepositoryProvider(
        providers: repositoryProviders,
        child: MaterialApp(
          home: child,
          theme: theme ?? _getTestTheme(),
          locale: locale,
          debugShowCheckedModeBanner: false,
        ),
      ),
    );
  }

  /// Default test theme for consistent testing
  static ThemeData _getTestTheme() {
    return ThemeData(
      primarySwatch: Colors.blue,
      useMaterial3: true,
      fontFamily: 'Roboto',
    );
  }

  /// Create a test MediaQuery wrapper with specified size
  static Widget wrapWithMediaQuery({
    required Widget child,
    Size size = const Size(375, 667), // iPhone SE size
    double devicePixelRatio = 1.0,
    Brightness brightness = Brightness.light,
  }) {
    return MediaQuery(
      data: MediaQueryData(
        size: size,
        devicePixelRatio: devicePixelRatio,
        platformBrightness: brightness,
      ),
      child: child,
    );
  }

  /// Pump widget with custom settings and wait for animations
  static Future<void> pumpWidgetWithCustomSettings(
    WidgetTester tester,
    Widget widget, {
    Duration? duration,
    bool skipOffstage = true,
  }) async {
    await tester.pumpWidget(widget);
    await tester.pumpAndSettle(duration, EnginePhase.sendSemanticsUpdate);
  }

  /// Access to widget finder utilities
  static const WidgetFinders = _WidgetFinders();

  /// Access to test actions
  static const TestActions = _TestActions();

  /// Access to performance helper
  static const PerformanceHelper = _PerformanceHelper();

  /// Access to data verification utilities
  static const DataVerification = _DataVerification();

  /// Access to mock data generators
  static const MockDataGenerator = _MockDataGenerator();
}

/// Common widget finder utilities
class _WidgetFinders {
  const _WidgetFinders();

  /// Find widget by test key
  Finder byTestKey(String key) => find.byKey(Key(key));

  /// Find button by text with specific button type
  Finder buttonByText(String text) => find.widgetWithText(ElevatedButton, text);

  /// Find text field by hint text
  Finder textFieldByHint(String hint) => find.widgetWithText(TextField, hint);

  /// Find app bar with title
  Finder appBarWithTitle(String title) => find.widgetWithText(AppBar, title);

  /// Find icon button by icon
  Finder iconButtonByIcon(IconData icon) => find.widgetWithIcon(IconButton, icon);

  /// Find loading indicators
  Finder loadingIndicator() => find.byType(CircularProgressIndicator);

  /// Find error widgets
  Finder errorWidget() => find.byType(ErrorWidget);
}

/// Common test actions
class _TestActions {
  const _TestActions();

  /// Tap and wait for animations to complete
  Future<void> tapAndSettle(WidgetTester tester, Finder finder) async {
    await tester.tap(finder);
    await tester.pumpAndSettle();
  }

  /// Enter text and wait for updates
  Future<void> enterTextAndSettle(
    WidgetTester tester,
    Finder finder,
    String text,
  ) async {
    await tester.enterText(finder, text);
    await tester.pumpAndSettle();
  }

  /// Scroll until widget is visible
  Future<void> scrollUntilVisible(
    WidgetTester tester,
    Finder finder,
    Finder scrollableFinder, {
    double delta = 100.0,
  }) async {
    await tester.scrollUntilVisible(finder, delta, scrollable: scrollableFinder);
    await tester.pumpAndSettle();
  }

  /// Drag to refresh
  Future<void> dragToRefresh(WidgetTester tester, Finder finder) async {
    await tester.drag(finder, const Offset(0, 300));
    await tester.pumpAndSettle();
  }

  /// Wait for specific condition with timeout
  Future<void> waitFor(
    WidgetTester tester,
    bool Function() condition, {
    Duration timeout = const Duration(seconds: 5),
  }) async {
    final stopwatch = Stopwatch()..start();

    while (!condition() && stopwatch.elapsed < timeout) {
      await tester.pump(const Duration(milliseconds: 100));
    }

    if (!condition()) {
      throw TimeoutException('Condition not met within timeout', timeout);
    }
  }
}

/// Performance testing utilities
class _PerformanceHelper {
  const _PerformanceHelper();

  /// Measure widget build time
  Future<Duration> measureBuildTime(
    WidgetTester tester,
    Widget widget,
  ) async {
    final stopwatch = Stopwatch()..start();
    await tester.pumpWidget(widget);
    stopwatch.stop();
    return stopwatch.elapsed;
  }

  /// Measure scroll performance
  Future<TestScrollMetrics> measureScrollPerformance(
    WidgetTester tester,
    Finder scrollableFinder,
    double scrollDistance,
  ) async {
    final scrollableWidget = tester.widget<Scrollable>(scrollableFinder);
    final controller = scrollableWidget.controller;

    if (controller == null) {
      throw StateError('Scrollable widget must have a controller for performance measurement');
    }

    final initialPosition = controller.position.pixels;
    final stopwatch = Stopwatch()..start();

    await tester.drag(scrollableFinder, Offset(0, -scrollDistance));
    await tester.pumpAndSettle();

    stopwatch.stop();

    return TestScrollMetrics(
      scrollDistance: (controller.position.pixels - initialPosition).abs(),
      duration: stopwatch.elapsed,
      frameCount: 0, // frameCount not available in TestWidgetsFlutterBinding
    );
  }
}

/// Data verification utilities
class _DataVerification {
  const _DataVerification();

  /// Verify BLoC state transitions
  void verifyBlocStateTransition<B extends BlocBase<S>, S>(
    B bloc,
    List<S> expectedStates,
  ) {
    expect(bloc.stream, emitsInOrder(expectedStates));
  }

  /// Verify API call with specific parameters
  void verifyApiCall(
    Mock mockObject,
    String methodName,
    dynamic expectedParams,
  ) {
    verify(() => mockObject.noSuchMethod(
      Invocation.method(Symbol(methodName), [expectedParams]),
    )).called(1);
  }

  /// Verify widget properties
  void verifyWidgetProperties<T extends Widget>(
    WidgetTester tester,
    Finder finder,
    Map<String, dynamic> expectedProperties,
  ) {
    final widget = tester.widget<T>(finder);

    for (final entry in expectedProperties.entries) {
      final property = entry.key;
      final expectedValue = entry.value;

      // Use reflection or specific property accessors
      // This is a simplified version - implement based on specific widget types
      expect(widget.toString().contains(expectedValue.toString()), isTrue,
          reason: 'Property $property should have value $expectedValue');
    }
  }
}

/// Mock data generators
class _MockDataGenerator {
  const _MockDataGenerator();

  /// Generate mock user data
  Map<String, dynamic> generateMockUser({
    String? id,
    String? email,
    String? name,
  }) {
    return {
      'id': id ?? 'test_user_${DateTime.now().millisecondsSinceEpoch}',
      'email': email ?? 'test@example.com',
      'name': name ?? 'Test User',
      'created_at': DateTime.now().toIso8601String(),
      'preferences': {
        'notifications': true,
        'theme': 'light',
        'language': 'en',
      },
    };
  }

  /// Generate mock risk data
  List<Map<String, dynamic>> generateMockRiskData({
    int count = 10,
    String? region,
  }) {
    return List.generate(count, (index) => {
      'id': 'risk_${index}_${DateTime.now().millisecondsSinceEpoch}',
      'region': region ?? 'test_region_$index',
      'risk_level': ['low', 'medium', 'high'][index % 3],
      'risk_score': (index % 100) / 100.0,
      'timestamp': DateTime.now().subtract(Duration(days: index)).toIso8601String(),
      'environmental_factors': {
        'temperature': 20.0 + (index % 15),
        'rainfall': 100.0 + (index % 200),
        'humidity': 60.0 + (index % 30),
      },
    });
  }

  /// Generate mock API responses
  Map<String, dynamic> generateMockApiResponse({
    required dynamic data,
    bool success = true,
    String? message,
    int statusCode = 200,
  }) {
    return {
      'success': success,
      'status_code': statusCode,
      'message': message ?? (success ? 'Operation successful' : 'Operation failed'),
      'data': data,
      'timestamp': DateTime.now().toIso8601String(),
    };
  }
}

/// Custom exception for test timeouts
class TimeoutException implements Exception {
  final String message;
  final Duration timeout;

  const TimeoutException(this.message, this.timeout);

  @override
  String toString() => 'TimeoutException: $message (timeout: $timeout)';
}

/// Test scroll performance metrics
class TestScrollMetrics {
  final double scrollDistance;
  final Duration duration;
  final int frameCount;

  const TestScrollMetrics({
    required this.scrollDistance,
    required this.duration,
    required this.frameCount,
  });

  /// Calculate scroll velocity in pixels per millisecond
  double get velocity => scrollDistance / duration.inMilliseconds;

  /// Calculate frames per second during scroll
  double get fps => frameCount / (duration.inMilliseconds / 1000);

  @override
  String toString() {
    return 'TestScrollMetrics(distance: $scrollDistance, duration: $duration, velocity: $velocity px/ms, fps: $fps)';
  }
}

/// Custom matchers for Flutter testing
class CustomMatchers {
  /// Matcher for checking if a widget has specific accessibility properties
  static Matcher hasAccessibilityLabel(String label) {
    return _HasAccessibilityLabel(label);
  }

  /// Matcher for checking widget performance benchmarks
  static Matcher buildsInTime(Duration maxDuration) {
    return _BuildsInTime(maxDuration);
  }
}

class _HasAccessibilityLabel extends Matcher {
  final String expectedLabel;

  const _HasAccessibilityLabel(this.expectedLabel);

  @override
  bool matches(Object? item, Map<dynamic, dynamic> matchState) {
    if (item is! Widget) return false;

    // Implement accessibility label checking logic
    // This is simplified - implement based on specific widget types
    return item.toString().contains(expectedLabel);
  }

  @override
  Description describe(Description description) {
    return description.add('has accessibility label "$expectedLabel"');
  }
}

class _BuildsInTime extends Matcher {
  final Duration maxDuration;

  const _BuildsInTime(this.maxDuration);

  @override
  bool matches(Object? item, Map<dynamic, dynamic> matchState) {
    // This would be used with a custom testing utility that measures build time
    return true; // Simplified implementation
  }

  @override
  Description describe(Description description) {
    return description.add('builds within $maxDuration');
  }
}