/// Analytics data model for JSON serialization and API communication
///
/// This model provides JSON serialization/deserialization for analytics data
/// transferred between the mobile app and the malaria prediction backend API.
/// It includes comprehensive analytics information for dashboard visualization.
///
/// Usage:
/// ```dart
/// // From JSON API response
/// final analyticsData = AnalyticsDataModel.fromJson(jsonResponse);
/// final entity = analyticsData.toEntity();
///
/// // To JSON for API requests
/// final json = analyticsDataModel.toJson();
/// ```
library;

import 'package:json_annotation/json_annotation.dart';
import 'package:equatable/equatable.dart';
import '../../domain/entities/analytics_data.dart';

part 'analytics_data_model.g.dart';

/// Analytics data model for JSON serialization
@JsonSerializable(explicitToJson: true)
class AnalyticsDataModel extends Equatable {
  /// Unique identifier for this analytics dataset
  @JsonKey(name: 'id')
  final String id;

  /// Geographic region for the analytics data
  @JsonKey(name: 'region')
  final String region;

  /// Date range for the analytics data period
  @JsonKey(name: 'date_range')
  final DateRangeModel dateRange;

  /// Prediction accuracy metrics for model performance
  @JsonKey(name: 'prediction_accuracy')
  final PredictionAccuracyModel predictionAccuracy;

  /// Environmental trend data points for climate visualization
  @JsonKey(name: 'environmental_trends')
  final List<EnvironmentalTrendModel> environmentalTrends;

  /// Risk trend data points for malaria risk visualization
  @JsonKey(name: 'risk_trends')
  final List<RiskTrendModel> riskTrends;

  /// Alert statistics for notification system performance
  @JsonKey(name: 'alert_statistics')
  final AlertStatisticsModel alertStatistics;

  /// Data source quality metrics for reliability assessment
  @JsonKey(name: 'data_quality')
  final DataQualityModel dataQuality;

  /// Timestamp when this analytics data was generated
  @JsonKey(name: 'generated_at')
  final DateTime generatedAt;

  const AnalyticsDataModel({
    required this.id,
    required this.region,
    required this.dateRange,
    required this.predictionAccuracy,
    required this.environmentalTrends,
    required this.riskTrends,
    required this.alertStatistics,
    required this.dataQuality,
    required this.generatedAt,
  });

  /// Creates AnalyticsDataModel from JSON map
  factory AnalyticsDataModel.fromJson(Map<String, dynamic> json) =>
      _$AnalyticsDataModelFromJson(json);

  /// Converts AnalyticsDataModel to JSON map
  Map<String, dynamic> toJson() => _$AnalyticsDataModelToJson(this);

  /// Converts model to domain entity
  AnalyticsData toEntity() {
    return AnalyticsData(
      id: id,
      region: region,
      dateRange: dateRange.toEntity(),
      predictionAccuracy: predictionAccuracy.toEntity(),
      environmentalTrends: environmentalTrends.map((trend) => trend.toEntity()).toList(),
      riskTrends: riskTrends.map((trend) => trend.toEntity()).toList(),
      alertStatistics: alertStatistics.toEntity(),
      dataQuality: dataQuality.toEntity(),
      generatedAt: generatedAt,
    );
  }

  /// Creates model from domain entity
  factory AnalyticsDataModel.fromEntity(AnalyticsData entity) {
    return AnalyticsDataModel(
      id: entity.id,
      region: entity.region,
      dateRange: DateRangeModel.fromEntity(entity.dateRange),
      predictionAccuracy: PredictionAccuracyModel.fromEntity(entity.predictionAccuracy),
      environmentalTrends: entity.environmentalTrends
          .map((trend) => EnvironmentalTrendModel.fromEntity(trend))
          .toList(),
      riskTrends: entity.riskTrends
          .map((trend) => RiskTrendModel.fromEntity(trend))
          .toList(),
      alertStatistics: AlertStatisticsModel.fromEntity(entity.alertStatistics),
      dataQuality: DataQualityModel.fromEntity(entity.dataQuality),
      generatedAt: entity.generatedAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        region,
        dateRange,
        predictionAccuracy,
        environmentalTrends,
        riskTrends,
        alertStatistics,
        dataQuality,
        generatedAt,
      ];
}

/// Date range model for JSON serialization
@JsonSerializable()
class DateRangeModel extends Equatable {
  /// Start date of the analytics period
  @JsonKey(name: 'start')
  final DateTime start;

  /// End date of the analytics period
  @JsonKey(name: 'end')
  final DateTime end;

  const DateRangeModel({
    required this.start,
    required this.end,
  });

  factory DateRangeModel.fromJson(Map<String, dynamic> json) =>
      _$DateRangeModelFromJson(json);

  Map<String, dynamic> toJson() => _$DateRangeModelToJson(this);

  DateRange toEntity() => DateRange(start: start, end: end);

  factory DateRangeModel.fromEntity(DateRange entity) {
    return DateRangeModel(start: entity.start, end: entity.end);
  }

  @override
  List<Object?> get props => [start, end];
}

/// Prediction accuracy model for JSON serialization
@JsonSerializable()
class PredictionAccuracyModel extends Equatable {
  /// Overall prediction accuracy as a percentage (0.0 to 1.0)
  @JsonKey(name: 'overall')
  final double overall;

  /// Accuracy breakdown by risk level
  @JsonKey(name: 'by_risk_level')
  final Map<String, double> byRiskLevel;

  /// Accuracy trend over time
  @JsonKey(name: 'trend')
  final List<AccuracyDataPointModel> trend;

  /// Precision metrics for prediction quality
  @JsonKey(name: 'precision')
  final double precision;

  /// Recall metrics for prediction completeness
  @JsonKey(name: 'recall')
  final double recall;

  /// F1 score for balanced prediction performance
  @JsonKey(name: 'f1_score')
  final double f1Score;

  const PredictionAccuracyModel({
    required this.overall,
    required this.byRiskLevel,
    required this.trend,
    required this.precision,
    required this.recall,
    required this.f1Score,
  });

  factory PredictionAccuracyModel.fromJson(Map<String, dynamic> json) =>
      _$PredictionAccuracyModelFromJson(json);

  Map<String, dynamic> toJson() => _$PredictionAccuracyModelToJson(this);

  PredictionAccuracy toEntity() {
    return PredictionAccuracy(
      overall: overall,
      byRiskLevel: byRiskLevel,
      trend: trend.map((point) => point.toEntity()).toList(),
      precision: precision,
      recall: recall,
      f1Score: f1Score,
    );
  }

  factory PredictionAccuracyModel.fromEntity(PredictionAccuracy entity) {
    return PredictionAccuracyModel(
      overall: entity.overall,
      byRiskLevel: entity.byRiskLevel,
      trend: entity.trend.map((point) => AccuracyDataPointModel.fromEntity(point)).toList(),
      precision: entity.precision,
      recall: entity.recall,
      f1Score: entity.f1Score,
    );
  }

  @override
  List<Object?> get props => [overall, byRiskLevel, trend, precision, recall, f1Score];
}

/// Environmental trend model for JSON serialization
@JsonSerializable()
class EnvironmentalTrendModel extends Equatable {
  /// Date of the environmental measurement
  @JsonKey(name: 'date')
  final DateTime date;

  /// Environmental factor type
  @JsonKey(name: 'factor')
  final String factor;

  /// Measured value for the environmental factor
  @JsonKey(name: 'value')
  final double value;

  /// Geographic coordinates where measurement was taken
  @JsonKey(name: 'coordinates')
  final CoordinatesModel coordinates;

  /// Quality score of the measurement (0.0 to 1.0)
  @JsonKey(name: 'quality')
  final double quality;

  const EnvironmentalTrendModel({
    required this.date,
    required this.factor,
    required this.value,
    required this.coordinates,
    required this.quality,
  });

  factory EnvironmentalTrendModel.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentalTrendModelFromJson(json);

  Map<String, dynamic> toJson() => _$EnvironmentalTrendModelToJson(this);

  EnvironmentalTrend toEntity() {
    return EnvironmentalTrend(
      date: date,
      factor: _parseEnvironmentalFactor(factor),
      value: value,
      coordinates: coordinates.toEntity(),
      quality: quality,
    );
  }

  factory EnvironmentalTrendModel.fromEntity(EnvironmentalTrend entity) {
    return EnvironmentalTrendModel(
      date: entity.date,
      factor: entity.factor.name,
      value: entity.value,
      coordinates: CoordinatesModel.fromEntity(entity.coordinates),
      quality: entity.quality,
    );
  }

  EnvironmentalFactor _parseEnvironmentalFactor(String factor) {
    switch (factor.toLowerCase()) {
      case 'temperature':
        return EnvironmentalFactor.temperature;
      case 'rainfall':
        return EnvironmentalFactor.rainfall;
      case 'vegetation':
        return EnvironmentalFactor.vegetation;
      case 'humidity':
        return EnvironmentalFactor.humidity;
      case 'windspeed':
      case 'wind_speed':
        return EnvironmentalFactor.windSpeed;
      case 'pressure':
        return EnvironmentalFactor.pressure;
      default:
        return EnvironmentalFactor.temperature;
    }
  }

  @override
  List<Object?> get props => [date, factor, value, coordinates, quality];
}

/// Risk trend model for JSON serialization
@JsonSerializable()
class RiskTrendModel extends Equatable {
  /// Date of the risk assessment
  @JsonKey(name: 'date')
  final DateTime date;

  /// Risk score (0.0 to 1.0)
  @JsonKey(name: 'risk_score')
  final double riskScore;

  /// Risk level category
  @JsonKey(name: 'risk_level')
  final String riskLevel;

  /// Geographic coordinates for the risk assessment
  @JsonKey(name: 'coordinates')
  final CoordinatesModel coordinates;

  /// Population at risk in the assessed area
  @JsonKey(name: 'population_at_risk')
  final int populationAtRisk;

  /// Confidence level of the risk prediction
  @JsonKey(name: 'confidence')
  final double confidence;

  const RiskTrendModel({
    required this.date,
    required this.riskScore,
    required this.riskLevel,
    required this.coordinates,
    required this.populationAtRisk,
    required this.confidence,
  });

  factory RiskTrendModel.fromJson(Map<String, dynamic> json) =>
      _$RiskTrendModelFromJson(json);

  Map<String, dynamic> toJson() => _$RiskTrendModelToJson(this);

  RiskTrend toEntity() {
    return RiskTrend(
      date: date,
      riskScore: riskScore,
      riskLevel: _parseRiskLevel(riskLevel),
      coordinates: coordinates.toEntity(),
      populationAtRisk: populationAtRisk,
      confidence: confidence,
    );
  }

  factory RiskTrendModel.fromEntity(RiskTrend entity) {
    return RiskTrendModel(
      date: entity.date,
      riskScore: entity.riskScore,
      riskLevel: entity.riskLevel.name,
      coordinates: CoordinatesModel.fromEntity(entity.coordinates),
      populationAtRisk: entity.populationAtRisk,
      confidence: entity.confidence,
    );
  }

  RiskLevel _parseRiskLevel(String level) {
    switch (level.toLowerCase()) {
      case 'low':
        return RiskLevel.low;
      case 'medium':
        return RiskLevel.medium;
      case 'high':
        return RiskLevel.high;
      case 'critical':
        return RiskLevel.critical;
      default:
        return RiskLevel.low;
    }
  }

  @override
  List<Object?> get props => [date, riskScore, riskLevel, coordinates, populationAtRisk, confidence];
}

/// Alert statistics model for JSON serialization
@JsonSerializable()
class AlertStatisticsModel extends Equatable {
  /// Total number of alerts sent
  @JsonKey(name: 'total_alerts')
  final int totalAlerts;

  /// Number of alerts by severity level
  @JsonKey(name: 'alerts_by_severity')
  final Map<String, int> alertsBySeverity;

  /// Alert delivery success rate
  @JsonKey(name: 'delivery_rate')
  final double deliveryRate;

  /// Average response time in seconds
  @JsonKey(name: 'average_response_time_seconds')
  final int averageResponseTimeSeconds;

  /// Number of false positive alerts
  @JsonKey(name: 'false_positives')
  final int falsePositives;

  /// Number of missed critical alerts
  @JsonKey(name: 'missed_alerts')
  final int missedAlerts;

  const AlertStatisticsModel({
    required this.totalAlerts,
    required this.alertsBySeverity,
    required this.deliveryRate,
    required this.averageResponseTimeSeconds,
    required this.falsePositives,
    required this.missedAlerts,
  });

  factory AlertStatisticsModel.fromJson(Map<String, dynamic> json) =>
      _$AlertStatisticsModelFromJson(json);

  Map<String, dynamic> toJson() => _$AlertStatisticsModelToJson(this);

  AlertStatistics toEntity() {
    final severityMap = <AlertSeverity, int>{};
    for (final entry in alertsBySeverity.entries) {
      final severity = _parseAlertSeverity(entry.key);
      severityMap[severity] = entry.value;
    }

    return AlertStatistics(
      totalAlerts: totalAlerts,
      alertsBySeverity: severityMap,
      deliveryRate: deliveryRate,
      averageResponseTime: Duration(seconds: averageResponseTimeSeconds),
      falsePositives: falsePositives,
      missedAlerts: missedAlerts,
    );
  }

  factory AlertStatisticsModel.fromEntity(AlertStatistics entity) {
    final severityMap = <String, int>{};
    for (final entry in entity.alertsBySeverity.entries) {
      severityMap[entry.key.name] = entry.value;
    }

    return AlertStatisticsModel(
      totalAlerts: entity.totalAlerts,
      alertsBySeverity: severityMap,
      deliveryRate: entity.deliveryRate,
      averageResponseTimeSeconds: entity.averageResponseTime.inSeconds,
      falsePositives: entity.falsePositives,
      missedAlerts: entity.missedAlerts,
    );
  }

  AlertSeverity _parseAlertSeverity(String severity) {
    switch (severity.toLowerCase()) {
      case 'info':
        return AlertSeverity.info;
      case 'warning':
        return AlertSeverity.warning;
      case 'high':
        return AlertSeverity.high;
      case 'critical':
        return AlertSeverity.critical;
      case 'emergency':
        return AlertSeverity.emergency;
      default:
        return AlertSeverity.info;
    }
  }

  @override
  List<Object?> get props => [
        totalAlerts,
        alertsBySeverity,
        deliveryRate,
        averageResponseTimeSeconds,
        falsePositives,
        missedAlerts,
      ];
}

/// Data quality model for JSON serialization
@JsonSerializable()
class DataQualityModel extends Equatable {
  /// Overall data completeness percentage
  @JsonKey(name: 'completeness')
  final double completeness;

  /// Data accuracy percentage
  @JsonKey(name: 'accuracy')
  final double accuracy;

  /// Data freshness in hours
  @JsonKey(name: 'freshness_hours')
  final double freshnessHours;

  /// Number of contributing data sources
  @JsonKey(name: 'sources_count')
  final int sourcesCount;

  /// Data sources with quality issues
  @JsonKey(name: 'sources_with_issues')
  final List<String> sourcesWithIssues;

  /// Last successful data update
  @JsonKey(name: 'last_update')
  final DateTime lastUpdate;

  const DataQualityModel({
    required this.completeness,
    required this.accuracy,
    required this.freshnessHours,
    required this.sourcesCount,
    required this.sourcesWithIssues,
    required this.lastUpdate,
  });

  factory DataQualityModel.fromJson(Map<String, dynamic> json) =>
      _$DataQualityModelFromJson(json);

  Map<String, dynamic> toJson() => _$DataQualityModelToJson(this);

  DataQuality toEntity() {
    return DataQuality(
      completeness: completeness,
      accuracy: accuracy,
      freshnessHours: freshnessHours,
      sourcesCount: sourcesCount,
      sourcesWithIssues: sourcesWithIssues,
      lastUpdate: lastUpdate,
    );
  }

  factory DataQualityModel.fromEntity(DataQuality entity) {
    return DataQualityModel(
      completeness: entity.completeness,
      accuracy: entity.accuracy,
      freshnessHours: entity.freshnessHours,
      sourcesCount: entity.sourcesCount,
      sourcesWithIssues: entity.sourcesWithIssues,
      lastUpdate: entity.lastUpdate,
    );
  }

  @override
  List<Object?> get props => [
        completeness,
        accuracy,
        freshnessHours,
        sourcesCount,
        sourcesWithIssues,
        lastUpdate,
      ];
}

/// Accuracy data point model for JSON serialization
@JsonSerializable()
class AccuracyDataPointModel extends Equatable {
  /// Date of the accuracy measurement
  @JsonKey(name: 'date')
  final DateTime date;

  /// Accuracy value (0.0 to 1.0)
  @JsonKey(name: 'accuracy')
  final double accuracy;

  /// Number of predictions evaluated
  @JsonKey(name: 'sample_size')
  final int sampleSize;

  const AccuracyDataPointModel({
    required this.date,
    required this.accuracy,
    required this.sampleSize,
  });

  factory AccuracyDataPointModel.fromJson(Map<String, dynamic> json) =>
      _$AccuracyDataPointModelFromJson(json);

  Map<String, dynamic> toJson() => _$AccuracyDataPointModelToJson(this);

  AccuracyDataPoint toEntity() {
    return AccuracyDataPoint(
      date: date,
      accuracy: accuracy,
      sampleSize: sampleSize,
    );
  }

  factory AccuracyDataPointModel.fromEntity(AccuracyDataPoint entity) {
    return AccuracyDataPointModel(
      date: entity.date,
      accuracy: entity.accuracy,
      sampleSize: entity.sampleSize,
    );
  }

  @override
  List<Object?> get props => [date, accuracy, sampleSize];
}

/// Coordinates model for JSON serialization
@JsonSerializable()
class CoordinatesModel extends Equatable {
  /// Latitude coordinate
  @JsonKey(name: 'latitude')
  final double latitude;

  /// Longitude coordinate
  @JsonKey(name: 'longitude')
  final double longitude;

  const CoordinatesModel({
    required this.latitude,
    required this.longitude,
  });

  factory CoordinatesModel.fromJson(Map<String, dynamic> json) =>
      _$CoordinatesModelFromJson(json);

  Map<String, dynamic> toJson() => _$CoordinatesModelToJson(this);

  Coordinates toEntity() => Coordinates(latitude: latitude, longitude: longitude);

  factory CoordinatesModel.fromEntity(Coordinates entity) {
    return CoordinatesModel(latitude: entity.latitude, longitude: entity.longitude);
  }

  @override
  List<Object?> get props => [latitude, longitude];
}