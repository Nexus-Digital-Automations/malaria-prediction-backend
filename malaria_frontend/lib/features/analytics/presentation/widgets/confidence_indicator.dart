/// Confidence interval and prediction confidence indicator widget
///
/// This widget displays confidence intervals, prediction reliability indicators,
/// and confidence distribution visualizations for model predictions.
///
/// Usage:
/// ```dart
/// ConfidenceIndicator(
///   confidenceInterval: accuracyPoint.confidenceInterval,
///   confidenceDistribution: model.confidenceDistribution,
///   reliabilityMetrics: metrics.reliability,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../domain/entities/prediction_metrics.dart';

/// Confidence indicator widget for prediction reliability visualization
class ConfidenceIndicator extends StatefulWidget {
  /// Confidence interval data to display
  final ConfidenceInterval? confidenceInterval;

  /// Confidence distribution data
  final List<ConfidenceDistribution>? confidenceDistribution;

  /// Reliability metrics
  final ReliabilityMetrics? reliabilityMetrics;

  /// Current confidence threshold
  final double confidenceThreshold;

  /// Callback when confidence threshold changes
  final ValueChanged<double>? onThresholdChanged;

  /// Whether the widget is in loading state
  final bool isLoading;

  /// Error message to display if any
  final String? errorMessage;

  /// Widget height
  final double height;

  /// Whether to show interactive threshold slider
  final bool showThresholdSlider;

  /// Whether to animate confidence changes
  final bool animateConfidence;

  /// Display mode for confidence visualization
  final ConfidenceDisplayMode displayMode;

  /// Constructor with required confidence data
  const ConfidenceIndicator({
    super.key,
    this.confidenceInterval,
    this.confidenceDistribution,
    this.reliabilityMetrics,
    this.confidenceThreshold = 0.8,
    this.onThresholdChanged,
    this.isLoading = false,
    this.errorMessage,
    this.height = 350,
    this.showThresholdSlider = true,
    this.animateConfidence = true,
    this.displayMode = ConfidenceDisplayMode.combined,
  });

  @override
  State<ConfidenceIndicator> createState() => _ConfidenceIndicatorState();
}

class _ConfidenceIndicatorState extends State<ConfidenceIndicator>
    with TickerProviderStateMixin {
  /// Animation controller for confidence animations
  late AnimationController _animationController;

  /// Currently selected confidence range
  ConfidenceRange? _selectedRange;

  /// Display mode selector
  late ConfidenceDisplayMode _currentDisplayMode;

  @override
  void initState() {
    super.initState();
    _currentDisplayMode = widget.displayMode;
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    if (widget.animateConfidence) {
      _animationController.forward();
    } else {
      _animationController.value = 1.0;
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

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
        child: widget.isLoading
            ? _buildLoadingState(theme)
            : widget.errorMessage != null
                ? _buildErrorState(theme)
                : _buildContent(theme, colorScheme),
      ),
    );
  }

  /// Builds the main content
  Widget _buildContent(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildHeader(theme, colorScheme),
        const SizedBox(height: 16),
        _buildControls(theme, colorScheme),
        const SizedBox(height: 16),
        Expanded(
          child: _buildVisualization(theme, colorScheme),
        ),
        if (widget.showThresholdSlider) ...[
          const SizedBox(height: 16),
          _buildThresholdSlider(theme, colorScheme),
        ],
      ],
    );
  }

  /// Builds the widget header
  Widget _buildHeader(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: colorScheme.tertiary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            Icons.psychology_outlined,
            size: 20,
            color: colorScheme.tertiary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Confidence Indicators',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Prediction reliability and confidence metrics',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        _buildOverallConfidenceIndicator(theme, colorScheme),
      ],
    );
  }

  /// Builds overall confidence indicator
  Widget _buildOverallConfidenceIndicator(ThemeData theme, ColorScheme colorScheme) {
    if (widget.reliabilityMetrics == null) return const SizedBox.shrink();

    final overallReliability = (widget.reliabilityMetrics!.consistency +
                               widget.reliabilityMetrics!.stability +
                               widget.reliabilityMetrics!.uncertaintyCalibration) / 3;

    Color indicatorColor;
    IconData indicatorIcon;
    String tooltip;

    if (overallReliability >= 0.9) {
      indicatorColor = Colors.green;
      indicatorIcon = Icons.verified;
      tooltip = 'Highly Reliable Predictions';
    } else if (overallReliability >= 0.8) {
      indicatorColor = Colors.lightGreen;
      indicatorIcon = Icons.check_circle;
      tooltip = 'Reliable Predictions';
    } else if (overallReliability >= 0.7) {
      indicatorColor = Colors.orange;
      indicatorIcon = Icons.warning;
      tooltip = 'Moderately Reliable';
    } else {
      indicatorColor = Colors.red;
      indicatorIcon = Icons.error;
      tooltip = 'Low Reliability';
    }

    return Tooltip(
      message: tooltip,
      child: Container(
        padding: const EdgeInsets.all(6),
        decoration: BoxDecoration(
          color: indicatorColor.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Icon(
          indicatorIcon,
          size: 18,
          color: indicatorColor,
        ),
      ),
    );
  }

  /// Builds control panel
  Widget _buildControls(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Text(
          'Display Mode:',
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(width: 8),
        DropdownButton<ConfidenceDisplayMode>(
          value: _currentDisplayMode,
          items: ConfidenceDisplayMode.values.map((mode) {
            return DropdownMenuItem(
              value: mode,
              child: Text(_getDisplayModeLabel(mode)),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) {
              setState(() => _currentDisplayMode = value);
            }
          },
          underline: Container(),
        ),
        const Spacer(),
        if (widget.confidenceInterval != null) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              'CI: ${(widget.confidenceInterval!.confidenceLevel * 100).toStringAsFixed(0)}%',
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ],
    );
  }

  /// Builds visualization based on current display mode
  Widget _buildVisualization(ThemeData theme, ColorScheme colorScheme) {
    switch (_currentDisplayMode) {
      case ConfidenceDisplayMode.interval:
        return _buildConfidenceInterval(theme, colorScheme);
      case ConfidenceDisplayMode.distribution:
        return _buildConfidenceDistribution(theme, colorScheme);
      case ConfidenceDisplayMode.reliability:
        return _buildReliabilityMetrics(theme, colorScheme);
      case ConfidenceDisplayMode.combined:
        return _buildCombinedView(theme, colorScheme);
    }
  }

  /// Builds confidence interval visualization
  Widget _buildConfidenceInterval(ThemeData theme, ColorScheme colorScheme) {
    if (widget.confidenceInterval == null) {
      return _buildNoDataMessage('No confidence interval data available', theme);
    }

    final interval = widget.confidenceInterval!;
    final range = interval.upperBound - interval.lowerBound;
    final midpoint = (interval.upperBound + interval.lowerBound) / 2;

    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return Column(
          children: [
            Text(
              'Confidence Interval',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Visual confidence interval display
                    SizedBox(
                      height: 60,
                      width: 300,
                      child: Stack(
                        children: [
                          // Background bar
                          Positioned(
                            left: 0,
                            right: 0,
                            top: 25,
                            child: Container(
                              height: 10,
                              decoration: BoxDecoration(
                                color: colorScheme.outline.withValues(alpha: 0.2),
                                borderRadius: BorderRadius.circular(5),
                              ),
                            ),
                          ),
                          // Confidence interval bar
                          Positioned(
                            left: interval.lowerBound * 300 * _animationController.value,
                            right: (1 - interval.upperBound) * 300 * _animationController.value,
                            top: 20,
                            child: Container(
                              height: 20,
                              decoration: BoxDecoration(
                                color: colorScheme.primary.withValues(alpha: 0.7),
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          ),
                          // Lower bound marker
                          Positioned(
                            left: interval.lowerBound * 300 * _animationController.value - 2,
                            top: 15,
                            child: Container(
                              width: 4,
                              height: 30,
                              decoration: BoxDecoration(
                                color: colorScheme.primary,
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                          ),
                          // Upper bound marker
                          Positioned(
                            left: interval.upperBound * 300 * _animationController.value - 2,
                            top: 15,
                            child: Container(
                              width: 4,
                              height: 30,
                              decoration: BoxDecoration(
                                color: colorScheme.primary,
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                          ),
                          // Midpoint marker
                          Positioned(
                            left: midpoint * 300 * _animationController.value - 1,
                            top: 10,
                            child: Container(
                              width: 2,
                              height: 40,
                              decoration: BoxDecoration(
                                color: colorScheme.secondary,
                                borderRadius: BorderRadius.circular(1),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    // Labels
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _buildIntervalLabel(
                          'Lower Bound',
                          interval.lowerBound,
                          colorScheme.primary,
                          theme,
                        ),
                        _buildIntervalLabel(
                          'Estimate',
                          midpoint,
                          colorScheme.secondary,
                          theme,
                        ),
                        _buildIntervalLabel(
                          'Upper Bound',
                          interval.upperBound,
                          colorScheme.primary,
                          theme,
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        children: [
                          Text(
                            'Interval Width: ${(range * 100).toStringAsFixed(1)}%',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            'Confidence Level: ${(interval.confidenceLevel * 100).toStringAsFixed(0)}%',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  /// Builds interval label
  Widget _buildIntervalLabel(String label, double value, Color color, ThemeData theme) {
    return Column(
      children: [
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          '${(value * 100).toStringAsFixed(1)}%',
          style: theme.textTheme.titleSmall?.copyWith(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  /// Builds confidence distribution visualization
  Widget _buildConfidenceDistribution(ThemeData theme, ColorScheme colorScheme) {
    if (widget.confidenceDistribution == null || widget.confidenceDistribution!.isEmpty) {
      return _buildNoDataMessage('No confidence distribution data available', theme);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Confidence Distribution',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: _buildDistributionChart(theme, colorScheme),
        ),
      ],
    );
  }

  /// Builds distribution chart
  Widget _buildDistributionChart(ThemeData theme, ColorScheme colorScheme) {
    final distribution = widget.confidenceDistribution!;

    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        final barGroups = distribution.asMap().entries.map((entry) {
          final index = entry.key;
          final data = entry.value;
          final isSelected = _selectedRange != null &&
                            _selectedRange!.lowerBound == data.range.lowerBound;

          return BarChartGroupData(
            x: index,
            barRods: [
              BarChartRodData(
                toY: data.count.toDouble() * _animationController.value,
                color: isSelected
                    ? colorScheme.primary
                    : _getConfidenceColor(data.predictedConfidence, colorScheme),
                width: 16,
                borderRadius: BorderRadius.circular(4),
                gradient: LinearGradient(
                  colors: [
                    (isSelected ? colorScheme.primary :
                     _getConfidenceColor(data.predictedConfidence, colorScheme))
                        .withValues(alpha: 0.8),
                    isSelected ? colorScheme.primary :
                    _getConfidenceColor(data.predictedConfidence, colorScheme),
                  ],
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                ),
              ),
            ],
          );
        }).toList();

        return BarChart(
          BarChartData(
            alignment: BarChartAlignment.spaceAround,
            barGroups: barGroups,
            titlesData: FlTitlesData(
              show: true,
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  getTitlesWidget: (value, meta) {
                    final index = value.toInt();
                    if (index >= 0 && index < distribution.length) {
                      final range = distribution[index].range;
                      return Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          '${(range.lowerBound * 100).toInt()}-${(range.upperBound * 100).toInt()}%',
                          style: theme.textTheme.bodySmall,
                        ),
                      );
                    }
                    return const SizedBox.shrink();
                  },
                ),
              ),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  getTitlesWidget: (value, meta) {
                    return Text(
                      value.toInt().toString(),
                      style: theme.textTheme.bodySmall,
                    );
                  },
                  reservedSize: 40,
                ),
              ),
              topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            ),
            borderData: FlBorderData(show: false),
            gridData: FlGridData(
              show: true,
              drawHorizontalLine: true,
              drawVerticalLine: false,
              horizontalInterval: 10,
              getDrawingHorizontalLine: (value) => FlLine(
                color: colorScheme.outline.withValues(alpha: 0.2),
                strokeWidth: 1,
              ),
            ),
            barTouchData: BarTouchData(
              enabled: true,
              touchTooltipData: BarTouchTooltipData(
                tooltipBgColor: colorScheme.inverseSurface,
                tooltipRoundedRadius: 8,
                getTooltipItem: (group, groupIndex, rod, rodIndex) {
                  final data = distribution[group.x];
                  return BarTooltipItem(
                    'Confidence: ${(data.range.lowerBound * 100).toInt()}-${(data.range.upperBound * 100).toInt()}%\n'
                    'Count: ${data.count}\n'
                    'Actual Accuracy: ${(data.actualAccuracy * 100).toStringAsFixed(1)}%',
                    TextStyle(
                      color: colorScheme.onInverseSurface,
                      fontWeight: FontWeight.w500,
                      fontSize: 12,
                    ),
                  );
                },
              ),
              touchCallback: (FlTouchEvent event, barTouchResponse) {
                if (event is FlTapUpEvent && barTouchResponse != null) {
                  final touchedGroup = barTouchResponse.spot?.touchedBarGroup;
                  if (touchedGroup != null) {
                    setState(() {
                      _selectedRange = distribution[touchedGroup.x].range;
                    });
                  }
                }
              },
            ),
          ),
        );
      },
    );
  }

  /// Builds reliability metrics visualization
  Widget _buildReliabilityMetrics(ThemeData theme, ColorScheme colorScheme) {
    if (widget.reliabilityMetrics == null) {
      return _buildNoDataMessage('No reliability metrics available', theme);
    }

    final metrics = widget.reliabilityMetrics!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Reliability Metrics',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: AnimatedBuilder(
            animation: _animationController,
            builder: (context, child) {
              return Column(
                children: [
                  _buildReliabilityMetric(
                    'Consistency',
                    metrics.consistency,
                    'Prediction consistency across similar inputs',
                    Icons.check_circle_outline,
                    theme,
                    colorScheme,
                  ),
                  const SizedBox(height: 12),
                  _buildReliabilityMetric(
                    'Stability',
                    metrics.stability,
                    'Model stability over time',
                    Icons.timeline,
                    theme,
                    colorScheme,
                  ),
                  const SizedBox(height: 12),
                  _buildReliabilityMetric(
                    'Uncertainty Calibration',
                    metrics.uncertaintyCalibration,
                    'Quality of uncertainty quantification',
                    Icons.psychology,
                    theme,
                    colorScheme,
                  ),
                  const SizedBox(height: 12),
                  _buildReliabilityMetric(
                    'OOD Detection',
                    metrics.oodDetection,
                    'Out-of-distribution detection capability',
                    Icons.security,
                    theme,
                    colorScheme,
                  ),
                  const SizedBox(height: 12),
                  _buildReliabilityMetric(
                    'Robustness',
                    metrics.robustness,
                    'Adversarial robustness score',
                    Icons.shield,
                    theme,
                    colorScheme,
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  /// Builds individual reliability metric
  Widget _buildReliabilityMetric(
    String label,
    double value,
    String description,
    IconData icon,
    ThemeData theme,
    ColorScheme colorScheme,
  ) {
    final animatedValue = value * _animationController.value;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: _getReliabilityColor(animatedValue).withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              icon,
              size: 20,
              color: _getReliabilityColor(animatedValue),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  description,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
                const SizedBox(height: 4),
                LinearProgressIndicator(
                  value: animatedValue,
                  backgroundColor: colorScheme.outline.withValues(alpha: 0.2),
                  valueColor: AlwaysStoppedAnimation(
                    _getReliabilityColor(animatedValue),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '${(animatedValue * 100).toStringAsFixed(1)}%',
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: _getReliabilityColor(animatedValue),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds combined view
  Widget _buildCombinedView(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: _buildConfidenceInterval(theme, colorScheme),
        ),
        const SizedBox(width: 16),
        Expanded(
          flex: 3,
          child: widget.reliabilityMetrics != null
              ? _buildReliabilityMetrics(theme, colorScheme)
              : _buildConfidenceDistribution(theme, colorScheme),
        ),
      ],
    );
  }

  /// Builds threshold slider
  Widget _buildThresholdSlider(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Confidence Threshold',
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: Slider(
                value: widget.confidenceThreshold,
                onChanged: widget.onThresholdChanged,
                min: 0.0,
                max: 1.0,
                divisions: 100,
                label: '${(widget.confidenceThreshold * 100).toStringAsFixed(0)}%',
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: colorScheme.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                '${(widget.confidenceThreshold * 100).toStringAsFixed(0)}%',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: colorScheme.primary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds loading state
  Widget _buildLoadingState(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation(theme.colorScheme.primary),
          ),
          const SizedBox(height: 16),
          Text(
            'Loading confidence indicators...',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds error state
  Widget _buildErrorState(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline,
            size: 48,
            color: theme.colorScheme.error,
          ),
          const SizedBox(height: 16),
          Text(
            'Error loading confidence data',
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.error,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            widget.errorMessage ?? 'Unknown error occurred',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage(String message, ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.info_outline,
            size: 48,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Helper methods

  /// Gets display mode label
  String _getDisplayModeLabel(ConfidenceDisplayMode mode) {
    switch (mode) {
      case ConfidenceDisplayMode.interval:
        return 'Interval';
      case ConfidenceDisplayMode.distribution:
        return 'Distribution';
      case ConfidenceDisplayMode.reliability:
        return 'Reliability';
      case ConfidenceDisplayMode.combined:
        return 'Combined';
    }
  }

  /// Gets confidence color based on value
  Color _getConfidenceColor(double confidence, ColorScheme colorScheme) {
    if (confidence >= 0.9) return Colors.green;
    if (confidence >= 0.8) return Colors.lightGreen;
    if (confidence >= 0.7) return colorScheme.primary;
    if (confidence >= 0.6) return Colors.orange;
    return Colors.red;
  }

  /// Gets reliability color based on value
  Color _getReliabilityColor(double reliability) {
    if (reliability >= 0.9) return Colors.green;
    if (reliability >= 0.8) return Colors.lightGreen;
    if (reliability >= 0.7) return Colors.orange;
    return Colors.red;
  }
}

/// Display mode enumeration for confidence visualization
enum ConfidenceDisplayMode {
  interval,
  distribution,
  reliability,
  combined,
}