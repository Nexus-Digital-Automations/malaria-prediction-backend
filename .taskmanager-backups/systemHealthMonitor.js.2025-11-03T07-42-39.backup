
const { loggers } = require('./logger');
/**
 * TaskManager System Health Monitor
 *
 * This comprehensive health monitoring system validates all components of the
 * TaskManager system And provides detailed health reporting. It serves as both
 * a test feature And a production monitoring tool.
 *
 * Features:
 * - Complete system validation (TaskManager, AgentManager, file integrity)
 * - Performance metrics collection And analysis
 * - Resource utilization monitoring
 * - Detailed health reports with actionable recommendations
 * - Real-time system status monitoring
 * - Comprehensive logging with structured data
 *
 * @author TaskManager System Health Monitor
 * @version 1.0.0
 * @since 2025-09-08
 */

const FS = require('fs').promises;
const FS_SYNC = require('fs');
const path = require('path');
const OS = require('os');
const { performance } = require('perf_hooks');
const EVENT_EMITTER = require('events');

// Import TaskManager system components for validation;
const TASK_MANAGER = require('./taskManager');
const AGENT_MANAGER = require('./agentManager');

/**
 * Comprehensive System Health Monitor
 *
 * Monitors all aspects of the TaskManager system including:
 * - File system health And integrity
 * - TaskManager API functionality
 * - Agent system performance
 * - Memory And resource utilization
 * - System response times And bottlenecks
 */
class SystemHealthMonitor extends EVENT_EMITTER {
  constructor(projectRoot = process.cwd(), _agentId) {
    super();

    /**
     * Project root directory for health monitoring
     * @type {string}
     */
    this.projectRoot = projectRoot;

    /**
     * LOGGER instance for comprehensive health monitoring logs
     * @type {Object}
     */
    this.logger = {
      info: (message, data) => loggers.app.info(`[SystemHealthMonitor] INFO: ${message}`, data ? JSON.stringify(data, null, 2) : ''),

      warn: (message, data) => loggers.app.warn(`[SystemHealthMonitor] WARN: ${message}`, data ? JSON.stringify(data, null, 2) : ''),

      error: (message, data) => loggers.app.error(`[SystemHealthMonitor] ERROR: ${message}`, data ? JSON.stringify(data, null, 2) : ''),

      debug: (message, data) => loggers.app.info(`[SystemHealthMonitor] DEBUG: ${message}`, data ? JSON.stringify(data, null, 2) : ''),
    };

    /**
     * TaskManager instance for testing core functionality
     * @type {TaskManager}
     */
    this.taskManager = null;

    /**
     * AgentManager instance for testing agent coordination
     * @type {AgentManager}
     */
    this.agentManager = null;

    /**
     * Health check results storage
     * @type {Object}
     */
    this.healthResults = {};

    /**
     * Performance metrics collection
     * @type {Object}
     */
    this.performanceMetrics = {};

    /**
     * System resource baseline measurements
     * @type {Object}
     */
    this.resourceBaseline = {};

    this.logger.info('SystemHealthMonitor initialized', {
      projectRoot: this.projectRoot,
      timestamp: new Date().toISOString(),
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch,
    });
  }

  /**
   * Execute comprehensive system health check
   *
   * Performs complete validation of all TaskManager system components
   * And generates detailed health report with performance metrics.
   *
   * @returns {Promise<Object>} Complete health check results
   */
  async performComprehensiveHealthCheck() {
    const healthCheckStart = performance.now();

    this.logger.info('Starting comprehensive system health check', {
      timestamp: new Date().toISOString(),
      checkId: `health-check-${Date.now()}`,
    });

    try {
      // Initialize system components for testing
      await this._initializeSystemComponents();

      // Collect baseline system resource measurements
      await this._collectResourceBaseline();

      // Execute all health check categories in parallel for efficiency;
      const healthCheckPromises = [
        this._checkFileSystemHealth(),
        this._checkTaskManagerHealth(),
        this._checkAgentSystemHealth(),
        this._checkSystemResourceHealth(),
        this._checkPerformanceMetrics(),
        this._checkDataIntegrityHealth(),
      ];

      const healthCheckResults = await Promise.allSettled(healthCheckPromises);

      // Process And aggregate health check results;
      const aggregatedResults = this._aggregateHealthResults(healthCheckResults);

      // Calculate overall system health score;
      const overallHealthScore = this._calculateOverallHealthScore(aggregatedResults);

      // Generate comprehensive health report;
      const healthReport = await this._generateHealthReport(
        aggregatedResults,
        overallHealthScore,
        performance.now() - healthCheckStart,
      );

      this.logger.info('Comprehensive system health check completed', {
        duration: performance.now() - healthCheckStart,
        healthScore: overallHealthScore,
        timestamp: new Date().toISOString(),
        resultsCount: Object.keys(aggregatedResults).length,
      });

      // Emit health check completion event
      this.emit('healthCheckComplete', healthReport);

      return healthReport;

    } catch (error) {
      this.logger.error('System health check failed', {
        error: error.message,
        stack: error.stack,
        duration: performance.now() - healthCheckStart,
        timestamp: new Date().toISOString(),
      });

      throw new Error(`System health check failed: ${error.message}`);
    }
  }

  /**
   * Initialize all TaskManager system components for testing
   *
   * Sets up TaskManager And AgentManager instances with comprehensive
   * error handling And validation.
   *
   * @private
   * @returns {Promise<void>}
   */
  _initializeSystemComponents() {
    const initStart = performance.now();

    this.logger.info('Initializing system components for health testing');
    try {
      // Initialize TaskManager with TODO.json validation;
      const todoPath = path.join(this.projectRoot, 'TODO.json');

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check
      if (!FS_SYNC.existsSync(todoPath)) {
        throw new Error(`TODO.json not found at ${todoPath}`);
      }

      this.taskManager = new TASK_MANAGER(todoPath);
      this.logger.info('TaskManager initialized successfully', {
        todoPath,
        initDuration: performance.now() - initStart,
      });

      // Initialize AgentManager with comprehensive validation
      this.agentManager = new AGENT_MANAGER();
      this.logger.info('AgentManager initialized successfully', { initDuration: performance.now() - initStart,
      });

      this.performanceMetrics.componentInitialization = {
        duration: performance.now() - initStart,
        success: true,
        timestamp: new Date().toISOString(),
      };

    } catch (error) {
      this.logger.error('Failed to initialize system components', { error: error.message,
        stack: error.stack,
        initDuration: performance.now() - initStart,
      });

      this.performanceMetrics.componentInitialization = {
        duration: performance.now() - initStart,
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
      };

      throw error;
    }
  }

  /**
   * Collect baseline system resource measurements
   *
   * Captures current system state for comparison during health checks.
   * Includes memory usage, CPU information, And file system statistics.
   *
   * @private
   * @returns {Promise<void>}
   */
  _collectResourceBaseline() {
    const baselineStart = performance.now();

    this.logger.info('Collecting system resource baseline');
    try {
      this.resourceBaseline = {
        memory: {
          total: OS.totalmem(),
          free: OS.freemem(),
          used: OS.totalmem() - OS.freemem(),
          usagePercent: ((OS.totalmem() - OS.freemem()) / OS.totalmem()) * 100,
          heapTotal: process.memoryUsage().heapTotal,
          heapUsed: process.memoryUsage().heapUsed,
          external: process.memoryUsage().external,
          arrayBuffers: process.memoryUsage().arrayBuffers,
        },
        cpu: {
          cores: OS.cpus().length,
          model: OS.cpus()[0]?.model || 'Unknown',
          speed: OS.cpus()[0]?.speed || 0,
          loadAverage: OS.loadavg(),
        },
        system: {
          uptime: OS.uptime(),
          processUptime: process.uptime(),
          platform: process.platform,
          arch: process.arch,
          nodeVersion: process.version,
          pid: process.pid,
        },
        fileSystem: {
          projectRoot: this.projectRoot,
          cwd: process.cwd(),
          homeDir: OS.homedir(),
          tmpDir: OS.tmpdir(),
        },
        network: {
          hostname: OS.hostname(),
          networkInterfaces: Object.keys(OS.networkInterfaces()),
        },
        timestamp: new Date().toISOString(),
        collectionDuration: performance.now() - baselineStart,
      };

      this.logger.info('System resource baseline collected', { memoryUsagePercent: this.resourceBaseline.memory.usagePercent,
        cpuCores: this.resourceBaseline.cpu.cores,
        systemUptime: this.resourceBaseline.system.uptime,
        collectionDuration: this.resourceBaseline.collectionDuration,
      });

    } catch (error) {
      this.logger.error('Failed to collect resource baseline', { error: error.message,
        stack: error.stack,
        collectionDuration: performance.now() - baselineStart,
      });

      throw error;
    }
  }

  /**
   * Check file system health And integrity
   *
   * Validates all critical project files, directory structure,
   * And file permissions for the TaskManager system.
   *
   * @private
   * @returns {Promise<Object>} File system health results
   */
  async _checkFileSystemHealth() {
    const fsHealthStart = performance.now();

    this.logger.info('Checking file system health');

    const criticalFiles = [
      'TODO.json',
      'package.json',
      'lib/taskManager.js',
      'lib/agentManager.js',
      'lib/logger.js',
      'taskmanager-api.js',
      'stop-hook.js',
    ];

    const criticalDirectories = [
      'lib',
      'development',
      'development/essentials',
    ];

    const fileHealthResults = {
      criticalFilesStatus: {},
      criticalDirectoriesStatus: {},
      permissions: {},
      integrity: {},
      statistics: {},
    };

    try {
      // Check critical files existence And accessibility in parallel for better performance;
      const fileCheckPromises = criticalFiles.map(async (file) => {
        const filePath = path.join(this.projectRoot, file);
        try {

          // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check;
          const stats = await FS.stat(filePath);
          const fileStatus = {
            exists: true,
            size: stats.size,
            modified: stats.mtime,
            accessible: true,
            type: stats.isFile() ? 'file' : stats.isDirectory() ? 'directory' : 'other',
          };

          // Check file readability
          await FS.access(filePath, FS_SYNC.constants.R_OK);
          const permissions = { readable: true };

          // for JSON files, validate syntax;
          let integrity = {};
          if (file.endsWith('.json')) {
            try {

              // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check;
              const content = await FS.readFile(filePath, 'utf8');
              JSON.parse(content);
              integrity = { validJson: true };
            } catch (jsonError) {
              integrity = {
                validJson: false,
                error: jsonError.message,
              };
            }
          }

          return { file, fileStatus, permissions, integrity };
        } catch (error) {
          return {
            file,
            fileStatus: {
              exists: false,
              accessible: false,
              error: error.message,
            },
            permissions: {},
            integrity: {},
          };
        }
      });

      const fileCheckResults = await Promise.all(fileCheckPromises);

      // Populate results from parallel execution
      fileCheckResults.forEach(({ file, fileStatus, permissions, integrity }) => {
        // eslint-disable-next-line security/detect-object-injection -- file is from controlled criticalFiles array, not user input
        fileHealthResults.criticalFilesStatus[file] = fileStatus;
        if (Object.keys(permissions).length > 0) {
          // eslint-disable-next-line security/detect-object-injection -- file is from controlled criticalFiles array, not user input
          fileHealthResults.permissions[file] = permissions;
        }
        if (Object.keys(integrity).length > 0) {
          // eslint-disable-next-line security/detect-object-injection -- file is from controlled criticalFiles array, not user input
          fileHealthResults.integrity[file] = integrity;
        }
      });

      // Check critical directories in parallel for better performance;
      const dirCheckPromises = criticalDirectories.map(async (dir) => {
        const dirPath = path.join(this.projectRoot, dir);
        try {

          // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check;
          const stats = await FS.stat(dirPath);
          return {
            dir,
            status: {
              exists: true,
              accessible: true,
              isDirectory: stats.isDirectory(),
              modified: stats.mtime,
            },
          };
        } catch (error) {
          return {
            dir,
            status: {
              exists: false,
              accessible: false,
              error: error.message,
            },
          };
        }
      });

      const dirCheckResults = await Promise.all(dirCheckPromises);

      // Populate directory results from parallel execution
      dirCheckResults.forEach(({ dir, status }) => {
        // eslint-disable-next-line security/detect-object-injection -- dir is from controlled criticalDirectories array, not user input
        fileHealthResults.criticalDirectoriesStatus[dir] = status;
      });

      // Calculate overall file system health score;
      const totalChecks = criticalFiles.length + criticalDirectories.length;
      const successfulChecks = Object.values(fileHealthResults.criticalFilesStatus)
        .filter(status => status.exists && status.accessible).length +
        Object.values(fileHealthResults.criticalDirectoriesStatus)
          .filter(status => status.exists && status.accessible).length;

      fileHealthResults.statistics = {
        healthScore: (successfulChecks / totalChecks) * 100,
        totalChecks,
        successfulChecks,
        checkDuration: performance.now() - fsHealthStart,
        timestamp: new Date().toISOString(),
      };

      this.logger.info('File system health check completed', { healthScore: fileHealthResults.statistics.healthScore,
        successfulChecks,
        totalChecks,
        duration: fileHealthResults.statistics.checkDuration,
      });

      return { fileSystemHealth: fileHealthResults };

    } catch (error) {
      this.logger.error('File system health check failed', { error: error.message,
        stack: error.stack,
        duration: performance.now() - fsHealthStart,
      });

      throw error;
    }
  }

  /**
   * Check TaskManager system health And functionality
   *
   * Validates TaskManager core operations including task creation,
   * task management, And data persistence.
   *
   * @private
   * @returns {Promise<Object>} TaskManager health results
   */
  async _checkTaskManagerHealth() {
    const tmHealthStart = performance.now();

    this.logger.info('Checking TaskManager system health');

    const taskManagerResults = {
      coreOperations: {},
      apiResponsiveness: {},
      dataConsistency: {},
      errorHandling: {},
      statistics: {},
    };

    try {
      // Test core TaskManager operations;
      const coreTestStart = performance.now();

      // Test TODO.json reading capability;
      const todoData = await this.taskManager.readTodo();
      taskManagerResults.coreOperations.todoReading = {
        success: true,
        taskCount: todoData.tasks ? todoData.tasks.length : 0,
        duration: performance.now() - coreTestStart,
        dataStructure: {
          hasProject: !!todoData.project,
          hasTasks: Array.isArray(todoData.tasks),
          hasFeatures: Array.isArray(todoData.features),
          hasAgents: typeof todoData.agents === 'object',
        },
      };

      // Test task filtering And querying;
      const filterTestStart = performance.now();
      const pendingTasks = todoData.tasks.filter(task => task.status === 'pending');
      const inProgressTasks = todoData.tasks.filter(task => task.status === 'in_progress');
      const completedTasks = todoData.tasks.filter(task => task.status === 'completed');

      taskManagerResults.coreOperations.taskFiltering = {
        success: true,
        duration: performance.now() - filterTestStart,
        taskCounts: {
          total: todoData.tasks.length,
          pending: pendingTasks.length,
          inProgress: inProgressTasks.length,
          completed: completedTasks.length,
        },
      };

      // Test TaskManager API responsiveness;
      const apiTestStart = performance.now();
      try {
        const statistics = await this.taskManager.getStatistics();
        taskManagerResults.apiResponsiveness.statisticsEndpoint = {
          success: true,
          duration: performance.now() - apiTestStart,
          responseData: statistics,
        };
      } catch (apiError) {
        taskManagerResults.apiResponsiveness.statisticsEndpoint = {
          success: false,
          duration: performance.now() - apiTestStart,
          error: apiError.message,
        };
      }

      // Test data consistency validation;
      const consistencyTestStart = performance.now();
      const consistencyIssues = [];

      // Check for duplicate task IDs;
      const taskIds = todoData.tasks.map(task => task.id);
      const duplicateIds = taskIds.filter((id, index) => taskIds.indexOf(id) !== index);
      if (duplicateIds.length > 0) {
        consistencyIssues.push(`Duplicate task IDs found: ${duplicateIds.join(', ')}`);
      }

      // Check for orphaned dependencies
      for (const task of todoData.tasks) {
        if (task.dependencies && task.dependencies.length > 0) {
          for (const depId of task.dependencies) {
            if (!taskIds.includes(depId)) {
              consistencyIssues.push(`Task ${task.id} has orphaned dependency: ${depId}`);
            }
          }
        }
      }

      taskManagerResults.dataConsistency = {
        issues: consistencyIssues,
        isConsistent: consistencyIssues.length === 0,
        checkDuration: performance.now() - consistencyTestStart,
        totalTasksValidated: todoData.tasks.length,
      };

      // Calculate overall TaskManager health score;
      const operationSuccessCount = Object.values(taskManagerResults.coreOperations)
        .filter(op => op.success).length;
      const totalOperations = Object.keys(taskManagerResults.coreOperations).length;
      const consistencyBonus = taskManagerResults.dataConsistency.isConsistent ? 20 : 0;

      taskManagerResults.statistics = {
        healthScore: ((operationSuccessCount / totalOperations) * 80) + consistencyBonus,
        totalOperations,
        successfulOperations: operationSuccessCount,
        consistencyIssues: consistencyIssues.length,
        totalDuration: performance.now() - tmHealthStart,
        timestamp: new Date().toISOString(),
      };

      this.logger.info('TaskManager health check completed', { healthScore: taskManagerResults.statistics.healthScore,
        operationSuccessCount,
        totalOperations,
        consistencyIssues: consistencyIssues.length,
        duration: taskManagerResults.statistics.totalDuration,
      });

      return { taskManagerHealth: taskManagerResults };

    } catch (error) {
      this.logger.error('TaskManager health check failed', { error: error.message,
        stack: error.stack,
        duration: performance.now() - tmHealthStart,
      });

      taskManagerResults.statistics = {
        healthScore: 0,
        error: error.message,
        duration: performance.now() - tmHealthStart,
        timestamp: new Date().toISOString(),
      };

      return { taskManagerHealth: taskManagerResults };
    }
  }

  /**
   * Check Agent system health And coordination
   *
   * Validates AgentManager functionality, agent registration,
   * And multi-agent coordination capabilities.
   *
   * @private
   * @returns {Promise<Object>} Agent system health results
   */
  async _checkAgentSystemHealth() {
    const agentHealthStart = performance.now();

    this.logger.info('Checking Agent system health');

    const agentResults = {
      agentRegistry: {},
      coordinationSystem: {},
      performanceMetrics: {},
      statistics: {},
    };

    try {
      // Test agent registration And management;
      const registryTestStart = performance.now();

      // Get current agent count;
      const activeAgents = await this.agentManager.getActiveAgents();
      const totalAgents = await this.agentManager.getAllAgents();

      agentResults.agentRegistry = {
        activeAgentCount: activeAgents.length,
        totalAgentCount: totalAgents.length,
        registryResponsive: true,
        queryDuration: performance.now() - registryTestStart,
        agentDistribution: this._analyzeAgentDistribution(activeAgents),
      };

      // Test agent coordination capabilities;
      const coordinationTestStart = performance.now();

      // Test agent heartbeat system
      try {
        const heartbeatTest = await this._testAgentHeartbeatSystem();
        agentResults.coordinationSystem.heartbeat = heartbeatTest;
      } catch (heartbeatError) {
        agentResults.coordinationSystem.heartbeat = {
          success: false,
          error: heartbeatError.message,
        };
      }

      agentResults.coordinationSystem.testDuration = performance.now() - coordinationTestStart;

      // Calculate agent system health score;
      const registryHealthy = agentResults.agentRegistry.registryResponsive ? 50 : 0;
      const coordinationHealthy = agentResults.coordinationSystem.heartbeat?.success ? 50 : 0;

      agentResults.statistics = {
        healthScore: registryHealthy + coordinationHealthy,
        activeAgents: activeAgents.length,
        totalAgents: totalAgents.length,
        totalDuration: performance.now() - agentHealthStart,
        timestamp: new Date().toISOString(),
      };

      this.logger.info('Agent system health check completed', { healthScore: agentResults.statistics.healthScore,
        activeAgents: activeAgents.length,
        totalAgents: totalAgents.length,
        duration: agentResults.statistics.totalDuration,
      });

      return { agentSystemHealth: agentResults };

    } catch (error) {
      this.logger.error('Agent system health check failed', { error: error.message,
        stack: error.stack,
        duration: performance.now() - agentHealthStart,
      });

      agentResults.statistics = {
        healthScore: 0,
        error: error.message,
        duration: performance.now() - agentHealthStart,
        timestamp: new Date().toISOString(),
      };

      return { agentSystemHealth: agentResults };
    }
  }

  /**
   * Analyze agent distribution across roles And specializations
   *
   * @private
   * @param {Array} agents - Active agents list
   * @returns {Object} Agent distribution analysis
   */
  _analyzeAgentDistribution(agents) {
    const distribution = {
      byRole: {},
      bySpecialization: {},
      byStatus: {},
      workloadDistribution: [],
    };

    for (const agent of agents) {
      // Count by role

      distribution.byRole[agent.role] = (distribution.byRole[agent.role] || 0) + 1;

      // Count by specialization
      if (agent.specialization && agent.specialization.length > 0) {
        for (const spec of agent.specialization) {
          // eslint-disable-next-line security/detect-object-injection -- spec is from controlled agent.specialization array, not user input
          distribution.bySpecialization[spec] = (distribution.bySpecialization[spec] || 0) + 1;
        }
      } else {
        distribution.bySpecialization['general'] = (distribution.bySpecialization['general'] || 0) + 1;
      }

      // Count by status

      distribution.byStatus[agent.status] = (distribution.byStatus[agent.status] || 0) + 1;

      // Track workload distribution
      distribution.workloadDistribution.push({
        agentId: agent.agentId,
        workload: agent.workload || 0,
        maxConcurrent: agent.maxConcurrentTasks || 5,
      });
    }

    return distribution;
  }

  /**
   * Test agent heartbeat system functionality
   *
   * @private
   * @returns {Promise<Object>} Heartbeat system test results
   */
  async _testAgentHeartbeatSystem() {
    const heartbeatTestStart = performance.now();

    this.logger.info('Testing agent heartbeat system');
    try {
      // Test heartbeat registration And renewal;
      const testAgentConfig = {
        role: 'health-test',
        specialization: ['system-health'],
        sessionId: `health-test-${Date.now()}`,
      };

      // Register test agent;
      const testAgent = await this.agentManager.registerAgent(testAgentConfig);

      // Test heartbeat renewal;
      const renewalResult = await this.agentManager.renewAgentHeartbeat(testAgent.agentId);

      // Clean up test agent
      await this.agentManager.deactivateAgent(testAgent.agentId);

      const heartbeatResults = {
        success: true,
        registrationWorking: !!testAgent.agentId,
        renewalWorking: renewalResult.success,
        cleanupWorking: true,
        duration: performance.now() - heartbeatTestStart,
        testAgentId: testAgent.agentId,
      };

      this.logger.info('Agent heartbeat system test completed', heartbeatResults);

      return heartbeatResults;

    } catch (error) {
      this.logger.error('Agent heartbeat system test failed', { error: error.message,
        stack: error.stack,
        duration: performance.now() - heartbeatTestStart,
      });

      return {
        success: false,
        error: error.message,
        duration: performance.now() - heartbeatTestStart,
      };
    }
  }

  /**
   * Check system resource health And utilization
   *
   * Monitors system resources, compares with baseline,
   * And identifies potential performance bottlenecks.
   *
   * @private
   * @returns {Promise<Object>} System resource health results
   */
  _checkSystemResourceHealth() {
    const resourceHealthStart = performance.now();

    this.logger.info('Checking system resource health');

    const resourceResults = {
      currentUsage: {},
      comparison: {},
      thresholds: {},
      recommendations: [],
      statistics: {},
    };

    try {
      // Collect current resource usage
      resourceResults.currentUsage = {
        memory: {
          total: OS.totalmem(),
          free: OS.freemem(),
          used: OS.totalmem() - OS.freemem(),
          usagePercent: ((OS.totalmem() - OS.freemem()) / OS.totalmem()) * 100,
          processHeapTotal: process.memoryUsage().heapTotal,
          processHeapUsed: process.memoryUsage().heapUsed,
          processExternal: process.memoryUsage().external,
        },
        cpu: {
          loadAverage: OS.loadavg(),
          cores: OS.cpus().length,
        },
        system: {
          uptime: OS.uptime(),
          processUptime: process.uptime(),
        },
        timestamp: new Date().toISOString(),
      };

      // Compare with baseline measurements
      if (this.resourceBaseline.memory) {
        resourceResults.comparison = {
          memoryChange: {
            usagePercentDelta: resourceResults.currentUsage.memory.usagePercent -
                               this.resourceBaseline.memory.usagePercent,
            heapUsedDelta: resourceResults.currentUsage.memory.processHeapUsed -
                          this.resourceBaseline.memory.heapUsed,
            freeMemoryDelta: resourceResults.currentUsage.memory.free -
                            this.resourceBaseline.memory.free,
          },
          cpuLoadChange: {
            loadAverage1mDelta: resourceResults.currentUsage.cpu.loadAverage[0] -
                               (this.resourceBaseline.cpu.loadAverage[0] || 0),
          },
        };
      }

      // Define resource health thresholds
      resourceResults.thresholds = {
        memory: {
          warning: 80, // 80% memory usage
          critical: 90, // 90% memory usage
        },
        cpu: {
          warning: resourceResults.currentUsage.cpu.cores * 0.7, // 70% of CPU cores
          critical: resourceResults.currentUsage.cpu.cores * 0.9,  // 90% of CPU cores
        },
        heap: {
          warning: 100 * 1024 * 1024, // 100MB heap usage
          critical: 250 * 1024 * 1024,  // 250MB heap usage
        },
      };

      // Generate health recommendations
      this._generateResourceRecommendations(resourceResults);

      // Calculate resource health score;
      let healthScore = 100;

      // Deduct points for high memory usage
      if (resourceResults.currentUsage.memory.usagePercent > resourceResults.thresholds.memory.critical) {
        healthScore -= 30;
      } else if (resourceResults.currentUsage.memory.usagePercent > resourceResults.thresholds.memory.warning) {
        healthScore -= 15;
      }

      // Deduct points for high CPU load;
      const avgLoad = resourceResults.currentUsage.cpu.loadAverage[0];
      if (avgLoad > resourceResults.thresholds.cpu.critical) {
        healthScore -= 25;
      } else if (avgLoad > resourceResults.thresholds.cpu.warning) {
        healthScore -= 10;
      }

      // Deduct points for high heap usage
      if (resourceResults.currentUsage.memory.processHeapUsed > resourceResults.thresholds.heap.critical) {
        healthScore -= 20;
      } else if (resourceResults.currentUsage.memory.processHeapUsed > resourceResults.thresholds.heap.warning) {
        healthScore -= 10;
      }

      resourceResults.statistics = {
        healthScore: Math.max(0, healthScore),
        checkDuration: performance.now() - resourceHealthStart,
        recommendationCount: resourceResults.recommendations.length,
        timestamp: new Date().toISOString(),
      };

      this.logger.info('System resource health check completed', { healthScore: resourceResults.statistics.healthScore,
        memoryUsagePercent: resourceResults.currentUsage.memory.usagePercent,
        cpuLoadAverage: resourceResults.currentUsage.cpu.loadAverage[0],
        recommendationCount: resourceResults.recommendations.length,
        duration: resourceResults.statistics.checkDuration,
      });

      return { systemResourceHealth: resourceResults };

    } catch (error) {
      this.logger.error('System resource health check failed', { error: error.message,
        stack: error.stack,
        duration: performance.now() - resourceHealthStart,
      });

      resourceResults.statistics = {
        healthScore: 0,
        error: error.message,
        duration: performance.now() - resourceHealthStart,
        timestamp: new Date().toISOString(),
      };

      return { systemResourceHealth: resourceResults };
    }
  }

  /**
   * Generate resource optimization recommendations
   *
   * @private
   * @param {Object} resourceResults - Resource health results
   */
  _generateResourceRecommendations(resourceResults) {
    const recommendations = [];

    // Memory usage recommendations
    if (resourceResults.currentUsage.memory.usagePercent > 80) {
      recommendations.push({
        type: 'memory',
        priority: resourceResults.currentUsage.memory.usagePercent > 90 ? 'high' : 'medium',
        message: `High memory usage detected (${resourceResults.currentUsage.memory.usagePercent.toFixed(1)}%). Consider optimizing memory-intensive operations or increasing system memory.`,
        technicalDetails: {
          currentUsage: resourceResults.currentUsage.memory.usagePercent,
          threshold: 80,
          totalMemory: resourceResults.currentUsage.memory.total,
          usedMemory: resourceResults.currentUsage.memory.used,
        },
      });
    }

    // Process heap recommendations
    if (resourceResults.currentUsage.memory.processHeapUsed > 100 * 1024 * 1024) {
      recommendations.push({
        type: 'heap',
        priority: resourceResults.currentUsage.memory.processHeapUsed > 250 * 1024 * 1024 ? 'high' : 'medium',
        message: `High process heap usage detected (${(resourceResults.currentUsage.memory.processHeapUsed / 1024 / 1024).toFixed(1)}MB). Consider implementing garbage collection optimizations.`,
        technicalDetails: {
          heapUsed: resourceResults.currentUsage.memory.processHeapUsed,
          heapTotal: resourceResults.currentUsage.memory.processHeapTotal,
          warningThreshold: 100 * 1024 * 1024,
          criticalThreshold: 250 * 1024 * 1024,
        },
      });
    }

    // CPU load recommendations;
    const avgLoad = resourceResults.currentUsage.cpu.loadAverage[0];
    const coreThreshold = resourceResults.currentUsage.cpu.cores * 0.7;

    if (avgLoad > coreThreshold) {
      recommendations.push({
        type: 'cpu',
        priority: avgLoad > resourceResults.currentUsage.cpu.cores * 0.9 ? 'high' : 'medium',
        message: `High CPU load detected (${avgLoad.toFixed(2)} avg load on ${resourceResults.currentUsage.cpu.cores} cores). Consider optimizing CPU-intensive operations.`,
        technicalDetails: {
          loadAverage1m: avgLoad,
          loadAverage5m: resourceResults.currentUsage.cpu.loadAverage[1],
          loadAverage15m: resourceResults.currentUsage.cpu.loadAverage[2],
          cores: resourceResults.currentUsage.cpu.cores,
          threshold: coreThreshold,
        },
      });
    }

    resourceResults.recommendations = recommendations;
  }

  /**
   * Check system performance metrics And response times
   *
   * Measures And analyzes system performance characteristics,
   * identifying bottlenecks And optimization opportunities.
   *
   * @private
   * @returns {Promise<Object>} Performance metrics results
   */
  async _checkPerformanceMetrics() {
    const performanceStart = performance.now();

    this.logger.info('Checking system performance metrics');

    const performanceResults = {
      responseTimeTests: {},
      throughputTests: {},
      concurrencyTests: {},
      bottleneckAnalysis: {},
      statistics: {},
    };

    try {
      // Test response times for common operations
      await this._measureResponseTimes(performanceResults);

      // Test system throughput capabilities
      await this._measureThroughput(performanceResults);

      // Analyze potential bottlenecks
      this._analyzeBottlenecks(performanceResults);

      // Calculate overall performance score;
      const performanceScore = this._calculatePerformanceScore(performanceResults);

      performanceResults.statistics = {
        performanceScore,
        totalTestDuration: performance.now() - performanceStart,
        testsCompleted: Object.keys(performanceResults.responseTimeTests).length +
                       Object.keys(performanceResults.throughputTests).length,
        timestamp: new Date().toISOString(),
      };

      this.logger.info('Performance metrics check completed', { performanceScore: performanceResults.statistics.performanceScore,
        testsCompleted: performanceResults.statistics.testsCompleted,
        duration: performanceResults.statistics.totalTestDuration,
      });

      return { performanceMetrics: performanceResults };

    } catch (error) {
      this.logger.error('Performance metrics check failed', { error: error.message,
        stack: error.stack,
        duration: performance.now() - performanceStart,
      });

      performanceResults.statistics = {
        performanceScore: 0,
        error: error.message,
        duration: performance.now() - performanceStart,
        timestamp: new Date().toISOString(),
      };

      return { performanceMetrics: performanceResults };
    }
  }

  /**
   * Measure response times for critical operations
   *
   * @private
   * @param {Object} performanceResults - Performance results object to populate
   * @returns {Promise<void>}
   */
  async _measureResponseTimes(performanceResults) {
    const responseTests = [{ name: 'todoFileRead',
      operation: () => this.taskManager.readTodo(),
    }, { name: 'taskFiltering',
      operation: async () => {
        const todoData = await this.taskManager.readTodo();
        return todoData.tasks.filter(task => task.status === 'pending');
      },
    }, { name: 'statisticsGeneration',
      operation: () => this.taskManager.getStatistics(),
    },
    ];

    for (const test of responseTests) {
      const testStart = performance.now();
      try {
        // eslint-disable-next-line no-await-in-loop -- Sequential test execution required for accurate performance measurement
        await test.operation();

        performanceResults.responseTimeTests[test.name] = {
          success: true,
          duration: performance.now() - testStart,
          timestamp: new Date().toISOString(),
        };
      } catch (error) {
        performanceResults.responseTimeTests[test.name] = {
          success: false,
          duration: performance.now() - testStart,
          error: error.message,
          timestamp: new Date().toISOString(),
        };
      }
    }
  }

  /**
   * Measure system throughput for batch operations
   *
   * @private
   * @param {Object} performanceResults - Performance results object to populate
   * @returns {Promise<void>}
   */
  async _measureThroughput(performanceResults) {
    const throughputStart = performance.now();
    try {
      // Test batch file operations throughput;
      const testIterations = 50;
      const batchStart = performance.now();

      for (let i = 0; i < testIterations; i++) {
        // eslint-disable-next-line no-await-in-loop -- Sequential iterations required for throughput measurement
        await this.taskManager.readTodo();
      }

      const batchDuration = performance.now() - batchStart;

      performanceResults.throughputTests.batchFileOperations = {
        success: true,
        iterations: testIterations,
        totalDuration: batchDuration,
        averageOperationTime: batchDuration / testIterations,
        operationsPerSecond: (testIterations / batchDuration) * 1000,
        timestamp: new Date().toISOString(),
      };

    } catch (error) {
      performanceResults.throughputTests.batchFileOperations = {
        success: false,
        error: error.message,
        duration: performance.now() - throughputStart,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Analyze potential system bottlenecks
   *
   * @private
   * @param {Object} performanceResults - Performance results object to populate
   */
  _analyzeBottlenecks(performanceResults) {
    const bottlenecks = [];

    // Analyze response time patterns;
    const responseTimes = Object.values(performanceResults.responseTimeTests)
      .filter(test => test.success)
      .map(test => test.duration);

    if (responseTimes.length > 0) {
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      const maxResponseTime = Math.max(...responseTimes);

      if (avgResponseTime > 100) { // 100ms threshold
        bottlenecks.push({
          type: 'response-time',
          severity: avgResponseTime > 500 ? 'high' : 'medium',
          description: `Average response time is ${avgResponseTime.toFixed(2)}ms, which exceeds recommended threshold of 100ms`,
          recommendation: 'Consider optimizing file I/O operations And implementing caching',
          metrics: { avgResponseTime, maxResponseTime, threshold: 100 },
        });
      }
    }

    // Analyze throughput patterns;
    const throughputTest = performanceResults.throughputTests.batchFileOperations;
    if (throughputTest && throughputTest.success) {
      if (throughputTest.operationsPerSecond < 100) { // 100 ops/sec threshold
        bottlenecks.push({
          type: 'throughput',
          severity: throughputTest.operationsPerSecond < 50 ? 'high' : 'medium',
          description: `Batch operation throughput is ${throughputTest.operationsPerSecond.toFixed(2)} ops/sec, below recommended 100 ops/sec`,
          recommendation: 'Consider implementing batch processing optimization And async I/O improvements',
          metrics: {
            operationsPerSecond: throughputTest.operationsPerSecond,
            threshold: 100,
            averageOperationTime: throughputTest.averageOperationTime,
          },
        });
      }
    }

    performanceResults.bottleneckAnalysis = {
      bottlenecks,
      bottleneckCount: bottlenecks.length,
      analysisTimestamp: new Date().toISOString(),
    };
  }

  /**
   * Calculate overall performance score based on test results
   *
   * @private
   * @param {Object} performanceResults - Performance results object
   * @returns {number} Performance score (0-100)
   */
  _calculatePerformanceScore(performanceResults) {
    let score = 100;

    // Deduct points for failed response time tests;
    const responseTests = Object.values(performanceResults.responseTimeTests);
    const failedResponseTests = responseTests.filter(test => !test.success).length;
    score -= (failedResponseTests * 20);

    // Deduct points for slow response times;
    const successfulResponseTests = responseTests.filter(test => test.success);
    const slowResponseTests = successfulResponseTests.filter(test => test.duration > 100).length;
    score -= (slowResponseTests * 10);

    // Deduct points for throughput issues;
    const throughputTest = performanceResults.throughputTests.batchFileOperations;
    if (throughputTest && throughputTest.success) {
      if (throughputTest.operationsPerSecond < 50) {
        score -= 20;
      } else if (throughputTest.operationsPerSecond < 100) {
        score -= 10;
      }
    } else if (throughputTest && !throughputTest.success) {
      score -= 25;
    }

    // Deduct points for identified bottlenecks;
    const bottleneckCount = performanceResults.bottleneckAnalysis?.bottleneckCount || 0;
    score -= (bottleneckCount * 5);

    return Math.max(0, score);
  }

  /**
   * Check data integrity And consistency across the system
   *
   * Validates data consistency, file integrity, And system coherence.
   *
   * @private
   * @returns {Promise<Object>} Data integrity health results
   */
  async _checkDataIntegrityHealth() {
    const integrityStart = performance.now();

    this.logger.info('Checking data integrity And consistency');

    const integrityResults = {
      fileIntegrity: {},
      dataConsistency: {},
      backupValidation: {},
      validationErrors: [],
      statistics: {},
    };

    try {
      // Validate JSON file integrity
      await this._validateJsonFileIntegrity(integrityResults);

      // Check data consistency across system
      await this._validateDataConsistency(integrityResults);

      // Validate backup files if they exist
      await this._validateBackupFiles(integrityResults);

      // Calculate data integrity score;
      const integrityScore = this._calculateIntegrityScore(integrityResults);

      integrityResults.statistics = {
        integrityScore,
        validationErrors: integrityResults.validationErrors.length,
        checkDuration: performance.now() - integrityStart,
        timestamp: new Date().toISOString(),
      };

      this.logger.info('Data integrity check completed', { integrityScore: integrityResults.statistics.integrityScore,
        validationErrors: integrityResults.statistics.validationErrors,
        duration: integrityResults.statistics.checkDuration,
      });

      return { dataIntegrityHealth: integrityResults };

    } catch (error) {
      this.logger.error('Data integrity check failed', { error: error.message,
        stack: error.stack,
        duration: performance.now() - integrityStart,
      });

      integrityResults.statistics = {
        integrityScore: 0,
        error: error.message,
        duration: performance.now() - integrityStart,
        timestamp: new Date().toISOString(),
      };

      return { dataIntegrityHealth: integrityResults };
    }
  }

  /**
   * Validate JSON file integrity
   *
   * @private
   * @param {Object} integrityResults - Integrity results object to populate
   * @returns {Promise<void>}
   */
  async _validateJsonFileIntegrity(integrityResults) {
    const jsonFiles = ['TODO.json', 'package.json'];

    // Process all JSON files in parallel for better performance;
    const fileValidationPromises = jsonFiles.map(async (fileName) => {
      const filePath = path.join(this.projectRoot, fileName);
      try {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check;
        const fileContent = await FS.readFile(filePath, 'utf8');
        const parsedData = JSON.parse(fileContent);
        return {
          fileName,
          result: {
            exists: true,
            validJson: true,
            parseTime: performance.now(),
            dataStructure: this._analyzeJsonStructure(parsedData),
            fileSize: fileContent.length,
          },
        };

      } catch (_error) {
        return {
          fileName,
          result: null,
          error: _error,
        };
      }
    });

    const validationResults = await Promise.all(fileValidationPromises);

    // Process results And update integrityResults
    for (const { fileName, result, error } of validationResults) {
      if (result) {
        // eslint-disable-next-line security/detect-object-injection -- fileName is from controlled jsonFiles array, not user input
        integrityResults.fileIntegrity[fileName] = result;
      } else {
        // eslint-disable-next-line security/detect-object-injection -- fileName is from controlled jsonFiles array, not user input
        integrityResults.fileIntegrity[fileName] = {
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check,,
          exists: FS_SYNC.existsSync(path.join(this.projectRoot, fileName)),
          validJson: false,
          error: error.message,
        };

        integrityResults.validationErrors.push({
          type: 'file-integrity',
          file: fileName,
          error: error.message,
          timestamp: new Date().toISOString(),
        });
      }
    }
  }

  /**
   * Analyze JSON data structure for validation
   *
   * @private
   * @param {Object} data - JSON data to analyze
   * @returns {Object} Structure analysis
   */
  _analyzeJsonStructure(data) {
    const analysis = {
      dataType: typeof data,
      isObject: typeof data === 'object' && data !== null,
      isArray: Array.isArray(data),
      keyCount: 0,
      nestedLevels: 0,
    };

    if (typeof data === 'object' && data !== null) {
      analysis.keyCount = Object.keys(data).length;
      analysis.nestedLevels = this._calculateNestingDepth(data);
    }

    return analysis;
  }

  /**
   * Calculate nesting depth of an object
   *
   * @private
   * @param {Object} obj - Object to analyze
   * @param {number} currentDepth - Current nesting depth
   * @returns {number} Maximum nesting depth
   */
  _calculateNestingDepth(obj, currentDepth = 0) {
    if (typeof obj !== 'object' || obj === null) {
      return currentDepth;
    }

    let maxDepth = currentDepth;

    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        // eslint-disable-next-line security/detect-object-injection -- key is from Object.prototype.hasOwnProperty iteration, controlled access;
        const depth = this._calculateNestingDepth(obj[key], currentDepth + 1);
        maxDepth = Math.max(maxDepth, depth);
      }
    }

    return maxDepth;
  }

  /**
   * Validate data consistency across the system
   *
   * @private
   * @param {Object} integrityResults - Integrity results object to populate
   * @returns {Promise<void>}
   */
  async _validateDataConsistency(integrityResults) {
    try {
      const todoData = await this.taskManager.readTodo();
      const consistencyIssues = [];

      // Validate task data consistency
      if (todoData.tasks && Array.isArray(todoData.tasks)) {
        // Check for required fields
        for (const task of todoData.tasks) {
          if (!task.id) {
            consistencyIssues.push(`Task missing ID: ${JSON.stringify(task)}`);
          }
          if (!task.title) {
            consistencyIssues.push(`Task ${task.id || 'unknown'} missing title`);
          }
          if (!task.status) {
            consistencyIssues.push(`Task ${task.id || 'unknown'} missing status`);
          }
        }

        // Check for orphaned references;
        const taskIds = todoData.tasks.map(task => task.id);
        for (const task of todoData.tasks) {
          if (task.dependencies && Array.isArray(task.dependencies)) {
            for (const depId of task.dependencies) {
              if (!taskIds.includes(depId)) {
                consistencyIssues.push(`Task ${task.id} has orphaned dependency: ${depId}`);
              }
            }
          }
        }
      }

      integrityResults.dataConsistency = {
        totalTasks: todoData.tasks ? todoData.tasks.length : 0,
        consistencyIssues: consistencyIssues,
        isConsistent: consistencyIssues.length === 0,
        validationTimestamp: new Date().toISOString(),
      };

      // Add consistency issues to validation errors
      for (const issue of consistencyIssues) {
        integrityResults.validationErrors.push({
          type: 'data-consistency',
          description: issue,
          timestamp: new Date().toISOString(),
        });
      }

    } catch (error) {
      integrityResults.dataConsistency = {
        error: error.message,
        isConsistent: false,
      };

      integrityResults.validationErrors.push({
        type: 'data-consistency',
        error: error.message,
        timestamp: new Date().toISOString(),
      });
    }
  }

  /**
   * Validate backup files if they exist
   *
   * @private
   * @param {Object} integrityResults - Integrity results object to populate
   * @returns {Promise<void>}
   */
  async _validateBackupFiles(integrityResults) {
    try {

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check;
      const backupFiles = await FS.readdir(this.projectRoot)
        .then(files => files.filter(file =>
          file.includes('.backup') ||
          file.includes('.bak') ||
          file.startsWith('TODO.json.') && file !== 'TODO.json',
        ))
        .catch(() => []);

      integrityResults.backupValidation = {
        backupFilesFound: backupFiles.length,
        backupFiles: backupFiles,
        validBackups: 0,
        invalidBackups: 0,
      };

      // Filter JSON backup files And validate them in parallel;
      const jsonBackupFiles = backupFiles.filter(file =>
        file.includes('TODO.json') || file.includes('.json'),
      );

      const backupValidationPromises = jsonBackupFiles.map(async (backupFile) => {
        const backupPath = path.join(this.projectRoot, backupFile);
        try {
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check;
          const backupContent = await FS.readFile(backupPath, 'utf8');
          JSON.parse(backupContent);
          return { backupFile, isValid: true, error: null };
        } catch (_error) {
          return { backupFile, isValid: false, error: _error };
        }
      });

      const backupResults = await Promise.all(backupValidationPromises);

      // Process validation results
      for (const { backupFile, isValid, error } of backupResults) {
        if (isValid) {
          integrityResults.backupValidation.validBackups++;
        } else {
          integrityResults.backupValidation.invalidBackups++;
          integrityResults.validationErrors.push({
            type: 'backup-validation',
            file: backupFile,
            error: error.message,
            timestamp: new Date().toISOString(),
          });
        }
      }

    } catch (error) {
      integrityResults.backupValidation = {
        error: error.message,
        backupFilesFound: 0,
      };
    }
  }

  /**
   * Calculate overall data integrity score
   *
   * @private
   * @param {Object} integrityResults - Integrity results object
   * @returns {number} Integrity score (0-100)
   */
  _calculateIntegrityScore(integrityResults) {
    let score = 100;

    // Deduct points for file integrity issues;
    const fileIntegrityTests = Object.values(integrityResults.fileIntegrity);
    const failedFileTests = fileIntegrityTests.filter(test => !test.validJson).length;
    score -= (failedFileTests * 30);

    // Deduct points for data consistency issues
    if (integrityResults.dataConsistency && !integrityResults.dataConsistency.isConsistent) {
      const issueCount = integrityResults.dataConsistency.consistencyIssues?.length || 1;
      score -= Math.min(40, issueCount * 10);
    }

    // Deduct points for backup validation failures
    if (integrityResults.backupValidation && integrityResults.backupValidation.invalidBackups > 0) {
      score -= (integrityResults.backupValidation.invalidBackups * 5);
    }

    // Total validation errors impact;
    const totalErrors = integrityResults.validationErrors.length;
    score -= Math.min(20, totalErrors * 2);

    return Math.max(0, score);
  }

  /**
   * Aggregate health check results from all categories
   *
   * @private
   * @param {Array} healthCheckResults - Array of PromiseSettledResult objects
   * @returns {Object} Aggregated health results
   */
  _aggregateHealthResults(healthCheckResults) {
    const aggregated = {};

    for (const result of healthCheckResults) {
      if (result.status === 'fulfilled' && result.value) {
        Object.assign(aggregated, result.value);
      } else if (result.status === 'rejected') {
        // Handle failed health checks;
        const errorCategory = `healthCheck_${Object.keys(aggregated).length}`;
        // eslint-disable-next-line security/detect-object-injection -- errorCategory is controlled string, not user input
        aggregated[errorCategory] = {
          error: result.reason?.message || 'Unknown health check error',
          status: 'failed',
          timestamp: new Date().toISOString(),
        };
      }
    }

    return aggregated;
  }

  /**
   * Calculate overall system health score
   *
   * @private
   * @param {Object} aggregatedResults - Aggregated health check results
   * @returns {number} Overall health score (0-100)
   */
  _calculateOverallHealthScore(aggregatedResults) {
    const healthScores = [];

    // Extract individual health scores
    Object.values(aggregatedResults).forEach(categoryResult => {
      if (categoryResult.statistics && typeof categoryResult.statistics.healthScore === 'number') {
        healthScores.push(categoryResult.statistics.healthScore);
      } else if (categoryResult.error) {
        healthScores.push(0); // Failed categories get 0 score
      }
    });

    if (healthScores.length === 0) {
      return 0; // No valid health checks completed
    }

    // Calculate weighted average (all categories have equal weight)
    const totalScore = healthScores.reduce((sum, score) => sum + score, 0);
    const averageScore = totalScore / healthScores.length;

    return Math.round(averageScore);
  }

  /**
   * Generate comprehensive health report
   *
   * @private
   * @param {Object} aggregatedResults - Aggregated health check results
   * @param {number} overallHealthScore - Overall system health score
   * @param {number} totalDuration - Total health check duration
   * @returns {Promise<Object>} Comprehensive health report
   */
  _generateHealthReport(aggregatedResults, overallHealthScore, totalDuration) {
    const report = {
      summary: {
        overallHealthScore,
        healthStatus: this._determineHealthStatus(overallHealthScore),
        totalCheckDuration: totalDuration,
        timestamp: new Date().toISOString(),
        systemInfo: {
          projectRoot: this.projectRoot,
          nodeVersion: process.version,
          platform: process.platform,
          arch: process.arch,
          processId: process.pid,
        },
      },
      categories: {},
      recommendations: [],
      alerts: [],
      metrics: {
        performanceSummary: {},
        resourceUsage: {},
        systemLoad: {},
      },
      healthTrends: {
        // Placeholder for trend analysis if historical data exists
        baselineComparison: this.resourceBaseline ? { memoryTrend: 'stable', // Would be calculated from historical data
          performanceTrend: 'stable',
          lastBaselineUpdate: this.resourceBaseline.timestamp,
        } : null,
      },
    };

    // Populate category results
    for (const [categoryName, categoryResult] of Object.entries(aggregatedResults)) {
      // eslint-disable-next-line security/detect-object-injection -- categoryName is from Object.entries iteration, controlled access
      report.categories[categoryName] = {
        healthScore: categoryResult.statistics?.healthScore || 0,
        status: categoryResult.error ? 'failed' : 'completed',
        duration: categoryResult.statistics?.checkDuration || 0,
        summary: this._generateCategorySummary(categoryName, categoryResult),
        details: categoryResult,
      };

      // Extract recommendations from category results
      if (categoryResult.recommendations) {
        report.recommendations.push(...categoryResult.recommendations);
      }

      // Generate alerts for critical issues
      if (categoryResult.statistics?.healthScore < 50) {
        report.alerts.push({
          type: 'health-warning',
          category: categoryName,
          message: `${categoryName} health score is critically low (${categoryResult.statistics.healthScore})`,
          priority: 'high',
          timestamp: new Date().toISOString(),
        });
      }
    }

    // Generate system-wide recommendations
    this._generateSystemRecommendations(report, aggregatedResults);

    // Populate performance metrics summary
    if (aggregatedResults.performanceMetrics) {
      report.metrics.performanceSummary = {
        averageResponseTime: this._calculateAverageResponseTime(aggregatedResults.performanceMetrics),
        throughput: aggregatedResults.performanceMetrics.throughputTests?.batchFileOperations?.operationsPerSecond || 0,
        bottleneckCount: aggregatedResults.performanceMetrics.bottleneckAnalysis?.bottleneckCount || 0,
      };
    }

    // Populate resource usage summary
    if (aggregatedResults.systemResourceHealth) {
      report.metrics.resourceUsage = {
        memoryUsagePercent: aggregatedResults.systemResourceHealth.currentUsage?.memory?.usagePercent || 0,
        cpuLoadAverage: aggregatedResults.systemResourceHealth.currentUsage?.cpu?.loadAverage?.[0] || 0,
        processHeapUsage: aggregatedResults.systemResourceHealth.currentUsage?.memory?.processHeapUsed || 0,
      };
    }

    this.logger.info('Comprehensive health report generated', {
      overallHealthScore,
      categoriesEvaluated: Object.keys(report.categories).length,
      recommendationsGenerated: report.recommendations.length,
      alertsGenerated: report.alerts.length,
      reportGenerationTime: new Date().toISOString(),
    });

    return report;
  }

  /**
   * Determine health status based on score
   *
   * @private
   * @param {number} score - Health score (0-100)
   * @returns {string} Health status description
   */
  _determineHealthStatus(score) {
    if (score >= 90) {return 'excellent';}
    if (score >= 75) {return 'good';}
    if (score >= 50) {return 'fair';}
    if (score >= 25) {return 'poor';}
    return 'critical';
  }

  /**
   * Generate category summary
   *
   * @private
   * @param {string} categoryName - Category name
   * @param {Object} categoryResult - Category results
   * @returns {string} Category summary
   */
  _generateCategorySummary(categoryName, categoryResult) {
    const score = categoryResult.statistics?.healthScore || 0;
    const duration = categoryResult.statistics?.checkDuration || 0;

    return `${categoryName} completed with ${score}% health score in ${duration.toFixed(2)}ms`;
  }

  /**
   * Calculate average response time from performance metrics
   *
   * @private
   * @param {Object} performanceMetrics - Performance metrics data
   * @returns {number} Average response time in milliseconds
   */
  _calculateAverageResponseTime(performanceMetrics) {
    const responseTests = performanceMetrics.responseTimeTests || {};
    const responseTimes = Object.values(responseTests)
      .filter(test => test.success && typeof test.duration === 'number')
      .map(test => test.duration);

    if (responseTimes.length === 0) {return 0;}

    return responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length;
  }

  /**
   * Generate system-wide recommendations
   *
   * @private
   * @param {Object} report - Health report object
   * @param {Object} aggregatedResults - Aggregated results
   */
  _generateSystemRecommendations(report, aggregatedResults) {
    // System-wide performance recommendations
    if (report.summary.overallHealthScore < 75) {
      report.recommendations.push({
        type: 'system-optimization',
        priority: 'high',
        message: 'Overall system health is below optimal levels. Consider implementing performance optimization strategies.',
        actions: [
          'Review And optimize file I/O operations',
          'Implement caching mechanisms for frequently accessed data',
          'Monitor And optimize memory usage patterns',
          'Consider upgrading system resources if consistently under high load',
        ],
      });
    }

    // File system optimization recommendations
    if (aggregatedResults.fileSystemHealth?.statistics?.healthScore < 90) {
      report.recommendations.push({
        type: 'file-system',
        priority: 'medium',
        message: 'File system health could be improved for better reliability.',
        actions: [
          'Verify all critical project files are present And accessible',
          'Implement automated backup strategies',
          'Regular file system integrity checks',
          'Optimize file permission settings',
        ],
      });
    }

    // TaskManager optimization recommendations
    if (aggregatedResults.taskManagerHealth?.statistics?.healthScore < 80) {
      report.recommendations.push({
        type: 'task-management',
        priority: 'high',
        message: 'TaskManager system requires optimization for better performance.',
        actions: [
          'Optimize task querying And filtering operations',
          'Implement task data validation improvements',
          'Consider task archival strategies for large datasets',
          'Review And optimize task dependency resolution',
        ],
      });
    }
  }

  /**
   * Save health report to file
   *
   * @param {Object} healthReport - Health report to save
   * @param {string} [filename] - Optional filename (auto-generated if not provided)
   * @returns {Promise<string>} Path to saved report file
   */
  async saveHealthReport(healthReport, filename = null) {
    try {
      const reportsDir = path.join(this.projectRoot, 'development', 'reports');

      // Ensure reports directory exists,
      try {

        // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check
        await FS.mkdir(reportsDir, { recursive: true });
      } catch {
        // Directory might already exist
      }

      const reportFilename = filename || `system-health-report-${Date.now()}.json`;
      const reportPath = path.join(reportsDir, reportFilename);


      // eslint-disable-next-line security/detect-non-literal-fs-filename -- System monitoring path validated through health check
      await FS.writeFile(reportPath, JSON.stringify(healthReport, null, 2), 'utf8');

      this.logger.info('Health report saved successfully', {
        reportPath,
        reportSize: JSON.stringify(healthReport).length,
        timestamp: new Date().toISOString(),
      });

      return reportPath;

    } catch (error) {
      this.logger.error('Failed to save health report', { error: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
      });

      throw error;
    }
  }

  /**
   * Run continuous health monitoring
   *
   * Starts background monitoring with periodic health checks
   * And alert notifications for system health changes.
   *
   * @param {Object} [options] - Monitoring options
   * @param {number} [options.interval=300000] - Monitoring interval in milliseconds (default: 5 minutes)
   * @param {number} [options.alertThreshold=50] - Health score threshold for alerts
   * @returns {Object} Monitoring control object
   */
  startContinuousMonitoring(options = {}) {
    const config = {
      interval: options.interval || 300000, // 5 minutes default
      alertThreshold: options.alertThreshold || 50,
      maxHistoryEntries: options.maxHistoryEntries || 100,
    };

    const monitoringState = {
      active: true,
      intervalId: null,
      healthHistory: [],
      alertCount: 0,
      lastHealthScore: null,
      startTime: Date.now(),
    };

    this.logger.info('Starting continuous health monitoring', { interval: config.interval,
      alertThreshold: config.alertThreshold,
      timestamp: new Date().toISOString(),
    });

    // Perform initial health check
    this.performComprehensiveHealthCheck()
      .then(initialReport => {
        monitoringState.lastHealthScore = initialReport.summary.overallHealthScore;
        monitoringState.healthHistory.push({
          timestamp: Date.now(),
          healthScore: initialReport.summary.overallHealthScore,
          categories: Object.keys(initialReport.categories).length,
        });

        this.emit('monitoringStarted', { initialHealthScore: initialReport.summary.overallHealthScore,
          config,
        });
      })
      .catch(error => {
        this.logger.error('Initial health check failed during monitoring startup', { error: error.message,
          timestamp: new Date().toISOString(),
        });
      });

    // Set up periodic monitoring
    monitoringState.intervalId = setInterval(async () => {
      if (!monitoringState.active) {return;}

      try {
        const healthReport = await this.performComprehensiveHealthCheck();
        const currentScore = healthReport.summary.overallHealthScore;

        // Update monitoring state
        monitoringState.healthHistory.push({
          timestamp: Date.now(),
          healthScore: currentScore,
          categories: Object.keys(healthReport.categories).length,
        });

        // Trim history if it gets too large
        if (monitoringState.healthHistory.length > config.maxHistoryEntries) {
          monitoringState.healthHistory = monitoringState.healthHistory.slice(-config.maxHistoryEntries);
        }

        // Check for alerts
        if (currentScore < config.alertThreshold) {
          monitoringState.alertCount++;
          this.emit('healthAlert', { healthScore: currentScore,
            threshold: config.alertThreshold,
            alertCount: monitoringState.alertCount,
            report: healthReport,
          });
        }

        // Check for significant health changes
        if (monitoringState.lastHealthScore !== null) {
          const scoreDelta = currentScore - monitoringState.lastHealthScore;
          if (Math.abs(scoreDelta) > 20) {
            this.emit('healthChange', { previousScore: monitoringState.lastHealthScore,
              currentScore,
              scoreDelta,
              report: healthReport,
            });
          }
        }

        monitoringState.lastHealthScore = currentScore;

        this.emit('periodicHealthCheck', { healthScore: currentScore,
          timestamp: Date.now(),
          report: healthReport,
        });

      } catch (error) {
        this.logger.error('Periodic health check failed', { error: error.message,
          stack: error.stack,
          timestamp: new Date().toISOString(),
        });

        this.emit('monitoringError', { error: error.message,
          timestamp: Date.now(),
        });
      }
    }, config.interval);

    // Return monitoring control object
    return {
      stop: () => {
        monitoringState.active = false;
        if (monitoringState.intervalId) {
          clearInterval(monitoringState.intervalId);
          monitoringState.intervalId = null;
        }

        this.logger.info('Continuous health monitoring stopped', { duration: Date.now() - monitoringState.startTime,
          totalChecks: monitoringState.healthHistory.length,
          alertsGenerated: monitoringState.alertCount,
          timestamp: new Date().toISOString(),
        });

        this.emit('monitoringStopped', { duration: Date.now() - monitoringState.startTime,
          totalChecks: monitoringState.healthHistory.length,
          alertsGenerated: monitoringState.alertCount,
        });
      },
      getStatus: () => ({
        active: monitoringState.active,
        uptime: Date.now() - monitoringState.startTime,
        checksPerformed: monitoringState.healthHistory.length,
        alertsGenerated: monitoringState.alertCount,
        lastHealthScore: monitoringState.lastHealthScore,
        config,
      }),
      getHealthHistory: () => [...monitoringState.healthHistory],
    };
  }

  /**
   * Generate health monitoring dashboard data
   *
   * @returns {Object} Dashboard data for health monitoring visualization
   */
  generateDashboardData() {
    const dashboardData = {
      systemOverview: {
        projectRoot: this.projectRoot,
        nodeVersion: process.version,
        platform: process.platform,
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
      },
      currentMetrics: {
        memory: {
          total: OS.totalmem(),
          free: OS.freemem(),
          usagePercent: ((OS.totalmem() - OS.freemem()) / OS.totalmem()) * 100,
          processHeap: process.memoryUsage().heapUsed,
        },
        cpu: {
          cores: OS.cpus().length,
          loadAverage: OS.loadavg(),
        },
        system: {
          hostname: OS.hostname(),
          uptime: OS.uptime(),
        },
      },
      healthIndicators: {
        // These would be populated from recent health checks,,
        fileSystemHealth: 'unknown',
        taskManagerHealth: 'unknown',
        agentSystemHealth: 'unknown',
        performanceHealth: 'unknown',
        dataIntegrityHealth: 'unknown',
      },
      quickActions: [{ name: 'Run Full Health Check',
        description: 'Perform comprehensive system health validation',
        command: 'performComprehensiveHealthCheck',
      }, { name: 'Start Monitoring',
        description: 'Begin continuous health monitoring',
        command: 'startContinuousMonitoring',
      }, { name: 'Generate Report',
        description: 'Create detailed health report',
        command: 'generateHealthReport',
      },
      ],
    };

    this.logger.info('Dashboard data generated', { timestamp: new Date().toISOString(),
      memoryUsage: dashboardData.currentMetrics.memory.usagePercent,
      systemUptime: dashboardData.currentMetrics.system.uptime,
    });

    return dashboardData;
  }

  /**
   * Cleanup And shutdown health monitor
   *
   * Performs cleanup of resources And saves final health state.
   */
  async shutdown() {
    try {
      this.logger.info('SystemHealthMonitor shutting down', { timestamp: new Date().toISOString(),
      });

      // Remove all event listeners
      this.removeAllListeners();

      // Cleanup TaskManager And AgentManager if initialized
      if (this.taskManager && typeof this.taskManager.cleanup === 'function') {
        await this.taskManager.cleanup();
      }

      if (this.agentManager && typeof this.agentManager.cleanup === 'function') {
        await this.agentManager.cleanup();
      }

      this.logger.info('SystemHealthMonitor shutdown completed', { timestamp: new Date().toISOString(),
      });

    } catch (error) {
      this.logger.error('Error during SystemHealthMonitor shutdown', { error: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
      });

      throw error;
    }
  }
}

module.exports = SystemHealthMonitor;
