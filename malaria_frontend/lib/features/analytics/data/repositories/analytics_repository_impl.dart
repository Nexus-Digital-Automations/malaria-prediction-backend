/// Analytics repository implementation coordinating local and remote data sources
///
/// This repository implementation provides a unified interface for analytics data
/// operations, coordinating between remote API calls and local caching for
/// optimal performance and offline functionality.
///
/// Usage:
/// ```dart
/// final analyticsData = await repository.getAnalyticsData(
///   region: 'Kenya',
///   dateRange: DateRange(start: startDate, end: endDate),
///   filters: AnalyticsFilters(includePredictions: true),
/// );
/// ```

import 'package:dartz/dartz.dart';
import 'package:flutter/material.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/network/network_info.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/chart_data.dart';
import '../../domain/repositories/analytics_repository.dart';
import '../datasources/analytics_local_datasource.dart';
import '../datasources/analytics_remote_datasource.dart';
import '../models/analytics_data_model.dart';

/// Implementation of analytics repository using local and remote data sources
class AnalyticsRepositoryImpl implements AnalyticsRepository {
  /// Remote data source for API communication
  final AnalyticsRemoteDataSource _remoteDataSource;

  /// Local data source for caching
  final AnalyticsLocalDataSource _localDataSource;

  /// Network connectivity checker
  final NetworkInfo _networkInfo;

  /// Constructor requiring data sources and network info
  const AnalyticsRepositoryImpl({
    required AnalyticsRemoteDataSource remoteDataSource,
    required AnalyticsLocalDataSource localDataSource,
    required NetworkInfo networkInfo,
  })  : _remoteDataSource = remoteDataSource,
        _localDataSource = localDataSource,
        _networkInfo = networkInfo;

  @override
  Future<Either<Failure, AnalyticsData>> getAnalyticsData({
    required String region,
    required DateRange dateRange,
    AnalyticsFilters? filters,
  }) async {
    try {
      // Check if device is connected to internet
      if (await _networkInfo.isConnected) {
        return await _getAnalyticsDataFromRemote(region, dateRange, filters);
      } else {
        return await _getAnalyticsDataFromCache(region, dateRange);
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during analytics data retrieval: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, PredictionAccuracy>> getPredictionAccuracyMetrics({
    required String region,
    required DateRange dateRange,
    List<String>? modelIds,
  }) async {
    try {
      if (await _networkInfo.isConnected) {
        return await _getPredictionAccuracyFromRemote(region, dateRange, modelIds);
      } else {
        return await _getPredictionAccuracyFromCache(region, dateRange);
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during prediction accuracy retrieval: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, List<EnvironmentalTrend>>> getEnvironmentalTrends({
    required String region,
    required DateRange dateRange,
    List<EnvironmentalFactor>? factors,
    AggregationMethod aggregation = AggregationMethod.daily,
  }) async {
    try {
      if (await _networkInfo.isConnected) {
        return await _getEnvironmentalTrendsFromRemote(
          region,
          dateRange,
          factors,
          aggregation,
        );
      } else {
        return await _getEnvironmentalTrendsFromCache(region, dateRange);
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during environmental trends retrieval: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, List<RiskTrend>>> getRiskTrends({
    required String region,
    required DateRange dateRange,
    List<RiskLevel>? riskLevels,
    AggregationMethod aggregation = AggregationMethod.daily,
  }) async {
    try {
      if (await _networkInfo.isConnected) {
        return await _getRiskTrendsFromRemote(region, dateRange, riskLevels, aggregation);
      } else {
        return await _getRiskTrendsFromCache(region, dateRange);
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during risk trends retrieval: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, AlertStatistics>> getAlertStatistics({
    required String region,
    required DateRange dateRange,
    List<AlertSeverity>? severityLevels,
  }) async {
    try {
      if (await _networkInfo.isConnected) {
        return await _getAlertStatisticsFromRemote(region, dateRange, severityLevels);
      } else {
        return Left(const NetworkFailure(
          message: 'Alert statistics require internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during alert statistics retrieval: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, DataQuality>> getDataQualityMetrics({
    required String region,
    required DateRange dateRange,
    List<String>? dataSources,
  }) async {
    try {
      if (await _networkInfo.isConnected) {
        return await _getDataQualityFromRemote(region, dateRange, dataSources);
      } else {
        return Left(const NetworkFailure(
          message: 'Data quality metrics require internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during data quality retrieval: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, LineChartDataEntity>> generateLineChartData({
    required ChartDataType type,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  }) async {
    try {
      final chartKey = _generateChartCacheKey('line', type.name, region, dateRange);

      // Try to get from cache first
      final cachedChartData = await _localDataSource.getCachedChartData(chartKey);
      if (cachedChartData != null) {
        return Right(_parseLineChartData(cachedChartData));
      }

      // Fetch from remote if network available
      if (await _networkInfo.isConnected) {
        return await _generateLineChartFromRemote(type, region, dateRange, configuration);
      } else {
        return Left(const NetworkFailure(
          message: 'Chart generation requires internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during line chart generation: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, BarChartDataEntity>> generateBarChartData({
    required ChartDataType type,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  }) async {
    try {
      final chartKey = _generateChartCacheKey('bar', type.name, region, dateRange);

      // Try to get from cache first
      final cachedChartData = await _localDataSource.getCachedChartData(chartKey);
      if (cachedChartData != null) {
        return Right(_parseBarChartData(cachedChartData));
      }

      // Fetch from remote if network available
      if (await _networkInfo.isConnected) {
        return await _generateBarChartFromRemote(type, region, dateRange, configuration);
      } else {
        return Left(const NetworkFailure(
          message: 'Chart generation requires internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during bar chart generation: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, PieChartDataEntity>> generatePieChartData({
    required ChartDataType type,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  }) async {
    try {
      final chartKey = _generateChartCacheKey('pie', type.name, region, dateRange);

      // Try to get from cache first
      final cachedChartData = await _localDataSource.getCachedChartData(chartKey);
      if (cachedChartData != null) {
        return Right(_parsePieChartData(cachedChartData));
      }

      // Fetch from remote if network available
      if (await _networkInfo.isConnected) {
        return await _generatePieChartFromRemote(type, region, dateRange, configuration);
      } else {
        return Left(const NetworkFailure(
          message: 'Chart generation requires internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during pie chart generation: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, ScatterPlotDataEntity>> generateScatterPlotData({
    required EnvironmentalFactor xFactor,
    required EnvironmentalFactor yFactor,
    required String region,
    required DateRange dateRange,
    ChartConfiguration? configuration,
  }) async {
    try {
      final chartKey = _generateScatterPlotCacheKey(
        xFactor.name,
        yFactor.name,
        region,
        dateRange,
      );

      // Try to get from cache first
      final cachedChartData = await _localDataSource.getCachedChartData(chartKey);
      if (cachedChartData != null) {
        return Right(_parseScatterPlotData(cachedChartData));
      }

      // Fetch from remote if network available
      if (await _networkInfo.isConnected) {
        return await _generateScatterPlotFromRemote(
          xFactor,
          yFactor,
          region,
          dateRange,
          configuration,
        );
      } else {
        return Left(const NetworkFailure(
          message: 'Chart generation requires internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during scatter plot generation: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, String>> exportAnalyticsReport({
    required String region,
    required DateRange dateRange,
    required ExportFormat format,
    bool includeCharts = true,
    List<ReportSection>? sections,
  }) async {
    try {
      if (await _networkInfo.isConnected) {
        final reportUrl = await _remoteDataSource.exportAnalyticsReport(
          region: region,
          startDate: dateRange.start,
          endDate: dateRange.end,
          format: format.name,
          includeCharts: includeCharts,
          sections: sections?.map((s) => s.name).toList(),
        );

        return Right(reportUrl);
      } else {
        return Left(const NetworkFailure(
          message: 'Report export requires internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during report export: ${e.toString()}',
      ));
    }
  }

  @override
  Stream<AnalyticsData> subscribeToRealTimeUpdates({
    required String region,
    int updateInterval = 60,
  }) {
    // TODO: Implement WebSocket subscription for real-time updates
    // This would require WebSocket implementation in the remote data source
    throw UnimplementedError('Real-time updates not yet implemented');
  }

  @override
  Future<Either<Failure, List<String>>> getAvailableRegions() async {
    try {
      // Try to get from cache first
      final cachedRegions = await _localDataSource.getCachedAvailableRegions();
      if (cachedRegions != null) {
        return Right(cachedRegions);
      }

      // Fetch from remote if network available
      if (await _networkInfo.isConnected) {
        final regions = await _remoteDataSource.getAvailableRegions();
        await _localDataSource.cacheAvailableRegions(regions, ttl: 168); // 1 week
        return Right(regions);
      } else {
        return Left(const NetworkFailure(
          message: 'Available regions require internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during regions retrieval: ${e.toString()}',
      ));
    }
  }

  @override
  Future<Either<Failure, DateRange>> getDataDateRange({
    required String region,
  }) async {
    try {
      if (await _networkInfo.isConnected) {
        final dateRangeModel = await _remoteDataSource.getDataDateRange(region: region);
        return Right(dateRangeModel.toEntity());
      } else {
        return Left(const NetworkFailure(
          message: 'Data date range requires internet connection',
        ));
      }
    } catch (e) {
      return Left(ServerFailure(
        message: 'Unexpected error during date range retrieval: ${e.toString()}',
      ));
    }
  }

  /// Fetches analytics data from remote source with caching
  Future<Either<Failure, AnalyticsData>> _getAnalyticsDataFromRemote(
    String region,
    DateRange dateRange,
    AnalyticsFilters? filters,
  ) async {
    try {
      final filtersMap = _convertFiltersToMap(filters);
      final analyticsDataModel = await _remoteDataSource.getAnalyticsData(
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        filters: filtersMap,
      );

      // Cache the result for offline access
      await _localDataSource.cacheAnalyticsData(analyticsDataModel, ttl: 24);

      return Right(analyticsDataModel.toEntity());
    } catch (e) {
      // If remote fails, try to get from cache as fallback
      return await _getAnalyticsDataFromCache(region, dateRange);
    }
  }

  /// Fetches analytics data from local cache
  Future<Either<Failure, AnalyticsData>> _getAnalyticsDataFromCache(
    String region,
    DateRange dateRange,
  ) async {
    try {
      final cachedData = await _localDataSource.getCachedAnalyticsData(
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
      );

      if (cachedData != null) {
        return Right(cachedData.toEntity());
      } else {
        return Left(const CacheFailure(
          message: 'No cached analytics data available for offline access',
        ));
      }
    } catch (e) {
      return Left(CacheFailure(
        message: 'Failed to retrieve cached analytics data: ${e.toString()}',
      ));
    }
  }

  /// Fetches prediction accuracy from remote source with caching
  Future<Either<Failure, PredictionAccuracy>> _getPredictionAccuracyFromRemote(
    String region,
    DateRange dateRange,
    List<String>? modelIds,
  ) async {
    try {
      final accuracyModel = await _remoteDataSource.getPredictionAccuracyMetrics(
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        modelIds: modelIds,
      );

      // Cache the result
      final dateRangeKey = _generateDateRangeKey(dateRange);
      await _localDataSource.cachePredictionAccuracy(accuracyModel, region, dateRangeKey);

      return Right(accuracyModel.toEntity());
    } catch (e) {
      return await _getPredictionAccuracyFromCache(region, dateRange);
    }
  }

  /// Fetches prediction accuracy from local cache
  Future<Either<Failure, PredictionAccuracy>> _getPredictionAccuracyFromCache(
    String region,
    DateRange dateRange,
  ) async {
    try {
      final dateRangeKey = _generateDateRangeKey(dateRange);
      final cachedData = await _localDataSource.getCachedPredictionAccuracy(
        region,
        dateRangeKey,
      );

      if (cachedData != null) {
        return Right(cachedData.toEntity());
      } else {
        return Left(const CacheFailure(
          message: 'No cached prediction accuracy data available',
        ));
      }
    } catch (e) {
      return Left(CacheFailure(
        message: 'Failed to retrieve cached prediction accuracy: ${e.toString()}',
      ));
    }
  }

  /// Fetches environmental trends from remote source with caching
  Future<Either<Failure, List<EnvironmentalTrend>>> _getEnvironmentalTrendsFromRemote(
    String region,
    DateRange dateRange,
    List<EnvironmentalFactor>? factors,
    AggregationMethod aggregation,
  ) async {
    try {
      final factorNames = factors?.map((f) => f.name).toList();
      final trendsModels = await _remoteDataSource.getEnvironmentalTrends(
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        factors: factorNames,
        aggregation: aggregation.name,
      );

      // Cache the result
      final dateRangeKey = _generateDateRangeKey(dateRange);
      await _localDataSource.cacheEnvironmentalTrends(trendsModels, region, dateRangeKey);

      return Right(trendsModels.map((model) => model.toEntity()).toList());
    } catch (e) {
      return await _getEnvironmentalTrendsFromCache(region, dateRange);
    }
  }

  /// Fetches environmental trends from local cache
  Future<Either<Failure, List<EnvironmentalTrend>>> _getEnvironmentalTrendsFromCache(
    String region,
    DateRange dateRange,
  ) async {
    try {
      final dateRangeKey = _generateDateRangeKey(dateRange);
      final cachedData = await _localDataSource.getCachedEnvironmentalTrends(
        region,
        dateRangeKey,
      );

      if (cachedData != null) {
        return Right(cachedData.map((model) => model.toEntity()).toList());
      } else {
        return Left(const CacheFailure(
          message: 'No cached environmental trends available',
        ));
      }
    } catch (e) {
      return Left(CacheFailure(
        message: 'Failed to retrieve cached environmental trends: ${e.toString()}',
      ));
    }
  }

  /// Fetches risk trends from remote source with caching
  Future<Either<Failure, List<RiskTrend>>> _getRiskTrendsFromRemote(
    String region,
    DateRange dateRange,
    List<RiskLevel>? riskLevels,
    AggregationMethod aggregation,
  ) async {
    try {
      final riskLevelNames = riskLevels?.map((r) => r.name).toList();
      final trendsModels = await _remoteDataSource.getRiskTrends(
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        riskLevels: riskLevelNames,
        aggregation: aggregation.name,
      );

      // Cache the result
      final dateRangeKey = _generateDateRangeKey(dateRange);
      await _localDataSource.cacheRiskTrends(trendsModels, region, dateRangeKey);

      return Right(trendsModels.map((model) => model.toEntity()).toList());
    } catch (e) {
      return await _getRiskTrendsFromCache(region, dateRange);
    }
  }

  /// Fetches risk trends from local cache
  Future<Either<Failure, List<RiskTrend>>> _getRiskTrendsFromCache(
    String region,
    DateRange dateRange,
  ) async {
    try {
      final dateRangeKey = _generateDateRangeKey(dateRange);
      final cachedData = await _localDataSource.getCachedRiskTrends(region, dateRangeKey);

      if (cachedData != null) {
        return Right(cachedData.map((model) => model.toEntity()).toList());
      } else {
        return Left(const CacheFailure(
          message: 'No cached risk trends available',
        ));
      }
    } catch (e) {
      return Left(CacheFailure(
        message: 'Failed to retrieve cached risk trends: ${e.toString()}',
      ));
    }
  }

  /// Fetches alert statistics from remote source (no caching for real-time data)
  Future<Either<Failure, AlertStatistics>> _getAlertStatisticsFromRemote(
    String region,
    DateRange dateRange,
    List<AlertSeverity>? severityLevels,
  ) async {
    try {
      final severityNames = severityLevels?.map((s) => s.name).toList();
      final statisticsModel = await _remoteDataSource.getAlertStatistics(
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        severityLevels: severityNames,
      );

      return Right(statisticsModel.toEntity());
    } catch (e) {
      return Left(ServerFailure(
        message: 'Failed to fetch alert statistics: ${e.toString()}',
      ));
    }
  }

  /// Fetches data quality metrics from remote source (no caching for real-time data)
  Future<Either<Failure, DataQuality>> _getDataQualityFromRemote(
    String region,
    DateRange dateRange,
    List<String>? dataSources,
  ) async {
    try {
      final qualityModel = await _remoteDataSource.getDataQualityMetrics(
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        dataSources: dataSources,
      );

      return Right(qualityModel.toEntity());
    } catch (e) {
      return Left(ServerFailure(
        message: 'Failed to fetch data quality metrics: ${e.toString()}',
      ));
    }
  }

  /// Generates line chart from remote source with caching
  Future<Either<Failure, LineChartDataEntity>> _generateLineChartFromRemote(
    ChartDataType type,
    String region,
    DateRange dateRange,
    ChartConfiguration? configuration,
  ) async {
    try {
      final configMap = _convertConfigurationToMap(configuration);
      final chartData = await _remoteDataSource.generateChartData(
        chartType: 'line',
        dataType: type.name,
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        configuration: configMap,
      );

      // Cache the result
      final chartKey = _generateChartCacheKey('line', type.name, region, dateRange);
      await _localDataSource.cacheChartData(chartData, chartKey);

      return Right(_parseLineChartData(chartData));
    } catch (e) {
      return Left(ServerFailure(
        message: 'Failed to generate line chart: ${e.toString()}',
      ));
    }
  }

  /// Generates bar chart from remote source with caching
  Future<Either<Failure, BarChartDataEntity>> _generateBarChartFromRemote(
    ChartDataType type,
    String region,
    DateRange dateRange,
    ChartConfiguration? configuration,
  ) async {
    try {
      final configMap = _convertConfigurationToMap(configuration);
      final chartData = await _remoteDataSource.generateChartData(
        chartType: 'bar',
        dataType: type.name,
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        configuration: configMap,
      );

      // Cache the result
      final chartKey = _generateChartCacheKey('bar', type.name, region, dateRange);
      await _localDataSource.cacheChartData(chartData, chartKey);

      return Right(_parseBarChartData(chartData));
    } catch (e) {
      return Left(ServerFailure(
        message: 'Failed to generate bar chart: ${e.toString()}',
      ));
    }
  }

  /// Generates pie chart from remote source with caching
  Future<Either<Failure, PieChartDataEntity>> _generatePieChartFromRemote(
    ChartDataType type,
    String region,
    DateRange dateRange,
    ChartConfiguration? configuration,
  ) async {
    try {
      final configMap = _convertConfigurationToMap(configuration);
      final chartData = await _remoteDataSource.generateChartData(
        chartType: 'pie',
        dataType: type.name,
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        configuration: configMap,
      );

      // Cache the result
      final chartKey = _generateChartCacheKey('pie', type.name, region, dateRange);
      await _localDataSource.cacheChartData(chartData, chartKey);

      return Right(_parsePieChartData(chartData));
    } catch (e) {
      return Left(ServerFailure(
        message: 'Failed to generate pie chart: ${e.toString()}',
      ));
    }
  }

  /// Generates scatter plot from remote source with caching
  Future<Either<Failure, ScatterPlotDataEntity>> _generateScatterPlotFromRemote(
    EnvironmentalFactor xFactor,
    EnvironmentalFactor yFactor,
    String region,
    DateRange dateRange,
    ChartConfiguration? configuration,
  ) async {
    try {
      final configMap = _convertConfigurationToMap(configuration);
      configMap?['x_factor'] = xFactor.name;
      configMap?['y_factor'] = yFactor.name;

      final chartData = await _remoteDataSource.generateChartData(
        chartType: 'scatter',
        dataType: 'environmental_correlation',
        region: region,
        startDate: dateRange.start,
        endDate: dateRange.end,
        configuration: configMap,
      );

      // Cache the result
      final chartKey = _generateScatterPlotCacheKey(
        xFactor.name,
        yFactor.name,
        region,
        dateRange,
      );
      await _localDataSource.cacheChartData(chartData, chartKey);

      return Right(_parseScatterPlotData(chartData));
    } catch (e) {
      return Left(ServerFailure(
        message: 'Failed to generate scatter plot: ${e.toString()}',
      ));
    }
  }

  /// Converts analytics filters to map for API communication
  Map<String, dynamic>? _convertFiltersToMap(AnalyticsFilters? filters) {
    if (filters == null) return null;

    return {
      'include_predictions': filters.includePredictions,
      'include_environmental': filters.includeEnvironmental,
      'include_risk': filters.includeRisk,
      'include_alerts': filters.includeAlerts,
      'include_data_quality': filters.includeDataQuality,
      if (filters.minConfidence != null) 'min_confidence': filters.minConfidence,
      if (filters.maxDataAgeHours != null) 'max_data_age_hours': filters.maxDataAgeHours,
    };
  }

  /// Converts chart configuration to map for API communication
  Map<String, dynamic>? _convertConfigurationToMap(ChartConfiguration? configuration) {
    if (configuration == null) return null;

    return {
      if (configuration.title != null) 'title': configuration.title,
      if (configuration.subtitle != null) 'subtitle': configuration.subtitle,
      if (configuration.colors != null)
        'colors': configuration.colors!.map((c) => c.value).toList(),
      if (configuration.width != null) 'width': configuration.width,
      if (configuration.height != null) 'height': configuration.height,
      'show_legend': configuration.showLegend,
      'show_grid': configuration.showGrid,
      'enable_animations': configuration.enableAnimations,
      'animation_duration': configuration.animationDuration,
    };
  }

  /// Generates cache key for chart data
  String _generateChartCacheKey(
    String chartType,
    String dataType,
    String region,
    DateRange dateRange,
  ) {
    final startDate = dateRange.start.toIso8601String().split('T')[0];
    final endDate = dateRange.end.toIso8601String().split('T')[0];
    return 'chart_${chartType}_${dataType}_${region}_${startDate}_$endDate';
  }

  /// Generates cache key for scatter plot data
  String _generateScatterPlotCacheKey(
    String xFactor,
    String yFactor,
    String region,
    DateRange dateRange,
  ) {
    final startDate = dateRange.start.toIso8601String().split('T')[0];
    final endDate = dateRange.end.toIso8601String().split('T')[0];
    return 'scatter_${xFactor}_${yFactor}_${region}_${startDate}_$endDate';
  }

  /// Generates date range key for caching
  String _generateDateRangeKey(DateRange dateRange) {
    final startDate = dateRange.start.toIso8601String().split('T')[0];
    final endDate = dateRange.end.toIso8601String().split('T')[0];
    return '${startDate}_$endDate';
  }

  /// Parses chart data response to LineChartDataEntity
  LineChartDataEntity _parseLineChartData(Map<String, dynamic> chartData) {
    // Implementation would parse the chart data from API response
    // This is a simplified version - actual implementation would be more complex
    return LineChartDataEntity(
      title: chartData['title'] as String? ?? 'Chart',
      subtitle: chartData['subtitle'] as String?,
      series: [], // Parse series data from chartData
      xAxis: _parseChartAxis(chartData['x_axis']),
      yAxis: _parseChartAxis(chartData['y_axis']),
      style: _parseChartStyle(chartData['style']),
    );
  }

  /// Parses chart data response to BarChartDataEntity
  BarChartDataEntity _parseBarChartData(Map<String, dynamic> chartData) {
    return BarChartDataEntity(
      title: chartData['title'] as String? ?? 'Chart',
      subtitle: chartData['subtitle'] as String?,
      dataGroups: [], // Parse data groups from chartData
      xAxis: _parseChartAxis(chartData['x_axis']),
      yAxis: _parseChartAxis(chartData['y_axis']),
      style: _parseChartStyle(chartData['style']),
    );
  }

  /// Parses chart data response to PieChartDataEntity
  PieChartDataEntity _parsePieChartData(Map<String, dynamic> chartData) {
    return PieChartDataEntity(
      title: chartData['title'] as String? ?? 'Chart',
      subtitle: chartData['subtitle'] as String?,
      sections: [], // Parse sections from chartData
      style: _parseChartStyle(chartData['style']),
    );
  }

  /// Parses chart data response to ScatterPlotDataEntity
  ScatterPlotDataEntity _parseScatterPlotData(Map<String, dynamic> chartData) {
    return ScatterPlotDataEntity(
      title: chartData['title'] as String? ?? 'Chart',
      subtitle: chartData['subtitle'] as String?,
      series: [], // Parse series from chartData
      xAxis: _parseChartAxis(chartData['x_axis']),
      yAxis: _parseChartAxis(chartData['y_axis']),
      style: _parseChartStyle(chartData['style']),
    );
  }

  /// Parses chart axis data
  ChartAxis _parseChartAxis(dynamic axisData) {
    if (axisData == null) {
      return const ChartAxis(title: 'Axis');
    }

    final axis = axisData as Map<String, dynamic>;
    return ChartAxis(
      title: axis['title'] as String? ?? 'Axis',
      min: axis['min'] as double?,
      max: axis['max'] as double?,
      interval: axis['interval'] as double?,
    );
  }

  /// Parses chart style data
  ChartStyle _parseChartStyle(dynamic styleData) {
    // Simplified style parsing - actual implementation would be more comprehensive
    return ChartStyle(
      backgroundColor: Colors.transparent,
      textTheme: ThemeData.light().textTheme,
    );
  }
}