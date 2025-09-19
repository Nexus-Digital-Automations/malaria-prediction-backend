#!/usr/bin/env dart

/// Test Runner Script for Malaria Prediction App
/// Comprehensive testing orchestration and reporting
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Orchestrate all testing phases with detailed reporting
library;

import 'dart:io';

import '../test/test_coverage_config.dart';

/// Main test runner orchestrating all testing phases
void main(List<String> arguments) async {
  final runner = TestRunner();
  await runner.run(arguments);
}

class TestRunner {
  static const String version = '1.0.0';

  /// Test execution phases
  final Map<String, TestPhase> phases = {
    'lint': TestPhase(
      name: 'Code Analysis & Linting',
      description: 'Run static analysis and linting checks',
      commands: ['flutter analyze --fatal-infos --fatal-warnings'],
      required: true,
    ),
    'format': TestPhase(
      name: 'Code Formatting',
      description: 'Check code formatting consistency',
      commands: ['dart format --set-exit-if-changed lib/ test/'],
      required: true,
    ),
    'unit': TestPhase(
      name: 'Unit Tests',
      description: 'Run unit tests with coverage',
      commands: ['flutter test test/unit/ --coverage --reporter json'],
      required: true,
      generatesCoverage: true,
    ),
    'widget': TestPhase(
      name: 'Widget Tests',
      description: 'Run widget tests',
      commands: ['flutter test test/widget/ --coverage'],
      required: true,
      generatesCoverage: true,
    ),
    'integration': TestPhase(
      name: 'Integration Tests',
      description: 'Run integration tests',
      commands: ['flutter test test/integration/ --coverage'],
      required: false,
      generatesCoverage: true,
    ),
    'performance': TestPhase(
      name: 'Performance Tests',
      description: 'Run performance benchmarks',
      commands: ['flutter test test/performance/ --reporter json'],
      required: false,
    ),
    'e2e': TestPhase(
      name: 'End-to-End Tests',
      description: 'Run full application E2E tests',
      commands: ['flutter drive --target=test_driver/app.dart'],
      required: false,
    ),
  };

  /// Run test suite with specified configuration
  Future<void> run(List<String> arguments) async {
    final config = _parseArguments(arguments);

    print('🧪 Malaria Prediction App Test Runner v$version');
    print('═' * 60);

    final results = <String, TestResult>{};
    final stopwatch = Stopwatch()..start();

    try {
      // Display execution plan
      _displayExecutionPlan(config);

      // Execute test phases
      for (final phaseEntry in phases.entries) {
        final phaseName = phaseEntry.key;
        final phase = phaseEntry.value;

        if (config.skipPhases.contains(phaseName)) {
          print('⏭️  Skipping ${phase.name}');
          continue;
        }

        if (config.onlyPhases.isNotEmpty && !config.onlyPhases.contains(phaseName)) {
          continue;
        }

        print('\n🔄 Running ${phase.name}...');
        print('   ${phase.description}');

        final result = await _runPhase(phase, config);
        results[phaseName] = result;

        if (!result.passed && phase.required && !config.continueOnFailure) {
          print('❌ Required phase failed: ${phase.name}');
          break;
        }
      }

      // Generate coverage reports if applicable
      if (config.generateCoverage && _hasCoverageData()) {
        await _generateCoverageReports(config);
      }

      // Display summary
      _displaySummary(results, stopwatch.elapsed);

      // Exit with appropriate code
      final overallSuccess = _calculateOverallSuccess(results);
      exit(overallSuccess ? 0 : 1);

    } catch (e) {
      print('💥 Test runner failed: $e');
      exit(1);
    }
  }

  /// Parse command line arguments
  TestConfig _parseArguments(List<String> arguments) {
    final config = TestConfig();

    for (int i = 0; i < arguments.length; i++) {
      final arg = arguments[i];

      switch (arg) {
        case '--help':
        case '-h':
          _displayHelp();
          exit(0);

        case '--verbose':
        case '-v':
          config.verbose = true;
          break;

        case '--coverage':
        case '-c':
          config.generateCoverage = true;
          break;

        case '--continue-on-failure':
          config.continueOnFailure = true;
          break;

        case '--skip':
          if (i + 1 < arguments.length) {
            config.skipPhases.addAll(arguments[++i].split(','));
          }
          break;

        case '--only':
          if (i + 1 < arguments.length) {
            config.onlyPhases.addAll(arguments[++i].split(','));
          }
          break;

        case '--output':
        case '-o':
          if (i + 1 < arguments.length) {
            config.outputDir = arguments[++i];
          }
          break;

        default:
          if (arg.startsWith('--')) {
            print('⚠️  Unknown option: $arg');
          }
      }
    }

    return config;
  }

  /// Display help information
  void _displayHelp() {
    print('''
Malaria Prediction App Test Runner v$version

USAGE:
    dart scripts/run_tests.dart [OPTIONS]

OPTIONS:
    -h, --help                 Display this help message
    -v, --verbose              Enable verbose output
    -c, --coverage             Generate coverage reports
    --continue-on-failure      Continue running tests even if some fail
    --skip PHASES              Skip specified test phases (comma-separated)
    --only PHASES              Run only specified test phases (comma-separated)
    -o, --output DIR           Output directory for reports

AVAILABLE PHASES:
    lint                       Code analysis and linting
    format                     Code formatting checks
    unit                       Unit tests
    widget                     Widget tests
    integration               Integration tests
    performance               Performance tests
    e2e                       End-to-end tests

EXAMPLES:
    dart scripts/run_tests.dart --coverage
    dart scripts/run_tests.dart --only unit,widget
    dart scripts/run_tests.dart --skip e2e --continue-on-failure
''');
  }

  /// Display execution plan
  void _displayExecutionPlan(TestConfig config) {
    print('\n📋 Execution Plan:');

    final phasesToRun = phases.entries.where((entry) {
      final phaseName = entry.key;
      if (config.skipPhases.contains(phaseName)) return false;
      if (config.onlyPhases.isNotEmpty && !config.onlyPhases.contains(phaseName)) return false;
      return true;
    }).toList();

    for (final entry in phasesToRun) {
      final required = entry.value.required ? '[REQUIRED]' : '[OPTIONAL]';
      print('   • ${entry.value.name} $required');
    }

    print('\n⚙️  Configuration:');
    print('   • Verbose: ${config.verbose}');
    print('   • Generate Coverage: ${config.generateCoverage}');
    print('   • Continue on Failure: ${config.continueOnFailure}');
    print('   • Output Directory: ${config.outputDir}');
  }

  /// Run a single test phase
  Future<TestResult> _runPhase(TestPhase phase, TestConfig config) async {
    final stopwatch = Stopwatch()..start();
    final results = <CommandResult>[];

    for (final command in phase.commands) {
      if (config.verbose) {
        print('   Running: $command');
      }

      final result = await _runCommand(command, config);
      results.add(result);

      if (!result.success && phase.required) {
        break;
      }
    }

    stopwatch.stop();

    final overallSuccess = results.every((r) => r.success);
    final status = overallSuccess ? '✅' : '❌';
    print('   $status ${phase.name} completed in ${stopwatch.elapsed.inMilliseconds}ms');

    if (!overallSuccess && config.verbose) {
      for (final result in results.where((r) => !r.success)) {
        print('   Error: ${result.error}');
      }
    }

    return TestResult(
      phase: phase,
      passed: overallSuccess,
      duration: stopwatch.elapsed,
      commandResults: results,
    );
  }

  /// Run a single command
  Future<CommandResult> _runCommand(String command, TestConfig config) async {
    try {
      final parts = command.split(' ');
      final executable = parts[0];
      final arguments = parts.sublist(1);

      final process = await Process.run(
        executable,
        arguments,
        runInShell: true,
      );

      if (config.verbose && process.stdout.toString().isNotEmpty) {
        print('   Output: ${process.stdout}');
      }

      return CommandResult(
        command: command,
        exitCode: process.exitCode,
        stdout: process.stdout.toString(),
        stderr: process.stderr.toString(),
        success: process.exitCode == 0,
        error: process.exitCode != 0 ? process.stderr.toString() : null,
      );

    } catch (e) {
      return CommandResult(
        command: command,
        exitCode: -1,
        stdout: '',
        stderr: '',
        success: false,
        error: e.toString(),
      );
    }
  }

  /// Check if coverage data exists
  bool _hasCoverageData() {
    return File('coverage/lcov.info').existsSync();
  }

  /// Generate coverage reports
  Future<void> _generateCoverageReports(TestConfig config) async {
    print('\n📊 Generating coverage reports...');

    try {
      final coverage = await TestCoverageConfig.analyzeCoverage();
      await TestCoverageConfig.generateReports(
        coverage: coverage,
        outputDir: '${config.outputDir}/coverage',
      );

      final validation = await TestCoverageConfig.validateCoverage();

      print('   📈 Overall line coverage: ${coverage.overallStatistics.linePercentage.toStringAsFixed(1)}%');
      print('   📊 Coverage validation: ${validation.passed ? "PASSED" : "FAILED"}');

      if (!validation.passed) {
        print('   ⚠️  Some coverage thresholds not met:');
        for (final entry in validation.validation.entries) {
          if (!(entry.value['passed'] as bool)) {
            print('      • ${entry.key}: ${entry.value['actual']}% < ${entry.value['threshold']}%');
          }
        }
      }

    } catch (e) {
      print('   ❌ Coverage report generation failed: $e');
    }
  }

  /// Display test summary
  void _displaySummary(Map<String, TestResult> results, Duration totalDuration) {
    print('\n${'═' * 60}');
    print('📋 Test Summary');
    print('═' * 60);

    final totalTests = results.length;
    final passedTests = results.values.where((r) => r.passed).length;
    final failedTests = totalTests - passedTests;

    print('Total Phases: $totalTests');
    print('Passed: $passedTests');
    print('Failed: $failedTests');
    print('Total Duration: ${totalDuration.inSeconds}s');
    print('');

    // Phase details
    for (final entry in results.entries) {
      final phaseName = entry.key;
      final result = entry.value;
      final status = result.passed ? '✅' : '❌';

      print('$status $phaseName (${result.duration.inMilliseconds}ms)');

      if (!result.passed) {
        for (final cmd in result.commandResults.where((c) => !c.success)) {
          print('   └─ ${cmd.command}: ${cmd.error ?? "Exit code ${cmd.exitCode}"}');
        }
      }
    }

    print('');
    print('Overall Result: ${_calculateOverallSuccess(results) ? "✅ PASSED" : "❌ FAILED"}');
  }

  /// Calculate overall success
  bool _calculateOverallSuccess(Map<String, TestResult> results) {
    // All required phases must pass
    for (final entry in results.entries) {
      final phaseName = entry.key;
      final result = entry.value;
      final phase = phases[phaseName]!;

      if (phase.required && !result.passed) {
        return false;
      }
    }

    return true;
  }
}

/// Test configuration
class TestConfig {
  bool verbose = false;
  bool generateCoverage = false;
  bool continueOnFailure = false;
  List<String> skipPhases = [];
  List<String> onlyPhases = [];
  String outputDir = 'test_reports';
}

/// Test phase definition
class TestPhase {
  final String name;
  final String description;
  final List<String> commands;
  final bool required;
  final bool generatesCoverage;

  TestPhase({
    required this.name,
    required this.description,
    required this.commands,
    this.required = false,
    this.generatesCoverage = false,
  });
}

/// Test result
class TestResult {
  final TestPhase phase;
  final bool passed;
  final Duration duration;
  final List<CommandResult> commandResults;

  TestResult({
    required this.phase,
    required this.passed,
    required this.duration,
    required this.commandResults,
  });
}

/// Command execution result
class CommandResult {
  final String command;
  final int exitCode;
  final String stdout;
  final String stderr;
  final bool success;
  final String? error;

  CommandResult({
    required this.command,
    required this.exitCode,
    required this.stdout,
    required this.stderr,
    required this.success,
    this.error,
  });
}