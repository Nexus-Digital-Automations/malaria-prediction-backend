/// Population risk assessment widget for malaria outbreak analysis
///
/// This widget displays comprehensive population risk assessments including
/// demographic breakdowns, vulnerability indicators, and risk distribution
/// across different population segments for public health planning.
///
/// Usage:
/// ```dart
/// PopulationRiskWidget(
///   riskTrends: riskTrends,
///   height: 350,
///   region: 'Kenya',
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Population risk assessment widget with demographic analysis
class PopulationRiskWidget extends StatefulWidget {
  /// Risk trend data to analyze
  final List<RiskTrend> riskTrends;

  /// Widget height
  final double height;

  /// Geographic region for analysis
  final String? region;

  /// Whether to show demographic breakdowns
  final bool showDemographics;

  /// Whether to show vulnerability indicators
  final bool showVulnerabilityIndicators;

  /// Population view mode
  final PopulationViewMode viewMode;

  /// Constructor requiring risk trends data
  const PopulationRiskWidget({
    super.key,
    required this.riskTrends,
    this.height = 350,
    this.region,
    this.showDemographics = true,
    this.showVulnerabilityIndicators = true,
    this.viewMode = PopulationViewMode.overview,
  });

  @override
  State<PopulationRiskWidget> createState() => _PopulationRiskWidgetState();
}

class _PopulationRiskWidgetState extends State<PopulationRiskWidget>
    with TickerProviderStateMixin {
  /// Current population view mode
  late PopulationViewMode _currentViewMode;

  /// Animation controller for transitions
  late AnimationController _animationController;

  /// Population risk segments
  List<PopulationSegment> _populationSegments = [];

  /// Risk distribution data
  Map<RiskLevel, PopulationRiskData> _riskDistribution = {};

  /// Vulnerability indicators
  List<VulnerabilityIndicator> _vulnerabilityIndicators = [];

  /// Selected population segment for detailed view
  PopulationSegment? _selectedSegment;

  /// Demographic categories for analysis
  final List<DemographicCategory> _demographics = [
    DemographicCategory('Children (<5 years)', 0.15, VulnerabilityLevel.high),
    DemographicCategory('Children (5-14 years)', 0.25, VulnerabilityLevel.medium),
    DemographicCategory('Adults (15-64 years)', 0.55, VulnerabilityLevel.low),
    DemographicCategory('Elderly (65+ years)', 0.05, VulnerabilityLevel.high),
  ];

  @override
  void initState() {
    super.initState();
    _currentViewMode = widget.viewMode;
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _processPopulationData();
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(PopulationRiskWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.riskTrends != widget.riskTrends) {
      _processPopulationData();
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
            const SizedBox(height: 12),
            Expanded(child: _buildMainContent()),
            if (_selectedSegment != null) _buildSelectedSegmentInfo(),
          ],
        ),
      ),
    );
  }

  /// Builds the widget header with title and key metrics
  Widget _buildHeader() {
    final totalPopulation = _riskDistribution.values
        .fold(0, (sum, data) => sum + data.populationCount);
    final highRiskPopulation = (_riskDistribution[RiskLevel.high]?.populationCount ?? 0) +
        (_riskDistribution[RiskLevel.critical]?.populationCount ?? 0);

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Population Risk Assessment',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '${widget.region ?? 'Region'} • ${_formatPopulation(totalPopulation)} total population',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        _buildRiskIndicator(highRiskPopulation, totalPopulation),
      ],
    );
  }

  /// Builds high-risk population indicator
  Widget _buildRiskIndicator(int highRiskPop, int totalPop) {
    final riskPercentage = totalPop > 0 ? (highRiskPop / totalPop) * 100 : 0.0;
    final color = _getRiskPercentageColor(riskPercentage);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Text(
            '${riskPercentage.toStringAsFixed(1)}%',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            'High Risk',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
            ),
          ),
          Text(
            _formatPopulation(highRiskPop),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color.withValues(alpha: 0.8),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds view mode selector
  Widget _buildViewModeSelector() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: PopulationViewMode.values.map((mode) {
          final isSelected = mode == _currentViewMode;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _getViewModeIcon(mode),
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                  Text(_getViewModeDisplayName(mode)),
                ],
              ),
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
    );
  }

  /// Builds main content based on view mode
  Widget _buildMainContent() {
    if (_riskDistribution.isEmpty) {
      return _buildNoDataMessage();
    }

    switch (_currentViewMode) {
      case PopulationViewMode.overview:
        return _buildOverviewView();
      case PopulationViewMode.riskDistribution:
        return _buildRiskDistributionView();
      case PopulationViewMode.demographics:
        return _buildDemographicsView();
      case PopulationViewMode.vulnerability:
        return _buildVulnerabilityView();
    }
  }

  /// Builds overview view with key metrics and charts
  Widget _buildOverviewView() {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: _buildRiskDistributionChart(),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            children: [
              Expanded(child: _buildRiskBreakdown()),
              const SizedBox(height: 16),
              if (widget.showVulnerabilityIndicators)
                Expanded(child: _buildVulnerabilityOverview()),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds risk distribution pie chart
  Widget _buildRiskDistributionChart() {
    return Column(
      children: [
        Text(
          'Population by Risk Level',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: PieChart(
            PieChartData(
              sectionsSpace: 2,
              centerSpaceRadius: 60,
              sections: _buildPieChartSections(),
              pieTouchData: PieTouchData(
                touchCallback: (FlTouchEvent event, pieTouchResponse) {
                  if (pieTouchResponse?.touchedSection != null) {
                    final sectionIndex = pieTouchResponse!.touchedSection!.touchedSectionIndex;
                    final riskLevels = RiskLevel.values;
                    if (sectionIndex < riskLevels.length) {
                      _handleRiskLevelSelection(riskLevels[sectionIndex]);
                    }
                  }
                },
              ),
            ),
          ),
        ),
      ],
    );
  }

  /// Builds pie chart sections for risk distribution
  List<PieChartSectionData> _buildPieChartSections() {
    final total = _riskDistribution.values
        .fold(0, (sum, data) => sum + data.populationCount);

    if (total == 0) return [];

    return RiskLevel.values.map((level) {
      final data = _riskDistribution[level];
      if (data == null || data.populationCount == 0) {
        return PieChartSectionData(
          color: Colors.transparent,
          value: 0,
          title: '',
          radius: 0,
        );
      }

      final percentage = (data.populationCount / total) * 100;
      final color = _getRiskLevelColor(level);

      return PieChartSectionData(
        color: color,
        value: data.populationCount.toDouble(),
        title: '${percentage.toStringAsFixed(1)}%',
        radius: 80,
        titleStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
        titlePositionPercentageOffset: 0.6,
      );
    }).where((section) => section.value > 0).toList();
  }

  /// Builds risk level breakdown list
  Widget _buildRiskBreakdown() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Risk Distribution',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: RiskLevel.values.map((level) {
              final data = _riskDistribution[level];
              if (data == null) return const SizedBox.shrink();

              return _buildRiskBreakdownItem(level, data);
            }).toList(),
          ),
        ),
      ],
    );
  }

  /// Builds individual risk breakdown item
  Widget _buildRiskBreakdownItem(RiskLevel level, PopulationRiskData data) {
    final color = _getRiskLevelColor(level);
    final totalPop = _riskDistribution.values
        .fold(0, (sum, d) => sum + d.populationCount);
    final percentage = totalPop > 0 ? (data.populationCount / totalPop) * 100 : 0.0;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: color.withValues(alpha: 0.3)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _getRiskLevelDisplayName(level),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  '${_formatPopulation(data.populationCount)} (${percentage.toStringAsFixed(1)}%)',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
              ],
            ),
          ),
          Text(
            'Avg Risk: ${(data.averageRisk * 100).toStringAsFixed(0)}%',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds vulnerability overview
  Widget _buildVulnerabilityOverview() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Vulnerability Indicators',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: _vulnerabilityIndicators.map((indicator) {
              return _buildVulnerabilityIndicatorItem(indicator);
            }).toList(),
          ),
        ),
      ],
    );
  }

  /// Builds individual vulnerability indicator item
  Widget _buildVulnerabilityIndicatorItem(VulnerabilityIndicator indicator) {
    final color = _getVulnerabilityLevelColor(indicator.level);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(
            indicator.icon,
            color: color,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              indicator.name,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: color,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Text(
            '${(indicator.score * 100).toStringAsFixed(0)}%',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds risk distribution detailed view
  Widget _buildRiskDistributionView() {
    return Column(
      children: [
        Expanded(
          flex: 2,
          child: _buildRiskDistributionChart(),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: _buildDetailedRiskTable(),
        ),
      ],
    );
  }

  /// Builds detailed risk table
  Widget _buildDetailedRiskTable() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Detailed Risk Analysis',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: SingleChildScrollView(
            child: Table(
              border: TableBorder.all(
                color: Theme.of(context).dividerColor,
                width: 1,
              ),
              columnWidths: const {
                0: FlexColumnWidth(2),
                1: FlexColumnWidth(2),
                2: FlexColumnWidth(2),
                3: FlexColumnWidth(2),
              },
              children: [
                TableRow(
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.3),
                  ),
                  children: [
                    _buildTableHeader('Risk Level'),
                    _buildTableHeader('Population'),
                    _buildTableHeader('Percentage'),
                    _buildTableHeader('Avg. Risk'),
                  ],
                ),
                ...RiskLevel.values.map((level) {
                  final data = _riskDistribution[level];
                  if (data == null) return const TableRow(children: []);

                  final totalPop = _riskDistribution.values
                      .fold(0, (sum, d) => sum + d.populationCount);
                  final percentage = totalPop > 0 ? (data.populationCount / totalPop) * 100 : 0.0;

                  return TableRow(
                    children: [
                      _buildTableCell(_getRiskLevelDisplayName(level)),
                      _buildTableCell(_formatPopulation(data.populationCount)),
                      _buildTableCell('${percentage.toStringAsFixed(1)}%'),
                      _buildTableCell('${(data.averageRisk * 100).toStringAsFixed(1)}%'),
                    ],
                  );
                }),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Builds demographics view
  Widget _buildDemographicsView() {
    return Row(
      children: [
        Expanded(
          child: _buildDemographicChart(),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildDemographicBreakdown(),
        ),
      ],
    );
  }

  /// Builds demographic distribution chart
  Widget _buildDemographicChart() {
    return Column(
      children: [
        Text(
          'Demographic Risk Distribution',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: BarChart(
            BarChartData(
              alignment: BarChartAlignment.spaceAround,
              maxY: 1.0,
              barTouchData: BarTouchData(enabled: true),
              titlesData: FlTitlesData(
                show: true,
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      if (value.toInt() < _demographics.length) {
                        return Text(
                          _demographics[value.toInt()].name.split(' ').first,
                          style: Theme.of(context).textTheme.bodySmall,
                        );
                      }
                      return const Text('');
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        '${(value * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodySmall,
                      );
                    },
                  ),
                ),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              gridData: const FlGridData(show: true),
              borderData: FlBorderData(
                show: true,
                border: Border.all(color: Theme.of(context).dividerColor),
              ),
              barGroups: _buildDemographicBarGroups(),
            ),
          ),
        ),
      ],
    );
  }

  /// Builds demographic bar groups
  List<BarChartGroupData> _buildDemographicBarGroups() {
    return _demographics.asMap().entries.map((entry) {
      final index = entry.key;
      final demographic = entry.value;
      final color = _getVulnerabilityLevelColor(demographic.vulnerabilityLevel);

      return BarChartGroupData(
        x: index,
        barRods: [
          BarChartRodData(
            toY: demographic.proportion,
            color: color,
            width: 20,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
          ),
        ],
      );
    }).toList();
  }

  /// Builds demographic breakdown
  Widget _buildDemographicBreakdown() {
    final totalPopulation = _riskDistribution.values
        .fold(0, (sum, data) => sum + data.populationCount);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Demographic Analysis',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: _demographics.map((demographic) {
              final populationCount = (totalPopulation * demographic.proportion).round();
              final color = _getVulnerabilityLevelColor(demographic.vulnerabilityLevel);

              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: color.withValues(alpha: 0.3)),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            demographic.name,
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: color.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            _getVulnerabilityLevelDisplayName(demographic.vulnerabilityLevel),
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: color,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text(
                          'Population: ${_formatPopulation(populationCount)}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const Spacer(),
                        Text(
                          'Proportion: ${(demographic.proportion * 100).toStringAsFixed(1)}%',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  /// Builds vulnerability detailed view
  Widget _buildVulnerabilityView() {
    return Column(
      children: [
        Expanded(
          child: GridView.count(
            crossAxisCount: 2,
            childAspectRatio: 2.5,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            children: _vulnerabilityIndicators.map((indicator) {
              return _buildVulnerabilityCard(indicator);
            }).toList(),
          ),
        ),
      ],
    );
  }

  /// Builds vulnerability indicator card
  Widget _buildVulnerabilityCard(VulnerabilityIndicator indicator) {
    final color = _getVulnerabilityLevelColor(indicator.level);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: color.withValues(alpha: 0.3)),
        borderRadius: BorderRadius.circular(12),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            color.withValues(alpha: 0.1),
            color.withValues(alpha: 0.05),
          ],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                indicator.icon,
                color: color,
                size: 24,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  indicator.name,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ),
            ],
          ),
          const Spacer(),
          Row(
            children: [
              Text(
                '${(indicator.score * 100).toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _getVulnerabilityLevelDisplayName(indicator.level),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: color,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Builds selected segment information panel
  Widget _buildSelectedSegmentInfo() {
    if (_selectedSegment == null) return const SizedBox.shrink();

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
                  'Population Segment Details',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () {
                  setState(() {
                    _selectedSegment = null;
                  });
                },
                tooltip: 'Close',
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Add segment details here
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
            Icons.people_outline,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No population risk data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds table header cell
  Widget _buildTableHeader(String text) {
    return Padding(
      padding: const EdgeInsets.all(8),
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          fontWeight: FontWeight.bold,
        ),
        textAlign: TextAlign.center,
      ),
    );
  }

  /// Builds table cell
  Widget _buildTableCell(String text) {
    return Padding(
      padding: const EdgeInsets.all(8),
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodySmall,
        textAlign: TextAlign.center,
      ),
    );
  }

  /// Processes population risk data from risk trends
  void _processPopulationData() {
    if (widget.riskTrends.isEmpty) {
      _riskDistribution = {};
      _populationSegments = [];
      _vulnerabilityIndicators = [];
      return;
    }

    // Group by risk level
    final riskGroups = <RiskLevel, List<RiskTrend>>{};
    for (final trend in widget.riskTrends) {
      riskGroups.putIfAbsent(trend.riskLevel, () => []).add(trend);
    }

    // Calculate risk distribution
    _riskDistribution = {};
    for (final entry in riskGroups.entries) {
      final riskLevel = entry.key;
      final trends = entry.value;

      final totalPopulation = trends.fold(0, (sum, trend) => sum + trend.populationAtRisk);
      final averageRisk = trends.fold(0.0, (sum, trend) => sum + trend.riskScore) / trends.length;
      final averageConfidence = trends.fold(0.0, (sum, trend) => sum + trend.confidence) / trends.length;

      _riskDistribution[riskLevel] = PopulationRiskData(
        riskLevel: riskLevel,
        populationCount: totalPopulation,
        averageRisk: averageRisk,
        averageConfidence: averageConfidence,
        areaCount: trends.length,
      );
    }

    // Generate vulnerability indicators
    _generateVulnerabilityIndicators();
  }

  /// Generates vulnerability indicators based on risk data
  void _generateVulnerabilityIndicators() {
    final totalPopulation = _riskDistribution.values
        .fold(0, (sum, data) => sum + data.populationCount);

    if (totalPopulation == 0) {
      _vulnerabilityIndicators = [];
      return;
    }

    final highRiskPop = (_riskDistribution[RiskLevel.high]?.populationCount ?? 0) +
        (_riskDistribution[RiskLevel.critical]?.populationCount ?? 0);

    _vulnerabilityIndicators = [
      VulnerabilityIndicator(
        name: 'Population Density',
        score: math.min(totalPopulation / 100000.0, 1.0),
        level: _calculateVulnerabilityLevel(totalPopulation / 100000.0),
        icon: Icons.people,
      ),
      VulnerabilityIndicator(
        name: 'High Risk Exposure',
        score: highRiskPop / totalPopulation,
        level: _calculateVulnerabilityLevel(highRiskPop / totalPopulation),
        icon: Icons.warning,
      ),
      VulnerabilityIndicator(
        name: 'Geographic Spread',
        score: _calculateGeographicSpread(),
        level: _calculateVulnerabilityLevel(_calculateGeographicSpread()),
        icon: Icons.map,
      ),
      VulnerabilityIndicator(
        name: 'Children at Risk',
        score: _calculateChildrenAtRisk(),
        level: _calculateVulnerabilityLevel(_calculateChildrenAtRisk()),
        icon: Icons.child_care,
      ),
    ];
  }

  /// Calculates geographic spread vulnerability
  double _calculateGeographicSpread() {
    if (widget.riskTrends.length < 2) return 0.0;

    final coordinates = widget.riskTrends.map((t) => t.coordinates).toList();

    // Calculate bounding box area
    double minLat = coordinates.first.latitude;
    double maxLat = coordinates.first.latitude;
    double minLng = coordinates.first.longitude;
    double maxLng = coordinates.first.longitude;

    for (final coord in coordinates) {
      minLat = math.min(minLat, coord.latitude);
      maxLat = math.max(maxLat, coord.latitude);
      minLng = math.min(minLng, coord.longitude);
      maxLng = math.max(maxLng, coord.longitude);
    }

    final area = (maxLat - minLat) * (maxLng - minLng);
    return math.min(area * 1000, 1.0); // Normalize to 0-1
  }

  /// Calculates children at risk score
  double _calculateChildrenAtRisk() {
    final totalPopulation = _riskDistribution.values
        .fold(0, (sum, data) => sum + data.populationCount);

    if (totalPopulation == 0) return 0.0;

    // Estimate children (0-14 years) as 40% of total population
    final childrenPopulation = (totalPopulation * 0.4).round();
    final highRiskPop = (_riskDistribution[RiskLevel.high]?.populationCount ?? 0) +
        (_riskDistribution[RiskLevel.critical]?.populationCount ?? 0);

    // Assume children represent 40% of high-risk population
    final childrenAtRisk = (highRiskPop * 0.4).round();

    return childrenPopulation > 0 ? childrenAtRisk / childrenPopulation : 0.0;
  }

  /// Calculates vulnerability level from score
  VulnerabilityLevel _calculateVulnerabilityLevel(double score) {
    if (score >= 0.8) return VulnerabilityLevel.critical;
    if (score >= 0.6) return VulnerabilityLevel.high;
    if (score >= 0.3) return VulnerabilityLevel.medium;
    return VulnerabilityLevel.low;
  }

  /// Handles risk level selection from chart
  void _handleRiskLevelSelection(RiskLevel riskLevel) {
    // Implementation for handling risk level selection
    // Could show detailed breakdown for selected risk level
  }

  /// Gets view mode icon
  IconData _getViewModeIcon(PopulationViewMode mode) {
    switch (mode) {
      case PopulationViewMode.overview:
        return Icons.dashboard;
      case PopulationViewMode.riskDistribution:
        return Icons.pie_chart;
      case PopulationViewMode.demographics:
        return Icons.groups;
      case PopulationViewMode.vulnerability:
        return Icons.health_and_safety;
    }
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(PopulationViewMode mode) {
    switch (mode) {
      case PopulationViewMode.overview:
        return 'Overview';
      case PopulationViewMode.riskDistribution:
        return 'Risk Distribution';
      case PopulationViewMode.demographics:
        return 'Demographics';
      case PopulationViewMode.vulnerability:
        return 'Vulnerability';
    }
  }

  /// Gets risk level color
  Color _getRiskLevelColor(RiskLevel level) {
    switch (level) {
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

  /// Gets risk level display name
  String _getRiskLevelDisplayName(RiskLevel level) {
    switch (level) {
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

  /// Gets vulnerability level color
  Color _getVulnerabilityLevelColor(VulnerabilityLevel level) {
    switch (level) {
      case VulnerabilityLevel.low:
        return Colors.green;
      case VulnerabilityLevel.medium:
        return Colors.orange;
      case VulnerabilityLevel.high:
        return Colors.red;
      case VulnerabilityLevel.critical:
        return Colors.purple;
    }
  }

  /// Gets vulnerability level display name
  String _getVulnerabilityLevelDisplayName(VulnerabilityLevel level) {
    switch (level) {
      case VulnerabilityLevel.low:
        return 'Low';
      case VulnerabilityLevel.medium:
        return 'Medium';
      case VulnerabilityLevel.high:
        return 'High';
      case VulnerabilityLevel.critical:
        return 'Critical';
    }
  }

  /// Gets color for risk percentage
  Color _getRiskPercentageColor(double percentage) {
    if (percentage >= 20) return Colors.red;
    if (percentage >= 10) return Colors.orange;
    if (percentage >= 5) return Colors.yellow.shade700;
    return Colors.green;
  }

  /// Formats population numbers for display
  String _formatPopulation(int population) {
    if (population >= 1000000) {
      return '${(population / 1000000).toStringAsFixed(1)}M';
    } else if (population >= 1000) {
      return '${(population / 1000).toStringAsFixed(1)}K';
    }
    return population.toString();
  }
}

/// Population view mode enumeration
enum PopulationViewMode {
  overview,
  riskDistribution,
  demographics,
  vulnerability,
}

/// Vulnerability level enumeration
enum VulnerabilityLevel {
  low,
  medium,
  high,
  critical,
}

/// Population risk data structure
class PopulationRiskData {
  final RiskLevel riskLevel;
  final int populationCount;
  final double averageRisk;
  final double averageConfidence;
  final int areaCount;

  const PopulationRiskData({
    required this.riskLevel,
    required this.populationCount,
    required this.averageRisk,
    required this.averageConfidence,
    required this.areaCount,
  });
}

/// Population segment structure
class PopulationSegment {
  final String name;
  final int populationCount;
  final RiskLevel riskLevel;
  final VulnerabilityLevel vulnerabilityLevel;

  const PopulationSegment({
    required this.name,
    required this.populationCount,
    required this.riskLevel,
    required this.vulnerabilityLevel,
  });
}

/// Vulnerability indicator structure
class VulnerabilityIndicator {
  final String name;
  final double score;
  final VulnerabilityLevel level;
  final IconData icon;

  const VulnerabilityIndicator({
    required this.name,
    required this.score,
    required this.level,
    required this.icon,
  });
}

/// Demographic category structure
class DemographicCategory {
  final String name;
  final double proportion;
  final VulnerabilityLevel vulnerabilityLevel;

  const DemographicCategory(
    this.name,
    this.proportion,
    this.vulnerabilityLevel,
  );
}