/// Mock Factories for Malaria Prediction App Testing
/// Provides comprehensive mock implementations for all app services
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Centralized mock factory for consistent test mocking
library;

import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:mocktail/mocktail.dart' as mocktail;
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:geolocator/geolocator.dart';

// Import app-specific classes when available
// Note: These imports will be added as the app develops
// import 'package:malaria_frontend/core/network/api_client.dart';
// import 'package:malaria_frontend/features/authentication/domain/repositories/auth_repository.dart';
// import 'package:malaria_frontend/features/risk_maps/domain/repositories/risk_maps_repository.dart';

/// Generate mocks for common Flutter and package dependencies
@GenerateMocks([
  Dio,
  SharedPreferences,
  FlutterSecureStorage,
  Connectivity,
  GeolocatorPlatform,
])
class MockFactories {
  /// Create mock Dio client with predefined responses
  static Dio createMockDio({
    Map<String, dynamic>? defaultResponse,
    int statusCode = 200,
  }) {
    final mockDio = MockDio();

    // Set up default response behavior
    when(mockDio.get(any, options: anyNamed('options')))
        .thenAnswer((_) async => Response(
              data: defaultResponse ?? {'success': true, 'data': []},
              statusCode: statusCode,
              requestOptions: RequestOptions(path: ''),
            ),);

    when(mockDio.post(any, data: anyNamed('data'), options: anyNamed('options')))
        .thenAnswer((_) async => Response(
              data: defaultResponse ?? {'success': true, 'message': 'Created'},
              statusCode: statusCode,
              requestOptions: RequestOptions(path: ''),
            ),);

    when(mockDio.put(any, data: anyNamed('data'), options: anyNamed('options')))
        .thenAnswer((_) async => Response(
              data: defaultResponse ?? {'success': true, 'message': 'Updated'},
              statusCode: statusCode,
              requestOptions: RequestOptions(path: ''),
            ),);

    when(mockDio.delete(any, options: anyNamed('options')))
        .thenAnswer((_) async => Response(
              data: defaultResponse ?? {'success': true, 'message': 'Deleted'},
              statusCode: statusCode,
              requestOptions: RequestOptions(path: ''),
            ),);

    return mockDio;
  }

  /// Create mock SharedPreferences with predefined values
  static SharedPreferences createMockSharedPreferences({
    Map<String, dynamic>? initialValues,
  }) {
    final mockPrefs = MockSharedPreferences();
    final values = initialValues ?? <String, dynamic>{};

    // Set up getter methods
    when(mockPrefs.getString(any)).thenAnswer((invocation) {
      final key = invocation.positionalArguments[0] as String;
      return values[key] as String?;
    });

    when(mockPrefs.getBool(any)).thenAnswer((invocation) {
      final key = invocation.positionalArguments[0] as String;
      return values[key] as bool?;
    });

    when(mockPrefs.getInt(any)).thenAnswer((invocation) {
      final key = invocation.positionalArguments[0] as String;
      return values[key] as int?;
    });

    when(mockPrefs.getDouble(any)).thenAnswer((invocation) {
      final key = invocation.positionalArguments[0] as String;
      return values[key] as double?;
    });

    when(mockPrefs.getStringList(any)).thenAnswer((invocation) {
      final key = invocation.positionalArguments[0] as String;
      return values[key] as List<String>?;
    });

    // Set up setter methods
    when(mockPrefs.setString(any, any)).thenAnswer((invocation) async {
      final key = invocation.positionalArguments[0] as String;
      final value = invocation.positionalArguments[1] as String;
      values[key] = value;
      return true;
    });

    when(mockPrefs.setBool(any, any)).thenAnswer((invocation) async {
      final key = invocation.positionalArguments[0] as String;
      final value = invocation.positionalArguments[1] as bool;
      values[key] = value;
      return true;
    });

    when(mockPrefs.setInt(any, any)).thenAnswer((invocation) async {
      final key = invocation.positionalArguments[0] as String;
      final value = invocation.positionalArguments[1] as int;
      values[key] = value;
      return true;
    });

    when(mockPrefs.setDouble(any, any)).thenAnswer((invocation) async {
      final key = invocation.positionalArguments[0] as String;
      final value = invocation.positionalArguments[1] as double;
      values[key] = value;
      return true;
    });

    when(mockPrefs.setStringList(any, any)).thenAnswer((invocation) async {
      final key = invocation.positionalArguments[0] as String;
      final value = invocation.positionalArguments[1] as List<String>;
      values[key] = value;
      return true;
    });

    // Set up removal and checking methods
    when(mockPrefs.remove(any)).thenAnswer((invocation) async {
      final key = invocation.positionalArguments[0] as String;
      values.remove(key);
      return true;
    });

    when(mockPrefs.containsKey(any)).thenAnswer((invocation) {
      final key = invocation.positionalArguments[0] as String;
      return values.containsKey(key);
    });

    when(mockPrefs.getKeys()).thenReturn(values.keys.toSet());

    return mockPrefs;
  }

  /// Create mock FlutterSecureStorage
  static FlutterSecureStorage createMockSecureStorage({
    Map<String, String>? initialValues,
  }) {
    final mockStorage = MockFlutterSecureStorage();
    final values = initialValues ?? <String, String>{};

    when(mockStorage.read(key: anyNamed('key'))).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String;
      return values[key];
    });

    when(mockStorage.write(key: anyNamed('key'), value: anyNamed('value')))
        .thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String;
      final value = invocation.namedArguments[#value] as String;
      values[key] = value;
      return null;
    });

    when(mockStorage.delete(key: anyNamed('key'))).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String;
      values.remove(key);
      return null;
    });

    when(mockStorage.deleteAll()).thenAnswer((_) async {
      values.clear();
      return null;
    });

    when(mockStorage.readAll()).thenAnswer((_) async => values);

    when(mockStorage.containsKey(key: anyNamed('key'))).thenAnswer((invocation) async {
      final key = invocation.namedArguments[#key] as String;
      return values.containsKey(key);
    });

    return mockStorage;
  }

  /// Create mock Connectivity service
  static Connectivity createMockConnectivity({
    ConnectivityResult initialResult = ConnectivityResult.wifi,
  }) {
    final mockConnectivity = MockConnectivity();

    when(mockConnectivity.checkConnectivity())
        .thenAnswer((_) async => initialResult);

    // Set up stream for connectivity changes
    final streamController = Stream<ConnectivityResult>.periodic(
      const Duration(seconds: 1),
      (_) => initialResult,
    );

    when(mockConnectivity.onConnectivityChanged)
        .thenAnswer((_) => streamController);

    return mockConnectivity;
  }

  /// Create mock Geolocator
  static GeolocatorPlatform createMockGeolocator({
    Position? mockPosition,
    bool serviceEnabled = true,
    LocationPermission permission = LocationPermission.whileInUse,
  }) {
    final mockGeolocator = MockGeolocatorPlatform();
    final defaultPosition = mockPosition ?? Position(
      latitude: -1.2921, // Nairobi coordinates
      longitude: 36.8219,
      timestamp: DateTime.now(),
      accuracy: 5,
      altitude: 1700,
      heading: 0,
      speed: 0,
      speedAccuracy: 0,
      altitudeAccuracy: 0,
      headingAccuracy: 0,
    );

    when(mockGeolocator.isLocationServiceEnabled())
        .thenAnswer((_) async => serviceEnabled);

    when(mockGeolocator.checkPermission())
        .thenAnswer((_) async => permission);

    when(mockGeolocator.requestPermission())
        .thenAnswer((_) async => permission);

    when(mockGeolocator.getCurrentPosition(
      locationSettings: anyNamed('locationSettings'),
    ),).thenAnswer((_) async => defaultPosition);

    when(mockGeolocator.getLastKnownPosition(
      forceLocationManager: anyNamed('forceLocationManager'),
    ),).thenAnswer((_) async => defaultPosition);

    // Set up position stream
    final positionStream = Stream<Position>.periodic(
      const Duration(seconds: 5),
      (_) => defaultPosition,
    );

    when(mockGeolocator.getPositionStream(
      locationSettings: anyNamed('locationSettings'),
    ),).thenAnswer((_) => positionStream);

    return mockGeolocator;
  }
}

/// Mock implementations using mocktail for better type safety
class MockTailFactories {
  /// Mock API Client using mocktail
  static MockApiClient createMockApiClient() {
    return MockApiClient();
  }

  /// Mock Authentication Repository using mocktail
  static MockAuthRepository createMockAuthRepository() {
    return MockAuthRepository();
  }

  /// Mock Risk Maps Repository using mocktail
  static MockRiskMapsRepository createMockRiskMapsRepository() {
    return MockRiskMapsRepository();
  }

  /// Mock Notification Service using mocktail
  static MockNotificationService createMockNotificationService() {
    return MockNotificationService();
  }

  /// Mock Analytics Service using mocktail
  static MockAnalyticsService createMockAnalyticsService() {
    return MockAnalyticsService();
  }
}

/// Mocktail mock classes
/// These will be replaced with actual implementations as the app develops

class MockApiClient extends mocktail.Mock {
  // Mock implementation will be added when actual ApiClient is implemented
}

class MockAuthRepository extends mocktail.Mock {
  // Mock implementation will be added when actual AuthRepository is implemented
}

class MockRiskMapsRepository extends mocktail.Mock {
  // Mock implementation will be added when actual RiskMapsRepository is implemented
}

class MockNotificationService extends mocktail.Mock {
  // Mock implementation will be added when actual NotificationService is implemented
}

class MockAnalyticsService extends mocktail.Mock {
  // Mock implementation will be added when actual AnalyticsService is implemented
}

/// Test data generators for specific app domains
class TestDataGenerators {
  /// Generate test risk assessment data
  static Map<String, dynamic> generateRiskAssessmentData({
    String? region,
    String? riskLevel,
    DateTime? timestamp,
  }) {
    return {
      'id': 'risk_${DateTime.now().millisecondsSinceEpoch}',
      'region': region ?? 'Nairobi',
      'coordinates': {
        'latitude': -1.2921,
        'longitude': 36.8219,
      },
      'risk_level': riskLevel ?? 'medium',
      'risk_score': 0.65,
      'confidence_interval': {
        'lower': 0.45,
        'upper': 0.85,
      },
      'environmental_factors': {
        'temperature': 24.5,
        'rainfall': 120.0,
        'humidity': 75.0,
        'vegetation_index': 0.8,
        'population_density': 1500,
      },
      'prediction_horizon_days': 14,
      'model_version': '2.1.0',
      'timestamp': (timestamp ?? DateTime.now()).toIso8601String(),
      'data_sources': [
        'ERA5',
        'CHIRPS',
        'MODIS',
        'WorldPop',
      ],
    };
  }

  /// Generate test user authentication data
  static Map<String, dynamic> generateAuthenticationData({
    String? userId,
    String? email,
    List<String>? roles,
  }) {
    return {
      'user': {
        'id': userId ?? 'user_${DateTime.now().millisecondsSinceEpoch}',
        'email': email ?? 'test@malaria-prediction.org',
        'name': 'Test User',
        'roles': roles ?? ['researcher', 'data_viewer'],
        'organization': 'Test Health Organization',
        'created_at': DateTime.now().toIso8601String(),
        'last_login': DateTime.now().toIso8601String(),
      },
      'tokens': {
        'access_token': 'mock_access_token_${DateTime.now().millisecondsSinceEpoch}',
        'refresh_token': 'mock_refresh_token_${DateTime.now().millisecondsSinceEpoch}',
        'expires_in': 3600,
        'token_type': 'Bearer',
      },
      'permissions': [
        'view_risk_data',
        'request_predictions',
        'view_analytics',
        'export_data',
      ],
    };
  }

  /// Generate test map layer data
  static Map<String, dynamic> generateMapLayerData({
    String? layerType,
    String? region,
  }) {
    return {
      'id': 'layer_${DateTime.now().millisecondsSinceEpoch}',
      'type': layerType ?? 'risk_choropleth',
      'name': 'Malaria Risk ${layerType ?? 'Assessment'}',
      'region': region ?? 'East_Africa',
      'bounds': {
        'north': 5.0,
        'south': -12.0,
        'east': 52.0,
        'west': 22.0,
      },
      'resolution': '1km',
      'data_url': 'https://api.malaria-prediction.org/layers/${layerType ?? 'risk'}/data',
      'style': {
        'color_scale': ['#00ff00', '#ffff00', '#ff6600', '#ff0000'],
        'opacity': 0.7,
        'stroke_width': 1,
      },
      'metadata': {
        'source': 'Malaria Prediction Model v2.1',
        'update_frequency': 'daily',
        'last_updated': DateTime.now().toIso8601String(),
        'data_quality': 'high',
      },
    };
  }

  /// Generate test alert notification data
  static Map<String, dynamic> generateAlertData({
    String? severity,
    String? region,
  }) {
    return {
      'id': 'alert_${DateTime.now().millisecondsSinceEpoch}',
      'type': 'malaria_outbreak_risk',
      'severity': severity ?? 'medium',
      'title': 'Elevated Malaria Risk Detected',
      'message': 'Increased malaria transmission risk predicted for the next 14 days due to favorable environmental conditions.',
      'region': region ?? 'Nairobi',
      'coordinates': {
        'latitude': -1.2921,
        'longitude': 36.8219,
      },
      'affected_population': 150000,
      'risk_increase_percentage': 35.0,
      'recommended_actions': [
        'Increase vector control activities',
        'Enhance surveillance efforts',
        'Prepare additional medical supplies',
        'Issue public health advisories',
      ],
      'valid_until': DateTime.now().add(const Duration(days: 14)).toIso8601String(),
      'created_at': DateTime.now().toIso8601String(),
      'confidence_level': 0.85,
      'model_version': '2.1.0',
    };
  }
}

/// HTTP response mock builders
class HttpResponseMockBuilder {
  /// Build success response with data
  static Response<T> buildSuccessResponse<T>(
    T data, {
    int statusCode = 200,
    String path = '/test',
    Map<String, dynamic>? headers,
  }) {
    return Response<T>(
      data: data,
      statusCode: statusCode,
      requestOptions: RequestOptions(path: path, headers: headers),
    );
  }

  /// Build error response
  static Response<Map<String, dynamic>> buildErrorResponse({
    int statusCode = 400,
    String message = 'Bad Request',
    String path = '/test',
    Map<String, dynamic>? headers,
  }) {
    return Response<Map<String, dynamic>>(
      data: {
        'error': {
          'code': statusCode,
          'message': message,
          'timestamp': DateTime.now().toIso8601String(),
        },
      },
      statusCode: statusCode,
      requestOptions: RequestOptions(path: path, headers: headers),
    );
  }

  /// Build network error
  static DioException buildNetworkError({
    String message = 'Network Error',
    String path = '/test',
  }) {
    return DioException(
      requestOptions: RequestOptions(path: path),
      type: DioExceptionType.connectionError,
      message: message,
    );
  }

  /// Build timeout error
  static DioException buildTimeoutError({
    String path = '/test',
  }) {
    return DioException(
      requestOptions: RequestOptions(path: path),
      type: DioExceptionType.connectionTimeout,
      message: 'Connection timeout',
    );
  }
}