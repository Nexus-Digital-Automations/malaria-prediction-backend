#!/usr/bin/env python3
"""
Performance Testing Runner for Malaria Prediction API.

This script provides a unified entry point for running all performance tests,
from quick smoke tests to comprehensive load testing and optimization.
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from performance.cache_optimization import CacheConfig, CacheOptimizer
from performance.database_optimization import DatabaseOptimizer
from performance.locust_config import LoadTestSettings
from performance.monitoring_dashboard import get_monitoring_dashboard
from performance.test_scenarios import PerformanceTestRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceTestSuite:
    """Comprehensive performance test suite runner."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.results = {}

        # Initialize components
        self.load_test_settings = LoadTestSettings()
        self.cache_config = CacheConfig()

        # Apply configuration overrides
        if "api_host" in self.config:
            self.load_test_settings.api_host = self.config["api_host"]

        if "redis_url" in self.config:
            self.cache_config.redis_url = self.config["redis_url"]

    async def run_all_tests(self, include_optimization: bool = True) -> dict:
        """Run the complete performance test suite."""
        logger.info("🚀 Starting comprehensive performance test suite")

        suite_start_time = time.time()

        try:
            # Phase 1: System Optimization (if requested)
            if include_optimization:
                logger.info("📊 Phase 1: System Optimization")
                optimization_results = await self._run_optimization_phase()
                self.results["optimization"] = optimization_results

            # Phase 2: Load Testing
            logger.info("🔥 Phase 2: Load Testing")
            load_test_results = await self._run_load_testing_phase()
            self.results["load_tests"] = load_test_results

            # Phase 3: Performance Monitoring
            logger.info("📈 Phase 3: Performance Monitoring")
            monitoring_results = await self._run_monitoring_phase()
            self.results["monitoring"] = monitoring_results

            # Phase 4: Analysis and Recommendations
            logger.info("🔍 Phase 4: Analysis and Recommendations")
            analysis_results = self._analyze_results()
            self.results["analysis"] = analysis_results

        except Exception as e:
            logger.error(f"Performance test suite failed: {e}")
            self.results["error"] = str(e)

        finally:
            suite_duration = time.time() - suite_start_time
            self.results["suite_duration"] = suite_duration
            self.results["timestamp"] = time.time()

            logger.info(
                f"✅ Performance test suite completed in {suite_duration:.2f} seconds"
            )

        return self.results

    async def _run_optimization_phase(self) -> dict:
        """Run database and cache optimization."""
        optimization_results = {}

        try:
            # Database optimization
            logger.info("Optimizing database performance...")
            db_optimizer = DatabaseOptimizer()

            # Create performance indexes
            index_results = await db_optimizer.create_indexes()
            optimization_results["database_indexes"] = index_results

            # Update table statistics
            stats_results = await db_optimizer.update_table_statistics()
            optimization_results["table_statistics"] = stats_results

            # Benchmark queries
            benchmark_results = await db_optimizer.benchmark_queries()
            optimization_results["query_benchmarks"] = benchmark_results

            # Cache optimization
            logger.info("Initializing cache optimization...")
            cache_optimizer = CacheOptimizer(self.cache_config)
            cache_initialized = await cache_optimizer.initialize()

            if cache_initialized:
                cache_stats = await cache_optimizer.get_cache_statistics()
                optimization_results["cache_initialization"] = {
                    "success": True,
                    "initial_stats": cache_stats,
                }
            else:
                optimization_results["cache_initialization"] = {
                    "success": False,
                    "error": "Failed to initialize Redis cache",
                }

        except Exception as e:
            logger.error(f"Optimization phase failed: {e}")
            optimization_results["error"] = str(e)

        return optimization_results

    async def _run_load_testing_phase(self) -> dict:
        """Run comprehensive load testing scenarios."""
        load_test_results = {}

        try:
            # Initialize test runner
            test_runner = PerformanceTestRunner(self.load_test_settings)

            # Define test scenarios to run
            scenarios_to_run = ["smoke_test", "load_test"]

            # Add stress test if explicitly requested
            if self.config.get("include_stress_tests", False):
                scenarios_to_run.append("stress_test")

            # Run each scenario
            for scenario_name in scenarios_to_run:
                logger.info(f"Running {scenario_name}...")

                try:
                    scenario_result = test_runner.run_scenario_by_name(scenario_name)
                    load_test_results[scenario_name] = scenario_result

                    # Brief pause between scenarios
                    if scenario_name != scenarios_to_run[-1]:
                        logger.info("Waiting 10 seconds before next scenario...")
                        await asyncio.sleep(10)

                except Exception as e:
                    logger.error(f"Scenario {scenario_name} failed: {e}")
                    load_test_results[scenario_name] = {"error": str(e)}

            # Generate comprehensive report
            overall_report = test_runner.generate_comprehensive_report()
            load_test_results["overall_report"] = overall_report

        except Exception as e:
            logger.error(f"Load testing phase failed: {e}")
            load_test_results["error"] = str(e)

        return load_test_results

    async def _run_monitoring_phase(self) -> dict:
        """Run performance monitoring and collect metrics."""
        monitoring_results = {}

        try:
            # Initialize monitoring dashboard
            dashboard = get_monitoring_dashboard()

            # Start monitoring for a brief period to collect baseline metrics
            await dashboard.start_monitoring()

            # Collect metrics for 30 seconds
            logger.info("Collecting performance metrics for 30 seconds...")
            await asyncio.sleep(30)

            # Get current metrics
            current_metrics = await self._collect_current_metrics(dashboard)
            monitoring_results["baseline_metrics"] = current_metrics

            # Stop monitoring
            await dashboard.stop_monitoring()

        except Exception as e:
            logger.error(f"Monitoring phase failed: {e}")
            monitoring_results["error"] = str(e)

        return monitoring_results

    async def _collect_current_metrics(self, dashboard) -> dict:
        """Collect current system metrics."""
        try:
            # Get the latest metrics from the dashboard
            recent_metrics = {}

            # System metrics
            import psutil

            recent_metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
            recent_metrics["memory_percent"] = psutil.virtual_memory().percent
            recent_metrics["disk_usage"] = psutil.disk_usage("/").percent

            # Database metrics
            try:
                from src.malaria_predictor.database.session import (
                    get_connection_pool_status,
                )

                pool_status = await get_connection_pool_status()
                recent_metrics["database_pool"] = pool_status
            except Exception:
                recent_metrics["database_pool"] = {
                    "error": "Could not collect database metrics"
                }

            # Cache metrics (if available)
            try:
                from performance.cache_optimization import get_cache_optimizer

                cache = await get_cache_optimizer()
                cache_stats = await cache.get_cache_statistics()
                recent_metrics["cache_stats"] = cache_stats
            except Exception:
                recent_metrics["cache_stats"] = {
                    "error": "Could not collect cache metrics"
                }

            return recent_metrics

        except Exception as e:
            logger.error(f"Failed to collect current metrics: {e}")
            return {"error": str(e)}

    def _analyze_results(self) -> dict:
        """Analyze all test results and provide recommendations."""
        analysis = {
            "overall_status": "unknown",
            "performance_score": 0,
            "issues_found": [],
            "recommendations": [],
            "summary": {},
        }

        try:
            # Analyze load test results
            load_tests = self.results.get("load_tests", {})

            passed_tests = 0
            total_tests = 0

            for test_name, test_result in load_tests.items():
                if test_name == "overall_report":
                    continue

                total_tests += 1

                if isinstance(test_result, dict) and "error" not in test_result:
                    # Check if test passed based on response time and success rate
                    p95_time = test_result.get("p95_response_time", float("inf"))
                    success_rate = test_result.get("success_rate", 0)

                    if p95_time < 3000 and success_rate > 0.95:  # 3s and 95% success
                        passed_tests += 1
                    else:
                        analysis["issues_found"].append(
                            f"{test_name}: P95 response time {p95_time:.2f}ms, "
                            f"success rate {success_rate:.1%}"
                        )

            # Calculate performance score
            if total_tests > 0:
                analysis["performance_score"] = (passed_tests / total_tests) * 100
                analysis["overall_status"] = (
                    "passed" if passed_tests == total_tests else "failed"
                )

            # Generate recommendations based on issues
            if analysis["issues_found"]:
                analysis["recommendations"].extend(
                    [
                        "Consider implementing database query optimization",
                        "Review and optimize caching strategies",
                        "Consider horizontal scaling for high-load scenarios",
                        "Implement connection pooling optimizations",
                    ]
                )

            # Add optimization results summary
            optimization = self.results.get("optimization", {})
            if "database_indexes" in optimization:
                index_results = optimization["database_indexes"]
                created_indexes = len(index_results.get("created", []))
                if created_indexes > 0:
                    analysis["recommendations"].append(
                        f"Successfully created {created_indexes} performance indexes"
                    )

            # Summary statistics
            analysis["summary"] = {
                "total_tests_run": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": total_tests - passed_tests,
                "performance_score": analysis["performance_score"],
                "has_optimizations": "optimization" in self.results,
            }

        except Exception as e:
            logger.error(f"Analysis phase failed: {e}")
            analysis["error"] = str(e)

        return analysis

    def print_summary(self):
        """Print a comprehensive summary of test results."""
        print("\n" + "=" * 80)
        print("MALARIA PREDICTION API - PERFORMANCE TEST SUITE SUMMARY")
        print("=" * 80)

        analysis = self.results.get("analysis", {})

        # Overall status
        status = analysis.get("overall_status", "unknown").upper()
        print(f"Overall Status: {'✅' if status == 'PASSED' else '❌'} {status}")

        # Performance score
        score = analysis.get("performance_score", 0)
        print(f"Performance Score: {score:.1f}%")

        # Summary statistics
        summary = analysis.get("summary", {})
        print(f"Tests Run: {summary.get('total_tests_run', 0)}")
        print(f"Tests Passed: {summary.get('tests_passed', 0)}")
        print(f"Tests Failed: {summary.get('tests_failed', 0)}")

        # Suite duration
        duration = self.results.get("suite_duration", 0)
        print(f"Suite Duration: {duration:.2f} seconds")

        # Issues found
        issues = analysis.get("issues_found", [])
        if issues:
            print(f"\nIssues Found ({len(issues)}):")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"  • {issue}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more issues")

        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print(f"\nRecommendations ({len(recommendations)}):")
            for rec in recommendations[:5]:  # Show first 5 recommendations
                print(f"  • {rec}")
            if len(recommendations) > 5:
                print(f"  ... and {len(recommendations) - 5} more recommendations")

        print("=" * 80)


async def main():
    """Main entry point for performance testing."""

    parser = argparse.ArgumentParser(
        description="Comprehensive Performance Testing Suite for Malaria Prediction API"
    )

    parser.add_argument(
        "--api-host",
        default="http://localhost:8000",
        help="API host URL to test (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379",
        help="Redis URL for caching tests (default: redis://localhost:6379)",
    )

    parser.add_argument(
        "--skip-optimization",
        action="store_true",
        help="Skip database and cache optimization phase",
    )

    parser.add_argument(
        "--include-stress-tests",
        action="store_true",
        help="Include stress testing scenarios",
    )

    parser.add_argument("--output-file", help="Save detailed results to JSON file")

    parser.add_argument(
        "--quick", action="store_true", help="Run quick smoke tests only"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Prepare configuration
    config = {
        "api_host": args.api_host,
        "redis_url": args.redis_url,
        "include_stress_tests": args.include_stress_tests,
    }

    # Create and run test suite
    test_suite = PerformanceTestSuite(config)

    if args.quick:
        logger.info("Running quick smoke tests only")
        # TODO: Implement quick test mode
        config["quick_mode"] = True

    # Run the test suite
    results = await test_suite.run_all_tests(
        include_optimization=not args.skip_optimization
    )

    # Print summary
    test_suite.print_summary()

    # Save detailed results if requested
    if args.output_file:
        import json

        with open(args.output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Detailed results saved to {args.output_file}")

    # Exit with appropriate code
    analysis = results.get("analysis", {})
    exit_code = 0 if analysis.get("overall_status") == "passed" else 1

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
