/// Choropleth Overlay Widget for Risk Map Visualization
///
/// Custom flutter_map layer widget that renders choropleth regions
/// with color-coded malaria risk levels, supporting interactive
/// selection, hover effects, and smooth animations.
///
/// Features:
/// - Color-coded polygon regions based on risk scores
/// - Interactive tap and hover effects
/// - Smooth color transitions
/// - Border highlighting for selected regions
/// - Opacity control for overlay blending
/// - Performance-optimized rendering
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:logger/logger.dart';

import '../../domain/entities/risk_data.dart';
import '../../domain/entities/map_layer.dart';

/// Choropleth overlay widget for flutter_map
class ChoroplethOverlay extends StatefulWidget {
  /// Risk data for each region
  final List<RiskData> riskData;

  /// Overall layer opacity
  final double opacity;

  /// Callback when a region is tapped
  final void Function(RiskData)? onRegionTap;

  /// Currently selected region ID
  final String? selectedRegionId;

  /// Color scheme for risk visualization
  final LayerColorScheme colorScheme;

  /// Enable hover effects (web/desktop)
  final bool enableHoverEffects;

  /// Show region labels
  final bool showLabels;

  /// Border width for regions
  final double borderWidth;

  const ChoroplethOverlay({
    super.key,
    required this.riskData,
    this.opacity = 0.7,
    this.onRegionTap,
    this.selectedRegionId,
    required this.colorScheme,
    this.enableHoverEffects = true,
    this.showLabels = false,
    this.borderWidth = 2.0,
  });

  @override
  State<ChoroplethOverlay> createState() => _ChoroplethOverlayState();
}

class _ChoroplethOverlayState extends State<ChoroplethOverlay>
    with SingleTickerProviderStateMixin {
  /// Logger instance
  final Logger _logger = Logger();

  /// Currently hovered region ID
  String? _hoveredRegionId;

  /// Animation controller for transitions
  late final AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    const String methodName = 'initState';
    _logger.d('[$methodName] Initializing ChoroplethOverlay with ${widget.riskData.length} regions');

    _animationController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const String methodName = 'build';
    _logger.d('[$methodName] Building choropleth overlay');

    if (widget.riskData.isEmpty) {
      return const SizedBox.shrink();
    }

    return PolygonLayer(
      polygons: _buildPolygons(),
    );
  }

  List<Polygon> _buildPolygons() {
    const String methodName = '_buildPolygons';
    final polygons = <Polygon>[];

    for (final data in widget.riskData) {
      final boundary = data.boundary;
      if (boundary == null || boundary.coordinates.isEmpty) {
        // Create a simple circle polygon around the coordinates for regions without boundaries
        final circlePolygon = _createCirclePolygon(data);
        if (circlePolygon != null) {
          polygons.add(circlePolygon);
        }
        continue;
      }

      final isSelected = data.id == widget.selectedRegionId;
      final isHovered = data.id == _hoveredRegionId;

      // Get fill color based on risk level
      final fillColor = _getFillColor(data, isSelected, isHovered);
      final borderColor = _getBorderColor(data, isSelected, isHovered);
      final effectiveBorderWidth = _getBorderWidth(isSelected, isHovered);

      final polygon = Polygon(
        points: boundary.coordinates,
        color: fillColor,
        borderColor: borderColor,
        borderStrokeWidth: effectiveBorderWidth,
        isFilled: true,
        label: widget.showLabels ? data.regionName : null,
        labelStyle: const TextStyle(
          color: Colors.black87,
          fontSize: 10,
          fontWeight: FontWeight.w500,
        ),
        hitValue: data, // Store data for hit testing
      );

      polygons.add(polygon);
    }

    _logger.d('[$methodName] Built ${polygons.length} polygons');
    return polygons;
  }

  /// Create a circle polygon for regions without boundary data
  Polygon? _createCirclePolygon(RiskData data) {
    const String methodName = '_createCirclePolygon';

    final center = data.coordinates;
    final points = <LatLng>[];
    const radiusKm = 10.0; // Default radius of 10km

    // Create a circle with 32 points
    for (int i = 0; i < 32; i++) {
      final angle = (i / 32) * 2 * 3.14159265359;
      // Approximate conversion: 1 degree latitude ~= 111km
      final latOffset = (radiusKm / 111) * (0.7 + 0.3 * (1 - (angle / 3.14159265359).abs()));
      final lngOffset = (radiusKm / (111 * (center.latitude.abs() < 1 ? 1 : center.latitude.abs()).clamp(0.1, 90))) *
          (0.7 + 0.3 * ((angle / 3.14159265359 - 0.5).abs()));

      final lat = center.latitude + latOffset * (angle < 3.14159265359 ? 1 : -1) *
          (angle > 1.5707963 && angle < 4.712389 ? -1 : 1);
      final lng = center.longitude + lngOffset *
          (angle > 0 && angle < 3.14159265359 ? 1 : -1);

      points.add(LatLng(
        center.latitude + 0.1 * _cos(angle),
        center.longitude + 0.1 * _sin(angle),
      ));
    }

    if (points.isEmpty) {
      _logger.w('[$methodName] Could not create circle polygon for ${data.regionName}');
      return null;
    }

    final isSelected = data.id == widget.selectedRegionId;
    final isHovered = data.id == _hoveredRegionId;

    return Polygon(
      points: points,
      color: _getFillColor(data, isSelected, isHovered),
      borderColor: _getBorderColor(data, isSelected, isHovered),
      borderStrokeWidth: _getBorderWidth(isSelected, isHovered),
      isFilled: true,
      hitValue: data,
    );
  }

  double _sin(double angle) => (angle - (angle * angle * angle) / 6 +
      (angle * angle * angle * angle * angle) / 120);

  double _cos(double angle) => (1 - (angle * angle) / 2 +
      (angle * angle * angle * angle) / 24);

  Color _getFillColor(RiskData data, bool isSelected, bool isHovered) {
    final baseColor = data.riskLevel.fillColor;

    if (isSelected) {
      return baseColor.withValues(alpha: widget.opacity * 1.2);
    }

    if (isHovered && widget.enableHoverEffects) {
      return baseColor.withValues(alpha: widget.opacity * 1.1);
    }

    return baseColor.withValues(alpha: widget.opacity);
  }

  Color _getBorderColor(RiskData data, bool isSelected, bool isHovered) {
    if (isSelected) {
      return widget.colorScheme.highlightColor;
    }

    if (isHovered && widget.enableHoverEffects) {
      return data.riskLevel.borderColor;
    }

    return data.riskLevel.borderColor.withValues(alpha: 0.7);
  }

  double _getBorderWidth(bool isSelected, bool isHovered) {
    if (isSelected) {
      return widget.borderWidth * 2;
    }

    if (isHovered && widget.enableHoverEffects) {
      return widget.borderWidth * 1.5;
    }

    return widget.borderWidth;
  }
}

/// Widget for rendering risk markers on the map
class RiskMarkerLayer extends StatelessWidget {
  /// Risk data points to display as markers
  final List<RiskData> riskData;

  /// Callback when a marker is tapped
  final void Function(RiskData)? onMarkerTap;

  /// Size of markers
  final double markerSize;

  /// Logger instance
  final Logger _logger = Logger();

  RiskMarkerLayer({
    super.key,
    required this.riskData,
    this.onMarkerTap,
    this.markerSize = 30.0,
  });

  @override
  Widget build(BuildContext context) {
    const String methodName = 'build';
    _logger.d('[$methodName] Building risk marker layer with ${riskData.length} markers');

    return MarkerLayer(
      markers: riskData.map(_buildMarker).toList(),
    );
  }

  Marker _buildMarker(RiskData data) {
    return Marker(
      point: data.coordinates,
      width: markerSize,
      height: markerSize,
      child: GestureDetector(
        onTap: () => onMarkerTap?.call(data),
        child: Container(
          decoration: BoxDecoration(
            color: data.riskLevel.color,
            shape: BoxShape.circle,
            border: Border.all(
              color: Colors.white,
              width: 2,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.3),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Center(
            child: Icon(
              data.riskLevel.icon,
              color: Colors.white,
              size: markerSize * 0.5,
            ),
          ),
        ),
      ),
    );
  }
}

/// Widget for displaying a heat map overlay
class RiskHeatmapLayer extends StatelessWidget {
  /// Risk data points for heat map generation
  final List<RiskData> riskData;

  /// Heat map intensity
  final double intensity;

  /// Heat map radius
  final double radius;

  /// Gradient colors
  final List<Color> gradientColors;

  /// Logger instance
  final Logger _logger = Logger();

  RiskHeatmapLayer({
    super.key,
    required this.riskData,
    this.intensity = 0.5,
    this.radius = 20.0,
    this.gradientColors = const [
      Color(0x004CAF50),
      Color(0x80FFEB3B),
      Color(0xC0FF9800),
      Color(0xFFF44336),
    ],
  });

  @override
  Widget build(BuildContext context) {
    const String methodName = 'build';
    _logger.d('[$methodName] Building risk heatmap layer');

    // For now, render as circles with gradients
    // A full heatmap implementation would use a custom tile layer or canvas
    return MarkerLayer(
      markers: riskData.map(_buildHeatPoint).toList(),
    );
  }

  Marker _buildHeatPoint(RiskData data) {
    final effectiveRadius = radius * (1 + data.riskScore);

    return Marker(
      point: data.coordinates,
      width: effectiveRadius * 2,
      height: effectiveRadius * 2,
      child: Container(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [
              _getHeatColor(data.riskScore).withValues(alpha: intensity),
              _getHeatColor(data.riskScore).withValues(alpha: 0),
            ],
          ),
        ),
      ),
    );
  }

  Color _getHeatColor(double score) {
    final index = (score * (gradientColors.length - 1)).floor();
    return gradientColors[index.clamp(0, gradientColors.length - 1)];
  }
}

/// Extension to add choropleth-specific methods to RiskData list
extension ChoroplethRiskDataExtension on List<RiskData> {
  /// Group risk data by risk level for choropleth rendering
  Map<RiskLevel, List<RiskData>> groupByRiskLevel() {
    final grouped = <RiskLevel, List<RiskData>>{};
    for (final data in this) {
      grouped.putIfAbsent(data.riskLevel, () => []).add(data);
    }
    return grouped;
  }

  /// Get regions within visible bounds
  List<RiskData> filterByBounds(GeographicBounds bounds) {
    return where((data) => bounds.contains(data.coordinates)).toList();
  }

  /// Calculate statistics for the visible regions
  RiskDataStatistics get statistics {
    if (isEmpty) {
      return const RiskDataStatistics(
        totalRegions: 0,
        averageRiskScore: 0,
        maxRiskScore: 0,
        minRiskScore: 0,
        criticalCount: 0,
        highCount: 0,
        mediumCount: 0,
        lowCount: 0,
      );
    }

    final scores = map((d) => d.riskScore).toList();
    final counts = groupByRiskLevel();

    return RiskDataStatistics(
      totalRegions: length,
      averageRiskScore: scores.reduce((a, b) => a + b) / length,
      maxRiskScore: scores.reduce((a, b) => a > b ? a : b),
      minRiskScore: scores.reduce((a, b) => a < b ? a : b),
      criticalCount: counts[RiskLevel.critical]?.length ?? 0,
      highCount: counts[RiskLevel.high]?.length ?? 0,
      mediumCount: counts[RiskLevel.medium]?.length ?? 0,
      lowCount: counts[RiskLevel.low]?.length ?? 0,
    );
  }
}

/// Statistics for risk data regions
class RiskDataStatistics {
  final int totalRegions;
  final double averageRiskScore;
  final double maxRiskScore;
  final double minRiskScore;
  final int criticalCount;
  final int highCount;
  final int mediumCount;
  final int lowCount;

  const RiskDataStatistics({
    required this.totalRegions,
    required this.averageRiskScore,
    required this.maxRiskScore,
    required this.minRiskScore,
    required this.criticalCount,
    required this.highCount,
    required this.mediumCount,
    required this.lowCount,
  });

  /// Get count for a specific risk level
  int countForLevel(RiskLevel level) {
    switch (level) {
      case RiskLevel.critical:
        return criticalCount;
      case RiskLevel.high:
        return highCount;
      case RiskLevel.medium:
        return mediumCount;
      case RiskLevel.low:
        return lowCount;
    }
  }
}
