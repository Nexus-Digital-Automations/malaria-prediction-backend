/// Alert correlation display widget for outbreak pattern analysis
///
/// This widget displays correlation analysis between alert statistics and
/// risk trends to identify alert system effectiveness, response patterns,
/// and optimization opportunities for public health decision-making.
///
/// Usage:
/// ```dart
/// AlertCorrelationDisplay(
///   riskTrends: riskTrends,
///   alertStatistics: alertStatistics,
///   height: 400,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Alert correlation display widget with comprehensive analysis
class AlertCorrelationDisplay extends StatefulWidget {
  /// Risk trend data for correlation analysis
  final List<RiskTrend> riskTrends;

  /// Alert statistics for correlation analysis
  final AlertStatistics alertStatistics;

  /// Widget height
  final double height;

  /// Whether to show detailed analysis
  final bool showDetailedAnalysis;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Constructor requiring risk trends and alert statistics
  const AlertCorrelationDisplay({
    super.key,
    required this.riskTrends,
    required this.alertStatistics,
    this.height = 350,
    this.showDetailedAnalysis = false,
    this.dateRange,
  });

  @override
  State<AlertCorrelationDisplay> createState() => _AlertCorrelationDisplayState();
}

class _AlertCorrelationDisplayState extends State<AlertCorrelationDisplay>
    with TickerProviderStateMixin {
  /// Current analysis view mode
  CorrelationViewMode _viewMode = CorrelationViewMode.overview;

  /// Animation controller for transitions
  late AnimationController _animationController;

  /// Alert correlation data
  List<AlertCorrelationPoint> _correlationData = [];

  /// Alert effectiveness metrics
  late AlertEffectivenessMetrics _effectivenessMetrics;

  /// Alert response analysis
  List<AlertResponseAnalysis> _responseAnalysis = [];

  /// Selected correlation period
  DateRange? _selectedPeriod;

  /// Alert severity color mapping
  final Map<AlertSeverity, Color> _severityColors = {
    AlertSeverity.info: Colors.blue,
    AlertSeverity.warning: Colors.orange,
    AlertSeverity.high: Colors.red,
    AlertSeverity.critical: Colors.purple,
    AlertSeverity.emergency: Colors.black,
  };

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _processCorrelationData();
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(AlertCorrelationDisplay oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.riskTrends != widget.riskTrends ||
        oldWidget.alertStatistics != widget.alertStatistics) {
      _processCorrelationData();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Container(
        height: widget.height,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 12),
            _buildViewModeSelector(),
            const SizedBox(height: 12),
            Expanded(child: _buildMainContent()),
            if (_selectedPeriod != null) _buildSelectedPeriodInfo(),
          ],
        ),
      ),
    );
  }

  /// Builds the widget header with title and key metrics
  Widget _buildHeader() {
    final alertEffectiveness = (_effectivenessMetrics.overallEffectiveness * 100);
    final responseTime = _effectivenessMetrics.averageResponseTime.inHours;

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Alert Correlation Analysis',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Alert effectiveness: ${alertEffectiveness.toStringAsFixed(1)}% • Avg response: ${responseTime}h',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        _buildEffectivenessIndicator(alertEffectiveness),
      ],
    );
  }

  /// Builds alert effectiveness indicator
  Widget _buildEffectivenessIndicator(double effectiveness) {
    final color = _getEffectivenessColor(effectiveness);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Icon(
            _getEffectivenessIcon(effectiveness),
            color: color,
            size: 24,
          ),
          const SizedBox(height: 4),
          Text(
            '${effectiveness.toStringAsFixed(0)}%',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            'Effective',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds view mode selector
  Widget _buildViewModeSelector() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: CorrelationViewMode.values.map((mode) {
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

  /// Builds main content based on view mode
  Widget _buildMainContent() {
    switch (_viewMode) {
      case CorrelationViewMode.overview:
        return _buildOverviewView();
      case CorrelationViewMode.correlation:
        return _buildCorrelationChart();
      case CorrelationViewMode.effectiveness:
        return _buildEffectivenessAnalysis();
      case CorrelationViewMode.response:
        return _buildResponseAnalysis();
    }
  }

  /// Builds overview view with key metrics and summaries
  Widget _buildOverviewView() {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: _buildCorrelationScatterPlot(),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            children: [
              Expanded(child: _buildAlertSummary()),
              const SizedBox(height: 16),
              Expanded(child: _buildCorrelationSummary()),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds correlation scatter plot
  Widget _buildCorrelationScatterPlot() {
    return Column(
      children: [
        Text(
          'Risk vs Alert Correlation',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: ScatterChart(
            ScatterChartData(
              scatterSpots: _buildScatterSpots(),
              minX: 0,
              maxX: 1,
              minY: 0,
              maxY: _getMaxAlertCount().toDouble(),
              backgroundColor: Colors.transparent,
              gridData: FlGridData(
                show: true,
                drawVerticalLine: true,
                drawHorizontalLine: true,
                checkToShowVerticalLine: (value) => value % 0.2 == 0,
                checkToShowHorizontalLine: (value) => value % 10 == 0,
              ),
              titlesData: FlTitlesData(
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '${(value * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodySmall,
                      );
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        value.toInt().toString(),
                        style: Theme.of(context).textTheme.bodySmall,
                      );
                    },
                  ),
                ),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              borderData: FlBorderData(
                show: true,
                border: Border.all(color: Theme.of(context).dividerColor),
              ),
              scatterTouchData: ScatterTouchData(
                enabled: true,
                touchTooltipData: ScatterTouchTooltipData(
                  getTooltipItems: (ScatterSpot touchedSpot) {
                    final correlation = _correlationData.firstWhere(
                      (c) => c.riskScore == touchedSpot.x && c.alertCount == touchedSpot.y.toInt(),
                      orElse: () => _correlationData.first,
                    );

                    return ScatterTooltipItem(
                      'Risk: ${(correlation.riskScore * 100).toStringAsFixed(1)}%\n'
                      'Alerts: ${correlation.alertCount}\n'
                      'Effectiveness: ${(correlation.effectiveness * 100).toStringAsFixed(1)}%',
                      TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Risk Score →',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Transform.rotate(
              angle: math.pi / 2,
              child: Text(
                '← Alert Count',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds scatter plot spots
  List<ScatterSpot> _buildScatterSpots() {
    return _correlationData.map((correlation) {
      final color = _getEffectivenessColor(correlation.effectiveness * 100);
      return ScatterSpot(
        correlation.riskScore,
        correlation.alertCount.toDouble(),
        color: color,
        radius: 6,
      );
    }).toList();
  }

  /// Builds alert summary panel
  Widget _buildAlertSummary() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Alert Summary',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: [
              _buildSummaryItem(
                'Total Alerts',
                widget.alertStatistics.totalAlerts.toString(),
                Icons.notifications,
                Colors.blue,
              ),
              const SizedBox(height: 8),
              _buildSummaryItem(
                'Delivery Rate',
                '${(widget.alertStatistics.deliveryRate * 100).toStringAsFixed(1)}%',
                Icons.check_circle,
                Colors.green,
              ),
              const SizedBox(height: 8),
              _buildSummaryItem(
                'False Positives',
                widget.alertStatistics.falsePositives.toString(),
                Icons.error,
                Colors.orange,
              ),
              const SizedBox(height: 8),
              _buildSummaryItem(
                'Missed Alerts',
                widget.alertStatistics.missedAlerts.toString(),
                Icons.cancel,
                Colors.red,
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds correlation summary panel
  Widget _buildCorrelationSummary() {
    final correlationStrength = _calculateCorrelationStrength();
    final alertAccuracy = _calculateAlertAccuracy();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Correlation Metrics',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: [
              _buildSummaryItem(
                'Correlation',
                '${(correlationStrength * 100).toStringAsFixed(1)}%',
                Icons.analytics,
                _getCorrelationColor(correlationStrength),
              ),
              const SizedBox(height: 8),
              _buildSummaryItem(
                'Alert Accuracy',
                '${(alertAccuracy * 100).toStringAsFixed(1)}%',
                Icons.target,
                _getAccuracyColor(alertAccuracy),
              ),
              const SizedBox(height: 8),
              _buildSummaryItem(
                'Response Time',
                '${widget.alertStatistics.averageResponseTime.inHours}h',
                Icons.timer,
                Colors.purple,
              ),
              const SizedBox(height: 8),
              _buildSummaryItem(
                'Coverage',
                '${(_effectivenessMetrics.coverage * 100).toStringAsFixed(1)}%',
                Icons.coverage,
                Colors.teal,
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds individual summary item
  Widget _buildSummaryItem(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: color,
              ),
            ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds correlation chart view
  Widget _buildCorrelationChart() {
    return Column(
      children: [
        Expanded(
          flex: 2,
          child: _buildDetailedCorrelationChart(),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: _buildCorrelationMatrix(),
        ),
      ],
    );
  }

  /// Builds detailed correlation line chart
  Widget _buildDetailedCorrelationChart() {
    return Column(
      children: [
        Text(
          'Risk-Alert Correlation Over Time',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: LineChart(
            LineChartData(
              gridData: FlGridData(
                show: true,
                drawVerticalLine: true,
                drawHorizontalLine: true,
              ),
              titlesData: FlTitlesData(
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      if (value.toInt() < _correlationData.length) {
                        return Text(
                          '${value.toInt()}',
                          style: Theme.of(context).textTheme.bodySmall,
                        );
                      }
                      return const Text('');
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '${(value * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodySmall,
                      );
                    },
                  ),
                ),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              borderData: FlBorderData(
                show: true,
                border: Border.all(color: Theme.of(context).dividerColor),
              ),
              lineBarsData: [
                // Risk score line
                LineChartBarData(
                  spots: _correlationData.asMap().entries.map((entry) {
                    return FlSpot(entry.key.toDouble(), entry.value.riskScore);
                  }).toList(),
                  isCurved: true,
                  color: Colors.red,
                  barWidth: 3,
                  dotData: const FlDotData(show: false),
                ),
                // Alert effectiveness line
                LineChartBarData(
                  spots: _correlationData.asMap().entries.map((entry) {
                    return FlSpot(entry.key.toDouble(), entry.value.effectiveness);
                  }).toList(),
                  isCurved: true,
                  color: Colors.blue,
                  barWidth: 3,
                  dotData: const FlDotData(show: false),
                ),
              ],
              lineTouchData: LineTouchData(
                enabled: true,
                touchTooltipData: LineTouchTooltipData(
                  getTooltipItems: (touchedSpots) {
                    return touchedSpots.map((spot) {
                      final dataIndex = spot.x.toInt();
                      if (dataIndex < _correlationData.length) {
                        final data = _correlationData[dataIndex];
                        return LineTooltipItem(
                          'Point $dataIndex\n'
                          'Risk: ${(data.riskScore * 100).toStringAsFixed(1)}%\n'
                          'Effectiveness: ${(data.effectiveness * 100).toStringAsFixed(1)}%',
                          const TextStyle(color: Colors.white),
                        );
                      }
                      return null;
                    }).whereType<LineTooltipItem>().toList();
                  },
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  /// Builds correlation matrix
  Widget _buildCorrelationMatrix() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Correlation Matrix',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: GridView.count(
            crossAxisCount: 3,
            childAspectRatio: 2,
            crossAxisSpacing: 8,
            mainAxisSpacing: 8,
            children: [
              _buildCorrelationCell('Risk → Alerts', _calculateRiskAlertCorrelation()),
              _buildCorrelationCell('Alerts → Response', _calculateAlertResponseCorrelation()),
              _buildCorrelationCell('Response → Outcome', _calculateResponseOutcomeCorrelation()),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds correlation matrix cell
  Widget _buildCorrelationCell(String label, double correlation) {
    final color = _getCorrelationColor(correlation.abs());

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            '${(correlation * 100).toStringAsFixed(0)}%',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds effectiveness analysis view
  Widget _buildEffectivenessAnalysis() {
    return Row(
      children: [
        Expanded(
          child: _buildEffectivenessMetrics(),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildEffectivenessChart(),
        ),
      ],
    );
  }

  /// Builds effectiveness metrics panel
  Widget _buildEffectivenessMetrics() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Effectiveness Metrics',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: [
              _buildEffectivenessMetricCard(
                'Overall Effectiveness',
                _effectivenessMetrics.overallEffectiveness,
                Icons.analytics,
                'Combined alert system performance',
              ),
              const SizedBox(height: 8),
              _buildEffectivenessMetricCard(
                'True Positive Rate',
                _effectivenessMetrics.truePositiveRate,
                Icons.check_circle,
                'Correctly identified high-risk areas',
              ),
              const SizedBox(height: 8),
              _buildEffectivenessMetricCard(
                'False Positive Rate',
                _effectivenessMetrics.falsePositiveRate,
                Icons.error,
                'Incorrectly flagged low-risk areas',
              ),
              const SizedBox(height: 8),
              _buildEffectivenessMetricCard(
                'Coverage',
                _effectivenessMetrics.coverage,
                Icons.coverage,
                'Percentage of high-risk areas covered',
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds effectiveness metric card
  Widget _buildEffectivenessMetricCard(String title, double value, IconData icon, String description) {
    final color = title.contains('False')
        ? _getAccuracyColor(1.0 - value)
        : _getAccuracyColor(value);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: color.withValues(alpha: 0.3)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Text(
                '${(value * 100).toStringAsFixed(1)}%',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            description,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds effectiveness chart
  Widget _buildEffectivenessChart() {
    return Column(
      children: [
        Text(
          'Alert Effectiveness by Severity',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: BarChart(
            BarChartData(
              alignment: BarChartAlignment.spaceAround,
              maxY: 1.0,
              barTouchData: BarTouchData(enabled: true),
              titlesData: FlTitlesData(
                show: true,
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      final severities = AlertSeverity.values;
                      if (value.toInt() < severities.length) {
                        return Text(
                          _getAlertSeverityShortName(severities[value.toInt()]),
                          style: Theme.of(context).textTheme.bodySmall,
                        );
                      }
                      return const Text('');
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '${(value * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodySmall,
                      );
                    },
                  ),
                ),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              gridData: const FlGridData(show: true),
              borderData: FlBorderData(
                show: true,
                border: Border.all(color: Theme.of(context).dividerColor),
              ),
              barGroups: _buildEffectivenessBarGroups(),
            ),
          ),
        ),
      ],
    );
  }

  /// Builds effectiveness bar groups
  List<BarChartGroupData> _buildEffectivenessBarGroups() {
    return AlertSeverity.values.asMap().entries.map((entry) {
      final index = entry.key;
      final severity = entry.value;
      final effectiveness = _calculateSeverityEffectiveness(severity);
      final color = _severityColors[severity] ?? Colors.grey;

      return BarChartGroupData(
        x: index,
        barRods: [
          BarChartRodData(
            toY: effectiveness,
            color: color,
            width: 20,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
          ),
        ],
      );
    }).toList();
  }

  /// Builds response analysis view
  Widget _buildResponseAnalysis() {
    return Column(
      children: [
        Expanded(
          flex: 2,
          child: _buildResponseTimeline(),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: _buildResponseMetrics(),
        ),
      ],
    );
  }

  /// Builds response timeline chart
  Widget _buildResponseTimeline() {
    return Column(
      children: [
        Text(
          'Alert Response Timeline',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: LineChart(
            LineChartData(
              gridData: FlGridData(
                show: true,
                drawVerticalLine: true,
                drawHorizontalLine: true,
              ),
              titlesData: FlTitlesData(
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      if (value.toInt() < _responseAnalysis.length) {
                        return Text(
                          'T${value.toInt()}',
                          style: Theme.of(context).textTheme.bodySmall,
                        );
                      }
                      return const Text('');
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '${value.toInt()}h',
                        style: Theme.of(context).textTheme.bodySmall,
                      );
                    },
                  ),
                ),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              borderData: FlBorderData(
                show: true,
                border: Border.all(color: Theme.of(context).dividerColor),
              ),
              lineBarsData: [
                LineChartBarData(
                  spots: _responseAnalysis.asMap().entries.map((entry) {
                    return FlSpot(
                      entry.key.toDouble(),
                      entry.value.responseTime.inHours.toDouble(),
                    );
                  }).toList(),
                  isCurved: true,
                  color: Colors.orange,
                  barWidth: 3,
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, percent, barData, index) {
                      final analysis = _responseAnalysis[index];
                      final color = _severityColors[analysis.alertSeverity] ?? Colors.grey;
                      return FlDotCirclePainter(
                        radius: 4,
                        color: color,
                        strokeWidth: 1,
                        strokeColor: Colors.white,
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Builds response metrics summary
  Widget _buildResponseMetrics() {
    return GridView.count(
      crossAxisCount: 4,
      childAspectRatio: 1.5,
      crossAxisSpacing: 8,
      mainAxisSpacing: 8,
      children: [
        _buildResponseMetricCard(
          'Avg Response',
          '${widget.alertStatistics.averageResponseTime.inHours}h',
          Icons.timer,
          Colors.orange,
        ),
        _buildResponseMetricCard(
          'False Positives',
          widget.alertStatistics.falsePositives.toString(),
          Icons.error,
          Colors.red,
        ),
        _buildResponseMetricCard(
          'Missed Alerts',
          widget.alertStatistics.missedAlerts.toString(),
          Icons.cancel,
          Colors.purple,
        ),
        _buildResponseMetricCard(
          'Delivery Rate',
          '${(widget.alertStatistics.deliveryRate * 100).toStringAsFixed(0)}%',
          Icons.check_circle,
          Colors.green,
        ),
      ],
    );
  }

  /// Builds response metric card
  Widget _buildResponseMetricCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(
            value,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            title,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds selected period information panel
  Widget _buildSelectedPeriodInfo() {
    if (_selectedPeriod == null) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Period Analysis: ${DateFormat('MMM dd').format(_selectedPeriod!.start)} - ${DateFormat('MMM dd').format(_selectedPeriod!.end)}',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () {
                  setState(() {
                    _selectedPeriod = null;
                  });
                },
                tooltip: 'Close',
              ),
            ],
          ),
          // Add period-specific analysis here
        ],
      ),
    );
  }

  /// Processes correlation data from risk trends and alert statistics
  void _processCorrelationData() {
    if (widget.riskTrends.isEmpty) {
      _correlationData = [];
      _effectivenessMetrics = AlertEffectivenessMetrics.empty();
      _responseAnalysis = [];
      return;
    }

    // Generate correlation data points
    _correlationData = widget.riskTrends.map((trend) {
      // Simulate alert count based on risk level
      final alertCount = _simulateAlertCount(trend.riskLevel);
      final effectiveness = _calculateEffectiveness(trend.riskScore, alertCount);

      return AlertCorrelationPoint(
        riskScore: trend.riskScore,
        alertCount: alertCount,
        effectiveness: effectiveness,
        timestamp: trend.date,
        riskLevel: trend.riskLevel,
      );
    }).toList();

    // Calculate effectiveness metrics
    _effectivenessMetrics = _calculateEffectivenessMetrics();

    // Generate response analysis
    _responseAnalysis = _generateResponseAnalysis();
  }

  /// Simulates alert count based on risk level
  int _simulateAlertCount(RiskLevel riskLevel) {
    final baseCount = widget.alertStatistics.totalAlerts / widget.riskTrends.length;

    switch (riskLevel) {
      case RiskLevel.critical:
        return (baseCount * 2).round();
      case RiskLevel.high:
        return (baseCount * 1.5).round();
      case RiskLevel.medium:
        return baseCount.round();
      case RiskLevel.low:
        return (baseCount * 0.5).round();
    }
  }

  /// Calculates effectiveness for a risk-alert pair
  double _calculateEffectiveness(double riskScore, int alertCount) {
    // Simple effectiveness calculation based on risk-alert correlation
    final expectedAlerts = riskScore * 10; // Expected alerts based on risk
    final alertRatio = alertCount / expectedAlerts;

    // Effectiveness is higher when alert count matches expected alerts
    return math.max(0.0, math.min(1.0, 1.0 - (alertRatio - 1.0).abs()));
  }

  /// Calculates overall effectiveness metrics
  AlertEffectivenessMetrics _calculateEffectivenessMetrics() {
    if (_correlationData.isEmpty) return AlertEffectivenessMetrics.empty();

    final avgEffectiveness = _correlationData
        .map((c) => c.effectiveness)
        .reduce((a, b) => a + b) / _correlationData.length;

    // Calculate true positive rate
    final highRiskTrends = widget.riskTrends.where((t) =>
        t.riskLevel == RiskLevel.high || t.riskLevel == RiskLevel.critical).length;
    final totalTrends = widget.riskTrends.length;
    final truePositiveRate = totalTrends > 0 ? highRiskTrends / totalTrends : 0.0;

    // Calculate false positive rate
    final falsePositiveRate = widget.alertStatistics.totalAlerts > 0
        ? widget.alertStatistics.falsePositives / widget.alertStatistics.totalAlerts
        : 0.0;

    // Calculate coverage
    final coverage = widget.alertStatistics.deliveryRate;

    return AlertEffectivenessMetrics(
      overallEffectiveness: avgEffectiveness,
      truePositiveRate: truePositiveRate,
      falsePositiveRate: falsePositiveRate,
      coverage: coverage,
      averageResponseTime: widget.alertStatistics.averageResponseTime,
    );
  }

  /// Generates response analysis data
  List<AlertResponseAnalysis> _generateResponseAnalysis() {
    return AlertSeverity.values.map((severity) {
      final alertCount = widget.alertStatistics.alertsBySeverity[severity] ?? 0;
      final responseTime = Duration(
        hours: widget.alertStatistics.averageResponseTime.inHours +
               _getSeverityResponseModifier(severity),
      );

      return AlertResponseAnalysis(
        alertSeverity: severity,
        alertCount: alertCount,
        responseTime: responseTime,
        effectiveness: _calculateSeverityEffectiveness(severity),
      );
    }).toList();
  }

  /// Gets response time modifier for alert severity
  int _getSeverityResponseModifier(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.emergency:
        return -3;
      case AlertSeverity.critical:
        return -2;
      case AlertSeverity.high:
        return -1;
      case AlertSeverity.warning:
        return 0;
      case AlertSeverity.info:
        return 1;
    }
  }

  /// Calculates effectiveness for specific alert severity
  double _calculateSeverityEffectiveness(AlertSeverity severity) {
    final totalAlerts = widget.alertStatistics.totalAlerts;
    final severityAlerts = widget.alertStatistics.alertsBySeverity[severity] ?? 0;

    if (totalAlerts == 0) return 0.0;

    // Higher severity should have higher effectiveness
    final severityWeight = _getSeverityWeight(severity);
    final alertRatio = severityAlerts / totalAlerts;

    return math.min(1.0, alertRatio * severityWeight);
  }

  /// Gets weight for alert severity
  double _getSeverityWeight(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.emergency:
        return 5.0;
      case AlertSeverity.critical:
        return 4.0;
      case AlertSeverity.high:
        return 3.0;
      case AlertSeverity.warning:
        return 2.0;
      case AlertSeverity.info:
        return 1.0;
    }
  }

  /// Calculates correlation strength between risk and alerts
  double _calculateCorrelationStrength() {
    if (_correlationData.length < 2) return 0.0;

    // Calculate Pearson correlation coefficient
    final n = _correlationData.length;
    final meanRisk = _correlationData.map((c) => c.riskScore).reduce((a, b) => a + b) / n;
    final meanAlerts = _correlationData.map((c) => c.alertCount).reduce((a, b) => a + b) / n;

    double numerator = 0;
    double denomRisk = 0;
    double denomAlerts = 0;

    for (final data in _correlationData) {
      final riskDiff = data.riskScore - meanRisk;
      final alertDiff = data.alertCount - meanAlerts;

      numerator += riskDiff * alertDiff;
      denomRisk += riskDiff * riskDiff;
      denomAlerts += alertDiff * alertDiff;
    }

    final denominator = math.sqrt(denomRisk * denomAlerts);
    return denominator > 0 ? numerator / denominator : 0.0;
  }

  /// Calculates alert accuracy
  double _calculateAlertAccuracy() {
    final totalAlerts = widget.alertStatistics.totalAlerts;
    final falsePositives = widget.alertStatistics.falsePositives;

    return totalAlerts > 0 ? (totalAlerts - falsePositives) / totalAlerts : 0.0;
  }

  /// Calculates risk-alert correlation
  double _calculateRiskAlertCorrelation() {
    return _calculateCorrelationStrength();
  }

  /// Calculates alert-response correlation
  double _calculateAlertResponseCorrelation() {
    // Inverse correlation - higher alerts should lead to faster response
    return 1.0 - (widget.alertStatistics.averageResponseTime.inHours / 24.0);
  }

  /// Calculates response-outcome correlation
  double _calculateResponseOutcomeCorrelation() {
    // Higher delivery rate indicates better outcome correlation
    return widget.alertStatistics.deliveryRate;
  }

  /// Gets maximum alert count for chart scaling
  int _getMaxAlertCount() {
    if (_correlationData.isEmpty) return 10;
    return _correlationData.map((c) => c.alertCount).reduce(math.max);
  }

  /// Gets view mode icon
  IconData _getViewModeIcon(CorrelationViewMode mode) {
    switch (mode) {
      case CorrelationViewMode.overview:
        return Icons.dashboard;
      case CorrelationViewMode.correlation:
        return Icons.analytics;
      case CorrelationViewMode.effectiveness:
        return Icons.assessment;
      case CorrelationViewMode.response:
        return Icons.timeline;
    }
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(CorrelationViewMode mode) {
    switch (mode) {
      case CorrelationViewMode.overview:
        return 'Overview';
      case CorrelationViewMode.correlation:
        return 'Correlation';
      case CorrelationViewMode.effectiveness:
        return 'Effectiveness';
      case CorrelationViewMode.response:
        return 'Response';
    }
  }

  /// Gets alert severity short name
  String _getAlertSeverityShortName(AlertSeverity severity) {
    switch (severity) {
      case AlertSeverity.info:
        return 'Info';
      case AlertSeverity.warning:
        return 'Warn';
      case AlertSeverity.high:
        return 'High';
      case AlertSeverity.critical:
        return 'Crit';
      case AlertSeverity.emergency:
        return 'Emrg';
    }
  }

  /// Gets effectiveness color based on percentage
  Color _getEffectivenessColor(double effectiveness) {
    if (effectiveness >= 80) return Colors.green;
    if (effectiveness >= 60) return Colors.orange;
    if (effectiveness >= 40) return Colors.red;
    return Colors.grey;
  }

  /// Gets effectiveness icon based on percentage
  IconData _getEffectivenessIcon(double effectiveness) {
    if (effectiveness >= 80) return Icons.check_circle;
    if (effectiveness >= 60) return Icons.warning;
    if (effectiveness >= 40) return Icons.error;
    return Icons.cancel;
  }

  /// Gets correlation color based on strength
  Color _getCorrelationColor(double correlation) {
    if (correlation >= 0.7) return Colors.green;
    if (correlation >= 0.5) return Colors.orange;
    if (correlation >= 0.3) return Colors.red;
    return Colors.grey;
  }

  /// Gets accuracy color based on value
  Color _getAccuracyColor(double accuracy) {
    if (accuracy >= 0.9) return Colors.green;
    if (accuracy >= 0.7) return Colors.orange;
    if (accuracy >= 0.5) return Colors.red;
    return Colors.grey;
  }
}

/// Correlation view mode enumeration
enum CorrelationViewMode {
  overview,
  correlation,
  effectiveness,
  response,
}

/// Alert correlation point structure
class AlertCorrelationPoint {
  final double riskScore;
  final int alertCount;
  final double effectiveness;
  final DateTime timestamp;
  final RiskLevel riskLevel;

  const AlertCorrelationPoint({
    required this.riskScore,
    required this.alertCount,
    required this.effectiveness,
    required this.timestamp,
    required this.riskLevel,
  });
}

/// Alert effectiveness metrics structure
class AlertEffectivenessMetrics {
  final double overallEffectiveness;
  final double truePositiveRate;
  final double falsePositiveRate;
  final double coverage;
  final Duration averageResponseTime;

  const AlertEffectivenessMetrics({
    required this.overallEffectiveness,
    required this.truePositiveRate,
    required this.falsePositiveRate,
    required this.coverage,
    required this.averageResponseTime,
  });

  factory AlertEffectivenessMetrics.empty() {
    return const AlertEffectivenessMetrics(
      overallEffectiveness: 0.0,
      truePositiveRate: 0.0,
      falsePositiveRate: 0.0,
      coverage: 0.0,
      averageResponseTime: Duration.zero,
    );
  }
}

/// Alert response analysis structure
class AlertResponseAnalysis {
  final AlertSeverity alertSeverity;
  final int alertCount;
  final Duration responseTime;
  final double effectiveness;

  const AlertResponseAnalysis({
    required this.alertSeverity,
    required this.alertCount,
    required this.responseTime,
    required this.effectiveness,
  });
}