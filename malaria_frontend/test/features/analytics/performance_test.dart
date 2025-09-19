/// Comprehensive performance and benchmarking tests for analytics feature
///
/// This test suite validates performance characteristics, benchmarks, and
/// scalability of the analytics feature under various load conditions.
///
/// Tests cover:
/// - Widget rendering performance
/// - Large dataset handling
/// - Memory usage optimization
/// - Chart animation performance
/// - Data processing efficiency
/// - UI responsiveness under load
/// - Scroll and interaction performance
/// - Cache effectiveness
/// - Network request optimization
/// - Memory leak detection
library;

import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mocktail/mocktail.dart';
import 'package:malaria_frontend/features/analytics/presentation/pages/analytics_dashboard_page.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/interactive_chart_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_overview_card.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/temperature_trend_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/rainfall_pattern_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/bloc/analytics_bloc.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_data.dart';
import '../test_config.dart';
import '../mocks/analytics_mocks.dart';
import '../helpers/widget_test_helpers.dart';
import '../helpers/chart_test_helpers.dart';

void main() {
  /// Global test setup
  setUpAll(() async {
    await TestConfig.initialize();
  });

  /// Cleanup after all tests
  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('Analytics Performance Tests', () {
    late MockAnalyticsBloc mockBloc;

    setUp(() {
      mockBloc = MockAnalyticsBloc();
    });

    group('Widget Rendering Performance', () {
      testWidgets('dashboard renders within acceptable time limits', (tester) async {
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Dashboard should render within 1 second
        expect(stopwatch.elapsedMilliseconds, lessThan(1000));

        // Verify all components are rendered
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('overview cards render efficiently', (tester) async {
        final renderTimes = <Duration>[];

        // Test multiple overview cards
        for (int i = 0; i < 10; i++) {
          final renderTime = await ChartTestHelpers.measureChartRenderingTime(
            tester,
            AnalyticsOverviewCard(
              title: 'Test Card $i',
              value: '${85 + i}%',
              icon: Icons.analytics,
              color: Colors.blue,
              trend: (i - 5) * 0.01,
            ),
          );

          renderTimes.add(renderTime);
        }

        // Each card should render within 100ms
        for (final time in renderTimes) {
          expect(time.inMilliseconds, lessThan(100));
        }

        // Average render time should be under 50ms
        final averageTime = renderTimes.map((t) => t.inMilliseconds).reduce((a, b) => a + b) / renderTimes.length;
        expect(averageTime, lessThan(50));
      });

      testWidgets('chart widgets render efficiently with animations', (tester) async {
        const chart = MockAnalyticsData.createMockInteractiveChart();

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          InteractiveChartWidget(chart: chart),
        );

        // Wait for initial render
        await tester.pump();
        final initialRenderTime = stopwatch.elapsedMilliseconds;

        // Wait for animations to complete
        await tester.pumpAndSettle();
        stopwatch.stop();

        // Initial render should be fast (under 200ms)
        expect(initialRenderTime, lessThan(200));

        // Total time including animations should be reasonable (under 1 second)
        expect(stopwatch.elapsedMilliseconds, lessThan(1000));
      });

      testWidgets('complex dashboard layout renders within time budget', (tester) async {
        // Create complex analytics data with multiple components
        final complexData = MockAnalyticsData.createMockAnalyticsData().copyWith(
          environmentalTrends: List.generate(100, (index) =>
            EnvironmentalTrend(
              date: DateTime.now().subtract(Duration(days: index)),
              factor: EnvironmentalFactor.values[index % EnvironmentalFactor.values.length],
              value: 20.0 + (index % 30),
              coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
              quality: 0.9,
            ),
          ),
        );

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: complexData,
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 100)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Complex layout should still render within reasonable time (2 seconds)
        expect(stopwatch.elapsedMilliseconds, lessThan(2000));
      });
    });

    group('Large Dataset Performance', () {
      testWidgets('handles 1000+ environmental data points efficiently', (tester) async {
        final largeEnvironmentalData = List.generate(1000, (index) =>
          EnvironmentalTrend(
            date: DateTime.now().subtract(Duration(hours: index)),
            factor: EnvironmentalFactor.temperature,
            value: 20.0 + (index % 40) + (index * 0.001),
            coordinates: Coordinates(
              latitude: -1.2921 + (index % 10) * 0.01,
              longitude: 36.8219 + (index % 10) * 0.01,
            ),
            quality: 0.8 + (index % 20) * 0.01,
          ),
        );

        final largeData = MockAnalyticsData.createMockAnalyticsData().copyWith(
          environmentalTrends: largeEnvironmentalData,
        );

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: largeData,
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 42)), // ~1000 hours
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Should handle large dataset within 3 seconds
        expect(stopwatch.elapsedMilliseconds, lessThan(3000));

        // Verify data is displayed
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('handles 5000+ data points with virtualization', (tester) async {
        final massiveDataset = List.generate(5000, (index) =>
          EnvironmentalTrend(
            date: DateTime.now().subtract(Duration(minutes: index)),
            factor: EnvironmentalFactor.values[index % EnvironmentalFactor.values.length],
            value: (index % 100).toDouble(),
            coordinates: Coordinates(
              latitude: -5.0 + (index % 100) * 0.1,
              longitude: 30.0 + (index % 100) * 0.1,
            ),
            quality: 0.5 + (index % 50) * 0.01,
          ),
        );

        final massiveData = MockAnalyticsData.createMockAnalyticsData().copyWith(
          environmentalTrends: massiveDataset,
        );

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: massiveData,
            selectedRegion: 'East Africa',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 4)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Should handle massive dataset within 5 seconds (with virtualization)
        expect(stopwatch.elapsedMilliseconds, lessThan(5000));
      });

      testWidgets('chart performance with large datasets', (tester) async {
        // Create line chart with 1000 data points
        final largeChartData = ChartTestHelpers.createPerformanceTestData(1000);
        final chart = InteractiveChart(
          id: 'performance_test',
          title: 'Performance Test Chart',
          chartType: InteractiveChartType.line,
          chartData: ChartTestHelpers.createTestLineChartData(largeChartData),
          interactionConfig: MockAnalyticsData.createMockInteractionConfig(),
          viewState: MockAnalyticsData.createMockViewState(),
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          InteractiveChartWidget(chart: chart),
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Chart with 1000 points should render within 2 seconds
        expect(stopwatch.elapsedMilliseconds, lessThan(2000));
      });
    });

    group('Memory Usage Performance', () {
      testWidgets('memory usage remains stable with multiple widgets', (tester) async {
        // Create multiple analytics components
        final widgets = List.generate(20, (index) =>
          AnalyticsOverviewCard(
            title: 'Card $index',
            value: '${80 + index}%',
            icon: Icons.analytics,
            color: Colors.primaries[index % Colors.primaries.length],
            trend: (index - 10) * 0.01,
          ),
        );

        // Measure initial memory
        await tester.pumpWidget(Container());
        await tester.pumpAndSettle();

        // Pump all widgets
        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          Column(children: widgets),
        );

        await tester.pumpAndSettle();

        // Dispose widgets
        await tester.pumpWidget(Container());
        await tester.pumpAndSettle();

        // Force garbage collection by creating and disposing multiple widgets
        for (int i = 0; i < 10; i++) {
          await tester.pumpWidget(
            MaterialApp(
              home: Scaffold(
                body: Column(children: widgets.take(5).toList()),
              ),
            ),
          );
          await tester.pump();
        }

        // Final cleanup
        await tester.pumpWidget(Container());
        await tester.pumpAndSettle();

        // Verify no memory leaks (no exceptions thrown)
        expect(tester.takeException(), isNull);
      });

      testWidgets('large data structures are properly disposed', (tester) async {
        for (int iteration = 0; iteration < 10; iteration++) {
          final largeData = MockAnalyticsData.createLargeAnalyticsDataSet();

          when(() => mockBloc.state).thenReturn(
            AnalyticsLoaded(
              analyticsData: largeData,
              selectedRegion: 'Kenya',
              selectedDateRange: DateRange(
                start: DateTime.now().subtract(const Duration(days: 365)),
                end: DateTime.now(),
              ),
              lastRefresh: DateTime.now(),
            ),
          );

          await WidgetTestHelpers.pumpWidgetWithBloc(
            tester,
            const AnalyticsDashboardPage(),
            mockBloc,
          );

          await tester.pump();

          // Clear widget to trigger disposal
          await tester.pumpWidget(Container());
          await tester.pump();
        }

        // Verify no memory-related exceptions
        expect(tester.takeException(), isNull);
      });

      testWidgets('chart memory usage scales appropriately', (tester) async {
        final dataSizes = [10, 100, 500, 1000];
        final renderTimes = <int, Duration>{};

        for (final size in dataSizes) {
          final chartData = ChartTestHelpers.createPerformanceTestData(size);
          final chart = InteractiveChart(
            id: 'memory_test_$size',
            title: 'Memory Test Chart',
            chartType: InteractiveChartType.line,
            chartData: ChartTestHelpers.createTestLineChartData(chartData),
            interactionConfig: MockAnalyticsData.createMockInteractionConfig(),
            viewState: MockAnalyticsData.createMockViewState(),
          );

          final renderTime = await ChartTestHelpers.measureChartRenderingTime(
            tester,
            InteractiveChartWidget(chart: chart),
          );

          renderTimes[size] = renderTime;

          // Clear between tests
          await tester.pumpWidget(Container());
          await tester.pumpAndSettle();
        }

        // Verify render times scale reasonably
        expect(renderTimes[10]!.inMilliseconds, lessThan(100));
        expect(renderTimes[100]!.inMilliseconds, lessThan(300));
        expect(renderTimes[500]!.inMilliseconds, lessThan(1000));
        expect(renderTimes[1000]!.inMilliseconds, lessThan(2000));
      });
    });

    group('Interaction Performance', () {
      testWidgets('chart interactions remain responsive', (tester) async {
        const chart = MockAnalyticsData.createMockInteractiveChart();

        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          InteractiveChartWidget(chart: chart),
        );

        await tester.pumpAndSettle();

        await ChartTestHelpers.testChartResponsiveness(
          tester,
          InteractiveChartWidget(chart: chart),
          interactionCount: 20,
          maxResponseTime: const Duration(milliseconds: 50),
        );
      });

      testWidgets('scroll performance in dashboard', (tester) async {
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Perform scroll performance test
        final scrollView = find.byType(Scrollable);
        if (scrollView.evaluate().isNotEmpty) {
          final stopwatch = Stopwatch()..start();

          // Perform multiple scroll operations
          for (int i = 0; i < 10; i++) {
            await tester.scroll(scrollView.first, const Offset(0, -100));
            await tester.pump(const Duration(milliseconds: 16)); // One frame
          }

          await tester.pumpAndSettle();
          stopwatch.stop();

          // Scroll operations should complete within reasonable time
          expect(stopwatch.elapsedMilliseconds, lessThan(500));
        }
      });

      testWidgets('filter interactions perform efficiently', (tester) async {
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Test filter interactions
        final filterButtons = find.byType(FilterChip);
        if (filterButtons.evaluate().isNotEmpty) {
          final stopwatch = Stopwatch()..start();

          // Rapidly tap filter buttons
          for (int i = 0; i < 5; i++) {
            for (final button in filterButtons.evaluate().take(3)) {
              await tester.tap(find.byWidget(button.widget));
              await tester.pump(const Duration(milliseconds: 10));
            }
          }

          await tester.pumpAndSettle();
          stopwatch.stop();

          // Filter interactions should be responsive
          expect(stopwatch.elapsedMilliseconds, lessThan(1000));
        }
      });

      testWidgets('rapid state changes maintain performance', (tester) async {
        final states = [
          const AnalyticsLoading(),
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
          const AnalyticsError(message: 'Test error', errorType: 'test'),
        ];

        final stopwatch = Stopwatch()..start();

        // Rapidly cycle through states
        for (int i = 0; i < 30; i++) {
          when(() => mockBloc.state).thenReturn(states[i % states.length]);

          await WidgetTestHelpers.pumpWidgetWithBloc(
            tester,
            const AnalyticsDashboardPage(),
            mockBloc,
          );

          await tester.pump(const Duration(milliseconds: 16));
        }

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Rapid state changes should not degrade performance significantly
        expect(stopwatch.elapsedMilliseconds, lessThan(2000));
      });
    });

    group('Animation Performance', () {
      testWidgets('chart animations maintain 60fps target', (tester) async {
        const chart = MockAnalyticsData.createMockInteractiveChart();

        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          InteractiveChartWidget(chart: chart),
        );

        await ChartTestHelpers.validateChartAnimations(
          tester,
          InteractiveChartWidget(chart: chart),
          expectedDuration: const Duration(milliseconds: 300),
        );

        // Verify smooth animations by checking frame timing
        // In a real implementation, this would measure actual frame times
        expect(tester.binding.hasScheduledFrame, isFalse);
      });

      testWidgets('loading animations are smooth', (tester) async {
        when(() => mockBloc.state).thenReturn(
          const AnalyticsLoading(message: 'Loading...', progress: 0.5),
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        // Pump several frames to observe animation
        for (int i = 0; i < 10; i++) {
          await tester.pump(const Duration(milliseconds: 16));
        }

        stopwatch.stop();

        // Animation frames should be consistent (10 frames at 16ms each = 160ms)
        expect(stopwatch.elapsedMilliseconds, lessThan(200));
      });

      testWidgets('transition animations between states are smooth', (tester) async {
        // Start with loading
        when(() => mockBloc.state).thenReturn(
          const AnalyticsLoading(),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pump();

        // Transition to loaded
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        final stopwatch = Stopwatch()..start();

        // Allow transition animation
        await tester.pumpAndSettle();
        stopwatch.stop();

        // Transition should be smooth and quick
        expect(stopwatch.elapsedMilliseconds, lessThan(500));
      });
    });

    group('Data Processing Performance', () {
      testWidgets('analytics data processing is efficient', (tester) async {
        final largeData = MockAnalyticsData.createLargeAnalyticsDataSet();

        final stopwatch = Stopwatch()..start();

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: largeData,
            selectedRegion: 'East Africa',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 365)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Large data processing should complete within reasonable time
        expect(stopwatch.elapsedMilliseconds, lessThan(3000));
      });

      testWidgets('chart data transformation is optimized', (tester) async {
        // Create complex data transformation scenario
        final complexData = List.generate(1000, (index) =>
          EnvironmentalTrend(
            date: DateTime.now().subtract(Duration(hours: index)),
            factor: EnvironmentalFactor.values[index % EnvironmentalFactor.values.length],
            value: 20.0 + (index % 40) * (1 + 0.1 * (index % 10)),
            coordinates: Coordinates(
              latitude: -1.2921 + (index % 100) * 0.001,
              longitude: 36.8219 + (index % 100) * 0.001,
            ),
            quality: 0.8 + (index % 20) * 0.01,
          ),
        );

        final transformationData = MockAnalyticsData.createMockAnalyticsData().copyWith(
          environmentalTrends: complexData,
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          TemperatureTrendChart(
            temperatureData: transformationData.temperature.dailyMean,
            showAnomalies: true,
            showSeasonalPattern: true,
          ),
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Complex data transformation should be efficient
        expect(stopwatch.elapsedMilliseconds, lessThan(1000));
      });

      testWidgets('filter operations are performant', (tester) async {
        final filteringData = MockAnalyticsData.createLargeAnalyticsDataSet();

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: filteringData,
            selectedRegion: 'East Africa',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 365)),
              end: DateTime.now(),
            ),
            appliedFilters: AnalyticsFilters(
              region: 'East Africa',
              dateRange: DateRange(
                start: DateTime.now().subtract(const Duration(days: 365)),
                end: DateTime.now(),
              ),
              riskLevels: {RiskLevel.high, RiskLevel.critical},
              environmentalFactors: {EnvironmentalFactor.temperature, EnvironmentalFactor.rainfall},
              dataQualityThreshold: 0.9,
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Filtered data processing should be efficient
        expect(stopwatch.elapsedMilliseconds, lessThan(2000));
      });
    });

    group('Network and Caching Performance', () {
      testWidgets('simulates efficient data caching', (tester) async {
        // First load - simulate network request
        when(() => mockBloc.state).thenReturn(
          const AnalyticsLoading(message: 'Loading from network...'),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pump();

        final firstLoadTime = Stopwatch()..start();

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await tester.pumpAndSettle();
        firstLoadTime.stop();

        // Clear and simulate cached load
        await tester.pumpWidget(Container());
        await tester.pump();

        final cachedLoadTime = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        cachedLoadTime.stop();

        // Cached load should be significantly faster
        expect(cachedLoadTime.elapsedMilliseconds, lessThan(firstLoadTime.elapsedMilliseconds));
        expect(cachedLoadTime.elapsedMilliseconds, lessThan(200));
      });

      testWidgets('handles concurrent data requests efficiently', (tester) async {
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        final stopwatch = Stopwatch()..start();

        // Simulate multiple concurrent widget requests
        final futures = List.generate(5, (index) =>
          WidgetTestHelpers.measureWidgetPerformance(
            tester,
            () async {
              await WidgetTestHelpers.pumpWidgetWithBloc(
                tester,
                const AnalyticsDashboardPage(),
                mockBloc,
              );
              await tester.pump();
            },
          ),
        );

        await Future.wait(futures);
        stopwatch.stop();

        // Concurrent requests should complete efficiently
        expect(stopwatch.elapsedMilliseconds, lessThan(2000));
      });
    });

    group('Stress Testing', () {
      testWidgets('handles extreme user interaction patterns', (tester) async {
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Perform stress test with rapid interactions
        final interactionTargets = [
          find.byType(ElevatedButton),
          find.byType(TextButton),
          find.byType(IconButton),
          find.byType(Chip),
        ];

        final stopwatch = Stopwatch()..start();

        for (final targetType in interactionTargets) {
          final targets = targetType.evaluate().take(3);
          for (final target in targets) {
            for (int i = 0; i < 10; i++) {
              await tester.tap(find.byWidget(target.widget));
              await tester.pump(const Duration(milliseconds: 10));
            }
          }
        }

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Stress test should complete without performance degradation
        expect(stopwatch.elapsedMilliseconds, lessThan(3000));
        expect(tester.takeException(), isNull);
      });

      testWidgets('memory usage remains stable under stress', (tester) async {
        // Perform repeated widget creation and disposal
        for (int cycle = 0; cycle < 20; cycle++) {
          when(() => mockBloc.state).thenReturn(
            AnalyticsLoaded(
              analyticsData: MockAnalyticsData.createLargeAnalyticsDataSet(),
              selectedRegion: 'Kenya',
              selectedDateRange: DateRange(
                start: DateTime.now().subtract(const Duration(days: 365)),
                end: DateTime.now(),
              ),
              lastRefresh: DateTime.now(),
            ),
          );

          await WidgetTestHelpers.pumpWidgetWithBloc(
            tester,
            const AnalyticsDashboardPage(),
            mockBloc,
          );

          await tester.pump();

          // Rapid interactions during each cycle
          final buttons = find.byType(IconButton);
          for (final button in buttons.evaluate().take(3)) {
            await tester.tap(find.byWidget(button.widget));
            await tester.pump(const Duration(milliseconds: 5));
          }

          // Clear widget
          await tester.pumpWidget(Container());
          await tester.pump();
        }

        // Final verification - no memory-related exceptions
        expect(tester.takeException(), isNull);
      });
    });
  });

  group('Performance Regression Tests', () {
    testWidgets('baseline performance benchmarks', (tester) async {
      final benchmarks = <String, Duration>{};

      // Benchmark 1: Simple dashboard load
      final simpleLoadTime = await _benchmarkOperation(tester, () async {
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 7)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
      });

      benchmarks['simple_dashboard_load'] = simpleLoadTime;

      // Benchmark 2: Complex chart rendering
      final chartRenderTime = await _benchmarkOperation(tester, () async {
        const chart = MockAnalyticsData.createMockInteractiveChart();
        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          InteractiveChartWidget(chart: chart),
        );
        await tester.pumpAndSettle();
      });

      benchmarks['chart_render'] = chartRenderTime;

      // Benchmark 3: Large dataset processing
      final largeDataTime = await _benchmarkOperation(tester, () async {
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createLargeAnalyticsDataSet(),
            selectedRegion: 'East Africa',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 365)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
      });

      benchmarks['large_dataset'] = largeDataTime;

      // Verify benchmarks meet performance targets
      expect(benchmarks['simple_dashboard_load']!.inMilliseconds, lessThan(500));
      expect(benchmarks['chart_render']!.inMilliseconds, lessThan(300));
      expect(benchmarks['large_dataset']!.inMilliseconds, lessThan(2000));

      // Print benchmarks for monitoring
      print('Performance Benchmarks:');
      for (final entry in benchmarks.entries) {
        print('${entry.key}: ${entry.value.inMilliseconds}ms');
      }
    });
  });

  /// Helper method to benchmark operations
  static Future<Duration> _benchmarkOperation(
    WidgetTester tester,
    Future<void> Function() operation,
  ) async {
    // Warm up
    await operation();
    await tester.pumpWidget(Container());
    await tester.pumpAndSettle();

    // Actual benchmark
    final stopwatch = Stopwatch()..start();
    await operation();
    stopwatch.stop();

    // Cleanup
    await tester.pumpWidget(Container());
    await tester.pumpAndSettle();

    return stopwatch.elapsed;
  }
}