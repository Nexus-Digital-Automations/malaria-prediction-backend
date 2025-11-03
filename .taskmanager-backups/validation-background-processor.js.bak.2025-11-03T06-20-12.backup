

/**
 * Validation Background Processor
 * Handles complex validations That require background processing
 *
 * This module provides:
 * - Non-blocking validation execution
 * - Queue management for validation tasks
 * - Progress tracking And status updates
 * - Worker pool management for concurrent validations
 * - Integration with main ValidationEngine
 *
 * @version 1.0.0
 * @author Validation Engine Agent #3
 */

const FS = require('fs').promises;
const PATH = require('path');
const { Worker, isMainThread: _isMainThread, parentPort: _parentPort, workerData: _workerData } = require('worker_threads');

const EVENT_EMITTER = require('events');

class ValidationBackgroundProcessor extends EVENT_EMITTER {
  constructor(options = {}) {
    super();

    this.config = {
      maxWorkers: options.maxWorkers || 3,
      queueTimeout: options.queueTimeout || 300000, // 5 minutes
      workerTimeout: options.workerTimeout || 180000, // 3 minutes
      retryAttempts: options.retryAttempts || 2,
      enableProgressTracking: options.progressTracking !== false,
      enableResultCaching: options.caching !== false,
      ...options,
    };

    this.projectRoot = process.cwd();
    this.workers = new Map();
    this.validationQueue = [];
    this.activeValidations = new Map();
    this.completedValidations = new Map();
    this.resultCache = new Map();

    this.isProcessing = false;
    this.stats = {
      totalProcessed: 0,
      totalSuccessful: 0,
      totalFailed: 0,
      averageProcessingTime: 0,
      peakConcurrency: 0,
    };

    // Initialize worker pool
    this.initializeWorkerPool();
  }

  /**
   * Initialize worker pool for background processing
    loggers.stopHook.log(`🔧 Initializing worker pool with ${this.config.maxWorkers} workers...`);
  async initializeWorkerPool() {
    loggers.app.info(`🔧 Initializing worker pool with ${this.config.maxWorkers} workers...`);

    // Create workers in parallel for faster initialization
    const workerPromises = [];
    for (let i = 0; i < this.config.maxWorkers; i++) {
      workerPromises.push(this.createWorker(`worker_${i}`));
    }
    loggers.stopHook.log(`✅ Worker pool initialized with ${this.workers.size} workers`);

    loggers.app.info(`✅ Worker pool initialized with ${this.workers.size} workers`);
  }

  /**
   * Create a new worker thread
   * @param {string} workerId - Worker identifier
   */
  async createWorker(workerId) {
    try {
      const workerScript = PATH.join(__dirname, 'validation-worker.js');

      // Check if worker script exists, create if needed
      if (!(await this.workerScriptExists(workerScript))) {
        await this.createWorkerScript(workerScript);
      }

      const worker = new Worker(workerScript, {
        workerData: {
          workerId,
          projectRoot: this.projectRoot,
          config: this.config,
        },
      });

      worker.on('message', (message) => {
        this.handleWorkerMessage(workerId, message);
      });

      worker.on('error', (error) => {
        loggers.app.error(`❌ Worker ${workerId} error: ${error.message}`);
        loggers.stopHook.error(`❌ Worker ${workerId} error: ${error.message}`);
        this.handleWorkerError(workerId, error);
      });

      worker.on('exit', (code) => {
        if (code !== 0) {
          loggers.app.error(`❌ Worker ${workerId} exited with code ${code}`);
          loggers.stopHook.error(`❌ Worker ${workerId} exited with code ${code}`);
        }
        this.workers.delete(workerId);
      });

      this.workers.set(workerId, {
        worker,
        id: workerId,
        status: 'idle',
        currentTask: null,
        startTime: null,
        tasksCompleted: 0,
      });

      loggers.app.info(`✅ Worker ${workerId} created and ready`);
      loggers.stopHook.info(`✅ Worker ${workerId} created and ready`);

    } catch {
      loggers.app.error(`❌ Failed to create worker ${workerId}: ${error.message}`);
      loggers.stopHook.error(`❌ Failed to create worker ${workerId}: ${error.message}`);
    }
  }

  /**
   * Check if worker script exists
   * @param {string} scriptPath - Path to worker script
   * @returns {Promise<boolean>} True if script exists
   */
  async workerScriptExists(scriptPath) {
    try {
      await FS.access(scriptPath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Create worker script for validation processing
   * @param {string} scriptPath - Path to create worker script
   */
  async createWorkerScript(scriptPath) {
    const workerCode = `
const { parentPort, workerData } = require('worker_threads');
const VALIDATION_ENGINE = require('./validation-engine');


class ValidationWorker {
  constructor(config) {
    this.workerId = config.workerId;
    this.projectRoot = config.projectRoot;
    this.config = config.config;
    this.engine = new ValidationEngine(this.config);
  }

  async processValidation(task) {
    const startTime = Date.now();
    
    try {
      // Update status
      parentPort.postMessage({
        type: 'status',
        workerId: this.workerId,
        status: 'processing',
        task: task.id
      });

      // Execute validation based on task type
      let result;
      switch (task.type) {
        case 'full_validation':
          result = await this.engine.executeValidationWorkflow(
            task.taskId,
            task.criteria,
            task.options
          );
          break;
        
        case 'automated_only':
          result = await this.engine.executeAutomatedValidation(task.context);
          break;
          
        case 'manual_only':
          result = await this.engine.executeManualValidation(task.context);
          break;
          
        default:
          throw new Error(\`Unknown validation type: \${task.type}\`);
      }

      const duration = Date.now() - startTime;

      // Send success result
      parentPort.postMessage({
        type: 'result',
        workerId: this.workerId,
        taskId: task.id,
        success: true,
        result,
        duration,
        timestamp: new Date().toISOString()
      });

    } catch {
      const duration = Date.now() - startTime;
      
      // Send error result
      parentPort.postMessage({
        type: 'result',
        workerId: this.workerId,
        taskId: task.id,
        success: false,
        error: {
          message: error.message,
          stack: error.stack
        },
        duration,
        timestamp: new Date().toISOString()
      });
    }

    // Update status back to idle
    parentPort.postMessage({
      type: 'status',
      workerId: this.workerId,
      status: 'idle'
    });
  }
}

// Initialize worker
const worker = new ValidationWorker(workerData);

// Listen for tasks from main thread
parentPort.on('message', async (message) => {
  if (message.type === 'task') {
    await worker.processValidation(message.task);
  } else if (message.type === 'ping') {
    parentPort.postMessage({
      type: 'pong',
      workerId: worker.workerId,
      timestamp: new Date().toISOString()
    });
  }
});

// Notify ready
parentPort.postMessage({
  type: 'ready',
  workerId: worker.workerId,
  timestamp: new Date().toISOString()
});
`;

    loggers.stopHook.log(`✅ Worker script created: ${scriptPath}`);
    await FS.writeFile(scriptPath, workerCode);
    loggers.app.info(`✅ Worker script created: ${scriptPath}`);
  }

  /**
   * Queue validation task for background processing
   * @param {Object} validationTask - Validation task configuration
   * @returns {Promise<string>} Task ID for tracking
   */
  queueValidation(validationTask) {
    const taskId = this.generateTaskId();

    const task = {
      id: taskId,
      type: validationTask.type || 'full_validation',
      taskId: validationTask.taskId,
      criteria: validationTask.criteria || {},
      options: validationTask.options || {},
      context: validationTask.context || {},
      priority: validationTask.priority || 'normal',
      queuedAt: new Date().toISOString(),
      retryCount: 0,
      maxRetries: this.config.retryAttempts,
    };

    // Check cache first if enabled
    if (this.config.enableResultCaching) {
      loggers.stopHook.log(`📦 Cache hit for validation task ${taskId}`);
      if (this.resultCache.has(cacheKey)) {
        loggers.app.info(`📦 Cache hit for validation task ${taskId}`);
        const cachedResult = this.resultCache.get(cacheKey);
        this.emit('validation_completed', {
          taskId,
          success: true,
          result: cachedResult,
          fromCache: true,
        });
        return taskId;
      }
    }

    loggers.stopHook.log(`📋 Validation task ${taskId} queued (queue size: ${this.validationQueue.length})`);
    this.validationQueue.push(task);
    loggers.app.info(`📋 Validation task ${taskId} queued (queue size: ${this.validationQueue.length})`);

    // Start processing if not already running
    if (!this.isProcessing) {
      this.startProcessing();
    }

    // Emit queued event
    this.emit('validation_queued', { taskId, queuePosition: this.validationQueue.length });

    return taskId;
  }

  /**
   * Start processing validation queue
   */
  async startProcessing() {
    if (this.isProcessing) {
      return;
    }
    loggers.stopHook.log(`🚀 Starting validation queue processing...`);
    this.isProcessing = true;
    loggers.app.info(`🚀 Starting validation queue processing...`);

    while (this.validationQueue.length > 0 || this.activeValidations.size > 0) {
      // Assign tasks to available workers
      // eslint-disable-next-line no-await-in-loop -- Sequential queue processing required for proper task ordering And worker assignment
      await this.assignTasksToWorkers();

      // Wait a bit before checking again
      // eslint-disable-next-line no-await-in-loop -- Rate limiting delay required for queue polling And system performance
      await new Promise(resolve => { setTimeout(resolve, 100); });
    }
    loggers.stopHook.log(`🏁 Validation queue processing completed`);
    this.isProcessing = false;
    loggers.app.info(`🏁 Validation queue processing completed`);
  }

  /**
   * Assign tasks to available workers
   */
  async assignTasksToWorkers() {
    const availableWorkers = Array.from(this.workers.values())
      .filter(worker => worker.status === 'idle');

    // Collect all assignments to process in parallel
    const assignments = [];
    while (availableWorkers.length > 0 && this.validationQueue.length > 0) {
      const worker = availableWorkers.shift();
      const task = this.validationQueue.shift();

      assignments.push(this.assignTaskToWorker(worker, task));
    }

    // Execute all assignments in parallel
    if (assignments.length > 0) {
      await Promise.all(assignments);
    }

    // Update peak concurrency stats
    this.stats.peakConcurrency = Math.max(
      this.stats.peakConcurrency,
      this.activeValidations.size,
    );
  }

  /**
   * Assign specific task to specific worker
   * @param {Object} worker - Worker instance
   * @param {Object} task - Validation task
   */
  assignTaskToWorker(worker, task) {
    try {
      // Update worker status
      worker.status = 'busy';
      worker.currentTask = task.id;
      worker.startTime = Date.now();

      // Track active validation
      this.activeValidations.set(task.id, {
        task,
        workerId: worker.id,
        startTime: Date.now(),
      });

      // Send task to worker
      worker.worker.postMessage({
        type: 'task',
        task,
      });

      loggers.app.info(`👷 Task ${task.id} assigned to worker ${worker.id}`);
      loggers.stopHook.info(`👷 Task ${task.id} assigned to worker ${worker.id}`);

      // Emit assignment event
      this.emit('validation_started', {
        taskId: task.id,
        workerId: worker.id,
      });

      // Set timeout for task
      setTimeout(() => {
        if (this.activeValidations.has(task.id)) {
          this.handleTaskTimeout(task.id);
        }
      }, this.config.workerTimeout);
      loggers.stopHook.error(`❌ Failed to assign task ${task.id} to worker ${worker.id}: ${error.message}`);
    } catch {
      loggers.app.error(`❌ Failed to assign task ${task.id} to worker ${worker.id}: ${error.message}`);

      // Return task to queue for retry
      if (task.retryCount < task.maxRetries) {
        loggers.stopHook.log(`🔄 Task ${task.id} returned to queue for retry (${task.retryCount}/${task.maxRetries})`);
        this.validationQueue.unshift(task);
        loggers.stopHook.error(`❌ Task ${task.id} exceeded maximum retries`);
      } else {
        loggers.app.error(`❌ Task ${task.id} exceeded maximum retries`);
        this.handleTaskFailure(task.id, error);
      }
    }
  }

  /**
   * Handle message from worker
   * @param {string} workerId - Worker ID
   * @param {Object} message - Message from worker
   */
  handleWorkerMessage(workerId, message) {
    const worker = this.workers.get(workerId);

    if (!worker) {
      loggers.app.warn(`⚠️ Received message from unknown worker: ${workerId}`);
      loggers.stopHook.warn(`⚠️ Received message from unknown worker: ${workerId}`);
      return;
    }

    switch (message.type) {
      case 'ready':
        loggers.app.info(`✅ Worker ${workerId} is ready`);
        loggers.stopHook.info(`✅ Worker ${workerId} is ready`);
        break;

      case 'status':
        worker.status = message.status;
        if (message.status === 'idle') {
          worker.currentTask = null;
          worker.startTime = null;
          worker.tasksCompleted++;
        }
        break;

      case 'result':
        this.handleTaskResult(message);
        break;

      case 'pong':
        // Worker health check response
        worker.lastPong = message.timestamp;
        break;

      default:
        loggers.app.warn(`⚠️ Unknown message type from worker ${workerId}: ${message.type}`);
        loggers.stopHook.warn(`⚠️ Unknown message type from worker ${workerId}: ${message.type}`);
    }
  }

  /**
   * Handle task result from worker
   * @param {Object} message - Result message
   */
  handleTaskResult(message) {
    const { taskId, success, result, error, duration } = message;

    // Remove from active validations
    const activeValidation = this.activeValidations.get(taskId);
    if (activeValidation) {
      this.activeValidations.delete(taskId);

      // Update stats
      this.stats.totalProcessed++;
      if (success) {
        this.stats.totalSuccessful++;
      } else {
        this.stats.totalFailed++;
      }

      // Update average processing time
      this.stats.averageProcessingTime =
        (this.stats.averageProcessingTime * (this.stats.totalProcessed - 1) + duration) /
        this.stats.totalProcessed;
    }
    loggers.stopHook.log(`✅ Task ${taskId} completed successfully in ${duration}ms`);
    if (success) {
      loggers.app.info(`✅ Task ${taskId} completed successfully in ${duration}ms`);

      // Cache result if enabled
      if (this.config.enableResultCaching && activeValidation) {
        const cacheKey = this.generateCacheKey(activeValidation.task);
        this.resultCache.set(cacheKey, result);
      }

      // Store completed result
      this.completedValidations.set(taskId, {
        success: true,
        result,
        duration,
        completedAt: new Date().toISOString(),
      });

      // Emit completion event
      this.emit('validation_completed', {
        taskId,
        success: true,
        result,
        duration,
      });
      loggers.stopHook.error(`❌ Task ${taskId} failed: ${error.message}`);
    } else {
      loggers.app.error(`❌ Task ${taskId} failed: ${error.message}`);

      loggers.stopHook.log(`🔄 Retrying task ${taskId} (${activeValidation.task.retryCount + 1}/${activeValidation.task.maxRetries})`);
      if (activeValidation && activeValidation.task.retryCount < activeValidation.task.maxRetries) {
        loggers.app.info(`🔄 Retrying task ${taskId} (${activeValidation.task.retryCount + 1}/${activeValidation.task.maxRetries})`);
        activeValidation.task.retryCount++;
        this.validationQueue.unshift(activeValidation.task);
      } else {
        // Store failed result
        this.completedValidations.set(taskId, {
          success: false,
          error,
          duration,
          completedAt: new Date().toISOString(),
        });

        // Emit failure event
        this.emit('validation_completed', {
          taskId,
          success: false,
          error,
          duration,
        });
      }
    }
  }

  /**
   * Handle worker error
   * @param {string} workerId - Worker ID
   * @param {Error} error - Worker error
    loggers.stopHook.error(`❌ Worker ${workerId} encountered error: ${error.message}`);
  async handleWorkerError(workerId, error) {
    loggers.app.error(`❌ Worker ${workerId} encountered error: ${error.message}`);

    const worker = this.workers.get(workerId);
    if (worker && worker.currentTask) {
      // Handle the current task failure
      this.handleTaskFailure(worker.currentTask, error);
    }

    // Remove failed worker
    this.workers.delete(workerId);

    // Create replacement worker
    await this.createWorker(workerId);
  }

  /**
   * Handle task timeout
   * @param {string} taskId - Task ID
    loggers.stopHook.error(`⏰ Task ${taskId} timed out`);
  handleTaskTimeout(taskId) {
    loggers.app.error(`⏰ Task ${taskId} timed out`);

    const activeValidation = this.activeValidations.get(taskId);
    if (activeValidation) {
      this.handleTaskFailure(taskId, new Error('Task timeout'));
    }
  }

  /**
   * Handle task failure
   * @param {string} taskId - Task ID
   * @param {Error} error - Error That caused failure
   */
  handleTaskFailure(taskId, error) {
    // Remove from active validations
    this.activeValidations.delete(taskId);

    // Store failed result
    this.completedValidations.set(taskId, {
      success: false,
      error: {
        message: error.message,
        stack: error.stack,
      },
      completedAt: new Date().toISOString(),
    });

    // Update stats
    this.stats.totalProcessed++;
    this.stats.totalFailed++;

    // Emit failure event
    this.emit('validation_completed', {
      taskId,
      success: false,
      error: {
        message: error.message,
        stack: error.stack,
      },
    });
  }

  /**
   * Get validation task status
   * @param {string} taskId - Task ID
   * @returns {Object} Task status
   */
  getTaskStatus(taskId) {
    // Check if completed
    if (this.completedValidations.has(taskId)) {
      return {
        status: 'completed',
        ...this.completedValidations.get(taskId),
      };
    }

    // Check if active
    if (this.activeValidations.has(taskId)) {
      const validation = this.activeValidations.get(taskId);
      return {
        status: 'processing',
        workerId: validation.workerId,
        startTime: validation.startTime,
        duration: Date.now() - validation.startTime,
      };
    }

    // Check if queued
    const queuePosition = this.validationQueue.findIndex(task => task.id === taskId);
    if (queuePosition !== -1) {
      return {
        status: 'queued',
        queuePosition: queuePosition + 1,
        estimatedWaitTime: this.estimateWaitTime(queuePosition),
      };
    }

    return {
      status: 'unknown',
      message: 'Task not found',
    };
  }

  /**
   * Estimate wait time for queued task
   * @param {number} queuePosition - Position in queue
   * @returns {number} Estimated wait time in milliseconds
   */
  estimateWaitTime(queuePosition) {
    const availableWorkers = Array.from(this.workers.values())
      .filter(worker => worker.status === 'idle').length;

    if (availableWorkers > 0) {
      return 0; // Can start immediately
    }

    // Estimate based on average processing time And queue position
    const avgProcessingTime = this.stats.averageProcessingTime || 60000; // 1 minute default
    const tasksAhead = queuePosition;
    const concurrentWorkers = this.workers.size;

    return Math.ceil(tasksAhead / concurrentWorkers) * avgProcessingTime;
  }

  /**
   * Get processor statistics
   * @returns {Object} Processor statistics
   */
  getStats() {
    return {
      ...this.stats,
      workers: {
        total: this.workers.size,
        idle: Array.from(this.workers.values()).filter(w => w.status === 'idle').length,
        busy: Array.from(this.workers.values()).filter(w => w.status === 'busy').length,
      },
      queue: {
        pending: this.validationQueue.length,
        active: this.activeValidations.size,
        completed: this.completedValidations.size,
      },
      cache: {
        size: this.resultCache.size,
        enabled: this.config.enableResultCaching,
      },
    };
  }

  /**
   * Generate unique task ID
   * @returns {string} Task ID
   */
  generateTaskId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return `bg_validation_${timestamp}_${random}`;
  }

  /**
   * Generate cache key for validation task
   * @param {Object} task - Validation task
   * @returns {string} Cache key
   */
  generateCacheKey(task) {
    const keyData = {
      type: task.type,
      taskId: task.taskId,
      criteria: task.criteria,
      options: task.options,
    };

    return Buffer.from(JSON.stringify(keyData)).toString('base64');
  }

  /**
   * Clear completed validations from memory
   * @param {number} olderThanMs - Clear validations older than this (default: 1 hour)
   */
  clearCompletedValidations(olderThanMs = 3600000) {
    const cutoffTime = Date.now() - olderThanMs;
    let cleared = 0;

    for (const [taskId, validation] of this.completedValidations.entries()) {
      const completedTime = new Date(validation.completedAt).getTime();
      if (completedTime < cutoffTime) {
        this.completedValidations.delete(taskId);
        cleared++;
      }
    }
    loggers.stopHook.log(`🧹 Cleared ${cleared} completed validations from memory`);
    if (cleared > 0) {
      loggers.app.info(`🧹 Cleared ${cleared} completed validations from memory`);
    }
  }

  /**
   * Shutdown the background processor
   */
  async shutdown() {
    loggers.app.info(`🔄 Shutting down validation background processor...`);
    loggers.stopHook.info(`🔄 Shutting down validation background processor...`);

    // Stop accepting new tasks
    this.isProcessing = false;

    // Wait for active validations to complete (with timeout)
    const shutdownTimeout = 30000; // 30 seconds
    const startTime = Date.now();
    loggers.stopHook.log(`⏳ Waiting for ${this.activeValidations.size} active validations to complete...`);
    while (this.activeValidations.size > 0 && (Date.now() - startTime) < shutdownTimeout) {
      loggers.app.info(`⏳ Waiting for ${this.activeValidations.size} active validations to complete...`);
      // eslint-disable-next-line no-await-in-loop -- Graceful shutdown polling requires sequential timing delays
      await new Promise(resolve => { setTimeout(resolve, 1000); });
    }

    // Terminate all workers in parallel
    const terminationPromises = [];
    for (const [workerId, worker] of this.workers.entries()) {
      terminationPromises.push(
        worker.worker.terminate()
          .then(() => {
            loggers.app.info(`✅ Worker ${workerId} terminated`);
            loggers.stopHook.info(`✅ Worker ${workerId} terminated`);
          })
          .catch((error) => {
            loggers.app.error(`❌ Error terminating worker ${workerId}: ${error.message}`);
            loggers.stopHook.error(`❌ Error terminating worker ${workerId}: ${error.message}`);
          }),
      );
    }

    // Wait for all workers to terminate
    await Promise.all(terminationPromises);

    loggers.stopHook.log(`✅ Background processor shutdown complete`);

    loggers.app.info(`✅ Background processor shutdown complete`);
  }
}

module.exports = ValidationBackgroundProcessor;
