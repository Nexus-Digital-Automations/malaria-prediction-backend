
const { loggers } = require('../../logger');
/**
 * Lesson Versioning System
 * Implements comprehensive lesson versioning to track evolution of lessons over time
 * Includes version comparison, rollback capabilities, And change tracking
 */

const crypto = require('crypto');

class LessonVersioning {
  constructor(ragDatabase) {
    this.ragDB = ragDatabase;
    this.initialized = false;
  }

  /**
   * Initialize versioning system with additional tables
   */
  async initialize() {
    if (this.initialized) {return { success: true };}

    try {
      await this.createVersioningTables();
      await this.migrateExistingLessons();
      this.initialized = true;
      return { success: true, message: 'Lesson versioning system initialized' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Create versioning-specific database tables
   */
  createVersioningTables(_category = 'general') {
    return new Promise((resolve, reject) => {


      const sql = `
        -- Add versioning columns to lessons table if they don't exist
        PRAGMA table_info(lessons);

        -- Lesson versions table for historical tracking
        CREATE TABLE IF NOT EXISTS lesson_versions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          lesson_id INTEGER NOT NULL,
          version_number TEXT NOT NULL,
          title TEXT NOT NULL,
          content TEXT NOT NULL,
          _category TEXT NOT NULL,
          subcategory TEXT,
          project_path TEXT,
          file_path TEXT,
          tags TEXT,
          embedding_id INTEGER,
          success_rate REAL DEFAULT 0.0,
          usage_count INTEGER DEFAULT 0,
          version_hash TEXT NOT NULL,
          change_type TEXT NOT NULL, -- 'created', 'updated', 'merged', 'rollback'
          change_description TEXT,
          previous_version TEXT,
          created_by TEXT DEFAULT 'system',
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          deprecated BOOLEAN DEFAULT 0,
          FOREIGN KEY (lesson_id) REFERENCES lessons (id)
        );

        -- Version metadata table
        CREATE TABLE IF NOT EXISTS version_metadata (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          lesson_id INTEGER NOT NULL,
          current_version TEXT NOT NULL,
          total_versions INTEGER DEFAULT 1,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          last_rollback_at DATETIME,
          version_strategy TEXT DEFAULT 'semantic', -- 'semantic', 'timestamp', 'manual'
          FOREIGN KEY (lesson_id) REFERENCES lessons (id)
        );

        -- Version comparisons table for tracking comparisons
        CREATE TABLE IF NOT EXISTS version_comparisons (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          lesson_id INTEGER NOT NULL,
          version_a TEXT NOT NULL,
          version_b TEXT NOT NULL,
          similarity_score REAL,
          diff_summary TEXT,
          compared_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (lesson_id) REFERENCES lessons (id)
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_lesson_versions_lesson_id ON lesson_versions(lesson_id);
        CREATE INDEX IF NOT EXISTS idx_lesson_versions_version ON lesson_versions(version_number);
        CREATE INDEX IF NOT EXISTS idx_lesson_versions_created ON lesson_versions(created_at);
        CREATE INDEX IF NOT EXISTS idx_version_metadata_lesson_id ON version_metadata(lesson_id);
        CREATE INDEX IF NOT EXISTS idx_version_comparisons_lesson_id ON version_comparisons(lesson_id);
      `;

      this.ragDB.db.exec(sql, (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Add versioning columns to existing lessons table
   */
  addVersioningColumns() {
    return new Promise((resolve, reject) => {


      const alterQueries = [
        `ALTER TABLE lessons ADD COLUMN current_version TEXT DEFAULT '1.0.0'`,
        `ALTER TABLE lessons ADD COLUMN version_hash TEXT`,
        `ALTER TABLE lessons ADD COLUMN created_by TEXT DEFAULT 'system'`,
        `ALTER TABLE lessons ADD COLUMN last_modified_by TEXT`,
        `ALTER TABLE lessons ADD COLUMN change_description TEXT`];

      const runQuery = (index) => {
        if (index >= alterQueries.length) {
          resolve();
          return;
        }

        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        this.ragDB.db.run(alterQueries[index], (error) => {
          if (error && !error.message.includes('duplicate column name')) {
            reject(error);
          } else {
            runQuery(index + 1);
          }
        });
      };

      runQuery(0);
    });
  }

  /**
   * Migrate existing lessons to versioning system
   */
  migrateExistingLessons() {
    return new Promise((resolve, reject) => {


      // First add versioning columns
      this.addVersioningColumns().then(() => {
        // Get all existing lessons
        this.ragDB.db.all('SELECT * FROM lessons WHERE current_version IS NULL OR current_version = ""', [], async (error, lessons) => {
          if (error) {
            reject(error);
            return;
          }

          // Process all lessons concurrently for version migration;
          const migrationPromises = lessons.map(async lesson => {
            try {
              const versionHash = this.generateVersionHash(lesson);
              const version = '1.0.0';

              // Update lesson with version info
              await this.updateLessonVersion(lesson.id, version, versionHash);

              // Create initial version record
              await this.createVersionRecord(lesson, version, versionHash, 'migrated', 'Initial version from migration');

              // Create version metadata
              await this.createVersionMetadata(lesson.id, version);
            } catch (error) {
              loggers.app.warn(`[VERSIONING] Migration warning for lesson ${lesson.id}:`, error.message);
            }
          });

          await Promise.all(migrationPromises);

          resolve();
        });
      }).catch ((error) => { loggers.rag.error('Version creation failed:', error); });
    });
  }

  /**
   * Generate content hash for version tracking
   */
  generateVersionHash(lessonData) {
    const content = `${lessonData.title}|${lessonData.content}|${lessonData.category}|${lessonData.subcategory || ''}`;
    return crypto.createHash('sha256').update(content).digest('hex').substring(0, 16);
  }

  /**
   * Store new version of a lesson
   */
  async storeLessonVersion(lessonData, versionInfo = {}) {
    try {
      const {
        changeType = 'updated',
        changeDescription = 'Lesson updated',
        createdBy = 'system',
        versionStrategy = 'semantic' } = versionInfo;

      // Check if lesson exists;
      const existingLesson = await this.findLessonByIdentifier(lessonData);

      if (existingLesson) {
        // Update existing lesson with new version
        return await this.updateExistingLessonVersion(existingLesson, lessonData, {
          changeType,
          changeDescription,
          createdBy,
          versionStrategy });
      } else {
        // Create new lesson with version 1.0.0
        return await this.createNewVersionedLesson(lessonData, {
          changeType: 'created',
          changeDescription: changeDescription || 'Initial lesson creation',
          createdBy,
          versionStrategy });
      }
    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Find lesson by title And category (identifier)
   */
  findLessonByIdentifier(lessonData) {
    return new Promise((resolve, reject) => {


      const sql = `
        SELECT * FROM lessons
        WHERE title = ? AND category = ?
        ORDER BY id DESC LIMIT 1
      `;

      this.ragDB.db.get(sql, [lessonData.title, lessonData._category], (error, row) => {
        if (error) {
          reject(error);
        } else {
          resolve(row || null);
        }
      });
    });
  }

  /**
   * Update existing lesson with new version
   */
  async updateExistingLessonVersion(existingLesson, newLessonData, versionInfo) {
    const newHash = this.generateVersionHash(newLessonData);
    const currentVersion = existingLesson.current_version || '1.0.0';

    // Check if content actually changed
    if (existingLesson.version_hash === newHash) {
      return {
        success: true,
        lessonId: existingLesson.id,
        version: currentVersion,
        message: 'No changes detected, version unchanged',
        changed: false };
    }

    // Generate new version number;
    const newVersion = this.generateNextVersion(currentVersion, versionInfo.versionStrategy);

    try {
      // Store current version as historical record
      await this.createVersionRecord(existingLesson, currentVersion, existingLesson.version_hash, 'archived', 'Previous version archived');

      // Update main lesson record
      await this.updateLessonContent(existingLesson.id, newLessonData, newVersion, newHash, versionInfo);

      // Create new version record
      await this.createVersionRecord(
        { ...existingLesson, ...newLessonData },
        newVersion,
        newHash,
        versionInfo.changeType,
        versionInfo.changeDescription,
        currentVersion,
      );

      // Update version metadata
      await this.updateVersionMetadata(existingLesson.id, newVersion);

      return {
        success: true,
        lessonId: existingLesson.id,
        version: newVersion,
        previousVersion: currentVersion,
        versionHash: newHash,
        message: 'Lesson version updated successfully',
        changed: true };

    } catch (_) {
      throw new Error(`Failed to update lesson version: ${_.message}`);
    }
  }

  /**
   * Create new versioned lesson
   */
  async createNewVersionedLesson(lessonData, versionInfo) {
    const versionHash = this.generateVersionHash(lessonData);
    const version = '1.0.0';
    try {
      // Generate embedding for new lesson;
      const embedding = await this.ragDB.generateEmbedding(`${lessonData.title} ${lessonData.content}`);
      const embeddingId = await this.ragDB.storeEmbedding(embedding);

      // Create lesson with versioning info;
      const lessonId = await this.createVersionedLessonRecord(lessonData, version, versionHash, embeddingId, versionInfo);

      // Create initial version record
      await this.createVersionRecord(
        { id: lessonId, ...lessonData },
        version,
        versionHash,
        versionInfo.changeType,
        versionInfo.changeDescription,
      );

      // Create version metadata
      await this.createVersionMetadata(lessonId, version);

      // Add to vector index
      if (this.ragDB.vectorIndex && !this.ragDB.useSimpleSearch) {
        this.ragDB.vectorIndex.add(embedding);
      }
      this.ragDB.vectorEmbeddings.push({ id: lessonId, embedding, type: 'lesson' });

      return {
        success: true,
        lessonId,
        version,
        versionHash,
        embeddingId,
        message: 'New versioned lesson created successfully',
        changed: true };

    } catch (_) {
      throw new Error(`Failed to create new versioned lesson: ${_.message}`);
    }
  }

  /**
   * Generate next version number based on strategy
   */
  generateNextVersion(currentVersion, strategy = 'semantic') {
    const parts = currentVersion.split('.').map(Number);

    switch (strategy) {
      case 'major':
        return `${parts[0] + 1}.0.0`;
      case 'minor':
        return `${parts[0]}.${parts[1] + 1}.0`;
      case 'patch':
      case 'semantic':
      default:
        return `${parts[0]}.${parts[1]}.${parts[2] + 1}`;
    }
  }

  /**
   * Create version record in lesson_versions table
   */
  createVersionRecord(lessonData, version, versionHash, changeType, changeDescription, previousVersion = null) {
    return new Promise((resolve, reject) => {
      const sql = `
        INSERT INTO lesson_versions (
          lesson_id, version_number, title, content, _category, subcategory,
          project_path, file_path, tags, embedding_id, success_rate, usage_count,
          version_hash, change_type, change_description, previous_version, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      const values = [
        lessonData.id,
        version,
        lessonData.title,
        lessonData.content,
        lessonData.category,
        lessonData.subcategory,
        lessonData.project_path,
        lessonData.file_path,
        lessonData.tags,
        lessonData.embedding_id,
        lessonData.success_rate || 0,
        lessonData.usage_count || 0,
        versionHash,
        changeType,
        changeDescription,
        previousVersion,
        lessonData.created_by || 'system'];

      this.ragDB.db.run(sql, values, function (error) {
        if (error) {
          reject(error);
        } else {
          resolve(this.lastID);
        }
      });
    });
  }

  /**
   * Create or update version metadata
   */
  createVersionMetadata(lessonId, version) {
    return new Promise((resolve, reject) => {
      const sql = `
        INSERT OR REPLACE INTO version_metadata (lesson_id, current_version, total_versions, updated_at)
        VALUES (?, ?,
          COALESCE((SELECT total_versions + 1 FROM version_metadata WHERE lesson_id = ?), 1),
          CURRENT_TIMESTAMP
        )
      `;

      this.ragDB.db.run(sql, [lessonId, version, lessonId], function (error) {
        if (error) {
          reject(error);
        } else {
          resolve(this.lastID);
        }
      });
    });
  }

  /**
   * Update version metadata
   */
  updateVersionMetadata(lessonId, newVersion) {
    return new Promise((resolve, reject) => {
      const sql = `
        UPDATE version_metadata
        SET current_version = ?,
            total_versions = total_versions + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE lesson_id = ?
      `;

      this.ragDB.db.run(sql, [newVersion, lessonId], function (error) {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Create versioned lesson record
   */
  createVersionedLessonRecord(lessonData, version, versionHash, embeddingId, versionInfo) {
    return new Promise((resolve, reject) => {
      const sql = `
        INSERT INTO lessons (
          title, content, _category, subcategory, project_path, file_path, tags,
          embedding_id, current_version, version_hash, created_by, change_description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      const values = [
        lessonData.title,
        lessonData.content,
        lessonData.category,
        lessonData.subcategory,
        lessonData.project_path,
        lessonData.file_path,
        JSON.stringify(lessonData.tags),
        embeddingId,
        version,
        versionHash,
        versionInfo.createdBy,
        versionInfo.changeDescription];

      this.ragDB.db.run(sql, values, function (error) {
        if (error) {
          reject(error);
        } else {
          resolve(this.lastID);
        }
      });
    });
  }

  /**
   * Update lesson content And version info
   */
  updateLessonContent(lessonId, newData, newVersion, newHash, versionInfo) {
    return new Promise((resolve, reject) => {
      const sql = `
        UPDATE lessons
        SET content = ?, title = ?, category = ?, subcategory = ?,
            project_path = ?, file_path = ?, tags = ?,
            current_version = ?, version_hash = ?,
            last_modified_by = ?, change_description = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
      `;

      const values = [
        newData.content,
        newData.title,
        newData.category,
        newData.subcategory,
        newData.project_path,
        newData.file_path,
        JSON.stringify(newData.tags),
        newVersion,
        newHash,
        versionInfo.createdBy,
        versionInfo.changeDescription,
        lessonId];

      this.ragDB.db.run(sql, values, function (error) {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Update lesson version metadata only
   */
  updateLessonVersion(lessonId, version, versionHash) {
    return new Promise((resolve, reject) => {
      const sql = `UPDATE lessons SET current_version = ?, version_hash = ? WHERE id = ?`;

      this.ragDB.db.run(sql, [version, versionHash, lessonId], function (error) {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Get version history for a lesson
   */
  getVersionHistory(lessonId) {
    return new Promise((resolve, reject) => {


      const sql = `
        SELECT lv.*, vm.current_version, vm.total_versions
        FROM lesson_versions lv
        LEFT JOIN version_metadata vm ON lv.lesson_id = vm.lesson_id
        WHERE lv.lesson_id = ?
        ORDER BY lv.created_at DESC
      `;

      this.ragDB.db.all(sql, [lessonId], (error, rows) => {
        if (error) {
          reject(error);
        } else {
          resolve(rows);
        }
      });
    });
  }

  /**
   * Compare two versions of a lesson
   */
  async compareVersions(lessonId, versionA, versionB) {
    try {
      const [versionAData, versionBData] = await Promise.all([
        this.getVersionData(lessonId, versionA),
        this.getVersionData(lessonId, versionB)]);

      if (!versionAData || !versionBData) {
        throw new Error('One or both versions not found');
      }

      const comparison = this.performVersionComparison(versionAData, versionBData);

      // Store comparison for future reference
      await this.storeVersionComparison(lessonId, versionA, versionB, comparison);

      return {
        success: true,
        lessonId,
        versionA,
        versionB,
        comparison };

    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Get version data
   */
  getVersionData(lessonId, version) {
    return new Promise((resolve, reject) => {


      const sql = `
        SELECT * FROM lesson_versions
        WHERE lesson_id = ? AND version_number = ?
        ORDER BY created_at DESC LIMIT 1
      `;

      this.ragDB.db.get(sql, [lessonId, version], (error, row) => {
        if (error) {
          reject(error);
        } else {
          resolve(row);
        }
      });
    });
  }

  /**
   * Perform detailed version comparison
   */
  performVersionComparison(versionA, versionB) {
    const differences = {
      title: versionA.title !== versionB.title,
      content: versionA.content !== versionB.content,
      category: versionA.category !== versionB.category,
      subcategory: versionA.subcategory !== versionB.subcategory,
      tags: versionA.tags !== versionB.tags };

    // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
    const changes = Object.keys(differences).filter(key => differences[key]);

    return {
      identical: changes.length === 0,
      changedFields: changes,
      contentSimilarity: this.calculateContentSimilarity(versionA.content, versionB.content),
      diffSummary: this.generateDiffSummary(versionA, versionB, changes) };
  }

  /**
   * Calculate content similarity using simple string comparison
   */
  calculateContentSimilarity(contentA, contentB) {
    if (contentA === contentB) {return 1.0;}

    const wordsA = contentA.toLowerCase().split(/\s+/);
    const wordsB = contentB.toLowerCase().split(/\s+/);

    const intersection = wordsA.filter(word => wordsB.includes(word));
    const union = [...new Set([...wordsA, ...wordsB])];

    return intersection.length / union.length;
  }

  /**
   * Generate diff summary
   */
  generateDiffSummary(versionA, versionB, changes) {
    if (changes.length === 0) {return 'No changes detected';}

    const summaries = changes.map(field => {
      switch (field) {
        case 'title':
          return `Title changed from "${versionA.title}" to "${versionB.title}"`;
        case 'content':
          return `Content modified (${Math.round(this.calculateContentSimilarity(versionA.content, versionB.content) * 100)}% similarity)`;
        case 'category':
          return `Category changed from "${versionA.category}" to "${versionB.category}"`;
        case 'subcategory':
          return `Subcategory changed from "${versionA.subcategory}" to "${versionB.subcategory}"`;
        case 'tags':
          return `Tags modified`;
        default:
          return `${field} changed`;
      }
    });

    return summaries.join('; ');
  }

  /**
   * Store version comparison result
   */
  storeVersionComparison(lessonId, versionA, versionB, comparison) {
    return new Promise((resolve, reject) => {
      const sql = `
        INSERT INTO version_comparisons (lesson_id, version_a, version_b, similarity_score, diff_summary)
        VALUES (?, ?, ?, ?, ?)
      `;

      this.ragDB.db.run(sql, [
        lessonId,
        versionA,
        versionB,
        comparison.contentSimilarity,
        comparison.diffSummary], function (error) {
        if (error) {
          reject(error);
        } else {
          resolve(this.lastID);
        }
      });
    });
  }

  /**
   * Rollback lesson to previous version
   */
  async rollbackToVersion(lessonId, targetVersion) {
    try {
      const versionData = await this.getVersionData(lessonId, targetVersion);
      if (!versionData) {
        throw new Error(`Version ${targetVersion} not found`);
      }

      const currentVersion = await this.getCurrentVersion(lessonId);
      const newVersion = this.generateNextVersion(currentVersion, 'patch');

      // Update main lesson with target version data
      await this.updateLessonContent(lessonId, versionData, newVersion, versionData.version_hash, {
        createdBy: 'system',
        changeDescription: `Rollback to version ${targetVersion}`,
      });

      // Create rollback version record
      await this.createVersionRecord(
        { ...versionData, id: lessonId },
        newVersion,
        versionData.version_hash,
        'rollback',
        `Rollback to version ${targetVersion}`,
        currentVersion,
      );

      // Update metadata with rollback info
      await this.updateVersionMetadataWithRollback(lessonId, newVersion);

      return {
        success: true,
        lessonId,
        rolledBackTo: targetVersion,
        newVersion,
        message: `Successfully rolled back to version ${targetVersion}` };

    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Get current version of a lesson
   */
  getCurrentVersion(lessonId) {
    return new Promise((resolve, reject) => {


      const sql = `SELECT current_version FROM lessons WHERE id = ?`;

      this.ragDB.db.get(sql, [lessonId], (error, row) => {
        if (error) {
          reject(error);
        } else {
          resolve(row ? row.current_version : '1.0.0');
        }
      });
    });
  }

  /**
   * Update metadata with rollback information
   */
  updateVersionMetadataWithRollback(lessonId, newVersion) {
    return new Promise((resolve, reject) => {
      const sql = `
        UPDATE version_metadata
        SET current_version = ?,
            total_versions = total_versions + 1,
            updated_at = CURRENT_TIMESTAMP,
            last_rollback_at = CURRENT_TIMESTAMP
        WHERE lesson_id = ?
      `;

      this.ragDB.db.run(sql, [newVersion, lessonId], function (error) {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Get comprehensive lesson version analytics
   */
  async getVersionAnalytics(lessonId) {
    try {
      const [history, metadata, comparisons] = await Promise.all([
        this.getVersionHistory(lessonId),
        this.getVersionMetadata(lessonId),
        this.getVersionComparisons(lessonId)]);
      return {
        success: true,
        lessonId,
        analytics: {
          totalVersions: metadata.total_versions,
          currentVersion: metadata.current_version,
          createdAt: metadata.created_at,
          lastUpdated: metadata.updated_at,
          lastRollback: metadata.last_rollback_at,
          versionStrategy: metadata.version_strategy,
          history: history.map(v => ({
            version: v.version_number,
            changeType: v.change_type,
            changeDescription: v.change_description,
            createdBy: v.created_by,
            createdAt: v.created_at,
            previousVersion: v.previous_version })),
          comparisons: comparisons.map(c => ({
            versionA: c.version_a,
            versionB: c.version_b,
            similarityScore: c.similarity_score,
            diffSummary: c.diff_summary,
            comparedAt: c.compared_at })) } };

    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Get version metadata
   */
  getVersionMetadata(lessonId) {
    return new Promise((resolve, reject) => {


      const sql = `SELECT * FROM version_metadata WHERE lesson_id = ?`;

      this.ragDB.db.get(sql, [lessonId], (error, row) => {
        if (error) {
          reject(error);
        } else {
          resolve(row || {});
        }
      });
    });
  }

  /**
   * Get version comparisons
   */
  getVersionComparisons(lessonId) {
    return new Promise((resolve, reject) => {


      const sql = `
        SELECT * FROM version_comparisons
        WHERE lesson_id = ?
        ORDER BY compared_at DESC
      `;

      this.ragDB.db.all(sql, [lessonId], (error, rows) => {
        if (error) {
          reject(error);
        } else {
          resolve(rows || []);
        }
      });
    });
  }
}

module.exports = LessonVersioning;
