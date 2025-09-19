/// Advanced Filter Panel widget for interactive data exploration
///
/// This widget provides comprehensive filtering capabilities including
/// dynamic filter creation, real-time filtering, filter combinations,
/// and filter management for malaria prediction analytics.
///
/// Usage:
/// ```dart
/// FilterPanelWidget(
///   appliedFilters: currentFilters,
///   onFiltersChanged: (filters) => updateFilters(filters),
///   availableFields: dataFields,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../domain/entities/data_explorer.dart';

/// Advanced filter panel with comprehensive filtering capabilities
class FilterPanelWidget extends StatefulWidget {
  /// Currently applied filters
  final List<FilterCriteria> appliedFilters;

  /// Callback for filter changes
  final Function(List<FilterCriteria>) onFiltersChanged;

  /// Available fields for filtering
  final List<FilterableField>? availableFields;

  /// Whether the panel is in read-only mode
  final bool readOnly;

  /// Theme configuration
  final FilterPanelThemeData? theme;

  /// Maximum number of filters allowed
  final int maxFilters;

  /// Whether to show quick filter suggestions
  final bool showQuickFilters;

  /// Preset filter configurations
  final List<FilterPreset>? presets;

  /// Callback for filter validation
  final bool Function(FilterCriteria)? onFilterValidate;

  const FilterPanelWidget({
    super.key,
    required this.appliedFilters,
    required this.onFiltersChanged,
    this.availableFields,
    this.readOnly = false,
    this.theme,
    this.maxFilters = 20,
    this.showQuickFilters = true,
    this.presets,
    this.onFilterValidate,
  });

  @override
  State<FilterPanelWidget> createState() => _FilterPanelWidgetState();
}

class _FilterPanelWidgetState extends State<FilterPanelWidget>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  /// Current working filters (includes unsaved changes)
  List<FilterCriteria> _workingFilters = [];

  /// Filter being edited
  FilterCriteria? _editingFilter;

  /// Search controller for fields
  final TextEditingController _fieldSearchController = TextEditingController();

  /// Available fields for filtering
  List<FilterableField> _availableFields = [];

  /// Filtered available fields based on search
  List<FilterableField> _filteredFields = [];

  /// Quick filter suggestions
  List<QuickFilter> _quickFilters = [];

  /// Filter combination mode
  FilterCombinationMode _combinationMode = FilterCombinationMode.and;

  /// Whether advanced mode is enabled
  bool _advancedMode = false;

  /// Scroll controller for filter list
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _initializeData();
    _setupListeners();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _fieldSearchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _initializeAnimations() {
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

    _animationController.forward();
  }

  void _initializeData() {
    _workingFilters = List.from(widget.appliedFilters);
    _availableFields = widget.availableFields ?? _getDefaultFields();
    _filteredFields = List.from(_availableFields);
    _generateQuickFilters();
  }

  void _setupListeners() {
    _fieldSearchController.addListener(_onFieldSearchChanged);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _fadeAnimation,
      builder: (context, child) {
        return Opacity(
          opacity: _fadeAnimation.value,
          child: _buildFilterPanel(),
        );
      },
    );
  }

  Widget _buildFilterPanel() {
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
          // Filter panel header
          _buildFilterHeader(),

          // Quick filters section
          if (widget.showQuickFilters && _quickFilters.isNotEmpty)
            _buildQuickFiltersSection(),

          // Active filters section
          if (_workingFilters.isNotEmpty)
            _buildActiveFiltersSection(),

          // Add filter section
          if (!widget.readOnly)
            _buildAddFilterSection(),

          // Filter presets section
          if (widget.presets?.isNotEmpty == true)
            _buildPresetsSection(),
        ],
      ),
    );
  }

  Widget _buildFilterHeader() {
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
            Icons.filter_list,
            size: 18,
            color: widget.theme?.iconColor ?? Colors.grey.shade700,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Filters (${_workingFilters.length})',
              style: widget.theme?.headerTextStyle ?? const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ),

          // Combination mode selector
          if (_workingFilters.length > 1 && _advancedMode)
            _buildCombinationModeSelector(),

          // Advanced mode toggle
          IconButton(
            icon: Icon(
              _advancedMode ? Icons.settings : Icons.settings_outlined,
              size: 16,
            ),
            onPressed: () => setState(() => _advancedMode = !_advancedMode),
            tooltip: 'Advanced Options',
          ),

          // Clear all filters
          if (_workingFilters.isNotEmpty && !widget.readOnly)
            IconButton(
              icon: const Icon(Icons.clear_all, size: 16),
              onPressed: _clearAllFilters,
              tooltip: 'Clear All Filters',
            ),
        ],
      ),
    );
  }

  Widget _buildCombinationModeSelector() {
    return SegmentedButton<FilterCombinationMode>(
      segments: const [
        ButtonSegment(
          value: FilterCombinationMode.and,
          label: Text('AND', style: TextStyle(fontSize: 12)),
        ),
        ButtonSegment(
          value: FilterCombinationMode.or,
          label: Text('OR', style: TextStyle(fontSize: 12)),
        ),
      ],
      selected: {_combinationMode},
      onSelectionChanged: (selected) {
        setState(() {
          _combinationMode = selected.first;
        });
      },
      style: ButtonStyle(
        visualDensity: VisualDensity.compact,
        textStyle: MaterialStateProperty.all(const TextStyle(fontSize: 10)),
      ),
    );
  }

  Widget _buildQuickFiltersSection() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: widget.theme?.quickFilterBackgroundColor ?? Colors.blue.shade50,
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
            'Quick Filters',
            style: widget.theme?.sectionHeaderStyle ?? const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.blue,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: _quickFilters.map(_buildQuickFilterChip).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickFilterChip(QuickFilter quickFilter) {
    final isApplied = _workingFilters.any((f) => f.fieldName == quickFilter.fieldName);

    return FilterChip(
      label: Text(
        quickFilter.label,
        style: const TextStyle(fontSize: 12),
      ),
      selected: isApplied,
      onSelected: widget.readOnly ? null : (selected) {
        if (selected) {
          _applyQuickFilter(quickFilter);
        } else {
          _removeFilterByField(quickFilter.fieldName);
        }
      },
      avatar: Icon(
        quickFilter.icon,
        size: 14,
        color: isApplied ? Colors.white : Colors.grey.shade600,
      ),
      backgroundColor: widget.theme?.quickFilterBackgroundColor,
      selectedColor: widget.theme?.primaryColor ?? Colors.blue,
    );
  }

  Widget _buildActiveFiltersSection() {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 12),
            Text(
              'Active Filters',
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
                itemCount: _workingFilters.length,
                itemBuilder: (context, index) {
                  return _buildFilterItem(_workingFilters[index], index);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterItem(FilterCriteria filter, int index) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: widget.theme?.filterItemBackgroundColor ?? Colors.grey.shade50,
        border: Border.all(
          color: widget.theme?.borderColor ?? Colors.grey.shade300,
        ),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(
        children: [
          // Filter header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                // Filter priority indicator
                Container(
                  width: 4,
                  height: 20,
                  decoration: BoxDecoration(
                    color: _getFilterPriorityColor(filter.priority),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: 8),

                // Filter icon
                Icon(
                  _getFilterIcon(filter.operation),
                  size: 16,
                  color: widget.theme?.iconColor ?? Colors.grey.shade600,
                ),
                const SizedBox(width: 8),

                // Filter display name
                Expanded(
                  child: Text(
                    filter.displayName,
                    style: widget.theme?.filterNameStyle ?? const TextStyle(
                      fontWeight: FontWeight.w500,
                      fontSize: 13,
                    ),
                  ),
                ),

                // Filter active toggle
                Switch(
                  value: filter.isActive,
                  onChanged: widget.readOnly ? null : (value) {
                    _updateFilterActive(index, value);
                  },
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),

                // Filter actions
                PopupMenuButton<String>(
                  icon: Icon(
                    Icons.more_vert,
                    size: 16,
                    color: widget.theme?.iconColor ?? Colors.grey.shade600,
                  ),
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'edit',
                      child: Row(
                        children: [
                          Icon(Icons.edit, size: 14),
                          SizedBox(width: 8),
                          Text('Edit', style: TextStyle(fontSize: 12)),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'duplicate',
                      child: Row(
                        children: [
                          Icon(Icons.copy, size: 14),
                          SizedBox(width: 8),
                          Text('Duplicate', style: TextStyle(fontSize: 12)),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete, size: 14, color: Colors.red),
                          SizedBox(width: 8),
                          Text('Delete', style: TextStyle(fontSize: 12, color: Colors.red)),
                        ],
                      ),
                    ),
                  ],
                  onSelected: (action) => _handleFilterAction(filter, index, action),
                ),
              ],
            ),
          ),

          // Filter details
          _buildFilterDetails(filter, index),
        ],
      ),
    );
  }

  Widget _buildFilterDetails(FilterCriteria filter, int index) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Operation and value display
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: widget.theme?.operationBackgroundColor ?? Colors.blue.shade100,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  _getOperationDisplayName(filter.operation),
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: widget.theme?.operationTextColor ?? Colors.blue.shade800,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  _getFilterValueDisplay(filter),
                  style: widget.theme?.filterValueStyle ?? const TextStyle(
                    fontSize: 12,
                    color: Colors.black87,
                  ),
                ),
              ),
            ],
          ),

          // Advanced options (if enabled)
          if (_advancedMode)
            _buildAdvancedFilterOptions(filter, index),
        ],
      ),
    );
  }

  Widget _buildAdvancedFilterOptions(FilterCriteria filter, int index) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: widget.theme?.advancedOptionsBackgroundColor ?? Colors.grey.shade100,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Advanced Options',
            style: widget.theme?.advancedHeaderStyle ?? const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              // Priority selector
              Text('Priority:', style: TextStyle(fontSize: 10, color: Colors.grey.shade700)),
              const SizedBox(width: 4),
              DropdownButton<int>(
                value: filter.priority,
                style: const TextStyle(fontSize: 10),
                underline: const SizedBox(),
                items: List.generate(5, (i) => DropdownMenuItem(
                  value: i,
                  child: Text('$i', style: const TextStyle(fontSize: 10)),
                )),
                onChanged: widget.readOnly ? null : (value) {
                  if (value != null) {
                    _updateFilterPriority(index, value);
                  }
                },
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAddFilterSection() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: widget.theme?.addFilterBackgroundColor ?? Colors.green.shade50,
        border: Border(
          top: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade200,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.add_circle_outline,
                size: 16,
                color: widget.theme?.addFilterIconColor ?? Colors.green.shade700,
              ),
              const SizedBox(width: 8),
              Text(
                'Add Filter',
                style: widget.theme?.addFilterHeaderStyle ?? TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Colors.green.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Field search
          TextField(
            controller: _fieldSearchController,
            decoration: InputDecoration(
              hintText: 'Search fields...',
              hintStyle: const TextStyle(fontSize: 12),
              prefixIcon: const Icon(Icons.search, size: 16),
              suffixIcon: _fieldSearchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 16),
                      onPressed: () {
                        _fieldSearchController.clear();
                        _onFieldSearchChanged();
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
            onChanged: (_) => _onFieldSearchChanged(),
          ),
          const SizedBox(height: 8),

          // Available fields
          if (_filteredFields.isNotEmpty)
            Container(
              height: 120,
              child: ListView.builder(
                itemCount: _filteredFields.length,
                itemBuilder: (context, index) {
                  return _buildAvailableFieldItem(_filteredFields[index]);
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildAvailableFieldItem(FilterableField field) {
    return ListTile(
      dense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 8),
      leading: Icon(
        _getDataTypeIcon(field.dataType),
        size: 16,
        color: _getDataTypeColor(field.dataType),
      ),
      title: Text(
        field.displayName,
        style: const TextStyle(fontSize: 12),
      ),
      subtitle: Text(
        field.description ?? field.fieldName,
        style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
      ),
      trailing: Icon(
        Icons.add,
        size: 16,
        color: widget.theme?.addFilterIconColor ?? Colors.green.shade700,
      ),
      onTap: () => _showAddFilterDialog(field),
    );
  }

  Widget _buildPresetsSection() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: widget.theme?.presetBackgroundColor ?? Colors.purple.shade50,
        border: Border(
          top: BorderSide(
            color: widget.theme?.borderColor ?? Colors.grey.shade200,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Filter Presets',
            style: widget.theme?.presetHeaderStyle ?? TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.purple.shade700,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: widget.presets!.map(_buildPresetChip).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildPresetChip(FilterPreset preset) {
    return ActionChip(
      label: Text(
        preset.name,
        style: const TextStyle(fontSize: 12),
      ),
      avatar: Icon(preset.icon, size: 14),
      onPressed: () => _applyPreset(preset),
      backgroundColor: widget.theme?.presetChipBackgroundColor,
    );
  }

  // Event handlers

  void _onFieldSearchChanged() {
    final query = _fieldSearchController.text.toLowerCase();
    setState(() {
      _filteredFields = _availableFields.where((field) {
        return field.displayName.toLowerCase().contains(query) ||
               field.fieldName.toLowerCase().contains(query) ||
               (field.description?.toLowerCase().contains(query) ?? false);
      }).toList();
    });
  }

  void _applyQuickFilter(QuickFilter quickFilter) {
    final filter = quickFilter.createFilter();
    if (widget.onFilterValidate?.call(filter) ?? true) {
      setState(() {
        _workingFilters.add(filter);
      });
      _notifyFiltersChanged();
    }
  }

  void _removeFilterByField(String fieldName) {
    setState(() {
      _workingFilters.removeWhere((f) => f.fieldName == fieldName);
    });
    _notifyFiltersChanged();
  }

  void _clearAllFilters() {
    setState(() {
      _workingFilters.clear();
    });
    _notifyFiltersChanged();
  }

  void _updateFilterActive(int index, bool isActive) {
    setState(() {
      _workingFilters[index] = _workingFilters[index].copyWith(isActive: isActive);
    });
    _notifyFiltersChanged();
  }

  void _updateFilterPriority(int index, int priority) {
    setState(() {
      _workingFilters[index] = _workingFilters[index].copyWith(priority: priority);
    });
    _notifyFiltersChanged();
  }

  void _handleFilterAction(FilterCriteria filter, int index, String action) {
    switch (action) {
      case 'edit':
        _editFilter(filter, index);
        break;
      case 'duplicate':
        _duplicateFilter(filter);
        break;
      case 'delete':
        _deleteFilter(index);
        break;
    }
  }

  void _editFilter(FilterCriteria filter, int index) {
    _showEditFilterDialog(filter, index);
  }

  void _duplicateFilter(FilterCriteria filter) {
    final duplicatedFilter = filter.copyWith(
      displayName: '${filter.displayName} (Copy)',
    );
    setState(() {
      _workingFilters.add(duplicatedFilter);
    });
    _notifyFiltersChanged();
  }

  void _deleteFilter(int index) {
    setState(() {
      _workingFilters.removeAt(index);
    });
    _notifyFiltersChanged();
  }

  void _showAddFilterDialog(FilterableField field) {
    // Show dialog to create new filter for the field
    showDialog(
      context: context,
      builder: (context) => _FilterDialog(
        field: field,
        onFilterCreated: (filter) {
          if (widget.onFilterValidate?.call(filter) ?? true) {
            setState(() {
              _workingFilters.add(filter);
            });
            _notifyFiltersChanged();
          }
        },
      ),
    );
  }

  void _showEditFilterDialog(FilterCriteria filter, int index) {
    showDialog(
      context: context,
      builder: (context) => _FilterDialog(
        field: _getFieldForFilter(filter),
        initialFilter: filter,
        onFilterCreated: (updatedFilter) {
          setState(() {
            _workingFilters[index] = updatedFilter;
          });
          _notifyFiltersChanged();
        },
      ),
    );
  }

  void _applyPreset(FilterPreset preset) {
    setState(() {
      _workingFilters = List.from(preset.filters);
    });
    _notifyFiltersChanged();
  }

  void _notifyFiltersChanged() {
    widget.onFiltersChanged(_workingFilters);
  }

  // Helper methods

  List<FilterableField> _getDefaultFields() {
    return [
      FilterableField(
        fieldName: 'region',
        displayName: 'Region',
        dataType: FilterDataType.categorical,
        description: 'Geographic region',
      ),
      FilterableField(
        fieldName: 'risk_score',
        displayName: 'Risk Score',
        dataType: FilterDataType.numeric,
        description: 'Malaria risk score',
      ),
      FilterableField(
        fieldName: 'date',
        displayName: 'Date',
        dataType: FilterDataType.datetime,
        description: 'Prediction date',
      ),
      FilterableField(
        fieldName: 'temperature',
        displayName: 'Temperature',
        dataType: FilterDataType.numeric,
        description: 'Average temperature',
      ),
      FilterableField(
        fieldName: 'rainfall',
        displayName: 'Rainfall',
        dataType: FilterDataType.numeric,
        description: 'Rainfall amount',
      ),
    ];
  }

  void _generateQuickFilters() {
    _quickFilters = [
      QuickFilter(
        label: 'High Risk',
        fieldName: 'risk_score',
        icon: Icons.warning,
        createFilter: () => FilterCriteria.range(
          fieldName: 'risk_score',
          displayName: 'High Risk Areas',
          minValue: 0.7,
          maxValue: 1.0,
        ),
      ),
      QuickFilter(
        label: 'Recent',
        fieldName: 'date',
        icon: Icons.schedule,
        createFilter: () => FilterCriteria.dateRange(
          fieldName: 'date',
          displayName: 'Recent Data',
          startDate: DateTime.now().subtract(const Duration(days: 30)),
          endDate: DateTime.now(),
        ),
      ),
      QuickFilter(
        label: 'High Temp',
        fieldName: 'temperature',
        icon: Icons.thermostat,
        createFilter: () => FilterCriteria.range(
          fieldName: 'temperature',
          displayName: 'High Temperature',
          minValue: 30.0,
          maxValue: 50.0,
        ),
      ),
    ];
  }

  Color _getFilterPriorityColor(int priority) {
    switch (priority) {
      case 0: return Colors.grey;
      case 1: return Colors.blue;
      case 2: return Colors.orange;
      case 3: return Colors.red;
      case 4: return Colors.purple;
      default: return Colors.grey;
    }
  }

  IconData _getFilterIcon(FilterOperation operation) {
    switch (operation) {
      case FilterOperation.equals: return Icons.drag_handle;
      case FilterOperation.notEquals: return Icons.not_equal;
      case FilterOperation.greaterThan: return Icons.keyboard_arrow_right;
      case FilterOperation.lessThan: return Icons.keyboard_arrow_left;
      case FilterOperation.range: return Icons.unfold_more;
      case FilterOperation.inList: return Icons.list;
      case FilterOperation.contains: return Icons.search;
      case FilterOperation.dateRange: return Icons.date_range;
      default: return Icons.filter_alt;
    }
  }

  String _getOperationDisplayName(FilterOperation operation) {
    switch (operation) {
      case FilterOperation.equals: return 'equals';
      case FilterOperation.notEquals: return 'not equals';
      case FilterOperation.greaterThan: return '>';
      case FilterOperation.lessThan: return '<';
      case FilterOperation.greaterThanOrEqual: return '>=';
      case FilterOperation.lessThanOrEqual: return '<=';
      case FilterOperation.range: return 'range';
      case FilterOperation.inList: return 'in';
      case FilterOperation.notInList: return 'not in';
      case FilterOperation.contains: return 'contains';
      case FilterOperation.startsWith: return 'starts with';
      case FilterOperation.endsWith: return 'ends with';
      case FilterOperation.isNull: return 'is null';
      case FilterOperation.isNotNull: return 'is not null';
      case FilterOperation.dateRange: return 'date range';
    }
  }

  String _getFilterValueDisplay(FilterCriteria filter) {
    if (filter.value == null) return 'null';

    switch (filter.operation) {
      case FilterOperation.range:
        final range = filter.value as Map<String, dynamic>;
        return '${range['min']} - ${range['max']}';
      case FilterOperation.dateRange:
        final range = filter.value as Map<String, DateTime>;
        return '${_formatDate(range['start']!)} - ${_formatDate(range['end']!)}';
      case FilterOperation.inList:
      case FilterOperation.notInList:
        final list = filter.value as List;
        return list.take(3).join(', ') + (list.length > 3 ? '...' : '');
      default:
        return filter.value.toString();
    }
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }

  IconData _getDataTypeIcon(FilterDataType dataType) {
    switch (dataType) {
      case FilterDataType.text: return Icons.text_fields;
      case FilterDataType.numeric: return Icons.numbers;
      case FilterDataType.datetime: return Icons.calendar_today;
      case FilterDataType.boolean: return Icons.toggle_on;
      case FilterDataType.categorical: return Icons.category;
    }
  }

  Color _getDataTypeColor(FilterDataType dataType) {
    switch (dataType) {
      case FilterDataType.text: return Colors.blue;
      case FilterDataType.numeric: return Colors.green;
      case FilterDataType.datetime: return Colors.purple;
      case FilterDataType.boolean: return Colors.orange;
      case FilterDataType.categorical: return Colors.teal;
    }
  }

  FilterableField _getFieldForFilter(FilterCriteria filter) {
    return _availableFields.firstWhere(
      (field) => field.fieldName == filter.fieldName,
      orElse: () => FilterableField(
        fieldName: filter.fieldName,
        displayName: filter.displayName,
        dataType: filter.dataType,
      ),
    );
  }
}

// Supporting classes

class FilterableField {
  final String fieldName;
  final String displayName;
  final FilterDataType dataType;
  final String? description;
  final List<dynamic>? allowedValues;
  final dynamic minValue;
  final dynamic maxValue;

  const FilterableField({
    required this.fieldName,
    required this.displayName,
    required this.dataType,
    this.description,
    this.allowedValues,
    this.minValue,
    this.maxValue,
  });
}

class QuickFilter {
  final String label;
  final String fieldName;
  final IconData icon;
  final FilterCriteria Function() createFilter;

  const QuickFilter({
    required this.label,
    required this.fieldName,
    required this.icon,
    required this.createFilter,
  });
}

class FilterPreset {
  final String name;
  final String description;
  final IconData icon;
  final List<FilterCriteria> filters;

  const FilterPreset({
    required this.name,
    required this.description,
    required this.icon,
    required this.filters,
  });
}

enum FilterCombinationMode { and, or }

class FilterPanelThemeData {
  final Color backgroundColor;
  final Color headerBackgroundColor;
  final Color borderColor;
  final Color iconColor;
  final Color primaryColor;
  final Color quickFilterBackgroundColor;
  final Color filterItemBackgroundColor;
  final Color operationBackgroundColor;
  final Color operationTextColor;
  final Color advancedOptionsBackgroundColor;
  final Color addFilterBackgroundColor;
  final Color addFilterIconColor;
  final Color presetBackgroundColor;
  final Color presetChipBackgroundColor;
  final TextStyle headerTextStyle;
  final TextStyle sectionHeaderStyle;
  final TextStyle filterNameStyle;
  final TextStyle filterValueStyle;
  final TextStyle advancedHeaderStyle;
  final TextStyle addFilterHeaderStyle;
  final TextStyle presetHeaderStyle;

  const FilterPanelThemeData({
    this.backgroundColor = Colors.white,
    this.headerBackgroundColor = const Color(0xFFF5F5F5),
    this.borderColor = const Color(0xFFE0E0E0),
    this.iconColor = const Color(0xFF757575),
    this.primaryColor = Colors.blue,
    this.quickFilterBackgroundColor = const Color(0xFFE3F2FD),
    this.filterItemBackgroundColor = const Color(0xFFF5F5F5),
    this.operationBackgroundColor = const Color(0xFFE3F2FD),
    this.operationTextColor = const Color(0xFF1565C0),
    this.advancedOptionsBackgroundColor = const Color(0xFFF0F0F0),
    this.addFilterBackgroundColor = const Color(0xFFE8F5E8),
    this.addFilterIconColor = const Color(0xFF2E7D32),
    this.presetBackgroundColor = const Color(0xFFF3E5F5),
    this.presetChipBackgroundColor = const Color(0xFFE1BEE7),
    this.headerTextStyle = const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
    this.sectionHeaderStyle = const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
    this.filterNameStyle = const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
    this.filterValueStyle = const TextStyle(fontSize: 12),
    this.advancedHeaderStyle = const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
    this.addFilterHeaderStyle = const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
    this.presetHeaderStyle = const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
  });
}

// Filter dialog for creating/editing filters
class _FilterDialog extends StatefulWidget {
  final FilterableField field;
  final FilterCriteria? initialFilter;
  final Function(FilterCriteria) onFilterCreated;

  const _FilterDialog({
    required this.field,
    this.initialFilter,
    required this.onFilterCreated,
  });

  @override
  State<_FilterDialog> createState() => _FilterDialogState();
}

class _FilterDialogState extends State<_FilterDialog> {
  late FilterOperation _selectedOperation;
  dynamic _filterValue;
  late TextEditingController _valueController;

  @override
  void initState() {
    super.initState();
    _selectedOperation = widget.initialFilter?.operation ?? _getDefaultOperation();
    _filterValue = widget.initialFilter?.value;
    _valueController = TextEditingController(
      text: _filterValue?.toString() ?? '',
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('${widget.initialFilter == null ? 'Add' : 'Edit'} Filter'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Field info
          Text('Field: ${widget.field.displayName}'),
          const SizedBox(height: 16),

          // Operation selector
          DropdownButtonFormField<FilterOperation>(
            value: _selectedOperation,
            decoration: const InputDecoration(labelText: 'Operation'),
            items: _getAvailableOperations().map((op) {
              return DropdownMenuItem(
                value: op,
                child: Text(_getOperationDisplayName(op)),
              );
            }).toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() {
                  _selectedOperation = value;
                });
              }
            },
          ),
          const SizedBox(height: 16),

          // Value input
          _buildValueInput(),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _createFilter,
          child: Text(widget.initialFilter == null ? 'Add' : 'Update'),
        ),
      ],
    );
  }

  Widget _buildValueInput() {
    // Build appropriate input widget based on operation and data type
    return TextField(
      controller: _valueController,
      decoration: const InputDecoration(labelText: 'Value'),
      onChanged: (value) => _filterValue = value,
    );
  }

  List<FilterOperation> _getAvailableOperations() {
    switch (widget.field.dataType) {
      case FilterDataType.numeric:
        return [
          FilterOperation.equals,
          FilterOperation.notEquals,
          FilterOperation.greaterThan,
          FilterOperation.lessThan,
          FilterOperation.greaterThanOrEqual,
          FilterOperation.lessThanOrEqual,
          FilterOperation.range,
        ];
      case FilterDataType.text:
        return [
          FilterOperation.equals,
          FilterOperation.notEquals,
          FilterOperation.contains,
          FilterOperation.startsWith,
          FilterOperation.endsWith,
        ];
      case FilterDataType.datetime:
        return [
          FilterOperation.equals,
          FilterOperation.greaterThan,
          FilterOperation.lessThan,
          FilterOperation.dateRange,
        ];
      case FilterDataType.categorical:
        return [
          FilterOperation.equals,
          FilterOperation.notEquals,
          FilterOperation.inList,
          FilterOperation.notInList,
        ];
      case FilterDataType.boolean:
        return [
          FilterOperation.equals,
          FilterOperation.notEquals,
        ];
    }
  }

  FilterOperation _getDefaultOperation() {
    switch (widget.field.dataType) {
      case FilterDataType.numeric:
        return FilterOperation.equals;
      case FilterDataType.text:
        return FilterOperation.contains;
      case FilterDataType.datetime:
        return FilterOperation.dateRange;
      case FilterDataType.categorical:
        return FilterOperation.equals;
      case FilterDataType.boolean:
        return FilterOperation.equals;
    }
  }

  String _getOperationDisplayName(FilterOperation operation) {
    // Same implementation as in parent widget
    switch (operation) {
      case FilterOperation.equals: return 'Equals';
      case FilterOperation.notEquals: return 'Not Equals';
      case FilterOperation.greaterThan: return 'Greater Than';
      case FilterOperation.lessThan: return 'Less Than';
      case FilterOperation.greaterThanOrEqual: return 'Greater Than or Equal';
      case FilterOperation.lessThanOrEqual: return 'Less Than or Equal';
      case FilterOperation.range: return 'Range';
      case FilterOperation.inList: return 'In List';
      case FilterOperation.notInList: return 'Not In List';
      case FilterOperation.contains: return 'Contains';
      case FilterOperation.startsWith: return 'Starts With';
      case FilterOperation.endsWith: return 'Ends With';
      case FilterOperation.isNull: return 'Is Null';
      case FilterOperation.isNotNull: return 'Is Not Null';
      case FilterOperation.dateRange: return 'Date Range';
    }
  }

  void _createFilter() {
    final filter = FilterCriteria(
      fieldName: widget.field.fieldName,
      displayName: widget.field.displayName,
      operation: _selectedOperation,
      value: _filterValue,
      dataType: widget.field.dataType,
    );

    widget.onFilterCreated(filter);
    Navigator.of(context).pop();
  }
}