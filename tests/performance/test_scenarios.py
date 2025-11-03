"""
Performance Test Scenarios for Malaria Prediction API.

This module defines comprehensive test scenarios for different types
of performance testing including load, stress, spike, and endurance tests.
"""

import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .locust_config import LOAD_TEST_SCENARIOS, LoadTestSettings

logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Configuration for a specific test scenario."""

    name: str
    description: str
    users: int
    spawn_rate: int
    duration: str
    host: str
    locustfile: str
    additional_args: list[str] = None
    expected_outcomes: dict[str, float] = None


class PerformanceTestRunner:
    """Manages execution of different performance test scenarios."""

    def __init__(self, settings: LoadTestSettings):
        self.settings = settings
        self.test_results = []
        self.current_test = None

        # Ensure output directories exist
        Path("performance/reports").mkdir(parents=True, exist_ok=True)
        Path("performance/logs").mkdir(parents=True, exist_ok=True)

    def create_scenarios(self) -> list[TestScenario]:
        """Create test scenarios based on configuration."""
        scenarios = []

        for name, config in LOAD_TEST_SCENARIOS.items():
            scenario = TestScenario(
                name=name,
                description=config["description"],
                users=config["users"],
                spawn_rate=config["spawn_rate"],
                duration=config["duration"],
                host=self.settings.api_host,
                locustfile="performance/locustfile.py",
                additional_args=self._get_scenario_args(name),
                expected_outcomes=self._get_expected_outcomes(name),
            )
            scenarios.append(scenario)

        return scenarios

    def _get_scenario_args(self, scenario_name: str) -> list[str]:
        """Get additional command line arguments for specific scenarios."""
        args = []

        if scenario_name == "smoke_test":
            args.extend(["--only-summary", "--reset-stats"])

        elif scenario_name == "stress_test":
            args.extend(["--expect-workers", "2"])

        elif scenario_name == "spike_test":
            args.extend(["--step-load", "--step-users", "100", "--step-time", "30s"])

        elif scenario_name == "endurance_test":
            args.extend(
                [
                    "--csv",
                    f"performance/logs/endurance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                ]
            )

        return args

    def _get_expected_outcomes(self, scenario_name: str) -> dict[str, float]:
        """Define expected performance outcomes for each scenario."""
        base_expectations = {
            "max_p95_response_time": 2000,  # ms
            "min_success_rate": 0.99,  # 99%
            "min_throughput": 50,  # RPS
        }

        scenario_expectations = {
            "smoke_test": {
                **base_expectations,
                "max_p95_response_time": 1000,  # Lower expectations for light load
                "min_throughput": 10,
            },
            "load_test": base_expectations,
            "stress_test": {
                **base_expectations,
                "max_p95_response_time": 3000,  # Higher tolerance for stress
                "min_success_rate": 0.95,  # 95%
            },
            "spike_test": {
                **base_expectations,
                "max_p95_response_time": 5000,  # Much higher tolerance for spikes
                "min_success_rate": 0.90,  # 90%
            },
            "endurance_test": {
                **base_expectations,
                "max_p95_response_time": 2500,  # Slight degradation over time acceptable
                "min_success_rate": 0.98,  # 98%
            },
        }

        return scenario_expectations.get(scenario_name, base_expectations)

    def run_scenario(self, scenario: TestScenario) -> dict:
        """Execute a single test scenario."""
        self.current_test = scenario

        logger.info(f"Starting test scenario: {scenario.name}")
        logger.info(f"Description: {scenario.description}")
        logger.info(
            f"Configuration: {scenario.users} users, {scenario.spawn_rate} spawn rate, {scenario.duration}"
        )

        # Prepare Locust command
        cmd = [
            sys.executable,
            "-m",
            "locust",
            "-f",
            scenario.locustfile,
            "--host",
            scenario.host,
            "--users",
            str(scenario.users),
            "--spawn-rate",
            str(scenario.spawn_rate),
            "--run-time",
            scenario.duration,
            "--headless",
            "--html",
            f"performance/reports/{scenario.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "--csv",
            f"performance/logs/{scenario.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        ]

        # Add scenario-specific arguments
        if scenario.additional_args:
            cmd.extend(scenario.additional_args)

        # Execute test
        start_time = time.time()

        try:
            logger.info(f"Executing command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._get_timeout(scenario.duration),
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # Parse results
            test_result = self._parse_test_results(scenario, result, execution_time)

            # Assess performance against expectations
            assessment = self._assess_scenario_performance(scenario, test_result)
            test_result["assessment"] = assessment

            self.test_results.append(test_result)

            logger.info(f"Test scenario completed: {scenario.name}")
            logger.info(
                f"Status: {'PASS' if assessment['meets_expectations'] else 'FAIL'}"
            )

            return test_result

        except subprocess.TimeoutExpired:
            logger.error(f"Test scenario timed out: {scenario.name}")
            return {
                "scenario": scenario.name,
                "status": "timeout",
                "error": "Test execution timed out",
            }

        except Exception as e:
            logger.error(f"Test scenario failed: {scenario.name}, Error: {e}")
            return {"scenario": scenario.name, "status": "error", "error": str(e)}

    def _get_timeout(self, duration_str: str) -> int:
        """Convert duration string to timeout in seconds with buffer."""
        # Parse duration (e.g., "10m", "5s", "1h")
        if duration_str.endswith("s"):
            base_seconds = int(duration_str[:-1])
        elif duration_str.endswith("m"):
            base_seconds = int(duration_str[:-1]) * 60
        elif duration_str.endswith("h"):
            base_seconds = int(duration_str[:-1]) * 3600
        else:
            base_seconds = int(duration_str)  # Assume seconds

        # Add 50% buffer for startup/shutdown
        return int(base_seconds * 1.5)

    def _parse_test_results(
        self,
        scenario: TestScenario,
        result: subprocess.CompletedProcess,
        execution_time: float,
    ) -> dict:
        """Parse Locust test results from command output."""
        test_result = {
            "scenario": scenario.name,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "command_exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

        # Parse key metrics from Locust output
        if result.stdout:
            lines = result.stdout.split("\n")

            for line in lines:
                # Look for summary statistics
                if "requests" in line.lower() and "failures" in line.lower():
                    # Parse request statistics
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            test_result["total_requests"] = int(parts[1])
                            test_result["failures"] = int(parts[3])
                        except (ValueError, IndexError):
                            pass

                elif "rps" in line.lower() or "requests/s" in line.lower():
                    # Parse throughput
                    try:
                        rps_match = line.split()
                        for i, part in enumerate(rps_match):
                            if "rps" in part.lower() or "requests/s" in part.lower():
                                test_result["throughput_rps"] = float(rps_match[i - 1])
                                break
                    except (ValueError, IndexError):
                        pass

                elif "95%" in line:
                    # Parse 95th percentile response time
                    try:
                        p95_parts = line.split()
                        for i, part in enumerate(p95_parts):
                            if "95%" in part:
                                # Response time is usually before the percentile
                                test_result["p95_response_time"] = float(
                                    p95_parts[i - 1]
                                )
                                break
                    except (ValueError, IndexError):
                        pass

        # Calculate derived metrics
        if "total_requests" in test_result and "failures" in test_result:
            total = test_result["total_requests"]
            failures = test_result["failures"]
            test_result["success_rate"] = (total - failures) / total if total > 0 else 0

        return test_result

    def _assess_scenario_performance(
        self, scenario: TestScenario, test_result: dict
    ) -> dict:
        """Assess test results against expected outcomes."""
        assessment = {"meets_expectations": True, "issues": [], "recommendations": []}

        expectations = scenario.expected_outcomes
        if not expectations:
            return assessment

        # Check P95 response time
        p95_time = test_result.get("p95_response_time", float("inf"))
        if p95_time > expectations.get("max_p95_response_time", float("inf")):
            assessment["meets_expectations"] = False
            assessment["issues"].append(
                f"P95 response time ({p95_time:.2f}ms) exceeds expectation "
                f"({expectations['max_p95_response_time']:.2f}ms)"
            )

        # Check success rate
        success_rate = test_result.get("success_rate", 0)
        if success_rate < expectations.get("min_success_rate", 0):
            assessment["meets_expectations"] = False
            assessment["issues"].append(
                f"Success rate ({success_rate:.3f}) below expectation "
                f"({expectations['min_success_rate']:.3f})"
            )

        # Check throughput
        throughput = test_result.get("throughput_rps", 0)
        if throughput < expectations.get("min_throughput", 0):
            assessment["meets_expectations"] = False
            assessment["issues"].append(
                f"Throughput ({throughput:.2f} RPS) below expectation "
                f"({expectations['min_throughput']:.2f} RPS)"
            )

        # Generate recommendations based on issues
        if assessment["issues"]:
            if "response time" in " ".join(assessment["issues"]).lower():
                assessment["recommendations"].append(
                    "Consider implementing caching, optimizing database queries, "
                    "or adding more application instances"
                )

            if "success rate" in " ".join(assessment["issues"]).lower():
                assessment["recommendations"].append(
                    "Investigate error causes and improve error handling. "
                    "Consider implementing circuit breakers and retry logic"
                )

            if "throughput" in " ".join(assessment["issues"]).lower():
                assessment["recommendations"].append(
                    "Scale infrastructure horizontally or optimize application performance. "
                    "Consider load balancing and connection pooling"
                )

        return assessment

    def run_all_scenarios(self, scenarios: list[str] | None = None) -> dict:
        """Run all or selected test scenarios."""
        available_scenarios = self.create_scenarios()

        if scenarios:
            # Filter to requested scenarios
            available_scenarios = [
                s for s in available_scenarios if s.name in scenarios
            ]

        logger.info(f"Running {len(available_scenarios)} test scenarios")

        overall_start = time.time()

        for scenario in available_scenarios:
            self.run_scenario(scenario)

            # Brief pause between scenarios
            if scenario != available_scenarios[-1]:
                logger.info("Waiting 30 seconds before next scenario...")
                time.sleep(30)

        overall_end = time.time()

        # Generate comprehensive report
        report = self._generate_overall_report(overall_end - overall_start)

        return report

    def _generate_overall_report(self, total_execution_time: float) -> dict:
        """Generate comprehensive report across all test scenarios."""
        passed_tests = sum(
            1
            for result in self.test_results
            if result.get("assessment", {}).get("meets_expectations", False)
        )

        total_tests = len(self.test_results)

        report = {
            "test_suite_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_execution_time": total_execution_time,
                "total_scenarios": total_tests,
                "passed_scenarios": passed_tests,
                "failed_scenarios": total_tests - passed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            },
            "scenario_results": self.test_results,
            "recommendations": self._generate_overall_recommendations(),
        }

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance/reports/test_suite_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Test suite report saved: {report_file}")

        # Print summary
        self._print_test_suite_summary(report)

        return report

    def _generate_overall_recommendations(self) -> list[str]:
        """Generate overall recommendations based on all test results."""
        recommendations = []

        # Analyze common issues across scenarios
        all_issues = []
        for result in self.test_results:
            assessment = result.get("assessment", {})
            all_issues.extend(assessment.get("issues", []))

        # Count issue types
        response_time_issues = sum(
            1 for issue in all_issues if "response time" in issue.lower()
        )
        success_rate_issues = sum(
            1 for issue in all_issues if "success rate" in issue.lower()
        )
        throughput_issues = sum(
            1 for issue in all_issues if "throughput" in issue.lower()
        )

        if response_time_issues >= 2:
            recommendations.append(
                "Response time issues detected across multiple scenarios. "
                "Priority: Implement comprehensive caching strategy and database optimization"
            )

        if success_rate_issues >= 2:
            recommendations.append(
                "Reliability issues detected across multiple scenarios. "
                "Priority: Implement robust error handling and circuit breakers"
            )

        if throughput_issues >= 2:
            recommendations.append(
                "Throughput issues detected across multiple scenarios. "
                "Priority: Scale infrastructure and optimize concurrency handling"
            )

        if not recommendations:
            recommendations.append(
                "All performance tests passed! Consider running additional scenarios "
                "or increasing load to identify scalability limits"
            )

        return recommendations

    def _print_test_suite_summary(self, report: dict):
        """Print test suite summary to console."""
        summary = report["test_suite_summary"]

        print("\n" + "=" * 80)
        print("MALARIA PREDICTION API - PERFORMANCE TEST SUITE SUMMARY")
        print("=" * 80)

        print(f"Total Execution Time: {summary['total_execution_time']:.2f} seconds")
        print(f"Total Scenarios: {summary['total_scenarios']}")
        print(f"Passed: {summary['passed_scenarios']}")
        print(f"Failed: {summary['failed_scenarios']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")

        print("\nScenario Results:")
        for result in report["scenario_results"]:
            status = (
                "✅ PASS"
                if result.get("assessment", {}).get("meets_expectations", False)
                else "❌ FAIL"
            )
            print(f"  {result['scenario']}: {status}")

        if report["recommendations"]:
            print("\nOverall Recommendations:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")

        print("=" * 80)


def main():
    """Main entry point for running performance tests."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run performance tests for Malaria Prediction API"
    )
    parser.add_argument("--scenarios", nargs="+", help="Specific scenarios to run")
    parser.add_argument("--host", default="http://localhost:8000", help="API host URL")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    # Load settings
    settings = LoadTestSettings()
    if args.host:
        settings.api_host = args.host

    # Create and run test runner
    runner = PerformanceTestRunner(settings)
    report = runner.run_all_scenarios(args.scenarios)

    # Exit with appropriate code
    success_rate = report["test_suite_summary"]["success_rate"]
    sys.exit(0 if success_rate >= 0.8 else 1)


if __name__ == "__main__":
    main()
