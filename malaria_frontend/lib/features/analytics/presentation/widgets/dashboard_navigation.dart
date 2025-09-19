/// Dashboard navigation widget for analytics dashboard section management
///
/// This widget provides comprehensive navigation capabilities for the analytics
/// dashboard with tab management, section switching, breadcrumb navigation,
/// and state preservation across different dashboard sections.
///
/// Features:
/// - Tab-based navigation with dynamic content
/// - Breadcrumb navigation for deep sections
/// - Section state preservation
/// - Keyboard navigation support
/// - Accessibility features
/// - Animation transitions between sections
///
/// Usage:
/// ```dart
/// DashboardNavigation(
///   sections: [
///     DashboardSection(id: 'overview', title: 'Overview', icon: Icons.dashboard),
///     DashboardSection(id: 'predictions', title: 'Predictions', icon: Icons.analytics),
///   ],
///   onSectionChanged: (section) => _handleSectionChange(section),
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../bloc/analytics_bloc.dart';
import 'dashboard_layout.dart';

/// Dashboard section configuration
class DashboardSection {
  /// Unique section identifier
  final String id;

  /// Section display title
  final String title;

  /// Section icon
  final IconData icon;

  /// Section description for tooltip
  final String? description;

  /// Whether section is enabled
  final bool enabled;

  /// Section badge count (for notifications)
  final int? badgeCount;

  /// Section color theme
  final Color? color;

  /// Whether section requires authentication
  final bool requiresAuth;

  /// Sub-sections within this section
  final List<DashboardSubSection>? subSections;

  const DashboardSection({
    required this.id,
    required this.title,
    required this.icon,
    this.description,
    this.enabled = true,
    this.badgeCount,
    this.color,
    this.requiresAuth = false,
    this.subSections,
  });
}

/// Dashboard sub-section configuration
class DashboardSubSection {
  /// Unique sub-section identifier
  final String id;

  /// Sub-section display title
  final String title;

  /// Sub-section icon
  final IconData? icon;

  /// Whether sub-section is enabled
  final bool enabled;

  /// Sub-section route
  final String? route;

  const DashboardSubSection({
    required this.id,
    required this.title,
    this.icon,
    this.enabled = true,
    this.route,
  });
}

/// Navigation breadcrumb item
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

/// Main dashboard navigation widget
class DashboardNavigation extends StatefulWidget {
  /// Available dashboard sections
  final List<DashboardSection> sections;

  /// Currently selected section ID
  final String? selectedSectionId;

  /// Currently selected sub-section ID
  final String? selectedSubSectionId;

  /// Callback when section changes
  final void Function(DashboardSection section)? onSectionChanged;

  /// Callback when sub-section changes
  final void Function(DashboardSubSection subSection)? onSubSectionChanged;

  /// Navigation style (tabs or sidebar)
  final NavigationStyle style;

  /// Whether to show breadcrumbs
  final bool showBreadcrumbs;

  /// Whether to enable keyboard navigation
  final bool enableKeyboardNavigation;

  /// Whether to show section badges
  final bool showBadges;

  /// Animation duration for transitions
  final Duration animationDuration;

  /// Tab controller for external control
  final TabController? tabController;

  const DashboardNavigation({
    super.key,
    required this.sections,
    this.selectedSectionId,
    this.selectedSubSectionId,
    this.onSectionChanged,
    this.onSubSectionChanged,
    this.style = NavigationStyle.tabs,
    this.showBreadcrumbs = true,
    this.enableKeyboardNavigation = true,
    this.showBadges = true,
    this.animationDuration = const Duration(milliseconds: 300),
    this.tabController,
  });

  @override
  State<DashboardNavigation> createState() => _DashboardNavigationState();
}

class _DashboardNavigationState extends State<DashboardNavigation>
    with TickerProviderStateMixin {
  /// Tab controller for managing tab navigation
  late TabController _tabController;

  /// Animation controller for section transitions
  late AnimationController _transitionController;

  /// Page controller for page view navigation
  final PageController _pageController = PageController();

  /// Current section index
  int _currentSectionIndex = 0;

  /// Current sub-section index
  int _currentSubSectionIndex = 0;

  /// Focus node for keyboard navigation
  final FocusNode _focusNode = FocusNode();

  /// Navigation history for breadcrumbs
  final List<NavigationBreadcrumb> _breadcrumbs = [];

  @override
  void initState() {
    super.initState();
    _initializeControllers();
    _initializeSelectedSection();
    _updateBreadcrumbs();
  }

  @override
  void didUpdateWidget(DashboardNavigation oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Update tab controller if sections changed
    if (oldWidget.sections.length != widget.sections.length) {
      _tabController.dispose();
      _initializeControllers();
    }

    // Update selected section if changed
    if (oldWidget.selectedSectionId != widget.selectedSectionId) {
      _initializeSelectedSection();
      _updateBreadcrumbs();
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    _transitionController.dispose();
    _pageController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<AnalyticsBloc, AnalyticsState>(
      listener: _handleBlocStateChanges,
      child: Focus(
        focusNode: _focusNode,
        onKey: widget.enableKeyboardNavigation ? _handleKeyPress : null,
        child: Column(
          children: [
            // Breadcrumb navigation
            if (widget.showBreadcrumbs) _buildBreadcrumbs(),

            // Main navigation based on style
            _buildMainNavigation(),
          ],
        ),
      ),
    );
  }

  /// Initializes tab and animation controllers
  void _initializeControllers() {
    _tabController = widget.tabController ??
        TabController(
          length: widget.sections.length,
          vsync: this,
          initialIndex: _currentSectionIndex,
        );

    _transitionController = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );

    // Listen to tab changes
    _tabController.addListener(_handleTabChange);
  }

  /// Initializes selected section based on provided ID
  void _initializeSelectedSection() {
    if (widget.selectedSectionId != null) {
      final index = widget.sections.indexWhere(
        (section) => section.id == widget.selectedSectionId,
      );
      if (index != -1) {
        _currentSectionIndex = index;
        _tabController.animateTo(index);
      }
    }

    // Initialize sub-section
    if (widget.selectedSubSectionId != null) {
      final currentSection = widget.sections[_currentSectionIndex];
      if (currentSection.subSections != null) {
        final subIndex = currentSection.subSections!.indexWhere(
          (subSection) => subSection.id == widget.selectedSubSectionId,
        );
        if (subIndex != -1) {
          _currentSubSectionIndex = subIndex;
        }
      }
    }
  }

  /// Builds breadcrumb navigation
  Widget _buildBreadcrumbs() {
    if (_breadcrumbs.isEmpty) return const SizedBox.shrink();

    return Container(
      height: 40,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Icon(
            Icons.home,
            size: 16,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _breadcrumbs.length,
              separatorBuilder: (context, index) => Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Icon(
                  Icons.chevron_right,
                  size: 16,
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
              itemBuilder: (context, index) {
                final breadcrumb = _breadcrumbs[index];
                return InkWell(
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
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  /// Builds main navigation based on style
  Widget _buildMainNavigation() {
    switch (widget.style) {
      case NavigationStyle.tabs:
        return _buildTabNavigation();
      case NavigationStyle.sidebar:
        return _buildSidebarNavigation();
      case NavigationStyle.pills:
        return _buildPillNavigation();
    }
  }

  /// Builds tab-style navigation
  Widget _buildTabNavigation() {
    return TabBar(
      controller: _tabController,
      isScrollable: true,
      tabAlignment: TabAlignment.start,
      tabs: widget.sections.map((section) => _buildTab(section)).toList(),
    );
  }

  /// Builds sidebar-style navigation
  Widget _buildSidebarNavigation() {
    return Column(
      children: widget.sections.asMap().entries.map((entry) {
        final index = entry.key;
        final section = entry.value;
        return _buildSidebarItem(section, index);
      }).toList(),
    );
  }

  /// Builds pill-style navigation
  Widget _buildPillNavigation() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: widget.sections.asMap().entries.map((entry) {
          final index = entry.key;
          final section = entry.value;
          return _buildPillItem(section, index);
        }).toList(),
      ),
    );
  }

  /// Builds individual tab
  Widget _buildTab(DashboardSection section) {
    return Tab(
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(section.icon, size: 20),
          const SizedBox(width: 8),
          Text(section.title),
          if (widget.showBadges && section.badgeCount != null && section.badgeCount! > 0)
            Container(
              margin: const EdgeInsets.only(left: 8),
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.error,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                section.badgeCount.toString(),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onError,
                  fontSize: 10,
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// Builds sidebar navigation item
  Widget _buildSidebarItem(DashboardSection section, int index) {
    final isSelected = index == _currentSectionIndex;

    return ListTile(
      leading: Icon(
        section.icon,
        color: isSelected ? Theme.of(context).colorScheme.primary : null,
      ),
      title: Text(
        section.title,
        style: TextStyle(
          color: isSelected ? Theme.of(context).colorScheme.primary : null,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      trailing: widget.showBadges && section.badgeCount != null && section.badgeCount! > 0
          ? Badge(
              label: Text(section.badgeCount.toString()),
              child: const SizedBox.shrink(),
            )
          : null,
      selected: isSelected,
      onTap: section.enabled ? () => _selectSection(index) : null,
      enabled: section.enabled,
    );
  }

  /// Builds pill navigation item
  Widget _buildPillItem(DashboardSection section, int index) {
    final isSelected = index == _currentSectionIndex;

    return Container(
      margin: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(section.icon, size: 16),
            const SizedBox(width: 8),
            Text(section.title),
          ],
        ),
        selected: isSelected,
        onSelected: section.enabled ? (selected) => _selectSection(index) : null,
        avatar: widget.showBadges && section.badgeCount != null && section.badgeCount! > 0
            ? Badge(
                label: Text(section.badgeCount.toString()),
                child: const SizedBox.shrink(),
              )
            : null,
      ),
    );
  }

  /// Handles tab change events
  void _handleTabChange() {
    if (_tabController.indexIsChanging) {
      _selectSection(_tabController.index);
    }
  }

  /// Handles section selection
  void _selectSection(int index) {
    if (index == _currentSectionIndex) return;

    setState(() {
      _currentSectionIndex = index;
      _currentSubSectionIndex = 0;
    });

    // Trigger transition animation
    _transitionController.forward().then((_) {
      _transitionController.reset();
    });

    // Update breadcrumbs
    _updateBreadcrumbs();

    // Notify parent
    if (widget.onSectionChanged != null) {
      widget.onSectionChanged!(widget.sections[index]);
    }
  }

  /// Handles sub-section selection
  void _selectSubSection(int subIndex) {
    if (subIndex == _currentSubSectionIndex) return;

    setState(() {
      _currentSubSectionIndex = subIndex;
    });

    // Update breadcrumbs
    _updateBreadcrumbs();

    // Notify parent
    final currentSection = widget.sections[_currentSectionIndex];
    if (currentSection.subSections != null &&
        widget.onSubSectionChanged != null) {
      widget.onSubSectionChanged!(currentSection.subSections![subIndex]);
    }
  }

  /// Updates breadcrumb navigation
  void _updateBreadcrumbs() {
    _breadcrumbs.clear();

    // Add dashboard breadcrumb
    _breadcrumbs.add(NavigationBreadcrumb(
      label: 'Dashboard',
      onTap: () => _selectSection(0),
    ));

    // Add current section breadcrumb
    final currentSection = widget.sections[_currentSectionIndex];
    _breadcrumbs.add(NavigationBreadcrumb(
      label: currentSection.title,
      onTap: () => _selectSection(_currentSectionIndex),
      isCurrent: _currentSubSectionIndex == 0,
    ));

    // Add sub-section breadcrumb if applicable
    if (currentSection.subSections != null && _currentSubSectionIndex > 0) {
      final subSection = currentSection.subSections![_currentSubSectionIndex];
      _breadcrumbs.add(NavigationBreadcrumb(
        label: subSection.title,
        isCurrent: true,
      ));
    }
  }

  /// Handles keyboard navigation
  KeyEventResult _handleKeyPress(FocusNode node, RawKeyEvent event) {
    if (event is! RawKeyDownEvent) return KeyEventResult.ignored;

    if (event.logicalKey == LogicalKeyboardKey.arrowLeft) {
      if (_currentSectionIndex > 0) {
        _selectSection(_currentSectionIndex - 1);
        return KeyEventResult.handled;
      }
    } else if (event.logicalKey == LogicalKeyboardKey.arrowRight) {
      if (_currentSectionIndex < widget.sections.length - 1) {
        _selectSection(_currentSectionIndex + 1);
        return KeyEventResult.handled;
      }
    }

    return KeyEventResult.ignored;
  }

  /// Handles BLoC state changes
  void _handleBlocStateChanges(BuildContext context, AnalyticsState state) {
    // Update navigation based on analytics state
    if (state is AnalyticsLoaded) {
      // Could update badges based on loaded data
    } else if (state is AnalyticsError) {
      // Could show error indicators in navigation
    }
  }
}

/// Navigation style enumeration
enum NavigationStyle {
  /// Tab-style navigation
  tabs,

  /// Sidebar-style navigation
  sidebar,

  /// Pill-style navigation
  pills,
}

/// Navigation state preservation mixin
mixin NavigationStateMixin<T extends StatefulWidget> on State<T> {
  /// Preserved navigation state
  Map<String, dynamic> _navigationState = {};

  /// Saves navigation state
  void saveNavigationState(String key, dynamic value) {
    _navigationState[key] = value;
  }

  /// Restores navigation state
  V? restoreNavigationState<V>(String key) {
    return _navigationState[key] as V?;
  }

  /// Clears navigation state
  void clearNavigationState() {
    _navigationState.clear();
  }
}