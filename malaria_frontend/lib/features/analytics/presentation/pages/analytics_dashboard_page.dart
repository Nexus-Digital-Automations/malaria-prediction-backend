/// Analytics dashboard page for comprehensive malaria prediction analytics
///
/// This page provides a comprehensive analytics dashboard displaying
/// prediction accuracy metrics, environmental trends, risk assessments,
/// and interactive data visualizations using fl_chart components.
///
/// Features:
/// - Real-time analytics data display
/// - Interactive charts and graphs
/// - Filtering and date range selection
/// - Export functionality
/// - Responsive layout for all screen sizes
///
/// Usage:
/// ```dart
/// Navigator.push(
///   context,
///   MaterialPageRoute(
///     builder: (context) => const AnalyticsDashboardPage(),
///   ),
/// );
/// ```

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/widgets/error_widget.dart';
import '../../../../core/widgets/loading_widget.dart';
import '../../domain/entities/analytics_data.dart';
import '../../domain/entities/chart_data.dart';
import '../../domain/repositories/analytics_repository.dart';
import '../bloc/analytics_bloc.dart';
import '../widgets/analytics_overview_card.dart';
import '../widgets/analytics_filters_panel.dart';
import '../widgets/prediction_accuracy_chart.dart';
import '../widgets/environmental_trends_chart.dart';
import '../widgets/risk_distribution_chart.dart';
import '../widgets/data_quality_indicator.dart';
import '../widgets/export_controls.dart';

/// Analytics dashboard page widget
class AnalyticsDashboardPage extends StatefulWidget {
  /// Initial region to display analytics for
  final String? initialRegion;

  /// Initial date range for analytics
  final DateRange? initialDateRange;

  /// Constructor with optional initial parameters
  const AnalyticsDashboardPage({
    super.key,
    this.initialRegion,
    this.initialDateRange,
  });

  @override
  State<AnalyticsDashboardPage> createState() => _AnalyticsDashboardPageState();
}

class _AnalyticsDashboardPageState extends State<AnalyticsDashboardPage>
    with TickerProviderStateMixin {
  /// Tab controller for dashboard sections
  late TabController _tabController;

  /// Scroll controller for dashboard content
  late ScrollController _scrollController;

  /// Current selected region
  String _selectedRegion = 'Kenya';

  /// Current selected date range
  late DateRange _selectedDateRange;

  /// Current applied filters
  AnalyticsFilters _appliedFilters = const AnalyticsFilters();

  /// Whether filters panel is expanded
  bool _filtersExpanded = false;

  @override
  void initState() {
    super.initState();

    // Initialize controllers
    _tabController = TabController(length: 4, vsync: this);
    _scrollController = ScrollController();

    // Set initial values
    _selectedRegion = widget.initialRegion ?? 'Kenya';
    _selectedDateRange = widget.initialDateRange ??
        DateRange(
          start: DateTime.now().subtract(const Duration(days: 30)),
          end: DateTime.now(),
        );

    // Load initial data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadAnalyticsData();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: BlocConsumer<AnalyticsBloc, AnalyticsState>(
        listener: _handleStateChanges,
        builder: (context, state) {
          return Column(
            children: [
              _buildFiltersSection(),
              Expanded(
                child: _buildDashboardContent(state),
              ),
            ],
          );
        },
      ),
      floatingActionButton: _buildFloatingActionButton(),
    );
  }

  /// Builds the app bar with dashboard title and actions
  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Analytics Dashboard'),
      subtitle: Text('${_selectedRegion} • ${_formatDateRange(_selectedDateRange)}'),
      elevation: 2,
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: _refreshData,
          tooltip: 'Refresh Data',
        ),
        IconButton(
          icon: Icon(_filtersExpanded ? Icons.filter_list : Icons.filter_list_off),
          onPressed: _toggleFilters,
          tooltip: 'Toggle Filters',
        ),
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert),
          onSelected: _handleMenuAction,
          itemBuilder: (context) => [
            const PopupMenuItem(
              value: 'export_pdf',
              child: ListTile(
                leading: Icon(Icons.picture_as_pdf),
                title: Text('Export PDF'),
                dense: true,
              ),
            ),
            const PopupMenuItem(
              value: 'export_csv',
              child: ListTile(
                leading: Icon(Icons.table_chart),
                title: Text('Export CSV'),
                dense: true,
              ),
            ),
            const PopupMenuItem(
              value: 'settings',
              child: ListTile(
                leading: Icon(Icons.settings),
                title: Text('Settings'),
                dense: true,
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds the filters section with collapsible panel
  Widget _buildFiltersSection() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      height: _filtersExpanded ? 120 : 0,
      child: _filtersExpanded
          ? AnalyticsFiltersPanel(
              selectedRegion: _selectedRegion,
              selectedDateRange: _selectedDateRange,
              appliedFilters: _appliedFilters,
              onRegionChanged: _onRegionChanged,
              onDateRangeChanged: _onDateRangeChanged,
              onFiltersChanged: _onFiltersChanged,
            )
          : null,
    );
  }

  /// Builds the main dashboard content based on current state
  Widget _buildDashboardContent(AnalyticsState state) {
    if (state is AnalyticsLoading) {
      return _buildLoadingState(state);
    } else if (state is AnalyticsError) {
      return _buildErrorState(state);
    } else if (state is AnalyticsLoaded) {
      return _buildLoadedState(state);
    } else if (state is ChartGenerating) {
      return _buildChartGeneratingState(state);
    } else if (state is ChartGenerated) {
      return _buildLoadedState(state.baseState);
    } else if (state is AnalyticsExporting) {
      return _buildExportingState(state);
    } else if (state is AnalyticsExported) {
      return _buildExportedState(state);
    } else {
      return _buildInitialState();
    }
  }

  /// Builds the loading state UI
  Widget _buildLoadingState(AnalyticsLoading state) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const LoadingWidget(),
          const SizedBox(height: 16),
          Text(
            state.message,
            style: Theme.of(context).textTheme.bodyLarge,
            textAlign: TextAlign.center,
          ),
          if (state.progress != null) ...[
            const SizedBox(height: 16),
            SizedBox(
              width: 200,
              child: LinearProgressIndicator(
                value: state.progress,
                backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
                valueColor: AlwaysStoppedAnimation<Color>(
                  Theme.of(context).colorScheme.primary,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '${(state.progress! * 100).toInt()}% Complete',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ],
      ),
    );
  }

  /// Builds the error state UI
  Widget _buildErrorState(AnalyticsError state) {
    return Center(
      child: CustomErrorWidget(
        message: state.message,
        onRetry: state.isRecoverable ? _retryLastAction : null,
        errorType: state.errorType,
      ),
    );
  }

  /// Builds the loaded state UI with dashboard content
  Widget _buildLoadedState(AnalyticsLoaded state) {
    return Column(
      children: [
        // Overview cards
        Container(
          height: 120,
          padding: const EdgeInsets.all(16),
          child: _buildOverviewCards(state.analyticsData),
        ),
        // Tabs and content
        Expanded(
          child: Column(
            children: [
              _buildTabBar(),
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildOverviewTab(state),
                    _buildPredictionTab(state),
                    _buildEnvironmentalTab(state),
                    _buildReportsTab(state),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds the chart generating state UI
  Widget _buildChartGeneratingState(ChartGenerating state) {
    return Column(
      children: [
        // Show base content
        Expanded(child: _buildLoadedState(state.baseState)),
        // Show chart generation overlay
        Container(
          height: 80,
          color: Theme.of(context).colorScheme.surface.withValues(alpha:0.9),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(),
                const SizedBox(height: 8),
                Text(
                  'Generating ${state.chartType.name} chart...',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Builds the exporting state UI
  Widget _buildExportingState(AnalyticsExporting state) {
    return Column(
      children: [
        Expanded(child: _buildLoadedState(state.baseState)),
        Container(
          height: 80,
          color: Theme.of(context).colorScheme.surface.withValues(alpha:0.9),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(),
                const SizedBox(height: 8),
                Text(
                  'Exporting ${state.format.name.toUpperCase()} report...',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                if (state.progress != null) ...[
                  const SizedBox(height: 8),
                  LinearProgressIndicator(value: state.progress),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Builds the exported state UI with success message
  Widget _buildExportedState(AnalyticsExported state) {
    return Column(
      children: [
        Expanded(child: _buildLoadedState(state.baseState)),
        Container(
          height: 80,
          color: Theme.of(context).colorScheme.primaryContainer,
          child: Center(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.check_circle,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 8),
                Text(
                  'Report exported successfully!',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(width: 16),
                ElevatedButton(
                  onPressed: () => _openReport(state.reportUrl),
                  child: const Text('Open Report'),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Builds the initial state UI
  Widget _buildInitialState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.analytics,
            size: 64,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'Welcome to Analytics Dashboard',
            style: Theme.of(context).textTheme.headlineSmall,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Load analytics data to get started',
            style: Theme.of(context).textTheme.bodyLarge,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _loadAnalyticsData,
            child: const Text('Load Analytics Data'),
          ),
        ],
      ),
    );
  }

  /// Builds overview cards showing key metrics
  Widget _buildOverviewCards(AnalyticsData analyticsData) {
    return Row(
      children: [
        Expanded(
          child: AnalyticsOverviewCard(
            title: 'Prediction Accuracy',
            value: '${(analyticsData.predictionAccuracy.overall * 100).toInt()}%',
            icon: Icons.accuracy,
            color: Theme.of(context).colorScheme.primary,
            trend: _calculateAccuracyTrend(analyticsData.predictionAccuracy),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: AnalyticsOverviewCard(
            title: 'Alert Delivery Rate',
            value: '${(analyticsData.alertStatistics.deliveryRate * 100).toInt()}%',
            icon: Icons.notifications_active,
            color: Theme.of(context).colorScheme.secondary,
            trend: 0.0, // Would calculate from historical data
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: AnalyticsOverviewCard(
            title: 'Data Quality',
            value: '${(analyticsData.dataQuality.completeness * 100).toInt()}%',
            icon: Icons.data_usage,
            color: Theme.of(context).colorScheme.tertiary,
            trend: _calculateDataQualityTrend(analyticsData.dataQuality),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: AnalyticsOverviewCard(
            title: 'Active Regions',
            value: '${analyticsData.riskTrends.length}',
            icon: Icons.map,
            color: Theme.of(context).colorScheme.error,
            trend: 0.0, // Would calculate from historical data
          ),
        ),
      ],
    );
  }

  /// Builds the tab bar for dashboard sections
  Widget _buildTabBar() {
    return TabBar(
      controller: _tabController,
      tabs: const [
        Tab(icon: Icon(Icons.dashboard), text: 'Overview'),
        Tab(icon: Icon(Icons.analytics), text: 'Predictions'),
        Tab(icon: Icon(Icons.eco), text: 'Environment'),
        Tab(icon: Icon(Icons.assessment), text: 'Reports'),
      ],
    );
  }

  /// Builds the overview tab content
  Widget _buildOverviewTab(AnalyticsLoaded state) {
    return SingleChildScrollView(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionHeader('System Performance'),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                flex: 2,
                child: PredictionAccuracyChart(
                  accuracyData: state.analyticsData.predictionAccuracy,
                  height: 300,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: RiskDistributionChart(
                  riskTrends: state.analyticsData.riskTrends,
                  height: 300,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          _buildSectionHeader('Data Quality'),
          const SizedBox(height: 16),
          DataQualityIndicator(
            dataQuality: state.analyticsData.dataQuality,
          ),
        ],
      ),
    );
  }

  /// Builds the predictions tab content
  Widget _buildPredictionTab(AnalyticsLoaded state) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionHeader('Prediction Accuracy Metrics'),
          const SizedBox(height: 16),
          PredictionAccuracyChart(
            accuracyData: state.analyticsData.predictionAccuracy,
            height: 400,
            showDetails: true,
          ),
          const SizedBox(height: 24),
          _buildSectionHeader('Risk Assessment Trends'),
          const SizedBox(height: 16),
          Container(
            height: 300,
            decoration: BoxDecoration(
              border: Border.all(color: Theme.of(context).dividerColor),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Center(
              child: Text('Risk trends chart will be displayed here'),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the environmental tab content
  Widget _buildEnvironmentalTab(AnalyticsLoaded state) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionHeader('Environmental Trends'),
          const SizedBox(height: 16),
          EnvironmentalTrendsChart(
            environmentalTrends: state.analyticsData.environmentalTrends,
            height: 400,
          ),
          const SizedBox(height: 24),
          _buildSectionHeader('Climate Patterns'),
          const SizedBox(height: 16),
          Container(
            height: 300,
            decoration: BoxDecoration(
              border: Border.all(color: Theme.of(context).dividerColor),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Center(
              child: Text('Climate patterns chart will be displayed here'),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds the reports tab content
  Widget _buildReportsTab(AnalyticsLoaded state) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionHeader('Export Reports'),
          const SizedBox(height: 16),
          ExportControls(
            onExport: _exportReport,
            availableFormats: const [
              ExportFormat.pdf,
              ExportFormat.csv,
              ExportFormat.xlsx,
            ],
          ),
          const SizedBox(height: 24),
          _buildSectionHeader('Report History'),
          const SizedBox(height: 16),
          Container(
            height: 300,
            decoration: BoxDecoration(
              border: Border.all(color: Theme.of(context).dividerColor),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Center(
              child: Text('Report history will be displayed here'),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds section header with title
  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
        fontWeight: FontWeight.bold,
      ),
    );
  }

  /// Builds floating action button for quick actions
  Widget? _buildFloatingActionButton() {
    return FloatingActionButton(
      onPressed: _showQuickActions,
      tooltip: 'Quick Actions',
      child: const Icon(Icons.add_chart),
    );
  }

  /// Handles state changes and shows appropriate feedback
  void _handleStateChanges(BuildContext context, AnalyticsState state) {
    if (state is AnalyticsError) {
      _showErrorSnackBar(state.message);
    } else if (state is AnalyticsExported) {
      _showSuccessSnackBar('Report exported successfully!');
    } else if (state is ChartGenerated) {
      _showInfoSnackBar('Chart generated successfully');
    }
  }

  /// Loads analytics data for current selections
  void _loadAnalyticsData() {
    context.read<AnalyticsBloc>().add(LoadAnalyticsData(
          region: _selectedRegion,
          dateRange: _selectedDateRange,
          filters: _appliedFilters,
        ));
  }

  /// Refreshes current analytics data
  void _refreshData() {
    context.read<AnalyticsBloc>().add(const RefreshAnalyticsData());
  }

  /// Toggles filters panel visibility
  void _toggleFilters() {
    setState(() {
      _filtersExpanded = !_filtersExpanded;
    });
  }

  /// Handles region selection change
  void _onRegionChanged(String region) {
    setState(() {
      _selectedRegion = region;
    });
    context.read<AnalyticsBloc>().add(ChangeRegion(region: region));
  }

  /// Handles date range selection change
  void _onDateRangeChanged(DateRange dateRange) {
    setState(() {
      _selectedDateRange = dateRange;
    });
    context.read<AnalyticsBloc>().add(ChangeDateRange(dateRange: dateRange));
  }

  /// Handles filters change
  void _onFiltersChanged(AnalyticsFilters filters) {
    setState(() {
      _appliedFilters = filters;
    });
    context.read<AnalyticsBloc>().add(ApplyFilters(filters: filters));
  }

  /// Handles menu actions
  void _handleMenuAction(String action) {
    switch (action) {
      case 'export_pdf':
        _exportReport(ExportFormat.pdf);
        break;
      case 'export_csv':
        _exportReport(ExportFormat.csv);
        break;
      case 'settings':
        _showSettings();
        break;
    }
  }

  /// Exports analytics report in specified format
  void _exportReport(ExportFormat format) {
    context.read<AnalyticsBloc>().add(ExportAnalyticsReport(
          format: format,
          includeCharts: true,
        ));
  }

  /// Shows quick actions dialog
  void _showQuickActions() {
    showModalBottomSheet<void>(
      context: context,
      builder: (context) => Container(
        height: 200,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Quick Actions',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.bar_chart),
              title: const Text('Generate Bar Chart'),
              onTap: () => _generateChart(ChartType.barChart),
            ),
            ListTile(
              leading: const Icon(Icons.pie_chart),
              title: const Text('Generate Pie Chart'),
              onTap: () => _generateChart(ChartType.pieChart),
            ),
          ],
        ),
      ),
    );
  }

  /// Generates chart for quick actions
  void _generateChart(ChartType chartType) {
    Navigator.pop(context); // Close bottom sheet
    context.read<AnalyticsBloc>().add(GenerateChart(
          chartType: chartType,
          dataType: ChartDataType.riskDistribution,
          region: _selectedRegion,
          dateRange: _selectedDateRange,
        ));
  }

  /// Shows settings dialog
  void _showSettings() {
    // TODO: Implement settings dialog
    _showInfoSnackBar('Settings not yet implemented');
  }

  /// Opens exported report URL
  void _openReport(String reportUrl) {
    // TODO: Implement report opening (launch URL)
    _showInfoSnackBar('Opening report: $reportUrl');
  }

  /// Retries last failed action
  void _retryLastAction() {
    _loadAnalyticsData();
  }

  /// Calculates accuracy trend from prediction data
  double _calculateAccuracyTrend(PredictionAccuracy accuracy) {
    if (accuracy.trend.length < 2) return 0.0;

    final recent = accuracy.trend.last.accuracy;
    final previous = accuracy.trend[accuracy.trend.length - 2].accuracy;
    return recent - previous;
  }

  /// Calculates data quality trend
  double _calculateDataQualityTrend(DataQuality dataQuality) {
    // Would calculate from historical data in real implementation
    return 0.05; // Placeholder positive trend
  }

  /// Formats date range for display
  String _formatDateRange(DateRange dateRange) {
    final formatter = DateFormat('MMM d');
    return '${formatter.format(dateRange.start)} - ${formatter.format(dateRange.end)}';
  }

  /// Shows error snack bar
  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Theme.of(context).colorScheme.error,
        action: SnackBarAction(
          label: 'Retry',
          onPressed: _retryLastAction,
        ),
      ),
    );
  }

  /// Shows success snack bar
  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  /// Shows info snack bar
  void _showInfoSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Theme.of(context).colorScheme.primary,
      ),
    );
  }
}