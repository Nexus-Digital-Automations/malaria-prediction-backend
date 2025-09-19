/// Environmental summary widget with key climate indicators
///
/// This widget displays a comprehensive summary of environmental conditions
/// including key climate indicators, threshold alerts, risk assessments,
/// and trend summaries for malaria transmission analysis.
///
/// Usage:
/// ```dart
/// EnvironmentalSummaryWidget(
///   environmentalData: environmentalData,
///   climateMetrics: climateMetrics,
///   showRiskAssessment: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Environmental summary widget with key climate indicators and risk assessment
class EnvironmentalSummaryWidget extends StatefulWidget {
  /// Environmental data for current analysis period
  final EnvironmentalData environmentalData;

  /// Climate metrics for correlation and trend analysis
  final ClimateMetrics? climateMetrics;

  /// Weather trend data for historical context
  final WeatherTrend? weatherTrend;

  /// Whether to show malaria risk assessment
  final bool showRiskAssessment;

  /// Whether to show threshold alerts
  final bool showThresholdAlerts;

  /// Whether to show trend indicators
  final bool showTrendIndicators;

  /// Constructor requiring environmental data
  const EnvironmentalSummaryWidget({
    super.key,
    required this.environmentalData,
    this.climateMetrics,
    this.weatherTrend,
    this.showRiskAssessment = true,
    this.showThresholdAlerts = true,
    this.showTrendIndicators = true,
  });

  @override
  State<EnvironmentalSummaryWidget> createState() => _EnvironmentalSummaryWidgetState();
}

class _EnvironmentalSummaryWidgetState extends State<EnvironmentalSummaryWidget> {
  /// Color scheme for risk levels
  final Map<MalariaRiskLevel, Color> _riskColors = {
    MalariaRiskLevel.minimal: Colors.green,
    MalariaRiskLevel.low: Colors.lightGreen,
    MalariaRiskLevel.moderate: Colors.orange,
    MalariaRiskLevel.high: Colors.red,
    MalariaRiskLevel.critical: Colors.purple,
  };

  /// Environmental factor icons
  final Map<EnvironmentalFactor, IconData> _factorIcons = {
    EnvironmentalFactor.temperature: Icons.thermostat,
    EnvironmentalFactor.rainfall: Icons.water_drop,
    EnvironmentalFactor.humidity: Icons.opacity,
    EnvironmentalFactor.vegetation: Icons.eco,
    EnvironmentalFactor.windSpeed: Icons.air,
    EnvironmentalFactor.pressure: Icons.speed,
  };

  /// Threshold values for malaria transmission
  final Map<String, double> _transmissionThresholds = {
    'minTemperature': 18.0,
    'maxTemperature': 34.0,
    'optimalTemperature': 25.0,
    'minHumidity': 60.0,
    'optimalHumidity': 80.0,
    'minRainfall': 80.0,
    'optimalRainfall': 150.0,
  };

  /// Selected view mode for summary display
  SummaryViewMode _viewMode = SummaryViewMode.overview;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 16),
            _buildViewSelector(),
            const SizedBox(height: 16),
            _buildSummaryContent(),
            if (widget.showThresholdAlerts) ...[
              const SizedBox(height: 16),
              _buildThresholdAlerts(),
            ],
            if (widget.showRiskAssessment) ...[
              const SizedBox(height: 16),
              _buildRiskAssessment(),
            ],
          ],
        ),
      ),
    );
  }

  /// Builds the summary header with title and controls
  Widget _buildHeader() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Environmental Summary',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '${widget.environmentalData.region} • '
                '${DateFormat('MMM d, yyyy').format(widget.environmentalData.lastUpdated)}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        Row(
          children: [
            IconButton(
              icon: Icon(
                Icons.refresh,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _refreshData(),
              tooltip: 'Refresh Data',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showEnvironmentalInfo(),
              tooltip: 'Environmental Info',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds view mode selector
  Widget _buildViewSelector() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: SummaryViewMode.values.map((mode) {
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
    );
  }

  /// Builds summary content based on selected view mode
  Widget _buildSummaryContent() {
    switch (_viewMode) {
      case SummaryViewMode.overview:
        return _buildOverviewSummary();
      case SummaryViewMode.detailed:
        return _buildDetailedSummary();
      case SummaryViewMode.trends:
        return _buildTrendsSummary();
      case SummaryViewMode.comparisons:
        return _buildComparisonSummary();
    }
  }

  /// Builds overview summary with key indicators
  Widget _buildOverviewSummary() {
    final currentStats = _calculateCurrentStats();

    return Column(
      children: [
        // Key environmental indicators grid
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.5,
          ),
          itemCount: currentStats.length,
          itemBuilder: (context, index) {
            final stat = currentStats[index];
            return _buildIndicatorCard(stat);
          },
        ),
        const SizedBox(height: 16),
        // Environmental quality meter
        _buildEnvironmentalQualityMeter(),
      ],
    );
  }

  /// Builds detailed summary with comprehensive metrics
  Widget _buildDetailedSummary() {
    return Column(
      children: [
        _buildTemperatureDetails(),
        const SizedBox(height: 12),
        _buildHumidityDetails(),
        const SizedBox(height: 12),
        _buildRainfallDetails(),
        const SizedBox(height: 12),
        _buildVegetationDetails(),
      ],
    );
  }

  /// Builds trends summary with historical context
  Widget _buildTrendsSummary() {
    if (widget.weatherTrend == null) {
      return _buildNoTrendDataMessage();
    }

    return Column(
      children: [
        _buildTrendIndicator(
          'Temperature Trend',
          widget.weatherTrend!.temperatureTrend,
          '°C/year',
          Icons.thermostat,
          widget.weatherTrend!.temperatureTrendConfidence,
        ),
        const SizedBox(height: 12),
        _buildTrendIndicator(
          'Rainfall Trend',
          widget.weatherTrend!.rainfallTrend,
          'mm/year',
          Icons.water_drop,
          widget.weatherTrend!.rainfallTrendConfidence,
        ),
        const SizedBox(height: 12),
        _buildTrendIndicator(
          'Humidity Trend',
          widget.weatherTrend!.humidityTrend,
          '%/year',
          Icons.opacity,
          widget.weatherTrend!.humidityTrendConfidence,
        ),
        const SizedBox(height: 16),
        _buildClimateChangeIndicators(),
      ],
    );
  }

  /// Builds comparison summary with seasonal context
  Widget _buildComparisonSummary() {
    if (widget.climateMetrics == null) {
      return _buildNoComparisonDataMessage();
    }

    return Column(
      children: [
        _buildSeasonalComparison(),
        const SizedBox(height: 16),
        _buildHistoricalComparison(),
      ],
    );
  }

  /// Builds individual indicator card
  Widget _buildIndicatorCard(EnvironmentalIndicator indicator) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: _getIndicatorBorderColor(indicator.status),
          width: 2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _factorIcons[indicator.factor] ?? Icons.eco,
                color: _getIndicatorBorderColor(indicator.status),
                size: 24,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  indicator.name,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${indicator.value.toStringAsFixed(1)}${indicator.unit}',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: _getIndicatorBorderColor(indicator.status),
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: _getIndicatorBorderColor(indicator.status).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  indicator.status.name.toUpperCase(),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: _getIndicatorBorderColor(indicator.status),
                    fontWeight: FontWeight.bold,
                    fontSize: 10,
                  ),
                ),
              ),
              const Spacer(),
              if (indicator.trend != 0)
                Icon(
                  indicator.trend > 0 ? Icons.trending_up : Icons.trending_down,
                  color: indicator.trend > 0 ? Colors.red : Colors.blue,
                  size: 16,
                ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds environmental quality meter
  Widget _buildEnvironmentalQualityMeter() {
    final qualityScore = _calculateEnvironmentalQuality();
    final qualityLevel = _getQualityLevel(qualityScore);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _riskColors[qualityLevel]!.withValues(alpha: 0.1),
            _riskColors[qualityLevel]!.withValues(alpha: 0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _riskColors[qualityLevel]!.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Text(
            'Environmental Quality for Malaria Transmission',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 120,
                height: 120,
                child: CircularProgressIndicator(
                  value: qualityScore / 100,
                  strokeWidth: 12,
                  backgroundColor: Colors.grey.shade300,
                  valueColor: AlwaysStoppedAnimation<Color>(_riskColors[qualityLevel]!),
                ),
              ),
              Column(
                children: [
                  Text(
                    '${qualityScore.toStringAsFixed(0)}%',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: _riskColors[qualityLevel],
                    ),
                  ),
                  Text(
                    qualityLevel.name.toUpperCase(),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: _riskColors[qualityLevel],
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            _getQualityDescription(qualityLevel),
            style: Theme.of(context).textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds temperature details
  Widget _buildTemperatureDetails() {
    final tempData = widget.environmentalData.temperature;
    final currentTemp = tempData.dailyMean.isNotEmpty
        ? tempData.dailyMean.last.temperature
        : 0.0;

    return _buildDetailCard(
      'Temperature Analysis',
      Icons.thermostat,
      [
        'Current: ${currentTemp.toStringAsFixed(1)}°C',
        'Optimal for transmission: ${_transmissionThresholds['optimalTemperature']}°C',
        'Transmission range: ${_transmissionThresholds['minTemperature']}°C - ${_transmissionThresholds['maxTemperature']}°C',
        'Recent anomalies: ${tempData.anomalies.where((a) => a.significance.abs() > 2).length}',
      ],
      _getTemperatureRiskLevel(currentTemp),
    );
  }

  /// Builds humidity details
  Widget _buildHumidityDetails() {
    final humidityData = widget.environmentalData.humidity;
    final currentHumidity = humidityData.relativeHumidity.isNotEmpty
        ? humidityData.relativeHumidity.last.humidity
        : 0.0;

    return _buildDetailCard(
      'Humidity Analysis',
      Icons.opacity,
      [
        'Current: ${currentHumidity.toStringAsFixed(1)}%',
        'Mosquito survival threshold: ${_transmissionThresholds['minHumidity']}%',
        'Optimal range: ${_transmissionThresholds['optimalHumidity']}%+',
        'Status: ${_getHumidityStatus(currentHumidity)}',
      ],
      _getHumidityRiskLevel(currentHumidity),
    );
  }

  /// Builds rainfall details
  Widget _buildRainfallDetails() {
    final rainfallData = widget.environmentalData.rainfall;
    final monthlyTotal = rainfallData.monthly.isNotEmpty
        ? rainfallData.monthly.last.rainfall
        : 0.0;

    return _buildDetailCard(
      'Rainfall Analysis',
      Icons.water_drop,
      [
        'Monthly total: ${monthlyTotal.toStringAsFixed(1)}mm',
        'Transmission threshold: ${_transmissionThresholds['minRainfall']}mm',
        'Optimal range: ${_transmissionThresholds['optimalRainfall']}mm+',
        'Extreme events: ${rainfallData.extremeEvents.length}',
      ],
      _getRainfallRiskLevel(monthlyTotal),
    );
  }

  /// Builds vegetation details
  Widget _buildVegetationDetails() {
    final vegetationData = widget.environmentalData.vegetation;
    final currentNDVI = vegetationData.ndvi.isNotEmpty
        ? vegetationData.ndvi.last.value
        : 0.0;

    return _buildDetailCard(
      'Vegetation Analysis',
      Icons.eco,
      [
        'Current NDVI: ${currentNDVI.toStringAsFixed(2)}',
        'Vegetation health: ${_getVegetationHealth(currentNDVI)}',
        'Breeding habitat: ${_getBreedingHabitat(currentNDVI)}',
        'Land cover: ${_getDominantLandCover()}',
      ],
      _getVegetationRiskLevel(currentNDVI),
    );
  }

  /// Builds detail card
  Widget _buildDetailCard(
    String title,
    IconData icon,
    List<String> details,
    MalariaRiskLevel riskLevel,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _riskColors[riskLevel]!.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _riskColors[riskLevel]!.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: _riskColors[riskLevel], size: 20),
              const SizedBox(width: 8),
              Text(
                title,
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: _riskColors[riskLevel],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...details.map((detail) => Padding(
            padding: const EdgeInsets.only(bottom: 2),
            child: Text(
              '• $detail',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          )),
        ],
      ),
    );
  }

  /// Builds trend indicator
  Widget _buildTrendIndicator(
    String name,
    double trend,
    String unit,
    IconData icon,
    double confidence,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(icon, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  '${trend > 0 ? '+' : ''}${trend.toStringAsFixed(2)} $unit',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: trend > 0 ? Colors.red : Colors.blue,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          Column(
            children: [
              Icon(
                trend > 0 ? Icons.trending_up : trend < 0 ? Icons.trending_down : Icons.trending_flat,
                color: trend > 0 ? Colors.red : trend < 0 ? Colors.blue : Colors.grey,
              ),
              Text(
                '${(confidence * 100).toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds threshold alerts
  Widget _buildThresholdAlerts() {
    final alerts = _generateThresholdAlerts();

    if (alerts.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.green.shade50,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.green.shade200),
        ),
        child: Row(
          children: [
            Icon(Icons.check_circle_outline, color: Colors.green.shade600, size: 20),
            const SizedBox(width: 8),
            Text(
              'All environmental parameters within normal ranges',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.green.shade800,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Threshold Alerts',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        ...alerts.map((alert) => _buildAlertCard(alert)),
      ],
    );
  }

  /// Builds risk assessment
  Widget _buildRiskAssessment() {
    final overallRisk = _calculateOverallRisk();
    final riskFactors = _getRiskFactors();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _riskColors[overallRisk]!.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _riskColors[overallRisk]!.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.warning_amber_outlined,
                color: _riskColors[overallRisk],
                size: 24,
              ),
              const SizedBox(width: 8),
              Text(
                'Malaria Transmission Risk Assessment',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: _riskColors[overallRisk],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _riskColors[overallRisk]!.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              '${overallRisk.name.toUpperCase()} RISK',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: _riskColors[overallRisk],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Contributing Factors:',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          ...riskFactors.map((factor) => Padding(
            padding: const EdgeInsets.only(bottom: 2),
            child: Text(
              '• $factor',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          )),
        ],
      ),
    );
  }

  /// Calculates current environmental statistics
  List<EnvironmentalIndicator> _calculateCurrentStats() {
    final stats = <EnvironmentalIndicator>[];

    // Temperature indicator
    final currentTemp = widget.environmentalData.temperature.dailyMean.isNotEmpty
        ? widget.environmentalData.temperature.dailyMean.last.temperature
        : 0.0;
    stats.add(EnvironmentalIndicator(
      factor: EnvironmentalFactor.temperature,
      name: 'Temperature',
      value: currentTemp,
      unit: '°C',
      status: _getTemperatureStatus(currentTemp),
      trend: 0.5, // Mock trend
    ));

    // Humidity indicator
    final currentHumidity = widget.environmentalData.humidity.relativeHumidity.isNotEmpty
        ? widget.environmentalData.humidity.relativeHumidity.last.humidity
        : 0.0;
    stats.add(EnvironmentalIndicator(
      factor: EnvironmentalFactor.humidity,
      name: 'Humidity',
      value: currentHumidity,
      unit: '%',
      status: _getHumidityStatusEnum(currentHumidity),
      trend: -0.2, // Mock trend
    ));

    // Rainfall indicator
    final monthlyRainfall = widget.environmentalData.rainfall.monthly.isNotEmpty
        ? widget.environmentalData.rainfall.monthly.last.rainfall
        : 0.0;
    stats.add(EnvironmentalIndicator(
      factor: EnvironmentalFactor.rainfall,
      name: 'Rainfall',
      value: monthlyRainfall,
      unit: 'mm',
      status: _getRainfallStatus(monthlyRainfall),
      trend: 1.2, // Mock trend
    ));

    // Vegetation indicator
    final currentNDVI = widget.environmentalData.vegetation.ndvi.isNotEmpty
        ? widget.environmentalData.vegetation.ndvi.last.value
        : 0.0;
    stats.add(EnvironmentalIndicator(
      factor: EnvironmentalFactor.vegetation,
      name: 'Vegetation',
      value: currentNDVI,
      unit: ' NDVI',
      status: _getVegetationStatus(currentNDVI),
      trend: 0.0, // Mock trend
    ));

    return stats;
  }

  /// Calculates environmental quality score
  double _calculateEnvironmentalQuality() {
    double score = 0;
    int factors = 0;

    // Temperature contribution (0-25 points)
    final currentTemp = widget.environmentalData.temperature.dailyMean.isNotEmpty
        ? widget.environmentalData.temperature.dailyMean.last.temperature
        : 0.0;
    score += _getTemperatureScore(currentTemp);
    factors++;

    // Humidity contribution (0-25 points)
    final currentHumidity = widget.environmentalData.humidity.relativeHumidity.isNotEmpty
        ? widget.environmentalData.humidity.relativeHumidity.last.humidity
        : 0.0;
    score += _getHumidityScore(currentHumidity);
    factors++;

    // Rainfall contribution (0-25 points)
    final monthlyRainfall = widget.environmentalData.rainfall.monthly.isNotEmpty
        ? widget.environmentalData.rainfall.monthly.last.rainfall
        : 0.0;
    score += _getRainfallScore(monthlyRainfall);
    factors++;

    // Vegetation contribution (0-25 points)
    final currentNDVI = widget.environmentalData.vegetation.ndvi.isNotEmpty
        ? widget.environmentalData.vegetation.ndvi.last.value
        : 0.0;
    score += _getVegetationScore(currentNDVI);
    factors++;

    return factors > 0 ? score / factors : 0;
  }

  /// Gets temperature score for quality calculation
  double _getTemperatureScore(double temp) {
    if (temp < 16 || temp > 35) return 5; // Very poor
    if (temp < 18 || temp > 34) return 10; // Poor
    if (temp >= 22 && temp <= 28) return 25; // Excellent
    if (temp >= 20 && temp <= 30) return 20; // Good
    return 15; // Fair
  }

  /// Gets humidity score for quality calculation
  double _getHumidityScore(double humidity) {
    if (humidity < 50) return 5; // Very poor
    if (humidity < 60) return 10; // Poor
    if (humidity >= 70 && humidity <= 90) return 25; // Excellent
    if (humidity >= 60) return 20; // Good
    return 15; // Fair
  }

  /// Gets rainfall score for quality calculation
  double _getRainfallScore(double rainfall) {
    if (rainfall < 50) return 5; // Very poor
    if (rainfall < 80) return 10; // Poor
    if (rainfall >= 150 && rainfall <= 250) return 25; // Excellent
    if (rainfall >= 80) return 20; // Good
    return 15; // Fair
  }

  /// Gets vegetation score for quality calculation
  double _getVegetationScore(double ndvi) {
    if (ndvi < 0.2) return 5; // Very poor
    if (ndvi < 0.3) return 10; // Poor
    if (ndvi >= 0.5 && ndvi <= 0.8) return 25; // Excellent
    if (ndvi >= 0.3) return 20; // Good
    return 15; // Fair
  }

  /// Gets overall risk level based on environmental conditions
  MalariaRiskLevel _calculateOverallRisk() {
    final qualityScore = _calculateEnvironmentalQuality();

    if (qualityScore >= 80) return MalariaRiskLevel.critical;
    if (qualityScore >= 60) return MalariaRiskLevel.high;
    if (qualityScore >= 40) return MalariaRiskLevel.moderate;
    if (qualityScore >= 20) return MalariaRiskLevel.low;
    return MalariaRiskLevel.minimal;
  }

  /// Gets risk factors contributing to current risk level
  List<String> _getRiskFactors() {
    final factors = <String>[];

    final currentTemp = widget.environmentalData.temperature.dailyMean.isNotEmpty
        ? widget.environmentalData.temperature.dailyMean.last.temperature
        : 0.0;
    if (currentTemp >= 20 && currentTemp <= 30) {
      factors.add('Temperature favorable for mosquito breeding (${currentTemp.toStringAsFixed(1)}°C)');
    }

    final currentHumidity = widget.environmentalData.humidity.relativeHumidity.isNotEmpty
        ? widget.environmentalData.humidity.relativeHumidity.last.humidity
        : 0.0;
    if (currentHumidity >= 60) {
      factors.add('High humidity supporting mosquito survival (${currentHumidity.toStringAsFixed(1)}%)');
    }

    final monthlyRainfall = widget.environmentalData.rainfall.monthly.isNotEmpty
        ? widget.environmentalData.rainfall.monthly.last.rainfall
        : 0.0;
    if (monthlyRainfall >= 80) {
      factors.add('Adequate rainfall creating breeding sites (${monthlyRainfall.toStringAsFixed(1)}mm)');
    }

    final currentNDVI = widget.environmentalData.vegetation.ndvi.isNotEmpty
        ? widget.environmentalData.vegetation.ndvi.last.value
        : 0.0;
    if (currentNDVI >= 0.3) {
      factors.add('Dense vegetation providing mosquito habitat (NDVI: ${currentNDVI.toStringAsFixed(2)})');
    }

    if (factors.isEmpty) {
      factors.add('Environmental conditions below transmission thresholds');
    }

    return factors;
  }

  /// Generates threshold alerts for environmental parameters
  List<ThresholdAlert> _generateThresholdAlerts() {
    final alerts = <ThresholdAlert>[];

    // Temperature alerts
    final currentTemp = widget.environmentalData.temperature.dailyMean.isNotEmpty
        ? widget.environmentalData.temperature.dailyMean.last.temperature
        : 0.0;
    if (currentTemp > 34) {
      alerts.add(ThresholdAlert(
        factor: EnvironmentalFactor.temperature,
        message: 'Temperature above transmission threshold (${currentTemp.toStringAsFixed(1)}°C > 34°C)',
        severity: AlertSeverity.high,
      ));
    } else if (currentTemp > 30) {
      alerts.add(ThresholdAlert(
        factor: EnvironmentalFactor.temperature,
        message: 'Temperature approaching critical levels (${currentTemp.toStringAsFixed(1)}°C)',
        severity: AlertSeverity.warning,
      ));
    }

    // Humidity alerts
    final currentHumidity = widget.environmentalData.humidity.relativeHumidity.isNotEmpty
        ? widget.environmentalData.humidity.relativeHumidity.last.humidity
        : 0.0;
    if (currentHumidity >= 80) {
      alerts.add(ThresholdAlert(
        factor: EnvironmentalFactor.humidity,
        message: 'High humidity optimal for mosquito survival (${currentHumidity.toStringAsFixed(1)}%)',
        severity: AlertSeverity.high,
      ));
    }

    // Rainfall alerts
    final monthlyRainfall = widget.environmentalData.rainfall.monthly.isNotEmpty
        ? widget.environmentalData.rainfall.monthly.last.rainfall
        : 0.0;
    if (monthlyRainfall >= 200) {
      alerts.add(ThresholdAlert(
        factor: EnvironmentalFactor.rainfall,
        message: 'Excessive rainfall may create extensive breeding sites (${monthlyRainfall.toStringAsFixed(1)}mm)',
        severity: AlertSeverity.high,
      ));
    }

    return alerts;
  }

  /// Builds alert card
  Widget _buildAlertCard(ThresholdAlert alert) {
    final color = _getAlertColor(alert.severity);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(
            _getAlertIcon(alert.severity),
            color: color,
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              alert.message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: color,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Helper methods for status determination
  IndicatorStatus _getTemperatureStatus(double temp) {
    if (temp >= 22 && temp <= 28) return IndicatorStatus.excellent;
    if (temp >= 20 && temp <= 30) return IndicatorStatus.good;
    if (temp >= 18 && temp <= 34) return IndicatorStatus.fair;
    if (temp >= 16 && temp <= 35) return IndicatorStatus.poor;
    return IndicatorStatus.critical;
  }

  IndicatorStatus _getHumidityStatusEnum(double humidity) {
    if (humidity >= 70 && humidity <= 90) return IndicatorStatus.excellent;
    if (humidity >= 60) return IndicatorStatus.good;
    if (humidity >= 50) return IndicatorStatus.fair;
    if (humidity >= 40) return IndicatorStatus.poor;
    return IndicatorStatus.critical;
  }

  IndicatorStatus _getRainfallStatus(double rainfall) {
    if (rainfall >= 150 && rainfall <= 250) return IndicatorStatus.excellent;
    if (rainfall >= 80) return IndicatorStatus.good;
    if (rainfall >= 50) return IndicatorStatus.fair;
    if (rainfall >= 20) return IndicatorStatus.poor;
    return IndicatorStatus.critical;
  }

  IndicatorStatus _getVegetationStatus(double ndvi) {
    if (ndvi >= 0.5 && ndvi <= 0.8) return IndicatorStatus.excellent;
    if (ndvi >= 0.3) return IndicatorStatus.good;
    if (ndvi >= 0.2) return IndicatorStatus.fair;
    if (ndvi >= 0.1) return IndicatorStatus.poor;
    return IndicatorStatus.critical;
  }

  MalariaRiskLevel _getTemperatureRiskLevel(double temp) {
    if (temp >= 22 && temp <= 28) return MalariaRiskLevel.critical;
    if (temp >= 20 && temp <= 30) return MalariaRiskLevel.high;
    if (temp >= 18 && temp <= 34) return MalariaRiskLevel.moderate;
    return MalariaRiskLevel.low;
  }

  MalariaRiskLevel _getHumidityRiskLevel(double humidity) {
    if (humidity >= 80) return MalariaRiskLevel.critical;
    if (humidity >= 70) return MalariaRiskLevel.high;
    if (humidity >= 60) return MalariaRiskLevel.moderate;
    return MalariaRiskLevel.low;
  }

  MalariaRiskLevel _getRainfallRiskLevel(double rainfall) {
    if (rainfall >= 200) return MalariaRiskLevel.critical;
    if (rainfall >= 150) return MalariaRiskLevel.high;
    if (rainfall >= 80) return MalariaRiskLevel.moderate;
    return MalariaRiskLevel.low;
  }

  MalariaRiskLevel _getVegetationRiskLevel(double ndvi) {
    if (ndvi >= 0.6) return MalariaRiskLevel.critical;
    if (ndvi >= 0.4) return MalariaRiskLevel.high;
    if (ndvi >= 0.3) return MalariaRiskLevel.moderate;
    return MalariaRiskLevel.low;
  }

  MalariaRiskLevel _getQualityLevel(double score) {
    if (score >= 80) return MalariaRiskLevel.critical;
    if (score >= 60) return MalariaRiskLevel.high;
    if (score >= 40) return MalariaRiskLevel.moderate;
    if (score >= 20) return MalariaRiskLevel.low;
    return MalariaRiskLevel.minimal;
  }

  String _getQualityDescription(MalariaRiskLevel level) {
    switch (level) {
      case MalariaRiskLevel.minimal:
        return 'Environmental conditions strongly limit malaria transmission';
      case MalariaRiskLevel.low:
        return 'Environmental conditions moderately favor transmission';
      case MalariaRiskLevel.moderate:
        return 'Environmental conditions support moderate transmission risk';
      case MalariaRiskLevel.high:
        return 'Environmental conditions highly favorable for transmission';
      case MalariaRiskLevel.critical:
        return 'Environmental conditions optimal for malaria transmission';
    }
  }

  String _getHumidityStatus(double humidity) {
    if (humidity >= 80) return 'Optimal for mosquito survival';
    if (humidity >= 60) return 'Suitable for mosquito survival';
    if (humidity >= 50) return 'Marginal for mosquito survival';
    return 'Poor for mosquito survival';
  }

  String _getVegetationHealth(double ndvi) {
    if (ndvi >= 0.6) return 'Very dense vegetation';
    if (ndvi >= 0.4) return 'Dense vegetation';
    if (ndvi >= 0.3) return 'Moderate vegetation';
    if (ndvi >= 0.2) return 'Sparse vegetation';
    return 'Very sparse vegetation';
  }

  String _getBreedingHabitat(double ndvi) {
    if (ndvi >= 0.5) return 'Extensive breeding habitat';
    if (ndvi >= 0.3) return 'Moderate breeding habitat';
    if (ndvi >= 0.2) return 'Limited breeding habitat';
    return 'Minimal breeding habitat';
  }

  String _getDominantLandCover() {
    final distribution = widget.environmentalData.vegetation.landCoverDistribution;
    final dominant = distribution.entries.reduce((a, b) => a.value > b.value ? a : b);
    return dominant.key.name;
  }

  Color _getIndicatorBorderColor(IndicatorStatus status) {
    switch (status) {
      case IndicatorStatus.excellent:
        return Colors.green;
      case IndicatorStatus.good:
        return Colors.lightGreen;
      case IndicatorStatus.fair:
        return Colors.orange;
      case IndicatorStatus.poor:
        return Colors.red;
      case IndicatorStatus.critical:
        return Colors.purple;
    }
  }

  Color _getAlertColor(AlertSeverity severity) {
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

  IconData _getAlertIcon(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.info:
        return Icons.info_outline;
      case AlertSeverity.warning:
        return Icons.warning_amber_outlined;
      case AlertSeverity.high:
        return Icons.error_outline;
      case AlertSeverity.critical:
        return Icons.dangerous_outlined;
      case AlertSeverity.emergency:
        return Icons.emergency_outlined;
    }
  }

  String _getViewModeDisplayName(SummaryViewMode mode) {
    switch (mode) {
      case SummaryViewMode.overview:
        return 'Overview';
      case SummaryViewMode.detailed:
        return 'Detailed';
      case SummaryViewMode.trends:
        return 'Trends';
      case SummaryViewMode.comparisons:
        return 'Comparisons';
    }
  }

  /// Builds no trend data message
  Widget _buildNoTrendDataMessage() {
    return Center(
      child: Column(
        children: [
          Icon(
            Icons.trending_flat,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No trend data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds no comparison data message
  Widget _buildNoComparisonDataMessage() {
    return Center(
      child: Column(
        children: [
          Icon(
            Icons.compare_arrows,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No comparison data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds climate change indicators
  Widget _buildClimateChangeIndicators() {
    if (widget.weatherTrend?.climateChangeIndicators == null) {
      return const SizedBox.shrink();
    }

    final indicators = widget.weatherTrend!.climateChangeIndicators;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.red.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.trending_up, color: Colors.red.shade600, size: 20),
              const SizedBox(width: 8),
              Text(
                'Climate Change Indicators',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.red.shade800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Temperature increase: ${indicators.temperatureIncreaseRate.toStringAsFixed(2)}°C/decade',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Text(
            'Precipitation change: ${indicators.precipitationChangeRate.toStringAsFixed(1)}mm/decade',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Text(
            'Extreme events increase: ${indicators.extremeWeatherIncreaseRate.toStringAsFixed(1)}/decade',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Text(
            'Analysis confidence: ${(indicators.confidence * 100).toStringAsFixed(0)}%',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  /// Builds seasonal comparison
  Widget _buildSeasonalComparison() {
    // Mock implementation - would use actual seasonal data
    return const Text('Seasonal comparison would be implemented here');
  }

  /// Builds historical comparison
  Widget _buildHistoricalComparison() {
    // Mock implementation - would use historical data
    return const Text('Historical comparison would be implemented here');
  }

  /// Refreshes environmental data
  void _refreshData() {
    // Mock implementation - would refresh from data sources
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Environmental data refreshed')),
    );
  }

  /// Shows environmental information dialog
  void _showEnvironmentalInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Environmental Summary Information'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Quality Score Calculation:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Temperature: Optimal 22-28°C (25 points)'),
              Text('• Humidity: Optimal 70-90% (25 points)'),
              Text('• Rainfall: Optimal 150-250mm (25 points)'),
              Text('• Vegetation: Optimal NDVI 0.5-0.8 (25 points)'),
              SizedBox(height: 16),
              Text(
                'Risk Levels:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Minimal: <20% (Very low transmission)'),
              Text('• Low: 20-39% (Low transmission)'),
              Text('• Moderate: 40-59% (Moderate transmission)'),
              Text('• High: 60-79% (High transmission)'),
              Text('• Critical: 80-100% (Peak transmission)'),
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

/// Environmental indicator data structure
class EnvironmentalIndicator {
  final EnvironmentalFactor factor;
  final String name;
  final double value;
  final String unit;
  final IndicatorStatus status;
  final double trend;

  const EnvironmentalIndicator({
    required this.factor,
    required this.name,
    required this.value,
    required this.unit,
    required this.status,
    required this.trend,
  });
}

/// Threshold alert data structure
class ThresholdAlert {
  final EnvironmentalFactor factor;
  final String message;
  final AlertSeverity severity;

  const ThresholdAlert({
    required this.factor,
    required this.message,
    required this.severity,
  });
}

/// Summary view mode enumeration
enum SummaryViewMode {
  overview,
  detailed,
  trends,
  comparisons,
}

/// Indicator status enumeration
enum IndicatorStatus {
  excellent,
  good,
  fair,
  poor,
  critical,
}

/// Malaria risk level enumeration
enum MalariaRiskLevel {
  minimal,
  low,
  moderate,
  high,
  critical,
}