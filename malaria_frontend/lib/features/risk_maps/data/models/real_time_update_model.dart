/// Real-time Update Model for Live Map Data Synchronization
///
/// This model handles real-time updates for malaria risk map data through
/// WebSocket connections. It provides serialization/deserialization for
/// live data streams, conflict resolution, and temporal data management.
///
/// Features:
/// - Real-time risk data updates with timestamps
/// - Conflict resolution for concurrent data changes
/// - Change tracking and delta updates
/// - Animation-friendly data structure
/// - Performance optimized serialization
/// - Validation and data integrity checks
///
/// Author: Claude AI Agent - Real-time Visualization System
/// Created: 2025-09-19
library;

import 'package:json_annotation/json_annotation.dart';
import 'risk_data_model.dart';
import '../../domain/entities/real_time_update.dart';

part 'real_time_update_model.g.dart';

/// Update types for real-time map data changes
enum UpdateType {
  /// New risk data added
  @JsonValue('create')
  create,

  /// Existing risk data updated
  @JsonValue('update')
  update,

  /// Risk data removed
  @JsonValue('delete')
  delete,

  /// Batch update of multiple regions
  @JsonValue('batch')
  batch,

  /// Emergency alert with immediate visualization
  @JsonValue('alert')
  alert,

  /// Heartbeat/keep-alive message
  @JsonValue('heartbeat')
  heartbeat,
}

/// Priority levels for real-time updates
enum UpdatePriority {
  /// Low priority, background updates
  @JsonValue('low')
  low,

  /// Normal priority updates
  @JsonValue('normal')
  normal,

  /// High priority updates requiring immediate attention
  @JsonValue('high')
  high,

  /// Critical updates requiring emergency response
  @JsonValue('critical')
  critical,
}

/// Animation types for data changes
enum AnimationType {
  /// Fade in/out animation
  @JsonValue('fade')
  fade,

  /// Scale animation for emphasis
  @JsonValue('scale')
  scale,

  /// Pulse animation for alerts
  @JsonValue('pulse')
  pulse,

  /// Slide animation for temporal changes
  @JsonValue('slide')
  slide,

  /// No animation
  @JsonValue('none')
  none,
}

/// Data model for real-time map updates with comprehensive metadata
@JsonSerializable(explicitToJson: true)
class RealTimeUpdateModel {
  /// Unique update identifier
  @JsonKey(name: 'update_id')
  final String updateId;

  /// Type of update operation
  @JsonKey(name: 'update_type')
  final UpdateType updateType;

  /// Priority level of the update
  @JsonKey(name: 'priority')
  final UpdatePriority priority;

  /// Timestamp when update was generated
  @JsonKey(name: 'timestamp')
  final DateTime timestamp;

  /// Timestamp when update should be applied
  @JsonKey(name: 'apply_at')
  final DateTime? applyAt;

  /// Version number for conflict resolution
  @JsonKey(name: 'version')
  final int version;

  /// Source of the update (system, user, external)
  @JsonKey(name: 'source')
  final String source;

  /// Session ID for tracking related updates
  @JsonKey(name: 'session_id')
  final String? sessionId;

  /// Risk data being updated
  @JsonKey(name: 'risk_data')
  final RiskDataModel? riskData;

  /// Batch of risk data for bulk updates
  @JsonKey(name: 'risk_data_batch')
  final List<RiskDataModel>? riskDataBatch;

  /// Change delta for efficient updates
  @JsonKey(name: 'change_delta')
  final Map<String, dynamic>? changeDelta;

  /// Previous data for rollback capability
  @JsonKey(name: 'previous_data')
  final RiskDataModel? previousData;

  /// Affected region identifiers
  @JsonKey(name: 'affected_regions')
  final List<String> affectedRegions;

  /// Geographic bounds of the update
  @JsonKey(name: 'geographic_bounds')
  final GeographicBoundsModel? geographicBounds;

  /// Animation configuration for the update
  @JsonKey(name: 'animation_config')
  final AnimationConfigModel? animationConfig;

  /// Validation checksum for data integrity
  @JsonKey(name: 'checksum')
  final String? checksum;

  /// Additional metadata and context
  @JsonKey(name: 'metadata')
  final Map<String, dynamic> metadata;

  /// Whether this update supersedes previous updates
  @JsonKey(name: 'supersedes')
  final List<String>? supersedes;

  /// TTL (time to live) for the update in seconds
  @JsonKey(name: 'ttl')
  final int? ttl;

  const RealTimeUpdateModel({
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

  /// Create model from JSON
  factory RealTimeUpdateModel.fromJson(Map<String, dynamic> json) =>
      _$RealTimeUpdateModelFromJson(json);

  /// Convert model to JSON
  Map<String, dynamic> toJson() => _$RealTimeUpdateModelToJson(this);

  /// Convert model to domain entity
  RealTimeUpdate toDomain() {
    return RealTimeUpdate(
      updateId: updateId,
      updateType: _mapUpdateType(updateType),
      priority: _mapPriority(priority),
      timestamp: timestamp,
      applyAt: applyAt,
      version: version,
      source: source,
      sessionId: sessionId,
      riskData: riskData?.toDomain(),
      riskDataBatch: riskDataBatch?.map((data) => data.toDomain()).toList(),
      changeDelta: changeDelta,
      previousData: previousData?.toDomain(),
      affectedRegions: affectedRegions,
      geographicBounds: geographicBounds?.toDomain(),
      animationConfig: animationConfig?.toDomain(),
      checksum: checksum,
      metadata: metadata,
      supersedes: supersedes,
      ttl: ttl,
    );
  }

  /// Create model from domain entity
  factory RealTimeUpdateModel.fromDomain(RealTimeUpdate update) {
    return RealTimeUpdateModel(
      updateId: update.updateId,
      updateType: _mapDomainUpdateType(update.updateType),
      priority: _mapDomainPriority(update.priority),
      timestamp: update.timestamp,
      applyAt: update.applyAt,
      version: update.version,
      source: update.source,
      sessionId: update.sessionId,
      riskData: update.riskData != null ? RiskDataModel.fromDomain(update.riskData!) : null,
      riskDataBatch: update.riskDataBatch?.map((data) => RiskDataModel.fromDomain(data)).toList(),
      changeDelta: update.changeDelta,
      previousData: update.previousData != null ? RiskDataModel.fromDomain(update.previousData!) : null,
      affectedRegions: update.affectedRegions,
      geographicBounds: update.geographicBounds != null ? GeographicBoundsModel.fromDomain(update.geographicBounds!) : null,
      animationConfig: update.animationConfig != null ? AnimationConfigModel.fromDomain(update.animationConfig!) : null,
      checksum: update.checksum,
      metadata: update.metadata,
      supersedes: update.supersedes,
      ttl: update.ttl,
    );
  }

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

  /// Create a copy with updated fields
  RealTimeUpdateModel copyWith({
    String? updateId,
    UpdateType? updateType,
    UpdatePriority? priority,
    DateTime? timestamp,
    DateTime? applyAt,
    int? version,
    String? source,
    String? sessionId,
    RiskDataModel? riskData,
    List<RiskDataModel>? riskDataBatch,
    Map<String, dynamic>? changeDelta,
    RiskDataModel? previousData,
    List<String>? affectedRegions,
    GeographicBoundsModel? geographicBounds,
    AnimationConfigModel? animationConfig,
    String? checksum,
    Map<String, dynamic>? metadata,
    List<String>? supersedes,
    int? ttl,
  }) {
    return RealTimeUpdateModel(
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

  /// Private helper methods for type mapping
  static RealTimeUpdateType _mapUpdateType(UpdateType type) {
    switch (type) {
      case UpdateType.create:
        return RealTimeUpdateType.create;
      case UpdateType.update:
        return RealTimeUpdateType.update;
      case UpdateType.delete:
        return RealTimeUpdateType.delete;
      case UpdateType.batch:
        return RealTimeUpdateType.batch;
      case UpdateType.alert:
        return RealTimeUpdateType.alert;
      case UpdateType.heartbeat:
        return RealTimeUpdateType.heartbeat;
    }
  }

  static UpdateType _mapDomainUpdateType(RealTimeUpdateType type) {
    switch (type) {
      case RealTimeUpdateType.create:
        return UpdateType.create;
      case RealTimeUpdateType.update:
        return UpdateType.update;
      case RealTimeUpdateType.delete:
        return UpdateType.delete;
      case RealTimeUpdateType.batch:
        return UpdateType.batch;
      case RealTimeUpdateType.alert:
        return UpdateType.alert;
      case RealTimeUpdateType.heartbeat:
        return UpdateType.heartbeat;
    }
  }

  static RealTimeUpdatePriority _mapPriority(UpdatePriority priority) {
    switch (priority) {
      case UpdatePriority.low:
        return RealTimeUpdatePriority.low;
      case UpdatePriority.normal:
        return RealTimeUpdatePriority.normal;
      case UpdatePriority.high:
        return RealTimeUpdatePriority.high;
      case UpdatePriority.critical:
        return RealTimeUpdatePriority.critical;
    }
  }

  static UpdatePriority _mapDomainPriority(RealTimeUpdatePriority priority) {
    switch (priority) {
      case RealTimeUpdatePriority.low:
        return UpdatePriority.low;
      case RealTimeUpdatePriority.normal:
        return UpdatePriority.normal;
      case RealTimeUpdatePriority.high:
        return UpdatePriority.high;
      case RealTimeUpdatePriority.critical:
        return UpdatePriority.critical;
    }
  }
}

/// Geographic bounds model for update regions
@JsonSerializable()
class GeographicBoundsModel {
  /// Southwest corner of the bounds
  @JsonKey(name: 'southwest')
  final LatLngModel southwest;

  /// Northeast corner of the bounds
  @JsonKey(name: 'northeast')
  final LatLngModel northeast;

  const GeographicBoundsModel({
    required this.southwest,
    required this.northeast,
  });

  factory GeographicBoundsModel.fromJson(Map<String, dynamic> json) =>
      _$GeographicBoundsModelFromJson(json);

  Map<String, dynamic> toJson() => _$GeographicBoundsModelToJson(this);

  GeographicBounds toDomain() {
    return GeographicBounds(
      southwest: southwest.toDomain(),
      northeast: northeast.toDomain(),
    );
  }

  factory GeographicBoundsModel.fromDomain(GeographicBounds bounds) {
    return GeographicBoundsModel(
      southwest: LatLngModel.fromDomain(bounds.southwest),
      northeast: LatLngModel.fromDomain(bounds.northeast),
    );
  }
}

/// Animation configuration model for updates
@JsonSerializable()
class AnimationConfigModel {
  /// Type of animation to apply
  @JsonKey(name: 'animation_type')
  final AnimationType animationType;

  /// Duration of animation in milliseconds
  @JsonKey(name: 'duration_ms')
  final int durationMs;

  /// Animation curve (linear, ease-in, ease-out, etc.)
  @JsonKey(name: 'curve')
  final String curve;

  /// Delay before starting animation in milliseconds
  @JsonKey(name: 'delay_ms')
  final int delayMs;

  /// Whether to repeat the animation
  @JsonKey(name: 'repeat')
  final bool repeat;

  /// Number of repetitions (null for infinite)
  @JsonKey(name: 'repeat_count')
  final int? repeatCount;

  const AnimationConfigModel({
    required this.animationType,
    this.durationMs = 300,
    this.curve = 'ease-in-out',
    this.delayMs = 0,
    this.repeat = false,
    this.repeatCount,
  });

  factory AnimationConfigModel.fromJson(Map<String, dynamic> json) =>
      _$AnimationConfigModelFromJson(json);

  Map<String, dynamic> toJson() => _$AnimationConfigModelToJson(this);

  AnimationConfig toDomain() {
    return AnimationConfig(
      animationType: _mapAnimationType(animationType),
      durationMs: durationMs,
      curve: curve,
      delayMs: delayMs,
      repeat: repeat,
      repeatCount: repeatCount,
    );
  }

  factory AnimationConfigModel.fromDomain(AnimationConfig config) {
    return AnimationConfigModel(
      animationType: _mapDomainAnimationType(config.animationType),
      durationMs: config.durationMs,
      curve: config.curve,
      delayMs: config.delayMs,
      repeat: config.repeat,
      repeatCount: config.repeatCount,
    );
  }

  static RealTimeAnimationType _mapAnimationType(AnimationType type) {
    switch (type) {
      case AnimationType.fade:
        return RealTimeAnimationType.fade;
      case AnimationType.scale:
        return RealTimeAnimationType.scale;
      case AnimationType.pulse:
        return RealTimeAnimationType.pulse;
      case AnimationType.slide:
        return RealTimeAnimationType.slide;
      case AnimationType.none:
        return RealTimeAnimationType.none;
    }
  }

  static AnimationType _mapDomainAnimationType(RealTimeAnimationType type) {
    switch (type) {
      case RealTimeAnimationType.fade:
        return AnimationType.fade;
      case RealTimeAnimationType.scale:
        return AnimationType.scale;
      case RealTimeAnimationType.pulse:
        return AnimationType.pulse;
      case RealTimeAnimationType.slide:
        return AnimationType.slide;
      case RealTimeAnimationType.none:
        return AnimationType.none;
    }
  }
}

/// Utility extensions for batch operations
extension RealTimeUpdateModelListExtension on List<RealTimeUpdateModel> {
  /// Convert list of models to domain entities
  List<RealTimeUpdate> toDomainList() =>
      map((model) => model.toDomain()).toList();

  /// Filter by update type
  List<RealTimeUpdateModel> filterByType(UpdateType type) =>
      where((update) => update.updateType == type).toList();

  /// Filter by priority
  List<RealTimeUpdateModel> filterByPriority(UpdatePriority priority) =>
      where((update) => update.priority == priority).toList();

  /// Filter by affected region
  List<RealTimeUpdateModel> filterByRegion(String region) =>
      where((update) => update.affectedRegions.contains(region)).toList();

  /// Sort by timestamp (newest first)
  List<RealTimeUpdateModel> sortByTimestamp({bool ascending = false}) {
    final sorted = List<RealTimeUpdateModel>.from(this);
    sorted.sort((a, b) => ascending
        ? a.timestamp.compareTo(b.timestamp)
        : b.timestamp.compareTo(a.timestamp));
    return sorted;
  }

  /// Sort by priority (critical first)
  List<RealTimeUpdateModel> sortByPriority() {
    final sorted = List<RealTimeUpdateModel>.from(this);
    sorted.sort((a, b) => _priorityOrder(b.priority).compareTo(_priorityOrder(a.priority)));
    return sorted;
  }

  /// Remove expired updates
  List<RealTimeUpdateModel> removeExpired() =>
      where((update) => !update.isExpired).toList();

  /// Get updates that should be applied now
  List<RealTimeUpdateModel> getApplicableNow() =>
      where((update) => update.shouldApplyNow).toList();
}

/// Helper function for priority ordering
int _priorityOrder(UpdatePriority priority) {
  switch (priority) {
    case UpdatePriority.critical:
      return 3;
    case UpdatePriority.high:
      return 2;
    case UpdatePriority.normal:
      return 1;
    case UpdatePriority.low:
      return 0;
  }
}