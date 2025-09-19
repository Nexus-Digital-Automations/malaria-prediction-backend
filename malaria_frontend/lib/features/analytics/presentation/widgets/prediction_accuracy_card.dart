/// Prediction accuracy overview card widget for analytics dashboard
///
/// This widget displays a comprehensive overview of prediction accuracy metrics
/// including overall accuracy, precision, recall, F1 score with interactive details.
///
/// Usage:
/// ```dart
/// PredictionAccuracyCard(
///   predictionAccuracy: analyticsData.predictionAccuracy,
///   isLoading: false,
///   onTap: () => Navigator.push(...),
/// );
/// ```
library;

import 'package:flutter/material.dart';
import '../../domain/entities/analytics_data.dart';

/// Prediction accuracy overview card for dashboard display
class PredictionAccuracyCard extends StatefulWidget {
  /// Prediction accuracy data to display
  final PredictionAccuracy predictionAccuracy;

  /// Whether the card is in loading state
  final bool isLoading;

  /// Error message to display if any
  final String? errorMessage;

  /// Callback for card tap interaction
  final VoidCallback? onTap;

  /// Card height customization
  final double height;

  /// Whether to show detailed metrics
  final bool showDetails;

  /// Whether to animate value changes
  final bool animateChanges;

  /// Constructor with required prediction accuracy data
  const PredictionAccuracyCard({
    super.key,
    required this.predictionAccuracy,
    this.isLoading = false,
    this.errorMessage,
    this.onTap,
    this.height = 280,
    this.showDetails = true,
    this.animateChanges = true,
  });

  @override
  State<PredictionAccuracyCard> createState() => _PredictionAccuracyCardState();
}

class _PredictionAccuracyCardState extends State<PredictionAccuracyCard>
    with TickerProviderStateMixin {
  /// Animation controller for value changes
  late AnimationController _animationController;

  /// Animation for overall accuracy
  late Animation<double> _accuracyAnimation;

  /// Animation for precision
  late Animation<double> _precisionAnimation;

  /// Animation for recall
  late Animation<double> _recallAnimation;

  /// Animation for F1 score
  late Animation<double> _f1Animation;

  /// Currently hovered metric for interaction
  String? _hoveredMetric;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
  }

  @override
  void didUpdateWidget(PredictionAccuracyCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.animateChanges &&
        oldWidget.predictionAccuracy != widget.predictionAccuracy) {
      _animateToNewValues();
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  /// Initializes animation controllers and animations
  void _initializeAnimations() {
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    _accuracyAnimation = Tween<double>(
      begin: 0.0,
      end: widget.predictionAccuracy.overall,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    _precisionAnimation = Tween<double>(
      begin: 0.0,
      end: widget.predictionAccuracy.precision,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    _recallAnimation = Tween<double>(
      begin: 0.0,
      end: widget.predictionAccuracy.recall,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    _f1Animation = Tween<double>(
      begin: 0.0,
      end: widget.predictionAccuracy.f1Score,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    if (widget.animateChanges) {
      _animationController.forward();
    } else {
      _animationController.value = 1.0;
    }
  }

  /// Animates to new values when data changes
  void _animateToNewValues() {
    _accuracyAnimation = Tween<double>(
      begin: _accuracyAnimation.value,
      end: widget.predictionAccuracy.overall,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    _precisionAnimation = Tween<double>(
      begin: _precisionAnimation.value,
      end: widget.predictionAccuracy.precision,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    _recallAnimation = Tween<double>(
      begin: _recallAnimation.value,
      end: widget.predictionAccuracy.recall,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    _f1Animation = Tween<double>(
      begin: _f1Animation.value,
      end: widget.predictionAccuracy.f1Score,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeOutCirc,
    ));

    _animationController.reset();
    _animationController.forward();
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
      child: InkWell(
        onTap: widget.onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          height: widget.height,
          padding: const EdgeInsets.all(16),
          child: widget.isLoading
              ? _buildLoadingState(theme)
              : widget.errorMessage != null
                  ? _buildErrorState(theme)
                  : _buildContent(theme, colorScheme),
        ),
      ),
    );
  }

  /// Builds the main content of the card
  Widget _buildContent(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildHeader(theme),
        const SizedBox(height: 16),
        Expanded(
          child: Row(
            children: [
              Expanded(
                flex: 2,
                child: _buildOverallAccuracy(theme, colorScheme),
              ),
              const SizedBox(width: 16),
              Expanded(
                flex: 3,
                child: widget.showDetails
                    ? _buildDetailedMetrics(theme, colorScheme)
                    : _buildAccuracyByRiskLevel(theme, colorScheme),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _buildFooter(theme),
      ],
    );
  }

  /// Builds the card header with title and status
  Widget _buildHeader(ThemeData theme) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            Icons.analytics_outlined,
            size: 20,
            color: theme.colorScheme.primary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Prediction Accuracy',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.onSurface,
                ),
              ),
              Text(
                'Model Performance Metrics',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        _buildPerformanceIndicator(theme),
      ],
    );
  }

  /// Builds performance indicator based on overall accuracy
  Widget _buildPerformanceIndicator(ThemeData theme) {
    final accuracy = widget.predictionAccuracy.overall;
    Color indicatorColor;
    IconData indicatorIcon;
    String tooltip;

    if (accuracy >= 0.9) {
      indicatorColor = Colors.green;
      indicatorIcon = Icons.verified;
      tooltip = 'Excellent Performance';
    } else if (accuracy >= 0.8) {
      indicatorColor = Colors.lightGreen;
      indicatorIcon = Icons.check_circle;
      tooltip = 'Good Performance';
    } else if (accuracy >= 0.7) {
      indicatorColor = Colors.orange;
      indicatorIcon = Icons.warning;
      tooltip = 'Fair Performance';
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

  /// Builds the overall accuracy display with circular progress
  Widget _buildOverallAccuracy(ThemeData theme, ColorScheme colorScheme) {
    return AnimatedBuilder(
      animation: _accuracyAnimation,
      builder: (context, child) {
        final accuracy = _accuracyAnimation.value;
        return Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 100,
                  height: 100,
                  child: CircularProgressIndicator(
                    value: accuracy,
                    strokeWidth: 8,
                    backgroundColor: colorScheme.outline.withValues(alpha: 0.2),
                    valueColor: AlwaysStoppedAnimation(
                      _getAccuracyColor(accuracy),
                    ),
                  ),
                ),
                Column(
                  children: [
                    Text(
                      '${(accuracy * 100).toStringAsFixed(1)}%',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: _getAccuracyColor(accuracy),
                      ),
                    ),
                    Text(
                      'Overall',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Accuracy',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
            ),
          ],
        );
      },
    );
  }

  /// Builds detailed metrics section
  Widget _buildDetailedMetrics(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      children: [
        _buildMetricRow(
          'Precision',
          _precisionAnimation,
          Icons.precision_manufacturing,
          theme,
          colorScheme,
          'precision',
        ),
        const SizedBox(height: 12),
        _buildMetricRow(
          'Recall',
          _recallAnimation,
          Icons.find_in_page,
          theme,
          colorScheme,
          'recall',
        ),
        const SizedBox(height: 12),
        _buildMetricRow(
          'F1 Score',
          _f1Animation,
          Icons.balance,
          theme,
          colorScheme,
          'f1',
        ),
      ],
    );
  }

  /// Builds individual metric row
  Widget _buildMetricRow(
    String label,
    Animation<double> animation,
    IconData icon,
    ThemeData theme,
    ColorScheme colorScheme,
    String metricKey,
  ) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) {
        final value = animation.value;
        final isHovered = _hoveredMetric == metricKey;

        return MouseRegion(
          onEnter: (_) => setState(() => _hoveredMetric = metricKey),
          onExit: (_) => setState(() => _hoveredMetric = null),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: EdgeInsets.all(isHovered ? 12 : 8),
            decoration: BoxDecoration(
              color: isHovered
                  ? colorScheme.surfaceContainerHighest
                  : colorScheme.surface.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isHovered
                    ? colorScheme.outline.withValues(alpha: 0.3)
                    : Colors.transparent,
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: _getAccuracyColor(value).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Icon(
                    icon,
                    size: 16,
                    color: _getAccuracyColor(value),
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
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 2),
                      LinearProgressIndicator(
                        value: value,
                        backgroundColor: colorScheme.outline.withValues(alpha: 0.2),
                        valueColor: AlwaysStoppedAnimation(
                          _getAccuracyColor(value),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '${(value * 100).toStringAsFixed(1)}%',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _getAccuracyColor(value),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  /// Builds accuracy by risk level visualization
  Widget _buildAccuracyByRiskLevel(ThemeData theme, ColorScheme colorScheme) {
    final byRiskLevel = widget.predictionAccuracy.byRiskLevel;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Accuracy by Risk Level',
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: ListView.builder(
            itemCount: byRiskLevel.length,
            itemBuilder: (context, index) {
              final entry = byRiskLevel.entries.elementAt(index);
              final riskLevel = entry.key;
              final accuracy = entry.value;

              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    _buildRiskLevelIcon(riskLevel),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            riskLevel.toUpperCase(),
                            style: theme.textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          LinearProgressIndicator(
                            value: accuracy,
                            backgroundColor: colorScheme.outline.withValues(alpha: 0.2),
                            valueColor: AlwaysStoppedAnimation(
                              _getRiskLevelColor(riskLevel),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      '${(accuracy * 100).toStringAsFixed(0)}%',
                      style: theme.textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  /// Builds risk level icon
  Widget _buildRiskLevelIcon(String riskLevel) {
    IconData icon;
    Color color;

    switch (riskLevel.toLowerCase()) {
      case 'low':
        icon = Icons.check_circle;
        color = Colors.green;
        break;
      case 'medium':
        icon = Icons.warning_amber;
        color = Colors.orange;
        break;
      case 'high':
        icon = Icons.error;
        color = Colors.red;
        break;
      case 'critical':
        icon = Icons.dangerous;
        color = Colors.red[800]!;
        break;
      default:
        icon = Icons.help;
        color = Colors.grey;
    }

    return Icon(icon, size: 16, color: color);
  }

  /// Builds the card footer with additional info
  Widget _buildFooter(ThemeData theme) {
    final trendData = widget.predictionAccuracy.trend;
    final lastUpdate = trendData.isNotEmpty ? trendData.last.date : DateTime.now();

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          'Last updated: ${_formatDateTime(lastUpdate)}',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
          ),
        ),
        if (widget.onTap != null)
          Text(
            'View Details →',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w500,
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
            'Loading prediction accuracy...',
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
            'Error loading accuracy data',
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

  /// Gets color based on accuracy value
  Color _getAccuracyColor(double accuracy) {
    if (accuracy >= 0.9) return Colors.green;
    if (accuracy >= 0.8) return Colors.lightGreen;
    if (accuracy >= 0.7) return Colors.orange;
    return Colors.red;
  }

  /// Gets color for risk level
  Color _getRiskLevelColor(String riskLevel) {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return Colors.green;
      case 'medium':
        return Colors.orange;
      case 'high':
        return Colors.red;
      case 'critical':
        return Colors.red[800]!;
      default:
        return Colors.grey;
    }
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