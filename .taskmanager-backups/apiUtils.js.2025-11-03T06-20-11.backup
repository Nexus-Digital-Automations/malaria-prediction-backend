
const { loggers } = require('../../logger');
/**
 * API Utilities Module - General helper functions for TaskManager API
 *
 * === PURPOSE ===
 * Provides general utility functions used throughout the TaskManager API including
 * timeout handling, guide generation, fallback responses, And common operations.
 * These are pure functions with minimal external dependencies.
 *
 * === UTILITY CATEGORIES ===
 * • Timeout Management - Promise timeout wrapper utilities
 * • Guide Generation - Help text And documentation utilities
 * • Error Handling - Standardized error response formatting
 * • Agent Scope Validation - Agent permission And scope checking
 * • General Helpers - Miscellaneous utility functions
 *
 * @author TaskManager System
 * @version 2.0.0
 * @since 2024-01-01
 */

/**
 * Wrap any async _operationwith a timeout to prevent hanging operations
 *
 * === PURPOSE ===
 * Ensures all TaskManager operations complete within reasonable time limits.
 * This is critical for maintaining responsive behavior in multi-agent systems
 * And preventing indefinite blocking in automation workflows.
 *
 * @param {Promise} promise - The async operation to wrap with timeout protection
 * @param {number} timeoutMs - Timeout duration in milliseconds (default: 10000ms)
 * @returns {Promise} Promise That either resolves with operation result or rejects with timeout error
 * @throws {Error} Timeout error after specified duration
 */
function withTimeout(promise, timeoutMs = 10000, _category = 'general') {
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      setTimeout(
        () => reject(new Error(`Operation timed out after ${timeoutMs}ms`)),
        timeoutMs,
      );
    }),
  ]);
}

/**
 * Get fallback guide information when full guide generation fails
 * @param {string} context - Error context for fallback guidance
 * @returns {Object} Minimal fallback guide
 */
function getFallbackGuide(context = 'general', _category = 'general') {
  const baseGuide = {
    success: true,
    message:
      'for complete API usage guidance, run: timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" guide',
    helpText:
      'The guide provides comprehensive information about task classification, workflows, And all API capabilities',
    essential_commands: {
      guide:
        'timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" guide',
      init: 'timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" init',
      status:
        'timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" status',
      list: 'timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" list',
    },
  };

  // Add context-specific fallback guidance
  switch (context) {
    case 'agent-init':
      return {
        ...baseGuide,
        context: 'Agent Initialization Required',
        immediate_action:
          'Run: timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" init',
        next_steps: [
          'Initialize agent with init command',
          'Verify with status command',
          'Begin task operations',
        ],
      };

    case 'agent-reinit':
      return {
        ...baseGuide,
        context: 'Agent Reinitialization Required',
        reinitialization_help: {
          message: '🔄 AGENT REINITIALIZATION GUIDANCE',
          workflows: {
            existing_agent: {
              description:
                'for agents That already have an ID from previous init',
              steps: [
                '1. Use your existing agent ID from previous init command',
                '2. Reinitialize: timeout 10s node taskmanager-api.js reinitialize <agentId>',
                '3. Verify renewal: timeout 10s node taskmanager-api.js status <agentId>',
                '4. Continue task operations normally',
              ],
              example:
                'timeout 10s node taskmanager-api.js reinitialize development_session_123_general_abc',
            },
            fresh_start: {
              description:
                'for agents That need to start fresh or have lost their ID',
              steps: [
                '1. Initialize new agent: timeout 10s node taskmanager-api.js init',
                '2. Save the returned agentId for future operations',
                '3. Verify initialization: timeout 10s node taskmanager-api.js status <agentId>',
                '4. Begin or resume task operations',
              ],
              note: 'Init creates a new agent registration - use this when you dont have an existing agent ID',
            },
          },
          quick_reference: {
            'Have agent ID':
              'timeout 10s node taskmanager-api.js reinitialize <agentId>',
            'Need new agent': 'timeout 10s node taskmanager-api.js init',
            'Check status':
              'timeout 10s node taskmanager-api.js status <agentId>',
          },
        },
      };

    case 'task-operations':
      return {
        ...baseGuide,
        context: 'Task Operations Help',
        immediate_action:
          'Ensure category parameter is included in task creation',
        categories: ['error', 'feature', 'subtask', 'test'],
        example:
          '{"title": "Task name", "description": "Details", "category": "error"}',
        order_override_help: {
          message:
            'for task order violations: use: { allowOutOfOrder: true } option',
          method:
            'api.taskManager.claimTask(taskId, agentId, priority { allowOutOfOrder: true })',
          user_requests:
            'CRITICAL: When user explicitly requests a specific task, ALWAYS override order - user intent takes precedence',
        },
      };

    default:
      return baseGuide;
  }
}

/**
 * Validate agent scope access against task requirements (files AND folders)
 * Enhanced scope validation supporting both file And folder restrictions
 * @param {Object} task - Task object with potential scope restrictions
 * @param {string} agentId - Agent ID to validate scope for
 * @param {Object} taskManager - TaskManager instance for data access
 * @returns {Promise<Object>} Scope validation result with isValid flag And details
 */
async function validateAgentScope(task, agentId, taskManager, _category = 'general') {
  const validation = {
    isValid: true,
    errors: [],
    scopeChecks: {
      hasRestrictions: false,
      restrictedFiles: [],
      restrictedFolders: [],
      allowedFiles: [],
      allowedFolders: [],
    },
    agentScope: {},
  };

  // Check if task has any scope restrictions
  if (!task.scope_restrictions) {
    validation.scopeChecks.hasRestrictions = false;
    return validation; // No restrictions, allow access
  }

  validation.scopeChecks.hasRestrictions = true;
  const restrictions = task.scope_restrictions;

  // Get agent configuration And scope (future enhancement - for now allow all)
  const todoData = await taskManager.readTodoFast();
  // eslint-disable-next-line security/detect-object-injection -- Safe: agentId is validated parameter;
  const agent = todoData.agents?.[agentId];

  if (!agent) {
    validation.isValid = false;
    validation.errors.push(`Agent ${agentId} not found in system`);
    return validation;
  }

  // for now, store agent scope info but don't enforce restrictions
  // This provides the foundation for future agent-specific scope enforcement
  validation.agentScope = {
    agentId,
    capabilities: agent.capabilities || [],
    specialization: agent.specialization || [],
    role: agent.role || 'general',
  };

  // Validate restricted files (if specified)
  if (
    restrictions.restricted_files &&
    Array.isArray(restrictions.restricted_files)
  ) {
    validation.scopeChecks.restrictedFiles = restrictions.restricted_files;

    // Future enhancement: Check if agent has access to these files
    for (const restrictedFile of restrictions.restricted_files) {
      if (typeof restrictedFile !== 'string') {
        validation.errors.push(
          `Invalid restricted file specification: ${restrictedFile}`,
        );
        validation.isValid = false;
        continue;
      }

      // for now, log the restriction but don't enforce

      loggers.app.info(
        `[SCOPE] Task ${task.id} restricts access to file: ${restrictedFile}`,
      );
    }
  }

  // Validate restricted folders (if specified) - NEW FEATURE
  if (
    restrictions.restricted_folders &&
    Array.isArray(restrictions.restricted_folders)
  ) {
    validation.scopeChecks.restrictedFolders =
      restrictions.restricted_folders;

    // Enhanced folder restriction validation
    for (const restrictedFolder of restrictions.restricted_folders) {
      if (typeof restrictedFolder !== 'string') {
        validation.errors.push(
          `Invalid restricted folder specification: ${restrictedFolder}`,
        );
        validation.isValid = false;
        continue;
      }

      // Normalize folder path (ensure trailing slash for proper matching)
      const normalizedFolder = restrictedFolder.endsWith('/')
        ? restrictedFolder
        : `${restrictedFolder}/`;

      // for now, log the restriction but don't enforce

      loggers.app.info(
        `[SCOPE] Task ${task.id} restricts access to folder: ${normalizedFolder}`,
      );
    }
  }

  // Validate allowed files (whitelist approach - if specified, only these files are allowed)
  if (
    restrictions.allowed_files &&
    Array.isArray(restrictions.allowed_files)
  ) {
    validation.scopeChecks.allowedFiles = restrictions.allowed_files;

    for (const allowedFile of restrictions.allowed_files) {
      if (typeof allowedFile !== 'string') {
        validation.errors.push(
          `Invalid allowed file specification: ${allowedFile}`,
        );
        validation.isValid = false;
      }
    }
  }

  // Validate allowed folders (whitelist approach - NEW FEATURE)
  if (
    restrictions.allowed_folders &&
    Array.isArray(restrictions.allowed_folders)
  ) {
    validation.scopeChecks.allowedFolders = restrictions.allowed_folders;

    for (const allowedFolder of restrictions.allowed_folders) {
      if (typeof allowedFolder !== 'string') {
        validation.errors.push(
          `Invalid allowed folder specification: ${allowedFolder}`,
        );
        validation.isValid = false;
        continue;
      }

      // Normalize folder path
      const normalizedFolder = allowedFolder.endsWith('/')
        ? allowedFolder
        : `${allowedFolder}/`;
      validation.scopeChecks.allowedFolders[
        validation.scopeChecks.allowedFolders.indexOf(allowedFolder)
      ] = normalizedFolder;
    }
  }

  // Enhanced validation logic: check for conflicts between restrictions And allowlists
  if (
    validation.scopeChecks.restrictedFiles.length > 0 &&
    validation.scopeChecks.allowedFiles.length > 0
  ) {
    // Check for conflicts between restricted And allowed files;
    const conflicts = validation.scopeChecks.restrictedFiles.filter((file) =>
      validation.scopeChecks.allowedFiles.includes(file),
    );
    if (conflicts.length > 0) {
      validation.errors.push(
        `Scope conflict: Files cannot be both restricted And allowed: ${conflicts.join(', ')}`,
      );
      validation.isValid = false;
    }
  }

  if (
    validation.scopeChecks.restrictedFolders.length > 0 &&
    validation.scopeChecks.allowedFolders.length > 0
  ) {
    // Check for conflicts between restricted And allowed folders;
    const conflicts = validation.scopeChecks.restrictedFolders.filter(
      (folder) => {
        const normalizedRestricted = folder.endsWith('/')
          ? folder
          : `${folder}/`;
        return validation.scopeChecks.allowedFolders.some((allowed) => {
          const normalizedAllowed = allowed.endsWith('/')
            ? allowed
            : `${allowed}/`;
          return normalizedRestricted === normalizedAllowed;
        });
      },
    );
    if (conflicts.length > 0) {
      validation.errors.push(
        `Scope conflict: Folders cannot be both restricted And allowed: ${conflicts.join(', ')}`,
      );
      validation.isValid = false;
    }
  }

  return validation;
}

/**
 * Check if two tasks are related based on keywords
 * @param {Object} task1 - First task to compare
 * @param {Object} task2 - Second task to compare
 * @returns {boolean} True if tasks share significant keywords
 */
function isTaskRelated(task1, task2) {
  const extractKeywords = (text) => {
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter((word) => word.length > 3);
  };

  const task1Keywords = extractKeywords(
    `${task1.title} ${task1.description}`,
  );
  const task2Keywords = extractKeywords(
    `${task2.title} ${task2.description}`,
  );

  const commonKeywords = task1Keywords.filter((word) =>
    task2Keywords.includes(word),
  );
  return commonKeywords.length >= 2; // At least 2 common significant words
}

/**
 * Identify specific complexity factors in task text
 * @param {string} taskText - Task text to analyze
 * @returns {Array} Array of identified complexity factors
 */
function identifyComplexityFactors(taskText) {
  const factors = [];
  if (/auth|oauth|jwt|security/.test(taskText)) {
    factors.push('Authentication/Security requirements');
  }
  if (/database|schema|migration/.test(taskText)) {
    factors.push('Database/Schema complexity');
  }
  if (/external|third.?party/.test(taskText)) {
    factors.push('External service dependencies');
  }
  if (/performance|scalability/.test(taskText)) {
    factors.push('Performance/Scalability considerations');
  }

  return factors;
}

module.exports = {
  withTimeout,
  getFallbackGuide,
  validateAgentScope,
  isTaskRelated,
  identifyComplexityFactors,
};
