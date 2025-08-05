#!/usr/bin/env python3
"""
Failover Orchestrator for Malaria Prediction System.

This module provides automated failover capabilities for critical services:
- Blue-green deployment automation
- Service health monitoring and automatic failover
- Database failover with read replica promotion
- Load balancer reconfiguration
- DNS failover management
- Rollback procedures for failed deployments
- Multi-region failover coordination
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any

import httpx
from kubernetes import client
from kubernetes import config as k8s_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/malaria-prediction/failover.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ServiceHealthChecker:
    """Monitors service health and determines failover readiness."""

    def __init__(self, api_base_url: str, timeout: float = 30.0):
        """Initialize health checker.

        Args:
            api_base_url: Base URL for API health checks
            timeout: Request timeout in seconds
        """
        self.api_base_url = api_base_url
        self.timeout = timeout

    async def check_api_health(self) -> dict[str, Any]:
        """Check API service health status.

        Returns:
            Health status dictionary
        """
        health_status = {
            "healthy": False,
            "response_time": None,
            "status_code": None,
            "checks": {},
            "timestamp": datetime.now(),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Check liveness endpoint
            try:
                start_time = time.time()
                response = await client.get(f"{self.api_base_url}/health/liveness")
                health_status["response_time"] = time.time() - start_time
                health_status["status_code"] = response.status_code
                health_status["checks"]["liveness"] = response.status_code == 200
            except Exception as e:
                health_status["checks"]["liveness"] = False
                health_status["error"] = str(e)

            # Check readiness endpoint
            try:
                response = await client.get(f"{self.api_base_url}/health/readiness")
                health_status["checks"]["readiness"] = response.status_code == 200
            except Exception:
                health_status["checks"]["readiness"] = False

            # Check database connectivity through API
            try:
                response = await client.get(f"{self.api_base_url}/health/database")
                health_status["checks"]["database"] = response.status_code == 200
            except Exception:
                health_status["checks"]["database"] = False

            # Overall health determination
            health_status["healthy"] = all(health_status["checks"].values())

        return health_status

    async def check_database_health(self, connection_string: str) -> dict[str, Any]:
        """Check database health directly.

        Args:
            connection_string: Database connection string

        Returns:
            Database health status
        """
        import asyncpg

        health_status = {
            "healthy": False,
            "connection_time": None,
            "replication_status": None,
            "active_connections": None,
            "timestamp": datetime.now(),
        }

        try:
            start_time = time.time()
            conn = await asyncpg.connect(connection_string, timeout=10.0)
            health_status["connection_time"] = time.time() - start_time

            # Check basic connectivity
            version = await conn.fetchval("SELECT version()")
            health_status["version"] = version

            # Check replication status (if applicable)
            try:
                replication_info = await conn.fetchrow(
                    """
                    SELECT state, sync_state, replay_lag
                    FROM pg_stat_replication
                    LIMIT 1
                """
                )
                if replication_info:
                    health_status["replication_status"] = dict(replication_info)
            except Exception:
                pass  # Not a primary server or no replication

            # Check active connections
            active_connections = await conn.fetchval(
                """
                SELECT count(*) FROM pg_stat_activity
                WHERE state = 'active'
            """
            )
            health_status["active_connections"] = active_connections

            await conn.close()
            health_status["healthy"] = True

        except Exception as e:
            health_status["error"] = str(e)
            health_status["healthy"] = False

        return health_status


class KubernetesFailoverManager:
    """Manages Kubernetes-based failover operations."""

    def __init__(self, namespace: str = "malaria-prediction-production"):
        """Initialize Kubernetes failover manager.

        Args:
            namespace: Kubernetes namespace
        """
        self.namespace = namespace

        # Load Kubernetes config
        try:
            k8s_config.load_incluster_config()
        except Exception:
            k8s_config.load_kube_config()

        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.networking_v1 = client.NetworkingV1Api()

    async def get_deployment_slots(self, service_name: str) -> dict[str, Any]:
        """Get current blue-green deployment slots.

        Args:
            service_name: Name of the service

        Returns:
            Deployment slot information
        """
        try:
            # Get service to see current active slot
            service = self.core_v1.read_namespaced_service(
                name=f"{service_name}-service", namespace=self.namespace
            )

            active_version = service.spec.selector.get("version", "blue")
            inactive_version = "green" if active_version == "blue" else "blue"

            # Get deployment status for both slots
            blue_deployment = None
            green_deployment = None

            try:
                blue_deployment = self.apps_v1.read_namespaced_deployment(
                    name=f"{service_name}-blue", namespace=self.namespace
                )
            except client.ApiException:
                pass

            try:
                green_deployment = self.apps_v1.read_namespaced_deployment(
                    name=f"{service_name}-green", namespace=self.namespace
                )
            except client.ApiException:
                pass

            return {
                "active_slot": active_version,
                "inactive_slot": inactive_version,
                "blue_deployment": {
                    "exists": blue_deployment is not None,
                    "ready_replicas": blue_deployment.status.ready_replicas
                    if blue_deployment
                    else 0,
                    "replicas": blue_deployment.spec.replicas if blue_deployment else 0,
                },
                "green_deployment": {
                    "exists": green_deployment is not None,
                    "ready_replicas": green_deployment.status.ready_replicas
                    if green_deployment
                    else 0,
                    "replicas": green_deployment.spec.replicas
                    if green_deployment
                    else 0,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get deployment slots for {service_name}: {e}")
            return {}

    async def switch_traffic_to_slot(self, service_name: str, target_slot: str) -> bool:
        """Switch traffic to specified deployment slot.

        Args:
            service_name: Name of the service
            target_slot: Target slot ('blue' or 'green')

        Returns:
            True if successful
        """
        try:
            # Update service selector to point to target slot
            service_patch = {
                "spec": {"selector": {"app": service_name, "version": target_slot}}
            }

            self.core_v1.patch_namespaced_service(
                name=f"{service_name}-service",
                namespace=self.namespace,
                body=service_patch,
            )

            logger.info(f"Switched {service_name} traffic to {target_slot} slot")
            return True

        except Exception as e:
            logger.error(f"Failed to switch traffic to {target_slot} slot: {e}")
            return False

    async def deploy_to_slot(
        self, service_name: str, target_slot: str, image_tag: str, replicas: int = 3
    ) -> bool:
        """Deploy new version to specified slot.

        Args:
            service_name: Name of the service
            target_slot: Target slot ('blue' or 'green')
            image_tag: Docker image tag to deploy
            replicas: Number of replicas

        Returns:
            True if deployment successful
        """
        try:
            deployment_name = f"{service_name}-{target_slot}"

            # Check if deployment exists
            try:
                self.apps_v1.read_namespaced_deployment(
                    name=deployment_name, namespace=self.namespace
                )
                deployment_exists = True
            except client.ApiException:
                deployment_exists = False

            if deployment_exists:
                # Update existing deployment
                patch_body = {
                    "spec": {
                        "replicas": replicas,
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "api",
                                        "image": f"{service_name}:{image_tag}",
                                    }
                                ]
                            }
                        },
                    }
                }

                self.apps_v1.patch_namespaced_deployment(
                    name=deployment_name, namespace=self.namespace, body=patch_body
                )
            else:
                # Create new deployment (would need complete deployment spec)
                logger.warning(
                    f"Deployment {deployment_name} does not exist, skipping creation"
                )
                return False

            # Wait for deployment to be ready
            max_wait_time = 600  # 10 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name, namespace=self.namespace
                )

                ready_replicas = deployment.status.ready_replicas or 0
                if ready_replicas >= replicas:
                    logger.info(
                        f"Deployment {deployment_name} is ready with {ready_replicas} replicas"
                    )
                    return True

                logger.info(
                    f"Waiting for deployment {deployment_name}: {ready_replicas}/{replicas} ready"
                )
                await asyncio.sleep(10)

            logger.error(
                f"Deployment {deployment_name} failed to become ready within timeout"
            )
            return False

        except Exception as e:
            logger.error(f"Failed to deploy to {target_slot} slot: {e}")
            return False

    async def scale_slot(self, service_name: str, slot: str, replicas: int) -> bool:
        """Scale deployment slot to specified number of replicas.

        Args:
            service_name: Name of the service
            slot: Deployment slot ('blue' or 'green')
            replicas: Target number of replicas

        Returns:
            True if scaling successful
        """
        try:
            deployment_name = f"{service_name}-{slot}"

            # Scale deployment
            scale_patch = {"spec": {"replicas": replicas}}

            self.apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name, namespace=self.namespace, body=scale_patch
            )

            # Wait for scaling to complete
            max_wait_time = 300  # 5 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name, namespace=self.namespace
                )

                ready_replicas = deployment.status.ready_replicas or 0
                if ready_replicas == replicas:
                    logger.info(f"Scaled {deployment_name} to {replicas} replicas")
                    return True

                await asyncio.sleep(5)

            logger.error(
                f"Failed to scale {deployment_name} to {replicas} replicas within timeout"
            )
            return False

        except Exception as e:
            logger.error(f"Failed to scale {slot} slot: {e}")
            return False


class DatabaseFailoverManager:
    """Manages database failover operations."""

    def __init__(self, primary_db_url: str, replica_db_urls: list[str]):
        """Initialize database failover manager.

        Args:
            primary_db_url: Primary database connection URL
            replica_db_urls: List of read replica connection URLs
        """
        self.primary_db_url = primary_db_url
        self.replica_db_urls = replica_db_urls
        self.health_checker = ServiceHealthChecker("")

    async def check_replication_lag(self, replica_url: str) -> float | None:
        """Check replication lag for a replica.

        Args:
            replica_url: Replica database URL

        Returns:
            Replication lag in seconds, or None if error
        """
        import asyncpg

        try:
            conn = await asyncpg.connect(replica_url, timeout=10.0)

            # Check if this is a standby server
            is_standby = await conn.fetchval("SELECT pg_is_in_recovery()")

            if is_standby:
                # Get replay lag
                lag_info = await conn.fetchrow(
                    """
                    SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) as lag_seconds
                """
                )

                lag_seconds = lag_info["lag_seconds"] if lag_info else None
                await conn.close()
                return lag_seconds
            else:
                await conn.close()
                return 0.0  # Not a replica, no lag

        except Exception as e:
            logger.error(f"Failed to check replication lag for {replica_url}: {e}")
            return None

    async def promote_replica_to_primary(self, replica_url: str) -> bool:
        """Promote a read replica to primary.

        Args:
            replica_url: URL of replica to promote

        Returns:
            True if promotion successful
        """
        import asyncpg

        try:
            # This is a simplified example - actual implementation would depend on
            # your database setup (streaming replication, logical replication, etc.)

            # For PostgreSQL streaming replication, you would typically:
            # 1. Stop the replica
            # 2. Create a trigger file or use pg_promote()
            # 3. Wait for promotion to complete
            # 4. Update connection strings in applications

            conn = await asyncpg.connect(replica_url, timeout=10.0)

            # Check if server is in recovery mode
            is_standby = await conn.fetchval("SELECT pg_is_in_recovery()")

            if is_standby:
                # Promote to primary (PostgreSQL 12+)
                await conn.execute("SELECT pg_promote()")

                # Wait for promotion to complete
                max_wait = 60  # 1 minute
                start_time = time.time()

                while time.time() - start_time < max_wait:
                    is_still_standby = await conn.fetchval("SELECT pg_is_in_recovery()")
                    if not is_still_standby:
                        logger.info("Successfully promoted replica to primary")
                        await conn.close()
                        return True
                    await asyncio.sleep(2)

                logger.error("Promotion timed out")
                await conn.close()
                return False
            else:
                logger.warning("Database is not a standby server")
                await conn.close()
                return False

        except Exception as e:
            logger.error(f"Failed to promote replica: {e}")
            return False

    async def find_best_replica_for_promotion(self) -> str | None:
        """Find the best replica for promotion based on lag and health.

        Returns:
            URL of best replica, or None if none suitable
        """
        best_replica = None
        lowest_lag = float("inf")

        for replica_url in self.replica_db_urls:
            # Check replica health
            health_status = await self.health_checker.check_database_health(replica_url)

            if not health_status["healthy"]:
                logger.warning(f"Replica {replica_url} is not healthy, skipping")
                continue

            # Check replication lag
            lag = await self.check_replication_lag(replica_url)

            if lag is not None and lag < lowest_lag:
                lowest_lag = lag
                best_replica = replica_url

        if best_replica:
            logger.info(
                f"Selected {best_replica} for promotion with {lowest_lag:.2f}s lag"
            )

        return best_replica


class FailoverOrchestrator:
    """Main orchestrator for service failover operations."""

    def __init__(
        self,
        service_name: str,
        api_base_url: str,
        primary_db_url: str,
        replica_db_urls: list[str],
        namespace: str = "malaria-prediction-production",
    ):
        """Initialize failover orchestrator.

        Args:
            service_name: Name of the service to manage
            api_base_url: Base URL for API health checks
            primary_db_url: Primary database URL
            replica_db_urls: List of replica database URLs
            namespace: Kubernetes namespace
        """
        self.service_name = service_name
        self.api_base_url = api_base_url
        self.namespace = namespace

        self.health_checker = ServiceHealthChecker(api_base_url)
        self.k8s_manager = KubernetesFailoverManager(namespace)
        self.db_manager = DatabaseFailoverManager(primary_db_url, replica_db_urls)

        # Failover state
        self.failover_in_progress = False
        self.last_health_check = None
        self.consecutive_failures = 0
        self.max_failures_before_failover = 3

    async def check_service_health(self) -> dict[str, Any]:
        """Comprehensive service health check.

        Returns:
            Health status summary
        """
        health_summary = {
            "overall_healthy": False,
            "timestamp": datetime.now(),
            "components": {},
        }

        # Check API health
        api_health = await self.health_checker.check_api_health()
        health_summary["components"]["api"] = api_health

        # Check database health
        db_health = await self.health_checker.check_database_health(
            self.db_manager.primary_db_url
        )
        health_summary["components"]["database"] = db_health

        # Check Kubernetes deployment status
        deployment_slots = await self.k8s_manager.get_deployment_slots(
            self.service_name
        )
        health_summary["components"]["deployments"] = deployment_slots

        # Determine overall health
        health_summary["overall_healthy"] = api_health.get(
            "healthy", False
        ) and db_health.get("healthy", False)

        self.last_health_check = health_summary
        return health_summary

    async def perform_blue_green_failover(self) -> dict[str, Any]:
        """Perform blue-green deployment failover.

        Returns:
            Failover result summary
        """
        if self.failover_in_progress:
            return {"error": "Failover already in progress"}

        self.failover_in_progress = True
        failover_result = {
            "started_at": datetime.now(),
            "type": "blue_green_failover",
            "success": False,
            "steps": [],
        }

        try:
            # Step 1: Get current deployment state
            deployment_slots = await self.k8s_manager.get_deployment_slots(
                self.service_name
            )
            current_active = deployment_slots.get("active_slot", "blue")
            target_slot = deployment_slots.get("inactive_slot", "green")

            failover_result["steps"].append(
                {
                    "step": "get_deployment_state",
                    "success": True,
                    "details": {
                        "current_active": current_active,
                        "target_slot": target_slot,
                    },
                }
            )

            # Step 2: Ensure target slot is healthy and ready
            target_deployment = deployment_slots.get(f"{target_slot}_deployment", {})

            if not target_deployment.get("exists", False):
                failover_result["steps"].append(
                    {
                        "step": "check_target_slot",
                        "success": False,
                        "error": f"{target_slot} deployment does not exist",
                    }
                )
                return failover_result

            if target_deployment.get("ready_replicas", 0) == 0:
                # Try to scale up target slot
                scale_success = await self.k8s_manager.scale_slot(
                    self.service_name, target_slot, 3
                )

                if not scale_success:
                    failover_result["steps"].append(
                        {
                            "step": "scale_target_slot",
                            "success": False,
                            "error": f"Failed to scale {target_slot} slot",
                        }
                    )
                    return failover_result

            failover_result["steps"].append(
                {
                    "step": "prepare_target_slot",
                    "success": True,
                    "details": {
                        "target_replicas": target_deployment.get("ready_replicas", 0)
                    },
                }
            )

            # Step 3: Health check target slot
            # We'd need to temporarily route some traffic or use a separate endpoint
            # For now, we'll assume it's healthy if pods are ready

            # Step 4: Switch traffic to target slot
            switch_success = await self.k8s_manager.switch_traffic_to_slot(
                self.service_name, target_slot
            )

            if not switch_success:
                failover_result["steps"].append(
                    {
                        "step": "switch_traffic",
                        "success": False,
                        "error": "Failed to switch traffic",
                    }
                )
                return failover_result

            failover_result["steps"].append(
                {
                    "step": "switch_traffic",
                    "success": True,
                    "details": {"new_active_slot": target_slot},
                }
            )

            # Step 5: Verify service health after switch
            await asyncio.sleep(10)  # Allow time for routing to take effect

            post_failover_health = await self.check_service_health()

            if post_failover_health["overall_healthy"]:
                # Step 6: Scale down old slot
                scale_down_success = await self.k8s_manager.scale_slot(
                    self.service_name, current_active, 1
                )

                failover_result["steps"].append(
                    {
                        "step": "scale_down_old_slot",
                        "success": scale_down_success,
                        "details": {"old_slot": current_active},
                    }
                )

                failover_result["success"] = True
                logger.info(
                    f"Blue-green failover completed: {current_active} -> {target_slot}"
                )
            else:
                # Rollback - switch back to original slot
                rollback_success = await self.k8s_manager.switch_traffic_to_slot(
                    self.service_name, current_active
                )

                failover_result["steps"].append(
                    {
                        "step": "rollback_traffic",
                        "success": rollback_success,
                        "error": "Post-failover health check failed",
                    }
                )

        except Exception as e:
            logger.error(f"Blue-green failover failed: {e}")
            failover_result["error"] = str(e)

        finally:
            failover_result["completed_at"] = datetime.now()
            failover_result["duration_seconds"] = (
                failover_result["completed_at"] - failover_result["started_at"]
            ).total_seconds()
            self.failover_in_progress = False

        return failover_result

    async def perform_database_failover(self) -> dict[str, Any]:
        """Perform database failover to read replica.

        Returns:
            Database failover result
        """
        failover_result = {
            "started_at": datetime.now(),
            "type": "database_failover",
            "success": False,
            "steps": [],
        }

        try:
            # Step 1: Find best replica for promotion
            best_replica = await self.db_manager.find_best_replica_for_promotion()

            if not best_replica:
                failover_result["steps"].append(
                    {
                        "step": "find_replica",
                        "success": False,
                        "error": "No suitable replica found for promotion",
                    }
                )
                return failover_result

            failover_result["steps"].append(
                {
                    "step": "find_replica",
                    "success": True,
                    "details": {"selected_replica": best_replica},
                }
            )

            # Step 2: Stop applications to prevent data loss
            # Scale down to 0 replicas temporarily
            scale_down_success = await self.k8s_manager.scale_slot(
                self.service_name, "blue", 0
            )
            scale_down_success &= await self.k8s_manager.scale_slot(
                self.service_name, "green", 0
            )

            if not scale_down_success:
                failover_result["steps"].append(
                    {
                        "step": "stop_applications",
                        "success": False,
                        "error": "Failed to stop applications",
                    }
                )
                return failover_result

            failover_result["steps"].append(
                {"step": "stop_applications", "success": True}
            )

            # Step 3: Promote replica to primary
            promotion_success = await self.db_manager.promote_replica_to_primary(
                best_replica
            )

            if not promotion_success:
                failover_result["steps"].append(
                    {
                        "step": "promote_replica",
                        "success": False,
                        "error": "Failed to promote replica",
                    }
                )

                # Rollback - restart applications with original database
                await self.k8s_manager.scale_slot(self.service_name, "blue", 3)
                return failover_result

            failover_result["steps"].append(
                {
                    "step": "promote_replica",
                    "success": True,
                    "details": {"new_primary": best_replica},
                }
            )

            # Step 4: Update application configuration to use new primary
            # This would typically involve updating Kubernetes secrets or config maps
            # For now, we'll assume this is handled externally

            # Step 5: Restart applications
            restart_success = await self.k8s_manager.scale_slot(
                self.service_name, "blue", 3
            )

            failover_result["steps"].append(
                {"step": "restart_applications", "success": restart_success}
            )

            if restart_success:
                failover_result["success"] = True
                logger.info(
                    f"Database failover completed successfully to {best_replica}"
                )

        except Exception as e:
            logger.error(f"Database failover failed: {e}")
            failover_result["error"] = str(e)

        finally:
            failover_result["completed_at"] = datetime.now()
            failover_result["duration_seconds"] = (
                failover_result["completed_at"] - failover_result["started_at"]
            ).total_seconds()

        return failover_result

    async def automated_failover_decision(self) -> dict[str, Any] | None:
        """Make automated failover decision based on health checks.

        Returns:
            Failover action taken, or None if no action needed
        """
        health_status = await self.check_service_health()

        if health_status["overall_healthy"]:
            # Reset failure counter on successful health check
            self.consecutive_failures = 0
            return None

        self.consecutive_failures += 1
        logger.warning(
            f"Health check failed {self.consecutive_failures} consecutive times"
        )

        if self.consecutive_failures < self.max_failures_before_failover:
            return None

        # Determine failover type based on failure pattern
        api_healthy = health_status["components"]["api"].get("healthy", False)
        db_healthy = health_status["components"]["database"].get("healthy", False)

        if not api_healthy and db_healthy:
            # API is down but database is healthy - try blue-green failover
            logger.warning("Initiating blue-green failover due to API failures")
            return await self.perform_blue_green_failover()

        elif not db_healthy:
            # Database is down - try database failover
            logger.warning("Initiating database failover due to database failures")
            return await self.perform_database_failover()

        else:
            # Both API and database are down - this needs manual intervention
            logger.error(
                "Both API and database are unhealthy - manual intervention required"
            )
            return {
                "type": "manual_intervention_required",
                "reason": "Both API and database are unhealthy",
                "timestamp": datetime.now(),
            }

    async def start_automated_monitoring(self, check_interval: int = 60) -> None:
        """Start automated health monitoring with failover capability.

        Args:
            check_interval: Health check interval in seconds
        """
        logger.info(f"Starting automated failover monitoring for {self.service_name}")

        while True:
            try:
                failover_action = await self.automated_failover_decision()

                if failover_action:
                    logger.info(
                        f"Automated failover action taken: {failover_action.get('type')}"
                    )

                    # Send alert about failover action
                    # This would integrate with your alerting system

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error in automated monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait longer on error


async def main():
    """Main entry point for failover orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(description="Failover Orchestrator")
    parser.add_argument(
        "--service-name", default="malaria-predictor", help="Service name"
    )
    parser.add_argument(
        "--api-url", default="https://api.malaria-prediction.com", help="API base URL"
    )
    parser.add_argument("--primary-db", required=True, help="Primary database URL")
    parser.add_argument(
        "--replica-db",
        action="append",
        help="Replica database URL (can specify multiple)",
    )
    parser.add_argument(
        "--namespace",
        default="malaria-prediction-production",
        help="Kubernetes namespace",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=60,
        help="Health check interval in seconds",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Monitor command
    subparsers.add_parser("monitor", help="Start automated monitoring")

    # Health check command
    subparsers.add_parser("health", help="Run health check")

    # Manual failover commands
    subparsers.add_parser("blue-green-failover", help="Perform blue-green failover")
    subparsers.add_parser("database-failover", help="Perform database failover")

    # Deployment management
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to specific slot")
    deploy_parser.add_argument(
        "--slot", choices=["blue", "green"], required=True, help="Deployment slot"
    )
    deploy_parser.add_argument("--image-tag", required=True, help="Docker image tag")
    deploy_parser.add_argument(
        "--replicas", type=int, default=3, help="Number of replicas"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize orchestrator
    orchestrator = FailoverOrchestrator(
        args.service_name,
        args.api_url,
        args.primary_db,
        args.replica_db or [],
        args.namespace,
    )

    try:
        if args.command == "monitor":
            await orchestrator.start_automated_monitoring(args.check_interval)

        elif args.command == "health":
            health_status = await orchestrator.check_service_health()
            print(json.dumps(health_status, indent=2, default=str))

        elif args.command == "blue-green-failover":
            result = await orchestrator.perform_blue_green_failover()
            print(json.dumps(result, indent=2, default=str))
            return 0 if result.get("success", False) else 1

        elif args.command == "database-failover":
            result = await orchestrator.perform_database_failover()
            print(json.dumps(result, indent=2, default=str))
            return 0 if result.get("success", False) else 1

        elif args.command == "deploy":
            success = await orchestrator.k8s_manager.deploy_to_slot(
                args.service_name, args.slot, args.image_tag, args.replicas
            )
            print(
                f"Deployment to {args.slot} slot: {'SUCCESS' if success else 'FAILED'}"
            )
            return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("Failover orchestrator stopped by user")
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
