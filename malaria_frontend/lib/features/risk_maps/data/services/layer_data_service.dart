/// Layer Data Service for Multi-Layer Mapping System
///
/// Comprehensive service for managing environmental and infrastructure
/// layer data, including loading, caching, updating, and processing
/// of various data sources for the malaria prediction mapping system.
///
/// Author: Claude AI Agent - Multi-Layer Mapping System
/// Created: 2025-09-19
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../domain/entities/environmental_layer.dart';
import '../../domain/entities/infrastructure_layer.dart';
import '../../domain/entities/map_layer.dart';

/// Comprehensive service for managing layer data across the mapping system
class LayerDataService extends ChangeNotifier {
  static const String _baseApiUrl = 'https://api.malaria-prediction.com/v1';
  static const int _defaultTimeoutSeconds = 30;
  static const int _maxRetryAttempts = 3;

  final http.Client _httpClient;
  final Map<String, LayerCacheEntry> _layerCache = {};
  final Map<String, StreamSubscription> _realtimeSubscriptions = {};
  final Map<String, Timer> _refreshTimers = {};

  /// Constructor with optional HTTP client for testing
  LayerDataService({http.Client? httpClient})
      : _httpClient = httpClient ?? http.Client();

  /// Load environmental layer data from various sources
  Future<EnvironmentalLayer> loadEnvironmentalLayer(String layerId) async {
    const String methodName = 'loadEnvironmentalLayer';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Loading environmental layer: $layerId');

      // Check cache first
      final cachedLayer = _getCachedLayer(layerId);
      if (cachedLayer != null && cachedLayer.isValid) {
        debugPrint('[$methodName] Returning cached layer: $layerId');
        return cachedLayer.data as EnvironmentalLayer;
      }

      // Load from remote source
      final response = await _makeApiRequest(
        'GET',
        '/layers/environmental/$layerId',
        null,
      );

      final layerData = json.decode(response.body) as Map<String, dynamic>;
      final environmentalLayer = _parseEnvironmentalLayerData(layerData);

      // Cache the layer
      _cacheLayer(layerId, environmentalLayer, layerData['cache_duration'] ?? 3600);

      // Set up real-time updates if configured
      if (environmentalLayer.dataSource.refreshInterval != null) {
        _setupRealTimeUpdates(layerId, environmentalLayer.dataSource.refreshInterval!);
      }

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Loaded environmental layer in ${endTime - startTime}ms');

      return environmentalLayer;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error loading environmental layer $layerId: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Load infrastructure layer data from various sources
  Future<InfrastructureLayer> loadInfrastructureLayer(String layerId) async {
    const String methodName = 'loadInfrastructureLayer';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Loading infrastructure layer: $layerId');

      // Check cache first
      final cachedLayer = _getCachedLayer(layerId);
      if (cachedLayer != null && cachedLayer.isValid) {
        debugPrint('[$methodName] Returning cached infrastructure layer: $layerId');
        return cachedLayer.data as InfrastructureLayer;
      }

      // Load from remote source
      final response = await _makeApiRequest(
        'GET',
        '/layers/infrastructure/$layerId',
        null,
      );

      final layerData = json.decode(response.body) as Map<String, dynamic>;
      final infrastructureLayer = _parseInfrastructureLayerData(layerData);

      // Cache the layer
      _cacheLayer(layerId, infrastructureLayer, layerData['cache_duration'] ?? 1800);

      // Set up real-time updates for operational status
      if (infrastructureLayer.operationalStatus.isRealTime) {
        _setupRealTimeUpdates(layerId, 300); // 5 minutes for real-time data
      }

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Loaded infrastructure layer in ${endTime - startTime}ms');

      return infrastructureLayer;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error loading infrastructure layer $layerId: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Load all available environmental layers
  Future<List<EnvironmentalLayer>> loadAllEnvironmentalLayers() async {
    const String methodName = 'loadAllEnvironmentalLayers';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Loading all environmental layers');

      final response = await _makeApiRequest(
        'GET',
        '/layers/environmental',
        null,
      );

      final layersData = json.decode(response.body) as Map<String, dynamic>;
      final layers = <EnvironmentalLayer>[];

      for (final layerData in layersData['layers'] as List) {
        try {
          final layer = _parseEnvironmentalLayerData(layerData);
          layers.add(layer);

          // Cache each layer
          _cacheLayer(layer.id, layer, layerData['cache_duration'] ?? 3600);
        } catch (error) {
          debugPrint('[$methodName] Error parsing environmental layer: $error');
          // Continue with other layers
        }
      }

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Loaded ${layers.length} environmental layers in ${endTime - startTime}ms');

      return layers;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error loading environmental layers: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Load all available infrastructure layers
  Future<List<InfrastructureLayer>> loadAllInfrastructureLayers() async {
    const String methodName = 'loadAllInfrastructureLayers';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Loading all infrastructure layers');

      final response = await _makeApiRequest(
        'GET',
        '/layers/infrastructure',
        null,
      );

      final layersData = json.decode(response.body) as Map<String, dynamic>;
      final layers = <InfrastructureLayer>[];

      for (final layerData in layersData['layers'] as List) {
        try {
          final layer = _parseInfrastructureLayerData(layerData);
          layers.add(layer);

          // Cache each layer
          _cacheLayer(layer.id, layer, layerData['cache_duration'] ?? 1800);
        } catch (error) {
          debugPrint('[$methodName] Error parsing infrastructure layer: $error');
          // Continue with other layers
        }
      }

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Loaded ${layers.length} infrastructure layers in ${endTime - startTime}ms');

      return layers;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error loading infrastructure layers: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Get layer data for a specific geographic region
  Future<Map<String, dynamic>> getLayerDataForRegion({
    required String layerId,
    required double northLat,
    required double southLat,
    required double eastLng,
    required double westLng,
    int? zoomLevel,
  }) async {
    const String methodName = 'getLayerDataForRegion';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Getting layer data for region: $layerId');

      final queryParams = {
        'north': northLat.toString(),
        'south': southLat.toString(),
        'east': eastLng.toString(),
        'west': westLng.toString(),
        if (zoomLevel != null) 'zoom': zoomLevel.toString(),
      };

      final response = await _makeApiRequest(
        'GET',
        '/layers/$layerId/data',
        queryParams,
      );

      final layerData = json.decode(response.body) as Map<String, dynamic>;

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Retrieved layer data in ${endTime - startTime}ms');

      return layerData;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error getting layer data for region: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Update layer configuration and refresh data
  Future<void> updateLayerConfiguration(String layerId, Map<String, dynamic> config) async {
    const String methodName = 'updateLayerConfiguration';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Updating layer configuration: $layerId');

      await _makeApiRequest(
        'PUT',
        '/layers/$layerId/config',
        null,
        body: config,
      );

      // Invalidate cache for this layer
      _invalidateLayerCache(layerId);

      // Notify listeners of configuration change
      notifyListeners();

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Updated layer configuration in ${endTime - startTime}ms');
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error updating layer configuration: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Load temporal data for environmental layers
  Future<Map<DateTime, dynamic>> loadTemporalData({
    required String layerId,
    required DateTime startDate,
    required DateTime endDate,
    String? aggregation,
  }) async {
    const String methodName = 'loadTemporalData';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Loading temporal data for layer: $layerId');

      final queryParams = {
        'start_date': startDate.toIso8601String(),
        'end_date': endDate.toIso8601String(),
        if (aggregation != null) 'aggregation': aggregation,
      };

      final response = await _makeApiRequest(
        'GET',
        '/layers/$layerId/temporal',
        queryParams,
      );

      final temporalData = json.decode(response.body) as Map<String, dynamic>;
      final result = <DateTime, dynamic>{};

      for (final entry in temporalData['data'] as List) {
        final timestamp = DateTime.parse(entry['timestamp']);
        result[timestamp] = entry['value'];
      }

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Loaded temporal data in ${endTime - startTime}ms');

      return result;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error loading temporal data: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Get layer statistics and metadata
  Future<LayerStatistics> getLayerStatistics(String layerId) async {
    const String methodName = 'getLayerStatistics';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Getting layer statistics: $layerId');

      final response = await _makeApiRequest(
        'GET',
        '/layers/$layerId/statistics',
        null,
      );

      final statsData = json.decode(response.body) as Map<String, dynamic>;
      final statistics = _parseLayerStatistics(statsData);

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Retrieved layer statistics in ${endTime - startTime}ms');

      return statistics;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error getting layer statistics: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Export layer data in various formats
  Future<Uint8List> exportLayerData({
    required String layerId,
    required String format, // 'geojson', 'csv', 'kml', 'shapefile'
    Map<String, dynamic>? filters,
  }) async {
    const String methodName = 'exportLayerData';
    final int startTime = DateTime.now().millisecondsSinceEpoch;

    try {
      debugPrint('[$methodName] Exporting layer data: $layerId as $format');

      final body = {
        'format': format,
        if (filters != null) 'filters': filters,
      };

      final response = await _makeApiRequest(
        'POST',
        '/layers/$layerId/export',
        null,
        body: body,
        expectBinaryResponse: true,
      );

      final int endTime = DateTime.now().millisecondsSinceEpoch;
      debugPrint('[$methodName] Exported layer data in ${endTime - startTime}ms');

      return response.bodyBytes;
    } catch (error, stackTrace) {
      debugPrint('[$methodName] Error exporting layer data: $error');
      debugPrint('[$methodName] Stack trace: $stackTrace');
      rethrow;
    }
  }

  /// Clear cache for all layers
  void clearCache() {
    const String methodName = 'clearCache';
    debugPrint('[$methodName] Clearing all layer cache');

    _layerCache.clear();
    notifyListeners();
  }

  /// Get cache statistics
  Map<String, dynamic> getCacheStatistics() {
    final totalEntries = _layerCache.length;
    final validEntries = _layerCache.values.where((entry) => entry.isValid).length;
    final totalSizeBytes = _layerCache.values.fold<int>(
      0,
      (sum, entry) => sum + entry.sizeBytes,
    );

    return {
      'total_entries': totalEntries,
      'valid_entries': validEntries,
      'expired_entries': totalEntries - validEntries,
      'total_size_bytes': totalSizeBytes,
      'total_size_mb': (totalSizeBytes / (1024 * 1024)).toStringAsFixed(2),
    };
  }

  /// Dispose of resources
  @override
  void dispose() {
    const String methodName = 'dispose';
    debugPrint('[$methodName] Disposing LayerDataService');

    // Cancel all real-time subscriptions
    for (final subscription in _realtimeSubscriptions.values) {
      subscription.cancel();
    }
    _realtimeSubscriptions.clear();

    // Cancel all refresh timers
    for (final timer in _refreshTimers.values) {
      timer.cancel();
    }
    _refreshTimers.clear();

    // Close HTTP client
    _httpClient.close();

    super.dispose();
  }

  // Private helper methods

  /// Make API request with retry logic and error handling
  Future<http.Response> _makeApiRequest(
    String method,
    String endpoint,
    Map<String, String>? queryParams, {
    Map<String, dynamic>? body,
    bool expectBinaryResponse = false,
  }) async {
    const String methodName = '_makeApiRequest';

    Uri url = Uri.parse('$_baseApiUrl$endpoint');
    if (queryParams != null && queryParams.isNotEmpty) {
      url = url.replace(queryParameters: queryParams);
    }

    for (int attempt = 1; attempt <= _maxRetryAttempts; attempt++) {
      try {
        debugPrint('[$methodName] $method $url (attempt $attempt)');

        late http.Response response;

        switch (method.toUpperCase()) {
          case 'GET':
            response = await _httpClient.get(url).timeout(
              const Duration(seconds: _defaultTimeoutSeconds),
            );
            break;
          case 'POST':
            response = await _httpClient
                .post(
                  url,
                  headers: {'Content-Type': 'application/json'},
                  body: body != null ? json.encode(body) : null,
                )
                .timeout(const Duration(seconds: _defaultTimeoutSeconds));
            break;
          case 'PUT':
            response = await _httpClient
                .put(
                  url,
                  headers: {'Content-Type': 'application/json'},
                  body: body != null ? json.encode(body) : null,
                )
                .timeout(const Duration(seconds: _defaultTimeoutSeconds));
            break;
          default:
            throw UnsupportedError('HTTP method $method not supported');
        }

        if (response.statusCode >= 200 && response.statusCode < 300) {
          return response;
        } else if (response.statusCode >= 400 && response.statusCode < 500) {
          // Client error - don't retry
          throw LayerDataException(
            'Client error: ${response.statusCode} - ${response.body}',
            response.statusCode,
          );
        } else {
          // Server error - retry
          throw LayerDataException(
            'Server error: ${response.statusCode} - ${response.body}',
            response.statusCode,
          );
        }
      } catch (error) {
        if (attempt == _maxRetryAttempts || error is LayerDataException) {
          rethrow;
        }

        // Wait before retry with exponential backoff
        await Future.delayed(Duration(seconds: attempt * 2));
      }
    }

    throw LayerDataException('Max retry attempts exceeded', 500);
  }

  /// Parse environmental layer data from API response
  EnvironmentalLayer _parseEnvironmentalLayerData(Map<String, dynamic> data) {
    // This is a simplified version - in a real implementation,
    // you would parse all the complex nested structures
    return EnvironmentalLayer(
      id: data['id'],
      name: data['name'],
      description: data['description'],
      dataType: EnvironmentalDataType.values.firstWhere(
        (type) => type.name == data['data_type'],
        orElse: () => EnvironmentalDataType.temperature,
      ),
      isVisible: data['is_visible'] ?? true,
      opacity: (data['opacity'] ?? 1.0).toDouble(),
      zIndex: data['z_index'] ?? 0,
      dataSource: _parseEnvironmentalDataSource(data['data_source']),
      visualizationStyle: _parseEnvironmentalVisualizationStyle(data['visualization_style']),
      colorMapping: _parseEnvironmentalColorMapping(data['color_mapping']),
      temporalConfig: data['temporal_config'] != null
          ? _parseTemporalConfiguration(data['temporal_config'])
          : null,
      qualityInfo: _parseDataQualityInfo(data['quality_info']),
      statistics: _parseEnvironmentalStatistics(data['statistics']),
      metadata: Map<String, dynamic>.from(data['metadata'] ?? {}),
    );
  }

  /// Parse infrastructure layer data from API response
  InfrastructureLayer _parseInfrastructureLayerData(Map<String, dynamic> data) {
    // Simplified parsing - implement full parsing as needed
    return InfrastructureLayer(
      id: data['id'],
      name: data['name'],
      description: data['description'],
      infrastructureType: InfrastructureType.values.firstWhere(
        (type) => type.name == data['infrastructure_type'],
        orElse: () => InfrastructureType.healthcare,
      ),
      isVisible: data['is_visible'] ?? true,
      opacity: (data['opacity'] ?? 1.0).toDouble(),
      zIndex: data['z_index'] ?? 0,
      dataSource: _parseInfrastructureDataSource(data['data_source']),
      visualizationStyle: _parseInfrastructureVisualizationStyle(data['visualization_style']),
      facilityConfig: _parseFacilityConfiguration(data['facility_config']),
      coverageInfo: _parseServiceCoverageInfo(data['coverage_info']),
      accessibilityInfo: _parseAccessibilityInfo(data['accessibility_info']),
      operationalStatus: _parseOperationalStatus(data['operational_status']),
      metrics: _parseInfrastructureMetrics(data['metrics']),
      metadata: Map<String, dynamic>.from(data['metadata'] ?? {}),
    );
  }

  // Additional helper methods for parsing complex nested structures
  // These would be fully implemented with proper error handling

  EnvironmentalDataSource _parseEnvironmentalDataSource(Map<String, dynamic> data) {
    return EnvironmentalDataSource(
      url: data['url'],
      format: data['format'],
      provider: data['provider'],
      refreshInterval: data['refresh_interval'],
      fieldMappings: Map<String, String>.from(data['field_mappings'] ?? {}),
      qualityAssessment: data['quality_assessment'] ?? '',
      spatialResolution: (data['spatial_resolution'] ?? 1.0).toDouble(),
      temporalResolution: data['temporal_resolution'] ?? 'daily',
    );
  }

  // ... Additional parsing methods would be implemented here

  /// Cache management methods
  LayerCacheEntry? _getCachedLayer(String layerId) {
    return _layerCache[layerId];
  }

  void _cacheLayer(String layerId, dynamic layerData, int cacheDurationSeconds) {
    _layerCache[layerId] = LayerCacheEntry(
      data: layerData,
      timestamp: DateTime.now(),
      duration: Duration(seconds: cacheDurationSeconds),
      sizeBytes: _estimateDataSize(layerData),
    );
  }

  void _invalidateLayerCache(String layerId) {
    _layerCache.remove(layerId);
  }

  int _estimateDataSize(dynamic data) {
    // Simple size estimation - could be more sophisticated
    try {
      return json.encode(data).length * 2; // Rough estimate including overhead
    } catch (e) {
      return 1024; // Default fallback
    }
  }

  /// Set up real-time updates for dynamic layers
  void _setupRealTimeUpdates(String layerId, int intervalSeconds) {
    // Cancel existing timer if any
    _refreshTimers[layerId]?.cancel();

    _refreshTimers[layerId] = Timer.periodic(
      Duration(seconds: intervalSeconds),
      (timer) async {
        try {
          // Invalidate cache to force reload
          _invalidateLayerCache(layerId);

          // Notify listeners that data may have changed
          notifyListeners();
        } catch (error) {
          debugPrint('Error in real-time update for layer $layerId: $error');
        }
      },
    );
  }

  // Placeholder implementations for parsing methods
  // These would be fully implemented based on the actual API structure

  EnvironmentalVisualizationStyle _parseEnvironmentalVisualizationStyle(Map<String, dynamic> data) {
    return const EnvironmentalVisualizationStyle(
      renderingType: EnvironmentalRenderingType.heatmap,
      strokeWidth: 1.0,
      borderColor: Colors.black,
      highlightColor: Colors.blue,
      transparency: 0.3,
      smoothing: 0.5,
      enableAnimations: false,
    );
  }

  EnvironmentalColorMapping _parseEnvironmentalColorMapping(Map<String, dynamic> data) {
    return EnvironmentalColorMapping(
      primaryColor: Colors.blue,
      secondaryColor: Colors.red,
      gradient: [Colors.blue, Colors.green, Colors.yellow, Colors.orange, Colors.red],
      steps: 5,
      noDataColor: Colors.grey,
      scaleType: ColorScaleType.linear,
      invertScale: false,
    );
  }

  TemporalConfiguration _parseTemporalConfiguration(Map<String, dynamic> data) {
    return TemporalConfiguration(
      startDate: DateTime.parse(data['start_date']),
      endDate: DateTime.parse(data['end_date']),
      currentTime: DateTime.parse(data['current_time']),
      timeStep: data['time_step'] ?? 86400000, // 1 day in milliseconds
      enableAnimation: data['enable_animation'] ?? false,
      loopMode: TemporalLoopMode.values.firstWhere(
        (mode) => mode.name == data['loop_mode'],
        orElse: () => TemporalLoopMode.loop,
      ),
    );
  }

  DataQualityInfo _parseDataQualityInfo(Map<String, dynamic> data) {
    return DataQualityInfo(
      level: DataQualityLevel.values.firstWhere(
        (level) => level.name == data['level'],
        orElse: () => DataQualityLevel.medium,
      ),
      accuracy: (data['accuracy'] ?? 0.8).toDouble(),
      completeness: (data['completeness'] ?? 0.9).toDouble(),
      freshness: Duration(hours: data['freshness_hours'] ?? 24),
      notes: data['notes'] ?? '',
    );
  }

  EnvironmentalStatistics _parseEnvironmentalStatistics(Map<String, dynamic> data) {
    return EnvironmentalStatistics(
      minValue: (data['min_value'] ?? 0.0).toDouble(),
      maxValue: (data['max_value'] ?? 100.0).toDouble(),
      meanValue: (data['mean_value'] ?? 50.0).toDouble(),
      standardDeviation: (data['standard_deviation'] ?? 10.0).toDouble(),
      unit: data['unit'] ?? '',
      dataPoints: data['data_points'] ?? 0,
      missingDataPercentage: (data['missing_data_percentage'] ?? 0.0).toDouble(),
    );
  }

  // Infrastructure parsing methods - simplified implementations
  InfrastructureDataSource _parseInfrastructureDataSource(Map<String, dynamic> data) {
    return InfrastructureDataSource(
      url: data['url'],
      format: data['format'],
      provider: data['provider'],
      refreshInterval: data['refresh_interval'],
      fieldMappings: Map<String, String>.from(data['field_mappings'] ?? {}),
      license: data['license'] ?? '',
      accuracy: (data['accuracy'] ?? 0.9).toDouble(),
      lastUpdated: DateTime.parse(data['last_updated'] ?? DateTime.now().toIso8601String()),
    );
  }

  InfrastructureVisualizationStyle _parseInfrastructureVisualizationStyle(Map<String, dynamic> data) {
    return InfrastructureVisualizationStyle(
      renderingType: InfrastructureRenderingType.markers,
      strokeWidth: 2,
      borderColor: Colors.black,
      highlightColor: Colors.blue,
      markerSize: 12,
      labelConfig: LabelConfiguration(
        showLabels: true,
        fontSize: 11,
        textColor: Colors.black,
        backgroundColor: Colors.white,
        minZoomForLabels: 10,
      ),
    );
  }

  // Additional placeholder parsing methods...
  FacilityConfiguration _parseFacilityConfiguration(Map<String, dynamic> data) {
    return FacilityConfiguration(
      primaryColor: Colors.red,
      secondaryColor: Colors.blue,
      categories: const [],
      capacity: const CapacityInfo(totalCapacity: 100, currentLoad: 50, availableCapacity: 50),
      serviceTypes: const ['emergency', 'outpatient'],
      operatingHours: const OperatingHours(
        weekdayHours: '08:00-17:00',
        weekendHours: '08:00-12:00',
        is24Hours: false,
        holidays: [],
      ),
    );
  }

  ServiceCoverageInfo _parseServiceCoverageInfo(Map<String, dynamic> data) {
    return const ServiceCoverageInfo(
      averageRadius: 5.0,
      maxRadius: 10.0,
      populationServed: 10000,
      coveragePercentage: 0.85,
      qualityMetrics: {},
    );
  }

  AccessibilityInfo _parseAccessibilityInfo(Map<String, dynamic> data) {
    return const AccessibilityInfo(
      averageTravelTime: 30.0,
      maxTravelTime: 60.0,
      transportModes: [TransportMode.car, TransportMode.walking],
      roadQuality: RoadQuality.good,
      seasonalAccess: SeasonalAccess(
        drySeasonAccess: true,
        wetSeasonAccess: true,
        restrictedMonths: [],
        alternativeAccess: '',
      ),
    );
  }

  OperationalStatus _parseOperationalStatus(Map<String, dynamic> data) {
    return const OperationalStatus(
      level: OperationalLevel.fullyOperational,
      isRealTime: false,
      lastUpdate: null,
      statusNotes: '',
      capacityUtilization: 0.7,
      maintenance: [],
    );
  }

  InfrastructureMetrics _parseInfrastructureMetrics(Map<String, dynamic> data) {
    return const InfrastructureMetrics(
      utilizationRate: 0.7,
      efficiencyScore: 0.8,
      qualityRating: 4,
      satisfactionScore: 0.85,
      reliability: 0.9,
      trends: {},
    );
  }

  LayerStatistics _parseLayerStatistics(Map<String, dynamic> data) {
    return LayerStatistics(
      totalFeatures: data['total_features'] ?? 0,
      averageValue: (data['average_value'] ?? 0.0).toDouble(),
      minValue: (data['min_value'] ?? 0.0).toDouble(),
      maxValue: (data['max_value'] ?? 0.0).toDouble(),
      lastUpdated: DateTime.parse(data['last_updated'] ?? DateTime.now().toIso8601String()),
      coverage: (data['coverage'] ?? 0.0).toDouble(),
    );
  }
}

/// Cache entry for layer data
class LayerCacheEntry {
  final dynamic data;
  final DateTime timestamp;
  final Duration duration;
  final int sizeBytes;

  LayerCacheEntry({
    required this.data,
    required this.timestamp,
    required this.duration,
    required this.sizeBytes,
  });

  bool get isValid => DateTime.now().difference(timestamp) < duration;
  bool get isExpired => !isValid;
}

/// Layer statistics information
class LayerStatistics {
  final int totalFeatures;
  final double averageValue;
  final double minValue;
  final double maxValue;
  final DateTime lastUpdated;
  final double coverage;

  const LayerStatistics({
    required this.totalFeatures,
    required this.averageValue,
    required this.minValue,
    required this.maxValue,
    required this.lastUpdated,
    required this.coverage,
  });
}

/// Custom exception for layer data operations
class LayerDataException implements Exception {
  final String message;
  final int? statusCode;

  const LayerDataException(this.message, [this.statusCode]);

  @override
  String toString() => 'LayerDataException: $message${statusCode != null ? ' (HTTP $statusCode)' : ''}';
}