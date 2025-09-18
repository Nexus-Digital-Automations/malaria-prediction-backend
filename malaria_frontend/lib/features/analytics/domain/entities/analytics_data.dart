/// Analytics data entity for malaria prediction analytics dashboard
///
/// This entity represents the core analytics data structure for visualizing
/// malaria prediction accuracy metrics, environmental trends, and risk assessments.
///
/// Usage:
/// ```dart
/// final analytics = AnalyticsData(
///   id: 'analytics_001',
///   region: 'Kenya',
///   dateRange: DateRange(start: DateTime.now().subtract(Duration(days: 30)), end: DateTime.now()),
///   predictionAccuracy: PredictionAccuracy(overall: 0.85, byRiskLevel: {...}),
///   environmentalTrends: [...],
///   riskTrends: [...],
/// );
/// ```

import 'package:equatable/equatable.dart';

/// Core analytics data entity representing comprehensive analytics information
class AnalyticsData extends Equatable {
  /// Unique identifier for this analytics dataset
  final String id;

  /// Geographic region for the analytics data
  final String region;

  /// Date range for the analytics data period
  final DateRange dateRange;

  /// Prediction accuracy metrics for model performance
  final PredictionAccuracy predictionAccuracy;

  /// Environmental trend data points for climate visualization
  final List<EnvironmentalTrend> environmentalTrends;

  /// Risk trend data points for malaria risk visualization
  final List<RiskTrend> riskTrends;

  /// Alert statistics for notification system performance
  final AlertStatistics alertStatistics;

  /// Data source quality metrics for reliability assessment
  final DataQuality dataQuality;

  /// Timestamp when this analytics data was generated
  final DateTime generatedAt;

  const AnalyticsData({
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

  /// Creates a copy of this analytics data with updated values
  AnalyticsData copyWith({
    String? id,
    String? region,
    DateRange? dateRange,
    PredictionAccuracy? predictionAccuracy,
    List<EnvironmentalTrend>? environmentalTrends,
    List<RiskTrend>? riskTrends,
    AlertStatistics? alertStatistics,
    DataQuality? dataQuality,
    DateTime? generatedAt,
  }) {
    return AnalyticsData(
      id: id ?? this.id,
      region: region ?? this.region,
      dateRange: dateRange ?? this.dateRange,
      predictionAccuracy: predictionAccuracy ?? this.predictionAccuracy,
      environmentalTrends: environmentalTrends ?? this.environmentalTrends,
      riskTrends: riskTrends ?? this.riskTrends,
      alertStatistics: alertStatistics ?? this.alertStatistics,
      dataQuality: dataQuality ?? this.dataQuality,
      generatedAt: generatedAt ?? this.generatedAt,
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

/// Date range entity for specifying analytics time periods
class DateRange extends Equatable {
  /// Start date of the analytics period
  final DateTime start;

  /// End date of the analytics period
  final DateTime end;

  const DateRange({
    required this.start,
    required this.end,
  });

  /// Duration of this date range
  Duration get duration => end.difference(start);

  /// Whether this date range contains the specified date
  bool contains(DateTime date) {
    return date.isAfter(start) && date.isBefore(end) ||
           date.isAtSameMomentAs(start) ||
           date.isAtSameMomentAs(end);
  }

  @override
  List<Object?> get props => [start, end];
}

/// Prediction accuracy metrics entity for model performance visualization
class PredictionAccuracy extends Equatable {
  /// Overall prediction accuracy as a percentage (0.0 to 1.0)
  final double overall;

  /// Accuracy breakdown by risk level (low, medium, high, critical)
  final Map<String, double> byRiskLevel;

  /// Accuracy trend over time
  final List<AccuracyDataPoint> trend;

  /// Precision metrics for prediction quality
  final double precision;

  /// Recall metrics for prediction completeness
  final double recall;

  /// F1 score for balanced prediction performance
  final double f1Score;

  const PredictionAccuracy({
    required this.overall,
    required this.byRiskLevel,
    required this.trend,
    required this.precision,
    required this.recall,
    required this.f1Score,
  });

  @override
  List<Object?> get props => [overall, byRiskLevel, trend, precision, recall, f1Score];
}

/// Environmental trend data point for climate visualization
class EnvironmentalTrend extends Equatable {
  /// Date of the environmental measurement
  final DateTime date;

  /// Environmental factor type (temperature, rainfall, vegetation, humidity)
  final EnvironmentalFactor factor;

  /// Measured value for the environmental factor
  final double value;

  /// Geographic coordinates where measurement was taken
  final Coordinates coordinates;

  /// Quality score of the measurement (0.0 to 1.0)
  final double quality;

  const EnvironmentalTrend({
    required this.date,
    required this.factor,
    required this.value,
    required this.coordinates,
    required this.quality,
  });

  @override
  List<Object?> get props => [date, factor, value, coordinates, quality];
}

/// Risk trend data point for malaria risk visualization
class RiskTrend extends Equatable {
  /// Date of the risk assessment
  final DateTime date;

  /// Risk score (0.0 to 1.0, where 1.0 is highest risk)
  final double riskScore;

  /// Risk level category (low, medium, high, critical)
  final RiskLevel riskLevel;

  /// Geographic coordinates for the risk assessment
  final Coordinates coordinates;

  /// Population at risk in the assessed area
  final int populationAtRisk;

  /// Confidence level of the risk prediction (0.0 to 1.0)
  final double confidence;

  const RiskTrend({
    required this.date,
    required this.riskScore,
    required this.riskLevel,
    required this.coordinates,
    required this.populationAtRisk,
    required this.confidence,
  });

  @override
  List<Object?> get props => [date, riskScore, riskLevel, coordinates, populationAtRisk, confidence];
}

/// Alert statistics for notification system performance
class AlertStatistics extends Equatable {
  /// Total number of alerts sent in the analytics period
  final int totalAlerts;

  /// Number of alerts by severity level
  final Map<AlertSeverity, int> alertsBySeverity;

  /// Alert delivery success rate (0.0 to 1.0)
  final double deliveryRate;

  /// Average time from risk detection to alert delivery
  final Duration averageResponseTime;

  /// Number of false positive alerts
  final int falsePositives;

  /// Number of missed critical alerts
  final int missedAlerts;

  const AlertStatistics({
    required this.totalAlerts,
    required this.alertsBySeverity,
    required this.deliveryRate,
    required this.averageResponseTime,
    required this.falsePositives,
    required this.missedAlerts,
  });

  @override
  List<Object?> get props => [
        totalAlerts,
        alertsBySeverity,
        deliveryRate,
        averageResponseTime,
        falsePositives,
        missedAlerts,
      ];
}

/// Data quality metrics for reliability assessment
class DataQuality extends Equatable {
  /// Overall data completeness percentage (0.0 to 1.0)
  final double completeness;

  /// Data accuracy percentage based on validation checks (0.0 to 1.0)
  final double accuracy;

  /// Data freshness - average age of data in hours
  final double freshnessHours;

  /// Number of data sources contributing to analytics
  final int sourcesCount;

  /// Data sources with quality issues
  final List<String> sourcesWithIssues;

  /// Last successful data update timestamp
  final DateTime lastUpdate;

  const DataQuality({
    required this.completeness,
    required this.accuracy,
    required this.freshnessHours,
    required this.sourcesCount,
    required this.sourcesWithIssues,
    required this.lastUpdate,
  });

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

/// Accuracy data point for trend visualization
class AccuracyDataPoint extends Equatable {
  /// Date of the accuracy measurement
  final DateTime date;

  /// Accuracy value (0.0 to 1.0)
  final double accuracy;

  /// Number of predictions evaluated
  final int sampleSize;

  const AccuracyDataPoint({
    required this.date,
    required this.accuracy,
    required this.sampleSize,
  });

  @override
  List<Object?> get props => [date, accuracy, sampleSize];
}

/// Geographic coordinates entity
class Coordinates extends Equatable {
  /// Latitude coordinate
  final double latitude;

  /// Longitude coordinate
  final double longitude;

  const Coordinates({
    required this.latitude,
    required this.longitude,
  });

  @override
  List<Object?> get props => [latitude, longitude];
}

/// Environmental factor enumeration
enum EnvironmentalFactor {
  temperature,
  rainfall,
  vegetation,
  humidity,
  windSpeed,
  pressure,
}

/// Risk level enumeration
enum RiskLevel {
  low,
  medium,
  high,
  critical,
}

/// Alert severity enumeration
enum AlertSeverity {
  info,
  warning,
  high,
  critical,
  emergency,
}