/// Advanced filter controls widget for analytics data customization
///
/// This widget provides comprehensive filtering capabilities for analytics data
/// including environmental factors, risk levels, data quality thresholds,
/// geographic bounds, and temporal aggregation options.
///
/// Features:
/// - Multi-select environmental factor filtering
/// - Risk level and alert severity selection
/// - Data quality threshold controls
/// - Geographic bounds selection
/// - Temporal aggregation options
/// - Custom filter combinations
/// - Filter validation and error handling
/// - Responsive design with adaptive layouts
///
/// Usage:
/// ```dart
/// FilterControlsWidget(
///   filters: currentFilters,
///   onFiltersChanged: (filters) => updateFilters(filters),
///   showAdvancedFilters: true,
///   allowCustomRanges: true,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:logging/logging.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/analytics_filters.dart';

/// Logger for filter controls operations
final _logger = Logger('FilterControlsWidget');

/// Advanced filter controls widget
class FilterControlsWidget extends StatefulWidget {
  /// Current analytics filters
  final AnalyticsFilters filters;

  /// Callback when filters are changed
  final ValueChanged<AnalyticsFilters> onFiltersChanged;

  /// Whether to show advanced filter options
  final bool showAdvancedFilters;

  /// Whether to allow custom range inputs
  final bool allowCustomRanges;

  /// Available environmental factors for filtering
  final List<EnvironmentalFactor>? availableFactors;

  /// Available risk levels for filtering
  final List<RiskLevel>? availableRiskLevels;

  /// Available alert severities for filtering
  final List<AlertSeverity>? availableAlertSeverities;

  /// Custom color scheme
  final ColorScheme? colorScheme;

  /// Whether filters are read-only
  final bool readOnly;

  /// Custom validation rules
  final Map<String, String Function(dynamic)?>? validators;

  const FilterControlsWidget({
    super.key,
    required this.filters,
    required this.onFiltersChanged,
    this.showAdvancedFilters = false,
    this.allowCustomRanges = true,
    this.availableFactors,
    this.availableRiskLevels,
    this.availableAlertSeverities,
    this.colorScheme,
    this.readOnly = false,
    this.validators,
  });

  @override
  State<FilterControlsWidget> createState() => _FilterControlsWidgetState();
}

class _FilterControlsWidgetState extends State<FilterControlsWidget>
    with TickerProviderStateMixin {
  /// Form key for validation
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  /// Animation controller for advanced filters
  late AnimationController _advancedAnimationController;

  /// Animation for advanced filters expansion
  late Animation<double> _advancedAnimation;

  /// Current filter state (mutable copy)
  late AnalyticsFilters _currentFilters;

  /// Text controllers for numeric inputs
  final TextEditingController _minQualityController = TextEditingController();
  final TextEditingController _maxAgeController = TextEditingController();
  final TextEditingController _smoothingWindowController = TextEditingController();
  final TextEditingController _confidenceLevelController = TextEditingController();

  /// Geographic bounds controllers
  final TextEditingController _northController = TextEditingController();
  final TextEditingController _southController = TextEditingController();
  final TextEditingController _eastController = TextEditingController();
  final TextEditingController _westController = TextEditingController();

  /// Focus nodes for input fields
  final List<FocusNode> _focusNodes = [];

  /// Whether advanced filters are expanded
  bool _advancedExpanded = false;

  @override
  void initState() {
    super.initState();
    _logger.info('Initializing filter controls widget');

    // Initialize animation controller
    _advancedAnimationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _advancedAnimation = CurvedAnimation(
      parent: _advancedAnimationController,
      curve: Curves.easeInOut,
    );

    // Initialize current filters
    _currentFilters = widget.filters;
    _advancedExpanded = widget.showAdvancedFilters;

    // Initialize text controllers
    _initializeControllers();

    // Create focus nodes
    for (int i = 0; i < 10; i++) {
      _focusNodes.add(FocusNode());
    }

    // Expand advanced filters if requested
    if (_advancedExpanded) {
      _advancedAnimationController.forward();
    }
  }

  @override
  void didUpdateWidget(FilterControlsWidget oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Update filters if they changed externally
    if (widget.filters != oldWidget.filters) {
      setState(() {
        _currentFilters = widget.filters;
      });
      _updateControllers();
    }

    // Update advanced filters visibility
    if (widget.showAdvancedFilters != oldWidget.showAdvancedFilters) {
      _toggleAdvancedFilters();
    }
  }

  @override
  void dispose() {
    _logger.info('Disposing filter controls widget');
    _advancedAnimationController.dispose();
    _minQualityController.dispose();
    _maxAgeController.dispose();
    _smoothingWindowController.dispose();
    _confidenceLevelController.dispose();
    _northController.dispose();
    _southController.dispose();
    _eastController.dispose();
    _westController.dispose();
    for (final node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  /// Initializes text controllers with current filter values
  void _initializeControllers() {
    _minQualityController.text = _currentFilters.minDataQuality?.toString() ?? '';
    _maxAgeController.text = _currentFilters.maxDataAgeHours?.toString() ?? '';
    _smoothingWindowController.text = _currentFilters.smoothingWindowDays.toString();
    _confidenceLevelController.text = _currentFilters.confidenceLevel.toString();

    final bounds = _currentFilters.geographicBounds;
    if (bounds != null) {
      _northController.text = bounds.north.toString();
      _southController.text = bounds.south.toString();
      _eastController.text = bounds.east.toString();
      _westController.text = bounds.west.toString();
    }
  }

  /// Updates controllers when filters change externally
  void _updateControllers() {
    _minQualityController.text = _currentFilters.minDataQuality?.toString() ?? '';
    _maxAgeController.text = _currentFilters.maxDataAgeHours?.toString() ?? '';
    _smoothingWindowController.text = _currentFilters.smoothingWindowDays.toString();
    _confidenceLevelController.text = _currentFilters.confidenceLevel.toString();

    final bounds = _currentFilters.geographicBounds;
    if (bounds != null) {
      _northController.text = bounds.north.toString();
      _southController.text = bounds.south.toString();
      _eastController.text = bounds.east.toString();
      _westController.text = bounds.west.toString();
    } else {
      _northController.clear();
      _southController.clear();
      _eastController.clear();
      _westController.clear();
    }
  }

  /// Toggles advanced filters visibility
  void _toggleAdvancedFilters() {
    setState(() {
      _advancedExpanded = !_advancedExpanded;
    });

    if (_advancedExpanded) {
      _advancedAnimationController.forward();
    } else {
      _advancedAnimationController.reverse();
    }

    _logger.info('Advanced filters ${_advancedExpanded ? 'expanded' : 'collapsed'}');
  }

  /// Updates filters and notifies parent
  void _updateFilters() {
    if (_formKey.currentState?.validate() ?? false) {
      widget.onFiltersChanged(_currentFilters);
      _logger.info('Filters updated: ${_currentFilters.toString()}');
    }
  }

  /// Resets all filters to defaults
  void _resetFilters() {
    setState(() {
      _currentFilters = const AnalyticsFilters();
    });
    _updateControllers();
    _updateFilters();
    _logger.info('Filters reset to defaults');
  }

  /// Validates numeric input
  String? _validateNumeric(String? value, {double? min, double? max, bool required = false}) {
    if (value == null || value.isEmpty) {
      return required ? 'This field is required' : null;
    }

    final number = double.tryParse(value);
    if (number == null) {
      return 'Please enter a valid number';
    }

    if (min != null && number < min) {
      return 'Value must be at least $min';
    }

    if (max != null && number > max) {
      return 'Value must be at most $max';
    }

    return null;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = widget.colorScheme ?? theme.colorScheme;

    return Form(
      key: _formKey,
      child: Card(
        elevation: 2,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with title and reset button
              _buildHeader(theme, colorScheme),

              const SizedBox(height: 16),

              // Basic filters
              _buildBasicFilters(theme, colorScheme),

              // Advanced filters toggle
              if (widget.allowCustomRanges) ...[
                const SizedBox(height: 16),
                _buildAdvancedToggle(theme, colorScheme),
              ],

              // Advanced filters (collapsible)
              AnimatedBuilder(
                animation: _advancedAnimation,
                builder: (context, child) {
                  return ClipRect(
                    child: SizeTransition(
                      sizeFactor: _advancedAnimation,
                      child: child,
                    ),
                  );
                },
                child: _buildAdvancedFilters(theme, colorScheme),
              ),

              const SizedBox(height: 16),

              // Action buttons
              _buildActionButtons(theme, colorScheme),
            ],
          ),
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
                'Filter Controls',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Customize data visualization and analysis parameters',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ),
        ),
        IconButton(
          onPressed: widget.readOnly ? null : _resetFilters,
          icon: const Icon(Icons.restart_alt),
          tooltip: 'Reset Filters',
          color: colorScheme.primary,
        ),
      ],
    );
  }

  /// Builds basic filter controls
  Widget _buildBasicFilters(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Data inclusion toggles
        Text(
          'Data Inclusion',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),

        Wrap(
          spacing: 16,
          runSpacing: 8,
          children: [
            _buildToggleFilter(
              'Environmental Data',
              _currentFilters.includeEnvironmentalData,
              (value) {
                setState(() {
                  _currentFilters = _currentFilters.copyWith(includeEnvironmentalData: value);
                });
                _updateFilters();
              },
              Icons.eco,
            ),
            _buildToggleFilter(
              'Prediction Accuracy',
              _currentFilters.includePredictionAccuracy,
              (value) {
                setState(() {
                  _currentFilters = _currentFilters.copyWith(includePredictionAccuracy: value);
                });
                _updateFilters();
              },
              Icons.analytics,
            ),
            _buildToggleFilter(
              'Risk Trends',
              _currentFilters.includeRiskTrends,
              (value) {
                setState(() {
                  _currentFilters = _currentFilters.copyWith(includeRiskTrends: value);
                });
                _updateFilters();
              },
              Icons.trending_up,
            ),
            _buildToggleFilter(
              'Alert Statistics',
              _currentFilters.includeAlertStatistics,
              (value) {
                setState(() {
                  _currentFilters = _currentFilters.copyWith(includeAlertStatistics: value);
                });
                _updateFilters();
              },
              Icons.notifications,
            ),
            _buildToggleFilter(
              'Data Quality',
              _currentFilters.includeDataQuality,
              (value) {
                setState(() {
                  _currentFilters = _currentFilters.copyWith(includeDataQuality: value);
                });
                _updateFilters();
              },
              Icons.verified,
            ),
          ],
        ),

        const SizedBox(height: 20),

        // Environmental factors
        _buildEnvironmentalFactorsFilter(theme, colorScheme),

        const SizedBox(height: 16),

        // Risk levels
        _buildRiskLevelsFilter(theme, colorScheme),

        const SizedBox(height: 16),

        // Aggregation period
        _buildAggregationPeriodFilter(theme, colorScheme),
      ],
    );
  }

  /// Builds toggle filter widget
  Widget _buildToggleFilter(String label, bool value, ValueChanged<bool> onChanged, IconData icon) {
    return SizedBox(
      width: 180,
      child: CheckboxListTile(
        value: value,
        onChanged: widget.readOnly ? null : onChanged,
        title: Text(
          label,
          style: const TextStyle(fontSize: 14),
        ),
        secondary: Icon(icon, size: 20),
        dense: true,
        contentPadding: EdgeInsets.zero,
        controlAffinity: ListTileControlAffinity.leading,
      ),
    );
  }

  /// Builds environmental factors filter
  Widget _buildEnvironmentalFactorsFilter(ThemeData theme, ColorScheme colorScheme) {
    final availableFactors = widget.availableFactors ?? EnvironmentalFactor.values;
    final selectedFactors = _currentFilters.environmentalFactors ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Environmental Factors',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: availableFactors.map((factor) {
            final isSelected = selectedFactors.contains(factor);
            return FilterChip(
              label: Text(_getEnvironmentalFactorLabel(factor)),
              selected: isSelected,
              onSelected: widget.readOnly
                  ? null
                  : (selected) {
                      final newFactors = List<EnvironmentalFactor>.from(selectedFactors);
                      if (selected) {
                        newFactors.add(factor);
                      } else {
                        newFactors.remove(factor);
                      }
                      setState(() {
                        _currentFilters = _currentFilters.copyWith(
                          environmentalFactors: newFactors.isEmpty ? null : newFactors,
                        );
                      });
                      _updateFilters();
                    },
              avatar: Icon(_getEnvironmentalFactorIcon(factor), size: 16),
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds risk levels filter
  Widget _buildRiskLevelsFilter(ThemeData theme, ColorScheme colorScheme) {
    final availableRiskLevels = widget.availableRiskLevels ?? RiskLevel.values;
    final selectedRiskLevels = _currentFilters.riskLevels ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Risk Levels',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: availableRiskLevels.map((riskLevel) {
            final isSelected = selectedRiskLevels.contains(riskLevel);
            return FilterChip(
              label: Text(_getRiskLevelLabel(riskLevel)),
              selected: isSelected,
              onSelected: widget.readOnly
                  ? null
                  : (selected) {
                      final newRiskLevels = List<RiskLevel>.from(selectedRiskLevels);
                      if (selected) {
                        newRiskLevels.add(riskLevel);
                      } else {
                        newRiskLevels.remove(riskLevel);
                      }
                      setState(() {
                        _currentFilters = _currentFilters.copyWith(
                          riskLevels: newRiskLevels.isEmpty ? null : newRiskLevels,
                        );
                      });
                      _updateFilters();
                    },
              backgroundColor: _getRiskLevelColor(riskLevel).withOpacity(0.1),
              selectedColor: _getRiskLevelColor(riskLevel).withOpacity(0.3),
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds aggregation period filter
  Widget _buildAggregationPeriodFilter(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Aggregation Period',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<AggregationPeriod>(
          value: _currentFilters.aggregationPeriod,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          ),
          items: AggregationPeriod.values.map((period) {
            return DropdownMenuItem(
              value: period,
              child: Text(_getAggregationPeriodLabel(period)),
            );
          }).toList(),
          onChanged: widget.readOnly
              ? null
              : (period) {
                  if (period != null) {
                    setState(() {
                      _currentFilters = _currentFilters.copyWith(aggregationPeriod: period);
                    });
                    _updateFilters();
                  }
                },
        ),
      ],
    );
  }

  /// Builds advanced filters toggle
  Widget _buildAdvancedToggle(ThemeData theme, ColorScheme colorScheme) {
    return InkWell(
      onTap: _toggleAdvancedFilters,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          children: [
            Icon(
              _advancedExpanded ? Icons.expand_less : Icons.expand_more,
              color: colorScheme.primary,
            ),
            const SizedBox(width: 8),
            Text(
              'Advanced Filters',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: colorScheme.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds advanced filter controls
  Widget _buildAdvancedFilters(ThemeData theme, ColorScheme colorScheme) {
    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Data quality and age filters
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _minQualityController,
                  focusNode: _focusNodes[0],
                  decoration: const InputDecoration(
                    labelText: 'Min Data Quality',
                    suffixText: '%',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*'))],
                  validator: (value) => _validateNumeric(value, min: 0, max: 100),
                  readOnly: widget.readOnly,
                  onChanged: (value) {
                    final quality = double.tryParse(value);
                    if (quality != null) {
                      setState(() {
                        _currentFilters = _currentFilters.copyWith(minDataQuality: quality / 100);
                      });
                      _updateFilters();
                    }
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: TextFormField(
                  controller: _maxAgeController,
                  focusNode: _focusNodes[1],
                  decoration: const InputDecoration(
                    labelText: 'Max Data Age',
                    suffixText: 'hours',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  validator: (value) => _validateNumeric(value, min: 0),
                  readOnly: widget.readOnly,
                  onChanged: (value) {
                    final age = int.tryParse(value);
                    if (age != null) {
                      setState(() {
                        _currentFilters = _currentFilters.copyWith(maxDataAgeHours: age);
                      });
                      _updateFilters();
                    }
                  },
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Data processing options
          _buildDataProcessingOptions(theme, colorScheme),

          const SizedBox(height: 16),

          // Geographic bounds
          _buildGeographicBounds(theme, colorScheme),

          const SizedBox(height: 16),

          // Alert severities
          _buildAlertSeveritiesFilter(theme, colorScheme),
        ],
      ),
    );
  }

  /// Builds data processing options
  Widget _buildDataProcessingOptions(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Data Processing',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),

        Row(
          children: [
            Expanded(
              child: CheckboxListTile(
                value: _currentFilters.smoothData,
                onChanged: widget.readOnly
                    ? null
                    : (value) {
                        setState(() {
                          _currentFilters = _currentFilters.copyWith(smoothData: value ?? false);
                        });
                        _updateFilters();
                      },
                title: const Text('Smooth Data'),
                subtitle: const Text('Apply moving average'),
                dense: true,
                contentPadding: EdgeInsets.zero,
              ),
            ),
            if (_currentFilters.smoothData) ...[
              const SizedBox(width: 16),
              SizedBox(
                width: 120,
                child: TextFormField(
                  controller: _smoothingWindowController,
                  focusNode: _focusNodes[2],
                  decoration: const InputDecoration(
                    labelText: 'Window',
                    suffixText: 'days',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  validator: (value) => _validateNumeric(value, min: 1, max: 365),
                  readOnly: widget.readOnly,
                  onChanged: (value) {
                    final window = int.tryParse(value);
                    if (window != null) {
                      setState(() {
                        _currentFilters = _currentFilters.copyWith(smoothingWindowDays: window);
                      });
                      _updateFilters();
                    }
                  },
                ),
              ),
            ],
          ],
        ),

        CheckboxListTile(
          value: _currentFilters.normalizeData,
          onChanged: widget.readOnly
              ? null
              : (value) {
                  setState(() {
                    _currentFilters = _currentFilters.copyWith(normalizeData: value ?? false);
                  });
                  _updateFilters();
                },
          title: const Text('Normalize Data'),
          subtitle: const Text('Scale values to 0-1 range'),
          dense: true,
          contentPadding: EdgeInsets.zero,
        ),

        CheckboxListTile(
          value: _currentFilters.includeConfidenceIntervals,
          onChanged: widget.readOnly
              ? null
              : (value) {
                  setState(() {
                    _currentFilters = _currentFilters.copyWith(includeConfidenceIntervals: value ?? false);
                  });
                  _updateFilters();
                },
          title: const Text('Confidence Intervals'),
          subtitle: const Text('Show prediction confidence'),
          dense: true,
          contentPadding: EdgeInsets.zero,
        ),

        if (_currentFilters.includeConfidenceIntervals) ...[
          const SizedBox(height: 8),
          SizedBox(
            width: 200,
            child: TextFormField(
              controller: _confidenceLevelController,
              focusNode: _focusNodes[3],
              decoration: const InputDecoration(
                labelText: 'Confidence Level',
                suffixText: '%',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*'))],
              validator: (value) => _validateNumeric(value, min: 50, max: 99.9),
              readOnly: widget.readOnly,
              onChanged: (value) {
                final confidence = double.tryParse(value);
                if (confidence != null) {
                  setState(() {
                    _currentFilters = _currentFilters.copyWith(confidenceLevel: confidence / 100);
                  });
                  _updateFilters();
                }
              },
            ),
          ),
        ],
      ],
    );
  }

  /// Builds geographic bounds filter
  Widget _buildGeographicBounds(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Geographic Bounds',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 12),

        Row(
          children: [
            Expanded(
              child: TextFormField(
                controller: _northController,
                focusNode: _focusNodes[4],
                decoration: const InputDecoration(
                  labelText: 'North Lat',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^-?\d*\.?\d*'))],
                validator: (value) => _validateNumeric(value, min: -90, max: 90),
                readOnly: widget.readOnly,
                onChanged: _updateGeographicBounds,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _southController,
                focusNode: _focusNodes[5],
                decoration: const InputDecoration(
                  labelText: 'South Lat',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^-?\d*\.?\d*'))],
                validator: (value) => _validateNumeric(value, min: -90, max: 90),
                readOnly: widget.readOnly,
                onChanged: _updateGeographicBounds,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _eastController,
                focusNode: _focusNodes[6],
                decoration: const InputDecoration(
                  labelText: 'East Lng',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^-?\d*\.?\d*'))],
                validator: (value) => _validateNumeric(value, min: -180, max: 180),
                readOnly: widget.readOnly,
                onChanged: _updateGeographicBounds,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextFormField(
                controller: _westController,
                focusNode: _focusNodes[7],
                decoration: const InputDecoration(
                  labelText: 'West Lng',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^-?\d*\.?\d*'))],
                validator: (value) => _validateNumeric(value, min: -180, max: 180),
                readOnly: widget.readOnly,
                onChanged: _updateGeographicBounds,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Updates geographic bounds from text controllers
  void _updateGeographicBounds(String value) {
    final north = double.tryParse(_northController.text);
    final south = double.tryParse(_southController.text);
    final east = double.tryParse(_eastController.text);
    final west = double.tryParse(_westController.text);

    if (north != null && south != null && east != null && west != null) {
      final bounds = GeographicBounds(
        north: north,
        south: south,
        east: east,
        west: west,
      );

      setState(() {
        _currentFilters = _currentFilters.copyWith(geographicBounds: bounds);
      });
      _updateFilters();
    } else if (_northController.text.isEmpty &&
               _southController.text.isEmpty &&
               _eastController.text.isEmpty &&
               _westController.text.isEmpty) {
      setState(() {
        _currentFilters = _currentFilters.copyWith(geographicBounds: null);
      });
      _updateFilters();
    }
  }

  /// Builds alert severities filter
  Widget _buildAlertSeveritiesFilter(ThemeData theme, ColorScheme colorScheme) {
    final availableAlertSeverities = widget.availableAlertSeverities ?? AlertSeverity.values;
    final selectedAlertSeverities = _currentFilters.alertSeverities ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Alert Severities',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: availableAlertSeverities.map((severity) {
            final isSelected = selectedAlertSeverities.contains(severity);
            return FilterChip(
              label: Text(_getAlertSeverityLabel(severity)),
              selected: isSelected,
              onSelected: widget.readOnly
                  ? null
                  : (selected) {
                      final newSeverities = List<AlertSeverity>.from(selectedAlertSeverities);
                      if (selected) {
                        newSeverities.add(severity);
                      } else {
                        newSeverities.remove(severity);
                      }
                      setState(() {
                        _currentFilters = _currentFilters.copyWith(
                          alertSeverities: newSeverities.isEmpty ? null : newSeverities,
                        );
                      });
                      _updateFilters();
                    },
              backgroundColor: _getAlertSeverityColor(severity).withOpacity(0.1),
              selectedColor: _getAlertSeverityColor(severity).withOpacity(0.3),
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds action buttons
  Widget _buildActionButtons(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: widget.readOnly ? null : _resetFilters,
            icon: const Icon(Icons.restart_alt),
            label: const Text('Reset All'),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: widget.readOnly
                ? null
                : () {
                    if (_formKey.currentState?.validate() ?? false) {
                      _updateFilters();
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Filters applied successfully')),
                      );
                    }
                  },
            icon: const Icon(Icons.check),
            label: const Text('Apply Filters'),
          ),
        ),
      ],
    );
  }

  /// Gets environmental factor label
  String _getEnvironmentalFactorLabel(EnvironmentalFactor factor) {
    switch (factor) {
      case EnvironmentalFactor.temperature:
        return 'Temperature';
      case EnvironmentalFactor.rainfall:
        return 'Rainfall';
      case EnvironmentalFactor.humidity:
        return 'Humidity';
      case EnvironmentalFactor.vegetation:
        return 'Vegetation';
      case EnvironmentalFactor.windSpeed:
        return 'Wind Speed';
      case EnvironmentalFactor.pressure:
        return 'Pressure';
    }
  }

  /// Gets environmental factor icon
  IconData _getEnvironmentalFactorIcon(EnvironmentalFactor factor) {
    switch (factor) {
      case EnvironmentalFactor.temperature:
        return Icons.thermostat;
      case EnvironmentalFactor.rainfall:
        return Icons.water_drop;
      case EnvironmentalFactor.humidity:
        return Icons.opacity;
      case EnvironmentalFactor.vegetation:
        return Icons.eco;
      case EnvironmentalFactor.windSpeed:
        return Icons.air;
      case EnvironmentalFactor.pressure:
        return Icons.speed;
    }
  }

  /// Gets risk level label
  String _getRiskLevelLabel(RiskLevel level) {
    switch (level) {
      case RiskLevel.low:
        return 'Low';
      case RiskLevel.medium:
        return 'Medium';
      case RiskLevel.high:
        return 'High';
      case RiskLevel.critical:
        return 'Critical';
    }
  }

  /// Gets risk level color
  Color _getRiskLevelColor(RiskLevel level) {
    switch (level) {
      case RiskLevel.low:
        return Colors.green;
      case RiskLevel.medium:
        return Colors.orange;
      case RiskLevel.high:
        return Colors.red;
      case RiskLevel.critical:
        return Colors.purple;
    }
  }

  /// Gets alert severity label
  String _getAlertSeverityLabel(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.info:
        return 'Info';
      case AlertSeverity.warning:
        return 'Warning';
      case AlertSeverity.high:
        return 'High';
      case AlertSeverity.critical:
        return 'Critical';
      case AlertSeverity.emergency:
        return 'Emergency';
    }
  }

  /// Gets alert severity color
  Color _getAlertSeverityColor(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.info:
        return Colors.blue;
      case AlertSeverity.warning:
        return Colors.orange;
      case AlertSeverity.high:
        return Colors.red;
      case AlertSeverity.critical:
        return Colors.purple;
      case AlertSeverity.emergency:
        return Colors.deepPurple;
    }
  }

  /// Gets aggregation period label
  String _getAggregationPeriodLabel(AggregationPeriod period) {
    switch (period) {
      case AggregationPeriod.hourly:
        return 'Hourly';
      case AggregationPeriod.daily:
        return 'Daily';
      case AggregationPeriod.weekly:
        return 'Weekly';
      case AggregationPeriod.monthly:
        return 'Monthly';
      case AggregationPeriod.quarterly:
        return 'Quarterly';
      case AggregationPeriod.yearly:
        return 'Yearly';
    }
  }
}