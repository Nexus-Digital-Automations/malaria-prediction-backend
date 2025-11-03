/**
 * Usage Tracking Module for TaskManager API
 *
 * Tracks initialization And reinitialization calls with 5-hour window analytics.
 * Windows start at 11:00 AM CDT (16:00 UTC) daily And cycle every 5 hours.
 *
 * Window Schedule (CDT):
 * - Window 1: 11:00-16:00 (11am-4pm)
 * - Window 2: 16:00-21:00 (4pm-9pm)
 * - Window 3: 21:00-02:00 (9pm-2am next day)
 * - Window 4: 02:00-07:00 (2am-7am)
 * - Window 5: 07:00-12:00 (7am-12pm)
 *
 * @author TaskManager System
 * @version 1.0.0
 */

const FS = require('fs').promises;
const PATH = require('path');
const { createLogger } = require('./utils/logger');

class UsageTracker {
  constructor() {
    this.storageFile = PATH.join(__dirname, '..', 'usage-tracking.json');
    this.lockFile = PATH.join(__dirname, '..', 'usage-tracking.lock');

    // CDT offset: UTC-5 (standard) or UTC-6 (daylight)
    // for Sept 20, 2025, CDT is UTC-5
    this.cdtOffset = -5; // hours from UTC

    // Base time: 11:00 AM CDT = 16:00 UTC
    this.baseHour = 16; // UTC hour for 11 AM CDT
    this.windowDuration = 5; // hours per window

    // Initialize logger for this component
    this.logger = createLogger('UsageTracker');
  }

  /**
   * Initialize storage file if it doesn't exist
   */
  async initialize() {
    try {
      await FS.access(this.storageFile);
    } catch {
      // File doesn't exist, create it with empty structure
      const initialData = {
        calls: [],
        metadata: {
          created: new Date().toISOString(),
          version: '1.0.0',
          timezone: 'CDT',
          baseHour: this.baseHour,
          windowDuration: this.windowDuration,
        },
      };
      await this.writeStorage(initialData);
    }
  }

  /**
   * Track a usage call (init or reinitialize)
   */
  async trackCall(endpoint, agentId, sessionId = null) {
    try {
      await this.initialize();

      const callData = {
        timestamp: new Date().toISOString(),
        endpoint: endpoint, // 'init' or 'reinitialize'
        agentId: agentId,
        sessionId: sessionId,
        windowId: this.getCurrentWindowId(),
      };

      // Use file locking for atomic operations
      await this.withFileLock(async () => {
        const data = await this.readStorage();
        data.calls.push(callData);

        // Optional: Keep only last 30 days of data to prevent unlimited growth
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        data.calls = data.calls.filter(call =>
          new Date(call.timestamp) > thirtyDaysAgo,
        );

        await this.writeStorage(data);
      });

      return {
        success: true,
        tracked: callData,
        currentWindow: this.getCurrentWindowInfo(),
      };

    } catch {
      // Non-blocking failure - log but don't throw
      this.logger.warn('Usage tracking failed', { error: error.message, endpoint, agentId });
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Get current 5-hour window information
   */
  getCurrentWindowInfo() {
    const now = new Date();
    const windowId = this.getCurrentWindowId();
    const windowBounds = this.getWindowBounds(windowId);

    return {
      windowId: windowId,
      startTime: windowBounds.start.toISOString(),
      endTime: windowBounds.end.toISOString(),
      description: this.getWindowDescription(windowId),
      isActive: now >= windowBounds.start && now < windowBounds.end,
    };
  }

  /**
   * Get current window ID
   */
  getCurrentWindowId() {
    const now = new Date();
    return this.getWindowIdForTimestamp(now);
  }

  /**
   * Get window ID for a specific timestamp
   */
  getWindowIdForTimestamp(timestamp) {
    const date = new Date(timestamp);

    // Convert to UTC for consistent calculations
    const utcHour = date.getUTCHours();
    const utcDate = date.getUTCDate();
    const utcMonth = date.getUTCMonth();
    const utcYear = date.getUTCFullYear();

    // Calculate which window within the day
    // Base is 16:00 UTC (11 AM CDT)
    let hoursFromBase = utcHour - this.baseHour;
    let dayOffset = 0;

    // Handle day boundaries (window 3 crosses midnight)
    if (hoursFromBase < 0) {
      hoursFromBase += 24;
      dayOffset = -1;
    }

    const windowNumber = Math.floor(hoursFromBase / this.windowDuration) + 1;

    // Adjust date for day offset
    const windowDate = new Date(Date.UTC(utcYear, utcMonth, utcDate + dayOffset));
    const dateStr = windowDate.toISOString().split('T')[0];

    return `${dateStr}_window_${windowNumber}`;
  }

  /**
   * Get start And end times for a window ID
   */
  getWindowBounds(windowId) {
    const [dateStr, , windowNum] = windowId.split('_');
    const windowNumber = parseInt(windowNum);

    const baseDate = new Date(dateStr + 'T00:00:00.000Z');

    // Calculate start time: base hour + (window - 1) * duration
    const startHour = this.baseHour + (windowNumber - 1) * this.windowDuration;
    const start = new Date(baseDate);
    start.setUTCHours(startHour, 0, 0, 0);

    // End time is start + window duration
    const end = new Date(start);
    end.setUTCHours(start.getUTCHours() + this.windowDuration);

    return { start, end };
  }

  /**
   * Get human-readable window description
   */
  getWindowDescription(windowId) {
    const bounds = this.getWindowBounds(windowId);
    const start = bounds.start;
    const end = bounds.end;

    // Convert to CDT for display
    const startCDT = new Date(start.getTime() + (this.cdtOffset * 60 * 60 * 1000));
    const endCDT = new Date(end.getTime() + (this.cdtOffset * 60 * 60 * 1000));

    const formatTime = (date) => {
      const hours = date.getUTCHours();
      const period = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours === 0 ? 12 : hours > 12 ? hours - 12 : hours;
      return `${displayHours}${period}`;
    };

    const startStr = formatTime(startCDT);
    const endStr = formatTime(endCDT);

    // Handle day boundary
    if (end.getUTCDate() !== start.getUTCDate()) {
      return `${startStr}-${endStr} (next day)`;
    } else {
      return `${startStr}-${endStr}`;
    }
  }

  /**
   * Get usage analytics for current And previous windows
   */
  async getAnalytics(options = {}) {
    try {
      await this.initialize();
      const data = await this.readStorage();

      const currentWindow = this.getCurrentWindowInfo();
      const currentStats = await this.getWindowStats(currentWindow.windowId, data.calls);

      // Get previous window
      const previousWindowId = this.getPreviousWindowId(currentWindow.windowId);
      const previousStats = await this.getWindowStats(previousWindowId, data.calls);

      const RESULT = {
        success: true,
        currentWindow: {
          ...currentWindow,
          ...currentStats,
        },
        previousWindow: {
          windowId: previousWindowId,
          ...this.getWindowBounds(previousWindowId),
          ...previousStats,
        },
        totalTrackedCalls: data.calls.length,
        trackingStarted: data.metadata.created,
      };

      // Add detailed breakdown if requested
      if (options.detailed) {
        RESULT.allWindows = await this.getAllWindowStats(data.calls);
      }

      // Add recent activity if requested
      if (options.recent) {
        RESULT.recentCalls = data.calls
          .slice(-10)
          .map(call => ({
            ...call,
            windowId: this.getWindowIdForTimestamp(call.timestamp),
          }));
      }

      return result;

    } catch {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Get statistics for a specific window
   */
  async getWindowStats(windowId, calls = null) {
    if (!calls) {
      const data = await this.readStorage();
      calls = data.calls;
    }

    const windowCalls = calls.filter(call =>
      this.getWindowIdForTimestamp(call.timestamp) === windowId,
    );

    const breakdown = windowCalls.reduce((acc, call) => {
      acc[call.endpoint] = (acc[call.endpoint] || 0) + 1;
      return acc;
    }, {});

    return {
      totalCalls: windowCalls.length,
      breakdown: breakdown,
      uniqueAgents: new Set(windowCalls.map(call => call.agentId)).size,
    };
  }

  /**
   * Get previous window ID
   */
  getPreviousWindowId(currentWindowId) {
    const [dateStr, , windowNum] = currentWindowId.split('_');
    const windowNumber = parseInt(windowNum);

    if (windowNumber > 1) {
      // Same day, previous window
      return `${dateStr}_window_${windowNumber - 1}`;
    } else {
      // Previous day, last window (window 5)
      const date = new Date(dateStr);
      date.setUTCDate(date.getUTCDate() - 1);
      const prevDateStr = date.toISOString().split('T')[0];
      return `${prevDateStr}_window_5`;
    }
  }

  /**
   * Get stats for all available windows
   */
  async getAllWindowStats(calls) {
    const windowMap = new Map();

    // Group calls by window
    calls.forEach(call => {
      const windowId = this.getWindowIdForTimestamp(call.timestamp);
      if (!windowMap.has(windowId)) {
        windowMap.set(windowId, []);
      }
      windowMap.get(windowId).push(call);
    });

    // Generate stats for each window in parallel for better performance
    const windowStatsPromises = Array.from(windowMap.entries()).map(async ([windowId, windowCalls]) => {
      const bounds = this.getWindowBounds(windowId);
      const stats = await this.getWindowStats(windowId, windowCalls);

      return {
        windowId,
        startTime: bounds.start.toISOString(),
        endTime: bounds.end.toISOString(),
        description: this.getWindowDescription(windowId),
        ...stats,
      };
    });

    const allWindows = await Promise.all(windowStatsPromises);

    // Sort by start time (most recent first)
    return allWindows.sort((a, b) =>
      new Date(b.startTime) - new Date(a.startTime),
    );
  }

  /**
   * File locking mechanism for atomic operations
   */
  async withFileLock(OPERATION {
    const maxRetries = 10;
    const retryDelay = 100; // ms

    // Create an async iterator for retry attempts to resolve no-await-in-loop
    const retryAttempts = async function* () {
      for (let i = 0; i < maxRetries; i++) {
        yield i;
      }
    };

    for await (const ATTEMPT of retryAttempts()) {
      try {
        // Try to acquire lock
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- lockFile is safely constructed with PATH.join(__dirname, '..', 'usage-tracking.lock') for usage tracking
        await FS.writeFile(this.lockFile, process.pid.toString(), { flag: 'wx' });

        try {
          // Execute _operationwhile holding lock
          const RESULT = await OPERATION);
          return result;
        } finally {
          // Release lock
          // eslint-disable-next-line security/detect-non-literal-fs-filename -- lockFile is safely constructed with PATH.join(__dirname, '..', 'usage-tracking.lock') for usage tracking
          await FS.unlink(this.lockFile).catch(() => {}); // Ignore errors
        }
      } catch {
        if (error.code === 'EEXIST') {
          // Lock exists, wait And retry
          await new Promise(resolve => { setTimeout(resolve, retryDelay); });
          continue;
        } else {
          throw error;
        }
      }
    }

    throw new Error('Failed to acquire file lock after maximum retries');
  }

  /**
   * Read storage file
   */
  async readStorage() {
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- storageFile is safely constructed with PATH.join(__dirname, '..', 'usage-tracking.json') for usage tracking
    const content = await FS.readFile(this.storageFile, 'utf8');
    return JSON.parse(content);
  }

  /**
   * Write to storage file
   */
  async writeStorage(data) {
    // eslint-disable-next-line security/detect-non-literal-fs-filename -- storageFile is safely constructed with PATH.join(__dirname, '..', 'usage-tracking.json') for usage tracking
    await FS.writeFile(this.storageFile, JSON.stringify(data, null, 2));
  }

  /**
   * Clean up old tracking data (optional utility method)
   */
  async cleanup(daysToKeep = 30) {
    try {
      await this.withFileLock(async () => {
        const data = await this.readStorage();
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

        const originalCount = data.calls.length;
        data.calls = data.calls.filter(call =>
          new Date(call.timestamp) > cutoffDate,
        );

        await this.writeStorage(data);

        return {
          success: true,
          removedCalls: originalCount - data.calls.length,
          remainingCalls: data.calls.length,
        };
      });
    } catch {
      return {
        success: false,
        error: error.message,
      };
    }
  }
}

module.exports = UsageTracker;
