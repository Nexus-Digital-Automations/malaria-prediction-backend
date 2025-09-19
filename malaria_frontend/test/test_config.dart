/// Test Configuration and Global Setup
///
/// Centralizes test configuration, mock services, and common test utilities
/// for the malaria prediction Flutter frontend testing suite.

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:network_image_mock/network_image_mock.dart';

/// Global test configuration class that sets up the testing environment
class TestConfig {
  static bool _isInitialized = false;

  /// Initialize the test environment with all necessary configurations
  static Future<void> initialize() async {
    if (_isInitialized) return;

    TestWidgetsFlutterBinding.ensureInitialized();

    // Configure golden tests
    await loadAppFonts();

    // Initialize Hive for testing
    await _initializeHive();

    // Setup method channel mocks
    _setupMethodChannelMocks();

    _isInitialized = true;
  }

  /// Initialize Hive with a temporary directory for testing
  static Future<void> _initializeHive() async {
    Hive.init('test/temp');
    // Register any custom adapters here
  }

  /// Setup method channel mocks for platform-specific functionality
  static void _setupMethodChannelMocks() {
    // Mock secure storage
    const secureStorageChannel = MethodChannel('plugins.it_nomads.com/flutter_secure_storage');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(secureStorageChannel, (MethodCall methodCall) async {
      switch (methodCall.method) {
        case 'read':
          return null;
        case 'write':
          return null;
        case 'delete':
          return null;
        case 'deleteAll':
          return null;
        case 'readAll':
          return <String, String>{};
        default:
          return null;
      }
    });

    // Mock geolocator
    const geolocatorChannel = MethodChannel('flutter.baseflow.com/geolocator');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(geolocatorChannel, (MethodCall methodCall) async {
      switch (methodCall.method) {
        case 'getCurrentPosition':
          return {
            'latitude': -1.2921,
            'longitude': 36.8219,
            'timestamp': DateTime.now().millisecondsSinceEpoch,
            'accuracy': 10.0,
            'altitude': 1661.0,
            'heading': 0.0,
            'speed': 0.0,
            'speedAccuracy': 0.0,
          };
        case 'getLocationAccuracy':
          return 'high';
        case 'checkPermission':
          return 'granted';
        case 'requestPermission':
          return 'granted';
        default:
          return null;
      }
    });

    // Mock connectivity
    const connectivityChannel = MethodChannel('dev.fluttercommunity.plus/connectivity');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, (MethodCall methodCall) async {
      switch (methodCall.method) {
        case 'check':
          return 'wifi';
        default:
          return null;
      }
    });

    // Mock local auth
    const localAuthChannel = MethodChannel('plugins.flutter.io/local_auth');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(localAuthChannel, (MethodCall methodCall) async {
      switch (methodCall.method) {
        case 'authenticate':
          return true;
        case 'getAvailableBiometrics':
          return ['fingerprint'];
        case 'isDeviceSupported':
          return true;
        default:
          return null;
      }
    });
  }

  /// Clean up after tests
  static Future<void> cleanup() async {
    if (Hive.isBoxOpen('test')) {
      await Hive.box('test').clear();
      await Hive.box('test').close();
    }
    await Hive.deleteFromDisk();
  }
}

/// Wrapper for widget tests that require network image mocking
Future<void> testWithNetworkImages(
  String description,
  Future<void> Function(WidgetTester) callback, {
  bool? skip,
  Timeout? timeout,
  bool semanticsEnabled = true,
  TestVariant<Object?> variant = const DefaultTestVariant(),
  dynamic tags,
}) {
  testWidgets(
    description,
    (tester) async {
      await mockNetworkImagesFor(() async {
        await callback(tester);
      });
    },
    skip: skip,
    timeout: timeout,
    semanticsEnabled: semanticsEnabled,
    variant: variant,
    tags: tags,
  );
}

/// Common test utilities and constants
class TestConstants {
  // Test user data
  static const testUser = {
    'id': 'test-user-123',
    'email': 'test@example.com',
    'name': 'Test User',
    'role': 'healthcare_worker',
  };

  // Test location data
  static const testLocation = {
    'latitude': -1.2921,
    'longitude': 36.8219,
    'region': 'Nairobi',
    'country': 'Kenya',
  };

  // Test risk data
  static const testRiskData = {
    'region': 'Nairobi',
    'riskLevel': 'medium',
    'riskScore': 0.65,
    'timestamp': '2024-01-15T12:00:00Z',
  };

  // API endpoints for testing
  static const apiBaseUrl = 'https://test-api.malaria-prediction.org/v1';
  static const mockResponses = {
    'auth/login': {'token': 'mock-jwt-token', 'user': testUser},
    'risk-data': [testRiskData],
    'predictions': [],
    'alerts': [],
  };
}