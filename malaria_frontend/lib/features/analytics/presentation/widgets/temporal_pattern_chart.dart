/// Temporal pattern chart widget for outbreak pattern analysis
///
/// This widget displays temporal malaria outbreak patterns using time series
/// visualization to identify seasonal trends, outbreak cycles, and temporal
/// risk patterns for epidemiological analysis.
///
/// Usage:
/// ```dart
/// TemporalPatternChart(
///   riskTrends: riskTrends,
///   height: 400,
///   showTrendLines: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Temporal pattern chart widget with advanced time series analysis
class TemporalPatternChart extends StatefulWidget {
  /// Risk trend data to display
  final List<RiskTrend> riskTrends;

  /// Chart height
  final double height;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Whether to enable interactive features
  final bool enableInteractivity;

  /// Whether to show trend lines
  final bool showTrendLines;

  /// Whether to show seasonal patterns
  final bool showSeasonalPatterns;

  /// Chart aggregation period
  final TemporalAggregation aggregation;

  /// Constructor requiring risk trends data
  const TemporalPatternChart({
    super.key,
    required this.riskTrends,
    this.height = 350,
    this.dateRange,
    this.enableInteractivity = true,
    this.showTrendLines = true,
    this.showSeasonalPatterns = true,
    this.aggregation = TemporalAggregation.weekly,
  });

  @override
  State<TemporalPatternChart> createState() => _TemporalPatternChartState();
}

class _TemporalPatternChartState extends State<TemporalPatternChart> {
  /// Current temporal aggregation mode
  late TemporalAggregation _currentAggregation;

  /// Chart view mode
  TemporalViewMode _viewMode = TemporalViewMode.riskScore;

  /// Time series data points
  List<TemporalDataPoint> _timeSeriesData = [];

  /// Seasonal pattern data
  Map<int, SeasonalData> _seasonalData = {};

  /// Outbreak events detected
  List<OutbreakEvent> _outbreakEvents = [];

  /// Selected time period for detailed view
  DateRange? _selectedPeriod;

  /// Chart touch data
  FlTouchEvent? _lastTouchEvent;

  @override
  void initState() {
    super.initState();
    _currentAggregation = widget.aggregation;
    _processTemporalData();
  }

  @override
  void didUpdateWidget(TemporalPatternChart oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.riskTrends != widget.riskTrends ||
        oldWidget.dateRange != widget.dateRange) {
      _processTemporalData();
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
            _buildControls(),
            const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (_selectedPeriod != null) _buildSelectedPeriodInfo(),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header with title and key statistics
  Widget _buildHeader() {
    final outbreaks = _outbreakEvents.length;
    final peakRisk = _timeSeriesData.isNotEmpty
        ? _timeSeriesData.map((d) => d.riskScore).reduce(math.max)
        : 0.0;

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Temporal Outbreak Patterns',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '$outbreaks outbreak events detected • Peak risk: ${(peakRisk * 100).toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        if (widget.showSeasonalPatterns)
          IconButton(
            icon: Icon(
              Icons.calendar_view_month,
              color: Theme.of(context).colorScheme.primary,
            ),
            onPressed: () => _showSeasonalAnalysis(),
            tooltip: 'Seasonal Analysis',
          ),
        IconButton(
          icon: Icon(
            Icons.analytics,
            color: Theme.of(context).colorScheme.primary,
          ),
          onPressed: () => _showOutbreakAnalysis(),
          tooltip: 'Outbreak Analysis',
        ),
      ],
    );
  }

  /// Builds control panel for chart options
  Widget _buildControls() {
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
              children: [
                ...TemporalViewMode.values.map((mode) {
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
                            _processTemporalData();
                          });
                        }
                      },
                    ),
                  );
                }),
                const SizedBox(width: 16),
                Text(
                  'Period:',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(width: 8),
                DropdownButton<TemporalAggregation>(
                  value: _currentAggregation,
                  isDense: true,
                  items: TemporalAggregation.values.map((agg) {
                    return DropdownMenuItem<TemporalAggregation>(
                      value: agg,
                      child: Text(_getAggregationDisplayName(agg)),
                    );
                  }).toList(),
                  onChanged: (agg) {
                    if (agg != null) {
                      setState(() {
                        _currentAggregation = agg;
                        _processTemporalData();
                      });
                    }
                  },
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Builds the main temporal chart
  Widget _buildChart() {
    if (_timeSeriesData.isEmpty) {
      return _buildNoDataMessage();
    }

    return Padding(
      padding: const EdgeInsets.only(right: 16, top: 8),
      child: LineChart(
        LineChartData(
          gridData: FlGridData(
            show: true,
            drawVerticalLine: true,
            drawHorizontalLine: true,
            horizontalInterval: 0.2,
            verticalInterval: _getVerticalInterval(),
            getDrawingHorizontalLine: (value) => FlLine(
              color: Theme.of(context).dividerColor,
              strokeWidth: 1,
            ),
            getDrawingVerticalLine: (value) => FlLine(
              color: Theme.of(context).dividerColor,
              strokeWidth: 1,
            ),
          ),
          titlesData: FlTitlesData(
            show: true,
            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 30,
                interval: _getBottomInterval(),
                getTitlesWidget: _buildBottomTitle,
              ),
            ),
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 50,
                interval: 0.2,
                getTitlesWidget: _buildLeftTitle,
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
          lineBarsData: _buildLineBarsData(),
          lineTouchData: widget.enableInteractivity ? LineTouchData(
            enabled: true,
            touchCallback: (FlTouchEvent event, LineTouchResponse? response) {
              setState(() {
                _lastTouchEvent = event;
              });
              if (response?.lineBarSpots?.isNotEmpty == true) {
                final spot = response!.lineBarSpots!.first;
                final dataPoint = _timeSeriesData[spot.x.toInt()];
                _handleDataPointSelection(dataPoint);
              }
            },
            getTouchedSpotIndicator: (LineChartBarData barData, List<int> spotIndexes) {
              return spotIndexes.map((index) {
                return TouchedSpotIndicatorData(
                  FlLine(
                    color: Theme.of(context).colorScheme.primary,
                    strokeWidth: 2,
                  ),
                  FlDotData(
                    getDotPainter: (spot, percent, barData, index) {
                      return FlDotCirclePainter(
                        radius: 6,
                        color: Theme.of(context).colorScheme.primary,
                        strokeWidth: 2,
                        strokeColor: Colors.white,
                      );
                    },
                  ),
                );
              }).toList();
            },
            touchTooltipData: LineTouchTooltipData(
              getTooltipItems: _buildTooltipItems,
            ),
          ) : LineTouchData(enabled: false),
        ),
      ),
    );
  }

  /// Builds line chart data
  List<LineChartBarData> _buildLineBarsData() {
    final lines = <LineChartBarData>[];

    // Main risk trend line
    lines.add(
      LineChartBarData(
        spots: _timeSeriesData.asMap().entries.map((entry) {
          final index = entry.key;
          final data = entry.value;
          return FlSpot(index.toDouble(), _getYValue(data));
        }).toList(),
        isCurved: true,
        color: _getRiskTrendColor(),
        barWidth: 3,
        dotData: FlDotData(
          show: _timeSeriesData.length <= 50,
          getDotPainter: (spot, percent, barData, index) {
            final data = _timeSeriesData[index];
            return FlDotCirclePainter(
              radius: 4,
              color: _getRiskLevelColor(data.dominantRiskLevel),
              strokeWidth: 1,
              strokeColor: Colors.white,
            );
          },
        ),
        belowBarData: BarAreaData(
          show: true,
          color: _getRiskTrendColor().withValues(alpha: 0.1),
        ),
      ),
    );

    // Trend line if enabled
    if (widget.showTrendLines && _timeSeriesData.length > 3) {
      final trendLine = _calculateTrendLine();
      lines.add(
        LineChartBarData(
          spots: trendLine,
          isCurved: false,
          color: Colors.orange,
          barWidth: 2,
          dotData: const FlDotData(show: false),
          dashArray: [5, 5],
        ),
      );
    }

    // Outbreak events overlay
    if (_outbreakEvents.isNotEmpty) {
      lines.add(_buildOutbreakEventsLine());
    }

    return lines;
  }

  /// Builds outbreak events line overlay
  LineChartBarData _buildOutbreakEventsLine() {
    final spots = <FlSpot>[];

    for (final event in _outbreakEvents) {
      final index = _timeSeriesData.indexWhere((d) =>
          d.date.isAfter(event.startDate.subtract(const Duration(days: 1))) &&
          d.date.isBefore(event.endDate.add(const Duration(days: 1))));

      if (index >= 0) {
        spots.add(FlSpot(index.toDouble(), 1.0));
      }
    }

    return LineChartBarData(
      spots: spots,
      isCurved: false,
      color: Colors.red,
      barWidth: 4,
      dotData: FlDotData(
        show: true,
        getDotPainter: (spot, percent, barData, index) {
          return FlDotCirclePainter(
            radius: 8,
            color: Colors.red.withValues(alpha: 0.7),
            strokeWidth: 2,
            strokeColor: Colors.red,
          );
        },
      ),
    );
  }

  /// Builds chart legend
  Widget _buildLegend() {
    return Row(
      children: [
        _buildLegendItem('Risk Trend', _getRiskTrendColor(), isLine: true),
        const SizedBox(width: 16),
        if (widget.showTrendLines)
          _buildLegendItem('Trend Line', Colors.orange, isDashed: true),
        const SizedBox(width: 16),
        _buildLegendItem('Outbreak Events', Colors.red, isDot: true),
        const Spacer(),
        Text(
          'Aggregation: ${_getAggregationDisplayName(_currentAggregation)}',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
          ),
        ),
      ],
    );
  }

  /// Builds individual legend item
  Widget _buildLegendItem(String label, Color color, {bool isLine = false, bool isDashed = false, bool isDot = false}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 20,
          height: 12,
          child: CustomPaint(
            painter: LegendPainter(
              color: color,
              isLine: isLine,
              isDashed: isDashed,
              isDot: isDot,
            ),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }

  /// Builds selected period information panel
  Widget _buildSelectedPeriodInfo() {
    if (_selectedPeriod == null) return const SizedBox.shrink();

    final periodData = _timeSeriesData.where((d) =>
        _selectedPeriod!.contains(d.date)).toList();

    if (periodData.isEmpty) return const SizedBox.shrink();

    final avgRisk = periodData.map((d) => d.riskScore).reduce((a, b) => a + b) / periodData.length;
    final maxRisk = periodData.map((d) => d.riskScore).reduce(math.max);
    final totalPopulation = periodData.map((d) => d.populationAtRisk).reduce((a, b) => a + b);

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
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Average Risk: ${(avgRisk * 100).toStringAsFixed(1)}%',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      'Peak Risk: ${(maxRisk * 100).toStringAsFixed(1)}%',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      'Total Population: ${_formatPopulation(totalPopulation)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.timeline,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No temporal data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Processes risk trends into temporal data points
  void _processTemporalData() {
    final filteredTrends = _getFilteredRiskTrends();

    if (filteredTrends.isEmpty) {
      _timeSeriesData = [];
      _outbreakEvents = [];
      return;
    }

    // Group data by aggregation period
    final groupedData = <DateTime, List<RiskTrend>>{};

    for (final trend in filteredTrends) {
      final aggregatedDate = _getAggregatedDate(trend.date);
      groupedData.putIfAbsent(aggregatedDate, () => []).add(trend);
    }

    // Convert to temporal data points
    _timeSeriesData = groupedData.entries.map((entry) {
      final date = entry.key;
      final trends = entry.value;

      final avgRiskScore = trends.map((t) => t.riskScore).reduce((a, b) => a + b) / trends.length;
      final totalPopulation = trends.map((t) => t.populationAtRisk).reduce((a, b) => a + b);
      final avgConfidence = trends.map((t) => t.confidence).reduce((a, b) => a + b) / trends.length;

      // Determine dominant risk level
      final riskCounts = <RiskLevel, int>{};
      for (final trend in trends) {
        riskCounts[trend.riskLevel] = (riskCounts[trend.riskLevel] ?? 0) + 1;
      }
      final dominantRiskLevel = riskCounts.entries.reduce((a, b) => a.value > b.value ? a : b).key;

      return TemporalDataPoint(
        date: date,
        riskScore: avgRiskScore,
        populationAtRisk: totalPopulation,
        confidence: avgConfidence,
        dominantRiskLevel: dominantRiskLevel,
        dataPoints: trends.length,
      );
    }).toList();

    // Sort by date
    _timeSeriesData.sort((a, b) => a.date.compareTo(b.date));

    // Detect outbreak events
    _detectOutbreakEvents();

    // Calculate seasonal patterns if enabled
    if (widget.showSeasonalPatterns) {
      _calculateSeasonalPatterns();
    }
  }

  /// Detects outbreak events from temporal data
  void _detectOutbreakEvents() {
    _outbreakEvents = [];

    if (_timeSeriesData.length < 3) return;

    final riskThreshold = 0.7; // Threshold for outbreak detection
    final minDuration = 2; // Minimum data points for outbreak

    List<TemporalDataPoint> currentOutbreak = [];

    for (final dataPoint in _timeSeriesData) {
      if (dataPoint.riskScore >= riskThreshold) {
        currentOutbreak.add(dataPoint);
      } else {
        if (currentOutbreak.length >= minDuration) {
          _outbreakEvents.add(OutbreakEvent(
            startDate: currentOutbreak.first.date,
            endDate: currentOutbreak.last.date,
            peakRisk: currentOutbreak.map((d) => d.riskScore).reduce(math.max),
            totalPopulation: currentOutbreak.map((d) => d.populationAtRisk).reduce((a, b) => a + b),
            severity: _calculateOutbreakSeverity(currentOutbreak),
          ));
        }
        currentOutbreak = [];
      }
    }

    // Handle ongoing outbreak
    if (currentOutbreak.length >= minDuration) {
      _outbreakEvents.add(OutbreakEvent(
        startDate: currentOutbreak.first.date,
        endDate: currentOutbreak.last.date,
        peakRisk: currentOutbreak.map((d) => d.riskScore).reduce(math.max),
        totalPopulation: currentOutbreak.map((d) => d.populationAtRisk).reduce((a, b) => a + b),
        severity: _calculateOutbreakSeverity(currentOutbreak),
      ));
    }
  }

  /// Calculates seasonal patterns from temporal data
  void _calculateSeasonalPatterns() {
    _seasonalData = {};

    final seasonalGroups = <int, List<TemporalDataPoint>>{};

    for (final dataPoint in _timeSeriesData) {
      final month = dataPoint.date.month;
      seasonalGroups.putIfAbsent(month, () => []).add(dataPoint);
    }

    for (final entry in seasonalGroups.entries) {
      final month = entry.key;
      final dataPoints = entry.value;

      if (dataPoints.isNotEmpty) {
        final avgRisk = dataPoints.map((d) => d.riskScore).reduce((a, b) => a + b) / dataPoints.length;
        final maxRisk = dataPoints.map((d) => d.riskScore).reduce(math.max);
        final minRisk = dataPoints.map((d) => d.riskScore).reduce(math.min);

        _seasonalData[month] = SeasonalData(
          month: month,
          averageRisk: avgRisk,
          maxRisk: maxRisk,
          minRisk: minRisk,
          dataPointCount: dataPoints.length,
        );
      }
    }
  }

  /// Gets aggregated date based on current aggregation mode
  DateTime _getAggregatedDate(DateTime date) {
    switch (_currentAggregation) {
      case TemporalAggregation.daily:
        return DateTime(date.year, date.month, date.day);
      case TemporalAggregation.weekly:
        final weekday = date.weekday;
        return date.subtract(Duration(days: weekday - 1));
      case TemporalAggregation.monthly:
        return DateTime(date.year, date.month);
      case TemporalAggregation.quarterly:
        final quarter = ((date.month - 1) ~/ 3) * 3 + 1;
        return DateTime(date.year, quarter);
      case TemporalAggregation.yearly:
        return DateTime(date.year);
    }
  }

  /// Calculates outbreak severity
  OutbreakSeverity _calculateOutbreakSeverity(List<TemporalDataPoint> outbreakData) {
    final maxRisk = outbreakData.map((d) => d.riskScore).reduce(math.max);
    final duration = outbreakData.length;
    final totalPopulation = outbreakData.map((d) => d.populationAtRisk).reduce((a, b) => a + b);

    if (maxRisk >= 0.9 || totalPopulation > 100000) return OutbreakSeverity.critical;
    if (maxRisk >= 0.8 || totalPopulation > 50000) return OutbreakSeverity.high;
    if (maxRisk >= 0.7 || duration > 4) return OutbreakSeverity.medium;
    return OutbreakSeverity.low;
  }

  /// Calculates trend line using linear regression
  List<FlSpot> _calculateTrendLine() {
    if (_timeSeriesData.length < 2) return [];

    double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    final n = _timeSeriesData.length;

    for (int i = 0; i < n; i++) {
      final x = i.toDouble();
      final y = _getYValue(_timeSeriesData[i]);
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumX2 += x * x;
    }

    final slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    final intercept = (sumY - slope * sumX) / n;

    return [
      FlSpot(0, intercept),
      FlSpot(n - 1, slope * (n - 1) + intercept),
    ];
  }

  /// Gets Y value based on current view mode
  double _getYValue(TemporalDataPoint dataPoint) {
    switch (_viewMode) {
      case TemporalViewMode.riskScore:
        return dataPoint.riskScore;
      case TemporalViewMode.populationAtRisk:
        return dataPoint.populationAtRisk / 100000.0; // Scale for chart
      case TemporalViewMode.confidence:
        return dataPoint.confidence;
    }
  }

  /// Gets risk trend color based on view mode
  Color _getRiskTrendColor() {
    switch (_viewMode) {
      case TemporalViewMode.riskScore:
        return Colors.red;
      case TemporalViewMode.populationAtRisk:
        return Colors.blue;
      case TemporalViewMode.confidence:
        return Colors.green;
    }
  }

  /// Gets risk level color
  Color _getRiskLevelColor(RiskLevel level) {
    switch (level) {
      case RiskLevel.low:
        return Colors.green;
      case RiskLevel.medium:
        return Colors.yellow;
      case RiskLevel.high:
        return Colors.orange;
      case RiskLevel.critical:
        return Colors.red;
    }
  }

  /// Builds bottom title widget
  Widget _buildBottomTitle(double value, TitleMeta meta) {
    if (value.toInt() >= _timeSeriesData.length) return const Text('');

    final dataPoint = _timeSeriesData[value.toInt()];
    final formatter = _getDateFormatter();

    return SideTitleWidget(
      axisSide: meta.axisSide,
      child: Text(
        formatter.format(dataPoint.date),
        style: Theme.of(context).textTheme.bodySmall,
      ),
    );
  }

  /// Builds left title widget
  Widget _buildLeftTitle(double value, TitleMeta meta) {
    String text;
    switch (_viewMode) {
      case TemporalViewMode.riskScore:
        text = '${(value * 100).toStringAsFixed(0)}%';
        break;
      case TemporalViewMode.populationAtRisk:
        text = '${(value * 100).toStringAsFixed(0)}K';
        break;
      case TemporalViewMode.confidence:
        text = '${(value * 100).toStringAsFixed(0)}%';
        break;
    }

    return SideTitleWidget(
      axisSide: meta.axisSide,
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodySmall,
      ),
    );
  }

  /// Builds tooltip items for touch events
  List<LineTooltipItem> _buildTooltipItems(List<LineBarSpot> touchedSpots) {
    return touchedSpots.map((spot) {
      if (spot.x.toInt() >= _timeSeriesData.length) return null;

      final dataPoint = _timeSeriesData[spot.x.toInt()];
      final formatter = DateFormat('MMM dd, yyyy');

      return LineTooltipItem(
        '${formatter.format(dataPoint.date)}\n'
        '${_getViewModeDisplayName(_viewMode)}: ${_formatTooltipValue(dataPoint)}\n'
        'Population: ${_formatPopulation(dataPoint.populationAtRisk)}',
        TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      );
    }).whereType<LineTooltipItem>().toList();
  }

  /// Handles data point selection
  void _handleDataPointSelection(TemporalDataPoint dataPoint) {
    final startDate = dataPoint.date;
    final endDate = _getAggregationEndDate(startDate);

    setState(() {
      _selectedPeriod = DateRange(start: startDate, end: endDate);
    });
  }

  /// Gets end date for aggregation period
  DateTime _getAggregationEndDate(DateTime startDate) {
    switch (_currentAggregation) {
      case TemporalAggregation.daily:
        return startDate.add(const Duration(days: 1));
      case TemporalAggregation.weekly:
        return startDate.add(const Duration(days: 7));
      case TemporalAggregation.monthly:
        return DateTime(startDate.year, startDate.month + 1);
      case TemporalAggregation.quarterly:
        return DateTime(startDate.year, startDate.month + 3);
      case TemporalAggregation.yearly:
        return DateTime(startDate.year + 1);
    }
  }

  /// Gets date formatter based on aggregation
  DateFormat _getDateFormatter() {
    switch (_currentAggregation) {
      case TemporalAggregation.daily:
        return DateFormat('MM/dd');
      case TemporalAggregation.weekly:
        return DateFormat('MM/dd');
      case TemporalAggregation.monthly:
        return DateFormat('MMM');
      case TemporalAggregation.quarterly:
        return DateFormat('MMM yyyy');
      case TemporalAggregation.yearly:
        return DateFormat('yyyy');
    }
  }

  /// Gets filtered risk trends
  List<RiskTrend> _getFilteredRiskTrends() {
    if (widget.dateRange == null) return widget.riskTrends;
    return widget.riskTrends.where((trend) => widget.dateRange!.contains(trend.date)).toList();
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(TemporalViewMode mode) {
    switch (mode) {
      case TemporalViewMode.riskScore:
        return 'Risk Score';
      case TemporalViewMode.populationAtRisk:
        return 'Population';
      case TemporalViewMode.confidence:
        return 'Confidence';
    }
  }

  /// Gets aggregation display name
  String _getAggregationDisplayName(TemporalAggregation agg) {
    switch (agg) {
      case TemporalAggregation.daily:
        return 'Daily';
      case TemporalAggregation.weekly:
        return 'Weekly';
      case TemporalAggregation.monthly:
        return 'Monthly';
      case TemporalAggregation.quarterly:
        return 'Quarterly';
      case TemporalAggregation.yearly:
        return 'Yearly';
    }
  }

  /// Formats tooltip value based on view mode
  String _formatTooltipValue(TemporalDataPoint dataPoint) {
    switch (_viewMode) {
      case TemporalViewMode.riskScore:
        return '${(dataPoint.riskScore * 100).toStringAsFixed(1)}%';
      case TemporalViewMode.populationAtRisk:
        return _formatPopulation(dataPoint.populationAtRisk);
      case TemporalViewMode.confidence:
        return '${(dataPoint.confidence * 100).toStringAsFixed(1)}%';
    }
  }

  /// Formats population numbers
  String _formatPopulation(int population) {
    if (population >= 1000000) {
      return '${(population / 1000000).toStringAsFixed(1)}M';
    } else if (population >= 1000) {
      return '${(population / 1000).toStringAsFixed(1)}K';
    }
    return population.toString();
  }

  /// Gets vertical interval for grid
  double _getVerticalInterval() {
    if (_timeSeriesData.isEmpty) return 1.0;

    final maxDate = _timeSeriesData.last.date;
    final minDate = _timeSeriesData.first.date;
    final duration = maxDate.difference(minDate).inDays;

    if (duration <= 30) return 7.0; // Weekly intervals
    if (duration <= 90) return 30.0; // Monthly intervals
    return 90.0; // Quarterly intervals
  }

  /// Gets bottom interval for dates
  double _getBottomInterval() {
    final length = _timeSeriesData.length;
    if (length <= 10) return 1.0;
    if (length <= 30) return 3.0;
    if (length <= 100) return 10.0;
    return (length / 10).round().toDouble();
  }

  /// Shows seasonal analysis dialog
  void _showSeasonalAnalysis() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Seasonal Pattern Analysis'),
        content: SizedBox(
          width: 400,
          height: 300,
          child: _seasonalData.isEmpty
              ? const Center(child: Text('Insufficient data for seasonal analysis'))
              : SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: _seasonalData.entries.map((entry) {
                      final monthName = DateFormat('MMMM').format(DateTime(2024, entry.key));
                      final data = entry.value;

                      return ListTile(
                        title: Text(monthName),
                        subtitle: Text(
                          'Avg: ${(data.averageRisk * 100).toStringAsFixed(1)}% • '
                          'Range: ${(data.minRisk * 100).toStringAsFixed(1)}%-${(data.maxRisk * 100).toStringAsFixed(1)}%',
                        ),
                        trailing: Container(
                          width: 60,
                          height: 20,
                          decoration: BoxDecoration(
                            color: _getRiskLevelColor(_calculateRiskLevel(data.averageRisk)),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
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

  /// Shows outbreak analysis dialog
  void _showOutbreakAnalysis() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Outbreak Event Analysis'),
        content: SizedBox(
          width: 400,
          height: 300,
          child: _outbreakEvents.isEmpty
              ? const Center(child: Text('No outbreak events detected'))
              : SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: _outbreakEvents.asMap().entries.map((entry) {
                      final index = entry.key + 1;
                      final outbreak = entry.value;

                      return Card(
                        child: ListTile(
                          title: Text('Outbreak Event #$index'),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Duration: ${DateFormat('MMM dd').format(outbreak.startDate)} - ${DateFormat('MMM dd').format(outbreak.endDate)}'),
                              Text('Peak Risk: ${(outbreak.peakRisk * 100).toStringAsFixed(1)}%'),
                              Text('Population: ${_formatPopulation(outbreak.totalPopulation)}'),
                            ],
                          ),
                          trailing: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: _getOutbreakSeverityColor(outbreak.severity),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              outbreak.severity.name.toUpperCase(),
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
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

  /// Calculates risk level from risk score
  RiskLevel _calculateRiskLevel(double riskScore) {
    if (riskScore >= 0.8) return RiskLevel.critical;
    if (riskScore >= 0.6) return RiskLevel.high;
    if (riskScore >= 0.3) return RiskLevel.medium;
    return RiskLevel.low;
  }

  /// Gets outbreak severity color
  Color _getOutbreakSeverityColor(OutbreakSeverity severity) {
    switch (severity) {
      case OutbreakSeverity.low:
        return Colors.green;
      case OutbreakSeverity.medium:
        return Colors.orange;
      case OutbreakSeverity.high:
        return Colors.red;
      case OutbreakSeverity.critical:
        return Colors.purple;
    }
  }
}

/// Temporal view mode enumeration
enum TemporalViewMode {
  riskScore,
  populationAtRisk,
  confidence,
}

/// Temporal aggregation enumeration
enum TemporalAggregation {
  daily,
  weekly,
  monthly,
  quarterly,
  yearly,
}

/// Outbreak severity enumeration
enum OutbreakSeverity {
  low,
  medium,
  high,
  critical,
}

/// Temporal data point structure
class TemporalDataPoint {
  final DateTime date;
  final double riskScore;
  final int populationAtRisk;
  final double confidence;
  final RiskLevel dominantRiskLevel;
  final int dataPoints;

  const TemporalDataPoint({
    required this.date,
    required this.riskScore,
    required this.populationAtRisk,
    required this.confidence,
    required this.dominantRiskLevel,
    required this.dataPoints,
  });
}

/// Outbreak event structure
class OutbreakEvent {
  final DateTime startDate;
  final DateTime endDate;
  final double peakRisk;
  final int totalPopulation;
  final OutbreakSeverity severity;

  const OutbreakEvent({
    required this.startDate,
    required this.endDate,
    required this.peakRisk,
    required this.totalPopulation,
    required this.severity,
  });
}

/// Seasonal data structure
class SeasonalData {
  final int month;
  final double averageRisk;
  final double maxRisk;
  final double minRisk;
  final int dataPointCount;

  const SeasonalData({
    required this.month,
    required this.averageRisk,
    required this.maxRisk,
    required this.minRisk,
    required this.dataPointCount,
  });
}

/// Custom painter for legend items
class LegendPainter extends CustomPainter {
  final Color color;
  final bool isLine;
  final bool isDashed;
  final bool isDot;

  LegendPainter({
    required this.color,
    this.isLine = false,
    this.isDashed = false,
    this.isDot = false,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2;

    if (isDot) {
      paint.style = PaintingStyle.fill;
      canvas.drawCircle(
        Offset(size.width / 2, size.height / 2),
        4,
        paint,
      );
    } else if (isLine || isDashed) {
      paint.style = PaintingStyle.stroke;

      if (isDashed) {
        final dashPath = Path();
        const dashWidth = 4.0;
        const dashSpace = 3.0;
        double distance = 0.0;

        while (distance < size.width) {
          dashPath.moveTo(distance, size.height / 2);
          dashPath.lineTo(distance + dashWidth, size.height / 2);
          distance += dashWidth + dashSpace;
        }
        canvas.drawPath(dashPath, paint);
      } else {
        canvas.drawLine(
          Offset(0, size.height / 2),
          Offset(size.width, size.height / 2),
          paint,
        );
      }
    } else {
      paint.style = PaintingStyle.fill;
      canvas.drawRect(
        Rect.fromLTWH(0, 0, size.width, size.height),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}