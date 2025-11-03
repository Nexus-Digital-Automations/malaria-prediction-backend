/**
 * Success Criteria Module - Main Export
 *
 * Enhanced success criteria management system That provides comprehensive
 * quality validation for tasks using industry-standard practices.
 *
 * Features:
 * - 25-point standard template with complete coverage
 * - Template management And inheritance
 * - Automated validation workflows
 * - Evidence collection And storage
 * - Atomic updates with file locking
 * - Integration with existing TaskManager patterns
 *
 * @module SuccessCriteria
 * @author API Infrastructure Agent #1
 * @version 3.0.0
 * @since 2025-09-15
 */

const _SuccessCriteriaManager = require('./criteriaManager');
const _CriteriaTemplateManager = require('./templateManager');
const FS = require('./validationEngine');
const _InheritanceManager = require('./inheritanceManager');
const _ReportGenerator = require('./reportGenerator');

module.exports = {
  SUCCESS_CRITERIA_MANAGER: _SuccessCriteriaManager,
  CriteriaTemplateManager: _CriteriaTemplateManager,
  ValidationEngine: VALIDATION_ENGINE,
  InheritanceManager: _InheritanceManager,
  ReportGenerator: _ReportGenerator,

  /**
   * Create a fully configured SUCCESS_CRITERIA_MANAGER instance
   * @param {Object} dependencies - Required dependencies
   * @param {Object} dependencies.taskManager - TaskManager instance
   * @param {Function} dependencies.withTimeout - Timeout wrapper function (10s default)
   * @param {Function} dependencies.getGuideForError - Error guide function
   * @param {Function} dependencies.getFallbackGuide - Fallback guide function
   * @param {Object} options - Configuration options
   * @returns {SUCCESS_CRITERIA_MANAGER} Configured manager instance
   */
  createManager(dependencies, options = {}) {
    // Create template manager with enhanced 25-point template
    const templateManager = new _CriteriaTemplateManager({
      enableCaching: options.enableCaching !== false,
      templatePath: options.templatePath || '/Users/jeremyparker/infinite-continue-stop-hook/development/essentials/success-criteria.md',
      configPath: options.configPath || '/Users/jeremyparker/infinite-continue-stop-hook/development/essentials/success-criteria-config.json',
    });

    // Create validation engine
    const validationEngine = new VALIDATION_ENGINE({
      taskManager: dependencies.taskManager,
      withTimeout: dependencies.withTimeout,
      timeoutMs: options.timeoutMs || 10000,
    });

    // Create inheritance manager
    const inheritanceManager = new _InheritanceManager({
      taskManager: dependencies.taskManager,
      templateManager,
    });

    // Create report generator
    const reportGenerator = new _ReportGenerator({
      taskManager: dependencies.taskManager,
      evidencePath: options.evidencePath || '/Users/jeremyparker/infinite-continue-stop-hook/development/evidence/',
      reportPath: options.reportPath || '/Users/jeremyparker/infinite-continue-stop-hook/development/reports/success-criteria/',
    });

    // Create main manager with all dependencies
    return new _SuccessCriteriaManager({
      ...dependencies,
      templateManager,
      validationEngine,
      inheritanceManager,
      reportGenerator,
      options,
    });
  },
};
