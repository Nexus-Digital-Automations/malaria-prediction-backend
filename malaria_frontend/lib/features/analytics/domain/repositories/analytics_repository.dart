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
import '../../../../core/errors/failures.dart';
import '../entities/analytics_data.dart';
import '../entities/analytics_filters.dart';
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

