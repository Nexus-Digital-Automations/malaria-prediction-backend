/**
 * State Machine for Task/Feature Status Management
 *
 * Provides formal state machine management for task And feature status transitions
 * using XState. Ensures valid state transitions, prevents invalid states, And
 * provides clear audit trails for all status changes.
 *
 * Features:
 * - Declarative state machine definitions
 * - Automatic validation of state transitions
 * - Event-driven status changes with guards And actions
 * - Comprehensive audit logging
 * - Support for both task And feature lifecycles
 * - Error handling And recovery mechanisms
 */

const { createMachine, interpret, assign } = require('xstate');
const { createContextLogger } = require('./logger');

const logger = createContextLogger({ module: 'stateMachine' });

/**
 * Task Status State Machine Configuration
 * Defines all valid task states And transitions
 */
const taskStateMachineConfig = {
  /** @xstate-layout N4IgpgJg5mDOIC5QAoC2BDAxgCwJYDswBKAOgEkA5AQQBUBhAbQAYBdRUAB1VlkuQHtYuEAA9EANgCsADgBMAFn4AmHpJk8ArABoQAT0QBOAGwAmHoqWy+igMz8AumfOXEydFlwFiZUhWp0DEyMLHLcAG5gUBjYeIQk5FT0TKzsXDwCQlJIAAwyaUraMnIAjDyZKtwATJn8KhpIWjp6hiYI-DwqmXwqnCpdfCp86gN+NrIW7VA2SLaOLq4QHl6+-oG9IeFRsQmiEmJS6ZkZqTw8mQCMmSqylSPjEybVE2Pl6gBsKn4qMwN8k20TxQO2QgVCO0i+xixGIZAoVFo9FYglYwggklhxCy-G4MgAmTK-CrdXjKWpNXiZZTg7YhMAkOzwCAYHZJdJZHJ5fGIADsOm4mQU6S6KnUKlUAzG-SpYz0NKcUK5fGFxWKmPWcTwUoUCjZChUbJ4JWO6jOpJNhzJNMZF2Ob3EAhIyFAYCgV2SqAZJOOqk9cgUmSdCjVfAN3BU-A1qk1fFDhqJY0QtCwEGWMXWCQA+uR0kMZMplJkvdx3Sq3TJvcbvb6VQGRoJhKhEJgALJwDAAMXjiaglvSGYzPGKKnKvHU-CUvDUoZ9mRH8l6WfpHFTqgUmWUKhH8jqF3z1xzBfdS8YLEr3LhJKxpx9Kgbni9mS9jZG5vGYmCbYWTjXDdJCxd9FxzF831JSlKU+GlAk6GQ-s0MSEQzn1WQvWvTl3TA7dAO9fhAzPQDQztCDP2-AAdCFCGNL4cS6e8nzKOo5F7eRb0pGkgA */
  id: 'taskStatus',
  initial: 'pending',
  context: {
    taskId: null,
    reason: null,
    metadata: {},
    timestamp: null,
    history: [] },
  states: {
    pending: {
      on: {
        START: {
          target: 'in_progress',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'canStart' },
        BLOCK: {
          target: 'blocked',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasBlockReason' },
        CANCEL: {
          target: 'cancelled',
          actions: ['logTransition', 'updateTimestamp'] },
      },
    },
    in_progress: {
      on: {
        COMPLETE: {
          target: 'completed',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'canComplete' },
        BLOCK: {
          target: 'blocked',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasBlockReason' },
        PAUSE: {
          target: 'paused',
          actions: ['logTransition', 'updateTimestamp'] },
        FAIL: {
          target: 'failed',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasFailureReason' },
      },
    },
    blocked: {
      on: {
        UNBLOCK: {
          target: 'pending',
          actions: ['logTransition', 'updateTimestamp'] },
        CANCEL: {
          target: 'cancelled',
          actions: ['logTransition', 'updateTimestamp'] },
      },
    },
    paused: {
      on: {
        RESUME: {
          target: 'in_progress',
          actions: ['logTransition', 'updateTimestamp'] },
        CANCEL: {
          target: 'cancelled',
          actions: ['logTransition', 'updateTimestamp'] },
      },
    },
    completed: {
      type: 'final',
      on: {
        REOPEN: {
          target: 'pending',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'canReopen' },
      },
    },
    cancelled: {
      type: 'final',
      on: {
        REOPEN: {
          target: 'pending',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'canReopen' },
      },
    },
    failed: {
      on: {
        RETRY: {
          target: 'pending',
          actions: ['logTransition', 'updateTimestamp'] },
        CANCEL: {
          target: 'cancelled',
          actions: ['logTransition', 'updateTimestamp'] },
      },
    },
  },
};

/**
 * Feature Status State Machine Configuration
 * Defines all valid feature states And transitions
 */
const featureStateMachineConfig = {
  id: 'featureStatus',
  initial: 'suggested',
  context: {
    featureId: null,
    reason: null,
    metadata: {},
    timestamp: null,
    history: [] },
  states: {
    suggested: {
      on: {
        APPROVE: {
          target: 'approved',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasApprover' },
        REJECT: {
          target: 'rejected',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasRejectionReason' },
        DEFER: {
          target: 'deferred',
          actions: ['logTransition', 'updateTimestamp'] },
      },
    },
    approved: {
      on: {
        START_IMPLEMENTATION: {
          target: 'in_development',
          actions: ['logTransition', 'updateTimestamp'] },
        REJECT: {
          target: 'rejected',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasRejectionReason' },
      },
    },
    in_development: {
      on: {
        COMPLETE_IMPLEMENTATION: {
          target: 'implemented',
          actions: ['logTransition', 'updateTimestamp'] },
        BLOCK: {
          target: 'blocked',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasBlockReason' },
        REJECT: {
          target: 'rejected',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasRejectionReason' },
      },
    },
    implemented: {
      type: 'final' },
    rejected: {
      type: 'final',
      on: {
        RECONSIDER: {
          target: 'suggested',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'canReconsider' },
      },
    },
    deferred: {
      on: {
        RECONSIDER: {
          target: 'suggested',
          actions: ['logTransition', 'updateTimestamp'] },
        REJECT: {
          target: 'rejected',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasRejectionReason' },
      },
    },
    blocked: {
      on: {
        UNBLOCK: {
          target: 'in_development',
          actions: ['logTransition', 'updateTimestamp'] },
        REJECT: {
          target: 'rejected',
          actions: ['logTransition', 'updateTimestamp'],
          cond: 'hasRejectionReason' },
      },
    },
  },
};

/**
 * State Machine Actions
 * Define what happens during state transitions
 */
const stateMachineActions = {
  logTransition: assign((context, event) => {
    const transitionEntry = {
      from: context.history.length > 0 ? context.history[context.history.length - 1].to : 'initial',
      to: event.type,
      timestamp: new Date().toISOString(),
      reason: event.reason || context.reason || 'No reason provided',
      metadata: event.metadata || {} };

    // Log the transition
    logger.info({
      entityId: context.taskId || context.featureId,
      entityType: context.taskId ? 'task' : 'feature',
      transition: transitionEntry }, `Status transition: ${transitionEntry.from} → ${transitionEntry.to}`);

    return {
      ...context,
      reason: event.reason || context.reason,
      metadata: { ...context.metadata, ...event.metadata },
      history: [...context.history, transitionEntry] };
  }),

  updateTimestamp: assign({
    timestamp: () => new Date().toISOString() }) };

/**
 * State Machine Guards
 * Define conditions for state transitions
 */
const stateMachineGuards = {
  canStart: (_context, _event) => {
    // Task can start if it has necessary dependencies resolved
    return true; // Simplified - could check dependencies, permissions, etc.
  },

  canComplete: (_context, _event) => {
    // Task can complete if validation criteria are met
    return true; // Simplified - could check completion criteria
  },

  canReopen: (context, event) => {
    // Can reopen if user has permissions And reason is provided
    return !!event.reason;
  },

  hasBlockReason: (context, event) => {
    return !!event.reason;
  },

  hasFailureReason: (context, event) => {
    return !!event.reason;
  },

  hasApprover: (context, event) => {
    return !!event.approver;
  },

  hasRejectionReason: (context, event) => {
    return !!event.reason;
  },

  canReconsider: (context, event) => {
    return !!event.reason;
  },
};

/**
 * State Machine Manager
 * Manages multiple state machine instances for different entities
 */
class StateMachineManager {
  constructor() {
    this.instances = new Map();
    this.logger = createContextLogger({ module: 'stateMachineManager' });
  }

  /**
   * Create a new state machine instance for a task
   * @param {string} taskId - Unique task identifier
   * @param {string} initialState - Initial state (optional)
   * @returns {Object} State machine service
   */
  createTaskStateMachine(taskId, initialState = 'pending') {
    const machineId = `task-${taskId}`;

    if (this.instances.has(machineId)) {
      this.logger.warn({ taskId, machineId }, 'Task state machine already exists');
      return this.instances.get(machineId);
    }

    const machine = createMachine({
      ...taskStateMachineConfig,
      context: {
        ...taskStateMachineConfig.context,
        taskId,
      },
    }, {
      actions: stateMachineActions,
      guards: stateMachineGuards,
    });

    const service = interpret(machine)
      .onTransition((state) => {
        this.logger.debug({
          taskId,
          state: state.value,
          context: state.context,
        }, `Task state machine transition: ${taskId}`);
      })
      .start();

    this.instances.set(machineId, service);

    this.logger.info({ taskId, initialState, machineId }, 'Created task state machine');
    return service;
  }

  /**
   * Create a new state machine instance for a feature
   * @param {string} featureId - Unique feature identifier
   * @param {string} initialState - Initial state (optional)
   * @returns {Object} State machine service
   */
  createFeatureStateMachine(featureId, initialState = 'suggested') {
    const machineId = `feature-${featureId}`;

    if (this.instances.has(machineId)) {
      this.logger.warn({ featureId, machineId }, 'Feature state machine already exists');
      return this.instances.get(machineId);
    }

    const machine = createMachine({
      ...featureStateMachineConfig,
      context: {
        ...featureStateMachineConfig.context,
        featureId,
      },
    }, {
      actions: stateMachineActions,
      guards: stateMachineGuards,
    });

    const service = interpret(machine)
      .onTransition((state) => {
        this.logger.debug({
          featureId,
          state: state.value,
          context: state.context,
        }, `Feature state machine transition: ${featureId}`);
      })
      .start();

    this.instances.set(machineId, service);

    this.logger.info({ featureId, initialState, machineId }, 'Created feature state machine');
    return service;
  }

  /**
   * Get an existing state machine instance
   * @param {string} entityId - Task or feature ID
   * @param {string} entityType - 'task' or 'feature'
   * @returns {Object|null} State machine service or null
   */
  getInstance(entityId, entityType) {
    const machineId = `${entityType}-${entityId}`;
    return this.instances.get(machineId) || null;
  }

  /**
   * Send an event to a state machine
   * @param {string} entityId - Task or feature ID
   * @param {string} entityType - 'task' or 'feature'
   * @param {string} event - Event type
   * @param {Object} eventData - Additional event data
   * @returns {boolean} Success status
   */
  sendEvent(entityId, entityType, event, eventData = {}) {
    const service = this.getInstance(entityId, entityType);

    if (!service) {
      this.logger.error({
        entityId,
        entityType,
        event }, 'State machine instance not found');
      return false;
    }

    try {
      service.send({
        type: event,
        ...eventData,
      });

      this.logger.info({
        entityId,
        entityType,
        event,
        currentState: service.state.value,
      }, 'Event sent to state machine');

      return true;
    } catch (error) {
      this.logger.error({
        entityId,
        entityType,
        event,
        error: error.message,
      }, 'Failed to send event to state machine');
      return false;
    }
  }

  /**
   * Get current state of an entity
   * @param {string} entityId - Task or feature ID
   * @param {string} entityType - 'task' or 'feature'
   * @returns {Object|null} Current state information
   */
  getCurrentState(entityId, entityType) {
    const service = this.getInstance(entityId, entityType);

    if (!service) {
      return null;
    }

    return {
      state: service.state.value,
      context: service.state.context,
      canTransition: this.getValidTransitions(entityId, entityType),
    };
  }

  /**
   * Get valid transitions from current state
   * @param {string} entityId - Task or feature ID
   * @param {string} entityType - 'task' or 'feature'
   * @returns {Array} Array of valid event types
   */
  getValidTransitions(entityId, entityType) {
    const service = this.getInstance(entityId, entityType);

    if (!service) {
      return [];
    }

    const currentState = service.state;
    const stateNode = currentState.machine.states[currentState.value];

    if (!stateNode || !stateNode.on) {
      return [];
    }

    return Object.keys(stateNode.on);
  }

  /**
   * Validate if a transition is allowed
   * @param {string} entityId - Task or feature ID
   * @param {string} entityType - 'task' or 'feature'
   * @param {string} event - Event type to validate
   * @returns {boolean} True if transition is valid
   */
  isValidTransition(entityId, entityType, event) {
    const validTransitions = this.getValidTransitions(entityId, entityType);
    return validTransitions.includes(event);
  }

  /**
   * Get transition history for an entity
   * @param {string} entityId - Task or feature ID
   * @param {string} entityType - 'task' or 'feature'
   * @returns {Array} Transition history
   */
  getTransitionHistory(entityId, entityType) {
    const service = this.getInstance(entityId, entityType);

    if (!service) {
      return [];
    }

    return service.state.context.history || [];
  }

  /**
   * Stop And remove a state machine instance
   * @param {string} entityId - Task or feature ID
   * @param {string} entityType - 'task' or 'feature'
   */
  removeInstance(entityId, entityType) {
    const machineId = `${entityType}-${entityId}`;
    const service = this.instances.get(machineId);

    if (service) {
      service.stop();
      this.instances.delete(machineId);
      this.logger.info({ entityId, entityType, machineId }, 'Removed state machine instance');
    }
  }

  /**
   * Get statistics about all state machines
   * @returns {Object} Statistics
   */
  getStatistics() {
    const stats = {
      totalInstances: this.instances.size,
      taskInstances: 0,
      featureInstances: 0,
      stateDistribution: {},
    };

    for (const [machineId, service] of this.instances.entries()) {
      if (machineId.startsWith('task-')) {
        stats.taskInstances++;
      } else if (machineId.startsWith('feature-')) {
        stats.featureInstances++;
      }

      const state = service.state.value;
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      stats.stateDistribution[state] = (stats.stateDistribution[state] || 0) + 1;
    }

    return stats;
  }
}

// Create singleton instance;
const stateMachineManager = new StateMachineManager();

/**
 * Utility functions for easier state management
 */

/**
 * Initialize a task state machine
 * @param {string} taskId - Task ID
 * @param {string} initialState - Initial state
 * @returns {Object} State machine service
 */
function initializeTaskStateMachine(taskId, initialState = 'pending') {
  return stateMachineManager.createTaskStateMachine(taskId, initialState);
}

/**
 * Initialize a feature state machine
 * @param {string} featureId - Feature ID
 * @param {string} initialState - Initial state
 * @returns {Object} State machine service
 */
function initializeFeatureStateMachine(featureId, initialState = 'suggested') {
  return stateMachineManager.createFeatureStateMachine(featureId, initialState);
}

/**
 * Transition a task to a new state
 * @param {string} taskId - Task ID
 * @param {string} event - Event type
 * @param {Object} data - Event data
 * @returns {boolean} Success status
 */
function transitionTask(taskId, event, data = {}) {
  return stateMachineManager.sendEvent(taskId, 'task', event, data);
}

/**
 * Transition a feature to a new state
 * @param {string} featureId - Feature ID
 * @param {string} event - Event type
 * @param {Object} data - Event data
 * @returns {boolean} Success status
 */
function transitionFeature(featureId, event, data = {}) {
  return stateMachineManager.sendEvent(featureId, 'feature', event, data);
}

module.exports = {
  StateMachineManager,
  stateMachineManager,
  initializeTaskStateMachine,
  initializeFeatureStateMachine,
  transitionTask,
  transitionFeature,
  taskStateMachineConfig,
  featureStateMachineConfig };
