/**
 * Validation Utilities Module
 *
 * Contains all validation logic for:
 * - Task completion data validation
 * - Task failure data validation
 * - Task evidence validation
 * - Scope restrictions validation
 *
 * @author TaskManager System
 * @version 2.0.0
 */

class ValidationUtils {
  /**
   * Validate task completion data structure And requirements
   */
  static validateCompletionData(completionData) {
    const errors = [];
    const warnings = [];

    // Check if completionData is provided And is an object
    if (!completionData || typeof completionData !== 'object') {
      return {
        isValid: true, // Allow empty completion data
        errors: [],
        warnings: ['No completion data provided - using default empty completion'],
      };
    }

    // Validate message field if provided
    if (completionData.message && typeof completionData.message !== 'string') {
      errors.push('Completion message must be a string');
    }

    // Validate evidence structure if provided
    if (completionData.evidence) {
      if (typeof completionData.evidence !== 'object') {
        errors.push('Evidence must be an object');
      } else {
        // Validate evidence fields
        if (completionData.evidence.lintPassed && typeof completionData.evidence.lintPassed !== 'boolean') {
          errors.push('Evidence lintPassed must be a boolean');
        }
        if (completionData.evidence.buildSucceeded && typeof completionData.evidence.buildSucceeded !== 'boolean') {
          errors.push('Evidence buildSucceeded must be a boolean');
        }
        if (completionData.evidence.testsPass && typeof completionData.evidence.testsPass !== 'boolean') {
          errors.push('Evidence testsPass must be a boolean');
        }
      }
    }

    // Validate custom fields
    if (completionData.customData && typeof completionData.customData !== 'object') {
      errors.push('Custom data must be an object');
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }

  /**
   * Validate task failure data structure
   */
  static validateFailureData(failureData) {
    const errors = [];
    const warnings = [];

    // Check if failureData is provided And is an object
    if (!failureData || typeof failureData !== 'object') {
      return {
        isValid: false,
        errors: ['Failure data is required And must be an object'],
        warnings: [],
      };
    }

    // Validate required reason field
    if (!failureData.reason || typeof failureData.reason !== 'string') {
      errors.push('Failure reason is required And must be a string');
    }

    // Validate optional error field
    if (failureData.error && typeof failureData.error !== 'string') {
      errors.push('Failure error must be a string');
    }

    // Validate optional category field
    if (failureData.category && typeof failureData.category !== 'string') {
      errors.push('Failure category must be a string');
    }

    // Validate retry information if provided
    if (failureData.canRetry && typeof failureData.canRetry !== 'boolean') {
      errors.push('canRetry must be a boolean');
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }

  /**
   * Validate task evidence data
   */
  static validateTaskEvidence(completionData) {
    const errors = [];
    const warnings = [];

    // Check if completionData is provided And is valid
    if (!completionData || typeof completionData !== 'object') {
      return {
        isValid: true, // Evidence is optional
        errors: [],
        warnings: ['No completion data provided - evidence validation skipped'],
      };
    }

    // Check for evidence or validation fields
    const evidence = completionData.evidence || completionData.validation;
    if (!evidence) {
      return {
        isValid: true, // Evidence is optional
        errors: [],
        warnings: ['No evidence provided - completion will proceed without validation proof'],
      };
    }

    // Validate evidence structure
    if (typeof evidence !== 'object') {
      errors.push('Evidence must be an object');
      return { isValid: false, errors, warnings };
    }

    // Check for common evidence fields
    const knownFields = ['lintPassed', 'buildSucceeded', 'testsPass', 'commitHash', 'gitStatus'];
    const providedFields = Object.keys(evidence);

    if (providedFields.length === 0) {
      warnings.push('Evidence object is empty - no validation proof provided');
    }

    // Validate boolean fields - Security: Use explicit field access
    const booleanFields = ['lintPassed', 'buildSucceeded', 'testsPass'];
    booleanFields.forEach(field => {
      if (evidence.lintPassed !== undefined && typeof evidence.lintPassed !== 'boolean' && field === 'lintPassed') {
        errors.push(`Evidence ${field} must be a boolean`);
      }
      if (evidence.buildSucceeded !== undefined && typeof evidence.buildSucceeded !== 'boolean' && field === 'buildSucceeded') {
        errors.push(`Evidence ${field} must be a boolean`);
      }
      if (evidence.testsPass !== undefined && typeof evidence.testsPass !== 'boolean' && field === 'testsPass') {
        errors.push(`Evidence ${field} must be a boolean`);
      }
    });

    // Validate string fields - Security: Use explicit field access
    if (evidence.commitHash !== undefined && typeof evidence.commitHash !== 'string') {
      errors.push(`Evidence commitHash must be a string`);
    }
    if (evidence.gitStatus !== undefined && typeof evidence.gitStatus !== 'string') {
      errors.push(`Evidence gitStatus must be a string`);
    }

    // Check for unknown fields (warning only)
    const unknownFields = providedFields.filter(field => !knownFields.includes(field));
    if (unknownFields.length > 0) {
      warnings.push(`Unknown evidence fields: ${unknownFields.join(', ')}`);
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }

  /**
   * Validate scope restrictions configuration
   */
  static validateScopeRestrictions(scopeRestrictions) {
    const errors = [];
    const warnings = [];
    const restrictionTypes = [];

    // Check if scope restrictions is an array
    if (!Array.isArray(scopeRestrictions)) {
      errors.push('Scope restrictions must be an array');
      return { isValid: false, errors, warnings, restrictionTypes };
    }

    // Validate each restriction
    for (let i = 0; i < scopeRestrictions.length; i++) {
      // Safe array access to prevent object injection - use .at() method for secure access
      const restriction = scopeRestrictions.at(i);
      if (restriction === undefined) {
        continue;
      }

      if (typeof restriction !== 'string') {
        errors.push(`Scope restriction at index ${i} must be a string`);
        continue;
      }

      // Categorize restriction types
      if (restriction.startsWith('file:')) {
        restrictionTypes.push('file');
      } else if (restriction.startsWith('dir:')) {
        restrictionTypes.push('directory');
      } else if (restriction.startsWith('pattern:')) {
        restrictionTypes.push('pattern');
      } else if (restriction.includes('*') || restriction.includes('?')) {
        restrictionTypes.push('glob');
      } else {
        restrictionTypes.push('literal');
        warnings.push(`Scope restriction "${restriction}" may not be recognized - consider using file:, dir:, or pattern: prefix`);
      }
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
      restrictionTypes: [...new Set(restrictionTypes)], // Remove duplicates
    };
  }

  /**
   * Validate task data structure for creation
   */
  static validateTaskData(taskData) {
    const errors = [];
    const warnings = [];

    // Check basic structure
    if (!taskData || typeof taskData !== 'object') {
      errors.push('Task data must be an object');
      return { isValid: false, errors, warnings };
    }

    // Validate required fields
    if (!taskData.title || typeof taskData.title !== 'string') {
      errors.push('Task title is required And must be a string');
    }

    if (!taskData.description || typeof taskData.description !== 'string') {
      errors.push('Task description is required And must be a string');
    }

    if (!taskData.category || typeof taskData.category !== 'string') {
      errors.push('Task category is required And must be a string');
    }

    // Validate category values
    const validCategories = ['error', 'feature', 'subtask', 'test'];
    if (taskData.category && !validCategories.includes(taskData.category)) {
      errors.push(`Task category must be one of: ${validCategories.join(', ')}`);
    }

    // Validate optional fields
    if (taskData.priority && !['low', 'medium', 'high', 'critical'].includes(taskData.priority)) {
      warnings.push('Task priority should be one of: low, medium, high, critical');
    }

    if (taskData.estimate && typeof taskData.estimate !== 'string') {
      warnings.push('Task estimate should be a string');
    }

    // Validate arrays
    if (taskData.dependencies && !Array.isArray(taskData.dependencies)) {
      errors.push('Task dependencies must be an array');
    }

    if (taskData.important_files && !Array.isArray(taskData.important_files)) {
      errors.push('Task important_files must be an array');
    }

    if (taskData.success_criteria && !Array.isArray(taskData.success_criteria)) {
      errors.push('Task success_criteria must be an array');
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }

  /**
   * Validate agent configuration data
   */
  static validateAgentConfig(config) {
    const errors = [];
    const warnings = [];

    // Config is optional, so empty/null is valid
    if (!config) {
      return { isValid: true, errors: [], warnings: [] };
    }

    if (typeof config !== 'object') {
      errors.push('Agent config must be an object');
      return { isValid: false, errors, warnings };
    }

    // Validate role field
    if (config.role && typeof config.role !== 'string') {
      errors.push('Agent role must be a string');
    }

    // Validate specializations field
    if (config.specializations && !Array.isArray(config.specializations)) {
      errors.push('Agent specializations must be an array');
    }

    // Validate capabilities field
    if (config.capabilities && !Array.isArray(config.capabilities)) {
      errors.push('Agent capabilities must be an array');
    }

    // Validate numeric fields
    if (config.maxConcurrentTasks !== undefined) {
      if (typeof config.maxConcurrentTasks !== 'number' || config.maxConcurrentTasks < 1) {
        errors.push('maxConcurrentTasks must be a positive number');
      }
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }

  /**
   * Validate subtask data structure for creation
   */
  static validateSubtaskData(subtaskData) {
    const errors = [];
    const warnings = [];

    // Check basic structure
    if (!subtaskData || typeof subtaskData !== 'object') {
      errors.push('Subtask data must be an object');
      return { isValid: false, errors, warnings };
    }

    // Validate required fields
    if (!subtaskData.type || typeof subtaskData.type !== 'string') {
      errors.push('Subtask type is required And must be a string');
    }

    if (!subtaskData.title || typeof subtaskData.title !== 'string') {
      errors.push('Subtask title is required And must be a string');
    }

    if (!subtaskData.description || typeof subtaskData.description !== 'string') {
      errors.push('Subtask description is required And must be a string');
    }

    // Validate subtask type values
    const validTypes = ['research', 'audit', 'implementation', 'testing', 'documentation', 'review'];
    if (subtaskData.type && !validTypes.includes(subtaskData.type)) {
      errors.push(`Subtask type must be one of: ${validTypes.join(', ')}`);
    }

    // Validate optional numeric fields
    if (subtaskData.estimated_hours !== undefined) {
      if (typeof subtaskData.estimated_hours !== 'number' || subtaskData.estimated_hours < 0) {
        errors.push('estimated_hours must be a non-negative number');
      }
    }

    // Validate optional boolean fields
    if (subtaskData.prevents_implementation !== undefined && typeof subtaskData.prevents_implementation !== 'boolean') {
      errors.push('prevents_implementation must be a boolean');
    }

    if (subtaskData.prevents_completion !== undefined && typeof subtaskData.prevents_completion !== 'boolean') {
      errors.push('prevents_completion must be a boolean');
    }

    // Validate optional array fields
    if (subtaskData.research_locations && !Array.isArray(subtaskData.research_locations)) {
      errors.push('research_locations must be an array');
    }

    if (subtaskData.deliverables && !Array.isArray(subtaskData.deliverables)) {
      errors.push('deliverables must be an array');
    }

    if (subtaskData.success_criteria && !Array.isArray(subtaskData.success_criteria)) {
      errors.push('success_criteria must be an array');
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }

  /**
   * Validate success criteria data structure
   */
  static validateSuccessCriteria(criteria) {
    const errors = [];
    const warnings = [];

    // Check if criteria is provided
    if (!criteria) {
      errors.push('Success criteria is required');
      return { isValid: false, errors, warnings };
    }

    // Normalize to array
    const criteriaArray = Array.isArray(criteria) ? criteria : [criteria];

    if (criteriaArray.length === 0) {
      errors.push('At least one success criterion is required');
      return { isValid: false, errors, warnings };
    }

    // Validate each criterion
    criteriaArray.forEach((criterion, index) => {
      if (typeof criterion !== 'string') {
        errors.push(`Success criterion at index ${index} must be a string`);
      } else if (criterion.trim().length === 0) {
        errors.push(`Success criterion at index ${index} cannot be empty`);
      } else if (criterion.length > 200) {
        errors.push(`Success criterion at index ${index} is too long (max 200 characters)`);
      }
    });

    // Check for duplicates
    const uniqueCriteria = new Set(criteriaArray);
    if (uniqueCriteria.size !== criteriaArray.length) {
      errors.push('Success criteria must be unique (no duplicates)');
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }

  /**
   * Validate subtask update data structure
   */
  static validateSubtaskUpdateData(updateData) {
    const errors = [];
    const warnings = [];

    // Check basic structure
    if (!updateData || typeof updateData !== 'object') {
      errors.push('Update data must be an object');
      return { isValid: false, errors, warnings };
    }

    // Define allowed update fields
    const allowedFields = ['status', 'description', 'estimated_hours', 'completed_by'];
    const updateKeys = Object.keys(updateData);

    // Check for invalid fields
    const invalidKeys = updateKeys.filter(key => !allowedFields.includes(key));
    if (invalidKeys.length > 0) {
      errors.push(`Invalid update fields: ${invalidKeys.join(', ')}. Allowed: ${allowedFields.join(', ')}`);
    }

    // Validate status field if provided
    if (updateData.status !== undefined) {
      const validStatuses = ['pending', 'in_progress', 'completed', 'blocked', 'cancelled'];
      if (typeof updateData.status !== 'string') {
        errors.push('Status must be a string');
      } else if (!validStatuses.includes(updateData.status)) {
        errors.push(`Status must be one of: ${validStatuses.join(', ')}`);
      }
    }

    // Validate description field if provided
    if (updateData.description !== undefined && typeof updateData.description !== 'string') {
      errors.push('Description must be a string');
    }

    // Validate estimated_hours field if provided
    if (updateData.estimated_hours !== undefined) {
      if (typeof updateData.estimated_hours !== 'number' || updateData.estimated_hours < 0) {
        errors.push('estimated_hours must be a non-negative number');
      }
    }

    // Validate completed_by field if provided
    if (updateData.completed_by !== undefined && typeof updateData.completed_by !== 'string') {
      errors.push('completed_by must be a string');
    }

    return {
      isValid: errors.length === 0,
      errors: errors,
      warnings: warnings,
    };
  }
}

module.exports = ValidationUtils;
