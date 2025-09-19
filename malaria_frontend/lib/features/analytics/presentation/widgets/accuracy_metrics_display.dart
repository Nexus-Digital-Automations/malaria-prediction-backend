/// Accuracy metrics display widget with detailed breakdown
///
/// This widget provides comprehensive accuracy metrics visualization including
/// precision, recall, F1-score, specificity, and additional performance indicators.
///
/// Usage:
/// ```dart
/// AccuracyMetricsDisplay(
///   predictionMetrics: metrics,
///   showTrendIndicators: true,
///   enableInteraction: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../domain/entities/prediction_metrics.dart';
import '../../domain/entities/analytics_data.dart';

/// Comprehensive accuracy metrics display widget
class AccuracyMetricsDisplay extends StatefulWidget {
  /// Prediction metrics data to display
  final PredictionMetrics predictionMetrics;

  /// Whether to show trend indicators
  final bool showTrendIndicators;

  /// Whether to enable user interaction
  final bool enableInteraction;

  /// Whether the widget is in loading state
  final bool isLoading;

  /// Error message to display if any
  final String? errorMessage;

  /// Widget height
  final double height;

  /// Whether to show confusion matrix
  final bool showConfusionMatrix;

  /// Whether to animate metric changes
  final bool animateMetrics;

  /// Constructor with required prediction metrics
  const AccuracyMetricsDisplay({
    super.key,
    required this.predictionMetrics,
    this.showTrendIndicators = true,
    this.enableInteraction = true,
    this.isLoading = false,
    this.errorMessage,
    this.height = 500,
    this.showConfusionMatrix = true,
    this.animateMetrics = true,
  });

  @override
  State<AccuracyMetricsDisplay> createState() => _AccuracyMetricsDisplayState();
}

class _AccuracyMetricsDisplayState extends State<AccuracyMetricsDisplay>
    with TickerProviderStateMixin {
  /// Animation controller for metric animations
  late AnimationController _animationController;

  /// Currently selected metric for detailed view
  String? _selectedMetric;

  /// Currently hovered metric section
  String? _hoveredSection;

  /// Show detailed breakdown
  bool _showDetailedBreakdown = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    if (widget.animateMetrics) {
      _animationController.forward();
    } else {
      _animationController.value = 1.0;
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Container(
        height: widget.height,
        padding: const EdgeInsets.all(16),
        child: widget.isLoading
            ? _buildLoadingState(theme)
            : widget.errorMessage != null
                ? _buildErrorState(theme)
                : _buildContent(theme, colorScheme),
      ),
    );
  }

  /// Builds the main content
  Widget _buildContent(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildHeader(theme, colorScheme),
        const SizedBox(height: 16),
        _buildControls(theme, colorScheme),
        const SizedBox(height: 16),
        Expanded(
          child: Row(
            children: [
              Expanded(
                flex: 2,
                child: _buildMetricsOverview(theme, colorScheme),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 3,
                child: _showDetailedBreakdown
                    ? _buildDetailedBreakdown(theme, colorScheme)
                    : widget.showConfusionMatrix
                        ? _buildConfusionMatrix(theme, colorScheme)
                        : _buildPerformanceChart(theme, colorScheme),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds the widget header
  Widget _buildHeader(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: colorScheme.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            Icons.analytics_outlined,
            size: 20,
            color: colorScheme.primary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Accuracy Metrics',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'Model: ${widget.predictionMetrics.modelId}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        _buildOverallQualityIndicator(theme, colorScheme),
      ],
    );
  }

  /// Builds overall quality indicator
  Widget _buildOverallQualityIndicator(ThemeData theme, ColorScheme colorScheme) {
    final overallScore = (widget.predictionMetrics.overallAccuracy +
                         widget.predictionMetrics.precision +
                         widget.predictionMetrics.recall +
                         widget.predictionMetrics.f1Score) / 4;

    Color indicatorColor;
    IconData indicatorIcon;
    String tooltip;

    if (overallScore >= 0.9) {
      indicatorColor = Colors.green;
      indicatorIcon = Icons.verified;
      tooltip = 'Excellent Overall Performance';
    } else if (overallScore >= 0.8) {
      indicatorColor = Colors.lightGreen;
      indicatorIcon = Icons.check_circle;
      tooltip = 'Good Overall Performance';
    } else if (overallScore >= 0.7) {
      indicatorColor = Colors.orange;
      indicatorIcon = Icons.warning;
      tooltip = 'Fair Overall Performance';
    } else {
      indicatorColor = Colors.red;
      indicatorIcon = Icons.error;
      tooltip = 'Needs Improvement';
    }

    return Tooltip(
      message: tooltip,
      child: Container(
        padding: const EdgeInsets.all(6),
        decoration: BoxDecoration(
          color: indicatorColor.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Icon(
          indicatorIcon,
          size: 18,
          color: indicatorColor,
        ),
      ),
    );
  }

  /// Builds control panel
  Widget _buildControls(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Switch.adaptive(
          value: _showDetailedBreakdown,
          onChanged: (value) => setState(() => _showDetailedBreakdown = value),
        ),
        const SizedBox(width: 8),
        Text(
          'Detailed Breakdown',
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const Spacer(),
        Text(
          'Last Updated: ${_formatDateTime(widget.predictionMetrics.calculatedAt)}',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
          ),
        ),
      ],
    );
  }

  /// Builds metrics overview section
  Widget _buildMetricsOverview(ThemeData theme, ColorScheme colorScheme) {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return Column(
          children: [
            _buildMetricCard(
              'Overall Accuracy',
              widget.predictionMetrics.overallAccuracy,
              Icons.track_changes,
              theme,
              colorScheme,
              'accuracy',
            ),
            const SizedBox(height: 12),
            _buildMetricCard(
              'Precision',
              widget.predictionMetrics.precision,
              Icons.precision_manufacturing,
              theme,
              colorScheme,
              'precision',
            ),
            const SizedBox(height: 12),
            _buildMetricCard(
              'Recall',
              widget.predictionMetrics.recall,
              Icons.find_in_page,
              theme,
              colorScheme,
              'recall',
            ),
            const SizedBox(height: 12),
            _buildMetricCard(
              'F1 Score',
              widget.predictionMetrics.f1Score,
              Icons.balance,
              theme,
              colorScheme,
              'f1Score',
            ),
          ],
        );
      },
    );
  }

  /// Builds individual metric card
  Widget _buildMetricCard(
    String label,
    double value,
    IconData icon,
    ThemeData theme,
    ColorScheme colorScheme,
    String metricKey,
  ) {
    final animatedValue = value * _animationController.value;
    final isSelected = _selectedMetric == metricKey;
    final isHovered = _hoveredSection == metricKey;

    return GestureDetector(
      onTap: widget.enableInteraction
          ? () => setState(() => _selectedMetric = isSelected ? null : metricKey)
          : null,
      child: MouseRegion(
        onEnter: (_) => setState(() => _hoveredSection = metricKey),
        onExit: (_) => setState(() => _hoveredSection = null),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: EdgeInsets.all(isHovered || isSelected ? 16 : 12),
          decoration: BoxDecoration(
            color: isSelected
                ? colorScheme.primary.withValues(alpha: 0.1)
                : isHovered
                    ? colorScheme.surfaceContainerHighest
                    : colorScheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected
                  ? colorScheme.primary
                  : isHovered
                      ? colorScheme.outline.withValues(alpha: 0.3)
                      : Colors.transparent,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _getMetricColor(animatedValue).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  icon,
                  size: 20,
                  color: _getMetricColor(animatedValue),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: isSelected ? colorScheme.primary : null,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${(animatedValue * 100).toStringAsFixed(1)}%',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: _getMetricColor(animatedValue),
                      ),
                    ),
                    if (widget.showTrendIndicators) ...[
                      const SizedBox(height: 4),
                      _buildTrendIndicator(metricKey, theme),
                    ],
                  ],
                ),
              ),
              Column(
                children: [
                  SizedBox(
                    width: 40,
                    height: 40,
                    child: CircularProgressIndicator(
                      value: animatedValue,
                      strokeWidth: 3,
                      backgroundColor: colorScheme.outline.withValues(alpha: 0.2),
                      valueColor: AlwaysStoppedAnimation(
                        _getMetricColor(animatedValue),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Builds trend indicator for a metric
  Widget _buildTrendIndicator(String metricKey, ThemeData theme) {
    // Mock trend data - in real implementation, this would come from historical data
    final trends = {
      'accuracy': 0.02,
      'precision': -0.01,
      'recall': 0.03,
      'f1Score': 0.015,
    };

    final trend = trends[metricKey] ?? 0.0;
    final isPositive = trend > 0;
    final isNeutral = trend.abs() < 0.005;

    if (isNeutral) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.trending_flat,
            size: 12,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
          ),
          const SizedBox(width: 2),
          Text(
            'Stable',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              fontSize: 10,
            ),
          ),
        ],
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          isPositive ? Icons.trending_up : Icons.trending_down,
          size: 12,
          color: isPositive ? Colors.green : Colors.red,
        ),
        const SizedBox(width: 2),
        Text(
          '${(trend * 100).toStringAsFixed(1)}%',
          style: theme.textTheme.bodySmall?.copyWith(
            color: isPositive ? Colors.green : Colors.red,
            fontWeight: FontWeight.w600,
            fontSize: 10,
          ),
        ),
      ],
    );
  }

  /// Builds detailed breakdown view
  Widget _buildDetailedBreakdown(ThemeData theme, ColorScheme colorScheme) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Performance by Risk Level',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          ...widget.predictionMetrics.performanceByLevel.entries.map(
            (entry) => _buildRiskLevelPerformance(
              entry.key,
              entry.value,
              theme,
              colorScheme,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'Additional Metrics',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          _buildAdditionalMetrics(theme, colorScheme),
        ],
      ),
    );
  }

  /// Builds risk level performance section
  Widget _buildRiskLevelPerformance(
    RiskLevel riskLevel,
    PerformanceByLevel performance,
    ThemeData theme,
    ColorScheme colorScheme,
  ) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _buildRiskLevelIcon(riskLevel),
                const SizedBox(width: 8),
                Text(
                  riskLevel.name.toUpperCase(),
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Text(
                  'Samples: ${performance.sampleSize}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: _buildMiniMetric(
                    'Accuracy',
                    performance.accuracy,
                    theme,
                  ),
                ),
                Expanded(
                  child: _buildMiniMetric(
                    'Precision',
                    performance.precision,
                    theme,
                  ),
                ),
                Expanded(
                  child: _buildMiniMetric(
                    'Recall',
                    performance.recall,
                    theme,
                  ),
                ),
                Expanded(
                  child: _buildMiniMetric(
                    'F1',
                    performance.f1Score,
                    theme,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Builds mini metric display
  Widget _buildMiniMetric(String label, double value, ThemeData theme) {
    return Column(
      children: [
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          '${(value * 100).toStringAsFixed(0)}%',
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: _getMetricColor(value),
          ),
        ),
      ],
    );
  }

  /// Builds additional metrics section
  Widget _buildAdditionalMetrics(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      children: [
        _buildAdditionalMetricRow(
          'AUC-ROC',
          widget.predictionMetrics.aucRoc,
          'Area under ROC curve',
          theme,
        ),
        _buildAdditionalMetricRow(
          'AUC-PR',
          widget.predictionMetrics.aucPr,
          'Area under Precision-Recall curve',
          theme,
        ),
        _buildAdditionalMetricRow(
          'Matthews Correlation',
          widget.predictionMetrics.matthewsCorrelation,
          'Correlation coefficient for classification',
          theme,
        ),
        _buildAdditionalMetricRow(
          'Specificity',
          widget.predictionMetrics.confusionMatrix.specificity,
          'True negative rate',
          theme,
        ),
      ],
    );
  }

  /// Builds additional metric row
  Widget _buildAdditionalMetricRow(
    String label,
    double value,
    String description,
    ThemeData theme,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  description,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: LinearProgressIndicator(
              value: value.clamp(0.0, 1.0),
              backgroundColor: theme.colorScheme.outline.withValues(alpha: 0.2),
              valueColor: AlwaysStoppedAnimation(_getMetricColor(value)),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '${(value * 100).toStringAsFixed(1)}%',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: _getMetricColor(value),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds confusion matrix visualization
  Widget _buildConfusionMatrix(ThemeData theme, ColorScheme colorScheme) {
    final matrix = widget.predictionMetrics.confusionMatrix;
    final total = matrix.totalPredictions;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Confusion Matrix',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: GridView.count(
            crossAxisCount: 2,
            childAspectRatio: 1.2,
            children: [
              _buildMatrixCell(
                'True Positive',
                matrix.truePositives,
                total,
                Colors.green,
                theme,
              ),
              _buildMatrixCell(
                'False Positive',
                matrix.falsePositives,
                total,
                Colors.red,
                theme,
              ),
              _buildMatrixCell(
                'False Negative',
                matrix.falseNegatives,
                total,
                Colors.orange,
                theme,
              ),
              _buildMatrixCell(
                'True Negative',
                matrix.trueNegatives,
                total,
                Colors.blue,
                theme,
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds confusion matrix cell
  Widget _buildMatrixCell(
    String label,
    int value,
    int total,
    Color color,
    ThemeData theme,
  ) {
    final percentage = total > 0 ? (value / total) : 0.0;

    return Card(
      margin: const EdgeInsets.all(4),
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          gradient: LinearGradient(
            colors: [
              color.withValues(alpha: 0.1),
              color.withValues(alpha: 0.05),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w600,
                color: color,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              value.toString(),
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              '${(percentage * 100).toStringAsFixed(1)}%',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds performance chart
  Widget _buildPerformanceChart(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Metrics Radar Chart',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: RadarChart(
            RadarChartData(
              dataSets: [
                RadarDataSet(
                  fillColor: colorScheme.primary.withValues(alpha: 0.2),
                  borderColor: colorScheme.primary,
                  entryRadius: 3,
                  dataEntries: [
                    RadarEntry(value: widget.predictionMetrics.overallAccuracy * 5.0),
                    RadarEntry(value: widget.predictionMetrics.precision * 5.0),
                    RadarEntry(value: widget.predictionMetrics.recall * 5.0),
                    RadarEntry(value: widget.predictionMetrics.f1Score * 5.0),
                    RadarEntry(value: widget.predictionMetrics.aucRoc * 5.0),
                  ],
                ),
              ],
              radarBackgroundColor: Colors.transparent,
              borderData: FlBorderData(show: false),
              radarBorderData: BorderSide(
                color: colorScheme.outline.withValues(alpha: 0.2),
              ),
              titlePositionPercentageOffset: 0.2,
              titleTextStyle: theme.textTheme.bodySmall!,
              getTitle: (index, angle) {
                switch (index) {
                  case 0:
                    return const RadarChartTitle(text: 'Accuracy');
                  case 1:
                    return const RadarChartTitle(text: 'Precision');
                  case 2:
                    return const RadarChartTitle(text: 'Recall');
                  case 3:
                    return const RadarChartTitle(text: 'F1 Score');
                  case 4:
                    return const RadarChartTitle(text: 'AUC-ROC');
                  default:
                    return const RadarChartTitle(text: '');
                }
              },
              ticksTextStyle: theme.textTheme.bodySmall!,
              tickBorderData: BorderSide(
                color: colorScheme.outline.withValues(alpha: 0.2),
              ),
              gridBorderData: BorderSide(
                color: colorScheme.outline.withValues(alpha: 0.2),
              ),
            ),
          ),
        ),
      ],
    );
  }

  /// Builds loading state
  Widget _buildLoadingState(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation(theme.colorScheme.primary),
          ),
          const SizedBox(height: 16),
          Text(
            'Loading accuracy metrics...',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds error state
  Widget _buildErrorState(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline,
            size: 48,
            color: theme.colorScheme.error,
          ),
          const SizedBox(height: 16),
          Text(
            'Error loading metrics',
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.error,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            widget.errorMessage ?? 'Unknown error occurred',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Helper methods

  /// Gets risk level icon
  Widget _buildRiskLevelIcon(RiskLevel riskLevel) {
    IconData icon;
    Color color;

    switch (riskLevel) {
      case RiskLevel.low:
        icon = Icons.check_circle;
        color = Colors.green;
        break;
      case RiskLevel.medium:
        icon = Icons.warning_amber;
        color = Colors.orange;
        break;
      case RiskLevel.high:
        icon = Icons.error;
        color = Colors.red;
        break;
      case RiskLevel.critical:
        icon = Icons.dangerous;
        color = Colors.red[800]!;
        break;
    }

    return Icon(icon, size: 16, color: color);
  }

  /// Gets metric color based on value
  Color _getMetricColor(double value) {
    if (value >= 0.9) return Colors.green;
    if (value >= 0.8) return Colors.lightGreen;
    if (value >= 0.7) return Colors.orange;
    return Colors.red;
  }

  /// Formats DateTime for display
  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }
}