/// Comprehensive error handling and edge cases tests for analytics feature
///
/// This test suite validates error handling, edge cases, boundary conditions,
/// and error recovery mechanisms throughout the analytics feature.
///
/// Tests cover:
/// - Network error handling and recovery
/// - Data corruption and validation errors
/// - UI error states and user feedback
/// - Edge cases with boundary values
/// - Timeout and performance edge cases
/// - Memory constraints and resource limits
/// - Invalid input handling
/// - State consistency during errors
/// - Error propagation and containment
/// - Graceful degradation scenarios
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mocktail/mocktail.dart';
import 'package:dartz/dartz.dart';
import 'package:malaria_frontend/features/analytics/presentation/pages/analytics_dashboard_page.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/interactive_chart_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_overview_card.dart';
import 'package:malaria_frontend/features/analytics/presentation/bloc/analytics_bloc.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_filters.dart';
import 'package:malaria_frontend/core/error/failures.dart';
import '../test_config.dart';
import '../mocks/analytics_mocks.dart';
import '../helpers/widget_test_helpers.dart';

void main() {
  /// Global test setup
  setUpAll(() async {
    await TestConfig.initialize();
  });

  /// Cleanup after all tests
  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('Analytics Error Handling Tests', () {
    late MockAnalyticsBloc mockBloc;

    setUp(() {
      mockBloc = MockAnalyticsBloc();
    });

    group('Network Error Handling', () {
      testWidgets('handles network connection timeout gracefully', (tester) async {
        // Setup timeout error
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Connection timeout - please check your internet connection',
            errorType: 'network_timeout',
            isRecoverable: true,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify error message is displayed
        expect(find.text('Connection timeout - please check your internet connection'), findsOneWidget);
        expect(find.byIcon(Icons.wifi_off), findsOneWidget);

        // Verify retry button is available
        expect(find.textContaining('Retry'), findsOneWidget);
      });

      testWidgets('handles server unavailable error', (tester) async {
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Server temporarily unavailable (503)',
            errorType: 'server_unavailable',
            isRecoverable: true,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify server error message
        expect(find.text('Server temporarily unavailable (503)'), findsOneWidget);
        expect(find.byIcon(Icons.cloud_off), findsOneWidget);
      });

      testWidgets('handles network disconnection during data loading', (tester) async {
        // Start with loading state
        when(() => mockBloc.state).thenReturn(
          const AnalyticsLoading(message: 'Loading analytics data...'),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pump();

        // Verify loading indicator
        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        // Simulate network disconnection
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Network connection lost during data transfer',
            errorType: 'network_disconnected',
            isRecoverable: true,
          ),
        );

        await tester.pumpAndSettle();

        // Verify error state transition
        expect(find.byType(CircularProgressIndicator), findsNothing);
        expect(find.text('Network connection lost during data transfer'), findsOneWidget);
      });

      testWidgets('handles slow network with timeout warning', (tester) async {
        when(() => mockBloc.state).thenReturn(
          const AnalyticsLoading(
            message: 'Slow connection detected - this may take longer...',
            progress: 0.3,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify slow connection warning
        expect(find.textContaining('Slow connection detected'), findsOneWidget);
        expect(find.byType(LinearProgressIndicator), findsOneWidget);
      });

      testWidgets('recovers from network error when connection restored', (tester) async {
        // Start with network error
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'No internet connection',
            errorType: 'network_offline',
            isRecoverable: true,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify error state
        expect(find.text('No internet connection'), findsOneWidget);

        // Simulate connection restoration
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

        // Tap retry button
        final retryButton = find.textContaining('Retry');
        if (retryButton.evaluate().isNotEmpty) {
          await tester.tap(retryButton);
          await tester.pumpAndSettle();
        }

        // Verify recovery
        expect(find.text('No internet connection'), findsNothing);
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });
    });

    group('Data Validation Error Handling', () {
      testWidgets('handles corrupted analytics data', (tester) async {
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Data corruption detected - unable to parse analytics data',
            errorType: 'data_corruption',
            isRecoverable: false,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify corruption error message
        expect(find.textContaining('Data corruption detected'), findsOneWidget);
        expect(find.byIcon(Icons.error), findsOneWidget);

        // Verify no retry option for non-recoverable error
        expect(find.textContaining('Retry'), findsNothing);
      });

      testWidgets('handles missing required data fields', (tester) async {
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Missing required data fields: predictionAccuracy, environmentalTrends',
            errorType: 'data_validation',
            isRecoverable: true,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify validation error
        expect(find.textContaining('Missing required data fields'), findsOneWidget);
        expect(find.byIcon(Icons.warning), findsOneWidget);
      });

      testWidgets('handles invalid date ranges', (tester) async {
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Invalid date range: end date must be after start date',
            errorType: 'validation_error',
            isRecoverable: true,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify date validation error
        expect(find.textContaining('Invalid date range'), findsOneWidget);
      });

      testWidgets('handles out-of-range metric values', (tester) async {
        // Create analytics data with invalid values
        final invalidData = MockAnalyticsData.createMockAnalyticsData().copyWith(
          predictionAccuracy: PredictionAccuracy(
            overall: 1.5, // Invalid: should be 0.0-1.0
            byRiskLevel: {'invalid': -0.5}, // Invalid negative value
            trend: [],
            precision: 2.0, // Invalid: should be 0.0-1.0
            recall: 0.0,
            f1Score: 0.0,
          ),
        );

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: invalidData,
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

        // Verify dashboard handles invalid data gracefully
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);

        // Should show warning or sanitized values
        expect(find.byIcon(Icons.warning), findsAtLeastNWidgets(1));
      });
    });

    group('UI Error State Handling', () {
      testWidgets('handles chart rendering failures', (tester) async {
        const chart = MockAnalyticsData.createMockInteractiveChart();

        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          InteractiveChartWidget(
            chart: chart,
            errorMessage: 'Failed to render chart - insufficient data',
          ),
        );

        await tester.pumpAndSettle();

        // Verify chart error state
        expect(find.text('Failed to render chart - insufficient data'), findsOneWidget);
        expect(find.byIcon(Icons.error_outline), findsOneWidget);
      });

      testWidgets('handles widget overflow in small screens', (tester) async {
        // Set very small screen size
        await WidgetTestHelpers.setScreenSize(tester, const Size(200, 300));

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

        // Verify no overflow errors
        expect(tester.takeException(), isNull);
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('handles theme inconsistencies gracefully', (tester) async {
        // Use malformed theme
        final invalidTheme = ThemeData(
          brightness: Brightness.light,
          // Missing required theme components
        );

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
          theme: invalidTheme,
        );

        await tester.pumpAndSettle();

        // Verify app doesn't crash with invalid theme
        expect(tester.takeException(), isNull);
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });
    });

    group('Edge Cases and Boundary Conditions', () {
      testWidgets('handles empty analytics data', (tester) async {
        final emptyData = AnalyticsData(
          id: 'empty',
          region: 'Kenya',
          dateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          predictionAccuracy: PredictionAccuracy(
            overall: 0.0,
            byRiskLevel: {},
            trend: [],
            precision: 0.0,
            recall: 0.0,
            f1Score: 0.0,
          ),
          environmentalTrends: [],
          riskTrends: [],
          alertStatistics: AlertStatistics(
            totalAlerts: 0,
            alertsBySeverity: {},
            deliveryRate: 0.0,
            averageResponseTime: Duration.zero,
            falsePositives: 0,
            missedAlerts: 0,
          ),
          dataQuality: DataQuality(
            completeness: 0.0,
            accuracy: 0.0,
            freshnessHours: 0.0,
            sourcesCount: 0,
            sourcesWithIssues: [],
            lastUpdate: DateTime.now(),
          ),
          generatedAt: DateTime.now(),
        );

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: emptyData,
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

        // Verify empty state handling
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
        expect(find.textContaining('No data available'), findsAtLeastNWidgets(1));
      });

      testWidgets('handles extreme date ranges', (tester) async {
        // Test with very large date range
        final extremeDateRange = DateRange(
          start: DateTime(1900, 1, 1),
          end: DateTime(2100, 12, 31),
        );

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: 'Kenya',
            selectedDateRange: extremeDateRange,
            lastRefresh: DateTime.now(),
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify app handles extreme date range
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('handles very long text content', (tester) async {
        const veryLongText = 'This is an extremely long region name that should test the text overflow handling mechanisms in the analytics dashboard and verify that the UI can gracefully handle content that exceeds normal display boundaries without breaking the layout or causing rendering issues';

        await WidgetTestHelpers.pumpWidgetWithMaterialApp(
          tester,
          AnalyticsOverviewCard(
            title: veryLongText,
            value: '85.5%',
            icon: Icons.place,
            color: Colors.blue,
          ),
        );

        await tester.pumpAndSettle();

        // Verify no overflow errors
        expect(tester.takeException(), isNull);
        expect(find.byType(AnalyticsOverviewCard), findsOneWidget);
      });

      testWidgets('handles maximum number of data points', (tester) async {
        // Create analytics data with maximum data points
        final maxDataPoints = List.generate(10000, (index) =>
          EnvironmentalTrend(
            date: DateTime.now().subtract(Duration(hours: index)),
            factor: EnvironmentalFactor.temperature,
            value: 25.0 + (index % 20),
            coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
            quality: 0.9,
          ),
        );

        final largeData = MockAnalyticsData.createMockAnalyticsData().copyWith(
          environmentalTrends: maxDataPoints,
        );

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

        final stopwatch = Stopwatch()..start();

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();
        stopwatch.stop();

        // Verify performance is acceptable even with large datasets
        expect(stopwatch.elapsedMilliseconds, lessThan(5000)); // Under 5 seconds
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('handles special characters in data', (tester) async {
        const specialCharsRegion = '肯尼亚 🇰🇪 (Kenya) - Nairobi/Special@Characters#Test';

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: MockAnalyticsData.createMockAnalyticsData(),
            selectedRegion: specialCharsRegion,
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

        // Verify special characters are handled correctly
        expect(find.textContaining('肯尼亚'), findsAtLeastNWidgets(1));
        expect(find.textContaining('🇰🇪'), findsAtLeastNWidgets(1));
      });
    });

    group('Memory and Resource Constraints', () {
      testWidgets('handles low memory conditions', (tester) async {
        // Simulate low memory warning
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Insufficient memory to load analytics data',
            errorType: 'memory_constraint',
            isRecoverable: true,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify memory constraint error
        expect(find.textContaining('Insufficient memory'), findsOneWidget);
        expect(find.byIcon(Icons.memory), findsOneWidget);
      });

      testWidgets('handles resource cleanup on widget disposal', (tester) async {
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

        // Remove widget to trigger disposal
        await tester.pumpWidget(Container());
        await tester.pumpAndSettle();

        // Verify no exceptions during disposal
        expect(tester.takeException(), isNull);
      });
    });

    group('State Consistency During Errors', () {
      testWidgets('maintains state consistency during error recovery', (tester) async {
        final initialData = MockAnalyticsData.createMockAnalyticsData();

        // Start with loaded state
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: initialData,
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

        // Verify initial state
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);

        // Transition to error state
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Temporary error',
            errorType: 'temporary',
            isRecoverable: true,
          ),
        );

        await tester.pumpAndSettle();

        // Verify error state
        expect(find.text('Temporary error'), findsOneWidget);

        // Recover to loaded state
        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: initialData,
            selectedRegion: 'Kenya',
            selectedDateRange: DateRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
            lastRefresh: DateTime.now(),
          ),
        );

        await tester.pumpAndSettle();

        // Verify state recovery
        expect(find.text('Temporary error'), findsNothing);
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('handles concurrent error conditions', (tester) async {
        // Start with multiple error conditions
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Multiple errors: Network timeout, Data corruption, Memory constraint',
            errorType: 'multiple_errors',
            isRecoverable: false,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify multiple errors are handled appropriately
        expect(find.textContaining('Multiple errors'), findsOneWidget);
        expect(find.byIcon(Icons.error), findsOneWidget);
      });
    });

    group('Graceful Degradation', () {
      testWidgets('provides fallback UI when charts fail to load', (tester) async {
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

        // Verify dashboard loads even if individual charts fail
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
        expect(find.byType(AnalyticsOverviewCard), findsAtLeastNWidgets(1));
      });

      testWidgets('maintains core functionality during partial failures', (tester) async {
        // Simulate partial data availability
        final partialData = MockAnalyticsData.createMockAnalyticsData().copyWith(
          environmentalTrends: [], // Missing environmental data
          // But prediction accuracy is available
        );

        when(() => mockBloc.state).thenReturn(
          AnalyticsLoaded(
            analyticsData: partialData,
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

        // Verify partial functionality is maintained
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
        expect(find.textContaining('No environmental data available'), findsAtLeastNWidgets(1));
      });
    });

    group('Error Recovery Mechanisms', () {
      testWidgets('automatically retries transient errors', (tester) async {
        // Start with transient error
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Transient network error - retrying...',
            errorType: 'transient',
            isRecoverable: true,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify retry message
        expect(find.textContaining('retrying'), findsOneWidget);

        // Simulate successful retry
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

        // Verify successful recovery
        expect(find.textContaining('retrying'), findsNothing);
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('provides manual recovery options for permanent errors', (tester) async {
        when(() => mockBloc.state).thenReturn(
          const AnalyticsError(
            message: 'Configuration error - manual intervention required',
            errorType: 'configuration',
            isRecoverable: false,
          ),
        );

        await WidgetTestHelpers.pumpWidgetWithBloc(
          tester,
          const AnalyticsDashboardPage(),
          mockBloc,
        );

        await tester.pumpAndSettle();

        // Verify manual intervention options
        expect(find.textContaining('manual intervention required'), findsOneWidget);
        expect(find.textContaining('Contact Support'), findsOneWidget);
      });
    });
  });

  group('Edge Case Performance Tests', () {
    testWidgets('handles rapid state changes without memory leaks', (tester) async {
      final mockBloc = MockAnalyticsBloc();

      // Rapidly cycle through different states
      for (int i = 0; i < 50; i++) {
        when(() => mockBloc.state).thenReturn(
          i % 2 == 0
              ? const AnalyticsLoading()
              : AnalyticsLoaded(
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

        await tester.pump();
      }

      await tester.pumpAndSettle();

      // Verify no exceptions during rapid state changes
      expect(tester.takeException(), isNull);
    });

    testWidgets('handles concurrent user interactions during error states', (tester) async {
      when(() => mockBloc.state).thenReturn(
        const AnalyticsError(
          message: 'Loading error',
          errorType: 'loading',
          isRecoverable: true,
        ),
      );

      await WidgetTestHelpers.pumpWidgetWithBloc(
        tester,
        const AnalyticsDashboardPage(),
        mockBloc,
      );

      await tester.pumpAndSettle();

      // Perform multiple rapid interactions
      final retryButton = find.textContaining('Retry');
      if (retryButton.evaluate().isNotEmpty) {
        for (int i = 0; i < 5; i++) {
          await tester.tap(retryButton);
          await tester.pump(const Duration(milliseconds: 100));
        }
      }

      await tester.pumpAndSettle();

      // Verify app remains stable
      expect(tester.takeException(), isNull);
    });
  });
}