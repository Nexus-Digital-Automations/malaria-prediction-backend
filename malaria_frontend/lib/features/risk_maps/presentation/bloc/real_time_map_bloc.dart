/// Real-time Map BLoC for Live Risk Data State Management
///
/// This BLoC manages the state for real-time malaria risk map visualization,
/// handling WebSocket updates, temporal navigation, conflict resolution,
/// and performance optimization for live data streams.
///
/// Features:
/// - Real-time WebSocket data stream management
/// - Temporal navigation and data interpolation
/// - Conflict resolution for concurrent updates
/// - Performance-optimized state updates
/// - Geographic subscription management
/// - Animation state coordination
/// - Error handling and recovery
/// - Connection health monitoring
/// - Data caching and persistence
///
/// Author: Claude AI Agent - Real-time Visualization System
/// Created: 2025-09-19
library;

import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:latlong2/latlong.dart';
import 'package:equatable/equatable.dart';
import 'package:logger/logger.dart';

import '../../data/services/real_time_map_service.dart';
import '../../domain/entities/real_time_update.dart';
import '../../domain/entities/risk_data.dart';
import '../../domain/entities/temporal_risk_data.dart';

/// Events for real-time map BLoC
abstract class RealTimeMapEvent extends Equatable {
  const RealTimeMapEvent();

  @override
  List<Object?> get props => [];
}

/// Initialize real-time connection
class InitializeRealTimeConnection extends RealTimeMapEvent {
  const InitializeRealTimeConnection();
}

/// Connect to real-time updates
class ConnectToRealTimeUpdates extends RealTimeMapEvent {
  const ConnectToRealTimeUpdates();
}

/// Disconnect from real-time updates
class DisconnectFromRealTimeUpdates extends RealTimeMapEvent {
  const DisconnectFromRealTimeUpdates();
}

/// Subscribe to geographic region
class SubscribeToGeographicRegion extends RealTimeMapEvent {
  final String subscriptionId;
  final LatLng center;
  final double radiusKm;
  final int? zoomLevel;
  final bool includePredictions;

  const SubscribeToGeographicRegion({
    required this.subscriptionId,
    required this.center,
    required this.radiusKm,
    this.zoomLevel,
    this.includePredictions = true,
  });

  @override
  List<Object?> get props => [subscriptionId, center, radiusKm, zoomLevel, includePredictions];
}

/// Unsubscribe from geographic region
class UnsubscribeFromGeographicRegion extends RealTimeMapEvent {
  final String subscriptionId;

  const UnsubscribeFromGeographicRegion({required this.subscriptionId});

  @override
  List<Object?> get props => [subscriptionId];
}

/// Real-time data update received
class RealTimeDataUpdateReceived extends RealTimeMapEvent {
  final RealTimeUpdate update;

  const RealTimeDataUpdateReceived({required this.update});

  @override
  List<Object?> get props => [update];
}

/// Batch real-time updates received
class BatchRealTimeUpdatesReceived extends RealTimeMapEvent {
  final List<RealTimeUpdate> updates;

  const BatchRealTimeUpdatesReceived({required this.updates});

  @override
  List<Object?> get props => [updates];
}

/// Temporal data update received
class TemporalDataUpdateReceived extends RealTimeMapEvent {
  final TemporalRiskData temporalData;

  const TemporalDataUpdateReceived({required this.temporalData});

  @override
  List<Object?> get props => [temporalData];
}

/// Connection status changed
class ConnectionStatusChanged extends RealTimeMapEvent {
  final RealTimeConnectionStatus status;

  const ConnectionStatusChanged({required this.status});

  @override
  List<Object?> get props => [status];
}

/// Performance metrics updated
class PerformanceMetricsUpdated extends RealTimeMapEvent {
  final RealTimeMetrics metrics;

  const PerformanceMetricsUpdated({required this.metrics});

  @override
  List<Object?> get props => [metrics];
}

/// Conflict notification received
class ConflictNotificationReceived extends RealTimeMapEvent {
  final ConflictNotification conflict;

  const ConflictNotificationReceived({required this.conflict});

  @override
  List<Object?> get props => [conflict];
}

/// Request data refresh
class RequestDataRefresh extends RealTimeMapEvent {
  final String? specificRegion;

  const RequestDataRefresh({this.specificRegion});

  @override
  List<Object?> get props => [specificRegion];
}

/// Change temporal navigation time
class ChangeTemporalTime extends RealTimeMapEvent {
  final DateTime selectedTime;

  const ChangeTemporalTime({required this.selectedTime});

  @override
  List<Object?> get props => [selectedTime];
}

/// Update visible map bounds
class UpdateVisibleMapBounds extends RealTimeMapEvent {
  final GeographicBounds bounds;
  final double zoomLevel;

  const UpdateVisibleMapBounds({
    required this.bounds,
    required this.zoomLevel,
  });

  @override
  List<Object?> get props => [bounds, zoomLevel];
}

/// Set conflict resolution strategy
class SetConflictResolutionStrategy extends RealTimeMapEvent {
  final ConflictResolutionStrategy strategy;

  const SetConflictResolutionStrategy({required this.strategy});

  @override
  List<Object?> get props => [strategy];
}

/// Resolve conflict manually
class ResolveConflictManually extends RealTimeMapEvent {
  final String conflictId;
  final RealTimeUpdate selectedUpdate;

  const ResolveConflictManually({
    required this.conflictId,
    required this.selectedUpdate,
  });

  @override
  List<Object?> get props => [conflictId, selectedUpdate];
}

/// Pause/resume real-time updates
class ToggleRealTimeUpdates extends RealTimeMapEvent {
  final bool pause;

  const ToggleRealTimeUpdates({required this.pause});

  @override
  List<Object?> get props => [pause];
}

/// Force reconnection
class ForceReconnection extends RealTimeMapEvent {
  const ForceReconnection();
}

/// States for real-time map BLoC
abstract class RealTimeMapState extends Equatable {
  const RealTimeMapState();

  @override
  List<Object?> get props => [];
}

/// Initial state
class RealTimeMapInitial extends RealTimeMapState {
  const RealTimeMapInitial();
}

/// Loading state
class RealTimeMapLoading extends RealTimeMapState {
  final String message;

  const RealTimeMapLoading({this.message = 'Loading...'});

  @override
  List<Object?> get props => [message];
}

/// Connected and operational state
class RealTimeMapConnected extends RealTimeMapState {
  /// Current connection status
  final RealTimeConnectionStatus connectionStatus;

  /// Current risk data by region ID
  final Map<String, RiskData> currentRiskData;

  /// Temporal risk data by region ID
  final Map<String, TemporalRiskData> temporalRiskData;

  /// Active geographic subscriptions
  final List<GeographicSubscription> activeSubscriptions;

  /// Current visible map bounds
  final GeographicBounds? visibleBounds;

  /// Current zoom level
  final double? zoomLevel;

  /// Selected temporal time
  final DateTime? selectedTemporalTime;

  /// Current performance metrics
  final RealTimeMetrics? performanceMetrics;

  /// Active conflicts awaiting resolution
  final List<ConflictNotification> activeConflicts;

  /// Current conflict resolution strategy
  final ConflictResolutionStrategy conflictStrategy;

  /// Whether real-time updates are paused
  final bool updatesPaused;

  /// Data refresh status
  final bool isRefreshing;

  /// Last update timestamp
  final DateTime lastUpdated;

  const RealTimeMapConnected({
    required this.connectionStatus,
    required this.currentRiskData,
    required this.temporalRiskData,
    required this.activeSubscriptions,
    this.visibleBounds,
    this.zoomLevel,
    this.selectedTemporalTime,
    this.performanceMetrics,
    required this.activeConflicts,
    required this.conflictStrategy,
    this.updatesPaused = false,
    this.isRefreshing = false,
    required this.lastUpdated,
  });

  @override
  List<Object?> get props => [
        connectionStatus,
        currentRiskData,
        temporalRiskData,
        activeSubscriptions,
        visibleBounds,
        zoomLevel,
        selectedTemporalTime,
        performanceMetrics,
        activeConflicts,
        conflictStrategy,
        updatesPaused,
        isRefreshing,
        lastUpdated,
      ];

  /// Copy with updated fields
  RealTimeMapConnected copyWith({
    RealTimeConnectionStatus? connectionStatus,
    Map<String, RiskData>? currentRiskData,
    Map<String, TemporalRiskData>? temporalRiskData,
    List<GeographicSubscription>? activeSubscriptions,
    GeographicBounds? visibleBounds,
    double? zoomLevel,
    DateTime? selectedTemporalTime,
    RealTimeMetrics? performanceMetrics,
    List<ConflictNotification>? activeConflicts,
    ConflictResolutionStrategy? conflictStrategy,
    bool? updatesPaused,
    bool? isRefreshing,
    DateTime? lastUpdated,
  }) {
    return RealTimeMapConnected(
      connectionStatus: connectionStatus ?? this.connectionStatus,
      currentRiskData: currentRiskData ?? this.currentRiskData,
      temporalRiskData: temporalRiskData ?? this.temporalRiskData,
      activeSubscriptions: activeSubscriptions ?? this.activeSubscriptions,
      visibleBounds: visibleBounds ?? this.visibleBounds,
      zoomLevel: zoomLevel ?? this.zoomLevel,
      selectedTemporalTime: selectedTemporalTime ?? this.selectedTemporalTime,
      performanceMetrics: performanceMetrics ?? this.performanceMetrics,
      activeConflicts: activeConflicts ?? this.activeConflicts,
      conflictStrategy: conflictStrategy ?? this.conflictStrategy,
      updatesPaused: updatesPaused ?? this.updatesPaused,
      isRefreshing: isRefreshing ?? this.isRefreshing,
      lastUpdated: lastUpdated ?? this.lastUpdated,
    );
  }

  /// Get risk data for visible bounds
  List<RiskData> get visibleRiskData {
    if (visibleBounds == null) return currentRiskData.values.toList();

    return currentRiskData.values.where((data) {
      return visibleBounds!.contains(data.coordinates);
    }).toList();
  }

  /// Get risk data for selected temporal time
  Map<String, double> get temporalRiskScores {
    if (selectedTemporalTime == null) {
      return currentRiskData.map((key, value) => MapEntry(key, value.riskScore));
    }

    return temporalRiskData.map((key, temporal) {
      final interpolatedRisk = temporal.interpolateRiskScore(selectedTemporalTime!);
      return MapEntry(key, interpolatedRisk);
    });
  }

  /// Check if connected and operational
  bool get isOperational {
    return connectionStatus == RealTimeConnectionStatus.connected && !updatesPaused;
  }

  /// Get connection health score (0.0 to 1.0)
  double get connectionHealth {
    switch (connectionStatus) {
      case RealTimeConnectionStatus.connected:
        return 1.0;
      case RealTimeConnectionStatus.connecting:
      case RealTimeConnectionStatus.reconnecting:
        return 0.5;
      case RealTimeConnectionStatus.paused:
        return 0.7;
      case RealTimeConnectionStatus.disconnected:
      case RealTimeConnectionStatus.error:
        return 0.0;
    }
  }
}

/// Error state
class RealTimeMapError extends RealTimeMapState {
  final String message;
  final Object? error;
  final StackTrace? stackTrace;

  const RealTimeMapError({
    required this.message,
    this.error,
    this.stackTrace,
  });

  @override
  List<Object?> get props => [message, error, stackTrace];
}

/// Disconnected state
class RealTimeMapDisconnected extends RealTimeMapState {
  final String reason;

  const RealTimeMapDisconnected({this.reason = 'Disconnected'});

  @override
  List<Object?> get props => [reason];
}

/// Real-time map BLoC implementation
class RealTimeMapBloc extends Bloc<RealTimeMapEvent, RealTimeMapState> {
  /// Real-time map service
  final RealTimeMapService _realTimeService;

  /// Logger for debugging
  final Logger _logger;

  /// Stream subscriptions
  final List<StreamSubscription> _subscriptions = [];

  /// Current risk data cache
  final Map<String, RiskData> _riskDataCache = {};

  /// Temporal risk data cache
  final Map<String, TemporalRiskData> _temporalDataCache = {};

  /// Active subscriptions
  final List<GeographicSubscription> _activeSubscriptions = [];

  /// Active conflicts
  final List<ConflictNotification> _activeConflicts = [];

  /// Current conflict resolution strategy
  ConflictResolutionStrategy _conflictStrategy = ConflictResolutionStrategy.latestWins;

  RealTimeMapBloc({
    required RealTimeMapService realTimeService,
    required Logger logger,
  })  : _realTimeService = realTimeService,
        _logger = logger,
        super(const RealTimeMapInitial()) {

    // Register event handlers
    on<InitializeRealTimeConnection>(_onInitializeRealTimeConnection);
    on<ConnectToRealTimeUpdates>(_onConnectToRealTimeUpdates);
    on<DisconnectFromRealTimeUpdates>(_onDisconnectFromRealTimeUpdates);
    on<SubscribeToGeographicRegion>(_onSubscribeToGeographicRegion);
    on<UnsubscribeFromGeographicRegion>(_onUnsubscribeFromGeographicRegion);
    on<RealTimeDataUpdateReceived>(_onRealTimeDataUpdateReceived);
    on<BatchRealTimeUpdatesReceived>(_onBatchRealTimeUpdatesReceived);
    on<TemporalDataUpdateReceived>(_onTemporalDataUpdateReceived);
    on<ConnectionStatusChanged>(_onConnectionStatusChanged);
    on<PerformanceMetricsUpdated>(_onPerformanceMetricsUpdated);
    on<ConflictNotificationReceived>(_onConflictNotificationReceived);
    on<RequestDataRefresh>(_onRequestDataRefresh);
    on<ChangeTemporalTime>(_onChangeTemporalTime);
    on<UpdateVisibleMapBounds>(_onUpdateVisibleMapBounds);
    on<SetConflictResolutionStrategy>(_onSetConflictResolutionStrategy);
    on<ResolveConflictManually>(_onResolveConflictManually);
    on<ToggleRealTimeUpdates>(_onToggleRealTimeUpdates);
    on<ForceReconnection>(_onForceReconnection);
  }

  @override
  Future<void> close() async {
    // Cancel all subscriptions
    for (final subscription in _subscriptions) {
      await subscription.cancel();
    }
    _subscriptions.clear();

    // Dispose service
    await _realTimeService.dispose();

    await super.close();
  }

  /// Initialize real-time connection
  Future<void> _onInitializeRealTimeConnection(
    InitializeRealTimeConnection event,
    Emitter<RealTimeMapState> emit,
  ) async {
    try {
      emit(const RealTimeMapLoading(message: 'Initializing real-time connection...'));

      // Set up service subscriptions
      _setupServiceSubscriptions();

      emit(RealTimeMapConnected(
        connectionStatus: _realTimeService.currentStatus,
        currentRiskData: Map.from(_riskDataCache),
        temporalRiskData: Map.from(_temporalDataCache),
        activeSubscriptions: List.from(_activeSubscriptions),
        activeConflicts: List.from(_activeConflicts),
        conflictStrategy: _conflictStrategy,
        lastUpdated: DateTime.now(),
      ));

      _logger.i('Real-time map BLoC initialized');
    } catch (e, stackTrace) {
      _logger.e('Failed to initialize real-time connection', error: e, stackTrace: stackTrace);
      emit(RealTimeMapError(
        message: 'Failed to initialize real-time connection',
        error: e,
        stackTrace: stackTrace,
      ));
    }
  }

  /// Connect to real-time updates
  Future<void> _onConnectToRealTimeUpdates(
    ConnectToRealTimeUpdates event,
    Emitter<RealTimeMapState> emit,
  ) async {
    try {
      emit(const RealTimeMapLoading(message: 'Connecting to real-time updates...'));

      await _realTimeService.connect();

      _logger.i('Connected to real-time updates');
    } catch (e, stackTrace) {
      _logger.e('Failed to connect to real-time updates', error: e, stackTrace: stackTrace);
      emit(RealTimeMapError(
        message: 'Failed to connect to real-time updates',
        error: e,
        stackTrace: stackTrace,
      ));
    }
  }

  /// Disconnect from real-time updates
  Future<void> _onDisconnectFromRealTimeUpdates(
    DisconnectFromRealTimeUpdates event,
    Emitter<RealTimeMapState> emit,
  ) async {
    try {
      await _realTimeService.disconnect();
      emit(const RealTimeMapDisconnected(reason: 'User disconnected'));
      _logger.i('Disconnected from real-time updates');
    } catch (e, stackTrace) {
      _logger.e('Error during disconnect', error: e, stackTrace: stackTrace);
      emit(RealTimeMapError(
        message: 'Error during disconnect',
        error: e,
        stackTrace: stackTrace,
      ));
    }
  }

  /// Subscribe to geographic region
  Future<void> _onSubscribeToGeographicRegion(
    SubscribeToGeographicRegion event,
    Emitter<RealTimeMapState> emit,
  ) async {
    try {
      await _realTimeService.subscribeToRegion(
        subscriptionId: event.subscriptionId,
        center: event.center,
        radiusKm: event.radiusKm,
        zoomLevel: event.zoomLevel,
        includePredictions: event.includePredictions,
      );

      final subscription = GeographicSubscription(
        id: event.subscriptionId,
        center: event.center,
        radiusKm: event.radiusKm,
        zoomLevel: event.zoomLevel,
        includePredictions: event.includePredictions,
      );

      _activeSubscriptions.add(subscription);

      if (state is RealTimeMapConnected) {
        final currentState = state as RealTimeMapConnected;
        emit(currentState.copyWith(
          activeSubscriptions: List.from(_activeSubscriptions),
          lastUpdated: DateTime.now(),
        ));
      }

      _logger.i('Subscribed to geographic region: ${event.subscriptionId}');
    } catch (e, stackTrace) {
      _logger.e('Failed to subscribe to region', error: e, stackTrace: stackTrace);
      emit(RealTimeMapError(
        message: 'Failed to subscribe to region',
        error: e,
        stackTrace: stackTrace,
      ));
    }
  }

  /// Unsubscribe from geographic region
  Future<void> _onUnsubscribeFromGeographicRegion(
    UnsubscribeFromGeographicRegion event,
    Emitter<RealTimeMapState> emit,
  ) async {
    try {
      await _realTimeService.unsubscribeFromRegion(event.subscriptionId);

      _activeSubscriptions.removeWhere((sub) => sub.id == event.subscriptionId);

      if (state is RealTimeMapConnected) {
        final currentState = state as RealTimeMapConnected;
        emit(currentState.copyWith(
          activeSubscriptions: List.from(_activeSubscriptions),
          lastUpdated: DateTime.now(),
        ));
      }

      _logger.i('Unsubscribed from geographic region: ${event.subscriptionId}');
    } catch (e, stackTrace) {
      _logger.e('Failed to unsubscribe from region', error: e, stackTrace: stackTrace);
    }
  }

  /// Handle real-time data update
  void _onRealTimeDataUpdateReceived(
    RealTimeDataUpdateReceived event,
    Emitter<RealTimeMapState> emit,
  ) {
    final update = event.update;

    // Process the update based on type
    switch (update.updateType) {
      case RealTimeUpdateType.create:
      case RealTimeUpdateType.update:
        _processDataUpdate(update);
        break;
      case RealTimeUpdateType.delete:
        _processDataDeletion(update);
        break;
      case RealTimeUpdateType.batch:
        _processBatchUpdate(update);
        break;
      default:
        break;
    }

    // Emit updated state
    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        currentRiskData: Map.from(_riskDataCache),
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle batch real-time updates
  void _onBatchRealTimeUpdatesReceived(
    BatchRealTimeUpdatesReceived event,
    Emitter<RealTimeMapState> emit,
  ) {
    for (final update in event.updates) {
      add(RealTimeDataUpdateReceived(update: update));
    }
  }

  /// Handle temporal data update
  void _onTemporalDataUpdateReceived(
    TemporalDataUpdateReceived event,
    Emitter<RealTimeMapState> emit,
  ) {
    final temporalData = event.temporalData;
    _temporalDataCache[temporalData.regionId] = temporalData;

    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        temporalRiskData: Map.from(_temporalDataCache),
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle connection status change
  void _onConnectionStatusChanged(
    ConnectionStatusChanged event,
    Emitter<RealTimeMapState> emit,
  ) {
    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        connectionStatus: event.status,
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle performance metrics update
  void _onPerformanceMetricsUpdated(
    PerformanceMetricsUpdated event,
    Emitter<RealTimeMapState> emit,
  ) {
    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        performanceMetrics: event.metrics,
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle conflict notification
  void _onConflictNotificationReceived(
    ConflictNotificationReceived event,
    Emitter<RealTimeMapState> emit,
  ) {
    _activeConflicts.add(event.conflict);

    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        activeConflicts: List.from(_activeConflicts),
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle data refresh request
  Future<void> _onRequestDataRefresh(
    RequestDataRefresh event,
    Emitter<RealTimeMapState> emit,
  ) async {
    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(isRefreshing: true));

      try {
        await _realTimeService.requestDataRefresh(specificRegion: event.specificRegion);
        _logger.i('Data refresh requested');
      } catch (e) {
        _logger.e('Failed to request data refresh', error: e);
      } finally {
        emit(currentState.copyWith(isRefreshing: false));
      }
    }
  }

  /// Handle temporal time change
  void _onChangeTemporalTime(
    ChangeTemporalTime event,
    Emitter<RealTimeMapState> emit,
  ) {
    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        selectedTemporalTime: event.selectedTime,
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle visible map bounds update
  void _onUpdateVisibleMapBounds(
    UpdateVisibleMapBounds event,
    Emitter<RealTimeMapState> emit,
  ) {
    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        visibleBounds: event.bounds,
        zoomLevel: event.zoomLevel,
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle conflict resolution strategy change
  void _onSetConflictResolutionStrategy(
    SetConflictResolutionStrategy event,
    Emitter<RealTimeMapState> emit,
  ) {
    _conflictStrategy = event.strategy;
    _realTimeService.setConflictResolutionStrategy(event.strategy);

    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        conflictStrategy: event.strategy,
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle manual conflict resolution
  void _onResolveConflictManually(
    ResolveConflictManually event,
    Emitter<RealTimeMapState> emit,
  ) {
    // Remove resolved conflict
    _activeConflicts.removeWhere((conflict) => conflict.conflictId == event.conflictId);

    // Apply the selected update
    _processDataUpdate(event.selectedUpdate);

    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        activeConflicts: List.from(_activeConflicts),
        currentRiskData: Map.from(_riskDataCache),
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle pause/resume updates
  void _onToggleRealTimeUpdates(
    ToggleRealTimeUpdates event,
    Emitter<RealTimeMapState> emit,
  ) {
    if (event.pause) {
      _realTimeService.pauseUpdates();
    } else {
      _realTimeService.resumeUpdates();
    }

    if (state is RealTimeMapConnected) {
      final currentState = state as RealTimeMapConnected;
      emit(currentState.copyWith(
        updatesPaused: event.pause,
        lastUpdated: DateTime.now(),
      ));
    }
  }

  /// Handle force reconnection
  Future<void> _onForceReconnection(
    ForceReconnection event,
    Emitter<RealTimeMapState> emit,
  ) async {
    try {
      emit(const RealTimeMapLoading(message: 'Reconnecting...'));
      await _realTimeService.forceReconnect();
      _logger.i('Forced reconnection completed');
    } catch (e, stackTrace) {
      _logger.e('Force reconnection failed', error: e, stackTrace: stackTrace);
      emit(RealTimeMapError(
        message: 'Force reconnection failed',
        error: e,
        stackTrace: stackTrace,
      ));
    }
  }

  /// Setup service subscriptions
  void _setupServiceSubscriptions() {
    // Connection status updates
    _subscriptions.add(
      _realTimeService.connectionStatus.listen(
        (status) => add(ConnectionStatusChanged(status: status)),
      ),
    );

    // Real-time updates
    _subscriptions.add(
      _realTimeService.updateStream.listen(
        (update) => add(RealTimeDataUpdateReceived(update: update)),
      ),
    );

    // Batch updates
    _subscriptions.add(
      _realTimeService.batchUpdateStream.listen(
        (updates) => add(BatchRealTimeUpdatesReceived(updates: updates)),
      ),
    );

    // Temporal updates
    _subscriptions.add(
      _realTimeService.temporalUpdateStream.listen(
        (temporalData) => add(TemporalDataUpdateReceived(temporalData: temporalData)),
      ),
    );

    // Conflict notifications
    _subscriptions.add(
      _realTimeService.conflictStream.listen(
        (conflict) => add(ConflictNotificationReceived(conflict: conflict)),
      ),
    );

    // Performance metrics
    _subscriptions.add(
      _realTimeService.metricsStream.listen(
        (metrics) => add(PerformanceMetricsUpdated(metrics: metrics)),
      ),
    );
  }

  /// Process data update
  void _processDataUpdate(RealTimeUpdate update) {
    if (update.riskData != null) {
      _riskDataCache[update.riskData!.id] = update.riskData!;
    }

    if (update.riskDataBatch != null) {
      for (final riskData in update.riskDataBatch!) {
        _riskDataCache[riskData.id] = riskData;
      }
    }
  }

  /// Process data deletion
  void _processDataDeletion(RealTimeUpdate update) {
    for (final regionId in update.affectedRegions) {
      _riskDataCache.removeWhere((key, value) => value.region == regionId);
    }
  }

  /// Process batch update
  void _processBatchUpdate(RealTimeUpdate update) {
    if (update.riskDataBatch != null) {
      for (final riskData in update.riskDataBatch!) {
        _riskDataCache[riskData.id] = riskData;
      }
    }
  }
}