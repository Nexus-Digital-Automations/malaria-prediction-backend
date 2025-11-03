# Flutter Frontend Documentation

> **📱 Complete guide to the Flutter frontend application**

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Setup & Installation](#setup--installation)
- [BLoC Pattern Implementation](#bloc-pattern-implementation)
- [Features](#features)
- [API Integration](#api-integration)
- [UI Components](#ui-components)
- [Testing](#testing)

---

## Overview

The Malaria Prediction frontend is a cross-platform Flutter application that provides:

- 📊 **Interactive Risk Maps** - Real-time malaria risk visualization
- 🚨 **Alert System** - Push notifications for high-risk predictions
- 📈 **Analytics Dashboard** - Comprehensive data visualization
- 🏥 **Healthcare Tools** - Patient management and treatment protocols
- 📱 **Offline Support** - Local data caching for poor connectivity

**Supported Platforms**:
- ✅ Android 6.0+ (API 23+)
- ✅ iOS 12.0+
- ✅ Web (responsive)
- ⏳ Desktop (planned)

---

## Architecture

### Project Structure

```
malaria_frontend/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── app.dart                  # Root app widget
│   │
│   ├── core/                     # Core functionality
│   │   ├── config/               # App configuration
│   │   ├── constants/            # Constants & enums
│   │   ├── errors/               # Error handling
│   │   ├── network/              # HTTP client setup
│   │   ├── theme/                # App theming
│   │   └── utils/                # Utilities & helpers
│   │
│   ├── data/                     # Data layer
│   │   ├── models/               # Data models
│   │   ├── repositories/         # Repository implementations
│   │   └── datasources/          # API & local data sources
│   │       ├── remote/           # API clients
│   │       └── local/            # Local storage
│   │
│   ├── domain/                   # Business logic layer
│   │   ├── entities/             # Domain entities
│   │   ├── repositories/         # Repository interfaces
│   │   └── usecases/             # Use cases
│   │
│   ├── presentation/             # Presentation layer
│   │   ├── blocs/                # BLoC state management
│   │   ├── pages/                # App pages/screens
│   │   ├── widgets/              # Reusable widgets
│   │   └── routes/               # Navigation & routing
│   │
│   └── injection_container.dart  # Dependency injection
│
├── test/                         # Unit & widget tests
├── integration_test/             # Integration tests
├── assets/                       # Images, fonts, etc.
└── pubspec.yaml                  # Dependencies
```

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│              Presentation Layer (UI)                    │
│  • BLoC State Management                                │
│  • Widgets & Pages                                      │
│  • User Input Handling                                  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Domain Layer (Business Logic)              │
│  • Use Cases                                            │
│  • Entities                                             │
│  • Repository Interfaces                                │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Data Layer (Data Sources)                  │
│  • Repository Implementations                           │
│  • API Clients (Remote)                                 │
│  • Local Storage (Hive, Shared Preferences)            │
└─────────────────────────────────────────────────────────┘
```

---

## Setup & Installation

### Prerequisites
- **Flutter SDK** 3.0.0+
- **Dart** 3.0.0+
- **Android Studio** or **VS Code** with Flutter extensions
- **Xcode** (for iOS development, macOS only)

### Installation Steps

```bash
# 1. Navigate to frontend directory
cd malaria_frontend

# 2. Install dependencies
flutter pub get

# 3. Generate code (for json_serializable, freezed, etc.)
flutter pub run build_runner build --delete-conflicting-outputs

# 4. Run on device/emulator
flutter run

# Or specify platform
flutter run -d chrome        # Web
flutter run -d android       # Android
flutter run -d ios           # iOS
```

### Environment Configuration

```dart
// lib/core/config/env_config.dart
abstract class EnvConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000'
  );

  static const String wsBaseUrl = String.fromEnvironment(
    'WS_BASE_URL',
    defaultValue: 'ws://localhost:8000/ws'
  );

  static const bool enableLogging = bool.fromEnvironment(
    'ENABLE_LOGGING',
    defaultValue: true
  );
}

// Run with environment variables
// flutter run --dart-define=API_BASE_URL=https://api.example.com
```

---

## BLoC Pattern Implementation

### BLoC Overview

The app uses **BLoC (Business Logic Component)** pattern for state management:

```dart
// presentation/blocs/prediction/prediction_bloc.dart
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part 'prediction_event.dart';
part 'prediction_state.dart';
part 'prediction_bloc.freezed.dart';

class PredictionBloc extends Bloc<PredictionEvent, PredictionState> {
  final GetPrediction getPrediction;

  PredictionBloc({required this.getPrediction})
      : super(const PredictionState.initial()) {
    on<PredictionRequested>(_onPredictionRequested);
  }

  Future<void> _onPredictionRequested(
    PredictionRequested event,
    Emitter<PredictionState> emit,
  ) async {
    emit(const PredictionState.loading());

    final result = await getPrediction(event.request);

    result.fold(
      (failure) => emit(PredictionState.error(failure.message)),
      (prediction) => emit(PredictionState.loaded(prediction)),
    );
  }
}

// Events
@freezed
class PredictionEvent with _$PredictionEvent {
  const factory PredictionEvent.requested(PredictionRequest request) =
      PredictionRequested;
}

// States
@freezed
class PredictionState with _$PredictionState {
  const factory PredictionState.initial() = _Initial;
  const factory PredictionState.loading() = _Loading;
  const factory PredictionState.loaded(Prediction prediction) = _Loaded;
  const factory PredictionState.error(String message) = _Error;
}
```

### Using BLoC in UI

```dart
// presentation/pages/prediction_page.dart
class PredictionPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => sl<PredictionBloc>(),
      child: Scaffold(
        appBar: AppBar(title: Text('Malaria Prediction')),
        body: BlocConsumer<PredictionBloc, PredictionState>(
          listener: (context, state) {
            state.maybeWhen(
              error: (message) => ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(message)),
              ),
              orElse: () {},
            );
          },
          builder: (context, state) {
            return state.when(
              initial: () => _buildInitialView(),
              loading: () => Center(child: CircularProgressIndicator()),
              loaded: (prediction) => _buildPredictionView(prediction),
              error: (message) => _buildErrorView(message),
            );
          },
        ),
        floatingActionButton: FloatingActionButton(
          onPressed: () => _requestPrediction(context),
          child: Icon(Icons.analytics),
        ),
      ),
    );
  }

  void _requestPrediction(BuildContext context) {
    final request = PredictionRequest(
      location: Location(latitude: -1.2921, longitude: 36.8219),
      predictionDate: DateTime.now(),
      modelType: ModelType.ensemble,
    );

    context.read<PredictionBloc>().add(
      PredictionEvent.requested(request),
    );
  }
}
```

---

## Features

### 1. Interactive Risk Maps

**Location**: `lib/presentation/pages/map/risk_map_page.dart`

```dart
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class RiskMapPage extends StatefulWidget {
  @override
  _RiskMapPageState createState() => _RiskMapPageState();
}

class _RiskMapPageState extends State<RiskMapPage> {
  final MapController _mapController = MapController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FlutterMap(
        mapController: _mapController,
        options: MapOptions(
          center: LatLng(-1.2921, 36.8219),  // Nairobi
          zoom: 10.0,
          maxZoom: 18.0,
          minZoom: 5.0,
        ),
        children: [
          // Base map tiles
          TileLayer(
            urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            userAgentPackageName: 'com.example.malaria_frontend',
          ),

          // Risk overlay (choropleth)
          PolygonLayer(
            polygons: _buildRiskPolygons(),
          ),

          // Health facility markers
          MarkerLayer(
            markers: _buildHealthFacilityMarkers(),
          ),
        ],
      ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton(
            heroTag: 'zoom_in',
            mini: true,
            onPressed: () => _mapController.move(
              _mapController.center,
              _mapController.zoom + 1,
            ),
            child: Icon(Icons.add),
          ),
          SizedBox(height: 8),
          FloatingActionButton(
            heroTag: 'zoom_out',
            mini: true,
            onPressed: () => _mapController.move(
              _mapController.center,
              _mapController.zoom - 1,
            ),
            child: Icon(Icons.remove),
          ),
        ],
      ),
    );
  }

  List<Polygon> _buildRiskPolygons() {
    // Build choropleth polygons based on risk scores
    return [
      Polygon(
        points: [/* polygon coordinates */],
        color: _getRiskColor(0.75).withOpacity(0.5),
        borderColor: _getRiskColor(0.75),
        borderStrokeWidth: 2,
      ),
      // ... more polygons
    ];
  }

  Color _getRiskColor(double riskScore) {
    if (riskScore < 0.3) return Colors.green;
    if (riskScore < 0.6) return Colors.yellow;
    if (riskScore < 0.8) return Colors.orange;
    return Colors.red;
  }

  List<Marker> _buildHealthFacilityMarkers() {
    // Build markers for health facilities
    return [
      Marker(
        point: LatLng(-1.2921, 36.8219),
        builder: (ctx) => Icon(
          Icons.local_hospital,
          color: Colors.blue,
          size: 32,
        ),
      ),
    ];
  }
}
```

### 2. Analytics Dashboard

**Location**: `lib/presentation/pages/analytics/analytics_page.dart`

```dart
import 'package:fl_chart/fl_chart.dart';

class AnalyticsDashboard extends StatelessWidget {
  final List<PredictionData> predictions;

  const AnalyticsDashboard({required this.predictions});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Risk trend line chart
          _buildRiskTrendChart(),
          SizedBox(height: 24),

          // Environmental factors bar chart
          _buildFactorsChart(),
          SizedBox(height: 24),

          // Risk distribution pie chart
          _buildRiskDistributionChart(),
        ],
      ),
    );
  }

  Widget _buildRiskTrendChart() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Risk Trend', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(show: true),
                  titlesData: FlTitlesData(show: true),
                  borderData: FlBorderData(show: true),
                  lineBarsData: [
                    LineChartBarData(
                      spots: _getRiskSpots(),
                      isCurved: true,
                      color: Colors.blue,
                      barWidth: 3,
                      dotData: FlDotData(show: true),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<FlSpot> _getRiskSpots() {
    return predictions
        .asMap()
        .entries
        .map((entry) => FlSpot(
              entry.key.toDouble(),
              entry.value.riskScore,
            ))
        .toList();
  }

  Widget _buildFactorsChart() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Contributing Factors', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  barGroups: [
                    BarChartGroupData(x: 0, barRods: [BarChartRodData(toY: 0.35, color: Colors.red)]),
                    BarChartGroupData(x: 1, barRods: [BarChartRodData(toY: 0.28, color: Colors.blue)]),
                    BarChartGroupData(x: 2, barRods: [BarChartRodData(toY: 0.22, color: Colors.green)]),
                    BarChartGroupData(x: 3, barRods: [BarChartRodData(toY: 0.15, color: Colors.orange)]),
                  ],
                  titlesData: FlTitlesData(
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          const titles = ['Temp', 'Rain', 'Humidity', 'NDVI'];
                          return Text(titles[value.toInt()]);
                        },
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRiskDistributionChart() {
    // Pie chart implementation
    return Card(/* ... */);
  }
}
```

### 3. Push Notifications

**Location**: `lib/core/services/notification_service.dart`

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  Future<void> initialize() async {
    // Request permissions
    await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // Get FCM token
    final token = await _fcm.getToken();
    print('FCM Token: $token');

    // Configure local notifications
    const initializationSettings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      iOS: DarwinInitializationSettings(),
    );

    await _localNotifications.initialize(initializationSettings);

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_handleBackgroundMessage);
  }

  void _handleForegroundMessage(RemoteMessage message) {
    final notification = message.notification;
    if (notification == null) return;

    _localNotifications.show(
      notification.hashCode,
      notification.title,
      notification.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          'high_risk_channel',
          'High Risk Alerts',
          importance: Importance.max,
          priority: Priority.high,
        ),
      ),
    );
  }

  static Future<void> _handleBackgroundMessage(RemoteMessage message) async {
    print('Background message: ${message.messageId}');
  }
}
```

---

## API Integration

### HTTP Client Setup

```dart
// core/network/dio_client.dart
import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

class DioClient {
  late final Dio _dio;

  DioClient({required String baseUrl}) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: Duration(seconds: 30),
        receiveTimeout: Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    // Add interceptors
    _dio.interceptors.addAll([
      AuthInterceptor(),
      PrettyDioLogger(
        requestHeader: true,
        requestBody: true,
        responseBody: true,
        responseHeader: false,
        error: true,
        compact: true,
      ),
    ]);
  }

  Dio get dio => _dio;
}

// Auth interceptor to add JWT token
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _getToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<String?> _getToken() async {
    // Retrieve token from secure storage
    final storage = await SharedPreferences.getInstance();
    return storage.getString('auth_token');
  }
}
```

### API Client Example

```dart
// data/datasources/remote/prediction_api_client.dart
class PredictionApiClient {
  final Dio _dio;

  PredictionApiClient(this._dio);

  Future<PredictionResponse> getPrediction(
    PredictionRequest request,
  ) async {
    try {
      final response = await _dio.post(
        '/predict/single',
        data: request.toJson(),
      );

      return PredictionResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  ApiException _handleError(DioException error) {
    if (error.response != null) {
      return ApiException(
        message: error.response!.data['detail'] ?? 'Unknown error',
        statusCode: error.response!.statusCode,
      );
    } else {
      return ApiException(
        message: 'Network error: ${error.message}',
      );
    }
  }
}
```

---

## Testing

### Unit Tests

```dart
// test/domain/usecases/get_prediction_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';

class MockPredictionRepository extends Mock implements PredictionRepository {}

void main() {
  late GetPrediction usecase;
  late MockPredictionRepository mockRepository;

  setUp(() {
    mockRepository = MockPredictionRepository();
    usecase = GetPrediction(mockRepository);
  });

  test('should get prediction from repository', () async {
    // Arrange
    final request = PredictionRequest(/* ... */);
    final expected = Prediction(/* ... */);
    when(mockRepository.getPrediction(request))
        .thenAnswer((_) async => Right(expected));

    // Act
    final result = await usecase(request);

    // Assert
    expect(result, Right(expected));
    verify(mockRepository.getPrediction(request));
    verifyNoMoreInteractions(mockRepository);
  });
}
```

### Widget Tests

```dart
// test/presentation/pages/prediction_page_test.dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('PredictionPage displays loading indicator', (tester) async {
    // Build widget
    await tester.pumpWidget(
      MaterialApp(
        home: BlocProvider(
          create: (_) => mockPredictionBloc,
          child: PredictionPage(),
        ),
      ),
    );

    // Emit loading state
    whenListen(
      mockPredictionBloc,
      Stream.value(PredictionState.loading()),
    );

    await tester.pump();

    // Verify loading indicator is shown
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
```

---

## Additional Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [BLoC Pattern Guide](https://bloclibrary.dev/)
- [Flutter Map Package](https://pub.dev/packages/flutter_map)
- [FL Chart Package](https://pub.dev/packages/fl_chart)

---

**Last Updated**: November 3, 2025
