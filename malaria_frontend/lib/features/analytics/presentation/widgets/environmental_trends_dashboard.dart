/// Environmental trends dashboard widget for comprehensive climate analysis
///
/// This dashboard provides a complete environmental analysis interface combining
/// temperature, rainfall, humidity, and vegetation trends with scientific
/// visualization capabilities for malaria prediction analytics.
///
/// Features:
/// - Multi-factor environmental analysis
/// - Seasonal pattern overlays
/// - Climate anomaly detection
/// - Correlation analysis between factors
/// - Scientific scales and units
/// - Interactive data exploration
///
/// Usage:
/// ```dart
/// EnvironmentalTrendsDashboard(
///   environmentalData: environmentalData,
///   showCorrelations: true,
///   showAnomalies: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';
import 'temperature_trend_chart.dart';
import 'rainfall_pattern_chart.dart';
import 'humidity_trend_display.dart';
import 'vegetation_index_chart.dart';
import 'seasonal_overlay_widget.dart';
import 'climate_anomaly_indicator.dart';
import 'metric_card.dart';

/// Main environmental trends dashboard widget
class EnvironmentalTrendsDashboard extends StatefulWidget {
  /// Environmental data for comprehensive analysis
  final EnvironmentalData environmentalData;

  /// Date range for filtering environmental data
  final DateRange? dateRange;

  /// Whether to show correlation analysis
  final bool showCorrelations;

  /// Whether to show climate anomaly detection
  final bool showAnomalies;

  /// Whether to enable seasonal pattern overlays
  final bool showSeasonalPatterns;

  /// Dashboard height
  final double? height;

  /// Whether to show as tabbed interface
  final bool useTabbedLayout;

  /// Constructor requiring environmental data
  const EnvironmentalTrendsDashboard({
    super.key,
    required this.environmentalData,
    this.dateRange,
    this.showCorrelations = true,
    this.showAnomalies = true,
    this.showSeasonalPatterns = true,
    this.height,
    this.useTabbedLayout = false,
  });

  @override
  State<EnvironmentalTrendsDashboard> createState() => _EnvironmentalTrendsDashboardState();
}

class _EnvironmentalTrendsDashboardState extends State<EnvironmentalTrendsDashboard>
    with TickerProviderStateMixin {
  /// Tab controller for dashboard sections
  late TabController _tabController;

  /// Current dashboard view mode
  DashboardViewMode _viewMode = DashboardViewMode.overview;

  /// Selected environmental factors for analysis
  final Set<EnvironmentalFactor> _selectedFactors = {
    EnvironmentalFactor.temperature,
    EnvironmentalFactor.rainfall,
    EnvironmentalFactor.humidity,
    EnvironmentalFactor.vegetation,
  };

  /// Dashboard configuration settings
  bool _showDataQuality = true;
  bool _showMalariaRiskOverlay = true;
  bool _showExtremeEvents = true;
  bool _enableRealTimeUpdates = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: widget.useTabbedLayout ? 4 : 1,
      vsync: this,
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.height,
      child: Card(
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDashboardHeader(),
            _buildControlPanel(),
            if (widget.showAnomalies) _buildAnomalyAlerts(),
            Expanded(
              child: widget.useTabbedLayout
                  ? _buildTabbedLayout()
                  : _buildGridLayout(),
            ),
            if (widget.showCorrelations) _buildCorrelationSummary(),
          ],
        ),
      ),
    );
  }

  /// Builds the dashboard header with title and metadata
  Widget _buildDashboardHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
            Theme.of(context).colorScheme.secondary.withValues(alpha: 0.05),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Environmental Trends Analysis',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Comprehensive climate analysis for malaria prediction',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
                const SizedBox(height: 8),
                _buildMetadataRow(),
              ],
            ),
          ),
          _buildHeaderActions(),
        ],
      ),
    );
  }

  /// Builds metadata row with region, date range, and data quality
  Widget _buildMetadataRow() {
    return Wrap(
      spacing: 16,
      runSpacing: 4,
      children: [
        _buildMetadataChip(
          icon: Icons.location_on_outlined,
          label: 'Region',
          value: widget.environmentalData.region,
          color: Colors.blue,
        ),
        _buildMetadataChip(
          icon: Icons.date_range_outlined,
          label: 'Period',
          value: widget.dateRange != null
              ? '${DateFormat('MMM yyyy').format(widget.dateRange!.start)} - ${DateFormat('MMM yyyy').format(widget.dateRange!.end)}'
              : '${DateFormat('MMM yyyy').format(widget.environmentalData.dateRange.start)} - ${DateFormat('MMM yyyy').format(widget.environmentalData.dateRange.end)}',
          color: Colors.green,
        ),
        _buildMetadataChip(
          icon: Icons.verified_outlined,
          label: 'Quality',
          value: '${(widget.environmentalData.dataQuality * 100).toStringAsFixed(1)}%',
          color: _getQualityColor(widget.environmentalData.dataQuality),
        ),
        _buildMetadataChip(
          icon: Icons.update_outlined,
          label: 'Updated',
          value: DateFormat('MMM d, HH:mm').format(widget.environmentalData.lastUpdated),
          color: Colors.orange,
        ),
      ],
    );
  }

  /// Builds individual metadata chip
  Widget _buildMetadataChip({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            '$label: $value',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds header action buttons
  Widget _buildHeaderActions() {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          icon: Icon(
            _enableRealTimeUpdates ? Icons.sync : Icons.sync_disabled,
            color: _enableRealTimeUpdates
                ? Theme.of(context).colorScheme.primary
                : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          onPressed: () {
            setState(() {
              _enableRealTimeUpdates = !_enableRealTimeUpdates;
            });
            // TODO: Implement real-time data updates
          },
          tooltip: 'Toggle Real-time Updates',
        ),
        IconButton(
          icon: Icon(
            Icons.settings_outlined,
            color: Theme.of(context).colorScheme.primary,
          ),
          onPressed: _showDashboardSettings,
          tooltip: 'Dashboard Settings',
        ),
        IconButton(
          icon: Icon(
            Icons.info_outline,
            color: Theme.of(context).colorScheme.primary,
          ),
          onPressed: _showDashboardInfo,
          tooltip: 'Environmental Analysis Information',
        ),
      ],
    );
  }

  /// Builds control panel for dashboard configuration
  Widget _buildControlPanel() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Text(
                'View Mode:',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: DashboardViewMode.values.map((mode) {
                      final isSelected = mode == _viewMode;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(_getViewModeDisplayName(mode)),
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
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Text(
                'Factors:',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: EnvironmentalFactor.values.map((factor) {
                      final isSelected = _selectedFactors.contains(factor);
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: FilterChip(
                          label: Text(_getFactorDisplayName(factor)),
                          selected: isSelected,
                          onSelected: (selected) {
                            setState(() {
                              if (selected) {
                                _selectedFactors.add(factor);
                              } else if (_selectedFactors.length > 1) {
                                _selectedFactors.remove(factor);
                              }
                            });
                          },
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds anomaly alerts section
  Widget _buildAnomalyAlerts() {
    return ClimateAnomalyIndicator(
      environmentalData: widget.environmentalData,
      dateRange: widget.dateRange,
      selectedFactors: _selectedFactors,
    );
  }

  /// Builds tabbed layout for organized view
  Widget _buildTabbedLayout() {
    return Column(
      children: [
        TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Temperature', icon: Icon(Icons.thermostat_outlined)),
            Tab(text: 'Rainfall', icon: Icon(Icons.water_drop_outlined)),
            Tab(text: 'Humidity', icon: Icon(Icons.opacity_outlined)),
            Tab(text: 'Vegetation', icon: Icon(Icons.eco_outlined)),
          ],
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildTemperatureTab(),
              _buildRainfallTab(),
              _buildHumidityTab(),
              _buildVegetationTab(),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds grid layout for comprehensive view
  Widget _buildGridLayout() {
    switch (_viewMode) {
      case DashboardViewMode.overview:
        return _buildOverviewGrid();
      case DashboardViewMode.detailed:
        return _buildDetailedGrid();
      case DashboardViewMode.comparison:
        return _buildComparisonGrid();
      case DashboardViewMode.correlation:
        return _buildCorrelationGrid();
    }
  }

  /// Builds overview grid with key metrics and charts
  Widget _buildOverviewGrid() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isWideScreen = constraints.maxWidth > 1200;
          return GridView.count(
            crossAxisCount: isWideScreen ? 3 : 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: isWideScreen ? 1.5 : 1.2,
            children: [
              if (_selectedFactors.contains(EnvironmentalFactor.temperature))
                TemperatureTrendChart(
                  temperatureData: widget.environmentalData.temperature,
                  height: 300,
                  dateRange: widget.dateRange,
                  showAnomalies: widget.showAnomalies,
                  showCorrelation: widget.showCorrelations,
                ),
              if (_selectedFactors.contains(EnvironmentalFactor.rainfall))
                RainfallPatternChart(
                  rainfallData: widget.environmentalData.rainfall,
                  height: 300,
                  dateRange: widget.dateRange,
                  showExtremeEvents: _showExtremeEvents,
                  showRiskPeriods: _showMalariaRiskOverlay,
                ),
              if (_selectedFactors.contains(EnvironmentalFactor.humidity))
                HumidityTrendDisplay(
                  humidityData: widget.environmentalData.humidity,
                  height: 300,
                  dateRange: widget.dateRange,
                  showSeasonalPattern: widget.showSeasonalPatterns,
                ),
              if (_selectedFactors.contains(EnvironmentalFactor.vegetation))
                VegetationIndexChart(
                  vegetationData: widget.environmentalData.vegetation,
                  height: 300,
                  dateRange: widget.dateRange,
                  showLandCover: true,
                ),
              if (widget.showSeasonalPatterns)
                SeasonalOverlayWidget(
                  environmentalData: widget.environmentalData,
                  selectedFactors: _selectedFactors,
                  height: 300,
                ),
            ],
          );
        },
      ),
    );
  }

  /// Builds detailed grid for in-depth analysis
  Widget _buildDetailedGrid() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          if (_selectedFactors.contains(EnvironmentalFactor.temperature))
            Container(
              height: 400,
              margin: const EdgeInsets.only(bottom: 16),
              child: TemperatureTrendChart(
                temperatureData: widget.environmentalData.temperature,
                height: 400,
                dateRange: widget.dateRange,
                showAnomalies: widget.showAnomalies,
                showCorrelation: widget.showCorrelations,
                showAllSeries: true,
              ),
            ),
          if (_selectedFactors.contains(EnvironmentalFactor.rainfall))
            Container(
              height: 400,
              margin: const EdgeInsets.only(bottom: 16),
              child: RainfallPatternChart(
                rainfallData: widget.environmentalData.rainfall,
                height: 400,
                dateRange: widget.dateRange,
                showExtremeEvents: _showExtremeEvents,
                showRiskPeriods: _showMalariaRiskOverlay,
                viewMode: RainfallViewMode.monthly,
              ),
            ),
          Row(
            children: [
              if (_selectedFactors.contains(EnvironmentalFactor.humidity))
                Expanded(
                  child: Container(
                    height: 350,
                    margin: const EdgeInsets.only(right: 8),
                    child: HumidityTrendDisplay(
                      humidityData: widget.environmentalData.humidity,
                      height: 350,
                      dateRange: widget.dateRange,
                      showSeasonalPattern: widget.showSeasonalPatterns,
                    ),
                  ),
                ),
              if (_selectedFactors.contains(EnvironmentalFactor.vegetation))
                Expanded(
                  child: Container(
                    height: 350,
                    margin: const EdgeInsets.only(left: 8),
                    child: VegetationIndexChart(
                      vegetationData: widget.environmentalData.vegetation,
                      height: 350,
                      dateRange: widget.dateRange,
                      showLandCover: true,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds comparison grid for factor comparison
  Widget _buildComparisonGrid() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Expanded(
            flex: 2,
            child: SeasonalOverlayWidget(
              environmentalData: widget.environmentalData,
              selectedFactors: _selectedFactors,
              height: 400,
              showComparison: true,
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: Row(
              children: [
                Expanded(
                  child: MetricCard(
                    title: 'Max Temperature',
                    value: _getMaxTemperature(),
                    subtitle: 'Optimal: 25°C for malaria transmission',
                    icon: Icons.thermostat_outlined,
                    color: Colors.red,
                    valueFormatter: (value) => '${value.toStringAsFixed(1)}°C',
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: MetricCard(
                    title: 'Total Rainfall',
                    value: _getTotalRainfall(),
                    subtitle: 'Threshold: 80mm/month for transmission',
                    icon: Icons.water_drop_outlined,
                    color: Colors.blue,
                    valueFormatter: (value) => '${value.toStringAsFixed(0)}mm',
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Builds correlation grid for factor relationships
  Widget _buildCorrelationGrid() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Theme.of(context).dividerColor,
                ),
              ),
              child: _buildCorrelationMatrix(),
            ),
          ),
          const SizedBox(height: 16),
          if (widget.showSeasonalPatterns)
            Expanded(
              child: SeasonalOverlayWidget(
                environmentalData: widget.environmentalData,
                selectedFactors: _selectedFactors,
                height: 300,
                showCorrelation: true,
              ),
            ),
        ],
      ),
    );
  }

  /// Builds individual temperature tab
  Widget _buildTemperatureTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: TemperatureTrendChart(
        temperatureData: widget.environmentalData.temperature,
        height: double.infinity,
        dateRange: widget.dateRange,
        showAnomalies: widget.showAnomalies,
        showCorrelation: widget.showCorrelations,
        showAllSeries: false,
      ),
    );
  }

  /// Builds individual rainfall tab
  Widget _buildRainfallTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: RainfallPatternChart(
        rainfallData: widget.environmentalData.rainfall,
        height: double.infinity,
        dateRange: widget.dateRange,
        showExtremeEvents: _showExtremeEvents,
        showRiskPeriods: _showMalariaRiskOverlay,
      ),
    );
  }

  /// Builds individual humidity tab
  Widget _buildHumidityTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: HumidityTrendDisplay(
        humidityData: widget.environmentalData.humidity,
        height: double.infinity,
        dateRange: widget.dateRange,
        showSeasonalPattern: widget.showSeasonalPatterns,
      ),
    );
  }

  /// Builds individual vegetation tab
  Widget _buildVegetationTab() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: VegetationIndexChart(
        vegetationData: widget.environmentalData.vegetation,
        height: double.infinity,
        dateRange: widget.dateRange,
        showLandCover: true,
      ),
    );
  }

  /// Builds correlation summary panel
  Widget _buildCorrelationSummary() {
    final correlations = _calculateCorrelations();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
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
            'Environmental Factor Correlations',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: correlations.entries.map((entry) {
              return _buildCorrelationChip(entry.key, entry.value);
            }).toList(),
          ),
        ],
      ),
    );
  }

  /// Builds correlation matrix visualization
  Widget _buildCorrelationMatrix() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Environmental Factor Correlation Matrix',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: Center(
              child: Text(
                'Correlation matrix visualization will be implemented here\nshowing relationships between environmental factors',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds individual correlation chip
  Widget _buildCorrelationChip(String label, double correlation) {
    final color = _getCorrelationColor(correlation);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              correlation.toStringAsFixed(2),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 11,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Calculates correlations between environmental factors
  Map<String, double> _calculateCorrelations() {
    // Mock correlation data - would be calculated from actual data
    return {
      'Temp-Rainfall': -0.34,
      'Temp-Humidity': -0.67,
      'Temp-Vegetation': 0.45,
      'Rainfall-Humidity': 0.58,
      'Rainfall-Vegetation': 0.72,
      'Humidity-Vegetation': 0.39,
    };
  }

  /// Gets correlation color based on strength
  Color _getCorrelationColor(double correlation) {
    final absCorr = correlation.abs();
    if (absCorr >= 0.7) return Colors.red;
    if (absCorr >= 0.5) return Colors.orange;
    if (absCorr >= 0.3) return Colors.yellow.shade700;
    return Colors.grey;
  }

  /// Gets quality color based on percentage
  Color _getQualityColor(double quality) {
    if (quality >= 0.9) return Colors.green;
    if (quality >= 0.7) return Colors.orange;
    return Colors.red;
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(DashboardViewMode mode) {
    switch (mode) {
      case DashboardViewMode.overview:
        return 'Overview';
      case DashboardViewMode.detailed:
        return 'Detailed';
      case DashboardViewMode.comparison:
        return 'Comparison';
      case DashboardViewMode.correlation:
        return 'Correlation';
    }
  }

  /// Gets environmental factor display name
  String _getFactorDisplayName(EnvironmentalFactor factor) {
    switch (factor) {
      case EnvironmentalFactor.temperature:
        return 'Temperature';
      case EnvironmentalFactor.rainfall:
        return 'Rainfall';
      case EnvironmentalFactor.vegetation:
        return 'Vegetation';
      case EnvironmentalFactor.humidity:
        return 'Humidity';
      case EnvironmentalFactor.windSpeed:
        return 'Wind Speed';
      case EnvironmentalFactor.pressure:
        return 'Pressure';
    }
  }

  /// Calculates minimum temperature
  double _getMinTemperature() {
    final temps = widget.environmentalData.temperature.dailyMin;
    if (temps.isEmpty) return 0;
    return temps.map((t) => t.temperature).reduce((a, b) => a < b ? a : b);
  }

  /// Calculates maximum temperature
  double _getMaxTemperature() {
    final temps = widget.environmentalData.temperature.dailyMax;
    if (temps.isEmpty) return 0;
    return temps.map((t) => t.temperature).reduce((a, b) => a > b ? a : b);
  }

  /// Calculates total rainfall
  double _getTotalRainfall() {
    final rainfall = widget.environmentalData.rainfall.monthly;
    if (rainfall.isEmpty) return 0;
    return rainfall.map((r) => r.rainfall).reduce((a, b) => a + b);
  }

  /// Shows dashboard settings dialog
  void _showDashboardSettings() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Dashboard Settings'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SwitchListTile(
              title: const Text('Show Data Quality'),
              value: _showDataQuality,
              onChanged: (value) {
                setState(() {
                  _showDataQuality = value;
                });
                Navigator.of(context).pop();
              },
            ),
            SwitchListTile(
              title: const Text('Show Malaria Risk Overlay'),
              value: _showMalariaRiskOverlay,
              onChanged: (value) {
                setState(() {
                  _showMalariaRiskOverlay = value;
                });
                Navigator.of(context).pop();
              },
            ),
            SwitchListTile(
              title: const Text('Show Extreme Events'),
              value: _showExtremeEvents,
              onChanged: (value) {
                setState(() {
                  _showExtremeEvents = value;
                });
                Navigator.of(context).pop();
              },
            ),
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

  /// Shows dashboard information dialog
  void _showDashboardInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Environmental Trends Dashboard'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Dashboard Features:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Multi-factor environmental analysis'),
              Text('• Real-time climate monitoring'),
              Text('• Anomaly detection and alerts'),
              Text('• Correlation analysis between factors'),
              Text('• Seasonal pattern recognition'),
              Text('• Malaria transmission risk assessment'),
              SizedBox(height: 16),
              Text(
                'Scientific Visualization:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Proper scientific scales and units'),
              Text('• Data quality indicators'),
              Text('• Statistical confidence measures'),
              Text('• Temporal and spatial analysis'),
              Text('• Climate anomaly detection'),
              SizedBox(height: 16),
              Text(
                'Malaria Relevance:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Temperature: 25°C optimal for transmission'),
              Text('• Rainfall: 80mm/month minimum threshold'),
              Text('• Humidity: High levels favor mosquito survival'),
              Text('• Vegetation: Breeding site availability'),
            ],
          ),
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

/// Dashboard view mode enumeration
enum DashboardViewMode {
  overview,
  detailed,
  comparison,
  correlation,
}