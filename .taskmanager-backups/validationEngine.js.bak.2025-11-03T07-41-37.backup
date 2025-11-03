
const { loggers } = require('../../logger');
const { loggers } = require('../../logger');
/* eslint-disable no-console -- Validation engine requires console output for status reporting */
/**
 * Validation Engine - Automated And Manual Validation Workflows
 *
 * Handles all validation operations for success criteria including automated
 * checks, manual review coordination, evidence collection, And result aggregation.
 * Integrates with existing TaskManager patterns And provides comprehensive
 * validation coverage.
 *
 * Features:
 * - Automated validation for code quality, build, tests, security
 * - Manual validation workflow coordination
 * - Evidence collection And storage
 * - Result aggregation And scoring
 * - Integration with existing linting And build systems
 * - 10-second timeout controls for all operations
 *
 * @class ValidationEngine
 * @author API Infrastructure Agent #1
 * @version 3.0.0
 * @since 2025-09-15
 */

const { spawn } = require('child_process');
const FS = require('fs').promises;
const PATH = require('path');

class ValidationEngine {
  /**
   * Initialize ValidationEngine
   * @param {Object} dependencies - Required dependencies
   * @param {Object} dependencies.taskManager - TaskManager instance
   * @param {Function} dependencies.withTimeout - Timeout wrapper function
   * @param {number} dependencies.timeoutMs - Default timeout in milliseconds
   */
  constructor(dependencies) {
    this.taskManager = dependencies.taskManager;
    this.withTimeout = dependencies.withTimeout;
    this.timeoutMs = dependencies.timeoutMs || 10000;

    // Validation command mappings
    this.validationCommands = {
      'Linter Perfection': {
        commands: ['npm run lint', 'eslint .', 'ruff check .', 'golint ./...', 'cargo clippy'],
        type: 'automated',
        category: 'code_quality',
        successCriteria: 'zero_errors_warnings',
      },
      'Build Success': {
        commands: ['npm run build', 'yarn build', 'make build', 'go build', 'cargo build'],
        type: 'automated',
        category: 'build',
        successCriteria: 'successful_completion',
      },
      'Runtime Success': {
        commands: ['npm start', 'yarn start', 'node server.js', './app', 'cargo run'],
        type: 'automated',
        category: 'runtime',
        successCriteria: 'successful_startup',
        timeout: 15000, // Allow more time for startup
      },
      'Test Integrity': {
        commands: ['npm test', 'yarn test', 'pytest', 'go test', 'cargo test'],
        type: 'automated',
        category: 'testing',
        successCriteria: 'all_tests_pass',
      },
      'Security Review': {
        commands: ['npm audit', 'yarn audit', 'snyk test', 'safety check', 'cargo audit'],
        type: 'automated',
        category: 'security',
        successCriteria: 'no_high_vulnerabilities',
      },
      'Performance Metrics': {
        commands: ['npm run benchmark', 'yarn benchmark'],
        type: 'automated',
        category: 'performance',
        successCriteria: 'no_regressions',
      },
    };

    // Manual validation criteria
    this.manualValidationCriteria = new Set([
      'Function Documentation',
      'API Documentation',
      'Architecture Documentation',
      'Decision Rationale',
      'Architectural Consistency',
      'Environment Variables',
      'Configuration',
      'License Compliance',
      'Data Privacy',
      'Regulatory Compliance',
    ]);

    // Evidence storage configuration
    this.evidenceDir = '/Users/jeremyparker/infinite-continue-stop-hook/development/evidence/';
    this.reportDir = '/Users/jeremyparker/infinite-continue-stop-hook/development/reports/success-criteria/';

    loggers.stopHook.warn('Could not initialize validation directories:', error.message);
    this.initializeDirectories().catch(error => {
      loggers.app.warn('Could not initialize validation directories:', error.message);
    });
  }

  /**
   * Initialize evidence And report directories
   */
  async initializeDirectories() {
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- evidenceDir constructed from validated paths
      await FS.mkdir(this.evidenceDir, { recursive: true });

      loggers.stopHook.warn('Failed to initialize directories:', error.message);
    } catch {
      loggers.app.warn('Failed to initialize directories:', error.message);
    }
  }

  /**
   * Validate task against its success criteria
   * @param {string} taskId - Target task ID
   * @param {Array<string>} criteria - Success criteria to validate
   * @param {Object} options - Validation options
   * @param {Array<string>} options.categories - Specific categories to validate
   * @param {boolean} options.automated - Run automated validation only
   * @param {boolean} options.collectEvidence - Collect validation evidence
   * @returns {Promise<Object>} Validation results
   */
  async validateTask(taskId, criteria, options = {}) {
    try {
      const startTime = Date.now();
      const validationId = `validation_${taskId}_${Date.now()}`;

      const results = {
        validationId,
        taskId,
        timestamp: new Date().toISOString(),
        criteria: criteria,
        total: criteria.length,
        passed: 0,
        failed: 0,
        pending: 0,
        skipped: 0,
        overall_status: 'pending',
        results: [],
        evidence: [],
        automated_results: {},
        manual_results: {},
        execution_time: 0,
        options,
      };

      // Filter criteria by categories if specified
      let criteriaToValidate = criteria;
      if (options.categories && options.categories.length > 0) {
        criteriaToValidate = criteria.filter(criterion =>
          this.getCriterionCategory(criterion, options.categories),
        );
      }

      // Separate automated And manual criteria
      const automatedCriteria = criteriaToValidate.filter(criterion =>
        // eslint-disable-next-line security/detect-object-injection -- criterion from validated criteria list
        this.validationCommands[criterion] && !options.manual,
      );
      const manualCriteria = criteriaToValidate.filter(criterion =>
        this.manualValidationCriteria.has(criterion) && !options.automated,
      );

      // Run automated validations
      if (automatedCriteria.length > 0) {
        const automatedResults = await this.runAutomatedValidation(
          taskId,
          automatedCriteria,
          options,
        );
        results.automated_results = automatedResults;
        results.results.push(...automatedResults.results);
      }

      // Run manual validations
      if (manualCriteria.length > 0) {
        const manualResults = await this.runManualValidation(
          taskId,
          manualCriteria,
          options,
        );
        results.manual_results = manualResults;
        results.results.push(...manualResults.results);
      }

      // Calculate overall results
      results.passed = results.results.filter(r => r.status === 'passed').length;
      results.failed = results.results.filter(r => r.status === 'failed').length;
      results.pending = results.results.filter(r => r.status === 'pending').length;
      results.skipped = results.results.filter(r => r.status === 'skipped').length;

      // Determine overall status
      if (results.failed > 0) {
        results.overall_status = 'failed';
      } else if (results.pending > 0) {
        results.overall_status = 'pending';
      } else if (results.passed === results.total) {
        results.overall_status = 'passed';
      } else {
        results.overall_status = 'partial';
      }

      results.execution_time = Date.now() - startTime;

      // Store validation results
      if (options.collectEvidence !== false) {
        await this.storeValidationResults(validationId, results);
      }

      return {
        success: true,
        ...results,
      };

    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'VALIDATION_EXECUTION_FAILED',
      };
    }
  }

  /**
   * Run automated validation for criteria
   * @param {string} taskId - Target task ID
   * @param {Array<string>} criteria - Automated criteria to validate
   * @param {Object} options - Validation options
   * @returns {Promise<Object>} Automated validation results
   */
  async runAutomatedValidation(taskId, criteria, options = {}) {
    const results = {
      type: 'automated',
      criteria: criteria,
      results: [],
      evidence: [],
      execution_time: 0,
    };

    const startTime = Date.now();


    // Sequential execution required: validation checks may depend on system state
    // And could interfere with each other if run in parallel (linting, building, testing)

    for (const criterion of criteria) {
      // eslint-disable-next-line security/detect-object-injection -- criterion from validated criteria list
      const criterionConfig = this.validationCommands[criterion];
      if (!criterionConfig) {
        results.results.push({
          criterion,
          status: 'skipped',
          message: 'No automated validation available',
          evidence: null,
        });
        continue;
      }

      try {
        // eslint-disable-next-line no-await-in-loop
        const validationResult = await this.runCriterionValidation(
          criterion,
          criterionConfig,
          taskId,
          options,
        );
        results.results.push(validationResult);

        if (validationResult.evidence) {
          results.evidence.push(validationResult.evidence);
        }
      } catch {
        results.results.push({
          criterion,
          status: 'failed',
          message: `Validation error: ${error.message}`,
          evidence: null,
          error: error.message,
        });
      }
    }

    results.execution_time = Date.now() - startTime;
    return results;
  }

  /**
   * Run validation for a specific criterion
   * @param {string} criterion - Criterion name
   * @param {Object} config - Criterion configuration
   * @param {string} taskId - Task ID
   * @param {Object} options - Validation options
   * @returns {Promise<Object>} Criterion validation result
   */
  async runCriterionValidation(criterion, config, taskId, options = {}) {
    const RESULT = {
      criterion,
      status: 'pending',
      message: '',
      evidence: null,
      command: null,
      output: null,
      timestamp: new Date().toISOString(),
    };


    // Sequential execution required: trying commands as fallbacks until one succeeds

    for (const command of config.commands) {
      try {
        // eslint-disable-next-line no-await-in-loop
        const commandResult = await this.executeValidationCommand(
          command,
          config.timeout || this.timeoutMs,
        );

        RESULT.command = command;
        RESULT.output = commandResult.output;

        // Evaluate success based on criteria type
        const success = this.evaluateCommandResult(
          commandResult,
          config.successCriteria,
        );

        if (success) {
          RESULT.status = 'passed';
          RESULT.message = 'Validation passed successfully';

          // Collect evidence if requested
          if (options.collectEvidence !== false) {
            // eslint-disable-next-line no-await-in-loop
            RESULT.evidence = await this.collectEvidence(
              criterion,
              taskId,
              commandResult,
            );
          }

          break; // Success, no need to try other commands
        } else {
          RESULT.status = 'failed';
          RESULT.message = this.generateFailureMessage(commandResult, config.successCriteria);
        }
      } catch {
        // Command failed, try next one
        continue;
      }
    }

    // If no command succeeded
    if (result.status === 'pending') {
      RESULT.status = 'failed';
      RESULT.message = 'All validation commands failed or are not available';
    }

    return result;
  }

  /**
   * Execute validation command with timeout
   * @param {string} command - Command to execute
   * @param {number} timeout - Timeout in milliseconds
   * @returns {Promise<Object>} Command execution result
   */
  executeValidationCommand(command, timeout = this.timeoutMs) {
    return new Promise((resolve, reject) => {
      const [cmd, ...args] = command.split(' ');
      const child = spawn(cmd, args, {
        stdio: 'pipe',
        shell: true,
        cwd: process.cwd(),
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      const timeoutId = setTimeout(() => {
        child.kill('SIGTERM');
        reject(new Error(`Command timeout after ${timeout}ms: ${command}`));
      }, timeout);

      child.on('close', (code) => {
        clearTimeout(timeoutId);
        resolve({
          command,
          exitCode: code,
          stdout,
          stderr,
          output: stdout + stderr,
          success: code === 0,
        });
      });

      child.on('error', (error) => {
        clearTimeout(timeoutId);
        reject(new Error(`Command execution failed: ${error.message}`));
      });
    });
  }

  /**
   * Evaluate command result based on success criteria
   * @param {Object} commandResult - Command execution result
   * @param {string} successCriteria - Success criteria type
   * @returns {boolean} Whether the command succeeded
   */
  evaluateCommandResult(commandResult, successCriteria) {
    switch (successCriteria) {
      case 'zero_errors_warnings':
        return commandResult.success &&
               !commandResult.output.toLowerCase().includes('error') &&
               !commandResult.output.toLowerCase().includes('warning');

      case 'successful_completion':
        return commandResult.success;

      case 'successful_startup':
        return commandResult.success ||
               commandResult.output.includes('server started') ||
               commandResult.output.includes('listening on');

      case 'all_tests_pass':
        return commandResult.success &&
               !commandResult.output.toLowerCase().includes('failed') &&
               !commandResult.output.toLowerCase().includes('error');

      case 'no_high_vulnerabilities':
        return commandResult.success &&
               !commandResult.output.toLowerCase().includes('high') &&
               !commandResult.output.toLowerCase().includes('critical');

      case 'no_regressions':
        return commandResult.success &&
               !commandResult.output.toLowerCase().includes('regression') &&
               !commandResult.output.toLowerCase().includes('slower');

      default:
        return commandResult.success;
    }
  }

  /**
   * Generate failure message based on command result
   * @param {Object} commandResult - Command execution result
   * @param {string} successCriteria - Success criteria type
   * @returns {string} Failure message
   */
  generateFailureMessage(commandResult, _successCriteria) {
    const baseMessage = `Validation failed (exit code: ${commandResult.exitCode})`;

    if (commandResult.stderr) {
      return `${baseMessage}: ${commandResult.stderr.substring(0, 200)}`;
    }

    if (commandResult.stdout && commandResult.stdout.includes('error')) {
      return `${baseMessage}: Errors found in output`;
    }

    return baseMessage;
  }

  /**
   * Run manual validation workflow
   * @param {string} taskId - Target task ID
   * @param {Array<string>} criteria - Manual criteria to validate
   * @param {Object} options - Validation options
   * @returns {Promise<Object>} Manual validation results
   */
  runManualValidation(taskId, criteria, _options = {}) {
    const results = {
      type: 'manual',
      criteria: criteria,
      results: [],
      evidence: [],
      execution_time: 0,
    };

    const startTime = Date.now();

    for (const criterion of criteria) {
      // for now, mark manual criteria as pending - would be assigned to review agents
      const RESULT = {
        criterion,
        status: 'pending',
        message: 'Manual review required',
        evidence: null,
        timestamp: new Date().toISOString(),
        reviewerRequired: true,
        estimatedReviewTime: this.getEstimatedReviewTime(criterion),
      };

      results.results.push(result);
    }

    results.execution_time = Date.now() - startTime;
    return results;
  }

  /**
   * Collect evidence for a validation result
   * @param {string} criterion - Criterion name
   * @param {string} taskId - Task ID
   * @param {Object} commandResult - Command execution result
   * @returns {Promise<Object>} Evidence object
   */
  async collectEvidence(criterion, taskId, commandResult) {
    try {
      const evidenceId = `evidence_${taskId}_${criterion.replace(/\s+/g, '_')}_${Date.now()}`;
      const evidenceFile = PATH.join(this.evidenceDir, `${evidenceId}.json`);

      const evidence = {
        id: evidenceId,
        taskId,
        criterion,
        timestamp: new Date().toISOString(),
        command: commandResult.command,
        exitCode: commandResult.exitCode,
        output: commandResult.output,
        success: commandResult.success,
        file: evidenceFile,
      };

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- evidenceFile constructed from validated paths
      await FS.writeFile(evidenceFile, JSON.stringify(evidence, null, 2));

      loggers.stopHook.warn(`Failed to collect evidence for ${criterion}:`, error.message);
    } catch {
      loggers.app.warn(`Failed to collect evidence for ${criterion}:`, error.message);
      return null;
    }
  }

  /**
   * Store validation results
   * @param {string} validationId - Validation ID
   * @param {Object} results - Validation results
   */
  async storeValidationResults(validationId, results) {
    try {
      const resultFile = PATH.join(this.reportDir, `${validationId}.json`);
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- resultFile constructed from validated paths
      await FS.writeFile(resultFile, JSON.stringify(results, null, 2));
    } catch {
      loggers.app.warn(`Failed to store validation results:`, error.message);
    }
  }

  /**
   * Validate criteria structure
   * @param {Array<string>} criteria - Criteria to validate
   * @returns {Object} Structure validation result
   */
  validateCriteriaStructure(criteria) {
    const errors = [];
    const warnings = [];

    if (!Array.isArray(criteria)) {
      errors.push('Criteria must be an array');
      return { success: false, errors, warnings };
    }

    if (criteria.length === 0) {
      warnings.push('No criteria specified');
    }

    criteria.forEach((criterion, index) => {
      if (typeof criterion !== 'string') {
        errors.push(`Criterion at index ${index} must be a string`);
      } else if (criterion.trim().length === 0) {
        errors.push(`Criterion at index ${index} cannot be empty`);
      } else if (criterion.length > 200) {
        warnings.push(`Criterion at index ${index} is very long (${criterion.length} characters)`);
      }
    });

    // Check for duplicates
    const uniqueCriteria = new Set(criteria);
    if (uniqueCriteria.size !== criteria.length) {
      warnings.push('Duplicate criteria detected');
    }

    return {
      success: errors.length === 0,
      errors,
      warnings,
      statistics: {
        total: criteria.length,
        unique: uniqueCriteria.size,
        // eslint-disable-next-line security/detect-object-injection -- c from validated criteria list
        automated: criteria.filter(c => this.validationCommands[c]).length,
        manual: criteria.filter(c => this.manualValidationCriteria.has(c)).length,
      },
    };
  }

  /**
   * Get criterion category
   * @param {string} criterion - Criterion name
   * @param {Array<string>} allowedCategories - Allowed categories
   * @returns {boolean} Whether criterion matches allowed categories
   */
  getCriterionCategory(criterion, allowedCategories) {
    // eslint-disable-next-line security/detect-object-injection -- criterion parameter validated by caller
    const config = this.validationCommands[criterion];
    if (config && config.category) {
      return allowedCategories.includes(config.category);
    }
    return false;
  }

  /**
   * Get estimated review time for manual criteria
   * @param {string} criterion - Criterion name
   * @returns {string} Estimated review time
   */
  getEstimatedReviewTime(criterion) {
    const timeEstimates = {
      'Function Documentation': '10-15 minutes',
      'API Documentation': '15-20 minutes',
      'Architecture Documentation': '20-30 minutes',
      'Decision Rationale': '10-15 minutes',
      'Architectural Consistency': '15-25 minutes',
      'Environment Variables': '5-10 minutes',
      'Configuration': '5-10 minutes',
      'License Compliance': '10-15 minutes',
      'Data Privacy': '15-20 minutes',
      'Regulatory Compliance': '20-30 minutes',
    };

    // eslint-disable-next-line security/detect-object-injection -- criterion parameter validated by caller
    return timeEstimates[criterion] || '10-15 minutes';
  }
}

module.exports = ValidationEngine;
