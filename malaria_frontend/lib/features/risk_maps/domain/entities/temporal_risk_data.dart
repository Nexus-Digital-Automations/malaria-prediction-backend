/// Temporal Risk Data Entity for Time-based Risk Visualization
///
/// This entity represents risk data across different time periods, enabling
/// temporal analysis and visualization of malaria risk patterns over time.
/// It supports time-series analysis, trend visualization, and predictive
/// modeling display with smooth temporal transitions.
///
/// Features:
/// - Time-series risk data with configurable intervals
/// - Temporal interpolation for smooth animations
/// - Historical trend analysis and future predictions
/// - Seasonal pattern recognition and display
/// - Data aggregation across multiple time scales
/// - Performance-optimized data structures
/// - Animation-friendly temporal transitions
///
/// Author: Claude AI Agent - Real-time Visualization System
/// Created: 2025-09-19
library;

import 'package:latlong2/latlong.dart';
import 'package:equatable/equatable.dart';
import 'risk_data.dart';

/// Time interval types for temporal data aggregation
enum TimeInterval {
  /// Hourly data points
  hourly,

  /// Daily data points
  daily,

  /// Weekly data points
  weekly,

  /// Monthly data points
  monthly,

  /// Seasonal data points (quarterly)
  seasonal,

  /// Yearly data points
  yearly,

  /// Custom interval defined by duration
  custom,
}

/// Temporal data point representing risk at a specific time
class TemporalDataPoint extends Equatable {
  /// Timestamp for this data point
  final DateTime timestamp;

  /// Risk score at this time
  final double riskScore;

  /// Confidence level (0.0 to 1.0)
  final double confidence;

  /// Actual reported cases (if available)
  final int? actualCases;

  /// Predicted cases
  final int? predictedCases;

  /// Environmental factors at this time
  final Map<String, double> environmentalFactors;

  /// Whether this is historical data or prediction
  final bool isPrediction;

  /// Data quality score (0.0 to 1.0)
  final double dataQuality;

  /// Additional metadata for this time point
  final Map<String, dynamic> metadata;

  const TemporalDataPoint({
    required this.timestamp,
    required this.riskScore,
    required this.confidence,
    this.actualCases,
    this.predictedCases,
    this.environmentalFactors = const {},
    this.isPrediction = false,
    this.dataQuality = 1.0,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [
        timestamp,
        riskScore,
        confidence,
        actualCases,
        predictedCases,
        environmentalFactors,
        isPrediction,
        dataQuality,
        metadata,
      ];

  /// Create a copy with updated values
  TemporalDataPoint copyWith({
    DateTime? timestamp,
    double? riskScore,
    double? confidence,
    int? actualCases,
    int? predictedCases,
    Map<String, double>? environmentalFactors,
    bool? isPrediction,
    double? dataQuality,
    Map<String, dynamic>? metadata,
  }) {
    return TemporalDataPoint(
      timestamp: timestamp ?? this.timestamp,
      riskScore: riskScore ?? this.riskScore,
      confidence: confidence ?? this.confidence,
      actualCases: actualCases ?? this.actualCases,
      predictedCases: predictedCases ?? this.predictedCases,
      environmentalFactors: environmentalFactors ?? this.environmentalFactors,
      isPrediction: isPrediction ?? this.isPrediction,
      dataQuality: dataQuality ?? this.dataQuality,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Get risk level based on score
  RiskLevel get riskLevel {
    if (riskScore >= 0.8) return RiskLevel.critical;
    if (riskScore >= 0.6) return RiskLevel.high;
    if (riskScore >= 0.3) return RiskLevel.medium;
    return RiskLevel.low;
  }

  /// Check if this data point represents an anomaly
  bool isAnomaly({double threshold = 2.0}) {
    return dataQuality < 0.5 || confidence < 0.3;
  }
}

/// Temporal trend analysis for risk patterns
class TemporalTrend extends Equatable {
  /// Overall trend direction (-1: decreasing, 0: stable, 1: increasing)
  final double trendDirection;

  /// Rate of change per time unit
  final double changeRate;

  /// Seasonal pattern strength (0.0 to 1.0)
  final double seasonalityStrength;

  /// Volatility measure (standard deviation)
  final double volatility;

  /// Correlation with environmental factors
  final Map<String, double> environmentalCorrelations;

  /// Trend confidence (0.0 to 1.0)
  final double confidence;

  /// Time range for this trend analysis
  final DateRange timeRange;

  const TemporalTrend({
    required this.trendDirection,
    required this.changeRate,
    required this.seasonalityStrength,
    required this.volatility,
    required this.environmentalCorrelations,
    required this.confidence,
    required this.timeRange,
  });

  @override
  List<Object?> get props => [
        trendDirection,
        changeRate,
        seasonalityStrength,
        volatility,
        environmentalCorrelations,
        confidence,
        timeRange,
      ];

  /// Get trend description
  String get trendDescription {
    if (trendDirection > 0.3) return 'Increasing';
    if (trendDirection < -0.3) return 'Decreasing';
    return 'Stable';
  }

  /// Check if trend is significant
  bool get isSignificant => confidence > 0.7;
}

/// Date range utility class
class DateRange extends Equatable {
  /// Start date of the range
  final DateTime start;

  /// End date of the range
  final DateTime end;

  const DateRange({
    required this.start,
    required this.end,
  });

  @override
  List<Object?> get props => [start, end];

  /// Get duration of the range
  Duration get duration => end.difference(start);

  /// Check if a date is within this range
  bool contains(DateTime date) {
    return date.isAfter(start) && date.isBefore(end);
  }

  /// Check if this range overlaps with another
  bool overlaps(DateRange other) {
    return start.isBefore(other.end) && end.isAfter(other.start);
  }
}

/// Comprehensive temporal risk data entity
class TemporalRiskData extends Equatable {
  /// Unique identifier for this temporal dataset
  final String id;

  /// Region identifier
  final String regionId;

  /// Human-readable region name
  final String regionName;

  /// Geographic coordinates of the region center
  final LatLng coordinates;

  /// Time interval for data aggregation
  final TimeInterval timeInterval;

  /// Custom interval duration (for TimeInterval.custom)
  final Duration? customInterval;

  /// Ordered list of temporal data points
  final List<TemporalDataPoint> dataPoints;

  /// Time range covered by this dataset
  final DateRange timeRange;

  /// Trend analysis for this temporal data
  final TemporalTrend? trend;

  /// Seasonal patterns identified in the data
  final List<SeasonalPattern> seasonalPatterns;

  /// Future predictions beyond current data
  final List<TemporalDataPoint> predictions;

  /// Data quality metrics
  final DataQualityMetrics qualityMetrics;

  /// Last update timestamp
  final DateTime lastUpdated;

  /// Data source information
  final String dataSource;

  /// Additional metadata
  final Map<String, dynamic> metadata;

  const TemporalRiskData({
    required this.id,
    required this.regionId,
    required this.regionName,
    required this.coordinates,
    required this.timeInterval,
    this.customInterval,
    required this.dataPoints,
    required this.timeRange,
    this.trend,
    this.seasonalPatterns = const [],
    this.predictions = const [],
    required this.qualityMetrics,
    required this.lastUpdated,
    required this.dataSource,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [
        id,
        regionId,
        regionName,
        coordinates,
        timeInterval,
        customInterval,
        dataPoints,
        timeRange,
        trend,
        seasonalPatterns,
        predictions,
        qualityMetrics,
        lastUpdated,
        dataSource,
        metadata,
      ];

  /// Get data points within a specific time range
  List<TemporalDataPoint> getDataInRange(DateRange range) {
    return dataPoints.where((point) => range.contains(point.timestamp)).toList();
  }

  /// Get the most recent data point
  TemporalDataPoint? get latestDataPoint {
    if (dataPoints.isEmpty) return null;
    return dataPoints.reduce((a, b) => a.timestamp.isAfter(b.timestamp) ? a : b);
  }

  /// Get the current risk score (from latest data point)
  double get currentRiskScore => latestDataPoint?.riskScore ?? 0.0;

  /// Get the current risk level
  RiskLevel get currentRiskLevel => latestDataPoint?.riskLevel ?? RiskLevel.low;

  /// Get data points for a specific time period
  List<TemporalDataPoint> getDataForPeriod({
    required DateTime start,
    required DateTime end,
  }) {
    return dataPoints
        .where((point) =>
            point.timestamp.isAfter(start) &&
            point.timestamp.isBefore(end))
        .toList();
  }

  /// Get historical data points (excluding predictions)
  List<TemporalDataPoint> get historicalData {
    return dataPoints.where((point) => !point.isPrediction).toList();
  }

  /// Get prediction data points
  List<TemporalDataPoint> get predictionData {
    return dataPoints.where((point) => point.isPrediction).toList();
  }

  /// Calculate average risk score over the time period
  double get averageRiskScore {
    if (dataPoints.isEmpty) return 0.0;
    final sum = dataPoints.fold<double>(0.0, (sum, point) => sum + point.riskScore);
    return sum / dataPoints.length;
  }

  /// Calculate maximum risk score in the time period
  double get maxRiskScore {
    if (dataPoints.isEmpty) return 0.0;
    return dataPoints.map((point) => point.riskScore).reduce((a, b) => a > b ? a : b);
  }

  /// Calculate minimum risk score in the time period
  double get minRiskScore {
    if (dataPoints.isEmpty) return 0.0;
    return dataPoints.map((point) => point.riskScore).reduce((a, b) => a < b ? a : b);
  }

  /// Get data points that represent anomalies
  List<TemporalDataPoint> get anomalies {
    return dataPoints.where((point) => point.isAnomaly()).toList();
  }

  /// Interpolate risk score at a specific timestamp
  double interpolateRiskScore(DateTime timestamp) {
    if (dataPoints.isEmpty) return 0.0;

    // Find surrounding data points
    final sortedPoints = dataPoints.toList()
      ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

    // If timestamp is before first point, return first value
    if (timestamp.isBefore(sortedPoints.first.timestamp)) {
      return sortedPoints.first.riskScore;
    }

    // If timestamp is after last point, return last value
    if (timestamp.isAfter(sortedPoints.last.timestamp)) {
      return sortedPoints.last.riskScore;
    }

    // Find the two points to interpolate between
    for (int i = 0; i < sortedPoints.length - 1; i++) {
      final current = sortedPoints[i];
      final next = sortedPoints[i + 1];

      if (timestamp.isAfter(current.timestamp) && timestamp.isBefore(next.timestamp)) {
        // Linear interpolation
        final totalDuration = next.timestamp.difference(current.timestamp).inMilliseconds;
        final elapsedDuration = timestamp.difference(current.timestamp).inMilliseconds;
        final ratio = elapsedDuration / totalDuration;

        return current.riskScore + (next.riskScore - current.riskScore) * ratio;
      }
    }

    // Exact match found
    final exactMatch = sortedPoints.firstWhere(
      (point) => point.timestamp == timestamp,
      orElse: () => sortedPoints.first,
    );
    return exactMatch.riskScore;
  }

  /// Create a copy with updated values
  TemporalRiskData copyWith({
    String? id,
    String? regionId,
    String? regionName,
    LatLng? coordinates,
    TimeInterval? timeInterval,
    Duration? customInterval,
    List<TemporalDataPoint>? dataPoints,
    DateRange? timeRange,
    TemporalTrend? trend,
    List<SeasonalPattern>? seasonalPatterns,
    List<TemporalDataPoint>? predictions,
    DataQualityMetrics? qualityMetrics,
    DateTime? lastUpdated,
    String? dataSource,
    Map<String, dynamic>? metadata,
  }) {
    return TemporalRiskData(
      id: id ?? this.id,
      regionId: regionId ?? this.regionId,
      regionName: regionName ?? this.regionName,
      coordinates: coordinates ?? this.coordinates,
      timeInterval: timeInterval ?? this.timeInterval,
      customInterval: customInterval ?? this.customInterval,
      dataPoints: dataPoints ?? this.dataPoints,
      timeRange: timeRange ?? this.timeRange,
      trend: trend ?? this.trend,
      seasonalPatterns: seasonalPatterns ?? this.seasonalPatterns,
      predictions: predictions ?? this.predictions,
      qualityMetrics: qualityMetrics ?? this.qualityMetrics,
      lastUpdated: lastUpdated ?? this.lastUpdated,
      dataSource: dataSource ?? this.dataSource,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Add a new data point
  TemporalRiskData addDataPoint(TemporalDataPoint point) {
    final updatedPoints = List<TemporalDataPoint>.from(dataPoints)..add(point);
    return copyWith(
      dataPoints: updatedPoints,
      lastUpdated: DateTime.now(),
    );
  }

  /// Update an existing data point by timestamp
  TemporalRiskData updateDataPoint(TemporalDataPoint updatedPoint) {
    final updatedPoints = dataPoints.map((point) {
      return point.timestamp == updatedPoint.timestamp ? updatedPoint : point;
    }).toList();

    return copyWith(
      dataPoints: updatedPoints,
      lastUpdated: DateTime.now(),
    );
  }

  /// Remove data points older than a specific date
  TemporalRiskData removeDataBefore(DateTime cutoffDate) {
    final filteredPoints = dataPoints
        .where((point) => point.timestamp.isAfter(cutoffDate))
        .toList();

    return copyWith(
      dataPoints: filteredPoints,
      lastUpdated: DateTime.now(),
    );
  }
}

/// Seasonal pattern in temporal risk data
class SeasonalPattern extends Equatable {
  /// Name or description of the pattern
  final String name;

  /// Season identifier (e.g., 'wet_season', 'dry_season')
  final String seasonId;

  /// Start month (1-12)
  final int startMonth;

  /// End month (1-12)
  final int endMonth;

  /// Average risk score during this season
  final double averageRiskScore;

  /// Peak risk score during this season
  final double peakRiskScore;

  /// Pattern strength (0.0 to 1.0)
  final double strength;

  /// Years of data this pattern is based on
  final int yearsOfData;

  const SeasonalPattern({
    required this.name,
    required this.seasonId,
    required this.startMonth,
    required this.endMonth,
    required this.averageRiskScore,
    required this.peakRiskScore,
    required this.strength,
    required this.yearsOfData,
  });

  @override
  List<Object?> get props => [
        name,
        seasonId,
        startMonth,
        endMonth,
        averageRiskScore,
        peakRiskScore,
        strength,
        yearsOfData,
      ];

  /// Check if a given month falls within this seasonal pattern
  bool containsMonth(int month) {
    if (startMonth <= endMonth) {
      return month >= startMonth && month <= endMonth;
    } else {
      // Pattern spans across year boundary
      return month >= startMonth || month <= endMonth;
    }
  }

  /// Get duration of the pattern in months
  int get durationMonths {
    if (startMonth <= endMonth) {
      return endMonth - startMonth + 1;
    } else {
      return (12 - startMonth + 1) + endMonth;
    }
  }
}

/// Data quality metrics for temporal data
class DataQualityMetrics extends Equatable {
  /// Overall data quality score (0.0 to 1.0)
  final double overallQuality;

  /// Percentage of data points with high confidence
  final double highConfidencePercentage;

  /// Number of missing data points
  final int missingDataPoints;

  /// Percentage of data completeness
  final double completenessPercentage;

  /// Number of anomalous data points detected
  final int anomalousPoints;

  /// Data freshness score (based on last update time)
  final double freshnessScore;

  const DataQualityMetrics({
    required this.overallQuality,
    required this.highConfidencePercentage,
    required this.missingDataPoints,
    required this.completenessPercentage,
    required this.anomalousPoints,
    required this.freshnessScore,
  });

  @override
  List<Object?> get props => [
        overallQuality,
        highConfidencePercentage,
        missingDataPoints,
        completenessPercentage,
        anomalousPoints,
        freshnessScore,
      ];

  /// Check if data quality is acceptable for visualization
  bool get isAcceptableQuality => overallQuality >= 0.7;

  /// Check if data is fresh enough for real-time visualization
  bool get isFresh => freshnessScore >= 0.8;

  /// Get quality description
  String get qualityDescription {
    if (overallQuality >= 0.9) return 'Excellent';
    if (overallQuality >= 0.8) return 'Good';
    if (overallQuality >= 0.7) return 'Fair';
    if (overallQuality >= 0.5) return 'Poor';
    return 'Very Poor';
  }
}

/// Utility extensions for temporal data operations
extension TemporalRiskDataListExtension on List<TemporalRiskData> {
  /// Get temporal data for a specific region
  TemporalRiskData? getByRegion(String regionId) {
    try {
      return firstWhere((data) => data.regionId == regionId);
    } catch (e) {
      return null;
    }
  }

  /// Get all regions with data in a time range
  List<TemporalRiskData> getDataInTimeRange(DateRange range) {
    return where((data) => data.timeRange.overlaps(range)).toList();
  }

  /// Sort by current risk score (descending)
  List<TemporalRiskData> sortByCurrentRisk() {
    final sorted = List<TemporalRiskData>.from(this);
    sorted.sort((a, b) => b.currentRiskScore.compareTo(a.currentRiskScore));
    return sorted;
  }

  /// Filter by minimum data quality
  List<TemporalRiskData> filterByQuality(double minQuality) {
    return where((data) => data.qualityMetrics.overallQuality >= minQuality).toList();
  }

  /// Get regions with increasing risk trends
  List<TemporalRiskData> getIncreasingRiskRegions() {
    return where((data) =>
        data.trend?.trendDirection != null &&
        data.trend!.trendDirection > 0.3).toList();
  }

  /// Get regions with anomalies
  List<TemporalRiskData> getRegionsWithAnomalies() {
    return where((data) => data.anomalies.isNotEmpty).toList();
  }
}