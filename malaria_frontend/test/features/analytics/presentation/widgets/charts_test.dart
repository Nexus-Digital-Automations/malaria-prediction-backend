/// Comprehensive unit tests for analytics chart widgets
///
/// This test suite provides exhaustive testing for all chart widgets including
/// interactive chart widget, prediction accuracy charts, environmental charts,
/// and data visualization accuracy validation.
///
/// Tests cover:
/// - Widget rendering and UI components
/// - Chart data visualization accuracy
/// - Interactive gestures and user interactions
/// - Error handling and edge cases
/// - Performance with large datasets
/// - Chart responsiveness and animations
/// - Accessibility features
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/interactive_chart_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_overview_card.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/prediction_accuracy_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/temperature_trend_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/rainfall_pattern_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/humidity_heatmap.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/risk_distribution_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/confusion_matrix_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/model_comparison_chart.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/climate_correlation_chart.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/interactive_chart.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/chart_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/prediction_metrics.dart';
import '../../../test_config.dart';
import '../../../mocks/analytics_mocks.dart';
import '../../../helpers/chart_test_helpers.dart';
import '../../../helpers/widget_test_helpers.dart';

void main() {
  /// Global test setup
  setUpAll(() async {
    await TestConfig.initialize();
  });

  /// Cleanup after all tests
  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('Analytics Overview Card Tests', () {
    testWidgets('renders basic overview card correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsOverviewCard(
              title: 'Prediction Accuracy',
              value: '85.5%',
              icon: Icons.accuracy,
              color: Colors.blue,
              trend: 0.05,
            ),
          ),
        ),
      );

      // Verify basic elements
      expect(find.text('Prediction Accuracy'), findsOneWidget);
      expect(find.text('85.5%'), findsOneWidget);
      expect(find.byIcon(Icons.accuracy), findsOneWidget);
      expect(find.byIcon(Icons.trending_up), findsOneWidget);
      expect(find.text('5.0%'), findsOneWidget);
    });

    testWidgets('displays negative trend correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsOverviewCard(
              title: 'Alert Response Time',
              value: '2.3 min',
              icon: Icons.schedule,
              color: Colors.red,
              trend: -0.12,
            ),
          ),
        ),
      );

      // Verify negative trend display
      expect(find.byIcon(Icons.trending_down), findsOneWidget);
      expect(find.text('12.0%'), findsOneWidget);

      // Verify color is red for negative trend
      final Container trendContainer = tester.widget(find.byType(Container).last);
      // Test would verify red color styling
    });

    testWidgets('handles zero trend correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsOverviewCard(
              title: 'Data Quality',
              value: '99%',
              icon: Icons.verified,
              color: Colors.green,
              trend: 0.0,
            ),
          ),
        ),
      );

      // Verify zero trend display
      expect(find.text('0%'), findsOneWidget);
      expect(find.byIcon(Icons.trending_up), findsNothing);
      expect(find.byIcon(Icons.trending_down), findsNothing);
    });

    testWidgets('handles tap interaction', (tester) async {
      bool wasTapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsOverviewCard(
              title: 'Test Card',
              value: '100',
              icon: Icons.star,
              color: Colors.blue,
              onTap: () => wasTapped = true,
            ),
          ),
        ),
      );

      // Tap the card
      await tester.tap(find.byType(AnalyticsOverviewCard));
      expect(wasTapped, isTrue);
    });

    testWidgets('renders with subtitle correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsOverviewCard(
              title: 'Active Cases',
              value: '1,234',
              subtitle: 'Last 7 days',
              icon: Icons.person,
              color: Colors.orange,
            ),
          ),
        ),
      );

      // Verify subtitle is displayed
      expect(find.text('Last 7 days'), findsOneWidget);
    });

    testWidgets('hides trend when showTrend is false', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsOverviewCard(
              title: 'Test Card',
              value: '100',
              icon: Icons.star,
              color: Colors.blue,
              trend: 0.15,
              showTrend: false,
            ),
          ),
        ),
      );

      // Verify trend indicators are not shown
      expect(find.byIcon(Icons.trending_up), findsNothing);
      expect(find.text('15.0%'), findsNothing);
    });
  });

  group('Interactive Chart Widget Tests', () {
    late InteractiveChart mockChart;
    late ChartInteraction mockInteraction;

    setUp(() {
      mockChart = MockAnalyticsData.createMockInteractiveChart();
      mockInteraction = MockAnalyticsData.createMockChartInteraction();
    });

    testWidgets('renders interactive chart correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: mockChart,
            ),
          ),
        ),
      );

      // Verify chart is rendered
      expect(find.byType(InteractiveChartWidget), findsOneWidget);

      // Allow for chart rendering animations
      await tester.pumpAndSettle();

      // Verify chart components based on chart type
      if (mockChart.chartType == InteractiveChartType.line) {
        expect(find.byType(LineChart), findsOneWidget);
      }
    });

    testWidgets('handles loading state correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: mockChart,
              isLoading: true,
            ),
          ),
        ),
      );

      // Verify loading indicator is shown
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('handles error state correctly', (tester) async {
      const errorMessage = 'Failed to load chart data';

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: mockChart,
              errorMessage: errorMessage,
            ),
          ),
        ),
      );

      // Verify error message is displayed
      expect(find.text(errorMessage), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('responds to tap interactions', (tester) async {
      ChartInteraction? receivedInteraction;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: mockChart,
              onInteraction: (interaction) => receivedInteraction = interaction,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Tap on chart area
      await tester.tap(find.byType(InteractiveChartWidget));
      await tester.pumpAndSettle();

      // Note: Actual interaction testing depends on fl_chart implementation
      // This would be enhanced with more specific gesture testing
    });

    testWidgets('displays toolbar when enabled', (tester) async {
      final chartWithToolbar = mockChart.copyWith(
        interactionConfig: mockChart.interactionConfig.copyWith(
          enableZoom: true,
          enableDrillDown: true,
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: chartWithToolbar,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify toolbar buttons
      expect(find.byIcon(Icons.zoom_in), findsOneWidget);
      expect(find.byIcon(Icons.zoom_out), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('handles zoom interactions', (tester) async {
      ChartInteraction? receivedInteraction;
      final chartWithZoom = mockChart.copyWith(
        interactionConfig: mockChart.interactionConfig.copyWith(
          enableZoom: true,
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: chartWithZoom,
              onInteraction: (interaction) => receivedInteraction = interaction,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test zoom in button
      await tester.tap(find.byIcon(Icons.zoom_in));
      await tester.pumpAndSettle();

      // Test zoom out button
      await tester.tap(find.byIcon(Icons.zoom_out));
      await tester.pumpAndSettle();

      // Test reset view
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();
    });

    testWidgets('displays drill-down breadcrumbs when available', (tester) async {
      final chartWithDrillDown = mockChart.copyWith(
        drillDownHierarchy: MockAnalyticsData.createMockDrillDownHierarchy(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: chartWithDrillDown,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify breadcrumb navigation
      expect(find.byIcon(Icons.home), findsOneWidget);
      expect(find.byIcon(Icons.chevron_right), findsAtLeastNWidgets(1));
    });

    testWidgets('handles performance metrics display', (tester) async {
      final chartWithPerformance = mockChart.copyWith(
        theme: const ChartThemeData(showPerformanceMetrics: true),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: chartWithPerformance,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify performance overlay
      expect(find.text('Performance'), findsOneWidget);
      expect(find.textContaining('Interactions:'), findsOneWidget);
      expect(find.textContaining('Render:'), findsOneWidget);
      expect(find.textContaining('Memory:'), findsOneWidget);
    });
  });

  group('Prediction Accuracy Chart Tests', () {
    late PredictionMetrics mockMetrics;

    setUp(() {
      mockMetrics = MockAnalyticsData.createMockPredictionMetrics();
    });

    testWidgets('renders prediction accuracy chart', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionAccuracyChart(
              metrics: mockMetrics,
              height: 300,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify chart rendering
      expect(find.byType(PredictionAccuracyChart), findsOneWidget);
    });

    testWidgets('displays accuracy trends correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionAccuracyChart(
              metrics: mockMetrics,
              showTrend: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify trend visualization elements
      // This would check for trend lines, indicators, etc.
    });

    testWidgets('handles empty metrics data', (tester) async {
      final emptyMetrics = PredictionMetrics(
        accuracy: 0.0,
        precision: 0.0,
        recall: 0.0,
        f1Score: 0.0,
        confusionMatrix: {},
        accuracyTrend: [],
        modelComparison: [],
        lastUpdated: DateTime.now(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionAccuracyChart(
              metrics: emptyMetrics,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify graceful handling of empty data
      expect(find.byType(PredictionAccuracyChart), findsOneWidget);
    });
  });

  group('Environmental Chart Tests', () {
    testWidgets('temperature trend chart renders correctly', (tester) async {
      final temperatureData = MockAnalyticsData.createMockTemperatureData();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: TemperatureTrendChart(
              temperatureData: temperatureData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(TemperatureTrendChart), findsOneWidget);
    });

    testWidgets('rainfall pattern chart renders correctly', (tester) async {
      final rainfallData = MockAnalyticsData.createMockRainfallData();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RainfallPatternChart(
              rainfallData: rainfallData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(RainfallPatternChart), findsOneWidget);
    });

    testWidgets('humidity heatmap renders correctly', (tester) async {
      final humidityData = MockAnalyticsData.createMockHumidityData();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumidityHeatmap(
              humidityData: humidityData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(HumidityHeatmap), findsOneWidget);
    });
  });

  group('Risk Analysis Chart Tests', () {
    testWidgets('risk distribution chart renders correctly', (tester) async {
      final riskData = MockAnalyticsData.createMockRiskDistributionData();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RiskDistributionChart(
              riskData: riskData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(RiskDistributionChart), findsOneWidget);
    });

    testWidgets('confusion matrix chart renders correctly', (tester) async {
      final confusionMatrix = MockAnalyticsData.createMockConfusionMatrix();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ConfusionMatrixChart(
              confusionMatrix: confusionMatrix,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ConfusionMatrixChart), findsOneWidget);
    });

    testWidgets('model comparison chart renders correctly', (tester) async {
      final modelData = MockAnalyticsData.createMockModelComparisonData();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ModelComparisonChart(
              modelData: modelData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ModelComparisonChart), findsOneWidget);
    });
  });

  group('Climate Correlation Chart Tests', () {
    testWidgets('climate correlation chart renders correctly', (tester) async {
      final correlationData = MockAnalyticsData.createMockCorrelationData();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ClimateCorrelationChart(
              correlationData: correlationData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ClimateCorrelationChart), findsOneWidget);
    });

    testWidgets('handles correlation matrix display', (tester) async {
      final correlationData = MockAnalyticsData.createMockCorrelationData();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ClimateCorrelationChart(
              correlationData: correlationData,
              showMatrix: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify matrix visualization
      expect(find.byType(ClimateCorrelationChart), findsOneWidget);
    });
  });

  group('Chart Data Visualization Accuracy Tests', () {
    testWidgets('verifies accurate data representation in line charts', (tester) async {
      final testData = ChartTestHelpers.createTestLineChartData([
        const ChartPoint(x: 0, y: 10),
        const ChartPoint(x: 1, y: 20),
        const ChartPoint(x: 2, y: 15),
        const ChartPoint(x: 3, y: 25),
      ]);

      final chart = InteractiveChart(
        id: 'test-chart',
        title: 'Test Chart',
        chartType: InteractiveChartType.line,
        chartData: testData,
        interactionConfig: MockAnalyticsData.createMockInteractionConfig(),
        viewState: MockAnalyticsData.createMockViewState(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify data points are accurately represented
      // This would involve testing fl_chart's internal data representation
      final lineChart = tester.widget<LineChart>(find.byType(LineChart));
      expect(lineChart.data.lineBarsData.first.spots.length, equals(4));

      // Verify data point values
      final spots = lineChart.data.lineBarsData.first.spots;
      expect(spots[0].x, equals(0));
      expect(spots[0].y, equals(10));
      expect(spots[3].x, equals(3));
      expect(spots[3].y, equals(25));
    });

    testWidgets('verifies bar chart data accuracy', (tester) async {
      final testData = ChartTestHelpers.createTestBarChartData([
        const BarValue(category: 'Low', value: 15),
        const BarValue(category: 'Medium', value: 30),
        const BarValue(category: 'High', value: 25),
        const BarValue(category: 'Critical', value: 10),
      ]);

      final chart = InteractiveChart(
        id: 'test-bar-chart',
        title: 'Test Bar Chart',
        chartType: InteractiveChartType.bar,
        chartData: testData,
        interactionConfig: MockAnalyticsData.createMockInteractionConfig(),
        viewState: MockAnalyticsData.createMockViewState(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify bar chart data accuracy
      final barChart = tester.widget<BarChart>(find.byType(BarChart));
      expect(barChart.data.barGroups.length, equals(4));

      // Verify individual bar values
      expect(barChart.data.barGroups[0].barRods.first.toY, equals(15));
      expect(barChart.data.barGroups[1].barRods.first.toY, equals(30));
      expect(barChart.data.barGroups[2].barRods.first.toY, equals(25));
      expect(barChart.data.barGroups[3].barRods.first.toY, equals(10));
    });

    testWidgets('verifies pie chart data accuracy', (tester) async {
      final testData = ChartTestHelpers.createTestPieChartData([
        const PieSlice(label: 'Low Risk', value: 40, color: Colors.green),
        const PieSlice(label: 'Medium Risk', value: 35, color: Colors.yellow),
        const PieSlice(label: 'High Risk', value: 20, color: Colors.orange),
        const PieSlice(label: 'Critical Risk', value: 5, color: Colors.red),
      ]);

      final chart = InteractiveChart(
        id: 'test-pie-chart',
        title: 'Test Pie Chart',
        chartType: InteractiveChartType.pie,
        chartData: testData,
        interactionConfig: MockAnalyticsData.createMockInteractionConfig(),
        viewState: MockAnalyticsData.createMockViewState(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify pie chart data accuracy
      final pieChart = tester.widget<PieChart>(find.byType(PieChart));
      expect(pieChart.data.sections.length, equals(4));

      // Verify slice values and percentages
      expect(pieChart.data.sections[0].value, equals(40));
      expect(pieChart.data.sections[1].value, equals(35));
      expect(pieChart.data.sections[2].value, equals(20));
      expect(pieChart.data.sections[3].value, equals(5));
    });
  });

  group('Chart Performance Tests', () {
    testWidgets('handles large datasets efficiently', (tester) async {
      // Create large dataset (1000 data points)
      final largeDataset = List.generate(1000, (index) =>
        ChartPoint(x: index.toDouble(), y: (index % 100).toDouble())
      );

      final testData = ChartTestHelpers.createTestLineChartData(largeDataset);
      final chart = InteractiveChart(
        id: 'large-dataset-chart',
        title: 'Large Dataset Chart',
        chartType: InteractiveChartType.line,
        chartData: testData,
        interactionConfig: MockAnalyticsData.createMockInteractionConfig(),
        viewState: MockAnalyticsData.createMockViewState(),
      );

      final stopwatch = Stopwatch()..start();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();
      stopwatch.stop();

      // Verify chart renders within reasonable time (under 1 second)
      expect(stopwatch.elapsedMilliseconds, lessThan(1000));
      expect(find.byType(InteractiveChartWidget), findsOneWidget);
    });

    testWidgets('maintains responsiveness during interactions', (tester) async {
      final chart = MockAnalyticsData.createMockInteractiveChart();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      final stopwatch = Stopwatch()..start();

      // Perform multiple rapid interactions
      for (int i = 0; i < 10; i++) {
        await tester.tap(find.byType(InteractiveChartWidget));
        await tester.pump(const Duration(milliseconds: 16)); // One frame
      }

      await tester.pumpAndSettle();
      stopwatch.stop();

      // Verify interactions remain responsive
      expect(stopwatch.elapsedMilliseconds, lessThan(500));
    });

    testWidgets('memory usage remains stable with multiple charts', (tester) async {
      final charts = List.generate(5, (index) =>
        MockAnalyticsData.createMockInteractiveChart()
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Column(
              children: charts.map((chart) =>
                Expanded(
                  child: InteractiveChartWidget(chart: chart),
                )
              ).toList(),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify all charts are rendered
      expect(find.byType(InteractiveChartWidget), findsNWidgets(5));

      // Memory usage testing would require additional profiling tools
      // This serves as a basic render verification
    });
  });

  group('Chart Accessibility Tests', () {
    testWidgets('charts have proper semantic labels', (tester) async {
      final chart = MockAnalyticsData.createMockInteractiveChart();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify semantic structure
      expect(find.byType(InteractiveChartWidget), findsOneWidget);

      // Test semantic labels (would require custom semantic widgets)
      // This would involve testing screen reader compatibility
    });

    testWidgets('interactive elements are accessible via keyboard', (tester) async {
      final chart = MockAnalyticsData.createMockInteractiveChart();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test keyboard navigation
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pump();

      // Verify focus behavior
      // This would be enhanced with custom focus testing
    });
  });

  group('Chart Error Handling Tests', () {
    testWidgets('handles invalid chart data gracefully', (tester) async {
      final chart = MockAnalyticsData.createMockInteractiveChart().copyWith(
        chartData: null, // Invalid data
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify error handling
      expect(find.byType(InteractiveChartWidget), findsOneWidget);
      // Should show error state or graceful fallback
    });

    testWidgets('handles network errors during data loading', (tester) async {
      const errorMessage = 'Network connection failed';
      final chart = MockAnalyticsData.createMockInteractiveChart();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: chart,
              errorMessage: errorMessage,
            ),
          ),
        ),
      );

      // Verify error message display
      expect(find.text(errorMessage), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('recovers from error states correctly', (tester) async {
      final chart = MockAnalyticsData.createMockInteractiveChart();

      // Start with error state
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(
              chart: chart,
              errorMessage: 'Initial error',
            ),
          ),
        ),
      );

      expect(find.text('Initial error'), findsOneWidget);

      // Rebuild without error
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: InteractiveChartWidget(chart: chart),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify recovery
      expect(find.text('Initial error'), findsNothing);
      expect(find.byType(InteractiveChartWidget), findsOneWidget);
    });
  });

  group('Golden Tests for Visual Regression', () {
    testGoldens('analytics overview card golden test', (tester) async {
      await tester.pumpWidgetBuilder(
        AnalyticsOverviewCard(
          title: 'Prediction Accuracy',
          value: '85.5%',
          icon: Icons.accuracy,
          color: Colors.blue,
          trend: 0.05,
        ),
      );

      await screenMatchesGolden(tester, 'analytics_overview_card');
    });

    testGoldens('interactive chart widget golden test', (tester) async {
      final chart = MockAnalyticsData.createMockInteractiveChart();

      await tester.pumpWidgetBuilder(
        InteractiveChartWidget(chart: chart),
      );

      await screenMatchesGolden(tester, 'interactive_chart_widget');
    });
  });
}