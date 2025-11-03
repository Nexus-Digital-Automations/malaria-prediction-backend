/**
 * TaskPerformance - Performance Monitoring And Metrics Module
 *
 * === OVERVIEW ===
 * Handles performance monitoring, metrics collection, cache hit rate tracking,
 * And performance reporting for the TaskManager system. This module provides
 * comprehensive performance insights And optimization tracking.
 *
 * === KEY FEATURES ===
 * • Query time tracking And analysis
 * • Cache hit rate monitoring
 * • Memory usage tracking
 * • Performance report generation
 * • Bottleneck identification
 * • Batch _operationmetrics
 *
 * @fileoverview Performance monitoring And metrics for TaskManager
 * @author TaskManager System
 * @version 2.0.0
 * @since 2024-01-01
 */

const { loggers } = require('../logger');

class TaskPerformance {
  /**
   * Initialize TaskPerformance with configuration options
   * @param {Object} options - Performance monitoring options
   */
  constructor(options = {}) {
    this.enabled = options.enablePerformanceMonitoring !== false;
    this.logger = loggers.performance;
    this.maxMetricsHistory = options.maxMetricsHistory || 1000;

    // Initialize performance monitoring if enabled
    if (this.enabled) {
      this._metrics = {
        queryTimes: [],
        cacheHitRates: { hits: 0, misses: 0 },
        batchOperations: [],
        memoryUsage: [],
        operationCounts: new Map(),
        slowOperations: [],
        performanceWarnings: [],
      };

      this.logger.info('TaskPerformance monitoring initialized');
    } else {
      this.logger.debug('TaskPerformance monitoring disabled');
    }
  }

  /**
   * Record execution time for an operation
   * @param {string} OPERATION- Operation name
   * @param {number} duration - Duration in milliseconds
   * @param {Object} metadata - Additional metadata
   */
  recordQueryTime(operation, duration, metadata = {}) {
    if (!this.enabled) {return;}

    const record = { operation,
      duration,
      timestamp: Date.now(),
      metadata,
    };

    this._metrics.queryTimes.push(record);

    // Track _operationcounts
    const currentCount = this._metrics.operationCounts.get(operation) || 0;
    this._metrics.operationCounts.set(operation, currentCount + 1);

    // Track slow operations (> 100ms)
    if (duration > 100) {
      this._metrics.slowOperations.push({
        ...record,
        threshold: 100,
        severity: duration > 500 ? 'high' : duration > 200 ? 'medium' : 'low',
      });

      this.logger.warn(`Slow operation detected: ${operation} took ${duration}ms`);
    }

    // Keep only recent metrics to prevent memory leaks
    if (this._metrics.queryTimes.length > this.maxMetricsHistory) {
      this._metrics.queryTimes = this._metrics.queryTimes.slice(-this.maxMetricsHistory);
    }

    // Performance warning for consistently slow operations
    if (this._isOperationConsistentlySlow(operation)) {
      this._addPerformanceWarning(operation, 'consistently_slow');
    }

    this.logger.debug(`Recorded query time: ${operation} = ${duration}ms`);
  }

  /**
   * Record cache hit or miss
   * @param {boolean} hit - True for cache hit, false for cache miss
   * @param {string} OPERATION- Operation That triggered the cache check
   * @param {Object} metadata - Additional metadata
   */
  recordCacheHit(hit, operation = 'unknown', _metadata = {}) {
    if (!this.enabled) {return;}

    if (hit) {
      this._metrics.cacheHitRates.hits++;
    } else {
      this._metrics.cacheHitRates.misses++;
    }

    this.logger.debug(`Cache ${hit ? 'hit' : 'miss'} for operation ${operation}`);

    // Track cache performance warnings
    const totalRequests = this._metrics.cacheHitRates.hits + this._metrics.cacheHitRates.misses;
    if (totalRequests > 100) { // Only check after sufficient data
      const hitRate = (this._metrics.cacheHitRates.hits / totalRequests) * 100;
      if (hitRate < 50) {
        this._addPerformanceWarning('cache', 'low_hit_rate', { hitRate });
      }
    }
  }

  /**
   * Record batch _operationmetrics
   * @param {string} OPERATION- Batch _operationname
   * @param {number} itemCount - Number of items processed
   * @param {number} duration - Total duration in milliseconds
   * @param {Object} metadata - Additional metadata
   */
  recordBatchOperation(operation, itemCount, duration, metadata = {}) {
    if (!this.enabled) {return;}

    const record = { operation,
      itemCount,
      duration,
      avgItemTime: itemCount > 0 ? duration / itemCount : 0,
      throughput: itemCount > 0 ? (itemCount / duration) * 1000 : 0, // items per second
      timestamp: Date.now(),
      metadata,
    };

    this._metrics.batchOperations.push(record);

    // Keep only recent batch metrics
    if (this._metrics.batchOperations.length > 100) {
      this._metrics.batchOperations = this._metrics.batchOperations.slice(-100);
    }

    this.logger.info(`Batch operation ${operation} processed ${itemCount} items in ${duration}ms (${record.throughput.toFixed(2)} items/sec)`);
  }

  /**
   * Record current memory usage
   * @param {Object} additionalMetrics - Additional memory metrics
   */
  recordMemoryUsage(additionalMetrics = {}) {
    if (!this.enabled) {return;}

    const memInfo = process.memoryUsage();
    const record = {
      timestamp: Date.now(),
      heapUsed: memInfo.heapUsed,
      heapTotal: memInfo.heapTotal,
      external: memInfo.external,
      rss: memInfo.rss,
      ...additionalMetrics,
    };

    this._metrics.memoryUsage.push(record);

    // Keep only recent memory metrics (last 100 samples)
    if (this._metrics.memoryUsage.length > 100) {
      this._metrics.memoryUsage = this._metrics.memoryUsage.slice(-100);
    }

    // Memory warning for high usage
    const heapUsedMB = memInfo.heapUsed / (1024 * 1024);
    if (heapUsedMB > 500) { // 500MB threshold
      this._addPerformanceWarning('memory', 'high_usage', { heapUsedMB });
    }

    this.logger.debug(`Memory usage: ${(heapUsedMB).toFixed(2)}MB heap used`);
  }

  /**
   * Generate comprehensive performance report
   * @returns {Object} Performance report with metrics And analysis
   */
  getPerformanceReport() {
    if (!this.enabled) {
      return {
        enabled: false,
        message: 'Performance monitoring is disabled',
      };
    }

    const report = {
      enabled: true,
      timestamp: new Date().toISOString(),
      summary: this._generateSummary(),
      queryMetrics: this._analyzeQueryMetrics(),
      cacheMetrics: this._analyzeCacheMetrics(),
      batchMetrics: this._analyzeBatchMetrics(),
      memoryMetrics: this._analyzeMemoryMetrics(),
      warnings: this._metrics.performanceWarnings.slice(-10), // Last 10 warnings
      recommendations: this._generateRecommendations(),
    };

    this.logger.info('Generated performance report');
    return report;
  }

  /**
   * Get basic performance statistics
   * @returns {Object} Basic performance statistics
   */
  getBasicStats() {
    if (!this.enabled) {
      return { enabled: false };
    }

    const avgQueryTime = this._metrics.queryTimes.length > 0
      ? this._metrics.queryTimes.reduce((sum, m) => sum + m.duration, 0) / this._metrics.queryTimes.length
      : 0;

    const totalCacheRequests = this._metrics.cacheHitRates.hits + this._metrics.cacheHitRates.misses;
    const cacheHitRate = totalCacheRequests > 0
      ? (this._metrics.cacheHitRates.hits / totalCacheRequests) * 100
      : 0;

    return {
      enabled: true,
      avgQueryTime: `${avgQueryTime.toFixed(2)}ms`,
      cacheHitRate: `${cacheHitRate.toFixed(1)}%`,
      totalQueries: this._metrics.queryTimes.length,
      slowOperations: this._metrics.slowOperations.length,
      warnings: this._metrics.performanceWarnings.length,
    };
  }

  /**
   * Clear all performance metrics
   */
  clearMetrics() {
    if (!this.enabled) {return;}

    this._metrics = {
      queryTimes: [],
      cacheHitRates: { hits: 0, misses: 0 },
      batchOperations: [],
      memoryUsage: [],
      operationCounts: new Map(),
      slowOperations: [],
      performanceWarnings: [],
    };

    this.logger.info('Performance metrics cleared');
  }

  /**
   * Enable performance monitoring
   */
  enable() {
    this.enabled = true;
    if (!this._metrics) {
      this._metrics = {
        queryTimes: [],
        cacheHitRates: { hits: 0, misses: 0 },
        batchOperations: [],
        memoryUsage: [],
        operationCounts: new Map(),
        slowOperations: [],
        performanceWarnings: [],
      };
    }
    this.logger.info('Performance monitoring enabled');
  }

  /**
   * Disable performance monitoring
   */
  disable() {
    this.enabled = false;
    this.logger.info('Performance monitoring disabled');
  }

  /**
   * Generate summary statistics
   * @returns {Object} Summary statistics
   * @private
   */
  _generateSummary() {
    const queryCount = this._metrics.queryTimes.length;
    const avgQueryTime = queryCount > 0
      ? this._metrics.queryTimes.reduce((sum, m) => sum + m.duration, 0) / queryCount
      : 0;

    const totalCacheRequests = this._metrics.cacheHitRates.hits + this._metrics.cacheHitRates.misses;
    const cacheHitRate = totalCacheRequests > 0
      ? (this._metrics.cacheHitRates.hits / totalCacheRequests) * 100
      : 0;

    const batchOpsCount = this._metrics.batchOperations.length;
    const avgBatchThroughput = batchOpsCount > 0
      ? this._metrics.batchOperations.reduce((sum, b) => sum + b.throughput, 0) / batchOpsCount
      : 0;

    return {
      totalQueries: queryCount,
      avgQueryTime: parseFloat(avgQueryTime.toFixed(2)),
      cacheHitRate: parseFloat(cacheHitRate.toFixed(1)),
      totalBatchOperations: batchOpsCount,
      avgBatchThroughput: parseFloat(avgBatchThroughput.toFixed(2)),
      slowOperations: this._metrics.slowOperations.length,
      activeWarnings: this._metrics.performanceWarnings.filter(w => !w.resolved).length,
    };
  }

  /**
   * Analyze query metrics in detail
   * @returns {Object} Query metrics analysis
   * @private
   */
  _analyzeQueryMetrics() {
    if (this._metrics.queryTimes.length === 0) {
      return { noData: true };
    }

    const durations = this._metrics.queryTimes.map(q => q.duration);
    durations.sort((a, b) => a - b);

    const percentile95 = durations[Math.floor(durations.length * 0.95)] || 0;
    const percentile99 = durations[Math.floor(durations.length * 0.99)] || 0;
    const median = durations[Math.floor(durations.length * 0.5)] || 0;

    const operationBreakdown = new Map();
    for (const [operation, count] of this._metrics.operationCounts.entries()) {
      const opQueries = this._metrics.queryTimes.filter(q => q.operation === operation);
      const avgTime = opQueries.length > 0
        ? opQueries.reduce((sum, q) => sum + q.duration, 0) / opQueries.length
        : 0;

      // Use Map.set() to safely assign without object injection risk
      operationBreakdown.set(operation, {
        count,
        avgTime: parseFloat(avgTime.toFixed(2)),
        slowQueries: opQueries.filter(q => q.duration > 100).length,
      });
    }

    return {
      total: this._metrics.queryTimes.length,
      median: parseFloat(median.toFixed(2)),
      percentile95: parseFloat(percentile95.toFixed(2)),
      percentile99: parseFloat(percentile99.toFixed(2)),
      slowQueries: this._metrics.slowOperations.length,
      operationBreakdown: Object.fromEntries(operationBreakdown),
    };
  }

  /**
   * Analyze cache metrics
   * @returns {Object} Cache metrics analysis
   * @private
   */
  _analyzeCacheMetrics() {
    const hits = this._metrics.cacheHitRates.hits;
    const misses = this._metrics.cacheHitRates.misses;
    const total = hits + misses;

    if (total === 0) {
      return { noData: true };
    }

    const hitRate = (hits / total) * 100;
    const missRate = (misses / total) * 100;

    return {
      hits,
      misses,
      total,
      hitRate: parseFloat(hitRate.toFixed(1)),
      missRate: parseFloat(missRate.toFixed(1)),
      efficiency: hitRate > 80 ? 'excellent' : hitRate > 60 ? 'good' : hitRate > 40 ? 'fair' : 'poor',
    };
  }

  /**
   * Analyze batch _operationmetrics
   * @returns {Object} Batch metrics analysis
   * @private
   */
  _analyzeBatchMetrics() {
    if (this._metrics.batchOperations.length === 0) {
      return { noData: true };
    }

    const totalItems = this._metrics.batchOperations.reduce((sum, b) => sum + b.itemCount, 0);
    const _totalDuration = this._metrics.batchOperations.reduce((sum, b) => sum + b.duration, 0);
    const avgThroughput = this._metrics.batchOperations.reduce((sum, b) => sum + b.throughput, 0) / this._metrics.batchOperations.length;

    const operationTypes = new Map();
    for (const batch of this._metrics.batchOperations) {
      const existing = operationTypes.get(batch.operation) || { count: 0, totalItems: 0, totalDuration: 0 };
      existing.count++;
      existing.totalItems += batch.itemCount;
      existing.totalDuration += batch.duration;
      operationTypes.set(batch.operation, existing);
    }

    const operationBreakdown = new Map();
    for (const [operation, data] of operationTypes.entries()) {
      // Use Map.set() to safely assign without object injection risk
      operationBreakdown.set(operation, {
        batchCount: data.count,
        avgItemsPerBatch: parseFloat((data.totalItems / data.count).toFixed(1)),
        avgThroughput: parseFloat(((data.totalItems / data.totalDuration) * 1000).toFixed(2)),
      });
    }

    return {
      totalBatches: this._metrics.batchOperations.length,
      totalItems,
      avgThroughput: parseFloat(avgThroughput.toFixed(2)),
      operationBreakdown: Object.fromEntries(operationBreakdown),
    };
  }

  /**
   * Analyze memory usage metrics
   * @returns {Object} Memory metrics analysis
   * @private
   */
  _analyzeMemoryMetrics() {
    if (this._metrics.memoryUsage.length === 0) {
      return { noData: true };
    }

    const latest = this._metrics.memoryUsage[this._metrics.memoryUsage.length - 1];
    const heapUsages = this._metrics.memoryUsage.map(m => m.heapUsed);
    const avgHeapUsage = heapUsages.reduce((sum, h) => sum + h, 0) / heapUsages.length;
    const maxHeapUsage = Math.max(...heapUsages);

    return {
      current: {
        heapUsedMB: parseFloat((latest.heapUsed / (1024 * 1024)).toFixed(2)),
        heapTotalMB: parseFloat((latest.heapTotal / (1024 * 1024)).toFixed(2)),
        rssMB: parseFloat((latest.rss / (1024 * 1024)).toFixed(2)),
      },
      average: {
        heapUsedMB: parseFloat((avgHeapUsage / (1024 * 1024)).toFixed(2)),
      },
      peak: {
        heapUsedMB: parseFloat((maxHeapUsage / (1024 * 1024)).toFixed(2)),
      },
      samples: this._metrics.memoryUsage.length,
    };
  }

  /**
   * Generate performance recommendations
   * @returns {Array} Array of performance recommendations
   * @private
   */
  _generateRecommendations() {
    const recommendations = [];

    // Cache hit rate recommendations
    const totalCacheRequests = this._metrics.cacheHitRates.hits + this._metrics.cacheHitRates.misses;
    if (totalCacheRequests > 100) {
      const hitRate = (this._metrics.cacheHitRates.hits / totalCacheRequests) * 100;
      if (hitRate < 50) {
        recommendations.push({
          type: 'cache',
          priority: 'high',
          message: `Cache hit rate is ${hitRate.toFixed(1)}%. Consider reviewing caching strategy.`,
          action: 'Review cache configuration And invalidation logic',
        });
      }
    }

    // Slow _operationrecommendations
    if (this._metrics.slowOperations.length > 10) {
      recommendations.push({
        type: 'performance',
        priority: 'medium',
        message: `${this._metrics.slowOperations.length} slow operations detected.`,
        action: 'Optimize frequently slow operations',
      });
    }

    // Memory usage recommendations
    if (this._metrics.memoryUsage.length > 0) {
      const latest = this._metrics.memoryUsage[this._metrics.memoryUsage.length - 1];
      const heapUsedMB = latest.heapUsed / (1024 * 1024);
      if (heapUsedMB > 500) {
        recommendations.push({
          type: 'memory',
          priority: 'high',
          message: `High memory usage: ${heapUsedMB.toFixed(2)}MB heap used.`,
          action: 'Review memory usage patterns And consider cleanup strategies',
        });
      }
    }

    return recommendations;
  }

  /**
   * Check if an _operationis consistently slow
   * @param {string} OPERATION- Operation name
   * @returns {boolean} True if consistently slow
   * @private
   */
  _isOperationConsistentlySlow(operation) {
    const recentOps = this._metrics.queryTimes
      .filter(q => q.operation === operation)
      .slice(-10); // Last 10 operations

    if (recentOps.length < 5) { return false; }

    const slowCount = recentOps.filter(q => q.duration > 100).length;
    return slowCount / recentOps.length > 0.8; // 80% are slow
  }

  /**
   * Add a performance warning
   * @param {string} category - Warning category
   * @param {string} type - Warning type
   * @param {Object} metadata - Additional metadata
   * @private
   */
  _addPerformanceWarning(category, type, metadata = {}) {
    // Avoid duplicate warnings for the same issue
    const recentWarnings = this._metrics.performanceWarnings.slice(-5);
    const isDuplicate = recentWarnings.some(w =>
      w.category === category && w.type === type && (Date.now() - w.timestamp < 60000),
    );

    if (!isDuplicate) {
      this._metrics.performanceWarnings.push({
        category,
        type,
        timestamp: Date.now(),
        metadata,
        resolved: false,
      });

      // Keep only recent warnings
      if (this._metrics.performanceWarnings.length > 50) {
        this._metrics.performanceWarnings = this._metrics.performanceWarnings.slice(-50);
      }

      this.logger.warn(`Performance warning: ${category}:${type}`, metadata);
    }
  }
}

module.exports = TaskPerformance;
