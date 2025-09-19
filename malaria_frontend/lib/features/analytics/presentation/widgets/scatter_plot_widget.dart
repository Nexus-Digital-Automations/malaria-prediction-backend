/// Scatter plot widget for correlation analysis using fl_chart
///
/// This widget displays correlation between different variables such as
/// environmental factors vs malaria risk, temperature vs humidity, etc.
/// It supports multiple datasets, trend lines, and interactive analysis.
///
/// Usage:
/// ```dart
/// ScatterPlotWidget(
///   title: 'Temperature vs Malaria Risk',
///   xAxisLabel: 'Temperature (°C)',
///   yAxisLabel: 'Risk Score',
///   datasets: [
///     ScatterDataset(
///       name: 'Regional Data',
///       points: correlationPoints,
///       color: Colors.blue,
///     ),
///   ],
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';
import 'base_chart_widget.dart';

/// Data point for scatter plot visualization
class ScatterDataPoint {
  /// X-axis value
  final double x;

  /// Y-axis value
  final double y;

  /// Optional size of the point (for bubble charts)
  final double? size;

  /// Optional color override for this point
  final Color? color;

  /// Optional label for this point
  final String? label;

  /// Optional metadata for this point
  final Map<String, dynamic>? metadata;

  const ScatterDataPoint({
    required this.x,
    required this.y,
    this.size,
    this.color,
    this.label,
    this.metadata,
  });

  /// Creates scatter point from environmental correlation
  factory ScatterDataPoint.fromEnvironmentalCorrelation({
    required double environmentalValue,
    required double riskScore,
    required EnvironmentalFactor factor,
    DateTime? date,
    Coordinates? coordinates,
  }) {
    return ScatterDataPoint(
      x: environmentalValue,
      y: riskScore,
      metadata: {
        'factor': factor,
        'date': date,
        'coordinates': coordinates,
      },
    );
  }

  /// Creates scatter point from climate metrics
  factory ScatterDataPoint.fromClimateMetrics({
    required double xValue,
    required double yValue,
    required String xMetric,
    required String yMetric,
    String? region,
    int? year,
  }) {
    return ScatterDataPoint(
      x: xValue,
      y: yValue,
      metadata: {
        'xMetric': xMetric,
        'yMetric': yMetric,
        'region': region,
        'year': year,
      },
    );
  }

  /// Creates scatter point from prediction accuracy
  factory ScatterDataPoint.fromAccuracyComparison({
    required double predicted,
    required double actual,
    DateTime? date,
    int? sampleSize,
  }) {
    return ScatterDataPoint(
      x: predicted,
      y: actual,
      size: sampleSize?.toDouble(),
      metadata: {
        'date': date,
        'sampleSize': sampleSize,
      },
    );
  }
}

/// Dataset configuration for scatter plot
class ScatterDataset {
  /// Display name for this dataset
  final String name;

  /// Data points in this dataset
  final List<ScatterDataPoint> points;

  /// Color for this dataset
  final Color color;

  /// Point size (radius)
  final double pointSize;

  /// Point shape
  final ScatterPointShape shape;

  /// Whether to show trend line
  final bool showTrendLine;

  /// Trend line color (null for same as points)
  final Color? trendLineColor;

  /// Whether this dataset is enabled/visible
  final bool isEnabled;

  /// Opacity of points
  final double opacity;

  const ScatterDataset({
    required this.name,
    required this.points,
    required this.color,
    this.pointSize = 4.0,
    this.shape = ScatterPointShape.circle,
    this.showTrendLine = false,
    this.trendLineColor,
    this.isEnabled = true,
    this.opacity = 0.8,
  });

  /// Creates a copy with updated properties
  ScatterDataset copyWith({
    String? name,
    List<ScatterDataPoint>? points,
    Color? color,
    double? pointSize,
    ScatterPointShape? shape,
    bool? showTrendLine,
    Color? trendLineColor,
    bool? isEnabled,
    double? opacity,
  }) {
    return ScatterDataset(
      name: name ?? this.name,
      points: points ?? this.points,
      color: color ?? this.color,
      pointSize: pointSize ?? this.pointSize,
      shape: shape ?? this.shape,
      showTrendLine: showTrendLine ?? this.showTrendLine,
      trendLineColor: trendLineColor ?? this.trendLineColor,
      isEnabled: isEnabled ?? this.isEnabled,
      opacity: opacity ?? this.opacity,
    );
  }
}

/// Point shape options for scatter plot
enum ScatterPointShape {
  circle,
  square,
  triangle,
  diamond,
}

/// Correlation statistics for trend analysis
class CorrelationStats {
  /// Pearson correlation coefficient (-1 to 1)
  final double correlation;

  /// R-squared value (0 to 1)
  final double rSquared;

  /// Slope of the trend line
  final double slope;

  /// Y-intercept of the trend line
  final double intercept;

  /// Number of data points used
  final int sampleSize;

  /// P-value for statistical significance
  final double? pValue;

  const CorrelationStats({
    required this.correlation,
    required this.rSquared,
    required this.slope,
    required this.intercept,
    required this.sampleSize,
    this.pValue,
  });

  /// Gets correlation strength description
  String get strengthDescription {
    final abs = correlation.abs();
    if (abs >= 0.8) return 'Very Strong';
    if (abs >= 0.6) return 'Strong';
    if (abs >= 0.4) return 'Moderate';
    if (abs >= 0.2) return 'Weak';
    return 'Very Weak';
  }

  /// Gets correlation direction description
  String get directionDescription {
    if (correlation > 0) return 'Positive';
    if (correlation < 0) return 'Negative';
    return 'No';
  }
}

/// Scatter plot widget for correlation analysis
class ScatterPlotWidget extends StatefulWidget {
  /// Chart title
  final String title;

  /// Chart subtitle
  final String? subtitle;

  /// X-axis label
  final String xAxisLabel;

  /// Y-axis label
  final String yAxisLabel;

  /// Scatter datasets to display
  final List<ScatterDataset> datasets;

  /// Chart height
  final double height;

  /// Chart width (null for responsive)
  final double? width;

  /// Whether to show legend
  final bool showLegend;

  /// Whether to show correlation statistics
  final bool showStats;

  /// X-axis range (null for auto)
  final (double min, double max)? xRange;

  /// Y-axis range (null for auto)
  final (double min, double max)? yRange;

  /// Number format for X-axis labels
  final String Function(double)? xAxisFormatter;

  /// Number format for Y-axis labels
  final String Function(double)? yAxisFormatter;

  /// Whether to enable bubble mode (size from data)
  final bool bubbleMode;

  /// Whether to show grid lines
  final bool showGrid;

  /// Custom toolbar actions
  final List<Widget>? toolbarActions;

  /// Callback when data point is tapped
  final void Function(ScatterDataPoint, ScatterDataset)? onDataPointTap;

  /// Constructor requiring datasets
  const ScatterPlotWidget({
    super.key,
    required this.title,
    this.subtitle,
    required this.xAxisLabel,
    required this.yAxisLabel,
    required this.datasets,
    this.height = 300,
    this.width,
    this.showLegend = true,
    this.showStats = true,
    this.xRange,
    this.yRange,
    this.xAxisFormatter,
    this.yAxisFormatter,
    this.bubbleMode = false,
    this.showGrid = true,
    this.toolbarActions,
    this.onDataPointTap,
  });

  @override
  State<ScatterPlotWidget> createState() => _ScatterPlotWidgetState();
}

class _ScatterPlotWidgetState extends State<ScatterPlotWidget> {
  /// Currently enabled datasets
  final Set<String> _enabledDatasets = <String>{};

  /// Calculated correlation statistics for each dataset
  final Map<String, CorrelationStats> _correlationStats = {};

  @override
  void initState() {
    super.initState();
    _initializeChart();
  }

  @override
  void didUpdateWidget(ScatterPlotWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.datasets != oldWidget.datasets) {
      _initializeChart();
    }
  }

  /// Initializes chart data and calculations
  void _initializeChart() {
    // Initialize enabled datasets
    _enabledDatasets.clear();
    for (final dataset in widget.datasets) {
      if (dataset.isEnabled) {
        _enabledDatasets.add(dataset.name);
      }
    }

    // Calculate correlation statistics
    _calculateCorrelationStats();
  }

  /// Calculates correlation statistics for all datasets
  void _calculateCorrelationStats() {
    _correlationStats.clear();

    for (final dataset in widget.datasets) {
      if (_enabledDatasets.contains(dataset.name) && dataset.points.length >= 2) {
        final stats = _calculateCorrelation(dataset.points);
        _correlationStats[dataset.name] = stats;
      }
    }
  }

  /// Calculates correlation statistics for a dataset
  CorrelationStats _calculateCorrelation(List<ScatterDataPoint> points) {
    final n = points.length;
    if (n < 2) {
      return const CorrelationStats(
        correlation: 0,
        rSquared: 0,
        slope: 0,
        intercept: 0,
        sampleSize: 0,
      );
    }

    // Calculate means
    final xMean = points.map((p) => p.x).reduce((a, b) => a + b) / n;
    final yMean = points.map((p) => p.y).reduce((a, b) => a + b) / n;

    // Calculate correlation coefficient
    double numerator = 0;
    double xSquareSum = 0;
    double ySquareSum = 0;

    for (final point in points) {
      final xDiff = point.x - xMean;
      final yDiff = point.y - yMean;
      numerator += xDiff * yDiff;
      xSquareSum += xDiff * xDiff;
      ySquareSum += yDiff * yDiff;
    }

    final denominator = math.sqrt(xSquareSum * ySquareSum);
    final correlation = denominator == 0 ? 0 : numerator / denominator;

    // Calculate linear regression
    final slope = xSquareSum == 0 ? 0 : numerator / xSquareSum;
    final intercept = yMean - slope * xMean;

    // Calculate R-squared
    final rSquared = correlation * correlation;

    return CorrelationStats(
      correlation: correlation,
      rSquared: rSquared,
      slope: slope,
      intercept: intercept,
      sampleSize: n,
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasData = widget.datasets.any((dataset) =>
        _enabledDatasets.contains(dataset.name) && dataset.points.isNotEmpty);

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
      noDataMessage: 'No correlation data available for analysis',
      toolbarActions: widget.toolbarActions,
      legend: widget.showLegend ? _buildLegend() : null,
      child: Column(
        children: [
          Expanded(child: _buildChart()),
          if (widget.showStats && _correlationStats.isNotEmpty) ...[
            const SizedBox(height: 16),
            _buildStatsPanel(),
          ],
        ],
      ),
    );
  }

  /// Builds the main scatter plot chart
  Widget _buildChart() {
    final enabledDatasets = widget.datasets
        .where((dataset) => _enabledDatasets.contains(dataset.name))
        .toList();

    if (enabledDatasets.isEmpty) {
      return const SizedBox.shrink();
    }

    // Calculate axis ranges
    final (minX, maxX) = widget.xRange ?? _calculateXRange(enabledDatasets);
    final (minY, maxY) = widget.yRange ?? _calculateYRange(enabledDatasets);

    return Column(
      children: [
        // Y-axis label
        Text(
          widget.yAxisLabel,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: Row(
            children: [
              // Y-axis values space
              const SizedBox(width: 50),
              Expanded(
                child: ScatterChart(
                  ScatterChartData(
                    scatterSpots: _buildScatterSpots(enabledDatasets),
                    gridData: widget.showGrid
                        ? ChartUtils.createGridData(context)
                        : FlGridData(show: false),
                    titlesData: _buildTitlesData(minX, maxX, minY, maxY),
                    borderData: ChartUtils.createBorderData(context),
                    minX: minX,
                    maxX: maxX,
                    minY: minY,
                    maxY: maxY,
                    scatterTouchData: _buildTouchData(enabledDatasets),
                    clipData: const FlClipData.all(),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        // X-axis label
        Text(
          widget.xAxisLabel,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  /// Builds scatter spots for all enabled datasets
  List<ScatterSpot> _buildScatterSpots(List<ScatterDataset> enabledDatasets) {
    final spots = <ScatterSpot>[];

    for (int datasetIndex = 0; datasetIndex < enabledDatasets.length; datasetIndex++) {
      final dataset = enabledDatasets[datasetIndex];

      for (final point in dataset.points) {
        final size = widget.bubbleMode && point.size != null
            ? _normalizeBubbleSize(point.size!, enabledDatasets)
            : dataset.pointSize;

        spots.add(
          ScatterSpot(
            point.x,
            point.y,
            radius: size,
            color: point.color ?? dataset.color.withValues(alpha: dataset.opacity),
          ),
        );
      }
    }

    return spots;
  }

  /// Normalizes bubble size for bubble charts
  double _normalizeBubbleSize(double size, List<ScatterDataset> datasets) {
    // Find min and max sizes across all datasets
    final allSizes = <double>[];
    for (final dataset in datasets) {
      for (final point in dataset.points) {
        if (point.size != null) {
          allSizes.add(point.size!);
        }
      }
    }

    if (allSizes.isEmpty) return 4.0;

    final minSize = allSizes.reduce(math.min);
    final maxSize = allSizes.reduce(math.max);

    if (maxSize == minSize) return 4.0;

    // Normalize to range 2-12
    const minRadius = 2.0;
    const maxRadius = 12.0;
    return minRadius + (size - minSize) / (maxSize - minSize) * (maxRadius - minRadius);
  }

  /// Builds titles configuration for axes
  FlTitlesData _buildTitlesData(double minX, double maxX, double minY, double maxY) {
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
            final formatted = widget.xAxisFormatter?.call(value) ??
                ChartUtils.formatValue(value);
            return Text(
              formatted,
              style: Theme.of(context).textTheme.bodySmall,
            );
          },
          reservedSize: 30,
        ),
      ),
    );
  }

  /// Builds touch data configuration
  ScatterTouchData _buildTouchData(List<ScatterDataset> enabledDatasets) {
    return ScatterTouchData(
      touchTooltipData: ScatterTouchTooltipData(
        getTooltipItems: (ScatterSpot touchedSpot) {
          // Find which dataset and point this spot belongs to
          final (dataset, point) = _findDatasetAndPoint(touchedSpot, enabledDatasets);

          if (dataset != null && point != null) {
            return ScatterTooltipItem(
              _buildTooltipText(dataset, point, touchedSpot),
              textStyle: TextStyle(
                color: dataset.color,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            );
          }

          return ScatterTooltipItem(
            'X: ${ChartUtils.formatValue(touchedSpot.x)}\n'
            'Y: ${ChartUtils.formatValue(touchedSpot.y)}',
            textStyle: const TextStyle(
              color: Colors.white,
              fontSize: 12,
            ),
          );
        },
      ),
      touchCallback: (event, touchResponse) {
        if (widget.onDataPointTap != null &&
            event is FlTapUpEvent &&
            touchResponse?.touchedSpot != null) {
          final spot = touchResponse!.touchedSpot!;
          final (dataset, point) = _findDatasetAndPoint(spot, enabledDatasets);

          if (dataset != null && point != null) {
            widget.onDataPointTap!(point, dataset);
          }
        }
      },
    );
  }

  /// Finds dataset and point for a touched spot
  (ScatterDataset?, ScatterDataPoint?) _findDatasetAndPoint(
    ScatterSpot spot,
    List<ScatterDataset> datasets,
  ) {
    const tolerance = 0.001;

    for (final dataset in datasets) {
      for (final point in dataset.points) {
        if ((point.x - spot.x).abs() < tolerance &&
            (point.y - spot.y).abs() < tolerance) {
          return (dataset, point);
        }
      }
    }

    return (null, null);
  }

  /// Builds tooltip text for a data point
  String _buildTooltipText(
    ScatterDataset dataset,
    ScatterDataPoint point,
    ScatterSpot spot,
  ) {
    final xStr = widget.xAxisFormatter?.call(point.x) ??
        ChartUtils.formatValue(point.x);
    final yStr = widget.yAxisFormatter?.call(point.y) ??
        ChartUtils.formatValue(point.y);

    String tooltip = '${dataset.name}\n'
        '${widget.xAxisLabel}: $xStr\n'
        '${widget.yAxisLabel}: $yStr';

    if (point.label != null) {
      tooltip = '${point.label}\n$tooltip';
    }

    if (widget.bubbleMode && point.size != null) {
      tooltip += '\nSize: ${ChartUtils.formatValue(point.size!)}';
    }

    if (point.metadata != null) {
      final metadata = point.metadata!;
      if (metadata.containsKey('date')) {
        final date = metadata['date'] as DateTime?;
        if (date != null) {
          tooltip += '\nDate: ${ChartUtils.formatDate(date)}';
        }
      }
      if (metadata.containsKey('region')) {
        tooltip += '\nRegion: ${metadata['region']}';
      }
    }

    return tooltip;
  }

  /// Calculates X-axis range from data
  (double, double) _calculateXRange(List<ScatterDataset> datasets) {
    final allX = <double>[];
    for (final dataset in datasets) {
      allX.addAll(dataset.points.map((point) => point.x));
    }
    return ChartUtils.calculateYRange(allX);
  }

  /// Calculates Y-axis range from data
  (double, double) _calculateYRange(List<ScatterDataset> datasets) {
    final allY = <double>[];
    for (final dataset in datasets) {
      allY.addAll(dataset.points.map((point) => point.y));
    }
    return ChartUtils.calculateYRange(allY);
  }

  /// Builds legend widget
  Widget _buildLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: widget.datasets.map((dataset) {
        final isEnabled = _enabledDatasets.contains(dataset.name);

        return InkWell(
          onTap: () {
            setState(() {
              if (isEnabled) {
                _enabledDatasets.remove(dataset.name);
              } else {
                _enabledDatasets.add(dataset.name);
              }
              _calculateCorrelationStats();
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
                      ? dataset.color
                      : dataset.color.withValues(alpha: 0.3),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                dataset.name,
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

  /// Builds correlation statistics panel
  Widget _buildStatsPanel() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Correlation Analysis',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          ..._correlationStats.entries.map((entry) {
            final dataset = widget.datasets.firstWhere((d) => d.name == entry.key);
            final stats = entry.value;

            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: dataset.color,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${dataset.name}: r=${stats.correlation.toStringAsFixed(3)}, '
                      'R²=${stats.rSquared.toStringAsFixed(3)} '
                      '(${stats.strengthDescription} ${stats.directionDescription})',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ],
      ),
    );
  }
}