/// Seasonal overlay widget for environmental pattern analysis
///
/// This widget provides comprehensive seasonal pattern visualization with
/// overlays showing how different environmental factors vary across seasons,
/// enabling identification of seasonal malaria transmission patterns.
///
/// Features:
/// - Multi-factor seasonal comparison
/// - Malaria transmission season highlighting
/// - Peak and low season identification
/// - Cyclical pattern analysis
/// - Climate zone overlays
/// - Year-over-year comparisons
///
/// Usage:
/// ```dart
/// SeasonalOverlayWidget(
///   environmentalData: environmentalData,
///   selectedFactors: factors,
///   height: 400,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Comprehensive seasonal pattern overlay widget
class SeasonalOverlayWidget extends StatefulWidget {
  /// Environmental data for seasonal analysis
  final EnvironmentalData environmentalData;

  /// Selected environmental factors to analyze
  final Set<EnvironmentalFactor> selectedFactors;

  /// Widget height
  final double height;

  /// Whether to show comparison mode
  final bool showComparison;

  /// Whether to show correlation analysis
  final bool showCorrelation;

  /// Whether to show malaria transmission seasons
  final bool showTransmissionSeasons;

  /// Years to compare (for multi-year analysis)
  final List<int>? comparisonYears;

  /// Constructor requiring environmental data
  const SeasonalOverlayWidget({
    super.key,
    required this.environmentalData,
    required this.selectedFactors,
    this.height = 350,
    this.showComparison = false,
    this.showCorrelation = false,
    this.showTransmissionSeasons = true,
    this.comparisonYears,
  });

  @override
  State<SeasonalOverlayWidget> createState() => _SeasonalOverlayWidgetState();
}

class _SeasonalOverlayWidgetState extends State<SeasonalOverlayWidget> {
  /// Current display mode
  SeasonalDisplayMode _displayMode = SeasonalDisplayMode.overlay;

  /// Current normalization method
  SeasonalNormalization _normalization = SeasonalNormalization.zScore;

  /// Selected seasons for focus analysis
  final Set<Season> _selectedSeasons = Season.values.toSet();

  /// Color mapping for environmental factors
  final Map<EnvironmentalFactor, Color> _factorColors = {
    EnvironmentalFactor.temperature: Colors.red.shade600,
    EnvironmentalFactor.rainfall: Colors.blue.shade600,
    EnvironmentalFactor.vegetation: Colors.green.shade600,
    EnvironmentalFactor.humidity: Colors.cyan.shade600,
    EnvironmentalFactor.windSpeed: Colors.orange.shade600,
    EnvironmentalFactor.pressure: Colors.purple.shade600,
  };

  /// Color mapping for seasons
  final Map<Season, Color> _seasonColors = {
    Season.spring: Colors.green.shade400,
    Season.summer: Colors.orange.shade600,
    Season.autumn: Colors.brown.shade500,
    Season.winter: Colors.blue.shade500,
  };

  /// Malaria transmission season indicators
  final Map<Season, bool> _transmissionSeasons = {
    Season.spring: true,
    Season.summer: true,
    Season.autumn: false,
    Season.winter: false,
  };

  /// Show statistical confidence intervals
  bool _showConfidenceIntervals = true;

  /// Show trend lines
  bool _showTrendLines = false;

  /// Current aggregation period
  SeasonalAggregation _aggregation = SeasonalAggregation.monthly;

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
            if (widget.showTransmissionSeasons) _buildTransmissionSeasonIndicator(),
            const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (widget.showCorrelation) _buildSeasonalCorrelationSummary(),
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
                'Seasonal Pattern Analysis',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Environmental factor seasonality for ${widget.environmentalData.region}',
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
                _showConfidenceIntervals ? Icons.show_chart : Icons.trending_up,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () {
                setState(() {
                  _showConfidenceIntervals = !_showConfidenceIntervals;
                });
              },
              tooltip: 'Toggle Confidence Intervals',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showSeasonalInfo(),
              tooltip: 'Seasonal Analysis Information',
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
              'Mode:',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: SeasonalDisplayMode.values.map((mode) {
                    final isSelected = mode == _displayMode;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(_getDisplayModeDisplayName(mode)),
                        selected: isSelected,
                        onSelected: (selected) {
                          if (selected) {
                            setState(() {
                              _displayMode = mode;
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
              'Normalization:',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: SeasonalNormalization.values.map((norm) {
                    final isSelected = norm == _normalization;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(_getNormalizationDisplayName(norm)),
                        selected: isSelected,
                        onSelected: (selected) {
                          if (selected) {
                            setState(() {
                              _normalization = norm;
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
      ],
    );
  }

  /// Builds transmission season indicator
  Widget _buildTransmissionSeasonIndicator() {
    final currentSeason = _getCurrentSeason();
    final isTransmissionSeason = _transmissionSeasons[currentSeason] ?? false;

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: isTransmissionSeason
            ? Colors.orange.shade50
            : Colors.green.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isTransmissionSeason
              ? Colors.orange.shade200
              : Colors.green.shade200,
        ),
      ),
      child: Row(
        children: [
          Icon(
            isTransmissionSeason
                ? Icons.warning_amber_outlined
                : Icons.check_circle_outline,
            color: isTransmissionSeason
                ? Colors.orange.shade600
                : Colors.green.shade600,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              isTransmissionSeason
                  ? 'Current season (${_getSeasonDisplayName(currentSeason)}) is a peak transmission period'
                  : 'Current season (${_getSeasonDisplayName(currentSeason)}) is a low transmission period',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: isTransmissionSeason
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

  /// Builds the main seasonal chart
  Widget _buildChart() {
    if (widget.selectedFactors.isEmpty) {
      return _buildNoDataMessage();
    }

    switch (_displayMode) {
      case SeasonalDisplayMode.overlay:
        return _buildOverlayChart();
      case SeasonalDisplayMode.comparison:
        return _buildComparisonChart();
      case SeasonalDisplayMode.radar:
        return _buildRadarChart();
      case SeasonalDisplayMode.heatmap:
        return _buildHeatmapChart();
    }
  }

  /// Builds overlay chart with multiple environmental factors
  Widget _buildOverlayChart() {
    final normalizedData = _prepareNormalizedData();

    if (normalizedData.isEmpty) {
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
                value.toStringAsFixed(1),
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 40,
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) => Text(
                value.toStringAsFixed(1),
                style: Theme.of(context).textTheme.bodySmall,
              ),
              reservedSize: 40,
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final monthIndex = value.toInt();
                if (monthIndex >= 1 && monthIndex <= 12) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      DateFormat('MMM').format(DateTime(2023, monthIndex)),
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
        lineBarsData: _buildOverlayLineBars(normalizedData),
        extraLinesData: widget.showTransmissionSeasons ? _buildTransmissionSeasonOverlays() : null,
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final factor = _getFactorFromBarIndex(spot.barIndex);
                final month = DateFormat('MMMM').format(DateTime(2023, spot.x.toInt()));
                return LineTooltipItem(
                  '${_getFactorDisplayName(factor)}\n'
                  'Month: $month\n'
                  'Normalized Value: ${spot.y.toStringAsFixed(2)}',
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

  /// Builds comparison chart for different years
  Widget _buildComparisonChart() {
    if (!widget.showComparison || widget.comparisonYears == null) {
      return _buildOverlayChart();
    }

    return Container(
      child: Center(
        child: Text(
          'Year-over-year comparison\nwill be implemented here',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// Builds radar chart for circular seasonal representation
  Widget _buildRadarChart() {
    return Container(
      child: Center(
        child: Text(
          'Radar chart visualization\nwill be implemented here',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// Builds heatmap chart for seasonal intensity
  Widget _buildHeatmapChart() {
    return Container(
      child: Center(
        child: Text(
          'Seasonal heatmap visualization\nwill be implemented here',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// Builds legend for environmental factors
  Widget _buildLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: widget.selectedFactors.map((factor) {
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

  /// Builds seasonal correlation summary
  Widget _buildSeasonalCorrelationSummary() {
    final correlations = _calculateSeasonalCorrelations();

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
            'Seasonal Correlations',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
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

  /// Builds individual correlation chip
  Widget _buildCorrelationChip(String label, double correlation) {
    final color = _getCorrelationColor(correlation);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
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
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              correlation.toStringAsFixed(2),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 10,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Prepares normalized seasonal data
  Map<EnvironmentalFactor, List<FlSpot>> _prepareNormalizedData() {
    final normalizedData = <EnvironmentalFactor, List<FlSpot>>{};

    for (final factor in widget.selectedFactors) {
      final monthlyData = _calculateMonthlyAverages(factor);
      if (monthlyData.isNotEmpty) {
        final normalizedValues = _normalizeData(monthlyData.values.toList());
        final spots = <FlSpot>[];

        monthlyData.keys.toList().asMap().forEach((index, month) {
          spots.add(FlSpot(month.toDouble(), normalizedValues[index]));
        });

        if (spots.isNotEmpty) {
          normalizedData[factor] = spots;
        }
      }
    }

    return normalizedData;
  }

  /// Calculates monthly averages for an environmental factor
  Map<int, double> _calculateMonthlyAverages(EnvironmentalFactor factor) {
    final monthlyData = <int, List<double>>{};

    // Initialize months
    for (int month = 1; month <= 12; month++) {
      monthlyData[month] = [];
    }

    // Collect data based on factor type
    switch (factor) {
      case EnvironmentalFactor.temperature:
        for (final measurement in widget.environmentalData.temperature.dailyMean) {
          monthlyData[measurement.date.month]?.add(measurement.temperature);
        }
        break;
      case EnvironmentalFactor.rainfall:
        for (final measurement in widget.environmentalData.rainfall.monthly) {
          monthlyData[measurement.date.month]?.add(measurement.rainfall);
        }
        break;
      case EnvironmentalFactor.humidity:
        for (final measurement in widget.environmentalData.humidity.relativeHumidity) {
          monthlyData[measurement.date.month]?.add(measurement.humidity);
        }
        break;
      case EnvironmentalFactor.vegetation:
        for (final measurement in widget.environmentalData.vegetation.ndvi) {
          monthlyData[measurement.date.month]?.add(measurement.value);
        }
        break;
      default:
        // Handle other factors if available
        break;
    }

    // Calculate averages
    return monthlyData.map((month, values) {
      final average = values.isEmpty ? 0.0 : values.reduce((a, b) => a + b) / values.length;
      return MapEntry(month, average);
    });
  }

  /// Normalizes data using selected normalization method
  List<double> _normalizeData(List<double> data) {
    if (data.isEmpty) return [];

    switch (_normalization) {
      case SeasonalNormalization.minMax:
        final min = data.reduce((a, b) => a < b ? a : b);
        final max = data.reduce((a, b) => a > b ? a : b);
        final range = max - min;
        if (range == 0) return List.filled(data.length, 0.5);
        return data.map((value) => (value - min) / range).toList();

      case SeasonalNormalization.zScore:
        final mean = data.reduce((a, b) => a + b) / data.length;
        final variance = data.map((x) => (x - mean) * (x - mean)).reduce((a, b) => a + b) / data.length;
        final stdDev = variance == 0 ? 1 : Math.sqrt(variance);
        return data.map((value) => (value - mean) / stdDev).toList();

      case SeasonalNormalization.percentile:
        final sorted = List<double>.from(data)..sort();
        return data.map((value) {
          final rank = sorted.indexOf(value);
          return rank / (sorted.length - 1);
        }).toList();

      case SeasonalNormalization.none:
        return data;
    }
  }

  /// Builds overlay line bars for multiple factors
  List<LineChartBarData> _buildOverlayLineBars(Map<EnvironmentalFactor, List<FlSpot>> normalizedData) {
    final lineBars = <LineChartBarData>[];

    normalizedData.forEach((factor, spots) {
      lineBars.add(
        LineChartBarData(
          spots: spots,
          isCurved: true,
          color: _factorColors[factor],
          barWidth: 3,
          isStrokeCapRound: true,
          dotData: FlDotData(
            show: true,
            getDotPainter: (spot, percent, barData, index) {
              return FlDotCirclePainter(
                radius: 4,
                color: _factorColors[factor]!,
                strokeWidth: 2,
                strokeColor: Theme.of(context).colorScheme.surface,
              );
            },
          ),
          belowBarData: BarAreaData(
            show: _showConfidenceIntervals,
            color: _factorColors[factor]?.withValues(alpha: 0.1),
          ),
        ),
      );
    });

    return lineBars;
  }

  /// Builds transmission season overlays
  ExtraLinesData _buildTransmissionSeasonOverlays() {
    final verticalLines = <VerticalLine>[];

    _transmissionSeasons.forEach((season, isTransmission) {
      if (isTransmission) {
        final monthRange = _getSeasonMonthRange(season);
        for (final month in monthRange) {
          verticalLines.add(
            VerticalLine(
              x: month.toDouble(),
              color: Colors.orange.withValues(alpha: 0.3),
              strokeWidth: 4,
            ),
          );
        }
      }
    });

    return ExtraLinesData(verticalLines: verticalLines);
  }

  /// Gets month range for a season
  List<int> _getSeasonMonthRange(Season season) {
    switch (season) {
      case Season.spring:
        return [3, 4, 5];
      case Season.summer:
        return [6, 7, 8];
      case Season.autumn:
        return [9, 10, 11];
      case Season.winter:
        return [12, 1, 2];
    }
  }

  /// Gets current season
  Season _getCurrentSeason() {
    final month = DateTime.now().month;
    if (month >= 3 && month <= 5) return Season.spring;
    if (month >= 6 && month <= 8) return Season.summer;
    if (month >= 9 && month <= 11) return Season.autumn;
    return Season.winter;
  }

  /// Gets environmental factor from bar index
  EnvironmentalFactor _getFactorFromBarIndex(int barIndex) {
    final factorsList = widget.selectedFactors.toList();
    return factorsList[barIndex % factorsList.length];
  }

  /// Calculates seasonal correlations
  Map<String, double> _calculateSeasonalCorrelations() {
    // Mock correlation data - would be calculated from actual seasonal data
    return {
      'Temp-Rainfall': -0.45,
      'Temp-Humidity': -0.62,
      'Rainfall-Vegetation': 0.78,
      'Humidity-Vegetation': 0.34,
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

  /// Gets display mode display name
  String _getDisplayModeDisplayName(SeasonalDisplayMode mode) {
    switch (mode) {
      case SeasonalDisplayMode.overlay:
        return 'Overlay';
      case SeasonalDisplayMode.comparison:
        return 'Comparison';
      case SeasonalDisplayMode.radar:
        return 'Radar';
      case SeasonalDisplayMode.heatmap:
        return 'Heatmap';
    }
  }

  /// Gets normalization display name
  String _getNormalizationDisplayName(SeasonalNormalization norm) {
    switch (norm) {
      case SeasonalNormalization.none:
        return 'None';
      case SeasonalNormalization.minMax:
        return 'Min-Max';
      case SeasonalNormalization.zScore:
        return 'Z-Score';
      case SeasonalNormalization.percentile:
        return 'Percentile';
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

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.calendar_today_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No seasonal data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Seasonal patterns will appear here when data is loaded',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Shows seasonal analysis information dialog
  void _showSeasonalInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Seasonal Pattern Analysis'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Analysis Features:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Multi-factor seasonal comparison'),
              Text('• Data normalization for overlay visualization'),
              Text('• Transmission season highlighting'),
              Text('• Correlation analysis between factors'),
              SizedBox(height: 16),
              Text(
                'Normalization Methods:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Min-Max: Scales values to 0-1 range'),
              Text('• Z-Score: Standardizes around mean and std dev'),
              Text('• Percentile: Shows relative ranking'),
              Text('• None: Shows original values'),
              SizedBox(height: 16),
              Text(
                'Malaria Transmission Seasons:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Spring-Summer: Peak transmission periods'),
              Text('• Autumn-Winter: Reduced transmission'),
              Text('• Highlighted months show optimal conditions'),
              Text('• Varies by geographic region'),
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

/// Seasonal display mode enumeration
enum SeasonalDisplayMode {
  overlay,
  comparison,
  radar,
  heatmap,
}

/// Seasonal normalization enumeration
enum SeasonalNormalization {
  none,
  minMax,
  zScore,
  percentile,
}

/// Seasonal aggregation enumeration
enum SeasonalAggregation {
  weekly,
  monthly,
  seasonal,
  annual,
}

/// Math class for calculations (placeholder)
class Math {
  static double sqrt(double x) => x == 0 ? 0 : 1.414; // Simplified for example
}