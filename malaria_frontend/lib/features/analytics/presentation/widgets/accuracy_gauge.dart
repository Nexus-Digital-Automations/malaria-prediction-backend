/// Accuracy gauge widget using fl_chart RadialBarChart
///
/// This widget displays prediction accuracy using a circular gauge
/// with color-coded segments and animated progress indication.
///
/// Usage:
/// ```dart
/// AccuracyGauge(
///   accuracy: 0.87,
///   size: 200,
///   showLabels: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:math' as math;

/// Accuracy gauge widget for prediction accuracy visualization
class AccuracyGauge extends StatefulWidget {
  /// Accuracy value (0.0 to 1.0)
  final double accuracy;

  /// Gauge size (width and height)
  final double size;

  /// Whether to show accuracy labels and text
  final bool showLabels;

  /// Whether to animate the gauge
  final bool animate;

  /// Animation duration
  final Duration animationDuration;

  /// Custom color scheme for gauge segments
  final AccuracyGaugeColors? colors;

  /// Gauge thickness
  final double strokeWidth;

  /// Whether to show performance bands
  final bool showPerformanceBands;

  /// Constructor with required accuracy value
  const AccuracyGauge({
    super.key,
    required this.accuracy,
    this.size = 200,
    this.showLabels = true,
    this.animate = true,
    this.animationDuration = const Duration(milliseconds: 1500),
    this.colors,
    this.strokeWidth = 20,
    this.showPerformanceBands = true,
  });

  @override
  State<AccuracyGauge> createState() => _AccuracyGaugeState();
}

class _AccuracyGaugeState extends State<AccuracyGauge>
    with TickerProviderStateMixin {
  /// Animation controller for gauge animation
  late AnimationController _animationController;

  /// Animation for accuracy value
  late Animation<double> _accuracyAnimation;

  /// Current displayed accuracy value
  double _currentAccuracy = 0.0;

  @override
  void initState() {
    super.initState();
    _setupAnimation();
    if (widget.animate) {
      _animationController.forward();
    } else {
      _currentAccuracy = widget.accuracy;
    }
  }

  @override
  void didUpdateWidget(AccuracyGauge oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.accuracy != widget.accuracy) {
      _updateAccuracy();
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
    final gaugeColors = widget.colors ?? AccuracyGaugeColors.defaultColors(theme.colorScheme);

    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Performance bands background (if enabled)
          if (widget.showPerformanceBands)
            _buildPerformanceBands(gaugeColors),

          // Main gauge
          _buildGauge(gaugeColors),

          // Center content
          _buildCenterContent(theme, gaugeColors),
        ],
      ),
    );
  }

  /// Sets up the animation
  void _setupAnimation() {
    _animationController = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );

    _accuracyAnimation = Tween<double>(
      begin: 0.0,
      end: widget.accuracy,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOutCubic,
    ));

    _accuracyAnimation.addListener(() {
      setState(() {
        _currentAccuracy = _accuracyAnimation.value;
      });
    });
  }

  /// Updates accuracy with animation
  void _updateAccuracy() {
    if (widget.animate) {
      _accuracyAnimation = Tween<double>(
        begin: _currentAccuracy,
        end: widget.accuracy,
      ).animate(CurvedAnimation(
        parent: _animationController,
        curve: Curves.easeInOutCubic,
      ));

      _animationController.reset();
      _animationController.forward();
    } else {
      setState(() {
        _currentAccuracy = widget.accuracy;
      });
    }
  }

  /// Builds performance bands background
  Widget _buildPerformanceBands(AccuracyGaugeColors colors) {
    return PieChart(
      PieChartData(
        startDegreeOffset: 135, // Start from bottom-left
        sections: [
          // Poor (0% - 60%)
          PieChartSectionData(
            value: 60,
            color: colors.poor.withValues(alpha: 0.3),
            radius: widget.strokeWidth + 10,
            showTitle: false,
          ),
          // Fair (60% - 70%)
          PieChartSectionData(
            value: 10,
            color: colors.fair.withValues(alpha: 0.3),
            radius: widget.strokeWidth + 10,
            showTitle: false,
          ),
          // Good (70% - 90%)
          PieChartSectionData(
            value: 20,
            color: colors.good.withValues(alpha: 0.3),
            radius: widget.strokeWidth + 10,
            showTitle: false,
          ),
          // Excellent (90% - 100%)
          PieChartSectionData(
            value: 10,
            color: colors.excellent.withValues(alpha: 0.3),
            radius: widget.strokeWidth + 10,
            showTitle: false,
          ),
          // Empty space to complete circle
          PieChartSectionData(
            value: 90, // 270 degrees empty
            color: Colors.transparent,
            radius: widget.strokeWidth + 10,
            showTitle: false,
          ),
        ],
        centerSpaceRadius: (widget.size - (widget.strokeWidth + 10) * 2) / 2,
        sectionsSpace: 1,
      ),
    );
  }

  /// Builds the main gauge
  Widget _buildGauge(AccuracyGaugeColors colors) {
    final accuracyPercentage = (_currentAccuracy * 270).clamp(0.0, 270.0); // 270 degrees max
    final remainingPercentage = 270 - accuracyPercentage;

    return PieChart(
      PieChartData(
        startDegreeOffset: 135, // Start from bottom-left
        sections: [
          // Accuracy fill
          if (accuracyPercentage > 0)
            PieChartSectionData(
              value: accuracyPercentage,
              color: _getAccuracyColor(colors),
              radius: widget.strokeWidth,
              showTitle: false,
            ),
          // Remaining empty space
          if (remainingPercentage > 0)
            PieChartSectionData(
              value: remainingPercentage,
              color: colors.background,
              radius: widget.strokeWidth,
              showTitle: false,
            ),
          // Complete the circle (empty space)
          PieChartSectionData(
            value: 90, // 90 degrees empty to complete 360
            color: Colors.transparent,
            radius: widget.strokeWidth,
            showTitle: false,
          ),
        ],
        centerSpaceRadius: (widget.size - widget.strokeWidth * 2) / 2,
        sectionsSpace: 0,
      ),
    );
  }

  /// Builds center content with accuracy value and labels
  Widget _buildCenterContent(ThemeData theme, AccuracyGaugeColors colors) {
    if (!widget.showLabels) return const SizedBox.shrink();

    final accuracyText = '${(_currentAccuracy * 100).toStringAsFixed(1)}%';
    final performanceLevel = _getPerformanceLevel();
    final performanceColor = _getAccuracyColor(colors);

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          accuracyText,
          style: theme.textTheme.headlineLarge?.copyWith(
            fontWeight: FontWeight.bold,
            color: performanceColor,
            height: 1.0,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Accuracy',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            color: performanceColor.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: performanceColor.withValues(alpha: 0.3),
              width: 1,
            ),
          ),
          child: Text(
            performanceLevel,
            style: theme.textTheme.bodySmall?.copyWith(
              color: performanceColor,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  /// Gets accuracy color based on current value
  Color _getAccuracyColor(AccuracyGaugeColors colors) {
    if (_currentAccuracy >= 0.9) return colors.excellent;
    if (_currentAccuracy >= 0.8) return colors.good;
    if (_currentAccuracy >= 0.7) return colors.fair;
    return colors.poor;
  }

  /// Gets performance level text based on accuracy
  String _getPerformanceLevel() {
    if (_currentAccuracy >= 0.9) return 'Excellent';
    if (_currentAccuracy >= 0.8) return 'Good';
    if (_currentAccuracy >= 0.7) return 'Fair';
    return 'Poor';
  }
}

/// Enhanced accuracy gauge with additional metrics
class EnhancedAccuracyGauge extends StatelessWidget {
  /// Primary accuracy value
  final double accuracy;

  /// Secondary metrics to display
  final Map<String, double> secondaryMetrics;

  /// Gauge size
  final double size;

  /// Whether to show secondary metrics
  final bool showSecondaryMetrics;

  /// Constructor with required accuracy and optional secondary metrics
  const EnhancedAccuracyGauge({
    super.key,
    required this.accuracy,
    this.secondaryMetrics = const {},
    this.size = 250,
    this.showSecondaryMetrics = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: size,
      height: size + (showSecondaryMetrics ? 80 : 0),
      child: Column(
        children: [
          AccuracyGauge(
            accuracy: accuracy,
            size: size,
            showLabels: true,
          ),
          if (showSecondaryMetrics && secondaryMetrics.isNotEmpty) ...[
            const SizedBox(height: 16),
            _buildSecondaryMetrics(theme),
          ],
        ],
      ),
    );
  }

  /// Builds secondary metrics display
  Widget _buildSecondaryMetrics(ThemeData theme) {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      alignment: WrapAlignment.center,
      children: secondaryMetrics.entries.map((entry) {
        return _buildSecondaryMetric(entry.key, entry.value, theme);
      }).toList(),
    );
  }

  /// Builds individual secondary metric
  Widget _buildSecondaryMetric(String label, double value, ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '${(value * 100).toStringAsFixed(1)}%',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onSurface,
            ),
          ),
          Text(
            label,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }
}

/// Multi-gauge widget for comparing multiple accuracy metrics
class MultiAccuracyGauge extends StatelessWidget {
  /// List of accuracy values with labels
  final List<AccuracyMetric> metrics;

  /// Individual gauge size
  final double gaugeSize;

  /// Whether to show comparative labels
  final bool showComparison;

  /// Constructor with required metrics
  const MultiAccuracyGauge({
    super.key,
    required this.metrics,
    this.gaugeSize = 150,
    this.showComparison = true,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      runSpacing: 16,
      alignment: WrapAlignment.center,
      children: metrics.map((metric) {
        return Column(
          children: [
            AccuracyGauge(
              accuracy: metric.value,
              size: gaugeSize,
              showLabels: true,
              strokeWidth: 15,
            ),
            const SizedBox(height: 8),
            Text(
              metric.label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            if (showComparison && metric.comparison != null) ...[
              const SizedBox(height: 4),
              _buildComparisonIndicator(metric.comparison!, context),
            ],
          ],
        );
      }).toList(),
    );
  }

  /// Builds comparison indicator
  Widget _buildComparisonIndicator(double comparison, BuildContext context) {
    final isPositive = comparison >= 0;
    final color = isPositive ? Colors.green : Colors.red;
    final icon = isPositive ? Icons.trending_up : Icons.trending_down;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 14,
          color: color,
        ),
        const SizedBox(width: 2),
        Text(
          '${comparison.abs().toStringAsFixed(1)}%',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: color,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

/// Accuracy metric data structure
class AccuracyMetric {
  final String label;
  final double value;
  final double? comparison; // Comparison value (e.g., vs previous period)

  const AccuracyMetric({
    required this.label,
    required this.value,
    this.comparison,
  });
}

/// Color scheme for accuracy gauge
class AccuracyGaugeColors {
  final Color excellent;
  final Color good;
  final Color fair;
  final Color poor;
  final Color background;

  const AccuracyGaugeColors({
    required this.excellent,
    required this.good,
    required this.fair,
    required this.poor,
    required this.background,
  });

  /// Default color scheme based on material colors
  factory AccuracyGaugeColors.defaultColors(ColorScheme colorScheme) {
    return AccuracyGaugeColors(
      excellent: const Color(0xFF4CAF50), // Green
      good: const Color(0xFF8BC34A), // Light Green
      fair: const Color(0xFFFF9800), // Orange
      poor: const Color(0xFFF44336), // Red
      background: colorScheme.outline.withValues(alpha: 0.2),
    );
  }

  /// High contrast color scheme
  factory AccuracyGaugeColors.highContrast() {
    return const AccuracyGaugeColors(
      excellent: Color(0xFF2E7D32), // Dark Green
      good: Color(0xFF689F38), // Dark Light Green
      fair: Color(0xFFEF6C00), // Dark Orange
      poor: Color(0xFFC62828), // Dark Red
      background: Color(0xFFBDBDBD), // Grey
    );
  }

  /// Accessible color scheme for color-blind users
  factory AccuracyGaugeColors.accessible() {
    return const AccuracyGaugeColors(
      excellent: Color(0xFF1976D2), // Blue
      good: Color(0xFF388E3C), // Green
      fair: Color(0xFFF57C00), // Orange
      poor: Color(0xFFD32F2F), // Red
      background: Color(0xFFE0E0E0), // Light Grey
    );
  }
}