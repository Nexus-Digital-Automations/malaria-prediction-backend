/// Analytics BLoC for managing analytics dashboard state
///
/// This BLoC handles all analytics-related state management including
/// fetching analytics data, generating charts, applying filters,
/// and managing dashboard interactions using the BLoC pattern.
///
/// Usage:
/// ```dart
/// // Fetch analytics data
/// context.read<AnalyticsBloc>().add(LoadAnalyticsData(
///   region: 'Kenya',
///   dateRange: DateRange(start: startDate, end: endDate),
/// ));
///
/// // Generate chart
/// context.read<AnalyticsBloc>().add(GenerateChart(
///   chartType: ChartType.lineChart,
///   dataType: ChartDataType.predictionAccuracy,
/// ));
/// ```

import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/chart_data.dart';
import '../../domain/usecases/get_analytics_data.dart';
import '../../domain/usecases/generate_chart_data.dart';
import '../../domain/repositories/analytics_repository.dart';

/// Events for analytics BLoC
abstract class AnalyticsEvent extends Equatable {
  const AnalyticsEvent();

  @override
  List<Object?> get props => [];
}

/// Event to load comprehensive analytics data
class LoadAnalyticsData extends AnalyticsEvent {
  /// Geographic region identifier
  final String region;

  /// Date range for analytics data
  final DateRange dateRange;

  /// Optional filters for data customization
  final AnalyticsFilters? filters;

  const LoadAnalyticsData({
    required this.region,
    required this.dateRange,
    this.filters,
  });

  @override
  List<Object?> get props => [region, dateRange, filters];

  @override
  String toString() => 'LoadAnalyticsData(region: $region, dateRange: $dateRange)';
}

/// Event to generate chart data for visualization
class GenerateChart extends AnalyticsEvent {
  /// Type of chart to generate
  final ChartType chartType;

  /// Type of data to visualize
  final ChartDataType dataType;

  /// Geographic region identifier
  final String region;

  /// Date range for chart data
  final DateRange dateRange;

  /// Optional chart configuration
  final ChartConfiguration? configuration;

  /// X-axis factor for scatter plots
  final EnvironmentalFactor? xFactor;

  /// Y-axis factor for scatter plots
  final EnvironmentalFactor? yFactor;

  const GenerateChart({
    required this.chartType,
    required this.dataType,
    required this.region,
    required this.dateRange,
    this.configuration,
    this.xFactor,
    this.yFactor,
  });

  @override
  List<Object?> get props => [
        chartType,
        dataType,
        region,
        dateRange,
        configuration,
        xFactor,
        yFactor,
      ];

  @override
  String toString() => 'GenerateChart(type: $chartType, data: $dataType)';
}

/// Event to apply filters to analytics data
class ApplyFilters extends AnalyticsEvent {
  /// Analytics filters to apply
  final AnalyticsFilters filters;

  /// Whether to reload data with new filters
  final bool reloadData;

  const ApplyFilters({
    required this.filters,
    this.reloadData = true,
  });

  @override
  List<Object?> get props => [filters, reloadData];

  @override
  String toString() => 'ApplyFilters(filters: $filters, reload: $reloadData)';
}

/// Event to change selected region
class ChangeRegion extends AnalyticsEvent {
  /// New region to select
  final String region;

  /// Whether to reload data for new region
  final bool reloadData;

  const ChangeRegion({
    required this.region,
    this.reloadData = true,
  });

  @override
  List<Object?> get props => [region, reloadData];

  @override
  String toString() => 'ChangeRegion(region: $region, reload: $reloadData)';
}

/// Event to change date range
class ChangeDateRange extends AnalyticsEvent {
  /// New date range to select
  final DateRange dateRange;

  /// Whether to reload data for new date range
  final bool reloadData;

  const ChangeDateRange({
    required this.dateRange,
    this.reloadData = true,
  });

  @override
  List<Object?> get props => [dateRange, reloadData];

  @override
  String toString() => 'ChangeDateRange(dateRange: $dateRange, reload: $reloadData)';
}

/// Event to refresh analytics data
class RefreshAnalyticsData extends AnalyticsEvent {
  const RefreshAnalyticsData();

  @override
  String toString() => 'RefreshAnalyticsData()';
}

/// Event to export analytics report
class ExportAnalyticsReport extends AnalyticsEvent {
  /// Export format
  final ExportFormat format;

  /// Whether to include charts in export
  final bool includeCharts;

  /// Report sections to include
  final List<ReportSection>? sections;

  const ExportAnalyticsReport({
    required this.format,
    this.includeCharts = true,
    this.sections,
  });

  @override
  List<Object?> get props => [format, includeCharts, sections];

  @override
  String toString() => 'ExportAnalyticsReport(format: $format)';
}

/// Event to load available regions
class LoadAvailableRegions extends AnalyticsEvent {
  const LoadAvailableRegions();

  @override
  String toString() => 'LoadAvailableRegions()';
}

/// Event to clear analytics data
class ClearAnalyticsData extends AnalyticsEvent {
  const ClearAnalyticsData();

  @override
  String toString() => 'ClearAnalyticsData()';
}

/// States for analytics BLoC
abstract class AnalyticsState extends Equatable {
  const AnalyticsState();

  @override
  List<Object?> get props => [];
}

/// Initial state
class AnalyticsInitial extends AnalyticsState {
  const AnalyticsInitial();

  @override
  String toString() => 'AnalyticsInitial()';
}

/// Loading state for analytics data
class AnalyticsLoading extends AnalyticsState {
  /// Loading message
  final String message;

  /// Loading progress (0.0 to 1.0)
  final double? progress;

  const AnalyticsLoading({
    this.message = 'Loading analytics data...',
    this.progress,
  });

  @override
  List<Object?> get props => [message, progress];

  @override
  String toString() => 'AnalyticsLoading(message: $message, progress: $progress)';
}

/// Loaded state with analytics data
class AnalyticsLoaded extends AnalyticsState {
  /// Comprehensive analytics data
  final AnalyticsData analyticsData;

  /// Currently selected region
  final String selectedRegion;

  /// Currently selected date range
  final DateRange selectedDateRange;

  /// Currently applied filters
  final AnalyticsFilters? appliedFilters;

  /// Available regions for selection
  final List<String>? availableRegions;

  /// Generated charts data
  final Map<String, dynamic> charts;

  /// Last refresh timestamp
  final DateTime lastRefresh;

  const AnalyticsLoaded({
    required this.analyticsData,
    required this.selectedRegion,
    required this.selectedDateRange,
    this.appliedFilters,
    this.availableRegions,
    this.charts = const {},
    required this.lastRefresh,
  });

  /// Creates a copy with updated values
  AnalyticsLoaded copyWith({
    AnalyticsData? analyticsData,
    String? selectedRegion,
    DateRange? selectedDateRange,
    AnalyticsFilters? appliedFilters,
    List<String>? availableRegions,
    Map<String, dynamic>? charts,
    DateTime? lastRefresh,
  }) {
    return AnalyticsLoaded(
      analyticsData: analyticsData ?? this.analyticsData,
      selectedRegion: selectedRegion ?? this.selectedRegion,
      selectedDateRange: selectedDateRange ?? this.selectedDateRange,
      appliedFilters: appliedFilters ?? this.appliedFilters,
      availableRegions: availableRegions ?? this.availableRegions,
      charts: charts ?? this.charts,
      lastRefresh: lastRefresh ?? this.lastRefresh,
    );
  }

  @override
  List<Object?> get props => [
        analyticsData,
        selectedRegion,
        selectedDateRange,
        appliedFilters,
        availableRegions,
        charts,
        lastRefresh,
      ];

  @override
  String toString() => 'AnalyticsLoaded(region: $selectedRegion, refresh: $lastRefresh)';
}

/// Chart generation loading state
class ChartGenerating extends AnalyticsState {
  /// Base analytics state
  final AnalyticsLoaded baseState;

  /// Chart type being generated
  final ChartType chartType;

  /// Data type being visualized
  final ChartDataType dataType;

  /// Generation progress (0.0 to 1.0)
  final double? progress;

  const ChartGenerating({
    required this.baseState,
    required this.chartType,
    required this.dataType,
    this.progress,
  });

  @override
  List<Object?> get props => [baseState, chartType, dataType, progress];

  @override
  String toString() => 'ChartGenerating(type: $chartType, data: $dataType)';
}

/// Chart generated successfully state
class ChartGenerated extends AnalyticsState {
  /// Base analytics state
  final AnalyticsLoaded baseState;

  /// Generated chart data
  final dynamic chartData;

  /// Chart identifier for tracking
  final String chartId;

  const ChartGenerated({
    required this.baseState,
    required this.chartData,
    required this.chartId,
  });

  @override
  List<Object?> get props => [baseState, chartData, chartId];

  @override
  String toString() => 'ChartGenerated(chartId: $chartId)';
}

/// Export in progress state
class AnalyticsExporting extends AnalyticsState {
  /// Base analytics state
  final AnalyticsLoaded baseState;

  /// Export format
  final ExportFormat format;

  /// Export progress (0.0 to 1.0)
  final double? progress;

  const AnalyticsExporting({
    required this.baseState,
    required this.format,
    this.progress,
  });

  @override
  List<Object?> get props => [baseState, format, progress];

  @override
  String toString() => 'AnalyticsExporting(format: $format, progress: $progress)';
}

/// Export completed state
class AnalyticsExported extends AnalyticsState {
  /// Base analytics state
  final AnalyticsLoaded baseState;

  /// URL of exported report
  final String reportUrl;

  /// Export format
  final ExportFormat format;

  const AnalyticsExported({
    required this.baseState,
    required this.reportUrl,
    required this.format,
  });

  @override
  List<Object?> get props => [baseState, reportUrl, format];

  @override
  String toString() => 'AnalyticsExported(url: $reportUrl, format: $format)';
}

/// Error state
class AnalyticsError extends AnalyticsState {
  /// Error message
  final String message;

  /// Error type for handling
  final String errorType;

  /// Previous state for recovery
  final AnalyticsState? previousState;

  /// Whether error is recoverable
  final bool isRecoverable;

  const AnalyticsError({
    required this.message,
    this.errorType = 'general',
    this.previousState,
    this.isRecoverable = true,
  });

  @override
  List<Object?> get props => [message, errorType, previousState, isRecoverable];

  @override
  String toString() => 'AnalyticsError(message: $message, type: $errorType)';
}

/// Analytics BLoC implementation
class AnalyticsBloc extends Bloc<AnalyticsEvent, AnalyticsState> {
  /// Use case for getting analytics data
  final GetAnalyticsData _getAnalyticsData;

  /// Use case for generating chart data
  final GenerateChartData _generateChartData;

  /// Analytics repository for additional operations
  final AnalyticsRepository _analyticsRepository;

  /// Constructor requiring use cases and repository
  AnalyticsBloc({
    required GetAnalyticsData getAnalyticsData,
    required GenerateChartData generateChartData,
    required AnalyticsRepository analyticsRepository,
  })  : _getAnalyticsData = getAnalyticsData,
        _generateChartData = generateChartData,
        _analyticsRepository = analyticsRepository,
        super(const AnalyticsInitial()) {
    // Register event handlers
    on<LoadAnalyticsData>(_onLoadAnalyticsData);
    on<GenerateChart>(_onGenerateChart);
    on<ApplyFilters>(_onApplyFilters);
    on<ChangeRegion>(_onChangeRegion);
    on<ChangeDateRange>(_onChangeDateRange);
    on<RefreshAnalyticsData>(_onRefreshAnalyticsData);
    on<ExportAnalyticsReport>(_onExportAnalyticsReport);
    on<LoadAvailableRegions>(_onLoadAvailableRegions);
    on<ClearAnalyticsData>(_onClearAnalyticsData);
  }

  /// Handles loading analytics data
  Future<void> _onLoadAnalyticsData(
    LoadAnalyticsData event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      emit(const AnalyticsLoading(message: 'Loading analytics data...'));

      // Create use case parameters
      final params = GetAnalyticsDataParams(
        region: event.region,
        dateRange: event.dateRange,
        filters: event.filters,
      );

      // Execute use case
      final result = await _getAnalyticsData(params);

      // Handle result
      result.fold(
        (failure) => emit(AnalyticsError(
          message: failure.message,
          errorType: 'data_loading',
          isRecoverable: true,
        )),
        (analyticsData) => emit(AnalyticsLoaded(
          analyticsData: analyticsData,
          selectedRegion: event.region,
          selectedDateRange: event.dateRange,
          appliedFilters: event.filters,
          lastRefresh: DateTime.now(),
        )),
      );
    } catch (e) {
      emit(AnalyticsError(
        message: 'Unexpected error loading analytics data: ${e.toString()}',
        errorType: 'unexpected',
        isRecoverable: true,
      ));
    }
  }

  /// Handles chart generation
  Future<void> _onGenerateChart(
    GenerateChart event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      // Ensure we have a loaded state to work with
      final currentState = state;
      if (currentState is! AnalyticsLoaded) {
        emit(const AnalyticsError(
          message: 'Cannot generate chart without loaded analytics data',
          errorType: 'invalid_state',
          isRecoverable: true,
        ));
        return;
      }

      // Emit chart generating state
      emit(ChartGenerating(
        baseState: currentState,
        chartType: event.chartType,
        dataType: event.dataType,
        progress: 0.0,
      ));

      // Create chart generation parameters
      final params = GenerateChartDataParams(
        chartType: event.chartType,
        dataType: event.dataType,
        region: event.region,
        dateRange: event.dateRange,
        configuration: event.configuration,
        xFactor: event.xFactor,
        yFactor: event.yFactor,
      );

      // Execute chart generation use case
      final result = await _generateChartData(params);

      // Handle result
      result.fold(
        (failure) => emit(AnalyticsError(
          message: failure.message,
          errorType: 'chart_generation',
          previousState: currentState,
          isRecoverable: true,
        )),
        (chartData) {
          // Generate unique chart ID
          final chartId = _generateChartId(event.chartType, event.dataType);

          // Update charts in base state
          final updatedCharts = Map<String, dynamic>.from(currentState.charts);
          updatedCharts[chartId] = chartData;

          // Emit chart generated state
          emit(ChartGenerated(
            baseState: currentState.copyWith(charts: updatedCharts),
            chartData: chartData,
            chartId: chartId,
          ));
        },
      );
    } catch (e) {
      emit(AnalyticsError(
        message: 'Unexpected error generating chart: ${e.toString()}',
        errorType: 'unexpected',
        isRecoverable: true,
      ));
    }
  }

  /// Handles applying filters
  Future<void> _onApplyFilters(
    ApplyFilters event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      final currentState = state;
      if (currentState is! AnalyticsLoaded) {
        emit(const AnalyticsError(
          message: 'Cannot apply filters without loaded analytics data',
          errorType: 'invalid_state',
          isRecoverable: true,
        ));
        return;
      }

      if (event.reloadData) {
        // Reload data with new filters
        add(LoadAnalyticsData(
          region: currentState.selectedRegion,
          dateRange: currentState.selectedDateRange,
          filters: event.filters,
        ));
      } else {
        // Just update filters without reloading
        emit(currentState.copyWith(appliedFilters: event.filters));
      }
    } catch (e) {
      emit(AnalyticsError(
        message: 'Error applying filters: ${e.toString()}',
        errorType: 'filter_application',
        isRecoverable: true,
      ));
    }
  }

  /// Handles region change
  Future<void> _onChangeRegion(
    ChangeRegion event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      final currentState = state;
      if (currentState is! AnalyticsLoaded) {
        emit(const AnalyticsError(
          message: 'Cannot change region without loaded analytics data',
          errorType: 'invalid_state',
          isRecoverable: true,
        ));
        return;
      }

      if (event.reloadData) {
        // Reload data for new region
        add(LoadAnalyticsData(
          region: event.region,
          dateRange: currentState.selectedDateRange,
          filters: currentState.appliedFilters,
        ));
      } else {
        // Just update region selection
        emit(currentState.copyWith(selectedRegion: event.region));
      }
    } catch (e) {
      emit(AnalyticsError(
        message: 'Error changing region: ${e.toString()}',
        errorType: 'region_change',
        isRecoverable: true,
      ));
    }
  }

  /// Handles date range change
  Future<void> _onChangeDateRange(
    ChangeDateRange event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      final currentState = state;
      if (currentState is! AnalyticsLoaded) {
        emit(const AnalyticsError(
          message: 'Cannot change date range without loaded analytics data',
          errorType: 'invalid_state',
          isRecoverable: true,
        ));
        return;
      }

      if (event.reloadData) {
        // Reload data for new date range
        add(LoadAnalyticsData(
          region: currentState.selectedRegion,
          dateRange: event.dateRange,
          filters: currentState.appliedFilters,
        ));
      } else {
        // Just update date range selection
        emit(currentState.copyWith(selectedDateRange: event.dateRange));
      }
    } catch (e) {
      emit(AnalyticsError(
        message: 'Error changing date range: ${e.toString()}',
        errorType: 'date_range_change',
        isRecoverable: true,
      ));
    }
  }

  /// Handles data refresh
  Future<void> _onRefreshAnalyticsData(
    RefreshAnalyticsData event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      final currentState = state;
      if (currentState is AnalyticsLoaded) {
        // Reload current data
        add(LoadAnalyticsData(
          region: currentState.selectedRegion,
          dateRange: currentState.selectedDateRange,
          filters: currentState.appliedFilters,
        ));
      } else {
        emit(const AnalyticsError(
          message: 'Cannot refresh without existing analytics data',
          errorType: 'refresh_error',
          isRecoverable: true,
        ));
      }
    } catch (e) {
      emit(AnalyticsError(
        message: 'Error refreshing data: ${e.toString()}',
        errorType: 'refresh_error',
        isRecoverable: true,
      ));
    }
  }

  /// Handles analytics report export
  Future<void> _onExportAnalyticsReport(
    ExportAnalyticsReport event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      final currentState = state;
      if (currentState is! AnalyticsLoaded) {
        emit(const AnalyticsError(
          message: 'Cannot export report without loaded analytics data',
          errorType: 'invalid_state',
          isRecoverable: true,
        ));
        return;
      }

      // Emit exporting state
      emit(AnalyticsExporting(
        baseState: currentState,
        format: event.format,
        progress: 0.0,
      ));

      // Export report through repository
      final result = await _analyticsRepository.exportAnalyticsReport(
        region: currentState.selectedRegion,
        dateRange: currentState.selectedDateRange,
        format: event.format,
        includeCharts: event.includeCharts,
        sections: event.sections,
      );

      // Handle result
      result.fold(
        (failure) => emit(AnalyticsError(
          message: failure.message,
          errorType: 'export_error',
          previousState: currentState,
          isRecoverable: true,
        )),
        (reportUrl) => emit(AnalyticsExported(
          baseState: currentState,
          reportUrl: reportUrl,
          format: event.format,
        )),
      );
    } catch (e) {
      emit(AnalyticsError(
        message: 'Unexpected error exporting report: ${e.toString()}',
        errorType: 'unexpected',
        isRecoverable: true,
      ));
    }
  }

  /// Handles loading available regions
  Future<void> _onLoadAvailableRegions(
    LoadAvailableRegions event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      final result = await _analyticsRepository.getAvailableRegions();

      result.fold(
        (failure) {
          // Don't emit error for regions loading failure - it's not critical
          print('Warning: Failed to load available regions: ${failure.message}');
        },
        (regions) {
          final currentState = state;
          if (currentState is AnalyticsLoaded) {
            emit(currentState.copyWith(availableRegions: regions));
          }
          // If not in loaded state, regions will be loaded when data is loaded
        },
      );
    } catch (e) {
      print('Warning: Unexpected error loading regions: ${e.toString()}');
    }
  }

  /// Handles clearing analytics data
  Future<void> _onClearAnalyticsData(
    ClearAnalyticsData event,
    Emitter<AnalyticsState> emit,
  ) async {
    try {
      emit(const AnalyticsInitial());
    } catch (e) {
      emit(AnalyticsError(
        message: 'Error clearing analytics data: ${e.toString()}',
        errorType: 'clear_error',
        isRecoverable: true,
      ));
    }
  }

  /// Generates unique chart ID for tracking
  String _generateChartId(ChartType chartType, ChartDataType dataType) {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    return '${chartType.name}_${dataType.name}_$timestamp';
  }
}