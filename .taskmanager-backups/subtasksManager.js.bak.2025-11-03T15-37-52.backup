
const { loggers } = require('../../logger');
/**
 * Subtasks Manager Module
 *
 * Handles all subtask operations for embedded subtasks within tasks including:
 * - Creating subtasks (research, audit, implementation subtasks)
 * - Listing And filtering subtasks
 * - Updating subtask status And progress
 * - Deleting subtasks
 * - Validating subtask dependencies And relationships
 * - Managing subtask lifecycle And completion
 * - Comprehensive security controls And data validation
 * - Authorization controls And audit trail logging
 *
 * @author TaskManager System
 * @version 2.0.0
 */

const _SubtasksSecurityEnhancer = require('./subtasksSecurityEnhancer');

class SubtasksManager {
  /**
   * Initialize SubtasksManager with required dependencies
   * @param {Object} dependencies - Dependency injection object
   * @param {Object} dependencies.taskManager - TaskManager instance
   * @param {Function} dependencies.withTimeout - Timeout wrapper function
   * @param {Function} dependencies.getGuideForError - Error guide function
   * @param {Function} dependencies.getFallbackGuide - Fallback guide function
   * @param {Function} dependencies.validateSubtask - Subtask validation function
   * @param {Function} dependencies.validateTaskExists - Task existence validator
   * @param {Function} dependencies.broadcastSubtaskUpdate - Subtask update broadcaster
   */
  constructor(dependencies) {
    this.taskManager = dependencies.taskManager;
    this.withTimeout = dependencies.withTimeout;
    this.getGuideForError = dependencies.getGuideForError;
    this.getFallbackGuide = dependencies.getFallbackGuide;
    this.validateSubtask = dependencies.validateSubtask || this._defaultSubtaskValidator.bind(this);
    this.validateTaskExists = dependencies.validateTaskExists || this._defaultTaskExistsValidator.bind(this);
    this.broadcastSubtaskUpdate = dependencies.broadcastSubtaskUpdate || (() => {});

    // Initialize comprehensive security controls for embedded subtasks system
    this.securityEnhancer = new _SubtasksSecurityEnhancer(dependencies.logger);

    this.log('info', 'SubtasksManager initialized with comprehensive security controls', {
      securityFeatures: ['validation', 'authorization', 'audit_trail', 'sanitization'],
      version: '2.0.0',
    });
  }

  /**
   * Create a new subtask within a parent task with comprehensive security controls
   * @param {string} taskId - Parent task ID
   * @param {Object} subtaskData - Subtask data object
   * @param {string} subtaskData.type - Subtask type (research, audit, implementation, etc.)
   * @param {string} subtaskData.title - Subtask title
   * @param {string} subtaskData.description - Detailed description
   * @param {number} [subtaskData.estimated_hours] - Estimated completion hours
   * @param {boolean} [subtaskData.prevents_implementation] - Whether subtask blocks implementation
   * @param {boolean} [subtaskData.prevents_completion] - Whether subtask blocks task completion
   * @param {string} agentId - Agent ID for authorization And audit trail
   * @returns {Promise<Object>} Response with created subtask or error
   */
  async createSubtask(taskId, subtaskData, agentId = 'unknown') {
    // Get guide information for all responses
    let guide = null;
    try {
      guide = await this.getGuideForError('subtasks-operations');
    } catch {
      // Continue with _operationwithout guide if guide fails
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Validate parent task exists
          const taskExists = await this.validateTaskExists(taskId);
          if (!taskExists.valid) {
            return {
              success: false,
              error: `Parent task ${taskId} not found or invalid`,
              errorCode: 'PARENT_TASK_NOT_FOUND',
            };
          }

          // Enhanced security validation with comprehensive controls
          const validationResult = await this.securityEnhancer.validateSubtaskWithSecurity(
            subtaskData,
            agentId,
            'create',
          );
          if (!validationResult.valid) {
            return {
              success: false,
              error: `Security validation failed: ${validationResult.errors.join(', ')}`,
              errorCode: 'SECURITY_VALIDATION_FAILED',
              validationId: validationResult.validationId,
            };
          }

          // Use sanitized data for subtask creation
          const sanitizedData = validationResult.sanitizedData || subtaskData;

          // Generate unique subtask ID
          const subtaskId = this._generateSubtaskId(sanitizedData.type);

          // Create subtask object with sanitized data And security metadata
          const subtask = {
            id: subtaskId,
            type: sanitizedData.type,
            title: sanitizedData.title,
            description: sanitizedData.description,
            status: 'pending',
            estimated_hours: sanitizedData.estimated_hours || 1,
            prevents_implementation: sanitizedData.prevents_implementation || false,
            prevents_completion: sanitizedData.prevents_completion || false,
            created_at: new Date().toISOString(),
            created_by: agentId,
            security_validated: true,
            validation_id: validationResult.validationId,
            ...(sanitizedData.research_locations && { research_locations: sanitizedData.research_locations }),
            ...(sanitizedData.deliverables && { deliverables: sanitizedData.deliverables }),
            ...(sanitizedData.success_criteria && { success_criteria: sanitizedData.success_criteria }),
          };

          // Add subtask to parent task
          const addResult = await this.taskManager.addSubtaskToTask(taskId, subtask);
          if (!addResult.success) {
            return {
              success: false,
              error: `Failed to add subtask to parent task: ${addResult.error}`,
              errorCode: 'SUBTASK_CREATION_FAILED',
            };
          }

          // Log audit trail for subtask creation
          this.securityEnhancer.logAuditTrail(agentId, 'create', 'SUBTASK_CREATED', {
            taskId,
            subtaskId,
            subtaskType: subtask.type,
            title: subtask.title,
            prevents_implementation: subtask.prevents_implementation,
            prevents_completion: subtask.prevents_completion,
            validation_id: validationResult.validationId,
          });

          // Broadcast subtask creation
          await this.broadcastSubtaskUpdate({
            action: 'created',
            taskId,
            subtaskId,
            subtask,
            agentId,
            security_validated: true,
          });

          this.log('info', 'Subtask created successfully with security validation', {
            taskId,
            subtaskId,
            agentId,
            subtaskType: subtask.type,
            validation_id: validationResult.validationId,
          });

          return {
            success: true,
            subtask,
            taskId,
            message: 'Subtask created successfully with security validation',
            security: {
              validated: true,
              validation_id: validationResult.validationId,
              created_by: agentId,
            },
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'SUBTASK_OPERATION_FAILED',
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    }
  }

  /**
   * Get all subtasks for a specific parent task
   * @param {string} taskId - Parent task ID
   * @param {Object} [filter] - Optional filtering options
   * @param {string} [filter.status] - Filter by subtask status
   * @param {string} [filter.type] - Filter by subtask type
   * @returns {Promise<Object>} Response with subtasks array or error
   */
  async getSubtasks(taskId, filter = {}) {
    let guide = null;
    try {
      guide = await this.getGuideForError('subtasks-operations');
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

          let subtasks = taskData.subtasks || [];

          // Apply filters
          if (filter.status) {
            subtasks = subtasks.filter(st => st.status === filter.status);
          }
          if (filter.type) {
            subtasks = subtasks.filter(st => st.type === filter.type);
          }

          return {
            success: true,
            subtasks,
            taskId,
            count: subtasks.length,
            filter,
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'SUBTASKS_RETRIEVAL_FAILED',
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    }
  }

  /**
   * Update an existing subtask
   * @param {string} subtaskId - Subtask ID to update
   * @param {Object} updateData - Data to update
   * @param {string} [updateData.status] - New status
   * @param {string} [updateData.description] - Updated description
   * @param {number} [updateData.estimated_hours] - Updated time estimate
   * @returns {Promise<Object>} Response with updated subtask or error
   */
  async updateSubtask(subtaskId, updateData) {
    let guide = null;
    try {
      guide = await this.getGuideForError('subtasks-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Find parent task And subtask
          const { taskId, subtask } = await this._findSubtaskByIdAcrossTasks(subtaskId);
          if (!subtask) {
            return {
              success: false,
              error: `Subtask ${subtaskId} not found`,
              errorCode: 'SUBTASK_NOT_FOUND',
            };
          }

          // Validate update data
          const allowedUpdates = ['status', 'description', 'estimated_hours', 'completed_by'];
          const updateKeys = Object.keys(updateData);
          const invalidKeys = updateKeys.filter(key => !allowedUpdates.includes(key));

          if (invalidKeys.length > 0) {
            return {
              success: false,
              error: `Invalid update fields: ${invalidKeys.join(', ')}. Allowed: ${allowedUpdates.join(', ')}`,
              errorCode: 'INVALID_UPDATE_FIELDS',
            };
          }

          // Apply updates
          const updatedSubtask = { ...subtask };

          // Security: Use explicit whitelist to prevent object injection
          if (updateKeys.includes('status') && updateData.status !== undefined) {
            updatedSubtask.status = updateData.status;
          }
          if (updateKeys.includes('description') && updateData.description !== undefined) {
            updatedSubtask.description = updateData.description;
          }
          if (updateKeys.includes('estimated_hours') && updateData.estimated_hours !== undefined) {
            updatedSubtask.estimated_hours = updateData.estimated_hours;
          }
          if (updateKeys.includes('completed_by') && updateData.completed_by !== undefined) {
            updatedSubtask.completed_by = updateData.completed_by;
          }

          // Add completion timestamp if status is completed
          if (updateData.status === 'completed' && subtask.status !== 'completed') {
            updatedSubtask.completed_at = new Date().toISOString();
          }

          // Update subtask in parent task
          const updateResult = await this.taskManager.updateSubtaskInTask(taskId, subtaskId, updatedSubtask);
          if (!updateResult.success) {
            return {
              success: false,
              error: `Failed to update subtask: ${updateResult.error}`,
              errorCode: 'SUBTASK_UPDATE_FAILED',
            };
          }

          // Broadcast subtask update
          await this.broadcastSubtaskUpdate({
            action: 'updated',
            taskId,
            subtaskId,
            subtask: updatedSubtask,
            changes: updateData,
          });

          return {
            success: true,
            subtask: updatedSubtask,
            taskId,
            message: 'Subtask updated successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'SUBTASK_UPDATE_OPERATION_FAILED',
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    }
  }

  /**
   * Delete a subtask from its parent task
   * @param {string} subtaskId - Subtask ID to delete
   * @returns {Promise<Object>} Response confirming deletion or error
   */
  async deleteSubtask(subtaskId) {
    let guide = null;
    try {
      guide = await this.getGuideForError('subtasks-operations');
    } catch {
      // Continue without guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          // Find parent task And subtask
          const { taskId, subtask } = await this._findSubtaskByIdAcrossTasks(subtaskId);
          if (!subtask) {
            return {
              success: false,
              error: `Subtask ${subtaskId} not found`,
              errorCode: 'SUBTASK_NOT_FOUND',
            };
          }

          // Check if subtask can be deleted (e.g., not completed or in progress)
          if (subtask.status === 'in_progress') {
            return {
              success: false,
              error: 'Cannot delete subtask That is currently in progress',
              errorCode: 'SUBTASK_IN_PROGRESS',
            };
          }

          // Remove subtask from parent task
          const deleteResult = await this.taskManager.removeSubtaskFromTask(taskId, subtaskId);
          if (!deleteResult.success) {
            return {
              success: false,
              error: `Failed to delete subtask: ${deleteResult.error}`,
              errorCode: 'SUBTASK_DELETION_FAILED',
            };
          }

          // Broadcast subtask deletion
          await this.broadcastSubtaskUpdate({
            action: 'deleted',
            taskId,
            subtaskId,
            subtask,
          });

          return {
            success: true,
            subtaskId,
            taskId,
            message: 'Subtask deleted successfully',
          };
        })(),
      );

      return {
        ...result,
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        errorCode: 'SUBTASK_DELETE_OPERATION_FAILED',
        guide: guide || this.getFallbackGuide('subtasks-operations'),
      };
    }
  }

  /**
   * Private method to generate unique subtask ID
   * @param {string} type - Subtask type
   * @returns {string} Generated subtask ID
   */
  _generateSubtaskId(type) {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15);
    return `${type}_${timestamp}_${random}`;
  }

  /**
   * Private method to find subtask by ID across all tasks
   * @param {string} subtaskId - Subtask ID to find
   * @returns {Promise<Object>} Object with taskId And subtask, or null values if not found
   */
  async _findSubtaskByIdAcrossTasks(subtaskId) {
    try {
      const allTasks = await this.taskManager.listTasks({});

      for (const task of allTasks) {
        if (task.subtasks && task.subtasks.length > 0) {
          const subtask = task.subtasks.find(st => st.id === subtaskId);
          if (subtask) {
            return { taskId: task.id, subtask };
          }
        }
      }

      return { taskId: null, subtask: null };
    } catch {
      return { taskId: null, subtask: null };
    }
  }

  /**
   * Default subtask validator
   * @param {Object} subtaskData - Subtask data to validate
   * @returns {Object} Validation result
   */
  _defaultSubtaskValidator(subtaskData) {
    const errors = [];

    if (!subtaskData.type) {errors.push('Subtask type is required');}
    if (!subtaskData.title) {errors.push('Subtask title is required');}
    if (!subtaskData.description) {errors.push('Subtask description is required');}

    const validTypes = ['research', 'audit', 'implementation', 'testing', 'documentation', 'review'];
    if (subtaskData.type && !validTypes.includes(subtaskData.type)) {
      errors.push(`Invalid subtask type. Must be one of: ${validTypes.join(', ')}`);
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
   * Enhanced updateSubtask with security controls
   * @param {string} subtaskId - Subtask ID to update
   * @param {Object} updateData - Update data
   * @param {string} agentId - Agent performing the update
   * @returns {Promise<Object>} Update result
   */
  async updateSubtaskWithSecurity(subtaskId, updateData, agentId = 'unknown') {
    try {
      // Validate update data with security controls
      const validationResult = await this.securityEnhancer.validateSubtaskWithSecurity(
        updateData,
        agentId,
        'update',
      );

      if (!validationResult.valid) {
        this.securityEnhancer.logAuditTrail(agentId, 'update', 'SUBTASK_UPDATE_DENIED', {
          subtaskId,
          reason: validationResult.errors.join(', '),
          validation_id: validationResult.validationId,
        });

        return {
          success: false,
          error: `Security validation failed: ${validationResult.errors.join(', ')}`,
          errorCode: 'SECURITY_VALIDATION_FAILED',
          validation_id: validationResult.validationId,
        };
      }

      // Use the base updateSubtask method with sanitized data
      const RESULT = await this.updateSubtask(subtaskId, validationResult.sanitizedData || updateData);

      if (result.success) {
        // Log successful update
        this.securityEnhancer.logAuditTrail(agentId, 'update', 'SUBTASK_UPDATED', {
          subtaskId,
          updatedFields: Object.keys(updateData),
          validation_id: validationResult.validationId,
        });

        this.log('info', 'Subtask updated with security validation', {
          subtaskId,
          agentId,
          validation_id: validationResult.validationId,
        });
      }

      return {
        ...result,
        security: {
          validated: true,
          validation_id: validationResult.validationId,
          updated_by: agentId,
        },
      };

    } catch {
      this.log('error', 'Secure subtask update failed', {
        subtaskId,
        agentId,
        error: error.message,
      });

      return {
        success: false,
        error: 'Secure subtask update failed',
        errorCode: 'SECURE_UPDATE_ERROR',
      };
    }
  }

  /**
   * Enhanced deleteSubtask with security controls
   * @param {string} subtaskId - Subtask ID to delete
   * @param {string} agentId - Agent performing the deletion
   * @returns {Promise<Object>} Deletion result
   */
  async deleteSubtaskWithSecurity(subtaskId, agentId = 'unknown') {
    try {
      // Authorization check for deletion
      const authResult = this.securityEnhancer.authorizeOperation(agentId, 'delete', { subtaskId });
      if (!authResult.authorized) {
        this.securityEnhancer.logUnauthorizedAccess(agentId, 'delete', authResult.reason);
        return {
          success: false,
          error: authResult.error,
          errorCode: 'UNAUTHORIZED_DELETE',
        };
      }

      // Use the base deleteSubtask method
      const RESULT = await this.deleteSubtask(subtaskId);

      if (result.success) {
        // Log successful deletion
        this.securityEnhancer.logAuditTrail(agentId, 'delete', 'SUBTASK_DELETED', {
          subtaskId,
          deleted_by: agentId,
        });

        this.log('info', 'Subtask deleted with security authorization', {
          subtaskId,
          agentId,
        });
      }

      return {
        ...result,
        security: {
          authorized: true,
          deleted_by: agentId,
        },
      };

    } catch {
      this.log('error', 'Secure subtask deletion failed', {
        subtaskId,
        agentId,
        error: error.message,
      });

      return {
        success: false,
        error: 'Secure subtask deletion failed',
        errorCode: 'SECURE_DELETE_ERROR',
      };
    }
  }

  /**
   * Get security audit trail for subtasks
   * @param {Object} filter - Filter criteria
   * @returns {Array} Audit trail entries
   */
  getSecurityAuditTrail(filter = {}) {
    return this.securityEnhancer.getAuditTrail(filter);
  }

  /**
   * Get security statistics
   * @returns {Object} Security statistics
   */
  getSecurityStats() {
    return this.securityEnhancer.getSecurityStats();
  }

  /**
   * Log message with appropriate level
   * @param {string} level - Log level
   * @param {string} message - Log message
   * @param {Object} metadata - Additional metadata
   */
  log(level, message, metadata = {}) {
    if (this.logger) {
      // eslint-disable-next-line security/detect-object-injection -- Safe logger method access with validated level parameter
      this.logger[level](message, metadata);
      loggers.stopHook.log(`[${level.toUpperCase()}] ${message}`, metadata);

      loggers.app.info(`[${level.toUpperCase()}] ${message}`, metadata);
    }
  }
}

module.exports = SubtasksManager;
