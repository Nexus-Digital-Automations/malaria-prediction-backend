/// Metric card widget for displaying key prediction statistics
///
/// This widget displays individual prediction metrics in a card format
/// with value, trend indicators, and optional sparkline visualization.
///
/// Usage:
/// ```dart
/// MetricCard(
///   title: 'Prediction Accuracy',
///   value: 0.87,
///   subtitle: 'Last 30 days',
///   trend: MetricTrend.increasing,
///   trendValue: 0.05,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

/// Metric card widget for displaying prediction statistics
class MetricCard extends StatelessWidget {
  /// Metric title
  final String title;

  /// Primary metric value (0.0 to 1.0 for percentages)
  final double value;

  /// Optional subtitle for context
  final String? subtitle;

  /// Metric trend direction
  final MetricTrend? trend;

  /// Trend change value
  final double? trendValue;

  /// Historical data for sparkline (optional)
  final List<double>? historicalData;

  /// Value formatter (defaults to percentage)
  final String Function(double)? valueFormatter;

  /// Custom color for the metric
  final Color? color;

  /// Icon for the metric
  final IconData? icon;

  /// Additional context information
  final String? contextInfo;

  /// Whether this metric represents a good or bad value when high
  final bool higherIsBetter;

  /// Constructor with required title and value
  const MetricCard({
    super.key,
    required this.title,
    required this.value,
    this.subtitle,
    this.trend,
    this.trendValue,
    this.historicalData,
    this.valueFormatter,
    this.color,
    this.icon,
    this.contextInfo,
    this.higherIsBetter = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final effectiveColor = color ?? _getDefaultColor(colorScheme);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              effectiveColor.withValues(alpha: 0.05),
              effectiveColor.withValues(alpha: 0.02),
            ],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(theme, effectiveColor),
            const SizedBox(height: 12),
            _buildValue(theme, effectiveColor),
            if (trend != null || trendValue != null) ...[
              const SizedBox(height: 8),
              _buildTrend(theme),
            ],
            if (historicalData != null && historicalData!.isNotEmpty) ...[
              const SizedBox(height: 12),
              _buildSparkline(effectiveColor),
            ],
            if (contextInfo != null) ...[
              const SizedBox(height: 8),
              _buildContextInfo(theme),
            ],
          ],
        ),
      ),
    );
  }

  /// Builds the card header with title and icon
  Widget _buildHeader(ThemeData theme, Color effectiveColor) {
    return Row(
      children: [
        if (icon != null) ...[
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: effectiveColor.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              icon,
              size: 20,
              color: effectiveColor,
            ),
          ),
          const SizedBox(width: 12),
        ],
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: theme.colorScheme.onSurface,
                ),
              ),
              if (subtitle != null)
                Text(
                  subtitle!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
            ],
          ),
        ),
        _buildQualityIndicator(theme, effectiveColor),
      ],
    );
  }

  /// Builds the primary value display
  Widget _buildValue(ThemeData theme, Color effectiveColor) {
    final formattedValue = valueFormatter?.call(value) ?? _defaultFormatter(value);

    return Text(
      formattedValue,
      style: theme.textTheme.headlineMedium?.copyWith(
        fontWeight: FontWeight.bold,
        color: effectiveColor,
        height: 1.0,
      ),
    );
  }

  /// Builds the trend indicator
  Widget _buildTrend(ThemeData theme) {
    if (trend == null && trendValue == null) return const SizedBox.shrink();

    final trendColor = _getTrendColor(theme.colorScheme);
    final trendIcon = _getTrendIcon();
    final trendText = _getTrendText();

    return Row(
      children: [
        if (trendIcon != null) ...[
          Icon(
            trendIcon,
            size: 16,
            color: trendColor,
          ),
          const SizedBox(width: 4),
        ],
        Text(
          trendText,
          style: theme.textTheme.bodySmall?.copyWith(
            color: trendColor,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  /// Builds the sparkline chart
  Widget _buildSparkline(Color effectiveColor) {
    if (historicalData == null || historicalData!.isEmpty) {
      return const SizedBox.shrink();
    }

    final spots = historicalData!.asMap().entries.map((entry) {
      return FlSpot(entry.key.toDouble(), entry.value);
    }).toList();

    return SizedBox(
      height: 40,
      child: LineChart(
        LineChartData(
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              color: effectiveColor,
              barWidth: 2,
              isStrokeCapRound: true,
              dotData: const FlDotData(show: false),
              belowBarData: BarAreaData(
                show: true,
                gradient: LinearGradient(
                  colors: [
                    effectiveColor.withValues(alpha: 0.3),
                    effectiveColor.withValues(alpha: 0.05),
                  ],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
            ),
          ],
          titlesData: const FlTitlesData(show: false),
          gridData: const FlGridData(show: false),
          borderData: FlBorderData(show: false),
          lineTouchData: const LineTouchData(enabled: false),
        ),
      ),
    );
  }

  /// Builds context information
  Widget _buildContextInfo(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        contextInfo!,
        style: theme.textTheme.bodySmall?.copyWith(
          color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
        ),
      ),
    );
  }

  /// Builds quality indicator based on value
  Widget _buildQualityIndicator(ThemeData theme, Color effectiveColor) {
    final quality = _getQualityLevel();
    Color indicatorColor;
    IconData indicatorIcon;

    switch (quality) {
      case QualityLevel.excellent:
        indicatorColor = Colors.green;
        indicatorIcon = Icons.trending_up;
        break;
      case QualityLevel.good:
        indicatorColor = Colors.lightGreen;
        indicatorIcon = Icons.check_circle_outline;
        break;
      case QualityLevel.fair:
        indicatorColor = Colors.orange;
        indicatorIcon = Icons.warning_amber_outlined;
        break;
      case QualityLevel.poor:
        indicatorColor = Colors.red;
        indicatorIcon = Icons.trending_down;
        break;
    }

    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: indicatorColor.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Icon(
        indicatorIcon,
        size: 16,
        color: indicatorColor,
      ),
    );
  }

  /// Gets default color based on metric value
  Color _getDefaultColor(ColorScheme colorScheme) {
    final quality = _getQualityLevel();

    switch (quality) {
      case QualityLevel.excellent:
        return Colors.green;
      case QualityLevel.good:
        return Colors.lightGreen;
      case QualityLevel.fair:
        return Colors.orange;
      case QualityLevel.poor:
        return Colors.red;
    }
  }

  /// Gets quality level based on metric value
  QualityLevel _getQualityLevel() {
    final normalizedValue = higherIsBetter ? value : (1.0 - value);

    if (normalizedValue >= 0.9) return QualityLevel.excellent;
    if (normalizedValue >= 0.8) return QualityLevel.good;
    if (normalizedValue >= 0.7) return QualityLevel.fair;
    return QualityLevel.poor;
  }

  /// Gets trend color based on trend direction and metric type
  Color _getTrendColor(ColorScheme colorScheme) {
    if (trend == null) return colorScheme.onSurface.withValues(alpha: 0.6);

    switch (trend!) {
      case MetricTrend.increasing:
        return higherIsBetter ? Colors.green : Colors.red;
      case MetricTrend.decreasing:
        return higherIsBetter ? Colors.red : Colors.green;
      case MetricTrend.stable:
        return colorScheme.onSurface.withValues(alpha: 0.6);
    }
  }

  /// Gets trend icon based on trend direction
  IconData? _getTrendIcon() {
    if (trend == null) return null;

    switch (trend!) {
      case MetricTrend.increasing:
        return Icons.trending_up;
      case MetricTrend.decreasing:
        return Icons.trending_down;
      case MetricTrend.stable:
        return Icons.trending_flat;
    }
  }

  /// Gets trend text description
  String _getTrendText() {
    if (trend == null && trendValue == null) return '';

    String trendDescription = '';
    if (trend != null) {
      switch (trend!) {
        case MetricTrend.increasing:
          trendDescription = 'Increasing';
          break;
        case MetricTrend.decreasing:
          trendDescription = 'Decreasing';
          break;
        case MetricTrend.stable:
          trendDescription = 'Stable';
          break;
      }
    }

    if (trendValue != null) {
      final formattedTrend = valueFormatter?.call(trendValue!.abs()) ??
                           _defaultFormatter(trendValue!.abs());
      trendDescription += trendDescription.isNotEmpty ? ' $formattedTrend' : formattedTrend;
    }

    return trendDescription;
  }

  /// Default value formatter (percentage)
  String _defaultFormatter(double value) {
    return '${(value * 100).toStringAsFixed(1)}%';
  }
}

/// Specialized metric cards for common prediction metrics

/// Accuracy metric card
class AccuracyCard extends MetricCard {
  const AccuracyCard({
    super.key,
    required super.value,
    super.subtitle = 'Overall accuracy',
    super.trend,
    super.trendValue,
    super.historicalData,
    super.contextInfo,
  }) : super(
          title: 'Accuracy',
          icon: Icons.target,
          higherIsBetter: true,
        );
}

/// Precision metric card
class PrecisionCard extends MetricCard {
  const PrecisionCard({
    super.key,
    required super.value,
    super.subtitle = 'Positive prediction quality',
    super.trend,
    super.trendValue,
    super.historicalData,
    super.contextInfo,
  }) : super(
          title: 'Precision',
          icon: Icons.precision_manufacturing,
          higherIsBetter: true,
        );
}

/// Recall metric card
class RecallCard extends MetricCard {
  const RecallCard({
    super.key,
    required super.value,
    super.subtitle = 'Sensitivity',
    super.trend,
    super.trendValue,
    super.historicalData,
    super.contextInfo,
  }) : super(
          title: 'Recall',
          icon: Icons.find_in_page,
          higherIsBetter: true,
        );
}

/// F1 Score metric card
class F1ScoreCard extends MetricCard {
  const F1ScoreCard({
    super.key,
    required super.value,
    super.subtitle = 'Balanced performance',
    super.trend,
    super.trendValue,
    super.historicalData,
    super.contextInfo,
  }) : super(
          title: 'F1 Score',
          icon: Icons.balance,
          higherIsBetter: true,
        );
}

/// AUC Score metric card
class AUCScoreCard extends MetricCard {
  const AUCScoreCard({
    super.key,
    required super.value,
    super.subtitle = 'Area under ROC curve',
    super.trend,
    super.trendValue,
    super.historicalData,
    super.contextInfo,
  }) : super(
          title: 'AUC Score',
          icon: Icons.timeline,
          higherIsBetter: true,
        );
}

/// Prediction speed metric card
class PredictionSpeedCard extends MetricCard {
  const PredictionSpeedCard({
    super.key,
    required super.value,
    super.subtitle = 'Average prediction time',
    super.trend,
    super.trendValue,
    super.historicalData,
    super.contextInfo,
  }) : super(
          title: 'Speed',
          icon: Icons.speed,
          valueFormatter: _speedFormatter,
          higherIsBetter: false,
        );

  static String _speedFormatter(double value) {
    // Assume value is in seconds, convert to appropriate unit
    if (value < 1) {
      return '${(value * 1000).toStringAsFixed(0)}ms';
    } else if (value < 60) {
      return '${value.toStringAsFixed(1)}s';
    } else {
      return '${(value / 60).toStringAsFixed(1)}min';
    }
  }
}

/// Model confidence metric card
class ConfidenceCard extends MetricCard {
  const ConfidenceCard({
    super.key,
    required super.value,
    super.subtitle = 'Average prediction confidence',
    super.trend,
    super.trendValue,
    super.historicalData,
    super.contextInfo,
  }) : super(
          title: 'Confidence',
          icon: Icons.psychology,
          higherIsBetter: true,
        );
}

/// Metric trend enumeration
enum MetricTrend {
  increasing,
  decreasing,
  stable,
}

/// Quality level enumeration
enum QualityLevel {
  excellent,
  good,
  fair,
  poor,
}