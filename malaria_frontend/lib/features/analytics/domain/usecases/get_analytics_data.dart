/// Use case for fetching comprehensive analytics data
///
/// This use case coordinates the retrieval of comprehensive analytics data
/// including prediction accuracy, environmental trends, risk assessments,
/// and system performance metrics for dashboard visualization.
///
/// Usage:
/// ```dart
/// final result = await getAnalyticsData(GetAnalyticsDataParams(
///   region: 'Kenya',
///   dateRange: DateRange(start: startDate, end: endDate),
///   filters: AnalyticsFilters(includePredictions: true),
/// ));
///
/// result.fold(
///   (failure) => handleError(failure),
///   (analyticsData) => displayDashboard(analyticsData),
/// );
/// ```
library;

import 'package:dartz/dartz.dart';
import 'package:equatable/equatable.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../entities/analytics_data.dart';
import '../repositories/analytics_repository.dart';

/// Use case for fetching comprehensive analytics data for dashboard display
class GetAnalyticsData implements UseCase<AnalyticsData, GetAnalyticsDataParams> {
  /// Analytics repository for data operations
  final AnalyticsRepository repository;

  /// Constructor requiring analytics repository dependency
  const GetAnalyticsData(this.repository);

  /// Executes analytics data retrieval with comprehensive error handling
  ///
  /// This method:
  /// 1. Validates input parameters for region and date range
  /// 2. Fetches analytics data from the repository
  /// 3. Performs data quality validation
  /// 4. Returns comprehensive analytics data or failure
  ///
  /// Parameters:
  /// - [params]: GetAnalyticsDataParams containing request details
  ///
  /// Returns:
  /// - [Right]: AnalyticsData with comprehensive analytics information
  /// - [Left]: Failure if data retrieval or validation fails
  @override
  Future<Either<Failure, AnalyticsData>> call(GetAnalyticsDataParams params) async {
    try {
      // Validate input parameters
      final validationResult = _validateParams(params);
      if (validationResult != null) {
        return Left(validationResult);
      }

      // Fetch analytics data from repository
      final result = await repository.getAnalyticsData(
        region: params.region,
        dateRange: params.dateRange,
        filters: params.filters,
      );

      // Return result with additional validation if successful
      return result.fold(
        (failure) => Left(failure),
        (analyticsData) => _validateAnalyticsData(analyticsData),
      );
    } catch (e) {
      // Handle unexpected errors during analytics data retrieval
      return Left(ServerFailure(
        message: 'Unexpected error during analytics data retrieval: ${e.toString()}',
        statusCode: 500,
      ),);
    }
  }

  /// Validates input parameters for analytics data request
  ///
  /// Performs comprehensive validation including:
  /// - Region identifier format and availability
  /// - Date range validity and bounds checking
  /// - Filter parameter validation
  ///
  /// Returns null if validation passes, Failure otherwise
  Failure? _validateParams(GetAnalyticsDataParams params) {
    // Validate region identifier
    if (params.region.isEmpty) {
      return const ValidationFailure(
        message: 'Region identifier cannot be empty',
        field: 'region',
      );
    }

    // Validate region format (basic validation)
    if (params.region.length < 2 || params.region.length > 100) {
      return const ValidationFailure(
        message: 'Region identifier must be between 2 and 100 characters',
        field: 'region',
      );
    }

    // Validate date range
    if (params.dateRange.start.isAfter(params.dateRange.end)) {
      return const ValidationFailure(
        message: 'Start date must be before end date',
        field: 'dateRange',
      );
    }

    // Validate date range duration (maximum 5 years for performance)
    const maxDuration = Duration(days: 365 * 5);
    if (params.dateRange.duration > maxDuration) {
      return const ValidationFailure(
        message: 'Date range cannot exceed 5 years for performance reasons',
        field: 'dateRange',
      );
    }

    // Validate date range is not too far in the future
    final maxFutureDate = DateTime.now().add(const Duration(days: 365));
    if (params.dateRange.start.isAfter(maxFutureDate)) {
      return const ValidationFailure(
        message: 'Date range cannot start more than 1 year in the future',
        field: 'dateRange',
      );
    }

    // Validate filters if provided
    if (params.filters != null) {
      final filterValidation = _validateFilters(params.filters!);
      if (filterValidation != null) {
        return filterValidation;
      }
    }

    return null;
  }

  /// Validates analytics filters for data retrieval
  ///
  /// Checks filter parameters including confidence thresholds
  /// and data age constraints for reasonable values
  ///
  /// Returns null if validation passes, Failure otherwise
  Failure? _validateFilters(AnalyticsFilters filters) {
    // Validate confidence threshold
    if (filters.minConfidence != null) {
      if (filters.minConfidence! < 0.0 || filters.minConfidence! > 1.0) {
        return const ValidationFailure(
          message: 'Minimum confidence must be between 0.0 and 1.0',
          field: 'minConfidence',
        );
      }
    }

    // Validate data age constraint
    if (filters.maxDataAgeHours != null) {
      if (filters.maxDataAgeHours! < 1 || filters.maxDataAgeHours! > 8760) {
        return const ValidationFailure(
          message: 'Maximum data age must be between 1 hour and 1 year',
          field: 'maxDataAgeHours',
        );
      }
    }

    // Validate at least one data type is included
    if (!filters.includePredictions &&
        !filters.includeEnvironmental &&
        !filters.includeRisk &&
        !filters.includeAlerts &&
        !filters.includeDataQuality) {
      return const ValidationFailure(
        message: 'At least one data type must be included in analytics request',
        field: 'filters',
      );
    }

    return null;
  }

  /// Validates retrieved analytics data for completeness and quality
  ///
  /// Performs comprehensive data validation including:
  /// - Data completeness checks
  /// - Quality threshold validation
  /// - Temporal consistency validation
  ///
  /// Returns validated analytics data or failure
  Either<Failure, AnalyticsData> _validateAnalyticsData(AnalyticsData data) {
    try {
      // Validate basic data completeness
      if (data.region.isEmpty) {
        return const Left(DataValidationFailure(
          message: 'Analytics data missing region information',
          field: 'region',
        ),);
      }

      // Validate data generation timestamp
      final now = DateTime.now();
      const maxAge = Duration(hours: 24);
      if (now.difference(data.generatedAt) > maxAge) {
        return const Left(DataValidationFailure(
          message: 'Analytics data is too old (over 24 hours)',
          field: 'generatedAt',
        ),);
      }

      // Validate prediction accuracy if included
      if (data.predictionAccuracy.overall < 0.0 || data.predictionAccuracy.overall > 1.0) {
        return const Left(DataValidationFailure(
          message: 'Invalid prediction accuracy value',
          field: 'predictionAccuracy',
        ),);
      }

      // Validate environmental trends data consistency
      if (data.environmentalTrends.isNotEmpty) {
        final invalidTrends = data.environmentalTrends.where(
          (trend) => trend.value.isNaN || trend.value.isInfinite,
        );
        if (invalidTrends.isNotEmpty) {
          return const Left(DataValidationFailure(
            message: 'Invalid environmental trend values detected',
            field: 'environmentalTrends',
          ),);
        }
      }

      // Validate risk trends data consistency
      if (data.riskTrends.isNotEmpty) {
        final invalidRiskTrends = data.riskTrends.where(
          (trend) => trend.riskScore < 0.0 || trend.riskScore > 1.0,
        );
        if (invalidRiskTrends.isNotEmpty) {
          return const Left(DataValidationFailure(
            message: 'Invalid risk score values detected',
            field: 'riskTrends',
          ),);
        }
      }

      // Validate data quality metrics
      if (data.dataQuality.completeness < 0.0 || data.dataQuality.completeness > 1.0) {
        return const Left(DataValidationFailure(
          message: 'Invalid data completeness value',
          field: 'dataQuality.completeness',
        ),);
      }

      if (data.dataQuality.accuracy < 0.0 || data.dataQuality.accuracy > 1.0) {
        return const Left(DataValidationFailure(
          message: 'Invalid data accuracy value',
          field: 'dataQuality.accuracy',
        ),);
      }

      // Data validation passed - return valid analytics data
      return Right(data);
    } catch (e) {
      return Left(DataValidationFailure(
        message: 'Error during analytics data validation: ${e.toString()}',
        field: 'validation',
      ),);
    }
  }
}

/// Parameters for analytics data retrieval use case
class GetAnalyticsDataParams extends Equatable {
  /// Geographic region identifier for analytics data
  final String region;

  /// Date range for analytics data retrieval
  final DateRange dateRange;

  /// Optional filters for customizing data retrieval
  final AnalyticsFilters? filters;

  /// Constructor for analytics data request parameters
  const GetAnalyticsDataParams({
    required this.region,
    required this.dateRange,
    this.filters,
  });

  /// Creates a copy of parameters with updated values
  GetAnalyticsDataParams copyWith({
    String? region,
    DateRange? dateRange,
    AnalyticsFilters? filters,
  }) {
    return GetAnalyticsDataParams(
      region: region ?? this.region,
      dateRange: dateRange ?? this.dateRange,
      filters: filters ?? this.filters,
    );
  }

  @override
  List<Object?> get props => [region, dateRange, filters];

  @override
  String toString() {
    return 'GetAnalyticsDataParams(region: $region, dateRange: $dateRange, filters: $filters)';
  }
}

/// Custom failure types for analytics data operations
class ValidationFailure extends Failure {
  /// The field that failed validation
  final String field;

  const ValidationFailure({
    required String message,
    required this.field,
  }) : super(message);

  @override
  List<Object?> get props => [message, field];
}

class DataValidationFailure extends Failure {
  /// The field that failed data validation
  final String field;

  const DataValidationFailure({
    required String message,
    required this.field,
  }) : super(message);

  @override
  List<Object?> get props => [message, field];
}

class ServerFailure extends Failure {
  /// HTTP status code if available
  final int? statusCode;

  const ServerFailure({
    required String message,
    this.statusCode,
  }) : super(message);

  @override
  List<Object?> get props => [message, statusCode];
}