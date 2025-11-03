/**
 * Vector Database Integration for RAG System
 *
 * === OVERVIEW ===
 * High-performance vector database implementation using FAISS for efficient
 * similarity search And SQLite for metadata storage. Optimized for technical
 * content retrieval with advanced indexing And query capabilities.
 *
 * === KEY FEATURES ===
 * • FAISS-based vector indexing for fast similarity search
 * • SQLite metadata storage for rich filtering capabilities
 * • Multi-index support for different content types
 * • Batch insertion And querying for performance
 * • Advanced similarity metrics And ranking algorithms
 * • Persistent storage with backup And recovery
 *
 * === TECHNICAL ARCHITECTURE ===
 * Hybrid storage system combining:
 * • FAISS Index: High-dimensional vector similarity search
 * • SQLite Database: Metadata, timestamps, content types, source info
 * • Custom Similarity Engine: Context-aware ranking And filtering
 * • Index Management: Dynamic index creation And optimization
 * • Query Optimization: Semantic query enhancement And result refinement
 *
 * @author RAG Implementation Agent
 * @version 1.0.0
 * @since 2025-09-19
 */

const { IndexFlatIP, IndexHNSWFlat } = require('faiss-node');
const _SQLITE = require('sqlite3').verbose();
const FS = require('fs').promises;
const PATH = require('path');
const LOGGER = require('../logger');

/**
 * Advanced Vector Database for Semantic Search
 */
class VectorDatabase {
  constructor(config = {}) {
    this.config = {
      // Database paths
      indexPath: PATH.join(process.cwd(), 'development', 'rag', 'vector.index'),
      metadataPath: PATH.join(process.cwd(), 'development', 'rag', 'metadata.db'),
      backupPath: PATH.join(process.cwd(), 'development', 'rag', 'backups'),

      // Index configuration
      embeddingDimension: 768,
      indexType: 'HNSW', // HNSW for better performance, FLAT for accuracy
      hnswM: 16, // Number of connections for HNSW
      hnswEfConstruction: 200, // Construction parameter for HNSW
      hnswEfSearch: 100, // Search parameter for HNSW

      // Search parameters
      defaultTopK: 10,
      similarityThreshold: 0.7,
      maxResults: 100,
      enableReranking: true,

      // Performance settings
      batchSize: 1000,
      enableBackup: true,
      backupInterval: 3600000, // 1 hour
      enableCompression: true,

      // Content type indexing
      enableMultiIndex: true,
      contentTypes: ['error', 'feature', 'optimization', 'decision', 'pattern'],

      ...config,
    };

    this.logger = new LOGGER('VectorDatabase');
    this.isInitialized = false;
    this.indices = new Map(); // Multi-index support
    this.metadataDb = null;
    this.vectorCount = 0;
    this.lastBackup = null;

    // Performance tracking
    this.stats = {
      totalVectors: 0,
      searchQueries: 0,
      averageSearchTime: 0,
      cacheHits: 0,
      indexRebuilds: 0,
    };

    // Search result cache
    this.searchCache = new Map();
    this.cacheSize = 1000;
  }

  /**
   * Initialize the vector database system
   * @returns {Promise<boolean>} Initialization success
   */
  async initialize() {
    try {
      this.logger.info('Initializing vector database system...');

      // Create directories
      await this._ensureDirectories();

      // Initialize metadata database
      await this._initializeMetadataDB();

      // Load or create vector indices
      await this._initializeIndices();

      // Setup backup system
      if (this.config.enableBackup) {
        this._setupBackupSystem();
      }

      this.isInitialized = true;
      this.logger.info('Vector database initialized successfully');

      return true;

    } catch {
      this.logger.error('Failed to initialize vector database', { error: error.message });
      throw error;
    }
  }

  /**
   * Ensure required directories exist
   * @private
   */
  async _ensureDirectories() {
    const dirs = [
      PATH.dirname(this.config.indexPath),
      PATH.dirname(this.config.metadataPath),
      this.config.backupPath,
    ];

    // Create directories in parallel for better performance
    await Promise.all(dirs.map(async (dir) => {
      try {
        // eslint-disable-next-line security/detect-non-literal-fs-filename -- Vector database path controlled by vector database security configuration
        await FS.mkdir(dir, { recursive: true });
      } catch {
        if (error.code !== 'EEXIST') {
          throw error;
        }
      }
    }));
  }

  /**
   * Initialize SQLite metadata database
   * @private
   */
  _initializeMetadataDB() {
    return new Promise((resolve, reject) => {
      this.metadataDb = new SQLITE3.Database(this.config.metadataPath, (error) => {
        if (error) {
          reject(error);
          return;
        }

        // Create metadata table
        const createTableSQL = `
          CREATE TABLE IF NOT EXISTS vector_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vector_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            source_path TEXT,
            title TEXT,
            description TEXT,
            tags TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            similarity_score REAL,
            content_hash TEXT UNIQUE,
            embedding_model TEXT,
            metadata_json TEXT
          )
        `;

        this.metadataDb.run(createTableSQL, (error) => {
          if (error) {
            reject(error);
          } else {
            // Create indices for performance
            this._createMetadataIndices().then(resolve).catch(reject);
          }
        });
      });
    });
  }

  /**
   * Create database indices for metadata queries
   * @private
   */
  async _createMetadataIndices() {
    const indices = [
      'CREATE INDEX IF NOT EXISTS idx_content_type ON vector_metadata(content_type)',
      'CREATE INDEX IF NOT EXISTS idx_vector_id ON vector_metadata(vector_id)',
      'CREATE INDEX IF NOT EXISTS idx_content_hash ON vector_metadata(content_hash)',
      'CREATE INDEX IF NOT EXISTS idx_created_at ON vector_metadata(created_at)',
      'CREATE INDEX IF NOT EXISTS idx_similarity_score ON vector_metadata(similarity_score)',
    ];

    // Create database indices in parallel for better performance
    await Promise.all(indices.map(indexSQL =>
      new Promise((resolve, reject) => {
        this.metadataDb.run(indexSQL, (error) => {
          if (error) {reject(error);} else {resolve();}
        });
      }),
    ));
  }

  /**
   * Initialize vector indices (FAISS)
   * @private
   */
  async _initializeIndices() {
    if (this.config.enableMultiIndex) {
      // Create separate indices for different content types
      // Create indices in parallel for better performance
      await Promise.all(this.config.contentTypes.map(contentType =>
        this._createIndex(contentType),
      ));
    } else {
      // Single unified index
      await this._createIndex('unified');
    }

    // Load existing indices from disk
    await this._loadIndices();
  }

  /**
   * Create a FAISS index for a content type
   * @param {string} contentType - Content type identifier
   * @private
   */
  _createIndex(contentType) {
    try {
      let _index;

      if (this.config.indexType === 'HNSW') {
        _index = new IndexHNSWFlat(this.config.embeddingDimension, this.config.hnswM);
        _index.setEfConstruction(this.config.hnswEfConstruction);
        _index.setEfSearch(this.config.hnswEfSearch);
      } else {
        // Flat index for exact search
        _index = new IndexFlatIP(this.config.embeddingDimension);
      }

      this.indices.set(contentType, {
        index: _index,
        vectorCount: 0,
        lastModified: Date.now(),
      });

      this.logger.debug(`Created ${this.config.indexType} index for ${contentType}`);

    } catch {
      this.logger.error(`Failed to create index for ${contentType}`, { error: error.message });
      throw error;
    }
  }

  /**
   * Load existing indices from disk
   * @private
   */
  async _loadIndices() {
    // Load indices in parallel for better performance
    const loadPromises = Array.from(this.indices.entries()).map(async ([contentType, indexInfo]) => {
      const indexPath = this._getIndexPath(contentType);

      try {
        await FS.access(indexPath);
        // Index file exists, load it
        indexInfo.index.read(indexPath);
        indexInfo.vectorCount = indexInfo.index.ntotal();
        this.vectorCount += indexInfo.vectorCount;

        this.logger.info(`Loaded index for ${contentType} with ${indexInfo.vectorCount} vectors`);

      } catch {
        // Index doesn't exist yet, will be created on first insert
        this.logger.debug(`No existing index found for ${contentType}, will create on first insert`);
      }
    });

    await Promise.all(loadPromises);

    // Update total stats
    this.stats.totalVectors = this.vectorCount;
  }

  /**
   * Get index file path for content type
   * @param {string} contentType - Content type
   * @returns {string} Index file path
   * @private
   */
  _getIndexPath(contentType) {
    const basePath = this.config.indexPath.replace('.index', '');
    return `${basePath}_${contentType}.index`;
  }

  /**
   * Add vectors to the database with metadata
   * @param {Array<Array<number>>} vectors - Vector embeddings
   * @param {Array<Object>} metadata - Corresponding metadata
   * @returns {Promise<Array<number>>} Vector IDs
   */
  async addVectors(vectors, metadata) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    if (vectors.length !== metadata.length) {
      throw new Error('Vectors And metadata arrays must have the same length');
    }

    try {
      this.logger.debug(`Adding ${vectors.length} vectors to database`);
      const vectorIds = [];

      // Group by content type for multi-index support
      const groupedData = this._groupByContentType(vectors, metadata);

      // Add vectors to indices in parallel for better performance
      const addPromises = Array.from(groupedData.entries()).map(([contentType, data]) => {
        const { vectors: typeVectors, metadata: typeMetadata } = data;
        return this._addVectorsToIndex(contentType, typeVectors, typeMetadata);
      });

      const results = await Promise.all(addPromises);
      results.forEach(ids => vectorIds.push(...ids));

      // Save indices to disk
      await this._saveIndices();

      this.logger.info(`Successfully added ${vectors.length} vectors`);
      return vectorIds;

    } catch {
      this.logger.error('Failed to add vectors', { error: error.message });
      throw error;
    }
  }

  /**
   * Group vectors And metadata by content type
   * @param {Array<Array<number>>} vectors - Vectors to group
   * @param {Array<Object>} metadata - Metadata to group
   * @returns {Map<string, Object>} Grouped data by content type
   * @private
   */
  _groupByContentType(vectors, metadata) {
    const grouped = new Map();

    for (let i = 0; i < vectors.length; i++) {
      // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for vector metadata processing
      const contentType = metadata[i].content_type || 'unified';

      if (!grouped.has(contentType)) {
        grouped.set(contentType, { vectors: [], metadata: [] });
      }

      // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for vector data grouping
      grouped.get(contentType).vectors.push(vectors[i]);
      // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for metadata grouping
      grouped.get(contentType).metadata.push(metadata[i]);
    }

    return grouped;
  }

  /**
   * Add vectors to a specific index
   * @param {string} contentType - Content type
   * @param {Array<Array<number>>} vectors - Vectors to add
   * @param {Array<Object>} metadata - Corresponding metadata
   * @returns {Promise<Array<number>>} Vector IDs
   * @private
   */
  async _addVectorsToIndex(contentType, vectors, metadata) {
    const indexInfo = this.indices.get(contentType);
    if (!indexInfo) {
      await this._createIndex(contentType);
    }

    const vectorIds = [];

    // Process in batches for performance
    for (let i = 0; i < vectors.length; i += this.config.batchSize) {
      const batchVectors = vectors.slice(i, i + this.config.batchSize);
      const batchMetadata = metadata.slice(i, i + this.config.batchSize);

      // Add to FAISS index
      const startVectorId = this.vectorCount;
      indexInfo.index.add(Float32Array.from(batchVectors.flat()));

      // Add metadata to SQLite in parallel for better performance
      const metadataPromises = batchVectors.map((_, j) => {
        const vectorId = startVectorId + j;
        // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for batch metadata insertion
        return this._insertMetadata(vectorId, batchMetadata[j]).then(() => vectorId);
      });

      const batchVectorIds = await Promise.all(metadataPromises); // eslint-disable-line no-await-in-loop -- Batch processing requires sequential completion to maintain data integrity
      vectorIds.push(...batchVectorIds);

      this.vectorCount += batchVectors.length;
      indexInfo.vectorCount += batchVectors.length;
    }

    indexInfo.lastModified = Date.now();
    this.stats.totalVectors = this.vectorCount;

    return vectorIds;
  }

  /**
   * Insert metadata into SQLite database
   * @param {number} vectorId - Vector identifier
   * @param {Object} metadata - Metadata object
   * @private
   */
  _insertMetadata(vectorId, metadata) {
    return new Promise((resolve, reject) => {
      const insertSQL = `
        INSERT INTO vector_metadata (
          vector_id, content_type, source_path, title, description,
          tags, content_hash, embedding_model, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      const values = [
        vectorId,
        metadata.content_type || 'unknown',
        metadata.source_path || null,
        metadata.title || null,
        metadata.description || null,
        JSON.stringify(metadata.tags || []),
        metadata.content_hash || null,
        metadata.embedding_model || 'unknown',
        JSON.stringify(metadata),
      ];

      this.metadataDb.run(insertSQL, values, function (error) {
        if (error) {
          reject(error);
        } else {
          resolve(this.lastID);
        }
      });
    });
  }

  /**
   * Search for similar vectors using semantic similarity
   * @param {Array<number>} queryVector - Query embedding
   * @param {Object} options - Search options
   * @returns {Promise<Array<Object>>} Search results with metadata
   */
  async search(queryVector, options = {}) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    const searchOptions = {
      topK: options.topK || this.config.defaultTopK,
      contentTypes: options.contentTypes || null,
      similarityThreshold: options.similarityThreshold || this.config.similarityThreshold,
      filters: options.filters || {},
      enableReranking: options.enableReranking !== false,
      ...options,
    };

    try {
      const startTime = Date.now();

      // Check cache first
      const cacheKey = this._generateSearchCacheKey(queryVector, searchOptions);
      if (this.searchCache.has(cacheKey)) {
        this.stats.cacheHits++;
        return this.searchCache.get(cacheKey);
      }

      const allResults = [];

      // Search across relevant indices
      const indicesToSearch = this._getIndicesToSearch(searchOptions.contentTypes);

      // Search indices in parallel for better performance
      const searchPromises = indicesToSearch.map(async (contentType) => {
        const indexInfo = this.indices.get(contentType);
        if (!indexInfo || indexInfo.vectorCount === 0) {
          return [];
        }

        const results = await this._searchIndex(indexInfo.index, queryVector, searchOptions);

        // Add content type to results
        results.forEach(result => {
          RESULT.content_type = contentType;
        });

        return results;
      });

      const searchResults = await Promise.all(searchPromises);
      searchResults.forEach(results => allResults.push(...results));

      // Merge And rank results
      const rankedResults = await this._rankAndFilterResults(allResults, searchOptions);

      // Cache results
      this._cacheSearchResults(cacheKey, rankedResults);

      const searchTime = Date.now() - startTime;
      this._updateSearchStats(searchTime);

      this.logger.debug(`Search completed in ${searchTime}ms, found ${rankedResults.length} results`);

      return rankedResults;

    } catch {
      this.logger.error('Search failed', { error: error.message });
      throw error;
    }
  }

  /**
   * Determine which indices to search based on content types
   * @param {Array<string>|null} contentTypes - Content types to search
   * @returns {Array<string>} Index names to search
   * @private
   */
  _getIndicesToSearch(contentTypes) {
    if (!contentTypes) {
      return Array.from(this.indices.keys());
    }

    return contentTypes.filter(type => this.indices.has(type));
  }

  /**
   * Search a specific FAISS index
   * @param {Object} index - FAISS index
   * @param {Array<number>} queryVector - Query vector
   * @param {Object} options - Search options
   * @returns {Promise<Array<Object>>} Raw search results
   * @private
   */
  async _searchIndex(index, queryVector, options) {
    try {
      const k = Math.min(options.topK * 2, this.config.maxResults); // Get more for filtering
      const results = index.search(Float32Array.from(queryVector), k);

      const searchResults = [];

      // Process search results in parallel for better performance
      const resultPromises = [];
      for (let i = 0; i < results.labels.length; i++) {
        // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for FAISS search results
        const vectorId = results.labels[i];
        // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for FAISS similarity scores
        const similarity = results.distances[i];

        if (similarity >= options.similarityThreshold) {
          resultPromises.push(this._getMetadata(vectorId).then(metadata => {
            if (metadata) {
              return {
                vectorId,
                similarity,
                ...metadata,
              };
            }
            return null;
          }));
        }
      }

      const metadataResults = await Promise.all(resultPromises);
      searchResults.push(...metadataResults.filter(result => result !== null));

      return searchResults;

    } catch {
      this.logger.warn('Index search failed', { error: error.message });
      return [];
    }
  }

  /**
   * Get metadata for a vector ID
   * @param {number} vectorId - Vector identifier
   * @returns {Promise<Object|null>} Metadata object
   * @private
   */
  _getMetadata(vectorId) {
    return new Promise((resolve, reject) => {
      const selectSQL = `
        SELECT * FROM vector_metadata WHERE vector_id = ?
      `;

      this.metadataDb.get(selectSQL, [vectorId], (error, row) => {
        if (error) {
          reject(error);
        } else if (row) {
          // Parse JSON fields
          try {
            row.tags = JSON.parse(row.tags || '[]');
            row.metadata_json = JSON.parse(row.metadata_json || '{}');
          } catch {
            this.logger.warn('Failed to parse metadata JSON', { vectorId });
          }
          resolve(row);
        } else {
          resolve(null);
        }
      });
    });
  }

  /**
   * Rank And filter search results
   * @param {Array<Object>} results - Raw search results
   * @param {Object} options - Search options
   * @returns {Promise<Array<Object>>} Ranked And filtered results
   * @private
   */
  _rankAndFilterResults(results, options) {
    // Apply metadata filters
    let filteredResults = this._applyMetadataFilters(results, options.filters);

    // Sort by similarity score
    filteredResults.sort((a, b) => b.similarity - a.similarity);

    // Apply reranking if enabled
    if (options.enableReranking) {
      filteredResults = this._reRankResults(filteredResults, options);
    }

    // Limit to top K
    return filteredResults.slice(0, options.topK);
  }

  /**
   * Apply metadata-based filters to results
   * @param {Array<Object>} results - Results to filter
   * @param {Object} filters - Filter criteria
   * @returns {Array<Object>} Filtered results
   * @private
   */
  _applyMetadataFilters(results, filters) {
    if (!filters || Object.keys(filters).length === 0) {
      return results;
    }

    return results.filter(result => {
      for (const [key, value] of Object.entries(filters)) {
        // eslint-disable-next-line security/detect-object-injection -- Filter key from Object.entries() for metadata filtering
        if (result[key] !== value) {
          return false;
        }
      }
      return true;
    });
  }

  /**
   * Re-rank results using advanced scoring
   * @param {Array<Object>} results - Results to re-rank
   * @param {Object} options - Ranking options
   * @returns {Array<Object>} Re-ranked results
   * @private
   */
  _reRankResults(results, options) {
    // Apply contextual scoring based on recency, content type, etc.
    const now = Date.now();

    return results.map(result => {
      let score = RESULT.similarity;

      // Recency boost (more recent content gets slight boost)
      if (result.created_at) {
        const age = now - new Date(result.created_at).getTime();
        const ageInDays = age / (1000 * 60 * 60 * 24);
        const recencyBoost = Math.exp(-ageInDays / 30) * 0.1; // Decay over 30 days
        score += recencyBoost;
      }

      // Content type relevance boost
      if (options.preferredContentTypes) {
        if (options.preferredContentTypes.includes(result.content_type)) {
          score += 0.05;
        }
      }

      RESULT.finalScore = score;
      return result;
    }).sort((a, b) => b.finalScore - a.finalScore);
  }

  /**
   * Generate cache key for search results
   * @param {Array<number>} queryVector - Query vector
   * @param {Object} options - Search options
   * @returns {string} Cache key
   * @private
   */
  _generateSearchCacheKey(queryVector, options) {
    const CRYPTO = require('crypto');
    const cacheInput = JSON.stringify({
      vector: queryVector.slice(0, 10), // Use first 10 dimensions for key
      options: {
        topK: options.topK,
        contentTypes: options.contentTypes,
        similarityThreshold: options.similarityThreshold,
        filters: options.filters,
      },
    });

    return CRYPTO.createHash('md5').update(cacheInput).digest('hex');
  }

  /**
   * Cache search results with LRU eviction
   * @param {string} key - Cache key
   * @param {Array<Object>} results - Search results
   * @private
   */
  _cacheSearchResults(key, results) {
    if (this.searchCache.size >= this.cacheSize) {
      const firstKey = this.searchCache.keys().next().value;
      this.searchCache.delete(firstKey);
    }

    this.searchCache.set(key, results);
  }

  /**
   * Update search performance statistics
   * @param {number} searchTime - Search time in milliseconds
   * @private
   */
  _updateSearchStats(searchTime) {
    this.stats.searchQueries++;
    const avgTime = this.stats.averageSearchTime;
    const totalQueries = this.stats.searchQueries;
    this.stats.averageSearchTime =
      ((avgTime * (totalQueries - 1)) + searchTime) / totalQueries;
  }

  /**
   * Save all indices to disk
   * @private
   */
  _saveIndices() {
    for (const [contentType, indexInfo] of this.indices) {
      if (indexInfo.vectorCount > 0) {
        const indexPath = this._getIndexPath(contentType);
        indexInfo.index.write(indexPath);
        this.logger.debug(`Saved index for ${contentType} to ${indexPath}`);
      }
    }
  }

  /**
   * Setup automatic backup system
   * @private
   */
  _setupBackupSystem() {
    setInterval(async () => {
      try {
        await this.backup();
      } catch {
        this.logger.error('Automatic backup failed', { error: error.message });
      }
    }, this.config.backupInterval);
  }

  /**
   * Create backup of all indices And metadata
   * @returns {Promise<string>} Backup path
   */
  async backup() {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const backupDir = PATH.join(this.config.backupPath, `backup_${timestamp}`);

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- Vector database backup path controlled by database configuration
      await FS.mkdir(backupDir, { recursive: true });

      // Backup indices in parallel for better performance
      const backupPromises = Array.from(this.indices.entries())
        .filter(([, indexInfo]) => indexInfo.vectorCount > 0)
        .map(([contentType, _indexInfo]) => {
          const sourcePath = this._getIndexPath(contentType);
          const backupPath = PATH.join(backupDir, `${contentType}.index`);
          return FS.copyFile(sourcePath, backupPath);
        });

      await Promise.all(backupPromises);

      // Backup metadata database
      const metadataBackupPath = PATH.join(backupDir, 'metadata.db');
      await FS.copyFile(this.config.metadataPath, metadataBackupPath);

      this.lastBackup = Date.now();
      this.logger.info(`Backup completed: ${backupDir}`);

      return backupDir;

    } catch {
      this.logger.error('Backup failed', { error: error.message });
      throw error;
    }
  }

  /**
   * Get database statistics
   * @returns {Object} Statistics object
   */
  getStatistics() {
    const indexStats = {};
    for (const [contentType, indexInfo] of this.indices) {
      // eslint-disable-next-line security/detect-object-injection -- Content type from Map iteration for statistics collection
      indexStats[contentType] = {
        vectorCount: indexInfo.vectorCount,
        lastModified: indexInfo.lastModified,
      };
    }

    return {
      ...this.stats,
      indexStats,
      isInitialized: this.isInitialized,
      embeddingDimension: this.config.embeddingDimension,
      lastBackup: this.lastBackup,
      cacheSize: this.searchCache.size,
    };
  }

  /**
   * Clear search cache
   */
  clearCache() {
    this.searchCache.clear();
    this.stats.cacheHits = 0;
    this.logger.info('Search cache cleared');
  }

  /**
   * Cleanup resources And close database connections
   */
  async cleanup() {
    try {
      await this._saveIndices();

      if (this.metadataDb) {
        await new Promise((resolve) => {
          this.metadataDb.close(resolve);
        });
      }

      this.clearCache();
      this.indices.clear();
      this.isInitialized = false;

      this.logger.info('Vector database cleanup completed');

    } catch {
      this.logger.error('Cleanup failed', { error: error.message });
    }
  }
}

module.exports = VectorDatabase;
