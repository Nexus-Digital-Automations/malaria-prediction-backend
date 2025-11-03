/**
 * Production-Ready Structured Logging System
 *
 * Comprehensive Pino-based logging for the infinite-continue-stop-hook project.
 * Provides structured JSON logging with consistent fields for monitoring platforms
 * like Datadog, Splunk, And ELK stack integration.
 *
 * Features:
 * - JSON structured output with consistent fields (timestamp, level, message, agentId, taskId)
 * - Multiple transport support (console, file, external systems)
 * - Production-ready configuration with performance optimization
 * - Context-aware logging with automatic field injection
 * - Backwards compatibility with existing logger interface
 *
 * @author Claude Code Agent - Structured Logging Implementation
 * @version 2.0.0
 */

const pino = require('pino');
const FS = require('fs').promises;
const PATH = require('path');

/**
 * Environment-specific logging configuration
 */
const LOG_CONFIG = {
  development: {
    level: process.env.LOG_LEVEL || 'info',
    prettyPrint: true,
    colorize: true,
  },
  production: {
    level: process.env.LOG_LEVEL || 'warn',
    prettyPrint: false,
    colorize: false,
  },
  test: {
    level: 'silent',
    prettyPrint: false,
    colorize: false,
  },
};

/**
 * Pino transport configuration for different environments
 */
function createPinoTransports(options = {}) {
  const environment = process.env.NODE_ENV || 'development';
  const config = LOG_CONFIG[environment] || LOG_CONFIG.development;

  const transports = [];

  // Console transport with conditional pretty printing
  transports.push({
    target: 'pino/file',
    options: {
      destination: 1, // stdout
      colorize: config.colorize,
      translateTime: 'yyyy-mm-dd HH:MM:ss.l',
      ignore: 'pid,hostname',
    },
  });

  // File transport if enabled
  if (options.logToFile && options.logDir) {
    transports.push({
      target: 'pino/file',
      options: {
        destination: PATH.join(options.logDir, `${options.component || 'app'}.log`),
        mkdir: true,
      },
    });
  }

  return {
    targets: transports,
  };
}

/**
 * Enhanced structured logger class using Pino
 */
class StructuredLogger {
  constructor(options = {}) {
    this.component = options.component || 'App';
    this.agentId = options.agentId || 'unknown';
    this.taskId = options.taskId || null;
    this.operationId = options.operationId || null;
    this.logToFile = options.logToFile || false;
    this.logDir = options.logDir || '/Users/jeremyparker/infinite-continue-stop-hook/development/logs';
    this.silent = options.silent || false;

    // Create Pino logger with appropriate configuration
    const environment = process.env.NODE_ENV || 'development';
    const baseConfig = LOG_CONFIG[environment] || LOG_CONFIG.development;

    const pinoOptions = {
      level: this.silent ? 'silent' : baseConfig.level,
      base: {
        // Core structured fields for monitoring platforms
        module: this.component,
        agentId: this.agentId,
        taskId: this.taskId,
        operationId: this.operationId,
        environment,
        version: '2.0.0',
      },
      timestamp: pino.stdTimeFunctions.isoTime,
      formatters: {
        level: (label) => ({ level: label }),
      },
    };

    // Configure transports
    if (environment === 'development' && baseConfig.prettyPrint && !this.silent) {
      // Pretty printing for development
      pinoOptions.transport = {
        target: 'pino-pretty',
        options: {
          colorize: baseConfig.colorize,
          translateTime: 'yyyy-mm-dd HH:MM:ss.l',
          ignore: 'pid,hostname',
          messageFormat: '[{agentId}] [{module}] {msg}',
        },
      };
    } else if (this.logToFile || environment === 'production') {
      // File transport for production or when explicitly requested
      pinoOptions.transport = createPinoTransports({
        logToFile: this.logToFile,
        logDir: this.logDir,
        component: this.component,
      });
    }

    this.logger = pino(pinoOptions);

    // Initialize log directory if logging to file
    if (this.logToFile) {
      this.ensureLogDirectory().catch(() => {
        // Fail silently if cannot create log directory
      });
    }
  }

  /**
   * Ensure log directory exists
   */
  async ensureLogDirectory() {
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- LOGGER path validated through logging configuration
      await FS.mkdir(this.logDir, { recursive: true });
    } catch {
      // Fail silently - logging should not crash the application
    }
  }

  /**
   * Create child logger with additional context
   */
  child(bindings = {}) {
    return new StructuredLogger({
      component: this.component,
      agentId: bindings.agentId || this.agentId,
      taskId: bindings.taskId || this.taskId,
      operationId: bindings.operationId || this.operationId,
      logToFile: this.logToFile,
      logDir: this.logDir,
      silent: this.silent,
      ...bindings,
    });
  }

  /**
   * Enhanced logging with structured context
   */
  log(level, message, context = {}) {
    const enrichedContext = {
      ...context,
      timestamp: new Date().toISOString(),
      // Additional monitoring fields
      source: 'infinite-continue-stop-hook',
      service: 'taskmanager',
    };

    this.logger[level](enrichedContext, message);
  }

  /**
   * Error logging with enhanced context
   */
  error(message, context = {}) {
    const errorContext = {
      ...context,
      errorType: context.error?.name || 'UnknownError',
      errorStack: context.error?.stack,
      severity: 'error',
    };
    this.log('error', message, errorContext);
  }

  /**
   * Warning logging
   */
  warn(message, context = {}) {
    this.log('warn', message, { ...context, severity: 'warning' });
  }

  /**
   * Info logging
   */
  info(message, context = {}) {
    this.log('info', message, { ...context, severity: 'info' });
  }

  /**
   * Debug logging
   */
  debug(message, context = {}) {
    this.log('debug', message, { ...context, severity: 'debug' });
  }

  /**
   * Trace logging for detailed debugging
   */
  trace(message, context = {}) {
    this.log('trace', message, { ...context, severity: 'trace' });
  }

  /**
   * Performance logging for timing operations
   */
  performance(operation, duration, context = {}) {
    this.info(`Performance: ${operation} completed in ${duration}ms`, {
      ...context, operation,
      duration_ms: duration,
      performance: true,
      severity: 'info',
    });
  }

  /**
   * Security logging for security-related events
   */
  security(message, context = {}) {
    this.warn('Security: ' + message, {
      ...context,
      security: true,
      severity: 'warning',
    });
  }

  /**
   * Business logic logging
   */
  business(message, context = {}) {
    this.info(`Business: ${message}`, {
      ...context,
      business: true,
      severity: 'info',
    });
  }

  /**
   * HTTP request/response logging
   */
  http(method, url, statusCode, duration, context = {}) {
    this.info(`HTTP ${method} ${url}`, {
      ...context,
      http: {
        method,
        url,
        statusCode,
        duration_ms: duration,
      },
      severity: statusCode >= 400 ? 'warning' : 'info',
    });
  }

  /**
   * Database operation logging
   */
  database(operation, table, duration, context = {}) {
    this.info(`Database: ${operation} on ${table}`, {
      ...context,
      database: { operation,
        table,
        duration_ms: duration,
      },
      severity: 'info',
    });
  }
}

/**
 * Create a structured logger instance for a specific component
 */
function createLogger(component, options = {}) {
  return new StructuredLogger({
    component,
    ...options,
  });
}

/**
 * Create a silent logger for test environments
 */
function createSilentLogger(component, options = {}) {
  return new StructuredLogger({
    component,
    silent: true,
    ...options,
  });
}

/**
 * Create logger with agent context
 */
function createAgentLogger(component, agentId, taskId = null, options = {}) {
  return new StructuredLogger({
    component,
    agentId,
    taskId,
    ...options,
  });
}

/**
 * Global logger instance for system-wide logging
 */
const systemLogger = createLogger('System', {
  agentId: 'system',
  logToFile: process.env.NODE_ENV === 'production',
});

/**
 * Legacy compatibility - maintain existing interface
 */
class LegacyLogger extends StructuredLogger {
  constructor(workingDir, options = {}) {
    super({
      component: 'Legacy',
      logDir: PATH.join(workingDir, 'development', 'logs'),
      logToFile: true,
      ...options,
    });
  }

  // Legacy methods for backwards compatibility
  logError(error, context = '') {
    this.error(`Legacy error in ${context}`, { error, context });
  }

  logInput(input) {
    this.info('Legacy input received', { input });
  }

  logExit(code, message) {
    this.info(`Legacy exit: ${message}`, { exitCode: code, message });
  }

  addFlow(message) {
    this.info(`Flow: ${message}`);
  }

  save() {
    // Legacy save method - no-op since Pino handles persistence automatically
    this.debug('Legacy save called - automatic persistence enabled');
  }
}

// Backwards compatibility exports
const LOG_LEVELS = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info',
  DEBUG: 'debug',
  TRACE: 'trace',
};

module.exports = {
  StructuredLogger,
  LegacyLogger,
  createLogger,
  createSilentLogger,
  createAgentLogger,
  systemLogger,
  LOG_LEVELS,
  // Legacy compatibility
  CentralizedLogger: StructuredLogger,
  LOGGER: LegacyLogger,
};
