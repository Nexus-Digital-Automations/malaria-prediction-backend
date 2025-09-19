/// Real-time Update Domain Entity for Live Map Data
///
/// This entity represents real-time updates for malaria risk map data,
/// providing a clean domain model for WebSocket-based live data updates
/// with conflict resolution, temporal management, and animation support.
///
/// Author: Claude AI Agent - Real-time Visualization System
/// Created: 2025-09-19
library;

import 'package:equatable/equatable.dart';
import 'package:latlong2/latlong.dart';
import 'risk_data.dart';

/// Update types for real-time map data changes
enum RealTimeUpdateType {
  /// New risk data added
  create,

  /// Existing risk data updated
  update,

  /// Risk data removed
  delete,

  /// Batch update of multiple regions
  batch,

  /// Emergency alert with immediate visualization
  alert,

  /// Heartbeat/keep-alive message
  heartbeat,
}

/// Priority levels for real-time updates
enum RealTimeUpdatePriority {
  /// Low priority, background updates
  low,

  /// Normal priority updates
  normal,

  /// High priority updates requiring immediate attention
  high,

  /// Critical updates requiring emergency response
  critical,
}

/// Animation types for data changes
enum RealTimeAnimationType {
  /// Fade in/out animation
  fade,

  /// Scale animation for emphasis
  scale,

  /// Pulse animation for alerts
  pulse,

  /// Slide animation for temporal changes
  slide,

  /// No animation
  none,
}

/// Geographic bounds for update regions
class GeographicBounds extends Equatable {
  /// Southwest corner of the bounds
  final LatLng southwest;

  /// Northeast corner of the bounds
  final LatLng northeast;

  const GeographicBounds({
    required this.southwest,
    required this.northeast,
  });

  @override
  List<Object?> get props => [southwest, northeast];

  /// Get center point of the bounds
  LatLng get center {
    final lat = (southwest.latitude + northeast.latitude) / 2;
    final lng = (southwest.longitude + northeast.longitude) / 2;
    return LatLng(lat, lng);
  }

  /// Check if a point is within these bounds
  bool contains(LatLng point) {
    return point.latitude >= southwest.latitude &&
        point.latitude <= northeast.latitude &&
        point.longitude >= southwest.longitude &&
        point.longitude <= northeast.longitude;
  }

  /// Get area of the bounds in square degrees
  double get area {
    final latDiff = northeast.latitude - southwest.latitude;
    final lngDiff = northeast.longitude - southwest.longitude;
    return latDiff * lngDiff;
  }
}

/// Animation configuration for updates
class AnimationConfig extends Equatable {
  /// Type of animation to apply
  final RealTimeAnimationType animationType;

  /// Duration of animation in milliseconds
  final int durationMs;

  /// Animation curve (linear, ease-in, ease-out, etc.)
  final String curve;

  /// Delay before starting animation in milliseconds
  final int delayMs;

  /// Whether to repeat the animation
  final bool repeat;

  /// Number of repetitions (null for infinite)
  final int? repeatCount;

  const AnimationConfig({
    required this.animationType,
    this.durationMs = 300,
    this.curve = 'ease-in-out',
    this.delayMs = 0,
    this.repeat = false,
    this.repeatCount,
  });

  @override
  List<Object?> get props => [
        animationType,
        durationMs,
        curve,
        delayMs,
        repeat,
        repeatCount,
      ];

  /// Create a copy with updated values
  AnimationConfig copyWith({
    RealTimeAnimationType? animationType,
    int? durationMs,
    String? curve,
    int? delayMs,
    bool? repeat,
    int? repeatCount,
  }) {
    return AnimationConfig(
      animationType: animationType ?? this.animationType,
      durationMs: durationMs ?? this.durationMs,
      curve: curve ?? this.curve,
      delayMs: delayMs ?? this.delayMs,
      repeat: repeat ?? this.repeat,
      repeatCount: repeatCount ?? this.repeatCount,
    );
  }

  /// Get Flutter Duration object
  Duration get duration => Duration(milliseconds: durationMs);

  /// Get delay as Duration object
  Duration get delay => Duration(milliseconds: delayMs);
}

/// Real-time update domain entity
class RealTimeUpdate extends Equatable {
  /// Unique update identifier
  final String updateId;

  /// Type of update operation
  final RealTimeUpdateType updateType;

  /// Priority level of the update
  final RealTimeUpdatePriority priority;

  /// Timestamp when update was generated
  final DateTime timestamp;

  /// Timestamp when update should be applied
  final DateTime? applyAt;

  /// Version number for conflict resolution
  final int version;

  /// Source of the update (system, user, external)
  final String source;

  /// Session ID for tracking related updates
  final String? sessionId;

  /// Risk data being updated
  final RiskData? riskData;

  /// Batch of risk data for bulk updates
  final List<RiskData>? riskDataBatch;

  /// Change delta for efficient updates
  final Map<String, dynamic>? changeDelta;

  /// Previous data for rollback capability
  final RiskData? previousData;

  /// Affected region identifiers
  final List<String> affectedRegions;

  /// Geographic bounds of the update
  final GeographicBounds? geographicBounds;

  /// Animation configuration for the update
  final AnimationConfig? animationConfig;

  /// Validation checksum for data integrity
  final String? checksum;

  /// Additional metadata and context
  final Map<String, dynamic> metadata;

  /// Whether this update supersedes previous updates
  final List<String>? supersedes;

  /// TTL (time to live) for the update in seconds
  final int? ttl;

  const RealTimeUpdate({
    required this.updateId,
    required this.updateType,
    required this.priority,
    required this.timestamp,
    this.applyAt,
    required this.version,
    required this.source,
    this.sessionId,
    this.riskData,
    this.riskDataBatch,
    this.changeDelta,
    this.previousData,
    required this.affectedRegions,
    this.geographicBounds,
    this.animationConfig,
    this.checksum,
    required this.metadata,
    this.supersedes,
    this.ttl,
  });

  @override
  List<Object?> get props => [
        updateId,
        updateType,
        priority,
        timestamp,
        applyAt,
        version,
        source,
        sessionId,
        riskData,
        riskDataBatch,
        changeDelta,
        previousData,
        affectedRegions,
        geographicBounds,
        animationConfig,
        checksum,
        metadata,
        supersedes,
        ttl,
      ];

  /// Check if update is expired based on TTL
  bool get isExpired {
    if (ttl == null) return false;
    final expiryTime = timestamp.add(Duration(seconds: ttl!));
    return DateTime.now().isAfter(expiryTime);
  }

  /// Check if update should be applied now
  bool get shouldApplyNow {
    if (applyAt == null) return true;
    return DateTime.now().isAfter(applyAt!);
  }

  /// Get update age in seconds
  int get ageInSeconds {
    return DateTime.now().difference(timestamp).inSeconds;
  }

  /// Check if this is a critical alert
  bool get isCriticalAlert {
    return priority == RealTimeUpdatePriority.critical &&
           updateType == RealTimeUpdateType.alert;
  }

  /// Check if this is a batch update
  bool get isBatchUpdate {
    return updateType == RealTimeUpdateType.batch ||
           (riskDataBatch != null && riskDataBatch!.isNotEmpty);
  }

  /// Check if this update has animation
  bool get hasAnimation {
    return animationConfig != null &&
           animationConfig!.animationType != RealTimeAnimationType.none;
  }

  /// Get the primary risk data (single data or first from batch)
  RiskData? get primaryRiskData {
    if (riskData != null) return riskData;
    if (riskDataBatch != null && riskDataBatch!.isNotEmpty) {
      return riskDataBatch!.first;
    }
    return null;
  }

  /// Get all risk data (single data as list or batch)
  List<RiskData> get allRiskData {
    if (riskDataBatch != null) return riskDataBatch!;
    if (riskData != null) return [riskData!];
    return [];
  }

  /// Get priority weight for sorting (higher number = higher priority)
  int get priorityWeight {
    switch (priority) {
      case RealTimeUpdatePriority.critical:
        return 4;
      case RealTimeUpdatePriority.high:
        return 3;
      case RealTimeUpdatePriority.normal:
        return 2;
      case RealTimeUpdatePriority.low:
        return 1;
    }
  }

  /// Check if this update affects a specific region
  bool affectsRegion(String regionId) {
    return affectedRegions.contains(regionId);
  }

  /// Check if this update affects any of the given regions
  bool affectsAnyRegion(List<String> regionIds) {
    return regionIds.any((id) => affectedRegions.contains(id));
  }

  /// Check if this update is within geographic bounds
  bool isWithinBounds(GeographicBounds bounds) {
    if (geographicBounds == null) return false;

    // Check if update bounds overlap with given bounds
    return geographicBounds!.southwest.latitude <= bounds.northeast.latitude &&
           geographicBounds!.northeast.latitude >= bounds.southwest.latitude &&
           geographicBounds!.southwest.longitude <= bounds.northeast.longitude &&
           geographicBounds!.northeast.longitude >= bounds.southwest.longitude;
  }

  /// Create a copy with updated values
  RealTimeUpdate copyWith({
    String? updateId,
    RealTimeUpdateType? updateType,
    RealTimeUpdatePriority? priority,
    DateTime? timestamp,
    DateTime? applyAt,
    int? version,
    String? source,
    String? sessionId,
    RiskData? riskData,
    List<RiskData>? riskDataBatch,
    Map<String, dynamic>? changeDelta,
    RiskData? previousData,
    List<String>? affectedRegions,
    GeographicBounds? geographicBounds,
    AnimationConfig? animationConfig,
    String? checksum,
    Map<String, dynamic>? metadata,
    List<String>? supersedes,
    int? ttl,
  }) {
    return RealTimeUpdate(
      updateId: updateId ?? this.updateId,
      updateType: updateType ?? this.updateType,
      priority: priority ?? this.priority,
      timestamp: timestamp ?? this.timestamp,
      applyAt: applyAt ?? this.applyAt,
      version: version ?? this.version,
      source: source ?? this.source,
      sessionId: sessionId ?? this.sessionId,
      riskData: riskData ?? this.riskData,
      riskDataBatch: riskDataBatch ?? this.riskDataBatch,
      changeDelta: changeDelta ?? this.changeDelta,
      previousData: previousData ?? this.previousData,
      affectedRegions: affectedRegions ?? this.affectedRegions,
      geographicBounds: geographicBounds ?? this.geographicBounds,
      animationConfig: animationConfig ?? this.animationConfig,
      checksum: checksum ?? this.checksum,
      metadata: metadata ?? this.metadata,
      supersedes: supersedes ?? this.supersedes,
      ttl: ttl ?? this.ttl,
    );
  }

  /// Apply change delta to existing risk data
  RiskData? applyChangeDelta(RiskData existingData) {
    if (changeDelta == null) return riskData;

    // Create a copy of existing data with delta changes
    final updatedMetadata = Map<String, dynamic>.from(existingData.metadata);

    if (changeDelta!.containsKey('metadata')) {
      final deltaMetadata = changeDelta!['metadata'] as Map<String, dynamic>;
      updatedMetadata.addAll(deltaMetadata);
    }

    return existingData.copyWith(
      riskScore: changeDelta!['riskScore'] as double? ?? existingData.riskScore,
      confidence: changeDelta!['confidence'] as double? ?? existingData.confidence,
      timestamp: changeDelta!['timestamp'] != null
          ? DateTime.parse(changeDelta!['timestamp'] as String)
          : existingData.timestamp,
      metadata: updatedMetadata,
    );
  }

  /// Validate update integrity using checksum
  bool validateIntegrity() {
    if (checksum == null) return true;

    // Simple checksum validation (in real implementation, use proper hashing)
    final dataString = toString();
    final calculatedChecksum = dataString.hashCode.toString();

    return checksum == calculatedChecksum;
  }

  /// Get summary description of the update
  String get updateSummary {
    final action = updateType.name;
    final regions = affectedRegions.length;
    final priority = this.priority.name;

    return '$action update for $regions region(s) with $priority priority';
  }

  /// Check if this update supersedes another update
  bool supersedesUpdate(String updateId) {
    return supersedes?.contains(updateId) ?? false;
  }

  /// Create animation configuration for this update type
  static AnimationConfig defaultAnimationForType(RealTimeUpdateType type) {
    switch (type) {
      case RealTimeUpdateType.create:
        return const AnimationConfig(
          animationType: RealTimeAnimationType.fade,
          durationMs: 500,
          curve: 'ease-in',
        );
      case RealTimeUpdateType.update:
        return const AnimationConfig(
          animationType: RealTimeAnimationType.scale,
          durationMs: 300,
          curve: 'ease-in-out',
        );
      case RealTimeUpdateType.delete:
        return const AnimationConfig(
          animationType: RealTimeAnimationType.fade,
          durationMs: 400,
          curve: 'ease-out',
        );
      case RealTimeUpdateType.alert:
        return const AnimationConfig(
          animationType: RealTimeAnimationType.pulse,
          durationMs: 800,
          curve: 'ease-in-out',
          repeat: true,
          repeatCount: 3,
        );
      case RealTimeUpdateType.batch:
        return const AnimationConfig(
          animationType: RealTimeAnimationType.slide,
          durationMs: 600,
          curve: 'ease-in-out',
        );
      case RealTimeUpdateType.heartbeat:
        return const AnimationConfig(
          animationType: RealTimeAnimationType.none,
        );
    }
  }
}

/// Utility extensions for real-time update operations
extension RealTimeUpdateListExtension on List<RealTimeUpdate> {
  /// Filter by update type
  List<RealTimeUpdate> filterByType(RealTimeUpdateType type) {
    return where((update) => update.updateType == type).toList();
  }

  /// Filter by priority
  List<RealTimeUpdate> filterByPriority(RealTimeUpdatePriority priority) {
    return where((update) => update.priority == priority).toList();
  }

  /// Filter by affected region
  List<RealTimeUpdate> filterByRegion(String regionId) {
    return where((update) => update.affectsRegion(regionId)).toList();
  }

  /// Filter by time range
  List<RealTimeUpdate> filterByTimeRange(DateTime start, DateTime end) {
    return where((update) =>
        update.timestamp.isAfter(start) &&
        update.timestamp.isBefore(end)).toList();
  }

  /// Sort by timestamp (newest first)
  List<RealTimeUpdate> sortByTimestamp({bool ascending = false}) {
    final sorted = List<RealTimeUpdate>.from(this);
    sorted.sort((a, b) => ascending
        ? a.timestamp.compareTo(b.timestamp)
        : b.timestamp.compareTo(a.timestamp));
    return sorted;
  }

  /// Sort by priority (critical first)
  List<RealTimeUpdate> sortByPriority() {
    final sorted = List<RealTimeUpdate>.from(this);
    sorted.sort((a, b) => b.priorityWeight.compareTo(a.priorityWeight));
    return sorted;
  }

  /// Remove expired updates
  List<RealTimeUpdate> removeExpired() {
    return where((update) => !update.isExpired).toList();
  }

  /// Get updates that should be applied now
  List<RealTimeUpdate> getApplicableNow() {
    return where((update) => update.shouldApplyNow).toList();
  }

  /// Get critical alerts
  List<RealTimeUpdate> getCriticalAlerts() {
    return where((update) => update.isCriticalAlert).toList();
  }

  /// Get updates with animations
  List<RealTimeUpdate> getAnimatedUpdates() {
    return where((update) => update.hasAnimation).toList();
  }

  /// Group updates by region
  Map<String, List<RealTimeUpdate>> groupByRegion() {
    final grouped = <String, List<RealTimeUpdate>>{};

    for (final update in this) {
      for (final region in update.affectedRegions) {
        grouped.putIfAbsent(region, () => []).add(update);
      }
    }

    return grouped;
  }

  /// Group updates by priority
  Map<RealTimeUpdatePriority, List<RealTimeUpdate>> groupByPriority() {
    final grouped = <RealTimeUpdatePriority, List<RealTimeUpdate>>{};

    for (final update in this) {
      grouped.putIfAbsent(update.priority, () => []).add(update);
    }

    return grouped;
  }

  /// Get updates that supersede others
  List<RealTimeUpdate> getSupersedingUpdates() {
    return where((update) =>
        update.supersedes != null && update.supersedes!.isNotEmpty).toList();
  }

  /// Remove updates that are superseded by others
  List<RealTimeUpdate> removeSuperseded() {
    final superseded = <String>{};

    // Collect all superseded update IDs
    for (final update in this) {
      if (update.supersedes != null) {
        superseded.addAll(update.supersedes!);
      }
    }

    // Return updates that are not superseded
    return where((update) => !superseded.contains(update.updateId)).toList();
  }

  /// Get the latest update for each region
  Map<String, RealTimeUpdate> getLatestByRegion() {
    final latest = <String, RealTimeUpdate>{};

    for (final update in this) {
      for (final region in update.affectedRegions) {
        final existing = latest[region];
        if (existing == null || update.timestamp.isAfter(existing.timestamp)) {
          latest[region] = update;
        }
      }
    }

    return latest;
  }
}