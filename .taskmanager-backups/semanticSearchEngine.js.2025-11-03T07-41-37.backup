/**
 * Semantic Search Engine for RAG System
 *
 * === OVERVIEW ===
 * Advanced semantic search engine That provides intelligent query processing,
 * context-aware ranking, And specialized search capabilities for technical
 * content retrieval with emphasis on code patterns And development lessons.
 *
 * === KEY FEATURES ===
 * • Intelligent query enhancement And preprocessing
 * • Context-aware semantic similarity search
 * • Multi-stage ranking with relevance scoring
 * • Specialized error pattern matching
 * • Query expansion And synonym handling
 * • Performance-optimized caching And indexing
 *
 * === TECHNICAL ARCHITECTURE ===
 * Search pipeline combining:
 * • Query Processor: Intent detection, preprocessing, expansion
 * • Semantic Matcher: Embedding-based similarity computation
 * • Ranking Engine: Multi-factor relevance scoring
 * • Result Enhancer: Context injection And metadata enrichment
 * • Cache Manager: Query result caching And optimization
 *
 * @author RAG Implementation Agent
 * @version 1.0.0
 * @since 2025-09-19
 */

const LOGGER = require('../logger');

/**
 * Advanced Semantic Search Engine for Technical Content
 */
class SemanticSearchEngine {
  constructor(config = {}) {
    this.config = {
      // Core components (injected)
      embeddingGenerator: config.embeddingGenerator,
      vectorDatabase: config.vectorDatabase,

      // Search parameters
      defaultTopK: config.defaultTopK || 10,
      similarityThreshold: config.similarityThreshold || 0.75,
      maxQueryLength: config.maxQueryLength || 512,

      // Query processing
      enableQueryExpansion: config.enableQueryExpansion !== false,
      enableSynonymMatching: config.enableSynonymMatching !== false,
      enableIntentDetection: config.enableIntentDetection !== false,

      // Ranking And filtering
      enableMultiStageRanking: config.enableMultiStageRanking !== false,
      enableContextualRanking: config.enableContextualRanking !== false,
      diversityWeight: config.diversityWeight || 0.2,

      // Performance
      enableQueryCaching: config.enableQueryCaching !== false,
      cacheSize: config.cacheSize || 1000,
      enableParallelSearch: config.enableParallelSearch !== false,

      // Error search enhancements
      enableErrorPatternMatching: config.enableErrorPatternMatching !== false,
      errorSimilarityBoost: config.errorSimilarityBoost || 0.1,

      ...config,
    };

    this.logger = new LOGGER('SemanticSearchEngine');
    this.isInitialized = false;

    // Query cache
    this.queryCache = new Map();

    // Performance tracking
    this.stats = {
      queriesProcessed: 0,
      averageQueryTime: 0,
      cacheHits: 0,
      cacheMisses: 0,
      expandedQueries: 0,
      reRankingEnabled: this.config.enableMultiStageRanking,
    };

    // Technical synonyms for query expansion
    this.technicalSynonyms = {
      'error': ['exception', 'failure', 'issue', 'problem', 'bug'],
      'function': ['method', 'procedure', 'routine', 'operation'],
      'variable': ['parameter', 'argument', 'field', 'property'],
      'class': ['object', 'type', 'structure', 'component'],
      'import': ['require', 'include', 'load', 'dependency'],
      'export': ['expose', 'provide', 'return', 'output'],
      'async': ['asynchronous', 'promise', 'await', 'concurrent'],
      'sync': ['synchronous', 'blocking', 'sequential'],
      'api': ['endpoint', 'service', 'interface', 'rest'],
      'database': ['db', 'storage', 'persistence', 'data'],
      'performance': ['optimization', 'speed', 'efficiency', 'fast'],
      'security': ['auth', 'authentication', 'authorization', 'access'],
      'test': ['testing', 'spec', 'validation', 'verification'],
      'build': ['compile', 'bundle', 'package', 'deploy'],
      'debug': ['debugging', 'troubleshoot', 'diagnose', 'fix'],
    };

    // Query intent patterns
    this.intentPatterns = {
      error_search: /error|exception|failed|broken|not working|issue|problem|bug/i,
      how_to: /how to|how do|how can|what is the way|best way/i,
      best_practice: /best practice|recommended|should|proper way|correct/i,
      troubleshooting: /troubleshoot|debug|diagnose|solve|fix|resolve/i,
      implementation: /implement|create|build|develop|add|make/i,
      optimization: /optimize|improve|faster|better|efficient|performance/i,
      configuration: /config|configure|setup|install|environment/i,
      comparison: /compare|difference|vs|versus|alternative|between/i,
    };
  }

  /**
   * Initialize the semantic search engine
   * @returns {Promise<boolean>} Initialization success
   */
  async initialize() {
    try {
      this.logger.info('Initializing semantic search engine...');

      // Validate required components
      if (!this.config.embeddingGenerator) {
        throw new Error('Embedding generator is required');
      }

      if (!this.config.vectorDatabase) {
        throw new Error('Vector database is required');
      }

      // Verify components are initialized
      if (!this.config.embeddingGenerator.isInitialized) {
        this.logger.info('Initializing embedding generator...');
        await this.config.embeddingGenerator.initialize();
      }

      if (!this.config.vectorDatabase.isInitialized) {
        this.logger.info('Initializing vector database...');
        await this.config.vectorDatabase.initialize();
      }

      this.isInitialized = true;
      this.logger.info('Semantic search engine initialized successfully');

      return true;

    } catch (error) {
      this.logger.error('Failed to initialize semantic search engine', { error: error.message });
      throw error;
    }
  }

  /**
   * Perform semantic search for lessons And knowledge
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @returns {Promise<Array<Object>>} Search results
   */
  async search(query, options = {}) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    const startTime = Date.now();

    try {
      this.logger.debug(`Performing semantic search: "${query.substring(0, 50)}..."`);

      // Check cache first
      const cacheKey = this._generateCacheKey(query, options);
      if (this.config.enableQueryCaching && this.queryCache.has(cacheKey)) {
        this.stats.cacheHits++;
        return this.queryCache.get(cacheKey);
      }

      // Process And enhance query
      const processedQuery = await this._processQuery(query, options);

      // Generate query embedding
      const queryEmbedding = await this.config.embeddingGenerator.generateEmbeddings(processedQuery);

      // Perform vector search
      const searchOptions = this._prepareSearchOptions(options);
      const rawResults = await this.config.vectorDatabase.search(queryEmbedding, searchOptions);

      // Enhance And rank results
      const enhancedResults = await this._enhanceResults(rawResults, query, options);

      // Cache results
      if (this.config.enableQueryCaching) {
        this._cacheResults(cacheKey, enhancedResults);
      }

      // Update statistics
      this._updateStats(startTime);
      this.stats.cacheMisses++;

      this.logger.debug(`Search completed in ${Date.now() - startTime}ms`, {
        resultsCount: enhancedResults.length,
        processedQuery: processedQuery.substring(0, 50),
      });

      return enhancedResults;

    } catch (error) {
      this.logger.error('Semantic search failed', { error: error.message, query });
      throw error;
    }
  }

  /**
   * Specialized search for error patterns And solutions
   * @param {string} errorDescription - Error description
   * @param {Object} options - Search options
   * @returns {Promise<Array<Object>>} Error-focused search results
   */
  async searchErrors(errorDescription, options = {}) {
    try {
      this.logger.debug(`Searching for similar errors: "${errorDescription.substring(0, 50)}..."`);

      // Enhance error description for better matching
      const enhancedQuery = this._enhanceErrorQuery(errorDescription);

      // Configure error-specific search options
      const errorOptions = {
        ...options,
        contentTypes: ['error'],
        enableErrorPatternMatching: true,
        similarityThreshold: options.similarityThreshold || (this.config.similarityThreshold - 0.1),
        topK: options.topK || this.config.defaultTopK,
        enableContextualRanking: true,
      };

      // Perform search with error-specific enhancements
      const results = await this.search(enhancedQuery, errorOptions);

      // Apply error-specific post-processing
      const errorResults = this._processErrorResults(results, errorDescription);

      this.logger.info(`Found ${errorResults.length} similar errors`, {
        withResolutions: errorResults.filter(r => r.resolution).length,
      });

      return errorResults;

    } catch (error) {
      this.logger.error('Error search failed', { error: error.message });
      throw error;
    }
  }

  /**
   * Get contextual recommendations based on task information
   * @param {Object} taskContext - Current task context
   * @param {Object} options - Recommendation options
   * @returns {Promise<Array<Object>>} Contextual recommendations
   */
  async getContextualRecommendations(taskContext, options = {}) {
    try {
      this.logger.debug('Generating contextual recommendations', {
        taskId: taskContext.id,
        taskCategory: taskContext.task.category,
      });

      // Generate context-aware query
      const contextQuery = this._generateContextQuery(taskContext);

      // Configure context-specific search
      const contextOptions = {
        ...options,
        currentTask: taskContext,
        enableContextualRanking: true,
        similarityThreshold: options.threshold || (this.config.similarityThreshold - 0.15),
        topK: options.maxResults || this.config.defaultTopK,
        preferredContentTypes: this._getPreferredContentTypes(taskContext.task.category),
      };

      // Perform contextual search
      const recommendations = await this.search(contextQuery, contextOptions);

      // Apply context-specific ranking
      const rankedRecommendations = this._rankByContext(recommendations, taskContext);

      this.logger.info(`Generated ${rankedRecommendations.length} contextual recommendations`);

      return rankedRecommendations;

    } catch (error) {
      this.logger.error('Contextual recommendation failed', { error: error.message });
      throw error;
    }
  }

  // =================== PRIVATE HELPER METHODS ===================

  /**
   * Process And enhance the search query
   * @param {string} query - Raw query
   * @param {Object} options - Processing options
   * @returns {string} Processed query
   * @private
   */
  _processQuery(query, _options) {
    let processedQuery = query.trim();

    // Basic preprocessing
    processedQuery = this._preprocessQuery(processedQuery);

    // Detect query intent
    if (this.config.enableIntentDetection) {
      const intent = this._detectQueryIntent(processedQuery);
      if (intent && intent !== 'general') {
        processedQuery = this._enhanceQueryByIntent(processedQuery, intent);
      }
    }

    // Expand query with synonyms
    if (this.config.enableQueryExpansion) {
      processedQuery = this._expandQuery(processedQuery);
      this.stats.expandedQueries++;
    }

    // Limit query length
    if (processedQuery.length > this.config.maxQueryLength) {
      processedQuery = processedQuery.substring(0, this.config.maxQueryLength);
    }

    return processedQuery;
  }

  /**
   * Basic query preprocessing
   * @param {string} query - Query to preprocess
   * @returns {string} Preprocessed query
   * @private
   */
  _preprocessQuery(query) {
    return query
      .toLowerCase()
      .replace(/[^\w\s-]/g, ' ') // Remove special characters except hyphens
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  }

  /**
   * Detect query intent from patterns
   * @param {string} query - Query to analyze
   * @returns {string} Detected intent
   * @private
   */
  _detectQueryIntent(query) {
    for (const [intent, pattern] of Object.entries(this.intentPatterns)) {
      if (pattern.test(query)) {
        return intent;
      }
    }
    return 'general';
  }

  /**
   * Enhance query based on detected intent
   * @param {string} query - Original query
   * @param {string} intent - Detected intent
   * @returns {string} Enhanced query
   * @private
   */
  _enhanceQueryByIntent(query, intent) {
    const intentEnhancements = {
      error_search: 'error resolution problem solution fix',
      how_to: 'implementation guide tutorial example',
      best_practice: 'best practice recommended approach pattern',
      troubleshooting: 'debug troubleshoot solve diagnose',
      implementation: 'implement create build develop code',
      optimization: 'optimize improve performance efficient',
      configuration: 'configuration setup install environment',
      comparison: 'compare difference alternative option',
    };

    // eslint-disable-next-line security/detect-object-injection -- Accessing known intent keys for query enhancement in semantic search;
    const enhancement = intentEnhancements[intent];
    return enhancement ? `${query} ${enhancement}` : query;
  }

  /**
   * Expand query with technical synonyms
   * @param {string} query - Query to expand
   * @returns {string} Expanded query
   * @private
   */
  _expandQuery(query) {
    let expandedQuery = query;
    const words = query.split(' ');

    for (const word of words) {
      // eslint-disable-next-line security/detect-object-injection -- Accessing known technical synonym keys for query expansion
      if (this.technicalSynonyms[word]) {
        // Add the most relevant synonym (first one)
        // eslint-disable-next-line security/detect-object-injection -- Accessing known technical synonym arrays for query expansion
        expandedQuery += ` ${this.technicalSynonyms[word][0]}`;
      }
    }

    return expandedQuery;
  }

  /**
   * Enhance error query for better pattern matching
   * @param {string} errorDescription - Error description
   * @returns {string} Enhanced error query
   * @private
   */
  _enhanceErrorQuery(errorDescription) {
    let enhanced = errorDescription;

    // Extract error type And message
    const errorType = this._extractErrorType(errorDescription);
    const errorMessage = this._extractErrorMessage(errorDescription);

    // Add error-specific terms
    enhanced += ' error exception failure issue problem';

    // Add extracted components
    if (errorType) {
      enhanced += ` ${errorType}`;
    }

    if (errorMessage) {
      enhanced += ` ${errorMessage}`;
    }

    return enhanced;
  }

  /**
   * Extract error type from description
   * @param {string} description - Error description
   * @returns {string} Error type
   * @private
   */
  _extractErrorType(description) {
    const typePatterns = [
      /(syntaxerror|typeerror|referenceerror|rangeerror)/i,
      /error[:\s]+([^\n]+)/i,
      /type[:\s]+([^\n]+)/i,
    ];

    for (const pattern of typePatterns) {
      const match = description.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    return '';
  }

  /**
   * Extract error message from description
   * @param {string} description - Error description
   * @returns {string} Error message
   * @private
   */
  _extractErrorMessage(description) {
    const messagePatterns = [
      /message[:\s]+([^\n]+)/i,
      /"([^"]+)"/g, // Quoted strings
      /'([^']+)'/g, // Single quoted strings
    ];

    const messages = [];

    for (const pattern of messagePatterns) {
      let _match;
      while ((_match = pattern.exec(description)) !== null) {
        if (_match[1] && _match[1].trim()) {
          messages.push(_match[1].trim());
        }
      }
    }

    return messages.join(' ');
  }

  /**
   * Prepare search options for vector database
   * @param {Object} options - Original options
   * @returns {Object} Prepared search options
   * @private
   */
  _prepareSearchOptions(options) {
    return {
      topK: Math.min(options.topK || this.config.defaultTopK, 100),
      similarityThreshold: options.similarityThreshold || this.config.similarityThreshold,
      contentTypes: options.contentTypes || null,
      filters: options.filters || {},
      enableReranking: this.config.enableMultiStageRanking,
      ...options,
    };
  }

  /**
   * Enhance search results with additional metadata And scoring
   * @param {Array<Object>} rawResults - Raw search results
   * @param {string} originalQuery - Original query
   * @param {Object} options - Search options
   * @returns {Array<Object>} Enhanced results
   * @private
   */
  _enhanceResults(rawResults, originalQuery, options) {
    const enhancedResults = rawResults.map(result => {
      // Add relevance scoring
      const relevanceScore = this._calculateRelevanceScore(result, originalQuery, options);

      // Add content analysis
      const contentAnalysis = this._analyzeContent(result);

      // Add context information
      const contextInfo = this._extractContextInfo(result, options);
      return {
        ...result,
        relevanceScore,
        contentAnalysis,
        contextInfo,
        searchQuery: originalQuery,
        enhancedAt: new Date().toISOString(),
      };
    });

    // Apply multi-stage ranking if enabled
    if (this.config.enableMultiStageRanking) {
      return this._applyMultiStageRanking(enhancedResults, originalQuery, options);
    }

    return enhancedResults;
  }

  /**
   * Calculate relevance score for a result
   * @param {Object} result - Search result
   * @param {string} query - Original query
   * @param {Object} options - Search options
   * @returns {number} Relevance score (0-1)
   * @private
   */
  _calculateRelevanceScore(result, query, options) {
    let score = result.similarity || 0;

    // Boost for exact keyword matches in title
    if (result.title) {
      const titleWords = result.title.toLowerCase().split(' ');
      const queryWords = query.toLowerCase().split(' ');
      const titleMatches = queryWords.filter(word => titleWords.includes(word)).length;
      score += (titleMatches / queryWords.length) * 0.1;
    }

    // Boost for content type preference
    if (options.preferredContentTypes && options.preferredContentTypes.includes(result.content_type)) {
      score += 0.05;
    }

    // Recency boost
    if (result.created_at) {
      const age = Date.now() - new Date(result.created_at).getTime();
      const ageInDays = age / (1000 * 60 * 60 * 24);
      score += Math.exp(-ageInDays / 30) * 0.05; // Decay over 30 days
    }

    // Quality indicators boost
    if (result.resolution && result.resolution.length > 100) {
      score += 0.03; // Boost for detailed resolutions
    }

    if (result.tags && result.tags.length > 0) {
      score += 0.02; // Boost for well-tagged content
    }

    return Math.min(score, 1.0);
  }

  /**
   * Analyze content characteristics
   * @param {Object} result - Search result
   * @returns {Object} Content analysis
   * @private
   */
  _analyzeContent(result) {
    return {
      hasResolution: !!result.resolution,
      hasPreventionStrategy: !!result.prevention_strategy,
      contentLength: (result.description || '').length,
      tagCount: (result.tags || []).length,
      isRecent: this._isRecentContent(result.created_at),
      contentType: result.content_type,
      qualityScore: this._assessContentQuality(result),
    };
  }

  /**
   * Check if content is recent
   * @param {string} createdAt - Creation date
   * @returns {boolean} Whether content is recent
   * @private
   */
  _isRecentContent(createdAt) {
    if (!createdAt) {return false;}

    const age = Date.now() - new Date(createdAt).getTime();
    const ageInDays = age / (1000 * 60 * 60 * 24);
    return ageInDays <= 30; // Consider content recent if within 30 days
  }

  /**
   * Assess content quality
   * @param {Object} result - Search result
   * @returns {number} Quality score (0-1)
   * @private
   */
  _assessContentQuality(result) {
    let score = 0.5; // Base score

    // Content completeness
    if (result.description && result.description.length > 50) {score += 0.2;}
    if (result.resolution && result.resolution.length > 100) {score += 0.2;}
    if (result.prevention_strategy) {score += 0.1;}

    // Metadata richness
    if (result.tags && result.tags.length >= 2) {score += 0.1;}
    if (result.source_path) {score += 0.05;}

    // Error-specific quality indicators
    if (result.content_type === 'error') {
      if (result.error_type) {score += 0.05;}
      if (result.stack_trace) {score += 0.05;}
    }

    return Math.min(score, 1.0);
  }

  /**
   * Extract context information for result
   * @param {Object} result - Search result
   * @param {Object} options - Search options
   * @returns {Object} Context information
   * @private
   */
  _extractContextInfo(result, options) {
    return {
      isContextual: !!options.currentTask,
      taskCategory: options.currentTask?.category,
      preferredType: options.preferredContentTypes?.includes(result.content_type),
      matchingTags: this._getMatchingTags(result, options.currentTask),
      applicabilityScore: options.currentTask ? this._assessApplicability(result, options.currentTask) : 0.5,
    };
  }

  /**
   * Get matching tags between result And current task
   * @param {Object} result - Search result
   * @param {Object} currentTask - Current task
   * @returns {Array<string>} Matching tags
   * @private
   */
  _getMatchingTags(result, currentTask) {
    if (!currentTask || !result.tags || !currentTask.tags) {
      return [];
    }

    return result.tags.filter(tag => currentTask.tags.includes(tag));
  }

  /**
   * Assess result applicability to current task
   * @param {Object} result - Search result
   * @param {Object} currentTask - Current task
   * @returns {number} Applicability score (0-1)
   * @private
   */
  _assessApplicability(result, currentTask) {
    let score = 0.5; // Base applicability

    // Category match
    if (result.content_type === currentTask.category) {
      score += 0.3;
    }

    // Tag overlap
    const matchingTags = this._getMatchingTags(result, currentTask);
    if (matchingTags.length > 0) {
      score += (matchingTags.length / Math.max(result.tags.length, 1)) * 0.2;
    }

    // Content similarity (basic keyword matching)
    if (result.description && currentTask.description) {
      const resultWords = result.description.toLowerCase().split(' ');
      const taskWords = currentTask.description.toLowerCase().split(' ');
      const commonWords = resultWords.filter(word => word.length > 3 && taskWords.includes(word));
      score += (commonWords.length / Math.max(taskWords.length, 1)) * 0.2;
    }

    return Math.min(score, 1.0);
  }

  /**
   * Apply multi-stage ranking to results
   * @param {Array<Object>} results - Results to rank
   * @param {string} query - Original query
   * @param {Object} options - Search options
   * @returns {Array<Object>} Re-ranked results
   * @private
   */
  _applyMultiStageRanking(results, query, options) {
    // Stage 1: Semantic similarity (already applied)

    // Stage 2: Content quality And completeness
    results.forEach(result => {
      result.qualityScore = result.contentAnalysis.qualityScore;
    });

    // Stage 3: Contextual relevance
    if (options.currentTask) {
      results.forEach(result => {
        result.contextualScore = result.contextInfo.applicabilityScore;
      });
    }

    // Stage 4: Diversity factor (avoid too similar results)
    if (this.config.diversityWeight > 0) {
      results = this._applyDiversityFilter(results);
    }

    // Final combined scoring
    results.forEach(result => {
      const weights = {
        similarity: 0.4,
        relevance: 0.3,
        quality: 0.2,
        contextual: 0.1,
      };

      result.finalScore =
        (result.similarity * weights.similarity) +
        (result.relevanceScore * weights.relevance) +
        (result.qualityScore * weights.quality) +
        ((result.contextualScore || 0.5) * weights.contextual);
    });

    // Sort by final score
    return results.sort((a, b) => b.finalScore - a.finalScore);
  }

  /**
   * Apply diversity filter to avoid redundant results
   * @param {Array<Object>} results - Results to diversify
   * @returns {Array<Object>} Diversified results
   * @private
   */
  _applyDiversityFilter(results) {
    const diversified = [];
    const seenTitles = new Set();
    const seenContentHashes = new Set();

    for (const result of results) {
      const titleSimilarity = this._findMostSimilarTitle(result.title, seenTitles);
      const isUnique = titleSimilarity < 0.8 && !seenContentHashes.has(result.content_hash);

      if (isUnique || diversified.length < 3) { // Always include top 3
        diversified.push(result);
        seenTitles.add(result.title);
        seenContentHashes.add(result.content_hash);
      }
    }

    return diversified;
  }

  /**
   * Find most similar title in a set
   * @param {string} title - Title to compare
   * @param {Set<string>} titleSet - Set of existing titles
   * @returns {number} Highest similarity score
   * @private
   */
  _findMostSimilarTitle(title, titleSet) {
    let maxSimilarity = 0;

    for (const existingTitle of titleSet) {
      const similarity = this._calculateStringSimilarity(title, existingTitle);
      maxSimilarity = Math.max(maxSimilarity, similarity);
    }

    return maxSimilarity;
  }

  /**
   * Calculate string similarity (simple Jaccard similarity)
   * @param {string} str1 - First string
   * @param {string} str2 - Second string
   * @returns {number} Similarity score (0-1)
   * @private
   */
  _calculateStringSimilarity(str1, str2) {
    if (!str1 || !str2) {return 0;}

    const words1 = new Set(str1.toLowerCase().split(' '));
    const words2 = new Set(str2.toLowerCase().split(' '));

    const intersection = new Set([...words1].filter(word => words2.has(word)));
    const union = new Set([...words1, ...words2]);

    return intersection.size / union.size;
  }

  /**
   * Process error-specific search results
   * @param {Array<Object>} results - Raw search results
   * @param {string} errorDescription - Original error description
   * @returns {Array<Object>} Processed error results
   * @private
   */
  _processErrorResults(results, _errorDescription) {
    return results.map(result => {
      // Add error-specific enhancements
      const errorEnhancement = {
        errorSimilarity: result.similarity + this.config.errorSimilarityBoost,
        hasResolution: !!result.resolution,
        resolutionQuality: this._assessResolutionQuality(result.resolution),
        errorComplexity: this._assessErrorComplexity(result),
        preventionAvailable: !!result.prevention_strategy,
      };

      return {
        ...result,
        errorEnhancement,
      };
    });
  }

  /**
   * Assess resolution quality
   * @param {string} resolution - Resolution text
   * @returns {string} Quality assessment
   * @private
   */
  _assessResolutionQuality(resolution) {
    if (!resolution) {return 'none';}

    if (resolution.length < 50) {return 'basic';}
    if (resolution.length < 200) {return 'good';}
    if (resolution.length >= 200) {return 'detailed';}

    return 'unknown';
  }

  /**
   * Assess error complexity
   * @param {Object} errorResult - Error result
   * @returns {string} Complexity level
   * @private
   */
  _assessErrorComplexity(errorResult) {
    let complexity = 0;

    if (errorResult.stack_trace && errorResult.stack_trace.length > 500) {complexity++;}
    if (errorResult.error_message && /multiple|chain|cascade/i.test(errorResult.error_message)) {complexity++;}
    if (/system|kernel|memory|resource/i.test(errorResult.error_type || '')) {complexity++;}
    if (!errorResult.resolution) {complexity++;}

    if (complexity >= 3) {return 'high';}
    if (complexity >= 2) {return 'medium';}
    if (complexity >= 1) {return 'low';}
    return 'trivial';
  }

  /**
   * Generate context query from task information
   * @param {Object} taskContext - Task context
   * @returns {string} Context query
   * @private
   */
  _generateContextQuery(taskContext) {
    const parts = [
      taskContext.title || '',
      taskContext.description || '',
      taskContext.task.category || '',
      (taskContext.tags || []).join(' '),
    ];

    return parts.filter(part => part.trim()).join(' ').trim();
  }

  /**
   * Get preferred content types for a task category
   * @param {string} category - Task category
   * @returns {Array<string>} Preferred content types
   * @private
   */
  _getPreferredContentTypes(category) {
    const mapping = {
      'error': ['error', 'patterns'],
      'feature': ['features', 'patterns', 'decisions'],
      'optimization': ['optimization', 'patterns'],
      'test': ['patterns', 'features'],
      'refactoring': ['patterns', 'optimization', 'decisions'],
    };

    // eslint-disable-next-line security/detect-object-injection -- Accessing known category keys for content type mapping
    return mapping[category] || ['features', 'patterns', 'optimization', 'decisions'];
  }

  /**
   * Rank results by task context
   * @param {Array<Object>} results - Results to rank
   * @param {Object} taskContext - Task context
   * @returns {Array<Object>} Context-ranked results
   * @private
   */
  _rankByContext(results, taskContext) {
    return results.map(result => {
      const contextScore = this._assessApplicability(result, taskContext);
      result.contextualRelevance = contextScore;
      result.combinedContextScore = (result.relevanceScore * 0.6) + (contextScore * 0.4);
      return result;
    }).sort((a, b) => b.combinedContextScore - a.combinedContextScore);
  }

  /**
   * Generate cache key for query And options
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @returns {string} Cache key
   * @private
   */
  _generateCacheKey(query, options) {
    const CRYPTO = require('crypto');
    const cacheInput = JSON.stringify({
      query: query.trim().toLowerCase(),
      contentTypes: options.contentTypes,
      topK: options.topK,
      similarityThreshold: options.similarityThreshold,
      filters: options.filters,
    });

    return CRYPTO.createHash('md5').update(cacheInput).digest('hex');
  }

  /**
   * Cache search results
   * @param {string} key - Cache key
   * @param {Array<Object>} results - Results to cache
   * @private
   */
  _cacheResults(key, results) {
    if (this.queryCache.size >= this.config.cacheSize) {
      // Remove oldest entry (LRU)
      const firstKey = this.queryCache.keys().next().value;
      this.queryCache.delete(firstKey);
    }

    this.queryCache.set(key, results);
  }

  /**
   * Update performance statistics
   * @param {number} startTime - Query start time
   * @private
   */
  _updateStats(startTime) {
    this.stats.queriesProcessed++;
    const queryTime = Date.now() - startTime;

    const avgTime = this.stats.averageQueryTime;
    const totalQueries = this.stats.queriesProcessed;
    this.stats.averageQueryTime = ((avgTime * (totalQueries - 1)) + queryTime) / totalQueries;
  }

  /**
   * Get search engine statistics
   * @returns {Object} Statistics object
   */
  getStatistics() {
    return {
      ...this.stats,
      isInitialized: this.isInitialized,
      cacheSize: this.queryCache.size,
      cacheHitRate: this.stats.cacheHits / (this.stats.cacheHits + this.stats.cacheMisses + 1),
      configuredFeatures: {
        queryExpansion: this.config.enableQueryExpansion,
        intentDetection: this.config.enableIntentDetection,
        multiStageRanking: this.config.enableMultiStageRanking,
        errorPatternMatching: this.config.enableErrorPatternMatching,
      },
    };
  }

  /**
   * Clear query cache
   */
  clearCache() {
    this.queryCache.clear();
    this.stats.cacheHits = 0;
    this.stats.cacheMisses = 0;
    this.logger.info('Search cache cleared');
  }

  /**
   * Cleanup search engine resources
   */
  cleanup() {
    try {
      this.clearCache();
      this.isInitialized = false;
      this.logger.info('Semantic search engine cleanup completed');
    } catch (error) {
      this.logger.error('Search engine cleanup failed', { error: error.message });
    }
  }
}

module.exports = SemanticSearchEngine;
