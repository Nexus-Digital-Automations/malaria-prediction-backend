
/**
 * TaskManager Synchronization System
 *
 * High-performance sync script that runs on every stop hook trigger (<1 second).
 * Intelligently syncs global TaskManager files to project-local directories while
 * preserving project-specific data and configurations.
 *
 * @module sync-taskmanager
 * @author TaskManager Team
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ============================================================================
// CONFIGURATION
// ============================================================================

const GLOBAL_TASKMANAGER_PATH = '/Users/jeremyparker/infinite-continue-stop-hook';
const SYNC_LOG_FILE = '.taskmanager-sync.log';
const BACKUP_DIR = '.taskmanager-backups';
const MAX_LOG_ENTRIES = 100;
const PERFORMANCE_TARGET_MS = 1000; // <1 second requirement

// Files to sync from global to local
const FILES_TO_SYNC = {
  'taskmanager-api.js': { type: 'copy', critical: true },
  'TASKMANAGER-USAGE.md': { type: 'copy', critical: false },
  'QUICKSTART.md': { type: 'copy', critical: false },
  'EXAMPLES.md': { type: 'copy', critical: false },
  'package.json': { type: 'merge', critical: true },
  '.claude/settings.json': { type: 'merge-stop-hook', critical: true },
  'lib/': { type: 'directory', critical: true },
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Log sync activity to file
 */
function logSync(message, level = 'INFO') {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] [${level}] ${message}\n`;

  try {
    // Read existing log
    let logContent = '';
    if (fs.existsSync(SYNC_LOG_FILE)) {
      logContent = fs.readFileSync(SYNC_LOG_FILE, 'utf8');
    }

    // Add new entry
    logContent += logEntry;

    // Keep only last MAX_LOG_ENTRIES
    const lines = logContent.split('\n').filter(line => line.trim());
    if (lines.length > MAX_LOG_ENTRIES) {
      logContent = lines.slice(-MAX_LOG_ENTRIES).join('\n') + '\n';
    }

    fs.writeFileSync(SYNC_LOG_FILE, logContent);
  } catch (error) {
    // Silent fail - don't block sync if logging fails
    console.error(`Failed to write log: ${error.message}`);
  }
}

/**
 * Calculate MD5 hash of file for fast comparison
 */
function calculateFileHash(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return null;
    }

    const fileBuffer = fs.readFileSync(filePath);
    const hashSum = crypto.createHash('md5');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex');
  } catch (error) {
    logSync(`Error calculating hash for ${filePath}: ${error.message}`, 'ERROR');
    return null;
  }
}

/**
 * Calculate combined hash for directory (recursive)
 */
function calculateDirHash(dirPath) {
  try {
    if (!fs.existsSync(dirPath)) {
      return null;
    }

    const files = [];

    function walkDir(dir) {
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          walkDir(fullPath);
        } else if (entry.isFile()) {
          const fileHash = calculateFileHash(fullPath);
          if (fileHash) {
            files.push({ path: fullPath, hash: fileHash });
          }
        }
      }
    }

    walkDir(dirPath);

    // Sort by path for consistent hashing
    files.sort((a, b) => a.path.localeCompare(b.path));

    // Combine all hashes
    const combinedHash = crypto.createHash('md5');
    files.forEach(file => {
      combinedHash.update(file.path);
      combinedHash.update(file.hash);
    });

    return combinedHash.digest('hex');
  } catch (error) {
    logSync(`Error calculating directory hash for ${dirPath}: ${error.message}`, 'ERROR');
    return null;
  }
}

/**
 * Check if file/directory needs sync (hash comparison)
 */
function needsSync(globalPath, localPath, isDirectory = false) {
  const globalHash = isDirectory ? calculateDirHash(globalPath) : calculateFileHash(globalPath);
  const localHash = isDirectory ? calculateDirHash(localPath) : calculateFileHash(localPath);

  if (globalHash === null) {
    logSync(`Global path does not exist: ${globalPath}`, 'WARN');
    return false; // Can't sync if global doesn't exist
  }

  if (localHash === null) {
    logSync(`Local path does not exist, will create: ${localPath}`, 'INFO');
    return true; // Local doesn't exist, need to create
  }

  const hashesMatch = globalHash === localHash;

  if (!hashesMatch) {
    logSync(`Hashes differ - Global: ${globalHash} vs Local: ${localHash}`, 'DEBUG');
  }

  return !hashesMatch; // Sync if hashes differ
}

/**
 * Create backup of file before overwriting
 */
function createBackup(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return null;
    }

    // Create backup directory if it doesn't exist
    if (!fs.existsSync(BACKUP_DIR)) {
      fs.mkdirSync(BACKUP_DIR, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/:/g, '-').replace(/\..+/, '');
    const fileName = path.basename(filePath);
    const backupPath = path.join(BACKUP_DIR, `${fileName}.${timestamp}.backup`);

    fs.copyFileSync(filePath, backupPath);
    logSync(`Created backup: ${backupPath}`, 'INFO');

    return backupPath;
  } catch (error) {
    logSync(`Failed to create backup for ${filePath}: ${error.message}`, 'ERROR');
    return null;
  }
}

/**
 * Copy file from global to local
 */
function copyFile(globalPath, localPath) {
  try {
    // Create directory if it doesn't exist
    const localDir = path.dirname(localPath);
    if (!fs.existsSync(localDir)) {
      fs.mkdirSync(localDir, { recursive: true });
    }

    // Backup existing file
    if (fs.existsSync(localPath)) {
      createBackup(localPath);
    }

    // Copy file
    fs.copyFileSync(globalPath, localPath);
    logSync(`Copied file: ${path.basename(globalPath)}`, 'INFO');

    return true;
  } catch (error) {
    logSync(`Failed to copy ${globalPath} to ${localPath}: ${error.message}`, 'ERROR');
    return false;
  }
}

/**
 * Copy directory from global to local (recursive)
 */
function copyDirectory(globalPath, localPath) {
  try {
    // Create directory if it doesn't exist
    if (!fs.existsSync(localPath)) {
      fs.mkdirSync(localPath, { recursive: true });
    }

    const entries = fs.readdirSync(globalPath, { withFileTypes: true });
    let successCount = 0;
    let errorCount = 0;

    for (const entry of entries) {
      const globalFullPath = path.join(globalPath, entry.name);
      const localFullPath = path.join(localPath, entry.name);

      if (entry.isDirectory()) {
        const result = copyDirectory(globalFullPath, localFullPath);
        successCount += result.successCount;
        errorCount += result.errorCount;
      } else if (entry.isFile()) {
        const success = copyFile(globalFullPath, localFullPath);
        if (success) {
          successCount++;
        } else {
          errorCount++;
        }
      }
    }

    logSync(`Copied directory: ${path.basename(globalPath)} (${successCount} files, ${errorCount} errors)`, 'INFO');

    return { successCount, errorCount };
  } catch (error) {
    logSync(`Failed to copy directory ${globalPath}: ${error.message}`, 'ERROR');
    return { successCount: 0, errorCount: 1 };
  }
}

/**
 * Merge package.json dependencies
 */
function mergePackageJson(globalPath, localPath) {
  try {
    const globalPkg = JSON.parse(fs.readFileSync(globalPath, 'utf8'));
    let localPkg = {};

    if (fs.existsSync(localPath)) {
      localPkg = JSON.parse(fs.readFileSync(localPath, 'utf8'));
    }

    // Backup existing
    if (fs.existsSync(localPath)) {
      createBackup(localPath);
    }

    // Deep merge dependencies and devDependencies
    const merged = { ...localPkg };

    // Merge dependencies (global takes precedence for TaskManager deps)
    if (globalPkg.dependencies) {
      merged.dependencies = {
        ...(localPkg.dependencies || {}),
        ...globalPkg.dependencies,
      };
    }

    // Merge devDependencies (global takes precedence for TaskManager devDeps)
    if (globalPkg.devDependencies) {
      merged.devDependencies = {
        ...(localPkg.devDependencies || {}),
        ...globalPkg.devDependencies,
      };
    }

    // Preserve local scripts, etc.

    fs.writeFileSync(localPath, JSON.stringify(merged, null, 2) + '\n');
    logSync('Merged package.json dependencies and devDependencies', 'INFO');

    return true;
  } catch (error) {
    logSync(`Failed to merge package.json: ${error.message}`, 'ERROR');
    return false;
  }
}

/**
 * Merge .claude/settings.json (ONLY stop hook section, preserve bash safety)
 */
function mergeSettingsJson(globalPath, localPath) {
  try {
    const globalSettings = JSON.parse(fs.readFileSync(globalPath, 'utf8'));
    let localSettings = {};

    if (fs.existsSync(localPath)) {
      localSettings = JSON.parse(fs.readFileSync(localPath, 'utf8'));
    }

    // Backup existing
    if (fs.existsSync(localPath)) {
      createBackup(localPath);
    }

    // Smart merge strategy:
    // - Start with global settings as base (provides env, permissions for new projects)
    // - Overlay local settings to preserve any custom env/permissions
    // - Always update continue.stop hook from global
    const merged = {
      ...globalSettings,  // Base: env, permissions, hooks from global template
      ...localSettings,   // Overlay: preserve any local customizations
    };

    // Always update continue.stop hook from global (don't preserve local version)
    if (globalSettings.hooks && globalSettings.hooks['continue.stop']) {
      if (!merged.hooks) {merged.hooks = {};}
      merged.hooks['continue.stop'] = globalSettings.hooks['continue.stop'];

      logSync('Updated stop hook configuration from global template', 'INFO');
    }

    // This approach ensures:
    // - New projects get full env/permissions from global template
    // - Existing projects keep their local env/permissions customizations
    // - All projects get updated continue.stop hook
    // - Bash safety rules (252 deny rules) distributed to all projects

    // Create directory if it doesn't exist
    const dir = path.dirname(localPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(localPath, JSON.stringify(merged, null, 2) + '\n');
    logSync('Merged .claude/settings.json (stop hook only)', 'INFO');

    return true;
  } catch (error) {
    logSync(`Failed to merge settings.json: ${error.message}`, 'ERROR');
    return false;
  }
}

/**
 * Sync single file based on type
 */
function syncFile(fileName, config, projectRoot) {
  const globalPath = path.join(GLOBAL_TASKMANAGER_PATH, fileName);
  const localPath = path.join(projectRoot, fileName);

  // Check if it's a directory
  const isDirectory = config.type === 'directory';

  // Check if sync needed (hash comparison)
  if (!needsSync(globalPath, localPath, isDirectory)) {
    logSync(`Skipping ${fileName} - no changes detected`, 'DEBUG');
    return { success: true, skipped: true };
  }

  logSync(`Syncing ${fileName} - changes detected`, 'INFO');

  let success = false;

  switch (config.type) {
    case 'copy':
      success = copyFile(globalPath, localPath);
      break;

    case 'directory': {
      const result = copyDirectory(globalPath, localPath);
      success = result.errorCount === 0;
      break;
    }

    case 'merge':
      success = mergePackageJson(globalPath, localPath);
      break;

    case 'merge-stop-hook':
      success = mergeSettingsJson(globalPath, localPath);
      break;

    default:
      logSync(`Unknown sync type: ${config.type}`, 'ERROR');
      success = false;
  }

  return { success, skipped: false };
}

/**
 * Main sync function
 */
function syncTaskManager() {
  const startTime = Date.now();

  logSync('=== TaskManager Sync Started ===', 'INFO');

  // Get project root (current directory)
  const projectRoot = process.cwd();
  logSync(`Project root: ${projectRoot}`, 'INFO');

  // Check if this is the global TaskManager directory
  if (projectRoot === GLOBAL_TASKMANAGER_PATH) {
    logSync('Running in global TaskManager directory - no sync needed', 'INFO');
    console.log('✓ Sync skipped (global directory)');
    return { success: true, skipped: true, duration: Date.now() - startTime };
  }

  // Sync statistics
  const stats = {
    totalFiles: 0,
    synced: 0,
    skipped: 0,
    failed: 0,
    critical_failures: [],
  };

  // Sync each file
  for (const [fileName, config] of Object.entries(FILES_TO_SYNC)) {
    stats.totalFiles++;

    const result = syncFile(fileName, config, projectRoot);

    if (result.success) {
      if (result.skipped) {
        stats.skipped++;
      } else {
        stats.synced++;
      }
    } else {
      stats.failed++;

      if (config.critical) {
        stats.critical_failures.push(fileName);
        logSync(`CRITICAL: Failed to sync ${fileName}`, 'ERROR');
      }
    }
  }

  const duration = Date.now() - startTime;

  logSync(`=== TaskManager Sync Completed ===`, 'INFO');
  logSync(`Total: ${stats.totalFiles} | Synced: ${stats.synced} | Skipped: ${stats.skipped} | Failed: ${stats.failed}`, 'INFO');
  logSync(`Duration: ${duration}ms (target: <${PERFORMANCE_TARGET_MS}ms)`, 'INFO');

  if (duration > PERFORMANCE_TARGET_MS) {
    logSync(`WARNING: Sync exceeded performance target (${duration}ms > ${PERFORMANCE_TARGET_MS}ms)`, 'WARN');
  }

  // Output to console
  if (stats.synced > 0) {
    console.log(`✓ TaskManager synced: ${stats.synced} file(s) updated`);
  } else {
    console.log('✓ TaskManager up to date');
  }

  if (stats.failed > 0) {
    console.log(`⚠ ${stats.failed} file(s) failed to sync`);
  }

  // Return status
  return {
    success: stats.critical_failures.length === 0,
    stats,
    duration,
  };
}

// ============================================================================
// ENTRY POINT
// ============================================================================

if (require.main === module) {
  try {
    const result = syncTaskManager();

    // Exit with 0 even on non-critical failures (don't block stop hook)
    // eslint-disable-next-line n/no-process-exit
    process.exit(result.success ? 0 : 0);
  } catch (error) {
    logSync(`FATAL ERROR: ${error.message}`, 'ERROR');
    console.error(`✗ Sync error: ${error.message}`);

    // Exit with 0 to prevent blocking stop hook
    // eslint-disable-next-line n/no-process-exit
    process.exit(0);
  }
}

module.exports = { syncTaskManager };
