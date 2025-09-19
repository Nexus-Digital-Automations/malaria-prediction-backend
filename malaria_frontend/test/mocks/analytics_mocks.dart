/// Mock data and classes for analytics testing
///
/// This file provides comprehensive mock implementations for all analytics-related
/// classes, entities, and data structures used throughout the testing suite.
library;

import 'package:mocktail/mocktail.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:dartz/dartz.dart';
import 'package:malaria_frontend/features/analytics/presentation/bloc/analytics_bloc.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_filters.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/chart_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/interactive_chart.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/prediction_metrics.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/data_explorer.dart';
import 'package:malaria_frontend/features/analytics/domain/usecases/get_analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/usecases/generate_chart_data.dart';
import 'package:malaria_frontend/features/analytics/data/datasources/analytics_remote_datasource.dart';
import 'package:malaria_frontend/features/analytics/data/datasources/analytics_local_datasource.dart';
import 'package:malaria_frontend/features/analytics/data/models/analytics_data_model.dart';
import 'package:malaria_frontend/core/network/network_info.dart';
import 'package:malaria_frontend/core/storage/storage_service.dart';

/// Mock Analytics BLoC for testing
class MockAnalyticsBloc extends Mock implements AnalyticsBloc {}

/// Mock Remote Data Source for testing
class MockAnalyticsRemoteDataSource extends Mock implements AnalyticsRemoteDataSource {}

/// Mock Local Data Source for testing
class MockAnalyticsLocalDataSource extends Mock implements AnalyticsLocalDataSource {}

/// Mock Network Info for testing
class MockNetworkInfo extends Mock implements NetworkInfo {}

/// Mock Storage Service for testing
class MockStorageService extends Mock implements StorageService {}

/// Mock data factory for analytics testing
class MockAnalyticsData {
  /// Creates mock analytics data entity
  static AnalyticsData createMockAnalyticsData() {
    return AnalyticsData(
      id: 'analytics_001',
      region: 'Kenya',
      dateRange: DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      ),
      predictionAccuracy: PredictionAccuracy(
        overall: 0.85,
        byRiskLevel: {
          'low': 0.92,
          'medium': 0.85,
          'high': 0.78,
          'critical': 0.65,
        },
        trend: [
          AccuracyDataPoint(
            date: DateTime(2024, 1, 1),
            accuracy: 0.82,
            sampleSize: 100,
          ),
          AccuracyDataPoint(
            date: DateTime(2024, 1, 15),
            accuracy: 0.85,
            sampleSize: 150,
          ),
          AccuracyDataPoint(
            date: DateTime(2024, 1, 31),
            accuracy: 0.87,
            sampleSize: 120,
          ),
        ],
        precision: 0.88,
        recall: 0.83,
        f1Score: 0.855,
      ),
      environmentalTrends: [
        EnvironmentalTrend(
          date: DateTime(2024, 1, 15),
          factor: EnvironmentalFactor.temperature,
          value: 28.5,
          coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
          quality: 0.95,
        ),
        EnvironmentalTrend(
          date: DateTime(2024, 1, 15),
          factor: EnvironmentalFactor.rainfall,
          value: 45.2,
          coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
          quality: 0.92,
        ),
        EnvironmentalTrend(
          date: DateTime(2024, 1, 15),
          factor: EnvironmentalFactor.humidity,
          value: 75.8,
          coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
          quality: 0.88,
        ),
      ],
      riskTrends: [
        RiskTrend(
          date: DateTime(2024, 1, 15),
          riskScore: 0.65,
          riskLevel: RiskLevel.medium,
          coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
          populationAtRisk: 50000,
          confidence: 0.85,
        ),
        RiskTrend(
          date: DateTime(2024, 1, 20),
          riskScore: 0.72,
          riskLevel: RiskLevel.high,
          coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
          populationAtRisk: 75000,
          confidence: 0.88,
        ),
      ],
      alertStatistics: AlertStatistics(
        totalAlerts: 125,
        alertsBySeverity: {
          AlertSeverity.info: 30,
          AlertSeverity.warning: 45,
          AlertSeverity.high: 35,
          AlertSeverity.critical: 10,
          AlertSeverity.emergency: 5,
        },
        deliveryRate: 0.95,
        averageResponseTime: const Duration(minutes: 5),
        falsePositives: 8,
        missedAlerts: 3,
      ),
      dataQuality: DataQuality(
        completeness: 0.92,
        accuracy: 0.88,
        freshnessHours: 2.5,
        sourcesCount: 5,
        sourcesWithIssues: ['WeatherAPI'],
        lastUpdate: DateTime.now().subtract(const Duration(hours: 2)),
      ),
      generatedAt: DateTime.now(),
    );
  }

  /// Creates mock analytics data model for data layer testing
  static AnalyticsDataModel createMockAnalyticsDataModel() {
    return AnalyticsDataModel(
      id: 'analytics_model_001',
      region: 'Kenya',
      dateRange: DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      ),
      predictionAccuracy: PredictionAccuracy(
        overall: 0.85,
        byRiskLevel: {'medium': 0.82, 'high': 0.75},
        trend: [],
        precision: 0.88,
        recall: 0.83,
        f1Score: 0.855,
      ),
      environmentalTrends: [],
      riskTrends: [],
      alertStatistics: AlertStatistics(
        totalAlerts: 100,
        alertsBySeverity: {},
        deliveryRate: 0.95,
        averageResponseTime: const Duration(minutes: 5),
        falsePositives: 5,
        missedAlerts: 2,
      ),
      dataQuality: DataQuality(
        completeness: 0.90,
        accuracy: 0.85,
        freshnessHours: 3.0,
        sourcesCount: 4,
        sourcesWithIssues: [],
        lastUpdate: DateTime.now(),
      ),
      generatedAt: DateTime.now(),
    );
  }

  /// Creates large analytics dataset for performance testing
  static AnalyticsDataModel createLargeAnalyticsDataSet() {
    final environmentalTrends = List.generate(1000, (index) =>
      EnvironmentalTrend(
        date: DateTime(2024, 1, 1).add(Duration(hours: index)),
        factor: EnvironmentalFactor.values[index % EnvironmentalFactor.values.length],
        value: 20.0 + (index % 20),
        coordinates: Coordinates(
          latitude: -1.2921 + (index % 10) * 0.01,
          longitude: 36.8219 + (index % 10) * 0.01,
        ),
        quality: 0.8 + (index % 20) * 0.01,
      ),
    );

    final riskTrends = List.generate(500, (index) =>
      RiskTrend(
        date: DateTime(2024, 1, 1).add(Duration(days: index ~/ 10)),
        riskScore: 0.3 + (index % 70) * 0.01,
        riskLevel: RiskLevel.values[index % RiskLevel.values.length],
        coordinates: Coordinates(
          latitude: -1.2921 + (index % 5) * 0.02,
          longitude: 36.8219 + (index % 5) * 0.02,
        ),
        populationAtRisk: 10000 + (index % 50) * 1000,
        confidence: 0.7 + (index % 30) * 0.01,
      ),
    );

    return AnalyticsDataModel(
      id: 'large_dataset_001',
      region: 'East Africa',
      dateRange: DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 12, 31),
      ),
      predictionAccuracy: PredictionAccuracy(
        overall: 0.83,
        byRiskLevel: {
          'low': 0.92,
          'medium': 0.85,
          'high': 0.78,
          'critical': 0.65,
        },
        trend: List.generate(365, (index) =>
          AccuracyDataPoint(
            date: DateTime(2024, 1, 1).add(Duration(days: index)),
            accuracy: 0.7 + (index % 20) * 0.01,
            sampleSize: 50 + (index % 100),
          ),
        ),
        precision: 0.85,
        recall: 0.81,
        f1Score: 0.83,
      ),
      environmentalTrends: environmentalTrends,
      riskTrends: riskTrends,
      alertStatistics: AlertStatistics(
        totalAlerts: 5000,
        alertsBySeverity: {
          AlertSeverity.info: 1500,
          AlertSeverity.warning: 2000,
          AlertSeverity.high: 1200,
          AlertSeverity.critical: 250,
          AlertSeverity.emergency: 50,
        },
        deliveryRate: 0.94,
        averageResponseTime: const Duration(minutes: 7),
        falsePositives: 120,
        missedAlerts: 35,
      ),
      dataQuality: DataQuality(
        completeness: 0.89,
        accuracy: 0.86,
        freshnessHours: 4.2,
        sourcesCount: 12,
        sourcesWithIssues: ['SatelliteData', 'WeatherStationC'],
        lastUpdate: DateTime.now().subtract(const Duration(hours: 4)),
      ),
      generatedAt: DateTime.now(),
    );
  }

  /// Creates mock analytics filters
  static AnalyticsFilters createMockAnalyticsFilters() {
    return AnalyticsFilters(
      region: 'Kenya',
      dateRange: DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      ),
      riskLevels: {RiskLevel.medium, RiskLevel.high},
      environmentalFactors: {
        EnvironmentalFactor.temperature,
        EnvironmentalFactor.rainfall,
      },
      dataQualityThreshold: 0.8,
    );
  }

  /// Creates mock interactive chart
  static InteractiveChart createMockInteractiveChart() {
    return InteractiveChart(
      id: 'chart_001',
      title: 'Prediction Accuracy Trend',
      chartType: InteractiveChartType.line,
      chartData: createMockLineChartData(),
      interactionConfig: createMockInteractionConfig(),
      viewState: createMockViewState(),
      theme: const ChartThemeData(),
    );
  }

  /// Creates mock line chart data
  static LineChartDataEntity createMockLineChartData() {
    return LineChartDataEntity(
      series: [
        ChartSeries(
          id: 'accuracy_series',
          name: 'Accuracy',
          data: [
            const ChartPoint(x: 0, y: 0.82),
            const ChartPoint(x: 1, y: 0.85),
            const ChartPoint(x: 2, y: 0.87),
            const ChartPoint(x: 3, y: 0.84),
            const ChartPoint(x: 4, y: 0.89),
          ],
          color: Colors.blue,
          strokeWidth: 2.0,
          fillArea: false,
        ),
      ],
      xAxis: ChartAxis(
        title: 'Time',
        min: 0,
        max: 4,
        interval: 1,
        showLabels: true,
        labelFormatter: (value) => 'Week ${value.toInt() + 1}',
      ),
      yAxis: ChartAxis(
        title: 'Accuracy',
        min: 0.7,
        max: 1.0,
        interval: 0.1,
        showLabels: true,
        labelFormatter: (value) => '${(value * 100).toInt()}%',
      ),
      showGrid: true,
      showMarkers: true,
    );
  }

  /// Creates mock chart interaction config
  static ChartInteractionConfig createMockInteractionConfig() {
    return ChartInteractionConfig(
      enableZoom: true,
      enablePan: true,
      enableTooltips: true,
      enableDrillDown: true,
      enableAnimations: true,
      animationDuration: const Duration(milliseconds: 300),
    );
  }

  /// Creates mock chart view state
  static ChartViewState createMockViewState() {
    return ChartViewState(
      zoomLevel: 1.0,
      panOffset: Offset.zero,
      selectedDataPoints: [],
      interactionHistory: [],
    );
  }

  /// Creates mock chart data
  static dynamic createMockChartData() {
    return createMockLineChartData();
  }

  /// Creates mock chart data model
  static dynamic createMockChartDataModel() {
    return createMockLineChartData();
  }

  /// Creates mock chart interaction
  static ChartInteraction createMockChartInteraction() {
    return ChartInteraction(
      type: ChartInteractionType.tap,
      position: const Offset(100, 100),
      timestamp: DateTime.now(),
      data: {'x': 2, 'y': 0.85},
    );
  }

  /// Creates mock drill down hierarchy
  static DrillDownHierarchy createMockDrillDownHierarchy() {
    return DrillDownHierarchy(
      currentLevel: 'Region',
      navigationPath: ['Country', 'Region'],
      availableOptions: [
        DrillDownOption(
          label: 'Sub-Region',
          targetDimension: 'sub_region',
          value: 'nairobi_central',
        ),
      ],
    );
  }

  /// Creates mock prediction metrics
  static PredictionMetrics createMockPredictionMetrics() {
    return PredictionMetrics(
      accuracy: 0.85,
      precision: 0.88,
      recall: 0.83,
      f1Score: 0.855,
      confusionMatrix: {
        'true_positive': 150,
        'false_positive': 20,
        'true_negative': 180,
        'false_negative': 30,
      },
      accuracyTrend: [
        AccuracyDataPoint(
          date: DateTime(2024, 1, 1),
          accuracy: 0.82,
          sampleSize: 100,
        ),
        AccuracyDataPoint(
          date: DateTime(2024, 1, 15),
          accuracy: 0.85,
          sampleSize: 150,
        ),
      ],
      modelComparison: [
        ModelPerformance(
          modelName: 'Random Forest',
          accuracy: 0.85,
          precision: 0.88,
          recall: 0.83,
          f1Score: 0.855,
        ),
        ModelPerformance(
          modelName: 'Neural Network',
          accuracy: 0.82,
          precision: 0.84,
          recall: 0.81,
          f1Score: 0.825,
        ),
      ],
      lastUpdated: DateTime.now(),
    );
  }

  /// Creates mock data explorer
  static DataExplorer createMockDataExplorer() {
    return DataExplorer(
      dimensions: ['region', 'time', 'risk_level'],
      currentDimension: 'region',
      data: [
        {'region': 'Kenya', 'risk_score': 0.65, 'population': 50000},
        {'region': 'Tanzania', 'risk_score': 0.58, 'population': 45000},
        {'region': 'Uganda', 'risk_score': 0.72, 'population': 38000},
      ],
      correlationMatrix: {
        'temperature_rainfall': 0.65,
        'humidity_temperature': 0.72,
        'vegetation_rainfall': 0.58,
      },
      summary: DataSummary(
        totalRecords: 1250,
        completeness: 0.92,
        qualityScore: 0.88,
        lastUpdated: DateTime.now(),
      ),
    );
  }

  /// Creates mock environmental data
  static EnvironmentalData createMockEnvironmentalData() {
    return EnvironmentalData(
      id: 'env_001',
      region: 'Kenya',
      dateRange: DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      ),
      temperature: TemperatureData(
        dailyMean: [
          TemperatureMeasurement(
            date: DateTime(2024, 1, 15),
            temperature: 28.5,
            quality: 0.95,
            source: 'WeatherStation_A',
          ),
        ],
        dailyMin: [
          TemperatureMeasurement(
            date: DateTime(2024, 1, 15),
            temperature: 22.1,
            quality: 0.95,
            source: 'WeatherStation_A',
          ),
        ],
        dailyMax: [
          TemperatureMeasurement(
            date: DateTime(2024, 1, 15),
            temperature: 34.2,
            quality: 0.95,
            source: 'WeatherStation_A',
          ),
        ],
        diurnalRange: [
          TemperatureMeasurement(
            date: DateTime(2024, 1, 15),
            temperature: 12.1,
            quality: 0.95,
            source: 'WeatherStation_A',
          ),
        ],
        anomalies: [],
        seasonalPattern: SeasonalPattern(
          spring: const SeasonalStatistics(
            average: 26.5,
            minimum: 20.0,
            maximum: 32.0,
            standardDeviation: 3.2,
            dataPoints: 90,
          ),
          summer: const SeasonalStatistics(
            average: 29.8,
            minimum: 24.0,
            maximum: 36.0,
            standardDeviation: 2.8,
            dataPoints: 92,
          ),
          autumn: const SeasonalStatistics(
            average: 27.2,
            minimum: 21.5,
            maximum: 33.5,
            standardDeviation: 3.1,
            dataPoints: 89,
          ),
          winter: const SeasonalStatistics(
            average: 24.8,
            minimum: 18.0,
            maximum: 30.0,
            standardDeviation: 3.5,
            dataPoints: 94,
          ),
          peakSeason: Season.summer,
          lowSeason: Season.winter,
        ),
      ),
      humidity: HumidityData(
        relativeHumidity: [
          HumidityMeasurement(
            date: DateTime(2024, 1, 15),
            humidity: 75.8,
            quality: 0.88,
            source: 'HumiditySensor_B',
          ),
        ],
        absoluteHumidity: [
          HumidityMeasurement(
            date: DateTime(2024, 1, 15),
            humidity: 18.2,
            quality: 0.88,
            source: 'HumiditySensor_B',
          ),
        ],
        dewPoint: [
          HumidityMeasurement(
            date: DateTime(2024, 1, 15),
            humidity: 21.5,
            quality: 0.88,
            source: 'HumiditySensor_B',
          ),
        ],
        seasonalPattern: SeasonalPattern(
          spring: const SeasonalStatistics(
            average: 72.5,
            minimum: 60.0,
            maximum: 85.0,
            standardDeviation: 8.2,
            dataPoints: 90,
          ),
          summer: const SeasonalStatistics(
            average: 78.2,
            minimum: 65.0,
            maximum: 90.0,
            standardDeviation: 7.5,
            dataPoints: 92,
          ),
          autumn: const SeasonalStatistics(
            average: 75.8,
            minimum: 62.0,
            maximum: 88.0,
            standardDeviation: 8.0,
            dataPoints: 89,
          ),
          winter: const SeasonalStatistics(
            average: 68.4,
            minimum: 55.0,
            maximum: 82.0,
            standardDeviation: 9.1,
            dataPoints: 94,
          ),
          peakSeason: Season.summer,
          lowSeason: Season.winter,
        ),
      ),
      rainfall: RainfallData(
        daily: [
          RainfallMeasurement(
            date: DateTime(2024, 1, 15),
            rainfall: 12.5,
            quality: 0.92,
            source: 'RainGauge_C',
          ),
        ],
        monthly: [
          RainfallMeasurement(
            date: DateTime(2024, 1, 1),
            rainfall: 245.8,
            quality: 0.92,
            source: 'RainGauge_C',
          ),
        ],
        seasonalPattern: SeasonalPattern(
          spring: const SeasonalStatistics(
            average: 185.5,
            minimum: 120.0,
            maximum: 280.0,
            standardDeviation: 45.2,
            dataPoints: 90,
          ),
          summer: const SeasonalStatistics(
            average: 125.2,
            minimum: 80.0,
            maximum: 200.0,
            standardDeviation: 35.8,
            dataPoints: 92,
          ),
          autumn: const SeasonalStatistics(
            average: 220.8,
            minimum: 150.0,
            maximum: 350.0,
            standardDeviation: 52.1,
            dataPoints: 89,
          ),
          winter: const SeasonalStatistics(
            average: 95.4,
            minimum: 60.0,
            maximum: 150.0,
            standardDeviation: 28.3,
            dataPoints: 94,
          ),
          peakSeason: Season.autumn,
          lowSeason: Season.winter,
        ),
        extremeEvents: [],
        postRainfallPeriods: [],
      ),
      vegetation: VegetationData(
        ndvi: [
          VegetationMeasurement(
            date: DateTime(2024, 1, 15),
            value: 0.65,
            quality: 0.85,
            source: 'SatelliteData_D',
          ),
        ],
        evi: [
          VegetationMeasurement(
            date: DateTime(2024, 1, 15),
            value: 0.58,
            quality: 0.85,
            source: 'SatelliteData_D',
          ),
        ],
        seasonalPattern: SeasonalPattern(
          spring: const SeasonalStatistics(
            average: 0.62,
            minimum: 0.45,
            maximum: 0.78,
            standardDeviation: 0.08,
            dataPoints: 90,
          ),
          summer: const SeasonalStatistics(
            average: 0.55,
            minimum: 0.38,
            maximum: 0.72,
            standardDeviation: 0.09,
            dataPoints: 92,
          ),
          autumn: const SeasonalStatistics(
            average: 0.68,
            minimum: 0.52,
            maximum: 0.82,
            standardDeviation: 0.07,
            dataPoints: 89,
          ),
          winter: const SeasonalStatistics(
            average: 0.48,
            minimum: 0.32,
            maximum: 0.65,
            standardDeviation: 0.11,
            dataPoints: 94,
          ),
          peakSeason: Season.autumn,
          lowSeason: Season.winter,
        ),
        landCoverDistribution: {
          LandCoverType.forest: 0.25,
          LandCoverType.grassland: 0.35,
          LandCoverType.cropland: 0.20,
          LandCoverType.urban: 0.08,
          LandCoverType.water: 0.05,
          LandCoverType.bareland: 0.04,
          LandCoverType.wetland: 0.03,
        },
      ),
      coordinates: const Coordinates(latitude: -1.2921, longitude: 36.8219),
      dataQuality: 0.89,
      lastUpdated: DateTime.now(),
    );
  }

  /// Creates mock temperature data for charts
  static List<TemperatureMeasurement> createMockTemperatureData() {
    return List.generate(30, (index) =>
      TemperatureMeasurement(
        date: DateTime(2024, 1, 1).add(Duration(days: index)),
        temperature: 25.0 + (index % 10),
        quality: 0.9 + (index % 10) * 0.01,
        source: 'MockWeatherStation',
      ),
    );
  }

  /// Creates mock rainfall data for charts
  static List<RainfallMeasurement> createMockRainfallData() {
    return List.generate(30, (index) =>
      RainfallMeasurement(
        date: DateTime(2024, 1, 1).add(Duration(days: index)),
        rainfall: (index % 5) * 2.5,
        quality: 0.85 + (index % 15) * 0.01,
        source: 'MockRainGauge',
      ),
    );
  }

  /// Creates mock humidity data for charts
  static List<HumidityMeasurement> createMockHumidityData() {
    return List.generate(30, (index) =>
      HumidityMeasurement(
        date: DateTime(2024, 1, 1).add(Duration(days: index)),
        humidity: 60.0 + (index % 30),
        quality: 0.88 + (index % 12) * 0.01,
        source: 'MockHumiditySensor',
      ),
    );
  }

  /// Creates mock risk distribution data for charts
  static Map<RiskLevel, int> createMockRiskDistributionData() {
    return {
      RiskLevel.low: 150,
      RiskLevel.medium: 85,
      RiskLevel.high: 45,
      RiskLevel.critical: 12,
    };
  }

  /// Creates mock confusion matrix data
  static Map<String, int> createMockConfusionMatrix() {
    return {
      'true_positive': 185,
      'false_positive': 25,
      'true_negative': 220,
      'false_negative': 35,
    };
  }

  /// Creates mock model comparison data
  static List<ModelPerformance> createMockModelComparisonData() {
    return [
      ModelPerformance(
        modelName: 'Random Forest',
        accuracy: 0.85,
        precision: 0.88,
        recall: 0.83,
        f1Score: 0.855,
      ),
      ModelPerformance(
        modelName: 'Neural Network',
        accuracy: 0.82,
        precision: 0.84,
        recall: 0.81,
        f1Score: 0.825,
      ),
      ModelPerformance(
        modelName: 'SVM',
        accuracy: 0.79,
        precision: 0.81,
        recall: 0.78,
        f1Score: 0.795,
      ),
    ];
  }

  /// Creates mock correlation data
  static Map<String, double> createMockCorrelationData() {
    return {
      'temperature_rainfall': 0.65,
      'temperature_humidity': 0.72,
      'temperature_vegetation': 0.58,
      'rainfall_humidity': 0.45,
      'rainfall_vegetation': 0.82,
      'humidity_vegetation': 0.38,
      'malaria_temperature': 0.68,
      'malaria_rainfall': 0.75,
      'malaria_humidity': 0.52,
      'malaria_vegetation': 0.61,
    };
  }

  /// Creates mock use case parameters
  static GetAnalyticsDataParams createMockGetAnalyticsDataParams() {
    return GetAnalyticsDataParams(
      region: 'Kenya',
      dateRange: DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      ),
      filters: createMockAnalyticsFilters(),
    );
  }

  /// Creates mock chart generation parameters
  static GenerateChartDataParams createMockGenerateChartDataParams() {
    return GenerateChartDataParams(
      chartType: ChartType.lineChart,
      dataType: ChartDataType.predictionAccuracy,
      region: 'Kenya',
      dateRange: DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      ),
    );
  }

  /// Creates mock export format
  static ExportFormat createMockExportFormat() {
    return ExportFormat.pdf;
  }
}

/// Additional chart data entities for testing

/// Chart point entity
class ChartPoint {
  final double x;
  final double y;

  const ChartPoint({required this.x, required this.y});
}

/// Chart series entity
class ChartSeries {
  final String id;
  final String name;
  final List<ChartPoint> data;
  final Color color;
  final double strokeWidth;
  final bool fillArea;
  final Color? fillColor;

  const ChartSeries({
    required this.id,
    required this.name,
    required this.data,
    required this.color,
    this.strokeWidth = 2.0,
    this.fillArea = false,
    this.fillColor,
  });
}

/// Chart axis entity
class ChartAxis {
  final String title;
  final double? min;
  final double? max;
  final double? interval;
  final bool showLabels;
  final String Function(double)? labelFormatter;
  final TextStyle? labelStyle;

  const ChartAxis({
    required this.title,
    this.min,
    this.max,
    this.interval,
    this.showLabels = true,
    this.labelFormatter,
    this.labelStyle,
  });
}

/// Line chart data entity
class LineChartDataEntity {
  final List<ChartSeries> series;
  final ChartAxis xAxis;
  final ChartAxis yAxis;
  final bool showGrid;
  final bool showMarkers;

  const LineChartDataEntity({
    required this.series,
    required this.xAxis,
    required this.yAxis,
    this.showGrid = true,
    this.showMarkers = false,
  });
}

/// Bar chart data entity
class BarChartDataEntity {
  final List<BarChartGroup> dataGroups;
  final ChartAxis xAxis;
  final ChartAxis yAxis;
  final bool showGrid;
  final double barWidth;

  const BarChartDataEntity({
    required this.dataGroups,
    required this.xAxis,
    required this.yAxis,
    this.showGrid = true,
    this.barWidth = 0.8,
  });
}

/// Bar chart group entity
class BarChartGroup {
  final int x;
  final List<BarValue> bars;

  const BarChartGroup({required this.x, required this.bars});
}

/// Bar value entity
class BarValue {
  final String category;
  final double value;
  final Color? color;

  const BarValue({required this.category, required this.value, this.color});
}

/// Pie chart data entity
class PieChartDataEntity {
  final List<PieSlice> sections;
  final double centerSpaceRadius;

  const PieChartDataEntity({
    required this.sections,
    this.centerSpaceRadius = 0.0,
  });
}

/// Pie slice entity
class PieSlice {
  final String label;
  final double value;
  final Color color;
  final double radius;
  final bool showLabel;
  final TextStyle? labelStyle;

  const PieSlice({
    required this.label,
    required this.value,
    required this.color,
    this.radius = 60.0,
    this.showLabel = true,
    this.labelStyle,
  });
}

/// Scatter plot data entity
class ScatterPlotDataEntity {
  final List<ScatterSeries> series;
  final ChartAxis xAxis;
  final ChartAxis yAxis;
  final bool showGrid;

  const ScatterPlotDataEntity({
    required this.series,
    required this.xAxis,
    required this.yAxis,
    this.showGrid = true,
  });
}

/// Scatter series entity
class ScatterSeries {
  final String id;
  final String name;
  final List<ScatterPoint> data;
  final Color color;
  final double pointSize;

  const ScatterSeries({
    required this.id,
    required this.name,
    required this.data,
    required this.color,
    this.pointSize = 4.0,
  });
}

/// Scatter point entity
class ScatterPoint {
  final double x;
  final double y;
  final double? size;
  final Color? color;

  const ScatterPoint({
    required this.x,
    required this.y,
    this.size,
    this.color,
  });
}

/// Chart interaction entities
enum ChartInteractionType { tap, doubleTap, longPress, pan, zoom }

class ChartInteraction {
  final ChartInteractionType type;
  final Offset position;
  final DateTime timestamp;
  final Map<String, dynamic> data;

  const ChartInteraction({
    required this.type,
    required this.position,
    required this.timestamp,
    required this.data,
  });
}

class ChartInteractionConfig {
  final bool enableZoom;
  final bool enablePan;
  final bool enableTooltips;
  final bool enableDrillDown;
  final bool enableAnimations;
  final Duration animationDuration;

  const ChartInteractionConfig({
    this.enableZoom = false,
    this.enablePan = false,
    this.enableTooltips = true,
    this.enableDrillDown = false,
    this.enableAnimations = true,
    this.animationDuration = const Duration(milliseconds: 300),
  });

  ChartInteractionConfig copyWith({
    bool? enableZoom,
    bool? enablePan,
    bool? enableTooltips,
    bool? enableDrillDown,
    bool? enableAnimations,
    Duration? animationDuration,
  }) {
    return ChartInteractionConfig(
      enableZoom: enableZoom ?? this.enableZoom,
      enablePan: enablePan ?? this.enablePan,
      enableTooltips: enableTooltips ?? this.enableTooltips,
      enableDrillDown: enableDrillDown ?? this.enableDrillDown,
      enableAnimations: enableAnimations ?? this.enableAnimations,
      animationDuration: animationDuration ?? this.animationDuration,
    );
  }
}

class ChartViewState {
  final double zoomLevel;
  final Offset panOffset;
  final List<dynamic> selectedDataPoints;
  final List<ChartInteraction> interactionHistory;

  const ChartViewState({
    this.zoomLevel = 1.0,
    this.panOffset = Offset.zero,
    this.selectedDataPoints = const [],
    this.interactionHistory = const [],
  });
}

/// Interactive chart entities
enum InteractiveChartType { line, bar, pie, scatter, area }

class InteractiveChart {
  final String id;
  final String title;
  final InteractiveChartType chartType;
  final dynamic chartData;
  final ChartInteractionConfig interactionConfig;
  final ChartViewState viewState;
  final ChartThemeData? theme;
  final DrillDownHierarchy? drillDownHierarchy;
  final RealTimeConfig? realTimeConfig;

  const InteractiveChart({
    required this.id,
    required this.title,
    required this.chartType,
    required this.chartData,
    required this.interactionConfig,
    required this.viewState,
    this.theme,
    this.drillDownHierarchy,
    this.realTimeConfig,
  });

  InteractiveChart copyWith({
    String? id,
    String? title,
    InteractiveChartType? chartType,
    dynamic chartData,
    ChartInteractionConfig? interactionConfig,
    ChartViewState? viewState,
    ChartThemeData? theme,
    DrillDownHierarchy? drillDownHierarchy,
    RealTimeConfig? realTimeConfig,
  }) {
    return InteractiveChart(
      id: id ?? this.id,
      title: title ?? this.title,
      chartType: chartType ?? this.chartType,
      chartData: chartData ?? this.chartData,
      interactionConfig: interactionConfig ?? this.interactionConfig,
      viewState: viewState ?? this.viewState,
      theme: theme ?? this.theme,
      drillDownHierarchy: drillDownHierarchy ?? this.drillDownHierarchy,
      realTimeConfig: realTimeConfig ?? this.realTimeConfig,
    );
  }

  bool canDrillDown() => drillDownHierarchy?.availableOptions.isNotEmpty ?? false;
  bool canDrillUp() => drillDownHierarchy?.navigationPath.isNotEmpty ?? false;

  List<DrillDownOption> getAvailableDrillDownOptions() {
    return drillDownHierarchy?.availableOptions ?? [];
  }

  Map<String, dynamic> getPerformanceStats() {
    return {
      'interactionCount': viewState.interactionHistory.length,
      'lastRenderTime': 16.7, // Mock render time in ms
      'memoryUsage': 1024 * 256, // Mock memory usage in bytes
    };
  }

  InteractiveChart zoom({required double zoomFactor, required Offset centerPoint}) {
    return copyWith(
      viewState: ChartViewState(
        zoomLevel: viewState.zoomLevel * zoomFactor,
        panOffset: viewState.panOffset,
        selectedDataPoints: viewState.selectedDataPoints,
        interactionHistory: [
          ...viewState.interactionHistory,
          ChartInteraction(
            type: ChartInteractionType.zoom,
            position: centerPoint,
            timestamp: DateTime.now(),
            data: {'zoomFactor': zoomFactor},
          ),
        ],
      ),
    );
  }

  InteractiveChart pan({required Offset panDelta}) {
    return copyWith(
      viewState: ChartViewState(
        zoomLevel: viewState.zoomLevel,
        panOffset: viewState.panOffset + panDelta,
        selectedDataPoints: viewState.selectedDataPoints,
        interactionHistory: [
          ...viewState.interactionHistory,
          ChartInteraction(
            type: ChartInteractionType.pan,
            position: panDelta,
            timestamp: DateTime.now(),
            data: {'panDelta': {'dx': panDelta.dx, 'dy': panDelta.dy}},
          ),
        ],
      ),
    );
  }

  InteractiveChart reset() {
    return copyWith(
      viewState: ChartViewState(
        zoomLevel: 1.0,
        panOffset: Offset.zero,
        selectedDataPoints: [],
        interactionHistory: [
          ...viewState.interactionHistory,
          ChartInteraction(
            type: ChartInteractionType.tap,
            position: Offset.zero,
            timestamp: DateTime.now(),
            data: {'action': 'reset'},
          ),
        ],
      ),
    );
  }
}

class DrillDownHierarchy {
  final String currentLevel;
  final List<String> navigationPath;
  final List<DrillDownOption> availableOptions;

  const DrillDownHierarchy({
    required this.currentLevel,
    required this.navigationPath,
    required this.availableOptions,
  });

  List<String> getBreadcrumbPath() => navigationPath;
}

class DrillDownOption {
  final String label;
  final String targetDimension;
  final dynamic value;

  const DrillDownOption({
    required this.label,
    required this.targetDimension,
    required this.value,
  });
}

class RealTimeConfig {
  final bool enabled;
  final Duration updateInterval;

  const RealTimeConfig({
    this.enabled = false,
    this.updateInterval = const Duration(seconds: 30),
  });
}

/// Chart data types and enums
enum ChartType { lineChart, barChart, pieChart, scatterPlot, areaChart }
enum ChartDataType { predictionAccuracy, environmentalTrends, riskDistribution }

/// Export format enum
enum ExportFormat { pdf, excel, csv, png }

/// Model performance entity
class ModelPerformance {
  final String modelName;
  final double accuracy;
  final double precision;
  final double recall;
  final double f1Score;

  const ModelPerformance({
    required this.modelName,
    required this.accuracy,
    required this.precision,
    required this.recall,
    required this.f1Score,
  });
}

/// Data summary entity
class DataSummary {
  final int totalRecords;
  final double completeness;
  final double qualityScore;
  final DateTime lastUpdated;

  const DataSummary({
    required this.totalRecords,
    required this.completeness,
    required this.qualityScore,
    required this.lastUpdated,
  });
}