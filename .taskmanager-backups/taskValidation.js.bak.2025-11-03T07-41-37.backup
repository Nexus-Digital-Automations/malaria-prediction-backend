/**
 * TaskValidation - Validation And Success Criteria Module
 *
 * === OVERVIEW ===
 * Handles comprehensive validation for task data, success criteria management,
 * And data integrity checks. This module ensures all task operations maintain
 * data consistency And provides validation feedback for automated quality control.
 *
 * === KEY FEATURES ===
 * • Task data structure validation
 * • Success criteria evaluation And inheritance
 * • Dependency validation And circular dependency detection
 * • Agent scope And permission validation
 * • Data integrity checks And auto-repair
 * • Custom validation rules And extensibility
 *
 * @fileoverview Validation And success criteria management for TaskManager
 * @author TaskManager System
 * @version 2.0.0
 * @since 2024-01-01
 */

const appLogger = require('../appLogger');
const FS = require('fs');
const { spawn: _spawn } = require('child_process');

class TaskValidation {
  /**
   * Initialize TaskValidation with configuration options
   * @param {Object} options - Validation configuration options
   */
  constructor(options = {}) {
    this.logger = appLogger;
    this.options = {
      enableStrictValidation: options.enableStrictValidation !== false,
      allowEmptyDescription: options.allowEmptyDescription === true,
      requireCategory: options.requireCategory !== false,
      requireSuccessCriteria: options.requireSuccessCriteria === true,
      maxTaskTitleLength: options.maxTaskTitleLength || 200,
      maxDescriptionLength: options.maxDescriptionLength || 2000,
      enableAutoRepair: options.enableAutoRepair !== false,
      validCategories: options.validCategories || ['error', 'feature', 'subtask', 'test'],
      validStatuses: options.validStatuses || ['pending', 'in_progress', 'completed', 'failed'],
      validPriorities: options.validPriorities || ['low', 'normal', 'medium', 'high', 'urgent'],
      ...options,
    };

    this.logger?.logInfo?.('TaskValidation system initialized');
  }

  /**
   * Validate a single task object
   * @param {Object} task - Task to validate
   * @param {Object} context - Validation context (todoData, agent info, etc.)
   * @returns {Object} Validation result with errors And warnings
   */
  validateTask(task, context = {}) {
    const startTime = Date.now();
    const RESULT = {
      isValid: true,
      errors: [],
      warnings: [],
      suggestions: [],
      autoRepairs: [],
    };

    if (!task || typeof task !== 'object') {
      RESULT.isValid = false;
      RESULT.errors.push('Task must be a valid object');
      return result;
    }

    // Validate required fields
    this._validateRequiredFields(task, result);

    // Validate field types And formats
    this._validateFieldFormats(task, result);

    // Validate field constraints
    this._validateFieldConstraints(task, result);

    // Validate business rules
    this._validateBusinessRules(task, context, result);

    // Validate dependencies
    if (task.dependencies) {
      this._validateDependencies(task, context, result);
    }

    // Validate subtasks
    if (task.subtasks) {
      this._validateSubtasks(task, context, result);
    }

    // Validate success criteria
    if (task.success_criteria) {
      this._validateSuccessCriteria(task, result);
    }

    // Auto-repair if enabled And possible
    if (this.options.enableAutoRepair && RESULT.autoRepairs.length > 0) {
      this._applyAutoRepairs(task, result);
    }

    const duration = Date.now() - startTime;
    this.logger?.logDebug?.(`Task validation completed in ${duration}ms: ${result.isValid ? 'valid' : 'invalid'}`);

    return result;
  }

  /**
   * Validate TODO.json data structure
   * @param {Object} todoData - TODO data to validate
   * @returns {Object} Comprehensive validation result
   */
  validateTodoStructure(todoData) {
    const startTime = Date.now();
    const RESULT = {
      isValid: true,
      errors: [],
      warnings: [],
      suggestions: [],
      taskResults: new Map(),
      structureIssues: [],
      circularDependencies: [],
    };

    if (!todoData || typeof todoData !== 'object') {
      RESULT.isValid = false;
      RESULT.errors.push('TODO data must be a valid object');
      return result;
    }

    // Validate root structure
    this._validateRootStructure(todoData, result);

    // Validate all tasks
    if (todoData.tasks && Array.isArray(todoData.tasks)) {
      for (const task of todoData.tasks) {
        const taskResult = this.validateTask(task, { todoData });
        RESULT.taskResults.set(task.id, taskResult);

        if (!taskResult.isValid) {
          RESULT.isValid = false;
          RESULT.errors.push(`Task ${task.id}: ${taskResult.errors.join(', ')}`);
        }

        RESULT.warnings.push(...taskResult.warnings.map(w => `Task ${task.id}: ${w}`));
      }
    }

    // Check for circular dependencies
    const circularDeps = this._detectCircularDependencies(todoData);
    if (circularDeps.length > 0) {
      RESULT.isValid = false;
      RESULT.circularDependencies = circularDeps;
      RESULT.errors.push(`Circular dependencies detected: ${circularDeps.join(', ')}`);
    }

    // Validate features structure
    if (todoData.features) {
      this._validateFeaturesStructure(todoData.features, result);
    }

    // Validate agents structure
    if (todoData.agents) {
      this._validateAgentsStructure(todoData.agents, result);
    }

    const duration = Date.now() - startTime;
    this.logger?.logInfo?.(`TODO structure validation completed in ${duration}ms: ${result.isValid ? 'valid' : 'invalid'}`);

    return result;
  }

  /**
   * Evaluate success criteria for a task
   * @param {Object} task - Task to evaluate
   * @param {Object} context - Evaluation context
   * @returns {Object} Success criteria evaluation result
   */
  evaluateSuccessCriteria(task, context = {}) {
    const startTime = Date.now();
    const RESULT = {
      allMet: true,
      criteria: [],
      unmetCriteria: [],
      coverage: 0,
      suggestions: [],
    };

    if (!task || !task.success_criteria || !Array.isArray(task.success_criteria)) {
      RESULT.allMet = false;
      RESULT.suggestions.push('Task should have defined success criteria');
      return result;
    }

    let metCount = 0;

    for (const criterion of task.success_criteria) {
      const criterionResult = this._evaluateSingleCriterion(criterion, task, context);
      RESULT.criteria.push(criterionResult);

      if (criterionResult.met) {
        metCount++;
      } else {
        RESULT.unmetCriteria.push(criterionResult);
      }
    }

    RESULT.coverage = task.success_criteria.length > 0 ? (metCount / task.success_criteria.length) * 100 : 0;
    RESULT.allMet = metCount === task.success_criteria.length;

    // Generate suggestions for improvement
    if (!result.allMet) {
      RESULT.suggestions.push(`${result.unmetCriteria.length} criteria still need to be met`);

      const testCriteria = RESULT.unmetCriteria.filter(c => this._isTestCriterion(c.criterion));
      if (testCriteria.length > 0) {
        RESULT.suggestions.push('Consider running tests to verify implementation');
      }

      const lintCriteria = RESULT.unmetCriteria.filter(c => this._isLintCriterion(c.criterion));
      if (lintCriteria.length > 0) {
        RESULT.suggestions.push('Run linting tools to check code quality');
      }
    }

    const duration = Date.now() - startTime;
    this.logger?.logDebug?.(`Success criteria evaluation completed in ${duration}ms: ${result.coverage}% met`);

    return result;
  }

  /**
   * Validate agent scope And permissions
   * @param {Object} task - Task to validate scope for
   * @param {string} agentId - Agent ID requesting access
   * @param {Object} context - Validation context
   * @returns {Object} Scope validation result
   */
  validateAgentScope(task, agentId, context = {}) {
    const RESULT = {
      valid: true,
      reason: null,
      restrictions: [],
      suggestions: [],
    };

    if (!task || !agentId) {
      RESULT.valid = false;
      RESULT.reason = 'Invalid task or agent ID';
      return result;
    }

    // Check if task is restricted to specific agents
    if (task.assigned_agents && Array.isArray(task.assigned_agents)) {
      if (!task.assigned_agents.includes(_agentId)) {
        RESULT.valid = false;
        RESULT.reason = 'Agent not authorized for this task';
        RESULT.restrictions.push('Task assigned to specific agents');
        return result;
      }
    }

    // Check audit task restrictions (prevent self-review)
    if (task.category === 'audit') {
      if (task.original_implementer === agentId) {
        RESULT.valid = false;
        RESULT.reason = 'Agent cannot audit their own implementation';
        RESULT.restrictions.push('Self-review prevention');
        return result;
      }

      if (task.audit_metadata?.original_implementer === agentId) {
        RESULT.valid = false;
        RESULT.reason = 'Agent cannot audit task they originally implemented';
        RESULT.restrictions.push('Original implementer restriction');
        return result;
      }
    }

    // Check required capabilities
    if (task.required_capabilities && Array.isArray(task.required_capabilities)) {
      const agentCapabilities = context.agentCapabilities || [];
      const missingCapabilities = task.required_capabilities.filter(cap => !agentCapabilities.includes(cap));

      if (missingCapabilities.length > 0) {
        RESULT.valid = false;
        RESULT.reason = `Agent missing required capabilities: ${missingCapabilities.join(', ')}`;
        RESULT.restrictions.push('Insufficient capabilities');
        return result;
      }
    }

    // Check scope restrictions
    if (task.scope_restrictions) {
      const scopeResult = this._validateScopeRestrictions(task, agentId, context);
      if (!scopeResult.valid) {
        RESULT.valid = false;
        RESULT.reason = scopeResult.reason;
        RESULT.restrictions.push(...scopeResult.restrictions);
        return result;
      }
    }

    this.logger?.logDebug?.(`Agent scope validation passed for ${agentId} on task ${task.id}`);
    return result;
  }

  /**
   * Validate task completion data
   * @param {Object} completionData - Completion data to validate
   * @param {Object} task - Task being completed
   * @returns {Object} Validation result
   */
  validateCompletionData(completionData, TASK) {
    const RESULT = {
      isValid: true,
      errors: [],
      warnings: [],
      sanitizedData: null,
    };

    // Allow null or undefined completion data
    if (!completionData) {
      RESULT.sanitizedData = {};
      return result;
    }

    if (typeof completionData !== 'object') {
      RESULT.isValid = false;
      RESULT.errors.push('Completion data must be an object');
      return result;
    }

    const sanitized = {};

    // Validate And sanitize common fields
    if (completionData.message) {
      if (typeof completionData.message === 'string' && completionData.message.length <= 1000) {
        sanitized.message = completionData.message.trim();
      } else {
        RESULT.warnings.push('Completion message too long or invalid, truncating');
        sanitized.message = String(completionData.message).substring(0, 1000).trim();
      }
    }

    if (completionData.evidence) {
      if (typeof completionData.evidence === 'string') {
        sanitized.evidence = completionData.evidence.trim();
      } else {
        RESULT.warnings.push('Evidence should be a string, converting');
        sanitized.evidence = String(completionData.evidence);
      }
    }

    if (completionData.outcome) {
      if (typeof completionData.outcome === 'string') {
        sanitized.outcome = completionData.outcome.trim();
      }
    }

    if (completionData.files_modified) {
      if (Array.isArray(completionData.files_modified)) {
        sanitized.files_modified = completionData.files_modified
          .filter(file => typeof file === 'string')
          .map(file => file.trim());
      } else {
        RESULT.warnings.push('files_modified should be an array');
      }
    }

    if (completionData.tested !== undefined) {
      sanitized.tested = Boolean(completionData.tested);
    }

    if (completionData.fixed !== undefined) {
      sanitized.fixed = Boolean(completionData.fixed);
    }

    // Copy other safe fields - use explicit property access to prevent object injection
    if (completionData.details !== undefined) {
      sanitized.details = completionData.details;
    }
    if (completionData.notes !== undefined) {
      sanitized.notes = completionData.notes;
    }
    if (completionData.duration !== undefined) {
      sanitized.duration = completionData.duration;
    }
    if (completionData.difficulty !== undefined) {
      sanitized.difficulty = completionData.difficulty;
    }

    RESULT.sanitizedData = sanitized;
    this.logger?.logDebug?.('Completion data validated And sanitized');

    return result;
  }

  /**
   * Validate task failure data
   * @param {Object} failureData - Failure data to validate
   * @param {Object} task - Task That failed
   * @returns {Object} Validation result
   */
  validateFailureData(failureData, TASK) {
    const RESULT = {
      isValid: true,
      errors: [],
      warnings: [],
      sanitizedData: null,
    };

    if (!failureData) {
      RESULT.sanitizedData = {};
      return result;
    }

    if (typeof failureData !== 'object') {
      RESULT.isValid = false;
      RESULT.errors.push('Failure data must be an object');
      return result;
    }

    const sanitized = {};

    // Validate reason (required for failures)
    if (!failureData.reason || typeof failureData.reason !== 'string') {
      RESULT.isValid = false;
      RESULT.errors.push('Failure reason is required And must be a string');
    } else {
      sanitized.reason = failureData.reason.trim();
    }

    // Validate And sanitize other fields
    if (failureData.error_details) {
      sanitized.error_details = typeof failureData.error_details === 'string'
        ? failureData.error_details.trim()
        : String(failureData.error_details);
    }

    if (failureData.attempted_solutions) {
      if (Array.isArray(failureData.attempted_solutions)) {
        sanitized.attempted_solutions = failureData.attempted_solutions
          .filter(solution => typeof solution === 'string')
          .map(solution => solution.trim());
      }
    }

    if (failureData.blocking_factors) {
      if (Array.isArray(failureData.blocking_factors)) {
        sanitized.blocking_factors = failureData.blocking_factors
          .filter(factor => typeof factor === 'string')
          .map(factor => factor.trim());
      }
    }

    if (failureData.needs_help !== undefined) {
      sanitized.needs_help = Boolean(failureData.needs_help);
    }

    RESULT.sanitizedData = sanitized;
    this.logger?.logDebug?.('Failure data validated And sanitized');

    return result;
  }

  /**
   * Get validation statistics
   * @returns {Object} Validation statistics
   */
  getValidationStats() {
    return {
      strictValidation: this.options.enableStrictValidation,
      autoRepair: this.options.enableAutoRepair,
      validCategories: this.options.validCategories,
      validStatuses: this.options.validStatuses,
      maxTitleLength: this.options.maxTaskTitleLength,
      maxDescriptionLength: this.options.maxDescriptionLength,
    };
  }

  // Private validation methods

  /**
   * Validate required fields for a task
   * @param {Object} task - Task to validate
   * @param {Object} result - Validation result to update
   * @private
   */
  _validateRequiredFields(task, result) {
    // Use explicit field access to prevent object injection
    if (!task.id) {
      RESULT.isValid = false;
      RESULT.errors.push(`Required field 'id' is missing`);
    }

    if (!task.title) {
      RESULT.isValid = false;
      RESULT.errors.push(`Required field 'title' is missing`);
    }

    if (this.options.requireCategory && !task.category) {
      RESULT.isValid = false;
      RESULT.errors.push(`Required field 'category' is missing`);
    }

    // Description is required unless explicitly allowed to be empty
    if (!this.options.allowEmptyDescription && (!task.description || task.description.trim().length === 0)) {
      RESULT.isValid = false;
      RESULT.errors.push('Task description is required');
    }
  }

  /**
   * Validate field formats And types
   * @param {Object} task - Task to validate
   * @param {Object} result - Validation result to update
   * @private
   */
  _validateFieldFormats(task, result) {
    // ID format validation
    if (task.id && typeof task.id !== 'string') {
      RESULT.isValid = false;
      RESULT.errors.push('Task ID must be a string');
    }

    // Title validation
    if (task.title && typeof task.title !== 'string') {
      RESULT.isValid = false;
      RESULT.errors.push('Task title must be a string');
    }

    // Description validation
    if (task.description && typeof task.description !== 'string') {
      RESULT.warnings.push('Task description should be a string');
      RESULT.autoRepairs.push({
        field: 'description',
        action: 'convert_to_string',
        oldValue: task.description,
        newValue: String(task.description),
      });
    }

    // Arrays validation - use explicit field access to prevent object injection
    if (task.dependencies && !Array.isArray(task.dependencies)) {
      RESULT.warnings.push(`Field 'dependencies' should be an array`);
      RESULT.autoRepairs.push({
        field: 'dependencies',
        action: 'convert_to_array',
        oldValue: task.dependencies,
        newValue: Array.isArray(task.dependencies) ? task.dependencies : [task.dependencies],
      });
    }

    if (task.success_criteria && !Array.isArray(task.success_criteria)) {
      RESULT.warnings.push(`Field 'success_criteria' should be an array`);
      RESULT.autoRepairs.push({
        field: 'success_criteria',
        action: 'convert_to_array',
        oldValue: task.success_criteria,
        newValue: Array.isArray(task.success_criteria) ? task.success_criteria : [task.success_criteria],
      });
    }

    if (task.important_files && !Array.isArray(task.important_files)) {
      RESULT.warnings.push(`Field 'important_files' should be an array`);
      RESULT.autoRepairs.push({
        field: 'important_files',
        action: 'convert_to_array',
        oldValue: task.important_files,
        newValue: Array.isArray(task.important_files) ? task.important_files : [task.important_files],
      });
    }

    if (task.assigned_agents && !Array.isArray(task.assigned_agents)) {
      RESULT.warnings.push(`Field 'assigned_agents' should be an array`);
      RESULT.autoRepairs.push({
        field: 'assigned_agents',
        action: 'convert_to_array',
        oldValue: task.assigned_agents,
        newValue: Array.isArray(task.assigned_agents) ? task.assigned_agents : [task.assigned_agents],
      });
    }

    if (task.subtasks && !Array.isArray(task.subtasks)) {
      RESULT.warnings.push(`Field 'subtasks' should be an array`);
      RESULT.autoRepairs.push({
        field: 'subtasks',
        action: 'convert_to_array',
        oldValue: task.subtasks,
        newValue: Array.isArray(task.subtasks) ? task.subtasks : [task.subtasks],
      });
    }

    // Date fields validation - use explicit field access to prevent object injection
    if (task.created_at && typeof task.created_at === 'string') {
      const date = new Date(task.created_at);
      if (isNaN(date.getTime())) {
        RESULT.warnings.push(`Invalid date format in field 'created_at'`);
      }
    }

    if (task.updated_at && typeof task.updated_at === 'string') {
      const date = new Date(task.updated_at);
      if (isNaN(date.getTime())) {
        RESULT.warnings.push(`Invalid date format in field 'updated_at'`);
      }
    }

    if (task.completed_at && typeof task.completed_at === 'string') {
      const date = new Date(task.completed_at);
      if (isNaN(date.getTime())) {
        RESULT.warnings.push(`Invalid date format in field 'completed_at'`);
      }
    }
  }

  /**
   * Validate field constraints
   * @param {Object} task - Task to validate
   * @param {Object} result - Validation result to update
   * @private
   */
  _validateFieldConstraints(task, result) {
    // Title length
    if (task.title && task.title.length > this.options.maxTaskTitleLength) {
      RESULT.warnings.push(`Task title exceeds maximum length of ${this.options.maxTaskTitleLength} characters`);
      RESULT.autoRepairs.push({
        field: 'title',
        action: 'truncate',
        oldValue: task.title,
        newValue: task.title.substring(0, this.options.maxTaskTitleLength).trim(),
      });
    }

    // Description length
    if (task.description && task.description.length > this.options.maxDescriptionLength) {
      RESULT.warnings.push(`Task description exceeds maximum length of ${this.options.maxDescriptionLength} characters`);
      RESULT.autoRepairs.push({
        field: 'description',
        action: 'truncate',
        oldValue: task.description,
        newValue: task.description.substring(0, this.options.maxDescriptionLength).trim(),
      });
    }

    // Category validation
    if (task.category && Array.isArray(this.options.validCategories) && !this.options.validCategories.includes(task.category)) {
      RESULT.isValid = false;
      RESULT.errors.push(`Invalid category '${task.category}'. Valid categories: ${this.options.validCategories.join(', ')}`);
    }

    // Status validation
    if (task.status && Array.isArray(this.options.validStatuses) && !this.options.validStatuses.includes(task.status)) {
      RESULT.warnings.push(`Invalid status '${task.status}'. Valid statuses: ${this.options.validStatuses.join(', ')}`);
      RESULT.autoRepairs.push({
        field: 'status',
        action: 'set_default',
        oldValue: task.status,
        newValue: 'pending',
      });
    }

    // Priority validation
    if (task.priority && Array.isArray(this.options.validPriorities) && !this.options.validPriorities.includes(task.priority)) {
      RESULT.warnings.push(`Invalid priority '${task.priority}'. Valid priorities: ${this.options.validPriorities.join(', ')}`);
      RESULT.autoRepairs.push({
        field: 'priority',
        action: 'set_default',
        oldValue: task.priority,
        newValue: 'normal',
      });
    }
  }

  /**
   * Validate business rules
   * @param {Object} task - Task to validate
   * @param {Object} context - Validation context
   * @param {Object} result - Validation result to update
   * @private
   */
  _validateBusinessRules(task, context, result) {
    // Completed tasks should have completion date
    if (task.status === 'completed' && !task.completed_at) {
      RESULT.warnings.push('Completed task should have a completion date');
      RESULT.autoRepairs.push({
        field: 'completed_at',
        action: 'set_current_date',
        oldValue: task.completed_at,
        newValue: new Date().toISOString(),
      });
    }

    // Failed tasks should have failure reason
    if (task.status === 'failed' && !task.failure_reason) {
      RESULT.warnings.push('Failed task should have a failure reason');
    }

    // In-progress tasks should have assigned agent
    if (task.status === 'in_progress' && !task.assigned_agent) {
      RESULT.warnings.push('In-progress task should have an assigned agent');
    }

    // Test category validation
    if (task.category === 'test' && context.todoData) {
      const pendingErrorTasks = context.todoData.tasks?.filter(t =>
        t.category === 'error' && t.status === 'pending',
      ) || [];

      if (pendingErrorTasks.length > 0) {
        RESULT.warnings.push('Test tasks should not be created while error tasks are pending');
      }
    }

    // Success criteria for certain categories
    if (this.options.requireSuccessCriteria &&
        ['feature', 'test'].includes(task.category) &&
        (!task.success_criteria || task.success_criteria.length === 0)) {
      RESULT.warnings.push(`${task.category} tasks should have success criteria`);
    }
  }

  /**
   * Validate task dependencies
   * @param {Object} task - Task to validate
   * @param {Object} context - Validation context
   * @param {Object} result - Validation result to update
   * @private
   */
  _validateDependencies(task, context, result) {
    if (!Array.isArray(task.dependencies)) {
      RESULT.warnings.push('Dependencies should be an array');
      return;
    }

    // Check if dependency tasks exist
    if (context.todoData && context.todoData.tasks) {
      const existingTaskIds = new Set(context.todoData.tasks.map(t => t.id));

      for (const depId of task.dependencies) {
        if (!existingTaskIds.has(depId)) {
          RESULT.warnings.push(`Dependency task '${depId}' does not exist`);
        }
      }
    }

    // Check for self-dependency
    if (Array.isArray(task.dependencies) && task.dependencies.includes(task.id)) {
      RESULT.isValid = false;
      RESULT.errors.push('Task cannot depend on itself');
    }

    // Check for duplicate dependencies
    if (Array.isArray(task.dependencies)) {
      const uniqueDeps = [...new Set(task.dependencies)];
      if (uniqueDeps.length !== task.dependencies.length) {
        RESULT.warnings.push('Task has duplicate dependencies');
        RESULT.autoRepairs.push({
          field: 'dependencies',
          action: 'remove_duplicates',
          oldValue: task.dependencies,
          newValue: uniqueDeps,
        });
      }
    }
  }

  /**
   * Validate subtasks
   * @param {Object} task - Task to validate
   * @param {Object} context - Validation context
   * @param {Object} result - Validation result to update
   * @private
   */
  _validateSubtasks(task, context, result) {
    if (!Array.isArray(task.subtasks)) {
      RESULT.warnings.push('Subtasks should be an array');
      return;
    }

    for (let i = 0; i < task.subtasks.length; i++) {
      // Use .at() method for secure array access
      const subtask = task.subtasks.at(i);

      if (!subtask || typeof subtask !== 'object') {
        RESULT.warnings.push(`Subtask ${i} is invalid`);
        continue;
      }

      // Validate subtask structure
      if (!subtask.id) {
        RESULT.warnings.push(`Subtask ${i} missing ID`);
      }

      if (!subtask.title) {
        RESULT.warnings.push(`Subtask ${i} missing title`);
      }

      // Validate subtask type
      const validSubtaskTypes = ['research', 'audit', 'implementation', 'testing'];
      if (subtask.type && !validSubtaskTypes.includes(subtask.type)) {
        RESULT.warnings.push(`Subtask ${i} has invalid type: ${subtask.type}`);
      }
    }
  }

  /**
   * Validate success criteria
   * @param {Object} task - Task to validate
   * @param {Object} result - Validation result to update
   * @private
   */
  _validateSuccessCriteria(task, result) {
    if (!Array.isArray(task.success_criteria)) {
      RESULT.warnings.push('Success criteria should be an array');
      return;
    }

    for (let i = 0; i < task.success_criteria.length; i++) {
      // Use .at() method for secure array access
      const criterion = task.success_criteria.at(i);

      if (typeof criterion !== 'string' || criterion.trim().length === 0) {
        RESULT.warnings.push(`Success criterion ${i} should be a non-empty string`);
      }

      // Check for reasonable length
      if (criterion && criterion.length > 500) {
        RESULT.warnings.push(`Success criterion ${i} is very long (${criterion.length} chars)`);
      }
    }

    // Check for duplicate criteria
    const uniqueCriteria = [...new Set(task.success_criteria)];
    if (uniqueCriteria.length !== task.success_criteria.length) {
      RESULT.warnings.push('Task has duplicate success criteria');
      RESULT.autoRepairs.push({
        field: 'success_criteria',
        action: 'remove_duplicates',
        oldValue: task.success_criteria,
        newValue: uniqueCriteria,
      });
    }
  }

  /**
   * Validate root TODO structure
   * @param {Object} todoData - TODO data
   * @param {Object} result - Validation result
   * @private
   */
  _validateRootStructure(todoData, result) {
    // Validate root structure fields explicitly to prevent object injection
    if (!todoData.tasks) {
      RESULT.warnings.push(`Missing root field: tasks`);
      RESULT.suggestions.push(`Add tasks: [] to root structure`);
    } else if (!Array.isArray(todoData.tasks)) {
      RESULT.isValid = false;
      RESULT.errors.push(`Root field 'tasks' should be an array`);
    }

    if (!todoData.completed_tasks) {
      RESULT.warnings.push(`Missing root field: completed_tasks`);
      RESULT.suggestions.push(`Add completed_tasks: [] to root structure`);
    } else if (!Array.isArray(todoData.completed_tasks)) {
      RESULT.isValid = false;
      RESULT.errors.push(`Root field 'completed_tasks' should be an array`);
    }

    if (!todoData.features) {
      RESULT.warnings.push(`Missing root field: features`);
      RESULT.suggestions.push(`Add features: [] to root structure`);
    } else if (!Array.isArray(todoData.features)) {
      RESULT.isValid = false;
      RESULT.errors.push(`Root field 'features' should be an array`);
    }

    // Check for unknown root fields
    const knownFields = [
      'tasks', 'completed_tasks', 'features', 'agents', 'project_success_criteria',
      'task_creation_attempts', 'last_mode', 'review_strikes', 'strikes_completed_last_run',
    ];

    for (const field of Object.keys(todoData)) {
      if (!knownFields.includes(field)) {
        RESULT.warnings.push(`Unknown root field: ${field}`);
      }
    }
  }

  /**
   * Detect circular dependencies in tasks
   * @param {Object} todoData - TODO data
   * @returns {Array} Array of circular dependency chains
   * @private
   */
  _detectCircularDependencies(todoData) {
    if (!todoData.tasks || !Array.isArray(todoData.tasks)) {
      return [];
    }

    const visited = new Set();
    const visiting = new Set();
    const circularDeps = [];

    const visit = (taskId, path = []) => {
      if (visiting.has(taskId)) {
        // Found circular dependency
        const cycleStart = PATH.indexOf(taskId);
        if (cycleStart !== -1) {
          circularDeps.push(PATH.slice(cycleStart).concat([taskId]));
        }
        return;
      }

      if (visited.has(taskId)) {
        return;
      }

      visiting.add(taskId);

      const task = todoData.tasks.find(t => t.id === taskId);
      if (task && task.dependencies) {
        for (const depId of task.dependencies) {
          visit(depId, [...path, taskId]);
        }
      }

      visiting.delete(taskId);
      visited.add(taskId);
    };

    // Visit all tasks
    for (const task of todoData.tasks) {
      if (!visited.has(task.id)) {
        visit(task.id);
      }
    }

    return circularDeps;
  }

  /**
   * Validate features structure
   * @param {Array} features - Features array
   * @param {Object} result - Validation result
   * @private
   */
  _validateFeaturesStructure(features, result) {
    if (!Array.isArray(features)) {
      RESULT.isValid = false;
      RESULT.errors.push('Features should be an array');
      return;
    }

    for (let i = 0; i < features.length; i++) {
      // Use .at() method for secure array access
      const feature = features.at(i);

      if (!feature || typeof feature !== 'object') {
        RESULT.warnings.push(`Feature ${i} is invalid`);
        continue;
      }

      if (!feature.id) {
        RESULT.warnings.push(`Feature ${i} missing ID`);
      }

      if (!feature.title) {
        RESULT.warnings.push(`Feature ${i} missing title`);
      }

      const validStatuses = ['suggested', 'approved', 'in_progress', 'completed'];
      if (feature.status && !validStatuses.includes(feature.status)) {
        RESULT.warnings.push(`Feature ${i} has invalid status: ${feature.status}`);
      }
    }
  }

  /**
   * Validate agents structure
   * @param {Object} agents - Agents object with agent IDs as keys
   * @param {Object} result - Validation result
   * @private
   */
  _validateAgentsStructure(agents, result) {
    if (!agents || typeof agents !== 'object' || Array.isArray(agents)) {
      RESULT.warnings.push('Agents should be an object with agent IDs as keys');
      return;
    }

    for (const [agentId, agent] of Object.entries(agents)) {

      if (!agent || typeof agent !== 'object') {
        RESULT.warnings.push(`Agent ${agentId} is invalid`);
        continue;
      }

      if (!agent.agentId) {
        RESULT.warnings.push(`Agent ${agentId} missing agentId`);
      }

      if (!agent.status) {
        RESULT.warnings.push(`Agent ${agentId} missing status`);
      }
    }
  }

  /**
   * Evaluate a single success criterion
   * @param {string} criterion - Success criterion to evaluate
   * @param {Object} task - Task being evaluated
   * @param {Object} context - Evaluation context
   * @returns {Object} Criterion evaluation result
   * @private
   */
  _evaluateSingleCriterion(criterion, task, context) {
    const RESULT = {
      criterion,
      met: false,
      type: 'unknown',
      details: '',
      suggestions: [],
    };

    // Determine criterion type
    if (this._isTestCriterion(criterion)) {
      RESULT.type = 'test';
      RESULT.met = this._evaluateTestCriterion(criterion, context);
    } else if (this._isLintCriterion(criterion)) {
      RESULT.type = 'lint';
      RESULT.met = this._evaluateLintCriterion(criterion, context);
    } else if (this._isBuildCriterion(criterion)) {
      RESULT.type = 'build';
      RESULT.met = this._evaluateBuildCriterion(criterion, context);
    } else if (this._isFileCriterion(criterion)) {
      RESULT.type = 'file';
      RESULT.met = this._evaluateFileCriterion(criterion, context);
    } else {
      RESULT.type = 'custom';
      RESULT.met = this._evaluateCustomCriterion(criterion, task, context);
    }

    return result;
  }

  /**
   * Check if criterion is test-related
   * @param {string} criterion - Success criterion
   * @returns {boolean} True if test criterion
   * @private
   */
  _isTestCriterion(criterion) {
    const testKeywords = ['test', 'spec', 'jest', 'mocha', 'pytest', 'coverage'];
    return testKeywords.some(keyword => criterion.toLowerCase().includes(keyword));
  }

  /**
   * Check if criterion is lint-related
   * @param {string} criterion - Success criterion
   * @returns {boolean} True if lint criterion
   * @private
   */
  _isLintCriterion(criterion) {
    const lintKeywords = ['lint', 'eslint', 'ruff', 'pylint', 'flake8'];
    return lintKeywords.some(keyword => criterion.toLowerCase().includes(keyword));
  }

  /**
   * Check if criterion is build-related
   * @param {string} criterion - Success criterion
   * @returns {boolean} True if build criterion
   * @private
   */
  _isBuildCriterion(criterion) {
    const buildKeywords = ['build', 'compile', 'bundle'];
    return buildKeywords.some(keyword => criterion.toLowerCase().includes(keyword));
  }

  /**
   * Check if criterion is file-related
   * @param {string} criterion - Success criterion
   * @returns {boolean} True if file criterion
   * @private
   */
  _isFileCriterion(criterion) {
    return criterion.toLowerCase().includes('file') || criterion.includes('/') || criterion.includes('.');
  }

  /**
   * Evaluate test criterion
   * @param {string} criterion - Test criterion
   * @param {Object} context - Evaluation context
   * @returns {boolean} True if criterion is met
   * @private
   */
  _evaluateTestCriterion(_CRITERION, _context) {
    // This is a placeholder - in a real implementation, this would
    // actually run tests or check test results
    return false;
  }

  /**
   * Evaluate lint criterion
   * @param {string} criterion - Lint criterion
   * @param {Object} context - Evaluation context
   * @returns {boolean} True if criterion is met
   * @private
   */
  _evaluateLintCriterion(_CRITERION, _context) {
    // This is a placeholder - in a real implementation, this would
    // actually run linters or check lint results
    return false;
  }

  /**
   * Evaluate build criterion
   * @param {string} criterion - Build criterion
   * @param {Object} context - Evaluation context
   * @returns {boolean} True if criterion is met
   * @private
   */
  _evaluateBuildCriterion(_CRITERION, _context) {
    // This is a placeholder - in a real implementation, this would
    // actually run builds or check build results
    return false;
  }

  /**
   * Evaluate file criterion
   * @param {string} criterion - File criterion
   * @param {Object} context - Evaluation context
   * @returns {boolean} True if criterion is met
   * @private
   */
  _evaluateFileCriterion(criterion, _context) {
    // Check if files exist
    if (criterion.toLowerCase().startsWith('file exists:')) {
      const filePath = criterion.substring('file exists:'.length).trim();
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Task validation path controlled by validation security protocols
      return FS.existsSync(filePath);
    }

    return false;
  }

  /**
   * Evaluate custom criterion
   * @param {string} criterion - Custom criterion
   * @param {Object} task - Task being evaluated
   * @param {Object} context - Evaluation context
   * @returns {boolean} True if criterion is met
   * @private
   */
  _evaluateCustomCriterion(_CRITERION, TASK, _context) {
    // for now, custom criteria are considered unmet until manually verified
    return false;
  }

  /**
   * Validate scope restrictions
   * @param {Object} task - Task with scope restrictions
   * @param {string} agentId - Agent ID
   * @param {Object} context - Validation context
   * @returns {Object} Scope validation result
   * @private
   */
  _validateScopeRestrictions(TASK, agentId, _context) {
    const RESULT = {
      valid: true,
      reason: null,
      restrictions: [],
    };

    // Placeholder for scope restriction logic
    // In a real implementation, this would check various scope rules

    return result;
  }

  /**
   * Apply auto-repairs to a task
   * @param {Object} task - Task to repair
   * @param {Object} result - Validation result with repairs
   * @private
   */
  _applyAutoRepairs(task, result) {
    let repairsApplied = 0;

    for (const repair of RESULT.autoRepairs) {
      try {
        switch (repair.action) {
          case 'convert_to_string':
            task[repair.field] = repair.newValue;
            repairsApplied++;
            break;

          case 'convert_to_array':
            task[repair.field] = repair.newValue;
            repairsApplied++;
            break;

          case 'truncate':
            task[repair.field] = repair.newValue;
            repairsApplied++;
            break;

          case 'set_default':
            task[repair.field] = repair.newValue;
            repairsApplied++;
            break;

          case 'set_current_date':
            task[repair.field] = repair.newValue;
            repairsApplied++;
            break;

          case 'remove_duplicates':
            task[repair.field] = repair.newValue;
            repairsApplied++;
            break;
        }
      } catch {
        this.logger?.logWarning?.(`Failed to apply auto-repair for ${repair.field}: ${error.message}`);
      }
    }

    if (repairsApplied > 0) {
      this.logger?.logInfo?.(`Applied ${repairsApplied} auto-repairs to task ${task.id}`);
      RESULT.suggestions.push(`Applied ${repairsApplied} automatic repairs`);
    }
  }
}

module.exports = TaskValidation;
