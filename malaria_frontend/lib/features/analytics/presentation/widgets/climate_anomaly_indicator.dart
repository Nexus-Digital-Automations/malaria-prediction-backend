/// Climate anomaly indicator widget for detecting unusual weather patterns
///
/// This widget provides comprehensive climate anomaly detection and visualization
/// for environmental factors affecting malaria transmission, including temperature
/// extremes, rainfall deviations, and other climate irregularities.
///
/// Features:
/// - Multi-factor anomaly detection
/// - Statistical significance testing
/// - Historical baseline comparisons
/// - Alert severity classification
/// - Climate change indicators
/// - Real-time monitoring
///
/// Usage:
/// ```dart
/// ClimateAnomalyIndicator(
///   environmentalData: environmentalData,
///   dateRange: dateRange,
///   selectedFactors: factors,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Comprehensive climate anomaly detection and indicator widget
class ClimateAnomalyIndicator extends StatefulWidget {
  /// Environmental data for anomaly analysis
  final EnvironmentalData environmentalData;

  /// Date range for anomaly detection
  final DateRange? dateRange;

  /// Environmental factors to monitor for anomalies
  final Set<EnvironmentalFactor> selectedFactors;

  /// Anomaly detection sensitivity (standard deviations)
  final double anomalyThreshold;

  /// Whether to show historical baselines
  final bool showBaselines;

  /// Whether to show climate change trends
  final bool showClimateChange;

  /// Widget height
  final double? height;

  /// Constructor requiring environmental data
  const ClimateAnomalyIndicator({
    super.key,
    required this.environmentalData,
    this.dateRange,
    required this.selectedFactors,
    this.anomalyThreshold = 2.0,
    this.showBaselines = true,
    this.showClimateChange = false,
    this.height,
  });

  @override
  State<ClimateAnomalyIndicator> createState() => _ClimateAnomalyIndicatorState();
}

class _ClimateAnomalyIndicatorState extends State<ClimateAnomalyIndicator> {
  /// Current anomaly view mode
  AnomalyViewMode _viewMode = AnomalyViewMode.alerts;

  /// Detected anomalies
  late List<ClimateAnomaly> _detectedAnomalies;

  /// Color mapping for anomaly severity
  final Map<AnomalySeverity, Color> _severityColors = {
    AnomalySeverity.minor: Colors.yellow.shade600,
    AnomalySeverity.moderate: Colors.orange.shade600,
    AnomalySeverity.major: Colors.red.shade600,
    AnomalySeverity.extreme: Colors.purple.shade600,
  };

  /// Color mapping for environmental factors
  final Map<EnvironmentalFactor, Color> _factorColors = {
    EnvironmentalFactor.temperature: Colors.red.shade600,
    EnvironmentalFactor.rainfall: Colors.blue.shade600,
    EnvironmentalFactor.vegetation: Colors.green.shade600,
    EnvironmentalFactor.humidity: Colors.cyan.shade600,
    EnvironmentalFactor.windSpeed: Colors.orange.shade600,
    EnvironmentalFactor.pressure: Colors.purple.shade600,
  };

  /// Show only active anomalies
  bool _showActiveOnly = true;

  /// Time window for anomaly detection (days)
  int _detectionWindow = 30;

  /// Current alert level
  AlertLevel _currentAlertLevel = AlertLevel.normal;

  @override
  void initState() {
    super.initState();
    _detectAnomalies();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: widget.height,
      child: Card(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            _buildAlertStatus(),
            if (_viewMode != AnomalyViewMode.alerts) _buildControlPanel(),
            Expanded(child: _buildContent()),
            if (_detectedAnomalies.isNotEmpty) _buildActionPanel(),
          ],
        ),
      ),
    );
  }

  /// Builds the widget header with title and controls
  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _getAlertLevelColor(_currentAlertLevel).withValues(alpha: 0.1),
            _getAlertLevelColor(_currentAlertLevel).withValues(alpha: 0.05),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      _getAlertLevelIcon(_currentAlertLevel),
                      color: _getAlertLevelColor(_currentAlertLevel),
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Climate Anomaly Detection',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: _getAlertLevelColor(_currentAlertLevel),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  '${_detectedAnomalies.length} anomalie(s) detected in ${widget.environmentalData.region}',
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
                  _showActiveOnly ? Icons.notifications_active : Icons.notifications_outlined,
                  color: Theme.of(context).colorScheme.primary,
                ),
                onPressed: () {
                  setState(() {
                    _showActiveOnly = !_showActiveOnly;
                  });
                },
                tooltip: 'Toggle Active Anomalies Only',
              ),
              PopupMenuButton<AnomalyViewMode>(
                icon: Icon(
                  Icons.view_module_outlined,
                  color: Theme.of(context).colorScheme.primary,
                ),
                onSelected: (mode) {
                  setState(() {
                    _viewMode = mode;
                  });
                },
                itemBuilder: (context) => AnomalyViewMode.values.map((mode) {
                  return PopupMenuItem(
                    value: mode,
                    child: Text(_getViewModeDisplayName(mode)),
                  );
                }).toList(),
                tooltip: 'Change View Mode',
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds alert status indicator
  Widget _buildAlertStatus() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _getAlertLevelColor(_currentAlertLevel).withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: _getAlertLevelColor(_currentAlertLevel).withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        children: [
          Icon(
            _getAlertLevelIcon(_currentAlertLevel),
            color: _getAlertLevelColor(_currentAlertLevel),
            size: 18,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _getAlertLevelTitle(_currentAlertLevel),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _getAlertLevelColor(_currentAlertLevel),
                  ),
                ),
                Text(
                  _getAlertLevelDescription(_currentAlertLevel),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: _getAlertLevelColor(_currentAlertLevel).withValues(alpha: 0.8),
                  ),
                ),
              ],
            ),
          ),
          if (_detectedAnomalies.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: _getAlertLevelColor(_currentAlertLevel),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '${_detectedAnomalies.length}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// Builds control panel for anomaly settings
  Widget _buildControlPanel() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        children: [
          Row(
            children: [
              Text(
                'Detection Window:',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Slider(
                  value: _detectionWindow.toDouble(),
                  min: 7,
                  max: 90,
                  divisions: 11,
                  label: '$_detectionWindow days',
                  onChanged: (value) {
                    setState(() {
                      _detectionWindow = value.toInt();
                      _detectAnomalies();
                    });
                  },
                ),
              ),
              Text(
                '$_detectionWindow days',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
          Row(
            children: [
              Text(
                'Sensitivity:',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Slider(
                  value: widget.anomalyThreshold,
                  min: 1.0,
                  max: 3.0,
                  divisions: 8,
                  label: '${widget.anomalyThreshold.toStringAsFixed(1)}σ',
                  onChanged: (value) {
                    // Note: This would need to be passed back to parent widget
                    // For now, just show the visual feedback
                  },
                ),
              ),
              Text(
                '${widget.anomalyThreshold.toStringAsFixed(1)}σ',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds main content based on view mode
  Widget _buildContent() {
    switch (_viewMode) {
      case AnomalyViewMode.alerts:
        return _buildAnomalyAlerts();
      case AnomalyViewMode.timeline:
        return _buildAnomalyTimeline();
      case AnomalyViewMode.heatmap:
        return _buildAnomalyHeatmap();
      case AnomalyViewMode.statistics:
        return _buildAnomalyStatistics();
    }
  }

  /// Builds anomaly alerts list
  Widget _buildAnomalyAlerts() {
    final displayAnomalies = _showActiveOnly
        ? _detectedAnomalies.where((a) => a.isActive).toList()
        : _detectedAnomalies;

    if (displayAnomalies.isEmpty) {
      return _buildNoAnomaliesMessage();
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: ListView.builder(
        itemCount: displayAnomalies.length,
        itemBuilder: (context, index) {
          final anomaly = displayAnomalies[index];
          return _buildAnomalyCard(anomaly);
        },
      ),
    );
  }

  /// Builds individual anomaly card
  Widget _buildAnomalyCard(ClimateAnomaly anomaly) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 4,
                  height: 40,
                  decoration: BoxDecoration(
                    color: _severityColors[anomaly.severity],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            _getFactorIcon(anomaly.factor),
                            color: _factorColors[anomaly.factor],
                            size: 16,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            _getFactorDisplayName(anomaly.factor),
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Spacer(),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: _severityColors[anomaly.severity]?.withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _getSeverityDisplayName(anomaly.severity),
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: _severityColors[anomaly.severity],
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        anomaly.description,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(
                  Icons.schedule_outlined,
                  size: 14,
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                const SizedBox(width: 4),
                Text(
                  'Detected: ${DateFormat('MMM d, yyyy HH:mm').format(anomaly.detectedAt)}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
                const SizedBox(width: 16),
                Icon(
                  Icons.trending_up_outlined,
                  size: 14,
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                const SizedBox(width: 4),
                Text(
                  'Deviation: ${anomaly.deviationScore.toStringAsFixed(1)}σ',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Builds anomaly timeline chart
  Widget _buildAnomalyTimeline() {
    final timelineData = _prepareTimelineData();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: LineChart(
        LineChartData(
          gridData: FlGridData(
            show: true,
            drawVerticalLine: true,
            drawHorizontalLine: true,
            getDrawingHorizontalLine: (value) => FlLine(
              color: Theme.of(context).dividerColor,
              strokeWidth: 0.5,
            ),
            getDrawingVerticalLine: (value) => FlLine(
              color: Theme.of(context).dividerColor,
              strokeWidth: 0.5,
            ),
          ),
          titlesData: FlTitlesData(
            show: true,
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) => Text(
                  '${value.toStringAsFixed(1)}σ',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                reservedSize: 40,
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  final date = DateTime.now().subtract(Duration(days: (30 - value).toInt()));
                  return Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      DateFormat('M/d').format(date),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  );
                },
                reservedSize: 30,
              ),
            ),
          ),
          borderData: FlBorderData(
            show: true,
            border: Border.all(
              color: Theme.of(context).dividerColor,
              width: 1,
            ),
          ),
          lineBarsData: timelineData,
          extraLinesData: ExtraLinesData(
            horizontalLines: [
              HorizontalLine(
                y: widget.anomalyThreshold,
                color: Colors.red.withValues(alpha: 0.5),
                strokeWidth: 2,
                dashArray: [5, 5],
                label: HorizontalLineLabel(
                  show: true,
                  labelResolver: (line) => 'Anomaly Threshold',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Colors.red,
                  ),
                ),
              ),
              HorizontalLine(
                y: -widget.anomalyThreshold,
                color: Colors.red.withValues(alpha: 0.5),
                strokeWidth: 2,
                dashArray: [5, 5],
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Builds anomaly heatmap
  Widget _buildAnomalyHeatmap() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Center(
        child: Text(
          'Anomaly heatmap visualization\nwill be implemented here',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// Builds anomaly statistics
  Widget _buildAnomalyStatistics() {
    final stats = _calculateAnomalyStatistics();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: GridView.count(
        crossAxisCount: 2,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
        childAspectRatio: 1.5,
        children: [
          _buildStatCard(
            'Total Anomalies',
            '${stats['total']}',
            Icons.warning_amber_outlined,
            Colors.orange,
          ),
          _buildStatCard(
            'Active Alerts',
            '${stats['active']}',
            Icons.notifications_active,
            Colors.red,
          ),
          _buildStatCard(
            'Most Affected',
            stats['mostAffected'],
            Icons.thermostat_outlined,
            Colors.blue,
          ),
          _buildStatCard(
            'Avg Severity',
            '${stats['avgSeverity']}σ',
            Icons.trending_up,
            Colors.purple,
          ),
        ],
      ),
    );
  }

  /// Builds individual statistic card
  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              title,
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  /// Builds action panel for anomaly management
  Widget _buildActionPanel() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.3),
        border: Border(
          top: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              'Anomaly Management',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          OutlinedButton.icon(
            onPressed: () => _acknowledgeAnomalies(),
            icon: const Icon(Icons.check, size: 16),
            label: const Text('Acknowledge'),
          ),
          const SizedBox(width: 8),
          ElevatedButton.icon(
            onPressed: () => _generateReport(),
            icon: const Icon(Icons.file_download, size: 16),
            label: const Text('Report'),
          ),
        ],
      ),
    );
  }

  /// Builds no anomalies message
  Widget _buildNoAnomaliesMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 48,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'No climate anomalies detected',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Environmental conditions are within normal ranges',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Detects climate anomalies in environmental data
  void _detectAnomalies() {
    final anomalies = <ClimateAnomaly>[];
    final endDate = DateTime.now();
    final startDate = endDate.subtract(Duration(days: _detectionWindow));

    // Mock anomaly detection - would use real statistical analysis
    for (final factor in widget.selectedFactors) {
      final factorAnomalies = _detectFactorAnomalies(factor, startDate, endDate);
      anomalies.addAll(factorAnomalies);
    }

    setState(() {
      _detectedAnomalies = anomalies;
      _currentAlertLevel = _calculateAlertLevel(anomalies);
    });
  }

  /// Detects anomalies for a specific environmental factor
  List<ClimateAnomaly> _detectFactorAnomalies(
    EnvironmentalFactor factor,
    DateTime startDate,
    DateTime endDate,
  ) {
    final anomalies = <ClimateAnomaly>[];

    // Mock anomaly detection logic
    // In real implementation, this would:
    // 1. Calculate historical baselines
    // 2. Compute z-scores for recent data
    // 3. Identify values exceeding threshold
    // 4. Apply statistical significance tests

    // Example: Temperature anomaly
    if (factor == EnvironmentalFactor.temperature) {
      anomalies.add(ClimateAnomaly(
        id: 'temp_001',
        factor: factor,
        severity: AnomalySeverity.moderate,
        deviationScore: 2.3,
        detectedAt: DateTime.now().subtract(const Duration(hours: 6)),
        description: 'Temperature 2.3°C above seasonal average',
        isActive: true,
        coordinates: widget.environmentalData.coordinates,
        confidence: 0.89,
      ));
    }

    // Example: Rainfall anomaly
    if (factor == EnvironmentalFactor.rainfall) {
      anomalies.add(ClimateAnomaly(
        id: 'rain_001',
        factor: factor,
        severity: AnomalySeverity.major,
        deviationScore: 3.1,
        detectedAt: DateTime.now().subtract(const Duration(days: 2)),
        description: 'Extreme rainfall event: 150mm in 24 hours',
        isActive: true,
        coordinates: widget.environmentalData.coordinates,
        confidence: 0.95,
      ));
    }

    return anomalies;
  }

  /// Calculates overall alert level based on detected anomalies
  AlertLevel _calculateAlertLevel(List<ClimateAnomaly> anomalies) {
    if (anomalies.isEmpty) return AlertLevel.normal;

    final activeSevereAnomalies = anomalies
        .where((a) => a.isActive && (a.severity == AnomalySeverity.major || a.severity == AnomalySeverity.extreme))
        .length;

    if (activeSevereAnomalies >= 2) return AlertLevel.critical;
    if (activeSevereAnomalies >= 1) return AlertLevel.high;
    if (anomalies.where((a) => a.isActive).length >= 2) return AlertLevel.medium;
    return AlertLevel.low;
  }

  /// Prepares timeline data for chart
  List<LineChartBarData> _prepareTimelineData() {
    final lineBars = <LineChartBarData>[];

    for (final factor in widget.selectedFactors) {
      final spots = <FlSpot>[];

      // Mock timeline data - would use real deviation scores
      for (int i = 0; i < 30; i++) {
        final deviation = (i - 15) * 0.2 + (i % 5 - 2) * 0.5;
        spots.add(FlSpot(i.toDouble(), deviation));
      }

      lineBars.add(
        LineChartBarData(
          spots: spots,
          isCurved: true,
          color: _factorColors[factor],
          barWidth: 2,
          dotData: FlDotData(
            show: true,
            getDotPainter: (spot, percent, barData, index) {
              final isAnomaly = spot.y.abs() >= widget.anomalyThreshold;
              return FlDotCirclePainter(
                radius: isAnomaly ? 4 : 2,
                color: isAnomaly ? Colors.red : _factorColors[factor]!,
                strokeWidth: 1,
                strokeColor: Theme.of(context).colorScheme.surface,
              );
            },
          ),
        ),
      );
    }

    return lineBars;
  }

  /// Calculates anomaly statistics
  Map<String, dynamic> _calculateAnomalyStatistics() {
    final activeAnomalies = _detectedAnomalies.where((a) => a.isActive).length;
    final avgSeverity = _detectedAnomalies.isEmpty
        ? 0.0
        : _detectedAnomalies.map((a) => a.deviationScore).reduce((a, b) => a + b) / _detectedAnomalies.length;

    final factorCounts = <EnvironmentalFactor, int>{};
    for (final anomaly in _detectedAnomalies) {
      factorCounts[anomaly.factor] = (factorCounts[anomaly.factor] ?? 0) + 1;
    }

    final mostAffected = factorCounts.isNotEmpty
        ? _getFactorDisplayName(factorCounts.entries.reduce((a, b) => a.value > b.value ? a : b).key)
        : 'None';

    return {
      'total': _detectedAnomalies.length,
      'active': activeAnomalies,
      'mostAffected': mostAffected,
      'avgSeverity': avgSeverity.toStringAsFixed(1),
    };
  }

  /// Acknowledges all current anomalies
  void _acknowledgeAnomalies() {
    setState(() {
      for (final anomaly in _detectedAnomalies) {
        anomaly.isActive = false;
      }
      _currentAlertLevel = AlertLevel.normal;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('All anomalies acknowledged')),
    );
  }

  /// Generates anomaly report
  void _generateReport() {
    // TODO: Implement report generation
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Generating anomaly report...')),
    );
  }

  /// Gets alert level color
  Color _getAlertLevelColor(AlertLevel level) {
    switch (level) {
      case AlertLevel.normal:
        return Colors.green;
      case AlertLevel.low:
        return Colors.yellow.shade700;
      case AlertLevel.medium:
        return Colors.orange;
      case AlertLevel.high:
        return Colors.red;
      case AlertLevel.critical:
        return Colors.purple;
    }
  }

  /// Gets alert level icon
  IconData _getAlertLevelIcon(AlertLevel level) {
    switch (level) {
      case AlertLevel.normal:
        return Icons.check_circle_outline;
      case AlertLevel.low:
        return Icons.info_outline;
      case AlertLevel.medium:
        return Icons.warning_amber_outlined;
      case AlertLevel.high:
        return Icons.error_outline;
      case AlertLevel.critical:
        return Icons.dangerous_outlined;
    }
  }

  /// Gets alert level title
  String _getAlertLevelTitle(AlertLevel level) {
    switch (level) {
      case AlertLevel.normal:
        return 'Normal Conditions';
      case AlertLevel.low:
        return 'Minor Deviations';
      case AlertLevel.medium:
        return 'Moderate Anomalies';
      case AlertLevel.high:
        return 'Significant Anomalies';
      case AlertLevel.critical:
        return 'Critical Anomalies';
    }
  }

  /// Gets alert level description
  String _getAlertLevelDescription(AlertLevel level) {
    switch (level) {
      case AlertLevel.normal:
        return 'All environmental parameters within normal ranges';
      case AlertLevel.low:
        return 'Minor deviations detected, monitoring recommended';
      case AlertLevel.medium:
        return 'Moderate anomalies detected, increased monitoring advised';
      case AlertLevel.high:
        return 'Significant anomalies detected, action may be required';
      case AlertLevel.critical:
        return 'Critical anomalies detected, immediate attention required';
    }
  }

  /// Gets factor icon
  IconData _getFactorIcon(EnvironmentalFactor factor) {
    switch (factor) {
      case EnvironmentalFactor.temperature:
        return Icons.thermostat_outlined;
      case EnvironmentalFactor.rainfall:
        return Icons.water_drop_outlined;
      case EnvironmentalFactor.vegetation:
        return Icons.eco_outlined;
      case EnvironmentalFactor.humidity:
        return Icons.opacity_outlined;
      case EnvironmentalFactor.windSpeed:
        return Icons.air_outlined;
      case EnvironmentalFactor.pressure:
        return Icons.compress_outlined;
    }
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(AnomalyViewMode mode) {
    switch (mode) {
      case AnomalyViewMode.alerts:
        return 'Alerts';
      case AnomalyViewMode.timeline:
        return 'Timeline';
      case AnomalyViewMode.heatmap:
        return 'Heatmap';
      case AnomalyViewMode.statistics:
        return 'Statistics';
    }
  }

  /// Gets severity display name
  String _getSeverityDisplayName(AnomalySeverity severity) {
    switch (severity) {
      case AnomalySeverity.minor:
        return 'Minor';
      case AnomalySeverity.moderate:
        return 'Moderate';
      case AnomalySeverity.major:
        return 'Major';
      case AnomalySeverity.extreme:
        return 'Extreme';
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
}

/// Climate anomaly data class
class ClimateAnomaly {
  final String id;
  final EnvironmentalFactor factor;
  final AnomalySeverity severity;
  final double deviationScore;
  final DateTime detectedAt;
  final String description;
  bool isActive;
  final Coordinates coordinates;
  final double confidence;

  ClimateAnomaly({
    required this.id,
    required this.factor,
    required this.severity,
    required this.deviationScore,
    required this.detectedAt,
    required this.description,
    required this.isActive,
    required this.coordinates,
    required this.confidence,
  });
}

/// Anomaly view mode enumeration
enum AnomalyViewMode {
  alerts,
  timeline,
  heatmap,
  statistics,
}

/// Anomaly severity enumeration
enum AnomalySeverity {
  minor,
  moderate,
  major,
  extreme,
}

/// Alert level enumeration
enum AlertLevel {
  normal,
  low,
  medium,
  high,
  critical,
}