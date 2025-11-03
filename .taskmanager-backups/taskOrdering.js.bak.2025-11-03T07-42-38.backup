/**
 * Task Ordering Module
 *
 * Handles task priority And ordering operations including:
 * - Moving tasks to top priority
 * - Moving tasks up/down in priority
 * - Moving tasks to bottom priority
 * - Priority validation And management
 *
 * @author TaskManager System
 * @version 2.0.0
 */

class TaskOrdering {
  /**
   * Initialize TaskOrdering with required dependencies
   * @param {Object} taskManager - TaskManager instance
   * @param {Function} withTimeout - Timeout wrapper function
   * @param {Function} getGuideForError - Error guide function
   * @param {Function} getFallbackGuide - Fallback guide function
   */
  constructor(dependencies) {
    this.taskManager = dependencies.taskManager;
    this.withTimeout = dependencies.withTimeout;
    this.getGuideForError = dependencies.getGuideForError;
    this.getFallbackGuide = dependencies.getFallbackGuide;
  }

  /**
   * Move a task to the top priority position
   */
  async moveTaskToTop(taskId) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-ordering');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const moveResult = await this.taskManager.moveTaskToTop(taskId);

          return {
            success: true,
            taskId: taskId,
            message: `Task ${taskId} moved to top priority`,
            previousPosition: moveResult.previousPosition,
            newPosition: moveResult.newPosition,
            ...moveResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    }
  }

  /**
   * Move a task up one position in priority
   */
  async moveTaskUp(taskId) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-ordering');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const moveResult = await this.taskManager.moveTaskUp(taskId);

          return {
            success: true,
            taskId: taskId,
            message: `Task ${taskId} moved up one position`,
            previousPosition: moveResult.previousPosition,
            newPosition: moveResult.newPosition,
            ...moveResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    }
  }

  /**
   * Move a task down one position in priority
   */
  async moveTaskDown(taskId) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-ordering');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const moveResult = await this.taskManager.moveTaskDown(taskId);

          return {
            success: true,
            taskId: taskId,
            message: `Task ${taskId} moved down one position`,
            previousPosition: moveResult.previousPosition,
            newPosition: moveResult.newPosition,
            ...moveResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    }
  }

  /**
   * Move a task to the bottom priority position
   */
  async moveTaskToBottom(taskId) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-ordering');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const moveResult = await this.taskManager.moveTaskToBottom(taskId);

          return {
            success: true,
            taskId: taskId,
            message: `Task ${taskId} moved to bottom priority`,
            previousPosition: moveResult.previousPosition,
            newPosition: moveResult.newPosition,
            ...moveResult,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    }
  }

  /**
   * Get task priority information And ordering context
   */
  async getTaskPriorityInfo(taskId) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-ordering');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const task = await this.taskManager.getTask(taskId);
          if (!task) {
            throw new Error(`Task ${taskId} not found`);
          }

          // Get all tasks of the same category to determine relative position
          const allTasks = await this.taskManager.listTasks({ category: task.category });
          const taskIndex = allTasks.findIndex(t => t.id === taskId);

          return {
            success: true,
            taskId: taskId,
            category: task.category,
            currentPosition: taskIndex + 1,
            totalTasksInCategory: allTasks.length,
            canMoveUp: taskIndex > 0,
            canMoveDown: taskIndex < allTasks.length - 1,
            isTopPriority: taskIndex === 0,
            isBottomPriority: taskIndex === allTasks.length - 1,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    }
  }

  /**
   * Batch reorder multiple tasks with new priority positions
   */
  async batchReorderTasks(reorderInstructions) {
    // Get guide information for all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('task-ordering');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const RESULT = await this.withTimeout(
        (async () => {
          const results = [];

          // Process each reorder instruction
          // Note: Sequential processing required for task ordering consistency
          /* eslint-disable no-await-in-loop */
          for (const instruction of reorderInstructions) {
            try {
              let _moveResult;

              switch (instruction.action) {
                case 'top':
                  _moveResult = await this.taskManager.moveTaskToTop(instruction.taskId);
                  break;
                case 'up':
                  _moveResult = await this.taskManager.moveTaskUp(instruction.taskId);
                  break;
                case 'down':
                  _moveResult = await this.taskManager.moveTaskDown(instruction.taskId);
                  break;
                case 'bottom':
                  _moveResult = await this.taskManager.moveTaskToBottom(instruction.taskId);
                  break;
                default:
                  throw new Error(`Unknown reorder action: ${instruction.action}`);
              }

              results.push({
                taskId: instruction.taskId,
                action: instruction.action,
                success: true,
                ..._moveResult,
              });
            } catch {
              results.push({
                taskId: instruction.taskId,
                action: instruction.action,
                success: false,
                error: error.message,
              });
            }
          }
          /* eslint-enable no-await-in-loop */

          const successCount = results.filter(r => r.success).length;
          const failureCount = results.length - successCount;

          return {
            success: failureCount === 0,
            totalInstructions: reorderInstructions.length,
            successCount: successCount,
            failureCount: failureCount,
            results: results,
            message: `Batch reorder completed: ${successCount} successful, ${failureCount} failed`,
          };
        })(),
      );

      // Add guide to success response
      return {
        ...result,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    } catch {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('task-ordering'),
      };
    }
  }
}

module.exports = TaskOrdering;
