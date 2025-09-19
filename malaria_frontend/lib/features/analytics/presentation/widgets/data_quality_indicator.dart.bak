/// Data quality indicator widget
///
/// This widget displays data quality metrics including completeness,
/// accuracy, freshness, and source reliability indicators.
///
/// Usage:
/// ```dart
/// DataQualityIndicator(
///   dataQuality: dataQualityMetrics,
/// );
/// ```

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';

/// Data quality indicator widget
class DataQualityIndicator extends StatelessWidget {
  /// Data quality metrics to display
  final DataQuality dataQuality;

  /// Constructor requiring data quality metrics
  const DataQualityIndicator({
    super.key,
    required this.dataQuality,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            const SizedBox(height: 16),
            _buildQualityMetrics(context),
            const SizedBox(height: 16),
            _buildSourcesInfo(context),
          ],
        ),
      ),
    );
  }

  /// Builds the header
  Widget _buildHeader(BuildContext context) {
    final overallScore = _calculateOverallScore();
    final scoreColor = _getScoreColor(overallScore);

    return Row(
      children: [
        Icon(
          Icons.data_usage,
          color: scoreColor,
          size: 24,
        ),
        const SizedBox(width: 8),
        Text(
          'Data Quality',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const Spacer(),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: scoreColor.withValues(alpha:0.1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: scoreColor.withValues(alpha:0.3)),
          ),
          child: Text(
            '${(overallScore * 100).toInt()}%',
            style: TextStyle(
              color: scoreColor,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
        ),
      ],
    );
  }

  /// Builds quality metrics indicators
  Widget _buildQualityMetrics(BuildContext context) {
    return Column(
      children: [
        _buildMetricRow(
          context,
          'Completeness',
          dataQuality.completeness,
          Icons.check_circle_outline,
        ),
        const SizedBox(height: 12),
        _buildMetricRow(
          context,
          'Accuracy',
          dataQuality.accuracy,
          Icons.target,
        ),
        const SizedBox(height: 12),
        _buildFreshnessIndicator(context),
      ],
    );
  }

  /// Builds individual metric row
  Widget _buildMetricRow(
    BuildContext context,
    String label,
    double value,
    IconData icon,
  ) {
    final color = _getScoreColor(value);

    return Row(
      children: [
        Icon(
          icon,
          color: color,
          size: 20,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          flex: 2,
          child: LinearProgressIndicator(
            value: value,
            backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 50,
          child: Text(
            '${(value * 100).toInt()}%',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.end,
          ),
        ),
      ],
    );
  }

  /// Builds freshness indicator
  Widget _buildFreshnessIndicator(BuildContext context) {
    final freshnessColor = _getFreshnessColor(dataQuality.freshnessHours);
    final freshnessLabel = _getFreshnessLabel(dataQuality.freshnessHours);

    return Row(
      children: [
        Icon(
          Icons.access_time,
          color: freshnessColor,
          size: 20,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            'Freshness',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: freshnessColor.withValues(alpha:0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            freshnessLabel,
            style: TextStyle(
              color: freshnessColor,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }

  /// Builds sources information
  Widget _buildSourcesInfo(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Data Sources',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _buildSourcesCard(
                context,
                'Total Sources',
                dataQuality.sourcesCount.toString(),
                Icons.storage,
                Theme.of(context).colorScheme.primary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildSourcesCard(
                context,
                'Issues',
                dataQuality.sourcesWithIssues.length.toString(),
                Icons.warning,
                dataQuality.sourcesWithIssues.isEmpty
                    ? Colors.green
                    : Colors.orange,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildSourcesCard(
                context,
                'Last Update',
                _formatLastUpdate(dataQuality.lastUpdate),
                Icons.update,
                Theme.of(context).colorScheme.secondary,
              ),
            ),
          ],
        ),
        if (dataQuality.sourcesWithIssues.isNotEmpty) ...[
          const SizedBox(height: 12),
          _buildIssuesSection(context),
        ],
      ],
    );
  }

  /// Builds individual sources card
  Widget _buildSourcesCard(
    BuildContext context,
    String title,
    String value,
    IconData icon,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha:0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha:0.3)),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            color: color,
            size: 24,
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: color,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            title,
            style: Theme.of(context).textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Builds issues section
  Widget _buildIssuesSection(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.orange.withValues(alpha:0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange.withValues(alpha:0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.warning,
                color: Colors.orange,
                size: 16,
              ),
              const SizedBox(width: 4),
              Text(
                'Sources with Issues',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w500,
                  color: Colors.orange,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            dataQuality.sourcesWithIssues.join(', '),
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  /// Calculates overall quality score
  double _calculateOverallScore() {
    return (dataQuality.completeness + dataQuality.accuracy) / 2;
  }

  /// Gets color based on score
  Color _getScoreColor(double score) {
    if (score >= 0.8) {
      return Colors.green;
    } else if (score >= 0.6) {
      return Colors.orange;
    } else {
      return Colors.red;
    }
  }

  /// Gets freshness color based on hours
  Color _getFreshnessColor(double hours) {
    if (hours <= 2) {
      return Colors.green;
    } else if (hours <= 12) {
      return Colors.orange;
    } else {
      return Colors.red;
    }
  }

  /// Gets freshness label
  String _getFreshnessLabel(double hours) {
    if (hours < 1) {
      return '< 1 hour';
    } else if (hours < 24) {
      return '${hours.toInt()} hours';
    } else {
      final days = (hours / 24).toInt();
      return '$days day${days > 1 ? 's' : ''}';
    }
  }

  /// Formats last update time
  String _formatLastUpdate(DateTime lastUpdate) {
    final now = DateTime.now();
    final difference = now.difference(lastUpdate);

    if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else {
      return DateFormat('MMM d').format(lastUpdate);
    }
  }
}