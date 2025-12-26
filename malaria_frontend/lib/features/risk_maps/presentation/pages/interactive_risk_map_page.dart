/// Interactive Risk Map Page with Choropleth Overlays
///
/// Main page for displaying interactive malaria risk maps with
/// choropleth overlays, temporal controls, layer management,
/// and real-time data updates.
///
/// Features:
/// - Choropleth risk overlays with color-coded regions
/// - Interactive map controls (zoom, pan, rotate)
/// - Temporal slider for historical/forecast data
/// - Layer management panel
/// - Region selection and details popup
/// - Risk legend display
/// - Export and sharing capabilities
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:logger/logger.dart';

import '../../domain/entities/risk_data.dart';
import '../../domain/entities/map_layer.dart';
import '../bloc/risk_map_bloc.dart';
import '../widgets/choropleth_overlay.dart';
import '../widgets/risk_legend_widget.dart';
import '../widgets/map_controls_widget.dart';
import '../widgets/region_info_popup.dart';
import '../widgets/temporal_risk_slider.dart';
import '../widgets/layer_control_panel.dart';

/// Interactive Risk Map Page widget
class InteractiveRiskMapPage extends StatefulWidget {
  /// Initial center coordinates
  final LatLng? initialCenter;

  /// Initial zoom level
  final double initialZoom;

  /// Whether to show controls
  final bool showControls;

  /// Whether to show legend
  final bool showLegend;

  /// Whether to enable temporal slider
  final bool enableTemporalSlider;

  const InteractiveRiskMapPage({
    super.key,
    this.initialCenter,
    this.initialZoom = 6.0,
    this.showControls = true,
    this.showLegend = true,
    this.enableTemporalSlider = true,
  });

  @override
  State<InteractiveRiskMapPage> createState() => _InteractiveRiskMapPageState();
}

class _InteractiveRiskMapPageState extends State<InteractiveRiskMapPage>
    with TickerProviderStateMixin {
  /// Logger instance
  final Logger _logger = Logger();

  /// Map controller
  late final MapController _mapController;

  /// Animation controller for transitions
  late final AnimationController _animationController;

  /// Currently selected region
  RiskData? _selectedRegion;

  /// Whether layer panel is expanded
  bool _isLayerPanelExpanded = false;

  /// Current temporal date for slider
  DateTime _currentTemporalDate = DateTime.now();

  /// Default center (Kenya)
  static const LatLng _defaultCenter = LatLng(-1.2921, 36.8219);

  @override
  void initState() {
    super.initState();
    const String methodName = 'initState';
    _logger.i('[$methodName] Initializing InteractiveRiskMapPage');

    _mapController = MapController();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    // Request initial data load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadInitialData();
    });
  }

  @override
  void dispose() {
    const String methodName = 'dispose';
    _logger.i('[$methodName] Disposing InteractiveRiskMapPage');

    _mapController.dispose();
    _animationController.dispose();
    super.dispose();
  }

  void _loadInitialData() {
    const String methodName = '_loadInitialData';
    _logger.i('[$methodName] Loading initial risk data');

    context.read<RiskMapBloc>().add(const LoadRiskDataEvent());
  }

  @override
  Widget build(BuildContext context) {
    const String methodName = 'build';
    _logger.d('[$methodName] Building InteractiveRiskMapPage');

    return BlocConsumer<RiskMapBloc, RiskMapState>(
      listener: _handleStateChanges,
      builder: (context, state) {
        return Scaffold(
          appBar: _buildAppBar(context, state),
          body: Stack(
            children: [
              // Main map
              _buildMap(context, state),

              // Loading overlay
              if (state is RiskMapLoading) _buildLoadingOverlay(),

              // Controls overlay
              if (widget.showControls) _buildControlsOverlay(context, state),

              // Legend
              if (widget.showLegend) _buildLegend(context, state),

              // Temporal slider
              if (widget.enableTemporalSlider)
                _buildTemporalSlider(context, state),

              // Layer panel
              if (_isLayerPanelExpanded) _buildLayerPanel(context, state),

              // Region info popup
              if (_selectedRegion != null)
                _buildRegionInfoPopup(context, _selectedRegion!),
            ],
          ),
        );
      },
    );
  }

  void _handleStateChanges(BuildContext context, RiskMapState state) {
    const String methodName = '_handleStateChanges';

    if (state is RiskMapError) {
      _logger.e('[$methodName] Risk map error: ${state.message}');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.message),
          backgroundColor: Colors.red,
          action: SnackBarAction(
            label: 'Retry',
            textColor: Colors.white,
            onPressed: _loadInitialData,
          ),
        ),
      );
    }
  }

  PreferredSizeWidget _buildAppBar(BuildContext context, RiskMapState state) {
    return AppBar(
      title: const Text('Malaria Risk Map'),
      backgroundColor: Theme.of(context).primaryColor,
      foregroundColor: Colors.white,
      elevation: 2,
      actions: [
        // Refresh button
        IconButton(
          icon: const Icon(Icons.refresh),
          tooltip: 'Refresh Data',
          onPressed: _loadInitialData,
        ),
        // Layer toggle
        IconButton(
          icon: Icon(
            _isLayerPanelExpanded ? Icons.layers : Icons.layers_outlined,
          ),
          tooltip: 'Toggle Layers',
          onPressed: () {
            setState(() {
              _isLayerPanelExpanded = !_isLayerPanelExpanded;
            });
          },
        ),
        // Export button
        IconButton(
          icon: const Icon(Icons.share),
          tooltip: 'Export Map',
          onPressed: _showExportOptions,
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildMap(BuildContext context, RiskMapState state) {
    final center = widget.initialCenter ?? _defaultCenter;
    final riskData = state is RiskMapLoaded ? state.riskData : <RiskData>[];

    return FlutterMap(
      mapController: _mapController,
      options: MapOptions(
        initialCenter: center,
        initialZoom: widget.initialZoom,
        minZoom: 3.0,
        maxZoom: 18.0,
        interactionOptions: const InteractionOptions(
          flags: InteractiveFlag.all,
        ),
        onTap: (tapPosition, latLng) => _handleMapTap(latLng, riskData),
        onPositionChanged: _handlePositionChanged,
      ),
      children: [
        // Base tile layer (OpenStreetMap)
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.malariaprediction.malaria_frontend',
          maxZoom: 19,
        ),

        // Choropleth overlay for risk data
        if (riskData.isNotEmpty)
          ChoroplethOverlay(
            riskData: riskData,
            opacity: 0.7,
            onRegionTap: _handleRegionTap,
            selectedRegionId: _selectedRegion?.id,
            colorScheme: LayerColorScheme.riskDefault(),
          ),

        // Markers layer for health facilities (if available)
        if (state is RiskMapLoaded && state.healthFacilities.isNotEmpty)
          MarkerLayer(
            markers: _buildHealthFacilityMarkers(state.healthFacilities),
          ),

        // Attribution
        const RichAttributionWidget(
          alignment: AttributionAlignment.bottomLeft,
          attributions: [
            TextSourceAttribution('OpenStreetMap contributors'),
          ],
        ),
      ],
    );
  }

  Widget _buildLoadingOverlay() {
    return Container(
      color: Colors.black.withValues(alpha: 0.3),
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: Colors.white),
            SizedBox(height: 16),
            Text(
              'Loading risk data...',
              style: TextStyle(color: Colors.white, fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildControlsOverlay(BuildContext context, RiskMapState state) {
    return Positioned(
      top: 16,
      right: 16,
      child: MapControlsWidget(
        mapController: _mapController,
        onZoomIn: () => _animateZoom(_mapController.camera.zoom + 1),
        onZoomOut: () => _animateZoom(_mapController.camera.zoom - 1),
        onResetView: _resetMapView,
        onLocate: _locateUser,
      ),
    );
  }

  Widget _buildLegend(BuildContext context, RiskMapState state) {
    return Positioned(
      bottom: widget.enableTemporalSlider ? 100 : 16,
      right: 16,
      child: RiskLegendWidget(
        isVisible: true,
        onToggle: () {
          // Toggle legend visibility if needed
        },
      ),
    );
  }

  Widget _buildTemporalSlider(BuildContext context, RiskMapState state) {
    return Positioned(
      bottom: 16,
      left: 16,
      right: 16,
      child: TemporalRiskSlider(
        currentDate: _currentTemporalDate,
        startDate: DateTime.now().subtract(const Duration(days: 365)),
        endDate: DateTime.now().add(const Duration(days: 90)),
        onDateChanged: _handleTemporalDateChanged,
      ),
    );
  }

  Widget _buildLayerPanel(BuildContext context, RiskMapState state) {
    return Positioned(
      top: 0,
      right: 0,
      bottom: 0,
      width: 320,
      child: Material(
        elevation: 8,
        child: LayerControlPanel(
          layers: state is RiskMapLoaded ? state.activeLayers : [],
          onLayerToggle: _handleLayerToggle,
          onLayerOpacityChange: _handleLayerOpacityChange,
          onClose: () {
            setState(() {
              _isLayerPanelExpanded = false;
            });
          },
        ),
      ),
    );
  }

  Widget _buildRegionInfoPopup(BuildContext context, RiskData region) {
    return Positioned(
      bottom: widget.enableTemporalSlider ? 120 : 36,
      left: 16,
      right: widget.showLegend ? 200 : 16,
      child: RegionInfoPopup(
        riskData: region,
        onClose: () {
          setState(() {
            _selectedRegion = null;
          });
        },
        onViewDetails: () => _navigateToRegionDetails(region),
      ),
    );
  }

  List<Marker> _buildHealthFacilityMarkers(List<HealthFacility> facilities) {
    return facilities.map((facility) {
      return Marker(
        point: facility.coordinates,
        width: 40,
        height: 40,
        child: GestureDetector(
          onTap: () => _handleFacilityTap(facility),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.blue, width: 2),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.2),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: const Icon(
              Icons.local_hospital,
              color: Colors.blue,
              size: 24,
            ),
          ),
        ),
      );
    }).toList();
  }

  void _handleMapTap(LatLng latLng, List<RiskData> riskData) {
    const String methodName = '_handleMapTap';
    _logger.d('[$methodName] Map tapped at: $latLng');

    // Check if tap is within any region
    for (final data in riskData) {
      if (data.boundary?.containsPoint(latLng) ?? false) {
        _handleRegionTap(data);
        return;
      }
    }

    // Clear selection if tapped outside any region
    setState(() {
      _selectedRegion = null;
    });
  }

  void _handleRegionTap(RiskData region) {
    const String methodName = '_handleRegionTap';
    _logger.i('[$methodName] Region tapped: ${region.regionName}');

    setState(() {
      _selectedRegion = region;
    });

    // Animate to region center
    _animateToLocation(region.coordinates, _mapController.camera.zoom);
  }

  void _handleFacilityTap(HealthFacility facility) {
    const String methodName = '_handleFacilityTap';
    _logger.i('[$methodName] Facility tapped: ${facility.name}');

    // Show facility details dialog
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(facility.name),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Type: ${facility.type}'),
            Text('Capacity: ${facility.capacity}'),
            if (facility.phone != null) Text('Phone: ${facility.phone}'),
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

  void _handlePositionChanged(MapCamera camera, bool hasGesture) {
    // Update visible region bounds for data filtering
    if (hasGesture) {
      final bounds = camera.visibleBounds;
      context.read<RiskMapBloc>().add(
            UpdateVisibleBoundsEvent(
              GeographicBounds(
                southWest: bounds.southWest,
                northEast: bounds.northEast,
              ),
            ),
          );
    }
  }

  void _handleTemporalDateChanged(DateTime date) {
    const String methodName = '_handleTemporalDateChanged';
    _logger.i('[$methodName] Temporal date changed to: $date');

    setState(() {
      _currentTemporalDate = date;
    });

    context.read<RiskMapBloc>().add(LoadTemporalRiskDataEvent(date: date));
  }

  void _handleLayerToggle(String layerId, bool isVisible) {
    const String methodName = '_handleLayerToggle';
    _logger.i('[$methodName] Layer $layerId visibility: $isVisible');

    context.read<RiskMapBloc>().add(
          ToggleLayerVisibilityEvent(layerId: layerId, isVisible: isVisible),
        );
  }

  void _handleLayerOpacityChange(String layerId, double opacity) {
    const String methodName = '_handleLayerOpacityChange';
    _logger.d('[$methodName] Layer $layerId opacity: $opacity');

    context.read<RiskMapBloc>().add(
          UpdateLayerOpacityEvent(layerId: layerId, opacity: opacity),
        );
  }

  void _animateZoom(double targetZoom) {
    const String methodName = '_animateZoom';
    _logger.d('[$methodName] Animating zoom to: $targetZoom');

    final clampedZoom = targetZoom.clamp(3.0, 18.0);
    _mapController.move(
      _mapController.camera.center,
      clampedZoom,
    );
  }

  void _animateToLocation(LatLng location, double zoom) {
    const String methodName = '_animateToLocation';
    _logger.d('[$methodName] Animating to location: $location');

    _mapController.move(location, zoom);
  }

  void _resetMapView() {
    const String methodName = '_resetMapView';
    _logger.i('[$methodName] Resetting map view');

    final center = widget.initialCenter ?? _defaultCenter;
    _mapController.move(center, widget.initialZoom);
  }

  Future<void> _locateUser() async {
    const String methodName = '_locateUser';
    _logger.i('[$methodName] Locating user');

    // Request location permission and get current location
    // This would integrate with geolocator package
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Location feature coming soon'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _navigateToRegionDetails(RiskData region) {
    const String methodName = '_navigateToRegionDetails';
    _logger.i('[$methodName] Navigating to region details: ${region.regionName}');

    // Navigate to region detail page
    Navigator.of(context).pushNamed(
      '/risk-maps/region/${region.id}',
      arguments: region,
    );
  }

  void _showExportOptions() {
    showModalBottomSheet(
      context: context,
      builder: (context) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.image),
            title: const Text('Export as Image'),
            onTap: () {
              Navigator.pop(context);
              _exportAsImage();
            },
          ),
          ListTile(
            leading: const Icon(Icons.picture_as_pdf),
            title: const Text('Export as PDF'),
            onTap: () {
              Navigator.pop(context);
              _exportAsPdf();
            },
          ),
          ListTile(
            leading: const Icon(Icons.share),
            title: const Text('Share Link'),
            onTap: () {
              Navigator.pop(context);
              _shareLink();
            },
          ),
        ],
      ),
    );
  }

  void _exportAsImage() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Export as image coming soon')),
    );
  }

  void _exportAsPdf() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Export as PDF coming soon')),
    );
  }

  void _shareLink() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Share link coming soon')),
    );
  }
}

/// Health facility data model
class HealthFacility {
  final String id;
  final String name;
  final String type;
  final LatLng coordinates;
  final int capacity;
  final String? phone;

  const HealthFacility({
    required this.id,
    required this.name,
    required this.type,
    required this.coordinates,
    required this.capacity,
    this.phone,
  });
}
