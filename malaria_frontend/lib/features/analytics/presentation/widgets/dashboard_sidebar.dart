/// Dashboard sidebar widget for analytics filtering and control panel
///
/// This widget provides a comprehensive sidebar for the analytics dashboard
/// with filtering controls, user preferences, quick actions, and navigation
/// elements integrated with BLoC state management.
///
/// Features:
/// - Dynamic filtering controls for analytics data
/// - User preference management and persistence
/// - Quick action buttons for common tasks
/// - Collapsible sections with state preservation
/// - Real-time filter preview
/// - Accessibility support
/// - Responsive design adaptation
///
/// Usage:
/// ```dart
/// DashboardSidebar(
///   isDrawer: false,
///   deviceType: DashboardDeviceType.desktop,
///   onFiltersChanged: (filters) => _handleFilterChange(filters),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/analytics_filters.dart';
import '../bloc/analytics_bloc.dart';
import 'dashboard_layout.dart';

/// Sidebar section configuration
class SidebarSection {
  /// Section identifier
  final String id;

  /// Section title
  final String title;

  /// Section icon
  final IconData icon;

  /// Whether section is expanded by default
  final bool initiallyExpanded;

  /// Whether section is enabled
  final bool enabled;

  /// Section content widget
  final Widget content;

  /// Section badge count
  final int? badgeCount;

  const SidebarSection({
    required this.id,
    required this.title,
    required this.icon,
    this.initiallyExpanded = true,
    this.enabled = true,
    required this.content,
    this.badgeCount,
  });
}

/// Quick action configuration
class QuickAction {
  /// Action identifier
  final String id;

  /// Action title
  final String title;

  /// Action icon
  final IconData icon;

  /// Action callback
  final VoidCallback onTap;

  /// Whether action is enabled
  final bool enabled;

  /// Action color theme
  final Color? color;

  /// Action tooltip
  final String? tooltip;

  const QuickAction({
    required this.id,
    required this.title,
    required this.icon,
    required this.onTap,
    this.enabled = true,
    this.color,
    this.tooltip,
  });
}

/// Main dashboard sidebar widget
class DashboardSidebar extends StatefulWidget {
  /// Whether sidebar is used as a drawer
  final bool isDrawer;

  /// Current device type for responsive behavior
  final DashboardDeviceType deviceType;

  /// Callback for drawer close (when isDrawer is true)
  final VoidCallback? onClose;

  /// Callback when filters change
  final void Function(AnalyticsFilters filters)? onFiltersChanged;

  /// Callback when region changes
  final void Function(String region)? onRegionChanged;

  /// Callback when date range changes
  final void Function(DateRange dateRange)? onDateRangeChanged;

  /// Custom sidebar sections
  final List<SidebarSection>? customSections;

  /// Whether to show quick actions
  final bool showQuickActions;

  /// Whether to show filter preview
  final bool showFilterPreview;

  /// Whether to persist sidebar state
  final bool persistState;

  const DashboardSidebar({
    super.key,
    this.isDrawer = false,
    this.deviceType = DashboardDeviceType.desktop,
    this.onClose,
    this.onFiltersChanged,
    this.onRegionChanged,
    this.onDateRangeChanged,
    this.customSections,
    this.showQuickActions = true,
    this.showFilterPreview = true,
    this.persistState = true,
  });

  @override
  State<DashboardSidebar> createState() => _DashboardSidebarState();
}

class _DashboardSidebarState extends State<DashboardSidebar> {
  /// Current analytics filters
  AnalyticsFilters _currentFilters = const AnalyticsFilters();

  /// Expanded sections state
  final Map<String, bool> _expandedSections = {};

  /// Selected region
  String _selectedRegion = 'Kenya';

  /// Selected date range
  DateRange _selectedDateRange = DateRange(
    start: DateTime.now().subtract(const Duration(days: 30)),
    end: DateTime.now(),
  );

  /// Available regions list
  List<String> _availableRegions = ['Kenya', 'Tanzania', 'Uganda', 'Rwanda'];

  /// Quick actions list
  late List<QuickAction> _quickActions;

  @override
  void initState() {
    super.initState();
    _initializeQuickActions();
    _loadPersistedState();
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<AnalyticsBloc, AnalyticsState>(
      listener: _handleBlocStateChanges,
      builder: (context, state) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            border: widget.isDrawer
                ? null
                : Border(
                    right: BorderSide(
                      color: Theme.of(context).dividerColor,
                      width: 1,
                    ),
                  ),
          ),
          child: Column(
            children: [
              // Sidebar header
              _buildSidebarHeader(),

              // Sidebar content
              Expanded(
                child: _buildSidebarContent(state),
              ),

              // Sidebar footer
              if (widget.showFilterPreview) _buildSidebarFooter(state),
            ],
          ),
        );
      },
    );
  }

  /// Builds sidebar header with title and actions
  Widget _buildSidebarHeader() {
    return Container(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.tune,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Analytics Controls',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          if (widget.isDrawer && widget.onClose != null)
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: widget.onClose,
              tooltip: 'Close',
            ),
        ],
      ),
    );
  }

  /// Builds main sidebar content
  Widget _buildSidebarContent(AnalyticsState state) {
    final sections = _buildSidebarSections(state);

    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: sections.length,
      itemBuilder: (context, index) => _buildExpandableSection(sections[index]),
    );
  }

  /// Builds sidebar footer with filter preview
  Widget _buildSidebarFooter(AnalyticsState state) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border(
          top: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Active Filters',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
          const SizedBox(height: 8),
          _buildFilterPreview(),
        ],
      ),
    );
  }

  /// Builds sidebar sections list
  List<SidebarSection> _buildSidebarSections(AnalyticsState state) {
    final sections = <SidebarSection>[
      // Region and Date Selection
      SidebarSection(
        id: 'location_time',
        title: 'Location & Time',
        icon: Icons.location_on,
        content: _buildLocationTimeSection(),
      ),

      // Data Filters
      SidebarSection(
        id: 'data_filters',
        title: 'Data Filters',
        icon: Icons.filter_list,
        content: _buildDataFiltersSection(),
      ),

      // Visualization Options
      SidebarSection(
        id: 'visualization',
        title: 'Visualization',
        icon: Icons.bar_chart,
        content: _buildVisualizationSection(),
      ),

      // Export Options
      SidebarSection(
        id: 'export',
        title: 'Export & Reports',
        icon: Icons.download,
        content: _buildExportSection(),
      ),
    ];

    // Add quick actions section
    if (widget.showQuickActions) {
      sections.insert(0, SidebarSection(
        id: 'quick_actions',
        title: 'Quick Actions',
        icon: Icons.flash_on,
        content: _buildQuickActionsSection(),
        initiallyExpanded: false,
      ));
    }

    // Add custom sections
    if (widget.customSections != null) {
      sections.addAll(widget.customSections!);
    }

    return sections;
  }

  /// Builds expandable section widget
  Widget _buildExpandableSection(SidebarSection section) {
    final isExpanded = _expandedSections[section.id] ?? section.initiallyExpanded;

    return ExpansionTile(
      key: ValueKey(section.id),
      leading: Icon(section.icon),
      title: Row(
        children: [
          Expanded(
            child: Text(
              section.title,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          if (section.badgeCount != null && section.badgeCount! > 0)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.error,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                section.badgeCount.toString(),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onError,
                  fontSize: 10,
                ),
              ),
            ),
        ],
      ),
      initiallyExpanded: isExpanded,
      onExpansionChanged: (expanded) {
        setState(() {
          _expandedSections[section.id] = expanded;
        });
        if (widget.persistState) {
          _savePersistedState();
        }
      },
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: section.content,
        ),
      ],
    );
  }

  /// Builds quick actions section
  Widget _buildQuickActionsSection() {
    return Column(
      children: _quickActions.map((action) => _buildQuickActionTile(action)).toList(),
    );
  }

  /// Builds quick action tile
  Widget _buildQuickActionTile(QuickAction action) {
    return ListTile(
      leading: Icon(
        action.icon,
        color: action.color ?? Theme.of(context).colorScheme.primary,
      ),
      title: Text(action.title),
      onTap: action.enabled ? action.onTap : null,
      enabled: action.enabled,
      dense: true,
    );
  }

  /// Builds location and time section
  Widget _buildLocationTimeSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Region selector
        _buildSectionLabel('Region'),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _selectedRegion,
          items: _availableRegions.map((region) => DropdownMenuItem(
            value: region,
            child: Text(region),
          )).toList(),
          onChanged: (region) {
            if (region != null) {
              setState(() {
                _selectedRegion = region;
              });
              if (widget.onRegionChanged != null) {
                widget.onRegionChanged!(region);
              }
            }
          },
          decoration: const InputDecoration(
            isDense: true,
            border: OutlineInputBorder(),
          ),
        ),

        const SizedBox(height: 16),

        // Date range selector
        _buildSectionLabel('Date Range'),
        const SizedBox(height: 8),
        _buildDateRangeSelector(),
      ],
    );
  }

  /// Builds data filters section
  Widget _buildDataFiltersSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Data types
        _buildSectionLabel('Data Types'),
        const SizedBox(height: 8),
        _buildDataTypeFilters(),

        const SizedBox(height: 16),

        // Risk levels
        _buildSectionLabel('Risk Levels'),
        const SizedBox(height: 8),
        _buildRiskLevelFilters(),

        const SizedBox(height: 16),

        // Environmental factors
        _buildSectionLabel('Environmental Factors'),
        const SizedBox(height: 8),
        _buildEnvironmentalFactorFilters(),
      ],
    );
  }

  /// Builds visualization section
  Widget _buildVisualizationSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Aggregation period
        _buildSectionLabel('Aggregation'),
        const SizedBox(height: 8),
        _buildAggregationSelector(),

        const SizedBox(height: 16),

        // Visualization options
        CheckboxListTile(
          title: const Text('Smooth Data'),
          subtitle: const Text('Apply moving average'),
          value: _currentFilters.smoothData,
          onChanged: (value) => _updateFilters(
            _currentFilters.copyWith(smoothData: value),
          ),
          dense: true,
        ),

        CheckboxListTile(
          title: const Text('Normalize Data'),
          subtitle: const Text('Scale to 0-1 range'),
          value: _currentFilters.normalizeData,
          onChanged: (value) => _updateFilters(
            _currentFilters.copyWith(normalizeData: value),
          ),
          dense: true,
        ),

        CheckboxListTile(
          title: const Text('Confidence Intervals'),
          subtitle: const Text('Show prediction confidence'),
          value: _currentFilters.includeConfidenceIntervals,
          onChanged: (value) => _updateFilters(
            _currentFilters.copyWith(includeConfidenceIntervals: value),
          ),
          dense: true,
        ),
      ],
    );
  }

  /// Builds export section
  Widget _buildExportSection() {
    return Column(
      children: [
        ElevatedButton.icon(
          onPressed: () => _exportData(ExportFormat.pdf),
          icon: const Icon(Icons.picture_as_pdf),
          label: const Text('Export PDF'),
          style: ElevatedButton.styleFrom(
            minimumSize: const Size(double.infinity, 40),
          ),
        ),
        const SizedBox(height: 8),
        ElevatedButton.icon(
          onPressed: () => _exportData(ExportFormat.csv),
          icon: const Icon(Icons.table_chart),
          label: const Text('Export CSV'),
          style: ElevatedButton.styleFrom(
            minimumSize: const Size(double.infinity, 40),
          ),
        ),
        const SizedBox(height: 8),
        ElevatedButton.icon(
          onPressed: () => _exportData(ExportFormat.xlsx),
          icon: const Icon(Icons.grid_on),
          label: const Text('Export Excel'),
          style: ElevatedButton.styleFrom(
            minimumSize: const Size(double.infinity, 40),
          ),
        ),
      ],
    );
  }

  /// Builds section label
  Widget _buildSectionLabel(String label) {
    return Text(
      label,
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
        fontWeight: FontWeight.bold,
        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
      ),
    );
  }

  /// Builds date range selector
  Widget _buildDateRangeSelector() {
    return OutlinedButton(
      onPressed: _showDateRangePicker,
      child: Row(
        children: [
          const Icon(Icons.date_range, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '${_formatDate(_selectedDateRange.start)} - ${_formatDate(_selectedDateRange.end)}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds data type filters
  Widget _buildDataTypeFilters() {
    return Column(
      children: [
        CheckboxListTile(
          title: const Text('Environmental Data'),
          value: _currentFilters.includeEnvironmentalData,
          onChanged: (value) => _updateFilters(
            _currentFilters.copyWith(includeEnvironmentalData: value),
          ),
          dense: true,
        ),
        CheckboxListTile(
          title: const Text('Prediction Accuracy'),
          value: _currentFilters.includePredictionAccuracy,
          onChanged: (value) => _updateFilters(
            _currentFilters.copyWith(includePredictionAccuracy: value),
          ),
          dense: true,
        ),
        CheckboxListTile(
          title: const Text('Risk Trends'),
          value: _currentFilters.includeRiskTrends,
          onChanged: (value) => _updateFilters(
            _currentFilters.copyWith(includeRiskTrends: value),
          ),
          dense: true,
        ),
        CheckboxListTile(
          title: const Text('Alert Statistics'),
          value: _currentFilters.includeAlertStatistics,
          onChanged: (value) => _updateFilters(
            _currentFilters.copyWith(includeAlertStatistics: value),
          ),
          dense: true,
        ),
      ],
    );
  }

  /// Builds risk level filters
  Widget _buildRiskLevelFilters() {
    final selectedRiskLevels = _currentFilters.riskLevels ?? RiskLevel.values;

    return Column(
      children: RiskLevel.values.map((level) {
        return CheckboxListTile(
          title: Text(level.name.toUpperCase()),
          value: selectedRiskLevels.contains(level),
          onChanged: (value) {
            final updatedLevels = List<RiskLevel>.from(selectedRiskLevels);
            if (value == true) {
              updatedLevels.add(level);
            } else {
              updatedLevels.remove(level);
            }
            _updateFilters(_currentFilters.copyWith(riskLevels: updatedLevels));
          },
          dense: true,
        );
      }).toList(),
    );
  }

  /// Builds environmental factor filters
  Widget _buildEnvironmentalFactorFilters() {
    final selectedFactors = _currentFilters.environmentalFactors ?? EnvironmentalFactor.values;

    return Column(
      children: EnvironmentalFactor.values.map((factor) {
        return CheckboxListTile(
          title: Text(factor.name.toUpperCase()),
          value: selectedFactors.contains(factor),
          onChanged: (value) {
            final updatedFactors = List<EnvironmentalFactor>.from(selectedFactors);
            if (value == true) {
              updatedFactors.add(factor);
            } else {
              updatedFactors.remove(factor);
            }
            _updateFilters(_currentFilters.copyWith(environmentalFactors: updatedFactors));
          },
          dense: true,
        );
      }).toList(),
    );
  }

  /// Builds aggregation selector
  Widget _buildAggregationSelector() {
    return DropdownButtonFormField<AggregationPeriod>(
      value: _currentFilters.aggregationPeriod,
      items: AggregationPeriod.values.map((period) => DropdownMenuItem(
        value: period,
        child: Text(period.name.toUpperCase()),
      )).toList(),
      onChanged: (period) {
        if (period != null) {
          _updateFilters(_currentFilters.copyWith(aggregationPeriod: period));
        }
      },
      decoration: const InputDecoration(
        isDense: true,
        border: OutlineInputBorder(),
      ),
    );
  }

  /// Builds filter preview
  Widget _buildFilterPreview() {
    final activeFilters = <String>[];

    if (!_currentFilters.includeEnvironmentalData) activeFilters.add('No Env Data');
    if (!_currentFilters.includePredictionAccuracy) activeFilters.add('No Predictions');
    if (_currentFilters.smoothData) activeFilters.add('Smoothed');
    if (_currentFilters.normalizeData) activeFilters.add('Normalized');

    if (activeFilters.isEmpty) {
      return Text(
        'No active filters',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
        ),
      );
    }

    return Wrap(
      spacing: 4,
      runSpacing: 4,
      children: activeFilters.map((filter) => Chip(
        label: Text(
          filter,
          style: Theme.of(context).textTheme.bodySmall,
        ),
        visualDensity: VisualDensity.compact,
      )).toList(),
    );
  }

  /// Initializes quick actions
  void _initializeQuickActions() {
    _quickActions = [
      QuickAction(
        id: 'refresh',
        title: 'Refresh Data',
        icon: Icons.refresh,
        onTap: _refreshData,
      ),
      QuickAction(
        id: 'reset_filters',
        title: 'Reset Filters',
        icon: Icons.clear_all,
        onTap: _resetFilters,
      ),
      QuickAction(
        id: 'save_preset',
        title: 'Save Preset',
        icon: Icons.bookmark_add,
        onTap: _savePreset,
      ),
    ];
  }

  /// Updates current filters
  void _updateFilters(AnalyticsFilters filters) {
    setState(() {
      _currentFilters = filters;
    });

    if (widget.onFiltersChanged != null) {
      widget.onFiltersChanged!(filters);
    }
  }

  /// Shows date range picker
  void _showDateRangePicker() async {
    final result = await showDateRangePicker(
      context: context,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now(),
      initialDateRange: DateTimeRange(
        start: _selectedDateRange.start,
        end: _selectedDateRange.end,
      ),
    );

    if (result != null) {
      final newDateRange = DateRange(
        start: result.start,
        end: result.end,
      );

      setState(() {
        _selectedDateRange = newDateRange;
      });

      if (widget.onDateRangeChanged != null) {
        widget.onDateRangeChanged!(newDateRange);
      }
    }
  }

  /// Exports data in specified format
  void _exportData(ExportFormat format) {
    context.read<AnalyticsBloc>().add(ExportAnalyticsReport(
      format: format,
      includeCharts: true,
    ));
  }

  /// Refreshes analytics data
  void _refreshData() {
    context.read<AnalyticsBloc>().add(const RefreshAnalyticsData());
  }

  /// Resets all filters to default
  void _resetFilters() {
    _updateFilters(const AnalyticsFilters());
  }

  /// Saves current filter preset
  void _savePreset() {
    // Implementation would save current filters as a preset
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Preset saved!')),
    );
  }

  /// Handles BLoC state changes
  void _handleBlocStateChanges(BuildContext context, AnalyticsState state) {
    if (state is AnalyticsLoaded) {
      if (state.availableRegions != null) {
        setState(() {
          _availableRegions = state.availableRegions!;
        });
      }
    }
  }

  /// Loads persisted state
  void _loadPersistedState() {
    if (!widget.persistState) return;
    // Implementation would load from shared preferences
  }

  /// Saves persisted state
  void _savePersistedState() {
    if (!widget.persistState) return;
    // Implementation would save to shared preferences
  }

  /// Formats date for display
  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}