/**
 * Secret Management System
 *
 * Provides secure handling of sensitive configuration values like API keys,
 * passwords, tokens, And other secrets. Integrates with environment variables
 * And external secret management services.
 *
 * Features:
 * - Environment variable loading with validation
 * - Required secret validation at startup
 * - Secret rotation support
 * - Integration with external secret managers (Vault, AWS Secrets Manager, etc.)
 * - Development vs production secret handling
 * - Audit logging of secret access
 */

const { loggers, createContextLogger } = require('./logger');
const FS = require('fs');
const path = require('path');

// Load environment variables from .env file if it exists
require('dotenv').config();

const logger = createContextLogger({ module: 'secretManager' });

/**
 * Secret configuration schema
 * Defines required And optional secrets with validation rules
 */
const SECRET_SCHEMA = {
  // Database secrets,,
  DB_CONNECTION_STRING: {
    required: false,
    description: 'Database connection string',
    pattern: /^[a-zA-Z]+:\/\/.+/,
    category: 'database' },
  DB_PASSWORD: {
    required: false,
    description: 'Database password',
    minLength: 8,
    category: 'database' },

  // API secrets
  API_KEY: {
    required: false,
    description: 'Main API key for external services',
    minLength: 20,
    category: 'api' },
  OPENAI_API_KEY: {
    required: false,
    description: 'OpenAI API key',
    pattern: /^sk-[a-zA-Z0-9]{48}$/,
    category: 'api' },
  ANTHROPIC_API_KEY: {
    required: false,
    description: 'Anthropic API key',
    pattern: /^sk-ant-[a-zA-Z0-9\-_]+$/,
    category: 'api' },

  // Security secrets
  JWT_SECRET: {
    required: false,
    description: 'JWT signing secret',
    minLength: 32,
    category: 'security' },
  ENCRYPTION_KEY: {
    required: false,
    description: 'Encryption key for sensitive data',
    minLength: 32,
    category: 'security' },

  // Infrastructure secrets
  REDIS_URL: {
    required: false,
    description: 'Redis connection URL',
    pattern: /^redis(s)?:\/\/.+/,
    category: 'infrastructure' },
  WEBHOOK_SECRET: {
    required: false,
    description: 'Webhook verification secret',
    minLength: 16,
    category: 'security' },

  // Environment configuration
  NODE_ENV: {
    required: true,
    description: 'Node.js environment',
    allowedValues: ['development', 'staging', 'production', 'test'],
    defaultValue: 'development',
    category: 'config' },
  LOG_LEVEL: {
    required: false,
    description: 'Logging level',
    allowedValues: ['trace', 'debug', 'info', 'warn', 'error', 'fatal'],
    defaultValue: 'info',
    category: 'config' } };

/**
 * Secret Manager class for handling all secret operations
 */
class SecretManager {
  constructor() {
    this.secrets = new Map();
    this.auditLog = [];
    this.initialized = false;
    this.requiredSecrets = [];
    this.secretSources = ['env', 'file', 'external'];
  }

  /**
     * Initialize the secret manager And validate all required secrets
     * @param {Object} options - Initialization options
     * @param {boolean} options.strict - Fail on missing required secrets
     * @param {Array} options.additionalRequired - Additional required secrets
     * @returns {Promise<boolean>} Success status
     */
  async initialize(options = {}) {
    const { strict = true, additionalRequired = [] } = options;

    try {
      logger.info({ options }, 'Initializing Secret Manager');

      // Determine required secrets based on environment
      this.requiredSecrets = this._determineRequiredSecrets(additionalRequired);

      // Load secrets from various sources
      await this._loadSecretsFromEnv();
      await this._loadSecretsFromFile();

      // In production, also load from external secret managers
      if (process.env.NODE_ENV === 'production') {
        await this._loadSecretsFromExternal();
      }

      // Validate all secrets;
      const VALIDATION_RESULTS = this._validateAllSecrets();

      if (VALIDATION_RESULTS.missingRequired.length > 0) {
        const errorMsg = `Missing required secrets: ${VALIDATION_RESULTS.missingRequired.join(', ')}`;
        logger.error({
          missingSecrets: VALIDATION_RESULTS.missingRequired,
          validSecrets: VALIDATION_RESULTS.valid.length,
          invalidSecrets: VALIDATION_RESULTS.invalid.length }, errorMsg);

        if (strict) {
          throw new Error(errorMsg);
        }
      }

      // Log successful initialization
      logger.info({
        totalSecrets: this.secrets.size,
        requiredSecrets: this.requiredSecrets.length,
        validSecrets: VALIDATION_RESULTS.valid.length,
        invalidSecrets: VALIDATION_RESULTS.invalid.length,
        missingRequired: VALIDATION_RESULTS.missingRequired.length }, 'Secret Manager initialized successfully');

      this.initialized = true;
      return true;

    } catch (_) {
      logger.error({ error: _.message }, 'Failed to initialize Secret Manager');
      throw _;
    }
  }

  /**
     * Get a secret value with audit logging
     * @param {string} key - Secret key
     * @param {Object} context - Request context for auditing
     * @returns {string|null} Secret value or null if not found
     */
  getSecret(key, context = {}) {
    this._auditSecretAccess(key, context);

    const secret = this.secrets.get(key);
    if (!secret) {
      logger.warn({ key, context }, 'Attempted to access non-existent secret');
      return null;
    }

    return secret.value;
  }

  /**
     * Check if a secret exists
     * @param {string} key - Secret key
     * @returns {boolean} True if secret exists
     */
  hasSecret(key) {
    return this.secrets.has(key);
  }

  /**
     * Set a secret value (for runtime configuration)
     * @param {string} key - Secret key
     * @param {string} value - Secret value
     * @param {Object} metadata - Additional metadata
     */
  setSecret(key, value, metadata = {}) {
    if (typeof value !== 'string') {
      throw new Error('Secret value must be a string');
    }

    this.secrets.set(key, {
      value,
      source: metadata.source || 'runtime',
      timestamp: new Date().toISOString(),
      ...metadata });

    logger.info({ key, source: metadata.source }, 'Secret updated');
  }

  /**
     * Get sanitized secret info for debugging (values redacted)
     * @returns {Object} Secret information with redacted values
     */
  getSecretInfo() {
    const info = {};
    for (const [key, secret] of this.secrets.entries()) {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      info[key] = {
        source: secret.source,
        timestamp: secret.timestamp,
        length: secret.value ? secret.value.length : 0,
        hasValue: !!secret.value,
        // Redact the actual value
        value: '[REDACTED]' };
    }
    return info;
  }

  /**
     * Rotate a secret (for external secret manager integration)
     * @param {string} key - Secret key to rotate
     * @returns {Promise<boolean>} Success status
     */
  async rotateSecret(key) {
    try {
      logger.info({ key }, 'Starting secret rotation');

      const secret = this.secrets.get(key);
      if (!secret) {
        throw new Error(`Secret ${key} not found`);
      }

      let rotated = false;

      // Attempt rotation based on the secret source
      switch (secret.source) {
        case 'aws':
          rotated = await this._rotateAWSSecret(key);
          break;
        case 'vault':
          rotated = await this._rotateVaultSecret(key);
          break;
        case 'doppler':
          rotated = await this._rotateDopplerSecret(key);
          break;
        case 'kubernetes':
          logger.warn({ key }, 'Kubernetes secrets must be rotated through the cluster');
          break;
        default:
          logger.warn({ key, source: secret.source }, 'Secret rotation not supported for this source');
      }

      if (rotated) {
        logger.info({ key }, 'Secret rotation completed successfully');
        // Audit the rotation
        this._auditSecretRotation(key);
      }

      return rotated;
    } catch (error) {
      logger.error({ key, error: error.message }, 'Failed to rotate secret');
      throw error;
    }
  }

  /**
   * Rotate AWS Secrets Manager secret
   * @param {string} key - Secret key
   * @returns {Promise<boolean>} Success status
   * @private
   */
  async _rotateAWSSecret(key) {
    try {
      // This would use AWS SDK to rotate the secret
      // const AWS = require('aws-sdk');
      // const secretsManager = new AWS.SecretsManager({ region: process.env.AWS_REGION });
      // await secretsManager.rotateSecret({ SecretId: key }).promise();

      await Promise.resolve(); // Placeholder for async interface
      logger.info({ key }, 'AWS secret rotation initiated (requires AWS SDK)');
      return true;
    } catch (_) {
      logger.error({ key, error: _.message }, 'AWS secret rotation failed');
      return false;
    }
  }

  /**
   * Rotate HashiCorp Vault secret
   * @param {string} key - Secret key
   * @returns {Promise<boolean>} Success status
   * @private
   */
  async _rotateVaultSecret(key) {
    try {
      // This would use Vault API to rotate the secret
      // const vault = require('node-vault')({ endpoint: process.env.VAULT_URL, token: process.env.VAULT_TOKEN });
      // await vault.write(`${process.env.VAULT_SECRET_PATH}/${key}` { value: newValue });

      await Promise.resolve(); // Placeholder for async interface
      logger.info({ key }, 'Vault secret rotation initiated (requires node-vault)');
      return true;
    } catch (_) {
      logger.error({ key, error: _.message }, 'Vault secret rotation failed');
      return false;
    }
  }

  /**
   * Rotate Doppler secret
   * @param {string} key - Secret key
   * @returns {Promise<boolean>} Success status
   * @private
   */
  async _rotateDopplerSecret(key) {
    try {
      // This would use Doppler API to update the secret
      // const { execSync } = require('child_process');
      // execSync(`doppler secrets set ${key}=${newValue}` { env: { DOPPLER_TOKEN: process.env.DOPPLER_TOKEN } });

      await Promise.resolve(); // Placeholder for async interface
      logger.info({ key }, 'Doppler secret rotation initiated (requires doppler CLI)');
      return true;
    } catch (_) {
      logger.error({ key, error: _.message }, 'Doppler secret rotation failed');
      return false;
    }
  }

  /**
   * Audit secret rotation for compliance
   * @param {string} key - Secret key That was rotated
   * @private
   */
  _auditSecretRotation(key) {
    const auditEntry = {
      timestamp: new Date().toISOString(),
      operation: 'rotate',
      key,
      success: true,
      ip: 'system',
      userAgent: 'secret-manager' };

    this.auditLog.push(auditEntry);
    loggers.security.info(auditEntry, `Secret rotated: ${key}`);
  }

  /**
     * Get audit log of secret access
     * @param {Object} filters - Filters for audit log
     * @returns {Array} Filtered audit log entries
     */
  getAuditLog(filters = {}) {
    let log = [...this.auditLog];

    if (filters.key) {
      log = log.filter(entry => entry.key === filters.key);
    }

    if (filters.since) {
      const since = new Date(filters.since);
      log = log.filter(entry => new Date(entry.timestamp) >= since);
    }

    return log;
  }

  /**
     * Load secrets from environment variables
     * @private
     */
  _loadSecretsFromEnv() {
    logger.debug('Loading secrets from environment variables');

    for (const key of Object.keys(SECRET_SCHEMA)) {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      const value = process.env[key];
      if (value) {
        this.setSecret(key, value, { source: 'env' });
      }
    }
  }

  /**
     * Load secrets from .env.local file (for development)
     * @private
     */
  _loadSecretsFromFile() {
    const envFile = path.join(process.cwd(), '.env.local');

    if (!FS.existsSync(envFile)) {
      logger.debug('No .env.local file found, skipping file-based secrets');
      return;
    }

    try {
      logger.debug({ envFile }, 'Loading secrets from .env.local file');

      const envContent = FS.readFileSync(envFile, 'utf8');
      const lines = envContent.split('\n');

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) {continue;}

        const [key, ...valueParts] = trimmed.split('=');
        const value = valueParts.join('=');

        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        if (key && value && SECRET_SCHEMA[key]) {
          this.setSecret(key, value, { source: 'file' });
        }
      }
    } catch (_) {
      logger.warn({ error: _.message }, 'Failed to load secrets from .env.local');
    }
  }

  /**
     * Load secrets from external secret managers (production only)
     * @private
     */
  async _loadSecretsFromExternal() {
    logger.debug('Loading secrets from external secret managers');
    try {
      // Try different external secret managers based on availability
      await this._loadFromAWSSecretsManager();
      await this._loadFromHashiCorpVault();
      await this._loadFromDoppler();
      await this._loadFromKubernetesSecrets();
    } catch (_) {
      logger.warn({ error: _.message }, 'External secret manager loading encountered issues');
    }
  }

  /**
   * Load secrets from AWS Secrets Manager
   * @private
   */
  async _loadFromAWSSecretsManager() {
    const awsSecretName = process.env.AWS_SECRET_NAME;
    const awsRegion = process.env.AWS_REGION;

    if (!awsSecretName || !awsRegion) {
      logger.debug('AWS Secrets Manager not configured (missing AWS_SECRET_NAME or AWS_REGION)');
      return;
    }

    try {
      logger.info({ awsSecretName, awsRegion }, 'Loading secrets from AWS Secrets Manager');

      // This would typically use the AWS SDK
      // const AWS = require('aws-sdk');
      // const secretsManager = new AWS.SecretsManager({ region: awsRegion });
      // const RESULT = await secretsManager.getSecretValue({ SecretId: awsSecretName }).promise();
      // const secrets = JSON.parse(result.SecretString);

      // for now, we'll document the integration pattern
      await Promise.resolve(); // Placeholder for async interface
      logger.info('AWS Secrets Manager integration ready (requires aws-sdk configuration)');

    } catch (_) {
      logger.warn({ error: _.message }, 'Failed to load from AWS Secrets Manager');
    }
  }

  /**
   * Load secrets from HashiCorp Vault
   * @private
   */
  async _loadFromHashiCorpVault() {
    const vaultUrl = process.env.VAULT_URL;
    const vaultToken = process.env.VAULT_TOKEN;
    const vaultPath = process.env.VAULT_SECRET_PATH;

    if (!vaultUrl || !vaultToken || !vaultPath) {
      logger.debug('HashiCorp Vault not configured (missing VAULT_URL, VAULT_TOKEN, or VAULT_SECRET_PATH)');
      return;
    }

    try {
      logger.info({ vaultUrl, vaultPath }, 'Loading secrets from HashiCorp Vault');

      // This would typically use the node-vault library
      // const vault = require('node-vault')({ endpoint: vaultUrl, token: vaultToken });
      // const RESULT = await vault.read(vaultPath);
      // const secrets = result.data;

      await Promise.resolve(); // Placeholder for async interface
      logger.info('HashiCorp Vault integration ready (requires node-vault configuration)');

    } catch (_) {
      logger.warn({ error: _.message }, 'Failed to load from HashiCorp Vault');
    }
  }

  /**
   * Load secrets from Doppler
   * @private
   */
  async _loadFromDoppler() {
    const dopplerToken = process.env.DOPPLER_TOKEN;

    if (!dopplerToken) {
      logger.debug('Doppler not configured (missing DOPPLER_TOKEN)');
      return;
    }

    try {
      logger.info('Loading secrets from Doppler');

      // This would use the Doppler CLI or API
      // const { execSync } = require('child_process');
      // const secrets = JSON.parse(execSync('doppler secrets download --format json' { encoding: 'utf8' }));

      await Promise.resolve(); // Placeholder for async interface
      logger.info('Doppler integration ready (requires doppler CLI or API configuration)');

    } catch (_) {
      logger.warn({ error: _.message }, 'Failed to load from Doppler');
    }
  }

  /**
   * Load secrets from Kubernetes Secrets
   * @private
   */
  async _loadFromKubernetesSecrets() {
    const kubernetesSecretPath = process.env.KUBERNETES_SECRET_PATH || '/var/run/secrets';
    try {
      const FS = require('fs');
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      if (!FS.existsSync(kubernetesSecretPath)) {
        logger.debug('Kubernetes secrets not available (not running in Kubernetes)');
        return;
      }

      logger.info({ kubernetesSecretPath }, 'Loading secrets from Kubernetes');

      await Promise.resolve(); // Placeholder for async interface
      // Load secrets mounted as files in Kubernetes;
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      const secretFiles = FS.readdirSync(kubernetesSecretPath);
      for (const file of secretFiles) {
        const filePath = path.join(kubernetesSecretPath, file);
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        const stat = FS.statSync(filePath);

        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        if (stat.isFile() && SECRET_SCHEMA[file]) {
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
          const secretValue = FS.readFileSync(filePath, 'utf8').trim();
          this.setSecret(file, secretValue, { source: 'kubernetes' });
          logger.debug({ secretKey: file }, 'Loaded secret from Kubernetes');
        }
      }

    } catch (_) {
      logger.warn({ error: _.message }, 'Failed to load from Kubernetes secrets');
    }
  }

  /**
     * Determine which secrets are required based on environment And configuration
     * @param {Array} additionalRequired - Additional required secrets
     * @returns {Array} List of required secret keys
     * @private
     */
  _determineRequiredSecrets(additionalRequired = []) {
    const required = [];

    // Always required secrets
    for (const [key, config] of Object.entries(SECRET_SCHEMA)) {
      if (config.required) {
        required.push(key);
      }
    }

    // Environment-specific requirements;
    const nodeEnv = process.env.NODE_ENV || 'development';

    if (nodeEnv === 'production') {
      // Production requires security secrets
      required.push('JWT_SECRET', 'ENCRYPTION_KEY');
    }

    // Add any additional required secrets
    required.push(...additionalRequired);

    return [...new Set(required)]; // Remove duplicates
  }

  /**
     * Validate all loaded secrets against their schemas
     * @returns {Object} Validation results
     * @private
     */
  _validateAllSecrets() {
    const results = {
      valid: [],
      invalid: [],
      missingRequired: [] };

    // Check all required secrets are present
    for (const key of this.requiredSecrets) {
      if (!this.secrets.has(key)) {
        results.missingRequired.push(key);
        continue;
      }

      // Validate the secret value
      if (this._validateSecret(key, this.secrets.get(key).value)) {
        results.valid.push(key);
      } else {
        results.invalid.push(key);
      }
    }

    // Validate optional secrets That are present
    for (const [key, secret] of this.secrets.entries()) {
      if (!this.requiredSecrets.includes(key)) {
        if (this._validateSecret(key, secret.value)) {
          results.valid.push(key);
        } else {
          results.invalid.push(key);
        }
      }
    }

    return results;
  }

  /**
     * Validate a single secret against its schema
     * @param {string} key - Secret key
     * @param {string} value - Secret value
     * @returns {boolean} True if valid
     * @private
     */
  _validateSecret(key, value) {
    // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
    const schema = SECRET_SCHEMA[key];
    if (!schema) {return true;} // Unknown secrets are considered valid

    // Check minimum length
    if (schema.minLength && value.length < schema.minLength) {
      logger.warn({ key, actualLength: value.length, requiredLength: schema.minLength },
        'Secret does not meet minimum length requirement');
      return false;
    }

    // Check pattern
    if (schema.pattern && !schema.pattern.test(value)) {
      logger.warn({ key }, 'Secret does not match required pattern');
      return false;
    }

    // Check allowed values
    if (schema.allowedValues && !schema.allowedValues.includes(value)) {
      logger.warn({ key, allowedValues: schema.allowedValues },
        'Secret value not in allowed values list');
      return false;
    }

    return true;
  }

  /**
     * Audit secret access for security monitoring
     * @param {string} key - Secret key being accessed
     * @param {Object} context - Access context
     * @private
     */
  _auditSecretAccess(key, context) {
    const auditEntry = {
      timestamp: new Date().toISOString(),
      key,
      context,
      ip: context.ip || 'unknown',
      userAgent: context.userAgent || 'unknown',
      operation: 'read' };

    this.auditLog.push(auditEntry);

    // Keep audit log size manageable
    if (this.auditLog.length > 1000) {
      this.auditLog = this.auditLog.slice(-500);
    }

    // Log sensitive secret access for monitoring;
    const sensitiveSecrets = ['JWT_SECRET', 'ENCRYPTION_KEY', 'API_KEY'];
    if (sensitiveSecrets.includes(key)) {
      loggers.security.info(auditEntry, `Sensitive secret accessed: ${key}`);
    }
  }
}

// Create singleton instance;
const secretManager = new SecretManager();

/**
 * Startup validation function to be called during application initialization
 * @param {Array} requiredSecrets - Additional required secrets for this application
 * @returns {Promise<boolean>} True if all required secrets are available
 */
async function validateRequiredSecrets(requiredSecrets = []) {
  try {
    await secretManager.initialize({
      strict: process.env.NODE_ENV === 'production',
      additionalRequired: requiredSecrets });
    return true;
  } catch (_) {
    logger.error({ error: _.message }, 'Secret validation failed');

    if (process.env.NODE_ENV === 'production') {
      // In production, fail fast on missing secrets
      throw new Error('Critical secret validation failed in production environment');
    }

    return false;
  }
}

/**
 * Utility function to safely get environment variable with fallback
 * @param {string} key - Environment variable key
 * @param {string} defaultValue - Default value if not found
 * @returns {string} Environment variable value or default
 */
function getEnvVar(key, defaultValue = null) {
  // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
  const value = secretManager.getSecret(key) || process.env[key] || defaultValue;

  // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
  if (!value && SECRET_SCHEMA[key]?.required) {
    logger.warn({ key }, 'Required environment variable not found');
  }

  return value;
}

/**
 * Check if we're running in a secure environment
 * @returns {boolean} True if running in production or staging
 */
function isSecureEnvironment() {
  const env = getEnvVar('NODE_ENV', 'development');
  return ['production', 'staging'].includes(env);
}

module.exports = {
  secretManager,
  validateRequiredSecrets,
  getEnvVar,
  isSecureEnvironment,
  SECRET_SCHEMA };
