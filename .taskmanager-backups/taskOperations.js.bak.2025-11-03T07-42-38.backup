/**
 * Task Operations Module
 *
 * Handles all core task operations including:
 * - Creating tasks (regular And error tasks)
 * - Listing And filtering tasks
 * - Claiming tasks with priority handling
 * - Completing And failing tasks
 * - Deleting tasks
 * - Updating task progress
 * - Managing subtasks (create, read, update, delete)
 * - Managing success criteria (create, read, update, delete)
 *
 * @author TaskManager System
 * @version 2.0.0
 */

// Import specialized managers for embedded resources
const _SubtasksManager = require('./subtasksManager');
const _SuccessCriteriaManager = require('./successCriteriaManager');

class TaskOperations {
  /**
   * Initialize TaskOperations with required dependencies
   * @param {Object} taskManager - TaskManager instance
   * @param {Function} withTimeout - Timeout wrapper function
   * @param {Function} getGuideForError - Error guide function
   * @param {Function} getFallbackGuide - Fallback guide function
   * @param {Function} validateScopeRestrictions - Scope validation function
   * @param {Function} validateCompletionData - Completion data validator
   * @param {Function} validateFailureData - Failure data validator
   * @param {Function} validateTaskEvidence - Task evidence validator
   * @param {Function} validateAgentScope - Agent scope validator
   * @param {Function} broadcastTaskCompletion - Task completion broadcaster
   * @param {Function} broadcastTaskFailed - Task failure broadcaster
   */
  constructor(dependencies) {
    this.taskManager = dependencies.taskManager;
    this.withTimeout = dependencies.withTimeout;
    this.getGuideForError = dependencies.getGuideForError;
    this.getFallbackGuide = dependencies.getFallbackGuide;
    this.validateScopeRestrictions = dependencies.validateScopeRestrictions;
    this.validateCompletionData = dependencies.validateCompletionData;
    this.validateFailureData = dependencies.validateFailureData;
    this.validateTaskEvidence = dependencies.validateTaskEvidence;
    this.validateAgentScope = dependencies.validateAgentScope;
    this.broadcastTaskCompletion = dependencies.broadcastTaskCompletion;
    this.broadcastTaskFailed = dependencies.broadcastTaskFailed;
    this.ragOperations = dependencies.ragOperations; // RAG operations for automatic knowledge retrieval

    // Initialize embedded resource managers
    this.subtasksManager = new _SubtasksManager({
      taskManager: this.taskManager,
      withTimeout: this.withTimeout,
      getGuideForError: this.getGuideForError,
      getFallbackGuide: this.getFallbackGuide,
      broadcastSubtaskUpdate: dependencies.broadcastSubtaskUpdate || (() => {}),
    });

    this.successCriteriaManager = new _SuccessCriteriaManager({
      taskManager: this.taskManager,
      withTimeout: this.withTimeout,
      getGuideForError: this.getGuideForError,
      getFallbackGuide: this.getFallbackGuide,
      broadcastCriteriaUpdate: dependencies.broadcastCriteriaUpdate || (() => {}),
    });
  }

  /**
   * List tasks with optional filtering
   */
  async listTasks(filter = {}) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const tasks = await this.taskManager.listTasks(filter);
          return {
            success: true,
            tasks: tasks,
            filter: filter,
            count: tasks.length,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  /**
   * Create a new task with validation And scope restrictions
   */
  async createTask(taskData) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate scope restrictions in task data (if provided)
          let scopeValidationInfo = null;
          if (taskData.scope_restrictions) {
            scopeValidationInfo = this.validateScopeRestrictions(
              taskData.scope_restrictions,
            );
            if (!scopeValidationInfo.isValid) {
              throw new Error(
                `Invalid scope restrictions: ${scopeValidationInfo.errors.join(', ')}`,
              );
            }
          }

          const taskId = await this.taskManager.createTask(taskData);

          const response = {
            success: true,
            taskId,
            task: taskData,
          };

          // Add scope validation information if scope restrictions were provided
          if (scopeValidationInfo) {
            response.scopeInfo = {
              hasRestrictions: true,
              restrictionTypes: scopeValidationInfo.restrictionTypes,
              validationPassed: scopeValidationInfo.isValid,
              message:
                'Task created with enhanced scope validation (files AND folders supported)',
            };
          } else {
            response.scopeInfo = {
              hasRestrictions: false,
              message:
                'Task created without scope restrictions - full access granted',
            };
          }

          return response;
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  /**
   * Create an error task with absolute priority
   */
  async createErrorTask(taskData) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // VALIDATE: Only allow actual error tasks through this method
          if (taskData.category && taskData.category !== 'error') {
            throw new Error(
              `createErrorTask can only be used for error category tasks. ` +
              `Received category: "${taskData.category}". ` +
              `Use createTask() for non-error categories.`,
            );
          }

          // Ensure task has error category for proper prioritization
          const errorTaskData = {
            ...taskData,
            category: 'error', // Force error category for absolute priority
            priority: 'critical', // Set critical priority
          };

          const taskId = await this.taskManager.createTask(errorTaskData);

          return {
            success: true,
            taskId,
            task: errorTaskData,
            message:
              'Error task created with absolute priority - bypasses all feature ordering',
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  /**
   * Claim a task for an agent with priority handling
   * Automatically queries RAG system for relevant lessons And errors
   */
  async claimTask(taskId, agentId, priority = 'normal') {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Get task details before claiming for RAG context
          let ragSuggestions = null;
          try {
            const task = await this.taskManager.getTask(taskId);
            if (task && this.ragOperations) {
              // Query RAG for relevant lessons And errors
              const taskContext = {
                title: task.title,
                description: task.description,
                category: task.category,
              };

              const ragResult = await this.ragOperations.getRelevantLessons(taskContext, {
                includeErrors: true,
                lessonLimit: 5,
                errorLimit: 3,
              });

              if (ragResult.success) {
                ragSuggestions = {
                  relevantLessons: ragResult.relevantLessons,
                  relatedErrors: ragResult.relatedErrors,
                  totalFound: ragResult.totalFound,
                  message: ragResult.message,
                  searchQuery: ragResult.taskContext?.searchQuery,
                };
              }
            }
          } catch {
            // RAG failure should not block task claiming - use silent failure for non-blocking RAG integration
          }

          // Proceed with normal task claiming
          const claimResult = await this.taskManager.claimTask(
            taskId,
            agentId,
            priority,
          );

          const response = {
            success: true,
            ...claimResult,
          };

          // Add RAG suggestions if available
          if (ragSuggestions) {
            response.ragSuggestions = ragSuggestions;
          }

          return response;
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  /**
   * Complete a task with validation And broadcasting
   */
  async completeTask(taskId, completionData = {}) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate completion data structure And evidence requirements
          const validationResult = this.validateCompletionData(completionData);
          if (!validationResult.isValid) {
            throw new Error(
              `Invalid completion data: ${validationResult.errors.join(', ')}`,
            );
          }

          // Validate task evidence if provided - add null check
          if (completionData && (completionData.evidence || completionData.validation)) {
            const evidenceValidation = this.validateTaskEvidence(completionData);
            if (!evidenceValidation.isValid) {
              throw new Error(
                `Invalid task evidence: ${evidenceValidation.errors.join(', ')}`,
              );
            }
          }

          // Get the task before completion for broadcasting
          const task = await this.taskManager.getTask(taskId);

          // Validate agent scope for task completion
          if (task && task.assigned_agent) {
            await this.validateAgentScope(task, task.assigned_agent);
          }

          const completionResult = await this.taskManager.completeTask(
            taskId,
            completionData,
          );

          // Broadcast task completion event for real-time updates
          if (completionResult.success && task) {
            this.broadcastTaskCompletion({
              taskId,
              task,
              completionData,
              timestamp: new Date().toISOString(),
            });
          }

          return {
            success: true,
            ...completionResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  /**
   * Mark a task as failed with detailed failure information
   */
  async failTask(taskId, failureData = {}) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate failure data structure
          const validationResult = this.validateFailureData(failureData);
          if (!validationResult.isValid) {
            throw new Error(
              `Invalid failure data: ${validationResult.errors.join(', ')}`,
            );
          }

          // Get the task before failure for broadcasting
          const task = await this.taskManager.getTask(taskId);

          const failureResult = await this.taskManager.failTask(
            taskId,
            failureData,
          );

          // Broadcast task failure event for real-time updates
          if (failureResult.success && task) {
            this.broadcastTaskFailed({
              taskId,
              task,
              failureData,
              timestamp: new Date().toISOString(),
            });
          }

          return {
            success: true,
            ...failureResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  /**
   * Delete a task from the system
   */
  async deleteTask(taskId) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Get task details before deletion for response
          const task = await this.taskManager.getTask(taskId);

          const deleteResult = await this.taskManager.deleteTask(taskId);

          return {
            success: true,
            taskId,
            deletedTask: {
              id: taskId,
              title: task ? task.title : 'Unknown',
              status: task ? task.status : 'Unknown',
            },
            ...deleteResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  /**
   * Update task progress with incremental status updates
   */
  async updateTaskProgress(taskId, updateData) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-operations');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const progressResult = await this.taskManager.updateTaskProgress(
            taskId,
            updateData,
          );

          return {
            success: true,
            ...progressResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-operations'),
      };
    }
  }

  // ============================================================================
  // SUBTASKS MANAGEMENT METHODS
  // ============================================================================

  /**
   * Create a new subtask within a parent task
   * Delegates to SubtasksManager for comprehensive subtask handling
   */
  createSubtask(taskId, subtaskData) {
    return this.subtasksManager.createSubtask(taskId, subtaskData);
  }

  /**
   * Get all subtasks for a specific parent task
   * Delegates to SubtasksManager with optional filtering
   */
  getSubtasks(taskId, filter = {}) {
    return this.subtasksManager.getSubtasks(taskId, filter);
  }

  /**
   * Update an existing subtask
   * Delegates to SubtasksManager for status And data updates
   */
  updateSubtask(subtaskId, updateData) {
    return this.subtasksManager.updateSubtask(subtaskId, updateData);
  }

  /**
   * Delete a subtask from its parent task
   * Delegates to SubtasksManager with validation And broadcasting
   */
  deleteSubtask(subtaskId) {
    return this.subtasksManager.deleteSubtask(subtaskId);
  }

  // ============================================================================
  // SUCCESS CRITERIA MANAGEMENT METHODS
  // ============================================================================

  /**
   * Add success criteria to a specific task
   * Delegates to SUCCESS_CRITERIA_MANAGER for comprehensive criteria handling
   */
  addSuccessCriteria(taskId, criteria, options = {}) {
    return this.successCriteriaManager.addCriteria(taskId, criteria, options);
  }

  /**
   * Get success criteria for a specific task
   * Delegates to SUCCESS_CRITERIA_MANAGER with template detection
   */
  getSuccessCriteria(taskId) {
    return this.successCriteriaManager.getCriteria(taskId);
  }

  /**
   * Update success criteria for a task (replace all criteria)
   * Delegates to SUCCESS_CRITERIA_MANAGER for complete replacement
   */
  updateSuccessCriteria(taskId, criteria) {
    return this.successCriteriaManager.updateCriteria(taskId, criteria);
  }

  /**
   * Delete a specific success criterion from a task
   * Delegates to SUCCESS_CRITERIA_MANAGER for targeted removal
   */
  deleteSuccessCriterion(taskId, criterionText) {
    return this.successCriteriaManager.deleteCriterion(taskId, criterionText);
  }

  /**
   * Get available project-wide success criteria templates
   * Delegates to SUCCESS_CRITERIA_MANAGER for template management
   */
  getProjectWideTemplates() {
    return this.successCriteriaManager.getProjectWideTemplates();
  }

  /**
   * Apply a project-wide template to a task
   * Delegates to SUCCESS_CRITERIA_MANAGER for template application
   */
  applyProjectTemplate(taskId, templateName, replace = false) {
    return this.successCriteriaManager.applyProjectTemplate(taskId, templateName, replace);
  }

  /**
   * Set project-wide success criteria configuration
   * Delegates to SUCCESS_CRITERIA_MANAGER for project-wide criteria management
   */
  setProjectCriteria(criteriaData) {
    return this.successCriteriaManager.setProjectCriteria(criteriaData);
  }

  /**
   * Validate task against success criteria
   * Delegates to SUCCESS_CRITERIA_MANAGER for criteria validation
   */
  validateCriteria(taskId, validationType = 'full', evidence = {}) {
    return this.successCriteriaManager.validateCriteria(taskId, {
      validationType,
      evidence,
      generateReport: true,
    });
  }

  /**
   * Get validation report for task criteria
   * Delegates to SUCCESS_CRITERIA_MANAGER for report generation
   */
  getCriteriaReport(taskId) {
    return this.successCriteriaManager.generateCriteriaReport(taskId);
  }
}

module.exports = TaskOperations;
