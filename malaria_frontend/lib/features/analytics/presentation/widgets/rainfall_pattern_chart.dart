/// Rainfall pattern chart widget using fl_chart for seasonal grouping visualization
///
/// This widget displays comprehensive rainfall pattern data including daily,
/// monthly measurements, seasonal patterns, extreme events, and post-rainfall
/// malaria risk periods using interactive bar charts with seasonal grouping.
///
/// Usage:
/// ```dart
/// RainfallPatternChart(
///   rainfallData: rainfallData,
///   height: 400,
///   viewMode: RainfallViewMode.seasonal,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Rainfall pattern chart widget with seasonal grouping bar visualization
class RainfallPatternChart extends StatefulWidget {
  /// Rainfall data to display
  final RainfallData rainfallData;

  /// Chart height
  final double height;

  /// View mode for rainfall data presentation
  final RainfallViewMode viewMode;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Whether to show extreme events overlay
  final bool showExtremeEvents;

  /// Whether to show post-rainfall risk periods
  final bool showRiskPeriods;

  /// Constructor requiring rainfall data
  const RainfallPatternChart({
    super.key,
    required this.rainfallData,
    this.height = 350,
    this.viewMode = RainfallViewMode.seasonal,
    this.dateRange,
    this.showExtremeEvents = false,
    this.showRiskPeriods = false,
  });

  @override
  State<RainfallPatternChart> createState() => _RainfallPatternChartState();
}

class _RainfallPatternChartState extends State<RainfallPatternChart> {
  /// Current rainfall view mode
  late RainfallViewMode _currentViewMode;

  /// Color mapping for seasonal patterns
  final Map<Season, Color> _seasonColors = {
    Season.spring: Colors.green,
    Season.summer: Colors.orange,
    Season.autumn: Colors.brown,
    Season.winter: Colors.blue,
  };

  /// Color mapping for rainfall intensity levels
  final Map<RainfallIntensity, Color> _intensityColors = {
    RainfallIntensity.light: Colors.lightBlue.shade200,
    RainfallIntensity.moderate: Colors.blue.shade400,
    RainfallIntensity.heavy: Colors.blue.shade700,
    RainfallIntensity.extreme: Colors.red.shade600,
  };

  /// Minimum rainfall threshold for malaria transmission (80mm)
  final double _transmissionThreshold = 80.0;

  /// Show cumulative rainfall toggle
  bool _showCumulative = false;

  /// Show rainfall deficit analysis
  final bool _showDeficit = false;

  @override
  void initState() {
    super.initState();
    _currentViewMode = widget.viewMode;
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
            if (widget.showRiskPeriods) _buildRiskIndicators(),
            const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (widget.showExtremeEvents) _buildExtremeEventsIndicator(),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header with title and controls
  Widget _buildHeader() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Rainfall Pattern Analysis',
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
                _showCumulative ? Icons.trending_up : Icons.bar_chart,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () {
                setState(() {
                  _showCumulative = !_showCumulative;
                });
              },
              tooltip: 'Toggle Cumulative View',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showRainfallInfo(),
              tooltip: 'Rainfall Analysis Info',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds view mode selector for different rainfall presentations
  Widget _buildViewModeSelector() {
    return Row(
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
              children: RainfallViewMode.values.map((mode) {
                final isSelected = mode == _currentViewMode;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(_getViewModeDisplayName(mode)),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        setState(() {
                          _currentViewMode = mode;
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
    );
  }

  /// Builds malaria risk indicators for post-rainfall periods
  Widget _buildRiskIndicators() {
    final riskPeriods = widget.rainfallData.postRainfallPeriods;
    final currentRiskPeriods = riskPeriods
        .where((period) => period.peakRiskDate.isAfter(DateTime.now().subtract(const Duration(days: 30))))
        .toList();

    if (currentRiskPeriods.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.orange.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange.shade200),
      ),
      child: Row(
        children: [
          Icon(
            Icons.warning_amber_outlined,
            color: Colors.orange.shade600,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Active Risk Period: ${currentRiskPeriods.length} post-rainfall risk zone(s)',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.orange.shade800,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the main rainfall pattern chart
  Widget _buildChart() {
    if (_isDataEmpty()) {
      return _buildNoDataMessage();
    }

    switch (_currentViewMode) {
      case RainfallViewMode.seasonal:
        return _buildSeasonalChart();
      case RainfallViewMode.monthly:
        return _buildMonthlyChart();
      case RainfallViewMode.daily:
        return _buildDailyChart();
      case RainfallViewMode.intensity:
        return _buildIntensityChart();
    }
  }

  /// Builds seasonal rainfall pattern chart
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
                '${value.toStringAsFixed(0)}mm',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 50,
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
        barTouchData: BarTouchData(
          touchTooltipData: BarTouchTooltipData(
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              final season = Season.values[groupIndex];
              final value = rod.toY;
              return BarTooltipItem(
                '${_getSeasonDisplayName(season)}\n'
                'Rainfall: ${value.toStringAsFixed(1)}mm\n'
                'Transmission Risk: ${_getRiskLevel(value)}',
                TextStyle(
                  color: _seasonColors[season],
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              );
            },
          ),
        ),
        maxY: _getMaxRainfall(seasonalData.values.toList()) * 1.1,
      ),
    );
  }

  /// Builds monthly rainfall chart
  Widget _buildMonthlyChart() {
    final monthlyData = widget.rainfallData.monthly;

    if (monthlyData.isEmpty) {
      return _buildNoDataMessage();
    }

    final barGroups = <BarChartGroupData>[];
    final filteredData = widget.dateRange != null
        ? monthlyData.where((m) => widget.dateRange!.contains(m.date)).toList()
        : monthlyData;

    filteredData.sort((a, b) => a.date.compareTo(b.date));

    for (int i = 0; i < filteredData.length; i++) {
      final measurement = filteredData[i];
      final color = _getRainfallColor(measurement.rainfall);

      barGroups.add(
        BarChartGroupData(
          x: i,
          barRods: [
            BarChartRodData(
              toY: measurement.rainfall,
              color: color,
              width: 16,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
            ),
          ],
        ),
      );
    }

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
                '${value.toStringAsFixed(0)}mm',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 50,
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index >= 0 && index < filteredData.length) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      DateFormat('MMM').format(filteredData[index].date),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  );
                }
                return const Text('');
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
        barGroups: barGroups,
        extraLinesData: ExtraLinesData(
          horizontalLines: [
            HorizontalLine(
              y: _transmissionThreshold,
              color: Colors.orange,
              strokeWidth: 2,
              dashArray: [5, 5],
              label: HorizontalLineLabel(
                show: true,
                labelResolver: (line) => 'Transmission Threshold',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.orange,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
        maxY: filteredData.isNotEmpty
            ? filteredData.map((m) => m.rainfall).reduce((a, b) => a > b ? a : b) * 1.2
            : 200,
      ),
    );
  }

  /// Builds daily rainfall chart
  Widget _buildDailyChart() {
    final dailyData = widget.rainfallData.daily;

    if (dailyData.isEmpty) {
      return _buildNoDataMessage();
    }

    final filteredData = widget.dateRange != null
        ? dailyData.where((m) => widget.dateRange!.contains(m.date)).toList()
        : dailyData.take(90).toList(); // Limit to last 90 days for readability

    filteredData.sort((a, b) => a.date.compareTo(b.date));

    final spots = filteredData.asMap().entries.map((entry) {
      return FlSpot(entry.key.toDouble(), entry.value.rainfall);
    }).toList();

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
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) => Text(
                '${value.toStringAsFixed(0)}mm',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 40,
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index >= 0 && index < filteredData.length && index % 7 == 0) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      DateFormat('M/d').format(filteredData[index].date),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  );
                }
                return const Text('');
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
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: false,
            color: Colors.blue,
            barWidth: 1,
            isStrokeCapRound: false,
            dotData: FlDotData(
              show: filteredData.length < 30,
              getDotPainter: (spot, percent, barData, index) {
                return FlDotCirclePainter(
                  radius: 2,
                  color: Colors.blue,
                  strokeWidth: 1,
                  strokeColor: Theme.of(context).colorScheme.surface,
                );
              },
            ),
            belowBarData: BarAreaData(
              show: true,
              color: Colors.blue.withValues(alpha: 0.2),
            ),
          ),
        ],
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final index = spot.x.toInt();
                if (index >= 0 && index < filteredData.length) {
                  final measurement = filteredData[index];
                  return LineTooltipItem(
                    'Date: ${DateFormat('MMM d, yyyy').format(measurement.date)}\n'
                    'Rainfall: ${spot.y.toStringAsFixed(1)}mm\n'
                    'Quality: ${(measurement.quality * 100).toStringAsFixed(0)}%',
                    const TextStyle(
                      color: Colors.blue,
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
      ),
    );
  }

  /// Builds rainfall intensity distribution chart
  Widget _buildIntensityChart() {
    final intensityData = _calculateIntensityDistribution();

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
                final intensity = RainfallIntensity.values[value.toInt() % RainfallIntensity.values.length];
                return Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    _getIntensityDisplayName(intensity),
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
        barGroups: _buildIntensityBarGroups(intensityData),
        maxY: 100,
      ),
    );
  }

  /// Builds legend for the chart
  Widget _buildLegend() {
    switch (_currentViewMode) {
      case RainfallViewMode.seasonal:
        return _buildSeasonalLegend();
      case RainfallViewMode.monthly:
      case RainfallViewMode.daily:
        return _buildRainfallLegend();
      case RainfallViewMode.intensity:
        return _buildIntensityLegend();
    }
  }

  /// Builds seasonal legend
  Widget _buildSeasonalLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: Season.values.map((season) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _seasonColors[season],
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              _getSeasonDisplayName(season),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Builds rainfall level legend
  Widget _buildRainfallLegend() {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: const BoxDecoration(
            color: Colors.blue,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          'Rainfall (mm)',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(width: 16),
        Container(
          width: 20,
          height: 2,
          color: Colors.orange,
        ),
        const SizedBox(width: 4),
        Text(
          'Transmission Threshold (80mm)',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }

  /// Builds intensity legend
  Widget _buildIntensityLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: RainfallIntensity.values.map((intensity) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _intensityColors[intensity],
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              _getIntensityDisplayName(intensity),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Builds extreme events indicator
  Widget _buildExtremeEventsIndicator() {
    final extremeEvents = widget.rainfallData.extremeEvents
        .where((event) => event.type == ExtremeEventType.flood || event.type == ExtremeEventType.drought)
        .toList();

    if (extremeEvents.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.red.shade200),
      ),
      child: Row(
        children: [
          Icon(
            Icons.warning,
            color: Colors.red.shade600,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Extreme Events: ${extremeEvents.length} event(s) detected in period',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.red.shade800,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Calculates seasonal rainfall data
  Map<Season, double> _calculateSeasonalData() {
    final seasonalData = <Season, List<double>>{
      Season.spring: [],
      Season.summer: [],
      Season.autumn: [],
      Season.winter: [],
    };

    for (final measurement in widget.rainfallData.monthly) {
      final season = _getSeasonFromDate(measurement.date);
      seasonalData[season]?.add(measurement.rainfall);
    }

    return seasonalData.map((season, values) {
      final average = values.isEmpty ? 0.0 : values.reduce((a, b) => a + b) / values.length;
      return MapEntry(season, average);
    });
  }

  /// Calculates rainfall intensity distribution
  Map<RainfallIntensity, double> _calculateIntensityDistribution() {
    final totalDays = widget.rainfallData.daily.length;
    if (totalDays == 0) return {};

    final intensityCounts = <RainfallIntensity, int>{
      RainfallIntensity.light: 0,
      RainfallIntensity.moderate: 0,
      RainfallIntensity.heavy: 0,
      RainfallIntensity.extreme: 0,
    };

    for (final measurement in widget.rainfallData.daily) {
      final intensity = _getRainfallIntensity(measurement.rainfall);
      intensityCounts[intensity] = (intensityCounts[intensity] ?? 0) + 1;
    }

    return intensityCounts.map((intensity, count) {
      final percentage = (count / totalDays) * 100;
      return MapEntry(intensity, percentage);
    });
  }

  /// Builds seasonal bar groups
  List<BarChartGroupData> _buildSeasonalBarGroups(Map<Season, double> seasonalData) {
    final barGroups = <BarChartGroupData>[];

    Season.values.asMap().forEach((index, season) {
      final value = seasonalData[season] ?? 0.0;
      barGroups.add(
        BarChartGroupData(
          x: index,
          barRods: [
            BarChartRodData(
              toY: value,
              color: _seasonColors[season],
              width: 24,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
            ),
          ],
        ),
      );
    });

    return barGroups;
  }

  /// Builds intensity bar groups
  List<BarChartGroupData> _buildIntensityBarGroups(Map<RainfallIntensity, double> intensityData) {
    final barGroups = <BarChartGroupData>[];

    RainfallIntensity.values.asMap().forEach((index, intensity) {
      final value = intensityData[intensity] ?? 0.0;
      barGroups.add(
        BarChartGroupData(
          x: index,
          barRods: [
            BarChartRodData(
              toY: value,
              color: _intensityColors[intensity],
              width: 24,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
            ),
          ],
        ),
      );
    });

    return barGroups;
  }

  /// Gets season from date
  Season _getSeasonFromDate(DateTime date) {
    final month = date.month;
    if (month >= 3 && month <= 5) return Season.spring;
    if (month >= 6 && month <= 8) return Season.summer;
    if (month >= 9 && month <= 11) return Season.autumn;
    return Season.winter;
  }

  /// Gets rainfall intensity level
  RainfallIntensity _getRainfallIntensity(double rainfall) {
    if (rainfall < 10) return RainfallIntensity.light;
    if (rainfall < 50) return RainfallIntensity.moderate;
    if (rainfall < 100) return RainfallIntensity.heavy;
    return RainfallIntensity.extreme;
  }

  /// Gets rainfall color based on amount
  Color _getRainfallColor(double rainfall) {
    if (rainfall < 10) return Colors.lightBlue.shade200;
    if (rainfall < 50) return Colors.blue.shade400;
    if (rainfall < 100) return Colors.blue.shade700;
    return Colors.red.shade600;
  }

  /// Gets malaria transmission risk level from rainfall
  String _getRiskLevel(double rainfall) {
    if (rainfall < 80) return 'Low Risk';
    if (rainfall < 150) return 'Moderate Risk';
    if (rainfall < 250) return 'High Risk';
    return 'Critical Risk';
  }

  /// Gets maximum rainfall value from list
  double _getMaxRainfall(List<double> values) {
    if (values.isEmpty) return 200;
    return values.reduce((a, b) => a > b ? a : b);
  }

  /// Gets display name for view mode
  String _getViewModeDisplayName(RainfallViewMode mode) {
    switch (mode) {
      case RainfallViewMode.seasonal:
        return 'Seasonal';
      case RainfallViewMode.monthly:
        return 'Monthly';
      case RainfallViewMode.daily:
        return 'Daily';
      case RainfallViewMode.intensity:
        return 'Intensity';
    }
  }

  /// Gets display name for season
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

  /// Gets display name for rainfall intensity
  String _getIntensityDisplayName(RainfallIntensity intensity) {
    switch (intensity) {
      case RainfallIntensity.light:
        return 'Light\n(<10mm)';
      case RainfallIntensity.moderate:
        return 'Moderate\n(10-50mm)';
      case RainfallIntensity.heavy:
        return 'Heavy\n(50-100mm)';
      case RainfallIntensity.extreme:
        return 'Extreme\n(>100mm)';
    }
  }

  /// Checks if rainfall data is empty
  bool _isDataEmpty() {
    return widget.rainfallData.daily.isEmpty &&
           widget.rainfallData.monthly.isEmpty;
  }

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.water_drop_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No rainfall data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Rainfall patterns will appear here when data is loaded',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Shows rainfall analysis information dialog
  void _showRainfallInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rainfall Analysis Information'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Malaria Transmission Requirements:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Minimum: 80mm monthly rainfall'),
              Text('• Optimal: 150-250mm for peak transmission'),
              Text('• Peak Risk: 1-2 months post-rainfall'),
              SizedBox(height: 16),
              Text(
                'Rainfall Intensity Levels:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Light: <10mm (low breeding sites)'),
              Text('• Moderate: 10-50mm (moderate risk)'),
              Text('• Heavy: 50-100mm (high risk)'),
              Text('• Extreme: >100mm (flooding, delayed risk)'),
              SizedBox(height: 16),
              Text(
                'Seasonal Patterns:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('Regional rainfall patterns affect mosquito\nbreeding cycles and malaria transmission'),
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

/// Rainfall view mode enumeration
enum RainfallViewMode {
  seasonal,
  monthly,
  daily,
  intensity,
}

/// Rainfall intensity enumeration
enum RainfallIntensity {
  light,
  moderate,
  heavy,
  extreme,
}