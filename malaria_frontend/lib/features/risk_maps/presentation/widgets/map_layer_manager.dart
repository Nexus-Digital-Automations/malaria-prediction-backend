/// Map Layer Manager Widget for Multi-Layer Mapping System
///
/// Comprehensive widget for managing multiple map layers including
/// environmental data, infrastructure layers, base maps, overlays,
/// markers, and providing layer switching and visibility controls.
///
/// Author: Claude AI Agent - Multi-Layer Mapping System
/// Created: 2025-09-19
library;

import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../domain/entities/environmental_layer.dart';
import '../../domain/entities/infrastructure_layer.dart';
import '../../domain/entities/map_layer.dart';
import '../../data/services/layer_data_service.dart';
import 'layer_opacity_slider.dart';

/// Comprehensive layer manager for multi-layer map visualization
class MapLayerManager extends StatefulWidget {
  /// Map instance for layer manipulation
  final dynamic mapController; // Could be GoogleMapController, FlutterMapController, etc.

  /// Initial list of active layers
  final List<MapLayer> initialLayers;

  /// Callback when layer visibility changes
  final void Function(String layerId, bool isVisible)? onLayerVisibilityChanged;

  /// Callback when layer opacity changes
  final void Function(String layerId, double opacity)? onLayerOpacityChanged;

  /// Callback when layer order changes
  final void Function(List<String> orderedLayerIds)? onLayerOrderChanged;

  /// Callback when layer configuration changes
  final void Function(String layerId, Map<String, dynamic> config)? onLayerConfigChanged;

  /// Whether to show advanced controls
  final bool showAdvancedControls;

  /// Maximum number of concurrent layers
  final int maxConcurrentLayers;

  /// Theme configuration for the layer manager
  final LayerManagerTheme? theme;

  const MapLayerManager({
    super.key,
    required this.mapController,
    this.initialLayers = const [],
    this.onLayerVisibilityChanged,
    this.onLayerOpacityChanged,
    this.onLayerOrderChanged,
    this.onLayerConfigChanged,
    this.showAdvancedControls = true,
    this.maxConcurrentLayers = 10,
    this.theme,
  });

  @override
  State<MapLayerManager> createState() => _MapLayerManagerState();
}

class _MapLayerManagerState extends State<MapLayerManager>
    with TickerProviderStateMixin {
  late final LayerDataService _layerDataService;
  late final TabController _tabController;
  late final AnimationController _animationController;
  late final Animation<double> _fadeAnimation;

  // Layer state management
  final Map<String, MapLayer> _activeLayers = {};
  final Map<String, EnvironmentalLayer> _environmentalLayers = {};
  final Map<String, InfrastructureLayer> _infrastructureLayers = {};
  final List<LayerGroup> _layerGroups = [];

  // UI state
  bool _isLoading = false;
  bool _isExpanded = true;
  String? _selectedLayerId;
  LayerFilterType _currentFilter = LayerFilterType.all;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  // Performance monitoring
  final Map<String, LayerPerformanceMetrics> _performanceMetrics = {};

  @override
  void initState() {
    super.initState();
    const String methodName = 'initState';
    debugPrint('[$methodName] Initializing MapLayerManager');

    _layerDataService = LayerDataService();
    _tabController = TabController(length: 4, vsync: this);
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );

    // Initialize with provided layers
    for (final layer in widget.initialLayers) {
      _activeLayers[layer.id] = layer;
    }

    // Start loading available layers
    _loadAvailableLayers();
    _animationController.forward();

    // Set up search listener
    _searchController.addListener(() {
      setState(() {
        _searchQuery = _searchController.text.toLowerCase();
      });
    });
  }

  @override
  void dispose() {
    const String methodName = 'dispose';
    debugPrint('[$methodName] Disposing MapLayerManager');

    _layerDataService.dispose();
    _tabController.dispose();
    _animationController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const String methodName = 'build';
    debugPrint('[$methodName] Building MapLayerManager widget');

    final theme = widget.theme ?? LayerManagerTheme.defaultTheme(context);

    return Container(
      decoration: BoxDecoration(
        color: theme.backgroundColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildHeader(theme),
          if (_isExpanded) ...[
            _buildSearchBar(theme),
            _buildTabBar(theme),
            _buildTabBarView(theme),
            if (widget.showAdvancedControls) _buildAdvancedControls(theme),
          ],
        ],
      ),
    );
  }

  /// Build the header with title and controls
  Widget _buildHeader(LayerManagerTheme theme) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.headerColor,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(12),
          topRight: Radius.circular(12),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.layers,
            color: theme.primaryColor,
            size: 20,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Layer Manager',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: theme.textColor,
              ),
            ),
          ),
          _buildLayerCounter(theme),
          const SizedBox(width: 8),
          _buildExpandToggle(theme),
        ],
      ),
    );
  }

  /// Build layer counter badge
  Widget _buildLayerCounter(LayerManagerTheme theme) {
    final activeCount = _activeLayers.values.where((layer) => layer.isVisible).length;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: theme.primaryColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$activeCount/${widget.maxConcurrentLayers}',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  /// Build expand/collapse toggle
  Widget _buildExpandToggle(LayerManagerTheme theme) {
    return IconButton(
      onPressed: () {
        setState(() {
          _isExpanded = !_isExpanded;
        });
      },
      icon: AnimatedRotation(
        turns: _isExpanded ? 0.5 : 0.0,
        duration: const Duration(milliseconds: 300),
        child: Icon(
          Icons.expand_more,
          color: theme.iconColor,
        ),
      ),
      iconSize: 20,
      padding: EdgeInsets.zero,
      constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
    );
  }

  /// Build search bar for filtering layers
  Widget _buildSearchBar(LayerManagerTheme theme) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search layers...',
                prefixIcon: Icon(Icons.search, color: theme.iconColor),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        onPressed: () {
                          _searchController.clear();
                        },
                        icon: Icon(Icons.clear, color: theme.iconColor),
                        iconSize: 18,
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: BorderSide(color: theme.borderColor),
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
              ),
              style: TextStyle(fontSize: 14, color: theme.textColor),
            ),
          ),
          const SizedBox(width: 8),
          _buildFilterDropdown(theme),
        ],
      ),
    );
  }

  /// Build filter dropdown for layer types
  Widget _buildFilterDropdown(LayerManagerTheme theme) {
    return DropdownButton<LayerFilterType>(
      value: _currentFilter,
      onChanged: (value) {
        if (value != null) {
          setState(() {
            _currentFilter = value;
          });
        }
      },
      items: LayerFilterType.values.map((filter) {
        return DropdownMenuItem(
          value: filter,
          child: Text(
            filter.displayName,
            style: TextStyle(fontSize: 12, color: theme.textColor),
          ),
        );
      }).toList(),
      underline: Container(),
      icon: Icon(Icons.filter_list, color: theme.iconColor, size: 18),
    );
  }

  /// Build tab bar for different layer categories
  Widget _buildTabBar(LayerManagerTheme theme) {
    return TabBar(
      controller: _tabController,
      isScrollable: true,
      indicatorColor: theme.primaryColor,
      labelColor: theme.primaryColor,
      unselectedLabelColor: theme.secondaryTextColor,
      labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      tabs: const [
        Tab(text: 'Active', icon: Icon(Icons.visibility, size: 16)),
        Tab(text: 'Environmental', icon: Icon(Icons.eco, size: 16)),
        Tab(text: 'Infrastructure', icon: Icon(Icons.location_city, size: 16)),
        Tab(text: 'Base Maps', icon: Icon(Icons.map, size: 16)),
      ],
    );
  }

  /// Build tab bar view with different layer lists
  Widget _buildTabBarView(LayerManagerTheme theme) {
    return SizedBox(
      height: 300,
      child: TabBarView(
        controller: _tabController,
        children: [
          _buildActiveLayersList(theme),
          _buildEnvironmentalLayersList(theme),
          _buildInfrastructureLayersList(theme),
          _buildBaseMapsList(theme),
        ],
      ),
    );
  }

  /// Build list of active layers
  Widget _buildActiveLayersList(LayerManagerTheme theme) {
    final filteredLayers = _getFilteredActiveLayers();

    if (filteredLayers.isEmpty) {
      return _buildEmptyState(theme, 'No active layers');
    }

    return ReorderableListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      itemCount: filteredLayers.length,
      onReorder: _reorderLayers,
      itemBuilder: (context, index) {
        final layer = filteredLayers[index];
        return _buildActiveLayerTile(layer, theme);
      },
    );
  }

  /// Build active layer tile with controls
  Widget _buildActiveLayerTile(MapLayer layer, LayerManagerTheme theme) {
    final metrics = _performanceMetrics[layer.id];

    return Card(
      key: ValueKey(layer.id),
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 2,
      child: ExpansionTile(
        leading: Icon(
          _getLayerIcon(layer.type),
          color: layer.isVisible ? theme.primaryColor : theme.disabledColor,
          size: 20,
        ),
        title: Text(
          layer.name,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: layer.isVisible ? theme.textColor : theme.disabledColor,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              layer.description,
              style: TextStyle(
                fontSize: 12,
                color: theme.secondaryTextColor,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            if (metrics != null) _buildPerformanceIndicator(metrics, theme),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Switch(
              value: layer.isVisible,
              onChanged: (value) => _toggleLayerVisibility(layer.id, value),
              activeColor: theme.primaryColor,
            ),
            const SizedBox(width: 8),
            Icon(
              Icons.drag_handle,
              color: theme.iconColor,
              size: 16,
            ),
          ],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                LayerOpacitySlider(
                  layerId: layer.id,
                  initialOpacity: layer.opacity,
                  onOpacityChanged: (opacity) {
                    _updateLayerOpacity(layer.id, opacity);
                  },
                ),
                const SizedBox(height: 8),
                _buildLayerActions(layer, theme),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Build environmental layers list
  Widget _buildEnvironmentalLayersList(LayerManagerTheme theme) {
    final filteredLayers = _getFilteredEnvironmentalLayers();

    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (filteredLayers.isEmpty) {
      return _buildEmptyState(theme, 'No environmental layers available');
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      itemCount: filteredLayers.length,
      itemBuilder: (context, index) {
        final layer = filteredLayers[index];
        return _buildEnvironmentalLayerTile(layer, theme);
      },
    );
  }

  /// Build environmental layer tile
  Widget _buildEnvironmentalLayerTile(EnvironmentalLayer layer, LayerManagerTheme theme) {
    final isActive = _activeLayers.containsKey(layer.id);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 1,
      child: ListTile(
        leading: Icon(
          _getEnvironmentalDataIcon(layer.dataType),
          color: theme.primaryColor,
          size: 20,
        ),
        title: Text(
          layer.name,
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              layer.description,
              style: TextStyle(fontSize: 12, color: theme.secondaryTextColor),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            _buildDataQualityIndicator(layer.qualityInfo, theme),
          ],
        ),
        trailing: IconButton(
          onPressed: isActive
              ? () => _removeLayer(layer.id)
              : () => _addEnvironmentalLayer(layer),
          icon: Icon(
            isActive ? Icons.remove_circle : Icons.add_circle,
            color: isActive ? Colors.red : theme.primaryColor,
          ),
        ),
      ),
    );
  }

  /// Build infrastructure layers list
  Widget _buildInfrastructureLayersList(LayerManagerTheme theme) {
    final filteredLayers = _getFilteredInfrastructureLayers();

    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (filteredLayers.isEmpty) {
      return _buildEmptyState(theme, 'No infrastructure layers available');
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      itemCount: filteredLayers.length,
      itemBuilder: (context, index) {
        final layer = filteredLayers[index];
        return _buildInfrastructureLayerTile(layer, theme);
      },
    );
  }

  /// Build infrastructure layer tile
  Widget _buildInfrastructureLayerTile(InfrastructureLayer layer, LayerManagerTheme theme) {
    final isActive = _activeLayers.containsKey(layer.id);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 1,
      child: ListTile(
        leading: Icon(
          layer.infrastructureType.defaultIcon,
          color: theme.primaryColor,
          size: 20,
        ),
        title: Text(
          layer.name,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              layer.description,
              style: TextStyle(fontSize: 12, color: theme.secondaryTextColor),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            _buildOperationalStatusIndicator(layer.operationalStatus, theme),
          ],
        ),
        trailing: IconButton(
          onPressed: isActive
              ? () => _removeLayer(layer.id)
              : () => _addInfrastructureLayer(layer),
          icon: Icon(
            isActive ? Icons.remove_circle : Icons.add_circle,
            color: isActive ? Colors.red : theme.primaryColor,
          ),
        ),
      ),
    );
  }

  /// Build base maps list
  Widget _buildBaseMapsList(LayerManagerTheme theme) {
    final baseMaps = _getAvailableBaseMaps();

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      itemCount: baseMaps.length,
      itemBuilder: (context, index) {
        final baseMap = baseMaps[index];
        return _buildBaseMapTile(baseMap, theme);
      },
    );
  }

  /// Build base map tile
  Widget _buildBaseMapTile(BaseMap baseMap, LayerManagerTheme theme) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 1,
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            image: baseMap.previewUrl != null
                ? DecorationImage(
                    image: NetworkImage(baseMap.previewUrl!),
                    fit: BoxFit.cover,
                  )
                : null,
            color: baseMap.previewUrl == null ? theme.primaryColor : null,
          ),
          child: baseMap.previewUrl == null
              ? Icon(Icons.map, color: Colors.white, size: 20)
              : null,
        ),
        title: Text(
          baseMap.name,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        ),
        subtitle: Text(
          baseMap.description,
          style: TextStyle(fontSize: 12, color: theme.secondaryTextColor),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Radio<String>(
          value: baseMap.id,
          groupValue: _selectedBaseMapId,
          onChanged: (value) => _selectBaseMap(value!),
          activeColor: theme.primaryColor,
        ),
      ),
    );
  }

  /// Build advanced controls section
  Widget _buildAdvancedControls(LayerManagerTheme theme) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border(
          top: BorderSide(color: theme.borderColor),
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _clearAllLayers,
                  icon: const Icon(Icons.clear_all, size: 16),
                  label: const Text('Clear All', style: TextStyle(fontSize: 12)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orange,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _refreshLayers,
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Refresh', style: TextStyle(fontSize: 12)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: theme.primaryColor,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _exportLayers,
                  icon: const Icon(Icons.download, size: 16),
                  label: const Text('Export', style: TextStyle(fontSize: 12)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _showSettings,
                  icon: const Icon(Icons.settings, size: 16),
                  label: const Text('Settings', style: TextStyle(fontSize: 12)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.grey.shade600,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Build empty state widget
  Widget _buildEmptyState(LayerManagerTheme theme, String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.layers_clear,
            size: 48,
            color: theme.disabledColor,
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: TextStyle(
              fontSize: 14,
              color: theme.secondaryTextColor,
            ),
          ),
        ],
      ),
    );
  }

  // Helper methods and state management

  /// Load available layers from the service
  Future<void> _loadAvailableLayers() async {
    const String methodName = '_loadAvailableLayers';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    setState(() {
      _isLoading = true;
    });

    try {
      debugPrint('[$methodName] Loading available layers');

      // Load environmental layers
      final environmentalLayers = await _layerDataService.loadAllEnvironmentalLayers();
      for (final layer in environmentalLayers) {
        _environmentalLayers[layer.id] = layer;
      }

      // Load infrastructure layers
      final infrastructureLayers = await _layerDataService.loadAllInfrastructureLayers();
      for (final layer in infrastructureLayers) {
        _infrastructureLayers[layer.id] = layer;
      }

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Loaded layers in ${endTime - startTime}ms');
    } catch (error) {
      debugPrint('[$methodName] Error loading layers: $error');
      _showErrorSnackBar('Failed to load layers: $error');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  /// Toggle layer visibility
  void _toggleLayerVisibility(String layerId, bool isVisible) {
    const String methodName = '_toggleLayerVisibility';
    debugPrint('[$methodName] Toggling layer $layerId visibility to $isVisible');

    if (_activeLayers.containsKey(layerId)) {
      final layer = _activeLayers[layerId]!;
      _activeLayers[layerId] = layer.copyWith(isVisible: isVisible);

      widget.onLayerVisibilityChanged?.call(layerId, isVisible);
      setState(() {});
    }
  }

  /// Update layer opacity
  void _updateLayerOpacity(String layerId, double opacity) {
    const String methodName = '_updateLayerOpacity';
    debugPrint('[$methodName] Updating layer $layerId opacity to $opacity');

    if (_activeLayers.containsKey(layerId)) {
      final layer = _activeLayers[layerId]!;
      _activeLayers[layerId] = layer.copyWith(opacity: opacity);

      widget.onLayerOpacityChanged?.call(layerId, opacity);
      setState(() {});
    }
  }

  /// Reorder layers
  void _reorderLayers(int oldIndex, int newIndex) {
    const String methodName = '_reorderLayers';
    debugPrint('[$methodName] Reordering layers from $oldIndex to $newIndex');

    if (newIndex > oldIndex) {
      newIndex -= 1;
    }

    final layerIds = _activeLayers.keys.toList();
    final item = layerIds.removeAt(oldIndex);
    layerIds.insert(newIndex, item);

    // Update z-index based on new order
    for (int i = 0; i < layerIds.length; i++) {
      final layerId = layerIds[i];
      if (_activeLayers.containsKey(layerId)) {
        final layer = _activeLayers[layerId]!;
        _activeLayers[layerId] = layer.copyWith(zIndex: i);
      }
    }

    widget.onLayerOrderChanged?.call(layerIds);
    setState(() {});
  }

  /// Add environmental layer to active layers
  void _addEnvironmentalLayer(EnvironmentalLayer layer) {
    const String methodName = '_addEnvironmentalLayer';
    debugPrint('[$methodName] Adding environmental layer: ${layer.id}');

    if (_activeLayers.length >= widget.maxConcurrentLayers) {
      _showErrorSnackBar('Maximum layer limit reached');
      return;
    }

    final mapLayer = layer.toMapLayer();
    _activeLayers[layer.id] = mapLayer;
    setState(() {});

    _startPerformanceMonitoring(layer.id);
  }

  /// Add infrastructure layer to active layers
  void _addInfrastructureLayer(InfrastructureLayer layer) {
    const String methodName = '_addInfrastructureLayer';
    debugPrint('[$methodName] Adding infrastructure layer: ${layer.id}');

    if (_activeLayers.length >= widget.maxConcurrentLayers) {
      _showErrorSnackBar('Maximum layer limit reached');
      return;
    }

    final mapLayer = layer.toMapLayer();
    _activeLayers[layer.id] = mapLayer;
    setState(() {});

    _startPerformanceMonitoring(layer.id);
  }

  /// Remove layer from active layers
  void _removeLayer(String layerId) {
    const String methodName = '_removeLayer';
    debugPrint('[$methodName] Removing layer: $layerId');

    _activeLayers.remove(layerId);
    _performanceMetrics.remove(layerId);
    setState(() {});
  }

  /// Clear all active layers
  void _clearAllLayers() {
    const String methodName = '_clearAllLayers';
    debugPrint('[$methodName] Clearing all layers');

    _activeLayers.clear();
    _performanceMetrics.clear();
    setState(() {});
  }

  /// Refresh all layers
  void _refreshLayers() {
    const String methodName = '_refreshLayers';
    debugPrint('[$methodName] Refreshing all layers');

    _layerDataService.clearCache();
    _loadAvailableLayers();
  }

  /// Export layers configuration
  void _exportLayers() {
    // Implementation for exporting layer configuration
    _showInfoSnackBar('Layer export functionality coming soon');
  }

  /// Show settings dialog
  void _showSettings() {
    showDialog(
      context: context,
      builder: (context) => _buildSettingsDialog(),
    );
  }

  /// Build settings dialog
  Widget _buildSettingsDialog() {
    return AlertDialog(
      title: const Text('Layer Manager Settings'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Settings options would go here
          const Text('Settings options will be implemented here'),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Close'),
        ),
      ],
    );
  }

  // Filter and search methods

  List<MapLayer> _getFilteredActiveLayers() {
    var layers = _activeLayers.values.toList();

    if (_searchQuery.isNotEmpty) {
      layers = layers
          .where((layer) =>
              layer.name.toLowerCase().contains(_searchQuery) ||
              layer.description.toLowerCase().contains(_searchQuery))
          .toList();
    }

    layers.sort((a, b) => b.zIndex.compareTo(a.zIndex));
    return layers;
  }

  List<EnvironmentalLayer> _getFilteredEnvironmentalLayers() {
    var layers = _environmentalLayers.values.toList();

    if (_searchQuery.isNotEmpty) {
      layers = layers
          .where((layer) =>
              layer.name.toLowerCase().contains(_searchQuery) ||
              layer.description.toLowerCase().contains(_searchQuery))
          .toList();
    }

    if (_currentFilter != LayerFilterType.all) {
      // Apply specific filters based on _currentFilter
    }

    layers.sort((a, b) => a.name.compareTo(b.name));
    return layers;
  }

  List<InfrastructureLayer> _getFilteredInfrastructureLayers() {
    var layers = _infrastructureLayers.values.toList();

    if (_searchQuery.isNotEmpty) {
      layers = layers
          .where((layer) =>
              layer.name.toLowerCase().contains(_searchQuery) ||
              layer.description.toLowerCase().contains(_searchQuery))
          .toList();
    }

    if (_currentFilter != LayerFilterType.all) {
      // Apply specific filters based on _currentFilter
    }

    layers.sort((a, b) => a.name.compareTo(b.name));
    return layers;
  }

  // Additional helper methods...

  String? _selectedBaseMapId;

  List<BaseMap> _getAvailableBaseMaps() {
    return [
      const BaseMap(
        id: 'osm',
        name: 'OpenStreetMap',
        description: 'Standard OpenStreetMap tiles',
        previewUrl: null,
      ),
      const BaseMap(
        id: 'satellite',
        name: 'Satellite',
        description: 'High-resolution satellite imagery',
        previewUrl: null,
      ),
      const BaseMap(
        id: 'terrain',
        name: 'Terrain',
        description: 'Topographic terrain map',
        previewUrl: null,
      ),
    ];
  }

  void _selectBaseMap(String baseMapId) {
    setState(() {
      _selectedBaseMapId = baseMapId;
    });
  }

  // UI helper methods

  IconData _getLayerIcon(LayerType type) {
    switch (type) {
      case LayerType.choropleth:
        return Icons.palette;
      case LayerType.markers:
        return Icons.place;
      case LayerType.heatmap:
        return Icons.grain;
      case LayerType.lines:
        return Icons.timeline;
      case LayerType.polygons:
        return Icons.crop_free;
      case LayerType.raster:
        return Icons.image;
      case LayerType.vector:
        return Icons.timeline;
      case LayerType.realtime:
        return Icons.live_tv;
      case LayerType.userGenerated:
        return Icons.edit;
      case LayerType.annotations:
        return Icons.label;
    }
  }

  IconData _getEnvironmentalDataIcon(EnvironmentalDataType dataType) {
    switch (dataType) {
      case EnvironmentalDataType.temperature:
        return Icons.thermostat;
      case EnvironmentalDataType.rainfall:
        return Icons.water_drop;
      case EnvironmentalDataType.vegetation:
        return Icons.park;
      case EnvironmentalDataType.humidity:
        return Icons.opacity;
      case EnvironmentalDataType.wind:
        return Icons.air;
      case EnvironmentalDataType.solar:
        return Icons.wb_sunny;
      case EnvironmentalDataType.elevation:
        return Icons.terrain;
      case EnvironmentalDataType.soil:
        return Icons.landscape;
      case EnvironmentalDataType.water:
        return Icons.waves;
      case EnvironmentalDataType.landUse:
        return Icons.location_city;
      case EnvironmentalDataType.airQuality:
        return Icons.cloud;
      case EnvironmentalDataType.climate:
        return Icons.ac_unit;
    }
  }

  Widget _buildDataQualityIndicator(DataQualityInfo qualityInfo, LayerManagerTheme theme) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: qualityInfo.level.color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          'Quality: ${qualityInfo.level.name}',
          style: TextStyle(fontSize: 10, color: theme.secondaryTextColor),
        ),
      ],
    );
  }

  Widget _buildOperationalStatusIndicator(OperationalStatus status, LayerManagerTheme theme) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: status.level.color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          'Status: ${status.level.name}',
          style: TextStyle(fontSize: 10, color: theme.secondaryTextColor),
        ),
      ],
    );
  }

  Widget _buildPerformanceIndicator(LayerPerformanceMetrics metrics, LayerManagerTheme theme) {
    return Container(
      margin: const EdgeInsets.only(top: 4),
      child: Row(
        children: [
          Icon(
            Icons.speed,
            size: 12,
            color: _getPerformanceColor(metrics.loadTime),
          ),
          const SizedBox(width: 4),
          Text(
            '${metrics.loadTime}ms',
            style: TextStyle(
              fontSize: 10,
              color: theme.secondaryTextColor,
            ),
          ),
        ],
      ),
    );
  }

  Color _getPerformanceColor(int loadTime) {
    if (loadTime < 1000) return Colors.green;
    if (loadTime < 3000) return Colors.orange;
    return Colors.red;
  }

  Widget _buildLayerActions(MapLayer layer, LayerManagerTheme theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        TextButton.icon(
          onPressed: () => _showLayerInfo(layer),
          icon: const Icon(Icons.info_outline, size: 16),
          label: const Text('Info', style: TextStyle(fontSize: 12)),
        ),
        TextButton.icon(
          onPressed: () => _configureLayer(layer),
          icon: const Icon(Icons.settings, size: 16),
          label: const Text('Configure', style: TextStyle(fontSize: 12)),
        ),
        TextButton.icon(
          onPressed: () => _removeLayer(layer.id),
          icon: const Icon(Icons.delete_outline, size: 16),
          label: const Text('Remove', style: TextStyle(fontSize: 12)),
          style: TextButton.styleFrom(foregroundColor: Colors.red),
        ),
      ],
    );
  }

  void _showLayerInfo(MapLayer layer) {
    showDialog(
      context: context,
      builder: (context) => _buildLayerInfoDialog(layer),
    );
  }

  Widget _buildLayerInfoDialog(MapLayer layer) {
    return AlertDialog(
      title: Text(layer.name),
      content: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Description: ${layer.description}'),
            const SizedBox(height: 8),
            Text('Type: ${layer.type.displayName}'),
            const SizedBox(height: 8),
            Text('Opacity: ${(layer.opacity * 100).toInt()}%'),
            const SizedBox(height: 8),
            Text('Z-Index: ${layer.zIndex}'),
            if (layer.minZoom != null)
              Text('Min Zoom: ${layer.minZoom}'),
            if (layer.maxZoom != null)
              Text('Max Zoom: ${layer.maxZoom}'),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Close'),
        ),
      ],
    );
  }

  void _configureLayer(MapLayer layer) {
    // Implementation for layer configuration
    _showInfoSnackBar('Layer configuration coming soon');
  }

  void _startPerformanceMonitoring(String layerId) {
    final startTime = DateTime.now().millisecondsSinceEpoch;

    // Simulate performance monitoring
    Timer(const Duration(milliseconds: 500), () {
      final endTime = DateTime.now().millisecondsSinceEpoch;
      _performanceMetrics[layerId] = LayerPerformanceMetrics(
        loadTime: endTime - startTime,
        renderTime: 100,
        memoryUsage: 1024,
      );
      setState(() {});
    });
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _showInfoSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.blue,
      ),
    );
  }
}

// Supporting classes and enums

enum LayerFilterType {
  all,
  environmental,
  infrastructure,
  active,
  inactive;

  String get displayName {
    switch (this) {
      case LayerFilterType.all:
        return 'All';
      case LayerFilterType.environmental:
        return 'Environmental';
      case LayerFilterType.infrastructure:
        return 'Infrastructure';
      case LayerFilterType.active:
        return 'Active';
      case LayerFilterType.inactive:
        return 'Inactive';
    }
  }
}

class LayerGroup {
  final String id;
  final String name;
  final List<String> layerIds;
  final bool isExpanded;

  const LayerGroup({
    required this.id,
    required this.name,
    required this.layerIds,
    required this.isExpanded,
  });
}

class BaseMap {
  final String id;
  final String name;
  final String description;
  final String? previewUrl;

  const BaseMap({
    required this.id,
    required this.name,
    required this.description,
    this.previewUrl,
  });
}

class LayerPerformanceMetrics {
  final int loadTime;
  final int renderTime;
  final int memoryUsage;

  const LayerPerformanceMetrics({
    required this.loadTime,
    required this.renderTime,
    required this.memoryUsage,
  });
}

class LayerManagerTheme {
  final Color backgroundColor;
  final Color headerColor;
  final Color primaryColor;
  final Color textColor;
  final Color secondaryTextColor;
  final Color iconColor;
  final Color borderColor;
  final Color disabledColor;

  const LayerManagerTheme({
    required this.backgroundColor,
    required this.headerColor,
    required this.primaryColor,
    required this.textColor,
    required this.secondaryTextColor,
    required this.iconColor,
    required this.borderColor,
    required this.disabledColor,
  });

  static LayerManagerTheme defaultTheme(BuildContext context) {
    final theme = Theme.of(context);
    return LayerManagerTheme(
      backgroundColor: theme.cardColor,
      headerColor: theme.primaryColor.withOpacity(0.1),
      primaryColor: theme.primaryColor,
      textColor: theme.textTheme.bodyLarge?.color ?? Colors.black,
      secondaryTextColor: theme.textTheme.bodySmall?.color ?? Colors.grey,
      iconColor: theme.iconTheme.color ?? Colors.grey,
      borderColor: theme.dividerColor,
      disabledColor: theme.disabledColor,
    );
  }
}