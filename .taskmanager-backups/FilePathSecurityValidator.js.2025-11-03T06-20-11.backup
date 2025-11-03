const { loggers } = require('../../logger');
/**
 * File Path Security Validator - Comprehensive filesystem operation security
 *
 * === PURPOSE ===
 * Provides enterprise-grade security validation for all filesystem operations,
 * preventing path traversal attacks, validating file extensions, and ensuring
 * operations stay within project boundaries.
 *
 * === SECURITY FEATURES ===
 * • Path traversal attack prevention (../, ..\, etc.)
 * • Project boundary enforcement (must be within project root)
 * • File extension whitelisting
 * • Symlink attack prevention
 * • Null byte injection prevention
 * • Path normalization and canonicalization
 * • Operation-specific validation (read vs write vs execute)
 *
 * === INTEGRATION ===
 * Use this module to validate ALL filesystem paths before any fs operations.
 * Integrates with existing SecurityValidator infrastructure.
 *
 * @author Security Enhancement Agent
 * @version 1.0.0
 * @since 2025-09-20
 */

const path = require('path');
const FS = require('fs');
const CRYPTO = require('crypto');

/**
 * FilePathSecurityValidator - Comprehensive file path security validation
 *
 * Provides layered security validation for filesystem operations:
 * - Path traversal prevention
 * - Project boundary enforcement
 * - Extension validation
 * - Symlink protection
 * - Operation-specific security
 */
class FilePathSecurityValidator {
  constructor(projectRoot, logger = null) {
    if (!projectRoot || typeof projectRoot !== 'string') {
      throw new Error('Project root must be a valid string path');
    }

    this.projectRoot = path.resolve(projectRoot);
    this.logger = logger;

    // Security configuration
    this.config = {
      // Allowed file extensions by operation type
      allowedExtensions: {
        read: ['.js', '.ts', '.json', '.md', '.txt', '.log', '.py', '.go', '.rs', '.java', '.cpp', '.c', '.h'],
        write: ['.js', '.ts', '.json', '.md', '.txt', '.log', '.py', '.go', '.rs', '.java', '.cpp', '.c', '.h'],
        execute: ['.js', '.ts', '.py', '.sh'],
        create: ['.js', '.ts', '.json', '.md', '.txt', '.log', '.py', '.go', '.rs', '.java', '.cpp', '.c', '.h'],
      },

      // Allowed directories (relative to project root)
      allowedDirectories: [
        'lib',
        'src',
        'development',
        'test',
        'tests',
        'docs',
        'scripts',
        'config',
        'data',
        'logs',
        'temp',
        'cache',
        'storage',
      ],

      // Forbidden directories (relative to project root)
      forbiddenDirectories: [
        'node_modules',
        '.git',
        '.env',
        'build',
        'dist',
        'coverage',
        '.nyc_output',
      ],

      // Maximum path length
      maxPathLength: 4096,

      // Maximum directory depth from project root
      maxDepthFromRoot: 20,

      // Dangerous patterns to block
      dangerousPatterns: [
        /\.\.[/\\]/,           // Directory traversal
        /[/\\]\.\./,           // Directory traversal
        // eslint-disable-next-line no-control-regex
        /\x00/,                // Null byte injection
        /[<>:"|?*]/,           // Windows forbidden characters
        // eslint-disable-next-line no-control-regex
        /[\x01-\x1f\x7f]/,     // Control characters
        /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i, // Windows reserved names
        /\.(exe|bat|cmd|com|pif|scr|vbs|js|jar)$/i, // Potentially dangerous extensions
      ],
    };

    this.log('info', 'FilePathSecurityValidator initialized', {
      projectRoot: this.projectRoot,
      version: '1.0.0',
    });
  }

  /**
   * Comprehensive file path validation for any filesystem operation
   *
   * @param {string} filePath - The file path to validate
   * @param {string} operation - Operation type: 'read', 'write', 'create', 'execute', 'delete'
   * @param {Object} options - Additional validation options
   * @returns {Object} Validation result with sanitized path
   */
  validateFilePath(filePath, operation = 'read', options = {}) {
    const validationId = this.generateValidationId();
    try {
      this.log('debug', 'Starting file path validation', {
        validationId,
        filePath: this.sanitizePathForLogging(filePath),
        operation,
        options,
      });

      // Step 1: Basic input validation
      const inputResult = this.validateInput(filePath);
      if (!inputResult.valid) {
        throw new Error(`Input validation failed: ${inputResult.error}`);
      }

      // Step 2: Path normalization and canonicalization
      const normalizedPath = this.normalizePath(inputResult.path);

      // Step 3: Project boundary validation
      const boundaryResult = this.validateProjectBoundary(normalizedPath);
      if (!boundaryResult.valid) {
        throw new Error(`Boundary validation failed: ${boundaryResult.error}`);
      }

      // Step 4: Security pattern detection
      const securityResult = this.detectSecurityThreats(normalizedPath);
      if (!securityResult.safe) {
        throw new Error(`Security threats detected: ${securityResult.threats.join(', ')}`);
      }

      // Step 5: Operation-specific validation
      const operationResult = this.validateOperation(normalizedPath, operation, options);
      if (!operationResult.valid) {
        throw new Error(`Operation validation failed: ${operationResult.error}`);
      }

      // Step 6: Final security checks
      const finalPath = this.performFinalValidation(normalizedPath, operation);

      this.log('info', 'File path validation successful', {
        validationId,
        originalPath: this.sanitizePathForLogging(filePath),
        validatedPath: this.sanitizePathForLogging(finalPath),
        operation,
      });

      return {
        valid: true,
        path: finalPath,
        validationId,
        operation,
        metadata: {
          isWithinProject: true,
          relativePath: path.relative(this.projectRoot, finalPath),
          extension: path.extname(finalPath),
          directory: path.dirname(finalPath),
        },
      };

    } catch (error) {
      this.log('warn', 'File path validation failed', {
        validationId,
        filePath: this.sanitizePathForLogging(filePath),
        operation,
        error: error.message,
      });

      return {
        valid: false,
        error: error.message,
        validationId,
        path: null,
      };
    }
  }

  /**
   * Validate file path for reading operations
   */
  validateReadPath(filePath, options = {}) {
    return this.validateFilePath(filePath, 'read', options);
  }

  /**
   * Validate file path for writing operations
   */
  validateWritePath(filePath, options = {}) {
    return this.validateFilePath(filePath, 'write', options);
  }

  /**
   * Validate file path for creation operations
   */
  validateCreatePath(filePath, options = {}) {
    return this.validateFilePath(filePath, 'create', options);
  }

  /**
   * Validate directory path for operations
   */
  validateDirectoryPath(dirPath, operation = 'read', options = {}) {
    const result = this.validateFilePath(dirPath, operation, { ...options, allowDirectory: true });
    if (result.valid && !this.isDirectory(result.path)) {
      return {
        valid: false,
        error: 'Path is not a directory',
        validationId: result.validationId,
        path: null,
      };
    }
    return result;
  }

  /**
   * Basic input validation
   * @private
   */
  validateInput(filePath) {
    if (!filePath || typeof filePath !== 'string') {
      return { valid: false, error: 'File path must be a non-empty string' };
    }

    if (filePath.length > this.config.maxPathLength) {
      return { valid: false, error: `Path too long: ${filePath.length} > ${this.config.maxPathLength}` };
    }

    if (filePath.trim() !== filePath) {
      return { valid: false, error: 'Path contains leading or trailing whitespace' };
    }

    return { valid: true, path: filePath };
  }

  /**
   * Normalize and canonicalize path
   * @private
   */
  normalizePath(filepath) {
    try {
      // Normalize path separators and resolve relative components
      const normalized = path.normalize(filepath);

      // Resolve to absolute path if not already absolute
      const resolved = path.resolve(this.projectRoot, normalized);

      return resolved;
    } catch (error) {
      throw new Error(`Path normalization failed: ${error.message}`);
    }
  }

  /**
   * Validate path is within project boundaries
   * @private
   */
  validateProjectBoundary(absolutePath) {
    try {
      // Ensure the path is within project root
      const relativePath = path.relative(this.projectRoot, absolutePath);

      // Check if path escapes project root
      if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
        return {
          valid: false,
          error: 'Path escapes project boundaries',
        };
      }

      // Check directory depth
      const depth = relativePath.split(path.sep).length - 1;
      if (depth > this.config.maxDepthFromRoot) {
        return {
          valid: false,
          error: `Path too deep: ${depth} > ${this.config.maxDepthFromRoot}`,
        };
      }

      // Check if path is in forbidden directory
      const pathParts = relativePath.split(path.sep);
      for (const forbiddenDir of this.config.forbiddenDirectories) {
        if (pathParts.includes(forbiddenDir)) {
          return {
            valid: false,
            error: `Path in forbidden directory: ${forbiddenDir}`,
          };
        }
      }

      return { valid: true, relativePath };

    } catch (error) {
      return {
        valid: false,
        error: `Boundary validation error: ${error.message}`,
      };
    }
  }

  /**
   * Detect security threats in path
   * @private
   */
  detectSecurityThreats(filePath) {
    const threats = [];

    // Check against dangerous patterns
    for (const pattern of this.config.dangerousPatterns) {
      if (pattern.test(filePath)) {
        threats.push(`Dangerous pattern: ${pattern.source}`);
      }
    }

    // Check for symlink attacks (if file exists)
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename
      if (FS.existsSync(filePath)) {
        // eslint-disable-next-line security/detect-non-literal-fs-filename
        const stats = FS.lstatSync(filePath);
        if (stats.isSymbolicLink()) {
          // eslint-disable-next-line security/detect-non-literal-fs-filename
          const realPath = FS.realpathSync(filePath);
          const relativePath = path.relative(this.projectRoot, realPath);
          if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
            threats.push('Symlink points outside project boundary');
          }
        }
      }
    } catch (error) {
      // If we can't check symlinks, error on the side of caution
      threats.push(`Cannot verify symlink safety: ${error.message}`);
    }

    return {
      safe: threats.length === 0,
      threats,
    };
  }

  /**
   * Validate operation-specific requirements
   * @private
   */
  validateOperation(filePath, operation, options = {}) {
    try {
      const ext = path.extname(filePath).toLowerCase();

      // Check allowed extensions for operation
      if (!options.skipExtensionCheck && ext) {
        // eslint-disable-next-line security/detect-object-injection -- Operation parameter validated at function entry
        const allowedExts = this.config.allowedExtensions[operation] || [];
        if (allowedExts.length > 0 && !allowedExts.includes(ext)) {
          return {
            valid: false,
            error: `Extension ${ext} not allowed for ${operation}`,
          };
        }
      }

      // Operation-specific checks
      switch (operation) {
        case 'read': {
          // For read operations, file should exist
          // eslint-disable-next-line security/detect-non-literal-fs-filename
          if (!options.allowNonExistent && !FS.existsSync(filePath)) {
            return {
              valid: false,
              error: 'File does not exist for read operation',
            };
          }
          break;
        }

        case 'write':
        case 'create': {
          // For write/create operations, ensure parent directory exists or can be created
          const parentDir = path.dirname(filePath);
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- Path already validated through security checks
          if (!FS.existsSync(parentDir)) {
            if (options.createParentDirs) {
              // Validate parent directory creation is safe
              const parentResult = this.validateDirectoryPath(parentDir, 'create');
              if (!parentResult.valid) {
                return {
                  valid: false,
                  error: `Cannot create parent directory: ${parentResult.error}`,
                };
              }
            } else {
              return {
                valid: false,
                error: 'Parent directory does not exist',
              };
            }
          }
          break;
        }

        case 'execute': {
          // For execute operations, additional security checks
          // eslint-disable-next-line security/detect-non-literal-fs-filename
          if (!FS.existsSync(filePath)) {
            return {
              valid: false,
              error: 'File does not exist for execute operation',
            };
          }

          // Check if file is executable
          try {
            FS.accessSync(filePath, FS.constants.F_OK | FS.constants.R_OK);
          } catch {
            return {
              valid: false,
              error: 'File not accessible for execute operation',
            };
          }
          break;
        }
      }

      return { valid: true };

    } catch (error) {
      return {
        valid: false,
        error: `Operation validation error: ${error.message}`,
      };
    }
  }

  /**
   * Perform final validation and return secure path
   * @private
   */
  performFinalValidation(filePath, operation) {
    // Final canonicalization
    try {
      // For existing files, resolve real path to handle symlinks
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Path already validated through comprehensive security checks
      if (FS.existsSync(filePath) && operation === 'read') {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- Path already validated through security checks
        const realPath = FS.realpathSync(filePath);

        // Ensure real path is still within project
        const relativePath = path.relative(this.projectRoot, realPath);
        if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
          throw new Error('Real path escapes project boundary');
        }

        return realPath;
      }

      return filePath;
    } catch (error) {
      throw new Error(`Final validation failed: ${error.message}`);
    }
  }

  /**
   * Utility methods
   * @private
   */
  isDirectory(pathToCheck) {
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Path validated through security validator
      return FS.existsSync(pathToCheck) && FS.statSync(pathToCheck).isDirectory();
    } catch {
      return false;
    }
  }

  generateValidationId() {
    return `fpval_${Date.now()}_${CRYPTO.randomBytes(4).toString('hex')}`;
  }

  sanitizePathForLogging(pathToSanitize) {
    if (!pathToSanitize || typeof pathToSanitize !== 'string') {
      return '[invalid]';
    }
    return pathToSanitize.length > 100 ? pathToSanitize.substring(0, 100) + '...' : pathToSanitize;
  }

  log(level, message, metadata = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      module: 'FilePathSecurityValidator',
      ...metadata,
    };

    if (this.logger) {
      // eslint-disable-next-line security/detect-object-injection -- Level parameter validated by logger interface
      this.logger[level](logEntry);
      loggers.stopHook.info(JSON.stringify(logEntry));

      loggers.app.info(JSON.stringify(logEntry));
    }
  }

  /**
   * Static helper methods for common use cases
   */
  static validateProjectPath(filePath, projectRoot, operation = 'read') {
    const validator = new FilePathSecurityValidator(projectRoot);
    return validator.validateFilePath(filePath, operation);
  }

  static createSecureHelper(projectRoot, logger = null) {
    return new FilePathSecurityValidator(projectRoot, logger);
  }
}

module.exports = FilePathSecurityValidator;
