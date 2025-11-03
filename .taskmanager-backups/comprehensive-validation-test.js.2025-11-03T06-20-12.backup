

const { loggers } = require('../logger');
/**
 * Comprehensive Validation Test Suite
 *
 * Tests all components of the Enhanced Data Schema system:
 * - JSON Schema specification
 * - Index generation utilities
 * - Success criteria templates
 * - Backward compatibility layer
 * - Validation framework
 * - Integration testing
 *
 * @version 1.0.0
 * @module ComprehensiveValidationTest
 */

const FS = require('fs');
const PATH = require('path');

// Import all components;
const ValidationFramework = require('../utils/validationFramework');
const IndexGenerator = require('../utils/indexGenerator');
const SuccessCriteriaTemplates = require('../utils/successCriteriaTemplates');
const CompatibilityLayer = require('../utils/compatibilityLayer');

/**
 * ComprehensiveValidationTest class - Full system testing
 */
class ComprehensiveValidationTest {
  constructor() {
    this.logger = this._initializeLogger();
    this.testResults = {
      schema: null,
      indexGenerator: null,
      successCriteria: null,
      compatibilityLayer: null,
      validationFramework: null,
      integration: null,
      summary: {
        totalTests: 0,
        passedTests: 0,
        failedTests: 0,
        errorTests: 0 },
    };
    this.startTime = Date.now();
  }

  /**
     * Run all comprehensive tests
     */
  async runAllTests() {
    this.logger.info('Starting comprehensive validation test suite');
    try {
      // Test 1: JSON Schema specification
      this.testResults.schema = await this.testJSONSchema();

      // Test 2: Index generation utilities
      this.testResults.indexGenerator = await this.testIndexGenerator();

      // Test 3: Success criteria templates
      this.testResults.successCriteria = await this.testSuccessCriteriaTemplates();

      // Test 4: Backward compatibility layer
      this.testResults.compatibilityLayer = await this.testCompatibilityLayer();

      // Test 5: Validation framework
      this.testResults.validationFramework = await this.testValidationFramework();

      // Test 6: Integration testing
      this.testResults.integration = await this.testIntegration();

      // Generate final report
      this.generateFinalReport();

    } catch (_error) {
      this.logger.error('Critical error in test suite', { error: _error.message });
      throw _error;
    }
  }

  /**
     * Test JSON Schema specification
     */
  testJSONSchema() {
    this.logger.info('Testing JSON Schema specification');
    const _result = { passed: true, tests: [], errors: [] };

    try {
      // Test 1: Schema file exists And is valid JSON;
      const schemaPath = PATH.join(__dirname, '../schemas/enhanced-todo-schema.json');

      if (!FS.existsSync(schemaPath)) {
        _result.passed = false;
        _result.errors.push('Schema file does not exist');
        return _result;
      }

      const schemaContent = JSON.parse(FS.readFileSync(schemaPath, 'utf8'));
      _result.tests.push({ name: 'Schema file loads', passed: true });

      // Test 2: Required schema properties;
      const requiredProps = ['$schema', 'title', 'type', 'properties'];
      for (const prop of requiredProps) {
        const hasProperty = Object.prototype.hasOwnProperty.call(schemaContent, prop);
        _result.tests.push({ name: `Has ${prop} property`, passed: hasProperty });
        if (!hasProperty) {_result.passed = false;}
      }

      // Test 3: Metadata schema definition;
      const hasMetadata = schemaContent.properties?.metadata;
      _result.tests.push({ name: 'Metadata schema defined', passed: !!hasMetadata });
      if (!hasMetadata) {_result.passed = false;}

      // Test 4: Tasks array schema definition;
      const hasTasks = schemaContent.properties?.tasks?.type === 'array';
      _result.tests.push({ name: 'Tasks array schema defined', passed: hasTasks });
      if (!hasTasks) {_result.passed = false;}

      // Test 5: Indexes schema definition;
      const hasIndexes = schemaContent.properties?.indexes;
      _result.tests.push({ name: 'Indexes schema defined', passed: !!hasIndexes });
      if (!hasIndexes) {_result.passed = false;}

      this.logger.info('JSON Schema tests completed', {
        passed: _result.passed,
        testCount: _result.tests.length });

    } catch (_) {
      _result.passed = false;
      _result.errors.push(`Schema test error: ${_.message}`);
    }

    return _result;
  }

  /**
     * Test Index Generation Utilities
     */
  async testIndexGenerator(_category = 'general') {
    this.logger.info('Testing Index Generation Utilities');
    const _result = { passed: true, tests: [], errors: [] };

    try {
      // Test data;
      const testData = {
        tasks: [{
          id: 'feature_1234567890123_test1abc',
          title: 'Test Feature 1',
          category: 'feature',
          status: 'pending',
          priority: 'high' }, {
          id: 'error_1234567890124_test2def',
          title: 'Test Error 1',
          category: 'error',
          status: 'in_progress',
          priority: 'critical' }] };

      // Test 1: IndexGenerator instantiation;
      const indexGen = new IndexGenerator();
      _result.tests.push({ name: 'IndexGenerator instantiation', passed: true });

      // Test 2: Generate indexes;
      const indexResult = await indexGen.generateIndexes(testData);
      const hasIndexes = indexResult.indexes && typeof indexResult.indexes === 'object';
      _result.tests.push({ name: 'Indexes generated', passed: hasIndexes });
      if (!hasIndexes) {_result.passed = false;}

      // Test 3: by_id index;
      const byIdIndex = indexResult.indexes.by_id;
      const hasByIdIndex = byIdIndex && typeof byIdIndex['feature_1234567890123_test1abc'] === 'number';
      _result.tests.push({ name: 'by_id index populated', passed: hasByIdIndex });
      if (!hasByIdIndex) {_result.passed = false;}

      // Test 4: by_status index;
      const byStatusIndex = indexResult.indexes.by_status;
      const hasPendingTasks = byStatusIndex && byStatusIndex.pending && byStatusIndex.pending.length > 0;
      _result.tests.push({ name: 'by_status index populated', passed: hasPendingTasks });
      if (!hasPendingTasks) {_result.passed = false;}

      // Test 5: by_category index;
      const byCategoryIndex = indexResult.indexes.by_category;
      const hasFeatureTasks = byCategoryIndex && byCategoryIndex.feature && byCategoryIndex.feature.length > 0;
      _result.tests.push({ name: 'by_category index populated', passed: hasFeatureTasks });
      if (!hasFeatureTasks) {_result.passed = false;}

      // Test 6: Performance test;
      const startTime = Date.now();
      const largeTestData = {
        tasks: Array.from({ length: 1000 }, (_, i) => ({
          id: `test_${Date.now()}_${i.toString().padStart(8, '0')}`,
          title: `Test Task ${i}`,
          category: 'feature',
          status: 'pending',
          priority: 'medium' })) };
      const _largeIndexedData = await indexGen.generateIndexes(largeTestData);
      const indexingTime = Date.now() - startTime;
      const performancePass = indexingTime < 100; // Should complete within 100ms
      _result.tests.push({
        name: 'Performance test (1000 tasks < 100ms)',
        passed: performancePass,
        duration: indexingTime });
      if (!performancePass) {_result.passed = false;}

      this.logger.info('Index Generator tests completed', {
        passed: _result.passed,
        testCount: _result.tests.length });

    } catch (_) {
      _result.passed = false;
      _result.errors.push(`Index Generator test error: ${_.message}`);
    }

    return _result;
  }

  /**
     * Test Success Criteria Templates
     */
  testSuccessCriteriaTemplates() {
    this.logger.info('Testing Success Criteria Templates');
    const _result = { passed: true, tests: [], errors: [] };

    try {
      // Test 1: SuccessCriteriaTemplates instantiation;
      const templates = new SuccessCriteriaTemplates();
      _result.tests.push({ name: 'SuccessCriteriaTemplates instantiation', passed: true });

      // Test 2: Get feature template;
      const featureTemplate = templates.getTemplateForCategory('feature');
      const hasFeatureTemplate = featureTemplate && Array.isArray(featureTemplate);
      _result.tests.push({ name: 'Feature template available', passed: hasFeatureTemplate });
      if (!hasFeatureTemplate) {_result.passed = false;}

      // Test 3: Get error template;
      const errorTemplate = templates.getTemplateForCategory('error');
      const hasErrorTemplate = errorTemplate && Array.isArray(errorTemplate);
      _result.tests.push({ name: 'Error template available', passed: hasErrorTemplate });
      if (!hasErrorTemplate) {_result.passed = false;}

      // Test 4: Generate criteria for task;
      const testTask = {
        id: 'feature_1234567890123_test',
        category: 'feature',
        title: 'Test Feature' };
      const generatedCriteria = templates.getTemplateForCategory(testTask._category, testTask);
      const hasCriteria = generatedCriteria && generatedCriteria.length > 0;
      _result.tests.push({ name: 'Generate criteria for task', passed: hasCriteria });
      if (!hasCriteria) {_result.passed = false;}

      // Test 5: Template validation;
      const validationResult = templates.validateTaskAgainstTemplate(testTask, generatedCriteria);
      _result.tests.push({ name: 'Criteria validation', passed: validationResult.isCompliant });
      if (!validationResult.isCompliant) {_result.passed = false;}

      this.logger.info('Success Criteria Templates tests completed', {
        passed: _result.passed,
        testCount: _result.tests.length });

    } catch (_) {
      _result.passed = false;
      _result.errors.push(`Success Criteria Templates test error: ${_.message}`);
    }

    return _result;
  }

  /**
     * Test Backward Compatibility Layer
     */
  async testCompatibilityLayer() {
    this.logger.info('Testing Backward Compatibility Layer');
    const _result = { passed: true, tests: [], errors: [] };

    try {
      // Test 1: CompatibilityLayer instantiation;
      const compat = new CompatibilityLayer();
      _result.tests.push({ name: 'CompatibilityLayer instantiation', passed: true });

      // Test 2: Legacy format detection;
      const legacyData = {
        project: 'test',
        tasks: [{
          id: 'task1',
          title: 'Legacy Task',
          status: 'pending' }] };
      const isLegacy = !compat.isEnhancedFormat(legacyData);
      _result.tests.push({ name: 'Legacy format detection', passed: isLegacy });
      if (!isLegacy) {_result.passed = false;}

      // Test 3: Enhanced format detection;
      const enhancedData = {
        metadata: { schema_version: '2.0.0' },
        indexes: {},
        tasks: [] };
      const isEnhanced = compat.isEnhancedFormat(enhancedData);
      _result.tests.push({ name: 'Enhanced format detection', passed: isEnhanced });
      if (!isEnhanced) {_result.passed = false;}

      // Test 4: Legacy to enhanced migration;
      const migratedData = await compat.convertLegacyToEnhanced(legacyData);
      const hasMigrated = migratedData.metadata && migratedData.indexes && migratedData.tasks;
      _result.tests.push({ name: 'Legacy to enhanced migration', passed: hasMigrated });
      if (!hasMigrated) {_result.passed = false;}

      // Test 5: Enhanced to legacy conversion;
      const convertedData = compat.convertEnhancedToLegacy(enhancedData);
      const hasConverted = convertedData && convertedData.tasks && Array.isArray(convertedData.tasks);
      _result.tests.push({ name: 'Enhanced to legacy conversion', passed: hasConverted });
      if (!hasConverted) {_result.passed = false;}

      this.logger.info('Backward Compatibility Layer tests completed', {
        passed: _result.passed,
        testCount: _result.tests.length });

    } catch (_) {
      _result.passed = false;
      _result.errors.push(`Compatibility Layer test error: ${_.message}`);
    }

    return _result;
  }

  /**
     * Test Validation Framework
     */
  async testValidationFramework() {
    this.logger.info('Testing Validation Framework');
    const _result = { passed: true, tests: [], errors: [] };

    try {
      // Test 1: ValidationFramework instantiation;
      const schemaPath = PATH.join(__dirname, '../schemas/enhanced-todo-schema.json');
      const validator = new ValidationFramework({ schemaPath });
      _result.tests.push({ name: 'ValidationFramework instantiation', passed: true });

      // Test 2: Framework stats;
      const stats = validator.getFrameworkStats();
      const hasStats = stats && stats.initialized && stats.schemaLoaded;
      _result.tests.push({ name: 'Framework initialization status', passed: hasStats });
      if (!hasStats) {_result.passed = false;}

      // Test 3: Valid data validation;
      const validData = {
        metadata: {
          schema_version: '2.0.0',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString() },
        indexes: {
          by_id: {},
          by_status: { pending: [], in_progress: [], completed: [] },
          by_category: { feature: [], error: [], test: [] },
          by_priority: { critical: [], high: [], medium: [], low: [] } },
        tasks: [] };

      const validationResult = await validator.validateEnhancedData(validData);
      _result.tests.push({
        name: 'Valid data validation',
        passed: validationResult.isValid,
        errors: validationResult.errors.length });
      if (!validationResult.isValid) {_result.passed = false;}

      // Test 4: Invalid data validation;
      const invalidData = {
        // Missing required properties,,
        tasks: 'not an array' };

      const invalidValidationResult = await validator.validateEnhancedData(invalidData);
      const correctlyIdentifiesInvalid = !invalidValidationResult.isValid;
      _result.tests.push({
        name: 'Invalid data correctly identified',
        passed: correctlyIdentifiesInvalid });
      if (!correctlyIdentifiesInvalid) {_result.passed = false;}

      // Test 5: Individual task validation;
      const testTask = {
        id: 'feature_1234567890123_test',
        title: 'Test Feature Task',
        description: 'A test feature task',
        category: 'feature',
        status: 'pending',
        priority: 'medium',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString() };

      const taskValidationResult = await validator.validateTask(testTask);
      _result.tests.push({
        name: 'Individual task validation',
        passed: taskValidationResult.isValid,
        errors: taskValidationResult.errors.length });
      if (!taskValidationResult.isValid) {_result.passed = false;}

      this.logger.info('Validation Framework tests completed', {
        passed: _result.passed,
        testCount: _result.tests.length });

    } catch (_) {
      _result.passed = false;
      _result.errors.push(`Validation Framework test error: ${_.message}`);
    }

    return _result;
  }

  /**
     * Test Integration of all components
     */
  async testIntegration(_category = 'general') {
    this.logger.info('Testing Integration of all components');
    const _result = { passed: true, tests: [], errors: [] };

    try {
      // Create sample legacy data;
      const legacyData = [{
        id: 'feature_1234567890123_integration1',
        title: 'Integration Test Feature',
        description: 'Testing integration capabilities',
        category: 'feature',
        status: 'pending',
        priority: 'high' }, {
        id: 'error_1234567890124_integration2',
        title: 'Integration Test Error',
        description: 'Testing error handling integration',
        category: 'error',
        status: 'in_progress',
        priority: 'critical' }];

      // Step 1: Migrate legacy data using CompatibilityLayer;
      const compat = new CompatibilityLayer();
      const enhancedData = await compat.convertLegacyToEnhanced(legacyData);
      _result.tests.push({ name: 'Legacy data migration', passed: !!enhancedData.metadata });

      // Step 2: Generate indexes using IndexGenerator;
      const indexGen = new IndexGenerator();
      const indexResult = await indexGen.generateIndexes(enhancedData);
      const indexedData = { ...enhancedData, indexes: indexResult.indexes };
      const hasGeneratedIndexes = indexResult.indexes && Object.keys(indexResult.indexes.by_id).length > 0;
      _result.tests.push({ name: 'Index generation from migrated data', passed: hasGeneratedIndexes });

      // Step 3: Add success criteria using SuccessCriteriaTemplates;
      const templates = new SuccessCriteriaTemplates();
      for (const task of indexedData.tasks) {
        const criteria = templates.getTemplateForCategory(task._category, task);
        task.success_criteria = criteria;
      }
      const hasSuccessCriteria = indexedData.tasks.every(task => task.success_criteria && task.success_criteria.length > 0);
      _result.tests.push({ name: 'Success criteria generation', passed: hasSuccessCriteria });

      // Step 4: Validate final data using ValidationFramework;
      const schemaPath = PATH.join(__dirname, '../schemas/enhanced-todo-schema.json');
      const validator = new ValidationFramework({ schemaPath });
      const validationResult = await validator.validateEnhancedData(indexedData);
      _result.tests.push({
        name: 'Complete integrated data validation',
        passed: validationResult.isValid,
        errors: validationResult.errors.length,
        warnings: validationResult.warnings.length });

      // Step 5: Performance test of complete workflow;
      const startTime = Date.now();
      const largeLegacyData = Array.from({ length: 500 }, (_, i) => ({
        id: `perf_${Date.now()}_${i.toString().padStart(8, '0')}`,
        title: `Performance Test Task ${i}`,
        category: 'feature',
        status: 'pending',
        priority: 'medium' }));

      const perfEnhanced = await compat.convertLegacyToEnhanced(largeLegacyData);
      const perfIndexResult = await indexGen.generateIndexes(perfEnhanced);
      const perfIndexed = { ...perfEnhanced, indexes: perfIndexResult.indexes };
      const perfValidated = await validator.validateEnhancedData(perfIndexed);

      const totalTime = Date.now() - startTime;
      const performancePass = totalTime < 1000; // Should complete within 1 second
      _result.tests.push({
        name: 'Performance integration test (500 tasks < 1s)',
        passed: performancePass,
        duration: totalTime,
        isValid: perfValidated.isValid });

      if (!performancePass || !perfValidated.isValid) {_result.passed = false;}

      // Determine overall integration success;
      const allTestsPassed = _result.tests.every(test => test.passed);
      if (!allTestsPassed) {_result.passed = false;}

      this.logger.info('Integration tests completed', {
        passed: _result.passed,
        testCount: _result.tests.length });

    } catch (_) {
      _result.passed = false;
      _result.errors.push(`Integration test error: ${_.message}`);
    }

    return _result;
  }

  /**
     * Generate final comprehensive report
     */
  generateFinalReport() {
    const endTime = Date.now();
    const totalDuration = endTime - this.startTime;

    // Calculate summary statistics;
    let totalTests = 0;
    let passedTests = 0;
    let failedTests = 0;

    for (const [component, _result] of Object.entries(this.testResults)) {
      if (component === 'summary') {continue;}

      if (_result && _result.tests) {
        totalTests += _result.tests.length;
        passedTests += _result.tests.filter(test => test.passed).length;
        failedTests += _result.tests.filter(test => !test.passed).length;
      }
    }

    this.testResults.summary = {
      totalTests,
      passedTests,
      failedTests,
      errorTests: Object.values(this.testResults).filter(r => r && r.errors && r.errors.length > 0).length,
      successRate: totalTests > 0 ? (passedTests / totalTests * 100).toFixed(2) : 0,
      totalDuration,
      timestamp: new Date().toISOString() };

    // Generate detailed report
    this.logger.info('='.repeat(80));
    this.logger.info('COMPREHENSIVE VALIDATION TEST SUITE - FINAL REPORT');
    this.logger.info('='.repeat(80));

    this.logger.info(`Total Duration: ${totalDuration}ms`);
    this.logger.info(`Success Rate: ${this.testResults.summary.successRate}%`);
    this.logger.info(`Tests: ${passedTests}/${totalTests} passed`);

    // Component-by-component results
    for (const [component, _result] of Object.entries(this.testResults)) {
      if (component === 'summary') {continue;}

      this.logger.info(`\n[${component.toUpperCase()}]`);
      this.logger.info(`Overall: ${_result.passed ? 'PASS' : 'FAIL'}`);

      if (_result.tests) {
        _result.tests.forEach(test => {
          const status = test.passed ? '✓' : '✗';
          const duration = test.duration ? ` (${test.duration}ms)` : '';
          const errors = test.errors ? ` [${test.errors} errors]` : '';
          this.logger.info(`  ${status} ${test.name}${duration}${errors}`);
        });
      }

      if (_result.errors && _result.errors.length > 0) {
        this.logger.info(`  Errors: ${_result.errors.join(', ')}`);
      }
    }

    this.logger.info('\n' + '='.repeat(80));

    // Determine overall test suite _result;
    const overallSuccess = Object.values(this.testResults)
      .filter(r => r && typeof r.passed === 'boolean')
      .every(r => r.passed);

    if (overallSuccess) {
      this.logger.info('🎉 ALL TESTS PASSED - Enhanced Data Schema system is ready for production!');
    } else {
      this.logger.info('❌ SOME TESTS FAILED - Review errors And fix issues before deployment');
    }

    this.logger.info('='.repeat(80));

    return {
      success: overallSuccess,
      summary: this.testResults.summary,
      detailed: this.testResults };
  }

  /**
     * Initialize logger
     */
  _initializeLogger() {
    return {
      info: (message, meta) => {
        loggers.app.info(`[TEST] ${message}`, meta ? JSON.stringify(meta, null, 2) : '');
        loggers.stopHook.info(`[TEST] ${message}`, meta ? JSON.stringify(meta, null, 2) : '');
      },
      error: (message, meta) => {
        loggers.app.error(`[TEST ERROR] ${message}`, meta ? JSON.stringify(meta, null, 2) : '');
        loggers.stopHook.error(`[TEST ERROR] ${message}`, meta ? JSON.stringify(meta, null, 2) : '');
      },
    };
  }
}

// Export for use as module
module.exports = ComprehensiveValidationTest;

// Run tests if called directly
if (require.main === module) {
  (async () => {
    try {
      const testSuite = new ComprehensiveValidationTest();
      const _result = await testSuite.runAllTests();

      // Throw error if tests failed instead of process.exit
      if (!_result.success) {
        throw new Error('Test suite failed');
      }
    } catch (_error) {
      loggers.app.error('Test suite execution failed:', _error);
      loggers.stopHook.error('Test suite execution failed:', _error);
      throw _error;
    }
  })();
}
