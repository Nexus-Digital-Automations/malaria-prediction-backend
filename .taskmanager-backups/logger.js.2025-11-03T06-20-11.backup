/**
 * Centralized Structured Logging Utility
 *
 * Provides consistent structured logging across the entire application using Pino.
 * Replaces console.log calls with structured JSON logging for better observability
 * And monitoring in production environments.
 *
 * Features:
 * - Structured JSON logging with consistent fields
 * - Context-aware logging (agentId, taskId, operationId)
 * - Performance metrics And timing information
 * - Error tracking with stack traces
 * - Development And production-friendly output formats
 */

const pino = require('pino');
// Removed circular dependency - loggers is defined in this file;
const os = require('os');
const FS = require('fs');
const path = require('path');

// LOGGER configuration;
const loggerConfig = {
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => {
      return { level: label.toUpperCase() };
    },
    log: (object) => {
      // Add consistent metadata to all log entries
      return {
        ...object,
        hostname: os.hostname(),
        pid: process.pid,
        service: 'infinite-continue-stop-hook',
        version: process.env.npm_package_version || '1.0.0',
      };
    },
  },
  timestamp: () => `,"timestamp":"${new Date().toISOString()}"`,
  // Pretty print in development, JSON in production
  transport: process.env.NODE_ENV !== 'production' ? {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'HH:MM:ss',
      ignore: 'pid,hostname,service,version',
    },
  } : undefined,
};

// Create base logger;
const baseLogger = pino(loggerConfig);

/**
 * Creates a contextual logger with agent/task/operation context
 * @param {Object} context - Context information
 * @param {string} context.agentId - Unique agent identifier
 * @param {string} context.taskId - Task identifier
 * @param {string} context.operationId - Operation identifier
 * @param {string} context.module - Module or component name
 * @returns {Object} Contextual logger instance
 */
function createContextLogger(context = {}, _agentId) {
  const contextData = {
    agentId: context.agentId || 'unknown',
    taskId: context.taskId || null,
    operationId: context.operationId || null,
    module: context.module || 'main',
  };

  return baseLogger.child(contextData);
}

/**
 * Performance timing utility for operations
 * @param {Object} logger - LOGGER instance
 * @param {string} operationName - name of the operation being timed
 * @returns {Function} Function to call when operation completes
 */
function timeOperation(logger, operationName) {
  const startTime = process.hrtime.bigint();

  logger.info({
    operation: operationName,
    status: 'started',
  }, `Starting operation ${operationName}`);

  return function endTiming(result = {}) {
    const endTime = process.hrtime.bigint();
    const durationMs = Number(endTime - startTime) / 1000000; // Convert to milliseconds

    logger.info({
      operation: operationName,
      status: 'completed',
      duration_ms: durationMs,
      ...result,
    }, `Completed operation ${operationName} in ${durationMs.toFixed(2)}ms`);

    return { duration_ms: durationMs, ...result };
  };
}

/**
 * Structured error logging with stack traces And context
 * @param {Object} logger - LOGGER instance
 * @param {Error} error - Error object
 * @param {Object} context - Additional context
 * @param {string} message - Custom error message
 */
function logError(logger, error, context = {}, message = 'An error occurred') {
  logger.error({
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
      code: error.code || null,
    },
    ...context,
  }, message);
}

/**
 * Log API request/response for audit trail
 * @param {Object} logger - LOGGER instance
 * @param {string} method - HTTP method or API method
 * @param {string} endpoint - API endpoint
 * @param {Object} params - Request parameters
 * @param {Object} response - Response data (sanitized)
 * @param {number} duration - Request duration in ms
 */
function logApiCall(logger, method, endpoint, params = {}, response = {}, duration = 0) {
  // Sanitize sensitive data;
  const sanitizedParams = { ...params };
  const sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth'];

  for (const key of Object.keys(sanitizedParams)) {
    if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      sanitizedParams[key] = '[REDACTED]';
    }
  }

  logger.info({
    api_call: {
      method,
      endpoint,
      params: sanitizedParams,
      response_status: response.status || 'success',
      duration_ms: duration,
    },
  }, `API Call: ${method} ${endpoint}`);
}

/**
 * Create specialized loggers for different components
 */
const LOGGERS = {
  // Main application logger
  app: createContextLogger({ module: 'app' }),

  // Task management logger
  taskManager: createContextLogger({ module: 'taskManager' }),

  // Agent operations logger
  agent: createContextLogger({ module: 'agent' }),

  // Validation system logger
  validation: createContextLogger({ module: 'validation' }),

  // Stop hook logger
  stopHook: createContextLogger({ module: 'stopHook' }),

  // Performance metrics logger
  performance: createContextLogger({ module: 'performance' }),

  // Security And audit logger
  security: createContextLogger({ module: 'security' }),

  // Database operations logger
  database: createContextLogger({ module: 'database' }),

  // API logger
  api: createContextLogger({ module: 'api' }),
};

/**
 * Legacy file-based logger for backward compatibility with stop hook
 * Maintains the original interface while adding structured logging capabilities
 */
class LegacyLogger {
  constructor(projectRoot, _agentId) {
    this.projectRoot = projectRoot;
    this.logger = createContextLogger({ module: 'stopHook', projectRoot });

    // Configure logging to development/logs directory;
    const logsDir = path.join(projectRoot, 'development', 'logs');
    // Ensure logs directory exists

    // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
    if (!FS.existsSync(logsDir)) {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      FS.mkdirSync(logsDir, { recursive: true });
    }
    this.logPath = path.join(logsDir, 'infinite-continue-hook.log');
    this.logData = {
      execution: {
        timestamp: new Date().toISOString(),
        projectRoot: projectRoot,
        hookVersion: '1.0.0',
        nodeVersion: process.version,
        platform: os.platform(),
        arch: os.arch(),
        pid: process.pid,
        cwd: process.cwd(),
      },
      input: {},
      projectState: {},
      decisions: [],
      flow: [],
      output: {},
      errors: [],
    };
  }

  logInput(hookInput) {
    this.logData.input = {
      sessionId: hookInput.session_id,
      transcriptPath: hookInput.transcript_path,
      stopHookActive: hookInput.stop_hook_active,
      rawInput: hookInput,
    };
    this.logger.info({ hookInput }, 'Received input from Claude Code');
    this.addFlow('Received input from Claude Code');
  }

  logProjectState(todoData, todoPath) {
    this.logData.projectState = {
      todoPath: todoPath,
      project: todoData.project,
      totalTasks: todoData.tasks.length,
      pendingTasks: todoData.tasks.filter(t => t.status === 'pending').length,
      inProgressTasks: todoData.tasks.filter(t => t.status === 'in_progress').length,
      completedTasks: todoData.tasks.filter(t => t.status === 'completed').length,
      lastMode: todoData.last_mode,
      reviewStrikes: todoData.review_strikes,
      strikesCompletedLastRun: todoData.strikes_completed_last_run,
      availableModes: todoData.available_modes,
    };
    this.logger.info({ projectState: this.logData.projectState }, 'Loaded project state from TODO.json');
    this.addFlow('Loaded project state from TODO.json');
  }

  logCurrentTask(task) {
    if (task) {
      this.logData.projectState.currentTask = {
        id: task.id,
        title: task.title,
        description: task.description,
        mode: task.mode,
        priority: task.priority,
        status: task.status,
        isReviewTask: task.is_review_task,
        strikeNumber: task.strike_number,
      };
      this.logger.info({ task: this.logData.projectState.currentTask }, `Selected task: ${task.title} (${task.id})`);
      this.addFlow(`Selected task: ${task.title} (${task.id})`);
    } else {
      this.logData.projectState.currentTask = null;
      this.logger.info('No tasks available');
      this.addFlow('No tasks available');
    }
  }

  logModeDecision(previousMode, selectedMode, reason) {
    const decision = {
      type: 'mode_selection',
      timestamp: new Date().toISOString(),
      previousMode: previousMode,
      selectedMode: selectedMode,
      reason: reason,
    };
    this.logData.decisions.push(decision);
    this.logger.info({ decision }, `Mode decision: ${previousMode || 'none'} → ${selectedMode} (${reason})`);
    this.addFlow(`Mode decision: ${previousMode || 'none'} → ${selectedMode} (${reason})`);
  }

  logStrikeHandling(strikeResult, todoData) {
    const decision = {
      type: 'strike_handling',
      timestamp: new Date().toISOString(),
      action: strikeResult.action,
      message: strikeResult.message,
      currentStrikes: todoData.review_strikes,
      strikesCompleted: todoData.strikes_completed_last_run,
    };
    this.logData.decisions.push(decision);
    this.logger.info({ decision }, `Strike handling: ${strikeResult.action} - ${strikeResult.message || 'continue'}`);
    this.addFlow(`Strike handling: ${strikeResult.action} - ${strikeResult.message || 'continue'}`);
  }

  logPromptGeneration(prompt, additionalInstructions) {
    this.logData.output = {
      promptLength: prompt.length,
      additionalInstructionsLength: additionalInstructions.length,
      totalLength: prompt.length + additionalInstructions.length,
      promptPreview: prompt.substring(0, 500) + '...',
      timestamp: new Date().toISOString(),
    };
    this.logger.info({ output: this.logData.output }, 'Generated prompt for Claude');
    this.addFlow('Generated prompt for Claude');
  }

  logExit(code, reason) {
    this.logData.output.exitCode = code;
    this.logData.output.exitReason = reason;
    this.logger.info({ exitCode: code, exitReason: reason }, `Exiting with code ${code}: ${reason}`);
    this.addFlow(`Exiting with code ${code}: ${reason}`);
  }

  logError(error, context) {
    const errorEntry = {
      timestamp: new Date().toISOString(),
      context: context,
      message: error.message,
      stack: error.stack,
      name: error.name,
    };
    this.logData.errors.push(errorEntry);
    logError(this.logger, error, { context }, `ERROR in ${context}: ${error.message}`);
    this.addFlow(`ERROR in ${context}: ${error.message}`);
  }

  addFlow(message) {
    this.logData.flow.push({
      timestamp: new Date().toISOString(),
      message: message,
    });
    this.logger.trace({ flowMessage: message }, message);
  }

  save() {
    try {
      // Add final timestamp
      this.logData.execution.endTimestamp = new Date().toISOString();

      // Calculate execution duration;
      const start = new Date(this.logData.execution.timestamp);
      const end = new Date(this.logData.execution.endTimestamp);
      this.logData.execution.durationMs = end - start;

      // Write log file (overwrites existing)

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      FS.writeFileSync(this.logPath, JSON.stringify(this.logData, null, 2), 'utf8');

      this.logger.info({
        logPath: this.logPath,
        durationMs: this.logData.execution.durationMs,
        errors: this.logData.errors.length,
      }, 'Saved execution log');

      // Also save a copy with timestamp for debugging if needed
      if (this.logData.errors.length > 0) {
        const debugPath = path.join(this.projectRoot, `.hook-debug-${Date.now()}.json`);

        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        FS.writeFileSync(debugPath, JSON.stringify(this.logData, null, 2), 'utf8');
        this.logger.warn({ debugPath }, 'Saved debug log due to errors');
      }
    } catch (error) {
      // Don't let logging errors crash the hook - but log it with structured logger
      logError(this.logger, error, {}, 'Failed to save legacy log file');
    }
  }
}

// Performance monitoring and alerting intervals
let systemHealthInterval = null;
let errorTrackingData = [];

// Initialize monitoring intervals
function startObservabilityMonitoring(options = {}) {
  const {
    healthCheckInterval = 60000, // 1 minute
    memoryThreshold = 80,
    errorTrackingWindow = 300000, // 5 minutes
  } = options;

  // System health monitoring
  if (!systemHealthInterval) {
    systemHealthInterval = setInterval(() => {
      try {
        // Collect system health metrics
        const _healthMetrics = module.exports.metrics.systemHealth();

        // Check for memory alerts
        module.exports.metrics.alerts.highMemoryUsage(memoryThreshold);

        // Clean up old error tracking data
        const now = Date.now();
        errorTrackingData = errorTrackingData.filter(err =>
          (now - new Date(err.timestamp).getTime()) < errorTrackingWindow,
        );

        // Track error trends if we have data
        if (errorTrackingData.length > 0) {
          module.exports.errorTracking.trackErrorTrend(errorTrackingData, errorTrackingWindow);
        }
      } catch (monitoringError) {
        LOGGERS.app.error({
          monitoring_error: {
            message: monitoringError.message,
            stack: monitoringError.stack,
          },
        }, 'Observability monitoring failed');
      }
    }, healthCheckInterval);

    LOGGERS.app.info({
      observability_monitoring: {
        started: true,
        health_check_interval_ms: healthCheckInterval,
        memory_threshold_percent: memoryThreshold,
        error_tracking_window_ms: errorTrackingWindow,
      },
    }, 'Observability monitoring started');
  }
}

// Stop monitoring intervals
function stopObservabilityMonitoring() {
  if (systemHealthInterval) {
    clearInterval(systemHealthInterval);
    systemHealthInterval = null;

    LOGGERS.app.info({
      observability_monitoring: {
        stopped: true,
      },
    }, 'Observability monitoring stopped');
  }
}

// Enhanced error logging that feeds into tracking
function logErrorWithTracking(logger, error, context = {}, message = 'An error occurred') {
  // Use existing logError function
  logError(logger, error, context, message);

  // Also categorize and track the error
  const categorizedError = module.exports.errorTracking.categorizeError(error, context);
  errorTrackingData.push(categorizedError);

  // Check for error rate spikes
  const recentErrors = errorTrackingData.filter(err =>
    (Date.now() - new Date(err.timestamp).getTime()) < 60000, // Last minute
  );

  if (recentErrors.length > 0) {
    module.exports.metrics.alerts.errorRateSpike(recentErrors.length, 60000, 5);
  }

  return categorizedError;
}

// Export logger utilities
module.exports = {
  // Base logger for direct use
  logger: baseLogger,

  // Specialized component loggers
  loggers: LOGGERS,

  // Utility functions
  createContextLogger,
  timeOperation,
  logError,
  logApiCall,

  // Legacy LOGGER class for backward compatibility
  LOGGER: LegacyLogger,

  // Convenience methods for migration from console.log
  info: (message, data = {}) => baseLogger.info(data, message),
  warn: (message, data = {}) => baseLogger.warn(data, message),
  error: (message, data = {}) => baseLogger.error(data, message),
  debug: (message, data = {}) => baseLogger.debug(data, message),
  trace: (message, data = {}) => baseLogger.trace(data, message),

  // Enhanced error logging with tracking
  logErrorWithTracking,

  // Observability monitoring controls
  startObservabilityMonitoring,
  stopObservabilityMonitoring,

  // Legacy console replacements (for gradual migration)
  log: (message, ...args) => {
    if (typeof message === 'object') {
      baseLogger.info(message);
    } else {
      baseLogger.info({ args }, message);
    }
  },

  // Performance metrics helpers
  metrics: {
    counter: (name, value = 1, labels = {}) => {
      LOGGERS.performance.info({
        metric_type: 'counter',
        metric_name: name,
        metric_value: value,
        labels,
      }, `Counter: ${name} = ${value}`);
    },

    gauge: (name, value, labels = {}) => {
      LOGGERS.performance.info({
        metric_type: 'gauge',
        metric_name: name,
        metric_value: value,
        labels,
      }, `Gauge: ${name} = ${value}`);
    },

    histogram: (name, value, labels = {}) => {
      LOGGERS.performance.info({
        metric_type: 'histogram',
        metric_name: name,
        metric_value: value,
        labels,
      }, `Histogram: ${name} = ${value}`);
    },

    // System health metrics
    systemHealth: () => {
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();
      const uptime = process.uptime();

      const healthMetrics = {
        memory: {
          heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024), // MB
          heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024), // MB
          external: Math.round(memUsage.external / 1024 / 1024), // MB
          rss: Math.round(memUsage.rss / 1024 / 1024), // MB
        },
        cpu: {
          user: cpuUsage.user,
          system: cpuUsage.system,
        },
        process: {
          uptime: Math.round(uptime),
          pid: process.pid,
          platform: os.platform(),
          arch: os.arch(),
          nodeVersion: process.version,
        },
        system: {
          hostname: os.hostname(),
          loadAverage: os.loadavg(),
          freeMemory: Math.round(os.freemem() / 1024 / 1024), // MB
          totalMemory: Math.round(os.totalmem() / 1024 / 1024), // MB
        },
      };

      LOGGERS.performance.info({
        metric_type: 'system_health',
        timestamp: new Date().toISOString(),
        ...healthMetrics,
      }, 'System health metrics collected');

      return healthMetrics;
    },

    // Business metrics for task management operations
    business: {
      taskCreated: (taskType, priority = 'normal') => {
        LOGGERS.performance.info({
          metric_type: 'business_metric',
          event: 'task_created',
          task_type: taskType,
          priority: priority,
          timestamp: new Date().toISOString(),
        }, `Task created: ${taskType} (${priority})`);
      },

      taskCompleted: (taskType, durationMs, success = true) => {
        LOGGERS.performance.info({
          metric_type: 'business_metric',
          event: 'task_completed',
          task_type: taskType,
          duration_ms: durationMs,
          success: success,
          timestamp: new Date().toISOString(),
        }, `Task completed: ${taskType} in ${durationMs}ms (${success ? 'success' : 'failed'})`);
      },

      agentInitialized: (agentId, capabilities = []) => {
        LOGGERS.performance.info({
          metric_type: 'business_metric',
          event: 'agent_initialized',
          agent_id: agentId,
          capabilities: capabilities,
          timestamp: new Date().toISOString(),
        }, `Agent initialized: ${agentId}`);
      },

      validationRun: (type, passed, failed, duration) => {
        LOGGERS.performance.info({
          metric_type: 'business_metric',
          event: 'validation_run',
          validation_type: type,
          tests_passed: passed,
          tests_failed: failed,
          duration_ms: duration,
          success_rate: passed / (passed + failed) * 100,
          timestamp: new Date().toISOString(),
        }, `Validation run: ${type} (${passed}/${passed + failed} passed)`);
      },
    },

    // Alert detection patterns
    alerts: {
      highMemoryUsage: (threshold = 80) => {
        const memUsage = process.memoryUsage();
        const usagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;

        if (usagePercent > threshold) {
          LOGGERS.security.warn({
            alert_type: 'high_memory_usage',
            severity: 'warning',
            memory_usage_percent: Math.round(usagePercent),
            threshold: threshold,
            heap_used_mb: Math.round(memUsage.heapUsed / 1024 / 1024),
            heap_total_mb: Math.round(memUsage.heapTotal / 1024 / 1024),
            requires_attention: true,
            timestamp: new Date().toISOString(),
          }, `ALERT: High memory usage detected (${Math.round(usagePercent)}% > ${threshold}%)`);
          return true;
        }
        return false;
      },

      errorRateSpike: (errorCount, timeWindowMs, threshold = 10) => {
        if (errorCount > threshold) {
          LOGGERS.security.error({
            alert_type: 'error_rate_spike',
            severity: 'critical',
            error_count: errorCount,
            time_window_ms: timeWindowMs,
            threshold: threshold,
            requires_immediate_attention: true,
            timestamp: new Date().toISOString(),
          }, `ALERT: Error rate spike detected (${errorCount} errors in ${timeWindowMs}ms)`);
          return true;
        }
        return false;
      },

      taskFailureRate: (failedTasks, totalTasks, threshold = 50) => {
        const failureRate = (failedTasks / totalTasks) * 100;

        if (failureRate > threshold) {
          LOGGERS.security.error({
            alert_type: 'task_failure_rate',
            severity: 'critical',
            failure_rate_percent: Math.round(failureRate),
            failed_tasks: failedTasks,
            total_tasks: totalTasks,
            threshold_percent: threshold,
            requires_immediate_attention: true,
            timestamp: new Date().toISOString(),
          }, `ALERT: High task failure rate (${Math.round(failureRate)}% > ${threshold}%)`);
          return true;
        }
        return false;
      },
    },
  },

  // Enhanced error categorization and tracking
  errorTracking: {
    categorizeError: (error, context = {}) => {
      let category = 'unknown';
      let severity = 'medium';

      // Categorize by error type and content
      if (error.code === 'ENOENT') {
        category = 'file_system';
        severity = 'medium';
      } else if (error.code === 'EACCES') {
        category = 'permission';
        severity = 'high';
      } else if (error.message.includes('timeout')) {
        category = 'timeout';
        severity = 'medium';
      } else if (error.message.includes('network') || error.message.includes('ECONNREFUSED')) {
        category = 'network';
        severity = 'high';
      } else if (error.name === 'SyntaxError') {
        category = 'syntax';
        severity = 'high';
      } else if (error.name === 'TypeError') {
        category = 'type';
        severity = 'medium';
      } else if (error.name === 'ReferenceError') {
        category = 'reference';
        severity = 'high';
      } else if (error.message.includes('validation')) {
        category = 'validation';
        severity = 'medium';
      } else if (error.message.includes('auth')) {
        category = 'authentication';
        severity = 'high';
      }

      const errorData = {
        error_id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        category: category,
        severity: severity,
        name: error.name,
        message: error.message,
        stack: error.stack,
        code: error.code || null,
        context: context,
        timestamp: new Date().toISOString(),
        requires_investigation: severity === 'high',
      };

      LOGGERS.security.error(errorData, `Categorized error: ${category}/${severity} - ${error.message}`);

      return errorData;
    },

    trackErrorTrend: (errors, timeWindowMs = 300000) => { // 5 minutes default
      const now = Date.now();
      const recentErrors = errors.filter(err =>
        (now - new Date(err.timestamp).getTime()) < timeWindowMs,
      );

      const categoryCounts = {};
      const severityCounts = {};

      recentErrors.forEach(err => {
        categoryCounts[err.category] = (categoryCounts[err.category] || 0) + 1;
        severityCounts[err.severity] = (severityCounts[err.severity] || 0) + 1;
      });

      const trendData = {
        time_window_ms: timeWindowMs,
        total_errors: recentErrors.length,
        category_breakdown: categoryCounts,
        severity_breakdown: severityCounts,
        error_rate_per_minute: (recentErrors.length / (timeWindowMs / 60000)).toFixed(2),
        timestamp: new Date().toISOString(),
      };

      LOGGERS.performance.info({
        metric_type: 'error_trend',
        ...trendData,
      }, `Error trend analysis: ${recentErrors.length} errors in ${timeWindowMs/60000} minutes`);

      return trendData;
    },
  },

  // Health check utilities for monitoring
  healthCheck: {
    performSystemCheck: () => {
      const healthData = {
        status: 'healthy',
        checks: {},
        timestamp: new Date().toISOString(),
      };

      try {
        // Memory check
        const memUsage = process.memoryUsage();
        const memoryUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
        healthData.checks.memory = {
          status: memoryUsagePercent < 80 ? 'healthy' : 'warning',
          usage_percent: Math.round(memoryUsagePercent),
          heap_used_mb: Math.round(memUsage.heapUsed / 1024 / 1024),
        };

        // Process check
        healthData.checks.process = {
          status: 'healthy',
          uptime_seconds: Math.round(process.uptime()),
          pid: process.pid,
        };

        // File system check (basic)
        try {
          const testPath = path.join(process.cwd(), '.health-check-test');
          FS.writeFileSync(testPath, 'test', 'utf8');
          FS.unlinkSync(testPath);
          healthData.checks.filesystem = { status: 'healthy' };
        } catch (fsError) {
          healthData.checks.filesystem = {
            status: 'error',
            error: fsError.message,
          };
          healthData.status = 'degraded';
        }

        // Overall status determination
        const hasErrors = Object.values(healthData.checks).some(check => check.status === 'error');
        const hasWarnings = Object.values(healthData.checks).some(check => check.status === 'warning');

        if (hasErrors) {
          healthData.status = 'unhealthy';
        } else if (hasWarnings) {
          healthData.status = 'degraded';
        }

        LOGGERS.app.info({
          health_check: healthData,
        }, `Health check completed: ${healthData.status}`);

        return healthData;
      } catch (error) {
        healthData.status = 'error';
        healthData.error = error.message;

        LOGGERS.app.error({
          health_check_error: {
            message: error.message,
            stack: error.stack,
          },
        }, 'Health check failed');

        return healthData;
      }
    },
  },
};
