
const { loggers } = require('./logger');
/**
 * ValidationFramework - Schema Enforcement System for Enhanced Data Architecture
 *
 * Provides comprehensive validation capabilities using JSON Schema Draft 2020-12
 * for the enhanced TODO.json data structure with embedded subtasks And performance indexing.
 *
 * @version 1.0.0
 * @module ValidationFramework
 */

const FS = require('fs');
const path = require('path');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

/**
 * ValidationFramework class - Comprehensive schema validation And enforcement
 *
 * Features:
 * - JSON Schema Draft 2020-12 compliance validation
 * - Type-specific validation for tasks, subtasks, And metadata
 * - Performance optimization validation for indexes
 * - Cross-reference integrity checks
 * - Detailed error reporting with context
 * - Migration compatibility validation
 *
 * @class ValidationFramework
 */
class ValidationFramework {
  /**
     * Initialize ValidationFramework with schema loading And compiler setup
     *
     * @param {Object} options - Configuration options
     * @param {string} options.schemaPath - Path to JSON schema file
     * @param {boolean} options.strictMode - Enable strict validation mode
     * @param {Object} options.customValidators - Custom validation functions
     */
  constructor(options = {}, _agentId) {
    this.logger = this._initializeLogger();
    this.options = {
      schemaPath: options.schemaPath || path.join(__dirname, '../schemas/enhanced-todo-schema.json'),
      strictMode: options.strictMode || true,
      customValidators: options.customValidators || {},
      ...options };

    this.logger.info('ValidationFramework initialization started', {
      schemaPath: this.options.schemaPath,
      strictMode: this.options.strictMode,
      customValidatorsCount: Object.keys(this.options.customValidators).length,
    });

    this.ajv = null;
    this.schema = null;
    this.validator = null;
    this.validationRules = new Map();

    this._initializeAjv();
    this._loadSchema();
    this._setupCustomValidators();
    this._initializeValidationRules();

    this.logger.info('ValidationFramework initialized successfully', {
      version: '1.0.0',
      features: ['schema_validation', 'cross_reference_checks', 'performance_validation', 'migration_compatibility'] });
  }

  /**
     * Initialize Ajv JSON Schema validator with optimizations
     *
     * @private
     */
  _initializeAjv() {
    try {
      this.ajv = new Ajv({
        allErrors: true,
        verbose: true,
        validateFormats: true,
        addUsedSchema: false,
        strict: false, // Allow draft-07 schemas
        removeAdditional: false,
        coerceTypes: false,
        schemaId: '$id',
        loadSchema: false });

      // Add format validation support
      addFormats(this.ajv);

      // Add custom keywords for enhanced validation
      this._addCustomKeywords();

      this.logger.debug('Ajv validator initialized with enhanced configuration');
    } catch (error) {
      this.logger.error('Failed to initialize Ajv validator', { error: error.message });
      throw new Error(`ValidationFramework: Ajv initialization failed - ${error.message}`);
    }
  }

  /**
     * Load JSON Schema from file system
     *
     * @private
     */
  _loadSchema() {
    try {
      if (!FS.existsSync(this.options.schemaPath)) {
        throw new Error(`Schema file not found: ${this.options.schemaPath}`);
      }

      const schemaContent = FS.readFileSync(this.options.schemaPath, 'utf8');
      this.schema = JSON.parse(schemaContent);

      // Compile schema validator
      this.validator = this.ajv.compile(this.schema);

      this.logger.info('JSON Schema loaded And compiled successfully', {
        schemaVersion: this.schema.version || 'unknown',
        schemaTitle: this.schema.title || 'Enhanced TODO Schema' });
    } catch (error) {
      this.logger.error('Failed to load JSON Schema', {
        schemaPath: this.options.schemaPath,
        error: error.message,
      });
      throw new Error(`ValidationFramework: Schema loading failed - ${error.message}`);
    }
  }

  /**
     * Add custom AJV keywords for enhanced validation
     *
     * @private
     */
  _addCustomKeywords() {
    // Custom keyword: isValidTaskId
    this.ajv.addKeyword({
      keyword: 'isValidTaskId',
      type: 'string',
      schemaType: 'boolean',
      compile: function (schema) {
        return function validate(data) {
          if (!schema) { return true; }
          // Task ID format: [category]_[timestamp]_[random]
          const taskIdPattern = /^(feature|error|test|subtask|research|audit)_\d{13}_[a-z0-9]{8}$/;
          return taskIdPattern.test(data);
        };
      },
    });

    // Custom keyword: isValidAgentId
    this.ajv.addKeyword({
      keyword: 'isValidAgentId',
      type: 'string',
      schemaType: 'boolean',
      compile: function (schema) {
        return function validate(data) {
          if (!schema) { return true; }
          // Agent ID format: [type]_[session]_[number]_[role]_[hash]
          const AGENT_ID_PATTERN = /^(dev|test|prod)_session_\d{13}_\d+_[a-z]+_[a-z0-9]{8}$/;
          return AGENT_ID_PATTERN.test(data);
        };
      },
    });

    this.logger.debug('Custom AJV keywords added successfully');
  }

  /**
     * Setup custom validation functions
     *
     * @private
     */
  _setupCustomValidators() {
    // Index consistency validator
    this.validationRules.set('indexConsistency', this._validateIndexConsistency.bind(this));

    // Cross-reference integrity validator
    this.validationRules.set('crossReferenceIntegrity', this._validateCrossReferenceIntegrity.bind(this));

    // Performance optimization validator
    this.validationRules.set('performanceOptimization', this._validatePerformanceOptimization.bind(this));

    // Migration compatibility validator
    this.validationRules.set('migrationCompatibility', this._validateMigrationCompatibility.bind(this));

    // Add user-defined custom validators
    Object.entries(this.options.customValidators).forEach(([name, validator]) => {
      this.validationRules.set(name, validator);
    });

    this.logger.debug('Custom validation rules initialized', {
      totalRules: this.validationRules.size });
  }

  /**
     * Initialize comprehensive validation rule set
     *
     * @private
     */
  _initializeValidationRules() {
    this.validationCategories = {
      structural: ['schema', 'indexConsistency'],
      integrity: ['crossReferenceIntegrity', 'dataConsistency'],
      performance: ['performanceOptimization', 'indexEfficiency'],
      compatibility: ['migrationCompatibility', 'versionCompatibility'] };

    this.logger.debug('Validation rule categories established', {
      categories: Object.keys(this.validationCategories) });
  }

  /**
     * Validate enhanced TODO data structure comprehensively
     *
     * @param {Object} data - Enhanced TODO data structure to validate
     * @param {Object} options - Validation options
     * @param {string[]} options.categories - Validation categories to run
     * @param {boolean} options.stopOnFirstError - Stop validation on first error
     * @param {boolean} options.includeWarnings - Include validation warnings
     * @returns {Object} Comprehensive validation _result
     */
  validateEnhancedData(data, options = {}) {
    const startTime = Date.now();
    const validationOptions = {
      categories: options.categories || ['structural', 'integrity', 'performance', 'compatibility'],
      stopOnFirstError: options.stopOnFirstError || false,
      includeWarnings: options.includeWarnings || true,
      ...options };

    this.logger.info('Starting comprehensive data validation', {
      dataType: typeof data,
      validationCategories: validationOptions.categories,
      stopOnFirstError: validationOptions.stopOnFirstError });

    const _result = {
      isValid: true,
      errors: [],
      warnings: [],
      performance: {
        startTime,
        endTime: null,
        duration: null,
        validationSteps: [] },
      validationResults: {},
      summary: {
        totalChecks: 0,
        passedChecks: 0,
        failedChecks: 0,
        warningChecks: 0 },
    };

    try {
      // Step 1: JSON Schema validation
      this._performSchemaValidation(data, _result, validationOptions);

      if (_result.isValid || !validationOptions.stopOnFirstError) {
        // Step 2: Category-based validation
        for (const category of validationOptions.categories) {

          this._performCategoryValidation(data, category, _result, validationOptions);

          if (!_result.isValid && validationOptions.stopOnFirstError) {
            break;
          }
        }
      }

      // Step 3: Generate validation summary
      this._generateValidationSummary(_result);

    } catch (error) {
      _result.isValid = false;
      _result.errors.push({
        type: 'validation_framework_error',
        message: `Validation framework error: ${error.message}`,
        context: { error: error.stack },
      });

      this.logger.error('Validation framework error occurred', {
        error: error.message,
        stack: error.stack,
      });
    }

    _result.performance.endTime = Date.now();
    _result.performance.duration = _result.performance.endTime - _result.performance.startTime;

    this.logger.info('Data validation completed', {
      isValid: _result.isValid,
      errorCount: _result.errors.length,
      warningCount: _result.warnings.length,
      duration: _result.performance.duration });

    return _result;
  }

  /**
     * Perform JSON Schema validation
     *
     * @param {Object} data - Data to validate
     * @param {Object} _result - Validation _result object
     * @param {Object} options - Validation options
     * @private
     */
  _performSchemaValidation(data, _result, _options) {
    const stepStart = Date.now();
    try {
      const isValidSchema = this.validator(data);

      if (!isValidSchema) {
        _result.isValid = false;

        const schemaErrors = this.validator.errors.map(error => ({
          type: 'schema_validation_error',
          message: `Schema validation failed: ${error.message}`,
          instancePath: error.instancePath,
          schemaPath: error.schemaPath,
          data: error.data,
          context: {
            keyword: error.keyword,
            params: error.params,
          },
        }));

        _result.errors.push(...schemaErrors);

        this.logger.warn('JSON Schema validation failed', {
          errorCount: schemaErrors.length,
          errors: schemaErrors });
      } else {
        this.logger.debug('JSON Schema validation passed');
      }

      _result.validationResults.schema = {
        passed: isValidSchema,
        errorCount: isValidSchema ? 0 : this.validator.errors.length,
      };

    } catch (error) {
      _result.isValid = false;
      _result.errors.push({
        type: 'schema_validation_error',
        message: `Schema validation error: ${error.message}`,
        context: { error: error.stack },
      });
    }

    _result.performance.validationSteps.push({
      step: 'schema_validation',
      duration: Date.now() - stepStart,
    });

    _result.summary.totalChecks++;
    if (_result.validationResults.schema?.passed) {
      _result.summary.passedChecks++;
    } else {
      _result.summary.failedChecks++;
    }
  }

  /**
     * Perform category-based validation
     *
     * @param {Object} data - Data to validate
     * @param {string} category - Validation category
     * @param {Object} _result - Validation _result object
     * @param {Object} options - Validation options
     * @private
     */
  _performCategoryValidation(data, category, _result, options) {
    const categoryStart = Date.now();

    if (!this.validationCategories[category]) {
      _result.warnings.push({
        type: 'unknown_validation_category',
        message: `Unknown validation category: ${category}`,
        context: { category },
      });
      return;
    }

    const categoryRules = this.validationCategories[category];
    const categoryResult = {
      passed: true,
      rules: {},
      errorCount: 0,
      warningCount: 0,
    };

    for (const ruleName of categoryRules) {
      const ruleValidator = this.validationRules.get(ruleName);

      if (!ruleValidator) {
        _result.warnings.push({
          type: 'missing_validation_rule',
          message: `Validation rule not found: ${ruleName}`,
          context: { rule: ruleName, category },
        });
        continue;
      }

      const ruleStart = Date.now();

      try {
        const ruleResult = ruleValidator(data, options);

        categoryResult.rules[ruleName] = {
          passed: ruleResult.passed,
          errors: ruleResult.errors || [],
          warnings: ruleResult.warnings || [],
          duration: Date.now() - ruleStart,
        };

        if (!ruleResult.passed) {
          categoryResult.passed = false;
          _result.isValid = false;
        }

        if (ruleResult.errors) {
          _result.errors.push(...ruleResult.errors);
          categoryResult.errorCount += ruleResult.errors.length;
        }

        if (ruleResult.warnings && options.includeWarnings) {
          _result.warnings.push(...ruleResult.warnings);
          categoryResult.warningCount += ruleResult.warnings.length;
        }

        _result.summary.totalChecks++;
        if (ruleResult.passed) {
          _result.summary.passedChecks++;
        } else {
          _result.summary.failedChecks++;
        }

      } catch (error) {
        categoryResult.passed = false;
        _result.isValid = false;

        const ruleError = {
          type: 'validation_rule_error',
          message: `Validation rule error in ${ruleName}: ${error.message}`,
          context: { rule: ruleName, category, error: error.stack },
        };

        _result.errors.push(ruleError);
        categoryResult.errorCount++;
        _result.summary.failedChecks++;

        this.logger.error('Validation rule execution failed', {
          rule: ruleName,
          category,
          error: error.message,
        });
      }
    }

    _result.validationResults[category] = categoryResult;

    _result.performance.validationSteps.push({
      step: `category_${category}`,
      duration: Date.now() - categoryStart,
      rulesExecuted: categoryRules.length,
    });

    this.logger.debug(`Category validation completed: ${category}`, {
      passed: categoryResult.passed,
      errorCount: categoryResult.errorCount,
      warningCount: categoryResult.warningCount,
    });
  }

  /**
     * Validate index consistency And integrity
     *
     * @param {Object} data - Enhanced TODO data structure
     * @param {Object} options - Validation options
     * @returns {Object} Validation _result
     * @private
     */
  _validateIndexConsistency(data, _options) {
    const _result = { passed: true, errors: [], warnings: [] };

    if (!data.indexes || !data.tasks) {
      _result.passed = false;
      _result.errors.push({
        type: 'missing_required_data',
        message: 'Missing indexes or tasks in data structure',
        context: { hasIndexes: !!data.indexes, hasTasks: !!data.tasks },
      });
      return _result;
    }

    // Validate by_id index consistency
    const byIdIndex = data.indexes.by_id || {};
    for (const task of data.tasks) {
      if (!byIdIndex[task.id]) {
        _result.passed = false;
        _result.errors.push({
          type: 'index_inconsistency',
          message: `Task ${task.id} missing from by_id index`,
          context: { taskId: task.id, indexType: 'by_id' },
        });
      }
    }

    // Validate status index consistency
    const statusIndex = data.indexes.by_status || {};
    for (const task of data.tasks) {
      const statusTasks = statusIndex[task.status] || [];
      if (!statusTasks.includes(task.id)) {
        _result.passed = false;
        _result.errors.push({
          type: 'index_inconsistency',
          message: `Task ${task.id} missing from status index ${task.status}`,
          context: { taskId: task.id, indexType: 'by_status', status: task.status },
        });
      }
    }

    return _result;
  }

  /**
     * Validate cross-reference integrity
     *
     * @param {Object} data - Enhanced TODO data structure
     * @param {Object} options - Validation options
     * @returns {Object} Validation _result
     * @private
     */
  _validateCrossReferenceIntegrity(data, _options) {
    const _result = { passed: true, errors: [], warnings: [] };

    if (!data.tasks) {
      return _result;
    }

    // Validate subtask parent references
    for (const task of data.tasks) {
      if (task.subtasks && Array.isArray(task.subtasks)) {
        for (const subtask of task.subtasks) {
          if (subtask.parent_task_id !== task.id) {
            _result.passed = false;
            _result.errors.push({
              type: 'cross_reference_error',
              message: `Subtask ${subtask.id} has incorrect parent reference`,
              context: {
                subtaskId: subtask.id,
                expectedParent: task.id,
                actualParent: subtask.parent_task_id,
              },
            });
          }
        }
      }

      // Validate agent assignments
      if (task.assignedAgents && Array.isArray(task.assignedAgents)) {
        for (const agentId of task.assignedAgents) {
          if (typeof agentId !== 'string' || agentId.trim() === '') {
            _result.warnings.push({
              type: 'invalid_agent_reference',
              message: `Invalid agent ID reference in task ${task.id}`,
              context: { taskId: task.id, agentId },
            });
          }
        }
      }
    }

    return _result;
  }

  /**
     * Validate performance optimization requirements
     *
     * @param {Object} data - Enhanced TODO data structure
     * @param {Object} options - Validation options
     * @returns {Object} Validation _result
     * @private
     */
  _validatePerformanceOptimization(data, _options) {
    const _result = { passed: true, errors: [], warnings: [] };

    if (!data.indexes) {
      _result.passed = false;
      _result.errors.push({
        type: 'performance_optimization_error',
        message: 'Missing performance indexes - O(n) operations detected',
        context: { recommendation: 'Add comprehensive indexing for O(1) lookups' },
      });
      return _result;
    }

    // Check required indexes for O(1) performance
    const requiredIndexes = ['by_id', 'by_status', 'by_category', 'by_priority'];
    for (const indexName of requiredIndexes) {
      if (!data.indexes[indexName]) {
        _result.warnings.push({
          type: 'missing_performance_index',
          message: `Missing ${indexName} index for performance optimization`,
          context: { indexName, impact: 'Potential O(n) lookup performance' },
        });
      }
    }

    // Validate index population
    if (data.tasks && data.tasks.length > 0) {
      const byIdCount = Object.keys(data.indexes.by_id || {}).length;
      if (byIdCount !== data.tasks.length) {
        _result.warnings.push({
          type: 'index_population_mismatch',
          message: 'Index population does not match task count',
          context: {
            taskCount: data.tasks.length,
            indexCount: byIdCount,
            recommendation: 'Rebuild indexes for consistency',
          },
        });
      }
    }

    return _result;
  }

  /**
     * Validate migration compatibility
     *
     * @param {Object} data - Enhanced TODO data structure
     * @param {Object} options - Validation options
     * @returns {Object} Validation _result
     * @private
     */
  _validateMigrationCompatibility(data, _options) {
    const _result = { passed: true, errors: [], warnings: [] };

    // Check for enhanced format markers
    if (!data.metadata || !data.metadata.schema_version) {
      _result.warnings.push({
        type: 'migration_compatibility_warning',
        message: 'Data may be in legacy format - missing schema version',
        context: { recommendation: 'Verify migration to enhanced format' },
      });
    }

    // Validate version compatibility
    if (data.metadata?.schema_version) {
      const currentVersion = '2.0.0';
      if (data.metadata.schema_version !== currentVersion) {
        _result.warnings.push({
          type: 'version_compatibility_warning',
          message: 'Schema version mismatch detected',
          context: {
            currentVersion,
            dataVersion: data.metadata.schema_version,
            recommendation: 'Consider migration to latest schema version',
          },
        });
      }
    }

    return _result;
  }

  /**
     * Generate comprehensive validation summary
     *
     * @param {Object} _result - Validation _result object
     * @private
     */
  _generateValidationSummary(_result) {
    // Calculate success rates
    const totalChecks = _result.summary.totalChecks;
    const successRate = totalChecks > 0 ? (_result.summary.passedChecks / totalChecks * 100).toFixed(2) : 0;

    _result.summary.successRate = parseFloat(successRate);
    _result.summary.hasErrors = _result.errors.length > 0;
    _result.summary.hasWarnings = _result.warnings.length > 0;

    // Generate recommendations
    _result.recommendations = this._generateRecommendations(_result);

    this.logger.info('Validation summary generated', {
      totalChecks,
      successRate: _result.summary.successRate,
      hasErrors: _result.summary.hasErrors,
      hasWarnings: _result.summary.hasWarnings,
    });
  }

  /**
     * Generate actionable recommendations based on validation results
     *
     * @param {Object} _result - Validation _result object
     * @returns {Array} Array of recommendation objects
     * @private
     */
  _generateRecommendations(_result) {
    const recommendations = [];

    // Error-based recommendations
    if (_result.errors.length > 0) {
      const errorTypes = [...new Set(_result.errors.map(e => e.type))];

      if (errorTypes.includes('schema_validation_error')) {
        recommendations.push({
          priority: 'high',
          category: 'data_structure',
          message: 'Fix schema validation errors to ensure data integrity',
          actions: ['Review error details', 'Correct data format', 'Re-validate structure'],
        });
      }

      if (errorTypes.includes('index_inconsistency')) {
        recommendations.push({
          priority: 'high',
          category: 'performance',
          message: 'Rebuild indexes to restore performance optimization',
          actions: ['Run index rebuild', 'Verify index consistency', 'Test lookup performance'],
        });
      }
    }

    // Warning-based recommendations
    if (_result.warnings.length > 0) {
      const warningTypes = [...new Set(_result.warnings.map(w => w.type))];

      if (warningTypes.includes('missing_performance_index')) {
        recommendations.push({
          priority: 'medium',
          category: 'optimization',
          message: 'Add missing performance indexes for better efficiency',
          actions: ['Create missing indexes', 'Populate index data', 'Validate performance'],
        });
      }

      if (warningTypes.includes('migration_compatibility_warning')) {
        recommendations.push({
          priority: 'low',
          category: 'migration',
          message: 'Consider migrating to latest enhanced format',
          actions: ['Plan migration strategy', 'Test migration process', 'Execute migration'],
        });
      }
    }

    return recommendations;
  }

  /**
     * Initialize logger for validation framework
     *
     * @returns {Object} LOGGER instance
     * @private
     */
  _initializeLogger() {
    return {
      info: (message, meta = {}) => {
        loggers.app.info(`[ValidationFramework] INFO: ${message}`, JSON.stringify(meta, null, 2));
        loggers.stopHook.info(`[ValidationFramework] INFO: ${message}`, JSON.stringify(meta, null, 2));
      },
      warn: (message, meta = {}) => {
        loggers.app.warn(`[ValidationFramework] WARN: ${message}`, JSON.stringify(meta, null, 2));
        loggers.stopHook.warn(`[ValidationFramework] WARN: ${message}`, JSON.stringify(meta, null, 2));
      },
      error: (message, meta = {}) => {
        loggers.app.error(`[ValidationFramework] ERROR: ${message}`, JSON.stringify(meta, null, 2));
        loggers.stopHook.error(`[ValidationFramework] ERROR: ${message}`, JSON.stringify(meta, null, 2));
      },
      debug: (message, meta = {}) => {
        loggers.stopHook.debug(`[ValidationFramework] DEBUG: ${message}`, JSON.stringify(meta, null, 2));
        if (process.env.NODE_ENV === 'development') {
          loggers.app.debug(`[ValidationFramework] DEBUG: ${message}`, JSON.stringify(meta, null, 2));
        }
      },
    };
  }

  /**
     * Validate specific task or subtask structure
     *
     * @param {Object} task - Task or subtask to validate
     * @param {Object} options - Validation options
     * @returns {Object} Validation _result
     */
  validateTask(task, _options = {}) {
    const startTime = Date.now();

    this.logger.info('Validating individual task', {
      taskId: task?.id,
      taskType: task?.task.category || 'unknown' });

    const _result = {
      isValid: true,
      errors: [],
      warnings: [],
      taskValidation: {
        structure: null,
        requirements: null,
        relationships: null,
      },
      performance: {
        startTime,
        endTime: null,
        duration: null,
      },
    };

    try {
      // Validate task structure against schema;
      const taskSchema = this.schema?.definitions?.Task || this.schema?.properties?.tasks?.items;
      if (taskSchema) {
        const taskValidator = this.ajv.compile(taskSchema);
        const isValidTask = taskValidator(task);

        _result.taskValidation.structure = {
          passed: isValidTask,
          errors: isValidTask ? [] : taskValidator.errors };

        if (!isValidTask) {
          _result.isValid = false;
          _result.errors.push(...taskValidator.errors.map(error => ({
            type: 'task_structure_error',
            message: `Task structure validation failed: ${error.message}`,
            instancePath: error.instancePath,
            context: { keyword: error.keyword, params: error.params } })));
        }
      }

      // Validate task requirements
      _result.taskValidation.requirements = this._validateTaskRequirements(task);
      if (!_result.taskValidation.requirements.passed) {
        _result.isValid = false;
        _result.errors.push(..._result.taskValidation.requirements.errors);
      }

      // Validate task relationships
      _result.taskValidation.relationships = this._validateTaskRelationships(task);
      if (!_result.taskValidation.relationships.passed) {
        _result.isValid = false;
        _result.errors.push(..._result.taskValidation.relationships.errors);
      }

    } catch (error) {
      _result.isValid = false;
      _result.errors.push({
        type: 'task_validation_error',
        message: `Task validation error: ${error.message}`,
        context: { error: error.stack } });

      this.logger.error('Task validation error', {
        taskId: task?.id,
        error: error.message });
    }

    _result.performance.endTime = Date.now();
    _result.performance.duration = _result.performance.endTime - _result.performance.startTime;

    this.logger.info('Task validation completed', {
      taskId: task?.id,
      isValid: _result.isValid,
      errorCount: _result.errors.length,
      duration: _result.performance.duration });

    return _result;
  }

  /**
     * Validate task requirements based on category
     *
     * @param {Object} task - Task to validate
     * @returns {Object} Validation _result
     * @private
     */
  _validateTaskRequirements(task) {
    const _result = { passed: true, errors: [], warnings: [] };

    if (!task.task.category) {
      _result.passed = false;
      _result.errors.push({
        type: 'missing_task_category',
        message: 'Task task.category is required',
        context: { taskId: task.id } });
      return _result;
    }

    // Category-specific validation
    switch (task.task.category) {
      case 'feature':
        if (!task.description || task.description.trim().length < 10) {
          _result.warnings.push({
            type: 'insufficient_description',
            message: 'Feature tasks should have detailed descriptions',
            context: { taskId: task.id, descriptionLength: task.description?.length || 0 } });
        }
        break;

      case 'error':
        if (!task.errorDetails) {
          _result.warnings.push({
            type: 'missing_error_details',
            message: 'Error tasks should include error details',
            context: { taskId: task.id } });
        }
        break;

      case 'test':
        if (!task.testCriteria) {
          _result.warnings.push({
            type: 'missing_test_criteria',
            message: 'Test tasks should specify test criteria',
            context: { taskId: task.id } });
        }
        break;
    }

    return _result;
  }

  /**
     * Validate task relationships And dependencies
     *
     * @param {Object} task - Task to validate
     * @returns {Object} Validation _result
     * @private
     */
  _validateTaskRelationships(task) {
    const _result = { passed: true, errors: [], warnings: [] };

    // Validate subtasks if present
    if (task.subtasks && Array.isArray(task.subtasks)) {
      for (const subtask of task.subtasks) {
        if (subtask.parent_task_id !== task.id) {
          _result.passed = false;
          _result.errors.push({
            type: 'subtask_parent_mismatch',
            message: 'Subtask parent ID does not match parent task',
            context: {
              taskId: task.id,
              subtaskId: subtask.id,
              expectedParent: task.id,
              actualParent: subtask.parent_task_id },
          });
        }
      }
    }

    // Validate dependencies
    if (task.dependencies && Array.isArray(task.dependencies)) {
      for (const dep of task.dependencies) {
        if (typeof dep !== 'string' || dep.trim() === '') {
          _result.warnings.push({
            type: 'invalid_dependency',
            message: 'Invalid dependency reference',
            context: { taskId: task.id, dependency: dep } });
        }
      }
    }

    return _result;
  }

  /**
     * Get validation framework statistics And health
     *
     * @returns {Object} Framework statistics
     */
  getFrameworkStats() {
    return {
      version: '1.0.0',
      initialized: !!this.validator,
      schemaLoaded: !!this.schema,
      validationRules: this.validationRules.size,
      customValidators: Object.keys(this.options.customValidators).length,
      features: [
        'schema_validation',
        'cross_reference_checks',
        'performance_validation',
        'migration_compatibility',
        'task_validation',
        'detailed_reporting'],
      supportedCategories: Object.keys(this.validationCategories),
      ajvVersion: this.ajv?.version || 'unknown' };
  }
}

module.exports = ValidationFramework;
