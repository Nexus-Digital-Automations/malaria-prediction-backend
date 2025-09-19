/// Use case for generating chart data for analytics dashboard visualization
///
/// This use case coordinates the generation of various chart data types
/// including line charts, bar charts, pie charts, and scatter plots
/// optimized for fl_chart visualization components.
///
/// Usage:
/// ```dart
/// final result = await generateChartData(GenerateChartDataParams(
///   chartType: ChartType.lineChart,
///   dataType: ChartDataType.predictionAccuracy,
///   region: 'Kenya',
///   dateRange: DateRange(start: startDate, end: endDate),
/// ));
///
/// result.fold(
///   (failure) => handleError(failure),
///   (chartData) => renderChart(chartData),
/// );
/// ```
library;

import 'package:dartz/dartz.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import '../../../../core/errors/failures.dart';
import '../../../../core/usecases/usecase.dart';
import '../entities/chart_data.dart';
import '../entities/analytics_data.dart';
import '../repositories/analytics_repository.dart';

/// Use case for generating chart data for dashboard visualization
class GenerateChartData implements UseCase<dynamic, GenerateChartDataParams> {
  /// Analytics repository for data operations
  final AnalyticsRepository repository;

  /// Constructor requiring analytics repository dependency
  const GenerateChartData(this.repository);

  /// Executes chart data generation with comprehensive validation
  ///
  /// This method:
  /// 1. Validates input parameters for chart configuration
  /// 2. Generates appropriate chart data based on chart type
  /// 3. Applies styling and configuration options
  /// 4. Returns chart data entity ready for fl_chart visualization
  ///
  /// Parameters:
  /// - [params]: GenerateChartDataParams containing chart request details
  ///
  /// Returns:
  /// - [Right]: Chart data entity (LineChartDataEntity, BarChartDataEntity, etc.)
  /// - [Left]: Failure if chart generation fails
  @override
  Future<Either<Failure, dynamic>> call(GenerateChartDataParams params) async {
    try {
      // Validate input parameters
      final validationResult = _validateParams(params);
      if (validationResult != null) {
        return Left(validationResult);
      }

      // Generate chart data based on chart type
      switch (params.chartType) {
        case ChartType.lineChart:
          return await _generateLineChart(params);
        case ChartType.barChart:
          return await _generateBarChart(params);
        case ChartType.pieChart:
          return await _generatePieChart(params);
        case ChartType.scatterPlot:
          return await _generateScatterPlot(params);
      }
    } catch (e) {
      return Left(ServerFailure(
        'Unexpected error during chart generation: ${e.toString()}',
      ),);
    }
  }

  /// Validates chart generation parameters
  ///
  /// Performs comprehensive validation including chart type compatibility,
  /// data type validation, and configuration consistency checks
  ///
  /// Returns null if validation passes, Failure otherwise
  Failure? _validateParams(GenerateChartDataParams params) {
    // Validate region identifier
    if (params.region.isEmpty) {
      return const ValidationFailure(
        'Region identifier cannot be empty',
        'region',
      );
    }

    // Validate date range
    if (params.dateRange.start.isAfter(params.dateRange.end)) {
      return const ValidationFailure(
        'Start date must be before end date',
        'dateRange',
      );
    }

    // Validate chart type and data type compatibility
    if (!_isChartTypeCompatible(params.chartType, params.dataType)) {
      return ValidationFailure(
        'Chart type ${params.chartType} is not compatible with data type ${params.dataType}',
        'chartType',
      );
    }

    // Validate scatter plot specific requirements
    if (params.chartType == ChartType.scatterPlot) {
      if (params.xFactor == null || params.yFactor == null) {
        return const ValidationFailure(
          'Scatter plot requires both X and Y environmental factors',
          'scatterPlotFactors',
        );
      }
    }

    return null;
  }

  /// Checks compatibility between chart type and data type
  ///
  /// Ensures that the requested chart type can effectively visualize
  /// the specified data type with meaningful representation
  bool _isChartTypeCompatible(ChartType chartType, ChartDataType dataType) {
    switch (chartType) {
      case ChartType.lineChart:
        return [
          ChartDataType.predictionAccuracy,
          ChartDataType.environmentalTrends,
          ChartDataType.riskTrends,
          ChartDataType.temporalPatterns,
        ].contains(dataType);

      case ChartType.barChart:
        return [
          ChartDataType.alertStatistics,
          ChartDataType.riskDistribution,
          ChartDataType.modelComparison,
          ChartDataType.dataQuality,
        ].contains(dataType);

      case ChartType.pieChart:
        return [
          ChartDataType.riskDistribution,
          ChartDataType.alertStatistics,
          ChartDataType.dataQuality,
        ].contains(dataType);

      case ChartType.scatterPlot:
        return [
          ChartDataType.environmentalCorrelation,
          ChartDataType.riskTrends,
        ].contains(dataType);
    }
  }

  /// Generates line chart data for trend visualization
  ///
  /// Creates LineChartDataEntity optimized for fl_chart with appropriate
  /// styling, axis configuration, and data series
  Future<Either<Failure, LineChartDataEntity>> _generateLineChart(
    GenerateChartDataParams params,
  ) async {
    try {
      final result = await repository.generateLineChartData(
        type: params.dataType,
        region: params.region,
        dateRange: params.dateRange,
        configuration: params.configuration,
      );

      return result.fold(
        (failure) => Left(failure),
        (chartData) => Right(_applyLineChartStyling(chartData, params)),
      );
    } catch (e) {
      return Left(ChartGenerationFailure(
        message: 'Failed to generate line chart: ${e.toString()}',
        chartType: 'lineChart',
      ),);
    }
  }

  /// Generates bar chart data for categorical visualization
  ///
  /// Creates BarChartDataEntity optimized for fl_chart with appropriate
  /// styling, axis configuration, and data grouping
  Future<Either<Failure, BarChartDataEntity>> _generateBarChart(
    GenerateChartDataParams params,
  ) async {
    try {
      final result = await repository.generateBarChartData(
        type: params.dataType,
        region: params.region,
        dateRange: params.dateRange,
        configuration: params.configuration,
      );

      return result.fold(
        (failure) => Left(failure),
        (chartData) => Right(_applyBarChartStyling(chartData, params)),
      );
    } catch (e) {
      return Left(ChartGenerationFailure(
        message: 'Failed to generate bar chart: ${e.toString()}',
        chartType: 'barChart',
      ),);
    }
  }

  /// Generates pie chart data for proportion visualization
  ///
  /// Creates PieChartDataEntity optimized for fl_chart with appropriate
  /// styling, section configuration, and percentage calculation
  Future<Either<Failure, PieChartDataEntity>> _generatePieChart(
    GenerateChartDataParams params,
  ) async {
    try {
      final result = await repository.generatePieChartData(
        type: params.dataType,
        region: params.region,
        dateRange: params.dateRange,
        configuration: params.configuration,
      );

      return result.fold(
        (failure) => Left(failure),
        (chartData) => Right(_applyPieChartStyling(chartData, params)),
      );
    } catch (e) {
      return Left(ChartGenerationFailure(
        message: 'Failed to generate pie chart: ${e.toString()}',
        chartType: 'pieChart',
      ),);
    }
  }

  /// Generates scatter plot data for correlation visualization
  ///
  /// Creates ScatterPlotDataEntity optimized for fl_chart with appropriate
  /// styling, axis configuration, and correlation analysis
  Future<Either<Failure, ScatterPlotDataEntity>> _generateScatterPlot(
    GenerateChartDataParams params,
  ) async {
    try {
      if (params.xFactor == null || params.yFactor == null) {
        return const Left(ValidationFailure(
          'Scatter plot requires both X and Y factors',
          'scatterPlotFactors',
        ),);
      }

      final result = await repository.generateScatterPlotData(
        xFactor: params.xFactor!,
        yFactor: params.yFactor!,
        region: params.region,
        dateRange: params.dateRange,
        configuration: params.configuration,
      );

      return result.fold(
        (failure) => Left(failure),
        (chartData) => Right(_applyScatterPlotStyling(chartData, params)),
      );
    } catch (e) {
      return Left(ChartGenerationFailure(
        message: 'Failed to generate scatter plot: ${e.toString()}',
        chartType: 'scatterPlot',
      ),);
    }
  }

  /// Applies custom styling to line chart data
  ///
  /// Enhances chart data with theme-appropriate colors, fonts,
  /// and configuration based on data type and user preferences
  LineChartDataEntity _applyLineChartStyling(
    LineChartDataEntity chartData,
    GenerateChartDataParams params,
  ) {
    // Apply custom configuration if provided
    if (params.configuration != null) {
      final config = params.configuration!;

      return LineChartDataEntity(
        title: config.title ?? chartData.title,
        subtitle: config.subtitle ?? chartData.subtitle,
        series: _applySeriesStyling(chartData.series, config.colors),
        xAxis: chartData.xAxis,
        yAxis: chartData.yAxis,
        style: chartData.style,
        showMarkers: chartData.showMarkers,
        showGrid: config.showGrid,
        enableTouch: chartData.enableTouch,
        animationDuration: config.enableAnimations ? config.animationDuration : 0,
      );
    }

    return chartData;
  }

  /// Applies custom styling to bar chart data
  ///
  /// Enhances chart data with appropriate colors and configuration
  BarChartDataEntity _applyBarChartStyling(
    BarChartDataEntity chartData,
    GenerateChartDataParams params,
  ) {
    if (params.configuration != null) {
      final config = params.configuration!;

      return BarChartDataEntity(
        title: config.title ?? chartData.title,
        subtitle: config.subtitle ?? chartData.subtitle,
        dataGroups: chartData.dataGroups,
        xAxis: chartData.xAxis,
        yAxis: chartData.yAxis,
        style: chartData.style,
        barWidth: chartData.barWidth,
        showValueLabels: chartData.showValueLabels,
        enableTouch: chartData.enableTouch,
        animationDuration: config.enableAnimations ? config.animationDuration : 0,
      );
    }

    return chartData;
  }

  /// Applies custom styling to pie chart data
  ///
  /// Enhances chart data with appropriate colors and configuration
  PieChartDataEntity _applyPieChartStyling(
    PieChartDataEntity chartData,
    GenerateChartDataParams params,
  ) {
    if (params.configuration != null) {
      final config = params.configuration!;

      return PieChartDataEntity(
        title: config.title ?? chartData.title,
        subtitle: config.subtitle ?? chartData.subtitle,
        sections: chartData.sections,
        style: chartData.style,
        centerSpaceRadius: chartData.centerSpaceRadius,
        showPercentages: chartData.showPercentages,
        showValues: chartData.showValues,
        enableTouch: chartData.enableTouch,
        animationDuration: config.enableAnimations ? config.animationDuration : 0,
      );
    }

    return chartData;
  }

  /// Applies custom styling to scatter plot data
  ///
  /// Enhances chart data with appropriate colors and configuration
  ScatterPlotDataEntity _applyScatterPlotStyling(
    ScatterPlotDataEntity chartData,
    GenerateChartDataParams params,
  ) {
    if (params.configuration != null) {
      final config = params.configuration!;

      return ScatterPlotDataEntity(
        title: config.title ?? chartData.title,
        subtitle: config.subtitle ?? chartData.subtitle,
        series: chartData.series,
        xAxis: chartData.xAxis,
        yAxis: chartData.yAxis,
        style: chartData.style,
        pointSize: chartData.pointSize,
        showTrendLines: chartData.showTrendLines,
        enableTouch: chartData.enableTouch,
        animationDuration: config.enableAnimations ? config.animationDuration : 0,
      );
    }

    return chartData;
  }

  /// Applies color styling to chart series
  ///
  /// Updates series colors based on custom color palette
  List<ChartSeries> _applySeriesStyling(
    List<ChartSeries> series,
    List<Color>? customColors,
  ) {
    if (customColors == null || customColors.isEmpty) {
      return series;
    }

    return series.asMap().entries.map((entry) {
      final index = entry.key;
      final seriesData = entry.value;
      final colorIndex = index % customColors.length;

      return ChartSeries(
        name: seriesData.name,
        data: seriesData.data,
        color: customColors[colorIndex],
        strokeWidth: seriesData.strokeWidth,
        fillArea: seriesData.fillArea,
        fillColor: seriesData.fillColor,
        dashPattern: seriesData.dashPattern,
        isVisible: seriesData.isVisible,
      );
    }).toList();
  }
}

/// Parameters for chart data generation use case
class GenerateChartDataParams extends Equatable {
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

  /// X-axis environmental factor (required for scatter plots)
  final EnvironmentalFactor? xFactor;

  /// Y-axis environmental factor (required for scatter plots)
  final EnvironmentalFactor? yFactor;

  /// Constructor for chart generation parameters
  const GenerateChartDataParams({
    required this.chartType,
    required this.dataType,
    required this.region,
    required this.dateRange,
    this.configuration,
    this.xFactor,
    this.yFactor,
  });

  /// Creates a copy of parameters with updated values
  GenerateChartDataParams copyWith({
    ChartType? chartType,
    ChartDataType? dataType,
    String? region,
    DateRange? dateRange,
    ChartConfiguration? configuration,
    EnvironmentalFactor? xFactor,
    EnvironmentalFactor? yFactor,
  }) {
    return GenerateChartDataParams(
      chartType: chartType ?? this.chartType,
      dataType: dataType ?? this.dataType,
      region: region ?? this.region,
      dateRange: dateRange ?? this.dateRange,
      configuration: configuration ?? this.configuration,
      xFactor: xFactor ?? this.xFactor,
      yFactor: yFactor ?? this.yFactor,
    );
  }

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
  String toString() {
    return 'GenerateChartDataParams(chartType: $chartType, dataType: $dataType, region: $region)';
  }
}

/// Chart type enumeration
enum ChartType {
  /// Line chart for trend visualization
  lineChart,

  /// Bar chart for categorical data
  barChart,

  /// Pie chart for proportion visualization
  pieChart,

  /// Scatter plot for correlation analysis
  scatterPlot,
}

/// Custom failure type for chart generation operations
class ChartGenerationFailure extends Failure {
  /// The type of chart that failed to generate
  final String chartType;

  const ChartGenerationFailure({
    required String message,
    required this.chartType,
  }) : super(message);

  @override
  List<Object?> get props => [message, chartType];
}

