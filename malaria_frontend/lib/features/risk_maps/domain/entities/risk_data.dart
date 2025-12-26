/// Risk Data Entity for Malaria Risk Visualization
///
/// Core entity representing malaria risk data for geographic regions,
/// including risk scores, confidence levels, environmental factors,
/// and supporting data for map visualizations.
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';

/// Risk levels for malaria outbreak classification
enum RiskLevel {
  /// Low risk - minimal intervention required
  low,

  /// Medium risk - moderate intervention recommended
  medium,

  /// High risk - immediate intervention recommended
  high,

  /// Critical risk - emergency response required
  critical;

  /// Get display name for this risk level
  String get displayName {
    switch (this) {
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

  /// Get color representation for this risk level
  Color get color {
    switch (this) {
      case RiskLevel.low:
        return const Color(0xFF4CAF50); // Green
      case RiskLevel.medium:
        return const Color(0xFFFF9800); // Orange
      case RiskLevel.high:
        return const Color(0xFFF44336); // Red
      case RiskLevel.critical:
        return const Color(0xFF9C27B0); // Purple
    }
  }

  /// Get fill color with opacity for choropleth overlays
  Color get fillColor {
    switch (this) {
      case RiskLevel.low:
        return const Color(0xFF4CAF50).withValues(alpha: 0.4);
      case RiskLevel.medium:
        return const Color(0xFFFF9800).withValues(alpha: 0.5);
      case RiskLevel.high:
        return const Color(0xFFF44336).withValues(alpha: 0.6);
      case RiskLevel.critical:
        return const Color(0xFF9C27B0).withValues(alpha: 0.7);
    }
  }

  /// Get border color for choropleth regions
  Color get borderColor {
    switch (this) {
      case RiskLevel.low:
        return const Color(0xFF388E3C);
      case RiskLevel.medium:
        return const Color(0xFFF57C00);
      case RiskLevel.high:
        return const Color(0xFFD32F2F);
      case RiskLevel.critical:
        return const Color(0xFF7B1FA2);
    }
  }

  /// Get icon for this risk level
  IconData get icon {
    switch (this) {
      case RiskLevel.low:
        return Icons.check_circle;
      case RiskLevel.medium:
        return Icons.warning;
      case RiskLevel.high:
        return Icons.error;
      case RiskLevel.critical:
        return Icons.dangerous;
    }
  }

  /// Create RiskLevel from numeric score
  static RiskLevel fromScore(double score) {
    if (score >= 0.8) return RiskLevel.critical;
    if (score >= 0.6) return RiskLevel.high;
    if (score >= 0.3) return RiskLevel.medium;
    return RiskLevel.low;
  }
}

/// Environmental factors affecting malaria risk
class EnvironmentalFactors extends Equatable {
  /// Temperature in Celsius
  final double temperature;

  /// Relative humidity percentage
  final double humidity;

  /// Monthly rainfall in mm
  final double rainfall;

  /// Vegetation index (NDVI)
  final double vegetationIndex;

  /// Elevation in meters
  final double? elevation;

  /// Water body proximity in km
  final double? waterBodyProximity;

  /// Population density per km²
  final double? populationDensity;

  const EnvironmentalFactors({
    required this.temperature,
    required this.humidity,
    required this.rainfall,
    required this.vegetationIndex,
    this.elevation,
    this.waterBodyProximity,
    this.populationDensity,
  });

  @override
  List<Object?> get props => [
        temperature,
        humidity,
        rainfall,
        vegetationIndex,
        elevation,
        waterBodyProximity,
        populationDensity,
      ];

  /// Create a copy with updated values
  EnvironmentalFactors copyWith({
    double? temperature,
    double? humidity,
    double? rainfall,
    double? vegetationIndex,
    double? elevation,
    double? waterBodyProximity,
    double? populationDensity,
  }) {
    return EnvironmentalFactors(
      temperature: temperature ?? this.temperature,
      humidity: humidity ?? this.humidity,
      rainfall: rainfall ?? this.rainfall,
      vegetationIndex: vegetationIndex ?? this.vegetationIndex,
      elevation: elevation ?? this.elevation,
      waterBodyProximity: waterBodyProximity ?? this.waterBodyProximity,
      populationDensity: populationDensity ?? this.populationDensity,
    );
  }

  /// Convert to map for serialization
  Map<String, double> toMap() {
    return {
      'temperature': temperature,
      'humidity': humidity,
      'rainfall': rainfall,
      'vegetationIndex': vegetationIndex,
      if (elevation != null) 'elevation': elevation!,
      if (waterBodyProximity != null) 'waterBodyProximity': waterBodyProximity!,
      if (populationDensity != null) 'populationDensity': populationDensity!,
    };
  }

  /// Create from map
  factory EnvironmentalFactors.fromMap(Map<String, dynamic> map) {
    return EnvironmentalFactors(
      temperature: (map['temperature'] as num?)?.toDouble() ?? 0.0,
      humidity: (map['humidity'] as num?)?.toDouble() ?? 0.0,
      rainfall: (map['rainfall'] as num?)?.toDouble() ?? 0.0,
      vegetationIndex: (map['vegetationIndex'] as num?)?.toDouble() ?? 0.0,
      elevation: (map['elevation'] as num?)?.toDouble(),
      waterBodyProximity: (map['waterBodyProximity'] as num?)?.toDouble(),
      populationDensity: (map['populationDensity'] as num?)?.toDouble(),
    );
  }
}

/// Geographic boundary for risk regions
class GeographicBoundary extends Equatable {
  /// List of coordinates forming the polygon boundary
  final List<LatLng> coordinates;

  /// Center point of the boundary
  final LatLng center;

  /// Area in square kilometers
  final double areaKm2;

  const GeographicBoundary({
    required this.coordinates,
    required this.center,
    required this.areaKm2,
  });

  @override
  List<Object?> get props => [coordinates, center, areaKm2];

  /// Check if a point is within this boundary
  bool containsPoint(LatLng point) {
    // Ray casting algorithm for point-in-polygon
    int intersections = 0;
    final n = coordinates.length;

    for (int i = 0; i < n; i++) {
      final p1 = coordinates[i];
      final p2 = coordinates[(i + 1) % n];

      if (point.latitude > p1.latitude != point.latitude > p2.latitude) {
        final x = (p2.longitude - p1.longitude) *
                (point.latitude - p1.latitude) /
                (p2.latitude - p1.latitude) +
            p1.longitude;

        if (point.longitude < x) {
          intersections++;
        }
      }
    }

    return intersections.isOdd;
  }
}

/// Geographic bounds for map viewport
class GeographicBounds extends Equatable {
  /// Southwest corner
  final LatLng southWest;

  /// Northeast corner
  final LatLng northEast;

  const GeographicBounds({
    required this.southWest,
    required this.northEast,
  });

  @override
  List<Object?> get props => [southWest, northEast];

  /// Get center of bounds
  LatLng get center {
    return LatLng(
      (southWest.latitude + northEast.latitude) / 2,
      (southWest.longitude + northEast.longitude) / 2,
    );
  }

  /// Check if bounds contains a point
  bool contains(LatLng point) {
    return point.latitude >= southWest.latitude &&
        point.latitude <= northEast.latitude &&
        point.longitude >= southWest.longitude &&
        point.longitude <= northEast.longitude;
  }

  /// Check if bounds intersects with another bounds
  bool intersects(GeographicBounds other) {
    return !(other.northEast.latitude < southWest.latitude ||
        other.southWest.latitude > northEast.latitude ||
        other.northEast.longitude < southWest.longitude ||
        other.southWest.longitude > northEast.longitude);
  }
}

/// Core risk data entity for a geographic region
class RiskData extends Equatable {
  /// Unique identifier for this risk data entry
  final String id;

  /// Region identifier (e.g., constituency, district)
  final String region;

  /// Human-readable region name
  final String regionName;

  /// Administrative level (constituency, district, county)
  final String administrativeLevel;

  /// Center coordinates of the region
  final LatLng coordinates;

  /// Geographic boundary of the region
  final GeographicBoundary? boundary;

  /// Risk score (0.0 to 1.0)
  final double riskScore;

  /// Computed risk level
  final RiskLevel riskLevel;

  /// Confidence level of the prediction (0.0 to 1.0)
  final double confidence;

  /// Environmental factors contributing to risk
  final EnvironmentalFactors? environmentalFactors;

  /// Predicted malaria cases
  final int? predictedCases;

  /// Historical actual cases (if available)
  final int? actualCases;

  /// Prediction date
  final DateTime predictionDate;

  /// Data freshness timestamp
  final DateTime lastUpdated;

  /// Model version used for prediction
  final String modelVersion;

  /// Additional metadata
  final Map<String, dynamic> metadata;

  const RiskData({
    required this.id,
    required this.region,
    required this.regionName,
    required this.administrativeLevel,
    required this.coordinates,
    this.boundary,
    required this.riskScore,
    required this.riskLevel,
    required this.confidence,
    this.environmentalFactors,
    this.predictedCases,
    this.actualCases,
    required this.predictionDate,
    required this.lastUpdated,
    required this.modelVersion,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [
        id,
        region,
        regionName,
        administrativeLevel,
        coordinates,
        boundary,
        riskScore,
        riskLevel,
        confidence,
        environmentalFactors,
        predictedCases,
        actualCases,
        predictionDate,
        lastUpdated,
        modelVersion,
        metadata,
      ];

  /// Create a copy with updated values
  RiskData copyWith({
    String? id,
    String? region,
    String? regionName,
    String? administrativeLevel,
    LatLng? coordinates,
    GeographicBoundary? boundary,
    double? riskScore,
    RiskLevel? riskLevel,
    double? confidence,
    EnvironmentalFactors? environmentalFactors,
    int? predictedCases,
    int? actualCases,
    DateTime? predictionDate,
    DateTime? lastUpdated,
    String? modelVersion,
    Map<String, dynamic>? metadata,
  }) {
    return RiskData(
      id: id ?? this.id,
      region: region ?? this.region,
      regionName: regionName ?? this.regionName,
      administrativeLevel: administrativeLevel ?? this.administrativeLevel,
      coordinates: coordinates ?? this.coordinates,
      boundary: boundary ?? this.boundary,
      riskScore: riskScore ?? this.riskScore,
      riskLevel: riskLevel ?? this.riskLevel,
      confidence: confidence ?? this.confidence,
      environmentalFactors: environmentalFactors ?? this.environmentalFactors,
      predictedCases: predictedCases ?? this.predictedCases,
      actualCases: actualCases ?? this.actualCases,
      predictionDate: predictionDate ?? this.predictionDate,
      lastUpdated: lastUpdated ?? this.lastUpdated,
      modelVersion: modelVersion ?? this.modelVersion,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Check if risk data is stale (older than threshold)
  bool isStale({Duration threshold = const Duration(hours: 24)}) {
    return DateTime.now().difference(lastUpdated) > threshold;
  }

  /// Check if confidence is acceptable
  bool get hasAcceptableConfidence => confidence >= 0.7;

  /// Get risk trend indicator (requires historical data)
  String get trendDescription {
    if (actualCases != null && predictedCases != null) {
      final diff = predictedCases! - actualCases!;
      if (diff > 0) return 'Increasing';
      if (diff < 0) return 'Decreasing';
    }
    return 'Stable';
  }

  /// Create from JSON map
  factory RiskData.fromJson(Map<String, dynamic> json) {
    final riskScore = (json['risk_score'] as num?)?.toDouble() ?? 0.0;

    return RiskData(
      id: json['id'] as String? ?? '',
      region: json['region'] as String? ?? '',
      regionName: json['region_name'] as String? ?? '',
      administrativeLevel: json['administrative_level'] as String? ?? 'constituency',
      coordinates: LatLng(
        (json['latitude'] as num?)?.toDouble() ?? 0.0,
        (json['longitude'] as num?)?.toDouble() ?? 0.0,
      ),
      boundary: json['boundary'] != null
          ? _parseBoundary(json['boundary'] as Map<String, dynamic>)
          : null,
      riskScore: riskScore,
      riskLevel: RiskLevel.fromScore(riskScore),
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      environmentalFactors: json['environmental_factors'] != null
          ? EnvironmentalFactors.fromMap(
              json['environmental_factors'] as Map<String, dynamic>)
          : null,
      predictedCases: json['predicted_cases'] as int?,
      actualCases: json['actual_cases'] as int?,
      predictionDate: json['prediction_date'] != null
          ? DateTime.parse(json['prediction_date'] as String)
          : DateTime.now(),
      lastUpdated: json['last_updated'] != null
          ? DateTime.parse(json['last_updated'] as String)
          : DateTime.now(),
      modelVersion: json['model_version'] as String? ?? 'unknown',
      metadata: json['metadata'] as Map<String, dynamic>? ?? {},
    );
  }

  /// Convert to JSON map
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'region': region,
      'region_name': regionName,
      'administrative_level': administrativeLevel,
      'latitude': coordinates.latitude,
      'longitude': coordinates.longitude,
      'risk_score': riskScore,
      'risk_level': riskLevel.name,
      'confidence': confidence,
      if (environmentalFactors != null)
        'environmental_factors': environmentalFactors!.toMap(),
      if (predictedCases != null) 'predicted_cases': predictedCases,
      if (actualCases != null) 'actual_cases': actualCases,
      'prediction_date': predictionDate.toIso8601String(),
      'last_updated': lastUpdated.toIso8601String(),
      'model_version': modelVersion,
      'metadata': metadata,
    };
  }

  static GeographicBoundary? _parseBoundary(Map<String, dynamic> json) {
    final coords = json['coordinates'] as List<dynamic>?;
    if (coords == null || coords.isEmpty) return null;

    final latLngs = coords
        .map((c) => LatLng(
              (c['lat'] as num?)?.toDouble() ?? 0.0,
              (c['lng'] as num?)?.toDouble() ?? 0.0,
            ))
        .toList();

    return GeographicBoundary(
      coordinates: latLngs,
      center: LatLng(
        (json['center_lat'] as num?)?.toDouble() ?? 0.0,
        (json['center_lng'] as num?)?.toDouble() ?? 0.0,
      ),
      areaKm2: (json['area_km2'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

/// Geographic subscription for real-time updates
class GeographicSubscription extends Equatable {
  /// Unique subscription identifier
  final String id;

  /// Center point of subscription area
  final LatLng center;

  /// Radius in kilometers
  final double radiusKm;

  /// Zoom level for detail filtering
  final int? zoomLevel;

  /// Whether to include prediction updates
  final bool includePredictions;

  const GeographicSubscription({
    required this.id,
    required this.center,
    required this.radiusKm,
    this.zoomLevel,
    this.includePredictions = true,
  });

  @override
  List<Object?> get props => [id, center, radiusKm, zoomLevel, includePredictions];
}

/// Extensions for RiskData list operations
extension RiskDataListExtension on List<RiskData> {
  /// Filter by risk level
  List<RiskData> filterByRiskLevel(RiskLevel level) {
    return where((data) => data.riskLevel == level).toList();
  }

  /// Filter by minimum risk score
  List<RiskData> filterByMinRiskScore(double minScore) {
    return where((data) => data.riskScore >= minScore).toList();
  }

  /// Sort by risk score descending
  List<RiskData> sortByRiskScore() {
    final sorted = List<RiskData>.from(this);
    sorted.sort((a, b) => b.riskScore.compareTo(a.riskScore));
    return sorted;
  }

  /// Get risk data within geographic bounds
  List<RiskData> withinBounds(GeographicBounds bounds) {
    return where((data) => bounds.contains(data.coordinates)).toList();
  }

  /// Get count by risk level
  Map<RiskLevel, int> get countByRiskLevel {
    final counts = <RiskLevel, int>{};
    for (final level in RiskLevel.values) {
      counts[level] = where((data) => data.riskLevel == level).length;
    }
    return counts;
  }

  /// Get average risk score
  double get averageRiskScore {
    if (isEmpty) return 0.0;
    return fold<double>(0.0, (sum, data) => sum + data.riskScore) / length;
  }
}
