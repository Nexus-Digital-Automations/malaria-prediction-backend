
const { loggers } = require('../../logger');

/**
 * CLI Interface Module - Command-line argument parsing And execution for TaskManager API
 *
 * === PURPOSE ===
 * Handles all command-line interface operations for the TaskManager API including:
 * • Command parsing And validation
 * • Argument extraction And JSON parsing
 * • Command execution delegation
 * • Error handling with contextual guidance
 * • CLI output formatting
 *
 * === COMMAND CATEGORIES ===
 * • Discovery Commands - guide, methods, help
 * • Agent Lifecycle - init, reinitialize, status, list-agents
 * • Task Operations - create, list, claim, complete, delete
 * • Task Management - move-top, move-up, move-down, move-bottom
 * • Feature Management - suggest-feature, approve-feature, reject-feature
 * • Phase Management - create-phase, update-phase, progress-phase
 * • Agent Swarm - get-tasks (self-organizing agent coordination)
 *
 * === ARCHITECTURE ===
 * This module acts as the translation layer between CLI commands And API methods.
 * Each CLI command maps to one or more TaskManagerAPI methods with proper
 * argument parsing, validation, And error handling.
 *
 * @author TaskManager System
 * @version 2.0.0
 * @since 2024-01-01
 */

// Import the utility modules we've already created;
const _apiUtils = require('../utils/apiUtils');

/**
 * Parse And execute CLI command with comprehensive error handling
 * @param {TaskManagerAPI} api - TaskManager API instance
 * @param {Array} args - Command line arguments (already processed)
 * @returns {Promise<void>} Command execution result via console output
 * @throws {Error} If command execution fails with contextual guidance
 */
async function executeCommand(api, args, _category = 'general') {
  const command = args[0];
  try {
    switch (command) {
      case 'methods': {
        const _result = await api.getApiMethods();
        loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
        loggers.app.info(JSON.stringify(_result, null, 2));
        break;
      }

      case 'guide': {
        const _result = await api.getComprehensiveGuide();
        loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
        loggers.app.info(JSON.stringify(_result, null, 2));
        break;
      }

      case 'init': {
        await _handleInitCommand(api, args);
        break;
      }

      case 'reinitialize': {
        await _handleReinitializeCommand(api, args);
        break;
      }

      case 'list-agents': {
        const _result = await api.listAgents();
        loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
        loggers.app.info(JSON.stringify(_result, null, 2));
        break;
      }

      case 'status': {
        await _handleStatusCommand(api, args);
        break;
      }

      case 'current': {
        await _handleCurrentCommand(api, args);
        break;
      }

      case 'stats': {
        const _result = await api.getStats();
        loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
        loggers.app.info(JSON.stringify(_result, null, 2));
        break;
      }

      case 'usage-analytics': {
        const options = {};
        const _result = await api.getUsageAnalytics(options);
        loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
        loggers.app.info(JSON.stringify(_result, null, 2));
        break;
      }

      case 'list': {
        await _handleListCommand(api, args);
        break;
      }

      case 'create': {
        await _handleCreateCommand(api, args);
        break;
      }

      case 'create-error': {
        await _handleCreateErrorCommand(api, args);
        break;
      }

      case 'analyze-phase-insertion': {
        await _handleAnalyzePhaseInsertionCommand(api, args);
        break;
      }

      case 'claim': {
        await _handleClaimCommand(api, args);
        break;
      }

      case 'complete': {
        await _handleCompleteCommand(api, args);
        break;
      }

      case 'delete': {
        await _handleDeleteCommand(api, args);
        break;
      }

      case 'move-top': {
        await _handleMoveTopCommand(api, args);
        break;
      }

      case 'move-up': {
        await _handleMoveUpCommand(api, args);
        break;
      }

      case 'move-down': {
        await _handleMoveDownCommand(api, args);
        break;
      }

      case 'move-bottom': {
        await _handleMoveBottomCommand(api, args);
        break;
      }

      case 'suggest-feature': {
        await _handleSuggestFeatureCommand(api, args);
        break;
      }

      case 'approve-feature': {
        await _handleApproveFeatureCommand(api, args);
        break;
      }

      case 'reject-feature': {
        await _handleRejectFeatureCommand(api, args);
        break;
      }

      case 'list-suggested-features': {
        const _result = await api.listSuggestedFeatures();
        loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
        loggers.app.info(JSON.stringify(_result, null, 2));
        break;
      }

      case 'list-features': {
        await _handleListFeaturesCommand(api, args);
        break;
      }

      case 'feature-stats': {
        const _result = await api.getFeatureStats();
        loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
        loggers.app.info(JSON.stringify(_result, null, 2));
        break;
      }

      case 'create-phase': {
        await _handleCreatePhaseCommand(api, args);
        break;
      }

      case 'update-phase': {
        await _handleUpdatePhaseCommand(api, args);
        break;
      }

      case 'progress-phase': {
        await _handleProgressPhaseCommand(api, args);
        break;
      }

      case 'list-phases': {
        await _handleListPhasesCommand(api, args);
        break;
      }

      case 'current-phase': {
        await _handleCurrentPhaseCommand(api, args);
        break;
      }

      case 'phase-stats': {
        await _handlePhaseStatsCommand(api, args);
        break;
      }

      case 'get-tasks': {
        await _handleGetTasksCommand(api, args);
        break;
      }

      case 'create-subtask': {
        await _handleCreateSubtaskCommand(api, args);
        break;
      }

      case 'list-subtasks': {
        await _handleListSubtasksCommand(api, args);
        break;
      }

      case 'update-subtask': {
        await _handleUpdateSubtaskCommand(api, args);
        break;
      }

      case 'delete-subtask': {
        await _handleDeleteSubtaskCommand(api, args);
        break;
      }

      case 'add-success-criteria': {
        await _handleAddSuccessCriteriaCommand(api, args);
        break;
      }

      case 'get-success-criteria': {
        await _handleGetSuccessCriteriaCommand(api, args);
        break;
      }

      case 'update-success-criteria': {
        await _handleUpdateSuccessCriteriaCommand(api, args);
        break;
      }

      case 'set-project-criteria': {
        await _handleSetProjectCriteriaCommand(api, args);
        break;
      }

      case 'validate-criteria': {
        await _handleValidateCriteriaCommand(api, args);
        break;
      }

      case 'criteria-report': {
        await _handleCriteriaReportCommand(api, args);
        break;
      }

      case 'research-task': {
        await _handleResearchTaskCommand(api, args);
        break;
      }

      case 'audit-task': {
        await _handleAuditTaskCommand(api, args);
        break;
      }

      // RAG Operations - Lessons And Error Database
      case 'store-lesson': {
        await _handleStoreLessonCommand(api, args);
        break;
      }

      case 'store-error': {
        await _handleStoreErrorCommand(api, args);
        break;
      }

      case 'search-lessons': {
        await _handleSearchLessonsCommand(api, args);
        break;
      }

      case 'find-similar-errors': {
        await _handleFindSimilarErrorsCommand(api, args);
        break;
      }

      case 'get-relevant-lessons': {
        await _handleGetRelevantLessonsCommand(api, args);
        break;
      }

      case 'rag-analytics': {
        await _handleRagAnalyticsCommand(api, args);
        break;
      }

      // RAG Command Aliases (for CLAUDE.md compatibility)
      case 'rag-health': {
        await _handleRagAnalyticsCommand(api, args);
        break;
      }

      case 'rag-search': {
        await _handleSearchLessonsCommand(api, args);
        break;
      }

      case 'rag-similar-errors': {
        await _handleFindSimilarErrorsCommand(api, args);
        break;
      }

      case 'rag-get-relevant': {
        await _handleGetRelevantLessonsCommand(api, args);
        break;
      }

      case 'rag-store-lesson': {
        await _handleStoreLessonCommand(api, args);
        break;
      }

      default: {
        // Display help for unknown commands
        await displayHelp();
        break;
      }
    }
  } catch (error) {
    throw await enhanceErrorWithContext(api, error, command);
  }
}

/**
 * Handle agent initialization command with config parsing
 */
async function _handleInitCommand(api, args) {
  let config = {};
  if (args[1]) {
    try {
      config = JSON.parse(args[1]);
    } catch (error) {
      throw new Error(`Invalid JSON configuration: ${error.message}`);
    }

    // Always create a new agent when init is called;
    const _result = await api.initAgent(config);
    loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
    loggers.app.info(JSON.stringify(_result, null, 2));
  }
}

/**
 * Handle agent reinitialization command with smart agent detection
 */
async function _handleReinitializeCommand(api, args) {
  const agentId = args[1];
  let config = {};

  // Parse config if provided
  if (args[2]) {
    try {
      config = JSON.parse(args[2]);
    } catch (error) {
      throw new Error(`Invalid JSON configuration: ${error.message}`);
    }
  }
  const _result = await api.reinitializeAgent(agentId, config);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle agent status command with auto-detection
 */
async function _handleStatusCommand(api, args) {
  const agentId = args[1];

  // Agent ID is always required
  if (!agentId) {
    throw new Error(
      'Agent ID required for status. Options:\n' +
        '1. Provide agent ID: status <agentId>\n' +
        '2. Initialize first: init (creates agent And returns agent ID)\n' +
        '3. Use list-agents to find available agents',
    );
  }
  const _result = await api.getAgentStatus(agentId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle current task command with agent ID detection
 */
async function _handleCurrentCommand(api, args) {
  const agentId = args[1];

  // Agent ID is always required
  if (!agentId) {
    throw new Error(
      'Agent ID required for current task. Options:\n' +
        '1. Provide agent ID: current <agentId>\n' +
        '2. Initialize first: init (creates agent And returns agent ID)\n' +
        '3. Use list-agents to find available agents',
    );
  }
  const _result = await api.getCurrentTask(agentId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle list tasks command with filter parsing
 */
async function _handleListCommand(api, args) {
  let filter = {};
  if (args[1]) {
    try {
      filter = JSON.parse(args[1]);
    } catch (error) {
      throw new Error(`Invalid JSON filter: ${error.message}`);
    }
  }
  const _result = await api.listTasks(filter);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle create task command with JSON parsing
 */
async function _handleCreateCommand(api, args) {
  if (!args[1]) {
    throw new Error('Task data required for create command');
  }
  let _taskData;
  try {
    _taskData = JSON.parse(args[1]);
  } catch (error) {
    throw new Error(`Invalid JSON task data: ${error.message}`);
  }
  const _result = await api.createTask(_taskData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle create error task command with JSON parsing And category validation
 */
async function _handleCreateErrorCommand(api, args) {
  if (!args[1]) {
    throw new Error('Task data required for create-error command');
  }
  let _taskData;
  try {
    _taskData = JSON.parse(args[1]);
  } catch (error) {
    throw new Error(`Invalid JSON task data: ${error.message}`);
  }

  // VALIDATE: Check category before proceeding
  if (_taskData.category && _taskData.category !== 'error') {
    throw new Error(
      `create-error command can only be used for error category tasks. ` +
      `Received category: "${_taskData.category}". ` +
      `Use 'create' command for category: ${_taskData.category}`,
    );
  }
  const _result = await api.createErrorTask(_taskData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle analyze phase insertion command
 */
async function _handleAnalyzePhaseInsertionCommand(api, args) {
  if (!args[1]) {
    throw new Error('Task data required for analyze-phase-insertion command');
  }
  let _taskData;
  try {
    _taskData = JSON.parse(args[1]);
  } catch (error) {
    throw new Error(`Invalid JSON task data: ${error.message}`);
  }
  const _result = await api.analyzePhaseInsertion(_taskData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle claim task command with agent ID detection And allowOutOfOrder support
 */
async function _handleClaimCommand(api, args, initialAgentId) {
  const taskId = args[1];
  let agentId = args[2] || initialAgentId;
  let priority = args[3] || 'normal';

  // Check for --allow-out-of-order flag in all arguments;
  const allowOutOfOrderFlag = args.includes('--allow-out-of-order');

  // Remove the flag from args And adjust parameters
  if (allowOutOfOrderFlag) {
    const flagIndex = args.indexOf('--allow-out-of-order');
    args.splice(flagIndex, 1);

    // Re-parse arguments after removing flag
    agentId = args[2];
    priority = args[3] || 'normal';
  }

  if (!taskId) {
    throw new Error('Task ID required for claim command');
  }

  // Agent ID is always required
  if (!agentId) {
    throw new Error(
      'Agent ID required for claim. Options:\n' +
        '1. Provide agent ID: claim <taskId> <agentId> [priority] [--allow-out-of-order]\n' +
        '2. Initialize first: init (creates agent And returns agent ID)\n' +
        '3. Find existing agents: list-agents (shows all agent IDs)\n\n' +
        'Flags:\n' +
        '  --allow-out-of-order: Override task order restrictions (use when user explicitly requests specific task)',
    );
  }

  // Use TaskManager directly when allowOutOfOrder is needed;
  let _result;
  if (allowOutOfOrderFlag) {
    loggers.stopHook.info('🔄 OVERRIDING TASK ORDER - User-requested task takes priority');
    loggers.app.info('🔄 OVERRIDING TASK ORDER - User-requested task takes priority');
    _result = await api.taskManager.claimTask(taskId, agentId, priority, {
      allowOutOfOrder: true,
    });
  } else {
    _result = await api.claimTask(taskId, agentId, priority);
  }
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));

  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle complete task command with completion data parsing
 */
async function _handleCompleteCommand(api, args) {
  const taskId = args[1];
  const agentId = null;
  let completionData = null;

  if (!taskId) {
    throw new Error('Task ID required for complete command');
  }

  // Parse optional completion data
  if (args[2]) {
    try {
      completionData = JSON.parse(args[2]);
    } catch (error) {
      throw new Error(`Invalid JSON completion data: ${error.message}`);
    }
  }
  const _result = await api.completeTask(taskId, agentId, completionData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle delete task command
 */
async function _handleDeleteCommand(api, args) {
  const taskId = args[1];
  if (!taskId) {
    throw new Error('Task ID required for delete command');
  }
  const _result = await api.deleteTask(taskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle move task to top command
 */
async function _handleMoveTopCommand(api, args) {
  const taskId = args[1];
  if (!taskId) {
    throw new Error('Task ID required for move-top command');
  }
  const _result = await api.moveTaskToTop(taskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle move task up command
 */
async function _handleMoveUpCommand(api, args) {
  const taskId = args[1];
  if (!taskId) {
    throw new Error('Task ID required for move-up command');
  }
  const _result = await api.moveTaskUp(taskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle move task down command
 */
async function _handleMoveDownCommand(api, args) {
  const taskId = args[1];
  if (!taskId) {
    throw new Error('Task ID required for move-down command');
  }
  const _result = await api.moveTaskDown(taskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle move task to bottom command
 */
async function _handleMoveBottomCommand(api, args) {
  const taskId = args[1];
  if (!taskId) {
    throw new Error('Task ID required for move-bottom command');
  }
  const _result = await api.moveTaskToBottom(taskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle suggest feature command
 */
async function _handleSuggestFeatureCommand(api, args) {
  if (!args[1]) {
    throw new Error('Feature data required for suggest-feature command');
  }
  let FEATURE_DATA;
  try {
    FEATURE_DATA = JSON.parse(args[1]);
  } catch (error) {
    throw new Error(`Invalid JSON feature data: ${error.message}`);
  }

  const agentId = null;
  const _result = await api.suggestFeature(FEATURE_DATA, agentId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle approve feature command
 */
async function _handleApproveFeatureCommand(api, args) {
  const featureId = args[1];
  if (!featureId) {
    throw new Error('Feature ID required for approve-feature command');
  }
  const userId = null;
  const _result = await api.approveFeature(featureId, userId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle reject feature command
 */
async function _handleRejectFeatureCommand(api, args) {
  const featureId = args[1];
  if (!featureId) {
    throw new Error('Feature ID required for reject-feature command');
  }
  const userId = args[2] || null;
  const reason = args[3] || null;
  const _result = await api.rejectFeature(featureId, userId, reason);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle list features command
 */
async function _handleListFeaturesCommand(api, args) {
  let filter = {};
  if (args[1]) {
    try {
      filter = JSON.parse(args[1]);
    } catch (error) {
      throw new Error(`Invalid JSON filter: ${error.message}`);
    }
  }
  const _result = await api.listFeatures(filter);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle create phase command
 */
async function _handleCreatePhaseCommand(api, args) {
  const featureId = args[1];
  if (!featureId) {
    throw new Error('Feature ID required for create-phase command');
  }
  if (!args[2]) {
    throw new Error('Phase data required for create-phase command');
  }
  let _phaseData;
  try {
    _phaseData = JSON.parse(args[2]);
  } catch (error) {
    throw new Error(`Invalid JSON phase data: ${error.message}`);
  }
  const _result = await api.createPhase(featureId, _phaseData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle update phase command
 */
async function _handleUpdatePhaseCommand(api, args) {
  const featureId = args[1];
  const phaseNumber = parseInt(args[2], 10);
  if (!featureId) {
    throw new Error('Feature ID required for update-phase command');
  }
  if (!args[2] || isNaN(phaseNumber)) {
    throw new Error('Valid phase number required for update-phase command');
  }
  if (!args[3]) {
    throw new Error('Update data required for update-phase command');
  }
  let _updates;
  try {
    _updates = JSON.parse(args[3]);
  } catch (error) {
    throw new Error(`Invalid JSON update data: ${error.message}`);
  }
  const _result = await api.updatePhase(featureId, phaseNumber, _updates);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle progress phase command
 */
async function _handleProgressPhaseCommand(api, args) {
  const featureId = args[1];
  const currentPhaseNumber = parseInt(args[2], 10);
  if (!featureId) {
    throw new Error('Feature ID required for progress-phase command');
  }
  if (!args[2] || isNaN(currentPhaseNumber)) {
    throw new Error('Valid current phase number required for progress-phase command');
  }
  const _result = await api.progressPhase(featureId, currentPhaseNumber);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle list phases command
 */
async function _handleListPhasesCommand(api, args) {
  const featureId = args[1];
  if (!featureId) {
    throw new Error('Feature ID required for list-phases command');
  }
  const _result = await api.listPhases(featureId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle current phase command
 */
async function _handleCurrentPhaseCommand(api, args) {
  const featureId = args[1];
  if (!featureId) {
    throw new Error('Feature ID required for current-phase command');
  }
  const _result = await api.getCurrentPhase(featureId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle phase stats command
 */
async function _handlePhaseStatsCommand(api, args) {
  const featureId = args[1];
  if (!featureId) {
    throw new Error('Feature ID required for phase-stats command');
  }
  const _result = await api.getPhaseStats(featureId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle get tasks command for agent swarm coordination
 */
async function _handleGetTasksCommand(api, args) {
  let options = {};
  if (args[1]) {
    try {
      options = JSON.parse(args[1]);
    } catch (error) {
      throw new Error(`Invalid JSON options: ${error.message}`);
    }
  }
  const _result = await api.getTasks(options);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle create subtask command - adds research or audit subtask to existing task
 */
async function _handleCreateSubtaskCommand(api, args) {
  const taskId = args[1];
  const subtaskType = args[2]; // 'research' or 'audit'

  if (!taskId) {
    throw new Error('Task ID required for create-subtask command');
  }

  if (!subtaskType || !['research', 'audit'].includes(subtaskType)) {
    throw new Error('Subtask type required: "research" or "audit"');
  }

  let subtaskData = {};
  if (args[3]) {
    try {
      subtaskData = JSON.parse(args[3]);
    } catch (error) {
      throw new Error(`Invalid JSON subtask data: ${error.message}`);
    }
  }
  const _result = await api.createSubtask(taskId, subtaskType, subtaskData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle list subtasks command - shows all subtasks for a given task
 */
async function _handleListSubtasksCommand(api, args) {
  const taskId = args[1];

  if (!taskId) {
    throw new Error('Task ID required for list-subtasks command');
  }
  const _result = await api.listSubtasks(taskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle update subtask command - updates subtask status, description, etc.
 */
async function _handleUpdateSubtaskCommand(api, args) {
  const taskId = args[1];
  const subtaskId = args[2];

  if (!taskId) {
    throw new Error('Task ID required for update-subtask command');
  }

  if (!subtaskId) {
    throw new Error('Subtask ID required for update-subtask command');
  }

  if (!args[3]) {
    throw new Error('Update data required for update-subtask command');
  }

  let _updateData;
  try {
    _updateData = JSON.parse(args[3]);
  } catch (error) {
    throw new Error(`Invalid JSON update data: ${error.message}`);
  }
  const _result = await api.updateSubtask(taskId, subtaskId, _updateData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle delete subtask command - removes subtask from task
 */
async function _handleDeleteSubtaskCommand(api, args) {
  const taskId = args[1];
  const subtaskId = args[2];

  if (!taskId) {
    throw new Error('Task ID required for delete-subtask command');
  }

  if (!subtaskId) {
    throw new Error('Subtask ID required for delete-subtask command');
  }
  const _result = await api.deleteSubtask(taskId, subtaskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle add success criteria command - adds success criteria to task or project-wide
 */
async function _handleAddSuccessCriteriaCommand(api, args) {
  const targetType = args[1]; // 'task' or 'project'
  const targetId = args[2]; // task ID for task-specific, null for project-wide

  if (!targetType || !['task', 'project'].includes(targetType)) {
    throw new Error('Target type required: "task" or "project"');
  }

  if (targetType === 'task' && !targetId) {
    throw new Error('Task ID required for task-specific success criteria');
  }

  if (!args[3]) {
    throw new Error('Success criteria data required');
  }

  let _criteriaData;
  try {
    _criteriaData = JSON.parse(args[3]);
  } catch (error) {
    throw new Error(`Invalid JSON criteria data: ${error.message}`);
  }
  const _result = await api.addSuccessCriteria(targetType, targetId, _criteriaData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle get success criteria command - retrieves success criteria for task or project
 */
async function _handleGetSuccessCriteriaCommand(api, args) {
  const targetType = args[1]; // 'task' or 'project'
  const targetId = args[2]; // task ID for task-specific, null for project-wide

  if (!targetType || !['task', 'project'].includes(targetType)) {
    throw new Error('Target type required: "task" or "project"');
  }

  if (targetType === 'task' && !targetId) {
    throw new Error('Task ID required for task-specific success criteria');
  }
  const _result = await api.getSuccessCriteria(targetType, targetId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle update success criteria command - modifies existing success criteria
 */
async function _handleUpdateSuccessCriteriaCommand(api, args) {
  const targetType = args[1]; // 'task' or 'project'
  const targetId = args[2]; // task ID for task-specific, null for project-wide

  if (!targetType || !['task', 'project'].includes(targetType)) {
    throw new Error('Target type required: "task" or "project"');
  }

  if (targetType === 'task' && !targetId) {
    throw new Error('Task ID required for task-specific success criteria');
  }

  if (!args[3]) {
    throw new Error('Update data required for update-success-criteria command');
  }

  let _updateData;
  try {
    _updateData = JSON.parse(args[3]);
  } catch (error) {
    throw new Error(`Invalid JSON update data: ${error.message}`);
  }
  const _result = await api.updateSuccessCriteria(targetType, targetId, _updateData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle set project criteria command - sets project-wide success criteria
 */
async function _handleSetProjectCriteriaCommand(api, args) {
  if (!args[1]) {
    throw new Error('Project criteria data required');
  }

  let _criteriaData;
  try {
    _criteriaData = JSON.parse(args[1]);
  } catch (error) {
    throw new Error(`Invalid JSON criteria data: ${error.message}`);
  }
  const _result = await api.setProjectCriteria(_criteriaData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle validate criteria command - validates task against success criteria
 */
async function _handleValidateCriteriaCommand(api, args) {
  const taskId = args[1];

  if (!taskId) {
    throw new Error('Task ID required for criteria validation');
  }

  // Optional validation type And evidence;
  const validationType = args[2] || 'full'; // 'full' or 'partial'
  let evidence = {};

  if (args[3]) {
    try {
      evidence = JSON.parse(args[3]);
    } catch (error) {
      throw new Error(`Invalid JSON evidence data: ${error.message}`);
    }
  }
  const _result = await api.validateCriteria(taskId, validationType, evidence);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle criteria report command - generates validation report for task
 */
async function _handleCriteriaReportCommand(api, args) {
  const taskId = args[1];

  if (!taskId) {
    throw new Error('Task ID required for criteria report');
  }
  const _result = await api.getCriteriaReport(taskId);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle research task command - manages research task routing And execution
 */
async function _handleResearchTaskCommand(api, args) {
  const action = args[1]; // 'start', 'complete', 'status'
  const taskId = args[2];

  if (!action || !['start', 'complete', 'status'].includes(action)) {
    throw new Error('Action required: "start", "complete", or "status"');
  }

  if (!taskId) {
    throw new Error('Task ID required for research task command');
  }

  let researchData = {};
  if (args[3]) {
    try {
      researchData = JSON.parse(args[3]);
    } catch (error) {
      throw new Error(`Invalid JSON research data: ${error.message}`);
    }
  }
  const _result = await api.manageResearchTask(action, taskId, researchData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle audit task command - manages audit task assignment And execution with objectivity controls
 */
async function _handleAuditTaskCommand(api, args) {
  const action = args[1]; // 'start', 'complete', 'status'
  const taskId = args[2];

  if (!action || !['start', 'complete', 'status'].includes(action)) {
    throw new Error('Action required: "start", "complete", or "status"');
  }

  if (!taskId) {
    throw new Error('Task ID required for audit task command');
  }

  let auditData = {};
  if (args[3]) {
    try {
      auditData = JSON.parse(args[3]);
    } catch (error) {
      throw new Error(`Invalid JSON audit data: ${error.message}`);
    }
  }
  const _result = await api.manageAuditTask(action, taskId, auditData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

// =================== RAG OPERATIONS HANDLERS ===================

/**
 * Handle store lesson command with JSON parsing
 */
async function _handleStoreLessonCommand(api, args) {
  if (!args[1]) {
    throw new Error('Lesson data required for store-lesson command');
  }
  let _lessonData;
  try {
    _lessonData = JSON.parse(args[1]);
  } catch (error) {
    throw new Error(`Invalid JSON lesson data: ${error.message}`);
  }
  const _result = await api.storeLesson(_lessonData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle store error command with JSON parsing
 */
async function _handleStoreErrorCommand(api, args) {
  if (!args[1]) {
    throw new Error('Error data required for store-error command');
  }
  let _errorData;
  try {
    _errorData = JSON.parse(args[1]);
  } catch (error) {
    throw new Error(`Invalid JSON _error data: ${error.message}`);
  }
  const _result = await api.storeError(_errorData);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle search lessons command
 */
async function _handleSearchLessonsCommand(api, args) {
  if (!args[1]) {
    throw new Error('Search query required for search-lessons command');
  }

  const query = args[1];
  let options = {};

  if (args[2]) {
    try {
      options = JSON.parse(args[2]);
    } catch (error) {
      throw new Error(`Invalid JSON options: ${error.message}`);
    }
  }
  const _result = await api.searchLessons(query, options);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle find similar errors command
 */
async function _handleFindSimilarErrorsCommand(api, args) {
  if (!args[1]) {
    throw new Error('Error description required for find-similar-errors command');
  }

  const errorDescription = args[1];
  let options = {};

  if (args[2]) {
    try {
      options = JSON.parse(args[2]);
    } catch (error) {
      throw new Error(`Invalid JSON options: ${error.message}`);
    }
  }
  const _result = await api.findSimilarErrors(errorDescription, options);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle get relevant lessons command
 */
async function _handleGetRelevantLessonsCommand(api, args) {
  if (!args[1]) {
    throw new Error('Task context required for get-relevant-lessons command');
  }

  const taskContext = args[1];
  let options = {};

  if (args[2]) {
    try {
      options = JSON.parse(args[2]);
    } catch (error) {
      throw new Error(`Invalid JSON options: ${error.message}`);
    }
  }
  const _result = await api.getRelevantLessons(taskContext, options);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Handle RAG analytics command
 */
async function _handleRagAnalyticsCommand(api, args) {
  let options = {};

  if (args[1]) {
    try {
      options = JSON.parse(args[1]);
    } catch (error) {
      throw new Error(`Invalid JSON options: ${error.message}`);
    }
  }
  const _result = await api.getRagAnalytics(options);
  loggers.stopHook.info({ additionalData: [null, 2] }, JSON.stringify(_result));
  loggers.app.info(JSON.stringify(_result, null, 2));
}

/**
 * Enhance error with contextual guidance
 */
async function enhanceErrorWithContext(api, error, command) {
  let guide = null;
  let errorContext = 'general';

  // Determine error context based on error message And command
  if (
    error.message.includes('no agent id') ||
    error.message.includes('agent not initialized')
  ) {
    errorContext = 'agent-init';
  } else if (command === 'init' || command === 'reinitialize') {
    errorContext = command === 'init' ? 'agent-init' : 'agent-reinit';
  } else if (['create', 'claim', 'complete', 'list'].includes(command)) {
    errorContext = 'task-operations';
  }

  try {
    // Use cached guide method for better performance
    guide = await api._getGuideForError(errorContext);
  } catch {
    // If contextual guide fails, try fallback
    try {
      guide = _apiUtils.getFallbackGuide(errorContext);
    } catch {
      // If everything fails, use basic guide
    }
  }

  const enhancedError = new Error(error.message);
  enhancedError.context = {
    command,
    errorContext,
    timestamp: new Date().toISOString(),
    guide: guide || {
      message:
        'for complete API usage guidance, run: timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" guide',
      helpText:
        'The guide provides comprehensive information about task classification, workflows, And all API capabilities',
    },
  };

  return enhancedError;
}

/**
 * Display comprehensive help information
 */
function displayHelp(agentId, _category = 'general') {
  loggers.app.info(`
TaskManager API - Universal Task Management CLI

Agent Management:
  init [config]                - Initialize agent with optional config JSON
  reinitialize <agentId> [config] - Reinitialize existing agent (use list-agents to find your agent ID)
  list-agents                  - List all active agents with their IDs And status
  status [agentId]             - Get agent status And current tasks
  current [agentId]            - Get current task for agent
  stats                        - Get orchestration statistics
  usage-analytics [options]   - Get TaskManager usage analytics with 5-hour window tracking

Discovery Commands:
  methods                      - Get all available TaskManager And API methods with CLI/API mapping
  guide                        - Get comprehensive API documentation And troubleshooting

Task Operations:
  create <taskData>            - Create new task with JSON data (requires category)
  create-error <taskData>      - Create error task with absolute priority (bypasses feature ordering)
  list [filter]                - List tasks with optional filter JSON
  claim <taskId> [agentId] [priority] - Claim task for agent
  complete <taskId> [data]     - Complete task with optional completion data JSON
  delete <taskId>              - Delete task (for task conversion/cleanup)

Task Management:
  move-top <taskId>            - Move task to top priority
  move-up <taskId>             - Move task up one position
  move-down <taskId>           - Move task down one position
  move-bottom <taskId>         - Move task to bottom

Feature Management:
  suggest-feature <featureData> [agentId] - Suggest new feature for user approval
  approve-feature <featureId> [userId]    - Approve suggested feature for implementation
  reject-feature <featureId> [userId] [reason] - Reject suggested feature
  list-suggested-features      - List all features awaiting user approval
  list-features [filter]       - List all features with optional filter
  feature-stats                - Get feature statistics And status breakdown

Phase Management (FEATURE-ONLY - not for error/subtask/test tasks):
  create-phase <featureId> <phaseData>    - Create new phase for a feature (sequential: Phase 1, Phase 2, etc.)
  update-phase <featureId> <phaseNumber> <updates> - Update phase status And details
  progress-phase <featureId> <currentPhaseNumber>  - Complete current phase And progress to next
  list-phases <featureId>      - List all phases for a feature with statistics
  current-phase <featureId>    - Get current active phase for a feature
  phase-stats <featureId>      - Get detailed phase completion statistics

Agent Swarm Coordination (Self-Organizing Agent Architecture):
  get-tasks [options]          - Get highest-priority available tasks for agent swarm
                                 Any agent can query this to find work autonomously
                                 TaskManager API acts as central "brain" coordinating agents
    Options: {"agentId": "...", "categories": ["error"], "limit": 5}

Embedded Subtasks Management:
  create-subtask <taskId> <type> [data]        - Create research/audit subtask for task
    Type: "research" or "audit"
  list-subtasks <taskId>                       - List all subtasks for a task
  update-subtask <taskId> <subtaskId> <data>   - Update subtask status/description
  delete-subtask <taskId> <subtaskId>          - Remove subtask from task

Success Criteria Management:
  add-success-criteria <type> <targetId> <data> - Add success criteria to task or project
    Type: "task" or "project"
  get-success-criteria <type> <targetId>       - Get success criteria for task/project
  update-success-criteria <type> <targetId> <data> - Update existing success criteria

Research & Audit Task Management:
  research-task <action> <taskId> [data]       - Manage research tasks (start/complete/status)
  audit-task <action> <taskId> [data]          - Manage audit tasks with objectivity controls

RAG Operations - Lessons And Error Database:
  store-lesson <lessonData>                    - Store new lesson with auto-embedding for semantic search
  store-error <errorData>                      - Store error resolution with embedding for similarity matching
  search-lessons <query> [options]             - Search for relevant lessons using semantic similarity
  find-similar-errors <errorDescription> [options] - Find similar resolved errors for current problem
  get-relevant-lessons <taskContext> [options] - Get contextually relevant lessons for task
  rag-analytics [options]                      - Get usage patterns And effectiveness metrics

Essential Examples:
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" init
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" create '{"title": "Fix linting errors", "description": "Resolve ESLint violations", "category": "error"}'
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" complete task_123 '{"message": "Task completed successfully"}'
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" list '{"status": "pending"}'
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" guide

Agent Swarm Examples:
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" get-tasks
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" get-tasks '{"categories": ["error"], "limit": 3}'
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" get-tasks '{"agentId": "development_session_123", "specializations": ["frontend"]}'

Subtasks & Success Criteria Examples:
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" create-subtask task_123 research '{"focus": "API best practices"}'
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" list-subtasks task_123
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" add-success-criteria task task_123 '{"criteria": ["Linter clean", "Tests pass"]}'
  timeout 10s node "/Users/jeremyparker/Desktop/Claude Coding Projects/infinite-continue-stop-hook/taskmanager-api.js" research-task start task_123 '{"locations": ["codebase", "internet"]}'

RAG Operations Examples:
  timeout 10s node "/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js" store-lesson '{"title": "API Error Handling", "content": "Always use try-catch blocks", "category": "best-practices"}'
  timeout 10s node "/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js" store-error '{"error_description": "Cannot read property", "resolution": "Add null checks", "error_type": "runtime"}'
  timeout 10s node "/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js" search-lessons "error handling best practices" '{"category": "best-practices", "limit": 5}'
  timeout 10s node "/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js" find-similar-errors "Cannot read property of undefined" '{"limit": 3}'
  timeout 10s node "/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js" get-relevant-lessons "implementing API endpoints" '{"projectId": "current"}'
  timeout 10s node "/Users/jeremyparker/infinite-continue-stop-hook/taskmanager-api.js" rag-analytics

Troubleshooting:
  • for completion JSON errors, ensure proper quoting: '{"message": "text"}'
  • Use 'methods' command to see CLI-to-API method mapping
  • Use 'guide' command for comprehensive documentation
  • CLI commands (like 'complete') map to API methods (like 'completeTask')
  `);
}

module.exports = {
  executeCommand,
  displayHelp,
};
