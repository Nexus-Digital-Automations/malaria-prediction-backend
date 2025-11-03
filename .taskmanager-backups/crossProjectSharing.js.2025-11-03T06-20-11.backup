/**
 * Cross-Project Lesson Sharing Module
 * Enables sharing lessons learned across multiple projects with intelligent categorization
 * And relevance scoring for enhanced knowledge reuse And organizational learning
 */

const crypto = require('crypto');

class CrossProjectSharing {
  constructor(ragDatabase) {
    this.ragDB = ragDatabase;
    this.initialized = false;

    // Project categorization scoring weights
    this.relevanceWeights = {
      technology_stack: 0.30,    // Technology/framework similarity
      project_type: 0.25,       // Type similarity (web, mobile, API, etc.)
      domain: 0.20,              // Business domain similarity
      patterns: 0.15,            // Pattern/approach similarity
      keywords: 0.10,             // Keyword matching
    };

    // Default project categories
    this.defaultCategories = {
      technology_stacks: ['javascript', 'python', 'java', 'react', 'node', 'typescript', 'go', 'rust'],
      project_types: ['web_app', 'mobile_app', 'api_service', 'microservice', 'desktop_app', 'cli_tool', 'library'],
      domains: ['ecommerce', 'healthcare', 'finance', 'education', 'entertainment', 'productivity', 'social'],
      patterns: ['mvc', 'microservices', 'serverless', 'monolith', 'spa', 'pwa', 'rest_api', 'graphql'] };
  }

  /**
   * Initialize cross-project sharing system with database tables
   */
  async initialize() {
    try {
      if (this.initialized) {
        return { success: true, message: 'Cross-project sharing already initialized' };
      }

      // Create project_registry table
      await new Promise((resolve, reject) => {
        this.ragDB.db.exec(`
          CREATE TABLE IF NOT EXISTS project_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT UNIQUE NOT NULL,
            project_name TEXT NOT NULL,
            description TEXT,
            technology_stack TEXT,
            project_type TEXT,
            domain TEXT,
            patterns TEXT,
            keywords TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
          )
        `, (error) => {
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });

      // Create project_lessons table (links lessons to projects)
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS project_lessons (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          lesson_id INTEGER NOT NULL,
          project_id TEXT NOT NULL,
          sharing_scope TEXT DEFAULT 'organization',  -- 'private', 'team', 'organization', 'public'
          project_specific_tags TEXT,                 -- JSON array of project-specific tags
          lesson_category TEXT,                       -- Feature, Bug, Pattern, Best Practice, etc.
          applicability_score REAL DEFAULT 1.0,      -- How applicable this lesson is to other projects
          sharing_metadata TEXT,                      -- JSON object for sharing-specific data
          shared_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
        )
      `);

      // Create cross_project_analytics table
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS cross_project_analytics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_project_id TEXT NOT NULL,
          target_project_id TEXT NOT NULL,
          lesson_id INTEGER NOT NULL,
          relevance_score REAL NOT NULL,
          applied_successfully BOOLEAN,
          application_outcome TEXT,           -- JSON object with success metrics
          feedback_score INTEGER,             -- 1-5 rating on lesson usefulness
          feedback_comment TEXT,
          applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
        )
      `);

      // Create sharing_recommendations table
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS sharing_recommendations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          recommendation_id TEXT UNIQUE NOT NULL,
          source_project_id TEXT NOT NULL,
          target_project_id TEXT NOT NULL,
          lesson_id INTEGER NOT NULL,
          relevance_score REAL NOT NULL,
          recommendation_reason TEXT,         -- JSON object explaining why recommended
          status TEXT DEFAULT 'pending',     -- 'pending', 'applied', 'dismissed', 'expired'
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          expires_at DATETIME,
          FOREIGN KEY (lesson_id) REFERENCES lessons (id) ON DELETE CASCADE
        )
      `);

      // Create indexes for performance
      const indexes = [
        'CREATE INDEX IF NOT EXISTS idx_project_lessons_project_id ON project_lessons(project_id)',
        'CREATE INDEX IF NOT EXISTS idx_project_lessons_lesson_id ON project_lessons(lesson_id)',
        'CREATE INDEX IF NOT EXISTS idx_project_lessons_scope ON project_lessons(sharing_scope)',
        'CREATE INDEX IF NOT EXISTS idx_cross_project_source ON cross_project_analytics(source_project_id)',
        'CREATE INDEX IF NOT EXISTS idx_cross_project_target ON cross_project_analytics(target_project_id)',
        'CREATE INDEX IF NOT EXISTS idx_cross_project_score ON cross_project_analytics(relevance_score)',
        'CREATE INDEX IF NOT EXISTS idx_sharing_recommendations_target ON sharing_recommendations(target_project_id)',
        'CREATE INDEX IF NOT EXISTS idx_sharing_recommendations_status ON sharing_recommendations(status)',
        'CREATE INDEX IF NOT EXISTS idx_project_registry_type ON project_registry(project_type)',
        'CREATE INDEX IF NOT EXISTS idx_project_registry_domain ON project_registry(domain)'];

      // Execute index creation queries concurrently
      await Promise.all(indexes.map(indexQuery => this.db.query(indexQuery)));

      this.initialized = true;
      return { success: true, message: 'Cross-project sharing system initialized successfully' };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Register a new project in the system
   */
  async registerProject(projectData) {
    try {
      await this.initialize();
      const {
        project_id,
        project_name,
        description = '',
        technology_stack = [],
        project_type = 'unknown',
        domain = 'general',
        patterns = [],
        keywords = [],
        metadata = {} } = projectData;

      if (!project_id || !project_name) {
        throw new Error('Project ID And name are required');
      }

      // Check if project already exists
      const [existingProject] = await this.db.query(
        'SELECT id FROM project_registry WHERE project_id = ?',
        { replacements: [project_id] },
      );

      if (existingProject.length > 0) {
        throw new Error(`Project ${project_id} already registered`);
      }

      // Insert new project
      const [_result] = await this.db.query(`
        INSERT INTO project_registry (
          project_id, project_name, description, technology_stack,
          project_type, domain, patterns, keywords, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `, {
        replacements: [
          project_id,
          project_name,
          description,
          JSON.stringify(technology_stack),
          project_type,
          domain,
          JSON.stringify(patterns),
          JSON.stringify(keywords),
          JSON.stringify(metadata),
        ],
      });

      return {
        success: true,
        project_id,
        message: 'Project registered successfully',
        registered_at: new Date().toISOString() };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Share a lesson across projects with categorization
   */
  async shareLessonCrossProject(lessonId, projectId, sharingData = {}) {
    try {
      await this.initialize();
      const {
        sharing_scope = 'organization',
        project_specific_tags = [],
        lesson_category = 'general',
        applicability_score = 1.0,
        sharing_metadata = {} } = sharingData;

      // Validate project exists
      const [project] = await this.db.query(
        'SELECT id FROM project_registry WHERE project_id = ?',
        { replacements: [projectId] },
      );

      if (project.length === 0) {
        throw new Error(`Project ${projectId} not found. Please register the project first.`);
      }

      // Validate lesson exists (assuming lessons table exists)
      const [lesson] = await this.db.query(
        'SELECT id FROM lessons WHERE id = ?',
        { replacements: [lessonId] },
      );

      if (lesson.length === 0) {
        throw new Error(`Lesson ${lessonId} not found`);
      }

      // Check if lesson already shared for this project
      const [existingSharing] = await this.db.query(
        'SELECT id FROM project_lessons WHERE lesson_id = ? AND project_id = ?',
        { replacements: [lessonId, projectId] },
      );

      if (existingSharing.length > 0) {
        throw new Error(`Lesson ${lessonId} already shared for project ${projectId}`);
      }

      // Insert sharing record
      const [_result] = await this.db.query(`
        INSERT INTO project_lessons (
          lesson_id, project_id, sharing_scope, project_specific_tags,
          lesson_category, applicability_score, sharing_metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
      `, {
        replacements: [
          lessonId,
          projectId,
          sharing_scope,
          JSON.stringify(project_specific_tags),
          lesson_category,
          applicability_score,
          JSON.stringify(sharing_metadata),
        ],
      });

      // Generate sharing recommendations for other projects
      await this._generateSharingRecommendations(lessonId, projectId);

      return {
        success: true,
        lesson_id: lessonId,
        project_id: projectId,
        sharing_scope,
        lesson_category,
        message: 'Lesson shared successfully across projects',
        shared_at: new Date().toISOString() };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Calculate project relevance score between two projects
   */
  async calculateProjectRelevance(sourceProjectId, targetProjectId) {
    try {
      // Get both project details
      const [sourceProject] = await this.db.query(
        'SELECT * FROM project_registry WHERE project_id = ?',
        { replacements: [sourceProjectId] },
      );

      const [targetProject] = await this.db.query(
        'SELECT * FROM project_registry WHERE project_id = ?',
        { replacements: [targetProjectId] },
      );

      if (sourceProject.length === 0 || targetProject.length === 0) {
        throw new Error('One or both projects not found');
      }

      const source = sourceProject[0];
      const target = targetProject[0];

      // Parse JSON fields
      const sourceTech = JSON.parse(source.technology_stack || '[]');
      const targetTech = JSON.parse(target.technology_stack || '[]');
      const sourcePatterns = JSON.parse(source.patterns || '[]');
      const targetPatterns = JSON.parse(target.patterns || '[]');
      const sourceKeywords = JSON.parse(source.keywords || '[]');
      const targetKeywords = JSON.parse(target.keywords || '[]');

      // Calculate similarity scores
      const techSimilarity = this._calculateArraySimilarity(sourceTech, targetTech);
      const typeSimilarity = source.project_type === target.project_type ? 1.0 : 0.0;
      const domainSimilarity = source.domain === target.domain ? 1.0 : 0.0;
      const patternSimilarity = this._calculateArraySimilarity(sourcePatterns, targetPatterns);
      const keywordSimilarity = this._calculateArraySimilarity(sourceKeywords, targetKeywords);

      // Calculate weighted relevance score
      const relevanceScore =
        (techSimilarity * this.relevanceWeights.technology_stack) +
        (typeSimilarity * this.relevanceWeights.project_type) +
        (domainSimilarity * this.relevanceWeights.domain) +
        (patternSimilarity * this.relevanceWeights.patterns) +
        (keywordSimilarity * this.relevanceWeights.keywords);

      return {
        success: true,
        source_project: sourceProjectId,
        target_project: targetProjectId,
        relevance_score: Math.round(relevanceScore * 100) / 100,
        similarity_breakdown: {
          technology_stack: techSimilarity,
          project_type: typeSimilarity,
          domain: domainSimilarity,
          patterns: patternSimilarity,
          keywords: keywordSimilarity },
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get shared lessons for a specific project with relevance filtering
   */
  async getSharedLessonsForProject(projectId, options = {}) {
    try {
      await this.initialize();
      const {
        sharing_scope = ['organization', 'team', 'public'],
        min_relevance_score = 0.3,
        lesson_category = null,
        limit = 20,
        include_recommendations = true } = options;

      const scopeCondition = Array.isArray(sharing_scope)
        ? `sharing_scope IN (${sharing_scope.map(() => '?').join(', ')})`
        : 'sharing_scope = ?';

      const scopeParams = Array.isArray(sharing_scope) ? sharing_scope : [sharing_scope];

      let categoryCondition = '';
      const params = [...scopeParams];

      if (lesson_category) {
        categoryCondition = ' AND pl.lesson_category = ?';
        params.push(lesson_category);
      }

      // Get shared lessons from other projects
      const [sharedLessons] = await this.db.query(`
        SELECT
          l.id as lesson_id,
          l.title,
          l.content,
          l.category,
          l.tags,
          pl.project_id as source_project,
          pl.sharing_scope,
          pl.lesson_category,
          pl.applicability_score,
          pl.project_specific_tags,
          pr.project_name as source_project_name,
          pr.project_type as source_project_type,
          pr.domain as source_domain
        FROM project_lessons pl
        JOIN lessons l ON pl.lesson_id = l.id
        JOIN project_registry pr ON pl.project_id = pr.project_id
        WHERE pl.project_id != ?
        AND ${scopeCondition}
        ${categoryCondition}
        ORDER BY pl.applicability_score DESC, pl.shared_at DESC
        LIMIT ?
      `, {
        replacements: [...params, projectId, limit],
      });

      // Calculate relevance scores for each lesson concurrently
      const relevancePromises = sharedLessons.map(async lesson => {
        const relevanceResult = await this.calculateProjectRelevance(
          lesson.source_project,
          projectId,
        );

        if (relevanceResult.success && relevanceResult.relevance_score >= min_relevance_score) {
          return {
            ...lesson,
            relevance_score: relevanceResult.relevance_score,
            similarity_breakdown: relevanceResult.similarity_breakdown,
            project_specific_tags: JSON.parse(lesson.project_specific_tags || '[]'),
          };
        }
        return null;
      });

      const enhancedLessonsResults = await Promise.all(relevancePromises);
      const enhancedLessons = enhancedLessonsResults.filter(lesson => lesson !== null);

      // Sort by relevance score
      enhancedLessons.sort((a, b) => b.relevance_score - a.relevance_score);

      const _result = {
        success: true,
        project_id: projectId,
        shared_lessons: enhancedLessons,
        count: enhancedLessons.length,
        filters: {
          sharing_scope,
          min_relevance_score,
          lesson_category },
      };

      // Include recommendations if requested
      if (include_recommendations) {
        const recommendations = await this.getProjectRecommendations(projectId);
        _result.recommendations = recommendations.success ? recommendations.recommendations : [];
      }

      return _result;

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get sharing recommendations for a project
   */
  async getProjectRecommendations(projectId, options = {}) {
    try {
      await this.initialize();
      const {
        min_relevance_score = 0.5,
        status = 'pending',
        limit = 10 } = options;

      const [recommendations] = await this.db.query(`
        SELECT
          sr.*,
          l.title as lesson_title,
          l.content as lesson_content,
          l.category as lesson_category,
          pr.project_name as source_project_name,
          pr.project_type as source_project_type
        FROM sharing_recommendations sr
        JOIN lessons l ON sr.lesson_id = l.id
        JOIN project_registry pr ON sr.source_project_id = pr.project_id
        WHERE sr.target_project_id = ?
        AND sr.status = ?
        AND sr.relevance_score >= ?
        AND (sr.expires_at IS NULL OR sr.expires_at > datetime('now'))
        ORDER BY sr.relevance_score DESC, sr.created_at DESC
        LIMIT ?
      `, {
        replacements: [projectId, status, min_relevance_score, limit],
      });

      return {
        success: true,
        project_id: projectId,
        recommendations: recommendations.map(rec => ({
          ...rec,
          recommendation_reason: JSON.parse(rec.recommendation_reason || '{}'),
        })),
        count: recommendations.length };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Record application of a shared lesson
   */
  async recordLessonApplication(applicationData) {
    try {
      await this.initialize();
      const {
        source_project_id,
        target_project_id,
        lesson_id,
        applied_successfully,
        application_outcome = {},
        feedback_score = null,
        feedback_comment = '' } = applicationData;

      // Calculate relevance score
      const relevanceResult = await this.calculateProjectRelevance(
        source_project_id,
        target_project_id,
      );

      const relevance_score = relevanceResult.success ? relevanceResult.relevance_score : 0.5;

      // Insert application record
      const [_result] = await this.db.query(`
        INSERT INTO cross_project_analytics (
          source_project_id, target_project_id, lesson_id, relevance_score,
          applied_successfully, application_outcome, feedback_score, feedback_comment
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, {
        replacements: [
          source_project_id,
          target_project_id,
          lesson_id,
          relevance_score,
          applied_successfully,
          JSON.stringify(application_outcome),
          feedback_score,
          feedback_comment,
        ],
      });

      // Update recommendation status if it exists
      await this.db.query(`
        UPDATE sharing_recommendations
        SET status = 'applied', updated_at = datetime('now')
        WHERE target_project_id = ? AND lesson_id = ? AND status = 'pending'
      `, {
        replacements: [target_project_id, lesson_id],
      });

      return {
        success: true,
        source_project: source_project_id,
        target_project: target_project_id,
        lesson_id,
        applied_successfully,
        relevance_score,
        message: 'Lesson application recorded successfully',
        applied_at: new Date().toISOString() };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get cross-project analytics And insights
   */
  async getCrossProjectAnalytics(projectId = null, options = {}) {
    try {
      await this.initialize();
      const {
        date_range = 30, // days
        include_breakdown = true } = options;

      const dateFilter = `datetime('now', '-${date_range} days')`;
      const projectFilter = projectId ? 'WHERE target_project_id = ?' : '';
      const params = projectId ? [projectId] : [];

      // Get overall analytics
      const [overallStats] = await this.db.query(`
        SELECT
          COUNT(*) as total_applications,
          COUNT(CASE WHEN applied_successfully = 1 THEN 1 END) as successful_applications,
          AVG(relevance_score) as avg_relevance_score,
          AVG(feedback_score) as avg_feedback_score,
          COUNT(DISTINCT source_project_id) as contributing_projects,
          COUNT(DISTINCT target_project_id) as benefiting_projects,
          COUNT(DISTINCT lesson_id) as shared_lessons
        FROM cross_project_analytics
        ${projectFilter}
        AND applied_at >= ${dateFilter}
      `, { replacements: params });

      const analytics = {
        success: true,
        project_id: projectId,
        date_range_days: date_range,
        analytics: overallStats[0] };

      if (include_breakdown) {
        // Get top contributing projects
        const [topContributors] = await this.db.query(`
          SELECT
            cpa.source_project_id,
            pr.project_name,
            COUNT(*) as lessons_shared,
            COUNT(CASE WHEN applied_successfully = 1 THEN 1 END) as successful_applications,
            AVG(relevance_score) as avg_relevance,
            AVG(feedback_score) as avg_feedback
          FROM cross_project_analytics cpa
          JOIN project_registry pr ON cpa.source_project_id = pr.project_id
          ${projectFilter ? 'WHERE cpa.target_project_id = ?' : ''}
          ${projectFilter ? 'AND' : 'WHERE'} cpa.applied_at >= ${dateFilter}
          GROUP BY cpa.source_project_id, pr.project_name
          ORDER BY lessons_shared DESC, avg_feedback DESC
          LIMIT 10
        `, { replacements: params });

        // Get top lesson categories
        const [topCategories] = await this.db.query(`
          SELECT
            pl.lesson_category,
            COUNT(DISTINCT cpa.lesson_id) as lessons_count,
            COUNT(*) as applications_count,
            AVG(cpa.relevance_score) as avg_relevance,
            COUNT(CASE WHEN applied_successfully = 1 THEN 1 END) as successful_applications
          FROM cross_project_analytics cpa
          JOIN project_lessons pl ON cpa.lesson_id = pl.lesson_id
          ${projectFilter ? 'WHERE cpa.target_project_id = ?' : ''}
          ${projectFilter ? 'AND' : 'WHERE'} cpa.applied_at >= ${dateFilter}
          GROUP BY pl.lesson_category
          ORDER BY applications_count DESC
          LIMIT 10
        `, { replacements: params });

        analytics.breakdown = {
          top_contributors: topContributors,
          top_categories: topCategories };
      }

      return analytics;

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Generate sharing recommendations for new lessons
   */
  async _generateSharingRecommendations(lessonId, sourceProjectId) {
    try {
      // Get all other projects
      const [otherProjects] = await this.db.query(
        'SELECT project_id FROM project_registry WHERE project_id != ?',
        { replacements: [sourceProjectId] },
      );

      const recommendations = [];
      const expirationTime = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

      // Calculate relevance scores concurrently
      const relevancePromises = otherProjects.map(async project => {
        const relevanceResult = await this.calculateProjectRelevance(
          sourceProjectId,
          project.project_id,
        );
        return { project, relevanceResult };
      });

      const relevanceResults = await Promise.all(relevancePromises);

      // Process qualifying projects And prepare database operations
      const dbOperations = [];
      const qualifiedResults = relevanceResults.filter(
        ({ relevanceResult }) => relevanceResult.success && relevanceResult.relevance_score >= 0.4,
      );

      for (const { project, relevanceResult } of qualifiedResults) {
        const recommendationId = crypto.randomUUID();
        const reason = {
          relevance_factors: relevanceResult.similarity_breakdown,
          overall_score: relevanceResult.relevance_score,
          generated_at: new Date().toISOString() };

        dbOperations.push(
          this.db.query(`
            INSERT INTO sharing_recommendations (
              recommendation_id, source_project_id, target_project_id,
              lesson_id, relevance_score, recommendation_reason, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
          `, {
            replacements: [
              recommendationId,
              sourceProjectId,
              project.project_id,
              lessonId,
              relevanceResult.relevance_score,
              JSON.stringify(reason),
              expirationTime.toISOString()] }),
        );

        recommendations.push({
          recommendation_id: recommendationId,
          target_project: project.project_id,
          relevance_score: relevanceResult.relevance_score });
      }

      // Execute all database operations concurrently
      await Promise.all(dbOperations);

      return recommendations;

    } catch (error) {
      // Use structured logging for error reporting
      const { createLogger } = require('../../utils/logger');
      const logger = createLogger('CrossProjectSharing');
      logger.error('Error generating sharing recommendations:', error);
      return [];
    }
  }

  /**
   * Calculate similarity between two arrays (Jaccard similarity)
   */
  _calculateArraySimilarity(array1, array2) {
    if (!Array.isArray(array1) || !Array.isArray(array2)) {
      return 0.0;
    }

    if (array1.length === 0 && array2.length === 0) {
      return 1.0;
    }

    if (array1.length === 0 || array2.length === 0) {
      return 0.0;
    }

    const set1 = new Set(array1.map(item => item.toLowerCase()));
    const set2 = new Set(array2.map(item => item.toLowerCase()));

    const intersection = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([...set1, ...set2]);

    return intersection.size / union.size;
  }

  /**
   * Update project information
   */
  async updateProject(projectId, updates) {
    try {
      await this.initialize();

      const allowedFields = [
        'project_name', 'description', 'technology_stack',
        'project_type', 'domain', 'patterns', 'keywords', 'metadata'];

      const updateFields = [];
      const params = [];

      for (const [field, value] of Object.entries(updates)) {
        if (allowedFields.includes(field)) {
          updateFields.push(`${field} = ?`);

          // JSON stringify arrays And objects
          if (['technology_stack', 'patterns', 'keywords', 'metadata'].includes(field)) {
            params.push(JSON.stringify(value));
          } else {
            params.push(value);
          }
        }
      }

      if (updateFields.length === 0) {
        throw new Error('No valid fields to update');
      }

      updateFields.push('updated_at = datetime(\'now\')');
      params.push(projectId);

      const [_result] = await this.db.query(`
        UPDATE project_registry
        SET ${updateFields.join(', ')}
        WHERE project_id = ?
      `, { replacements: params });

      return {
        success: true,
        project_id: projectId,
        updated_fields: Object.keys(updates),
        message: 'Project updated successfully' };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get project details
   */
  async getProject(projectId) {
    try {
      await this.initialize();

      const [project] = await this.db.query(
        'SELECT * FROM project_registry WHERE project_id = ?',
        { replacements: [projectId] },
      );

      if (project.length === 0) {
        throw new Error(`Project ${projectId} not found`);
      }

      const projectData = project[0];

      // Parse JSON fields
      return {
        success: true,
        project: {
          ...projectData,
          technology_stack: JSON.parse(projectData.technology_stack || '[]'),
          patterns: JSON.parse(projectData.patterns || '[]'),
          keywords: JSON.parse(projectData.keywords || '[]'),
          metadata: JSON.parse(projectData.metadata || '{}') },
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * List all registered projects
   */
  async listProjects(options = {}) {
    try {
      await this.initialize();
      const {
        project_type = null,
        domain = null,
        technology = null,
        limit = 50 } = options;

      const whereConditions = [];
      const params = [];

      if (project_type) {
        whereConditions.push('project_type = ?');
        params.push(project_type);
      }

      if (domain) {
        whereConditions.push('domain = ?');
        params.push(domain);
      }

      if (technology) {
        whereConditions.push('technology_stack LIKE ?');
        params.push(`%"${technology}"%`);
      }

      const whereClause = whereConditions.length > 0
        ? `WHERE ${whereConditions.join(' AND ')}`
        : '';

      params.push(limit);

      const [projects] = await this.db.query(`
        SELECT
          project_id, project_name, description, technology_stack,
          project_type, domain, patterns, keywords, created_at, updated_at
        FROM project_registry
        ${whereClause}
        ORDER BY updated_at DESC
        LIMIT ?
      `, { replacements: params });

      return {
        success: true,
        projects: projects.map(project => ({
          ...project,
          technology_stack: JSON.parse(project.technology_stack || '[]'),
          patterns: JSON.parse(project.patterns || '[]'),
          keywords: JSON.parse(project.keywords || '[]') })),
        count: projects.length,
        filters: { project_type, domain, technology },
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

module.exports = CrossProjectSharing;
