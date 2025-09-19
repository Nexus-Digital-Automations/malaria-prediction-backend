/// Interactive data exploration panel for analytics dashboard
///
/// This widget provides a comprehensive interface for exploring analytics data
/// with advanced filtering, visualization controls, and interaction capabilities.
/// Integrates with AnalyticsBloc for state management and real-time updates.
///
/// Features:
/// - Multi-dimensional filtering and sorting
/// - Interactive visualization controls
/// - Real-time data refresh capabilities
/// - Export and bookmark functionality
/// - Responsive design for various screen sizes
///
/// Usage:
/// ```dart
/// DataExplorationPanel(
///   onFiltersChanged: (filters) => analyticsBloc.add(ApplyFilters(filters: filters)),
///   onExportRequested: (format) => analyticsBloc.add(ExportAnalyticsReport(format: format)),
///   onBookmarkSaved: (name, state) => bookmarkManager.saveBookmark(name, state),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:logging/logging.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/analytics_filters.dart';
import '../bloc/analytics_bloc.dart';
import 'filter_controls_widget.dart';
import 'date_range_selector.dart';
import 'drill_down_interface.dart';
import 'comparison_mode_widget.dart';
import 'data_export_panel.dart';
import 'bookmark_manager.dart';

/// Logger for data exploration panel operations
final _logger = Logger('DataExplorationPanel');

/// Main data exploration panel widget
class DataExplorationPanel extends StatefulWidget {
  /// Callback when filters are changed
  final ValueChanged<AnalyticsFilters>? onFiltersChanged;

  /// Callback when export is requested
  final ValueChanged<ExportFormat>? onExportRequested;

  /// Callback when bookmark is saved
  final Function(String name, Map<String, dynamic> state)? onBookmarkSaved;

  /// Callback when bookmark is loaded
  final ValueChanged<Map<String, dynamic>>? onBookmarkLoaded;

  /// Initial analytics filters
  final AnalyticsFilters? initialFilters;

  /// Whether panel should auto-refresh data
  final bool autoRefresh;

  /// Auto-refresh interval in seconds
  final int refreshIntervalSeconds;

  /// Whether to show advanced controls by default
  final bool showAdvancedControls;

  /// Custom color scheme for the panel
  final ColorScheme? colorScheme;

  const DataExplorationPanel({
    super.key,
    this.onFiltersChanged,
    this.onExportRequested,
    this.onBookmarkSaved,
    this.onBookmarkLoaded,
    this.initialFilters,
    this.autoRefresh = false,
    this.refreshIntervalSeconds = 30,
    this.showAdvancedControls = false,
    this.colorScheme,
  });

  @override
  State<DataExplorationPanel> createState() => _DataExplorationPanelState();
}

class _DataExplorationPanelState extends State<DataExplorationPanel>
    with TickerProviderStateMixin {
  /// Animation controller for panel transitions
  late AnimationController _animationController;

  /// Animation for panel expansion/collapse
  late Animation<double> _expansionAnimation;

  /// Tab controller for exploration modes
  late TabController _tabController;

  /// Current analytics filters
  late AnalyticsFilters _currentFilters;

  /// Whether panel is expanded
  bool _isExpanded = true;

  /// Whether advanced controls are visible
  bool _showAdvancedControls = false;

  /// Whether comparison mode is active
  bool _comparisonMode = false;

  /// Current exploration mode
  ExplorationMode _explorationMode = ExplorationMode.overview;

  /// Auto-refresh timer
  Stream<int>? _refreshTimer;

  /// Form key for filter validation
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  /// Search controller for data filtering
  final TextEditingController _searchController = TextEditingController();

  /// Focus node for search field
  final FocusNode _searchFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _logger.info('Initializing data exploration panel');

    // Initialize animations
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _expansionAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );

    // Initialize tab controller
    _tabController = TabController(
      length: ExplorationMode.values.length,
      vsync: this,
    );

    // Initialize filters
    _currentFilters = widget.initialFilters ?? const AnalyticsFilters();
    _showAdvancedControls = widget.showAdvancedControls;

    // Setup auto-refresh if enabled
    if (widget.autoRefresh) {
      _setupAutoRefresh();
    }

    // Start expanded
    _animationController.forward();

    // Listen to tab changes
    _tabController.addListener(_onTabChanged);
  }

  @override
  void dispose() {
    _logger.info('Disposing data exploration panel');
    _animationController.dispose();
    _tabController.dispose();
    _searchController.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  /// Sets up auto-refresh timer
  void _setupAutoRefresh() {
    _refreshTimer = Stream.periodic(
      Duration(seconds: widget.refreshIntervalSeconds),
      (count) => count,
    );

    _refreshTimer?.listen((_) {
      if (mounted) {
        _refreshData();
      }
    });
  }

  /// Handles tab change events
  void _onTabChanged() {
    if (_tabController.indexIsChanging) {
      setState(() {
        _explorationMode = ExplorationMode.values[_tabController.index];
      });
      _logger.info('Exploration mode changed to: $_explorationMode');
    }
  }

  /// Refreshes analytics data
  void _refreshData() {
    _logger.info('Refreshing analytics data');
    context.read<AnalyticsBloc>().add(const RefreshAnalyticsData());
  }

  /// Toggles panel expansion
  void _toggleExpansion() {
    setState(() {
      _isExpanded = !_isExpanded;
    });

    if (_isExpanded) {
      _animationController.forward();
    } else {
      _animationController.reverse();
    }

    _logger.info('Panel ${_isExpanded ? 'expanded' : 'collapsed'}');
  }

  /// Toggles advanced controls visibility
  void _toggleAdvancedControls() {
    setState(() {
      _showAdvancedControls = !_showAdvancedControls;
    });
    _logger.info('Advanced controls ${_showAdvancedControls ? 'shown' : 'hidden'}');
  }

  /// Toggles comparison mode
  void _toggleComparisonMode() {
    setState(() {
      _comparisonMode = !_comparisonMode;
    });
    _logger.info('Comparison mode ${_comparisonMode ? 'enabled' : 'disabled'}');
  }

  /// Handles filter changes
  void _onFiltersChanged(AnalyticsFilters filters) {
    setState(() {
      _currentFilters = filters;
    });

    widget.onFiltersChanged?.call(filters);
    _logger.info('Filters updated: ${filters.toString()}');
  }

  /// Handles search query changes
  void _onSearchChanged(String query) {
    _logger.info('Search query changed: $query');
    // Apply search filter - implementation depends on search requirements
  }

  /// Clears all filters
  void _clearFilters() {
    final clearedFilters = const AnalyticsFilters();
    _onFiltersChanged(clearedFilters);
    _searchController.clear();
    _logger.info('All filters cleared');
  }

  /// Exports current view
  void _exportCurrentView(ExportFormat format) {
    widget.onExportRequested?.call(format);
    _logger.info('Export requested: $format');
  }

  /// Saves current state as bookmark
  void _saveBookmark(String name) {
    final state = {
      'filters': _currentFilters,
      'explorationMode': _explorationMode.name,
      'comparisonMode': _comparisonMode,
      'searchQuery': _searchController.text,
      'timestamp': DateTime.now().toIso8601String(),
    };

    widget.onBookmarkSaved?.call(name, state);
    _logger.info('Bookmark saved: $name');
  }

  /// Loads bookmark state
  void _loadBookmark(Map<String, dynamic> state) {
    if (state['filters'] != null) {
      _onFiltersChanged(state['filters'] as AnalyticsFilters);
    }

    if (state['explorationMode'] != null) {
      final mode = ExplorationMode.values.firstWhere(
        (m) => m.name == state['explorationMode'],
        orElse: () => ExplorationMode.overview,
      );
      _tabController.animateTo(mode.index);
    }

    if (state['comparisonMode'] != null) {
      setState(() {
        _comparisonMode = state['comparisonMode'] as bool;
      });
    }

    if (state['searchQuery'] != null) {
      _searchController.text = state['searchQuery'] as String;
    }

    widget.onBookmarkLoaded?.call(state);
    _logger.info('Bookmark loaded');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = widget.colorScheme ?? theme.colorScheme;

    return BlocBuilder<AnalyticsBloc, AnalyticsState>(
      builder: (context, state) {
        return Card(
          elevation: 4,
          margin: const EdgeInsets.all(16),
          child: AnimatedBuilder(
            animation: _expansionAnimation,
            builder: (context, child) {
              return Column(
                children: [
                  // Panel header with controls
                  _buildPanelHeader(colorScheme),

                  // Expandable content
                  ClipRect(
                    child: SizeTransition(
                      sizeFactor: _expansionAnimation,
                      child: _buildPanelContent(context, state, colorScheme),
                    ),
                  ),
                ],
              );
            },
          ),
        );
      },
    );
  }

  /// Builds the panel header with title and controls
  Widget _buildPanelHeader(ColorScheme colorScheme) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.primaryContainer,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
      ),
      child: Row(
        children: [
          // Title and subtitle
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Data Exploration',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Interactive analytics dashboard with advanced filtering',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: colorScheme.onPrimaryContainer.withOpacity(0.8),
                  ),
                ),
              ],
            ),
          ),

          // Control buttons
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Refresh button
              IconButton(
                onPressed: _refreshData,
                icon: const Icon(Icons.refresh),
                tooltip: 'Refresh Data',
                color: colorScheme.onPrimaryContainer,
              ),

              // Advanced controls toggle
              IconButton(
                onPressed: _toggleAdvancedControls,
                icon: Icon(_showAdvancedControls ? Icons.tune : Icons.tune_outlined),
                tooltip: 'Advanced Controls',
                color: colorScheme.onPrimaryContainer,
              ),

              // Comparison mode toggle
              IconButton(
                onPressed: _toggleComparisonMode,
                icon: Icon(_comparisonMode ? Icons.compare_arrows : Icons.compare_arrows_outlined),
                tooltip: 'Comparison Mode',
                color: colorScheme.onPrimaryContainer,
              ),

              // Expand/collapse toggle
              IconButton(
                onPressed: _toggleExpansion,
                icon: Icon(_isExpanded ? Icons.expand_less : Icons.expand_more),
                tooltip: _isExpanded ? 'Collapse' : 'Expand',
                color: colorScheme.onPrimaryContainer,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds the main panel content
  Widget _buildPanelContent(BuildContext context, AnalyticsState state, ColorScheme colorScheme) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Search and quick actions
          _buildSearchAndActions(colorScheme),

          const SizedBox(height: 16),

          // Tab bar for exploration modes
          _buildExplorationTabs(colorScheme),

          const SizedBox(height: 16),

          // Main content area
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                // Overview tab
                _buildOverviewTab(context, state),

                // Filtering tab
                _buildFilteringTab(context, state),

                // Drill-down tab
                _buildDrillDownTab(context, state),

                // Comparison tab
                _buildComparisonTab(context, state),

                // Export tab
                _buildExportTab(context, state),

                // Bookmarks tab
                _buildBookmarksTab(context, state),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Builds search bar and quick actions
  Widget _buildSearchAndActions(ColorScheme colorScheme) {
    return Row(
      children: [
        // Search field
        Expanded(
          child: TextField(
            controller: _searchController,
            focusNode: _searchFocusNode,
            decoration: InputDecoration(
              hintText: 'Search data...',
              prefixIcon: const Icon(Icons.search),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
              suffixIcon: _searchController.text.isNotEmpty
                  ? IconButton(
                      onPressed: () {
                        _searchController.clear();
                        _onSearchChanged('');
                      },
                      icon: const Icon(Icons.clear),
                    )
                  : null,
            ),
            onChanged: _onSearchChanged,
          ),
        ),

        const SizedBox(width: 16),

        // Quick action buttons
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Clear filters
            ElevatedButton.icon(
              onPressed: _clearFilters,
              icon: const Icon(Icons.clear_all),
              label: const Text('Clear'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colorScheme.surfaceContainerHighest,
                foregroundColor: colorScheme.onSurface,
              ),
            ),

            const SizedBox(width: 8),

            // Apply filters
            ElevatedButton.icon(
              onPressed: () => _onFiltersChanged(_currentFilters),
              icon: const Icon(Icons.filter_alt),
              label: const Text('Apply'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colorScheme.primary,
                foregroundColor: colorScheme.onPrimary,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds exploration mode tabs
  Widget _buildExplorationTabs(ColorScheme colorScheme) {
    return TabBar(
      controller: _tabController,
      isScrollable: true,
      labelColor: colorScheme.primary,
      unselectedLabelColor: colorScheme.onSurface.withOpacity(0.6),
      indicatorColor: colorScheme.primary,
      tabs: const [
        Tab(icon: Icon(Icons.dashboard), text: 'Overview'),
        Tab(icon: Icon(Icons.filter_alt), text: 'Filters'),
        Tab(icon: Icon(Icons.zoom_in), text: 'Drill Down'),
        Tab(icon: Icon(Icons.compare), text: 'Compare'),
        Tab(icon: Icon(Icons.download), text: 'Export'),
        Tab(icon: Icon(Icons.bookmark), text: 'Bookmarks'),
      ],
    );
  }

  /// Builds overview tab content
  Widget _buildOverviewTab(BuildContext context, AnalyticsState state) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Data summary cards
          _buildDataSummaryCards(state),

          const SizedBox(height: 16),

          // Quick insights
          _buildQuickInsights(state),

          const SizedBox(height: 16),

          // Recent activity
          _buildRecentActivity(state),
        ],
      ),
    );
  }

  /// Builds filtering tab content
  Widget _buildFilteringTab(BuildContext context, AnalyticsState state) {
    return SingleChildScrollView(
      child: Column(
        children: [
          // Date range selector
          DateRangeSelector(
            initialDateRange: state is AnalyticsLoaded ? state.selectedDateRange : null,
            onDateRangeChanged: (dateRange) {
              context.read<AnalyticsBloc>().add(ChangeDateRange(dateRange: dateRange));
            },
            showPresets: true,
            showQuickOptions: true,
          ),

          const SizedBox(height: 16),

          // Filter controls
          FilterControlsWidget(
            filters: _currentFilters,
            onFiltersChanged: _onFiltersChanged,
            showAdvancedFilters: _showAdvancedControls,
            allowCustomRanges: true,
          ),
        ],
      ),
    );
  }

  /// Builds drill-down tab content
  Widget _buildDrillDownTab(BuildContext context, AnalyticsState state) {
    return DrillDownInterface(
      analyticsData: state is AnalyticsLoaded ? state.analyticsData : null,
      onDrillDown: (level, filters) {
        _onFiltersChanged(filters);
      },
      maxDrillLevels: 5,
      showBreadcrumbs: true,
    );
  }

  /// Builds comparison tab content
  Widget _buildComparisonTab(BuildContext context, AnalyticsState state) {
    if (!_comparisonMode) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.compare_arrows,
              size: 64,
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
            ),
            const SizedBox(height: 16),
            Text(
              'Enable comparison mode to compare datasets',
              style: Theme.of(context).textTheme.bodyLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _toggleComparisonMode,
              icon: const Icon(Icons.compare_arrows),
              label: const Text('Enable Comparison Mode'),
            ),
          ],
        ),
      );
    }

    return ComparisonModeWidget(
      primaryData: state is AnalyticsLoaded ? state.analyticsData : null,
      secondaryData: null, // Would be set when selecting comparison dataset
      comparisonType: ComparisonType.sideBySide,
      onComparisonTypeChanged: (type) {
        // Handle comparison type change
      },
    );
  }

  /// Builds export tab content
  Widget _buildExportTab(BuildContext context, AnalyticsState state) {
    return DataExportPanel(
      analyticsData: state is AnalyticsLoaded ? state.analyticsData : null,
      availableFormats: const [
        ExportFormat.pdf,
        ExportFormat.xlsx,
        ExportFormat.csv,
        ExportFormat.json,
        ExportFormat.png,
      ],
      onExportRequested: _exportCurrentView,
      showPreview: true,
      allowCustomization: true,
    );
  }

  /// Builds bookmarks tab content
  Widget _buildBookmarksTab(BuildContext context, AnalyticsState state) {
    return BookmarkManager(
      onBookmarkSaved: _saveBookmark,
      onBookmarkLoaded: _loadBookmark,
      showCategories: true,
      allowSharing: true,
    );
  }

  /// Builds data summary cards
  Widget _buildDataSummaryCards(AnalyticsState state) {
    if (state is! AnalyticsLoaded) {
      return const SizedBox.shrink();
    }

    return Wrap(
      spacing: 16,
      runSpacing: 16,
      children: [
        _buildSummaryCard(
          'Data Points',
          '${state.analyticsData.environmentalTrends.length}',
          Icons.data_usage,
          Colors.blue,
        ),
        _buildSummaryCard(
          'Date Range',
          '${state.selectedDateRange.duration.inDays} days',
          Icons.date_range,
          Colors.green,
        ),
        _buildSummaryCard(
          'Accuracy',
          '${(state.analyticsData.predictionAccuracy.overall * 100).toStringAsFixed(1)}%',
          Icons.accuracy,
          Colors.orange,
        ),
        _buildSummaryCard(
          'Quality',
          '${(state.analyticsData.dataQuality.completeness * 100).toStringAsFixed(1)}%',
          Icons.verified,
          Colors.purple,
        ),
      ],
    );
  }

  /// Builds individual summary card
  Widget _buildSummaryCard(String title, String value, IconData icon, Color color) {
    return SizedBox(
      width: 120,
      height: 100,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 24),
              const SizedBox(height: 8),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                title,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Builds quick insights section
  Widget _buildQuickInsights(AnalyticsState state) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Quick Insights',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            if (state is AnalyticsLoaded) ...[
              _buildInsightItem(
                'Prediction accuracy is ${(state.analyticsData.predictionAccuracy.overall * 100).toStringAsFixed(1)}%',
                state.analyticsData.predictionAccuracy.overall > 0.8 ? Icons.trending_up : Icons.trending_down,
                state.analyticsData.predictionAccuracy.overall > 0.8 ? Colors.green : Colors.red,
              ),
              _buildInsightItem(
                'Data quality: ${(state.analyticsData.dataQuality.completeness * 100).toStringAsFixed(1)}% complete',
                Icons.assessment,
                Colors.blue,
              ),
              _buildInsightItem(
                '${state.analyticsData.alertStatistics.totalAlerts} alerts in period',
                Icons.notifications,
                Colors.orange,
              ),
            ] else
              const Text('Load data to see insights'),
          ],
        ),
      ),
    );
  }

  /// Builds individual insight item
  Widget _buildInsightItem(String text, IconData icon, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 8),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }

  /// Builds recent activity section
  Widget _buildRecentActivity(AnalyticsState state) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Recent Activity',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            if (state is AnalyticsLoaded)
              Text('Last updated: ${state.lastRefresh.toString()}')
            else
              const Text('No recent activity'),
          ],
        ),
      ),
    );
  }
}

/// Exploration mode enumeration
enum ExplorationMode {
  overview,
  filtering,
  drillDown,
  comparison,
  export,
  bookmarks,
}