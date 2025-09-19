/// Test Runner Configuration for Malaria Frontend
///
/// Centralized test execution configuration with coverage reporting,
/// test categorization, and CI/CD integration for the malaria prediction system.

import 'package:flutter_test/flutter_test.dart';

import 'test_config.dart';

// Import all test suites
import 'unit/features/authentication/auth_bloc_test.dart' as auth_bloc_tests;
import 'unit/features/authentication/auth_repository_impl_test.dart' as auth_repo_tests;
import 'widget/features/authentication/login_page_test.dart' as login_page_tests;
import 'integration/auth_flow_test.dart' as auth_flow_tests;
import 'performance/performance_test.dart' as performance_tests;

void main() {
  setUpAll(() async {
    await TestConfig.initialize();
  });

  tearDownAll(() async {
    await TestConfig.cleanup();
  });

  group('All Tests Suite', () {
    group('Unit Tests', () {
      group('Authentication', () {
        auth_bloc_tests.main();
        auth_repo_tests.main();
      });
    });

    group('Widget Tests', () {
      group('Authentication', () {
        login_page_tests.main();
      });
    });

    group('Integration Tests', () {
      auth_flow_tests.main();
    });

    group('Performance Tests', () {
      performance_tests.main();
    });
  });
}