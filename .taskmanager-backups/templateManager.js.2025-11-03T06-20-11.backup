/**
 * Criteria Template Manager - Enhanced Template Handling
 *
 * Manages success criteria templates including the complete 25-point standard template,
 * custom templates, And template inheritance. Provides comprehensive template management
 * with caching, validation, And configuration support.
 *
 * Features:
 * - Complete 25-point standard template with detailed criteria
 * - Custom template creation And management
 * - Template inheritance And composition
 * - Evidence requirements And validation types
 * - Caching for performance optimization
 * - Configuration-driven template selection
 *
 * @class CriteriaTemplateManager
 * @author API Infrastructure Agent #1
 * @version 3.0.0
 * @since 2025-09-15
 */

const FS = require('fs').promises;
const path = require('path');
const _LOGGER = require('../../logger');
const FilePathSecurityValidator = require('../security/FilePathSecurityValidator');

class CriteriaTemplateManager {
  /**
   * Initialize CriteriaTemplateManager
   * @param {Object} options - Configuration options
   * @param {boolean} options.enableCaching - Enable template caching
   * @param {string} options.templatePath - Path to success-criteria.md
   * @param {string} options.configPath - Path to success-criteria-config.json
   */
  constructor(options = {}) {
    this.enableCaching = options.enableCaching !== false;
    this.templatePath = options.templatePath || '/Users/jeremyparker/infinite-continue-stop-hook/development/essentials/success-criteria.md';
    this.configPath = options.configPath || '/Users/jeremyparker/infinite-continue-stop-hook/development/essentials/success-criteria-config.json';

    // Template cache
    this.templateCache = new Map();
    this.configCache = new Map();

    // Initialize standard templates
    this.initializeStandardTemplates();

    // Load configuration
    this.loadConfiguration().catch(_err => {
      // Silently handle configuration loading errors - will use defaults
    });
  }

  /**
   * Initialize the complete 25-point standard template system
   */
  initializeStandardTemplates(_category = 'general') {
    const standardTemplate = {
      id: '25_point_standard',
      name: 'Industry Standard 25-Point Quality Criteria',
      version: '3.0.0',
      description: 'Comprehensive quality criteria Covering all aspects of professional software development',
      created: '2025-09-15T00:00:00Z',
      lastUpdated: '2025-09-15T00:00:00Z',
      categories: {
        critical: {
          name: 'Core Quality Gates',
          description: 'Mandatory criteria That must pass (Points 1-10)',
          priority: 1,
          mandatory: true,
          points: [{
            id: 1,
            title: 'Linter Perfection',
            description: 'All linting rules pass with zero violations',
            requirements: [
              'No warnings or errors from static code analysis',
              'Code style consistency maintained',
              'All formatting rules followed',
            ],
            evidence: 'Clean linter output screenshot',
            validation: 'automated',
            mandatory: true,
            category: 'code_quality',
            commands: ['npm run lint', 'eslint .', 'ruff check .'],
          }, {
            id: 2,
            title: 'Build Success',
            description: 'Project builds successfully without errors',
            requirements: [
              'No build warnings or failures',
              'All assets generated correctly',
              'Build reproducible across environments',
            ],
            evidence: 'Build log with success confirmation',
            validation: 'automated',
            mandatory: true,
            category: 'build',
            commands: ['npm run build', 'yarn build', 'make build'],
          }, {
            id: 3,
            title: 'Runtime Success',
            description: 'Application starts without errors',
            requirements: [
              'All services initialize correctly',
              'Core functionality accessible',
              'Health checks pass',
            ],
            evidence: 'Startup logs And health check',
            validation: 'automated',
            mandatory: true,
            category: 'runtime',
            commands: ['npm start', 'yarn start', 'node server.js'],
          }, {
            id: 4,
            title: 'Test Integrity',
            description: 'All existing tests continue to pass',
            requirements: [
              'No test regressions introduced',
              'Coverage maintained or improved',
              'Test suite completes without errors',
            ],
            evidence: 'Test results And coverage report',
            validation: 'automated',
            mandatory: true,
            category: 'testing',
            commands: ['npm test', 'yarn test', 'pytest', 'go test'],
          }, {
            id: 5,
            title: 'Function Documentation',
            description: 'All public functions documented with JSDoc/docstrings',
            requirements: [
              'Parameters And return values described',
              'Usage examples provided where appropriate',
              'Documentation follows project standards',
            ],
            evidence: 'Documentation coverage report',
            validation: 'manual',
            mandatory: true,
            category: 'documentation',
          }, {
            id: 6,
            title: 'API Documentation',
            description: 'All public interfaces documented',
            requirements: [
              'Endpoint definitions with examples',
              'Integration guides updated',
              'API changes documented',
            ],
            evidence: 'API documentation completeness',
            validation: 'manual',
            mandatory: true,
            category: 'documentation',
          }, {
            id: 7,
            title: 'Architecture Documentation',
            description: 'System design decisions documented',
            requirements: [
              'Integration patterns explained',
              'Data flow diagrams updated',
              'Component relationships documented',
            ],
            evidence: 'Architecture documentation review',
            validation: 'manual',
            mandatory: true,
            category: 'architecture',
          }, {
            id: 8,
            title: 'Decision Rationale',
            description: 'Technical decisions explained And justified',
            requirements: [
              'Alternative approaches considered',
              'Trade-offs documented',
              'Decision criteria explained',
            ],
            evidence: 'Decision log entries',
            validation: 'manual',
            mandatory: true,
            category: 'documentation',
          }, {
            id: 9,
            title: 'Error Handling',
            description: 'Comprehensive error handling implemented',
            requirements: [
              'Error messages clear And actionable',
              'Graceful degradation where applicable',
              'Error logging implemented',
            ],
            evidence: 'Error handling test results',
            validation: 'automated',
            mandatory: true,
            category: 'reliability',
          }, {
            id: 10,
            title: 'Performance Metrics',
            description: 'No performance regressions (< 10% slower)',
            requirements: [
              'Memory usage within bounds',
              'Response times meet requirements',
              'Resource utilization optimized',
            ],
            evidence: 'Performance benchmark comparison',
            validation: 'automated',
            mandatory: true,
            category: 'performance',
          },
          ],
        },
        security: {
          name: 'Security & Compliance',
          description: 'Security And compliance requirements (Points 11-20)',
          priority: 2,
          mandatory: false,
          points: [
            {
              id: 11,
              title: 'Security Review',
              description: 'No security vulnerabilities introduced',
              requirements: [
                'Security best practices followed',
                'Threat model considerations addressed',
                'Security scanning completed',
              ],
              evidence: 'Security scan results',
              validation: 'automated',
              mandatory: false,
              category: 'security',
              commands: ['npm audit', 'snyk test', 'safety check'],
            }, {
              id: 12,
              title: 'Architectural Consistency',
              description: 'Follows established project patterns',
              requirements: [
                'Consistent with existing codebase style',
                'Maintains separation of concerns',
                'Follows design principles',
              ],
              evidence: 'Architecture review checklist',
              validation: 'manual',
              mandatory: false,
              category: 'architecture',
            }, {
              id: 13,
              title: 'Dependency Validation',
              description: 'Dependencies properly managed',
              requirements: [
                'Version compatibility verified',
                'Licenses compatible with project',
                'No unnecessary dependencies',
              ],
              evidence: 'Dependency audit report',
              validation: 'automated',
              mandatory: false,
              category: 'dependencies',
            }, {
              id: 14,
              title: 'Version Compatibility',
              description: 'Compatible with target platform versions',
              requirements: [
                'Backward compatibility maintained',
                'Breaking changes documented',
                'Migration path provided',
              ],
              evidence: 'Compatibility test results',
              validation: 'automated',
              mandatory: false,
              category: 'compatibility',
            }, {
              id: 15,
              title: 'Security Audit',
              description: 'Dependencies scanned for vulnerabilities',
              requirements: [
                'Code scanned for security issues',
                'Authentication/authorization validated',
                'Sensitive data protection verified',
              ],
              evidence: 'Security audit report',
              validation: 'automated',
              mandatory: false,
              category: 'security',
            }, {
              id: 16,
              title: 'Cross-Platform',
              description: 'Works across supported platforms',
              requirements: [
                'Platform-specific issues addressed',
                'Environment compatibility verified',
                'Cross-platform testing completed',
              ],
              evidence: 'Multi-platform test results',
              validation: 'automated',
              mandatory: false,
              category: 'compatibility',
            }, {
              id: 17,
              title: 'Environment Variables',
              description: 'Required environment variables documented',
              requirements: [
                'Default values provided where appropriate',
                'Configuration validation implemented',
                'Environment setup documented',
              ],
              evidence: 'Environment configuration guide',
              validation: 'manual',
              mandatory: false,
              category: 'configuration',
            }, {
              id: 18,
              title: 'Configuration',
              description: 'Proper configuration management',
              requirements: [
                'Settings externalized appropriately',
                'Configuration validation implemented',
                'Config changes documented',
              ],
              evidence: 'Configuration documentation',
              validation: 'manual',
              mandatory: false,
              category: 'configuration',
            }, {
              id: 19,
              title: 'No Credential Exposure',
              description: 'No secrets or credentials in code',
              requirements: [
                'Secure credential management',
                'No sensitive data in logs',
                'Secrets properly encrypted',
              ],
              evidence: 'Credential scan results',
              validation: 'automated',
              mandatory: false,
              category: 'security',
            }, {
              id: 20,
              title: 'Input Validation',
              description: 'All user inputs properly validated',
              requirements: [
                'Sanitization implemented where needed',
                'Boundary conditions handled',
                'Input validation comprehensive',
              ],
              evidence: 'Input validation test results',
              validation: 'automated',
              mandatory: false,
              category: 'security',
            },
          ],
        },
        excellence: {
          name: 'Final Validation',
          description: 'Excellence And operational criteria (Points 21-25)',
          priority: 3,
          mandatory: false,
          points: [
            {
              id: 21,
              title: 'Output Encoding',
              description: 'Proper output encoding to prevent injection',
              requirements: [
                'Data sanitization before output',
                'Context-appropriate encoding used',
                'Output validation implemented',
              ],
              evidence: 'Output validation test results',
              validation: 'automated',
              mandatory: false,
              category: 'security',
            }, {
              id: 22,
              title: 'Authentication/Authorization',
              description: 'Proper access controls implemented',
              requirements: [
                'User permissions validated',
                'Security boundaries enforced',
                'Access controls tested',
              ],
              evidence: 'Auth/authz test results',
              validation: 'automated',
              mandatory: false,
              category: 'security',
            }, {
              id: 23,
              title: 'License Compliance',
              description: 'All code compatible with project license',
              requirements: [
                'Third-party licenses compatible',
                'License headers present where required',
                'License compliance verified',
              ],
              evidence: 'License compliance report',
              validation: 'manual',
              mandatory: false,
              category: 'compliance',
            }, {
              id: 24,
              title: 'Data Privacy',
              description: 'No unauthorized data collection',
              requirements: [
                'Privacy policies followed',
                'Data minimization principles applied',
                'Privacy compliance verified',
              ],
              evidence: 'Privacy compliance review',
              validation: 'manual',
              mandatory: false,
              category: 'compliance',
            }, {
              id: 25,
              title: 'Regulatory Compliance',
              description: 'Applicable regulations considered',
              requirements: [
                'Compliance requirements met',
                'Audit trails maintained where required',
                'Regulatory requirements verified',
              ],
              evidence: 'Regulatory compliance checklist',
              validation: 'manual',
              mandatory: false,
              category: 'compliance',
            },
          ],
        },
      },
      totalPoints: 25,
      mandatoryPoints: 10,
      optionalPoints: 15,
      estimatedValidationTime: '30-45 minutes',
      usage: {
        defaultFor: ['feature', 'major_feature'],
        recommendedFor: ['enterprise', 'production', 'security_critical'],
        notRecommendedFor: ['hotfix', 'documentation_only'],
      },
    };

    // Cache the standard template
    if (this.enableCaching) {
      this.templateCache.set('25_point_standard', standardTemplate);
    }

    // Initialize legacy templates for backward compatibility
    this.initializeLegacyTemplates();
  }

  /**
   * Initialize legacy templates for backward compatibility
   */
  initializeLegacyTemplates() {
    const legacyTemplates = {
      basic: {
        id: 'basic',
        name: 'Basic Quality Template',
        criteria: ['Linter Perfection', 'Build Success', 'Runtime Success', 'Test Integrity'],
      },
      comprehensive: {
        id: 'comprehensive',
        name: 'Comprehensive Quality Template',
        criteria: [
          'Linter Perfection', 'Build Success', 'Runtime Success', 'Test Integrity',
          'Function Documentation', 'API Documentation', 'Error Handling', 'Performance Metrics',
        ],
      },
      enterprise: {
        id: 'enterprise',
        name: 'Enterprise Quality Template',
        criteria: this.extractCriteriaFromTemplate(this.templateCache.get('25_point_standard')),
      },
    };

    if (this.enableCaching) {
      Object.values(legacyTemplates).forEach(template => {
        this.templateCache.set(template.id, template);
      });
    }
  }

  /**
   * Load configuration from success-criteria-config.json
   */
  async loadConfiguration() {
    try {
      // Security: Validate config path before reading;
      const pathValidator = new FilePathSecurityValidator(this.projectRoot, this.logger);
      const pathValidation = pathValidator.validateReadPath(this.configPath);
      if (!pathValidation.valid) {
        throw new Error(`Security validation failed: ${pathValidation.error}`);
      }
      // eslint-disable-next-line security/detect-non-literal-fs-filename
      const configData = await FS.readFile(pathValidation.path, 'utf8');
      const config = JSON.parse(configData);

      if (this.enableCaching) {
        this.configCache.set('main', config);
      }

      this.config = config;
      return { success: true, config };
    } catch (_error) {
      // Use default configuration
      this.config = this.getDefaultConfiguration();
      return { success: false, _error: _error.message, config: this.config };
    }
  }

  /**
   * Get default configuration
   * @returns {Object} Default configuration
   */
  getDefaultConfiguration() {
    return {
      default_template: '25_point_standard',
      validation_timeout: 300,
      auto_inheritance: true,
      mandatory_validation: true,
      evidence_storage: '/Users/jeremyparker/infinite-continue-stop-hook/development/evidence/',
      report_storage: '/Users/jeremyparker/infinite-continue-stop-hook/development/reports/success-criteria/',
      validation_agents: {
        automated: ['linter', 'build', 'test', 'security'],
        manual: ['documentation', 'architecture', 'decision_rationale'],
      },
      project_wide_criteria: {},
      validation_rules: {},
    };
  }

  /**
   * Get template by ID
   * @param {string} templateId - Template identifier
   * @returns {Promise<Object>} Template data or error
   */
  async getTemplate(templateId) {
    try {
      // Check cache first
      if (this.enableCaching && this.templateCache.has(templateId)) {
        const template = this.templateCache.get(templateId);
        return {
          success: true,
          template,
          criteria: this.extractCriteriaFromTemplate(template),
        };
      }

      // Handle built-in templates
      if (['25_point_standard', 'basic', 'comprehensive', 'enterprise'].includes(templateId)) {
        this.initializeStandardTemplates(); // Ensure templates are loaded;
        const template = this.templateCache.get(templateId);
        return {
          success: true,
          template,
          criteria: this.extractCriteriaFromTemplate(template),
        };
      }

      // Try to load custom template from filesystem;
      const customTemplatePath = path.join(
        path.dirname(this.configPath),
        'templates',
        `${templateId}.json`,
      );

      try {
        // Security: Validate template path before reading;
        const pathValidator = new FilePathSecurityValidator(this.projectRoot, this.logger);
        const pathValidation = pathValidator.validateReadPath(customTemplatePath);
        if (!pathValidation.valid) {
          throw new Error(`Security validation failed: ${pathValidation.error}`);
        }
        // eslint-disable-next-line security/detect-non-literal-fs-filename
        const templateData = await FS.readFile(pathValidation.path, 'utf8');
        const template = JSON.parse(templateData);

        // Validate template structure;
        const validation = this.validateTemplateStructure(template);
        if (!validation.valid) {
          return {
            success: false,
            error: `Invalid template structure: ${validation.errors.join(', ')}`,
            errorCode: 'INVALID_TEMPLATE_STRUCTURE',
          };
        }

        // Cache the template
        if (this.enableCaching) {
          this.templateCache.set(templateId, template);
        }

        return {
          success: true,
          template,
          criteria: this.extractCriteriaFromTemplate(template),
        };
      } catch {
        return {
          success: false,
          error: `Template '${templateId}' not found`,
          errorCode: 'TEMPLATE_NOT_FOUND',
        };
      }
    } catch (_error) {
      return {
        success: false,
        _error: _error.message,
        errorCode: 'TEMPLATE_RETRIEVAL_FAILED',
      };
    }
  }

  /**
   * Get all available templates
   * @returns {Promise<Object>} All templates
   */
  async getAllTemplates() {
    try {
      const templates = {};

      // Get built-in templates (parallelized for performance)
      const builtInIds = ['25_point_standard', 'basic', 'comprehensive', 'enterprise'];
      const templatePromises = builtInIds.map(templateId =>
        this.getTemplate(templateId).then(result => ({ templateId, result })),
      );

      const templateResults = await Promise.all(templatePromises);
      templateResults.forEach(({ templateId, result }) => {
        if (result.success) {
          // eslint-disable-next-line security/detect-object-injection -- templateId validated from known template list
          templates[templateId] = {
            ...result.template,
            type: 'built-in',
            criteriaCount: result.criteria.length,
          };
        }
      });

      // Get custom templates
      try {
        const templatesDir = path.join(path.dirname(this.configPath), 'templates');
        // Security: Validate templates directory before reading;
        const pathValidator = new FilePathSecurityValidator(this.projectRoot, this.logger);
        const pathValidation = pathValidator.validateDirectoryPath(templatesDir, 'read');
        if (!pathValidation.valid) {
          throw new Error(`Security validation failed: ${pathValidation.error}`);
        }
        // eslint-disable-next-line security/detect-non-literal-fs-filename
        const files = await FS.readdir(pathValidation.path);

        // Load custom templates in parallel for better performance;
        const customTemplatePromises = files
          .filter(file => file.endsWith('.json'))
          .map(file => {
            const templateId = file.replace('.json', '');
            return this.getTemplate(templateId).then(result => ({ templateId, result }));
          });

        const customTemplateResults = await Promise.all(customTemplatePromises);
        customTemplateResults.forEach(({ templateId, result }) => {
          if (result.success) {
            // eslint-disable-next-line security/detect-object-injection -- templateId validated from filesystem listing
            templates[templateId] = {
              ...result.template,
              type: 'custom',
              criteriaCount: result.criteria.length,
            };
          }
        });
      } catch {
        // Templates directory doesn't exist or is empty
      }

      return {
        success: true,
        templates,
        count: Object.keys(templates).length,
        types: {
          builtIn: Object.values(templates).filter(t => t.type === 'built-in').length,
          custom: Object.values(templates).filter(t => t.type === 'custom').length,
        },
      };
    } catch (_error) {
      return {
        success: false,
        _error: _error.message,
        errorCode: 'TEMPLATES_RETRIEVAL_FAILED',
      };
    }
  }

  /**
   * Detect applied template from criteria array
   * @param {Array<string>} criteria - Criteria to analyze
   * @returns {Promise<Object>} Template detection result
   */
  async detectAppliedTemplate(criteria) {
    try {
      const allTemplates = await this.getAllTemplates();
      if (!allTemplates.success) {
        return { success: false, error: allTemplates.error };
      }

      const detectionResults = [];

      for (const [templateId, template] of Object.entries(allTemplates.templates)) {
        const templateCriteria = this.extractCriteriaFromTemplate(template);

        // Calculate match percentage;
        const matchCount = templateCriteria.filter(tc => criteria.includes(tc)).length;
        const matchPercentage = templateCriteria.length > 0 ? (matchCount / templateCriteria.length) * 100 : 0;

        detectionResults.push({
          templateId,
          templateName: template.name,
          matchCount,
          totalCriteria: templateCriteria.length,
          matchPercentage,
          exactMatch: matchCount === templateCriteria.length && criteria.length === templateCriteria.length,
        });
      }

      // Sort by match percentage
      detectionResults.sort((a, b) => b.matchPercentage - a.matchPercentage);

      const bestMatch = detectionResults[0];
      const isStrongMatch = bestMatch.matchPercentage >= 80;

      return {
        success: true,
        detected: isStrongMatch ? bestMatch.templateId : null,
        confidence: bestMatch.matchPercentage,
        allMatches: detectionResults,
        summary: {
          exactMatch: bestMatch.exactMatch,
          strongMatch: isStrongMatch,
          bestMatch: bestMatch.templateId,
          confidence: Math.round(bestMatch.matchPercentage),
        },
      };
    } catch (_error) {
      return {
        success: false,
        _error: _error.message,
        errorCode: 'TEMPLATE_DETECTION_FAILED',
      };
    }
  }

  /**
   * Extract criteria strings from template object
   * @param {Object} template - Template object
   * @returns {Array<string>} Array of criteria strings
   */
  extractCriteriaFromTemplate(template) {
    if (!template) {return [];}

    // Handle legacy template format
    if (template.criteria && Array.isArray(template.criteria)) {
      return template.criteria;
    }

    // Handle new template format with categories;
    const criteria = [];
    if (template.categories) {
      Object.values(template.categories).forEach(category => {
        if (category.points && Array.isArray(category.points)) {
          category.points.forEach(point => {
            criteria.push(point.title);
          });
        }
      });
    }

    return criteria;
  }

  /**
   * Validate template structure
   * @param {Object} template - Template to validate
   * @returns {Object} Validation result
   */
  validateTemplateStructure(template) {
    const errors = [];

    if (!template.id) {errors.push('Template must have an id');}
    if (!template.name) {errors.push('Template must have a name');}
    if (!template.version) {errors.push('Template must have a version');}

    // Validate categories structure for new format
    if (template.categories) {
      Object.entries(template.categories).forEach(([categoryKey, _category]) => {
        if (!_category.name) {errors.push(`Category ${categoryKey} must have a name`);}
        if (!_category.points || !Array.isArray(_category.points)) {
          errors.push(`Category ${categoryKey} must have a points array`);
        } else {
          _category.points.forEach((point, index) => {
            if (!point.id) {errors.push(`Point ${index} in ${categoryKey} must have an id`);}
            if (!point.title) {errors.push(`Point ${index} in ${categoryKey} must have a title`);}
            if (!point.description) {errors.push(`Point ${index} in ${categoryKey} must have a description`);}
          });
        }
      });
    }

    // Validate legacy format
    if (!template.categories && !template.criteria) {
      errors.push('Template must have either categories or criteria array');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Clear template cache
   */
  clearCache() {
    if (this.enableCaching) {
      this.templateCache.clear();
      this.configCache.clear();
    }
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  getCacheStatistics() {
    return {
      enabled: this.enableCaching,
      templates: this.templateCache.size,
      configurations: this.configCache.size,
      totalMemoryUsage: this.enableCaching ? JSON.stringify([...this.templateCache.values()]).length : 0,
    };
  }
}

module.exports = CriteriaTemplateManager;
