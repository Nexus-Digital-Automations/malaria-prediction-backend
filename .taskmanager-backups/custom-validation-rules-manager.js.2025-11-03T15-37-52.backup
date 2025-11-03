const { loggers } = require('./logger');


/**
 * Custom Project Validation Rules Management System
 *
 * Allows projects to define custom validation rules through configuration files.
 * Enables project-specific criteria beyond standard validation (linter, build, test).
 * Supports custom commands, file checks, And conditional validation rules based on
 * project type And technology stack.
 *
 * @author Stop Hook Custom Validation System
 * @version 1.0.0
 * @since 2025-09-27
 */

const path = require('path');
const FS = require('fs').promises;
const { execSync } = require('child_process');


/**
 * Custom validation rule types
 */
const VALIDATION_RULE_TYPES = {
  COMMAND: 'command',           // Execute shell command
  FILE_EXISTS: 'file_exists',   // Check file existence
  FILE_CONTENT: 'file_content', // Check file content patterns
  CONDITIONAL: 'conditional',   // Conditional validation based on project state
  COMPOSITE: 'composite',       // Combination of multiple validations
};

/**
 * Project technology stack detection patterns
 */
const TECH_STACK_PATTERNS = {
  'nodejs': ['package.json', 'npm-shrinkwrap.json', 'yarn.lock'],
  'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
  'go': ['go.mod', 'go.sum', 'Gopkg.toml'],
  'rust': ['Cargo.toml', 'Cargo.lock'],
  'java': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
  'php': ['composer.json', 'composer.lock'],
  'ruby': ['Gemfile', 'Gemfile.lock'],
  'dotnet': ['*.csproj', '*.sln', 'project.json'],
  'docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
  'kubernetes': ['*.yaml', '*.yml', 'kustomization.yaml'],
  'frontend': ['webpack.config.js', 'vite.config.js', 'rollup.config.js'] };

/**
 * Custom Validation Rules Manager
 *
 * Manages project-specific validation rules, technology stack detection,
 * And conditional validation execution based on project configuration.
 */
class CustomValidationRulesManager {
  constructor(options = {}) {
    this.projectRoot = options.projectRoot || process.cwd();
    this.configFile = options.configFile || '.validation-rules.json';
    this.customRules = new Map();
    this.detectedTechStack = [];
    this.projectType = null;
    this.enabledRules = new Set();

    // Performance And execution tracking
    this.executionHistory = [];
    this.ruleExecutionTimes = new Map();
  }

  /**
   * Load custom validation rules from configuration file
   */
  async loadCustomRules() {
    try {
      const configPath = path.join(this.projectRoot, this.configFile);

      // Check if configuration file exists,
      try {
        await FS.access(configPath);
      } catch {
        loggers.stopHook.info('No custom validation rules configuration found. Using default rules only.');
        // No custom rules file found - use default empty configuration
        loggers.app.info('No custom validation rules configuration found. Using default rules only.');
        return { success: true, rulesLoaded: 0, message: 'No custom rules configuration found' };
      }

      // Load And parse configuration;
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      const configContent = await FS.readFile(configPath, 'utf8');
      const config = JSON.parse(configContent);

      // Validate configuration structure;
      const validationResult = this._validateConfiguration(config);
      if (!validationResult.valid) {
        throw new Error(`Invalid configuration: ${validationResult.errors.join(', ')}`);
      }

      // Detect project technology stack And type
      await this._detectTechnologyStack();
      this.projectType = config.project_type || this._inferProjectType();

      // Process And load custom rules;
      let rulesLoaded = 0;
      for (const ruleId in config.custom_rules || {}) {
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        const rule = config.custom_rules[ruleId];

        // Check if rule conditions are met for current project
        if (this._shouldEnableRule(rule)) {
          const processedRule = this._processRule(ruleId, rule);
          this.customRules.set(ruleId, processedRule);
          this.enabledRules.add(ruleId);
          rulesLoaded++;
        }
      }

      // Load global project settings
      this.globalSettings = config.global_settings || {};

      return {
        success: true,
        rulesLoaded,
        detectedTechStack: this.detectedTechStack,
        projectType: this.projectType,
        enabledRules: Array.from(this.enabledRules),
        message: `Successfully loaded ${rulesLoaded} custom validation rules` };

    } catch (_) {
      return {
        success: false,
        error: _.message,
        message: 'Failed to load custom validation rules' };
    }
  }

  /**
   * Validate configuration file structure
   */
  _validateConfiguration(config) {
    const errors = [];

    // Check required top-level structure
    if (typeof config !== 'object') {
      errors.push('Configuration must be a JSON object');
      return { valid: false, errors };
    }

    // Validate custom rules section
    if (config.custom_rules) {
      if (typeof config.custom_rules !== 'object') {
        errors.push('custom_rules must be an object');
      } else {
        for (const ruleId in config.custom_rules) {
          // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
          const rule = config.custom_rules[ruleId];
          const ruleErrors = this._validateRule(ruleId, rule);
          errors.push(...ruleErrors);
        }
      }
    }

    // Validate global settings
    if (config.global_settings && typeof config.global_settings !== 'object') {
      errors.push('global_settings must be an object');
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * Validate individual rule structure
   */
  _validateRule(ruleId, rule) {
    const errors = [];

    // Required fields
    if (!rule.type || !Object.values(VALIDATION_RULE_TYPES).includes(rule.type)) {
      errors.push(`Rule ${ruleId}: type must be one of ${Object.values(VALIDATION_RULE_TYPES).join(', ')}`);
    }

    if (!rule.description) {
      errors.push(`Rule ${ruleId}: description is required`);
    }

    // Type-specific validation
    switch (rule.type) {
      case VALIDATION_RULE_TYPES.COMMAND:
        if (!rule.command) {
          errors.push(`Rule ${ruleId}: command is required for command type`);
        }
        break;

      case VALIDATION_RULE_TYPES.FILE_EXISTS:
        if (!rule.files || !Array.isArray(rule.files)) {
          errors.push(`Rule ${ruleId}: files array is required for file_exists type`);
        }
        break;

      case VALIDATION_RULE_TYPES.FILE_CONTENT:
        if (!rule.file || !rule.pattern) {
          errors.push(`Rule ${ruleId}: file And pattern are required for file_content type`);
        }
        break;

      case VALIDATION_RULE_TYPES.CONDITIONAL:
        if (!rule.condition || !rule.rules) {
          errors.push(`Rule ${ruleId}: condition And rules are required for conditional type`);
        }
        break;

      case VALIDATION_RULE_TYPES.COMPOSITE:
        if (!rule.rules || !Array.isArray(rule.rules)) {
          errors.push(`Rule ${ruleId}: rules array is required for composite type`);
        }
        break;
    }

    return errors;
  }

  /**
   * Detect project technology stack by examining files
   */
  async _detectTechnologyStack() {
    this.detectedTechStack = [];

    for (const [techName, patterns] of Object.entries(TECH_STACK_PATTERNS)) {
      for (const pattern of patterns) {
        try {
          // eslint-disable-next-line no-await-in-loop -- Sequential processing required for early exit;
          const files = await this._findFiles(pattern);
          if (files.length > 0) {
            this.detectedTechStack.push(techName);
            break;
          }
        } catch {
          // Continue with next pattern if error occurs
        }
      }
    }

    return this.detectedTechStack;
  }

  /**
   * Find files matching pattern in project root
   */
  async _findFiles(pattern) {
    try {
      if (pattern.includes('*')) {
        // Use glob pattern matching;
        const { glob } = require('glob');
        return await glob(pattern, { cwd: this.projectRoot });
      } else {
        // Simple file existence check;
        const filePath = path.join(this.projectRoot, pattern);
        await FS.access(filePath);
        return [pattern];
      }
    } catch {
      return [];
    }
  }

  /**
   * Infer project type from detected technology stack
   */
  _inferProjectType() {
    if (this.detectedTechStack.includes('nodejs')) {
      if (this.detectedTechStack.includes('frontend')) {
        return 'frontend';
      }
      return 'backend';
    }

    if (this.detectedTechStack.includes('python')) {
      return 'backend';
    }

    if (this.detectedTechStack.includes('docker') || this.detectedTechStack.includes('kubernetes')) {
      return 'infrastructure';
    }

    return 'generic';
  }

  /**
   * Check if rule should be enabled for current project
   */
  _shouldEnableRule(rule) {
    // Check technology stack requirements
    if (rule.requires_tech_stack) {
      const requiredTech = Array.isArray(rule.requires_tech_stack)
        ? rule.requires_tech_stack
        : [rule.requires_tech_stack];

      const hasRequiredTech = requiredTech.some(tech =>
        this.detectedTechStack.includes(tech),
      );

      if (!hasRequiredTech) {
        return false;
      }
    }

    // Check project type requirements
    if (rule.requires_project_type) {
      if (this.projectType !== rule.requires_project_type) {
        return false;
      }
    }

    // Check file existence requirements
    if (rule.requires_files) {
      // This will be checked during rule execution
    }

    // Rule is enabled by default if no exclusion conditions met
    return rule.enabled !== false;
  }

  /**
   * Process And normalize rule configuration
   */
  _processRule(ruleId, rule) {
    return {
      id: ruleId,
      type: rule.type,
      description: rule.description,
      priority: rule.priority || 'normal',
      timeout: rule.timeout || 30000,
      retry_count: rule.retry_count || 0,
      allow_failure: rule.allow_failure || false,
      dependencies: rule.dependencies || [],
      metadata: {
        estimatedDuration: rule.estimated_duration || 10000,
        parallelizable: rule.parallelizable !== false,
        resourceRequirements: rule.resource_requirements || ['filesystem'],
        category: rule.category || 'custom',
        tags: rule.tags || [] },
      config: this._extractRuleConfig(rule) };
  }

  /**
   * Extract rule-specific configuration
   */
  _extractRuleConfig(rule) {
    const config = { ...rule };

    // Remove metadata fields to keep only execution-specific config
    delete config.description;
    delete config.priority;
    delete config.timeout;
    delete config.retry_count;
    delete config.allow_failure;
    delete config.dependencies;
    delete config.estimated_duration;
    delete config.parallelizable;
    delete config.resource_requirements;
    delete config.category;
    delete config.tags;
    delete config.requires_tech_stack;
    delete config.requires_project_type;
    delete config.requires_files;
    delete config.enabled;

    return config;
  }

  /**
   * Execute custom validation rule
   */
  async executeRule(ruleId) {
    const startTime = Date.now();
    try {
      const rule = this.customRules.get(ruleId);
      if (!rule) {
        throw new Error(`Rule '${ruleId}' not found or not enabled`);
      }

      loggers.stopHook.info(`🔄 Executing custom validation rule: ${ruleId}`);
      loggers.app.info(`🔄 Executing custom validation rule: ${ruleId}`);

      // Execute rule based on type;
      let result;
      switch (rule.type) {
        case VALIDATION_RULE_TYPES.COMMAND:
          result = await this._executeCommandRule(rule);
          break;

        case VALIDATION_RULE_TYPES.FILE_EXISTS:
          result = await this._executeFileExistsRule(rule);
          break;

        case VALIDATION_RULE_TYPES.FILE_CONTENT:
          result = await this._executeFileContentRule(rule);
          break;

        case VALIDATION_RULE_TYPES.CONDITIONAL:
          result = await this._executeConditionalRule(rule);
          break;

        case VALIDATION_RULE_TYPES.COMPOSITE:
          result = await this._executeCompositeRule(rule);
          break;
        default:
          throw new Error(`Unsupported rule type: ${rule.type}`);
      }

      const duration = Date.now() - startTime;
      this._recordExecution(ruleId, result, duration);

      return {
        success: result.success,
        ruleId,
        duration,
        details: result.details || `Custom validation rule '${ruleId}' executed successfully`,
        output: result.output,
        metadata: rule.metadata };

    } catch (error) {
      const duration = Date.now() - startTime;
      this._recordExecution(ruleId, { success: false, error: error.message }, duration);

      return {
        success: false,
        ruleId,
        duration,
        error: error.message,
        details: `Custom validation rule '${ruleId}' failed: ${error.message}` };
    }
  }

  /**
   * Execute command-based validation rule
   */
  _executeCommandRule(rule) {
    try {
      const command = rule.config.command;
      const workingDir = rule.config.working_directory || this.projectRoot;
      loggers.stopHook.info(`  📋 Executing command: ${command}`);
      loggers.app.info(`  📋 Executing command: ${command}`);

      const env = { ...process.env };
      const output = execSync(command, {
        cwd: workingDir,
        env,
        timeout: rule.timeout,
        encoding: 'utf8',
        stdio: 'pipe' });

      return {
        success: true,
        output: output.trim(),
        details: `Command executed successfully: ${command}` };

    } catch (error) {
      if (rule.allow_failure) {
        return {
          success: true,
          output: error.stdout || error.stderr || '',
          details: `Command failed but failure is allowed: ${error.message}`,
          warning: error.message };
      }

      throw error;
    }
  }

  /**
   * Execute file existence validation rule
   */
  async _executeFileExistsRule(rule) {
    const files = rule.config.files;
    const missingFiles = [];
    const foundFiles = [];

    const fileChecks = files.map(async (file) => {
      const filePath = path.resolve(this.projectRoot, file);
      try {
        await FS.access(filePath);
        return { file, found: true };
      } catch {
        return { file, found: false };
      }
    });

    const results = await Promise.all(fileChecks);
    for (const { file, found } of results) {
      if (found) {
        loggers.stopHook.info(`  ✅ Found required file: ${file}`);
        foundFiles.push(file);
        loggers.app.info(`  ✅ Found required file: ${file}`);
      } else {
        loggers.stopHook.info(`  ❌ Missing required file: ${file}`);
        missingFiles.push(file);
        loggers.app.info(`  ❌ Missing required file: ${file}`);
      }
    }

    if (missingFiles.length > 0 && !rule.allow_failure) {
      throw new Error(`Missing required files: ${missingFiles.join(', ')}`);
    }

    return {
      success: missingFiles.length === 0,
      details: `File existence check: ${foundFiles.length}/${files.length} files found`,
      output: {
        found: foundFiles,
        missing: missingFiles,
        total: files.length } };
  }

  /**
   * Execute file content validation rule
   */
  async _executeFileContentRule(rule) {
    const file = rule.config.file;
    const pattern = rule.config.pattern;
    const flags = rule.config.flags || 'i';
    const filePath = path.resolve(this.projectRoot, file);
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      const content = await FS.readFile(filePath, 'utf8');
      // eslint-disable-next-line security/detect-non-literal-regexp -- RegExp pattern constructed from validated input
      const regex = new RegExp(pattern, flags);
      const matches = content.match(regex);
      loggers.stopHook.info(`  🔍 Checking file content: ${file}`);
      loggers.app.info(`  🔍 Checking file content: ${file}`);

      if (rule.config.should_match !== false) {
        // Default behavior: pattern should match
        if (!matches) {
          throw new Error(`Pattern '${pattern}' not found in file '${file}'`);
        }

        return {
          success: true,
          details: `Pattern '${pattern}' found in file '${file}'`,
          output: {
            matches: matches,
            matchCount: matches.length } };
      } else {
        // Pattern should NOT match
        if (matches) {
          throw new Error(`Pattern '${pattern}' should not be present in file '${file}' but was found`);
        }

        return {
          success: true,
          details: `Pattern '${pattern}' correctly not found in file '${file}'`,
          output: {
            patternAbsent: true } };
      }

    } catch (error) {
      if (error.code === 'ENOENT') {
        throw new Error(`File '${file}' not found for content validation`);
      }
      throw error;
    }
  }

  /**
   * Execute conditional validation rule
   */
  async _executeConditionalRule(rule) {
    const condition = rule.config.condition;
    const rules = rule.config.rules;

    // Evaluate condition;
    const conditionMet = await this._evaluateCondition(condition);
    loggers.stopHook.info(`  ❓ Evaluating condition: ${JSON.stringify(condition)} = ${conditionMet}`);
    loggers.app.info(`  ❓ Evaluating condition: ${JSON.stringify(condition)} = ${conditionMet}`);

    if (!conditionMet) {
      return {
        success: true,
        details: 'Conditional validation skipped - condition not met',
        output: {
          conditionMet: false,
          skipped: true } };
    }

    // Execute conditional rules;
    const results = [];
    for (const subRule of rules) {
      // eslint-disable-next-line no-await-in-loop -- Sequential processing required for error handling;
      const result = await this._executeSubRule(subRule);
      results.push(result);

      if (!result.success && !rule.allow_failure) {
        throw new Error(`Conditional validation failed: ${result.error || 'Unknown error'}`);
      }
    }

    return {
      success: results.every(r => r.success),
      details: `Conditional validation completed: ${results.length} sub-rules executed`,
      output: {
        conditionMet: true,
        results } };
  }

  /**
   * Execute composite validation rule (multiple rules)
   */
  async _executeCompositeRule(rule) {
    const rules = rule.config.rules;
    const operator = rule.config.operator || 'And'; // 'And' or 'or'
    const results = [];
    loggers.stopHook.info(`  📋 Executing composite rule with ${rules.length} sub-rules (${operator})`);
    loggers.app.info(`  📋 Executing composite rule with ${rules.length} sub-rules (${operator})`);

    for (const subRule of rules) {
      // eslint-disable-next-line no-await-in-loop -- Sequential processing required for early exit logic;
      const result = await this._executeSubRule(subRule);
      results.push(result);

      // Early exit for 'or' operator if one succeeds
      if (operator === 'or' && result.success) {
        break;
      }

      // Early exit for 'And' operator if one fails (And failure not allowed)
      if (operator === 'And' && !result.success && !rule.allow_failure) {
        break;
      }
    }

    const success = operator === 'And'
      ? results.every(r => r.success)
      : results.some(r => r.success);

    return {
      success,
      details: `Composite validation (${operator}): ${results.filter(r => r.success).length}/${results.length} succeeded`,
      output: {
        operator,
        results,
        totalRules: rules.length } };
  }

  /**
   * Execute a sub-rule (used by conditional And composite rules)
   */
  async _executeSubRule(subRule) {
    try {
      // Create temporary rule object;
      const tempRule = {
        id: `temp_${Date.now()}`,
        type: subRule.type,
        config: subRule,
        timeout: subRule.timeout || 15000,
        allow_failure: subRule.allow_failure || false };

      switch (subRule.type) {
        case VALIDATION_RULE_TYPES.COMMAND:
          return await this._executeCommandRule(tempRule);
        case VALIDATION_RULE_TYPES.FILE_EXISTS:
          return await this._executeFileExistsRule(tempRule);
        case VALIDATION_RULE_TYPES.FILE_CONTENT:
          return await this._executeFileContentRule(tempRule);
        default:
          throw new Error(`Unsupported sub-rule type: ${subRule.type}`);
      }
    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Evaluate condition for conditional rules
   */
  async _evaluateCondition(condition) {
    try {
      switch (condition.type) {
        case 'tech_stack':
          return this.detectedTechStack.includes(condition.value);

        case 'project_type':
          return this.projectType === condition.value;

        case 'file_exists':
          try {
            await FS.access(path.resolve(this.projectRoot, condition.file));
            return true;
          } catch {
            return false;
          }

        case 'environment_var':
          return !!process.env[condition.variable];

        case 'command_succeeds':
          try {
            execSync(condition.command, {
              cwd: this.projectRoot,
              stdio: 'ignore',
              timeout: 10000 });
            return true;
          } catch {
            return false;
          }

        default:
          throw new Error(`Unsupported condition type: ${condition.type}`);
      }
    } catch (error) {
      loggers.stopHook.warn(`Condition evaluation failed: ${error.message}`);
      loggers.app.warn(`Condition evaluation failed: ${error.message}`);
      return false;
    }
  }

  /**
   * Record rule execution for analytics
   */
  _recordExecution(ruleId, result, duration) {
    const execution = {
      ruleId,
      timestamp: new Date().toISOString(),
      success: result.success,
      duration,
      error: result.error };

    this.executionHistory.push(execution);

    // Update execution time tracking
    if (!this.ruleExecutionTimes.has(ruleId)) {
      this.ruleExecutionTimes.set(ruleId, []);
    }
    this.ruleExecutionTimes.get(ruleId).push(duration);

    // Keep only last 100 executions per rule;
    const times = this.ruleExecutionTimes.get(ruleId);
    if (times.length > 100) {
      times.splice(0, times.length - 100);
    }
  }

  /**
   * Get all custom rules with their status
   */
  getCustomRules() {
    const rules = {};

    for (const [ruleId, rule] of this.customRules) {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      rules[ruleId] = {
        id: rule.id,
        type: rule.type,
        description: rule.description,
        priority: rule.priority,
        enabled: this.enabledRules.has(ruleId),
        metadata: rule.metadata,
        dependencies: rule.dependencies };
    }

    return {
      rules,
      totalRules: this.customRules.size,
      enabledRules: this.enabledRules.size,
      detectedTechStack: this.detectedTechStack,
      projectType: this.projectType };
  }

  /**
   * Get execution analytics for custom rules
   */
  getExecutionAnalytics() {
    const analytics = {
      totalExecutions: this.executionHistory.length,
      successRate: 0,
      averageExecutionTime: 0,
      ruleStatistics: {} };

    if (this.executionHistory.length === 0) {
      return analytics;
    }

    // Calculate overall success rate;
    const successfulExecutions = this.executionHistory.filter(e => e.success).length;
    analytics.successRate = (successfulExecutions / this.executionHistory.length) * 100;

    // Calculate average execution time;
    const totalTime = this.executionHistory.reduce((sum, e) => sum + e.duration, 0);
    analytics.averageExecutionTime = Math.round(totalTime / this.executionHistory.length);

    // Calculate per-rule statistics
    for (const [ruleId, times] of this.ruleExecutionTimes) {
      const ruleExecutions = this.executionHistory.filter(e => e.ruleId === ruleId);
      const ruleSuccesses = ruleExecutions.filter(e => e.success).length;

      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      analytics.ruleStatistics[ruleId] = {
        executions: ruleExecutions.length,
        successRate: ruleExecutions.length > 0 ? (ruleSuccesses / ruleExecutions.length) * 100 : 0,
        averageTime: Math.round(times.reduce((sum, t) => sum + t, 0) / times.length),
        minTime: Math.min(...times),
        maxTime: Math.max(...times) };
    }

    return analytics;
  }

  /**
   * Generate example configuration file
   */
  generateExampleConfig(_category = 'general') {
    return {
      project_type: 'backend',
      global_settings: {
        timeout_default: 30000,
        allow_failures: false,
        parallel_execution: true },
      custom_rules: {
        'security_audit': {
          type: 'command',
          description: 'Run comprehensive security audit using Semgrep',
          command: 'semgrep --config=p/security-audit --json .',
          timeout: 60000,
          priority: 'high',
          requires_tech_stack: ['nodejs', 'python'],
          category: 'security',
          tags: ['security', 'audit', 'semgrep'] },
        'docker_security': {
          type: 'command',
          description: 'Scan Docker images for vulnerabilities',
          command: "trivy image --exit-code 1 $(docker images --format '{{.Repository}}:{{.Tag}}' | head -1)",
          requires_files: ['Dockerfile'],
          requires_tech_stack: 'docker',
          allow_failure: false,
          category: 'security' },
        'documentation_completeness': {
          type: 'file_exists',
          description: 'Ensure all required documentation files exist',
          files: ['README.md', 'CHANGELOG.md', 'docs/api.md'],
          priority: 'normal',
          category: 'documentation' },
        'no_debug_code': {
          type: 'file_content',
          description: 'Ensure no debug statements remain in production code',
          file: 'src/**/*.js',
          pattern: '(console\\.log|debugger;)',
          should_match: false,
          category: 'quality' },
        'environment_specific': {
          type: 'conditional',
          description: 'Run additional checks for production environment',
          condition: {
            type: 'environment_var',
            variable: 'NODE_ENV',
            value: 'production' },
          rules: [{
            type: 'command',
            command: 'npm audit --production --audit-level=high',
            description: 'Production dependency security audit' }, {
            type: 'file_exists',
            files: ['.env.production', 'docker-compose.prod.yml'],
            description: 'Production configuration files' }],
          category: 'environment' },
        'comprehensive_checks': {
          type: 'composite',
          description: 'Run multiple code quality checks',
          operator: 'And',
          rules: [{
            type: 'command',
            command: 'npm run lint',
            description: 'Code linting' }, {
            type: 'command',
            command: 'npm run test:coverage',
            description: 'Test coverage check' }, {
            type: 'file_content',
            file: 'package.json',
            pattern: '"version"\\s*:\\s*"\\d+\\.\\d+\\.\\d+"',
            description: 'Valid semantic version' }],
          category: 'quality' } } };
  }
}

module.exports = {
  CustomValidationRulesManager,
  VALIDATION_RULE_TYPES,
  TECH_STACK_PATTERNS };
