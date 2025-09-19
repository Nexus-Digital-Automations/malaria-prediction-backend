/// Comprehensive tests for Offline Request Queue
///
/// Tests offline request queuing, priority handling, retry mechanisms,
/// sync capabilities, and persistence across app sessions.
///
/// Author: Claude AI Agent - Caching Specialist
/// Created: 2025-09-19
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

import 'package:malaria_frontend/core/offline/offline_request_queue.dart';

// Generate mocks
@GenerateMocks([Dio, Logger, Connectivity])
import 'offline_request_queue_test.mocks.dart';

void main() {
  group('OfflineRequestQueue', () {
    late OfflineRequestQueue requestQueue;
    late MockDio mockDio;
    late MockLogger mockLogger;
    late MockConnectivity mockConnectivity;

    setUp(() async {
      mockDio = MockDio();
      mockLogger = MockLogger();
      mockConnectivity = MockConnectivity();

      // Mock connectivity to return offline by default for testing
      when(mockConnectivity.checkConnectivity())
          .thenAnswer((_) async => ConnectivityResult.none);

      requestQueue = OfflineRequestQueue(
        dio: mockDio,
        connectivity: mockConnectivity,
        logger: mockLogger,
        maxQueueSize: 100,
        syncBatchSize: 5,
        autoSyncEnabled: false, // Disable for controlled testing
        syncOnConnectivity: false,
      );

      await requestQueue.initialize();
    });

    tearDown(() async {
      await requestQueue.dispose();
    });

    group('Request Enqueuing', () {
      test('should enqueue request successfully', () async {
        final requestId = await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/test',
          priority: OfflineRequestPriority.normal,
          tags: ['prediction'],
        );

        expect(requestId, isNotNull);
        expect(requestId, isNotEmpty);

        final queueSize = await requestQueue.getQueueSize();
        expect(queueSize, equals(1));
      });

      test('should enqueue requests with different priorities', () async {
        final priorities = [
          OfflineRequestPriority.low,
          OfflineRequestPriority.normal,
          OfflineRequestPriority.high,
          OfflineRequestPriority.critical,
          OfflineRequestPriority.emergency,
        ];

        final requestIds = <String>[];

        for (final priority in priorities) {
          final requestId = await requestQueue.enqueue(
            method: 'POST',
            url: '/predict/batch',
            data: {'priority': priority.name},
            priority: priority,
          );
          requestIds.add(requestId);
        }

        expect(requestIds.length, equals(5));

        final queuedRequests = await requestQueue.getQueuedRequests();
        expect(queuedRequests.length, equals(5));

        // Verify sorting by priority (highest first)
        for (int i = 0; i < queuedRequests.length - 1; i++) {
          expect(
            queuedRequests[i].priority.value,
            greaterThanOrEqualTo(queuedRequests[i + 1].priority.value),
          );
        }
      });

      test('should include request headers and data', () async {
        final headers = {'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'};
        final data = {'location': {'lat': 1.0, 'lng': 2.0}, 'model': 'lstm'};
        final queryParams = {'format': 'json', 'version': 'v1'};

        final requestId = await requestQueue.enqueue(
          method: 'POST',
          url: '/predict/location',
          headers: headers,
          data: data,
          queryParameters: queryParams,
          priority: OfflineRequestPriority.high,
        );

        final queuedRequests = await requestQueue.getQueuedRequests();
        final request = queuedRequests.firstWhere((r) => r.id == requestId);

        expect(request.headers, equals(headers));
        expect(request.data, equals(data));
        expect(request.queryParameters, equals(queryParams));
      });

      test('should handle request expiration', () async {
        final requestId = await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/expired',
          priority: OfflineRequestPriority.normal,
          expiresIn: const Duration(milliseconds: 10),
        );

        // Wait for expiration
        await Future.delayed(const Duration(milliseconds: 20));

        final queuedRequests = await requestQueue.getQueuedRequests();
        final expiredRequests = await requestQueue.getQueuedRequests(includeExpired: true);

        // Should not include expired requests by default
        expect(queuedRequests.where((r) => r.id == requestId), isEmpty);

        // Should include when explicitly requested
        expect(expiredRequests.where((r) => r.id == requestId), isNotEmpty);
      });
    });

    group('Request Dependencies', () {
      test('should handle request dependencies correctly', () async {
        final parentRequestId = await requestQueue.enqueue(
          method: 'POST',
          url: '/auth/login',
          data: {'username': 'test', 'password': 'test'},
          priority: OfflineRequestPriority.high,
        );

        final childRequestId = await requestQueue.enqueue(
          method: 'GET',
          url: '/user/profile',
          dependencies: [parentRequestId],
          priority: OfflineRequestPriority.normal,
        );

        final queuedRequests = await requestQueue.getQueuedRequests();
        final childRequest = queuedRequests.firstWhere((r) => r.id == childRequestId);

        expect(childRequest.dependencies, contains(parentRequestId));
      });
    });

    group('Retry Mechanisms', () {
      test('should handle different retry strategies', () async {
        final strategies = [
          RetryStrategy.none,
          RetryStrategy.immediate,
          RetryStrategy.linear,
          RetryStrategy.exponential,
        ];

        for (final strategy in strategies) {
          await requestQueue.enqueue(
            method: 'GET',
            url: '/predict/retry-test',
            retryStrategy: strategy,
            maxRetries: 3,
            priority: OfflineRequestPriority.normal,
          );
        }

        final queuedRequests = await requestQueue.getQueuedRequests();
        expect(queuedRequests.length, equals(4));

        for (int i = 0; i < strategies.length; i++) {
          expect(queuedRequests[i].retryStrategy, equals(strategies[i]));
          expect(queuedRequests[i].maxRetries, equals(3));
        }
      });
    });

    group('Queue Management', () {
      test('should filter requests by priority', () async {
        // Add requests with different priorities
        await requestQueue.enqueue(
          method: 'GET',
          url: '/test/low',
          priority: OfflineRequestPriority.low,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/test/high',
          priority: OfflineRequestPriority.high,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/test/critical',
          priority: OfflineRequestPriority.critical,
        );

        // Filter by minimum priority
        final highPriorityRequests = await requestQueue.getQueuedRequests(
          minPriority: OfflineRequestPriority.high,
        );

        expect(highPriorityRequests.length, equals(2));
        for (final request in highPriorityRequests) {
          expect(request.priority.value, greaterThanOrEqualTo(OfflineRequestPriority.high.value));
        }
      });

      test('should filter requests by tags', () async {
        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/location1',
          tags: ['prediction', 'location'],
          priority: OfflineRequestPriority.normal,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/environmental/data',
          tags: ['environmental', 'data'],
          priority: OfflineRequestPriority.normal,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/location2',
          tags: ['prediction', 'location'],
          priority: OfflineRequestPriority.normal,
        );

        final predictionRequests = await requestQueue.getQueuedRequests(
          tags: ['prediction'],
        );

        expect(predictionRequests.length, equals(2));
        for (final request in predictionRequests) {
          expect(request.tags, contains('prediction'));
        }
      });

      test('should remove specific requests', () async {
        final requestId = await requestQueue.enqueue(
          method: 'GET',
          url: '/test/remove',
          priority: OfflineRequestPriority.normal,
        );

        expect(await requestQueue.getQueueSize(), equals(1));

        final removed = await requestQueue.removeRequest(requestId);
        expect(removed, isTrue);
        expect(await requestQueue.getQueueSize(), equals(0));
      });

      test('should clear queue by criteria', () async {
        // Add requests with different priorities
        await requestQueue.enqueue(
          method: 'GET',
          url: '/test/low1',
          priority: OfflineRequestPriority.low,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/test/low2',
          priority: OfflineRequestPriority.low,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/test/high',
          priority: OfflineRequestPriority.high,
        );

        expect(await requestQueue.getQueueSize(), equals(3));

        // Clear only low priority requests
        await requestQueue.clearQueue(maxPriority: OfflineRequestPriority.low);

        final remainingRequests = await requestQueue.getQueuedRequests();
        expect(remainingRequests.length, equals(1));
        expect(remainingRequests.first.priority, equals(OfflineRequestPriority.high));
      });
    });

    group('Synchronization', () {
      test('should sync requests when online', () async {
        // Mock successful responses
        when(mockDio.request(
          any,
          options: anyNamed('options'),
          queryParameters: anyNamed('queryParameters'),
          data: anyNamed('data'),
        ),).thenAnswer((_) async => Response(
          requestOptions: RequestOptions(path: '/test'),
          statusCode: 200,
          data: {'success': true},
        ),);

        // Mock online connectivity
        when(mockConnectivity.checkConnectivity())
            .thenAnswer((_) async => ConnectivityResult.wifi);

        // Add test requests
        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/sync1',
          priority: OfflineRequestPriority.normal,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/sync2',
          priority: OfflineRequestPriority.high,
        );

        final sizeBefore = await requestQueue.getQueueSize();
        expect(sizeBefore, equals(2));

        // Perform sync
        final results = await requestQueue.sync();

        expect(results.length, equals(2));
        for (final result in results) {
          expect(result.success, isTrue);
        }

        // Queue should be empty after successful sync
        final sizeAfter = await requestQueue.getQueueSize();
        expect(sizeAfter, equals(0));
      });

      test('should handle sync failures with retry', () async {
        // Mock failed response
        when(mockDio.request(
          any,
          options: anyNamed('options'),
          queryParameters: anyNamed('queryParameters'),
          data: anyNamed('data'),
        ),).thenThrow(DioException(
          requestOptions: RequestOptions(path: '/test'),
          type: DioExceptionType.connectionTimeout,
        ),);

        // Mock online connectivity
        when(mockConnectivity.checkConnectivity())
            .thenAnswer((_) async => ConnectivityResult.wifi);

        // Add test request with retry
        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/fail',
          priority: OfflineRequestPriority.normal,
          retryStrategy: RetryStrategy.exponential,
          maxRetries: 2,
        );

        // Perform sync
        final results = await requestQueue.sync();

        expect(results.length, equals(1));
        expect(results.first.success, isFalse);
        expect(results.first.retryScheduled, isTrue);

        // Request should still be in queue for retry
        final queueSize = await requestQueue.getQueueSize();
        expect(queueSize, equals(1));

        final queuedRequests = await requestQueue.getQueuedRequests();
        expect(queuedRequests.first.retryCount, equals(1));
      });

      test('should remove requests after max retries exceeded', () async {
        // Mock failed response
        when(mockDio.request(
          any,
          options: anyNamed('options'),
          queryParameters: anyNamed('queryParameters'),
          data: anyNamed('data'),
        ),).thenThrow(DioException(
          requestOptions: RequestOptions(path: '/test'),
          type: DioExceptionType.badResponse,
          response: Response(
            requestOptions: RequestOptions(path: '/test'),
            statusCode: 404,
          ),
        ),);

        // Mock online connectivity
        when(mockConnectivity.checkConnectivity())
            .thenAnswer((_) async => ConnectivityResult.wifi);

        // Add test request that will fail
        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/maxretries',
          priority: OfflineRequestPriority.normal,
          retryStrategy: RetryStrategy.immediate,
          maxRetries: 1,
        );

        // First sync attempt
        await requestQueue.sync();

        // Should still be in queue after first failure
        expect(await requestQueue.getQueueSize(), equals(1));

        // Second sync attempt (should exceed max retries)
        await requestQueue.sync();

        // Should be removed after exceeding max retries
        expect(await requestQueue.getQueueSize(), equals(0));
      });
    });

    group('Queue Statistics', () {
      test('should provide accurate statistics', () async {
        // Add requests with different priorities and methods
        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/stats1',
          priority: OfflineRequestPriority.low,
        );

        await requestQueue.enqueue(
          method: 'POST',
          url: '/predict/stats2',
          priority: OfflineRequestPriority.high,
        );

        await requestQueue.enqueue(
          method: 'GET',
          url: '/predict/stats3',
          priority: OfflineRequestPriority.critical,
          expiresIn: const Duration(milliseconds: 10),
        );

        // Wait for one to expire
        await Future.delayed(const Duration(milliseconds: 20));

        final stats = await requestQueue.getStatistics();

        expect(stats['totalRequests'], equals(3));
        expect(stats['validRequests'], equals(2));
        expect(stats['expiredRequests'], equals(1));
        expect(stats['priorityDistribution'], isNotEmpty);
        expect(stats['methodDistribution'], isNotEmpty);
        expect(stats['queueSizeLimit'], equals(100));
      });
    });

    group('Conflict Resolution', () {
      test('should handle conflict resolution strategies', () async {
        final strategies = [
          ConflictResolution.overwrite,
          ConflictResolution.merge,
          ConflictResolution.skip,
          ConflictResolution.latest,
        ];

        for (final strategy in strategies) {
          await requestQueue.enqueue(
            method: 'PUT',
            url: '/user/profile',
            data: {'strategy': strategy.name},
            conflictResolution: strategy,
            priority: OfflineRequestPriority.normal,
          );
        }

        final queuedRequests = await requestQueue.getQueuedRequests();
        expect(queuedRequests.length, equals(4));

        for (int i = 0; i < strategies.length; i++) {
          expect(queuedRequests[i].conflictResolution, equals(strategies[i]));
        }
      });
    });

    group('Performance Tests', () {
      test('should handle large number of requests efficiently', () async {
        const numberOfRequests = 100;
        final stopwatch = Stopwatch()..start();

        final requestIds = <String>[];

        // Enqueue many requests
        for (int i = 0; i < numberOfRequests; i++) {
          final requestId = await requestQueue.enqueue(
            method: 'GET',
            url: '/predict/performance_$i',
            data: {'index': i},
            priority: i.isEven ? OfflineRequestPriority.normal : OfflineRequestPriority.high,
          );
          requestIds.add(requestId);
        }

        stopwatch.stop();

        expect(requestIds.length, equals(numberOfRequests));
        expect(await requestQueue.getQueueSize(), equals(numberOfRequests));

        // Should complete within reasonable time
        expect(stopwatch.elapsedMilliseconds, lessThan(5000)); // 5 seconds max
      });

      test('should handle concurrent enqueue operations', () async {
        const concurrentRequests = 50;
        final futures = <Future<String>>[];

        // Create concurrent enqueue operations
        for (int i = 0; i < concurrentRequests; i++) {
          futures.add(requestQueue.enqueue(
            method: 'POST',
            url: '/predict/concurrent_$i',
            data: {'index': i},
            priority: OfflineRequestPriority.normal,
          ),);
        }

        // Wait for all operations to complete
        final requestIds = await Future.wait(futures);

        expect(requestIds.length, equals(concurrentRequests));
        expect(await requestQueue.getQueueSize(), equals(concurrentRequests));

        // All request IDs should be unique
        final uniqueIds = requestIds.toSet();
        expect(uniqueIds.length, equals(concurrentRequests));
      });
    });

    group('Queue Size Limits', () {
      test('should respect maximum queue size', () async {
        // Create a queue with small limit for testing
        final smallQueue = OfflineRequestQueue(
          dio: mockDio,
          connectivity: mockConnectivity,
          logger: mockLogger,
          maxQueueSize: 5,
          autoSyncEnabled: false,
        );

        await smallQueue.initialize();

        try {
          // Add more requests than the limit
          for (int i = 0; i < 10; i++) {
            await smallQueue.enqueue(
              method: 'GET',
              url: '/test/limit_$i',
              priority: i > 5 ? OfflineRequestPriority.high : OfflineRequestPriority.low,
            );
          }

          final queueSize = await smallQueue.getQueueSize();

          // Should not exceed the limit
          expect(queueSize, lessThanOrEqualTo(5));
        } finally {
          await smallQueue.dispose();
        }
      });
    });

    group('Request Metadata', () {
      test('should store and retrieve request metadata', () async {
        final metadata = {
          'userId': 'test_user_123',
          'sessionId': 'session_456',
          'version': '1.0.0',
          'features': ['prediction', 'environmental'],
        };

        final requestId = await requestQueue.enqueue(
          method: 'POST',
          url: '/predict/metadata',
          data: {'test': 'data'},
          metadata: metadata,
          priority: OfflineRequestPriority.normal,
        );

        final queuedRequests = await requestQueue.getQueuedRequests();
        final request = queuedRequests.firstWhere((r) => r.id == requestId);

        expect(request.metadata, equals(metadata));
        expect(request.metadata['userId'], equals('test_user_123'));
        expect(request.metadata['features'], equals(['prediction', 'environmental']));
      });
    });
  });
}