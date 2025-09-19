/// Model performance comparison widget for analytics dashboard
///
/// This widget provides comprehensive comparison of multiple model performances
/// including accuracy metrics, resource usage, and deployment status visualization.
///
/// Usage:
/// ```dart
/// ModelPerformanceWidget(
///   models: predictionMetrics.models,
///   selectedModel: 'malaria_model_v2',
///   onModelSelected: (modelId) => updateSelectedModel(modelId),
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../domain/entities/prediction_metrics.dart';

/// Model performance comparison widget for analytics dashboard
class ModelPerformanceWidget extends StatefulWidget {
  /// List of model performances to compare
  final List<ModelPerformance> models;

  /// Currently selected model ID
  final String? selectedModel;

  /// Callback when a model is selected
  final ValueChanged<String>? onModelSelected;

  /// Whether the widget is in loading state
  final bool isLoading;

  /// Error message to display if any
  final String? errorMessage;

  /// Widget height
  final double height;

  /// Whether to show detailed comparison
  final bool showDetailedComparison;

  /// Metrics to display in comparison
  final List<String> metricsToShow;

  /// Constructor with required models list
  const ModelPerformanceWidget({
    super.key,
    required this.models,
    this.selectedModel,
    this.onModelSelected,
    this.isLoading = false,
    this.errorMessage,
    this.height = 400,
    this.showDetailedComparison = true,
    this.metricsToShow = const ['accuracy', 'precision', 'recall', 'f1Score'],
  });

  @override
  State<ModelPerformanceWidget> createState() => _ModelPerformanceWidgetState();
}

class _ModelPerformanceWidgetState extends State<ModelPerformanceWidget>
    with TickerProviderStateMixin {
  /// Animation controller for chart animations
  late AnimationController _animationController;

  /// Currently selected metric for detailed view
  String _selectedMetric = 'accuracy';

  /// Whether to show chart or table view
  bool _showChartView = true;

  /// Sort order for model comparison
  String _sortBy = 'accuracy';
  bool _sortAscending = false;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _animationController.forward();
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
                : widget.models.isEmpty
                    ? _buildEmptyState(theme)
                    : _buildContent(theme, colorScheme),
      ),
    );
  }

  /// Builds the main content of the widget
  Widget _buildContent(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildHeader(theme, colorScheme),
        const SizedBox(height: 16),
        _buildControls(theme, colorScheme),
        const SizedBox(height: 16),
        Expanded(
          child: _showChartView
              ? _buildChartView(theme, colorScheme)
              : _buildTableView(theme, colorScheme),
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
            color: colorScheme.secondary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            Icons.speed,
            size: 20,
            color: colorScheme.secondary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Model Performance Comparison',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '${widget.models.length} models compared',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        _buildBestModelIndicator(theme, colorScheme),
      ],
    );
  }

  /// Builds best model indicator
  Widget _buildBestModelIndicator(ThemeData theme, ColorScheme colorScheme) {
    if (widget.models.isEmpty) return const SizedBox.shrink();

    final bestModel = widget.models.reduce((a, b) =>
        a.accuracy > b.accuracy ? a : b);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.green.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.star,
            size: 16,
            color: Colors.green,
          ),
          const SizedBox(width: 4),
          Text(
            'Best: ${bestModel.modelName}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: Colors.green,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds control panel for view options
  Widget _buildControls(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        // View toggle
        Container(
          decoration: BoxDecoration(
            color: colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildToggleButton(
                icon: Icons.bar_chart,
                label: 'Chart',
                isSelected: _showChartView,
                onTap: () => setState(() => _showChartView = true),
                theme: theme,
                colorScheme: colorScheme,
              ),
              _buildToggleButton(
                icon: Icons.table_chart,
                label: 'Table',
                isSelected: !_showChartView,
                onTap: () => setState(() => _showChartView = false),
                theme: theme,
                colorScheme: colorScheme,
              ),
            ],
          ),
        ),
        const SizedBox(width: 16),
        // Metric selector
        if (_showChartView) ...[
          Text(
            'Metric:',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(width: 8),
          DropdownButton<String>(
            value: _selectedMetric,
            items: widget.metricsToShow.map((metric) {
              return DropdownMenuItem(
                value: metric,
                child: Text(_getMetricDisplayName(metric)),
              );
            }).toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() => _selectedMetric = value);
              }
            },
            underline: Container(),
          ),
        ],
        const Spacer(),
        // Sort controls
        if (!_showChartView) ...[
          Text(
            'Sort by:',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(width: 8),
          DropdownButton<String>(
            value: _sortBy,
            items: ['accuracy', 'modelName', 'trainedAt', 'status'].map((field) {
              return DropdownMenuItem(
                value: field,
                child: Text(_getSortFieldDisplayName(field)),
              );
            }).toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() => _sortBy = value);
              }
            },
            underline: Container(),
          ),
          IconButton(
            icon: Icon(
              _sortAscending ? Icons.arrow_upward : Icons.arrow_downward,
              size: 18,
            ),
            onPressed: () => setState(() => _sortAscending = !_sortAscending),
          ),
        ],
      ],
    );
  }

  /// Builds toggle button for view switching
  Widget _buildToggleButton({
    required IconData icon,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
    required ThemeData theme,
    required ColorScheme colorScheme,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? colorScheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 16,
              color: isSelected
                  ? colorScheme.onPrimary
                  : colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            const SizedBox(width: 4),
            Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                color: isSelected
                    ? colorScheme.onPrimary
                    : colorScheme.onSurface.withValues(alpha: 0.7),
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds chart view for model comparison
  Widget _buildChartView(ThemeData theme, ColorScheme colorScheme) {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return Column(
          children: [
            Expanded(
              flex: 3,
              child: _buildBarChart(theme, colorScheme),
            ),
            const SizedBox(height: 16),
            Expanded(
              flex: 1,
              child: _buildModelLegend(theme, colorScheme),
            ),
          ],
        );
      },
    );
  }

  /// Builds bar chart for metric comparison
  Widget _buildBarChart(ThemeData theme, ColorScheme colorScheme) {
    final sortedModels = List<ModelPerformance>.from(widget.models);
    sortedModels.sort((a, b) {
      final aValue = _getMetricValue(a, _selectedMetric);
      final bValue = _getMetricValue(b, _selectedMetric);
      return bValue.compareTo(aValue);
    });

    final barGroups = sortedModels.asMap().entries.map((entry) {
      final index = entry.key;
      final model = entry.value;
      final value = _getMetricValue(model, _selectedMetric);
      final isSelected = model.modelId == widget.selectedModel;

      return BarChartGroupData(
        x: index,
        barRods: [
          BarChartRodData(
            toY: value * _animationController.value,
            color: isSelected
                ? colorScheme.primary
                : _getModelColor(index, colorScheme),
            width: 24,
            borderRadius: BorderRadius.circular(4),
            gradient: LinearGradient(
              colors: [
                (isSelected ? colorScheme.primary : _getModelColor(index, colorScheme))
                    .withValues(alpha: 0.8),
                isSelected ? colorScheme.primary : _getModelColor(index, colorScheme),
              ],
              begin: Alignment.bottomCenter,
              end: Alignment.topCenter,
            ),
          ),
        ],
      );
    }).toList();

    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: 1.0,
        barGroups: barGroups,
        titlesData: FlTitlesData(
          show: true,
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index >= 0 && index < sortedModels.length) {
                  final model = sortedModels[index];
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      model.modelName.length > 8
                          ? '${model.modelName.substring(0, 8)}...'
                          : model.modelName,
                      style: theme.textTheme.bodySmall,
                    ),
                  );
                }
                return const SizedBox.shrink();
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                return Text(
                  '${(value * 100).toStringAsFixed(0)}%',
                  style: theme.textTheme.bodySmall,
                );
              },
              reservedSize: 40,
            ),
          ),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: false),
        gridData: FlGridData(
          show: true,
          drawHorizontalLine: true,
          drawVerticalLine: false,
          horizontalInterval: 0.2,
          getDrawingHorizontalLine: (value) => FlLine(
            color: colorScheme.outline.withValues(alpha: 0.2),
            strokeWidth: 1,
          ),
        ),
        barTouchData: BarTouchData(
          enabled: true,
          touchTooltipData: BarTouchTooltipData(
            tooltipBgColor: colorScheme.inverseSurface,
            tooltipRoundedRadius: 8,
            getTooltipItem: (group, groupIndex, rod, rodIndex) {
              final model = sortedModels[group.x];
              final value = _getMetricValue(model, _selectedMetric);
              return BarTooltipItem(
                '${model.modelName}\n${_getMetricDisplayName(_selectedMetric)}: ${(value * 100).toStringAsFixed(1)}%\nStatus: ${_getStatusDisplayName(model.status)}',
                TextStyle(
                  color: colorScheme.onInverseSurface,
                  fontWeight: FontWeight.w500,
                  fontSize: 12,
                ),
              );
            },
          ),
          touchCallback: (FlTouchEvent event, barTouchResponse) {
            if (event is FlTapUpEvent && barTouchResponse != null) {
              final touchedGroup = barTouchResponse.spot?.touchedBarGroup;
              if (touchedGroup != null) {
                final model = sortedModels[touchedGroup.x];
                widget.onModelSelected?.call(model.modelId);
              }
            }
          },
        ),
      ),
    );
  }

  /// Builds model legend
  Widget _buildModelLegend(ThemeData theme, ColorScheme colorScheme) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: widget.models.asMap().entries.map((entry) {
          final index = entry.key;
          final model = entry.value;
          final isSelected = model.modelId == widget.selectedModel;

          return GestureDetector(
            onTap: () => widget.onModelSelected?.call(model.modelId),
            child: Container(
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: isSelected
                    ? colorScheme.primary.withValues(alpha: 0.1)
                    : colorScheme.surface,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: isSelected
                      ? colorScheme.primary
                      : colorScheme.outline.withValues(alpha: 0.3),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: isSelected
                          ? colorScheme.primary
                          : _getModelColor(index, colorScheme),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        model.modelName,
                        style: theme.textTheme.bodySmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: isSelected ? colorScheme.primary : null,
                        ),
                      ),
                      Text(
                        'v${model.version}',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  /// Builds table view for detailed comparison
  Widget _buildTableView(ThemeData theme, ColorScheme colorScheme) {
    final sortedModels = _getSortedModels();

    return SingleChildScrollView(
      child: DataTable(
        sortColumnIndex: _getSortColumnIndex(),
        sortAscending: _sortAscending,
        columns: [
          DataColumn(
            label: Text('Model', style: theme.textTheme.titleSmall),
            onSort: (columnIndex, ascending) => _onSort('modelName', ascending),
          ),
          DataColumn(
            label: Text('Accuracy', style: theme.textTheme.titleSmall),
            numeric: true,
            onSort: (columnIndex, ascending) => _onSort('accuracy', ascending),
          ),
          DataColumn(
            label: Text('Status', style: theme.textTheme.titleSmall),
            onSort: (columnIndex, ascending) => _onSort('status', ascending),
          ),
          DataColumn(
            label: Text('Trained', style: theme.textTheme.titleSmall),
            onSort: (columnIndex, ascending) => _onSort('trainedAt', ascending),
          ),
          DataColumn(
            label: Text('Actions', style: theme.textTheme.titleSmall),
          ),
        ],
        rows: sortedModels.map((model) {
          final isSelected = model.modelId == widget.selectedModel;

          return DataRow(
            selected: isSelected,
            cells: [
              DataCell(
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      model.modelName,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'v${model.version}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                  ],
                ),
              ),
              DataCell(
                Text(
                  '${(model.accuracy * 100).toStringAsFixed(1)}%',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _getAccuracyColor(model.accuracy),
                  ),
                ),
              ),
              DataCell(_buildStatusChip(model.status, theme, colorScheme)),
              DataCell(
                Text(
                  _formatDate(model.trainedAt),
                  style: theme.textTheme.bodySmall,
                ),
              ),
              DataCell(
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (!isSelected)
                      TextButton(
                        onPressed: () => widget.onModelSelected?.call(model.modelId),
                        child: Text('Select'),
                      ),
                    IconButton(
                      icon: Icon(Icons.info_outline, size: 18),
                      onPressed: () => _showModelDetails(model),
                    ),
                  ],
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }

  /// Builds status chip
  Widget _buildStatusChip(ModelStatus status, ThemeData theme, ColorScheme colorScheme) {
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
        color = Colors.purple;
        break;
      case ModelStatus.deprecated:
        color = Colors.grey;
        break;
      case ModelStatus.retired:
        color = Colors.red;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        _getStatusDisplayName(status),
        style: theme.textTheme.bodySmall?.copyWith(
          color: color,
          fontWeight: FontWeight.bold,
        ),
      ),
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
            'Loading model performance data...',
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
            'Error loading model data',
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

  /// Builds empty state
  Widget _buildEmptyState(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.model_training,
            size: 48,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No models available',
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Train or deploy models to see performance comparison',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Helper methods

  /// Gets metric value from model
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
        return model.accuracy;
    }
  }

  /// Gets metric display name
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
        return metric;
    }
  }

  /// Gets sort field display name
  String _getSortFieldDisplayName(String field) {
    switch (field) {
      case 'accuracy':
        return 'Accuracy';
      case 'modelName':
        return 'Model Name';
      case 'trainedAt':
        return 'Trained Date';
      case 'status':
        return 'Status';
      default:
        return field;
    }
  }

  /// Gets status display name
  String _getStatusDisplayName(ModelStatus status) {
    return status.name.toUpperCase();
  }

  /// Gets model color for visualization
  Color _getModelColor(int index, ColorScheme colorScheme) {
    final colors = [
      colorScheme.primary,
      colorScheme.secondary,
      colorScheme.tertiary,
      Colors.green,
      Colors.orange,
      Colors.red,
      Colors.purple,
      Colors.teal,
    ];
    return colors[index % colors.length];
  }

  /// Gets accuracy color
  Color _getAccuracyColor(double accuracy) {
    if (accuracy >= 0.9) return Colors.green;
    if (accuracy >= 0.8) return Colors.lightGreen;
    if (accuracy >= 0.7) return Colors.orange;
    return Colors.red;
  }

  /// Gets sorted models based on current sort settings
  List<ModelPerformance> _getSortedModels() {
    final models = List<ModelPerformance>.from(widget.models);
    models.sort((a, b) {
      int comparison;
      switch (_sortBy) {
        case 'accuracy':
          comparison = a.accuracy.compareTo(b.accuracy);
          break;
        case 'modelName':
          comparison = a.modelName.compareTo(b.modelName);
          break;
        case 'trainedAt':
          comparison = a.trainedAt.compareTo(b.trainedAt);
          break;
        case 'status':
          comparison = a.status.index.compareTo(b.status.index);
          break;
        default:
          comparison = 0;
      }
      return _sortAscending ? comparison : -comparison;
    });
    return models;
  }

  /// Gets sort column index
  int _getSortColumnIndex() {
    switch (_sortBy) {
      case 'modelName':
        return 0;
      case 'accuracy':
        return 1;
      case 'status':
        return 2;
      case 'trainedAt':
        return 3;
      default:
        return 0;
    }
  }

  /// Handles sort order change
  void _onSort(String field, bool ascending) {
    setState(() {
      _sortBy = field;
      _sortAscending = ascending;
    });
  }

  /// Formats date for display
  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays > 30) {
      return '${date.day}/${date.month}/${date.year}';
    } else if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else {
      return 'Just now';
    }
  }

  /// Shows model details dialog
  void _showModelDetails(ModelPerformance model) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${model.modelName} Details'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Version: ${model.version}'),
            Text('Accuracy: ${(model.accuracy * 100).toStringAsFixed(1)}%'),
            Text('Status: ${_getStatusDisplayName(model.status)}'),
            Text('Trained: ${_formatDate(model.trainedAt)}'),
            Text('Parameters: ${model.complexity.parameterCount}'),
            Text('Model Size: ${model.complexity.modelSizeMb.toStringAsFixed(1)} MB'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Close'),
          ),
        ],
      ),
    );
  }
}