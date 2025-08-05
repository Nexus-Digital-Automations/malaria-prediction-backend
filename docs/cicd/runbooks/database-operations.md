# Database Operations Runbook

## Overview

This runbook provides procedures for database operations, maintenance, and emergency response for the Malaria Prediction Backend PostgreSQL database with TimescaleDB extensions.

## Table of Contents

1. [Database Architecture](#database-architecture)
2. [Routine Maintenance](#routine-maintenance)
3. [Migration Procedures](#migration-procedures)
4. [Backup & Recovery](#backup--recovery)
5. [Performance Troubleshooting](#performance-troubleshooting)
6. [Emergency Procedures](#emergency-procedures)
7. [Monitoring & Alerting](#monitoring--alerting)

## Database Architecture

### Primary Components
- **PostgreSQL 15**: Primary database engine
- **TimescaleDB**: Time-series extension for environmental data
- **PgBouncer**: Connection pooling
- **Streaming Replication**: Read replicas for scaling
- **WAL-G**: Continuous archiving and point-in-time recovery

### Database Schema
```sql
-- Core application tables
- users (authentication and user data)
- environmental_data (time-series environmental measurements)
- malaria_cases (historical malaria case data)
- predictions (ML model predictions and results)
- model_metadata (ML model versioning and performance)

-- TimescaleDB hypertables
- environmental_data (partitioned by time)
- predictions (partitioned by time and location)
```

### Connection Details
```bash
# Production (Primary)
DATABASE_URL=postgresql+asyncpg://username:password@db-prod.internal:5432/malaria_prediction

# Production (Read Replica)
REPLICA_URL=postgresql+asyncpg://username:password@db-replica.internal:5432/malaria_prediction

# Staging
DATABASE_URL=postgresql+asyncpg://username:password@db-staging.internal:5432/malaria_prediction_staging
```

## Routine Maintenance

### Daily Tasks

#### 1. Health Check
```bash
# Connect to database pod
kubectl exec -it postgres-0 -n malaria-prediction-production -- bash

# Basic connectivity test
psql -U postgres -d malaria_prediction -c "SELECT version();"

# Check database size
psql -U postgres -d malaria_prediction -c "
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;
"

# Check active connections
psql -U postgres -d malaria_prediction -c "
SELECT
    count(*) as active_connections,
    state,
    application_name
FROM pg_stat_activity
WHERE state = 'active'
GROUP BY state, application_name
ORDER BY active_connections DESC;
"
```

#### 2. Performance Metrics
```bash
# Top 10 slowest queries
psql -U postgres -d malaria_prediction -c "
SELECT
    query,
    calls,
    total_time,
    mean_time,
    stddev_time,
    rows
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_time DESC
LIMIT 10;
"

# Table statistics
psql -U postgres -d malaria_prediction -c "
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"
```

#### 3. TimescaleDB Maintenance
```bash
# Check hypertable statistics
psql -U postgres -d malaria_prediction -c "
SELECT
    hypertable_name,
    num_chunks,
    table_size,
    index_size,
    total_size
FROM timescaledb_information.hypertables
JOIN timescaledb_information.hypertable_detailed_size USING (hypertable_name);
"

# Compress old chunks (data older than 30 days)
psql -U postgres -d malaria_prediction -c "
SELECT compress_chunk(chunk_name)
FROM timescaledb_information.chunks
WHERE hypertable_name IN ('environmental_data', 'predictions')
  AND range_end < NOW() - INTERVAL '30 days'
  AND NOT is_compressed;
"
```

### Weekly Tasks

#### 1. Vacuum and Analyze
```bash
# Manual vacuum analyze for critical tables
psql -U postgres -d malaria_prediction -c "
VACUUM ANALYZE users;
VACUUM ANALYZE model_metadata;
"

# Check vacuum progress
psql -U postgres -d malaria_prediction -c "
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
FROM pg_stat_activity
WHERE query LIKE '%VACUUM%';
"
```

#### 2. Index Maintenance
```bash
# Check for unused indexes
psql -U postgres -d malaria_prediction -c "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND pg_relation_size(indexrelid) > 1048576  -- > 1MB
ORDER BY pg_relation_size(indexrelid) DESC;
"

# Reindex if needed (during maintenance window)
psql -U postgres -d malaria_prediction -c "
REINDEX INDEX CONCURRENTLY idx_environmental_data_time;
"
```

#### 3. Statistics Update
```bash
# Update table statistics
psql -U postgres -d malaria_prediction -c "
ANALYZE;
"

# Check if auto-analyze is working
psql -U postgres -d malaria_prediction -c "
SELECT
    schemaname,
    tablename,
    last_analyze,
    last_autoanalyze,
    analyze_count,
    autoanalyze_count
FROM pg_stat_user_tables
WHERE last_analyze < NOW() - INTERVAL '7 days'
   OR last_autoanalyze < NOW() - INTERVAL '7 days';
"
```

### Monthly Tasks

#### 1. Capacity Planning
```bash
# Database growth analysis
psql -U postgres -d malaria_prediction -c "
WITH monthly_growth AS (
    SELECT
        date_trunc('month', created_at) as month,
        count(*) as records,
        pg_size_pretty(sum(octet_length(data::text))) as data_size
    FROM environmental_data
    WHERE created_at > NOW() - INTERVAL '12 months'
    GROUP BY date_trunc('month', created_at)
    ORDER BY month
)
SELECT
    month,
    records,
    data_size,
    records - LAG(records) OVER (ORDER BY month) as record_growth,
    data_size as size_growth
FROM monthly_growth;
"
```

#### 2. Partition Management
```bash
# Drop old partitions (keep 2 years of data)
psql -U postgres -d malaria_prediction -c "
SELECT drop_chunks('environmental_data', INTERVAL '2 years');
SELECT drop_chunks('predictions', INTERVAL '2 years');
"

# Create future partitions
psql -U postgres -d malaria_prediction -c "
SELECT add_partition('environmental_data', NOW() + INTERVAL '3 months');
SELECT add_partition('predictions', NOW() + INTERVAL '3 months');
"
```

## Migration Procedures

### Pre-Migration Checklist
- [ ] Review migration scripts for syntax errors
- [ ] Test migration on staging environment
- [ ] Verify rollback procedures
- [ ] Schedule maintenance window
- [ ] Notify stakeholders
- [ ] Create database backup

### Running Migrations

#### 1. Automated Migration (CI/CD)
```bash
# Migrations are automatically run during deployment
# See: k8s/migration-job.yaml

# Check migration status
kubectl logs job/db-migration-<migration-id> -n malaria-prediction-production

# Verify migration completion
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT version_num FROM alembic_version;
  "
```

#### 2. Manual Migration
```bash
# Connect to database pod
kubectl exec -it postgres-0 -n malaria-prediction-production -- bash

# Check current version
alembic current

# List available migrations
alembic heads

# Run specific migration
alembic upgrade <revision>

# Run all pending migrations
alembic upgrade head
```

#### 3. Migration Rollback
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>

# Check rollback status
alembic current
```

### Large Data Migrations

#### 1. Batch Processing
```sql
-- Example: Migrating large table with batching
DO $$
DECLARE
    batch_size INT := 10000;
    total_rows INT;
    processed INT := 0;
BEGIN
    SELECT count(*) INTO total_rows FROM large_table WHERE needs_migration = true;

    WHILE processed < total_rows LOOP
        WITH batch AS (
            SELECT id FROM large_table
            WHERE needs_migration = true
            LIMIT batch_size
        )
        UPDATE large_table
        SET
            new_column = transform_data(old_column),
            needs_migration = false
        WHERE id IN (SELECT id FROM batch);

        processed := processed + batch_size;
        RAISE NOTICE 'Processed % of % rows', processed, total_rows;

        -- Pause to avoid overwhelming the database
        PERFORM pg_sleep(1);
    END LOOP;
END $$;
```

#### 2. Online Schema Changes
```sql
-- Use pt-online-schema-change equivalent for PostgreSQL
-- Or pg_repack for table reorganization

-- Example: Adding index concurrently
CREATE INDEX CONCURRENTLY idx_new_column ON large_table(new_column);

-- Example: Adding column with default (11+ feature)
ALTER TABLE large_table ADD COLUMN new_col TEXT DEFAULT 'default_value';
```

## Backup & Recovery

### Backup Strategy

#### 1. Continuous WAL Archival
```bash
# Check WAL archiving status
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -c "
  SELECT
    name,
    setting,
    context
  FROM pg_settings
  WHERE name IN ('archive_mode', 'archive_command', 'wal_level');
  "

# Check archive status
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -c "
  SELECT
    last_archived_wal,
    last_archived_time,
    last_failed_wal,
    last_failed_time,
    stats_reset
  FROM pg_stat_archiver;
  "
```

#### 2. Base Backups
```bash
# Create base backup using WAL-G
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  wal-g backup-push /var/lib/postgresql/data

# List available backups
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  wal-g backup-list

# Verify backup integrity
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  wal-g backup-fetch /tmp/backup-verify LATEST
```

#### 3. Logical Backups
```bash
# Full database dump
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  pg_dump -U postgres -d malaria_prediction \
  --format=custom \
  --compress=9 \
  --file=/backups/malaria_prediction_$(date +%Y%m%d_%H%M%S).dump

# Schema-only backup
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  pg_dump -U postgres -d malaria_prediction \
  --schema-only \
  --file=/backups/schema_$(date +%Y%m%d_%H%M%S).sql

# Data-only backup
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  pg_dump -U postgres -d malaria_prediction \
  --data-only \
  --format=custom \
  --file=/backups/data_$(date +%Y%m%d_%H%M%S).dump
```

### Recovery Procedures

#### 1. Point-in-Time Recovery (PITR)
```bash
# Stop PostgreSQL
kubectl scale statefulset postgres --replicas=0 -n malaria-prediction-production

# Restore from base backup
kubectl exec -it postgres-recovery -- \
  wal-g backup-fetch /var/lib/postgresql/data LATEST

# Create recovery configuration
kubectl exec -it postgres-recovery -- \
  cat > /var/lib/postgresql/data/recovery.conf << EOF
restore_command = 'wal-g wal-fetch %f %p'
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'
EOF

# Start PostgreSQL in recovery mode
kubectl scale statefulset postgres-recovery --replicas=1

# Monitor recovery progress
kubectl logs -f postgres-recovery-0 | grep -i recovery
```

#### 2. Logical Restore
```bash
# Drop and recreate database (if needed)
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -c "
  DROP DATABASE IF EXISTS malaria_prediction_restore;
  CREATE DATABASE malaria_prediction_restore;
  "

# Restore from dump
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  pg_restore -U postgres -d malaria_prediction_restore \
  --verbose \
  --jobs=4 \
  /backups/malaria_prediction_20240115_143000.dump

# Verify restoration
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction_restore -c "
  SELECT count(*) FROM environmental_data;
  SELECT count(*) FROM users;
  SELECT count(*) FROM predictions;
  "
```

#### 3. Streaming Replica Promotion
```bash
# In case of primary failure, promote replica
kubectl exec -it postgres-replica-0 -n malaria-prediction-production -- \
  pg_ctl promote -D /var/lib/postgresql/data

# Update application configuration to point to new primary
kubectl set env deployment/malaria-predictor-api \
  DATABASE_URL="postgresql+asyncpg://user:pass@postgres-replica:5432/malaria_prediction" \
  -n malaria-prediction-production

# Verify new primary is accepting writes
kubectl exec -it postgres-replica-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT pg_is_in_recovery();
  "
```

## Performance Troubleshooting

### Query Performance Issues

#### 1. Identify Slow Queries
```bash
# Top 10 slowest queries by mean time
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    query,
    calls,
    total_time,
    mean_time,
    stddev_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
  FROM pg_stat_statements
  WHERE query NOT LIKE '%pg_stat_statements%'
  ORDER BY mean_time DESC
  LIMIT 10;
  "

# Currently running slow queries
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    client_addr
  FROM pg_stat_activity
  WHERE now() - pg_stat_activity.query_start > interval '30 seconds'
    AND state = 'active'
  ORDER BY duration DESC;
  "
```

#### 2. Query Optimization
```bash
# Analyze specific query
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
  SELECT * FROM environmental_data
  WHERE location_id = 'loc_001'
    AND timestamp > NOW() - INTERVAL '30 days';
  "

# Check missing indexes
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    seq_tup_read / seq_scan AS avg_seq_read
  FROM pg_stat_user_tables
  WHERE seq_scan > 0
  ORDER BY seq_tup_read DESC;
  "
```

#### 3. Index Analysis
```bash
# Index usage statistics
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
  FROM pg_stat_user_indexes
  ORDER BY idx_scan DESC;
  "

# Duplicate indexes
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    pg_size_pretty(SUM(pg_relation_size(idx))::BIGINT) AS size,
    (array_agg(indexrelname))[1] AS idx1,
    (array_agg(indexrelname))[2] AS idx2,
    (array_agg(indexrelname))[3] AS idx3,
    (array_agg(indexrelname))[4] AS idx4
  FROM (
    SELECT
      indexrelname,
      pg_class.relname,
      indkey::text,
      indclass::text,
      indkey,
      indclass,
      pg_class.oid as idx
    FROM pg_index
    JOIN pg_class ON pg_class.oid = pg_index.indexrelid
    WHERE indisunique IS FALSE
  ) sub
  GROUP BY indkey::text, indclass::text, relname
  HAVING COUNT(*) > 1
  ORDER BY SUM(pg_relation_size(idx)) DESC;
  "
```

### Connection Issues

#### 1. Connection Pool Analysis
```bash
# Check PgBouncer status
kubectl exec -it pgbouncer-0 -n malaria-prediction-production -- \
  psql -h localhost -p 6432 -U pgbouncer pgbouncer -c "SHOW POOLS;"

kubectl exec -it pgbouncer-0 -n malaria-prediction-production -- \
  psql -h localhost -p 6432 -U pgbouncer pgbouncer -c "SHOW CLIENTS;"

kubectl exec -it pgbouncer-0 -n malaria-prediction-production -- \
  psql -h localhost -p 6432 -U pgbouncer pgbouncer -c "SHOW SERVERS;"
```

#### 2. Connection Limit Issues
```bash
# Check current connections vs limits
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    setting::int as max_connections,
    (SELECT count(*) FROM pg_stat_activity) as current_connections,
    setting::int - (SELECT count(*) FROM pg_stat_activity) as remaining_connections
  FROM pg_settings
  WHERE name = 'max_connections';
  "

# Identify connection hogs
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    application_name,
    client_addr,
    count(*) as connection_count,
    max(now() - backend_start) as longest_connection
  FROM pg_stat_activity
  GROUP BY application_name, client_addr
  ORDER BY connection_count DESC;
  "
```

### Lock Issues

#### 1. Identify Blocking Queries
```bash
# Current locks and blocking relationships
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS current_statement_in_blocking_process,
    blocked_activity.application_name AS blocked_application,
    blocking_activity.application_name AS blocking_application
  FROM pg_catalog.pg_locks blocked_locks
  JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
  JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
  JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
  WHERE NOT blocked_locks.granted;
  "
```

#### 2. Kill Blocking Queries
```bash
# Kill specific blocking query (use with caution)
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT pg_terminate_backend(<blocking_pid>);
  "

# Kill all idle-in-transaction connections older than 5 minutes
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    pid,
    now() - state_change as duration,
    pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle in transaction'
    AND now() - state_change > interval '5 minutes';
  "
```

## Emergency Procedures

### Database Corruption

#### 1. Detect Corruption
```bash
# Check for corruption
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT
    datname,
    pg_database_size(datname) as size,
    stats_reset
  FROM pg_database
  JOIN pg_stat_database USING (datname)
  WHERE datname = 'malaria_prediction';
  "

# Verify table integrity
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  \d+ environmental_data
  SELECT count(*) FROM environmental_data;
  "
```

#### 2. Emergency Read-Only Mode
```bash
# Set database to read-only
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  ALTER DATABASE malaria_prediction SET default_transaction_read_only = on;
  "

# Restart database to apply
kubectl rollout restart statefulset/postgres -n malaria-prediction-production
```

### Out of Disk Space

#### 1. Immediate Response
```bash
# Check disk usage
kubectl exec -it postgres-0 -n malaria-prediction-production -- df -h

# Clean up temporary files
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  find /var/lib/postgresql/data/base -name "pgsql_tmp*" -delete

# Clean up old WAL files (if archiving is working)
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -c "SELECT pg_switch_wal();"
```

#### 2. Emergency Cleanup
```bash
# Drop old partitions
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT drop_chunks('environmental_data', INTERVAL '6 months');
  "

# Vacuum to reclaim space
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "VACUUM FULL;"
```

### Primary Database Failure

#### 1. Promote Replica
```bash
# Check replica status
kubectl exec -it postgres-replica-0 -n malaria-prediction-production -- \
  psql -U postgres -d malaria_prediction -c "
  SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();
  "

# Promote replica to primary
kubectl exec -it postgres-replica-0 -n malaria-prediction-production -- \
  pg_ctl promote -D /var/lib/postgresql/data

# Update application configuration
kubectl patch configmap app-config -n malaria-prediction-production --patch '
{
  "data": {
    "DATABASE_URL": "postgresql+asyncpg://user:pass@postgres-replica:5432/malaria_prediction"
  }
}'

# Restart application pods
kubectl rollout restart deployment/malaria-predictor-api -n malaria-prediction-production
```

#### 2. Emergency Backup
```bash
# If primary is still accessible, create emergency backup
kubectl exec -it postgres-0 -n malaria-prediction-production -- \
  pg_dump -U postgres -d malaria_prediction \
  --format=custom \
  --compress=9 \
  --file=/emergency-backup/malaria_prediction_emergency_$(date +%Y%m%d_%H%M%S).dump
```

## Monitoring & Alerting

### Key Metrics to Monitor

#### 1. Database Health
```bash
# Connection count
SELECT count(*) FROM pg_stat_activity;

# Database size
SELECT pg_size_pretty(pg_database_size('malaria_prediction'));

# Replication lag (on replica)
SELECT
  now() - pg_last_xact_replay_timestamp() AS replication_lag;
```

#### 2. Performance Metrics
```bash
# Query performance
SELECT avg(mean_time) FROM pg_stat_statements;

# Cache hit ratio
SELECT
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;

# Transaction rate
SELECT
  xact_commit + xact_rollback as total_transactions,
  xact_commit,
  xact_rollback
FROM pg_stat_database
WHERE datname = 'malaria_prediction';
```

### Alert Thresholds

#### Critical Alerts
- Database down: Immediate
- Replication lag > 60 seconds: Immediate
- Disk usage > 90%: Immediate
- Connection count > 80% of max: Immediate

#### Warning Alerts
- Query time > 5 seconds: 5 minutes
- Cache hit ratio < 95%: 10 minutes
- Disk usage > 80%: 15 minutes
- Lock wait time > 30 seconds: 5 minutes

### Emergency Contacts

- **DBA On-Call**: +1-555-DBA-ONCALL
- **DevOps Team**: +1-555-DEVOPS
- **Platform Team**: +1-555-PLATFORM
- **Database Vendor Support**: +1-555-POSTGRES-SUPPORT

### Escalation Procedures

1. **Level 1 (0-15 min)**: On-call DBA
2. **Level 2 (15-30 min)**: Senior DBA + DevOps Lead
3. **Level 3 (30+ min)**: Database vendor support + Platform team
