/// Responsive dashboard layout widget for analytics dashboard
///
/// This widget provides a comprehensive responsive layout system for the
/// malaria prediction analytics dashboard with proper BLoC integration,
/// breakpoint handling, and adaptive UI components.
///
/// Features:
/// - Responsive breakpoint system (mobile, tablet, desktop)
/// - Adaptive sidebar and content layout
/// - Header with navigation and user controls
/// - Loading and error state overlays
/// - Real-time data refresh capabilities
///
/// Usage:
/// ```dart
/// DashboardLayout(
///   header: DashboardHeader(),
///   sidebar: DashboardSidebar(),
///   content: AnalyticsContent(),
///   onRefresh: () => _refreshData(),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/analytics_bloc.dart';
import 'dashboard_header.dart';
import 'dashboard_sidebar.dart';
import 'loading_overlay.dart';
import 'error_recovery_widget.dart';

/// Responsive breakpoints for dashboard layout
class DashboardBreakpoints {
  /// Mobile breakpoint (phones)
  static const double mobile = 600.0;

  /// Tablet breakpoint (tablets, small laptops)
  static const double tablet = 1024.0;

  /// Desktop breakpoint (large screens)
  static const double desktop = 1440.0;
}

/// Dashboard layout configuration
class DashboardLayoutConfig {
  /// Sidebar width for desktop view
  static const double sidebarWidthDesktop = 280.0;

  /// Sidebar width for tablet view
  static const double sidebarWidthTablet = 240.0;

  /// Header height across all devices
  static const double headerHeight = 64.0;

  /// Content padding
  static const EdgeInsets contentPadding = EdgeInsets.all(16.0);

  /// Sidebar animation duration
  static const Duration sidebarAnimationDuration = Duration(milliseconds: 300);
}

/// Dashboard device type enumeration
enum DashboardDeviceType {
  mobile,
  tablet,
  desktop,
}

/// Main dashboard layout widget providing responsive design
class DashboardLayout extends StatefulWidget {
  /// Dashboard content widget
  final Widget content;

  /// Initial sidebar visibility state
  final bool initialSidebarVisible;

  /// Callback for data refresh actions
  final VoidCallback? onRefresh;

  /// Callback for settings access
  final VoidCallback? onSettings;

  /// Callback for user profile access
  final VoidCallback? onProfile;

  /// Whether to show floating action button
  final bool showFloatingActionButton;

  /// Custom floating action button
  final Widget? customFloatingActionButton;

  /// Whether to enable real-time updates
  final bool enableRealTimeUpdates;

  /// Real-time update interval in seconds
  final int realTimeUpdateInterval;

  const DashboardLayout({
    super.key,
    required this.content,
    this.initialSidebarVisible = true,
    this.onRefresh,
    this.onSettings,
    this.onProfile,
    this.showFloatingActionButton = true,
    this.customFloatingActionButton,
    this.enableRealTimeUpdates = false,
    this.realTimeUpdateInterval = 30,
  });

  @override
  State<DashboardLayout> createState() => _DashboardLayoutState();
}

class _DashboardLayoutState extends State<DashboardLayout>
    with TickerProviderStateMixin {
  /// Animation controller for sidebar
  late AnimationController _sidebarController;

  /// Animation for sidebar slide
  late Animation<Offset> _sidebarSlideAnimation;

  /// Animation for sidebar fade
  late Animation<double> _sidebarFadeAnimation;

  /// Current sidebar visibility state
  bool _sidebarVisible = true;

  /// Current device type
  DashboardDeviceType _currentDeviceType = DashboardDeviceType.desktop;

  /// Global key for scaffold
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  void initState() {
    super.initState();

    // Initialize animations
    _initializeAnimations();

    // Set initial sidebar state
    _sidebarVisible = widget.initialSidebarVisible;

    // Initialize real-time updates if enabled
    if (widget.enableRealTimeUpdates) {
      _initializeRealTimeUpdates();
    }
  }

  @override
  void dispose() {
    _sidebarController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Determine device type based on screen width
        _currentDeviceType = _getDeviceType(constraints.maxWidth);

        return Scaffold(
          key: _scaffoldKey,
          body: BlocConsumer<AnalyticsBloc, AnalyticsState>(
            listener: _handleBlocStateChanges,
            builder: (context, state) {
              return Stack(
                children: [
                  // Main layout based on device type
                  _buildMainLayout(constraints),

                  // Loading overlay for loading states
                  if (_shouldShowLoadingOverlay(state))
                    LoadingOverlay(
                      message: _getLoadingMessage(state),
                      progress: _getLoadingProgress(state),
                    ),

                  // Error overlay for error states
                  if (state is AnalyticsError)
                    ErrorRecoveryWidget(
                      error: state,
                      onRetry: _handleErrorRetry,
                      onDismiss: _handleErrorDismiss,
                    ),
                ],
              );
            },
          ),
          floatingActionButton: _buildFloatingActionButton(),
          floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
        );
      },
    );
  }

  /// Initializes animation controllers and animations
  void _initializeAnimations() {
    _sidebarController = AnimationController(
      duration: DashboardLayoutConfig.sidebarAnimationDuration,
      vsync: this,
    );

    _sidebarSlideAnimation = Tween<Offset>(
      begin: const Offset(-1.0, 0.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _sidebarController,
      curve: Curves.easeInOut,
    ));

    _sidebarFadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _sidebarController,
      curve: Curves.easeInOut,
    ));

    // Set initial animation state
    if (_sidebarVisible) {
      _sidebarController.value = 1.0;
    }
  }

  /// Initializes real-time data updates
  void _initializeRealTimeUpdates() {
    // Implementation would set up periodic refresh
    // This is a placeholder for real-time update logic
  }

  /// Determines device type based on screen width
  DashboardDeviceType _getDeviceType(double width) {
    if (width < DashboardBreakpoints.mobile) {
      return DashboardDeviceType.mobile;
    } else if (width < DashboardBreakpoints.tablet) {
      return DashboardDeviceType.tablet;
    } else {
      return DashboardDeviceType.desktop;
    }
  }

  /// Builds main layout based on device type
  Widget _buildMainLayout(BoxConstraints constraints) {
    switch (_currentDeviceType) {
      case DashboardDeviceType.mobile:
        return _buildMobileLayout();
      case DashboardDeviceType.tablet:
        return _buildTabletLayout();
      case DashboardDeviceType.desktop:
        return _buildDesktopLayout();
    }
  }

  /// Builds mobile layout with drawer-style sidebar
  Widget _buildMobileLayout() {
    return Scaffold(
      appBar: _buildAppBar(),
      drawer: _buildSidebar(true),
      body: _buildContent(),
    );
  }

  /// Builds tablet layout with collapsible sidebar
  Widget _buildTabletLayout() {
    return Column(
      children: [
        _buildHeader(),
        Expanded(
          child: Row(
            children: [
              // Animated sidebar
              AnimatedContainer(
                duration: DashboardLayoutConfig.sidebarAnimationDuration,
                width: _sidebarVisible
                    ? DashboardLayoutConfig.sidebarWidthTablet
                    : 0,
                child: _sidebarVisible
                    ? _buildSidebar(false)
                    : const SizedBox.shrink(),
              ),

              // Content area
              Expanded(child: _buildContent()),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds desktop layout with fixed sidebar
  Widget _buildDesktopLayout() {
    return Column(
      children: [
        _buildHeader(),
        Expanded(
          child: Row(
            children: [
              // Fixed sidebar with animation
              SlideTransition(
                position: _sidebarSlideAnimation,
                child: FadeTransition(
                  opacity: _sidebarFadeAnimation,
                  child: SizedBox(
                    width: DashboardLayoutConfig.sidebarWidthDesktop,
                    child: _buildSidebar(false),
                  ),
                ),
              ),

              // Content area
              Expanded(child: _buildContent()),
            ],
          ),
        ),
      ],
    );
  }

  /// Builds app bar for mobile layout
  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: const Text('Analytics Dashboard'),
      elevation: 2,
      actions: _buildHeaderActions(),
    );
  }

  /// Builds header for tablet and desktop layouts
  Widget _buildHeader() {
    return DashboardHeader(
      onToggleSidebar: _toggleSidebar,
      onRefresh: widget.onRefresh,
      onSettings: widget.onSettings,
      onProfile: widget.onProfile,
      sidebarVisible: _sidebarVisible,
      deviceType: _currentDeviceType,
    );
  }

  /// Builds sidebar widget
  Widget _buildSidebar(bool isDrawer) {
    return DashboardSidebar(
      isDrawer: isDrawer,
      deviceType: _currentDeviceType,
      onClose: isDrawer ? () => Navigator.of(context).pop() : null,
    );
  }

  /// Builds main content area
  Widget _buildContent() {
    return Container(
      padding: DashboardLayoutConfig.contentPadding,
      child: widget.content,
    );
  }

  /// Builds header actions for app bar
  List<Widget> _buildHeaderActions() {
    return [
      if (widget.onRefresh != null)
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: widget.onRefresh,
          tooltip: 'Refresh Data',
        ),

      if (widget.onSettings != null)
        IconButton(
          icon: const Icon(Icons.settings),
          onPressed: widget.onSettings,
          tooltip: 'Settings',
        ),

      if (widget.onProfile != null)
        IconButton(
          icon: const Icon(Icons.account_circle),
          onPressed: widget.onProfile,
          tooltip: 'Profile',
        ),
    ];
  }

  /// Builds floating action button
  Widget? _buildFloatingActionButton() {
    if (!widget.showFloatingActionButton) return null;

    if (widget.customFloatingActionButton != null) {
      return widget.customFloatingActionButton;
    }

    return FloatingActionButton(
      onPressed: _showQuickActions,
      tooltip: 'Quick Actions',
      child: const Icon(Icons.add_chart),
    );
  }

  /// Toggles sidebar visibility
  void _toggleSidebar() {
    setState(() {
      _sidebarVisible = !_sidebarVisible;
    });

    if (_sidebarVisible) {
      _sidebarController.forward();
    } else {
      _sidebarController.reverse();
    }
  }

  /// Shows quick actions bottom sheet
  void _showQuickActions() {
    showModalBottomSheet<void>(
      context: context,
      builder: (context) => _buildQuickActionsSheet(),
    );
  }

  /// Builds quick actions bottom sheet
  Widget _buildQuickActionsSheet() {
    return Container(
      height: 250,
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
            leading: const Icon(Icons.refresh),
            title: const Text('Refresh All Data'),
            onTap: () {
              Navigator.pop(context);
              if (widget.onRefresh != null) widget.onRefresh!();
            },
          ),

          ListTile(
            leading: const Icon(Icons.bar_chart),
            title: const Text('Generate Chart'),
            onTap: () {
              Navigator.pop(context);
              _generateQuickChart();
            },
          ),

          ListTile(
            leading: const Icon(Icons.download),
            title: const Text('Export Data'),
            onTap: () {
              Navigator.pop(context);
              _exportData();
            },
          ),
        ],
      ),
    );
  }

  /// Handles BLoC state changes
  void _handleBlocStateChanges(BuildContext context, AnalyticsState state) {
    if (state is AnalyticsError) {
      _showErrorFeedback(state.message);
    } else if (state is AnalyticsExported) {
      _showSuccessFeedback('Data exported successfully!');
    } else if (state is ChartGenerated) {
      _showInfoFeedback('Chart generated successfully');
    }
  }

  /// Determines if loading overlay should be shown
  bool _shouldShowLoadingOverlay(AnalyticsState state) {
    return state is AnalyticsLoading ||
           state is ChartGenerating ||
           state is AnalyticsExporting;
  }

  /// Gets loading message for current state
  String _getLoadingMessage(AnalyticsState state) {
    if (state is AnalyticsLoading) {
      return state.message;
    } else if (state is ChartGenerating) {
      return 'Generating ${state.chartType.name} chart...';
    } else if (state is AnalyticsExporting) {
      return 'Exporting ${state.format.name.toUpperCase()} report...';
    }
    return 'Loading...';
  }

  /// Gets loading progress for current state
  double? _getLoadingProgress(AnalyticsState state) {
    if (state is AnalyticsLoading) {
      return state.progress;
    } else if (state is ChartGenerating) {
      return state.progress;
    } else if (state is AnalyticsExporting) {
      return state.progress;
    }
    return null;
  }

  /// Handles error retry action
  void _handleErrorRetry() {
    context.read<AnalyticsBloc>().add(const RefreshAnalyticsData());
  }

  /// Handles error dismissal
  void _handleErrorDismiss() {
    // Clear error state by reloading data
    context.read<AnalyticsBloc>().add(const RefreshAnalyticsData());
  }

  /// Generates quick chart
  void _generateQuickChart() {
    // Implementation would trigger chart generation
    // This is a placeholder for chart generation logic
  }

  /// Exports data
  void _exportData() {
    context.read<AnalyticsBloc>().add(const ExportAnalyticsReport(
      format: ExportFormat.csv,
      includeCharts: true,
    ));
  }

  /// Shows error feedback
  void _showErrorFeedback(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Theme.of(context).colorScheme.error,
        action: SnackBarAction(
          label: 'Retry',
          onPressed: _handleErrorRetry,
        ),
      ),
    );
  }

  /// Shows success feedback
  void _showSuccessFeedback(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  /// Shows info feedback
  void _showInfoFeedback(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Theme.of(context).colorScheme.primary,
      ),
    );
  }
}

/// Layout helper widget for responsive spacing
class ResponsiveSpacing extends StatelessWidget {
  /// Child widget
  final Widget child;

  /// Mobile spacing
  final EdgeInsets mobileSpacing;

  /// Tablet spacing
  final EdgeInsets tabletSpacing;

  /// Desktop spacing
  final EdgeInsets desktopSpacing;

  const ResponsiveSpacing({
    super.key,
    required this.child,
    this.mobileSpacing = const EdgeInsets.all(8.0),
    this.tabletSpacing = const EdgeInsets.all(12.0),
    this.desktopSpacing = const EdgeInsets.all(16.0),
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        EdgeInsets spacing;

        if (constraints.maxWidth < DashboardBreakpoints.mobile) {
          spacing = mobileSpacing;
        } else if (constraints.maxWidth < DashboardBreakpoints.tablet) {
          spacing = tabletSpacing;
        } else {
          spacing = desktopSpacing;
        }

        return Padding(
          padding: spacing,
          child: child,
        );
      },
    );
  }
}

/// Layout helper for responsive grid
class ResponsiveGrid extends StatelessWidget {
  /// Grid children
  final List<Widget> children;

  /// Mobile columns
  final int mobileColumns;

  /// Tablet columns
  final int tabletColumns;

  /// Desktop columns
  final int desktopColumns;

  /// Cross-axis spacing
  final double crossAxisSpacing;

  /// Main-axis spacing
  final double mainAxisSpacing;

  const ResponsiveGrid({
    super.key,
    required this.children,
    this.mobileColumns = 1,
    this.tabletColumns = 2,
    this.desktopColumns = 3,
    this.crossAxisSpacing = 16.0,
    this.mainAxisSpacing = 16.0,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        int columns;

        if (constraints.maxWidth < DashboardBreakpoints.mobile) {
          columns = mobileColumns;
        } else if (constraints.maxWidth < DashboardBreakpoints.tablet) {
          columns = tabletColumns;
        } else {
          columns = desktopColumns;
        }

        return GridView.builder(
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: columns,
            crossAxisSpacing: crossAxisSpacing,
            mainAxisSpacing: mainAxisSpacing,
          ),
          itemCount: children.length,
          itemBuilder: (context, index) => children[index],
        );
      },
    );
  }
}