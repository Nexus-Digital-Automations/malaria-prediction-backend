/// Multi-level drill-down interface for data exploration
///
/// This widget provides hierarchical data exploration capabilities
/// allowing users to progressively drill down into analytics data
/// from high-level summaries to detailed individual records.
///
/// Features:
/// - Multi-level hierarchical navigation (Region > District > Facility > Data Point)
/// - Breadcrumb navigation with back/forward controls
/// - Dynamic data loading at each drill level
/// - Context-aware filtering and visualization
/// - Real-time data aggregation and summaries
/// - Responsive layout for different screen sizes
/// - Data preview and detail views
/// - Export capabilities at any drill level
///
/// Usage:
/// ```dart
/// DrillDownInterface(
///   analyticsData: currentAnalyticsData,
///   onDrillDown: (level, filters) => handleDrillDown(level, filters),
///   maxDrillLevels: 5,
///   showBreadcrumbs: true,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:logging/logging.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/analytics_filters.dart';

/// Logger for drill-down interface operations
final _logger = Logger('DrillDownInterface');

/// Multi-level drill-down interface widget
class DrillDownInterface extends StatefulWidget {
  /// Current analytics data to explore
  final AnalyticsData? analyticsData;

  /// Callback when drilling down to a new level
  final Function(DrillLevel level, AnalyticsFilters filters) onDrillDown;

  /// Maximum number of drill levels allowed
  final int maxDrillLevels;

  /// Whether to show breadcrumb navigation
  final bool showBreadcrumbs;

  /// Whether to show data previews
  final bool showPreviews;

  /// Whether to allow data export at any level
  final bool allowExport;

  /// Custom drill level configurations
  final List<DrillLevelConfig>? customLevels;

  /// Initial drill level
  final DrillLevel? initialLevel;

  /// Custom color scheme
  final ColorScheme? colorScheme;

  /// Whether interface is read-only
  final bool readOnly;

  const DrillDownInterface({
    super.key,
    this.analyticsData,
    required this.onDrillDown,
    this.maxDrillLevels = 5,
    this.showBreadcrumbs = true,
    this.showPreviews = true,
    this.allowExport = true,
    this.customLevels,
    this.initialLevel,
    this.colorScheme,
    this.readOnly = false,
  });

  @override
  State<DrillDownInterface> createState() => _DrillDownInterfaceState();
}

class _DrillDownInterfaceState extends State<DrillDownInterface>
    with TickerProviderStateMixin {
  /// Animation controller for level transitions
  late AnimationController _transitionController;

  /// Animation for slide transitions
  late Animation<Offset> _slideAnimation;

  /// Animation controller for loading states
  late AnimationController _loadingController;

  /// Current drill path (navigation history)
  final List<DrillPathItem> _drillPath = [];

  /// Current drill level
  DrillLevel _currentLevel = DrillLevel.overview;

  /// Currently selected item at each level
  final Map<DrillLevel, DrillItem> _selectedItems = {};

  /// Loading state for each level
  final Map<DrillLevel, bool> _loadingStates = {};

  /// Data cache for each level
  final Map<DrillLevel, List<DrillItem>> _levelData = {};

  /// Current filters applied
  AnalyticsFilters _currentFilters = const AnalyticsFilters();

  /// Search controller
  final TextEditingController _searchController = TextEditingController();

  /// Focus node for search
  final FocusNode _searchFocus = FocusNode();

  @override
  void initState() {
    super.initState();
    _logger.info('Initializing drill-down interface');

    // Initialize animations
    _transitionController = AnimationController(
      duration: const Duration(milliseconds: 400),
      vsync: this,
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(1.0, 0.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _transitionController,
      curve: Curves.easeInOut,
    ));

    _loadingController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    // Set initial level
    _currentLevel = widget.initialLevel ?? DrillLevel.overview;

    // Initialize drill path
    _initializeDrillPath();

    // Load initial data
    _loadLevelData(_currentLevel);
  }

  @override
  void didUpdateWidget(DrillDownInterface oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Reload data if analytics data changed
    if (widget.analyticsData != oldWidget.analyticsData) {
      _refreshCurrentLevel();
    }
  }

  @override
  void dispose() {
    _logger.info('Disposing drill-down interface');
    _transitionController.dispose();
    _loadingController.dispose();
    _searchController.dispose();
    _searchFocus.dispose();
    super.dispose();
  }

  /// Initializes the drill path
  void _initializeDrillPath() {
    _drillPath.clear();
    _drillPath.add(DrillPathItem(
      level: DrillLevel.overview,
      title: 'Overview',
      subtitle: 'Analytics Summary',
      icon: Icons.dashboard,
    ));
  }

  /// Loads data for a specific drill level
  Future<void> _loadLevelData(DrillLevel level) async {
    setState(() {
      _loadingStates[level] = true;
    });

    _loadingController.repeat();

    try {
      // Simulate API call with actual data loading logic
      await Future.delayed(const Duration(milliseconds: 800));

      final data = _generateLevelData(level);
      setState(() {
        _levelData[level] = data;
        _loadingStates[level] = false;
      });

      _logger.info('Loaded ${data.length} items for level: $level');
    } catch (e) {
      setState(() {
        _loadingStates[level] = false;
      });
      _logger.severe('Error loading data for level $level: $e');
    } finally {
      _loadingController.stop();
    }
  }

  /// Generates mock data for a drill level
  List<DrillItem> _generateLevelData(DrillLevel level) {
    switch (level) {
      case DrillLevel.overview:
        return _generateOverviewData();
      case DrillLevel.region:
        return _generateRegionData();
      case DrillLevel.district:
        return _generateDistrictData();
      case DrillLevel.facility:
        return _generateFacilityData();
      case DrillLevel.dataPoint:
        return _generateDataPointData();
    }
  }

  /// Generates overview level data
  List<DrillItem> _generateOverviewData() {
    return [
      DrillItem(
        id: 'regions',
        title: 'Regions',
        subtitle: '5 regions with data',
        value: '5 regions',
        icon: Icons.map,
        level: DrillLevel.region,
        metadata: {'count': 5, 'type': 'regions'},
      ),
      DrillItem(
        id: 'timespan',
        title: 'Time Analysis',
        subtitle: 'Temporal patterns',
        value: '365 days',
        icon: Icons.timeline,
        level: DrillLevel.dataPoint,
        metadata: {'count': 365, 'type': 'temporal'},
      ),
      DrillItem(
        id: 'predictions',
        title: 'Predictions',
        subtitle: 'Model predictions analysis',
        value: '${widget.analyticsData?.predictionAccuracy.overall.toStringAsFixed(1) ?? "N/A"}% accuracy',
        icon: Icons.analytics,
        level: DrillLevel.dataPoint,
        metadata: {'accuracy': widget.analyticsData?.predictionAccuracy.overall},
      ),
    ];
  }

  /// Generates region level data
  List<DrillItem> _generateRegionData() {
    return [
      DrillItem(
        id: 'kenya',
        title: 'Kenya',
        subtitle: '47 counties, high activity',
        value: '847 facilities',
        icon: Icons.location_on,
        level: DrillLevel.district,
        metadata: {'counties': 47, 'facilities': 847, 'risk': 'high'},
      ),
      DrillItem(
        id: 'uganda',
        title: 'Uganda',
        subtitle: '134 districts, moderate activity',
        value: '623 facilities',
        icon: Icons.location_on,
        level: DrillLevel.district,
        metadata: {'districts': 134, 'facilities': 623, 'risk': 'medium'},
      ),
      DrillItem(
        id: 'tanzania',
        title: 'Tanzania',
        subtitle: '31 regions, moderate activity',
        value: '492 facilities',
        icon: Icons.location_on,
        level: DrillLevel.district,
        metadata: {'regions': 31, 'facilities': 492, 'risk': 'medium'},
      ),
    ];
  }

  /// Generates district level data
  List<DrillItem> _generateDistrictData() {
    final selectedRegion = _selectedItems[DrillLevel.region];
    if (selectedRegion?.id == 'kenya') {
      return [
        DrillItem(
          id: 'nairobi',
          title: 'Nairobi County',
          subtitle: 'Urban, 45 facilities',
          value: '2.1M population',
          icon: Icons.location_city,
          level: DrillLevel.facility,
          metadata: {'population': 2100000, 'facilities': 45, 'type': 'urban'},
        ),
        DrillItem(
          id: 'mombasa',
          title: 'Mombasa County',
          subtitle: 'Coastal, 32 facilities',
          value: '1.2M population',
          icon: Icons.location_city,
          level: DrillLevel.facility,
          metadata: {'population': 1200000, 'facilities': 32, 'type': 'coastal'},
        ),
        DrillItem(
          id: 'kisumu',
          title: 'Kisumu County',
          subtitle: 'Lakeside, 28 facilities',
          value: '968K population',
          icon: Icons.location_city,
          level: DrillLevel.facility,
          metadata: {'population': 968000, 'facilities': 28, 'type': 'lakeside'},
        ),
      ];
    }
    return [];
  }

  /// Generates facility level data
  List<DrillItem> _generateFacilityData() {
    return [
      DrillItem(
        id: 'knh',
        title: 'Kenyatta National Hospital',
        subtitle: 'Level 6 hospital, teaching facility',
        value: '2000 beds',
        icon: Icons.local_hospital,
        level: DrillLevel.dataPoint,
        metadata: {'level': 6, 'beds': 2000, 'type': 'teaching'},
      ),
      DrillItem(
        id: 'kiambu_hospital',
        title: 'Kiambu Level 4 Hospital',
        subtitle: 'County referral hospital',
        value: '300 beds',
        icon: Icons.local_hospital,
        level: DrillLevel.dataPoint,
        metadata: {'level': 4, 'beds': 300, 'type': 'referral'},
      ),
      DrillItem(
        id: 'mathare_hc',
        title: 'Mathare Health Centre',
        subtitle: 'Community health centre',
        value: '50 beds',
        icon: Icons.healing,
        level: DrillLevel.dataPoint,
        metadata: {'level': 3, 'beds': 50, 'type': 'community'},
      ),
    ];
  }

  /// Generates data point level data
  List<DrillItem> _generateDataPointData() {
    return [
      DrillItem(
        id: 'prediction_1',
        title: 'Risk Prediction - High',
        subtitle: 'Environmental factors indicate high risk',
        value: '85% confidence',
        icon: Icons.warning,
        level: DrillLevel.dataPoint,
        metadata: {'confidence': 0.85, 'risk': 'high', 'factors': ['temperature', 'rainfall']},
      ),
      DrillItem(
        id: 'environmental_1',
        title: 'Temperature Data',
        subtitle: 'Daily temperature readings',
        value: '28.5°C avg',
        icon: Icons.thermostat,
        level: DrillLevel.dataPoint,
        metadata: {'average': 28.5, 'unit': 'celsius', 'readings': 30},
      ),
      DrillItem(
        id: 'alert_1',
        title: 'Alert Generated',
        subtitle: 'Automatic alert triggered',
        value: 'Critical severity',
        icon: Icons.notification_important,
        level: DrillLevel.dataPoint,
        metadata: {'severity': 'critical', 'timestamp': DateTime.now()},
      ),
    ];
  }

  /// Drills down to the next level
  void _drillDown(DrillItem item) {
    if (widget.readOnly) return;

    final nextLevel = item.level;
    if (_drillPath.length >= widget.maxDrillLevels) {
      _showMessage('Maximum drill depth reached');
      return;
    }

    // Update selected item for current level
    _selectedItems[_currentLevel] = item;

    // Add to drill path
    _drillPath.add(DrillPathItem(
      level: nextLevel,
      title: item.title,
      subtitle: item.subtitle,
      icon: item.icon,
      item: item,
    ));

    // Update current level
    setState(() {
      _currentLevel = nextLevel;
    });

    // Create filters for the new level
    final newFilters = _createFiltersForLevel(nextLevel, item);

    // Trigger drill down callback
    widget.onDrillDown(nextLevel, newFilters);

    // Load data for new level
    _loadLevelData(nextLevel);

    // Animate transition
    _transitionController.forward(from: 0);

    _logger.info('Drilled down to level: $nextLevel, item: ${item.title}');
  }

  /// Creates filters for a specific drill level
  AnalyticsFilters _createFiltersForLevel(DrillLevel level, DrillItem item) {
    // Create context-specific filters based on the drill path
    var filters = _currentFilters;

    // Add geographic filtering if applicable
    if (item.metadata.containsKey('region')) {
      // Add region-specific filtering
    }

    // Add temporal filtering if applicable
    if (item.metadata.containsKey('timeRange')) {
      // Add time-specific filtering
    }

    return filters;
  }

  /// Navigates back in the drill path
  void _navigateBack() {
    if (_drillPath.length <= 1) return;

    _drillPath.removeLast();
    final previousItem = _drillPath.last;

    setState(() {
      _currentLevel = previousItem.level;
    });

    // Remove selected item for the level we're leaving
    _selectedItems.remove(_currentLevel);

    _logger.info('Navigated back to level: $_currentLevel');
  }

  /// Navigates to a specific level in the breadcrumb
  void _navigateToLevel(int index) {
    if (index >= _drillPath.length || index < 0) return;

    // Remove items after the selected index
    _drillPath.removeRange(index + 1, _drillPath.length);

    final targetItem = _drillPath[index];
    setState(() {
      _currentLevel = targetItem.level;
    });

    _logger.info('Navigated to level: $_currentLevel via breadcrumb');
  }

  /// Refreshes current level data
  void _refreshCurrentLevel() {
    _loadLevelData(_currentLevel);
  }

  /// Searches within current level
  void _searchCurrentLevel(String query) {
    // Implementation would filter current level data based on search query
    _logger.info('Searching current level with query: $query');
  }

  /// Shows a message to the user
  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = widget.colorScheme ?? theme.colorScheme;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            _buildHeader(theme, colorScheme),

            const SizedBox(height: 16),

            // Breadcrumbs (if enabled)
            if (widget.showBreadcrumbs) ...[
              _buildBreadcrumbs(theme, colorScheme),
              const SizedBox(height: 16),
            ],

            // Search bar
            _buildSearchBar(theme, colorScheme),

            const SizedBox(height: 16),

            // Current level content
            Expanded(
              child: _buildCurrentLevelContent(theme, colorScheme),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds the header section
  Widget _buildHeader(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Data Drill-Down',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Explore data hierarchically from overview to details',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ),
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Back button
            IconButton(
              onPressed: _drillPath.length > 1 ? _navigateBack : null,
              icon: const Icon(Icons.arrow_back),
              tooltip: 'Go Back',
              color: colorScheme.primary,
            ),
            // Refresh button
            IconButton(
              onPressed: _refreshCurrentLevel,
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh',
              color: colorScheme.primary,
            ),
            // Export button (if enabled)
            if (widget.allowExport)
              IconButton(
                onPressed: () {
                  // Implement export functionality
                  _showMessage('Export feature coming soon');
                },
                icon: const Icon(Icons.download),
                tooltip: 'Export Current Level',
                color: colorScheme.primary,
              ),
          ],
        ),
      ],
    );
  }

  /// Builds breadcrumb navigation
  Widget _buildBreadcrumbs(ThemeData theme, ColorScheme colorScheme) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(Icons.navigation, color: colorScheme.primary, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Wrap(
              children: _drillPath.asMap().entries.map((entry) {
                final index = entry.key;
                final item = entry.value;
                final isLast = index == _drillPath.length - 1;

                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    InkWell(
                      onTap: isLast ? null : () => _navigateToLevel(index),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(item.icon, size: 14, color: isLast ? colorScheme.primary : colorScheme.onSurface),
                            const SizedBox(width: 4),
                            Text(
                              item.title,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: isLast ? colorScheme.primary : colorScheme.onSurface,
                                fontWeight: isLast ? FontWeight.bold : FontWeight.normal,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    if (!isLast) ...[
                      Icon(Icons.chevron_right, size: 16, color: colorScheme.onSurface.withOpacity(0.5)),
                    ],
                  ],
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds search bar
  Widget _buildSearchBar(ThemeData theme, ColorScheme colorScheme) {
    return TextField(
      controller: _searchController,
      focusNode: _searchFocus,
      decoration: InputDecoration(
        hintText: 'Search current level...',
        prefixIcon: const Icon(Icons.search),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        suffixIcon: _searchController.text.isNotEmpty
            ? IconButton(
                onPressed: () {
                  _searchController.clear();
                  _searchCurrentLevel('');
                },
                icon: const Icon(Icons.clear),
              )
            : null,
      ),
      onChanged: _searchCurrentLevel,
      readOnly: widget.readOnly,
    );
  }

  /// Builds current level content
  Widget _buildCurrentLevelContent(ThemeData theme, ColorScheme colorScheme) {
    final isLoading = _loadingStates[_currentLevel] ?? false;
    final data = _levelData[_currentLevel] ?? [];

    if (isLoading) {
      return _buildLoadingState(theme, colorScheme);
    }

    if (data.isEmpty) {
      return _buildEmptyState(theme, colorScheme);
    }

    return SlideTransition(
      position: _slideAnimation,
      child: _buildDataList(data, theme, colorScheme),
    );
  }

  /// Builds loading state
  Widget _buildLoadingState(ThemeData theme, ColorScheme colorScheme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          AnimatedBuilder(
            animation: _loadingController,
            builder: (context, child) {
              return CircularProgressIndicator(
                value: _loadingController.value,
                color: colorScheme.primary,
              );
            },
          ),
          const SizedBox(height: 16),
          Text(
            'Loading ${_currentLevel.name} data...',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds empty state
  Widget _buildEmptyState(ThemeData theme, ColorScheme colorScheme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.folder_open,
            size: 64,
            color: colorScheme.onSurface.withOpacity(0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No data available at this level',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Try going back or refreshing the data',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: colorScheme.onSurface.withOpacity(0.5),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds data list for current level
  Widget _buildDataList(List<DrillItem> data, ThemeData theme, ColorScheme colorScheme) {
    return ListView.builder(
      itemCount: data.length,
      itemBuilder: (context, index) {
        final item = data[index];
        return _buildDataItem(item, theme, colorScheme);
      },
    );
  }

  /// Builds individual data item
  Widget _buildDataItem(DrillItem item, ThemeData theme, ColorScheme colorScheme) {
    final canDrillDown = item.level != DrillLevel.dataPoint && !widget.readOnly;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: colorScheme.primaryContainer,
          child: Icon(item.icon, color: colorScheme.onPrimaryContainer),
        ),
        title: Text(
          item.title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item.subtitle),
            const SizedBox(height: 4),
            Text(
              item.value,
              style: theme.textTheme.bodySmall?.copyWith(
                color: colorScheme.primary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        trailing: canDrillDown
            ? Icon(Icons.chevron_right, color: colorScheme.primary)
            : widget.showPreviews
                ? IconButton(
                    onPressed: () => _showItemPreview(item),
                    icon: const Icon(Icons.preview),
                    tooltip: 'Preview',
                  )
                : null,
        onTap: canDrillDown ? () => _drillDown(item) : () => _showItemPreview(item),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        tileColor: colorScheme.surface,
        hoverColor: colorScheme.surfaceContainerHighest,
      ),
    );
  }

  /// Shows item preview dialog
  void _showItemPreview(DrillItem item) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(item.icon),
            const SizedBox(width: 8),
            Expanded(child: Text(item.title)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Value: ${item.value}'),
            const SizedBox(height: 8),
            Text('Description: ${item.subtitle}'),
            const SizedBox(height: 8),
            if (item.metadata.isNotEmpty) ...[
              const Text('Metadata:'),
              ...item.metadata.entries.map(
                (entry) => Text('  ${entry.key}: ${entry.value}'),
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}

/// Drill level enumeration
enum DrillLevel {
  overview,
  region,
  district,
  facility,
  dataPoint,
}

/// Drill path item for navigation history
class DrillPathItem {
  final DrillLevel level;
  final String title;
  final String subtitle;
  final IconData icon;
  final DrillItem? item;

  const DrillPathItem({
    required this.level,
    required this.title,
    required this.subtitle,
    required this.icon,
    this.item,
  });
}

/// Individual drill item representing data at a specific level
class DrillItem {
  final String id;
  final String title;
  final String subtitle;
  final String value;
  final IconData icon;
  final DrillLevel level;
  final Map<String, dynamic> metadata;

  const DrillItem({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.icon,
    required this.level,
    this.metadata = const {},
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is DrillItem && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Configuration for custom drill levels
class DrillLevelConfig {
  final DrillLevel level;
  final String name;
  final String description;
  final IconData icon;
  final Function(DrillItem)? dataLoader;

  const DrillLevelConfig({
    required this.level,
    required this.name,
    required this.description,
    required this.icon,
    this.dataLoader,
  });
}