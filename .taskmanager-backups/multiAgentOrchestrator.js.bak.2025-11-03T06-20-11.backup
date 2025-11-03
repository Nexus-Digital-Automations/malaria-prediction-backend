
/*
 * Security exceptions: This file operates on validated internal data structures
 * with controlled property access patterns for multi-agent orchestration.
 */

const FS = require('./agentManager');
const TASK_MANAGER = require('./taskManager');
const LOGGER = require('./appLogger');

class MultiAgentOrchestrator {
  constructor(todoPath, options = {}) {
    this.todoPath = todoPath;
    this.logger = options.logger || new LOGGER(process.cwd());
    this.systemStartTime = Date.now();

    // Initialize core components
    this.taskManager = new TASK_MANAGER(todoPath, {
      enableMultiAgent: true,
      lockTimeout: options.lockTimeout || 30000,
      ...options.taskManager,
    });

    this.agentManager = new AGENT_MANAGER(todoPath, {
      logger: this.logger,
      maxConcurrentTasks: options.maxConcurrentTasks || 3,
      ...options.agentManager,
    });

    this.lockManager = this.taskManager.lockManager;

    this.options = {
      maxParallelAgents: options.maxParallelAgents || 3,
      coordinationTimeout: options.coordinationTimeout || 60000, // 1 minute
      enableLoadBalancing: options.enableLoadBalancing !== false,
      enableIntelligentAssignment:
        options.enableIntelligentAssignment !== false,
      retryFailedTasks: options.retryFailedTasks !== false,
      ...options,
    };

    // Coordination state
    this.activeCoordinations = new Map();
    this.coordinationResults = new Map();
  }

  /**
   * Initialize a multi-agent session
   * @param {Array} agentConfigs - Array of agent configurations
   * @returns {Promise<Object>} Session initialization result
   */
  async initializeSession(agentConfigs) {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const registeredAgents = [];
    const failedAgents = [];

    // Register all agents in parallel for better performance
    const registrationPromises = agentConfigs.map(async (config) => {
      try {
        const agentId = await this.agentManager.registerAgent({
          ...config,
          sessionId: sessionId,
        });
        this.logger.addFlow(
          `Registered agent ${agentId} for session ${sessionId}`,
        );
        return { success: true, agentId, config };
      } catch {
        this.logger.logError(error, `Agent registration for ${config.role}`);
        return { success: false, config, error: error.message };
      }
    });

    const registrationResults = await Promise.all(registrationPromises);

    // Separate successful And failed registrations
    for (const result of registrationResults) {
      if (result.success) {
        registeredAgents.push({ agentId: RESULT.agentId, config: RESULT.config });
      } else {
        failedAgents.push({ config: RESULT.config, error: RESULT.error });
      }
    }

    return {
      sessionId: sessionId,
      registeredAgents: registeredAgents,
      failedAgents: failedAgents,
      totalRegistered: registeredAgents.length,
      totalFailed: failedAgents.length,
    };
  }

  /**
   * Orchestrate task distribution across multiple agents
   * @param {Object} distributionConfig - Distribution configuration
   * @returns {Promise<Object>} Distribution result
   */
  async orchestrateTaskDistribution(distributionConfig = {}) {
    const {
      maxTasks = this.options.maxParallelAgents,
      agentFilters = {},
      _taskFilters = {},
      strategy = 'intelligent',
    } = distributionConfig;

    let availableAgents;
    let availableTasks;

    try {
      // Get available agents
      this.logger.debug('Getting available agents');
      availableAgents = await this.agentManager.getActiveAgents(agentFilters);
      this.logger.debug('Available agents retrieved', {
        count: availableAgents.length,
      });

      if (availableAgents.length === 0) {
        this.logger.warn('No available agents found');
        return {
          success: false,
          reason: 'No available agents found',
          availableAgents: 0,
        };
      }

      // Get available tasks
      this.logger.debug('Getting available tasks');
      availableTasks = await this.taskManager.getAvailableTasksForAgents(
        maxTasks,
        availableAgents.map((agent) => agent.capabilities),
      );
      this.logger.debug('Available tasks retrieved', {
        count: availableTasks.length,
      });

      if (availableTasks.length === 0) {
        this.logger.warn('No available tasks found');
        return {
          success: false,
          reason: 'No available tasks found',
          availableTasks: 0,
        };
      }
    } catch {
      this.logger.error('Error in orchestrateTaskDistribution', {
        error: error.message,
        stack: error.stack,
      });
      return {
        success: false,
        reason: 'Exception during task distribution',
        error: error.message,
      };
    }

    // Execute distribution strategy
    let distributionResult;

    switch (strategy) {
      case 'intelligent':
        distributionResult = await this.intelligentTaskDistribution(
          availableAgents,
          availableTasks,
        );
        break;
      case 'round_robin':
        distributionResult = await this.roundRobinDistribution(
          availableAgents,
          availableTasks,
        );
        break;
      case 'capability_based':
        distributionResult = await this.capabilityBasedDistribution(
          availableAgents,
          availableTasks,
        );
        break;
      case 'load_balanced':
        distributionResult = await this.loadBalancedDistribution(
          availableAgents,
          availableTasks,
        );
        break;
      default:
        throw new Error(`Unknown distribution strategy: ${strategy}`);
    }

    return {
      success: true,
      strategy: strategy,
      availableAgents: availableAgents.length,
      availableTasks: availableTasks.length,
      distribution: distributionResult,
    };
  }

  /**
   * Create And manage parallel task execution
   * @param {Array} taskIds - Task IDs to execute in parallel
   * @param {Object} options - Execution options
   * @returns {Promise<Object>} Parallel execution result
   */
  async createParallelExecution(taskIds, options = {}) {
    const {
      coordinatorRequired = false,
      syncPoints = [],
      timeout = this.options.coordinationTimeout,
      _failureHandling = 'continue', // 'abort', 'continue', 'retry'
    } = options;

    // Get available agents for parallel execution
    const availableAgents = await this.agentManager.getActiveAgents({
      maxWorkload: this.agentManager.options.maxConcurrentTasks - 1,
    });

    if (availableAgents.length < taskIds.length) {
      return {
        success: false,
        reason: 'Insufficient agents for parallel execution',
        required: taskIds.length,
        available: availableAgents.length,
      };
    }

    const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      // Create coordination plan
      let coordinationPlan;

      if (coordinatorRequired) {
        const coordinatorAgent = availableAgents[0];
        const workerAgents = availableAgents.slice(1, taskIds.length);

        coordinationPlan = await this.taskManager.createCoordinatedExecution(
          taskIds[0], // Master task
          taskIds.slice(1), // Worker tasks
          coordinatorAgent.agentId,
        );

        // Assign tasks to workers in parallel
        const workerAssignmentPromises = workerAgents.map((agent, i) =>
          this.taskManager.claimTask(
            taskIds[i + 1],
            agent.agentId,
            'high',
          ),
        );
        await Promise.all(workerAssignmentPromises);
      } else {
        // Independent parallel execution
        const agentIds = availableAgents
          .slice(0, taskIds.length)
          .map((a) => a.agentId);

        coordinationPlan = await this.taskManager.createParallelExecution(
          taskIds,
          agentIds,
          syncPoints,
        );
      }

      if (!coordinationPlan.success) {
        return {
          success: false,
          reason: 'Failed to create coordination plan',
          error: coordinationPlan.reason,
        };
      }

      // Track execution
      this.activeCoordinations.set(executionId, {
        type: coordinatorRequired ? 'coordinated' : 'parallel',
        taskIds: taskIds,
        plan: coordinationPlan,
        startTime: Date.now(),
        timeout: timeout,
        status: 'active',
      });

      this.logger.addFlow(
        `Created ${coordinatorRequired ? 'coordinated' : 'parallel'} execution ${executionId} for ${taskIds.length} tasks`,
      );

      return {
        success: true,
        executionId: executionId,
        type: coordinatorRequired ? 'coordinated' : 'parallel',
        taskCount: taskIds.length,
        plan: coordinationPlan,
      };
    } catch {
      this.logger.logError(
        error,
        `Parallel execution creation for ${taskIds.length} tasks`,
      );
      return {
        success: false,
        reason: 'Exception during parallel execution setup',
        error: error.message,
      };
    }
  }

  /**
   * Monitor And manage active coordinations
   * @returns {Promise<Object>} Coordination status
   */
  async monitorCoordinations() {
    const currentTime = Date.now();
    const coordinationStatus = {
      active: 0,
      completed: 0,
      failed: 0,
      timedOut: 0,
      details: [],
    };

    // Process coordinations sequentially to maintain state consistency

    for (const [
      executionId,
      coordination,
    ] of this.activeCoordinations.entries()) {
      const elapsed = currentTime - coordination.startTime;

      if (elapsed > coordination.timeout) {
        // Handle timeout
        coordination.status = 'timeout';
        coordinationStatus.timedOut++;

        this.handleCoordinationTimeout(executionId, coordination);
      } else {
        // Check task completion status
        // eslint-disable-next-line no-await-in-loop -- Sequential processing required for coordination state management
        const taskStatuses = await this.checkTaskStatuses(coordination.taskIds);

        if (taskStatuses.allCompleted) {
          coordination.status = 'completed';
          coordinationStatus.completed++;
          this.coordinationResults.set(executionId, {
            success: true,
            completedAt: currentTime,
            duration: elapsed,
            tasks: taskStatuses.tasks,
          });
        } else if (taskStatuses.anyFailed) {
          coordination.status = 'failed';
          coordinationStatus.failed++;

          this.handleCoordinationFailure(
            executionId,
            coordination,
            taskStatuses,
          );
        } else {
          coordinationStatus.active++;
        }
      }

      coordinationStatus.details.push({
        executionId: executionId,
        type: coordination.type,
        status: coordination.status,
        taskCount: coordination.taskIds.length,
        elapsed: elapsed,
        progress: this.calculateCoordinationProgress(coordination.taskIds),
      });
    }

    return coordinationStatus;
  }

  /**
   * Intelligent task distribution based on agent capabilities And workload
   * @param {Array} agents - Available agents
   * @param {Array} tasks - Available tasks
   * @returns {Promise<Object>} Distribution result
   */
  async intelligentTaskDistribution(agents, tasks) {
    const assignments = [];
    const failedAssignments = [];

    // Score each agent-task combination
    const scoredCombinations = [];

    for (const task of tasks) {
      for (const agent of agents) {
        if (agent.workload < agent.maxConcurrentTasks) {
          const score = this.calculateAgentTaskScore(agent, task);
          scoredCombinations.push({
            agentId: agent.agentId,
            taskId: task.id,
            score: score,
            agent: agent,
            task: task,
          });
        }
      }
    }

    // Sort by score (highest first)
    scoredCombinations.sort((a, b) => b.score - a.score);

    const usedAgents = new Set();
    const usedTasks = new Set();

    // Assign tasks based on scores - process sequentially to avoid conflicts
    // Note: This loop intentionally uses sequential processing to prevent race conditions
    // in task claiming And agent workload management

    for (const combination of scoredCombinations) {
      if (
        !usedAgents.has(combination.agentId) &&
        !usedTasks.has(combination.taskId)
      ) {
        try {
          // eslint-disable-next-line no-await-in-loop -- Sequential processing prevents race conditions
          const claimResult = await this.taskManager.claimTask(
            combination.taskId,
            combination.agentId,
            'normal',
          );

          if (claimResult.success) {
            assignments.push({
              agentId: combination.agentId,
              taskId: combination.taskId,
              score: combination.score,
              claimedAt: claimResult.claimedAt,
            });

            usedAgents.add(combination.agentId);
            usedTasks.add(combination.taskId);

            // Update agent workload
            // eslint-disable-next-line no-await-in-loop -- Sequential workload updates required
            await this.agentManager.updateAgentWorkload(combination.agentId, 1);
          } else {
            failedAssignments.push({
              agentId: combination.agentId,
              taskId: combination.taskId,
              reason: claimResult.reason,
            });
          }
        } catch {
          failedAssignments.push({
            agentId: combination.agentId,
            taskId: combination.taskId,
            reason: error.message,
          });
        }
      }
    }

    return {
      assignments: assignments,
      failedAssignments: failedAssignments,
      totalAssigned: assignments.length,
      totalFailed: failedAssignments.length,
    };
  }

  /**
   * Round-robin task distribution
   * @param {Array} agents - Available agents
   * @param {Array} tasks - Available tasks
   * @returns {Promise<Object>} Distribution result
   */
  async roundRobinDistribution(agents, tasks) {
    const assignments = [];
    const failedAssignments = [];
    let agentIndex = 0;

    // Round-robin task assignment - sequential to maintain order And prevent conflicts

    for (const task of tasks) {
      if (agents.length === 0) {
        break;
      }

      const agent = agents[agentIndex % agents.length];

      if (agent.workload < agent.maxConcurrentTasks) {
        try {
          // eslint-disable-next-line no-await-in-loop -- Sequential round-robin assignment
          const claimResult = await this.taskManager.claimTask(
            task.id,
            agent.agentId,
            'normal',
          );

          if (claimResult.success) {
            assignments.push({
              agentId: agent.agentId,
              taskId: task.id,
              claimedAt: claimResult.claimedAt,
            });

            // eslint-disable-next-line no-await-in-loop -- Sequential workload updates required
            await this.agentManager.updateAgentWorkload(agent.agentId, 1);
          } else {
            failedAssignments.push({
              agentId: agent.agentId,
              taskId: task.id,
              reason: claimResult.reason,
            });
          }
        } catch {
          failedAssignments.push({
            agentId: agent.agentId,
            taskId: task.id,
            reason: error.message,
          });
        }
      }

      agentIndex++;
    }

    return {
      assignments: assignments,
      failedAssignments: failedAssignments,
      totalAssigned: assignments.length,
      totalFailed: failedAssignments.length,
    };
  }

  /**
   * Capability-based task distribution
   * @param {Array} agents - Available agents
   * @param {Array} tasks - Available tasks
   * @returns {Promise<Object>} Distribution result
   */
  async capabilityBasedDistribution(agents, tasks) {
    const assignments = [];
    const failedAssignments = [];

    // Capability-based task assignment - sequential to ensure proper agent selection

    for (const task of tasks) {
      // Find the best agent for this task based on capabilities
      // eslint-disable-next-line no-await-in-loop -- Sequential capability matching required
      const bestAgent = await this.agentManager.findBestAgentForTask(task);

      if (bestAgent) {
        try {
          // eslint-disable-next-line no-await-in-loop -- Sequential task claiming
          const claimResult = await this.taskManager.claimTask(
            task.id,
            bestAgent,
            'normal',
          );

          if (claimResult.success) {
            assignments.push({
              agentId: bestAgent,
              taskId: task.id,
              claimedAt: claimResult.claimedAt,
            });

            // eslint-disable-next-line no-await-in-loop -- Sequential workload updates required
            await this.agentManager.updateAgentWorkload(bestAgent, 1);
          } else {
            failedAssignments.push({
              agentId: bestAgent,
              taskId: task.id,
              reason: claimResult.reason,
            });
          }
        } catch {
          failedAssignments.push({
            agentId: bestAgent,
            taskId: task.id,
            reason: error.message,
          });
        }
      } else {
        failedAssignments.push({
          agentId: null,
          taskId: task.id,
          reason: 'No suitable agent found',
        });
      }
    }

    return {
      assignments: assignments,
      failedAssignments: failedAssignments,
      totalAssigned: assignments.length,
      totalFailed: failedAssignments.length,
    };
  }

  /**
   * Load-balanced task distribution
   * @param {Array} agents - Available agents
   * @param {Array} tasks - Available tasks
   * @returns {Promise<Object>} Distribution result
   */
  async loadBalancedDistribution(agents, tasks) {
    const assignments = [];
    const failedAssignments = [];

    // Sort agents by current workload (ascending)
    const sortedAgents = [...agents].sort((a, b) => a.workload - b.workload);

    // Load-balanced task assignment - sequential to maintain accurate workload tracking

    for (const task of tasks) {
      // Find agent with lowest workload That can handle the task
      const availableAgent = sortedAgents.find(
        (agent) => agent.workload < agent.maxConcurrentTasks,
      );

      if (availableAgent) {
        try {
          // eslint-disable-next-line no-await-in-loop -- Sequential load-balanced assignment
          const claimResult = await this.taskManager.claimTask(
            task.id,
            availableAgent.agentId,
            'normal',
          );

          if (claimResult.success) {
            assignments.push({
              agentId: availableAgent.agentId,
              taskId: task.id,
              claimedAt: claimResult.claimedAt,
            });

            // Update workload for sorting
            availableAgent.workload++;
            // eslint-disable-next-line no-await-in-loop -- Sequential workload updates required
            await this.agentManager.updateAgentWorkload(
              availableAgent.agentId,
              1,
            );

            // Re-sort agents by workload
            sortedAgents.sort((a, b) => a.workload - b.workload);
          } else {
            failedAssignments.push({
              agentId: availableAgent.agentId,
              taskId: task.id,
              reason: claimResult.reason,
            });
          }
        } catch {
          failedAssignments.push({
            agentId: availableAgent.agentId,
            taskId: task.id,
            reason: error.message,
          });
        }
      } else {
        failedAssignments.push({
          agentId: null,
          taskId: task.id,
          reason: 'No available agents with capacity',
        });
      }
    }

    return {
      assignments: assignments,
      failedAssignments: failedAssignments,
      totalAssigned: assignments.length,
      totalFailed: failedAssignments.length,
    };
  }

  /**
   * Calculate agent-task compatibility score
   * @param {Object} agent - Agent object
   * @param {Object} task - Task object
   * @returns {number} Compatibility score
   */
  calculateAgentTaskScore(agent, task) {
    let score = 0;

    // Role match
    if (agent.role === task.mode?.toLowerCase()) {
      score += 50;
    }

    // Specialization match
    if (
      task.specialization &&
      agent.specialization.includes(task.specialization)
    ) {
      score += 30;
    }

    // Capability match
    if (task.required_capabilities) {
      const matches = task.required_capabilities.filter((cap) =>
        agent.capabilities.includes(cap),
      ).length;
      score += matches * 10;
    }

    // Priority bonus
    if (task.priority === 'high') {
      score += 20;
    }
    if (task.priority === 'medium') {
      score += 10;
    }

    // Workload penalty
    score -= agent.workload * 5;

    return Math.max(0, score);
  }

  /**
   * Check statuses of multiple tasks
   * @param {Array} taskIds - Task IDs to check
   * @returns {Promise<Object>} Task status summary
   */
  async checkTaskStatuses(taskIds) {
    const todoData = await this.taskManager.readTodo();
    const tasks = taskIds
      .map((id) => todoData.tasks.find((t) => t.id === id))
      .filter((t) => t);

    const completed = tasks.filter((t) => t.status === 'completed').length;
    const failed = tasks.filter(
      (t) => t.status === 'blocked' || t.status === 'failed',
    ).length;
    const inProgress = tasks.filter((t) => t.status === 'in_progress').length;
    const pending = tasks.filter((t) => t.status === 'pending').length;

    return {
      allCompleted: completed === taskIds.length,
      anyFailed: failed > 0,
      tasks: tasks,
      summary: {
        completed: completed,
        failed: failed,
        inProgress: inProgress,
        pending: pending,
        total: taskIds.length,
      },
    };
  }

  /**
   * Calculate coordination progress
   * @param {Array} taskIds - Task IDs in coordination
   * @returns {Promise<number>} Progress percentage
   */
  async calculateCoordinationProgress(taskIds) {
    const statuses = await this.checkTaskStatuses(taskIds);
    return Math.round(
      (statuses.summary.completed / statuses.summary.total) * 100,
    );
  }

  /**
   * Handle coordination timeout
   * @param {string} executionId - Execution ID
   * @param {Object} coordination - Coordination object
   */
  handleCoordinationTimeout(executionId, coordination) {
    this.logger.addFlow(
      `Coordination ${executionId} timed out after ${coordination.timeout}ms`,
    );

    // Mark coordination as timed out
    this.coordinationResults.set(executionId, {
      success: false,
      reason: 'timeout',
      duration: Date.now() - coordination.startTime,
    });

    // TODO: Implement timeout recovery strategies
  }

  /**
   * Handle coordination failure
   * @param {string} executionId - Execution ID
   * @param {Object} coordination - Coordination object
   * @param {Object} taskStatuses - Task status summary
   */
  handleCoordinationFailure(executionId, coordination, taskStatuses) {
    this.logger.addFlow(
      `Coordination ${executionId} failed with ${taskStatuses.summary.failed} failed tasks`,
    );

    this.coordinationResults.set(executionId, {
      success: false,
      reason: 'task_failures',
      failedTasks: taskStatuses.summary.failed,
      duration: Date.now() - coordination.startTime,
    });

    // TODO: Implement failure recovery strategies
  }

  /**
   * Get orchestration statistics
   * @returns {Promise<Object>} Orchestration statistics
   */
  async getOrchestrationStatistics() {
    const [agentStats, taskStats, lockStats] = await Promise.all([
      this.agentManager.getAgentStatistics(),
      this.taskManager.getMultiAgentStatistics(),
      this.lockManager.getStatistics(),
    ]);

    return {
      agents: agentStats,
      tasks: taskStats,
      locks: lockStats,
      coordinations: {
        active: this.activeCoordinations.size,
        completed: this.coordinationResults.size,
      },
      performance: {
        operationsPerformed:
          this.coordinationResults.size + this.activeCoordinations.size,
        averageCoordinationTime: this._calculateAverageCoordinationTime(),
        systemUptime: Date.now() - (this.systemStartTime || Date.now()),
        memory: process.memoryUsage(),
        lastUpdate: new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Calculate average coordination time from completed coordinations
   * @private
   * @returns {number} Average coordination time in milliseconds
   */
  _calculateAverageCoordinationTime() {
    if (this.coordinationResults.size === 0) {
      return 0;
    }

    let totalTime = 0;
    let count = 0;

    for (const [_coordinationId, result] of this.coordinationResults) {
      if (result.startTime && RESULT.endTime) {
        totalTime += RESULT.endTime - RESULT.startTime;
        count++;
      }
    }

    return count > 0 ? totalTime / count : 0;
  }

  /**
   * Cleanup orchestrator resources
   */
  async cleanup() {
    await this.agentManager.cleanup();
    await this.lockManager.cleanup();

    this.activeCoordinations.clear();
    this.coordinationResults.clear();
  }
}

module.exports = MultiAgentOrchestrator;
