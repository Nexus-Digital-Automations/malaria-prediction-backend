/// Interactive date range selector widget for analytics dashboard
///
/// This widget provides a comprehensive date range selection interface
/// with predefined presets, custom range picker, quick options,
/// and validation for analytics data filtering.
///
/// Features:
/// - Predefined date range presets (last 7 days, 30 days, etc.)
/// - Custom date range picker with calendar
/// - Quick action buttons for common ranges
/// - Visual date range preview and validation
/// - Timezone handling and formatting options
/// - Responsive design for mobile and desktop
/// - Integration with analytics date filtering
///
/// Usage:
/// ```dart
/// DateRangeSelector(
///   initialDateRange: currentDateRange,
///   onDateRangeChanged: (dateRange) => updateAnalytics(dateRange),
///   showPresets: true,
///   showQuickOptions: true,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:logging/logging.dart';
import '../../domain/entities/analytics_data.dart';

/// Logger for date range selector operations
final _logger = Logger('DateRangeSelector');

/// Interactive date range selector widget
class DateRangeSelector extends StatefulWidget {
  /// Initial date range selection
  final DateRange? initialDateRange;

  /// Callback when date range is changed
  final ValueChanged<DateRange> onDateRangeChanged;

  /// Whether to show preset date ranges
  final bool showPresets;

  /// Whether to show quick option buttons
  final bool showQuickOptions;

  /// Minimum selectable date
  final DateTime? minDate;

  /// Maximum selectable date
  final DateTime? maxDate;

  /// Maximum allowed date range duration
  final Duration? maxRangeDuration;

  /// Date format for display
  final DateFormat? dateFormat;

  /// Custom preset date ranges
  final List<DateRangePreset>? customPresets;

  /// Whether the selector is read-only
  final bool readOnly;

  /// Custom color scheme
  final ColorScheme? colorScheme;

  /// Whether to show timezone selector
  final bool showTimezone;

  /// Default timezone (if null, uses system timezone)
  final String? defaultTimezone;

  const DateRangeSelector({
    super.key,
    this.initialDateRange,
    required this.onDateRangeChanged,
    this.showPresets = true,
    this.showQuickOptions = true,
    this.minDate,
    this.maxDate,
    this.maxRangeDuration,
    this.dateFormat,
    this.customPresets,
    this.readOnly = false,
    this.colorScheme,
    this.showTimezone = false,
    this.defaultTimezone,
  });

  @override
  State<DateRangeSelector> createState() => _DateRangeSelectorState();
}

class _DateRangeSelectorState extends State<DateRangeSelector>
    with TickerProviderStateMixin {
  /// Animation controller for UI transitions
  late AnimationController _animationController;

  /// Animation for preset panel expansion
  late Animation<double> _presetsAnimation;

  /// Tab controller for selection modes
  late TabController _tabController;

  /// Current selected date range
  DateRange? _selectedDateRange;

  /// Currently selected preset (if any)
  DateRangePreset? _selectedPreset;

  /// Whether presets panel is expanded
  bool _presetsExpanded = true;

  /// Date format for display
  late DateFormat _dateFormat;

  /// Available timezone (simplified for demo)
  String _selectedTimezone = 'UTC';

  /// Form key for validation
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  /// Text controllers for custom date inputs
  final TextEditingController _startDateController = TextEditingController();
  final TextEditingController _endDateController = TextEditingController();

  /// Focus nodes for date inputs
  final FocusNode _startDateFocus = FocusNode();
  final FocusNode _endDateFocus = FocusNode();

  @override
  void initState() {
    super.initState();
    _logger.info('Initializing date range selector');

    // Initialize animations
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _presetsAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );

    // Initialize tab controller
    _tabController = TabController(length: 2, vsync: this);

    // Initialize date format
    _dateFormat = widget.dateFormat ?? DateFormat('MMM dd, yyyy');

    // Set initial date range
    _selectedDateRange = widget.initialDateRange;
    _updateControllers();

    // Set initial timezone
    _selectedTimezone = widget.defaultTimezone ?? 'UTC';

    // Expand presets if enabled
    if (widget.showPresets && _presetsExpanded) {
      _animationController.forward();
    }
  }

  @override
  void didUpdateWidget(DateRangeSelector oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Update selected date range if changed externally
    if (widget.initialDateRange != oldWidget.initialDateRange) {
      setState(() {
        _selectedDateRange = widget.initialDateRange;
      });
      _updateControllers();
    }
  }

  @override
  void dispose() {
    _logger.info('Disposing date range selector');
    _animationController.dispose();
    _tabController.dispose();
    _startDateController.dispose();
    _endDateController.dispose();
    _startDateFocus.dispose();
    _endDateFocus.dispose();
    super.dispose();
  }

  /// Updates text controllers with current date range
  void _updateControllers() {
    if (_selectedDateRange != null) {
      _startDateController.text = _dateFormat.format(_selectedDateRange!.start);
      _endDateController.text = _dateFormat.format(_selectedDateRange!.end);
    } else {
      _startDateController.clear();
      _endDateController.clear();
    }
  }

  /// Toggles presets panel expansion
  void _togglePresets() {
    setState(() {
      _presetsExpanded = !_presetsExpanded;
    });

    if (_presetsExpanded) {
      _animationController.forward();
    } else {
      _animationController.reverse();
    }

    _logger.info('Presets panel ${_presetsExpanded ? 'expanded' : 'collapsed'}');
  }

  /// Applies a preset date range
  void _applyPreset(DateRangePreset preset) {
    final now = DateTime.now();
    late DateRange dateRange;

    switch (preset.type) {
      case DateRangeType.lastDays:
        dateRange = DateRange(
          start: now.subtract(Duration(days: preset.value)),
          end: now,
        );
        break;
      case DateRangeType.lastWeeks:
        dateRange = DateRange(
          start: now.subtract(Duration(days: preset.value * 7)),
          end: now,
        );
        break;
      case DateRangeType.lastMonths:
        dateRange = DateRange(
          start: DateTime(now.year, now.month - preset.value, now.day),
          end: now,
        );
        break;
      case DateRangeType.thisWeek:
        final startOfWeek = now.subtract(Duration(days: now.weekday - 1));
        dateRange = DateRange(
          start: DateTime(startOfWeek.year, startOfWeek.month, startOfWeek.day),
          end: now,
        );
        break;
      case DateRangeType.thisMonth:
        dateRange = DateRange(
          start: DateTime(now.year, now.month, 1),
          end: now,
        );
        break;
      case DateRangeType.thisYear:
        dateRange = DateRange(
          start: DateTime(now.year, 1, 1),
          end: now,
        );
        break;
      case DateRangeType.custom:
        // Handle custom preset
        if (preset.customStart != null && preset.customEnd != null) {
          dateRange = DateRange(
            start: preset.customStart!,
            end: preset.customEnd!,
          );
        } else {
          return;
        }
        break;
    }

    _applyDateRange(dateRange, preset);
  }

  /// Applies a date range and updates state
  void _applyDateRange(DateRange dateRange, [DateRangePreset? preset]) {
    // Validate date range
    if (_validateDateRange(dateRange)) {
      setState(() {
        _selectedDateRange = dateRange;
        _selectedPreset = preset;
      });

      _updateControllers();
      widget.onDateRangeChanged(dateRange);

      _logger.info('Date range applied: ${dateRange.start} to ${dateRange.end}');
    }
  }

  /// Validates a date range
  bool _validateDateRange(DateRange dateRange) {
    // Check minimum date
    if (widget.minDate != null && dateRange.start.isBefore(widget.minDate!)) {
      _showError('Start date cannot be before ${_dateFormat.format(widget.minDate!)}');
      return false;
    }

    // Check maximum date
    if (widget.maxDate != null && dateRange.end.isAfter(widget.maxDate!)) {
      _showError('End date cannot be after ${_dateFormat.format(widget.maxDate!)}');
      return false;
    }

    // Check date order
    if (dateRange.start.isAfter(dateRange.end)) {
      _showError('Start date must be before end date');
      return false;
    }

    // Check maximum range duration
    if (widget.maxRangeDuration != null && dateRange.duration > widget.maxRangeDuration!) {
      _showError('Date range cannot exceed ${widget.maxRangeDuration!.inDays} days');
      return false;
    }

    return true;
  }

  /// Shows an error message
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  /// Opens native date range picker
  Future<void> _openDateRangePicker() async {
    final initialRange = _selectedDateRange != null
        ? DateTimeRange(start: _selectedDateRange!.start, end: _selectedDateRange!.end)
        : null;

    final range = await showDateRangePicker(
      context: context,
      firstDate: widget.minDate ?? DateTime(2020),
      lastDate: widget.maxDate ?? DateTime.now().add(const Duration(days: 365)),
      initialDateRange: initialRange,
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: widget.colorScheme ?? Theme.of(context).colorScheme,
          ),
          child: child!,
        );
      },
    );

    if (range != null) {
      final dateRange = DateRange(start: range.start, end: range.end);
      _applyDateRange(dateRange);
    }
  }

  /// Opens start date picker
  Future<void> _openStartDatePicker() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _selectedDateRange?.start ?? DateTime.now(),
      firstDate: widget.minDate ?? DateTime(2020),
      lastDate: _selectedDateRange?.end ?? DateTime.now(),
    );

    if (date != null && _selectedDateRange != null) {
      final dateRange = DateRange(start: date, end: _selectedDateRange!.end);
      _applyDateRange(dateRange);
    } else if (date != null) {
      setState(() {
        _selectedDateRange = DateRange(start: date, end: date);
      });
      _updateControllers();
    }
  }

  /// Opens end date picker
  Future<void> _openEndDatePicker() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _selectedDateRange?.end ?? DateTime.now(),
      firstDate: _selectedDateRange?.start ?? (widget.minDate ?? DateTime(2020)),
      lastDate: widget.maxDate ?? DateTime.now().add(const Duration(days: 365)),
    );

    if (date != null && _selectedDateRange != null) {
      final dateRange = DateRange(start: _selectedDateRange!.start, end: date);
      _applyDateRange(dateRange);
    } else if (date != null) {
      setState(() {
        _selectedDateRange = DateRange(start: date, end: date);
      });
      _updateControllers();
    }
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

            // Tab bar for selection modes
            _buildTabBar(theme, colorScheme),

            const SizedBox(height: 16),

            // Tab content
            _buildTabContent(theme, colorScheme),

            const SizedBox(height: 16),

            // Current selection display
            _buildCurrentSelection(theme, colorScheme),

            // Timezone selector (if enabled)
            if (widget.showTimezone) ...[
              const SizedBox(height: 16),
              _buildTimezoneSelector(theme, colorScheme),
            ],
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
                'Date Range Selection',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Select time period for analytics data',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ),
        ),
        if (widget.showPresets)
          IconButton(
            onPressed: _togglePresets,
            icon: Icon(_presetsExpanded ? Icons.expand_less : Icons.expand_more),
            tooltip: 'Toggle Presets',
            color: colorScheme.primary,
          ),
      ],
    );
  }

  /// Builds the tab bar
  Widget _buildTabBar(ThemeData theme, ColorScheme colorScheme) {
    return TabBar(
      controller: _tabController,
      labelColor: colorScheme.primary,
      unselectedLabelColor: colorScheme.onSurface.withOpacity(0.6),
      indicatorColor: colorScheme.primary,
      tabs: const [
        Tab(icon: Icon(Icons.list), text: 'Presets'),
        Tab(icon: Icon(Icons.calendar_today), text: 'Custom'),
      ],
    );
  }

  /// Builds the tab content
  Widget _buildTabContent(ThemeData theme, ColorScheme colorScheme) {
    return SizedBox(
      height: 300,
      child: TabBarView(
        controller: _tabController,
        children: [
          // Presets tab
          _buildPresetsTab(theme, colorScheme),
          // Custom tab
          _buildCustomTab(theme, colorScheme),
        ],
      ),
    );
  }

  /// Builds the presets tab content
  Widget _buildPresetsTab(ThemeData theme, ColorScheme colorScheme) {
    final presets = widget.customPresets ?? _getDefaultPresets();

    return SingleChildScrollView(
      child: Column(
        children: [
          // Quick options (if enabled)
          if (widget.showQuickOptions) ...[
            _buildQuickOptions(theme, colorScheme),
            const SizedBox(height: 16),
          ],

          // Preset list
          ...presets.map((preset) => _buildPresetItem(preset, theme, colorScheme)),
        ],
      ),
    );
  }

  /// Builds quick option buttons
  Widget _buildQuickOptions(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Quick Options',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: [
            _buildQuickButton('Today', () => _applyQuickRange(0)),
            _buildQuickButton('Yesterday', () => _applyQuickRange(1)),
            _buildQuickButton('Last 7 days', () => _applyQuickRange(7)),
            _buildQuickButton('Last 30 days', () => _applyQuickRange(30)),
            _buildQuickButton('This Month', _applyThisMonth),
          ],
        ),
      ],
    );
  }

  /// Builds a quick option button
  Widget _buildQuickButton(String label, VoidCallback onPressed) {
    return OutlinedButton(
      onPressed: widget.readOnly ? null : onPressed,
      child: Text(label),
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      ),
    );
  }

  /// Applies a quick date range
  void _applyQuickRange(int days) {
    final now = DateTime.now();
    final start = days == 0
        ? DateTime(now.year, now.month, now.day)
        : now.subtract(Duration(days: days));

    _applyDateRange(DateRange(start: start, end: now));
  }

  /// Applies this month range
  void _applyThisMonth() {
    final now = DateTime.now();
    _applyDateRange(DateRange(
      start: DateTime(now.year, now.month, 1),
      end: now,
    ));
  }

  /// Builds a preset item
  Widget _buildPresetItem(DateRangePreset preset, ThemeData theme, ColorScheme colorScheme) {
    final isSelected = _selectedPreset == preset;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(preset.name),
        subtitle: Text(preset.description),
        leading: Icon(
          preset.icon,
          color: isSelected ? colorScheme.primary : colorScheme.onSurface.withOpacity(0.6),
        ),
        trailing: isSelected
            ? Icon(Icons.check_circle, color: colorScheme.primary)
            : const Icon(Icons.radio_button_unchecked),
        selected: isSelected,
        selectedTileColor: colorScheme.primaryContainer.withOpacity(0.3),
        onTap: widget.readOnly ? null : () => _applyPreset(preset),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  /// Builds the custom tab content
  Widget _buildCustomTab(ThemeData theme, ColorScheme colorScheme) {
    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        child: Column(
          children: [
            // Date range picker button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: widget.readOnly ? null : _openDateRangePicker,
                icon: const Icon(Icons.date_range),
                label: const Text('Open Date Range Picker'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.all(16),
                ),
              ),
            ),

            const SizedBox(height: 20),

            // Divider with "OR" text
            Row(
              children: [
                const Expanded(child: Divider()),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    'OR',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ),
                const Expanded(child: Divider()),
              ],
            ),

            const SizedBox(height: 20),

            // Individual date pickers
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _startDateController,
                    focusNode: _startDateFocus,
                    decoration: InputDecoration(
                      labelText: 'Start Date',
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        onPressed: widget.readOnly ? null : _openStartDatePicker,
                        icon: const Icon(Icons.calendar_today),
                      ),
                    ),
                    readOnly: true,
                    onTap: widget.readOnly ? null : _openStartDatePicker,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: TextFormField(
                    controller: _endDateController,
                    focusNode: _endDateFocus,
                    decoration: InputDecoration(
                      labelText: 'End Date',
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        onPressed: widget.readOnly ? null : _openEndDatePicker,
                        icon: const Icon(Icons.calendar_today),
                      ),
                    ),
                    readOnly: true,
                    onTap: widget.readOnly ? null : _openEndDatePicker,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Validation info
            if (_selectedDateRange != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Icon(Icons.info, color: colorScheme.primary, size: 16),
                        const SizedBox(width: 8),
                        Text(
                          'Range Duration: ${_selectedDateRange!.duration.inDays} days',
                          style: theme.textTheme.bodyMedium,
                        ),
                      ],
                    ),
                    if (widget.maxRangeDuration != null) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(Icons.warning, color: Colors.orange, size: 16),
                          const SizedBox(width: 8),
                          Text(
                            'Maximum allowed: ${widget.maxRangeDuration!.inDays} days',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: Colors.orange,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// Builds current selection display
  Widget _buildCurrentSelection(ThemeData theme, ColorScheme colorScheme) {
    if (_selectedDateRange == null) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: colorScheme.outline.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Icon(Icons.info, color: colorScheme.onSurface.withOpacity(0.6)),
            const SizedBox(width: 12),
            Text(
              'No date range selected',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.primaryContainer.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colorScheme.primary.withOpacity(0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Selected Range',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: colorScheme.primary,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'From: ${_dateFormat.format(_selectedDateRange!.start)}',
                      style: theme.textTheme.bodyMedium,
                    ),
                    Text(
                      'To: ${_dateFormat.format(_selectedDateRange!.end)}',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${_selectedDateRange!.duration.inDays} days',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: colorScheme.primary,
                    ),
                  ),
                  if (_selectedPreset != null)
                    Text(
                      _selectedPreset!.name,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: colorScheme.onSurface.withOpacity(0.7),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds timezone selector
  Widget _buildTimezoneSelector(ThemeData theme, ColorScheme colorScheme) {
    final timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Timezone',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _selectedTimezone,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          ),
          items: timezones.map((timezone) {
            return DropdownMenuItem(
              value: timezone,
              child: Text(timezone),
            );
          }).toList(),
          onChanged: widget.readOnly
              ? null
              : (timezone) {
                  if (timezone != null) {
                    setState(() {
                      _selectedTimezone = timezone;
                    });
                    _logger.info('Timezone changed to: $timezone');
                  }
                },
        ),
      ],
    );
  }

  /// Gets default date range presets
  List<DateRangePreset> _getDefaultPresets() {
    return [
      DateRangePreset(
        name: 'Last 7 Days',
        description: 'Recent week of data',
        type: DateRangeType.lastDays,
        value: 7,
        icon: Icons.calendar_view_week,
      ),
      DateRangePreset(
        name: 'Last 30 Days',
        description: 'Recent month of data',
        type: DateRangeType.lastDays,
        value: 30,
        icon: Icons.calendar_view_month,
      ),
      DateRangePreset(
        name: 'Last 90 Days',
        description: 'Recent quarter of data',
        type: DateRangeType.lastDays,
        value: 90,
        icon: Icons.calendar_today,
      ),
      DateRangePreset(
        name: 'Last 6 Months',
        description: 'Half year of data',
        type: DateRangeType.lastMonths,
        value: 6,
        icon: Icons.calendar_month,
      ),
      DateRangePreset(
        name: 'Last Year',
        description: 'Full year of data',
        type: DateRangeType.lastMonths,
        value: 12,
        icon: Icons.calendar_view_year,
      ),
      DateRangePreset(
        name: 'This Week',
        description: 'Current week to date',
        type: DateRangeType.thisWeek,
        value: 0,
        icon: Icons.today,
      ),
      DateRangePreset(
        name: 'This Month',
        description: 'Current month to date',
        type: DateRangeType.thisMonth,
        value: 0,
        icon: Icons.calendar_today,
      ),
      DateRangePreset(
        name: 'This Year',
        description: 'Current year to date',
        type: DateRangeType.thisYear,
        value: 0,
        icon: Icons.calendar_view_year,
      ),
    ];
  }
}

/// Date range preset configuration
class DateRangePreset {
  /// Display name for the preset
  final String name;

  /// Description of the preset
  final String description;

  /// Type of date range
  final DateRangeType type;

  /// Value for the range calculation
  final int value;

  /// Icon for the preset
  final IconData icon;

  /// Custom start date (for custom type)
  final DateTime? customStart;

  /// Custom end date (for custom type)
  final DateTime? customEnd;

  const DateRangePreset({
    required this.name,
    required this.description,
    required this.type,
    required this.value,
    required this.icon,
    this.customStart,
    this.customEnd,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is DateRangePreset &&
          runtimeType == other.runtimeType &&
          name == other.name &&
          type == other.type &&
          value == other.value;

  @override
  int get hashCode => name.hashCode ^ type.hashCode ^ value.hashCode;
}

/// Date range type enumeration
enum DateRangeType {
  lastDays,
  lastWeeks,
  lastMonths,
  thisWeek,
  thisMonth,
  thisYear,
  custom,
}