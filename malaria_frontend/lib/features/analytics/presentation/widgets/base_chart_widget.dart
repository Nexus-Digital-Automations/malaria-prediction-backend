/// Base chart widget providing common functionality for fl_chart components
///
/// This widget provides shared chart configuration, styling, and common
/// functionality for all analytics chart widgets in the malaria prediction system.
/// It ensures consistent styling, error handling, and responsive behavior.
///
/// Usage:
/// ```dart
/// BaseChartWidget(
///   title: 'Environmental Trends',
///   height: 400,
///   showLegend: true,
///   child: LineChart(...),
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

/// Configuration class for chart appearance and behavior
class ChartConfiguration {
  /// Chart title
  final String title;

  /// Chart subtitle (optional)
  final String? subtitle;

  /// Chart height
  final double height;

  /// Chart width (null for responsive)
  final double? width;

  /// Whether to show chart legend
  final bool showLegend;

  /// Whether to show chart grid
  final bool showGrid;

  /// Whether to enable touch interactions
  final bool enableTooltips;

  /// Whether to show loading state
  final bool isLoading;

  /// Custom color scheme for the chart
  final List<Color>? colors;

  /// Chart background color
  final Color? backgroundColor;

  /// Chart border radius
  final double borderRadius;

  /// Chart elevation
  final double elevation;

  /// Chart padding
  final EdgeInsets padding;

  /// Animation duration
  final Duration animationDuration;

  /// Whether to show toolbar with export/fullscreen options
  final bool showToolbar;

  const ChartConfiguration({
    required this.title,
    this.subtitle,
    this.height = 300,
    this.width,
    this.showLegend = true,
    this.showGrid = true,
    this.enableTooltips = true,
    this.isLoading = false,
    this.colors,
    this.backgroundColor,
    this.borderRadius = 12,
    this.elevation = 2,
    this.padding = const EdgeInsets.all(16),
    this.animationDuration = const Duration(milliseconds: 300),
    this.showToolbar = false,
  });

  /// Creates a copy with updated values
  ChartConfiguration copyWith({
    String? title,
    String? subtitle,
    double? height,
    double? width,
    bool? showLegend,
    bool? showGrid,
    bool? enableTooltips,
    bool? isLoading,
    List<Color>? colors,
    Color? backgroundColor,
    double? borderRadius,
    double? elevation,
    EdgeInsets? padding,
    Duration? animationDuration,
    bool? showToolbar,
  }) {
    return ChartConfiguration(
      title: title ?? this.title,
      subtitle: subtitle ?? this.subtitle,
      height: height ?? this.height,
      width: width ?? this.width,
      showLegend: showLegend ?? this.showLegend,
      showGrid: showGrid ?? this.showGrid,
      enableTooltips: enableTooltips ?? this.enableTooltips,
      isLoading: isLoading ?? this.isLoading,
      colors: colors ?? this.colors,
      backgroundColor: backgroundColor ?? this.backgroundColor,
      borderRadius: borderRadius ?? this.borderRadius,
      elevation: elevation ?? this.elevation,
      padding: padding ?? this.padding,
      animationDuration: animationDuration ?? this.animationDuration,
      showToolbar: showToolbar ?? this.showToolbar,
    );
  }
}

/// Base chart widget providing common functionality and styling
class BaseChartWidget extends StatefulWidget {
  /// Chart configuration
  final ChartConfiguration configuration;

  /// The main chart widget to display
  final Widget child;

  /// Optional legend widget
  final Widget? legend;

  /// Optional toolbar actions
  final List<Widget>? toolbarActions;

  /// No data message to display when data is empty
  final String? noDataMessage;

  /// Whether the chart has data
  final bool hasData;

  /// Error message to display on error
  final String? errorMessage;

  /// Callback for fullscreen mode
  final VoidCallback? onFullscreen;

  /// Callback for export action
  final VoidCallback? onExport;

  /// Constructor requiring configuration and child chart
  const BaseChartWidget({
    super.key,
    required this.configuration,
    required this.child,
    this.legend,
    this.toolbarActions,
    this.noDataMessage,
    this.hasData = true,
    this.errorMessage,
    this.onFullscreen,
    this.onExport,
  });

  @override
  State<BaseChartWidget> createState() => _BaseChartWidgetState();
}

class _BaseChartWidgetState extends State<BaseChartWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: widget.configuration.animationDuration,
      vsync: this,
    );
    _fadeAnimation = Tween<double>(
      begin: 0,
      end: 1,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: Card(
        elevation: widget.configuration.elevation,
        color: widget.configuration.backgroundColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(widget.configuration.borderRadius),
        ),
        child: Container(
          height: widget.configuration.height,
          width: widget.configuration.width,
          padding: widget.configuration.padding,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(),
              const SizedBox(height: 16),
              Expanded(
                child: _buildContent(),
              ),
              if (widget.configuration.showLegend && widget.legend != null) ...[
                const SizedBox(height: 16),
                widget.legend!,
              ],
            ],
          ),
        ),
      ),
    );
  }

  /// Builds the chart header with title and toolbar
  Widget _buildHeader() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.configuration.title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (widget.configuration.subtitle != null) ...[
                const SizedBox(height: 4),
                Text(
                  widget.configuration.subtitle!,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
              ],
            ],
          ),
        ),
        if (widget.configuration.showToolbar || widget.toolbarActions != null)
          _buildToolbar(),
      ],
    );
  }

  /// Builds the toolbar with action buttons
  Widget _buildToolbar() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.toolbarActions != null) ...widget.toolbarActions!,
        if (widget.configuration.showToolbar) ...[
          IconButton(
            icon: const Icon(Icons.download_outlined),
            tooltip: 'Export Chart',
            onPressed: widget.onExport,
            iconSize: 20,
          ),
          IconButton(
            icon: const Icon(Icons.fullscreen_outlined),
            tooltip: 'Fullscreen',
            onPressed: widget.onFullscreen,
            iconSize: 20,
          ),
        ],
      ],
    );
  }

  /// Builds the main content area
  Widget _buildContent() {
    if (widget.configuration.isLoading) {
      return _buildLoadingWidget();
    }

    if (widget.errorMessage != null) {
      return _buildErrorWidget();
    }

    if (!widget.hasData) {
      return _buildNoDataWidget();
    }

    return widget.child;
  }

  /// Builds loading indicator
  Widget _buildLoadingWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'Loading chart data...',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds error state widget
  Widget _buildErrorWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline,
            size: 48,
            color: Theme.of(context).colorScheme.error,
          ),
          const SizedBox(height: 16),
          Text(
            'Chart Error',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.error,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            widget.errorMessage!,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds no data state widget
  Widget _buildNoDataWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.analytics_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No Data Available',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            widget.noDataMessage ?? 'No data to display in this chart',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

/// Common chart utilities and helper functions
class ChartUtils {
  /// Default color palette for charts
  static const List<Color> defaultColors = [
    Color(0xFF2E7D32), // Green
    Color(0xFF1976D2), // Blue
    Color(0xFFD32F2F), // Red
    Color(0xFFF57C00), // Orange
    Color(0xFF7B1FA2), // Purple
    Color(0xFF388E3C), // Light Green
    Color(0xFF1565C0), // Light Blue
    Color(0xFFE53935), // Light Red
    Color(0xFFFF9800), // Amber
    Color(0xFF9C27B0), // Light Purple
  ];

  /// Environmental factor color mapping
  static const Map<String, Color> environmentalColors = {
    'temperature': Color(0xFFD32F2F), // Red
    'rainfall': Color(0xFF1976D2),    // Blue
    'humidity': Color(0xFF00BCD4),    // Cyan
    'vegetation': Color(0xFF4CAF50),  // Green
    'windSpeed': Color(0xFFFF9800),   // Orange
    'pressure': Color(0xFF9C27B0),    // Purple
  };

  /// Risk level color mapping
  static const Map<String, Color> riskColors = {
    'low': Color(0xFF4CAF50),      // Green
    'medium': Color(0xFFFF9800),   // Orange
    'high': Color(0xFFFF5722),     // Deep Orange
    'critical': Color(0xFFD32F2F), // Red
  };

  /// Alert severity color mapping
  static const Map<String, Color> alertColors = {
    'info': Color(0xFF2196F3),     // Blue
    'warning': Color(0xFFFF9800),  // Orange
    'high': Color(0xFFFF5722),     // Deep Orange
    'critical': Color(0xFFD32F2F), // Red
    'emergency': Color(0xFF9C27B0), // Purple
  };

  /// Gets color for environmental factor
  static Color getEnvironmentalColor(String factor, [int index = 0]) {
    return environmentalColors[factor.toLowerCase()] ??
           defaultColors[index % defaultColors.length];
  }

  /// Gets color for risk level
  static Color getRiskColor(String riskLevel) {
    return riskColors[riskLevel.toLowerCase()] ?? defaultColors[0];
  }

  /// Gets color for alert severity
  static Color getAlertColor(String severity) {
    return alertColors[severity.toLowerCase()] ?? defaultColors[0];
  }

  /// Creates gradient for charts
  static LinearGradient createGradient(Color color, {double opacity = 0.3}) {
    return LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [
        color.withValues(alpha: opacity),
        color.withValues(alpha: 0.1),
      ],
    );
  }

  /// Creates standard grid data configuration
  static FlGridData createGridData(BuildContext context, {
    bool showVertical = true,
    bool showHorizontal = true,
  }) {
    return FlGridData(
      show: true,
      drawVerticalLine: showVertical,
      drawHorizontalLine: showHorizontal,
      getDrawingHorizontalLine: (value) => FlLine(
        color: Theme.of(context).dividerColor,
        strokeWidth: 0.5,
      ),
      getDrawingVerticalLine: (value) => FlLine(
        color: Theme.of(context).dividerColor,
        strokeWidth: 0.5,
      ),
    );
  }

  /// Creates standard border data configuration
  static FlBorderData createBorderData(BuildContext context) {
    return FlBorderData(
      show: true,
      border: Border.all(
        color: Theme.of(context).dividerColor,
        width: 1,
      ),
    );
  }

  /// Formats value for display
  static String formatValue(double value, {
    int decimals = 1,
    String unit = '',
    bool isPercentage = false,
  }) {
    if (isPercentage) {
      return '${(value * 100).toStringAsFixed(decimals)}%';
    }
    return '${value.toStringAsFixed(decimals)}$unit';
  }

  /// Formats date for axis labels
  static String formatDate(DateTime date, {
    bool showTime = false,
    bool abbreviated = true,
  }) {
    if (showTime) {
      return '${date.month}/${date.day} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
    }

    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    if (abbreviated) {
      return '${months[date.month - 1]} ${date.day}';
    }

    return '${date.month}/${date.day}/${date.year}';
  }

  /// Calculates appropriate Y-axis range
  static (double min, double max) calculateYRange(
    List<double> values, {
    double padding = 0.1,
  }) {
    if (values.isEmpty) return (0, 1);

    final min = values.reduce((a, b) => a < b ? a : b);
    final max = values.reduce((a, b) => a > b ? a : b);
    final range = max - min;
    final paddingAmount = range * padding;

    return (
      (min - paddingAmount).clamp(0, double.infinity),
      max + paddingAmount,
    );
  }

  /// Creates responsive font size based on chart size
  static double getResponsiveFontSize(double chartHeight) {
    if (chartHeight < 200) return 10;
    if (chartHeight < 300) return 12;
    if (chartHeight < 400) return 14;
    return 16;
  }
}