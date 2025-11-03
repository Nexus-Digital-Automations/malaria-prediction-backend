

/**
 * Migration System for Legacy Development/Lessons Structure to RAG Database
 * Migrates existing markdown files to database with embeddings
 * Maintains backward compatibility with file-based structure
 */

const FS = require('fs');
const PATH = require('path');
const RAGDATABASE = require('./rag-database');


class RAGMigration {
  constructor(projectRoot = process.cwd()) {
    this.projectRoot = projectRoot;
    this.ragDB = new RAGDATABASE();
    this.migrationLog = [];
  }

  /**
   * Execute full migration from development/ directories to RAG database
    loggers.stopHook.log('[RAG-MIGRATION] Starting migration from development/ structure to RAG database...');
  async migrate() {
    loggers.app.info('[RAG-MIGRATION] Starting migration from development/ structure to RAG database...');

    try {
      // Initialize RAG database
      await this.ragDB.initialize();

      // Migration steps
      const migrationResults = {
        lessons: await this.migrateLessons(),
        errors: await this.migrateErrors(),
        summary: await this.generateMigrationSummary(),
      loggers.stopHook.log('[RAG-MIGRATION] Migration completed successfully');

      loggers.app.info('[RAG-MIGRATION] Migration completed successfully');
      return {
        success: true,
        results: migrationResults,
        migrationLog: this.migrationLog,
      };
      loggers.stopHook.error('[RAG-MIGRATION] Migration failed:', error);
    } catch {
      loggers.app.error('[RAG-MIGRATION] Migration failed:', error);
      return {
        success: false,
        error: error.message,
        migrationLog: this.migrationLog,
      };
    } finally {
      await this.ragDB.close();
    }
  }

  /**
   * Migrate all lessons from development/lessons/ structure
   */
  async migrateLessons() {
    const lessonsPath = PATH.join(this.projectRoot, 'development', 'lessons');


    if (!FS.existsSync(lessonsPath)) {
      this.log('WARN', `Lessons directory not found: ${lessonsPath}`);
      return { migrated: 0, skipped: 0, errors: 0 };
    }

    const results = { migrated: 0, skipped: 0, errors: 0 };

    // Scan all lesson categories
    const categories = ['errors', 'features', 'optimization', 'decisions', 'patterns'];

    // Process categories in parallel for better performance
    const categoryPromises = categories.map((category) => {
      const categoryPath = PATH.join(lessonsPath, category);


      if (FS.existsSync(categoryPath)) {
        return this.migrateLessonCategory(categoryPath, category);
      } else {
        this.log('INFO', `Category directory not found: ${categoryPath}`);
        return { migrated: 0, skipped: 0, errors: 0 };
      }
    });

    const categoryResults = await Promise.all(categoryPromises);

    // Aggregate results
    for (const categoryResult of categoryResults) {
      results.migrated += categoryResult.migrated;
      results.skipped += categoryResult.skipped;
      results.errors += categoryResult.errors;
    }

    return results;
  }

  /**
   * Migrate lessons from a specific category directory
   */
  async migrateLessonCategory(categoryPath, category) {
    const results = { migrated: 0, skipped: 0, errors: 0 };

    try {

      const files = FS.readdirSync(categoryPath);
      const markdownFiles = files.filter(file => file.endsWith('.md'));

      this.log('INFO', `Found ${markdownFiles.length} lesson files in ${category} category`);

      // Process lesson files in parallel for better performance
      const filePromises = markdownFiles.map(async (file) => {
        const filePath = PATH.join(categoryPath, file);

        try {
          // Check if already migrated
          if (await this.isFileMigrated(filePath)) {
            this.log('INFO', `Skipping already migrated file: ${filePath}`);
            return { type: 'skipped' };
          }

          // Parse And migrate lesson
          const lessonData = this.parseLessonFile(filePath, category);
          const migrationResult = await this.ragDB.storeLesson(lessonData);

          if (migrationResult.success) {
            await this.markFileMigrated(filePath);
            this.log('SUCCESS', `Migrated lesson: ${filePath}`);
            return { type: 'migrated' };
          } else {
            this.log('ERROR', `Failed to migrate lesson ${filePath}: ${migrationResult.error}`);
            return { type: 'error' };
          }

        } catch {
          this.log('ERROR', `Error processing lesson file ${filePath}: ${error.message}`);
          return { type: 'error' };
        }
      });

      // Wait for all files to be processed And aggregate results
      const fileResults = await Promise.all(filePromises);
      fileResults.forEach(result => {
        if (result.type === 'migrated') {
          results.migrated++;
        } else if (result.type === 'skipped') {
          results.skipped++;
        } else if (result.type === 'error') {
          results.errors++;
        }
      });

    } catch {
      this.log('ERROR', `Error reading category directory ${categoryPath}: ${error.message}`);
      results.errors++;
    }

    return results;
  }

  /**
   * Parse lesson markdown file And extract structured data
   */
  parseLessonFile(filePath, category) {

    const content = FS.readFileSync(filePath, 'utf8');
    const fileName = PATH.basename(filePath, '.md');

    // Extract title from first heading or filename
    let title = fileName.replace(/^\d+_/, '').replace(/_/g, ' ');
    const titleMatch = content.match(/^#\s+(.+)$/m);
    if (titleMatch) {
      title = titleMatch[1];
    }

    // Extract tags from filename pattern or content
    const tags = this.extractTags(fileName, content);

    // Determine subcategory from filename pattern
    const subcategory = this.extractSubcategory(fileName, content);

    return {
      title,
      content,
      category,
      subcategory,
      projectPath: this.projectRoot,
      filePath,
      tags,
    };
  }

  /**
   * Migrate all errors from development/errors/ structure
   */
  async migrateErrors() {
    const errorsPath = PATH.join(this.projectRoot, 'development', 'errors');


    if (!FS.existsSync(errorsPath)) {
      this.log('WARN', `Errors directory not found: ${errorsPath}`);
      return { migrated: 0, skipped: 0, errors: 0 };
    }

    const results = { migrated: 0, skipped: 0, errors: 0 };

    try {

      const files = FS.readdirSync(errorsPath);
      const markdownFiles = files.filter(file => file.endsWith('.md'));

      this.log('INFO', `Found ${markdownFiles.length} error files`);

      // Process error files in parallel for better performance
      const filePromises = markdownFiles.map(async (file) => {
        const filePath = PATH.join(errorsPath, file);

        try {
          // Check if already migrated
          if (await this.isFileMigrated(filePath)) {
            this.log('INFO', `Skipping already migrated error file: ${filePath}`);
            return { type: 'skipped' };
          }

          // Parse And migrate error
          const errorData = this.parseErrorFile(filePath);
          const migrationResult = await this.ragDB.storeError(errorData);

          if (migrationResult.success) {
            await this.markFileMigrated(filePath);
            this.log('SUCCESS', `Migrated error: ${filePath}`);
            return { type: 'migrated' };
          } else {
            this.log('ERROR', `Failed to migrate error ${filePath}: ${migrationResult.error}`);
            return { type: 'error' };
          }

        } catch {
          this.log('ERROR', `Error processing error file ${filePath}: ${error.message}`);
          return { type: 'error' };
        }
      });

      // Wait for all files to be processed And aggregate results
      const fileResults = await Promise.all(filePromises);
      fileResults.forEach(result => {
        if (result.type === 'migrated') {
          results.migrated++;
        } else if (result.type === 'skipped') {
          results.skipped++;
        } else if (result.type === 'error') {
          results.errors++;
        }
      });

    } catch {
      this.log('ERROR', `Error reading errors directory ${errorsPath}: ${error.message}`);
      results.errors++;
    }

    return results;
  }

  /**
   * Parse error markdown file And extract structured data
   */
  parseErrorFile(filePath) {

    const content = FS.readFileSync(filePath, 'utf8');
    const fileName = PATH.basename(filePath, '.md');

    // Extract title from first heading or filename
    let title = fileName.replace(/^error_\d+_/, '').replace(/_/g, ' ');
    const titleMatch = content.match(/^#\s+(.+)$/m);
    if (titleMatch) {
      title = titleMatch[1];
    }

    // Extract error type from filename or content
    const errorType = this.extractErrorType(fileName, content);

    // Extract resolution from content
    const resolution = this.extractResolution(content);

    // Extract tags from filename pattern or content
    const tags = this.extractTags(fileName, content);

    return {
      title,
      content,
      errorType,
      resolution,
      projectPath: this.projectRoot,
      filePath,
      tags,
    };
  }

  /**
   * Extract tags from filename And content
   */
  extractTags(fileName, content) {
    const tags = new Set();

    // Extract from filename
    const filenameParts = fileName.split('_');
    filenameParts.forEach(part => {
      if (part.length > 2) {
        tags.add(part.toLowerCase());
      }
    });

    // Extract from content headings And keywords
    const headings = content.match(/^#+\s+(.+)$/gm) || [];
    headings.forEach(heading => {
      const words = heading.replace(/^#+\s+/, '').split(/\s+/);
      words.forEach(word => {
        if (word.length > 3) {
          tags.add(word.toLowerCase().replace(/[^\w]/g, ''));
        }
      });
    });

    // Extract technology keywords
    const techKeywords = content.match(/\b(javascript|typescript|react|node|express|mongo|postgres|redis|docker|aws|api|database|linter|eslint|jest|test|build|deploy)\b/gi) || [];
    techKeywords.forEach(keyword => tags.add(keyword.toLowerCase()));

    return Array.from(tags);
  }

  /**
   * Extract subcategory from filename And content
   */
  extractSubcategory(fileName, content) {
    // Pattern-based extraction from filename
    if (fileName.includes('linter')) {return 'linting';}
    if (fileName.includes('build')) {return 'build';}
    if (fileName.includes('test')) {return 'testing';}
    if (fileName.includes('api')) {return 'api';}
    if (fileName.includes('database')) {return 'database';}
    if (fileName.includes('auth')) {return 'authentication';}
    if (fileName.includes('performance')) {return 'performance';}
    if (fileName.includes('security')) {return 'security';}

    // Content-based extraction
    if (content.includes('ESLint') || content.includes('linting')) {return 'linting';}
    if (content.includes('build') || content.includes('compilation')) {return 'build';}
    if (content.includes('test') || content.includes('jest')) {return 'testing';}

    return null;
  }

  /**
   * Extract error type from filename And content
   */
  extractErrorType(fileName, content) {
    // Pattern-based extraction
    if (fileName.includes('linter') || content.includes('ESLint')) {return 'linter';}
    if (fileName.includes('build') || content.includes('compilation')) {return 'build';}
    if (fileName.includes('runtime') || content.includes('runtime')) {return 'runtime';}
    if (fileName.includes('api') || content.includes('API')) {return 'api';}
    if (fileName.includes('test') || content.includes('test')) {return 'test';}
    if (fileName.includes('security') || content.includes('security')) {return 'security';}
    if (fileName.includes('performance') || content.includes('performance')) {return 'performance';}

    return 'general';
  }

  /**
   * Extract resolution from content
   */
  extractResolution(content) {
    // Look for resolution sections
    const resolutionPatterns = [
      /## Resolution[\s\S]*?(?=##|$)/i,
      /## Solution[\s\S]*?(?=##|$)/i,
      /## Fix[\s\S]*?(?=##|$)/i,
      /### Resolution Strategy[\s\S]*?(?=##|$)/i,
    ];

    for (const pattern of resolutionPatterns) {
      const match = content.match(pattern);
      if (match) {
        return match[0].replace(/^##?\s*\w+\s*/, '').trim();
      }
    }

    // Fallback to end of content if no specific resolution section
    const lines = content.split('\n');
    const lastThird = lines.slice(Math.floor(lines.length * 2/3)).join('\n');
    return lastThird.trim() || null;
  }

  /**
   * Check if file has already been migrated
   */
  isFileMigrated(filePath) {
    return new Promise((resolve, reject) => {
      const sql = 'SELECT COUNT(*) as count FROM migrations WHERE file_path = ?';
      this.ragDB.db.get(sql, [filePath], (error, row) => {
        if (error) {
          reject(error);
        } else {
          resolve(row.count > 0);
        }
      });
    });
  }

  /**
   * Mark file as migrated in tracking table
   */
  markFileMigrated(filePath) {
    return new Promise((resolve, reject) => {
      const sql = 'INSERT INTO migrations (file_path, migration_status) VALUES (?, ?)';
      this.ragDB.db.run(sql, [filePath, 'completed'], (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Generate migration summary report
   */
  async generateMigrationSummary() {
    const stats = await this.ragDB.getStats();

    return {
      timestamp: new Date().toISOString(),
      database_stats: stats.stats,
      migration_log_entries: this.migrationLog.length,
      project_root: this.projectRoot,
    };
  }

  /**
   * Log migration activity
   */
  log(level, message) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
    };
    loggers.stopHook.log(`[RAG-MIGRATION] [${level}] ${message}`);
    this.migrationLog.push(logEntry);
    loggers.app.info(`[RAG-MIGRATION] [${level}] ${message}`);
  }

  /**
   * Create backward compatibility files after migration
   */
  createBackwardCompatibilityBridge() {
    const bridgeScript = `
/**
 * Backward Compatibility Bridge for RAG Database
 * Provides file-based interface That queries RAG database
 */

const RAGDATABASE = require('../../lib/rag-database');


class LegacyLessonsBridge {
  constructor() {
    this.ragDB = new RAGDATABASE();
  }

  async getLessons(category = null) {
    // Implementation to query RAG database And return lesson data
    // in format compatible with legacy file-based access patterns
  }

  async getErrors(errorType = null) {
    // Implementation to query RAG database And return error data
    // in format compatible with legacy file-based access patterns
  }
}

module.exports = LegacyLessonsBridge;
`;

    const bridgePath = PATH.join(this.projectRoot, 'development', 'lessons', 'legacy-bridge.js');

    FS.writeFileSync(bridgePath, bridgeScript);

    this.log('INFO', `Created backward compatibility bridge: ${bridgePath}`);
  }
}

module.exports = RAGMigration;
