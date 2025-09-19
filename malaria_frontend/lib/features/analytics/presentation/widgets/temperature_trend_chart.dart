/// Temperature trend chart widget using fl_chart for multi-series visualization
///
/// This widget displays comprehensive temperature trend data including daily mean,
/// minimum, maximum temperatures, and diurnal ranges using interactive line charts
/// with multiple series and correlation analysis capabilities.
///
/// Usage:
/// ```dart
/// TemperatureTrendChart(
///   temperatureData: temperatureData,
///   height: 400,
///   showAllSeries: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Temperature trend chart widget with multi-series line visualization
class TemperatureTrendChart extends StatefulWidget {
  /// Temperature data to display
  final TemperatureData temperatureData;

  /// Chart height
  final double height;

  /// Whether to show all temperature series or allow selection
  final bool showAllSeries;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Whether to show temperature anomalies
  final bool showAnomalies;

  /// Whether to enable correlation overlay
  final bool showCorrelation;

  /// Constructor requiring temperature data
  const TemperatureTrendChart({
    super.key,
    required this.temperatureData,
    this.height = 350,
    this.showAllSeries = true,
    this.dateRange,
    this.showAnomalies = false,
    this.showCorrelation = false,
  });

  @override
  State<TemperatureTrendChart> createState() => _TemperatureTrendChartState();
}

class _TemperatureTrendChartState extends State<TemperatureTrendChart> {
  /// Selected temperature series to display
  final Set<TemperatureSeries> _selectedSeries = {
    TemperatureSeries.dailyMean,
    TemperatureSeries.dailyMin,
    TemperatureSeries.dailyMax,
  };

  /// Color mapping for temperature series
  final Map<TemperatureSeries, Color> _seriesColors = {
    TemperatureSeries.dailyMean: Colors.orange,
    TemperatureSeries.dailyMin: Colors.blue,
    TemperatureSeries.dailyMax: Colors.red,
    TemperatureSeries.diurnalRange: Colors.purple,
  };

  /// Selected anomaly threshold for highlighting
  double _anomalyThreshold = 2;

  /// Whether to show moving average
  bool _showMovingAverage = false;

  /// Moving average window size in days
  final int _movingAverageWindow = 7;

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
            if (!widget.showAllSeries) _buildSeriesSelector(),
            if (widget.showAnomalies) _buildAnomalyControls(),
            if (!widget.showAllSeries || widget.showAnomalies) const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (widget.showCorrelation) _buildCorrelationIndicators(),
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
                'Temperature Trends Analysis',
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
            if (!widget.showAllSeries)
              IconButton(
                icon: Icon(
                  _showMovingAverage ? Icons.trending_up : Icons.trending_flat,
                  color: Theme.of(context).colorScheme.primary,
                ),
                onPressed: () {
                  setState(() {
                    _showMovingAverage = !_showMovingAverage;
                  });
                },
                tooltip: 'Toggle Moving Average',
              ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showTemperatureInfo(),
              tooltip: 'Temperature Analysis Info',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds temperature series selector chips
  Widget _buildSeriesSelector() {
    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: TemperatureSeries.values.map((series) {
        final isSelected = _selectedSeries.contains(series);
        return FilterChip(
          label: Text(_getSeriesDisplayName(series)),
          selected: isSelected,
          onSelected: (selected) {
            setState(() {
              if (selected) {
                _selectedSeries.add(series);
              } else {
                if (_selectedSeries.length > 1) {
                  _selectedSeries.remove(series);
                }
              }
            });
          },
          selectedColor: _seriesColors[series]?.withValues(alpha: 0.2),
          checkmarkColor: _seriesColors[series],
        );
      }).toList(),
    );
  }

  /// Builds anomaly detection controls
  Widget _buildAnomalyControls() {
    return Row(
      children: [
        Text(
          'Anomaly Threshold:',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 100,
          child: Slider(
            value: _anomalyThreshold,
            min: 1.0,
            max: 3.0,
            divisions: 8,
            label: '${_anomalyThreshold.toStringAsFixed(1)}σ',
            onChanged: (value) {
              setState(() {
                _anomalyThreshold = value;
              });
            },
          ),
        ),
        Text(
          '${_anomalyThreshold.toStringAsFixed(1)}σ',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  /// Builds the main temperature trends chart
  Widget _buildChart() {
    if (_isDataEmpty()) {
      return _buildNoDataMessage();
    }

    final seriesToShow = widget.showAllSeries
        ? TemperatureSeries.values.toSet()
        : _selectedSeries;

    final chartData = _prepareChartData(seriesToShow);

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
                '${value.toStringAsFixed(0)}°C',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 45,
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
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final series = _getSeriesFromBarIndex(spot.barIndex);
                final date = _getDateFromIndex(spot.x.toInt());
                if (date != null) {
                  return LineTooltipItem(
                    '${_getSeriesDisplayName(series)}\n'
                    'Date: ${DateFormat('MMM d, yyyy').format(date)}\n'
                    'Temperature: ${spot.y.toStringAsFixed(1)}°C',
                    TextStyle(
                      color: _seriesColors[series],
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
        minY: _getMinTemperature(chartData) - 2,
        maxY: _getMaxTemperature(chartData) + 2,
      ),
    );
  }

  /// Builds legend for temperature series
  Widget _buildLegend() {
    final seriesToShow = widget.showAllSeries
        ? TemperatureSeries.values.toSet()
        : _selectedSeries;

    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: seriesToShow.map((series) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _seriesColors[series],
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              _getSeriesDisplayName(series),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Builds correlation indicators if enabled
  Widget _buildCorrelationIndicators() {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildCorrelationIndicator(
            'Temp-Malaria Risk',
            0.73, // Mock correlation value
            Colors.red,
          ),
          _buildCorrelationIndicator(
            'Temp-Humidity',
            -0.45, // Mock correlation value
            Colors.blue,
          ),
          _buildCorrelationIndicator(
            'Diurnal-Transmission',
            0.62, // Mock correlation value
            Colors.purple,
          ),
        ],
      ),
    );
  }

  /// Builds individual correlation indicator
  Widget _buildCorrelationIndicator(String label, double correlation, Color color) {
    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontSize: 10,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 2),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            correlation.toStringAsFixed(2),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 11,
            ),
          ),
        ),
      ],
    );
  }

  /// Prepares chart data for visualization
  Map<TemperatureSeries, List<FlSpot>> _prepareChartData(Set<TemperatureSeries> series) {
    final chartData = <TemperatureSeries, List<FlSpot>>{};

    for (final seriesType in series) {
      final spots = <FlSpot>[];
      List<TemperatureMeasurement> measurements;

      switch (seriesType) {
        case TemperatureSeries.dailyMean:
          measurements = widget.temperatureData.dailyMean;
          break;
        case TemperatureSeries.dailyMin:
          measurements = widget.temperatureData.dailyMin;
          break;
        case TemperatureSeries.dailyMax:
          measurements = widget.temperatureData.dailyMax;
          break;
        case TemperatureSeries.diurnalRange:
          measurements = widget.temperatureData.diurnalRange;
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
        if (measurement.quality >= 0.5) {  // Filter low quality data
          spots.add(FlSpot(i.toDouble(), measurement.temperature));
        }
      }

      if (_showMovingAverage && spots.length > _movingAverageWindow) {
        spots.addAll(_calculateMovingAverage(spots, _movingAverageWindow));
      }

      if (spots.isNotEmpty) {
        chartData[seriesType] = spots;
      }
    }

    return chartData;
  }

  /// Calculates moving average for smoothing
  List<FlSpot> _calculateMovingAverage(List<FlSpot> spots, int window) {
    final movingAverageSpots = <FlSpot>[];

    for (int i = window; i < spots.length; i++) {
      double sum = 0;
      for (int j = i - window; j < i; j++) {
        sum += spots[j].y;
      }
      final average = sum / window;
      movingAverageSpots.add(FlSpot(spots[i].x, average));
    }

    return movingAverageSpots;
  }

  /// Builds line chart bars for each temperature series
  List<LineChartBarData> _buildLineChartBars(Map<TemperatureSeries, List<FlSpot>> chartData) {
    final lineBars = <LineChartBarData>[];

    chartData.forEach((series, spots) {
      lineBars.add(
        LineChartBarData(
          spots: spots,
          isCurved: true,
          color: _seriesColors[series],
          barWidth: series == TemperatureSeries.diurnalRange ? 3 : 2,
          isStrokeCapRound: true,
          dotData: FlDotData(
            show: spots.length < 50, // Only show dots for smaller datasets
            getDotPainter: (spot, percent, barData, index) {
              return FlDotCirclePainter(
                radius: 2,
                color: _seriesColors[series]!,
                strokeWidth: 1,
                strokeColor: Theme.of(context).colorScheme.surface,
              );
            },
          ),
          belowBarData: BarAreaData(
            show: series == TemperatureSeries.dailyMean,
            color: _seriesColors[series]?.withValues(alpha: 0.1),
          ),
        ),
      );
    });

    // Add anomaly markers if enabled
    if (widget.showAnomalies) {
      lineBars.addAll(_buildAnomalyMarkers());
    }

    return lineBars;
  }

  /// Builds anomaly markers for highlighting unusual temperatures
  List<LineChartBarData> _buildAnomalyMarkers() {
    final anomalyBars = <LineChartBarData>[];

    final significantAnomalies = widget.temperatureData.anomalies
        .where((anomaly) => anomaly.significance.abs() >= _anomalyThreshold)
        .toList();

    if (significantAnomalies.isNotEmpty) {
      final anomalySpots = significantAnomalies.map((anomaly) {
        final index = _getIndexFromDate(anomaly.date);
        return FlSpot(index.toDouble(), anomaly.observedTemperature);
      }).toList();

      anomalyBars.add(
        LineChartBarData(
          spots: anomalySpots,
          isCurved: false,
          color: Colors.transparent,
          barWidth: 0,
          dotData: FlDotData(
            show: true,
            getDotPainter: (spot, percent, barData, index) {
              return FlDotCirclePainter(
                radius: 6,
                color: Colors.red.withValues(alpha: 0.7),
                strokeWidth: 2,
                strokeColor: Colors.red,
              );
            },
          ),
        ),
      );
    }

    return anomalyBars;
  }

  /// Gets minimum temperature from chart data
  double _getMinTemperature(Map<TemperatureSeries, List<FlSpot>> chartData) {
    double min = double.infinity;
    chartData.values.forEach((spots) {
      for (final spot in spots) {
        if (spot.y < min) min = spot.y;
      }
    });
    return min == double.infinity ? 0 : min;
  }

  /// Gets maximum temperature from chart data
  double _getMaxTemperature(Map<TemperatureSeries, List<FlSpot>> chartData) {
    double max = double.negativeInfinity;
    chartData.values.forEach((spots) {
      for (final spot in spots) {
        if (spot.y > max) max = spot.y;
      }
    });
    return max == double.negativeInfinity ? 40 : max;
  }

  /// Gets date from chart index
  DateTime? _getDateFromIndex(int index) {
    final allMeasurements = <TemperatureMeasurement>[];
    allMeasurements.addAll(widget.temperatureData.dailyMean);
    allMeasurements.addAll(widget.temperatureData.dailyMin);
    allMeasurements.addAll(widget.temperatureData.dailyMax);

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

  /// Gets index from date
  int _getIndexFromDate(DateTime date) {
    final allMeasurements = <TemperatureMeasurement>[];
    allMeasurements.addAll(widget.temperatureData.dailyMean);

    final uniqueDates = allMeasurements
        .map((m) => m.date)
        .toSet()
        .toList();
    uniqueDates.sort();

    return uniqueDates.indexWhere((d) =>
      d.year == date.year &&
      d.month == date.month &&
      d.day == date.day
    );
  }

  /// Gets temperature series from bar index
  TemperatureSeries _getSeriesFromBarIndex(int barIndex) {
    final seriesToShow = widget.showAllSeries
        ? TemperatureSeries.values.toList()
        : _selectedSeries.toList();
    return seriesToShow[barIndex % seriesToShow.length];
  }

  /// Gets display name for temperature series
  String _getSeriesDisplayName(TemperatureSeries series) {
    switch (series) {
      case TemperatureSeries.dailyMean:
        return 'Daily Mean';
      case TemperatureSeries.dailyMin:
        return 'Daily Min';
      case TemperatureSeries.dailyMax:
        return 'Daily Max';
      case TemperatureSeries.diurnalRange:
        return 'Diurnal Range';
    }
  }

  /// Checks if temperature data is empty
  bool _isDataEmpty() {
    return widget.temperatureData.dailyMean.isEmpty &&
           widget.temperatureData.dailyMin.isEmpty &&
           widget.temperatureData.dailyMax.isEmpty &&
           widget.temperatureData.diurnalRange.isEmpty;
  }

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.thermostat_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No temperature data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Temperature trends will appear here when data is loaded',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Shows temperature analysis information dialog
  void _showTemperatureInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Temperature Analysis Information'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Temperature Metrics:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Daily Mean: Average temperature for each day'),
              Text('• Daily Min: Minimum temperature for each day'),
              Text('• Daily Max: Maximum temperature for each day'),
              Text('• Diurnal Range: Day-night temperature variation'),
              SizedBox(height: 16),
              Text(
                'Malaria Transmission Zones:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Optimal: 25°C (peak transmission)'),
              Text('• Suitable: 18-34°C (transmission possible)'),
              Text('• Limited: <16°C or >34°C (transmission stops)'),
              SizedBox(height: 16),
              Text(
                'Anomaly Detection:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('Red markers indicate temperatures significantly\ndifferent from historical norms'),
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

/// Temperature series enumeration for data selection
enum TemperatureSeries {
  dailyMean,
  dailyMin,
  dailyMax,
  diurnalRange,
}