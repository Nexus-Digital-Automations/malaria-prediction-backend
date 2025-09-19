/// Outbreak pattern recognition dashboard widget
///
/// This widget provides a comprehensive dashboard for analyzing outbreak patterns
/// including risk heat maps, temporal patterns, population assessments, alert correlations,
/// early warning indicators, and prediction trends specifically designed for
/// public health visualization requirements with clear risk communication.
///
/// Usage:
/// ```dart
/// OutbreakPatternDashboard(
///   analyticsData: analyticsData,
///   height: 800,
///   enableInteractivity: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';
import 'risk_heat_map_widget.dart';
import 'temporal_pattern_chart.dart';
import 'population_risk_widget.dart';
import 'alert_correlation_display.dart';
import 'early_warning_indicators.dart';
import 'risk_prediction_chart.dart';

/// Comprehensive outbreak pattern recognition dashboard
class OutbreakPatternDashboard extends StatefulWidget {
  /// Analytics data containing risk trends and alert statistics
  final AnalyticsData analyticsData;

  /// Dashboard height
  final double height;

  /// Whether to enable interactive features
  final bool enableInteractivity;

  /// Date range for filtering patterns
  final DateRange? dateRange;

  /// Geographic region for filtering
  final String? region;

  /// Whether to show population risk assessments
  final bool showPopulationRisk;

  /// Whether to show early warning indicators
  final bool showEarlyWarning;

  /// Constructor requiring analytics data
  const OutbreakPatternDashboard({
    super.key,
    required this.analyticsData,
    this.height = 800,
    this.enableInteractivity = true,
    this.dateRange,
    this.region,
    this.showPopulationRisk = true,
    this.showEarlyWarning = true,
  });

  @override
  State<OutbreakPatternDashboard> createState() => _OutbreakPatternDashboardState();
}

class _OutbreakPatternDashboardState extends State<OutbreakPatternDashboard>
    with TickerProviderStateMixin {
  /// Tab controller for dashboard sections
  late TabController _tabController;

  /// Current selected view mode
  OutbreakViewMode _viewMode = OutbreakViewMode.overview;

  /// Filter settings
  late DateRange _currentDateRange;
  String? _selectedRegion;
  RiskLevel? _riskLevelFilter;

  /// Loading states for each component
  final Map<String, bool> _loadingStates = {
    'heatmap': false,
    'temporal': false,
    'population': false,
    'alerts': false,
    'warnings': false,
    'predictions': false,
  };

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _currentDateRange = widget.dateRange ?? widget.analyticsData.dateRange;
    _selectedRegion = widget.region ?? widget.analyticsData.region;
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        height: widget.height,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 16),
            _buildFiltersAndControls(),
            const SizedBox(height: 16),
            _buildViewModeSelector(),
            const SizedBox(height: 16),
            Expanded(child: _buildMainContent()),
          ],
        ),
      ),
    );
  }

  /// Builds the dashboard header with title and overview metrics
  Widget _buildHeader() {
    final totalRiskAreas = widget.analyticsData.riskTrends.length;
    final highRiskAreas = widget.analyticsData.riskTrends
        .where((r) => r.riskLevel == RiskLevel.high || r.riskLevel == RiskLevel.critical)
        .length;
    final totalPopulationAtRisk = widget.analyticsData.riskTrends
        .fold(0, (sum, trend) => sum + trend.populationAtRisk);

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Outbreak Pattern Recognition Dashboard',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Region: $_selectedRegion • Period: ${DateFormat('MMM dd, yyyy').format(_currentDateRange.start)} - ${DateFormat('MMM dd, yyyy').format(_currentDateRange.end)}',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        _buildKeyMetricsCards(totalRiskAreas, highRiskAreas, totalPopulationAtRisk),
      ],
    );
  }

  /// Builds key metrics overview cards
  Widget _buildKeyMetricsCards(int totalAreas, int highRiskAreas, int totalPopulation) {
    return Row(
      children: [
        _buildMetricCard(
          'Risk Areas',
          totalAreas.toString(),
          Icons.location_on,
          Colors.blue,
        ),
        const SizedBox(width: 8),
        _buildMetricCard(
          'High Risk',
          highRiskAreas.toString(),
          Icons.warning,
          Colors.red,
        ),
        const SizedBox(width: 8),
        _buildMetricCard(
          'At Risk Pop.',
          _formatPopulation(totalPopulation),
          Icons.people,
          Colors.orange,
        ),
      ],
    );
  }

  /// Builds individual metric card
  Widget _buildMetricCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color.withValues(alpha: 0.8),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds filters and control panel
  Widget _buildFiltersAndControls() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(
            Icons.filter_list,
            color: Theme.of(context).colorScheme.primary,
            size: 20,
          ),
          const SizedBox(width: 8),
          Text(
            'Filters:',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(width: 16),
          _buildRiskLevelFilter(),
          const SizedBox(width: 16),
          _buildDateRangeSelector(),
          const Spacer(),
          _buildRefreshButton(),
          const SizedBox(width: 8),
          _buildExportButton(),
        ],
      ),
    );
  }

  /// Builds risk level filter dropdown
  Widget _buildRiskLevelFilter() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          'Risk Level:',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(width: 8),
        DropdownButton<RiskLevel?>(
          value: _riskLevelFilter,
          hint: const Text('All'),
          isDense: true,
          items: [
            const DropdownMenuItem<RiskLevel?>(
              value: null,
              child: Text('All Levels'),
            ),
            ...RiskLevel.values.map((level) {
              return DropdownMenuItem<RiskLevel?>(
                value: level,
                child: Text(_getRiskLevelDisplayName(level)),
              );
            }),
          ],
          onChanged: (level) {
            setState(() {
              _riskLevelFilter = level;
            });
          },
        ),
      ],
    );
  }

  /// Builds date range selector
  Widget _buildDateRangeSelector() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          'Period:',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(width: 8),
        TextButton.icon(
          icon: const Icon(Icons.date_range, size: 16),
          label: Text(
            '${DateFormat('MMM dd').format(_currentDateRange.start)} - ${DateFormat('MMM dd').format(_currentDateRange.end)}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          onPressed: () => _selectDateRange(),
        ),
      ],
    );
  }

  /// Builds refresh button
  Widget _buildRefreshButton() {
    return IconButton(
      icon: const Icon(Icons.refresh),
      onPressed: () {
        setState(() {
          // Trigger refresh of all components
          _loadingStates.updateAll((key, value) => true);
        });

        // Simulate refresh delay
        Future.delayed(const Duration(milliseconds: 500), () {
          if (mounted) {
            setState(() {
              _loadingStates.updateAll((key, value) => false);
            });
          }
        });
      },
      tooltip: 'Refresh Dashboard',
    );
  }

  /// Builds export button
  Widget _buildExportButton() {
    return IconButton(
      icon: const Icon(Icons.download),
      onPressed: () => _showExportDialog(),
      tooltip: 'Export Analysis',
    );
  }

  /// Builds view mode selector
  Widget _buildViewModeSelector() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: OutbreakViewMode.values.map((mode) {
          final isSelected = mode == _viewMode;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _getViewModeIcon(mode),
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                  Text(_getViewModeDisplayName(mode)),
                ],
              ),
              selected: isSelected,
              onSelected: (selected) {
                if (selected) {
                  setState(() {
                    _viewMode = mode;
                  });
                }
              },
            ),
          );
        }).toList(),
      ),
    );
  }

  /// Builds main dashboard content based on view mode
  Widget _buildMainContent() {
    switch (_viewMode) {
      case OutbreakViewMode.overview:
        return _buildOverviewGrid();
      case OutbreakViewMode.geographic:
        return _buildGeographicView();
      case OutbreakViewMode.temporal:
        return _buildTemporalView();
      case OutbreakViewMode.alerts:
        return _buildAlertsView();
    }
  }

  /// Builds overview grid with all components
  Widget _buildOverviewGrid() {
    return GridView.count(
      crossAxisCount: 2,
      childAspectRatio: 1.2,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      children: [
        RiskHeatMapWidget(
          riskTrends: _getFilteredRiskTrends(),
          height: 300,
          dateRange: _currentDateRange,
          enableInteractivity: widget.enableInteractivity,
        ),
        TemporalPatternChart(
          riskTrends: _getFilteredRiskTrends(),
          height: 300,
          dateRange: _currentDateRange,
          enableInteractivity: widget.enableInteractivity,
        ),
        if (widget.showPopulationRisk)
          PopulationRiskWidget(
            riskTrends: _getFilteredRiskTrends(),
            height: 300,
            region: _selectedRegion,
          ),
        if (widget.showEarlyWarning)
          EarlyWarningIndicators(
            riskTrends: _getFilteredRiskTrends(),
            alertStatistics: widget.analyticsData.alertStatistics,
            height: 300,
          ),
      ],
    );
  }

  /// Builds geographic-focused view
  Widget _buildGeographicView() {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: RiskHeatMapWidget(
            riskTrends: _getFilteredRiskTrends(),
            height: double.infinity,
            dateRange: _currentDateRange,
            enableInteractivity: widget.enableInteractivity,
            showDetailedTooltips: true,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            children: [
              Expanded(
                child: PopulationRiskWidget(
                  riskTrends: _getFilteredRiskTrends(),
                  height: double.infinity,
                  region: _selectedRegion,
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: AlertCorrelationDisplay(
                  riskTrends: _getFilteredRiskTrends(),
                  alertStatistics: widget.analyticsData.alertStatistics,
                  height: double.infinity,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds temporal analysis view
  Widget _buildTemporalView() {
    return Column(
      children: [
        Expanded(
          flex: 2,
          child: TemporalPatternChart(
            riskTrends: _getFilteredRiskTrends(),
            height: double.infinity,
            dateRange: _currentDateRange,
            enableInteractivity: widget.enableInteractivity,
            showTrendLines: true,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: RiskPredictionChart(
            riskTrends: _getFilteredRiskTrends(),
            predictionAccuracy: widget.analyticsData.predictionAccuracy,
            height: double.infinity,
            enableInteractivity: widget.enableInteractivity,
          ),
        ),
      ],
    );
  }

  /// Builds alerts-focused view
  Widget _buildAlertsView() {
    return Row(
      children: [
        Expanded(
          child: AlertCorrelationDisplay(
            riskTrends: _getFilteredRiskTrends(),
            alertStatistics: widget.analyticsData.alertStatistics,
            height: double.infinity,
            showDetailedAnalysis: true,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: EarlyWarningIndicators(
            riskTrends: _getFilteredRiskTrends(),
            alertStatistics: widget.analyticsData.alertStatistics,
            height: double.infinity,
            showPredictiveIndicators: true,
          ),
        ),
      ],
    );
  }

  /// Gets filtered risk trends based on current filters
  List<RiskTrend> _getFilteredRiskTrends() {
    var trends = widget.analyticsData.riskTrends;

    // Filter by risk level
    if (_riskLevelFilter != null) {
      trends = trends.where((t) => t.riskLevel == _riskLevelFilter).toList();
    }

    // Filter by date range
    trends = trends.where((t) => _currentDateRange.contains(t.date)).toList();

    return trends;
  }

  /// Gets risk level display name
  String _getRiskLevelDisplayName(RiskLevel level) {
    switch (level) {
      case RiskLevel.low:
        return 'Low Risk';
      case RiskLevel.medium:
        return 'Medium Risk';
      case RiskLevel.high:
        return 'High Risk';
      case RiskLevel.critical:
        return 'Critical Risk';
    }
  }

  /// Gets view mode icon
  IconData _getViewModeIcon(OutbreakViewMode mode) {
    switch (mode) {
      case OutbreakViewMode.overview:
        return Icons.dashboard;
      case OutbreakViewMode.geographic:
        return Icons.map;
      case OutbreakViewMode.temporal:
        return Icons.timeline;
      case OutbreakViewMode.alerts:
        return Icons.notifications;
    }
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(OutbreakViewMode mode) {
    switch (mode) {
      case OutbreakViewMode.overview:
        return 'Overview';
      case OutbreakViewMode.geographic:
        return 'Geographic';
      case OutbreakViewMode.temporal:
        return 'Temporal';
      case OutbreakViewMode.alerts:
        return 'Alerts';
    }
  }

  /// Formats population numbers for display
  String _formatPopulation(int population) {
    if (population >= 1000000) {
      return '${(population / 1000000).toStringAsFixed(1)}M';
    } else if (population >= 1000) {
      return '${(population / 1000).toStringAsFixed(1)}K';
    }
    return population.toString();
  }

  /// Shows date range selection dialog
  Future<void> _selectDateRange() async {
    final dateRange = await showDateRangePicker(
      context: context,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 30)),
      initialDateRange: DateTimeRange(
        start: _currentDateRange.start,
        end: _currentDateRange.end,
      ),
    );

    if (dateRange != null) {
      setState(() {
        _currentDateRange = DateRange(
          start: dateRange.start,
          end: dateRange.end,
        );
      });
    }
  }

  /// Shows export options dialog
  void _showExportDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Export Analysis'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: Icon(Icons.picture_as_pdf),
              title: Text('PDF Report'),
              subtitle: Text('Comprehensive outbreak analysis report'),
            ),
            ListTile(
              leading: Icon(Icons.table_chart),
              title: Text('CSV Data'),
              subtitle: Text('Raw risk trend and alert data'),
            ),
            ListTile(
              leading: Icon(Icons.image),
              title: Text('PNG Images'),
              subtitle: Text('High-resolution visualization images'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              // TODO: Implement export functionality
            },
            child: const Text('Export'),
          ),
        ],
      ),
    );
  }
}

/// Outbreak view mode enumeration
enum OutbreakViewMode {
  overview,
  geographic,
  temporal,
  alerts,
}