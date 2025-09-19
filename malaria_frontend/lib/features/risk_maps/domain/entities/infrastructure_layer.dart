/// Infrastructure Layer Entity for Risk Maps
///
/// Specialized entity for infrastructure data layers including hospitals,
/// health facilities, transportation networks, utilities, and other
/// infrastructure elements relevant to malaria risk and response.
///
/// Author: Claude AI Agent - Multi-Layer Mapping System
/// Created: 2025-09-19
library;

import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'map_layer.dart';

/// Infrastructure data layer for facility and service visualization
class InfrastructureLayer extends Equatable {
  /// Unique identifier for this infrastructure layer
  final String id;

  /// Display name for the infrastructure layer
  final String name;

  /// Detailed description of infrastructure data
  final String description;

  /// Type of infrastructure data
  final InfrastructureType infrastructureType;

  /// Whether this layer is currently visible
  final bool isVisible;

  /// Opacity of the layer (0.0 = transparent, 1.0 = opaque)
  final double opacity;

  /// Z-index for layer ordering
  final int zIndex;

  /// Data source configuration
  final InfrastructureDataSource dataSource;

  /// Visualization style for this infrastructure layer
  final InfrastructureVisualizationStyle visualizationStyle;

  /// Facility information and categorization
  final FacilityConfiguration facilityConfig;

  /// Service coverage and capacity information
  final ServiceCoverageInfo coverageInfo;

  /// Accessibility and transportation details
  final AccessibilityInfo accessibilityInfo;

  /// Operational status and real-time data
  final OperationalStatus operationalStatus;

  /// Quality and capacity metrics
  final InfrastructureMetrics metrics;

  /// Metadata about facilities, services, and capabilities
  final Map<String, dynamic> metadata;

  const InfrastructureLayer({
    required this.id,
    required this.name,
    required this.description,
    required this.infrastructureType,
    required this.isVisible,
    required this.opacity,
    required this.zIndex,
    required this.dataSource,
    required this.visualizationStyle,
    required this.facilityConfig,
    required this.coverageInfo,
    required this.accessibilityInfo,
    required this.operationalStatus,
    required this.metrics,
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
      tags: ['infrastructure', infrastructureType.name],
      metadata: metadata,
    );
  }

  /// Check if layer has real-time operational data
  bool get hasRealTimeData => operationalStatus.isRealTime;

  /// Get current operational status level
  OperationalLevel get operationalLevel => operationalStatus.level;

  /// Get service coverage radius in kilometers
  double get coverageRadius => coverageInfo.averageRadius;

  @override
  List<Object?> get props => [
        id,
        name,
        description,
        infrastructureType,
        isVisible,
        opacity,
        zIndex,
        dataSource,
        visualizationStyle,
        facilityConfig,
        coverageInfo,
        accessibilityInfo,
        operationalStatus,
        metrics,
        metadata,
      ];

  /// Create a copy with updated properties
  InfrastructureLayer copyWith({
    String? id,
    String? name,
    String? description,
    InfrastructureType? infrastructureType,
    bool? isVisible,
    double? opacity,
    int? zIndex,
    InfrastructureDataSource? dataSource,
    InfrastructureVisualizationStyle? visualizationStyle,
    FacilityConfiguration? facilityConfig,
    ServiceCoverageInfo? coverageInfo,
    AccessibilityInfo? accessibilityInfo,
    OperationalStatus? operationalStatus,
    InfrastructureMetrics? metrics,
    Map<String, dynamic>? metadata,
  }) {
    return InfrastructureLayer(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      infrastructureType: infrastructureType ?? this.infrastructureType,
      isVisible: isVisible ?? this.isVisible,
      opacity: opacity ?? this.opacity,
      zIndex: zIndex ?? this.zIndex,
      dataSource: dataSource ?? this.dataSource,
      visualizationStyle: visualizationStyle ?? this.visualizationStyle,
      facilityConfig: facilityConfig ?? this.facilityConfig,
      coverageInfo: coverageInfo ?? this.coverageInfo,
      accessibilityInfo: accessibilityInfo ?? this.accessibilityInfo,
      operationalStatus: operationalStatus ?? this.operationalStatus,
      metrics: metrics ?? this.metrics,
      metadata: metadata ?? this.metadata,
    );
  }

  // Helper methods for MapLayer conversion
  LayerType _getLayerType() {
    switch (visualizationStyle.renderingType) {
      case InfrastructureRenderingType.markers:
        return LayerType.markers;
      case InfrastructureRenderingType.clusters:
        return LayerType.markers;
      case InfrastructureRenderingType.network:
        return LayerType.lines;
      case InfrastructureRenderingType.serviceArea:
        return LayerType.polygons;
      case InfrastructureRenderingType.heatmap:
        return LayerType.heatmap;
    }
  }

  LayerColorScheme _buildColorScheme() {
    return LayerColorScheme(
      primaryColor: facilityConfig.primaryColor,
      secondaryColor: facilityConfig.secondaryColor,
      gradient: _buildGradientColors(),
      steps: 5,
      noDataColor: Colors.grey.shade300,
      borderColor: visualizationStyle.borderColor,
      highlightColor: visualizationStyle.highlightColor,
    );
  }

  List<Color> _buildGradientColors() {
    // Build gradient based on operational status or capacity
    return [
      Colors.red.shade300,    // Low capacity/offline
      Colors.orange.shade300, // Medium capacity
      Colors.yellow.shade300, // Good capacity
      Colors.lightGreen.shade300, // High capacity
      Colors.green.shade400,  // Excellent capacity/fully operational
    ];
  }

  LayerDataConfig _buildDataConfig() {
    return LayerDataConfig(
      dataUrl: dataSource.url,
      sourceType: DataSourceType.api,
      refreshInterval: dataSource.refreshInterval,
      enableCaching: true,
      cacheDuration: 1800, // 30 minutes
      dataFormat: dataSource.format,
      fieldMappings: dataSource.fieldMappings,
      filters: const [],
      aggregations: const {},
    );
  }

  LayerStyleConfig _buildStyleConfig() {
    return LayerStyleConfig(
      strokeWidth: visualizationStyle.strokeWidth,
      fillColor: facilityConfig.primaryColor.withValues(alpha: 0.3),
      strokeColor: visualizationStyle.borderColor,
      dashPattern: null,
      markerSize: visualizationStyle.markerSize,
      fontSize: 11,
      fontWeight: FontWeight.w500,
      textColor: Colors.black87,
    );
  }

  LayerLegend _buildLegend() {
    final items = _generateLegendItems();
    return LayerLegend(
      isVisible: true,
      title: name,
      items: items,
      position: LegendPosition.bottomLeft,
      backgroundColor: Colors.white.withValues(alpha: 0.9),
      textColor: Colors.black87,
      borderColor: Colors.grey.shade300,
    );
  }

  List<LegendItem> _generateLegendItems() {
    final items = <LegendItem>[];

    switch (infrastructureType) {
      case InfrastructureType.healthcare:
        items.addAll([
          LegendItem(
            color: Colors.red.shade600,
            label: 'Hospitals',
            value: 'hospital',
            description: 'Major healthcare facilities',
          ),
          LegendItem(
            color: Colors.blue.shade600,
            label: 'Health Centers',
            value: 'health_center',
            description: 'Primary care facilities',
          ),
          LegendItem(
            color: Colors.green.shade600,
            label: 'Clinics',
            value: 'clinic',
            description: 'Community health services',
          ),
        ]);
        break;

      case InfrastructureType.transportation:
        items.addAll([
          LegendItem(
            color: Colors.blue.shade800,
            label: 'Major Roads',
            value: 'highway',
            description: 'Primary transportation routes',
          ),
          LegendItem(
            color: Colors.blue.shade600,
            label: 'Secondary Roads',
            value: 'secondary',
            description: 'Regional connections',
          ),
          LegendItem(
            color: Colors.blue.shade400,
            label: 'Local Roads',
            value: 'local',
            description: 'Community access roads',
          ),
        ]);
        break;

      case InfrastructureType.utilities:
        items.addAll([
          LegendItem(
            color: Colors.yellow.shade700,
            label: 'Power Grid',
            value: 'power',
            description: 'Electricity infrastructure',
          ),
          LegendItem(
            color: Colors.blue.shade700,
            label: 'Water Supply',
            value: 'water',
            description: 'Clean water access points',
          ),
        ]);
        break;

      default:
        items.add(LegendItem(
          color: facilityConfig.primaryColor,
          label: infrastructureType.displayName,
          value: infrastructureType.name,
          description: description,
        ),);
    }

    return items;
  }
}

/// Types of infrastructure that can be visualized
enum InfrastructureType {
  /// Healthcare facilities (hospitals, clinics, health centers)
  healthcare,

  /// Transportation networks (roads, railways, airports)
  transportation,

  /// Educational institutions (schools, universities)
  education,

  /// Utilities (power, water, telecommunications)
  utilities,

  /// Emergency services (police, fire, ambulance)
  emergency,

  /// Government and administrative facilities
  government,

  /// Commercial and market areas
  commercial,

  /// Agricultural infrastructure
  agriculture,

  /// Research and surveillance facilities
  research,

  /// Border control and checkpoints
  borders,

  /// Housing and residential areas
  residential,

  /// Environmental monitoring stations
  monitoring;

  /// Get human-readable display name
  String get displayName {
    switch (this) {
      case InfrastructureType.healthcare:
        return 'Healthcare Facilities';
      case InfrastructureType.transportation:
        return 'Transportation';
      case InfrastructureType.education:
        return 'Educational Facilities';
      case InfrastructureType.utilities:
        return 'Utilities';
      case InfrastructureType.emergency:
        return 'Emergency Services';
      case InfrastructureType.government:
        return 'Government Facilities';
      case InfrastructureType.commercial:
        return 'Commercial Areas';
      case InfrastructureType.agriculture:
        return 'Agricultural Infrastructure';
      case InfrastructureType.research:
        return 'Research Facilities';
      case InfrastructureType.borders:
        return 'Border Control';
      case InfrastructureType.residential:
        return 'Residential Areas';
      case InfrastructureType.monitoring:
        return 'Monitoring Stations';
    }
  }

  /// Get default icon for this infrastructure type
  IconData get defaultIcon {
    switch (this) {
      case InfrastructureType.healthcare:
        return Icons.local_hospital;
      case InfrastructureType.transportation:
        return Icons.directions_car;
      case InfrastructureType.education:
        return Icons.school;
      case InfrastructureType.utilities:
        return Icons.power;
      case InfrastructureType.emergency:
        return Icons.emergency;
      case InfrastructureType.government:
        return Icons.account_balance;
      case InfrastructureType.commercial:
        return Icons.store;
      case InfrastructureType.agriculture:
        return Icons.agriculture;
      case InfrastructureType.research:
        return Icons.science;
      case InfrastructureType.borders:
        return Icons.border_clear;
      case InfrastructureType.residential:
        return Icons.home;
      case InfrastructureType.monitoring:
        return Icons.sensors;
    }
  }
}

/// Data source configuration for infrastructure layers
class InfrastructureDataSource extends Equatable {
  /// URL endpoint for data retrieval
  final String url;

  /// Data format (geojson, json, csv, etc.)
  final String format;

  /// Source provider/organization
  final String provider;

  /// Refresh interval in seconds for real-time data
  final int? refreshInterval;

  /// Field mappings for data interpretation
  final Map<String, String> fieldMappings;

  /// Data licensing information
  final String license;

  /// Data accuracy and validation level
  final double accuracy;

  /// Last update timestamp
  final DateTime lastUpdated;

  const InfrastructureDataSource({
    required this.url,
    required this.format,
    required this.provider,
    this.refreshInterval,
    required this.fieldMappings,
    required this.license,
    required this.accuracy,
    required this.lastUpdated,
  });

  @override
  List<Object?> get props => [
        url,
        format,
        provider,
        refreshInterval,
        fieldMappings,
        license,
        accuracy,
        lastUpdated,
      ];
}

/// Visualization style configuration for infrastructure layers
class InfrastructureVisualizationStyle extends Equatable {
  /// Type of rendering for this infrastructure layer
  final InfrastructureRenderingType renderingType;

  /// Stroke width for lines and borders
  final double strokeWidth;

  /// Border color for facilities and areas
  final Color borderColor;

  /// Highlight color for selected facilities
  final Color highlightColor;

  /// Marker size for point features
  final double markerSize;

  /// Minimum zoom level for visibility
  final double? minZoom;

  /// Maximum zoom level for visibility
  final double? maxZoom;

  /// Clustering settings for dense areas
  final ClusteringConfiguration? clustering;

  /// Label display settings
  final LabelConfiguration labelConfig;

  const InfrastructureVisualizationStyle({
    required this.renderingType,
    required this.strokeWidth,
    required this.borderColor,
    required this.highlightColor,
    required this.markerSize,
    this.minZoom,
    this.maxZoom,
    this.clustering,
    required this.labelConfig,
  });

  @override
  List<Object?> get props => [
        renderingType,
        strokeWidth,
        borderColor,
        highlightColor,
        markerSize,
        minZoom,
        maxZoom,
        clustering,
        labelConfig,
      ];
}

/// Rendering types for infrastructure data visualization
enum InfrastructureRenderingType {
  /// Individual markers for each facility
  markers,

  /// Clustered markers for dense areas
  clusters,

  /// Network lines for transportation
  network,

  /// Service coverage areas
  serviceArea,

  /// Heat map for facility density
  heatmap;
}

/// Facility configuration and categorization
class FacilityConfiguration extends Equatable {
  /// Primary color for this facility type
  final Color primaryColor;

  /// Secondary color for variations
  final Color secondaryColor;

  /// Facility categories and classifications
  final List<FacilityCategory> categories;

  /// Capacity information
  final CapacityInfo capacity;

  /// Service types offered
  final List<String> serviceTypes;

  /// Operating hours and availability
  final OperatingHours operatingHours;

  const FacilityConfiguration({
    required this.primaryColor,
    required this.secondaryColor,
    required this.categories,
    required this.capacity,
    required this.serviceTypes,
    required this.operatingHours,
  });

  @override
  List<Object?> get props => [
        primaryColor,
        secondaryColor,
        categories,
        capacity,
        serviceTypes,
        operatingHours,
      ];
}

/// Facility categories for detailed classification
class FacilityCategory extends Equatable {
  /// Category identifier
  final String id;

  /// Display name
  final String name;

  /// Category description
  final String description;

  /// Category level (primary, secondary, tertiary)
  final String level;

  /// Icon representation
  final IconData icon;

  /// Color coding
  final Color color;

  const FacilityCategory({
    required this.id,
    required this.name,
    required this.description,
    required this.level,
    required this.icon,
    required this.color,
  });

  @override
  List<Object?> get props => [id, name, description, level, icon, color];
}

/// Service coverage information
class ServiceCoverageInfo extends Equatable {
  /// Average service radius in kilometers
  final double averageRadius;

  /// Maximum service radius
  final double maxRadius;

  /// Population served
  final int populationServed;

  /// Coverage percentage of total area
  final double coveragePercentage;

  /// Service quality metrics
  final Map<String, double> qualityMetrics;

  const ServiceCoverageInfo({
    required this.averageRadius,
    required this.maxRadius,
    required this.populationServed,
    required this.coveragePercentage,
    required this.qualityMetrics,
  });

  @override
  List<Object?> get props => [
        averageRadius,
        maxRadius,
        populationServed,
        coveragePercentage,
        qualityMetrics,
      ];
}

/// Accessibility information for infrastructure
class AccessibilityInfo extends Equatable {
  /// Average travel time in minutes
  final double averageTravelTime;

  /// Maximum travel time
  final double maxTravelTime;

  /// Transportation modes available
  final List<TransportMode> transportModes;

  /// Road quality assessment
  final RoadQuality roadQuality;

  /// Seasonal accessibility
  final SeasonalAccess seasonalAccess;

  const AccessibilityInfo({
    required this.averageTravelTime,
    required this.maxTravelTime,
    required this.transportModes,
    required this.roadQuality,
    required this.seasonalAccess,
  });

  @override
  List<Object?> get props => [
        averageTravelTime,
        maxTravelTime,
        transportModes,
        roadQuality,
        seasonalAccess,
      ];
}

/// Transportation modes available
enum TransportMode {
  walking,
  bicycle,
  motorcycle,
  car,
  publicTransport,
  boat,
  aircraft;

  String get displayName {
    switch (this) {
      case TransportMode.walking:
        return 'Walking';
      case TransportMode.bicycle:
        return 'Bicycle';
      case TransportMode.motorcycle:
        return 'Motorcycle';
      case TransportMode.car:
        return 'Car';
      case TransportMode.publicTransport:
        return 'Public Transport';
      case TransportMode.boat:
        return 'Boat';
      case TransportMode.aircraft:
        return 'Aircraft';
    }
  }
}

/// Road quality assessment
enum RoadQuality {
  excellent,
  good,
  fair,
  poor,
  impassable;

  Color get color {
    switch (this) {
      case RoadQuality.excellent:
        return Colors.green;
      case RoadQuality.good:
        return Colors.lightGreen;
      case RoadQuality.fair:
        return Colors.yellow;
      case RoadQuality.poor:
        return Colors.orange;
      case RoadQuality.impassable:
        return Colors.red;
    }
  }
}

/// Seasonal accessibility patterns
class SeasonalAccess extends Equatable {
  /// Accessibility during dry season
  final bool drySeasonAccess;

  /// Accessibility during wet season
  final bool wetSeasonAccess;

  /// Months with reduced access
  final List<int> restrictedMonths;

  /// Alternative access during restrictions
  final String alternativeAccess;

  const SeasonalAccess({
    required this.drySeasonAccess,
    required this.wetSeasonAccess,
    required this.restrictedMonths,
    required this.alternativeAccess,
  });

  @override
  List<Object?> get props => [
        drySeasonAccess,
        wetSeasonAccess,
        restrictedMonths,
        alternativeAccess,
      ];
}

/// Operational status and real-time information
class OperationalStatus extends Equatable {
  /// Current operational level
  final OperationalLevel level;

  /// Whether real-time data is available
  final bool isRealTime;

  /// Last status update
  final DateTime lastUpdate;

  /// Status notes and details
  final String statusNotes;

  /// Current capacity utilization
  final double capacityUtilization;

  /// Maintenance and downtime schedules
  final List<MaintenanceWindow> maintenance;

  const OperationalStatus({
    required this.level,
    required this.isRealTime,
    required this.lastUpdate,
    required this.statusNotes,
    required this.capacityUtilization,
    required this.maintenance,
  });

  @override
  List<Object?> get props => [
        level,
        isRealTime,
        lastUpdate,
        statusNotes,
        capacityUtilization,
        maintenance,
      ];
}

/// Operational levels for infrastructure
enum OperationalLevel {
  fullyOperational,
  partiallyOperational,
  limitedOperational,
  offline,
  maintenance;

  Color get color {
    switch (this) {
      case OperationalLevel.fullyOperational:
        return Colors.green;
      case OperationalLevel.partiallyOperational:
        return Colors.yellow;
      case OperationalLevel.limitedOperational:
        return Colors.orange;
      case OperationalLevel.offline:
        return Colors.red;
      case OperationalLevel.maintenance:
        return Colors.blue;
    }
  }
}

/// Infrastructure metrics and performance indicators
class InfrastructureMetrics extends Equatable {
  /// Utilization rate (0.0 to 1.0)
  final double utilizationRate;

  /// Efficiency score (0.0 to 1.0)
  final double efficiencyScore;

  /// Quality rating (1 to 5 stars)
  final int qualityRating;

  /// User satisfaction score (0.0 to 1.0)
  final double satisfactionScore;

  /// Reliability percentage
  final double reliability;

  /// Performance trends over time
  final Map<String, List<double>> trends;

  const InfrastructureMetrics({
    required this.utilizationRate,
    required this.efficiencyScore,
    required this.qualityRating,
    required this.satisfactionScore,
    required this.reliability,
    required this.trends,
  });

  @override
  List<Object?> get props => [
        utilizationRate,
        efficiencyScore,
        qualityRating,
        satisfactionScore,
        reliability,
        trends,
      ];
}

/// Additional supporting classes
class CapacityInfo extends Equatable {
  final int totalCapacity;
  final int currentLoad;
  final int availableCapacity;

  const CapacityInfo({
    required this.totalCapacity,
    required this.currentLoad,
    required this.availableCapacity,
  });

  double get utilizationPercentage => currentLoad / totalCapacity;

  @override
  List<Object?> get props => [totalCapacity, currentLoad, availableCapacity];
}

class OperatingHours extends Equatable {
  final String weekdayHours;
  final String weekendHours;
  final bool is24Hours;
  final List<String> holidays;

  const OperatingHours({
    required this.weekdayHours,
    required this.weekendHours,
    required this.is24Hours,
    required this.holidays,
  });

  @override
  List<Object?> get props => [weekdayHours, weekendHours, is24Hours, holidays];
}

class ClusteringConfiguration extends Equatable {
  final bool enableClustering;
  final int minClusterSize;
  final double clusterRadius;
  final int maxZoomForClustering;

  const ClusteringConfiguration({
    required this.enableClustering,
    required this.minClusterSize,
    required this.clusterRadius,
    required this.maxZoomForClustering,
  });

  @override
  List<Object?> get props => [
        enableClustering,
        minClusterSize,
        clusterRadius,
        maxZoomForClustering,
      ];
}

class LabelConfiguration extends Equatable {
  final bool showLabels;
  final double fontSize;
  final Color textColor;
  final Color backgroundColor;
  final double minZoomForLabels;

  const LabelConfiguration({
    required this.showLabels,
    required this.fontSize,
    required this.textColor,
    required this.backgroundColor,
    required this.minZoomForLabels,
  });

  @override
  List<Object?> get props => [
        showLabels,
        fontSize,
        textColor,
        backgroundColor,
        minZoomForLabels,
      ];
}

class MaintenanceWindow extends Equatable {
  final DateTime startTime;
  final DateTime endTime;
  final String description;
  final bool affectsService;

  const MaintenanceWindow({
    required this.startTime,
    required this.endTime,
    required this.description,
    required this.affectsService,
  });

  @override
  List<Object?> get props => [startTime, endTime, description, affectsService];
}