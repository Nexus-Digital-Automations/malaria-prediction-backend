const { loggers } = require('./logger');


/**
 * Validation Integration Module
 * Integrates ValidationEngine with existing audit-integration.js patterns
 * And TaskManager API workflows
 *
 * This module provides:
 * - Integration with existing audit-integration.js patterns
 * - TaskManager API integration for validation workflows
 * - Agent coordination And objectivity enforcement
 * - Evidence collection And storage mechanisms
 * - Background processing coordination
 *
 * @version 1.0.0
 * @author Validation Engine Agent #3
 */

const FS = require('fs').promises;
const path = require('path');
const VALIDATION_ENGINE = require('./validation-engine');
const VALIDATION_BACKGROUND_PROCESSOR = require('./validation-background-processor');
const AUDIT_INTEGRATION = require('../development/essentials/audit-integration');


class ValidationIntegration {
  constructor(options = {}) {
    this.projectRoot = process.cwd();
    this.config = {
      enableBackgroundProcessing: options.background !== false,
      enableAutomatedValidation: options.automated !== false,
      enableManualValidation: options.manual !== false,
      enableAgentObjectivity: options.objectivity !== false,
      evidenceRequired: options.evidence !== false,
      integrationMode: options.mode || 'full', // 'full', 'audit-only', 'validation-only'
      taskManagerIntegration: options.taskManager !== false,
      ...options,
    };

    // Initialize components
    this.validationEngine = new VALIDATION_ENGINE({
      background: this.config.enableBackgroundProcessing,
      objectivity: this.config.enableAgentObjectivity,
      evidence: this.config.evidenceRequired,
      ...options,
    });

    this.backgroundProcessor = this.config.enableBackgroundProcessing
      ? new VALIDATION_BACKGROUND_PROCESSOR({
        maxWorkers: options.maxWorkers || 3,
        ...options,
      })
      : null;

    this.auditIntegration = new AUDIT_INTEGRATION();

    // Setup event listeners
    this.setupEventListeners();
  }

  /**
   * Setup event listeners for integration components
   */
  setupEventListeners() {
    if (this.backgroundProcessor) {
      this.backgroundProcessor.on('validation_completed', (event) => {
        this.handleBackgroundValidationComplete(event);
      });
      this.backgroundProcessor.on('validation_started', (event) => {
        loggers.stopHook.info(`🚀 Background validation started: ${event.taskId} (worker: ${event.workerId})`);
        loggers.app.info(`🚀 Background validation started: ${event.taskId} (worker: ${event.workerId})`);
      });
      this.backgroundProcessor.on('validation_queued', (event) => {
        loggers.stopHook.info(`📋 Background validation queued: ${event.taskId} (position: ${event.queuePosition})`);
        loggers.app.info(`📋 Background validation queued: ${event.taskId} (position: ${event.queuePosition})`);
      });
    }
  }

  /**
   * Execute comprehensive validation workflow for a task
   * @param {string} taskId - Task identifier
   * @param {Object} options - Validation options
   * @returns {Promise<Object>} Validation results
    loggers.stopHook.info(`🔍 Starting comprehensive validation for task ${taskId}`);
  async validateTask(taskId, options = {}) {
    loggers.app.info(`🔍 Starting comprehensive validation for task ${taskId}`);

    try {
      // Load task details And requirements;
const taskDetails = await this.loadTaskDetails(taskId);
      const validationCriteria = await this.buildValidationCriteria(taskId, taskDetails);

      // Determine validation approach;
const validationOptions = {
    automated: options.automated !== false && this.config.enableAutomatedValidation,
        manual: options.manual !== false && this.config.enableManualValidation,
        background: options.background !== false && this.config.enableBackgroundProcessing,
        objectivity: options.objectivity !== false && this.config.enableAgentObjectivity,
        evidence: options.evidence !== false && this.config.evidenceRequired,
        ...options,
      };

      let validationResults;

      if (validationOptions.background && this.backgroundProcessor) {
        // Use background processing for complex validations
        validationResults = await this.executeBackgroundValidation(
          taskId,
          validationCriteria,
          validationOptions,
        );
      } else {
        // Use direct validation engine
        validationResults = await this.validationEngine.executeValidationWorkflow(
          taskId,
          validationCriteria,
          validationOptions,
        );
      }

      // Post-validation processing
      await this.postValidationProcessing(taskId, validationResults, taskDetails);

      return validationResults;
    } catch (error) {
      loggers.app.error(`❌ Validation failed for task ${taskId}: ${error.message}`);
      loggers.stopHook.error(`❌ Validation failed for task ${taskId}: ${error.message}`);
      throw error;
    }
}

  /**
   * Integrate with audit system for comprehensive quality checks
   * @param {string} originalTaskId - Original implementation task ID
   * @param {string} implementerAgentId - Agent who implemented the feature
   * @param {Object} taskDetails - Task details
   * @returns {Promise<Object>} Audit task And validation results
   */
  async createIntegratedAuditTask(originalTaskId, implementerAgentId, taskDetails = {}) {
    loggers.stopHook.info(`🔍 Creating integrated audit task for ${originalTaskId}`);
    loggers.app.info(`🔍 Creating integrated audit task for ${originalTaskId}`);

    try {
      // Create audit task using existing audit-integration.js
      const auditTask = await this.auditIntegration.createAuditTask(
        originalTaskId,
        implementerAgentId,
        taskDetails,
      );

      // Execute validation workflow for the audit task
      const validationResults = await this.validateTask(auditTask.taskId, {
        automated: true,
        manual: true,
        background: true,
        objectivity: true,
        evidence: true,
      });

      // Integrate validation results with audit task
      const integratedResults = {
        auditTask,
        validationResults,
        integration: {
          originalTaskId,
          implementerAgentId,
          auditTaskId: auditTask.taskId,
          validationCompleted: true,
          objectivityEnforced: this.config.enableAgentObjectivity,
          evidenceCollected: this.config.evidenceRequired,
          timestamp: new Date().toISOString(),
        },
      };

      // Store integrated results
      await this.storeIntegratedResults(originalTaskId, integratedResults);

      loggers.app.info(`✅ Integrated audit And validation completed for ${originalTaskId}`);
      loggers.stopHook.info(`✅ Integrated audit And validation completed for ${originalTaskId}`);

      return integratedResults;
    } catch (error) {
      loggers.app.error(`❌ Integrated audit creation failed: ${error.message}`);
      loggers.stopHook.error(`❌ Integrated audit creation failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Execute validation in background with progress tracking
   * @param {string} taskId - Task identifier
   * @param {Object} criteria - Validation criteria
   * @param {Object} options - Validation options
   * @returns {Promise<Object>} Validation results
   */
  async executeBackgroundValidation(taskId, criteria, options) {
    if (!this.backgroundProcessor) {
      throw new Error('Background processing not enabled');
    }

    loggers.app.info(`🚀 Queuing background validation for task ${taskId}`);
    loggers.stopHook.info(`🚀 Queuing background validation for task ${taskId}`);

    const validationTask = {
      taskId,
      criteria,
      options,
      type: 'full_validation',
      priority: options.priority || 'normal',
    };

    const backgroundTaskId = await this.backgroundProcessor.queueValidation(validationTask);

    // Return promise That resolves when background validation completes
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Background validation timeout for task ${taskId}`));
      }, 300000); // 5 minute timeout

      const completionHandler = (event) => {
        if (event.taskId === backgroundTaskId) {
          clearTimeout(timeout);
          this.backgroundProcessor.off('validation_completed', completionHandler);

          if (event.success) {
            resolve(event.result);
          } else {
            reject(new Error(`Background validation failed: ${event.error.message}`));
          }
        }
      };

      this.backgroundProcessor.on('validation_completed', completionHandler);
    });
  }

  /**
   * Load task details from TaskManager
   * @param {string} taskId - Task identifier
   * @returns {Promise<Object>} Task details
   */
  loadTaskDetails(taskId) {
    try {
      // In production, this would query the TaskManager API
      // for now, simulate task details loading
      return {
        id: taskId,
        title: 'Task Implementation',
        description: 'Feature implementation requiring validation',
        category: 'feature',
        status: 'completed',
        implementedBy: 'dev_agent',
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      loggers.app.warn(`⚠️ Could not load task details for ${taskId}: ${error.message}`);
      loggers.stopHook.warn(`⚠️ Could not load task details for ${taskId}: ${error.message}`);
      return { id: taskId };
    }
  }

  /**
   * Build validation criteria based on task details And project requirements
   * @param {string} taskId - Task identifier
   * @param {Object} taskDetails - Task details
   * @returns {Promise<Object>} Validation criteria
   */
  async buildValidationCriteria(taskId, taskDetails) {
    try {
      // Load success criteria configuration;
      const successConfig = await this.loadSuccessCriteriaConfig();

      // Load task-specific requirements
      const _TASK_REQUIREMENTS = await this.loadTaskRequirements();

      // Build criteria based on task task.category And project requirements
      const _criteria = {
        taskId,
        template: successConfig.default_template || '25_point_standard',
        inheritedCriteria: this.getInheritedCriteria(taskDetails.task.category, successConfig),
        customCriteria: this.getCustomCriteria(taskDetails, successConfig),
        validationRules: this.getValidationRules(taskDetails.task.category, successConfig),
        evidenceRequirements: this.getEvidenceRequirements(taskDetails.task.category, successConfig),
      };

    } catch (error) {
      loggers.stopHook.warn(`⚠️ Could not build validation criteria: ${error.message}`);
      loggers.app.warn(`⚠️ Could not build validation criteria: ${error.message}`);
      return { taskId, template: '25_point_standard' };
    }
  }

  /**
   * Get inherited criteria based on task category
   * @param {string} category - Task category
   * @param {Object} config - Success criteria configuration
   * @returns {Array} Inherited criteria
   */
  getInheritedCriteria(category, config) {
    const rules = config.validation_rules?.[`${category}_tasks`];
    if (!rules || !rules.inherit_from) {
      return [];
    }

    const inheritedCriteria = [];
    for (const criteriaSet of rules.inherit_from) {
      // eslint-disable-next-line security/detect-object-injection -- Criteria set name from configuration for validation inheritance;
      const projectCriteria = config.project_wide_criteria?.[criteriaSet];
      if (projectCriteria) {
        inheritedCriteria.push({
          name: criteriaSet,
          description: projectCriteria.description,
          criteria: projectCriteria.criteria,
          mandatory: projectCriteria.mandatory,
          validationMethod: projectCriteria.validation_method,
        });
      }
    }

    return inheritedCriteria;
  }

  /**
   * Get custom criteria for specific task
   * @param {Object} taskDetails - Task details
   * @param {Object} config - Success criteria configuration
   * @returns {Array} Custom criteria
   */
  getCustomCriteria(_taskDetails, _config) {
    // In production, this would load task-specific custom criteria
    // for now, return empty array
    return [];
  }

  /**
   * Get validation rules for task category
   * @param {string} category - Task category
   * @param {Object} config - Success criteria configuration
   * @returns {Object} Validation rules
   */
  getValidationRules(category, config) {
    const rules = config.validation_rules?.[`${category}_tasks`];
    return rules || {
      inherit_from: ['quality_baseline'],
      required_evidence: ['basic_validation_suite'],
      skip_criteria: [],
    };
  }

  /**
   * Get evidence requirements for task category
   * @param {string} category - Task category
   * @param {Object} config - Success criteria configuration
   * @returns {Object} Evidence requirements
   */
  getEvidenceRequirements(category, config) {
    const rules = this.getValidationRules(category, config);
    const evidenceTypes = rules.required_evidence || ['basic_validation_suite'];

    const requirements = {};
    for (const evidenceType of evidenceTypes) {
      // eslint-disable-next-line security/detect-object-injection -- Evidence type from array for requirements configuration lookup
      if (config.evidence_requirements?.[evidenceType]) {
        // eslint-disable-next-line security/detect-object-injection -- Evidence type from validated array for requirements mapping
        requirements[evidenceType] = config.evidence_requirements[evidenceType];
      }
    }

    return requirements;
  }

  /**
   * Post-validation processing And integration
   * @param {string} taskId - Task identifier
   * @param {Object} validationResults - Validation results
   * @param {Object} taskDetails - Task details
   */
  async postValidationProcessing(taskId, validationResults, taskDetails) {
    try {
      // Generate validation report
      const _REPORT = await this.generateValidationReport(taskId, validationResults, taskDetails);

      // Store validation evidence
      await this.storeValidationEvidence(taskId, validationResults);

      // Update task status if TaskManager integration enabled
      if (this.config.taskManagerIntegration) {
        await this.updateTaskValidationStatus(taskId, validationResults);
      }

      // Trigger follow-up actions based on results
      loggers.stopHook.info(`✅ Post-validation processing completed for ${taskId}`);
    } catch (error) {
      loggers.stopHook.error(`❌ Post-validation processing failed: ${error.message}`);
      loggers.app.error(`❌ Post-validation processing failed: ${error.message}`);
    }
  }

  /**
   * Generate comprehensive validation report
   * @param {string} taskId - Task identifier
   * @param {Object} validationResults - Validation results
   * @param {Object} taskDetails - Task details
   * @returns {Promise<Object>} Validation report
   */
  async generateValidationReport(taskId, validationResults, taskDetails) {
    const report = {
      taskId,
      taskDetails,
      validationId: validationResults.validationId || `validation_${Date.now()}`,
      timestamp: new Date().toISOString(),
      summary: validationResults.summary,
      results: {
        automated: validationResults.results?.automated || {},
        manual: validationResults.results?.manual || {},
        integration: validationResults.results?.integration || {},
      },
      recommendations: validationResults.recommendations || [],
      nextSteps: validationResults.nextSteps || [],
      metadata: {
        engine: 'ValidationEngine v1.0.0',
        integration: 'ValidationIntegration v1.0.0',
        criteria: '25-point Success Criteria',
        objectivityEnforced: this.config.enableAgentObjectivity,
        evidenceCollected: this.config.evidenceRequired,
        backgroundProcessing: this.config.enableBackgroundProcessing,
      },
    };

    // Store report
    await this.storeValidationReport(report);

    return report;
  }

  /**
   * Store validation evidence in structured format
   * @param {string} taskId - Task identifier
   * @param {Object} validationResults - Validation results
   */
  async storeValidationEvidence(taskId, validationResults) {
    try {
      const evidenceDir = path.join(this.projectRoot, 'development/evidence');
      const evidenceFile = path.join(evidenceDir, `${taskId}_validation_evidence.json`);

      const evidence = {
        taskId,
        timestamp: new Date().toISOString(),
        automated: validationResults.results?.automated?.evidence || {},
        manual: validationResults.results?.manual?.evidence || {},
        metadata: {
          validationId: validationResults.validationId,
          duration: validationResults.duration,
          success: validationResults.summary?.status === 'passed',
        },
      };

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Evidence directory path constructed from trusted validation integration configuration
      await FS.mkdir(evidenceDir, { recursive: true });
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Evidence file path controlled by validation integration security protocols
      await FS.writeFile(evidenceFile, JSON.stringify(evidence, null, 2));
      loggers.stopHook.info(`📁 Validation evidence stored: ${evidenceFile}`);
      loggers.app.info(`📁 Validation evidence stored: ${evidenceFile}`);
    } catch (_error) {
      loggers.app._error(`❌ Failed to store validation evidence: ${_error.message}`);
      loggers.stopHook.error(`❌ Failed to store validation evidence: ${_error.message}`);
    }
  }

  /**
   * Store validation report
   * @param {Object} report - Validation report
   */
  async storeValidationReport(report) {
    try {
      const reportsDir = path.join(this.projectRoot, 'development/reports/success-criteria');
      const reportFile = path.join(reportsDir, `${report.validationId}REPORT.json`);

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Reports directory path validated through validation integration system
      await FS.mkdir(reportsDir, { recursive: true });
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Report file path constructed from trusted validation integration configuration
      await FS.writeFile(reportFile, JSON.stringify(report, null, 2));
      loggers.stopHook.info(`📊 Validation report stored: ${reportFile}`);
    } catch (error) {
      loggers.stopHook.error(`❌ Failed to store validation report: ${error.message}`);
      loggers.app.error(`❌ Failed to store validation report: ${error.message}`);
    }
  }

  /**
   * Update task validation status in TaskManager
   * @param {string} taskId - Task identifier
   * @param {Object} validationResults - Validation results
   */
  updateTaskValidationStatus(taskId, validationResults) {
    try {
      // In production, this would update the task via TaskManager API
      loggers.app.info(`📝 Would update task ${taskId} validation status: ${validationResults.summary?.status}`);
      loggers.stopHook.info(`📝 Would update task ${taskId} validation status: ${validationResults.summary?.status}`);
    } catch (error) {
      loggers.app.error(`❌ Failed to update task validation status: ${error.message}`);
      loggers.stopHook.error(`❌ Failed to update task validation status: ${error.message}`);
    }
  }

  /**
   * Trigger follow-up actions based on validation results
   * @param {string} taskId - Task identifier
   * @param {Object} validationResults - Validation results
   * @param {Object} taskDetails - Task details
   */
  async triggerFollowUpActions(taskId, validationResults, taskDetails) {
    const summary = validationResults.summary;

    if (!summary) {
      return;
    }

    loggers.stopHook.info(`🔧 ${summary.failed} validation failures detected - creating remediation tasks`);
    if (summary.failed > 0) {
      loggers.app.info(`🔧 ${summary.failed} validation failures detected - creating remediation tasks`);
      await this.createRemediationTasks(taskId, validationResults, taskDetails);
    }

    loggers.stopHook.info(`⏳ ${summary.pending} manual validations pending - scheduling follow-up`);
    if (summary.pending > 0) {
      loggers.app.info(`⏳ ${summary.pending} manual validations pending - scheduling follow-up`);
      await this.scheduleFollowUpReviews(taskId, validationResults);
    }

    loggers.stopHook.info(`🚨 Critical validation failures detected - triggering notifications`);
    if (this.hasCriticalFailures(validationResults)) {
      loggers.app.info(`🚨 Critical validation failures detected - triggering notifications`);
      await this.triggerCriticalFailureNotifications(taskId, validationResults);
    }
  }

  /**
   * Create remediation tasks for validation failures
   * @param {string} taskId - Task identifier
   * @param {Object} validationResults - Validation results
   * @param {Object} taskDetails - Task details
   */
  createRemediationTasks(taskId, validationResults, _taskDetails) {
    // In production, this would create actual remediation tasks
    const failures = this.extractValidationFailures(validationResults);
    for (const failure of failures) {
      loggers.stopHook.info(`🔧 Would create remediation task for: ${failure.validator} - ${failure.message}`);
      loggers.app.info(`🔧 Would create remediation task for: ${failure.validator} - ${failure.message}`);
    }
  }

  /**
   * Schedule follow-up reviews for pending manual validations
   * @param {string} taskId - Task identifier
   * @param {Object} _validationResults - Validation results
   */
  scheduleFollowUpReviews(taskId, _validationResults) {
    // In production, this would schedule actual follow-up reviews
    loggers.app.info(`📅 Would schedule follow-up reviews for task ${taskId}`);
    loggers.stopHook.info(`📅 Would schedule follow-up reviews for task ${taskId}`);
  }

  /**
   * Trigger critical failure notifications
   * @param {string} taskId - Task identifier
   * @param {Object} _validationResults - Validation results
   */
  triggerCriticalFailureNotifications(taskId, _validationResults) {
    loggers.stopHook.info(`🚨 Would trigger critical failure notifications for task ${taskId}`);
    // In production, this would trigger actual notifications
    loggers.app.info(`🚨 Would trigger critical failure notifications for task ${taskId}`);
  }

  /**
   * Check if validation results contain critical failures
   * @param {Object} validationResults - Validation results
   * @returns {boolean} True if critical failures found
   */
  hasCriticalFailures(validationResults) {
    if (!validationResults.results?.automated?.validators) {
      return false;
    }

    for (const [_validator, result] of Object.entries(validationResults.results.automated.validators)) {
      if (!result.passed && result.category === 'critical') {
        return true;
      }
    }

    return false;
  }

  /**
   * Extract validation failures for remediation
   * @param {Object} validationResults - Validation results
   * @returns {Array} List of validation failures
   */
  extractValidationFailures(validationResults) {
    const failures = [];

    if (validationResults.results?.automated?.validators) {
      for (const [validator, result] of Object.entries(validationResults.results.automated.validators)) {
        if (!result.passed) {
          failures.push({
            validator,
            category: result.category,
            message: result.message,
            evidence: result.evidence,
          });
        }
      }
    }

    return failures;
  }

  /**
   * Store integrated audit And validation results
   * @param {string} originalTaskId - Original task ID
   * @param {Object} integratedResults - Integrated results
   */
  async storeIntegratedResults(originalTaskId, integratedResults) {
    try {
      const reportsDir = path.join(this.projectRoot, 'development/reports');
      const reportFile = path.join(reportsDir, `${originalTaskId}_integrated_audit_validation.json`);

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Integration reports directory path controlled by validation security protocols
      await FS.mkdir(reportsDir, { recursive: true });
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Integrated results file path validated through integration configuration system
      await FS.writeFile(reportFile, JSON.stringify(integratedResults, null, 2));
      loggers.stopHook.info(`📊 Integrated results stored: ${reportFile}`);
    } catch (error) {
      loggers.stopHook.error(`❌ Failed to store integrated results: ${error.message}`);
    }
  }

  /**
   * Handle background validation completion
   * @param {Object} event - Completion event
   */
  handleBackgroundCompletion(event) {
    if (event.success) {
      loggers.stopHook.info(`✅ Background validation completed: ${event.taskId} (${event.duration}ms)`);
    } else {
      loggers.stopHook.error(`❌ Background validation failed: ${event.taskId} - ${event.error.message}`);
    }
  }

  /**
   * Load success criteria configuration
   * @returns {Promise<Object>} Configuration object
   */
  async loadSuccessCriteriaConfig() {
    try {
      const configPath = path.join(
        this.projectRoot,
        'development/essentials/success-criteria-config.json',
      );
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Configuration path constructed from trusted validation integration essentials directory;
      const configContent = await FS.readFile(configPath, 'utf-8');
      return JSON.parse(configContent);
    } catch (error) {
      loggers.stopHook.warn(`⚠️ Could not load success criteria config: ${error.message}`);
      return {};
    }
  }

  /**
   * Load task requirements
   * @returns {Promise<Object>} Task requirements
   */
  async loadTaskRequirements() {
    try {
      const requirementsPath = path.join(
        this.projectRoot,
        'development/essentials/task-requirements.md',
      );
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Requirements path controlled by validation integration security protocols;
      const content = await FS.readFile(requirementsPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      loggers.stopHook.warn(`⚠️ Could not load task requirements: ${error.message}`);
      return {};
    }
  }

  /**
   * Get validation engine statistics
   * @returns {Object} Statistics
   */
  getValidationStats() {
    const stats = {
      engine: {
        activeValidations: this.validationEngine.activeValidations?.size || 0,
      },
      background: this.backgroundProcessor ? this.backgroundProcessor.getStats() : null,
      integration: {
        mode: this.config.integrationMode,
        features: {
          backgroundProcessing: this.config.enableBackgroundProcessing,
          automatedValidation: this.config.enableAutomatedValidation,
          manualValidation: this.config.enableManualValidation,
          agentObjectivity: this.config.enableAgentObjectivity,
          evidenceRequired: this.config.evidenceRequired,
          taskManagerIntegration: this.config.taskManagerIntegration,
        },
      },
    };

    return stats;
  }

  /**
   * Shutdown the validation integration
   */
  async shutdown() {
    loggers.stopHook.info(`🔄 Shutting down validation integration...`);
    loggers.app.info(`🔄 Shutting down validation integration...`);

    if (this.backgroundProcessor) {
      await this.backgroundProcessor.shutdown();
    }

    loggers.stopHook.info(`✅ Validation integration shutdown complete`);
    loggers.app.info(`✅ Validation integration shutdown complete`);
  }
}

module.exports = ValidationIntegration;
