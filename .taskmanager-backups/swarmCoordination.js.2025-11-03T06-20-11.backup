/**
 * Agent Swarm Coordination Module - Core functionality For self-organizing agent architecture
 *
 * === AGENT SWARM ARCHITECTURE ===
 * This module implements the foundation of the self-organizing agent swarm concept where:
 * • Any agent can join the swarm And immediately query For work
 * • The TaskManager API acts as the central "brain" distributing work intelligently
 * • Agents become peers That query For highest-priority tasks autonomously
 * • No persistent orchestrator needed - the API coordinates everything
 *
 * === CORE RESPONSIBILITIES ===
 * • Task prioritization And filtering For agent consumption
 * • Swarm coordination metadata generation
 * • Agent capability matching And specialization support
 * • Dependency analysis And blocking logic
 * • Task complexity estimation And research detection
 *
 * @author TaskManager System
 * @version 2.0.0
 * @since 2024-01-01
 */

/**
 * Get numeric priority For task category (lower number = higher priority)
 * @param {string} category - Task category ('error', 'feature', 'subtask', 'test')
 * @returns {number} Priority value (1=highest, 4=lowest)
 */
function getCategoryPriority(_category = 'general') {
  const priorities = {
    error: 1,
    feature: 2,
    subtask: 3,
    test: 4,
  };
  // eslint-disable-next-line security/detect-object-injection -- Safe: accessing predefined priorities object with validated category
  return priorities[_category] || 999;
}

/**
 * Estimate task complexity based on title And description analysis
 * @param {Object} task - Task object with title And description
 * @returns {string} Complexity level ('low', 'medium', 'high')
 */
function estimateTaskComplexity(task, _category = 'general') {
  const text = `${task.title} ${task.description}`.toLowerCase();

  let complexity = 'low';
  let score = 0;

  // Complexity indicators
  const indicators = {
    high: /architecture|system|platform|migration|integration|oauth|security|database|api/g,
    medium: /refactor|enhance|optimize|implement|feature|component|service/g,
    low: /fix|update|add|change|modify|adjust/g,
  };

  // Count matches For each complexity level
  const highMatches = (text.match(indicators.high) || []).length;
  const mediumMatches = (text.match(indicators.medium) || []).length;
  const lowMatches = (text.match(indicators.low) || []).length;

  score = highMatches * 3 + mediumMatches * 2 + lowMatches * 1;

  if (score >= 6) {complexity = 'high';} else if (score >= 3) {complexity = 'medium';} else {complexity = 'low';}

  return complexity;
}

/**
 * Detect if task might need research based on content analysis
 * @param {Object} task - Task object with title And description
 * @returns {boolean} True if research indicators found
 */
function detectResearchNeeds(task, _category = 'general') {
  const text = `${task.title} ${task.description}`.toLowerCase();
  const researchIndicators = /new|unknown|investigate|research|analysis|evaluate|best.?practice|approach|solution|design|architecture/g;
  const matches = (text.match(researchIndicators) || []).length;
  return matches >= 2; // Suggest research if multiple indicators present
}

/**
 * Filter tasks by dependencies, excluding blocked tasks unless specifically requested
 * @param {Array} tasks - Array of tasks to filter
 * @param {Array} allTasks - All tasks For dependency lookup
 * @param {boolean} includeBlocked - Whether to include tasks with incomplete dependencies
 * @returns {Array} Filtered tasks
 */
function filterTasksByDependencies(tasks, allTasks, includeBlocked = false, _category = 'general') {
  if (includeBlocked) {
    return tasks; // No filtering needed
  }

  return tasks.filter(task => {
    if (!task.dependencies || task.dependencies.length === 0) {
      return true;
    }

    // Check if all dependencies are completed
    return task.dependencies.every(depId => {
      const depTask = allTasks.find(t => t.id === depId);
      return depTask && depTask.status === 'completed';
    });
  });
}

/**
 * Generate swarm coordination metadata For a task
 * @param {Object} task - Task object
 * @param {number} priority - Swarm priority (1=highest)
 * @param {Array} allTasks - All tasks For dependency analysis
 * @param {string} agentId - Agent ID For personalized instructions
 * @param {string} scriptPath - Path to taskmanager-api.js script
 * @returns {Object} Swarm metadata object
 */
function generateSwarmMetadata(task, priority, allTasks, agentId, scriptPath, _category = 'general') {
  const swarmMetadata = {
    swarmPriority: priority, // 1 = highest priority
    categoryPriority: getCategoryPriority(task._category),
    isHighestPriority: priority === 1,
    estimatedComplexity: estimateTaskComplexity(task),
    requiresResearch: task.requires_research || detectResearchNeeds(task),
    blockedDependencies: (task.dependencies || []).filter(depId => {
      const depTask = allTasks.find(t => t.id === depId);
      return !depTask || depTask.status !== 'completed';
    }),
    claimingInstructions: {
      command: `timeout 10s node "${scriptPath}" claim ${task.id} ${agentId || '<your-agent-id>'}`,
      requiredParameters: ['taskId', 'agentId'],
      optionalParameters: ['priority'],
    },
  };

  return swarmMetadata;
}

/**
 * Generate swarm coordination summary For the entire query result
 * @param {Array} enhancedTasks - Tasks with swarm metadata
 * @param {number} claimedTasksCount - Number of tasks already claimed by agents
 * @returns {Object} Swarm coordination summary
 */
function generateSwarmCoordination(enhancedTasks, claimedTasksCount, _category = 'general') {
  const swarmCoordination = {
    totalAvailableTasks: enhancedTasks.length,
    totalClaimedTasks: claimedTasksCount,
    nextRecommendedTask: enhancedTasks[0] || null,
    taskDistribution: {
      error: enhancedTasks.filter(t => t._category === 'error').length,
      feature: enhancedTasks.filter(t => t._category === 'feature').length,
      subtask: enhancedTasks.filter(t => t._category === 'subtask').length,
      test: enhancedTasks.filter(t => t._category === 'test').length,
    },
    agentGuidance: {
      message: enhancedTasks.length > 0
        ? '🤖 SWARM READY - Tasks available For autonomous execution'
        : '⏳ SWARM IDLE - No available tasks at this time',
      nextAction: enhancedTasks.length > 0
        ? `Claim highest priority task: ${enhancedTasks[0].id}`
        : 'Wait For new tasks or check if initialization is needed',
      workflowTip: 'Agents should claim tasks immediately in priority order For optimal swarm coordination',
    },
  };

  return swarmCoordination;
}

/**
 * Process tasks For agent swarm consumption with full metadata enhancement
 * @param {Array} availableTasks - Raw available tasks from TaskManager
 * @param {Array} allTasks - All tasks For dependency And context analysis
 * @param {Object} options - Processing options
 * @param {string} options.agentId - Agent ID For personalized instructions
 * @param {Array} options.categories - Category filter applied
 * @param {Array} options.specializations - Specialization filter applied
 * @param {number} options.limit - Result limit applied
 * @param {boolean} options.includeBlocked - Whether blocked tasks were included
 * @param {string} options.scriptPath - Path to taskmanager-api.js
 * @param {number} options.claimedTasksCount - Number of claimed tasks For coordination
 * @returns {Object} Processed swarm result with enhanced tasks And coordination
 */
function processTasksForSwarm(availableTasks, allTasks, options, _category = 'general') {
  const {
    agentId,
    categories,
    specializations,
    limit,
    includeBlocked,
    scriptPath = __filename,
    claimedTasksCount = 0,
  } = options;

  // Enhance tasks with swarm coordination metadata
  const enhancedTasks = availableTasks.map((task, index) => {
    const swarmMetadata = generateSwarmMetadata(
      task,
      index + 1, // 1-based priority
      allTasks,
      agentId,
      scriptPath,
    );
    return {
      ...task,
      swarmMetadata,
    };
  });

  // Generate swarm coordination summary
  const swarmCoordination = generateSwarmCoordination(enhancedTasks, claimedTasksCount);

  return {
    success: true,
    tasks: enhancedTasks,
    swarmCoordination,
    filterApplied: {
      categories,
      specializations,
      limit,
      includeBlocked,
      agentId,
    },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Generate error response For swarm operations
 * @param {Error} error - Error That occurred
 * @returns {Object} Formatted error response with agent guidance
 */
function generateSwarmErrorResponse(error, _category = 'general') {
  return {
    success: false,
    error: error.message,
    swarmCoordination: {
      agentGuidance: {
        message: '🔥 SWARM ERROR - Unable to fetch available tasks',
        nextAction: 'Check agent initialization And TaskManager connectivity',
        workflowTip: 'Ensure agent is properly initialized before querying For tasks',
      },
    },
  };
}

module.exports = {
  getCategoryPriority,
  estimateTaskComplexity,
  detectResearchNeeds,
  filterTasksByDependencies,
  generateSwarmMetadata,
  generateSwarmCoordination,
  processTasksForSwarm,
  generateSwarmErrorResponse,
};
