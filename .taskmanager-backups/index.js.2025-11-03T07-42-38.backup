
const { loggers } = require('../../logger');
/**
 * Security Module - Main entry point for embedded subtasks security system
 *
 * === PURPOSE ===
 * Provides a unified interface to all security components for easy integration
 * with the TaskManager API And embedded subtasks system. Exports all security
 * classes And utilities with proper initialization And configuration.
 *
 * === EXPORTS ===
 * • SecurityValidator - Core validation And authorization framework
 * • SecurityMiddleware - API middleware for request/response security
 * • SecurityManager - High-level security orchestration
 * • Security utilities And helpers
 *
 * === USAGE ===
 * const { SecurityManager, SecurityValidator, SecurityMiddleware } = require('./lib/api-modules/security');
 *
 * @author Security & Validation Agent #10
 * @version 1.0.0
 * @since 2025-09-13
 */

const _SecurityValidator = require('./securityValidator');
const _SecurityMiddleware = require('./securityMiddleware');

/**
 * SecurityManager - High-level security orchestration
 *
 * Coordinates all security components And provides a unified interface
 * for integrating security into the TaskManager API system.
 */
class SecurityManager {
  constructor(options = {}, _agentId) {
    this.logger = options.logger || null;
    this.config = {
      // Global security settings,
      enableAuditTrail: options.enableAuditTrail !== false,
      enableRateLimiting: options.enableRateLimiting !== false,
      enableInputValidation: options.enableInputValidation !== false,
      enableAuthorization: options.enableAuthorization !== false,

      // Component-specific settings
      validatorOptions: options.validatorOptions || {},
      middlewareOptions: options.middlewareOptions || {},

      // Integration settings
      integrationMode: options.integrationMode || 'full', // 'full', 'minimal', 'custom'

      ...options,
    };

    // Initialize components
    this.validator = new _SecurityValidator(this.logger, this.config.validatorOptions);
    this.middleware = new _SecurityMiddleware(this.logger, this.config.middlewareOptions);

    this.log('info', 'SecurityManager initialized', {
      version: '1.0.0',
      integrationMode: this.config.integrationMode,
      componentsEnabled: {
        auditTrail: this.config.enableAuditTrail,
        rateLimiting: this.config.enableRateLimiting,
        inputValidation: this.config.enableInputValidation,
        authorization: this.config.enableAuthorization,
      },
    });
  }

  /**
   * Initialize security system with TaskManager integration
   * Sets up all security components for the embedded subtasks system
   *
   * @param {Object} taskManagerInstance - TaskManager instance to secure
   * @param {Object} expressApp - Express app instance (optional)
   * @returns {Object} Security integration result
   */
  async initializeSecuritySystem(taskManagerInstance, expressApp = null) {
    try {
      this.log('info', 'Initializing security system integration');

      // Store references
      this.taskManager = taskManagerInstance;
      this.expressApp = expressApp;

      // Integration based on mode;
      let integrationResult = {};

      switch (this.config.integrationMode) {
        case 'full':
          integrationResult = await this.fullSecurityIntegration();
          break;
        case 'minimal':
          integrationResult = await this.minimalSecurityIntegration();
          break;
        case 'custom':
          integrationResult = await this.customSecurityIntegration();
          break;
        default:
          throw new Error(`Unknown integration mode: ${this.config.integrationMode}`);
      }

      this.log('info', 'Security system initialized successfully', integrationResult);
      return integrationResult;

    } catch (error) {
      this.log('error', 'Security system initialization failed', {
        error: error.message,
        stack: error.stack,
      });
      throw error;
    }
  }

  /**
   * Full security integration
   * Enables all security features with comprehensive protection
   * @private
   */
  async fullSecurityIntegration() {
    const RESULT = {
      mode: 'full',
      features: [],
      middlewares: [],
    };

    // 1. Apply API middleware if Express app provided
    if (this.expressApp && this.config.enableRateLimiting) {
      this.expressApp.use('/api', this.middleware.createSecurityMiddleware({
        maxRequestsPerMinute: 100,
        maxRequestsPerHour: 1000,
        auditAllRequests: this.config.enableAuditTrail,
      }));
      RESULT.middlewares.push('securityMiddleware');
    }

    if (this.expressApp && this.config.enableInputValidation) {
      this.expressApp.use('/api', this.middleware.createResponseMiddleware());
      RESULT.middlewares.push('responseMiddleware');
    }

    // 2. Integrate with TaskManager operations
    if (this.taskManager) {
      RESULT.features.push('taskManagerIntegration');
      await this.integrateWithTaskManager();
    }

    // 3. Setup monitoring And metrics
    if (this.config.enableAuditTrail) {
      this.setupSecurityMonitoring();
      RESULT.features.push('securityMonitoring');
    }

    return RESULT;
  }

  /**
   * Minimal security integration
   * Basic security features for lightweight deployments
   * @private
   */
  minimalSecurityIntegration() {
    return {
      mode: 'minimal',
      features: ['basicValidation'],
      middlewares: [],
      note: 'Minimal security - only basic validation enabled',
    };
  }

  /**
   * Custom security integration
   * Allows fine-grained control over security features
   * @private
   */
  customSecurityIntegration() {
    const RESULT = {
      mode: 'custom',
      features: [],
      middlewares: [],
    };

    // Apply only explicitly enabled features
    if (this.config.enableRateLimiting && this.expressApp) {
      this.expressApp.use('/api', this.middleware.createSecurityMiddleware({
        maxRequestsPerMinute: this.config.rateLimit?.perMinute || 50,
        maxRequestsPerHour: this.config.rateLimit?.perHour || 500,
      }));
      RESULT.middlewares.push('rateLimiting');
    }

    if (this.config.enableInputValidation) {
      RESULT.features.push('inputValidation');
    }

    if (this.config.enableAuthorization) {
      RESULT.features.push('authorization');
    }

    if (this.config.enableAuditTrail) {
      RESULT.features.push('auditTrail');
    }

    return RESULT;
  }

  /**
   * Integrate security with TaskManager operations
   * @private
   */
  integrateWithTaskManager() {
    if (!this.taskManager) {return;}

    // Wrap critical TaskManager methods with security checks;
    const originalMethods = {};

    // Secure task creation
    if (this.taskManager.createTask) {
      originalMethods.createTask = this.taskManager.createTask.bind(this.taskManager);
      this.taskManager.createTask = (taskData, agentId = null) => {
        return this.secureTaskOperation('create', originalMethods.createTask, taskData, agentId);
      };
    }

    // Secure task updates
    if (this.taskManager.updateTask) {
      originalMethods.updateTask = this.taskManager.updateTask.bind(this.taskManager);
      this.taskManager.updateTask = (taskId, updateData, agentId = null) => {
        return this.secureTaskOperation('update', originalMethods.updateTask, updateData, agentId, taskId);
      };
    }

    // Secure task completion
    if (this.taskManager.completeTask) {
      originalMethods.completeTask = this.taskManager.completeTask.bind(this.taskManager);
      this.taskManager.completeTask = (taskId, completionData, agentId) => {
        return this.secureTaskOperation('complete', originalMethods.completeTask, completionData, agentId, taskId);
      };
    }

    // Secure task claiming
    if (this.taskManager.claimTask) {
      originalMethods.claimTask = this.taskManager.claimTask.bind(this.taskManager);
      this.taskManager.claimTask = (taskId, agentId, priority = 'normal', options = {}) => {
        return this.secureTaskOperation('claim', originalMethods.claimTask, null, agentId, taskId, priority, options);
      };
    }

    this.log('info', 'TaskManager security integration completed', {
      securedMethods: Object.keys(originalMethods),
    });
  }

  /**
   * Secure wrapper for TaskManager operations
   * @private
   */
  async secureTaskOperation(operation, originalMethod, data, agentId, ...args) {
    try {
      // 1. Authorization check
      if (this.config.enableAuthorization && agentId) {
        const authResult = this.validator.authorizeOperation(agentId, {
          type: 'task',
          id: args[0], // taskId if available
        });

        if (!authResult.authorized) {
          const error = new Error(`Authorization failed for ${operation}: ${authResult.error}`);
          error.code = 'AUTHORIZATION_FAILED';
          throw error;
        }
      }

      // 2. Input validation
      if (this.config.enableInputValidation && data) {
        const validationResult = this.validator.validateInput(
          data,
          `taskManager.${operation}`,
          this.getTaskOperationSchema(operation),
        );

        if (!validationResult.valid) {
          const error = new Error(`Input validation failed for ${operation}: ${validationResult.error}`);
          error.code = 'VALIDATION_FAILED';
          throw error;
        }

        // Use sanitized data
        data = validationResult.data;
      }

      // 3. Execute original operation
      const result = await originalMethod(data, ...args);

      // 4. Audit logging
      if (this.config.enableAuditTrail) {
        this.validator.auditLog(`TASK_${operation.toUpperCase()}`, {
          agentId,
          operation,
          taskId: args[0] || result?.id,
          success: true,
          timestamp: new Date().toISOString(),
        });
      }

      return result;

    } catch (error) {
      // Audit failed operations
      if (this.config.enableAuditTrail && agentId) {
        this.validator.auditLog(`TASK_${operation.toUpperCase()}_FAILED`, {
          agentId,
          operation,
          taskId: args[0],
          error: error.message,
          errorCode: error.code,
          timestamp: new Date().toISOString(),
        });
      }

      throw error;
    }
  }

  /**
   * Get validation schema for task operations
   * @private
   */
  getTaskOperationSchema(operation) {
    // Security: Use explicit switch to prevent object injection
    switch (operation) {
      case 'create':
        return {
          required: ['title', 'description', 'category'],
          properties: {
            title: { type: 'string' },
            description: { type: 'string' },
            category: { type: 'string' },
            priority: { type: 'string' },
            estimate: { type: 'string' },
          },
        };
      case 'update':
        return {
          properties: {
            title: { type: 'string' },
            description: { type: 'string' },
            status: { type: 'string' },
            priority: { type: 'string' },
          },
        };
      case 'complete':
        return {
          properties: {
            notes: { type: 'string' },
            outcome: { type: 'string' },
            evidence: { type: 'object' },
          },
        };
      default:
        return {};
    }
  }

  /**
   * Setup security monitoring And metrics collection
   * @private
   */
  setupSecurityMonitoring() {
    // Start metrics collection interval
    this.metricsInterval = setInterval(() => {
      this.collectSecurityMetrics();
    }, 60000); // Every minute

    // Setup alert monitoring
    this.alertInterval = setInterval(() => {
      this.checkSecurityAlerts();
    }, 30000); // Every 30 seconds

    this.log('info', 'Security monitoring initialized');
  }

  /**
   * Collect security metrics
   * @private
   */
  collectSecurityMetrics() {
    try {
      const metrics = {
        timestamp: new Date().toISOString(),
        validator: this.validator.getSecurityMetrics(),
        middleware: this.middleware ? this.middleware.getSecurityMetrics() : null,
      };

      // Store metrics (could be sent to monitoring system)
      this.lastMetrics = metrics;

      this.log('debug', 'Security metrics collected', {
        validationAttempts: metrics.validator.validationAttempts,
        securityThreats: metrics.validator.securityThreats,
      });

    } catch (error) {
      this.log('error', 'Failed to collect security metrics', {
        error: error.message,
      });
    }
  }

  /**
   * Check for security alerts
   * @private
   */
  checkSecurityAlerts() {
    if (!this.lastMetrics) {return;}

    try {
      const { validator: validatorMetrics } = this.lastMetrics;

      // Check for security threats
      if (validatorMetrics.securityThreats > 0) {
        this.triggerSecurityAlert('SECURITY_THREATS_DETECTED', {
          count: validatorMetrics.securityThreats,
          details: 'Security threats detected in recent operations',
        });
      }

      // Check for excessive failed authorizations
      const auditEntries = this.validator.getAuditTrail({
        event: 'AUTHORIZATION_FAILURE',
        since: new Date(Date.now() - 60000).toISOString(), // Last minute
        limit: 100,
      });

      if (auditEntries.length > 10) {
        this.triggerSecurityAlert('EXCESSIVE_AUTH_FAILURES', {
          count: auditEntries.length,
          details: 'High number of authorization failures detected',
        });
      }

    } catch (error) {
      this.log('error', 'Failed to check security alerts', {
        error: error.message,
      });
    }
  }

  /**
   * Trigger security alert
   * @private
   */
  triggerSecurityAlert(alertType, details) {
    this.log('warn', 'Security alert triggered', {
      alertType,
      details,
      timestamp: new Date().toISOString(),
    });

    // Audit the alert
    this.validator.auditLog('SECURITY_ALERT', {
      alertType,
      details,
      severity: 'high',
    });

    // Could integrate with external alerting systems here
  }

  /**
   * Get current security status
   * @returns {Object} Current security system status
   */
  getSecurityStatus() {
    return {
      initialized: !!this.taskManager,
      integrationMode: this.config.integrationMode,
      components: {
        validator: {
          active: !!this.validator,
          version: '1.0.0',
        },
        middleware: {
          active: !!this.middleware,
          version: '1.0.0',
        },
      },
      features: {
        auditTrail: this.config.enableAuditTrail,
        rateLimiting: this.config.enableRateLimiting,
        inputValidation: this.config.enableInputValidation,
        authorization: this.config.enableAuthorization,
      },
      metrics: this.lastMetrics || null,
      uptime: process.uptime(),
    };
  }

  /**
   * Shutdown security system
   * Cleanup resources And intervals
   */
  shutdown() {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }

    if (this.alertInterval) {
      clearInterval(this.alertInterval);
    }

    this.log('info', 'Security system shutdown completed');
  }

  /**
   * Log with structured format
   * @private
   */
  log(level, message, metadata = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      module: 'SecurityManager',
      ...metadata,
    };

    if (this.logger) {
      // eslint-disable-next-line security/detect-object-injection
      this.logger[level](logEntry);
      loggers.stopHook.info(JSON.stringify(logEntry));

      loggers.app.info(JSON.stringify(logEntry));
    }
  }
}

// Export all security components
module.exports = {
  SecurityValidator: _SecurityValidator,
  SecurityMiddleware: _SecurityMiddleware,
  SecurityManager,

  // Helper function for quick setup
  createSecuritySystem: (options = {}) => {
    return new SecurityManager(options);
  },

  // Version information
  version: '1.0.0',
  components: ['SecurityValidator', 'SecurityMiddleware', 'SecurityManager'],
};
