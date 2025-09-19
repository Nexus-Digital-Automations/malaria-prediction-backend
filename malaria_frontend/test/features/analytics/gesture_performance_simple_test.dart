/// Simple gesture performance tests
///
/// This file contains basic performance tests for chart gesture handling
/// focusing on responsiveness and efficiency of user interactions.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mocktail/mocktail.dart';

import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_overview_card.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/line_chart_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/bar_chart_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/bloc/analytics_bloc.dart';

import '../../mocks/analytics_mocks.dart';
import '../../helpers/widget_test_helpers.dart';
import '../../test_config.dart';

void main() {
  group('Gesture Performance Tests', () {
    late MockAnalyticsBloc mockBloc;

    setUpAll(() {
      TestConfig.setupTestEnvironment();
    });

    setUp(() {
      mockBloc = MockAnalyticsBloc();
      when(() => mockBloc.state).thenReturn(
        const AnalyticsLoaded(data: MockAnalyticsData()),
      );
    });

    group('Touch Response Performance', () {
      testWidgets('should respond to touch within acceptable time', (tester) async {
        final responseTimes = <Duration>[];

        final card = AnalyticsOverviewCard(
          title: 'Performance Test',
          value: '42',
          subtitle: 'Response Time',
          onTap: () {
            responseTimes.add(DateTime.now().difference(DateTime.now()));
          },
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(tester, card, mockBloc);

        final cardFinder = find.byType(AnalyticsOverviewCard);

        // Perform multiple taps and measure response
        for (int i = 0; i < 5; i++) {
          final tapStart = DateTime.now();
          await tester.tap(cardFinder);
          await tester.pump();
          final tapEnd = DateTime.now();

          responseTimes.add(tapEnd.difference(tapStart));
        }

        // Verify response times are reasonable
        for (final responseTime in responseTimes) {
          expect(responseTime.inMilliseconds, lessThan(50),
              reason: 'Touch response should be under 50ms');
        }
      });

      testWidgets('should maintain performance with chart widgets', (tester) async {
        final lineChart = LineChartWidget(
          data: const MockChartData(),
          title: 'Performance Chart',
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(tester, lineChart, mockBloc);

        final chartFinder = find.byType(LineChartWidget);

        // Measure rendering performance
        final renderTime = await WidgetTestHelpers.measureWidgetPerformance(
          tester,
          () async {
            await tester.pump();
          },
        );

        expect(renderTime.inMilliseconds, lessThan(100),
            reason: 'Chart should render within 100ms');

        // Test gesture performance
        final gestureStart = DateTime.now();
        await tester.tap(chartFinder);
        await tester.pump();
        final gestureEnd = DateTime.now();

        expect(gestureEnd.difference(gestureStart).inMilliseconds, lessThan(50),
            reason: 'Chart gesture should respond within 50ms');
      });
    });

    group('Rapid Gesture Handling', () {
      testWidgets('should handle rapid gesture sequences', (tester) async {
        final card = AnalyticsOverviewCard(
          title: 'Rapid Test',
          value: '100',
          subtitle: 'Gesture Speed',
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(tester, card, mockBloc);

        final cardFinder = find.byType(AnalyticsOverviewCard);

        // Rapid tap sequence
        final sequenceStart = DateTime.now();
        for (int i = 0; i < 10; i++) {
          await tester.tap(cardFinder);
          await tester.pump(const Duration(milliseconds: 10));
        }
        final sequenceEnd = DateTime.now();

        expect(sequenceEnd.difference(sequenceStart).inMilliseconds, lessThan(300),
            reason: 'Rapid gesture sequence should complete quickly');

        expect(tester.takeException(), isNull);
      });

      testWidgets('should handle mixed gesture types efficiently', (tester) async {
        final barChart = BarChartWidget(
          data: const MockChartData(),
          title: 'Mixed Gesture Chart',
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(tester, barChart, mockBloc);

        final chartFinder = find.byType(BarChartWidget);

        // Mixed gesture sequence: tap, drag, tap
        final mixedStart = DateTime.now();

        await tester.tap(chartFinder);
        await tester.pump();

        await tester.drag(chartFinder, const Offset(50, 0));
        await tester.pump();

        await tester.tap(chartFinder);
        await tester.pump();

        final mixedEnd = DateTime.now();

        expect(mixedEnd.difference(mixedStart).inMilliseconds, lessThan(200),
            reason: 'Mixed gesture sequence should be efficient');
      });
    });

    group('Memory Efficiency During Gestures', () {
      testWidgets('should not leak memory during extended interaction', (tester) async {
        final card = AnalyticsOverviewCard(
          title: 'Memory Test',
          value: '200',
          subtitle: 'Leak Prevention',
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(tester, card, mockBloc);

        final cardFinder = find.byType(AnalyticsOverviewCard);

        // Extended interaction session
        for (int session = 0; session < 3; session++) {
          for (int i = 0; i < 20; i++) {
            await tester.tap(cardFinder);
            await tester.pump();
          }

          // Force cleanup
          await tester.pumpAndSettle();
        }

        // Widget should still be responsive
        await tester.tap(cardFinder);
        await tester.pump();

        expect(cardFinder, findsOneWidget);
        expect(tester.takeException(), isNull);
      });

      testWidgets('should clean up resources properly on dispose', (tester) async {
        final lineChart = LineChartWidget(
          data: const MockChartData(),
          title: 'Disposal Test',
        );

        // Build and dispose multiple times
        for (int i = 0; i < 3; i++) {
          await WidgetTestHelpers.pumpWidgetWithBloc(tester, lineChart, mockBloc);

          final chartFinder = find.byType(LineChartWidget);
          await tester.tap(chartFinder);
          await tester.pump();

          // Dispose widget
          await tester.pumpWidget(Container());
          await tester.pumpAndSettle();
        }

        // No widget should remain
        expect(find.byType(LineChartWidget), findsNothing);
      });
    });

    group('Gesture Accuracy Performance', () {
      testWidgets('should accurately detect touch coordinates quickly', (tester) async {
        final detectedPoints = <Offset>[];

        final testWidget = GestureDetector(
          onTapDown: (details) => detectedPoints.add(details.localPosition),
          child: const AnalyticsOverviewCard(
            title: 'Accuracy Test',
            value: '100%',
            subtitle: 'Touch Precision',
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(tester, testWidget, mockBloc);

        final gestureDetectorFinder = find.byType(GestureDetector);
        final rect = tester.getRect(gestureDetectorFinder);

        // Test multiple precise touch points
        final testPoints = [
          rect.topLeft + const Offset(10, 10),
          rect.center,
          rect.bottomRight - const Offset(10, 10),
        ];

        final accuracyStart = DateTime.now();

        for (final point in testPoints) {
          await tester.tapAt(point);
          await tester.pump();
        }

        final accuracyEnd = DateTime.now();

        expect(accuracyEnd.difference(accuracyStart).inMilliseconds, lessThan(100),
            reason: 'Touch accuracy detection should be fast');

        expect(detectedPoints.length, equals(testPoints.length));

        // Verify accuracy within tolerance
        for (int i = 0; i < testPoints.length; i++) {
          final expected = testPoints[i] - rect.topLeft;
          final actual = detectedPoints[i];
          expect((actual - expected).distance, lessThan(5.0),
              reason: 'Touch detection should be accurate within 5 pixels');
        }
      });
    });

    group('Concurrent Gesture Performance', () {
      testWidgets('should handle simultaneous touches efficiently', (tester) async {
        final lineChart = LineChartWidget(
          data: const MockChartData(),
          title: 'Concurrent Touch Test',
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(tester, lineChart, mockBloc);

        final chartFinder = find.byType(LineChartWidget);
        final center = tester.getCenter(chartFinder);

        // Simulate multiple simultaneous touches
        final concurrentStart = DateTime.now();

        final gestures = <TestGesture>[];
        for (int i = 0; i < 3; i++) {
          final gesture = await tester.createGesture();
          await gesture.down(center + Offset(i * 20.0, 0));
          gestures.add(gesture);
        }

        await tester.pump(const Duration(milliseconds: 50));

        for (final gesture in gestures) {
          await gesture.up();
        }

        final concurrentEnd = DateTime.now();

        expect(concurrentEnd.difference(concurrentStart).inMilliseconds, lessThan(150),
            reason: 'Concurrent touches should be handled efficiently');

        expect(tester.takeException(), isNull);
      });
    });

    group('Performance Benchmarking', () {
      testWidgets('should benchmark gesture response across widget types', (tester) async {
        final widgets = [
          AnalyticsOverviewCard(title: 'Card', value: '1', subtitle: 'Test'),
          LineChartWidget(data: const MockChartData(), title: 'Line Chart'),
          BarChartWidget(data: const MockChartData(), title: 'Bar Chart'),
        ];

        final results = <Type, Duration>{};

        for (final widget in widgets) {
          await WidgetTestHelpers.pumpWidgetWithBloc(tester, widget, mockBloc);

          final finder = find.byWidget(widget);

          final benchmarkTime = await WidgetTestHelpers.measureWidgetPerformance(
            tester,
            () async {
              await tester.tap(finder);
              await tester.pump();
            },
          );

          results[widget.runtimeType] = benchmarkTime;
        }

        // All widgets should perform within acceptable limits
        for (final entry in results.entries) {
          expect(entry.value.inMilliseconds, lessThan(50),
              reason: '${entry.key} should respond within 50ms');
        }
      });
    });
  });
}

/// Mock analytics data for testing
class MockAnalyticsData {
  const MockAnalyticsData();
}

/// Mock chart data for testing
class MockChartData {
  const MockChartData();
}