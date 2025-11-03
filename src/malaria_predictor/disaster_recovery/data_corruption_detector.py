#!/usr/bin/env python3
"""
Data Corruption Detection and Recovery System for Malaria Prediction System.

This module provides comprehensive data corruption detection and automated recovery:
- Real-time data integrity monitoring
- Anomaly detection in time-series data
- Checksums and data validation
- Automated corruption recovery procedures
- Data quality metrics and alerting
- Point-in-time recovery capabilities
"""

import asyncio
import json
import logging
import statistics
from datetime import datetime
from typing import Any

import asyncpg  # type: ignore[import-untyped]
from pydantic import BaseModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/malaria-prediction/data-corruption.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DataQualityMetrics(BaseModel):
    """Data quality metrics model."""

    table_name: str
    total_records: int
    null_count: int
    duplicate_count: int
    outlier_count: int
    data_range_min: float | None = None
    data_range_max: float | None = None
    data_checksum: str
    last_updated: datetime
    quality_score: float  # 0.0 to 1.0


class CorruptionAlert(BaseModel):
    """Data corruption alert model."""

    alert_id: str
    table_name: str
    corruption_type: str
    severity: str  # low, medium, high, critical
    description: str
    detected_at: datetime
    affected_records: int
    suggested_action: str
    recovery_estimate: str


class DataIntegrityChecker:
    """Checks data integrity and detects corruption patterns."""

    def __init__(self, database_url: str):
        """Initialize data integrity checker.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.corruption_alerts: list[CorruptionAlert] = []

    async def check_table_integrity(self, table_name: str) -> DataQualityMetrics:
        """Check integrity of a specific table.

        Args:
            table_name: Name of table to check

        Returns:
            Data quality metrics for the table
        """
        try:
            conn = await asyncpg.connect(self.database_url)

            # Get basic statistics
            total_records = await conn.fetchval(f"SELECT count(*) FROM {table_name}")

            # Check for nulls in critical columns
            null_counts = await conn.fetch(
                f"""
                SELECT column_name,
                       SUM(CASE WHEN column_value IS NULL THEN 1 ELSE 0 END) as null_count
                FROM (
                    SELECT column_name,
                           CASE column_name
                               WHEN 'id' THEN id::text
                               WHEN 'timestamp' THEN timestamp::text
                               WHEN 'latitude' THEN latitude::text
                               WHEN 'longitude' THEN longitude::text
                               ELSE NULL
                           END as column_value
                    FROM information_schema.columns
                    CROSS JOIN {table_name}
                    WHERE table_name = '{table_name}'
                    AND column_name IN ('id', 'timestamp', 'latitude', 'longitude')
                ) subquery
                GROUP BY column_name
            """
            )

            total_nulls = sum(row["null_count"] for row in null_counts)

            # Check for duplicates (if table has timestamp and coordinates)
            try:
                duplicate_count = await conn.fetchval(
                    f"""
                    SELECT count(*) - count(DISTINCT (timestamp, latitude, longitude))
                    FROM {table_name}
                    WHERE timestamp IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
                """
                )
                if duplicate_count is None:
                    duplicate_count = 0
            except Exception:
                duplicate_count = 0

            # Calculate data checksum
            checksum_data = await conn.fetchval(
                f"""
                SELECT md5(string_agg(
                    COALESCE({table_name}::text, 'NULL'), '|'
                    ORDER BY COALESCE(id::text, timestamp::text)
                ))
                FROM {table_name}
            """
            )

            # Get data range for numeric columns
            data_range_min = None
            data_range_max = None

            try:
                # Attempt to get range for numeric data (temperature, precipitation, etc.)
                numeric_columns = await conn.fetch(
                    f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    AND data_type IN ('numeric', 'real', 'double precision', 'integer', 'bigint')
                    AND column_name NOT IN ('id', 'latitude', 'longitude')
                    LIMIT 1
                """
                )

                if numeric_columns:
                    col_name = numeric_columns[0]["column_name"]
                    range_data = await conn.fetchrow(
                        f"""
                        SELECT min({col_name}) as min_val, max({col_name}) as max_val
                        FROM {table_name}
                        WHERE {col_name} IS NOT NULL
                    """
                    )
                    if range_data:
                        data_range_min = (
                            float(range_data["min_val"])
                            if range_data["min_val"] is not None
                            else None
                        )
                        data_range_max = (
                            float(range_data["max_val"])
                            if range_data["max_val"] is not None
                            else None
                        )
            except Exception as e:
                logger.warning(f"Could not calculate data range for {table_name}: {e}")

            # Detect outliers using IQR method for numeric columns
            outlier_count = 0
            try:
                if numeric_columns:
                    col_name = numeric_columns[0]["column_name"]
                    percentiles = await conn.fetchrow(
                        f"""
                        SELECT
                            percentile_cont(0.25) WITHIN GROUP (ORDER BY {col_name}) as q1,
                            percentile_cont(0.75) WITHIN GROUP (ORDER BY {col_name}) as q3
                        FROM {table_name}
                        WHERE {col_name} IS NOT NULL
                    """
                    )

                    if (
                        percentiles
                        and percentiles["q1"] is not None
                        and percentiles["q3"] is not None
                    ):
                        q1, q3 = float(percentiles["q1"]), float(percentiles["q3"])
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr

                        outlier_count = await conn.fetchval(
                            f"""
                            SELECT count(*)
                            FROM {table_name}
                            WHERE {col_name} < {lower_bound} OR {col_name} > {upper_bound}
                        """
                        )
            except Exception as e:
                logger.warning(f"Could not calculate outliers for {table_name}: {e}")

            await conn.close()

            # Calculate quality score
            quality_score = self._calculate_quality_score(
                total_records, total_nulls, duplicate_count, outlier_count
            )

            return DataQualityMetrics(
                table_name=table_name,
                total_records=total_records,
                null_count=total_nulls,
                duplicate_count=duplicate_count,
                outlier_count=outlier_count,
                data_range_min=data_range_min,
                data_range_max=data_range_max,
                data_checksum=checksum_data or "",
                last_updated=datetime.now(),
                quality_score=quality_score,
            )

        except Exception as e:
            logger.error(f"Failed to check integrity for table {table_name}: {e}")
            raise

    def _calculate_quality_score(
        self,
        total_records: int,
        null_count: int,
        duplicate_count: int,
        outlier_count: int,
    ) -> float:
        """Calculate data quality score (0.0 to 1.0).

        Args:
            total_records: Total number of records
            null_count: Number of null values in critical columns
            duplicate_count: Number of duplicate records
            outlier_count: Number of outlier values

        Returns:
            Quality score between 0.0 and 1.0
        """
        if total_records == 0:
            return 0.0

        # Calculate penalties
        null_penalty = min(null_count / total_records, 0.5)  # Max 50% penalty for nulls
        duplicate_penalty = min(
            duplicate_count / total_records, 0.3
        )  # Max 30% penalty for duplicates
        outlier_penalty = min(
            outlier_count / total_records, 0.2
        )  # Max 20% penalty for outliers

        # Calculate final score
        quality_score = 1.0 - (null_penalty + duplicate_penalty + outlier_penalty)
        return max(quality_score, 0.0)

    async def detect_corruption_patterns(
        self, table_name: str
    ) -> list[CorruptionAlert]:
        """Detect corruption patterns in table data.

        Args:
            table_name: Name of table to analyze

        Returns:
            List of corruption alerts
        """
        alerts = []

        try:
            conn = await asyncpg.connect(self.database_url)

            # Check for sudden data drops
            recent_counts = await conn.fetch(
                f"""
                SELECT date_trunc('hour', timestamp) as hour_bucket,
                       count(*) as record_count
                FROM {table_name}
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY hour_bucket
                ORDER BY hour_bucket DESC
                LIMIT 24
            """
            )

            if len(recent_counts) >= 5:
                counts = [row["record_count"] for row in recent_counts]
                avg_count = statistics.mean(counts)
                recent_avg = statistics.mean(counts[:3])

                # Alert if recent average is less than 50% of overall average
                if recent_avg < avg_count * 0.5 and avg_count > 0:
                    alerts.append(
                        CorruptionAlert(
                            alert_id=f"data_drop_{table_name}_{datetime.now().timestamp()}",
                            table_name=table_name,
                            corruption_type="data_drop",
                            severity="high",
                            description=f"Significant drop in data ingestion rate detected. "
                            f"Recent average: {recent_avg:.1f}, Expected: {avg_count:.1f}",
                            detected_at=datetime.now(),
                            affected_records=int(avg_count - recent_avg),
                            suggested_action="Check data ingestion pipeline and external APIs",
                            recovery_estimate="1-2 hours",
                        )
                    )

            # Check for future timestamps (data corruption indicator)
            future_records = await conn.fetchval(
                f"""
                SELECT count(*)
                FROM {table_name}
                WHERE timestamp > NOW() + INTERVAL '1 hour'
            """
            )

            if future_records > 0:
                alerts.append(
                    CorruptionAlert(
                        alert_id=f"future_timestamps_{table_name}_{datetime.now().timestamp()}",
                        table_name=table_name,
                        corruption_type="invalid_timestamps",
                        severity="medium",
                        description=f"Found {future_records} records with future timestamps",
                        detected_at=datetime.now(),
                        affected_records=future_records,
                        suggested_action="Clean up invalid timestamp data and check data source",
                        recovery_estimate="30 minutes",
                    )
                )

            # Check for coordinate anomalies (if geographic data)
            if table_name in ["environmental_data", "malaria_risk_data"]:
                invalid_coordinates = await conn.fetchval(
                    f"""
                    SELECT count(*)
                    FROM {table_name}
                    WHERE latitude < -90 OR latitude > 90
                       OR longitude < -180 OR longitude > 180
                       OR (latitude = 0 AND longitude = 0)
                """
                )

                if invalid_coordinates > 0:
                    alerts.append(
                        CorruptionAlert(
                            alert_id=f"invalid_coords_{table_name}_{datetime.now().timestamp()}",
                            table_name=table_name,
                            corruption_type="invalid_coordinates",
                            severity="high",
                            description=f"Found {invalid_coordinates} records with invalid coordinates",
                            detected_at=datetime.now(),
                            affected_records=invalid_coordinates,
                            suggested_action="Remove or correct invalid coordinate data",
                            recovery_estimate="1 hour",
                        )
                    )

            # Check for extreme value anomalies in environmental data
            if table_name == "environmental_data":
                extreme_values = await conn.fetchval(
                    f"""
                    SELECT count(*)
                    FROM {table_name}
                    WHERE temperature_2m < -50 OR temperature_2m > 70
                       OR precipitation < 0 OR precipitation > 1000
                       OR humidity < 0 OR humidity > 100
                """
                )

                if extreme_values > 0:
                    alerts.append(
                        CorruptionAlert(
                            alert_id=f"extreme_values_{table_name}_{datetime.now().timestamp()}",
                            table_name=table_name,
                            corruption_type="extreme_values",
                            severity="medium",
                            description=f"Found {extreme_values} records with physically impossible values",
                            detected_at=datetime.now(),
                            affected_records=extreme_values,
                            suggested_action="Review and clean extreme value data",
                            recovery_estimate="45 minutes",
                        )
                    )

            await conn.close()

        except Exception as e:
            logger.error(f"Failed to detect corruption patterns in {table_name}: {e}")

        return alerts

    async def check_data_consistency(self) -> list[CorruptionAlert]:
        """Check data consistency across related tables.

        Returns:
            List of consistency alerts
        """
        alerts = []

        try:
            conn = await asyncpg.connect(self.database_url)

            # Check for orphaned prediction records
            orphaned_predictions = await conn.fetchval(
                """
                SELECT count(*)
                FROM predictions p
                LEFT JOIN environmental_data e ON (
                    p.latitude = e.latitude AND
                    p.longitude = e.longitude AND
                    date_trunc('day', p.prediction_date) = date_trunc('day', e.timestamp)
                )
                WHERE e.id IS NULL
                AND p.created_at >= NOW() - INTERVAL '7 days'
            """
            )

            if orphaned_predictions > 0:
                alerts.append(
                    CorruptionAlert(
                        alert_id=f"orphaned_predictions_{datetime.now().timestamp()}",
                        table_name="predictions",
                        corruption_type="referential_integrity",
                        severity="medium",
                        description=f"Found {orphaned_predictions} predictions without corresponding environmental data",
                        detected_at=datetime.now(),
                        affected_records=orphaned_predictions,
                        suggested_action="Rebuild predictions or restore missing environmental data",
                        recovery_estimate="2 hours",
                    )
                )

            # Check for missing recent environmental data
            hours_without_data = await conn.fetchval(
                """
                SELECT count(*)
                FROM generate_series(
                    NOW() - INTERVAL '24 hours',
                    NOW(),
                    INTERVAL '1 hour'
                ) AS expected_hour
                LEFT JOIN (
                    SELECT DISTINCT date_trunc('hour', timestamp) as data_hour
                    FROM environmental_data
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                ) ed ON expected_hour = ed.data_hour
                WHERE ed.data_hour IS NULL
            """
            )

            if hours_without_data > 3:  # More than 3 hours missing is concerning
                alerts.append(
                    CorruptionAlert(
                        alert_id=f"missing_environmental_data_{datetime.now().timestamp()}",
                        table_name="environmental_data",
                        corruption_type="data_gaps",
                        severity="high",
                        description=f"Missing environmental data for {hours_without_data} hours in last 24h",
                        detected_at=datetime.now(),
                        affected_records=hours_without_data,
                        suggested_action="Check data ingestion services and restore missing data",
                        recovery_estimate="1-3 hours",
                    )
                )

            await conn.close()

        except Exception as e:
            logger.error(f"Failed to check data consistency: {e}")

        return alerts


class DataCorruptionRecovery:
    """Handles automated data corruption recovery procedures."""

    def __init__(
        self,
        database_url: str,
        backup_orchestrator_path: str,
        max_auto_recovery_records: int = 1000,
    ):
        """Initialize corruption recovery system.

        Args:
            database_url: PostgreSQL connection URL
            backup_orchestrator_path: Path to backup orchestrator script
            max_auto_recovery_records: Maximum records to auto-recover
        """
        self.database_url = database_url
        self.backup_orchestrator_path = backup_orchestrator_path
        self.max_auto_recovery_records = max_auto_recovery_records

    async def recover_from_corruption(self, alert: CorruptionAlert) -> dict[str, Any]:
        """Attempt automated recovery from corruption.

        Args:
            alert: Corruption alert to recover from

        Returns:
            Recovery result dictionary
        """
        recovery_result = {
            "alert_id": alert.alert_id,
            "recovery_attempted": True,
            "recovery_successful": False,
            "records_recovered": 0,
            "recovery_method": None,
            "recovery_time": datetime.now(),
            "manual_intervention_required": False,
        }

        try:
            if alert.corruption_type == "invalid_timestamps":
                recovery_result = await self._recover_invalid_timestamps(
                    alert, recovery_result
                )

            elif alert.corruption_type == "invalid_coordinates":
                recovery_result = await self._recover_invalid_coordinates(
                    alert, recovery_result
                )

            elif alert.corruption_type == "extreme_values":
                recovery_result = await self._recover_extreme_values(
                    alert, recovery_result
                )

            elif alert.corruption_type == "data_gaps":
                recovery_result = await self._recover_data_gaps(alert, recovery_result)

            else:
                recovery_result["manual_intervention_required"] = True
                recovery_result["recovery_method"] = "manual_review_required"
                logger.warning(
                    f"Corruption type {alert.corruption_type} requires manual intervention"
                )

        except Exception as e:
            logger.error(f"Recovery failed for alert {alert.alert_id}: {e}")
            recovery_result["recovery_error"] = str(e)
            recovery_result["manual_intervention_required"] = True

        return recovery_result

    async def _recover_invalid_timestamps(
        self, alert: CorruptionAlert, recovery_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Recover from invalid timestamp corruption."""
        if alert.affected_records > self.max_auto_recovery_records:
            recovery_result["manual_intervention_required"] = True
            recovery_result["recovery_method"] = "too_many_records_for_auto_recovery"
            return recovery_result

        conn = await asyncpg.connect(self.database_url)

        # Remove records with future timestamps
        deleted_count = await conn.fetchval(
            f"""
            DELETE FROM {alert.table_name}
            WHERE timestamp > NOW() + INTERVAL '1 hour'
            RETURNING count(*)
        """
        )

        await conn.close()

        recovery_result["recovery_successful"] = True
        recovery_result["records_recovered"] = deleted_count or 0
        recovery_result["recovery_method"] = "delete_invalid_records"

        logger.info(
            f"Recovered from invalid timestamps: deleted {deleted_count} records"
        )
        return recovery_result

    async def _recover_invalid_coordinates(
        self, alert: CorruptionAlert, recovery_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Recover from invalid coordinate corruption."""
        if alert.affected_records > self.max_auto_recovery_records:
            recovery_result["manual_intervention_required"] = True
            recovery_result["recovery_method"] = "too_many_records_for_auto_recovery"
            return recovery_result

        conn = await asyncpg.connect(self.database_url)

        # Delete records with invalid coordinates
        deleted_count = await conn.fetchval(
            f"""
            DELETE FROM {alert.table_name}
            WHERE latitude < -90 OR latitude > 90
               OR longitude < -180 OR longitude > 180
               OR (latitude = 0 AND longitude = 0)
            RETURNING count(*)
        """
        )

        await conn.close()

        recovery_result["recovery_successful"] = True
        recovery_result["records_recovered"] = deleted_count or 0
        recovery_result["recovery_method"] = "delete_invalid_coordinates"

        logger.info(
            f"Recovered from invalid coordinates: deleted {deleted_count} records"
        )
        return recovery_result

    async def _recover_extreme_values(
        self, alert: CorruptionAlert, recovery_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Recover from extreme value corruption."""
        if alert.affected_records > self.max_auto_recovery_records:
            recovery_result["manual_intervention_required"] = True
            recovery_result["recovery_method"] = "too_many_records_for_auto_recovery"
            return recovery_result

        conn = await asyncpg.connect(self.database_url)

        # Set extreme values to NULL (will be handled by data processing pipeline)
        updated_count = await conn.fetchval(
            f"""
            UPDATE {alert.table_name}
            SET temperature_2m = CASE
                    WHEN temperature_2m < -50 OR temperature_2m > 70 THEN NULL
                    ELSE temperature_2m
                END,
                precipitation = CASE
                    WHEN precipitation < 0 OR precipitation > 1000 THEN NULL
                    ELSE precipitation
                END,
                humidity = CASE
                    WHEN humidity < 0 OR humidity > 100 THEN NULL
                    ELSE humidity
                END
            WHERE temperature_2m < -50 OR temperature_2m > 70
               OR precipitation < 0 OR precipitation > 1000
               OR humidity < 0 OR humidity > 100
            RETURNING count(*)
        """
        )

        await conn.close()

        recovery_result["recovery_successful"] = True
        recovery_result["records_recovered"] = updated_count or 0
        recovery_result["recovery_method"] = "nullify_extreme_values"

        logger.info(f"Recovered from extreme values: updated {updated_count} records")
        return recovery_result

    async def _recover_data_gaps(
        self, alert: CorruptionAlert, recovery_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Recover from data gaps by triggering data re-ingestion."""
        # This would trigger the data ingestion pipeline to re-fetch missing data
        # For now, we'll mark it as requiring manual intervention
        recovery_result["manual_intervention_required"] = True
        recovery_result["recovery_method"] = "trigger_data_ingestion_required"

        logger.info("Data gap recovery requires triggering data ingestion pipeline")
        return recovery_result

    async def create_recovery_point(self, table_name: str, description: str) -> str:
        """Create a recovery point before attempting fixes.

        Args:
            table_name: Table to create recovery point for
            description: Description of the recovery point

        Returns:
            Recovery point identifier
        """
        recovery_id = (
            f"recovery_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        try:
            # Create a backup of the table
            conn = await asyncpg.connect(self.database_url)

            # Create recovery table
            await conn.execute(
                f"""
                CREATE TABLE {recovery_id} AS
                SELECT * FROM {table_name}
            """
            )

            # Add metadata
            await conn.execute(
                f"""
                COMMENT ON TABLE {recovery_id} IS
                'Recovery point created {datetime.now().isoformat()}: {description}'
            """
            )

            await conn.close()

            logger.info(f"Created recovery point: {recovery_id}")
            return recovery_id

        except Exception as e:
            logger.error(f"Failed to create recovery point: {e}")
            raise

    async def restore_from_recovery_point(
        self, recovery_id: str, target_table: str
    ) -> bool:
        """Restore table from recovery point.

        Args:
            recovery_id: Recovery point identifier
            target_table: Target table to restore

        Returns:
            True if restoration successful
        """
        try:
            conn = await asyncpg.connect(self.database_url)

            # Verify recovery point exists
            recovery_exists = await conn.fetchval(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = '{recovery_id}'
                )
            """
            )

            if not recovery_exists:
                logger.error(f"Recovery point {recovery_id} not found")
                return False

            # Backup current table
            backup_name = (
                f"{target_table}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            await conn.execute(
                f"CREATE TABLE {backup_name} AS SELECT * FROM {target_table}"
            )

            # Restore from recovery point
            await conn.execute(f"TRUNCATE TABLE {target_table}")
            await conn.execute(
                f"INSERT INTO {target_table} SELECT * FROM {recovery_id}"
            )

            await conn.close()

            logger.info(f"Restored {target_table} from recovery point {recovery_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore from recovery point {recovery_id}: {e}")
            return False


class DataCorruptionMonitor:
    """Main monitoring service for data corruption detection and recovery."""

    def __init__(
        self,
        database_url: str,
        backup_orchestrator_path: str,
        monitoring_interval: int = 300,  # 5 minutes
        alert_webhook_url: str | None = None,
    ):
        """Initialize corruption monitor.

        Args:
            database_url: PostgreSQL connection URL
            backup_orchestrator_path: Path to backup orchestrator
            monitoring_interval: Monitoring interval in seconds
            alert_webhook_url: URL for sending alerts
        """
        self.database_url = database_url
        self.monitoring_interval = monitoring_interval
        self.alert_webhook_url = alert_webhook_url

        self.integrity_checker = DataIntegrityChecker(database_url)
        self.corruption_recovery = DataCorruptionRecovery(
            database_url, backup_orchestrator_path
        )

        self.monitored_tables = [
            "environmental_data",
            "malaria_risk_data",
            "predictions",
            "worldpop_data",
            "modis_data",
        ]

        self.baseline_metrics: dict[str, DataQualityMetrics] = {}
        self.active_alerts: list[CorruptionAlert] = []

    async def establish_baseline_metrics(self) -> None:
        """Establish baseline metrics for all monitored tables."""
        logger.info("Establishing baseline metrics for data corruption detection")

        for table_name in self.monitored_tables:
            try:
                metrics = await self.integrity_checker.check_table_integrity(table_name)
                self.baseline_metrics[table_name] = metrics
                logger.info(
                    f"Baseline established for {table_name}: quality score {metrics.quality_score:.3f}"
                )
            except Exception as e:
                logger.error(f"Failed to establish baseline for {table_name}: {e}")

    async def run_corruption_scan(self) -> dict[str, Any]:
        """Run comprehensive corruption detection scan.

        Returns:
            Scan results summary
        """
        scan_results = {
            "scan_timestamp": datetime.now(),
            "tables_scanned": [],
            "alerts_generated": [],
            "recoveries_attempted": [],
            "overall_health_score": 0.0,
        }

        all_quality_scores = []

        # Check each monitored table
        for table_name in self.monitored_tables:
            try:
                # Check table integrity
                current_metrics = await self.integrity_checker.check_table_integrity(
                    table_name
                )
                scan_results["tables_scanned"].append(
                    {
                        "table_name": table_name,
                        "quality_score": current_metrics.quality_score,
                        "total_records": current_metrics.total_records,
                    }
                )
                all_quality_scores.append(current_metrics.quality_score)

                # Compare with baseline if available
                if table_name in self.baseline_metrics:
                    baseline = self.baseline_metrics[table_name]

                    # Check for significant quality degradation
                    if current_metrics.quality_score < baseline.quality_score * 0.8:
                        alert = CorruptionAlert(
                            alert_id=f"quality_degradation_{table_name}_{datetime.now().timestamp()}",
                            table_name=table_name,
                            corruption_type="quality_degradation",
                            severity="medium",
                            description=f"Data quality degraded from {baseline.quality_score:.3f} to {current_metrics.quality_score:.3f}",
                            detected_at=datetime.now(),
                            affected_records=current_metrics.total_records,
                            suggested_action="Investigate recent data changes and ingestion processes",
                            recovery_estimate="1-2 hours",
                        )
                        self.active_alerts.append(alert)
                        scan_results["alerts_generated"].append(alert.dict())

                # Detect corruption patterns
                pattern_alerts = (
                    await self.integrity_checker.detect_corruption_patterns(table_name)
                )
                for alert in pattern_alerts:
                    self.active_alerts.append(alert)
                    scan_results["alerts_generated"].append(alert.dict())

            except Exception as e:
                logger.error(f"Failed to scan table {table_name}: {e}")

        # Check cross-table consistency
        consistency_alerts = await self.integrity_checker.check_data_consistency()
        for alert in consistency_alerts:
            self.active_alerts.append(alert)
            scan_results["alerts_generated"].append(alert.dict())

        # Calculate overall health score
        if all_quality_scores:
            scan_results["overall_health_score"] = statistics.mean(all_quality_scores)

        # Attempt automated recovery for high-severity alerts
        high_severity_alerts = [
            alert
            for alert in self.active_alerts
            if alert.severity in ["high", "critical"]
            and alert.affected_records
            <= self.corruption_recovery.max_auto_recovery_records
        ]

        for alert in high_severity_alerts:
            try:
                recovery_result = (
                    await self.corruption_recovery.recover_from_corruption(alert)
                )
                scan_results["recoveries_attempted"].append(recovery_result)

                if recovery_result["recovery_successful"]:
                    # Remove alert if recovery was successful
                    self.active_alerts = [
                        a for a in self.active_alerts if a.alert_id != alert.alert_id
                    ]

            except Exception as e:
                logger.error(f"Failed to recover from alert {alert.alert_id}: {e}")

        logger.info(
            f"Corruption scan completed: {len(scan_results['alerts_generated'])} alerts, "
            f"overall health score: {scan_results['overall_health_score']:.3f}"
        )

        return scan_results

    async def start_monitoring(self) -> None:
        """Start continuous corruption monitoring."""
        logger.info("Starting data corruption monitoring service")

        # Establish baseline metrics
        await self.establish_baseline_metrics()

        # Main monitoring loop
        while True:
            try:
                scan_results = await self.run_corruption_scan()

                # Log summary
                logger.info(
                    f"Monitoring cycle completed: "
                    f"{len(scan_results['alerts_generated'])} new alerts, "
                    f"overall health: {scan_results['overall_health_score']:.3f}"
                )

                # Send alerts if configured
                if self.alert_webhook_url and scan_results["alerts_generated"]:
                    await self._send_alerts(scan_results["alerts_generated"])

                # Wait for next cycle
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Monitoring cycle failed: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _send_alerts(self, alerts: list[dict]) -> None:
        """Send alerts to configured webhook."""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(
                    self.alert_webhook_url,
                    json={
                        "service": "malaria-prediction-data-corruption",
                        "timestamp": datetime.now().isoformat(),
                        "alerts": alerts,
                    },
                    timeout=30.0,
                )
                logger.info(f"Sent {len(alerts)} alerts to webhook")

        except Exception as e:
            logger.error(f"Failed to send alerts to webhook: {e}")


async def main():
    """Main entry point for data corruption detection service."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Data Corruption Detection and Recovery"
    )
    parser.add_argument("--database-url", required=True, help="Database connection URL")
    parser.add_argument(
        "--backup-orchestrator",
        default="disaster_recovery/backup_orchestrator.py",
        help="Path to backup orchestrator script",
    )
    parser.add_argument(
        "--monitoring-interval",
        type=int,
        default=300,
        help="Monitoring interval in seconds",
    )
    parser.add_argument("--alert-webhook", help="Webhook URL for alerts")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Monitor command
    subparsers.add_parser("monitor", help="Start continuous monitoring")

    # Scan command
    subparsers.add_parser("scan", help="Run single corruption scan")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check specific table")
    check_parser.add_argument("table_name", help="Table to check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize monitor
    monitor = DataCorruptionMonitor(
        args.database_url,
        args.backup_orchestrator,
        args.monitoring_interval,
        args.alert_webhook,
    )

    try:
        if args.command == "monitor":
            await monitor.start_monitoring()

        elif args.command == "scan":
            results = await monitor.run_corruption_scan()
            print(json.dumps(results, indent=2, default=str))

        elif args.command == "check":
            metrics = await monitor.integrity_checker.check_table_integrity(
                args.table_name
            )
            print(json.dumps(metrics.dict(), indent=2, default=str))

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
