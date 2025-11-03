
/**
 * Embedding Generation System for RAG Implementation
 *
 * === OVERVIEW ===
 * Advanced embedding generation system optimized for technical content, code,
 * And development lessons. Provides semantic understanding of code patterns,
 * technical documentation, And error scenarios for intelligent retrieval.
 *
 * === KEY FEATURES ===
 * • Code-optimized embedding models for technical content understanding
 * • Multi-modal content processing (code + documentation + errors)
 * • Batch processing capabilities for efficient large-scale processing
 * • Semantic preprocessing for improved embedding quality
 * • Context-aware embedding generation based on content type
 * • Performance optimization with caching And model reuse
 *
 * === TECHNICAL ARCHITECTURE ===
 * Built on Transformers.js for client-side ML inference:
 * • Primary Model: microsoft/codebert-base (code understanding)
 * • Fallback Model: sentence-transformers/all-MiniLM-L6-v2 (general text)
 * • Custom preprocessing pipeline for technical content
 * • Embedding dimension: 768 (CodeBERT) / 384 (MiniLM)
 * • Support for incremental processing And batching
 *
 * @author RAG Implementation Agent
 * @version 1.0.0
 * @since 2025-09-19
 */

const { pipeline, env } = require('@xenova/transformers');
const LOGGER = require('../logger');

// Configure transformers environment for offline usage
env.allowRemoteModels = true;
env.allowLocalModels = true;

/**
 * Advanced Embedding Generator for Technical Content
 */
class EmbeddingGenerator {
  constructor(config = {}) {
    this.config = {
      // Model configuration
      primaryModel: 'microsoft/codebert-base',
      fallbackModel: 'sentence-transformers/all-MiniLM-L6-v2',
      embeddingDimension: 768,

      // Performance settings
      batchSize: 32,
      maxTextLength: 512,
      enableCaching: true,
      cacheSize: 1000,

      // Content processing
      enablePreprocessing: true,
      preserveCodeStructure: true,
      enableContextualEmbedding: true,

      // Timeouts And retries
      modelLoadTimeout: 60000,
      embeddingTimeout: 30000,
      maxRetries: 3,

      ...config,
    };

    this.logger = new LOGGER('EmbeddingGenerator');
    this.models = new Map();
    this.cache = new Map();
    this.isInitialized = false;
    this.stats = {
      embeddingsGenerated: 0,
      cacheHits: 0,
      cacheMisses: 0,
      averageProcessingTime: 0,
      modelSwitches: 0,
    };

    // Content type detection patterns
    this.contentPatterns = {
      code: /(?:function|class|const|let|var|import|export|if|for|while|try|catch)/i,
      error: /(?:error|exception|failed|undefined|null|cannot|invalid|syntax)/i,
      api: /(?:endpoint|route|request|response|http|api|rest|graphql)/i,
      config: /(?:config|settings|environment|env|package\.json|\.env)/i,
      documentation: /(?:readme|docs|guide|tutorial|example|usage)/i,
    };
  }

  /**
   * Initialize the embedding system with model loading
   * @returns {Promise<boolean>} Success status
   */
  async initialize() {
    try {
      this.logger.info('Initializing embedding generation system...');
      const startTime = Date.now();

      // Load primary model (CodeBERT for code understanding)
      this.logger.info(`Loading primary model: ${this.config.primaryModel}`);
      try {
        const primaryModel = await this._loadModel(this.config.primaryModel, 'feature-extraction');
        this.models.set('primary', primaryModel);
        this.logger.info('Primary model loaded successfully');
      } catch (primaryError) {
        this.logger.warn(`Primary model failed to load: ${primaryError.message}`);
        this.logger.info('Falling back to secondary model...');

        // Fallback to general text model
        const fallbackModel = await this._loadModel(this.config.fallbackModel, 'feature-extraction');
        this.models.set('primary', fallbackModel);
        this.config.embeddingDimension = 384; // MiniLM dimension
        this.stats.modelSwitches++;
      }

      const loadTime = Date.now() - startTime;
      this.logger.info(`Model loading completed in ${loadTime}ms`);

      this.isInitialized = true;
      return true;

    } catch (error) {
      this.logger.error('Failed to initialize embedding system', { error: error.message });
      throw error;
    }
  }

  /**
   * Load a specific model with timeout handling
   * @param {string} modelName - Model identifier
   * @param {string} task - Task type (feature-extraction)
   * @returns {Promise<Object>} Loaded model pipeline
   * @private
   */
  _loadModel(modelName, task) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Model loading timeout after ${this.config.modelLoadTimeout}ms`));
      }, this.config.modelLoadTimeout);

      pipeline(task, modelName)
        .then(model => {
          clearTimeout(timeout);
          resolve(model);
        })
        .catch(error => {
          clearTimeout(timeout);
          reject(error);
        });
    });
  }

  /**
   * Generate embeddings for technical content with context awareness
   * @param {string|Array<string>} content - Content to embed
   * @param {Object} options - Generation options
   * @returns {Promise<Array<number>|Array<Array<number>>>} Embedding vectors
   */
  async generateEmbeddings(content, options = {}) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    const startTime = Date.now();
    const isArray = Array.isArray(content);
    const contents = isArray ? content : [content];
    try {
      this.logger.debug(`Generating embeddings for ${contents.length} items`);

      const results = [];
      const primaryModel = this.models.get('primary');

      // Process batches concurrently for better performance;
      const batchPromises = [];
      for (let i = 0; i < contents.length; i += this.config.batchSize) {
        const batch = contents.slice(i, i + this.config.batchSize);
        batchPromises.push(this._processBatch(batch, primaryModel, options));
      }

      const batchResults = await Promise.all(batchPromises);
      batchResults.forEach(batchResult => results.push(...batchResult));

      const processingTime = Date.now() - startTime;
      this._updateStats(contents.length, processingTime);

      this.logger.debug(`Generated ${results.length} embeddings in ${processingTime}ms`);

      return isArray ? results : results[0];

    } catch (error) {
      this.logger.error('Embedding generation failed', {
        error: error.message,
        contentCount: contents.length,
      });
      throw error;
    }
  }

  /**
   * Process a batch of content for embedding generation
   * @param {Array<string>} batch - Content batch
   * @param {Object} model - ML model pipeline
   * @param {Object} options - Processing options
   * @returns {Promise<Array<Array<number>>>} Batch embeddings
   * @private
   */
  _processBatch(batch, model, options) {
    // Process batch items concurrently for better performance
    const contentPromises = batch.map(async (content) => {
      try {
        // Check cache first
        const cacheKey = this._generateCacheKey(content, options);
        if (this.config.enableCaching && this.cache.has(cacheKey)) {
          this.stats.cacheHits++;
          return this.cache.get(cacheKey);
        }

        // Preprocess content for better embeddings
        const processedContent = this.config.enablePreprocessing
          ? this._preprocessContent(content, options)
          : content;

        // Generate embedding with timeout
        const embedding = await this._generateSingleEmbedding(processedContent, model);

        // Cache result
        if (this.config.enableCaching) {
          this._cacheEmbedding(cacheKey, embedding);
        }

        this.stats.cacheMisses++;
        return embedding;

      } catch (error) {
        this.logger.warn(`Failed to generate embedding for content: ${error.message}`);
        // Return zero vector as fallback
        return new Array(this.config.embeddingDimension).fill(0);
      }
    });

    return Promise.all(contentPromises);
  }

  /**
   * Generate single embedding with timeout protection
   * @param {string} content - Preprocessed content
   * @param {Object} model - ML model pipeline
   * @returns {Promise<Array<number>>} Embedding vector
   * @private
   */
  _generateSingleEmbedding(content, model) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Embedding generation timeout after ${this.config.embeddingTimeout}ms`));
      }, this.config.embeddingTimeout);

      model(content, { pooling: 'mean', normalize: true })
        .then(result => {
          clearTimeout(timeout);
          // Extract embedding array from result
          const embedding = result.data ? Array.from(result.data) : Array.from(result);
          resolve(embedding);
        })
        .catch(error => {
          clearTimeout(timeout);
          reject(error);
        });
    });
  }

  /**
   * Preprocess content for optimal embedding generation
   * @param {string} content - Raw content
   * @param {Object} options - Processing options
   * @returns {string} Preprocessed content
   * @private
   */
  _preprocessContent(content, _options = {}) {
    if (!content || typeof content !== 'string') {
      return '';
    }

    let processed = content;

    // Detect content type for specialized processing;
    const contentType = this._detectContentType(content);

    // Apply content-type specific preprocessing
    switch (contentType) {
      case 'code':
        processed = this._preprocessCode(processed);
        break;
      case 'error':
        processed = this._preprocessError(processed);
        break;
      case 'api':
        processed = this._preprocessAPI(processed);
        break;
      case 'config':
        processed = this._preprocessConfig(processed);
        break;
      default:
        processed = this._preprocessGeneral(processed);
    }

    // Apply length limits
    if (processed.length > this.config.maxTextLength) {
      processed = this._truncateIntelligently(processed, contentType);
    }

    return processed;
  }

  /**
   * Detect content type for specialized processing
   * @param {string} content - Content to analyze
   * @returns {string} Detected content type
   * @private
   */
  _detectContentType(content) {
    for (const [type, pattern] of Object.entries(this.contentPatterns)) {
      if (pattern.test(content)) {
        return type;
      }
    }
    return 'general';
  }

  /**
   * Preprocess code content for better embeddings
   * @param {string} content - Code content
   * @returns {string} Processed code
   * @private
   */
  _preprocessCode(content) {
    if (!this.config.preserveCodeStructure) {
      return content;
    }

    // Normalize whitespace while preserving structure
    return content
      .replace(/\r\n/g, '\n')
      .replace(/\t/g, '  ')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  /**
   * Preprocess error content for better semantic understanding
   * @param {string} content - Error content
   * @returns {string} Processed error content
   * @private
   */
  _preprocessError(content) {
    // Extract key error information And stack traces
    return content
      .replace(/\s+at\s+[\w./\\:]+/g, ' [stack]') // Normalize stack traces
      .replace(/\b\d+:\d+\b/g, '[line:col]') // Normalize line numbers
      .replace(/\bfile:\/\/.*?\b/g, '[filepath]') // Normalize file paths
      .trim();
  }

  /**
   * Preprocess API content for endpoint understanding
   * @param {string} content - API content
   * @returns {string} Processed API content
   * @private
   */
  _preprocessAPI(content) {
    // Normalize API routes And HTTP methods
    return content
      .replace(/\b(GET|POST|PUT|DELETE|PATCH)\b/gi, method => method.toUpperCase())
      .replace(/\/api\/v\d+/g, '/api/[version]')
      .trim();
  }

  /**
   * Preprocess configuration content
   * @param {string} content - Config content
   * @returns {string} Processed config content
   * @private
   */
  _preprocessConfig(content) {
    // Normalize configuration values while preserving structure
    return content
      .replace(/"[^"]*"/g, '"[value]"') // Normalize string values
      .replace(/:\s*\d+/g, ': [number]') // Normalize numeric values
      .trim();
  }

  /**
   * Preprocess general content
   * @param {string} content - General content
   * @returns {string} Processed content
   * @private
   */
  _preprocessGeneral(content) {
    // Basic text normalization
    return content
      .replace(/\s+/g, ' ')
      .replace(/[^\w\s\-_.,;:()[\]{}]/g, '')
      .trim();
  }

  /**
   * Intelligently truncate content while preserving semantic meaning
   * @param {string} content - Content to truncate
   * @param {string} contentType - Type of content
   * @returns {string} Truncated content
   * @private
   */
  _truncateIntelligently(content, contentType) {
    const maxLength = this.config.maxTextLength;

    if (content.length <= maxLength) {
      return content;
    }

    // Try to truncate at natural boundaries
    const truncated = content.substring(0, maxLength);

    // for code, try to end at a complete line
    if (contentType === 'code') {
      const lastNewline = truncated.lastIndexOf('\n');
      if (lastNewline > maxLength * 0.8) {
        return truncated.substring(0, lastNewline);
      }
    }

    // for other content, try to end at a sentence
    const lastSentence = truncated.lastIndexOf('.');
    if (lastSentence > maxLength * 0.8) {
      return truncated.substring(0, lastSentence + 1);
    }

    // Fallback to word boundary
    const lastSpace = truncated.lastIndexOf(' ');
    if (lastSpace > maxLength * 0.8) {
      return truncated.substring(0, lastSpace);
    }

    return truncated;
  }

  /**
   * Generate cache key for embedding caching
   * @param {string} content - Content to cache
   * @param {Object} options - Caching options
   * @returns {string} Cache key
   * @private
   */
  _generateCacheKey(content, options) {
    const CRYPTO = require('crypto');
    const optionsHash = JSON.stringify(options);
    return CRYPTO.createHash('md5')
      .update(content + optionsHash)
      .digest('hex');
  }

  /**
   * Cache embedding result with LRU eviction
   * @param {string} key - Cache key
   * @param {Array<number>} embedding - Embedding to cache
   * @private
   */
  _cacheEmbedding(key, embedding) {
    if (this.cache.size >= this.config.cacheSize) {
      // Remove oldest entry (LRU)
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, embedding);
  }

  /**
   * Update performance statistics
   * @param {number} itemCount - Number of items processed
   * @param {number} processingTime - Processing time in ms
   * @private
   */
  _updateStats(itemCount, processingTime) {
    this.stats.embeddingsGenerated += itemCount;
    const avgTime = this.stats.averageProcessingTime;
    const totalProcessed = this.stats.embeddingsGenerated;
    this.stats.averageProcessingTime =
      ((avgTime * (totalProcessed - itemCount)) + processingTime) / totalProcessed;
  }

  /**
   * Get embedding system statistics
   * @returns {Object} Performance statistics
   */
  getStatistics() {
    return {
      ...this.stats,
      cacheHitRate: this.stats.cacheHits / (this.stats.cacheHits + this.stats.cacheMisses),
      isInitialized: this.isInitialized,
      embeddingDimension: this.config.embeddingDimension,
      modelsLoaded: this.models.size,
    };
  }

  /**
   * Clear the embedding cache
   */
  clearCache() {
    this.cache.clear();
    this.logger.info('Embedding cache cleared');
  }

  /**
   * Cleanup resources And models
   */
  cleanup() {
    try {
      this.clearCache();
      this.models.clear();
      this.isInitialized = false;
      this.logger.info('Embedding generator cleanup completed');
    } catch (error) {
      this.logger.error('Error during cleanup', { error: error.message });
    }
  }
}

module.exports = EmbeddingGenerator;
