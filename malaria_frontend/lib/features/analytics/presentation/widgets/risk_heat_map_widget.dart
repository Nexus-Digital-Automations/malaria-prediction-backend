/// Risk heat map widget for geographic visualization of malaria risk patterns
///
/// This widget displays comprehensive risk heat maps using geographic coordinates
/// and risk trend data to visualize spatial malaria risk patterns with clear
/// risk communication for public health decision-making.
///
/// Usage:
/// ```dart
/// RiskHeatMapWidget(
///   riskTrends: riskTrends,
///   height: 400,
///   enableInteractivity: true,
/// );
/// ```
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'dart:math' as math;
import '../../domain/entities/analytics_data.dart';

/// Geographic risk heat map widget with interactive features
class RiskHeatMapWidget extends StatefulWidget {
  /// Risk trend data to display
  final List<RiskTrend> riskTrends;

  /// Widget height
  final double height;

  /// Date range for filtering data
  final DateRange? dateRange;

  /// Whether to enable interactive features
  final bool enableInteractivity;

  /// Whether to show detailed tooltips
  final bool showDetailedTooltips;

  /// Grid resolution for heat map
  final int gridResolution;

  /// Whether to show population density overlay
  final bool showPopulationOverlay;

  /// Constructor requiring risk trends data
  const RiskHeatMapWidget({
    super.key,
    required this.riskTrends,
    this.height = 350,
    this.dateRange,
    this.enableInteractivity = true,
    this.showDetailedTooltips = false,
    this.gridResolution = 20,
    this.showPopulationOverlay = true,
  });

  @override
  State<RiskHeatMapWidget> createState() => _RiskHeatMapWidgetState();
}

class _RiskHeatMapWidgetState extends State<RiskHeatMapWidget> {
  /// Risk color mapping for visualization
  final Map<RiskLevel, Color> _riskColors = {
    RiskLevel.low: Colors.green.shade400,
    RiskLevel.medium: Colors.yellow.shade600,
    RiskLevel.high: Colors.orange.shade600,
    RiskLevel.critical: Colors.red.shade600,
  };

  /// Heat map grid data
  late List<List<HeatMapCell>> _heatMapGrid;

  /// Geographic bounds for the risk data
  late GeographicBounds _bounds;

  /// Selected cell for detailed view
  HeatMapCell? _selectedCell;

  /// Current view mode
  HeatMapViewMode _viewMode = HeatMapViewMode.riskLevel;

  /// Zoom level for geographic detail
  double _zoomLevel = 1.0;

  /// Offset for panning
  Offset _panOffset = Offset.zero;

  @override
  void initState() {
    super.initState();
    _calculateGeographicBounds();
    _generateHeatMapGrid();
  }

  @override
  void didUpdateWidget(RiskHeatMapWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.riskTrends != widget.riskTrends ||
        oldWidget.dateRange != widget.dateRange) {
      _calculateGeographicBounds();
      _generateHeatMapGrid();
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
            _buildControls(),
            const SizedBox(height: 12),
            Expanded(child: _buildHeatMap()),
            const SizedBox(height: 8),
            _buildLegend(),
            if (_selectedCell != null) _buildSelectedCellInfo(),
          ],
        ),
      ),
    );
  }

  /// Builds the heat map header with title and statistics
  Widget _buildHeader() {
    final highRiskCount = _getFilteredRiskTrends()
        .where((r) => r.riskLevel == RiskLevel.high || r.riskLevel == RiskLevel.critical)
        .length;
    final totalAreas = _getFilteredRiskTrends().length;

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Risk Heat Map',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '$highRiskCount high-risk areas out of $totalAreas total',
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
                Icons.zoom_in,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: widget.enableInteractivity ? () {
                setState(() {
                  _zoomLevel = math.min(_zoomLevel * 1.2, 3.0);
                });
              } : null,
              tooltip: 'Zoom In',
            ),
            IconButton(
              icon: Icon(
                Icons.zoom_out,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: widget.enableInteractivity ? () {
                setState(() {
                  _zoomLevel = math.max(_zoomLevel / 1.2, 0.5);
                });
              } : null,
              tooltip: 'Zoom Out',
            ),
            IconButton(
              icon: Icon(
                Icons.center_focus_strong,
                color: Theme.of(context).colorScheme.primary,
              ),
              onPressed: widget.enableInteractivity ? () {
                setState(() {
                  _zoomLevel = 1.0;
                  _panOffset = Offset.zero;
                });
              } : null,
              tooltip: 'Reset View',
            ),
          ],
        ),
      ],
    );
  }

  /// Builds control panel for heat map options
  Widget _buildControls() {
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
              children: HeatMapViewMode.values.map((mode) {
                final isSelected = mode == _viewMode;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(_getViewModeDisplayName(mode)),
                    selected: isSelected,
                    onSelected: (selected) {
                      if (selected) {
                        setState(() {
                          _viewMode = mode;
                          _generateHeatMapGrid();
                        });
                      }
                    },
                  ),
                );
              }).toList(),
            ),
          ),
        ),
        if (widget.showPopulationOverlay)
          Row(
            children: [
              const SizedBox(width: 16),
              Text(
                'Population:',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              Switch(
                value: widget.showPopulationOverlay,
                onChanged: null, // Read-only for now
              ),
            ],
          ),
      ],
    );
  }

  /// Builds the main heat map visualization
  Widget _buildHeatMap() {
    if (_heatMapGrid.isEmpty) {
      return _buildNoDataMessage();
    }

    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: widget.enableInteractivity
          ? GestureDetector(
              onPanUpdate: (details) {
                setState(() {
                  _panOffset += details.delta / _zoomLevel;
                });
              },
              onTapUp: (details) => _handleTap(details.localPosition),
              child: _buildHeatMapGrid(),
            )
          : _buildHeatMapGrid(),
    );
  }

  /// Builds the heat map grid
  Widget _buildHeatMapGrid() {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).dividerColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final cellWidth = constraints.maxWidth / widget.gridResolution;
          final cellHeight = constraints.maxHeight / widget.gridResolution;

          return Transform.scale(
            scale: _zoomLevel,
            child: Transform.translate(
              offset: _panOffset,
              child: Column(
                children: List.generate(widget.gridResolution, (row) {
                  return Expanded(
                    child: Row(
                      children: List.generate(widget.gridResolution, (col) {
                        final cell = _heatMapGrid[row][col];
                        return Expanded(
                          child: GestureDetector(
                            onTap: widget.enableInteractivity ? () {
                              setState(() {
                                _selectedCell = cell;
                              });
                            } : null,
                            child: Container(
                              decoration: BoxDecoration(
                                color: _getCellColor(cell),
                                border: Border.all(
                                  color: _selectedCell == cell
                                      ? Theme.of(context).colorScheme.primary
                                      : Colors.grey.shade300,
                                  width: _selectedCell == cell ? 2 : 0.5,
                                ),
                              ),
                              child: widget.enableInteractivity && widget.showDetailedTooltips
                                  ? Tooltip(
                                      message: _getCellTooltip(cell),
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
          );
        },
      ),
    );
  }

  /// Builds color legend for risk levels
  Widget _buildLegend() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Risk Level Scale',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: _riskColors.entries.map((entry) {
                  return Column(
                    children: [
                      Container(
                        width: 20,
                        height: 20,
                        decoration: BoxDecoration(
                          color: entry.value,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: Colors.grey.shade300),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _getRiskLevelDisplayName(entry.key),
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  );
                }).toList(),
              ),
            ),
            if (_viewMode == HeatMapViewMode.populationDensity)
              Row(
                children: [
                  const SizedBox(width: 16),
                  Container(
                    width: 100,
                    height: 20,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [Colors.blue.shade100, Colors.blue.shade800],
                      ),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'Population\nDensity',
                    style: Theme.of(context).textTheme.bodySmall,
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
          ],
        ),
      ],
    );
  }

  /// Builds selected cell information panel
  Widget _buildSelectedCellInfo() {
    if (_selectedCell == null) return const SizedBox.shrink();

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
                  'Area Analysis',
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
          _buildCellDetails(_selectedCell!),
        ],
      ),
    );
  }

  /// Builds detailed information for selected cell
  Widget _buildCellDetails(HeatMapCell cell) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Location: ${cell.coordinates.latitude.toStringAsFixed(3)}, ${cell.coordinates.longitude.toStringAsFixed(3)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  Text(
                    'Risk Score: ${cell.riskScore.toStringAsFixed(2)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  Text(
                    'Population: ${cell.populationAtRisk}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  Text(
                    'Confidence: ${(cell.confidence * 100).toStringAsFixed(0)}%',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: _riskColors[cell.riskLevel]?.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                _getRiskLevelDisplayName(cell.riskLevel),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: _riskColors[cell.riskLevel],
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds no data message
  Widget _buildNoDataMessage() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.map_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No risk data available for heat map',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  /// Calculates geographic bounds from risk trends
  void _calculateGeographicBounds() {
    if (widget.riskTrends.isEmpty) {
      _bounds = GeographicBounds(
        minLat: -1.0,
        maxLat: 1.0,
        minLng: -1.0,
        maxLng: 1.0,
      );
      return;
    }

    double minLat = double.infinity;
    double maxLat = double.negativeInfinity;
    double minLng = double.infinity;
    double maxLng = double.negativeInfinity;

    for (final trend in _getFilteredRiskTrends()) {
      minLat = math.min(minLat, trend.coordinates.latitude);
      maxLat = math.max(maxLat, trend.coordinates.latitude);
      minLng = math.min(minLng, trend.coordinates.longitude);
      maxLng = math.max(maxLng, trend.coordinates.longitude);
    }

    // Add padding
    final latPadding = (maxLat - minLat) * 0.1;
    final lngPadding = (maxLng - minLng) * 0.1;

    _bounds = GeographicBounds(
      minLat: minLat - latPadding,
      maxLat: maxLat + latPadding,
      minLng: minLng - lngPadding,
      maxLng: maxLng + lngPadding,
    );
  }

  /// Generates heat map grid from risk trend data
  void _generateHeatMapGrid() {
    _heatMapGrid = List.generate(
      widget.gridResolution,
      (row) => List.generate(
        widget.gridResolution,
        (col) => HeatMapCell(
          coordinates: _getCellCoordinates(row, col),
          riskScore: 0.0,
          riskLevel: RiskLevel.low,
          populationAtRisk: 0,
          confidence: 0.0,
          dataPoints: 0,
        ),
      ),
    );

    final trends = _getFilteredRiskTrends();

    // Aggregate risk data into grid cells
    for (final trend in trends) {
      final gridPos = _getGridPosition(trend.coordinates);
      if (gridPos != null) {
        final cell = _heatMapGrid[gridPos.row][gridPos.col];

        // Calculate weighted average
        final totalPoints = cell.dataPoints + 1;
        final newRiskScore = (cell.riskScore * cell.dataPoints + trend.riskScore) / totalPoints;
        final newConfidence = (cell.confidence * cell.dataPoints + trend.confidence) / totalPoints;

        _heatMapGrid[gridPos.row][gridPos.col] = HeatMapCell(
          coordinates: cell.coordinates,
          riskScore: newRiskScore,
          riskLevel: _calculateRiskLevel(newRiskScore),
          populationAtRisk: cell.populationAtRisk + trend.populationAtRisk,
          confidence: newConfidence,
          dataPoints: totalPoints,
        );
      }
    }

    // Apply spatial interpolation for empty cells
    _applySpatialInterpolation();
  }

  /// Applies spatial interpolation to fill empty grid cells
  void _applySpatialInterpolation() {
    for (int row = 0; row < widget.gridResolution; row++) {
      for (int col = 0; col < widget.gridResolution; col++) {
        if (_heatMapGrid[row][col].dataPoints == 0) {
          final neighbors = _getNeighborCells(row, col);
          if (neighbors.isNotEmpty) {
            double totalRisk = 0;
            double totalConfidence = 0;
            int totalPopulation = 0;
            int validNeighbors = 0;

            for (final neighbor in neighbors) {
              if (neighbor.dataPoints > 0) {
                totalRisk += neighbor.riskScore;
                totalConfidence += neighbor.confidence;
                totalPopulation += neighbor.populationAtRisk;
                validNeighbors++;
              }
            }

            if (validNeighbors > 0) {
              final avgRisk = totalRisk / validNeighbors;
              _heatMapGrid[row][col] = HeatMapCell(
                coordinates: _heatMapGrid[row][col].coordinates,
                riskScore: avgRisk,
                riskLevel: _calculateRiskLevel(avgRisk),
                populationAtRisk: (totalPopulation / validNeighbors).round(),
                confidence: (totalConfidence / validNeighbors) * 0.7, // Reduced for interpolated
                dataPoints: 1,
              );
            }
          }
        }
      }
    }
  }

  /// Gets neighbor cells for interpolation
  List<HeatMapCell> _getNeighborCells(int row, int col) {
    final neighbors = <HeatMapCell>[];
    final radius = 2; // Check cells within radius

    for (int dr = -radius; dr <= radius; dr++) {
      for (int dc = -radius; dc <= radius; dc++) {
        if (dr == 0 && dc == 0) continue;

        final newRow = row + dr;
        final newCol = col + dc;

        if (newRow >= 0 && newRow < widget.gridResolution &&
            newCol >= 0 && newCol < widget.gridResolution) {
          neighbors.add(_heatMapGrid[newRow][newCol]);
        }
      }
    }

    return neighbors;
  }

  /// Gets coordinates for grid cell
  Coordinates _getCellCoordinates(int row, int col) {
    final lat = _bounds.minLat + (row / (widget.gridResolution - 1)) * (_bounds.maxLat - _bounds.minLat);
    final lng = _bounds.minLng + (col / (widget.gridResolution - 1)) * (_bounds.maxLng - _bounds.minLng);
    return Coordinates(latitude: lat, longitude: lng);
  }

  /// Gets grid position for coordinates
  GridPosition? _getGridPosition(Coordinates coords) {
    if (coords.latitude < _bounds.minLat || coords.latitude > _bounds.maxLat ||
        coords.longitude < _bounds.minLng || coords.longitude > _bounds.maxLng) {
      return null;
    }

    final row = ((coords.latitude - _bounds.minLat) / (_bounds.maxLat - _bounds.minLat) * (widget.gridResolution - 1)).round();
    final col = ((coords.longitude - _bounds.minLng) / (_bounds.maxLng - _bounds.minLng) * (widget.gridResolution - 1)).round();

    return GridPosition(
      row: math.max(0, math.min(row, widget.gridResolution - 1)),
      col: math.max(0, math.min(col, widget.gridResolution - 1)),
    );
  }

  /// Calculates risk level from risk score
  RiskLevel _calculateRiskLevel(double riskScore) {
    if (riskScore >= 0.8) return RiskLevel.critical;
    if (riskScore >= 0.6) return RiskLevel.high;
    if (riskScore >= 0.3) return RiskLevel.medium;
    return RiskLevel.low;
  }

  /// Gets cell color based on view mode
  Color _getCellColor(HeatMapCell cell) {
    switch (_viewMode) {
      case HeatMapViewMode.riskLevel:
        return _riskColors[cell.riskLevel] ?? Colors.grey;
      case HeatMapViewMode.riskScore:
        return _getRiskScoreColor(cell.riskScore);
      case HeatMapViewMode.populationDensity:
        return _getPopulationDensityColor(cell.populationAtRisk);
      case HeatMapViewMode.confidence:
        return _getConfidenceColor(cell.confidence);
    }
  }

  /// Gets color for risk score visualization
  Color _getRiskScoreColor(double score) {
    final intensity = math.min(score, 1.0);
    return Color.lerp(Colors.green.shade200, Colors.red.shade800, intensity) ?? Colors.grey;
  }

  /// Gets color for population density visualization
  Color _getPopulationDensityColor(int population) {
    final maxPopulation = _heatMapGrid.expand((row) => row).map((cell) => cell.populationAtRisk).reduce(math.max);
    if (maxPopulation == 0) return Colors.blue.shade100;

    final intensity = population / maxPopulation;
    return Color.lerp(Colors.blue.shade100, Colors.blue.shade800, intensity) ?? Colors.blue;
  }

  /// Gets color for confidence visualization
  Color _getConfidenceColor(double confidence) {
    return Color.lerp(Colors.grey.shade300, Colors.blue.shade600, confidence) ?? Colors.grey;
  }

  /// Gets tooltip text for cell
  String _getCellTooltip(HeatMapCell cell) {
    return 'Location: ${cell.coordinates.latitude.toStringAsFixed(3)}, ${cell.coordinates.longitude.toStringAsFixed(3)}\n'
           'Risk: ${_getRiskLevelDisplayName(cell.riskLevel)}\n'
           'Score: ${cell.riskScore.toStringAsFixed(2)}\n'
           'Population: ${cell.populationAtRisk}\n'
           'Confidence: ${(cell.confidence * 100).toStringAsFixed(0)}%';
  }

  /// Handles tap events on heat map
  void _handleTap(Offset position) {
    // Calculate which cell was tapped based on position
    // This is a simplified implementation
    final row = (position.dy / widget.height * widget.gridResolution).floor();
    final col = (position.dx / widget.height * widget.gridResolution).floor();

    if (row >= 0 && row < widget.gridResolution && col >= 0 && col < widget.gridResolution) {
      setState(() {
        _selectedCell = _heatMapGrid[row][col];
      });
    }
  }

  /// Gets filtered risk trends based on date range
  List<RiskTrend> _getFilteredRiskTrends() {
    if (widget.dateRange == null) return widget.riskTrends;
    return widget.riskTrends.where((trend) => widget.dateRange!.contains(trend.date)).toList();
  }

  /// Gets risk level display name
  String _getRiskLevelDisplayName(RiskLevel level) {
    switch (level) {
      case RiskLevel.low:
        return 'Low';
      case RiskLevel.medium:
        return 'Medium';
      case RiskLevel.high:
        return 'High';
      case RiskLevel.critical:
        return 'Critical';
    }
  }

  /// Gets view mode display name
  String _getViewModeDisplayName(HeatMapViewMode mode) {
    switch (mode) {
      case HeatMapViewMode.riskLevel:
        return 'Risk Level';
      case HeatMapViewMode.riskScore:
        return 'Risk Score';
      case HeatMapViewMode.populationDensity:
        return 'Population';
      case HeatMapViewMode.confidence:
        return 'Confidence';
    }
  }
}

/// Heat map view mode enumeration
enum HeatMapViewMode {
  riskLevel,
  riskScore,
  populationDensity,
  confidence,
}

/// Heat map cell data structure
class HeatMapCell {
  final Coordinates coordinates;
  final double riskScore;
  final RiskLevel riskLevel;
  final int populationAtRisk;
  final double confidence;
  final int dataPoints;

  const HeatMapCell({
    required this.coordinates,
    required this.riskScore,
    required this.riskLevel,
    required this.populationAtRisk,
    required this.confidence,
    required this.dataPoints,
  });

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is HeatMapCell &&
        other.coordinates == coordinates &&
        other.riskScore == riskScore &&
        other.riskLevel == riskLevel;
  }

  @override
  int get hashCode => coordinates.hashCode ^ riskScore.hashCode ^ riskLevel.hashCode;
}

/// Geographic bounds data structure
class GeographicBounds {
  final double minLat;
  final double maxLat;
  final double minLng;
  final double maxLng;

  const GeographicBounds({
    required this.minLat,
    required this.maxLat,
    required this.minLng,
    required this.maxLng,
  });
}

/// Grid position data structure
class GridPosition {
  final int row;
  final int col;

  const GridPosition({
    required this.row,
    required this.col,
  });
}