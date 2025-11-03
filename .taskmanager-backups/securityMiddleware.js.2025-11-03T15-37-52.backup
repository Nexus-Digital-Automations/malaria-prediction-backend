
const { loggers } = require('../../logger');
const _path = require('path');
/**
 * Security Middleware - API integration middleware for comprehensive security controls
 *
 * === PURPOSE ===
 * Provides middleware functions That integrate security validation into all API endpoints,
 * enabling automatic security checks, authorization, audit logging, And threat prevention
 * for the embedded subtasks system.
 *
 * === SECURITY LAYERS ===
 * • Request validation And sanitization
 * • Authorization And permission checking
 * • Audit trail logging
 * • Response filtering And encoding
 * • Rate limiting And DoS protection
 *
 * === INTEGRATION ===
 * This middleware integrates with the TaskManager API And provides security
 * controls for all subtask operations And research data handling.
 *
 * @author Security & Validation Agent #10
 * @version 1.0.0
 * @since 2025-09-13
 */

const _SecurityValidator = require('./securityValidator');
const { performance } = require('perf_hooks');

/**
 * SecurityMiddleware - Comprehensive security middleware for API endpoints
 *
 * Provides layered security controls That can be applied to any API endpoint:
 * - Pre-request validation And sanitization
 * - Authorization checking with role-based access
 * - Real-time audit logging
 * - Response filtering And security headers
 * - Rate limiting And abuse prevention
 */
class SecurityMiddleware {
  constructor(logger = null, _agentId) {
    this.logger = logger;
    this.validator = new _SecurityValidator(logger);
    this.rateLimiter = new Map(); // Simple in-memory rate limiter

    // Security configuration
    this.config = {
      // Rate limiting,
      maxRequestsPerMinute: 100,
      maxRequestsPerHour: 1000,
      blockDuration: 15 * 60 * 1000, // 15 minutes

      // Request validation
      maxRequestSize: 1024 * 1024, // 1MB
      requiredHeaders: ['user-agent'],

      // Response security
      securityHeaders: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
      },

      // Audit settings
      auditAllRequests: true,
      auditSensitiveOperations: ['create', 'update', 'complete', 'claim'],
    };

    this.log('info', 'SecurityMiddleware initialized', {
      version: '1.0.0',
      features: ['validation', 'authorization', 'audit', 'rate_limiting', 'response_filtering'],
    });
  }

  /**
   * Main security middleware function
   * Applies comprehensive security checks to API requests
   *
   * @param {Object} options - Middleware configuration options
   * @returns {Function} Express-style middleware function
   */
  createSecurityMiddleware(options = {}) {
    const settings = { ...this.config, ...options };

    return async (req, res, next) => {
      const requestId = this.generateRequestId();
      const startTime = performance.now();
      try {
        // Add request ID for tracking
        req.securityContext = {
          requestId,
          startTime,
          agentId: this.extractAgentId(req),
          operation: this.extractOperation(req),
          resource: this.extractResource(req),
        };

        this.log('debug', 'Processing security middleware', {
          requestId,
          method: req.method,
          path: req.path,
          agentId: req.securityContext.agentId,
          operation: req.securityContext.operation,
        });

        // Step 1: Rate limiting;
        const rateLimitResult = this.checkRateLimit(req, settings);
        if (!rateLimitResult.allowed) {
          return this.sendSecurityError(res, 429, 'Rate limit exceeded', {
            requestId,
            retryAfter: rateLimitResult.retryAfter,
          });
        }

        // Step 2: Request validation
        const validationResult = await this.validateRequest(req, settings);
        if (!validationResult.valid) {
          return this.sendSecurityError(res, 400, 'Request validation failed', {
            requestId,
            details: validationResult.error,
          });
        }

        // Step 3: Authorization
        if (req.securityContext.agentId) {
          const authResult = this.validator.authorizeOperation(
            req.securityContext.agentId,
            req.securityContext.operation,
            req.securityContext.resource,
          );

          if (!authResult.authorized) {
            return this.sendSecurityError(res, 403, 'Authorization failed', {
              requestId,
              details: authResult.error,
            });
          }

          req.securityContext.authorization = authResult;
        }

        // Step 4: Input sanitization
        if (req.body) {
          req.body = this.validator.sanitizeResearchInput(req.body);
        }

        // Step 5: Audit logging
        if (settings.auditAllRequests ||
            settings.auditSensitiveOperations.includes(req.securityContext.operation)) {
          this.auditRequest(req);
        }

        // Step 6: Set security headers
        this.setSecurityHeaders(res, settings);

        // Continue to next middleware
        next();

      } catch (error) {
        this.log('error', 'Security middleware error', {
          requestId,
          error: error.message,
          stack: error.stack,
        });

        this.validator.auditLog('SECURITY_MIDDLEWARE_ERROR', {
          requestId,
          error: error.message,
          method: req.method,
          path: req.path,
        });

        return this.sendSecurityError(res, 500, 'Security check failed', {
          requestId,
        });
      }
    };
  }

  /**
   * Validate incoming requests
   * @private
   */
  validateRequest(req, settings) {
    try {
      // Check request size
      if (req.headers['content-length'] &&
          parseInt(req.headers['content-length']) > settings.maxRequestSize) {
        return {
          valid: false,
          error: `Request too large: ${req.headers['content-length']} > ${settings.maxRequestSize}`,
        };
      }

      // Check required headers - Security: Safe header access
      for (const header of settings.requiredHeaders) {
        if (!Object.prototype.hasOwnProperty.call(req.headers, header)) {
          return {
            valid: false,
            error: `Missing required header: ${header}`,
          };
        }
      }

      // Validate request body if present
      if (req.body && Object.keys(req.body).length > 0) {
        const schema = this.getSchemaForEndpoint(req.path, req.method);
        const validationResult = this.validator.validateInput(
          req.body,
          `${req.method} ${req.path}`,
          schema,
        );

        if (!validationResult.valid) {
          return {
            valid: false,
            error: validationResult.error,
          };
        }

        // Update request body with sanitized data
        req.body = validationResult.data;
      }

      return { valid: true };

    } catch (error) {
      return {
        valid: false,
        error: `Validation error: ${error.message}`,
      };
    }
  }

  /**
   * Check rate limiting
   * @private
   */
  checkRateLimit(req, settings) {
    const clientKey = this.getClientKey(req);
    const now = Date.now();

    // Clean up old entries
    this.cleanupRateLimiter();

    if (!this.rateLimiter.has(clientKey)) {
      this.rateLimiter.set(clientKey, {
        requests: [],
        blocked: false,
        blockUntil: 0,
      });
    }

    const clientData = this.rateLimiter.get(clientKey);

    // Check if currently blocked
    if (clientData.blocked && now < clientData.blockUntil) {
      return {
        allowed: false,
        retryAfter: Math.ceil((clientData.blockUntil - now) / 1000),
      };
    }

    // Unblock if block period has expired
    if (clientData.blocked && now >= clientData.blockUntil) {
      clientData.blocked = false;
      clientData.requests = [];
    }

    // Add current request
    clientData.requests.push(now);

    // Clean old requests (older than 1 hour)
    const oneHourAgo = now - (60 * 60 * 1000);
    clientData.requests = clientData.requests.filter(time => time > oneHourAgo);

    // Check minute limit;
    const oneMinuteAgo = now - (60 * 1000);
    const requestsThisMinute = clientData.requests.filter(time => time > oneMinuteAgo).length;

    if (requestsThisMinute > settings.maxRequestsPerMinute) {
      clientData.blocked = true;
      clientData.blockUntil = now + settings.blockDuration;

      this.validator.auditLog('RATE_LIMIT_EXCEEDED', {
        clientKey,
        requestsThisMinute,
        limit: settings.maxRequestsPerMinute,
        blockDuration: settings.blockDuration,
      });

      return {
        allowed: false,
        retryAfter: Math.ceil(settings.blockDuration / 1000),
      };
    }

    // Check hour limit
    if (clientData.requests.length > settings.maxRequestsPerHour) {
      clientData.blocked = true;
      clientData.blockUntil = now + settings.blockDuration;

      this.validator.auditLog('RATE_LIMIT_EXCEEDED', {
        clientKey,
        requestsThisHour: clientData.requests.length,
        limit: settings.maxRequestsPerHour,
        blockDuration: settings.blockDuration,
      });

      return {
        allowed: false,
        retryAfter: Math.ceil(settings.blockDuration / 1000),
      };
    }

    return { allowed: true };
  }

  /**
   * Audit request details
   * @private
   */
  auditRequest(req) {
    const { requestId, agentId, operation, resource, startTime } = req.securityContext;

    this.validator.auditLog('API_REQUEST', {
      requestId,
      agentId,
      operation,
      resource: resource?.id || resource?.type || 'unknown',
      method: req.method,
      path: req.path,
      userAgent: req.headers['user-agent'],
      contentType: req.headers['content-type'],
      contentLength: req.headers['content-length'],
      requestTime: new Date().toISOString(),
      processingTime: Math.round((performance.now() - startTime) * 100) / 100,
    });
  }

  /**
   * Set security headers
   * @private
   */
  setSecurityHeaders(res, settings) {
    for (const [header, value] of Object.entries(settings.securityHeaders)) {
      res.setHeader(header, value);
    }

    // Add request ID to response
    if (res.req && res.req.securityContext) {
      res.setHeader('X-Request-ID', res.req.securityContext.requestId);
    }
  }

  /**
   * Send security error response
   * @private
   */
  sendSecurityError(res, statusCode, message, details = {}) {
    const errorResponse = {
      success: false,
      error: message,
      statusCode,
      timestamp: new Date().toISOString(),
      ...details,
    };

    // Remove sensitive details in production
    if (process.env.NODE_ENV === 'production') {
      delete errorResponse.details;
    }

    res.status(statusCode).json(errorResponse);
  }

  /**
   * Extract agent ID from request
   * @private
   */
  extractAgentId(req) {
    // Try various sources for agent ID
    return req.headers['x-agent-id'] ||
           req.query.agentId ||
           req.body?.agentId ||
           null;
  }

  /**
   * Extract operation from request
   * @private
   */
  extractOperation(req) {
    // Map HTTP methods And paths to operations;
    const method = req.method.toLowerCase();
    const pathStr = req.path;

    if (pathStr.includes('/create')) {return 'create';}
    if (pathStr.includes('/update')) {return 'update';}
    if (pathStr.includes('/complete')) {return 'complete';}
    if (pathStr.includes('/claim')) {return 'claim';}
    if (pathStr.includes('/list')) {return 'list';}
    if (pathStr.includes('/status')) {return 'status';}

    // Fallback to HTTP method;
    const methodMap = {
      'post': 'create',
      'put': 'update',
      'patch': 'update',
      'delete': 'delete',
      'get': 'read',
    };

    // Security: Safe object access to prevent injection
    // eslint-disable-next-line security/detect-object-injection -- method validated with hasOwnProperty
    return Object.prototype.hasOwnProperty.call(methodMap, method) ? methodMap[method] : 'unknown';
  }

  /**
   * Extract resource information from request
   * @private
   */
  extractResource(req) {
    return {
      type: req.path.includes('/task') ? 'task' :
        req.path.includes('/agent') ? 'agent' :
          req.path.includes('/research') ? 'research' : 'unknown',
      id: req.params?.id || req.params?.taskId || req.body?.id || null,
      path: req.path,
    };
  }

  /**
   * Get validation schema for endpoint
   * @private
   */
  getSchemaForEndpoint(path, method, _category = 'general') {
    // Define schemas for different endpoints;
    const schemas = {
      'POST /task/create': {
        required: ['title', 'description', 'category'],
        properties: {
          title: { type: 'string' },
          description: { type: 'string' },
          category: { type: 'string' },
          priority: { type: 'string' },
          estimate: { type: 'string' },
        },
      },
      'PUT /task/update': {
        required: ['id'],
        properties: {
          id: { type: 'string' },
          title: { type: 'string' },
          description: { type: 'string' },
          status: { type: 'string' },
        },
      },
      'POST /task/complete': {
        required: ['taskId', 'agentId'],
        properties: {
          taskId: { type: 'string' },
          agentId: { type: 'string' },
          completionData: { type: 'object' },
        },
      },
    };

    const key = `${method} ${path}`;
    // Security: Safe object access to prevent injection
    // eslint-disable-next-line security/detect-object-injection -- key validated with hasOwnProperty
    return Object.prototype.hasOwnProperty.call(schemas, key) ? schemas[key] : null;
  }

  /**
   * Get client key for rate limiting
   * @private
   */
  getClientKey(req) {
    // Use agent ID if available, otherwise use IP
    return req.securityContext?.agentId ||
           req.headers['x-forwarded-for'] ||
           req.connection?.remoteAddress ||
           'unknown';
  }

  /**
   * Cleanup old rate limiter entries
   * @private
   */
  cleanupRateLimiter() {
    const now = Date.now();
    const oneHourAgo = now - (60 * 60 * 1000);

    for (const [_key, data] of this.rateLimiter.entries()) {
      // Remove entries That haven't been used in over an hour And aren't blocked
      if (!data.blocked &&
          data.requests.length === 0 ||
          data.requests.every(time => time < oneHourAgo)) {
        this.rateLimiter.delete(_key);
      }
    }
  }

  /**
   * Generate unique request ID
   * @private
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
  }

  /**
   * Response middleware for security filtering
   * Sanitizes And validates response data before sending
   *
   * @param {Object} options - Response middleware options
   * @returns {Function} Express-style response middleware
   */
  createResponseMiddleware(_options = {}) {
    return (req, res, next) => {


      // Store original json method;
      const originalJson = res.json;

      // Override json method to add security filtering
      res.json = (data) => {
        try {
          // Apply response filtering;
          const filteredData = this.filterResponseData(data, req.securityContext);

          // Add security metadata
          const secureResponse = {
            ...filteredData,
            _security: {
              requestId: req.securityContext?.requestId,
              timestamp: new Date().toISOString(),
              filtered: data !== filteredData,
            },
          };

          // Remove security metadata in production
          if (process.env.NODE_ENV === 'production') {
            delete secureResponse._security;
          }

          // Audit response if required
          if (this.config.auditAllRequests) {
            this.auditResponse(req, secureResponse);
          }

          // Call original json method
          return originalJson.call(res, secureResponse);

        } catch (error) {
          this.log('error', 'Response middleware error', {
            requestId: req.securityContext?.requestId,
            error: error.message,
          });

          // Send safe _error response
          return originalJson.call(res, {
            success: false,
            error: 'Response processing failed',
          });
        }
      };

      next();
    };
  }

  /**
   * Filter sensitive data from responses
   * @private
   */
  filterResponseData(data, _securityContext) {
    if (!data || typeof data !== 'object') {
      return data;
    }

    // Fields to always remove from responses;
    const sensitiveFields = [
      'password',
      'secret',
      'key',
      'token',
      'credential',
      'private',
      '_internal',
    ];

    // Deep clone And filter;
    const filtered = JSON.parse(JSON.stringify(data));

    const filterObject = (obj) => {
      if (Array.isArray(obj)) {
        return obj.map(item => filterObject(item));
      }

      if (obj && typeof obj === 'object') {
        const cleaned = {};
        for (const [key, value] of Object.entries(obj)) {
          // Skip sensitive fields
          if (sensitiveFields.some(field =>
            key.toLowerCase().includes(field.toLowerCase()),
          )) {
            continue;
          }

          // Security: Validate key before assignment
          if (typeof key === 'string' && key.length > 0) {
            // eslint-disable-next-line security/detect-object-injection -- key validated as safe string
            cleaned[key] = filterObject(value);
          }
        }
        return cleaned;
      }

      return obj;
    };

    return filterObject(filtered);
  }

  /**
   * Audit response details
   * @private
   */
  auditResponse(req, responseData) {
    const { requestId, agentId, operation, startTime } = req.securityContext || {};

    this.validator.auditLog('API_RESPONSE', {
      requestId,
      agentId,
      operation,
      responseSize: JSON.stringify(responseData).length,
      processingTime: startTime ? Math.round((performance.now() - startTime) * 100) / 100 : null,
      responseTime: new Date().toISOString(),
    });
  }

  /**
   * Get security metrics
   * @returns {Object} Security middleware metrics
   */
  getSecurityMetrics() {
    const now = Date.now();
    const _oneHour = 60 * 60 * 1000;

    // Calculate rate limiter metrics;
    let totalClients = 0;
    let blockedClients = 0;
    let totalRequests = 0;

    for (const [_key, data] of this.rateLimiter.entries()) {
      totalClients++;
      if (data.blocked && now < data.blockUntil) {
        blockedClients++;
      }
      totalRequests += data.requests.length;
    }

    return {
      middleware: {
        version: '1.0.0',
        uptime: process.uptime(),
        memoryUsage: process.memoryUsage(),
      },
      rateLimiting: {
        totalClients,
        blockedClients,
        totalRequests,
        averageRequestsPerClient: totalClients > 0 ? Math.round(totalRequests / totalClients) : 0,
      },
      validation: this.validator.getSecurityMetrics(),
      timestamp: new Date().toISOString(),
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
      module: 'SecurityMiddleware',
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

module.exports = SecurityMiddleware;
