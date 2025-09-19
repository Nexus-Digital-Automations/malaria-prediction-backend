/// Analytics repository interface for malaria prediction analytics data
///
/// This repository defines the contract for analytics data operations,
/// including fetching prediction accuracy metrics, environmental trends,
/// risk assessments, and generating exportable reports.
///
/// Usage:
/// ```dart
/// final analyticsData = await analyticsRepository.getAnalyticsData(
///   region: 'Kenya',
///   dateRange: DateRange(start: startDate, end: endDate),
///   filters: AnalyticsFilters(includePredictions: true),
/// );
/// ```
library;

import 'package:dartz/dartz.dart';
import 'package:flutter/material.dart';
import '../../../../core/errors/failures.dart';
import '../entities/analytics_data.dart';
import '../entities/chart_data.dart';

/// Repository interface for analytics data operations
abstract class AnalyticsRepository {
  /// Fetches comprehensive analytics data for a specific region and date range
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier (e.g., 'Kenya', 'Tanzania')
  /// - [dateRange]: Date range for analytics data retrieval
  /// - [filters]: Optional filters to customize data retrieval
  ///
  /// Returns:
  /// - [Right]: AnalyticsData containing comprehensive analytics information
  /// - [Left]: Failure if data retrieval fails
  Future<Either<Failure, AnalyticsData>> getAnalyticsData({
    required String region,
    required DateRange dateRange,
    AnalyticsFilters? filters,
  });

  /// Fetches prediction accuracy metrics for model performance visualization
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for accuracy metrics
  /// - [modelIds]: Optional list of specific model IDs to analyze
  ///
  /// Returns:
  /// - [Right]: PredictionAccuracy containing performance metrics
  /// - [Left]: Failure if metrics retrieval fails
  Future<Either<Failure, PredictionAccuracy>> getPredictionAccuracyMetrics({
    required String region,
    required DateRange dateRange,
    List<String>? modelIds,
  });

  /// Fetches environmental trend data for climate visualization
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for environmental data
  /// - [factors]: Environmental factors to include (temperature, rainfall, etc.)
  /// - [aggregation]: Data aggregation method (daily, weekly, monthly)
  ///
  /// Returns:
  /// - [Right]: List of EnvironmentalTrend data points
  /// - [Left]: Failure if environmental data retrieval fails
  Future<Either<Failure, List<EnvironmentalTrend>>> getEnvironmentalTrends({
    required String region,
    required DateRange dateRange,
    List<EnvironmentalFactor>? factors,
    AggregationMethod aggregation = AggregationMethod.daily,
  });

  /// Fetches risk trend data for malaria risk visualization
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for risk data
  /// - [riskLevels]: Risk levels to include in results
  /// - [aggregation]: Data aggregation method
  ///
  /// Returns:
  /// - [Right]: List of RiskTrend data points
  /// - [Left]: Failure if risk data retrieval fails
  Future<Either<Failure, List<RiskTrend>>> getRiskTrends({
    required String region,
    required DateRange dateRange,
    List<RiskLevel>? riskLevels,
    AggregationMethod aggregation = AggregationMethod.daily,
  });

  /// Fetches alert statistics for notification system performance
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for alert statistics
  /// - [severityLevels]: Alert severity levels to include
  ///
  /// Returns:
  /// - [Right]: AlertStatistics containing notification performance data
  /// - [Left]: Failure if alert statistics retrieval fails
  Future<Either<Failure, AlertStatistics>> getAlertStatistics({
    required String region,
    required DateRange dateRange,
    List<AlertSeverity>? severityLevels,
  });

  /// Fetches data quality metrics for reliability assessment
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for quality assessment
  /// - [dataSources]: Specific data sources to evaluate
  ///
  /// Returns:
  /// - [Right]: DataQuality containing reliability metrics
  /// - [Left]: Failure if quality metrics retrieval fails
  Future<Either<Failure, DataQuality>> getDataQualityMetrics({
    required String region,
    required DateRange dateRange,
    List<String>? dataSources,
  });

  /// Generates line chart data for trend visualization
  ///
  /// Parameters:
  /// - [type]: Type of chart data to generate
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for chart data
  /// - [configuration]: Chart configuration options
  ///
  /// Returns:
  /// - [Right]: LineChartDataEntity ready for fl_chart visualization
  /// - [Left]: Failure if chart data generation fails
  Future<Either<Failure, LineChartDataEntity>> generateLineChartData({
    required ChartDataType type,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  });

  /// Generates bar chart data for categorical visualization
  ///
  /// Parameters:
  /// - [type]: Type of chart data to generate
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for chart data
  /// - [configuration]: Chart configuration options
  ///
  /// Returns:
  /// - [Right]: BarChartDataEntity ready for fl_chart visualization
  /// - [Left]: Failure if chart data generation fails
  Future<Either<Failure, BarChartDataEntity>> generateBarChartData({
    required ChartDataType type,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  });

  /// Generates pie chart data for proportion visualization
  ///
  /// Parameters:
  /// - [type]: Type of chart data to generate
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for chart data
  /// - [configuration]: Chart configuration options
  ///
  /// Returns:
  /// - [Right]: PieChartDataEntity ready for fl_chart visualization
  /// - [Left]: Failure if chart data generation fails
  Future<Either<Failure, PieChartDataEntity>> generatePieChartData({
    required ChartDataType type,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  });

  /// Generates scatter plot data for correlation visualization
  ///
  /// Parameters:
  /// - [xFactor]: Environmental factor for X-axis
  /// - [yFactor]: Environmental factor for Y-axis
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for scatter plot data
  /// - [configuration]: Chart configuration options
  ///
  /// Returns:
  /// - [Right]: ScatterPlotDataEntity ready for fl_chart visualization
  /// - [Left]: Failure if scatter plot data generation fails
  Future<Either<Failure, ScatterPlotDataEntity>> generateScatterPlotData({
    required EnvironmentalFactor xFactor,
    required EnvironmentalFactor yFactor,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  });

  /// Exports analytics data as a report in specified format
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for report data
  /// - [format]: Export format (PDF, CSV, JSON)
  /// - [includeCharts]: Whether to include chart visualizations
  /// - [sections]: Report sections to include
  ///
  /// Returns:
  /// - [Right]: String file path of generated report
  /// - [Left]: Failure if report generation fails
  Future<Either<Failure, String>> exportAnalyticsReport({
    required String region,
    required DateRange dateRange,
    required ExportFormat format,
    bool includeCharts = true,
    List<ReportSection>? sections,
  });

  /// Subscribes to real-time analytics data updates
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [updateInterval]: Update interval in seconds
  ///
  /// Returns:
  /// - Stream of AnalyticsData updates
  Stream<AnalyticsData> subscribeToRealTimeUpdates({
    required String region,
    int updateInterval = 60,
  });

  /// Gets available regions for analytics data
  ///
  /// Returns:
  /// - [Right]: List of available region identifiers
  /// - [Left]: Failure if region retrieval fails
  Future<Either<Failure, List<String>>> getAvailableRegions();

  /// Gets date range bounds for available data
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  ///
  /// Returns:
  /// - [Right]: DateRange representing available data bounds
  /// - [Left]: Failure if date range retrieval fails
  Future<Either<Failure, DateRange>> getDataDateRange({
    required String region,
  });
}

/// Analytics filters for customizing data retrieval
class AnalyticsFilters {
  /// Whether to include prediction accuracy data
  final bool includePredictions;

  /// Whether to include environmental trend data
  final bool includeEnvironmental;

  /// Whether to include risk trend data
  final bool includeRisk;

  /// Whether to include alert statistics
  final bool includeAlerts;

  /// Whether to include data quality metrics
  final bool includeDataQuality;

  /// Minimum confidence threshold for predictions (0.0 to 1.0)
  final double? minConfidence;

  /// Maximum data age in hours
  final int? maxDataAgeHours;

  const AnalyticsFilters({
    this.includePredictions = true,
    this.includeEnvironmental = true,
    this.includeRisk = true,
    this.includeAlerts = true,
    this.includeDataQuality = true,
    this.minConfidence,
    this.maxDataAgeHours,
  });
}

/// Chart configuration for customizing visualization
class ChartConfiguration {
  /// Chart title override
  final String? title;

  /// Chart subtitle override
  final String? subtitle;

  /// Custom color palette
  final List<Color>? colors;

  /// Chart width in pixels
  final double? width;

  /// Chart height in pixels
  final double? height;

  /// Whether to show legend
  final bool showLegend;

  /// Whether to show grid
  final bool showGrid;

  /// Whether to enable animations
  final bool enableAnimations;

  /// Animation duration in milliseconds
  final int animationDuration;

  const ChartConfiguration({
    this.title,
    this.subtitle,
    this.colors,
    this.width,
    this.height,
    this.showLegend = true,
    this.showGrid = true,
    this.enableAnimations = true,
    this.animationDuration = 1000,
  });
}

/// Data aggregation method enumeration
enum AggregationMethod {
  /// Raw data points without aggregation
  raw,

  /// Daily aggregation
  daily,

  /// Weekly aggregation
  weekly,

  /// Monthly aggregation
  monthly,

  /// Quarterly aggregation
  quarterly,

  /// Yearly aggregation
  yearly,
}

/// Chart data type enumeration
enum ChartDataType {
  /// Prediction accuracy trends
  predictionAccuracy,

  /// Environmental factor trends
  environmentalTrends,

  /// Risk level trends
  riskTrends,

  /// Alert statistics
  alertStatistics,

  /// Data quality metrics
  dataQuality,

  /// Risk level distribution
  riskDistribution,

  /// Environmental factor correlation
  environmentalCorrelation,

  /// Model performance comparison
  modelComparison,

  /// Temporal patterns
  temporalPatterns,
}

/// Export format enumeration
enum ExportFormat {
  /// Portable Document Format
  pdf,

  /// Comma-Separated Values
  csv,

  /// JavaScript Object Notation
  json,

  /// Microsoft Excel format
  xlsx,

  /// HyperText Markup Language
  html,
}

/// Report section enumeration
enum ReportSection {
  /// Executive summary
  summary,

  /// Prediction accuracy analysis
  predictionAccuracy,

  /// Environmental trends analysis
  environmentalTrends,

  /// Risk assessment analysis
  riskAnalysis,

  /// Alert system performance
  alertPerformance,

  /// Data quality assessment
  dataQuality,

  /// Recommendations and insights
  recommendations,
}

