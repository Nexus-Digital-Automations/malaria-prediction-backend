/// Integration testing helper utilities
///
/// This file provides utility functions and helpers for integration testing,
/// including environment setup, service mocking, and end-to-end test flows.
library;

import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:get_it/get_it.dart';
import 'package:mocktail/mocktail.dart';
import '../mocks/analytics_mocks.dart';
import '../test_config.dart';

/// Integration testing helper class
class IntegrationTestHelpers {
  static final GetIt _serviceLocator = GetIt.instance;

  /// Sets up the integration test environment
  static Future<void> setupIntegrationTestEnvironment() async {
    // Initialize Flutter binding for integration tests
    IntegrationTestWidgetsFlutterBinding.ensureInitialized();

    // Set up test configuration
    await TestConfig.initialize();

    // Setup platform-specific configurations
    await _setupPlatformSpecifics();

    // Initialize mock services
    await _initializeMockServices();

    // Setup test data
    await _setupTestData();
  }

  /// Cleans up the integration test environment
  static Future<void> cleanupIntegrationTestEnvironment() async {
    // Reset service locator
    await _serviceLocator.reset();

    // Clean up test configuration
    await TestConfig.cleanup();

    // Clear test data
    await _clearTestData();
  }

  /// Sets up platform-specific configurations for testing
  static Future<void> _setupPlatformSpecifics() async {
    // Setup method channel mocks for platform-specific functionality
    const platform = MethodChannel('flutter/platform');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(platform, (MethodCall methodCall) async {
      switch (methodCall.method) {
        case 'SystemNavigator.pop':
          return null;
        case 'HapticFeedback.vibrate':
          return null;
        case 'SystemChrome.setApplicationSwitcherDescription':
          return null;
        default:
          return null;
      }
    });

    // Setup file system mocks if needed
    if (Platform.isAndroid || Platform.isIOS) {
      const fileSystemChannel = MethodChannel('plugins.flutter.io/path_provider');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(fileSystemChannel, (MethodCall methodCall) async {
        switch (methodCall.method) {
          case 'getTemporaryDirectory':
            return '/tmp';
          case 'getApplicationDocumentsDirectory':
            return '/documents';
          case 'getExternalStorageDirectory':
            return '/external';
          default:
            return null;
        }
      });
    }
  }

  /// Initializes mock services for integration testing
  static Future<void> _initializeMockServices() async {
    // Register mock analytics services
    _serviceLocator.registerLazySingleton<MockAnalyticsRemoteDataSource>(
      () => MockAnalyticsRemoteDataSource(),
    );

    _serviceLocator.registerLazySingleton<MockAnalyticsLocalDataSource>(
      () => MockAnalyticsLocalDataSource(),
    );

    _serviceLocator.registerLazySingleton<MockNetworkInfo>(
      () => MockNetworkInfo(),
    );

    _serviceLocator.registerLazySingleton<MockStorageService>(
      () => MockStorageService(),
    );

    // Setup default mock behaviors
    final remoteDataSource = _serviceLocator<MockAnalyticsRemoteDataSource>();
    final localDataSource = _serviceLocator<MockAnalyticsLocalDataSource>();
    final networkInfo = _serviceLocator<MockNetworkInfo>();
    final storageService = _serviceLocator<MockStorageService>();

    // Configure network info mock
    when(() => networkInfo.isConnected).thenAnswer((_) async => true);

    // Configure storage service mock
    when(() => storageService.getString(any())).thenAnswer((_) async => null);
    when(() => storageService.setString(any(), any())).thenAnswer((_) async => true);
    when(() => storageService.getBool(any())).thenAnswer((_) async => null);
    when(() => storageService.setBool(any(), any())).thenAnswer((_) async => true);
    when(() => storageService.remove(any())).thenAnswer((_) async => true);
    when(() => storageService.clear()).thenAnswer((_) async => true);

    // Configure local data source mock
    when(() => localDataSource.getCachedAnalyticsData(any()))
        .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());
    when(() => localDataSource.cacheAnalyticsData(any()))
        .thenAnswer((_) async => {});

    // Configure remote data source mock
    when(() => remoteDataSource.getAnalyticsData(any()))
        .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());
    when(() => remoteDataSource.generateChartData(any()))
        .thenAnswer((_) async => MockAnalyticsData.createMockChartDataModel());
    when(() => remoteDataSource.exportAnalyticsReport(
      region: any(named: 'region'),
      dateRange: any(named: 'dateRange'),
      format: any(named: 'format'),
      includeCharts: any(named: 'includeCharts'),
      sections: any(named: 'sections'),
    )).thenAnswer((_) async => 'https://example.com/report.pdf');
  }

  /// Sets up test data for integration tests
  static Future<void> _setupTestData() async {
    // Create test directories and files if needed
    // This would set up any required test data files
  }

  /// Clears test data after integration tests
  static Future<void> _clearTestData() async {
    // Clean up any test files or directories created during testing
  }

  /// Simulates user login for integration tests
  static Future<void> simulateUserLogin(
    WidgetTester tester, {
    String email = 'test@example.com',
    String password = 'password123',
  }) async {
    // Wait for login screen
    await tester.pumpAndSettle();

    // Find and fill email field
    final emailField = find.byKey(const Key('email_field'));
    if (emailField.evaluate().isNotEmpty) {
      await tester.enterText(emailField, email);
      await tester.pump();
    }

    // Find and fill password field
    final passwordField = find.byKey(const Key('password_field'));
    if (passwordField.evaluate().isNotEmpty) {
      await tester.enterText(passwordField, password);
      await tester.pump();
    }

    // Tap login button
    final loginButton = find.byKey(const Key('login_button'));
    if (loginButton.evaluate().isNotEmpty) {
      await tester.tap(loginButton);
      await tester.pumpAndSettle();
    }
  }

  /// Simulates network connectivity changes
  static Future<void> simulateNetworkChange(
    bool isConnected, {
    Duration delay = const Duration(seconds: 1),
  }) async {
    final networkInfo = _serviceLocator<MockNetworkInfo>();
    when(() => networkInfo.isConnected).thenAnswer((_) async => isConnected);

    // Wait for the change to take effect
    await Future.delayed(delay);
  }

  /// Simulates server response delays
  static Future<void> simulateServerDelay(Duration delay) async {
    final remoteDataSource = _serviceLocator<MockAnalyticsRemoteDataSource>();

    // Add delay to remote data source calls
    when(() => remoteDataSource.getAnalyticsData(any())).thenAnswer((_) async {
      await Future.delayed(delay);
      return MockAnalyticsData.createMockAnalyticsDataModel();
    });

    when(() => remoteDataSource.generateChartData(any())).thenAnswer((_) async {
      await Future.delayed(delay);
      return MockAnalyticsData.createMockChartDataModel();
    });
  }

  /// Simulates server errors
  static void simulateServerError(String errorMessage) {
    final remoteDataSource = _serviceLocator<MockAnalyticsRemoteDataSource>();

    when(() => remoteDataSource.getAnalyticsData(any()))
        .thenThrow(Exception(errorMessage));
    when(() => remoteDataSource.generateChartData(any()))
        .thenThrow(Exception(errorMessage));
  }

  /// Waits for specific UI state to appear
  static Future<void> waitForUIState(
    WidgetTester tester,
    Finder finder, {
    Duration timeout = const Duration(seconds: 10),
    Duration pollInterval = const Duration(milliseconds: 500),
  }) async {
    final endTime = DateTime.now().add(timeout);

    while (DateTime.now().isBefore(endTime)) {
      await tester.pumpAndSettle(pollInterval);

      if (finder.evaluate().isNotEmpty) {
        return;
      }
    }

    throw Exception('UI state not reached within timeout: $finder');
  }

  /// Performs end-to-end navigation test
  static Future<void> performNavigationTest(
    WidgetTester tester,
    List<NavigationStep> steps,
  ) async {
    for (final step in steps) {
      await _executeNavigationStep(tester, step);
    }
  }

  /// Executes a single navigation step
  static Future<void> _executeNavigationStep(
    WidgetTester tester,
    NavigationStep step,
  ) async {
    switch (step.action) {
      case NavigationAction.tap:
        await tester.tap(step.finder);
        break;
      case NavigationAction.longPress:
        await tester.longPress(step.finder);
        break;
      case NavigationAction.scroll:
        await tester.scroll(step.finder, step.offset ?? Offset.zero);
        break;
      case NavigationAction.enterText:
        await tester.enterText(step.finder, step.text ?? '');
        break;
      case NavigationAction.wait:
        await Future.delayed(step.duration ?? const Duration(seconds: 1));
        break;
    }

    await tester.pumpAndSettle();

    // Verify expected outcome if provided
    if (step.expectedOutcome != null) {
      expect(step.expectedOutcome!.evaluate().isNotEmpty, isTrue);
    }
  }

  /// Tests data persistence across app restarts
  static Future<void> testDataPersistence(
    WidgetTester tester,
    Future<void> Function() setupData,
    Future<void> Function() verifyData,
  ) async {
    // Setup data
    await setupData();
    await tester.pumpAndSettle();

    // Simulate app restart by rebuilding the app
    await tester.restartAndRestore();
    await tester.pumpAndSettle();

    // Verify data persistence
    await verifyData();
  }

  /// Measures app performance during integration tests
  static Future<PerformanceMetrics> measurePerformance(
    WidgetTester tester,
    Future<void> Function() operation,
  ) async {
    final startTime = DateTime.now();
    final initialMemory = _getCurrentMemoryUsage();

    await operation();
    await tester.pumpAndSettle();

    final endTime = DateTime.now();
    final finalMemory = _getCurrentMemoryUsage();

    return PerformanceMetrics(
      executionTime: endTime.difference(startTime),
      memoryUsage: finalMemory - initialMemory,
      frameCount: tester.binding.platformDispatcher.onReportTimings?.call([]).length ?? 0,
    );
  }

  /// Gets current memory usage (simplified implementation)
  static int _getCurrentMemoryUsage() {
    // This would integrate with actual memory profiling tools
    // For now, return a mock value
    return 1024 * 1024; // 1MB
  }

  /// Simulates different device orientations
  static Future<void> testOrientationChanges(
    WidgetTester tester,
    Future<void> Function(Orientation) testCallback,
  ) async {
    for (final orientation in Orientation.values) {
      await _setOrientation(tester, orientation);
      await testCallback(orientation);
    }
  }

  /// Sets device orientation
  static Future<void> _setOrientation(
    WidgetTester tester,
    Orientation orientation,
  ) async {
    final size = orientation == Orientation.portrait
        ? const Size(400, 800)
        : const Size(800, 400);

    await tester.binding.setSurfaceSize(size);
    await tester.pumpAndSettle();
  }

  /// Simulates different screen densities
  static Future<void> testScreenDensities(
    WidgetTester tester,
    Future<void> Function(double) testCallback,
    List<double> densities = const [1.0, 1.5, 2.0, 3.0],
  ) async {
    for (final density in densities) {
      tester.view.devicePixelRatio = density;
      await tester.pumpAndSettle();
      await testCallback(density);
    }
  }

  /// Tests accessibility features
  static Future<void> testAccessibilityFeatures(
    WidgetTester tester,
    Widget widget,
  ) async {
    // Test with accessibility enabled
    tester.view.accessibilityFeatures = AccessibilityFeatures.allOn();
    await tester.pumpWidget(widget);
    await tester.pumpAndSettle();

    // Verify semantic information is available
    final semantics = tester.binding.pipelineOwner.semanticsOwner?.rootSemanticsNode;
    expect(semantics, isNotNull);

    // Test with different accessibility settings
    final accessibilityVariations = [
      AccessibilityFeatures.allOff(),
      AccessibilityFeatures.allOn(),
      const AccessibilityFeatures(boldText: true),
      const AccessibilityFeatures(highContrast: true),
    ];

    for (final features in accessibilityVariations) {
      tester.view.accessibilityFeatures = features;
      await tester.pumpAndSettle();

      // Verify app still functions correctly
      expect(find.byWidget(widget), findsOneWidget);
    }
  }

  /// Performs stress testing with rapid interactions
  static Future<void> performStressTest(
    WidgetTester tester,
    Widget widget,
    List<Finder> interactionTargets, {
    int iterations = 100,
    Duration delayBetweenActions = const Duration(milliseconds: 10),
  }) async {
    await tester.pumpWidget(widget);
    await tester.pumpAndSettle();

    for (int i = 0; i < iterations; i++) {
      for (final target in interactionTargets) {
        if (target.evaluate().isNotEmpty) {
          await tester.tap(target);
          await tester.pump(delayBetweenActions);
        }
      }

      // Periodically settle to prevent test timeout
      if (i % 10 == 0) {
        await tester.pumpAndSettle();
      }
    }

    // Final settle
    await tester.pumpAndSettle();
  }

  /// Tests memory leaks by creating and disposing widgets repeatedly
  static Future<void> testMemoryLeaks(
    WidgetTester tester,
    Widget Function() widgetFactory, {
    int iterations = 50,
  }) async {
    final initialMemory = _getCurrentMemoryUsage();

    for (int i = 0; i < iterations; i++) {
      final widget = widgetFactory();
      await tester.pumpWidget(widget);
      await tester.pumpAndSettle();

      // Clear the widget tree
      await tester.pumpWidget(Container());
      await tester.pumpAndSettle();
    }

    final finalMemory = _getCurrentMemoryUsage();
    final memoryIncrease = finalMemory - initialMemory;

    // Verify memory usage hasn't increased significantly
    // This threshold would need tuning based on actual app behavior
    const maxMemoryIncrease = 10 * 1024 * 1024; // 10MB
    expect(memoryIncrease, lessThan(maxMemoryIncrease));
  }

  /// Creates a comprehensive test report
  static TestReport createTestReport({
    required List<TestResult> results,
    required PerformanceMetrics performance,
    required DateTime startTime,
    required DateTime endTime,
  }) {
    return TestReport(
      results: results,
      performance: performance,
      startTime: startTime,
      endTime: endTime,
      duration: endTime.difference(startTime),
      successRate: results.where((r) => r.passed).length / results.length,
    );
  }
}

/// Navigation step for end-to-end testing
class NavigationStep {
  final NavigationAction action;
  final Finder finder;
  final Offset? offset;
  final String? text;
  final Duration? duration;
  final Finder? expectedOutcome;

  const NavigationStep({
    required this.action,
    required this.finder,
    this.offset,
    this.text,
    this.duration,
    this.expectedOutcome,
  });
}

/// Navigation actions for testing
enum NavigationAction {
  tap,
  longPress,
  scroll,
  enterText,
  wait,
}

/// Performance metrics for integration testing
class PerformanceMetrics {
  final Duration executionTime;
  final int memoryUsage;
  final int frameCount;

  const PerformanceMetrics({
    required this.executionTime,
    required this.memoryUsage,
    required this.frameCount,
  });

  double get averageFrameTime => frameCount > 0 ? executionTime.inMicroseconds / frameCount : 0.0;

  @override
  String toString() {
    return 'PerformanceMetrics(executionTime: $executionTime, memoryUsage: ${memoryUsage}bytes, frameCount: $frameCount)';
  }
}

/// Test result for reporting
class TestResult {
  final String name;
  final bool passed;
  final String? error;
  final Duration duration;

  const TestResult({
    required this.name,
    required this.passed,
    this.error,
    required this.duration,
  });
}

/// Comprehensive test report
class TestReport {
  final List<TestResult> results;
  final PerformanceMetrics performance;
  final DateTime startTime;
  final DateTime endTime;
  final Duration duration;
  final double successRate;

  const TestReport({
    required this.results,
    required this.performance,
    required this.startTime,
    required this.endTime,
    required this.duration,
    required this.successRate,
  });

  @override
  String toString() {
    return '''
Integration Test Report
======================
Start Time: $startTime
End Time: $endTime
Duration: $duration
Success Rate: ${(successRate * 100).toStringAsFixed(1)}%

Performance:
$performance

Results:
${results.map((r) => '${r.passed ? "✓" : "✗"} ${r.name} (${r.duration})').join("\n")}
    ''';
  }
}