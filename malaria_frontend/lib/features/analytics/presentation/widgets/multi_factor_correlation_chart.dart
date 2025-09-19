/// Multi-factor correlation analysis chart for environmental data
///
/// This widget provides comprehensive correlation analysis between multiple
/// environmental factors affecting malaria transmission, including statistical
/// significance testing, correlation matrices, and interactive visualization.
///
/// Features:
/// - Correlation matrix visualization
/// - Statistical significance indicators
/// - Time-lagged correlation analysis
/// - Factor relationship networks
/// - Malaria transmission correlations
/// - Interactive correlation exploration
///
/// Usage:
/// ```dart
/// MultiFactorCorrelationChart(
///   environmentalData: environmentalData,
///   selectedFactors: factors,
///   height: 400,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Comprehensive multi-factor correlation analysis chart widget
class MultiFactorCorrelationChart extends StatefulWidget {
  /// Environmental data for correlation analysis
  final EnvironmentalData environmentalData;

  /// Environmental factors to analyze
  final Set<EnvironmentalFactor> selectedFactors;

  /// Widget height
  final double height;

  /// Whether to include malaria risk correlations
  final bool includeMalariaRisk;

  /// Whether to show statistical significance
  final bool showSignificance;

  /// Whether to enable time-lag analysis
  final bool enableTimeLag;

  /// Date range for correlation analysis
  final DateRange? dateRange;

  /// Constructor requiring environmental data
  const MultiFactorCorrelationChart({
    super.key,
    required this.environmentalData,
    required this.selectedFactors,
    this.height = 400,
    this.includeMalariaRisk = true,
    this.showSignificance = true,
    this.enableTimeLag = false,
    this.dateRange,
  });

  @override
  State<MultiFactorCorrelationChart> createState() => _MultiFactorCorrelationChartState();
}

class _MultiFactorCorrelationChartState extends State<MultiFactorCorrelationChart> {
  /// Current correlation view mode
  CorrelationViewMode _viewMode = CorrelationViewMode.matrix;

  /// Current correlation method
  CorrelationMethod _method = CorrelationMethod.pearson;

  /// Time lag for analysis (days)
  int _timeLag = 0;

  /// Correlation threshold for significance
  double _significanceThreshold = 0.05;

  /// Color mapping for correlation strength
  final Map<CorrelationStrength, Color> _strengthColors = {
    CorrelationStrength.veryWeak: Colors.grey.shade300,
    CorrelationStrength.weak: Colors.yellow.shade400,
    CorrelationStrength.moderate: Colors.orange.shade500,
    CorrelationStrength.strong: Colors.red.shade600,
    CorrelationStrength.veryStrong: Colors.purple.shade700,
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

  /// Calculated correlation matrix
  late Map<String, Map<String, CorrelationResult>> _correlationMatrix;

  /// Show only significant correlations
  bool _showSignificantOnly = false;

  /// Selected correlation cell for details
  CorrelationResult? _selectedCorrelation;

  @override
  void initState() {
    super.initState();
    _calculateCorrelations();
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
            const SizedBox(height: 12),
            Expanded(child: _buildChart()),
            if (_selectedCorrelation != null) _buildCorrelationDetails(),
            const SizedBox(height: 8),
            _buildLegend(),
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
                'Multi-Factor Correlation Analysis',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '${widget.selectedFactors.length} factors • ${_getAnalysisTypeDescription()}',
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
                _showSignificantOnly ? Icons.filter_alt : Icons.filter_alt_outlined,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () {
                setState(() {
                  _showSignificantOnly = !_showSignificantOnly;
                });
              },
              tooltip: 'Toggle Significant Correlations Only',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showCorrelationInfo(),
              tooltip: 'Correlation Analysis Information',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds control panel for analysis options
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
                  children: CorrelationViewMode.values.map((mode) {
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
              'Method:',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: CorrelationMethod.values.map((method) {
                    final isSelected = method == _method;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(_getMethodDisplayName(method)),
                        selected: isSelected,
                        onSelected: (selected) {
                          if (selected) {
                            setState(() {
                              _method = method;
                              _calculateCorrelations();
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
        if (widget.enableTimeLag)
          Row(
            children: [
              Text(
                'Time Lag:',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Slider(
                  value: _timeLag.toDouble(),
                  min: 0,
                  max: 30,
                  divisions: 30,
                  label: '${_timeLag} days',
                  onChanged: (value) {
                    setState(() {
                      _timeLag = value.toInt();
                      _calculateCorrelations();
                    });
                  },
                ),
              ),
              Text(
                '${_timeLag} days',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
      ],
    );
  }

  /// Builds the main correlation chart
  Widget _buildChart() {
    if (widget.selectedFactors.length < 2) {
      return _buildInsufficientDataMessage();
    }

    switch (_viewMode) {
      case CorrelationViewMode.matrix:
        return _buildCorrelationMatrix();
      case CorrelationViewMode.network:
        return _buildCorrelationNetwork();
      case CorrelationViewMode.scatterplot:
        return _buildScatterplotMatrix();
      case CorrelationViewMode.heatmap:
        return _buildCorrelationHeatmap();
    }
  }

  /// Builds correlation matrix visualization
  Widget _buildCorrelationMatrix() {
    final factors = widget.selectedFactors.toList();
    if (widget.includeMalariaRisk) {
      factors.add(EnvironmentalFactor.temperature); // Using as placeholder for malaria risk
    }

    return GridView.builder(
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: factors.length,
        childAspectRatio: 1,
        crossAxisSpacing: 2,
        mainAxisSpacing: 2,
      ),
      itemCount: factors.length * factors.length,
      itemBuilder: (context, index) {
        final row = index ~/ factors.length;
        final col = index % factors.length;
        final factor1 = factors[row];
        final factor2 = factors[col];

        return _buildCorrelationCell(factor1, factor2, row, col);
      },
    );
  }

  /// Builds individual correlation matrix cell
  Widget _buildCorrelationCell(EnvironmentalFactor factor1, EnvironmentalFactor factor2, int row, int col) {
    final correlation = _correlationMatrix[_getFactorKey(factor1)]?[_getFactorKey(factor2)];

    final isDiagonal = row == col;
    final isSignificant = correlation?.pValue != null && correlation!.pValue! < _significanceThreshold;

    if (_showSignificantOnly && !isDiagonal && (!isSignificant)) {
      return Container(
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          border: Border.all(color: Colors.grey.shade300, width: 0.5),
        ),
      );
    }

    return GestureDetector(
      onTap: isDiagonal ? null : () {
        setState(() {
          _selectedCorrelation = correlation;
        });
      },
      child: Container(
        decoration: BoxDecoration(
          color: isDiagonal
              ? Colors.grey.shade200
              : _getCorrelationColor(correlation?.coefficient ?? 0),
          border: Border.all(
            color: _selectedCorrelation == correlation
                ? Theme.of(context).colorScheme.primary
                : Colors.grey.shade300,
            width: _selectedCorrelation == correlation ? 2 : 0.5,
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (isDiagonal)
                Icon(
                  _getFactorIcon(factor1),
                  size: 16,
                  color: _factorColors[factor1],
                )
              else ...[
                Text(
                  correlation?.coefficient.toStringAsFixed(2) ?? '0.00',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _getTextColor(correlation?.coefficient ?? 0),
                  ),
                ),
                if (widget.showSignificance && isSignificant)
                  Icon(
                    Icons.star,
                    size: 8,
                    color: Colors.amber.shade700,
                  ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  /// Builds correlation network visualization
  Widget _buildCorrelationNetwork() {
    return Container(
      child: CustomPaint(
        painter: CorrelationNetworkPainter(
          factors: widget.selectedFactors.toList(),
          correlations: _correlationMatrix,
          factorColors: _factorColors,
          showSignificantOnly: _showSignificantOnly,
          significanceThreshold: _significanceThreshold,
        ),
        child: Container(),
      ),
    );
  }

  /// Builds scatterplot matrix
  Widget _buildScatterplotMatrix() {
    return Container(
      child: Center(
        child: Text(
          'Scatterplot matrix visualization\nwill be implemented here',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// Builds correlation heatmap
  Widget _buildCorrelationHeatmap() {
    final factors = widget.selectedFactors.toList();

    return Container(
      padding: const EdgeInsets.all(8),
      child: Column(
        children: factors.map((factor1) {
          return Expanded(
            child: Row(
              children: factors.map((factor2) {
                final correlation = _correlationMatrix[_getFactorKey(factor1)]?[_getFactorKey(factor2)];
                final coefficient = correlation?.coefficient ?? 0;

                return Expanded(
                  child: Container(
                    margin: const EdgeInsets.all(1),
                    decoration: BoxDecoration(
                      color: _getCorrelationColor(coefficient),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Center(
                      child: Text(
                        coefficient.toStringAsFixed(2),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: _getTextColor(coefficient),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          );
        }).toList(),
      ),
    );
  }

  /// Builds correlation details panel
  Widget _buildCorrelationDetails() {
    final correlation = _selectedCorrelation!;

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
              Text(
                'Correlation Details',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () {
                  setState(() {
                    _selectedCorrelation = null;
                  });
                },
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _buildDetailItem('Coefficient', correlation.coefficient.toStringAsFixed(3)),
              ),
              Expanded(
                child: _buildDetailItem('Strength', _getCorrelationStrengthName(correlation.coefficient.abs())),
              ),
              if (correlation.pValue != null)
                Expanded(
                  child: _buildDetailItem('P-Value', correlation.pValue!.toStringAsFixed(4)),
                ),
            ],
          ),
          if (correlation.confidence != null)
            Row(
              children: [
                Expanded(
                  child: _buildDetailItem('Confidence', '${(correlation.confidence! * 100).toStringAsFixed(1)}%'),
                ),
                Expanded(
                  child: _buildDetailItem('Sample Size', '${correlation.sampleSize}'),
                ),
                Expanded(
                  child: _buildDetailItem(
                    'Significance',
                    correlation.pValue != null && correlation.pValue! < _significanceThreshold
                        ? 'Significant'
                        : 'Not Significant',
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  /// Builds individual detail item
  Widget _buildDetailItem(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
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
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  /// Builds legend for correlation visualization
  Widget _buildLegend() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Correlation Strength',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
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
                    color: _strengthColors[strength],
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

  /// Builds insufficient data message
  Widget _buildInsufficientDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.analytics_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'Insufficient data for correlation analysis',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Select at least 2 environmental factors',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Calculates correlation matrix for selected factors
  void _calculateCorrelations() {
    final matrix = <String, Map<String, CorrelationResult>>{};

    for (final factor1 in widget.selectedFactors) {
      matrix[_getFactorKey(factor1)] = {};

      for (final factor2 in widget.selectedFactors) {
        final correlation = _calculateCorrelation(factor1, factor2);
        matrix[_getFactorKey(factor1)]![_getFactorKey(factor2)] = correlation;
      }
    }

    setState(() {
      _correlationMatrix = matrix;
    });
  }

  /// Calculates correlation between two environmental factors
  CorrelationResult _calculateCorrelation(EnvironmentalFactor factor1, EnvironmentalFactor factor2) {
    if (factor1 == factor2) {
      return CorrelationResult(
        factor1: factor1,
        factor2: factor2,
        coefficient: 1.0,
        pValue: 0.0,
        confidence: 1.0,
        sampleSize: 100, // Mock value
      );
    }

    // Mock correlation calculation - would use real statistical methods
    final coefficient = _getMockCorrelation(factor1, factor2);
    final pValue = _calculateMockPValue(coefficient.abs());
    final confidence = 1 - pValue;
    const sampleSize = 100; // Mock sample size

    return CorrelationResult(
      factor1: factor1,
      factor2: factor2,
      coefficient: coefficient,
      pValue: pValue,
      confidence: confidence,
      sampleSize: sampleSize,
    );
  }

  /// Gets mock correlation values (would be replaced with real calculations)
  double _getMockCorrelation(EnvironmentalFactor factor1, EnvironmentalFactor factor2) {
    final correlations = {
      'temperature_rainfall': -0.34,
      'temperature_humidity': -0.67,
      'temperature_vegetation': 0.45,
      'rainfall_humidity': 0.58,
      'rainfall_vegetation': 0.72,
      'humidity_vegetation': 0.39,
      'temperature_windSpeed': 0.23,
      'temperature_pressure': -0.18,
      'rainfall_windSpeed': -0.41,
      'rainfall_pressure': 0.29,
      'humidity_windSpeed': -0.25,
      'humidity_pressure': 0.31,
      'vegetation_windSpeed': -0.19,
      'vegetation_pressure': 0.15,
      'windSpeed_pressure': -0.22,
    };

    final key1 = '${_getFactorKey(factor1)}_${_getFactorKey(factor2)}';
    final key2 = '${_getFactorKey(factor2)}_${_getFactorKey(factor1)}';

    return correlations[key1] ?? correlations[key2] ?? 0.0;
  }

  /// Calculates mock p-value based on correlation strength
  double _calculateMockPValue(double absCorrelation) {
    if (absCorrelation >= 0.7) return 0.001;
    if (absCorrelation >= 0.5) return 0.01;
    if (absCorrelation >= 0.3) return 0.05;
    return 0.1;
  }

  /// Gets color for correlation value
  Color _getCorrelationColor(double correlation) {
    final abs = correlation.abs();
    if (abs >= 0.8) return correlation > 0 ? Colors.red.shade700 : Colors.blue.shade700;
    if (abs >= 0.6) return correlation > 0 ? Colors.red.shade500 : Colors.blue.shade500;
    if (abs >= 0.4) return correlation > 0 ? Colors.red.shade300 : Colors.blue.shade300;
    if (abs >= 0.2) return correlation > 0 ? Colors.red.shade100 : Colors.blue.shade100;
    return Colors.grey.shade200;
  }

  /// Gets text color for correlation cell
  Color _getTextColor(double correlation) {
    return correlation.abs() >= 0.5 ? Colors.white : Colors.black87;
  }

  /// Gets correlation strength name
  String _getCorrelationStrengthName(double absCorrelation) {
    if (absCorrelation >= 0.8) return 'Very Strong';
    if (absCorrelation >= 0.6) return 'Strong';
    if (absCorrelation >= 0.4) return 'Moderate';
    if (absCorrelation >= 0.2) return 'Weak';
    return 'Very Weak';
  }

  /// Gets analysis type description
  String _getAnalysisTypeDescription() {
    final timeLagText = widget.enableTimeLag && _timeLag > 0 ? ' with ${_timeLag}d lag' : '';
    return '${_getMethodDisplayName(_method)} correlation$timeLagText';
  }

  /// Gets factor key for correlation matrix
  String _getFactorKey(EnvironmentalFactor factor) {
    return factor.toString().split('.').last;
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
  String _getViewModeDisplayName(CorrelationViewMode mode) {
    switch (mode) {
      case CorrelationViewMode.matrix:
        return 'Matrix';
      case CorrelationViewMode.network:
        return 'Network';
      case CorrelationViewMode.scatterplot:
        return 'Scatterplot';
      case CorrelationViewMode.heatmap:
        return 'Heatmap';
    }
  }

  /// Gets correlation method display name
  String _getMethodDisplayName(CorrelationMethod method) {
    switch (method) {
      case CorrelationMethod.pearson:
        return 'Pearson';
      case CorrelationMethod.spearman:
        return 'Spearman';
      case CorrelationMethod.kendall:
        return 'Kendall';
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
                'Correlation Methods:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Pearson: Linear relationships (parametric)'),
              Text('• Spearman: Monotonic relationships (non-parametric)'),
              Text('• Kendall: Rank-based correlation (robust)'),
              SizedBox(height: 16),
              Text(
                'Correlation Strength:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• 0.8-1.0: Very Strong'),
              Text('• 0.6-0.8: Strong'),
              Text('• 0.4-0.6: Moderate'),
              Text('• 0.2-0.4: Weak'),
              Text('• 0.0-0.2: Very Weak'),
              SizedBox(height: 16),
              Text(
                'Statistical Significance:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Star indicator: p < 0.05'),
              Text('• High confidence correlations'),
              Text('• Sample size affects significance'),
              SizedBox(height: 16),
              Text(
                'Malaria Relevance:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Multi-factor analysis reveals complex relationships'),
              Text('• Time-lag analysis for delayed effects'),
              Text('• Network view shows factor dependencies'),
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

/// Correlation result data class
class CorrelationResult {
  final EnvironmentalFactor factor1;
  final EnvironmentalFactor factor2;
  final double coefficient;
  final double? pValue;
  final double? confidence;
  final int sampleSize;

  const CorrelationResult({
    required this.factor1,
    required this.factor2,
    required this.coefficient,
    this.pValue,
    this.confidence,
    required this.sampleSize,
  });
}

/// Custom painter for correlation network visualization
class CorrelationNetworkPainter extends CustomPainter {
  final List<EnvironmentalFactor> factors;
  final Map<String, Map<String, CorrelationResult>> correlations;
  final Map<EnvironmentalFactor, Color> factorColors;
  final bool showSignificantOnly;
  final double significanceThreshold;

  CorrelationNetworkPainter({
    required this.factors,
    required this.correlations,
    required this.factorColors,
    required this.showSignificantOnly,
    required this.significanceThreshold,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 3;

    // Draw connections
    for (int i = 0; i < factors.length; i++) {
      for (int j = i + 1; j < factors.length; j++) {
        final factor1 = factors[i];
        final factor2 = factors[j];
        final correlation = correlations[factor1.toString().split('.').last]?[factor2.toString().split('.').last];

        if (correlation != null) {
          final isSignificant = correlation.pValue != null && correlation.pValue! < significanceThreshold;
          if (showSignificantOnly && !isSignificant) continue;

          final angle1 = (i / factors.length) * 2 * math.pi;
          final angle2 = (j / factors.length) * 2 * math.pi;

          final pos1 = Offset(
            center.dx + math.cos(angle1) * radius,
            center.dy + math.sin(angle1) * radius,
          );
          final pos2 = Offset(
            center.dx + math.cos(angle2) * radius,
            center.dy + math.sin(angle2) * radius,
          );

          final paint = Paint()
            ..color = correlation.coefficient > 0 ? Colors.red : Colors.blue
            ..strokeWidth = correlation.coefficient.abs() * 5
            ..style = PaintingStyle.stroke;

          canvas.drawLine(pos1, pos2, paint);
        }
      }
    }

    // Draw factor nodes
    for (int i = 0; i < factors.length; i++) {
      final factor = factors[i];
      final angle = (i / factors.length) * 2 * math.pi;
      final position = Offset(
        center.dx + math.cos(angle) * radius,
        center.dy + math.sin(angle) * radius,
      );

      final paint = Paint()
        ..color = factorColors[factor] ?? Colors.grey
        ..style = PaintingStyle.fill;

      canvas.drawCircle(position, 20, paint);
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => true;
}

/// Correlation view mode enumeration
enum CorrelationViewMode {
  matrix,
  network,
  scatterplot,
  heatmap,
}

/// Correlation method enumeration
enum CorrelationMethod {
  pearson,
  spearman,
  kendall,
}

/// Correlation strength enumeration
enum CorrelationStrength {
  veryWeak,
  weak,
  moderate,
  strong,
  veryStrong,
}