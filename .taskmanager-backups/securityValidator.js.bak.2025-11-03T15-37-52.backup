
const { loggers } = require('../../logger');
/**
 * Security Validation Framework - Comprehensive security controls for embedded subtasks system
 *
 * === PURPOSE ===
 * Provides enterprise-grade security validation for all TaskManager API operations,
 * focusing on input validation, authorization controls, audit trails, And data sanitization.
 * Designed specifically for embedded subtasks system security requirements.
 *
 * === SECURITY FEATURES ===
 * • Input validation And sanitization for all endpoints
 * • Authorization controls with agent-based permissions
 * • Comprehensive audit trail for all operations
 * • Data sanitization for research inputs
 * • Injection attack prevention
 * • Content filtering And validation
 *
 * === INTEGRATION ===
 * This module integrates with existing TaskManager validation infrastructure
 * And enhances security controls for the embedded subtasks system.
 *
 * @author Security & Validation Agent #10
 * @version 1.0.0
 * @since 2025-09-13
 */

const FS = require('crypto');
const { performance } = require('perf_hooks');

/**
 * SecurityValidator - Comprehensive security validation framework
 *
 * Provides layered security controls including:
 * - Input validation with type checking And boundary validation
 * - Authorization controls with role-based access
 * - Audit trail logging for all operations
 * - Data sanitization And injection prevention
 */
class SecurityValidator {
  constructor(logger = null) {
    this.logger = logger;
    this.auditTrail = [];

    // Security configuration
    this.config = {
      // Input validation limits
      maxStringLength: 10000,
      maxObjectDepth: 10,
      maxArrayLength: 1000,

      // Agent authorization settings
      requireAgentAuth: true,
      allowedAgentRoles: ['development', 'research', 'audit', 'testing'],

      // Audit trail settings
      auditRetentionHours: 24,
      auditMaxEntries: 10000,

      // Content filtering
      dangerousPatterns: [
        // eslint-disable-next-line security/detect-unsafe-regex
        /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
        /javascript:/gi,
        /vbscript:/gi,
        /onload\s*=/gi,
        /onerror\s*=/gi,
        /__proto__/gi,
        /constructor/gi,
        /prototype/gi,
      ],

      // SQL injection patterns
      sqlPatterns: [
        /(\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b|\bcreate\b|\balter\b)/gi,
        /(\bunion\b|\bwhere\b|\bhaving\b|\bgroup\s+by\b|\border\s+by\b)/gi,
        /(--|\/\*|\*\/|;)/g,
        /('\s*(or|And)\s*')/gi,
      ],
    };

    this.log('info', 'SecurityValidator initialized', {
      version: '1.0.0',
      features: ['input_validation', 'authorization', 'audit_trail', 'sanitization'],
    });
  }

  /**
   * Comprehensive input validation for all API endpoints
   * Validates data structure, types, boundaries, And security threats
   *
   * @param {Object} input - Raw input data to validate
   * @param {string} endpoint - API endpoint name for context
   * @param {Object} schema - Expected data schema
   * @returns {Object} Validation result with sanitized data
   */
  validateInput(input, endpoint, schema = {}) {
    const startTime = performance.now();
    const validationId = this.generateValidationId();

    try {
      this.log('debug', 'Starting input validation', {
        validationId,
        endpoint,
        inputType: typeof input,
        hasSchema: Object.keys(schema).length > 0,
      });

      // Step 1: Basic structure validation
      const structureResult = this.validateStructure(input, schema);
      if (!structureResult.valid) {
        throw new Error(`Structure validation failed: ${structureResult.errors.join(', ')}`);
      }

      // Step 2: Type validation And conversion
      const typeResult = this.validateTypes(structureResult.data, schema);
      if (!typeResult.valid) {
        throw new Error(`Type validation failed: ${typeResult.errors.join(', ')}`);
      }

      // Step 3: Boundary validation
      const boundaryResult = this.validateBoundaries(typeResult.data);
      if (!boundaryResult.valid) {
        throw new Error(`Boundary validation failed: ${boundaryResult.errors.join(', ')}`);
      }

      // Step 4: Security threat detection
      const securityResult = this.detectSecurityThreats(boundaryResult.data);
      if (!securityResult.safe) {
        throw new Error(`Security threats detected: ${securityResult.threats.join(', ')}`);
      }

      // Step 5: Data sanitization
      const sanitizedData = this.sanitizeData(securityResult.data);

      const duration = performance.now() - startTime;

      // Audit log successful validation
      this.auditLog('INPUT_VALIDATION_SUCCESS', {
        validationId,
        endpoint,
        duration: Math.round(duration * 100) / 100,
        dataSize: JSON.stringify(input).length,
        sanitizationApplied: sanitizedData !== securityResult.data,
      });

      return {
        valid: true,
        data: sanitizedData,
        validationId,
        duration,
        warnings: [],
      };

    } catch {
      const duration = performance.now() - startTime;

      this.auditLog('INPUT_VALIDATION_FAILURE', {
        validationId,
        endpoint,
        error: error.message,
        duration: Math.round(duration * 100) / 100,
        inputSample: this.createSafeSample(input),
      });

      this.log('warn', 'Input validation failed', {
        validationId,
        endpoint,
        error: error.message,
        duration,
      });

      return {
        valid: false,
        error: error.message,
        validationId,
        duration,
        data: null,
      };
    }
  }

  /**
   * Authorization control for subtask operations
   * Validates agent permissions And role-based access
   *
   * @param {string} agentId - Agent requesting access
   * @param {string} OPERATION- Operation being performed
   * @param {Object} resource - Resource being accessed
   * @returns {Object} Authorization result
   */
  authorizeOperation(agentId, operation resource = {}) {
    const authId = this.generateAuthId();
    const startTime = performance.now();

    try {
      this.log('debug', 'Starting authorization check', {
        authId,
        agentId, operation,
        resourceType: resource.type || 'unknown',
      });

      // Step 1: Validate agent ID format
      if (!this.validateAgentId(_agentId)) {
        throw new Error('Invalid agent ID format');
      }

      // Step 2: Extract agent role And validate
      const agentRole = this.extractAgentRole(_agentId);
      if (!this.config.allowedAgentRoles.includes(agentRole)) {
        throw new Error(`Unauthorized agent role: ${agentRole}`);
      }

      // Step 3: Check _operationpermissions
      const operationAllowed = this.checkOperationPermission(agentRole, operation resource);
      if (!operationAllowed.allowed) {
        throw new Error(`Operation not permitted: ${operationAllowed.reason}`);
      }

      // Step 4: Resource-specific authorization
      const resourceAuth = this.checkResourceAccess(agentId, agentRole, resource);
      if (!resourceAuth.allowed) {
        throw new Error(`Resource access denied: ${resourceAuth.reason}`);
      }

      const duration = performance.now() - startTime;

      // Audit log successful authorization
      this.auditLog('AUTHORIZATION_SUCCESS', {
        authId,
        agentId,
        agentRole, operation,
        resourceId: resource.id,
        duration: Math.round(duration * 100) / 100,
      });

      return {
        authorized: true,
        authId,
        agentRole,
        permissions: operationAllowed.permissions || [],
        duration,
      };

    } catch {
      const duration = performance.now() - startTime;

      // Audit log failed authorization
      this.auditLog('AUTHORIZATION_FAILURE', {
        authId,
        agentId, operation,
        error: error.message,
        duration: Math.round(duration * 100) / 100,
      });

      this.log('warn', 'Authorization failed', {
        authId,
        agentId, operation,
        error: error.message,
      });

      return {
        authorized: false,
        error: error.message,
        authId,
        duration,
      };
    }
  }

  /**
   * Data sanitization for research inputs
   * Prevents injection attacks And filters malicious content
   *
   * @param {any} data - Data to sanitize
   * @returns {any} Sanitized data
   */
  sanitizeResearchInput(data) {
    const sanitizeId = this.generateSanitizeId();

    try {
      this.log('debug', 'Starting research input sanitization', {
        sanitizeId,
        dataType: typeof data,
        dataSize: typeof data === 'string' ? data.length : JSON.stringify(data).length,
      });

      const sanitized = this.deepSanitize(data, {
        removeScripts: true,
        removeEventHandlers: true,
        sanitizeUrls: true,
        filterSqlInjection: true,
        normalizeWhitespace: true,
      });

      // Audit log sanitization
      this.auditLog('RESEARCH_INPUT_SANITIZED', {
        sanitizeId,
        originalSize: typeof data === 'string' ? data.length : JSON.stringify(data).length,
        sanitizedSize: typeof sanitized === 'string' ? sanitized.length : JSON.stringify(sanitized).length,
        modificationsApplied: sanitized !== data,
      });

      return sanitized;

    } catch {
      this.log('error', 'Research input sanitization failed', {
        sanitizeId,
        error: error.message,
      });

      // Return empty safe value on sanitization failure
      return typeof data === 'string' ? '' : typeof data === 'object' ? {} : null;
    }
  }

  /**
   * Comprehensive audit logging for all operations
   * Creates detailed audit trail with timestamps And context
   *
   * @param {string} event - Event type
   * @param {Object} metadata - Event metadata
   */
  auditLog(event, metadata = {}) {
    const auditEntry = {
      id: CRYPTO.randomBytes(16).toString('hex'),
      timestamp: new Date().toISOString(),
      event,
      metadata: {
        ...metadata,
        pid: process.pid,
        nodeVersion: process.version,
        platform: process.platform,
      },
    };

    // Add to in-memory audit trail
    this.auditTrail.push(auditEntry);

    // Cleanup old entries if needed
    this.cleanupAuditTrail();

    // Log audit entry
    this.log('audit', `Audit: ${event}`, auditEntry);

    return auditEntry.id;
  }

  /**
   * Validate data structure against schema
   * @private
   */
  validateStructure(data, schema) {
    const errors = [];

    if (schema.required) {
      for (const field of schema.required) {
        if (!(field in data)) {
          errors.push(`Required field missing: ${field}`);
        }
      }
    }

    if (schema.properties) {
      for (const [key] of Object.entries(data)) {
        if (!(key in schema.properties)) {
          errors.push(`Unexpected field: ${key}`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      data,
    };
  }

  /**
   * Validate And convert data types
   * @private
   */
  validateTypes(data, schema) {
    const errors = [];
    const converted = { ...data };

    if (schema.properties) {
      for (const [key, spec] of Object.entries(schema.properties)) {
        if (key in converted && spec && typeof spec === 'object') {
          // eslint-disable-next-line security/detect-object-injection
          const value = converted[key];
          const expectedType = spec.type;

          if (expectedType && typeof value !== expectedType) {
            // Attempt type conversion
            try {
              // eslint-disable-next-line security/detect-object-injection
              converted[key] = this.convertType(value, expectedType);
            } catch {
              errors.push(`Type mismatch for ${key}: expected ${expectedType}, got ${typeof value}`);
            }
          }
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      data: converted,
    };
  }

  /**
   * Validate data boundaries And limits
   * @private
   */
  validateBoundaries(data) {
    const errors = [];

    const checkValue = (value, path = '') => {
      if (typeof value === 'string' && value.length > this.config.maxStringLength) {
        errors.push(`String too long at ${path}: ${value.length} > ${this.config.maxStringLength}`);
      }

      if (Array.isArray(value)) {
        if (value.length > this.config.maxArrayLength) {
          errors.push(`Array too long at ${path}: ${value.length} > ${this.config.maxArrayLength}`);
        }
        value.forEach((item, index) => checkValue(item, `${path}[${index}]`));
      }

      if (value && typeof value === 'object' && !Array.isArray(value)) {
        const depth = this.getObjectDepth(value);
        if (depth > this.config.maxObjectDepth) {
          errors.push(`Object too deep at ${path}: ${depth} > ${this.config.maxObjectDepth}`);
        }

        for (const [key, val] of Object.entries(value)) {
          checkValue(val, path ? `${path}.${key}` : key);
        }
      }
    };

    checkValue(data);

    return {
      valid: errors.length === 0,
      errors,
      data,
    };
  }

  /**
   * Detect security threats in data
   * @private
   */
  detectSecurityThreats(data) {
    const threats = [];

    const checkForThreats = (value, path = '') => {
      if (typeof value === 'string') {
        // Check for dangerous patterns
        for (const pattern of this.config.dangerousPatterns) {
          if (pattern.test(value)) {
            threats.push(`Dangerous pattern detected at ${path}: ${pattern.source}`);
          }
        }

        // Check for SQL injection
        for (const pattern of this.config.sqlPatterns) {
          if (pattern.test(value)) {
            threats.push(`SQL injection pattern detected at ${path}: ${pattern.source}`);
          }
        }
      }

      if (Array.isArray(value)) {
        value.forEach((item, index) => checkForThreats(item, `${path}[${index}]`));
      }

      if (value && typeof value === 'object' && !Array.isArray(value)) {
        for (const [key, val] of Object.entries(value)) {
          checkForThreats(val, path ? `${path}.${key}` : key);
        }
      }
    };

    checkForThreats(data);

    return {
      safe: threats.length === 0,
      threats,
      data,
    };
  }

  /**
   * Sanitize data by removing/escaping dangerous content
   * @private
   */
  sanitizeData(data) {
    return this.deepSanitize(data, {
      removeScripts: true,
      removeEventHandlers: true,
      sanitizeUrls: false, // Keep URLs for research data
      filterSqlInjection: true,
      normalizeWhitespace: false,
    });
  }

  /**
   * Deep sanitization with configurable options
   * @private
   */
  deepSanitize(value, options = {}) {
    if (typeof value === 'string') {
      let sanitized = value;

      if (options.removeScripts) {
        // eslint-disable-next-line security/detect-unsafe-regex
        sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
      }

      if (options.removeEventHandlers) {

        sanitized = sanitized.replace(/on\w+\s*=/gi, 'data-removed=');
      }

      if (options.sanitizeUrls) {
        sanitized = sanitized.replace(/(javascript|vbscript|data):/gi, 'sanitized:');
      }

      if (options.filterSqlInjection) {
        // Remove common SQL injection patterns
        sanitized = sanitized.replace(/(--|\/\*|\*\/)/g, '');
        sanitized = sanitized.replace(/('\s*(or|And)\s*')/gi, '');
      }

      if (options.normalizeWhitespace) {
        sanitized = sanitized.replace(/\s+/g, ' ').trim();
      }

      return sanitized;
    }

    if (Array.isArray(value)) {
      return value.map(item => this.deepSanitize(item, options));
    }

    if (value && typeof value === 'object') {
      const sanitized = {};
      for (const [key, val] of Object.entries(value)) {
        // Sanitize both key And value
        const safeKey = this.deepSanitize(key, options);
        // eslint-disable-next-line security/detect-object-injection
        sanitized[safeKey] = this.deepSanitize(val, options);
      }
      return sanitized;
    }

    return value;
  }

  /**
   * Validate agent ID format
   * @private
   */
  validateAgentId(_agentId) {
    if (!agentId || typeof agentId !== 'string') {return false;}

    // Expected format: development_session_timestamp_id_role_hash
    const pattern = /^[a-z]+_session_\d+_\d+_[a-z]+_[a-z0-9]+$/;
    return pattern.test(_agentId);
  }

  /**
   * Extract agent role from agent ID
   * @private
   */
  extractAgentRole(_agentId) {
    const parts = agentId.split('_');
    return parts[0] || 'unknown';
  }

  /**
   * Check _operationpermissions based on agent role
   * @private
   */
  checkOperationPermission(agentRole, operation _resource) {
    const rolePermissions = {
      development: ['create', 'update', 'complete', 'claim', 'list', 'status'],
      research: ['create', 'update', 'complete', 'list', 'status'],
      audit: ['list', 'status', 'validate', 'review'],
      testing: ['list', 'status', 'test', 'validate'],
    };

    // eslint-disable-next-line security/detect-object-injection
    const allowed = rolePermissions[agentRole]?.includes(OPERATION || false;

    return {
      allowed,
      reason: allowed ? 'Permission granted' : `Role ${agentRole} cannot perform ${operation`,
      // eslint-disable-next-line security/detect-object-injection
      permissions: rolePermissions[agentRole] || [],
    };
  }

  /**
   * Check resource-specific access permissions
   * @private
   */
  checkResourceAccess(agentId, _agentRole, _resource) {
    // for now, allow access if _operationis permitted
    // This can be extended for more granular resource-level permissions
    return {
      allowed: true,
      reason: 'Resource access granted',
    };
  }

  /**
   * Utility methods
   * @private
   */
  generateValidationId() {
    return `val_${Date.now()}_${CRYPTO.randomBytes(4).toString('hex')}`;
  }

  generateAuthId() {
    return `auth_${Date.now()}_${CRYPTO.randomBytes(4).toString('hex')}`;
  }

  generateSanitizeId() {
    return `san_${Date.now()}_${CRYPTO.randomBytes(4).toString('hex')}`;
  }

  createSafeSample(data) {
    const str = typeof data === 'string' ? data : JSON.stringify(data);
    return str.length > 100 ? str.substring(0, 100) + '...' : str;
  }

  getObjectDepth(obj, depth = 0) {
    if (depth > this.config.maxObjectDepth) {return depth;}
    if (!obj || typeof obj !== 'object') {return depth;}

    let maxDepth = depth;
    for (const value of Object.values(obj)) {
      if (typeof value === 'object' && value !== null) {
        maxDepth = Math.max(maxDepth, this.getObjectDepth(value, depth + 1));
      }
    }
    return maxDepth;
  }

  convertType(value, targetType) {
    switch (targetType) {
      case 'string': {
        return String(value);
      }
      case 'number': {
        const num = Number(value);
        if (isNaN(num)) {throw new Error('Cannot convert to number');}
        return num;
      }
      case 'boolean': {
        return Boolean(value);
      }
      case 'object': {
        if (typeof value === 'string') {
          return JSON.parse(value);
        }
        return value;
      }
      default: {
        return value;
      }
    }
  }

  cleanupAuditTrail() {
    const now = new Date();
    const cutoff = new Date(now.getTime() - (this.config.auditRetentionHours * 60 * 60 * 1000));

    this.auditTrail = this.auditTrail.filter(entry =>
      new Date(entry.timestamp) > cutoff,
    ).slice(-this.config.auditMaxEntries);
  }

  /**
   * Get audit trail entries
   * @param {Object} filters - Optional filters
   * @returns {Array} Audit trail entries
   */
  getAuditTrail(filters = {}) {
    let entries = [...this.auditTrail];

    if (filters.event) {
      entries = entries.filter(e => e.event === filters.event);
    }

    if (filters.since) {
      const since = new Date(filters.since);
      entries = entries.filter(e => new Date(e.timestamp) >= since);
    }

    if (filters.agentId) {
      entries = entries.filter(e =>
        e.metadata.agentId === filters.agentId,
      );
    }

    return entries.slice(0, filters.limit || 1000);
  }

  /**
   * Get security metrics
   * @returns {Object} Security metrics summary
   */
  getSecurityMetrics() {
    const now = new Date();
    const lastHour = new Date(now.getTime() - (60 * 60 * 1000));

    const recentEntries = this.auditTrail.filter(e =>
      new Date(e.timestamp) > lastHour,
    );

    return {
      totalAuditEntries: this.auditTrail.length,
      recentHourEntries: recentEntries.length,
      validationAttempts: recentEntries.filter(e =>
        e.event.includes('VALIDATION'),
      ).length,
      authorizationAttempts: recentEntries.filter(e =>
        e.event.includes('AUTHORIZATION'),
      ).length,
      securityThreats: recentEntries.filter(e =>
        e.event.includes('FAILURE') || e.event.includes('THREAT'),
      ).length,
      uptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
    };
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
      module: 'SecurityValidator',
      ...metadata,
    };

    if (this.logger) {
      // eslint-disable-next-line security/detect-object-injection
      this.logger[level](logEntry);
      loggers.stopHook.log(JSON.stringify(logEntry));
      // eslint-disable-next-line no-console
      loggers.app.info(JSON.stringify(logEntry));
    }
  }
}

module.exports = SecurityValidator;
