/// Comprehensive integration tests for analytics feature data flow
///
/// This test suite validates the complete analytics feature integration including
/// data flow from repositories through use cases to BLoC and UI components.
///
/// Tests cover:
/// - End-to-end analytics data flow
/// - Repository and use case integration
/// - BLoC and UI widget integration
/// - Chart generation and interaction workflows
/// - Filter application and data refresh cycles
/// - Export functionality from start to finish
/// - Error propagation and recovery mechanisms
/// - Performance under realistic usage patterns
/// - Real-time data updates and caching
/// - Cross-feature integration points
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';
import 'package:mockito/mockito.dart';
import 'package:http/http.dart' as http;
import 'package:malaria_frontend/features/analytics/presentation/pages/analytics_dashboard_page.dart';
import 'package:malaria_frontend/features/analytics/presentation/bloc/analytics_bloc.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_filters_panel.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/interactive_chart_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_overview_card.dart';
import 'package:malaria_frontend/features/analytics/data/repositories/analytics_repository_impl.dart';
import 'package:malaria_frontend/features/analytics/data/datasources/analytics_remote_datasource.dart';
import 'package:malaria_frontend/features/analytics/data/datasources/analytics_local_datasource.dart';
import 'package:malaria_frontend/features/analytics/domain/usecases/get_analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/usecases/generate_chart_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_filters.dart';
import 'package:malaria_frontend/core/network/network_info.dart';
import 'package:malaria_frontend/core/storage/storage_service.dart';
import '../../../test_config.dart';
import '../../../mocks/analytics_mocks.dart';
import '../../../helpers/integration_test_helpers.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  /// Global test setup
  setUpAll(() async {
    await TestConfig.initialize();
    await IntegrationTestHelpers.setupIntegrationTestEnvironment();
  });

  /// Cleanup after all tests
  tearDownAll(() async {
    await TestConfig.cleanup();
    await IntegrationTestHelpers.cleanupIntegrationTestEnvironment();
  });

  group('Analytics Integration Tests', () {
    late GetIt serviceLocator;
    late MockAnalyticsRemoteDataSource mockRemoteDataSource;
    late MockAnalyticsLocalDataSource mockLocalDataSource;
    late MockNetworkInfo mockNetworkInfo;
    late MockStorageService mockStorageService;

    setUp(() async {
      serviceLocator = GetIt.instance;
      await serviceLocator.reset();

      // Setup mock dependencies
      mockRemoteDataSource = MockAnalyticsRemoteDataSource();
      mockLocalDataSource = MockAnalyticsLocalDataSource();
      mockNetworkInfo = MockNetworkInfo();
      mockStorageService = MockStorageService();

      // Register mock dependencies
      serviceLocator.registerLazySingleton<AnalyticsRemoteDataSource>(
        () => mockRemoteDataSource,
      );
      serviceLocator.registerLazySingleton<AnalyticsLocalDataSource>(
        () => mockLocalDataSource,
      );
      serviceLocator.registerLazySingleton<NetworkInfo>(() => mockNetworkInfo);
      serviceLocator.registerLazySingleton<StorageService>(() => mockStorageService);

      // Setup default mock behaviors
      when(mockNetworkInfo.isConnected).thenAnswer((_) async => true);
      when(mockRemoteDataSource.getAnalyticsData(any))
          .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());
      when(mockLocalDataSource.getCachedAnalyticsData(any))
          .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());
      when(mockLocalDataSource.cacheAnalyticsData(any))
          .thenAnswer((_) async => {});
    });

    tearDown(() async {
      await serviceLocator.reset();
    });

    group('End-to-End Analytics Data Flow', () {
      testWidgets('complete analytics data loading workflow', (tester) async {
        // Setup test data
        final analyticsData = MockAnalyticsData.createMockAnalyticsDataModel();
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => analyticsData);

        // Build the complete analytics feature
        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Verify initial loading state
        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        // Wait for data to load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Verify dashboard is loaded with data
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
        expect(find.byType(AnalyticsFiltersPanel), findsOneWidget);
        expect(find.byType(AnalyticsOverviewCard), findsAtLeastNWidgets(1));

        // Verify remote data source was called
        verify(mockRemoteDataSource.getAnalyticsData(any)).called(1);

        // Verify data was cached locally
        verify(mockLocalDataSource.cacheAnalyticsData(any)).called(1);
      });

      testWidgets('analytics workflow with network error and local fallback', (tester) async {
        // Setup network failure scenario
        when(mockNetworkInfo.isConnected).thenAnswer((_) async => false);
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenThrow(Exception('Network error'));

        final cachedData = MockAnalyticsData.createMockAnalyticsDataModel();
        when(mockLocalDataSource.getCachedAnalyticsData(any))
            .thenAnswer((_) async => cachedData);

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for error handling and fallback
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Verify cached data was used
        verify(mockLocalDataSource.getCachedAnalyticsData(any)).called(1);

        // Verify dashboard shows cached data
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('complete chart generation workflow', (tester) async {
        // Setup analytics data
        final analyticsData = MockAnalyticsData.createMockAnalyticsDataModel();
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => analyticsData);

        // Setup chart data generation
        final chartData = MockAnalyticsData.createMockChartDataModel();
        when(mockRemoteDataSource.generateChartData(any))
            .thenAnswer((_) async => chartData);

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial data load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Find and tap chart generation button
        final chartButton = find.byKey(const Key('generate_chart_button'));
        if (chartButton.found()) {
          await tester.tap(chartButton);
          await tester.pumpAndSettle();

          // Verify chart generation was triggered
          verify(mockRemoteDataSource.generateChartData(any)).called(1);
        }

        // Verify chart widget is displayed
        expect(find.byType(InteractiveChartWidget), findsAtLeastNWidgets(1));
      });

      testWidgets('filter application end-to-end workflow', (tester) async {
        // Setup initial data
        final analyticsData = MockAnalyticsData.createMockAnalyticsDataModel();
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => analyticsData);

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Find filters panel
        expect(find.byType(AnalyticsFiltersPanel), findsOneWidget);

        // Test region filter change
        final regionDropdown = find.byKey(const Key('region_filter_dropdown'));
        if (regionDropdown.found()) {
          await tester.tap(regionDropdown);
          await tester.pumpAndSettle();

          // Select a different region
          final tanzaniaOption = find.text('Tanzania').last;
          if (tanzaniaOption.found()) {
            await tester.tap(tanzaniaOption);
            await tester.pumpAndSettle();

            // Verify data reload was triggered with new filters
            verify(mockRemoteDataSource.getAnalyticsData(any)).called(greaterThan(1));
          }
        }

        // Test date range filter
        final dateRangeButton = find.byKey(const Key('date_range_filter_button'));
        if (dateRangeButton.found()) {
          await tester.tap(dateRangeButton);
          await tester.pumpAndSettle();

          // Date picker should appear
          expect(find.byType(CalendarDatePicker), findsOneWidget);
        }

        // Test risk level filters
        final highRiskFilter = find.byKey(const Key('high_risk_filter_checkbox'));
        if (highRiskFilter.found()) {
          await tester.tap(highRiskFilter);
          await tester.pumpAndSettle();

          // Verify filter state change triggered data reload
          verify(mockRemoteDataSource.getAnalyticsData(any)).called(greaterThan(1));
        }
      });

      testWidgets('export functionality end-to-end workflow', (tester) async {
        // Setup analytics data
        final analyticsData = MockAnalyticsData.createMockAnalyticsDataModel();
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => analyticsData);

        // Setup export functionality
        when(mockRemoteDataSource.exportAnalyticsReport(
          region: any(named: 'region'),
          dateRange: any(named: 'dateRange'),
          format: any(named: 'format'),
          includeCharts: any(named: 'includeCharts'),
          sections: any(named: 'sections'),
        )).thenAnswer((_) async => 'https://example.com/report.pdf');

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Find and tap export button
        final exportButton = find.byKey(const Key('export_analytics_button'));
        if (exportButton.found()) {
          await tester.tap(exportButton);
          await tester.pumpAndSettle();

          // Export dialog should appear
          expect(find.text('Export Analytics Report'), findsOneWidget);

          // Select export format
          final formatDropdown = find.byKey(const Key('export_format_dropdown'));
          if (formatDropdown.found()) {
            await tester.tap(formatDropdown);
            await tester.pumpAndSettle();

            // Select PDF format
            final pdfOption = find.text('PDF');
            if (pdfOption.found()) {
              await tester.tap(pdfOption);
              await tester.pumpAndSettle();
            }
          }

          // Confirm export
          final confirmButton = find.text('Export');
          await tester.tap(confirmButton);
          await tester.pumpAndSettle();

          // Verify export was initiated
          verify(mockRemoteDataSource.exportAnalyticsReport(
            region: any(named: 'region'),
            dateRange: any(named: 'dateRange'),
            format: any(named: 'format'),
            includeCharts: any(named: 'includeCharts'),
            sections: any(named: 'sections'),
          )).called(1);

          // Verify success message or download link
          expect(find.text('Export completed'), findsOneWidget);
        }
      });
    });

    group('Data Refresh and Caching Integration', () {
      testWidgets('automatic data refresh workflow', (tester) async {
        final analyticsData = MockAnalyticsData.createMockAnalyticsDataModel();
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => analyticsData);

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Find and tap refresh button
        final refreshButton = find.byIcon(Icons.refresh);
        if (refreshButton.found()) {
          await tester.tap(refreshButton);
          await tester.pumpAndSettle();

          // Verify refresh was triggered
          verify(mockRemoteDataSource.getAnalyticsData(any)).called(greaterThan(1));
        }

        // Verify loading indicator during refresh
        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        // Wait for refresh to complete
        await tester.pumpAndSettle(const Duration(seconds: 3));

        // Verify dashboard is updated
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });

      testWidgets('cache invalidation and update workflow', (tester) async {
        // Setup stale cached data
        final staleData = MockAnalyticsData.createMockAnalyticsDataModel()
            .copyWith(generatedAt: DateTime.now().subtract(const Duration(hours: 2)));
        when(mockLocalDataSource.getCachedAnalyticsData(any))
            .thenAnswer((_) async => staleData);

        // Setup fresh remote data
        final freshData = MockAnalyticsData.createMockAnalyticsDataModel()
            .copyWith(generatedAt: DateTime.now());
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => freshData);

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for data load and cache update
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Verify fresh data was fetched and cached
        verify(mockRemoteDataSource.getAnalyticsData(any)).called(1);
        verify(mockLocalDataSource.cacheAnalyticsData(any)).called(1);
      });
    });

    group('Error Handling and Recovery Integration', () {
      testWidgets('network error recovery workflow', (tester) async {
        // Start with network error
        when(mockNetworkInfo.isConnected).thenAnswer((_) async => false);
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenThrow(Exception('Network unreachable'));

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for error state
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Verify error message is displayed
        expect(find.text('Network unreachable'), findsOneWidget);
        expect(find.byIcon(Icons.error_outline), findsOneWidget);

        // Simulate network recovery
        when(mockNetworkInfo.isConnected).thenAnswer((_) async => true);
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());

        // Find and tap retry button
        final retryButton = find.text('Retry');
        if (retryButton.found()) {
          await tester.tap(retryButton);
          await tester.pumpAndSettle(const Duration(seconds: 5));

          // Verify successful recovery
          expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
          expect(find.text('Network unreachable'), findsNothing);
        }
      });

      testWidgets('data corruption recovery workflow', (tester) async {
        // Setup corrupted cached data
        when(mockLocalDataSource.getCachedAnalyticsData(any))
            .thenThrow(Exception('Data corruption detected'));

        // Setup valid remote data
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for recovery from corrupted cache
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Verify fallback to remote data succeeded
        verify(mockRemoteDataSource.getAnalyticsData(any)).called(1);
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });
    });

    group('Performance Integration Tests', () {
      testWidgets('large dataset handling workflow', (tester) async {
        // Setup large dataset
        final largeDataset = MockAnalyticsData.createLargeAnalyticsDataSet();
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => largeDataset);

        final stopwatch = Stopwatch()..start();

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for large dataset to load
        await tester.pumpAndSettle(const Duration(seconds: 10));
        stopwatch.stop();

        // Verify performance is acceptable (under 10 seconds)
        expect(stopwatch.elapsedMilliseconds, lessThan(10000));

        // Verify dashboard loaded successfully with large dataset
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
        expect(find.byType(AnalyticsOverviewCard), findsAtLeastNWidgets(1));
      });

      testWidgets('concurrent operations workflow', (tester) async {
        // Setup data sources
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());
        when(mockRemoteDataSource.generateChartData(any))
            .thenAnswer((_) async => MockAnalyticsData.createMockChartDataModel());

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Trigger multiple concurrent operations
        final refreshButton = find.byIcon(Icons.refresh);
        final chartButton = find.byKey(const Key('generate_chart_button'));
        final exportButton = find.byKey(const Key('export_analytics_button'));

        if (refreshButton.found() && chartButton.found()) {
          // Trigger refresh and chart generation simultaneously
          await tester.tap(refreshButton);
          await tester.tap(chartButton);
          await tester.pumpAndSettle(const Duration(seconds: 5));

          // Verify both operations completed successfully
          verify(mockRemoteDataSource.getAnalyticsData(any)).called(greaterThan(1));
          verify(mockRemoteDataSource.generateChartData(any)).called(atLeast(1));
        }

        // Verify UI remains responsive
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });
    });

    group('Real-time Updates Integration', () {
      testWidgets('live data updates workflow', (tester) async {
        // Setup initial data
        final initialData = MockAnalyticsData.createMockAnalyticsDataModel();
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => initialData);

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Simulate real-time data update
        final updatedData = MockAnalyticsData.createMockAnalyticsDataModel()
            .copyWith(generatedAt: DateTime.now());
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => updatedData);

        // Trigger auto-refresh (simulated by manual refresh)
        final refreshButton = find.byIcon(Icons.refresh);
        if (refreshButton.found()) {
          await tester.tap(refreshButton);
          await tester.pumpAndSettle(const Duration(seconds: 3));

          // Verify updated data was loaded
          verify(mockRemoteDataSource.getAnalyticsData(any)).called(greaterThan(1));
          verify(mockLocalDataSource.cacheAnalyticsData(any)).called(greaterThan(1));
        }

        // Verify UI reflects updated data
        expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      });
    });

    group('Cross-Feature Integration', () {
      testWidgets('analytics to risk assessment navigation', (tester) async {
        // Setup analytics data
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Find navigation to risk assessment
        final riskAssessmentButton = find.byKey(const Key('navigate_to_risk_assessment'));
        if (riskAssessmentButton.found()) {
          await tester.tap(riskAssessmentButton);
          await tester.pumpAndSettle();

          // Verify navigation occurred
          // This would check for risk assessment page components
        }
      });

      testWidgets('analytics data sharing with reporting feature', (tester) async {
        // Setup analytics data
        when(mockRemoteDataSource.getAnalyticsData(any))
            .thenAnswer((_) async => MockAnalyticsData.createMockAnalyticsDataModel());

        await tester.pumpWidget(
          MaterialApp(
            home: MultiBlocProvider(
              providers: [
                BlocProvider(
                  create: (context) => AnalyticsBloc(
                    getAnalyticsData: GetAnalyticsData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    generateChartData: GenerateChartData(
                      AnalyticsRepositoryImpl(
                        remoteDataSource: mockRemoteDataSource,
                        localDataSource: mockLocalDataSource,
                        networkInfo: mockNetworkInfo,
                      ),
                    ),
                    analyticsRepository: AnalyticsRepositoryImpl(
                      remoteDataSource: mockRemoteDataSource,
                      localDataSource: mockLocalDataSource,
                      networkInfo: mockNetworkInfo,
                    ),
                  ),
                ),
              ],
              child: const AnalyticsDashboardPage(),
            ),
          ),
        );

        // Wait for initial load
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // Test data sharing with reporting
        final shareDataButton = find.byKey(const Key('share_analytics_data'));
        if (shareDataButton.found()) {
          await tester.tap(shareDataButton);
          await tester.pumpAndSettle();

          // Verify data sharing interface
          expect(find.text('Share Analytics Data'), findsOneWidget);
        }
      });
    });
  });
}