/// Prediction metrics tab widget with comprehensive dashboard layout
///
/// This widget provides a complete prediction metrics dashboard with grid layout,
/// filtering capabilities, and interactive visualizations for model performance analysis.
///
/// Usage:
/// ```dart
/// PredictionMetricsTab(
///   predictionMetrics: metricsData,
///   models: modelsList,
///   onFilterChanged: (filter) => handleFilterChange(filter),
/// );
/// ```
library;

import 'package:flutter/material.dart';
import '../../domain/entities/prediction_metrics.dart';
import '../../domain/entities/analytics_data.dart';
import '../widgets/accuracy_trend_chart.dart';
import '../widgets/confusion_matrix_chart.dart';
import '../widgets/model_comparison_chart.dart';
import '../widgets/roc_curve_chart.dart';
import '../widgets/metric_card.dart';
import '../widgets/accuracy_gauge.dart';

/// Prediction metrics tab widget for comprehensive dashboard
class PredictionMetricsTab extends StatefulWidget {
  /// Primary prediction metrics data
  final PredictionMetrics? predictionMetrics;

  /// List of models for comparison
  final List<ModelPerformance> models;

  /// ROC curve data
  final List<ROCPoint>? rocData;

  /// Callback for filter changes
  final Function(PredictionMetricsFilter)? onFilterChanged;

  /// Callback for metric export
  final Function(String format)? onExportMetrics;

  /// Whether to show export functionality
  final bool showExportOptions;

  /// Constructor with required data
  const PredictionMetricsTab({
    super.key,
    this.predictionMetrics,
    this.models = const [],
    this.rocData,
    this.onFilterChanged,
    this.onExportMetrics,
    this.showExportOptions = true,
  });

  @override
  State<PredictionMetricsTab> createState() => _PredictionMetricsTabState();
}

class _PredictionMetricsTabState extends State<PredictionMetricsTab>
    with TickerProviderStateMixin {
  /// Tab controller for metric sections
  late TabController _tabController;

  /// Current filter state
  PredictionMetricsFilter _currentFilter = const PredictionMetricsFilter();

  /// Loading state
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildHeader(context),
        _buildFilterBar(context),
        _buildTabBar(context),
        Expanded(
          child: _isLoading
              ? _buildLoadingState(context)
              : _buildTabBarView(context),
        ),
      ],
    );
  }

  /// Builds the dashboard header
  Widget _buildHeader(BuildContext context) {
    final theme = Theme.of(context);
    final hasData = widget.predictionMetrics != null;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(12),
          topRight: Radius.circular(12),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Prediction Model Analytics',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  hasData
                      ? 'Model: ${widget.predictionMetrics!.modelId} v${widget.predictionMetrics!.modelVersion}'
                      : 'No model data available',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
              ],
            ),
          ),
          if (widget.showExportOptions) _buildExportButton(context),
        ],
      ),
    );
  }

  /// Builds the filter bar
  Widget _buildFilterBar(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outline.withValues(alpha: 0.2),
          ),
        ),
      ),
      child: Row(
        children: [
          _buildDateRangeFilter(context),
          const SizedBox(width: 16),
          _buildRegionFilter(context),
          const SizedBox(width: 16),
          _buildMetricFilter(context),
          const Spacer(),
          _buildRefreshButton(context),
        ],
      ),
    );
  }

  /// Builds date range filter
  Widget _buildDateRangeFilter(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.date_range, size: 16),
        const SizedBox(width: 4),
        Text(
          'Period: ${_formatDateRange(_currentFilter.dateRange)}',
          style: Theme.of(context).textTheme.bodySmall,
        ),
        IconButton(
          icon: const Icon(Icons.edit, size: 16),
          onPressed: () => _showDateRangePicker(context),
          tooltip: 'Change date range',
        ),
      ],
    );
  }

  /// Builds region filter
  Widget _buildRegionFilter(BuildContext context) {
    return DropdownButton<String>(
      value: _currentFilter.region,
      hint: const Text('All Regions'),
      underline: const SizedBox.shrink(),
      items: ['All', 'Kenya', 'Uganda', 'Tanzania', 'Rwanda']
          .map((region) => DropdownMenuItem(
                value: region == 'All' ? null : region,
                child: Text(region),
              ))
          .toList(),
      onChanged: (value) => _updateFilter(_currentFilter.copyWith(region: value)),
    );
  }

  /// Builds metric filter
  Widget _buildMetricFilter(BuildContext context) {
    return DropdownButton<String>(
      value: _currentFilter.selectedMetric,
      hint: const Text('All Metrics'),
      underline: const SizedBox.shrink(),
      items: ['accuracy', 'precision', 'recall', 'f1Score', 'aucRoc']
          .map((metric) => DropdownMenuItem(
                value: metric,
                child: Text(_getMetricDisplayName(metric)),
              ))
          .toList(),
      onChanged: (value) => _updateFilter(_currentFilter.copyWith(selectedMetric: value)),
    );
  }

  /// Builds refresh button
  Widget _buildRefreshButton(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.refresh),
      onPressed: _refreshData,
      tooltip: 'Refresh data',
    );
  }

  /// Builds export button
  Widget _buildExportButton(BuildContext context) {
    return PopupMenuButton<String>(
      icon: const Icon(Icons.download),
      tooltip: 'Export metrics',
      onSelected: (format) => widget.onExportMetrics?.call(format),
      itemBuilder: (context) => [
        const PopupMenuItem(value: 'pdf', child: Text('Export as PDF')),
        const PopupMenuItem(value: 'csv', child: Text('Export as CSV')),
        const PopupMenuItem(value: 'json', child: Text('Export as JSON')),
      ],
    );
  }

  /// Builds tab bar
  Widget _buildTabBar(BuildContext context) {
    return TabBar(
      controller: _tabController,
      isScrollable: true,
      tabs: const [
        Tab(icon: Icon(Icons.dashboard), text: 'Overview'),
        Tab(icon: Icon(Icons.trending_up), text: 'Performance'),
        Tab(icon: Icon(Icons.compare), text: 'Comparison'),
        Tab(icon: Icon(Icons.timeline), text: 'Trends'),
      ],
    );
  }

  /// Builds tab bar view
  Widget _buildTabBarView(BuildContext context) {
    return TabBarView(
      controller: _tabController,
      children: [
        _buildOverviewTab(context),
        _buildPerformanceTab(context),
        _buildComparisonTab(context),
        _buildTrendsTab(context),
      ],
    );
  }

  /// Builds overview tab
  Widget _buildOverviewTab(BuildContext context) {
    if (widget.predictionMetrics == null) {
      return _buildNoDataMessage('No prediction metrics available');
    }

    final metrics = widget.predictionMetrics!;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Key metrics row
          Row(
            children: [
              Expanded(
                child: AccuracyGauge(
                  accuracy: metrics.overallAccuracy,
                  size: 180,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 2,
                child: GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  childAspectRatio: 1.8,
                  mainAxisSpacing: 8,
                  crossAxisSpacing: 8,
                  children: [
                    PrecisionCard(
                      value: metrics.precision,
                      trend: _getTrendForMetric('precision'),
                    ),
                    RecallCard(
                      value: metrics.recall,
                      trend: _getTrendForMetric('recall'),
                    ),
                    F1ScoreCard(
                      value: metrics.f1Score,
                      trend: _getTrendForMetric('f1Score'),
                    ),
                    AUCScoreCard(
                      value: metrics.aucRoc,
                      trend: _getTrendForMetric('aucRoc'),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          // Performance breakdown
          Text(
            'Performance by Risk Level',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          _buildPerformanceByLevelGrid(metrics.performanceByLevel),
          const SizedBox(height: 24),
          // Model information
          _buildModelInfoCard(metrics),
        ],
      ),
    );
  }

  /// Builds performance tab
  Widget _buildPerformanceTab(BuildContext context) {
    if (widget.predictionMetrics == null) {
      return _buildNoDataMessage('No performance data available');
    }

    final metrics = widget.predictionMetrics!;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Confusion matrix
          ConfusionMatrixChart(
            confusionMatrix: metrics.confusionMatrix,
            height: 350,
            showPercentages: true,
          ),
          const SizedBox(height: 16),
          // ROC curve
          if (widget.rocData != null)
            ROCCurveChart(
              rocData: widget.rocData!,
              height: 350,
              showAUCScore: true,
            ),
        ],
      ),
    );
  }

  /// Builds comparison tab
  Widget _buildComparisonTab(BuildContext context) {
    if (widget.models.isEmpty) {
      return _buildNoDataMessage('No models available for comparison');
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          ModelComparisonChart(
            models: widget.models,
            height: 350,
            selectedMetric: _currentFilter.selectedMetric ?? 'accuracy',
          ),
          const SizedBox(height: 16),
          _buildModelComparisonTable(),
        ],
      ),
    );
  }

  /// Builds trends tab
  Widget _buildTrendsTab(BuildContext context) {
    if (widget.predictionMetrics?.accuracyTrend.isEmpty ?? true) {
      return _buildNoDataMessage('No trend data available');
    }

    final metrics = widget.predictionMetrics!;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          AccuracyTrendChart(
            accuracyTrend: metrics.accuracyTrend,
            height: 350,
            showConfidenceInterval: true,
          ),
          const SizedBox(height: 16),
          _buildTrendStatistics(metrics.accuracyTrend),
        ],
      ),
    );
  }

  /// Builds performance by level grid
  Widget _buildPerformanceByLevelGrid(Map<RiskLevel, PerformanceByLevel> performanceByLevel) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      childAspectRatio: 1.5,
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      children: performanceByLevel.entries.map((entry) {
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _getRiskLevelDisplayName(entry.key),
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text('Accuracy: ${(entry.value.accuracy * 100).toStringAsFixed(1)}%'),
                Text('Precision: ${(entry.value.precision * 100).toStringAsFixed(1)}%'),
                Text('Recall: ${(entry.value.recall * 100).toStringAsFixed(1)}%'),
                Text('Support: ${entry.value.support}'),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  /// Builds model information card
  Widget _buildModelInfoCard(PredictionMetrics metrics) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Model Information',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            _buildInfoRow('Model ID', metrics.modelId),
            _buildInfoRow('Version', metrics.modelVersion),
            _buildInfoRow('Region', metrics.region),
            _buildInfoRow('Evaluation Period', _formatDateRange(metrics.evaluationPeriod)),
            _buildInfoRow('Calculated', _formatTimestamp(metrics.calculatedAt)),
          ],
        ),
      ),
    );
  }

  /// Builds model comparison table
  Widget _buildModelComparisonTable() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Model Comparison Details',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('Model')),
                  DataColumn(label: Text('Version')),
                  DataColumn(label: Text('Accuracy')),
                  DataColumn(label: Text('Status')),
                ],
                rows: widget.models.map((model) {
                  return DataRow(
                    cells: [
                      DataCell(Text(model.modelName)),
                      DataCell(Text(model.version)),
                      DataCell(Text('${(model.accuracy * 100).toStringAsFixed(1)}%')),
                      DataCell(_buildStatusChip(model.status)),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds trend statistics
  Widget _buildTrendStatistics(List<AccuracyTrendPoint> accuracyTrend) {
    if (accuracyTrend.isEmpty) return const SizedBox.shrink();

    final latest = accuracyTrend.last;
    final earliest = accuracyTrend.first;
    final change = latest.accuracy - earliest.accuracy;
    final changePercent = (change * 100);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Trend Analysis',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            _buildInfoRow('Data Points', accuracyTrend.length.toString()),
            _buildInfoRow('Period Change', '${changePercent.toStringAsFixed(2)}%'),
            _buildInfoRow('Latest Accuracy', '${(latest.accuracy * 100).toStringAsFixed(1)}%'),
            _buildInfoRow('Trend Direction', change > 0 ? 'Improving' : change < 0 ? 'Declining' : 'Stable'),
          ],
        ),
      ),
    );
  }

  /// Builds status chip
  Widget _buildStatusChip(ModelStatus status) {
    Color color;
    switch (status) {
      case ModelStatus.production:
        color = Colors.green;
        break;
      case ModelStatus.staging:
        color = Colors.orange;
        break;
      case ModelStatus.testing:
        color = Colors.blue;
        break;
      case ModelStatus.development:
        color = Colors.grey;
        break;
      case ModelStatus.deprecated:
        color = Colors.red;
        break;
      case ModelStatus.retired:
        color = Colors.black54;
        break;
    }

    return Chip(
      label: Text(
        status.name.toUpperCase(),
        style: const TextStyle(fontSize: 10),
      ),
      backgroundColor: color.withValues(alpha: 0.1),
      labelStyle: TextStyle(color: color),
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }

  /// Builds info row
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  /// Builds loading state
  Widget _buildLoadingState(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('Loading prediction metrics...'),
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
            Icons.analytics_outlined,
            size: 64,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: Theme.of(context).textTheme.bodyLarge,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Shows date range picker
  Future<void> _showDateRangePicker(BuildContext context) async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now(),
      initialDateRange: DateTimeRange(
        start: _currentFilter.dateRange?.start ?? DateTime.now().subtract(const Duration(days: 30)),
        end: _currentFilter.dateRange?.end ?? DateTime.now(),
      ),
    );

    if (picked != null) {
      _updateFilter(_currentFilter.copyWith(
        dateRange: DateRange(start: picked.start, end: picked.end),
      ));
    }
  }

  /// Updates filter and notifies parent
  void _updateFilter(PredictionMetricsFilter newFilter) {
    setState(() {
      _currentFilter = newFilter;
    });
    widget.onFilterChanged?.call(newFilter);
  }

  /// Refreshes data
  void _refreshData() {
    setState(() {
      _isLoading = true;
    });

    // Simulate refresh delay
    Future.delayed(const Duration(seconds: 1), () {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    });
  }

  /// Helper methods
  String _formatDateRange(DateRange? range) {
    if (range == null) return 'Last 30 days';
    return '${_formatDate(range.start)} - ${_formatDate(range.end)}';
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }

  String _formatTimestamp(DateTime timestamp) {
    return '${_formatDate(timestamp)} ${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
  }

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
      case 'aucRoc':
        return 'AUC ROC';
      default:
        return metric;
    }
  }

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

  MetricTrend? _getTrendForMetric(String metric) {
    // Placeholder - in real implementation, calculate from historical data
    return MetricTrend.increasing;
  }
}

/// Filter for prediction metrics
class PredictionMetricsFilter {
  final DateRange? dateRange;
  final String? region;
  final String? selectedMetric;
  final List<ModelStatus>? modelStatuses;

  const PredictionMetricsFilter({
    this.dateRange,
    this.region,
    this.selectedMetric,
    this.modelStatuses,
  });

  PredictionMetricsFilter copyWith({
    DateRange? dateRange,
    String? region,
    String? selectedMetric,
    List<ModelStatus>? modelStatuses,
  }) {
    return PredictionMetricsFilter(
      dateRange: dateRange ?? this.dateRange,
      region: region ?? this.region,
      selectedMetric: selectedMetric ?? this.selectedMetric,
      modelStatuses: modelStatuses ?? this.modelStatuses,
    );
  }
}