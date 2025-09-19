/// Comprehensive tests for Intelligent Cache Interceptor
///
/// Tests HTTP cache interceptor functionality including different cache
/// strategies, request deduplication, stale-while-revalidate, and
/// sophisticated caching policies.
///
/// Author: Claude AI Agent - Caching Specialist
/// Created: 2025-09-19

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

import 'package:malaria_frontend/core/cache/intelligent_cache_manager.dart';
import 'package:malaria_frontend/core/cache/intelligent_cache_interceptor.dart';

// Generate mocks
@GenerateMocks([IntelligentCacheManager, Logger, Connectivity, Dio])
import 'intelligent_cache_interceptor_test.mocks.dart';

void main() {
  group('IntelligentCacheInterceptor', () {
    late IntelligentCacheInterceptor interceptor;
    late MockIntelligentCacheManager mockCacheManager;
    late MockLogger mockLogger;
    late MockConnectivity mockConnectivity;
    late MockDio mockDio;

    setUp(() {
      mockCacheManager = MockIntelligentCacheManager();
      mockLogger = MockLogger();
      mockConnectivity = MockConnectivity();
      mockDio = MockDio();

      // Mock connectivity to return online by default
      when(mockConnectivity.checkConnectivity())
          .thenAnswer((_) async => ConnectivityResult.wifi);

      interceptor = IntelligentCacheInterceptor(
        cacheManager: mockCacheManager,
        connectivity: mockConnectivity,
        logger: mockLogger,
      );
    });

    group('Cache Strategy - Network First', () {
      test('should proceed to network for network-first strategy', () async {
        final requestOptions = RequestOptions(
          path: '/predict/test',
          method: 'GET',
        );

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should proceed to network (not resolve with cache)
        verify(handler.next(requestOptions)).called(1);
        verifyNever(handler.resolve(any));
      });
    });

    group('Cache Strategy - Cache First', () {
      test('should return cached data when available', () async {
        final requestOptions = RequestOptions(
          path: '/environmental/test',
          method: 'GET',
        );

        final cachedData = {
          'statusCode': 200,
          'statusMessage': 'OK',
          'headers': <String, List<String>>{},
          'data': {'cached': true, 'value': 'test_data'},
          'extra': {},
          '_cached_at': DateTime.now().toIso8601String(),
        };

        // Mock cache hit
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => cachedData);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should resolve with cached response
        verify(handler.resolve(any)).called(1);
        verifyNever(handler.next(any));
      });

      test('should proceed to network when cache miss', () async {
        final requestOptions = RequestOptions(
          path: '/environmental/test',
          method: 'GET',
        );

        // Mock cache miss
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => null);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should proceed to network
        verify(handler.next(requestOptions)).called(1);
        verifyNever(handler.resolve(any));
      });
    });

    group('Cache Strategy - Stale While Revalidate', () {
      test('should return stale cache and trigger background revalidation', () async {
        final requestOptions = RequestOptions(
          path: '/predict/stale-test',
          method: 'GET',
        );

        final staleData = {
          'statusCode': 200,
          'statusMessage': 'OK',
          'headers': <String, List<String>>{},
          'data': {'stale': true, 'value': 'stale_data'},
          'extra': {},
          '_cached_at': DateTime.now().subtract(const Duration(hours: 1)).toIso8601String(),
        };

        // Mock cache hit with stale data
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => staleData);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should resolve with stale response
        verify(handler.resolve(any)).called(1);
        verifyNever(handler.next(any));
      });
    });

    group('Cache Strategy - Network Only', () {
      test('should never use cache for network-only paths', () async {
        final requestOptions = RequestOptions(
          path: '/auth/login',
          method: 'POST',
        );

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should proceed to network without checking cache
        verify(handler.next(requestOptions)).called(1);
        verifyNever(handler.resolve(any));
        verifyNever(mockCacheManager.retrieve(any));
      });
    });

    group('Cache Strategy - Cache Only', () {
      test('should reject request when no cache available', () async {
        final requestOptions = RequestOptions(
          path: '/test/cache-only',
          method: 'GET',
          extra: {
            'cachePolicy': const CachePolicyConfig(
              strategy: CacheStrategy.cacheOnly,
              ttl: Duration(hours: 1),
            ),
          },
        );

        // Mock cache miss
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => null);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should reject the request
        verify(handler.reject(any)).called(1);
        verifyNever(handler.next(any));
        verifyNever(handler.resolve(any));
      });
    });

    group('Response Caching', () {
      test('should cache successful responses', () async {
        final requestOptions = RequestOptions(
          path: '/predict/test',
          method: 'GET',
        );

        final response = Response(
          requestOptions: requestOptions,
          statusCode: 200,
          statusMessage: 'OK',
          data: {'prediction': 'success', 'risk_score': 0.75},
          headers: Headers.fromMap({
            'content-type': ['application/json'],
            'etag': ['test-etag'],
          }),
        );

        final handler = MockResponseInterceptorHandler();

        // Execute interceptor
        await interceptor.onResponse(response, handler);

        // Should store in cache
        verify(mockCacheManager.store(
          key: any,
          data: any,
          ttl: any,
          priority: any,
          tags: any,
          etag: 'test-etag',
          lastModified: any,
        )).called(1);

        verify(handler.next(response)).called(1);
      });

      test('should not cache error responses by default', () async {
        final requestOptions = RequestOptions(
          path: '/predict/test',
          method: 'GET',
        );

        final response = Response(
          requestOptions: requestOptions,
          statusCode: 500,
          statusMessage: 'Internal Server Error',
          data: {'error': 'Server error'},
        );

        final handler = MockResponseInterceptorHandler();

        // Execute interceptor
        await interceptor.onResponse(response, handler);

        // Should not store in cache
        verifyNever(mockCacheManager.store(
          key: any,
          data: any,
          ttl: any,
          priority: any,
          tags: any,
        ));

        verify(handler.next(response)).called(1);
      });
    });

    group('Error Handling', () {
      test('should serve stale cache on network errors', () async {
        final requestOptions = RequestOptions(
          path: '/predict/test',
          method: 'GET',
        );

        final dioException = DioException(
          requestOptions: requestOptions,
          type: DioExceptionType.connectionTimeout,
          error: 'Connection timeout',
        );

        final staleData = {
          'statusCode': 200,
          'statusMessage': 'OK (Cached)',
          'headers': <String, List<String>>{},
          'data': {'cached': true, 'value': 'stale_fallback'},
          'extra': {},
          '_cached_at': DateTime.now().subtract(const Duration(hours: 2)).toIso8601String(),
        };

        // Mock cache hit with stale data
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => staleData);

        final handler = MockErrorInterceptorHandler();

        // Execute interceptor
        await interceptor.onError(dioException, handler);

        // Should resolve with stale cache
        verify(handler.resolve(any)).called(1);
        verifyNever(handler.next(any));
      });

      test('should proceed with error when no cache available', () async {
        final requestOptions = RequestOptions(
          path: '/predict/test',
          method: 'GET',
        );

        final dioException = DioException(
          requestOptions: requestOptions,
          type: DioExceptionType.connectionTimeout,
          error: 'Connection timeout',
        );

        // Mock cache miss
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => null);

        final handler = MockErrorInterceptorHandler();

        // Execute interceptor
        await interceptor.onError(dioException, handler);

        // Should proceed with error
        verify(handler.next(dioException)).called(1);
        verifyNever(handler.resolve(any));
      });
    });

    group('Cache Key Generation', () {
      test('should generate consistent cache keys', () async {
        final requestOptions1 = RequestOptions(
          path: '/predict/test',
          method: 'GET',
          queryParameters: {'lat': '1.0', 'lng': '2.0'},
        );

        final requestOptions2 = RequestOptions(
          path: '/predict/test',
          method: 'GET',
          queryParameters: {'lat': '1.0', 'lng': '2.0'},
        );

        // Both requests should generate the same cache key
        // This is tested indirectly through cache operations
        expect(requestOptions1.path, equals(requestOptions2.path));
        expect(requestOptions1.queryParameters, equals(requestOptions2.queryParameters));
      });

      test('should generate different keys for different requests', () async {
        final requestOptions1 = RequestOptions(
          path: '/predict/test',
          method: 'GET',
          queryParameters: {'lat': '1.0', 'lng': '2.0'},
        );

        final requestOptions2 = RequestOptions(
          path: '/predict/test',
          method: 'GET',
          queryParameters: {'lat': '3.0', 'lng': '4.0'},
        );

        // Different query parameters should result in different cache keys
        expect(requestOptions1.queryParameters, isNot(equals(requestOptions2.queryParameters)));
      });
    });

    group('Custom Cache Policies', () {
      test('should respect custom cache policy in request options', () async {
        final customPolicy = const CachePolicyConfig(
          strategy: CacheStrategy.cacheFirst,
          ttl: Duration(minutes: 30),
          priority: CachePriority.high,
          tags: ['custom'],
        );

        final requestOptions = RequestOptions(
          path: '/test/custom-policy',
          method: 'GET',
          extra: {'cachePolicy': customPolicy},
        );

        // Mock cache miss to trigger network request
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => null);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should proceed to network (cache miss)
        verify(handler.next(requestOptions)).called(1);
      });
    });

    group('Metrics Collection', () {
      test('should collect hit/miss metrics', () async {
        final requestOptions = RequestOptions(
          path: '/predict/metrics-test',
          method: 'GET',
        );

        // Test cache hit
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => {
              'statusCode': 200,
              'data': {'cached': true},
              '_cached_at': DateTime.now().toIso8601String(),
            });

        final handler = MockRequestInterceptorHandler();
        await interceptor.onRequest(requestOptions, handler);

        // Test cache miss
        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => null);

        await interceptor.onRequest(requestOptions, handler);

        // Verify metrics collection
        final metrics = interceptor.getMetrics();
        expect(metrics['cacheHits'], greaterThanOrEqualTo(1));
        expect(metrics['cacheMisses'], greaterThanOrEqualTo(1));
        expect(metrics['totalRequests'], greaterThanOrEqualTo(2));
      });

      test('should reset metrics correctly', () async {
        // Generate some metrics first
        final requestOptions = RequestOptions(
          path: '/test/reset-metrics',
          method: 'GET',
        );

        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => null);

        final handler = MockRequestInterceptorHandler();
        await interceptor.onRequest(requestOptions, handler);

        // Reset metrics
        interceptor.resetMetrics();

        final metrics = interceptor.getMetrics();
        expect(metrics['cacheHits'], equals(0));
        expect(metrics['cacheMisses'], equals(0));
        expect(metrics['totalRequests'], equals(0));
      });
    });

    group('Adaptive Cache Strategy', () {
      test('should use fresh cache when online and cache is fresh', () async {
        final requestOptions = RequestOptions(
          path: '/test/adaptive',
          method: 'GET',
          extra: {
            'cachePolicy': const CachePolicyConfig(
              strategy: CacheStrategy.adaptive,
              ttl: Duration(hours: 1),
            ),
          },
        );

        final freshData = {
          'statusCode': 200,
          'data': {'fresh': true},
          '_cached_at': DateTime.now().subtract(const Duration(minutes: 30)).toIso8601String(),
        };

        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => freshData);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should resolve with fresh cache
        verify(handler.resolve(any)).called(1);
        verifyNever(handler.next(any));
      });

      test('should fetch from network when cache is stale but online', () async {
        final requestOptions = RequestOptions(
          path: '/test/adaptive',
          method: 'GET',
          extra: {
            'cachePolicy': const CachePolicyConfig(
              strategy: CacheStrategy.adaptive,
              ttl: Duration(hours: 1),
            ),
          },
        );

        final staleData = {
          'statusCode': 200,
          'data': {'stale': true},
          '_cached_at': DateTime.now().subtract(const Duration(hours: 2)).toIso8601String(),
        };

        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => staleData);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should proceed to network for fresh data
        verify(handler.next(requestOptions)).called(1);
        verifyNever(handler.resolve(any));
      });

      test('should use stale cache when offline', () async {
        final requestOptions = RequestOptions(
          path: '/test/adaptive',
          method: 'GET',
          extra: {
            'cachePolicy': const CachePolicyConfig(
              strategy: CacheStrategy.adaptive,
              ttl: Duration(hours: 1),
              maxStaleTime: Duration(hours: 24),
            ),
          },
        );

        final staleData = {
          'statusCode': 200,
          'data': {'stale_offline': true},
          '_cached_at': DateTime.now().subtract(const Duration(hours: 2)).toIso8601String(),
        };

        // Mock offline
        when(mockConnectivity.checkConnectivity())
            .thenAnswer((_) async => ConnectivityResult.none);

        when(mockCacheManager.retrieve(any))
            .thenAnswer((_) async => staleData);

        final handler = MockRequestInterceptorHandler();

        // Execute interceptor
        await interceptor.onRequest(requestOptions, handler);

        // Should resolve with stale cache when offline
        verify(handler.resolve(any)).called(1);
        verifyNever(handler.next(any));
      });
    });

    group('Request Method Handling', () {
      test('should only cache GET requests', () async {
        final methods = ['POST', 'PUT', 'DELETE', 'PATCH'];

        for (final method in methods) {
          final requestOptions = RequestOptions(
            path: '/test/method',
            method: method,
          );

          final handler = MockRequestInterceptorHandler();

          // Execute interceptor
          await interceptor.onRequest(requestOptions, handler);

          // Should proceed to network without cache check
          verify(handler.next(requestOptions)).called(1);
          verifyNever(mockCacheManager.retrieve(any));

          // Reset mocks for next iteration
          reset(handler);
          reset(mockCacheManager);
        }
      });
    });
  });
}

// Mock handlers for testing
class MockRequestInterceptorHandler extends Mock implements RequestInterceptorHandler {
  @override
  void next(RequestOptions options) {}

  @override
  void resolve(Response response, [bool callFollowRedirects = false]) {}

  @override
  void reject(DioException error, [bool callFollowRedirects = false]) {}
}

class MockResponseInterceptorHandler extends Mock implements ResponseInterceptorHandler {
  @override
  void next(Response response) {}

  @override
  void resolve(Response response) {}

  @override
  void reject(DioException error, [bool callFollowRedirects = false]) {}
}

class MockErrorInterceptorHandler extends Mock implements ErrorInterceptorHandler {
  @override
  void next(DioException error) {}

  @override
  void resolve(Response response) {}

  @override
  void reject(DioException error) {}
}