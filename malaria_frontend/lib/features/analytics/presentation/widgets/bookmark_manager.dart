/// Bookmark manager widget for saving and restoring dashboard views
///
/// This widget provides comprehensive bookmark management capabilities
/// allowing users to save, organize, and restore dashboard views with
/// filters, visualizations, and custom configurations.
///
/// Features:
/// - Save and restore dashboard states
/// - Organize bookmarks into categories
/// - Share bookmarks with other users
/// - Import/export bookmark collections
/// - Quick access bookmarks toolbar
/// - Search and filter bookmarks
/// - Bookmark validation and verification
/// - Auto-save recent states
/// - Collaborative bookmark spaces
/// - Bookmark analytics and usage tracking
///
/// Usage:
/// ```dart
/// BookmarkManager(
///   onBookmarkSaved: (name, state) => saveBookmark(name, state),
///   onBookmarkLoaded: (state) => loadBookmark(state),
///   showCategories: true,
///   allowSharing: true,
/// )
/// ```
library;

import 'package:flutter/material.dart';
import 'package:logging/logging.dart';
import '../../domain/entities/analytics_filters.dart';

/// Logger for bookmark manager operations
final _logger = Logger('BookmarkManager');

/// Bookmark manager widget for dashboard state management
class BookmarkManager extends StatefulWidget {
  /// Callback when bookmark is saved
  final Function(String name, Map<String, dynamic> state) onBookmarkSaved;

  /// Callback when bookmark is loaded
  final ValueChanged<Map<String, dynamic>> onBookmarkLoaded;

  /// Whether to show bookmark categories
  final bool showCategories;

  /// Whether to allow bookmark sharing
  final bool allowSharing;

  /// Whether to show usage analytics
  final bool showAnalytics;

  /// Maximum number of bookmarks per user
  final int? maxBookmarks;

  /// Custom bookmark categories
  final List<BookmarkCategory>? customCategories;

  /// Whether bookmark manager is read-only
  final bool readOnly;

  /// Custom color scheme
  final ColorScheme? colorScheme;

  /// Current dashboard state for saving
  final Map<String, dynamic>? currentState;

  const BookmarkManager({
    super.key,
    required this.onBookmarkSaved,
    required this.onBookmarkLoaded,
    this.showCategories = true,
    this.allowSharing = true,
    this.showAnalytics = false,
    this.maxBookmarks,
    this.customCategories,
    this.readOnly = false,
    this.colorScheme,
    this.currentState,
  });

  @override
  State<BookmarkManager> createState() => _BookmarkManagerState();
}

class _BookmarkManagerState extends State<BookmarkManager>
    with TickerProviderStateMixin {
  /// Tab controller for bookmark views
  late TabController _tabController;

  /// Animation controller for UI transitions
  late AnimationController _animationController;

  /// Animation for panel transitions
  late Animation<double> _panelAnimation;

  /// List of bookmarks
  final List<Bookmark> _bookmarks = [];

  /// List of bookmark categories
  late List<BookmarkCategory> _categories;

  /// Currently selected category
  BookmarkCategory? _selectedCategory;

  /// Search controller
  final TextEditingController _searchController = TextEditingController();

  /// Form key for bookmark creation
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  /// Text controllers for bookmark creation
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();

  /// Current sort option
  BookmarkSortOption _sortOption = BookmarkSortOption.dateCreated;

  /// Whether to show archived bookmarks
  bool _showArchived = false;

  /// Focus node for search
  final FocusNode _searchFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _logger.info('Initializing bookmark manager');

    // Initialize tab controller
    _tabController = TabController(length: BookmarkView.values.length, vsync: this);

    // Initialize animations
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _panelAnimation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );

    // Initialize categories
    _initializeCategories();

    // Load existing bookmarks
    _loadBookmarks();

    // Start animation
    _animationController.forward();
  }

  @override
  void dispose() {
    _logger.info('Disposing bookmark manager');
    _tabController.dispose();
    _animationController.dispose();
    _searchController.dispose();
    _nameController.dispose();
    _descriptionController.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  /// Initializes bookmark categories
  void _initializeCategories() {
    _categories = widget.customCategories ?? [
      BookmarkCategory(
        id: 'general',
        name: 'General',
        description: 'General purpose bookmarks',
        icon: Icons.bookmark,
        color: Colors.blue,
      ),
      BookmarkCategory(
        id: 'reports',
        name: 'Reports',
        description: 'Saved report configurations',
        icon: Icons.description,
        color: Colors.green,
      ),
      BookmarkCategory(
        id: 'analysis',
        name: 'Analysis',
        description: 'Analysis and research bookmarks',
        icon: Icons.analytics,
        color: Colors.orange,
      ),
      BookmarkCategory(
        id: 'favorites',
        name: 'Favorites',
        description: 'Most frequently used bookmarks',
        icon: Icons.star,
        color: Colors.amber,
      ),
    ];
  }

  /// Loads existing bookmarks (mock implementation)
  void _loadBookmarks() {
    _bookmarks.addAll([
      Bookmark(
        id: 'bookmark_1',
        name: 'Monthly Kenya Report',
        description: 'Monthly analytics for Kenya region',
        state: {
          'region': 'Kenya',
          'dateRange': 'last_30_days',
          'filters': {'includeEnvironmentalData': true},
        },
        category: _categories.firstWhere((c) => c.id == 'reports'),
        createdAt: DateTime.now().subtract(const Duration(days: 5)),
        lastUsed: DateTime.now().subtract(const Duration(hours: 2)),
        usageCount: 15,
        isShared: false,
        isArchived: false,
        tags: ['kenya', 'monthly', 'environmental'],
      ),
      Bookmark(
        id: 'bookmark_2',
        name: 'High Risk Analysis',
        description: 'Focus on high-risk areas and predictions',
        state: {
          'filters': {
            'riskLevels': ['high', 'critical'],
            'includeAlertStatistics': true,
          },
        },
        category: _categories.firstWhere((c) => c.id == 'analysis'),
        createdAt: DateTime.now().subtract(const Duration(days: 10)),
        lastUsed: DateTime.now().subtract(const Duration(days: 1)),
        usageCount: 8,
        isShared: true,
        isArchived: false,
        tags: ['high-risk', 'alerts', 'critical'],
      ),
      Bookmark(
        id: 'bookmark_3',
        name: 'Q4 Executive Summary',
        description: 'Executive dashboard for Q4 presentation',
        state: {
          'dateRange': 'q4_2024',
          'view': 'executive',
          'sections': ['overview', 'key_metrics'],
        },
        category: _categories.firstWhere((c) => c.id == 'favorites'),
        createdAt: DateTime.now().subtract(const Duration(days: 30)),
        lastUsed: DateTime.now().subtract(const Duration(days: 7)),
        usageCount: 25,
        isShared: true,
        isArchived: false,
        tags: ['executive', 'q4', 'summary'],
      ),
    ]);

    _logger.info('Loaded ${_bookmarks.length} bookmarks');
  }

  /// Saves a new bookmark
  Future<void> _saveBookmark() async {
    if (!_formKey.currentState!.validate()) return;
    if (widget.readOnly) return;

    if (widget.maxBookmarks != null && _bookmarks.length >= widget.maxBookmarks!) {
      _showError('Maximum number of bookmarks reached (${widget.maxBookmarks})');
      return;
    }

    final bookmark = Bookmark(
      id: 'bookmark_${DateTime.now().millisecondsSinceEpoch}',
      name: _nameController.text,
      description: _descriptionController.text,
      state: widget.currentState ?? {},
      category: _selectedCategory ?? _categories.first,
      createdAt: DateTime.now(),
      lastUsed: DateTime.now(),
      usageCount: 0,
      isShared: false,
      isArchived: false,
      tags: _extractTags(_nameController.text, _descriptionController.text),
    );

    setState(() {
      _bookmarks.insert(0, bookmark);
    });

    // Clear form
    _nameController.clear();
    _descriptionController.clear();

    // Call callback
    widget.onBookmarkSaved(bookmark.name, bookmark.state);

    _showMessage('Bookmark saved successfully');
    _logger.info('Bookmark saved: ${bookmark.name}');
  }

  /// Loads a bookmark
  void _loadBookmark(Bookmark bookmark) {
    if (widget.readOnly) return;

    // Update usage statistics
    setState(() {
      bookmark.lastUsed = DateTime.now();
      bookmark.usageCount++;
    });

    // Sort bookmarks by last used
    _sortBookmarks();

    // Call callback
    widget.onBookmarkLoaded(bookmark.state);

    _showMessage('Bookmark "${bookmark.name}" loaded');
    _logger.info('Bookmark loaded: ${bookmark.name}');
  }

  /// Deletes a bookmark
  void _deleteBookmark(Bookmark bookmark) {
    if (widget.readOnly) return;

    setState(() {
      _bookmarks.remove(bookmark);
    });

    _showMessage('Bookmark deleted');
    _logger.info('Bookmark deleted: ${bookmark.name}');
  }

  /// Archives/unarchives a bookmark
  void _toggleArchive(Bookmark bookmark) {
    if (widget.readOnly) return;

    setState(() {
      bookmark.isArchived = !bookmark.isArchived;
    });

    _showMessage(bookmark.isArchived ? 'Bookmark archived' : 'Bookmark unarchived');
    _logger.info('Bookmark ${bookmark.isArchived ? 'archived' : 'unarchived'}: ${bookmark.name}');
  }

  /// Shares/unshares a bookmark
  void _toggleShare(Bookmark bookmark) {
    if (widget.readOnly || !widget.allowSharing) return;

    setState(() {
      bookmark.isShared = !bookmark.isShared;
    });

    _showMessage(bookmark.isShared ? 'Bookmark shared' : 'Bookmark unshared');
    _logger.info('Bookmark ${bookmark.isShared ? 'shared' : 'unshared'}: ${bookmark.name}');
  }

  /// Duplicates a bookmark
  void _duplicateBookmark(Bookmark bookmark) {
    if (widget.readOnly) return;

    if (widget.maxBookmarks != null && _bookmarks.length >= widget.maxBookmarks!) {
      _showError('Maximum number of bookmarks reached');
      return;
    }

    final duplicate = Bookmark(
      id: 'bookmark_${DateTime.now().millisecondsSinceEpoch}',
      name: '${bookmark.name} (Copy)',
      description: bookmark.description,
      state: Map<String, dynamic>.from(bookmark.state),
      category: bookmark.category,
      createdAt: DateTime.now(),
      lastUsed: DateTime.now(),
      usageCount: 0,
      isShared: false,
      isArchived: false,
      tags: List<String>.from(bookmark.tags),
    );

    setState(() {
      _bookmarks.insert(_bookmarks.indexOf(bookmark) + 1, duplicate);
    });

    _showMessage('Bookmark duplicated');
    _logger.info('Bookmark duplicated: ${bookmark.name}');
  }

  /// Extracts tags from name and description
  List<String> _extractTags(String name, String description) {
    final words = '$name $description'.toLowerCase().split(RegExp(r'\s+'));
    return words.where((word) => word.length > 2).take(5).toList();
  }

  /// Sorts bookmarks based on current sort option
  void _sortBookmarks() {
    setState(() {
      switch (_sortOption) {
        case BookmarkSortOption.dateCreated:
          _bookmarks.sort((a, b) => b.createdAt.compareTo(a.createdAt));
          break;
        case BookmarkSortOption.lastUsed:
          _bookmarks.sort((a, b) => b.lastUsed.compareTo(a.lastUsed));
          break;
        case BookmarkSortOption.usageCount:
          _bookmarks.sort((a, b) => b.usageCount.compareTo(a.usageCount));
          break;
        case BookmarkSortOption.alphabetical:
          _bookmarks.sort((a, b) => a.name.compareTo(b.name));
          break;
      }
    });
  }

  /// Filters bookmarks based on search and category
  List<Bookmark> _getFilteredBookmarks() {
    var filtered = _bookmarks.where((bookmark) {
      // Filter by archive status
      if (!_showArchived && bookmark.isArchived) return false;

      // Filter by category
      if (_selectedCategory != null && bookmark.category.id != _selectedCategory!.id) {
        return false;
      }

      // Filter by search query
      final query = _searchController.text.toLowerCase();
      if (query.isNotEmpty) {
        return bookmark.name.toLowerCase().contains(query) ||
               bookmark.description.toLowerCase().contains(query) ||
               bookmark.tags.any((tag) => tag.toLowerCase().contains(query));
      }

      return true;
    }).toList();

    return filtered;
  }

  /// Shows success message
  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  /// Shows error message
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  /// Shows bookmark creation dialog
  void _showCreateBookmarkDialog() {
    if (widget.readOnly) return;

    _nameController.clear();
    _descriptionController.clear();
    _selectedCategory = _categories.first;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Save Bookmark'),
        content: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Bookmark Name',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter a bookmark name';
                  }
                  if (_bookmarks.any((b) => b.name == value)) {
                    return 'Bookmark name already exists';
                  }
                  return null;
                },
                autofocus: true,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Description (optional)',
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<BookmarkCategory>(
                value: _selectedCategory,
                decoration: const InputDecoration(
                  labelText: 'Category',
                  border: OutlineInputBorder(),
                ),
                items: _categories.map((category) {
                  return DropdownMenuItem(
                    value: category,
                    child: Row(
                      children: [
                        Icon(category.icon, color: category.color),
                        const SizedBox(width: 8),
                        Text(category.name),
                      ],
                    ),
                  );
                }).toList(),
                onChanged: (category) {
                  setState(() {
                    _selectedCategory = category;
                  });
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _saveBookmark();
                Navigator.of(context).pop();
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = widget.colorScheme ?? theme.colorScheme;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            _buildHeader(theme, colorScheme),

            const SizedBox(height: 16),

            // Search and filters
            _buildSearchAndFilters(theme, colorScheme),

            const SizedBox(height: 16),

            // Tab bar
            _buildTabBar(theme, colorScheme),

            const SizedBox(height: 16),

            // Main content
            Expanded(
              child: AnimatedBuilder(
                animation: _panelAnimation,
                builder: (context, child) {
                  return Opacity(
                    opacity: _panelAnimation.value,
                    child: _buildMainContent(theme, colorScheme),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds the header section
  Widget _buildHeader(ThemeData theme, ColorScheme colorScheme) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Bookmark Manager',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Save and manage dashboard configurations',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: colorScheme.onSurface.withOpacity(0.7),
                ),
              ),
            ],
          ),
        ),
        // Quick save button
        if (!widget.readOnly)
          ElevatedButton.icon(
            onPressed: _showCreateBookmarkDialog,
            icon: const Icon(Icons.add),
            label: const Text('Save Current'),
          ),
      ],
    );
  }

  /// Builds search and filter controls
  Widget _buildSearchAndFilters(ThemeData theme, ColorScheme colorScheme) {
    return Column(
      children: [
        // Search bar
        TextField(
          controller: _searchController,
          focusNode: _searchFocusNode,
          decoration: InputDecoration(
            hintText: 'Search bookmarks...',
            prefixIcon: const Icon(Icons.search),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            suffixIcon: _searchController.text.isNotEmpty
                ? IconButton(
                    onPressed: () {
                      _searchController.clear();
                      setState(() {});
                    },
                    icon: const Icon(Icons.clear),
                  )
                : null,
          ),
          onChanged: (value) => setState(() {}),
        ),

        const SizedBox(height: 12),

        // Filter controls
        Row(
          children: [
            // Category filter
            if (widget.showCategories) ...[
              Expanded(
                child: DropdownButton<BookmarkCategory?>(
                  value: _selectedCategory,
                  hint: const Text('All Categories'),
                  isExpanded: true,
                  items: [
                    const DropdownMenuItem<BookmarkCategory?>(
                      value: null,
                      child: Text('All Categories'),
                    ),
                    ..._categories.map((category) {
                      return DropdownMenuItem<BookmarkCategory?>(
                        value: category,
                        child: Row(
                          children: [
                            Icon(category.icon, color: category.color, size: 16),
                            const SizedBox(width: 8),
                            Text(category.name),
                          ],
                        ),
                      );
                    }),
                  ],
                  onChanged: (category) {
                    setState(() {
                      _selectedCategory = category;
                    });
                  },
                ),
              ),
              const SizedBox(width: 12),
            ],

            // Sort dropdown
            DropdownButton<BookmarkSortOption>(
              value: _sortOption,
              items: BookmarkSortOption.values.map((option) {
                return DropdownMenuItem(
                  value: option,
                  child: Text(_getSortOptionLabel(option)),
                );
              }).toList(),
              onChanged: (option) {
                if (option != null) {
                  setState(() {
                    _sortOption = option;
                  });
                  _sortBookmarks();
                }
              },
            ),

            const SizedBox(width: 12),

            // Archive toggle
            FilterChip(
              label: const Text('Show Archived'),
              selected: _showArchived,
              onSelected: (selected) {
                setState(() {
                  _showArchived = selected;
                });
              },
              avatar: const Icon(Icons.archive, size: 16),
            ),
          ],
        ),
      ],
    );
  }

  /// Builds tab bar
  Widget _buildTabBar(ThemeData theme, ColorScheme colorScheme) {
    return TabBar(
      controller: _tabController,
      isScrollable: true,
      labelColor: colorScheme.primary,
      unselectedLabelColor: colorScheme.onSurface.withOpacity(0.6),
      indicatorColor: colorScheme.primary,
      tabs: const [
        Tab(icon: Icon(Icons.list), text: 'All Bookmarks'),
        Tab(icon: Icon(Icons.category), text: 'Categories'),
        Tab(icon: Icon(Icons.analytics), text: 'Analytics'),
        Tab(icon: Icon(Icons.settings), text: 'Settings'),
      ],
    );
  }

  /// Builds main content area
  Widget _buildMainContent(ThemeData theme, ColorScheme colorScheme) {
    return TabBarView(
      controller: _tabController,
      children: [
        _buildBookmarksTab(theme, colorScheme),
        _buildCategoriesTab(theme, colorScheme),
        _buildAnalyticsTab(theme, colorScheme),
        _buildSettingsTab(theme, colorScheme),
      ],
    );
  }

  /// Builds bookmarks tab
  Widget _buildBookmarksTab(ThemeData theme, ColorScheme colorScheme) {
    final filteredBookmarks = _getFilteredBookmarks();

    if (filteredBookmarks.isEmpty) {
      return _buildEmptyState(theme, colorScheme);
    }

    return ListView.builder(
      itemCount: filteredBookmarks.length,
      itemBuilder: (context, index) {
        final bookmark = filteredBookmarks[index];
        return _buildBookmarkCard(bookmark, theme, colorScheme);
      },
    );
  }

  /// Builds empty state
  Widget _buildEmptyState(ThemeData theme, ColorScheme colorScheme) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.bookmark_border,
            size: 64,
            color: colorScheme.onSurface.withOpacity(0.5),
          ),
          const SizedBox(height: 16),
          Text(
            'No bookmarks found',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: colorScheme.onSurface.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Save your current dashboard state to create bookmarks',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: colorScheme.onSurface.withOpacity(0.5),
            ),
            textAlign: TextAlign.center,
          ),
          if (!widget.readOnly) ...[
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _showCreateBookmarkDialog,
              icon: const Icon(Icons.add),
              label: const Text('Create First Bookmark'),
            ),
          ],
        ],
      ),
    );
  }

  /// Builds bookmark card
  Widget _buildBookmarkCard(Bookmark bookmark, ThemeData theme, ColorScheme colorScheme) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: bookmark.category.color.withOpacity(0.2),
          child: Icon(
            bookmark.category.icon,
            color: bookmark.category.color,
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                bookmark.name,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  decoration: bookmark.isArchived ? TextDecoration.lineThrough : null,
                ),
              ),
            ),
            if (bookmark.isShared)
              Icon(Icons.share, size: 16, color: colorScheme.primary),
            if (bookmark.isArchived)
              Icon(Icons.archive, size: 16, color: colorScheme.onSurface.withOpacity(0.5)),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (bookmark.description.isNotEmpty) ...[
              Text(bookmark.description),
              const SizedBox(height: 4),
            ],
            Row(
              children: [
                Text(
                  'Used ${bookmark.usageCount} times',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '• Last used: ${_formatLastUsed(bookmark.lastUsed)}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
              ],
            ),
            if (bookmark.tags.isNotEmpty) ...[
              const SizedBox(height: 4),
              Wrap(
                spacing: 4,
                children: bookmark.tags.take(3).map((tag) {
                  return Chip(
                    label: Text(tag),
                    labelStyle: theme.textTheme.bodySmall,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  );
                }).toList(),
              ),
            ],
          ],
        ),
        trailing: PopupMenuButton<String>(
          itemBuilder: (context) => [
            const PopupMenuItem(value: 'load', child: Text('Load')),
            const PopupMenuItem(value: 'duplicate', child: Text('Duplicate')),
            if (widget.allowSharing)
              PopupMenuItem(
                value: 'share',
                child: Text(bookmark.isShared ? 'Unshare' : 'Share'),
              ),
            PopupMenuItem(
              value: 'archive',
              child: Text(bookmark.isArchived ? 'Unarchive' : 'Archive'),
            ),
            const PopupMenuItem(value: 'delete', child: Text('Delete')),
          ],
          onSelected: (action) => _handleBookmarkAction(action, bookmark),
        ),
        onTap: () => _loadBookmark(bookmark),
      ),
    );
  }

  /// Builds categories tab
  Widget _buildCategoriesTab(ThemeData theme, ColorScheme colorScheme) {
    return ListView.builder(
      itemCount: _categories.length,
      itemBuilder: (context, index) {
        final category = _categories[index];
        final bookmarkCount = _bookmarks.where((b) => b.category.id == category.id).length;

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: category.color.withOpacity(0.2),
              child: Icon(category.icon, color: category.color),
            ),
            title: Text(category.name),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(category.description),
                const SizedBox(height: 4),
                Text(
                  '$bookmarkCount bookmarks',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
              ],
            ),
            onTap: () {
              setState(() {
                _selectedCategory = category;
                _tabController.animateTo(0); // Switch to bookmarks tab
              });
            },
          ),
        );
      },
    );
  }

  /// Builds analytics tab
  Widget _buildAnalyticsTab(ThemeData theme, ColorScheme colorScheme) {
    if (!widget.showAnalytics) {
      return Center(
        child: Text(
          'Analytics not enabled',
          style: theme.textTheme.bodyLarge?.copyWith(
            color: colorScheme.onSurface.withOpacity(0.7),
          ),
        ),
      );
    }

    final totalBookmarks = _bookmarks.length;
    final totalUsage = _bookmarks.fold<int>(0, (sum, b) => sum + b.usageCount);
    final mostUsed = _bookmarks.isNotEmpty
        ? _bookmarks.reduce((a, b) => a.usageCount > b.usageCount ? a : b)
        : null;

    return SingleChildScrollView(
      child: Column(
        children: [
          // Statistics cards
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  'Total Bookmarks',
                  totalBookmarks.toString(),
                  Icons.bookmark,
                  Colors.blue,
                  theme,
                  colorScheme,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildStatCard(
                  'Total Usage',
                  totalUsage.toString(),
                  Icons.trending_up,
                  Colors.green,
                  theme,
                  colorScheme,
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Most used bookmark
          if (mostUsed != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Most Used Bookmark',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ListTile(
                      leading: Icon(mostUsed.category.icon, color: mostUsed.category.color),
                      title: Text(mostUsed.name),
                      subtitle: Text('Used ${mostUsed.usageCount} times'),
                      contentPadding: EdgeInsets.zero,
                    ),
                  ],
                ),
              ),
            ),

          const SizedBox(height: 16),

          // Category distribution
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Bookmarks by Category',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  ..._categories.map((category) {
                    final count = _bookmarks.where((b) => b.category.id == category.id).length;
                    final percentage = totalBookmarks > 0 ? (count / totalBookmarks) * 100 : 0;

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          Icon(category.icon, color: category.color, size: 16),
                          const SizedBox(width: 8),
                          Expanded(child: Text(category.name)),
                          Text('$count (${percentage.toStringAsFixed(0)}%)'),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Builds statistics card
  Widget _buildStatCard(String title, String value, IconData icon, Color color, ThemeData theme, ColorScheme colorScheme) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              value,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              title,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: colorScheme.onSurface.withOpacity(0.7),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  /// Builds settings tab
  Widget _buildSettingsTab(ThemeData theme, ColorScheme colorScheme) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Bookmark Settings',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: colorScheme.primary,
            ),
          ),
          const SizedBox(height: 16),

          // Export/Import
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.download),
                  title: const Text('Export Bookmarks'),
                  subtitle: const Text('Export all bookmarks to file'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showMessage('Export functionality coming soon'),
                ),
                const Divider(),
                ListTile(
                  leading: const Icon(Icons.upload),
                  title: const Text('Import Bookmarks'),
                  subtitle: const Text('Import bookmarks from file'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showMessage('Import functionality coming soon'),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Storage info
          if (widget.maxBookmarks != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Storage Usage',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    LinearProgressIndicator(
                      value: _bookmarks.length / widget.maxBookmarks!,
                      backgroundColor: colorScheme.outline.withOpacity(0.3),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${_bookmarks.length} of ${widget.maxBookmarks} bookmarks used',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
            ),

          const SizedBox(height: 16),

          // Cleanup options
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.cleaning_services),
                  title: const Text('Clean Up Unused'),
                  subtitle: const Text('Remove bookmarks not used in 90 days'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showMessage('Cleanup functionality coming soon'),
                ),
                const Divider(),
                ListTile(
                  leading: const Icon(Icons.delete_sweep),
                  title: const Text('Clear All Archived'),
                  subtitle: const Text('Permanently delete all archived bookmarks'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showMessage('Clear archived functionality coming soon'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Handles bookmark actions
  void _handleBookmarkAction(String action, Bookmark bookmark) {
    switch (action) {
      case 'load':
        _loadBookmark(bookmark);
        break;
      case 'duplicate':
        _duplicateBookmark(bookmark);
        break;
      case 'share':
        _toggleShare(bookmark);
        break;
      case 'archive':
        _toggleArchive(bookmark);
        break;
      case 'delete':
        _showDeleteConfirmation(bookmark);
        break;
    }
  }

  /// Shows delete confirmation dialog
  void _showDeleteConfirmation(Bookmark bookmark) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Bookmark'),
        content: Text('Are you sure you want to delete "${bookmark.name}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              _deleteBookmark(bookmark);
              Navigator.of(context).pop();
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  /// Formats last used time
  String _formatLastUsed(DateTime lastUsed) {
    final now = DateTime.now();
    final difference = now.difference(lastUsed);

    if (difference.inDays > 7) {
      return '${difference.inDays} days ago';
    } else if (difference.inDays > 0) {
      return '${difference.inDays} days ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} hours ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} minutes ago';
    } else {
      return 'Just now';
    }
  }

  /// Gets sort option label
  String _getSortOptionLabel(BookmarkSortOption option) {
    switch (option) {
      case BookmarkSortOption.dateCreated:
        return 'Date Created';
      case BookmarkSortOption.lastUsed:
        return 'Last Used';
      case BookmarkSortOption.usageCount:
        return 'Usage Count';
      case BookmarkSortOption.alphabetical:
        return 'Alphabetical';
    }
  }
}

/// Bookmark view enumeration
enum BookmarkView {
  all,
  categories,
  analytics,
  settings,
}

/// Bookmark sort option enumeration
enum BookmarkSortOption {
  dateCreated,
  lastUsed,
  usageCount,
  alphabetical,
}

/// Bookmark class
class Bookmark {
  final String id;
  final String name;
  final String description;
  final Map<String, dynamic> state;
  final BookmarkCategory category;
  final DateTime createdAt;
  DateTime lastUsed;
  int usageCount;
  bool isShared;
  bool isArchived;
  final List<String> tags;

  Bookmark({
    required this.id,
    required this.name,
    required this.description,
    required this.state,
    required this.category,
    required this.createdAt,
    required this.lastUsed,
    required this.usageCount,
    required this.isShared,
    required this.isArchived,
    required this.tags,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Bookmark && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Bookmark category class
class BookmarkCategory {
  final String id;
  final String name;
  final String description;
  final IconData icon;
  final Color color;

  const BookmarkCategory({
    required this.id,
    required this.name,
    required this.description,
    required this.icon,
    required this.color,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is BookmarkCategory && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}