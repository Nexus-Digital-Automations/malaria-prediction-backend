/// Remote data source for analytics data from malaria prediction backend API
///
/// This data source handles all network communication with the analytics
/// endpoints of the malaria prediction backend API, including fetching
/// comprehensive analytics data, generating chart data, and exporting reports.
///
/// Usage:
/// ```dart
/// final analyticsData = await remoteDataSource.getAnalyticsData(
///   region: 'Kenya',
///   startDate: DateTime.now().subtract(Duration(days: 30)),
///   endDate: DateTime.now(),
///   filters: {'include_predictions': true},
/// );
/// ```
library;

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../../../../core/errors/exceptions.dart';
import '../models/analytics_data_model.dart';

part 'analytics_remote_datasource.g.dart';

/// Abstract interface for analytics remote data source
abstract class AnalyticsRemoteDataSource {
  /// Fetches comprehensive analytics data for a specific region and date range
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier (e.g., 'Kenya', 'Tanzania')
  /// - [startDate]: Start date for analytics data retrieval
  /// - [endDate]: End date for analytics data retrieval
  /// - [filters]: Optional filters for customizing data retrieval
  ///
  /// Returns:
  /// - AnalyticsDataModel containing comprehensive analytics information
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  /// - [NetworkException]: If network connectivity issues occur
  /// - [ParseException]: If response data cannot be parsed
  Future<AnalyticsDataModel> getAnalyticsData({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    Map<String, dynamic>? filters,
  });

  /// Fetches prediction accuracy metrics for model performance visualization
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for accuracy metrics
  /// - [endDate]: End date for accuracy metrics
  /// - [modelIds]: Optional list of specific model IDs to analyze
  ///
  /// Returns:
  /// - PredictionAccuracyModel containing performance metrics
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<PredictionAccuracyModel> getPredictionAccuracyMetrics({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? modelIds,
  });

  /// Fetches environmental trend data for climate visualization
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for environmental data
  /// - [endDate]: End date for environmental data
  /// - [factors]: Environmental factors to include
  /// - [aggregation]: Data aggregation method
  ///
  /// Returns:
  /// - List of EnvironmentalTrendModel data points
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<List<EnvironmentalTrendModel>> getEnvironmentalTrends({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? factors,
    String? aggregation,
  });

  /// Fetches risk trend data for malaria risk visualization
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for risk data
  /// - [endDate]: End date for risk data
  /// - [riskLevels]: Risk levels to include in results
  /// - [aggregation]: Data aggregation method
  ///
  /// Returns:
  /// - List of RiskTrendModel data points
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<List<RiskTrendModel>> getRiskTrends({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? riskLevels,
    String? aggregation,
  });

  /// Fetches alert statistics for notification system performance
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for alert statistics
  /// - [endDate]: End date for alert statistics
  /// - [severityLevels]: Alert severity levels to include
  ///
  /// Returns:
  /// - AlertStatisticsModel containing notification performance data
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<AlertStatisticsModel> getAlertStatistics({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? severityLevels,
  });

  /// Fetches data quality metrics for reliability assessment
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for quality assessment
  /// - [endDate]: End date for quality assessment
  /// - [dataSources]: Specific data sources to evaluate
  ///
  /// Returns:
  /// - DataQualityModel containing reliability metrics
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<DataQualityModel> getDataQualityMetrics({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? dataSources,
  });

  /// Generates and fetches chart data for visualization
  ///
  /// Parameters:
  /// - [chartType]: Type of chart to generate (line, bar, pie, scatter)
  /// - [dataType]: Type of data to visualize
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for chart data
  /// - [endDate]: End date for chart data
  /// - [configuration]: Chart configuration options
  ///
  /// Returns:
  /// - Map containing chart data optimized for fl_chart
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<Map<String, dynamic>> generateChartData({
    required String chartType,
    required String dataType,
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    Map<String, dynamic>? configuration,
  });

  /// Exports analytics data as a report in specified format
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for report data
  /// - [endDate]: End date for report data
  /// - [format]: Export format (pdf, csv, json, xlsx)
  /// - [includeCharts]: Whether to include chart visualizations
  /// - [sections]: Report sections to include
  ///
  /// Returns:
  /// - String URL of generated report file
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<String> exportAnalyticsReport({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    required String format,
    bool includeCharts = true,
    List<String>? sections,
  });

  /// Gets available regions for analytics data
  ///
  /// Returns:
  /// - List of available region identifiers
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<List<String>> getAvailableRegions();

  /// Gets date range bounds for available data
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  ///
  /// Returns:
  /// - DateRangeModel representing available data bounds
  ///
  /// Throws:
  /// - [ServerException]: If API request fails or returns error
  Future<DateRangeModel> getDataDateRange({
    required String region,
  });
}

/// Retrofit-based implementation of analytics remote data source
@RestApi()
abstract class AnalyticsApiService {
  factory AnalyticsApiService(Dio dio, {String baseUrl}) = _AnalyticsApiService;

  /// Fetches comprehensive analytics data
  @GET('/analytics/data')
  Future<Map<String, dynamic>> getAnalyticsData(
    @Query('region') String region,
    @Query('start_date') String startDate,
    @Query('end_date') String endDate,
    @Queries() Map<String, dynamic>? filters,
  );

  /// Fetches prediction accuracy metrics
  @GET('/analytics/prediction-accuracy')
  Future<Map<String, dynamic>> getPredictionAccuracyMetrics(
    @Query('region') String region,
    @Query('start_date') String startDate,
    @Query('end_date') String endDate,
    @Query('model_ids') List<String>? modelIds,
  );

  /// Fetches environmental trend data
  @GET('/analytics/environmental-trends')
  Future<List<Map<String, dynamic>>> getEnvironmentalTrends(
    @Query('region') String region,
    @Query('start_date') String startDate,
    @Query('end_date') String endDate,
    @Query('factors') List<String>? factors,
    @Query('aggregation') String? aggregation,
  );

  /// Fetches risk trend data
  @GET('/analytics/risk-trends')
  Future<List<Map<String, dynamic>>> getRiskTrends(
    @Query('region') String region,
    @Query('start_date') String startDate,
    @Query('end_date') String endDate,
    @Query('risk_levels') List<String>? riskLevels,
    @Query('aggregation') String? aggregation,
  );

  /// Fetches alert statistics
  @GET('/analytics/alert-statistics')
  Future<Map<String, dynamic>> getAlertStatistics(
    @Query('region') String region,
    @Query('start_date') String startDate,
    @Query('end_date') String endDate,
    @Query('severity_levels') List<String>? severityLevels,
  );

  /// Fetches data quality metrics
  @GET('/analytics/data-quality')
  Future<Map<String, dynamic>> getDataQualityMetrics(
    @Query('region') String region,
    @Query('start_date') String startDate,
    @Query('end_date') String endDate,
    @Query('data_sources') List<String>? dataSources,
  );

  /// Generates chart data
  @POST('/analytics/charts/generate')
  Future<Map<String, dynamic>> generateChartData(
    @Body() Map<String, dynamic> request,
  );

  /// Exports analytics report
  @POST('/analytics/export')
  Future<Map<String, dynamic>> exportAnalyticsReport(
    @Body() Map<String, dynamic> request,
  );

  /// Gets available regions
  @GET('/analytics/regions')
  Future<List<String>> getAvailableRegions();

  /// Gets data date range for region
  @GET('/analytics/date-range')
  Future<Map<String, dynamic>> getDataDateRange(
    @Query('region') String region,
  );
}

/// Concrete implementation of analytics remote data source
class AnalyticsRemoteDataSourceImpl implements AnalyticsRemoteDataSource {
  /// Retrofit API service for making HTTP requests
  final AnalyticsApiService _apiService;

  /// Constructor requiring API service dependency
  const AnalyticsRemoteDataSourceImpl(this._apiService);

  @override
  Future<AnalyticsDataModel> getAnalyticsData({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    Map<String, dynamic>? filters,
  }) async {
    try {
      final response = await _apiService.getAnalyticsData(
        region,
        startDate.toIso8601String(),
        endDate.toIso8601String(),
        filters,
      );

      return AnalyticsDataModel.fromJson(response);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse analytics data response: ${e.toString()}',
      );
    }
  }

  @override
  Future<PredictionAccuracyModel> getPredictionAccuracyMetrics({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? modelIds,
  }) async {
    try {
      final response = await _apiService.getPredictionAccuracyMetrics(
        region,
        startDate.toIso8601String(),
        endDate.toIso8601String(),
        modelIds,
      );

      return PredictionAccuracyModel.fromJson(response);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse prediction accuracy response: ${e.toString()}',
      );
    }
  }

  @override
  Future<List<EnvironmentalTrendModel>> getEnvironmentalTrends({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? factors,
    String? aggregation,
  }) async {
    try {
      final response = await _apiService.getEnvironmentalTrends(
        region,
        startDate.toIso8601String(),
        endDate.toIso8601String(),
        factors,
        aggregation,
      );

      return response
          .map((json) => EnvironmentalTrendModel.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse environmental trends response: ${e.toString()}',
      );
    }
  }

  @override
  Future<List<RiskTrendModel>> getRiskTrends({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? riskLevels,
    String? aggregation,
  }) async {
    try {
      final response = await _apiService.getRiskTrends(
        region,
        startDate.toIso8601String(),
        endDate.toIso8601String(),
        riskLevels,
        aggregation,
      );

      return response
          .map((json) => RiskTrendModel.fromJson(json))
          .toList();
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse risk trends response: ${e.toString()}',
      );
    }
  }

  @override
  Future<AlertStatisticsModel> getAlertStatistics({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? severityLevels,
  }) async {
    try {
      final response = await _apiService.getAlertStatistics(
        region,
        startDate.toIso8601String(),
        endDate.toIso8601String(),
        severityLevels,
      );

      return AlertStatisticsModel.fromJson(response);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse alert statistics response: ${e.toString()}',
      );
    }
  }

  @override
  Future<DataQualityModel> getDataQualityMetrics({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    List<String>? dataSources,
  }) async {
    try {
      final response = await _apiService.getDataQualityMetrics(
        region,
        startDate.toIso8601String(),
        endDate.toIso8601String(),
        dataSources,
      );

      return DataQualityModel.fromJson(response);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse data quality response: ${e.toString()}',
      );
    }
  }

  @override
  Future<Map<String, dynamic>> generateChartData({
    required String chartType,
    required String dataType,
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    Map<String, dynamic>? configuration,
  }) async {
    try {
      final request = {
        'chart_type': chartType,
        'data_type': dataType,
        'region': region,
        'start_date': startDate.toIso8601String(),
        'end_date': endDate.toIso8601String(),
        if (configuration != null) 'configuration': configuration,
      };

      final response = await _apiService.generateChartData(request);
      return response;
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse chart data response: ${e.toString()}',
      );
    }
  }

  @override
  Future<String> exportAnalyticsReport({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
    required String format,
    bool includeCharts = true,
    List<String>? sections,
  }) async {
    try {
      final request = {
        'region': region,
        'start_date': startDate.toIso8601String(),
        'end_date': endDate.toIso8601String(),
        'format': format,
        'include_charts': includeCharts,
        if (sections != null) 'sections': sections,
      };

      final response = await _apiService.exportAnalyticsReport(request);
      return response['download_url'] as String;
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse export response: ${e.toString()}',
      );
    }
  }

  @override
  Future<List<String>> getAvailableRegions() async {
    try {
      return await _apiService.getAvailableRegions();
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse regions response: ${e.toString()}',
      );
    }
  }

  @override
  Future<DateRangeModel> getDataDateRange({
    required String region,
  }) async {
    try {
      final response = await _apiService.getDataDateRange(region);
      return DateRangeModel.fromJson(response);
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ParseException(
        'Failed to parse date range response: ${e.toString()}',
      );
    }
  }

  /// Handles Dio exceptions and converts to appropriate app exceptions
  ///
  /// Provides comprehensive error handling for different types of HTTP
  /// and network errors with user-friendly error messages
  Exception _handleDioException(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const NetworkException(
          'Request timeout. Please check your internet connection.',
        );

      case DioExceptionType.connectionError:
        return const NetworkException(
          'Unable to connect to server. Please check your internet connection.',
        );

      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode ?? 0;
        final errorMessage = _getErrorMessageFromResponse(e.response);

        if (statusCode >= 500) {
          return const ServerException(
            'Server error occurred. Please try again later.',
          );
        } else if (statusCode == 404) {
          return const ServerException(
            'Analytics data not found for the specified region and date range.',
          );
        } else if (statusCode == 401) {
          return const ServerException(
            'Authentication required. Please log in again.',
          );
        } else if (statusCode == 403) {
          return const ServerException(
            'Access denied. You do not have permission to access this data.',
          );
        } else {
          return ServerException(
            errorMessage ?? 'An error occurred while fetching analytics data.',
          );
        }

      case DioExceptionType.cancel:
        return const NetworkException(
          'Request was cancelled.',
        );

      case DioExceptionType.unknown:
      default:
        return NetworkException(
          'An unexpected error occurred: ${e.message}',
        );
    }
  }

  /// Extracts error message from HTTP response
  ///
  /// Attempts to parse error messages from API response body
  /// for more specific error reporting to users
  String? _getErrorMessageFromResponse(Response? response) {
    if (response?.data is Map<String, dynamic>) {
      final data = response!.data as Map<String, dynamic>;
      return data['message'] as String? ??
             data['error'] as String? ??
             data['detail'] as String?;
    }
    return null;
  }
}