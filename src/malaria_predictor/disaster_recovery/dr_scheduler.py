#!/usr/bin/env python3
"""
Disaster Recovery Scheduler for Malaria Prediction System.

This module provides automated scheduling for disaster recovery operations:
- Automated backup scheduling with retention management
- Regular DR testing execution
- Data corruption monitoring schedules
- System health check automation
- Recovery orchestration timing
- Maintenance window coordination
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,  # type: ignore[import-not-found]
)
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-not-found]
from apscheduler.triggers.interval import (
    IntervalTrigger,  # type: ignore[import-not-found]
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/malaria-prediction/dr-scheduler.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class DRScheduleConfig:
    """Configuration for DR scheduling operations."""

    def __init__(self, config_file: Path | None = None):
        """Initialize DR schedule configuration.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or Path(
            "disaster_recovery/dr_schedule_config.json"
        )
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "backup_schedules": {
                "database_full": {
                    "schedule": "cron",
                    "cron": "0 2 * * *",  # Daily at 2 AM
                    "enabled": True,
                    "retention_days": 30,
                },
                "database_incremental": {
                    "schedule": "interval",
                    "interval_hours": 4,
                    "enabled": True,
                    "retention_days": 7,
                },
                "models": {
                    "schedule": "cron",
                    "cron": "0 3 * * *",  # Daily at 3 AM
                    "enabled": True,
                    "retention_days": 60,
                },
                "configuration": {
                    "schedule": "cron",
                    "cron": "0 1 * * *",  # Daily at 1 AM
                    "enabled": True,
                    "retention_days": 90,
                },
                "redis": {
                    "schedule": "interval",
                    "interval_hours": 6,
                    "enabled": True,
                    "retention_days": 7,
                },
                "logs": {
                    "schedule": "cron",
                    "cron": "0 4 * * *",  # Daily at 4 AM
                    "enabled": True,
                    "retention_days": 30,
                },
                "complete_system": {
                    "schedule": "cron",
                    "cron": "0 1 * * 0",  # Weekly on Sunday at 1 AM
                    "enabled": True,
                    "retention_days": 84,
                },
            },
            "testing_schedules": {
                "backup_verification": {
                    "schedule": "cron",
                    "cron": "0 6 * * *",  # Daily at 6 AM
                    "enabled": True,
                },
                "application_recovery": {
                    "schedule": "cron",
                    "cron": "0 8 * * 1",  # Weekly on Monday at 8 AM
                    "enabled": True,
                },
                "database_recovery_simulation": {
                    "schedule": "cron",
                    "cron": "0 10 * * 6",  # Weekly on Saturday at 10 AM
                    "enabled": True,
                },
                "comprehensive_dr_test": {
                    "schedule": "cron",
                    "cron": "0 2 1 * *",  # Monthly on 1st at 2 AM
                    "enabled": True,
                },
            },
            "monitoring_schedules": {
                "data_corruption_scan": {
                    "schedule": "interval",
                    "interval_minutes": 15,
                    "enabled": True,
                },
                "service_health_check": {
                    "schedule": "interval",
                    "interval_minutes": 5,
                    "enabled": True,
                },
                "backup_integrity_check": {
                    "schedule": "cron",
                    "cron": "30 * * * *",  # Every hour at 30 minutes
                    "enabled": True,
                },
            },
            "maintenance_windows": {
                "primary": {
                    "start_time": "01:00",
                    "end_time": "05:00",
                    "timezone": "UTC",
                    "days": ["sunday"],
                },
                "secondary": {
                    "start_time": "02:00",
                    "end_time": "04:00",
                    "timezone": "UTC",
                    "days": ["wednesday"],
                },
            },
        }

        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                return {**default_config, **config}
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")

        return default_config

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def get_backup_schedule(self, backup_type: str) -> dict[str, Any] | None:
        """Get backup schedule configuration."""
        return self.config.get("backup_schedules", {}).get(backup_type)  # type: ignore[no-any-return]

    def get_testing_schedule(self, test_type: str) -> dict[str, Any] | None:
        """Get testing schedule configuration."""
        return self.config.get("testing_schedules", {}).get(test_type)  # type: ignore[no-any-return]

    def get_monitoring_schedule(self, monitoring_type: str) -> dict[str, Any] | None:
        """Get monitoring schedule configuration."""
        return self.config.get("monitoring_schedules", {}).get(monitoring_type)  # type: ignore[no-any-return]

    def is_maintenance_window(self) -> bool:
        """Check if current time is within a maintenance window."""
        current_time = datetime.now()
        current_day = current_time.strftime("%A").lower()
        current_time_str = current_time.strftime("%H:%M")

        for _window_name, window_config in self.config.get(
            "maintenance_windows", {}
        ).items():
            if current_day in window_config.get("days", []):
                start_time = window_config.get("start_time")
                end_time = window_config.get("end_time")

                if start_time <= current_time_str <= end_time:
                    return True

        return False


class DRTaskExecutor:
    """Executes DR tasks based on scheduled configuration."""

    def __init__(
        self,
        database_url: str,
        redis_url: str,
        backup_orchestrator_path: str,
        testing_framework_path: str,
        corruption_detector_path: str,
        failover_orchestrator_path: str,
    ):
        """Initialize DR task executor.

        Args:
            database_url: Database connection URL
            redis_url: Redis connection URL
            backup_orchestrator_path: Path to backup orchestrator script
            testing_framework_path: Path to testing framework script
            corruption_detector_path: Path to corruption detector script
            failover_orchestrator_path: Path to failover orchestrator script
        """
        self.database_url = database_url
        self.redis_url = redis_url
        self.backup_orchestrator_path = backup_orchestrator_path
        self.testing_framework_path = testing_framework_path
        self.corruption_detector_path = corruption_detector_path
        self.failover_orchestrator_path = failover_orchestrator_path

        # Task execution statistics
        self.task_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "last_execution_time": None,
        }

    async def execute_backup_task(
        self, backup_type: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute backup task.

        Args:
            backup_type: Type of backup to execute
            config: Backup configuration

        Returns:
            Task execution result
        """
        start_time = datetime.now()
        logger.info(f"Starting backup task: {backup_type}")

        try:
            # Build backup command
            cmd = [
                "python",
                self.backup_orchestrator_path,
                "--database-url",
                self.database_url,
                "--redis-url",
                self.redis_url,
                "backup",
                "--type",
                backup_type,
            ]

            # Add upload flag if needed
            if config.get("upload_to_s3", True):
                cmd.append("--upload")

            # Execute backup
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            success = result.returncode == 0
            duration = (datetime.now() - start_time).total_seconds()

            task_result = {
                "task_type": "backup",
                "backup_type": backup_type,
                "success": success,
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }

            if success:
                logger.info(
                    f"Backup task {backup_type} completed successfully in {duration:.2f}s"
                )
                self.task_stats["successful_executions"] += 1  # type: ignore[operator]
            else:
                logger.error(f"Backup task {backup_type} failed: {stderr.decode()}")
                self.task_stats["failed_executions"] += 1  # type: ignore[operator]

            # Cleanup old backups if retention is configured
            if config.get("retention_days"):
                await self._cleanup_old_backups(backup_type, config["retention_days"])

            return task_result

        except Exception as e:
            logger.error(f"Error executing backup task {backup_type}: {e}")
            self.task_stats["failed_executions"] += 1  # type: ignore[operator]
            return {
                "task_type": "backup",
                "backup_type": backup_type,
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
            }
        finally:
            self.task_stats["total_executions"] += 1  # type: ignore[operator]
            self.task_stats["last_execution_time"] = datetime.now().isoformat()  # type: ignore[assignment]

    async def execute_testing_task(
        self, test_type: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute DR testing task.

        Args:
            test_type: Type of test to execute
            config: Test configuration

        Returns:
            Task execution result
        """
        start_time = datetime.now()
        logger.info(f"Starting DR test: {test_type}")

        try:
            # Build test command
            cmd = [
                "python",
                self.testing_framework_path,
                "--database-url",
                self.database_url,
                "--redis-url",
                self.redis_url,
                test_type.replace("_", "-"),
            ]

            # Execute test
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            success = result.returncode == 0
            duration = (datetime.now() - start_time).total_seconds()

            task_result = {
                "task_type": "testing",
                "test_type": test_type,
                "success": success,
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }

            if success:
                logger.info(
                    f"DR test {test_type} completed successfully in {duration:.2f}s"
                )
                self.task_stats["successful_executions"] += 1  # type: ignore[operator]
            else:
                logger.error(f"DR test {test_type} failed: {stderr.decode()}")
                self.task_stats["failed_executions"] += 1  # type: ignore[operator]

            return task_result

        except Exception as e:
            logger.error(f"Error executing DR test {test_type}: {e}")
            self.task_stats["failed_executions"] += 1  # type: ignore[operator]
            return {
                "task_type": "testing",
                "test_type": test_type,
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
            }
        finally:
            self.task_stats["total_executions"] += 1  # type: ignore[operator]
            self.task_stats["last_execution_time"] = datetime.now().isoformat()  # type: ignore[assignment]

    async def execute_monitoring_task(
        self, monitoring_type: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute monitoring task.

        Args:
            monitoring_type: Type of monitoring to execute
            config: Monitoring configuration

        Returns:
            Task execution result
        """
        start_time = datetime.now()
        logger.info(f"Starting monitoring task: {monitoring_type}")

        try:
            task_result = {
                "task_type": "monitoring",
                "monitoring_type": monitoring_type,
                "success": False,
                "start_time": start_time.isoformat(),
            }

            if monitoring_type == "data_corruption_scan":
                # Execute data corruption scan
                cmd = [
                    "python",
                    self.corruption_detector_path,
                    "--database-url",
                    self.database_url,
                    "scan",
                ]

                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()
                task_result["success"] = result.returncode == 0
                task_result["stdout"] = stdout.decode() if stdout else ""
                task_result["stderr"] = stderr.decode() if stderr else ""

            elif monitoring_type == "service_health_check":
                # Execute service health check
                cmd = [
                    "python",
                    self.failover_orchestrator_path,
                    "--primary-db",
                    self.database_url,
                    "health",
                ]

                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()
                task_result["success"] = result.returncode == 0
                task_result["stdout"] = stdout.decode() if stdout else ""
                task_result["stderr"] = stderr.decode() if stderr else ""

            elif monitoring_type == "backup_integrity_check":
                # Execute backup integrity check
                cmd = [
                    "python",
                    self.backup_orchestrator_path,
                    "--database-url",
                    self.database_url,
                    "--redis-url",
                    self.redis_url,
                    "verify-all-backups",
                ]

                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()
                task_result["success"] = result.returncode == 0
                task_result["stdout"] = stdout.decode() if stdout else ""
                task_result["stderr"] = stderr.decode() if stderr else ""

            duration = (datetime.now() - start_time).total_seconds()
            task_result["duration_seconds"] = duration
            task_result["end_time"] = datetime.now().isoformat()

            if task_result["success"]:
                logger.info(f"Monitoring task {monitoring_type} completed successfully")
                self.task_stats["successful_executions"] += 1  # type: ignore[operator]
            else:
                logger.error(f"Monitoring task {monitoring_type} failed")
                self.task_stats["failed_executions"] += 1  # type: ignore[operator]

            return task_result

        except Exception as e:
            logger.error(f"Error executing monitoring task {monitoring_type}: {e}")
            self.task_stats["failed_executions"] += 1  # type: ignore[operator]
            return {
                "task_type": "monitoring",
                "monitoring_type": monitoring_type,
                "success": False,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
            }
        finally:
            self.task_stats["total_executions"] += 1  # type: ignore[operator]
            self.task_stats["last_execution_time"] = datetime.now().isoformat()  # type: ignore[assignment]

    async def _cleanup_old_backups(self, backup_type: str, retention_days: int) -> None:
        """Clean up old backups based on retention policy."""
        try:
            cmd = [
                "python",
                self.backup_orchestrator_path,
                "--database-url",
                self.database_url,
                "--redis-url",
                self.redis_url,
                "--retention-days",
                str(retention_days),
                "cleanup",
            ]

            result = await asyncio.create_subprocess_exec(*cmd)
            await result.communicate()

            if result.returncode == 0:
                logger.info(
                    f"Cleaned up old {backup_type} backups (retention: {retention_days} days)"
                )
            else:
                logger.warning(f"Backup cleanup for {backup_type} may have failed")

        except Exception as e:
            logger.error(f"Error cleaning up old backups for {backup_type}: {e}")


class DRScheduler:
    """Main DR scheduler service."""

    def __init__(
        self, database_url: str, redis_url: str, config_file: Path | None = None
    ):
        """Initialize DR scheduler.

        Args:
            database_url: Database connection URL
            redis_url: Redis connection URL
            config_file: Path to configuration file
        """
        self.database_url = database_url
        self.redis_url = redis_url

        # Initialize components
        self.config = DRScheduleConfig(config_file)
        self.executor = DRTaskExecutor(
            database_url,
            redis_url,
            "disaster_recovery/backup_orchestrator.py",
            "disaster_recovery/disaster_recovery_tester.py",
            "disaster_recovery/data_corruption_detector.py",
            "disaster_recovery/failover_orchestrator.py",
        )

        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()

        # Task execution log
        self.execution_log: list[dict[str, Any]] = []

    def setup_schedules(self) -> None:
        """Setup all scheduled tasks based on configuration."""
        # Setup backup schedules
        for backup_type, backup_config in self.config.config.get(
            "backup_schedules", {}
        ).items():
            if not backup_config.get("enabled", True):
                continue

            if backup_config.get("schedule") == "cron":
                trigger = CronTrigger.from_crontab(backup_config["cron"])
            elif backup_config.get("schedule") == "interval":
                trigger = IntervalTrigger(hours=backup_config.get("interval_hours", 24))
            else:
                logger.warning(f"Unknown schedule type for backup {backup_type}")
                continue

            self.scheduler.add_job(
                self._execute_backup_job,
                trigger=trigger,
                args=[backup_type, backup_config],
                id=f"backup_{backup_type}",
                name=f"Backup: {backup_type}",
                replace_existing=True,
            )

            logger.info(f"Scheduled backup job: {backup_type}")

        # Setup testing schedules
        for test_type, test_config in self.config.config.get(
            "testing_schedules", {}
        ).items():
            if not test_config.get("enabled", True):
                continue

            if test_config.get("schedule") == "cron":
                trigger = CronTrigger.from_crontab(test_config["cron"])
            else:
                logger.warning(f"Unknown schedule type for test {test_type}")
                continue

            self.scheduler.add_job(
                self._execute_testing_job,
                trigger=trigger,
                args=[test_type, test_config],
                id=f"test_{test_type}",
                name=f"Test: {test_type}",
                replace_existing=True,
            )

            logger.info(f"Scheduled testing job: {test_type}")

        # Setup monitoring schedules
        for monitoring_type, monitoring_config in self.config.config.get(
            "monitoring_schedules", {}
        ).items():
            if not monitoring_config.get("enabled", True):
                continue

            if monitoring_config.get("schedule") == "cron":
                trigger = CronTrigger.from_crontab(monitoring_config["cron"])
            elif monitoring_config.get("schedule") == "interval":
                if "interval_minutes" in monitoring_config:
                    trigger = IntervalTrigger(
                        minutes=monitoring_config["interval_minutes"]
                    )
                elif "interval_hours" in monitoring_config:
                    trigger = IntervalTrigger(hours=monitoring_config["interval_hours"])
                else:
                    logger.warning(
                        f"No interval specified for monitoring {monitoring_type}"
                    )
                    continue
            else:
                logger.warning(
                    f"Unknown schedule type for monitoring {monitoring_type}"
                )
                continue

            self.scheduler.add_job(
                self._execute_monitoring_job,
                trigger=trigger,
                args=[monitoring_type, monitoring_config],
                id=f"monitoring_{monitoring_type}",
                name=f"Monitoring: {monitoring_type}",
                replace_existing=True,
            )

            logger.info(f"Scheduled monitoring job: {monitoring_type}")

    async def _execute_backup_job(
        self, backup_type: str, config: dict[str, Any]
    ) -> None:
        """Execute scheduled backup job."""
        try:
            result = await self.executor.execute_backup_task(backup_type, config)
            self.execution_log.append(result)

            # Keep execution log to reasonable size
            if len(self.execution_log) > 1000:
                self.execution_log = self.execution_log[-500:]

        except Exception as e:
            logger.error(f"Error in scheduled backup job {backup_type}: {e}")

    async def _execute_testing_job(
        self, test_type: str, config: dict[str, Any]
    ) -> None:
        """Execute scheduled testing job."""
        try:
            # Check if we're in a maintenance window for disruptive tests
            disruptive_tests = ["application_recovery", "database_recovery_simulation"]
            if (
                test_type in disruptive_tests
                and not self.config.is_maintenance_window()
            ):
                logger.info(
                    f"Skipping disruptive test {test_type} outside maintenance window"
                )
                return

            result = await self.executor.execute_testing_task(test_type, config)
            self.execution_log.append(result)

            # Keep execution log to reasonable size
            if len(self.execution_log) > 1000:
                self.execution_log = self.execution_log[-500:]

        except Exception as e:
            logger.error(f"Error in scheduled testing job {test_type}: {e}")

    async def _execute_monitoring_job(
        self, monitoring_type: str, config: dict[str, Any]
    ) -> None:
        """Execute scheduled monitoring job."""
        try:
            result = await self.executor.execute_monitoring_task(
                monitoring_type, config
            )
            self.execution_log.append(result)

            # Keep execution log to reasonable size
            if len(self.execution_log) > 1000:
                self.execution_log = self.execution_log[-500:]

        except Exception as e:
            logger.error(f"Error in scheduled monitoring job {monitoring_type}: {e}")

    def start_scheduler(self) -> None:
        """Start the DR scheduler."""
        logger.info("Starting DR scheduler")

        # Setup all scheduled jobs
        self.setup_schedules()

        # Start the scheduler
        self.scheduler.start()

        logger.info(f"DR scheduler started with {len(self.scheduler.get_jobs())} jobs")

        # Log all scheduled jobs
        for job in self.scheduler.get_jobs():
            logger.info(
                f"Scheduled job: {job.name} (ID: {job.id}, Next run: {job.next_run_time})"
            )

    def stop_scheduler(self) -> None:
        """Stop the DR scheduler."""
        logger.info("Stopping DR scheduler")
        self.scheduler.shutdown()

    def get_job_status(self) -> dict[str, Any]:
        """Get current job status and statistics."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
            )

        return {
            "scheduler_running": self.scheduler.running,
            "total_jobs": len(jobs),
            "jobs": jobs,
            "execution_stats": self.executor.task_stats,
            "recent_executions": self.execution_log[-10:],  # Last 10 executions
        }

    def trigger_manual_job(self, job_id: str) -> bool:
        """Manually trigger a scheduled job.

        Args:
            job_id: ID of job to trigger

        Returns:
            True if job was triggered successfully
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Manually triggered job: {job_id}")
                return True
            else:
                logger.warning(f"Job not found: {job_id}")
                return False
        except Exception as e:
            logger.error(f"Error triggering job {job_id}: {e}")
            return False


async def main() -> int:
    """Main entry point for DR scheduler."""
    import argparse

    parser = argparse.ArgumentParser(description="Disaster Recovery Scheduler")
    parser.add_argument("--database-url", required=True, help="Database connection URL")
    parser.add_argument("--redis-url", required=True, help="Redis connection URL")
    parser.add_argument("--config-file", help="Path to configuration file")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    subparsers.add_parser("start", help="Start DR scheduler service")

    # Status command
    subparsers.add_parser("status", help="Show scheduler status")

    # Trigger command
    trigger_parser = subparsers.add_parser("trigger", help="Manually trigger a job")
    trigger_parser.add_argument("job_id", help="Job ID to trigger")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize scheduler
    scheduler = DRScheduler(
        args.database_url,
        args.redis_url,
        Path(args.config_file) if args.config_file else None,
    )

    try:
        if args.command == "start":
            scheduler.start_scheduler()

            # Keep scheduler running
            try:
                while True:
                    await asyncio.sleep(60)

                    # Periodically log status
                    status = scheduler.get_job_status()
                    logger.info(
                        f"Scheduler status: {status['total_jobs']} jobs, "
                        f"{status['execution_stats']['total_executions']} executions"
                    )

            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                scheduler.stop_scheduler()

        elif args.command == "status":
            scheduler.start_scheduler()  # Need to start to get job info
            status = scheduler.get_job_status()
            print(json.dumps(status, indent=2, default=str))
            scheduler.stop_scheduler()

        elif args.command == "trigger":
            scheduler.start_scheduler()
            success = scheduler.trigger_manual_job(args.job_id)
            if success:
                print(f"Job {args.job_id} triggered successfully")
                # Wait a bit for the job to complete
                await asyncio.sleep(5)
            else:
                print(f"Failed to trigger job {args.job_id}")
                return 1
            scheduler.stop_scheduler()

    except Exception as e:
        logger.error(f"Scheduler service failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
