/// Data Explorer Tab widget for comprehensive analytics exploration
///
/// This widget provides a comprehensive data exploration interface with
/// interactive charts, filters, multi-dimensional analysis, and drill-down
/// capabilities for malaria prediction analytics.
///
/// Usage:
/// ```dart
/// DataExplorerTab(
///   explorer: dataExplorer,
///   onExplorationChanged: (updatedExplorer) => handleUpdate(updatedExplorer),
///   onChartInteraction: (interaction) => processInteraction(interaction),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../domain/entities/data_explorer.dart';
import '../../domain/entities/interactive_chart.dart';
import '../../domain/entities/chart_data.dart';
import 'interactive_chart_widget.dart';
import 'filter_panel_widget.dart';
import 'multi_dimensional_viewer_widget.dart';
import 'cross_filter_chart_widget.dart';

/// Comprehensive data exploration tab with advanced analytics capabilities
class DataExplorerTab extends StatefulWidget {
  /// Data explorer configuration and state
  final DataExplorer explorer;

  /// Callback for exploration state changes
  final Function(DataExplorer)? onExplorationChanged;

  /// Callback for chart interactions
  final Function(ChartInteraction)? onChartInteraction;

  /// Callback for filter changes
  final Function(List<FilterCriteria>)? onFiltersChanged;

  /// Callback for dimension selection changes
  final Function(List<DataDimension>)? onDimensionsChanged;

  /// Available chart data for exploration
  final Map<String, dynamic>? availableChartData;

  /// Loading state indicator
  final bool isLoading;

  /// Error message if any
  final String? errorMessage;

  /// Whether the explorer is in read-only mode
  final bool readOnly;

  /// Custom exploration tools and actions
  final List<ExplorationTool>? customTools;

  /// Theme configuration for the explorer
  final ExplorerThemeData? theme;

  const DataExplorerTab({
    super.key,
    required this.explorer,
    this.onExplorationChanged,
    this.onChartInteraction,
    this.onFiltersChanged,
    this.onDimensionsChanged,
    this.availableChartData,
    this.isLoading = false,
    this.errorMessage,
    this.readOnly = false,
    this.customTools,
    this.theme,
  });

  @override
  State<DataExplorerTab> createState() => _DataExplorerTabState();
}

class _DataExplorerTabState extends State<DataExplorerTab>
    with TickerProviderStateMixin, AutomaticKeepAliveClientMixin {
  late TabController _tabController;
  late AnimationController _animationController;
  late Animation<double> _slideAnimation;

  /// Current selected chart for main view
  InteractiveChart? _selectedChart;

  /// Charts generated from current exploration
  Map<String, InteractiveChart> _generatedCharts = {};

  /// Current exploration layout mode
  ExplorationLayoutMode _layoutMode = ExplorationLayoutMode.dashboard;

  /// Filter panel visibility
  bool _showFilterPanel = true;

  /// Dimension panel visibility
  bool _showDimensionPanel = true;

  /// Performance metrics tracking
  final Map<String, dynamic> _performanceMetrics = {};

  /// Keyboard shortcuts handler
  late FocusNode _focusNode;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _initializeControllers();
    _initializeKeyboardHandlers();
    _generateInitialCharts();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _animationController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  /// Initializes animation and tab controllers
  void _initializeControllers() {
    _tabController = TabController(length: 4, vsync: this);
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _slideAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _animationController.forward();
  }

  /// Initializes keyboard shortcuts
  void _initializeKeyboardHandlers() {
    _focusNode = FocusNode();
  }

  /// Generates initial charts based on explorer configuration
  void _generateInitialCharts() {
    // Create default charts based on available data and dimensions
    _createDefaultCharts();
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);

    return RawKeyboardListener(
      focusNode: _focusNode,
      onKey: _handleKeyboard,
      child: Scaffold(
        backgroundColor: widget.theme?.backgroundColor ?? Colors.grey.shade50,
        body: _buildExplorerBody(),
        floatingActionButton: _buildFloatingActions(),
        bottomNavigationBar: _buildBottomControls(),
      ),
    );
  }

  /// Builds the main explorer body with responsive layout
  Widget _buildExplorerBody() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isTablet = constraints.maxWidth > 768;
        final isDesktop = constraints.maxWidth > 1024;

        return AnimatedBuilder(
          animation: _slideAnimation,
          child: _buildExplorerContent(constraints, isTablet, isDesktop),
          builder: (context, child) {
            return Transform.translate(
              offset: Offset(0, (1 - _slideAnimation.value) * 50),
              child: Opacity(
                opacity: _slideAnimation.value,
                child: child,
              ),
            );
          },
        );
      },
    );
  }

  /// Builds the explorer content based on layout mode
  Widget _buildExplorerContent(BoxConstraints constraints, bool isTablet, bool isDesktop) {
    if (widget.isLoading) {
      return _buildLoadingState();
    }

    if (widget.errorMessage != null) {
      return _buildErrorState();
    }

    switch (_layoutMode) {
      case ExplorationLayoutMode.dashboard:
        return _buildDashboardLayout(isTablet, isDesktop);
      case ExplorationLayoutMode.focused:
        return _buildFocusedLayout(isTablet, isDesktop);
      case ExplorationLayoutMode.comparison:
        return _buildComparisonLayout(isTablet, isDesktop);
      case ExplorationLayoutMode.presentation:
        return _buildPresentationLayout(isTablet, isDesktop);
    }
  }

  /// Builds dashboard layout with multiple panels
  Widget _buildDashboardLayout(bool isTablet, bool isDesktop) {
    return Row(
      children: [
        // Left sidebar with filters and dimensions
        if (_showFilterPanel && isTablet)
          _buildLeftSidebar(),

        // Main content area
        Expanded(
          flex: isDesktop ? 3 : 2,
          child: Column(
            children: [
              // Explorer header with controls
              _buildExplorerHeader(),

              // Tabbed content area
              Expanded(
                child: _buildTabbedContent(),
              ),
            ],
          ),
        ),

        // Right sidebar with tools and insights
        if (_showDimensionPanel && isDesktop)
          _buildRightSidebar(),
      ],
    );
  }

  /// Builds focused layout for single chart analysis
  Widget _buildFocusedLayout(bool isTablet, bool isDesktop) {
    return Column(
      children: [
        _buildExplorerHeader(),
        Expanded(
          child: _selectedChart != null
              ? _buildChartFocusView(_selectedChart!)
              : _buildEmptyState(),
        ),
      ],
    );
  }

  /// Builds comparison layout for multiple charts
  Widget _buildComparisonLayout(bool isTablet, bool isDesktop) {
    return Column(
      children: [
        _buildExplorerHeader(),
        Expanded(
          child: _buildComparisonGrid(),
        ),
      ],
    );
  }

  /// Builds presentation layout for demos
  Widget _buildPresentationLayout(bool isTablet, bool isDesktop) {
    return Column(
      children: [
        _buildPresentationHeader(),
        Expanded(
          child: _buildPresentationContent(),
        ),
      ],
    );
  }

  /// Builds the explorer header with controls and navigation
  Widget _buildExplorerHeader() {
    return Container(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: widget.theme?.headerBackgroundColor ?? Colors.white,
        border: Border(
          bottom: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade300,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          // Session info
          _buildSessionInfo(),

          const Spacer(),

          // Layout mode selector
          _buildLayoutModeSelector(),

          const SizedBox(width: 16),

          // Explorer actions
          _buildExplorerActions(),
        ],
      ),
    );
  }

  /// Builds session information display
  Widget _buildSessionInfo() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          widget.explorer.name,
          style: widget.theme?.titleTextStyle ?? const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          'Session: ${widget.explorer.sessionId}',
          style: widget.theme?.subtitleTextStyle ?? TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }

  /// Builds layout mode selector
  Widget _buildLayoutModeSelector() {
    return SegmentedButton<ExplorationLayoutMode>(
      segments: const [
        ButtonSegment(
          value: ExplorationLayoutMode.dashboard,
          icon: Icon(Icons.dashboard, size: 16),
          label: Text('Dashboard'),
        ),
        ButtonSegment(
          value: ExplorationLayoutMode.focused,
          icon: Icon(Icons.center_focus_strong, size: 16),
          label: Text('Focus'),
        ),
        ButtonSegment(
          value: ExplorationLayoutMode.comparison,
          icon: Icon(Icons.compare, size: 16),
          label: Text('Compare'),
        ),
        ButtonSegment(
          value: ExplorationLayoutMode.presentation,
          icon: Icon(Icons.present_to_all, size: 16),
          label: Text('Present'),
        ),
      ],
      selected: {_layoutMode},
      onSelectionChanged: (selected) {
        setState(() {
          _layoutMode = selected.first;
        });
      },
    );
  }

  /// Builds explorer action buttons
  Widget _buildExplorerActions() {
    return Row(
      children: [
        // Toggle filter panel
        IconButton(
          icon: Icon(_showFilterPanel ? Icons.filter_list : Icons.filter_list_off),
          onPressed: () => setState(() => _showFilterPanel = !_showFilterPanel),
          tooltip: 'Toggle Filters',
        ),

        // Toggle dimension panel
        IconButton(
          icon: Icon(_showDimensionPanel ? Icons.view_column : Icons.view_column_outlined),
          onPressed: () => setState(() => _showDimensionPanel = !_showDimensionPanel),
          tooltip: 'Toggle Dimensions',
        ),

        // Export data
        IconButton(
          icon: const Icon(Icons.download),
          onPressed: _exportExplorationData,
          tooltip: 'Export Data',
        ),

        // Save exploration
        if (!widget.readOnly)
          IconButton(
            icon: const Icon(Icons.save),
            onPressed: _saveExploration,
            tooltip: 'Save Exploration',
          ),

        // Settings menu
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert),
          itemBuilder: (context) => [
            const PopupMenuItem(
              value: 'reset',
              child: Row(
                children: [
                  Icon(Icons.refresh, size: 16),
                  SizedBox(width: 8),
                  Text('Reset Exploration'),
                ],
              ),
            ),
            const PopupMenuItem(
              value: 'duplicate',
              child: Row(
                children: [
                  Icon(Icons.copy, size: 16),
                  SizedBox(width: 8),
                  Text('Duplicate Session'),
                ],
              ),
            ),
            const PopupMenuItem(
              value: 'share',
              child: Row(
                children: [
                  Icon(Icons.share, size: 16),
                  SizedBox(width: 8),
                  Text('Share Exploration'),
                ],
              ),
            ),
          ],
          onSelected: _handleMenuAction,
        ),
      ],
    );
  }

  /// Builds the left sidebar with filters and data source controls
  Widget _buildLeftSidebar() {
    return Container(
      width: 300,
      decoration: BoxDecoration(
        color: widget.theme?.sidebarBackgroundColor ?? Colors.white,
        border: Border(
          right: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade300,
          ),
        ),
      ),
      child: Column(
        children: [
          // Filter panel header
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              color: widget.theme?.panelHeaderColor ?? Colors.grey.shade100,
              border: Border(
                bottom: BorderSide(
                  color: widget.theme?.borderColor ?? Colors.grey.shade300,
                ),
              ),
            ),
            child: const Row(
              children: [
                Icon(Icons.filter_list, size: 18),
                SizedBox(width: 8),
                Text(
                  'Filters & Data Sources',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),

          // Filter panel content
          Expanded(
            child: FilterPanelWidget(
              appliedFilters: widget.explorer.appliedFilters,
              onFiltersChanged: _handleFiltersChanged,
              readOnly: widget.readOnly,
              theme: widget.theme?.filterPanelTheme,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the right sidebar with dimensions and insights
  Widget _buildRightSidebar() {
    return Container(
      width: 280,
      decoration: BoxDecoration(
        color: widget.theme?.sidebarBackgroundColor ?? Colors.white,
        border: Border(
          left: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade300,
          ),
        ),
      ),
      child: Column(
        children: [
          // Dimension panel header
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              color: widget.theme?.panelHeaderColor ?? Colors.grey.shade100,
              border: Border(
                bottom: BorderSide(
                  color: widget.theme?.borderColor ?? Colors.grey.shade300,
                ),
              ),
            ),
            child: const Row(
              children: [
                Icon(Icons.view_column, size: 18),
                SizedBox(width: 8),
                Text(
                  'Dimensions & Analysis',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),

          // Multi-dimensional viewer
          Expanded(
            child: MultiDimensionalViewerWidget(
              selectedDimensions: widget.explorer.selectedDimensions,
              onDimensionsChanged: _handleDimensionsChanged,
              onAnalysisRequested: _handleAnalysisRequest,
              readOnly: widget.readOnly,
              theme: widget.theme?.dimensionViewerTheme,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the tabbed content area
  Widget _buildTabbedContent() {
    return Column(
      children: [
        // Tab bar
        Container(
          decoration: BoxDecoration(
            color: widget.theme?.tabBarBackgroundColor ?? Colors.white,
            border: Border(
              bottom: BorderSide(
                color: widget.theme?.borderColor ?? Colors.grey.shade300,
              ),
            ),
          ),
          child: TabBar(
            controller: _tabController,
            tabs: const [
              Tab(
                icon: Icon(Icons.analytics, size: 18),
                text: 'Charts',
              ),
              Tab(
                icon: Icon(Icons.grid_view, size: 18),
                text: 'Cross-Filter',
              ),
              Tab(
                icon: Icon(Icons.table_chart, size: 18),
                text: 'Data Table',
              ),
              Tab(
                icon: Icon(Icons.insights, size: 18),
                text: 'Insights',
              ),
            ],
            labelColor: widget.theme?.primaryColor ?? Colors.blue,
            unselectedLabelColor: Colors.grey.shade600,
            indicatorColor: widget.theme?.primaryColor ?? Colors.blue,
          ),
        ),

        // Tab content
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildChartsTab(),
              _buildCrossFilterTab(),
              _buildDataTableTab(),
              _buildInsightsTab(),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds the charts tab with interactive visualizations
  Widget _buildChartsTab() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: _generatedCharts.isEmpty
          ? _buildEmptyChartsState()
          : _buildChartsGrid(),
    );
  }

  /// Builds the cross-filter tab
  Widget _buildCrossFilterTab() {
    return CrossFilterChartWidget(
      charts: _generatedCharts.values.toList(),
      onCrossFilter: _handleCrossFilter,
      onChartInteraction: widget.onChartInteraction,
      theme: widget.theme?.crossFilterTheme,
    );
  }

  /// Builds the data table tab
  Widget _buildDataTableTab() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: _buildDataTable(),
    );
  }

  /// Builds the insights tab with AI-generated insights
  Widget _buildInsightsTab() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: _buildInsightsPanel(),
    );
  }

  /// Builds the charts grid layout
  Widget _buildChartsGrid() {
    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: 600,
        childAspectRatio: 1.5,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
      ),
      itemCount: _generatedCharts.length,
      itemBuilder: (context, index) {
        final chart = _generatedCharts.values.elementAt(index);
        return _buildChartCard(chart);
      },
    );
  }

  /// Builds individual chart card
  Widget _buildChartCard(InteractiveChart chart) {
    return Card(
      elevation: 2,
      child: Column(
        children: [
          // Chart header
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              border: Border(
                bottom: BorderSide(color: Colors.grey.shade200),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    chart.title,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert, size: 18),
                  itemBuilder: (context) => [
                    const PopupMenuItem(value: 'focus', child: Text('Focus')),
                    const PopupMenuItem(value: 'duplicate', child: Text('Duplicate')),
                    const PopupMenuItem(value: 'export', child: Text('Export')),
                    const PopupMenuItem(value: 'remove', child: Text('Remove')),
                  ],
                  onSelected: (action) => _handleChartAction(chart, action),
                ),
              ],
            ),
          ),

          // Chart content
          Expanded(
            child: InteractiveChartWidget(
              chart: chart,
              onInteraction: widget.onChartInteraction,
              onDrillDown: _handleChartDrillDown,
              onSelectionChanged: _handleChartSelection,
              theme: widget.theme?.chartTheme,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds empty charts state
  Widget _buildEmptyChartsState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.analytics,
            size: 64,
            color: Colors.grey.shade400,
          ),
          const SizedBox(height: 16),
          Text(
            'No charts generated yet',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Apply filters and select dimensions to generate visualizations',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade500,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _generateDefaultCharts,
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Generate Sample Charts'),
          ),
        ],
      ),
    );
  }

  /// Builds data table view
  Widget _buildDataTable() {
    // Implementation for data table with sorting, filtering, and pagination
    return const Center(
      child: Text('Data Table View - Coming Soon'),
    );
  }

  /// Builds insights panel with AI-generated insights
  Widget _buildInsightsPanel() {
    // Implementation for AI insights and recommendations
    return const Center(
      child: Text('AI Insights Panel - Coming Soon'),
    );
  }

  /// Builds loading state
  Widget _buildLoadingState() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('Loading exploration data...'),
        ],
      ),
    );
  }

  /// Builds error state
  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            size: 64,
            color: Colors.red,
          ),
          const SizedBox(height: 16),
          Text(
            'Error loading exploration',
            style: const TextStyle(fontSize: 18),
          ),
          const SizedBox(height: 8),
          Text(
            widget.errorMessage!,
            style: TextStyle(color: Colors.grey.shade600),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => widget.onExplorationChanged?.call(widget.explorer),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  /// Builds empty state for various views
  Widget _buildEmptyState() {
    return const Center(
      child: Text('No data available for current selection'),
    );
  }

  /// Builds floating action buttons
  Widget? _buildFloatingActions() {
    if (widget.readOnly) return null;

    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        FloatingActionButton(
          heroTag: 'add_chart',
          onPressed: _showAddChartDialog,
          tooltip: 'Add Chart',
          child: const Icon(Icons.add_chart),
        ),
        const SizedBox(height: 8),
        FloatingActionButton(
          heroTag: 'quick_analysis',
          onPressed: _performQuickAnalysis,
          tooltip: 'Quick Analysis',
          backgroundColor: Colors.green,
          child: const Icon(Icons.auto_awesome),
        ),
      ],
    );
  }

  /// Builds bottom controls for mobile layout
  Widget? _buildBottomControls() {
    return null; // Implementation for mobile-specific controls
  }

  // Event handlers

  void _handleFiltersChanged(List<FilterCriteria> filters) {
    final updatedExplorer = widget.explorer.copyWith(appliedFilters: filters);
    widget.onFiltersChanged?.call(filters);
    widget.onExplorationChanged?.call(updatedExplorer);
    _regenerateCharts();
  }

  void _handleDimensionsChanged(List<DataDimension> dimensions) {
    final updatedExplorer = widget.explorer.copyWith(selectedDimensions: dimensions);
    widget.onDimensionsChanged?.call(dimensions);
    widget.onExplorationChanged?.call(updatedExplorer);
    _regenerateCharts();
  }

  void _handleAnalysisRequest(String analysisType, Map<String, dynamic> parameters) {
    // Perform requested analysis
    _performAnalysis(analysisType, parameters);
  }

  void _handleChartDrillDown(String dimension, dynamic value) {
    // Handle drill-down operation
    _performDrillDown(dimension, value);
  }

  void _handleChartSelection(List<dynamic> selectedValues) {
    // Handle chart selection for cross-filtering
    _applyCrossFilter(selectedValues);
  }

  void _handleCrossFilter(Map<String, dynamic> filterCriteria) {
    // Apply cross-filter across all charts
    _applyCrossFilterToAllCharts(filterCriteria);
  }

  void _handleChartAction(InteractiveChart chart, String action) {
    switch (action) {
      case 'focus':
        _focusOnChart(chart);
        break;
      case 'duplicate':
        _duplicateChart(chart);
        break;
      case 'export':
        _exportChart(chart);
        break;
      case 'remove':
        _removeChart(chart);
        break;
    }
  }

  void _handleMenuAction(String action) {
    switch (action) {
      case 'reset':
        _resetExploration();
        break;
      case 'duplicate':
        _duplicateExploration();
        break;
      case 'share':
        _shareExploration();
        break;
    }
  }

  void _handleKeyboard(RawKeyEvent event) {
    if (event is RawKeyDownEvent) {
      // Handle keyboard shortcuts
      if (event.isControlPressed) {
        switch (event.logicalKey.keyLabel) {
          case 'Z':
            _undoLastAction();
            break;
          case 'Y':
            _redoLastAction();
            break;
          case 'S':
            _saveExploration();
            break;
          case 'E':
            _exportExplorationData();
            break;
        }
      }
    }
  }

  // Helper methods

  void _createDefaultCharts() {
    // Create default charts based on available data
    _generateDefaultCharts();
  }

  void _generateDefaultCharts() {
    // Generate sample charts for demonstration
    setState(() {
      _generatedCharts = _createSampleCharts();
    });
  }

  Map<String, InteractiveChart> _createSampleCharts() {
    // Create sample interactive charts
    return {
      'risk_trend': _createSampleRiskTrendChart(),
      'regional_comparison': _createSampleRegionalChart(),
      'environmental_correlation': _createSampleCorrelationChart(),
    };
  }

  InteractiveChart _createSampleRiskTrendChart() {
    // Create sample risk trend chart
    return InteractiveChart.create(
      chartId: 'risk_trend',
      title: 'Malaria Risk Trends',
      chartType: InteractiveChartType.line,
      chartData: _createSampleLineChartData(),
    );
  }

  InteractiveChart _createSampleRegionalChart() {
    // Create sample regional comparison chart
    return InteractiveChart.create(
      chartId: 'regional_comparison',
      title: 'Regional Risk Comparison',
      chartType: InteractiveChartType.bar,
      chartData: _createSampleBarChartData(),
    );
  }

  InteractiveChart _createSampleCorrelationChart() {
    // Create sample correlation chart
    return InteractiveChart.create(
      chartId: 'environmental_correlation',
      title: 'Environmental Factors Correlation',
      chartType: InteractiveChartType.scatter,
      chartData: _createSampleScatterChartData(),
    );
  }

  dynamic _createSampleLineChartData() {
    // Create sample line chart data
    return null; // Simplified for now
  }

  dynamic _createSampleBarChartData() {
    // Create sample bar chart data
    return null; // Simplified for now
  }

  dynamic _createSampleScatterChartData() {
    // Create sample scatter chart data
    return null; // Simplified for now
  }

  void _regenerateCharts() {
    // Regenerate charts based on current filters and dimensions
    setState(() {
      _generatedCharts = _createChartsFromCurrentSelection();
    });
  }

  Map<String, InteractiveChart> _createChartsFromCurrentSelection() {
    // Create charts based on current exploration state
    return {}; // Implementation depends on data source
  }

  void _performAnalysis(String analysisType, Map<String, dynamic> parameters) {
    // Perform requested analysis
  }

  void _performDrillDown(String dimension, dynamic value) {
    // Perform drill-down operation
  }

  void _applyCrossFilter(List<dynamic> selectedValues) {
    // Apply cross-filter based on selection
  }

  void _applyCrossFilterToAllCharts(Map<String, dynamic> filterCriteria) {
    // Apply cross-filter to all charts
  }

  void _focusOnChart(InteractiveChart chart) {
    setState(() {
      _selectedChart = chart;
      _layoutMode = ExplorationLayoutMode.focused;
    });
  }

  void _duplicateChart(InteractiveChart chart) {
    // Duplicate chart
  }

  void _exportChart(InteractiveChart chart) {
    // Export chart
  }

  void _removeChart(InteractiveChart chart) {
    setState(() {
      _generatedCharts.remove(chart.chartId);
    });
  }

  void _resetExploration() {
    // Reset exploration to initial state
  }

  void _duplicateExploration() {
    // Duplicate current exploration
  }

  void _shareExploration() {
    // Share exploration
  }

  void _saveExploration() {
    // Save exploration
  }

  void _exportExplorationData() {
    // Export exploration data
  }

  void _showAddChartDialog() {
    // Show dialog to add new chart
  }

  void _performQuickAnalysis() {
    // Perform quick AI-powered analysis
  }

  void _undoLastAction() {
    // Undo last action
  }

  void _redoLastAction() {
    // Redo last action
  }

  // Placeholder build methods for layouts not yet implemented
  Widget _buildChartFocusView(InteractiveChart chart) {
    return InteractiveChartWidget(
      chart: chart,
      onInteraction: widget.onChartInteraction,
      theme: widget.theme?.chartTheme,
    );
  }

  Widget _buildComparisonGrid() {
    return const Center(child: Text('Comparison view - Coming Soon'));
  }

  Widget _buildPresentationHeader() {
    return Container(
      height: 64,
      child: const Center(child: Text('Presentation Mode')),
    );
  }

  Widget _buildPresentationContent() {
    return const Center(child: Text('Presentation content - Coming Soon'));
  }
}

/// Exploration tool definition for custom tools
class ExplorationTool {
  final String name;
  final IconData icon;
  final String tooltip;
  final VoidCallback onPressed;

  const ExplorationTool({
    required this.name,
    required this.icon,
    required this.tooltip,
    required this.onPressed,
  });
}

/// Theme data for the explorer
class ExplorerThemeData {
  final Color backgroundColor;
  final Color headerBackgroundColor;
  final Color sidebarBackgroundColor;
  final Color tabBarBackgroundColor;
  final Color panelHeaderColor;
  final Color borderColor;
  final Color primaryColor;
  final TextStyle titleTextStyle;
  final TextStyle subtitleTextStyle;
  final ChartThemeData? chartTheme;
  final dynamic filterPanelTheme;
  final dynamic dimensionViewerTheme;
  final dynamic crossFilterTheme;

  const ExplorerThemeData({
    this.backgroundColor = const Color(0xFFF5F5F5),
    this.headerBackgroundColor = Colors.white,
    this.sidebarBackgroundColor = Colors.white,
    this.tabBarBackgroundColor = Colors.white,
    this.panelHeaderColor = const Color(0xFFF0F0F0),
    this.borderColor = const Color(0xFFE0E0E0),
    this.primaryColor = Colors.blue,
    this.titleTextStyle = const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
    this.subtitleTextStyle = const TextStyle(fontSize: 12, color: Colors.grey),
    this.chartTheme,
    this.filterPanelTheme,
    this.dimensionViewerTheme,
    this.crossFilterTheme,
  });
}

/// Exploration layout modes
enum ExplorationLayoutMode {
  dashboard,
  focused,
  comparison,
  presentation,
}