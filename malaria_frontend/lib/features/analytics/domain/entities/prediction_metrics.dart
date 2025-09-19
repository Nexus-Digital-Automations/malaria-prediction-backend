/// Prediction metrics entities for comprehensive model performance analysis
///
/// This file contains entities specifically designed for tracking and analyzing
/// prediction model performance, accuracy metrics, and prediction reliability
/// for the malaria prediction analytics dashboard.
///
/// Usage:
/// ```dart
/// final metrics = PredictionMetrics(
///   id: 'metrics_001',
///   modelId: 'malaria_model_v2',
///   evaluationPeriod: DateRange(start: DateTime.now().subtract(Duration(days: 7)), end: DateTime.now()),
///   overallAccuracy: 0.87,
///   precision: 0.85,
///   recall: 0.89,
///   f1Score: 0.87,
/// );
/// ```
library;

import 'package:equatable/equatable.dart';
import 'analytics_data.dart';

/// Comprehensive prediction metrics entity for model performance tracking
class PredictionMetrics extends Equatable {
  /// Unique identifier for this metrics dataset
  final String id;

  /// Model identifier being evaluated
  final String modelId;

  /// Model version for tracking iterations
  final String modelVersion;

  /// Evaluation period for these metrics
  final DateRange evaluationPeriod;

  /// Geographic region for localized metrics
  final String region;

  /// Overall prediction accuracy (0.0 to 1.0)
  final double overallAccuracy;

  /// Precision metric for positive prediction quality
  final double precision;

  /// Recall metric for prediction completeness
  final double recall;

  /// F1 score for balanced performance assessment
  final double f1Score;

  /// Area under ROC curve for binary classification performance
  final double aucRoc;

  /// Area under precision-recall curve
  final double aucPr;

  /// Matthews correlation coefficient for balanced accuracy
  final double matthewsCorrelation;

  /// Confusion matrix data for detailed analysis
  final ConfusionMatrix confusionMatrix;

  /// Performance breakdown by risk level
  final Map<RiskLevel, PerformanceByLevel> performanceByLevel;

  /// Temporal accuracy trends
  final List<AccuracyTrendPoint> accuracyTrend;

  /// Model reliability metrics
  final ReliabilityMetrics reliability;

  /// Prediction speed and performance metrics
  final PerformanceMetrics performance;

  /// Timestamp when metrics were calculated
  final DateTime calculatedAt;

  const PredictionMetrics({
    required this.id,
    required this.modelId,
    required this.modelVersion,
    required this.evaluationPeriod,
    required this.region,
    required this.overallAccuracy,
    required this.precision,
    required this.recall,
    required this.f1Score,
    required this.aucRoc,
    required this.aucPr,
    required this.matthewsCorrelation,
    required this.confusionMatrix,
    required this.performanceByLevel,
    required this.accuracyTrend,
    required this.reliability,
    required this.performance,
    required this.calculatedAt,
  });

  /// Creates a copy with updated values
  PredictionMetrics copyWith({
    String? id,
    String? modelId,
    String? modelVersion,
    DateRange? evaluationPeriod,
    String? region,
    double? overallAccuracy,
    double? precision,
    double? recall,
    double? f1Score,
    double? aucRoc,
    double? aucPr,
    double? matthewsCorrelation,
    ConfusionMatrix? confusionMatrix,
    Map<RiskLevel, PerformanceByLevel>? performanceByLevel,
    List<AccuracyTrendPoint>? accuracyTrend,
    ReliabilityMetrics? reliability,
    PerformanceMetrics? performance,
    DateTime? calculatedAt,
  }) {
    return PredictionMetrics(
      id: id ?? this.id,
      modelId: modelId ?? this.modelId,
      modelVersion: modelVersion ?? this.modelVersion,
      evaluationPeriod: evaluationPeriod ?? this.evaluationPeriod,
      region: region ?? this.region,
      overallAccuracy: overallAccuracy ?? this.overallAccuracy,
      precision: precision ?? this.precision,
      recall: recall ?? this.recall,
      f1Score: f1Score ?? this.f1Score,
      aucRoc: aucRoc ?? this.aucRoc,
      aucPr: aucPr ?? this.aucPr,
      matthewsCorrelation: matthewsCorrelation ?? this.matthewsCorrelation,
      confusionMatrix: confusionMatrix ?? this.confusionMatrix,
      performanceByLevel: performanceByLevel ?? this.performanceByLevel,
      accuracyTrend: accuracyTrend ?? this.accuracyTrend,
      reliability: reliability ?? this.reliability,
      performance: performance ?? this.performance,
      calculatedAt: calculatedAt ?? this.calculatedAt,
    );
  }

  @override
  List<Object?> get props => [
        id,
        modelId,
        modelVersion,
        evaluationPeriod,
        region,
        overallAccuracy,
        precision,
        recall,
        f1Score,
        aucRoc,
        aucPr,
        matthewsCorrelation,
        confusionMatrix,
        performanceByLevel,
        accuracyTrend,
        reliability,
        performance,
        calculatedAt,
      ];
}

/// Model performance entity for comparing multiple models
class ModelPerformance extends Equatable {
  /// Model identifier
  final String modelId;

  /// Model name for display
  final String modelName;

  /// Model version
  final String version;

  /// Model training date
  final DateTime trainedAt;

  /// Model deployment status
  final ModelStatus status;

  /// Primary accuracy metric for comparison
  final double accuracy;

  /// Key performance indicators
  final Map<String, double> kpis;

  /// Model complexity metrics
  final ModelComplexity complexity;

  /// Resource usage statistics
  final ResourceUsage resourceUsage;

  /// Model confidence distribution
  final List<ConfidenceDistribution> confidenceDistribution;

  /// Calibration metrics for prediction reliability
  final CalibrationMetrics calibration;

  const ModelPerformance({
    required this.modelId,
    required this.modelName,
    required this.version,
    required this.trainedAt,
    required this.status,
    required this.accuracy,
    required this.kpis,
    required this.complexity,
    required this.resourceUsage,
    required this.confidenceDistribution,
    required this.calibration,
  });

  @override
  List<Object?> get props => [
        modelId,
        modelName,
        version,
        trainedAt,
        status,
        accuracy,
        kpis,
        complexity,
        resourceUsage,
        confidenceDistribution,
        calibration,
      ];
}

/// Time series metric entity for historical trend analysis
class TimeSeriesMetric extends Equatable {
  /// Metric identifier
  final String metricId;

  /// Metric name for display
  final String metricName;

  /// Metric type categorization
  final MetricType type;

  /// Unit of measurement
  final String unit;

  /// Time series data points
  final List<TimeSeriesPoint> dataPoints;

  /// Statistical summary
  final StatisticalSummary summary;

  /// Trend analysis results
  final TrendAnalysis trend;

  /// Seasonality detection results
  final SeasonalityAnalysis seasonality;

  /// Data quality indicators
  final TimeSeriesQuality quality;

  const TimeSeriesMetric({
    required this.metricId,
    required this.metricName,
    required this.type,
    required this.unit,
    required this.dataPoints,
    required this.summary,
    required this.trend,
    required this.seasonality,
    required this.quality,
  });

  @override
  List<Object?> get props => [
        metricId,
        metricName,
        type,
        unit,
        dataPoints,
        summary,
        trend,
        seasonality,
        quality,
      ];
}

/// Confusion matrix entity for classification analysis
class ConfusionMatrix extends Equatable {
  /// True positives count
  final int truePositives;

  /// True negatives count
  final int trueNegatives;

  /// False positives count
  final int falsePositives;

  /// False negatives count
  final int falseNegatives;

  /// Class labels for multi-class scenarios
  final List<String> classLabels;

  /// Multi-class confusion matrix (for more than binary classification)
  final List<List<int>>? multiClassMatrix;

  const ConfusionMatrix({
    required this.truePositives,
    required this.trueNegatives,
    required this.falsePositives,
    required this.falseNegatives,
    required this.classLabels,
    this.multiClassMatrix,
  });

  /// Total predictions count
  int get totalPredictions => truePositives + trueNegatives + falsePositives + falseNegatives;

  /// Accuracy calculation
  double get accuracy => totalPredictions > 0 ? (truePositives + trueNegatives) / totalPredictions : 0.0;

  /// Precision calculation
  double get precision => (truePositives + falsePositives) > 0 ? truePositives / (truePositives + falsePositives) : 0.0;

  /// Recall calculation
  double get recall => (truePositives + falseNegatives) > 0 ? truePositives / (truePositives + falseNegatives) : 0.0;

  /// Specificity calculation
  double get specificity => (trueNegatives + falsePositives) > 0 ? trueNegatives / (trueNegatives + falsePositives) : 0.0;

  @override
  List<Object?> get props => [
        truePositives,
        trueNegatives,
        falsePositives,
        falseNegatives,
        classLabels,
        multiClassMatrix,
      ];
}

/// Performance metrics by risk level
class PerformanceByLevel extends Equatable {
  /// Risk level
  final RiskLevel riskLevel;

  /// Accuracy for this risk level
  final double accuracy;

  /// Precision for this risk level
  final double precision;

  /// Recall for this risk level
  final double recall;

  /// F1 score for this risk level
  final double f1Score;

  /// Sample size for this risk level
  final int sampleSize;

  /// Support (number of true instances) for this risk level
  final int support;

  const PerformanceByLevel({
    required this.riskLevel,
    required this.accuracy,
    required this.precision,
    required this.recall,
    required this.f1Score,
    required this.sampleSize,
    required this.support,
  });

  @override
  List<Object?> get props => [riskLevel, accuracy, precision, recall, f1Score, sampleSize, support];
}

/// Accuracy trend point for temporal analysis
class AccuracyTrendPoint extends Equatable {
  /// Timestamp of the measurement
  final DateTime timestamp;

  /// Accuracy value at this point
  final double accuracy;

  /// Sample size for this measurement
  final int sampleSize;

  /// Confidence interval bounds
  final ConfidenceInterval confidenceInterval;

  /// Additional context or metadata
  final Map<String, dynamic> metadata;

  const AccuracyTrendPoint({
    required this.timestamp,
    required this.accuracy,
    required this.sampleSize,
    required this.confidenceInterval,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [timestamp, accuracy, sampleSize, confidenceInterval, metadata];
}

/// Reliability metrics for model trustworthiness
class ReliabilityMetrics extends Equatable {
  /// Prediction consistency across similar inputs
  final double consistency;

  /// Model stability over time
  final double stability;

  /// Uncertainty quantification quality
  final double uncertaintyCalibration;

  /// Out-of-distribution detection capability
  final double oodDetection;

  /// Adversarial robustness score
  final double robustness;

  /// Prediction interval coverage
  final double intervalCoverage;

  const ReliabilityMetrics({
    required this.consistency,
    required this.stability,
    required this.uncertaintyCalibration,
    required this.oodDetection,
    required this.robustness,
    required this.intervalCoverage,
  });

  @override
  List<Object?> get props => [
        consistency,
        stability,
        uncertaintyCalibration,
        oodDetection,
        robustness,
        intervalCoverage,
      ];
}

/// Performance metrics for computational efficiency
class PerformanceMetrics extends Equatable {
  /// Average prediction time in milliseconds
  final double avgPredictionTime;

  /// Memory usage in MB
  final double memoryUsage;

  /// CPU utilization percentage
  final double cpuUtilization;

  /// Throughput (predictions per second)
  final double throughput;

  /// Model loading time in milliseconds
  final double loadingTime;

  /// Energy consumption metrics
  final EnergyConsumption energyConsumption;

  const PerformanceMetrics({
    required this.avgPredictionTime,
    required this.memoryUsage,
    required this.cpuUtilization,
    required this.throughput,
    required this.loadingTime,
    required this.energyConsumption,
  });

  @override
  List<Object?> get props => [
        avgPredictionTime,
        memoryUsage,
        cpuUtilization,
        throughput,
        loadingTime,
        energyConsumption,
      ];
}

/// Energy consumption metrics
class EnergyConsumption extends Equatable {
  /// Energy per prediction in joules
  final double energyPerPrediction;

  /// Total energy consumption in kWh
  final double totalEnergyKwh;

  /// Carbon footprint in grams CO2
  final double carbonFootprintGrams;

  const EnergyConsumption({
    required this.energyPerPrediction,
    required this.totalEnergyKwh,
    required this.carbonFootprintGrams,
  });

  @override
  List<Object?> get props => [energyPerPrediction, totalEnergyKwh, carbonFootprintGrams];
}

/// Model complexity metrics
class ModelComplexity extends Equatable {
  /// Number of parameters
  final int parameterCount;

  /// Model size in MB
  final double modelSizeMb;

  /// Number of layers (for neural networks)
  final int? layerCount;

  /// Computational complexity score
  final double complexityScore;

  /// Interpretability score (higher = more interpretable)
  final double interpretabilityScore;

  const ModelComplexity({
    required this.parameterCount,
    required this.modelSizeMb,
    this.layerCount,
    required this.complexityScore,
    required this.interpretabilityScore,
  });

  @override
  List<Object?> get props => [
        parameterCount,
        modelSizeMb,
        layerCount,
        complexityScore,
        interpretabilityScore,
      ];
}

/// Resource usage statistics
class ResourceUsage extends Equatable {
  /// Peak memory usage in MB
  final double peakMemoryMb;

  /// Average CPU usage percentage
  final double avgCpuUsage;

  /// GPU usage percentage (if applicable)
  final double? gpuUsage;

  /// Network bandwidth usage in MB
  final double networkUsageMb;

  /// Storage usage in MB
  final double storageUsageMb;

  const ResourceUsage({
    required this.peakMemoryMb,
    required this.avgCpuUsage,
    this.gpuUsage,
    required this.networkUsageMb,
    required this.storageUsageMb,
  });

  @override
  List<Object?> get props => [
        peakMemoryMb,
        avgCpuUsage,
        gpuUsage,
        networkUsageMb,
        storageUsageMb,
      ];
}

/// Confidence distribution for prediction analysis
class ConfidenceDistribution extends Equatable {
  /// Confidence range (e.g., 0.0-0.1, 0.1-0.2, etc.)
  final ConfidenceRange range;

  /// Number of predictions in this confidence range
  final int count;

  /// Actual accuracy for predictions in this range
  final double actualAccuracy;

  /// Predicted confidence for this range
  final double predictedConfidence;

  const ConfidenceDistribution({
    required this.range,
    required this.count,
    required this.actualAccuracy,
    required this.predictedConfidence,
  });

  @override
  List<Object?> get props => [range, count, actualAccuracy, predictedConfidence];
}

/// Confidence range definition
class ConfidenceRange extends Equatable {
  /// Lower bound of the confidence range
  final double lowerBound;

  /// Upper bound of the confidence range
  final double upperBound;

  const ConfidenceRange({
    required this.lowerBound,
    required this.upperBound,
  });

  @override
  List<Object?> get props => [lowerBound, upperBound];
}

/// Calibration metrics for prediction reliability
class CalibrationMetrics extends Equatable {
  /// Expected calibration error
  final double expectedCalibrationError;

  /// Maximum calibration error
  final double maxCalibrationError;

  /// Average calibration error
  final double avgCalibrationError;

  /// Brier score for probability calibration
  final double brierScore;

  /// Reliability diagram data
  final List<CalibrationBin> reliabilityDiagram;

  const CalibrationMetrics({
    required this.expectedCalibrationError,
    required this.maxCalibrationError,
    required this.avgCalibrationError,
    required this.brierScore,
    required this.reliabilityDiagram,
  });

  @override
  List<Object?> get props => [
        expectedCalibrationError,
        maxCalibrationError,
        avgCalibrationError,
        brierScore,
        reliabilityDiagram,
      ];
}

/// Calibration bin for reliability diagram
class CalibrationBin extends Equatable {
  /// Predicted confidence for this bin
  final double predictedConfidence;

  /// Actual accuracy for this bin
  final double actualAccuracy;

  /// Sample count in this bin
  final int sampleCount;

  const CalibrationBin({
    required this.predictedConfidence,
    required this.actualAccuracy,
    required this.sampleCount,
  });

  @override
  List<Object?> get props => [predictedConfidence, actualAccuracy, sampleCount];
}

/// Time series data point
class TimeSeriesPoint extends Equatable {
  /// Timestamp of the measurement
  final DateTime timestamp;

  /// Metric value at this point
  final double value;

  /// Quality indicator for this data point
  final double quality;

  /// Additional metadata
  final Map<String, dynamic> metadata;

  const TimeSeriesPoint({
    required this.timestamp,
    required this.value,
    required this.quality,
    this.metadata = const {},
  });

  @override
  List<Object?> get props => [timestamp, value, quality, metadata];
}

/// Statistical summary for time series
class StatisticalSummary extends Equatable {
  /// Mean value
  final double mean;

  /// Standard deviation
  final double standardDeviation;

  /// Minimum value
  final double minimum;

  /// Maximum value
  final double maximum;

  /// Median value
  final double median;

  /// 25th percentile
  final double percentile25;

  /// 75th percentile
  final double percentile75;

  const StatisticalSummary({
    required this.mean,
    required this.standardDeviation,
    required this.minimum,
    required this.maximum,
    required this.median,
    required this.percentile25,
    required this.percentile75,
  });

  @override
  List<Object?> get props => [
        mean,
        standardDeviation,
        minimum,
        maximum,
        median,
        percentile25,
        percentile75,
      ];
}

/// Trend analysis results
class TrendAnalysis extends Equatable {
  /// Overall trend direction
  final TrendDirection direction;

  /// Trend strength (0.0 to 1.0)
  final double strength;

  /// Trend slope
  final double slope;

  /// R-squared value for trend line fit
  final double rSquared;

  /// Trend significance p-value
  final double pValue;

  const TrendAnalysis({
    required this.direction,
    required this.strength,
    required this.slope,
    required this.rSquared,
    required this.pValue,
  });

  @override
  List<Object?> get props => [direction, strength, slope, rSquared, pValue];
}

/// Seasonality analysis results
class SeasonalityAnalysis extends Equatable {
  /// Whether seasonality is detected
  final bool hasSeasonality;

  /// Dominant seasonal period in days
  final int? seasonalPeriod;

  /// Seasonal strength (0.0 to 1.0)
  final double seasonalStrength;

  /// Seasonal component peaks
  final List<int> seasonalPeaks;

  const SeasonalityAnalysis({
    required this.hasSeasonality,
    this.seasonalPeriod,
    required this.seasonalStrength,
    required this.seasonalPeaks,
  });

  @override
  List<Object?> get props => [hasSeasonality, seasonalPeriod, seasonalStrength, seasonalPeaks];
}

/// Time series quality indicators
class TimeSeriesQuality extends Equatable {
  /// Data completeness percentage
  final double completeness;

  /// Data consistency score
  final double consistency;

  /// Number of outliers detected
  final int outlierCount;

  /// Missing data points count
  final int missingCount;

  /// Data freshness in hours
  final double freshnessHours;

  const TimeSeriesQuality({
    required this.completeness,
    required this.consistency,
    required this.outlierCount,
    required this.missingCount,
    required this.freshnessHours,
  });

  @override
  List<Object?> get props => [completeness, consistency, outlierCount, missingCount, freshnessHours];
}

/// Confidence interval for statistical measurements
class ConfidenceInterval extends Equatable {
  /// Lower bound of the interval
  final double lowerBound;

  /// Upper bound of the interval
  final double upperBound;

  /// Confidence level (e.g., 0.95 for 95% confidence)
  final double confidenceLevel;

  const ConfidenceInterval({
    required this.lowerBound,
    required this.upperBound,
    required this.confidenceLevel,
  });

  @override
  List<Object?> get props => [lowerBound, upperBound, confidenceLevel];
}

/// Model deployment status
enum ModelStatus {
  development,
  testing,
  staging,
  production,
  deprecated,
  retired,
}

/// Metric type categorization
enum MetricType {
  accuracy,
  performance,
  resource,
  reliability,
  calibration,
  fairness,
  custom,
}

/// Trend direction enumeration
enum TrendDirection {
  increasing,
  decreasing,
  stable,
  cyclical,
  unknown,
}

/// ROC curve data point
class ROCPoint {
  /// Classification threshold
  final double threshold;

  /// True positive rate (sensitivity)
  final double truePositiveRate;

  /// False positive rate (1 - specificity)
  final double falsePositiveRate;

  /// Precision (optional)
  final double? precision;

  /// Recall (optional, same as TPR)
  final double? recall;

  const ROCPoint({
    required this.threshold,
    required this.truePositiveRate,
    required this.falsePositiveRate,
    this.precision,
    this.recall,
  });

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ROCPoint &&
        other.threshold == threshold &&
        other.truePositiveRate == truePositiveRate &&
        other.falsePositiveRate == falsePositiveRate;
  }

  @override
  int get hashCode => Object.hash(threshold, truePositiveRate, falsePositiveRate);
}