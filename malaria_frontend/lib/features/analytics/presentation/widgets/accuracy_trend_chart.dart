/// Accuracy trend chart widget using fl_chart LineChart
///
/// This widget displays prediction accuracy trends over time using line charts
/// to visualize model performance evolution and accuracy patterns.
///
/// Usage:
/// ```dart
/// AccuracyTrendChart(
///   accuracyTrend: predictionMetrics.accuracyTrend,
///   height: 300,
///   showConfidenceInterval: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/prediction_metrics.dart';

/// Accuracy trend chart widget for prediction performance visualization
class AccuracyTrendChart extends StatefulWidget {
  /// Accuracy trend data points to display
  final List<AccuracyTrendPoint> accuracyTrend;

  /// Chart height
  final double height;

  /// Whether to show confidence intervals
  final bool showConfidenceInterval;

  /// Whether to show data point markers
  final bool showMarkers;

  /// Whether to enable touch interactions
  final bool enableTouch;

  /// Custom color for the accuracy line
  final Color? lineColor;

  /// Custom color for confidence interval fill
  final Color? confidenceColor;

  /// Constructor with required accuracy trend data
  const AccuracyTrendChart({
    super.key,
    required this.accuracyTrend,
    this.height = 300,
    this.showConfidenceInterval = true,
    this.showMarkers = true,
    this.enableTouch = true,
    this.lineColor,
    this.confidenceColor,
  });

  @override
  State<AccuracyTrendChart> createState() => _AccuracyTrendChartState();
}

class _AccuracyTrendChartState extends State<AccuracyTrendChart> {
  /// Touched spot index for interaction feedback
  int _touchedIndex = -1;

  /// Date formatter for x-axis labels
  final DateFormat _dateFormatter = DateFormat('MMM dd');

  /// Time formatter for detailed tooltips
  final DateFormat _timeFormatter = DateFormat('MMM dd, yyyy HH:mm');

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Container(
        height: widget.height,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(theme),
            const SizedBox(height: 16),
            Expanded(
              child: widget.accuracyTrend.isEmpty
                  ? _buildNoDataMessage(theme)
                  : _buildChart(colorScheme),
            ),
            const SizedBox(height: 8),
            _buildLegend(theme),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header with title and statistics
  Widget _buildHeader(ThemeData theme) {
    final currentAccuracy = widget.accuracyTrend.isNotEmpty
        ? widget.accuracyTrend.last.accuracy
        : 0.0;

    final averageAccuracy = widget.accuracyTrend.isNotEmpty
        ? widget.accuracyTrend.map((p) => p.accuracy).reduce((a, b) => a + b) / widget.accuracyTrend.length
        : 0.0;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Prediction Accuracy Trend',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '${widget.accuracyTrend.length} data points',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          ],
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            _buildStatChip(
              'Current',
              '${(currentAccuracy * 100).toStringAsFixed(1)}%',
              theme,
            ),
            const SizedBox(height: 4),
            _buildStatChip(
              'Average',
              '${(averageAccuracy * 100).toStringAsFixed(1)}%',
              theme,
            ),
          ],
        ),
      ],
    );
  }

  /// Builds a statistics chip widget
  Widget _buildStatChip(String label, String value, ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$label: ',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSecondaryContainer.withValues(alpha: 0.7),
            ),
          ),
          Text(
            value,
            style: theme.textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onSecondaryContainer,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the line chart with accuracy data
  Widget _buildChart(ColorScheme colorScheme) {
    if (widget.accuracyTrend.isEmpty) {
      return _buildNoDataMessage(Theme.of(context));
    }

    // Convert accuracy trend points to fl_chart data
    final spots = _convertToSpots();
    final confidenceSpots = widget.showConfidenceInterval ? _convertToConfidenceSpots() : null;

    // Determine chart bounds
    final accuracyValues = widget.accuracyTrend.map((p) => p.accuracy).toList();
    final minAccuracy = accuracyValues.reduce((a, b) => a < b ? a : b);
    final maxAccuracy = accuracyValues.reduce((a, b) => a > b ? a : b);

    // Add padding to y-axis bounds
    final yPadding = (maxAccuracy - minAccuracy) * 0.1;
    final minY = (minAccuracy - yPadding).clamp(0.0, 1.0);
    final maxY = (maxAccuracy + yPadding).clamp(0.0, 1.0);

    return LineChart(
      LineChartData(
        lineTouchData: widget.enableTouch ? _buildTouchData(colorScheme) : LineTouchData(enabled: false),
        gridData: _buildGridData(colorScheme),
        titlesData: _buildTitlesData(colorScheme),
        borderData: FlBorderData(show: false),
        minX: 0,
        maxX: (widget.accuracyTrend.length - 1).toDouble(),
        minY: minY,
        maxY: maxY,
        lineBarsData: [
          // Confidence interval fill (if enabled)
          if (widget.showConfidenceInterval && confidenceSpots != null)
            _buildConfidenceLineBar(confidenceSpots, colorScheme),
          // Main accuracy line
          _buildAccuracyLineBar(spots, colorScheme),
        ],
      ),
    );
  }

  /// Builds touch interaction data
  LineTouchData _buildTouchData(ColorScheme colorScheme) {
    return LineTouchData(
      touchCallback: (FlTouchEvent event, LineTouchResponse? touchResponse) {
        setState(() {
          if (touchResponse == null || touchResponse.lineBarSpots == null) {
            _touchedIndex = -1;
            return;
          }
          _touchedIndex = touchResponse.lineBarSpots!.first.spotIndex;
        });
      },
      touchTooltipData: LineTouchTooltipData(
        getTooltipColor: (_) => colorScheme.inverseSurface,
        tooltipRoundedRadius: 8,
        getTooltipItems: _buildTooltipItems,
      ),
      getTouchedSpotIndicator: (LineChartBarData barData, List<int> spotIndexes) {
        return spotIndexes.map((index) {
          return TouchedSpotIndicatorData(
            FlLine(
              color: colorScheme.primary,
              strokeWidth: 2,
              dashArray: [5, 5],
            ),
            FlDotData(
              getDotPainter: (spot, percent, barData, index) {
                return FlDotCirclePainter(
                  radius: 6,
                  color: colorScheme.primary,
                  strokeWidth: 2,
                  strokeColor: colorScheme.surface,
                );
              },
            ),
          );
        }).toList();
      },
    );
  }

  /// Builds tooltip items for touch interaction
  List<LineTooltipItem> _buildTooltipItems(List<LineBarSpot> touchedSpots) {
    return touchedSpots.map((LineBarSpot touchedSpot) {
      final index = touchedSpot.spotIndex;
      if (index >= 0 && index < widget.accuracyTrend.length) {
        final point = widget.accuracyTrend[index];
        return LineTooltipItem(
          '${_timeFormatter.format(point.timestamp)}\n'
          'Accuracy: ${(point.accuracy * 100).toStringAsFixed(1)}%\n'
          'Sample Size: ${point.sampleSize}',
          TextStyle(
            color: Theme.of(context).colorScheme.onInverseSurface,
            fontWeight: FontWeight.w500,
            fontSize: 12,
          ),
        );
      }
      return LineTooltipItem('', const TextStyle());
    }).toList();
  }

  /// Builds grid data configuration
  FlGridData _buildGridData(ColorScheme colorScheme) {
    return FlGridData(
      show: true,
      drawHorizontalLine: true,
      drawVerticalLine: true,
      horizontalInterval: 0.1,
      getDrawingHorizontalLine: (value) {
        return FlLine(
          color: colorScheme.outline.withValues(alpha: 0.2),
          strokeWidth: 1,
        );
      },
      getDrawingVerticalLine: (value) {
        return FlLine(
          color: colorScheme.outline.withValues(alpha: 0.1),
          strokeWidth: 1,
        );
      },
    );
  }

  /// Builds titles data for axes
  FlTitlesData _buildTitlesData(ColorScheme colorScheme) {
    return FlTitlesData(
      leftTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 50,
          interval: 0.1,
          getTitlesWidget: (value, meta) {
            return Text(
              '${(value * 100).toInt()}%',
              style: TextStyle(
                color: colorScheme.onSurface.withValues(alpha: 0.6),
                fontSize: 11,
              ),
            );
          },
        ),
        axisNameWidget: Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Text(
            'Accuracy',
            style: TextStyle(
              color: colorScheme.onSurface.withValues(alpha: 0.8),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ),
      bottomTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 30,
          interval: (widget.accuracyTrend.length / 5).clamp(1, 10).toDouble(),
          getTitlesWidget: (value, meta) {
            final index = value.toInt();
            if (index >= 0 && index < widget.accuracyTrend.length) {
              return Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  _dateFormatter.format(widget.accuracyTrend[index].timestamp),
                  style: TextStyle(
                    color: colorScheme.onSurface.withValues(alpha: 0.6),
                    fontSize: 10,
                  ),
                ),
              );
            }
            return const SizedBox.shrink();
          },
        ),
      ),
      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
    );
  }

  /// Builds the main accuracy line bar
  LineChartBarData _buildAccuracyLineBar(List<FlSpot> spots, ColorScheme colorScheme) {
    final lineColor = widget.lineColor ?? colorScheme.primary;

    return LineChartBarData(
      spots: spots,
      color: lineColor,
      barWidth: 3,
      isStrokeCapRound: true,
      dotData: FlDotData(
        show: widget.showMarkers,
        getDotPainter: (spot, percent, barData, index) {
          final isHighlighted = index == _touchedIndex;
          return FlDotCirclePainter(
            radius: isHighlighted ? 6 : 4,
            color: lineColor,
            strokeWidth: isHighlighted ? 2 : 1,
            strokeColor: colorScheme.surface,
          );
        },
      ),
      belowBarData: BarAreaData(
        show: false,
      ),
    );
  }

  /// Builds confidence interval line bar (filled area)
  LineChartBarData _buildConfidenceLineBar(
    List<FlSpot> confidenceSpots,
    ColorScheme colorScheme,
  ) {
    final confidenceColor = widget.confidenceColor ??
        colorScheme.primary.withValues(alpha: 0.2);

    return LineChartBarData(
      spots: confidenceSpots,
      color: Colors.transparent,
      barWidth: 0,
      dotData: const FlDotData(show: false),
      belowBarData: BarAreaData(
        show: true,
        gradient: LinearGradient(
          colors: [
            confidenceColor,
            confidenceColor.withValues(alpha: 0.1),
          ],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
    );
  }

  /// Converts accuracy trend points to FlSpot objects
  List<FlSpot> _convertToSpots() {
    return widget.accuracyTrend.asMap().entries.map((entry) {
      return FlSpot(entry.key.toDouble(), entry.value.accuracy);
    }).toList();
  }

  /// Converts to confidence interval spots (upper bounds)
  List<FlSpot>? _convertToConfidenceSpots() {
    if (!widget.showConfidenceInterval) return null;

    return widget.accuracyTrend.asMap().entries.map((entry) {
      return FlSpot(entry.key.toDouble(), entry.value.confidenceInterval.upperBound);
    }).toList();
  }

  /// Builds legend for the chart
  Widget _buildLegend(ThemeData theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildLegendItem(
          'Accuracy',
          widget.lineColor ?? theme.colorScheme.primary,
          theme,
        ),
        if (widget.showConfidenceInterval) ...[
          const SizedBox(width: 16),
          _buildLegendItem(
            'Confidence Interval',
            widget.confidenceColor ?? theme.colorScheme.primary.withValues(alpha: 0.3),
            theme,
          ),
        ],
      ],
    );
  }

  /// Builds individual legend item
  Widget _buildLegendItem(String label, Color color, ThemeData theme) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: theme.textTheme.bodySmall,
        ),
      ],
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.trending_up_outlined,
            size: 48,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No accuracy trend data available',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Accuracy trends will appear as prediction data becomes available',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}