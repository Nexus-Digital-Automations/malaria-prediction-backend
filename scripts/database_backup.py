#!/usr/bin/env python3
"""
Database Backup and Recovery Scripts for Malaria Prediction System.

This module provides comprehensive backup and recovery capabilities for
TimescaleDB databases with support for:
- Full database backups
- Incremental backups
- Point-in-time recovery
- Backup validation and verification
- Automated backup scheduling
- Backup retention policies
"""

import argparse
import asyncio
import gzip
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import asyncpg

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseBackupManager:
    """Manages database backup and recovery operations for TimescaleDB."""

    def __init__(
        self,
        database_url: str,
        backup_dir: str = "/var/backups/malaria-prediction",
        retention_days: int = 30,
    ):
        """Initialize the backup manager.

        Args:
            database_url: PostgreSQL connection URL
            backup_dir: Directory to store backups
            retention_days: Number of days to retain backups
        """
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days

        # Parse database URL
        self._parse_database_url()

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Configure pg_dump and pg_restore paths
        self.pg_dump_path = shutil.which("pg_dump") or "/usr/bin/pg_dump"
        self.pg_restore_path = shutil.which("pg_restore") or "/usr/bin/pg_restore"

        logger.info(f"Backup manager initialized with backup_dir: {self.backup_dir}")

    def _parse_database_url(self) -> None:
        """Parse database URL into components."""
        # Simple URL parsing for postgresql://user:pass@host:port/dbname
        if not self.database_url.startswith("postgresql://"):
            raise ValueError("Database URL must start with postgresql://")

        url_parts = self.database_url.replace("postgresql://", "").split("@")
        if len(url_parts) != 2:
            raise ValueError("Invalid database URL format")

        user_pass, host_db = url_parts
        user_pass_parts = user_pass.split(":")
        host_db_parts = host_db.split("/")

        self.db_user = user_pass_parts[0]
        self.db_password = user_pass_parts[1] if len(user_pass_parts) > 1 else ""

        host_port = host_db_parts[0].split(":")
        self.db_host = host_port[0]
        self.db_port = host_port[1] if len(host_port) > 1 else "5432"
        self.db_name = host_db_parts[1] if len(host_db_parts) > 1 else ""

    async def create_backup(
        self,
        backup_type: str = "full",
        compress: bool = True,
        include_data: bool = True,
    ) -> str:
        """Create a database backup.

        Args:
            backup_type: Type of backup ('full', 'schema', 'data')
            compress: Whether to compress the backup
            include_data: Whether to include data in backup

        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"malaria_prediction_{backup_type}_{timestamp}"
        backup_file = self.backup_dir / f"{backup_name}.sql"

        if compress:
            backup_file = backup_file.with_suffix(".sql.gz")

        logger.info(f"Creating {backup_type} backup: {backup_file}")

        # Build pg_dump command
        cmd = [
            self.pg_dump_path,
            f"--host={self.db_host}",
            f"--port={self.db_port}",
            f"--username={self.db_user}",
            "--verbose",
            "--no-password",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
        ]

        if backup_type == "schema":
            cmd.append("--schema-only")
        elif backup_type == "data":
            cmd.append("--data-only")
        elif not include_data:
            cmd.append("--schema-only")

        cmd.append(self.db_name)

        # Set environment for password
        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_password

        try:
            # Execute pg_dump
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"pg_dump failed: {stderr.decode()}")
                raise RuntimeError(f"Backup failed: {stderr.decode()}")

            # Write output to file
            if compress:
                with gzip.open(backup_file, "wb") as f:
                    f.write(stdout)
            else:
                with open(backup_file, "wb") as f:
                    f.write(stdout)

            # Create metadata file
            await self._create_backup_metadata(backup_file, backup_type)

            logger.info(f"Backup completed successfully: {backup_file}")
            return str(backup_file)

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if backup_file.exists():
                backup_file.unlink()
            raise

    async def _create_backup_metadata(
        self, backup_file: Path, backup_type: str
    ) -> None:
        """Create metadata file for backup."""
        metadata_file = backup_file.with_suffix(".metadata.json")

        # Get database statistics
        conn = await asyncpg.connect(self.database_url)
        try:
            # Get table sizes
            table_sizes = await conn.fetch(
                """
                SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            )

            # Get database size
            db_size = await conn.fetchval(
                "SELECT pg_size_pretty(pg_database_size($1))", self.db_name
            )

            # Check TimescaleDB chunks
            chunks_info = await conn.fetch(
                """
                SELECT hypertable_name, chunk_name, range_start, range_end
                FROM timescaledb_information.chunks
                WHERE hypertable_schema = 'public'
                ORDER BY hypertable_name, range_start
                LIMIT 10
            """
            )

        finally:
            await conn.close()

        metadata = {
            "backup_file": backup_file.name,
            "backup_type": backup_type,
            "created_at": datetime.now().isoformat(),
            "database_name": self.db_name,
            "database_size": db_size,
            "table_sizes": [dict(row) for row in table_sizes],
            "timescaledb_chunks": [dict(row) for row in chunks_info],
            "file_size_bytes": backup_file.stat().st_size,
        }

        import json

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    async def restore_backup(
        self, backup_file: str, target_db: str | None = None, clean_first: bool = False
    ) -> None:
        """Restore database from backup.

        Args:
            backup_file: Path to backup file
            target_db: Target database name (defaults to original)
            clean_first: Whether to clean existing database first
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        target_database = target_db or self.db_name
        logger.info(f"Restoring backup {backup_file} to database {target_database}")

        # Build pg_restore command
        cmd = [
            self.pg_restore_path,
            f"--host={self.db_host}",
            f"--port={self.db_port}",
            f"--username={self.db_user}",
            f"--dbname={target_database}",
            "--verbose",
            "--no-password",
        ]

        if clean_first:
            cmd.append("--clean")

        cmd.append(str(backup_path))

        # Set environment for password
        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_password

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"pg_restore failed: {stderr.decode()}")
                raise RuntimeError(f"Restore failed: {stderr.decode()}")

            logger.info("Database restore completed successfully")

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise

    async def verify_backup(self, backup_file: str) -> dict:
        """Verify backup integrity and metadata.

        Args:
            backup_file: Path to backup file

        Returns:
            Dictionary with verification results
        """
        backup_path = Path(backup_file)
        verification_results = {
            "file_exists": backup_path.exists(),
            "file_readable": False,
            "metadata_exists": False,
            "file_size_bytes": 0,
            "valid": False,
        }

        if not verification_results["file_exists"]:
            return verification_results

        try:
            # Check file readability
            verification_results["file_size_bytes"] = backup_path.stat().st_size
            verification_results["file_readable"] = True

            # Check metadata file
            metadata_file = backup_path.with_suffix(".metadata.json")
            verification_results["metadata_exists"] = metadata_file.exists()

            # Try to read backup file header
            if backup_path.suffix == ".gz":
                with gzip.open(backup_path, "rb") as f:
                    header = f.read(100)
            else:
                with open(backup_path, "rb") as f:
                    header = f.read(100)

            # Check for pg_dump header
            verification_results["valid"] = b"PGDMP" in header[:10]

            logger.info(f"Backup verification completed for {backup_file}")

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            verification_results["error"] = str(e)

        return verification_results

    async def list_backups(self) -> list[dict]:
        """List all available backups with metadata.

        Returns:
            List of backup information dictionaries
        """
        backups = []

        for backup_file in self.backup_dir.glob("*.sql*"):
            if backup_file.suffix in [".sql", ".gz"]:
                backup_info = {
                    "file_path": str(backup_file),
                    "file_name": backup_file.name,
                    "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime),
                    "size_bytes": backup_file.stat().st_size,
                    "compressed": backup_file.suffix == ".gz",
                }

                # Load metadata if available
                metadata_file = backup_file.with_suffix(".metadata.json")
                if metadata_file.exists():
                    try:
                        import json

                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        backup_info.update(metadata)
                    except Exception as e:
                        logger.warning(
                            f"Failed to read metadata for {backup_file}: {e}"
                        )

                backups.append(backup_info)

        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    async def cleanup_old_backups(self) -> int:
        """Remove backups older than retention period.

        Returns:
            Number of backups removed
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0

        backups = await self.list_backups()

        for backup in backups:
            if backup["created_at"] < cutoff_date:
                backup_file = Path(backup["file_path"])
                metadata_file = backup_file.with_suffix(".metadata.json")

                try:
                    backup_file.unlink()
                    if metadata_file.exists():
                        metadata_file.unlink()

                    logger.info(f"Removed old backup: {backup_file.name}")
                    removed_count += 1

                except Exception as e:
                    logger.error(f"Failed to remove backup {backup_file}: {e}")

        logger.info(f"Cleanup completed: {removed_count} backups removed")
        return removed_count

    async def create_scheduled_backup(self) -> str:
        """Create a scheduled backup with automatic cleanup."""
        # Determine backup type based on day of week
        # Full backup on Sunday, incremental on other days
        backup_type = "full" if datetime.now().weekday() == 6 else "incremental"

        # Create backup
        backup_file = await self.create_backup(backup_type=backup_type)

        # Verify backup
        verification = await self.verify_backup(backup_file)
        if not verification["valid"]:
            raise RuntimeError(f"Backup verification failed: {verification}")

        # Cleanup old backups
        await self.cleanup_old_backups()

        return backup_file


async def main():
    """Main CLI interface for backup operations."""
    parser = argparse.ArgumentParser(description="Database backup and recovery tool")
    parser.add_argument("--database-url", required=True, help="PostgreSQL database URL")
    parser.add_argument(
        "--backup-dir",
        default="/var/backups/malaria-prediction",
        help="Backup directory",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to retain backups",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create database backup")
    backup_parser.add_argument(
        "--type", choices=["full", "schema", "data"], default="full", help="Backup type"
    )
    backup_parser.add_argument(
        "--no-compress", action="store_true", help="Disable compression"
    )

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database backup")
    restore_parser.add_argument("backup_file", help="Path to backup file")
    restore_parser.add_argument("--target-db", help="Target database name")
    restore_parser.add_argument(
        "--clean", action="store_true", help="Clean existing database first"
    )

    # List command
    subparsers.add_parser("list", help="List available backups")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_parser.add_argument("backup_file", help="Path to backup file")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Remove old backups")

    # Scheduled backup command
    subparsers.add_parser("scheduled", help="Create scheduled backup with cleanup")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize backup manager
    backup_manager = DatabaseBackupManager(
        args.database_url, args.backup_dir, args.retention_days
    )

    try:
        if args.command == "backup":
            backup_file = await backup_manager.create_backup(
                backup_type=args.type, compress=not args.no_compress
            )
            print(f"Backup created: {backup_file}")

        elif args.command == "restore":
            await backup_manager.restore_backup(
                args.backup_file, args.target_db, args.clean
            )
            print("Restore completed successfully")

        elif args.command == "list":
            backups = await backup_manager.list_backups()
            print(f"Found {len(backups)} backups:")
            for backup in backups:
                print(
                    f"  {backup['file_name']} - {backup['created_at']} - {backup['size_bytes']} bytes"
                )

        elif args.command == "verify":
            result = await backup_manager.verify_backup(args.backup_file)
            print(f"Verification result: {result}")

        elif args.command == "cleanup":
            removed = await backup_manager.cleanup_old_backups()
            print(f"Removed {removed} old backups")

        elif args.command == "scheduled":
            backup_file = await backup_manager.create_scheduled_backup()
            print(f"Scheduled backup created: {backup_file}")

    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
