/// Enhanced Layer Control Panel for Multi-Layer Mapping System
///
/// Comprehensive widget for managing environmental, infrastructure, and base
/// map layers with advanced controls for opacity, blending, and configuration.
/// Integrates with the new multi-layer mapping system architecture.
///
/// Author: Claude AI Agent - Multi-Layer Mapping System Enhancement
/// Created: 2025-09-18, Enhanced: 2025-09-19
library;

import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../domain/entities/map_layer.dart';
import '../../data/services/layer_data_service.dart';
import '../../domain/entities/environmental_layer.dart';
import '../../domain/entities/infrastructure_layer.dart';
import 'layer_opacity_slider.dart';
import 'map_layer_manager.dart';

/// Enhanced layer control panel with comprehensive multi-layer support
class LayerControlPanel extends StatefulWidget {
  /// List of map layers to display
  final List<MapLayer> mapLayers;

  /// Callback when layer visibility is toggled
  final Function(String layerId, bool isVisible)? onLayerToggle;

  /// Callback when layer opacity is changed
  final Function(String layerId, double opacity)? onLayerOpacityChanged;

  /// Callback when layer configuration changes
  final Function(String layerId, Map<String, dynamic> config)? onLayerConfigChanged;

  /// Map controller for layer management
  final dynamic mapController;

  /// Whether to show advanced controls
  final bool showAdvancedControls;

  /// Whether to show environmental layers section
  final bool showEnvironmentalLayers;

  /// Whether to show infrastructure layers section
  final bool showInfrastructureLayers;

  /// Panel layout mode
  final LayerControlPanelMode mode;

  /// Custom theme for the panel
  final LayerControlPanelTheme? theme;

  /// Maximum number of concurrent layers
  final int maxConcurrentLayers;

  const LayerControlPanel({
    super.key,
    required this.mapLayers,
    this.onLayerToggle,
    this.onLayerOpacityChanged,
    this.onLayerConfigChanged,
    this.mapController,
    this.showAdvancedControls = true,
    this.showEnvironmentalLayers = true,
    this.showInfrastructureLayers = true,
    this.mode = LayerControlPanelMode.compact,
    this.theme,
    this.maxConcurrentLayers = 8,
  });

  @override
  State<LayerControlPanel> createState() => _LayerControlPanelState();
}

class _LayerControlPanelState extends State<LayerControlPanel>
    with TickerProviderStateMixin {
  late final LayerDataService _layerDataService;
  late final TabController _tabController;

  // Layer state
  final Map<String, MapLayer> _activeLayers = {};
  final Map<String, EnvironmentalLayer> _environmentalLayers = {};
  final Map<String, InfrastructureLayer> _infrastructureLayers = {};

  // UI state
  bool _isLoading = false;
  bool _isExpanded = true;
  LayerControlSection _activeSection = LayerControlSection.active;

  @override
  void initState() {
    super.initState();
    const String methodName = 'initState';
    debugPrint('[$methodName] Initializing Enhanced LayerControlPanel');

    _layerDataService = LayerDataService();
    _tabController = TabController(length: 3, vsync: this);

    // Initialize with provided layers
    for (final layer in widget.mapLayers) {
      _activeLayers[layer.id] = layer;
    }

    // Load additional layer data
    _loadLayerData();
  }

  @override
  void dispose() {
    const String methodName = 'dispose';
    debugPrint('[$methodName] Disposing Enhanced LayerControlPanel');

    _layerDataService.dispose();
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const String methodName = 'build';
    debugPrint('[$methodName] Building Enhanced LayerControlPanel widget');

    final theme = widget.theme ?? LayerControlPanelTheme.defaultTheme(context);

    return Container(
      constraints: BoxConstraints(
        maxHeight: widget.mode == LayerControlPanelMode.expanded ? 600 : 400,
        maxWidth: 350,
      ),
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
            if (widget.mode == LayerControlPanelMode.tabbed)
              _buildTabBar(theme),
            Flexible(
              child: widget.mode == LayerControlPanelMode.tabbed
                  ? _buildTabbedContent(theme)
                  : _buildCompactContent(theme),
            ),
            if (widget.showAdvancedControls) _buildAdvancedControls(theme),
          ],
        ],
      ),
    );
  }

  /// Build panel header with title and controls
  Widget _buildHeader(LayerControlPanelTheme theme) {
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
              'Layer Controls',
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
  Widget _buildLayerCounter(LayerControlPanelTheme theme) {
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
  Widget _buildExpandToggle(LayerControlPanelTheme theme) {
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

  /// Build tab bar for organized sections
  Widget _buildTabBar(LayerControlPanelTheme theme) {
    return TabBar(
      controller: _tabController,
      indicatorColor: theme.primaryColor,
      labelColor: theme.primaryColor,
      unselectedLabelColor: theme.secondaryTextColor,
      labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
      tabs: const [
        Tab(text: 'Active', icon: Icon(Icons.visibility, size: 16)),
        Tab(text: 'Environment', icon: Icon(Icons.eco, size: 16)),
        Tab(text: 'Infrastructure', icon: Icon(Icons.location_city, size: 16)),
      ],
    );
  }

  /// Build tabbed content layout
  Widget _buildTabbedContent(LayerControlPanelTheme theme) {
    return TabBarView(
      controller: _tabController,
      children: [
        _buildActiveLayersSection(theme),
        _buildEnvironmentalLayersSection(theme),
        _buildInfrastructureLayersSection(theme),
      ],
    );
  }

  /// Build compact content layout
  Widget _buildCompactContent(LayerControlPanelTheme theme) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          _buildActiveLayersSection(theme),
          if (widget.showEnvironmentalLayers) ...[
            const SizedBox(height: 16),
            _buildEnvironmentalLayersSection(theme),
          ],
          if (widget.showInfrastructureLayers) ...[
            const SizedBox(height: 16),
            _buildInfrastructureLayersSection(theme),
          ],
        ],
      ),
    );
  }

  /// Build active layers section
  Widget _buildActiveLayersSection(LayerControlPanelTheme theme) {
    if (_activeLayers.isEmpty) {
      return _buildEmptyState(theme, 'No active layers');
    }

    final sortedLayers = _activeLayers.values.toList()
      ..sort((a, b) => b.zIndex.compareTo(a.zIndex));

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: sortedLayers.length,
      itemBuilder: (context, index) {
        final layer = sortedLayers[index];
        return _buildEnhancedLayerControl(layer, theme);
      },
    );
  }

  /// Build environmental layers section
  Widget _buildEnvironmentalLayersSection(LayerControlPanelTheme theme) {
    if (_isLoading) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader('Environmental Data', theme),
        const SizedBox(height: 8),
        _buildEnvironmentalLayersList(theme),
      ],
    );
  }

  /// Build infrastructure layers section
  Widget _buildInfrastructureLayersSection(LayerControlPanelTheme theme) {
    if (_isLoading) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader('Infrastructure', theme),
        const SizedBox(height: 8),
        _buildInfrastructureLayersList(theme),
      ],
    );
  }

  /// Build section header
  Widget _buildSectionHeader(String title, LayerControlPanelTheme theme) {
    return Text(
      title,
      style: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: theme.textColor,
      ),
    );
  }

  /// Build enhanced layer control with advanced features
  Widget _buildEnhancedLayerControl(MapLayer layer, LayerControlPanelTheme theme) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 1,
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
        subtitle: Text(
          layer.description,
          style: TextStyle(
            fontSize: 12,
            color: theme.secondaryTextColor,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Switch(
          value: layer.isVisible,
          onChanged: (value) => _toggleLayerVisibility(layer.id, value),
          activeColor: theme.primaryColor,
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
                  showAdvancedControls: widget.showAdvancedControls,
                  label: 'Opacity',
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
  Widget _buildEnvironmentalLayersList(LayerControlPanelTheme theme) {
    return Column(
      children: [
        _LayerControl(
          title: 'Temperature',
          subtitle: 'Environmental temperature data',
          color: AppColors.temperature,
          isEnabled: _isLayerActive('temperature'),
          onToggle: (enabled) => _toggleEnvironmentalLayer('temperature', enabled),
          onOpacityChanged: (opacity) => _updateLayerOpacity('temperature', opacity),
          showOpacityControl: widget.showAdvancedControls,
          theme: theme,
        ),
        const SizedBox(height: 8),
        _LayerControl(
          title: 'Rainfall',
          subtitle: 'Precipitation data',
          color: AppColors.rainfall,
          isEnabled: _isLayerActive('rainfall'),
          onToggle: (enabled) => _toggleEnvironmentalLayer('rainfall', enabled),
          onOpacityChanged: (opacity) => _updateLayerOpacity('rainfall', opacity),
          showOpacityControl: widget.showAdvancedControls,
          theme: theme,
        ),
        const SizedBox(height: 8),
        _LayerControl(
          title: 'Vegetation',
          subtitle: 'NDVI vegetation index',
          color: AppColors.vegetation,
          isEnabled: _isLayerActive('vegetation'),
          onToggle: (enabled) => _toggleEnvironmentalLayer('vegetation', enabled),
          onOpacityChanged: (opacity) => _updateLayerOpacity('vegetation', opacity),
          showOpacityControl: widget.showAdvancedControls,
          theme: theme,
        ),
        const SizedBox(height: 8),
        _LayerControl(
          title: 'Humidity',
          subtitle: 'Atmospheric humidity levels',
          color: Colors.lightBlue,
          isEnabled: _isLayerActive('humidity'),
          onToggle: (enabled) => _toggleEnvironmentalLayer('humidity', enabled),
          onOpacityChanged: (opacity) => _updateLayerOpacity('humidity', opacity),
          showOpacityControl: widget.showAdvancedControls,
          theme: theme,
        ),
      ],
    );
  }

  /// Build infrastructure layers list
  Widget _buildInfrastructureLayersList(LayerControlPanelTheme theme) {
    return Column(
      children: [
        _LayerControl(
          title: 'Healthcare Facilities',
          subtitle: 'Hospitals, clinics, health centers',
          color: Colors.red,
          isEnabled: _isLayerActive('healthcare'),
          onToggle: (enabled) => _toggleInfrastructureLayer('healthcare', enabled),
          onOpacityChanged: (opacity) => _updateLayerOpacity('healthcare', opacity),
          showOpacityControl: widget.showAdvancedControls,
          theme: theme,
        ),
        const SizedBox(height: 8),
        _LayerControl(
          title: 'Transportation',
          subtitle: 'Roads, highways, access routes',
          color: Colors.blue,
          isEnabled: _isLayerActive('transportation'),
          onToggle: (enabled) => _toggleInfrastructureLayer('transportation', enabled),
          onOpacityChanged: (opacity) => _updateLayerOpacity('transportation', opacity),
          showOpacityControl: widget.showAdvancedControls,
          theme: theme,
        ),
        const SizedBox(height: 8),
        _LayerControl(
          title: 'Population Centers',
          subtitle: 'Urban areas and settlements',
          color: Colors.orange,
          isEnabled: _isLayerActive('population'),
          onToggle: (enabled) => _toggleInfrastructureLayer('population', enabled),
          onOpacityChanged: (opacity) => _updateLayerOpacity('population', opacity),
          showOpacityControl: widget.showAdvancedControls,
          theme: theme,
        ),
      ],
    );
  }

  /// Build advanced controls section
  Widget _buildAdvancedControls(LayerControlPanelTheme theme) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border(
          top: BorderSide(color: theme.borderColor),
        ),
      ),
      child: Row(
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
              onPressed: _openLayerManager,
              icon: const Icon(Icons.settings, size: 16),
              label: const Text('Manage', style: TextStyle(fontSize: 12)),
              style: ElevatedButton.styleFrom(
                backgroundColor: theme.primaryColor,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 8),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Build empty state widget
  Widget _buildEmptyState(LayerControlPanelTheme theme, String message) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          Icon(
            Icons.layers_clear,
            size: 48,
            color: theme.disabledColor,
          ),
          const SizedBox(height: 8),
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

  Widget _buildLayerActions(MapLayer layer, LayerControlPanelTheme theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        TextButton.icon(
          onPressed: () => _showLayerInfo(layer),
          icon: const Icon(Icons.info_outline, size: 16),
          label: const Text('Info', style: TextStyle(fontSize: 12)),
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

  // Event handlers and state management

  Future<void> _loadLayerData() async {
    const String methodName = '_loadLayerData';
    debugPrint('[$methodName] Loading additional layer data');

    setState(() {
      _isLoading = true;
    });

    try {
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
    } catch (error) {
      debugPrint('[$methodName] Error loading layer data: $error');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _toggleLayerVisibility(String layerId, bool isVisible) {
    if (_activeLayers.containsKey(layerId)) {
      final layer = _activeLayers[layerId]!;
      _activeLayers[layerId] = layer.copyWith(isVisible: isVisible);
      widget.onLayerToggle?.call(layerId, isVisible);
      setState(() {});
    }
  }

  void _updateLayerOpacity(String layerId, double opacity) {
    if (_activeLayers.containsKey(layerId)) {
      final layer = _activeLayers[layerId]!;
      _activeLayers[layerId] = layer.copyWith(opacity: opacity);
      widget.onLayerOpacityChanged?.call(layerId, opacity);
      setState(() {});
    }
  }

  bool _isLayerActive(String layerId) {
    return _activeLayers.containsKey(layerId) && _activeLayers[layerId]!.isVisible;
  }

  void _toggleEnvironmentalLayer(String layerId, bool enabled) {
    if (enabled) {
      _addEnvironmentalLayer(layerId);
    } else {
      _removeLayer(layerId);
    }
  }

  void _toggleInfrastructureLayer(String layerId, bool enabled) {
    if (enabled) {
      _addInfrastructureLayer(layerId);
    } else {
      _removeLayer(layerId);
    }
  }

  void _addEnvironmentalLayer(String layerId) {
    // Create a basic environmental layer for demo
    final layer = MapLayer(
      id: layerId,
      name: _getEnvironmentalLayerName(layerId),
      description: _getEnvironmentalLayerDescription(layerId),
      type: LayerType.choropleth,
      isVisible: true,
      isToggleable: true,
      opacity: 0.7,
      zIndex: _activeLayers.length,
      colorScheme: _getDefaultColorScheme(),
      dataConfig: _getDefaultDataConfig(),
      styleConfig: _getDefaultStyleConfig(),
      legend: _getDefaultLegend(),
      requiresAuth: false,
      tags: ['environmental', layerId],
      metadata: {},
    );

    _activeLayers[layerId] = layer;
    widget.onLayerToggle?.call(layerId, true);
    setState(() {});
  }

  void _addInfrastructureLayer(String layerId) {
    // Create a basic infrastructure layer for demo
    final layer = MapLayer(
      id: layerId,
      name: _getInfrastructureLayerName(layerId),
      description: _getInfrastructureLayerDescription(layerId),
      type: LayerType.markers,
      isVisible: true,
      isToggleable: true,
      opacity: 0.8,
      zIndex: _activeLayers.length,
      colorScheme: _getDefaultColorScheme(),
      dataConfig: _getDefaultDataConfig(),
      styleConfig: _getDefaultStyleConfig(),
      legend: _getDefaultLegend(),
      requiresAuth: false,
      tags: ['infrastructure', layerId],
      metadata: {},
    );

    _activeLayers[layerId] = layer;
    widget.onLayerToggle?.call(layerId, true);
    setState(() {});
  }

  void _removeLayer(String layerId) {
    _activeLayers.remove(layerId);
    widget.onLayerToggle?.call(layerId, false);
    setState(() {});
  }

  void _clearAllLayers() {
    for (final layerId in _activeLayers.keys.toList()) {
      widget.onLayerToggle?.call(layerId, false);
    }
    _activeLayers.clear();
    setState(() {});
  }

  void _openLayerManager() {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        child: Container(
          width: 600,
          height: 500,
          child: MapLayerManager(
            mapController: widget.mapController,
            initialLayers: _activeLayers.values.toList(),
            onLayerVisibilityChanged: widget.onLayerToggle,
            onLayerOpacityChanged: widget.onLayerOpacityChanged,
          ),
        ),
      ),
    );
  }

  void _showLayerInfo(MapLayer layer) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(layer.name),
        content: Column(
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
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  // Helper methods

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
        return Icons.vector_graphics;
      case LayerType.realtime:
        return Icons.live_tv;
      case LayerType.userGenerated:
        return Icons.edit;
      case LayerType.annotations:
        return Icons.label;
    }
  }

  String _getEnvironmentalLayerName(String layerId) {
    switch (layerId) {
      case 'temperature':
        return 'Temperature';
      case 'rainfall':
        return 'Rainfall';
      case 'vegetation':
        return 'Vegetation';
      case 'humidity':
        return 'Humidity';
      default:
        return layerId.toUpperCase();
    }
  }

  String _getEnvironmentalLayerDescription(String layerId) {
    switch (layerId) {
      case 'temperature':
        return 'Environmental temperature data';
      case 'rainfall':
        return 'Precipitation data';
      case 'vegetation':
        return 'NDVI vegetation index';
      case 'humidity':
        return 'Atmospheric humidity levels';
      default:
        return 'Environmental data layer';
    }
  }

  String _getInfrastructureLayerName(String layerId) {
    switch (layerId) {
      case 'healthcare':
        return 'Healthcare Facilities';
      case 'transportation':
        return 'Transportation';
      case 'population':
        return 'Population Centers';
      default:
        return layerId.toUpperCase();
    }
  }

  String _getInfrastructureLayerDescription(String layerId) {
    switch (layerId) {
      case 'healthcare':
        return 'Hospitals, clinics, health centers';
      case 'transportation':
        return 'Roads, highways, access routes';
      case 'population':
        return 'Urban areas and settlements';
      default:
        return 'Infrastructure data layer';
    }
  }

  // Default configurations for layers
  LayerColorScheme _getDefaultColorScheme() {
    return const LayerColorScheme(
      primaryColor: Colors.blue,
      secondaryColor: Colors.red,
      gradient: [Colors.blue, Colors.green, Colors.yellow, Colors.orange, Colors.red],
      steps: 5,
      noDataColor: Colors.grey,
      borderColor: Colors.black,
      highlightColor: Colors.yellow,
    );
  }

  LayerDataConfig _getDefaultDataConfig() {
    return const LayerDataConfig(
      sourceType: DataSourceType.api,
      enableCaching: true,
      cacheDuration: 3600,
      dataFormat: 'geojson',
      fieldMappings: {},
      filters: [],
      aggregations: {},
    );
  }

  LayerStyleConfig _getDefaultStyleConfig() {
    return const LayerStyleConfig(
      strokeWidth: 1.0,
      markerSize: 8.0,
      fontSize: 12.0,
      fontWeight: FontWeight.normal,
      textColor: Colors.black,
    );
  }

  LayerLegend _getDefaultLegend() {
    return const LayerLegend(
      isVisible: true,
      title: 'Legend',
      items: [],
      position: LegendPosition.bottomRight,
      backgroundColor: Colors.white,
      textColor: Colors.black,
    );
  }
}

/// Individual layer control widget with enhanced features
class _LayerControl extends StatelessWidget {
  const _LayerControl({
    required this.title,
    required this.subtitle,
    required this.color,
    required this.isEnabled,
    required this.onToggle,
    this.onOpacityChanged,
    this.showOpacityControl = false,
    required this.theme,
  });

  final String title;
  final String subtitle;
  final Color color;
  final bool isEnabled;
  final ValueChanged<bool> onToggle;
  final ValueChanged<double>? onOpacityChanged;
  final bool showOpacityControl;
  final LayerControlPanelTheme theme;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 1,
      child: ExpansionTile(
        leading: Container(
          width: 16,
          height: 16,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
        title: Text(
          title,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: isEnabled ? theme.textColor : theme.disabledColor,
          ),
        ),
        subtitle: Text(
          subtitle,
          style: TextStyle(
            fontSize: 12,
            color: theme.secondaryTextColor,
          ),
        ),
        trailing: Switch(
          value: isEnabled,
          onChanged: onToggle,
          activeColor: theme.primaryColor,
        ),
        children: [
          if (showOpacityControl && onOpacityChanged != null)
            Padding(
              padding: const EdgeInsets.all(12),
              child: LayerOpacitySlider(
                layerId: title.toLowerCase().replaceAll(' ', '_'),
                initialOpacity: 0.7,
                onOpacityChanged: onOpacityChanged!,
                label: 'Opacity',
                showPercentageLabel: true,
              ),
            ),
        ],
      ),
    );
  }
}

// Supporting enums and classes

enum LayerControlPanelMode {
  compact,
  expanded,
  tabbed;
}

enum LayerControlSection {
  active,
  environmental,
  infrastructure,
  baseMaps;
}

class LayerControlPanelTheme {
  final Color backgroundColor;
  final Color headerColor;
  final Color primaryColor;
  final Color textColor;
  final Color secondaryTextColor;
  final Color iconColor;
  final Color borderColor;
  final Color disabledColor;

  const LayerControlPanelTheme({
    required this.backgroundColor,
    required this.headerColor,
    required this.primaryColor,
    required this.textColor,
    required this.secondaryTextColor,
    required this.iconColor,
    required this.borderColor,
    required this.disabledColor,
  });

  static LayerControlPanelTheme defaultTheme(BuildContext context) {
    final theme = Theme.of(context);
    return LayerControlPanelTheme(
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
