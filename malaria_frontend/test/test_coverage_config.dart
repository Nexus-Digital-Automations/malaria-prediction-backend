/// Test Coverage Configuration and Metrics
/// Defines coverage requirements and quality thresholds
///
/// Author: Testing Agent 8
/// Created: 2025-09-18
/// Purpose: Ensure comprehensive test coverage and quality metrics
library;

import 'dart:io';
import 'dart:convert';

/// Test coverage configuration and analysis tools
class TestCoverageConfig {
  /// Minimum coverage thresholds for different components
  static const Map<String, double> coverageThresholds = {
    'global': 90.0,
    'business_logic': 95.0,
    'data_layer': 90.0,
    'presentation_layer': 85.0,
    'core_utilities': 95.0,
    'widgets': 80.0,
    'integration': 75.0,
  };

  /// Files and directories to exclude from coverage
  static const List<String> coverageExclusions = [
    '**/*.g.dart',
    '**/*.freezed.dart',
    '**/*.config.dart',
    '**/*.mocks.dart',
    '**/generated_plugin_registrant.dart',
    'lib/generated/**',
    'lib/firebase_options.dart',
    'test/**',
    'test_driver/**',
    'integration_test/**',
  ];

  /// Coverage analysis and reporting
  static Future<CoverageReport> analyzeCoverage({
    String coverageFile = 'coverage/lcov.info',
  }) async {
    try {
      final file = File(coverageFile);
      if (!await file.exists()) {
        throw Exception('Coverage file not found: $coverageFile');
      }

      final content = await file.readAsString();
      return _parseLcovFile(content);
    } catch (e) {
      throw Exception('Failed to analyze coverage: $e');
    }
  }

  /// Parse LCOV format coverage file
  static CoverageReport _parseLcovFile(String content) {
    final lines = content.split('\n');
    final files = <FileCoverageInfo>[];
    FileCoverageInfo? currentFile;

    for (final line in lines) {
      if (line.startsWith('SF:')) {
        // Source file
        final filePath = line.substring(3);
        currentFile = FileCoverageInfo(filePath: filePath);
      } else if (line.startsWith('LF:')) {
        // Lines found
        final linesFound = int.parse(line.substring(3));
        currentFile?.linesFound = linesFound;
      } else if (line.startsWith('LH:')) {
        // Lines hit
        final linesHit = int.parse(line.substring(3));
        currentFile?.linesHit = linesHit;
      } else if (line.startsWith('FNF:')) {
        // Functions found
        final functionsFound = int.parse(line.substring(4));
        currentFile?.functionsFound = functionsFound;
      } else if (line.startsWith('FNH:')) {
        // Functions hit
        final functionsHit = int.parse(line.substring(4));
        currentFile?.functionsHit = functionsHit;
      } else if (line.startsWith('BRF:')) {
        // Branches found
        final branchesFound = int.parse(line.substring(4));
        currentFile?.branchesFound = branchesFound;
      } else if (line.startsWith('BRH:')) {
        // Branches hit
        final branchesHit = int.parse(line.substring(4));
        currentFile?.branchesHit = branchesHit;
      } else if (line == 'end_of_record' && currentFile != null) {
        files.add(currentFile);
        currentFile = null;
      }
    }

    return CoverageReport(files: files);
  }

  /// Generate coverage report in various formats
  static Future<void> generateReports({
    required CoverageReport coverage,
    String outputDir = 'coverage/reports',
  }) async {
    final dir = Directory(outputDir);
    await dir.create(recursive: true);

    // Generate HTML report
    await _generateHtmlReport(coverage, '$outputDir/index.html');

    // Generate JSON report
    await _generateJsonReport(coverage, '$outputDir/coverage.json');

    // Generate summary report
    await _generateSummaryReport(coverage, '$outputDir/summary.txt');

    // Generate threshold validation report
    await _generateThresholdReport(coverage, '$outputDir/thresholds.json');
  }

  /// Generate HTML coverage report
  static Future<void> _generateHtmlReport(
    CoverageReport coverage,
    String outputPath,
  ) async {
    final html = _buildHtmlReport(coverage);
    await File(outputPath).writeAsString(html);
  }

  /// Generate JSON coverage report
  static Future<void> _generateJsonReport(
    CoverageReport coverage,
    String outputPath,
  ) async {
    final jsonData = coverage.toJson();
    await File(outputPath).writeAsString(
      const JsonEncoder.withIndent('  ').convert(jsonData),
    );
  }

  /// Generate summary report
  static Future<void> _generateSummaryReport(
    CoverageReport coverage,
    String outputPath,
  ) async {
    final summary = _buildSummaryReport(coverage);
    await File(outputPath).writeAsString(summary);
  }

  /// Generate threshold validation report
  static Future<void> _generateThresholdReport(
    CoverageReport coverage,
    String outputPath,
  ) async {
    final validation = _validateThresholds(coverage);
    await File(outputPath).writeAsString(
      const JsonEncoder.withIndent('  ').convert(validation),
    );
  }

  /// Build HTML report content
  static String _buildHtmlReport(CoverageReport coverage) {
    final overallStats = coverage.overallStatistics;

    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Malaria Prediction App - Test Coverage Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .metric { background: white; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }
        .metric h3 { margin-top: 0; color: #333; }
        .metric .value { font-size: 24px; font-weight: bold; }
        .good { color: #28a745; }
        .warning { color: #ffc107; }
        .bad { color: #dc3545; }
        .file-list { margin-top: 30px; }
        .file-item { background: #f8f9fa; margin: 5px 0; padding: 10px; border-radius: 3px; }
        .coverage-bar { background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }
        .coverage-fill { height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Coverage Report</h1>
        <p>Generated: ${DateTime.now().toIso8601String()}</p>
        <p>Total Files: ${coverage.files.length}</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Line Coverage</h3>
            <div class="value ${_getColorClass(overallStats.linePercentage)}">${overallStats.linePercentage.toStringAsFixed(1)}%</div>
            <p>${overallStats.linesHit} / ${overallStats.linesFound} lines</p>
        </div>
        <div class="metric">
            <h3>Function Coverage</h3>
            <div class="value ${_getColorClass(overallStats.functionPercentage)}">${overallStats.functionPercentage.toStringAsFixed(1)}%</div>
            <p>${overallStats.functionsHit} / ${overallStats.functionsFound} functions</p>
        </div>
        <div class="metric">
            <h3>Branch Coverage</h3>
            <div class="value ${_getColorClass(overallStats.branchPercentage)}">${overallStats.branchPercentage.toStringAsFixed(1)}%</div>
            <p>${overallStats.branchesHit} / ${overallStats.branchesFound} branches</p>
        </div>
    </div>

    <div class="file-list">
        <h2>File Coverage Details</h2>
        ${coverage.files.map((file) => _buildFileHtml(file)).join('\n')}
    </div>
</body>
</html>
''';
  }

  /// Build file coverage HTML
  static String _buildFileHtml(FileCoverageInfo file) {
    final linePercentage = file.linePercentage;
    return '''
<div class="file-item">
    <h4>${file.filePath}</h4>
    <div class="coverage-bar">
        <div class="coverage-fill" style="width: $linePercentage%"></div>
    </div>
    <p>Lines: ${linePercentage.toStringAsFixed(1)}% (${file.linesHit}/${file.linesFound})</p>
</div>
''';
  }

  /// Get CSS class for coverage percentage
  static String _getColorClass(double percentage) {
    if (percentage >= 90) return 'good';
    if (percentage >= 70) return 'warning';
    return 'bad';
  }

  /// Build summary report content
  static String _buildSummaryReport(CoverageReport coverage) {
    final stats = coverage.overallStatistics;
    final buffer = StringBuffer();

    buffer.writeln('MALARIA PREDICTION APP - TEST COVERAGE SUMMARY');
    buffer.writeln('=' * 50);
    buffer.writeln('Generated: ${DateTime.now().toIso8601String()}');
    buffer.writeln();

    buffer.writeln('OVERALL COVERAGE:');
    buffer.writeln('  Lines:     ${stats.linePercentage.toStringAsFixed(2)}% (${stats.linesHit}/${stats.linesFound})');
    buffer.writeln('  Functions: ${stats.functionPercentage.toStringAsFixed(2)}% (${stats.functionsHit}/${stats.functionsFound})');
    buffer.writeln('  Branches:  ${stats.branchPercentage.toStringAsFixed(2)}% (${stats.branchesHit}/${stats.branchesFound})');
    buffer.writeln();

    buffer.writeln('THRESHOLD VALIDATION:');
    final validation = _validateThresholds(coverage);
    for (final entry in validation.entries) {
      final status = entry.value['passed'] ? 'PASS' : 'FAIL';
      buffer.writeln('  ${entry.key}: $status (${entry.value['actual']}% >= ${entry.value['threshold']}%)');
    }
    buffer.writeln();

    buffer.writeln('FILES WITH LOW COVERAGE (<80%):');
    final lowCoverageFiles = coverage.files
        .where((file) => file.linePercentage < 80.0)
        .toList()
      ..sort((a, b) => a.linePercentage.compareTo(b.linePercentage));

    if (lowCoverageFiles.isEmpty) {
      buffer.writeln('  None - All files meet minimum coverage requirements!');
    } else {
      for (final file in lowCoverageFiles) {
        buffer.writeln('  ${file.filePath}: ${file.linePercentage.toStringAsFixed(1)}%');
      }
    }

    return buffer.toString();
  }

  /// Validate coverage against thresholds
  static Map<String, Map<String, dynamic>> _validateThresholds(CoverageReport coverage) {
    final stats = coverage.overallStatistics;
    final results = <String, Map<String, dynamic>>{};

    // Global threshold
    results['global'] = {
      'threshold': coverageThresholds['global']!,
      'actual': stats.linePercentage,
      'passed': stats.linePercentage >= coverageThresholds['global']!,
    };

    // Component-specific thresholds (would require file categorization)
    // This is simplified - in a real implementation, you'd categorize files
    // by their path patterns to determine which threshold applies

    return results;
  }

  /// Run coverage analysis and validation
  static Future<CoverageValidationResult> validateCoverage({
    String coverageFile = 'coverage/lcov.info',
    bool exitOnFailure = false,
  }) async {
    try {
      final coverage = await analyzeCoverage(coverageFile: coverageFile);
      final validation = _validateThresholds(coverage);

      final allPassed = validation.values.every((result) => result['passed'] as bool);
      final result = CoverageValidationResult(
        passed: allPassed,
        coverage: coverage,
        validation: validation,
      );

      if (!allPassed && exitOnFailure) {
        print('Coverage validation failed!');
        for (final entry in validation.entries) {
          if (!(entry.value['passed'] as bool)) {
            print('  ${entry.key}: ${entry.value['actual']}% < ${entry.value['threshold']}%');
          }
        }
        exit(1);
      }

      return result;
    } catch (e) {
      throw Exception('Coverage validation failed: $e');
    }
  }
}

/// Coverage report data structures
class CoverageReport {
  final List<FileCoverageInfo> files;

  CoverageReport({required this.files});

  CoverageStatistics get overallStatistics {
    int totalLinesFound = 0;
    int totalLinesHit = 0;
    int totalFunctionsFound = 0;
    int totalFunctionsHit = 0;
    int totalBranchesFound = 0;
    int totalBranchesHit = 0;

    for (final file in files) {
      totalLinesFound += file.linesFound;
      totalLinesHit += file.linesHit;
      totalFunctionsFound += file.functionsFound;
      totalFunctionsHit += file.functionsHit;
      totalBranchesFound += file.branchesFound;
      totalBranchesHit += file.branchesHit;
    }

    return CoverageStatistics(
      linesFound: totalLinesFound,
      linesHit: totalLinesHit,
      functionsFound: totalFunctionsFound,
      functionsHit: totalFunctionsHit,
      branchesFound: totalBranchesFound,
      branchesHit: totalBranchesHit,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'generated_at': DateTime.now().toIso8601String(),
      'overall_statistics': overallStatistics.toJson(),
      'files': files.map((f) => f.toJson()).toList(),
      'total_files': files.length,
    };
  }
}

class FileCoverageInfo {
  final String filePath;
  int linesFound = 0;
  int linesHit = 0;
  int functionsFound = 0;
  int functionsHit = 0;
  int branchesFound = 0;
  int branchesHit = 0;

  FileCoverageInfo({required this.filePath});

  double get linePercentage =>
      linesFound > 0 ? (linesHit / linesFound) * 100 : 0.0;

  double get functionPercentage =>
      functionsFound > 0 ? (functionsHit / functionsFound) * 100 : 0.0;

  double get branchPercentage =>
      branchesFound > 0 ? (branchesHit / branchesFound) * 100 : 0.0;

  Map<String, dynamic> toJson() {
    return {
      'file_path': filePath,
      'lines': {
        'found': linesFound,
        'hit': linesHit,
        'percentage': linePercentage,
      },
      'functions': {
        'found': functionsFound,
        'hit': functionsHit,
        'percentage': functionPercentage,
      },
      'branches': {
        'found': branchesFound,
        'hit': branchesHit,
        'percentage': branchPercentage,
      },
    };
  }
}

class CoverageStatistics {
  final int linesFound;
  final int linesHit;
  final int functionsFound;
  final int functionsHit;
  final int branchesFound;
  final int branchesHit;

  CoverageStatistics({
    required this.linesFound,
    required this.linesHit,
    required this.functionsFound,
    required this.functionsHit,
    required this.branchesFound,
    required this.branchesHit,
  });

  double get linePercentage =>
      linesFound > 0 ? (linesHit / linesFound) * 100 : 0.0;

  double get functionPercentage =>
      functionsFound > 0 ? (functionsHit / functionsFound) * 100 : 0.0;

  double get branchPercentage =>
      branchesFound > 0 ? (branchesHit / branchesFound) * 100 : 0.0;

  Map<String, dynamic> toJson() {
    return {
      'lines': {
        'found': linesFound,
        'hit': linesHit,
        'percentage': linePercentage,
      },
      'functions': {
        'found': functionsFound,
        'hit': functionsHit,
        'percentage': functionPercentage,
      },
      'branches': {
        'found': branchesFound,
        'hit': branchesHit,
        'percentage': branchPercentage,
      },
    };
  }
}

class CoverageValidationResult {
  final bool passed;
  final CoverageReport coverage;
  final Map<String, Map<String, dynamic>> validation;

  CoverageValidationResult({
    required this.passed,
    required this.coverage,
    required this.validation,
  });
}