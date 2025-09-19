/// Cross Filter Chart widget for linked data visualization
///
/// This widget provides comprehensive cross-filtering capabilities where
/// selections in one chart dynamically filter data in all other charts,
/// enabling powerful multi-dimensional data exploration for malaria prediction analytics.
///
/// Usage:
/// ```dart
/// CrossFilterChartWidget(
///   charts: interactiveCharts,
///   onCrossFilter: (criteria) => applyCrossFilter(criteria),
///   onChartInteraction: (interaction) => handleInteraction(interaction),
/// )
/// ```
library;

import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import '../../domain/entities/interactive_chart.dart';
import '../../domain/entities/chart_data.dart';
import 'interactive_chart_widget.dart';

/// Cross-filtering chart grid with linked visualizations
class CrossFilterChartWidget extends StatefulWidget {
  /// List of interactive charts for cross-filtering
  final List<InteractiveChart> charts;

  /// Callback for cross-filter operations
  final Function(Map<String, dynamic>)? onCrossFilter;

  /// Callback for individual chart interactions
  final Function(ChartInteraction)? onChartInteraction;

  /// Theme configuration
  final CrossFilterThemeData? theme;

  /// Grid layout configuration
  final CrossFilterLayoutConfig? layoutConfig;

  /// Whether to show connection lines between charts
  final bool showConnections;

  /// Whether to enable brush selection across charts
  final bool enableBrushSelection;

  /// Whether to enable chart linking
  final bool enableChartLinking;

  /// Maximum number of charts to display
  final int maxCharts;

  /// Whether to show filter summary
  final bool showFilterSummary;

  const CrossFilterChartWidget({
    super.key,
    required this.charts,
    this.onCrossFilter,
    this.onChartInteraction,
    this.theme,
    this.layoutConfig,
    this.showConnections = true,
    this.enableBrushSelection = true,
    this.enableChartLinking = true,
    this.maxCharts = 12,
    this.showFilterSummary = true,
  });

  @override
  State<CrossFilterChartWidget> createState() => _CrossFilterChartWidgetState();
}

class _CrossFilterChartWidgetState extends State<CrossFilterChartWidget>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _connectionAnimation;

  /// Currently active cross-filters
  Map<String, dynamic> _activeCrossFilters = {};

  /// Selected chart for brush operations
  String? _selectedChartForBrush;

  /// Brush selection coordinates
  Rect? _brushSelection;

  /// Chart connections for visual linking
  List<ChartConnection> _chartConnections = [];

  /// Hover states for charts
  Map<String, bool> _chartHoverStates = {};

  /// Chart layout positions
  Map<String, Rect> _chartPositions = {};

  /// Performance metrics for cross-filtering
  Map<String, int> _filterPerformanceMetrics = {};

  /// Last filter application timestamp
  DateTime _lastFilterTime = DateTime.now();

  /// Filter debounce timer
  Timer? _filterDebounceTimer;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _initializeChartConnections();
    _initializePerformanceMetrics();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _filterDebounceTimer?.cancel();
    super.dispose();
  }

  void _initializeAnimations() {
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );

    _connectionAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _animationController.forward();
  }

  void _initializeChartConnections() {
    _chartConnections = _generateChartConnections();
  }

  void _initializePerformanceMetrics() {
    for (final chart in widget.charts) {
      _filterPerformanceMetrics[chart.chartId] = 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return Container(
          width: constraints.maxWidth,
          height: constraints.maxHeight,
          child: Stack(
            children: [
              // Main chart grid
              _buildChartGrid(constraints),

              // Cross-filter connections overlay
              if (widget.showConnections)
                _buildConnectionsOverlay(constraints),

              // Filter summary overlay
              if (widget.showFilterSummary && _activeCrossFilters.isNotEmpty)
                _buildFilterSummaryOverlay(),

              // Brush selection overlay
              if (_brushSelection != null)
                _buildBrushSelectionOverlay(),
            ],
          ),
        );
      },
    );
  }

  Widget _buildChartGrid(BoxConstraints constraints) {
    final layoutConfig = widget.layoutConfig ?? CrossFilterLayoutConfig.adaptive();
    final gridColumns = _calculateGridColumns(constraints.maxWidth, widget.charts.length);
    final gridRows = (widget.charts.length / gridColumns).ceil();

    return CustomScrollView(
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.all(16),
          sliver: SliverGrid(
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: gridColumns,
              childAspectRatio: layoutConfig.chartAspectRatio,
              crossAxisSpacing: layoutConfig.chartSpacing,
              mainAxisSpacing: layoutConfig.chartSpacing,
            ),
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                if (index >= widget.charts.length) return null;
                return _buildCrossFilterChart(widget.charts[index], index, constraints);
              },
              childCount: widget.charts.length,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCrossFilterChart(InteractiveChart chart, int index, BoxConstraints constraints) {
    final isHovered = _chartHoverStates[chart.chartId] ?? false;
    final hasActiveFilter = _activeCrossFilters.containsKey(chart.chartId);

    return MouseRegion(
      onEnter: (_) => _onChartHover(chart.chartId, true),
      onExit: (_) => _onChartHover(chart.chartId, false),
      child: GestureDetector(
        onTapDown: (details) => _onChartTapDown(chart, details),
        onPanStart: widget.enableBrushSelection ? (details) => _onBrushStart(chart, details) : null,
        onPanUpdate: widget.enableBrushSelection ? (details) => _onBrushUpdate(chart, details) : null,
        onPanEnd: widget.enableBrushSelection ? (details) => _onBrushEnd(chart, details) : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          decoration: BoxDecoration(
            border: Border.all(
              color: hasActiveFilter
                  ? widget.theme?.activeFilterBorderColor ?? Colors.blue
                  : isHovered
                      ? widget.theme?.hoverBorderColor ?? Colors.grey.shade400
                      : widget.theme?.defaultBorderColor ?? Colors.grey.shade300,
              width: hasActiveFilter ? 2.0 : 1.0,
            ),
            borderRadius: BorderRadius.circular(8),
            boxShadow: isHovered || hasActiveFilter
                ? [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.1),
                      blurRadius: 8,
                      offset: const Offset(0, 4),
                    ),
                  ]
                : null,
          ),
          child: Column(
            children: [
              // Chart header with cross-filter controls
              _buildChartHeader(chart, hasActiveFilter),

              // Interactive chart content
              Expanded(
                child: _buildChartContent(chart, index),
              ),

              // Chart footer with filter status
              if (hasActiveFilter)
                _buildChartFooter(chart),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChartHeader(InteractiveChart chart, bool hasActiveFilter) {
    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: hasActiveFilter
            ? widget.theme?.activeFilterHeaderColor ?? Colors.blue.shade50
            : widget.theme?.chartHeaderColor ?? Colors.grey.shade50,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(8),
          topRight: Radius.circular(8),
        ),
        border: Border(
          bottom: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade200,
          ),
        ),
      ),
      child: Row(
        children: [
          // Chart title
          Expanded(
            child: Text(
              chart.title,
              style: widget.theme?.chartTitleStyle ?? const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),

          // Cross-filter indicator
          if (hasActiveFilter)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              decoration: BoxDecoration(
                color: widget.theme?.filterIndicatorColor ?? Colors.blue,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.filter_alt,
                size: 12,
                color: Colors.white,
              ),
            ),

          const SizedBox(width: 4),

          // Chart controls
          PopupMenuButton<String>(
            icon: Icon(
              Icons.more_vert,
              size: 14,
              color: widget.theme?.iconColor ?? Colors.grey.shade600,
            ),
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'clear_filter',
                enabled: hasActiveFilter,
                child: const Row(
                  children: [
                    Icon(Icons.clear, size: 12),
                    SizedBox(width: 6),
                    Text('Clear Filter', style: TextStyle(fontSize: 11)),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'isolate',
                child: Row(
                  children: [
                    Icon(Icons.center_focus_strong, size: 12),
                    SizedBox(width: 6),
                    Text('Isolate Chart', style: TextStyle(fontSize: 11)),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'export',
                child: Row(
                  children: [
                    Icon(Icons.download, size: 12),
                    SizedBox(width: 6),
                    Text('Export Chart', style: TextStyle(fontSize: 11)),
                  ],
                ),
              ),
            ],
            onSelected: (action) => _handleChartMenuAction(chart, action),
          ),
        ],
      ),
    );
  }

  Widget _buildChartContent(InteractiveChart chart, int index) {
    // Apply cross-filters to chart data
    final filteredChart = _applyFiltersToChart(chart);

    return InteractiveChartWidget(
      chart: filteredChart,
      onInteraction: (interaction) => _handleChartInteraction(chart, interaction),
      onSelectionChanged: (selectedValues) => _handleChartSelection(chart, selectedValues),
      onFilterApplied: (field, value, type) => _handleChartFilter(chart, field, value, type),
      theme: widget.theme?.chartTheme,
      isLoading: false,
    );
  }

  Widget _buildChartFooter(InteractiveChart chart) {
    final filterInfo = _activeCrossFilters[chart.chartId];
    if (filterInfo == null) return const SizedBox.shrink();

    return Container(
      height: 24,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: widget.theme?.chartFooterColor ?? Colors.blue.shade50,
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(8),
          bottomRight: Radius.circular(8),
        ),
        border: Border(
          top: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade200,
          ),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.filter_alt,
            size: 10,
            color: widget.theme?.filterIndicatorColor ?? Colors.blue,
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Text(
              _getFilterDescription(filterInfo),
              style: widget.theme?.filterDescriptionStyle ?? const TextStyle(
                fontSize: 9,
                color: Colors.blue,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          GestureDetector(
            onTap: () => _clearChartFilter(chart.chartId),
            child: Icon(
              Icons.close,
              size: 10,
              color: widget.theme?.filterIndicatorColor ?? Colors.blue,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConnectionsOverlay(BoxConstraints constraints) {
    if (!widget.enableChartLinking || _chartConnections.isEmpty) {
      return const SizedBox.shrink();
    }

    return AnimatedBuilder(
      animation: _connectionAnimation,
      builder: (context, child) {
        return CustomPaint(
          painter: ChartConnectionsPainter(
            connections: _chartConnections,
            chartPositions: _chartPositions,
            animationValue: _connectionAnimation.value,
            theme: widget.theme,
          ),
          size: Size(constraints.maxWidth, constraints.maxHeight),
        );
      },
    );
  }

  Widget _buildFilterSummaryOverlay() {
    return Positioned(
      top: 16,
      right: 16,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 300),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: widget.theme?.filterSummaryBackgroundColor ?? Colors.white,
          border: Border.all(
            color: widget.theme?.borderColor ?? Colors.grey.shade300,
          ),
          borderRadius: BorderRadius.circular(8),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Icon(
                  Icons.filter_list,
                  size: 16,
                  color: widget.theme?.primaryColor ?? Colors.blue,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Active Filters (${_activeCrossFilters.length})',
                    style: widget.theme?.filterSummaryHeaderStyle ?? const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.clear_all, size: 14),
                  onPressed: _clearAllFilters,
                  tooltip: 'Clear All Filters',
                ),
              ],
            ),
            const SizedBox(height: 8),
            ..._activeCrossFilters.entries.map((entry) {
              return Container(
                margin: const EdgeInsets.only(bottom: 4),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: widget.theme?.filterSummaryItemColor ?? Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${_getChartTitle(entry.key)}: ${_getFilterDescription(entry.value)}',
                        style: const TextStyle(fontSize: 10),
                      ),
                    ),
                    GestureDetector(
                      onTap: () => _clearChartFilter(entry.key),
                      child: Icon(
                        Icons.close,
                        size: 12,
                        color: widget.theme?.primaryColor ?? Colors.blue,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildBrushSelectionOverlay() {
    return Positioned.fromRect(
      rect: _brushSelection!,
      child: Container(
        decoration: BoxDecoration(
          color: widget.theme?.brushSelectionColor?.withOpacity(0.3) ?? Colors.blue.withOpacity(0.3),
          border: Border.all(
            color: widget.theme?.brushSelectionColor ?? Colors.blue,
            width: 1,
          ),
        ),
      ),
    );
  }

  // Event handlers

  void _onChartHover(String chartId, bool isHovered) {
    setState(() {
      _chartHoverStates[chartId] = isHovered;
    });

    if (widget.enableChartLinking) {
      _highlightConnectedCharts(chartId, isHovered);
    }
  }

  void _onChartTapDown(InteractiveChart chart, TapDownDetails details) {
    // Handle chart selection for cross-filtering
    _selectedChartForBrush = chart.chartId;
  }

  void _onBrushStart(InteractiveChart chart, DragStartDetails details) {
    if (!widget.enableBrushSelection) return;

    setState(() {
      _selectedChartForBrush = chart.chartId;
      _brushSelection = Rect.fromLTWH(
        details.localPosition.dx,
        details.localPosition.dy,
        0,
        0,
      );
    });
  }

  void _onBrushUpdate(InteractiveChart chart, DragUpdateDetails details) {
    if (!widget.enableBrushSelection || _brushSelection == null) return;

    setState(() {
      _brushSelection = Rect.fromLTRB(
        _brushSelection!.left,
        _brushSelection!.top,
        details.localPosition.dx,
        details.localPosition.dy,
      );
    });
  }

  void _onBrushEnd(InteractiveChart chart, DragEndDetails details) {
    if (!widget.enableBrushSelection || _brushSelection == null) return;

    // Apply brush selection as cross-filter
    final filterCriteria = _convertBrushToFilter(chart, _brushSelection!);
    _applyCrossFilter(chart.chartId, filterCriteria);

    setState(() {
      _brushSelection = null;
      _selectedChartForBrush = null;
    });
  }

  void _handleChartInteraction(InteractiveChart chart, ChartInteraction interaction) {
    // Forward interaction to parent
    widget.onChartInteraction?.call(interaction);

    // Handle cross-filtering based on interaction type
    if (interaction.type == InteractionType.select) {
      final selectedValues = interaction.parameters['selectedValues'] as List<dynamic>?;
      if (selectedValues != null && selectedValues.isNotEmpty) {
        _applyCrossFilter(chart.chartId, {
          'type': 'selection',
          'values': selectedValues,
          'field': _getPrimaryDataField(chart),
        });
      }
    }
  }

  void _handleChartSelection(InteractiveChart chart, List<dynamic> selectedValues) {
    if (selectedValues.isNotEmpty) {
      _applyCrossFilter(chart.chartId, {
        'type': 'selection',
        'values': selectedValues,
        'field': _getPrimaryDataField(chart),
      });
    } else {
      _clearChartFilter(chart.chartId);
    }
  }

  void _handleChartFilter(InteractiveChart chart, String field, dynamic value, FilterInteractionType type) {
    switch (type) {
      case FilterInteractionType.add:
        _applyCrossFilter(chart.chartId, {
          'type': 'filter',
          'field': field,
          'value': value,
          'operation': 'equals',
        });
        break;
      case FilterInteractionType.remove:
        _clearChartFilter(chart.chartId);
        break;
      case FilterInteractionType.replace:
        _clearAllFilters();
        _applyCrossFilter(chart.chartId, {
          'type': 'filter',
          'field': field,
          'value': value,
          'operation': 'equals',
        });
        break;
    }
  }

  void _handleChartMenuAction(InteractiveChart chart, String action) {
    switch (action) {
      case 'clear_filter':
        _clearChartFilter(chart.chartId);
        break;
      case 'isolate':
        _isolateChart(chart);
        break;
      case 'export':
        _exportChart(chart);
        break;
    }
  }

  void _applyCrossFilter(String sourceChartId, Map<String, dynamic> filterCriteria) {
    // Cancel any pending filter operations
    _filterDebounceTimer?.cancel();

    // Debounce filter application for performance
    _filterDebounceTimer = Timer(const Duration(milliseconds: 200), () {
      setState(() {
        _activeCrossFilters[sourceChartId] = filterCriteria;
        _lastFilterTime = DateTime.now();
        _filterPerformanceMetrics[sourceChartId] =
            (_filterPerformanceMetrics[sourceChartId] ?? 0) + 1;
      });

      // Notify parent of cross-filter change
      widget.onCrossFilter?.call(_activeCrossFilters);

      // Update chart connections
      _updateChartConnections();
    });
  }

  void _clearChartFilter(String chartId) {
    setState(() {
      _activeCrossFilters.remove(chartId);
    });

    widget.onCrossFilter?.call(_activeCrossFilters);
    _updateChartConnections();
  }

  void _clearAllFilters() {
    setState(() {
      _activeCrossFilters.clear();
    });

    widget.onCrossFilter?.call(_activeCrossFilters);
    _updateChartConnections();
  }

  void _isolateChart(InteractiveChart chart) {
    // Clear all other filters and focus on this chart
    _clearAllFilters();
    // Implement chart isolation logic
  }

  void _exportChart(InteractiveChart chart) {
    // Implement chart export functionality
  }

  void _highlightConnectedCharts(String chartId, bool highlight) {
    // Update visual connections between charts
    if (highlight) {
      _animationController.forward();
    }
  }

  void _updateChartConnections() {
    setState(() {
      _chartConnections = _generateChartConnections();
    });
  }

  // Helper methods

  int _calculateGridColumns(double width, int chartCount) {
    if (width < 600) return 1;
    if (width < 900) return 2;
    if (width < 1200) return 3;
    return math.min(4, chartCount);
  }

  List<ChartConnection> _generateChartConnections() {
    final connections = <ChartConnection>[];

    // Generate connections based on active cross-filters
    for (final entry in _activeCrossFilters.entries) {
      final sourceChartId = entry.key;
      final filterCriteria = entry.value;

      // Find charts that share data fields
      for (final chart in widget.charts) {
        if (chart.chartId != sourceChartId && _chartsShareData(sourceChartId, chart.chartId)) {
          connections.add(ChartConnection(
            sourceChartId: sourceChartId,
            targetChartId: chart.chartId,
            connectionType: ConnectionType.filter,
            strength: _calculateConnectionStrength(filterCriteria),
          ));
        }
      }
    }

    return connections;
  }

  bool _chartsShareData(String chartId1, String chartId2) {
    // Determine if charts share common data fields
    final chart1 = widget.charts.firstWhere((c) => c.chartId == chartId1);
    final chart2 = widget.charts.firstWhere((c) => c.chartId == chartId2);

    final field1 = _getPrimaryDataField(chart1);
    final field2 = _getPrimaryDataField(chart2);

    return field1 == field2 || _fieldsAreRelated(field1, field2);
  }

  bool _fieldsAreRelated(String field1, String field2) {
    // Define relationships between data fields
    const relatedFields = {
      'region': ['country', 'state', 'district'],
      'date': ['month', 'quarter', 'year'],
      'risk_score': ['prediction_confidence', 'alert_level'],
    };

    for (final entry in relatedFields.entries) {
      if ((entry.key == field1 && entry.value.contains(field2)) ||
          (entry.key == field2 && entry.value.contains(field1))) {
        return true;
      }
    }

    return false;
  }

  double _calculateConnectionStrength(Map<String, dynamic> filterCriteria) {
    // Calculate connection strength based on filter selectivity
    final type = filterCriteria['type'] as String?;
    switch (type) {
      case 'selection':
        final values = filterCriteria['values'] as List<dynamic>?;
        return 1.0 / (values?.length ?? 1);
      case 'filter':
        return 0.8;
      default:
        return 0.5;
    }
  }

  InteractiveChart _applyFiltersToChart(InteractiveChart chart) {
    // Apply active cross-filters to chart data
    if (_activeCrossFilters.isEmpty) return chart;

    // Create filtered version of chart data
    dynamic filteredData = _filterChartData(chart.chartData, _activeCrossFilters);

    return chart.copyWith(chartData: filteredData);
  }

  dynamic _filterChartData(dynamic chartData, Map<String, dynamic> filters) {
    // Apply filters to chart data based on data type
    if (chartData is LineChartDataEntity) {
      return _filterLineChartData(chartData, filters);
    } else if (chartData is BarChartDataEntity) {
      return _filterBarChartData(chartData, filters);
    } else if (chartData is PieChartDataEntity) {
      return _filterPieChartData(chartData, filters);
    }

    return chartData;
  }

  LineChartDataEntity _filterLineChartData(LineChartDataEntity data, Map<String, dynamic> filters) {
    // Implement line chart data filtering
    return data; // Simplified for now
  }

  BarChartDataEntity _filterBarChartData(BarChartDataEntity data, Map<String, dynamic> filters) {
    // Implement bar chart data filtering
    return data; // Simplified for now
  }

  PieChartDataEntity _filterPieChartData(PieChartDataEntity data, Map<String, dynamic> filters) {
    // Implement pie chart data filtering
    return data; // Simplified for now
  }

  Map<String, dynamic> _convertBrushToFilter(InteractiveChart chart, Rect brushRect) {
    // Convert brush selection coordinates to filter criteria
    return {
      'type': 'brush',
      'bounds': {
        'left': brushRect.left,
        'top': brushRect.top,
        'right': brushRect.right,
        'bottom': brushRect.bottom,
      },
      'field': _getPrimaryDataField(chart),
    };
  }

  String _getPrimaryDataField(InteractiveChart chart) {
    // Determine primary data field for chart
    switch (chart.chartType) {
      case InteractiveChartType.line:
        return 'time';
      case InteractiveChartType.bar:
        return 'category';
      case InteractiveChartType.pie:
        return 'category';
      case InteractiveChartType.scatter:
        return 'value';
      default:
        return 'value';
    }
  }

  String _getChartTitle(String chartId) {
    return widget.charts.firstWhere((c) => c.chartId == chartId).title;
  }

  String _getFilterDescription(Map<String, dynamic> filterCriteria) {
    final type = filterCriteria['type'] as String?;
    switch (type) {
      case 'selection':
        final values = filterCriteria['values'] as List<dynamic>?;
        return '${values?.length ?? 0} selected';
      case 'filter':
        final field = filterCriteria['field'] as String?;
        final value = filterCriteria['value'];
        return '$field = $value';
      case 'brush':
        return 'brush selection';
      default:
        return 'filtered';
    }
  }
}

// Supporting classes and enums

class ChartConnection {
  final String sourceChartId;
  final String targetChartId;
  final ConnectionType connectionType;
  final double strength;

  const ChartConnection({
    required this.sourceChartId,
    required this.targetChartId,
    required this.connectionType,
    required this.strength,
  });
}

enum ConnectionType {
  filter,
  selection,
  brush,
  correlation,
}

class CrossFilterLayoutConfig {
  final double chartAspectRatio;
  final double chartSpacing;
  final int maxChartsPerRow;
  final bool adaptiveLayout;

  const CrossFilterLayoutConfig({
    required this.chartAspectRatio,
    required this.chartSpacing,
    required this.maxChartsPerRow,
    required this.adaptiveLayout,
  });

  factory CrossFilterLayoutConfig.adaptive() {
    return const CrossFilterLayoutConfig(
      chartAspectRatio: 1.5,
      chartSpacing: 12,
      maxChartsPerRow: 4,
      adaptiveLayout: true,
    );
  }

  factory CrossFilterLayoutConfig.compact() {
    return const CrossFilterLayoutConfig(
      chartAspectRatio: 1.0,
      chartSpacing: 8,
      maxChartsPerRow: 6,
      adaptiveLayout: true,
    );
  }
}

class CrossFilterThemeData {
  final Color defaultBorderColor;
  final Color hoverBorderColor;
  final Color activeFilterBorderColor;
  final Color chartHeaderColor;
  final Color chartFooterColor;
  final Color activeFilterHeaderColor;
  final Color filterIndicatorColor;
  final Color filterSummaryBackgroundColor;
  final Color filterSummaryItemColor;
  final Color brushSelectionColor;
  final Color connectionLineColor;
  final Color borderColor;
  final Color primaryColor;
  final Color iconColor;
  final TextStyle chartTitleStyle;
  final TextStyle filterDescriptionStyle;
  final TextStyle filterSummaryHeaderStyle;
  final ChartThemeData? chartTheme;

  const CrossFilterThemeData({
    this.defaultBorderColor = const Color(0xFFE0E0E0),
    this.hoverBorderColor = const Color(0xFFBDBDBD),
    this.activeFilterBorderColor = Colors.blue,
    this.chartHeaderColor = const Color(0xFFF5F5F5),
    this.chartFooterColor = const Color(0xFFE3F2FD),
    this.activeFilterHeaderColor = const Color(0xFFE3F2FD),
    this.filterIndicatorColor = Colors.blue,
    this.filterSummaryBackgroundColor = Colors.white,
    this.filterSummaryItemColor = const Color(0xFFE3F2FD),
    this.brushSelectionColor = Colors.blue,
    this.connectionLineColor = Colors.blue,
    this.borderColor = const Color(0xFFE0E0E0),
    this.primaryColor = Colors.blue,
    this.iconColor = const Color(0xFF757575),
    this.chartTitleStyle = const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
    this.filterDescriptionStyle = const TextStyle(fontSize: 9, color: Colors.blue),
    this.filterSummaryHeaderStyle = const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
    this.chartTheme,
  });
}

// Custom painter for chart connections
class ChartConnectionsPainter extends CustomPainter {
  final List<ChartConnection> connections;
  final Map<String, Rect> chartPositions;
  final double animationValue;
  final CrossFilterThemeData? theme;

  ChartConnectionsPainter({
    required this.connections,
    required this.chartPositions,
    required this.animationValue,
    this.theme,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = (theme?.connectionLineColor ?? Colors.blue).withOpacity(0.6 * animationValue)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    for (final connection in connections) {
      final sourceRect = chartPositions[connection.sourceChartId];
      final targetRect = chartPositions[connection.targetChartId];

      if (sourceRect != null && targetRect != null) {
        final startPoint = Offset(
          sourceRect.center.dx,
          sourceRect.center.dy,
        );
        final endPoint = Offset(
          targetRect.center.dx,
          targetRect.center.dy,
        );

        // Draw curved connection line
        final controlPoint1 = Offset(
          startPoint.dx + (endPoint.dx - startPoint.dx) * 0.3,
          startPoint.dy,
        );
        final controlPoint2 = Offset(
          startPoint.dx + (endPoint.dx - startPoint.dx) * 0.7,
          endPoint.dy,
        );

        final path = Path()
          ..moveTo(startPoint.dx, startPoint.dy)
          ..cubicTo(
            controlPoint1.dx,
            controlPoint1.dy,
            controlPoint2.dx,
            controlPoint2.dy,
            endPoint.dx,
            endPoint.dy,
          );

        // Adjust paint opacity based on connection strength
        paint.color = (theme?.connectionLineColor ?? Colors.blue)
            .withOpacity(connection.strength * animationValue);

        canvas.drawPath(path, paint);

        // Draw arrowhead at target
        _drawArrowhead(canvas, paint, endPoint, startPoint);
      }
    }
  }

  void _drawArrowhead(Canvas canvas, Paint paint, Offset endPoint, Offset startPoint) {
    final direction = (endPoint - startPoint).direction;
    final arrowLength = 8.0;
    final arrowAngle = 0.5;

    final arrowPoint1 = Offset(
      endPoint.dx - arrowLength * math.cos(direction - arrowAngle),
      endPoint.dy - arrowLength * math.sin(direction - arrowAngle),
    );

    final arrowPoint2 = Offset(
      endPoint.dx - arrowLength * math.cos(direction + arrowAngle),
      endPoint.dy - arrowLength * math.sin(direction + arrowAngle),
    );

    final arrowPath = Path()
      ..moveTo(endPoint.dx, endPoint.dy)
      ..lineTo(arrowPoint1.dx, arrowPoint1.dy)
      ..lineTo(arrowPoint2.dx, arrowPoint2.dy)
      ..close();

    paint.style = PaintingStyle.fill;
    canvas.drawPath(arrowPath, paint);
    paint.style = PaintingStyle.stroke;
  }

  @override
  bool shouldRepaint(covariant ChartConnectionsPainter oldDelegate) {
    return connections != oldDelegate.connections ||
           chartPositions != oldDelegate.chartPositions ||
           animationValue != oldDelegate.animationValue;
  }
}