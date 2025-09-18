/// Analytics overview card widget for displaying key metrics
///
/// This widget displays a single key metric with an icon, value, and trend indicator.
/// It provides a clean, consistent way to show important analytics data at a glance.
///
/// Usage:
/// ```dart
/// AnalyticsOverviewCard(
///   title: 'Prediction Accuracy',
///   value: '85%',
///   icon: Icons.accuracy,
///   color: Colors.blue,
///   trend: 0.05, // 5% increase
/// );
/// ```

import 'package:flutter/material.dart';

/// Overview card widget for displaying analytics metrics
class AnalyticsOverviewCard extends StatelessWidget {
  /// Card title
  final String title;

  /// Primary value to display
  final String value;

  /// Icon representing the metric
  final IconData icon;

  /// Primary color for the card
  final Color color;

  /// Trend value (-1.0 to 1.0, where positive is improvement)
  final double trend;

  /// Optional subtitle text
  final String? subtitle;

  /// Optional onTap callback
  final VoidCallback? onTap;

  /// Whether to show trend indicator
  final bool showTrend;

  /// Constructor requiring essential parameters
  const AnalyticsOverviewCard({
    super.key,
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
    this.trend = 0.0,
    this.subtitle,
    this.onTap,
    this.showTrend = true,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            gradient: LinearGradient(
              colors: [
                color.withOpacity(0.1),
                color.withOpacity(0.05),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      icon,
                      color: color,
                      size: 20,
                    ),
                  ),
                  const Spacer(),
                  if (showTrend) _buildTrendIndicator(),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                value,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                title,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 4),
                Text(
                  subtitle!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  /// Builds trend indicator with arrow and percentage
  Widget _buildTrendIndicator() {
    if (trend == 0.0) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: Colors.grey.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          '0%',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: Colors.grey[600],
          ),
        ),
      );
    }

    final isPositive = trend > 0;
    final percentage = (trend.abs() * 100).toStringAsFixed(1);
    final trendColor = isPositive ? Colors.green : Colors.red;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: trendColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isPositive ? Icons.trending_up : Icons.trending_down,
            size: 12,
            color: trendColor,
          ),
          const SizedBox(width: 2),
          Text(
            '$percentage%',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: trendColor,
            ),
          ),
        ],
      ),
    );
  }
}