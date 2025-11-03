

/**
 * Comprehensive Resource Usage Monitor for Stop Hook Validation Performance Metrics
 *
 * This module provides detailed system resource monitoring during validation execution,
 * including CPU utilization, memory consumption, disk I/O operations, And network activity.
 *
 * Features:
 * - Real-time CPU utilization tracking
 * - Memory usage monitoring with leak detection
 * - Disk I/O operations monitoring
 * - Network activity tracking
 * - Process-level resource monitoring
 * - System-level resource monitoring
 * - Resource usage alerts And thresholds
 * - Historical resource usage trends
 */

const FS = require('fs').promises;
const { loggers } = require('../lib/logger');
const os = require('os');
const { execSync } = require('child_process');


class ResourceMonitor {
  constructor(projectRoot, options = {}) {
    this.projectRoot = projectRoot;
    this.isMonitoring = false;
    this.monitoringInterval = null;
    this.samplingInterval = options.samplingInterval || 500; // 500ms default
    this.maxSamples = options.maxSamples || 1000; // Keep last 1000 samples

    // Resource data storage
    this.resourceData = {
      cpu: [],
      memory: [],
      disk: [],
      network: [],
      process: [],
      system: [],
    };

    // Baseline measurements
    this.baseline = {
      cpu: null,
      memory: null,
      disk: null,
      network: null,
      timestamp: null,
    };

    // Thresholds for alerting
    this.thresholds = {
      cpu: options.cpuThreshold || 80, // 80% CPU usage
      memory: options.memoryThreshold || 1024 * 1024 * 1024, // 1GB memory increase
      diskIO: options.diskIOThreshold || 1000, // 1000 operations per sample
      networkIO: options.networkIOThreshold || 1024 * 1024, // 1MB per sample
    };

    // Alert callbacks
    this.alertCallbacks = [];

    // Platform-specific implementation
    this.platform = os.platform();
    this.initializePlatformSpecific();
  }

  /**
   * Initialize platform-specific monitoring capabilities
   */
  initializePlatformSpecific() {
    this.platformCapabilities = {
      cpu: true,
      memory: true,
      disk: this.platform === 'linux' || this.platform === 'darwin',
      network: this.platform === 'linux' || this.platform === 'darwin',
      processes: true,
    };

    // Platform-specific commands
    this.commands = {
      cpu: {
        linux: "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'",
        darwin: "top -l1 -n0 | grep 'CPU usage' | awk '{print $3}' | sed 's/%//'",
        win32: 'wmic cpu get loadpercentage /value',
      },
      memory: {
        linux: 'free -m',
        darwin: 'vm_stat',
        win32: 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value',
      },
      disk: {
        linux: 'iostat -x 1 1',
        darwin: 'iostat -d 1 1',
        win32: 'wmic logicaldisk get size,freespace',
      },
      network: {
        linux: 'cat /proc/net/dev',
        darwin: 'netstat -ibn',
        win32: 'wmic path Win32_NetworkAdapter get name,BytesReceivedPerSec,BytesSentPerSec',
      },
    };
  }

  /**
   * Start comprehensive resource monitoring
   */
  async startMonitoring() {
    if (this.isMonitoring) {
      loggers.app.warn('Resource monitoring is already active');
      return { success: false, error: 'Already monitoring' };
    }

    try {
      this.isMonitoring = true;

      // Capture baseline measurements
      await this.captureBaseline();

      // Start monitoring intervals
      this.monitoringInterval = setInterval(async () => {
        await this.captureResourceSnapshot();
      }, this.samplingInterval);

      loggers.stopHook.info(`Resource monitoring started with ${this.samplingInterval}ms sampling interval`);

      loggers.app.info(`Resource monitoring started with ${this.samplingInterval}ms sampling interval`);

      return {
        success: true,
        samplingInterval: this.samplingInterval,
        capabilities: this.platformCapabilities,
        thresholds: this.thresholds,
      };

    } catch (error) {
      this.isMonitoring = false;
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Stop resource monitoring And return summary
   */
  async stopMonitoring() {
    if (!this.isMonitoring) {
      return { success: false, error: 'Not currently monitoring' };
    }

    try {
      // Stop monitoring
      this.isMonitoring = false;
      if (this.monitoringInterval) {
        clearInterval(this.monitoringInterval);
        this.monitoringInterval = null;
      }

      // Capture final snapshot
      const finalSnapshot = await this.captureResourceSnapshot();

      // Generate monitoring summary
      const summary = this.generateMonitoringSummary();

      // Check for alerts
      const alerts = this.checkThresholds();
      loggers.stopHook.info(`Resource monitoring stopped. Captured ${summary.totalSamples} samples`);

      loggers.app.info(`Resource monitoring stopped. Captured ${summary.totalSamples} samples`);

      return {
        success: true,
        summary,
        alerts,
        finalSnapshot,
        monitoringDuration: summary.duration,
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Capture baseline resource measurements
   */
  async captureBaseline() {
    this.baseline = {
      cpu: await this.getCPUUsage(),
      memory: await this.getMemoryUsage(),
      disk: await this.getDiskIO(),
      network: await this.getNetworkIO(),
      timestamp: Date.now(),
    };
  }

  /**
   * Capture a complete resource snapshot
   */
  async captureResourceSnapshot() {
    const timestamp = Date.now();
    try {
      // Capture all resource metrics;
      const snapshot = {
        timestamp,
        cpu: await this.getCPUUsage(),
        memory: await this.getMemoryUsage(),
        disk: await this.getDiskIO(),
        network: await this.getNetworkIO(),
        process: await this.getProcessUsage(),
        system: await this.getSystemInfo(),
      };

      // Store in appropriate arrays
      this.resourceData.cpu.push({ timestamp, ...snapshot.cpu });
      this.resourceData.memory.push({ timestamp, ...snapshot.memory });
      this.resourceData.disk.push({ timestamp, ...snapshot.disk });
      this.resourceData.network.push({ timestamp, ...snapshot.network });
      this.resourceData.process.push({ timestamp, ...snapshot.process });
      this.resourceData.system.push({ timestamp, ...snapshot.system });

      // Maintain rolling window
      this.trimDataArrays();

      // Check thresholds And trigger alerts if needed;
      const alerts = this.checkThresholds(snapshot);
      if (alerts.length > 0) {
        this.triggerAlerts(alerts);
      }

      return snapshot;
    } catch (error) {
      loggers.stopHook.warn('Failed to capture resource snapshot:', error.message);
      loggers.app.warn('Failed to capture resource snapshot:', error.message);
      return null;
    }
  }

  /**
   * Get CPU usage information
   */
  getCPUUsage() {
    try {
      const cpuUsage = process.cpuUsage();
      const loadAverage = os.loadavg();
      const cpuCount = os.cpus().length;

      // System-level CPU usage (platform-specific)
      let systemCpuUsage = null;
      try {
        const command = this.commands.cpu[this.platform];
        if (command) {
          const output = execSync(command, { timeout: 2000, encoding: 'utf8' });
          systemCpuUsage = this.parseCPUOutput(output);
        }
      } catch {
        // Platform command failed, use load average as fallback
        systemCpuUsage = Math.min(100, (loadAverage[0] / cpuCount) * 100);
      }

      return {
        process: {
          user: cpuUsage.user,
          system: cpuUsage.system,
          total: cpuUsage.user + cpuUsage.system,
        },
        system: {
          usage: systemCpuUsage,
          loadAverage,
          cpuCount,
          utilization: Math.min(100, (loadAverage[0] / cpuCount) * 100),
        },
      };

    } catch (error) {
      return {
        process: { user: 0, system: 0, total: 0 },
        system: { usage: null, loadAverage: [0, 0, 0], cpuCount: 0, utilization: 0 },
        error: error.message,
      };
    }
  }

  /**
   * Get memory usage information
   */
  getMemoryUsage() {
    try {
      const processMemory = process.memoryUsage();
      const systemMemory = {
        total: os.totalmem(),
        free: os.freemem(),
        used: os.totalmem() - os.freemem(),
      };

      // Calculate memory utilization;
      const systemUtilization = (systemMemory.used / systemMemory.total) * 100;

      // Memory pressure indicators;
      const memoryPressure = {
        rss: processMemory.rss,
        heapUsed: processMemory.heapUsed,
        heapTotal: processMemory.heapTotal,
        external: processMemory.external,
        arrayBuffers: processMemory.arrayBuffers,
      };

      return {
        process: processMemory,
        system: {
          ...systemMemory,
          utilization: systemUtilization,
          available: systemMemory.free,
        },
        pressure: memoryPressure,
      };

    } catch (error) {
      return {
        process: process.memoryUsage(),
        system: { total: 0, free: 0, used: 0, utilization: 0 },
        error: error.message,
      };
    }
  }

  /**
   * Get disk I/O information
   */
  async getDiskIO() {
    if (!this.platformCapabilities.disk) {
      return { available: false, reason: 'Platform not supported' };
    }

    try {
      // Platform-specific disk I/O monitoring;
      let diskStats = null;

      const command = this.commands.disk[this.platform];
      if (command) {
        const output = execSync(command, { timeout: 3000, encoding: 'utf8' });
        diskStats = this.parseDiskOutput(output);
      }

      // Get disk space information;
      const diskSpace = await this.getDiskSpace();

      return {
        io: diskStats,
        space: diskSpace,
        available: true,
      };

    } catch (error) {
      return {
        available: false,
        error: error.message,
      };
    }
  }

  /**
   * Get network I/O information
   */
  getNetworkIO() {
    if (!this.platformCapabilities.network) {
      return { available: false, reason: 'Platform not supported' };
    }

    try {
      let networkStats = null;

      const command = this.commands.network[this.platform];
      if (command) {
        const output = execSync(command, { timeout: 3000, encoding: 'utf8' });
        networkStats = this.parseNetworkOutput(output);
      }

      return {
        stats: networkStats,
        available: true,
      };

    } catch (error) {
      return {
        available: false,
        error: error.message,
      };
    }
  }

  /**
   * Get process-specific usage information
   */
  getProcessUsage() {
    try {
      const pid = process.pid;
      const uptime = process.uptime();
      const cwd = process.cwd();

      // File descriptor usage (Unix-like systems)
      let fdCount = null;
      try {
        if (this.platform !== 'win32') {
          const fdOutput = execSync(`ls /proc/${pid}/fd 2>/dev/null | wc -l`, { timeout: 1000, encoding: 'utf8' });
          fdCount = parseInt(fdOutput.trim(), 10);
        }
      } catch {
        // Ignore fd counting errors
      }

      return {
        pid,
        uptime,
        cwd,
        fdCount,
        nodeVersion: process.version,
        architecture: process.arch,
        platform: process.platform,
      };

    } catch (error) {
      return {
        pid: process.pid,
        error: error.message,
      };
    }
  }

  /**
   * Get system information
   */
  getSystemInfo() {
    try {
      return {
        hostname: os.hostname(),
        platform: os.platform(),
        release: os.release(),
        architecture: os.arch(),
        uptime: os.uptime(),
        cpuModel: os.cpus()[0]?.model || 'Unknown',
        cpuSpeed: os.cpus()[0]?.speed || 0,
        tempDir: os.tmpdir(),
      };

    } catch (error) {
      return {
        error: error.message,
      };
    }
  }

  /**
   * Get disk space information
   */
  async getDiskSpace() {
    try {
      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      await FS.stat(this.projectRoot);

      // Try to get disk usage for the project directory
      if (this.platform !== 'win32') {
        try {
          const dfOutput = execSync(`df -h "${this.projectRoot}"`, { timeout: 2000, encoding: 'utf8' });
          const lines = dfOutput.trim().split('\n');
          if (lines.length > 1) {
            const parts = lines[1].split(/\s+/);
            return {
              total: parts[1],
              used: parts[2],
              available: parts[3],
              usePercent: parts[4],
              filesystem: parts[0],
            };
          }
        } catch {
          // Ignore df command errors
        }
      }

      return {
        available: true,
        note: 'Basic disk space info unavailable',
      };

    } catch (error) {
      return {
        available: false,
        error: error.message,
      };
    }
  }

  /**
   * Parse platform-specific CPU _output
   */
  parseCPUOutput(_output) {
    try {
      if (this.platform === 'linux') {
        return parseFloat(_output.trim());
      } else if (this.platform === 'darwin') {
        return parseFloat(_output.trim());
      } else if (this.platform === 'win32') {
        const match = _output.match(/LoadPercentage=(\d+)/);
        return match ? parseInt(match[1], 10) : null;
      }
      return null;
    } catch {
      return null;
    }
  }

  /**
   * Parse platform-specific disk I/O _output
   */
  parseDiskOutput(_output) {
    try {
      const lines = _output.trim().split('\n');

      if (this.platform === 'linux') {
        // Parse iostat _output;
        const deviceLines = lines.filter(line => line.includes('sd') || line.includes('nvme'));
        if (deviceLines.length > 0) {
          const parts = deviceLines[0].split(/\s+/);
          return {
            device: parts[0],
            readsPerSec: parseFloat(parts[3]) || 0,
            writesPerSec: parseFloat(parts[4]) || 0,
            readKBPerSec: parseFloat(parts[5]) || 0,
            writeKBPerSec: parseFloat(parts[6]) || 0,
          };
        }
      } else if (this.platform === 'darwin') {
        // Parse macOS iostat _output;
        const diskLines = lines.filter(line => line.includes('disk'));
        if (diskLines.length > 0) {
          const parts = diskLines[0].split(/\s+/);
          return {
            device: parts[0],
            readMBPerSec: parseFloat(parts[1]) || 0,
            writeMBPerSec: parseFloat(parts[2]) || 0,
          };
        }
      }

      return null;
    } catch {
      return null;
    }
  }

  /**
   * Parse platform-specific network I/O _output
   */
  parseNetworkOutput(_output) {
    try {
      const lines = _output.trim().split('\n');

      if (this.platform === 'linux') {
        // Parse /proc/net/dev;
        const interfaceLines = lines.filter(line =>
          line.includes('eth') || line.includes('wlan') || line.includes('en'),
        );

        if (interfaceLines.length > 0) {
          const parts = interfaceLines[0].split(/\s+/);
          return {
            interface: parts[0].replace(':', ''),
            bytesReceived: parseInt(parts[1], 10) || 0,
            packetsReceived: parseInt(parts[2], 10) || 0,
            bytesTransmitted: parseInt(parts[9], 10) || 0,
            packetsTransmitted: parseInt(parts[10], 10) || 0,
          };
        }
      } else if (this.platform === 'darwin') {
        // Parse netstat _output;
        const interfaceLines = lines.filter(line => line.includes('en0') || line.includes('en1'));
        if (interfaceLines.length > 0) {
          const parts = interfaceLines[0].split(/\s+/);
          return {
            interface: parts[0],
            bytesReceived: parseInt(parts[6], 10) || 0,
            bytesTransmitted: parseInt(parts[9], 10) || 0,
          };
        }
      }

      return null;
    } catch {
      return null;
    }
  }

  /**
   * Trim data arrays to maintain rolling window
   */
  trimDataArrays() {
    Object.keys(this.resourceData).forEach(key => {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through Object.keys
      if (this.resourceData[key].length > this.maxSamples) {
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through Object.keys
        this.resourceData[key] = this.resourceData[key].slice(-this.maxSamples);
      }
    });
  }

  /**
   * Check resource usage against thresholds
   */
  checkThresholds(snapshot = null) {
    const alerts = [];

    if (!snapshot && this.resourceData.cpu.length === 0) {
      return alerts;
    }

    try {
      // Use latest snapshot if none provided;
      const current = snapshot || {
        cpu: this.resourceData.cpu[this.resourceData.cpu.length - 1],
        memory: this.resourceData.memory[this.resourceData.memory.length - 1],
        disk: this.resourceData.disk[this.resourceData.disk.length - 1],
        network: this.resourceData.network[this.resourceData.network.length - 1],
      };

      // CPU threshold check
      if (current.cpu && current.cpu.system && current.cpu.system.utilization > this.thresholds.cpu) {
        alerts.push({
          type: 'cpu',
          severity: 'warning',
          message: `CPU utilization (${current.cpu.system.utilization.toFixed(1)}%) exceeds threshold (${this.thresholds.cpu}%)`,
          value: current.cpu.system.utilization,
          threshold: this.thresholds.cpu,
          timestamp: current.timestamp || Date.now(),
        });
      }

      // Memory threshold check
      if (current.memory && this.baseline.memory) {
        const memoryIncrease = current.memory.process.rss - this.baseline.memory.process.rss;
        if (memoryIncrease > this.thresholds.memory) {
          alerts.push({
            type: 'memory',
            severity: 'warning',
            message: `Memory usage increased by ${Math.round(memoryIncrease / 1024 / 1024)}MB, exceeding threshold`,
            value: memoryIncrease,
            threshold: this.thresholds.memory,
            timestamp: current.timestamp || Date.now(),
          });
        }
      }

      return alerts;
    } catch (error) {
      loggers.stopHook.warn('Error checking thresholds:', error.message);
      loggers.app.warn('Error checking thresholds:', error.message);
      return alerts;
    }
  }

  /**
   * Trigger alerts by calling registered callbacks
   */
  triggerAlerts(alerts) {
    this.alertCallbacks.forEach(callback => {
      try {
        callback(alerts);
      } catch (error) {
        loggers.stopHook.warn('Alert callback failed:', error.message);
        loggers.app.warn('Alert callback failed:', error.message);
      }
    });
  }

  /**
   * Register alert callback
   */
  onAlert(callback) {
    if (typeof callback === 'function') {
      this.alertCallbacks.push(callback);
    }
  }

  /**
   * Generate comprehensive monitoring summary
   */
  generateMonitoringSummary() {
    const summary = {
      totalSamples: this.resourceData.cpu.length,
      duration: this.resourceData.cpu.length > 0 ?
        this.resourceData.cpu[this.resourceData.cpu.length - 1].timestamp - this.resourceData.cpu[0].timestamp :
        0,
      samplingInterval: this.samplingInterval,
      cpu: this.summarizeCPUData(),
      memory: this.summarizeMemoryData(),
      disk: this.summarizeDiskData(),
      network: this.summarizeNetworkData(),
      alerts: this.getAllAlerts(),
    };

    return summary;
  }

  /**
   * Summarize CPU usage data
   */
  summarizeCPUData() {
    if (this.resourceData.cpu.length === 0) {
      return { available: false };
    }

    const cpuData = this.resourceData.cpu.filter(d => d.system && d.system.utilization != null);
    if (cpuData.length === 0) {
      return { available: false };
    }

    const utilizations = cpuData.map(d => d.system.utilization);

    return {
      available: true,
      samples: cpuData.length,
      average: utilizations.reduce((sum, val) => sum + val, 0) / utilizations.length,
      min: Math.min(...utilizations),
      max: Math.max(...utilizations),
      trend: this.calculateTrend(utilizations),
    };
  }

  /**
   * Summarize memory usage data
   */
  summarizeMemoryData() {
    if (this.resourceData.memory.length === 0) {
      return { available: false };
    }

    const memData = this.resourceData.memory;
    const rssValues = memData.map(d => d.process.rss);
    const heapValues = memData.map(d => d.process.heapUsed);

    return {
      available: true,
      samples: memData.length,
      rss: {
        initial: rssValues[0],
        final: rssValues[rssValues.length - 1],
        peak: Math.max(...rssValues),
        average: rssValues.reduce((sum, val) => sum + val, 0) / rssValues.length,
      },
      heap: {
        initial: heapValues[0],
        final: heapValues[heapValues.length - 1],
        peak: Math.max(...heapValues),
        average: heapValues.reduce((sum, val) => sum + val, 0) / heapValues.length,
      },
      trend: this.calculateTrend(rssValues),
    };
  }

  /**
   * Summarize disk I/O data
   */
  summarizeDiskData() {
    const diskData = this.resourceData.disk.filter(d => d.io && d.available);

    if (diskData.length === 0) {
      return { available: false };
    }

    return {
      available: true,
      samples: diskData.length,
      // Additional disk analysis would go here
    };
  }

  /**
   * Summarize network I/O data
   */
  summarizeNetworkData() {
    const networkData = this.resourceData.network.filter(d => d.stats && d.available);

    if (networkData.length === 0) {
      return { available: false };
    }

    return {
      available: true,
      samples: networkData.length,
      // Additional network analysis would go here
    };
  }

  /**
   * Calculate trend for a series of values
   */
  calculateTrend(values) {
    if (values.length < 2) {
      return 'insufficient_data';
    }

    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));

    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;

    const change = ((secondAvg - firstAvg) / firstAvg) * 100;

    if (Math.abs(change) < 5) {return 'stable';}
    if (change > 10) {return 'increasing_significantly';}
    if (change > 0) {return 'increasing';}
    if (change < -10) {return 'decreasing_significantly';}
    return 'decreasing';
  }

  /**
   * Get all triggered alerts
   */
  getAllAlerts() {
    // This would maintain a history of all alerts triggered during monitoring
    // for now, return empty array as alerts are handled in real-time
    return [];
  }

  /**
   * Get current resource usage snapshot
   */
  getCurrentSnapshot() {
    return this.captureResourceSnapshot();
  }

  /**
   * Get resource usage data for external analysis
   */
  getResourceData() {
    return {
      ...this.resourceData,
      baseline: this.baseline,
      summary: this.generateMonitoringSummary(),
    };
  }
}

module.exports = ResourceMonitor;
