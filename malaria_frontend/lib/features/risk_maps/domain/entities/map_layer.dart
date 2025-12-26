/// Map Layer Entity for Multi-Layer Map Visualization
///
/// Core entity representing configurable map layers for the risk
/// visualization system, supporting various layer types including
/// choropleth, heatmap, markers, and environmental overlays.
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';

/// Types of map layers supported
enum LayerType {
  /// Choropleth layer with colored regions
  choropleth,

  /// Point markers on the map
  markers,

  /// Heat map visualization
  heatmap,

  /// Line features (roads, rivers, etc.)
  lines,

  /// Polygon features
  polygons,

  /// Raster tile layer
  raster,

  /// Vector tile layer
  vector,

  /// Real-time data layer
  realtime,

  /// User-generated content layer
  userGenerated,

  /// Annotation layer
  annotations;

  /// Get display name for this layer type
  String get displayName {
    switch (this) {
      case LayerType.choropleth:
        return 'Choropleth';
      case LayerType.markers:
        return 'Markers';
      case LayerType.heatmap:
        return 'Heatmap';
      case LayerType.lines:
        return 'Lines';
      case LayerType.polygons:
        return 'Polygons';
      case LayerType.raster:
        return 'Raster';
      case LayerType.vector:
        return 'Vector';
      case LayerType.realtime:
        return 'Real-time';
      case LayerType.userGenerated:
        return 'User Generated';
      case LayerType.annotations:
        return 'Annotations';
    }
  }

  /// Get default icon for this layer type
  IconData get icon {
    switch (this) {
      case LayerType.choropleth:
        return Icons.palette;
      case LayerType.markers:
        return Icons.place;
      case LayerType.heatmap:
        return Icons.grain;
      case LayerType.lines:
        return Icons.timeline;
      case LayerType.polygons:
        return Icons.crop_free;
      case LayerType.raster:
        return Icons.image;
      case LayerType.vector:
        return Icons.polyline;
      case LayerType.realtime:
        return Icons.live_tv;
      case LayerType.userGenerated:
        return Icons.edit;
      case LayerType.annotations:
        return Icons.label;
    }
  }
}

/// Data source types for map layers
enum DataSourceType {
  /// API endpoint data source
  api,

  /// Local file data source
  file,

  /// Real-time WebSocket data
  websocket,

  /// Tile server
  tileServer,

  /// GeoJSON data
  geojson,

  /// Vector tiles
  vectorTiles,

  /// Static data embedded in app
  staticData,
}

/// Position options for legends
enum LegendPosition {
  topLeft,
  topRight,
  bottomLeft,
  bottomRight,
  topCenter,
  bottomCenter,
}

/// Color scheme configuration for layers
class LayerColorScheme extends Equatable {
  /// Primary color for the layer
  final Color primaryColor;

  /// Secondary color for contrast
  final Color secondaryColor;

  /// Color gradient for value-based coloring
  final List<Color> gradient;

  /// Number of color steps
  final int steps;

  /// Color for missing/null data
  final Color noDataColor;

  /// Border color for features
  final Color borderColor;

  /// Highlight color for selected features
  final Color highlightColor;

  const LayerColorScheme({
    required this.primaryColor,
    required this.secondaryColor,
    required this.gradient,
    required this.steps,
    required this.noDataColor,
    required this.borderColor,
    required this.highlightColor,
  });

  @override
  List<Object?> get props => [
        primaryColor,
        secondaryColor,
        gradient,
        steps,
        noDataColor,
        borderColor,
        highlightColor,
      ];

  /// Create default risk color scheme
  factory LayerColorScheme.riskDefault() {
    return const LayerColorScheme(
      primaryColor: Color(0xFF4CAF50),
      secondaryColor: Color(0xFFF44336),
      gradient: [
        Color(0xFF4CAF50), // Green - Low
        Color(0xFFCDDC39), // Light green
        Color(0xFFFFEB3B), // Yellow
        Color(0xFFFF9800), // Orange
        Color(0xFFF44336), // Red - High
        Color(0xFF9C27B0), // Purple - Critical
      ],
      steps: 6,
      noDataColor: Color(0xFFBDBDBD),
      borderColor: Color(0xFF757575),
      highlightColor: Color(0xFF2196F3),
    );
  }

  /// Get color for a normalized value (0.0 to 1.0)
  Color getColorForValue(double value) {
    if (value.isNaN || value < 0) return noDataColor;

    final clampedValue = value.clamp(0.0, 1.0);
    final index = (clampedValue * (gradient.length - 1)).floor();
    final nextIndex = (index + 1).clamp(0, gradient.length - 1);
    final t = (clampedValue * (gradient.length - 1)) - index;

    return Color.lerp(gradient[index], gradient[nextIndex], t) ?? gradient[index];
  }
}

/// Data configuration for layer data sources
class LayerDataConfig extends Equatable {
  /// URL for data retrieval
  final String dataUrl;

  /// Type of data source
  final DataSourceType sourceType;

  /// Refresh interval in seconds
  final int? refreshInterval;

  /// Enable caching
  final bool enableCaching;

  /// Cache duration in seconds
  final int cacheDuration;

  /// Data format (geojson, csv, etc.)
  final String dataFormat;

  /// Field mappings for data interpretation
  final Map<String, String> fieldMappings;

  /// Filter expressions
  final List<String> filters;

  /// Aggregation settings
  final Map<String, String> aggregations;

  const LayerDataConfig({
    required this.dataUrl,
    required this.sourceType,
    this.refreshInterval,
    required this.enableCaching,
    required this.cacheDuration,
    required this.dataFormat,
    required this.fieldMappings,
    required this.filters,
    required this.aggregations,
  });

  @override
  List<Object?> get props => [
        dataUrl,
        sourceType,
        refreshInterval,
        enableCaching,
        cacheDuration,
        dataFormat,
        fieldMappings,
        filters,
        aggregations,
      ];
}

/// Style configuration for layer rendering
class LayerStyleConfig extends Equatable {
  /// Stroke width for lines and borders
  final double strokeWidth;

  /// Fill color for polygons
  final Color? fillColor;

  /// Stroke color for lines and borders
  final Color? strokeColor;

  /// Dash pattern for lines
  final List<double>? dashPattern;

  /// Marker size for point features
  final double markerSize;

  /// Font size for labels
  final double fontSize;

  /// Font weight for labels
  final FontWeight fontWeight;

  /// Text color for labels
  final Color textColor;

  const LayerStyleConfig({
    required this.strokeWidth,
    this.fillColor,
    this.strokeColor,
    this.dashPattern,
    required this.markerSize,
    required this.fontSize,
    required this.fontWeight,
    required this.textColor,
  });

  @override
  List<Object?> get props => [
        strokeWidth,
        fillColor,
        strokeColor,
        dashPattern,
        markerSize,
        fontSize,
        fontWeight,
        textColor,
      ];

  /// Create default style
  factory LayerStyleConfig.defaultStyle() {
    return const LayerStyleConfig(
      strokeWidth: 2.0,
      fillColor: null,
      strokeColor: null,
      dashPattern: null,
      markerSize: 8.0,
      fontSize: 12.0,
      fontWeight: FontWeight.normal,
      textColor: Colors.black87,
    );
  }
}

/// Legend item for layer legend
class LegendItem extends Equatable {
  /// Color for this legend item
  final Color color;

  /// Label text
  final String label;

  /// Numeric value (if applicable)
  final String? value;

  /// Description text
  final String? description;

  const LegendItem({
    required this.color,
    required this.label,
    this.value,
    this.description,
  });

  @override
  List<Object?> get props => [color, label, value, description];
}

/// Legend configuration for layers
class LayerLegend extends Equatable {
  /// Whether legend is visible
  final bool isVisible;

  /// Legend title
  final String title;

  /// Legend items
  final List<LegendItem> items;

  /// Position on the map
  final LegendPosition position;

  /// Background color
  final Color backgroundColor;

  /// Text color
  final Color textColor;

  /// Border color
  final Color borderColor;

  const LayerLegend({
    required this.isVisible,
    required this.title,
    required this.items,
    required this.position,
    required this.backgroundColor,
    required this.textColor,
    required this.borderColor,
  });

  @override
  List<Object?> get props => [
        isVisible,
        title,
        items,
        position,
        backgroundColor,
        textColor,
        borderColor,
      ];

  /// Create default risk legend
  factory LayerLegend.riskDefault() {
    return LayerLegend(
      isVisible: true,
      title: 'Malaria Risk',
      items: const [
        LegendItem(color: Color(0xFF4CAF50), label: 'Low', value: '< 30%'),
        LegendItem(color: Color(0xFFFF9800), label: 'Medium', value: '30-60%'),
        LegendItem(color: Color(0xFFF44336), label: 'High', value: '60-80%'),
        LegendItem(color: Color(0xFF9C27B0), label: 'Critical', value: '> 80%'),
      ],
      position: LegendPosition.bottomRight,
      backgroundColor: Colors.white,
      textColor: Colors.black87,
      borderColor: Colors.grey,
    );
  }
}

/// Core map layer entity
class MapLayer extends Equatable {
  /// Unique identifier
  final String id;

  /// Display name
  final String name;

  /// Description
  final String description;

  /// Layer type
  final LayerType type;

  /// Visibility state
  final bool isVisible;

  /// Whether layer can be toggled
  final bool isToggleable;

  /// Opacity (0.0 to 1.0)
  final double opacity;

  /// Z-index for layer ordering
  final int zIndex;

  /// Color scheme configuration
  final LayerColorScheme colorScheme;

  /// Data configuration
  final LayerDataConfig? dataConfig;

  /// Style configuration
  final LayerStyleConfig styleConfig;

  /// Legend configuration
  final LayerLegend? legend;

  /// Whether layer requires authentication
  final bool requiresAuth;

  /// Minimum zoom level
  final double? minZoom;

  /// Maximum zoom level
  final double? maxZoom;

  /// Tags for categorization
  final List<String> tags;

  /// Additional metadata
  final Map<String, dynamic> metadata;

  const MapLayer({
    required this.id,
    required this.name,
    required this.description,
    required this.type,
    required this.isVisible,
    required this.isToggleable,
    required this.opacity,
    required this.zIndex,
    required this.colorScheme,
    this.dataConfig,
    required this.styleConfig,
    this.legend,
    required this.requiresAuth,
    this.minZoom,
    this.maxZoom,
    required this.tags,
    required this.metadata,
  });

  @override
  List<Object?> get props => [
        id,
        name,
        description,
        type,
        isVisible,
        isToggleable,
        opacity,
        zIndex,
        colorScheme,
        dataConfig,
        styleConfig,
        legend,
        requiresAuth,
        minZoom,
        maxZoom,
        tags,
        metadata,
      ];

  /// Create a copy with updated values
  MapLayer copyWith({
    String? id,
    String? name,
    String? description,
    LayerType? type,
    bool? isVisible,
    bool? isToggleable,
    double? opacity,
    int? zIndex,
    LayerColorScheme? colorScheme,
    LayerDataConfig? dataConfig,
    LayerStyleConfig? styleConfig,
    LayerLegend? legend,
    bool? requiresAuth,
    double? minZoom,
    double? maxZoom,
    List<String>? tags,
    Map<String, dynamic>? metadata,
  }) {
    return MapLayer(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      type: type ?? this.type,
      isVisible: isVisible ?? this.isVisible,
      isToggleable: isToggleable ?? this.isToggleable,
      opacity: opacity ?? this.opacity,
      zIndex: zIndex ?? this.zIndex,
      colorScheme: colorScheme ?? this.colorScheme,
      dataConfig: dataConfig ?? this.dataConfig,
      styleConfig: styleConfig ?? this.styleConfig,
      legend: legend ?? this.legend,
      requiresAuth: requiresAuth ?? this.requiresAuth,
      minZoom: minZoom ?? this.minZoom,
      maxZoom: maxZoom ?? this.maxZoom,
      tags: tags ?? this.tags,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Check if layer should be visible at current zoom
  bool isVisibleAtZoom(double zoom) {
    if (minZoom != null && zoom < minZoom!) return false;
    if (maxZoom != null && zoom > maxZoom!) return false;
    return isVisible;
  }

  /// Create a choropleth layer for risk visualization
  factory MapLayer.riskChoropleth({
    required String id,
    String name = 'Malaria Risk',
    String description = 'Choropleth map showing malaria risk levels',
  }) {
    return MapLayer(
      id: id,
      name: name,
      description: description,
      type: LayerType.choropleth,
      isVisible: true,
      isToggleable: true,
      opacity: 0.7,
      zIndex: 10,
      colorScheme: LayerColorScheme.riskDefault(),
      dataConfig: null,
      styleConfig: LayerStyleConfig.defaultStyle(),
      legend: LayerLegend.riskDefault(),
      requiresAuth: false,
      minZoom: 5,
      maxZoom: 18,
      tags: const ['risk', 'choropleth', 'malaria'],
      metadata: const {},
    );
  }

  /// Create a heatmap layer
  factory MapLayer.heatmap({
    required String id,
    required String name,
    String description = 'Heat map visualization',
  }) {
    return MapLayer(
      id: id,
      name: name,
      description: description,
      type: LayerType.heatmap,
      isVisible: true,
      isToggleable: true,
      opacity: 0.6,
      zIndex: 15,
      colorScheme: LayerColorScheme.riskDefault(),
      dataConfig: null,
      styleConfig: LayerStyleConfig.defaultStyle(),
      legend: null,
      requiresAuth: false,
      minZoom: 3,
      maxZoom: 18,
      tags: const ['heatmap'],
      metadata: const {},
    );
  }

  /// Create a markers layer
  factory MapLayer.markers({
    required String id,
    required String name,
    String description = 'Point markers',
  }) {
    return MapLayer(
      id: id,
      name: name,
      description: description,
      type: LayerType.markers,
      isVisible: true,
      isToggleable: true,
      opacity: 1.0,
      zIndex: 20,
      colorScheme: LayerColorScheme.riskDefault(),
      dataConfig: null,
      styleConfig: LayerStyleConfig.defaultStyle(),
      legend: null,
      requiresAuth: false,
      minZoom: null,
      maxZoom: null,
      tags: const ['markers'],
      metadata: const {},
    );
  }
}

/// Extension for MapLayer list operations
extension MapLayerListExtension on List<MapLayer> {
  /// Get visible layers
  List<MapLayer> get visibleLayers {
    return where((layer) => layer.isVisible).toList();
  }

  /// Get layers sorted by z-index
  List<MapLayer> get sortedByZIndex {
    final sorted = List<MapLayer>.from(this);
    sorted.sort((a, b) => a.zIndex.compareTo(b.zIndex));
    return sorted;
  }

  /// Get layers visible at a specific zoom level
  List<MapLayer> visibleAtZoom(double zoom) {
    return where((layer) => layer.isVisibleAtZoom(zoom)).toList();
  }

  /// Get layers by type
  List<MapLayer> ofType(LayerType type) {
    return where((layer) => layer.type == type).toList();
  }

  /// Get layers by tag
  List<MapLayer> withTag(String tag) {
    return where((layer) => layer.tags.contains(tag)).toList();
  }
}
