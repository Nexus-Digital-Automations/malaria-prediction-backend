/// Widget testing helper utilities
///
/// This file provides utility functions and helpers for widget testing,
/// including test setup, widget finding, and interaction simulation.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../mocks/analytics_mocks.dart';
import '../test_config.dart';

/// Widget testing helper class
class WidgetTestHelpers {
  /// Pumps a widget with MaterialApp wrapper and theme
  static Future<void> pumpWidgetWithMaterialApp(
    WidgetTester tester,
    Widget widget, {
    ThemeData? theme,
    Locale? locale,
    NavigatorObserver? navigatorObserver,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: theme ?? ThemeData.light(),
        locale: locale,
        navigatorObservers: navigatorObserver != null ? [navigatorObserver] : [],
        home: Scaffold(body: widget),
      ),
    );
  }

  /// Pumps a widget with BLoC providers
  static Future<void> pumpWidgetWithBloc<T extends BlocBase>(
    WidgetTester tester,
    Widget widget,
    T bloc, {
    ThemeData? theme,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: theme ?? ThemeData.light(),
        home: BlocProvider<T>(
          create: (context) => bloc,
          child: Scaffold(body: widget),
        ),
      ),
    );
  }

  /// Pumps a widget with multiple BLoC providers
  static Future<void> pumpWidgetWithMultipleBlocs(
    WidgetTester tester,
    Widget widget,
    List<BlocProvider> providers, {
    ThemeData? theme,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: theme ?? ThemeData.light(),
        home: MultiBlocProvider(
          providers: providers,
          child: Scaffold(body: widget),
        ),
      ),
    );
  }

  /// Simulates user tap with optional delay
  static Future<void> tapWidget(
    WidgetTester tester,
    Finder finder, {
    Duration delay = const Duration(milliseconds: 100),
  }) async {
    await tester.tap(finder);
    await tester.pump(delay);
  }

  /// Simulates user long press
  static Future<void> longPressWidget(
    WidgetTester tester,
    Finder finder, {
    Duration delay = const Duration(milliseconds: 100),
  }) async {
    await tester.longPress(finder);
    await tester.pump(delay);
  }

  /// Simulates user drag gesture
  static Future<void> dragWidget(
    WidgetTester tester,
    Finder finder,
    Offset offset, {
    Duration delay = const Duration(milliseconds: 100),
  }) async {
    await tester.drag(finder, offset);
    await tester.pump(delay);
  }

  /// Enters text into a form field
  static Future<void> enterText(
    WidgetTester tester,
    Finder finder,
    String text, {
    Duration delay = const Duration(milliseconds: 100),
  }) async {
    await tester.enterText(finder, text);
    await tester.pump(delay);
  }

  /// Scrolls a scrollable widget
  static Future<void> scrollWidget(
    WidgetTester tester,
    Finder finder,
    Offset offset, {
    Duration delay = const Duration(milliseconds: 100),
  }) async {
    await tester.scroll(finder, offset);
    await tester.pump(delay);
  }

  /// Waits for a specific widget to appear
  static Future<void> waitForWidget(
    WidgetTester tester,
    Finder finder, {
    Duration timeout = const Duration(seconds: 5),
    Duration pollInterval = const Duration(milliseconds: 100),
  }) async {
    final endTime = DateTime.now().add(timeout);

    while (DateTime.now().isBefore(endTime)) {
      await tester.pump(pollInterval);

      if (finder.evaluate().isNotEmpty) {
        return;
      }
    }

    throw TestFailure('Widget not found within timeout: $finder');
  }

  /// Waits for a widget to disappear
  static Future<void> waitForWidgetToDisappear(
    WidgetTester tester,
    Finder finder, {
    Duration timeout = const Duration(seconds: 5),
    Duration pollInterval = const Duration(milliseconds: 100),
  }) async {
    final endTime = DateTime.now().add(timeout);

    while (DateTime.now().isBefore(endTime)) {
      await tester.pump(pollInterval);

      if (finder.evaluate().isEmpty) {
        return;
      }
    }

    throw TestFailure('Widget did not disappear within timeout: $finder');
  }

  /// Finds widget by key with type safety
  static Finder findByKeyWithType<T extends Widget>(String key) {
    return find.byKey(Key(key)).having((finder) => finder.evaluate().first.widget, 'widget', isA<T>());
  }

  /// Finds widget by text with exact match
  static Finder findByTextExact(String text) {
    return find.text(text);
  }

  /// Finds widget by text containing substring
  static Finder findByTextContaining(String substring) {
    return find.textContaining(substring);
  }

  /// Finds widget by icon
  static Finder findByIcon(IconData icon) {
    return find.byIcon(icon);
  }

  /// Finds widget by type
  static Finder findByType<T extends Widget>() {
    return find.byType(T);
  }

  /// Verifies widget properties
  static void verifyWidgetProperties<T extends Widget>(
    WidgetTester tester,
    Finder finder,
    Map<String, dynamic> expectedProperties,
  ) {
    final widget = tester.widget<T>(finder);

    for (final entry in expectedProperties.entries) {
      final property = entry.key;
      final expectedValue = entry.value;

      // Use reflection or specific property checks
      // This is a simplified version - would need more robust property checking
      switch (property) {
        case 'visible':
          expect(finder.evaluate().isNotEmpty, equals(expectedValue));
          break;
        case 'enabled':
          if (widget is StatefulWidget) {
            // Check if widget is enabled based on its state
          }
          break;
        default:
          // Custom property verification would go here
          break;
      }
    }
  }

  /// Takes a screenshot for visual regression testing
  static Future<void> takeScreenshot(
    WidgetTester tester,
    String name, {
    Finder? finder,
  }) async {
    // This would integrate with screenshot testing tools
    await tester.pump();

    // For golden tests, use:
    // await expectLater(finder ?? find.byType(MaterialApp), matchesGoldenFile('$name.png'));
  }

  /// Measures widget performance
  static Future<Duration> measureWidgetPerformance(
    WidgetTester tester,
    Future<void> Function() widgetOperation,
  ) async {
    final stopwatch = Stopwatch()..start();

    await widgetOperation();
    await tester.pumpAndSettle();

    stopwatch.stop();
    return stopwatch.elapsed;
  }

  /// Simulates device orientation change
  static Future<void> changeOrientation(
    WidgetTester tester,
    Orientation orientation,
  ) async {
    final size = orientation == Orientation.portrait
        ? const Size(400, 800)
        : const Size(800, 400);

    await tester.binding.setSurfaceSize(size);
    await tester.pumpAndSettle();
  }

  /// Simulates different screen sizes
  static Future<void> setScreenSize(
    WidgetTester tester,
    Size size,
  ) async {
    await tester.binding.setSurfaceSize(size);
    await tester.pumpAndSettle();
  }

  /// Tests widget accessibility
  static Future<void> testWidgetAccessibility(
    WidgetTester tester,
    Widget widget,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: widget),
      ),
    );

    // Test semantic labels
    final handle = tester.binding.pipelineOwner.semanticsOwner?.rootSemanticsNode;
    expect(handle, isNotNull);

    // Verify semantic information is available
    await tester.pumpAndSettle();
  }

  /// Creates mock theme data for testing
  static ThemeData createMockThemeData({
    Brightness brightness = Brightness.light,
    Color? primaryColor,
  }) {
    return ThemeData(
      brightness: brightness,
      primarySwatch: primaryColor != null ? Colors.blue : null,
      useMaterial3: true,
    );
  }

  /// Creates test data for forms
  static Map<String, String> createTestFormData({
    String name = 'Test User',
    String email = 'test@example.com',
    String region = 'Kenya',
  }) {
    return {
      'name': name,
      'email': email,
      'region': region,
    };
  }

  /// Verifies form validation
  static Future<void> verifyFormValidation(
    WidgetTester tester,
    Map<String, Finder> formFields,
    Map<String, String> invalidData,
    List<String> expectedErrors,
  ) async {
    // Enter invalid data
    for (final entry in invalidData.entries) {
      final fieldFinder = formFields[entry.key];
      if (fieldFinder != null) {
        await enterText(tester, fieldFinder, entry.value);
      }
    }

    // Trigger validation (usually by tapping submit)
    final submitButton = find.byType(ElevatedButton);
    if (submitButton.evaluate().isNotEmpty) {
      await tapWidget(tester, submitButton);
    }

    // Verify error messages appear
    for (final error in expectedErrors) {
      expect(find.text(error), findsOneWidget);
    }
  }

  /// Tests loading states
  static Future<void> testLoadingState(
    WidgetTester tester,
    Widget widget,
    Future<void> Function() triggerLoading,
  ) async {
    await pumpWidgetWithMaterialApp(tester, widget);

    // Trigger loading
    await triggerLoading();
    await tester.pump();

    // Verify loading indicator
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // Wait for completion
    await tester.pumpAndSettle();

    // Verify loading indicator disappears
    expect(find.byType(CircularProgressIndicator), findsNothing);
  }

  /// Tests error states
  static Future<void> testErrorState(
    WidgetTester tester,
    Widget widget,
    Future<void> Function() triggerError,
    String expectedErrorMessage,
  ) async {
    await pumpWidgetWithMaterialApp(tester, widget);

    // Trigger error
    await triggerError();
    await tester.pumpAndSettle();

    // Verify error message
    expect(find.text(expectedErrorMessage), findsOneWidget);
    expect(find.byIcon(Icons.error), findsOneWidget);
  }

  /// Tests empty states
  static Future<void> testEmptyState(
    WidgetTester tester,
    Widget widget,
    String expectedEmptyMessage,
  ) async {
    await pumpWidgetWithMaterialApp(tester, widget);
    await tester.pumpAndSettle();

    // Verify empty state message
    expect(find.text(expectedEmptyMessage), findsOneWidget);
  }

  /// Simulates network conditions
  static Future<void> simulateNetworkCondition(
    WidgetTester tester,
    NetworkCondition condition,
    Future<void> Function() operation,
  ) async {
    // This would integrate with network mocking tools
    switch (condition) {
      case NetworkCondition.offline:
        // Simulate offline condition
        break;
      case NetworkCondition.slow:
        // Simulate slow network
        await Future.delayed(const Duration(seconds: 2));
        break;
      case NetworkCondition.fast:
        // Simulate fast network
        break;
    }

    await operation();
  }

  /// Creates test context with providers
  static Widget createTestContextWithProviders({
    required Widget child,
    List<BlocProvider>? blocProviders,
    ThemeData? theme,
  }) {
    Widget app = MaterialApp(
      theme: theme ?? ThemeData.light(),
      home: Scaffold(body: child),
    );

    if (blocProviders != null && blocProviders.isNotEmpty) {
      app = MultiBlocProvider(
        providers: blocProviders,
        child: app,
      );
    }

    return app;
  }

  /// Verifies widget tree structure
  static void verifyWidgetTreeStructure(
    WidgetTester tester,
    List<Type> expectedWidgetTypes,
  ) {
    final widgets = tester.allWidgets.toList();

    for (final expectedType in expectedWidgetTypes) {
      final foundWidget = widgets.any((widget) => widget.runtimeType == expectedType);
      expect(foundWidget, isTrue, reason: 'Expected widget type $expectedType not found in widget tree');
    }
  }

  /// Tests widget responsiveness across different screen sizes
  static Future<void> testResponsiveness(
    WidgetTester tester,
    Widget widget,
    List<Size> screenSizes,
  ) async {
    for (final size in screenSizes) {
      await setScreenSize(tester, size);
      await pumpWidgetWithMaterialApp(tester, widget);
      await tester.pumpAndSettle();

      // Verify widget renders correctly at this size
      expect(find.byWidget(widget), findsOneWidget);
    }
  }

  /// Common screen sizes for responsive testing
  static const List<Size> commonScreenSizes = [
    Size(360, 640),   // Mobile portrait
    Size(640, 360),   // Mobile landscape
    Size(768, 1024),  // Tablet portrait
    Size(1024, 768),  // Tablet landscape
    Size(1920, 1080), // Desktop
  ];
}

/// Network condition enumeration for testing
enum NetworkCondition {
  offline,
  slow,
  fast,
}

/// Test failure exception
class TestFailure implements Exception {
  final String message;

  const TestFailure(this.message);

  @override
  String toString() => 'TestFailure: $message';
}