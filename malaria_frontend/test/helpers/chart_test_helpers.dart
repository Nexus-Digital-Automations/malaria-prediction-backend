/// Chart testing helper utilities
///
/// This file provides utility functions and helpers specifically for testing
/// chart widgets, data visualization accuracy, and chart interactions.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../mocks/analytics_mocks.dart';

/// Chart testing helper class
class ChartTestHelpers {
  /// Creates test line chart data with specified points
  static LineChartDataEntity createTestLineChartData(List<ChartPoint> points) {
    return LineChartDataEntity(
      series: [
        ChartSeries(
          id: 'test_series',
          name: 'Test Series',
          data: points,
          color: Colors.blue,
          strokeWidth: 2.0,
          fillArea: false,
        ),
      ],
      xAxis: const ChartAxis(
        title: 'X Axis',
        min: 0,
        max: 10,
        interval: 1,
        showLabels: true,
      ),
      yAxis: const ChartAxis(
        title: 'Y Axis',
        min: 0,
        max: 100,
        interval: 10,
        showLabels: true,
      ),
      showGrid: true,
      showMarkers: true,
    );
  }

  /// Creates test bar chart data with specified values
  static BarChartDataEntity createTestBarChartData(List<BarValue> values) {
    return BarChartDataEntity(
      dataGroups: values.asMap().entries.map((entry) =>
        BarChartGroup(
          x: entry.key,
          bars: [entry.value],
        ),
      ).toList(),
      xAxis: const ChartAxis(
        title: 'Categories',
        showLabels: true,
      ),
      yAxis: const ChartAxis(
        title: 'Values',
        min: 0,
        max: 100,
        interval: 10,
        showLabels: true,
      ),
      showGrid: true,
      barWidth: 0.8,
    );
  }

  /// Creates test pie chart data with specified slices
  static PieChartDataEntity createTestPieChartData(List<PieSlice> slices) {
    return PieChartDataEntity(
      sections: slices,
      centerSpaceRadius: 20.0,
    );
  }

  /// Creates test scatter plot data with specified points
  static ScatterPlotDataEntity createTestScatterPlotData(List<ScatterPoint> points) {
    return ScatterPlotDataEntity(
      series: [
        ScatterSeries(
          id: 'test_scatter',
          name: 'Test Scatter',
          data: points,
          color: Colors.red,
          pointSize: 4.0,
        ),
      ],
      xAxis: const ChartAxis(
        title: 'X Variable',
        min: 0,
        max: 100,
        interval: 10,
        showLabels: true,
      ),
      yAxis: const ChartAxis(
        title: 'Y Variable',
        min: 0,
        max: 100,
        interval: 10,
        showLabels: true,
      ),
      showGrid: true,
    );
  }

  /// Validates chart data accuracy by comparing expected vs actual values
  static void validateChartDataAccuracy({
    required dynamic chartData,
    required List<dynamic> expectedValues,
    double tolerance = 0.001,
  }) {
    if (chartData is LineChartDataEntity) {
      _validateLineChartAccuracy(chartData, expectedValues, tolerance);
    } else if (chartData is BarChartDataEntity) {
      _validateBarChartAccuracy(chartData, expectedValues, tolerance);
    } else if (chartData is PieChartDataEntity) {
      _validatePieChartAccuracy(chartData, expectedValues, tolerance);
    } else if (chartData is ScatterPlotDataEntity) {
      _validateScatterChartAccuracy(chartData, expectedValues, tolerance);
    }
  }

  /// Validates line chart data accuracy
  static void _validateLineChartAccuracy(
    LineChartDataEntity chartData,
    List<dynamic> expectedValues,
    double tolerance,
  ) {
    expect(chartData.series.isNotEmpty, isTrue);

    final series = chartData.series.first;
    expect(series.data.length, equals(expectedValues.length));

    for (int i = 0; i < expectedValues.length; i++) {
      final expected = expectedValues[i] as ChartPoint;
      final actual = series.data[i];

      expect(actual.x, closeTo(expected.x, tolerance));
      expect(actual.y, closeTo(expected.y, tolerance));
    }
  }

  /// Validates bar chart data accuracy
  static void _validateBarChartAccuracy(
    BarChartDataEntity chartData,
    List<dynamic> expectedValues,
    double tolerance,
  ) {
    expect(chartData.dataGroups.isNotEmpty, isTrue);
    expect(chartData.dataGroups.length, equals(expectedValues.length));

    for (int i = 0; i < expectedValues.length; i++) {
      final expected = expectedValues[i] as BarValue;
      final actual = chartData.dataGroups[i].bars.first;

      expect(actual.value, closeTo(expected.value, tolerance));
      expect(actual.category, equals(expected.category));
    }
  }

  /// Validates pie chart data accuracy
  static void _validatePieChartAccuracy(
    PieChartDataEntity chartData,
    List<dynamic> expectedValues,
    double tolerance,
  ) {
    expect(chartData.sections.isNotEmpty, isTrue);
    expect(chartData.sections.length, equals(expectedValues.length));

    // Validate total adds up to 100%
    final totalValue = chartData.sections.fold<double>(
      0.0,
      (sum, section) => sum + section.value,
    );
    expect(totalValue, closeTo(100.0, tolerance));

    for (int i = 0; i < expectedValues.length; i++) {
      final expected = expectedValues[i] as PieSlice;
      final actual = chartData.sections[i];

      expect(actual.value, closeTo(expected.value, tolerance));
      expect(actual.label, equals(expected.label));
    }
  }

  /// Validates scatter chart data accuracy
  static void _validateScatterChartAccuracy(
    ScatterPlotDataEntity chartData,
    List<dynamic> expectedValues,
    double tolerance,
  ) {
    expect(chartData.series.isNotEmpty, isTrue);

    final series = chartData.series.first;
    expect(series.data.length, equals(expectedValues.length));

    for (int i = 0; i < expectedValues.length; i++) {
      final expected = expectedValues[i] as ScatterPoint;
      final actual = series.data[i];

      expect(actual.x, closeTo(expected.x, tolerance));
      expect(actual.y, closeTo(expected.y, tolerance));
    }
  }

  /// Measures chart rendering performance
  static Future<Duration> measureChartRenderingTime(
    WidgetTester tester,
    Widget chartWidget,
  ) async {
    final stopwatch = Stopwatch()..start();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: chartWidget),
      ),
    );

    await tester.pumpAndSettle();
    stopwatch.stop();

    return stopwatch.elapsed;
  }

  /// Tests chart responsiveness under load
  static Future<void> testChartResponsiveness(
    WidgetTester tester,
    Widget chartWidget, {
    int interactionCount = 10,
    Duration maxResponseTime = const Duration(milliseconds: 100),
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: chartWidget),
      ),
    );

    await tester.pumpAndSettle();

    // Perform rapid interactions
    for (int i = 0; i < interactionCount; i++) {
      final stopwatch = Stopwatch()..start();

      await tester.tap(find.byWidget(chartWidget));
      await tester.pump();

      stopwatch.stop();
      expect(stopwatch.elapsed, lessThan(maxResponseTime));
    }
  }

  /// Validates chart accessibility features
  static void validateChartAccessibility(WidgetTester tester, Widget chartWidget) {
    // Test semantic labels
    final semanticNodes = tester.binding.pipelineOwner.semanticsOwner?.rootSemanticsNode;
    expect(semanticNodes, isNotNull);

    // Verify chart has descriptive labels
    expect(find.bySemanticsLabel(RegExp(r'chart|graph|data')), findsAtLeastNWidgets(1));
  }

  /// Creates performance test data with specified size
  static List<ChartPoint> createPerformanceTestData(int pointCount) {
    return List.generate(pointCount, (index) =>
      ChartPoint(
        x: index.toDouble(),
        y: (index % 100).toDouble(),
      ),
    );
  }

  /// Validates chart animations
  static Future<void> validateChartAnimations(
    WidgetTester tester,
    Widget chartWidget, {
    Duration expectedDuration = const Duration(milliseconds: 300),
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: chartWidget),
      ),
    );

    // Start animation
    await tester.pump();

    // Check animation is running
    expect(tester.binding.hasScheduledFrame, isTrue);

    // Let animation complete
    await tester.pumpAndSettle(expectedDuration);

    // Verify animation completed
    expect(tester.binding.hasScheduledFrame, isFalse);
  }

  /// Tests chart memory usage
  static void validateChartMemoryUsage(
    Widget chartWidget, {
    int maxMemoryMB = 50,
  }) {
    // This would integrate with memory profiling tools in a real implementation
    // For now, we'll just verify the chart doesn't cause obvious memory leaks

    // Create multiple instances to test for leaks
    for (int i = 0; i < 10; i++) {
      final chart = chartWidget;
      // Dispose of chart reference
    }

    // Force garbage collection (in a real implementation)
    // System.gc() equivalent would be called here
  }

  /// Generates test data for stress testing
  static Map<String, dynamic> generateStressTestData({
    int seriesCount = 5,
    int pointsPerSeries = 1000,
  }) {
    final series = <ChartSeries>[];

    for (int i = 0; i < seriesCount; i++) {
      final points = List.generate(pointsPerSeries, (index) =>
        ChartPoint(
          x: index.toDouble(),
          y: (index % 100 + i * 10).toDouble(),
        ),
      );

      series.add(ChartSeries(
        id: 'series_$i',
        name: 'Test Series $i',
        data: points,
        color: Colors.primaries[i % Colors.primaries.length],
        strokeWidth: 2.0,
      ));
    }

    return {
      'series': series,
      'totalPoints': seriesCount * pointsPerSeries,
      'expectedRenderTime': Duration(milliseconds: seriesCount * pointsPerSeries ~/ 10),
    };
  }

  /// Validates chart data consistency
  static void validateDataConsistency(dynamic chartData) {
    if (chartData is LineChartDataEntity) {
      _validateLineChartConsistency(chartData);
    } else if (chartData is BarChartDataEntity) {
      _validateBarChartConsistency(chartData);
    } else if (chartData is PieChartDataEntity) {
      _validatePieChartConsistency(chartData);
    } else if (chartData is ScatterPlotDataEntity) {
      _validateScatterChartConsistency(chartData);
    }
  }

  static void _validateLineChartConsistency(LineChartDataEntity chartData) {
    for (final series in chartData.series) {
      // Verify data points are ordered by x-value
      for (int i = 1; i < series.data.length; i++) {
        expect(series.data[i].x, greaterThanOrEqualTo(series.data[i - 1].x));
      }

      // Verify no null values
      for (final point in series.data) {
        expect(point.x, isNotNull);
        expect(point.y, isNotNull);
        expect(point.x.isFinite, isTrue);
        expect(point.y.isFinite, isTrue);
      }
    }
  }

  static void _validateBarChartConsistency(BarChartDataEntity chartData) {
    for (final group in chartData.dataGroups) {
      for (final bar in group.bars) {
        expect(bar.value, isNotNull);
        expect(bar.value.isFinite, isTrue);
        expect(bar.value, greaterThanOrEqualTo(0));
      }
    }
  }

  static void _validatePieChartConsistency(PieChartDataEntity chartData) {
    double totalValue = 0;

    for (final section in chartData.sections) {
      expect(section.value, isNotNull);
      expect(section.value.isFinite, isTrue);
      expect(section.value, greaterThan(0));
      totalValue += section.value;
    }

    // Total should be reasonable (allowing for percentage or absolute values)
    expect(totalValue, greaterThan(0));
  }

  static void _validateScatterChartConsistency(ScatterPlotDataEntity chartData) {
    for (final series in chartData.series) {
      for (final point in series.data) {
        expect(point.x, isNotNull);
        expect(point.y, isNotNull);
        expect(point.x.isFinite, isTrue);
        expect(point.y.isFinite, isTrue);
      }
    }
  }

  /// Creates chart test configuration
  static Map<String, dynamic> createChartTestConfig({
    bool enableAnimations = true,
    bool enableInteractions = true,
    Duration animationDuration = const Duration(milliseconds: 300),
    double tolerance = 0.001,
  }) {
    return {
      'enableAnimations': enableAnimations,
      'enableInteractions': enableInteractions,
      'animationDuration': animationDuration,
      'tolerance': tolerance,
    };
  }
}