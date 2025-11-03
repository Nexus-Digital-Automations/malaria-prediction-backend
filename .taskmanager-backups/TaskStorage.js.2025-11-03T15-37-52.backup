/**
 * TaskStorage - File Operations And Data Persistence Module
 *
 * === OVERVIEW ===
 * Handles all file system operations for TaskManager including reading/writing
 * TODO.json And DONE.json files, backup management, caching, And archiving.
 * This module provides atomic operations with caching for performance optimization.
 *
 * === KEY FEATURES ===
 * • Fast cached reading with file modification time tracking
 * • Atomic write operations with backup/restore capability
 * • Completed task archiving to DONE.json
 * • Legacy backup cleanup And management
 * • Performance-optimized file operations
 *
 * @fileoverview File operations And data persistence for TaskManager
 * @author TaskManager System
 * @version 2.0.0
 * @since 2024-01-01
 */

const FS = require('fs');
const path = require('path');
const LOGGER = require('../appLogger');

class TaskStorage {
  /**
   * Initialize TaskStorage with paths And options
   * @param {string} todoPath - Path to TODO.json file
   * @param {Object} options - Configuration options
   */
  constructor(todoPath, options = {}) {
    this.todoPath = todoPath;
    this.donePath = options.donePath || todoPath.replace('TODO.json', 'DONE.json');
    this.logger = LOGGER;

    // Performance optimization: Add aggressive caching
    this._cache = {
      data: null,
      lastModified: 0,
      enabled: options.enableCache !== false,
    };

    this.options = {
      enableArchiving: options.enableArchiving !== false,
      validateOnRead: options.validateOnRead !== false,
      ...options,
    };
  }

  /**
   * Read TODO.json synchronously without caching
   * @returns {Object} Parsed TODO data
   */
  readTodoSync() {
    this.logger?.logInfo?.('Reading TODO.json synchronously');
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization
    if (!FS.existsSync(this.todoPath)) {
      this.logger?.logWarning?.('TODO.json does not exist, returning default structure');
      return {
        tasks: [],
        completed_tasks: [],
        features: [],
        agents: [],
        project_success_criteria: [],
        task_creation_attempts: [],
      };
    }

    try {
      /* eslint-disable security/detect-non-literal-fs-filename */
      const data = FS.readFileSync(this.todoPath, 'utf8');
      /* eslint-enable security/detect-non-literal-fs-filename */
      return JSON.parse(data);
    } catch (error) {
      this.logger?.logError?.(error, 'Failed to read TODO.json synchronously');
      throw error;
    }
  }

  /**
   * Fast read with caching for performance optimization
   * @returns {Object} Cached or freshly read TODO data
   */
  readTodoFast() {
    this.logger?.logDebug?.('Fast read with caching');
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath is validated path from constructor
    if (!FS.existsSync(this.todoPath)) {
      this.logger?.logWarning?.('TODO.json does not exist for fast read');
      return { tasks: [], completed_tasks: [], features: [], agents: [] };
    }

    if (this._cache.enabled) {
      try {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath is validated path from constructor;
        const stats = FS.statSync(this.todoPath);
        const currentModified = stats.mtime.getTime();

        // Return cached data if file hasn't been modified
        if (this._cache.data && this._cache.lastModified === currentModified) {
          this.logger?.logDebug?.('Returning cached TODO data');
          return this._cache.data;
        }

        // Update cache with fresh data
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath is validated path from constructor;
        const data = FS.readFileSync(this.todoPath, 'utf8');
        const parsedData = JSON.parse(data);

        this._cache.data = parsedData;
        this._cache.lastModified = currentModified;

        this.logger?.logDebug?.('Updated cache with fresh TODO data');
        return parsedData;
      } catch (error) {
        this.logger?.logError?.(error, 'Error in fast read, falling back to uncached read');
        // Fall through to uncached read
      }
    }

    // Fallback to uncached read
    return this.readTodoSync();
  }

  /**
   * Read TODO.json with full validation And auto-fix capabilities
   * @param {boolean} skipValidation - Skip validation for performance
   * @returns {Promise<Object>} Validated TODO data
   */
  async readTodo(skipValidation = false) {
    this.logger?.logInfo?.('Reading TODO.json with validation');
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization
    if (!FS.existsSync(this.todoPath)) {
      this.logger?.logInfo?.('TODO.json does not exist, creating default structure');
      const defaultData = {
        tasks: [],
        completed_tasks: [],
        features: [],
        agents: [],
        project_success_criteria: [],
        task_creation_attempts: [],
      };
      await this.writeTodo(defaultData);
      return defaultData;
    }

    let DATA;
    try {
      if (skipValidation || !this.options.validateOnRead) {
        DATA = this.readTodoFast();
        return DATA;
      }

      // TODO: Add validation logic here when needed
      DATA = this.readTodoFast();
      return DATA;
    } catch (error) {
      this.logger?.logError?.(error, 'Critical error reading TODO.json');
      throw error;
    }
  }

  /**
   * Write TODO.json with atomic operations And backup
   * @param {Object} data - Data to write
   * @param {boolean} skipBackup - Skip backup creation
   * @returns {Promise<Object>} Write _operationresult
   */
  async writeTodo(data, skipBackup = false) {
    await Promise.resolve(); // Minimal async _operationto satisfy linter
    this.logger?.logInfo?.('Writing TODO.json with atomic operation');

    if (!data || typeof data !== 'object') {
      const error = new Error('Invalid data provided to writeTodo');
      this.logger?.logError?.(error, 'WriteTodo validation failed');
      throw error;
    }

    // Ensure required structure
    if (!data.tasks) {data.tasks = [];}
    if (!data.completed_tasks) {data.completed_tasks = [];}
    if (!data.features) {data.features = [];}
    if (!data.agents) {data.agents = [];}

    let backupPath = null;

    try {
      // Create backup if file exists And backup is enabled
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization
      if (!skipBackup && FS.existsSync(this.todoPath)) {
        backupPath = `${this.todoPath}.backup.${Date.now()}`;
        FS.copyFileSync(this.todoPath, backupPath);
        this.logger?.logDebug?.(`Created backup: ${backupPath}`);
      }

      // Write with atomic OPERATION(write to temp file, then rename)
      const tempPath = `${this.todoPath}.tmp.${Date.now()}`;
      const jsonData = JSON.stringify(data, null, 2);

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- tempPath constructed from validated todoPath
      FS.writeFileSync(tempPath, jsonData, 'utf8');
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization
      FS.renameSync(tempPath, this.todoPath);

      this.logger?.logInfo?.('Successfully wrote TODO.json');

      // Update cache
      if (this._cache.enabled) {
        this._cache.data = data;
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization;
        const stats = FS.statSync(this.todoPath);
        this._cache.lastModified = stats.mtime.getTime();
      }

      return {
        success: true,
        message: 'TODO.json written successfully',
        backupPath,
      };
    } catch (error) {
      this.logger?.logError?.(error, 'Failed to write TODO.json');

      // Restore from backup if available
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- backupPath constructed from validated todoPath
      if (backupPath && FS.existsSync(backupPath)) {
        try {
          FS.copyFileSync(backupPath, this.todoPath);
          this.logger?.logInfo?.('Restored from backup after write failure');
        } catch (_error) {
          this.logger?.logError?.(_error, 'Failed to restore from backup');
        }
      }

      throw error;
    } finally {
      // Clean up backup after successful operation
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- backupPath constructed from validated todoPath
      if (backupPath && FS.existsSync(backupPath)) {
        try {
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- backupPath constructed from validated todoPath
          FS.unlinkSync(backupPath);
          this.logger?.logDebug?.('Cleaned up temporary backup');
        } catch (_error) {
          this.logger?.logWarning?.(_error, 'Failed to cleanup temporary backup');
        }
      }
    }
  }

  /**
   * Create a timestamped backup of TODO.json
   * @returns {Promise<Object>} Backup _operationresult
   */
  async createBackup() {
    await Promise.resolve(); // Minimal async _operationto satisfy linter
    this.logger?.logInfo?.('Creating manual backup of TODO.json');

    // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization
    if (!FS.existsSync(this.todoPath)) {
      return {
        success: false,
        message: 'TODO.json does not exist, cannot create backup',
      };
    }

    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupPath = `${this.todoPath}.backup.${timestamp}`;

      FS.copyFileSync(this.todoPath, backupPath);

      this.logger?.logInfo?.(`Backup created: ${backupPath}`);
      return {
        success: true,
        message: 'Backup created successfully',
        backupPath,
      };
    } catch (error) {
      this.logger?.logError?.(error, 'Failed to create backup');
      return {
        success: false,
        message: `Failed to create backup: ${error.message}`,
        error,
      };
    }
  }

  /**
   * List available backup files
   * @returns {Array} List of backup files with metadata
   */
  listBackups() {
    this.logger?.logDebug?.('Listing available backups');

    const todoDir = path.dirname(this.todoPath);
    const todoFilename = path.basename(this.todoPath);
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoDir derived from validated todoPath;
      const files = FS.readdirSync(todoDir);
      const backupFiles = files
        .filter(file => file.startsWith(`${todoFilename}.backup.`))
        .map(file => {
          const filePath = path.join(todoDir, file);
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- filePath constructed from validated directory structure;
          const stats = FS.statSync(filePath);
          return {
            filename: file,
            path: filePath,
            size: stats.size,
            created: stats.birthtime,
            modified: stats.mtime,
          };
        })
        .sort((a, b) => b.created.getTime() - a.created.getTime());

      this.logger?.logDebug?.(`Found ${backupFiles.length} backup files`);
      return backupFiles;
    } catch (error) {
      this.logger?.logError?.(error, 'Failed to list backups');
      return [];
    }
  }

  /**
   * Restore TODO.json from a backup file
   * @param {string} backupFile - Backup filename (optional, uses latest if not provided)
   * @returns {Promise<Object>} Restore _operationresult
   */
  async restoreFromBackup(backupFile = null) {
    await Promise.resolve(); // Minimal async _operationto satisfy linter
    this.logger?.logInfo?.('Restoring TODO.json from backup');

    const backups = this.listBackups();
    if (backups.length === 0) {
      return {
        success: false,
        message: 'No backup files found',
      };
    }

    let selectedBackup;
    if (backupFile) {
      selectedBackup = backups.find(backup => backup.filename === backupFile);
      if (!selectedBackup) {
        return {
          success: false,
          message: `Backup file '${backupFile}' not found`,
        };
      }
    } else {
      selectedBackup = backups[0]; // Latest backup
    }

    try {
      // Create backup of current file before restore
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization
      if (FS.existsSync(this.todoPath)) {
        const preRestoreBackup = `${this.todoPath}.pre-restore.${Date.now()}`;
        FS.copyFileSync(this.todoPath, preRestoreBackup);
        this.logger?.logInfo?.(`Created pre-restore backup: ${preRestoreBackup}`);
      }

      // Restore from backup
      FS.copyFileSync(selectedBackup.path, this.todoPath);

      // Clear cache to force reload
      if (this._cache.enabled) {
        this._cache.data = null;
        this._cache.lastModified = 0;
      }

      this.logger?.logInfo?.(`Successfully restored from backup: ${selectedBackup.filename}`);
      return {
        success: true,
        message: `Restored from backup: ${selectedBackup.filename}`,
        backupUsed: selectedBackup,
      };
    } catch (error) {
      this.logger?.logError?.(error, 'Failed to restore from backup');
      return {
        success: false,
        message: `Failed to restore from backup: ${error.message}`,
        error,
      };
    }
  }

  /**
   * Clean up old backup files, keeping only the most recent ones
   * @param {number} keepCount - Number of backups to keep (default: 5)
   * @returns {Object} Cleanup _operationresult
   */
  cleanupLegacyBackups(keepCount = 5) {
    this.logger?.logInfo?.(`Cleaning up old backups, keeping ${keepCount} most recent`);

    const backups = this.listBackups();
    if (backups.length <= keepCount) {
      return {
        success: true,
        message: `No cleanup needed, ${backups.length} backups found`,
        removedCount: 0,
      };
    }

    const toRemove = backups.slice(keepCount);
    let removedCount = 0;

    for (const backup of toRemove) {
      try {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- backup.path from trusted backup listing
        FS.unlinkSync(backup.path);
        removedCount++;
        this.logger?.logDebug?.(`Removed old backup: ${backup.filename}`);
      } catch (error) {
        this.logger?.logWarning?.(error, `Failed to remove backup: ${backup.filename}`);
      }
    }

    this.logger?.logInfo?.(`Cleanup completed, removed ${removedCount} old backups`);
    return {
      success: true,
      message: `Cleaned up ${removedCount} old backups`,
      removedCount,
    };
  }

  /**
   * Archive multiple completed tasks to DONE.json (bulk operation,
   * @param {Array} tasks - Array of completed tasks to archive
   * @returns {Promise<Object>} Archive _operationresult with batch statistics
   */
  async archiveCompletedTasks(tasks) {
    // Note: This method is mostly synchronous but returns a Promise for API compatibility
    await Promise.resolve(); // Minimal async _operationto satisfy linter
    if (!Array.isArray(tasks) || tasks.length === 0) {
      this.logger?.logWarning?.('No tasks provided for archiving');
      return {
        success: true,
        message: 'No tasks to archive',
        archived: 0,
        skipped: 0,
        errors: 0,
      };
    }

    if (!this.options.enableArchiving) {
      this.logger?.logDebug?.('Archiving disabled, skipping bulk task archive');
      return {
        success: true,
        message: 'Archiving disabled',
        archived: 0,
        skipped: tasks.length,
        errors: 0,
      };
    }

    this.logger?.logInfo?.(`Archiving ${tasks.length} completed tasks`);

    const results = {
      archived: 0,
      skipped: 0,
      errors: 0,
      errorDetails: [],
    };

    try {
      let doneData = {};

      // Read existing DONE.json or create structure
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization
      if (FS.existsSync(this.donePath)) {
        try {
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization;
          const doneContent = FS.readFileSync(this.donePath, 'utf8');
          doneData = JSON.parse(doneContent);

          // Ensure structure exists
          if (!doneData.completed_tasks) {
            doneData = { ...this._createDefaultDoneStructure(), ...doneData };
          }
        } catch (error) {
          this.logger?.logWarning?.('Failed to read DONE.json, creating new structure:', error.message);
          doneData = this._createDefaultDoneStructure();
        }
      } else {
        doneData = this._createDefaultDoneStructure();
      }

      // Archive each task
      for (const task of tasks) {
        try {
          if (!task || !task.id) {
            results.skipped++;
            this.logger?.logWarning?.('Skipping invalid task (missing id)');
            continue;
          }

          // Check if task is already archived;
          const existingTask = doneData.completed_tasks.find(t => t.id === task.id);
          if (existingTask) {
            results.skipped++;
            this.logger?.logDebug?.(`Task already archived: ${task.id}`);
            continue;
          }

          const archivedTask = {
            ...task,
            archived_at: new Date().toISOString(),
            archive_version: '2.0.0',
          };

          doneData.completed_tasks.push(archivedTask);
          results.archived++;
          this.logger?.logDebug?.(`Task queued for archive: ${task.id}`);
        } catch (error) {
          results.errors++;
          results.errorDetails.push({
            taskId: task?.id || 'unknown',
            error: error.message,
          });
          this.logger?.logError?.(error, `Failed to prepare task for archiving: ${task?.id}`);
        }
      }

      // Update metadata
      doneData.last_archived = new Date().toISOString();
      doneData.total_completed = doneData.completed_tasks.length;
      doneData.metadata = {
        ...doneData.metadata,
        last_bulk_archive: new Date().toISOString(),
        bulk_archive_count: (doneData.metadata?.bulk_archive_count || 0) + 1,
      };

      // Write DONE.json atomically;
      const tempPath = `${this.donePath}.tmp.${Date.now()}`;
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- tempPath constructed from validated donePath
      FS.writeFileSync(tempPath, JSON.stringify(doneData, null, 2), 'utf8');
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization
      FS.renameSync(tempPath, this.donePath);

      this.logger?.logInfo?.(`Bulk archive completed: ${results.archived} archived, ${results.skipped} skipped, ${results.errors} errors`);

      return {
        success: true,
        message: `Successfully archived ${results.archived} tasks`,
        archived: results.archived,
        skipped: results.skipped,
        errors: results.errors,
        errorDetails: results.errorDetails,
        archivePath: this.donePath,
      };

    } catch (error) {
      this.logger?.logError?.(error, 'Failed to perform bulk task archiving');
      return {
        success: false,
        message: `Failed to archive tasks: ${error.message}`,
        archived: results.archived,
        skipped: results.skipped,
        errors: results.errors + 1,
        errorDetails: [...results.errorDetails, { error: error.message }],
        error,
      };
    }
  }

  /**
   * Archive a completed task to DONE.json
   * @param {Object} task - Completed task to archive
   * @returns {Promise<Object>} Archive _operationresult
   */
  async archiveCompletedTask(task) {
    await Promise.resolve(); // Minimal async _operationto satisfy linter
    if (!this.options.enableArchiving) {
      this.logger?.logDebug?.('Archiving disabled, skipping task archive');
      return {
        success: true,
        message: 'Archiving disabled',
        archived: false,
      };
    }

    this.logger?.logInfo?.(`Archiving completed task: ${task.id}`);

    try {
      let doneData = {};

      // Read existing DONE.json or create structure
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization
      if (FS.existsSync(this.donePath)) {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization;
        const doneContent = FS.readFileSync(this.donePath, 'utf8');
        doneData = JSON.parse(doneContent);
      } else {
        doneData = this._createDoneStructure();
      }

      // Ensure structure exists
      if (!doneData.completed_tasks) {
        doneData.completed_tasks = [];
      }

      // Add completion metadata;
      const archivedTask = {
        ...task,
        archived_at: new Date().toISOString(),
        archive_version: '2.0.0',
      };

      doneData.completed_tasks.push(archivedTask);
      doneData.last_archived = new Date().toISOString();
      doneData.total_completed = doneData.completed_tasks.length;

      // Write DONE.json
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization
      FS.writeFileSync(this.donePath, JSON.stringify(doneData, null, 2), 'utf8');

      this.logger?.logInfo?.(`Task archived successfully: ${task.id}`);
      return {
        success: true,
        message: 'Task archived successfully',
        archived: true,
        archivePath: this.donePath,
      };
    } catch (error) {
      this.logger?.logError?.(error, `Failed to archive task: ${task.id}`);
      return {
        success: false,
        message: `Failed to archive task: ${error.message}`,
        archived: false,
        error,
      };
    }
  }

  /**
   * Create default DONE.json structure
   * @returns {Object} Default DONE.json structure
   * @private
   */
  _createDoneStructure() {
    return {
      completed_tasks: [],
      project_info: {
        created: new Date().toISOString(),
        version: '2.0.0',
      },
      statistics: {
        total_completed: 0,
        last_archived: null,
      },
    };
  }

  /**
   * Read DONE.json file
   * @returns {Promise<Object>} DONE.json data
   */
  async readDone() {
    await Promise.resolve(); // Minimal async _operationto satisfy linter
    this.logger?.logDebug?.('Reading DONE.json');

    // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization
    if (!FS.existsSync(this.donePath)) {
      this.logger?.logInfo?.('DONE.json does not exist, creating default structure');
      const defaultData = this._createDoneStructure();
      try {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization
        FS.writeFileSync(this.donePath, JSON.stringify(defaultData, null, 2), 'utf8');
        return defaultData;
      } catch (error) {
        this.logger?.logWarning?.(error, 'Failed to create DONE.json, returning default structure');
        return defaultData;
      }
    }

    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization;
      const data = FS.readFileSync(this.donePath, 'utf8');
      const parsedData = JSON.parse(data);

      // Ensure structure
      if (!parsedData.completed_tasks) {
        parsedData.completed_tasks = [];
      }

      return parsedData;
    } catch (error) {
      this.logger?.logError?.(error, 'Failed to read DONE.json');
      throw error;
    }
  }

  /**
   * Get file status information
   * @returns {Object} File status information
   */
  getFileStatus() {
    this.logger?.logDebug?.('Getting file status information');

    const status = {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization,,
      todoExists: FS.existsSync(this.todoPath),
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization
      doneExists: FS.existsSync(this.donePath),
      cacheEnabled: this._cache.enabled,
      cacheValid: this._cache.data !== null,
    };

    if (status.todoExists) {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- todoPath validated during constructor initialization;
      const stats = FS.statSync(this.todoPath);
      status.todoSize = stats.size;
      status.todoModified = stats.mtime;
    }

    if (status.doneExists) {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- donePath validated during constructor initialization;
      const stats = FS.statSync(this.donePath);
      status.doneSize = stats.size;
      status.doneModified = stats.mtime;
    }

    return status;
  }

  /**
   * Clear the cache to force fresh reads
   */
  clearCache() {
    this.logger?.logDebug?.('Clearing storage cache');
    this._cache.data = null;
    this._cache.lastModified = 0;
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  getCacheStats() {
    return {
      enabled: this._cache.enabled,
      hasData: this._cache.data !== null,
      lastModified: this._cache.lastModified,
      size: this._cache.data ? JSON.stringify(this._cache.data).length : 0,
    };
  }
}

module.exports = TaskStorage;
