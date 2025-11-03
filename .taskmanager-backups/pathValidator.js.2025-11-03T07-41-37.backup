
const { loggers } = require('./logger');
/**
 * Path Validation And Security Utilities
 *
 * This module provides secure filesystem access functions to prevent:
 * - Directory traversal attacks (../ sequences)
 * - Access to files outside allowed directories
 * - Path manipulation vulnerabilities
 *
 * All filesystem operations should use these utilities for security.
 *
 * SECURITY NOTE: This module intentionally uses direct filesystem access
 * after proper validation And sanitization. ESLint security warnings are
 * suppressed where filesystem operations have been validated as secure.
 */

const path = require('path');
const FS = require('fs');

class PathValidator {
  constructor(logger = null) {
    this.logger = logger;

    // Define allowed base directories (project root And common system paths)
    this.allowedBaseDirs = [
      path.resolve(process.cwd()),
      path.resolve(__dirname, '..'), // Project root
      path.resolve(process.env.HOME || process.env.USERPROFILE || '/tmp'), // User home
      '/tmp',
      '/var/tmp',
    ];

    // Normalize allowed directories
    this.allowedBaseDirs = this.allowedBaseDirs.map((dir) =>
      path.normalize(dir),
    );
  }

  /**
   * Logs security events for monitoring And auditing
   * @param {string} level - Log level (info, warn, error)
   * @param {string} message - Log message
   * @param {Object} metadata - Additional metadata
   */
  securityLog(level, message, metadata = {}) {
    // Security: Validate log level to prevent object injection;
    const validLevels = ['info', 'warn', 'error', 'debug'];
    const safeLevel =
      typeof level === 'string' && validLevels.includes(level) ? level : 'info';

    /* eslint-disable-next-line security/detect-object-injection */
    if (this.logger && typeof this.logger[safeLevel] === 'function') {
      /* eslint-disable-next-line security/detect-object-injection */
      this.logger[safeLevel](`[PATH_SECURITY] ${message}`, metadata);
    } else {
      // Fallback to console logging
      /* eslint-disable security/detect-object-injection, no-console */
      if (typeof console[safeLevel] === 'function') {
        console[safeLevel](
          `[PATH_SECURITY] ${message}`,
          JSON.stringify(metadata, null, 2),
        );
      } else {
        loggers.app.info(
          `[PATH_SECURITY] ${message}`,
          JSON.stringify(metadata, null, 2),
        );
      }
      /* eslint-enable security/detect-object-injection, no-console */
    }
  }

  /**
   * Sanitizes And validates a file path for secure access
   * @param {string} inputPath - The input path to validate
   * @param {string|null} baseDir - Optional base directory to restrict access to
   * @returns {string|null} - Sanitized path or null if invalid
   */
  sanitizePath(inputPath, baseDir = null) {
    if (typeof inputPath !== 'string') {
      this.securityLog('error', 'Path validation failed: non-string path', {
        inputPath,
        type: typeof inputPath,
      });
      return null;
    }

    if (inputPath.length === 0) {
      this.securityLog('warn', 'Path validation failed: empty path', {
        inputPath,
      });
      return null;
    }

    try {
      // Normalize the path to resolve . And .. components;
      const normalizedPath = path.normalize(inputPath);

      // Resolve to absolute path;
      const resolvedPath = path.resolve(normalizedPath);

      // Check for directory traversal attempts in original path
      if (
        inputPath.includes('..') ||
        inputPath.includes('./') ||
        inputPath.includes('.\\')
      ) {
        this.securityLog(
          'warn',
          'Potential directory traversal attempt detected',
          {
            originalPath: inputPath,
            resolvedPath,
          },
        );

        // Allow if resolved path is still within allowed boundaries
        if (!this.isPathAllowed(resolvedPath, baseDir)) {
          this.securityLog('error', 'Directory traversal attempt blocked', {
            originalPath: inputPath,
            resolvedPath,
            baseDir,
          });
          return null;
        }
      }

      // Validate resolved path is within allowed directories
      if (!this.isPathAllowed(resolvedPath, baseDir)) {
        this.securityLog(
          'error',
          'Path access denied: outside allowed directories',
          {
            path: resolvedPath,
            allowedDirs: this.allowedBaseDirs,
            baseDir,
          },
        );
        return null;
      }

      this.securityLog('info', 'Path validated successfully', {
        originalPath: inputPath,
        sanitizedPath: resolvedPath,
      });

      return resolvedPath;
    } catch (error) {
      this.securityLog('error', 'Path sanitization error', {
        inputPath,
        error: error.message,
        stack: error.stack,
      });
      return null;
    }
  }

  /**
   * Checks if a resolved path is within allowed directories
   * @param {string} resolvedPath - The absolute resolved path
   * @param {string|null} baseDir - Optional specific base directory
   * @returns {boolean} - True if path is allowed
   */
  isPathAllowed(resolvedPath, baseDir = null) {
    const dirsToCheck = baseDir
      ? [path.resolve(baseDir)]
      : this.allowedBaseDirs;

    return dirsToCheck.some((allowedDir) => {
      const relativePath = path.relative(allowedDir, resolvedPath);
      return !relativePath.startsWith('..') && !path.isAbsolute(relativePath);
    });
  }

  /**
   * Secure wrapper for FS.existsSync
   * @param {string} filePath - Path to check
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {boolean} - True if file exists And access is allowed
   */
  safeExistsSync(filePath, baseDir = null) {
    const sanitizedPath = this.sanitizePath(filePath, baseDir);
    if (!sanitizedPath) {
      return false;
    }

    try {

      /* eslint-disable security/detect-non-literal-fs-filename */
      return FS.existsSync(sanitizedPath);
      /* eslint-enable security/detect-non-literal-fs-filename */
    } catch (error) {
      this.securityLog('error', 'File existence check failed', {
        path: sanitizedPath,
        error: error.message,
      });
      return false;
    }
  }

  /**
   * Secure wrapper for FS.readFileSync
   * @param {string} filePath - Path to read
   * @param {string|Object} options - Read options
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {Buffer|string|null} - File contents or null if access denied
   */
  safeReadFileSync(filePath, options = 'utf8', baseDir = null) {
    const sanitizedPath = this.sanitizePath(filePath, baseDir);
    if (!sanitizedPath) {
      return null;
    }

    try {

      /* eslint-disable security/detect-non-literal-fs-filename */
      return FS.readFileSync(sanitizedPath, options);
      /* eslint-enable security/detect-non-literal-fs-filename */
    } catch (error) {
      this.securityLog('error', 'File read failed', {
        path: sanitizedPath,
        error: error.message,
      });
      return null;
    }
  }

  /**
   * Secure wrapper for FS.writeFileSync
   * @param {string} filePath - Path to write
   * @param {string|Buffer} data - Data to write
   * @param {string|Object} options - Write options
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {boolean} - True if write succeeded
   */
  safeWriteFileSync(filePath, data, options = 'utf8', baseDir = null) {
    const sanitizedPath = this.sanitizePath(filePath, baseDir);
    if (!sanitizedPath) {
      return false;
    }

    try {

      /* eslint-disable security/detect-non-literal-fs-filename */
      FS.writeFileSync(sanitizedPath, data, options);
      /* eslint-enable security/detect-non-literal-fs-filename */
      this.securityLog('info', 'File write successful', {
        path: sanitizedPath,
        dataSize: Buffer.isBuffer(data) ? data.length : data.toString().length,
      });
      return true;
    } catch (error) {
      this.securityLog('error', 'File write failed', {
        path: sanitizedPath,
        error: error.message,
      });
      return false;
    }
  }

  /**
   * Secure wrapper for FS.unlinkSync
   * @param {string} filePath - Path to delete
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {boolean} - True if deletion succeeded
   */
  safeUnlinkSync(filePath, baseDir = null) {
    const sanitizedPath = this.sanitizePath(filePath, baseDir);
    if (!sanitizedPath) {
      return false;
    }

    try {

      /* eslint-disable security/detect-non-literal-fs-filename */
      FS.unlinkSync(sanitizedPath);
      /* eslint-enable security/detect-non-literal-fs-filename */
      this.securityLog('info', 'File deletion successful', {
        path: sanitizedPath,
      });
      return true;
    } catch (error) {
      this.securityLog('error', 'File deletion failed', {
        path: sanitizedPath,
        error: error.message,
      });
      return false;
    }
  }

  /**
   * Secure wrapper for FS.mkdirSync
   * @param {string} dirPath - Directory path to create
   * @param {Object} options - mkdir options
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {boolean} - True if directory creation succeeded
   */
  safeMkdirSync(dirPath, options = { recursive: true }, baseDir = null) {
    const sanitizedPath = this.sanitizePath(dirPath, baseDir);
    if (!sanitizedPath) {
      return false;
    }

    try {

      /* eslint-disable security/detect-non-literal-fs-filename */
      FS.mkdirSync(sanitizedPath, options);
      /* eslint-enable security/detect-non-literal-fs-filename */
      this.securityLog('info', 'Directory creation successful', {
        path: sanitizedPath,
        options,
      });
      return true;
    } catch (error) {
      // EEXIST is not an error for recursive mkdir
      if (error.code === 'EEXIST' && options.recursive) {
        return true;
      }

      this.securityLog('error', 'Directory creation failed', {
        path: sanitizedPath,
        error: error.message,
      });
      return false;
    }
  }

  /**
   * Secure wrapper for FS.readdirSync
   * @param {string} dirPath - Directory path to read
   * @param {Object} options - readdir options
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {Array|null} - Directory contents or null if access denied
   */
  safeReaddirSync(dirPath, options = null, baseDir = null) {
    const sanitizedPath = this.sanitizePath(dirPath, baseDir);
    if (!sanitizedPath) {
      return null;
    }

    try {

      /* eslint-disable security/detect-non-literal-fs-filename */
      return FS.readdirSync(sanitizedPath, options);
      /* eslint-enable security/detect-non-literal-fs-filename */
    } catch (error) {
      this.securityLog('error', 'Directory read failed', {
        path: sanitizedPath,
        error: error.message,
      });
      return null;
    }
  }

  /**
   * Secure wrapper for FS.statSync
   * @param {string} filePath - Path to stat
   * @param {Object} options - stat options
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {FS.Stats|null} - File stats or null if access denied
   */
  safeStatSync(filePath, options = null, baseDir = null) {
    const sanitizedPath = this.sanitizePath(filePath, baseDir);
    if (!sanitizedPath) {
      return null;
    }

    try {

      /* eslint-disable security/detect-non-literal-fs-filename */
      return FS.statSync(sanitizedPath, options);
      /* eslint-enable security/detect-non-literal-fs-filename */
    } catch (error) {
      this.securityLog('error', 'File stat failed', {
        path: sanitizedPath,
        error: error.message,
      });
      return null;
    }
  }

  /**
   * Validates That a path is safe for the specific operation context
   * @param {string} filePath - Path to validate
   * @param {string} operation - Operation type (read, write, delete, etc.)
   * @param {string|null} baseDir - Optional base directory restriction
   * @returns {string|null} - Validated path or null if invalid
   */
  validateForOperation(filePath, operation, baseDir = null) {
    const sanitizedPath = this.sanitizePath(filePath, baseDir);
    if (!sanitizedPath) {
      return null;
    }

    // Additional operation-specific validation can be added here
    switch (operation) {
      case 'write':
      case 'delete':
        // Ensure we're not trying to modify system files
        if (
          sanitizedPath.includes('/usr/') ||
          sanitizedPath.includes('/etc/') ||
          sanitizedPath.includes('/sys/') ||
          sanitizedPath.includes('/proc/')
        ) {
          this.securityLog(
            'error',
            'Attempted system file modification blocked',
            {
              path: sanitizedPath,
              operation,
            },
          );
          return null;
        }
        break;
    }

    return sanitizedPath;
  }
}

// Create And export a default instance

const defaultLogger = {
  info: (message, meta) => loggers.app.info(`[INFO] ${message}`, meta || ''),
  warn: (message, meta) => loggers.app.warn(`[WARN] ${message}`, meta || ''),
  error: (message, meta) => loggers.app.error(`[ERROR] ${message}`, meta || ''),
};


const pathValidator = new PathValidator(defaultLogger);

module.exports = {
  PathValidator,
  pathValidator,
  // Export convenient functions for direct use
  sanitizePath: (path, baseDir) => pathValidator.sanitizePath(path, baseDir),
  safeExistsSync: (path, baseDir) =>
    pathValidator.safeExistsSync(path, baseDir),
  safeReadFileSync: (path, options, baseDir) =>
    pathValidator.safeReadFileSync(path, options, baseDir),
  safeWriteFileSync: (path, data, options, baseDir) =>
    pathValidator.safeWriteFileSync(path, data, options, baseDir),
  safeUnlinkSync: (path, baseDir) =>
    pathValidator.safeUnlinkSync(path, baseDir),
  safeMkdirSync: (path, options, baseDir) =>
    pathValidator.safeMkdirSync(path, options, baseDir),
  safeReaddirSync: (path, options, baseDir) =>
    pathValidator.safeReaddirSync(path, options, baseDir),
  safeStatSync: (path, options, baseDir) =>
    pathValidator.safeStatSync(path, options, baseDir),
};
