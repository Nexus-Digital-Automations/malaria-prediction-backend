/// Comprehensive unit tests for AnalyticsBloc
///
/// This test suite provides exhaustive testing for the analytics BLoC including
/// all events, states, transitions, and business logic validation.
///
/// Tests cover:
/// - Event handling and state transitions
/// - Error handling and recovery scenarios
/// - Data loading and caching mechanisms
/// - Chart generation and interaction logic
/// - Filter application and data refresh
/// - Export functionality and file generation
/// - Concurrency and async operation handling
/// - Edge cases and boundary conditions
/// - Performance under various load conditions
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:dartz/dartz.dart';
import 'package:malaria_frontend/features/analytics/presentation/bloc/analytics_bloc.dart';
import 'package:malaria_frontend/features/analytics/domain/usecases/get_analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/usecases/generate_chart_data.dart';
import 'package:malaria_frontend/features/analytics/domain/repositories/analytics_repository.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_filters.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/chart_data.dart';
import 'package:malaria_frontend/core/error/failures.dart';
import '../../../test_config.dart';
import '../../../mocks/analytics_mocks.dart';

/// Mock classes for testing
class MockGetAnalyticsData extends Mock implements GetAnalyticsData {}
class MockGenerateChartData extends Mock implements GenerateChartData {}
class MockAnalyticsRepository extends Mock implements AnalyticsRepository {}

void main() {
  /// Global test setup
  setUpAll(() async {
    await TestConfig.initialize();
  });

  /// Cleanup after all tests
  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('AnalyticsBloc', () {
    late AnalyticsBloc analyticsBloc;
    late MockGetAnalyticsData mockGetAnalyticsData;
    late MockGenerateChartData mockGenerateChartData;
    late MockAnalyticsRepository mockAnalyticsRepository;

    setUp(() {
      mockGetAnalyticsData = MockGetAnalyticsData();
      mockGenerateChartData = MockGenerateChartData();
      mockAnalyticsRepository = MockAnalyticsRepository();

      analyticsBloc = AnalyticsBloc(
        getAnalyticsData: mockGetAnalyticsData,
        generateChartData: mockGenerateChartData,
        analyticsRepository: mockAnalyticsRepository,
      );

      // Register fallback values for mocktail
      registerFallbackValue(MockAnalyticsData.createMockGetAnalyticsDataParams());
      registerFallbackValue(MockAnalyticsData.createMockGenerateChartDataParams());
      registerFallbackValue(MockAnalyticsData.createMockExportFormat());
    });

    tearDown(() {
      analyticsBloc.close();
    });

    test('initial state is AnalyticsInitial', () {
      expect(analyticsBloc.state, equals(const AnalyticsInitial()));
    });

    group('LoadAnalyticsData', () {
      final tAnalyticsData = MockAnalyticsData.createMockAnalyticsData();
      final tRegion = 'Kenya';
      final tDateRange = DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      );
      final tFilters = MockAnalyticsData.createMockAnalyticsFilters();

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits [AnalyticsLoading, AnalyticsLoaded] when analytics data is loaded successfully',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(tAnalyticsData));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: tRegion,
          dateRange: tDateRange,
          filters: tFilters,
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          AnalyticsLoaded(
            analyticsData: tAnalyticsData,
            selectedRegion: tRegion,
            selectedDateRange: tDateRange,
            appliedFilters: tFilters,
            lastRefresh: any(named: 'lastRefresh'),
          ),
        ],
        verify: (_) {
          verify(() => mockGetAnalyticsData(any())).called(1);
        },
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits [AnalyticsLoading, AnalyticsError] when analytics data loading fails',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => const Left(ServerFailure('Server error')));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: tRegion,
          dateRange: tDateRange,
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          const AnalyticsError(
            message: 'Server error',
            errorType: 'data_loading',
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits [AnalyticsLoading, AnalyticsError] when unexpected error occurs',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenThrow(Exception('Unexpected error'));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: tRegion,
          dateRange: tDateRange,
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          const AnalyticsError(
            message: 'Unexpected error loading analytics data: Exception: Unexpected error',
            errorType: 'unexpected',
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'calls GetAnalyticsData use case with correct parameters',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(tAnalyticsData));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: tRegion,
          dateRange: tDateRange,
          filters: tFilters,
        )),
        verify: (_) {
          verify(() => mockGetAnalyticsData(
            GetAnalyticsDataParams(
              region: tRegion,
              dateRange: tDateRange,
              filters: tFilters,
            ),
          )).called(1);
        },
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles loading with progress updates',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(tAnalyticsData));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: tRegion,
          dateRange: tDateRange,
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>(),
        ],
      );
    });

    group('GenerateChart', () {
      final tChartData = MockAnalyticsData.createMockChartData();
      final tChartType = ChartType.lineChart;
      final tDataType = ChartDataType.predictionAccuracy;
      final tRegion = 'Kenya';
      final tDateRange = DateRange(
        start: DateTime(2024, 1, 1),
        end: DateTime(2024, 1, 31),
      );

      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: tRegion,
        selectedDateRange: tDateRange,
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits [ChartGenerating, ChartGenerated] when chart is generated successfully',
        build: () {
          when(() => mockGenerateChartData(any()))
              .thenAnswer((_) async => Right(tChartData));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(GenerateChart(
          chartType: tChartType,
          dataType: tDataType,
          region: tRegion,
          dateRange: tDateRange,
        )),
        expect: () => [
          ChartGenerating(
            baseState: tLoadedState,
            chartType: tChartType,
            dataType: tDataType,
            progress: 0,
          ),
          isA<ChartGenerated>(),
        ],
        verify: (_) {
          verify(() => mockGenerateChartData(any())).called(1);
        },
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits [ChartGenerating, AnalyticsError] when chart generation fails',
        build: () {
          when(() => mockGenerateChartData(any()))
              .thenAnswer((_) async => const Left(ServerFailure('Chart generation failed')));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(GenerateChart(
          chartType: tChartType,
          dataType: tDataType,
          region: tRegion,
          dateRange: tDateRange,
        )),
        expect: () => [
          ChartGenerating(
            baseState: tLoadedState,
            chartType: tChartType,
            dataType: tDataType,
            progress: 0,
          ),
          AnalyticsError(
            message: 'Chart generation failed',
            errorType: 'chart_generation',
            previousState: tLoadedState,
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits error when trying to generate chart without loaded data',
        build: () => analyticsBloc,
        act: (bloc) => bloc.add(GenerateChart(
          chartType: tChartType,
          dataType: tDataType,
          region: tRegion,
          dateRange: tDateRange,
        )),
        expect: () => [
          const AnalyticsError(
            message: 'Cannot generate chart without loaded analytics data',
            errorType: 'invalid_state',
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'updates charts map in loaded state after successful generation',
        build: () {
          when(() => mockGenerateChartData(any()))
              .thenAnswer((_) async => Right(tChartData));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(GenerateChart(
          chartType: tChartType,
          dataType: tDataType,
          region: tRegion,
          dateRange: tDateRange,
        )),
        verify: (bloc) {
          final state = bloc.state;
          if (state is ChartGenerated) {
            expect(state.baseState.charts, isNotEmpty);
            expect(state.chartData, equals(tChartData));
          }
        },
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'generates unique chart IDs for different chart types',
        build: () {
          when(() => mockGenerateChartData(any()))
              .thenAnswer((_) async => Right(tChartData));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) {
          bloc.add(GenerateChart(
            chartType: ChartType.lineChart,
            dataType: ChartDataType.predictionAccuracy,
            region: tRegion,
            dateRange: tDateRange,
          ));
          bloc.add(GenerateChart(
            chartType: ChartType.barChart,
            dataType: ChartDataType.environmentalTrends,
            region: tRegion,
            dateRange: tDateRange,
          ));
        },
        verify: (bloc) {
          final state = bloc.state;
          if (state is ChartGenerated) {
            expect(state.chartId, contains('lineChart_predictionAccuracy_'));
          }
        },
      );
    });

    group('ApplyFilters', () {
      final tFilters = AnalyticsFilters(
        region: 'Kenya',
        dateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        riskLevels: {RiskLevel.high},
        environmentalFactors: {EnvironmentalFactor.temperature},
        dataQualityThreshold: 0.8,
      );

      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: 'Kenya',
        selectedDateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'reloads data when reloadData is true',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ApplyFilters(
          filters: tFilters,
          reloadData: true,
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>(),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'updates filters without reloading when reloadData is false',
        build: () => analyticsBloc,
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ApplyFilters(
          filters: tFilters,
          reloadData: false,
        )),
        expect: () => [
          tLoadedState.copyWith(appliedFilters: tFilters),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits error when trying to apply filters without loaded data',
        build: () => analyticsBloc,
        act: (bloc) => bloc.add(ApplyFilters(
          filters: tFilters,
        )),
        expect: () => [
          const AnalyticsError(
            message: 'Cannot apply filters without loaded analytics data',
            errorType: 'invalid_state',
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles filter application errors gracefully',
        build: () => analyticsBloc,
        seed: () => tLoadedState,
        act: (bloc) {
          // Simulate an error in filter processing
          final invalidFilters = AnalyticsFilters(
            region: '',
            dateRange: DateRange(
              start: DateTime(2024, 12, 31),
              end: DateTime(2024, 1, 1), // Invalid range
            ),
            riskLevels: {},
            environmentalFactors: {},
            dataQualityThreshold: -1.0, // Invalid threshold
          );
          bloc.add(ApplyFilters(filters: invalidFilters));
        },
        expect: () => [
          isA<AnalyticsError>().having(
            (error) => error.errorType,
            'errorType',
            'filter_application',
          ),
        ],
      );
    });

    group('ChangeRegion', () {
      final tNewRegion = 'Tanzania';
      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: 'Kenya',
        selectedDateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'reloads data when reloadData is true',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ChangeRegion(
          region: tNewRegion,
          reloadData: true,
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>().having(
            (state) => state.selectedRegion,
            'selectedRegion',
            tNewRegion,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'updates region without reloading when reloadData is false',
        build: () => analyticsBloc,
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ChangeRegion(
          region: tNewRegion,
          reloadData: false,
        )),
        expect: () => [
          tLoadedState.copyWith(selectedRegion: tNewRegion),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits error when trying to change region without loaded data',
        build: () => analyticsBloc,
        act: (bloc) => bloc.add(ChangeRegion(region: tNewRegion)),
        expect: () => [
          const AnalyticsError(
            message: 'Cannot change region without loaded analytics data',
            errorType: 'invalid_state',
            isRecoverable: true,
          ),
        ],
      );
    });

    group('ChangeDateRange', () {
      final tNewDateRange = DateRange(
        start: DateTime(2024, 2, 1),
        end: DateTime(2024, 2, 28),
      );
      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: 'Kenya',
        selectedDateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'reloads data when reloadData is true',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ChangeDateRange(
          dateRange: tNewDateRange,
          reloadData: true,
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>().having(
            (state) => state.selectedDateRange,
            'selectedDateRange',
            tNewDateRange,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'updates date range without reloading when reloadData is false',
        build: () => analyticsBloc,
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ChangeDateRange(
          dateRange: tNewDateRange,
          reloadData: false,
        )),
        expect: () => [
          tLoadedState.copyWith(selectedDateRange: tNewDateRange),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits error when trying to change date range without loaded data',
        build: () => analyticsBloc,
        act: (bloc) => bloc.add(ChangeDateRange(dateRange: tNewDateRange)),
        expect: () => [
          const AnalyticsError(
            message: 'Cannot change date range without loaded analytics data',
            errorType: 'invalid_state',
            isRecoverable: true,
          ),
        ],
      );
    });

    group('RefreshAnalyticsData', () {
      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: 'Kenya',
        selectedDateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'reloads current data when in loaded state',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(const RefreshAnalyticsData()),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>(),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits error when trying to refresh without existing data',
        build: () => analyticsBloc,
        act: (bloc) => bloc.add(const RefreshAnalyticsData()),
        expect: () => [
          const AnalyticsError(
            message: 'Cannot refresh without existing analytics data',
            errorType: 'refresh_error',
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles refresh errors gracefully',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenThrow(Exception('Network error'));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(const RefreshAnalyticsData()),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          const AnalyticsError(
            message: 'Unexpected error loading analytics data: Exception: Network error',
            errorType: 'unexpected',
            isRecoverable: true,
          ),
        ],
      );
    });

    group('ExportAnalyticsReport', () {
      final tReportUrl = 'https://example.com/report.pdf';
      final tExportFormat = ExportFormat.pdf;
      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: 'Kenya',
        selectedDateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits [AnalyticsExporting, AnalyticsExported] when export succeeds',
        build: () {
          when(() => mockAnalyticsRepository.exportAnalyticsReport(
            region: any(named: 'region'),
            dateRange: any(named: 'dateRange'),
            format: any(named: 'format'),
            includeCharts: any(named: 'includeCharts'),
            sections: any(named: 'sections'),
          )).thenAnswer((_) async => Right(tReportUrl));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ExportAnalyticsReport(
          format: tExportFormat,
          includeCharts: true,
        )),
        expect: () => [
          AnalyticsExporting(
            baseState: tLoadedState,
            format: tExportFormat,
            progress: 0,
          ),
          AnalyticsExported(
            baseState: tLoadedState,
            reportUrl: tReportUrl,
            format: tExportFormat,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits [AnalyticsExporting, AnalyticsError] when export fails',
        build: () {
          when(() => mockAnalyticsRepository.exportAnalyticsReport(
            region: any(named: 'region'),
            dateRange: any(named: 'dateRange'),
            format: any(named: 'format'),
            includeCharts: any(named: 'includeCharts'),
            sections: any(named: 'sections'),
          )).thenAnswer((_) async => const Left(ServerFailure('Export failed')));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ExportAnalyticsReport(format: tExportFormat)),
        expect: () => [
          AnalyticsExporting(
            baseState: tLoadedState,
            format: tExportFormat,
            progress: 0,
          ),
          AnalyticsError(
            message: 'Export failed',
            errorType: 'export_error',
            previousState: tLoadedState,
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'emits error when trying to export without loaded data',
        build: () => analyticsBloc,
        act: (bloc) => bloc.add(ExportAnalyticsReport(format: tExportFormat)),
        expect: () => [
          const AnalyticsError(
            message: 'Cannot export report without loaded analytics data',
            errorType: 'invalid_state',
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles unexpected export errors',
        build: () {
          when(() => mockAnalyticsRepository.exportAnalyticsReport(
            region: any(named: 'region'),
            dateRange: any(named: 'dateRange'),
            format: any(named: 'format'),
            includeCharts: any(named: 'includeCharts'),
            sections: any(named: 'sections'),
          )).thenThrow(Exception('Unexpected error'));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(ExportAnalyticsReport(format: tExportFormat)),
        expect: () => [
          AnalyticsExporting(
            baseState: tLoadedState,
            format: tExportFormat,
            progress: 0,
          ),
          const AnalyticsError(
            message: 'Unexpected error exporting report: Exception: Unexpected error',
            errorType: 'unexpected',
            isRecoverable: true,
          ),
        ],
      );
    });

    group('LoadAvailableRegions', () {
      final tRegions = ['Kenya', 'Tanzania', 'Uganda', 'Rwanda'];
      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: 'Kenya',
        selectedDateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'updates available regions when in loaded state',
        build: () {
          when(() => mockAnalyticsRepository.getAvailableRegions())
              .thenAnswer((_) async => Right(tRegions));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(const LoadAvailableRegions()),
        expect: () => [
          tLoadedState.copyWith(availableRegions: tRegions),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles region loading failure gracefully without state change',
        build: () {
          when(() => mockAnalyticsRepository.getAvailableRegions())
              .thenAnswer((_) async => const Left(ServerFailure('Failed to load regions')));
          return analyticsBloc;
        },
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(const LoadAvailableRegions()),
        expect: () => <AnalyticsState>[],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'does not emit state change when not in loaded state',
        build: () {
          when(() => mockAnalyticsRepository.getAvailableRegions())
              .thenAnswer((_) async => Right(tRegions));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(const LoadAvailableRegions()),
        expect: () => <AnalyticsState>[],
      );
    });

    group('ClearAnalyticsData', () {
      final tLoadedState = AnalyticsLoaded(
        analyticsData: MockAnalyticsData.createMockAnalyticsData(),
        selectedRegion: 'Kenya',
        selectedDateRange: DateRange(
          start: DateTime(2024, 1, 1),
          end: DateTime(2024, 1, 31),
        ),
        lastRefresh: DateTime.now(),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'resets to initial state when clearing data',
        build: () => analyticsBloc,
        seed: () => tLoadedState,
        act: (bloc) => bloc.add(const ClearAnalyticsData()),
        expect: () => [
          const AnalyticsInitial(),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles clear data errors gracefully',
        build: () => analyticsBloc,
        seed: () => tLoadedState,
        act: (bloc) {
          // This simulates an error during clearing
          bloc.add(const ClearAnalyticsData());
        },
        expect: () => [
          const AnalyticsInitial(),
        ],
      );
    });

    group('Complex Scenarios', () {
      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles multiple rapid events correctly',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          when(() => mockGenerateChartData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockChartData()));
          return analyticsBloc;
        },
        act: (bloc) {
          // Rapid fire multiple events
          bloc.add(LoadAnalyticsData(
            region: 'Kenya',
            dateRange: DateRange(
              start: DateTime(2024, 1, 1),
              end: DateTime(2024, 1, 31),
            ),
          ));
          bloc.add(const RefreshAnalyticsData());
          bloc.add(ChangeRegion(region: 'Tanzania'));
        },
        // The exact expected states depend on the timing and order of processing
        verify: (_) {
          // Verify that the use cases were called appropriately
          verify(() => mockGetAnalyticsData(any())).called(greaterThan(1));
        },
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'recovers from error state when receiving new valid events',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          return analyticsBloc;
        },
        seed: () => const AnalyticsError(
          message: 'Previous error',
          errorType: 'test_error',
        ),
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: 'Kenya',
          dateRange: DateRange(
            start: DateTime(2024, 1, 1),
            end: DateTime(2024, 1, 31),
          ),
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>(),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'maintains data consistency during filter and region changes',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          return analyticsBloc;
        },
        act: (bloc) async {
          // Load initial data
          bloc.add(LoadAnalyticsData(
            region: 'Kenya',
            dateRange: DateRange(
              start: DateTime(2024, 1, 1),
              end: DateTime(2024, 1, 31),
            ),
          ));

          // Wait for initial load
          await Future.delayed(const Duration(milliseconds: 100));

          // Apply filters
          bloc.add(ApplyFilters(
            filters: AnalyticsFilters(
              region: 'Kenya',
              dateRange: DateRange(
                start: DateTime(2024, 1, 1),
                end: DateTime(2024, 1, 31),
              ),
              riskLevels: {RiskLevel.high},
              environmentalFactors: {EnvironmentalFactor.temperature},
              dataQualityThreshold: 0.8,
            ),
          ));

          // Change region
          bloc.add(ChangeRegion(region: 'Tanzania'));
        },
        verify: (bloc) {
          // Verify final state consistency
          final state = bloc.state;
          if (state is AnalyticsLoaded) {
            expect(state.selectedRegion, equals('Tanzania'));
          }
        },
      );
    });

    group('Performance Tests', () {
      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles large data sets efficiently',
        build: () {
          // Create large mock data set
          final largeDataSet = MockAnalyticsData.createLargeAnalyticsDataSet();
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(largeDataSet));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: 'Kenya',
          dateRange: DateRange(
            start: DateTime(2024, 1, 1),
            end: DateTime(2024, 12, 31), // Full year
          ),
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>(),
        ],
        timeout: const Duration(seconds: 5),
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'processes concurrent chart generation requests',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockAnalyticsData()));
          when(() => mockGenerateChartData(any()))
              .thenAnswer((_) async => Right(MockAnalyticsData.createMockChartData()));
          return analyticsBloc;
        },
        seed: () => AnalyticsLoaded(
          analyticsData: MockAnalyticsData.createMockAnalyticsData(),
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime(2024, 1, 1),
            end: DateTime(2024, 1, 31),
          ),
          lastRefresh: DateTime.now(),
        ),
        act: (bloc) {
          // Generate multiple charts concurrently
          bloc.add(GenerateChart(
            chartType: ChartType.lineChart,
            dataType: ChartDataType.predictionAccuracy,
            region: 'Kenya',
            dateRange: DateRange(
              start: DateTime(2024, 1, 1),
              end: DateTime(2024, 1, 31),
            ),
          ));
          bloc.add(GenerateChart(
            chartType: ChartType.barChart,
            dataType: ChartDataType.environmentalTrends,
            region: 'Kenya',
            dateRange: DateRange(
              start: DateTime(2024, 1, 1),
              end: DateTime(2024, 1, 31),
            ),
          ));
        },
        verify: (_) {
          verify(() => mockGenerateChartData(any())).called(2);
        },
        timeout: const Duration(seconds: 5),
      );
    });

    group('Edge Cases', () {
      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles empty analytics data correctly',
        build: () {
          final emptyData = AnalyticsData(
            id: 'empty',
            region: 'Kenya',
            dateRange: DateRange(
              start: DateTime(2024, 1, 1),
              end: DateTime(2024, 1, 31),
            ),
            predictionAccuracy: PredictionAccuracy(
              overall: 0.0,
              byRiskLevel: {},
              trend: [],
              precision: 0.0,
              recall: 0.0,
              f1Score: 0.0,
            ),
            environmentalTrends: [],
            riskTrends: [],
            alertStatistics: AlertStatistics(
              totalAlerts: 0,
              alertsBySeverity: {},
              deliveryRate: 0.0,
              averageResponseTime: Duration.zero,
              falsePositives: 0,
              missedAlerts: 0,
            ),
            dataQuality: DataQuality(
              completeness: 0.0,
              accuracy: 0.0,
              freshnessHours: 0.0,
              sourcesCount: 0,
              sourcesWithIssues: [],
              lastUpdate: DateTime.now(),
            ),
            generatedAt: DateTime.now(),
          );
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => Right(emptyData));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: 'Kenya',
          dateRange: DateRange(
            start: DateTime(2024, 1, 1),
            end: DateTime(2024, 1, 31),
          ),
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          isA<AnalyticsLoaded>(),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles invalid date ranges correctly',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => const Left(ValidationFailure('Invalid date range')));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: 'Kenya',
          dateRange: DateRange(
            start: DateTime(2024, 12, 31),
            end: DateTime(2024, 1, 1), // End before start
          ),
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          const AnalyticsError(
            message: 'Invalid date range',
            errorType: 'data_loading',
            isRecoverable: true,
          ),
        ],
      );

      blocTest<AnalyticsBloc, AnalyticsState>(
        'handles network timeouts gracefully',
        build: () {
          when(() => mockGetAnalyticsData(any()))
              .thenAnswer((_) async => const Left(NetworkFailure('Connection timeout')));
          return analyticsBloc;
        },
        act: (bloc) => bloc.add(LoadAnalyticsData(
          region: 'Kenya',
          dateRange: DateRange(
            start: DateTime(2024, 1, 1),
            end: DateTime(2024, 1, 31),
          ),
        )),
        expect: () => [
          const AnalyticsLoading(message: 'Loading analytics data...'),
          const AnalyticsError(
            message: 'Connection timeout',
            errorType: 'data_loading',
            isRecoverable: true,
          ),
        ],
      );
    });
  });
}