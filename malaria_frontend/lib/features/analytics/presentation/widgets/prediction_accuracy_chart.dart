/// Prediction accuracy chart widget using fl_chart
///
/// This widget displays prediction accuracy metrics using a line chart
/// with accuracy trends over time and breakdown by risk levels.
/// It uses fl_chart for smooth, interactive visualizations.
///
/// Usage:
/// ```dart
/// PredictionAccuracyChart(
///   accuracyData: predictionAccuracy,
///   height: 300,
///   showDetails: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Prediction accuracy chart widget
class PredictionAccuracyChart extends StatefulWidget {
  /// Prediction accuracy data to display
  final PredictionAccuracy accuracyData;

  /// Chart height
  final double height;

  /// Whether to show detailed breakdowns
  final bool showDetails;

  /// Whether to show interactive tooltips
  final bool showTooltips;

  /// Custom color scheme for the chart
  final List<Color>? colors;

  /// Constructor requiring accuracy data
  const PredictionAccuracyChart({
    super.key,
    required this.accuracyData,
    this.height = 300,
    this.showDetails = false,
    this.showTooltips = true,
    this.colors,
  });

  @override
  State<PredictionAccuracyChart> createState() => _PredictionAccuracyChartState();
}

class _PredictionAccuracyChartState extends State<PredictionAccuracyChart> {
  /// Currently selected chart view
  int _selectedIndex = 0;

  /// Chart view options
  final List<String> _chartViews = ['Trend', 'By Risk Level', 'Metrics'];

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
            Expanded(
              child: _buildChartContent(),
            ),
            if (widget.showDetails) ...[
              const SizedBox(height: 16),
              _buildDetailsSection(),
            ],
          ],
        ),
      ),
    );
  }

  /// Builds the chart header with title and view selector
  Widget _buildHeader() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Prediction Accuracy',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Overall: ${(widget.accuracyData.overall * 100).toInt()}%',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.primary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
        SegmentedButton<int>(
          selected: {_selectedIndex},
          onSelectionChanged: (Set<int> selection) {
            setState(() {
              _selectedIndex = selection.first;
            });
          },
          segments: _chartViews.asMap().entries.map((entry) {
            return ButtonSegment<int>(
              value: entry.key,
              label: Text(
                entry.value,
                style: const TextStyle(fontSize: 12),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  /// Builds the main chart content based on selected view
  Widget _buildChartContent() {
    switch (_selectedIndex) {
      case 0:
        return _buildTrendChart();
      case 1:
        return _buildRiskLevelChart();
      case 2:
        return _buildMetricsChart();
      default:
        return _buildTrendChart();
    }
  }

  /// Builds accuracy trend line chart
  Widget _buildTrendChart() {
    if (widget.accuracyData.trend.isEmpty) {
      return _buildNoDataMessage('No trend data available');
    }

    final spots = widget.accuracyData.trend.asMap().entries.map((entry) {
      return FlSpot(entry.key.toDouble(), entry.value.accuracy);
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
                '${(value * 100).toInt()}%',
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
                if (index >= 0 && index < widget.accuracyData.trend.length) {
                  final date = widget.accuracyData.trend[index].date;
                  return Text(
                    DateFormat('MMM d').format(date),
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
        minX: 0,
        maxX: (widget.accuracyData.trend.length - 1).toDouble(),
        minY: 0,
        maxY: 1,
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Theme.of(context).colorScheme.primary,
            barWidth: 3,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, percent, barData, index) {
                return FlDotCirclePainter(
                  radius: 4,
                  color: Theme.of(context).colorScheme.primary,
                  strokeWidth: 2,
                  strokeColor: Theme.of(context).colorScheme.surface,
                );
              },
            ),
            belowBarData: BarAreaData(
              show: true,
              color: Theme.of(context).colorScheme.primary.withValues(alpha:0.1),
            ),
          ),
        ],
        lineTouchData: widget.showTooltips
            ? LineTouchData(
                touchTooltipData: LineTouchTooltipData(
                  getTooltipItems: (touchedSpots) {
                    return touchedSpots.map((spot) {
                      final index = spot.x.toInt();
                      if (index >= 0 && index < widget.accuracyData.trend.length) {
                        final dataPoint = widget.accuracyData.trend[index];
                        return LineTooltipItem(
                          'Date: ${DateFormat('MMM d, y').format(dataPoint.date)}\n'
                          'Accuracy: ${(dataPoint.accuracy * 100).toStringAsFixed(1)}%\n'
                          'Sample Size: ${dataPoint.sampleSize}',
                          TextStyle(
                            color: Theme.of(context).colorScheme.onSurface,
                            fontSize: 12,
                          ),
                        );
                      }
                      return null;
                    }).toList();
                  },
                ),
              )
            : const LineTouchData(enabled: false),
      ),
    );
  }

  /// Builds risk level accuracy bar chart
  Widget _buildRiskLevelChart() {
    if (widget.accuracyData.byRiskLevel.isEmpty) {
      return _buildNoDataMessage('No risk level data available');
    }

    final entries = widget.accuracyData.byRiskLevel.entries.toList();
    final colors = widget.colors ??
        [
          Colors.green,
          Colors.orange,
          Colors.red,
          Colors.purple,
        ];

    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: 1,
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
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
                '${(value * 100).toInt()}%',
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
                if (index >= 0 && index < entries.length) {
                  return Text(
                    entries[index].key.toUpperCase(),
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
        barGroups: entries.asMap().entries.map((entry) {
          final index = entry.key;
          final accuracy = entry.value.value;
          final color = colors[index % colors.length];

          return BarChartGroupData(
            x: index,
            barRods: [
              BarChartRodData(
                toY: accuracy,
                color: color,
                width: 20,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
              ),
            ],
          );
        }).toList(),
        barTouchData: widget.showTooltips
            ? BarTouchData(
                touchTooltipData: BarTouchTooltipData(
                  getTooltipItem: (group, groupIndex, rod, rodIndex) {
                    final entry = entries[group.x.toInt()];
                    return BarTooltipItem(
                      'Risk Level: ${entry.key.toUpperCase()}\n'
                      'Accuracy: ${(entry.value * 100).toStringAsFixed(1)}%',
                      TextStyle(
                        color: Theme.of(context).colorScheme.onSurface,
                        fontSize: 12,
                      ),
                    );
                  },
                ),
              )
            : BarTouchData(enabled: false),
      ),
    );
  }

  /// Builds metrics overview chart
  Widget _buildMetricsChart() {
    final metrics = [
      ('Precision', widget.accuracyData.precision),
      ('Recall', widget.accuracyData.recall),
      ('F1 Score', widget.accuracyData.f1Score),
    ];

    return Column(
      children: [
        Expanded(
          child: Row(
            children: metrics.asMap().entries.map((entry) {
              final index = entry.key;
              final metric = entry.value;
              final colors = [
                Theme.of(context).colorScheme.primary,
                Theme.of(context).colorScheme.secondary,
                Theme.of(context).colorScheme.tertiary,
              ];

              return Expanded(
                child: Container(
                  margin: EdgeInsets.only(
                    right: index < metrics.length - 1 ? 8 : 0,
                  ),
                  child: _buildMetricCard(
                    metric.$1,
                    metric.$2,
                    colors[index],
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 16),
        _buildOverallAccuracyIndicator(),
      ],
    );
  }

  /// Builds individual metric card
  Widget _buildMetricCard(String title, double value, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha:0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha:0.3)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            '${(value * 100).toStringAsFixed(1)}%',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.bold,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: value,
            backgroundColor: color.withValues(alpha:0.2),
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ],
      ),
    );
  }

  /// Builds overall accuracy circular indicator
  Widget _buildOverallAccuracyIndicator() {
    return SizedBox(
      height: 120,
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 100,
            height: 100,
            child: CircularProgressIndicator(
              value: widget.accuracyData.overall,
              strokeWidth: 8,
              backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
              valueColor: AlwaysStoppedAnimation<Color>(
                Theme.of(context).colorScheme.primary,
              ),
            ),
          ),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '${(widget.accuracyData.overall * 100).toInt()}%',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              Text(
                'Overall',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds details section with additional information
  Widget _buildDetailsSection() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha:0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildDetailItem(
              'Total Samples',
              widget.accuracyData.trend.isNotEmpty
                  ? widget.accuracyData.trend.last.sampleSize.toString()
                  : 'N/A',
            ),
          ),
          Expanded(
            child: _buildDetailItem(
              'Risk Levels',
              widget.accuracyData.byRiskLevel.length.toString(),
            ),
          ),
          Expanded(
            child: _buildDetailItem(
              'Data Points',
              widget.accuracyData.trend.length.toString(),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds individual detail item
  Widget _buildDetailItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.info_outline,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha:0.5),
          ),
          const SizedBox(height: 16),
          Text(
            message,
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