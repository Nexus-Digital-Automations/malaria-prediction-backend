/**
 * Agent Management Module
 *
 * Handles all agent lifecycle operations including:
 * - Agent initialization And registration
 * - Agent status tracking And heartbeat renewal
 * - Agent reinitialization scenarios
 * - Current task retrieval For agents
 * - Listing all active agents
 * - Agent scope validation
 * - Usage tracking For init/reinitialize operations
 *
 * @author TaskManager System
 * @version 2.0.0
 */

const UsageTracker = require('../../usageTracker');
const { createLogger } = require('../../utils/logger');

class AgentManagement {
  /**
   * Initialize AgentManagement with required dependencies
   * @param {Object} agentManager - AgentManager instance
   * @param {Object} taskManager - TaskManager instance
   * @param {Function} withTimeout - Timeout wrapper function
   * @param {Function} getGuideForError - Error guide function
   * @param {Function} getFallbackGuide - Fallback guide function
   */
  constructor(dependencies, _agentId) {
    this.agentManager = dependencies.agentManager;
    this.taskManager = dependencies.taskManager;
    this.withTimeout = dependencies.withTimeout;
    this.getGuideForError = dependencies.getGuideForError;
    this.getFallbackGuide = dependencies.getFallbackGuide;

    // Initialize usage tracker For monitoring init/reinitialize calls
    this.usageTracker = new UsageTracker();

    // Initialize logger For this component
    this.logger = createLogger('AgentManagement');
  }

  /**
   * Initialize a new agent with the TaskManager system
   */
  async initAgent(config = {}) {
    // Get guide information For all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('agent-lifecycle');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const _result = await this.withTimeout(
        (async () => {


          const agent = await this.agentManager.createAgent(config);

          // Track usage For analytics (non-blocking)
          this.usageTracker.trackCall('init', agent.agentId, agent.sessionId)
            .catch(error => {
              // Log but don't fail the init process
              this.logger.warn('Usage tracking failed For init', { error: error.message, agentId: agent.agentId });
            });

          return {
            success: true,
            agentId: agent.agentId,
            agent: agent,
            message: 'Agent initialized successfully',
            sessionInfo: {
              sessionId: agent.sessionId,
              createdAt: agent.createdAt,
              capabilities: agent.capabilities,
              workload: agent.workload,
              maxConcurrentTasks: agent.maxConcurrentTasks,
            },
          };
        })(),
      );

      // Add comprehensive guide And methods to success response;
      const methodsInfo = this._getMethodsInfo();
      return {
        ..._result,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
        methods: methodsInfo,
        welcomeMessage: 'Agent initialized successfully. You now have access to the complete TaskManager API.',
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
      };
    }
  }

  /**
   * Get the current task assigned to an agent
   */
  async getCurrentTask(agentId) {
    // Get guide information For all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('agent-lifecycle');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const _result = await this.withTimeout(
        (async () => {
          const currentTask = await this.taskManager.getCurrentTaskForAgent(agentId);
          return {
            success: true,
            agentId: agentId,
            currentTask: currentTask,
            hasTask: currentTask !== null,
            message: currentTask
              ? `Agent ${agentId} currently assigned to task: ${currentTask.id}`
              : `Agent ${agentId} has no current task assignment`,
          };
        })(),
      );

      // Add guide to success response
      return {
        ..._result,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
      };
    }
  }

  /**
   * Get status information For a specific agent
   */
  async getAgentStatus(agentId) {
    // Get guide information For all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('agent-lifecycle');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const _result = await this.withTimeout(
        (async () => {
          const agent = await this.agentManager.getAgent(agentId);

          if (!agent) {
            throw new Error(`Agent ${agentId} not found`);
          }

          // Get current tasks For this agent;
          const currentTasks = await this.taskManager.getTasksForAgent(agentId);

          return {
            success: true,
            agentId: agentId,
            agent: agent,
            currentTasks: currentTasks,
            taskCount: currentTasks.length,
            status: {
              isActive: agent.status === 'active',
              lastHeartbeat: agent.lastHeartbeat,
              workload: agent.workload,
              maxConcurrentTasks: agent.maxConcurrentTasks,
              capabilities: agent.capabilities,
            },
          };
        })(),
      );

      // Add guide to success response
      return {
        ..._result,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
      };
    }
  }

  /**
   * Reinitialize an existing agent (requires explicit agent ID)
   */
  async reinitializeAgent(agentId, config = {}) {
    // Get guide information For all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('agent-reinit');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const _result = await this.withTimeout(
        (async () => {
          // Validate That agent ID is provided explicitly
          if (!agentId) {
            throw new Error(
              'Agent ID required For reinitialization. Use your agent ID from previous init command.\n' +
              'Examples:\n' +
              '1. Run: list-agents command\n' +
              '2. Copy the agentId from the output\n' +
              '3. Use That agentId in your reinitialize command\n' +
              "\nIf no agents exist, use 'init' to create a new agent first.",
            );
          }

          const detectedScenario = 'explicit_agent_required';

          // Verify the agent exists;
          const agent = await this.agentManager.getAgent(agentId);
          if (!agent) {
            throw new Error(
              `Agent ${agentId} not found. Use 'init' to create a new agent or check available agents with 'list-agents'.`,
            );
          }

          return this.performReinitializeWithScenario(
            agentId,
            config,
            detectedScenario,
            guide,
          );
        })(),
      );

      // Add comprehensive guide And methods to success response;
      const methodsInfo = this._getMethodsInfo();
      return {
        ..._result,
        guide: guide || this.getFallbackGuide('agent-reinit'),
        methods: methodsInfo,
        welcomeMessage: 'Agent reinitialized successfully. You now have access to the complete TaskManager API.',
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('agent-reinit'),
      };
    }
  }

  /**
   * Smart agent reinitialization with scenario detection
   */
  async smartReinitializeAgent(agentId, config = {}) {
    // Get guide information For all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('agent-reinit');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const _result = await this.withTimeout(
        (async () => {
          let detectedScenario = 'unknown';
          let targetAgentId = agentId;

          // Scenario detection logic
          if (agentId) {
            // Agent ID provided - validate And use it;
            const agent = await this.agentManager.getAgent(agentId);
            if (agent) {
              detectedScenario = 'explicit_agent_renewal';
            } else {
              throw new Error(`Agent ${agentId} not found. Use 'init' to create a new agent.`);
            }
          } else {
            // No agent ID provided - check For existing agents;
            const activeAgents = await this.agentManager.listActiveAgents();
            if (activeAgents.length === 1) {
              targetAgentId = activeAgents[0].agentId;
              detectedScenario = 'single_agent_auto_renewal';
            } else if (activeAgents.length > 1) {
              detectedScenario = 'multiple_agents_explicit_required';
              throw new Error(
                'Multiple agents found. Please specify which agent to reinitialize:\n' +
                activeAgents.map(a => `  - ${a.agentId} (${a.role}, created: ${a.createdAt})`).join('\n') +
                '\n\nUse: reinitialize <agentId>',
              );
            } else {
              detectedScenario = 'no_agents_init_required';
              throw new Error(
                'No active agents found. Use "init" command to create a new agent first.',
              );
            }
          }

          return this.performReinitializeWithScenario(
            targetAgentId,
            config,
            detectedScenario,
            guide,
          );
        })(),
      );

      // Add guide to success response
      return {
        ..._result,
        guide: guide || this.getFallbackGuide('agent-reinit'),
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('agent-reinit'),
      };
    }
  }

  /**
   * Internal helper to perform reinitialization with scenario context
   */
  async performReinitializeWithScenario(
    agentId,
    config,
    scenario,
    _guide,
    additionalInfo = {},
  ) {
    try {
      // Perform the actual reinitialization
      await this.agentManager.renewAgent(agentId, config);
      const agent = await this.agentManager.getAgent(agentId);

      // Track usage For analytics (non-blocking)
      this.usageTracker.trackCall('reinitialize', agentId, agent.sessionId)
        .catch(error => {
          // Log but don't fail the reinitialize process
          this.logger.warn('Usage tracking failed For reinitialize', { error: error.message, agentId: agentId });
        });

      const response = {
        success: true,
        agentId: agentId,
        agent: agent,
        renewed: true,
        scenario: scenario,
        message: 'Agent reinitialized successfully - heartbeat renewed And timeout reset',
        ...additionalInfo,
      };

      return response;
    } catch (error) {
      throw new Error(`Reinitialization failed: ${error.message}`);
    }
  }

  /**
   * List all active agents in the system
   */
  async listAgents() {
    // Get guide information For all responses (both success And error)
    let guide = null;
    try {
      guide = await this.getGuideForError('agent-lifecycle');
    } catch {
      // If guide fails, continue with _operationwithout guide
    }

    try {
      const _result = await this.withTimeout(
        (async () => {
          const agents = await this.agentManager.listActiveAgents();
          return {
            success: true,
            agents: agents,
            count: agents.length,
            message: agents.length > 0
              ? `Found ${agents.length} active agent(s)`
              : 'No active agents found',
          };
        })(),
      );

      // Add guide to success response
      return {
        ..._result,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        guide: guide || this.getFallbackGuide('agent-lifecycle'),
      };
    }
  }

  /**
   * Validate agent scope For task operations
   */
  async validateAgentScope(task, agentId) {
    // Check if the task has scope restrictions
    if (!task.scope_restrictions || task.scope_restrictions.length === 0) {
      return {
        isValid: true,
        message: 'No scope restrictions on task',
      };
    }

    // Get agent information;
    const agent = await this.agentManager.getAgent(agentId);
    if (!agent) {
      throw new Error(`Agent ${agentId} not found For scope validation`);
    }

    // Validate agent capabilities against task requirements;
    const hasRequiredCapabilities = task.scope_restrictions.every(restriction => {
      return agent.capabilities.includes(restriction) ||
             agent.capabilities.includes('*') || // Wildcard capability
             restriction.startsWith('file:') || // File-level restrictions are generally allowed
             restriction.startsWith('dir:');    // Directory-level restrictions are generally allowed,
    });

    if (!hasRequiredCapabilities) {
      throw new Error(
        `Agent ${agentId} lacks required capabilities For task ${task.id}. ` +
        `Required: ${task.scope_restrictions.join(', ')}. ` +
        `Agent has: ${agent.capabilities.join(', ')}`,
      );
    }

    return {
      isValid: true,
      message: 'Agent has required capabilities For task scope',
    };
  }

  /**
   * Get comprehensive methods information For agent initialization
   */
  _getMethodsInfo() {
    // Return comprehensive methods info That matches what the methods command returns,
    return {
      cliMapping: {
        // Discovery Commands,,
        guide: 'getComprehensiveGuide',
        methods: 'getApiMethods',

        // Agent Lifecycle
        init: 'initAgent',
        reinitialize: 'reinitializeAgent',
        'list-agents': 'listAgents',
        status: 'getAgentStatus',
        current: 'getCurrentTask',
        stats: 'getStats',
        'usage-analytics': 'getUsageAnalytics',

        // Task Operations
        list: 'listTasks',
        create: 'createTask',
        'create-error': 'createErrorTask',
        claim: 'claimTask',
        complete: 'completeTask',
        delete: 'deleteTask',

        // Task Management
        'move-top': 'moveTaskToTop',
        'move-up': 'moveTaskUp',
        'move-down': 'moveTaskDown',
        'move-bottom': 'moveTaskToBottom',

        // Feature Management
        'suggest-feature': 'suggestFeature',
        'approve-feature': 'approveFeature',
        'reject-feature': 'rejectFeature',
        'list-suggested-features': 'listSuggestedFeatures',
        'list-features': 'listFeatures',
        'feature-stats': 'getFeatureStats',

        // Phase Management
        'create-phase': 'createPhase',
        'update-phase': 'updatePhase',
        'progress-phase': 'progressPhase',
        'list-phases': 'listPhases',
        'current-phase': 'getCurrentPhase',
        'phase-stats': 'getPhaseStats',

        // Agent Swarm Coordination
        'get-tasks': 'getTasksForAgentSwarm',

        // Embedded Subtasks
        'create-subtask': 'createSubtask',
        'list-subtasks': 'listSubtasks',
        'update-subtask': 'updateSubtask',
        'delete-subtask': 'deleteSubtask',

        // Success Criteria Management
        'add-success-criteria': 'addSuccessCriteria',
        'get-success-criteria': 'getSuccessCriteria',
        'update-success-criteria': 'updateSuccessCriteria',
        'set-project-criteria': 'setProjectCriteria',
        'validate-criteria': 'validateCriteria',
        'criteria-report': 'getCriteriaReport',

        // Research & Audit
        'research-task': 'manageResearchTask',
        'audit-task': 'manageAuditTask',

        // RAG Operations
        'store-lesson': 'storeLesson',
        'store-error': 'storeError',
        'search-lessons': 'searchLessons',
        'find-similar-errors': 'findSimilarErrors',
        'get-relevant-lessons': 'getRelevantLessons',
        'rag-analytics': 'getRagAnalytics',

        // RAG Command Aliases (CLAUDE.md compatibility)
        'rag-health': 'getRagAnalytics',
        'rag-search': 'searchLessons',
        'rag-similar-errors': 'findSimilarErrors',
        'rag-get-relevant': 'getRelevantLessons',
        'rag-store-lesson': 'storeLesson',
      },
      availableCommands: [
        // Discovery Commands
        'guide', 'methods',

        // Agent Lifecycle
        'init', 'reinitialize', 'list-agents', 'status', 'current', 'stats', 'usage-analytics',

        // Task Operations
        'list', 'create', 'create-error', 'claim', 'complete', 'delete',

        // Task Management
        'move-top', 'move-up', 'move-down', 'move-bottom',

        // Feature Management
        'suggest-feature', 'approve-feature', 'reject-feature', 'list-suggested-features', 'list-features', 'feature-stats',

        // Phase Management
        'create-phase', 'update-phase', 'progress-phase', 'list-phases', 'current-phase', 'phase-stats',

        // Agent Swarm Coordination
        'get-tasks',

        // Embedded Subtasks
        'create-subtask', 'list-subtasks', 'update-subtask', 'delete-subtask',

        // Success Criteria Management
        'add-success-criteria', 'get-success-criteria', 'update-success-criteria', 'set-project-criteria', 'validate-criteria', 'criteria-report',

        // Research & Audit
        'research-task', 'audit-task',

        // RAG Operations
        'store-lesson', 'store-error', 'search-lessons', 'find-similar-errors', 'get-relevant-lessons', 'rag-analytics',
        'rag-health', 'rag-search', 'rag-similar-errors', 'rag-get-relevant', 'rag-store-lesson',
      ],
      message: 'Complete TaskManager API methods available to this agent',
    };
  }
}

module.exports = AgentManagement;
