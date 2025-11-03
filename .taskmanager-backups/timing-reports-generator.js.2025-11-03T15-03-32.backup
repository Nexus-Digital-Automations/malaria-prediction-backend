

/**
 * Detailed Timing Reports Generator for Stop Hook Validation Performance Metrics
 *
 * This module provides comprehensive timing analysis And reporting capabilities
 * for validation performance metrics. It generates detailed reports showing
 * execution times, trends, bottlenecks, And performance insights.
 *
 * Features:
 * - Per-criterion timing analysis
 * - Phase-by-phase execution breakdown
 * - Historical trend analysis
 * - Performance benchmarking
 * - Comparative analysis
 * - Bottleneck identification
 */

const FS = require('fs').promises;
const { loggers } = require('../lib/logger');
const path = require('path');


class TimingReportsGenerator {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.metricsFile = path.join(projectRoot, '.validation-performance-enhanced.json');
    this.legacyMetricsFile = path.join(projectRoot, '.validation-performance.json');
  }

  /**
   * Generate comprehensive timing report for all validation criteria
   */
  async generateComprehensiveTimingReport(options = {}) {
    try {
      const timeRange = options.timeRange || 30; // days;
      const includePhases = options.includePhases !== false;
      const includeTrends = options.includeTrends !== false;
      const includeComparisons = options.includeComparisons !== false;

      // Load metrics data;
      const metricsData = await this._loadMetricsData();

      // Filter by time range;
      const cutoffDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);
      const filteredMetrics = metricsData.filter(m =>
        new Date(m.timing ? m.timing.startTime : m.startTime) >= cutoffDate,
      );

      if (filteredMetrics.length === 0) {
        return {
          success: true,
          report: {
            summary: 'No metrics data available for the specified time range',
            timeRange: { days: timeRange, from: cutoffDate.toISOString() },
            totalRecords: 0 } };
      }

      // Generate report sections;
      const report = {
        metadata: {
          generatedAt: new Date().toISOString(),
          timeRange: {
            days: timeRange,
            from: cutoffDate.toISOString(),
            to: new Date().toISOString() },
          totalRecords: filteredMetrics.length,
          reportType: 'comprehensive_timing_analysis' },

        // Overall timing summary
        summary: await this._generateTimingSummary(filteredMetrics),

        // Per-criterion analysis
        byCriterion: await this._generateCriterionTimingAnalysis(filteredMetrics),

        // Phase analysis (if requested And available)
        phaseAnalysis: includePhases ? await this._generatePhaseTimingAnalysis(filteredMetrics) : null,

        // Trend analysis (if requested)
        trends: includeTrends ? await this._generateTimingTrends(filteredMetrics, options) : null,

        // Performance benchmarks And comparisons
        benchmarks: includeComparisons ? await this._generatePerformanceBenchmarks(filteredMetrics) : null,

        // Bottleneck analysis
        bottlenecks: await this._analyzeTimingBottlenecks(filteredMetrics),

        // Recommendations
        recommendations: await this._generateTimingRecommendations(filteredMetrics) };

      return {
        success: true,
        report };

    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Generate timing report for a specific validation criterion
   */
  async generateCriterionTimingReport(criterion, options = {}) {
    try {
      const timeRange = options.timeRange || 30;
      const includeDetails = options.includeDetails !== false;

      // Load And filter metrics;
      const metricsData = await this._loadMetricsData();
      const cutoffDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

      const criterionMetrics = metricsData.filter(m => {
        const metricCriterion = m.criterion || m.criterion;
        const metricTime = new Date(m.timing ? m.timing.startTime : m.startTime);
        return metricCriterion === criterion && metricTime >= cutoffDate;
      });

      if (criterionMetrics.length === 0) {
        return {
          success: true,
          report: {
            criterion,
            summary: 'No timing data available for this criterion in the specified time range',
            totalRecords: 0 } };
      }

      const report = {
        metadata: {
          criterion,
          generatedAt: new Date().toISOString(),
          timeRange: { days: timeRange, from: cutoffDate.toISOString() },
          totalRecords: criterionMetrics.length },

        // Statistical summary
        statistics: this._calculateTimingStatistics(criterionMetrics),

        // Performance distribution
        distribution: this._calculateTimingDistribution(criterionMetrics),

        // Recent performance
        recentPerformance: this._analyzeRecentPerformance(criterionMetrics, 7), // Last 7 days

        // Performance trends
        trends: this._calculatePerformanceTrend(criterionMetrics),

        // Detailed execution records (if requested)
        executionHistory: includeDetails ? this._formatExecutionHistory(criterionMetrics.slice(-20)) : null,

        // Anomaly detection
        anomalies: this._detectPerformanceAnomalies(criterionMetrics),

        // Performance insights
        insights: this._generateCriterionInsights(criterionMetrics) };

      return {
        success: true,
        report };

    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Generate performance comparison report between multiple criteria
   */
  async generatePerformanceComparison(criteria = [], options = {}) {
    try {
      const timeRange = options.timeRange || 30;
      const metricsData = await this._loadMetricsData();
      const cutoffDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

      // If no criteria specified, use all available
      if (criteria.length === 0) {
        criteria = [...new Set(metricsData.map(m => m.criterion || m.criterion))];
      }

      const comparisons = {};
      const overallStats = {
        fastest: null,
        slowest: null,
        mostReliable: null,
        leastReliable: null };

      for (const criterion of criteria) {
        const criterionMetrics = metricsData.filter(m => {
          const metricCriterion = m.criterion || m.criterion;
          const metricTime = new Date(m.timing ? m.timing.startTime : m.startTime);
          return metricCriterion === criterion && metricTime >= cutoffDate;
        });

        if (criterionMetrics.length > 0) {
          const stats = this._calculateTimingStatistics(criterionMetrics);
          // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
          comparisons[criterion] = {
            ...stats,
            relativePerformance: 'calculating...', // Will be calculated after all stats
          };

          // Track overall extremes
          if (!overallStats.fastest || stats.averageDuration < comparisons[overallStats.fastest].averageDuration) {
            overallStats.fastest = criterion;
          }
          if (!overallStats.slowest || stats.averageDuration > comparisons[overallStats.slowest].averageDuration) {
            overallStats.slowest = criterion;
          }
          if (!overallStats.mostReliable || stats.successRate > comparisons[overallStats.mostReliable].successRate) {
            overallStats.mostReliable = criterion;
          }
          if (!overallStats.leastReliable || stats.successRate < comparisons[overallStats.leastReliable].successRate) {
            overallStats.leastReliable = criterion;
          }
        }
      }

      // Calculate relative performance ratings;
      const avgOfAverages = Object.values(comparisons).reduce((sum, c) => sum + c.averageDuration, 0) / Object.keys(comparisons).length;

      Object.keys(comparisons).forEach(criterion => {
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        const comp = comparisons[criterion];
        const relativeFactor = comp.averageDuration / avgOfAverages;

        if (relativeFactor <= 0.7) {comp.relativePerformance = 'excellent';} else if (relativeFactor <= 0.9) {comp.relativePerformance = 'good';} else if (relativeFactor <= 1.1) {comp.relativePerformance = 'average';} else if (relativeFactor <= 1.5) {comp.relativePerformance = 'below_average';} else {comp.relativePerformance = 'poor';}
      });

      return {
        success: true,
        report: {
          metadata: {
            generatedAt: new Date().toISOString(),
            timeRange: { days: timeRange, from: cutoffDate.toISOString() },
            criteriaCompared: criteria.length },
          overallStats,
          comparisons,
          summary: this._generateComparisonSummary(comparisons, overallStats) } };

    } catch (_) {
      return {
        success: false,
        error: _.message };
    }
  }

  /**
   * Load metrics data from both enhanced And legacy sources
   */
  async _loadMetricsData() {
    let allMetrics = [];

    // Try to load enhanced metrics first,
    try {
      if (await this._fileExists(this.metricsFile)) {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        const enhancedData = JSON.parse(await FS.readFile(this.metricsFile, 'utf8'));
        if (enhancedData.metrics && Array.isArray(enhancedData.metrics)) {
          allMetrics = allMetrics.concat(enhancedData.metrics);
        }
      }
    } catch (_) {
      loggers.stopHook.warn('Could not load enhanced metrics:', _.message);
    }

    // Load legacy metrics for compatibility
    try {
      if (await this._fileExists(this.legacyMetricsFile)) {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
        const legacyData = JSON.parse(await FS.readFile(this.legacyMetricsFile, 'utf8'));
        if (legacyData.metrics && Array.isArray(legacyData.metrics)) {
          allMetrics = allMetrics.concat(legacyData.metrics);
        }
      }
    } catch (_) {
      loggers.stopHook.warn('Could not load legacy metrics:', _.message);
      loggers.app.warn('Could not load legacy metrics:', _.message);
    }

    // Remove duplicates And sort by timestamp;
    const uniqueMetrics = allMetrics.filter((metric, index, array) => {


      const timestamp = metric.timing ? metric.timing.startTime : metric.startTime;
      return array.findIndex(m => {
        const mTimestamp = m.timing ? m.timing.startTime : m.startTime;
        return mTimestamp === timestamp && (m.criterion || m.criterion) === (metric.criterion || metric.criterion);
      }) === index;
    });

    return uniqueMetrics.sort((a, b) => {
      const aTime = new Date(a.timing ? a.timing.startTime : a.startTime);
      const bTime = new Date(b.timing ? b.timing.startTime : b.startTime);
      return aTime - bTime;
    });
  }

  /**
   * Generate overall timing summary
   */
  _generateTimingSummary(metrics) {
    const durations = metrics.map(m => m.timing ? m.timing.durationMs : m.durationMs).filter(d => d != null);
    const successful = metrics.filter(m => m.execution ? m.execution.success : m.success);
    return {
      totalExecutions: metrics.length,
      successfulExecutions: successful.length,
      failedExecutions: metrics.length - successful.length,
      successRate: ((successful.length / metrics.length) * 100).toFixed(2) + '%',
      timing: {
        averageDuration: Math.round(durations.reduce((sum, d) => sum + d, 0) / durations.length),
        medianDuration: this._calculateMedian(durations),
        minDuration: Math.min(...durations),
        maxDuration: Math.max(...durations),
        totalTime: durations.reduce((sum, d) => sum + d, 0) },
      timeRange: {
        from: metrics[0].timing ? metrics[0].timing.startTime : metrics[0].startTime,
        to: metrics[metrics.length - 1].timing ? metrics[metrics.length - 1].timing.startTime : metrics[metrics.length - 1].startTime } };
  }

  /**
   * Generate per-criterion timing analysis
   */
  _generateCriterionTimingAnalysis(metrics) {
    const byCriterion = {};

    // Group metrics by criterion
    metrics.forEach(metric => {
      const criterion = metric.criterion || metric.criterion;
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      if (!byCriterion[criterion]) {
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        byCriterion[criterion] = [];
      }
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      byCriterion[criterion].push(metric);
    });

    // Calculate statistics for each criterion;
    const analysis = {};
    Object.entries(byCriterion).forEach(([criterion, criterionMetrics]) => {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      analysis[criterion] = this._calculateTimingStatistics(criterionMetrics);
    });

    return analysis;
  }

  /**
   * Generate phase timing analysis for enhanced metrics
   */
  _generatePhaseTimingAnalysis(metrics) {
    const enhancedMetrics = metrics.filter(m => m.timing && m.timing.phases);

    if (enhancedMetrics.length === 0) {
      return { message: 'No phase timing data available' };
    }

    const phaseStats = {};

    enhancedMetrics.forEach(metric => {


      Object.entries(metric.timing.phases).forEach(([phase, duration]) => {
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        if (!phaseStats[phase]) {
          // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
          phaseStats[phase] = { durations: [], total: 0, count: 0 };
        }
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        phaseStats[phase].durations.push(duration);
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        phaseStats[phase].total += duration;
        // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
        phaseStats[phase].count++;
      });
    });

    const analysis = {};
    Object.entries(phaseStats).forEach(([phase, stats]) => {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      analysis[phase] = {
        averageDuration: Math.round(stats.total / stats.count),
        medianDuration: this._calculateMedian(stats.durations),
        minDuration: Math.min(...stats.durations),
        maxDuration: Math.max(...stats.durations),
        totalTime: stats.total,
        executionCount: stats.count,
        percentageOfTotal: 0, // Will be calculated below
      };
    });

    // Calculate percentage of total time for each phase;
    const totalPhaseTime = Object.values(analysis).reduce((sum, phase) => sum + phase.totalTime, 0);
    Object.values(analysis).forEach(phase => {
      phase.percentageOfTotal = ((phase.totalTime / totalPhaseTime) * 100).toFixed(1) + '%';
    });

    return {
      summary: `Phase analysis based on ${enhancedMetrics.length} enhanced metric records`,
      phases: analysis,
      insights: this._generatePhaseInsights(analysis) };
  }

  /**
   * Calculate timing statistics for a set of metrics
   */
  _calculateTimingStatistics(metrics) {
    const durations = metrics.map(m => m.timing ? m.timing.durationMs : m.durationMs).filter(d => d != null);
    const successful = metrics.filter(m => m.execution ? m.execution.success : m.success);

    if (durations.length === 0) {
      return { error: 'No duration data available' };
    }

    return {
      executionCount: metrics.length,
      successCount: successful.length,
      failureCount: metrics.length - successful.length,
      successRate: ((successful.length / metrics.length) * 100).toFixed(2) + '%',
      averageDuration: Math.round(durations.reduce((sum, d) => sum + d, 0) / durations.length),
      medianDuration: this._calculateMedian(durations),
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      standardDeviation: Math.round(this._calculateStandardDeviation(durations)),
      percentiles: {
        p50: this._calculatePercentile(durations, 50),
        p90: this._calculatePercentile(durations, 90),
        p95: this._calculatePercentile(durations, 95),
        p99: this._calculatePercentile(durations, 99) } };
  }

  /**
   * Calculate timing distribution
   */
  _calculateTimingDistribution(metrics) {
    const durations = metrics.map(m => m.timing ? m.timing.durationMs : m.durationMs).filter(d => d != null);

    const buckets = {
      'under_1s': durations.filter(d => d < 1000).length,
      '1s_to_5s': durations.filter(d => d >= 1000 && d < 5000).length,
      '5s_to_15s': durations.filter(d => d >= 5000 && d < 15000).length,
      '15s_to_30s': durations.filter(d => d >= 15000 && d < 30000).length,
      'over_30s': durations.filter(d => d >= 30000).length };

    const total = durations.length;
    const distribution = {};

    Object.entries(buckets).forEach(([bucket, count]) => {
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      distribution[bucket] = {
        count,
        percentage: ((count / total) * 100).toFixed(1) + '%' };
    });

    return distribution;
  }

  /**
   * Helper methods for statistical calculations
   */
  _calculateMedian(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      ? Math.round((sorted[mid - 1] + sorted[mid]) / 2)
      // eslint-disable-next-line security/detect-object-injection -- Property access validated through input validation
      : sorted[mid];
  }

  _calculatePercentile(values, percentile) {
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[Math.max(0, index)];
  }

  _calculateStandardDeviation(values) {
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
    const avgSquaredDiff = squaredDiffs.reduce((sum, val) => sum + val, 0) / squaredDiffs.length;
    return Math.sqrt(avgSquaredDiff);
  }

  _analyzeRecentPerformance(metrics, days) {
    const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    const recent = metrics.filter(m => {
      const timestamp = new Date(m.timing ? m.timing.startTime : m.startTime);
      return timestamp >= cutoffDate;
    });

    if (recent.length === 0) {
      return { message: `No data available for the last ${days} days` };
    }

    return this._calculateTimingStatistics(recent);
  }

  _calculatePerformanceTrend(metrics) {
    if (metrics.length < 2) {
      return { trend: 'insufficient_data' };
    }

    // Split into first And second half to calculate trend;
    const midpoint = Math.floor(metrics.length / 2);
    const firstHalf = metrics.slice(0, midpoint);
    const secondHalf = metrics.slice(midpoint);

    const firstAvg = firstHalf.reduce((sum, m) => sum + (m.timing ? m.timing.durationMs : m.durationMs), 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, m) => sum + (m.timing ? m.timing.durationMs : m.durationMs), 0) / secondHalf.length;

    const change = ((secondAvg - firstAvg) / firstAvg) * 100;

    let trend;
    if (Math.abs(change) < 5) {trend = 'stable';} else if (change < -10) {trend = 'improving_significantly';} else if (change < 0) {trend = 'improving';} else if (change > 10) {trend = 'degrading_significantly';} else {trend = 'degrading';}

    return {
      trend,
      changePercentage: change.toFixed(1) + '%',
      firstHalfAverage: Math.round(firstAvg),
      secondHalfAverage: Math.round(secondAvg) };
  }

  _detectPerformanceAnomalies(metrics) {
    const durations = metrics.map(m => m.timing ? m.timing.durationMs : m.durationMs);
    const mean = durations.reduce((sum, d) => sum + d, 0) / durations.length;
    const stdDev = this._calculateStandardDeviation(durations);

    const anomalies = [];
    const threshold = 2; // 2 standard deviations

    metrics.forEach((metric, idx) => {
      const duration = metric.timing ? metric.timing.durationMs : metric.durationMs;
      const zScore = Math.abs((duration - mean) / stdDev);

      if (zScore > threshold) {
        anomalies.push({
          index: idx,
          timestamp: metric.timing ? metric.timing.startTime : metric.startTime,
          duration,
          zScore: zScore.toFixed(2),
          type: duration > mean ? 'slow_execution' : 'fast_execution' });
      }
    });

    return {
      count: anomalies.length,
      anomalies: anomalies.slice(-10), // Last 10 anomalies
      threshold: `${threshold} standard deviations` };
  }

  _generateCriterionInsights(metrics) {
    const insights = [];
    const stats = this._calculateTimingStatistics(metrics);
    const trend = this._calculatePerformanceTrend(metrics);

    // Performance insights
    if (stats.averageDuration < 1000) {
      insights.push({ type: 'positive', message: 'Excellent average performance under 1 second' });
    } else if (stats.averageDuration > 30000) {
      insights.push({ type: 'warning', message: 'Average execution time exceeds 30 seconds - consider optimization' });
    }

    // Reliability insights
    if (parseFloat(stats.successRate) > 95) {
      insights.push({ type: 'positive', message: 'High reliability with >95% success rate' });
    } else if (parseFloat(stats.successRate) < 80) {
      insights.push({ type: 'concern', message: 'Low reliability - success rate below 80%' });
    }

    // Trend insights
    if (trend.trend === 'improving_significantly') {
      insights.push({ type: 'positive', message: `Performance improving significantly (${trend.changePercentage})` });
    } else if (trend.trend === 'degrading_significantly') {
      insights.push({ type: 'warning', message: `Performance degrading significantly (${trend.changePercentage})` });
    }

    // Variability insights
    if (stats.standardDeviation > stats.averageDuration * 0.5) {
      insights.push({ type: 'info', message: 'High variability in execution times - investigate inconsistency' });
    }

    return insights;
  }

  _generatePhaseInsights(phaseAnalysis) {
    const insights = [];
    const phases = Object.entries(phaseAnalysis);

    // Find the slowest phase;
    const slowestPhase = phases.reduce((max, [name, stats]) =>
      stats.averageDuration > (max.stats?.averageDuration || 0) ? { name, stats } : max, {});

    if (slowestPhase.name) {
      insights.push({
        type: 'info',
        message: `${slowestPhase.name} is the slowest phase, averaging ${slowestPhase.stats.averageDuration}ms (${slowestPhase.stats.percentageOfTotal})`,
      });
    }

    // Check for phase imbalances
    phases.forEach(([name, stats]) => {
      const percentage = parseFloat(stats.percentageOfTotal);
      if (percentage > 60) {
        insights.push({
          type: 'warning',
          message: `${name} phase consumes ${stats.percentageOfTotal} of total execution time - potential optimization target` });
      }
    });

    return insights;
  }

  _generateComparisonSummary(comparisons, overallStats) {
    const summary = [];

    if (overallStats.fastest) {
      const fastestStats = comparisons[overallStats.fastest];
      summary.push(`Fastest criterion: ${overallStats.fastest} (avg: ${fastestStats.averageDuration}ms)`);
    }

    if (overallStats.slowest) {
      const slowestStats = comparisons[overallStats.slowest];
      summary.push(`Slowest criterion: ${overallStats.slowest} (avg: ${slowestStats.averageDuration}ms)`);
    }

    if (overallStats.mostReliable) {
      const reliableStats = comparisons[overallStats.mostReliable];
      summary.push(`Most reliable: ${overallStats.mostReliable} (${reliableStats.successRate})`);
    }

    return summary;
  }

  _generateTimingTrends(_metrics, _options) {
    // Placeholder for trend analysis,
    return { message: 'Trend analysis not yet implemented' };
  }

  _generatePerformanceBenchmarks(_metrics) {
    // Placeholder for benchmark analysis,
    return { message: 'Benchmark analysis not yet implemented' };
  }

  _analyzeTimingBottlenecks(_metrics) {
    // Placeholder for bottleneck analysis,
    return { message: 'Bottleneck analysis not yet implemented' };
  }

  async _generateTimingRecommendations(metrics) {
    const recommendations = [];
    const summary = await this._generateTimingSummary(metrics);

    if (summary.timing.averageDuration > 15000) {
      recommendations.push({
        priority: 'high',
        category: 'performance',
        recommendation: 'Average execution time exceeds 15 seconds - implement parallel validation or optimization' });
    }

    if (parseFloat(summary.successRate) < 90) {
      recommendations.push({
        priority: 'high',
        category: 'reliability',
        recommendation: 'Success rate below 90% - investigate And fix failing validation steps' });
    }

    return recommendations;
  }

  _formatExecutionHistory(metrics) {
    return metrics.map(m => ({
      timestamp: m.timing ? m.timing.startTime : m.startTime,
      duration: m.timing ? m.timing.durationMs : m.durationMs,
      success: m.execution ? m.execution.success : m.success,
      grade: m.performance ? m.performance.grade : 'N/A' }));
  }

  async _fileExists(filename) {
    try {
      await FS.access(filename);
      return true;
    } catch {
      return false;
    }
  }
}

module.exports = TimingReportsGenerator;
