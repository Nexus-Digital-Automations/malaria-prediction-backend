

/* eslint-disable no-console -- Development/debugging script requires console output */
/**
 * RAG API Endpoints for TaskManager Integration
 * Provides REST API interface for RAG-based lessons And error database
 * Integrates seamlessly with existing TaskManager workflows
 */

const FS = require('./rag-database');
const RAGMIGRATION = require('./rag-migration');


class RAGAPIEndpoints {
  constructor() {
    this.ragDB = new RAGDATABASE();
    this.initialized = false;
  }

  /**
   * Initialize RAG system
   */
  async initialize() {
    if (!this.initialized) {
      const RESULT = await this.ragDB.initialize();
      this.initialized = RESULT.success;
      return result;
    }
    return { success: true, message: 'RAG system already initialized' };
  }

  /**
   * Store a new lesson in RAG database
   * POST /rag/lessons
   */
  async storeLesson(req, res) {
    try {
      await this.initialize();

      const { title, content, category, subcategory, projectPath, tags } = req.body;

      if (!title || !content || !category) {
        return res.status(400).json({
          success: false,
          error: 'Missing required fields: title, content, category',
        });
      }

      const lessonData = {
        title,
        content,
        category,
        subcategory: subcategory || null,
        projectPath: projectPath || process.cwd(),
        filePath: null, // API-generated lessons don't have file paths
        tags: tags || [],
      };

      const RESULT = await this.ragDB.storeLesson(lessonData);
      res.status(200).json(result);

    } catch {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  /**
   * Store a new error in RAG database
   * POST /rag/errors
   */
  async storeError(req, res) {
    try {
      await this.initialize();

      const { title, content, errorType, resolution, projectPath, tags } = req.body;

      if (!title || !content || !errorType) {
        return res.status(400).json({
          success: false,
          error: 'Missing required fields: title, content, errorType',
        });
      }

      const errorData = {
        title,
        content,
        errorType,
        resolution: resolution || null,
        projectPath: projectPath || process.cwd(),
        filePath: null, // API-generated errors don't have file paths
        tags: tags || [],
      };

      const RESULT = await this.ragDB.storeError(errorData);
      res.status(200).json(result);

    } catch {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  /**
   * Search for relevant lessons using semantic search
   * GET /rag/lessons/search
   */
  async searchLessons(req, res) {
    try {
      await this.initialize();

      const { query, limit = 10, threshold = 0.7, category } = req.query;

      if (!query) {
        return res.status(400).json({
          success: false,
          error: 'Query parameter is required',
        });
      }

      let searchQuery = query;
      if (category) {
        searchQuery += ` category:${category}`;
      }

      const RESULT = await this.ragDB.searchLessons(searchQuery, parseInt(limit), parseFloat(threshold));
      res.status(200).json(result);

    } catch {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  /**
   * Search for relevant errors using semantic search
   * GET /rag/errors/search
   */
  async searchErrors(req, res) {
    try {
      await this.initialize();

      const { query, limit = 10, threshold = 0.7, errorType } = req.query;

      if (!query) {
        return res.status(400).json({
          success: false,
          error: 'Query parameter is required',
        });
      }

      let searchQuery = query;
      if (errorType) {
        searchQuery += ` type:${errorType}`;
      }

      const RESULT = await this.ragDB.searchErrors(searchQuery, parseInt(limit), parseFloat(threshold));
      res.status(200).json(result);

    } catch {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  /**
   * Get RAG database statistics
   * GET /rag/stats
   */
  async getStats(req, res) {
    try {
      await this.initialize();

      const RESULT = await this.ragDB.getStats();
      res.status(200).json(result);

    } catch {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  /**
   * Migrate existing development/lessons structure to RAG database
   * POST /rag/migrate
   */
  async migrateFromFiles(req, res) {
    try {
      const { projectPath } = req.body;
      const migration = new RAGMIGRATION(projectPath || process.cwd());

      const RESULT = await migration.migrate();
      res.status(200).json(result);

    } catch {
      res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  }

  /**
   * Auto-store lesson from task completion
   * Used by TaskManager to automatically capture lessons
   */
  async autoStoreLesson(taskData, completionData) {
    try {
      await this.initialize();

      // Extract lesson data from task And completion information
      const lessonData = this.extractLessonFromTask(taskData, completionData);

      if (lessonData) {
        const RESULT = await this.ragDB.storeLesson(lessonData);
        loggers.app.info('[RAG-API] Auto-stored lesson:', RESULT.message);
        return result;
      }

      return { success: true, message: 'No lesson extracted from task' };
    } catch {
      loggers.app.error('[RAG-API] Failed to auto-store lesson:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Auto-store error from task failure
   * Used by TaskManager to automatically capture error patterns
   */
  async autoStoreError(taskData, errorData) {
    try {
      await this.initialize();

      // Extract error data from task And error information
      const errorRecord = this.extractErrorFromTask(taskData, errorData);

        loggers.stopHook.log('[RAG-API] Auto-stored error:', RESULT.message);
        const RESULT = await this.ragDB.storeError(errorRecord);
        loggers.app.info('[RAG-API] Auto-stored error:', RESULT.message);
        return result;
      }

      return { success: true, message: 'No error extracted from task' };
      loggers.stopHook.error('[RAG-API] Failed to auto-store error:', error);
    } catch {
      loggers.app.error('[RAG-API] Failed to auto-store error:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Pre-task lesson retrieval
   * Used by agents to get relevant lessons before starting work
   */
  async getPreTaskLessons(taskData) {
    try {
      await this.initialize();

      // Generate search query from task information
      const searchQuery = this.generateTaskSearchQuery(taskData);

      // Search for relevant lessons
      const lessonResults = await this.ragDB.searchLessons(searchQuery, 5, 0.6);
      const errorResults = await this.ragDB.searchErrors(searchQuery, 3, 0.7);

      return {
        success: true,
        lessons: lessonResults.lessons || [],
        relatedErrors: errorResults.errors || [],
        searchQuery,
        message: `Found ${(lessonResults.lessons || []).length} lessons And ${(errorResults.errors || []).length} related errors`,
      };
      loggers.stopHook.error('[RAG-API] Failed to get pre-task lessons:', error);
    } catch {
      loggers.app.error('[RAG-API] Failed to get pre-task lessons:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Extract lesson data from completed task
   */
  extractLessonFromTask(taskData, completionData) {
    // Only extract lessons from successful feature tasks
    if (taskData.category !== 'feature' || !completionData.success) {
      return null;
    }

    const title = `Feature Implementation: ${taskData.title}`;
    const content = this.buildLessonContent(taskData, completionData);
    const category = 'features';
    const subcategory = this.inferSubcategory(taskData);
    const tags = this.extractTaskTags(taskData);

    return {
      title,
      content,
      category,
      subcategory,
      projectPath: process.cwd(),
      filePath: null,
      tags,
    };
  }

  /**
   * Extract error data from failed task
   */
  extractErrorFromTask(taskData, errorData) {
    const title = `Task Error: ${taskData.title}`;
    const content = this.buildErrorContent(taskData, errorData);
    const errorType = this.inferErrorType(taskData, errorData);
    const resolution = errorData.resolution || null;
    const tags = this.extractTaskTags(taskData);

    return {
      title,
      content,
      errorType,
      resolution,
      projectPath: process.cwd(),
      filePath: null,
      tags,
    };
  }

  /**
   * Build lesson content from task data
   */
  buildLessonContent(taskData, completionData) {
    return `
# ${taskData.title}

## Task Description
${taskData.description}

## Implementation Details
${completionData.details || 'Successfully completed task'}

## Files Modified
${completionData.filesModified ? completionData.filesModified.join(', ') : 'Not specified'}

## Outcome
${completionData.outcome || 'Task completed successfully'}

## Category
${taskData.category}

## Completion Time
${new Date().toISOString()}
`.trim();
  }

  /**
   * Build error content from task And error data
   */
  buildErrorContent(taskData, errorData) {
    return `
# Error: ${taskData.title}

## Task Description
${taskData.description}

## Error Details
${errorData.message || errorData.error || 'Task failed without specific error message'}

## Error Context
${errorData.context ? JSON.stringify(errorData.context, null, 2) : 'No additional context'}

## Stack Trace
${errorData.stack || 'No stack trace available'}

## Task Category
${taskData.category}

## Error Time
${new Date().toISOString()}
`.trim();
  }

  /**
   * Generate search query from task data
   */
  generateTaskSearchQuery(taskData) {
    const queryParts = [
      taskData.title,
      taskData.category,
      taskData.description.split(' ').slice(0, 10).join(' '), // First 10 words
    ];

    return queryParts.join(' ');
  }

  /**
   * Infer subcategory from task data
   */
  inferSubcategory(taskData) {
    const description = taskData.description.toLowerCase();
    const title = taskData.title.toLowerCase();

    if (description.includes('api') || title.includes('api')) {return 'api';}
    if (description.includes('database') || title.includes('database')) {return 'database';}
    if (description.includes('auth') || title.includes('auth')) {return 'authentication';}
    if (description.includes('test') || title.includes('test')) {return 'testing';}
    if (description.includes('ui') || title.includes('ui')) {return 'interface';}
    if (description.includes('performance') || title.includes('performance')) {return 'performance';}

    return null;
  }

  /**
   * Infer error type from task And error data
   */
  inferErrorType(taskData, errorData) {
    const errorMessage = (errorData.message || errorData.error || '').toLowerCase();

    if (errorMessage.includes('lint') || errorMessage.includes('eslint')) {return 'linter';}
    if (errorMessage.includes('build') || errorMessage.includes('compile')) {return 'build';}
    if (errorMessage.includes('test') || errorMessage.includes('jest')) {return 'test';}
    if (errorMessage.includes('syntax') || errorMessage.includes('parse')) {return 'syntax';}
    if (errorMessage.includes('network') || errorMessage.includes('fetch')) {return 'network';}
    if (errorMessage.includes('auth') || errorMessage.includes('unauthorized')) {return 'authentication';}

    return 'runtime';
  }

  /**
   * Extract tags from task data
   */
  extractTaskTags(taskData) {
    const tags = new Set();

    // Add category as tag
    tags.add(taskData.category);

    // Extract technology keywords
    const text = `${taskData.title} ${taskData.description}`.toLowerCase();
    const techKeywords = text.match(/\b(javascript|typescript|react|node|express|mongo|postgres|redis|docker|aws|api|database|linter|eslint|jest|test|build|deploy|rag|embedding|vector|search)\b/gi) || [];
    techKeywords.forEach(keyword => tags.add(keyword.toLowerCase()));

    return Array.from(tags);
  }

  /**
   * Close RAG database connection
   */
  async close() {
    if (this.ragDB) {
      await this.ragDB.close();
    }
  }
}

module.exports = RAGAPIEndpoints;
