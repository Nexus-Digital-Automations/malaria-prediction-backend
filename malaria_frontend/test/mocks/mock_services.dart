/// Mock Services for Testing
///
/// Provides mock implementations of all core services used throughout
/// the malaria prediction Flutter application for comprehensive testing.

import 'package:mocktail/mocktail.dart';
import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hive/hive.dart';

// Core Service Mocks
class MockDio extends Mock implements Dio {}
class MockConnectivity extends Mock implements Connectivity {}
class MockGeolocator extends Mock implements GeolocatorPlatform {}
class MockFlutterSecureStorage extends Mock implements FlutterSecureStorage {}
class MockSharedPreferences extends Mock implements SharedPreferences {}
class MockHiveBox extends Mock implements Box {}

// Network and API Mocks
class MockApiClient extends Mock {
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onReceiveProgress,
  }) async {
    return Response<T>(
      data: null,
      statusCode: 200,
      requestOptions: RequestOptions(path: path),
    );
  }

  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
    CancelToken? cancelToken,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    return Response<T>(
      data: null,
      statusCode: 200,
      requestOptions: RequestOptions(path: path),
    );
  }
}

class MockNetworkInfo extends Mock {
  bool get isConnected => true;
  Stream<bool> get onConnectivityChanged => Stream.value(true);
}

// Authentication Service Mocks
class MockAuthService extends Mock {
  Future<String?> getAccessToken() async => 'mock-access-token';
  Future<String?> getRefreshToken() async => 'mock-refresh-token';
  Future<void> storeTokens(String accessToken, String refreshToken) async {}
  Future<void> clearTokens() async {}
  bool get isAuthenticated => true;
  Stream<bool> get authStateChanges => Stream.value(true);
}

class MockTokenManager extends Mock {
  Future<String?> getValidToken() async => 'mock-valid-token';
  Future<bool> refreshToken() async => true;
  bool get hasValidToken => true;
  Future<void> clearTokens() async {}
}

// Location Service Mocks
class MockLocationService extends Mock {
  Future<Position> getCurrentPosition() async {
    return Position(
      longitude: 36.8219,
      latitude: -1.2921,
      timestamp: DateTime.now(),
      accuracy: 10.0,
      altitude: 1661.0,
      heading: 0.0,
      speed: 0.0,
      speedAccuracy: 0.0,
    );
  }

  Future<bool> requestPermission() async => true;
  Future<LocationPermission> checkPermission() async => LocationPermission.always;
  Stream<Position> get positionStream => Stream.value(
    Position(
      longitude: 36.8219,
      latitude: -1.2921,
      timestamp: DateTime.now(),
      accuracy: 10.0,
      altitude: 1661.0,
      heading: 0.0,
      speed: 0.0,
      speedAccuracy: 0.0,
    ),
  );
}

// Cache Service Mocks
class MockCacheService extends Mock {
  Future<T?> get<T>(String key) async => null;
  Future<void> set<T>(String key, T value, {Duration? ttl}) async {}
  Future<void> remove(String key) async {}
  Future<void> clear() async {}
  bool contains(String key) => false;
  int get size => 0;
}

class MockOfflineCacheService extends Mock {
  Future<Map<String, dynamic>?> getCachedData(String key) async => null;
  Future<void> cacheData(String key, Map<String, dynamic> data) async {}
  Future<void> clearExpiredCache() async {}
  Future<List<String>> getCachedKeys() async => [];
  bool get hasOfflineData => false;
}

// WebSocket Service Mocks
class MockWebSocketService extends Mock {
  Stream<dynamic> get messageStream => Stream.empty();
  Future<void> connect(String url) async {}
  Future<void> disconnect() async {}
  void sendMessage(Map<String, dynamic> message) {}
  bool get isConnected => false;
  ConnectionState get connectionState => ConnectionState.disconnected;
}

enum ConnectionState { connected, disconnected, connecting, error }

// Notification Service Mocks
class MockNotificationService extends Mock {
  Future<void> initialize() async {}
  Future<bool> requestPermission() async => true;
  Future<void> showNotification({
    required String title,
    required String body,
    String? payload,
  }) async {}
  Future<void> scheduleNotification({
    required String title,
    required String body,
    required DateTime scheduledDate,
    String? payload,
  }) async {}
  Stream<String> get onNotificationTap => Stream.empty();
}

// Analytics Service Mocks
class MockAnalyticsService extends Mock {
  Future<void> logEvent(String eventName, Map<String, dynamic> parameters) async {}
  Future<void> setUserProperties(Map<String, dynamic> properties) async {}
  Future<void> setUserId(String userId) async {}
  Future<void> logScreenView(String screenName) async {}
  Future<void> logError(String error, String? stackTrace) async {}
}

// Biometric Service Mocks
class MockBiometricService extends Mock {
  Future<bool> isAvailable() async => true;
  Future<List<BiometricType>> getAvailableBiometrics() async => [BiometricType.fingerprint];
  Future<bool> authenticate({
    required String localizedReason,
    bool biometricOnly = false,
  }) async => true;
  Future<void> stopAuthentication() async {}
}

enum BiometricType { fingerprint, face, iris }

// Validation Service Mocks
class MockValidationService extends Mock {
  bool isValidEmail(String email) => email.contains('@') && email.contains('.');
  bool isValidPassword(String password) => password.length >= 8;
  bool isValidPhoneNumber(String phoneNumber) => phoneNumber.length >= 10;
  String? validateEmail(String? email) => null;
  String? validatePassword(String? password) => null;
  String? validatePhoneNumber(String? phoneNumber) => null;
  String? validateRequired(String? value, String fieldName) => null;
}

// Image Service Mocks
class MockImageService extends Mock {
  Future<String?> pickImage({required ImageSource source}) async => 'mock-image-path';
  Future<List<String>> pickMultipleImages() async => ['mock-image-1', 'mock-image-2'];
  Future<String?> captureImage() async => 'mock-captured-image';
  Future<void> saveImageToGallery(String imagePath) async {}
  Future<String?> compressImage(String imagePath, {int quality = 85}) async => 'mock-compressed-image';
}

enum ImageSource { camera, gallery }

// File Service Mocks
class MockFileService extends Mock {
  Future<String> getApplicationDocumentsDirectory() async => '/mock/documents';
  Future<String> getTemporaryDirectory() async => '/mock/temp';
  Future<String> getExternalStorageDirectory() async => '/mock/external';
  Future<bool> fileExists(String path) async => false;
  Future<void> writeFile(String path, String content) async {}
  Future<String> readFile(String path) async => '';
  Future<void> deleteFile(String path) async {}
  Future<List<String>> listFiles(String directory) async => [];
}

// Crash Reporting Service Mocks
class MockCrashReportingService extends Mock {
  Future<void> recordError(
    dynamic exception,
    StackTrace? stack, {
    bool fatal = false,
    Iterable<Object> information = const [],
  }) async {}

  Future<void> log(String message) async {}
  Future<void> setCustomKey(String key, dynamic value) async {}
  Future<void> setUserIdentifier(String identifier) async {}
  Future<void> sendUnsentReports() async {}
}

// Mock Factory for easy mock creation
class MockFactory {
  static MockDio createMockDio() => MockDio();
  static MockConnectivity createMockConnectivity() => MockConnectivity();
  static MockAuthService createMockAuthService() => MockAuthService();
  static MockLocationService createMockLocationService() => MockLocationService();
  static MockCacheService createMockCacheService() => MockCacheService();
  static MockWebSocketService createMockWebSocketService() => MockWebSocketService();
  static MockNotificationService createMockNotificationService() => MockNotificationService();
  static MockAnalyticsService createMockAnalyticsService() => MockAnalyticsService();
  static MockBiometricService createMockBiometricService() => MockBiometricService();
  static MockValidationService createMockValidationService() => MockValidationService();
  static MockImageService createMockImageService() => MockImageService();
  static MockFileService createMockFileService() => MockFileService();
  static MockCrashReportingService createMockCrashReportingService() => MockCrashReportingService();
}

// Mock setup helpers
class MockSetupHelpers {
  /// Sets up a mock Dio client with standard responses
  static void setupMockDio(MockDio mockDio) {
    // Setup successful login response
    when(() => mockDio.post(
      '/auth/login',
      data: any(named: 'data'),
    )).thenAnswer((_) async => Response(
      data: {
        'success': true,
        'data': {
          'accessToken': 'mock-access-token',
          'refreshToken': 'mock-refresh-token',
          'user': {
            'id': 'user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'healthcare_worker',
          },
        },
      },
      statusCode: 200,
      requestOptions: RequestOptions(path: '/auth/login'),
    ));

    // Setup risk data response
    when(() => mockDio.get(
      '/risk-data',
      queryParameters: any(named: 'queryParameters'),
    )).thenAnswer((_) async => Response(
      data: {
        'success': true,
        'data': [
          {
            'id': 'risk-123',
            'region': 'Nairobi',
            'riskLevel': 'medium',
            'riskScore': 0.65,
            'timestamp': DateTime.now().toIso8601String(),
          },
        ],
      },
      statusCode: 200,
      requestOptions: RequestOptions(path: '/risk-data'),
    ));
  }

  /// Sets up mock connectivity with various states
  static void setupMockConnectivity(MockConnectivity mockConnectivity) {
    when(() => mockConnectivity.checkConnectivity())
        .thenAnswer((_) async => ConnectivityResult.wifi);

    when(() => mockConnectivity.onConnectivityChanged)
        .thenAnswer((_) => Stream.value(ConnectivityResult.wifi));
  }

  /// Sets up mock location service with test coordinates
  static void setupMockLocationService(MockLocationService mockLocationService) {
    final testPosition = Position(
      longitude: 36.8219,
      latitude: -1.2921,
      timestamp: DateTime.now(),
      accuracy: 10.0,
      altitude: 1661.0,
      heading: 0.0,
      speed: 0.0,
      speedAccuracy: 0.0,
    );

    when(() => mockLocationService.getCurrentPosition())
        .thenAnswer((_) async => testPosition);

    when(() => mockLocationService.requestPermission())
        .thenAnswer((_) async => true);

    when(() => mockLocationService.checkPermission())
        .thenAnswer((_) async => LocationPermission.always);
  }
}