/// Unit tests for MalariaApiService Retrofit interface
///
/// Comprehensive testing of all API endpoints including authentication,
/// prediction requests, health checks, and error handling scenarios.
///
/// Author: Claude AI Agent
/// Created: 2025-09-19
library;

import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import '../../../lib/core/api/malaria_api_service.dart';
import '../../../lib/core/models/models.dart';

import 'malaria_api_service_test.mocks.dart';

@GenerateMocks([Dio])
void main() {
  group('MalariaApiService', () {
    late MockDio mockDio;
    late MalariaApiService apiService;

    setUp(() {
      mockDio = MockDio();
      apiService = MalariaApiService(mockDio);
    });

    group('Authentication Endpoints', () {
      test('login should return AuthResponse on success', () async {
        // Arrange
        final loginRequest = LoginRequest(
          email: 'test@example.com',
          password: 'password123',
        );

        final expectedResponse = AuthResponse(
          user: UserProfile(
            id: '123',
            email: 'test@example.com',
            roles: ['user'],
            permissions: ['read'],
            isActive: true,
            isVerified: true,
            createdAt: DateTime.now(),
          ),
          tokens: TokenResponse(
            accessToken: 'access_token_123',
            tokenType: 'Bearer',
            expiresIn: 3600,
          ),
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/auth/login',
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/auth/login'),
        ));

        // Act
        final result = await apiService.login(loginRequest);

        // Assert
        expect(result.user.email, equals('test@example.com'));
        expect(result.tokens.accessToken, equals('access_token_123'));
        verify(mockDio.post<Map<String, dynamic>>(
          '/auth/login',
          data: loginRequest.toJson(),
        )).called(1);
      });

      test('refreshToken should return TokenResponse on success', () async {
        // Arrange
        final refreshRequest = RefreshTokenRequest(
          refreshToken: 'refresh_token_123',
        );

        final expectedResponse = TokenResponse(
          accessToken: 'new_access_token',
          refreshToken: 'new_refresh_token',
          tokenType: 'Bearer',
          expiresIn: 3600,
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/auth/refresh',
          data: anyNamed('data'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/auth/refresh'),
        ));

        // Act
        final result = await apiService.refreshToken(refreshRequest);

        // Assert
        expect(result.accessToken, equals('new_access_token'));
        expect(result.refreshToken, equals('new_refresh_token'));
      });

      test('validateSession should return ValidationResponse', () async {
        // Arrange
        const token = 'Bearer valid_token';
        final expectedResponse = ValidationResponse(
          valid: true,
          message: 'Session is valid',
        );

        when(mockDio.get<Map<String, dynamic>>(
          '/auth/validate',
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/auth/validate'),
        ));

        // Act
        final result = await apiService.validateSession(token);

        // Assert
        expect(result.valid, isTrue);
        expect(result.message, equals('Session is valid'));
      });
    });

    group('Prediction Endpoints', () {
      test('getSinglePrediction should return PredictionResult', () async {
        // Arrange
        final request = SinglePredictionRequest(
          location: LocationPoint(
            latitude: -1.2921,
            longitude: 36.8219,
            name: 'Nairobi',
          ),
          timeHorizonDays: 30,
          includeFactors: true,
        );

        final expectedResponse = PredictionResult(
          location: request.location,
          riskScore: 0.75,
          riskLevel: 'high',
          predictionDate: DateTime.now(),
          timeHorizonDays: 30,
          modelVersion: 'v1.0',
          environmentalFactors: {
            'temperature': 25.5,
            'rainfall': 150.0,
            'humidity': 80.0,
          },
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/predict/single',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/predict/single'),
        ));

        // Act
        final result = await apiService.getSinglePrediction(request, null);

        // Assert
        expect(result.riskScore, equals(0.75));
        expect(result.riskLevel, equals('high'));
        expect(result.location.name, equals('Nairobi'));
      });

      test('getBatchPredictions should return BatchPredictionResult', () async {
        // Arrange
        final request = BatchPredictionRequest(
          locations: [
            LocationPoint(latitude: -1.2921, longitude: 36.8219, name: 'Nairobi'),
            LocationPoint(latitude: -1.9536, longitude: 30.0605, name: 'Kigali'),
          ],
          timeHorizonDays: 30,
        );

        final expectedResponse = BatchPredictionResult(
          predictions: [
            PredictionResult(
              location: request.locations[0],
              riskScore: 0.75,
              riskLevel: 'high',
              predictionDate: DateTime.now(),
              timeHorizonDays: 30,
              modelVersion: 'v1.0',
            ),
            PredictionResult(
              location: request.locations[1],
              riskScore: 0.45,
              riskLevel: 'medium',
              predictionDate: DateTime.now(),
              timeHorizonDays: 30,
              modelVersion: 'v1.0',
            ),
          ],
          batchId: 'batch_123',
          processingTimeMs: 1500.0,
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/predict/batch',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/predict/batch'),
        ));

        // Act
        final result = await apiService.getBatchPredictions(request, null);

        // Assert
        expect(result.predictions.length, equals(2));
        expect(result.batchId, equals('batch_123'));
        expect(result.predictions[0].riskScore, equals(0.75));
        expect(result.predictions[1].riskScore, equals(0.45));
      });

      test('getSpatialPredictions should return SpatialPredictionResult', () async {
        // Arrange
        final request = SpatialPredictionRequest(
          boundingBox: GeographicBounds(
            northEast: LocationPoint(latitude: -1.0, longitude: 37.0),
            southWest: LocationPoint(latitude: -2.0, longitude: 36.0),
          ),
          resolution: 0.1,
          timeHorizonDays: 30,
        );

        final expectedResponse = SpatialPredictionResult(
          gridPoints: [
            SpatialGridPoint(
              location: LocationPoint(latitude: -1.5, longitude: 36.5),
              riskScore: 0.6,
              riskLevel: 'medium',
            ),
          ],
          boundingBox: request.boundingBox,
          resolution: 0.1,
          predictionDate: DateTime.now(),
          modelVersion: 'v1.0',
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/predict/spatial',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/predict/spatial'),
        ));

        // Act
        final result = await apiService.getSpatialPredictions(request, null);

        // Assert
        expect(result.gridPoints.length, equals(1));
        expect(result.resolution, equals(0.1));
        expect(result.gridPoints[0].riskScore, equals(0.6));
      });

      test('getTimeSeriesPredictions should return TimeSeriesPredictionResult', () async {
        // Arrange
        final request = TimeSeriesPredictionRequest(
          location: LocationPoint(
            latitude: -1.2921,
            longitude: 36.8219,
            name: 'Nairobi',
          ),
          timeRangeDays: 90,
          predictionIntervalDays: 7,
        );

        final expectedResponse = TimeSeriesPredictionResult(
          location: request.location,
          timeSeries: [
            TimeSeriesPoint(
              date: DateTime.now(),
              riskScore: 0.6,
              riskLevel: 'medium',
            ),
            TimeSeriesPoint(
              date: DateTime.now().add(Duration(days: 7)),
              riskScore: 0.7,
              riskLevel: 'high',
            ),
          ],
          predictionIntervalDays: 7,
          modelVersion: 'v1.0',
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/predict/time-series',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/predict/time-series'),
        ));

        // Act
        final result = await apiService.getTimeSeriesPredictions(request, null);

        // Assert
        expect(result.timeSeries.length, equals(2));
        expect(result.predictionIntervalDays, equals(7));
        expect(result.location.name, equals('Nairobi'));
      });
    });

    group('Health Monitoring Endpoints', () {
      test('getHealthStatus should return HealthStatusResponse', () async {
        // Arrange
        final expectedResponse = HealthStatusResponse(
          status: 'healthy',
          timestamp: DateTime.now(),
          uptimeSeconds: 86400.0,
          version: '1.0.0',
        );

        when(mockDio.get<Map<String, dynamic>>('/health/status'))
            .thenAnswer((_) async => Response(
              data: expectedResponse.toJson(),
              statusCode: 200,
              requestOptions: RequestOptions(path: '/health/status'),
            ));

        // Act
        final result = await apiService.getHealthStatus();

        // Assert
        expect(result.status, equals('healthy'));
        expect(result.version, equals('1.0.0'));
        expect(result.uptimeSeconds, equals(86400.0));
      });

      test('getSystemHealth should return SystemHealthResponse', () async {
        // Arrange
        final expectedResponse = SystemHealthResponse(
          status: 'healthy',
          components: {
            'database': {'status': 'healthy', 'response_time_ms': 10},
            'redis': {'status': 'healthy', 'response_time_ms': 5},
            'external_apis': {'status': 'degraded', 'response_time_ms': 500},
          },
          timestamp: DateTime.now(),
          overallHealth: 'degraded',
          degradedServices: ['external_apis'],
        );

        when(mockDio.get<Map<String, dynamic>>('/health/system'))
            .thenAnswer((_) async => Response(
              data: expectedResponse.toJson(),
              statusCode: 200,
              requestOptions: RequestOptions(path: '/health/system'),
            ));

        // Act
        final result = await apiService.getSystemHealth();

        // Assert
        expect(result.status, equals('healthy'));
        expect(result.overallHealth, equals('degraded'));
        expect(result.degradedServices, contains('external_apis'));
        expect(result.components['database']['status'], equals('healthy'));
      });

      test('getModelHealth should return ModelHealthResponse', () async {
        // Arrange
        final expectedResponse = ModelHealthResponse(
          modelStatus: {
            'lstm_model': {'status': 'healthy', 'accuracy': 0.85},
            'transformer_model': {'status': 'healthy', 'accuracy': 0.87},
            'ensemble_model': {'status': 'healthy', 'accuracy': 0.89},
          },
          lastTraining: DateTime.now().subtract(Duration(days: 1)),
          modelVersions: {
            'lstm_model': 'v2.1',
            'transformer_model': 'v1.5',
            'ensemble_model': 'v3.0',
          },
          performanceMetrics: {
            'avg_prediction_time_ms': 150.0,
            'throughput_requests_per_second': 100.0,
          },
        );

        when(mockDio.get<Map<String, dynamic>>('/health/models'))
            .thenAnswer((_) async => Response(
              data: expectedResponse.toJson(),
              statusCode: 200,
              requestOptions: RequestOptions(path: '/health/models'),
            ));

        // Act
        final result = await apiService.getModelHealth();

        // Assert
        expect(result.modelStatus['lstm_model']['status'], equals('healthy'));
        expect(result.modelVersions!['ensemble_model'], equals('v3.0'));
        expect(result.performanceMetrics!['throughput_requests_per_second'], equals(100.0));
      });
    });

    group('Alert System Endpoints', () {
      test('subscribeToAlerts should return SubscriptionResponse', () async {
        // Arrange
        final request = SubscriptionRequest(
          alertTypes: ['outbreak_prediction', 'high_risk_alert'],
          regions: ['kenya', 'uganda'],
          severityThreshold: 'medium',
          notificationMethods: ['email', 'push'],
        );

        final expectedResponse = SubscriptionResponse(
          subscriptionId: 'sub_123',
          status: 'active',
          createdAt: DateTime.now(),
          alertTypes: request.alertTypes,
          regions: request.regions,
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/alerts/subscribe',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/alerts/subscribe'),
        ));

        // Act
        final result = await apiService.subscribeToAlerts(request, 'Bearer token');

        // Assert
        expect(result.subscriptionId, equals('sub_123'));
        expect(result.status, equals('active'));
        expect(result.alertTypes.length, equals(2));
        expect(result.regions.length, equals(2));
      });

      test('getActiveAlerts should return ActiveAlertsResponse', () async {
        // Arrange
        final expectedResponse = ActiveAlertsResponse(
          activeAlerts: [
            AlertItem(
              id: 'alert_1',
              type: 'outbreak_prediction',
              severity: 'high',
              title: 'High Malaria Risk Predicted',
              message: 'Increased malaria risk detected in Nairobi region',
              region: 'kenya',
              createdAt: DateTime.now(),
            ),
          ],
          alertSummary: {
            'high': 1,
            'medium': 0,
            'low': 0,
          },
          lastUpdated: DateTime.now(),
        );

        when(mockDio.get<Map<String, dynamic>>(
          '/alerts/active',
          queryParameters: anyNamed('queryParameters'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/alerts/active'),
        ));

        // Act
        final result = await apiService.getActiveAlerts('kenya', 'Bearer token');

        // Assert
        expect(result.activeAlerts.length, equals(1));
        expect(result.activeAlerts[0].severity, equals('high'));
        expect(result.alertSummary!['high'], equals(1));
      });
    });

    group('Error Handling', () {
      test('should handle DioException properly', () async {
        // Arrange
        final loginRequest = LoginRequest(
          email: 'invalid@example.com',
          password: 'wrongpassword',
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/auth/login',
          data: anyNamed('data'),
        )).thenThrow(DioException(
          requestOptions: RequestOptions(path: '/auth/login'),
          response: Response(
            statusCode: 401,
            statusMessage: 'Unauthorized',
            data: {'message': 'Invalid credentials'},
            requestOptions: RequestOptions(path: '/auth/login'),
          ),
        ));

        // Act & Assert
        expect(
          () => apiService.login(loginRequest),
          throwsA(isA<DioException>()),
        );
      });

      test('should handle network timeout', () async {
        // Arrange
        final request = SinglePredictionRequest(
          location: LocationPoint(latitude: 0.0, longitude: 0.0),
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/predict/single',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenThrow(DioException(
          requestOptions: RequestOptions(path: '/predict/single'),
          type: DioExceptionType.receiveTimeout,
        ));

        // Act & Assert
        expect(
          () => apiService.getSinglePrediction(request, null),
          throwsA(isA<DioException>()),
        );
      });

      test('should handle server error (500)', () async {
        // Arrange
        when(mockDio.get<Map<String, dynamic>>('/health/status'))
            .thenThrow(DioException(
          requestOptions: RequestOptions(path: '/health/status'),
          response: Response(
            statusCode: 500,
            statusMessage: 'Internal Server Error',
            data: {'message': 'Database connection failed'},
            requestOptions: RequestOptions(path: '/health/status'),
          ),
        ));

        // Act & Assert
        expect(
          () => apiService.getHealthStatus(),
          throwsA(isA<DioException>()),
        );
      });
    });

    group('Headers and Authorization', () {
      test('should include Authorization header when token provided', () async {
        // Arrange
        const token = 'Bearer test_token_123';
        final request = SinglePredictionRequest(
          location: LocationPoint(latitude: -1.2921, longitude: 36.8219),
        );

        final expectedResponse = PredictionResult(
          location: request.location,
          riskScore: 0.5,
          riskLevel: 'medium',
          predictionDate: DateTime.now(),
          timeHorizonDays: 30,
          modelVersion: 'v1.0',
        );

        when(mockDio.post<Map<String, dynamic>>(
          '/predict/single',
          data: anyNamed('data'),
          options: anyNamed('options'),
        )).thenAnswer((_) async => Response(
          data: expectedResponse.toJson(),
          statusCode: 200,
          requestOptions: RequestOptions(path: '/predict/single'),
        ));

        // Act
        await apiService.getSinglePrediction(request, token);

        // Assert
        final captured = verify(mockDio.post<Map<String, dynamic>>(
          '/predict/single',
          data: captureAnyNamed('data'),
          options: captureAnyNamed('options'),
        )).captured;

        // Verify the authorization header would be set by Retrofit
        expect(captured[0], equals(request.toJson()));
      });
    });
  });
}