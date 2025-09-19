/// Unit tests for AuthInterceptor
///
/// Tests authentication header injection, token refresh logic,
/// request queuing, and error handling scenarios.
///
/// Author: Claude AI Agent
/// Created: 2025-09-19
library;

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:logger/logger.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

import '../../../lib/core/auth/token_manager.dart';
import '../../../lib/core/network/auth_interceptor.dart';

import 'auth_interceptor_test.mocks.dart';

@GenerateMocks([TokenManager, Logger, RequestInterceptorHandler, ResponseInterceptorHandler, ErrorInterceptorHandler])
void main() {
  group('AuthInterceptor', () {
    late MockTokenManager mockTokenManager;
    late MockLogger mockLogger;
    late AuthInterceptor authInterceptor;

    setUp(() {
      mockTokenManager = MockTokenManager();
      mockLogger = MockLogger();
      authInterceptor = AuthInterceptor(
        tokenManager: mockTokenManager,
        logger: mockLogger,
      );
    });

    group('onRequest', () {
      test('should skip authentication for excluded paths', () async {
        // Arrange
        final options = RequestOptions(path: '/auth/login');
        final handler = MockRequestInterceptorHandler();

        // Act
        await authInterceptor.onRequest(options, handler);

        // Assert
        verify(handler.next(options)).called(1);
        verifyNever(mockTokenManager.getAccessToken());
      });

      test('should add Authorization header for authenticated requests', () async {
        // Arrange
        const accessToken = 'test_access_token';
        final options = RequestOptions(path: '/predict/single');
        final handler = MockRequestInterceptorHandler();

        when(mockTokenManager.getAccessToken()).thenAnswer((_) async => accessToken);
        when(mockTokenManager.isTokenExpired()).thenAnswer((_) async => false);
        when(mockTokenManager.isTokenNearExpiry(bufferMinutes: anyNamed('bufferMinutes')))
            .thenAnswer((_) async => false);

        // Act
        await authInterceptor.onRequest(options, handler);

        // Assert
        expect(options.headers['Authorization'], equals('Bearer $accessToken'));
        verify(handler.next(options)).called(1);
      });

      test('should refresh token when expired', () async {
        // Arrange
        const newAccessToken = 'new_access_token';
        final options = RequestOptions(path: '/predict/single');
        final handler = MockRequestInterceptorHandler();

        when(mockTokenManager.getAccessToken())
            .thenAnswer((_) async => 'old_token')
            .thenAnswer((_) async => newAccessToken);
        when(mockTokenManager.isTokenExpired()).thenAnswer((_) async => true);
        when(mockTokenManager.refreshToken()).thenAnswer((_) async => true);

        // Act
        await authInterceptor.onRequest(options, handler);

        // Assert
        verify(mockTokenManager.refreshToken()).called(1);
        verify(handler.next(options)).called(1);
      });

      test('should queue requests during token refresh', () async {
        // Arrange
        final options1 = RequestOptions(path: '/predict/single');
        final options2 = RequestOptions(path: '/predict/batch');
        final handler1 = MockRequestInterceptorHandler();
        final handler2 = MockRequestInterceptorHandler();

        when(mockTokenManager.getAccessToken()).thenAnswer((_) async => 'old_token');
        when(mockTokenManager.isTokenExpired()).thenAnswer((_) async => true);
        when(mockTokenManager.refreshToken()).thenAnswer((_) async {
          // Simulate slow refresh
          await Future.delayed(Duration(milliseconds: 100));
          return true;
        });

        // Act
        final future1 = authInterceptor.onRequest(options1, handler1);
        final future2 = authInterceptor.onRequest(options2, handler2);

        await Future.wait([future1, future2]);

        // Assert
        expect(authInterceptor.queueSize, equals(0)); // Queue should be cleared after processing
        verify(mockTokenManager.refreshToken()).called(1); // Only one refresh should occur
      });

      test('should handle token refresh failure', () async {
        // Arrange
        final options = RequestOptions(path: '/predict/single');
        final handler = MockRequestInterceptorHandler();

        when(mockTokenManager.getAccessToken()).thenAnswer((_) async => 'old_token');
        when(mockTokenManager.isTokenExpired()).thenAnswer((_) async => true);
        when(mockTokenManager.refreshToken()).thenAnswer((_) async => false);

        // Act & Assert
        expect(
          () => authInterceptor.onRequest(options, handler),
          throwsA(isA<Exception>()),
        );
      });

      test('should handle missing access token', () async {
        // Arrange
        final options = RequestOptions(path: '/predict/single');
        final handler = MockRequestInterceptorHandler();

        when(mockTokenManager.getAccessToken()).thenAnswer((_) async => null);

        // Act & Assert
        expect(
          () => authInterceptor.onRequest(options, handler),
          throwsA(isA<Exception>()),
        );
      });
    });

    group('onResponse', () {
      test('should log successful authenticated requests', () async {
        // Arrange
        final requestOptions = RequestOptions(path: '/predict/single');
        requestOptions.headers['Authorization'] = 'Bearer token';
        final response = Response(
          requestOptions: requestOptions,
          statusCode: 200,
          data: {'result': 'success'},
        );
        final handler = MockResponseInterceptorHandler();

        // Act
        await authInterceptor.onResponse(response, handler);

        // Assert
        verify(handler.next(response)).called(1);
        verify(mockLogger.d(any)).called(1);
      });
    });

    group('onError', () {
      test('should handle 401 error with token refresh', () async {
        // Arrange
        final requestOptions = RequestOptions(path: '/predict/single');
        final dioError = DioException(
          requestOptions: requestOptions,
          response: Response(
            requestOptions: requestOptions,
            statusCode: 401,
            statusMessage: 'Unauthorized',
          ),
        );
        final handler = MockErrorInterceptorHandler();

        when(mockTokenManager.refreshToken()).thenAnswer((_) async => true);
        when(mockTokenManager.getAccessToken()).thenAnswer((_) async => 'new_token');

        // Act
        await authInterceptor.onError(dioError, handler);

        // Assert
        verify(mockTokenManager.refreshToken()).called(1);
      });

      test('should skip refresh for auth endpoints', () async {
        // Arrange
        final requestOptions = RequestOptions(path: '/auth/login');
        final dioError = DioException(
          requestOptions: requestOptions,
          response: Response(
            requestOptions: requestOptions,
            statusCode: 401,
            statusMessage: 'Unauthorized',
          ),
        );
        final handler = MockErrorInterceptorHandler();

        // Act
        await authInterceptor.onError(dioError, handler);

        // Assert
        verify(handler.next(dioError)).called(1);
        verifyNever(mockTokenManager.refreshToken());
      });

      test('should handle 403 Forbidden error', () async {
        // Arrange
        final requestOptions = RequestOptions(path: '/admin/users');
        final dioError = DioException(
          requestOptions: requestOptions,
          response: Response(
            requestOptions: requestOptions,
            statusCode: 403,
            statusMessage: 'Forbidden',
          ),
        );
        final handler = MockErrorInterceptorHandler();

        // Act
        await authInterceptor.onError(dioError, handler);

        // Assert
        verify(handler.next(any)).called(1);
        verifyNever(mockTokenManager.refreshToken());
      });

      test('should clear tokens on refresh failure', () async {
        // Arrange
        final requestOptions = RequestOptions(path: '/predict/single');
        final dioError = DioException(
          requestOptions: requestOptions,
          response: Response(
            requestOptions: requestOptions,
            statusCode: 401,
            statusMessage: 'Unauthorized',
          ),
        );
        final handler = MockErrorInterceptorHandler();

        when(mockTokenManager.refreshToken()).thenAnswer((_) async => false);

        // Act
        await authInterceptor.onError(dioError, handler);

        // Assert
        verify(mockTokenManager.clearAuthData()).called(1);
      });
    });

    group('Configuration', () {
      test('should add and remove excluded paths', () {
        // Act
        authInterceptor.addExcludedPath('/custom/endpoint');

        // Assert
        expect(authInterceptor.excludedPaths, contains('/custom/endpoint'));

        // Act
        authInterceptor.removeExcludedPath('/custom/endpoint');

        // Assert
        expect(authInterceptor.excludedPaths, isNot(contains('/custom/endpoint')));
      });

      test('should provide queue size and refresh status', () {
        // Assert
        expect(authInterceptor.queueSize, isA<int>());
        expect(authInterceptor.isRefreshing, isA<bool>());
      });
    });

    group('Disposal', () {
      test('should dispose resources properly', () {
        // Act
        authInterceptor.dispose();

        // Assert
        expect(authInterceptor.queueSize, equals(0));
        expect(authInterceptor.isRefreshing, isFalse);
      });
    });
  });
}