/// Chart data entities for fl_chart visualization components
///
/// This file contains entities specifically designed for data visualization
/// using the fl_chart library for comprehensive analytics dashboard.
///
/// Usage:
/// ```dart
/// final lineChartData = LineChartDataEntity(
///   title: 'Risk Trends',
///   series: [
///     ChartSeries(
///       name: 'Risk Score',
///       data: riskDataPoints,
///       color: AppColors.riskHigh,
///     )
///   ],
/// );
/// ```

import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

/// Line chart data entity for trend visualization
class LineChartDataEntity extends Equatable {
  /// Chart title for display
  final String title;

  /// Chart subtitle for additional context
  final String? subtitle;

  /// List of data series to display on the chart
  final List<ChartSeries> series;

  /// X-axis configuration
  final ChartAxis xAxis;

  /// Y-axis configuration
  final ChartAxis yAxis;

  /// Chart styling configuration
  final ChartStyle style;

  /// Whether to show data point markers
  final bool showMarkers;

  /// Whether to show grid lines
  final bool showGrid;

  /// Whether to enable touch interactions
  final bool enableTouch;

  /// Animation duration in milliseconds
  final int animationDuration;

  const LineChartDataEntity({
    required this.title,
    this.subtitle,
    required this.series,
    required this.xAxis,
    required this.yAxis,
    required this.style,
    this.showMarkers = true,
    this.showGrid = true,
    this.enableTouch = true,
    this.animationDuration = 1000,
  });

  @override
  List<Object?> get props => [
        title,
        subtitle,
        series,
        xAxis,
        yAxis,
        style,
        showMarkers,
        showGrid,
        enableTouch,
        animationDuration,
      ];
}

/// Bar chart data entity for categorical data visualization
class BarChartDataEntity extends Equatable {
  /// Chart title for display
  final String title;

  /// Chart subtitle for additional context
  final String? subtitle;

  /// List of bar data groups
  final List<BarDataGroup> dataGroups;

  /// X-axis configuration
  final ChartAxis xAxis;

  /// Y-axis configuration
  final ChartAxis yAxis;

  /// Chart styling configuration
  final ChartStyle style;

  /// Bar width as percentage of available space (0.0 to 1.0)
  final double barWidth;

  /// Whether to show value labels on bars
  final bool showValueLabels;

  /// Whether to enable touch interactions
  final bool enableTouch;

  /// Animation duration in milliseconds
  final int animationDuration;

  const BarChartDataEntity({
    required this.title,
    this.subtitle,
    required this.dataGroups,
    required this.xAxis,
    required this.yAxis,
    required this.style,
    this.barWidth = 0.8,
    this.showValueLabels = true,
    this.enableTouch = true,
    this.animationDuration = 1000,
  });

  @override
  List<Object?> get props => [
        title,
        subtitle,
        dataGroups,
        xAxis,
        yAxis,
        style,
        barWidth,
        showValueLabels,
        enableTouch,
        animationDuration,
      ];
}

/// Pie chart data entity for proportion visualization
class PieChartDataEntity extends Equatable {
  /// Chart title for display
  final String title;

  /// Chart subtitle for additional context
  final String? subtitle;

  /// List of pie chart sections
  final List<PieSection> sections;

  /// Chart styling configuration
  final ChartStyle style;

  /// Center space radius (0.0 for full pie, >0.0 for donut)
  final double centerSpaceRadius;

  /// Whether to show percentage labels
  final bool showPercentages;

  /// Whether to show value labels
  final bool showValues;

  /// Whether to enable touch interactions
  final bool enableTouch;

  /// Animation duration in milliseconds
  final int animationDuration;

  const PieChartDataEntity({
    required this.title,
    this.subtitle,
    required this.sections,
    required this.style,
    this.centerSpaceRadius = 0.0,
    this.showPercentages = true,
    this.showValues = false,
    this.enableTouch = true,
    this.animationDuration = 1000,
  });

  @override
  List<Object?> get props => [
        title,
        subtitle,
        sections,
        style,
        centerSpaceRadius,
        showPercentages,
        showValues,
        enableTouch,
        animationDuration,
      ];
}

/// Scatter plot data entity for correlation visualization
class ScatterPlotDataEntity extends Equatable {
  /// Chart title for display
  final String title;

  /// Chart subtitle for additional context
  final String? subtitle;

  /// List of scatter plot series
  final List<ScatterSeries> series;

  /// X-axis configuration
  final ChartAxis xAxis;

  /// Y-axis configuration
  final ChartAxis yAxis;

  /// Chart styling configuration
  final ChartStyle style;

  /// Point size for scatter plot markers
  final double pointSize;

  /// Whether to show trend lines
  final bool showTrendLines;

  /// Whether to enable touch interactions
  final bool enableTouch;

  /// Animation duration in milliseconds
  final int animationDuration;

  const ScatterPlotDataEntity({
    required this.title,
    this.subtitle,
    required this.series,
    required this.xAxis,
    required this.yAxis,
    required this.style,
    this.pointSize = 4.0,
    this.showTrendLines = false,
    this.enableTouch = true,
    this.animationDuration = 1000,
  });

  @override
  List<Object?> get props => [
        title,
        subtitle,
        series,
        xAxis,
        yAxis,
        style,
        pointSize,
        showTrendLines,
        enableTouch,
        animationDuration,
      ];
}

/// Chart series entity for line and scatter plots
class ChartSeries extends Equatable {
  /// Series name for legend
  final String name;

  /// Data points in the series
  final List<ChartDataPoint> data;

  /// Series color
  final Color color;

  /// Line thickness for line charts
  final double strokeWidth;

  /// Whether to fill area under line
  final bool fillArea;

  /// Fill color if fillArea is true
  final Color? fillColor;

  /// Line dash pattern (null for solid line)
  final List<int>? dashPattern;

  /// Whether this series is visible
  final bool isVisible;

  const ChartSeries({
    required this.name,
    required this.data,
    required this.color,
    this.strokeWidth = 2.0,
    this.fillArea = false,
    this.fillColor,
    this.dashPattern,
    this.isVisible = true,
  });

  @override
  List<Object?> get props => [
        name,
        data,
        color,
        strokeWidth,
        fillArea,
        fillColor,
        dashPattern,
        isVisible,
      ];
}

/// Scatter plot series entity
class ScatterSeries extends Equatable {
  /// Series name for legend
  final String name;

  /// Data points in the series
  final List<ScatterPoint> data;

  /// Series color
  final Color color;

  /// Point size
  final double pointSize;

  /// Point shape
  final PointShape shape;

  /// Whether this series is visible
  final bool isVisible;

  const ScatterSeries({
    required this.name,
    required this.data,
    required this.color,
    this.pointSize = 4.0,
    this.shape = PointShape.circle,
    this.isVisible = true,
  });

  @override
  List<Object?> get props => [name, data, color, pointSize, shape, isVisible];
}

/// Bar data group for bar charts
class BarDataGroup extends Equatable {
  /// X-axis position
  final int x;

  /// List of bars in this group
  final List<BarDataItem> bars;

  /// Group label
  final String? label;

  const BarDataGroup({
    required this.x,
    required this.bars,
    this.label,
  });

  @override
  List<Object?> get props => [x, bars, label];
}

/// Individual bar data item
class BarDataItem extends Equatable {
  /// Bar value (height)
  final double value;

  /// Bar color
  final Color color;

  /// Bar label
  final String? label;

  /// Tooltip text
  final String? tooltip;

  const BarDataItem({
    required this.value,
    required this.color,
    this.label,
    this.tooltip,
  });

  @override
  List<Object?> get props => [value, color, label, tooltip];
}

/// Pie chart section entity
class PieSection extends Equatable {
  /// Section value
  final double value;

  /// Section color
  final Color color;

  /// Section label
  final String label;

  /// Radius for this section
  final double radius;

  /// Text style for label
  final TextStyle? labelStyle;

  /// Whether to show this section's label
  final bool showLabel;

  /// Badge widget for this section
  final Widget? badge;

  const PieSection({
    required this.value,
    required this.color,
    required this.label,
    this.radius = 60.0,
    this.labelStyle,
    this.showLabel = true,
    this.badge,
  });

  @override
  List<Object?> get props => [value, color, label, radius, labelStyle, showLabel, badge];
}

/// Chart data point for line and area charts
class ChartDataPoint extends Equatable {
  /// X-axis value
  final double x;

  /// Y-axis value
  final double y;

  /// Data point label
  final String? label;

  /// Additional metadata
  final Map<String, dynamic>? metadata;

  const ChartDataPoint({
    required this.x,
    required this.y,
    this.label,
    this.metadata,
  });

  @override
  List<Object?> get props => [x, y, label, metadata];
}

/// Scatter plot point entity
class ScatterPoint extends Equatable {
  /// X-axis value
  final double x;

  /// Y-axis value
  final double y;

  /// Point size (overrides series default if specified)
  final double? size;

  /// Point color (overrides series default if specified)
  final Color? color;

  /// Point label
  final String? label;

  /// Additional metadata
  final Map<String, dynamic>? metadata;

  const ScatterPoint({
    required this.x,
    required this.y,
    this.size,
    this.color,
    this.label,
    this.metadata,
  });

  @override
  List<Object?> get props => [x, y, size, color, label, metadata];
}

/// Chart axis configuration
class ChartAxis extends Equatable {
  /// Axis title
  final String title;

  /// Minimum value
  final double? min;

  /// Maximum value
  final double? max;

  /// Axis label interval
  final double? interval;

  /// Whether to show axis labels
  final bool showLabels;

  /// Whether to show axis title
  final bool showTitle;

  /// Label formatter function
  final String Function(double)? labelFormatter;

  /// Text style for labels
  final TextStyle? labelStyle;

  /// Text style for title
  final TextStyle? titleStyle;

  const ChartAxis({
    required this.title,
    this.min,
    this.max,
    this.interval,
    this.showLabels = true,
    this.showTitle = true,
    this.labelFormatter,
    this.labelStyle,
    this.titleStyle,
  });

  @override
  List<Object?> get props => [
        title,
        min,
        max,
        interval,
        showLabels,
        showTitle,
        labelFormatter,
        labelStyle,
        titleStyle,
      ];
}

/// Chart styling configuration
class ChartStyle extends Equatable {
  /// Background color
  final Color backgroundColor;

  /// Border color
  final Color? borderColor;

  /// Border width
  final double borderWidth;

  /// Grid line color
  final Color gridColor;

  /// Grid line width
  final double gridWidth;

  /// Text theme for chart text
  final TextTheme textTheme;

  /// Whether to show legend
  final bool showLegend;

  /// Legend position
  final LegendPosition legendPosition;

  const ChartStyle({
    this.backgroundColor = Colors.transparent,
    this.borderColor,
    this.borderWidth = 1.0,
    this.gridColor = Colors.grey,
    this.gridWidth = 0.5,
    required this.textTheme,
    this.showLegend = true,
    this.legendPosition = LegendPosition.bottom,
  });

  @override
  List<Object?> get props => [
        backgroundColor,
        borderColor,
        borderWidth,
        gridColor,
        gridWidth,
        textTheme,
        showLegend,
        legendPosition,
      ];
}

/// Point shape enumeration for scatter plots
enum PointShape {
  circle,
  square,
  triangle,
  diamond,
  cross,
}

/// Legend position enumeration
enum LegendPosition {
  top,
  bottom,
  left,
  right,
  topLeft,
  topRight,
  bottomLeft,
  bottomRight,
}