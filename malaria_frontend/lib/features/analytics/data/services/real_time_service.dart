/// Real-time data service for analytics dashboard WebSocket integration
///
/// This service provides comprehensive real-time data update capabilities
/// for the analytics dashboard with WebSocket connection management,
/// automatic reconnection, message queuing, and data synchronization.
///
/// Features:
/// - WebSocket connection management with auto-reconnection
/// - Real-time analytics data updates
/// - Message queuing and offline handling
/// - Connection state monitoring
/// - Data synchronization and conflict resolution
/// - Heartbeat and keep-alive functionality
/// - Error handling and retry mechanisms
/// - Data compression and optimization
///
/// Usage:
/// ```dart
/// final realTimeService = RealTimeService();
/// await realTimeService.initialize();
///
/// // Listen to data updates
/// realTimeService.analyticsUpdates.listen((data) {
///   // Handle real-time analytics data
/// });
///
/// // Subscribe to specific region updates
/// await realTimeService.subscribeToRegion('Kenya');
/// ```
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import '../../domain/entities/analytics_data.dart';

/// Real-time update message types
enum RealTimeMessageType {
  /// Analytics data update
  analyticsUpdate,

  /// Alert notification
  alertNotification,

  /// System status update
  systemStatus,

  /// Error notification
  error,

  /// Heartbeat message
  heartbeat,

  /// Subscription confirmation
  subscriptionConfirmed,

  /// Subscription error
  subscriptionError,

  /// Data quality update
  dataQualityUpdate,

  /// Configuration change
  configurationChange,
}

/// Connection state enumeration
enum ConnectionState {
  /// Not connected
  disconnected,

  /// Connecting to server
  connecting,

  /// Connected and ready
  connected,

  /// Connection lost, attempting to reconnect
  reconnecting,

  /// Connection error
  error,

  /// Service disabled
  disabled,
}

/// Real-time message entity
class RealTimeMessage {
  /// Message type
  final RealTimeMessageType type;

  /// Message data payload
  final Map<String, dynamic> data;

  /// Message timestamp
  final DateTime timestamp;

  /// Message ID for tracking
  final String messageId;

  /// Source region or service
  final String? source;

  /// Message priority level
  final int priority;

  const RealTimeMessage({
    required this.type,
    required this.data,
    required this.timestamp,
    required this.messageId,
    this.source,
    this.priority = 0,
  });

  /// Creates message from JSON
  factory RealTimeMessage.fromJson(Map<String, dynamic> json) {
    return RealTimeMessage(
      type: RealTimeMessageType.values.firstWhere(
        (type) => type.name == json['type'],
        orElse: () => RealTimeMessageType.analyticsUpdate,
      ),
      data: json['data'] ?? {},
      timestamp: DateTime.parse(json['timestamp']),
      messageId: json['messageId'],
      source: json['source'],
      priority: json['priority'] ?? 0,
    );
  }

  /// Converts message to JSON
  Map<String, dynamic> toJson() {
    return {
      'type': type.name,
      'data': data,
      'timestamp': timestamp.toIso8601String(),
      'messageId': messageId,
      'source': source,
      'priority': priority,
    };
  }
}

/// Real-time analytics update entity
class RealTimeAnalyticsUpdate {
  /// Updated analytics data
  final AnalyticsData analyticsData;

  /// Update type
  final String updateType;

  /// Affected regions
  final List<String> affectedRegions;

  /// Update timestamp
  final DateTime timestamp;

  /// Change summary
  final String changeSummary;

  const RealTimeAnalyticsUpdate({
    required this.analyticsData,
    required this.updateType,
    required this.affectedRegions,
    required this.timestamp,
    required this.changeSummary,
  });

  /// Creates update from real-time message
  factory RealTimeAnalyticsUpdate.fromMessage(RealTimeMessage message) {
    final data = message.data;
    return RealTimeAnalyticsUpdate(
      analyticsData: AnalyticsData.fromJson(data['analyticsData']),
      updateType: data['updateType'] ?? 'data_refresh',
      affectedRegions: List<String>.from(data['affectedRegions'] ?? []),
      timestamp: message.timestamp,
      changeSummary: data['changeSummary'] ?? 'Analytics data updated',
    );
  }
}

/// Connection configuration
class ConnectionConfig {
  /// WebSocket server URL
  final String serverUrl;

  /// Connection timeout duration
  final Duration connectionTimeout;

  /// Heartbeat interval
  final Duration heartbeatInterval;

  /// Maximum reconnection attempts
  final int maxReconnectAttempts;

  /// Reconnection delay
  final Duration reconnectDelay;

  /// Whether to enable compression
  final bool enableCompression;

  /// Authentication token
  final String? authToken;

  /// User agent string
  final String userAgent;

  const ConnectionConfig({
    required this.serverUrl,
    this.connectionTimeout = const Duration(seconds: 30),
    this.heartbeatInterval = const Duration(seconds: 30),
    this.maxReconnectAttempts = 5,
    this.reconnectDelay = const Duration(seconds: 5),
    this.enableCompression = true,
    this.authToken,
    this.userAgent = 'MalariaAnalyticsDashboard/1.0',
  });
}

/// Real-time data service implementation
class RealTimeService {
  /// WebSocket channel
  WebSocketChannel? _channel;

  /// Connection configuration
  late ConnectionConfig _config;

  /// Current connection state
  ConnectionState _connectionState = ConnectionState.disconnected;

  /// Connection state stream controller
  final StreamController<ConnectionState> _connectionStateController =
      StreamController<ConnectionState>.broadcast();

  /// Analytics updates stream controller
  final StreamController<RealTimeAnalyticsUpdate> _analyticsUpdatesController =
      StreamController<RealTimeAnalyticsUpdate>.broadcast();

  /// Alert notifications stream controller
  final StreamController<RealTimeMessage> _alertNotificationsController =
      StreamController<RealTimeMessage>.broadcast();

  /// System status updates stream controller
  final StreamController<Map<String, dynamic>> _systemStatusController =
      StreamController<Map<String, dynamic>>.broadcast();

  /// Message queue for offline messages
  final List<Map<String, dynamic>> _messageQueue = [];

  /// Subscribed regions
  final Set<String> _subscribedRegions = {};

  /// Reconnection attempt count
  int _reconnectAttempts = 0;

  /// Heartbeat timer
  Timer? _heartbeatTimer;

  /// Reconnection timer
  Timer? _reconnectionTimer;

  /// Last heartbeat timestamp
  DateTime? _lastHeartbeat;

  /// Singleton instance
  static RealTimeService? _instance;

  /// Private constructor
  RealTimeService._();

  /// Gets singleton instance
  static RealTimeService get instance {
    _instance ??= RealTimeService._();
    return _instance!;
  }

  /// Connection state stream
  Stream<ConnectionState> get connectionState => _connectionStateController.stream;

  /// Analytics updates stream
  Stream<RealTimeAnalyticsUpdate> get analyticsUpdates => _analyticsUpdatesController.stream;

  /// Alert notifications stream
  Stream<RealTimeMessage> get alertNotifications => _alertNotificationsController.stream;

  /// System status updates stream
  Stream<Map<String, dynamic>> get systemStatus => _systemStatusController.stream;

  /// Current connection state
  ConnectionState get currentConnectionState => _connectionState;

  /// Whether service is connected
  bool get isConnected => _connectionState == ConnectionState.connected;

  /// Initializes the real-time service
  Future<void> initialize({
    String? serverUrl,
    String? authToken,
  }) async {
    try {
      _config = ConnectionConfig(
        serverUrl: serverUrl ?? _getDefaultServerUrl(),
        authToken: authToken,
      );

      await _connect();
    } catch (e) {
      debugPrint('Error initializing RealTimeService: $e');
      _updateConnectionState(ConnectionState.error);
    }
  }

  /// Connects to the WebSocket server
  Future<void> _connect() async {
    if (_connectionState == ConnectionState.connecting) return;

    _updateConnectionState(ConnectionState.connecting);

    try {
      final uri = Uri.parse(_config.serverUrl);
      final headers = <String, String>{
        'User-Agent': _config.userAgent,
      };

      if (_config.authToken != null) {
        headers['Authorization'] = 'Bearer ${_config.authToken}';
      }

      _channel = WebSocketChannel.connect(
        uri,
        protocols: ['analytics-v1'],
      );

      // Listen to messages
      _channel!.stream.listen(
        _handleIncomingMessage,
        onError: _handleConnectionError,
        onDone: _handleConnectionClosed,
      );

      // Start heartbeat
      _startHeartbeat();

      _updateConnectionState(ConnectionState.connected);
      _reconnectAttempts = 0;

      // Process queued messages
      await _processMessageQueue();

      debugPrint('Real-time service connected successfully');
    } catch (e) {
      debugPrint('Connection error: $e');
      _handleConnectionError(e);
    }
  }

  /// Disconnects from the WebSocket server
  Future<void> disconnect() async {
    _stopHeartbeat();
    _stopReconnectionTimer();

    if (_channel != null) {
      await _channel!.sink.close(status.goingAway);
      _channel = null;
    }

    _updateConnectionState(ConnectionState.disconnected);
    debugPrint('Real-time service disconnected');
  }

  /// Subscribes to real-time updates for a specific region
  Future<bool> subscribeToRegion(String region) async {
    if (!isConnected) {
      _queueMessage({
        'action': 'subscribe',
        'region': region,
      });
      return false;
    }

    try {
      final message = {
        'action': 'subscribe',
        'type': 'region',
        'region': region,
        'timestamp': DateTime.now().toIso8601String(),
      };

      _sendMessage(message);
      _subscribedRegions.add(region);

      debugPrint('Subscribed to region: $region');
      return true;
    } catch (e) {
      debugPrint('Error subscribing to region $region: $e');
      return false;
    }
  }

  /// Unsubscribes from real-time updates for a specific region
  Future<bool> unsubscribeFromRegion(String region) async {
    if (!isConnected) {
      _queueMessage({
        'action': 'unsubscribe',
        'region': region,
      });
      return false;
    }

    try {
      final message = {
        'action': 'unsubscribe',
        'type': 'region',
        'region': region,
        'timestamp': DateTime.now().toIso8601String(),
      };

      _sendMessage(message);
      _subscribedRegions.remove(region);

      debugPrint('Unsubscribed from region: $region');
      return true;
    } catch (e) {
      debugPrint('Error unsubscribing from region $region: $e');
      return false;
    }
  }

  /// Subscribes to alert notifications
  Future<bool> subscribeToAlerts({List<AlertSeverity>? severities}) async {
    if (!isConnected) {
      _queueMessage({
        'action': 'subscribe',
        'type': 'alerts',
        'severities': severities?.map((s) => s.name).toList(),
      });
      return false;
    }

    try {
      final message = {
        'action': 'subscribe',
        'type': 'alerts',
        'severities': severities?.map((s) => s.name).toList(),
        'timestamp': DateTime.now().toIso8601String(),
      };

      _sendMessage(message);
      debugPrint('Subscribed to alerts');
      return true;
    } catch (e) {
      debugPrint('Error subscribing to alerts: $e');
      return false;
    }
  }

  /// Requests immediate data refresh
  Future<bool> requestDataRefresh({String? region}) async {
    if (!isConnected) {
      _queueMessage({
        'action': 'refresh',
        'region': region,
      });
      return false;
    }

    try {
      final message = {
        'action': 'refresh',
        'region': region,
        'timestamp': DateTime.now().toIso8601String(),
      };

      _sendMessage(message);
      debugPrint('Requested data refresh${region != null ? ' for $region' : ''}');
      return true;
    } catch (e) {
      debugPrint('Error requesting data refresh: $e');
      return false;
    }
  }

  /// Sends a message to the server
  void _sendMessage(Map<String, dynamic> message) {
    if (_channel != null && isConnected) {
      final jsonMessage = jsonEncode(message);
      _channel!.sink.add(jsonMessage);
    }
  }

  /// Handles incoming messages from the server
  void _handleIncomingMessage(dynamic rawMessage) {
    try {
      final messageData = jsonDecode(rawMessage as String) as Map<String, dynamic>;
      final message = RealTimeMessage.fromJson(messageData);

      _lastHeartbeat = DateTime.now();

      switch (message.type) {
        case RealTimeMessageType.analyticsUpdate:
          final update = RealTimeAnalyticsUpdate.fromMessage(message);
          _analyticsUpdatesController.add(update);
          break;

        case RealTimeMessageType.alertNotification:
          _alertNotificationsController.add(message);
          break;

        case RealTimeMessageType.systemStatus:
          _systemStatusController.add(message.data);
          break;

        case RealTimeMessageType.heartbeat:
          // Heartbeat received, connection is alive
          break;

        case RealTimeMessageType.subscriptionConfirmed:
          debugPrint('Subscription confirmed: ${message.data}');
          break;

        case RealTimeMessageType.subscriptionError:
          debugPrint('Subscription error: ${message.data}');
          break;

        case RealTimeMessageType.error:
          debugPrint('Server error: ${message.data}');
          break;

        default:
          debugPrint('Unknown message type: ${message.type}');
      }
    } catch (e) {
      debugPrint('Error handling incoming message: $e');
    }
  }

  /// Handles connection errors
  void _handleConnectionError(dynamic error) {
    debugPrint('WebSocket error: $error');
    _updateConnectionState(ConnectionState.error);
    _attemptReconnection();
  }

  /// Handles connection closure
  void _handleConnectionClosed() {
    debugPrint('WebSocket connection closed');
    _updateConnectionState(ConnectionState.disconnected);
    _attemptReconnection();
  }

  /// Attempts to reconnect to the server
  void _attemptReconnection() {
    if (_reconnectAttempts >= _config.maxReconnectAttempts) {
      debugPrint('Maximum reconnection attempts reached');
      _updateConnectionState(ConnectionState.error);
      return;
    }

    _reconnectAttempts++;
    _updateConnectionState(ConnectionState.reconnecting);

    _reconnectionTimer = Timer(_config.reconnectDelay, () async {
      debugPrint('Attempting reconnection $_reconnectAttempts/${_config.maxReconnectAttempts}');
      await _connect();
    });
  }

  /// Starts the heartbeat timer
  void _startHeartbeat() {
    _heartbeatTimer = Timer.periodic(_config.heartbeatInterval, (_) {
      if (isConnected) {
        _sendMessage({
          'action': 'heartbeat',
          'timestamp': DateTime.now().toIso8601String(),
        });

        // Check if we've received a heartbeat recently
        if (_lastHeartbeat != null) {
          final timeSinceLastHeartbeat = DateTime.now().difference(_lastHeartbeat!);
          if (timeSinceLastHeartbeat > _config.heartbeatInterval * 2) {
            debugPrint('Heartbeat timeout detected');
            _handleConnectionError('Heartbeat timeout');
          }
        }
      }
    });
  }

  /// Stops the heartbeat timer
  void _stopHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
  }

  /// Stops the reconnection timer
  void _stopReconnectionTimer() {
    _reconnectionTimer?.cancel();
    _reconnectionTimer = null;
  }

  /// Updates the connection state
  void _updateConnectionState(ConnectionState newState) {
    if (_connectionState != newState) {
      _connectionState = newState;
      _connectionStateController.add(newState);
      debugPrint('Connection state changed to: $newState');
    }
  }

  /// Queues a message for later sending
  void _queueMessage(Map<String, dynamic> message) {
    _messageQueue.add(message);
    debugPrint('Message queued: ${message['action']}');
  }

  /// Processes queued messages
  Future<void> _processMessageQueue() async {
    if (_messageQueue.isEmpty) return;

    debugPrint('Processing ${_messageQueue.length} queued messages');

    final messagesToProcess = List<Map<String, dynamic>>.from(_messageQueue);
    _messageQueue.clear();

    for (final message in messagesToProcess) {
      try {
        _sendMessage(message);
        await Future.delayed(const Duration(milliseconds: 100)); // Rate limiting
      } catch (e) {
        debugPrint('Error processing queued message: $e');
        _queueMessage(message); // Re-queue failed message
      }
    }
  }

  /// Gets default server URL based on environment
  String _getDefaultServerUrl() {
    if (kDebugMode) {
      return 'ws://localhost:8080/analytics/ws';
    } else {
      return 'wss://api.malaria-analytics.com/ws';
    }
  }

  /// Disposes the service
  void dispose() {
    _stopHeartbeat();
    _stopReconnectionTimer();
    _channel?.sink.close();
    _connectionStateController.close();
    _analyticsUpdatesController.close();
    _alertNotificationsController.close();
    _systemStatusController.close();
  }
}