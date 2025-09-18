/// Test Fixtures for Malaria Prediction App
/// Provides consistent test data across all test suites
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Centralized test data management for consistent testing

import 'dart:convert';

/// Centralized test fixtures and sample data
class TestFixtures {
  /// Sample user authentication data
  static const Map<String, dynamic> sampleUser = {
    'id': 'user_123456789',
    'email': 'researcher@malaria-prediction.org',
    'name': 'Dr. Sarah Johnson',
    'organization': 'Global Health Research Institute',
    'roles': ['researcher', 'data_analyst', 'report_viewer'],
    'permissions': [
      'view_risk_data',
      'request_predictions',
      'view_analytics',
      'export_data',
      'manage_alerts',
    ],
    'preferences': {
      'theme': 'light',
      'language': 'en',
      'notifications': {
        'push_enabled': true,
        'email_enabled': true,
        'sms_enabled': false,
      },
      'default_region': 'East_Africa',
      'default_prediction_horizon': 14,
    },
    'created_at': '2024-01-15T08:30:00.000Z',
    'last_login': '2025-09-18T14:30:00.000Z',
    'account_status': 'active',
  };

  /// Sample authentication tokens
  static const Map<String, dynamic> sampleTokens = {
    'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'token_type': 'Bearer',
    'expires_in': 3600,
    'refresh_expires_in': 86400,
    'scope': 'read write',
  };

  /// Sample risk assessment data for different regions
  static const List<Map<String, dynamic>> sampleRiskAssessments = [
    {
      'id': 'risk_nairobi_20250918',
      'region': 'Nairobi',
      'country': 'Kenya',
      'coordinates': {
        'latitude': -1.2921,
        'longitude': 36.8219,
      },
      'risk_level': 'medium',
      'risk_score': 0.65,
      'confidence_interval': {
        'lower': 0.45,
        'upper': 0.85,
      },
      'environmental_factors': {
        'temperature_avg': 24.5,
        'temperature_min': 18.2,
        'temperature_max': 30.8,
        'rainfall_mm': 120.0,
        'humidity_percent': 75.0,
        'vegetation_index': 0.8,
        'elevation_m': 1700,
      },
      'population_data': {
        'total_population': 4397073,
        'population_density': 4500,
        'urban_percentage': 95.0,
        'vulnerable_population': 879414,
      },
      'model_metadata': {
        'model_version': '2.1.0',
        'prediction_date': '2025-09-18T12:00:00.000Z',
        'data_sources': ['ERA5', 'CHIRPS', 'MODIS', 'WorldPop'],
        'last_updated': '2025-09-18T08:00:00.000Z',
      },
    },
    {
      'id': 'risk_mombasa_20250918',
      'region': 'Mombasa',
      'country': 'Kenya',
      'coordinates': {
        'latitude': -4.0435,
        'longitude': 39.6682,
      },
      'risk_level': 'high',
      'risk_score': 0.85,
      'confidence_interval': {
        'lower': 0.75,
        'upper': 0.95,
      },
      'environmental_factors': {
        'temperature_avg': 28.5,
        'temperature_min': 22.1,
        'temperature_max': 35.2,
        'rainfall_mm': 180.0,
        'humidity_percent': 85.0,
        'vegetation_index': 0.6,
        'elevation_m': 50,
      },
      'population_data': {
        'total_population': 1208333,
        'population_density': 3000,
        'urban_percentage': 85.0,
        'vulnerable_population': 362500,
      },
      'model_metadata': {
        'model_version': '2.1.0',
        'prediction_date': '2025-09-18T12:00:00.000Z',
        'data_sources': ['ERA5', 'CHIRPS', 'MODIS', 'WorldPop'],
        'last_updated': '2025-09-18T08:00:00.000Z',
      },
    },
  ];

  /// Sample prediction data
  static const Map<String, dynamic> samplePrediction = {
    'id': 'prediction_nairobi_14d_20250918',
    'region': 'Nairobi',
    'coordinates': {
      'latitude': -1.2921,
      'longitude': 36.8219,
    },
    'prediction_horizon_days': 14,
    'generated_at': '2025-09-18T14:30:00.000Z',
    'model_version': '2.1.0',
    'confidence_level': 0.85,
    'predictions': [
      {'date': '2025-09-19', 'risk_score': 0.62, 'confidence': 0.88},
      {'date': '2025-09-20', 'risk_score': 0.65, 'confidence': 0.86},
      {'date': '2025-09-21', 'risk_score': 0.68, 'confidence': 0.84},
      {'date': '2025-09-22', 'risk_score': 0.71, 'confidence': 0.82},
      {'date': '2025-09-23', 'risk_score': 0.74, 'confidence': 0.80},
      {'date': '2025-09-24', 'risk_score': 0.77, 'confidence': 0.78},
      {'date': '2025-09-25', 'risk_score': 0.80, 'confidence': 0.76},
      {'date': '2025-09-26', 'risk_score': 0.78, 'confidence': 0.74},
      {'date': '2025-09-27', 'risk_score': 0.75, 'confidence': 0.76},
      {'date': '2025-09-28', 'risk_score': 0.72, 'confidence': 0.78},
      {'date': '2025-09-29', 'risk_score': 0.69, 'confidence': 0.80},
      {'date': '2025-09-30', 'risk_score': 0.66, 'confidence': 0.82},
      {'date': '2025-10-01', 'risk_score': 0.63, 'confidence': 0.84},
      {'date': '2025-10-02', 'risk_score': 0.60, 'confidence': 0.86},
    ],
    'summary': {
      'trend': 'increasing_then_decreasing',
      'peak_date': '2025-09-25',
      'peak_risk_score': 0.80,
      'average_risk_score': 0.69,
      'risk_change_percentage': 12.5,
    },
    'environmental_forecast': {
      'temperature_trend': 'stable',
      'rainfall_expected': true,
      'humidity_trend': 'increasing',
      'key_factors': ['upcoming_rainfall', 'temperature_stability'],
    },
  };

  /// Sample alert data
  static const List<Map<String, dynamic>> sampleAlerts = [
    {
      'id': 'alert_001_20250918',
      'type': 'malaria_outbreak_risk',
      'severity': 'high',
      'title': 'Elevated Malaria Risk - Mombasa Region',
      'message': 'Malaria transmission risk has increased significantly in the Mombasa region due to favorable environmental conditions. Immediate preventive measures recommended.',
      'region': 'Mombasa',
      'country': 'Kenya',
      'coordinates': {
        'latitude': -4.0435,
        'longitude': 39.6682,
      },
      'affected_population': 1208333,
      'risk_increase_percentage': 45.0,
      'trigger_conditions': [
        'risk_score_threshold_exceeded',
        'environmental_conditions_favorable',
        'population_vulnerability_high',
      ],
      'recommended_actions': [
        'Increase vector control activities in urban areas',
        'Enhance surveillance and case detection',
        'Distribute additional bed nets to vulnerable populations',
        'Issue public health advisories through local media',
        'Prepare medical facilities for potential case surge',
      ],
      'alert_level': 'level_3',
      'valid_until': '2025-10-02T23:59:59.000Z',
      'created_at': '2025-09-18T10:15:00.000Z',
      'updated_at': '2025-09-18T14:30:00.000Z',
      'confidence_level': 0.92,
      'model_version': '2.1.0',
      'data_sources': ['real_time_monitoring', 'prediction_model', 'environmental_data'],
      'status': 'active',
    },
    {
      'id': 'alert_002_20250918',
      'type': 'environmental_change',
      'severity': 'medium',
      'title': 'Environmental Conditions Change - Western Kenya',
      'message': 'Significant changes in environmental conditions detected in Western Kenya. Monitor for potential malaria risk changes.',
      'region': 'Western_Kenya',
      'country': 'Kenya',
      'coordinates': {
        'latitude': 0.5143,
        'longitude': 35.2699,
      },
      'affected_population': 5000000,
      'environmental_changes': {
        'rainfall_increase': 25.0,
        'temperature_change': 2.5,
        'humidity_increase': 15.0,
      },
      'alert_level': 'level_2',
      'valid_until': '2025-09-25T23:59:59.000Z',
      'created_at': '2025-09-18T09:00:00.000Z',
      'confidence_level': 0.78,
      'status': 'active',
    },
  ];

  /// Sample map layer data
  static const List<Map<String, dynamic>> sampleMapLayers = [
    {
      'id': 'layer_malaria_risk_choropleth',
      'name': 'Malaria Risk Choropleth',
      'type': 'choropleth',
      'category': 'risk_assessment',
      'description': 'Regional malaria risk levels displayed as colored polygons',
      'region': 'East_Africa',
      'bounds': {
        'north': 5.0,
        'south': -12.0,
        'east': 52.0,
        'west': 22.0,
      },
      'zoom_levels': {
        'min': 3,
        'max': 18,
      },
      'resolution': '1km',
      'data_url': 'https://api.malaria-prediction.org/v1/layers/risk/choropleth',
      'tile_url': 'https://tiles.malaria-prediction.org/risk/{z}/{x}/{y}.png',
      'style': {
        'color_scale': {
          'low': '#00ff00',
          'medium': '#ffff00',
          'high': '#ff6600',
          'critical': '#ff0000',
        },
        'opacity': 0.7,
        'stroke_color': '#333333',
        'stroke_width': 1,
        'stroke_opacity': 0.8,
      },
      'legend': {
        'title': 'Malaria Risk Level',
        'categories': [
          {'label': 'Low Risk (0.0-0.3)', 'color': '#00ff00'},
          {'label': 'Medium Risk (0.3-0.6)', 'color': '#ffff00'},
          {'label': 'High Risk (0.6-0.8)', 'color': '#ff6600'},
          {'label': 'Critical Risk (0.8-1.0)', 'color': '#ff0000'},
        ],
      },
      'metadata': {
        'source': 'Malaria Prediction Model v2.1',
        'update_frequency': 'daily',
        'last_updated': '2025-09-18T08:00:00.000Z',
        'data_quality': 'high',
        'coverage': '95%',
      },
      'is_visible': true,
      'is_base_layer': false,
    },
    {
      'id': 'layer_temperature',
      'name': 'Temperature Data',
      'type': 'heatmap',
      'category': 'environmental',
      'description': 'Average temperature data from ERA5',
      'data_source': 'ERA5',
      'style': {
        'color_scale': ['#0000ff', '#00ffff', '#ffff00', '#ff0000'],
        'opacity': 0.6,
      },
      'units': 'celsius',
      'is_visible': false,
      'is_base_layer': false,
    },
    {
      'id': 'layer_rainfall',
      'name': 'Rainfall Data',
      'type': 'isopleth',
      'category': 'environmental',
      'description': 'Precipitation data from CHIRPS',
      'data_source': 'CHIRPS',
      'style': {
        'color_scale': ['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8', '#253494'],
        'opacity': 0.5,
      },
      'units': 'mm',
      'is_visible': false,
      'is_base_layer': false,
    },
  ];

  /// Sample analytics data
  static const Map<String, dynamic> sampleAnalytics = {
    'dashboard_metrics': {
      'total_regions_monitored': 125,
      'active_alerts': 8,
      'high_risk_regions': 15,
      'predictions_generated_today': 247,
      'data_sources_active': 4,
      'model_accuracy': 0.89,
      'last_model_update': '2025-09-15T02:00:00.000Z',
    },
    'risk_distribution': {
      'low_risk': 65,
      'medium_risk': 35,
      'high_risk': 20,
      'critical_risk': 5,
    },
    'temporal_trends': {
      'last_7_days': [
        {'date': '2025-09-12', 'avg_risk': 0.45, 'alerts': 2},
        {'date': '2025-09-13', 'avg_risk': 0.48, 'alerts': 3},
        {'date': '2025-09-14', 'avg_risk': 0.52, 'alerts': 4},
        {'date': '2025-09-15', 'avg_risk': 0.55, 'alerts': 5},
        {'date': '2025-09-16', 'avg_risk': 0.58, 'alerts': 6},
        {'date': '2025-09-17', 'avg_risk': 0.61, 'alerts': 7},
        {'date': '2025-09-18', 'avg_risk': 0.64, 'alerts': 8},
      ],
    },
    'geographic_distribution': {
      'East_Africa': {'regions': 45, 'avg_risk': 0.62},
      'West_Africa': {'regions': 38, 'avg_risk': 0.55},
      'Central_Africa': {'regions': 25, 'avg_risk': 0.48},
      'Southern_Africa': {'regions': 17, 'avg_risk': 0.41},
    },
  };

  /// Sample API responses for different scenarios
  static Map<String, dynamic> successApiResponse({
    required dynamic data,
    String? message,
  }) {
    return {
      'success': true,
      'status_code': 200,
      'message': message ?? 'Operation completed successfully',
      'data': data,
      'timestamp': DateTime.now().toIso8601String(),
      'request_id': 'req_${DateTime.now().millisecondsSinceEpoch}',
    };
  }

  static Map<String, dynamic> errorApiResponse({
    int statusCode = 400,
    String? message,
    String? errorCode,
  }) {
    return {
      'success': false,
      'status_code': statusCode,
      'error': {
        'code': errorCode ?? 'GENERIC_ERROR',
        'message': message ?? 'An error occurred',
        'details': {},
      },
      'timestamp': DateTime.now().toIso8601String(),
      'request_id': 'req_${DateTime.now().millisecondsSinceEpoch}',
    };
  }

  /// Sample configuration data
  static const Map<String, dynamic> sampleAppConfig = {
    'api': {
      'base_url': 'https://api.malaria-prediction.org/v1',
      'timeout_seconds': 30,
      'retry_attempts': 3,
      'rate_limit': {
        'requests_per_minute': 100,
        'burst_limit': 10,
      },
    },
    'features': {
      'risk_assessment': true,
      'predictions': true,
      'maps': true,
      'alerts': true,
      'analytics': true,
      'offline_mode': true,
      'real_time_updates': true,
    },
    'cache': {
      'ttl_seconds': {
        'risk_data': 3600,
        'predictions': 1800,
        'map_tiles': 86400,
        'user_data': 600,
      },
      'max_size_mb': 100,
    },
    'performance': {
      'image_cache_size': 50,
      'list_pagination_size': 20,
      'map_tile_cache_size': 100,
    },
  };

  /// Generate test data programmatically
  static List<Map<String, dynamic>> generateRiskDataSeries({
    required int count,
    required String region,
    required String startDate,
  }) {
    final startDateTime = DateTime.parse(startDate);
    return List.generate(count, (index) {
      final date = startDateTime.add(Duration(days: index));
      final baseRisk = 0.3 + (index % 5) * 0.1;
      final noise = (index % 3 - 1) * 0.05;

      return {
        'id': 'risk_${region.toLowerCase()}_${date.toIso8601String().split('T')[0]}',
        'region': region,
        'date': date.toIso8601String(),
        'risk_score': (baseRisk + noise).clamp(0.0, 1.0),
        'confidence': 0.85 - (index * 0.01).clamp(0.0, 0.2),
        'environmental_factors': {
          'temperature': 25.0 + (index % 10 - 5) * 0.5,
          'rainfall': 100.0 + (index % 7 - 3) * 20.0,
          'humidity': 70.0 + (index % 5 - 2) * 5.0,
        },
      };
    });
  }

  /// Generate large dataset for performance testing
  static List<Map<String, dynamic>> generateLargeDataset(int size) {
    return List.generate(size, (index) => {
      'id': 'item_$index',
      'name': 'Test Item $index',
      'description': 'Description for test item number $index with some additional content',
      'value': index * 1.5,
      'category': ['Category A', 'Category B', 'Category C'][index % 3],
      'timestamp': DateTime.now().subtract(Duration(hours: index)).toIso8601String(),
      'metadata': {
        'source': 'test_generator',
        'index': index,
        'batch': index ~/ 100,
      },
    });
  }

  /// Mock API responses for different HTTP status codes
  static const Map<int, Map<String, dynamic>> httpStatusResponses = {
    200: {
      'success': true,
      'message': 'OK',
      'data': {'result': 'success'},
    },
    201: {
      'success': true,
      'message': 'Created',
      'data': {'id': 'new_resource_123'},
    },
    400: {
      'success': false,
      'error': {
        'code': 'BAD_REQUEST',
        'message': 'Invalid request parameters',
      },
    },
    401: {
      'success': false,
      'error': {
        'code': 'UNAUTHORIZED',
        'message': 'Authentication required',
      },
    },
    403: {
      'success': false,
      'error': {
        'code': 'FORBIDDEN',
        'message': 'Access denied',
      },
    },
    404: {
      'success': false,
      'error': {
        'code': 'NOT_FOUND',
        'message': 'Resource not found',
      },
    },
    429: {
      'success': false,
      'error': {
        'code': 'RATE_LIMIT_EXCEEDED',
        'message': 'Too many requests',
      },
    },
    500: {
      'success': false,
      'error': {
        'code': 'INTERNAL_SERVER_ERROR',
        'message': 'Server error occurred',
      },
    },
    503: {
      'success': false,
      'error': {
        'code': 'SERVICE_UNAVAILABLE',
        'message': 'Service temporarily unavailable',
      },
    },
  };

  /// Utility methods for test data manipulation
  static String toJsonString(Map<String, dynamic> data) {
    return jsonEncode(data);
  }

  static Map<String, dynamic> fromJsonString(String jsonString) {
    return jsonDecode(jsonString) as Map<String, dynamic>;
  }

  /// Create test data variants
  static Map<String, dynamic> createRiskAssessmentVariant({
    String? region,
    String? riskLevel,
    double? riskScore,
  }) {
    final base = Map<String, dynamic>.from(sampleRiskAssessments[0]);
    if (region != null) base['region'] = region;
    if (riskLevel != null) base['risk_level'] = riskLevel;
    if (riskScore != null) base['risk_score'] = riskScore;
    return base;
  }

  static Map<String, dynamic> createUserVariant({
    String? email,
    List<String>? roles,
    Map<String, dynamic>? preferences,
  }) {
    final base = Map<String, dynamic>.from(sampleUser);
    if (email != null) base['email'] = email;
    if (roles != null) base['roles'] = roles;
    if (preferences != null) {
      base['preferences'] = {...base['preferences'], ...preferences};
    }
    return base;
  }

  /// Test data validation helpers
  static bool isValidRiskScore(double score) {
    return score >= 0.0 && score <= 1.0;
  }

  static bool isValidCoordinates(Map<String, dynamic> coords) {
    final lat = coords['latitude'] as double?;
    final lng = coords['longitude'] as double?;
    return lat != null && lng != null &&
           lat >= -90.0 && lat <= 90.0 &&
           lng >= -180.0 && lng <= 180.0;
  }

  static bool isValidTimestamp(String timestamp) {
    try {
      DateTime.parse(timestamp);
      return true;
    } catch (e) {
      return false;
    }
  }
}