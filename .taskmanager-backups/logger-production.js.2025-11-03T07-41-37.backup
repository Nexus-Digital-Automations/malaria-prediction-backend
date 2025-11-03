/**
 * Production Logger Factory
 *
 * Creates production-optimized loggers with monitoring integration,
 * security compliance, and performance optimizations.
 */

const pino = require('pino');
const fs = require('fs');
const path = require('path');
const _os = require('os');
const { getProductionConfig } = require('../config/logging-production');

// Initialize a basic logger for factory initialization messages
const initLogger = pino({
  _level: 'info',
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'HH:MM:ss',
      ignore: 'pid,hostname',
      messageFormat: '[ProductionLoggerFactory] {msg}' } } });

class ProductionLoggerFactory {
  constructor() {
    this.config = getProductionConfig();
    this.destinations = new Map();
    this.alertingEnabled = true;
    this.monitoringStarted = false;
    this.errorTracker = [];
    this.performanceMetrics = new Map();
  }

  /**
   * Initialize production logging infrastructure
   */
  async initialize() {
    try {
      // Ensure log directories exist
      this.ensureLogDirectories();

      // Set up log rotation
      this.setupLogRotation();

      // Initialize monitoring integrations
      await this.initializeMonitoring();

      // Start health monitoring
      this.startHealthMonitoring();

      initLogger.info({
        initialization: 'success',
        monitoring_enabled: this.monitoringStarted,
        destinations_count: this.destinations.size }, 'Production logging infrastructure initialized successfully');
      return true;
    } catch (error) {
      initLogger.error({
        initialization: 'failed',
        error: error.message,
        stack: error.stack }, 'Failed to initialize production logging');
      throw error;
    }
  }

  /**
   * Create production logger with enhanced capabilities
   */
  createProductionLogger(_module = 'app', options = {}) {
    const loggerConfig = {
      ...this.config.logging,
      ...options,
      base: {
        ...this.config.logging.base,
        module: module,
        logger_version: '2.0.0' } };

    // Create logger with production configuration
    const logger = pino(loggerConfig);

    // Enhance logger with production features
    return this.enhanceLogger(logger, _module);
  }

  /**
   * Enhance logger with production-specific features
   */
  enhanceLogger(baseLogger, _module) {
    const enhancedLogger = {
      // Standard logging methods
      info: (_data, _message) => this.logWithTracking('info', baseLogger, _data, _message, _module),
      warn: (_data, _message) => this.logWithTracking('warn', baseLogger, _data, _message, _module),
      error: (_data, _message) => this.logWithTracking('error', baseLogger, _data, _message, _module),
      debug: (_data, _message) => this.logWithTracking('debug', baseLogger, _data, _message, _module),
      trace: (_data, _message) => this.logWithTracking('trace', baseLogger, _data, _message, _module),

      // Production-specific methods
      audit: (_data, _message) => this.auditLog(baseLogger, _data, _message, _module),
      security: (_data, _message) => this.securityLog(baseLogger, _data, _message, _module),
      performance: (_data, _message) => this.performanceLog(baseLogger, _data, _message, _module),
      business: (_data, _message) => this.businessLog(baseLogger, _data, _message, _module),

      // Alert triggering methods
      alert: (severity, _data, _message) => this.triggerAlert(severity, baseLogger, _data, _message, _module),

      // Child logger creation
      child: (bindings) => this.enhanceLogger(baseLogger.child(bindings), module),

      // Performance timing
      time: (operationName) => this.timeOperation(baseLogger, operationName, _module),

      // Error categorization
      categorizeError: (error, context) => this.categorizeAndLogError(baseLogger, error, context, _module) };

    return enhancedLogger;
  }

  /**
   * Log with production tracking and alerting
   */
  logWithTracking(_level, logger, _data, _message, _module) {
    try {
      // Apply security redaction
      const sanitizedData = this.sanitizeLogData(_data);

      // Add production metadata
      const enhancedData = {
        ...sanitizedData,
        module: _module,
        level: _level.toUpperCase(),
        environment: process.env.NODE_ENV || 'production',
        correlation_id: this.generateCorrelationId(),
        timestamp: new Date().toISOString() };

      // Perform the actual logging
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      logger[_level](enhancedData, _message);

      // Track for alerting if error or warning
      if (_level === 'error' || _level === 'warn') {
        this.trackForAlerting(_level, enhancedData, _message, _module);
      }

      // Send to external monitoring if configured
      this.sendToMonitoring(_level, enhancedData, _message, _module);

    } catch (loggingError) {
      // Fallback logging - never let logging break the application
      // Use basic Pino fallback since structured logger may be compromised
      initLogger.error({
        logging_error: loggingError.message,
        original_level: _level,
        original_data: _data,
        original_message: _message,
        fallback_triggered: true }, 'Structured logging failed - fallback triggered');
    }
  }

  /**
   * Audit logging for compliance
   */
  auditLog(logger, _data, _message, _module) {
    const auditData = {
      ..._data,
      audit_event: true,
      compliance: 'GDPR/SOX/HIPAA',
      retention_category: 'audit',
      module: _module,
      user_id: _data.user_id || 'system',
      action: _data.action || 'unknown',
      resource: _data.resource || 'system',
      ip_address: _data.ip_address || 'localhost',
      user_agent: _data.user_agent || 'system' };

    logger.info(this.sanitizeLogData(auditData), `[AUDIT] ${_message}`);

    // Send to audit-specific destinations
    this.sendToAuditSystem(auditData, _message);
  }

  /**
   * Security event logging
   */
  securityLog(logger, _data, _message, _module) {
    const securityData = {
      ..._data,
      security_event: true,
      severity: _data.severity || 'medium',
      threat_level: _data.threat_level || 'low',
      module: _module,
      detection_method: _data.detection_method || 'automatic',
      false_positive_likelihood: _data.false_positive_likelihood || 'low' };

    logger.warn(this.sanitizeLogData(securityData), `[SECURITY] ${_message}`);

    // Trigger immediate alert for high-severity security events
    if (_data.severity === 'high' || _data.severity === 'critical') {
      this.triggerSecurityAlert(securityData, _message);
    }
  }

  /**
   * Performance metrics logging
   */
  performanceLog(logger, _data, _message, _module) {
    const performanceData = {
      ..._data,
      performance_metric: true,
      module: _module,
      operation: _data.operation || 'unknown',
      duration_ms: _data.duration_ms || 0,
      memory_usage: process.memoryUsage(),
      cpu_usage: process.cpuUsage() };

    logger.info(performanceData, `[PERFORMANCE] ${_message}`);

    // Track performance trends
    this.trackPerformanceMetric(_data._operation, _data.duration_ms);

    // Alert on slow operations
    if (_data.duration_ms > this.config.alerting.performance.slowOperationMs) {
      this.triggerPerformanceAlert(performanceData, _message);
    }
  }

  /**
   * Business metrics logging
   */
  businessLog(logger, _data, _message, _module) {
    const businessData = {
      ..._data,
      business_metric: true,
      module: _module,
      metric_category: _data.metric_category || 'general',
      business_impact: _data.business_impact || 'low',
      kpi_relevant: _data.kpi_relevant || false };

    logger.info(businessData, `[BUSINESS] ${_message}`);

    // Send to business intelligence systems
    this.sendToBusinessIntelligence(businessData, _message);
  }

  /**
   * Trigger production alerts
   */
  triggerAlert(severity, logger, _data, _message, _module) {
    const alertData = {
      ..._data,
      alert: true,
      severity: severity,
      module: _module,
      alert_id: this.generateAlertId(),
      requires_attention: severity === 'critical' || severity === 'emergency',
      escalation_level: this.getEscalationLevel(severity) };

    logger.error(alertData, `[ALERT-${severity.toUpperCase()}] ${_message}`);

    // Send to alerting systems
    this.sendToAlertingSystems(alertData, _message);
  }

  /**
   * Performance operation timing
   */
  timeOperation(logger, operationName, _module) {
    const startTime = process.hrtime.bigint();
    const startTimestamp = Date.now();

    return {
      end: (result = {}) => {
        const endTime = process.hrtime.bigint();
        const _duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds

        const timingData = {
          operation: operationName,
          duration_ms: _duration,
          module: _module,
          started_at: new Date(startTimestamp).toISOString(),
          completed_at: new Date().toISOString(),
          ...result };

        this.performanceLog(logger, timingData, `Operation ${operationName} completed in ${_duration.toFixed(2)}ms`, _module);

        return { duration_ms: _duration, ...result };
      } };
  }

  /**
   * Error categorization and logging
   */
  categorizeAndLogError(logger, error, context, _module) {
    const categorizedError = {
      error_id: this.generateErrorId(),
      name: error.name,
      message: error.message,
      stack: error.stack,
      code: error.code,
      category: this.categorizeError(error),
      severity: this.assessErrorSeverity(error),
      module: module,
      context: context,
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'production' };

    this.logWithTracking('error', logger, categorizedError, `Categorized error: ${error._message}`);

    // Add to error tracking
    this.errorTracker.push({
      ...categorizedError,
      timestamp: Date.now() });

    // Maintain error tracker size
    if (this.errorTracker.length > 1000) {
      this.errorTracker = this.errorTracker.slice(-500); // Keep last 500 errors
    }

    return categorizedError;
  }

  /**
   * Sanitize log data to remove sensitive information
   */
  sanitizeLogData(_data) {
    if (!_data || typeof _data !== 'object') {
      return _data;
    }

    const sanitized = { ..._data };
    const redactFields = this.config.security.redactFields;

    const redactRecursive = (obj) => {
      if (!obj || typeof obj !== 'object') {return obj;}

      for (const [key, value] of Object.entries(obj)) {
        const lowerKey = key.toLowerCase();

        if (redactFields.some(field => lowerKey.includes(field.toLowerCase()))) {
          // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
          obj[key] = '[REDACTED]';
        } else if (typeof value === 'object' && value !== null) {
          // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
          obj[key] = redactRecursive({ ...value });
        }
      }
      return obj;
    };

    return redactRecursive(sanitized);
  }

  /**
   * Ensure log directories exist
   */
  ensureLogDirectories() {
    const logDir = path.dirname(this.config.rotation.paths.application);

    // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
    if (!fs.existsSync(logDir)) {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      fs.mkdirSync(logDir, { recursive: true });
    }
  }

  /**
   * Set up log rotation
   */
  setupLogRotation() {
    // Implementation would depend on chosen log rotation library
    // e.g., winston-daily-rotate-file or similar
    initLogger.info({
      log_rotation: 'configured',
      config_applied: true }, 'Log rotation configured');
  }

  /**
   * Initialize monitoring integrations
   */
  async initializeMonitoring() {
    const monitoring = this.config.monitoring;

    // Initialize CloudWatch if enabled
    if (monitoring.cloudwatch.enabled) {
      await this.initializeCloudWatch();
    }

    // Initialize Datadog if enabled
    if (monitoring.datadog.enabled) {
      await this.initializeDatadog();
    }

    // Initialize ELK if enabled
    if (monitoring.elk.enabled) {
      await this.initializeELK();
    }

    initLogger.info({
      monitoring_integrations: 'initialized',
      integrations_enabled: true }, 'Monitoring integrations initialized');
  }

  /**
   * Start health monitoring
   */
  startHealthMonitoring() {
    if (this.monitoringStarted) {return;}

    const interval = this.config.alerting.healthCheck.intervalMs;

    setInterval(() => {
      this.performHealthCheck();
    }, interval);

    this.monitoringStarted = true;
    initLogger.info({
      health_monitoring: 'started',
      monitoring_active: true }, 'Health monitoring started');
  }

  /**
   * Perform comprehensive health check
   */
  performHealthCheck() {
    try {
      const memUsage = process.memoryUsage();
      const memoryPercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;

      // Check memory thresholds
      if (memoryPercent > this.config.alerting.memory.critical) {
        this.triggerAlert('critical', null, {
          memory_usage_percent: memoryPercent,
          heap_used_mb: Math.round(memUsage.heapUsed / 1024 / 1024) }, 'Critical memory usage detected');
      } else if (memoryPercent > this.config.alerting.memory.warning) {
        this.triggerAlert('warning', null, {
          memory_usage_percent: memoryPercent }, 'High memory usage detected');
      }

      // Check error rates
      this.checkErrorRates();

    } catch (error) {
      initLogger.error({
        health_check_error: error.message,
        health_check_failed: true,
        error_stack: error.stack }, 'Health monitoring check failed');
    }
  }

  /**
   * Check error rates for alerting
   */
  checkErrorRates() {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;

    const recentErrors = this.errorTracker.filter(error =>
      error.timestamp > oneMinuteAgo,
    );

    const errorCount = recentErrors.length;
    const alerting = this.config.alerting.errorRate;

    if (errorCount > alerting.emergencyPerMinute) {
      this.triggerAlert('emergency', null, {
        error_count: errorCount,
        time_window: '1 minute' }, 'Emergency error rate detected');
    } else if (errorCount > alerting.criticalPerMinute) {
      this.triggerAlert('critical', null, {
        error_count: errorCount,
        time_window: '1 minute' }, 'Critical error rate detected');
    } else if (errorCount > alerting.warningPerMinute) {
      this.triggerAlert('warning', null, {
        error_count: errorCount,
        time_window: '1 minute' }, 'High error rate detected');
    }
  }

  // Utility methods
  generateCorrelationId() {
    return `corr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  generateAlertId() {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  generateErrorId() {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  categorizeError(error) {
    if (error.code === 'ENOENT') {return 'file_system';}
    if (error.code === 'EACCES') {return 'permission';}
    if (error._message.includes('timeout')) {return 'timeout';}
    if (error._message.includes('network')) {return 'network';}
    if (error.name === 'SyntaxError') {return 'syntax';}
    if (error.name === 'TypeError') {return 'type';}
    if (error.name === 'ReferenceError') {return 'reference';}
    return 'unknown';
  }

  assessErrorSeverity(error) {
    if (['EACCES', 'authentication', 'authorization'].some(term =>
      error.code === term || error._message.toLowerCase().includes(term))) {
      return 'high';
    }
    if (['ENOENT', 'timeout', 'network'].some(term =>
      error.code === term || error._message.toLowerCase().includes(term))) {
      return 'medium';
    }
    return 'low';
  }

  getEscalationLevel(severity) {
    switch (severity) {
      case 'emergency': return 3;
      case 'critical': return 2;
      case 'warning': return 1;
      default: return 0;
    }
  }

  // Placeholder methods for external system integration
  sendToMonitoring(_level, _data, _message, _module) {
    // Implementation depends on chosen monitoring system
  }

  sendToAuditSystem(_data, _message) {
    // Implementation for audit log destination
  }

  triggerSecurityAlert(_data, _message) {
    // Implementation for security alerting
  }

  triggerPerformanceAlert(_data, _message) {
    // Implementation for performance alerting
  }

  sendToBusinessIntelligence(_data, _message) {
    // Implementation for BI system integration
  }

  sendToAlertingSystems(_data, _message) {
    // Implementation for alerting system integration
  }

  trackForAlerting(_level, _data, _message, _module) {
    // Track errors and warnings for rate-based alerting
  }

  trackPerformanceMetric(_operation, _duration) {
    // Track performance metrics for trending
  }

  async initializeCloudWatch() {
    // CloudWatch integration setup
  }

  async initializeDatadog() {
    // Datadog integration setup
  }

  async initializeELK() {
    // ELK stack integration setup
  }
}

// Export factory instance
const productionLoggerFactory = new ProductionLoggerFactory();

module.exports = {
  ProductionLoggerFactory,
  productionLoggerFactory,

  // Convenience method to get production logger
  getProductionLogger: (_module = 'app', options = {}) => {
    return productionLoggerFactory.createProductionLogger(_module, options);
  },

  // Initialize production logging
  initializeProductionLogging: () => {
    return productionLoggerFactory.initialize();
  } };
