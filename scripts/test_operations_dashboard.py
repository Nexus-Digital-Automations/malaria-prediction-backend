#!/usr/bin/env python3
"""
Operations Dashboard Testing Script.

This script provides comprehensive testing for the production operations dashboard
including API endpoints, WebSocket connections, alert generation, and dashboard rendering.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime

import aiohttp
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OperationsDashboardTester:
    """Comprehensive testing suite for the operations dashboard."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.websocket_url = "ws://localhost:8000/ws/operations-dashboard"
        self.session = None
        self.test_results = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        logger.info(f"{status}: {test_name} - {details}")

    async def test_api_endpoints(self):
        """Test all operations dashboard API endpoints."""
        logger.info("🧪 Testing API Endpoints...")

        endpoints = [
            ("GET", "/operations/summary", "Dashboard summary"),
            ("GET", "/operations/alerts", "Active alerts"),
            ("GET", "/operations/alerts/history", "Alert history"),
            ("GET", "/operations/health/detailed", "Detailed health status"),
            ("GET", "/operations/metrics/prometheus", "Prometheus metrics"),
            ("GET", "/operations/config/grafana", "Grafana config"),
            ("GET", "/operations/config/prometheus-alerts", "Prometheus alerts config"),
            ("GET", "/operations/system/resources", "System resources"),
            ("GET", "/operations/database/status", "Database status"),
            ("GET", "/operations/cache/status", "Cache status"),
            ("GET", "/operations/models/status", "ML models status"),
        ]

        for method, endpoint, description in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                async with self.session.request(method, url, timeout=10) as response:
                    if response.status == 200:
                        await response.json()
                        self.log_test_result(
                            f"API {method} {endpoint}",
                            True,
                            f"{description} - Status: {response.status}",
                        )
                    else:
                        self.log_test_result(
                            f"API {method} {endpoint}",
                            False,
                            f"{description} - Status: {response.status}",
                        )
            except Exception as e:
                self.log_test_result(
                    f"API {method} {endpoint}",
                    False,
                    f"{description} - Error: {str(e)}",
                )

    async def test_dashboard_html(self):
        """Test dashboard HTML page rendering."""
        logger.info("🧪 Testing Dashboard HTML...")

        try:
            url = f"{self.base_url}/operations/dashboard"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html_content = await response.text()

                    # Check for key dashboard elements
                    required_elements = [
                        "Malaria Prediction - Production Operations Dashboard",
                        "System Health Status",
                        "API Request Rate",
                        "Error Rate",
                        "ML Predictions",
                        "WebSocket",
                        "Chart.js",
                    ]

                    missing_elements = []
                    for element in required_elements:
                        if element not in html_content:
                            missing_elements.append(element)

                    if not missing_elements:
                        self.log_test_result(
                            "Dashboard HTML Rendering",
                            True,
                            "All required elements present",
                        )
                    else:
                        self.log_test_result(
                            "Dashboard HTML Rendering",
                            False,
                            f"Missing elements: {missing_elements}",
                        )
                else:
                    self.log_test_result(
                        "Dashboard HTML Rendering", False, f"HTTP {response.status}"
                    )
        except Exception as e:
            self.log_test_result("Dashboard HTML Rendering", False, f"Error: {str(e)}")

    async def test_websocket_connection(self):
        """Test WebSocket connection and real-time updates."""
        logger.info("🧪 Testing WebSocket Connection...")

        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                # Test connection establishment
                self.log_test_result(
                    "WebSocket Connection", True, "Connection established successfully"
                )

                # Wait for initial data
                try:
                    initial_message = await asyncio.wait_for(
                        websocket.recv(), timeout=5
                    )
                    data = json.loads(initial_message)

                    if data.get("type") == "initial_state":
                        self.log_test_result(
                            "WebSocket Initial Data",
                            True,
                            "Received initial dashboard state",
                        )
                    else:
                        self.log_test_result(
                            "WebSocket Initial Data",
                            False,
                            f"Unexpected message type: {data.get('type')}",
                        )
                except TimeoutError:
                    self.log_test_result(
                        "WebSocket Initial Data",
                        False,
                        "Timeout waiting for initial data",
                    )

                # Test ping-pong
                await websocket.send("ping")
                try:
                    pong_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    if pong_response == "pong":
                        self.log_test_result(
                            "WebSocket Ping-Pong",
                            True,
                            "Ping-pong communication working",
                        )
                    else:
                        self.log_test_result(
                            "WebSocket Ping-Pong",
                            False,
                            f"Unexpected response: {pong_response}",
                        )
                except TimeoutError:
                    self.log_test_result(
                        "WebSocket Ping-Pong",
                        False,
                        "Timeout waiting for pong response",
                    )

        except Exception as e:
            self.log_test_result(
                "WebSocket Connection", False, f"Connection failed: {str(e)}"
            )

    async def test_monitoring_control(self):
        """Test monitoring start/stop control endpoints."""
        logger.info("🧪 Testing Monitoring Control...")

        try:
            # Test start monitoring
            start_url = f"{self.base_url}/operations/monitoring/start"
            async with self.session.post(start_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test_result(
                        "Start Monitoring",
                        True,
                        f"Response: {data.get('message', 'Success')}",
                    )
                else:
                    self.log_test_result(
                        "Start Monitoring", False, f"HTTP {response.status}"
                    )

            # Wait a moment for monitoring to start
            await asyncio.sleep(2)

            # Test stop monitoring
            stop_url = f"{self.base_url}/operations/monitoring/stop"
            async with self.session.post(stop_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test_result(
                        "Stop Monitoring",
                        True,
                        f"Response: {data.get('message', 'Success')}",
                    )
                else:
                    self.log_test_result(
                        "Stop Monitoring", False, f"HTTP {response.status}"
                    )

        except Exception as e:
            self.log_test_result("Monitoring Control", False, f"Error: {str(e)}")

    async def test_dashboard_data_structure(self):
        """Test the structure and content of dashboard data."""
        logger.info("🧪 Testing Dashboard Data Structure...")

        try:
            # Get dashboard summary
            url = f"{self.base_url}/operations/summary"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    # Check required fields
                    required_fields = [
                        "system_status",
                        "active_alerts_count",
                        "performance_summary",
                        "last_update",
                    ]

                    missing_fields = []
                    for field in required_fields:
                        if field not in data:
                            missing_fields.append(field)

                    if not missing_fields:
                        self.log_test_result(
                            "Dashboard Data Structure",
                            True,
                            "All required fields present",
                        )

                        # Check performance summary structure
                        perf_summary = data.get("performance_summary", {})
                        perf_fields = [
                            "api_requests_per_second",
                            "api_error_rate",
                            "average_response_time",
                            "cpu_usage_percent",
                            "memory_usage_percent",
                            "model_prediction_rate",
                            "cache_hit_rate",
                        ]

                        missing_perf_fields = []
                        for field in perf_fields:
                            if field not in perf_summary:
                                missing_perf_fields.append(field)

                        if not missing_perf_fields:
                            self.log_test_result(
                                "Performance Summary Structure",
                                True,
                                "All performance fields present",
                            )
                        else:
                            self.log_test_result(
                                "Performance Summary Structure",
                                False,
                                f"Missing fields: {missing_perf_fields}",
                            )
                    else:
                        self.log_test_result(
                            "Dashboard Data Structure",
                            False,
                            f"Missing fields: {missing_fields}",
                        )
                else:
                    self.log_test_result(
                        "Dashboard Data Structure", False, f"HTTP {response.status}"
                    )
        except Exception as e:
            self.log_test_result("Dashboard Data Structure", False, f"Error: {str(e)}")

    async def test_alert_system(self):
        """Test alert system functionality."""
        logger.info("🧪 Testing Alert System...")

        try:
            # Get active alerts
            alerts_url = f"{self.base_url}/operations/alerts"
            async with self.session.get(alerts_url, timeout=10) as response:
                if response.status == 200:
                    alerts = await response.json()
                    self.log_test_result(
                        "Active Alerts Endpoint",
                        True,
                        f"Retrieved {len(alerts)} active alerts",
                    )
                else:
                    self.log_test_result(
                        "Active Alerts Endpoint", False, f"HTTP {response.status}"
                    )

            # Get alert history
            history_url = f"{self.base_url}/operations/alerts/history?hours=1"
            async with self.session.get(history_url, timeout=10) as response:
                if response.status == 200:
                    history = await response.json()
                    self.log_test_result(
                        "Alert History Endpoint",
                        True,
                        f"Retrieved {len(history)} historical alerts",
                    )
                else:
                    self.log_test_result(
                        "Alert History Endpoint", False, f"HTTP {response.status}"
                    )

        except Exception as e:
            self.log_test_result("Alert System", False, f"Error: {str(e)}")

    async def test_configuration_export(self):
        """Test configuration export functionality."""
        logger.info("🧪 Testing Configuration Export...")

        try:
            # Test Grafana config export
            grafana_url = f"{self.base_url}/operations/config/grafana"
            async with self.session.get(grafana_url, timeout=10) as response:
                if response.status == 200:
                    config = await response.json()
                    if "dashboards" in config:
                        self.log_test_result(
                            "Grafana Config Export",
                            True,
                            f"Exported {len(config['dashboards'])} dashboards",
                        )
                    else:
                        self.log_test_result(
                            "Grafana Config Export",
                            False,
                            "Missing dashboards in config",
                        )
                else:
                    self.log_test_result(
                        "Grafana Config Export", False, f"HTTP {response.status}"
                    )

            # Test Prometheus alerts export
            prometheus_url = f"{self.base_url}/operations/config/prometheus-alerts"
            async with self.session.get(prometheus_url, timeout=10) as response:
                if response.status == 200:
                    config = await response.json()
                    if "rules" in config:
                        self.log_test_result(
                            "Prometheus Alerts Export",
                            True,
                            "Alert rules exported successfully",
                        )
                    else:
                        self.log_test_result(
                            "Prometheus Alerts Export", False, "Missing rules in config"
                        )
                else:
                    self.log_test_result(
                        "Prometheus Alerts Export", False, f"HTTP {response.status}"
                    )

        except Exception as e:
            self.log_test_result("Configuration Export", False, f"Error: {str(e)}")

    async def run_all_tests(self):
        """Run all dashboard tests."""
        logger.info("🚀 Starting Operations Dashboard Tests...")

        start_time = time.time()

        # Run all test suites
        await self.test_api_endpoints()
        await self.test_dashboard_html()
        await self.test_websocket_connection()
        await self.test_monitoring_control()
        await self.test_dashboard_data_structure()
        await self.test_alert_system()
        await self.test_configuration_export()

        end_time = time.time()
        duration = end_time - start_time

        # Generate test report
        self.generate_test_report(duration)

    def generate_test_report(self, duration: float):
        """Generate and display test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        print("\n" + "=" * 80)
        print("🦟 MALARIA PREDICTION OPERATIONS DASHBOARD TEST REPORT")
        print("=" * 80)
        print(f"⏱️  Test Duration: {duration:.2f} seconds")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()

        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()

        print("✅ PASSED TESTS:")
        print("-" * 40)
        for result in self.test_results:
            if result["success"]:
                print(f"  • {result['test']}: {result['details']}")
        print()

        # Overall status
        if success_rate >= 95:
            print("🎉 OVERALL STATUS: EXCELLENT - Dashboard is production ready!")
        elif success_rate >= 85:
            print("✅ OVERALL STATUS: GOOD - Minor issues to address")
        elif success_rate >= 70:
            print("⚠️  OVERALL STATUS: NEEDS ATTENTION - Several issues detected")
        else:
            print(
                "🚨 OVERALL STATUS: CRITICAL - Major issues require immediate attention"
            )

        print("=" * 80)


async def main():
    """Main test runner."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"🧪 Testing Operations Dashboard at: {base_url}")
    print("=" * 60)

    async with OperationsDashboardTester(base_url) as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
