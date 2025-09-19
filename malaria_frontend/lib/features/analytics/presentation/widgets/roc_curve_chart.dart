/// ROC (Receiver Operating Characteristic) curve chart widget
///
/// This widget displays ROC curves using fl_chart LineChart with custom styling
/// to visualize binary classification performance and threshold analysis.
///
/// Usage:
/// ```dart
/// ROCCurveChart(
///   rocData: predictionMetrics.rocCurveData,
///   height: 350,
///   showAUCScore: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:math' as math;
import '../../domain/entities/prediction_metrics.dart';

/// ROC curve chart widget for binary classification analysis
class ROCCurveChart extends StatefulWidget {
  /// ROC curve data points to display
  final List<ROCPoint> rocData;

  /// Chart height
  final double height;

  /// Whether to show AUC score in the chart
  final bool showAUCScore;

  /// Whether to show diagonal reference line
  final bool showReferenceLine;

  /// Whether to show optimal threshold point
  final bool showOptimalThreshold;

  /// Custom colors for ROC curve
  final ROCCurveColors? colors;

  /// Constructor with required ROC data
  const ROCCurveChart({
    super.key,
    required this.rocData,
    this.height = 350,
    this.showAUCScore = true,
    this.showReferenceLine = true,
    this.showOptimalThreshold = true,
    this.colors,
  });

  @override
  State<ROCCurveChart> createState() => _ROCCurveChartState();
}

class _ROCCurveChartState extends State<ROCCurveChart> {
  /// Touched point index for interaction
  int _touchedIndex = -1;

  /// Calculated AUC score
  double? _aucScore;

  /// Optimal threshold point
  ROCPoint? _optimalThreshold;

  @override
  void initState() {
    super.initState();
    _calculateMetrics();
  }

  @override
  void didUpdateWidget(ROCCurveChart oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.rocData != widget.rocData) {
      _calculateMetrics();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rocColors = widget.colors ?? ROCCurveColors.defaultColors(theme.colorScheme);

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
              child: widget.rocData.isEmpty
                  ? _buildNoDataMessage(theme)
                  : _buildChart(rocColors),
            ),
            const SizedBox(height: 8),
            _buildLegend(theme, rocColors),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header with title and AUC score
  Widget _buildHeader(ThemeData theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'ROC Curve Analysis',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '${widget.rocData.length} threshold points',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          ],
        ),
        if (widget.showAUCScore && _aucScore != null)
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _getAUCScoreColor(theme.colorScheme),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  'AUC: ${_aucScore!.toStringAsFixed(3)}',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _getAUCInterpretation(),
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
              ),
            ],
          ),
      ],
    );
  }

  /// Builds the ROC curve chart
  Widget _buildChart(ROCCurveColors colors) {
    if (widget.rocData.isEmpty) {
      return _buildNoDataMessage(Theme.of(context));
    }

    final lineChartData = LineChartData(
      lineTouchData: _buildTouchData(colors),
      gridData: _buildGridData(colors),
      titlesData: _buildTitlesData(colors),
      borderData: FlBorderData(
        show: true,
        border: Border.all(color: colors.border, width: 1),
      ),
      minX: 0,
      maxX: 1,
      minY: 0,
      maxY: 1,
      lineBarsData: [
        // Reference line (diagonal)
        if (widget.showReferenceLine) _buildReferenceLine(colors),
        // ROC curve
        _buildROCCurveLine(colors),
        // Optimal threshold point
        if (widget.showOptimalThreshold && _optimalThreshold != null)
          _buildOptimalThresholdLine(colors),
      ],
    );

    return LineChart(lineChartData);
  }

  /// Builds touch interaction data
  LineTouchData _buildTouchData(ROCCurveColors colors) {
    return LineTouchData(
      touchCallback: (FlTouchEvent event, LineTouchResponse? touchResponse) {
        setState(() {
          if (touchResponse == null || touchResponse.lineBarSpots == null) {
            _touchedIndex = -1;
            return;
          }

          // Only respond to the ROC curve line (index 1 if reference line exists, 0 otherwise)
          final rocLineIndex = widget.showReferenceLine ? 1 : 0;
          final spot = touchResponse.lineBarSpots!
              .where((spot) => spot.barIndex == rocLineIndex)
              .firstOrNull;

          if (spot != null) {
            _touchedIndex = spot.spotIndex;
          } else {
            _touchedIndex = -1;
          }
        });
      },
      touchTooltipData: LineTouchTooltipData(
        tooltipBgColor: colors.tooltipBackground,
        tooltipRoundedRadius: 8,
        getTooltipItems: _buildTooltipItems,
      ),
      getTouchedSpotIndicator: (LineChartBarData barData, List<int> spotIndexes) {
        return spotIndexes.map((index) {
          return TouchedSpotIndicatorData(
            FlLine(
              color: colors.touchIndicator,
              strokeWidth: 2,
              dashArray: [5, 5],
            ),
            FlDotData(
              getDotPainter: (spot, percent, barData, index) {
                return FlDotCirclePainter(
                  radius: 6,
                  color: colors.rocCurve,
                  strokeWidth: 2,
                  strokeColor: Colors.white,
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
      // Only show tooltip for ROC curve line
      final rocLineIndex = widget.showReferenceLine ? 1 : 0;
      if (touchedSpot.barIndex != rocLineIndex) {
        return LineTooltipItem('', const TextStyle());
      }

      final index = touchedSpot.spotIndex;
      if (index >= 0 && index < widget.rocData.length) {
        final point = widget.rocData[index];
        return LineTooltipItem(
          'Threshold: ${point.threshold.toStringAsFixed(3)}\n'
          'TPR: ${point.truePositiveRate.toStringAsFixed(3)}\n'
          'FPR: ${point.falsePositiveRate.toStringAsFixed(3)}\n'
          'Precision: ${point.precision?.toStringAsFixed(3) ?? 'N/A'}\n'
          'Recall: ${point.recall?.toStringAsFixed(3) ?? 'N/A'}',
          TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w500,
            fontSize: 12,
          ),
        );
      }
      return LineTooltipItem('', const TextStyle());
    }).toList();
  }

  /// Builds grid data configuration
  FlGridData _buildGridData(ROCCurveColors colors) {
    return FlGridData(
      show: true,
      drawHorizontalLine: true,
      drawVerticalLine: true,
      horizontalInterval: 0.2,
      verticalInterval: 0.2,
      getDrawingHorizontalLine: (value) {
        return FlLine(
          color: colors.gridLines,
          strokeWidth: 1,
        );
      },
      getDrawingVerticalLine: (value) {
        return FlLine(
          color: colors.gridLines,
          strokeWidth: 1,
        );
      },
    );
  }

  /// Builds titles data for axes
  FlTitlesData _buildTitlesData(ROCCurveColors colors) {
    return FlTitlesData(
      leftTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 50,
          interval: 0.2,
          getTitlesWidget: (value, meta) {
            return Text(
              value.toStringAsFixed(1),
              style: TextStyle(
                color: colors.axisLabels,
                fontSize: 11,
              ),
            );
          },
        ),
        axisNameWidget: Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Text(
            'True Positive Rate (Sensitivity)',
            style: TextStyle(
              color: colors.axisLabels,
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
          interval: 0.2,
          getTitlesWidget: (value, meta) {
            return Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                value.toStringAsFixed(1),
                style: TextStyle(
                  color: colors.axisLabels,
                  fontSize: 11,
                ),
              ),
            );
          },
        ),
        axisNameWidget: Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Text(
            'False Positive Rate (1 - Specificity)',
            style: TextStyle(
              color: colors.axisLabels,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ),
      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
    );
  }

  /// Builds the reference line (diagonal)
  LineChartBarData _buildReferenceLine(ROCCurveColors colors) {
    return LineChartBarData(
      spots: [
        const FlSpot(0, 0),
        const FlSpot(1, 1),
      ],
      color: colors.referenceLine,
      barWidth: 2,
      isStrokeCapRound: true,
      dotData: const FlDotData(show: false),
      dashArray: [8, 4],
      belowBarData: BarAreaData(show: false),
    );
  }

  /// Builds the ROC curve line
  LineChartBarData _buildROCCurveLine(ROCCurveColors colors) {
    final spots = widget.rocData.map((point) {
      return FlSpot(point.falsePositiveRate, point.truePositiveRate);
    }).toList();

    return LineChartBarData(
      spots: spots,
      color: colors.rocCurve,
      barWidth: 3,
      isStrokeCapRound: true,
      dotData: FlDotData(
        show: true,
        getDotPainter: (spot, percent, barData, index) {
          final isHighlighted = index == _touchedIndex;
          return FlDotCirclePainter(
            radius: isHighlighted ? 5 : 3,
            color: colors.rocCurve,
            strokeWidth: isHighlighted ? 2 : 1,
            strokeColor: Colors.white,
          );
        },
      ),
      belowBarData: BarAreaData(
        show: true,
        gradient: LinearGradient(
          colors: [
            colors.rocCurve.withValues(alpha: 0.3),
            colors.rocCurve.withValues(alpha: 0.1),
          ],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
    );
  }

  /// Builds the optimal threshold point line
  LineChartBarData _buildOptimalThresholdLine(ROCCurveColors colors) {
    final point = _optimalThreshold!;

    return LineChartBarData(
      spots: [
        FlSpot(point.falsePositiveRate, point.truePositiveRate),
      ],
      color: colors.optimalThreshold,
      barWidth: 0,
      dotData: FlDotData(
        show: true,
        getDotPainter: (spot, percent, barData, index) {
          return FlDotCirclePainter(
            radius: 8,
            color: colors.optimalThreshold,
            strokeWidth: 3,
            strokeColor: Colors.white,
          );
        },
      ),
      belowBarData: BarAreaData(show: false),
    );
  }

  /// Builds legend for the chart
  Widget _buildLegend(ThemeData theme, ROCCurveColors colors) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildLegendItem('ROC Curve', colors.rocCurve, theme),
        if (widget.showReferenceLine) ...[
          const SizedBox(width: 16),
          _buildLegendItem('Random Classifier', colors.referenceLine, theme),
        ],
        if (widget.showOptimalThreshold && _optimalThreshold != null) ...[
          const SizedBox(width: 16),
          _buildLegendItem('Optimal Threshold', colors.optimalThreshold, theme),
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
            Icons.timeline_outlined,
            size: 48,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No ROC curve data available',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'ROC analysis will appear when binary classification data is available',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Calculates AUC score and finds optimal threshold
  void _calculateMetrics() {
    if (widget.rocData.isEmpty) {
      _aucScore = null;
      _optimalThreshold = null;
      return;
    }

    // Calculate AUC using trapezoidal rule
    _aucScore = _calculateAUC();

    // Find optimal threshold (Youden's index: TPR - FPR)
    _optimalThreshold = _findOptimalThreshold();
  }

  /// Calculates AUC score using trapezoidal rule
  double _calculateAUC() {
    if (widget.rocData.length < 2) return 0.0;

    // Sort points by FPR
    final sortedPoints = List<ROCPoint>.from(widget.rocData)
      ..sort((a, b) => a.falsePositiveRate.compareTo(b.falsePositiveRate));

    double auc = 0.0;
    for (int i = 1; i < sortedPoints.length; i++) {
      final x1 = sortedPoints[i - 1].falsePositiveRate;
      final y1 = sortedPoints[i - 1].truePositiveRate;
      final x2 = sortedPoints[i].falsePositiveRate;
      final y2 = sortedPoints[i].truePositiveRate;

      // Trapezoidal rule: (x2 - x1) * (y1 + y2) / 2
      auc += (x2 - x1) * (y1 + y2) / 2;
    }

    return auc.clamp(0.0, 1.0);
  }

  /// Finds optimal threshold using Youden's index
  ROCPoint _findOptimalThreshold() {
    if (widget.rocData.isEmpty) {
      return ROCPoint(
        threshold: 0.5,
        truePositiveRate: 0.0,
        falsePositiveRate: 0.0,
      );
    }

    ROCPoint best = widget.rocData.first;
    double bestScore = best.truePositiveRate - best.falsePositiveRate;

    for (final point in widget.rocData) {
      final score = point.truePositiveRate - point.falsePositiveRate;
      if (score > bestScore) {
        best = point;
        bestScore = score;
      }
    }

    return best;
  }

  /// Gets color for AUC score based on performance
  Color _getAUCScoreColor(ColorScheme colorScheme) {
    if (_aucScore == null) return colorScheme.primary;

    if (_aucScore! >= 0.9) return Colors.green;
    if (_aucScore! >= 0.8) return Colors.lightGreen;
    if (_aucScore! >= 0.7) return Colors.orange;
    if (_aucScore! >= 0.6) return Colors.deepOrange;
    return Colors.red;
  }

  /// Gets interpretation text for AUC score
  String _getAUCInterpretation() {
    if (_aucScore == null) return '';

    if (_aucScore! >= 0.9) return 'Excellent';
    if (_aucScore! >= 0.8) return 'Good';
    if (_aucScore! >= 0.7) return 'Fair';
    if (_aucScore! >= 0.6) return 'Poor';
    return 'Fail';
  }
}


/// Color scheme for ROC curve chart
class ROCCurveColors {
  final Color rocCurve;
  final Color referenceLine;
  final Color optimalThreshold;
  final Color gridLines;
  final Color axisLabels;
  final Color border;
  final Color touchIndicator;
  final Color tooltipBackground;

  const ROCCurveColors({
    required this.rocCurve,
    required this.referenceLine,
    required this.optimalThreshold,
    required this.gridLines,
    required this.axisLabels,
    required this.border,
    required this.touchIndicator,
    required this.tooltipBackground,
  });

  /// Default color scheme based on material colors
  factory ROCCurveColors.defaultColors(ColorScheme colorScheme) {
    return ROCCurveColors(
      rocCurve: colorScheme.primary,
      referenceLine: Colors.grey,
      optimalThreshold: Colors.red,
      gridLines: colorScheme.outline.withValues(alpha: 0.2),
      axisLabels: colorScheme.onSurface.withValues(alpha: 0.7),
      border: colorScheme.outline.withValues(alpha: 0.3),
      touchIndicator: colorScheme.primary,
      tooltipBackground: colorScheme.inverseSurface,
    );
  }

  /// High contrast color scheme
  factory ROCCurveColors.highContrast() {
    return const ROCCurveColors(
      rocCurve: Color(0xFF1976D2),
      referenceLine: Color(0xFF757575),
      optimalThreshold: Color(0xFFD32F2F),
      gridLines: Color(0xFFBDBDBD),
      axisLabels: Color(0xFF424242),
      border: Color(0xFF9E9E9E),
      touchIndicator: Color(0xFF1976D2),
      tooltipBackground: Color(0xFF263238),
    );
  }
}