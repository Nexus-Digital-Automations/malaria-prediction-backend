/**
 * TaskIndexing - High-Performance Task Indexing And Lookup Module
 *
 * === OVERVIEW ===
 * Provides high-performance indexing system for tasks, subtasks, And success criteria
 * with O(1) lookup capabilities. This module optimizes TaskManager performance by
 * maintaining specialized indexes And caches for fast data retrieval.
 *
 * === KEY FEATURES ===
 * • O(1) task And subtask lookups by ID
 * • Category-based indexing for fast filtering
 * • Success criteria caching with inheritance
 * • Research And audit task specialized indexes
 * • Automatic index invalidation on data changes
 * • Performance-optimized rebuild algorithms
 *
 * @fileoverview High-performance indexing And lookup system for TaskManager
 * @author TaskManager System
 * @version 2.0.0
 * @since 2024-01-01
 */

const { loggers } = require('../logger');

class TaskIndexing {
  /**
   * Initialize TaskIndexing with performance monitor integration
   * @param {Object} performanceMonitor - Performance monitoring instance
   * @param {Object} options - Configuration options
   */
  constructor(performanceMonitor = null, options = {}) {
    this.performanceMonitor = performanceMonitor;
    this.logger = loggers.taskManager;

    // Task indexing system
    this._taskIndex = null;
    this._lastIndexTime = 0;
    this._indexingEnabled = options.enableIndexing !== false;

    // Success criteria caching system
    this._criteriaCache = null;
    this._lastCriteriaTime = 0;
    this._criteriaInheritance = options.enableCriteriaInheritance !== false;

    // Cache invalidation tracking
    this._lastDataModified = 0;

    this.logger.info('TaskIndexing system initialized');
  }

  /**
   * Build comprehensive task index for O(1) lookups
   * @param {Object} todoData - TODO data to index
   * @returns {Object} Task index structure
   */
  buildTaskIndex(todoData) {
    if (!this._indexingEnabled) {
      this.logger.debug('Task indexing disabled, skipping index build');
      return null;
    }

    const startTime = Date.now();

    // Check if index is still valid
    if (this._taskIndex && this._lastDataModified <= this._lastIndexTime) {
      this.performanceMonitor?.recordCacheHit(true, 'taskIndex');
      return this._taskIndex;
    }

    this.logger.debug('Building comprehensive task index');

    this._taskIndex = {
      byId: new Map(),
      byCategory: new Map(),
      byStatus: new Map(),
      byPriority: new Map(),
      byParent: new Map(),
      subtasks: new Map(),
      researchTasks: new Map(),
      auditTasks: new Map(),
      byAgent: new Map(),
      dependents: new Map(), // Tasks That depend on this task
      dependencies: new Map(), // Tasks this task depends on
    };

    // Index main tasks
    if (todoData.tasks && Array.isArray(todoData.tasks)) {
      for (const task of todoData.tasks) {
        this._indexTask(task);
      }
    }

    this._lastIndexTime = Date.now();
    const duration = Date.now() - startTime;

    // Record performance metrics
    this.performanceMonitor?.recordQueryTime('buildTaskIndex', duration);
    this.performanceMonitor?.recordCacheHit(false, 'taskIndex');

    this.logger.info(`Task index built with ${this._taskIndex.byId.size} tasks in ${duration}ms`);
    return this._taskIndex;
  }

  /**
   * Build success criteria cache with inheritance support
   * @param {Object} todoData - TODO data to cache criteria from
   * @returns {Map} Success criteria cache
   */
  buildSuccessCriteriaCache(todoData) {
    const startTime = Date.now();

    // Check if cache is still valid
    if (this._criteriaCache && this._lastDataModified <= this._lastCriteriaTime) {
      this.performanceMonitor?.recordCacheHit(true, 'successCriteria');
      return this._criteriaCache;
    }

    this.logger.debug('Building success criteria cache');

    this._criteriaCache = new Map();

    // Cache project-wide criteria
    if (todoData.project_success_criteria && Array.isArray(todoData.project_success_criteria)) {
      this._criteriaCache.set('__project_wide__', new Set(todoData.project_success_criteria));
    }

    // Cache task-specific criteria
    if (todoData.tasks && Array.isArray(todoData.tasks)) {
      for (const task of todoData.tasks) {
        this._indexTaskCriteria(task);
      }
    }

    this._lastCriteriaTime = Date.now();
    const duration = Date.now() - startTime;

    // Record performance metrics
    this.performanceMonitor?.recordQueryTime('buildSuccessCriteriaCache', duration);
    this.performanceMonitor?.recordCacheHit(false, 'successCriteria');

    this.logger.debug(`Success criteria cache built in ${duration}ms`);
    return this._criteriaCache;
  }

  /**
   * Get effective success criteria for a task (includes inheritance)
   * @param {string} taskId - Task ID to get criteria for
   * @param {Object} todoData - TODO data for criteria lookup
   * @returns {Set} Set of effective success criteria
   */
  getEffectiveCriteria(taskId, todoData) {
    const startTime = Date.now();
    const cache = this.buildSuccessCriteriaCache(todoData);

    const taskCriteria = cache.get(taskId) || new Set();
    const RESULT = new Set([...taskCriteria]);

    // Add project-wide criteria if inheritance is enabled
    if (this._criteriaInheritance) {
      const projectCriteria = cache.get('__project_wide__') || new Set();
      for (const criterion of projectCriteria) {
        RESULT.add(criterion);
      }
    }

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getEffectiveCriteria', duration);
    this.performanceMonitor?.recordCacheHit(cache.has(taskId), 'effectiveCriteria');

    return result;
  }

  /**
   * Get subtasks for a parent task with O(1) lookup
   * @param {string} parentTaskId - Parent task ID
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of subtasks
   */
  getSubtasksOptimized(parentTaskId, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      this.logger.warn('Task indexing disabled, using fallback subtask lookup');
      return this._getFallbackSubtasks(parentTaskId, todoData);
    }

    const parentTask = index.byId.get(parentTaskId);
    const RESULT = parentTask?.subtasks || [];

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getSubtasksOptimized', duration);
    this.performanceMonitor?.recordCacheHit(index.byId.has(parentTaskId), 'subtasks');

    return result;
  }

  /**
   * Get subtask by ID with O(1) lookup
   * @param {string} subtaskId - Subtask ID
   * @param {Object} todoData - TODO data for indexing
   * @returns {Object|null} Subtask object with parent information
   */
  getSubtaskById(subtaskId, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      this.logger.warn('Task indexing disabled, using fallback subtask lookup');
      return this._getFallbackSubtaskById(subtaskId, todoData);
    }

    const RESULT = index.subtasks.get(subtaskId);

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getSubtaskById', duration);
    this.performanceMonitor?.recordCacheHit(!!result, 'subtaskById');

    return result || null;
  }

  /**
   * Get research tasks with optimized lookup
   * @param {string} parentTaskId - Parent task ID (optional)
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of research tasks
   */
  getResearchTasksOptimized(parentTaskId, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      this.logger.warn('Task indexing disabled, using fallback research lookup');
      return this._getFallbackResearchTasks(parentTaskId, todoData);
    }

    let result;
    if (parentTaskId) {
      const parentTask = index.byId.get(parentTaskId);
      result = (parentTask?.subtasks || []).filter(subtask => subtask.type === 'research');
    } else {
      result = Array.from(index.researchTasks.values());
    }

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getResearchTasksOptimized', duration);
    this.performanceMonitor?.recordCacheHit(!!index.researchTasks.size, 'researchTasks');

    return result;
  }

  /**
   * Get audit tasks with optimized lookup
   * @param {string} parentTaskId - Parent task ID (optional)
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of audit tasks
   */
  getAuditTasksOptimized(parentTaskId, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      this.logger.warn('Task indexing disabled, using fallback audit lookup');
      return this._getFallbackAuditTasks(parentTaskId, todoData);
    }

    let result;
    if (parentTaskId) {
      const parentTask = index.byId.get(parentTaskId);
      result = (parentTask?.subtasks || []).filter(subtask => subtask.type === 'audit');
    } else {
      result = Array.from(index.auditTasks.values());
    }

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getAuditTasksOptimized', duration);
    this.performanceMonitor?.recordCacheHit(!!index.auditTasks.size, 'auditTasks');

    return result;
  }

  /**
   * Get tasks by category with O(1) lookup
   * @param {string} category - Task category
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of tasks in the category
   */
  getTasksByCategory(category, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      return this._getFallbackTasksByCategory(category, todoData);
    }

    const RESULT = index.byCategory.get(category) || [];

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getTasksByCategory', duration);

    return result;
  }

  /**
   * Get tasks by status with O(1) lookup
   * @param {string} status - Task status
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of tasks with the status
   */
  getTasksByStatus(status, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      return this._getFallbackTasksByStatus(status, todoData);
    }

    const RESULT = index.byStatus.get(status) || [];

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getTasksByStatus', duration);

    return result;
  }

  /**
   * Get tasks assigned to an agent
   * @param {string} agentId - Agent ID
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of tasks assigned to the agent
   */
  getTasksByAgent(agentId, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      return this._getFallbackTasksByAgent(agentId, todoData);
    }

    const RESULT = index.byAgent.get(_agentId) || [];

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getTasksByAgent', duration);

    return result;
  }

  /**
   * Get task dependencies (tasks this task depends on)
   * @param {string} taskId - Task ID
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of dependency tasks
   */
  getTaskDependencies(taskId, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      return this._getFallbackTaskDependencies(taskId, todoData);
    }

    const RESULT = index.dependencies.get(taskId) || [];

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getTaskDependencies', duration);

    return result;
  }

  /**
   * Get task dependents (tasks That depend on this task)
   * @param {string} taskId - Task ID
   * @param {Object} todoData - TODO data for indexing
   * @returns {Array} Array of dependent tasks
   */
  getTaskDependents(taskId, todoData) {
    const startTime = Date.now();
    const index = this.buildTaskIndex(todoData);

    if (!index) {
      return this._getFallbackTaskDependents(taskId, todoData);
    }

    const RESULT = index.dependents.get(taskId) || [];

    // Record performance metrics
    const duration = Date.now() - startTime;
    this.performanceMonitor?.recordQueryTime('getTaskDependents', duration);

    return result;
  }

  /**
   * Invalidate all indexes to force rebuild on next access
   * @param {number} dataModifiedTime - Timestamp when data was modified
   */
  invalidateIndexes(dataModifiedTime = Date.now()) {
    this._lastDataModified = dataModifiedTime;
    this._taskIndex = null;
    this._criteriaCache = null;
    this._lastIndexTime = 0;
    this._lastCriteriaTime = 0;

    this.logger.debug('All indexes invalidated');
  }

  /**
   * Get indexing statistics
   * @returns {Object} Indexing statistics
   */
  getIndexingStats() {
    const stats = {
      enabled: this._indexingEnabled,
      taskIndexValid: this._taskIndex !== null,
      criteriaIndexValid: this._criteriaCache !== null,
      lastIndexTime: this._lastIndexTime,
      lastCriteriaTime: this._lastCriteriaTime,
      lastDataModified: this._lastDataModified,
    };

    if (this._taskIndex) {
      stats.taskIndex = {
        totalTasks: this._taskIndex.byId.size,
        totalSubtasks: this._taskIndex.subtasks.size,
        researchTasks: this._taskIndex.researchTasks.size,
        auditTasks: this._taskIndex.auditTasks.size,
        categories: this._taskIndex.byCategory.size,
        statuses: this._taskIndex.byStatus.size,
      };
    }

    if (this._criteriaCache) {
      stats.criteriaCache = {
        totalEntries: this._criteriaCache.size,
        hasProjectCriteria: this._criteriaCache.has('__project_wide__'),
      };
    }

    return stats;
  }

  /**
   * Index a single task And its subtasks
   * @param {Object} task - Task to index
   * @private
   */
  _indexTask(task) {
    if (!task || !task.id) {return;}

    // Core task indexing
    this._taskIndex.byId.set(task.id, task);

    // Category indexing
    if (task.category) {
      if (!this._taskIndex.byCategory.has(task.category)) {
        this._taskIndex.byCategory.set(task.category, []);
      }
      this._taskIndex.byCategory.get(task.category).push(task);
    }

    // Status indexing
    if (task.status) {
      if (!this._taskIndex.byStatus.has(task.status)) {
        this._taskIndex.byStatus.set(task.status, []);
      }
      this._taskIndex.byStatus.get(task.status).push(task);
    }

    // Priority indexing
    if (task.priority) {
      if (!this._taskIndex.byPriority.has(task.priority)) {
        this._taskIndex.byPriority.set(task.priority, []);
      }
      this._taskIndex.byPriority.get(task.priority).push(task);
    }

    // Agent indexing
    if (task.assigned_agent) {
      if (!this._taskIndex.byAgent.has(task.assigned_agent)) {
        this._taskIndex.byAgent.set(task.assigned_agent, []);
      }
      this._taskIndex.byAgent.get(task.assigned_agent).push(task);
    }

    // Dependency indexing
    if (task.dependencies && Array.isArray(task.dependencies)) {
      this._taskIndex.dependencies.set(task.id, task.dependencies);

      // Build reverse dependency map
      for (const depId of task.dependencies) {
        if (!this._taskIndex.dependents.has(depId)) {
          this._taskIndex.dependents.set(depId, []);
        }
        this._taskIndex.dependents.get(depId).push(task.id);
      }
    }

    // Index subtasks
    if (task.subtasks && Array.isArray(task.subtasks)) {
      for (const subtask of task.subtasks) {
        if (subtask.id) {
          this._taskIndex.subtasks.set(subtask.id, {
            ...subtask,
            parentId: task.id,
            parentTask: task,
          });

          // Special indexing for research And audit subtasks
          if (subtask.type === 'research') {
            this._taskIndex.researchTasks.set(subtask.id, {
              ...subtask,
              parentId: task.id,
              parentTask: task,
            });
          } else if (subtask.type === 'audit') {
            this._taskIndex.auditTasks.set(subtask.id, {
              ...subtask,
              parentId: task.id,
              parentTask: task,
            });
          }
        }
      }
    }
  }

  /**
   * Index success criteria for a task And its subtasks
   * @param {Object} task - Task to index criteria for
   * @private
   */
  _indexTaskCriteria(task) {
    if (!task || !task.id) {return;}

    // Index task-specific criteria
    if (task.success_criteria && Array.isArray(task.success_criteria)) {
      this._criteriaCache.set(task.id, new Set(task.success_criteria));
    }

    // Index subtask criteria
    if (task.subtasks && Array.isArray(task.subtasks)) {
      for (const subtask of task.subtasks) {
        if (subtask.id && subtask.success_criteria && Array.isArray(subtask.success_criteria)) {
          this._criteriaCache.set(subtask.id, new Set(subtask.success_criteria));
        }
      }
    }
  }

  // Fallback methods for when indexing is disabled

  /**
   * Fallback subtask lookup without indexing
   * @param {string} parentTaskId - Parent task ID
   * @param {Object} todoData - TODO data
   * @returns {Array} Subtasks array
   * @private
   */
  _getFallbackSubtasks(parentTaskId, todoData) {
    const parentTask = todoData.tasks?.find(task => task.id === parentTaskId);
    return parentTask?.subtasks || [];
  }

  /**
   * Fallback subtask by ID lookup without indexing
   * @param {string} subtaskId - Subtask ID
   * @param {Object} todoData - TODO data
   * @returns {Object|null} Subtask with parent info
   * @private
   */
  _getFallbackSubtaskById(subtaskId, todoData) {
    if (!todoData.tasks) {return null;}

    for (const task of todoData.tasks) {
      if (task.subtasks) {
        const subtask = task.subtasks.find(st => st.id === subtaskId);
        if (subtask) {
          return {
            ...subtask,
            parentId: task.id,
            parentTask: task,
          };
        }
      }
    }
    return null;
  }

  /**
   * Fallback research tasks lookup without indexing
   * @param {string} parentTaskId - Parent task ID
   * @param {Object} todoData - TODO data
   * @returns {Array} Research tasks
   * @private
   */
  _getFallbackResearchTasks(parentTaskId, todoData) {
    if (!todoData.tasks) {return [];}

    if (parentTaskId) {
      const parentTask = todoData.tasks.find(task => task.id === parentTaskId);
      return (parentTask?.subtasks || []).filter(subtask => subtask.type === 'research');
    }

    const researchTasks = [];
    for (const task of todoData.tasks) {
      if (task.subtasks) {
        researchTasks.push(...task.subtasks.filter(st => st.type === 'research'));
      }
    }
    return researchTasks;
  }

  /**
   * Fallback audit tasks lookup without indexing
   * @param {string} parentTaskId - Parent task ID
   * @param {Object} todoData - TODO data
   * @returns {Array} Audit tasks
   * @private
   */
  _getFallbackAuditTasks(parentTaskId, todoData) {
    if (!todoData.tasks) {return [];}

    if (parentTaskId) {
      const parentTask = todoData.tasks.find(task => task.id === parentTaskId);
      return (parentTask?.subtasks || []).filter(subtask => subtask.type === 'audit');
    }

    const auditTasks = [];
    for (const task of todoData.tasks) {
      if (task.subtasks) {
        auditTasks.push(...task.subtasks.filter(st => st.type === 'audit'));
      }
    }
    return auditTasks;
  }

  /**
   * Fallback tasks by category lookup without indexing
   * @param {string} category - Category
   * @param {Object} todoData - TODO data
   * @returns {Array} Tasks in category
   * @private
   */
  _getFallbackTasksByCategory(category, todoData) {
    return (todoData.tasks || []).filter(task => task.category === category);
  }

  /**
   * Fallback tasks by status lookup without indexing
   * @param {string} status - Status
   * @param {Object} todoData - TODO data
   * @returns {Array} Tasks with status
   * @private
   */
  _getFallbackTasksByStatus(status, todoData) {
    return (todoData.tasks || []).filter(task => task.status === status);
  }

  /**
   * Fallback tasks by agent lookup without indexing
   * @param {string} agentId - Agent ID
   * @param {Object} todoData - TODO data
   * @returns {Array} Tasks assigned to agent
   * @private
   */
  _getFallbackTasksByAgent(agentId, todoData) {
    return (todoData.tasks || []).filter(task => task.assigned_agent === agentId);
  }

  /**
   * Fallback task dependencies lookup without indexing
   * @param {string} taskId - Task ID
   * @param {Object} todoData - TODO data
   * @returns {Array} Dependency task IDs
   * @private
   */
  _getFallbackTaskDependencies(taskId, todoData) {
    const task = todoData.tasks?.find(t => t.id === taskId);
    return task?.dependencies || [];
  }

  /**
   * Fallback task dependents lookup without indexing
   * @param {string} taskId - Task ID
   * @param {Object} todoData - TODO data
   * @returns {Array} Dependent task IDs
   * @private
   */
  _getFallbackTaskDependents(taskId, todoData) {
    if (!todoData.tasks) {return [];}

    return todoData.tasks
      .filter(task => task.dependencies && task.dependencies.includes(taskId))
      .map(task => task.id);
  }
}

module.exports = TaskIndexing;
