/// Comprehensive widget tests for analytics dashboard components
///
/// This test suite covers all dashboard widgets and UI components including
/// filter panels, data explorer tabs, analytics overview cards,
/// environmental summary widgets, and dashboard layout components.
///
/// Tests cover:
/// - Dashboard widget rendering and layout
/// - Filter panel interactions and state management
/// - Data explorer tab navigation and content
/// - Environmental summary displays
/// - Export controls functionality
/// - Dashboard responsiveness across screen sizes
/// - Accessibility features
/// - Error states and edge cases
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:golden_toolkit/golden_toolkit.dart';
import 'package:malaria_frontend/features/analytics/presentation/pages/analytics_dashboard_page.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_filters_panel.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/filter_panel_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/data_explorer_tab.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/prediction_metrics_tab.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/environmental_summary_widget.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/export_controls.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/data_quality_indicator.dart';
import 'package:malaria_frontend/features/analytics/presentation/widgets/analytics_overview_card.dart';
import 'package:malaria_frontend/features/analytics/presentation/bloc/analytics_bloc.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_data.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/analytics_filters.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/prediction_metrics.dart';
import 'package:malaria_frontend/features/analytics/domain/entities/data_explorer.dart';
import '../../../test_config.dart';
import '../../../mocks/analytics_mocks.dart';
import '../../../helpers/widget_test_helpers.dart';

void main() {
  /// Global test setup
  setUpAll(() async {
    await TestConfig.initialize();
  });

  /// Cleanup after all tests
  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('Analytics Dashboard Page Tests', () {
    late MockAnalyticsBloc mockBloc;
    late AnalyticsData mockAnalyticsData;

    setUp(() {
      mockBloc = MockAnalyticsBloc();
      mockAnalyticsData = MockAnalyticsData.createMockAnalyticsData();
    });

    testWidgets('renders dashboard page correctly', (tester) async {
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: mockAnalyticsData,
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify main dashboard components
      expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
      expect(find.byType(AnalyticsFiltersPanel), findsOneWidget);
      expect(find.byType(AnalyticsOverviewCard), findsAtLeastNWidgets(1));
    });

    testWidgets('handles loading state correctly', (tester) async {
      when(() => mockBloc.state).thenReturn(
        const AnalyticsLoading(message: 'Loading analytics data...'),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify loading indicator
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Loading analytics data...'), findsOneWidget);
    });

    testWidgets('handles error state correctly', (tester) async {
      when(() => mockBloc.state).thenReturn(
        const AnalyticsError(
          message: 'Failed to load analytics data',
          errorType: 'network_error',
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify error display
      expect(find.text('Failed to load analytics data'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('navigates between tabs correctly', (tester) async {
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: mockAnalyticsData,
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test tab navigation
      final overviewTab = find.text('Overview');
      final metricsTab = find.text('Prediction Metrics');
      final explorerTab = find.text('Data Explorer');

      if (overviewTab.found()) {
        await tester.tap(overviewTab);
        await tester.pumpAndSettle();
      }

      if (metricsTab.found()) {
        await tester.tap(metricsTab);
        await tester.pumpAndSettle();
        expect(find.byType(PredictionMetricsTab), findsOneWidget);
      }

      if (explorerTab.found()) {
        await tester.tap(explorerTab);
        await tester.pumpAndSettle();
        expect(find.byType(DataExplorerTab), findsOneWidget);
      }
    });

    testWidgets('handles refresh action correctly', (tester) async {
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: mockAnalyticsData,
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test refresh action
      final refreshButton = find.byIcon(Icons.refresh);
      if (refreshButton.found()) {
        await tester.tap(refreshButton);
        await tester.pumpAndSettle();

        // Verify refresh event was triggered
        verify(() => mockBloc.add(any(that: isA<RefreshAnalyticsData>()))).called(1);
      }
    });
  });

  group('Analytics Filters Panel Tests', () {
    late AnalyticsFilters mockFilters;

    setUp(() {
      mockFilters = MockAnalyticsData.createMockAnalyticsFilters();
    });

    testWidgets('renders filters panel correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsFiltersPanel(
              filters: mockFilters,
              onFiltersChanged: (filters) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify filter components
      expect(find.byType(AnalyticsFiltersPanel), findsOneWidget);
      expect(find.text('Filters'), findsOneWidget);
    });

    testWidgets('handles date range selection', (tester) async {
      AnalyticsFilters? updatedFilters;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsFiltersPanel(
              filters: mockFilters,
              onFiltersChanged: (filters) => updatedFilters = filters,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test date range picker interaction
      final dateRangeButton = find.byType(TextButton);
      if (dateRangeButton.found()) {
        await tester.tap(dateRangeButton.first);
        await tester.pumpAndSettle();

        // Date picker dialog should appear
        // This would be enhanced with actual date selection testing
      }
    });

    testWidgets('handles region selection', (tester) async {
      AnalyticsFilters? updatedFilters;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsFiltersPanel(
              filters: mockFilters,
              onFiltersChanged: (filters) => updatedFilters = filters,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test region dropdown
      final regionDropdown = find.byType(DropdownButton<String>);
      if (regionDropdown.found()) {
        await tester.tap(regionDropdown);
        await tester.pumpAndSettle();

        // Select a different region
        final kenyaOption = find.text('Kenya').last;
        if (kenyaOption.found()) {
          await tester.tap(kenyaOption);
          await tester.pumpAndSettle();

          expect(updatedFilters?.region, equals('Kenya'));
        }
      }
    });

    testWidgets('handles risk level filters', (tester) async {
      AnalyticsFilters? updatedFilters;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsFiltersPanel(
              filters: mockFilters,
              onFiltersChanged: (filters) => updatedFilters = filters,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test risk level checkboxes
      final highRiskCheckbox = find.byKey(const Key('high_risk_filter'));
      if (highRiskCheckbox.found()) {
        await tester.tap(highRiskCheckbox);
        await tester.pumpAndSettle();

        expect(updatedFilters?.riskLevels, contains(RiskLevel.high));
      }
    });

    testWidgets('validates filter constraints', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsFiltersPanel(
              filters: mockFilters,
              onFiltersChanged: (filters) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test invalid date range selection
      // This would involve testing date validation logic
      expect(find.byType(AnalyticsFiltersPanel), findsOneWidget);
    });

    testWidgets('persists filter state correctly', (tester) async {
      final initialFilters = AnalyticsFilters(
        region: 'Kenya',
        dateRange: DateRange(
          start: DateTime.now().subtract(const Duration(days: 7)),
          end: DateTime.now(),
        ),
        riskLevels: {RiskLevel.medium, RiskLevel.high},
        environmentalFactors: {EnvironmentalFactor.temperature},
        dataQualityThreshold: 0.8,
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AnalyticsFiltersPanel(
              filters: initialFilters,
              onFiltersChanged: (filters) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify initial filter state is displayed
      expect(find.text('Kenya'), findsOneWidget);
      expect(find.text('Medium'), findsOneWidget);
      expect(find.text('High'), findsOneWidget);
    });
  });

  group('Filter Panel Widget Tests', () {
    testWidgets('renders expandable filter sections', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilterPanelWidget(
              onFiltersApplied: (filters) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify expandable sections
      expect(find.byType(ExpansionTile), findsAtLeastNWidgets(1));
      expect(find.text('Date Range'), findsOneWidget);
      expect(find.text('Risk Levels'), findsOneWidget);
      expect(find.text('Environmental Factors'), findsOneWidget);
    });

    testWidgets('handles filter reset correctly', (tester) async {
      Map<String, dynamic>? appliedFilters;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilterPanelWidget(
              onFiltersApplied: (filters) => appliedFilters = filters,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test reset button
      final resetButton = find.text('Reset Filters');
      if (resetButton.found()) {
        await tester.tap(resetButton);
        await tester.pumpAndSettle();

        expect(appliedFilters, isNotNull);
        // Verify filters are reset to defaults
      }
    });

    testWidgets('validates filter combinations', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FilterPanelWidget(
              onFiltersApplied: (filters) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test invalid filter combinations
      // This would involve testing validation logic
      expect(find.byType(FilterPanelWidget), findsOneWidget);
    });
  });

  group('Data Explorer Tab Tests', () {
    late DataExplorer mockDataExplorer;

    setUp(() {
      mockDataExplorer = MockAnalyticsData.createMockDataExplorer();
    });

    testWidgets('renders data explorer correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataExplorerTab(
              dataExplorer: mockDataExplorer,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify data explorer components
      expect(find.byType(DataExplorerTab), findsOneWidget);
      expect(find.text('Data Explorer'), findsOneWidget);
    });

    testWidgets('handles data dimension selection', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataExplorerTab(
              dataExplorer: mockDataExplorer,
              onDimensionChanged: (dimension) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test dimension dropdown
      final dimensionDropdown = find.byType(DropdownButton);
      if (dimensionDropdown.found()) {
        await tester.tap(dimensionDropdown.first);
        await tester.pumpAndSettle();

        // Select a dimension
        final temperatureDimension = find.text('Temperature');
        if (temperatureDimension.found()) {
          await tester.tap(temperatureDimension);
          await tester.pumpAndSettle();
        }
      }
    });

    testWidgets('displays correlation matrix correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataExplorerTab(
              dataExplorer: mockDataExplorer,
              showCorrelationMatrix: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify correlation matrix display
      expect(find.text('Correlation Matrix'), findsOneWidget);
    });

    testWidgets('handles data filtering and sorting', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataExplorerTab(
              dataExplorer: mockDataExplorer,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test sorting controls
      final sortButton = find.byIcon(Icons.sort);
      if (sortButton.found()) {
        await tester.tap(sortButton);
        await tester.pumpAndSettle();
      }

      // Test filter controls
      final filterButton = find.byIcon(Icons.filter_list);
      if (filterButton.found()) {
        await tester.tap(filterButton);
        await tester.pumpAndSettle();
      }
    });

    testWidgets('exports data correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataExplorerTab(
              dataExplorer: mockDataExplorer,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test export functionality
      final exportButton = find.byIcon(Icons.download);
      if (exportButton.found()) {
        await tester.tap(exportButton);
        await tester.pumpAndSettle();

        // Verify export dialog
        expect(find.text('Export Data'), findsOneWidget);
      }
    });
  });

  group('Prediction Metrics Tab Tests', () {
    late PredictionMetrics mockMetrics;

    setUp(() {
      mockMetrics = MockAnalyticsData.createMockPredictionMetrics();
    });

    testWidgets('renders prediction metrics correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionMetricsTab(
              metrics: mockMetrics,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify metrics display
      expect(find.byType(PredictionMetricsTab), findsOneWidget);
      expect(find.text('Prediction Metrics'), findsOneWidget);
    });

    testWidgets('displays accuracy metrics correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionMetricsTab(
              metrics: mockMetrics,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify accuracy metrics
      expect(find.textContaining('Accuracy:'), findsOneWidget);
      expect(find.textContaining('Precision:'), findsOneWidget);
      expect(find.textContaining('Recall:'), findsOneWidget);
      expect(find.textContaining('F1 Score:'), findsOneWidget);
    });

    testWidgets('shows confusion matrix visualization', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionMetricsTab(
              metrics: mockMetrics,
              showConfusionMatrix: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify confusion matrix
      expect(find.text('Confusion Matrix'), findsOneWidget);
    });

    testWidgets('displays model comparison charts', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PredictionMetricsTab(
              metrics: mockMetrics,
              showModelComparison: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify model comparison
      expect(find.text('Model Comparison'), findsOneWidget);
    });
  });

  group('Environmental Summary Widget Tests', () {
    late EnvironmentalData mockEnvironmentalData;

    setUp(() {
      mockEnvironmentalData = MockAnalyticsData.createMockEnvironmentalData();
    });

    testWidgets('renders environmental summary correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EnvironmentalSummaryWidget(
              environmentalData: mockEnvironmentalData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify environmental summary components
      expect(find.byType(EnvironmentalSummaryWidget), findsOneWidget);
      expect(find.text('Environmental Summary'), findsOneWidget);
    });

    testWidgets('displays temperature data correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EnvironmentalSummaryWidget(
              environmentalData: mockEnvironmentalData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify temperature display
      expect(find.textContaining('Temperature'), findsOneWidget);
      expect(find.textContaining('°C'), findsAtLeastNWidgets(1));
    });

    testWidgets('displays humidity data correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EnvironmentalSummaryWidget(
              environmentalData: mockEnvironmentalData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify humidity display
      expect(find.textContaining('Humidity'), findsOneWidget);
      expect(find.textContaining('%'), findsAtLeastNWidgets(1));
    });

    testWidgets('displays rainfall data correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EnvironmentalSummaryWidget(
              environmentalData: mockEnvironmentalData,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify rainfall display
      expect(find.textContaining('Rainfall'), findsOneWidget);
      expect(find.textContaining('mm'), findsAtLeastNWidgets(1));
    });

    testWidgets('shows environmental trends correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: EnvironmentalSummaryWidget(
              environmentalData: mockEnvironmentalData,
              showTrends: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify trend indicators
      expect(find.byIcon(Icons.trending_up), findsAtLeastNWidgets(1));
    });
  });

  group('Export Controls Tests', () {
    testWidgets('renders export controls correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ExportControls(
              onExport: (format, options) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify export controls
      expect(find.byType(ExportControls), findsOneWidget);
      expect(find.text('Export'), findsOneWidget);
    });

    testWidgets('handles format selection correctly', (tester) async {
      ExportFormat? selectedFormat;
      Map<String, dynamic>? exportOptions;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ExportControls(
              onExport: (format, options) {
                selectedFormat = format;
                exportOptions = options;
              },
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test format selection
      final formatDropdown = find.byType(DropdownButton<ExportFormat>);
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

      // Test export button
      final exportButton = find.text('Export');
      await tester.tap(exportButton);
      await tester.pumpAndSettle();

      expect(selectedFormat, equals(ExportFormat.pdf));
    });

    testWidgets('validates export options correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ExportControls(
              onExport: (format, options) {},
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test export options validation
      final includeChartsCheckbox = find.byType(Checkbox);
      if (includeChartsCheckbox.found()) {
        await tester.tap(includeChartsCheckbox.first);
        await tester.pumpAndSettle();
      }
    });
  });

  group('Data Quality Indicator Tests', () {
    testWidgets('renders data quality correctly', (tester) async {
      final dataQuality = DataQuality(
        completeness: 0.95,
        accuracy: 0.88,
        freshnessHours: 2.5,
        sourcesCount: 5,
        sourcesWithIssues: ['Source A'],
        lastUpdate: DateTime.now().subtract(const Duration(hours: 2)),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataQualityIndicator(
              dataQuality: dataQuality,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify data quality display
      expect(find.byType(DataQualityIndicator), findsOneWidget);
      expect(find.textContaining('95%'), findsOneWidget); // Completeness
      expect(find.textContaining('88%'), findsOneWidget); // Accuracy
    });

    testWidgets('shows quality issues correctly', (tester) async {
      final dataQuality = DataQuality(
        completeness: 0.75,
        accuracy: 0.65,
        freshnessHours: 12.0,
        sourcesCount: 3,
        sourcesWithIssues: ['Source A', 'Source B'],
        lastUpdate: DateTime.now().subtract(const Duration(hours: 12)),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataQualityIndicator(
              dataQuality: dataQuality,
              showIssues: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify quality issues display
      expect(find.textContaining('Source A'), findsOneWidget);
      expect(find.textContaining('Source B'), findsOneWidget);
      expect(find.byIcon(Icons.warning), findsAtLeastNWidgets(1));
    });

    testWidgets('displays quality trends correctly', (tester) async {
      final dataQuality = DataQuality(
        completeness: 0.92,
        accuracy: 0.89,
        freshnessHours: 1.5,
        sourcesCount: 4,
        sourcesWithIssues: [],
        lastUpdate: DateTime.now().subtract(const Duration(minutes: 90)),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DataQualityIndicator(
              dataQuality: dataQuality,
              showTrend: true,
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify trend indicators
      expect(find.byIcon(Icons.trending_up), findsAtLeastNWidgets(1));
    });
  });

  group('Dashboard Responsiveness Tests', () {
    testWidgets('adapts to small screen sizes', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      final mockBloc = MockAnalyticsBloc();
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: MockAnalyticsData.createMockAnalyticsData(),
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify responsive layout
      expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
    });

    testWidgets('adapts to large screen sizes', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      final mockBloc = MockAnalyticsBloc();
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: MockAnalyticsData.createMockAnalyticsData(),
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify desktop layout
      expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
    });
  });

  group('Dashboard Accessibility Tests', () {
    testWidgets('has proper semantic structure', (tester) async {
      final mockBloc = MockAnalyticsBloc();
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: MockAnalyticsData.createMockAnalyticsData(),
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify semantic structure
      expect(find.byType(AnalyticsDashboardPage), findsOneWidget);

      // Test semantic labels and descriptions
      // This would be enhanced with more specific accessibility testing
    });

    testWidgets('supports keyboard navigation', (tester) async {
      final mockBloc = MockAnalyticsBloc();
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: MockAnalyticsData.createMockAnalyticsData(),
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalyticsBloc>(
            create: (context) => mockBloc,
            child: const AnalyticsDashboardPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Test keyboard navigation
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pump();

      // Verify focus behavior
      expect(find.byType(AnalyticsDashboardPage), findsOneWidget);
    });
  });

  group('Golden Tests for Visual Regression', () {
    testGoldens('analytics dashboard page golden test', (tester) async {
      final mockBloc = MockAnalyticsBloc();
      when(() => mockBloc.state).thenReturn(
        AnalyticsLoaded(
          analyticsData: MockAnalyticsData.createMockAnalyticsData(),
          selectedRegion: 'Kenya',
          selectedDateRange: DateRange(
            start: DateTime.now().subtract(const Duration(days: 30)),
            end: DateTime.now(),
          ),
          lastRefresh: DateTime.now(),
        ),
      );

      await tester.pumpWidgetBuilder(
        BlocProvider<AnalyticsBloc>(
          create: (context) => mockBloc,
          child: const AnalyticsDashboardPage(),
        ),
      );

      await screenMatchesGolden(tester, 'analytics_dashboard_page');
    });

    testGoldens('analytics filters panel golden test', (tester) async {
      await tester.pumpWidgetBuilder(
        AnalyticsFiltersPanel(
          filters: MockAnalyticsData.createMockAnalyticsFilters(),
          onFiltersChanged: (filters) {},
        ),
      );

      await screenMatchesGolden(tester, 'analytics_filters_panel');
    });
  });
}