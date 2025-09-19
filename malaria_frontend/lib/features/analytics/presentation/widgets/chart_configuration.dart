/// Chart configuration and customization options for analytics visualization
///
/// This file provides comprehensive configuration classes and utilities
/// for customizing chart appearance, behavior, and data presentation
/// across all chart widgets in the malaria prediction analytics system.
///
/// Usage:
/// ```dart
/// final config = AnalyticsChartConfig.malariaDashboard();
/// final theme = ChartTheme.fromContext(context);
/// final colors = ColorScheme.environmentalFactors();
/// ```
library;

import 'package:flutter/material.dart';
import '../../domain/entities/analytics_data.dart';

/// Comprehensive chart configuration for analytics visualizations
class AnalyticsChartConfig {
  /// Chart appearance configuration
  final ChartAppearance appearance;

  /// Chart interaction configuration
  final ChartInteraction interaction;

  /// Chart data configuration
  final ChartDataConfig data;

  /// Chart animation configuration
  final ChartAnimation animation;

  /// Chart accessibility configuration
  final ChartAccessibility accessibility;

  const AnalyticsChartConfig({
    required this.appearance,
    required this.interaction,
    required this.data,
    required this.animation,
    required this.accessibility,
  });

  /// Default configuration for malaria dashboard
  factory AnalyticsChartConfig.malariaDashboard({
    Brightness brightness = Brightness.light,
  }) {
    return AnalyticsChartConfig(
      appearance: ChartAppearance.dashboard(brightness: brightness),
      interaction: ChartInteraction.standard(),
      data: ChartDataConfig.defaultConfig(),
      animation: ChartAnimation.smooth(),
      accessibility: ChartAccessibility.standard(),
    );
  }

  /// Configuration for environmental analytics
  factory AnalyticsChartConfig.environmental({
    Brightness brightness = Brightness.light,
  }) {
    return AnalyticsChartConfig(
      appearance: ChartAppearance.environmental(brightness: brightness),
      interaction: ChartInteraction.detailed(),
      data: ChartDataConfig.environmental(),
      animation: ChartAnimation.smooth(),
      accessibility: ChartAccessibility.enhanced(),
    );
  }

  /// Configuration for prediction accuracy analytics
  factory AnalyticsChartConfig.predictionAccuracy({
    Brightness brightness = Brightness.light,
  }) {
    return AnalyticsChartConfig(
      appearance: ChartAppearance.prediction(brightness: brightness),
      interaction: ChartInteraction.minimal(),
      data: ChartDataConfig.prediction(),
      animation: ChartAnimation.fast(),
      accessibility: ChartAccessibility.standard(),
    );
  }

  /// Configuration for risk analysis
  factory AnalyticsChartConfig.riskAnalysis({
    Brightness brightness = Brightness.light,
  }) {
    return AnalyticsChartConfig(
      appearance: ChartAppearance.risk(brightness: brightness),
      interaction: ChartInteraction.standard(),
      data: ChartDataConfig.risk(),
      animation: ChartAnimation.smooth(),
      accessibility: ChartAccessibility.enhanced(),
    );
  }

  /// Creates a copy with updated values
  AnalyticsChartConfig copyWith({
    ChartAppearance? appearance,
    ChartInteraction? interaction,
    ChartDataConfig? data,
    ChartAnimation? animation,
    ChartAccessibility? accessibility,
  }) {
    return AnalyticsChartConfig(
      appearance: appearance ?? this.appearance,
      interaction: interaction ?? this.interaction,
      data: data ?? this.data,
      animation: animation ?? this.animation,
      accessibility: accessibility ?? this.accessibility,
    );
  }
}

/// Chart appearance configuration
class ChartAppearance {
  /// Color scheme for the chart
  final AnalyticsColorScheme colorScheme;

  /// Typography configuration
  final ChartTypography typography;

  /// Grid and border styling
  final ChartStyling styling;

  /// Chart spacing and sizing
  final ChartDimensions dimensions;

  const ChartAppearance({
    required this.colorScheme,
    required this.typography,
    required this.styling,
    required this.dimensions,
  });

  /// Dashboard appearance
  factory ChartAppearance.dashboard({
    Brightness brightness = Brightness.light,
  }) {
    return ChartAppearance(
      colorScheme: AnalyticsColorScheme.dashboard(brightness: brightness),
      typography: const ChartTypography.dashboard(),
      styling: const ChartStyling.dashboard(),
      dimensions: const ChartDimensions.standard(),
    );
  }

  /// Environmental analytics appearance
  factory ChartAppearance.environmental({
    Brightness brightness = Brightness.light,
  }) {
    return ChartAppearance(
      colorScheme: AnalyticsColorScheme.environmental(brightness: brightness),
      typography: const ChartTypography.detailed(),
      styling: const ChartStyling.detailed(),
      dimensions: const ChartDimensions.large(),
    );
  }

  /// Prediction accuracy appearance
  factory ChartAppearance.prediction({
    Brightness brightness = Brightness.light,
  }) {
    return ChartAppearance(
      colorScheme: AnalyticsColorScheme.prediction(brightness: brightness),
      typography: const ChartTypography.compact(),
      styling: const ChartStyling.minimal(),
      dimensions: const ChartDimensions.compact(),
    );
  }

  /// Risk analysis appearance
  factory ChartAppearance.risk({
    Brightness brightness = Brightness.light,
  }) {
    return ChartAppearance(
      colorScheme: AnalyticsColorScheme.risk(brightness: brightness),
      typography: const ChartTypography.standard(),
      styling: const ChartStyling.standard(),
      dimensions: const ChartDimensions.standard(),
    );
  }
}

/// Analytics color scheme configuration
class AnalyticsColorScheme {
  /// Primary colors for main data
  final List<Color> primary;

  /// Secondary colors for supporting data
  final List<Color> secondary;

  /// Environmental factor colors
  final Map<EnvironmentalFactor, Color> environmental;

  /// Risk level colors
  final Map<String, Color> risk;

  /// Alert severity colors
  final Map<String, Color> alert;

  /// Background and surface colors
  final Color background;
  final Color surface;
  final Color onSurface;

  /// Grid and border colors
  final Color gridColor;
  final Color borderColor;

  const AnalyticsColorScheme({
    required this.primary,
    required this.secondary,
    required this.environmental,
    required this.risk,
    required this.alert,
    required this.background,
    required this.surface,
    required this.onSurface,
    required this.gridColor,
    required this.borderColor,
  });

  /// Dashboard color scheme
  factory AnalyticsColorScheme.dashboard({
    Brightness brightness = Brightness.light,
  }) {
    final isDark = brightness == Brightness.dark;

    return AnalyticsColorScheme(
      primary: isDark ? _darkPrimaryColors : _lightPrimaryColors,
      secondary: isDark ? _darkSecondaryColors : _lightSecondaryColors,
      environmental: _environmentalColors,
      risk: _riskColors,
      alert: _alertColors,
      background: isDark ? const Color(0xFF121212) : Colors.white,
      surface: isDark ? const Color(0xFF1E1E1E) : const Color(0xFFF5F5F5),
      onSurface: isDark ? Colors.white : Colors.black,
      gridColor: isDark ? Colors.white.withValues(alpha: 0.1) : Colors.black.withValues(alpha: 0.1),
      borderColor: isDark ? Colors.white.withValues(alpha: 0.2) : Colors.black.withValues(alpha: 0.2),
    );
  }

  /// Environmental analytics color scheme
  factory AnalyticsColorScheme.environmental({
    Brightness brightness = Brightness.light,
  }) {
    final base = AnalyticsColorScheme.dashboard(brightness: brightness);

    return base.copyWith(
      primary: _environmentalPrimaryColors,
      environmental: _enhancedEnvironmentalColors,
    );
  }

  /// Prediction accuracy color scheme
  factory AnalyticsColorScheme.prediction({
    Brightness brightness = Brightness.light,
  }) {
    final base = AnalyticsColorScheme.dashboard(brightness: brightness);

    return base.copyWith(
      primary: _predictionColors,
    );
  }

  /// Risk analysis color scheme
  factory AnalyticsColorScheme.risk({
    Brightness brightness = Brightness.light,
  }) {
    final base = AnalyticsColorScheme.dashboard(brightness: brightness);

    return base.copyWith(
      primary: _riskAnalysisColors,
      risk: _enhancedRiskColors,
    );
  }

  /// Creates a copy with updated values
  AnalyticsColorScheme copyWith({
    List<Color>? primary,
    List<Color>? secondary,
    Map<EnvironmentalFactor, Color>? environmental,
    Map<String, Color>? risk,
    Map<String, Color>? alert,
    Color? background,
    Color? surface,
    Color? onSurface,
    Color? gridColor,
    Color? borderColor,
  }) {
    return AnalyticsColorScheme(
      primary: primary ?? this.primary,
      secondary: secondary ?? this.secondary,
      environmental: environmental ?? this.environmental,
      risk: risk ?? this.risk,
      alert: alert ?? this.alert,
      background: background ?? this.background,
      surface: surface ?? this.surface,
      onSurface: onSurface ?? this.onSurface,
      gridColor: gridColor ?? this.gridColor,
      borderColor: borderColor ?? this.borderColor,
    );
  }

  // Color definitions
  static const _lightPrimaryColors = [
    Color(0xFF2E7D32), // Green
    Color(0xFF1976D2), // Blue
    Color(0xFFD32F2F), // Red
    Color(0xFFF57C00), // Orange
    Color(0xFF7B1FA2), // Purple
    Color(0xFF388E3C), // Light Green
    Color(0xFF1565C0), // Light Blue
    Color(0xFFE53935), // Light Red
  ];

  static const _darkPrimaryColors = [
    Color(0xFF4CAF50), // Light Green
    Color(0xFF2196F3), // Light Blue
    Color(0xFFFF5722), // Deep Orange
    Color(0xFFFF9800), // Orange
    Color(0xFF9C27B0), // Purple
    Color(0xFF8BC34A), // Lime
    Color(0xFF03A9F4), // Light Blue
    Color(0xFFFF6B6B), // Light Red
  ];

  static const _lightSecondaryColors = [
    Color(0xFF81C784), // Light Green
    Color(0xFF64B5F6), // Light Blue
    Color(0xFFE57373), // Light Red
    Color(0xFFFFB74D), // Light Orange
    Color(0xFFBA68C8), // Light Purple
  ];

  static const _darkSecondaryColors = [
    Color(0xFF66BB6A), // Medium Green
    Color(0xFF42A5F5), // Medium Blue
    Color(0xFFEF5350), // Medium Red
    Color(0xFFFF8A65), // Medium Orange
    Color(0xFFAB47BC), // Medium Purple
  ];

  static const _environmentalColors = {
    EnvironmentalFactor.temperature: Color(0xFFD32F2F), // Red
    EnvironmentalFactor.rainfall: Color(0xFF1976D2),    // Blue
    EnvironmentalFactor.humidity: Color(0xFF00BCD4),    // Cyan
    EnvironmentalFactor.vegetation: Color(0xFF4CAF50),  // Green
    EnvironmentalFactor.windSpeed: Color(0xFFFF9800),   // Orange
    EnvironmentalFactor.pressure: Color(0xFF9C27B0),    // Purple
  };

  static const _enhancedEnvironmentalColors = {
    EnvironmentalFactor.temperature: Color(0xFFFF5722), // Deep Orange
    EnvironmentalFactor.rainfall: Color(0xFF2196F3),    // Blue
    EnvironmentalFactor.humidity: Color(0xFF00E5FF),    // Cyan Accent
    EnvironmentalFactor.vegetation: Color(0xFF4CAF50),  // Green
    EnvironmentalFactor.windSpeed: Color(0xFFFF9800),   // Orange
    EnvironmentalFactor.pressure: Color(0xFF673AB7),    // Deep Purple
  };

  static const _riskColors = {
    'low': Color(0xFF4CAF50),      // Green
    'medium': Color(0xFFFF9800),   // Orange
    'high': Color(0xFFFF5722),     // Deep Orange
    'critical': Color(0xFFD32F2F), // Red
  };

  static const _enhancedRiskColors = {
    'low': Color(0xFF8BC34A),      // Light Green
    'medium': Color(0xFFFFB74D),   // Light Orange
    'high': Color(0xFFFF7043),     // Deep Orange
    'critical': Color(0xFFE53935), // Red
  };

  static const _alertColors = {
    'info': Color(0xFF2196F3),     // Blue
    'warning': Color(0xFFFF9800),  // Orange
    'high': Color(0xFFFF5722),     // Deep Orange
    'critical': Color(0xFFD32F2F), // Red
    'emergency': Color(0xFF9C27B0), // Purple
  };

  static const _environmentalPrimaryColors = [
    Color(0xFF4CAF50), // Green (vegetation)
    Color(0xFF2196F3), // Blue (rainfall)
    Color(0xFFFF5722), // Deep Orange (temperature)
    Color(0xFF00BCD4), // Cyan (humidity)
    Color(0xFFFF9800), // Orange (wind)
    Color(0xFF9C27B0), // Purple (pressure)
  ];

  static const _predictionColors = [
    Color(0xFF4CAF50), // Green (high accuracy)
    Color(0xFFFF9800), // Orange (medium accuracy)
    Color(0xFFFF5722), // Deep Orange (low accuracy)
    Color(0xFF2196F3), // Blue (prediction trend)
  ];

  static const _riskAnalysisColors = [
    Color(0xFF4CAF50), // Green (low risk)
    Color(0xFFFFEB3B), // Yellow (medium-low risk)
    Color(0xFFFF9800), // Orange (medium risk)
    Color(0xFFFF5722), // Deep Orange (high risk)
    Color(0xFFD32F2F), // Red (critical risk)
  ];
}

/// Chart typography configuration
class ChartTypography {
  /// Title text style
  final TextStyle title;

  /// Subtitle text style
  final TextStyle subtitle;

  /// Axis label text style
  final TextStyle axisLabel;

  /// Legend text style
  final TextStyle legend;

  /// Tooltip text style
  final TextStyle tooltip;

  /// Value label text style
  final TextStyle valueLabel;

  const ChartTypography({
    required this.title,
    required this.subtitle,
    required this.axisLabel,
    required this.legend,
    required this.tooltip,
    required this.valueLabel,
  });

  /// Dashboard typography
  const ChartTypography.dashboard()
      : title = const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        subtitle = const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        axisLabel = const TextStyle(fontSize: 12),
        legend = const TextStyle(fontSize: 12),
        tooltip = const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        valueLabel = const TextStyle(fontSize: 10, fontWeight: FontWeight.w500);

  /// Detailed typography for complex charts
  const ChartTypography.detailed()
      : title = const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        subtitle = const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
        axisLabel = const TextStyle(fontSize: 14),
        legend = const TextStyle(fontSize: 14),
        tooltip = const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        valueLabel = const TextStyle(fontSize: 12, fontWeight: FontWeight.w500);

  /// Compact typography for small charts
  const ChartTypography.compact()
      : title = const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        subtitle = const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        axisLabel = const TextStyle(fontSize: 10),
        legend = const TextStyle(fontSize: 10),
        tooltip = const TextStyle(fontSize: 10, fontWeight: FontWeight.w500),
        valueLabel = const TextStyle(fontSize: 8, fontWeight: FontWeight.w500);

  /// Standard typography
  const ChartTypography.standard()
      : title = const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        subtitle = const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        axisLabel = const TextStyle(fontSize: 12),
        legend = const TextStyle(fontSize: 12),
        tooltip = const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        valueLabel = const TextStyle(fontSize: 10, fontWeight: FontWeight.w500);
}

/// Chart styling configuration
class ChartStyling {
  /// Grid line configuration
  final GridStyle gridStyle;

  /// Border configuration
  final BorderStyle borderStyle;

  /// Elevation and shadows
  final double elevation;

  /// Border radius
  final double borderRadius;

  /// Padding
  final EdgeInsets padding;

  const ChartStyling({
    required this.gridStyle,
    required this.borderStyle,
    required this.elevation,
    required this.borderRadius,
    required this.padding,
  });

  /// Dashboard styling
  const ChartStyling.dashboard()
      : gridStyle = const GridStyle.subtle(),
        borderStyle = const BorderStyle.standard(),
        elevation = 2,
        borderRadius = 12,
        padding = const EdgeInsets.all(16);

  /// Detailed styling for complex charts
  const ChartStyling.detailed()
      : gridStyle = const GridStyle.detailed(),
        borderStyle = const BorderStyle.prominent(),
        elevation = 4,
        borderRadius = 16,
        padding = const EdgeInsets.all(20);

  /// Minimal styling
  const ChartStyling.minimal()
      : gridStyle = const GridStyle.minimal(),
        borderStyle = const BorderStyle.minimal(),
        elevation = 1,
        borderRadius = 8,
        padding = const EdgeInsets.all(12);

  /// Standard styling
  const ChartStyling.standard()
      : gridStyle = const GridStyle.standard(),
        borderStyle = const BorderStyle.standard(),
        elevation = 2,
        borderRadius = 12,
        padding = const EdgeInsets.all(16);
}

/// Grid style configuration
class GridStyle {
  /// Whether to show horizontal grid lines
  final bool showHorizontal;

  /// Whether to show vertical grid lines
  final bool showVertical;

  /// Grid line width
  final double lineWidth;

  /// Grid line opacity
  final double opacity;

  const GridStyle({
    required this.showHorizontal,
    required this.showVertical,
    required this.lineWidth,
    required this.opacity,
  });

  /// Subtle grid
  const GridStyle.subtle()
      : showHorizontal = true,
        showVertical = false,
        lineWidth = 0.5,
        opacity = 0.3;

  /// Detailed grid
  const GridStyle.detailed()
      : showHorizontal = true,
        showVertical = true,
        lineWidth = 0.5,
        opacity = 0.5;

  /// Minimal grid
  const GridStyle.minimal()
      : showHorizontal = true,
        showVertical = false,
        lineWidth = 0.25,
        opacity = 0.2;

  /// Standard grid
  const GridStyle.standard()
      : showHorizontal = true,
        showVertical = false,
        lineWidth = 0.5,
        opacity = 0.4;
}

/// Border style configuration
class BorderStyle {
  /// Whether to show border
  final bool show;

  /// Border width
  final double width;

  /// Border opacity
  final double opacity;

  const BorderStyle({
    required this.show,
    required this.width,
    required this.opacity,
  });

  /// Standard border
  const BorderStyle.standard()
      : show = true,
        width = 1,
        opacity = 0.5;

  /// Prominent border
  const BorderStyle.prominent()
      : show = true,
        width = 1.5,
        opacity = 0.7;

  /// Minimal border
  const BorderStyle.minimal()
      : show = true,
        width = 0.5,
        opacity = 0.3;
}

/// Chart dimensions configuration
class ChartDimensions {
  /// Default chart height
  final double height;

  /// Default chart width (null for responsive)
  final double? width;

  /// Minimum chart height
  final double minHeight;

  /// Maximum chart height
  final double maxHeight;

  /// Aspect ratio (width/height)
  final double? aspectRatio;

  const ChartDimensions({
    required this.height,
    this.width,
    required this.minHeight,
    required this.maxHeight,
    this.aspectRatio,
  });

  /// Standard dimensions
  const ChartDimensions.standard()
      : height = 300,
        width = null,
        minHeight = 200,
        maxHeight = 600,
        aspectRatio = null;

  /// Large dimensions for detailed charts
  const ChartDimensions.large()
      : height = 400,
        width = null,
        minHeight = 300,
        maxHeight = 800,
        aspectRatio = null;

  /// Compact dimensions for small charts
  const ChartDimensions.compact()
      : height = 200,
        width = null,
        minHeight = 150,
        maxHeight = 300,
        aspectRatio = null;
}

/// Chart interaction configuration
class ChartInteraction {
  /// Whether to enable tooltips
  final bool enableTooltips;

  /// Whether to enable zoom and pan
  final bool enableZoomPan;

  /// Whether to enable selection
  final bool enableSelection;

  /// Whether to enable legend interaction
  final bool enableLegendInteraction;

  /// Touch sensitivity
  final double touchSensitivity;

  const ChartInteraction({
    required this.enableTooltips,
    required this.enableZoomPan,
    required this.enableSelection,
    required this.enableLegendInteraction,
    required this.touchSensitivity,
  });

  /// Standard interaction
  const ChartInteraction.standard()
      : enableTooltips = true,
        enableZoomPan = false,
        enableSelection = true,
        enableLegendInteraction = true,
        touchSensitivity = 1.0;

  /// Detailed interaction for complex charts
  const ChartInteraction.detailed()
      : enableTooltips = true,
        enableZoomPan = true,
        enableSelection = true,
        enableLegendInteraction = true,
        touchSensitivity = 1.0;

  /// Minimal interaction
  const ChartInteraction.minimal()
      : enableTooltips = true,
        enableZoomPan = false,
        enableSelection = false,
        enableLegendInteraction = false,
        touchSensitivity = 1.0;
}

/// Chart data configuration
class ChartDataConfig {
  /// Number format configuration
  final NumberFormat numberFormat;

  /// Date format configuration
  final DateFormat dateFormat;

  /// Data aggregation settings
  final DataAggregation aggregation;

  /// Data filtering settings
  final DataFiltering filtering;

  const ChartDataConfig({
    required this.numberFormat,
    required this.dateFormat,
    required this.aggregation,
    required this.filtering,
  });

  /// Default data configuration
  const ChartDataConfig.defaultConfig()
      : numberFormat = NumberFormat.standard(),
        dateFormat = DateFormat.standard(),
        aggregation = DataAggregation.none(),
        filtering = DataFiltering.none();

  /// Environmental data configuration
  const ChartDataConfig.environmental()
      : numberFormat = NumberFormat.decimal(),
        dateFormat = DateFormat.detailed(),
        aggregation = DataAggregation.daily(),
        filtering = DataFiltering.quality();

  /// Prediction data configuration
  const ChartDataConfig.prediction()
      : numberFormat = NumberFormat.percentage(),
        dateFormat = DateFormat.compact(),
        aggregation = DataAggregation.weekly(),
        filtering = DataFiltering.confidence();

  /// Risk data configuration
  const ChartDataConfig.risk()
      : numberFormat = NumberFormat.risk(),
        dateFormat = DateFormat.standard(),
        aggregation = DataAggregation.regional(),
        filtering = DataFiltering.threshold();
}

/// Number format configuration
class NumberFormat {
  /// Number of decimal places
  final int decimals;

  /// Whether to show units
  final bool showUnits;

  /// Whether to format as percentage
  final bool asPercentage;

  /// Custom unit string
  final String? unit;

  const NumberFormat({
    required this.decimals,
    required this.showUnits,
    required this.asPercentage,
    this.unit,
  });

  /// Standard number format
  const NumberFormat.standard()
      : decimals = 1,
        showUnits = false,
        asPercentage = false,
        unit = null;

  /// Decimal number format
  const NumberFormat.decimal()
      : decimals = 2,
        showUnits = true,
        asPercentage = false,
        unit = null;

  /// Percentage format
  const NumberFormat.percentage()
      : decimals = 1,
        showUnits = false,
        asPercentage = true,
        unit = null;

  /// Risk score format
  const NumberFormat.risk()
      : decimals = 2,
        showUnits = false,
        asPercentage = false,
        unit = null;
}

/// Date format configuration
class DateFormat {
  /// Whether to show time
  final bool showTime;

  /// Whether to use abbreviated format
  final bool abbreviated;

  /// Custom format pattern
  final String? pattern;

  const DateFormat({
    required this.showTime,
    required this.abbreviated,
    this.pattern,
  });

  /// Standard date format
  const DateFormat.standard()
      : showTime = false,
        abbreviated = true,
        pattern = null;

  /// Detailed date format
  const DateFormat.detailed()
      : showTime = true,
        abbreviated = false,
        pattern = null;

  /// Compact date format
  const DateFormat.compact()
      : showTime = false,
        abbreviated = true,
        pattern = 'M/d';
}

/// Data aggregation configuration
class DataAggregation {
  /// Aggregation type
  final AggregationType type;

  /// Time period for aggregation
  final Duration? period;

  const DataAggregation({
    required this.type,
    this.period,
  });

  /// No aggregation
  const DataAggregation.none()
      : type = AggregationType.none,
        period = null;

  /// Daily aggregation
  DataAggregation.daily()
      : type = AggregationType.average,
        period = const Duration(days: 1);

  /// Weekly aggregation
  DataAggregation.weekly()
      : type = AggregationType.average,
        period = const Duration(days: 7);

  /// Regional aggregation
  DataAggregation.regional()
      : type = AggregationType.sum,
        period = null;
}

/// Aggregation types
enum AggregationType {
  none,
  sum,
  average,
  maximum,
  minimum,
  median,
}

/// Data filtering configuration
class DataFiltering {
  /// Filter type
  final FilterType type;

  /// Filter threshold
  final double? threshold;

  /// Filter criteria
  final Map<String, dynamic>? criteria;

  const DataFiltering({
    required this.type,
    this.threshold,
    this.criteria,
  });

  /// No filtering
  DataFiltering.none()
      : type = FilterType.none,
        threshold = null,
        criteria = null;

  /// Quality-based filtering
  DataFiltering.quality()
      : type = FilterType.quality,
        threshold = 0.7,
        criteria = null;

  /// Confidence-based filtering
  DataFiltering.confidence()
      : type = FilterType.confidence,
        threshold = 0.8,
        criteria = null;

  /// Threshold-based filtering
  DataFiltering.threshold()
      : type = FilterType.threshold,
        threshold = 0.5,
        criteria = null;
}

/// Filter types
enum FilterType {
  none,
  quality,
  confidence,
  threshold,
  custom,
}

/// Chart animation configuration
class ChartAnimation {
  /// Animation duration
  final Duration duration;

  /// Animation curve
  final Curve curve;

  /// Whether to enable animations
  final bool enabled;

  const ChartAnimation({
    required this.duration,
    required this.curve,
    required this.enabled,
  });

  /// Smooth animations
  ChartAnimation.smooth()
      : duration = const Duration(milliseconds: 500),
        curve = Curves.easeInOut,
        enabled = true;

  /// Fast animations
  ChartAnimation.fast()
      : duration = const Duration(milliseconds: 200),
        curve = Curves.easeOut,
        enabled = true;

  /// No animations
  ChartAnimation.none()
      : duration = Duration.zero,
        curve = Curves.linear,
        enabled = false;
}

/// Chart accessibility configuration
class ChartAccessibility {
  /// Whether to include semantic labels
  final bool includeSemanticLabels;

  /// Whether to support screen readers
  final bool screenReaderSupport;

  /// High contrast mode
  final bool highContrast;

  /// Font scaling support
  final bool fontScaling;

  const ChartAccessibility({
    required this.includeSemanticLabels,
    required this.screenReaderSupport,
    required this.highContrast,
    required this.fontScaling,
  });

  /// Standard accessibility
  ChartAccessibility.standard()
      : includeSemanticLabels = true,
        screenReaderSupport = true,
        highContrast = false,
        fontScaling = true;

  /// Enhanced accessibility
  ChartAccessibility.enhanced()
      : includeSemanticLabels = true,
        screenReaderSupport = true,
        highContrast = true,
        fontScaling = true;
}