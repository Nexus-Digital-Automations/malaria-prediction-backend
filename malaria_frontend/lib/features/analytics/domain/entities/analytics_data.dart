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
library;

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

/// Comprehensive environmental data entity for detailed climate analysis
class EnvironmentalData extends Equatable {
  /// Unique identifier for this environmental dataset
  final String id;

  /// Geographic region for the environmental data
  final String region;

  /// Date range for the environmental data period
  final DateRange dateRange;

  /// Temperature measurements and patterns
  final TemperatureData temperature;

  /// Humidity measurements and patterns
  final HumidityData humidity;

  /// Rainfall measurements and patterns
  final RainfallData rainfall;

  /// Vegetation index measurements and patterns
  final VegetationData vegetation;

  /// Geographic coordinates for this environmental data
  final Coordinates coordinates;

  /// Data quality metrics for this environmental dataset
  final double dataQuality;

  /// Timestamp when this environmental data was last updated
  final DateTime lastUpdated;

  const EnvironmentalData({
    required this.id,
    required this.region,
    required this.dateRange,
    required this.temperature,
    required this.humidity,
    required this.rainfall,
    required this.vegetation,
    required this.coordinates,
    required this.dataQuality,
    required this.lastUpdated,
  });

  @override
  List<Object?> get props => [
        id,
        region,
        dateRange,
        temperature,
        humidity,
        rainfall,
        vegetation,
        coordinates,
        dataQuality,
        lastUpdated,
      ];
}

/// Temperature data entity for comprehensive temperature analysis
class TemperatureData extends Equatable {
  /// Daily mean temperature measurements
  final List<TemperatureMeasurement> dailyMean;

  /// Daily minimum temperature measurements
  final List<TemperatureMeasurement> dailyMin;

  /// Daily maximum temperature measurements
  final List<TemperatureMeasurement> dailyMax;

  /// Diurnal temperature range (day-night variation)
  final List<TemperatureMeasurement> diurnalRange;

  /// Temperature anomalies from historical norms
  final List<TemperatureAnomaly> anomalies;

  /// Seasonal temperature patterns
  final SeasonalPattern seasonalPattern;

  const TemperatureData({
    required this.dailyMean,
    required this.dailyMin,
    required this.dailyMax,
    required this.diurnalRange,
    required this.anomalies,
    required this.seasonalPattern,
  });

  @override
  List<Object?> get props => [
        dailyMean,
        dailyMin,
        dailyMax,
        diurnalRange,
        anomalies,
        seasonalPattern,
      ];
}

/// Individual temperature measurement
class TemperatureMeasurement extends Equatable {
  /// Date of the temperature measurement
  final DateTime date;

  /// Temperature value in Celsius
  final double temperature;

  /// Measurement quality score (0.0 to 1.0)
  final double quality;

  /// Data source for this measurement
  final String source;

  const TemperatureMeasurement({
    required this.date,
    required this.temperature,
    required this.quality,
    required this.source,
  });

  @override
  List<Object?> get props => [date, temperature, quality, source];
}

/// Temperature anomaly from historical norms
class TemperatureAnomaly extends Equatable {
  /// Date of the temperature anomaly
  final DateTime date;

  /// Observed temperature value
  final double observedTemperature;

  /// Historical average for this date
  final double historicalAverage;

  /// Anomaly value (observed - historical)
  final double anomaly;

  /// Significance level (standard deviations from norm)
  final double significance;

  const TemperatureAnomaly({
    required this.date,
    required this.observedTemperature,
    required this.historicalAverage,
    required this.anomaly,
    required this.significance,
  });

  @override
  List<Object?> get props => [
        date,
        observedTemperature,
        historicalAverage,
        anomaly,
        significance,
      ];
}

/// Humidity data entity for comprehensive humidity analysis
class HumidityData extends Equatable {
  /// Relative humidity measurements
  final List<HumidityMeasurement> relativeHumidity;

  /// Absolute humidity measurements
  final List<HumidityMeasurement> absoluteHumidity;

  /// Dew point measurements
  final List<HumidityMeasurement> dewPoint;

  /// Seasonal humidity patterns
  final SeasonalPattern seasonalPattern;

  const HumidityData({
    required this.relativeHumidity,
    required this.absoluteHumidity,
    required this.dewPoint,
    required this.seasonalPattern,
  });

  @override
  List<Object?> get props => [
        relativeHumidity,
        absoluteHumidity,
        dewPoint,
        seasonalPattern,
      ];
}

/// Individual humidity measurement
class HumidityMeasurement extends Equatable {
  /// Date of the humidity measurement
  final DateTime date;

  /// Humidity value (percentage for relative, g/m³ for absolute)
  final double humidity;

  /// Measurement quality score (0.0 to 1.0)
  final double quality;

  /// Data source for this measurement
  final String source;

  const HumidityMeasurement({
    required this.date,
    required this.humidity,
    required this.quality,
    required this.source,
  });

  @override
  List<Object?> get props => [date, humidity, quality, source];
}

/// Rainfall data entity for comprehensive precipitation analysis
class RainfallData extends Equatable {
  /// Daily rainfall measurements
  final List<RainfallMeasurement> daily;

  /// Monthly rainfall totals
  final List<RainfallMeasurement> monthly;

  /// Seasonal rainfall patterns
  final SeasonalPattern seasonalPattern;

  /// Extreme rainfall events
  final List<ExtremeEvent> extremeEvents;

  /// Post-rainfall periods for malaria risk assessment
  final List<PostRainfallPeriod> postRainfallPeriods;

  const RainfallData({
    required this.daily,
    required this.monthly,
    required this.seasonalPattern,
    required this.extremeEvents,
    required this.postRainfallPeriods,
  });

  @override
  List<Object?> get props => [
        daily,
        monthly,
        seasonalPattern,
        extremeEvents,
        postRainfallPeriods,
      ];
}

/// Individual rainfall measurement
class RainfallMeasurement extends Equatable {
  /// Date of the rainfall measurement
  final DateTime date;

  /// Rainfall amount in millimeters
  final double rainfall;

  /// Measurement quality score (0.0 to 1.0)
  final double quality;

  /// Data source for this measurement
  final String source;

  const RainfallMeasurement({
    required this.date,
    required this.rainfall,
    required this.quality,
    required this.source,
  });

  @override
  List<Object?> get props => [date, rainfall, quality, source];
}

/// Vegetation data entity for vegetation index analysis
class VegetationData extends Equatable {
  /// NDVI (Normalized Difference Vegetation Index) measurements
  final List<VegetationMeasurement> ndvi;

  /// EVI (Enhanced Vegetation Index) measurements
  final List<VegetationMeasurement> evi;

  /// Seasonal vegetation patterns
  final SeasonalPattern seasonalPattern;

  /// Land cover type distribution
  final Map<LandCoverType, double> landCoverDistribution;

  const VegetationData({
    required this.ndvi,
    required this.evi,
    required this.seasonalPattern,
    required this.landCoverDistribution,
  });

  @override
  List<Object?> get props => [
        ndvi,
        evi,
        seasonalPattern,
        landCoverDistribution,
      ];
}

/// Individual vegetation measurement
class VegetationMeasurement extends Equatable {
  /// Date of the vegetation measurement
  final DateTime date;

  /// Vegetation index value (typically -1.0 to 1.0)
  final double value;

  /// Measurement quality score (0.0 to 1.0)
  final double quality;

  /// Data source for this measurement
  final String source;

  const VegetationMeasurement({
    required this.date,
    required this.value,
    required this.quality,
    required this.source,
  });

  @override
  List<Object?> get props => [date, value, quality, source];
}

/// Climate metrics entity for seasonal pattern analysis
class ClimateMetrics extends Equatable {
  /// Unique identifier for this climate metrics dataset
  final String id;

  /// Geographic region for the climate metrics
  final String region;

  /// Year for the climate metrics
  final int year;

  /// Seasonal temperature statistics
  final Map<Season, SeasonalStatistics> temperatureStats;

  /// Seasonal rainfall statistics
  final Map<Season, SeasonalStatistics> rainfallStats;

  /// Seasonal humidity statistics
  final Map<Season, SeasonalStatistics> humidityStats;

  /// Temperature-rainfall correlation coefficient
  final double temperatureRainfallCorrelation;

  /// Humidity-temperature correlation coefficient
  final double humidityTemperatureCorrelation;

  /// Vegetation-rainfall correlation coefficient
  final double vegetationRainfallCorrelation;

  /// Malaria risk correlation with environmental factors
  final Map<EnvironmentalFactor, double> malariaCorrelations;

  const ClimateMetrics({
    required this.id,
    required this.region,
    required this.year,
    required this.temperatureStats,
    required this.rainfallStats,
    required this.humidityStats,
    required this.temperatureRainfallCorrelation,
    required this.humidityTemperatureCorrelation,
    required this.vegetationRainfallCorrelation,
    required this.malariaCorrelations,
  });

  @override
  List<Object?> get props => [
        id,
        region,
        year,
        temperatureStats,
        rainfallStats,
        humidityStats,
        temperatureRainfallCorrelation,
        humidityTemperatureCorrelation,
        vegetationRainfallCorrelation,
        malariaCorrelations,
      ];
}

/// Weather trend entity for historical climate analysis
class WeatherTrend extends Equatable {
  /// Unique identifier for this weather trend dataset
  final String id;

  /// Geographic region for the weather trend
  final String region;

  /// Date range for the trend analysis
  final DateRange dateRange;

  /// Long-term temperature trend (°C per year)
  final double temperatureTrend;

  /// Long-term rainfall trend (mm per year)
  final double rainfallTrend;

  /// Long-term humidity trend (% per year)
  final double humidityTrend;

  /// Temperature trend confidence level (0.0 to 1.0)
  final double temperatureTrendConfidence;

  /// Rainfall trend confidence level (0.0 to 1.0)
  final double rainfallTrendConfidence;

  /// Humidity trend confidence level (0.0 to 1.0)
  final double humidityTrendConfidence;

  /// Cyclical patterns detected in the data
  final List<CyclicalPattern> cyclicalPatterns;

  /// Climate change indicators
  final ClimateChangeIndicators climateChangeIndicators;

  const WeatherTrend({
    required this.id,
    required this.region,
    required this.dateRange,
    required this.temperatureTrend,
    required this.rainfallTrend,
    required this.humidityTrend,
    required this.temperatureTrendConfidence,
    required this.rainfallTrendConfidence,
    required this.humidityTrendConfidence,
    required this.cyclicalPatterns,
    required this.climateChangeIndicators,
  });

  @override
  List<Object?> get props => [
        id,
        region,
        dateRange,
        temperatureTrend,
        rainfallTrend,
        humidityTrend,
        temperatureTrendConfidence,
        rainfallTrendConfidence,
        humidityTrendConfidence,
        cyclicalPatterns,
        climateChangeIndicators,
      ];
}

/// Seasonal pattern entity for cyclical trend analysis
class SeasonalPattern extends Equatable {
  /// Spring season statistics
  final SeasonalStatistics spring;

  /// Summer season statistics
  final SeasonalStatistics summer;

  /// Autumn season statistics
  final SeasonalStatistics autumn;

  /// Winter season statistics
  final SeasonalStatistics winter;

  /// Peak season for this environmental factor
  final Season peakSeason;

  /// Low season for this environmental factor
  final Season lowSeason;

  const SeasonalPattern({
    required this.spring,
    required this.summer,
    required this.autumn,
    required this.winter,
    required this.peakSeason,
    required this.lowSeason,
  });

  @override
  List<Object?> get props => [spring, summer, autumn, winter, peakSeason, lowSeason];
}

/// Seasonal statistics for a specific season
class SeasonalStatistics extends Equatable {
  /// Average value for the season
  final double average;

  /// Minimum value recorded in the season
  final double minimum;

  /// Maximum value recorded in the season
  final double maximum;

  /// Standard deviation for the season
  final double standardDeviation;

  /// Number of data points for the season
  final int dataPoints;

  const SeasonalStatistics({
    required this.average,
    required this.minimum,
    required this.maximum,
    required this.standardDeviation,
    required this.dataPoints,
  });

  @override
  List<Object?> get props => [average, minimum, maximum, standardDeviation, dataPoints];
}

/// Extreme weather event entity
class ExtremeEvent extends Equatable {
  /// Date of the extreme event
  final DateTime date;

  /// Type of extreme event
  final ExtremeEventType type;

  /// Magnitude of the event
  final double magnitude;

  /// Duration of the event
  final Duration duration;

  /// Impact severity (0.0 to 1.0)
  final double severity;

  /// Geographic area affected
  final double affectedArea;

  const ExtremeEvent({
    required this.date,
    required this.type,
    required this.magnitude,
    required this.duration,
    required this.severity,
    required this.affectedArea,
  });

  @override
  List<Object?> get props => [date, type, magnitude, duration, severity, affectedArea];
}

/// Post-rainfall period for malaria risk assessment
class PostRainfallPeriod extends Equatable {
  /// Date of the rainfall event
  final DateTime rainfallDate;

  /// Amount of rainfall (mm)
  final double rainfallAmount;

  /// Peak transmission risk date (typically 1-2 months post-rainfall)
  final DateTime peakRiskDate;

  /// Risk multiplier for this period (1.0 = baseline risk)
  final double riskMultiplier;

  /// Duration of elevated risk period
  final Duration riskDuration;

  const PostRainfallPeriod({
    required this.rainfallDate,
    required this.rainfallAmount,
    required this.peakRiskDate,
    required this.riskMultiplier,
    required this.riskDuration,
  });

  @override
  List<Object?> get props => [
        rainfallDate,
        rainfallAmount,
        peakRiskDate,
        riskMultiplier,
        riskDuration,
      ];
}

/// Cyclical pattern detected in weather data
class CyclicalPattern extends Equatable {
  /// Type of cyclical pattern
  final CyclicalPatternType type;

  /// Period of the cycle (in days)
  final int periodDays;

  /// Amplitude of the cycle
  final double amplitude;

  /// Phase of the cycle (offset)
  final double phase;

  /// Confidence in pattern detection (0.0 to 1.0)
  final double confidence;

  /// Environmental factor affected by this pattern
  final EnvironmentalFactor affectedFactor;

  const CyclicalPattern({
    required this.type,
    required this.periodDays,
    required this.amplitude,
    required this.phase,
    required this.confidence,
    required this.affectedFactor,
  });

  @override
  List<Object?> get props => [type, periodDays, amplitude, phase, confidence, affectedFactor];
}

/// Climate change indicators entity
class ClimateChangeIndicators extends Equatable {
  /// Rate of temperature increase (°C per decade)
  final double temperatureIncreaseRate;

  /// Change in precipitation patterns (mm per decade)
  final double precipitationChangeRate;

  /// Increase in extreme weather frequency (events per decade)
  final double extremeWeatherIncreaseRate;

  /// Confidence in climate change detection (0.0 to 1.0)
  final double confidence;

  /// Years of data used for analysis
  final int analysisYears;

  const ClimateChangeIndicators({
    required this.temperatureIncreaseRate,
    required this.precipitationChangeRate,
    required this.extremeWeatherIncreaseRate,
    required this.confidence,
    required this.analysisYears,
  });

  @override
  List<Object?> get props => [
        temperatureIncreaseRate,
        precipitationChangeRate,
        extremeWeatherIncreaseRate,
        confidence,
        analysisYears,
      ];
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

/// Season enumeration
enum Season {
  spring,
  summer,
  autumn,
  winter,
}

/// Land cover type enumeration
enum LandCoverType {
  forest,
  grassland,
  cropland,
  urban,
  water,
  bareland,
  wetland,
}

/// Extreme event type enumeration
enum ExtremeEventType {
  drought,
  flood,
  heatwave,
  coldSnap,
  storm,
}

/// Cyclical pattern type enumeration
enum CyclicalPatternType {
  seasonal,
  annual,
  elNino,
  laNina,
  monsoon,
  other,
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