/// Environmental Layer Entity for Risk Maps
///
/// Specialized entity for environmental data layers including temperature,
/// rainfall, vegetation, climate data, and other environmental factors
/// that impact malaria risk assessment.
///
/// Author: Claude AI Agent - Multi-Layer Mapping System
/// Created: 2025-09-19
library;

import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'map_layer.dart';

/// Environmental data layer for environmental factor visualization
class EnvironmentalLayer extends Equatable {
  /// Unique identifier for this environmental layer
  final String id;

  /// Display name for the environmental layer
  final String name;

  /// Detailed description of environmental data
  final String description;

  /// Type of environmental data
  final EnvironmentalDataType dataType;

  /// Whether this layer is currently visible
  final bool isVisible;

  /// Opacity of the layer (0.0 = transparent, 1.0 = opaque)
  final double opacity;

  /// Z-index for layer ordering
  final int zIndex;

  /// Data source configuration
  final EnvironmentalDataSource dataSource;

  /// Visualization style for this environmental layer
  final EnvironmentalVisualizationStyle visualizationStyle;

  /// Color mapping for environmental values
  final EnvironmentalColorMapping colorMapping;

  /// Temporal information for time-series data
  final TemporalConfiguration? temporalConfig;

  /// Data quality and reliability indicators
  final DataQualityInfo qualityInfo;

  /// Statistical information about the data
  final EnvironmentalStatistics statistics;

  /// Metadata about units, ranges, and interpretations
  final Map<String, dynamic> metadata;

  const EnvironmentalLayer({
    required this.id,
    required this.name,
    required this.description,
    required this.dataType,
    required this.isVisible,
    required this.opacity,
    required this.zIndex,
    required this.dataSource,
    required this.visualizationStyle,
    required this.colorMapping,
    this.temporalConfig,
    required this.qualityInfo,
    required this.statistics,
    required this.metadata,
  });

  /// Convert to base MapLayer for unified layer management
  MapLayer toMapLayer() {
    return MapLayer(
      id: id,
      name: name,
      description: description,
      type: _getLayerType(),
      isVisible: isVisible,
      isToggleable: true,
      opacity: opacity,
      zIndex: zIndex,
      colorScheme: _buildColorScheme(),
      dataConfig: _buildDataConfig(),
      styleConfig: _buildStyleConfig(),
      legend: _buildLegend(),
      requiresAuth: false,
      minZoom: visualizationStyle.minZoom,
      maxZoom: visualizationStyle.maxZoom,
      tags: ['environmental', dataType.name],
      metadata: metadata,
    );
  }

  /// Check if layer has temporal data capabilities
  bool get hasTemporalData => temporalConfig != null;

  /// Get current data quality level
  DataQualityLevel get qualityLevel => qualityInfo.level;

  /// Get data unit display string
  String get unitDisplay => statistics.unit;

  @override
  List<Object?> get props => [
        id,
        name,
        description,
        dataType,
        isVisible,
        opacity,
        zIndex,
        dataSource,
        visualizationStyle,
        colorMapping,
        temporalConfig,
        qualityInfo,
        statistics,
        metadata,
      ];

  /// Create a copy with updated properties
  EnvironmentalLayer copyWith({
    String? id,
    String? name,
    String? description,
    EnvironmentalDataType? dataType,
    bool? isVisible,
    double? opacity,
    int? zIndex,
    EnvironmentalDataSource? dataSource,
    EnvironmentalVisualizationStyle? visualizationStyle,
    EnvironmentalColorMapping? colorMapping,
    TemporalConfiguration? temporalConfig,
    DataQualityInfo? qualityInfo,
    EnvironmentalStatistics? statistics,
    Map<String, dynamic>? metadata,
  }) {
    return EnvironmentalLayer(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      dataType: dataType ?? this.dataType,
      isVisible: isVisible ?? this.isVisible,
      opacity: opacity ?? this.opacity,
      zIndex: zIndex ?? this.zIndex,
      dataSource: dataSource ?? this.dataSource,
      visualizationStyle: visualizationStyle ?? this.visualizationStyle,
      colorMapping: colorMapping ?? this.colorMapping,
      temporalConfig: temporalConfig ?? this.temporalConfig,
      qualityInfo: qualityInfo ?? this.qualityInfo,
      statistics: statistics ?? this.statistics,
      metadata: metadata ?? this.metadata,
    );
  }

  // Helper methods for MapLayer conversion
  LayerType _getLayerType() {
    switch (visualizationStyle.renderingType) {
      case EnvironmentalRenderingType.choropleth:
        return LayerType.choropleth;
      case EnvironmentalRenderingType.heatmap:
        return LayerType.heatmap;
      case EnvironmentalRenderingType.contour:
        return LayerType.vector;
      case EnvironmentalRenderingType.raster:
        return LayerType.raster;
      case EnvironmentalRenderingType.isoline:
        return LayerType.lines;
    }
  }

  LayerColorScheme _buildColorScheme() {
    return LayerColorScheme(
      primaryColor: colorMapping.primaryColor,
      secondaryColor: colorMapping.secondaryColor,
      gradient: colorMapping.gradient,
      steps: colorMapping.steps,
      noDataColor: colorMapping.noDataColor,
      borderColor: visualizationStyle.borderColor,
      highlightColor: visualizationStyle.highlightColor,
    );
  }

  LayerDataConfig _buildDataConfig() {
    return LayerDataConfig(
      dataUrl: dataSource.url,
      sourceType: DataSourceType.api,
      refreshInterval: dataSource.refreshInterval,
      enableCaching: true,
      cacheDuration: 3600, // 1 hour
      dataFormat: dataSource.format,
      fieldMappings: dataSource.fieldMappings,
      filters: const [],
      aggregations: const {},
    );
  }

  LayerStyleConfig _buildStyleConfig() {
    return LayerStyleConfig(
      strokeWidth: visualizationStyle.strokeWidth,
      fillColor: null,
      strokeColor: visualizationStyle.borderColor,
      dashPattern: null,
      markerSize: 8,
      fontSize: 12,
      fontWeight: FontWeight.normal,
      textColor: Colors.black87,
    );
  }

  LayerLegend _buildLegend() {
    final items = _generateLegendItems();
    return LayerLegend(
      isVisible: true,
      title: name,
      items: items,
      position: LegendPosition.bottomRight,
      backgroundColor: Colors.white.withValues(alpha: 0.9),
      textColor: Colors.black87,
      borderColor: Colors.grey.shade300,
    );
  }

  List<LegendItem> _generateLegendItems() {
    final items = <LegendItem>[];
    final stepSize = (statistics.maxValue - statistics.minValue) / colorMapping.steps;

    for (int i = 0; i < colorMapping.steps; i++) {
      final value = statistics.minValue + (i * stepSize);
      final nextValue = statistics.minValue + ((i + 1) * stepSize);
      final color = colorMapping.gradient[i];

      items.add(LegendItem(
        color: color,
        label: '${value.toStringAsFixed(1)} - ${nextValue.toStringAsFixed(1)}',
        value: value.toStringAsFixed(1),
        description: statistics.unit,
      ),);
    }

    return items;
  }
}

/// Types of environmental data that can be visualized
enum EnvironmentalDataType {
  /// Temperature data (daily, monthly, seasonal averages)
  temperature,

  /// Rainfall and precipitation data
  rainfall,

  /// Vegetation index and land cover data
  vegetation,

  /// Humidity and moisture levels
  humidity,

  /// Wind patterns and speed
  wind,

  /// Solar radiation and UV index
  solar,

  /// Elevation and topography
  elevation,

  /// Soil moisture and composition
  soil,

  /// Water body identification and quality
  water,

  /// Land use and urban development
  landUse,

  /// Air quality and pollution levels
  airQuality,

  /// Climate zones and classifications
  climate;

  /// Get human-readable display name
  String get displayName {
    switch (this) {
      case EnvironmentalDataType.temperature:
        return 'Temperature';
      case EnvironmentalDataType.rainfall:
        return 'Rainfall';
      case EnvironmentalDataType.vegetation:
        return 'Vegetation';
      case EnvironmentalDataType.humidity:
        return 'Humidity';
      case EnvironmentalDataType.wind:
        return 'Wind';
      case EnvironmentalDataType.solar:
        return 'Solar Radiation';
      case EnvironmentalDataType.elevation:
        return 'Elevation';
      case EnvironmentalDataType.soil:
        return 'Soil';
      case EnvironmentalDataType.water:
        return 'Water Bodies';
      case EnvironmentalDataType.landUse:
        return 'Land Use';
      case EnvironmentalDataType.airQuality:
        return 'Air Quality';
      case EnvironmentalDataType.climate:
        return 'Climate';
    }
  }

  /// Get typical unit for this data type
  String get defaultUnit {
    switch (this) {
      case EnvironmentalDataType.temperature:
        return '°C';
      case EnvironmentalDataType.rainfall:
        return 'mm';
      case EnvironmentalDataType.vegetation:
        return 'NDVI';
      case EnvironmentalDataType.humidity:
        return '%';
      case EnvironmentalDataType.wind:
        return 'm/s';
      case EnvironmentalDataType.solar:
        return 'W/m²';
      case EnvironmentalDataType.elevation:
        return 'm';
      case EnvironmentalDataType.soil:
        return 'index';
      case EnvironmentalDataType.water:
        return 'binary';
      case EnvironmentalDataType.landUse:
        return 'category';
      case EnvironmentalDataType.airQuality:
        return 'AQI';
      case EnvironmentalDataType.climate:
        return 'category';
    }
  }
}

/// Data source configuration for environmental layers
class EnvironmentalDataSource extends Equatable {
  /// URL endpoint for data retrieval
  final String url;

  /// Data format (geojson, netcdf, tiff, etc.)
  final String format;

  /// Source provider/organization
  final String provider;

  /// Refresh interval in seconds for real-time data
  final int? refreshInterval;

  /// Field mappings for data interpretation
  final Map<String, String> fieldMappings;

  /// Quality assessment information
  final String qualityAssessment;

  /// Spatial resolution of the data
  final double spatialResolution;

  /// Temporal resolution (daily, monthly, etc.)
  final String temporalResolution;

  const EnvironmentalDataSource({
    required this.url,
    required this.format,
    required this.provider,
    this.refreshInterval,
    required this.fieldMappings,
    required this.qualityAssessment,
    required this.spatialResolution,
    required this.temporalResolution,
  });

  @override
  List<Object?> get props => [
        url,
        format,
        provider,
        refreshInterval,
        fieldMappings,
        qualityAssessment,
        spatialResolution,
        temporalResolution,
      ];
}

/// Visualization style configuration for environmental layers
class EnvironmentalVisualizationStyle extends Equatable {
  /// Type of rendering for this environmental layer
  final EnvironmentalRenderingType renderingType;

  /// Stroke width for vector elements
  final double strokeWidth;

  /// Border color for polygons and regions
  final Color borderColor;

  /// Highlight color for selected areas
  final Color highlightColor;

  /// Transparency for overlay blending
  final double transparency;

  /// Minimum zoom level for visibility
  final double? minZoom;

  /// Maximum zoom level for visibility
  final double? maxZoom;

  /// Smoothing factor for interpolation
  final double smoothing;

  /// Animation settings for dynamic layers
  final bool enableAnimations;

  const EnvironmentalVisualizationStyle({
    required this.renderingType,
    required this.strokeWidth,
    required this.borderColor,
    required this.highlightColor,
    required this.transparency,
    this.minZoom,
    this.maxZoom,
    required this.smoothing,
    required this.enableAnimations,
  });

  @override
  List<Object?> get props => [
        renderingType,
        strokeWidth,
        borderColor,
        highlightColor,
        transparency,
        minZoom,
        maxZoom,
        smoothing,
        enableAnimations,
      ];
}

/// Rendering types for environmental data visualization
enum EnvironmentalRenderingType {
  /// Colored regions based on data values
  choropleth,

  /// Heat map with smooth gradients
  heatmap,

  /// Contour lines for equal values
  contour,

  /// Raster image overlay
  raster,

  /// Isoline representation
  isoline;
}

/// Color mapping configuration for environmental values
class EnvironmentalColorMapping extends Equatable {
  /// Primary color for the scale
  final Color primaryColor;

  /// Secondary color for contrast
  final Color secondaryColor;

  /// Color gradient for value mapping
  final List<Color> gradient;

  /// Number of color steps
  final int steps;

  /// Color for no-data or null values
  final Color noDataColor;

  /// Color scale type (linear, logarithmic, etc.)
  final ColorScaleType scaleType;

  /// Invert the color scale
  final bool invertScale;

  const EnvironmentalColorMapping({
    required this.primaryColor,
    required this.secondaryColor,
    required this.gradient,
    required this.steps,
    required this.noDataColor,
    required this.scaleType,
    required this.invertScale,
  });

  @override
  List<Object?> get props => [
        primaryColor,
        secondaryColor,
        gradient,
        steps,
        noDataColor,
        scaleType,
        invertScale,
      ];
}

/// Color scale types for data visualization
enum ColorScaleType {
  /// Linear color scale
  linear,

  /// Logarithmic color scale
  logarithmic,

  /// Quantile-based color scale
  quantile,

  /// Custom defined breakpoints
  custom;
}

/// Temporal configuration for time-series environmental data
class TemporalConfiguration extends Equatable {
  /// Start date for temporal data
  final DateTime startDate;

  /// End date for temporal data
  final DateTime endDate;

  /// Current time for animation
  final DateTime currentTime;

  /// Time step for animation (in milliseconds)
  final int timeStep;

  /// Whether to enable temporal animation
  final bool enableAnimation;

  /// Animation loop mode
  final TemporalLoopMode loopMode;

  const TemporalConfiguration({
    required this.startDate,
    required this.endDate,
    required this.currentTime,
    required this.timeStep,
    required this.enableAnimation,
    required this.loopMode,
  });

  @override
  List<Object?> get props => [
        startDate,
        endDate,
        currentTime,
        timeStep,
        enableAnimation,
        loopMode,
      ];
}

/// Loop modes for temporal animation
enum TemporalLoopMode {
  /// Play once and stop
  once,

  /// Loop continuously
  loop,

  /// Loop back and forth
  pingPong;
}

/// Data quality information for environmental layers
class DataQualityInfo extends Equatable {
  /// Overall quality level
  final DataQualityLevel level;

  /// Accuracy percentage (0-100)
  final double accuracy;

  /// Completeness percentage (0-100)
  final double completeness;

  /// Data freshness (time since last update)
  final Duration freshness;

  /// Quality assessment notes
  final String notes;

  const DataQualityInfo({
    required this.level,
    required this.accuracy,
    required this.completeness,
    required this.freshness,
    required this.notes,
  });

  @override
  List<Object?> get props => [level, accuracy, completeness, freshness, notes];
}

/// Quality levels for environmental data
enum DataQualityLevel {
  /// High quality, validated data
  high,

  /// Medium quality with some limitations
  medium,

  /// Low quality, use with caution
  low,

  /// Quality unknown or not assessed
  unknown;

  /// Get color representation for quality level
  Color get color {
    switch (this) {
      case DataQualityLevel.high:
        return Colors.green;
      case DataQualityLevel.medium:
        return Colors.orange;
      case DataQualityLevel.low:
        return Colors.red;
      case DataQualityLevel.unknown:
        return Colors.grey;
    }
  }
}

/// Statistical information about environmental data
class EnvironmentalStatistics extends Equatable {
  /// Minimum value in the dataset
  final double minValue;

  /// Maximum value in the dataset
  final double maxValue;

  /// Mean/average value
  final double meanValue;

  /// Standard deviation
  final double standardDeviation;

  /// Data unit (°C, mm, etc.)
  final String unit;

  /// Number of data points
  final int dataPoints;

  /// Percentage of missing data
  final double missingDataPercentage;

  const EnvironmentalStatistics({
    required this.minValue,
    required this.maxValue,
    required this.meanValue,
    required this.standardDeviation,
    required this.unit,
    required this.dataPoints,
    required this.missingDataPercentage,
  });

  @override
  List<Object?> get props => [
        minValue,
        maxValue,
        meanValue,
        standardDeviation,
        unit,
        dataPoints,
        missingDataPercentage,
      ];
}