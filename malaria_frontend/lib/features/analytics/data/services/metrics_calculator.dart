/// Metrics calculator service for statistical calculations and data processing
///
/// This service provides comprehensive statistical analysis and metric calculations
/// for prediction performance, trend analysis, and data quality assessment.
///
/// Usage:
/// ```dart
/// final calculator = MetricsCalculator();
/// final confusionMatrix = calculator.calculateConfusionMatrix(predictions, actual);
/// final aucScore = calculator.calculateAUC(rocPoints);
/// ```
library;

import 'dart:math' as math;
import '../../domain/entities/prediction_metrics.dart';

/// Metrics calculator service for prediction analytics
class MetricsCalculator {
  /// Calculate confusion matrix from predictions and actual values
  ConfusionMatrix calculateConfusionMatrix(
    List<bool> predictions,
    List<bool> actual, {
    List<String>? classLabels,
  }) {
    if (predictions.length != actual.length) {
      throw ArgumentError('Predictions and actual values must have same length');
    }

    int truePositives = 0;
    int trueNegatives = 0;
    int falsePositives = 0;
    int falseNegatives = 0;

    for (int i = 0; i < predictions.length; i++) {
      if (predictions[i] && actual[i]) {
        truePositives++;
      } else if (!predictions[i] && !actual[i]) {
        trueNegatives++;
      } else if (predictions[i] && !actual[i]) {
        falsePositives++;
      } else {
        falseNegatives++;
      }
    }

    return ConfusionMatrix(
      truePositives: truePositives,
      trueNegatives: trueNegatives,
      falsePositives: falsePositives,
      falseNegatives: falseNegatives,
      classLabels: classLabels ?? ['Negative', 'Positive'],
    );
  }

  /// Calculate ROC curve points from probability scores and actual labels
  List<ROCPoint> calculateROCCurve(
    List<double> probabilities,
    List<bool> actual,
  ) {
    if (probabilities.length != actual.length) {
      throw ArgumentError('Probabilities and actual values must have same length');
    }

    // Create threshold points
    final thresholds = <double>{};
    thresholds.addAll(probabilities);
    thresholds.addAll([0.0, 1.0]);

    final sortedThresholds = thresholds.toList()..sort((a, b) => b.compareTo(a));

    final rocPoints = <ROCPoint>[];

    for (final threshold in sortedThresholds) {
      final predictions = probabilities.map((p) => p >= threshold).toList();
      final confusionMatrix = calculateConfusionMatrix(predictions, actual);

      final tpr = confusionMatrix.recall;
      final fpr = 1.0 - confusionMatrix.specificity;

      rocPoints.add(ROCPoint(
        threshold: threshold,
        truePositiveRate: tpr,
        falsePositiveRate: fpr,
        precision: confusionMatrix.precision,
        recall: tpr,
      ));
    }

    return rocPoints;
  }

  /// Calculate AUC (Area Under Curve) from ROC points
  double calculateAUC(List<ROCPoint> rocPoints) {
    if (rocPoints.length < 2) return 0.0;

    // Sort points by false positive rate
    final sortedPoints = List<ROCPoint>.from(rocPoints)
      ..sort((a, b) => a.falsePositiveRate.compareTo(b.falsePositiveRate));

    double auc = 0.0;
    for (int i = 1; i < sortedPoints.length; i++) {
      final x1 = sortedPoints[i - 1].falsePositiveRate;
      final y1 = sortedPoints[i - 1].truePositiveRate;
      final x2 = sortedPoints[i].falsePositiveRate;
      final y2 = sortedPoints[i].truePositiveRate;

      // Trapezoidal rule
      auc += (x2 - x1) * (y1 + y2) / 2;
    }

    return auc.clamp(0.0, 1.0);
  }

  /// Calculate precision-recall curve
  List<PrecisionRecallPoint> calculatePrecisionRecallCurve(
    List<double> probabilities,
    List<bool> actual,
  ) {
    if (probabilities.length != actual.length) {
      throw ArgumentError('Probabilities and actual values must have same length');
    }

    final thresholds = <double>{};
    thresholds.addAll(probabilities);
    thresholds.addAll([0.0, 1.0]);

    final sortedThresholds = thresholds.toList()..sort((a, b) => b.compareTo(a));

    final prPoints = <PrecisionRecallPoint>[];

    for (final threshold in sortedThresholds) {
      final predictions = probabilities.map((p) => p >= threshold).toList();
      final confusionMatrix = calculateConfusionMatrix(predictions, actual);

      prPoints.add(PrecisionRecallPoint(
        threshold: threshold,
        precision: confusionMatrix.precision,
        recall: confusionMatrix.recall,
      ));
    }

    return prPoints;
  }

  /// Calculate calibration metrics for probability calibration
  CalibrationMetrics calculateCalibrationMetrics(
    List<double> probabilities,
    List<bool> actual, {
    int numBins = 10,
  }) {
    if (probabilities.length != actual.length) {
      throw ArgumentError('Probabilities and actual values must have same length');
    }

    final reliabilityDiagram = <CalibrationBin>[];
    double totalError = 0.0;
    double maxError = 0.0;
    double brierScore = 0.0;

    // Calculate Brier score
    for (int i = 0; i < probabilities.length; i++) {
      final actualValue = actual[i] ? 1.0 : 0.0;
      brierScore += math.pow(probabilities[i] - actualValue, 2);
    }
    brierScore /= probabilities.length;

    // Create calibration bins
    for (int bin = 0; bin < numBins; bin++) {
      final lowerBound = bin / numBins;
      final upperBound = (bin + 1) / numBins;

      final binIndices = <int>[];
      for (int i = 0; i < probabilities.length; i++) {
        if (probabilities[i] >= lowerBound && probabilities[i] < upperBound) {
          binIndices.add(i);
        }
      }

      if (binIndices.isEmpty) continue;

      final binProbabilities = binIndices.map((i) => probabilities[i]).toList();
      final binActual = binIndices.map((i) => actual[i]).toList();

      final avgPredicted = binProbabilities.reduce((a, b) => a + b) / binProbabilities.length;
      final avgActual = binActual.where((x) => x).length / binActual.length;

      final error = (avgPredicted - avgActual).abs();
      totalError += error * binIndices.length;
      maxError = math.max(maxError, error);

      reliabilityDiagram.add(CalibrationBin(
        predictedConfidence: avgPredicted,
        actualAccuracy: avgActual,
        sampleCount: binIndices.length,
      ));
    }

    final expectedCalibrationError = totalError / probabilities.length;
    final avgCalibrationError = reliabilityDiagram.isEmpty
        ? 0.0
        : reliabilityDiagram.map((bin) => (bin.predictedConfidence - bin.actualAccuracy).abs()).reduce((a, b) => a + b) / reliabilityDiagram.length;

    return CalibrationMetrics(
      expectedCalibrationError: expectedCalibrationError,
      maxCalibrationError: maxError,
      avgCalibrationError: avgCalibrationError,
      brierScore: brierScore,
      reliabilityDiagram: reliabilityDiagram,
    );
  }

  /// Calculate statistical summary for time series data
  StatisticalSummary calculateStatisticalSummary(List<double> values) {
    if (values.isEmpty) {
      return const StatisticalSummary(
        mean: 0.0,
        standardDeviation: 0.0,
        minimum: 0.0,
        maximum: 0.0,
        median: 0.0,
        percentile25: 0.0,
        percentile75: 0.0,
      );
    }

    final sortedValues = List<double>.from(values)..sort();
    final n = values.length;

    // Mean
    final mean = values.reduce((a, b) => a + b) / n;

    // Standard deviation
    final variance = values.map((x) => math.pow(x - mean, 2)).reduce((a, b) => a + b) / n;
    final standardDeviation = math.sqrt(variance);

    // Percentiles
    final median = _calculatePercentile(sortedValues, 0.5);
    final percentile25 = _calculatePercentile(sortedValues, 0.25);
    final percentile75 = _calculatePercentile(sortedValues, 0.75);

    return StatisticalSummary(
      mean: mean,
      standardDeviation: standardDeviation,
      minimum: sortedValues.first,
      maximum: sortedValues.last,
      median: median,
      percentile25: percentile25,
      percentile75: percentile75,
    );
  }

  /// Calculate trend analysis for time series data
  TrendAnalysis calculateTrendAnalysis(List<TimeSeriesPoint> points) {
    if (points.length < 2) {
      return const TrendAnalysis(
        direction: TrendDirection.unknown,
        strength: 0.0,
        slope: 0.0,
        rSquared: 0.0,
        pValue: 1.0,
      );
    }

    // Sort points by timestamp
    final sortedPoints = List<TimeSeriesPoint>.from(points)
      ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

    // Convert timestamps to numeric values (days since first point)
    final firstTimestamp = sortedPoints.first.timestamp;
    final xValues = sortedPoints.map((p) => p.timestamp.difference(firstTimestamp).inDays.toDouble()).toList();
    final yValues = sortedPoints.map((p) => p.value).toList();

    // Calculate linear regression
    final n = xValues.length;
    final sumX = xValues.reduce((a, b) => a + b);
    final sumY = yValues.reduce((a, b) => a + b);
    final sumXY = List.generate(n, (i) => xValues[i] * yValues[i]).reduce((a, b) => a + b);
    final sumXX = xValues.map((x) => x * x).reduce((a, b) => a + b);
    final sumYY = yValues.map((y) => y * y).reduce((a, b) => a + b);

    final slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    final intercept = (sumY - slope * sumX) / n;

    // Calculate R-squared
    final meanY = sumY / n;
    final ssTotal = yValues.map((y) => math.pow(y - meanY, 2)).reduce((a, b) => a + b);
    final ssResidual = List.generate(n, (i) => math.pow(yValues[i] - (slope * xValues[i] + intercept), 2)).reduce((a, b) => a + b);
    final rSquared = 1 - (ssResidual / ssTotal);

    // Determine trend direction
    TrendDirection direction;
    if (slope.abs() < 0.001) {
      direction = TrendDirection.stable;
    } else if (slope > 0) {
      direction = TrendDirection.increasing;
    } else {
      direction = TrendDirection.decreasing;
    }

    // Calculate trend strength (based on R-squared)
    final strength = rSquared.clamp(0.0, 1.0);

    // Simple p-value approximation (for demonstration)
    final tStatistic = slope / (math.sqrt(ssResidual / (n - 2)) / math.sqrt(sumXX - sumX * sumX / n));
    final pValue = _approximatePValue(tStatistic.abs(), n - 2);

    return TrendAnalysis(
      direction: direction,
      strength: strength,
      slope: slope,
      rSquared: rSquared,
      pValue: pValue,
    );
  }

  /// Detect seasonality in time series data
  SeasonalityAnalysis detectSeasonality(List<TimeSeriesPoint> points) {
    if (points.length < 24) { // Need at least 2 cycles for meaningful analysis
      return const SeasonalityAnalysis(
        hasSeasonality: false,
        seasonalStrength: 0.0,
        seasonalPeaks: [],
      );
    }

    final sortedPoints = List<TimeSeriesPoint>.from(points)
      ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

    // Simple autocorrelation-based seasonality detection
    final values = sortedPoints.map((p) => p.value).toList();
    final meanValue = values.reduce((a, b) => a + b) / values.length;

    // Test common seasonal periods (in days)
    final testPeriods = [7, 14, 30, 90, 365]; // Weekly, bi-weekly, monthly, quarterly, yearly
    double maxCorrelation = 0.0;
    int? detectedPeriod;

    for (final period in testPeriods) {
      if (period >= values.length / 2) continue;

      final correlation = _calculateAutocorrelation(values, period, meanValue);
      if (correlation > maxCorrelation) {
        maxCorrelation = correlation;
        detectedPeriod = period;
      }
    }

    final hasSeasonality = maxCorrelation > 0.3; // Threshold for significant seasonality
    final seasonalPeaks = hasSeasonality && detectedPeriod != null
        ? _findSeasonalPeaks(values, detectedPeriod)
        : <int>[];

    return SeasonalityAnalysis(
      hasSeasonality: hasSeasonality,
      seasonalPeriod: detectedPeriod,
      seasonalStrength: maxCorrelation,
      seasonalPeaks: seasonalPeaks,
    );
  }

  /// Calculate data quality metrics
  TimeSeriesQuality calculateDataQuality(List<TimeSeriesPoint> points) {
    if (points.isEmpty) {
      return const TimeSeriesQuality(
        completeness: 0.0,
        consistency: 0.0,
        outlierCount: 0,
        missingCount: 0,
        freshnessHours: 0.0,
      );
    }

    final now = DateTime.now();
    final values = points.map((p) => p.value).toList();
    final qualities = points.map((p) => p.quality).toList();

    // Completeness (based on quality scores)
    final avgQuality = qualities.reduce((a, b) => a + b) / qualities.length;
    final completeness = avgQuality;

    // Consistency (coefficient of variation)
    final summary = calculateStatisticalSummary(values);
    final consistency = summary.mean != 0
        ? 1.0 - (summary.standardDeviation / summary.mean.abs()).clamp(0.0, 1.0)
        : 1.0;

    // Outlier detection (values beyond 2 standard deviations)
    final threshold = summary.mean + 2 * summary.standardDeviation;
    final outlierCount = values.where((v) => (v - summary.mean).abs() > 2 * summary.standardDeviation).length;

    // Missing data (quality score below threshold)
    final missingCount = qualities.where((q) => q < 0.5).length;

    // Data freshness
    final latestTimestamp = points.map((p) => p.timestamp).reduce((a, b) => a.isAfter(b) ? a : b);
    final freshnessHours = now.difference(latestTimestamp).inHours.toDouble();

    return TimeSeriesQuality(
      completeness: completeness,
      consistency: consistency,
      outlierCount: outlierCount,
      missingCount: missingCount,
      freshnessHours: freshnessHours,
    );
  }

  /// Calculate confidence intervals
  ConfidenceInterval calculateConfidenceInterval(
    List<double> values, {
    double confidenceLevel = 0.95,
  }) {
    if (values.isEmpty) {
      return ConfidenceInterval(
        lowerBound: 0.0,
        upperBound: 0.0,
        confidenceLevel: confidenceLevel,
      );
    }

    final summary = calculateStatisticalSummary(values);
    final n = values.length;

    // Use t-distribution for small samples, normal for large samples
    final criticalValue = n < 30 ? _getTCriticalValue(confidenceLevel, n - 1) : _getZCriticalValue(confidenceLevel);
    final standardError = summary.standardDeviation / math.sqrt(n);
    final marginOfError = criticalValue * standardError;

    return ConfidenceInterval(
      lowerBound: summary.mean - marginOfError,
      upperBound: summary.mean + marginOfError,
      confidenceLevel: confidenceLevel,
    );
  }

  /// Calculate percentile value
  double _calculatePercentile(List<double> sortedValues, double percentile) {
    final n = sortedValues.length;
    final index = percentile * (n - 1);
    final lowerIndex = index.floor();
    final upperIndex = index.ceil();

    if (lowerIndex == upperIndex) {
      return sortedValues[lowerIndex];
    }

    final lowerValue = sortedValues[lowerIndex];
    final upperValue = sortedValues[upperIndex];
    final weight = index - lowerIndex;

    return lowerValue + weight * (upperValue - lowerValue);
  }

  /// Calculate autocorrelation for seasonality detection
  double _calculateAutocorrelation(List<double> values, int lag, double mean) {
    if (lag >= values.length) return 0.0;

    double numerator = 0.0;
    double denominator = 0.0;

    for (int i = 0; i < values.length - lag; i++) {
      numerator += (values[i] - mean) * (values[i + lag] - mean);
    }

    for (int i = 0; i < values.length; i++) {
      denominator += math.pow(values[i] - mean, 2);
    }

    return denominator != 0 ? numerator / denominator : 0.0;
  }

  /// Find seasonal peaks in the data
  List<int> _findSeasonalPeaks(List<double> values, int period) {
    final peaks = <int>[];
    final periodValues = <double>[];

    // Calculate average values for each position in the period
    for (int pos = 0; pos < period; pos++) {
      final positionValues = <double>[];
      for (int i = pos; i < values.length; i += period) {
        positionValues.add(values[i]);
      }
      if (positionValues.isNotEmpty) {
        periodValues.add(positionValues.reduce((a, b) => a + b) / positionValues.length);
      }
    }

    // Find peaks (local maxima)
    for (int i = 1; i < periodValues.length - 1; i++) {
      if (periodValues[i] > periodValues[i - 1] && periodValues[i] > periodValues[i + 1]) {
        peaks.add(i);
      }
    }

    return peaks;
  }

  /// Approximate p-value for t-statistic (simplified)
  double _approximatePValue(double tStat, int degreesOfFreedom) {
    // Simplified approximation - in practice, use proper statistical libraries
    if (degreesOfFreedom <= 1) return 1.0;
    if (tStat < 1.0) return 0.5;
    if (tStat > 3.0) return 0.01;
    return math.max(0.01, 0.5 - (tStat - 1.0) * 0.2);
  }

  /// Get critical value for t-distribution (simplified)
  double _getTCriticalValue(double confidenceLevel, int degreesOfFreedom) {
    // Simplified - use proper statistical tables in production
    if (confidenceLevel >= 0.99) return 2.58;
    if (confidenceLevel >= 0.95) return 1.96;
    if (confidenceLevel >= 0.90) return 1.65;
    return 1.0;
  }

  /// Get critical value for normal distribution
  double _getZCriticalValue(double confidenceLevel) {
    if (confidenceLevel >= 0.99) return 2.58;
    if (confidenceLevel >= 0.95) return 1.96;
    if (confidenceLevel >= 0.90) return 1.65;
    return 1.0;
  }
}

/// Precision-recall curve point
class PrecisionRecallPoint {
  final double threshold;
  final double precision;
  final double recall;

  const PrecisionRecallPoint({
    required this.threshold,
    required this.precision,
    required this.recall,
  });
}