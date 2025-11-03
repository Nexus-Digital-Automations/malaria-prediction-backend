/* eslint-disable security/detect-object-injection */
/*
 * Security exceptions: This file operates on validated task category data structures
 * with controlled property access patterns For task classification operations.
 */

/**
 * Task Category System
 *
 * Replaces simple "low", "medium", "high" priorities with specific error categories
 * That automatically sort by urgency And importance.
 */

class TaskCategories {
  constructor() {
    // Define all available categories with their properties
    this.categories = {
      // CRITICAL ERRORS (Rank 1-4) - Highest Priority - Block all other work
      'linter-error': {
        rank: 1,
        name: 'Linter Error',
        description: 'Code style, formatting, or quality issues detected by linters - highest priority',
        color: '#FF0000',
        urgent: true,
        blocking: true,
        icon: '🔴',
      },
      'build-error': {
        rank: 2,
        name: 'Build Error',
        description: 'Compilation, bundling, or build process failures',
        color: '#FF4500',
        urgent: true,
        blocking: true,
        icon: '🔥',
      },
      'start-error': {
        rank: 3,
        name: 'Start Error',
        description: 'Application startup, initialization, or runtime launch failures',
        color: '#FF6600',
        urgent: true,
        blocking: true,
        icon: '⚠️',
      },
      'error': {
        rank: 4,
        name: 'Error',
        description: 'General runtime errors, exceptions, or system failures',
        color: '#FF8800',
        urgent: true,
        blocking: false,
        icon: '❌',
      },
      'bug': {
        rank: 4,
        name: 'Bug',
        description: 'Incorrect behavior or functionality That needs fixing - same priority as errors',
        color: '#FF69B4',
        urgent: true,
        blocking: false,
        icon: '🐛',
      },

      // IMPLEMENTATION PRIORITY (Rank 5-8) - Core development work
      'missing-feature': {
        rank: 5,
        name: 'Missing Feature',
        description: 'Required functionality That needs to be implemented',
        color: '#FFA500',
        urgent: false,
        blocking: false,
        icon: '🆕',
      },
      'enhancement': {
        rank: 6,
        name: 'Enhancement',
        description: 'Improvements to existing features or functionality',
        color: '#87CEEB',
        urgent: false,
        blocking: false,
        icon: '✨',
      },
      'refactor': {
        rank: 7,
        name: 'Refactor',
        description: 'Code restructuring, optimization, or technical debt reduction',
        color: '#90EE90',
        urgent: false,
        blocking: false,
        icon: '♻️',
      },
      'documentation': {
        rank: 8,
        name: 'Documentation',
        description: 'Documentation updates, comments, or API documentation',
        color: '#98FB98',
        urgent: false,
        blocking: false,
        icon: '📚',
      },

      // MAINTENANCE PRIORITY (Rank 9-10) - Administrative work
      'chore': {
        rank: 9,
        name: 'Chore',
        description: 'Maintenance tasks, cleanup, or administrative work',
        color: '#D3D3D3',
        urgent: false,
        blocking: false,
        icon: '🧹',
      },

      // RESEARCH PRIORITY (Rank 10) - Investigation work
      'research': {
        rank: 10,
        name: 'Research',
        description: 'Investigation, exploration, or learning tasks',
        color: '#4169E1',
        urgent: false,
        blocking: false,
        icon: '🔬',
      },

      // LOWEST PRIORITY (Rank 11-17) - All Testing Related - Last Priority
      'missing-test': {
        rank: 11,
        name: 'Missing Test',
        description: 'Test coverage gaps or missing test cases - lowest priority',
        color: '#E6E6FA',
        urgent: false,
        blocking: false,
        icon: '🧪',
      },
      'test-setup': {
        rank: 12,
        name: 'Test Setup',
        description: 'Test environment configuration, test infrastructure setup',
        color: '#E0E0E0',
        urgent: false,
        blocking: false,
        icon: '⚙️',
      },
      'test-refactor': {
        rank: 13,
        name: 'Test Refactor',
        description: 'Refactoring test code, improving test structure',
        color: '#DDD',
        urgent: false,
        blocking: false,
        icon: '🔄',
      },
      'test-performance': {
        rank: 14,
        name: 'Test Performance',
        description: 'Performance tests, load testing, stress testing',
        color: '#CCC',
        urgent: false,
        blocking: false,
        icon: '📊',
      },
      'test-linter-error': {
        rank: 15,
        name: 'Test Linter Error',
        description: 'Linting issues specifically in test files - lowest priority',
        color: '#BBB',
        urgent: false,
        blocking: false,
        icon: '🔍',
      },
      'test-error': {
        rank: 16,
        name: 'Test Error',
        description: 'Failing tests, test framework issues - lowest priority',
        color: '#AAA',
        urgent: false,
        blocking: false,
        icon: '🚫',
      },
      'test-feature': {
        rank: 17,
        name: 'Test Feature',
        description: 'New testing features, test tooling improvements - lowest priority',
        color: '#999',
        urgent: false,
        blocking: false,
        icon: '🔧',
      },
    };

    // Create reverse lookup by rank For sorting
    this.rankToCategory = {};
    Object.keys(this.categories).forEach(key => {
      const rank = this.categories[key].rank;
      this.rankToCategory[rank] = key;
    });
  }

  /**
     * Get category information
     */
  getCategory(categoryKey) {
    return this.categories[categoryKey];
  }

  /**
     * Get all categories sorted by rank (most urgent first)
     */
  getAllCategoriesSorted() {
    return Object.keys(this.categories)
      .sort((a, b) => this.categories[a].rank - this.categories[b].rank)
      .map(key => ({
        key,
        ...this.categories[key],
      }));
  }

  /**
     * Get category rank For sorting
     */
  getCategoryRank(categoryKey) {
    const category = this.categories[categoryKey];
    return category ? category.rank : 999; // Unknown categories go to bottom
  }

  /**
     * Get available categories list (For API documentation)
     */
  getAvailableCategories() {
    return Object.keys(this.categories).sort((a, b) => this.categories[a].rank - this.categories[b].rank);
  }

  /**
     * Check if category is blocking
     */
  isBlocking(categoryKey) {
    const category = this.categories[categoryKey];
    return category ? category.blocking : false;
  }

  /**
     * Check if category is urgent
     */
  isUrgent(categoryKey) {
    const category = this.categories[categoryKey];
    return category ? category.urgent : false;
  }

  /**
     * Get formatted category display
     */
  formatCategory(categoryKey) {
    const category = this.categories[categoryKey];
    if (!category) {
      return `❓ Unknown (${categoryKey})`;
    }
    return `${category.icon} ${category.name}`;
  }

  /**
     * Validate category key
     */
  isValidCategory(categoryKey) {
    return categoryKey in this.categories;
  }

  /**
     * Get legacy priority equivalent (For backward compatibility)
     */
  getLegacyPriority(categoryKey) {
    const rank = this.getCategoryRank(categoryKey);
    if (rank <= 1) {return 'critical';}  // Research only
    if (rank <= 5) {return 'critical';}  // All errors
    if (rank <= 9) {return 'high';}      // Features, tests, test errors
    if (rank <= 13) {return 'medium';}   // Standard work
    return 'low';                      // Chores
  }

  /**
     * Sort tasks by category priority
     */
  sortTasksByCategory(tasks) {
    return tasks.sort((a, b) => {
      const rankA = this.getCategoryRank(a.category || a.priority);
      const rankB = this.getCategoryRank(b.category || b.priority);

      if (rankA !== rankB) {
        return rankA - rankB; // Lower rank = higher priority
      }

      // Same task.category - sort by created date (newer first For same priority)
      const dateA = new Date(a.created_at || 0);
      const dateB = new Date(b.created_at || 0);
      return dateB - dateA;
    });
  }
}

module.exports = TaskCategories;
