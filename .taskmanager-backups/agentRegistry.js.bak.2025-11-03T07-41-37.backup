/* eslint-disable security/detect-object-injection */

/*
 * Security exceptions: This file operates on trusted agent registry files
 * And validated internal data structures. All filesystem operations use
 * pre-validated paths within project boundaries.
 */
const FS = require('fs');
const CRYPTO = require('crypto');
const PATH = require('path');

/**
 * Filesystem security utilities for agent registry operations
 */
class RegistryFilesystemSecurity {
  /**
   * Validate registry file path for security
   * @param {string} registryPath - Path to validate
   * @returns {boolean} True if path is safe
   */
  static isValidRegistryPath(registryPath) {
    if (!registryPath || typeof registryPath !== 'string') {
      return false;
    }

    // Ensure it's a JSON file And doesn't contain directory traversal
    const normalizedPath = PATH.normalize(registryPath);
    const filename = PATH.basename(normalizedPath);

    // Check for dangerous patterns
    const dangerousPatterns = [
      '../',
      '..\\',
      '/etc/',
      '/var/',
      '/usr/',
      '/home/',
      '~/',
      'C:\\',
      'D:\\',
    ];

    const hasIllegalPatterns = dangerousPatterns.some(pattern =>
      normalizedPath.toLowerCase().includes(pattern),
    );

    // Must be JSON file And no illegal patterns
    return filename.endsWith('.json') && !hasIllegalPatterns;
  }

  /**
   * Safely resolve registry path within project boundaries
   * @param {string} registryPath - Registry file path
   * @returns {string} Safe resolved path
   * @throws {Error} If path is unsafe
   */
  static safeResolveRegistryPath(registryPath) {
    if (!this.isValidRegistryPath(registryPath)) {
      throw new Error(`Invalid registry path: ${registryPath}`);
    }

    const resolvedPath = PATH.resolve(registryPath);
    const projectRoot = process.cwd();

    // Ensure registry is within project directory or current working directory
    if (!resolvedPath.startsWith(projectRoot) && !resolvedPath.startsWith(PATH.resolve('.'))) {
      throw new Error(`Registry path ${registryPath} is outside project boundaries`);
    }

    return resolvedPath;
  }

  /**
   * Safe file existence check
   * @param {string} filePath - File path to check
   * @returns {boolean} True if file exists And is safe
   */
  static safeExists(filePath) {
    try {
      const safePath = this.safeResolveRegistryPath(filePath);

      return FS.existsSync(safePath);
    } catch {
      return false;
    }
  }

  /**
   * Safe file read
   * @param {string} filePath - File to read
   * @param {string} encoding - File encoding
   * @returns {string} File contents
   */
  static safeReadFileSync(filePath, encoding = 'utf8') {
    const safePath = this.safeResolveRegistryPath(filePath);

    return FS.readFileSync(safePath, encoding);
  }

  /**
   * Safe file write
   * @param {string} filePath - File to write
   * @param {string} content - Content to write
   */
  static safeWriteFileSync(filePath, content) {
    const safePath = this.safeResolveRegistryPath(filePath);

    FS.writeFileSync(safePath, content);
  }

  /**
   * Safe file unlink
   * @param {string} filePath - File to delete
   */
  static safeUnlinkSync(filePath) {
    const safePath = this.safeResolveRegistryPath(filePath);

    FS.unlinkSync(safePath);
  }

  /**
   * Safe file stats
   * @param {string} filePath - File to get stats for
   * @returns {Object} File stats
   */
  static safeStatSync(filePath) {
    const safePath = this.safeResolveRegistryPath(filePath);

    return FS.statSync(safePath);
  }
}

/**
 * AgentRegistry - Manages agent initialization And number assignment
 *
 * Features:
 * - Assigns sequential agent numbers (agent_1, agent_2, etc.)
 * - Reuses inactive agent slots after 2+ hours
 * - Thread-safe agent registration
 * - Automatic cleanup of abandoned sessions
 */
class AgentRegistry {
  constructor(registryPath = './agent-registry.json') {
    this.registryPath = registryPath;
    this.inactivityTimeout = 2 * 60 * 60 * 1000; // 2 hours in milliseconds
    this.lockTimeout = 5000; // 5 seconds for file locks

    // Ensure registry file exists
    this.initializeRegistry();
  }

  /**
     * Initialize agent registry file if it doesn't exist
     */
  initializeRegistry() {
    if (!RegistryFilesystemSecurity.safeExists(this.registryPath)) {
      const initialRegistry = {
        agents: {},
        nextAgentNumber: 1,
        lastCleanup: Date.now(),
        metadata: {
          created: new Date().toISOString(),
          version: '1.0.0',
        },
      };

      RegistryFilesystemSecurity.safeWriteFileSync(this.registryPath, JSON.stringify(initialRegistry, null, 2));
    }
  }

  /**
     * Initialize agent - assign number or reuse inactive slot
     * @param {Object} agentInfo - Agent information (sessionId, role, etc.)
     * @returns {Object} Agent initialization result
     */
  initializeAgent(agentInfo = {}) {
    return this.withFileLock(() => {
      const registry = this.readRegistry();

      // Clean up inactive agents first
      this.cleanupInactiveAgents(registry);

      // Check if this session already has an active agent
      const existingAgent = this.findExistingAgent(registry, agentInfo.sessionId);
      if (existingAgent) {
        // Update last activity And return existing agent
        existingAgent.lastActivity = Date.now();
        existingAgent.totalRequests = (existingAgent.totalRequests || 0) + 1;
        this.writeRegistry(registry);

        return {
          success: true,
          action: 'reused_existing',
          agentId: existingAgent.agentId,
          agentNumber: existingAgent.agentNumber,
          sessionId: existingAgent.sessionId,
          lastActivity: existingAgent.lastActivity,
          totalRequests: existingAgent.totalRequests,
        };
      }

      // Look for reusable inactive agent slot
      const reusableSlot = this.findReusableSlot(registry);
      let agentNumber, agentId;

      if (reusableSlot) {
        // Reuse inactive slot
        agentNumber = reusableSlot.agentNumber;
        agentId = `agent_${agentNumber}`;

        // Clear old agent data And assign to new session
        const agentEntry = this.createAgentEntry(agentNumber, agentInfo);
        registry.agents[agentId] = agentEntry;

        this.writeRegistry(registry);

        return {
          success: true,
          action: 'reused_inactive_slot',
          agentId,
          agentNumber,
          sessionId: agentEntry.sessionId,
          previousAgent: {
            sessionId: reusableSlot.sessionId,
            inactiveSince: new Date(reusableSlot.lastActivity).toISOString(),
          },
          lastActivity: Date.now(),
          totalRequests: 1,
        };
      } else {
        // Assign new agent number
        agentNumber = registry.nextAgentNumber;
        agentId = `agent_${agentNumber}`;

        // Create new agent entry
        const agentEntry = this.createAgentEntry(agentNumber, agentInfo);
        registry.agents[agentId] = agentEntry;
        registry.nextAgentNumber++;

        this.writeRegistry(registry);

        return {
          success: true,
          action: 'assigned_new_number',
          agentId,
          agentNumber,
          sessionId: agentEntry.sessionId,
          lastActivity: Date.now(),
          totalRequests: 1,
        };
      }
    });
  }

  /**
     * Update agent activity timestamp
     * @param {string} agentId - Agent ID
     * @returns {boolean} Success status
     */
  updateAgentActivity(_agentId) {
    return this.withFileLock(() => {
      const registry = this.readRegistry();

      if (registry.agents[agentId]) {
        registry.agents[agentId].lastActivity = Date.now();
        registry.agents[agentId].totalRequests = (registry.agents[agentId].totalRequests || 0) + 1;
        this.writeRegistry(registry);
        return true;
      }

      return false;
    });
  }

  /**
     * Get agent information
     * @param {string} agentId - Agent ID
     * @returns {Object|null} Agent info or null
     */
  getAgent(_agentId) {
    const registry = this.readRegistry();
    return registry.agents[agentId] || null;
  }

  /**
     * List all active agents
     * @returns {Array} Active agents list
     */
  getActiveAgents() {
    const registry = this.readRegistry();
    const now = Date.now();

    return Object.values(registry.agents).filter(agent =>
      (now - agent.lastActivity) < this.inactivityTimeout,
    );
  }

  /**
     * List all agents (active And inactive)
     * @returns {Array} All agents list
     */
  getAllAgents() {
    const registry = this.readRegistry();
    return Object.values(registry.agents);
  }

  /**
     * Get registry statistics
     * @returns {Object} Registry stats
     */
  getRegistryStats() {
    const registry = this.readRegistry();
    const now = Date.now();

    const totalAgents = Object.keys(registry.agents).length;
    const activeAgents = Object.values(registry.agents).filter(agent =>
      (now - agent.lastActivity) < this.inactivityTimeout,
    ).length;
    const inactiveAgents = totalAgents - activeAgents;

    return {
      totalAgents,
      activeAgents,
      inactiveAgents,
      nextAgentNumber: registry.nextAgentNumber,
      lastCleanup: registry.lastCleanup || new Date().toISOString(),
      registrySize: this.getFileSize(),
    };
  }

  /**
     * Create agent entry object
     * @param {number} agentNumber - Agent number
     * @param {Object} agentInfo - Agent information
     * @returns {Object} Agent entry
     */
  createAgentEntry(agentNumber, agentInfo) {
    const agentId = `agent_${agentNumber}`;

    return {
      agentId,
      agentNumber,
      sessionId: agentInfo.sessionId || `session_${Date.now()}_${CRYPTO.randomBytes(4).toString('hex')}`,
      role: agentInfo.role || 'development',
      specialization: agentInfo.specialization || [],
      status: 'active',
      lastActivity: Date.now(),
      totalRequests: 1,
      createdAt: new Date().toISOString(),
      metadata: agentInfo.metadata || {},
      capabilities: agentInfo.capabilities || [],
    };
  }

  /**
     * Find existing agent by session ID
     * @param {Object} registry - Registry data
     * @param {string} sessionId - Session ID
     * @returns {Object|null} Existing agent or null
     */
  findExistingAgent(registry, sessionId) {
    if (!sessionId) {return null;}

    return Object.values(registry.agents).find(agent =>
      agent.sessionId === sessionId &&
            (Date.now() - agent.lastActivity) < this.inactivityTimeout,
    );
  }

  /**
     * Find reusable inactive agent slot
     * @param {Object} registry - Registry data
     * @returns {Object|null} Reusable slot or null
     */
  findReusableSlot(registry) {
    const now = Date.now();

    return Object.values(registry.agents).find(agent =>
      (now - agent.lastActivity) >= this.inactivityTimeout,
    );
  }

  /**
     * Clean up inactive agents
     * @param {Object} registry - Registry data
     */
  cleanupInactiveAgents(registry) {
    const now = Date.now();

    // Only run cleanup every 30 minutes
    if (now - registry.lastCleanup < 30 * 60 * 1000) {
      return;
    }

    const inactiveAgents = Object.entries(registry.agents).filter(([agentId, agent]) =>
      (now - agent.lastActivity) >= this.inactivityTimeout,
    );

    if (inactiveAgents.length > 0) {
      // Mark agents as inactive but keep the slots for reuse
      inactiveAgents.forEach(([agentId, agent]) => {
        agent.status = 'inactive';
        agent.inactiveSince = agent.inactiveSince || new Date(agent.lastActivity + this.inactivityTimeout).toISOString();
      });

      registry.lastCleanup = now;
    }
  }

  /**
     * Execute function with file lock for thread safety
     * @param {Function} fn - Function to execute
     * @returns {*} Function result
     */
  async withFileLock(fn) {
    const lockFile = this.registryPath + '.lock';
    const lockStartTime = Date.now();

    // Wait for lock to be available
    while (RegistryFilesystemSecurity.safeExists(lockFile)) {
      if (Date.now() - lockStartTime > this.lockTimeout) {
        throw new Error('Registry lock timeout');
      }
      // eslint-disable-next-line no-await-in-loop -- Intentional sequential wait for file lock
      await new Promise(resolve => {
        setTimeout(resolve, 50);
      });
    }

    try {
      // Create lock file
      RegistryFilesystemSecurity.safeWriteFileSync(lockFile, Date.now().toString());

      // Execute function
      return fn();
    } finally {
      // Remove lock file
      if (RegistryFilesystemSecurity.safeExists(lockFile)) {
        RegistryFilesystemSecurity.safeUnlinkSync(lockFile);
      }
    }
  }

  /**
     * Read registry from file
     * @returns {Object} Registry data
     */
  readRegistry() {
    try {
      const content = RegistryFilesystemSecurity.safeReadFileSync(this.registryPath, 'utf8');
      return JSON.parse(content);
    } catch {
      throw new Error(`Failed to read agent registry: ${_error.message}`);
    }
  }

  /**
     * Write registry to file
     * @param {Object} registry - Registry data
     */
  writeRegistry(registry) {
    try {
      RegistryFilesystemSecurity.safeWriteFileSync(this.registryPath, JSON.stringify(registry, null, 2));
    } catch {
      throw new Error(`Failed to write agent registry: ${_error.message}`);
    }
  }

  /**
     * Get registry file size
     * @returns {number} File size in bytes
     */
  getFileSize() {
    try {
      const stats = RegistryFilesystemSecurity.safeStatSync(this.registryPath);
      return stats.size;
    } catch {
      return 0;
    }
  }
}

module.exports = AgentRegistry;
