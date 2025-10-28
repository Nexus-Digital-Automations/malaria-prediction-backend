"""
Comprehensive Data Source Acquisition Tests.

This module tests all data source acquisition features in the codebase,
documenting what works, what doesn't, and what actions are needed.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from malaria_predictor.config import Settings
from malaria_predictor.services.chirps_client import CHIRPSClient
from malaria_predictor.services.era5_client import ERA5Client
from malaria_predictor.services.map_client import MAPClient
from malaria_predictor.services.modis_client import MODISClient
from malaria_predictor.services.worldpop_client import WorldPopClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataSourceTester:
    """Comprehensive tester for all data source clients."""

    def __init__(self):
        """Initialize tester with settings."""
        self.settings = Settings()
        self.results = {
            'era5': {'status': 'pending', 'details': [], 'errors': []},
            'chirps': {'status': 'pending', 'details': [], 'errors': []},
            'modis': {'status': 'pending', 'details': [], 'errors': []},
            'map': {'status': 'pending', 'details': [], 'errors': []},
            'worldpop': {'status': 'pending', 'details': [], 'errors': []}
        }

    def test_era5_client(self):
        """Test ERA5 climate data client."""
        logger.info("Testing ERA5 Client...")
        source_name = 'era5'

        try:
            # Initialize client
            client = ERA5Client(self.settings)
            self.results[source_name]['details'].append("✓ Client initialization successful")

            # Test authentication check
            try:
                # Check if CDS API config exists
                config_file = Path.home() / ".cdsapirc"
                if config_file.exists():
                    self.results[source_name]['details'].append(f"✓ CDS API config found at {config_file}")
                else:
                    self.results[source_name]['errors'].append(
                        f"⚠ CDS API config NOT found at {config_file}. User action required: Create ~/.cdsapirc with CDS credentials"
                    )
                    self.results[source_name]['status'] = 'needs_user_action'
            except Exception as e:
                self.results[source_name]['errors'].append(f"⚠ Authentication check failed: {e}")

            # Test client methods existence
            methods_to_check = [
                'download_climate_data',
                'download_temperature_data',
                'validate_downloaded_file',
                'list_downloaded_files'
            ]

            for method in methods_to_check:
                if hasattr(client, method):
                    self.results[source_name]['details'].append(f"✓ Method '{method}' available")
                else:
                    self.results[source_name]['errors'].append(f"✗ Method '{method}' missing")

            # Test variable presets
            if hasattr(client, 'VARIABLE_PRESETS'):
                presets = client.VARIABLE_PRESETS.keys()
                self.results[source_name]['details'].append(
                    f"✓ Variable presets available: {', '.join(presets)}"
                )

            # Test regional presets
            if hasattr(client, 'REGIONAL_PRESETS'):
                regions = client.REGIONAL_PRESETS.keys()
                self.results[source_name]['details'].append(
                    f"✓ Regional presets available: {', '.join(regions)}"
                )

            # Check download directory
            download_dir = client.download_directory
            if download_dir.exists():
                self.results[source_name]['details'].append(f"✓ Download directory exists: {download_dir}")
            else:
                self.results[source_name]['details'].append(f"⚠ Download directory will be created: {download_dir}")

            if self.results[source_name]['status'] == 'pending':
                self.results[source_name]['status'] = 'ready_needs_credentials'

        except ImportError as e:
            self.results[source_name]['status'] = 'failed'
            self.results[source_name]['errors'].append(
                f"✗ Import error: {e}. Developer action: Install cdsapi package"
            )
        except Exception as e:
            self.results[source_name]['status'] = 'failed'
            self.results[source_name]['errors'].append(f"✗ Unexpected error: {e}")

    def test_chirps_client(self):
        """Test CHIRPS precipitation data client."""
        logger.info("Testing CHIRPS Client...")
        source_name = 'chirps'

        try:
            # Initialize client
            client = CHIRPSClient(self.settings)
            self.results[source_name]['details'].append("✓ Client initialization successful")

            # CHIRPS requires no authentication
            self.results[source_name]['details'].append("✓ No authentication required (open access)")

            # Test BASE_URL accessibility
            import requests
            try:
                response = requests.head(client.BASE_URL, timeout=10)
                if response.status_code < 400:
                    self.results[source_name]['details'].append(
                        f"✓ CHIRPS server accessible: {client.BASE_URL}"
                    )
                else:
                    self.results[source_name]['errors'].append(
                        f"⚠ CHIRPS server returned status {response.status_code}"
                    )
            except requests.RequestException as e:
                self.results[source_name]['errors'].append(
                    f"⚠ Cannot reach CHIRPS server: {e}"
                )

            # Test client methods existence
            methods_to_check = [
                'download_rainfall_data',
                'process_rainfall_data',
                'validate_rainfall_file',
                'aggregate_to_monthly'
            ]

            for method in methods_to_check:
                if hasattr(client, method):
                    self.results[source_name]['details'].append(f"✓ Method '{method}' available")
                else:
                    self.results[source_name]['errors'].append(f"✗ Method '{method}' missing")

            # Check download directory
            download_dir = client.download_directory
            if download_dir.exists():
                self.results[source_name]['details'].append(f"✓ Download directory exists: {download_dir}")

            # Check for rasterio (required for processing)
            try:
                import rasterio
                self.results[source_name]['details'].append("✓ rasterio library available for GeoTIFF processing")
            except ImportError:
                self.results[source_name]['errors'].append(
                    "⚠ rasterio not installed. Developer action: pip install rasterio"
                )

            self.results[source_name]['status'] = 'ready'
            client.close()

        except Exception as e:
            self.results[source_name]['status'] = 'failed'
            self.results[source_name]['errors'].append(f"✗ Unexpected error: {e}")

    def test_modis_client(self):
        """Test MODIS vegetation indices client."""
        logger.info("Testing MODIS Client...")
        source_name = 'modis'

        try:
            # Initialize client
            client = MODISClient(self.settings)
            self.results[source_name]['details'].append("✓ Client initialization successful")

            # MODIS requires NASA EarthData authentication
            self.results[source_name]['details'].append(
                "⚠ Requires NASA EarthData credentials"
            )
            self.results[source_name]['errors'].append(
                "User action required: Create NASA EarthData account at https://urs.earthdata.nasa.gov/"
            )

            # Test client methods existence
            methods_to_check = [
                'authenticate',
                'download_vegetation_indices',
                'discover_modis_tiles'
            ]

            for method in methods_to_check:
                if hasattr(client, method):
                    self.results[source_name]['details'].append(f"✓ Method '{method}' available")
                else:
                    self.results[source_name]['errors'].append(f"✗ Method '{method}' missing (expected for MODIS)")

            # Check supported products
            if hasattr(client, 'SUPPORTED_PRODUCTS'):
                products = client.SUPPORTED_PRODUCTS
                self.results[source_name]['details'].append(
                    f"✓ Supported products: {', '.join(products)}"
                )

            # Check download directory
            download_dir = client.download_directory
            if download_dir.exists():
                self.results[source_name]['details'].append(f"✓ Download directory exists: {download_dir}")

            # Check for required libraries
            try:
                import rasterio
                self.results[source_name]['details'].append("✓ rasterio library available")
            except ImportError:
                self.results[source_name]['errors'].append(
                    "⚠ rasterio not installed. Developer action: pip install rasterio"
                )

            try:
                import pyproj
                self.results[source_name]['details'].append("✓ pyproj library available for coordinate transformation")
            except ImportError:
                self.results[source_name]['errors'].append(
                    "⚠ pyproj not installed. Developer action: pip install pyproj"
                )

            self.results[source_name]['status'] = 'ready_needs_credentials'

        except Exception as e:
            self.results[source_name]['status'] = 'failed'
            self.results[source_name]['errors'].append(f"✗ Unexpected error: {e}")

    def test_map_client(self):
        """Test Malaria Atlas Project client."""
        logger.info("Testing MAP Client...")
        source_name = 'map'

        try:
            # Initialize client
            client = MAPClient(self.settings)
            self.results[source_name]['details'].append("✓ Client initialization successful")

            # MAP requires no authentication
            self.results[source_name]['details'].append("✓ No authentication required (open access)")

            # Test BASE_URL accessibility
            import requests
            try:
                response = requests.head(client.BASE_URL, timeout=10)
                if response.status_code < 400:
                    self.results[source_name]['details'].append(
                        f"✓ MAP server accessible: {client.BASE_URL}"
                    )
            except requests.RequestException as e:
                self.results[source_name]['errors'].append(
                    f"⚠ Cannot reach MAP server: {e}"
                )

            # Check R availability
            if hasattr(client, '_r_available'):
                if client._r_available:
                    self.results[source_name]['details'].append(
                        "✓ R integration available (enhanced functionality)"
                    )
                else:
                    self.results[source_name]['details'].append(
                        "⚠ R integration not available (will use HTTP fallback)"
                    )
                    self.results[source_name]['details'].append(
                        "Optional: Install R and malariaAtlas package for enhanced features"
                    )

            # Test client methods existence
            methods_to_check = [
                'download_parasite_rate_surface',
                'download_vector_occurrence_data'
            ]

            for method in methods_to_check:
                if hasattr(client, method):
                    self.results[source_name]['details'].append(f"✓ Method '{method}' available")
                else:
                    self.results[source_name]['errors'].append(f"⚠ Method '{method}' may be missing")

            # Check download directory
            download_dir = client.download_directory
            if download_dir.exists():
                self.results[source_name]['details'].append(f"✓ Download directory exists: {download_dir}")

            self.results[source_name]['status'] = 'ready'

        except Exception as e:
            self.results[source_name]['status'] = 'failed'
            self.results[source_name]['errors'].append(f"✗ Unexpected error: {e}")

    def test_worldpop_client(self):
        """Test WorldPop population data client."""
        logger.info("Testing WorldPop Client...")
        source_name = 'worldpop'

        try:
            # Initialize client
            client = WorldPopClient(self.settings)
            self.results[source_name]['details'].append("✓ Client initialization successful")

            # WorldPop requires no authentication
            self.results[source_name]['details'].append("✓ No authentication required (open access)")

            # Verify FTP removed for security
            if hasattr(client, 'FTP_BASE_URL'):
                self.results[source_name]['errors'].append(
                    "✗ SECURITY: FTP support should be removed (insecure)"
                )
            else:
                self.results[source_name]['details'].append(
                    "✓ SECURITY: FTP properly removed, using HTTPS only"
                )

            # Test REST API URL accessibility
            import requests
            try:
                response = requests.head(client.REST_BASE_URL, timeout=10)
                if response.status_code < 400:
                    self.results[source_name]['details'].append(
                        f"✓ WorldPop REST API accessible: {client.REST_BASE_URL}"
                    )
            except requests.RequestException as e:
                self.results[source_name]['errors'].append(
                    f"⚠ Cannot reach WorldPop server: {e}"
                )

            # Test client methods existence
            methods_to_check = [
                'download_population_data',
                'discover_available_datasets',
                'calculate_population_at_risk'
            ]

            for method in methods_to_check:
                if hasattr(client, method):
                    self.results[source_name]['details'].append(f"✓ Method '{method}' available")
                else:
                    self.results[source_name]['errors'].append(f"⚠ Method '{method}' may be missing")

            # Check download directory
            download_dir = client.download_directory
            if download_dir.exists():
                self.results[source_name]['details'].append(f"✓ Download directory exists: {download_dir}")

            # Check for rasterio (required for processing)
            try:
                import rasterio
                self.results[source_name]['details'].append("✓ rasterio library available")
            except ImportError:
                self.results[source_name]['errors'].append(
                    "⚠ rasterio not installed. Developer action: pip install rasterio"
                )

            self.results[source_name]['status'] = 'ready'

        except Exception as e:
            self.results[source_name]['status'] = 'failed'
            self.results[source_name]['errors'].append(f"✗ Unexpected error: {e}")

    def run_all_tests(self):
        """Run all data source tests."""
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE DATA SOURCE TESTS")
        logger.info("=" * 80)

        self.test_era5_client()
        self.test_chirps_client()
        self.test_modis_client()
        self.test_map_client()
        self.test_worldpop_client()

        return self.results

    def generate_summary(self):
        """Generate test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)

        for source, data in self.results.items():
            status_icon = {
                'ready': '✓',
                'ready_needs_credentials': '⚠',
                'needs_user_action': '⚠',
                'failed': '✗',
                'pending': '○'
            }.get(data['status'], '?')

            logger.info(f"\n{status_icon} {source.upper()}: {data['status']}")

            if data['details']:
                logger.info("  Details:")
                for detail in data['details']:
                    logger.info(f"    {detail}")

            if data['errors']:
                logger.info("  Issues/Actions Required:")
                for error in data['errors']:
                    logger.info(f"    {error}")


def main():
    """Run comprehensive data source tests."""
    tester = DataSourceTester()
    results = tester.run_all_tests()
    tester.generate_summary()

    return results


if __name__ == "__main__":
    results = main()
