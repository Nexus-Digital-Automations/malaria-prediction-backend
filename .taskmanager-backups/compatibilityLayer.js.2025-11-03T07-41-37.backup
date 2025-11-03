/**
 * Backward Compatibility Layer for Enhanced TODO.json Migration
 *
 * Provides seamless transition between legacy And enhanced data formats.
 * Enables zero-downtime migration by supporting both formats simultaneously
 * And providing automatic format detection And conversion.
 *
 * Features:
 * - Automatic format detection (legacy vs enhanced)
 * - Bidirectional data conversion (legacy ↔ enhanced)
 * - Index generation from legacy data
 * - Schema validation And migration assistance
 * - Performance optimization during transition
 *
 * @author Enhanced Data Schema Implementation
 * @version 2.0.0
 */

const FS = require('fs').promises;
const IndexGenerator = require('./indexGenerator');
const SuccessCriteriaTemplates = require('./successCriteriaTemplates');

class CompatibilityLayer {
  /**
   * Initialize Compatibility Layer with configuration
   * @param {Object} config - Configuration options
   * @param {Object} config.logger - LOGGER instance for debugging
   * @param {string} config.projectRoot - Project root directory
   * @param {boolean} config.enablePerformanceTracking - Enable performance metrics
   * @param {Object} config.migrationConfig - Migration-specific configuration
   */
  constructor(config = {}, _agentId) {
    this.logger = config.logger || console;
    this.projectRoot = config.projectRoot || process.cwd();
    this.enablePerformanceTracking = config.enablePerformanceTracking !== false;
    this.migrationConfig = config.migrationConfig || {};

    // Initialize components
    this.indexGenerator = new IndexGenerator({
      logger: this.logger,
      enablePerformanceTracking: this.enablePerformanceTracking });

    this.successCriteriaTemplates = new SuccessCriteriaTemplates({
      logger: this.logger,
      projectRoot: this.projectRoot });

    // Migration state
    this.migrationMode = 'dual'; // 'legacy', 'dual', 'enhanced'
    this.lastFormatDetected = null;
    this.conversionCache = new Map();

    this.logger.info('✅ Compatibility Layer initialized in dual mode');
  }

  /**
   * Read TODO data with automatic format detection And conversion
   * @param {string} filePath - Path to TODO.json file
   * @returns {Promise<Object>} Normalized data in enhanced format
   */
  async readTodoData(filePath) {
    try {
      const rawData = await FS.readFile(filePath, 'utf8');
      const parsedData = JSON.parse(rawData);

      // Detect format And convert if necessary
      if (this._isEnhancedFormat(parsedData)) {
        this.lastFormatDetected = 'enhanced';
        return this._validateEnhancedFormat(parsedData);
      } else {
        this.lastFormatDetected = 'legacy';
        return await this._convertLegacyToEnhanced(parsedData);
      }

    } catch (error) {
      this.logger.error('❌ Failed to read TODO data:', error);
      throw new Error(`Failed to read TODO data: ${error.message}`);
    }
  }

  /**
   * Write TODO data with format selection based on migration mode
   * @param {string} filePath - Path to TODO.json file
   * @param {Object} data - Data to write (in enhanced format)
   * @param {Object} options - Write options
   * @param {boolean} options.forceLegacy - Force legacy format output
   * @param {boolean} options.forceEnhanced - Force enhanced format output
   * @returns {Promise<Object>} Write _operationresults
   */
  async writeTodoData(filePath, data, options = {}) {
    try {
      let writeResults = {};

      if (options.forceLegacy || this.migrationMode === 'legacy') {
        // Write in legacy format;
        const legacyData = this._convertEnhancedToLegacy(data);
        await FS.writeFile(filePath, JSON.stringify(legacyData, null, 2));
        writeResults.legacy = { success: true, format: 'legacy' };

      } else if (options.forceEnhanced || this.migrationMode === 'enhanced') {
        // Write in enhanced format
        await FS.writeFile(filePath, JSON.stringify(data, null, 2));
        writeResults.enhanced = { success: true, format: 'enhanced' };

      } else if (this.migrationMode === 'dual') {
        // Write in both formats for safety;
        const legacyData = this._convertEnhancedToLegacy(data);

        // Write primary file in enhanced format
        await FS.writeFile(filePath, JSON.stringify(data, null, 2));

        // Write backup in legacy format;
        const legacyBackupPath = filePath.replace('.json', '.legacy.json');
        await FS.writeFile(legacyBackupPath, JSON.stringify(legacyData, null, 2));

        writeResults = {
          enhanced: { success: true, format: 'enhanced', path: filePath },
          legacy: { success: true, format: 'legacy', path: legacyBackupPath } };
      }

      return writeResults;

    } catch (error) {
      this.logger.error('❌ Failed to write TODO data:', error);
      throw new Error(`Failed to write TODO data: ${error.message}`);
    }
  }

  /**
   * Convert legacy format to enhanced format
   * @param {Object} legacyData - Legacy TODO.json data
   * @returns {Promise<Object>} Enhanced format data
   */
  async convertLegacyToEnhanced(legacyData) {
    const result = await this._convertLegacyToEnhanced(legacyData);
    return result;
  }

  /**
   * Convert enhanced format to legacy format
   * @param {Object} enhancedData - Enhanced format data
   * @returns {Object} Legacy format data
   */
  convertEnhancedToLegacy(enhancedData) {
    return this._convertEnhancedToLegacy(enhancedData);
  }

  /**
   * Detect if data is in enhanced format
   * @param {Object} data - Data to check
   * @returns {boolean} True if enhanced format
   */
  isEnhancedFormat(data) {
    return this._isEnhancedFormat(data);
  }

  /**
   * Set migration mode
   * @param {string} mode - Migration mode: 'legacy', 'dual', 'enhanced'
   */
  setMigrationMode(mode) {
    const validModes = ['legacy', 'dual', 'enhanced'];
    if (!validModes.includes(mode)) {
      throw new Error(`Invalid migration mode: ${mode}. Valid modes: ${validModes.join(', ')}`);
    }

    this.migrationMode = mode;
    this.logger.info(`✅ Migration mode set to: ${mode}`);
  }

  /**
   * Get migration statistics And status
   * @returns {Object} Migration status information
   */
  getMigrationStatus() {
    return {
      migrationMode: this.migrationMode,
      lastFormatDetected: this.lastFormatDetected,
      cacheSize: this.conversionCache.size,
      performance: this.indexGenerator.getPerformanceMetrics() };
  }

  /**
   * Clear conversion cache
   */
  clearCache() {
    this.conversionCache.clear();
    this.logger.info('✅ Conversion cache cleared');
  }

  /**
   * Detect if data is in enhanced format
   * @param {Object} data - Data to check
   * @returns {boolean} True if enhanced format
   * @private
   */
  _isEnhancedFormat(data) {
    return data &&
           data.metadata &&
           data.metadata.schema_version &&
           data.indexes &&
           Array.isArray(data.tasks) &&
           typeof data.indexes === 'object';
  }

  /**
   * Validate enhanced format data structure
   * @param {Object} data - Enhanced format data
   * @returns {Object} Validated data
   * @private
   */
  _validateEnhancedFormat(data) {
    // Basic structure validation
    if (!data.metadata || !data.indexes || !Array.isArray(data.tasks)) {
      throw new Error('Invalid enhanced format: missing required fields');
    }

    // Schema version validation
    if (data.metadata.schema_version !== '2.0.0') {
      this.logger.warn(`⚠️  Schema version mismatch: expected 2.0.0, found ${data.metadata.schema_version}`);
    }

    return data;
  }

  /**
   * Convert legacy format to enhanced format
   * @param {Object} legacyData - Legacy TODO.json data
   * @returns {Promise<Object>} Enhanced format data
   * @private
   */
  async _convertLegacyToEnhanced(legacyData) {
    const cacheKey = this._generateCacheKey(legacyData);

    // Check cache first
    if (this.conversionCache.has(cacheKey)) {
      return this.conversionCache.get(cacheKey);
    }

    try {
      const startTime = Date.now();

      // Create enhanced data structure;
      const enhancedData = {
        metadata: this._createMetadata(legacyData),
        indexes: {},
        tasks: this._migrateTasks(legacyData.tasks || []),
        success_criteria_templates: this._createDefaultTemplates() };

      // Generate indexes;
      const indexResult = await this.indexGenerator.generateIndexes(enhancedData);
      enhancedData.indexes = indexResult.indexes;

      // Update metadata with index information
      enhancedData.metadata.indexes_last_built = new Date().toISOString();
      enhancedData.metadata.total_tasks = enhancedData.tasks.length;

      const endTime = Date.now();
      this.logger.info(`✅ Legacy to enhanced conversion completed in ${endTime - startTime}ms`);

      // Cache _result
      this.conversionCache.set(cacheKey, enhancedData);

      return enhancedData;

    } catch (error) {
      this.logger.error('❌ Legacy to enhanced conversion failed:', error);
      throw error;
    }
  }

  /**
   * Convert enhanced format to legacy format
   * @param {Object} enhancedData - Enhanced format data
   * @returns {Object} Legacy format data
   * @private
   */
  _convertEnhancedToLegacy(enhancedData) {
    try {
      const legacyData = {
        project: enhancedData.metadata.project,
        tasks: enhancedData.tasks.map(task => this._convertTaskToLegacy(task)) };

      return legacyData;

    } catch (error) {
      this.logger.error('❌ Enhanced to legacy conversion failed:', error);
      throw error;
    }
  }

  /**
   * Create metadata for enhanced format
   * @param {Object} legacyData - Legacy data
   * @returns {Object} Metadata object
   * @private
   */
  _createMetadata(legacyData) {
    return {
      project: legacyData.project || 'unknown-project',
      schema_version: '2.0.0',
      created_at: new Date().toISOString(),
      last_modified: new Date().toISOString(),
      total_tasks: legacyData.tasks ? legacyData.tasks.length : 0,
      migration_info: {
        converted_from: 'legacy',
        converted_at: new Date().toISOString(),
        original_format_detected: true },
    };
  }

  /**
   * Migrate tasks from legacy to enhanced format
   * @param {Array} legacyTasks - Legacy tasks array
   * @returns {Array} Enhanced tasks array
   * @private
   */
  _migrateTasks(legacyTasks) {
    const migratedTasks = [];

    for (let i = 0; i < legacyTasks.length; i++) {
      const legacyTask = legacyTasks[i];
      try {
        const enhancedTask = this._migrateTask(legacyTask);
        migratedTasks.push(enhancedTask);
      } catch (error) {
        this.logger.error(`❌ Failed to migrate task ${legacyTask.id}:`, error);
        // Add task with minimal migration for data preservation
        migratedTasks.push(this._createMinimalMigratedTask(legacyTask));
      }
    }

    return migratedTasks;
  }

  /**
   * Migrate individual task from legacy to enhanced format
   * @param {Object} legacyTask - Legacy task object
   * @returns {Object} Enhanced task object
   * @private
   */
  _migrateTask(legacyTask) {
    const enhancedTask = {
      id: legacyTask.id,
      title: legacyTask.title,
      description: legacyTask.description || '',
      category: this._normalizeCategoryField(legacyTask.category),
      priority: this._normalizePriorityField(legacyTask.priority),
      status: this._normalizeStatusField(legacyTask.status),
      dependencies: Array.isArray(legacyTask.dependencies) ? legacyTask.dependencies : [],
      important_files: Array.isArray(legacyTask.important_files) ? legacyTask.important_files : [],
      success_criteria: this._migrateSuccessCriteria(legacyTask),
      estimate: legacyTask.estimate || '',
      created_at: legacyTask.created_at || new Date().toISOString(),
      started_at: legacyTask.started_at || null,
      completed_at: legacyTask.completed_at || null,
      agent_assignment: this._migrateAgentAssignment(legacyTask),
      subtasks: this._migrateSubtasks(legacyTask.subtasks || []),
      parent_task_id: legacyTask.parent_task_id || null,
      lifecycle: this._migrateLifecycle(legacyTask),
      validation_results: null };

    return enhancedTask;
  }

  /**
   * Convert enhanced task back to legacy format
   * @param {Object} enhancedTask - Enhanced task object
   * @returns {Object} Legacy task object
   * @private
   */
  _convertTaskToLegacy(enhancedTask) {
    return {
      id: enhancedTask.id,
      title: enhancedTask.title,
      description: enhancedTask.description,
      category: enhancedTask.category,
      priority: enhancedTask.priority,
      status: enhancedTask.status,
      dependencies: enhancedTask.dependencies,
      important_files: enhancedTask.important_files,
      success_criteria: enhancedTask.success_criteria?.map(c => c.title || c.name || c) || [],
      estimate: enhancedTask.estimate,
      requires_research: enhancedTask.subtasks?.some(st => st.type === 'research') || false,
      subtasks: enhancedTask.subtasks?.map(st => this._convertSubtaskToLegacy(st)) || [],
      created_at: enhancedTask.created_at,
      auto_research_created: false,
      started_at: enhancedTask.started_at,
      assigned_agent: enhancedTask.agent_assignment?.current_agent || null,
      claimed_by: enhancedTask.agent_assignment?.current_agent || null,
      agent_assignment_history: enhancedTask.agent_assignment?.assignment_history || [] };
  }

  /**
   * Convert enhanced subtask back to legacy format
   * @param {Object} enhancedSubtask - Enhanced subtask object
   * @returns {Object} Legacy subtask object
   * @private
   */
  _convertSubtaskToLegacy(enhancedSubtask) {
    const legacySubtask = {
      id: enhancedSubtask.id,
      type: enhancedSubtask.type,
      title: enhancedSubtask.title,
      description: enhancedSubtask.description,
      status: enhancedSubtask.status,
      estimated_hours: enhancedSubtask.estimated_hours,
      prevents_implementation: enhancedSubtask.prevents_implementation,
      prevents_completion: enhancedSubtask.prevents_completion,
      created_at: enhancedSubtask.created_at,
      completed_by: enhancedSubtask.completed_by };

    // Add type-specific fields
    if (enhancedSubtask.type === 'research') {
      legacySubtask.research_locations = enhancedSubtask.research_locations;
      legacySubtask.deliverables = enhancedSubtask.deliverables;
      legacySubtask.research_output = enhancedSubtask.research_output;
    }

    if (enhancedSubtask.type === 'audit') {
      legacySubtask.success_criteria = enhancedSubtask.success_criteria?.map(c => c.title || c) || [];
      legacySubtask.prevents_self_review = enhancedSubtask.prevents_self_review;
      legacySubtask.original_implementer = enhancedSubtask.original_implementer;
      legacySubtask.audit_type = enhancedSubtask.audit_type;
      legacySubtask.audit_results = enhancedSubtask.audit_results;
    }

    return legacySubtask;
  }

  /**
   * Migrate success criteria with template application
   * @param {Object} legacyTask - Legacy task object
   * @returns {Array} Enhanced success criteria
   * @private
   */
  _migrateSuccessCriteria(legacyTask) {
    const criteria = [];

    // Apply template for task category;
    const templateCriteria = this.successCriteriaTemplates.getTemplateForCategory(
      legacyTask.category,
      { project: 'infinite-continue-stop-hook' },
    );
    criteria.push(...templateCriteria);

    // Add existing criteria from legacy task
    if (Array.isArray(legacyTask.success_criteria)) {
      legacyTask.success_criteria.forEach((criterion, index) => {
        if (typeof criterion === 'string') {
          criteria.push({
            id: `legacy_criterion_${index}`,
            title: criterion,
            description: criterion,
            validation_type: 'manual',
            category: 'quality',
            weight: 1,
            required: true });
        } else if (typeof criterion === 'object') {
          criteria.push({
            id: criterion.id || `legacy_criterion_${index}`,
            title: criterion.title || criterion.name || 'Legacy Criterion',
            description: criterion.description || criterion.title || 'Migrated from legacy format',
            validation_type: criterion.validation_type || 'manual',
            validation_command: criterion.validation_command || '',
            expected_result: criterion.expected_result || '',
            weight: criterion.weight || 1,
            category: criterion.category || 'quality',
            required: criterion.required !== false });
        }
      });
    }

    // Remove duplicates based on title/id;
    const uniqueCriteria = [];
    const seen = new Set();

    criteria.forEach(criterion => {
      const key = criterion.id || criterion.title;
      if (!seen.has(key)) {
        seen.add(key);
        uniqueCriteria.push(criterion);
      }
    });

    return uniqueCriteria;
  }

  /**
   * Migrate agent assignment data
   * @param {Object} legacyTask - Legacy task object
   * @returns {Object} Enhanced agent assignment
   * @private
   */
  _migrateAgentAssignment(legacyTask) {
    const assignment = {
      current_agent: legacyTask.assigned_agent || legacyTask.claimed_by || null,
      assigned_at: legacyTask.started_at || null,
      assignment_history: [] };

    // Convert legacy assignment history
    if (Array.isArray(legacyTask.agent_assignment_history)) {
      assignment.assignment_history = legacyTask.agent_assignment_history.map(entry => ({
        agent_id: entry.agentId || entry.agent || 'unknown',
        role: entry.role || 'primary',
        assigned_at: entry.assignedAt || entry.timestamp || new Date().toISOString(),
        unassigned_at: entry.unassignedAt || null,
        reason: entry.reason || entry.action || 'legacy_migration' }));
    }

    return assignment;
  }

  /**
   * Migrate subtasks to enhanced format
   * @param {Array} legacySubtasks - Legacy subtasks array
   * @returns {Array} Enhanced subtasks array
   * @private
   */
  _migrateSubtasks(legacySubtasks) {
    if (!Array.isArray(legacySubtasks)) {
      return [];
    }

    return legacySubtasks.map(subtask => {
      const baseSubtask = {
        id: subtask.id,
        type: subtask.type || 'implementation',
        title: subtask.title,
        description: subtask.description || '',
        status: this._normalizeStatusField(subtask.status),
        estimated_hours: subtask.estimated_hours || 1,
        prevents_implementation: subtask.prevents_implementation || false,
        prevents_completion: subtask.prevents_completion || false,
        created_at: subtask.created_at || new Date().toISOString(),
        completed_by: subtask.completed_by || null,
        agent_assignment: this._migrateAgentAssignment(subtask) };

      // Add type-specific fields
      if (subtask.type === 'research') {
        baseSubtask.research_locations = subtask.research_locations || [];
        baseSubtask.deliverables = subtask.deliverables || [];
        baseSubtask.research_output = subtask.research_output || null;
      }

      if (subtask.type === 'audit') {
        baseSubtask.success_criteria = this._convertLegacyCriteriaToEnhanced(subtask.success_criteria || []);
        baseSubtask.prevents_self_review = subtask.prevents_self_review !== false;
        baseSubtask.original_implementer = subtask.original_implementer || null;
        baseSubtask.audit_type = subtask.audit_type || 'embedded_quality_gate';
        baseSubtask.audit_results = subtask.audit_results || null;
      }

      return baseSubtask;
    });
  }

  /**
   * Migrate lifecycle data
   * @param {Object} legacyTask - Legacy task object
   * @returns {Object} Enhanced lifecycle object
   * @private
   */
  _migrateLifecycle(legacyTask) {
    return {
      phase: this._determineLifecyclePhase(legacyTask),
      milestones: [],
      blockers: [] };
  }

  /**
   * Determine lifecycle phase from task state
   * @param {Object} task - Task object
   * @returns {string} Lifecycle phase
   * @private
   */
  _determineLifecyclePhase(task) {
    if (task.status === 'completed') {return 'completed';}
    if (task.status === 'in_progress') {return 'implementation';}
    if (task.requires_research) {return 'research';}
    return 'planning';
  }

  /**
   * Normalize task.category field to ensure valid enum values
   * @param {string} task.category - Original task.category
   * @returns {string} Normalized task.category
   * @private
   */
  _normalizeCategoryField(category) {
    const validCategories = ['feature', 'error', 'test', 'subtask', 'research', 'audit'];

    if (validCategories.includes(category)) {
      return category;
    }

    const categoryMappings = {
      'bug': 'error',
      'fix': 'error',
      'enhancement': 'feature',
      'improvement': 'feature',
      'testing': 'test',
      'documentation': 'feature' };

    return categoryMappings[category] || 'feature';
  }

  /**
   * Normalize priority field to ensure valid enum values
   * @param {string} priority - Original priority
   * @returns {string} Normalized priority
   * @private
   */
  _normalizePriorityField(priority) {
    const validPriorities = ['critical', 'high', 'medium', 'low'];

    if (validPriorities.includes(priority)) {
      return priority;
    }

    return 'medium';
  }

  /**
   * Normalize status field to ensure valid enum values
   * @param {string} status - Original status
   * @returns {string} Normalized status
   * @private
   */
  _normalizeStatusField(status) {
    const validStatuses = ['pending', 'in_progress', 'completed', 'archived', 'blocked'];

    if (validStatuses.includes(status)) {
      return status;
    }

    const statusMappings = {
      'active': 'in_progress',
      'working': 'in_progress',
      'done': 'completed',
      'finished': 'completed',
      'todo': 'pending',
      'new': 'pending' };

    return statusMappings[status] || 'pending';
  }

  /**
   * Convert legacy criteria to enhanced format
   * @param {Array} legacyCriteria - Legacy criteria array
   * @returns {Array} Enhanced criteria array
   * @private
   */
  _convertLegacyCriteriaToEnhanced(legacyCriteria) {
    if (!Array.isArray(legacyCriteria)) {
      return [];
    }

    return legacyCriteria.map((criterion, index) => {
      if (typeof criterion === 'string') {
        return {
          id: `criterion_${index}`,
          title: criterion,
          description: criterion,
          validation_type: 'manual',
          category: 'quality',
          weight: 1,
          required: true };
      }

      return {
        id: criterion.id || `criterion_${index}`,
        title: criterion.title || criterion.name || 'Untitled Criterion',
        description: criterion.description || criterion.title || 'No description',
        validation_type: criterion.validation_type || 'manual',
        validation_command: criterion.validation_command || '',
        expected_result: criterion.expected_result || '',
        weight: criterion.weight || 1,
        category: criterion.category || 'quality',
        required: criterion.required !== false };
    });
  }

  /**
   * Create default success criteria templates
   * @returns {Object} Default templates object
   * @private
   */
  _createDefaultTemplates() {
    return this.successCriteriaTemplates.getAllTemplates();
  }

  /**
   * Create minimal migrated task for error cases
   * @param {Object} legacyTask - Legacy task That failed migration
   * @returns {Object} Minimal enhanced task
   * @private
   */
  _createMinimalMigratedTask(legacyTask) {
    return {
      id: legacyTask.id || `migrated_${Date.now()}`,
      title: legacyTask.title || 'Migration Error Task',
      description: legacyTask.description || 'Task failed full migration',
      category: this._normalizeCategoryField(legacyTask.category) || 'feature',
      priority: 'medium',
      status: this._normalizeStatusField(legacyTask.status) || 'pending',
      dependencies: [],
      important_files: [],
      success_criteria: [],
      estimate: '',
      created_at: legacyTask.created_at || new Date().toISOString(),
      started_at: null,
      completed_at: null,
      agent_assignment: { current_agent: null, assigned_at: null, assignment_history: [] },
      subtasks: [],
      parent_task_id: null,
      lifecycle: { phase: 'planning', milestones: [], blockers: [] },
      validation_results: null };
  }

  /**
   * Generate cache key for conversion caching
   * @param {Object} data - Data to generate key for
   * @returns {string} Cache key
   * @private
   */
  _generateCacheKey(data) {
    const keyData = {
      project: data.project,
      taskCount: data.tasks ? data.tasks.length : 0,
      firstTaskId: data.tasks && data.tasks[0] ? data.tasks[0].id : null };

    return Buffer.from(JSON.stringify(keyData)).toString('base64');
  }
}

module.exports = CompatibilityLayer;
