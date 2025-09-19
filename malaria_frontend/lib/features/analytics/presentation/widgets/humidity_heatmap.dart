/// Humidity heatmap widget using custom grid visualization
///
/// This widget displays comprehensive humidity data using a custom grid-based
/// heatmap visualization showing spatial and temporal humidity patterns,
/// including relative humidity, absolute humidity, and dew point measurements
/// with mosquito survival threshold indicators.
///
/// Usage:
/// ```dart
/// HumidityHeatmap(
///   humidityData: humidityData,
///   height: 400,
///   viewMode: HumidityViewMode.relative,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Humidity heatmap widget with custom grid visualization
class HumidityHeatmap extends StatefulWidget {
  /// Humidity data to display
  final HumidityData humidityData;

  /// Chart height
  final double height;

  /// View mode for humidity data presentation
  final HumidityViewMode viewMode;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Geographic coordinates for spatial filtering
  final List<Coordinates>? coordinates;

  /// Whether to show mosquito survival thresholds
  final bool showSurvivalThresholds;

  /// Whether to enable interactive tooltips
  final bool enableInteractivity;

  /// Constructor requiring humidity data
  const HumidityHeatmap({
    super.key,
    required this.humidityData,
    this.height = 350,
    this.viewMode = HumidityViewMode.relative,
    this.dateRange,
    this.coordinates,
    this.showSurvivalThresholds = true,
    this.enableInteractivity = true,
  });

  @override
  State<HumidityHeatmap> createState() => _HumidityHeatmapState();
}

class _HumidityHeatmapState extends State<HumidityHeatmap> {
  /// Current humidity view mode
  late HumidityViewMode _currentViewMode;

  /// Mosquito survival humidity threshold (60%)
  final double _survivalThreshold = 60.0;

  /// Optimal humidity range for mosquito breeding (70-90%)
  final double _optimalMinHumidity = 70.0;
  final double _optimalMaxHumidity = 90.0;

  /// Grid dimensions for heatmap
  final int _gridRows = 12; // Months
  final int _gridCols = 24; // Hours or spatial divisions

  /// Color gradient for humidity visualization
  final List<Color> _humidityGradient = [
    Colors.brown.shade800,    // Very dry (0-20%)
    Colors.orange.shade600,   // Dry (20-40%)
    Colors.yellow.shade600,   // Moderate (40-60%)
    Colors.green.shade400,    // Good (60-80%)
    Colors.blue.shade400,     // High (80-100%)
    Colors.indigo.shade600,   // Very high (>100% for absolute)
  ];

  /// Selected grid cell for detailed view
  GridCell? _selectedCell;

  /// Heatmap data matrix
  late List<List<HumidityCell>> _heatmapData;

  @override
  void initState() {
    super.initState();
    _currentViewMode = widget.viewMode;
    _generateHeatmapData();
  }

  @override
  void didUpdateWidget(HumidityHeatmap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.humidityData != widget.humidityData ||
        oldWidget.viewMode != widget.viewMode ||
        oldWidget.dateRange != widget.dateRange) {
      _generateHeatmapData();
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
            if (widget.showSurvivalThresholds) _buildThresholdIndicators(),
            const SizedBox(height: 12),
            Expanded(child: _buildHeatmap()),
            const SizedBox(height: 8),
            _buildColorScale(),
            if (_selectedCell != null) _buildSelectedCellInfo(),
          ],
        ),
      ),
    );
  }

  /// Builds the chart header with title and controls
  Widget _buildHeader() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Humidity Heatmap Analysis',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                _getViewModeDescription(_currentViewMode),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
        Row(
          children: [
            IconButton(
              icon: Icon(
                Icons.refresh,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () {
                setState(() {
                  _generateHeatmapData();
                });
              },
              tooltip: 'Refresh Heatmap',
            ),
            IconButton(
              icon: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: () => _showHumidityInfo(),
              tooltip: 'Humidity Analysis Info',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds humidity view mode selector
  Widget _buildViewModeSelector() {
    return Row(
      children: [
        Text(
          'View:',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: HumidityViewMode.values.map((mode) {
                final isSelected = mode == _currentViewMode;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(_getViewModeDisplayName(mode)),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        setState(() {
                          _currentViewMode = mode;
                          _generateHeatmapData();
                        });
                      }
                    },
                  ),
                );
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }

  /// Builds mosquito survival threshold indicators
  Widget _buildThresholdIndicators() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.green.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.green.shade200),
      ),
      child: Row(
        children: [
          Icon(
            Icons.info_outline,
            color: Colors.green.shade600,
            size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Mosquito Survival: ≥${_survivalThreshold.toStringAsFixed(0)}% | '
              'Optimal Breeding: ${_optimalMinHumidity.toStringAsFixed(0)}-${_optimalMaxHumidity.toStringAsFixed(0)}%',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.green.shade800,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the main humidity heatmap
  Widget _buildHeatmap() {
    if (_heatmapData.isEmpty) {
      return _buildNoDataMessage();
    }

    return Column(
      children: [
        // Y-axis labels (months or spatial coordinates)
        Expanded(
          child: Row(
            children: [
              // Y-axis labels
              SizedBox(
                width: 50,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: List.generate(_gridRows, (row) {
                    return Text(
                      _getYAxisLabel(row),
                      style: Theme.of(context).textTheme.bodySmall,
                      textAlign: TextAlign.center,
                    );
                  }),
                ),
              ),
              // Heatmap grid
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: Theme.of(context).dividerColor,
                      width: 1,
                    ),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Column(
                    children: List.generate(_gridRows, (row) {
                      return Expanded(
                        child: Row(
                          children: List.generate(_gridCols, (col) {
                            final cell = _heatmapData[row][col];
                            return Expanded(
                              child: GestureDetector(
                                onTap: widget.enableInteractivity ? () {
                                  setState(() {
                                    _selectedCell = GridCell(row: row, col: col);
                                  });
                                } : null,
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: _getHumidityColor(cell.value),
                                    border: Border.all(
                                      color: _selectedCell?.row == row && _selectedCell?.col == col
                                          ? Theme.of(context).colorScheme.primary
                                          : Colors.grey.shade300,
                                      width: _selectedCell?.row == row && _selectedCell?.col == col ? 2 : 0.5,
                                    ),
                                  ),
                                  child: widget.enableInteractivity
                                      ? Tooltip(
                                          message: _getCellTooltip(cell, row, col),
                                          child: const SizedBox.expand(),
                                        )
                                      : const SizedBox.expand(),
                                ),
                              ),
                            );
                          }),
                        ),
                      );
                    }),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        // X-axis labels
        Row(
          children: [
            const SizedBox(width: 50), // Offset for Y-axis labels
            Expanded(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: List.generate(_gridCols ~/ 4, (index) {
                  final col = index * 4;
                  return Text(
                    _getXAxisLabel(col),
                    style: Theme.of(context).textTheme.bodySmall,
                    textAlign: TextAlign.center,
                  );
                }),
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds color scale legend
  Widget _buildColorScale() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Humidity Scale (${_getUnitLabel(_currentViewMode)})',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            // Color gradient bar
            Expanded(
              child: Container(
                height: 20,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: _humidityGradient,
                    stops: const [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                  ),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: Theme.of(context).dividerColor),
                ),
              ),
            ),
            const SizedBox(width: 8),
            // Scale labels
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('High', style: Theme.of(context).textTheme.bodySmall),
                Text('Low', style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ],
        ),
        const SizedBox(height: 4),
        // Threshold indicators
        if (widget.showSurvivalThresholds)
          Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: _getHumidityColor(_survivalThreshold),
                  border: Border.all(color: Colors.black, width: 2),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                'Survival Threshold',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(width: 16),
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: _getHumidityColor(_optimalMinHumidity),
                  border: Border.all(color: Colors.green, width: 2),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                'Optimal Range',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
      ],
    );
  }

  /// Builds selected cell information panel
  Widget _buildSelectedCellInfo() {
    if (_selectedCell == null) return const SizedBox.shrink();

    final cell = _heatmapData[_selectedCell!.row][_selectedCell!.col];
    final riskLevel = _getMosquitoRiskLevel(cell.value);

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Selected Cell Analysis',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: () {
                  setState(() {
                    _selectedCell = null;
                  });
                },
                tooltip: 'Close',
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Position: ${_getYAxisLabel(_selectedCell!.row)} × ${_getXAxisLabel(_selectedCell!.col)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      'Humidity: ${cell.value.toStringAsFixed(1)}${_getUnitLabel(_currentViewMode)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      'Quality: ${(cell.quality * 100).toStringAsFixed(0)}%',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getRiskColor(riskLevel).withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  riskLevel,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: _getRiskColor(riskLevel),
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

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.water_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No humidity data available',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Humidity patterns will appear here when data is loaded',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Generates heatmap data matrix from humidity measurements
  void _generateHeatmapData() {
    _heatmapData = List.generate(_gridRows, (row) =>
        List.generate(_gridCols, (col) => HumidityCell(value: 0.0, quality: 0.0, count: 0)));

    List<HumidityMeasurement> measurements;

    switch (_currentViewMode) {
      case HumidityViewMode.relative:
        measurements = widget.humidityData.relativeHumidity;
        break;
      case HumidityViewMode.absolute:
        measurements = widget.humidityData.absoluteHumidity;
        break;
      case HumidityViewMode.dewPoint:
        measurements = widget.humidityData.dewPoint;
        break;
    }

    // Filter by date range if specified
    if (widget.dateRange != null) {
      measurements = measurements
          .where((m) => widget.dateRange!.contains(m.date))
          .toList();
    }

    // Aggregate measurements into grid cells
    for (final measurement in measurements) {
      final row = _getRowFromDate(measurement.date);
      final col = _getColFromDate(measurement.date);

      if (row >= 0 && row < _gridRows && col >= 0 && col < _gridCols) {
        final cell = _heatmapData[row][col];

        // Calculate weighted average
        final totalWeight = cell.count + 1;
        final newValue = (cell.value * cell.count + measurement.humidity) / totalWeight;
        final newQuality = (cell.quality * cell.count + measurement.quality) / totalWeight;

        _heatmapData[row][col] = HumidityCell(
          value: newValue,
          quality: newQuality,
          count: totalWeight,
        );
      }
    }

    // Apply smoothing for empty cells
    _applySpatialSmoothing();
  }

  /// Applies spatial smoothing to fill empty cells
  void _applySpatialSmoothing() {
    for (int row = 0; row < _gridRows; row++) {
      for (int col = 0; col < _gridCols; col++) {
        if (_heatmapData[row][col].count == 0) {
          final neighbors = _getNeighborCells(row, col);
          if (neighbors.isNotEmpty) {
            double totalValue = 0;
            double totalQuality = 0;
            int validNeighbors = 0;

            for (final neighbor in neighbors) {
              if (neighbor.count > 0) {
                totalValue += neighbor.value;
                totalQuality += neighbor.quality;
                validNeighbors++;
              }
            }

            if (validNeighbors > 0) {
              _heatmapData[row][col] = HumidityCell(
                value: totalValue / validNeighbors,
                quality: totalQuality / validNeighbors * 0.7, // Reduced quality for interpolated
                count: 1,
              );
            }
          }
        }
      }
    }
  }

  /// Gets neighbor cells for spatial smoothing
  List<HumidityCell> _getNeighborCells(int row, int col) {
    final neighbors = <HumidityCell>[];

    for (int dr = -1; dr <= 1; dr++) {
      for (int dc = -1; dc <= 1; dc++) {
        if (dr == 0 && dc == 0) continue; // Skip self

        final newRow = row + dr;
        final newCol = col + dc;

        if (newRow >= 0 && newRow < _gridRows && newCol >= 0 && newCol < _gridCols) {
          neighbors.add(_heatmapData[newRow][newCol]);
        }
      }
    }

    return neighbors;
  }

  /// Gets row index from date (month-based)
  int _getRowFromDate(DateTime date) {
    return date.month - 1; // 0-11 for months
  }

  /// Gets column index from date (hour-based or day-based)
  int _getColFromDate(DateTime date) {
    return date.hour; // 0-23 for hours
  }

  /// Gets humidity color based on value
  Color _getHumidityColor(double humidity) {
    double normalizedValue;

    switch (_currentViewMode) {
      case HumidityViewMode.relative:
        normalizedValue = math.min(humidity / 100.0, 1.0);
        break;
      case HumidityViewMode.absolute:
        normalizedValue = math.min(humidity / 30.0, 1.0); // Assuming max 30 g/m³
        break;
      case HumidityViewMode.dewPoint:
        // Normalize dew point (-20°C to 30°C)
        normalizedValue = math.max(0.0, math.min((humidity + 20) / 50.0, 1.0));
        break;
    }

    final index = (normalizedValue * (_humidityGradient.length - 1)).round();
    return _humidityGradient[math.min(index, _humidityGradient.length - 1)];
  }

  /// Gets mosquito risk level from humidity value
  String _getMosquitoRiskLevel(double humidity) {
    if (_currentViewMode != HumidityViewMode.relative) {
      return 'N/A'; // Risk assessment only for relative humidity
    }

    if (humidity < _survivalThreshold) return 'No Risk';
    if (humidity >= _optimalMinHumidity && humidity <= _optimalMaxHumidity) return 'High Risk';
    if (humidity >= _survivalThreshold) return 'Moderate Risk';
    return 'Low Risk';
  }

  /// Gets risk level color
  Color _getRiskColor(String riskLevel) {
    switch (riskLevel) {
      case 'No Risk':
        return Colors.grey;
      case 'Low Risk':
        return Colors.green;
      case 'Moderate Risk':
        return Colors.orange;
      case 'High Risk':
        return Colors.red;
      default:
        return Colors.blue;
    }
  }

  /// Gets Y-axis label (months)
  String _getYAxisLabel(int row) {
    final monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return monthNames[row % 12];
  }

  /// Gets X-axis label (hours)
  String _getXAxisLabel(int col) {
    return '${col.toString().padLeft(2, '0')}h';
  }

  /// Gets cell tooltip information
  String _getCellTooltip(HumidityCell cell, int row, int col) {
    final riskLevel = _getMosquitoRiskLevel(cell.value);
    return '${_getYAxisLabel(row)} × ${_getXAxisLabel(col)}\n'
           'Humidity: ${cell.value.toStringAsFixed(1)}${_getUnitLabel(_currentViewMode)}\n'
           'Quality: ${(cell.quality * 100).toStringAsFixed(0)}%\n'
           'Risk: $riskLevel';
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(HumidityViewMode mode) {
    switch (mode) {
      case HumidityViewMode.relative:
        return 'Relative';
      case HumidityViewMode.absolute:
        return 'Absolute';
      case HumidityViewMode.dewPoint:
        return 'Dew Point';
    }
  }

  /// Gets view mode description
  String _getViewModeDescription(HumidityViewMode mode) {
    switch (mode) {
      case HumidityViewMode.relative:
        return 'Relative humidity patterns by month and hour';
      case HumidityViewMode.absolute:
        return 'Absolute humidity patterns by month and hour';
      case HumidityViewMode.dewPoint:
        return 'Dew point temperature patterns by month and hour';
    }
  }

  /// Gets unit label for humidity view mode
  String _getUnitLabel(HumidityViewMode mode) {
    switch (mode) {
      case HumidityViewMode.relative:
        return '%';
      case HumidityViewMode.absolute:
        return ' g/m³';
      case HumidityViewMode.dewPoint:
        return '°C';
    }
  }

  /// Shows humidity analysis information dialog
  void _showHumidityInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Humidity Analysis Information'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Mosquito Survival Requirements:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Minimum: 60% relative humidity'),
              Text('• Optimal: 70-90% for peak survival'),
              Text('• Critical: <50% limits survival significantly'),
              SizedBox(height: 16),
              Text(
                'Humidity Types:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• Relative: Percentage of moisture in air'),
              Text('• Absolute: Actual water content (g/m³)'),
              Text('• Dew Point: Temperature when condensation occurs'),
              SizedBox(height: 16),
              Text(
                'Heatmap Reading:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('• X-axis: Hour of day (00-23h)'),
              Text('• Y-axis: Month of year (Jan-Dec)'),
              Text('• Color: Humidity intensity'),
              Text('• Tap cells for detailed information'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}

/// Humidity view mode enumeration
enum HumidityViewMode {
  relative,
  absolute,
  dewPoint,
}

/// Humidity cell data structure for heatmap
class HumidityCell {
  final double value;
  final double quality;
  final int count;

  const HumidityCell({
    required this.value,
    required this.quality,
    required this.count,
  });
}

/// Grid cell position
class GridCell {
  final int row;
  final int col;

  const GridCell({
    required this.row,
    required this.col,
  });

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is GridCell && other.row == row && other.col == col;
  }

  @override
  int get hashCode => row.hashCode ^ col.hashCode;
}