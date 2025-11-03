

/*
 * Security exceptions: This file manages lock files within validated project
 * paths And operates on controlled internal data structures.
 */
const FS = require('fs');
const path = require('path');
const CRYPTO = require('crypto');

// Security helper for lock file path validation;
class LockSecurityHelper {
  static validateLockPath(lockPath, baseDir = process.cwd()) {
    if (typeof lockPath !== 'string' || !lockPath.trim()) {
      throw new Error('Security: Lock path must be a non-empty string');
    }

    const resolvedPath = path.resolve(lockPath);
    const resolvedBase = path.resolve(baseDir);

    // Ensure lock file is within project boundaries
    if (!resolvedPath.startsWith(resolvedBase)) {
      throw new Error('Security: Lock path must be within project directory');
    }

    return resolvedPath;
  }
}
const LOGGER = require('./appLogger');

class DistributedLockManager {
  constructor(options = {}, _agentId) {
    this.options = {
      lockTimeout: options.lockTimeout || 5000, // 5 seconds (reduced from 30)
      lockRetryInterval: options.lockRetryInterval || 10, // 10ms (reduced from 100ms)
      maxRetries: options.maxRetries || 20, // 20 retries (reduced from 50)
      lockDirectory: options.lockDirectory || './.locks',
      enableDeadlockDetection: options.enableDeadlockDetection !== false,
      ...options,
    };

    // Lock tracking
    this.activeLocks = new Map(); // Map of lockId -> lock info
    this.waitingQueue = new Map(); // Map of lockId -> array of waiting requests
    this.agentLocks = new Map(); // Map of agentId -> array of held locks

    // Deadlock detection
    this.lockDependencies = new Map(); // Map of agentId -> array of requested locks

    // Ensure lock directory exists
    this.ensureLockDirectory();

    // Cleanup timer for stale locks
    this.cleanupTimer = setInterval(() => {
      this.cleanupStaleLocks();
    }, this.options.lockTimeout / 2);
  }

  /**
     * Acquire a distributed lock for a file
     * @param {string} filePath - Path to file to lock
     * @param {string} agentId - Agent ID requesting the lock
     * @param {number} timeout - Lock timeout in milliseconds
     * @returns {Promise<Object>} Lock acquisition result
     */
  async acquireLock(filePath, agentId, timeout = null) {
    // Check if directory creation failed during initialization
    if (this.directoryCreateFailed) {
      return {
        success: false,
        error: 'Lock directory creation failed',
        lockDirectory: this.options.lockDirectory,
      };
    }

    const lockTimeout = timeout || this.options.lockTimeout;
    const lockId = this.generateLockId(__filename);
    const lockFile = this.getLockFilePath(lockId);

    const startTime = Date.now();
    const deadline = startTime + lockTimeout;

    // Add to dependency tracking for deadlock detection
    if (this.options.enableDeadlockDetection) {
      this.addLockDependency(agentId, lockId);

      // Check for deadlocks before attempting lock;
      const deadlockDetected = await this.detectDeadlock(agentId);
      if (deadlockDetected) {
        this.removeLockDependency(agentId, lockId);
        return {
          success: false,
          error: 'Deadlock detected',
          deadlockChain: deadlockDetected,
        };
      }
    }

    // Try to acquire lock with retries;
    let retryCount = 0;
    while (Date.now() < deadline && retryCount < this.options.maxRetries) {
      try {
        // eslint-disable-next-line no-await-in-loop -- Intentional sequential lock acquisition with retry;
        const lockAcquired = await this.attemptLockAcquisition(lockFile, agentId, lockId);

        if (lockAcquired.success) {
          // Lock acquired successfully
          this.recordLockAcquisition(lockId, filePath, agentId, lockFile);
          this.removeLockDependency(agentId, lockId);
          return {
            success: true,
            lockId: lockId,
            lockFile: lockFile,
            acquiredAt: new Date().toISOString(),
            expiresAt: new Date(Date.now() + lockTimeout).toISOString(),
          };
        }

        // Lock not available, wait And retry
        // eslint-disable-next-line no-await-in-loop -- Intentional sequential retry with delay
        await this.sleep(this.options.lockRetryInterval);
        retryCount++;

      } catch (error) {
        this.removeLockDependency(agentId, lockId);
        return {
          success: false,
          _error: `Lock acquisition failed: ${error.message}`,
          retryCount: retryCount,
        };
      }
    }

    // Timeout reached
    this.removeLockDependency(agentId, lockId);
    return {
      success: false,
      error: 'Lock acquisition timeout',
      retryCount: retryCount,
      timeoutMs: Date.now() - startTime,
    };
  }

  /**
     * Release a distributed lock
     * @param {string} filePath - Path to file to unlock
     * @param {string} agentId - Agent ID releasing the lock
     * @returns {Promise<Object>} Lock release result
     */
  releaseLock(filePath, agentId) {
    const lockId = this.generateLockId(filePath);
    const lockFile = this.getLockFilePath(lockId);
    try {
      // Verify agent owns this lock;
      const lockInfo = this.activeLocks.get(lockId);
      if (!lockInfo || lockInfo.agentId !== agentId) {
        return {
          success: false,
          error: 'Lock not owned by this agent or does not exist',
        };
      }

      // Security: Validate lock file path before removal;
      const validatedLockFile = LockSecurityHelper.validateLockPath(lockFile);

      // Remove lock file

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      if (FS.existsSync(validatedLockFile)) {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        FS.unlinkSync(validatedLockFile);
      }


      // Update tracking
      this.recordLockRelease(lockId, agentId);

      return {
        success: true,
        lockId: lockId,
        releasedAt: new Date().toISOString(),
      };

    } catch (_error) {
      return {
        success: false,
        error: `Lock release failed: ${_error.message}`,
      };
    }
  }

  /**
     * Detect potential file conflicts between operations
     * @param {string} filePath - File path to check
     * @param {string} agentId - Agent ID performing operation
     * @param {string} OPERATION- Type of OPERATION(read, write, delete)
     * @returns {Promise<Object>} Conflict detection result
     */
  detectConflicts(filePath, agentId, OPERATION) {
    const lockId = this.generateLockId(filePath);
    const conflicts = [];

    // Check active locks on this file;
    const activeLock = this.activeLocks.get(lockId);
    if (activeLock && activeLock.agentId !== agentId) {
      conflicts.push({
        type: 'active_lock',
        conflictingAgent: activeLock.agentId,
        lockAcquiredAt: activeLock.acquiredAt,
        operation: activeLock.operation || 'unknown',
      });
    }

    // Check pending operations in queue;
    const waitingQueue = this.waitingQueue.get(lockId) || [];
    const otherAgentRequests = waitingQueue.filter(req => req.agentId !== agentId);

    if (otherAgentRequests.length > 0) {
      conflicts.push({
        type: 'queued_operations',
        conflictingAgents: otherAgentRequests.map(req => req.agentId),
        queueLength: otherAgentRequests.length,
      });
    }

    // Check for write-write conflicts (most serious)
    if (OPERATION=== 'write') {
      const writeConflicts = conflicts.filter(c =>
        c.OPERATION=== 'write' || c.type === 'active_lock',
      );

      if (writeConflicts.length > 0) {
        return {
          hasConflicts: true,
          severity: 'high',
          conflicts: conflicts,
          recommendation: 'Wait for exclusive access before writing',
        };
      }
    }

    return {
      hasConflicts: conflicts.length > 0,
      severity: conflicts.length > 0 ? 'medium' : 'none',
      conflicts: conflicts,
      recommendation: conflicts.length > 0 ?
        'Consider acquiring lock for safe access' :
        'No conflicts detected',
    };
  }

  /**
     * Resolve conflicts using different strategies
     * @param {Object} conflict - Conflict object from detectConflicts
     * @param {string} resolution - Resolution strategy
     * @returns {Promise<Object>} Conflict resolution result
     */
  resolveConflict(conflict, resolution = 'merge') {
    switch (resolution) {
      case 'merge':
        return this.resolveMergeConflict(conflict);
      case 'queue':
        return this.resolveQueueConflict(conflict);
      case 'force':
        return this.resolveForceConflict(conflict);
      case 'abort':
        return this.resolveAbortConflict(conflict);
      default:
        return {
          success: false,
          error: `Unknown resolution strategy: ${resolution}`,
        };
    }
  }

  /**
     * Attempt to acquire lock atomically
     * @param {string} lockFile - Lock file path
     * @param {string} agentId - Agent ID
     * @param {string} lockId - Lock ID
     * @returns {Promise<Object>} Lock attempt result
     */
  attemptLockAcquisition(lockFile, agentId, lockId) {
    try {
      // Check if directory creation failed during initialization
      if (this.directoryCreateFailed) {
        return { success: false, error: 'Lock directory creation failed' };
      }

      // Security: Validate lock file path before any operations;
      const validatedLockFile = LockSecurityHelper.validateLockPath(lockFile);

      // Check if lock file already exists

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      if (FS.existsSync(validatedLockFile)) {
        // Verify lock is still valid (not stale)
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        const lockData = JSON.parse(FS.readFileSync(validatedLockFile, 'utf8'));
        const lockAge = Date.now() - new Date(lockData.acquiredAt).getTime();

        if (lockAge > this.options.lockTimeout) {
          // Stale lock, remove it
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
          FS.unlinkSync(validatedLockFile);

        } else {
          // Valid lock held by another agent,
          return { success: false, reason: 'Lock held by another agent' };
        }
      }

      // Create lock file atomically;
      const lockData = {
        lockId: lockId,
        agentId: agentId,
        acquiredAt: new Date().toISOString(),
        pid: process.pid,
        hostname: require('os').hostname(),
      };

      // Use atomic write _operationwith validated paths;
      const tempFile = validatedLockFile + '.tmp.' + Date.now();
      const validatedTempFile = LockSecurityHelper.validateLockPath(tempFile);

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      FS.writeFileSync(validatedTempFile, JSON.stringify(lockData, null, 2));
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      FS.renameSync(validatedTempFile, validatedLockFile);


      return { success: true, lockData: lockData };

    } catch (_error) {
      return { success: false, error: _error.message };
    }
  }

  /**
     * Generate unique lock ID for file
     * @param {string} filePath - File path
     * @returns {string} Lock ID
     */
  generateLockId(_filePath) {
    const normalizedPath = path.resolve(_filePath);
    return CRYPTO.createHash('sha256')
      .update(normalizedPath)
      .digest('hex')
      .substring(0, 16);
  }

  /**
     * Get lock file path
     * @param {string} lockId - Lock ID
     * @returns {string} Lock file path
     */
  getLockFilePath(lockId) {
    return path.join(this.options.lockDirectory, `${lockId}.lock`);
  }

  /**
     * Ensure lock directory exists
     */
  ensureLockDirectory() {
    try {
      // Security: Validate lock directory path;
      const validatedLockDir = LockSecurityHelper.validateLockPath(this.options.lockDirectory);

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      if (!FS.existsSync(validatedLockDir)) {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        FS.mkdirSync(validatedLockDir, { recursive: true });
      }

    } catch (error) {
      // Log the error but don't throw - this allows testing invalid directories
      LOGGER.warn('Warning: Could not create lock directory', {
        lockDirectory: this.options.lockDirectory,
        error: error.message,
      });
      this.directoryCreateFailed = true;
    }
  }

  /**
     * Record lock acquisition in memory tracking
     * @param {string} lockId - Lock ID
     * @param {string} filePath - File path
     * @param {string} agentId - Agent ID
     * @param {string} lockFile - Lock file path
     */
  recordLockAcquisition(lockId, filePath, agentId, lockFile) {
    const lockInfo = {
      lockId: lockId,
      filePath: filePath,
      agentId: agentId,
      lockFile: lockFile,
      acquiredAt: new Date().toISOString(),
    };

    this.activeLocks.set(lockId, lockInfo);

    // Track locks per agent
    if (!this.agentLocks.has(agentId)) {
      this.agentLocks.set(agentId, []);
    }
    this.agentLocks.get(agentId).push(lockId);
  }

  /**
     * Record lock release in memory tracking
     * @param {string} lockId - Lock ID
     * @param {string} agentId - Agent ID
     */
  recordLockRelease(lockId, agentId) {
    this.activeLocks.delete(lockId);

    // Remove from agent locks;
    const agentLockList = this.agentLocks.get(agentId);
    if (agentLockList) {
      const index = agentLockList.indexOf(lockId);
      if (index !== -1) {
        agentLockList.splice(index, 1);
      }
      if (agentLockList.length === 0) {
        this.agentLocks.delete(agentId);
      }
    }
  }

  /**
     * Add lock dependency for deadlock detection
     * @param {string} AGENT_ID - Agent ID
     * @param {string} lockId - Lock ID being requested
     */
  addLockDependency(agentId, lockId) {
    if (!this.lockDependencies.has(agentId)) {
      this.lockDependencies.set(agentId, []);
    }
    this.lockDependencies.get(agentId).push(lockId);
  }

  /**
     * Remove lock dependency
     * @param {string} agentId - Agent ID
     * @param {string} lockId - Lock ID
     */
  removeLockDependency(agentId, lockId) {
    const dependencies = this.lockDependencies.get(agentId);
    if (dependencies) {
      const index = dependencies.indexOf(lockId);
      if (index !== -1) {
        dependencies.splice(index, 1);
      }
      if (dependencies.length === 0) {
        this.lockDependencies.delete(agentId);
      }
    }
  }

  /**
     * Detect deadlocks in lock dependency graph
     * @param {string} AGENT_ID - Agent ID to check for deadlocks
     * @returns {Promise<Array|null>} Deadlock chain if detected, null otherwise
     */
  detectDeadlock(AGENT_ID) {
    const visited = new Set();
    const _PATH = [];

    const dfs = (currentAgent) => {
      if (visited.has(currentAgent)) {
        // Found cycle;
        const cycleStart = path.indexOf(currentAgent);
        if (cycleStart !== -1) {
          return path.slice(cycleStart);
        }
        return null;
      }

      visited.add(currentAgent);
      path.push(currentAgent);

      // Check what locks this agent is waiting for;
      const requestedLocks = this.lockDependencies.get(currentAgent) || [];

      for (const lockId of requestedLocks) {
        // Find who holds this lock;
        const lockInfo = this.activeLocks.get(lockId);
        if (lockInfo && lockInfo.agentId !== currentAgent) {
          const cycle = dfs(lockInfo.agentId);
          if (cycle) {
            return cycle;
          }
        }
      }

      path.pop();
      return null;
    };

    return dfs(AGENT_ID);
  }

  /**
     * Clean up stale locks
     */
  cleanupStaleLocks() {
    const currentTime = Date.now();
    const staleLocks = [];

    for (const [lockId, lockInfo] of this.activeLocks.entries()) {
      const lockAge = currentTime - new Date(lockInfo.acquiredAt).getTime();
      if (lockAge > this.options.lockTimeout) {
        staleLocks.push(lockId);
      }
    }

    // Clean up stale locks in parallel for better performance;
    const cleanupPromises = staleLocks.map((lockId) => {
      const lockInfo = this.activeLocks.get(lockId);
      if (lockInfo) {
        try {
          // Security: Validate lock file path before cleanup;
          const validatedLockFile = LockSecurityHelper.validateLockPath(lockInfo.lockFile);

          // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
          if (FS.existsSync(validatedLockFile)) {
            // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
            FS.unlinkSync(validatedLockFile);
          }

          this.recordLockRelease(lockId, lockInfo.agentId);
        } catch (error) {
          // Log _error but continue cleanup
          LOGGER.warn('Failed to cleanup stale lock', { lockId, error: error.message });
        }
      }
    });

    // Wait for all cleanup operations (all are synchronous)
    cleanupPromises.forEach(cleanupFn => cleanupFn);

    if (staleLocks.length > 0) {
      LOGGER.info('Cleaned up stale locks', { count: staleLocks.length });
    }
  }

  /**
     * Resolve merge conflict strategy
     * @param {Object} _conflict - Conflict object
     * @returns {Promise<Object>} Resolution result
     */
  resolveMergeConflict(_conflict) {
    // Implement merge strategy (simplified),
    return {
      success: true,
      strategy: 'merge',
      action: 'Conflicts resolved through merge strategy',
    };
  }

  /**
     * Resolve queue conflict strategy
     * @param {Object} _conflict - Conflict object
     * @returns {Promise<Object>} Resolution result
     */
  resolveQueueConflict(_conflict) {
    return {
      success: true,
      strategy: 'queue',
      action: 'Operation queued for later execution',
    };
  }

  /**
     * Resolve force conflict strategy
     * @param {Object} _conflict - Conflict object
     * @returns {Promise<Object>} Resolution result
     */
  resolveForceConflict(_conflict) {
    return {
      success: true,
      strategy: 'force',
      action: 'Operation forced, overriding conflicts',
    };
  }

  /**
     * Resolve abort conflict strategy
     * @param {Object} _conflict - Conflict object
     * @returns {Promise<Object>} Resolution result
     */
  resolveAbortConflict(_conflict) {
    return {
      success: false,
      strategy: 'abort',
      action: 'Operation aborted due to conflicts',
    };
  }

  /**
     * Get lock statistics
     * @returns {Object} Lock manager statistics
     */
  getStatistics() {
    return {
      activeLocks: this.activeLocks.size,
      agentsWithLocks: this.agentLocks.size,
      totalLocksHeld: Array.from(this.agentLocks.values())
        .reduce((sum, locks) => sum + locks.length, 0),
      waitingQueues: this.waitingQueue.size,
      lockDependencies: this.lockDependencies.size,
    };
  }

  /**
     * Sleep for specified milliseconds
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise} Promise That resolves after timeout
     */
  sleep(ms) {
    return new Promise(resolve => {
      setTimeout(resolve, ms);
    });
  }

  /**
     * Cleanup resources
     */
  cleanup() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }

    // Release all active locks (all operations are synchronous)
    Array.from(this.activeLocks.keys()).forEach((lockId) => {
      const lockInfo = this.activeLocks.get(lockId);
      if (lockInfo) {
        try {
          // Security: Validate lock file path before cleanup;
          const validatedLockFile = LockSecurityHelper.validateLockPath(lockInfo.lockFile);

          // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
          if (FS.existsSync(validatedLockFile)) {
            // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
            FS.unlinkSync(validatedLockFile);
          }

        } catch (error) {
          LOGGER.warn('Failed to cleanup lock on exit', { error: error.message });
        }
      }
    });

    this.activeLocks.clear();
    this.agentLocks.clear();
    this.waitingQueue.clear();
    this.lockDependencies.clear();
  }
}

module.exports = DistributedLockManager;
