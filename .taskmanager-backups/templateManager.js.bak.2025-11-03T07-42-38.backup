/**
 * Success Criteria Template Manager Module
 *
 * Comprehensive template management system for Success Criteria including:
 * - 25-point standard template system implementation
 * - Project-wide inheritance rules And cascading
 * - Custom criteria support with validation
 * - Template versioning And management
 * - Criteria categorization (Critical/Quality/Integration/Excellence)
 * - Template loading And caching mechanisms
 * - Integration with existing audit criteria from audit-criteria.md
 *
 * @author Template System Agent #2
 * @version 1.0.0
 * @since 2025-09-15
 */

const FS = require('fs').promises;
const PATH = require('path');
const FilePathSecurityValidator = require('../security/FilePathSecurityValidator');

class TemplateManager {
  /**
   * Initialize TemplateManager with comprehensive template support
   * @param {Object} dependencies - Dependency injection object
   * @param {Object} dependencies.taskManager - TaskManager instance
   * @param {Function} dependencies.withTimeout - Timeout wrapper function
   * @param {string} dependencies.projectRoot - Project root directory
   * @param {Object} dependencies.logger - LOGGER instance
   */
  constructor(dependencies) {
    this.taskManager = dependencies.taskManager;
    this.withTimeout = dependencies.withTimeout;
    this.projectRoot = dependencies.projectRoot;
    this.logger = dependencies.logger || console;

    // Cache for templates And configurations
    this.templateCache = new Map();
    this.configCache = new Map();
    this.inheritanceCache = new Map();

    // Template categories for organization
    this.categories = {
      CRITICAL: 'critical',
      QUALITY: 'quality',
      INTEGRATION: 'integration',
      EXCELLENCE: 'excellence',
    };

    // Initialize 25-point standard template
    this.initializeStandardTemplates();

    // Load configuration from success-criteria-config.json
    this.loadConfiguration();
  }

  /**
   * Initialize the 25-point standard template system
   */
  initializeStandardTemplates() {
    // 25-point standard template based on success-criteria.md
    this.standardTemplate = {
      id: '25_point_standard',
      name: '25-Point Standard Success Criteria Template',
      version: '1.0.0',
      description: 'Comprehensive 25-point quality And compliance template',
      categories: {
        [this.categories.CRITICAL]: {
          name: 'Core Quality Gates',
          description: 'Mandatory criteria That must pass (Points 1-10)',
          points: [
            {
              id: 1,
              title: 'Linter Perfection',
              description: 'All linting rules pass with zero violations',
              requirements: [
                'No warnings or errors from static code analysis',
                'Code style consistency maintained',
              ],
              evidence: 'Clean linter output screenshot',
              validation: 'automated',
              mandatory: true,
            },
            {
              id: 2,
              title: 'Build Success',
              description: 'Project builds successfully without errors',
              requirements: [
                'No build warnings or failures',
                'All assets generated correctly',
              ],
              evidence: 'Build log with success confirmation',
              validation: 'automated',
              mandatory: true,
            },
            {
              id: 3,
              title: 'Runtime Success',
              description: 'Application starts without errors',
              requirements: [
                'All services initialize correctly',
                'Core functionality accessible',
              ],
              evidence: 'Startup logs And health check',
              validation: 'automated',
              mandatory: true,
            },
            {
              id: 4,
              title: 'Test Integrity',
              description: 'All existing tests continue to pass',
              requirements: [
                'No test regressions introduced',
                'Coverage maintained or improved',
              ],
              evidence: 'Test results And coverage report',
              validation: 'automated',
              mandatory: true,
            },
            {
              id: 5,
              title: 'Function Documentation',
              description: 'All public functions documented with JSDoc/docstrings',
              requirements: [
                'Parameters And return values described',
                'Usage examples provided where appropriate',
              ],
              evidence: 'Documentation coverage report',
              validation: 'manual',
              mandatory: true,
            },
            {
              id: 6,
              title: 'API Documentation',
              description: 'All public interfaces documented',
              requirements: [
                'Endpoint definitions with examples',
                'Integration guides updated',
              ],
              evidence: 'API documentation completeness',
              validation: 'manual',
              mandatory: true,
            },
            {
              id: 7,
              title: 'Architecture Documentation',
              description: 'System design decisions documented',
              requirements: [
                'Integration patterns explained',
                'Data flow diagrams updated',
              ],
              evidence: 'Architecture documentation review',
              validation: 'manual',
              mandatory: true,
            },
            {
              id: 8,
              title: 'Decision Rationale',
              description: 'Technical decisions explained And justified',
              requirements: [
                'Alternative approaches considered',
                'Trade-offs documented',
              ],
              evidence: 'Decision log entries',
              validation: 'manual',
              mandatory: true,
            },
            {
              id: 9,
              title: 'Error Handling',
              description: 'Comprehensive error handling implemented',
              requirements: [
                'Error messages clear And actionable',
                'Graceful degradation where applicable',
              ],
              evidence: 'Error handling test results',
              validation: 'automated',
              mandatory: true,
            },
            {
              id: 10,
              title: 'Performance Metrics',
              description: 'No performance regressions (< 10% slower)',
              requirements: [
                'Memory usage within bounds',
                'Response times meet requirements',
              ],
              evidence: 'Performance benchmark comparison',
              validation: 'automated',
              mandatory: true,
            },
          ],
        },
        [this.categories.QUALITY]: {
          name: 'Security & Compliance',
          description: 'Security And compliance requirements (Points 11-20)',
          points: [
            {
              id: 11,
              title: 'Security Review',
              description: 'No security vulnerabilities introduced',
              requirements: [
                'Security best practices followed',
                'Threat model considerations addressed',
              ],
              evidence: 'Security scan results',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 12,
              title: 'Architectural Consistency',
              description: 'Follows established project patterns',
              requirements: [
                'Consistent with existing codebase style',
                'Maintains separation of concerns',
              ],
              evidence: 'Architecture review checklist',
              validation: 'manual',
              mandatory: false,
            },
            {
              id: 13,
              title: 'Dependency Validation',
              description: 'Dependencies properly managed',
              requirements: [
                'Version compatibility verified',
                'Licenses compatible with project',
              ],
              evidence: 'Dependency audit report',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 14,
              title: 'Version Compatibility',
              description: 'Compatible with target platform versions',
              requirements: [
                'Backward compatibility maintained',
                'Breaking changes documented',
              ],
              evidence: 'Compatibility test results',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 15,
              title: 'Security Audit',
              description: 'Dependencies scanned for vulnerabilities',
              requirements: [
                'Code scanned for security issues',
                'Authentication/authorization validated',
              ],
              evidence: 'Security audit report',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 16,
              title: 'Cross-Platform',
              description: 'Works across supported platforms',
              requirements: [
                'Platform-specific issues addressed',
                'Environment compatibility verified',
              ],
              evidence: 'Multi-platform test results',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 17,
              title: 'Environment Variables',
              description: 'Required environment variables documented',
              requirements: [
                'Default values provided where appropriate',
                'Configuration validation implemented',
              ],
              evidence: 'Environment configuration guide',
              validation: 'manual',
              mandatory: false,
            },
            {
              id: 18,
              title: 'Configuration',
              description: 'Proper configuration management',
              requirements: [
                'Settings externalized appropriately',
                'Configuration validation implemented',
              ],
              evidence: 'Configuration documentation',
              validation: 'manual',
              mandatory: false,
            },
            {
              id: 19,
              title: 'No Credential Exposure',
              description: 'No secrets or credentials in code',
              requirements: [
                'Secure credential management',
                'No sensitive data in logs',
              ],
              evidence: 'Credential scan results',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 20,
              title: 'Input Validation',
              description: 'All user inputs properly validated',
              requirements: [
                'Sanitization implemented where needed',
                'Boundary conditions handled',
              ],
              evidence: 'Input validation test results',
              validation: 'automated',
              mandatory: false,
            },
          ],
        },
        [this.categories.INTEGRATION]: {
          name: 'Final Validation',
          description: 'Integration And operational criteria (Points 21-25)',
          points: [
            {
              id: 21,
              title: 'Output Encoding',
              description: 'Proper output encoding to prevent injection',
              requirements: [
                'Data sanitization before output',
                'Context-appropriate encoding used',
              ],
              evidence: 'Output validation test results',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 22,
              title: 'Authentication/Authorization',
              description: 'Proper access controls implemented',
              requirements: [
                'User permissions validated',
                'Security boundaries enforced',
              ],
              evidence: 'Auth/authz test results',
              validation: 'automated',
              mandatory: false,
            },
            {
              id: 23,
              title: 'License Compliance',
              description: 'All code compatible with project license',
              requirements: [
                'Third-party licenses compatible',
                'License headers present where required',
              ],
              evidence: 'License compliance report',
              validation: 'manual',
              mandatory: false,
            },
            {
              id: 24,
              title: 'Data Privacy',
              description: 'No unauthorized data collection',
              requirements: [
                'Privacy policies followed',
                'Data minimization principles applied',
              ],
              evidence: 'Privacy compliance review',
              validation: 'manual',
              mandatory: false,
            },
            {
              id: 25,
              title: 'Regulatory Compliance',
              description: 'Applicable regulations considered',
              requirements: [
                'Compliance requirements met',
                'Audit trails maintained where required',
              ],
              evidence: 'Regulatory compliance checklist',
              validation: 'manual',
              mandatory: false,
            },
          ],
        },
      },
    };

    // Cache the standard template
    this.templateCache.set('25_point_standard', this.standardTemplate);
  }

  /**
   * Load configuration from success-criteria-config.json
   */
  async loadConfiguration() {
    try {
      const configPath = PATH.join(this.projectRoot, 'development', 'essentials', 'success-criteria-config.json');
      // Security: Validate config path before reading
      const pathValidator = new FilePathSecurityValidator(this.projectRoot, this.logger);
      const pathValidation = pathValidator.validateReadPath(configPath);
      if (!pathValidation.valid) {
        throw new Error(`Security validation failed: ${pathValidation.error}`);
      }
      // eslint-disable-next-line security/detect-non-literal-fs-filename
      const configData = await FS.readFile(pathValidation.path, 'utf8');
      const config = JSON.parse(configData);

      this.config = config;
      this.configCache.set('main', config);

      this.logger.info('TemplateManager: Configuration loaded successfully');
    } catch {
      this.logger.warn('TemplateManager: Could not load configuration, using defaults', error.message);
      this.config = this.getDefaultConfiguration();
    }
  }

  /**
   * Get default configuration if file is not available
   */
  getDefaultConfiguration() {
    return {
      default_template: '25_point_standard',
      validation_timeout: 300,
      auto_inheritance: true,
      mandatory_validation: true,
      project_wide_criteria: {},
      validation_rules: {},
    };
  }

  /**
   * Load template by ID with caching
   * @param {string} templateId - Template identifier
   * @returns {Promise<Object>} Template object or null
   */
  async loadTemplate(templateId) {
    try {
      // Check cache first
      if (this.templateCache.has(templateId)) {
        return this.templateCache.get(templateId);
      }

      // Handle standard template
      if (templateId === '25_point_standard') {
        return this.standardTemplate;
      }

      // Try to load custom template from file system
      const templatePath = PATH.join(this.projectRoot, 'development', 'templates', `${templateId}.json`);

      try {
        // Security: Validate template path before reading
        const pathValidator = new FilePathSecurityValidator(this.projectRoot, this.logger);
        const pathValidation = pathValidator.validateReadPath(templatePath);
        if (!pathValidation.valid) {
          throw new Error(`Security validation failed: ${pathValidation.error}`);
        }
        // eslint-disable-next-line security/detect-non-literal-fs-filename
        const templateData = await FS.readFile(pathValidation.path, 'utf8');
        const template = JSON.parse(templateData);

        // Validate template structure
        const validationResult = this.validateTemplateStructure(template);
        if (!validationResult.valid) {
          this.logger.error(`TemplateManager: Invalid template structure for ${templateId}:`, validationResult.errors);
          return null;
        }

        // Cache the template
        this.templateCache.set(templateId, template);
        return template;
      } catch {
        this.logger.warn(`TemplateManager: Template file not found for ${templateId}:`, error.message);
        return null;
      }
    } catch {
      this.logger.error(`TemplateManager: Error loading template ${templateId}:`, error.message);
      return null;
    }
  }

  /**
   * Apply inheritance rules to create final criteria set for a task
   * @param {string} taskId - Task identifier
   * @param {Object} taskData - Task data object
   * @param {Array} customCriteria - Custom criteria to add
   * @returns {Promise<Object>} Final criteria set with inheritance applied
   */
  async applyInheritance(taskId, taskData, customCriteria = []) {
    try {
      const cacheKey = `${taskId}_${JSON.stringify(customCriteria)}`;

      // Check inheritance cache
      if (this.inheritanceCache.has(cacheKey)) {
        return this.inheritanceCache.get(cacheKey);
      }

      const RESULT = {
        templateCriteria: [],
        projectWideCriteria: [],
        customCriteria: customCriteria,
        finalCriteria: [],
        inheritance: {
          template: null,
          projectWide: [],
          applied: [],
        },
      };

      // 1. Load template criteria
      const templateId = this.config.default_template || '25_point_standard';
      const template = await this.loadTemplate(templateId);

      if (template) {
        RESULT.templateCriteria = this.extractCriteriaFromTemplate(template);
        RESULT.inheritance.template = templateId;
      }

      // 2. Apply project-wide inheritance rules
      const taskCategory = taskData.category || 'feature';
      const projectWideRules = this.config.validation_rules[`${taskCategory}_tasks`];

      if (projectWideRules && projectWideRules.inherit_from) {
        for (const ruleSetName of projectWideRules.inherit_from) {
          // Security: Use safe getter to prevent object injection
          const ruleSet = this._getProjectWideRule(ruleSetName);
          if (ruleSet && ruleSet.applies_to.includes(taskCategory)) {
            RESULT.projectWideCriteria.push(...ruleSet.criteria);
            RESULT.inheritance.projectWide.push(ruleSetName);
          }
        }
      }

      // 3. Combine all criteria with precedence: Template < Project-wide < Custom
      const allCriteria = [
        ...result.templateCriteria,
        ...result.projectWideCriteria,
        ...result.customCriteria,
      ];

      // Remove duplicates while preserving order
      RESULT.finalCriteria = [...new Set(allCriteria)];
      RESULT.inheritance.applied = RESULT.finalCriteria.length;

      // Cache the result
      this.inheritanceCache.set(cacheKey, result);

      this.logger.info(`TemplateManager: Applied inheritance for task ${taskId}:`, {
        template: RESULT.inheritance.template,
        projectWide: RESULT.inheritance.projectWide.length,
        custom: RESULT.customCriteria.length,
        final: RESULT.finalCriteria.length,
      });

      return result;
    } catch {
      this.logger.error(`TemplateManager: Error applying inheritance for task ${taskId}:`, error.message);
      return {
        templateCriteria: [],
        projectWideCriteria: [],
        customCriteria: customCriteria,
        finalCriteria: customCriteria,
        inheritance: {
          template: null,
          projectWide: [],
          applied: customCriteria.length,
        },
      };
    }
  }

  /**
   * Extract criteria strings from template object
   * @param {Object} template - Template object
   * @returns {Array<string>} Array of criteria strings
   */
  extractCriteriaFromTemplate(template) {
    const criteria = [];

    if (template.categories) {
      Object.values(template.categories).forEach(category => {
        if (category.points) {
          category.points.forEach(point => {
            criteria.push(point.title);
          });
        }
      });
    }

    return criteria;
  }

  /**
   * Get criteria categorization from template
   * @param {string} templateId - Template identifier
   * @returns {Promise<Object>} Categorized criteria object
   */
  async getCriteriaCategories(templateId = '25_point_standard') {
    try {
      const template = await this.loadTemplate(templateId);
      if (!template || !template.categories) {
        return null;
      }

      const categorized = {};

      Object.entries(template.categories).forEach(([categoryKey, category]) => {
        // Security: Validate categoryKey before object assignment
        if (typeof categoryKey === 'string' && categoryKey.length > 0) {
          // eslint-disable-next-line security/detect-object-injection -- categoryKey validated as safe string
          categorized[categoryKey] = {
            name: category.name,
            description: category.description,
            count: category.points.length,
            criteria: category.points.map(point => ({
              id: point.id,
              title: point.title,
              description: point.description,
              mandatory: point.mandatory,
              validation: point.validation,
              evidence: point.evidence,
            })),
          };
        }
      });

      return categorized;
    } catch {
      this.logger.error(`TemplateManager: Error getting categories for template ${templateId}:`, error.message);
      return null;
    }
  }

  /**
   * Validate custom criteria against project standards
   * @param {Array} criteria - Array of criteria to validate
   * @param {Object} options - Validation options
   * @returns {Object} Validation result
   */
  validateCriteria(criteria, _options = {}) {
    const errors = [];
    const warnings = [];

    if (!Array.isArray(criteria)) {
      errors.push('Criteria must be an array');
      return { valid: false, errors, warnings };
    }

    criteria.forEach((criterion, index) => {
      // Basic validation
      if (typeof criterion !== 'string') {
        errors.push(`Criterion at index ${index} must be a string`);
        return;
      }

      if (criterion.trim().length === 0) {
        errors.push(`Criterion at index ${index} cannot be empty`);
        return;
      }

      if (criterion.length > 200) {
        errors.push(`Criterion at index ${index} exceeds maximum length of 200 characters`);
        return;
      }

      // Content validation
      if (!/^[A-Z]/.test(criterion.trim())) {
        warnings.push(`Criterion at index ${index} should start with a capital letter`);
      }

      // Check for common issues
      if (criterion.includes('TODO') || criterion.includes('FIXME')) {
        warnings.push(`Criterion at index ${index} contains TODO/FIXME - ensure it's finalized`);
      }
    });

    // Check for duplicates
    const uniqueCriteria = new Set(criteria);
    if (uniqueCriteria.size !== criteria.length) {
      errors.push('Criteria must be unique (no duplicates found)');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Validate template structure
   * @param {Object} template - Template object to validate
   * @returns {Object} Validation result
   */
  validateTemplateStructure(template) {
    const errors = [];

    if (!template.id) {
      errors.push('Template must have an id field');
    }

    if (!template.name) {
      errors.push('Template must have a name field');
    }

    if (!template.version) {
      errors.push('Template must have a version field');
    }

    if (!template.categories || typeof template.categories !== 'object') {
      errors.push('Template must have a categories object');
    } else {
      Object.entries(template.categories).forEach(([categoryKey, category]) => {
        if (!category.name) {
          errors.push(`Category ${categoryKey} must have a name field`);
        }

        if (!category.points || !Array.isArray(category.points)) {
          errors.push(`Category ${categoryKey} must have a points array`);
        } else {
          category.points.forEach((point, index) => {
            if (!point.id) {
              errors.push(`Point at index ${index} in category ${categoryKey} must have an id`);
            }
            if (!point.title) {
              errors.push(`Point at index ${index} in category ${categoryKey} must have a title`);
            }
            if (!point.description) {
              errors.push(`Point at index ${index} in category ${categoryKey} must have a description`);
            }
          });
        }
      });
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Create a new custom template
   * @param {Object} templateData - Template data
   * @returns {Promise<Object>} Creation result
   */
  async createCustomTemplate(templateData) {
    try {
      // Validate template structure
      const validationResult = this.validateTemplateStructure(templateData);
      if (!validationResult.valid) {
        return {
          success: false,
          error: 'Invalid template structure',
          validationErrors: validationResult.errors,
        };
      }

      // Ensure templates directory exists
      const templatesDir = PATH.join(this.projectRoot, 'development', 'templates');
      // Security: Validate templates directory path
      const pathValidator = new FilePathSecurityValidator(this.projectRoot, this.logger);
      const dirValidation = pathValidator.validateDirectoryPath(templatesDir, 'create', { createParentDirs: true });
      if (!dirValidation.valid) {
        throw new Error(`Security validation failed: ${dirValidation.error}`);
      }
      // eslint-disable-next-line security/detect-non-literal-fs-filename
      await FS.mkdir(dirValidation.path, { recursive: true });

      // Save template to file
      const templatePath = PATH.join(templatesDir, `${templateData.id}.json`);
      // Security: Validate template path before writing
      const fileValidation = pathValidator.validateWritePath(templatePath, { createParentDirs: true });
      if (!fileValidation.valid) {
        throw new Error(`Security validation failed: ${fileValidation.error}`);
      }
      // eslint-disable-next-line security/detect-non-literal-fs-filename
      await FS.writeFile(fileValidation.path, JSON.stringify(templateData, null, 2), 'utf8');

      // Add to cache
      this.templateCache.set(templateData.id, templateData);

      this.logger.info(`TemplateManager: Created custom template ${templateData.id}`);

      return {
        success: true,
        templateId: templateData.id,
        message: 'Custom template created successfully',
      };
    } catch {
      this.logger.error('TemplateManager: Error creating custom template:', error.message);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Update template versioning
   * @param {string} templateId - Template identifier
   * @param {string} newVersion - New version string
   * @returns {Promise<Object>} Update result
   */
  async updateTemplateVersion(templateId, newVersion) {
    try {
      const template = await this.loadTemplate(templateId);
      if (!template) {
        return {
          success: false,
          error: `Template ${templateId} not found`,
        };
      }

      // Update version
      template.version = newVersion;
      template.lastUpdated = new Date().toISOString();

      // Save updated template
      if (templateId !== '25_point_standard') {
        const templatePath = PATH.join(this.projectRoot, 'development', 'templates', `${templateId}.json`);
        // Security: Validate template path before writing
        const pathValidator = new FilePathSecurityValidator(this.projectRoot, this.logger);
        const pathValidation = pathValidator.validateWritePath(templatePath, { createParentDirs: true });
        if (!pathValidation.valid) {
          throw new Error(`Security validation failed: ${pathValidation.error}`);
        }
        // eslint-disable-next-line security/detect-non-literal-fs-filename
        await FS.writeFile(pathValidation.path, JSON.stringify(template, null, 2), 'utf8');
      }

      // Update cache
      this.templateCache.set(templateId, template);

      this.logger.info(`TemplateManager: Updated template ${templateId} to version ${newVersion}`);

      return {
        success: true,
        templateId,
        version: newVersion,
        message: 'Template version updated successfully',
      };
    } catch {
      this.logger.error(`TemplateManager: Error updating template version for ${templateId}:`, error.message);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Clear all caches
   */
  clearCaches() {
    this.templateCache.clear();
    this.configCache.clear();
    this.inheritanceCache.clear();
    this.logger.info('TemplateManager: All caches cleared');
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  getCacheStatistics() {
    return {
      templates: this.templateCache.size,
      configurations: this.configCache.size,
      inheritance: this.inheritanceCache.size,
      totalMemoryFootprint: JSON.stringify({
        templates: [...this.templateCache.values()],
        configs: [...this.configCache.values()],
        inheritance: [...this.inheritanceCache.values()],
      }).length,
    };
  }

  /**
   * Security helper: Safe getter for project-wide rules
   * @param {string} ruleSetName - Rule set name to retrieve
   * @returns {Object|null} Rule set or null if not found
   */
  _getProjectWideRule(ruleSetName) {
    if (!this.config || !this.config.project_wide_criteria) {
      return null;
    }

    // Validate rule set name
    if (typeof ruleSetName !== 'string' || ruleSetName.length === 0) {
      return null;
    }

    // Safe object access using hasOwnProperty
    if (Object.prototype.hasOwnProperty.call(this.config.project_wide_criteria, ruleSetName)) {
      // eslint-disable-next-line security/detect-object-injection -- ruleSetName validated with hasOwnProperty
      return this.config.project_wide_criteria[ruleSetName];
    }

    return null;
  }
}

module.exports = TemplateManager;
