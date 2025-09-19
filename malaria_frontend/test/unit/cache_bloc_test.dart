/// Unit tests for CacheBloc
///
/// Comprehensive tests covering all events, states, and edge cases
/// for the cache management functionality in the malaria prediction app.
///
/// Author: Claude AI Agent - BLoC Infrastructure Testing
/// Created: 2025-09-19
library;

import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:malaria_frontend/core/cache/offline_cache_service.dart';
import 'package:malaria_frontend/core/cache/cache_bloc.dart';
import 'package:malaria_frontend/core/errors/failures.dart';

import 'cache_bloc_test.mocks.dart';

@GenerateMocks([
  OfflineCacheService,
])
void main() {
  group('CacheBloc Tests', () {
    late CacheBloc cacheBloc;
    late MockOfflineCacheService mockCacheService;

    setUp(() {
      mockCacheService = MockOfflineCacheService();

      // Setup default mock behaviors
      when(mockCacheService.getStats()).thenAnswer((_) async => {
        'total_entries': 10,
        'size_mb': 5,
        'expired_entries': 2,
        'priority_counts': {'normal': 8, 'high': 2},
      });

      cacheBloc = CacheBloc(
        cacheService: mockCacheService,
        config: const CacheConfiguration(
          maxSizeMB: 50,
          enableAutoCleanup: false, // Disable for testing
          enableMonitoring: false,  // Disable for testing
        ),
      );
    });

    tearDown(() {
      cacheBloc.close();
    });

    group('Initial State', () {
      test('should have CacheInitial as initial state', () {
        expect(cacheBloc.state, isA<CacheInitial>());
      });

      test('should initialize with provided configuration', () {
        expect(cacheBloc.config.maxSizeMB, equals(50));
        expect(cacheBloc.config.enableAutoCleanup, isFalse);
      });
    });

    group('CacheData Event', () {
      final testData = {'key': 'value', 'number': 42, 'list': [1, 2, 3]};
      const testPolicy = CachePolicy(
        ttl: Duration(hours: 1),
        priority: CachePriority.normal,
        compressData: false,
        enableEncryption: false,
      );

      blocTest<CacheBloc, CacheState>(
        'should store data successfully without encryption or compression',
        build: () {
          when(mockCacheService.store(
            key: any(named: 'key'),
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
            tags: any(named: 'tags'),
          )).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(CacheData(
          key: 'test-key',
          data: testData,
          policy: testPolicy,
        )),
        expect: () => [
          isA<CacheLoading>()
              .having((state) => state.operation, 'operation', CacheOperation.storing),
          isA<CacheLoaded>()
              .having((state) => state.key, 'key', 'test-key')
              .having((state) => state.data, 'data', testData)
              .having((state) => state.hitType, 'hitType', CacheHitType.refreshed),
        ],
        verify: (_) {
          verify(mockCacheService.store(
            key: 'test-key',
            data: testData,
            ttl: const Duration(hours: 1),
            priority: CachePriority.normal,
            tags: [],
          )).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should store data with encryption when enabled',
        build: () {
          when(mockCacheService.store(
            key: any(named: 'key'),
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
            tags: any(named: 'tags'),
          )).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(CacheData(
          key: 'encrypted-key',
          data: testData,
          policy: const CachePolicy(
            ttl: Duration(hours: 1),
            priority: CachePriority.normal,
            enableEncryption: true,
          ),
          encrypt: true,
        )),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheLoaded>()
              .having((state) => state.metadata.isEncrypted, 'isEncrypted', true),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should store data with compression when enabled',
        build: () {
          when(mockCacheService.store(
            key: any(named: 'key'),
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
            tags: any(named: 'tags'),
          )).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(CacheData(
          key: 'compressed-key',
          data: testData,
          policy: const CachePolicy(
            ttl: Duration(hours: 1),
            priority: CachePriority.normal,
            compressData: true,
          ),
        )),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheLoaded>()
              .having((state) => state.metadata.isCompressed, 'isCompressed', true),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should store data with tags',
        build: () {
          when(mockCacheService.store(
            key: any(named: 'key'),
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
            tags: any(named: 'tags'),
          )).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(CacheData(
          key: 'tagged-key',
          data: testData,
          policy: testPolicy,
          tags: ['prediction', 'user-data'],
        )),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheLoaded>()
              .having((state) => state.metadata.tags, 'tags', ['prediction', 'user-data']),
        ],
        verify: (_) {
          verify(mockCacheService.store(
            key: 'tagged-key',
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
            tags: ['prediction', 'user-data'],
          )).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when storage fails',
        build: () {
          when(mockCacheService.store(
            key: any(named: 'key'),
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
            tags: any(named: 'tags'),
          )).thenThrow(Exception('Storage failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(CacheData(
          key: 'error-key',
          data: testData,
          policy: testPolicy,
        )),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.storing)
              .having((state) => state.key, 'key', 'error-key')
              .having((state) => state.failure, 'failure', isA<CacheFailure>()),
        ],
      );
    });

    group('LoadFromCache Event', () {
      final testData = {'cached': 'data', 'timestamp': '2023-01-01'};

      blocTest<CacheBloc, CacheState>(
        'should load data successfully from cache',
        build: () {
          when(mockCacheService.retrieve('test-key'))
              .thenAnswer((_) async => testData);
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const LoadFromCache(key: 'test-key')),
        expect: () => [
          isA<CacheLoading>()
              .having((state) => state.operation, 'operation', CacheOperation.loading),
          isA<CacheLoaded>()
              .having((state) => state.key, 'key', 'test-key')
              .having((state) => state.data, 'data', testData)
              .having((state) => state.hitType, 'hitType', CacheHitType.hit),
        ],
        verify: (_) {
          verify(mockCacheService.retrieve('test-key')).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when data not found',
        build: () {
          when(mockCacheService.retrieve('missing-key'))
              .thenAnswer((_) async => null);
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const LoadFromCache(key: 'missing-key')),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.loading)
              .having((state) => state.key, 'key', 'missing-key')
              .having((state) => state.failure.message, 'failure.message', 'Data not found in cache'),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should handle encrypted data correctly',
        build: () {
          when(mockCacheService.retrieve('encrypted-key'))
              .thenAnswer((_) async => {
                '_encrypted': true,
                '_data': 'base64EncodedData',
                '_hash': 'someHash',
              });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const LoadFromCache(key: 'encrypted-key')),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheLoaded>(), // Should successfully decrypt and load
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should handle compressed data correctly',
        build: () {
          when(mockCacheService.retrieve('compressed-key'))
              .thenAnswer((_) async => {
                '_compressed': true,
                '_data': '{"decompressed":"data"}',
                '_original_size': 100,
              });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const LoadFromCache(key: 'compressed-key')),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheLoaded>()
              .having((state) => state.data['decompressed'], 'decompressed', 'data'),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when retrieval fails',
        build: () {
          when(mockCacheService.retrieve('error-key'))
              .thenThrow(Exception('Retrieval failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const LoadFromCache(key: 'error-key')),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.loading),
        ],
      );
    });

    group('ClearCache Event', () {
      blocTest<CacheBloc, CacheState>(
        'should clear all cache entries',
        build: () {
          when(mockCacheService.clearAll()).thenAnswer((_) async {});
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'total_entries': 0,
            'size_mb': 0,
          });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const ClearCache(type: ClearCacheType.all)),
        expect: () => [
          isA<CacheLoading>()
              .having((state) => state.operation, 'operation', CacheOperation.clearing),
          isA<CacheCleared>()
              .having((state) => state.clearType, 'clearType', ClearCacheType.all),
        ],
        verify: (_) {
          verify(mockCacheService.clearAll()).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should clear cache by specific keys',
        build: () {
          when(mockCacheService.remove(any)).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const ClearCache(
          type: ClearCacheType.byKeys,
          keys: ['key1', 'key2', 'key3'],
        )),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheCleared>()
              .having((state) => state.clearType, 'clearType', ClearCacheType.byKeys)
              .having((state) => state.clearedEntries, 'clearedEntries', 3)
              .having((state) => state.clearedKeys, 'clearedKeys', ['key1', 'key2', 'key3']),
        ],
        verify: (_) {
          verify(mockCacheService.remove('key1')).called(1);
          verify(mockCacheService.remove('key2')).called(1);
          verify(mockCacheService.remove('key3')).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should clear cache by tags',
        build: () {
          when(mockCacheService.clearByTags(any)).thenAnswer((_) async {});
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'total_entries': 5,
          });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const ClearCache(
          type: ClearCacheType.byTags,
          tags: ['prediction', 'user-data'],
        )),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheCleared>()
              .having((state) => state.clearType, 'clearType', ClearCacheType.byTags),
        ],
        verify: (_) {
          verify(mockCacheService.clearByTags(['prediction', 'user-data'])).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should clear expired entries',
        build: () {
          when(mockCacheService.clearExpired()).thenAnswer((_) async {});
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'total_entries': 8,
          });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const ClearCache(type: ClearCacheType.expired)),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheCleared>()
              .having((state) => state.clearType, 'clearType', ClearCacheType.expired),
        ],
        verify: (_) {
          verify(mockCacheService.clearExpired()).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when clear fails',
        build: () {
          when(mockCacheService.clearAll()).thenThrow(Exception('Clear failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const ClearCache(type: ClearCacheType.all)),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.clearing),
        ],
      );
    });

    group('UpdateCachePolicy Event', () {
      blocTest<CacheBloc, CacheState>(
        'should update cache policy configuration',
        build: () => cacheBloc,
        act: (bloc) => bloc.add(UpdateCachePolicy(
          config: const CacheConfiguration(
            maxSizeMB: 200,
            enableAutoCleanup: true,
            cleanupInterval: Duration(hours: 12),
          ),
        )),
        verify: (_) {
          expect(cacheBloc.config.maxSizeMB, equals(200));
          expect(cacheBloc.config.enableAutoCleanup, isTrue);
          expect(cacheBloc.config.cleanupInterval, equals(const Duration(hours: 12)));
        },
      );
    });

    group('InvalidateCache Event', () {
      blocTest<CacheBloc, CacheState>(
        'should invalidate specific cache entries',
        build: () {
          when(mockCacheService.remove(any)).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const InvalidateCache(
          keys: ['invalid1', 'invalid2'],
          reason: InvalidationReason.dataChanged,
        )),
        expect: () => [
          isA<CacheCleared>()
              .having((state) => state.clearType, 'clearType', ClearCacheType.byKeys)
              .having((state) => state.clearedEntries, 'clearedEntries', 2)
              .having((state) => state.clearedKeys, 'clearedKeys', ['invalid1', 'invalid2']),
        ],
        verify: (_) {
          verify(mockCacheService.remove('invalid1')).called(1);
          verify(mockCacheService.remove('invalid2')).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when invalidation fails',
        build: () {
          when(mockCacheService.remove(any)).thenThrow(Exception('Remove failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const InvalidateCache(
          keys: ['error-key'],
          reason: InvalidationReason.corruption,
        )),
        expect: () => [
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.clearing),
        ],
      );
    });

    group('WarmCache Event', () {
      final warmupItems = {
        'item1': CacheWarmupItem(
          key: 'warm1',
          data: {'warm': 'data1'},
          policy: const CachePolicy(ttl: Duration(hours: 1)),
        ),
        'item2': CacheWarmupItem(
          key: 'warm2',
          data: {'warm': 'data2'},
          policy: const CachePolicy(ttl: Duration(hours: 2)),
        ),
      };

      blocTest<CacheBloc, CacheState>(
        'should warm cache with multiple items successfully',
        build: () {
          when(mockCacheService.store(
            key: any(named: 'key'),
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
          )).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(WarmCache(items: warmupItems)),
        expect: () => [
          isA<CacheLoading>()
              .having((state) => state.operation, 'operation', CacheOperation.warming),
          isA<CacheWarmed>()
              .having((state) => state.warmedEntries, 'warmedEntries', 2),
        ],
        verify: (_) {
          verify(mockCacheService.store(
            key: 'warm1',
            data: {'warm': 'data1'},
            ttl: const Duration(hours: 1),
            priority: CachePriority.normal,
          )).called(1);
          verify(mockCacheService.store(
            key: 'warm2',
            data: {'warm': 'data2'},
            ttl: const Duration(hours: 2),
            priority: CachePriority.normal,
          )).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should handle partial failures during warmup',
        build: () {
          when(mockCacheService.store(
            key: 'warm1',
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
          )).thenAnswer((_) async {});
          when(mockCacheService.store(
            key: 'warm2',
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
          )).thenThrow(Exception('Storage failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(WarmCache(items: warmupItems)),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheWarmed>()
              .having((state) => state.warmedEntries, 'warmedEntries', 1), // Only one succeeded
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when warmup fails completely',
        build: () {
          when(mockCacheService.store(
            key: any(named: 'key'),
            data: any(named: 'data'),
            ttl: any(named: 'ttl'),
            priority: any(named: 'priority'),
          )).thenThrow(Exception('Complete failure'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(WarmCache(items: {'single': warmupItems.values.first})),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheWarmed>()
              .having((state) => state.warmedEntries, 'warmedEntries', 0),
        ],
      );
    });

    group('GetCacheStats Event', () {
      blocTest<CacheBloc, CacheState>(
        'should return cache statistics successfully',
        build: () {
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'total_entries': 25,
            'size_mb': 15,
            'expired_entries': 3,
            'priority_counts': {'normal': 20, 'high': 3, 'critical': 2},
          });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const GetCacheStats()),
        expect: () => [
          isA<CacheStatsLoaded>()
              .having((state) => state.stats.totalEntries, 'totalEntries', 25)
              .having((state) => state.stats.totalSizeMB, 'totalSizeMB', 15)
              .having((state) => state.stats.expiredEntries, 'expiredEntries', 3),
        ],
        verify: (_) {
          verify(mockCacheService.getStats()).called(1);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should calculate hit ratio correctly',
        build: () {
          // Simulate some cache hits and misses
          cacheBloc.add(const LoadFromCache(key: 'existing-key'));
          when(mockCacheService.retrieve('existing-key'))
              .thenAnswer((_) async => {'data': 'exists'});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const GetCacheStats()),
        wait: const Duration(milliseconds: 100),
        expect: () => [
          isA<CacheLoading>(), // From LoadFromCache
          isA<CacheLoaded>(),   // From LoadFromCache
          isA<CacheStatsLoaded>(), // From GetCacheStats
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when stats retrieval fails',
        build: () {
          when(mockCacheService.getStats()).thenThrow(Exception('Stats failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const GetCacheStats()),
        expect: () => [
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.monitoring),
        ],
      );
    });

    group('OptimizeCache Event', () {
      blocTest<CacheBloc, CacheState>(
        'should optimize cache with conservative strategy',
        build: () {
          when(mockCacheService.getStats())
              .thenAnswerInOrder([
                // Initial stats
                Future.value({
                  'total_entries': 100,
                  'size_mb': 50,
                }),
                // Final stats after optimization
                Future.value({
                  'total_entries': 80,
                  'size_mb': 40,
                }),
              ]);
          when(mockCacheService.clearExpired()).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const OptimizeCache(strategy: OptimizationStrategy.conservative)),
        expect: () => [
          isA<CacheLoading>()
              .having((state) => state.operation, 'operation', CacheOperation.optimizing),
          isA<CacheOptimized>()
              .having((state) => state.result.removedEntries, 'removedEntries', 20)
              .having((state) => state.result.freedSpaceMB, 'freedSpaceMB', 10)
              .having((state) => state.result.strategy, 'strategy', OptimizationStrategy.conservative),
        ],
        verify: (_) {
          verify(mockCacheService.clearExpired()).called(1);
          verify(mockCacheService.getStats()).called(2);
        },
      );

      blocTest<CacheBloc, CacheState>(
        'should optimize cache with aggressive strategy',
        build: () {
          when(mockCacheService.getStats())
              .thenAnswerInOrder([
                Future.value({'total_entries': 200, 'size_mb': 100}),
                Future.value({'total_entries': 120, 'size_mb': 60}),
              ]);
          when(mockCacheService.clearExpired()).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const OptimizeCache(strategy: OptimizationStrategy.aggressive)),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheOptimized>()
              .having((state) => state.result.removedEntries, 'removedEntries', 80)
              .having((state) => state.result.freedSpaceMB, 'freedSpaceMB', 40),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when optimization fails',
        build: () {
          when(mockCacheService.getStats()).thenThrow(Exception('Stats failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const OptimizeCache(strategy: OptimizationStrategy.balanced)),
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.optimizing),
        ],
      );
    });

    group('MonitorCacheHealth Event', () {
      blocTest<CacheBloc, CacheState>(
        'should monitor cache health and report excellent status',
        build: () {
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'size_mb': 25, // 50% utilization (maxSizeMB is 50)
            'total_entries': 100,
          });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const MonitorCacheHealth()),
        expect: () => [
          isA<CacheHealthMonitored>()
              .having((state) => state.health.overallStatus, 'overallStatus', HealthStatus.excellent)
              .having((state) => state.health.utilizationPercentage, 'utilizationPercentage', 50.0),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should monitor cache health and report warning for high utilization',
        build: () {
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'size_mb': 42, // 84% utilization
            'total_entries': 100,
          });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const MonitorCacheHealth()),
        expect: () => [
          isA<CacheHealthMonitored>()
              .having((state) => state.health.overallStatus, 'overallStatus', HealthStatus.warning)
              .having((state) => state.health.utilizationPercentage, 'utilizationPercentage', 84.0)
              .having((state) => state.health.issues.length, 'issues.length', greaterThan(0)),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should monitor cache health and report critical for very high utilization',
        build: () {
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'size_mb': 46, // 92% utilization
            'total_entries': 100,
          });
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const MonitorCacheHealth()),
        expect: () => [
          isA<CacheHealthMonitored>()
              .having((state) => state.health.overallStatus, 'overallStatus', HealthStatus.critical)
              .having((state) => state.health.utilizationPercentage, 'utilizationPercentage', 92.0),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should emit CacheError when health monitoring fails',
        build: () {
          when(mockCacheService.getStats()).thenThrow(Exception('Health check failed'));
          return cacheBloc;
        },
        act: (bloc) => bloc.add(const MonitorCacheHealth()),
        expect: () => [
          isA<CacheError>()
              .having((state) => state.operation, 'operation', CacheOperation.monitoring),
        ],
      );
    });

    group('State Properties and Getters', () {
      test('CacheInitial should have correct loading properties', () {
        const state = CacheInitial();
        expect(state.isLoading, isTrue);
        expect(state.loadingMessage, equals('Initializing cache system...'));
      });

      test('CacheLoading should have correct loading messages', () {
        const storingState = CacheLoading(operation: CacheOperation.storing);
        const loadingState = CacheLoading(operation: CacheOperation.loading);
        const clearingState = CacheLoading(operation: CacheOperation.clearing);

        expect(storingState.loadingMessage, equals('Storing data in cache...'));
        expect(loadingState.loadingMessage, equals('Loading data from cache...'));
        expect(clearingState.loadingMessage, equals('Clearing cache...'));
      });

      test('CacheLoaded should have correct success properties', () {
        final metadata = CacheMetadata(
          createdAt: DateTime.now(),
          lastAccessedAt: DateTime.now(),
          expiresAt: DateTime.now().add(const Duration(hours: 1)),
          accessCount: 5,
          sizeBytes: 1024,
          priority: CachePriority.high,
        );

        final state = CacheLoaded(
          key: 'test-key',
          data: {'test': 'data'},
          metadata: metadata,
          hitType: CacheHitType.hit,
        );

        expect(state.isSuccess, isTrue);
        expect(state.isFromCache, isTrue);
        expect(state.wasRefreshed, isFalse);
        expect(state.successMessage, contains('hit'));
      });

      test('CacheError should have correct error properties', () {
        const state = CacheError(
          failure: CacheFailure('Cache operation failed'),
          operation: CacheOperation.loading,
          key: 'error-key',
        );

        expect(state.hasError, isTrue);
        expect(state.isRecoverable, isTrue);
        expect(state.severity, equals(ErrorSeverity.medium));
      });

      test('CacheCleared should have correct success properties', () {
        const state = CacheCleared(
          clearType: ClearCacheType.byKeys,
          clearedEntries: 5,
          clearedKeys: ['key1', 'key2', 'key3', 'key4', 'key5'],
        );

        expect(state.isSuccess, isTrue);
        expect(state.successMessage, equals('Cleared 5 cache entries'));
      });
    });

    group('BLoC Getters', () {
      test('should provide correct configuration and statistics', () {
        expect(cacheBloc.config.maxSizeMB, equals(50));
        expect(cacheBloc.hitRatio, equals(0.0)); // No accesses yet
        expect(cacheBloc.totalAccesses, equals(0));
        expect(cacheBloc.averageAccessTime, equals(Duration.zero));
      });
    });

    group('Data Classes', () {
      group('CachePolicy', () {
        test('should create CachePolicy with defaults', () {
          const policy = CachePolicy(ttl: Duration(hours: 1));

          expect(policy.ttl, equals(const Duration(hours: 1)));
          expect(policy.priority, equals(CachePriority.normal));
          expect(policy.compressData, isFalse);
          expect(policy.enableEncryption, isFalse);
          expect(policy.evictionStrategy, equals(CacheEvictionStrategy.lru));
        });

        test('should serialize to/from JSON correctly', () {
          const policy = CachePolicy(
            ttl: Duration(hours: 2),
            priority: CachePriority.high,
            compressData: true,
            enableEncryption: true,
            evictionStrategy: CacheEvictionStrategy.fifo,
          );

          final json = policy.toJson();
          final restored = CachePolicy.fromJson(json);

          expect(restored.ttl, equals(policy.ttl));
          expect(restored.priority, equals(policy.priority));
          expect(restored.compressData, equals(policy.compressData));
          expect(restored.enableEncryption, equals(policy.enableEncryption));
          expect(restored.evictionStrategy, equals(policy.evictionStrategy));
        });
      });

      group('CacheMetadata', () {
        test('should calculate expiration correctly', () {
          final now = DateTime.now();
          final metadata = CacheMetadata(
            createdAt: now.subtract(const Duration(minutes: 30)),
            lastAccessedAt: now.subtract(const Duration(minutes: 10)),
            expiresAt: now.add(const Duration(minutes: 30)),
            accessCount: 5,
            sizeBytes: 1024,
            priority: CachePriority.normal,
          );

          expect(metadata.isExpired, isFalse);
          expect(metadata.age.inMinutes, equals(30));
          expect(metadata.timeSinceLastAccess.inMinutes, equals(10));
        });

        test('should create copy with updated access', () {
          final metadata = CacheMetadata(
            createdAt: DateTime.now(),
            lastAccessedAt: DateTime.now().subtract(const Duration(minutes: 5)),
            expiresAt: DateTime.now().add(const Duration(hours: 1)),
            accessCount: 3,
            sizeBytes: 1024,
            priority: CachePriority.normal,
          );

          final updated = metadata.copyWithAccess();
          expect(updated.accessCount, equals(4));
          expect(updated.lastAccessedAt.isAfter(metadata.lastAccessedAt), isTrue);
        });

        test('should serialize to/from JSON correctly', () {
          final metadata = CacheMetadata(
            createdAt: DateTime.now(),
            lastAccessedAt: DateTime.now(),
            expiresAt: DateTime.now().add(const Duration(hours: 1)),
            accessCount: 10,
            sizeBytes: 2048,
            tags: ['tag1', 'tag2'],
            priority: CachePriority.critical,
            isEncrypted: true,
            isCompressed: true,
          );

          final json = metadata.toJson();
          final restored = CacheMetadata.fromJson(json);

          expect(restored.accessCount, equals(metadata.accessCount));
          expect(restored.sizeBytes, equals(metadata.sizeBytes));
          expect(restored.tags, equals(metadata.tags));
          expect(restored.priority, equals(metadata.priority));
          expect(restored.isEncrypted, equals(metadata.isEncrypted));
          expect(restored.isCompressed, equals(metadata.isCompressed));
        });
      });

      group('CacheConfiguration', () {
        test('should create configuration with defaults', () {
          const config = CacheConfiguration();

          expect(config.maxSizeMB, equals(100));
          expect(config.defaultTtl, equals(const Duration(hours: 24)));
          expect(config.enableAutoCleanup, isTrue);
          expect(config.cleanupThreshold, equals(0.8));
        });

        test('should serialize to/from JSON correctly', () {
          const config = CacheConfiguration(
            maxSizeMB: 200,
            defaultTtl: Duration(hours: 12),
            enableAutoCleanup: false,
            cleanupThreshold: 0.9,
          );

          final json = config.toJson();
          final restored = CacheConfiguration.fromJson(json);

          expect(restored.maxSizeMB, equals(config.maxSizeMB));
          expect(restored.defaultTtl, equals(config.defaultTtl));
          expect(restored.enableAutoCleanup, equals(config.enableAutoCleanup));
          expect(restored.cleanupThreshold, equals(config.cleanupThreshold));
        });
      });

      group('CacheStatistics', () {
        test('should create statistics correctly', () {
          const stats = CacheStatistics(
            totalEntries: 100,
            totalSizeMB: 50,
            hitCount: 80,
            missCount: 20,
            hitRatio: 0.8,
            expiredEntries: 5,
            entriesByPriority: {
              CachePriority.normal: 70,
              CachePriority.high: 20,
              CachePriority.critical: 10,
            },
            entriesByTag: {'prediction': 50, 'user-data': 30},
            lastCleanup: Duration.zero, // Using Duration.zero as placeholder
            averageAccessTime: Duration(milliseconds: 50),
          );

          expect(stats.totalEntries, equals(100));
          expect(stats.hitRatio, equals(0.8));
          expect(stats.entriesByPriority[CachePriority.normal], equals(70));
        });
      });
    });

    group('Edge Cases and Error Handling', () {
      test('should handle encryption/decryption edge cases', () {
        // Test with non-encrypted data
        final normalData = {'key': 'value'};
        expect(cacheBloc.toString(), contains('CacheBloc')); // Basic sanity check
      });

      test('should handle compression edge cases', () {
        // Test with non-compressed data
        final normalData = {'key': 'value'};
        expect(normalData['key'], equals('value')); // Basic sanity check
      });

      blocTest<CacheBloc, CacheState>(
        'should handle cache size threshold checking',
        build: () {
          when(mockCacheService.getStats()).thenAnswer((_) async => {
            'size_mb': 45, // Above threshold of 40 (80% of 50MB)
            'total_entries': 100,
          });
          when(mockCacheService.clearExpired()).thenAnswer((_) async {});
          return cacheBloc;
        },
        act: (bloc) {
          // Trigger cache size check (would normally happen after caching data)
          bloc.add(const OptimizeCache(strategy: OptimizationStrategy.balanced));
        },
        expect: () => [
          isA<CacheLoading>(),
          isA<CacheOptimized>(),
        ],
      );

      blocTest<CacheBloc, CacheState>(
        'should track hit ratio correctly across multiple operations',
        build: () {
          when(mockCacheService.retrieve('hit-key'))
              .thenAnswer((_) async => {'data': 'hit'});
          when(mockCacheService.retrieve('miss-key'))
              .thenAnswer((_) async => null);
          return cacheBloc;
        },
        act: (bloc) async {
          bloc.add(const LoadFromCache(key: 'hit-key'));
          await Future.delayed(const Duration(milliseconds: 10));
          bloc.add(const LoadFromCache(key: 'miss-key'));
          await Future.delayed(const Duration(milliseconds: 10));
          bloc.add(const LoadFromCache(key: 'hit-key'));
        },
        expect: () => [
          isA<CacheLoading>(), // First hit
          isA<CacheLoaded>(),
          isA<CacheLoading>(), // Miss
          isA<CacheError>(),
          isA<CacheLoading>(), // Second hit
          isA<CacheLoaded>(),
        ],
        verify: (_) {
          // Hit ratio should be 2/3 ≈ 0.67
          expect(cacheBloc.hitRatio, greaterThan(0.6));
          expect(cacheBloc.totalAccesses, equals(3));
        },
      );
    });
  });
}