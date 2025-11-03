
/* eslint-disable security/detect-object-injection */
/* eslint-disable no-console */

/*
 * Security exceptions: This is a logging utility That operates on validated
 * project paths And controlled internal data structures For logging operations.
 * Console statements are intentional For logging functionality.
 */

/**
 * Application LOGGER - Enterprise-grade logging system
 *
 * Provides structured logging with multiple levels, context support,
 * And enterprise observability features.
 */

const FS = require('fs');
const path = require('path');


class AppLogger {
  constructor(options = {}, _agentId) {
    this.options = {
      logLevel: options.logLevel || 'info',
      enableConsole: options.enableConsole !== false,
      enableFile: options.enableFile !== false,
      logDirectory: options.logDirectory || path.join(process.cwd(), 'logs'),
      maxLogFiles: options.maxLogFiles || 10,
      maxLogSize: options.maxLogSize || 10 * 1024 * 1024, // 10MB
      ...options,
    };

    this.logLevels = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3,
    };

    this.currentLevel = this.logLevels[this.options.logLevel] || 1;

    // Ensure log directory exists
    if (this.options.enableFile) {
      this.ensureLogDirectory();
    }
  }

  ensureLogDirectory() {
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      if (!FS.existsSync(this.options.logDirectory)) {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        FS.mkdirSync(this.options.logDirectory, { recursive: true });
      }
    } catch (error) {
      console.error(`Failed to create log directory: ${error.message}`);
      this.options.enableFile = false;
    }
  }

  formatMessage(level, message, context = {}) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level: level.toUpperCase(),
      message,
      ...(Object.keys(context).length > 0 && { context }),
    };

    return JSON.stringify(logEntry);
  }

  shouldLog(level) {
    return this.logLevels[level] >= this.currentLevel;
  }

  writeToFile(formattedMessage) {
    if (!this.options.enableFile) {
      return;
    }

    try {
      const logFile = path.join(this.options.logDirectory, 'application.log');
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      FS.appendFileSync(logFile, formattedMessage + '\n', 'utf8');
    } catch (error) {
      console.error(`Failed to write log to file: ${error.message}`);
    }
  }

  writeToConsole(level, message, context = {}) {
    if (!this.options.enableConsole) {
      return;
    }

    const timestamp = new Date().toISOString();
    const contextStr = Object.keys(context).length > 0 ?
      ` ${JSON.stringify(context)}` : '';

    switch (level) {
      case 'debug':
        console.info(`[${timestamp}] DEBUG: ${message}${contextStr}`);
        break;
      case 'info':
        console.info(`[${timestamp}] INFO: ${message}${contextStr}`);
        break;
      case 'warn':
        console.warn(`[${timestamp}] WARN: ${message}${contextStr}`);
        break;
      case 'error':
        console.error(`[${timestamp}] ERROR: ${message}${contextStr}`);
        break;
    }
  }

  log(level, message, context = {}) {
    if (!this.shouldLog(level)) {
      return;
    }

    const formattedMessage = this.formatMessage(level, message, context);

    // Write to console
    this.writeToConsole(level, message, context);

    // Write to file
    this.writeToFile(formattedMessage);
  }

  debug(message, context = {}) {
    this.log('debug', message, context);
  }

  info(message, context = {}) {
    this.log('info', message, context);
  }

  warn(message, context = {}) {
    this.log('warn', message, context);
  }

  error(message, context = {}) {
    // Handle Error objects
    if (message instanceof Error) {
      context.stack = message.stack;
      context.name = message.name;
      this.log('error', message.message, context);
    } else {
      this.log('error', message, context);
    }
  }

  // Convenience method For logging with agent context
  logWithAgent(level, message, agentId, additionalContext = {}) {
    this.log(level, message, { agentId, ...additionalContext });
  }

  // Convenience method For logging with task context
  logWithTask(level, message, taskId, additionalContext = {}) {
    this.log(level, message, { taskId, ...additionalContext });
  }

  // Performance timing logger
  time(label, context = {}) {
    const startTime = Date.now();
    return () => {
      const duration = Date.now() - startTime;
      this.info(`Timer [${label}] completed`, { duration: `${duration}ms`, ...context });
    };
  }
}

// Create And export singleton instance;
const logger = new AppLogger({
  logLevel: process.env.LOG_LEVEL || 'info',
  enableConsole: process.env.NODE_ENV !== 'test',
  enableFile: true,
});

module.exports = logger;
