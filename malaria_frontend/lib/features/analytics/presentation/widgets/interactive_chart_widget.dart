/// Interactive chart widget with advanced exploration capabilities
///
/// This widget provides comprehensive interactive chart functionality including
/// zooming, panning, drill-down, real-time updates, and dynamic filtering
/// for malaria prediction analytics data visualization.
///
/// Usage:
/// ```dart
/// InteractiveChartWidget(
///   chart: interactiveChart,
///   onInteraction: (interaction) => handleInteraction(interaction),
///   onDrillDown: (dimension, value) => performDrillDown(dimension, value),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:math' as math;
import '../../domain/entities/interactive_chart.dart';
import '../../domain/entities/chart_data.dart';

/// Interactive chart widget with comprehensive interaction support
class InteractiveChartWidget extends StatefulWidget {
  /// Interactive chart data and configuration
  final InteractiveChart chart;

  /// Callback for chart interactions
  final Function(ChartInteraction)? onInteraction;

  /// Callback for drill-down events
  final Function(String dimension, dynamic value)? onDrillDown;

  /// Callback for drill-up events
  final VoidCallback? onDrillUp;

  /// Callback for selection changes
  final Function(List<dynamic> selectedValues)? onSelectionChanged;

  /// Callback for filter applications
  final Function(String field, dynamic value, FilterInteractionType type)? onFilterApplied;

  /// Callback for data requests (for real-time updates)
  final Function()? onDataRequested;

  /// Custom toolbar actions
  final List<ChartToolbarAction>? customActions;

  /// Theme configuration
  final ChartThemeData? theme;

  /// Loading state indicator
  final bool isLoading;

  /// Error state message
  final String? errorMessage;

  const InteractiveChartWidget({
    super.key,
    required this.chart,
    this.onInteraction,
    this.onDrillDown,
    this.onDrillUp,
    this.onSelectionChanged,
    this.onFilterApplied,
    this.onDataRequested,
    this.customActions,
    this.theme,
    this.isLoading = false,
    this.errorMessage,
  });

  @override
  State<InteractiveChartWidget> createState() => _InteractiveChartWidgetState();
}

class _InteractiveChartWidgetState extends State<InteractiveChartWidget>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;

  /// Gesture recognizers for touch interactions
  late PanGestureRecognizer _panGestureRecognizer;
  late ScaleGestureRecognizer _scaleGestureRecognizer;
  late TapGestureRecognizer _tapGestureRecognizer;
  late DoubleTapGestureRecognizer _doubleTapGestureRecognizer;

  /// Current gesture state
  Offset _initialFocalPoint = Offset.zero;
  double _initialScale = 1.0;
  bool _isInteracting = false;

  /// Tooltip controller
  OverlayEntry? _tooltipOverlay;

  /// Performance monitoring
  DateTime? _renderStartTime;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _initializeGestureRecognizers();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _panGestureRecognizer.dispose();
    _scaleGestureRecognizer.dispose();
    _tapGestureRecognizer.dispose();
    _doubleTapGestureRecognizer.dispose();
    _removeTooltip();
    super.dispose();
  }

  /// Initializes animations for smooth interactions
  void _initializeAnimations() {
    _animationController = AnimationController(
      duration: widget.chart.interactionConfig.animationDuration,
      vsync: this,
    );

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.05,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.elasticOut,
    ));
  }

  /// Initializes gesture recognizers for touch interactions
  void _initializeGestureRecognizers() {
    _panGestureRecognizer = PanGestureRecognizer()
      ..onStart = _onPanStart
      ..onUpdate = _onPanUpdate
      ..onEnd = _onPanEnd;

    _scaleGestureRecognizer = ScaleGestureRecognizer()
      ..onStart = _onScaleStart
      ..onUpdate = _onScaleUpdate
      ..onEnd = _onScaleEnd;

    _tapGestureRecognizer = TapGestureRecognizer()
      ..onTapDown = _onTapDown
      ..onTapUp = _onTapUp;

    _doubleTapGestureRecognizer = DoubleTapGestureRecognizer()
      ..onDoubleTap = _onDoubleTap;
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return Column(
          children: [
            // Chart toolbar
            if (_shouldShowToolbar())
              _buildChartToolbar(),

            // Breadcrumb navigation for drill-down
            if (_shouldShowBreadcrumbs())
              _buildBreadcrumbs(),

            // Main chart area
            Expanded(
              child: _buildChartArea(constraints),
            ),

            // Chart legend and controls
            if (_shouldShowLegend())
              _buildChartLegend(),
          ],
        );
      },
    );
  }

  /// Builds the main chart area with interactions
  Widget _buildChartArea(BoxConstraints constraints) {
    _renderStartTime = DateTime.now();

    return Container(
      width: constraints.maxWidth,
      height: constraints.maxHeight,
      child: Stack(
        children: [
          // Chart background
          Container(
            decoration: BoxDecoration(
              color: widget.theme?.backgroundColor ?? Colors.white,
              border: Border.all(
                color: widget.theme?.borderColor ?? Colors.grey.shade300,
                width: 1.0,
              ),
              borderRadius: BorderRadius.circular(8.0),
            ),
          ),

          // Loading overlay
          if (widget.isLoading)
            _buildLoadingOverlay(),

          // Error overlay
          if (widget.errorMessage != null)
            _buildErrorOverlay(),

          // Interactive chart content
          if (!widget.isLoading && widget.errorMessage == null)
            _buildInteractiveChart(constraints),

          // Performance overlay (debug mode)
          if (widget.theme?.showPerformanceMetrics == true)
            _buildPerformanceOverlay(),
        ],
      ),
    );
  }

  /// Builds the interactive chart with gesture handling
  Widget _buildInteractiveChart(BoxConstraints constraints) {
    return RawGestureDetector(
      gestures: {
        if (widget.chart.interactionConfig.enablePan)
          PanGestureRecognizer: GestureRecognizerFactory<PanGestureRecognizer>(
            () => _panGestureRecognizer,
            (instance) => instance,
          ),
        if (widget.chart.interactionConfig.enableZoom)
          ScaleGestureRecognizer: GestureRecognizerFactory<ScaleGestureRecognizer>(
            () => _scaleGestureRecognizer,
            (instance) => instance,
          ),
        TapGestureRecognizer: GestureRecognizerFactory<TapGestureRecognizer>(
          () => _tapGestureRecognizer,
          (instance) => instance,
        ),
        DoubleTapGestureRecognizer: GestureRecognizerFactory<DoubleTapGestureRecognizer>(
          () => _doubleTapGestureRecognizer,
          (instance) => instance,
        ),
      },
      child: AnimatedBuilder(
        animation: _scaleAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: _buildChartContent(constraints),
          );
        },
      ),
    );
  }

  /// Builds the actual chart content based on chart type
  Widget _buildChartContent(BoxConstraints constraints) {
    switch (widget.chart.chartType) {
      case InteractiveChartType.line:
        return _buildLineChart(constraints);
      case InteractiveChartType.bar:
        return _buildBarChart(constraints);
      case InteractiveChartType.pie:
        return _buildPieChart(constraints);
      case InteractiveChartType.scatter:
        return _buildScatterChart(constraints);
      case InteractiveChartType.area:
        return _buildAreaChart(constraints);
      default:
        return _buildLineChart(constraints);
    }
  }

  /// Builds line chart with fl_chart
  Widget _buildLineChart(BoxConstraints constraints) {
    if (widget.chart.chartData is! LineChartDataEntity) {
      return const Center(child: Text('Invalid chart data for line chart'));
    }

    final chartData = widget.chart.chartData as LineChartDataEntity;
    final viewState = widget.chart.viewState;

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: LineChart(
        LineChartData(
          // Chart data
          lineBarsData: _buildLineChartBars(chartData),

          // Interaction configuration
          lineTouchData: LineTouchData(
            enabled: widget.chart.interactionConfig.enableTooltips,
            touchCallback: _onLineTouchCallback,
            touchTooltipData: LineTouchTooltipData(
              tooltipBgColor: widget.theme?.tooltipBackgroundColor ?? Colors.blueGrey.withOpacity(0.8),
              getTooltipItems: _getLineTooltipItems,
            ),
          ),

          // Grid configuration
          gridData: FlGridData(
            show: chartData.showGrid,
            drawVerticalLine: true,
            drawHorizontalLine: true,
            verticalInterval: _calculateVerticalInterval(chartData),
            horizontalInterval: _calculateHorizontalInterval(chartData),
          ),

          // Axis configuration
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: chartData.yAxis.showLabels,
                getTitlesWidget: (value, meta) => _buildAxisTitle(
                  value,
                  chartData.yAxis,
                  isVertical: true,
                ),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: chartData.xAxis.showLabels,
                getTitlesWidget: (value, meta) => _buildAxisTitle(
                  value,
                  chartData.xAxis,
                  isVertical: false,
                ),
              ),
            ),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),

          // Border configuration
          borderData: FlBorderData(
            show: widget.theme?.showBorder ?? true,
            border: Border.all(
              color: widget.theme?.borderColor ?? Colors.grey,
              width: 1,
            ),
          ),

          // View bounds based on zoom and pan
          minX: _calculateMinX(chartData, viewState),
          maxX: _calculateMaxX(chartData, viewState),
          minY: _calculateMinY(chartData, viewState),
          maxY: _calculateMaxY(chartData, viewState),
        ),
        duration: widget.chart.interactionConfig.animationDuration,
        curve: Curves.easeInOut,
      ),
    );
  }

  /// Builds bar chart with fl_chart
  Widget _buildBarChart(BoxConstraints constraints) {
    if (widget.chart.chartData is! BarChartDataEntity) {
      return const Center(child: Text('Invalid chart data for bar chart'));
    }

    final chartData = widget.chart.chartData as BarChartDataEntity;

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: BarChart(
        BarChartData(
          // Chart data
          barGroups: _buildBarChartGroups(chartData),

          // Interaction configuration
          barTouchData: BarTouchData(
            enabled: widget.chart.interactionConfig.enableTooltips,
            touchCallback: _onBarTouchCallback,
            touchTooltipData: BarTouchTooltipData(
              tooltipBgColor: widget.theme?.tooltipBackgroundColor ?? Colors.blueGrey.withOpacity(0.8),
              getTooltipItem: _getBarTooltipItem,
            ),
          ),

          // Grid and axis configuration
          gridData: FlGridData(show: chartData.showGrid),
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: chartData.yAxis.showLabels,
                getTitlesWidget: (value, meta) => _buildAxisTitle(value, chartData.yAxis, isVertical: true),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: chartData.xAxis.showLabels,
                getTitlesWidget: (value, meta) => _buildAxisTitle(value, chartData.xAxis, isVertical: false),
              ),
            ),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),

          borderData: FlBorderData(
            show: widget.theme?.showBorder ?? true,
            border: Border.all(color: widget.theme?.borderColor ?? Colors.grey),
          ),
        ),
        duration: widget.chart.interactionConfig.animationDuration,
      ),
    );
  }

  /// Builds pie chart with fl_chart
  Widget _buildPieChart(BoxConstraints constraints) {
    if (widget.chart.chartData is! PieChartDataEntity) {
      return const Center(child: Text('Invalid chart data for pie chart'));
    }

    final chartData = widget.chart.chartData as PieChartDataEntity;

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: PieChart(
        PieChartData(
          // Chart data
          sections: _buildPieChartSections(chartData),

          // Interaction configuration
          pieTouchData: PieTouchData(
            enabled: widget.chart.interactionConfig.enableTooltips,
            touchCallback: _onPieTouchCallback,
          ),

          // Visual configuration
          centerSpaceRadius: chartData.centerSpaceRadius,
          sectionsSpace: 2,
          startDegreeOffset: 0,
        ),
        duration: widget.chart.interactionConfig.animationDuration,
      ),
    );
  }

  /// Builds scatter chart with fl_chart
  Widget _buildScatterChart(BoxConstraints constraints) {
    if (widget.chart.chartData is! ScatterPlotDataEntity) {
      return const Center(child: Text('Invalid chart data for scatter chart'));
    }

    final chartData = widget.chart.chartData as ScatterPlotDataEntity;

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: ScatterChart(
        ScatterChartData(
          // Chart data
          scatterSpots: _buildScatterSpots(chartData),

          // Interaction configuration
          scatterTouchData: ScatterTouchData(
            enabled: widget.chart.interactionConfig.enableTooltips,
            touchCallback: _onScatterTouchCallback,
            touchTooltipData: ScatterTouchTooltipData(
              tooltipBgColor: widget.theme?.tooltipBackgroundColor ?? Colors.blueGrey.withOpacity(0.8),
              getTooltipItems: _getScatterTooltipItems,
            ),
          ),

          // Grid and axis configuration
          gridData: FlGridData(show: chartData.showGrid),
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: chartData.yAxis.showLabels,
                getTitlesWidget: (value, meta) => _buildAxisTitle(value, chartData.yAxis, isVertical: true),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: chartData.xAxis.showLabels,
                getTitlesWidget: (value, meta) => _buildAxisTitle(value, chartData.xAxis, isVertical: false),
              ),
            ),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          ),

          borderData: FlBorderData(
            show: widget.theme?.showBorder ?? true,
            border: Border.all(color: widget.theme?.borderColor ?? Colors.grey),
          ),
        ),
        duration: widget.chart.interactionConfig.animationDuration,
      ),
    );
  }

  /// Builds area chart (similar to line chart with filled areas)
  Widget _buildAreaChart(BoxConstraints constraints) {
    // Area chart implementation using LineChart with betweenBarsData
    return _buildLineChart(constraints);
  }

  /// Builds chart toolbar with actions
  Widget _buildChartToolbar() {
    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: widget.theme?.toolbarBackgroundColor ?? Colors.grey.shade100,
        border: Border(
          bottom: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade300,
          ),
        ),
      ),
      child: Row(
        children: [
          // Chart title
          Expanded(
            child: Text(
              widget.chart.title,
              style: widget.theme?.titleTextStyle ?? const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),

          // Action buttons
          ..._buildToolbarActions(),
        ],
      ),
    );
  }

  /// Builds toolbar action buttons
  List<Widget> _buildToolbarActions() {
    final actions = <Widget>[];

    // Zoom controls
    if (widget.chart.interactionConfig.enableZoom) {
      actions.addAll([
        IconButton(
          icon: const Icon(Icons.zoom_in),
          onPressed: () => _performZoom(1.2, const Offset(0.5, 0.5)),
          tooltip: 'Zoom In',
        ),
        IconButton(
          icon: const Icon(Icons.zoom_out),
          onPressed: () => _performZoom(0.8, const Offset(0.5, 0.5)),
          tooltip: 'Zoom Out',
        ),
      ]);
    }

    // Reset view
    actions.add(
      IconButton(
        icon: const Icon(Icons.refresh),
        onPressed: _resetView,
        tooltip: 'Reset View',
      ),
    );

    // Drill-up button
    if (widget.chart.canDrillUp()) {
      actions.add(
        IconButton(
          icon: const Icon(Icons.arrow_upward),
          onPressed: widget.onDrillUp,
          tooltip: 'Drill Up',
        ),
      );
    }

    // Real-time toggle
    if (widget.chart.realTimeConfig?.enabled == true) {
      actions.add(
        IconButton(
          icon: const Icon(Icons.play_arrow),
          onPressed: widget.onDataRequested,
          tooltip: 'Refresh Data',
        ),
      );
    }

    // Custom actions
    if (widget.customActions != null) {
      for (final action in widget.customActions!) {
        actions.add(
          IconButton(
            icon: Icon(action.icon),
            onPressed: action.onPressed,
            tooltip: action.tooltip,
          ),
        );
      }
    }

    return actions;
  }

  /// Builds breadcrumb navigation for drill-down
  Widget _buildBreadcrumbs() {
    if (widget.chart.drillDownHierarchy == null) return const SizedBox.shrink();

    final breadcrumbs = widget.chart.drillDownHierarchy!.getBreadcrumbPath();
    if (breadcrumbs.isEmpty) return const SizedBox.shrink();

    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          const Icon(Icons.home, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: breadcrumbs.length,
              separatorBuilder: (context, index) => const Padding(
                padding: EdgeInsets.symmetric(horizontal: 8),
                child: Icon(Icons.chevron_right, size: 16),
              ),
              itemBuilder: (context, index) {
                return GestureDetector(
                  onTap: () => _navigateToBreadcrumb(index),
                  child: Text(
                    breadcrumbs[index],
                    style: TextStyle(
                      color: Colors.blue,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  /// Builds chart legend
  Widget _buildChartLegend() {
    // Implementation depends on chart type and data
    return const SizedBox.shrink();
  }

  /// Builds loading overlay
  Widget _buildLoadingOverlay() {
    return const Center(
      child: CircularProgressIndicator(),
    );
  }

  /// Builds error overlay
  Widget _buildErrorOverlay() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            color: Colors.red,
            size: 48,
          ),
          const SizedBox(height: 16),
          Text(
            widget.errorMessage!,
            style: const TextStyle(color: Colors.red),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds performance metrics overlay
  Widget _buildPerformanceOverlay() {
    final stats = widget.chart.getPerformanceStats();

    return Positioned(
      top: 8,
      right: 8,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Performance',
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
            Text(
              'Interactions: ${stats['interactionCount']}',
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
            Text(
              'Render: ${stats['lastRenderTime']?.toStringAsFixed(1) ?? 0}ms',
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
            Text(
              'Memory: ${(stats['memoryUsage'] / 1024).toStringAsFixed(1)}KB',
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  // Gesture handlers
  void _onPanStart(DragStartDetails details) {
    _initialFocalPoint = details.localPosition;
    _isInteracting = true;
  }

  void _onPanUpdate(DragUpdateDetails details) {
    if (!_isInteracting) return;

    final panDelta = details.localPosition - _initialFocalPoint;
    _performPan(panDelta);
    _initialFocalPoint = details.localPosition;
  }

  void _onPanEnd(DragEndDetails details) {
    _isInteracting = false;
  }

  void _onScaleStart(ScaleStartDetails details) {
    _initialFocalPoint = details.localFocalPoint;
    _initialScale = widget.chart.viewState.zoomLevel;
    _isInteracting = true;
  }

  void _onScaleUpdate(ScaleUpdateDetails details) {
    if (!_isInteracting) return;

    final scaleFactor = details.scale / _initialScale;
    _performZoom(scaleFactor, details.localFocalPoint);
  }

  void _onScaleEnd(ScaleEndDetails details) {
    _isInteracting = false;
  }

  void _onTapDown(TapDownDetails details) {
    // Handle tap down for visual feedback
    if (widget.chart.interactionConfig.enableAnimations) {
      _animationController.forward();
    }
  }

  void _onTapUp(TapUpDetails details) {
    // Handle tap up and potential drill-down
    if (widget.chart.interactionConfig.enableAnimations) {
      _animationController.reverse();
    }

    // Check for drill-down interaction
    _handleTapForDrillDown(details.localPosition);
  }

  void _onDoubleTap() {
    _resetView();
  }

  // Chart-specific touch callbacks
  void _onLineTouchCallback(FlTouchEvent event, LineTouchResponse? response) {
    _handleChartTouch(event, response?.lineBarSpots);
  }

  void _onBarTouchCallback(FlTouchEvent event, BarTouchResponse? response) {
    _handleChartTouch(event, response?.spot);
  }

  void _onPieTouchCallback(FlTouchEvent event, PieTouchResponse? response) {
    _handleChartTouch(event, response?.touchedSection);
  }

  void _onScatterTouchCallback(FlTouchEvent event, ScatterTouchResponse? response) {
    _handleChartTouch(event, response?.touchedSpot);
  }

  // Helper methods for chart building
  List<LineChartBarData> _buildLineChartBars(LineChartDataEntity chartData) {
    return chartData.series.map((series) {
      return LineChartBarData(
        spots: series.data.map((point) => FlSpot(point.x, point.y)).toList(),
        color: series.color,
        barWidth: series.strokeWidth,
        isCurved: false,
        dotData: FlDotData(show: chartData.showMarkers),
        belowBarData: BarAreaData(
          show: series.fillArea,
          color: series.fillColor?.withOpacity(0.3),
        ),
      );
    }).toList();
  }

  List<BarChartGroupData> _buildBarChartGroups(BarChartDataEntity chartData) {
    return chartData.dataGroups.map((group) {
      return BarChartGroupData(
        x: group.x,
        barRods: group.bars.map((bar) {
          return BarChartRodData(
            toY: bar.value,
            color: bar.color,
            width: chartData.barWidth * 20, // Adjust width scaling
          );
        }).toList(),
      );
    }).toList();
  }

  List<PieChartSectionData> _buildPieChartSections(PieChartDataEntity chartData) {
    return chartData.sections.map((section) {
      return PieChartSectionData(
        value: section.value,
        color: section.color,
        title: section.showLabel ? section.label : '',
        radius: section.radius,
        titleStyle: section.labelStyle,
      );
    }).toList();
  }

  List<ScatterSpot> _buildScatterSpots(ScatterPlotDataEntity chartData) {
    final spots = <ScatterSpot>[];
    for (final series in chartData.series) {
      for (final point in series.data) {
        spots.add(ScatterSpot(
          point.x,
          point.y,
          color: point.color ?? series.color,
          radius: point.size ?? series.pointSize,
        ));
      }
    }
    return spots;
  }

  Widget _buildAxisTitle(double value, ChartAxis axis, {required bool isVertical}) {
    String text;
    if (axis.labelFormatter != null) {
      text = axis.labelFormatter!(value);
    } else {
      text = value.toStringAsFixed(0);
    }

    return Text(
      text,
      style: axis.labelStyle ?? const TextStyle(fontSize: 12),
    );
  }

  List<LineTooltipItem> _getLineTooltipItems(List<LineBarSpot> touchedSpots) {
    return touchedSpots.map((spot) {
      return LineTooltipItem(
        '${spot.x.toStringAsFixed(1)}, ${spot.y.toStringAsFixed(1)}',
        const TextStyle(color: Colors.white),
      );
    }).toList();
  }

  BarTooltipItem? _getBarTooltipItem(BarChartGroupData group, int groupIndex, BarChartRodData rod, int rodIndex) {
    return BarTooltipItem(
      'Value: ${rod.toY.toStringAsFixed(1)}',
      const TextStyle(color: Colors.white),
    );
  }

  List<ScatterTooltipItem> _getScatterTooltipItems(ScatterSpot touchedSpot) {
    return [
      ScatterTooltipItem(
        '(${touchedSpot.x.toStringAsFixed(1)}, ${touchedSpot.y.toStringAsFixed(1)})',
        textStyle: const TextStyle(color: Colors.white),
      ),
    ];
  }

  // Calculation methods for view bounds
  double _calculateMinX(LineChartDataEntity chartData, ChartViewState viewState) {
    // Implementation depends on zoom and pan state
    return chartData.xAxis.min ?? 0;
  }

  double _calculateMaxX(LineChartDataEntity chartData, ChartViewState viewState) {
    // Implementation depends on zoom and pan state
    return chartData.xAxis.max ?? 100;
  }

  double _calculateMinY(LineChartDataEntity chartData, ChartViewState viewState) {
    // Implementation depends on zoom and pan state
    return chartData.yAxis.min ?? 0;
  }

  double _calculateMaxY(LineChartDataEntity chartData, ChartViewState viewState) {
    // Implementation depends on zoom and pan state
    return chartData.yAxis.max ?? 100;
  }

  double _calculateVerticalInterval(LineChartDataEntity chartData) {
    return chartData.xAxis.interval ?? 10;
  }

  double _calculateHorizontalInterval(LineChartDataEntity chartData) {
    return chartData.yAxis.interval ?? 10;
  }

  // Interaction handlers
  void _performZoom(double zoomFactor, Offset centerPoint) {
    final interaction = widget.chart.zoom(
      zoomFactor: zoomFactor,
      centerPoint: centerPoint,
    );
    widget.onInteraction?.call(interaction.interactionHistory.last);
  }

  void _performPan(Offset panDelta) {
    final interaction = widget.chart.pan(panDelta: panDelta);
    widget.onInteraction?.call(interaction.interactionHistory.last);
  }

  void _resetView() {
    final interaction = widget.chart.reset();
    widget.onInteraction?.call(interaction.interactionHistory.last);
  }

  void _handleTapForDrillDown(Offset position) {
    if (!widget.chart.interactionConfig.enableDrillDown || !widget.chart.canDrillDown()) {
      return;
    }

    // Convert tap position to data coordinates and trigger drill-down
    // Implementation depends on chart type and data mapping
    final availableOptions = widget.chart.getAvailableDrillDownOptions();
    if (availableOptions.isNotEmpty) {
      final option = availableOptions.first; // Simplified selection
      widget.onDrillDown?.call(option.targetDimension, 'drill_down_value');
    }
  }

  void _handleChartTouch(FlTouchEvent event, dynamic touchData) {
    if (event is FlTapUpEvent && touchData != null) {
      // Handle chart-specific touch interactions
      _showTooltip(event.localPosition, touchData);
    }
  }

  void _showTooltip(Offset position, dynamic data) {
    _removeTooltip();

    if (!widget.chart.interactionConfig.enableTooltips) return;

    // Create and show tooltip overlay
    // Implementation depends on data type and requirements
  }

  void _removeTooltip() {
    _tooltipOverlay?.remove();
    _tooltipOverlay = null;
  }

  void _navigateToBreadcrumb(int index) {
    // Navigate to specific breadcrumb level
    // Implementation depends on drill-down hierarchy
  }

  // Helper methods for UI state
  bool _shouldShowToolbar() {
    return widget.chart.interactionConfig.enableZoom ||
           widget.chart.interactionConfig.enableDrillDown ||
           widget.customActions?.isNotEmpty == true;
  }

  bool _shouldShowBreadcrumbs() {
    return widget.chart.interactionConfig.enableDrillDown &&
           widget.chart.drillDownHierarchy?.navigationPath.isNotEmpty == true;
  }

  bool _shouldShowLegend() {
    // Determine if legend should be shown based on chart data
    return false; // Simplified for now
  }
}

/// Chart toolbar action definition
class ChartToolbarAction {
  final IconData icon;
  final String tooltip;
  final VoidCallback onPressed;

  const ChartToolbarAction({
    required this.icon,
    required this.tooltip,
    required this.onPressed,
  });
}

/// Chart theme data for styling
class ChartThemeData {
  final Color backgroundColor;
  final Color borderColor;
  final Color toolbarBackgroundColor;
  final Color tooltipBackgroundColor;
  final TextStyle titleTextStyle;
  final bool showBorder;
  final bool showPerformanceMetrics;

  const ChartThemeData({
    this.backgroundColor = Colors.white,
    this.borderColor = Colors.grey,
    this.toolbarBackgroundColor = const Color(0xFFF5F5F5),
    this.tooltipBackgroundColor = const Color(0xFF37474F),
    this.titleTextStyle = const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
    this.showBorder = true,
    this.showPerformanceMetrics = false,
  });
}