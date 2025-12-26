/// Risk Map BLoC for State Management
///
/// BLoC (Business Logic Component) for managing risk map state,
/// including data loading, layer management, region selection,
/// and temporal navigation.
///
/// Author: Claude AI Agent - Risk Map Implementation
/// Created: 2025-12-26
library;

import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:logger/logger.dart';

import '../../domain/entities/risk_data.dart';
import '../../domain/entities/map_layer.dart';
import '../pages/interactive_risk_map_page.dart';

// ============================================================================
// Events
// ============================================================================

/// Base class for risk map events
abstract class RiskMapEvent extends Equatable {
  const RiskMapEvent();

  @override
  List<Object?> get props => [];
}

/// Load risk data from API
class LoadRiskDataEvent extends RiskMapEvent {
  final String? regionFilter;
  final DateTime? dateFilter;

  const LoadRiskDataEvent({
    this.regionFilter,
    this.dateFilter,
  });

  @override
  List<Object?> get props => [regionFilter, dateFilter];
}

/// Load temporal risk data for a specific date
class LoadTemporalRiskDataEvent extends RiskMapEvent {
  final DateTime date;

  const LoadTemporalRiskDataEvent({required this.date});

  @override
  List<Object?> get props => [date];
}

/// Update visible map bounds for filtering
class UpdateVisibleBoundsEvent extends RiskMapEvent {
  final GeographicBounds bounds;

  const UpdateVisibleBoundsEvent(this.bounds);

  @override
  List<Object?> get props => [bounds];
}

/// Select a specific region
class SelectRegionEvent extends RiskMapEvent {
  final RiskData? region;

  const SelectRegionEvent({this.region});

  @override
  List<Object?> get props => [region];
}

/// Toggle layer visibility
class ToggleLayerVisibilityEvent extends RiskMapEvent {
  final String layerId;
  final bool isVisible;

  const ToggleLayerVisibilityEvent({
    required this.layerId,
    required this.isVisible,
  });

  @override
  List<Object?> get props => [layerId, isVisible];
}

/// Update layer opacity
class UpdateLayerOpacityEvent extends RiskMapEvent {
  final String layerId;
  final double opacity;

  const UpdateLayerOpacityEvent({
    required this.layerId,
    required this.opacity,
  });

  @override
  List<Object?> get props => [layerId, opacity];
}

/// Refresh risk data
class RefreshRiskDataEvent extends RiskMapEvent {
  const RefreshRiskDataEvent();
}

/// Clear all filters
class ClearFiltersEvent extends RiskMapEvent {
  const ClearFiltersEvent();
}

// ============================================================================
// States
// ============================================================================

/// Base class for risk map states
abstract class RiskMapState extends Equatable {
  const RiskMapState();

  @override
  List<Object?> get props => [];
}

/// Initial state
class RiskMapInitial extends RiskMapState {
  const RiskMapInitial();
}

/// Loading state
class RiskMapLoading extends RiskMapState {
  final String message;

  const RiskMapLoading({this.message = 'Loading...'});

  @override
  List<Object?> get props => [message];
}

/// Loaded state with data
class RiskMapLoaded extends RiskMapState {
  /// Risk data for all visible regions
  final List<RiskData> riskData;

  /// Currently visible bounds
  final GeographicBounds? visibleBounds;

  /// Currently selected region
  final RiskData? selectedRegion;

  /// Active map layers
  final List<MapLayer> activeLayers;

  /// Health facilities in visible area
  final List<HealthFacility> healthFacilities;

  /// Current temporal date
  final DateTime? temporalDate;

  /// Last update timestamp
  final DateTime lastUpdated;

  const RiskMapLoaded({
    required this.riskData,
    this.visibleBounds,
    this.selectedRegion,
    required this.activeLayers,
    this.healthFacilities = const [],
    this.temporalDate,
    required this.lastUpdated,
  });

  @override
  List<Object?> get props => [
        riskData,
        visibleBounds,
        selectedRegion,
        activeLayers,
        healthFacilities,
        temporalDate,
        lastUpdated,
      ];

  /// Create a copy with updated values
  RiskMapLoaded copyWith({
    List<RiskData>? riskData,
    GeographicBounds? visibleBounds,
    RiskData? selectedRegion,
    List<MapLayer>? activeLayers,
    List<HealthFacility>? healthFacilities,
    DateTime? temporalDate,
    DateTime? lastUpdated,
  }) {
    return RiskMapLoaded(
      riskData: riskData ?? this.riskData,
      visibleBounds: visibleBounds ?? this.visibleBounds,
      selectedRegion: selectedRegion ?? this.selectedRegion,
      activeLayers: activeLayers ?? this.activeLayers,
      healthFacilities: healthFacilities ?? this.healthFacilities,
      temporalDate: temporalDate ?? this.temporalDate,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }

  /// Get filtered risk data for visible bounds
  List<RiskData> get visibleRiskData {
    if (visibleBounds == null) return riskData;
    return riskData.where((data) => visibleBounds!.contains(data.coordinates)).toList();
  }

  /// Get risk statistics for visible regions
  Map<RiskLevel, int> get riskLevelCounts {
    final counts = <RiskLevel, int>{};
    for (final level in RiskLevel.values) {
      counts[level] = riskData.where((d) => d.riskLevel == level).length;
    }
    return counts;
  }
}

/// Error state
class RiskMapError extends RiskMapState {
  final String message;
  final Object? error;

  const RiskMapError({
    required this.message,
    this.error,
  });

  @override
  List<Object?> get props => [message, error];
}

// ============================================================================
// BLoC Implementation
// ============================================================================

/// Risk Map BLoC for state management
class RiskMapBloc extends Bloc<RiskMapEvent, RiskMapState> {
  /// Logger instance
  final Logger _logger;

  /// Cached risk data
  List<RiskData> _cachedRiskData = [];

  /// Active layers configuration
  final List<MapLayer> _activeLayers = [];

  RiskMapBloc({
    Logger? logger,
  })  : _logger = logger ?? Logger(),
        super(const RiskMapInitial()) {
    // Register event handlers
    on<LoadRiskDataEvent>(_onLoadRiskData);
    on<LoadTemporalRiskDataEvent>(_onLoadTemporalRiskData);
    on<UpdateVisibleBoundsEvent>(_onUpdateVisibleBounds);
    on<SelectRegionEvent>(_onSelectRegion);
    on<ToggleLayerVisibilityEvent>(_onToggleLayerVisibility);
    on<UpdateLayerOpacityEvent>(_onUpdateLayerOpacity);
    on<RefreshRiskDataEvent>(_onRefreshRiskData);
    on<ClearFiltersEvent>(_onClearFilters);

    // Initialize default layers
    _initializeDefaultLayers();
  }

  void _initializeDefaultLayers() {
    _activeLayers.addAll([
      MapLayer.riskChoropleth(id: 'risk_choropleth'),
      MapLayer.markers(id: 'health_facilities', name: 'Health Facilities'),
    ]);
  }

  /// Load risk data
  Future<void> _onLoadRiskData(
    LoadRiskDataEvent event,
    Emitter<RiskMapState> emit,
  ) async {
    const String methodName = '_onLoadRiskData';
    _logger.i('[$methodName] Loading risk data');

    emit(const RiskMapLoading(message: 'Loading risk data...'));

    try {
      // Simulate API call - replace with actual API integration
      await Future.delayed(const Duration(milliseconds: 500));

      final riskData = _generateSampleRiskData();
      _cachedRiskData = riskData;

      final healthFacilities = _generateSampleHealthFacilities();

      emit(RiskMapLoaded(
        riskData: riskData,
        activeLayers: List.from(_activeLayers),
        healthFacilities: healthFacilities,
        lastUpdated: DateTime.now(),
      ));

      _logger.i('[$methodName] Loaded ${riskData.length} risk regions');
    } catch (e, stackTrace) {
      _logger.e('[$methodName] Error loading risk data', error: e, stackTrace: stackTrace);
      emit(RiskMapError(message: 'Failed to load risk data: $e', error: e));
    }
  }

  /// Load temporal risk data
  Future<void> _onLoadTemporalRiskData(
    LoadTemporalRiskDataEvent event,
    Emitter<RiskMapState> emit,
  ) async {
    const String methodName = '_onLoadTemporalRiskData';
    _logger.i('[$methodName] Loading temporal risk data for ${event.date}');

    if (state is! RiskMapLoaded) return;
    final currentState = state as RiskMapLoaded;

    try {
      // Simulate temporal data loading
      await Future.delayed(const Duration(milliseconds: 300));

      // In a real implementation, this would fetch data for the specific date
      emit(currentState.copyWith(
        temporalDate: event.date,
        lastUpdated: DateTime.now(),
      ));
    } catch (e) {
      _logger.e('[$methodName] Error loading temporal data', error: e);
    }
  }

  /// Update visible bounds
  void _onUpdateVisibleBounds(
    UpdateVisibleBoundsEvent event,
    Emitter<RiskMapState> emit,
  ) {
    const String methodName = '_onUpdateVisibleBounds';
    _logger.d('[$methodName] Updating visible bounds');

    if (state is RiskMapLoaded) {
      final currentState = state as RiskMapLoaded;
      emit(currentState.copyWith(visibleBounds: event.bounds));
    }
  }

  /// Select a region
  void _onSelectRegion(
    SelectRegionEvent event,
    Emitter<RiskMapState> emit,
  ) {
    const String methodName = '_onSelectRegion';
    _logger.i('[$methodName] Selected region: ${event.region?.regionName}');

    if (state is RiskMapLoaded) {
      final currentState = state as RiskMapLoaded;
      emit(currentState.copyWith(selectedRegion: event.region));
    }
  }

  /// Toggle layer visibility
  void _onToggleLayerVisibility(
    ToggleLayerVisibilityEvent event,
    Emitter<RiskMapState> emit,
  ) {
    const String methodName = '_onToggleLayerVisibility';
    _logger.i('[$methodName] Toggling layer ${event.layerId} visibility: ${event.isVisible}');

    final index = _activeLayers.indexWhere((l) => l.id == event.layerId);
    if (index != -1) {
      _activeLayers[index] = _activeLayers[index].copyWith(isVisible: event.isVisible);

      if (state is RiskMapLoaded) {
        final currentState = state as RiskMapLoaded;
        emit(currentState.copyWith(activeLayers: List.from(_activeLayers)));
      }
    }
  }

  /// Update layer opacity
  void _onUpdateLayerOpacity(
    UpdateLayerOpacityEvent event,
    Emitter<RiskMapState> emit,
  ) {
    const String methodName = '_onUpdateLayerOpacity';
    _logger.d('[$methodName] Updating layer ${event.layerId} opacity: ${event.opacity}');

    final index = _activeLayers.indexWhere((l) => l.id == event.layerId);
    if (index != -1) {
      _activeLayers[index] = _activeLayers[index].copyWith(opacity: event.opacity);

      if (state is RiskMapLoaded) {
        final currentState = state as RiskMapLoaded;
        emit(currentState.copyWith(activeLayers: List.from(_activeLayers)));
      }
    }
  }

  /// Refresh risk data
  Future<void> _onRefreshRiskData(
    RefreshRiskDataEvent event,
    Emitter<RiskMapState> emit,
  ) async {
    const String methodName = '_onRefreshRiskData';
    _logger.i('[$methodName] Refreshing risk data');

    add(const LoadRiskDataEvent());
  }

  /// Clear all filters
  void _onClearFilters(
    ClearFiltersEvent event,
    Emitter<RiskMapState> emit,
  ) {
    const String methodName = '_onClearFilters';
    _logger.i('[$methodName] Clearing filters');

    if (state is RiskMapLoaded) {
      final currentState = state as RiskMapLoaded;
      emit(RiskMapLoaded(
        riskData: _cachedRiskData,
        activeLayers: List.from(_activeLayers),
        healthFacilities: currentState.healthFacilities,
        lastUpdated: DateTime.now(),
      ));
    }
  }

  // ============================================================================
  // Sample Data Generation (Replace with API calls)
  // ============================================================================

  List<RiskData> _generateSampleRiskData() {
    // Sample Kenyan constituencies
    return [
      _createRiskData('nairobi', 'Nairobi Central', -1.2864, 36.8172, 0.35),
      _createRiskData('mombasa', 'Mombasa', -4.0435, 39.6682, 0.72),
      _createRiskData('kisumu', 'Kisumu', -0.0917, 34.7680, 0.85),
      _createRiskData('nakuru', 'Nakuru', -0.3031, 36.0800, 0.45),
      _createRiskData('eldoret', 'Eldoret', 0.5143, 35.2698, 0.28),
      _createRiskData('malindi', 'Malindi', -3.2138, 40.1169, 0.78),
      _createRiskData('kilifi', 'Kilifi', -3.6305, 39.8499, 0.82),
      _createRiskData('kakamega', 'Kakamega', 0.2827, 34.7519, 0.68),
      _createRiskData('bungoma', 'Bungoma', 0.5635, 34.5606, 0.55),
      _createRiskData('migori', 'Migori', -1.0634, 34.4731, 0.91),
      _createRiskData('homabay', 'Homa Bay', -0.5273, 34.4571, 0.88),
      _createRiskData('siaya', 'Siaya', -0.0613, 34.2422, 0.79),
      _createRiskData('kwale', 'Kwale', -4.1756, 39.4521, 0.65),
      _createRiskData('tanariver', 'Tana River', -1.5000, 40.0000, 0.58),
      _createRiskData('garissa', 'Garissa', -0.4536, 39.6401, 0.42),
    ];
  }

  RiskData _createRiskData(String id, String name, double lat, double lng, double riskScore) {
    return RiskData(
      id: id,
      region: id,
      regionName: name,
      administrativeLevel: 'constituency',
      coordinates: LatLng(lat, lng),
      riskScore: riskScore,
      riskLevel: RiskLevel.fromScore(riskScore),
      confidence: 0.85,
      environmentalFactors: EnvironmentalFactors(
        temperature: 25.0 + (riskScore * 5),
        humidity: 60.0 + (riskScore * 20),
        rainfall: 50.0 + (riskScore * 100),
        vegetationIndex: 0.3 + (riskScore * 0.4),
      ),
      predictedCases: (riskScore * 1000).toInt(),
      predictionDate: DateTime.now(),
      lastUpdated: DateTime.now(),
      modelVersion: 'ensemble-v1.2.0',
    );
  }

  List<HealthFacility> _generateSampleHealthFacilities() {
    return [
      const HealthFacility(
        id: 'knh',
        name: 'Kenyatta National Hospital',
        type: 'National Referral',
        coordinates: LatLng(-1.3000, 36.8067),
        capacity: 2000,
        phone: '+254 20 2726300',
      ),
      const HealthFacility(
        id: 'mtrh',
        name: 'Moi Teaching & Referral Hospital',
        type: 'Teaching Hospital',
        coordinates: LatLng(0.5167, 35.2833),
        capacity: 800,
        phone: '+254 53 2033471',
      ),
      const HealthFacility(
        id: 'cpgh',
        name: 'Coast Provincial General Hospital',
        type: 'Provincial Hospital',
        coordinates: LatLng(-4.0500, 39.6667),
        capacity: 600,
      ),
    ];
  }
}
