/// Confusion matrix chart widget for model performance analysis
///
/// This widget displays confusion matrix data using custom visualizations
/// to show detailed classification performance and error analysis.
///
/// Usage:
/// ```dart
/// ConfusionMatrixChart(
///   confusionMatrix: predictionMetrics.confusionMatrix,
///   height: 350,
///   showPercentages: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../../domain/entities/prediction_metrics.dart';

/// Confusion matrix chart widget for classification analysis
class ConfusionMatrixChart extends StatefulWidget {
  /// Confusion matrix data to display
  final ConfusionMatrix confusionMatrix;

  /// Chart height
  final double height;

  /// Whether to show percentages instead of counts
  final bool showPercentages;

  /// Whether to show detailed statistics
  final bool showStatistics;

  /// Custom color scheme for the matrix
  final ConfusionMatrixColorScheme? colorScheme;

  /// Constructor with required confusion matrix data
  const ConfusionMatrixChart({
    super.key,
    required this.confusionMatrix,
    this.height = 350,
    this.showPercentages = false,
    this.showStatistics = true,
    this.colorScheme,
  });

  @override
  State<ConfusionMatrixChart> createState() => _ConfusionMatrixChartState();
}

class _ConfusionMatrixChartState extends State<ConfusionMatrixChart> {
  /// Selected cell for detailed information
  _MatrixCell? _selectedCell;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = widget.colorScheme ?? ConfusionMatrixColorScheme.defaultScheme(theme.colorScheme);

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
            _buildHeader(theme),
            const SizedBox(height: 16),
            Expanded(
              child: widget.confusionMatrix.totalPredictions == 0
                  ? _buildNoDataMessage(theme)
                  : Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: _buildMatrix(colorScheme),
                        ),
                        if (widget.showStatistics) ...[
                          const SizedBox(width: 16),
                          Expanded(
                            flex: 2,
                            child: _buildStatistics(theme),
                          ),
                        ],
                      ],
                    ),
            ),
            const SizedBox(height: 8),
            _buildLegend(theme, colorScheme),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header with title and accuracy
  Widget _buildHeader(ThemeData theme) {
    final accuracy = widget.confusionMatrix.accuracy;
    final totalPredictions = widget.confusionMatrix.totalPredictions;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Confusion Matrix',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '$totalPredictions predictions',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          ],
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: theme.colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(
            'Accuracy: ${(accuracy * 100).toStringAsFixed(1)}%',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onPrimaryContainer,
            ),
          ),
        ),
      ],
    );
  }

  /// Builds the confusion matrix visualization
  Widget _buildMatrix(ConfusionMatrixColorScheme colorScheme) {
    final matrix = widget.confusionMatrix;
    final total = matrix.totalPredictions;

    if (total == 0) {
      return _buildNoDataMessage(Theme.of(context));
    }

    // Calculate cell sizes and intensities
    final cellData = [
      _MatrixCell(
        value: matrix.truePositives,
        percentage: matrix.truePositives / total,
        row: 0,
        col: 1,
        label: 'True Positive',
        type: _CellType.truePositive,
      ),
      _MatrixCell(
        value: matrix.falsePositive,
        percentage: matrix.falsePositive / total,
        row: 0,
        col: 0,
        label: 'False Positive',
        type: _CellType.falsePositive,
      ),
      _MatrixCell(
        value: matrix.falseNegatives,
        percentage: matrix.falseNegatives / total,
        row: 1,
        col: 1,
        label: 'False Negative',
        type: _CellType.falseNegative,
      ),
      _MatrixCell(
        value: matrix.trueNegatives,
        percentage: matrix.trueNegatives / total,
        row: 1,
        col: 0,
        label: 'True Negative',
        type: _CellType.trueNegative,
      ),
    ];

    return Column(
      children: [
        // Column headers
        Row(
          children: [
            const SizedBox(width: 80), // Space for row labels
            Expanded(child: _buildColumnHeader('Predicted\nNegative')),
            Expanded(child: _buildColumnHeader('Predicted\nPositive')),
          ],
        ),
        const SizedBox(height: 8),
        // Matrix rows
        Expanded(
          child: Column(
            children: [
              // Actual Positive row
              Expanded(
                child: Row(
                  children: [
                    SizedBox(
                      width: 80,
                      child: _buildRowHeader('Actual\nPositive'),
                    ),
                    Expanded(
                      child: _buildMatrixCell(
                        cellData.firstWhere((c) => c.row == 0 && c.col == 0),
                        colorScheme,
                      ),
                    ),
                    Expanded(
                      child: _buildMatrixCell(
                        cellData.firstWhere((c) => c.row == 0 && c.col == 1),
                        colorScheme,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              // Actual Negative row
              Expanded(
                child: Row(
                  children: [
                    SizedBox(
                      width: 80,
                      child: _buildRowHeader('Actual\nNegative'),
                    ),
                    Expanded(
                      child: _buildMatrixCell(
                        cellData.firstWhere((c) => c.row == 1 && c.col == 1),
                        colorScheme,
                      ),
                    ),
                    Expanded(
                      child: _buildMatrixCell(
                        cellData.firstWhere((c) => c.row == 1 && c.col == 0),
                        colorScheme,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds column header
  Widget _buildColumnHeader(String text) {
    return Container(
      alignment: Alignment.center,
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  /// Builds row header
  Widget _buildRowHeader(String text) {
    return Container(
      alignment: Alignment.center,
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  /// Builds individual matrix cell
  Widget _buildMatrixCell(_MatrixCell cell, ConfusionMatrixColorScheme colorScheme) {
    final isSelected = _selectedCell == cell;
    final intensity = cell.percentage.clamp(0.1, 1.0); // Minimum 10% intensity

    Color cellColor;
    switch (cell.type) {
      case _CellType.truePositive:
        cellColor = colorScheme.truePositive.withValues(alpha: intensity);
        break;
      case _CellType.trueNegative:
        cellColor = colorScheme.trueNegative.withValues(alpha: intensity);
        break;
      case _CellType.falsePositive:
        cellColor = colorScheme.falsePositive.withValues(alpha: intensity);
        break;
      case _CellType.falseNegative:
        cellColor = colorScheme.falseNegative.withValues(alpha: intensity);
        break;
    }

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedCell = _selectedCell == cell ? null : cell;
        });
      },
      child: Container(
        margin: const EdgeInsets.all(2),
        decoration: BoxDecoration(
          color: cellColor,
          borderRadius: BorderRadius.circular(8),
          border: isSelected
              ? Border.all(
                  color: Theme.of(context).colorScheme.primary,
                  width: 3,
                )
              : null,
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              widget.showPercentages
                  ? '${(cell.percentage * 100).toStringAsFixed(1)}%'
                  : cell.value.toString(),
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: _getTextColor(cellColor),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              cell.label,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: _getTextColor(cellColor).withValues(alpha: 0.8),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Gets appropriate text color based on background
  Color _getTextColor(Color backgroundColor) {
    final luminance = backgroundColor.computeLuminance();
    return luminance > 0.5 ? Colors.black87 : Colors.white;
  }

  /// Builds statistics panel
  Widget _buildStatistics(ThemeData theme) {
    final matrix = widget.confusionMatrix;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Performance Metrics',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          _buildStatistic('Accuracy', matrix.accuracy, theme),
          _buildStatistic('Precision', matrix.precision, theme),
          _buildStatistic('Recall', matrix.recall, theme),
          _buildStatistic('Specificity', matrix.specificity, theme),
          const SizedBox(height: 12),
          if (_selectedCell != null) ...[
            Text(
              'Selected Cell',
              style: theme.textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            _buildCellDetails(_selectedCell!, theme),
          ],
        ],
      ),
    );
  }

  /// Builds individual statistic item
  Widget _buildStatistic(String label, double value, ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: theme.textTheme.bodyMedium,
          ),
          Text(
            '${(value * 100).toStringAsFixed(1)}%',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  /// Builds selected cell details
  Widget _buildCellDetails(_MatrixCell cell, ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          cell.label,
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Count: ${cell.value}',
          style: theme.textTheme.bodySmall,
        ),
        Text(
          'Percentage: ${(cell.percentage * 100).toStringAsFixed(1)}%',
          style: theme.textTheme.bodySmall,
        ),
      ],
    );
  }

  /// Builds legend for matrix colors
  Widget _buildLegend(ThemeData theme, ConfusionMatrixColorScheme colorScheme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildLegendItem('Correct', colorScheme.truePositive, theme),
        _buildLegendItem('Error', colorScheme.falsePositive, theme),
        Text(
          'Tap cells for details',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
          ),
        ),
      ],
    );
  }

  /// Builds individual legend item
  Widget _buildLegendItem(String label, Color color, ThemeData theme) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: theme.textTheme.bodySmall,
        ),
      ],
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage(ThemeData theme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.grid_3x3_outlined,
            size: 48,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No confusion matrix data available',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Matrix will appear when prediction data is available',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

/// Matrix cell data structure
class _MatrixCell {
  final int value;
  final double percentage;
  final int row;
  final int col;
  final String label;
  final _CellType type;

  _MatrixCell({
    required this.value,
    required this.percentage,
    required this.row,
    required this.col,
    required this.label,
    required this.type,
  });

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is _MatrixCell && other.row == row && other.col == col;
  }

  @override
  int get hashCode => Object.hash(row, col);
}

/// Cell type enumeration
enum _CellType {
  truePositive,
  trueNegative,
  falsePositive,
  falseNegative,
}

/// Color scheme for confusion matrix
class ConfusionMatrixColorScheme {
  final Color truePositive;
  final Color trueNegative;
  final Color falsePositive;
  final Color falseNegative;

  const ConfusionMatrixColorScheme({
    required this.truePositive,
    required this.trueNegative,
    required this.falsePositive,
    required this.falseNegative,
  });

  /// Default color scheme based on material color scheme
  factory ConfusionMatrixColorScheme.defaultScheme(ColorScheme colorScheme) {
    return ConfusionMatrixColorScheme(
      truePositive: Colors.green,
      trueNegative: Colors.blue,
      falsePositive: Colors.orange,
      falseNegative: Colors.red,
    );
  }

  /// High contrast color scheme
  factory ConfusionMatrixColorScheme.highContrast() {
    return const ConfusionMatrixColorScheme(
      truePositive: Color(0xFF2E7D32), // Dark green
      trueNegative: Color(0xFF1565C0), // Dark blue
      falsePositive: Color(0xFFEF6C00), // Dark orange
      falseNegative: Color(0xFFC62828), // Dark red
    );
  }

  /// Accessible color scheme for color-blind users
  factory ConfusionMatrixColorScheme.accessible() {
    return const ConfusionMatrixColorScheme(
      truePositive: Color(0xFF4CAF50), // Green
      trueNegative: Color(0xFF2196F3), // Blue
      falsePositive: Color(0xFF9C27B0), // Purple
      falseNegative: Color(0xFFFF5722), // Deep orange
    );
  }
}