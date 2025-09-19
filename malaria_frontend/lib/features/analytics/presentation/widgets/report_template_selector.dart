/// Report template selector widget for malaria analytics report generation
///
/// This widget provides a comprehensive template selection interface with
/// preview functionality, search, filtering, and template management.
///
/// Features:
/// - Template grid with visual previews
/// - Search and filtering capabilities
/// - Template details and metadata display
/// - Favorite templates management
/// - Template usage statistics
/// - Custom template creation support
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/report_template_model.dart';
import '../../domain/entities/analytics_filters.dart';

/// Report template selector widget with advanced functionality
class ReportTemplateSelector extends StatefulWidget {
  /// Available report templates
  final List<ReportTemplate> templates;

  /// Currently selected template
  final ReportTemplate? selectedTemplate;

  /// Callback when template is selected
  final ValueChanged<ReportTemplate> onTemplateSelected;

  /// Callback when template details are requested
  final ValueChanged<ReportTemplate>? onTemplateDetails;

  /// Callback when template is favorited
  final ValueChanged<ReportTemplate>? onTemplateFavorited;

  /// Whether to show template usage statistics
  final bool showUsageStats;

  /// Whether to enable template management features
  final bool enableManagement;

  /// Custom template creation callback
  final VoidCallback? onCreateCustomTemplate;

  /// Template search placeholder text
  final String searchPlaceholder;

  /// Whether to show category filters
  final bool showCategoryFilters;

  /// Initial search query
  final String? initialSearchQuery;

  /// Initial category filter
  final ReportTemplateCategory? initialCategory;

  const ReportTemplateSelector({
    super.key,
    required this.templates,
    this.selectedTemplate,
    required this.onTemplateSelected,
    this.onTemplateDetails,
    this.onTemplateFavorited,
    this.showUsageStats = true,
    this.enableManagement = false,
    this.onCreateCustomTemplate,
    this.searchPlaceholder = 'Search report templates...',
    this.showCategoryFilters = true,
    this.initialSearchQuery,
    this.initialCategory,
  });

  @override
  State<ReportTemplateSelector> createState() => _ReportTemplateSelectorState();
}

class _ReportTemplateSelectorState extends State<ReportTemplateSelector>
    with TickerProviderStateMixin {
  /// Search controller
  late TextEditingController _searchController;

  /// Animation controller for grid animations
  late AnimationController _animationController;

  /// Search query
  String _searchQuery = '';

  /// Selected category filter
  ReportTemplateCategory? _selectedCategory;

  /// View mode (grid or list)
  TemplateViewMode _viewMode = TemplateViewMode.grid;

  /// Sort criteria
  TemplateSortCriteria _sortCriteria = TemplateSortCriteria.name;

  /// Sort direction
  SortDirection _sortDirection = SortDirection.ascending;

  /// Favorite template IDs
  final Set<String> _favoriteTemplateIds = {};

  /// Filtered and sorted templates
  List<ReportTemplate> _filteredTemplates = [];

  @override
  void initState() {
    super.initState();

    // Initialize controllers
    _searchController = TextEditingController(text: widget.initialSearchQuery ?? '');
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    // Initialize state
    _searchQuery = widget.initialSearchQuery ?? '';
    _selectedCategory = widget.initialCategory;

    // Initial filtering
    _updateFilteredTemplates();

    // Start animation
    _animationController.forward();

    // Log initialization
    debugPrint('ReportTemplateSelector initialized with ${widget.templates.length} templates');
  }

  @override
  void didUpdateWidget(ReportTemplateSelector oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.templates != widget.templates) {
      _updateFilteredTemplates();
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildHeader(),
        _buildSearchAndFilters(),
        if (widget.showCategoryFilters) _buildCategoryFilter(),
        _buildViewControls(),
        Expanded(
          child: _buildTemplateView(),
        ),
      ],
    );
  }

  /// Builds the header section
  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Icon(
            Icons.dashboard_customize,
            color: Theme.of(context).colorScheme.primary,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Report Templates',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  '${_filteredTemplates.length} of ${widget.templates.length} templates',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
              ],
            ),
          ),
          if (widget.enableManagement && widget.onCreateCustomTemplate != null)
            FilledButton.icon(
              onPressed: widget.onCreateCustomTemplate,
              icon: const Icon(Icons.add),
              label: const Text('Create'),
            ),
        ],
      ),
    );
  }

  /// Builds search and filter section
  Widget _buildSearchAndFilters() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: widget.searchPlaceholder,
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: _clearSearch,
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: Theme.of(context).colorScheme.surface,
              ),
              onChanged: _onSearchChanged,
            ),
          ),
          const SizedBox(width: 12),
          _buildSortButton(),
        ],
      ),
    );
  }

  /// Builds category filter chips
  Widget _buildCategoryFilter() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            _buildCategoryChip('All', null),
            const SizedBox(width: 8),
            ...ReportTemplateCategory.values.map(
              (category) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: _buildCategoryChip(
                  _getCategoryDisplayName(category),
                  category,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Builds a category filter chip
  Widget _buildCategoryChip(String label, ReportTemplateCategory? category) {
    final isSelected = _selectedCategory == category;

    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() {
          _selectedCategory = selected ? category : null;
        });
        _updateFilteredTemplates();
      },
      backgroundColor: Theme.of(context).colorScheme.surface,
      selectedColor: Theme.of(context).colorScheme.primaryContainer,
      labelStyle: TextStyle(
        color: isSelected
            ? Theme.of(context).colorScheme.onPrimaryContainer
            : Theme.of(context).colorScheme.onSurface,
      ),
    );
  }

  /// Builds view controls (grid/list toggle, sort)
  Widget _buildViewControls() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          SegmentedButton<TemplateViewMode>(
            segments: const [
              ButtonSegment(
                value: TemplateViewMode.grid,
                icon: Icon(Icons.grid_view),
                label: Text('Grid'),
              ),
              ButtonSegment(
                value: TemplateViewMode.list,
                icon: Icon(Icons.list),
                label: Text('List'),
              ),
            ],
            selected: {_viewMode},
            onSelectionChanged: (Set<TemplateViewMode> newSelection) {
              setState(() {
                _viewMode = newSelection.first;
              });
            },
          ),
          const Spacer(),
          if (widget.showUsageStats)
            Chip(
              avatar: const Icon(Icons.analytics, size: 16),
              label: Text('Usage: ${_getTotalUsage()}'),
              backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
              labelStyle: TextStyle(
                color: Theme.of(context).colorScheme.onSecondaryContainer,
                fontSize: 12,
              ),
            ),
        ],
      ),
    );
  }

  /// Builds sort button
  Widget _buildSortButton() {
    return PopupMenuButton<TemplateSortCriteria>(
      icon: Icon(
        _sortDirection == SortDirection.ascending
            ? Icons.sort_by_alpha
            : Icons.sort_by_alpha,
        color: Theme.of(context).colorScheme.primary,
      ),
      tooltip: 'Sort templates',
      onSelected: (criteria) {
        setState(() {
          if (_sortCriteria == criteria) {
            // Toggle direction if same criteria
            _sortDirection = _sortDirection == SortDirection.ascending
                ? SortDirection.descending
                : SortDirection.ascending;
          } else {
            _sortCriteria = criteria;
            _sortDirection = SortDirection.ascending;
          }
        });
        _updateFilteredTemplates();
      },
      itemBuilder: (context) => [
        PopupMenuItem(
          value: TemplateSortCriteria.name,
          child: ListTile(
            leading: const Icon(Icons.sort_by_alpha),
            title: const Text('Name'),
            trailing: _sortCriteria == TemplateSortCriteria.name
                ? Icon(_sortDirection == SortDirection.ascending
                    ? Icons.arrow_upward
                    : Icons.arrow_downward)
                : null,
          ),
        ),
        PopupMenuItem(
          value: TemplateSortCriteria.category,
          child: ListTile(
            leading: const Icon(Icons.category),
            title: const Text('Category'),
            trailing: _sortCriteria == TemplateSortCriteria.category
                ? Icon(_sortDirection == SortDirection.ascending
                    ? Icons.arrow_upward
                    : Icons.arrow_downward)
                : null,
          ),
        ),
        PopupMenuItem(
          value: TemplateSortCriteria.usage,
          child: ListTile(
            leading: const Icon(Icons.trending_up),
            title: const Text('Usage'),
            trailing: _sortCriteria == TemplateSortCriteria.usage
                ? Icon(_sortDirection == SortDirection.ascending
                    ? Icons.arrow_upward
                    : Icons.arrow_downward)
                : null,
          ),
        ),
        PopupMenuItem(
          value: TemplateSortCriteria.modified,
          child: ListTile(
            leading: const Icon(Icons.schedule),
            title: const Text('Modified'),
            trailing: _sortCriteria == TemplateSortCriteria.modified
                ? Icon(_sortDirection == SortDirection.ascending
                    ? Icons.arrow_upward
                    : Icons.arrow_downward)
                : null,
          ),
        ),
      ],
    );
  }

  /// Builds the template view (grid or list)
  Widget _buildTemplateView() {
    if (_filteredTemplates.isEmpty) {
      return _buildEmptyState();
    }

    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return _viewMode == TemplateViewMode.grid
            ? _buildGridView()
            : _buildListView();
      },
    );
  }

  /// Builds grid view
  Widget _buildGridView() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: GridView.builder(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.75,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
        ),
        itemCount: _filteredTemplates.length,
        itemBuilder: (context, index) {
          final template = _filteredTemplates[index];
          final animation = Tween<double>(begin: 0, end: 1).animate(
            CurvedAnimation(
              parent: _animationController,
              curve: Interval(
                index * 0.1,
                (index * 0.1 + 0.3).clamp(0.0, 1.0),
                curve: Curves.easeOutBack,
              ),
            ),
          );

          return AnimatedBuilder(
            animation: animation,
            builder: (context, child) {
              return Transform.scale(
                scale: animation.value,
                child: TemplateGridCard(
                  template: template,
                  isSelected: widget.selectedTemplate?.id == template.id,
                  isFavorite: _favoriteTemplateIds.contains(template.id),
                  showUsageStats: widget.showUsageStats,
                  onSelected: widget.onTemplateSelected,
                  onDetails: widget.onTemplateDetails,
                  onFavoriteToggled: _toggleFavorite,
                ),
              );
            },
          );
        },
      ),
    );
  }

  /// Builds list view
  Widget _buildListView() {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _filteredTemplates.length,
      separatorBuilder: (context, index) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final template = _filteredTemplates[index];
        final animation = Tween<Offset>(
          begin: const Offset(1, 0),
          end: Offset.zero,
        ).animate(
          CurvedAnimation(
            parent: _animationController,
            curve: Interval(
              index * 0.05,
              (index * 0.05 + 0.2).clamp(0.0, 1.0),
              curve: Curves.easeOut,
            ),
          ),
        );

        return AnimatedBuilder(
          animation: animation,
          builder: (context, child) {
            return SlideTransition(
              position: animation,
              child: TemplateListTile(
                template: template,
                isSelected: widget.selectedTemplate?.id == template.id,
                isFavorite: _favoriteTemplateIds.contains(template.id),
                showUsageStats: widget.showUsageStats,
                onSelected: widget.onTemplateSelected,
                onDetails: widget.onTemplateDetails,
                onFavoriteToggled: _toggleFavorite,
              ),
            );
          },
        );
      },
    );
  }

  /// Builds empty state
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.search_off,
            size: 64,
            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.4),
          ),
          const SizedBox(height: 16),
          Text(
            'No templates found',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Try adjusting your search or filters',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _clearAllFilters,
            icon: const Icon(Icons.refresh),
            label: const Text('Clear Filters'),
          ),
        ],
      ),
    );
  }

  /// Handles search text changes
  void _onSearchChanged(String value) {
    setState(() {
      _searchQuery = value;
    });
    _updateFilteredTemplates();
  }

  /// Clears search
  void _clearSearch() {
    _searchController.clear();
    setState(() {
      _searchQuery = '';
    });
    _updateFilteredTemplates();
  }

  /// Clears all filters
  void _clearAllFilters() {
    _searchController.clear();
    setState(() {
      _searchQuery = '';
      _selectedCategory = null;
    });
    _updateFilteredTemplates();
  }

  /// Toggles template favorite status
  void _toggleFavorite(ReportTemplate template) {
    setState(() {
      if (_favoriteTemplateIds.contains(template.id)) {
        _favoriteTemplateIds.remove(template.id);
      } else {
        _favoriteTemplateIds.add(template.id);
      }
    });

    widget.onTemplateFavorited?.call(template);

    // Haptic feedback
    HapticFeedback.lightImpact();
  }

  /// Updates filtered templates based on current filters
  void _updateFilteredTemplates() {
    var filtered = widget.templates.where((template) {
      // Search filter
      if (_searchQuery.isNotEmpty) {
        final query = _searchQuery.toLowerCase();
        if (!template.name.toLowerCase().contains(query) &&
            !template.description.toLowerCase().contains(query) &&
            !template.metadata.tags.any((tag) => tag.toLowerCase().contains(query))) {
          return false;
        }
      }

      // Category filter
      if (_selectedCategory != null && template.category != _selectedCategory) {
        return false;
      }

      return true;
    }).toList();

    // Sort templates
    filtered.sort((a, b) {
      int compare = 0;

      switch (_sortCriteria) {
        case TemplateSortCriteria.name:
          compare = a.name.compareTo(b.name);
          break;
        case TemplateSortCriteria.category:
          compare = a.category.index.compareTo(b.category.index);
          break;
        case TemplateSortCriteria.usage:
          compare = a.metadata.usageStats.totalUsage.compareTo(b.metadata.usageStats.totalUsage);
          break;
        case TemplateSortCriteria.modified:
          compare = a.metadata.modifiedAt.compareTo(b.metadata.modifiedAt);
          break;
      }

      return _sortDirection == SortDirection.ascending ? compare : -compare;
    });

    setState(() {
      _filteredTemplates = filtered;
    });

    // Restart animation
    _animationController.reset();
    _animationController.forward();
  }

  /// Gets category display name
  String _getCategoryDisplayName(ReportTemplateCategory category) {
    switch (category) {
      case ReportTemplateCategory.executive:
        return 'Executive';
      case ReportTemplateCategory.technical:
        return 'Technical';
      case ReportTemplateCategory.operational:
        return 'Operational';
      case ReportTemplateCategory.compliance:
        return 'Compliance';
      case ReportTemplateCategory.research:
        return 'Research';
      case ReportTemplateCategory.custom:
        return 'Custom';
    }
  }

  /// Gets total usage across all templates
  int _getTotalUsage() {
    return _filteredTemplates.fold(
      0,
      (total, template) => total + template.metadata.usageStats.totalUsage,
    );
  }
}

/// Template grid card widget
class TemplateGridCard extends StatelessWidget {
  final ReportTemplate template;
  final bool isSelected;
  final bool isFavorite;
  final bool showUsageStats;
  final ValueChanged<ReportTemplate> onSelected;
  final ValueChanged<ReportTemplate>? onDetails;
  final ValueChanged<ReportTemplate> onFavoriteToggled;

  const TemplateGridCard({
    super.key,
    required this.template,
    required this.isSelected,
    required this.isFavorite,
    required this.showUsageStats,
    required this.onSelected,
    required this.onDetails,
    required this.onFavoriteToggled,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: isSelected ? 8 : 2,
      color: isSelected
          ? Theme.of(context).colorScheme.primaryContainer
          : Theme.of(context).colorScheme.surface,
      child: InkWell(
        onTap: () => onSelected(template),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(context),
              const SizedBox(height: 8),
              _buildTitle(context),
              const SizedBox(height: 4),
              _buildDescription(context),
              const Spacer(),
              _buildFooter(context),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      children: [
        Icon(
          _getCategoryIcon(template.category),
          color: isSelected
              ? Theme.of(context).colorScheme.onPrimaryContainer
              : Theme.of(context).colorScheme.primary,
          size: 20,
        ),
        const Spacer(),
        IconButton(
          icon: Icon(
            isFavorite ? Icons.favorite : Icons.favorite_border,
            color: isFavorite
                ? Colors.red
                : Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            size: 18,
          ),
          onPressed: () => onFavoriteToggled(template),
          visualDensity: VisualDensity.compact,
        ),
        if (onDetails != null)
          IconButton(
            icon: Icon(
              Icons.info_outline,
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              size: 18,
            ),
            onPressed: () => onDetails!(template),
            visualDensity: VisualDensity.compact,
          ),
      ],
    );
  }

  Widget _buildTitle(BuildContext context) {
    return Text(
      template.name,
      style: Theme.of(context).textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.bold,
        color: isSelected
            ? Theme.of(context).colorScheme.onPrimaryContainer
            : null,
      ),
      maxLines: 2,
      overflow: TextOverflow.ellipsis,
    );
  }

  Widget _buildDescription(BuildContext context) {
    return Text(
      template.description,
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
        color: isSelected
            ? Theme.of(context).colorScheme.onPrimaryContainer.withOpacity(0.8)
            : Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
      ),
      maxLines: 3,
      overflow: TextOverflow.ellipsis,
    );
  }

  Widget _buildFooter(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              Icons.schedule,
              size: 14,
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
            ),
            const SizedBox(width: 4),
            Text(
              '${template.metadata.estimatedGenerationTime} min',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.secondaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                template.category.name.toUpperCase(),
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.onSecondaryContainer,
                ),
              ),
            ),
          ],
        ),
        if (showUsageStats && template.metadata.usageStats.totalUsage > 0) ...[
          const SizedBox(height: 4),
          Text(
            'Used ${template.metadata.usageStats.totalUsage} times',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
              fontSize: 10,
            ),
          ),
        ],
      ],
    );
  }

  IconData _getCategoryIcon(ReportTemplateCategory category) {
    switch (category) {
      case ReportTemplateCategory.executive:
        return Icons.business;
      case ReportTemplateCategory.technical:
        return Icons.engineering;
      case ReportTemplateCategory.operational:
        return Icons.settings;
      case ReportTemplateCategory.compliance:
        return Icons.verified;
      case ReportTemplateCategory.research:
        return Icons.science;
      case ReportTemplateCategory.custom:
        return Icons.tune;
    }
  }
}

/// Template list tile widget
class TemplateListTile extends StatelessWidget {
  final ReportTemplate template;
  final bool isSelected;
  final bool isFavorite;
  final bool showUsageStats;
  final ValueChanged<ReportTemplate> onSelected;
  final ValueChanged<ReportTemplate>? onDetails;
  final ValueChanged<ReportTemplate> onFavoriteToggled;

  const TemplateListTile({
    super.key,
    required this.template,
    required this.isSelected,
    required this.isFavorite,
    required this.showUsageStats,
    required this.onSelected,
    required this.onDetails,
    required this.onFavoriteToggled,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: isSelected ? 4 : 1,
      color: isSelected
          ? Theme.of(context).colorScheme.primaryContainer
          : Theme.of(context).colorScheme.surface,
      child: ListTile(
        onTap: () => onSelected(template),
        leading: Icon(
          _getCategoryIcon(template.category),
          color: isSelected
              ? Theme.of(context).colorScheme.onPrimaryContainer
              : Theme.of(context).colorScheme.primary,
        ),
        title: Text(
          template.name,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: isSelected
                ? Theme.of(context).colorScheme.onPrimaryContainer
                : null,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              template.description,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: isSelected
                    ? Theme.of(context).colorScheme.onPrimaryContainer.withOpacity(0.8)
                    : Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
              ),
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Chip(
                  label: Text(template.category.name.toUpperCase()),
                  backgroundColor: Theme.of(context).colorScheme.secondaryContainer,
                  labelStyle: TextStyle(
                    color: Theme.of(context).colorScheme.onSecondaryContainer,
                    fontSize: 10,
                  ),
                  visualDensity: VisualDensity.compact,
                ),
                const SizedBox(width: 8),
                Text(
                  '${template.metadata.estimatedGenerationTime} min',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
                if (showUsageStats && template.metadata.usageStats.totalUsage > 0) ...[
                  const SizedBox(width: 8),
                  Text(
                    '• ${template.metadata.usageStats.totalUsage} uses',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: Icon(
                isFavorite ? Icons.favorite : Icons.favorite_border,
                color: isFavorite
                    ? Colors.red
                    : Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              ),
              onPressed: () => onFavoriteToggled(template),
            ),
            if (onDetails != null)
              IconButton(
                icon: Icon(
                  Icons.info_outline,
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                ),
                onPressed: () => onDetails!(template),
              ),
          ],
        ),
        contentPadding: const EdgeInsets.all(12),
      ),
    );
  }

  IconData _getCategoryIcon(ReportTemplateCategory category) {
    switch (category) {
      case ReportTemplateCategory.executive:
        return Icons.business;
      case ReportTemplateCategory.technical:
        return Icons.engineering;
      case ReportTemplateCategory.operational:
        return Icons.settings;
      case ReportTemplateCategory.compliance:
        return Icons.verified;
      case ReportTemplateCategory.research:
        return Icons.science;
      case ReportTemplateCategory.custom:
        return Icons.tune;
    }
  }
}

/// Template view mode enumeration
enum TemplateViewMode {
  grid,
  list,
}

/// Template sort criteria enumeration
enum TemplateSortCriteria {
  name,
  category,
  usage,
  modified,
}

/// Sort direction enumeration
enum SortDirection {
  ascending,
  descending,
}