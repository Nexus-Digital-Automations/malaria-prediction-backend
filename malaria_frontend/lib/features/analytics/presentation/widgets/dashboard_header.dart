/// Dashboard header widget for analytics dashboard navigation and controls
///
/// This widget provides a comprehensive header for the analytics dashboard
/// with user actions, breadcrumb navigation, search functionality, and
/// real-time status indicators integrated with BLoC state management.
///
/// Features:
/// - Breadcrumb navigation with section indicators
/// - User profile and settings access
/// - Real-time data status indicators
/// - Search functionality for dashboard content
/// - Notification center with alerts
/// - Theme and layout controls
/// - Responsive design adaptation
///
/// Usage:
/// ```dart
/// DashboardHeader(
///   onToggleSidebar: () => _toggleSidebar(),
///   onRefresh: () => _refreshData(),
///   sidebarVisible: true,
///   deviceType: DashboardDeviceType.desktop,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/analytics_data.dart';
import '../bloc/analytics_bloc.dart';
import 'dashboard_layout.dart';

/// Header action configuration
class HeaderAction {
  /// Action identifier
  final String id;

  /// Action icon
  final IconData icon;

  /// Action tooltip
  final String tooltip;

  /// Action callback
  final VoidCallback onTap;

  /// Whether action is enabled
  final bool enabled;

  /// Action badge count
  final int? badgeCount;

  /// Action color
  final Color? color;

  const HeaderAction({
    required this.id,
    required this.icon,
    required this.tooltip,
    required this.onTap,
    this.enabled = true,
    this.badgeCount,
    this.color,
  });
}

/// Status indicator configuration
class StatusIndicator {
  /// Status type
  final StatusType type;

  /// Status message
  final String message;

  /// Status color
  final Color color;

  /// Status icon
  final IconData icon;

  /// Last updated timestamp
  final DateTime? lastUpdated;

  const StatusIndicator({
    required this.type,
    required this.message,
    required this.color,
    required this.icon,
    this.lastUpdated,
  });
}

/// Status type enumeration
enum StatusType {
  dataFresh,
  dataStale,
  dataError,
  processing,
  offline,
}

/// Main dashboard header widget
class DashboardHeader extends StatefulWidget {
  /// Callback to toggle sidebar visibility
  final VoidCallback? onToggleSidebar;

  /// Callback for data refresh
  final VoidCallback? onRefresh;

  /// Callback for settings access
  final VoidCallback? onSettings;

  /// Callback for user profile access
  final VoidCallback? onProfile;

  /// Whether sidebar is currently visible
  final bool sidebarVisible;

  /// Current device type for responsive behavior
  final DashboardDeviceType deviceType;

  /// Whether to show search functionality
  final bool showSearch;

  /// Whether to show status indicators
  final bool showStatusIndicators;

  /// Whether to show notification center
  final bool showNotifications;

  /// Custom header actions
  final List<HeaderAction>? customActions;

  /// Whether to show breadcrumbs
  final bool showBreadcrumbs;

  /// Current page title
  final String? pageTitle;

  /// Current page subtitle
  final String? pageSubtitle;

  const DashboardHeader({
    super.key,
    this.onToggleSidebar,
    this.onRefresh,
    this.onSettings,
    this.onProfile,
    this.sidebarVisible = true,
    this.deviceType = DashboardDeviceType.desktop,
    this.showSearch = true,
    this.showStatusIndicators = true,
    this.showNotifications = true,
    this.customActions,
    this.showBreadcrumbs = true,
    this.pageTitle,
    this.pageSubtitle,
  });

  @override
  State<DashboardHeader> createState() => _DashboardHeaderState();
}

class _DashboardHeaderState extends State<DashboardHeader> {
  /// Search controller
  final TextEditingController _searchController = TextEditingController();

  /// Search focus node
  final FocusNode _searchFocusNode = FocusNode();

  /// Whether search is expanded
  bool _searchExpanded = false;

  /// Current status indicators
  final List<StatusIndicator> _statusIndicators = [];

  /// Notification count
  int _notificationCount = 0;

  /// Current user name
  String _currentUser = 'Analytics User';

  /// Last refresh time
  DateTime? _lastRefresh;

  /// Header actions list
  late List<HeaderAction> _headerActions;

  @override
  void initState() {
    super.initState();
    _initializeHeaderActions();
    _updateStatusIndicators();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<AnalyticsBloc, AnalyticsState>(
      listener: _handleBlocStateChanges,
      builder: (context, state) {
        return Container(
          height: DashboardLayoutConfig.headerHeight,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            border: Border(
              bottom: BorderSide(
                color: Theme.of(context).dividerColor,
                width: 1,
              ),
            ),
            boxShadow: [
              BoxShadow(
                color: Theme.of(context).shadowColor.withValues(alpha: 0.1),
                offset: const Offset(0, 2),
                blurRadius: 4,
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                // Left section: Menu toggle and title
                _buildLeftSection(),

                // Center section: Search and breadcrumbs
                Expanded(child: _buildCenterSection(state)),

                // Right section: Actions and user profile
                _buildRightSection(state),
              ],
            ),
          ),
        );
      },
    );
  }

  /// Builds left section with menu toggle and title
  Widget _buildLeftSection() {
    return Row(
      children: [
        // Menu toggle button
        if (widget.deviceType != DashboardDeviceType.desktop)
          IconButton(
            icon: Icon(widget.sidebarVisible ? Icons.menu_open : Icons.menu),
            onPressed: widget.onToggleSidebar,
            tooltip: widget.sidebarVisible ? 'Close Sidebar' : 'Open Sidebar',
          ),

        if (widget.deviceType != DashboardDeviceType.desktop)
          const SizedBox(width: 8),

        // Logo and title
        Row(
          children: [
            Icon(
              Icons.analytics,
              color: Theme.of(context).colorScheme.primary,
              size: 28,
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  widget.pageTitle ?? 'Analytics Dashboard',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (widget.pageSubtitle != null)
                  Text(
                    widget.pageSubtitle!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ],
    );
  }

  /// Builds center section with search and breadcrumbs
  Widget _buildCenterSection(AnalyticsState state) {
    return Row(
      children: [
        const SizedBox(width: 32),

        // Breadcrumbs (desktop only)
        if (widget.showBreadcrumbs && widget.deviceType == DashboardDeviceType.desktop)
          Expanded(child: _buildBreadcrumbs(state)),

        // Search functionality
        if (widget.showSearch) _buildSearchSection(),

        const SizedBox(width: 16),
      ],
    );
  }

  /// Builds right section with actions and user profile
  Widget _buildRightSection(AnalyticsState state) {
    return Row(
      children: [
        // Status indicators
        if (widget.showStatusIndicators) _buildStatusIndicators(state),

        const SizedBox(width: 8),

        // Header actions
        ..._headerActions.map((action) => _buildHeaderAction(action)),

        // Notifications
        if (widget.showNotifications) _buildNotificationButton(),

        // User profile
        _buildUserProfile(),
      ],
    );
  }

  /// Builds breadcrumb navigation
  Widget _buildBreadcrumbs(AnalyticsState state) {
    final breadcrumbs = _getBreadcrumbs(state);

    if (breadcrumbs.isEmpty) return const SizedBox.shrink();

    return Row(
      children: [
        Icon(
          Icons.home,
          size: 16,
          color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
        ),
        const SizedBox(width: 8),
        ...breadcrumbs.expand((breadcrumb) => [
          InkWell(
            onTap: breadcrumb.onTap,
            borderRadius: BorderRadius.circular(4),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Text(
                breadcrumb.label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: breadcrumb.isCurrent
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                  fontWeight: breadcrumb.isCurrent
                      ? FontWeight.bold
                      : FontWeight.normal,
                ),
              ),
            ),
          ),
          if (breadcrumb != breadcrumbs.last)
            Icon(
              Icons.chevron_right,
              size: 16,
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
        ]).toList(),
      ],
    );
  }

  /// Builds search section
  Widget _buildSearchSection() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      width: _searchExpanded ? 300 : 40,
      height: 36,
      child: _searchExpanded
          ? TextField(
              controller: _searchController,
              focusNode: _searchFocusNode,
              decoration: InputDecoration(
                hintText: 'Search dashboard...',
                prefixIcon: const Icon(Icons.search, size: 20),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: _collapseSearch,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                isDense: true,
              ),
              onChanged: _handleSearchChange,
              onSubmitted: _handleSearchSubmit,
            )
          : IconButton(
              icon: const Icon(Icons.search),
              onPressed: _expandSearch,
              tooltip: 'Search',
            ),
    );
  }

  /// Builds status indicators
  Widget _buildStatusIndicators(AnalyticsState state) {
    _updateStatusIndicators(state);

    if (_statusIndicators.isEmpty) return const SizedBox.shrink();

    return Row(
      children: _statusIndicators.map((indicator) => _buildStatusIndicator(indicator)).toList(),
    );
  }

  /// Builds individual status indicator
  Widget _buildStatusIndicator(StatusIndicator indicator) {
    return Tooltip(
      message: indicator.message,
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: indicator.color.withValues(alpha: 0.1),
          border: Border.all(color: indicator.color.withValues(alpha: 0.3)),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(indicator.icon, size: 12, color: indicator.color),
            const SizedBox(width: 4),
            Text(
              _getStatusDisplayText(indicator),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: indicator.color,
                fontSize: 10,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds header action button
  Widget _buildHeaderAction(HeaderAction action) {
    return Stack(
      children: [
        IconButton(
          icon: Icon(action.icon, color: action.color),
          onPressed: action.enabled ? action.onTap : null,
          tooltip: action.tooltip,
        ),
        if (action.badgeCount != null && action.badgeCount! > 0)
          Positioned(
            right: 8,
            top: 8,
            child: Container(
              padding: const EdgeInsets.all(2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.error,
                borderRadius: BorderRadius.circular(6),
              ),
              constraints: const BoxConstraints(
                minWidth: 12,
                minHeight: 12,
              ),
              child: Text(
                action.badgeCount.toString(),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onError,
                  fontSize: 9,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
      ],
    );
  }

  /// Builds notification button
  Widget _buildNotificationButton() {
    return Stack(
      children: [
        IconButton(
          icon: const Icon(Icons.notifications_outlined),
          onPressed: _showNotifications,
          tooltip: 'Notifications',
        ),
        if (_notificationCount > 0)
          Positioned(
            right: 8,
            top: 8,
            child: Container(
              padding: const EdgeInsets.all(2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.error,
                borderRadius: BorderRadius.circular(6),
              ),
              constraints: const BoxConstraints(
                minWidth: 12,
                minHeight: 12,
              ),
              child: Text(
                _notificationCount.toString(),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onError,
                  fontSize: 9,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
      ],
    );
  }

  /// Builds user profile section
  Widget _buildUserProfile() {
    return PopupMenuButton<String>(
      onSelected: _handleUserMenuSelection,
      itemBuilder: (context) => [
        PopupMenuItem(
          value: 'profile',
          child: ListTile(
            leading: const Icon(Icons.person),
            title: const Text('Profile'),
            dense: true,
          ),
        ),
        PopupMenuItem(
          value: 'settings',
          child: ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('Settings'),
            dense: true,
          ),
        ),
        const PopupMenuDivider(),
        PopupMenuItem(
          value: 'logout',
          child: ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Logout'),
            dense: true,
          ),
        ),
      ],
      child: Row(
        children: [
          CircleAvatar(
            radius: 16,
            backgroundColor: Theme.of(context).colorScheme.primary,
            child: Text(
              _currentUser.substring(0, 1).toUpperCase(),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 8),
          if (widget.deviceType == DashboardDeviceType.desktop)
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  _currentUser,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
                ),
                if (_lastRefresh != null)
                  Text(
                    'Last: ${DateFormat('HH:mm').format(_lastRefresh!)}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                      fontSize: 10,
                    ),
                  ),
              ],
            ),
          const Icon(Icons.arrow_drop_down),
        ],
      ),
    );
  }

  /// Initializes header actions
  void _initializeHeaderActions() {
    _headerActions = [
      HeaderAction(
        id: 'refresh',
        icon: Icons.refresh,
        tooltip: 'Refresh Data',
        onTap: widget.onRefresh ?? () {},
      ),
    ];

    // Add custom actions
    if (widget.customActions != null) {
      _headerActions.addAll(widget.customActions!);
    }
  }

  /// Updates status indicators based on state
  void _updateStatusIndicators([AnalyticsState? state]) {
    _statusIndicators.clear();

    if (state is AnalyticsLoaded) {
      _statusIndicators.add(StatusIndicator(
        type: StatusType.dataFresh,
        message: 'Data is up to date',
        color: Colors.green,
        icon: Icons.check_circle,
        lastUpdated: state.lastRefresh,
      ));
    } else if (state is AnalyticsError) {
      _statusIndicators.add(StatusIndicator(
        type: StatusType.dataError,
        message: 'Data error: ${state.message}',
        color: Colors.red,
        icon: Icons.error,
      ));
    } else if (state is AnalyticsLoading) {
      _statusIndicators.add(StatusIndicator(
        type: StatusType.processing,
        message: 'Loading analytics data...',
        color: Colors.orange,
        icon: Icons.sync,
      ));
    }
  }

  /// Gets breadcrumbs for current state
  List<NavigationBreadcrumb> _getBreadcrumbs(AnalyticsState state) {
    // Implementation would build breadcrumbs based on current navigation state
    return [
      NavigationBreadcrumb(label: 'Analytics', onTap: () {}),
      NavigationBreadcrumb(label: 'Dashboard', isCurrent: true),
    ];
  }

  /// Gets status display text
  String _getStatusDisplayText(StatusIndicator indicator) {
    switch (indicator.type) {
      case StatusType.dataFresh:
        return 'Fresh';
      case StatusType.dataStale:
        return 'Stale';
      case StatusType.dataError:
        return 'Error';
      case StatusType.processing:
        return 'Loading';
      case StatusType.offline:
        return 'Offline';
    }
  }

  /// Expands search input
  void _expandSearch() {
    setState(() {
      _searchExpanded = true;
    });
    _searchFocusNode.requestFocus();
  }

  /// Collapses search input
  void _collapseSearch() {
    setState(() {
      _searchExpanded = false;
      _searchController.clear();
    });
    _searchFocusNode.unfocus();
  }

  /// Handles search text change
  void _handleSearchChange(String query) {
    // Implementation would filter dashboard content
  }

  /// Handles search submission
  void _handleSearchSubmit(String query) {
    // Implementation would execute search
    _collapseSearch();
  }

  /// Shows notifications panel
  void _showNotifications() {
    // Implementation would show notifications overlay
  }

  /// Handles user menu selection
  void _handleUserMenuSelection(String value) {
    switch (value) {
      case 'profile':
        if (widget.onProfile != null) widget.onProfile!();
        break;
      case 'settings':
        if (widget.onSettings != null) widget.onSettings!();
        break;
      case 'logout':
        _handleLogout();
        break;
    }
  }

  /// Handles user logout
  void _handleLogout() {
    // Implementation would handle user logout
  }

  /// Handles BLoC state changes
  void _handleBlocStateChanges(BuildContext context, AnalyticsState state) {
    if (state is AnalyticsLoaded) {
      setState(() {
        _lastRefresh = state.lastRefresh;
      });
    }
  }
}

/// Navigation breadcrumb item for header breadcrumbs
class NavigationBreadcrumb {
  /// Breadcrumb label
  final String label;

  /// Breadcrumb action when tapped
  final VoidCallback? onTap;

  /// Whether this is the current breadcrumb
  final bool isCurrent;

  const NavigationBreadcrumb({
    required this.label,
    this.onTap,
    this.isCurrent = false,
  });
}