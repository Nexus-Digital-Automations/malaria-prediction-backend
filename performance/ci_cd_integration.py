"""
CI/CD Integration for Automated Performance Testing.

This module provides comprehensive CI/CD pipeline integration for automated
performance regression testing, benchmarking, and continuous monitoring.
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PerformanceBenchmark:
    """Performance benchmark definition for CI/CD."""

    name: str
    test_type: str  # load, stress, smoke, endurance
    max_users: int
    duration: str
    success_criteria: dict[str, float]
    timeout_minutes: int = 30
    enabled: bool = True


@dataclass
class RegressionTest:
    """Performance regression test configuration."""

    baseline_file: str
    current_results: dict
    regression_threshold: float = 0.2  # 20% degradation threshold
    metrics_to_compare: list[str] = None


class CICDPerformanceIntegration:
    """CI/CD performance testing integration system."""

    def __init__(self, config_file: str = "performance/ci_cd_config.yml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.benchmarks = self._load_benchmarks()

        # Results storage
        self.results_dir = Path("performance/ci_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Baseline storage
        self.baselines_dir = Path("performance/baselines")
        self.baselines_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        """Load CI/CD configuration from YAML file."""
        default_config = {
            "enabled": True,
            "run_on_pr": True,
            "run_on_merge": True,
            "performance_gates": {
                "max_p95_response_time": 2000,  # ms
                "min_throughput": 50,  # RPS
                "max_error_rate": 0.01,  # 1%
                "min_cache_hit_rate": 0.7,  # 70%
            },
            "notification": {
                "slack_webhook": None,
                "email_recipients": [],
                "github_status": True,
            },
            "artifact_retention_days": 30,
            "baseline_branch": "main",
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file) as f:
                    config_data = yaml.safe_load(f)
                    default_config.update(config_data)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        return default_config

    def _load_benchmarks(self) -> list[PerformanceBenchmark]:
        """Load performance benchmarks configuration."""
        return [
            PerformanceBenchmark(
                name="smoke_test",
                test_type="smoke",
                max_users=5,
                duration="2m",
                success_criteria={
                    "max_p95_response_time": 1000,
                    "min_success_rate": 0.99,
                },
                timeout_minutes=5,
            ),
            PerformanceBenchmark(
                name="load_test",
                test_type="load",
                max_users=50,
                duration="10m",
                success_criteria={
                    "max_p95_response_time": 2000,
                    "min_throughput": 50,
                    "min_success_rate": 0.99,
                },
                timeout_minutes=15,
            ),
            PerformanceBenchmark(
                name="stress_test",
                test_type="stress",
                max_users=200,
                duration="15m",
                success_criteria={
                    "max_p95_response_time": 5000,
                    "min_throughput": 100,
                    "min_success_rate": 0.95,
                },
                timeout_minutes=20,
                enabled=os.getenv("RUN_STRESS_TESTS", "false").lower() == "true",
            ),
        ]

    def generate_github_workflow(self) -> str:
        """Generate GitHub Actions workflow for performance testing."""
        workflow = {
            "name": "Performance Testing",
            "on": {
                "pull_request": {
                    "paths": [
                        "src/**",
                        "performance/**",
                        "requirements.txt",
                        "pyproject.toml",
                    ]
                },
                "push": {"branches": ["main", "develop"]},
                "schedule": [
                    {"cron": "0 6 * * *"}  # Daily at 6 AM
                ],
            },
            "jobs": {
                "performance-tests": {
                    "runs-on": "ubuntu-latest",
                    "timeout-minutes": 60,
                    "services": {
                        "postgres": {
                            "image": "timescale/timescaledb:latest-pg14",
                            "env": {
                                "POSTGRES_PASSWORD": "testpass",
                                "POSTGRES_DB": "malaria_test",
                            },
                            "options": "--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5",
                            "ports": ["5432:5432"],
                        },
                        "redis": {
                            "image": "redis:7-alpine",
                            "options": "--health-cmd 'redis-cli ping' --health-interval 10s --health-timeout 5s --health-retries 5",
                            "ports": ["6379:6379"],
                        },
                    },
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v4",
                            "with": {"fetch-depth": 0},
                        },
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "3.12"},
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -e .[dev] locust",
                        },
                        {
                            "name": "Set up database",
                            "run": "python -m malaria_predictor.cli init-database",
                            "env": {
                                "DATABASE_URL": "postgresql://postgres:testpass@localhost:5432/malaria_test",
                                "REDIS_URL": "redis://localhost:6379",
                            },
                        },
                        {
                            "name": "Start API server",
                            "run": "uvicorn src.malaria_predictor.api.main:app --host 0.0.0.0 --port 8000 &",
                            "env": {
                                "DATABASE_URL": "postgresql://postgres:testpass@localhost:5432/malaria_test",
                                "REDIS_URL": "redis://localhost:6379",
                            },
                        },
                        {
                            "name": "Wait for API to be ready",
                            "run": "sleep 30 && curl -f http://localhost:8000/health || exit 1",
                        },
                        {
                            "name": "Run performance tests",
                            "run": "python performance/ci_cd_integration.py --run-all --output-format=github",
                            "env": {
                                "API_HOST": "http://localhost:8000",
                                "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
                            },
                        },
                        {
                            "name": "Upload performance results",
                            "uses": "actions/upload-artifact@v3",
                            "if": "always()",
                            "with": {
                                "name": "performance-results",
                                "path": "performance/ci_results/",
                                "retention-days": 30,
                            },
                        },
                        {
                            "name": "Comment PR with results",
                            "if": "github.event_name == 'pull_request'",
                            "uses": "actions/github-script@v6",
                            "with": {
                                "script": """
                                const fs = require('fs');
                                const path = 'performance/ci_results/pr_comment.md';
                                if (fs.existsSync(path)) {
                                  const body = fs.readFileSync(path, 'utf8');
                                  github.rest.issues.createComment({
                                    issue_number: context.issue.number,
                                    owner: context.repo.owner,
                                    repo: context.repo.repo,
                                    body: body
                                  });
                                }
                                """
                            },
                        },
                    ],
                }
            },
        }

        return yaml.dump(workflow, default_flow_style=False, sort_keys=False)

    def generate_jenkins_pipeline(self) -> str:
        """Generate Jenkins pipeline for performance testing."""
        pipeline = """
pipeline {
    agent any

    parameters {
        choice(
            name: 'TEST_TYPE',
            choices: ['smoke', 'load', 'stress', 'all'],
            description: 'Type of performance test to run'
        )
        booleanParam(
            name: 'UPDATE_BASELINE',
            defaultValue: false,
            description: 'Update performance baseline'
        )
    }

    environment {
        DATABASE_URL = "postgresql://postgres:testpass@localhost:5432/malaria_test"
        REDIS_URL = "redis://localhost:6379"
        API_HOST = "http://localhost:8000"
    }

    stages {
        stage('Setup') {
            steps {
                script {
                    sh 'pip install -e .[dev] locust'
                }
            }
        }

        stage('Start Services') {
            parallel {
                stage('Database') {
                    steps {
                        sh 'docker run -d --name postgres-test -e POSTGRES_PASSWORD=testpass -e POSTGRES_DB=malaria_test -p 5432:5432 timescale/timescaledb:latest-pg14'
                        sh 'sleep 30'  // Wait for DB to start
                    }
                }
                stage('Redis') {
                    steps {
                        sh 'docker run -d --name redis-test -p 6379:6379 redis:7-alpine'
                        sh 'sleep 10'
                    }
                }
            }
        }

        stage('Initialize Database') {
            steps {
                sh 'python -m malaria_predictor.cli init-database'
            }
        }

        stage('Start API') {
            steps {
                sh 'uvicorn src.malaria_predictor.api.main:app --host 0.0.0.0 --port 8000 &'
                sh 'sleep 30'
                sh 'curl -f http://localhost:8000/health'
            }
        }

        stage('Performance Tests') {
            steps {
                script {
                    def testCommand = "python performance/ci_cd_integration.py"

                    if (params.TEST_TYPE == 'all') {
                        testCommand += " --run-all"
                    } else {
                        testCommand += " --test-type=${params.TEST_TYPE}"
                    }

                    if (params.UPDATE_BASELINE) {
                        testCommand += " --update-baseline"
                    }

                    testCommand += " --output-format=jenkins"

                    sh testCommand
                }
            }
        }

        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'performance/ci_results/**', fingerprint: true
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'performance/ci_results',
                    reportFiles: 'performance_report.html',
                    reportName: 'Performance Test Report'
                ])
            }
        }
    }

    post {
        always {
            sh 'docker stop postgres-test redis-test || true'
            sh 'docker rm postgres-test redis-test || true'
            sh 'pkill -f uvicorn || true'
        }

        failure {
            emailext(
                subject: "Performance Test Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Performance tests failed. Check the build logs for details.",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@malaria-predictor.org'}"
            )
        }

        success {
            script {
                if (params.TEST_TYPE == 'all' || params.TEST_TYPE == 'load') {
                    emailext(
                        subject: "Performance Test Passed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "All performance tests passed successfully.",
                        to: "${env.CHANGE_AUTHOR_EMAIL ?: 'team@malaria-predictor.org'}"
                    )
                }
            }
        }
    }
}
        """
        return pipeline

    async def run_ci_performance_tests(
        self, test_types: list[str] = None, update_baseline: bool = False
    ) -> dict:
        """Run performance tests in CI/CD environment."""
        if test_types is None:
            test_types = ["smoke", "load"]

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self._get_environment_info(),
            "test_results": {},
            "overall_status": "passed",
            "performance_gates": {},
            "baseline_comparison": {},
        }

        logger.info(f"Running CI performance tests: {test_types}")

        # Run each test type
        for test_type in test_types:
            benchmark = next(
                (b for b in self.benchmarks if b.test_type == test_type), None
            )
            if not benchmark or not benchmark.enabled:
                logger.warning(f"Benchmark {test_type} not found or disabled")
                continue

            logger.info(f"Running {test_type} performance test")

            try:
                test_result = await self._run_single_test(benchmark)
                results["test_results"][test_type] = test_result

                # Check performance gates
                gate_result = self._check_performance_gates(test_result, benchmark)
                results["performance_gates"][test_type] = gate_result

                if not gate_result["passed"]:
                    results["overall_status"] = "failed"

                # Compare with baseline if available
                baseline_comparison = self._compare_with_baseline(
                    test_type, test_result
                )
                if baseline_comparison:
                    results["baseline_comparison"][test_type] = baseline_comparison

                    if baseline_comparison.get("regression_detected"):
                        results["overall_status"] = "failed"

            except Exception as e:
                logger.error(f"Failed to run {test_type} test: {e}")
                results["test_results"][test_type] = {"error": str(e)}
                results["overall_status"] = "failed"

        # Update baseline if requested and tests passed
        if update_baseline and results["overall_status"] == "passed":
            self._update_baseline(results["test_results"])

        # Save results
        self._save_ci_results(results)

        # Generate reports
        await self._generate_ci_reports(results)

        return results

    async def _run_single_test(self, benchmark: PerformanceBenchmark) -> dict:
        """Run a single performance test benchmark."""
        from .locust_config import LoadTestSettings
        from .test_scenarios import PerformanceTestRunner

        # Configure test settings
        settings = LoadTestSettings()
        settings.api_host = os.getenv("API_HOST", "http://localhost:8000")

        # Create test runner
        runner = PerformanceTestRunner(settings)

        # Run specific scenario
        scenario_result = runner.run_scenario_by_type(benchmark.test_type)

        return scenario_result

    def _check_performance_gates(
        self, test_result: dict, benchmark: PerformanceBenchmark
    ) -> dict:
        """Check if test results pass performance gates."""
        gate_result = {"passed": True, "failures": [], "metrics": {}}

        criteria = benchmark.success_criteria

        # Check P95 response time
        if "max_p95_response_time" in criteria:
            p95_time = test_result.get("p95_response_time", float("inf"))
            gate_result["metrics"]["p95_response_time"] = p95_time

            if p95_time > criteria["max_p95_response_time"]:
                gate_result["passed"] = False
                gate_result["failures"].append(
                    f"P95 response time ({p95_time:.2f}ms) exceeds limit "
                    f"({criteria['max_p95_response_time']:.2f}ms)"
                )

        # Check throughput
        if "min_throughput" in criteria:
            throughput = test_result.get("throughput_rps", 0)
            gate_result["metrics"]["throughput"] = throughput

            if throughput < criteria["min_throughput"]:
                gate_result["passed"] = False
                gate_result["failures"].append(
                    f"Throughput ({throughput:.2f} RPS) below minimum "
                    f"({criteria['min_throughput']} RPS)"
                )

        # Check success rate
        if "min_success_rate" in criteria:
            success_rate = test_result.get("success_rate", 0)
            gate_result["metrics"]["success_rate"] = success_rate

            if success_rate < criteria["min_success_rate"]:
                gate_result["passed"] = False
                gate_result["failures"].append(
                    f"Success rate ({success_rate:.3f}) below minimum "
                    f"({criteria['min_success_rate']:.3f})"
                )

        return gate_result

    def _compare_with_baseline(
        self, test_type: str, current_result: dict
    ) -> dict | None:
        """Compare current results with baseline."""
        baseline_file = self.baselines_dir / f"{test_type}_baseline.json"

        if not baseline_file.exists():
            logger.info(f"No baseline found for {test_type}")
            return None

        try:
            with open(baseline_file) as f:
                baseline = json.load(f)

            comparison = {
                "baseline_date": baseline.get("timestamp"),
                "metrics_comparison": {},
                "regression_detected": False,
                "improvements": [],
                "regressions": [],
            }

            # Compare key metrics
            metrics_to_compare = ["p95_response_time", "throughput_rps", "success_rate"]

            for metric in metrics_to_compare:
                baseline_value = baseline.get(metric)
                current_value = current_result.get(metric)

                if baseline_value is None or current_value is None:
                    continue

                # Calculate percentage change
                if baseline_value != 0:
                    change_pct = (current_value - baseline_value) / baseline_value
                else:
                    change_pct = 0

                comparison["metrics_comparison"][metric] = {
                    "baseline": baseline_value,
                    "current": current_value,
                    "change_percent": change_pct * 100,
                }

                # Check for regression (depends on metric)
                threshold = 0.2  # 20% regression threshold

                if metric == "p95_response_time":
                    # Higher is worse
                    if change_pct > threshold:
                        comparison["regression_detected"] = True
                        comparison["regressions"].append(
                            f"{metric} increased by {change_pct * 100:.1f}%"
                        )
                    elif change_pct < -0.1:  # 10% improvement
                        comparison["improvements"].append(
                            f"{metric} improved by {abs(change_pct) * 100:.1f}%"
                        )

                elif metric in ["throughput_rps", "success_rate"]:
                    # Lower is worse
                    if change_pct < -threshold:
                        comparison["regression_detected"] = True
                        comparison["regressions"].append(
                            f"{metric} decreased by {abs(change_pct) * 100:.1f}%"
                        )
                    elif change_pct > 0.1:  # 10% improvement
                        comparison["improvements"].append(
                            f"{metric} improved by {change_pct * 100:.1f}%"
                        )

            return comparison

        except Exception as e:
            logger.error(f"Failed to compare with baseline: {e}")
            return None

    def _update_baseline(self, test_results: dict):
        """Update performance baselines with current results."""
        timestamp = datetime.utcnow().isoformat()

        for test_type, result in test_results.items():
            if "error" in result:
                continue

            baseline_data = {"timestamp": timestamp, "test_type": test_type, **result}

            baseline_file = self.baselines_dir / f"{test_type}_baseline.json"

            try:
                with open(baseline_file, "w") as f:
                    json.dump(baseline_data, f, indent=2)

                logger.info(f"Updated baseline for {test_type}")

            except Exception as e:
                logger.error(f"Failed to update baseline for {test_type}: {e}")

    def _save_ci_results(self, results: dict):
        """Save CI test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"ci_results_{timestamp}.json"

        try:
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)

            logger.info(f"CI results saved to {results_file}")

        except Exception as e:
            logger.error(f"Failed to save CI results: {e}")

    async def _generate_ci_reports(self, results: dict):
        """Generate CI-specific reports."""
        # Generate GitHub PR comment
        if os.getenv("GITHUB_TOKEN"):
            await self._generate_github_pr_comment(results)

        # Generate HTML report
        self._generate_html_report(results)

        # Generate JUnit XML for Jenkins
        self._generate_junit_xml(results)

    async def _generate_github_pr_comment(self, results: dict):
        """Generate GitHub PR comment with performance results."""
        comment_lines = [
            "## 🦟 Performance Test Results",
            "",
            f"**Overall Status:** {'✅ PASSED' if results['overall_status'] == 'passed' else '❌ FAILED'}",
            f"**Test Date:** {results['timestamp']}",
            "",
        ]

        # Add test results summary
        comment_lines.append("### Test Results")
        comment_lines.append(
            "| Test Type | Status | P95 Response Time | Throughput | Success Rate |"
        )
        comment_lines.append(
            "|-----------|---------|-------------------|------------|--------------|"
        )

        for test_type, result in results["test_results"].items():
            if "error" in result:
                status = "❌ ERROR"
                p95 = "N/A"
                throughput = "N/A"
                success_rate = "N/A"
            else:
                gate_result = results["performance_gates"].get(test_type, {})
                status = "✅ PASS" if gate_result.get("passed", False) else "❌ FAIL"
                p95 = f"{result.get('p95_response_time', 0):.0f}ms"
                throughput = f"{result.get('throughput_rps', 0):.1f} RPS"
                success_rate = f"{result.get('success_rate', 0):.1%}"

            comment_lines.append(
                f"| {test_type} | {status} | {p95} | {throughput} | {success_rate} |"
            )

        # Add baseline comparison
        if results["baseline_comparison"]:
            comment_lines.extend(["", "### Baseline Comparison"])

            for test_type, comparison in results["baseline_comparison"].items():
                if comparison.get("regression_detected"):
                    comment_lines.append(f"⚠️ **Regression detected in {test_type}:**")
                    for regression in comparison["regressions"]:
                        comment_lines.append(f"  - {regression}")

                if comparison.get("improvements"):
                    comment_lines.append(f"🎉 **Improvements in {test_type}:**")
                    for improvement in comparison["improvements"]:
                        comment_lines.append(f"  - {improvement}")

        # Add performance gate failures
        failed_gates = [
            (test_type, gate)
            for test_type, gate in results["performance_gates"].items()
            if not gate.get("passed", True)
        ]

        if failed_gates:
            comment_lines.extend(["", "### Performance Gate Failures"])
            for test_type, gate in failed_gates:
                comment_lines.append(f"**{test_type}:**")
                for failure in gate.get("failures", []):
                    comment_lines.append(f"  - {failure}")

        # Save comment to file for GitHub Action to use
        comment_file = self.results_dir / "pr_comment.md"
        with open(comment_file, "w") as f:
            f.write("\n".join(comment_lines))

    def _generate_html_report(self, results: dict):
        """Generate HTML performance report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .status-pass {{ color: #27ae60; font-weight: bold; }}
        .status-fail {{ color: #e74c3c; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Performance Test Report</h1>
        <p>Generated: {results["timestamp"]}</p>
        <p class="{"status-pass" if results["overall_status"] == "passed" else "status-fail"}">
            Overall Status: {results["overall_status"].upper()}
        </p>
    </div>

    <h2>Test Results Summary</h2>
    <table>
        <tr>
            <th>Test Type</th>
            <th>Status</th>
            <th>P95 Response Time</th>
            <th>Throughput (RPS)</th>
            <th>Success Rate</th>
        </tr>
        """

        for test_type, result in results["test_results"].items():
            if "error" in result:
                status_class = "status-fail"
                status = "ERROR"
                p95 = "N/A"
                throughput = "N/A"
                success_rate = "N/A"
            else:
                gate_result = results["performance_gates"].get(test_type, {})
                passed = gate_result.get("passed", False)
                status_class = "status-pass" if passed else "status-fail"
                status = "PASS" if passed else "FAIL"
                p95 = f"{result.get('p95_response_time', 0):.0f}ms"
                throughput = f"{result.get('throughput_rps', 0):.1f}"
                success_rate = f"{result.get('success_rate', 0):.1%}"

            html_content += f"""
        <tr>
            <td>{test_type}</td>
            <td class="{status_class}">{status}</td>
            <td>{p95}</td>
            <td>{throughput}</td>
            <td>{success_rate}</td>
        </tr>
            """

        html_content += """
    </table>

    <h2>Environment Information</h2>
    <div class="metric">
        <strong>Python Version:</strong> {python_version}<br>
        <strong>Platform:</strong> {platform}<br>
        <strong>CPU Count:</strong> {cpu_count}<br>
        <strong>Memory Total:</strong> {memory_gb:.1f} GB
    </div>
</body>
</html>
        """.format(
            python_version=results["environment"]["python_version"],
            platform=results["environment"]["platform"],
            cpu_count=results["environment"]["cpu_count"],
            memory_gb=results["environment"]["memory_total"] / (1024**3),
        )

        # Save HTML report
        report_file = self.results_dir / "performance_report.html"
        with open(report_file, "w") as f:
            f.write(html_content)

    def _generate_junit_xml(self, results: dict):
        """Generate JUnit XML for Jenkins integration."""
        junit_lines = ['<?xml version="1.0" encoding="UTF-8"?>']

        total_tests = len(results["test_results"])
        failed_tests = sum(
            1 for result in results["test_results"].values() if "error" in result
        )

        junit_lines.append(
            f'<testsuite name="PerformanceTests" tests="{total_tests}" '
            f'failures="{failed_tests}" time="0">'
        )

        for test_type, result in results["test_results"].items():
            if "error" in result:
                junit_lines.extend(
                    [
                        f'  <testcase name="{test_type}" classname="PerformanceTests">',
                        f'    <failure message="Test execution failed">{result["error"]}</failure>',
                        "  </testcase>",
                    ]
                )
            else:
                gate_result = results["performance_gates"].get(test_type, {})
                if gate_result.get("passed", True):
                    junit_lines.append(
                        f'  <testcase name="{test_type}" classname="PerformanceTests"/>'
                    )
                else:
                    failures = "; ".join(gate_result.get("failures", []))
                    junit_lines.extend(
                        [
                            f'  <testcase name="{test_type}" classname="PerformanceTests">',
                            f'    <failure message="Performance gate failed">{failures}</failure>',
                            "  </testcase>",
                        ]
                    )

        junit_lines.append("</testsuite>")

        # Save JUnit XML
        junit_file = self.results_dir / "junit_results.xml"
        with open(junit_file, "w") as f:
            f.write("\n".join(junit_lines))

    def _get_environment_info(self) -> dict:
        """Get environment information for reporting."""
        import platform

        import psutil

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "github_sha": os.getenv("GITHUB_SHA", "unknown"),
            "github_ref": os.getenv("GITHUB_REF", "unknown"),
            "ci_environment": os.getenv("CI", "false"),
        }


def main():
    """Main entry point for CI/CD performance testing."""
    import argparse

    parser = argparse.ArgumentParser(description="CI/CD Performance Testing")
    parser.add_argument(
        "--run-all", action="store_true", help="Run all performance tests"
    )
    parser.add_argument("--test-type", help="Specific test type to run")
    parser.add_argument(
        "--update-baseline", action="store_true", help="Update performance baseline"
    )
    parser.add_argument(
        "--output-format",
        choices=["github", "jenkins", "console"],
        default="console",
        help="Output format",
    )
    parser.add_argument(
        "--generate-workflow",
        choices=["github", "jenkins"],
        help="Generate CI/CD workflow file",
    )

    args = parser.parse_args()

    integration = CICDPerformanceIntegration()

    if args.generate_workflow == "github":
        workflow = integration.generate_github_workflow()
        with open(".github/workflows/performance.yml", "w") as f:
            f.write(workflow)
        print("GitHub workflow generated: .github/workflows/performance.yml")
        return

    elif args.generate_workflow == "jenkins":
        pipeline = integration.generate_jenkins_pipeline()
        with open("Jenkinsfile.performance", "w") as f:
            f.write(pipeline)
        print("Jenkins pipeline generated: Jenkinsfile.performance")
        return

    # Run performance tests
    import asyncio

    async def run_tests():
        test_types = []

        if args.run_all:
            test_types = ["smoke", "load"]
        elif args.test_type:
            test_types = [args.test_type]
        else:
            test_types = ["smoke"]  # Default

        results = await integration.run_ci_performance_tests(
            test_types=test_types, update_baseline=args.update_baseline
        )

        # Output results based on format
        if args.output_format == "console":
            print(f"Performance tests completed: {results['overall_status']}")
            for test_type, result in results["test_results"].items():
                print(f"  {test_type}: {result}")

        # Exit with appropriate code
        sys.exit(0 if results["overall_status"] == "passed" else 1)

    asyncio.run(run_tests())


if __name__ == "__main__":
    main()
