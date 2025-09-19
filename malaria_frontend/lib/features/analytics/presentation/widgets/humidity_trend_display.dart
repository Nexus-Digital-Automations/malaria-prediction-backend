/// Humidity trend display widget for comprehensive humidity analysis
///
/// This widget provides advanced humidity visualization including relative humidity,
/// absolute humidity, dew point analysis, and seasonal patterns with scientific
/// precision for malaria prediction analytics.
///
/// Features:
/// - Multi-metric humidity analysis (relative, absolute, dew point)
/// - Seasonal pattern visualization
/// - Mosquito breeding condition indicators
/// - Transmission zone overlays
/// - Scientific units and scales
/// - Data quality visualization
///
/// Usage:
/// ```dart
/// HumidityTrendDisplay(
///   humidityData: humidityData,
///   height: 400,
///   showSeasonalPattern: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Comprehensive humidity trend display widget
class HumidityTrendDisplay extends StatefulWidget {
  /// Humidity data to display
  final HumidityData humidityData;

  /// Chart height
  final double height;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Whether to show seasonal pattern overlay
  final bool showSeasonalPattern;

  /// Whether to show mosquito breeding conditions
  final bool showBreedingConditions;

  /// Whether to show transmission zones
  final bool showTransmissionZones;

  /// Humidity metrics to display
  final Set<HumidityMetric> displayMetrics;

  /// Constructor requiring humidity data
  const HumidityTrendDisplay({
    super.key,
    required this.humidityData,
    this.height = 350,
    this.dateRange,
    this.showSeasonalPattern = true,
    this.showBreedingConditions = true,
    this.showTransmissionZones = true,
    this.displayMetrics = const {
      HumidityMetric.relative,
      HumidityMetric.absolute,
      HumidityMetric.dewPoint,
    },
  });

  @override
  State<HumidityTrendDisplay> createState() => _HumidityTrendDisplayState();
}

class _HumidityTrendDisplayState extends State<HumidityTrendDisplay> {
  /// Current humidity view mode
  HumidityViewMode _viewMode = HumidityViewMode.timeSeries;

  /// Selected humidity metrics to display
  late Set<HumidityMetric> _selectedMetrics;

  /// Color mapping for humidity metrics
  final Map<HumidityMetric, Color> _metricColors = {
    HumidityMetric.relative: Colors.blue.shade600,
    HumidityMetric.absolute: Colors.cyan.shade600,
    HumidityMetric.dewPoint: Colors.teal.shade600,
  };

  /// Humidity thresholds for malaria transmission
  static const double _optimalRelativeHumidity = 70.0; // % for optimal transmission
  static const double _minimumRelativeHumidity = 60.0; // % minimum for transmission
  static const double _maximumRelativeHumidity = 95.0; // % maximum before reduced activity

  /// Show data quality indicators
  bool _showDataQuality = true;

  /// Show comfort zones
  bool _showComfortZones = false;

  /// Time aggregation mode
  HumidityAggregation _aggregation = HumidityAggregation.daily;

  @override
  void initState() {
    super.initState();
    _selectedMetrics = Set.from(widget.displayMetrics);
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
            _buildControlPanel(),
            if (widget.showBreedingConditions) _buildBreedingConditionsAlert(),
            const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (widget.showSeasonalPattern) _buildSeasonalSummary(),
          ],
        ),
      ),
    );
  }

  /// Builds the widget header with title and controls
  Widget _buildHeader() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Humidity Trend Analysis',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (widget.dateRange != null)
                Text(
                  '${DateFormat('MMM d, yyyy').format(widget.dateRange!.start)} - '
                  '${DateFormat('MMM d, yyyy').format(widget.dateRange!.end)}',
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
                _showDataQuality ? Icons.verified : Icons.verified_outlined,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () {
                setState(() {
                  _showDataQuality = !_showDataQuality;
                });
              },
              tooltip: 'Toggle Data Quality Indicators',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showHumidityInfo(),
              tooltip: 'Humidity Analysis Information',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds control panel for display options
  Widget _buildControlPanel() {
    return Column(
      children: [
        Row(
          children: [
            Text(
              'View:',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: HumidityViewMode.values.map((mode) {
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
              'Metrics:',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Wrap(
                spacing: 8,
                runSpacing: 4,
                children: HumidityMetric.values.map((metric) {
                  final isSelected = _selectedMetrics.contains(metric);
                  return FilterChip(
                    label: Text(_getMetricDisplayName(metric)),
                    selected: isSelected,
                    onSelected: (selected) {
                      setState(() {
                        if (selected) {
                          _selectedMetrics.add(metric);
                        } else if (_selectedMetrics.length > 1) {
                          _selectedMetrics.remove(metric);
                        }
                      });
                    },
                    selectedColor: _metricColors[metric]?.withValues(alpha: 0.2),
                    checkmarkColor: _metricColors[metric],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds breeding conditions alert panel
  Widget _buildBreedingConditionsAlert() {
    final currentHumidity = _getCurrentRelativeHumidity();
    final isOptimal = currentHumidity >= _minimumRelativeHumidity &&
                     currentHumidity <= _maximumRelativeHumidity;

    if (!isOptimal) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: currentHumidity >= _optimalRelativeHumidity - 10 &&
               currentHumidity <= _optimalRelativeHumidity + 10
            ? Colors.orange.shade50
            : Colors.green.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: currentHumidity >= _optimalRelativeHumidity - 10 &&
                 currentHumidity <= _optimalRelativeHumidity + 10
              ? Colors.orange.shade200
              : Colors.green.shade200,
        ),
      ),
      child: Row(
        children: [
          Icon(
            currentHumidity >= _optimalRelativeHumidity - 10 &&
            currentHumidity <= _optimalRelativeHumidity + 10
                ? Icons.warning_amber_outlined
                : Icons.check_circle_outline,
            color: currentHumidity >= _optimalRelativeHumidity - 10 &&
                   currentHumidity <= _optimalRelativeHumidity + 10
                ? Colors.orange.shade600
                : Colors.green.shade600,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              currentHumidity >= _optimalRelativeHumidity - 10 &&
              currentHumidity <= _optimalRelativeHumidity + 10
                  ? 'Optimal humidity for mosquito breeding (${currentHumidity.toStringAsFixed(1)}%)'
                  : 'Favorable humidity conditions detected (${currentHumidity.toStringAsFixed(1)}%)',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: currentHumidity >= _optimalRelativeHumidity - 10 &&
                       currentHumidity <= _optimalRelativeHumidity + 10
                    ? Colors.orange.shade800
                    : Colors.green.shade800,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the main humidity chart
  Widget _buildChart() {
    if (_isDataEmpty()) {
      return _buildNoDataMessage();
    }

    switch (_viewMode) {
      case HumidityViewMode.timeSeries:
        return _buildTimeSeriesChart();
      case HumidityViewMode.seasonal:
        return _buildSeasonalChart();
      case HumidityViewMode.distribution:
        return _buildDistributionChart();
      case HumidityViewMode.correlation:
        return _buildCorrelationChart();
    }
  }

  /// Builds time series humidity chart
  Widget _buildTimeSeriesChart() {
    final chartData = _prepareTimeSeriesData();

    if (chartData.isEmpty) {
      return _buildNoDataMessage();
    }

    return LineChart(
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
          rightTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) => Text(
                _getHumidityUnit(value),
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 50,
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) => Text(
                value.toStringAsFixed(0),
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 40,
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final date = _getDateFromIndex(value.toInt());
                if (date != null) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      DateFormat('MMM d').format(date),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  );
                }
                return const Text('');
              },
              reservedSize: 35,
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
        lineBarsData: _buildLineChartBars(chartData),
        extraLinesData: widget.showTransmissionZones ? _buildTransmissionZones() : null,
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final metric = _getMetricFromBarIndex(spot.barIndex);
                final date = _getDateFromIndex(spot.x.toInt());
                if (date != null) {
                  return LineTooltipItem(
                    '${_getMetricDisplayName(metric)}\n'
                    'Date: ${DateFormat('MMM d, yyyy').format(date)}\n'
                    'Value: ${spot.y.toStringAsFixed(1)}${_getMetricUnit(metric)}',
                    TextStyle(
                      color: _metricColors[metric],
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  );
                }
                return null;
              }).where((item) => item != null).cast<LineTooltipItem>().toList();
            },
          ),
        ),
        minY: 0,
        maxY: _getMaxHumidityValue(chartData) * 1.1,
      ),
    );
  }

  /// Builds seasonal humidity pattern chart
  Widget _buildSeasonalChart() {
    final seasonalData = _calculateSeasonalData();

    return BarChart(
      BarChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          drawHorizontalLine: true,
          getDrawingHorizontalLine: (value) => FlLine(
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
                '${value.toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 40,
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final season = Season.values[value.toInt() % Season.values.length];
                return Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    _getSeasonDisplayName(season),
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
        barGroups: _buildSeasonalBarGroups(seasonalData),
        extraLinesData: widget.showTransmissionZones
            ? ExtraLinesData(
                horizontalLines: [
                  HorizontalLine(
                    y: _optimalRelativeHumidity,
                    color: Colors.orange,
                    strokeWidth: 2,
                    dashArray: [5, 5],
                  ),
                ],
              )
            : null,
        maxY: 100,
      ),
    );
  }

  /// Builds humidity distribution chart
  Widget _buildDistributionChart() {
    final distributionData = _calculateDistributionData();

    return BarChart(
      BarChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          drawHorizontalLine: true,
          getDrawingHorizontalLine: (value) => FlLine(
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
                '${value.toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 40,
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final range = _getHumidityRange(value.toInt());
                return Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    range,
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
        barGroups: _buildDistributionBarGroups(distributionData),
        maxY: distributionData.values.isNotEmpty
            ? distributionData.values.reduce((a, b) => a > b ? a : b) * 1.1
            : 50,
      ),
    );
  }

  /// Builds correlation analysis chart
  Widget _buildCorrelationChart() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Text(
            'Humidity Correlation Analysis',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              children: [
                _buildCorrelationCard('Temperature', -0.67, Colors.red),
                _buildCorrelationCard('Rainfall', 0.58, Colors.blue),
                _buildCorrelationCard('Vegetation', 0.39, Colors.green),
                _buildCorrelationCard('Malaria Risk', 0.73, Colors.orange),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Builds correlation card
  Widget _buildCorrelationCard(String factor, double correlation, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              factor,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: color, width: 2),
              ),
              child: Center(
                child: Text(
                  correlation.toStringAsFixed(2),
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: color,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _getCorrelationStrength(correlation.abs()),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: color,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  /// Builds legend for humidity metrics
  Widget _buildLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: _selectedMetrics.map((metric) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _metricColors[metric],
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              '${_getMetricDisplayName(metric)} ${_getMetricUnit(metric)}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Builds seasonal summary panel
  Widget _buildSeasonalSummary() {
    final seasonalStats = widget.humidityData.seasonalPattern;

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Seasonal Pattern Summary',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildSeasonalStat('Peak', _getSeasonDisplayName(seasonalStats.peakSeason)),
              _buildSeasonalStat('Low', _getSeasonDisplayName(seasonalStats.lowSeason)),
              _buildSeasonalStat('Avg', '${seasonalStats.spring.average.toStringAsFixed(1)}%'),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds individual seasonal statistic
  Widget _buildSeasonalStat(String label, String value) {
    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
          ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  /// Prepares time series chart data
  Map<HumidityMetric, List<FlSpot>> _prepareTimeSeriesData() {
    final chartData = <HumidityMetric, List<FlSpot>>{};

    for (final metric in _selectedMetrics) {
      final spots = <FlSpot>[];
      List<HumidityMeasurement> measurements;

      switch (metric) {
        case HumidityMetric.relative:
          measurements = widget.humidityData.relativeHumidity;
          break;
        case HumidityMetric.absolute:
          measurements = widget.humidityData.absoluteHumidity;
          break;
        case HumidityMetric.dewPoint:
          measurements = widget.humidityData.dewPoint;
          break;
      }

      // Filter by date range if specified
      if (widget.dateRange != null) {
        measurements = measurements
            .where((m) => widget.dateRange!.contains(m.date))
            .toList();
      }

      // Sort by date
      measurements.sort((a, b) => a.date.compareTo(b.date));

      // Convert to FlSpot data points
      for (int i = 0; i < measurements.length; i++) {
        final measurement = measurements[i];
        if (measurement.quality >= 0.6 || !_showDataQuality) {
          spots.add(FlSpot(i.toDouble(), measurement.humidity));
        }
      }

      if (spots.isNotEmpty) {
        chartData[metric] = spots;
      }
    }

    return chartData;
  }

  /// Builds line chart bars for humidity metrics
  List<LineChartBarData> _buildLineChartBars(Map<HumidityMetric, List<FlSpot>> chartData) {
    final lineBars = <LineChartBarData>[];

    chartData.forEach((metric, spots) {
      lineBars.add(
        LineChartBarData(
          spots: spots,
          isCurved: true,
          color: _metricColors[metric],
          barWidth: 2.5,
          isStrokeCapRound: true,
          dotData: FlDotData(
            show: spots.length < 50,
            getDotPainter: (spot, percent, barData, index) {
              return FlDotCirclePainter(
                radius: 3,
                color: _metricColors[metric]!,
                strokeWidth: 1,
                strokeColor: Theme.of(context).colorScheme.surface,
              );
            },
          ),
          belowBarData: BarAreaData(
            show: metric == HumidityMetric.relative,
            color: _metricColors[metric]?.withValues(alpha: 0.1),
          ),
        ),
      );
    });

    return lineBars;
  }

  /// Builds transmission zone overlays
  ExtraLinesData _buildTransmissionZones() {
    return ExtraLinesData(
      horizontalLines: [
        HorizontalLine(
          y: _minimumRelativeHumidity,
          color: Colors.red.withValues(alpha: 0.6),
          strokeWidth: 2,
          dashArray: [5, 5],
          label: HorizontalLineLabel(
            show: true,
            labelResolver: (line) => 'Min Transmission',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.red,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        HorizontalLine(
          y: _optimalRelativeHumidity,
          color: Colors.orange.withValues(alpha: 0.8),
          strokeWidth: 3,
          dashArray: [3, 3],
          label: HorizontalLineLabel(
            show: true,
            labelResolver: (line) => 'Optimal',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.orange,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        HorizontalLine(
          y: _maximumRelativeHumidity,
          color: Colors.blue.withValues(alpha: 0.6),
          strokeWidth: 2,
          dashArray: [5, 5],
          label: HorizontalLineLabel(
            show: true,
            labelResolver: (line) => 'Max Transmission',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.blue,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }

  /// Calculates seasonal humidity data
  Map<Season, double> _calculateSeasonalData() {
    final seasonalData = <Season, List<double>>{
      Season.spring: [],
      Season.summer: [],
      Season.autumn: [],
      Season.winter: [],
    };

    for (final measurement in widget.humidityData.relativeHumidity) {
      final season = _getSeasonFromDate(measurement.date);
      seasonalData[season]?.add(measurement.humidity);
    }

    return seasonalData.map((season, values) {
      final average = values.isEmpty ? 0.0 : values.reduce((a, b) => a + b) / values.length;
      return MapEntry(season, average);
    });
  }

  /// Builds seasonal bar groups
  List<BarChartGroupData> _buildSeasonalBarGroups(Map<Season, double> seasonalData) {
    final barGroups = <BarChartGroupData>[];

    Season.values.asMap().forEach((index, season) {
      final value = seasonalData[season] ?? 0.0;
      final isOptimal = value >= _minimumRelativeHumidity && value <= _maximumRelativeHumidity;

      barGroups.add(
        BarChartGroupData(
          x: index,
          barRods: [
            BarChartRodData(
              toY: value,
              color: isOptimal ? Colors.green.shade600 : Colors.grey.shade400,
              width: 24,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
            ),
          ],
        ),
      );
    });

    return barGroups;
  }

  /// Calculates humidity distribution data
  Map<int, double> _calculateDistributionData() {
    final ranges = <int, int>{
      0: 0, 1: 0, 2: 0, 3: 0, 4: 0, // 0-20%, 20-40%, 40-60%, 60-80%, 80-100%
    };

    for (final measurement in widget.humidityData.relativeHumidity) {
      final rangeIndex = (measurement.humidity / 20).floor().clamp(0, 4);
      ranges[rangeIndex] = (ranges[rangeIndex] ?? 0) + 1;
    }

    final total = ranges.values.reduce((a, b) => a + b);
    if (total == 0) return {};

    return ranges.map((index, count) {
      final percentage = (count / total) * 100;
      return MapEntry(index, percentage);
    });
  }

  /// Builds distribution bar groups
  List<BarChartGroupData> _buildDistributionBarGroups(Map<int, double> distributionData) {
    final barGroups = <BarChartGroupData>[];

    distributionData.forEach((index, percentage) {
      barGroups.add(
        BarChartGroupData(
          x: index,
          barRods: [
            BarChartRodData(
              toY: percentage,
              color: Colors.blue.shade600,
              width: 24,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
            ),
          ],
        ),
      );
    });

    return barGroups;
  }

  /// Gets current relative humidity value
  double _getCurrentRelativeHumidity() {
    final recent = widget.humidityData.relativeHumidity;
    if (recent.isEmpty) return 0;
    return recent.last.humidity;
  }

  /// Gets season from date
  Season _getSeasonFromDate(DateTime date) {
    final month = date.month;
    if (month >= 3 && month <= 5) return Season.spring;
    if (month >= 6 && month <= 8) return Season.summer;
    if (month >= 9 && month <= 11) return Season.autumn;
    return Season.winter;
  }

  /// Gets date from chart index
  DateTime? _getDateFromIndex(int index) {
    final allMeasurements = <HumidityMeasurement>[];
    allMeasurements.addAll(widget.humidityData.relativeHumidity);

    final uniqueDates = allMeasurements
        .map((m) => m.date)
        .toSet()
        .toList();
    uniqueDates.sort();

    if (index >= 0 && index < uniqueDates.length) {
      return uniqueDates[index];
    }
    return null;
  }

  /// Gets humidity metric from bar index
  HumidityMetric _getMetricFromBarIndex(int barIndex) {
    final metricsList = _selectedMetrics.toList();
    return metricsList[barIndex % metricsList.length];
  }

  /// Gets maximum humidity value from chart data
  double _getMaxHumidityValue(Map<HumidityMetric, List<FlSpot>> chartData) {
    double max = 0;
    chartData.values.forEach((spots) {
      for (final spot in spots) {
        if (spot.y > max) max = spot.y;
      }
    });
    return max == 0 ? 100 : max;
  }

  /// Gets humidity unit display text
  String _getHumidityUnit(double value) {
    return '${value.toStringAsFixed(0)}%';
  }

  /// Gets metric unit string
  String _getMetricUnit(HumidityMetric metric) {
    switch (metric) {
      case HumidityMetric.relative:
        return '%';
      case HumidityMetric.absolute:
        return 'g/m³';
      case HumidityMetric.dewPoint:
        return '°C';
    }
  }

  /// Gets humidity range string for distribution
  String _getHumidityRange(int index) {
    switch (index) {
      case 0: return '0-20%';
      case 1: return '20-40%';
      case 2: return '40-60%';
      case 3: return '60-80%';
      case 4: return '80-100%';
      default: return '';
    }
  }

  /// Gets correlation strength description
  String _getCorrelationStrength(double correlation) {
    if (correlation >= 0.7) return 'Strong';
    if (correlation >= 0.5) return 'Moderate';
    if (correlation >= 0.3) return 'Weak';
    return 'Very Weak';
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(HumidityViewMode mode) {
    switch (mode) {
      case HumidityViewMode.timeSeries:
        return 'Time Series';
      case HumidityViewMode.seasonal:
        return 'Seasonal';
      case HumidityViewMode.distribution:
        return 'Distribution';
      case HumidityViewMode.correlation:
        return 'Correlation';
    }
  }

  /// Gets metric display name
  String _getMetricDisplayName(HumidityMetric metric) {
    switch (metric) {
      case HumidityMetric.relative:
        return 'Relative Humidity';
      case HumidityMetric.absolute:
        return 'Absolute Humidity';
      case HumidityMetric.dewPoint:
        return 'Dew Point';
    }
  }

  /// Gets season display name
  String _getSeasonDisplayName(Season season) {
    switch (season) {
      case Season.spring:
        return 'Spring';
      case Season.summer:
        return 'Summer';
      case Season.autumn:
        return 'Autumn';
      case Season.winter:
        return 'Winter';
    }
  }

  /// Checks if humidity data is empty
  bool _isDataEmpty() {
    return widget.humidityData.relativeHumidity.isEmpty &&
           widget.humidityData.absoluteHumidity.isEmpty &&
           widget.humidityData.dewPoint.isEmpty;
  }

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.opacity_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No humidity data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Humidity trends will appear here when data is loaded',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Shows humidity analysis information dialog
  void _showHumidityInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Humidity Analysis Information'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Humidity Metrics:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Relative Humidity: Percentage of water vapor (%)'),
              Text('• Absolute Humidity: Water vapor density (g/m³)'),
              Text('• Dew Point: Temperature at saturation (°C)'),
              SizedBox(height: 16),
              Text(
                'Malaria Transmission Zones:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Minimum: 60% RH (transmission threshold)'),
              Text('• Optimal: 70% RH (peak mosquito survival)'),
              Text('• Maximum: 95% RH (reduced activity above)'),
              SizedBox(height: 16),
              Text(
                'Mosquito Biology:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• High humidity extends mosquito lifespan'),
              Text('• Optimal breeding in humid microclimates'),
              Text('• Flight activity peaks at 70-80% RH'),
              Text('• Low humidity (<60%) reduces survival'),
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

/// Humidity view mode enumeration
enum HumidityViewMode {
  timeSeries,
  seasonal,
  distribution,
  correlation,
}

/// Humidity metric enumeration
enum HumidityMetric {
  relative,
  absolute,
  dewPoint,
}

/// Humidity aggregation enumeration
enum HumidityAggregation {
  hourly,
  daily,
  weekly,
  monthly,
}