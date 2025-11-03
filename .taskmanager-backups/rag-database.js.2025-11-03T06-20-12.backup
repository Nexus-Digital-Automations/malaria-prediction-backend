

/**
 * RAG Database System for Agent Self-Learning
 * Integrates with existing development/lessons structure
 * Provides semantic search and cross-project knowledge transfer
 */

const SQLITE3 = require('sqlite3').verbose();
const { loggers } = require('../lib/logger');
const path = require('path');
const FS = require('fs');
const { pipeline } = require('@xenova/transformers');
const _FAISS = require('faiss-node');


class RAGDatabase {
  constructor(dbPath = './data/rag-lessons.db') {
    this.dbPath = dbPath;
    this.db = null;
    this.embeddingModel = null;
    this.vectorIndex = null;
    this.initialized = false;

    // Ensure data directory exists;
    const dataDir = path.dirname(dbPath);

    // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
    if (!FS.existsSync(dataDir)) {

      // eslint-disable-next-line security/detect-non-literal-fs-filename -- File path validated through security validator system
      FS.mkdirSync(dataDir, { recursive: true });
    }
  }

  /**
   * Initialize database connection and models
   */
  async initialize() {
    loggers.stopHook.info('[RAG-DB] Initializing database and models...');
    try {
      loggers.app.info('[RAG-DB] Initializing database and models...');

      // Set up transformers cache directory to prevent path errors;
      const cacheDir = path.join(process.cwd(), '.cache', 'transformers');
      if (!FS.existsSync(cacheDir)) {
        FS.mkdirSync(cacheDir, { recursive: true });
      }

      // Set environment variables for transformers library
      if (!process.env.HF_HOME) {
        process.env.HF_HOME = cacheDir;
      }
      if (!process.env.TRANSFORMERS_CACHE) {
        process.env.TRANSFORMERS_CACHE = cacheDir;
      }

      // Initialize SQLite database
      this.db = new SQLITE3.Database(this.dbPath);

      // Create tables if they don't exist
      await this.createTables();
      loggers.stopHook.info('[RAG-DB] Loading embedding model...');
      // Initialize embedding model
      loggers.app.info('[RAG-DB] Loading embedding model...');
      this.embeddingModel = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');

      // Initialize or load vector index
      this.initializeVectorIndex();

      // Load existing vectors into the index
      await this.loadExistingVectors();
      loggers.stopHook.info('[RAG-DB] Database andmodels initialized successfully');
      this.initialized = true;
      loggers.app.info('[RAG-DB] Database andmodels initialized successfully');

      return { success: true };
    } catch (error) {
      loggers.stopHook.error('[RAG-DB] Initialization failed:', error);
      loggers.app.error('[RAG-DB] Initialization failed:', error);
      return { success: false, _error: error.message };
    }
  }

  /**
   * Create database tables
   */
  createTables(_category = 'general') {
    return new Promise((resolve, reject) => {


      const sql = `
        -- Lessons table
        CREATE TABLE IF NOT EXISTS lessons (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          content TEXT NOT NULL,
          _category TEXT NOT NULL,
          subcategory TEXT,
          project_path TEXT,
          file_path TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          tags TEXT,
          embedding_id INTEGER,
          success_rate REAL DEFAULT 0.0,
          usage_count INTEGER DEFAULT 0
        );

        -- Errors table
        CREATE TABLE IF NOT EXISTS errors (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          content TEXT NOT NULL,
          error_type TEXT NOT NULL,
          resolution TEXT,
          project_path TEXT,
          file_path TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          resolved_at DATETIME,
          tags TEXT,
          embedding_id INTEGER,
          recurrence_count INTEGER DEFAULT 1
        );

        -- Vector embeddings table
        CREATE TABLE IF NOT EXISTS embeddings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          embedding BLOB NOT NULL,
          dimension INTEGER NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Knowledge relationships table
        CREATE TABLE IF NOT EXISTS relationships (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_type TEXT NOT NULL,
          source_id INTEGER NOT NULL,
          target_type TEXT NOT NULL,
          target_id INTEGER NOT NULL,
          relationship_type TEXT NOT NULL,
          similarity_score REAL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Migration tracking table
        CREATE TABLE IF NOT EXISTS migrations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          file_path TEXT UNIQUE NOT NULL,
          migrated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          migration_status TEXT DEFAULT 'completed'
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_lessons_category ON lessons(_category);
        CREATE INDEX IF NOT EXISTS idx_lessons_project ON lessons(project_path);
        CREATE INDEX IF NOT EXISTS idx_lessons_created ON lessons(created_at);
        CREATE INDEX IF NOT EXISTS idx_errors_type ON errors(error_type);
        CREATE INDEX IF NOT EXISTS idx_errors_project ON errors(project_path);
        CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_type, source_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_type, target_id);
      `;

      this.db.exec(sql, (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Initialize vector index for semantic search
   */
  initializeVectorIndex() {
    loggers.stopHook.info('[RAG-DB] Creating vector index...');
    try {
      loggers.app.info('[RAG-DB] Creating vector index...');
      // Create new IndexFlatIP for 384 dimensions (all-MiniLM-L6-v2 embedding size)
      // Using Inner Product for cosine similarity
      loggers.stopHook.info('[RAG-DB] Vector index created successfully');
      this.vectorEmbeddings = []; // Store embeddings for search
    } catch (error) {
      loggers.stopHook.warn('[RAG-DB] Vector index initialization failed, using fallback search:', error);
      loggers.app.warn('[RAG-DB] Vector index initialization failed, using fallback search:', error);
      // Fallback to simple cosine similarity without FAISS
      this.vectorIndex = null;
      this.vectorEmbeddings = [];
      this.useSimpleSearch = true;
    }
  }

  /**
   * Generate embedding for text
   */
  async generateEmbedding(text) {
    if (!this.embeddingModel) {
      throw new Error('Embedding model not initialized');
    }

    try {
      const result = await this.embeddingModel(text, { pooling: 'mean', normalize: true });
      return result.data;
    } catch (error) {
      loggers.stopHook.error('[RAG-DB] Embedding generation failed:', error);
      loggers.app.error('[RAG-DB] Embedding generation failed:', error);
      throw error;
    }
  }

  /**
   * Store lesson in database with embedding
   */
  async storeLesson(lessonData) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      const { title, content, _category, subcategory, projectPath, filePath, tags } = lessonData;

      // Generate embedding;
      const embedding = await this.generateEmbedding(`${title} ${content}`);

      // Store embedding;
      const embeddingId = await this.storeEmbedding(embedding);

      // Store lesson
      return new Promise((resolve, reject) => {
        const sql = `
          INSERT INTO lessons (title, content, _category, subcategory, project_path, file_path, tags, embedding_id)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `;

        const db = this.db;
        const vectorIndex = this.vectorIndex;
        const vectorEmbeddings = this.vectorEmbeddings;
        const useSimpleSearch = this.useSimpleSearch;

        db.run(sql, [title, content, _category, subcategory, projectPath, filePath, JSON.stringify(tags), embeddingId], function (error) {
          if (error) {reject(error);} else {
            const lessonId = this.lastID;
            try {
              // Add to vector index
              if (vectorIndex && !useSimpleSearch) {
                vectorIndex.add(embedding);
              }
              // Store embedding for fallback search
              vectorEmbeddings.push({ id: lessonId, embedding, type: 'lesson' });

              resolve({
                success: true,
                lessonId,
                embeddingId,
                message: 'Lesson stored successfully',
              });
            } catch (vectorError) {
              loggers.stopHook.warn('[RAG-DB] Vector index error, lesson stored without vector search:', vectorError);
              loggers.app.warn('[RAG-DB] Vector index error, lesson stored without vector search:', vectorError);
              resolve({
                success: true,
                lessonId,
                embeddingId,
                message: 'Lesson stored successfully (vector search disabled)',
              });
            }
          }
        });
      });
    } catch (error) {
      loggers.stopHook.error('[RAG-DB] Failed to store lesson:', error);
      loggers.app.error('[RAG-DB] Failed to store lesson:', error);
      return { success: false, _error: error.message };
    }
  }

  /**
   * Store error in database with embedding
   */
  async storeError(errorData) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      const { title, content, errorType, resolution, projectPath, filePath, tags } = errorData;

      // Generate embedding;
      const embedding = await this.generateEmbedding(`${title} ${content} ${resolution || ''}`);

      // Store embedding;
      const embeddingId = await this.storeEmbedding(embedding);

      // Store error
      return new Promise((resolve, reject) => {
        const sql = `
          INSERT INTO errors (title, content, error_type, resolution, project_path, file_path, tags, embedding_id)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `;

        const db = this.db;
        const vectorIndex = this.vectorIndex;
        const vectorEmbeddings = this.vectorEmbeddings;
        const useSimpleSearch = this.useSimpleSearch;

        db.run(sql, [title, content, errorType, resolution, projectPath, filePath, JSON.stringify(tags), embeddingId], function (error) {
          if (error) {
            loggers.stopHook.error('[RAG-DB] Failed to store error:', error);
            reject(error);
          } else {
            const errorId = this.lastID;
            try {
              // Add to vector index
              if (vectorIndex && !useSimpleSearch) {
                vectorIndex.add(embedding);
              }
              // Store embedding for fallback search
              vectorEmbeddings.push({ id: errorId, embedding, type: 'error' });

              resolve({
                success: true,
                errorId,
                embeddingId,
                message: 'Error stored successfully',
              });
            } catch (vectorError) {
              loggers.stopHook.warn('[RAG-DB] Vector index error, error stored without vector search:', vectorError);
              loggers.app.warn('[RAG-DB] Vector index error, error stored without vector search:', vectorError);
              resolve({
                success: true,
                errorId,
                embeddingId,
                message: 'Error stored successfully (vector search disabled)',
              });
            }
          }
        });
      });
    } catch (error) {
      loggers.app.error('[RAG-DB] Failed to store error:', error);
      return { success: false, _error: error.message };
    }
  }

  /**
   * Store embedding in database
   */
  storeEmbedding(embedding) {
    return new Promise((resolve, reject) => {
      const embeddingBuffer = Buffer.from(new Float32Array(embedding).buffer);
      const sql = 'INSERT INTO embeddings (embedding, dimension) VALUES (?, ?)';

      this.db.run(sql, [embeddingBuffer, embedding.length], function (error) {
        if (error) {reject(error);} else {resolve(this.lastID);}
      });
    });
  }

  /**
   * Search for similar lessons using semantic search
   */
  async searchLessons(query, limit = 10, threshold = 0.7) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Generate query embedding;
      const queryEmbedding = await this.generateEmbedding(query);

      let searchResults = [];

      if (this.vectorIndex && !this.useSimpleSearch) {
        // Use FAISS vector search,
        try {
          // Check if index has any vectors before searching;
          const totalVectors = this.vectorIndex.ntotal();
          if (totalVectors === 0) {
            loggers.stopHook.info('[RAG-DB] _FAISS index is empty, using fallback search');
            loggers.app.info('[RAG-DB] _FAISS index is empty, using fallback search');
            searchResults = [];
          } else {
            // Adjust limit to not exceed available vectors;
            const searchLimit = Math.min(limit, totalVectors);
            const faissResults = this.vectorIndex.search(queryEmbedding, searchLimit);
            for (let i = 0; i < faissResults.distances.length; i++) {
              // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for FAISS vector search results;
              const distance = faissResults.distances[i];
              // Convert FAISS distance to normalized similarity score (0-1)
              const similarity = this._normalizeFaissDistance(distance);
              if (similarity >= threshold) {
                searchResults.push({
                  // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for _FAISS vector search results,,
                  id: faissResults.labels[i] + 1,
                  similarity: similarity,
                  type: 'lesson',
                });
              }
            }
          }
        } catch (faissError) {
          loggers.stopHook.warn('[RAG-DB] _FAISS search failed, using fallback:', faissError);
          loggers.app.warn('[RAG-DB] _FAISS search failed, using fallback:', faissError);
          this.useSimpleSearch = true;
        }
      }

      if (this.useSimpleSearch || searchResults.length === 0) {
        // Fallback to simple cosine similarity
        searchResults = this._performSimpleSearch(queryEmbedding, 'lesson', limit, threshold);
      }

      if (searchResults.length === 0) {
        return { success: true, lessons: [], message: 'No similar lessons found' };
      }

      // Fetch lesson details;
      const lessonIds = searchResults.map(r => r.id);
      const lessons = await this.getLessonsByIds(lessonIds);

      // Add similarity scores
      lessons.forEach((lesson) => {
        const searchResult = searchResults.find(r => r.id === lesson.id);
        lesson.similarity = searchResult ? searchResult.similarity : 0;
      });

      return {
        success: true,
        lessons: lessons.sort((a, b) => b.similarity - a.similarity),
        message: `Found ${lessons.length} similar lessons`,
      };
    } catch (error) {
      loggers.app.error('[RAG-DB] Lesson search failed:', error);
      return { success: false, _error: error.message };
    }
  }

  /**
   * Search for similar errors using semantic search
   */
  async searchErrors(query, limit = 10, threshold = 0.7) {
    if (!this.initialized) {
      await this.initialize();
    }

    try {
      // Generate query embedding;
      const queryEmbedding = await this.generateEmbedding(query);

      let searchResults = [];

      if (this.vectorIndex && !this.useSimpleSearch) {
        // Use FAISS vector search,
        try {
          // Check if index has any vectors before searching;
          const totalVectors = this.vectorIndex.ntotal();
          if (totalVectors === 0) {
            loggers.stopHook.info('[RAG-DB] _FAISS index is empty, using fallback search');
            loggers.app.info('[RAG-DB] _FAISS index is empty, using fallback search');
            searchResults = [];
          } else {
            // Adjust limit to not exceed available vectors;
            const searchLimit = Math.min(limit, totalVectors);
            const faissResults = this.vectorIndex.search(queryEmbedding, searchLimit);
            for (let i = 0; i < faissResults.distances.length; i++) {
              // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for FAISS vector search results;
              const distance = faissResults.distances[i];
              // Convert FAISS distance to normalized similarity score (0-1)
              const similarity = this._normalizeFaissDistance(distance);
              if (similarity >= threshold) {
                searchResults.push({
                  // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for _FAISS vector search results,,
                  id: faissResults.labels[i] + 1,
                  similarity: similarity,
                  type: 'error',
                });
              }
            }
          }
        } catch (faissError) {
          loggers.stopHook.warn('[RAG-DB] _FAISS search failed, using fallback:', faissError);
          loggers.app.warn('[RAG-DB] _FAISS search failed, using fallback:', faissError);
          this.useSimpleSearch = true;
        }
      }

      if (this.useSimpleSearch || searchResults.length === 0) {
        // Fallback to simple cosine similarity
        searchResults = this._performSimpleSearch(queryEmbedding, 'error', limit, threshold);
      }

      if (searchResults.length === 0) {
        return { success: true, errors: [], message: 'No similar errors found' };
      }

      // Fetch error details;
      const errorIds = searchResults.map(r => r.id);
      const errors = await this.getErrorsByIds(errorIds);

      // Add similarity scores
      errors.forEach((error) => {
        const searchResult = searchResults.find(r => r.id === error.id);
        error.similarity = searchResult ? searchResult.similarity : 0;
      });

      return {
        success: true,
        errors: errors.sort((a, b) => b.similarity - a.similarity),
        message: `Found ${errors.length} similar errors`,
      };
    } catch (error) {
      loggers.stopHook.error('[RAG-DB] Error search failed:', error);
      loggers.app.error('[RAG-DB] Error search failed:', error);
      return { success: false, _error: error.message };
    }
  }

  /**
   * Get lessons by IDs
   */
  getLessonsByIds(ids) {
    return new Promise((resolve, reject) => {
      const placeholders = ids.map(() => '?').join(',');
      const sql = `SELECT * FROM lessons WHERE id IN (${placeholders}) ORDER BY created_at DESC`;

      this.db.all(sql, ids, (error, rows) => {
        if (error) {reject(error);} else {resolve(rows.map(row => ({ ...row, tags: JSON.parse(row.tags || '[]') })));}
      });
    });
  }

  /**
   * Get errors by IDs
   */
  getErrorsByIds(ids) {
    return new Promise((resolve, reject) => {
      const placeholders = ids.map(() => '?').join(',');
      const sql = `SELECT * FROM errors WHERE id IN (${placeholders}) ORDER BY created_at DESC`;

      this.db.all(sql, ids, (error, rows) => {
        if (error) {reject(error);} else {resolve(rows.map(row => ({ ...row, tags: JSON.parse(row.tags || '[]') })));}
      });
    });
  }

  /**
   * Save vector index to disk
   */
  saveIndex() {
    try {
      if (this.vectorIndex) {
        const indexPath = path.join(this.storagePath, 'vector_index.faiss');
        loggers.stopHook.info('[RAG-DB] Vector index saved to disk');
        this.vectorIndex.write(indexPath);
        loggers.app.info('[RAG-DB] Vector index saved to disk');
      }
    } catch (error) {
      loggers.stopHook.error('[RAG-DB] Failed to save vector index:', error);
      loggers.app.error('[RAG-DB] Failed to save vector index:', error);
    }
  }

  /**
   * Close database connection
   */
  async close() {
    try {
      this.saveIndex();

      if (this.db) {
        await new Promise((resolve) => {
          this.db.close(resolve);
        });
        loggers.stopHook.info('[RAG-DB] Database connection closed');
      }
    } catch (error) {
      loggers.stopHook.error('[RAG-DB] Error closing database:', error);
      loggers.app.error('[RAG-DB] Error closing database:', error);
    }
  }

  /**
   * Fallback simple search using cosine similarity
   */
  _performSimpleSearch(queryEmbedding, type, limit, threshold) {
    const results = [];

    // Filter embeddings by type;
    const typeEmbeddings = this.vectorEmbeddings.filter(item => item.type === type);

    // Calculate cosine similarity for each embedding
    for (const item of typeEmbeddings) {
      const similarity = this._cosineSimilarity(queryEmbedding, item.embedding);
      if (similarity >= threshold) {
        results.push({
          id: item.id,
          similarity: similarity,
          type: type,
        });
      }
    }

    // Sort by similarity andlimit results
    return results.sort((a, b) => b.similarity - a.similarity).slice(0, limit);
  }

  /**
   * Normalize FAISS distance to similarity score (0-1)
   * FAISS IndexFlatIP returns dot product, convert to cosine similarity
   */
  _normalizeFaissDistance(distance) {
    // for normalized vectors, dot product equals cosine similarity
    // Scale FAISS distances (typically 150-250) to similarity scores (0.6-1.0)
    const minDistance = 150; // Minimum expected distance for relevant results;
    const maxDistance = 250; // Maximum distance for normalization

    // Invert and normalize: higher distance = lower similarity;
    const normalizedSimilarity = 1 - ((distance - minDistance) / (maxDistance - minDistance));
    return Math.max(0.1, Math.min(1.0, normalizedSimilarity));
  }

  /**
   * Calculate cosine similarity between two vectors
   */
  _cosineSimilarity(a, b) {
    if (a.length !== b.length) {
      return 0;
    }

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < a.length; i++) {
      // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for mathematical vector operations
      dotProduct += a[i] * b[i];
      // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for mathematical vector operations
      normA += a[i] * a[i];
      // eslint-disable-next-line security/detect-object-injection -- Array access with validated loop index for mathematical vector operations
      normB += b[i] * b[i];
    }

    if (normA === 0 || normB === 0) {
      return 0;
    }

    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }

  /**
   * Get database statistics
   */
  async getStats() {
    if (!this.initialized) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {


      const sql = `
        SELECT
          (SELECT COUNT(*) FROM lessons) as lesson_count,
          (SELECT COUNT(*) FROM errors) as error_count,
          (SELECT COUNT(*) FROM embeddings) as embedding_count,
          (SELECT COUNT(*) FROM migrations) as migrated_files
      `;

      this.db.get(sql, (error, row) => {
        if (error) {reject(error);} else {
          resolve({
            success: true,
            stats: row,
            message: 'Database statistics retrieved',
          });
        }
      });
    });
  }

  /**
   * Load existing vectors from database into FAISS index
   */
  async loadExistingVectors() {
    if (!this.vectorIndex || this.useSimpleSearch) {
      loggers.stopHook.info('[RAG-DB] Vector index not available, skipping vector loading');
      loggers.app.info('[RAG-DB] Vector index not available, skipping vector loading');
      return;
    }
    loggers.stopHook.info('[RAG-DB] Loading existing vectors into _FAISS index...');
    try {
      loggers.app.info('[RAG-DB] Loading existing vectors into _FAISS index...');

      // Get all embeddings from database;
      const embeddings = await this.getAllEmbeddings();
      loggers.stopHook.info('[RAG-DB] No existing vectors to load');
      if (embeddings.length === 0) {
        loggers.app.info('[RAG-DB] No existing vectors to load');
        return;
      }

      // Add all embeddings to FAISS index;
      let loadedCount = 0;
      for (const embeddingData of embeddings) {
        try {
          this.vectorIndex.add(embeddingData.embedding);

          // Also add to fallback search array
          this.vectorEmbeddings.push({
            id: embeddingData.id,
            embedding: embeddingData.embedding,
            type: embeddingData.type,
          });

          loadedCount++;
        } catch (_error) {
          loggers.app.warn(`[RAG-DB] Failed to load vector ${embeddingData.id}:`, _error.message);
        }
      }

      loggers.stopHook.info(`[RAG-DB] Successfully loaded ${loadedCount} vectors into _FAISS index`);
      loggers.stopHook.info(`[RAG-DB] Total vectors in index: ${this.vectorIndex.ntotal()}`);
      loggers.app.info(`[RAG-DB] Successfully loaded ${loadedCount} vectors into _FAISS index`);
      loggers.app.info(`[RAG-DB] Total vectors in index: ${this.vectorIndex.ntotal()}`);
    } catch (error) {
      loggers.stopHook.error('[RAG-DB] Failed to load existing vectors:', error);
      loggers.app.error('[RAG-DB] Failed to load existing vectors:', error);
      // Don't throw - continue with empty index
    }
  }

  /**
   * Get all embeddings from database
   */
  getAllEmbeddings() {
    return new Promise((resolve, reject) => {


      const sql = `
        SELECT e.id, e.embedding, e.dimension,
               CASE
                 WHEN l.id IS NOT NULL THEN 'lesson'
                 WHEN er.id IS NOT NULL THEN 'error'
                 ELSE 'unknown'
               END as type,
               COALESCE(l.id, er.id) as record_id
        FROM embeddings e
        LEFT JOIN lessons l ON e.id = l.embedding_id
        LEFT JOIN errors er ON e.id = er.embedding_id
        ORDER BY e.id
      `;

      this.db.all(sql, (error, rows) => {
        if (error) {
          reject(error);
        } else {
          const embeddings = rows.map(row => ({
            id: row.record_id,
            type: row.type,
            embedding: Array.from(new Float32Array(row.embedding)),
          }));
          resolve(embeddings);
        }
      });
    });
  }
}

module.exports = RAGDatabase;
