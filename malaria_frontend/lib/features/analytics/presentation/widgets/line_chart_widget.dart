/// Line chart widget for time series data visualization using fl_chart
///
/// This widget displays time series data including environmental trends,
/// prediction accuracy over time, and other temporal analytics data.
/// It supports multiple series, interactive tooltips, and responsive design.
///
/// Usage:
/// ```dart
/// LineChartWidget(
///   title: 'Temperature Trends',
///   series: [
///     TimeSeriesData(
///       name: 'Daily Temperature',
///       data: temperaturePoints,
///       color: Colors.red,
///     ),
///   ],
///   height: 400,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';
import 'base_chart_widget.dart';

/// Data point for time series visualization
class TimeSeriesDataPoint {
  /// Date/time of the data point
  final DateTime date;

  /// Value at this point in time
  final double value;

  /// Optional quality score (0.0 to 1.0)
  final double? quality;

  /// Optional metadata for this point
  final Map<String, dynamic>? metadata;

  const TimeSeriesDataPoint({
    required this.date,
    required this.value,
    this.quality,
    this.metadata,
  });

  /// Creates data point from environmental trend
  factory TimeSeriesDataPoint.fromEnvironmentalTrend(EnvironmentalTrend trend) {
    return TimeSeriesDataPoint(
      date: trend.date,
      value: trend.value,
      quality: trend.quality,
      metadata: {
        'factor': trend.factor,
        'coordinates': trend.coordinates,
      },
    );
  }

  /// Creates data point from accuracy data
  factory TimeSeriesDataPoint.fromAccuracyData(AccuracyDataPoint accuracy) {
    return TimeSeriesDataPoint(
      date: accuracy.date,
      value: accuracy.accuracy,
      metadata: {
        'sampleSize': accuracy.sampleSize,
      },
    );
  }

  /// Creates data point from risk trend
  factory TimeSeriesDataPoint.fromRiskTrend(RiskTrend risk) {
    return TimeSeriesDataPoint(
      date: risk.date,
      value: risk.riskScore,
      quality: risk.confidence,
      metadata: {
        'riskLevel': risk.riskLevel,
        'populationAtRisk': risk.populationAtRisk,
        'coordinates': risk.coordinates,
      },
    );
  }
}

/// Time series data configuration for a single line
class TimeSeriesData {
  /// Display name for this series
  final String name;

  /// Data points for this series
  final List<TimeSeriesDataPoint> data;

  /// Color for this series line
  final Color color;

  /// Line width
  final double lineWidth;

  /// Whether to show dots at data points
  final bool showDots;

  /// Whether to show area under the curve
  final bool showArea;

  /// Whether this series is enabled/visible
  final bool isEnabled;

  /// Custom line style
  final LineStyle? lineStyle;

  const TimeSeriesData({
    required this.name,
    required this.data,
    required this.color,
    this.lineWidth = 2.0,
    this.showDots = true,
    this.showArea = false,
    this.isEnabled = true,
    this.lineStyle,
  });

  /// Creates a copy with updated properties
  TimeSeriesData copyWith({
    String? name,
    List<TimeSeriesDataPoint>? data,
    Color? color,
    double? lineWidth,
    bool? showDots,
    bool? showArea,
    bool? isEnabled,
    LineStyle? lineStyle,
  }) {
    return TimeSeriesData(
      name: name ?? this.name,
      data: data ?? this.data,
      color: color ?? this.color,
      lineWidth: lineWidth ?? this.lineWidth,
      showDots: showDots ?? this.showDots,
      showArea: showArea ?? this.showArea,
      isEnabled: isEnabled ?? this.isEnabled,
      lineStyle: lineStyle ?? this.lineStyle,
    );
  }
}

/// Line style configuration
enum LineStyle {
  solid,
  dashed,
  dotted,
}

/// Line chart widget for time series data
class LineChartWidget extends StatefulWidget {
  /// Chart title
  final String title;

  /// Chart subtitle
  final String? subtitle;

  /// Time series data to display
  final List<TimeSeriesData> series;

  /// Chart height
  final double height;

  /// Chart width (null for responsive)
  final double? width;

  /// Whether to show legend
  final bool showLegend;

  /// Whether to enable zoom and pan
  final bool enableInteraction;

  /// Date range to display (null for auto)
  final DateRange? dateRange;

  /// Y-axis range (null for auto)
  final (double min, double max)? yRange;

  /// Number format for Y-axis labels
  final String Function(double)? yAxisFormatter;

  /// Date format for X-axis labels
  final String Function(DateTime)? xAxisFormatter;

  /// Whether to show quality indicators
  final bool showQuality;

  /// Custom toolbar actions
  final List<Widget>? toolbarActions;

  /// Callback when data point is tapped
  final void Function(TimeSeriesDataPoint, TimeSeriesData)? onDataPointTap;

  /// Constructor requiring series data
  const LineChartWidget({
    super.key,
    required this.title,
    this.subtitle,
    required this.series,
    this.height = 300,
    this.width,
    this.showLegend = true,
    this.enableInteraction = true,
    this.dateRange,
    this.yRange,
    this.yAxisFormatter,
    this.xAxisFormatter,
    this.showQuality = false,
    this.toolbarActions,
    this.onDataPointTap,
  });

  @override
  State<LineChartWidget> createState() => _LineChartWidgetState();
}

class _LineChartWidgetState extends State<LineChartWidget> {
  /// Currently enabled series
  final Set<String> _enabledSeries = <String>{};

  /// Date range for chart display
  late DateRange _displayRange;

  /// All unique dates from all series
  late List<DateTime> _allDates;

  @override
  void initState() {
    super.initState();
    _initializeChart();
  }

  @override
  void didUpdateWidget(LineChartWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.series != oldWidget.series) {
      _initializeChart();
    }
  }

  /// Initializes chart data and configuration
  void _initializeChart() {
    // Initialize enabled series
    _enabledSeries.clear();
    for (final series in widget.series) {
      if (series.isEnabled) {
        _enabledSeries.add(series.name);
      }
    }

    // Calculate date range
    _calculateDateRange();
  }

  /// Calculates the date range for the chart
  void _calculateDateRange() {
    if (widget.dateRange != null) {
      _displayRange = widget.dateRange!;
    } else {
      // Calculate from data
      final allDates = <DateTime>[];
      for (final series in widget.series) {
        if (_enabledSeries.contains(series.name)) {
          allDates.addAll(series.data.map((point) => point.date));
        }
      }

      if (allDates.isNotEmpty) {
        allDates.sort();
        _displayRange = DateRange(
          start: allDates.first,
          end: allDates.last,
        );
      } else {
        final now = DateTime.now();
        _displayRange = DateRange(
          start: now.subtract(const Duration(days: 30)),
          end: now,
        );
      }
    }

    // Generate all dates for X-axis
    _allDates = _generateDateRange(_displayRange);
  }

  /// Generates list of dates for X-axis
  List<DateTime> _generateDateRange(DateRange range) {
    final dates = <DateTime>[];
    final duration = range.duration;
    final daysBetween = duration.inDays;

    if (daysBetween <= 31) {
      // Daily intervals for up to 31 days
      for (int i = 0; i <= daysBetween; i++) {
        dates.add(range.start.add(Duration(days: i)));
      }
    } else if (daysBetween <= 365) {
      // Weekly intervals for up to 1 year
      DateTime current = range.start;
      while (current.isBefore(range.end) || current.isAtSameMomentAs(range.end)) {
        dates.add(current);
        current = current.add(const Duration(days: 7));
      }
    } else {
      // Monthly intervals for more than 1 year
      DateTime current = DateTime(range.start.year, range.start.month, 1);
      while (current.isBefore(range.end) || current.isAtSameMomentAs(range.end)) {
        dates.add(current);
        current = DateTime(current.year, current.month + 1, 1);
      }
    }

    return dates;
  }

  @override
  Widget build(BuildContext context) {
    final hasData = widget.series.any((series) =>
        _enabledSeries.contains(series.name) && series.data.isNotEmpty);

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
      noDataMessage: 'No time series data available for the selected period',
      toolbarActions: widget.toolbarActions,
      legend: widget.showLegend ? _buildLegend() : null,
      child: _buildChart(),
    );
  }

  /// Builds the main line chart
  Widget _buildChart() {
    final enabledSeriesData = widget.series
        .where((series) => _enabledSeries.contains(series.name))
        .toList();

    if (enabledSeriesData.isEmpty) {
      return const SizedBox.shrink();
    }

    // Calculate Y-axis range
    final (minY, maxY) = widget.yRange ?? _calculateYRange(enabledSeriesData);

    return LineChart(
      LineChartData(
        gridData: ChartUtils.createGridData(context),
        titlesData: _buildTitlesData(),
        borderData: ChartUtils.createBorderData(context),
        minX: 0,
        maxX: (_allDates.length - 1).toDouble(),
        minY: minY,
        maxY: maxY,
        lineBarsData: _buildLineBarsData(enabledSeriesData),
        lineTouchData: _buildTouchData(enabledSeriesData),
        clipData: const FlClipData.all(),
      ),
    );
  }

  /// Builds titles configuration for axes
  FlTitlesData _buildTitlesData() {
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
            if (index >= 0 && index < _allDates.length) {
              final date = _allDates[index];
              final formatted = widget.xAxisFormatter?.call(date) ??
                  ChartUtils.formatDate(date);
              return Text(
                formatted,
                style: Theme.of(context).textTheme.bodySmall,
              );
            }
            return const Text('');
          },
          reservedSize: 35,
        ),
      ),
    );
  }

  /// Builds line bars data for each enabled series
  List<LineChartBarData> _buildLineBarsData(List<TimeSeriesData> enabledSeries) {
    return enabledSeries.map((series) {
      final spots = _createSpotsForSeries(series);

      return LineChartBarData(
        spots: spots,
        isCurved: true,
        color: series.color,
        barWidth: series.lineWidth,
        isStrokeCapRound: true,
        dotData: FlDotData(
          show: series.showDots,
          getDotPainter: (spot, percent, barData, index) {
            return FlDotCirclePainter(
              radius: 3,
              color: series.color,
              strokeWidth: 1,
              strokeColor: Theme.of(context).colorScheme.surface,
            );
          },
        ),
        belowBarData: series.showArea
            ? BarAreaData(
                show: true,
                gradient: ChartUtils.createGradient(series.color),
              )
            : BarAreaData(show: false),
        dashArray: _getDashArray(series.lineStyle),
      );
    }).toList();
  }

  /// Creates FL spots for a time series
  List<FlSpot> _createSpotsForSeries(TimeSeriesData series) {
    final spots = <FlSpot>[];

    for (final dataPoint in series.data) {
      // Find the index of this date in our all dates list
      final dateIndex = _findDateIndex(dataPoint.date);
      if (dateIndex != -1) {
        spots.add(FlSpot(dateIndex.toDouble(), dataPoint.value));
      }
    }

    return spots;
  }

  /// Finds the index of a date in the all dates list
  int _findDateIndex(DateTime targetDate) {
    for (int i = 0; i < _allDates.length; i++) {
      final date = _allDates[i];
      // Compare dates ignoring time for daily data
      if (date.year == targetDate.year &&
          date.month == targetDate.month &&
          date.day == targetDate.day) {
        return i;
      }
    }
    return -1;
  }

  /// Gets dash array for line style
  List<int>? _getDashArray(LineStyle? style) {
    switch (style) {
      case LineStyle.dashed:
        return [8, 4];
      case LineStyle.dotted:
        return [2, 4];
      case LineStyle.solid:
      case null:
        return null;
    }
  }

  /// Builds touch data configuration
  LineTouchData _buildTouchData(List<TimeSeriesData> enabledSeries) {
    return LineTouchData(
      touchTooltipData: LineTouchTooltipData(
        getTooltipItems: (touchedSpots) {
          return touchedSpots.map((spot) {
            final seriesIndex = spot.barIndex;
            if (seriesIndex < enabledSeries.length) {
              final series = enabledSeries[seriesIndex];
              final dateIndex = spot.x.toInt();

              if (dateIndex < _allDates.length) {
                final date = _allDates[dateIndex];
                final dataPoint = _findDataPointForDate(series, date);

                return LineTooltipItem(
                  _buildTooltipText(series, dataPoint, date, spot.y),
                  TextStyle(
                    color: series.color,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                );
              }
            }
            return null;
          }).toList();
        },
      ),
      touchCallback: (event, touchResponse) {
        if (widget.onDataPointTap != null &&
            event is FlTapUpEvent &&
            touchResponse?.lineBarSpots != null) {
          for (final spot in touchResponse!.lineBarSpots!) {
            final seriesIndex = spot.barIndex;
            if (seriesIndex < enabledSeries.length) {
              final series = enabledSeries[seriesIndex];
              final dateIndex = spot.x.toInt();

              if (dateIndex < _allDates.length) {
                final date = _allDates[dateIndex];
                final dataPoint = _findDataPointForDate(series, date);
                if (dataPoint != null) {
                  widget.onDataPointTap!(dataPoint, series);
                }
              }
            }
          }
        }
      },
    );
  }

  /// Finds data point for a specific date in a series
  TimeSeriesDataPoint? _findDataPointForDate(TimeSeriesData series, DateTime date) {
    for (final point in series.data) {
      if (point.date.year == date.year &&
          point.date.month == date.month &&
          point.date.day == date.day) {
        return point;
      }
    }
    return null;
  }

  /// Builds tooltip text for a data point
  String _buildTooltipText(
    TimeSeriesData series,
    TimeSeriesDataPoint? dataPoint,
    DateTime date,
    double value,
  ) {
    final dateStr = DateFormat('MMM d, y').format(date);
    final valueStr = widget.yAxisFormatter?.call(value) ??
        ChartUtils.formatValue(value);

    String tooltip = '${series.name}\n$dateStr\nValue: $valueStr';

    if (dataPoint != null) {
      if (widget.showQuality && dataPoint.quality != null) {
        tooltip += '\nQuality: ${(dataPoint.quality! * 100).toInt()}%';
      }

      if (dataPoint.metadata != null) {
        final metadata = dataPoint.metadata!;
        if (metadata.containsKey('sampleSize')) {
          tooltip += '\nSamples: ${metadata['sampleSize']}';
        }
        if (metadata.containsKey('populationAtRisk')) {
          tooltip += '\nAt Risk: ${metadata['populationAtRisk']}';
        }
      }
    }

    return tooltip;
  }

  /// Calculates Y-axis range from data
  (double, double) _calculateYRange(List<TimeSeriesData> enabledSeries) {
    final allValues = <double>[];

    for (final series in enabledSeries) {
      allValues.addAll(series.data.map((point) => point.value));
    }

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
                  color: isEnabled ? series.color : series.color.withValues(alpha: 0.3),
                  shape: BoxShape.circle,
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