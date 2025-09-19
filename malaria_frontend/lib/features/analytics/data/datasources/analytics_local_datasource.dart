/// Local data source for analytics data caching and offline access
///
/// This data source handles local storage of analytics data using Hive
/// for efficient caching, offline access, and performance optimization.
/// It provides comprehensive caching strategies for different types of analytics data.
///
/// Usage:
/// ```dart
/// // Cache analytics data
/// await localDataSource.cacheAnalyticsData(analyticsData);
///
/// // Retrieve cached data
/// final cachedData = await localDataSource.getCachedAnalyticsData(
///   region: 'Kenya',
///   startDate: startDate,
///   endDate: endDate,
/// );
/// ```
library;

import 'dart:convert';
import 'package:hive/hive.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../../core/errors/exceptions.dart';
import '../models/analytics_data_model.dart';

/// Abstract interface for analytics local data source
abstract class AnalyticsLocalDataSource {
  /// Caches comprehensive analytics data for offline access
  ///
  /// Parameters:
  /// - [analyticsData]: Analytics data model to cache
  /// - [ttl]: Time-to-live for cached data in hours (default: 24)
  ///
  /// Throws:
  /// - [CacheException]: If caching operation fails
  Future<void> cacheAnalyticsData(
    AnalyticsDataModel analyticsData, {
    int ttl = 24,
  });

  /// Retrieves cached analytics data for specified parameters
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [startDate]: Start date for analytics data
  /// - [endDate]: End date for analytics data
  ///
  /// Returns:
  /// - AnalyticsDataModel if cached data exists and is valid
  /// - null if no valid cached data found
  ///
  /// Throws:
  /// - [CacheException]: If cache retrieval fails
  Future<AnalyticsDataModel?> getCachedAnalyticsData({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
  });

  /// Caches prediction accuracy metrics
  ///
  /// Parameters:
  /// - [accuracyData]: Prediction accuracy model to cache
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for the accuracy data
  /// - [ttl]: Time-to-live for cached data in hours
  ///
  /// Throws:
  /// - [CacheException]: If caching operation fails
  Future<void> cachePredictionAccuracy(
    PredictionAccuracyModel accuracyData,
    String region,
    String dateRange, {
    int ttl = 24,
  });

  /// Retrieves cached prediction accuracy metrics
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for the accuracy data
  ///
  /// Returns:
  /// - PredictionAccuracyModel if cached data exists and is valid
  /// - null if no valid cached data found
  ///
  /// Throws:
  /// - [CacheException]: If cache retrieval fails
  Future<PredictionAccuracyModel?> getCachedPredictionAccuracy(
    String region,
    String dateRange,
  );

  /// Caches environmental trend data
  ///
  /// Parameters:
  /// - [trends]: List of environmental trend models to cache
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for the trend data
  /// - [ttl]: Time-to-live for cached data in hours
  ///
  /// Throws:
  /// - [CacheException]: If caching operation fails
  Future<void> cacheEnvironmentalTrends(
    List<EnvironmentalTrendModel> trends,
    String region,
    String dateRange, {
    int ttl = 12,
  });

  /// Retrieves cached environmental trend data
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for the trend data
  ///
  /// Returns:
  /// - List of EnvironmentalTrendModel if cached data exists
  /// - null if no valid cached data found
  ///
  /// Throws:
  /// - [CacheException]: If cache retrieval fails
  Future<List<EnvironmentalTrendModel>?> getCachedEnvironmentalTrends(
    String region,
    String dateRange,
  );

  /// Caches risk trend data
  ///
  /// Parameters:
  /// - [trends]: List of risk trend models to cache
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for the trend data
  /// - [ttl]: Time-to-live for cached data in hours
  ///
  /// Throws:
  /// - [CacheException]: If caching operation fails
  Future<void> cacheRiskTrends(
    List<RiskTrendModel> trends,
    String region,
    String dateRange, {
    int ttl = 6,
  });

  /// Retrieves cached risk trend data
  ///
  /// Parameters:
  /// - [region]: Geographic region identifier
  /// - [dateRange]: Date range for the trend data
  ///
  /// Returns:
  /// - List of RiskTrendModel if cached data exists
  /// - null if no valid cached data found
  ///
  /// Throws:
  /// - [CacheException]: If cache retrieval fails
  Future<List<RiskTrendModel>?> getCachedRiskTrends(
    String region,
    String dateRange,
  );

  /// Caches chart data for visualization
  ///
  /// Parameters:
  /// - [chartData]: Chart data to cache
  /// - [chartKey]: Unique key identifying the chart configuration
  /// - [ttl]: Time-to-live for cached data in hours
  ///
  /// Throws:
  /// - [CacheException]: If caching operation fails
  Future<void> cacheChartData(
    Map<String, dynamic> chartData,
    String chartKey, {
    int ttl = 6,
  });

  /// Retrieves cached chart data
  ///
  /// Parameters:
  /// - [chartKey]: Unique key identifying the chart configuration
  ///
  /// Returns:
  /// - Map containing chart data if cached data exists
  /// - null if no valid cached data found
  ///
  /// Throws:
  /// - [CacheException]: If cache retrieval fails
  Future<Map<String, dynamic>?> getCachedChartData(String chartKey);

  /// Caches available regions list
  ///
  /// Parameters:
  /// - [regions]: List of available regions
  /// - [ttl]: Time-to-live for cached data in hours
  ///
  /// Throws:
  /// - [CacheException]: If caching operation fails
  Future<void> cacheAvailableRegions(
    List<String> regions, {
    int ttl = 168, // 1 week
  });

  /// Retrieves cached available regions
  ///
  /// Returns:
  /// - List of available regions if cached data exists
  /// - null if no valid cached data found
  ///
  /// Throws:
  /// - [CacheException]: If cache retrieval fails
  Future<List<String>?> getCachedAvailableRegions();

  /// Clears expired cache entries
  ///
  /// Removes all cached data that has exceeded its time-to-live
  /// to free up storage space and maintain data freshness
  ///
  /// Throws:
  /// - [CacheException]: If cache cleanup fails
  Future<void> clearExpiredCache();

  /// Clears all cached analytics data
  ///
  /// Removes all analytics-related cached data for complete cache reset
  ///
  /// Throws:
  /// - [CacheException]: If cache clearing fails
  Future<void> clearAllCache();

  /// Gets cache size and statistics
  ///
  /// Returns:
  /// - Map containing cache size, entry count, and other statistics
  ///
  /// Throws:
  /// - [CacheException]: If cache statistics retrieval fails
  Future<Map<String, dynamic>> getCacheStatistics();
}

/// Concrete implementation of analytics local data source using Hive
class AnalyticsLocalDataSourceImpl implements AnalyticsLocalDataSource {
  /// Hive box for storing analytics data
  final Box<String> _analyticsBox;

  /// Hive box for storing chart data
  final Box<String> _chartBox;

  /// Hive box for storing metadata and cache information
  final Box<String> _metadataBox;

  /// Shared preferences for simple key-value storage
  final SharedPreferences _sharedPreferences;

  /// Constructor requiring Hive boxes and shared preferences
  const AnalyticsLocalDataSourceImpl({
    required Box<String> analyticsBox,
    required Box<String> chartBox,
    required Box<String> metadataBox,
    required SharedPreferences sharedPreferences,
  })  : _analyticsBox = analyticsBox,
        _chartBox = chartBox,
        _metadataBox = metadataBox,
        _sharedPreferences = sharedPreferences;

  @override
  Future<void> cacheAnalyticsData(
    AnalyticsDataModel analyticsData, {
    int ttl = 24,
  }) async {
    try {
      final cacheKey = _generateAnalyticsCacheKey(
        analyticsData.region,
        analyticsData.dateRange.start,
        analyticsData.dateRange.end,
      );

      final cacheEntry = CacheEntry(
        data: jsonEncode(analyticsData.toJson()),
        expiresAt: DateTime.now().add(Duration(hours: ttl)),
        cachedAt: DateTime.now(),
        dataType: 'analytics_data',
      );

      await _analyticsBox.put(cacheKey, jsonEncode(cacheEntry.toJson()));

      // Update cache metadata
      await _updateCacheMetadata('analytics_data', cacheKey, cacheEntry);
    } catch (e) {
      throw CacheException(
        'Failed to cache analytics data: ${e.toString()}',
      );
    }
  }

  @override
  Future<AnalyticsDataModel?> getCachedAnalyticsData({
    required String region,
    required DateTime startDate,
    required DateTime endDate,
  }) async {
    try {
      final cacheKey = _generateAnalyticsCacheKey(region, startDate, endDate);
      final cachedData = _analyticsBox.get(cacheKey);

      if (cachedData == null) {
        return null;
      }

      final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));

      // Check if cache entry has expired
      if (cacheEntry.expiresAt.isBefore(DateTime.now())) {
        await _analyticsBox.delete(cacheKey);
        return null;
      }

      final analyticsData = AnalyticsDataModel.fromJson(
        jsonDecode(cacheEntry.data),
      );

      return analyticsData;
    } catch (e) {
      throw CacheException(
        'Failed to retrieve cached analytics data: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> cachePredictionAccuracy(
    PredictionAccuracyModel accuracyData,
    String region,
    String dateRange, {
    int ttl = 24,
  }) async {
    try {
      final cacheKey = 'prediction_accuracy_${region}_$dateRange';

      final cacheEntry = CacheEntry(
        data: jsonEncode(accuracyData.toJson()),
        expiresAt: DateTime.now().add(Duration(hours: ttl)),
        cachedAt: DateTime.now(),
        dataType: 'prediction_accuracy',
      );

      await _analyticsBox.put(cacheKey, jsonEncode(cacheEntry.toJson()));
      await _updateCacheMetadata('prediction_accuracy', cacheKey, cacheEntry);
    } catch (e) {
      throw CacheException(
        'Failed to cache prediction accuracy: ${e.toString()}',
      );
    }
  }

  @override
  Future<PredictionAccuracyModel?> getCachedPredictionAccuracy(
    String region,
    String dateRange,
  ) async {
    try {
      final cacheKey = 'prediction_accuracy_${region}_$dateRange';
      final cachedData = _analyticsBox.get(cacheKey);

      if (cachedData == null) {
        return null;
      }

      final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));

      if (cacheEntry.expiresAt.isBefore(DateTime.now())) {
        await _analyticsBox.delete(cacheKey);
        return null;
      }

      return PredictionAccuracyModel.fromJson(jsonDecode(cacheEntry.data));
    } catch (e) {
      throw CacheException(
        'Failed to retrieve cached prediction accuracy: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> cacheEnvironmentalTrends(
    List<EnvironmentalTrendModel> trends,
    String region,
    String dateRange, {
    int ttl = 12,
  }) async {
    try {
      final cacheKey = 'environmental_trends_${region}_$dateRange';

      final trendsJson = trends.map((trend) => trend.toJson()).toList();
      final cacheEntry = CacheEntry(
        data: jsonEncode(trendsJson),
        expiresAt: DateTime.now().add(Duration(hours: ttl)),
        cachedAt: DateTime.now(),
        dataType: 'environmental_trends',
      );

      await _analyticsBox.put(cacheKey, jsonEncode(cacheEntry.toJson()));
      await _updateCacheMetadata('environmental_trends', cacheKey, cacheEntry);
    } catch (e) {
      throw CacheException(
        'Failed to cache environmental trends: ${e.toString()}',
      );
    }
  }

  @override
  Future<List<EnvironmentalTrendModel>?> getCachedEnvironmentalTrends(
    String region,
    String dateRange,
  ) async {
    try {
      final cacheKey = 'environmental_trends_${region}_$dateRange';
      final cachedData = _analyticsBox.get(cacheKey);

      if (cachedData == null) {
        return null;
      }

      final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));

      if (cacheEntry.expiresAt.isBefore(DateTime.now())) {
        await _analyticsBox.delete(cacheKey);
        return null;
      }

      final trendsJson = jsonDecode(cacheEntry.data) as List<dynamic>;
      return trendsJson
          .map((json) => EnvironmentalTrendModel.fromJson(json))
          .toList();
    } catch (e) {
      throw CacheException(
        'Failed to retrieve cached environmental trends: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> cacheRiskTrends(
    List<RiskTrendModel> trends,
    String region,
    String dateRange, {
    int ttl = 6,
  }) async {
    try {
      final cacheKey = 'risk_trends_${region}_$dateRange';

      final trendsJson = trends.map((trend) => trend.toJson()).toList();
      final cacheEntry = CacheEntry(
        data: jsonEncode(trendsJson),
        expiresAt: DateTime.now().add(Duration(hours: ttl)),
        cachedAt: DateTime.now(),
        dataType: 'risk_trends',
      );

      await _analyticsBox.put(cacheKey, jsonEncode(cacheEntry.toJson()));
      await _updateCacheMetadata('risk_trends', cacheKey, cacheEntry);
    } catch (e) {
      throw CacheException(
        'Failed to cache risk trends: ${e.toString()}',
      );
    }
  }

  @override
  Future<List<RiskTrendModel>?> getCachedRiskTrends(
    String region,
    String dateRange,
  ) async {
    try {
      final cacheKey = 'risk_trends_${region}_$dateRange';
      final cachedData = _analyticsBox.get(cacheKey);

      if (cachedData == null) {
        return null;
      }

      final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));

      if (cacheEntry.expiresAt.isBefore(DateTime.now())) {
        await _analyticsBox.delete(cacheKey);
        return null;
      }

      final trendsJson = jsonDecode(cacheEntry.data) as List<dynamic>;
      return trendsJson
          .map((json) => RiskTrendModel.fromJson(json))
          .toList();
    } catch (e) {
      throw CacheException(
        'Failed to retrieve cached risk trends: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> cacheChartData(
    Map<String, dynamic> chartData,
    String chartKey, {
    int ttl = 6,
  }) async {
    try {
      final cacheEntry = CacheEntry(
        data: jsonEncode(chartData),
        expiresAt: DateTime.now().add(Duration(hours: ttl)),
        cachedAt: DateTime.now(),
        dataType: 'chart_data',
      );

      await _chartBox.put(chartKey, jsonEncode(cacheEntry.toJson()));
      await _updateCacheMetadata('chart_data', chartKey, cacheEntry);
    } catch (e) {
      throw CacheException(
        'Failed to cache chart data: ${e.toString()}',
      );
    }
  }

  @override
  Future<Map<String, dynamic>?> getCachedChartData(String chartKey) async {
    try {
      final cachedData = _chartBox.get(chartKey);

      if (cachedData == null) {
        return null;
      }

      final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));

      if (cacheEntry.expiresAt.isBefore(DateTime.now())) {
        await _chartBox.delete(chartKey);
        return null;
      }

      return jsonDecode(cacheEntry.data) as Map<String, dynamic>;
    } catch (e) {
      throw CacheException(
        'Failed to retrieve cached chart data: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> cacheAvailableRegions(
    List<String> regions, {
    int ttl = 168,
  }) async {
    try {
      const cacheKey = 'available_regions';

      final cacheEntry = CacheEntry(
        data: jsonEncode(regions),
        expiresAt: DateTime.now().add(Duration(hours: ttl)),
        cachedAt: DateTime.now(),
        dataType: 'available_regions',
      );

      await _metadataBox.put(cacheKey, jsonEncode(cacheEntry.toJson()));
    } catch (e) {
      throw CacheException(
        'Failed to cache available regions: ${e.toString()}',
      );
    }
  }

  @override
  Future<List<String>?> getCachedAvailableRegions() async {
    try {
      const cacheKey = 'available_regions';
      final cachedData = _metadataBox.get(cacheKey);

      if (cachedData == null) {
        return null;
      }

      final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));

      if (cacheEntry.expiresAt.isBefore(DateTime.now())) {
        await _metadataBox.delete(cacheKey);
        return null;
      }

      final regionsJson = jsonDecode(cacheEntry.data) as List<dynamic>;
      return regionsJson.cast<String>();
    } catch (e) {
      throw CacheException(
        'Failed to retrieve cached regions: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> clearExpiredCache() async {
    try {
      final now = DateTime.now();

      // Clear expired analytics data
      final analyticsKeysToDelete = <String>[];
      for (final key in _analyticsBox.keys) {
        final cachedData = _analyticsBox.get(key);
        if (cachedData != null) {
          try {
            final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));
            if (cacheEntry.expiresAt.isBefore(now)) {
              analyticsKeysToDelete.add(key.toString());
            }
          } catch (e) {
            // Invalid cache entry, mark for deletion
            analyticsKeysToDelete.add(key.toString());
          }
        }
      }

      // Clear expired chart data
      final chartKeysToDelete = <String>[];
      for (final key in _chartBox.keys) {
        final cachedData = _chartBox.get(key);
        if (cachedData != null) {
          try {
            final cacheEntry = CacheEntry.fromJson(jsonDecode(cachedData));
            if (cacheEntry.expiresAt.isBefore(now)) {
              chartKeysToDelete.add(key.toString());
            }
          } catch (e) {
            chartKeysToDelete.add(key.toString());
          }
        }
      }

      // Delete expired entries
      await _analyticsBox.deleteAll(analyticsKeysToDelete);
      await _chartBox.deleteAll(chartKeysToDelete);

      // Update cache statistics
      await _updateCacheStatistics();
    } catch (e) {
      throw CacheException(
        'Failed to clear expired cache: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> clearAllCache() async {
    try {
      await _analyticsBox.clear();
      await _chartBox.clear();
      await _metadataBox.clear();
      await _updateCacheStatistics();
    } catch (e) {
      throw CacheException(
        'Failed to clear all cache: ${e.toString()}',
      );
    }
  }

  @override
  Future<Map<String, dynamic>> getCacheStatistics() async {
    try {
      final analyticsSize = _analyticsBox.length;
      final chartSize = _chartBox.length;
      final metadataSize = _metadataBox.length;

      final totalSize = analyticsSize + chartSize + metadataSize;

      return {
        'total_entries': totalSize,
        'analytics_entries': analyticsSize,
        'chart_entries': chartSize,
        'metadata_entries': metadataSize,
        'last_cleanup': _sharedPreferences.getString('last_cache_cleanup'),
        'cache_hit_rate': _sharedPreferences.getDouble('cache_hit_rate') ?? 0.0,
        'total_cache_requests': _sharedPreferences.getInt('total_cache_requests') ?? 0,
        'cache_hits': _sharedPreferences.getInt('cache_hits') ?? 0,
      };
    } catch (e) {
      throw CacheException(
        'Failed to get cache statistics: ${e.toString()}',
      );
    }
  }

  /// Generates cache key for analytics data
  String _generateAnalyticsCacheKey(
    String region,
    DateTime startDate,
    DateTime endDate,
  ) {
    final startDateStr = startDate.toIso8601String().split('T')[0];
    final endDateStr = endDate.toIso8601String().split('T')[0];
    return 'analytics_${region}_${startDateStr}_$endDateStr';
  }

  /// Updates cache metadata for tracking and statistics
  Future<void> _updateCacheMetadata(
    String dataType,
    String cacheKey,
    CacheEntry cacheEntry,
  ) async {
    try {
      final metadataKey = 'metadata_$dataType';
      final existingMetadata = _metadataBox.get(metadataKey);

      Map<String, dynamic> metadata;
      if (existingMetadata != null) {
        metadata = jsonDecode(existingMetadata) as Map<String, dynamic>;
      } else {
        metadata = {
          'data_type': dataType,
          'entries': <String, dynamic>{},
          'created_at': DateTime.now().toIso8601String(),
        };
      }

      metadata['entries'][cacheKey] = {
        'cached_at': cacheEntry.cachedAt.toIso8601String(),
        'expires_at': cacheEntry.expiresAt.toIso8601String(),
        'data_size': cacheEntry.data.length,
      };

      metadata['updated_at'] = DateTime.now().toIso8601String();

      await _metadataBox.put(metadataKey, jsonEncode(metadata));
    } catch (e) {
      // Non-critical error - log but don't throw
      print('Warning: Failed to update cache metadata: ${e.toString()}');
    }
  }

  /// Updates cache statistics for monitoring
  Future<void> _updateCacheStatistics() async {
    try {
      await _sharedPreferences.setString(
        'last_cache_cleanup',
        DateTime.now().toIso8601String(),
      );
    } catch (e) {
      // Non-critical error - log but don't throw
      print('Warning: Failed to update cache statistics: ${e.toString()}');
    }
  }
}

/// Cache entry model for storing cached data with metadata
class CacheEntry {
  /// Serialized data content
  final String data;

  /// Expiration timestamp
  final DateTime expiresAt;

  /// Cache timestamp
  final DateTime cachedAt;

  /// Type of cached data
  final String dataType;

  const CacheEntry({
    required this.data,
    required this.expiresAt,
    required this.cachedAt,
    required this.dataType,
  });

  /// Creates cache entry from JSON
  factory CacheEntry.fromJson(Map<String, dynamic> json) {
    return CacheEntry(
      data: json['data'] as String,
      expiresAt: DateTime.parse(json['expires_at'] as String),
      cachedAt: DateTime.parse(json['cached_at'] as String),
      dataType: json['data_type'] as String,
    );
  }

  /// Converts cache entry to JSON
  Map<String, dynamic> toJson() {
    return {
      'data': data,
      'expires_at': expiresAt.toIso8601String(),
      'cached_at': cachedAt.toIso8601String(),
      'data_type': dataType,
    };
  }
}