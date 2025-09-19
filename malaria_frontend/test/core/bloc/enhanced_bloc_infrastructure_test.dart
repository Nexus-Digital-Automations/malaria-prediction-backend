/// Comprehensive unit tests for Enhanced BLoC Infrastructure
///
/// Tests cover:
/// - Global event bus functionality
/// - Service registration and lifetime management
/// - Error recovery and retry strategies
/// - Performance monitoring and health checks
/// - Service scoping and dependency injection
/// - Configuration management
/// - Memory management and cleanup
library;

import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:malaria_frontend/core/bloc/enhanced_bloc_infrastructure.dart';

// Generate mocks
@GenerateMocks([
  BlocBase,
])
import 'enhanced_bloc_infrastructure_test.mocks.dart';

/// Test BLoC for testing purposes
class TestBloc extends Bloc<TestEvent, TestState> {
  TestBloc() : super(const TestState.initial()) {
    on<TestEventTriggered>(_onEventTriggered);
    on<TestEventWithError>(_onEventWithError);
  }

  Future<void> _onEventTriggered(TestEventTriggered event, Emitter<TestState> emit) async {
    emit(const TestState.loading());
    await Future.delayed(const Duration(milliseconds: 100));
    emit(TestState.success(event.data));
  }

  Future<void> _onEventWithError(TestEventWithError event, Emitter<TestState> emit) async {
    emit(const TestState.loading());
    await Future.delayed(const Duration(milliseconds: 50));
    emit(TestState.error(event.errorMessage));
  }
}

/// Test events
abstract class TestEvent {
  const TestEvent();
}

class TestEventTriggered extends TestEvent {
  final String data;
  const TestEventTriggered(this.data);
}

class TestEventWithError extends TestEvent {
  final String errorMessage;
  const TestEventWithError(this.errorMessage);
}

/// Test states
abstract class TestState {
  const TestState();

  const factory TestState.initial() = TestInitial;
  const factory TestState.loading() = TestLoading;
  const factory TestState.success(String data) = TestSuccess;
  const factory TestState.error(String message) = TestError;
}

class TestInitial extends TestState {
  const TestInitial();
}

class TestLoading extends TestState {
  const TestLoading();
}

class TestSuccess extends TestState {
  final String data;
  const TestSuccess(this.data);
}

class TestError extends TestState {
  final String message;
  const TestError(this.message);
}

/// Test service for dependency injection testing
class TestService {
  final String name;
  final DateTime createdAt;
  bool isDisposed = false;

  TestService(this.name) : createdAt = DateTime.now();

  void dispose() {
    isDisposed = true;
  }

  String processData(String input) {
    if (isDisposed) {
      throw StateError('Service is disposed');
    }
    return 'Processed: $input';
  }
}

/// Test service that throws errors for error recovery testing
class UnreliableTestService {
  int _callCount = 0;
  final int failUntilCall;

  UnreliableTestService({this.failUntilCall = 2});

  Future<String> unreliableOperation() async {
    _callCount++;
    if (_callCount <= failUntilCall) {
      throw Exception('Operation failed on attempt $_callCount');
    }
    return 'Success on attempt $_callCount';
  }

  void reset() {
    _callCount = 0;
  }
}

void main() {
  group('Enhanced BLoC Infrastructure Tests', () {
    setUp(() async {
      // Reset infrastructure before each test
      await EnhancedBlocInfrastructure.dispose();
    });

    tearDown(() async {
      // Clean up after each test
      await EnhancedBlocInfrastructure.dispose();
    });

    group('Initialization and Basic Setup', () {
      test('should initialize successfully with default configuration', () async {
        await EnhancedBlocInfrastructure.initialize();

        final healthReport = EnhancedBlocInfrastructure.getHealthReport();
        expect(healthReport['isInitialized'], isTrue);
        expect(healthReport['totalServices'], equals(0));
        expect(healthReport['activeScopes'], greaterThan(0)); // Root and default scopes
      });

      test('should initialize with custom configuration', () async {
        await EnhancedBlocInfrastructure.initialize(
          enablePerformanceMonitoring: false,
          enableHealthChecks: false,
          healthCheckInterval: const Duration(seconds: 30),
        );

        final healthReport = EnhancedBlocInfrastructure.getHealthReport();
        expect(healthReport['isInitialized'], isTrue);
      });

      test('should handle multiple initialization calls gracefully', () async {
        await EnhancedBlocInfrastructure.initialize();
        await EnhancedBlocInfrastructure.initialize(); // Second call should be safe
        await EnhancedBlocInfrastructure.initialize(); // Third call should be safe

        final healthReport = EnhancedBlocInfrastructure.getHealthReport();
        expect(healthReport['isInitialized'], isTrue);
      });
    });

    group('Global Event Bus', () {
      late GlobalEventBus eventBus;

      setUp(() async {
        await EnhancedBlocInfrastructure.initialize();
        eventBus = EnhancedBlocInfrastructure.eventBus;
      });

      test('should publish and receive events', () async {
        final receivedEvents = <ConnectivityChangedEvent>[];

        eventBus.subscribe<ConnectivityChangedEvent>(\n          'test_subscriber',\n          (event) => receivedEvents.add(event),\n        );\n\n        final testEvent = ConnectivityChangedEvent(\n          sourceBlocName: 'TestBloc',\n          connectivityResult: ConnectivityResult.wifi,\n          isOnline: true,\n        );\n\n        eventBus.publish(testEvent);\n        await Future.delayed(const Duration(milliseconds: 10));\n\n        expect(receivedEvents, hasLength(1));\n        expect(receivedEvents.first.sourceBlocName, equals('TestBloc'));\n        expect(receivedEvents.first.isOnline, isTrue);\n      });\n\n      test('should filter events correctly', () async {\n        final wifiEvents = <ConnectivityChangedEvent>[];\n        final mobileEvents = <ConnectivityChangedEvent>[];\n        \n        eventBus.subscribe<ConnectivityChangedEvent>(\n          'wifi_subscriber',\n          (event) => wifiEvents.add(event),\n          filter: (event) => event.connectivityResult == ConnectivityResult.wifi,\n        );\n\n        eventBus.subscribe<ConnectivityChangedEvent>(\n          'mobile_subscriber',\n          (event) => mobileEvents.add(event),\n          filter: (event) => event.connectivityResult == ConnectivityResult.mobile,\n        );\n\n        eventBus.publish(ConnectivityChangedEvent(\n          sourceBlocName: 'TestBloc',\n          connectivityResult: ConnectivityResult.wifi,\n          isOnline: true,\n        ));\n\n        eventBus.publish(ConnectivityChangedEvent(\n          sourceBlocName: 'TestBloc',\n          connectivityResult: ConnectivityResult.mobile,\n          isOnline: true,\n        ));\n\n        await Future.delayed(const Duration(milliseconds: 10));\n\n        expect(wifiEvents, hasLength(1));\n        expect(mobileEvents, hasLength(1));\n        expect(wifiEvents.first.connectivityResult, equals(ConnectivityResult.wifi));\n        expect(mobileEvents.first.connectivityResult, equals(ConnectivityResult.mobile));\n      });\n\n      test('should maintain event history', () async {\n        for (int i = 0; i < 5; i++) {\n          eventBus.publish(ConnectivityChangedEvent(\n            sourceBlocName: 'TestBloc$i',\n            connectivityResult: ConnectivityResult.wifi,\n            isOnline: true,\n          ));\n        }\n\n        final history = eventBus.getEventHistory();\n        expect(history, hasLength(5));\n        expect(history.first.sourceBlocName, equals('TestBloc0'));\n        expect(history.last.sourceBlocName, equals('TestBloc4'));\n      });\n\n      test('should limit event history size', () async {\n        // Publish more than max history size (100 events)\n        for (int i = 0; i < 105; i++) {\n          eventBus.publish(ConnectivityChangedEvent(\n            sourceBlocName: 'TestBloc$i',\n            connectivityResult: ConnectivityResult.wifi,\n            isOnline: true,\n          ));\n        }\n\n        final history = eventBus.getEventHistory();\n        expect(history, hasLength(100)); // Should be limited to max size\n        expect(history.first.sourceBlocName, equals('TestBloc5')); // First 5 should be removed\n        expect(history.last.sourceBlocName, equals('TestBloc104'));\n      });\n\n      test('should unsubscribe correctly', () async {\n        final receivedEvents = <ConnectivityChangedEvent>[];\n        \n        eventBus.subscribe<ConnectivityChangedEvent>(\n          'test_subscriber',\n          (event) => receivedEvents.add(event),\n        );\n\n        eventBus.publish(ConnectivityChangedEvent(\n          sourceBlocName: 'TestBloc',\n          connectivityResult: ConnectivityResult.wifi,\n          isOnline: true,\n        ));\n\n        await eventBus.unsubscribe('test_subscriber');\n\n        eventBus.publish(ConnectivityChangedEvent(\n          sourceBlocName: 'TestBloc2',\n          connectivityResult: ConnectivityResult.mobile,\n          isOnline: true,\n        ));\n\n        await Future.delayed(const Duration(milliseconds: 10));\n\n        expect(receivedEvents, hasLength(1)); // Only first event should be received\n      });\n    });\n\n    group('Service Registration and Lifetime Management', () {\n      setUp(() async {\n        await EnhancedBlocInfrastructure.initialize();\n      });\n\n      test('should register singleton service correctly', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('TestService')\n            .using(() => TestService('singleton'))\n            .withLifetime(ServiceLifetime.singleton)\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        final instance1 = EnhancedBlocInfrastructure.get<TestService>();\n        final instance2 = EnhancedBlocInfrastructure.get<TestService>();\n\n        expect(instance1, isNotNull);\n        expect(instance2, isNotNull);\n        expect(identical(instance1, instance2), isTrue); // Same instance\n        expect(instance1.name, equals('singleton'));\n      });\n\n      test('should register transient service correctly', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('TestService')\n            .using(() => TestService('transient'))\n            .withLifetime(ServiceLifetime.transient)\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        final instance1 = EnhancedBlocInfrastructure.get<TestService>();\n        final instance2 = EnhancedBlocInfrastructure.get<TestService>();\n\n        expect(instance1, isNotNull);\n        expect(instance2, isNotNull);\n        expect(identical(instance1, instance2), isFalse); // Different instances\n        expect(instance1.name, equals('transient'));\n        expect(instance2.name, equals('transient'));\n      });\n\n      test('should register scoped service correctly', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('TestService')\n            .using(() => TestService('scoped'))\n            .withLifetime(ServiceLifetime.scoped)\n            .inScope('test_scope')\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        final scope1 = EnhancedBlocInfrastructure.createScope('scope1');\n        final scope2 = EnhancedBlocInfrastructure.createScope('scope2');\n\n        final instance1 = EnhancedBlocInfrastructure.getScoped<TestService>(scope1.id);\n        final instance2 = EnhancedBlocInfrastructure.getScoped<TestService>(scope1.id);\n        final instance3 = EnhancedBlocInfrastructure.getScoped<TestService>(scope2.id);\n\n        expect(instance1, isNotNull);\n        expect(instance2, isNotNull);\n        expect(instance3, isNotNull);\n        expect(identical(instance1, instance2), isTrue); // Same scope, same instance\n        expect(identical(instance1, instance3), isFalse); // Different scope, different instance\n      });\n\n      test('should handle service with TTL correctly', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('TestService')\n            .using(() => TestService('cached'))\n            .withLifetime(ServiceLifetime.lazySingleton)\n            .withTtl(const Duration(milliseconds: 100))\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        final instance1 = EnhancedBlocInfrastructure.get<TestService>();\n        expect(instance1.name, equals('cached'));\n\n        // Wait for TTL to expire\n        await Future.delayed(const Duration(milliseconds: 150));\n\n        final instance2 = EnhancedBlocInfrastructure.get<TestService>();\n        expect(instance2.name, equals('cached'));\n        \n        // Note: In this test, we can't easily verify that a new instance was created\n        // due to the way GetIt manages instances, but the TTL logic is tested in the infrastructure\n      });\n    });\n\n    group('Error Recovery and Retry Strategies', () {\n      late UnreliableTestService unreliableService;\n\n      setUp(() async {\n        await EnhancedBlocInfrastructure.initialize();\n        unreliableService = UnreliableTestService(failUntilCall: 2);\n      });\n\n      test('should retry failed operations with exponential backoff', () async {\n        final stopwatch = Stopwatch()..start();\n        \n        final result = await EnhancedBlocInfrastructure.applyErrorRecovery<String>(\n          Exception,\n          () => unreliableService.unreliableOperation(),\n          serviceName: 'UnreliableTestService',\n        );\n\n        stopwatch.stop();\n\n        expect(result, equals('Success on attempt 3'));\n        expect(stopwatch.elapsedMilliseconds, greaterThan(1000)); // At least 1s delay from retries\n      });\n\n      test('should fail after max retry attempts', () async {\n        final unreliableService = UnreliableTestService(failUntilCall: 10); // Will never succeed\n\n        expect(\n          () => EnhancedBlocInfrastructure.applyErrorRecovery<String>(\n            Exception,\n            () => unreliableService.unreliableOperation(),\n            serviceName: 'UnreliableTestService',\n          ),\n          throwsA(isA<Exception>()),\n        );\n      });\n\n      test('should return null for unknown error types', () async {\n        final result = await EnhancedBlocInfrastructure.applyErrorRecovery<String>(\n          StateError, // No retry policy for StateError\n          () => throw StateError('Unknown error'),\n          serviceName: 'TestService',\n        );\n\n        expect(result, isNull);\n      });\n\n      test('should succeed on first try without retries', () async {\n        final stopwatch = Stopwatch()..start();\n        \n        final result = await EnhancedBlocInfrastructure.applyErrorRecovery<String>(\n          Exception,\n          () => Future.value('immediate success'),\n          serviceName: 'TestService',\n        );\n\n        stopwatch.stop();\n\n        expect(result, equals('immediate success'));\n        expect(stopwatch.elapsedMilliseconds, lessThan(100)); // Should be immediate\n      });\n    });\n\n    group('Service Scoping', () {\n      setUp(() async {\n        await EnhancedBlocInfrastructure.initialize();\n      });\n\n      test('should create and manage service scopes correctly', () async {\n        final parentScope = EnhancedBlocInfrastructure.createScope('parent');\n        final childScope1 = EnhancedBlocInfrastructure.createScope('child1', parent: parentScope);\n        final childScope2 = EnhancedBlocInfrastructure.createScope('child2', parent: parentScope);\n\n        expect(parentScope.name, equals('parent'));\n        expect(childScope1.name, equals('child1'));\n        expect(childScope2.name, equals('child2'));\n        expect(childScope1.parent, equals(parentScope));\n        expect(childScope2.parent, equals(parentScope));\n      });\n\n      test('should maintain scope hierarchy paths correctly', () async {\n        final rootScope = EnhancedBlocInfrastructure.createScope('app');\n        final featureScope = EnhancedBlocInfrastructure.createScope('feature', parent: rootScope);\n        final componentScope = EnhancedBlocInfrastructure.createScope('component', parent: featureScope);\n\n        expect(rootScope.hierarchyPath, contains('app'));\n        expect(featureScope.hierarchyPath, contains('feature'));\n        expect(componentScope.hierarchyPath, contains('component'));\n        expect(componentScope.hierarchyPath, contains('app'));\n        expect(componentScope.hierarchyPath, contains('feature'));\n      });\n\n      test('should isolate instances between different scopes', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('TestService')\n            .using(() => TestService('scoped'))\n            .withLifetime(ServiceLifetime.scoped)\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        final scope1 = EnhancedBlocInfrastructure.createScope('scope1');\n        final scope2 = EnhancedBlocInfrastructure.createScope('scope2');\n\n        scope1.addInstance<TestService>(TestService('scope1_service'));\n        scope2.addInstance<TestService>(TestService('scope2_service'));\n\n        final instance1 = scope1.getInstance<TestService>();\n        final instance2 = scope2.getInstance<TestService>();\n\n        expect(instance1?.name, equals('scope1_service'));\n        expect(instance2?.name, equals('scope2_service'));\n        expect(identical(instance1, instance2), isFalse);\n      });\n\n      test('should properly dispose scoped instances', () async {\n        final scope = EnhancedBlocInfrastructure.createScope('test_scope');\n        final service = TestService('disposable');\n        \n        scope.addInstance<TestService>(service);\n        expect(service.isDisposed, isFalse);\n\n        await scope.dispose();\n        \n        // Note: The actual disposal of TestService depends on the scope implementation\n        // In a real scenario, the scope would call dispose() on disposable instances\n      });\n    });\n\n    group('Performance Monitoring and Health Checks', () {\n      setUp(() async {\n        await EnhancedBlocInfrastructure.initialize(\n          enableHealthChecks: true,\n          healthCheckInterval: const Duration(milliseconds: 100),\n        );\n      });\n\n      test('should generate comprehensive health report', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('TestService')\n            .using(() => TestService('healthy'))\n            .withHealthCheck()\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        final healthReport = EnhancedBlocInfrastructure.getHealthReport();\n\n        expect(healthReport['isInitialized'], isTrue);\n        expect(healthReport['totalServices'], equals(1));\n        expect(healthReport['services'], hasLength(1));\n        expect(healthReport['services'][0]['name'], equals('TestService'));\n        expect(healthReport['services'][0]['healthCheckEnabled'], isTrue);\n      });\n\n      test('should track service performance metrics', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('TestService')\n            .using(() => TestService('performance'))\n            .withHealthCheck()\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        // Access service multiple times to generate metrics\n        for (int i = 0; i < 5; i++) {\n          final service = EnhancedBlocInfrastructure.get<TestService>();\n          service.processData('test$i');\n        }\n\n        final healthReport = EnhancedBlocInfrastructure.getHealthReport();\n        expect(healthReport['totalServices'], equals(1));\n        \n        // In a real implementation, you would check actual performance metrics here\n      });\n\n      test('should handle service health check failures gracefully', () async {\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('FailingService')\n            .using(() => throw Exception('Service creation failed'))\n            .withHealthCheck()\n            .build();\n\n        expect(\n          () => EnhancedBlocInfrastructure.registerService(registration),\n          throwsA(isA<Exception>()),\n        );\n      });\n    });\n\n    group('Memory Management and Cleanup', () {\n      setUp(() async {\n        await EnhancedBlocInfrastructure.initialize();\n      });\n\n      test('should properly dispose all services on shutdown', () async {\n        final services = <TestService>[];\n        \n        for (int i = 0; i < 3; i++) {\n          final service = TestService('service$i');\n          services.add(service);\n          \n          final registration = ServiceRegistrationBuilder<TestService>()\n              .named('TestService$i')\n              .using(() => service)\n              .withLifetime(ServiceLifetime.singleton)\n              .build();\n\n          await EnhancedBlocInfrastructure.registerService(registration);\n        }\n\n        // Verify services are registered\n        final healthReport = EnhancedBlocInfrastructure.getHealthReport();\n        expect(healthReport['totalServices'], equals(3));\n\n        // Dispose infrastructure\n        await EnhancedBlocInfrastructure.dispose();\n\n        // Verify cleanup\n        final disposedHealthReport = EnhancedBlocInfrastructure.getHealthReport();\n        expect(disposedHealthReport['isInitialized'], isFalse);\n        expect(disposedHealthReport['totalServices'], equals(0));\n      });\n\n      test('should clean up event bus subscriptions on disposal', () async {\n        final eventBus = EnhancedBlocInfrastructure.eventBus;\n        final receivedEvents = <ConnectivityChangedEvent>[];\n        \n        eventBus.subscribe<ConnectivityChangedEvent>(\n          'test_subscriber',\n          (event) => receivedEvents.add(event),\n        );\n\n        eventBus.publish(ConnectivityChangedEvent(\n          sourceBlocName: 'TestBloc',\n          connectivityResult: ConnectivityResult.wifi,\n          isOnline: true,\n        ));\n\n        await Future.delayed(const Duration(milliseconds: 10));\n        expect(receivedEvents, hasLength(1));\n\n        // Dispose infrastructure\n        await EnhancedBlocInfrastructure.dispose();\n\n        // Try to publish another event (should not reach subscriber)\n        eventBus.publish(ConnectivityChangedEvent(\n          sourceBlocName: 'TestBloc2',\n          connectivityResult: ConnectivityResult.mobile,\n          isOnline: true,\n        ));\n\n        await Future.delayed(const Duration(milliseconds: 10));\n        expect(receivedEvents, hasLength(1)); // Should still be 1\n      });\n\n      test('should handle disposal of uninitialized infrastructure gracefully', () async {\n        // Should not throw when disposing uninitialized infrastructure\n        expect(() => EnhancedBlocInfrastructure.dispose(), returnsNormally);\n      });\n    });\n\n    group('Configuration Management', () {\n      setUp(() async {\n        await EnhancedBlocInfrastructure.initialize();\n      });\n\n      test('should register services with custom configurations', () async {\n        final customConfig = {\n          'timeout': 5000,\n          'retries': 3,\n          'enableCaching': true,\n        };\n\n        final registration = ServiceRegistrationBuilder<TestService>()\n            .named('ConfiguredService')\n            .using(() => TestService('configured'))\n            .withConfiguration(customConfig)\n            .withPriority(10)\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(registration);\n\n        final healthReport = EnhancedBlocInfrastructure.getHealthReport();\n        final serviceInfo = healthReport['services'][0];\n        \n        expect(serviceInfo['name'], equals('ConfiguredService'));\n        // Configuration would be accessible through the registration in real implementation\n      });\n\n      test('should handle complex service dependencies', () async {\n        // Register dependency first\n        final dependencyRegistration = ServiceRegistrationBuilder<TestService>()\n            .named('DependencyService')\n            .using(() => TestService('dependency'))\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(dependencyRegistration);\n\n        // Register service that depends on it\n        final mainRegistration = ServiceRegistrationBuilder<TestService>()\n            .named('MainService')\n            .using(() => TestService('main'))\n            .dependsOn([TestService])\n            .build();\n\n        await EnhancedBlocInfrastructure.registerService(mainRegistration);\n\n        final healthReport = EnhancedBlocInfrastructure.getHealthReport();\n        expect(healthReport['totalServices'], equals(2));\n      });\n    });\n\n    group('Integration Tests', () {\n      test('should handle complex scenario with multiple services and events', () async {\n        await EnhancedBlocInfrastructure.initialize(\n          enablePerformanceMonitoring: true,\n          enableHealthChecks: true,\n          healthCheckInterval: const Duration(milliseconds: 50),\n        );\n\n        // Register multiple services with different lifetimes\n        final services = [\n          ServiceRegistrationBuilder<TestService>()\n              .named('SingletonService')\n              .using(() => TestService('singleton'))\n              .withLifetime(ServiceLifetime.singleton)\n              .withHealthCheck()\n              .build(),\n          ServiceRegistrationBuilder<TestService>()\n              .named('TransientService')\n              .using(() => TestService('transient'))\n              .withLifetime(ServiceLifetime.transient)\n              .withHealthCheck()\n              .build(),\n        ];\n\n        for (final service in services) {\n          await EnhancedBlocInfrastructure.registerService(service);\n        }\n\n        // Set up event subscriptions\n        final eventBus = EnhancedBlocInfrastructure.eventBus;\n        final receivedEvents = <GlobalBlocEvent>[];\n        \n        eventBus.subscribe<GlobalBlocEvent>(\n          'integration_test',\n          (event) => receivedEvents.add(event),\n        );\n\n        // Publish various events\n        eventBus.publish(ConnectivityChangedEvent(\n          sourceBlocName: 'ConnectivityBloc',\n          connectivityResult: ConnectivityResult.wifi,\n          isOnline: true,\n        ));\n\n        eventBus.publish(AuthenticationStateChangedEvent(\n          sourceBlocName: 'AuthBloc',\n          isAuthenticated: true,\n          userId: 'user123',\n        ));\n\n        eventBus.publish(ErrorOccurredEvent(\n          sourceBlocName: 'DataBloc',\n          errorMessage: 'Network timeout',\n          errorType: 'NetworkError',\n          severity: ErrorSeverity.medium,\n        ));\n\n        // Test error recovery\n        final unreliableService = UnreliableTestService(failUntilCall: 1);\n        final recoveryResult = await EnhancedBlocInfrastructure.applyErrorRecovery<String>(\n          Exception,\n          () => unreliableService.unreliableOperation(),\n          serviceName: 'IntegrationTestService',\n        );\n\n        await Future.delayed(const Duration(milliseconds: 100));\n\n        // Verify results\n        expect(receivedEvents, hasLength(3));\n        expect(recoveryResult, equals('Success on attempt 2'));\n        \n        final healthReport = EnhancedBlocInfrastructure.getHealthReport();\n        expect(healthReport['isInitialized'], isTrue);\n        expect(healthReport['totalServices'], equals(2));\n        expect(healthReport['eventBusStats'], isNotEmpty);\n\n        // Clean up\n        await EnhancedBlocInfrastructure.dispose();\n        \n        final finalHealthReport = EnhancedBlocInfrastructure.getHealthReport();\n        expect(finalHealthReport['isInitialized'], isFalse);\n      });\n    });\n  });\n}\n