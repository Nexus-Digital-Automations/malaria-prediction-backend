-- =====================================================================
-- RAG-Based Agent Learning Database Schema
-- =====================================================================
--
-- Purpose: Comprehensive database schema for storing agent lessons,
--          errors, and vector embeddings to support semantic search
--          and machine learning-based task optimization
--
-- Technology: SQLite with vector extension support
-- Author: Database Architecture Agent
-- Version: 1.0.0
-- Date: 2025-09-20
-- =====================================================================

-- Enable foreign key constraints and WAL mode for better performance
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;

-- =====================================================================
-- CORE TABLES
-- =====================================================================

-- Projects table - tracks different codebases/projects
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    metadata JSON DEFAULT '{}'
);

-- Performance indexes for projects table
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_projects_path ON projects(path);
CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(is_active);

-- Agents table - tracks agent instances and their capabilities
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY, -- Agent ID from TaskManager
    session_id TEXT,
    name TEXT,
    role TEXT NOT NULL, -- development, testing, research, etc.
    specialization JSON DEFAULT '[]', -- Array of specializations
    capabilities JSON DEFAULT '[]', -- Array of capabilities
    project_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active', -- active, inactive, archived
    performance_metrics JSON DEFAULT '{}',

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- Performance indexes for agents table
CREATE INDEX IF NOT EXISTS idx_agents_session ON agents(session_id);
CREATE INDEX IF NOT EXISTS idx_agents_role ON agents(role);
CREATE INDEX IF NOT EXISTS idx_agents_project ON agents(project_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_last_active ON agents(last_active);

-- Tasks table - comprehensive task tracking with enhanced metadata
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- error, feature, subtask, test
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, failed
    priority TEXT DEFAULT 'normal', -- low, normal, high, critical
    project_id INTEGER,
    assigned_agent_id TEXT,
    created_by_agent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_duration INTEGER, -- in minutes
    actual_duration INTEGER, -- in minutes
    complexity_score INTEGER CHECK (complexity_score BETWEEN 1 AND 10),
    success_criteria JSON DEFAULT '[]',
    dependencies JSON DEFAULT '[]',
    metadata JSON DEFAULT '{}',

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

-- Performance indexes for tasks table
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_complexity ON tasks(complexity_score);

-- =====================================================================
-- LESSONS AND ERRORS STORAGE
-- =====================================================================

-- Lessons table - stores successful patterns and learnings
CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL, -- error_resolution, feature_implementation, optimization, decision, pattern
    subcategory TEXT, -- specific type within category
    content TEXT NOT NULL, -- markdown formatted lesson content
    context TEXT, -- specific context where lesson applies
    task_id TEXT, -- reference to originating task
    project_id INTEGER,
    agent_id TEXT, -- agent that created the lesson
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 0.5 CHECK (confidence_score BETWEEN 0 AND 1),
    effectiveness_score REAL DEFAULT 0.5 CHECK (effectiveness_score BETWEEN 0 AND 1),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    tags JSON DEFAULT '[]', -- searchable tags
    code_patterns JSON DEFAULT '[]', -- code patterns associated with lesson
    file_patterns JSON DEFAULT '[]', -- file patterns where lesson applies
    dependencies JSON DEFAULT '[]', -- technologies/frameworks lesson applies to
    related_errors JSON DEFAULT '[]', -- error types this lesson helps solve
    metadata JSON DEFAULT '{}',

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Performance indexes for lessons table
CREATE INDEX IF NOT EXISTS idx_lessons_category ON lessons(category);
CREATE INDEX IF NOT EXISTS idx_lessons_subcategory ON lessons(subcategory);
CREATE INDEX IF NOT EXISTS idx_lessons_project ON lessons(project_id);
CREATE INDEX IF NOT EXISTS idx_lessons_agent ON lessons(agent_id);
CREATE INDEX IF NOT EXISTS idx_lessons_task ON lessons(task_id);
CREATE INDEX IF NOT EXISTS idx_lessons_created_at ON lessons(created_at);
CREATE INDEX IF NOT EXISTS idx_lessons_confidence ON lessons(confidence_score);
CREATE INDEX IF NOT EXISTS idx_lessons_effectiveness ON lessons(effectiveness_score);
CREATE INDEX IF NOT EXISTS idx_lessons_usage_count ON lessons(usage_count);

-- Errors table - comprehensive error tracking and analysis
CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    error_type TEXT NOT NULL, -- linter, build, runtime, integration, security
    error_code TEXT, -- specific error code if available
    message TEXT NOT NULL, -- error message
    stack_trace TEXT, -- full stack trace
    file_path TEXT, -- file where error occurred
    line_number INTEGER, -- line number of error
    column_number INTEGER, -- column number of error
    context TEXT, -- surrounding code context
    task_id TEXT, -- task where error occurred
    project_id INTEGER,
    agent_id TEXT, -- agent that encountered the error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_method TEXT, -- how the error was resolved
    resolution_description TEXT, -- detailed resolution steps
    prevention_strategy TEXT, -- how to prevent this error in future
    severity TEXT DEFAULT 'medium', -- low, medium, high, critical
    frequency INTEGER DEFAULT 1, -- how often this error occurs
    impact_score REAL DEFAULT 0.5 CHECK (impact_score BETWEEN 0 AND 1),
    is_resolved BOOLEAN DEFAULT 0,
    tags JSON DEFAULT '[]',
    related_lessons JSON DEFAULT '[]', -- lessons that help resolve this error
    code_patterns JSON DEFAULT '[]', -- problematic code patterns
    environment_info JSON DEFAULT '{}', -- system/environment details
    metadata JSON DEFAULT '{}',

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Performance indexes for errors table
CREATE INDEX IF NOT EXISTS idx_errors_type ON errors(error_type);
CREATE INDEX IF NOT EXISTS idx_errors_code ON errors(error_code);
CREATE INDEX IF NOT EXISTS idx_errors_project ON errors(project_id);
CREATE INDEX IF NOT EXISTS idx_errors_agent ON errors(agent_id);
CREATE INDEX IF NOT EXISTS idx_errors_task ON errors(task_id);
CREATE INDEX IF NOT EXISTS idx_errors_created_at ON errors(created_at);
CREATE INDEX IF NOT EXISTS idx_errors_resolved ON errors(is_resolved);
CREATE INDEX IF NOT EXISTS idx_errors_severity ON errors(severity);
CREATE INDEX IF NOT EXISTS idx_errors_frequency ON errors(frequency);
CREATE INDEX IF NOT EXISTS idx_errors_file_path ON errors(file_path);

-- =====================================================================
-- VECTOR EMBEDDINGS STORAGE
-- =====================================================================

-- Embeddings table - stores vector representations for semantic search
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, -- 'lesson', 'error', 'task', 'code_pattern'
    entity_id INTEGER NOT NULL, -- ID of the referenced entity
    embedding_model TEXT NOT NULL, -- model used to generate embedding
    embedding_vector BLOB NOT NULL, -- serialized vector data
    vector_dimension INTEGER NOT NULL, -- dimension of the vector
    content_hash TEXT NOT NULL, -- hash of the content that was embedded
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON DEFAULT '{}',

    -- Ensure one embedding per entity per model
    UNIQUE(entity_type, entity_id, embedding_model)
);

-- Performance indexes for embeddings table
CREATE INDEX IF NOT EXISTS idx_embeddings_entity ON embeddings(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(embedding_model);
CREATE INDEX IF NOT EXISTS idx_embeddings_hash ON embeddings(content_hash);
CREATE INDEX IF NOT EXISTS idx_embeddings_dimension ON embeddings(vector_dimension);

-- =====================================================================
-- RELATIONSHIPS AND ASSOCIATIONS
-- =====================================================================

-- Lesson relationships - track relationships between lessons
CREATE TABLE IF NOT EXISTS lesson_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_lesson_id INTEGER NOT NULL,
    target_lesson_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL, -- 'related', 'prerequisite', 'alternative', 'supersedes'
    strength REAL DEFAULT 0.5 CHECK (strength BETWEEN 0 AND 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_agent_id TEXT,

    FOREIGN KEY (source_lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
    FOREIGN KEY (target_lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_agent_id) REFERENCES agents(id) ON DELETE SET NULL,

    -- Prevent duplicate relationships
    UNIQUE(source_lesson_id, target_lesson_id, relationship_type)
);

-- Performance indexes for lesson_relationships table
CREATE INDEX IF NOT EXISTS idx_lesson_rel_source ON lesson_relationships(source_lesson_id);
CREATE INDEX IF NOT EXISTS idx_lesson_rel_target ON lesson_relationships(target_lesson_id);
CREATE INDEX IF NOT EXISTS idx_lesson_rel_type ON lesson_relationships(relationship_type);

-- Error-Lesson associations - link errors to lessons that resolve them
CREATE TABLE IF NOT EXISTS error_lesson_associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    association_type TEXT NOT NULL, -- 'resolves', 'prevents', 'related'
    effectiveness_score REAL DEFAULT 0.5 CHECK (effectiveness_score BETWEEN 0 AND 1),
    validation_count INTEGER DEFAULT 0, -- how many times this association was validated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,
    created_by_agent_id TEXT,

    FOREIGN KEY (error_id) REFERENCES errors(id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_agent_id) REFERENCES agents(id) ON DELETE SET NULL,

    -- Prevent duplicate associations
    UNIQUE(error_id, lesson_id, association_type)
);

-- Performance indexes for error_lesson_associations table
CREATE INDEX IF NOT EXISTS idx_error_lesson_error ON error_lesson_associations(error_id);
CREATE INDEX IF NOT EXISTS idx_error_lesson_lesson ON error_lesson_associations(lesson_id);
CREATE INDEX IF NOT EXISTS idx_error_lesson_type ON error_lesson_associations(association_type);
CREATE INDEX IF NOT EXISTS idx_error_lesson_effectiveness ON error_lesson_associations(effectiveness_score);

-- =====================================================================
-- ANALYTICS AND METRICS
-- =====================================================================

-- Usage analytics - track how lessons and errors are accessed
CREATE TABLE IF NOT EXISTS usage_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, -- 'lesson', 'error', 'task'
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL, -- 'view', 'apply', 'reference', 'update'
    agent_id TEXT,
    project_id INTEGER,
    task_id TEXT, -- task context where action occurred
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context JSON DEFAULT '{}', -- additional context data
    outcome TEXT, -- success, failure, partial

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Performance indexes for usage_analytics table
CREATE INDEX IF NOT EXISTS idx_analytics_entity ON usage_analytics(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_analytics_action ON usage_analytics(action);
CREATE INDEX IF NOT EXISTS idx_analytics_agent ON usage_analytics(agent_id);
CREATE INDEX IF NOT EXISTS idx_analytics_project ON usage_analytics(project_id);
CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON usage_analytics(created_at);

-- Performance metrics - track agent and system performance
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_type TEXT NOT NULL, -- 'task_completion', 'error_resolution', 'lesson_effectiveness'
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT, -- 'seconds', 'percentage', 'count', etc.
    agent_id TEXT,
    project_id INTEGER,
    task_id TEXT,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context JSON DEFAULT '{}',

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Performance indexes for performance_metrics table
CREATE INDEX IF NOT EXISTS idx_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_agent ON performance_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_metrics_project ON performance_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_metrics_measured_at ON performance_metrics(measured_at);

-- =====================================================================
-- SEARCH AND SIMILARITY FUNCTIONS
-- =====================================================================

-- Create virtual table for full-text search on lessons
CREATE VIRTUAL TABLE IF NOT EXISTS lessons_fts USING fts5(
    title,
    content,
    context,
    tags,
    content='lessons',
    content_rowid='id'
);

-- Create virtual table for full-text search on errors
CREATE VIRTUAL TABLE IF NOT EXISTS errors_fts USING fts5(
    title,
    message,
    stack_trace,
    context,
    resolution_description,
    tags,
    content='errors',
    content_rowid='id'
);

-- =====================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================================

-- Update timestamps on lessons table
CREATE TRIGGER IF NOT EXISTS update_lessons_timestamp
    AFTER UPDATE ON lessons
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE lessons SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps on errors table
CREATE TRIGGER IF NOT EXISTS update_errors_timestamp
    AFTER UPDATE ON errors
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE errors SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamps on projects table
CREATE TRIGGER IF NOT EXISTS update_projects_timestamp
    AFTER UPDATE ON projects
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update last_active on agents when referenced
CREATE TRIGGER IF NOT EXISTS update_agent_last_active
    AFTER INSERT ON usage_analytics
    FOR EACH ROW
    WHEN NEW.agent_id IS NOT NULL
BEGIN
    UPDATE agents SET last_active = CURRENT_TIMESTAMP WHERE id = NEW.agent_id;
END;

-- Maintain FTS indexes
CREATE TRIGGER IF NOT EXISTS lessons_fts_insert
    AFTER INSERT ON lessons
BEGIN
    INSERT INTO lessons_fts(rowid, title, content, context, tags)
    VALUES (NEW.id, NEW.title, NEW.content, NEW.context, json_extract(NEW.tags, '$'));
END;

CREATE TRIGGER IF NOT EXISTS lessons_fts_update
    AFTER UPDATE ON lessons
BEGIN
    UPDATE lessons_fts SET
        title = NEW.title,
        content = NEW.content,
        context = NEW.context,
        tags = json_extract(NEW.tags, '$')
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS lessons_fts_delete
    AFTER DELETE ON lessons
BEGIN
    DELETE FROM lessons_fts WHERE rowid = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS errors_fts_insert
    AFTER INSERT ON errors
BEGIN
    INSERT INTO errors_fts(rowid, title, message, stack_trace, context, resolution_description, tags)
    VALUES (NEW.id, NEW.title, NEW.message, NEW.stack_trace, NEW.context, NEW.resolution_description, json_extract(NEW.tags, '$'));
END;

CREATE TRIGGER IF NOT EXISTS errors_fts_update
    AFTER UPDATE ON errors
BEGIN
    UPDATE errors_fts SET
        title = NEW.title,
        message = NEW.message,
        stack_trace = NEW.stack_trace,
        context = NEW.context,
        resolution_description = NEW.resolution_description,
        tags = json_extract(NEW.tags, '$')
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS errors_fts_delete
    AFTER DELETE ON errors
BEGIN
    DELETE FROM errors_fts WHERE rowid = OLD.id;
END;

-- =====================================================================
-- INITIAL DATA AND CONFIGURATION
-- =====================================================================

-- Insert default project if not exists
INSERT OR IGNORE INTO projects (name, path, description)
VALUES ('infinite-continue-stop-hook', '/Users/jeremyparker/infinite-continue-stop-hook', 'Universal TaskManager API system');

-- =====================================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================================

-- View for active lessons with effectiveness metrics
CREATE VIEW IF NOT EXISTS active_lessons_view AS
SELECT
    l.*,
    COUNT(ua.id) as access_count,
    AVG(ela.effectiveness_score) as avg_effectiveness,
    MAX(ua.created_at) as last_accessed
FROM lessons l
LEFT JOIN usage_analytics ua ON l.id = ua.entity_id AND ua.entity_type = 'lesson'
LEFT JOIN error_lesson_associations ela ON l.id = ela.lesson_id
GROUP BY l.id
ORDER BY l.effectiveness_score DESC, l.usage_count DESC;

-- View for recent errors with resolution status
CREATE VIEW IF NOT EXISTS recent_errors_view AS
SELECT
    e.*,
    COUNT(ela.id) as lesson_count,
    MAX(ela.effectiveness_score) as best_resolution_score
FROM errors e
LEFT JOIN error_lesson_associations ela ON e.id = ela.error_id
WHERE e.created_at >= datetime('now', '-30 days')
GROUP BY e.id
ORDER BY e.created_at DESC;

-- View for agent performance summary
CREATE VIEW IF NOT EXISTS agent_performance_view AS
SELECT
    a.id,
    a.name,
    a.role,
    COUNT(DISTINCT t.id) as tasks_completed,
    COUNT(DISTINCT l.id) as lessons_created,
    COUNT(DISTINCT e.id) as errors_encountered,
    AVG(pm.metric_value) as avg_performance,
    MAX(a.last_active) as last_active
FROM agents a
LEFT JOIN tasks t ON a.id = t.assigned_agent_id AND t.status = 'completed'
LEFT JOIN lessons l ON a.id = l.agent_id
LEFT JOIN errors e ON a.id = e.agent_id
LEFT JOIN performance_metrics pm ON a.id = pm.agent_id
GROUP BY a.id
ORDER BY tasks_completed DESC, lessons_created DESC;

-- =====================================================================
-- END OF SCHEMA
-- =====================================================================