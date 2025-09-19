/// Multi-Dimensional Viewer widget for advanced data analysis
///
/// This widget provides comprehensive multi-dimensional data analysis
/// capabilities including dimension selection, aggregation configuration,
/// drill-down hierarchies, and cross-dimensional correlation analysis
/// for malaria prediction analytics.
///
/// Usage:
/// ```dart
/// MultiDimensionalViewerWidget(
///   selectedDimensions: currentDimensions,
///   onDimensionsChanged: (dimensions) => updateDimensions(dimensions),
///   onAnalysisRequested: (type, params) => performAnalysis(type, params),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../domain/entities/data_explorer.dart';

/// Advanced multi-dimensional data viewer with analysis capabilities
class MultiDimensionalViewerWidget extends StatefulWidget {
  /// Currently selected dimensions for analysis
  final List<DataDimension> selectedDimensions;

  /// Callback for dimension selection changes
  final Function(List<DataDimension>) onDimensionsChanged;

  /// Callback for analysis requests
  final Function(String analysisType, Map<String, dynamic> parameters)? onAnalysisRequested;

  /// Available dimensions for selection
  final List<DataDimension>? availableDimensions;

  /// Whether the viewer is in read-only mode
  final bool readOnly;

  /// Theme configuration
  final MultiDimensionalViewerThemeData? theme;

  /// Maximum number of dimensions allowed for analysis
  final int maxDimensions;

  /// Whether to show dimension statistics
  final bool showStatistics;

  /// Whether to show correlation analysis
  final bool showCorrelationAnalysis;

  /// Callback for dimension validation
  final bool Function(DataDimension)? onDimensionValidate;

  const MultiDimensionalViewerWidget({
    super.key,
    required this.selectedDimensions,
    required this.onDimensionsChanged,
    this.onAnalysisRequested,
    this.availableDimensions,
    this.readOnly = false,
    this.theme,
    this.maxDimensions = 10,
    this.showStatistics = true,
    this.showCorrelationAnalysis = true,
    this.onDimensionValidate,
  });

  @override
  State<MultiDimensionalViewerWidget> createState() => _MultiDimensionalViewerWidgetState();
}

class _MultiDimensionalViewerWidgetState extends State<MultiDimensionalViewerWidget>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  /// Current working dimensions (includes unsaved changes)
  List<DataDimension> _workingDimensions = [];

  /// Available dimensions for selection
  List<DataDimension> _availableDimensions = [];

  /// Search controller for dimensions
  final TextEditingController _dimensionSearchController = TextEditingController();

  /// Filtered available dimensions based on search
  List<DataDimension> _filteredDimensions = [];

  /// Current analysis mode
  AnalysisMode _analysisMode = AnalysisMode.dimensional;

  /// Selected analysis type
  String _selectedAnalysisType = 'correlation';

  /// Whether advanced options are shown
  bool _showAdvancedOptions = false;

  /// Scroll controller for dimension list
  final ScrollController _scrollController = ScrollController();

  /// Tab controller for different views
  late TabController _tabController;

  /// Correlation analysis results
  Map<String, double> _correlationResults = {};

  /// Dimension statistics cache
  Map<String, DimensionStatistics> _statisticsCache = {};

  @override
  void initState() {
    super.initState();
    _initializeControllers();
    _initializeData();
    _setupListeners();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _dimensionSearchController.dispose();
    _scrollController.dispose();
    _tabController.dispose();
    super.dispose();
  }

  void _initializeControllers() {
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));

    _tabController = TabController(length: 3, vsync: this);

    _animationController.forward();
  }

  void _initializeData() {
    _workingDimensions = List.from(widget.selectedDimensions);
    _availableDimensions = widget.availableDimensions ?? _getDefaultDimensions();
    _filteredDimensions = List.from(_availableDimensions);
    _generateStatistics();
  }

  void _setupListeners() {
    _dimensionSearchController.addListener(_onDimensionSearchChanged);
    _tabController.addListener(_onTabChanged);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _fadeAnimation,
      builder: (context, child) {
        return Opacity(
          opacity: _fadeAnimation.value,
          child: _buildMultiDimensionalViewer(),
        );
      },
    );
  }

  Widget _buildMultiDimensionalViewer() {
    return Container(
      decoration: BoxDecoration(
        color: widget.theme?.backgroundColor ?? Colors.white,
        border: Border.all(
          color: widget.theme?.borderColor ?? Colors.grey.shade300,
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          // Viewer header
          _buildViewerHeader(),

          // Tab bar for different views
          _buildTabBar(),

          // Tab content
          Expanded(
            child: _buildTabContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildViewerHeader() {
    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: widget.theme?.headerBackgroundColor ?? Colors.grey.shade50,
        border: Border(
          bottom: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade200,
          ),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.view_column,
            size: 18,
            color: widget.theme?.iconColor ?? Colors.grey.shade700,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Dimensions (${_workingDimensions.length})',
              style: widget.theme?.headerTextStyle ?? const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ),

          // Analysis mode selector
          _buildAnalysisModeSelector(),

          // Advanced options toggle
          IconButton(
            icon: Icon(
              _showAdvancedOptions ? Icons.expand_less : Icons.expand_more,
              size: 16,
            ),
            onPressed: () => setState(() => _showAdvancedOptions = !_showAdvancedOptions),
            tooltip: 'Advanced Options',
          ),

          // Clear all dimensions
          if (_workingDimensions.isNotEmpty && !widget.readOnly)
            IconButton(
              icon: const Icon(Icons.clear_all, size: 16),
              onPressed: _clearAllDimensions,
              tooltip: 'Clear All Dimensions',
            ),
        ],
      ),
    );
  }

  Widget _buildAnalysisModeSelector() {
    return SegmentedButton<AnalysisMode>(
      segments: const [
        ButtonSegment(
          value: AnalysisMode.dimensional,
          label: Text('Dim', style: TextStyle(fontSize: 10)),
          tooltip: 'Dimensional Analysis',
        ),
        ButtonSegment(
          value: AnalysisMode.correlation,
          label: Text('Corr', style: TextStyle(fontSize: 10)),
          tooltip: 'Correlation Analysis',
        ),
        ButtonSegment(
          value: AnalysisMode.hierarchical,
          label: Text('Hier', style: TextStyle(fontSize: 10)),
          tooltip: 'Hierarchical Analysis',
        ),
      ],
      selected: {_analysisMode},
      onSelectionChanged: (selected) {
        setState(() {
          _analysisMode = selected.first;
        });
        _onAnalysisModeChanged();
      },
      style: ButtonStyle(
        visualDensity: VisualDensity.compact,
        textStyle: WidgetStateProperty.all(const TextStyle(fontSize: 9)),
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      decoration: BoxDecoration(
        color: widget.theme?.tabBarBackgroundColor ?? Colors.white,
        border: Border(
          bottom: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade200,
          ),
        ),
      ),
      child: TabBar(
        controller: _tabController,
        tabs: const [
          Tab(
            icon: Icon(Icons.list, size: 16),
            text: 'Dimensions',
          ),
          Tab(
            icon: Icon(Icons.analytics, size: 16),
            text: 'Analysis',
          ),
          Tab(
            icon: Icon(Icons.insights, size: 16),
            text: 'Insights',
          ),
        ],
        labelColor: widget.theme?.primaryColor ?? Colors.blue,
        unselectedLabelColor: Colors.grey.shade600,
        indicatorColor: widget.theme?.primaryColor ?? Colors.blue,
        labelStyle: const TextStyle(fontSize: 11),
        unselectedLabelStyle: const TextStyle(fontSize: 11),
      ),
    );
  }

  Widget _buildTabContent() {
    return TabBarView(
      controller: _tabController,
      children: [
        _buildDimensionsTab(),
        _buildAnalysisTab(),
        _buildInsightsTab(),
      ],
    );
  }

  Widget _buildDimensionsTab() {
    return Column(
      children: [
        // Selected dimensions section
        if (_workingDimensions.isNotEmpty)
          _buildSelectedDimensionsSection(),

        // Available dimensions section
        Expanded(
          child: _buildAvailableDimensionsSection(),
        ),
      ],
    );
  }

  Widget _buildSelectedDimensionsSection() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: widget.theme?.selectedDimensionsBackgroundColor ?? Colors.blue.shade50,
        border: Border(
          bottom: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade200,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Selected Dimensions',
            style: widget.theme?.sectionHeaderStyle ?? const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.blue,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            height: 120,
            child: ListView.builder(
              itemCount: _workingDimensions.length,
              itemBuilder: (context, index) {
                return _buildSelectedDimensionItem(_workingDimensions[index], index);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSelectedDimensionItem(DataDimension dimension, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      decoration: BoxDecoration(
        color: widget.theme?.dimensionItemBackgroundColor ?? Colors.white,
        border: Border.all(
          color: widget.theme?.borderColor ?? Colors.grey.shade300,
        ),
        borderRadius: BorderRadius.circular(6),
      ),
      child: ListTile(
        dense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        leading: Container(
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            color: _getDimensionTypeColor(dimension.dataType),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Icon(
            _getDimensionTypeIcon(dimension.dataType),
            size: 14,
            color: Colors.white,
          ),
        ),
        title: Text(
          dimension.displayName,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _getDimensionTypeDisplayName(dimension.dataType),
              style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
            ),
            if (dimension.currentAggregation != null)
              Text(
                'Aggregation: ${_getAggregationDisplayName(dimension.currentAggregation!)}',
                style: TextStyle(fontSize: 10, color: Colors.orange.shade700),
              ),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Hierarchy level indicator
            if (dimension.hierarchyLevel > 0)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.purple.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'L${dimension.hierarchyLevel}',
                  style: const TextStyle(fontSize: 8, fontWeight: FontWeight.bold),
                ),
              ),

            // Dimension actions
            PopupMenuButton<String>(
              icon: Icon(
                Icons.more_vert,
                size: 14,
                color: widget.theme?.iconColor ?? Colors.grey.shade600,
              ),
              itemBuilder: (context) => [
                if (dimension.isAggregatable)
                  const PopupMenuItem(
                    value: 'aggregation',
                    child: Row(
                      children: [
                        Icon(Icons.functions, size: 12),
                        SizedBox(width: 6),
                        Text('Set Aggregation', style: TextStyle(fontSize: 11)),
                      ],
                    ),
                  ),
                if (dimension.supportsDrillDown)
                  const PopupMenuItem(
                    value: 'drill_down',
                    child: Row(
                      children: [
                        Icon(Icons.arrow_downward, size: 12),
                        SizedBox(width: 6),
                        Text('Drill Down', style: TextStyle(fontSize: 11)),
                      ],
                    ),
                  ),
                const PopupMenuItem(
                  value: 'properties',
                  child: Row(
                    children: [
                      Icon(Icons.settings, size: 12),
                      SizedBox(width: 6),
                      Text('Properties', style: TextStyle(fontSize: 11)),
                    ],
                  ),
                ),
                const PopupMenuItem(
                  value: 'remove',
                  child: Row(
                    children: [
                      Icon(Icons.remove, size: 12, color: Colors.red),
                      SizedBox(width: 6),
                      Text('Remove', style: TextStyle(fontSize: 11, color: Colors.red)),
                    ],
                  ),
                ),
              ],
              onSelected: (action) => _handleDimensionAction(dimension, index, action),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAvailableDimensionsSection() {
    return Container(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Search and filter controls
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _dimensionSearchController,
                  decoration: InputDecoration(
                    hintText: 'Search dimensions...',
                    hintStyle: const TextStyle(fontSize: 12),
                    prefixIcon: const Icon(Icons.search, size: 16),
                    suffixIcon: _dimensionSearchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 16),
                            onPressed: () {
                              _dimensionSearchController.clear();
                              _onDimensionSearchChanged();
                            },
                          )
                        : null,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(6),
                      borderSide: BorderSide(color: Colors.grey.shade300),
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    isDense: true,
                  ),
                  style: const TextStyle(fontSize: 12),
                  onChanged: (_) => _onDimensionSearchChanged(),
                ),
              ),
              const SizedBox(width: 8),
              // Data type filter
              _buildDataTypeFilter(),
            ],
          ),
          const SizedBox(height: 12),

          // Available dimensions list
          Text(
            'Available Dimensions (${_filteredDimensions.length})',
            style: widget.theme?.sectionHeaderStyle ?? const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              itemCount: _filteredDimensions.length,
              itemBuilder: (context, index) {
                return _buildAvailableDimensionItem(_filteredDimensions[index]);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDataTypeFilter() {
    return PopupMenuButton<DimensionDataType?>(
      icon: Icon(
        Icons.filter_list,
        size: 16,
        color: widget.theme?.iconColor ?? Colors.grey.shade600,
      ),
      tooltip: 'Filter by Data Type',
      itemBuilder: (context) => [
        const PopupMenuItem(
          value: null,
          child: Text('All Types', style: TextStyle(fontSize: 12)),
        ),
        ...DimensionDataType.values.map((type) => PopupMenuItem(
          value: type,
          child: Row(
            children: [
              Icon(_getDimensionTypeIcon(type), size: 12),
              const SizedBox(width: 6),
              Text(_getDimensionTypeDisplayName(type), style: const TextStyle(fontSize: 12)),
            ],
          ),
        )),
      ],
      onSelected: _filterByDataType,
    );
  }

  Widget _buildAvailableDimensionItem(DataDimension dimension) {
    final isSelected = _workingDimensions.any((d) => d.name == dimension.name);
    final canAdd = !isSelected && _workingDimensions.length < widget.maxDimensions;

    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      decoration: BoxDecoration(
        color: isSelected
            ? widget.theme?.selectedDimensionBackgroundColor ?? Colors.grey.shade100
            : widget.theme?.availableDimensionBackgroundColor ?? Colors.white,
        border: Border.all(
          color: isSelected
              ? widget.theme?.primaryColor ?? Colors.blue
              : widget.theme?.borderColor ?? Colors.grey.shade300,
        ),
        borderRadius: BorderRadius.circular(6),
      ),
      child: ListTile(
        dense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        leading: Container(
          width: 20,
          height: 20,
          decoration: BoxDecoration(
            color: _getDimensionTypeColor(dimension.dataType),
            borderRadius: BorderRadius.circular(3),
          ),
          child: Icon(
            _getDimensionTypeIcon(dimension.dataType),
            size: 12,
            color: Colors.white,
          ),
        ),
        title: Text(
          dimension.displayName,
          style: const TextStyle(fontSize: 11),
        ),
        subtitle: Text(
          '${_getDimensionTypeDisplayName(dimension.dataType)}${dimension.isAggregatable ? ' • Aggregatable' : ''}${dimension.supportsDrillDown ? ' • Drillable' : ''}',
          style: TextStyle(fontSize: 9, color: Colors.grey.shade600),
        ),
        trailing: isSelected
            ? Icon(
                Icons.check_circle,
                size: 16,
                color: widget.theme?.primaryColor ?? Colors.blue,
              )
            : canAdd && !widget.readOnly
                ? IconButton(
                    icon: Icon(
                      Icons.add_circle_outline,
                      size: 16,
                      color: widget.theme?.primaryColor ?? Colors.blue,
                    ),
                    onPressed: () => _addDimension(dimension),
                  )
                : Icon(
                    Icons.block,
                    size: 16,
                    color: Colors.grey.shade400,
                  ),
        onTap: canAdd && !isSelected && !widget.readOnly
            ? () => _addDimension(dimension)
            : null,
      ),
    );
  }

  Widget _buildAnalysisTab() {
    return Container(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Analysis type selector
          _buildAnalysisTypeSelector(),
          const SizedBox(height: 16),

          // Analysis configuration
          _buildAnalysisConfiguration(),
          const SizedBox(height: 16),

          // Run analysis button
          if (_workingDimensions.length >= 2)
            _buildRunAnalysisButton(),

          // Analysis results
          Expanded(
            child: _buildAnalysisResults(),
          ),
        ],
      ),
    );
  }

  Widget _buildAnalysisTypeSelector() {
    final analysisTypes = [
      'correlation',
      'distribution',
      'clustering',
      'regression',
      'pca',
      'trend_analysis',
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Analysis Type',
          style: widget.theme?.sectionHeaderStyle ?? const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _selectedAnalysisType,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            isDense: true,
          ),
          style: const TextStyle(fontSize: 12),
          items: analysisTypes.map((type) {
            return DropdownMenuItem(
              value: type,
              child: Text(_getAnalysisTypeDisplayName(type)),
            );
          }).toList(),
          onChanged: (value) {
            if (value != null) {
              setState(() {
                _selectedAnalysisType = value;
              });
            }
          },
        ),
      ],
    );
  }

  Widget _buildAnalysisConfiguration() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Configuration',
          style: widget.theme?.sectionHeaderStyle ?? const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: BorderRadius.circular(6),
          ),
          child: _buildAnalysisConfigurationContent(),
        ),
      ],
    );
  }

  Widget _buildAnalysisConfigurationContent() {
    switch (_selectedAnalysisType) {
      case 'correlation':
        return _buildCorrelationConfiguration();
      case 'distribution':
        return _buildDistributionConfiguration();
      case 'clustering':
        return _buildClusteringConfiguration();
      default:
        return const Text(
          'Configuration options will appear here based on analysis type.',
          style: TextStyle(fontSize: 11, color: Colors.grey),
        );
    }
  }

  Widget _buildCorrelationConfiguration() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Correlation Method:',
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            Radio<String>(
              value: 'pearson',
              groupValue: 'pearson',
              onChanged: (_) {},
              visualDensity: VisualDensity.compact,
            ),
            const Text('Pearson', style: TextStyle(fontSize: 10)),
            const SizedBox(width: 12),
            Radio<String>(
              value: 'spearman',
              groupValue: 'pearson',
              onChanged: (_) {},
              visualDensity: VisualDensity.compact,
            ),
            const Text('Spearman', style: TextStyle(fontSize: 10)),
          ],
        ),
      ],
    );
  }

  Widget _buildDistributionConfiguration() {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Distribution analysis will show statistical summaries and histograms.',
          style: TextStyle(fontSize: 11),
        ),
      ],
    );
  }

  Widget _buildClusteringConfiguration() {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'K-means clustering configuration:',
          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
        ),
        SizedBox(height: 8),
        Text(
          'Number of clusters: 3',
          style: TextStyle(fontSize: 10),
        ),
      ],
    );
  }

  Widget _buildRunAnalysisButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: _runAnalysis,
        icon: const Icon(Icons.play_arrow, size: 16),
        label: Text('Run ${_getAnalysisTypeDisplayName(_selectedAnalysisType)}'),
        style: ElevatedButton.styleFrom(
          backgroundColor: widget.theme?.primaryColor ?? Colors.blue,
          foregroundColor: Colors.white,
          textStyle: const TextStyle(fontSize: 12),
          padding: const EdgeInsets.symmetric(vertical: 8),
        ),
      ),
    );
  }

  Widget _buildAnalysisResults() {
    if (_correlationResults.isEmpty) {
      return const Center(
        child: Text(
          'Run analysis to see results here',
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
      );
    }

    return ListView(
      children: [
        Text(
          'Analysis Results',
          style: widget.theme?.sectionHeaderStyle ?? const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        ..._correlationResults.entries.map((entry) {
          return Card(
            child: ListTile(
              dense: true,
              title: Text(entry.key, style: const TextStyle(fontSize: 11)),
              trailing: Text(
                entry.value.toStringAsFixed(3),
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: _getCorrelationColor(entry.value),
                ),
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildInsightsTab() {
    return Container(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Dimension Insights',
            style: widget.theme?.sectionHeaderStyle ?? const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _buildInsightsContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildInsightsContent() {
    if (_workingDimensions.isEmpty) {
      return const Center(
        child: Text(
          'Select dimensions to see insights',
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
      );
    }

    return ListView.builder(
      itemCount: _workingDimensions.length,
      itemBuilder: (context, index) {
        final dimension = _workingDimensions[index];
        final stats = _statisticsCache[dimension.name];
        return _buildDimensionInsightCard(dimension, stats);
      },
    );
  }

  Widget _buildDimensionInsightCard(DataDimension dimension, DimensionStatistics? stats) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  _getDimensionTypeIcon(dimension.dataType),
                  size: 16,
                  color: _getDimensionTypeColor(dimension.dataType),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    dimension.displayName,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (stats != null) ...[
              Text(
                'Unique Values: ${stats.uniqueValues}',
                style: const TextStyle(fontSize: 10),
              ),
              if (stats.mean != null)
                Text(
                  'Mean: ${stats.mean!.toStringAsFixed(2)}',
                  style: const TextStyle(fontSize: 10),
                ),
              if (stats.standardDeviation != null)
                Text(
                  'Std Dev: ${stats.standardDeviation!.toStringAsFixed(2)}',
                  style: const TextStyle(fontSize: 10),
                ),
            ] else
              const Text(
                'Loading statistics...',
                style: TextStyle(fontSize: 10, color: Colors.grey),
              ),
          ],
        ),
      ),
    );
  }

  // Event handlers

  void _onDimensionSearchChanged() {
    final query = _dimensionSearchController.text.toLowerCase();
    setState(() {
      _filteredDimensions = _availableDimensions.where((dimension) {
        return dimension.displayName.toLowerCase().contains(query) ||
               dimension.name.toLowerCase().contains(query);
      }).toList();
    });
  }

  void _onTabChanged() {
    if (_tabController.index == 1) {
      // Analysis tab - update correlation if needed
      _updateCorrelationAnalysis();
    }
  }

  void _onAnalysisModeChanged() {
    // Handle analysis mode changes
    if (_analysisMode == AnalysisMode.correlation) {
      _selectedAnalysisType = 'correlation';
    } else if (_analysisMode == AnalysisMode.hierarchical) {
      _selectedAnalysisType = 'clustering';
    }
  }

  void _addDimension(DataDimension dimension) {
    if (widget.onDimensionValidate?.call(dimension) ?? true) {
      setState(() {
        _workingDimensions.add(dimension);
      });
      _notifyDimensionsChanged();
      _generateStatisticsForDimension(dimension);
    }
  }

  void _handleDimensionAction(DataDimension dimension, int index, String action) {
    switch (action) {
      case 'aggregation':
        _showAggregationDialog(dimension, index);
        break;
      case 'drill_down':
        _performDrillDown(dimension);
        break;
      case 'properties':
        _showDimensionProperties(dimension);
        break;
      case 'remove':
        _removeDimension(index);
        break;
    }
  }

  void _filterByDataType(DimensionDataType? dataType) {
    setState(() {
      if (dataType == null) {
        _filteredDimensions = List.from(_availableDimensions);
      } else {
        _filteredDimensions = _availableDimensions
            .where((dimension) => dimension.dataType == dataType)
            .toList();
      }
    });
  }

  void _clearAllDimensions() {
    setState(() {
      _workingDimensions.clear();
      _correlationResults.clear();
    });
    _notifyDimensionsChanged();
  }

  void _removeDimension(int index) {
    setState(() {
      _workingDimensions.removeAt(index);
    });
    _notifyDimensionsChanged();
  }

  void _runAnalysis() {
    final parameters = <String, dynamic>{
      'analysisType': _selectedAnalysisType,
      'dimensions': _workingDimensions.map((d) => d.name).toList(),
      'configuration': _getAnalysisConfiguration(),
    };

    widget.onAnalysisRequested?.call(_selectedAnalysisType, parameters);

    // Simulate analysis results for demo
    _simulateAnalysisResults();
  }

  void _showAggregationDialog(DataDimension dimension, int index) {
    showDialog(
      context: context,
      builder: (context) => _AggregationDialog(
        dimension: dimension,
        onAggregationSelected: (aggregation) {
          setState(() {
            _workingDimensions[index] = dimension.withAggregation(aggregation);
          });
          _notifyDimensionsChanged();
        },
      ),
    );
  }

  void _performDrillDown(DataDimension dimension) {
    // Implement drill-down functionality
    if (dimension.childDimensions.isNotEmpty) {
      final childDimension = dimension.drillDownTo(dimension.childDimensions.first);
      _addDimension(childDimension);
    }
  }

  void _showDimensionProperties(DataDimension dimension) {
    // Show dimension properties dialog
    showDialog(
      context: context,
      builder: (context) => _DimensionPropertiesDialog(dimension: dimension),
    );
  }

  void _notifyDimensionsChanged() {
    widget.onDimensionsChanged(_workingDimensions);
  }

  // Helper methods

  List<DataDimension> _getDefaultDimensions() {
    return [
      DataDimension.numeric(
        name: 'risk_score',
        displayName: 'Risk Score',
        supportsDrillDown: true,
      ),
      DataDimension.categorical(
        name: 'region',
        displayName: 'Region',
        supportsDrillDown: true,
        childDimensions: ['country', 'state', 'district'],
      ),
      DataDimension.temporal(
        name: 'date',
        displayName: 'Date',
        supportsDrillDown: true,
      ),
      DataDimension.numeric(
        name: 'temperature',
        displayName: 'Temperature',
      ),
      DataDimension.numeric(
        name: 'rainfall',
        displayName: 'Rainfall',
      ),
      DataDimension.categorical(
        name: 'season',
        displayName: 'Season',
      ),
    ];
  }

  void _generateStatistics() {
    for (final dimension in _workingDimensions) {
      _generateStatisticsForDimension(dimension);
    }
  }

  void _generateStatisticsForDimension(DataDimension dimension) {
    // Simulate statistics generation
    _statisticsCache[dimension.name] = DimensionStatistics(
      uniqueValues: 100,
      mean: dimension.dataType == DimensionDataType.numeric ? 50.0 : null,
      standardDeviation: dimension.dataType == DimensionDataType.numeric ? 15.0 : null,
      nullCount: 5,
      totalCount: 1000,
    );
  }

  void _updateCorrelationAnalysis() {
    if (_workingDimensions.length >= 2 && widget.showCorrelationAnalysis) {
      _simulateCorrelationResults();
    }
  }

  void _simulateAnalysisResults() {
    setState(() {
      _correlationResults = {
        for (int i = 0; i < _workingDimensions.length; i++)
          for (int j = i + 1; j < _workingDimensions.length; j++)
            '${_workingDimensions[i].displayName} ↔ ${_workingDimensions[j].displayName}':
                (0.5 - 1.0) * (i + j) / 10 + 0.5
      };
    });
  }

  void _simulateCorrelationResults() {
    if (_workingDimensions.length >= 2) {
      setState(() {
        _correlationResults = {
          for (int i = 0; i < _workingDimensions.length; i++)
            for (int j = i + 1; j < _workingDimensions.length; j++)
              '${_workingDimensions[i].displayName} ↔ ${_workingDimensions[j].displayName}':
                  (0.8 - 0.2) * ((i + j) % 5) / 4 + 0.2
        };
      });
    }
  }

  Map<String, dynamic> _getAnalysisConfiguration() {
    switch (_selectedAnalysisType) {
      case 'correlation':
        return {'method': 'pearson'};
      case 'clustering':
        return {'clusters': 3, 'method': 'kmeans'};
      default:
        return {};
    }
  }

  // UI helper methods

  Color _getDimensionTypeColor(DimensionDataType dataType) {
    switch (dataType) {
      case DimensionDataType.numeric:
        return Colors.green;
      case DimensionDataType.categorical:
        return Colors.blue;
      case DimensionDataType.temporal:
        return Colors.purple;
      case DimensionDataType.geographic:
        return Colors.orange;
      case DimensionDataType.binary:
        return Colors.teal;
    }
  }

  IconData _getDimensionTypeIcon(DimensionDataType dataType) {
    switch (dataType) {
      case DimensionDataType.numeric:
        return Icons.numbers;
      case DimensionDataType.categorical:
        return Icons.category;
      case DimensionDataType.temporal:
        return Icons.schedule;
      case DimensionDataType.geographic:
        return Icons.place;
      case DimensionDataType.binary:
        return Icons.toggle_on;
    }
  }

  String _getDimensionTypeDisplayName(DimensionDataType dataType) {
    switch (dataType) {
      case DimensionDataType.numeric:
        return 'Numeric';
      case DimensionDataType.categorical:
        return 'Categorical';
      case DimensionDataType.temporal:
        return 'Temporal';
      case DimensionDataType.geographic:
        return 'Geographic';
      case DimensionDataType.binary:
        return 'Binary';
    }
  }

  String _getAggregationDisplayName(AggregationFunction aggregation) {
    switch (aggregation) {
      case AggregationFunction.sum:
        return 'Sum';
      case AggregationFunction.average:
        return 'Average';
      case AggregationFunction.count:
        return 'Count';
      case AggregationFunction.countDistinct:
        return 'Count Distinct';
      case AggregationFunction.min:
        return 'Minimum';
      case AggregationFunction.max:
        return 'Maximum';
      case AggregationFunction.median:
        return 'Median';
      case AggregationFunction.standardDeviation:
        return 'Std Deviation';
      case AggregationFunction.variance:
        return 'Variance';
    }
  }

  String _getAnalysisTypeDisplayName(String analysisType) {
    switch (analysisType) {
      case 'correlation':
        return 'Correlation Analysis';
      case 'distribution':
        return 'Distribution Analysis';
      case 'clustering':
        return 'Clustering Analysis';
      case 'regression':
        return 'Regression Analysis';
      case 'pca':
        return 'Principal Component Analysis';
      case 'trend_analysis':
        return 'Trend Analysis';
      default:
        return analysisType;
    }
  }

  Color _getCorrelationColor(double correlation) {
    final absCorr = correlation.abs();
    if (absCorr > 0.7) return Colors.red;
    if (absCorr > 0.5) return Colors.orange;
    if (absCorr > 0.3) return Colors.yellow.shade700;
    return Colors.grey;
  }
}

// Supporting classes

class DimensionStatistics {
  final int uniqueValues;
  final double? mean;
  final double? standardDeviation;
  final int nullCount;
  final int totalCount;

  const DimensionStatistics({
    required this.uniqueValues,
    this.mean,
    this.standardDeviation,
    required this.nullCount,
    required this.totalCount,
  });
}

enum AnalysisMode {
  dimensional,
  correlation,
  hierarchical,
}

class MultiDimensionalViewerThemeData {
  final Color backgroundColor;
  final Color headerBackgroundColor;
  final Color tabBarBackgroundColor;
  final Color borderColor;
  final Color iconColor;
  final Color primaryColor;
  final Color selectedDimensionsBackgroundColor;
  final Color dimensionItemBackgroundColor;
  final Color selectedDimensionBackgroundColor;
  final Color availableDimensionBackgroundColor;
  final TextStyle headerTextStyle;
  final TextStyle sectionHeaderStyle;

  const MultiDimensionalViewerThemeData({
    this.backgroundColor = Colors.white,
    this.headerBackgroundColor = const Color(0xFFF5F5F5),
    this.tabBarBackgroundColor = Colors.white,
    this.borderColor = const Color(0xFFE0E0E0),
    this.iconColor = const Color(0xFF757575),
    this.primaryColor = Colors.blue,
    this.selectedDimensionsBackgroundColor = const Color(0xFFE3F2FD),
    this.dimensionItemBackgroundColor = Colors.white,
    this.selectedDimensionBackgroundColor = const Color(0xFFF0F0F0),
    this.availableDimensionBackgroundColor = Colors.white,
    this.headerTextStyle = const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
    this.sectionHeaderStyle = const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
  });
}

// Dialogs

class _AggregationDialog extends StatefulWidget {
  final DataDimension dimension;
  final Function(AggregationFunction) onAggregationSelected;

  const _AggregationDialog({
    required this.dimension,
    required this.onAggregationSelected,
  });

  @override
  State<_AggregationDialog> createState() => _AggregationDialogState();
}

class _AggregationDialogState extends State<_AggregationDialog> {
  AggregationFunction? _selectedAggregation;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Select Aggregation'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: widget.dimension.availableAggregations.map((aggregation) {
          return RadioListTile<AggregationFunction>(
            title: Text(_getAggregationDisplayName(aggregation)),
            value: aggregation,
            groupValue: _selectedAggregation,
            onChanged: (value) {
              setState(() {
                _selectedAggregation = value;
              });
            },
          );
        }).toList(),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _selectedAggregation != null
              ? () {
                  widget.onAggregationSelected(_selectedAggregation!);
                  Navigator.of(context).pop();
                }
              : null,
          child: const Text('Apply'),
        ),
      ],
    );
  }

  String _getAggregationDisplayName(AggregationFunction aggregation) {
    switch (aggregation) {
      case AggregationFunction.sum:
        return 'Sum';
      case AggregationFunction.average:
        return 'Average';
      case AggregationFunction.count:
        return 'Count';
      case AggregationFunction.countDistinct:
        return 'Count Distinct';
      case AggregationFunction.min:
        return 'Minimum';
      case AggregationFunction.max:
        return 'Maximum';
      case AggregationFunction.median:
        return 'Median';
      case AggregationFunction.standardDeviation:
        return 'Standard Deviation';
      case AggregationFunction.variance:
        return 'Variance';
    }
  }
}

class _DimensionPropertiesDialog extends StatelessWidget {
  final DataDimension dimension;

  const _DimensionPropertiesDialog({required this.dimension});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${dimension.displayName} Properties'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Name: ${dimension.name}'),
          Text('Type: ${dimension.dataType}'),
          Text('Aggregatable: ${dimension.isAggregatable ? 'Yes' : 'No'}'),
          Text('Supports Drill-down: ${dimension.supportsDrillDown ? 'Yes' : 'No'}'),
          if (dimension.childDimensions.isNotEmpty)
            Text('Child Dimensions: ${dimension.childDimensions.join(', ')}'),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Close'),
        ),
      ],
    );
  }
}