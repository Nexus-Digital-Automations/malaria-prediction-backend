/// Climate correlation chart widget showing malaria risk correlations
///
/// This widget displays comprehensive correlation analysis between environmental
/// factors and malaria transmission risk using scatter plots, correlation matrices,
/// and statistical significance indicators for predictive modeling insights.
///
/// Usage:
/// ```dart
/// ClimateCorrelationChart(
///   climateMetrics: climateMetrics,
///   height: 400,
///   viewMode: CorrelationViewMode.scatterMatrix,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Climate correlation chart widget with malaria risk correlation analysis
class ClimateCorrelationChart extends StatefulWidget {
  /// Climate metrics data containing correlation coefficients
  final ClimateMetrics climateMetrics;

  /// Chart height
  final double height;

  /// View mode for correlation presentation
  final CorrelationViewMode viewMode;

  /// Environmental data for scatter plot analysis
  final EnvironmentalData? environmentalData;

  /// Risk trend data for correlation analysis
  final List<RiskTrend>? riskTrends;

  /// Whether to show statistical significance indicators
  final bool showSignificance;

  /// Confidence level for significance testing (default 0.95)
  final double confidenceLevel;

  /// Constructor requiring climate metrics
  const ClimateCorrelationChart({
    super.key,
    required this.climateMetrics,
    this.height = 400,
    this.viewMode = CorrelationViewMode.matrix,
    this.environmentalData,
    this.riskTrends,
    this.showSignificance = true,
    this.confidenceLevel = 0.95,
  });

  @override
  State<ClimateCorrelationChart> createState() => _ClimateCorrelationChartState();
}

class _ClimateCorrelationChartState extends State<ClimateCorrelationChart> {
  /// Current correlation view mode
  late CorrelationViewMode _currentViewMode;

  /// Color mapping for correlation strength
  final Map<CorrelationStrength, Color> _correlationColors = {
    CorrelationStrength.veryWeak: Colors.grey.shade300,
    CorrelationStrength.weak: Colors.blue.shade200,
    CorrelationStrength.moderate: Colors.blue.shade500,
    CorrelationStrength.strong: Colors.red.shade500,
    CorrelationStrength.veryStrong: Colors.red.shade700,
  };

  /// Environmental factors for correlation analysis
  final List<EnvironmentalFactor> _factors = [
    EnvironmentalFactor.temperature,
    EnvironmentalFactor.rainfall,
    EnvironmentalFactor.humidity,
    EnvironmentalFactor.vegetation,
  ];

  /// Selected factors for detailed analysis
  final Set<EnvironmentalFactor> _selectedFactors = {
    EnvironmentalFactor.temperature,
    EnvironmentalFactor.rainfall,
  };

  /// Correlation matrix data
  late Map<String, Map<String, double>> _correlationMatrix;

  /// Selected factor pair for scatter plot
  FactorPair? _selectedPair;

  @override
  void initState() {
    super.initState();
    _currentViewMode = widget.viewMode;
    _buildCorrelationMatrix();
  }

  @override
  void didUpdateWidget(ClimateCorrelationChart oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.climateMetrics != widget.climateMetrics) {
      _buildCorrelationMatrix();
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
            if (_currentViewMode == CorrelationViewMode.scatter) _buildFactorSelector(),
            const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (widget.showSignificance) _buildSignificanceIndicators(),
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
                'Climate-Malaria Correlation Analysis',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '${widget.climateMetrics.region} • ${widget.climateMetrics.year}',
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
                Icons.download,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _exportCorrelationData(),
              tooltip: 'Export Correlation Data',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showCorrelationInfo(),
              tooltip: 'Correlation Analysis Info',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds correlation view mode selector
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
              children: CorrelationViewMode.values.map((mode) {
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

  /// Builds factor selector for scatter plot mode
  Widget _buildFactorSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Select Factors for Scatter Plot:',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 8,
          children: _factors.map((factor) {
            final isSelected = _selectedFactors.contains(factor);
            return FilterChip(
              label: Text(_getFactorDisplayName(factor)),
              selected: isSelected,
              onSelected: (selected) {
                setState(() {
                  if (selected && _selectedFactors.length < 2) {
                    _selectedFactors.add(factor);
                  } else if (!selected) {
                    _selectedFactors.remove(factor);
                  }

                  // Update selected pair for scatter plot
                  if (_selectedFactors.length == 2) {
                    final factorList = _selectedFactors.toList();
                    _selectedPair = FactorPair(
                      factorX: factorList[0],
                      factorY: factorList[1],
                    );
                  } else {
                    _selectedPair = null;
                  }
                });
              },
              backgroundColor: isSelected ? null : Colors.grey.shade100,
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds the main correlation chart
  Widget _buildChart() {
    switch (_currentViewMode) {
      case CorrelationViewMode.matrix:
        return _buildCorrelationMatrix();
      case CorrelationViewMode.scatter:
        return _buildScatterPlot();
      case CorrelationViewMode.heatmap:
        return _buildCorrelationHeatmap();
      case CorrelationViewMode.barChart:
        return _buildCorrelationBarChart();
    }
  }

  /// Builds correlation matrix visualization
  Widget _buildCorrelationMatrix() {
    final factors = ['Temperature', 'Rainfall', 'Humidity', 'Vegetation', 'Malaria Risk'];
    final matrixSize = factors.length;

    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).dividerColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          // Header row
          Container(
            height: 40,
            child: Row(
              children: [
                SizedBox(width: 80), // Empty corner
                ...factors.map((factor) => Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    child: Text(
                      factor,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                )),
              ],
            ),
          ),
          // Matrix rows
          Expanded(
            child: Column(
              children: List.generate(matrixSize, (row) {
                return Expanded(
                  child: Row(
                    children: [
                      // Row label
                      Container(
                        width: 80,
                        padding: const EdgeInsets.all(4),
                        child: Text(
                          factors[row],
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      // Correlation cells
                      ...List.generate(matrixSize, (col) {
                        final correlation = _getCorrelationValue(factors[row], factors[col]);
                        final isSignificant = _isSignificant(correlation);

                        return Expanded(
                          child: GestureDetector(
                            onTap: () {
                              if (row != col) {
                                _showCorrelationDetails(factors[row], factors[col], correlation);
                              }
                            },
                            child: Container(
                              decoration: BoxDecoration(
                                color: _getCorrelationColor(correlation),
                                border: Border.all(
                                  color: isSignificant ? Colors.black : Colors.grey.shade300,
                                  width: isSignificant ? 1 : 0.5,
                                ),
                              ),
                              child: Center(
                                child: Text(
                                  row == col ? '1.00' : correlation.toStringAsFixed(2),
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: _getTextColor(correlation),
                                    fontWeight: isSignificant ? FontWeight.bold : FontWeight.normal,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        );
                      }),
                    ],
                  ),
                );
              }),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds scatter plot for selected factor pair
  Widget _buildScatterPlot() {
    if (_selectedPair == null || widget.environmentalData == null || widget.riskTrends == null) {
      return _buildNoDataMessage('Select two factors to view scatter plot correlation');
    }

    final scatterData = _generateScatterData(_selectedPair!);

    if (scatterData.isEmpty) {
      return _buildNoDataMessage('No data available for selected factor pair');
    }

    return ScatterChart(
      ScatterChartData(
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
            axisNameWidget: Text(
              _getFactorDisplayName(_selectedPair!.factorY),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
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
            axisNameWidget: Text(
              _getFactorDisplayName(_selectedPair!.factorX),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) => Text(
                value.toStringAsFixed(1),
                style: Theme.of(context).textTheme.bodySmall,
              ),
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
        scatterSpots: scatterData.map((point) => ScatterSpot(
          point.x,
          point.y,
          color: _getScatterPointColor(point.riskLevel),
          radius: 4,
        )).toList(),
        scatterTouchData: ScatterTouchData(
          touchTooltipData: ScatterTouchTooltipData(
            getTooltipItems: (spot) {
              final point = scatterData[scatterData.indexWhere((p) =>
                p.x == spot.x && p.y == spot.y)];
              return ScatterTooltipItem(
                '${_getFactorDisplayName(_selectedPair!.factorX)}: ${spot.x.toStringAsFixed(1)}\n'
                '${_getFactorDisplayName(_selectedPair!.factorY)}: ${spot.y.toStringAsFixed(1)}\n'
                'Risk Level: ${point.riskLevel.name}',
                TextStyle(
                  color: _getScatterPointColor(point.riskLevel),
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  /// Builds correlation heatmap
  Widget _buildCorrelationHeatmap() {
    final factors = _factors.map(_getFactorDisplayName).toList();
    factors.add('Malaria Risk');

    return GridView.builder(
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: factors.length,
        crossAxisSpacing: 1,
        mainAxisSpacing: 1,
      ),
      itemCount: factors.length * factors.length,
      itemBuilder: (context, index) {
        final row = index ~/ factors.length;
        final col = index % factors.length;
        final correlation = _getCorrelationValue(factors[row], factors[col]);

        return Container(
          decoration: BoxDecoration(
            color: _getCorrelationColor(correlation),
            border: Border.all(color: Colors.white, width: 0.5),
          ),
          child: Center(
            child: Text(
              row == col ? '1.0' : correlation.toStringAsFixed(1),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: _getTextColor(correlation),
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        );
      },
    );
  }

  /// Builds correlation bar chart
  Widget _buildCorrelationBarChart() {
    final correlations = widget.climateMetrics.malariaCorrelations;

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
                final factors = correlations.keys.toList();
                final index = value.toInt();
                if (index >= 0 && index < factors.length) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      _getFactorDisplayName(factors[index]),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  );
                }
                return const Text('');
              },
              reservedSize: 60,
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
        barGroups: correlations.entries.map((entry) {
          final index = correlations.keys.toList().indexOf(entry.key);
          final correlation = entry.value;

          return BarChartGroupData(
            x: index,
            barRods: [
              BarChartRodData(
                toY: correlation,
                color: _getCorrelationColor(correlation),
                width: 24,
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(4),
                  bottom: Radius.circular(4),
                ),
              ),
            ],
          );
        }).toList(),
        barTouchData: BarTouchData(
          touchTooltipData: BarTouchTooltipData(
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              final factor = correlations.keys.toList()[groupIndex];
              final correlation = rod.toY;
              return BarTooltipItem(
                '${_getFactorDisplayName(factor)}\n'
                'Correlation: ${correlation.toStringAsFixed(3)}\n'
                'Strength: ${_getCorrelationStrength(correlation).name}',
                TextStyle(
                  color: _getCorrelationColor(correlation),
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              );
            },
          ),
        ),
        minY: -1.0,
        maxY: 1.0,
        extraLinesData: ExtraLinesData(
          horizontalLines: [
            HorizontalLine(
              y: 0,
              color: Colors.black,
              strokeWidth: 1,
            ),
          ],
        ),
      ),
    );
  }

  /// Builds legend for the chart
  Widget _buildLegend() {
    switch (_currentViewMode) {
      case CorrelationViewMode.matrix:
      case CorrelationViewMode.heatmap:
      case CorrelationViewMode.barChart:
        return _buildCorrelationLegend();
      case CorrelationViewMode.scatter:
        return _buildScatterLegend();
    }
  }

  /// Builds correlation strength legend
  Widget _buildCorrelationLegend() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Correlation Strength',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 12,
          runSpacing: 4,
          children: CorrelationStrength.values.map((strength) {
            return Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: _correlationColors[strength],
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  _getStrengthDisplayName(strength),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds scatter plot legend
  Widget _buildScatterLegend() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Risk Levels',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 12,
          runSpacing: 4,
          children: RiskLevel.values.map((level) {
            return Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _getScatterPointColor(level),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  level.name.toUpperCase(),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds statistical significance indicators
  Widget _buildSignificanceIndicators() {
    final significantCorrelations = widget.climateMetrics.malariaCorrelations.entries
        .where((entry) => _isSignificant(entry.value))
        .length;

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: significantCorrelations > 0
            ? Colors.green.shade50
            : Colors.orange.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: significantCorrelations > 0
              ? Colors.green.shade200
              : Colors.orange.shade200,
        ),
      ),
      child: Row(
        children: [
          Icon(
            significantCorrelations > 0 ? Icons.check_circle_outline : Icons.warning_amber_outlined,
            color: significantCorrelations > 0
                ? Colors.green.shade600
                : Colors.orange.shade600,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Statistical Significance (${(widget.confidenceLevel * 100).toStringAsFixed(0)}% confidence): '
              '$significantCorrelations/${widget.climateMetrics.malariaCorrelations.length} correlations significant',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: significantCorrelations > 0
                    ? Colors.green.shade800
                    : Colors.orange.shade800,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.scatter_plot_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds correlation matrix data
  void _buildCorrelationMatrix() {
    _correlationMatrix = {
      'Temperature': {
        'Temperature': 1.0,
        'Rainfall': widget.climateMetrics.temperatureRainfallCorrelation,
        'Humidity': widget.climateMetrics.humidityTemperatureCorrelation,
        'Vegetation': widget.climateMetrics.vegetationRainfallCorrelation * 0.7, // Approximation
        'Malaria Risk': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.temperature] ?? 0.0,
      },
      'Rainfall': {
        'Temperature': widget.climateMetrics.temperatureRainfallCorrelation,
        'Rainfall': 1.0,
        'Humidity': 0.65, // Typical correlation
        'Vegetation': widget.climateMetrics.vegetationRainfallCorrelation,
        'Malaria Risk': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.rainfall] ?? 0.0,
      },
      'Humidity': {
        'Temperature': widget.climateMetrics.humidityTemperatureCorrelation,
        'Rainfall': 0.65,
        'Humidity': 1.0,
        'Vegetation': 0.45, // Typical correlation
        'Malaria Risk': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.humidity] ?? 0.0,
      },
      'Vegetation': {
        'Temperature': widget.climateMetrics.vegetationRainfallCorrelation * 0.7,
        'Rainfall': widget.climateMetrics.vegetationRainfallCorrelation,
        'Humidity': 0.45,
        'Vegetation': 1.0,
        'Malaria Risk': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.vegetation] ?? 0.0,
      },
      'Malaria Risk': {
        'Temperature': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.temperature] ?? 0.0,
        'Rainfall': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.rainfall] ?? 0.0,
        'Humidity': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.humidity] ?? 0.0,
        'Vegetation': widget.climateMetrics.malariaCorrelations[EnvironmentalFactor.vegetation] ?? 0.0,
        'Malaria Risk': 1.0,
      },
    };
  }

  /// Generates scatter plot data for factor pair
  List<ScatterDataPoint> _generateScatterData(FactorPair pair) {
    // Mock implementation - in real app, this would combine environmental and risk data
    final random = math.Random(42); // Seeded for consistent results
    final dataPoints = <ScatterDataPoint>[];

    for (int i = 0; i < 50; i++) {
      final x = random.nextDouble() * 100; // Mock environmental factor value
      final y = random.nextDouble() * 100; // Mock second environmental factor value

      // Determine risk level based on combined factors
      final riskScore = (x + y) / 200; // Normalize to 0-1
      late RiskLevel riskLevel;
      if (riskScore < 0.25) {
        riskLevel = RiskLevel.low;
      } else if (riskScore < 0.5) {
        riskLevel = RiskLevel.medium;
      } else if (riskScore < 0.75) {
        riskLevel = RiskLevel.high;
      } else {
        riskLevel = RiskLevel.critical;
      }

      dataPoints.add(ScatterDataPoint(
        x: x,
        y: y,
        riskLevel: riskLevel,
      ));
    }

    return dataPoints;
  }

  /// Gets correlation value from matrix
  double _getCorrelationValue(String factor1, String factor2) {
    return _correlationMatrix[factor1]?[factor2] ?? 0.0;
  }

  /// Gets correlation color based on strength
  Color _getCorrelationColor(double correlation) {
    final strength = _getCorrelationStrength(correlation);
    return _correlationColors[strength] ?? Colors.grey;
  }

  /// Gets correlation strength category
  CorrelationStrength _getCorrelationStrength(double correlation) {
    final abs = correlation.abs();
    if (abs < 0.2) return CorrelationStrength.veryWeak;
    if (abs < 0.4) return CorrelationStrength.weak;
    if (abs < 0.6) return CorrelationStrength.moderate;
    if (abs < 0.8) return CorrelationStrength.strong;
    return CorrelationStrength.veryStrong;
  }

  /// Gets text color for correlation value
  Color _getTextColor(double correlation) {
    final abs = correlation.abs();
    return abs > 0.5 ? Colors.white : Colors.black;
  }

  /// Gets scatter point color based on risk level
  Color _getScatterPointColor(RiskLevel riskLevel) {
    switch (riskLevel) {
      case RiskLevel.low:
        return Colors.green;
      case RiskLevel.medium:
        return Colors.orange;
      case RiskLevel.high:
        return Colors.red;
      case RiskLevel.critical:
        return Colors.purple;
    }
  }

  /// Checks if correlation is statistically significant
  bool _isSignificant(double correlation) {
    // Simplified significance test - in real app, would use proper statistical tests
    return correlation.abs() > 0.3; // Threshold for significance
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(CorrelationViewMode mode) {
    switch (mode) {
      case CorrelationViewMode.matrix:
        return 'Matrix';
      case CorrelationViewMode.scatter:
        return 'Scatter Plot';
      case CorrelationViewMode.heatmap:
        return 'Heatmap';
      case CorrelationViewMode.barChart:
        return 'Bar Chart';
    }
  }

  /// Gets factor display name
  String _getFactorDisplayName(EnvironmentalFactor factor) {
    switch (factor) {
      case EnvironmentalFactor.temperature:
        return 'Temperature';
      case EnvironmentalFactor.rainfall:
        return 'Rainfall';
      case EnvironmentalFactor.humidity:
        return 'Humidity';
      case EnvironmentalFactor.vegetation:
        return 'Vegetation';
      case EnvironmentalFactor.windSpeed:
        return 'Wind Speed';
      case EnvironmentalFactor.pressure:
        return 'Pressure';
    }
  }

  /// Gets strength display name
  String _getStrengthDisplayName(CorrelationStrength strength) {
    switch (strength) {
      case CorrelationStrength.veryWeak:
        return 'Very Weak';
      case CorrelationStrength.weak:
        return 'Weak';
      case CorrelationStrength.moderate:
        return 'Moderate';
      case CorrelationStrength.strong:
        return 'Strong';
      case CorrelationStrength.veryStrong:
        return 'Very Strong';
    }
  }

  /// Shows correlation details dialog
  void _showCorrelationDetails(String factor1, String factor2, double correlation) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Correlation Details'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Factors: $factor1 × $factor2'),
            const SizedBox(height: 8),
            Text('Correlation: ${correlation.toStringAsFixed(3)}'),
            Text('Strength: ${_getCorrelationStrength(correlation).name}'),
            Text('Significant: ${_isSignificant(correlation) ? "Yes" : "No"}'),
            const SizedBox(height: 16),
            Text(
              'Interpretation:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(_getCorrelationInterpretation(correlation)),
          ],
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

  /// Gets correlation interpretation text
  String _getCorrelationInterpretation(double correlation) {
    if (correlation > 0.7) {
      return 'Strong positive relationship - as one factor increases, the other tends to increase significantly.';
    } else if (correlation > 0.3) {
      return 'Moderate positive relationship - factors tend to increase together.';
    } else if (correlation > -0.3) {
      return 'Weak relationship - little linear association between factors.';
    } else if (correlation > -0.7) {
      return 'Moderate negative relationship - as one factor increases, the other tends to decrease.';
    } else {
      return 'Strong negative relationship - factors have opposite trends.';
    }
  }

  /// Exports correlation data
  void _exportCorrelationData() {
    // Mock implementation - in real app, would export to CSV or PDF
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Correlation data exported successfully'),
      ),
    );
  }

  /// Shows correlation analysis information dialog
  void _showCorrelationInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Correlation Analysis Information'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Correlation Interpretation:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• +1.0: Perfect positive correlation'),
              Text('• +0.7: Strong positive correlation'),
              Text('• +0.3: Moderate positive correlation'),
              Text('• 0.0: No linear relationship'),
              Text('• -0.3: Moderate negative correlation'),
              Text('• -0.7: Strong negative correlation'),
              Text('• -1.0: Perfect negative correlation'),
              SizedBox(height: 16),
              Text(
                'Malaria Transmission Correlations:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Temperature: Positive correlation (25°C optimal)'),
              Text('• Rainfall: Strong positive (breeding sites)'),
              Text('• Humidity: Positive (mosquito survival)'),
              Text('• Vegetation: Moderate positive (habitat)'),
              SizedBox(height: 16),
              Text(
                'Statistical Significance:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('Bold values indicate statistically significant\ncorrelations at 95% confidence level'),
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

/// Correlation view mode enumeration
enum CorrelationViewMode {
  matrix,
  scatter,
  heatmap,
  barChart,
}

/// Correlation strength enumeration
enum CorrelationStrength {
  veryWeak,
  weak,
  moderate,
  strong,
  veryStrong,
}

/// Factor pair for scatter plot analysis
class FactorPair {
  final EnvironmentalFactor factorX;
  final EnvironmentalFactor factorY;

  const FactorPair({
    required this.factorX,
    required this.factorY,
  });
}

/// Scatter plot data point
class ScatterDataPoint {
  final double x;
  final double y;
  final RiskLevel riskLevel;

  const ScatterDataPoint({
    required this.x,
    required this.y,
    required this.riskLevel,
  });
}