"""Basic CLI tests to improve coverage."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from malaria_predictor.cli import app


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


def test_cli_version(runner):
    """Test version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "malaria-predictor" in result.stdout


def test_cli_help(runner):
    """Test help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI-powered malaria outbreak prediction system" in result.stdout


@patch("malaria_predictor.services.era5_client.ERA5Client")
def test_era5_ingest_help(mock_era5_client, runner):
    """Test ERA5 ingestion help."""
    result = runner.invoke(app, ["ingest-era5", "--help"])
    assert result.exit_code == 0
    assert "Download ERA5 climate data" in result.stdout


@patch("malaria_predictor.services.chirps_client.CHIRPSClient")
def test_chirps_ingest_help(mock_chirps_client, runner):
    """Test CHIRPS ingestion help."""
    result = runner.invoke(app, ["ingest-chirps", "--help"])
    assert result.exit_code == 0
    assert "Download CHIRPS rainfall data" in result.stdout


@patch("malaria_predictor.services.map_client.MAPClient")
def test_map_ingest_help(mock_map_client, runner):
    """Test MAP ingestion help."""
    result = runner.invoke(app, ["ingest-map", "--help"])
    assert result.exit_code == 0
    assert "Download MAP data" in result.stdout


@patch("malaria_predictor.services.worldpop_client.WorldPopClient")
def test_worldpop_analysis_help(mock_worldpop_client, runner):
    """Test WorldPop analysis help."""
    result = runner.invoke(app, ["population-analysis", "--help"])
    assert result.exit_code == 0
    assert "Analyze population demographics" in result.stdout


@patch("malaria_predictor.services.modis_client.MODISClient")
def test_modis_ingest_help(mock_modis_client, runner):
    """Test MODIS ingestion help."""
    result = runner.invoke(app, ["ingest-modis", "--help"])
    assert result.exit_code == 0
    assert "Download MODIS vegetation data" in result.stdout


def test_ingest_data_help(runner):
    """Test general data ingestion help."""
    result = runner.invoke(app, ["ingest-data", "--help"])
    assert result.exit_code == 0
    assert "Download and process all environmental data" in result.stdout


@patch("malaria_predictor.services.era5_client.ERA5Client")
@patch("malaria_predictor.services.chirps_client.CHIRPSClient")
@patch("malaria_predictor.services.map_client.MAPClient")
@patch("malaria_predictor.services.worldpop_client.WorldPopClient")
@patch("malaria_predictor.services.modis_client.MODISClient")
def test_ingest_data_dry_run(
    mock_modis, mock_worldpop, mock_map, mock_chirps, mock_era5, runner
):
    """Test data ingestion with dry run."""
    result = runner.invoke(app, ["ingest-data", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN MODE" in result.stdout


def test_invalid_bounds_format(runner):
    """Test invalid bounds format handling."""
    result = runner.invoke(app, ["population-analysis", "--area-bounds", "invalid"])
    assert result.exit_code == 1
    assert "Invalid area bounds format" in result.stderr


@patch("malaria_predictor.services.era5_client.ERA5Client")
def test_era5_missing_dependencies(mock_era5_client, runner):
    """Test ERA5 with missing dependencies."""
    mock_era5_client.side_effect = ImportError("cdsapi not found")

    result = runner.invoke(app, ["ingest-era5", "--year", "2023"])
    assert result.exit_code == 1
    assert "dependencies not installed" in result.stderr


@patch("malaria_predictor.services.chirps_client.CHIRPSClient")
def test_chirps_missing_dependencies(mock_chirps_client, runner):
    """Test CHIRPS with missing dependencies."""
    mock_chirps_client.side_effect = ImportError("rasterio not found")

    result = runner.invoke(app, ["ingest-chirps", "--month", "2023-06"])
    assert result.exit_code == 1
    assert "dependencies not installed" in result.stderr


@patch("malaria_predictor.services.map_client.MAPClient")
def test_map_missing_dependencies(mock_map_client, runner):
    """Test MAP with missing dependencies."""
    mock_map_client.side_effect = ImportError("rasterio not found")

    result = runner.invoke(app, ["ingest-map", "--year", "2023"])
    assert result.exit_code == 1
    assert "dependencies not installed" in result.stderr


@patch("malaria_predictor.services.modis_client.MODISClient")
def test_modis_missing_dependencies(mock_modis_client, runner):
    """Test MODIS with missing dependencies."""
    mock_modis_client.side_effect = ImportError("rasterio not found")

    result = runner.invoke(
        app, ["ingest-modis", "--username", "test", "--password", "test"]
    )
    assert result.exit_code == 1
    assert "dependencies not installed" in result.stderr
