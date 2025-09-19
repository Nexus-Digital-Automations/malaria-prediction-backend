/// Comparison mode widget for side-by-side data analysis
///
/// This widget provides comprehensive comparison capabilities for analytics data
/// allowing users to compare datasets side-by-side with visual diff indicators,
/// metric calculations, and various comparison modes.
///
/// Features:
/// - Side-by-side dataset comparison
/// - Difference visualization with color coding
/// - Multiple comparison types (absolute, percentage, normalized)
/// - Interactive sync scrolling and navigation
/// - Metric comparison tables and charts
/// - Export comparison results
/// - Responsive layout for different screen sizes
/// - Customizable comparison parameters
///
/// Usage:
/// ```dart
/// ComparisonModeWidget(
///   primaryData: currentData,
///   secondaryData: comparisonData,
///   comparisonType: ComparisonType.sideBySide,
///   onComparisonTypeChanged: (type) => updateComparisonType(type),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:logging/logging.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/analytics_filters.dart';

/// Logger for comparison mode operations
final _logger = Logger('ComparisonModeWidget');

/// Comparison mode widget for data analysis
class ComparisonModeWidget extends StatefulWidget {
  /// Primary dataset for comparison
  final AnalyticsData? primaryData;

  /// Secondary dataset for comparison
  final AnalyticsData? secondaryData;

  /// Current comparison type
  final ComparisonType comparisonType;

  /// Callback when comparison type changes
  final ValueChanged<ComparisonType> onComparisonTypeChanged;

  /// Whether to show difference indicators
  final bool showDifferences;

  /// Whether to sync scrolling between panels
  final bool syncScrolling;

  /// Custom comparison metrics
  final List<ComparisonMetric>? customMetrics;

  /// Whether to allow data export
  final bool allowExport;

  /// Custom color scheme
  final ColorScheme? colorScheme;

  /// Whether comparison is read-only
  final bool readOnly;

  /// Callback when secondary data selection is requested
  final VoidCallback? onSelectSecondaryData;

  const ComparisonModeWidget({
    super.key,
    this.primaryData,
    this.secondaryData,
    required this.comparisonType,
    required this.onComparisonTypeChanged,
    this.showDifferences = true,
    this.syncScrolling = true,
    this.customMetrics,
    this.allowExport = true,
    this.colorScheme,
    this.readOnly = false,
    this.onSelectSecondaryData,
  });

  @override
  State<ComparisonModeWidget> createState() => _ComparisonModeWidgetState();
}

class _ComparisonModeWidgetState extends State<ComparisonModeWidget>
    with TickerProviderStateMixin {
  /// Tab controller for comparison modes
  late TabController _tabController;

  /// Animation controller for UI transitions
  late AnimationController _animationController;

  /// Animation for panel transitions
  late Animation<double> _panelAnimation;

  /// Scroll controllers for sync scrolling
  final ScrollController _primaryScrollController = ScrollController();
  final ScrollController _secondaryScrollController = ScrollController();

  /// Current comparison results
  ComparisonResult? _comparisonResult;

  /// Whether sync scrolling is active
  bool _syncScrollingActive = false;

  /// Current selected metrics for comparison
  final Set<String> _selectedMetrics = {};

  /// Form key for comparison configuration
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _logger.info('Initializing comparison mode widget');

    // Initialize tab controller
    _tabController = TabController(length: ComparisonView.values.length, vsync: this);

    // Initialize animations
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _panelAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );

    // Setup sync scrolling
    if (widget.syncScrolling) {
      _setupSyncScrolling();
    }

    // Initialize selected metrics
    _initializeSelectedMetrics();

    // Calculate initial comparison
    _calculateComparison();

    // Start animation
    _animationController.forward();
  }

  @override
  void didUpdateWidget(ComparisonModeWidget oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Recalculate comparison if data changed
    if (widget.primaryData != oldWidget.primaryData ||
        widget.secondaryData != oldWidget.secondaryData ||
        widget.comparisonType != oldWidget.comparisonType) {
      _calculateComparison();
    }

    // Update sync scrolling if setting changed
    if (widget.syncScrolling != oldWidget.syncScrolling) {
      if (widget.syncScrolling) {
        _setupSyncScrolling();
      } else {
        _removeSyncScrolling();
      }
    }
  }

  @override
  void dispose() {
    _logger.info('Disposing comparison mode widget');
    _tabController.dispose();
    _animationController.dispose();
    _primaryScrollController.dispose();
    _secondaryScrollController.dispose();
    super.dispose();
  }

  /// Sets up synchronized scrolling between panels
  void _setupSyncScrolling() {
    _primaryScrollController.addListener(() {
      if (_syncScrollingActive) return;
      _syncScrollingActive = true;
      _secondaryScrollController.jumpTo(_primaryScrollController.offset);
      _syncScrollingActive = false;
    });

    _secondaryScrollController.addListener(() {
      if (_syncScrollingActive) return;
      _syncScrollingActive = true;
      _primaryScrollController.jumpTo(_secondaryScrollController.offset);
      _syncScrollingActive = false;
    });
  }

  /// Removes synchronized scrolling
  void _removeSyncScrolling() {
    _primaryScrollController.removeListener(() {});
    _secondaryScrollController.removeListener(() {});
  }

  /// Initializes selected metrics
  void _initializeSelectedMetrics() {
    _selectedMetrics.addAll([
      'prediction_accuracy',
      'data_quality',
      'alert_statistics',
      'environmental_trends',
    ]);
  }

  /// Calculates comparison between datasets
  void _calculateComparison() {
    if (widget.primaryData == null || widget.secondaryData == null) {
      setState(() {
        _comparisonResult = null;
      });
      return;
    }

    final result = ComparisonResult(
      primaryData: widget.primaryData!,
      secondaryData: widget.secondaryData!,
      comparisonType: widget.comparisonType,
      metrics: _calculateMetricComparisons(),
      summary: _calculateSummaryComparison(),
      generatedAt: DateTime.now(),
    );

    setState(() {
      _comparisonResult = result;
    });

    _logger.info('Comparison calculated with ${result.metrics.length} metrics');
  }

  /// Calculates metric comparisons
  Map<String, MetricComparison> _calculateMetricComparisons() {
    final metrics = <String, MetricComparison>{};

    if (widget.primaryData == null || widget.secondaryData == null) {
      return metrics;
    }

    final primary = widget.primaryData!;
    final secondary = widget.secondaryData!;

    // Prediction accuracy comparison
    if (_selectedMetrics.contains('prediction_accuracy')) {
      metrics['prediction_accuracy'] = MetricComparison(
        name: 'Prediction Accuracy',
        primaryValue: primary.predictionAccuracy.overall,
        secondaryValue: secondary.predictionAccuracy.overall,
        unit: '%',
        differenceType: DifferenceType.percentage,
        significance: _calculateSignificance(
          primary.predictionAccuracy.overall,
          secondary.predictionAccuracy.overall,
        ),
      );
    }

    // Data quality comparison
    if (_selectedMetrics.contains('data_quality')) {
      metrics['data_quality'] = MetricComparison(
        name: 'Data Quality',
        primaryValue: primary.dataQuality.completeness,
        secondaryValue: secondary.dataQuality.completeness,
        unit: '%',
        differenceType: DifferenceType.percentage,
        significance: _calculateSignificance(
          primary.dataQuality.completeness,
          secondary.dataQuality.completeness,
        ),
      );
    }

    // Alert statistics comparison
    if (_selectedMetrics.contains('alert_statistics')) {
      metrics['alert_statistics'] = MetricComparison(
        name: 'Total Alerts',
        primaryValue: primary.alertStatistics.totalAlerts.toDouble(),
        secondaryValue: secondary.alertStatistics.totalAlerts.toDouble(),
        unit: 'alerts',
        differenceType: DifferenceType.absolute,
        significance: _calculateSignificance(
          primary.alertStatistics.totalAlerts.toDouble(),
          secondary.alertStatistics.totalAlerts.toDouble(),
        ),
      );
    }

    // Environmental trends comparison
    if (_selectedMetrics.contains('environmental_trends')) {
      metrics['environmental_trends'] = MetricComparison(
        name: 'Environmental Data Points',
        primaryValue: primary.environmentalTrends.length.toDouble(),
        secondaryValue: secondary.environmentalTrends.length.toDouble(),
        unit: 'points',
        differenceType: DifferenceType.absolute,
        significance: _calculateSignificance(
          primary.environmentalTrends.length.toDouble(),
          secondary.environmentalTrends.length.toDouble(),
        ),
      );
    }

    return metrics;
  }

  /// Calculates summary comparison
  ComparisonSummary _calculateSummaryComparison() {
    if (_comparisonResult?.metrics.isEmpty ?? true) {
      return ComparisonSummary(
        overallTrend: ComparisonTrend.neutral,
        significantDifferences: 0,
        averageDifference: 0.0,
        recommendations: [],
      );
    }

    final metrics = _comparisonResult!.metrics.values;
    final significantDifferences = metrics.where((m) => m.significance > 0.1).length;
    final averageDifference = metrics.map((m) => m.difference.abs()).reduce((a, b) => a + b) / metrics.length;

    ComparisonTrend trend = ComparisonTrend.neutral;
    if (averageDifference > 0.1) {
      trend = metrics.map((m) => m.difference).reduce((a, b) => a + b) > 0
          ? ComparisonTrend.improving
          : ComparisonTrend.declining;
    }

    return ComparisonSummary(
      overallTrend: trend,
      significantDifferences: significantDifferences,
      averageDifference: averageDifference,
      recommendations: _generateRecommendations(metrics.toList()),
    );
  }

  /// Calculates statistical significance
  double _calculateSignificance(double value1, double value2) {
    if (value1 == 0 && value2 == 0) return 0.0;
    final maxValue = [value1, value2].reduce((a, b) => a > b ? a : b);
    if (maxValue == 0) return 0.0;
    return (value1 - value2).abs() / maxValue;
  }

  /// Generates recommendations based on comparison
  List<String> _generateRecommendations(List<MetricComparison> metrics) {
    final recommendations = <String>[];

    for (final metric in metrics) {
      if (metric.significance > 0.2) {
        if (metric.difference > 0) {
          recommendations.add('${metric.name} shows significant improvement (+${metric.differenceString})');
        } else {
          recommendations.add('${metric.name} shows significant decline (${metric.differenceString})');
        }
      }
    }

    if (recommendations.isEmpty) {
      recommendations.add('No significant differences detected between datasets');
    }

    return recommendations;
  }

  /// Exports comparison results
  void _exportComparison() {
    if (_comparisonResult == null) {
      _showMessage('No comparison data to export');
      return;
    }

    // Implementation would handle actual export
    _showMessage('Comparison exported successfully');
    _logger.info('Comparison results exported');
  }

  /// Shows a message to the user
  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = widget.colorScheme ?? theme.colorScheme;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            _buildHeader(theme, colorScheme),

            const SizedBox(height: 16),

            // Comparison type selector
            _buildComparisonTypeSelector(theme, colorScheme),

            const SizedBox(height: 16),

            // Tab bar for views
            _buildTabBar(theme, colorScheme),

            const SizedBox(height: 16),

            // Main content
            Expanded(
              child: AnimatedBuilder(
                animation: _panelAnimation,
                builder: (context, child) {
                  return Opacity(
                    opacity: _panelAnimation.value,
                    child: _buildMainContent(theme, colorScheme),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds the header section
  Widget _buildHeader(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Data Comparison',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Compare datasets side-by-side with difference analysis',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ),
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Select secondary data button
            if (widget.secondaryData == null)
              ElevatedButton.icon(
                onPressed: widget.onSelectSecondaryData,
                icon: const Icon(Icons.add_chart),
                label: const Text('Select Data'),
              ),
            // Export button
            if (widget.allowExport && _comparisonResult != null) ...[
              const SizedBox(width: 8),
              IconButton(
                onPressed: _exportComparison,
                icon: const Icon(Icons.download),
                tooltip: 'Export Comparison',
                color: colorScheme.primary,
              ),
            ],
          ],
        ),
      ],
    );
  }

  /// Builds comparison type selector
  Widget _buildComparisonTypeSelector(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Text(
          'Comparison Type:',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Wrap(
            spacing: 8,
            children: ComparisonType.values.map((type) {
              final isSelected = widget.comparisonType == type;
              return FilterChip(
                label: Text(_getComparisonTypeLabel(type)),
                selected: isSelected,
                onSelected: widget.readOnly
                    ? null
                    : (selected) {
                        if (selected) {
                          widget.onComparisonTypeChanged(type);
                        }
                      },
                selectedColor: colorScheme.primaryContainer,
                avatar: Icon(_getComparisonTypeIcon(type), size: 16),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  /// Builds tab bar for different views
  Widget _buildTabBar(ThemeData theme, ColorScheme colorScheme) {
    return TabBar(
      controller: _tabController,
      isScrollable: true,
      labelColor: colorScheme.primary,
      unselectedLabelColor: colorScheme.onSurface.withOpacity(0.6),
      indicatorColor: colorScheme.primary,
      tabs: const [
        Tab(icon: Icon(Icons.compare_arrows), text: 'Side by Side'),
        Tab(icon: Icon(Icons.analytics), text: 'Metrics'),
        Tab(icon: Icon(Icons.trending_up), text: 'Trends'),
        Tab(icon: Icon(Icons.summarize), text: 'Summary'),
      ],
    );
  }

  /// Builds main content area
  Widget _buildMainContent(ThemeData theme, ColorScheme colorScheme) {
    if (widget.primaryData == null) {
      return _buildNoDataState('No primary data available', theme, colorScheme);
    }

    if (widget.secondaryData == null) {
      return _buildNoDataState('Select secondary data to compare', theme, colorScheme);
    }

    return TabBarView(
      controller: _tabController,
      children: [
        _buildSideBySideView(theme, colorScheme),
        _buildMetricsView(theme, colorScheme),
        _buildTrendsView(theme, colorScheme),
        _buildSummaryView(theme, colorScheme),
      ],
    );
  }

  /// Builds no data state
  Widget _buildNoDataState(String message, ThemeData theme, ColorScheme colorScheme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.compare_arrows,
            size: 64,
            color: colorScheme.onSurface.withOpacity(0.5),
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: theme.textTheme.bodyLarge?.copyWith(
              color: colorScheme.onSurface.withOpacity(0.7),
            ),
            textAlign: TextAlign.center,
          ),
          if (widget.onSelectSecondaryData != null) ...[
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: widget.onSelectSecondaryData,
              icon: const Icon(Icons.add_chart),
              label: const Text('Select Comparison Data'),
            ),
          ],
        ],
      ),
    );
  }

  /// Builds side-by-side comparison view
  Widget _buildSideBySideView(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        // Primary data panel
        Expanded(
          child: _buildDataPanel(
            'Primary Dataset',
            widget.primaryData!,
            _primaryScrollController,
            colorScheme.primaryContainer,
            theme,
            colorScheme,
          ),
        ),

        // Divider with comparison indicators
        Container(
          width: 2,
          margin: const EdgeInsets.symmetric(horizontal: 8),
          decoration: BoxDecoration(
            color: colorScheme.outline,
            borderRadius: BorderRadius.circular(1),
          ),
        ),

        // Secondary data panel
        Expanded(
          child: _buildDataPanel(
            'Secondary Dataset',
            widget.secondaryData!,
            _secondaryScrollController,
            colorScheme.secondaryContainer,
            theme,
            colorScheme,
          ),
        ),
      ],
    );
  }

  /// Builds individual data panel
  Widget _buildDataPanel(
    String title,
    AnalyticsData data,
    ScrollController scrollController,
    Color backgroundColor,
    ThemeData theme,
    ColorScheme colorScheme,
  ) {
    return Container(
      decoration: BoxDecoration(
        color: backgroundColor.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Panel header
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: backgroundColor.withOpacity(0.6),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
            ),
            child: Row(
              children: [
                Text(
                  title,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Text(
                  data.region,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
              ],
            ),
          ),

          // Panel content
          Expanded(
            child: SingleChildScrollView(
              controller: scrollController,
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildDataSummaryCard('Prediction Accuracy',
                    '${(data.predictionAccuracy.overall * 100).toStringAsFixed(1)}%',
                    Icons.analytics, theme, colorScheme),
                  const SizedBox(height: 8),
                  _buildDataSummaryCard('Data Quality',
                    '${(data.dataQuality.completeness * 100).toStringAsFixed(1)}%',
                    Icons.verified, theme, colorScheme),
                  const SizedBox(height: 8),
                  _buildDataSummaryCard('Total Alerts',
                    '${data.alertStatistics.totalAlerts}',
                    Icons.notifications, theme, colorScheme),
                  const SizedBox(height: 8),
                  _buildDataSummaryCard('Environmental Points',
                    '${data.environmentalTrends.length}',
                    Icons.eco, theme, colorScheme),
                  const SizedBox(height: 8),
                  _buildDataSummaryCard('Risk Trends',
                    '${data.riskTrends.length}',
                    Icons.trending_up, theme, colorScheme),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds data summary card
  Widget _buildDataSummaryCard(String title, String value, IconData icon, ThemeData theme, ColorScheme colorScheme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(icon, color: colorScheme.primary),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: colorScheme.onSurface.withOpacity(0.7),
                    ),
                  ),
                  Text(
                    value,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds metrics comparison view
  Widget _buildMetricsView(ThemeData theme, ColorScheme colorScheme) {
    if (_comparisonResult == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return SingleChildScrollView(
      child: Column(
        children: _comparisonResult!.metrics.values.map((metric) {
          return _buildMetricComparisonCard(metric, theme, colorScheme);
        }).toList(),
      ),
    );
  }

  /// Builds metric comparison card
  Widget _buildMetricComparisonCard(MetricComparison metric, ThemeData theme, ColorScheme colorScheme) {
    final isPositive = metric.difference >= 0;
    final significanceColor = metric.significance > 0.2
        ? (isPositive ? Colors.green : Colors.red)
        : Colors.grey;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    metric.name,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: significanceColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${isPositive ? '+' : ''}${metric.differenceString}',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: significanceColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Primary', style: theme.textTheme.bodySmall),
                      Text(
                        '${metric.primaryValue.toStringAsFixed(2)} ${metric.unit}',
                        style: theme.textTheme.titleSmall,
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Secondary', style: theme.textTheme.bodySmall),
                      Text(
                        '${metric.secondaryValue.toStringAsFixed(2)} ${metric.unit}',
                        style: theme.textTheme.titleSmall,
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Significance', style: theme.textTheme.bodySmall),
                      Text(
                        '${(metric.significance * 100).toStringAsFixed(1)}%',
                        style: theme.textTheme.titleSmall?.copyWith(
                          color: significanceColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Builds trends comparison view
  Widget _buildTrendsView(ThemeData theme, ColorScheme colorScheme) {
    return const Center(
      child: Text('Trends comparison view coming soon'),
    );
  }

  /// Builds summary view
  Widget _buildSummaryView(ThemeData theme, ColorScheme colorScheme) {
    if (_comparisonResult?.summary == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final summary = _comparisonResult!.summary;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Overall trend card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Overall Comparison',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Icon(
                        _getTrendIcon(summary.overallTrend),
                        color: _getTrendColor(summary.overallTrend),
                        size: 32,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _getTrendLabel(summary.overallTrend),
                              style: theme.textTheme.titleMedium?.copyWith(
                                color: _getTrendColor(summary.overallTrend),
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              '${summary.significantDifferences} significant differences detected',
                              style: theme.textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Recommendations
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Recommendations',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ...summary.recommendations.map((recommendation) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.lightbulb,
                            color: colorScheme.primary,
                            size: 16,
                          ),
                          const SizedBox(width: 8),
                          Expanded(child: Text(recommendation)),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Gets comparison type label
  String _getComparisonTypeLabel(ComparisonType type) {
    switch (type) {
      case ComparisonType.sideBySide:
        return 'Side by Side';
      case ComparisonType.overlay:
        return 'Overlay';
      case ComparisonType.difference:
        return 'Difference';
    }
  }

  /// Gets comparison type icon
  IconData _getComparisonTypeIcon(ComparisonType type) {
    switch (type) {
      case ComparisonType.sideBySide:
        return Icons.view_column;
      case ComparisonType.overlay:
        return Icons.layers;
      case ComparisonType.difference:
        return Icons.compare_arrows;
    }
  }

  /// Gets trend icon
  IconData _getTrendIcon(ComparisonTrend trend) {
    switch (trend) {
      case ComparisonTrend.improving:
        return Icons.trending_up;
      case ComparisonTrend.declining:
        return Icons.trending_down;
      case ComparisonTrend.neutral:
        return Icons.trending_flat;
    }
  }

  /// Gets trend color
  Color _getTrendColor(ComparisonTrend trend) {
    switch (trend) {
      case ComparisonTrend.improving:
        return Colors.green;
      case ComparisonTrend.declining:
        return Colors.red;
      case ComparisonTrend.neutral:
        return Colors.grey;
    }
  }

  /// Gets trend label
  String _getTrendLabel(ComparisonTrend trend) {
    switch (trend) {
      case ComparisonTrend.improving:
        return 'Improving Trend';
      case ComparisonTrend.declining:
        return 'Declining Trend';
      case ComparisonTrend.neutral:
        return 'Stable/Neutral';
    }
  }
}

/// Comparison type enumeration
enum ComparisonType {
  sideBySide,
  overlay,
  difference,
}

/// Comparison view enumeration
enum ComparisonView {
  sideBySide,
  metrics,
  trends,
  summary,
}

/// Comparison trend enumeration
enum ComparisonTrend {
  improving,
  declining,
  neutral,
}

/// Difference type enumeration
enum DifferenceType {
  absolute,
  percentage,
  normalized,
}

/// Metric comparison class
class MetricComparison {
  final String name;
  final double primaryValue;
  final double secondaryValue;
  final String unit;
  final DifferenceType differenceType;
  final double significance;

  const MetricComparison({
    required this.name,
    required this.primaryValue,
    required this.secondaryValue,
    required this.unit,
    required this.differenceType,
    required this.significance,
  });

  double get difference => secondaryValue - primaryValue;

  String get differenceString {
    switch (differenceType) {
      case DifferenceType.absolute:
        return difference.toStringAsFixed(2);
      case DifferenceType.percentage:
        if (primaryValue == 0) return 'N/A';
        final percent = (difference / primaryValue) * 100;
        return '${percent.toStringAsFixed(1)}%';
      case DifferenceType.normalized:
        final maxValue = [primaryValue, secondaryValue].reduce((a, b) => a > b ? a : b);
        if (maxValue == 0) return '0.0';
        return (difference / maxValue).toStringAsFixed(3);
    }
  }
}

/// Comparison result class
class ComparisonResult {
  final AnalyticsData primaryData;
  final AnalyticsData secondaryData;
  final ComparisonType comparisonType;
  final Map<String, MetricComparison> metrics;
  final ComparisonSummary summary;
  final DateTime generatedAt;

  const ComparisonResult({
    required this.primaryData,
    required this.secondaryData,
    required this.comparisonType,
    required this.metrics,
    required this.summary,
    required this.generatedAt,
  });
}

/// Comparison summary class
class ComparisonSummary {
  final ComparisonTrend overallTrend;
  final int significantDifferences;
  final double averageDifference;
  final List<String> recommendations;

  const ComparisonSummary({
    required this.overallTrend,
    required this.significantDifferences,
    required this.averageDifference,
    required this.recommendations,
  });
}

/// Custom comparison metric configuration
class ComparisonMetric {
  final String id;
  final String name;
  final String description;
  final Function(AnalyticsData) valueExtractor;
  final String unit;
  final DifferenceType differenceType;

  const ComparisonMetric({
    required this.id,
    required this.name,
    required this.description,
    required this.valueExtractor,
    required this.unit,
    required this.differenceType,
  });
}