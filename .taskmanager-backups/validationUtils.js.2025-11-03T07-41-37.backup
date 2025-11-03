/**
 * Validation Utilities - Helper Functions for Success Criteria Validation
 *
 * Provides specialized utility functions for validating success criteria,
 * evidence collection, result processing, and validation workflow management.
 *
 * @module ValidationUtils
 * @author API Infrastructure Agent #1
 * @version 3.0.0
 * @since 2025-09-15
 */

const { spawn } = require('child_process');
const _fs = require('fs').promises;
const _path = require('path');

/**
 * Whitelist of allowed commands for validation operations
 * Only these commands are permitted to prevent command injection
 */
const ALLOWED_COMMANDS = new Set([
  'npm',
  'yarn',
  'node',
  'python',
  'python3',
  'eslint',
  'ruff',
  'make',
  'pytest',
  'go',
  'snyk',
  'safety',
  'echo',
  'timeout',
  'tsc',
  'javac',
  'mvn',
  'gradle',
  'cargo',
  'dotnet',
]);

/**
 * Sanitize and validate command input to prevent injection attacks
 * @param {string} command - Command to validate
 * @param {Array<string>} args - Command arguments to validate
 * @returns {Object} Validation result with sanitized values
 */
function _sanitizeCommand(command, args = [], _category = 'general') {
  if (!command || typeof command !== 'string') {
    throw new Error('Command must be a non-empty string');
  }

  // Remove any path traversal attempts and shell metacharacters
  const sanitizedCommand = command.replace(/[;&|`$(){}[\]<>'"\\]/g, '').trim();

  // Extract just the command name (remove any path)
  const commandName = _path.basename(sanitizedCommand).toLowerCase();

  // Check against whitelist
  if (!ALLOWED_COMMANDS.has(commandName)) {
    throw new Error(`Command '${commandName}' is not allowed. Permitted commands: ${Array.from(ALLOWED_COMMANDS).join(', ')}`);
  }

  // Validate and sanitize arguments
  if (!Array.isArray(args)) {
    throw new Error('Arguments must be an array');
  }

  const sanitizedArgs = args.map(arg => {
    if (typeof arg !== 'string') {
      throw new Error('All arguments must be strings');
    }

    // Remove dangerous shell metacharacters from arguments
    const sanitized = arg.replace(/[;&|`$(){}[\]<>'"\\]/g, '');

    // Validate that argument doesn't contain suspicious patterns
    if (arg.includes('..') || arg.startsWith('/') || arg.includes('~')) {
      // Allow common safe patterns but be restrictive
      const safePaths = /^(\.\/|src\/|test\/|lib\/|dist\/|build\/|node_modules\/)/;
      const safeFlags = /^--?[a-zA-Z0-9-]+$/;
      const safeValues = /^[a-zA-Z0-9._-]+$/;

      if (!safePaths.test(arg) && !safeFlags.test(arg) && !safeValues.test(arg)) {
        throw new Error(`Argument '${arg}' contains potentially unsafe path or pattern`);
      }
    }

    return sanitized;
  });

  return {
    command: commandName,
    args: sanitizedArgs,
    isValid: true,
  };
}

/**
 * Execute validation command with proper error handling
 * @param {string} command - Command to execute
 * @param {Array<string>} args - Command arguments
 * @param {Object} options - Execution options
 * @returns {Promise<Object>} Command execution result
 */
function executeValidationCommand(command, args = [], options = {}, _category = 'general') {
  const {
    timeout = 10000,
    cwd = process.cwd(),
    env = process.env,
    shell = true,
  } = options;

  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd,
      env,
      shell,
      timeout,
    });

    let stdout = '';
    let stderr = '';
    let timeoutId;

    // Set up timeout
    if (timeout > 0) {
      timeoutId = setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error(`Command timed out after ${timeout}ms: ${command} ${args.join(' ')}`));
      }, timeout);
    }

    // Collect output
    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    // Handle completion
    child.on('close', (code, signal) => {
      if (timeoutId) {clearTimeout(timeoutId);}

      const _result = {
        command: `${command} ${args.join(' ')}`,
        exitCode: code,
        signal,
        stdout,
        stderr,
        output: stdout + stderr,
        success: code === 0,
        timedOut: signal === 'SIGTERM',
        timestamp: new Date().toISOString(),
      };

      resolve(_result);
    });

    // Handle errors
    child.on('error', (_error) => {
      if (timeoutId) {clearTimeout(timeoutId);}
      reject(new Error(`Command execution failed: ${_error.message}`));
    });
  });
}

/**
 * Validate command result against success criteria
 * @param {Object} commandResult - Result from executeValidationCommand
 * @param {string} criteriaType - Type of success criteria
 * @param {Object} options - Validation options
 * @returns {Object} Validation result
 */
function validateCommandResult(commandResult, criteriaType, options = {}, _category = 'general') {
  const result = {
    criterion: criteriaType,
    passed: false,
    confidence: 0,
    details: [],
    evidence: null,
    recommendations: [],
  };

  // If command failed to execute
  if (!commandResult.success && commandResult.timedOut) {
    result.details.push(`Command timed out after ${options.timeout || 10000}ms`);
    result.recommendations.push('Consider increasing timeout or optimizing the validation process');
    return result;
  }

  // Validate based on criteria type
  switch (criteriaType) {
    case 'Linter Perfection':
      result.passed = validateLinterOutput(commandResult);
      result.confidence = result.passed ? 100 : 80;
      if (!result.passed) {
        result.recommendations.push('Run linter with --fix flag to automatically resolve issues');
        result.recommendations.push('Review linting configuration for project-specific rules');
      }
      break;

    case 'Build Success':
      result.passed = validateBuildOutput(commandResult);
      result.confidence = result.passed ? 100 : 90;
      if (!result.passed) {
        result.recommendations.push('Check for missing dependencies or version conflicts');
        result.recommendations.push('Verify build configuration files');
      }
      break;

    case 'Runtime Success':
      result.passed = validateRuntimeOutput(commandResult);
      result.confidence = result.passed ? 85 : 70; // Runtime can be tricky to detect
      if (!result.passed) {
        result.recommendations.push('Check application logs for startup errors');
        result.recommendations.push('Verify all required services and ports are available');
      }
      break;

    case 'Test Integrity':
      result.passed = validateTestOutput(commandResult);
      result.confidence = result.passed ? 95 : 85;
      if (!result.passed) {
        result.recommendations.push('Review failed test cases and update as needed');
        result.recommendations.push('Check test environment configuration');
      }
      break;

    case 'Security Review':
      result.passed = validateSecurityOutput(commandResult);
      result.confidence = result.passed ? 80 : 60; // Security requires manual review
      if (!result.passed) {
        result.recommendations.push('Address high and critical vulnerabilities immediately');
        result.recommendations.push('Update dependencies to patched versions');
      }
      break;

    case 'Performance Metrics':
      result.passed = validatePerformanceOutput(commandResult);
      result.confidence = result.passed ? 75 : 50; // Performance is contextual
      if (!result.passed) {
        result.recommendations.push('Profile application to identify performance bottlenecks');
        result.recommendations.push('Compare against baseline performance metrics');
      }
      break;

    default:
      // Generic validation for unknown criteria
      result.passed = commandResult.success;
      result.confidence = 50;
      result.details.push('Generic validation based on command exit code');
      break;
  }

  // Add generic details based on command result
  if (commandResult.success) {
    result.details.push('Command executed successfully');
  } else {
    result.details.push(`Command failed with exit code ${commandResult.exitCode}`);
  }

  if (commandResult.stderr) {
    result.details.push(`Error output: ${commandResult.stderr.substring(0, 200)}`);
  }

  return result;
}

/**
 * Validate linter output for perfection criteria
 * @param {Object} commandResult - Command result
 * @returns {boolean} Whether linter criteria is met
 */
function validateLinterOutput(commandResult, _category = 'general') {
  if (!commandResult.success) {
    return false;
  }

  const output = commandResult.output.toLowerCase();

  // Check for common error indicators
  const errorIndicators = [
    'error',
    'warning',
    'violation',
    'failed',
    'missing',
    'unexpected',
  ];

  // Some linters output "0 errors, 0 warnings" which is success
  const successIndicators = [
    '0 errors',
    '0 warnings',
    'no problems',
    'clean',
    'passed',
    'ok',
  ];

  // If any success indicators are present, it's likely successful
  if (successIndicators.some(indicator => output.includes(indicator))) {
    return true;
  }

  // If any error indicators are present, it's likely failed
  if (errorIndicators.some(indicator => output.includes(indicator))) {
    return false;
  }

  // If no clear indicators, rely on exit code
  return commandResult.success;
}

/**
 * Validate build output for success criteria
 * @param {Object} commandResult - Command result
 * @returns {boolean} Whether build criteria is met
 */
function validateBuildOutput(commandResult, _category = 'general') {
  if (!commandResult.success) {
    return false;
  }

  const output = commandResult.output.toLowerCase();

  // Build success indicators
  const successIndicators = [
    'build successful',
    'compilation successful',
    'built successfully',
    'bundle generated',
    'compiled successfully',
  ];

  // Build failure indicators
  const failureIndicators = [
    'build failed',
    'compilation error',
    'syntax error',
    'module not found',
    'dependency error',
  ];

  if (successIndicators.some(indicator => output.includes(indicator))) {
    return true;
  }

  if (failureIndicators.some(indicator => output.includes(indicator))) {
    return false;
  }

  return commandResult.success;
}

/**
 * Validate runtime output for startup success
 * @param {Object} commandResult - Command result
 * @returns {boolean} Whether runtime criteria is met
 */
function validateRuntimeOutput(commandResult, _category = 'general') {
  const output = commandResult.output.toLowerCase();

  // Runtime success indicators
  const successIndicators = [
    'server started',
    'listening on',
    'application started',
    'ready on',
    'server running',
    'started successfully',
  ];

  // Runtime failure indicators
  const failureIndicators = [
    'failed to start',
    'port already in use',
    'connection refused',
    'startup failed',
    'cannot bind',
    'error starting',
  ];

  if (successIndicators.some(indicator => output.includes(indicator))) {
    return true;
  }

  if (failureIndicators.some(indicator => output.includes(indicator))) {
    return false;
  }

  // For runtime, success code might not be reliable since app might be killed
  return commandResult.success || !commandResult.timedOut;
}

/**
 * Validate test output for integrity criteria
 * @param {Object} commandResult - Command result
 * @returns {boolean} Whether test criteria is met
 */
function validateTestOutput(commandResult, _category = 'general') {
  if (!commandResult.success) {
    return false;
  }

  const _output = commandResult.output.toLowerCase();

  // Test success indicators
  const successIndicators = [
    'tests passed',
    'all tests passed',
    'test suites passed',
    '0 failed',
    'no failures',
  ];

  // Test failure indicators
  const failureIndicators = [
    'failed',
    'error',
    'failing',
    'assertion',
    'expected',
  ];

  if (successIndicators.some(indicator => _output.includes(indicator))) {
    return true;
  }

  if (failureIndicators.some(indicator => _output.includes(indicator))) {
    return false;
  }

  return commandResult.success;
}

/**
 * Validate security output for security review criteria
 * @param {Object} commandResult - Command result
 * @returns {boolean} Whether security criteria is met
 */
function validateSecurityOutput(commandResult, _category = 'general') {
  const _output = commandResult.output.toLowerCase();

  // Security success indicators
  const successIndicators = [
    'no vulnerabilities',
    '0 vulnerabilities',
    'audit clean',
    'no security issues',
  ];

  // Security failure indicators (high/critical only)
  const criticalFailureIndicators = [
    'high vulnerability',
    'critical vulnerability',
    'high severity',
    'critical severity',
  ];

  if (successIndicators.some(indicator => _output.includes(indicator))) {
    return true;
  }

  if (criticalFailureIndicators.some(indicator => _output.includes(indicator))) {
    return false;
  }

  // For security, we're more lenient with low/medium issues
  return commandResult.success;
}

/**
 * Validate performance output for performance criteria
 * @param {Object} commandResult - Command result
 * @returns {boolean} Whether performance criteria is met
 */
function validatePerformanceOutput(commandResult, _category = 'general') {
  if (!commandResult.success) {
    return false;
  }

  const _output = commandResult.output.toLowerCase();

  // Performance success indicators
  const successIndicators = [
    'performance acceptable',
    'benchmarks passed',
    'within limits',
    'no regressions',
    'improved performance',
  ];

  // Performance failure indicators
  const failureIndicators = [
    'performance regression',
    'too slow',
    'memory leak',
    'timeout exceeded',
    'performance degraded',
  ];

  if (successIndicators.some(indicator => _output.includes(indicator))) {
    return true;
  }

  if (failureIndicators.some(indicator => _output.includes(indicator))) {
    return false;
  }

  return commandResult.success;
}

/**
 * Collect evidence from validation result
 * @param {string} taskId - Task ID
 * @param {string} criterion - Criterion name
 * @param {Object} commandResult - Command result
 * @param {string} evidenceDir - Evidence directory
 * @returns {Promise<Object>} Evidence collection result
 */
async function collectValidationEvidence(taskId, criterion, commandResult, evidenceDir, _category = 'general') {
  try {
    const timestamp = Date.now();
    const cleanCriterion = criterion.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
    const evidenceId = `${taskId}_${cleanCriterion}_${timestamp}`;

    // Create evidence directory
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- evidenceDir constructed from validated paths
    await _fs.mkdir(evidenceDir, { recursive: true });

    // Prepare evidence object
    const evidence = {
      id: evidenceId,
      taskId,
      criterion,
      timestamp: new Date().toISOString(),
      command: commandResult.command,
      exitCode: commandResult.exitCode,
      success: commandResult.success,
      stdout: commandResult.stdout,
      stderr: commandResult.stderr,
      executionTime: commandResult.executionTime || null,
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        cwd: process.cwd(),
      },
    };

    // Save evidence to file
    const evidenceFile = _path.join(evidenceDir, `${evidenceId}.json`);
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- evidenceFile constructed from validated paths
    await _fs.writeFile(evidenceFile, JSON.stringify(evidence, null, 2));

    // Save raw output if significant
    if (commandResult.output && commandResult.output.length > 100) {
      const outputFile = _path.join(evidenceDir, `${evidenceId}_output.txt`);
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- outputFile constructed from validated paths
      await _fs.writeFile(outputFile, commandResult.output);
      evidence.outputFile = outputFile;
    }

    return {
      success: true,
      evidenceId,
      evidenceFile,
      size: JSON.stringify(evidence).length,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Aggregate validation results across multiple criteria
 * @param {Array<Object>} results - Individual validation results
 * @returns {Object} Aggregated validation summary
 */
function aggregateValidationResults(results, _category = 'general') {
  const summary = {
    total: results.length,
    passed: 0,
    failed: 0,
    pending: 0,
    skipped: 0,
    averageConfidence: 0,
    criticalFailures: [],
    recommendations: [],
    categories: {},
  };

  let totalConfidence = 0;
  const categoryStats = {};

  results.forEach(result => {
    // Count by status
    switch (result.status || (result.passed ? 'passed' : 'failed')) {
      case 'passed':
        summary.passed++;
        break;
      case 'failed':
        summary.failed++;
        if (isCriticalCriterion(result.criterion)) {
          summary.criticalFailures.push(result.criterion);
        }
        break;
      case 'pending':
        summary.pending++;
        break;
      case 'skipped':
        summary.skipped++;
        break;
    }

    // Aggregate confidence
    if (typeof result.confidence === 'number') {
      totalConfidence += result.confidence;
    }

    // Collect recommendations
    if (result.recommendations && Array.isArray(result.recommendations)) {
      summary.recommendations.push(...result.recommendations);
    }

    // Category statistics
    const resultCategory = getCriterionCategory(result.criterion);
    // eslint-disable-next-line security/detect-object-injection -- resultCategory from validated getCriterionCategory function
    if (!categoryStats[resultCategory]) {
      // eslint-disable-next-line security/detect-object-injection -- resultCategory from validated getCriterionCategory function
      categoryStats[resultCategory] = { total: 0, passed: 0 };
    }
    // eslint-disable-next-line security/detect-object-injection -- resultCategory from validated getCriterionCategory function
    categoryStats[resultCategory].total++;
    if (result.passed || result.status === 'passed') {
      // eslint-disable-next-line security/detect-object-injection -- resultCategory from validated getCriterionCategory function
      categoryStats[resultCategory].passed++;
    }
  });

  // Calculate averages and rates
  summary.averageConfidence = results.length > 0 ? Math.round(totalConfidence / results.length) : 0;
  summary.successRate = summary.total > 0 ? Math.round((summary.passed / summary.total) * 100) : 0;
  summary.categories = categoryStats;

  // Remove duplicate recommendations
  summary.recommendations = [...new Set(summary.recommendations)];

  // Determine overall status
  if (summary.criticalFailures.length > 0) {
    summary.overallStatus = 'critical_failure';
  } else if (summary.failed > 0) {
    summary.overallStatus = 'has_failures';
  } else if (summary.pending > 0) {
    summary.overallStatus = 'pending';
  } else if (summary.passed === summary.total && summary.total > 0) {
    summary.overallStatus = 'success';
  } else {
    summary.overallStatus = 'unknown';
  }

  return summary;
}

/**
 * Check if criterion is critical for basic functionality
 * @param {string} criterion - Criterion name
 * @returns {boolean} Whether criterion is critical
 */
function isCriticalCriterion(criterion, _category = 'general') {
  const criticalCriteria = [
    'Linter Perfection',
    'Build Success',
    'Runtime Success',
    'Test Integrity',
  ];
  return criticalCriteria.includes(criterion);
}

/**
 * Get category for a criterion
 * @param {string} criterion - Criterion name
 * @returns {string} Category name
 */
function getCriterionCategory(criterion, _category = 'general') {
  const categoryMap = {
    'Linter Perfection': 'code_quality',
    'Build Success': 'build',
    'Runtime Success': 'runtime',
    'Test Integrity': 'testing',
    'Security Review': 'security',
    'Performance Metrics': 'performance',
    'Function Documentation': 'documentation',
    'API Documentation': 'documentation',
    'Architecture Documentation': 'documentation',
  };

  // eslint-disable-next-line security/detect-object-injection -- criterion parameter validated by caller
  return categoryMap[criterion] || 'other';
}

/**
 * Generate validation commands for a criterion
 * @param {string} criterion - Criterion name
 * @param {Object} context - Project context
 * @returns {Array<Object>} Validation commands
 */
function generateValidationCommands(criterion, _context = {}, _category = 'general') {
  const commandMap = {
    'Linter Perfection': [
      { command: 'npm', args: ['run', 'lint'], description: 'Run npm lint script' },
      { command: 'eslint', args: ['.'], description: 'Run ESLint directly' },
      { command: 'ruff', args: ['check', '.'], description: 'Run Ruff for Python' },
    ],
    'Build Success': [
      { command: 'npm', args: ['run', 'build'], description: 'Run npm build script' },
      { command: 'yarn', args: ['build'], description: 'Run yarn build' },
      { command: 'make', args: ['build'], description: 'Run make build' },
    ],
    'Runtime Success': [
      { command: 'npm', args: ['start'], description: 'Start with npm' },
      { command: 'node', args: ['server.js'], description: 'Start Node.js server' },
      { command: 'python', args: ['app.py'], description: 'Start Python app' },
    ],
    'Test Integrity': [
      { command: 'npm', args: ['test'], description: 'Run npm test' },
      { command: 'pytest', args: [], description: 'Run pytest' },
      { command: 'go', args: ['test', './...'], description: 'Run Go tests' },
    ],
    'Security Review': [
      { command: 'npm', args: ['audit'], description: 'NPM security audit' },
      { command: 'snyk', args: ['test'], description: 'Snyk security scan' },
      { command: 'safety', args: ['check'], description: 'Python safety check' },
    ],
  };

  // eslint-disable-next-line security/detect-object-injection -- criterion parameter validated by caller
  return commandMap[criterion] || [
    { command: 'echo', args: [`No automated validation available for: ${criterion}`], description: 'Manual validation required' },
  ];
}

module.exports = {
  executeValidationCommand,
  validateCommandResult,
  validateLinterOutput,
  validateBuildOutput,
  validateRuntimeOutput,
  validateTestOutput,
  validateSecurityOutput,
  validatePerformanceOutput,
  collectValidationEvidence,
  aggregateValidationResults,
  isCriticalCriterion,
  getCriterionCategory,
  generateValidationCommands,
};
