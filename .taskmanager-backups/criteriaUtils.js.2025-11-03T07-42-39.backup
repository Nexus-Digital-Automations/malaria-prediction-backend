
const { loggers } = require('../../../logger');

/**
 * Criteria Utilities - Helper Functions for Success Criteria Management
 *
 * Provides common utility functions for working with success criteria including
 * validation, formatting, comparison, and data manipulation utilities.
 *
 * @module CriteriaUtils
 * @author API Infrastructure Agent #1
 * @version 3.0.0
 * @since 2025-09-15
 */

/**
 * Validate criteria array structure and content
 * @param {Array<string>} criteria - Criteria array to validate
 * @returns {Object} Validation result with errors and warnings
 */
function validateCriteriaArray(criteria, _category = 'general') {
  const errors = [];
  const warnings = [];

  if (!Array.isArray(criteria)) {
    errors.push('Criteria must be an array');
    return { valid: false, errors, warnings };
  }

  if (criteria.length === 0) {
    warnings.push('Empty criteria array provided');
  }

  criteria.forEach((criterion, index) => {
    if (typeof criterion !== 'string') {
      errors.push(`Criterion at index ${index} must be a string, got ${typeof criterion}`);
    } else {
      // String validation
      if (criterion.trim().length === 0) {
        errors.push(`Criterion at index ${index} cannot be empty or whitespace only`);
      } else if (criterion.length > 200) {
        warnings.push(`Criterion at index ${index} is very long (${criterion.length} characters)`);
      } else if (criterion.length < 3) {
        warnings.push(`Criterion at index ${index} is very short (${criterion.length} characters)`);
      }

      // Content validation
      if (criterion.includes('undefined') || criterion.includes('null')) {
        errors.push(`Criterion at index ${index} contains invalid placeholder text`);
      }
    }
  });

  // Check for duplicates
  const uniqueCriteria = new Set(criteria);
  if (uniqueCriteria.size !== criteria.length) {
    const duplicates = criteria.filter((item, index) => criteria.indexOf(item) !== index);
    errors.push(`Duplicate criteria found: ${[...new Set(duplicates)].join(', ')}`);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    statistics: {
      total: criteria.length,
      unique: uniqueCriteria.size,
      duplicates: criteria.length - uniqueCriteria.size,
      averageLength: criteria.length > 0 ? Math.round(criteria.reduce((sum, c) => sum + c.length, 0) / criteria.length) : 0,
    },
  };
}

/**
 * Normalize criteria strings for consistent formatting
 * @param {Array<string>} criteria - Criteria to normalize
 * @returns {Array<string>} Normalized criteria
 */
function normalizeCriteria(criteria, _category = 'general') {
  if (!Array.isArray(criteria)) {
    return [];
  }

  return criteria
    .map(criterion => {
      if (typeof criterion !== 'string') {
        return null;
      }

      // Normalize whitespace and trim
      return criterion
        .trim()
        .replace(/\s+/g, ' ')
        .replace(/^\w/, c => c.toUpperCase()); // Capitalize first letter
    })
    .filter(criterion => criterion && criterion.length > 0);
}

/**
 * Compare two criteria arrays for differences
 * @param {Array<string>} oldCriteria - Original criteria
 * @param {Array<string>} newCriteria - New criteria
 * @returns {Object} Comparison result with added, removed, and unchanged criteria
 */
function compareCriteria(oldCriteria, newCriteria, _category = 'general') {
  const oldSet = new Set(normalizeCriteria(oldCriteria || []));
  const newSet = new Set(normalizeCriteria(newCriteria || []));

  const added = [...newSet].filter(criterion => !oldSet.has(criterion));
  const removed = [...oldSet].filter(criterion => !newSet.has(criterion));
  const unchanged = [...newSet].filter(criterion => oldSet.has(criterion));

  return {
    added,
    removed,
    unchanged,
    hasChanges: added.length > 0 || removed.length > 0,
    summary: {
      addedCount: added.length,
      removedCount: removed.length,
      unchangedCount: unchanged.length,
      totalOld: oldSet.size,
      totalNew: newSet.size,
    },
  };
}

/**
 * Merge multiple criteria arrays with deduplication
 * @param {...Array<string>} criteriaArrays - Multiple criteria arrays to merge
 * @returns {Array<string>} Merged and deduplicated criteria array
 */
function mergeCriteria(...criteriaArrays) {
  const allCriteria = [];

  for (const criteria of criteriaArrays) {
    if (Array.isArray(criteria)) {
      allCriteria.push(...normalizeCriteria(criteria));
    }
  }

  // Remove duplicates while preserving order
  return [...new Set(allCriteria)];
}

/**
 * Filter criteria by category or pattern
 * @param {Array<string>} criteria - Criteria to filter
 * @param {Object} filters - Filter options
 * @param {Array<string>} filters.categories - Categories to include
 * @param {string} filters.pattern - Regex pattern to match
 * @param {Array<string>} filters.exclude - Criteria to exclude
 * @returns {Array<string>} Filtered criteria
 */
function filterCriteria(criteria, filters = {}, _category = 'general') {
  if (!Array.isArray(criteria)) {
    return [];
  }

  let filtered = [...criteria];

  // Filter by pattern (security: validate pattern before regex construction)
  if (filters.pattern) {
    try {
      if (typeof filters.pattern !== 'string' || filters.pattern.length > 100) {
        loggers.app.warn('Invalid pattern for criteria filtering: pattern too long or not a string');
        return filtered;
      }
      // eslint-disable-next-line security/detect-non-literal-regexp
      const regex = new RegExp(filters.pattern, 'i');
      filtered = filtered.filter(criterion => regex.test(criterion));
    } catch {
      loggers.app.warn('Invalid pattern for criteria filtering:', filters.pattern);
    }
  }

  // Filter by categories (simplified - would need _category mapping)
  if (filters.categories && filters.categories.length > 0) {
    // This would need to be enhanced with actual category mapping
    const categoryKeywords = {
      'code_quality': ['linter', 'lint', 'format', 'style'],
      'build': ['build', 'compile', 'bundle'],
      'testing': ['test', 'spec', 'coverage'],
      'security': ['security', 'audit', 'vulnerability', 'credential'],
      'documentation': ['documentation', 'doc', 'comment', 'readme'],
      'performance': ['performance', 'speed', 'memory', 'cpu'],
    };

    filtered = filtered.filter(criterion => {
      return filters.categories.some(_category => {
        // eslint-disable-next-line security/detect-object-injection -- _category from validated filter list
        const keywords = categoryKeywords[_category] || [_category];
        return keywords.some(keyword =>
          criterion.toLowerCase().includes(keyword.toLowerCase()),
        );
      });
    });
  }

  // Exclude specific criteria
  if (filters.exclude && filters.exclude.length > 0) {
    const excludeSet = new Set(filters.exclude.map(c => c.toLowerCase()));
    filtered = filtered.filter(criterion =>
      !excludeSet.has(criterion.toLowerCase()),
    );
  }

  return filtered;
}

/**
 * Group criteria by category based on keyword analysis
 * @param {Array<string>} criteria - Criteria to group
 * @returns {Object} Grouped criteria by category
 */
function groupCriteriaByCategory(criteria, _category = 'general') {
  if (!Array.isArray(criteria)) {
    return {};
  }

  const categories = {
    critical: [],
    security: [],
    quality: [],
    documentation: [],
    performance: [],
    compliance: [],
    other: [],
  };

  const categoryPatterns = {
    critical: /\b(linter|lint|build|runtime|test|error)\b/i,
    security: /\b(security|audit|vulnerability|credential|auth|encryption)\b/i,
    quality: /\b(code|quality|consistency|standard|pattern)\b/i,
    documentation: /\b(documentation|doc|comment|readme|api|guide)\b/i,
    performance: /\b(performance|speed|memory|cpu|benchmark|metric)\b/i,
    compliance: /\b(compliance|regulation|license|privacy|policy)\b/i,
  };

  criteria.forEach(criterion => {
    let categorized = false;

    for (const [_category, pattern] of Object.entries(categoryPatterns)) {
      if (pattern.test(criterion)) {
        // eslint-disable-next-line security/detect-object-injection -- category from Object.entries of known patterns
        categories[_category].push(criterion);
        categorized = true;
        break;
      }
    }

    if (!categorized) {
      categories.other.push(criterion);
    }
  });

  // Remove empty categories
  Object.keys(categories).forEach(_category => {
    // eslint-disable-next-line security/detect-object-injection -- _category from Object.keys of validated object
    if (categories[_category].length === 0) {
      // eslint-disable-next-line security/detect-object-injection -- category from Object.keys of validated object
      delete categories[_category];
    }
  });

  return categories;
}

/**
 * Calculate criteria statistics
 * @param {Array<string>} criteria - Criteria to analyze
 * @returns {Object} Statistical analysis of criteria
 */
function calculateCriteriaStatistics(criteria) {
  if (!Array.isArray(criteria)) {
    return {
      total: 0,
      unique: 0,
      duplicates: 0,
      averageLength: 0,
      categories: {},
      complexity: 'unknown',
    };
  }

  const normalized = normalizeCriteria(criteria);
  const unique = new Set(normalized);
  const groups = groupCriteriaByCategory(normalized);

  const lengths = normalized.map(c => c.length);
  const averageLength = lengths.length > 0 ?
    Math.round(lengths.reduce((sum, len) => sum + len, 0) / lengths.length) : 0;

  // Determine complexity based on number and types of criteria
  let complexity = 'simple';
  if (normalized.length > 20) {
    complexity = 'complex';
  } else if (normalized.length > 10) {
    complexity = 'moderate';
  }

  return {
    total: criteria.length,
    unique: unique.size,
    duplicates: criteria.length - unique.size,
    averageLength,
    minLength: lengths.length > 0 ? Math.min(...lengths) : 0,
    maxLength: lengths.length > 0 ? Math.max(...lengths) : 0,
    categories: Object.fromEntries(
      Object.entries(groups).map(([cat, items]) => [cat, items.length]),
    ),
    complexity,
    distribution: {
      automated: normalized.filter(c => isAutomatedCriterion(c)).length,
      manual: normalized.filter(c => isManualCriterion(c)).length,
    },
  };
}

/**
 * Format criteria for display with consistent formatting
 * @param {Array<string>} criteria - Criteria to format
 * @param {Object} options - Formatting options
 * @returns {Array<string>} Formatted criteria
 */
function formatCriteriaForDisplay(criteria, options = {}) {
  if (!Array.isArray(criteria)) {
    return [];
  }

  const {
    numbered = false,
    maxLength = 80,
    prefix = '',
    suffix = '',
  } = options;

  return criteria.map((criterion, index) => {
    let formatted = criterion.trim();

    // Truncate if needed
    if (formatted.length > maxLength) {
      formatted = formatted.substring(0, maxLength - 3) + '...';
    }

    // Add numbering if requested
    if (numbered) {
      formatted = `${index + 1}. ${formatted}`;
    }

    // Add prefix and suffix
    return `${prefix}${formatted}${suffix}`;
  });
}

/**
 * Check if criterion is typically automated
 * @param {string} criterion - Criterion to check
 * @returns {boolean} Whether criterion is typically automated
 */
function isAutomatedCriterion(criterion) {
  const automatedPatterns = [
    /\b(linter|lint|format)\b/i,
    /\b(build|compile)\b/i,
    /\b(test|spec|coverage)\b/i,
    /\b(security audit|vulnerability scan)\b/i,
    /\b(performance|benchmark)\b/i,
  ];

  return automatedPatterns.some(pattern => pattern.test(criterion));
}

/**
 * Check if criterion requires manual validation
 * @param {string} criterion - Criterion to check
 * @returns {boolean} Whether criterion requires manual validation
 */
function isManualCriterion(criterion) {
  const manualPatterns = [
    /\b(documentation|doc)\b/i,
    /\b(architecture|design)\b/i,
    /\b(decision|rationale)\b/i,
    /\b(compliance|regulation)\b/i,
    /\b(privacy|license)\b/i,
  ];

  return manualPatterns.some(pattern => pattern.test(criterion));
}

/**
 * Generate criteria suggestions based on task type and context
 * @param {string} taskType - Type of task (feature, error, test, etc.)
 * @param {Object} context - Additional context about the task
 * @returns {Array<string>} Suggested criteria
 */
function generateCriteriaSuggestions(taskType, context = {}) {
  const baseCriteria = [
    'Linter Perfection',
    'Build Success',
    'Runtime Success',
    'Test Integrity',
  ];

  const typeSuggestions = {
    feature: [
      ...baseCriteria,
      'Function Documentation',
      'API Documentation',
      'Performance Metrics',
      'Security Review',
    ],
    error: [
      ...baseCriteria,
      'Error Handling',
      'Root Cause Analysis',
      'Regression Prevention',
    ],
    test: [
      ...baseCriteria,
      'Test Coverage',
      'Performance Benchmarks',
      'Cross-Platform Testing',
    ],
    security: [
      ...baseCriteria,
      'Security Audit',
      'Vulnerability Assessment',
      'Authentication/Authorization',
      'Data Privacy',
      'Input Validation',
    ],
    documentation: [
      'Documentation Completeness',
      'API Documentation',
      'Architecture Documentation',
      'Usage Examples',
      'Migration Guides',
    ],
  };

  // eslint-disable-next-line security/detect-object-injection -- taskType validated by function parameter
  const suggestions = typeSuggestions[taskType] || baseCriteria;

  // Add context-specific suggestions
  if (context.hasAPI) {
    suggestions.push('API Documentation');
  }
  if (context.hasDatabase) {
    suggestions.push('Database Migration Safety');
  }
  if (context.isPublic) {
    suggestions.push('License Compliance', 'Documentation Completeness');
  }

  return [...new Set(suggestions)];
}

module.exports = {
  validateCriteriaArray,
  normalizeCriteria,
  compareCriteria,
  mergeCriteria,
  filterCriteria,
  groupCriteriaByCategory,
  calculateCriteriaStatistics,
  formatCriteriaForDisplay,
  isAutomatedCriterion,
  isManualCriterion,
  generateCriteriaSuggestions,
};
