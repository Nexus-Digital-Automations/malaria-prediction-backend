/// Analytics filters panel widget for filtering dashboard data
///
/// This widget provides an interface for filtering analytics data by
/// region, date range, and various data inclusion options.
///
/// Usage:
/// ```dart
/// AnalyticsFiltersPanel(
///   selectedRegion: 'Kenya',
///   selectedDateRange: dateRange,
///   appliedFilters: filters,
///   onRegionChanged: (region) => handleRegionChange(region),
///   onDateRangeChanged: (range) => handleDateRangeChange(range),
///   onFiltersChanged: (filters) => handleFiltersChange(filters),
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/repositories/analytics_repository.dart';

/// Analytics filters panel widget
class AnalyticsFiltersPanel extends StatefulWidget {
  /// Currently selected region
  final String selectedRegion;

  /// Currently selected date range
  final DateRange selectedDateRange;

  /// Currently applied filters
  final AnalyticsFilters appliedFilters;

  /// Callback when region changes
  final ValueChanged<String> onRegionChanged;

  /// Callback when date range changes
  final ValueChanged<DateRange> onDateRangeChanged;

  /// Callback when filters change
  final ValueChanged<AnalyticsFilters> onFiltersChanged;

  /// Available regions for selection
  final List<String>? availableRegions;

  /// Constructor requiring callbacks
  const AnalyticsFiltersPanel({
    super.key,
    required this.selectedRegion,
    required this.selectedDateRange,
    required this.appliedFilters,
    required this.onRegionChanged,
    required this.onDateRangeChanged,
    required this.onFiltersChanged,
    this.availableRegions,
  });

  @override
  State<AnalyticsFiltersPanel> createState() => _AnalyticsFiltersPanelState();
}

class _AnalyticsFiltersPanelState extends State<AnalyticsFiltersPanel> {
  /// Local copy of filters for immediate UI updates
  late AnalyticsFilters _currentFilters;

  /// Date format for display
  final DateFormat _dateFormat = DateFormat('MMM d, y');

  @override
  void initState() {
    super.initState();
    _currentFilters = widget.appliedFilters;
  }

  @override
  void didUpdateWidget(AnalyticsFiltersPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.appliedFilters != widget.appliedFilters) {
      _currentFilters = widget.appliedFilters;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.filter_list,
                color: Theme.of(context).colorScheme.primary,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'Analytics Filters',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const Spacer(),
              TextButton(
                onPressed: _resetFilters,
                child: const Text('Reset'),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: _applyFilters,
                child: const Text('Apply'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(flex: 2, child: _buildRegionSelector()),
              const SizedBox(width: 16),
              Expanded(flex: 3, child: _buildDateRangeSelector()),
              const SizedBox(width: 16),
              Expanded(flex: 3, child: _buildDataInclusionOptions()),
              const SizedBox(width: 16),
              Expanded(flex: 2, child: _buildAdvancedOptions()),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds region selector dropdown
  Widget _buildRegionSelector() {
    final regions = widget.availableRegions ?? ['Kenya', 'Tanzania', 'Uganda', 'Rwanda'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Region',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        DropdownButtonFormField<String>(
          initialValue: widget.selectedRegion,
          decoration: InputDecoration(
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: Theme.of(context).dividerColor),
            ),
          ),
          items: regions.map((region) {
            return DropdownMenuItem(
              value: region,
              child: Text(region),
            );
          }).toList(),
          onChanged: (region) {
            if (region != null) {
              widget.onRegionChanged(region);
            }
          },
        ),
      ],
    );
  }

  /// Builds date range selector
  Widget _buildDateRangeSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Date Range',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(
              child: InkWell(
                onTap: () => _selectStartDate(),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                  decoration: BoxDecoration(
                    border: Border.all(color: Theme.of(context).dividerColor),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _dateFormat.format(widget.selectedDateRange.start),
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 8),
              child: Text('to'),
            ),
            Expanded(
              child: InkWell(
                onTap: () => _selectEndDate(),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                  decoration: BoxDecoration(
                    border: Border.all(color: Theme.of(context).dividerColor),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _dateFormat.format(widget.selectedDateRange.end),
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds data inclusion options
  Widget _buildDataInclusionOptions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Include Data',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: [
            _buildFilterChip(
              'Predictions',
              _currentFilters.includePredictions,
              (value) => _updateFilters(
                includePredictions: value,
              ),
            ),
            _buildFilterChip(
              'Environment',
              _currentFilters.includeEnvironmental,
              (value) => _updateFilters(
                includeEnvironmental: value,
              ),
            ),
            _buildFilterChip(
              'Risk Data',
              _currentFilters.includeRisk,
              (value) => _updateFilters(
                includeRisk: value,
              ),
            ),
            _buildFilterChip(
              'Alerts',
              _currentFilters.includeAlerts,
              (value) => _updateFilters(
                includeAlerts: value,
              ),
            ),
            _buildFilterChip(
              'Data Quality',
              _currentFilters.includeDataQuality,
              (value) => _updateFilters(
                includeDataQuality: value,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds advanced filter options
  Widget _buildAdvancedOptions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Advanced',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Min Confidence',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
                SizedBox(
                  width: 60,
                  child: TextFormField(
                    initialValue: _currentFilters.minConfidence?.toStringAsFixed(2) ?? '',
                    decoration: const InputDecoration(
                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                    keyboardType: TextInputType.number,
                    onChanged: (value) {
                      final confidence = double.tryParse(value);
                      if (confidence != null && confidence >= 0 && confidence <= 1) {
                        _updateFilters(minConfidence: confidence);
                      }
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Max Age (hrs)',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
                SizedBox(
                  width: 60,
                  child: TextFormField(
                    initialValue: _currentFilters.maxDataAgeHours?.toString() ?? '',
                    decoration: const InputDecoration(
                      contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                    keyboardType: TextInputType.number,
                    onChanged: (value) {
                      final hours = int.tryParse(value);
                      if (hours != null && hours > 0) {
                        _updateFilters(maxDataAgeHours: hours);
                      }
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ],
    );
  }

  /// Builds a filter chip
  Widget _buildFilterChip(String label, bool selected, ValueChanged<bool> onChanged) {
    return FilterChip(
      label: Text(
        label,
        style: const TextStyle(fontSize: 12),
      ),
      selected: selected,
      onSelected: onChanged,
      selectedColor: Theme.of(context).colorScheme.primary.withValues(alpha:0.2),
      checkmarkColor: Theme.of(context).colorScheme.primary,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      visualDensity: VisualDensity.compact,
    );
  }

  /// Selects start date
  Future<void> _selectStartDate() async {
    final selectedDate = await showDatePicker(
      context: context,
      initialDate: widget.selectedDateRange.start,
      firstDate: DateTime.now().subtract(const Duration(days: 365 * 2)),
      lastDate: widget.selectedDateRange.end.subtract(const Duration(days: 1)),
    );

    if (selectedDate != null) {
      widget.onDateRangeChanged(DateRange(
        start: selectedDate,
        end: widget.selectedDateRange.end,
      ),);
    }
  }

  /// Selects end date
  Future<void> _selectEndDate() async {
    final selectedDate = await showDatePicker(
      context: context,
      initialDate: widget.selectedDateRange.end,
      firstDate: widget.selectedDateRange.start.add(const Duration(days: 1)),
      lastDate: DateTime.now(),
    );

    if (selectedDate != null) {
      widget.onDateRangeChanged(DateRange(
        start: widget.selectedDateRange.start,
        end: selectedDate,
      ),);
    }
  }

  /// Updates current filters
  void _updateFilters({
    bool? includePredictions,
    bool? includeEnvironmental,
    bool? includeRisk,
    bool? includeAlerts,
    bool? includeDataQuality,
    double? minConfidence,
    int? maxDataAgeHours,
  }) {
    setState(() {
      _currentFilters = AnalyticsFilters(
        includePredictions: includePredictions ?? _currentFilters.includePredictions,
        includeEnvironmental: includeEnvironmental ?? _currentFilters.includeEnvironmental,
        includeRisk: includeRisk ?? _currentFilters.includeRisk,
        includeAlerts: includeAlerts ?? _currentFilters.includeAlerts,
        includeDataQuality: includeDataQuality ?? _currentFilters.includeDataQuality,
        minConfidence: minConfidence ?? _currentFilters.minConfidence,
        maxDataAgeHours: maxDataAgeHours ?? _currentFilters.maxDataAgeHours,
      );
    });
  }

  /// Applies current filters
  void _applyFilters() {
    widget.onFiltersChanged(_currentFilters);
  }

  /// Resets filters to default
  void _resetFilters() {
    setState(() {
      _currentFilters = const AnalyticsFilters();
    });
    widget.onFiltersChanged(_currentFilters);
  }
}