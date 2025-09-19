/// Environmental trends chart widget using fl_chart
///
/// This widget displays environmental trend data including temperature,
/// rainfall, vegetation, and other climate factors using interactive line charts.
///
/// Usage:
/// ```dart
/// EnvironmentalTrendsChart(
///   environmentalTrends: environmentalData,
///   height: 400,
/// );
/// ```

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Environmental trends chart widget
class EnvironmentalTrendsChart extends StatefulWidget {
  /// Environmental trend data to display
  final List<EnvironmentalTrend> environmentalTrends;

  /// Chart height
  final double height;

  /// Whether to show all factors or allow selection
  final bool showAllFactors;

  /// Constructor requiring environmental trends data
  const EnvironmentalTrendsChart({
    super.key,
    required this.environmentalTrends,
    this.height = 300,
    this.showAllFactors = true,
  });

  @override
  State<EnvironmentalTrendsChart> createState() => _EnvironmentalTrendsChartState();
}

class _EnvironmentalTrendsChartState extends State<EnvironmentalTrendsChart> {
  /// Selected environmental factors to display
  Set<EnvironmentalFactor> _selectedFactors = {
    EnvironmentalFactor.temperature,
    EnvironmentalFactor.rainfall,
    EnvironmentalFactor.vegetation,
  };

  /// Color mapping for environmental factors
  final Map<EnvironmentalFactor, Color> _factorColors = {
    EnvironmentalFactor.temperature: Colors.red,
    EnvironmentalFactor.rainfall: Colors.blue,
    EnvironmentalFactor.vegetation: Colors.green,
    EnvironmentalFactor.humidity: Colors.cyan,
    EnvironmentalFactor.windSpeed: Colors.orange,
    EnvironmentalFactor.pressure: Colors.purple,
  };

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
            const SizedBox(height: 16),
            if (!widget.showAllFactors) _buildFactorSelector(),
            if (!widget.showAllFactors) const SizedBox(height: 16),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header
  Widget _buildHeader() {
    return Text(
      'Environmental Trends',
      style: Theme.of(context).textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.bold,
      ),
    );
  }

  /// Builds factor selector chips
  Widget _buildFactorSelector() {
    return Wrap(
      spacing: 8,
      children: EnvironmentalFactor.values.map((factor) {
        final isSelected = _selectedFactors.contains(factor);
        return FilterChip(
          label: Text(_getFactorDisplayName(factor)),
          selected: isSelected,
          onSelected: (selected) {
            setState(() {
              if (selected) {
                _selectedFactors.add(factor);
              } else {
                _selectedFactors.remove(factor);
              }
            });
          },
          selectedColor: _factorColors[factor]?.withValues(alpha:0.2),
          checkmarkColor: _factorColors[factor],
        );
      }).toList(),
    );
  }

  /// Builds the main environmental trends chart
  Widget _buildChart() {
    if (widget.environmentalTrends.isEmpty) {
      return _buildNoDataMessage();
    }

    final factorsToShow = widget.showAllFactors
        ? EnvironmentalFactor.values.toSet()
        : _selectedFactors;

    final groupedData = _groupDataByFactor(factorsToShow);

    if (groupedData.isEmpty) {
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
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
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
                final index = value.toInt();
                final dates = _getAllDates();
                if (index >= 0 && index < dates.length) {
                  return Text(
                    DateFormat('MMM d').format(dates[index]),
                    style: Theme.of(context).textTheme.bodySmall,
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
        lineBarsData: _buildLineChartBars(groupedData),
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final factor = _getFactorFromLineIndex(spot.barIndex);
                final date = _getDateFromSpotIndex(spot.x.toInt());
                return LineTooltipItem(
                  '${_getFactorDisplayName(factor)}\n'
                  'Date: ${DateFormat('MMM d').format(date)}\n'
                  'Value: ${spot.y.toStringAsFixed(1)}',
                  TextStyle(
                    color: _factorColors[factor],
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                );
              }).toList();
            },
          ),
        ),
      ),
    );
  }

  /// Builds legend for environmental factors
  Widget _buildLegend() {
    final factorsToShow = widget.showAllFactors
        ? EnvironmentalFactor.values.toSet()
        : _selectedFactors;

    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: factorsToShow.map((factor) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _factorColors[factor],
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              _getFactorDisplayName(factor),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Groups environmental data by factor
  Map<EnvironmentalFactor, List<EnvironmentalTrend>> _groupDataByFactor(
    Set<EnvironmentalFactor> factors,
  ) {
    final groupedData = <EnvironmentalFactor, List<EnvironmentalTrend>>{};

    for (final factor in factors) {
      final factorData = widget.environmentalTrends
          .where((trend) => trend.factor == factor)
          .toList();

      if (factorData.isNotEmpty) {
        factorData.sort((a, b) => a.date.compareTo(b.date));
        groupedData[factor] = factorData;
      }
    }

    return groupedData;
  }

  /// Builds line chart bars for each environmental factor
  List<LineChartBarData> _buildLineChartBars(
    Map<EnvironmentalFactor, List<EnvironmentalTrend>> groupedData,
  ) {
    final allDates = _getAllDates();
    final lineBars = <LineChartBarData>[];

    groupedData.forEach((factor, trends) {
      final spots = <FlSpot>[];

      for (int i = 0; i < allDates.length; i++) {
        final date = allDates[i];
        final trend = trends.where((t) =>
          t.date.year == date.year &&
          t.date.month == date.month &&
          t.date.day == date.day
        ).firstOrNull;

        if (trend != null) {
          spots.add(FlSpot(i.toDouble(), trend.value));
        }
      }

      if (spots.isNotEmpty) {
        lineBars.add(
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: _factorColors[factor],
            barWidth: 2,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, percent, barData, index) {
                return FlDotCirclePainter(
                  radius: 3,
                  color: _factorColors[factor]!,
                  strokeWidth: 1,
                  strokeColor: Theme.of(context).colorScheme.surface,
                );
              },
            ),
          ),
        );
      }
    });

    return lineBars;
  }

  /// Gets all unique dates from environmental trends
  List<DateTime> _getAllDates() {
    final dates = widget.environmentalTrends
        .map((trend) => DateTime(trend.date.year, trend.date.month, trend.date.day))
        .toSet()
        .toList();

    dates.sort();
    return dates;
  }

  /// Gets environmental factor from line chart bar index
  EnvironmentalFactor _getFactorFromLineIndex(int lineIndex) {
    final factorsToShow = widget.showAllFactors
        ? EnvironmentalFactor.values.toSet()
        : _selectedFactors;

    final factorsList = factorsToShow.toList();
    return factorsList[lineIndex % factorsList.length];
  }

  /// Gets date from spot index
  DateTime _getDateFromSpotIndex(int spotIndex) {
    final dates = _getAllDates();
    return dates[spotIndex % dates.length];
  }

  /// Gets display name for environmental factor
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

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.eco_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha:0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No environmental data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha:0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}