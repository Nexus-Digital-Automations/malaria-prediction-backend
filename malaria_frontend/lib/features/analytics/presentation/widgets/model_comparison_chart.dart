/// Model comparison chart widget using fl_chart BarChart
///
/// This widget displays comparative performance metrics across multiple models
/// using bar charts to visualize model performance differences.
///
/// Usage:
/// ```dart
/// ModelComparisonChart(
///   models: modelPerformanceList,
///   height: 350,
///   selectedMetric: 'accuracy',
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../domain/entities/prediction_metrics.dart';

/// Model comparison chart widget for performance analysis
class ModelComparisonChart extends StatefulWidget {
  /// List of model performance data to compare
  final List<ModelPerformance> models;

  /// Chart height
  final double height;

  /// Currently selected metric for comparison
  final String selectedMetric;

  /// Available metrics for comparison
  final List<String> availableMetrics;

  /// Whether to show metric selector
  final bool showMetricSelector;

  /// Whether to show model status indicators
  final bool showStatusIndicators;

  /// Custom color palette for models
  final List<Color>? modelColors;

  /// Constructor with required model data
  const ModelComparisonChart({
    super.key,
    required this.models,
    this.height = 350,
    this.selectedMetric = 'accuracy',
    this.availableMetrics = const ['accuracy', 'precision', 'recall', 'f1Score'],
    this.showMetricSelector = true,
    this.showStatusIndicators = true,
    this.modelColors,
  });

  @override
  State<ModelComparisonChart> createState() => _ModelComparisonChartState();
}

class _ModelComparisonChartState extends State<ModelComparisonChart> {
  /// Currently selected metric
  late String _selectedMetric;

  /// Touched bar index for interaction
  int _touchedBarIndex = -1;

  /// Default color palette for models
  static const List<Color> _defaultColors = [
    Color(0xFF2196F3), // Blue
    Color(0xFF4CAF50), // Green
    Color(0xFFFF9800), // Orange
    Color(0xFFE91E63), // Pink
    Color(0xFF9C27B0), // Purple
    Color(0xFF00BCD4), // Cyan
    Color(0xFFFF5722), // Deep Orange
    Color(0xFF795548), // Brown
    Color(0xFF607D8B), // Blue Grey
    Color(0xFF8BC34A), // Light Green
  ];

  @override
  void initState() {
    super.initState();
    _selectedMetric = widget.selectedMetric;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

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
            _buildHeader(theme),
            if (widget.showMetricSelector) ...[
              const SizedBox(height: 12),
              _buildMetricSelector(theme),
            ],
            const SizedBox(height: 16),
            Expanded(
              child: widget.models.isEmpty
                  ? _buildNoDataMessage(theme)
                  : _buildChart(theme.colorScheme),
            ),
            const SizedBox(height: 8),
            _buildLegend(theme),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header
  Widget _buildHeader(ThemeData theme) {
    final bestModel = _getBestPerformingModel();
    final metricDisplay = _getMetricDisplayName(_selectedMetric);

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Model Performance Comparison',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '${widget.models.length} models • $metricDisplay',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          ],
        ),
        if (bestModel != null)
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'Best: ${bestModel.modelName}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${(_getMetricValue(bestModel, _selectedMetric) * 100).toStringAsFixed(1)}%',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
              ),
            ],
          ),
      ],
    );
  }

  /// Builds metric selector dropdown
  Widget _buildMetricSelector(ThemeData theme) {
    return Row(
      children: [
        Text(
          'Metric: ',
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            border: Border.all(color: theme.colorScheme.outline),
            borderRadius: BorderRadius.circular(8),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: _selectedMetric,
              onChanged: (String? newValue) {
                if (newValue != null) {
                  setState(() {
                    _selectedMetric = newValue;
                  });
                }
              },
              items: widget.availableMetrics.map((String metric) {
                return DropdownMenuItem<String>(
                  value: metric,
                  child: Text(
                    _getMetricDisplayName(metric),
                    style: theme.textTheme.bodyMedium,
                  ),
                );
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }

  /// Builds the bar chart
  Widget _buildChart(ColorScheme colorScheme) {
    if (widget.models.isEmpty) {
      return _buildNoDataMessage(Theme.of(context));
    }

    final barGroups = _buildBarGroups();
    final maxValue = _getMaxValue();

    return BarChart(
      BarChartData(
        barTouchData: _buildTouchData(colorScheme),
        titlesData: _buildTitlesData(colorScheme),
        borderData: FlBorderData(show: false),
        gridData: _buildGridData(colorScheme),
        barGroups: barGroups,
        maxY: maxValue * 1.1, // Add 10% padding
        minY: 0,
        groupsSpace: 12,
      ),
    );
  }

  /// Builds touch interaction data
  BarTouchData _buildTouchData(ColorScheme colorScheme) {
    return BarTouchData(
      touchCallback: (FlTouchEvent event, BarTouchResponse? touchResponse) {
        setState(() {
          if (touchResponse == null || touchResponse.spot == null) {
            _touchedBarIndex = -1;
            return;
          }
          _touchedBarIndex = touchResponse.spot!.touchedBarGroupIndex;
        });
      },
      touchTooltipData: BarTouchTooltipData(
        getTooltipColor: (_) => colorScheme.inverseSurface,
        tooltipRoundedRadius: 8,
        getTooltipItem: _buildTooltipItem,
      ),
    );
  }

  /// Builds tooltip item for touch interaction
  BarTooltipItem _buildTooltipItem(
    BarChartGroupData group,
    int groupIndex,
    BarChartRodData rod,
    int rodIndex,
  ) {
    if (groupIndex >= 0 && groupIndex < widget.models.length) {
      final model = widget.models[groupIndex];
      final value = _getMetricValue(model, _selectedMetric);

      return BarTooltipItem(
        '${model.modelName}\n'
        '${_getMetricDisplayName(_selectedMetric)}: ${(value * 100).toStringAsFixed(1)}%\n'
        'Status: ${_getStatusDisplayName(model.status)}',
        TextStyle(
          color: Theme.of(context).colorScheme.onInverseSurface,
          fontWeight: FontWeight.w500,
          fontSize: 12,
        ),
      );
    }
    return BarTooltipItem('', const TextStyle());
  }

  /// Builds grid data configuration
  FlGridData _buildGridData(ColorScheme colorScheme) {
    return FlGridData(
      show: true,
      drawHorizontalLine: true,
      drawVerticalLine: false,
      horizontalInterval: 0.1,
      getDrawingHorizontalLine: (value) {
        return FlLine(
          color: colorScheme.outline.withValues(alpha: 0.2),
          strokeWidth: 1,
        );
      },
    );
  }

  /// Builds titles data for axes
  FlTitlesData _buildTitlesData(ColorScheme colorScheme) {
    return FlTitlesData(
      leftTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 50,
          interval: 0.1,
          getTitlesWidget: (value, meta) {
            return Text(
              '${(value * 100).toInt()}%',
              style: TextStyle(
                color: colorScheme.onSurface.withValues(alpha: 0.6),
                fontSize: 11,
              ),
            );
          },
        ),
        axisNameWidget: Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Text(
            _getMetricDisplayName(_selectedMetric),
            style: TextStyle(
              color: colorScheme.onSurface.withValues(alpha: 0.8),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ),
      bottomTitles: AxisTitles(
        sideTitles: SideTitles(
          showTitles: true,
          reservedSize: 60,
          getTitlesWidget: (value, meta) {
            final index = value.toInt();
            if (index >= 0 && index < widget.models.length) {
              final model = widget.models[index];
              return Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Column(
                  children: [
                    Text(
                      model.modelName,
                      style: TextStyle(
                        color: colorScheme.onSurface.withValues(alpha: 0.7),
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    if (widget.showStatusIndicators) ...[
                      const SizedBox(height: 2),
                      _buildStatusIndicator(model.status, colorScheme),
                    ],
                  ],
                ),
              );
            }
            return const SizedBox.shrink();
          },
        ),
      ),
      rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
    );
  }

  /// Builds status indicator
  Widget _buildStatusIndicator(ModelStatus status, ColorScheme colorScheme) {
    Color statusColor;
    switch (status) {
      case ModelStatus.production:
        statusColor = Colors.green;
        break;
      case ModelStatus.staging:
        statusColor = Colors.orange;
        break;
      case ModelStatus.testing:
        statusColor = Colors.blue;
        break;
      case ModelStatus.development:
        statusColor = Colors.grey;
        break;
      case ModelStatus.deprecated:
        statusColor = Colors.red;
        break;
      case ModelStatus.retired:
        statusColor = Colors.black54;
        break;
    }

    return Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(
        color: statusColor,
        shape: BoxShape.circle,
      ),
    );
  }

  /// Builds bar groups for the chart
  List<BarChartGroupData> _buildBarGroups() {
    final colors = widget.modelColors ?? _defaultColors;

    return widget.models.asMap().entries.map((entry) {
      final index = entry.key;
      final model = entry.value;
      final value = _getMetricValue(model, _selectedMetric);
      final isTouched = index == _touchedBarIndex;
      final color = colors[index % colors.length];

      return BarChartGroupData(
        x: index,
        barRods: [
          BarChartRodData(
            toY: value,
            color: color,
            width: isTouched ? 20 : 16,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(4),
              topRight: Radius.circular(4),
            ),
            backDrawRodData: BackgroundBarChartRodData(
              show: true,
              toY: 1.0, // Max value (100%)
              color: color.withValues(alpha: 0.1),
            ),
          ),
        ],
      );
    }).toList();
  }

  /// Gets metric value from model performance
  double _getMetricValue(ModelPerformance model, String metric) {
    switch (metric) {
      case 'accuracy':
        return model.accuracy;
      case 'precision':
        return model.kpis['precision'] ?? 0.0;
      case 'recall':
        return model.kpis['recall'] ?? 0.0;
      case 'f1Score':
        return model.kpis['f1Score'] ?? 0.0;
      default:
        return model.kpis[metric] ?? 0.0;
    }
  }

  /// Gets display name for metric
  String _getMetricDisplayName(String metric) {
    switch (metric) {
      case 'accuracy':
        return 'Accuracy';
      case 'precision':
        return 'Precision';
      case 'recall':
        return 'Recall';
      case 'f1Score':
        return 'F1 Score';
      default:
        return metric.replaceAll('_', ' ').split(' ').map((word) =>
          word.isEmpty ? '' : word[0].toUpperCase() + word.substring(1)).join(' ');
    }
  }

  /// Gets display name for model status
  String _getStatusDisplayName(ModelStatus status) {
    switch (status) {
      case ModelStatus.production:
        return 'Production';
      case ModelStatus.staging:
        return 'Staging';
      case ModelStatus.testing:
        return 'Testing';
      case ModelStatus.development:
        return 'Development';
      case ModelStatus.deprecated:
        return 'Deprecated';
      case ModelStatus.retired:
        return 'Retired';
    }
  }

  /// Gets the maximum value for chart scaling
  double _getMaxValue() {
    if (widget.models.isEmpty) return 1.0;

    return widget.models
        .map((model) => _getMetricValue(model, _selectedMetric))
        .reduce((a, b) => a > b ? a : b);
  }

  /// Gets the best performing model
  ModelPerformance? _getBestPerformingModel() {
    if (widget.models.isEmpty) return null;

    return widget.models.reduce((a, b) {
      final aValue = _getMetricValue(a, _selectedMetric);
      final bValue = _getMetricValue(b, _selectedMetric);
      return aValue > bValue ? a : b;
    });
  }

  /// Builds legend for model colors
  Widget _buildLegend(ThemeData theme) {
    final colors = widget.modelColors ?? _defaultColors;

    return Wrap(
      spacing: 12,
      runSpacing: 8,
      children: widget.models.asMap().entries.take(5).map((entry) {
        final index = entry.key;
        final model = entry.value;
        final color = colors[index % colors.length];

        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 4),
            Text(
              model.modelName,
              style: theme.textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.bar_chart_outlined,
            size: 48,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No model comparison data available',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Performance comparison will appear when multiple models are available',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}