/// Vegetation index chart widget for NDVI and EVI analysis
///
/// This widget provides comprehensive vegetation index visualization including
/// NDVI (Normalized Difference Vegetation Index) and EVI (Enhanced Vegetation Index)
/// analysis with land cover distribution and seasonal patterns for malaria
/// prediction analytics.
///
/// Features:
/// - NDVI and EVI trend visualization
/// - Land cover type distribution
/// - Seasonal vegetation patterns
/// - Breeding habitat indicators
/// - Vegetation health assessment
/// - Scientific index scaling (-1 to +1)
///
/// Usage:
/// ```dart
/// VegetationIndexChart(
///   vegetationData: vegetationData,
///   height: 400,
///   showLandCover: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Comprehensive vegetation index chart widget
class VegetationIndexChart extends StatefulWidget {
  /// Vegetation data to display
  final VegetationData vegetationData;

  /// Chart height
  final double height;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Whether to show land cover distribution
  final bool showLandCover;

  /// Whether to show breeding habitat indicators
  final bool showBreedingHabitats;

  /// Whether to show seasonal patterns
  final bool showSeasonalPatterns;

  /// Vegetation indices to display
  final Set<VegetationIndex> displayIndices;

  /// Constructor requiring vegetation data
  const VegetationIndexChart({
    super.key,
    required this.vegetationData,
    this.height = 350,
    this.dateRange,
    this.showLandCover = true,
    this.showBreedingHabitats = true,
    this.showSeasonalPatterns = true,
    this.displayIndices = const {
      VegetationIndex.ndvi,
      VegetationIndex.evi,
    },
  });

  @override
  State<VegetationIndexChart> createState() => _VegetationIndexChartState();
}

class _VegetationIndexChartState extends State<VegetationIndexChart> {
  /// Current vegetation view mode
  VegetationViewMode _viewMode = VegetationViewMode.timeSeries;

  /// Selected vegetation indices to display
  late Set<VegetationIndex> _selectedIndices;

  /// Color mapping for vegetation indices
  final Map<VegetationIndex, Color> _indexColors = {
    VegetationIndex.ndvi: Colors.green.shade700,
    VegetationIndex.evi: Colors.teal.shade600,
  };

  /// Color mapping for land cover types
  final Map<LandCoverType, Color> _landCoverColors = {
    LandCoverType.forest: Colors.green.shade800,
    LandCoverType.grassland: Colors.lightGreen.shade600,
    LandCoverType.cropland: Colors.yellow.shade700,
    LandCoverType.urban: Colors.grey.shade600,
    LandCoverType.water: Colors.blue.shade600,
    LandCoverType.bareland: Colors.brown.shade400,
    LandCoverType.wetland: Colors.blue.shade800,
  };

  /// Vegetation health thresholds
  static const double _healthyVegetationThreshold = 0.4; // NDVI > 0.4 indicates healthy vegetation
  static const double _sparseVegetationThreshold = 0.2; // NDVI 0.2-0.4 indicates sparse vegetation
  static const double _bareGroundThreshold = 0.1; // NDVI < 0.1 indicates bare ground/water

  /// Show vegetation health zones
  bool _showHealthZones = true;

  /// Show data quality indicators
  bool _showDataQuality = true;

  /// Current aggregation level
  VegetationAggregation _aggregation = VegetationAggregation.monthly;

  @override
  void initState() {
    super.initState();
    _selectedIndices = Set.from(widget.displayIndices);
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
            if (widget.showBreedingHabitats) _buildBreedingHabitatAlert(),
            const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (widget.showLandCover) _buildLandCoverSummary(),
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
                'Vegetation Index Analysis',
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
                _showHealthZones ? Icons.eco : Icons.eco_outlined,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () {
                setState(() {
                  _showHealthZones = !_showHealthZones;
                });
              },
              tooltip: 'Toggle Vegetation Health Zones',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showVegetationInfo(),
              tooltip: 'Vegetation Analysis Information',
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
                  children: VegetationViewMode.values.map((mode) {
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
              'Indices:',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Wrap(
                spacing: 8,
                runSpacing: 4,
                children: VegetationIndex.values.map((index) {
                  final isSelected = _selectedIndices.contains(index);
                  return FilterChip(
                    label: Text(_getIndexDisplayName(index)),
                    selected: isSelected,
                    onSelected: (selected) {
                      setState(() {
                        if (selected) {
                          _selectedIndices.add(index);
                        } else if (_selectedIndices.length > 1) {
                          _selectedIndices.remove(index);
                        }
                      });
                    },
                    selectedColor: _indexColors[index]?.withValues(alpha: 0.2),
                    checkmarkColor: _indexColors[index],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds breeding habitat alert panel
  Widget _buildBreedingHabitatAlert() {
    final currentNDVI = _getCurrentNDVIValue();
    final suitableForBreeding = currentNDVI >= _sparseVegetationThreshold &&
                               currentNDVI <= _healthyVegetationThreshold;

    if (!suitableForBreeding) return const SizedBox.shrink();

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
              'Suitable vegetation density for mosquito breeding (NDVI: ${currentNDVI.toStringAsFixed(2)})',
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

  /// Builds the main vegetation chart
  Widget _buildChart() {
    if (_isDataEmpty()) {
      return _buildNoDataMessage();
    }

    switch (_viewMode) {
      case VegetationViewMode.timeSeries:
        return _buildTimeSeriesChart();
      case VegetationViewMode.seasonal:
        return _buildSeasonalChart();
      case VegetationViewMode.landCover:
        return _buildLandCoverChart();
      case VegetationViewMode.health:
        return _buildHealthAssessmentChart();
    }
  }

  /// Builds time series vegetation index chart
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
        extraLinesData: _showHealthZones ? _buildHealthZones() : null,
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final index = _getIndexFromBarIndex(spot.barIndex);
                final date = _getDateFromIndex(spot.x.toInt());
                if (date != null) {
                  return LineTooltipItem(
                    '${_getIndexDisplayName(index)}\n'
                    'Date: ${DateFormat('MMM d, yyyy').format(date)}\n'
                    'Value: ${spot.y.toStringAsFixed(3)}\n'
                    'Health: ${_getVegetationHealth(spot.y)}',
                    TextStyle(
                      color: _indexColors[index],
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
        minY: -0.5,
        maxY: 1.0,
      ),
    );
  }

  /// Builds seasonal vegetation pattern chart
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
        extraLinesData: _showHealthZones
            ? ExtraLinesData(
                horizontalLines: [
                  HorizontalLine(
                    y: _healthyVegetationThreshold,
                    color: Colors.green,
                    strokeWidth: 2,
                    dashArray: [5, 5],
                  ),
                  HorizontalLine(
                    y: _sparseVegetationThreshold,
                    color: Colors.orange,
                    strokeWidth: 2,
                    dashArray: [5, 5],
                  ),
                ],
              )
            : null,
        maxY: 1.0,
        minY: -0.1,
      ),
    );
  }

  /// Builds land cover distribution chart
  Widget _buildLandCoverChart() {
    final landCoverData = widget.vegetationData.landCoverDistribution;

    return PieChart(
      PieChartData(
        sections: _buildLandCoverSections(landCoverData),
        centerSpaceRadius: 60,
        sectionsSpace: 2,
        pieTouchData: PieTouchData(
          touchCallback: (FlTouchEvent event, pieTouchResponse) {
            // Handle touch interactions
          },
        ),
      ),
    );
  }

  /// Builds vegetation health assessment chart
  Widget _buildHealthAssessmentChart() {
    final healthData = _calculateHealthDistribution();

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
                final health = VegetationHealth.values[value.toInt() % VegetationHealth.values.length];
                return Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    _getHealthDisplayName(health),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                );
              },
              reservedSize: 40,
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
        barGroups: _buildHealthBarGroups(healthData),
        maxY: healthData.values.isNotEmpty
            ? healthData.values.reduce((a, b) => a > b ? a : b) * 1.1
            : 100,
      ),
    );
  }

  /// Builds legend for vegetation indices
  Widget _buildLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: _selectedIndices.map((index) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _indexColors[index],
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              _getIndexDisplayName(index),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Builds land cover summary panel
  Widget _buildLandCoverSummary() {
    final landCoverData = widget.vegetationData.landCoverDistribution;
    final dominantType = landCoverData.entries
        .reduce((a, b) => a.value > b.value ? a : b);

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
            'Land Cover Summary',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildLandCoverStat(
                'Dominant',
                _getLandCoverDisplayName(dominantType.key),
                _landCoverColors[dominantType.key] ?? Colors.grey,
              ),
              _buildLandCoverStat(
                'Coverage',
                '${(dominantType.value * 100).toStringAsFixed(1)}%',
                _landCoverColors[dominantType.key] ?? Colors.grey,
              ),
              _buildLandCoverStat(
                'Breeding Risk',
                _getBreedingRisk(dominantType.key),
                _getBreedingRiskColor(dominantType.key),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds individual land cover statistic
  Widget _buildLandCoverStat(String label, String value, Color color) {
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
            color: color,
          ),
        ),
      ],
    );
  }

  /// Prepares time series chart data
  Map<VegetationIndex, List<FlSpot>> _prepareTimeSeriesData() {
    final chartData = <VegetationIndex, List<FlSpot>>{};

    for (final index in _selectedIndices) {
      final spots = <FlSpot>[];
      List<VegetationMeasurement> measurements;

      switch (index) {
        case VegetationIndex.ndvi:
          measurements = widget.vegetationData.ndvi;
          break;
        case VegetationIndex.evi:
          measurements = widget.vegetationData.evi;
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
        if (measurement.quality >= 0.7 || !_showDataQuality) {
          spots.add(FlSpot(i.toDouble(), measurement.value));
        }
      }

      if (spots.isNotEmpty) {
        chartData[index] = spots;
      }
    }

    return chartData;
  }

  /// Builds line chart bars for vegetation indices
  List<LineChartBarData> _buildLineChartBars(Map<VegetationIndex, List<FlSpot>> chartData) {
    final lineBars = <LineChartBarData>[];

    chartData.forEach((index, spots) {
      lineBars.add(
        LineChartBarData(
          spots: spots,
          isCurved: true,
          color: _indexColors[index],
          barWidth: 3,
          isStrokeCapRound: true,
          dotData: FlDotData(
            show: spots.length < 30,
            getDotPainter: (spot, percent, barData, barIndex) {
              return FlDotCirclePainter(
                radius: 3,
                color: _indexColors[index]!,
                strokeWidth: 1,
                strokeColor: Theme.of(context).colorScheme.surface,
              );
            },
          ),
          belowBarData: BarAreaData(
            show: index == VegetationIndex.ndvi,
            color: _indexColors[index]?.withValues(alpha: 0.1),
          ),
        ),
      );
    });

    return lineBars;
  }

  /// Builds vegetation health zones
  ExtraLinesData _buildHealthZones() {
    return ExtraLinesData(
      horizontalLines: [
        HorizontalLine(
          y: _bareGroundThreshold,
          color: Colors.brown.withValues(alpha: 0.6),
          strokeWidth: 2,
          dashArray: [5, 5],
          label: HorizontalLineLabel(
            show: true,
            labelResolver: (line) => 'Bare Ground',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.brown,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        HorizontalLine(
          y: _sparseVegetationThreshold,
          color: Colors.orange.withValues(alpha: 0.8),
          strokeWidth: 2,
          dashArray: [3, 3],
          label: HorizontalLineLabel(
            show: true,
            labelResolver: (line) => 'Sparse Vegetation',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.orange,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        HorizontalLine(
          y: _healthyVegetationThreshold,
          color: Colors.green.withValues(alpha: 0.8),
          strokeWidth: 3,
          dashArray: [3, 3],
          label: HorizontalLineLabel(
            show: true,
            labelResolver: (line) => 'Healthy Vegetation',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Colors.green,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  /// Calculates seasonal vegetation data
  Map<Season, double> _calculateSeasonalData() {
    final seasonalData = <Season, List<double>>{
      Season.spring: [],
      Season.summer: [],
      Season.autumn: [],
      Season.winter: [],
    };

    for (final measurement in widget.vegetationData.ndvi) {
      final season = _getSeasonFromDate(measurement.date);
      seasonalData[season]?.add(measurement.value);
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
      final color = _getSeasonalVegetationColor(value);

      barGroups.add(
        BarChartGroupData(
          x: index,
          barRods: [
            BarChartRodData(
              toY: value,
              color: color,
              width: 24,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
            ),
          ],
        ),
      );
    });

    return barGroups;
  }

  /// Builds land cover pie chart sections
  List<PieChartSectionData> _buildLandCoverSections(Map<LandCoverType, double> landCoverData) {
    final sections = <PieChartSectionData>[];

    landCoverData.forEach((type, percentage) {
      sections.add(
        PieChartSectionData(
          value: percentage * 100,
          title: '${(percentage * 100).toStringAsFixed(1)}%',
          color: _landCoverColors[type] ?? Colors.grey,
          radius: 50,
          titleStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      );
    });

    return sections;
  }

  /// Calculates vegetation health distribution
  Map<VegetationHealth, double> _calculateHealthDistribution() {
    final healthCounts = <VegetationHealth, int>{
      VegetationHealth.bare: 0,
      VegetationHealth.sparse: 0,
      VegetationHealth.moderate: 0,
      VegetationHealth.healthy: 0,
    };

    for (final measurement in widget.vegetationData.ndvi) {
      final health = _getVegetationHealthEnum(measurement.value);
      healthCounts[health] = (healthCounts[health] ?? 0) + 1;
    }

    final total = healthCounts.values.reduce((a, b) => a + b);
    if (total == 0) return {};

    return healthCounts.map((health, count) {
      final percentage = (count / total) * 100;
      return MapEntry(health, percentage);
    });
  }

  /// Builds health assessment bar groups
  List<BarChartGroupData> _buildHealthBarGroups(Map<VegetationHealth, double> healthData) {
    final barGroups = <BarChartGroupData>[];

    VegetationHealth.values.asMap().forEach((index, health) {
      final percentage = healthData[health] ?? 0.0;
      final color = _getHealthColor(health);

      barGroups.add(
        BarChartGroupData(
          x: index,
          barRods: [
            BarChartRodData(
              toY: percentage,
              color: color,
              width: 24,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
            ),
          ],
        ),
      );
    });

    return barGroups;
  }

  /// Gets current NDVI value
  double _getCurrentNDVIValue() {
    final ndvi = widget.vegetationData.ndvi;
    if (ndvi.isEmpty) return 0;
    return ndvi.last.value;
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
    final allMeasurements = <VegetationMeasurement>[];
    allMeasurements.addAll(widget.vegetationData.ndvi);
    allMeasurements.addAll(widget.vegetationData.evi);

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

  /// Gets vegetation index from bar index
  VegetationIndex _getIndexFromBarIndex(int barIndex) {
    final indicesList = _selectedIndices.toList();
    return indicesList[barIndex % indicesList.length];
  }

  /// Gets seasonal vegetation color based on value
  Color _getSeasonalVegetationColor(double value) {
    if (value >= _healthyVegetationThreshold) return Colors.green.shade600;
    if (value >= _sparseVegetationThreshold) return Colors.orange.shade600;
    return Colors.brown.shade400;
  }

  /// Gets vegetation health from NDVI value
  String _getVegetationHealth(double ndvi) {
    if (ndvi >= _healthyVegetationThreshold) return 'Healthy';
    if (ndvi >= _sparseVegetationThreshold) return 'Sparse';
    if (ndvi >= _bareGroundThreshold) return 'Very Sparse';
    return 'Bare/Water';
  }

  /// Gets vegetation health enum from NDVI value
  VegetationHealth _getVegetationHealthEnum(double ndvi) {
    if (ndvi >= _healthyVegetationThreshold) return VegetationHealth.healthy;
    if (ndvi >= _sparseVegetationThreshold) return VegetationHealth.moderate;
    if (ndvi >= _bareGroundThreshold) return VegetationHealth.sparse;
    return VegetationHealth.bare;
  }

  /// Gets health color
  Color _getHealthColor(VegetationHealth health) {
    switch (health) {
      case VegetationHealth.bare:
        return Colors.brown.shade400;
      case VegetationHealth.sparse:
        return Colors.orange.shade400;
      case VegetationHealth.moderate:
        return Colors.yellow.shade600;
      case VegetationHealth.healthy:
        return Colors.green.shade600;
    }
  }

  /// Gets breeding risk from land cover type
  String _getBreedingRisk(LandCoverType type) {
    switch (type) {
      case LandCoverType.wetland:
      case LandCoverType.water:
        return 'High';
      case LandCoverType.forest:
      case LandCoverType.grassland:
        return 'Moderate';
      case LandCoverType.cropland:
        return 'Low';
      case LandCoverType.urban:
      case LandCoverType.bareland:
        return 'Very Low';
    }
  }

  /// Gets breeding risk color
  Color _getBreedingRiskColor(LandCoverType type) {
    switch (type) {
      case LandCoverType.wetland:
      case LandCoverType.water:
        return Colors.red;
      case LandCoverType.forest:
      case LandCoverType.grassland:
        return Colors.orange;
      case LandCoverType.cropland:
        return Colors.yellow.shade700;
      case LandCoverType.urban:
      case LandCoverType.bareland:
        return Colors.green;
    }
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(VegetationViewMode mode) {
    switch (mode) {
      case VegetationViewMode.timeSeries:
        return 'Time Series';
      case VegetationViewMode.seasonal:
        return 'Seasonal';
      case VegetationViewMode.landCover:
        return 'Land Cover';
      case VegetationViewMode.health:
        return 'Health';
    }
  }

  /// Gets index display name
  String _getIndexDisplayName(VegetationIndex index) {
    switch (index) {
      case VegetationIndex.ndvi:
        return 'NDVI';
      case VegetationIndex.evi:
        return 'EVI';
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

  /// Gets health display name
  String _getHealthDisplayName(VegetationHealth health) {
    switch (health) {
      case VegetationHealth.bare:
        return 'Bare/Water';
      case VegetationHealth.sparse:
        return 'Sparse';
      case VegetationHealth.moderate:
        return 'Moderate';
      case VegetationHealth.healthy:
        return 'Healthy';
    }
  }

  /// Gets land cover display name
  String _getLandCoverDisplayName(LandCoverType type) {
    switch (type) {
      case LandCoverType.forest:
        return 'Forest';
      case LandCoverType.grassland:
        return 'Grassland';
      case LandCoverType.cropland:
        return 'Cropland';
      case LandCoverType.urban:
        return 'Urban';
      case LandCoverType.water:
        return 'Water';
      case LandCoverType.bareland:
        return 'Bare Land';
      case LandCoverType.wetland:
        return 'Wetland';
    }
  }

  /// Checks if vegetation data is empty
  bool _isDataEmpty() {
    return widget.vegetationData.ndvi.isEmpty &&
           widget.vegetationData.evi.isEmpty;
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
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No vegetation data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Vegetation indices will appear here when data is loaded',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Shows vegetation analysis information dialog
  void _showVegetationInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Vegetation Analysis Information'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Vegetation Indices:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• NDVI: Normalized Difference Vegetation Index (-1 to +1)'),
              Text('• EVI: Enhanced Vegetation Index (improved NDVI)'),
              Text('• Higher values indicate denser, healthier vegetation'),
              SizedBox(height: 16),
              Text(
                'Vegetation Health Zones:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Bare Ground/Water: <0.1 (no vegetation)'),
              Text('• Sparse Vegetation: 0.1-0.2 (limited cover)'),
              Text('• Moderate Vegetation: 0.2-0.4 (breeding habitats)'),
              Text('• Healthy Vegetation: >0.4 (dense cover)'),
              SizedBox(height: 16),
              Text(
                'Malaria Relevance:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Moderate vegetation provides optimal breeding sites'),
              Text('• Dense vegetation reduces larval development'),
              Text('• Water bodies (low NDVI) are prime breeding areas'),
              Text('• Land cover affects local microclimates'),
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

/// Vegetation view mode enumeration
enum VegetationViewMode {
  timeSeries,
  seasonal,
  landCover,
  health,
}

/// Vegetation index enumeration
enum VegetationIndex {
  ndvi,
  evi,
}

/// Vegetation health enumeration
enum VegetationHealth {
  bare,
  sparse,
  moderate,
  healthy,
}

/// Vegetation aggregation enumeration
enum VegetationAggregation {
  daily,
  weekly,
  monthly,
  seasonal,
}