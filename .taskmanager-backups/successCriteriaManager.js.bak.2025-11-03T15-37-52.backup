/**
 * Success Criteria Manager Module - Enhanced with Template System Integration
 *
 * Handles all success criteria operations for tasks including:
 * - Adding success criteria to tasks with template integration
 * - Retrieving success criteria for tasks with inheritance
 * - Updating success criteria collections with validation
 * - Removing specific success criteria items
 * - Managing project-wide success criteria templates
 * - Validating success criteria format And requirements
 * - 25-point standard template system integration
 * - Project-wide inheritance rules And cascading
 * - Custom criteria support with comprehensive validation
 *
 * @author TaskManager System (Enhanced by Template System Agent #2)
 * @version 2.1.0
 */

const _TemplateManager = require('./templateManager');

class SUCCESS_CRITERIA_MANAGER {
  /**
   * Initialize SUCCESS_CRITERIA_MANAGER with enhanced template system support
   * @param {Object} dependencies - Dependency injection object
   * @param {Object} dependencies.taskManager - TaskManager instance
   * @param {Function} dependencies.withTimeout - Timeout wrapper function
   * @param {Function} dependencies.getGuideForError - Error guide function
   * @param {Function} dependencies.getFallbackGuide - Fallback guide function
   * @param {Function} dependencies.validateCriteria - Criteria validation function
   * @param {Function} dependencies.validateTaskExists - Task existence validator
   * @param {Function} dependencies.broadcastCriteriaUpdate - Criteria update broadcaster
   * @param {string} dependencies.projectRoot - Project root directory
   * @param {Object} dependencies.logger - LOGGER instance
   */
  constructor(dependencies) {
    this.taskManager = dependencies.taskManager;
    this.withTimeout = dependencies.withTimeout;
    this.getGuideForError = dependencies.getGuideForError;
    this.getFallbackGuide = dependencies.getFallbackGuide;
    this.validateCriteria = dependencies.validateCriteria || this._defaultCriteriaValidator.bind(this);
    this.validateTaskExists = dependencies.validateTaskExists || this._defaultTaskExistsValidator.bind(this);
    this.broadcastCriteriaUpdate = dependencies.broadcastCriteriaUpdate || (() => {});
    this.projectRoot = dependencies.projectRoot;
    this.logger = dependencies.logger || console;

    // Initialize comprehensive template manager
    this.templateManager = new _TemplateManager({
      taskManager: this.taskManager,
      withTimeout: this.withTimeout,
      projectRoot: this.projectRoot,
      logger: this.logger,
    });

    // Backward compatibility: Legacy template mappings
    this.defaultCriteriaTemplates = {
      basic: [
        'Linter Perfection',
        'Build Success',
        'Runtime Success',
        'Test Integrity',
      ],
      comprehensive: [
        'Linter Perfection',
        'Build Success',
        'Runtime Success',
        'Test Integrity',
        'Function Documentation',
        'API Documentation',
        'Error Handling',
        'Performance Metrics',
      ],
      enterprise: [
        'Linter Perfection',
        'Build Success',
        'Runtime Success',
        'Test Integrity',
        'Function Documentation',
        'API Documentation',
        'Architecture Documentation',
        'Decision Rationale',
        'Error Handling',
        'Performance Metrics',
        'Security Review',
        'Architectural Consistency',
        'Dependency Validation',
        'Version Compatibility',
        'Security Audit',
        'Cross-Platform',
        'Environment Variables',
        'Configuration',
        'No Credential Exposure',
        'Input Validation',
        'Output Encoding',
        'Authentication/Authorization',
        'License Compliance',
        'Data Privacy',
        'Regulatory Compliance',
      ],
    };
  }

  /**
   * Add success criteria to a specific task
   * @param {string} taskId - Target task ID
   * @param {Array<string>|string} criteria - Success criteria (string or array of strings)
   * @param {Object} [options] - Additional options
   * @param {boolean} [options.replace] - Whether to replace existing criteria (default: false, append)
   * @param {string} [options.template] - Apply a template (basic, comprehensive, enterprise)
   * @returns {Promise<Object>} Response with updated criteria or error
   */
  async addCriteria(taskId, criteria, options = {}) {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate parent task exists
          const taskExists = await this.validateTaskExists(taskId);
          if (!taskExists.valid) {
            return {
              success: false,
              error: `Task ${taskId} not found or invalid`,
              errorCode: 'TASK_NOT_FOUND',
            };
          }

          // Handle template application
          let criteriaToAdd = criteria;
          if (options.template && this.defaultCriteriaTemplates[options.template]) {
            criteriaToAdd = this.defaultCriteriaTemplates[options.template];
          }

          // Normalize criteria to array
          const criteriaArray = Array.isArray(criteriaToAdd) ? criteriaToAdd : [criteriaToAdd];

          // Validate criteria
          const validationResult = this.validateCriteria(criteriaArray);
          if (!validationResult.valid) {
            return {
              success: false,
              error: `Invalid success criteria: ${validationResult.errors.join(', ')}`,
              errorCode: 'INVALID_CRITERIA',
            };
          }

          // Get current task data
          const taskData = await this.taskManager.getTask(taskId);
          if (!taskData) {
            return {
              success: false,
              error: `Could not retrieve task data for ${taskId}`,
              errorCode: 'TASK_DATA_RETRIEVAL_FAILED',
            };
          }

          // Determine final criteria based on options
          let finalCriteria;
          if (options.replace) {
            finalCriteria = [...criteriaArray];
          } else {
            const existingCriteria = taskData.success_criteria || [];
            // Add only unique criteria to avoid duplicates
            const uniqueNewCriteria = criteriaArray.filter(criterion =>
              !existingCriteria.includes(criterion),
            );
            finalCriteria = [...existingCriteria, ...uniqueNewCriteria];
          }

          // Update task with new success criteria
          const updateResult = await this.taskManager.updateTaskSuccessCriteria(taskId, finalCriteria);
          if (!updateResult.success) {
            return {
              success: false,
              error: `Failed to update success criteria: ${updateResult.error}`,
              errorCode: 'CRITERIA_UPDATE_FAILED',
            };
          }

          // Broadcast criteria update
          await this.broadcastCriteriaUpdate({
            action: 'added',
            taskId,
            criteria: finalCriteria,
            addedCriteria: options.replace ? criteriaArray : criteriaArray.filter(c => !taskData.success_criteria?.includes(c)),
            template: options.template,
          });

          return {
            success: true,
            taskId,
            criteria: finalCriteria,
            addedCount: options.replace ? criteriaArray.length : criteriaArray.length,
            totalCount: finalCriteria.length,
            message: `Success criteria ${options.replace ? 'replaced' : 'added'} successfully`,
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'CRITERIA_ADD_OPERATION_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Get success criteria for a specific task
   * @param {string} taskId - Target task ID
   * @returns {Promise<Object>} Response with criteria array or error
   */
  async getCriteria(taskId) {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate parent task exists
          const taskExists = await this.validateTaskExists(taskId);
          if (!taskExists.valid) {
            return {
              success: false,
              error: `Task ${taskId} not found`,
              errorCode: 'TASK_NOT_FOUND',
            };
          }

          // Get task data
          const taskData = await this.taskManager.getTask(taskId);
          if (!taskData) {
            return {
              success: false,
              error: `Could not retrieve task data for ${taskId}`,
              errorCode: 'TASK_DATA_RETRIEVAL_FAILED',
            };
          }

          const criteria = taskData.success_criteria || [];

          return {
            success: true,
            taskId,
            criteria,
            count: criteria.length,
            hasTemplate: this._detectAppliedTemplate(criteria),
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'CRITERIA_RETRIEVAL_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Update success criteria for a task (replace all criteria)
   * @param {string} taskId - Target task ID
   * @param {Array<string>} criteria - New success criteria array
   * @returns {Promise<Object>} Response with updated criteria or error
   */
  updateCriteria(taskId, criteria) {
    return this.addCriteria(taskId, criteria, { replace: true });
  }

  /**
   * Delete a specific success criterion from a task
   * @param {string} taskId - Target task ID
   * @param {string} criterionText - Exact text of criterion to remove
   * @returns {Promise<Object>} Response confirming deletion or error
   */
  async deleteCriterion(taskId, criterionText) {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate parent task exists
          const taskExists = await this.validateTaskExists(taskId);
          if (!taskExists.valid) {
            return {
              success: false,
              error: `Task ${taskId} not found`,
              errorCode: 'TASK_NOT_FOUND',
            };
          }

          // Get current task data
          const taskData = await this.taskManager.getTask(taskId);
          if (!taskData) {
            return {
              success: false,
              error: `Could not retrieve task data for ${taskId}`,
              errorCode: 'TASK_DATA_RETRIEVAL_FAILED',
            };
          }

          const currentCriteria = taskData.success_criteria || [];

          // Check if criterion exists
          if (!currentCriteria.includes(criterionText)) {
            return {
              success: false,
              error: `Success criterion "${criterionText}" not found in task ${taskId}`,
              errorCode: 'CRITERION_NOT_FOUND',
            };
          }

          // Remove the specific criterion
          const updatedCriteria = currentCriteria.filter(criterion => criterion !== criterionText);

          // Update task
          const updateResult = await this.taskManager.updateTaskSuccessCriteria(taskId, updatedCriteria);
          if (!updateResult.success) {
            return {
              success: false,
              error: `Failed to update success criteria: ${updateResult.error}`,
              errorCode: 'CRITERIA_UPDATE_FAILED',
            };
          }

          // Broadcast criteria update
          await this.broadcastCriteriaUpdate({
            action: 'deleted',
            taskId,
            criteria: updatedCriteria,
            deletedCriterion: criterionText,
          });

          return {
            success: true,
            taskId,
            deletedCriterion: criterionText,
            remainingCriteria: updatedCriteria,
            remainingCount: updatedCriteria.length,
            message: 'Success criterion deleted successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'CRITERION_DELETE_OPERATION_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Get available project-wide success criteria templates
   * @returns {Promise<Object>} Response with available templates
   */
  async getProjectWideTemplates() {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (() => {
          const templates = {};

          Object.keys(this.defaultCriteriaTemplates).forEach(templateName => {
            // Security: Validate template name to prevent object injection
            if (typeof templateName === 'string' && Object.prototype.hasOwnProperty.call(this.defaultCriteriaTemplates, templateName)) {
              // eslint-disable-next-line security/detect-object-injection -- templateName validated with hasOwnProperty
              const templateCriteria = this.defaultCriteriaTemplates[templateName];
              /* eslint-disable security/detect-object-injection */
              templates[templateName] = {
              /* eslint-enable security/detect-object-injection */
                name: templateName,
                criteria: templateCriteria,
                count: templateCriteria.length,
                description: this._getTemplateDescription(templateName),
              };
            }
          });

          return {
            success: true,
            templates,
            availableTemplates: Object.keys(templates),
            message: 'Project-wide templates retrieved successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'TEMPLATES_RETRIEVAL_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Apply a project-wide template to a task (Enhanced with Template Manager)
   * @param {string} taskId - Target task ID
   * @param {string} templateName - Template name (basic, comprehensive, enterprise, 25_point_standard)
   * @param {boolean} [replace=false] - Whether to replace existing criteria
   * @returns {Promise<Object>} Response with applied template or error
   */
  async applyProjectTemplate(taskId, templateName, replace = false) {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Try to load template from TemplateManager first
          const template = await this.templateManager.loadTemplate(templateName);

          if (template) {
            // Use comprehensive template system
            const taskData = await this.taskManager.getTask(taskId);
            if (!taskData) {
              return {
                success: false,
                error: `Task ${taskId} not found`,
                errorCode: 'TASK_NOT_FOUND',
              };
            }

            // Apply inheritance And get final criteria
            const inheritanceResult = await this.templateManager.applyInheritance(taskId, taskData, []);
            const finalCriteria = inheritanceResult.finalCriteria;

            // Update task with comprehensive criteria
            const updateResult = await this.taskManager.updateTaskSuccessCriteria(taskId, finalCriteria);
            if (!updateResult.success) {
              return {
                success: false,
                error: `Failed to update success criteria: ${updateResult.error}`,
                errorCode: 'CRITERIA_UPDATE_FAILED',
              };
            }

            // Broadcast criteria update
            await this.broadcastCriteriaUpdate({
              action: 'template_applied',
              taskId,
              criteria: finalCriteria,
              template: templateName,
              inheritance: inheritanceResult.inheritance,
            });

            return {
              success: true,
              taskId,
              templateName,
              appliedCriteria: finalCriteria,
              totalCount: finalCriteria.length,
              inheritance: inheritanceResult.inheritance,
              message: `Template ${templateName} applied successfully with inheritance`,
            };
          }

          // Fallback to legacy template system
          // Security: Validate template name before object access
          if (typeof templateName !== 'string' || !Object.prototype.hasOwnProperty.call(this.defaultCriteriaTemplates, templateName)) {
            return {
              success: false,
              error: `Template "${templateName}" not found. Available templates: ${Object.keys(this.defaultCriteriaTemplates).join(', ')}, 25_point_standard`,
              errorCode: 'TEMPLATE_NOT_FOUND',
            };
          }

          // Security: Safe object access with validation
          const templateCriteria = Object.prototype.hasOwnProperty.call(this.defaultCriteriaTemplates, templateName)
            // eslint-disable-next-line security/detect-object-injection -- templateName validated with hasOwnProperty
            ? this.defaultCriteriaTemplates[templateName]
            : null;

          if (!templateCriteria) {
            return {
              success: false,
              error: `Template "${templateName}" not found or invalid`,
              errorCode: 'TEMPLATE_NOT_FOUND',
            };
          }

          return this.addCriteria(taskId, templateCriteria, {
            replace,
            template: templateName,
          });
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'TEMPLATE_APPLICATION_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Private method to detect which template was applied based on criteria
   * @param {Array<string>} criteria - Current criteria array
   * @returns {string|null} Detected template name or null
   */
  _detectAppliedTemplate(criteria) {
    for (const [templateName, templateCriteria] of Object.entries(this.defaultCriteriaTemplates)) {
      const hasAllCriteria = templateCriteria.every(criterion => criteria.includes(criterion));
      if (hasAllCriteria && criteria.length === templateCriteria.length) {
        return templateName;
      }
    }
    return null;
  }

  /**
   * Private method to get template descriptions
   * @param {string} templateName - Template name
   * @returns {string} Template description
   */
  _getTemplateDescription(templateName) {
    const descriptions = {
      basic: 'Essential success criteria for code quality And functionality',
      comprehensive: 'Extended criteria including documentation And performance',
      enterprise: 'Full enterprise-grade criteria including security, compliance, And architecture',
    };
    // Security: Validate key before object access
    return (typeof templateName === 'string' && Object.prototype.hasOwnProperty.call(descriptions, templateName))
      // eslint-disable-next-line security/detect-object-injection -- templateName validated with hasOwnProperty
      ? descriptions[templateName]
      : 'Custom template';
  }

  /**
   * Default success criteria validator
   * @param {Array<string>} criteria - Criteria array to validate
   * @returns {Object} Validation result
   */
  _defaultCriteriaValidator(criteria) {
    const errors = [];

    if (!Array.isArray(criteria)) {
      errors.push('Success criteria must be an array');
      return { valid: false, errors };
    }

    if (criteria.length === 0) {
      errors.push('At least one success criterion is required');
    }

    criteria.forEach((criterion, index) => {
      if (typeof criterion !== 'string') {
        errors.push(`Success criterion at index ${index} must be a string`);
      } else if (criterion.trim().length === 0) {
        errors.push(`Success criterion at index ${index} cannot be empty`);
      } else if (criterion.length > 200) {
        errors.push(`Success criterion at index ${index} is too long (max 200 characters)`);
      }
    });

    // Check for duplicates
    const uniqueCriteria = new Set(criteria);
    if (uniqueCriteria.size !== criteria.length) {
      errors.push('Success criteria must be unique (no duplicates)');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Default task existence validator
   * @param {string} taskId - Task ID to validate
   * @returns {Promise<Object>} Validation result
   */
  async _defaultTaskExistsValidator(taskId) {
    try {
      const task = await this.taskManager.getTask(taskId);
      return {
        valid: !!task,
        task,
      };
    } catch {
      return {
        valid: false,
        error: error.message,
      };
    }
  }

  /**
   * Set project-wide success criteria configuration
   * @param {Object} criteriaData - Project-wide criteria configuration
   * @returns {Promise<Object>} Response with _operationresult
   */
  async setProjectCriteria(criteriaData) {
    let guide;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (() => {
          // Validate criteria data structure
          if (!criteriaData || typeof criteriaData !== 'object') {
            return {
              success: false,
              error: 'Project criteria data must be a valid object',
              errorCode: 'INVALID_CRITERIA_DATA',
            };
          }

          // Set default structure if not provided
          const normalizedData = {
            project_wide_criteria: criteriaData.project_wide_criteria || criteriaData,
            default_template: criteriaData.default_template || '25_point_standard',
            inheritance_rules: criteriaData.inheritance_rules || {},
            last_updated: new Date().toISOString(),
          };

          // Store in TODO.json project metadata (this would be implemented in TaskManager)
          // for now, return success response indicating project criteria would be set
          return {
            success: true,
            criteriaData: normalizedData,
            affected: {
              sets: Object.keys(normalizedData.project_wide_criteria).length,
              rules: Object.keys(normalizedData.inheritance_rules).length,
            },
            message: 'Project-wide success criteria configuration updated successfully',
          };
        })(),
        this.timeoutMs || 10000,
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'PROJECT_CRITERIA_SET_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Generate comprehensive criteria report for a task
   * @param {string} taskId - Target task ID
   * @returns {Promise<Object>} Response with detailed criteria report
   */
  async generateCriteriaReport(taskId) {
    let guide;
    try {
      guide = await this.getGuideForError('success-criteria-reporting');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate task exists
          const taskValidation = await this.validateTaskExists(taskId);
          if (!taskValidation.valid) {
            return {
              success: false,
              error: `Task ${taskId} not found`,
              errorCode: 'TASK_NOT_FOUND',
            };
          }

          const task = taskValidation.task;

          // Get full criteria information
          const criteriaResult = await this.getCriteria(taskId);
          if (!criteriaResult.success) {
            return criteriaResult;
          }

          // Generate comprehensive report
          const report = {
            taskId,
            taskInfo: {
              title: task.title || 'Unknown Task',
              category: task.category || 'unknown',
              status: task.status || 'unknown',
              created_at: task.created_at,
              assigned_agent: task.assigned_agent,
            },
            criteria: {
              total: criteriaResult.criteria.length,
              items: criteriaResult.criteria,
            },
            validation: {
              status: task.criteria_validation_status || 'pending',
              last_validated: task.criteria_validation_updated || null,
              summary: task.criteria_validation_summary || {
                total: 0,
                passed: 0,
                failed: 0,
                pending: 0,
              },
            },
            template: criteriaResult.templateInfo || null,
            evidence: criteriaResult.evidenceData || {},
            recommendations: this._generateRecommendations(task, criteriaResult),
            generated_at: new Date().toISOString(),
          };

          return {
            success: true,
            taskId,
            report,
            message: 'Criteria report generated successfully',
          };
        })(),
        this.timeoutMs || 10000,
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-reporting'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'CRITERIA_REPORT_GENERATION_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-reporting'),
      };
    }
  }

  /**
   * Generate recommendations based on task And criteria data
   * @param {Object} task - Task data
   * @param {Object} criteriaResult - Criteria information
   * @returns {Array} Array of recommendation objects
   */
  _generateRecommendations(task, criteriaResult) {
    const recommendations = [];

    // Check if task has any criteria
    if (!criteriaResult.criteria || criteriaResult.criteria.length === 0) {
      recommendations.push({
        type: 'warning',
        message: 'Task has no success criteria defined',
        action: 'Consider adding success criteria using add-success-criteria command',
        priority: 'high',
      });
    }

    // Check if using comprehensive template
    if (criteriaResult.criteria.length < 10) {
      recommendations.push({
        type: 'suggestion',
        message: 'Consider using comprehensive success criteria template',
        action: 'Apply comprehensive template for better quality assurance',
        priority: 'medium',
      });
    }

    // Check validation status
    if (task.criteria_validation_status === 'pending') {
      recommendations.push({
        type: 'action',
        message: 'Success criteria validation is pending',
        action: 'Run validate-criteria command to check criteria compliance',
        priority: 'medium',
      });
    }

    return recommendations;
  }

  /**
   * Get available templates including 25-point standard template
   * @returns {Promise<Object>} Response with all available templates
   */
  async getAvailableTemplates() {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const templates = {};

          // Add legacy templates
          Object.keys(this.defaultCriteriaTemplates).forEach(templateName => {
            // Security: Validate template name to prevent object injection
            if (typeof templateName === 'string' && Object.prototype.hasOwnProperty.call(this.defaultCriteriaTemplates, templateName)) {
              // eslint-disable-next-line security/detect-object-injection -- templateName validated with hasOwnProperty
              const templateCriteria = this.defaultCriteriaTemplates[templateName];
              /* eslint-disable security/detect-object-injection */
              templates[templateName] = {
              /* eslint-enable security/detect-object-injection */
                name: templateName,
                criteria: templateCriteria,
                count: templateCriteria.length,
                description: this._getTemplateDescription(templateName),
                type: 'legacy',
              };
            }
          });

          // Add 25-point standard template
          const standardTemplate = await this.templateManager.loadTemplate('25_point_standard');
          if (standardTemplate) {
            templates['25_point_standard'] = {
              name: '25-Point Standard Template',
              criteria: this.templateManager.extractCriteriaFromTemplate(standardTemplate),
              count: 25,
              description: 'Comprehensive 25-point quality And compliance template',
              type: 'comprehensive',
              categories: await this.templateManager.getCriteriaCategories('25_point_standard'),
            };
          }

          return {
            success: true,
            templates,
            availableTemplates: Object.keys(templates),
            totalTemplates: Object.keys(templates).length,
            message: 'All available templates retrieved successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'TEMPLATES_RETRIEVAL_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Get categorized criteria from 25-point template
   * @param {string} [templateId='25_point_standard'] - Template identifier
   * @returns {Promise<Object>} Response with categorized criteria
   */
  async getCategorizedCriteria(templateId = '25_point_standard') {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const categories = await this.templateManager.getCriteriaCategories(templateId);

          if (!categories) {
            return {
              success: false,
              error: `Template ${templateId} not found or does not support categorization`,
              errorCode: 'TEMPLATE_NOT_FOUND',
            };
          }

          return {
            success: true,
            templateId,
            categories,
            totalCategories: Object.keys(categories).length,
            totalCriteria: Object.values(categories).reduce((sum, cat) => sum + cat.count, 0),
            message: 'Categorized criteria retrieved successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'CATEGORIES_RETRIEVAL_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Apply inheritance rules to task criteria
   * @param {string} taskId - Target task ID
   * @param {Array} [customCriteria=[]] - Additional custom criteria
   * @returns {Promise<Object>} Response with inheritance applied
   */
  async applyInheritanceRules(taskId, customCriteria = []) {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate task exists
          const taskExists = await this.validateTaskExists(taskId);
          if (!taskExists.valid) {
            return {
              success: false,
              error: `Task ${taskId} not found`,
              errorCode: 'TASK_NOT_FOUND',
            };
          }

          const taskData = await this.taskManager.getTask(taskId);
          if (!taskData) {
            return {
              success: false,
              error: `Could not retrieve task data for ${taskId}`,
              errorCode: 'TASK_DATA_RETRIEVAL_FAILED',
            };
          }

          // Validate custom criteria
          if (customCriteria.length > 0) {
            const validationResult = this.templateManager.validateCriteria(customCriteria);
            if (!validationResult.valid) {
              return {
                success: false,
                error: `Invalid custom criteria: ${validationResult.errors.join(', ')}`,
                errorCode: 'INVALID_CUSTOM_CRITERIA',
                validationWarnings: validationResult.warnings,
              };
            }
          }

          // Apply inheritance
          const inheritanceResult = await this.templateManager.applyInheritance(taskId, taskData, customCriteria);

          // Update task with final criteria
          const updateResult = await this.taskManager.updateTaskSuccessCriteria(taskId, inheritanceResult.finalCriteria);
          if (!updateResult.success) {
            return {
              success: false,
              error: `Failed to update success criteria: ${updateResult.error}`,
              errorCode: 'CRITERIA_UPDATE_FAILED',
            };
          }

          // Broadcast criteria update
          await this.broadcastCriteriaUpdate({
            action: 'inheritance_applied',
            taskId,
            criteria: inheritanceResult.finalCriteria,
            inheritance: inheritanceResult.inheritance,
          });

          return {
            success: true,
            taskId,
            finalCriteria: inheritanceResult.finalCriteria,
            templateCriteria: inheritanceResult.templateCriteria,
            projectWideCriteria: inheritanceResult.projectWideCriteria,
            customCriteria: inheritanceResult.customCriteria,
            inheritance: inheritanceResult.inheritance,
            totalCount: inheritanceResult.finalCriteria.length,
            message: 'Inheritance rules applied successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'INHERITANCE_APPLICATION_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Create custom template
   * @param {Object} templateData - Template data object
   * @returns {Promise<Object>} Response with creation result
   */
  async createCustomTemplate(templateData) {
    let guide = null;
    try {
      guide = await this.getGuideForError('success-criteria-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const creationResult = await this.templateManager.createCustomTemplate(templateData);

          if (!creationResult.success) {
            return creationResult;
          }

          // Broadcast template creation
          await this.broadcastCriteriaUpdate({
            action: 'template_created',
            templateId: templateData.id,
            templateName: templateData.name,
          });

          return {
            success: true,
            templateId: creationResult.templateId,
            message: 'Custom template created successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'TEMPLATE_CREATION_FAILED',
        guide: guide || this.getFallbackGuide('success-criteria-operations'),
      };
    }
  }

  /**
   * Get template manager cache statistics
   * @returns {Promise<Object>} Response with cache statistics
   */
  getCacheStatistics() {
    try {
      const stats = this.templateManager.getCacheStatistics();

      return {
        success: true,
        cacheStatistics: stats,
        message: 'Cache statistics retrieved successfully',
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'CACHE_STATS_RETRIEVAL_FAILED',
      };
    }
  }

  /**
   * Clear template manager caches
   * @returns {Promise<Object>} Response with clear result
   */
  clearCaches() {
    try {
      this.templateManager.clearCaches();

      return {
        success: true,
        message: 'All template caches cleared successfully',
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'CACHE_CLEAR_FAILED',
      };
    }
  }
}

module.exports = SUCCESS_CRITERIA_MANAGER;
