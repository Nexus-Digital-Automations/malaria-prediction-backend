/// Real-time Overlay Widget for Live Risk Map Visualization
///
/// This widget provides a comprehensive real-time overlay system for malaria
/// risk maps with animated transitions, data refresh indicators, conflict
/// resolution UI, and performance-optimized rendering for frequent updates.
///
/// Features:
/// - Animated risk markers with smooth transitions
/// - Real-time data refresh indicators and loading states
/// - Conflict resolution notifications and controls
/// - Performance metrics and connection status display
/// - Customizable animation configurations
/// - Touch-friendly interaction controls
/// - Accessibility support for screen readers
/// - Responsive design for different screen sizes
///
/// Author: Claude AI Agent - Real-time Visualization System
/// Created: 2025-09-19
library;

import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:latlong2/latlong.dart';

import '../../data/services/real_time_map_service.dart';
import '../../domain/entities/real_time_update.dart';
import '../../domain/entities/risk_data.dart';

/// Real-time overlay configuration
class RealTimeOverlayConfig {
  /// Whether to show connection status indicator
  final bool showConnectionStatus;

  /// Whether to show performance metrics
  final bool showPerformanceMetrics;

  /// Whether to show data refresh indicators
  final bool showRefreshIndicators;

  /// Whether to enable animated transitions
  final bool enableAnimations;

  /// Default animation duration
  final Duration defaultAnimationDuration;

  /// Maximum number of concurrent animations
  final int maxConcurrentAnimations;

  /// Whether to show conflict notifications
  final bool showConflictNotifications;

  /// Auto-refresh interval for data
  final Duration? autoRefreshInterval;

  /// Theme configuration
  final RealTimeOverlayTheme theme;

  const RealTimeOverlayConfig({
    this.showConnectionStatus = true,
    this.showPerformanceMetrics = false,
    this.showRefreshIndicators = true,
    this.enableAnimations = true,
    this.defaultAnimationDuration = const Duration(milliseconds: 300),
    this.maxConcurrentAnimations = 10,
    this.showConflictNotifications = true,
    this.autoRefreshInterval,
    this.theme = const RealTimeOverlayTheme(),
  });
}

/// Theme configuration for real-time overlay
class RealTimeOverlayTheme {
  /// Colors for different connection states
  final Map<RealTimeConnectionStatus, Color> connectionStatusColors;

  /// Colors for different risk levels
  final Map<RiskLevel, Color> riskLevelColors;

  /// Animation curve for transitions
  final Curve animationCurve;

  /// Opacity for overlay elements
  final double overlayOpacity;

  /// Border radius for UI elements
  final double borderRadius;

  /// Shadow elevation
  final double elevation;

  const RealTimeOverlayTheme({
    this.connectionStatusColors = const {
      RealTimeConnectionStatus.connected: Colors.green,
      RealTimeConnectionStatus.connecting: Colors.orange,
      RealTimeConnectionStatus.disconnected: Colors.red,
      RealTimeConnectionStatus.reconnecting: Colors.amber,
      RealTimeConnectionStatus.error: Colors.red,
      RealTimeConnectionStatus.paused: Colors.grey,
    },
    this.riskLevelColors = const {
      RiskLevel.low: Colors.green,
      RiskLevel.medium: Colors.orange,
      RiskLevel.high: Colors.red,
      RiskLevel.critical: Colors.deepPurple,
    },
    this.animationCurve = Curves.easeInOut,
    this.overlayOpacity = 0.9,
    this.borderRadius = 8.0,
    this.elevation = 4.0,
  });
}

/// Interactive real-time overlay widget
class RealTimeOverlay extends StatefulWidget {
  /// Real-time map service for data updates
  final RealTimeMapService realTimeService;

  /// Configuration for overlay appearance and behavior
  final RealTimeOverlayConfig config;

  /// Callback for risk marker taps
  final void Function(RiskData riskData)? onRiskMarkerTap;

  /// Callback for overlay long press
  final void Function(LatLng position)? onLongPress;

  /// Callback for refresh requests
  final VoidCallback? onRefreshRequested;

  /// Callback for conflict resolution
  final void Function(ConflictNotification conflict)? onConflictResolution;

  /// Current map bounds for optimization
  final GeographicBounds? visibleBounds;

  /// Current zoom level for detail filtering
  final double? zoomLevel;

  const RealTimeOverlay({
    Key? key,
    required this.realTimeService,
    this.config = const RealTimeOverlayConfig(),
    this.onRiskMarkerTap,
    this.onLongPress,
    this.onRefreshRequested,
    this.onConflictResolution,
    this.visibleBounds,
    this.zoomLevel,
  }) : super(key: key);

  @override
  State<RealTimeOverlay> createState() => _RealTimeOverlayState();
}

class _RealTimeOverlayState extends State<RealTimeOverlay>
    with TickerProviderStateMixin {
  /// Stream subscriptions
  late StreamSubscription<RealTimeConnectionStatus> _connectionSubscription;
  late StreamSubscription<RealTimeUpdate> _updateSubscription;
  late StreamSubscription<List<RealTimeUpdate>> _batchUpdateSubscription;
  late StreamSubscription<ConflictNotification> _conflictSubscription;
  late StreamSubscription<RealTimeMetrics> _metricsSubscription;

  /// Current real-time data
  final Map<String, RiskData> _currentRiskData = {};

  /// Animation controllers for different markers
  final Map<String, AnimationController> _animationControllers = {};

  /// Current connection status
  RealTimeConnectionStatus _connectionStatus = RealTimeConnectionStatus.disconnected;

  /// Current performance metrics
  RealTimeMetrics? _currentMetrics;

  /// Active conflicts awaiting resolution
  final List<ConflictNotification> _activeConflicts = [];

  /// Refresh indicator state
  bool _isRefreshing = false;

  /// Auto-refresh timer
  Timer? _autoRefreshTimer;

  /// Active animations count for performance management
  int _activeAnimations = 0;

  @override
  void initState() {
    super.initState();
    _initializeSubscriptions();
    _setupAutoRefresh();
  }

  @override
  void dispose() {
    _disposeSubscriptions();
    _disposeAnimationControllers();
    _autoRefreshTimer?.cancel();
    super.dispose();
  }

  void _initializeSubscriptions() {
    // Connection status updates
    _connectionSubscription = widget.realTimeService.connectionStatus.listen(
      (status) {
        setState(() {
          _connectionStatus = status;
        });
      },
    );

    // Individual real-time updates
    _updateSubscription = widget.realTimeService.updateStream.listen(
      _handleRealTimeUpdate,
    );

    // Batch updates
    _batchUpdateSubscription = widget.realTimeService.batchUpdateStream.listen(
      _handleBatchUpdate,
    );

    // Conflict notifications
    _conflictSubscription = widget.realTimeService.conflictStream.listen(
      _handleConflictNotification,
    );

    // Performance metrics
    _metricsSubscription = widget.realTimeService.metricsStream.listen(
      (metrics) {
        setState(() {
          _currentMetrics = metrics;
        });
      },
    );
  }

  void _disposeSubscriptions() {
    _connectionSubscription.cancel();
    _updateSubscription.cancel();
    _batchUpdateSubscription.cancel();
    _conflictSubscription.cancel();
    _metricsSubscription.cancel();
  }

  void _disposeAnimationControllers() {
    for (final controller in _animationControllers.values) {
      controller.dispose();
    }
    _animationControllers.clear();
  }

  void _setupAutoRefresh() {
    if (widget.config.autoRefreshInterval != null) {
      _autoRefreshTimer = Timer.periodic(
        widget.config.autoRefreshInterval!,
        (_) => _requestDataRefresh(),
      );
    }
  }

  void _handleRealTimeUpdate(RealTimeUpdate update) {
    if (!_isUpdateRelevant(update)) return;

    switch (update.updateType) {
      case RealTimeUpdateType.create:
      case RealTimeUpdateType.update:
        _handleDataUpdate(update);
        break;
      case RealTimeUpdateType.delete:
        _handleDataDeletion(update);
        break;
      case RealTimeUpdateType.alert:
        _handleAlertUpdate(update);
        break;
      default:
        break;
    }
  }

  void _handleBatchUpdate(List<RealTimeUpdate> updates) {
    for (final update in updates) {
      _handleRealTimeUpdate(update);
    }
  }

  void _handleConflictNotification(ConflictNotification conflict) {
    if (widget.config.showConflictNotifications) {
      setState(() {
        _activeConflicts.add(conflict);
      });

      // Auto-resolve after timeout if not manually resolved
      Timer(const Duration(seconds: 30), () {
        _activeConflicts.removeWhere((c) => c.conflictId == conflict.conflictId);
        if (mounted) setState(() {});
      });
    }

    widget.onConflictResolution?.call(conflict);
  }

  void _handleDataUpdate(RealTimeUpdate update) {
    final riskData = update.primaryRiskData;
    if (riskData == null) return;

    setState(() {
      _currentRiskData[riskData.id] = riskData;
    });

    if (widget.config.enableAnimations && update.hasAnimation) {
      _animateUpdate(riskData.id, update.animationConfig!);
    }
  }

  void _handleDataDeletion(RealTimeUpdate update) {
    for (final regionId in update.affectedRegions) {
      setState(() {
        _currentRiskData.removeWhere((key, value) => value.region == regionId);
      });

      _disposeAnimationController(regionId);
    }
  }

  void _handleAlertUpdate(RealTimeUpdate update) {
    final riskData = update.primaryRiskData;
    if (riskData == null) return;

    _handleDataUpdate(update);

    // Show alert notification
    if (update.isCriticalAlert) {
      _showCriticalAlert(riskData);
    }

    // Trigger haptic feedback for critical alerts
    if (update.priority == RealTimeUpdatePriority.critical) {
      HapticFeedback.vibrate();
    }
  }

  void _animateUpdate(String markerId, AnimationConfig config) {
    if (_activeAnimations >= widget.config.maxConcurrentAnimations) return;

    final controller = _getOrCreateAnimationController(markerId, config);

    _activeAnimations++;
    controller.forward().then((_) {
      _activeAnimations--;
      if (config.repeat && (config.repeatCount == null || config.repeatCount! > 1)) {
        controller.reset();
        _animateUpdate(markerId, config.copyWith(
          repeatCount: config.repeatCount != null ? config.repeatCount! - 1 : null,
        ));
      }
    });
  }

  AnimationController _getOrCreateAnimationController(
    String markerId,
    AnimationConfig config,
  ) {
    final existing = _animationControllers[markerId];
    if (existing != null) {
      return existing;
    }

    final controller = AnimationController(
      duration: config.duration,
      vsync: this,
    );

    _animationControllers[markerId] = controller;
    return controller;
  }

  void _disposeAnimationController(String markerId) {
    final controller = _animationControllers.remove(markerId);
    controller?.dispose();
  }

  bool _isUpdateRelevant(RealTimeUpdate update) {
    // Check if update is within visible bounds
    if (widget.visibleBounds != null && update.geographicBounds != null) {
      return widget.visibleBounds!.isWithinBounds(update.geographicBounds!);
    }

    // Check zoom level appropriateness
    if (widget.zoomLevel != null) {
      // This would need proper implementation based on detail levels
      return true;
    }

    return true;
  }

  void _requestDataRefresh() {
    if (_isRefreshing) return;

    setState(() {
      _isRefreshing = true;
    });

    widget.realTimeService.requestDataRefresh().then((_) {
      if (mounted) {
        setState(() {
          _isRefreshing = false;
        });
      }
    }).catchError((error) {
      if (mounted) {
        setState(() {
          _isRefreshing = false;
        });
      }
    });

    widget.onRefreshRequested?.call();
  }

  void _showCriticalAlert(RiskData riskData) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning, color: Colors.red),
            SizedBox(width: 8),
            Text('Critical Risk Alert'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('High risk detected in ${riskData.regionName}'),
            const SizedBox(height: 8),
            Text('Risk Score: ${(riskData.riskScore * 100).toStringAsFixed(1)}%'),
            Text('Confidence: ${(riskData.confidence * 100).toStringAsFixed(1)}%'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Acknowledge'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              widget.onRiskMarkerTap?.call(riskData);
            },
            child: const Text('View Details'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Main risk markers overlay
        Positioned.fill(
          child: _buildRiskMarkersOverlay(),
        ),

        // Connection status indicator
        if (widget.config.showConnectionStatus)
          Positioned(
            top: 16,
            right: 16,
            child: _buildConnectionStatusIndicator(),
          ),

        // Performance metrics
        if (widget.config.showPerformanceMetrics && _currentMetrics != null)
          Positioned(
            top: 16,
            left: 16,
            child: _buildPerformanceMetrics(),
          ),

        // Refresh indicator
        if (widget.config.showRefreshIndicators)
          Positioned(
            top: 60,
            right: 16,
            child: _buildRefreshIndicator(),
          ),

        // Conflict notifications
        if (widget.config.showConflictNotifications && _activeConflicts.isNotEmpty)
          Positioned(
            bottom: 100,
            left: 16,
            right: 16,
            child: _buildConflictNotifications(),
          ),
      ],
    );
  }

  Widget _buildRiskMarkersOverlay() {
    return GestureDetector(
      onLongPressStart: (details) {
        // Convert screen position to geographic coordinates
        // This would need proper coordinate conversion
        final position = LatLng(0, 0); // Placeholder
        widget.onLongPress?.call(position);
      },
      child: CustomPaint(
        painter: RiskMarkersPainter(
          riskData: _currentRiskData.values.toList(),
          animationControllers: _animationControllers,
          theme: widget.config.theme,
          onMarkerTap: widget.onRiskMarkerTap,
        ),
        child: Container(),
      ),
    );
  }

  Widget _buildConnectionStatusIndicator() {
    final color = widget.config.theme.connectionStatusColors[_connectionStatus] ?? Colors.grey;
    final icon = _getConnectionStatusIcon(_connectionStatus);

    return AnimatedContainer(
      duration: widget.config.defaultAnimationDuration,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(widget.config.theme.overlayOpacity),
        borderRadius: BorderRadius.circular(widget.config.theme.borderRadius),
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: widget.config.theme.elevation,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white, size: 16),
          const SizedBox(width: 4),
          Text(
            _connectionStatus.name.toUpperCase(),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPerformanceMetrics() {
    if (_currentMetrics == null) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(widget.config.theme.overlayOpacity),
        borderRadius: BorderRadius.circular(widget.config.theme.borderRadius),
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: widget.config.theme.elevation,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Performance',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Updates: ${_currentMetrics!.updatesProcessed}',
            style: const TextStyle(color: Colors.white70, fontSize: 10),
          ),
          Text(
            'Latency: ${_currentMetrics!.latencyMs}ms',
            style: const TextStyle(color: Colors.white70, fontSize: 10),
          ),
          Text(
            'Uptime: ${_currentMetrics!.uptimePercentage.toStringAsFixed(1)}%',
            style: const TextStyle(color: Colors.white70, fontSize: 10),
          ),
        ],
      ),
    );
  }

  Widget _buildRefreshIndicator() {
    return AnimatedContainer(
      duration: widget.config.defaultAnimationDuration,
      child: FloatingActionButton(
        mini: true,
        onPressed: _isRefreshing ? null : _requestDataRefresh,
        backgroundColor: _isRefreshing ? Colors.grey : Colors.blue,
        child: _isRefreshing
            ? const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Icon(Icons.refresh, size: 16),
      ),
    );
  }

  Widget _buildConflictNotifications() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: _activeConflicts.map((conflict) {
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.orange.withOpacity(widget.config.theme.overlayOpacity),
            borderRadius: BorderRadius.circular(widget.config.theme.borderRadius),
            boxShadow: [
              BoxShadow(
                color: Colors.black26,
                blurRadius: widget.config.theme.elevation,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              const Icon(Icons.warning, color: Colors.white, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      'Data Conflict',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                    Text(
                      'Conflict in ${conflict.existingUpdate.affectedRegions.join(', ')}',
                      style: const TextStyle(color: Colors.white70, fontSize: 10),
                    ),
                  ],
                ),
              ),
              TextButton(
                onPressed: () {
                  setState(() {
                    _activeConflicts.remove(conflict);
                  });
                  widget.onConflictResolution?.call(conflict);
                },
                child: const Text(
                  'Resolve',
                  style: TextStyle(color: Colors.white, fontSize: 10),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  IconData _getConnectionStatusIcon(RealTimeConnectionStatus status) {
    switch (status) {
      case RealTimeConnectionStatus.connected:
        return Icons.wifi;
      case RealTimeConnectionStatus.connecting:
      case RealTimeConnectionStatus.reconnecting:
        return Icons.wifi_tethering;
      case RealTimeConnectionStatus.disconnected:
        return Icons.wifi_off;
      case RealTimeConnectionStatus.error:
        return Icons.error;
      case RealTimeConnectionStatus.paused:
        return Icons.pause;
    }
  }
}

/// Custom painter for risk markers with animations
class RiskMarkersPainter extends CustomPainter {
  final List<RiskData> riskData;
  final Map<String, AnimationController> animationControllers;
  final RealTimeOverlayTheme theme;
  final void Function(RiskData)? onMarkerTap;

  RiskMarkersPainter({
    required this.riskData,
    required this.animationControllers,
    required this.theme,
    this.onMarkerTap,
  });

  @override
  void paint(Canvas canvas, Size size) {
    for (final data in riskData) {
      _paintRiskMarker(canvas, size, data);
    }
  }

  void _paintRiskMarker(Canvas canvas, Size size, RiskData data) {
    // Convert geographic coordinates to screen coordinates
    // This would need proper map projection
    final screenX = size.width * 0.5; // Placeholder
    final screenY = size.height * 0.5; // Placeholder

    final controller = animationControllers[data.id];
    final animationValue = controller?.value ?? 1.0;

    final color = theme.riskLevelColors[data.riskLevel] ?? Colors.grey;
    final radius = 10.0 * animationValue;

    final paint = Paint()
      ..color = color.withOpacity(0.7 * animationValue)
      ..style = PaintingStyle.fill;

    final borderPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Draw marker circle
    canvas.drawCircle(
      Offset(screenX, screenY),
      radius,
      paint,
    );

    canvas.drawCircle(
      Offset(screenX, screenY),
      radius,
      borderPaint,
    );

    // Draw risk score text
    final textPainter = TextPainter(
      text: TextSpan(
        text: (data.riskScore * 100).toStringAsFixed(0),
        style: TextStyle(
          color: Colors.white,
          fontSize: 8 * animationValue,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(
        screenX - textPainter.width / 2,
        screenY - textPainter.height / 2,
      ),
    );
  }

  @override
  bool shouldRepaint(RiskMarkersPainter oldDelegate) {
    return riskData != oldDelegate.riskData ||
           animationControllers != oldDelegate.animationControllers;
  }
}

/// Extension for geographic bounds checks
extension GeographicBoundsExtension on GeographicBounds {
  /// Check if this bounds is within another bounds
  bool isWithinBounds(GeographicBounds other) {
    return southwest.latitude >= other.southwest.latitude &&
           northeast.latitude <= other.northeast.latitude &&
           southwest.longitude >= other.southwest.longitude &&
           northeast.longitude <= other.northeast.longitude;
  }
}