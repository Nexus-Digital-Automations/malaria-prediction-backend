/// Pie chart widget for data distribution visualization using fl_chart
///
/// This widget displays distribution data such as risk levels distribution,
/// alert severity breakdown, land cover type distribution, etc.
/// It supports donut charts, multiple pie charts, and interactive segments.
///
/// Usage:
/// ```dart
/// PieChartWidget(
///   title: 'Risk Level Distribution',
///   segments: [
///     PieSegment(
///       label: 'Low Risk',
///       value: 45.0,
///       color: Colors.green,
///     ),
///     PieSegment(
///       label: 'High Risk',
///       value: 15.0,
///       color: Colors.red,
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

/// Data segment for pie chart
class PieSegment {
  /// Display label for this segment
  final String label;

  /// Value for this segment
  final double value;

  /// Color for this segment
  final Color color;

  /// Whether this segment is selected/highlighted
  final bool isSelected;

  /// Custom radius for this segment (null for default)
  final double? radius;

  /// Optional metadata for this segment
  final Map<String, dynamic>? metadata;

  const PieSegment({
    required this.label,
    required this.value,
    required this.color,
    this.isSelected = false,
    this.radius,
    this.metadata,
  });

  /// Creates a copy with updated properties
  PieSegment copyWith({
    String? label,
    double? value,
    Color? color,
    bool? isSelected,
    double? radius,
    Map<String, dynamic>? metadata,
  }) {
    return PieSegment(
      label: label ?? this.label,
      value: value ?? this.value,
      color: color ?? this.color,
      isSelected: isSelected ?? this.isSelected,
      radius: radius ?? this.radius,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Creates pie segment from alert statistics
  factory PieSegment.fromAlertSeverity(
    AlertSeverity severity,
    int count,
    int total,
  ) {
    final percentage = total > 0 ? (count / total) * 100 : 0.0;

    return PieSegment(
      label: _formatSeverityLabel(severity),
      value: percentage,
      color: ChartUtils.getAlertColor(severity.name),
      metadata: {
        'severity': severity,
        'count': count,
        'total': total,
        'percentage': percentage,
      },
    );
  }

  /// Creates pie segment from risk level distribution
  factory PieSegment.fromRiskLevel(
    String riskLevel,
    double percentage,
    int count,
  ) {
    return PieSegment(
      label: _formatRiskLabel(riskLevel),
      value: percentage,
      color: ChartUtils.getRiskColor(riskLevel),
      metadata: {
        'riskLevel': riskLevel,
        'count': count,
        'percentage': percentage,
      },
    );
  }

  /// Creates pie segment from land cover distribution
  factory PieSegment.fromLandCover(
    LandCoverType landCover,
    double percentage,
  ) {
    return PieSegment(
      label: _formatLandCoverLabel(landCover),
      value: percentage,
      color: _getLandCoverColor(landCover),
      metadata: {
        'landCover': landCover,
        'percentage': percentage,
      },
    );
  }

  /// Creates pie segment from data quality sources
  factory PieSegment.fromDataQuality(
    String source,
    double percentage,
    bool hasIssues,
  ) {
    return PieSegment(
      label: source,
      value: percentage,
      color: hasIssues ? Colors.orange : Colors.green,
      metadata: {
        'source': source,
        'percentage': percentage,
        'hasIssues': hasIssues,
      },
    );
  }

  /// Formats severity label
  static String _formatSeverityLabel(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.info:
        return 'Info';
      case AlertSeverity.warning:
        return 'Warning';
      case AlertSeverity.high:
        return 'High';
      case AlertSeverity.critical:
        return 'Critical';
      case AlertSeverity.emergency:
        return 'Emergency';
    }
  }

  /// Formats risk level label
  static String _formatRiskLabel(String riskLevel) {
    return '${riskLevel[0].toUpperCase()}${riskLevel.substring(1)} Risk';
  }

  /// Formats land cover label
  static String _formatLandCoverLabel(LandCoverType landCover) {
    switch (landCover) {
      case LandCoverType.forest:
        return 'Forest';
      case LandCoverType.grassland:
        return 'Grassland';
      case LandCoverType.cropland:
        return 'Cropland';
      case LandCoverType.urban:
        return 'Urban';
      case LandCoverType.water:
        return 'Water';
      case LandCoverType.bareland:
        return 'Bare Land';
      case LandCoverType.wetland:
        return 'Wetland';
    }
  }

  /// Gets color for land cover type
  static Color _getLandCoverColor(LandCoverType landCover) {
    switch (landCover) {
      case LandCoverType.forest:
        return const Color(0xFF2E7D32); // Dark Green
      case LandCoverType.grassland:
        return const Color(0xFF8BC34A); // Light Green
      case LandCoverType.cropland:
        return const Color(0xFFFFEB3B); // Yellow
      case LandCoverType.urban:
        return const Color(0xFF607D8B); // Blue Grey
      case LandCoverType.water:
        return const Color(0xFF2196F3); // Blue
      case LandCoverType.bareland:
        return const Color(0xFF795548); // Brown
      case LandCoverType.wetland:
        return const Color(0xFF009688); // Teal
    }
  }
}

/// Pie chart style configuration
enum PieChartStyle {
  pie,
  donut,
  semiCircle,
}

/// Label position for pie chart segments
enum LabelPosition {
  inside,
  outside,
  none,
}

/// Pie chart widget for data distribution
class PieChartWidget extends StatefulWidget {
  /// Chart title
  final String title;

  /// Chart subtitle
  final String? subtitle;

  /// Pie segments to display
  final List<PieSegment> segments;

  /// Chart height
  final double height;

  /// Chart width (null for responsive)
  final double? width;

  /// Chart style (pie, donut, semi-circle)
  final PieChartStyle style;

  /// Whether to show legend
  final bool showLegend;

  /// Legend position
  final LegendPosition legendPosition;

  /// Label position on segments
  final LabelPosition labelPosition;

  /// Whether to show percentages on labels
  final bool showPercentages;

  /// Whether to show values on labels
  final bool showValues;

  /// Pie chart radius
  final double radius;

  /// Donut inner radius (for donut style)
  final double? innerRadius;

  /// Whether to enable segment selection
  final bool enableSelection;

  /// Whether to animate segment changes
  final bool enableAnimation;

  /// Custom value formatter
  final String Function(double)? valueFormatter;

  /// Custom toolbar actions
  final List<Widget>? toolbarActions;

  /// Callback when segment is tapped
  final void Function(PieSegment)? onSegmentTap;

  /// Constructor requiring segments
  const PieChartWidget({
    super.key,
    required this.title,
    this.subtitle,
    required this.segments,
    this.height = 300,
    this.width,
    this.style = PieChartStyle.pie,
    this.showLegend = true,
    this.legendPosition = LegendPosition.right,
    this.labelPosition = LabelPosition.outside,
    this.showPercentages = true,
    this.showValues = false,
    this.radius = 80,
    this.innerRadius,
    this.enableSelection = true,
    this.enableAnimation = true,
    this.valueFormatter,
    this.toolbarActions,
    this.onSegmentTap,
  });

  @override
  State<PieChartWidget> createState() => _PieChartWidgetState();
}

/// Legend position options
enum LegendPosition {
  top,
  bottom,
  left,
  right,
}

class _PieChartWidgetState extends State<PieChartWidget> {
  /// Currently selected segment index
  int? _selectedSegmentIndex;

  /// Total value of all segments
  late double _totalValue;

  /// Processed segments with calculated percentages
  late List<PieSegment> _processedSegments;

  @override
  void initState() {
    super.initState();
    _processSegments();
  }

  @override
  void didUpdateWidget(PieChartWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.segments != oldWidget.segments) {
      _processSegments();
    }
  }

  /// Processes segments and calculates totals
  void _processSegments() {
    _totalValue = widget.segments.fold(0.0, (sum, segment) => sum + segment.value);

    _processedSegments = widget.segments.asMap().entries.map((entry) {
      final index = entry.key;
      final segment = entry.value;

      return segment.copyWith(
        isSelected: _selectedSegmentIndex == index,
      );
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final hasData = widget.segments.isNotEmpty && _totalValue > 0;

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
      noDataMessage: 'No distribution data available to display',
      toolbarActions: widget.toolbarActions,
      legend: widget.showLegend ? _buildLegend() : null,
      child: _buildChart(),
    );
  }

  /// Builds the main pie chart
  Widget _buildChart() {
    if (_processedSegments.isEmpty || _totalValue == 0) {
      return const SizedBox.shrink();
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final availableWidth = constraints.maxWidth;
        final availableHeight = constraints.maxHeight;

        // Calculate chart size based on available space and legend position
        final chartSize = _calculateChartSize(availableWidth, availableHeight);

        return _buildChartLayout(chartSize);
      },
    );
  }

  /// Calculates optimal chart size
  Size _calculateChartSize(double availableWidth, double availableHeight) {
    double chartWidth = availableWidth;
    double chartHeight = availableHeight;

    if (widget.showLegend) {
      switch (widget.legendPosition) {
        case LegendPosition.left:
        case LegendPosition.right:
          chartWidth = availableWidth * 0.7; // Reserve 30% for legend
          break;
        case LegendPosition.top:
        case LegendPosition.bottom:
          chartHeight = availableHeight * 0.7; // Reserve 30% for legend
          break;
      }
    }

    // Ensure chart is square for best pie chart appearance
    final size = math.min(chartWidth, chartHeight);
    return Size(size, size);
  }

  /// Builds chart layout based on legend position
  Widget _buildChartLayout(Size chartSize) {
    final pieChart = _buildPieChart(chartSize);
    final legend = widget.showLegend ? _buildLegend() : null;

    if (!widget.showLegend || legend == null) {
      return Center(child: pieChart);
    }

    switch (widget.legendPosition) {
      case LegendPosition.top:
        return Column(
          children: [
            legend,
            const SizedBox(height: 16),
            Expanded(child: Center(child: pieChart)),
          ],
        );
      case LegendPosition.bottom:
        return Column(
          children: [
            Expanded(child: Center(child: pieChart)),
            const SizedBox(height: 16),
            legend,
          ],
        );
      case LegendPosition.left:
        return Row(
          children: [
            Expanded(flex: 3, child: legend),
            const SizedBox(width: 16),
            Expanded(flex: 7, child: Center(child: pieChart)),
          ],
        );
      case LegendPosition.right:
        return Row(
          children: [
            Expanded(flex: 7, child: Center(child: pieChart)),
            const SizedBox(width: 16),
            Expanded(flex: 3, child: legend),
          ],
        );
    }
  }

  /// Builds the actual pie chart
  Widget _buildPieChart(Size chartSize) {
    return SizedBox(
      width: chartSize.width,
      height: chartSize.height,
      child: PieChart(
        PieChartData(
          sections: _buildPieSections(),
          centerSpaceRadius: _getCenterSpaceRadius(),
          sectionsSpace: 2,
          startDegreeOffset: widget.style == PieChartStyle.semiCircle ? 180 : 0,
          pieTouchData: _buildPieTouchData(),
        ),
      ),
    );
  }

  /// Gets center space radius based on chart style
  double _getCenterSpaceRadius() {
    switch (widget.style) {
      case PieChartStyle.pie:
        return 0;
      case PieChartStyle.donut:
        return widget.innerRadius ?? widget.radius * 0.4;
      case PieChartStyle.semiCircle:
        return 0;
    }
  }

  /// Builds pie chart sections
  List<PieChartSectionData> _buildPieSections() {
    return _processedSegments.asMap().entries.map((entry) {
      final index = entry.key;
      final segment = entry.value;
      final percentage = _totalValue > 0 ? (segment.value / _totalValue) * 100 : 0;

      // Adjust radius for selection
      final radius = segment.radius ??
          (segment.isSelected ? widget.radius + 10 : widget.radius);

      return PieChartSectionData(
        value: widget.style == PieChartStyle.semiCircle
            ? percentage / 2 // Semi-circle uses half the percentage
            : percentage,
        color: segment.color,
        radius: radius,
        title: _buildSectionTitle(segment, percentage),
        titleStyle: _getSectionTitleStyle(segment),
        titlePositionPercentageOffset: widget.labelPosition == LabelPosition.outside ? 1.3 : 0.5,
        showTitle: widget.labelPosition != LabelPosition.none,
      );
    }).toList();
  }

  /// Builds section title based on label configuration
  String _buildSectionTitle(PieSegment segment, double percentage) {
    final parts = <String>[];

    if (widget.labelPosition == LabelPosition.outside) {
      parts.add(segment.label);
    }

    if (widget.showPercentages) {
      parts.add('${percentage.toStringAsFixed(1)}%');
    }

    if (widget.showValues) {
      final formatted = widget.valueFormatter?.call(segment.value) ??
          ChartUtils.formatValue(segment.value);
      parts.add(formatted);
    }

    return parts.join('\n');
  }

  /// Gets title style for section
  TextStyle _getSectionTitleStyle(PieSegment segment) {
    final baseStyle = Theme.of(context).textTheme.bodySmall ?? const TextStyle();

    return baseStyle.copyWith(
      fontWeight: FontWeight.w500,
      color: widget.labelPosition == LabelPosition.inside
          ? Colors.white
          : Theme.of(context).colorScheme.onSurface,
      fontSize: widget.labelPosition == LabelPosition.inside ? 10 : 12,
    );
  }

  /// Builds touch data configuration
  PieTouchData _buildPieTouchData() {
    return PieTouchData(
      touchCallback: widget.enableSelection
          ? (event, pieTouchResponse) {
              if (event is FlTapUpEvent && pieTouchResponse?.touchedSection != null) {
                final sectionIndex = pieTouchResponse!.touchedSection!.touchedSectionIndex;

                setState(() {
                  _selectedSegmentIndex = _selectedSegmentIndex == sectionIndex
                      ? null
                      : sectionIndex;
                  _processSegments();
                });

                if (widget.onSegmentTap != null && sectionIndex < _processedSegments.length) {
                  widget.onSegmentTap!(_processedSegments[sectionIndex]);
                }
              }
            }
          : null,
      enabled: widget.enableSelection,
    );
  }

  /// Builds legend widget
  Widget _buildLegend() {
    final isHorizontal = widget.legendPosition == LegendPosition.top ||
                        widget.legendPosition == LegendPosition.bottom;

    return Wrap(
      direction: isHorizontal ? Axis.horizontal : Axis.vertical,
      spacing: 16,
      runSpacing: 8,
      children: _processedSegments.asMap().entries.map((entry) {
        final index = entry.key;
        final segment = entry.value;
        final percentage = _totalValue > 0 ? (segment.value / _totalValue) * 100 : 0;

        return InkWell(
          onTap: widget.enableSelection
              ? () {
                  setState(() {
                    _selectedSegmentIndex = _selectedSegmentIndex == index ? null : index;
                    _processSegments();
                  });

                  if (widget.onSegmentTap != null) {
                    widget.onSegmentTap!(segment);
                  }
                }
              : null,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: segment.isSelected
                      ? segment.color
                      : segment.color.withValues(alpha: 0.7),
                  shape: BoxShape.circle,
                  border: segment.isSelected
                      ? Border.all(color: Theme.of(context).colorScheme.primary, width: 2)
                      : null,
                ),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      segment.label,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontWeight: segment.isSelected ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                    Text(
                      '${percentage.toStringAsFixed(1)}% (${widget.valueFormatter?.call(segment.value) ?? ChartUtils.formatValue(segment.value)})',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}