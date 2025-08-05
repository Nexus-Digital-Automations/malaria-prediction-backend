#!/usr/bin/env python3
"""
Disaster Recovery Backup Orchestrator for Malaria Prediction System.

This module provides comprehensive backup orchestration capabilities including:
- Database backups with TimescaleDB support
- ML model backup and versioning
- Configuration and secrets backup
- Log aggregation and archival
- Automated backup scheduling and coordination
- Backup encryption and compression
- Multi-destination backup storage
- Backup integrity verification
"""

import asyncio
import gzip
import json
import logging
import os
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path

import aiofiles
import asyncpg
import boto3
import redis.asyncio as redis
from botocore.exceptions import ClientError, NoCredentialsError
from cryptography.fernet import Fernet

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/malaria-prediction/backup.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class BackupEncryption:
    """Handles backup encryption and decryption operations."""

    def __init__(self, encryption_key: str | None = None):
        """Initialize encryption handler.

        Args:
            encryption_key: Base64-encoded encryption key. If None, generates new key.
        """
        if encryption_key:
            self.fernet = Fernet(encryption_key.encode())
        else:
            key = Fernet.generate_key()
            self.fernet = Fernet(key)
            # Store key securely (in production, use a key management service)
            logger.warning("Generated new encryption key. Store securely!")
            logger.info(f"Encryption key: {key.decode()}")

    def encrypt_file(self, input_path: Path, output_path: Path) -> None:
        """Encrypt a file.

        Args:
            input_path: Path to input file
            output_path: Path to encrypted output file
        """
        with open(input_path, "rb") as infile:
            encrypted_data = self.fernet.encrypt(infile.read())

        with open(output_path, "wb") as outfile:
            outfile.write(encrypted_data)

    def decrypt_file(self, input_path: Path, output_path: Path) -> None:
        """Decrypt a file.

        Args:
            input_path: Path to encrypted input file
            output_path: Path to decrypted output file
        """
        with open(input_path, "rb") as infile:
            decrypted_data = self.fernet.decrypt(infile.read())

        with open(output_path, "wb") as outfile:
            outfile.write(decrypted_data)


class S3BackupStorage:
    """Handles backup storage to AWS S3."""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key: str | None = None,
        aws_secret_key: str | None = None,
        region: str = "us-east-1",
    ):
        """Initialize S3 storage handler.

        Args:
            bucket_name: S3 bucket name
            aws_access_key: AWS access key (optional, uses IAM role if not provided)
            aws_secret_key: AWS secret key (optional, uses IAM role if not provided)
            region: AWS region
        """
        self.bucket_name = bucket_name

        try:
            if aws_access_key and aws_secret_key:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=region,
                )
            else:
                # Use IAM role or default credentials
                self.s3_client = boto3.client("s3", region_name=region)

            # Test connection
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 storage initialized for bucket: {bucket_name}")
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Failed to initialize S3 storage: {e}")
            self.s3_client = None

    async def upload_backup(self, local_path: Path, s3_key: str) -> bool:
        """Upload backup file to S3.

        Args:
            local_path: Local file path
            s3_key: S3 object key

        Returns:
            True if upload successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False

        try:
            # Add metadata
            metadata = {
                "backup-timestamp": datetime.now().isoformat(),
                "backup-type": "malaria-prediction-dr",
                "file-size": str(local_path.stat().st_size),
            }

            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={"Metadata": metadata},
            )
            logger.info(f"Uploaded backup to S3: s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            return False

    async def download_backup(self, s3_key: str, local_path: Path) -> bool:
        """Download backup file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local destination path

        Returns:
            True if download successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False

        try:
            self.s3_client.download_file(self.bucket_name, s3_key, str(local_path))
            logger.info(f"Downloaded backup from S3: s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to download backup from S3: {e}")
            return False


class DisasterRecoveryOrchestrator:
    """Main orchestrator for disaster recovery backup operations."""

    def __init__(
        self,
        database_url: str,
        redis_url: str,
        backup_base_dir: str = "/var/backups/malaria-prediction",
        s3_bucket: str | None = None,
        encryption_key: str | None = None,
        retention_days: int = 30,
    ):
        """Initialize disaster recovery orchestrator.

        Args:
            database_url: PostgreSQL connection URL
            redis_url: Redis connection URL
            backup_base_dir: Base directory for local backups
            s3_bucket: S3 bucket name for remote storage
            encryption_key: Encryption key for backup security
            retention_days: Number of days to retain backups
        """
        self.database_url = database_url
        self.redis_url = redis_url
        self.backup_base_dir = Path(backup_base_dir)
        self.retention_days = retention_days

        # Initialize components
        self.encryption = BackupEncryption(encryption_key)
        self.s3_storage = S3BackupStorage(s3_bucket) if s3_bucket else None

        # Create backup directories
        self.backup_dirs = {
            "database": self.backup_base_dir / "database",
            "models": self.backup_base_dir / "models",
            "config": self.backup_base_dir / "config",
            "logs": self.backup_base_dir / "logs",
            "complete": self.backup_base_dir / "complete",
        }

        for backup_dir in self.backup_dirs.values():
            backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"DR Orchestrator initialized with backup_dir: {self.backup_base_dir}"
        )

    async def backup_database(self, backup_type: str = "full") -> Path | None:
        """Create database backup with TimescaleDB support.

        Args:
            backup_type: Type of backup ('full', 'schema', 'data')

        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"database_{backup_type}_{timestamp}.sql.gz"
        backup_file = self.backup_dirs["database"] / backup_name

        logger.info(f"Creating database backup: {backup_file}")

        try:
            # Parse database URL
            db_parts = self.database_url.replace("postgresql://", "").split("@")
            user_pass, host_db = db_parts
            user_pass_parts = user_pass.split(":")
            host_db_parts = host_db.split("/")

            db_user = user_pass_parts[0]
            db_password = user_pass_parts[1] if len(user_pass_parts) > 1 else ""
            host_port = host_db_parts[0].split(":")
            db_host = host_port[0]
            db_port = host_port[1] if len(host_port) > 1 else "5432"
            db_name = host_db_parts[1].split("?")[0] if len(host_db_parts) > 1 else ""

            # Build pg_dump command
            cmd = [
                "pg_dump",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
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

            cmd.append(db_name)

            # Set environment for password
            env = os.environ.copy()
            env["PGPASSWORD"] = db_password

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
                return None

            # Compress and save output
            with gzip.open(backup_file, "wb") as f:
                f.write(stdout)

            # Create metadata
            await self._create_backup_metadata(backup_file, "database", backup_type)

            logger.info(f"Database backup completed: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            if backup_file.exists():
                backup_file.unlink()
            return None

    async def backup_models(self) -> Path | None:
        """Backup ML models and training artifacts.

        Returns:
            Path to created backup archive
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"models_{timestamp}.tar.gz"
        backup_file = self.backup_dirs["models"] / backup_name

        logger.info(f"Creating models backup: {backup_file}")

        try:
            # Define model directories and files to backup
            model_paths = [
                Path("/app/models"),
                Path("/app/src/malaria_predictor/ml/models"),
                Path("/app/artifacts"),
                Path("/app/experiments"),
            ]

            # Create tar archive
            with tarfile.open(backup_file, "w:gz") as tar:
                for model_path in model_paths:
                    if model_path.exists():
                        tar.add(model_path, arcname=model_path.name)
                        logger.info(f"Added to models backup: {model_path}")

            # Create metadata
            await self._create_backup_metadata(backup_file, "models")

            logger.info(f"Models backup completed: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Models backup failed: {e}")
            if backup_file.exists():
                backup_file.unlink()
            return None

    async def backup_configuration(self) -> Path | None:
        """Backup configuration files and secrets.

        Returns:
            Path to created backup archive
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config_{timestamp}.tar.gz"
        backup_file = self.backup_dirs["config"] / backup_name

        logger.info(f"Creating configuration backup: {backup_file}")

        try:
            # Define configuration paths to backup
            config_paths = [
                Path("/app/config"),
                Path("/app/.env"),
                Path("/app/pyproject.toml"),
                Path("/app/alembic.ini"),
                Path("/app/k8s"),
                Path("/app/docker-compose.prod.yml"),
                Path("/app/docker/monitoring"),
            ]

            # Create tar archive
            with tarfile.open(backup_file, "w:gz") as tar:
                for config_path in config_paths:
                    if config_path.exists():
                        tar.add(config_path, arcname=config_path.name)
                        logger.info(f"Added to config backup: {config_path}")

            # Create metadata
            await self._create_backup_metadata(backup_file, "config")

            logger.info(f"Configuration backup completed: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            if backup_file.exists():
                backup_file.unlink()
            return None

    async def backup_redis_data(self) -> Path | None:
        """Backup Redis data and configuration.

        Returns:
            Path to created backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"redis_{timestamp}.rdb"
        backup_file = self.backup_dirs["database"] / backup_name

        logger.info(f"Creating Redis backup: {backup_file}")

        try:
            # Connect to Redis
            redis_client = redis.from_url(self.redis_url)

            # Trigger Redis BGSAVE
            await redis_client.bgsave()

            # Wait for background save to complete
            while True:
                info = await redis_client.info("persistence")
                if info.get("rdb_bgsave_in_progress", 0) == 0:
                    break
                await asyncio.sleep(1)

            # Copy Redis dump file
            redis_dump_path = Path("/data/dump.rdb")  # Default Redis dump location
            if redis_dump_path.exists():
                shutil.copy2(redis_dump_path, backup_file)
            else:
                logger.warning("Redis dump file not found at expected location")
                return None

            await redis_client.close()

            # Create metadata
            await self._create_backup_metadata(backup_file, "redis")

            logger.info(f"Redis backup completed: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Redis backup failed: {e}")
            return None

    async def backup_logs(self) -> Path | None:
        """Backup application logs.

        Returns:
            Path to created backup archive
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"logs_{timestamp}.tar.gz"
        backup_file = self.backup_dirs["logs"] / backup_name

        logger.info(f"Creating logs backup: {backup_file}")

        try:
            # Define log paths to backup
            log_paths = [
                Path("/app/logs"),
                Path("/var/log/malaria-prediction"),
                Path("/var/log/nginx"),
                Path("/var/log/postgresql"),
            ]

            # Create tar archive
            with tarfile.open(backup_file, "w:gz") as tar:
                for log_path in log_paths:
                    if log_path.exists():
                        tar.add(log_path, arcname=log_path.name)
                        logger.info(f"Added to logs backup: {log_path}")

            # Create metadata
            await self._create_backup_metadata(backup_file, "logs")

            logger.info(f"Logs backup completed: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Logs backup failed: {e}")
            if backup_file.exists():
                backup_file.unlink()
            return None

    async def create_complete_backup(self) -> Path | None:
        """Create a complete system backup including all components.

        Returns:
            Path to created complete backup archive
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"complete_backup_{timestamp}"
        backup_dir = self.backup_dirs["complete"] / backup_name
        backup_dir.mkdir(exist_ok=True)

        logger.info(f"Creating complete system backup: {backup_dir}")

        backup_results = {}

        try:
            # Create all component backups
            backup_tasks = [
                ("database", self.backup_database("full")),
                ("models", self.backup_models()),
                ("config", self.backup_configuration()),
                ("redis", self.backup_redis_data()),
                ("logs", self.backup_logs()),
            ]

            # Execute backups concurrently
            for component, task in backup_tasks:
                try:
                    result = await task
                    if result:
                        # Move backup to complete backup directory
                        dest_path = backup_dir / result.name
                        shutil.move(str(result), str(dest_path))
                        backup_results[component] = str(dest_path)
                        logger.info(f"Completed {component} backup")
                    else:
                        backup_results[component] = None
                        logger.error(f"Failed to create {component} backup")
                except Exception as e:
                    logger.error(f"Error creating {component} backup: {e}")
                    backup_results[component] = None

            # Create manifest file
            manifest = {
                "backup_timestamp": timestamp,
                "backup_type": "complete",
                "components": backup_results,
                "total_size_bytes": sum(
                    Path(path).stat().st_size
                    for path in backup_results.values()
                    if path and Path(path).exists()
                ),
            }

            manifest_file = backup_dir / "manifest.json"
            async with aiofiles.open(manifest_file, "w") as f:
                await f.write(json.dumps(manifest, indent=2))

            # Create final archive
            final_archive = backup_dir.with_suffix(".tar.gz")
            with tarfile.open(final_archive, "w:gz") as tar:
                tar.add(backup_dir, arcname=backup_name)

            # Cleanup temporary directory
            shutil.rmtree(backup_dir)

            logger.info(f"Complete backup created: {final_archive}")
            return final_archive

        except Exception as e:
            logger.error(f"Complete backup failed: {e}")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            return None

    async def encrypt_and_upload_backup(self, backup_file: Path) -> bool:
        """Encrypt backup and upload to remote storage.

        Args:
            backup_file: Path to backup file

        Returns:
            True if successful, False otherwise
        """
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False

        try:
            # Encrypt backup
            encrypted_file = backup_file.with_suffix(backup_file.suffix + ".enc")
            self.encryption.encrypt_file(backup_file, encrypted_file)
            logger.info(f"Encrypted backup: {encrypted_file}")

            # Upload to S3 if configured
            if self.s3_storage:
                s3_key = f"malaria-prediction-dr/{encrypted_file.name}"
                upload_success = await self.s3_storage.upload_backup(
                    encrypted_file, s3_key
                )

                if upload_success:
                    # Remove local encrypted file after successful upload
                    encrypted_file.unlink()
                    logger.info("Backup encrypted and uploaded successfully")
                    return True
                else:
                    logger.error("Failed to upload encrypted backup")
                    return False
            else:
                logger.info(
                    "No remote storage configured, keeping encrypted backup locally"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to encrypt and upload backup: {e}")
            return False

    async def _create_backup_metadata(
        self, backup_file: Path, backup_component: str, backup_type: str = None
    ) -> None:
        """Create metadata file for backup.

        Args:
            backup_file: Path to backup file
            backup_component: Component that was backed up
            backup_type: Type of backup (if applicable)
        """
        metadata_file = backup_file.with_suffix(".metadata.json")

        try:
            # Get file statistics
            stat = backup_file.stat()

            metadata = {
                "backup_file": backup_file.name,
                "backup_component": backup_component,
                "backup_type": backup_type,
                "created_at": datetime.now().isoformat(),
                "file_size_bytes": stat.st_size,
                "file_size_human": self._human_readable_size(stat.st_size),
                "checksum": await self._calculate_checksum(backup_file),
            }

            # Add component-specific metadata
            if backup_component == "database":
                metadata.update(await self._get_database_metadata())
            elif backup_component == "redis":
                metadata.update(await self._get_redis_metadata())

            async with aiofiles.open(metadata_file, "w") as f:
                await f.write(json.dumps(metadata, indent=2))

        except Exception as e:
            logger.error(f"Failed to create metadata for {backup_file}: {e}")

    async def _get_database_metadata(self) -> dict:
        """Get database-specific metadata."""
        try:
            conn = await asyncpg.connect(self.database_url)

            # Get database size
            db_size = await conn.fetchval(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            )

            # Get table information
            tables = await conn.fetch(
                """
                SELECT schemaname, tablename,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20
            """
            )

            # Get TimescaleDB hypertables
            hypertables = await conn.fetch(
                """
                SELECT hypertable_name, num_chunks
                FROM timescaledb_information.hypertables
                WHERE hypertable_schema = 'public'
            """
            )

            await conn.close()

            return {
                "database_size": db_size,
                "table_count": len(tables),
                "largest_tables": [dict(row) for row in tables[:10]],
                "hypertables": [dict(row) for row in hypertables],
            }
        except Exception as e:
            logger.error(f"Failed to get database metadata: {e}")
            return {}

    async def _get_redis_metadata(self) -> dict:
        """Get Redis-specific metadata."""
        try:
            redis_client = redis.from_url(self.redis_url)
            info = await redis_client.info()
            await redis_client.close()

            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "keys_count": info.get("db0", {}).get("keys", 0)
                if "db0" in info
                else 0,
                "uptime_days": info.get("uptime_in_days"),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis metadata: {e}")
            return {}

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        import hashlib

        sha256_hash = hashlib.sha256()
        async with aiofiles.open(file_path, "rb") as f:
            async for chunk in f:
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    async def cleanup_old_backups(self) -> dict[str, int]:
        """Remove backups older than retention period.

        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cleanup_stats = {}

        for component, backup_dir in self.backup_dirs.items():
            removed_count = 0

            for backup_file in backup_dir.glob("*"):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)

                    if file_time < cutoff_date:
                        try:
                            backup_file.unlink()

                            # Also remove metadata file if exists
                            metadata_file = backup_file.with_suffix(".metadata.json")
                            if metadata_file.exists():
                                metadata_file.unlink()

                            logger.info(f"Removed old backup: {backup_file.name}")
                            removed_count += 1

                        except Exception as e:
                            logger.error(f"Failed to remove backup {backup_file}: {e}")

            cleanup_stats[component] = removed_count

        total_removed = sum(cleanup_stats.values())
        logger.info(f"Backup cleanup completed: {total_removed} files removed")

        return cleanup_stats

    async def verify_backup_integrity(self, backup_file: Path) -> dict:
        """Verify backup file integrity.

        Args:
            backup_file: Path to backup file

        Returns:
            Dictionary with verification results
        """
        verification_results = {
            "file_exists": backup_file.exists(),
            "file_readable": False,
            "metadata_exists": False,
            "checksum_valid": False,
            "file_size_bytes": 0,
            "valid": False,
        }

        if not verification_results["file_exists"]:
            return verification_results

        try:
            # Check file readability
            verification_results["file_size_bytes"] = backup_file.stat().st_size
            verification_results["file_readable"] = True

            # Check metadata file
            metadata_file = backup_file.with_suffix(".metadata.json")
            verification_results["metadata_exists"] = metadata_file.exists()

            # Verify checksum if metadata exists
            if verification_results["metadata_exists"]:
                async with aiofiles.open(metadata_file) as f:
                    metadata = json.loads(await f.read())

                expected_checksum = metadata.get("checksum")
                if expected_checksum:
                    actual_checksum = await self._calculate_checksum(backup_file)
                    verification_results["checksum_valid"] = (
                        expected_checksum == actual_checksum
                    )

            # Overall validity
            verification_results["valid"] = (
                verification_results["file_readable"]
                and verification_results["metadata_exists"]
                and verification_results["checksum_valid"]
            )

            logger.info(f"Backup verification completed for {backup_file.name}")

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            verification_results["error"] = str(e)

        return verification_results


async def main():
    """Main entry point for backup orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Disaster Recovery Backup Orchestrator"
    )
    parser.add_argument("--database-url", required=True, help="PostgreSQL database URL")
    parser.add_argument("--redis-url", required=True, help="Redis connection URL")
    parser.add_argument(
        "--backup-dir",
        default="/var/backups/malaria-prediction",
        help="Backup directory",
    )
    parser.add_argument("--s3-bucket", help="S3 bucket for remote storage")
    parser.add_argument("--encryption-key", help="Encryption key for backups")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to retain backups",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup commands
    backup_parser = subparsers.add_parser("backup", help="Create backups")
    backup_parser.add_argument(
        "--type",
        choices=["database", "models", "config", "redis", "logs", "complete"],
        default="complete",
        help="Backup type",
    )
    backup_parser.add_argument(
        "--upload", action="store_true", help="Upload to remote storage"
    )

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify backup integrity")
    verify_parser.add_argument("backup_file", help="Path to backup file")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Remove old backups")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize orchestrator
    orchestrator = DisasterRecoveryOrchestrator(
        args.database_url,
        args.redis_url,
        args.backup_dir,
        args.s3_bucket,
        args.encryption_key,
        args.retention_days,
    )

    try:
        if args.command == "backup":
            backup_file = None

            if args.type == "database":
                backup_file = await orchestrator.backup_database()
            elif args.type == "models":
                backup_file = await orchestrator.backup_models()
            elif args.type == "config":
                backup_file = await orchestrator.backup_configuration()
            elif args.type == "redis":
                backup_file = await orchestrator.backup_redis_data()
            elif args.type == "logs":
                backup_file = await orchestrator.backup_logs()
            elif args.type == "complete":
                backup_file = await orchestrator.create_complete_backup()

            if backup_file:
                print(f"Backup created: {backup_file}")

                if args.upload:
                    success = await orchestrator.encrypt_and_upload_backup(backup_file)
                    if success:
                        print("Backup encrypted and uploaded successfully")
                    else:
                        print("Failed to encrypt and upload backup")
            else:
                print("Backup creation failed")

        elif args.command == "verify":
            result = await orchestrator.verify_backup_integrity(Path(args.backup_file))
            print(f"Verification result: {json.dumps(result, indent=2)}")

        elif args.command == "cleanup":
            stats = await orchestrator.cleanup_old_backups()
            print(f"Cleanup completed: {json.dumps(stats, indent=2)}")

    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
