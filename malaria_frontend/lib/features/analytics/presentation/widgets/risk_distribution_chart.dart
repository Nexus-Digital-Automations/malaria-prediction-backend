/// Risk distribution chart widget using fl_chart
///
/// This widget displays risk distribution data using pie charts
/// to show the proportion of different risk levels across regions.
///
/// Usage:
/// ```dart
/// RiskDistributionChart(
///   riskTrends: riskData,
///   height: 300,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../domain/entities/analytics_data.dart';

/// Risk distribution chart widget
class RiskDistributionChart extends StatefulWidget {
  /// Risk trend data to display
  final List<RiskTrend> riskTrends;

  /// Chart height
  final double height;

  /// Constructor requiring risk trends data
  const RiskDistributionChart({
    super.key,
    required this.riskTrends,
    this.height = 300,
  });

  @override
  State<RiskDistributionChart> createState() => _RiskDistributionChartState();
}

class _RiskDistributionChartState extends State<RiskDistributionChart> {
  /// Touched section index for interaction
  int _touchedIndex = -1;

  /// Color mapping for risk levels
  final Map<RiskLevel, Color> _riskColors = {
    RiskLevel.low: Colors.green,
    RiskLevel.medium: Colors.orange,
    RiskLevel.high: Colors.red,
    RiskLevel.critical: Colors.purple,
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
            Expanded(
              child: widget.riskTrends.isEmpty
                  ? _buildNoDataMessage()
                  : _buildChart(),
            ),
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
      'Risk Distribution',
      style: Theme.of(context).textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.bold,
      ),
    );
  }

  /// Builds the pie chart
  Widget _buildChart() {
    final riskCounts = _calculateRiskCounts();
    final total = riskCounts.values.fold(0, (sum, count) => sum + count);

    if (total == 0) {
      return _buildNoDataMessage();
    }

    return Row(
      children: [
        Expanded(
          flex: 2,
          child: PieChart(
            PieChartData(
              pieTouchData: PieTouchData(
                touchCallback: (FlTouchEvent event, pieTouchResponse) {
                  setState(() {
                    if (!event.isInterestedForInteractions ||
                        pieTouchResponse == null ||
                        pieTouchResponse.touchedSection == null) {
                      _touchedIndex = -1;
                      return;
                    }
                    _touchedIndex = pieTouchResponse.touchedSection!.touchedSectionIndex;
                  });
                },
              ),
              borderData: FlBorderData(show: false),
              sectionsSpace: 2,
              centerSpaceRadius: 40,
              sections: _buildPieSections(riskCounts, total),
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildStatistics(riskCounts, total),
        ),
      ],
    );
  }

  /// Builds pie chart sections
  List<PieChartSectionData> _buildPieSections(
    Map<RiskLevel, int> riskCounts,
    int total,
  ) {
    final sections = <PieChartSectionData>[];
    int index = 0;

    for (final entry in riskCounts.entries) {
      final riskLevel = entry.key;
      final count = entry.value;
      final percentage = (count / total) * 100;
      final isTouched = index == _touchedIndex;

      sections.add(
        PieChartSectionData(
          color: _riskColors[riskLevel],
          value: count.toDouble(),
          title: '${percentage.toStringAsFixed(1)}%',
          radius: isTouched ? 60 : 50,
          titleStyle: TextStyle(
            fontSize: isTouched ? 18 : 14,
            fontWeight: FontWeight.bold,
            color: Colors.white,
            shadows: const [
              Shadow(
                color: Colors.black26,
                offset: Offset(1, 1),
                blurRadius: 2,
              ),
            ],
          ),
          titlePositionPercentageOffset: 0.6,
        ),
      );
      index++;
    }

    return sections;
  }

  /// Builds statistics panel
  Widget _buildStatistics(Map<RiskLevel, int> riskCounts, int total) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Statistics',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          'Total Areas: $total',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        ...riskCounts.entries.map((entry) {
          final riskLevel = entry.key;
          final count = entry.value;
          final percentage = (count / total) * 100;

          return Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: _riskColors[riskLevel],
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${_getRiskLevelDisplayName(riskLevel)}: $count (${percentage.toStringAsFixed(1)}%)',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  /// Builds legend for risk levels
  Widget _buildLegend() {
    final riskCounts = _calculateRiskCounts();

    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: riskCounts.keys.map((riskLevel) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _riskColors[riskLevel],
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              _getRiskLevelDisplayName(riskLevel),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      }).toList(),
    );
  }

  /// Calculates risk level counts from trends data
  Map<RiskLevel, int> _calculateRiskCounts() {
    final counts = <RiskLevel, int>{
      RiskLevel.low: 0,
      RiskLevel.medium: 0,
      RiskLevel.high: 0,
      RiskLevel.critical: 0,
    };

    for (final trend in widget.riskTrends) {
      counts[trend.riskLevel] = (counts[trend.riskLevel] ?? 0) + 1;
    }

    // Remove zero counts for cleaner display
    counts.removeWhere((key, value) => value == 0);

    return counts;
  }

  /// Gets display name for risk level
  String _getRiskLevelDisplayName(RiskLevel riskLevel) {
    switch (riskLevel) {
      case RiskLevel.low:
        return 'Low Risk';
      case RiskLevel.medium:
        return 'Medium Risk';
      case RiskLevel.high:
        return 'High Risk';
      case RiskLevel.critical:
        return 'Critical Risk';
    }
  }

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.donut_large_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha:0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No risk distribution data available',
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