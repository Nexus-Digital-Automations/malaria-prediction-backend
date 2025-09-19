/// Bar chart widget for categorical data display using fl_chart
///
/// This widget displays categorical data such as risk levels by region,
/// alert statistics by severity, prediction accuracy by risk category, etc.
/// It supports grouped bars, stacked bars, and horizontal orientation.
///
/// Usage:
/// ```dart
/// BarChartWidget(
///   title: 'Risk Distribution by Region',
///   categories: ['Region A', 'Region B', 'Region C'],
///   series: [
///     BarSeries(
///       name: 'High Risk',
///       values: [25, 15, 30],
///       color: Colors.red,
///     ),
///   ],
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../domain/entities/analytics_data.dart';
import 'base_chart_widget.dart';

/// Data series for bar chart
class BarSeries {
  /// Display name for this series
  final String name;

  /// Values for each category
  final List<double> values;

  /// Color for this series
  final Color color;

  /// Whether this series is enabled/visible
  final bool isEnabled;

  /// Opacity of bars
  final double opacity;

  /// Custom labels for values (optional)
  final List<String>? valueLabels;

  /// Metadata for each value (optional)
  final List<Map<String, dynamic>>? metadata;

  const BarSeries({
    required this.name,
    required this.values,
    required this.color,
    this.isEnabled = true,
    this.opacity = 0.8,
    this.valueLabels,
    this.metadata,
  });

  /// Creates a copy with updated properties
  BarSeries copyWith({
    String? name,
    List<double>? values,
    Color? color,
    bool? isEnabled,
    double? opacity,
    List<String>? valueLabels,
    List<Map<String, dynamic>>? metadata,
  }) {
    return BarSeries(
      name: name ?? this.name,
      values: values ?? this.values,
      color: color ?? this.color,
      isEnabled: isEnabled ?? this.isEnabled,
      opacity: opacity ?? this.opacity,
      valueLabels: valueLabels ?? this.valueLabels,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Creates bar series from alert statistics
  factory BarSeries.fromAlertStatistics(
    AlertStatistics stats,
    String seriesName,
    Color color,
  ) {
    const categories = AlertSeverity.values;
    final values = categories.map((severity) {
      return (stats.alertsBySeverity[severity] ?? 0).toDouble();
    }).toList();

    return BarSeries(
      name: seriesName,
      values: values,
      color: color,
      metadata: categories.map((severity) => {
        'severity': severity,
        'count': stats.alertsBySeverity[severity] ?? 0,
      }).toList(),
    );
  }

  /// Creates bar series from risk level accuracy
  factory BarSeries.fromRiskLevelAccuracy(
    Map<String, double> accuracyByRisk,
    String seriesName,
    Color color,
  ) {
    final riskLevels = ['low', 'medium', 'high', 'critical'];
    final values = riskLevels.map((level) {
      return accuracyByRisk[level] ?? 0.0;
    }).toList();

    return BarSeries(
      name: seriesName,
      values: values,
      color: color,
      metadata: riskLevels.map((level) => {
        'riskLevel': level,
        'accuracy': accuracyByRisk[level] ?? 0.0,
      }).toList(),
    );
  }

  /// Creates bar series from environmental factor distribution
  factory BarSeries.fromEnvironmentalDistribution(
    List<EnvironmentalTrend> trends,
    EnvironmentalFactor targetFactor,
    String seriesName,
    Color color,
  ) {
    // Group by month or region (simplified example)
    final monthlyValues = <int, List<double>>{};

    for (final trend in trends) {
      if (trend.factor == targetFactor) {
        final month = trend.date.month;
        monthlyValues.putIfAbsent(month, () => []).add(trend.value);
      }
    }

    final values = List.generate(12, (index) {
      final month = index + 1;
      final monthData = monthlyValues[month] ?? [];
      return monthData.isEmpty
          ? 0.0
          : monthData.reduce((a, b) => a + b) / monthData.length;
    });

    return BarSeries(
      name: seriesName,
      values: values,
      color: color,
      metadata: List.generate(12, (index) => {
        'month': index + 1,
        'factor': targetFactor,
        'average': values[index],
      }),
    );
  }
}

/// Bar chart orientation
enum BarChartOrientation {
  vertical,
  horizontal,
}

/// Bar chart style
enum BarChartStyle {
  grouped,
  stacked,
  percentage,
}

/// Bar chart widget for categorical data
class BarChartWidget extends StatefulWidget {
  /// Chart title
  final String title;

  /// Chart subtitle
  final String? subtitle;

  /// Category labels
  final List<String> categories;

  /// Data series to display
  final List<BarSeries> series;

  /// Chart height
  final double height;

  /// Chart width (null for responsive)
  final double? width;

  /// Chart orientation
  final BarChartOrientation orientation;

  /// Chart style (grouped, stacked, percentage)
  final BarChartStyle style;

  /// Whether to show legend
  final bool showLegend;

  /// Whether to show values on bars
  final bool showValues;

  /// Y-axis range (null for auto)
  final (double min, double max)? yRange;

  /// Number format for Y-axis labels
  final String Function(double)? yAxisFormatter;

  /// Whether to show grid
  final bool showGrid;

  /// Bar width (0.0 to 1.0)
  final double barWidth;

  /// Space between bar groups (0.0 to 1.0)
  final double groupSpacing;

  /// Custom toolbar actions
  final List<Widget>? toolbarActions;

  /// Callback when bar is tapped
  final void Function(int categoryIndex, int seriesIndex, double value)? onBarTap;

  /// Constructor requiring categories and series
  const BarChartWidget({
    super.key,
    required this.title,
    this.subtitle,
    required this.categories,
    required this.series,
    this.height = 300,
    this.width,
    this.orientation = BarChartOrientation.vertical,
    this.style = BarChartStyle.grouped,
    this.showLegend = true,
    this.showValues = false,
    this.yRange,
    this.yAxisFormatter,
    this.showGrid = true,
    this.barWidth = 0.8,
    this.groupSpacing = 0.2,
    this.toolbarActions,
    this.onBarTap,
  });

  @override
  State<BarChartWidget> createState() => _BarChartWidgetState();
}

class _BarChartWidgetState extends State<BarChartWidget> {
  /// Currently enabled series
  final Set<String> _enabledSeries = <String>{};

  @override
  void initState() {
    super.initState();
    _initializeChart();
  }

  @override
  void didUpdateWidget(BarChartWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.series != oldWidget.series) {
      _initializeChart();
    }
  }

  /// Initializes chart data
  void _initializeChart() {
    // Initialize enabled series
    _enabledSeries.clear();
    for (final series in widget.series) {
      if (series.isEnabled) {
        _enabledSeries.add(series.name);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final hasData = widget.series.any((series) =>
        _enabledSeries.contains(series.name) && series.values.any((v) => v != 0));

    return BaseChartWidget(
      configuration: ChartConfiguration(
        title: widget.title,
        subtitle: widget.subtitle,
        height: widget.height,
        width: widget.width,
        showLegend: widget.showLegend,
        showToolbar: true,
      ),
      hasData: hasData,
      noDataMessage: 'No categorical data available to display',
      toolbarActions: widget.toolbarActions,
      legend: widget.showLegend ? _buildLegend() : null,
      child: _buildChart(),
    );
  }

  /// Builds the main bar chart
  Widget _buildChart() {
    final enabledSeries = widget.series
        .where((series) => _enabledSeries.contains(series.name))
        .toList();

    if (enabledSeries.isEmpty) {
      return const SizedBox.shrink();
    }

    return widget.orientation == BarChartOrientation.vertical
        ? _buildVerticalChart(enabledSeries)
        : _buildHorizontalChart(enabledSeries);
  }

  /// Builds vertical bar chart
  Widget _buildVerticalChart(List<BarSeries> enabledSeries) {
    // Calculate Y-axis range
    final (minY, maxY) = widget.yRange ?? _calculateYRange(enabledSeries);

    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: maxY,
        minY: minY,
        gridData: widget.showGrid
            ? ChartUtils.createGridData(context, showVertical: false)
            : FlGridData(show: false),
        titlesData: _buildVerticalTitlesData(),
        borderData: ChartUtils.createBorderData(context),
        barGroups: _buildBarGroups(enabledSeries),
        barTouchData: _buildBarTouchData(enabledSeries),
      ),
    );
  }

  /// Builds horizontal bar chart
  Widget _buildHorizontalChart(List<BarSeries> enabledSeries) {
    // For horizontal charts, we need to transpose the data
    // This is a simplified implementation
    return _buildVerticalChart(enabledSeries);
  }

  /// Builds titles data for vertical chart
  FlTitlesData _buildVerticalTitlesData() {
    return FlTitlesData(
      show: true,
      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      leftTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          getTitlesWidget: (value, meta) {
            final formatted = widget.yAxisFormatter?.call(value) ??
                ChartUtils.formatValue(value);
            return Text(
              formatted,
              style: Theme.of(context).textTheme.bodySmall,
            );
          },
          reservedSize: 50,
        ),
      ),
      bottomTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          getTitlesWidget: (value, meta) {
            final index = value.toInt();
            if (index >= 0 && index < widget.categories.length) {
              return Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  widget.categories[index],
                  style: Theme.of(context).textTheme.bodySmall,
                  textAlign: TextAlign.center,
                ),
              );
            }
            return const Text('');
          },
          reservedSize: 40,
        ),
      ),
    );
  }

  /// Builds bar groups based on chart style
  List<BarChartGroupData> _buildBarGroups(List<BarSeries> enabledSeries) {
    switch (widget.style) {
      case BarChartStyle.grouped:
        return _buildGroupedBars(enabledSeries);
      case BarChartStyle.stacked:
        return _buildStackedBars(enabledSeries);
      case BarChartStyle.percentage:
        return _buildPercentageBars(enabledSeries);
    }
  }

  /// Builds grouped bars
  List<BarChartGroupData> _buildGroupedBars(List<BarSeries> enabledSeries) {
    final barGroups = <BarChartGroupData>[];

    for (int categoryIndex = 0; categoryIndex < widget.categories.length; categoryIndex++) {
      final barRods = <BarChartRodData>[];

      for (int seriesIndex = 0; seriesIndex < enabledSeries.length; seriesIndex++) {
        final series = enabledSeries[seriesIndex];
        final value = categoryIndex < series.values.length
            ? series.values[categoryIndex]
            : 0.0;

        barRods.add(
          BarChartRodData(
            toY: value,
            color: series.color.withValues(alpha: series.opacity),
            width: _calculateBarWidth(enabledSeries.length),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(2)),
          ),
        );
      }

      barGroups.add(
        BarChartGroupData(
          x: categoryIndex,
          barRods: barRods,
          barsSpace: 4,
        ),
      );
    }

    return barGroups;
  }

  /// Builds stacked bars
  List<BarChartGroupData> _buildStackedBars(List<BarSeries> enabledSeries) {
    final barGroups = <BarChartGroupData>[];

    for (int categoryIndex = 0; categoryIndex < widget.categories.length; categoryIndex++) {
      double stackedValue = 0;
      final barRods = <BarChartRodData>[];

      for (int seriesIndex = 0; seriesIndex < enabledSeries.length; seriesIndex++) {
        final series = enabledSeries[seriesIndex];
        final value = categoryIndex < series.values.length
            ? series.values[categoryIndex]
            : 0.0;

        barRods.add(
          BarChartRodData(
            fromY: stackedValue,
            toY: stackedValue + value,
            color: series.color.withValues(alpha: series.opacity),
            width: _calculateBarWidth(1),
            borderRadius: seriesIndex == enabledSeries.length - 1
                ? const BorderRadius.vertical(top: Radius.circular(2))
                : BorderRadius.zero,
          ),
        );

        stackedValue += value;
      }

      barGroups.add(
        BarChartGroupData(
          x: categoryIndex,
          barRods: barRods,
        ),
      );
    }

    return barGroups;
  }

  /// Builds percentage bars (stacked to 100%)
  List<BarChartGroupData> _buildPercentageBars(List<BarSeries> enabledSeries) {
    final barGroups = <BarChartGroupData>[];

    for (int categoryIndex = 0; categoryIndex < widget.categories.length; categoryIndex++) {
      // Calculate total for this category
      double total = 0;
      for (final series in enabledSeries) {
        if (categoryIndex < series.values.length) {
          total += series.values[categoryIndex];
        }
      }

      if (total == 0) {
        barGroups.add(
          BarChartGroupData(
            x: categoryIndex,
            barRods: [
              BarChartRodData(
                toY: 0,
                color: Colors.grey.withValues(alpha: 0.3),
                width: _calculateBarWidth(1),
              ),
            ],
          ),
        );
        continue;
      }

      double stackedPercentage = 0;
      final barRods = <BarChartRodData>[];

      for (int seriesIndex = 0; seriesIndex < enabledSeries.length; seriesIndex++) {
        final series = enabledSeries[seriesIndex];
        final value = categoryIndex < series.values.length
            ? series.values[categoryIndex]
            : 0.0;
        final percentage = (value / total) * 100;

        barRods.add(
          BarChartRodData(
            fromY: stackedPercentage,
            toY: stackedPercentage + percentage,
            color: series.color.withValues(alpha: series.opacity),
            width: _calculateBarWidth(1),
            borderRadius: seriesIndex == enabledSeries.length - 1
                ? const BorderRadius.vertical(top: Radius.circular(2))
                : BorderRadius.zero,
          ),
        );

        stackedPercentage += percentage;
      }

      barGroups.add(
        BarChartGroupData(
          x: categoryIndex,
          barRods: barRods,
        ),
      );
    }

    return barGroups;
  }

  /// Calculates bar width based on number of series
  double _calculateBarWidth(int seriesCount) {
    final baseWidth = 20.0;
    if (widget.style == BarChartStyle.grouped) {
      return baseWidth / seriesCount;
    }
    return baseWidth;
  }

  /// Builds touch data configuration
  BarTouchData _buildBarTouchData(List<BarSeries> enabledSeries) {
    return BarTouchData(
      touchTooltipData: BarTouchTooltipData(
        getTooltipItem: (group, groupIndex, rod, rodIndex) {
          final categoryIndex = group.x.toInt();
          if (categoryIndex < widget.categories.length) {
            final category = widget.categories[categoryIndex];

            String tooltip = category;

            if (widget.style == BarChartStyle.grouped && rodIndex < enabledSeries.length) {
              final series = enabledSeries[rodIndex];
              final value = rod.toY;
              final formattedValue = widget.yAxisFormatter?.call(value) ??
                  ChartUtils.formatValue(value);

              tooltip += '\n${series.name}: $formattedValue';
            } else if (widget.style == BarChartStyle.stacked ||
                       widget.style == BarChartStyle.percentage) {
              final value = rod.toY - rod.fromY;
              final formattedValue = widget.style == BarChartStyle.percentage
                  ? ChartUtils.formatValue(value, isPercentage: false, unit: '%')
                  : widget.yAxisFormatter?.call(value) ?? ChartUtils.formatValue(value);

              if (rodIndex < enabledSeries.length) {
                final series = enabledSeries[rodIndex];
                tooltip += '\n${series.name}: $formattedValue';
              }
            }

            return BarTooltipItem(
              tooltip,
              TextStyle(
                color: Theme.of(context).colorScheme.onSurface,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            );
          }

          return null;
        },
      ),
      touchCallback: (event, barTouchResponse) {
        if (widget.onBarTap != null &&
            event is FlTapUpEvent &&
            barTouchResponse?.spot != null) {
          final spot = barTouchResponse!.spot!;
          final categoryIndex = spot.touchedBarGroup.x.toInt();
          final seriesIndex = spot.touchedRodDataIndex;
          final value = spot.touchedRodData.toY;

          widget.onBarTap!(categoryIndex, seriesIndex, value);
        }
      },
    );
  }

  /// Calculates Y-axis range from data
  (double, double) _calculateYRange(List<BarSeries> enabledSeries) {
    final allValues = <double>[];

    switch (widget.style) {
      case BarChartStyle.grouped:
        for (final series in enabledSeries) {
          allValues.addAll(series.values);
        }
        break;
      case BarChartStyle.stacked:
        for (int i = 0; i < widget.categories.length; i++) {
          double stackedValue = 0;
          for (final series in enabledSeries) {
            if (i < series.values.length) {
              stackedValue += series.values[i];
            }
          }
          allValues.add(stackedValue);
        }
        break;
      case BarChartStyle.percentage:
        return (0, 100);
    }

    if (allValues.isEmpty) return (0, 1);

    return ChartUtils.calculateYRange(allValues);
  }

  /// Builds legend widget
  Widget _buildLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: widget.series.map((series) {
        final isEnabled = _enabledSeries.contains(series.name);

        return InkWell(
          onTap: () {
            setState(() {
              if (isEnabled) {
                _enabledSeries.remove(series.name);
              } else {
                _enabledSeries.add(series.name);
              }
            });
          },
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: isEnabled
                      ? series.color
                      : series.color.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 6),
              Text(
                series.name,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: isEnabled
                      ? null
                      : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}