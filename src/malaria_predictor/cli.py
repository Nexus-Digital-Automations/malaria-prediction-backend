"""Command-line interface for the malaria prediction system."""

import typer

from . import __version__


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo(f"malaria-predictor {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="malaria-predictor", help="AI-powered malaria outbreak prediction system"
)


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=version_callback, help="Show version and exit"
    ),
):
    """Malaria Prediction Backend CLI."""
    pass


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server"),
    port: int = typer.Option(8000, help="Port to bind the server"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
) -> None:
    """Start the FastAPI server."""
    import uvicorn

    uvicorn.run(
        "malaria_predictor.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def predict(
    area: str = typer.Argument(..., help="Geographic area to predict for"),
    time_horizon: int = typer.Option(30, help="Days ahead to predict"),
    latitude: float = typer.Option(0.0, help="Latitude in decimal degrees"),
    longitude: float = typer.Option(0.0, help="Longitude in decimal degrees"),
    temperature: float = typer.Option(25.0, help="Mean temperature in Celsius"),
    rainfall: float = typer.Option(150.0, help="Monthly rainfall in mm"),
    humidity: float = typer.Option(75.0, help="Relative humidity percentage"),
    elevation: float = typer.Option(1000.0, help="Elevation in meters"),
) -> None:
    """Make malaria outbreak predictions using environmental risk assessment."""
    from datetime import date

    from .models import EnvironmentalFactors, GeographicLocation
    from .services.risk_calculator import RiskCalculator

    typer.echo(
        f"🔮 Predicting malaria risk for {area} over next {time_horizon} days..."
    )

    # Validation
    if time_horizon < 1 or time_horizon > 365:
        typer.echo("❌ Error: Time horizon must be between 1 and 365 days", err=True)
        raise typer.Exit(1)

    try:
        # Create location and environmental data
        location = GeographicLocation(
            latitude=latitude,
            longitude=longitude,
            area_name=area,
            country_code="XX",  # Placeholder - would be determined from coordinates
        )

        env_factors = EnvironmentalFactors(
            mean_temperature=temperature,
            min_temperature=temperature - 5.0,  # Estimate from mean
            max_temperature=temperature + 5.0,  # Estimate from mean
            monthly_rainfall=rainfall,
            relative_humidity=humidity,
            elevation=elevation,
        )

        # Calculate risk using real business logic
        calculator = RiskCalculator()
        prediction = calculator.create_prediction(
            location=location,
            environmental_data=env_factors,
            prediction_date=date.today(),
            time_horizon_days=time_horizon,
            data_sources=["CLI_input"],
        )

        # Display results
        risk = prediction.risk_assessment
        typer.echo(f"📊 Risk Assessment for {area}:")
        typer.echo(f"   Risk Level: {risk.risk_level.value.upper()}")
        typer.echo(f"   Risk Score: {risk.risk_score:.3f}")
        typer.echo(f"   Confidence: {risk.confidence:.3f}")
        typer.echo(f"   Time Horizon: {time_horizon} days")
        typer.echo("")
        typer.echo("🧮 Contributing Factors:")
        typer.echo(f"   Temperature: {risk.temperature_factor:.3f}")
        typer.echo(f"   Rainfall: {risk.rainfall_factor:.3f}")
        typer.echo(f"   Humidity: {risk.humidity_factor:.3f}")
        typer.echo(f"   Elevation: {risk.elevation_factor:.3f}")
        typer.echo("")
        typer.echo(
            "ℹ️  Note: This uses research-based environmental risk factors. Real data ingestion and ML models will be integrated in future phases."
        )

    except Exception as e:
        typer.echo(f"❌ Error calculating risk: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def ingest_data(
    source: str | None = typer.Option(None, help="Specific data source to ingest"),
    dry_run: bool = typer.Option(
        False, help="Preview what would be ingested without downloading"
    ),
) -> None:
    """Download and process all environmental data."""
    available_sources = ["era5", "chirps", "map", "modis", "worldpop", "all"]

    if source and source not in available_sources:
        typer.echo(f"❌ Error: Unknown data source '{source}'", err=True)
        typer.echo(f"Available sources: {', '.join(available_sources)}")
        raise typer.Exit(1)

    target_source = source or "all"

    typer.echo(f"🌍 Starting data ingestion for: {target_source}")
    if dry_run:
        typer.echo("DRY RUN MODE")
    typer.echo(f"   Mode: {'Dry run (preview only)' if dry_run else 'Live ingestion'}")

    # Handle ERA5 with real implementation
    if target_source == "era5" or target_source == "all":
        _ingest_era5_data(dry_run)

    # Handle CHIRPS with real implementation
    if target_source == "chirps" or target_source == "all":
        _ingest_chirps_data(dry_run)

    # Handle MAP with real implementation
    if target_source == "map" or target_source == "all":
        _ingest_map_data(dry_run)

    # Handle WorldPop with real implementation
    if target_source == "worldpop" or target_source == "all":
        _ingest_worldpop_data(dry_run)

    # Handle MODIS with real implementation
    if target_source == "modis" or target_source == "all":
        _ingest_modis_data(dry_run)

    typer.echo("✅ Data ingestion complete")


@app.command(name="ingest-era5")
def ingest_era5_command(
    year: int = typer.Option(2023, help="Year to download data for"),
    dry_run: bool = typer.Option(
        False, help="Preview what would be downloaded without executing"
    ),
) -> None:
    """Download ERA5 climate data."""
    typer.echo(f"🌡️ Downloading ERA5 data for {year}")
    if dry_run:
        typer.echo("DRY RUN MODE - would download ERA5 climate data")
        return
    _ingest_era5_data(dry_run)


@app.command(name="ingest-chirps")
def ingest_chirps_command(
    month: str = typer.Option("2023-06", help="Month to download in YYYY-MM format"),
    dry_run: bool = typer.Option(
        False, help="Preview what would be downloaded without executing"
    ),
) -> None:
    """Download CHIRPS rainfall data."""
    typer.echo(f"🌧️ Downloading CHIRPS data for {month}")
    if dry_run:
        typer.echo("DRY RUN MODE - would download CHIRPS rainfall data")
        return
    _ingest_chirps_data(dry_run)


@app.command(name="ingest-map")
def ingest_map_command(
    year: int = typer.Option(2023, help="Year to download data for"),
    dry_run: bool = typer.Option(
        False, help="Preview what would be downloaded without executing"
    ),
) -> None:
    """Download MAP data."""
    typer.echo(f"🗺️ Downloading MAP data for {year}")
    if dry_run:
        typer.echo("DRY RUN MODE - would download MAP data")
        return
    _ingest_map_data(dry_run)


@app.command(name="ingest-modis")
def ingest_modis_command(
    username: str = typer.Option(..., help="MODIS username"),
    password: str = typer.Option(..., help="MODIS password"),
    dry_run: bool = typer.Option(
        False, help="Preview what would be downloaded without executing"
    ),
) -> None:
    """Download MODIS vegetation data."""
    typer.echo(f"🌿 Downloading MODIS data with user {username}")
    if dry_run:
        typer.echo("DRY RUN MODE - would download MODIS vegetation data")
        return
    _ingest_modis_data(dry_run)


@app.command()
def population_analysis(
    countries: str = typer.Option("KEN,UGA", help="Comma-separated ISO3 country codes"),
    year: int = typer.Option(2020, help="Target year for population data"),
    output_format: str = typer.Option(
        "summary", help="Output format: summary, detailed, json"
    ),
    calculate_risk: bool = typer.Option(
        False, help="Calculate population at malaria risk"
    ),
    area_bounds: str = typer.Option(
        None, help="Geographic bounds as 'west,south,east,north'"
    ),
) -> None:
    """Analyze population demographics."""
    import json

    from .services.worldpop_client import WorldPopClient

    country_codes = [code.strip().upper() for code in countries.split(",")]

    typer.echo(f"👥 Population Analysis for {', '.join(country_codes)} ({year})")

    # Parse area bounds if provided
    bounds = None
    if area_bounds:
        try:
            bounds = tuple(map(float, area_bounds.split(",")))
            if len(bounds) != 4:
                raise ValueError("Must provide exactly 4 values")
            typer.echo(f"   🗺️  Analysis bounds: {bounds}")
        except ValueError as e:
            typer.echo(f"❌ Invalid area bounds format: {e}", err=True)
            typer.echo(
                "   Expected format: 'west,south,east,north' (e.g., '33,-5,42,5')"
            )
            raise typer.Exit(1) from e

    client = None
    try:
        client = WorldPopClient()

        # Discover available datasets
        typer.echo("   🔍 Discovering available population datasets...")
        available_datasets = client.discover_available_datasets(
            country_codes=country_codes, data_type="population_density", year=year
        )

        if not available_datasets:
            typer.echo("❌ No population data found for specified countries and year")
            return

        analysis_results = {}

        for country_code in country_codes:
            if country_code not in available_datasets:
                typer.echo(f"   ⚠️  No data available for {country_code}")
                continue

            typer.echo(f"   🏁 Analyzing {country_code}...")

            # Download country data
            download_result = client.download_population_data(
                country_codes=[country_code],
                target_year=year,
                data_type="population_density",
            )

            if not download_result.success:
                typer.echo(f"   ❌ Failed to download data for {country_code}")
                continue

            country_analysis = {"country": country_code, "year": year}

            # Extract population data for region
            for file_path in download_result.file_paths:
                analysis_bounds = bounds or (
                    -180,
                    -90,
                    180,
                    90,
                )  # World bounds if not specified

                pop_data = client.extract_population_for_region(
                    file_path, analysis_bounds
                )

                if pop_data:
                    stats = pop_data["statistics"]
                    country_analysis.update(
                        {
                            "total_population": stats["total_population"],
                            "mean_density": stats["mean_density"],
                            "max_density": stats["max_density"],
                            "coverage_ratio": stats["coverage_ratio"],
                        }
                    )

                    # Calculate population at risk if requested
                    if calculate_risk:
                        # Look for MAP risk data
                        risk_file = (
                            file_path.parent.parent
                            / "map"
                            / f"risk_{file_path.stem}.tif"
                        )

                        if risk_file.exists():
                            risk_result = client.calculate_population_at_risk(
                                population_file=file_path,
                                malaria_risk_file=risk_file,
                                area_bounds=analysis_bounds,
                            )

                            if risk_result:
                                country_analysis.update(
                                    {
                                        "population_at_risk": risk_result.population_at_risk,
                                        "risk_percentage": risk_result.risk_percentage,
                                        "high_risk_population": risk_result.high_risk_population,
                                        "children_under_5_at_risk": risk_result.children_under_5_at_risk,
                                    }
                                )
                        else:
                            typer.echo(f"     ⚠️  No risk data found for {country_code}")
                            country_analysis.update(
                                {
                                    "population_at_risk": "No risk data available",
                                    "risk_note": "Run 'malaria-predictor ingest-data map' to download risk surfaces",
                                }
                            )

                break  # Process first file for now

            analysis_results[country_code] = country_analysis

        # Output results based on format
        if output_format == "json":
            typer.echo(json.dumps(analysis_results, indent=2))
        elif output_format == "detailed":
            for country, data in analysis_results.items():
                typer.echo(f"\n📊 {country} Population Analysis ({year}):")
                typer.echo(
                    f"   Total Population: {data.get('total_population', 0):,.0f}"
                )
                typer.echo(
                    f"   Mean Density: {data.get('mean_density', 0):.2f} people/km²"
                )
                typer.echo(
                    f"   Max Density: {data.get('max_density', 0):.2f} people/km²"
                )
                typer.echo(f"   Coverage Ratio: {data.get('coverage_ratio', 0):.2%}")

                if calculate_risk and "population_at_risk" in data:
                    if isinstance(data["population_at_risk"], str):
                        typer.echo(f"   Risk Status: {data['population_at_risk']}")
                        if "risk_note" in data:
                            typer.echo(f"   Note: {data['risk_note']}")
                    else:
                        typer.echo(
                            f"   Population at Risk: {data['population_at_risk']:,.0f}"
                        )
                        typer.echo(
                            f"   Risk Percentage: {data['risk_percentage']:.1f}%"
                        )
                        typer.echo(
                            f"   High Risk Population: {data['high_risk_population']:,.0f}"
                        )
                        typer.echo(
                            f"   Children Under 5 at Risk: {data['children_under_5_at_risk']:,.0f}"
                        )
        else:  # summary format
            typer.echo("\n📊 Population Analysis Summary:")
            total_population = sum(
                data.get("total_population", 0) for data in analysis_results.values()
            )
            typer.echo(f"   Countries Analyzed: {len(analysis_results)}")
            typer.echo(f"   Total Population: {total_population:,.0f}")

            if calculate_risk:
                total_at_risk = sum(
                    data.get("population_at_risk", 0)
                    for data in analysis_results.values()
                    if isinstance(data.get("population_at_risk"), int | float)
                )
                if total_at_risk > 0:
                    risk_pct = (
                        (total_at_risk / total_population * 100)
                        if total_population > 0
                        else 0
                    )
                    typer.echo(
                        f"   Total at Risk: {total_at_risk:,.0f} ({risk_pct:.1f}%)"
                    )

            typer.echo("\n   By Country:")
            for country, data in analysis_results.items():
                pop = data.get("total_population", 0)
                typer.echo(f"     {country}: {pop:,.0f} people")

    except Exception as e:
        typer.echo(f"❌ Error during population analysis: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        if client:
            client.close()


def _ingest_era5_data(dry_run: bool) -> None:
    """Handle ERA5-specific data ingestion."""
    from datetime import date, timedelta

    from .services.era5_client import ERA5Client

    try:
        typer.echo("🌡️  ERA5 Climate Data Ingestion")

        if dry_run:
            typer.echo("   📋 Dry run mode - would download:")
            typer.echo("   • Temperature data (2m, min, max)")
            typer.echo("   • Geographic coverage: Africa region")
            typer.echo("   • Temporal coverage: Last 7 days")
            typer.echo("   • File format: NetCDF")
            return

        client = ERA5Client()

        # Test CDS credentials
        typer.echo("   🔑 Validating CDS API credentials...")
        if not client.validate_credentials():
            typer.echo("❌ Error: CDS API credentials validation failed", err=True)
            typer.echo("   Please ensure ~/.cdsapirc is properly configured")
            typer.echo("   Visit: https://cds.climate.copernicus.eu/how-to-api")
            raise typer.Exit(1)

        typer.echo("   ✅ CDS credentials validated successfully")

        # Download recent temperature data
        end_date = date.today() - timedelta(days=5)  # ERA5 has delay
        start_date = end_date - timedelta(days=6)  # 7 days total

        typer.echo(f"   📅 Downloading data from {start_date} to {end_date}")
        typer.echo("   🌍 Coverage: Africa region (40N, 20W, 35S, 55E)")
        typer.echo("   📊 Variables: 2m temperature (current, min, max)")

        result = client.download_and_validate_temperature_data(start_date, end_date)

        if result.success:
            typer.echo(f"   ✅ Download successful: {result.file_path.name}")
            typer.echo(
                f"   📁 File size: {result.file_size_bytes / 1024 / 1024:.2f} MB"
            )
            typer.echo(
                f"   ⏱️  Duration: {result.download_duration_seconds:.1f} seconds"
            )

            # Show validation results
            validation = client.validate_downloaded_file(result.file_path)
            if validation["success"]:
                typer.echo("   ✅ Data validation passed")
                typer.echo(
                    f"   🔍 Variables found: {', '.join(validation['variables_found'])}"
                )
                if validation.get("temporal_range"):
                    temp_range = validation["temporal_range"]
                    typer.echo(
                        f"   📅 Time range: {temp_range.get('count', 0)} time steps"
                    )
            else:
                typer.echo(
                    f"   ⚠️  Data validation issues: {validation.get('error_message', 'Unknown')}"
                )
        else:
            typer.echo(f"❌ Download failed: {result.error_message}", err=True)
            raise typer.Exit(1)

    except ImportError:
        typer.echo("❌ Error: ERA5 dependencies not installed", err=True)
        typer.echo("   Install with: pip install cdsapi xarray netcdf4")
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"❌ ERA5 ingestion error: {e}", err=True)
        raise typer.Exit(1) from e


def _ingest_chirps_data(dry_run: bool) -> None:
    """Handle CHIRPS-specific data ingestion."""
    from datetime import date, timedelta

    from .services.chirps_client import CHIRPSClient

    try:
        typer.echo("🌧️  CHIRPS Rainfall Data Ingestion")

        if dry_run:
            typer.echo("   📋 Dry run mode - would download:")
            typer.echo("   • Daily rainfall data (0.05° resolution)")
            typer.echo("   • Geographic coverage: Africa region")
            typer.echo("   • Temporal coverage: Last 7 days")
            typer.echo("   • File format: GeoTIFF")
            typer.echo("   • No authentication required")
            return

        client = CHIRPSClient()

        # Download recent rainfall data
        end_date = date.today() - timedelta(days=1)  # CHIRPS has 1-2 day delay
        start_date = end_date - timedelta(days=6)  # 7 days total

        typer.echo(f"   📅 Downloading data from {start_date} to {end_date}")
        typer.echo("   🌍 Coverage: Africa region (20W, 35S, 55E, 40N)")
        typer.echo("   ☔ Variables: Daily precipitation (mm/day)")

        result = client.download_rainfall_data(start_date, end_date, data_type="daily")

        if result.success:
            typer.echo(f"   ✅ Download successful: {result.files_processed} files")
            typer.echo(
                f"   📁 Total size: {result.total_size_bytes / 1024 / 1024:.2f} MB"
            )
            typer.echo(
                f"   ⏱️  Duration: {result.download_duration_seconds:.1f} seconds"
            )

            # Validate downloaded files
            if result.file_paths:
                typer.echo("   🔍 Validating downloaded files...")
                valid_count = 0
                for file_path in result.file_paths[:3]:  # Check first 3 files
                    validation = client.validate_rainfall_file(file_path)
                    if validation["success"]:
                        valid_count += 1

                if valid_count > 0:
                    typer.echo(f"   ✅ Validation passed for {valid_count} files")
                else:
                    typer.echo("   ⚠️  Some files failed validation")
        else:
            typer.echo(f"❌ Download failed: {result.error_message}", err=True)
            raise typer.Exit(1)

        # Clean up resources
        client.close()

    except ImportError:
        typer.echo("❌ Error: CHIRPS dependencies not installed", err=True)
        typer.echo("   Install with: pip install rasterio requests")
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"❌ CHIRPS ingestion error: {e}", err=True)
        raise typer.Exit(1) from e


def _ingest_map_data(dry_run: bool) -> None:
    """Handle MAP-specific data ingestion."""
    from datetime import date

    from .services.map_client import MAPClient

    try:
        typer.echo("🗺️  MAP (Malaria Atlas Project) Data Ingestion")

        if dry_run:
            typer.echo("   📋 Dry run mode - would download:")
            typer.echo("   • Parasite rate surfaces (5km resolution)")
            typer.echo("   • P. falciparum prevalence data")
            typer.echo("   • Vector occurrence data")
            typer.echo("   • Intervention coverage (ITN, IRS)")
            typer.echo("   • Geographic coverage: Africa region")
            typer.echo("   • No authentication required")
            return

        client = MAPClient()

        # Check R availability
        if client._r_available:
            typer.echo("   ✅ R integration available (malariaAtlas package)")
        else:
            typer.echo("   ℹ️  R not available, using HTTP fallback")
            typer.echo("   💡 For full functionality, install R and run:")
            typer.echo("      R -e 'install.packages(\"malariaAtlas\")'")

        # Download recent parasite rate data
        current_year = date.today().year
        data_year = current_year - 2  # MAP data typically has 2-year delay

        typer.echo(f"   📅 Downloading data for year: {data_year}")
        typer.echo("   🌍 Coverage: Africa region (20W, 35S, 55E, 40N)")
        typer.echo("   🦟 Data type: P. falciparum parasite rate (2-10 years)")

        # Download parasite rate surface
        pr_result = client.download_parasite_rate_surface(
            year=data_year, species="Pf", resolution="5km"
        )

        if pr_result.success:
            typer.echo(
                f"   ✅ Parasite rate download successful: {len(pr_result.file_paths)} files"
            )
            typer.echo(
                f"   📁 Total size: {pr_result.total_size_bytes / 1024 / 1024:.2f} MB"
            )
            typer.echo(
                f"   ⏱️  Duration: {pr_result.download_duration_seconds:.1f} seconds"
            )

            # Validate downloaded files
            if pr_result.file_paths:
                typer.echo("   🔍 Validating downloaded files...")
                for file_path in pr_result.file_paths[:1]:  # Validate first file
                    validation = client.validate_raster_file(file_path)
                    if validation["success"]:
                        typer.echo(f"   ✅ Validation passed: {file_path.name}")
                        if validation.get("data_range"):
                            data_range = validation["data_range"]
                            typer.echo(
                                f"      PR range: {data_range.get('min', 0):.1f}% - {data_range.get('max', 0):.1f}%"
                            )
                            typer.echo(
                                f"      Mean PR: {data_range.get('mean', 0):.1f}%"
                            )
                    else:
                        typer.echo(
                            f"   ⚠️  Validation failed: {validation.get('error_message')}"
                        )
        else:
            typer.echo(
                f"   ❌ Parasite rate download failed: {pr_result.error_message}"
            )

        # Download vector occurrence data
        typer.echo("   🦟 Downloading Anopheles vector occurrence data...")
        vector_result = client.download_vector_occurrence_data(
            species_complex="gambiae", start_year=data_year - 5, end_year=data_year
        )

        if vector_result.success:
            typer.echo("   ✅ Vector data download successful")
            typer.echo(f"   📁 Files: {len(vector_result.file_paths)}")
        else:
            typer.echo(
                f"   ⚠️  Vector data download failed: {vector_result.error_message}"
            )

        # Clean up resources
        client.close()

    except ImportError:
        typer.echo("❌ Error: MAP dependencies not installed", err=True)
        typer.echo("   Install with: pip install rasterio shapely")
        typer.echo("   For full functionality: Install R and malariaAtlas package")
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"❌ MAP ingestion error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def era5_setup() -> None:
    """Set up automated ERA5 data downloads."""
    from .services.era5_client import ERA5Client

    try:
        typer.echo("⚙️  Setting up ERA5 automated data ingestion")

        client = ERA5Client()

        # Validate credentials first
        typer.echo("   🔑 Validating CDS API credentials...")
        if not client.validate_credentials():
            typer.echo("❌ Error: CDS API credentials validation failed", err=True)
            typer.echo("")
            typer.echo("📖 Setup Instructions:")
            typer.echo("   1. Register at: https://cds.climate.copernicus.eu/")
            typer.echo("   2. Create ~/.cdsapirc file with your credentials")
            typer.echo("   3. Accept terms for ERA5 datasets")
            typer.echo("   4. Run this command again")
            raise typer.Exit(1)

        typer.echo("   ✅ Credentials validated")

        # Set up automated schedules
        typer.echo("   📅 Configuring automated update schedules...")
        client.setup_automated_updates()

        typer.echo("✅ ERA5 automation setup complete!")
        typer.echo("")
        typer.echo("📋 Scheduled Updates:")
        typer.echo("   • Daily: 06:00 UTC (recent 7-day data)")
        typer.echo("   • Monthly: 1st day of month (previous month complete data)")
        typer.echo("")
        typer.echo("🚀 To start the scheduler:")
        typer.echo(
            '   python -c "from malaria_predictor.services.era5_client import ERA5Client; ERA5Client().run_scheduler()"'
        )

    except Exception as e:
        typer.echo(f"❌ Setup error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def era5_validate(
    file_path: str = typer.Argument(help="Path to ERA5 NetCDF file to validate"),
) -> None:
    """Validate downloaded ERA5 data file."""
    from pathlib import Path

    from .services.era5_client import ERA5Client

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            typer.echo(f"❌ Error: File not found: {file_path}", err=True)
            raise typer.Exit(1)

        client = ERA5Client()
        typer.echo(f"🔍 Validating ERA5 file: {file_path_obj.name}")

        result = client.validate_downloaded_file(file_path_obj)

        # Display results
        typer.echo(f"   📁 File exists: {'✅' if result['file_exists'] else '❌'}")
        typer.echo(
            f"   📏 File size: {result['file_size_mb']:.2f} MB {'✅' if result['file_size_valid'] else '❌'}"
        )
        typer.echo(
            f"   📊 Data accessible: {'✅' if result['data_accessible'] else '❌'}"
        )
        typer.echo(
            f"   🔬 Variables present: {'✅' if result['variables_present'] else '❌'}"
        )

        if result["variables_found"]:
            typer.echo(f"      Variables: {', '.join(result['variables_found'])}")

        typer.echo(
            f"   📅 Temporal coverage: {'✅' if result['temporal_coverage_valid'] else '❌'}"
        )
        if result.get("temporal_range"):
            temp_range = result["temporal_range"]
            typer.echo(f"      Time steps: {temp_range.get('count', 0)}")
            typer.echo(
                f"      Range: {temp_range.get('start', 'N/A')} to {temp_range.get('end', 'N/A')}"
            )

        typer.echo(
            f"   🌍 Spatial bounds: {'✅' if result['spatial_bounds_valid'] else '❌'}"
        )

        overall = "✅ VALID" if result["success"] else "❌ INVALID"
        typer.echo(f"   🎯 Overall: {overall}")

        if result.get("error_message"):
            typer.echo(f"   ⚠️  Error: {result['error_message']}")

    except Exception as e:
        typer.echo(f"❌ Validation error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def chirps_validate(
    file_path: str = typer.Argument(help="Path to CHIRPS GeoTIFF file to validate"),
) -> None:
    """Validate downloaded CHIRPS rainfall data file."""
    from pathlib import Path

    from .services.chirps_client import CHIRPSClient

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            typer.echo(f"❌ Error: File not found: {file_path}", err=True)
            raise typer.Exit(1)

        client = CHIRPSClient()
        typer.echo(f"🔍 Validating CHIRPS file: {file_path_obj.name}")

        result = client.validate_rainfall_file(file_path_obj)

        # Display results
        typer.echo(f"   📁 File exists: {'✅' if result['file_exists'] else '❌'}")
        typer.echo(
            f"   📏 File size: {result['file_size_mb']:.2f} MB {'✅' if result['file_size_valid'] else '❌'}"
        )
        typer.echo(
            f"   📊 Data accessible: {'✅' if result['data_accessible'] else '❌'}"
        )
        typer.echo(
            f"   🌧️ Has valid rainfall data: {'✅' if result['has_valid_data'] else '❌'}"
        )

        if result.get("data_range"):
            data_range = result["data_range"]
            typer.echo(
                f"      Rainfall range: {data_range.get('min', 0):.2f} - {data_range.get('max', 0):.2f} mm"
            )
            typer.echo(f"      Mean rainfall: {data_range.get('mean', 0):.2f} mm")

        typer.echo(
            f"   🌍 Spatial resolution: {'✅' if result['spatial_resolution_valid'] else '❌'} (0.05° expected)"
        )

        overall = "✅ VALID" if result["success"] else "❌ INVALID"
        typer.echo(f"   🎯 Overall: {overall}")

        if result.get("error_message"):
            typer.echo(f"   ⚠️  Error: {result['error_message']}")

        # Clean up
        client.close()

    except Exception as e:
        typer.echo(f"❌ Validation error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def chirps_aggregate(
    month: str = typer.Argument(help="Month to aggregate (YYYY-MM format)"),
    output_dir: str = typer.Option(
        "./data/chirps", help="Output directory for aggregated data"
    ),
) -> None:
    """Aggregate daily CHIRPS data to monthly totals."""
    from datetime import datetime
    from pathlib import Path

    from .services.chirps_client import CHIRPSClient

    try:
        # Parse month
        try:
            target_date = datetime.strptime(month, "%Y-%m")
        except ValueError as e:
            typer.echo(
                "❌ Error: Invalid month format. Use YYYY-MM (e.g., 2023-06)", err=True
            )
            raise typer.Exit(1) from e

        client = CHIRPSClient()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        typer.echo(f"📆 Aggregating CHIRPS data for {month}")

        # Find daily files for the month
        daily_files = []
        for day in range(1, 32):  # Check all possible days
            try:
                date_str = f"{target_date.year}.{target_date.month:02d}.{day:02d}"
                file_pattern = f"chirps-v2.0.{date_str}.tif"
                matching_files = list(client.download_directory.glob(file_pattern))
                daily_files.extend(matching_files)
            except Exception:
                continue

        if not daily_files:
            typer.echo(f"❌ No daily files found for {month}", err=True)
            typer.echo(f"   Looked in: {client.download_directory}")
            raise typer.Exit(1)

        typer.echo(f"   📁 Found {len(daily_files)} daily files")

        # Create output filename
        output_file = (
            output_path
            / f"chirps-v2.0.{target_date.year}.{target_date.month:02d}.monthly.tif"
        )

        # Aggregate
        typer.echo("   🔄 Aggregating daily rainfall to monthly total...")
        success = client.aggregate_to_monthly(daily_files, output_file)

        if success:
            typer.echo(f"   ✅ Monthly aggregate created: {output_file.name}")

            # Validate the output
            validation = client.validate_rainfall_file(output_file)
            if validation["success"]:
                typer.echo("   ✅ Output file validation passed")
                if validation.get("data_range"):
                    typer.echo(
                        f"      Total rainfall: {validation['data_range'].get('max', 0):.2f} mm"
                    )
            else:
                typer.echo("   ⚠️  Output validation failed")
        else:
            typer.echo("❌ Aggregation failed", err=True)
            raise typer.Exit(1)

        # Clean up
        client.close()

    except Exception as e:
        typer.echo(f"❌ Aggregation error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def map_validate(
    file_path: str = typer.Argument(help="Path to MAP raster file to validate"),
) -> None:
    """Validate downloaded MAP data file."""
    from pathlib import Path

    from .services.map_client import MAPClient

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            typer.echo(f"❌ Error: File not found: {file_path}", err=True)
            raise typer.Exit(1)

        client = MAPClient()
        typer.echo(f"🔍 Validating MAP file: {file_path_obj.name}")

        result = client.validate_raster_file(file_path_obj)

        # Display results
        typer.echo(f"   📁 File exists: {'✅' if result['file_exists'] else '❌'}")
        typer.echo(
            f"   📏 File size: {result['file_size_mb']:.2f} MB {'✅' if result['file_size_valid'] else '❌'}"
        )
        typer.echo(
            f"   📊 Data accessible: {'✅' if result['data_accessible'] else '❌'}"
        )
        typer.echo(
            f"   🗺️  Has valid data: {'✅' if result['has_valid_data'] else '❌'}"
        )

        if result.get("data_range"):
            data_range = result["data_range"]
            typer.echo(
                f"      Range: {data_range.get('min', 0):.3f} - {data_range.get('max', 0):.3f}"
            )
            typer.echo(
                f"      Mean: {data_range.get('mean', 0):.3f} ± {data_range.get('std', 0):.3f}"
            )

        typer.echo(
            f"   🌍 Spatial resolution: {'✅' if result['spatial_resolution_valid'] else '❌'}"
        )
        if result.get("resolution"):
            res = result["resolution"]
            typer.echo(f"      Resolution: {res[0]}° x {res[1]}°")

        typer.echo(
            f"   🧭 CRS valid: {'✅' if result['crs_valid'] else '❌'} (WGS84 expected)"
        )
        if result.get("crs"):
            typer.echo(f"      CRS: {result['crs']}")

        overall = "✅ VALID" if result["success"] else "❌ INVALID"
        typer.echo(f"   🎯 Overall: {overall}")

        if result.get("error_message"):
            typer.echo(f"   ⚠️  Error: {result['error_message']}")

        # Clean up
        client.close()

    except Exception as e:
        typer.echo(f"❌ Validation error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def map_download(
    data_type: str = typer.Argument(help="Type of MAP data (pr, vector, itn, irs)"),
    year: int = typer.Option(2021, help="Year of data to download"),
    species: str = typer.Option("Pf", help="Parasite species (Pf or Pv) for PR data"),
    resolution: str = typer.Option(
        "5km", help="Resolution (1km or 5km) for raster data"
    ),
    output_dir: str = typer.Option(
        "./data/map", help="Output directory for downloaded data"
    ),
) -> None:
    """Download specific MAP data."""
    from pathlib import Path

    from .services.map_client import MAPClient

    try:
        # Validate data type
        valid_types = ["pr", "vector", "itn", "irs", "act"]
        if data_type.lower() not in valid_types:
            typer.echo(f"❌ Error: Invalid data type '{data_type}'", err=True)
            typer.echo(f"Valid types: {', '.join(valid_types)}")
            raise typer.Exit(1)

        client = MAPClient()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        typer.echo(f"📥 Downloading MAP {data_type.upper()} data")

        if data_type == "pr":
            # Download parasite rate surface
            typer.echo(f"   🦟 Species: {species}")
            typer.echo(f"   📅 Year: {year}")
            typer.echo(f"   🔍 Resolution: {resolution}")

            result = client.download_parasite_rate_surface(
                year=year,
                species=species,
                resolution=resolution,  # type: ignore
            )

        elif data_type == "vector":
            # Download vector occurrence data
            typer.echo("   🦟 Anopheles gambiae complex")
            typer.echo(f"   📅 Years: {year - 5} to {year}")

            result = client.download_vector_occurrence_data(
                species_complex="gambiae", start_year=year - 5, end_year=year
            )

        elif data_type in ["itn", "irs", "act"]:
            # Download intervention coverage
            intervention_map = {"itn": "ITN", "irs": "IRS", "act": "ACT"}
            intervention_type = intervention_map[data_type]

            typer.echo(f"   💉 Intervention: {intervention_type}")
            typer.echo(f"   📅 Year: {year}")

            result = client.download_intervention_coverage(
                intervention_type=intervention_type,  # type: ignore
                year=year,
            )

        # Display results
        if result.success:
            typer.echo("   ✅ Download successful")
            typer.echo(f"   📁 Files: {len(result.file_paths)}")
            typer.echo(
                f"   💾 Total size: {result.total_size_bytes / 1024 / 1024:.2f} MB"
            )
            typer.echo(
                f"   ⏱️  Duration: {result.download_duration_seconds:.1f} seconds"
            )

            # List downloaded files
            if result.file_paths:
                typer.echo("   📄 Downloaded files:")
                for file_path in result.file_paths:
                    typer.echo(f"      • {file_path.name}")
        else:
            typer.echo(f"❌ Download failed: {result.error_message}", err=True)
            raise typer.Exit(1)

        # Clean up
        client.close()

    except Exception as e:
        typer.echo(f"❌ Download error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def modis_setup() -> None:
    """Set up NASA EarthData authentication for MODIS data access."""
    try:
        typer.echo("⚙️  Setting up MODIS/NASA EarthData authentication")

        # Check current environment variables
        import os

        username = os.getenv("NASA_EARTHDATA_USERNAME")
        password = os.getenv("NASA_EARTHDATA_PASSWORD")

        if username and password:
            typer.echo("   ✅ Environment variables already set")
            typer.echo(f"   Username: {username}")

            # Test authentication
            from .services.modis_client import MODISClient

            client = MODISClient()

            typer.echo("   🔑 Testing authentication...")
            if client.authenticate(username, password):
                typer.echo("   ✅ Authentication successful!")
            else:
                typer.echo("   ❌ Authentication failed - please check credentials")

            client.close()
        else:
            typer.echo("   ⚠️  NASA EarthData credentials not found")

        typer.echo("")
        typer.echo("📖 Setup Instructions:")
        typer.echo("   1. Register at: https://urs.earthdata.nasa.gov/")
        typer.echo("   2. Accept MODIS data use agreements:")
        typer.echo("      - Navigate to 'My Applications' > 'Approved Applications'")
        typer.echo("      - Approve 'LP DAAC Data Pool'")
        typer.echo("   3. Set environment variables:")
        typer.echo("      export NASA_EARTHDATA_USERNAME=your_username")
        typer.echo("      export NASA_EARTHDATA_PASSWORD=your_password")
        typer.echo("   4. Or add to .env file:")
        typer.echo("      NASA_EARTHDATA_USERNAME=your_username")
        typer.echo("      NASA_EARTHDATA_PASSWORD=your_password")
        typer.echo("")
        typer.echo("🛰️  MODIS Products Available:")
        typer.echo("   • MOD13Q1 (Terra, 250m, 16-day NDVI/EVI)")
        typer.echo("   • MYD13Q1 (Aqua, 250m, 16-day NDVI/EVI)")
        typer.echo("   • Collection 6.1 (most recent)")

    except Exception as e:
        typer.echo(f"❌ Setup error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def modis_download(
    product: str = typer.Option("MOD13Q1", help="MODIS product (MOD13Q1/MYD13Q1)"),
    start_date: str = typer.Option(None, help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, help="End date (YYYY-MM-DD)"),
    area_bounds: str = typer.Option(
        None, help="Geographic bounds as 'west,south,east,north'"
    ),
    tiles: str = typer.Option(
        None, help="Specific MODIS tiles (e.g., 'h21v08,h22v08')"
    ),
    output_dir: str = typer.Option(
        "./data/modis", help="Output directory for downloaded data"
    ),
) -> None:
    """Download specific MODIS vegetation indices data."""
    from datetime import date, datetime, timedelta

    from .services.modis_client import MODISClient

    try:
        # Validate product
        if product not in ["MOD13Q1", "MYD13Q1"]:
            typer.echo(f"❌ Error: Invalid product '{product}'", err=True)
            typer.echo("Valid products: MOD13Q1 (Terra), MYD13Q1 (Aqua)")
            raise typer.Exit(1)

        # Parse dates
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError as e:
                typer.echo("❌ Error: Invalid date format. Use YYYY-MM-DD", err=True)
                raise typer.Exit(1) from e
        else:
            # Default to last month
            end = date.today() - timedelta(days=7)
            start = end - timedelta(days=31)

        # Parse area bounds
        bounds = None
        if area_bounds:
            try:
                bounds = tuple(map(float, area_bounds.split(",")))
                if len(bounds) != 4:
                    raise ValueError("Must provide exactly 4 values")
            except ValueError as e:
                typer.echo(f"❌ Invalid area bounds format: {e}", err=True)
                typer.echo(
                    "   Expected format: 'west,south,east,north' (e.g., '30,-5,45,15')"
                )
                raise typer.Exit(1) from e
        else:
            bounds = (-20.0, -35.0, 55.0, 40.0)  # Default Africa bounds

        client = None
        try:
            client = MODISClient()

            # Authenticate
            import os

            username = os.getenv("NASA_EARTHDATA_USERNAME")
            password = os.getenv("NASA_EARTHDATA_PASSWORD")

            if not username or not password:
                typer.echo("❌ Error: NASA EarthData credentials not found", err=True)
                typer.echo(
                    "   Run 'malaria-predictor modis-setup' for setup instructions"
                )
                raise typer.Exit(1)

            typer.echo(f"🛰️  Downloading MODIS {product} data")
            typer.echo(f"   📅 Period: {start} to {end}")
            typer.echo(f"   🌍 Area: {bounds}")

            if not client.authenticate(username, password):
                typer.echo("❌ Authentication failed", err=True)
                raise typer.Exit(1)

            # Download data
            result = client.download_vegetation_indices(
                start_date=start, end_date=end, product=product, area_bounds=bounds
            )

            if result.success:
                typer.echo("   ✅ Download successful")
                typer.echo(f"   📁 Files: {result.files_processed}")
                typer.echo(
                    f"   💾 Total size: {result.total_size_bytes / 1024 / 1024:.2f} MB"
                )
                typer.echo(f"   🗺️  Tiles: {', '.join(result.tiles_processed)}")
                typer.echo(
                    f"   ⏱️  Duration: {result.download_duration_seconds:.1f} seconds"
                )

                # List downloaded files
                if result.file_paths:
                    typer.echo("   📄 Downloaded files:")
                    for file_path in result.file_paths[:10]:  # Show first 10
                        typer.echo(f"      • {file_path.name}")
                    if len(result.file_paths) > 10:
                        typer.echo(
                            f"      ... and {len(result.file_paths) - 10} more files"
                        )
            else:
                typer.echo(f"❌ Download failed: {result.error_message}", err=True)
                raise typer.Exit(1)

        finally:
            if client:
                client.close()

    except Exception as e:
        typer.echo(f"❌ Download error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def modis_validate(
    file_path: str = typer.Argument(help="Path to MODIS HDF file to validate"),
) -> None:
    """Validate downloaded MODIS data file."""
    from pathlib import Path

    from .services.modis_client import MODISClient

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            typer.echo(f"❌ Error: File not found: {file_path}", err=True)
            raise typer.Exit(1)

        client = MODISClient()
        typer.echo(f"🔍 Validating MODIS file: {file_path_obj.name}")

        result = client.validate_modis_file(file_path_obj)

        # Display results
        typer.echo(f"   📁 File exists: {'✅' if result['file_exists'] else '❌'}")
        typer.echo(
            f"   📏 File size: {result['file_size_mb']:.2f} MB {'✅' if result['file_size_valid'] else '❌'}"
        )
        typer.echo(f"   📊 HDF readable: {'✅' if result['hdf_readable'] else '❌'}")
        typer.echo(f"   🌿 Has VI data: {'✅' if result['has_vi_data'] else '❌'}")
        typer.echo(
            f"   🔍 Has quality data: {'✅' if result['has_quality_data'] else '❌'}"
        )
        typer.echo(f"   📦 Subdatasets: {result['subdatasets_count']}")

        if result.get("spatial_info"):
            spatial = result["spatial_info"]
            if "height" in spatial and "width" in spatial:
                typer.echo(
                    f"   🗺️  Spatial dimensions: {spatial['width']} x {spatial['height']} {'✅' if result['spatial_dimensions_valid'] else '❌'}"
                )
                typer.echo(f"   🧭 CRS: {spatial.get('crs', 'Unknown')}")

        if result["subdatasets"]:
            typer.echo("   📋 Available subdatasets:")
            for i, subdataset in enumerate(result["subdatasets"][:5]):  # Show first 5
                dataset_name = (
                    subdataset.split(":")[-1] if ":" in subdataset else subdataset
                )
                typer.echo(f"      {i + 1}. {dataset_name}")
            if len(result["subdatasets"]) > 5:
                typer.echo(f"      ... and {len(result['subdatasets']) - 5} more")

        overall = "✅ VALID" if result["success"] else "❌ INVALID"
        typer.echo(f"   🎯 Overall: {overall}")

        if result.get("error_message"):
            typer.echo(f"   ⚠️  Error: {result['error_message']}")

        client.close()

    except Exception as e:
        typer.echo(f"❌ Validation error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def modis_process(
    file_path: str = typer.Argument(help="Path to MODIS HDF file to process"),
    vegetation_indices: str = typer.Option(
        "NDVI,EVI", help="Comma-separated VI list (NDVI,EVI)"
    ),
    quality_filter: bool = typer.Option(True, help="Apply VI Quality flags filtering"),
    output_format: str = typer.Option(
        "geotiff", help="Output format (geotiff, numpy, both)"
    ),
    output_dir: str = typer.Option(
        "./data/modis/processed", help="Output directory for processed data"
    ),
) -> None:
    """Process MODIS HDF file and extract vegetation indices."""
    from pathlib import Path

    from .services.modis_client import MODISClient

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            typer.echo(f"❌ Error: File not found: {file_path}", err=True)
            raise typer.Exit(1)

        # Parse vegetation indices
        vi_list = [vi.strip().upper() for vi in vegetation_indices.split(",")]
        valid_vis = ["NDVI", "EVI", "ARVI", "SAVI"]
        invalid_vis = [vi for vi in vi_list if vi not in valid_vis]

        if invalid_vis:
            typer.echo(
                f"❌ Error: Invalid vegetation indices: {', '.join(invalid_vis)}",
                err=True,
            )
            typer.echo(f"Valid indices: {', '.join(valid_vis)}")
            raise typer.Exit(1)

        client = MODISClient()
        typer.echo(f"🔄 Processing MODIS file: {file_path_obj.name}")
        typer.echo(f"   🌿 Vegetation indices: {', '.join(vi_list)}")
        typer.echo(
            f"   🔍 Quality filtering: {'Enabled' if quality_filter else 'Disabled'}"
        )
        typer.echo(f"   📁 Output format: {output_format}")

        results = client.process_vegetation_indices(
            file_path_obj,
            vegetation_indices=vi_list,
            apply_quality_filter=quality_filter,
            output_format=output_format,
        )

        success_count = 0
        for result in results:
            if result.success:
                success_count += 1
                stats = result.statistics
                typer.echo(f"   ✅ {result.vegetation_index}:")
                typer.echo(
                    f"      Shape: {result.data_shape[1]} x {result.data_shape[0]} pixels"
                )
                typer.echo(f"      Valid pixels: {result.valid_pixel_count:,}")
                typer.echo(
                    f"      Range: {stats.get('min', 0):.3f} to {stats.get('max', 0):.3f}"
                )
                typer.echo(
                    f"      Mean: {stats.get('mean', 0):.3f} ± {stats.get('std', 0):.3f}"
                )

                if result.quality_flags:
                    qf = result.quality_flags
                    if "good_quality" in qf:
                        total_pixels = qf.get("total_pixels", 1)
                        good_pct = qf["good_quality"] / total_pixels * 100
                        typer.echo(
                            f"      Quality: {qf['good_quality']:,} good pixels ({good_pct:.1f}%)"
                        )

                if result.temporal_info:
                    temp_info = result.temporal_info
                    if "acquisition_date" in temp_info:
                        typer.echo(f"      Date: {temp_info['acquisition_date']}")

                typer.echo(f"      Output: {result.file_path}")
            else:
                typer.echo(f"   ❌ {result.vegetation_index}: {result.error_message}")

        typer.echo(
            f"   📊 Successfully processed {success_count}/{len(results)} vegetation indices"
        )

        client.close()

    except Exception as e:
        typer.echo(f"❌ Processing error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def modis_aggregate(
    input_dir: str = typer.Argument(help="Directory containing processed MODIS files"),
    vegetation_index: str = typer.Option("NDVI", help="Vegetation index to aggregate"),
    method: str = typer.Option(
        "monthly", help="Aggregation method (monthly, seasonal, annual)"
    ),
    output_file: str = typer.Option(None, help="Output file path (optional)"),
) -> None:
    """Aggregate processed MODIS vegetation indices temporally."""
    from pathlib import Path

    from .services.modis_client import MODISClient

    try:
        input_path = Path(input_dir)
        if not input_path.exists():
            typer.echo(f"❌ Error: Directory not found: {input_dir}", err=True)
            raise typer.Exit(1)

        # Validate aggregation method
        valid_methods = ["monthly", "seasonal", "annual"]
        if method not in valid_methods:
            typer.echo(f"❌ Error: Invalid aggregation method '{method}'", err=True)
            typer.echo(f"Valid methods: {', '.join(valid_methods)}")
            raise typer.Exit(1)

        # Find matching files
        vi_pattern = f"*{vegetation_index}*processed.tif"
        matching_files = list(input_path.glob(vi_pattern))

        if not matching_files:
            typer.echo(
                f"❌ Error: No {vegetation_index} files found in {input_dir}", err=True
            )
            typer.echo(f"   Looking for pattern: {vi_pattern}")
            raise typer.Exit(1)

        client = MODISClient()
        typer.echo(f"📊 Aggregating MODIS {vegetation_index} data")
        typer.echo(f"   📁 Input directory: {input_dir}")
        typer.echo(f"   🔢 Files found: {len(matching_files)}")
        typer.echo(f"   📅 Method: {method}")

        output_path = Path(output_file) if output_file else None
        result_path = client.aggregate_temporal_data(
            file_paths=matching_files,
            aggregation_method=method,
            vegetation_index=vegetation_index,
            output_path=output_path,
        )

        if result_path:
            typer.echo("   ✅ Aggregation successful")
            typer.echo(f"   📁 Output file: {result_path}")

            # Get file size
            file_size_mb = result_path.stat().st_size / 1024 / 1024
            typer.echo(f"   💾 File size: {file_size_mb:.2f} MB")
        else:
            typer.echo("❌ Aggregation failed", err=True)
            raise typer.Exit(1)

        client.close()

    except Exception as e:
        typer.echo(f"❌ Aggregation error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def map_process(
    file_path: str = typer.Argument(help="Path to MAP raster file to process"),
    output_format: str = typer.Option("csv", help="Output format (csv or stats)"),
    output_file: str = typer.Option(None, help="Output file path (optional)"),
) -> None:
    """Process MAP raster data and extract statistics or convert to CSV."""
    from pathlib import Path

    import numpy as np

    from .services.map_client import MAPClient

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            typer.echo(f"❌ Error: File not found: {file_path}", err=True)
            raise typer.Exit(1)

        client = MAPClient()
        typer.echo(f"🔄 Processing MAP file: {file_path_obj.name}")

        if output_format == "stats":
            # Process and display statistics
            data = client.process_parasite_rate_data(
                file_path_obj, output_format="array"
            )

            if data is not None:
                valid_data = data[~np.isnan(data)]
                typer.echo("📊 Parasite Rate Statistics:")
                typer.echo(f"   • Min: {valid_data.min():.2f}%")
                typer.echo(f"   • Max: {valid_data.max():.2f}%")
                typer.echo(f"   • Mean: {valid_data.mean():.2f}%")
                typer.echo(f"   • Std: {valid_data.std():.2f}%")
                typer.echo(f"   • Pixels: {len(valid_data):,}")
            else:
                typer.echo("❌ Failed to process data", err=True)

        elif output_format == "csv":
            # Convert to CSV
            import pandas as pd

            df = client.process_parasite_rate_data(
                file_path_obj, output_format="dataframe"
            )

            if df is not None and isinstance(df, pd.DataFrame):
                if output_file:
                    df.to_csv(output_file, index=False)
                    typer.echo(f"   ✅ Saved to: {output_file}")
                    typer.echo(f"   📊 Records: {len(df):,}")
                else:
                    # Display sample
                    typer.echo("📊 Sample data (first 5 rows):")
                    typer.echo(df.head().to_string())
                    typer.echo(f"   Total records: {len(df):,}")
            else:
                typer.echo("❌ Failed to process data", err=True)

        else:
            typer.echo(f"❌ Invalid output format: {output_format}", err=True)
            typer.echo("Valid formats: stats, csv")

        # Clean up
        client.close()

    except ImportError:
        typer.echo("❌ Error: Required dependencies not installed", err=True)
        typer.echo("   Install with: pip install pandas")
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"❌ Processing error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def db_init(
    drop_existing: bool = typer.Option(
        False, help="Drop existing tables before initialization"
    ),
    run_migrations: bool = typer.Option(True, help="Run database migrations"),
) -> None:
    """Initialize the database schema and run migrations."""
    import asyncio

    from .database.session import init_database

    async def run_init():
        try:
            typer.echo("🗄️  Initializing database...")
            if drop_existing:
                typer.echo("   ⚠️  Dropping existing tables")

            await init_database(drop_existing=drop_existing)
            typer.echo("✅ Database initialization completed")

            if run_migrations:
                typer.echo("🔄 Running database migrations...")
                # Run Alembic migrations
                import subprocess

                result = subprocess.run(
                    ["alembic", "upgrade", "head"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    typer.echo("✅ Migrations completed successfully")
                else:
                    typer.echo(f"❌ Migration failed: {result.stderr}", err=True)
                    return False

            return True
        except Exception as e:
            typer.echo(f"❌ Database initialization failed: {e}", err=True)
            return False

    success = asyncio.run(run_init())
    if not success:
        raise typer.Exit(1)


@app.command()
def db_health(
    detailed: bool = typer.Option(False, help="Show detailed health metrics"),
) -> None:
    """Check database health and connectivity."""
    import asyncio
    import json

    from .database.session import check_database_health

    async def run_health_check():
        try:
            typer.echo("🏥 Checking database health...")
            health_status = await check_database_health()

            # Display basic status
            connected = "✅" if health_status["connected"] else "❌"
            tables_exist = "✅" if health_status["tables_exist"] else "❌"
            timescaledb = "✅" if health_status["timescaledb_enabled"] else "❌"
            postgis = "✅" if health_status["postgis_enabled"] else "❌"

            typer.echo(f"   Database Connected: {connected}")
            typer.echo(f"   Tables Exist: {tables_exist}")
            typer.echo(f"   TimescaleDB: {timescaledb}")
            typer.echo(f"   PostGIS: {postgis}")

            if health_status["response_time_ms"]:
                typer.echo(f"   Response Time: {health_status['response_time_ms']}ms")

            if detailed:
                typer.echo("\n📊 Detailed Metrics:")

                # Connection pool status
                pool_status = health_status.get("connection_pool", {})
                if pool_status:
                    typer.echo("   Connection Pool:")
                    for key, value in pool_status.items():
                        if value is not None:
                            typer.echo(f"     {key}: {value}")

                # TimescaleDB details
                if "timescaledb_version" in health_status:
                    typer.echo(
                        f"   TimescaleDB Version: {health_status['timescaledb_version']}"
                    )

                if "postgis_version" in health_status:
                    typer.echo(
                        f"   PostGIS Version: {health_status['postgis_version']}"
                    )

                if "hypertables_count" in health_status:
                    typer.echo(f"   Hypertables: {health_status['hypertables_count']}")

                # JSON output for detailed analysis
                typer.echo("\n📋 Raw Health Data:")
                typer.echo(json.dumps(health_status, indent=2, default=str))

            if health_status["error"]:
                typer.echo(f"❌ Error: {health_status['error']}", err=True)
                return False

            return True
        except Exception as e:
            typer.echo(f"❌ Health check failed: {e}", err=True)
            return False

    success = asyncio.run(run_health_check())
    if not success:
        raise typer.Exit(1)


@app.command()
def db_backup(
    backup_type: str = typer.Option("full", help="Backup type (full, schema, data)"),
    output_dir: str = typer.Option(
        "/var/backups/malaria-prediction", help="Backup directory"
    ),
    compress: bool = typer.Option(True, help="Compress backup files"),
) -> None:
    """Create database backup."""
    import subprocess
    import sys
    from pathlib import Path

    from .config import settings

    try:
        # Use the backup script
        script_path = (
            Path(__file__).parent.parent.parent.parent
            / "scripts"
            / "database_backup.py"
        )

        cmd = [
            sys.executable,
            str(script_path),
            "--database-url",
            settings.database_url,
            "--backup-dir",
            output_dir,
            "backup",
            "--type",
            backup_type,
        ]

        if not compress:
            cmd.append("--no-compress")

        typer.echo(f"🗄️  Creating {backup_type} database backup...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            typer.echo("✅ Backup completed successfully")
            typer.echo(result.stdout)
        else:
            typer.echo(f"❌ Backup failed: {result.stderr}", err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Backup error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def db_restore(
    backup_file: str = typer.Argument(..., help="Path to backup file"),
    target_db: str = typer.Option(None, help="Target database name"),
    clean_first: bool = typer.Option(False, help="Clean existing database first"),
) -> None:
    """Restore database from backup."""
    import subprocess
    import sys
    from pathlib import Path

    from .config import settings

    try:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            typer.echo(f"❌ Backup file not found: {backup_file}", err=True)
            raise typer.Exit(1)

        # Use the backup script
        script_path = (
            Path(__file__).parent.parent.parent.parent
            / "scripts"
            / "database_backup.py"
        )

        cmd = [
            sys.executable,
            str(script_path),
            "--database-url",
            settings.database_url,
            "restore",
            str(backup_path),
        ]

        if target_db:
            cmd.extend(["--target-db", target_db])

        if clean_first:
            cmd.append("--clean")

        typer.echo(f"🔄 Restoring database from {backup_file}...")
        if clean_first:
            typer.echo("   ⚠️  Cleaning existing database first")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            typer.echo("✅ Restore completed successfully")
            typer.echo(result.stdout)
        else:
            typer.echo(f"❌ Restore failed: {result.stderr}", err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Restore error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def db_maintenance(
    operation: str = typer.Argument(
        ...,
        help="Maintenance operation (metrics, retention, optimize, compress, report)",
    ),
    older_than_days: int = typer.Option(
        30, help="For compress: compress chunks older than N days"
    ),
) -> None:
    """Run database maintenance operations."""
    import subprocess
    import sys
    from pathlib import Path

    from .config import settings

    valid_operations = [
        "metrics",
        "retention",
        "optimize",
        "compress",
        "report",
        "scheduled",
    ]
    if operation not in valid_operations:
        typer.echo(f"❌ Invalid operation: {operation}", err=True)
        typer.echo(f"Valid operations: {', '.join(valid_operations)}")
        raise typer.Exit(1)

    try:
        # Use the maintenance script
        script_path = (
            Path(__file__).parent.parent.parent.parent
            / "scripts"
            / "database_maintenance.py"
        )

        cmd = [
            sys.executable,
            str(script_path),
            "--database-url",
            settings.database_url,
            operation,
        ]

        if operation == "compress":
            cmd.extend(["--older-than-days", str(older_than_days)])

        typer.echo(f"🔧 Running database maintenance: {operation}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            typer.echo("✅ Maintenance completed successfully")
            typer.echo(result.stdout)
        else:
            typer.echo(f"❌ Maintenance failed: {result.stderr}", err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Maintenance error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def db_migrate(
    direction: str = typer.Option("up", help="Migration direction (up, down)"),
    revision: str = typer.Option(
        "head", help="Target revision (head, base, or specific revision)"
    ),
) -> None:
    """Run database migrations."""
    import subprocess

    try:
        if direction == "up":
            cmd = ["alembic", "upgrade", revision]
            typer.echo(f"⬆️  Upgrading database to revision: {revision}")
        elif direction == "down":
            cmd = ["alembic", "downgrade", revision]
            typer.echo(f"⬇️  Downgrading database to revision: {revision}")
        else:
            typer.echo("❌ Invalid direction. Use 'up' or 'down'", err=True)
            raise typer.Exit(1)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            typer.echo("✅ Migration completed successfully")
            if result.stdout:
                typer.echo(result.stdout)
        else:
            typer.echo(f"❌ Migration failed: {result.stderr}", err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Migration error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def db_revision(
    message: str = typer.Argument(..., help="Migration message"),
    autogenerate: bool = typer.Option(
        True, help="Auto-generate migration from model changes"
    ),
) -> None:
    """Create new database migration revision."""
    import subprocess

    try:
        cmd = ["alembic", "revision"]

        if autogenerate:
            cmd.append("--autogenerate")

        cmd.extend(["-m", message])

        typer.echo(f"📝 Creating new migration: {message}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            typer.echo("✅ Migration revision created successfully")
            if result.stdout:
                typer.echo(result.stdout)
        else:
            typer.echo(f"❌ Migration creation failed: {result.stderr}", err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Migration creation error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def train(
    model_type: str = typer.Option(
        "lstm", help="Model type to train (lstm/transformer)"
    ),
    epochs: int = typer.Option(10, help="Number of training epochs"),
    data_path: str = typer.Option("./data", help="Path to training data"),
) -> None:
    """Train AI models."""
    available_models = ["lstm", "transformer", "ensemble"]

    if model_type not in available_models:
        typer.echo(f"❌ Error: Unknown model type '{model_type}'", err=True)
        typer.echo(f"Available models: {', '.join(available_models)}")
        raise typer.Exit(1)

    if epochs < 1 or epochs > 1000:
        typer.echo("❌ Error: Epochs must be between 1 and 1000", err=True)
        raise typer.Exit(1)

    typer.echo(f"🤖 Training {model_type.upper()} model...")
    typer.echo(f"   Epochs: {epochs}")
    typer.echo(f"   Data path: {data_path}")

    # Placeholder implementation - will be replaced with actual ML training
    import time

    model_info = {
        "lstm": "Long Short-Term Memory network for time series prediction",
        "transformer": "Transformer model for complex pattern recognition",
        "ensemble": "Combined LSTM + Transformer ensemble model",
    }

    typer.echo(f"📈 Model: {model_info[model_type]}")
    typer.echo("🔄 Simulating training progress...")

    for epoch in range(1, min(epochs + 1, 4)):  # Simulate first few epochs
        time.sleep(0.1)  # Brief pause for realism
        loss = 1.0 - (epoch * 0.2)  # Decreasing loss
        typer.echo(f"   Epoch {epoch}/{epochs}: loss = {loss:.4f}")

    if epochs > 3:
        typer.echo(f"   ... (continuing for {epochs - 3} more epochs)")

    typer.echo("✅ Model training simulation complete")
    typer.echo(
        "⚠️  Note: This is placeholder functionality. Real ML training will be implemented in Phase 3."
    )


def _ingest_modis_data(dry_run: bool) -> None:
    """Handle MODIS-specific data ingestion."""
    from datetime import date, timedelta

    from .services.modis_client import MODISClient

    client = None
    try:
        typer.echo("🛰️  MODIS Vegetation Indices Data Ingestion")

        if dry_run:
            typer.echo("   📋 Dry run mode - would download:")
            typer.echo("   • MOD13Q1/MYD13Q1 vegetation indices (250m resolution)")
            typer.echo("   • NDVI and EVI with quality filtering")
            typer.echo("   • 16-day composite products")
            typer.echo("   • Geographic coverage: Africa region")
            typer.echo("   • Temporal coverage: Last 32 days (2 periods)")
            typer.echo("   • File format: HDF4 with GeoTIFF processing")
            typer.echo("   • Authentication: NASA EarthData credentials required")
            return

        client = MODISClient()

        # Check if authentication credentials are available
        import os

        username = os.getenv("NASA_EARTHDATA_USERNAME")
        password = os.getenv("NASA_EARTHDATA_PASSWORD")

        if not username or not password:
            typer.echo("❌ Error: NASA EarthData credentials not found", err=True)
            typer.echo("")
            typer.echo("📖 Setup Instructions:")
            typer.echo("   1. Register at: https://urs.earthdata.nasa.gov/")
            typer.echo("   2. Set environment variables:")
            typer.echo("      export NASA_EARTHDATA_USERNAME=your_username")
            typer.echo("      export NASA_EARTHDATA_PASSWORD=your_password")
            typer.echo("   3. Run this command again")
            raise typer.Exit(1)

        # Authenticate with NASA EarthData
        typer.echo("   🔑 Authenticating with NASA EarthData...")
        if not client.authenticate(username, password):
            typer.echo("❌ Error: NASA EarthData authentication failed", err=True)
            typer.echo("   Please check your credentials and try again")
            raise typer.Exit(1)

        typer.echo("   ✅ NASA EarthData authentication successful")

        # Download recent MODIS data (last 32 days to get 2 16-day periods)
        end_date = date.today() - timedelta(days=7)  # MODIS has processing delay
        start_date = end_date - timedelta(days=31)  # ~2 16-day periods

        typer.echo(f"   📅 Downloading data from {start_date} to {end_date}")
        typer.echo("   🌍 Coverage: Africa region (20W, 35S, 55E, 40N)")
        typer.echo("   📊 Product: MOD13Q1 (Terra) vegetation indices")
        typer.echo("   🌿 Variables: NDVI, EVI with quality filtering")

        result = client.download_vegetation_indices(
            start_date=start_date,
            end_date=end_date,
            product="MOD13Q1",
            area_bounds=(-20.0, -35.0, 55.0, 40.0),  # Africa bounds
        )

        if result.success:
            typer.echo(f"   ✅ Download successful: {result.files_processed} files")
            typer.echo(
                f"   📁 Total size: {result.total_size_bytes / 1024 / 1024:.2f} MB"
            )
            typer.echo(f"   🗺️  Tiles processed: {len(result.tiles_processed)}")
            typer.echo(
                f"   ⏱️  Duration: {result.download_duration_seconds:.1f} seconds"
            )

            # Display quality summary
            if result.quality_summary:
                quality = result.quality_summary
                typer.echo("   🔍 Quality Assessment:")
                typer.echo(
                    f"      Valid files: {quality.get('valid_files', 0)}/{quality.get('total_files', 0)}"
                )
                typer.echo(
                    f"      Validation rate: {quality.get('validation_rate', 0):.1%}"
                )

            # Process vegetation indices for a sample of files
            if result.file_paths:
                typer.echo("   🌿 Processing vegetation indices...")
                sample_files = result.file_paths[:3]  # Process first 3 files as demo

                processed_count = 0
                for file_path in sample_files:
                    try:
                        processing_results = client.process_vegetation_indices(
                            file_path,
                            vegetation_indices=["NDVI", "EVI"],
                            apply_quality_filter=True,
                        )

                        for proc_result in processing_results:
                            if proc_result.success:
                                stats = proc_result.statistics
                                typer.echo(
                                    f"     ✅ {proc_result.vegetation_index}: "
                                    f"mean={stats.get('mean', 0):.3f}, "
                                    f"valid_pixels={proc_result.valid_pixel_count:,}"
                                )
                                processed_count += 1
                            else:
                                typer.echo(
                                    f"     ❌ {proc_result.vegetation_index}: {proc_result.error_message}"
                                )

                    except Exception as e:
                        typer.echo(
                            f"     ⚠️  Processing failed for {file_path.name}: {e}"
                        )

                typer.echo(
                    f"   📊 Successfully processed {processed_count} vegetation indices"
                )

            # Validate downloaded files
            typer.echo("   🔍 Validating downloaded files...")
            validated_files = 0

            for file_path in result.file_paths[:5]:  # Validate first 5 files
                validation = client.validate_modis_file(file_path)
                if validation["success"]:
                    validated_files += 1
                    size_mb = validation["file_size_mb"]
                    subdatasets = validation["subdatasets_count"]
                    typer.echo(
                        f"     ✅ {file_path.name}: {size_mb:.1f}MB, {subdatasets} datasets"
                    )
                else:
                    typer.echo(
                        f"     ❌ {file_path.name}: {validation.get('error_message', 'Unknown error')}"
                    )

            typer.echo(
                f"   📋 Validated: {validated_files}/{min(len(result.file_paths), 5)} files"
            )

        else:
            typer.echo(f"❌ Download failed: {result.error_message}", err=True)
            raise typer.Exit(1)

        # Clean up old files
        typer.echo("   🧹 Cleaning up old files...")
        deleted_count = client.cleanup_old_files(days_to_keep=60)
        typer.echo(f"   🗑️  Deleted {deleted_count} old files")

    except ImportError:
        typer.echo("❌ Error: MODIS dependencies not installed", err=True)
        typer.echo("   Install with: pip install rasterio h5py pyproj")
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"❌ MODIS ingestion error: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        if client:
            client.close()


def _ingest_worldpop_data(dry_run: bool) -> None:
    """Handle WorldPop population data ingestion."""
    from .services.worldpop_client import WorldPopClient

    client = None
    try:
        typer.echo("👥 WorldPop Population Data Ingestion")

        if dry_run:
            typer.echo("   📋 Dry run mode - would download:")
            typer.echo("   • Population density data (100m resolution)")
            typer.echo("   • Age/sex structure data (1km resolution)")
            typer.echo("   • Geographic coverage: Sub-Saharan Africa")
            typer.echo("   • Target countries: Kenya, Uganda, Tanzania, Nigeria")
            typer.echo("   • Target year: 2020")
            typer.echo("   • File format: GeoTIFF")
            return

        client = WorldPopClient()

        # Define priority countries for malaria analysis
        priority_countries = ["KEN", "UGA", "TZA", "NGA", "GHA", "MLI", "BFA", "SEN"]
        target_year = 2020

        typer.echo(f"   🌍 Target countries: {', '.join(priority_countries)}")
        typer.echo(f"   📅 Target year: {target_year}")
        typer.echo("   🔍 Discovering available datasets...")

        # Discover available datasets
        available_datasets = client.discover_available_datasets(
            country_codes=priority_countries,
            data_type="population_density",
            year=target_year,
        )

        if not available_datasets:
            typer.echo("❌ No datasets found for specified countries and year")
            typer.echo("   This may be due to API connectivity or data availability")
            return

        found_countries = list(available_datasets.keys())
        typer.echo(
            f"   ✅ Found data for {len(found_countries)} countries: {', '.join(found_countries)}"
        )

        # Download population density data
        typer.echo("   📊 Downloading population density data...")

        density_result = client.download_population_data(
            country_codes=found_countries,
            target_year=target_year,
            data_type="population_density",
            resolution="100m",
        )

        if density_result.success:
            typer.echo("   ✅ Population density download successful")
            typer.echo(f"   📁 Files downloaded: {density_result.files_processed}")
            typer.echo(
                f"   💾 Total size: {density_result.total_size_bytes / 1024 / 1024:.2f} MB"
            )
            typer.echo(
                f"   ⏱️  Duration: {density_result.download_duration_seconds:.1f} seconds"
            )

            # Validate downloaded files
            typer.echo("   🔍 Validating downloaded files...")
            validated_files = 0

            for file_path in density_result.file_paths:
                validation = client.validate_population_file(file_path)
                if validation["success"]:
                    validated_files += 1
                    total_pop = validation.get("population_stats", {}).get(
                        "total_population", 0
                    )
                    typer.echo(f"     ✅ {file_path.name}: {total_pop:,.0f} people")
                else:
                    typer.echo(
                        f"     ❌ {file_path.name}: {validation.get('error_message', 'Unknown error')}"
                    )

            typer.echo(
                f"   📊 Validated: {validated_files}/{len(density_result.file_paths)} files"
            )

        else:
            typer.echo(
                f"   ❌ Population density download failed: {density_result.error_message}"
            )

        # Download age-specific data for children under 5 (key for malaria)
        typer.echo("   👶 Downloading age-specific data (children under 5)...")

        age_data = client.get_age_specific_population(
            country_codes=found_countries[:3],  # Limit to first 3 countries for demo
            target_year=target_year,
            age_groups=["0", "1", "5"],  # Ages 0, 1, and 5 years
        )

        if age_data:
            typer.echo(
                f"   ✅ Age-specific data retrieved for {len(age_data)} countries"
            )
            for country, ages in age_data.items():
                under_5_total = sum(ages.values())
                typer.echo(f"     {country}: {under_5_total:,.0f} children under 5")
        else:
            typer.echo("   ⚠️  Age-specific data not available")

        # Calculate population at risk (if malaria risk data available)
        typer.echo("   🦟 Attempting population-at-risk calculation...")

        # Check for existing malaria risk files
        risk_files_found = 0

        for file_path in density_result.file_paths:
            # Look for corresponding risk files (this would be from MAP data)
            risk_file_pattern = (
                file_path.parent.parent / "map" / f"risk_{file_path.stem}.tif"
            )

            if risk_file_pattern.exists():
                typer.echo(f"     🔍 Found risk data for {file_path.stem}")

                # Calculate population at risk
                area_bounds = (-20.0, -35.0, 55.0, 40.0)  # Africa bounds
                risk_result = client.calculate_population_at_risk(
                    population_file=file_path,
                    malaria_risk_file=risk_file_pattern,
                    area_bounds=area_bounds,
                    risk_threshold=0.1,
                )

                if risk_result:
                    typer.echo(
                        f"       Total population: {risk_result.total_population:,.0f}"
                    )
                    typer.echo(
                        f"       Population at risk: {risk_result.population_at_risk:,.0f}"
                    )
                    typer.echo(
                        f"       Risk percentage: {risk_result.risk_percentage:.1f}%"
                    )
                    typer.echo(
                        f"       Children under 5 at risk: {risk_result.children_under_5_at_risk:,.0f}"
                    )
                    risk_files_found += 1

        if risk_files_found == 0:
            typer.echo(
                "     ⚠️  No malaria risk surfaces found for population-at-risk calculation"
            )
            typer.echo(
                "     📝 Run 'malaria-predictor ingest-data map' first to download risk data"
            )

        typer.echo("   🧹 Cleaning up old files...")
        deleted_count = client.cleanup_old_files(days_to_keep=60)
        typer.echo(f"   🗑️  Deleted {deleted_count} old files")

    except Exception as e:
        typer.echo(f"❌ Error during WorldPop ingestion: {e}", err=True)
        raise typer.Exit(1) from e
    finally:
        if client:
            client.close()


@app.command()
def harmonize_data(
    region_bounds: str = typer.Option(
        None, help="Geographic bounds as 'west,south,east,north' (e.g., '-10,-5,10,5')"
    ),
    target_date: str = typer.Option(
        None, help="Target date for prediction (YYYY-MM-DD, defaults to today)"
    ),
    lookback_days: int = typer.Option(
        90, help="Number of days to look back for temporal features"
    ),
    resolution: str = typer.Option(
        "1km", help="Target spatial resolution (1km, 5km, 10km)"
    ),
    output_dir: str = typer.Option(
        None, help="Output directory for harmonized features"
    ),
    show_quality: bool = typer.Option(True, help="Show data quality assessment"),
    cache_results: bool = typer.Option(
        True, help="Cache harmonized results for future use"
    ),
) -> None:
    """Harmonize multi-source environmental data for ML feature engineering."""
    import asyncio
    import json
    from datetime import date, datetime
    from pathlib import Path

    from .config import Settings
    from .services.unified_data_harmonizer import UnifiedDataHarmonizer

    typer.echo("🔄 Starting data harmonization pipeline...")

    # Parse and validate inputs
    if region_bounds:
        try:
            bounds = tuple(map(float, region_bounds.split(",")))
            if len(bounds) != 4:
                raise ValueError("Must provide exactly 4 values")
            west, south, east, north = bounds
            typer.echo(
                f"   🗺️  Region: {west:.3f}°W to {east:.3f}°E, {south:.3f}°S to {north:.3f}°N"
            )
        except ValueError as e:
            typer.echo(f"❌ Invalid region bounds: {e}", err=True)
            typer.echo(
                "   Expected format: 'west,south,east,north' (e.g., '-10,-5,10,5')"
            )
            raise typer.Exit(1) from e
    else:
        # Default to Nigeria bounds for demonstration
        bounds = (2.5, 4.0, 14.8, 14.0)
        typer.echo(f"   🗺️  Using default region (Nigeria): {bounds}")

    # Parse target date
    if target_date:
        try:
            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError as e:
            typer.echo(f"❌ Invalid date format: {e}", err=True)
            typer.echo("   Expected format: YYYY-MM-DD (e.g., '2023-06-15')")
            raise typer.Exit(1) from e
    else:
        target_date_obj = date.today()
        typer.echo(f"   📅 Using today's date: {target_date_obj}")

    # Validate resolution
    if resolution not in ["1km", "5km", "10km"]:
        typer.echo(f"❌ Invalid resolution: {resolution}", err=True)
        typer.echo("   Valid options: 1km, 5km, 10km")
        raise typer.Exit(1)

    typer.echo(f"   🎯 Target resolution: {resolution}")
    typer.echo(f"   ⏰ Lookback period: {lookback_days} days")

    async def run_harmonization():
        try:
            # Initialize settings and harmonizer
            settings = Settings()
            harmonizer = UnifiedDataHarmonizer(settings)

            # Validate region bounds
            if not harmonizer.validate_region_bounds(bounds):
                typer.echo(
                    "❌ Invalid region bounds - region too large or invalid coordinates",
                    err=True,
                )
                return False

            typer.echo("   🔍 Downloading and harmonizing data from all sources...")

            # Run harmonization
            result = await harmonizer.get_harmonized_features(
                region_bounds=bounds,
                target_date=target_date_obj,
                lookback_days=lookback_days,
                target_resolution=resolution,
            )

            # Display results
            typer.echo("✅ Data harmonization completed!")
            typer.echo(f"   📊 Generated {len(result.feature_names)} ML-ready features")
            typer.echo(f"   🎯 Target date: {target_date_obj}")
            typer.echo(f"   📏 Resolution: {result.target_resolution}")
            typer.echo(f"   ⏱️  Processing time: {result.processing_timestamp}")

            # Show feature summary
            typer.echo("\n📋 Feature Summary:")
            feature_groups: dict[str, list[str]] = {}
            for feature_name in result.feature_names:
                group = feature_name.split("_")[0]
                if group not in feature_groups:
                    feature_groups[group] = []
                feature_groups[group].append(feature_name)

            for group, features in feature_groups.items():
                typer.echo(f"   {group.upper()}: {len(features)} features")
                if len(features) <= 5:
                    for feature in features:
                        typer.echo(f"     - {feature}")
                else:
                    for feature in features[:3]:
                        typer.echo(f"     - {feature}")
                    typer.echo(f"     - ... and {len(features) - 3} more")

            # Show quality assessment
            if show_quality and result.quality_metrics:
                typer.echo("\n🔍 Data Quality Assessment:")
                quality_metrics = result.quality_metrics

                if "overall_quality" in quality_metrics:
                    overall_quality = quality_metrics["overall_quality"]
                    typer.echo(f"   Overall Quality: {overall_quality:.3f}")

                    if overall_quality >= 0.8:
                        typer.echo("   Status: ✅ High quality")
                    elif overall_quality >= 0.6:
                        typer.echo("   Status: ⚠️  Medium quality")
                    else:
                        typer.echo("   Status: ❌ Low quality")

                if "source_quality" in quality_metrics:
                    source_quality = quality_metrics["source_quality"]
                    for source, quality_info in source_quality.items():
                        score = quality_info.get("score", 0)
                        typer.echo(f"   {source.upper()}: {score:.3f}")

                        flags = quality_info.get("flags", [])
                        if flags:
                            typer.echo(f"     Issues: {', '.join(flags)}")

            # Save results if output directory specified
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                # Save feature data
                for feature_name, feature_data in result.data.items():
                    feature_file = output_path / f"{feature_name}.npy"
                    import numpy as np

                    np.save(feature_file, feature_data)

                # Save metadata
                metadata = {
                    "feature_names": result.feature_names,
                    "spatial_bounds": result.spatial_bounds,
                    "temporal_range": [dt.isoformat() for dt in result.temporal_range],
                    "target_resolution": result.target_resolution,
                    "processing_timestamp": result.processing_timestamp.isoformat(),
                    "quality_metrics": result.quality_metrics,
                    "metadata": result.metadata,
                }

                metadata_file = output_path / "harmonization_metadata.json"
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2, default=str)

                typer.echo(f"\n💾 Results saved to: {output_path}")
                typer.echo(f"   Feature files: {len(result.feature_names)} .npy files")
                typer.echo("   Metadata: harmonization_metadata.json")

            return True

        except Exception as e:
            typer.echo(f"❌ Error during harmonization: {e}", err=True)
            return False

    # Run the async harmonization
    success = asyncio.run(run_harmonization())
    if not success:
        raise typer.Exit(1)


@app.command()
def validate_harmonization(
    data_dir: str = typer.Argument(..., help="Directory containing harmonized data"),
    show_details: bool = typer.Option(False, help="Show detailed validation results"),
    check_correlations: bool = typer.Option(
        True, help="Check cross-source correlations"
    ),
) -> None:
    """Validate harmonized data quality and consistency."""
    import json
    from pathlib import Path

    import numpy as np

    from .services.feature_engineering import QualityManager

    data_path = Path(data_dir)

    if not data_path.exists():
        typer.echo(f"❌ Data directory not found: {data_dir}", err=True)
        raise typer.Exit(1)

    # Load metadata
    metadata_file = data_path / "harmonization_metadata.json"
    if not metadata_file.exists():
        typer.echo(f"❌ Metadata file not found: {metadata_file}", err=True)
        raise typer.Exit(1)

    with open(metadata_file) as f:
        metadata = json.load(f)

    typer.echo(f"🔍 Validating harmonized data in: {data_dir}")
    typer.echo(f"   📊 Features: {len(metadata['feature_names'])}")
    typer.echo(f"   📏 Resolution: {metadata['target_resolution']}")
    typer.echo(f"   📅 Processed: {metadata['processing_timestamp']}")

    # Load feature data
    harmonized_data = {}
    feature_groups: dict[str, list[str]] = {}

    for feature_name in metadata["feature_names"]:
        feature_file = data_path / f"{feature_name}.npy"
        if feature_file.exists():
            data_array = np.load(feature_file)

            # Group by data source
            source = feature_name.split("_")[0]
            if source not in feature_groups:
                feature_groups[source] = {}
            feature_groups[source][feature_name] = {"data": data_array}
        else:
            typer.echo(f"   ⚠️  Missing feature file: {feature_name}.npy")

    # Organize data by source for quality assessment
    for source in feature_groups.keys():
        # Use first feature from each source as representative
        first_feature = next(iter(feature_groups[source].values()))
        harmonized_data[source] = first_feature

    # Run quality assessment
    quality_manager = QualityManager()
    quality_assessment = quality_manager.assess_harmonized_quality(harmonized_data)

    # Display validation results
    typer.echo("\n📋 Validation Results:")

    overall_quality = quality_assessment.get("overall_quality", 0)
    quality_category = quality_assessment.get("quality_category", "unknown")

    typer.echo(f"   Overall Quality: {overall_quality:.3f} ({quality_category})")

    if overall_quality >= 0.8:
        typer.echo("   Status: ✅ Data meets quality standards")
    elif overall_quality >= 0.6:
        typer.echo("   Status: ⚠️  Data has moderate quality issues")
    else:
        typer.echo("   Status: ❌ Data has significant quality issues")

    # Source-specific validation
    source_quality = quality_assessment.get("source_quality", {})
    if source_quality:
        typer.echo("\n🎯 Source Quality:")
        for source, quality_info in source_quality.items():
            score = quality_info.get("score", 0)
            flags = quality_info.get("flags", [])

            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
            typer.echo(f"   {source.upper()}: {score:.3f} {status}")

            if flags and show_details:
                typer.echo(f"     Issues: {', '.join(flags)}")

    # Cross-source consistency
    consistency_checks = quality_assessment.get("consistency_checks", {})
    if consistency_checks and check_correlations:
        typer.echo("\n🔗 Cross-Source Consistency:")

        overall_consistency = consistency_checks.get("overall_consistency", False)
        status = "✅" if overall_consistency else "⚠️"
        typer.echo(f"   Overall Consistency: {status}")

        if show_details:
            checks = consistency_checks.get("checks", [])
            for check in checks:
                check_name = check.get("check", "unknown")
                value = check.get("value", 0)
                passed = check.get("passed", False)

                status = "✅" if passed else "❌"
                typer.echo(f"   {check_name}: {value:.3f} {status}")

    # Data completeness
    completeness = quality_assessment.get("data_completeness", {})
    if completeness:
        typer.echo("\n📊 Data Completeness:")

        overall_completeness = completeness.get("overall_completeness", 0)
        complete_sources = completeness.get("complete_sources", 0)
        total_sources = completeness.get("total_sources", 0)

        typer.echo(f"   Overall: {overall_completeness:.1%}")
        typer.echo(f"   Complete Sources: {complete_sources}/{total_sources}")

        if show_details:
            source_completeness = completeness.get("source_completeness", {})
            for source, completeness_ratio in source_completeness.items():
                typer.echo(f"   {source.upper()}: {completeness_ratio:.1%}")

    # Feature statistics
    if show_details:
        typer.echo("\n📈 Feature Statistics:")
        for feature_name in metadata["feature_names"][:10]:  # Show first 10
            feature_file = data_path / f"{feature_name}.npy"
            if feature_file.exists():
                data_array = np.load(feature_file)

                # Calculate basic statistics
                valid_data = data_array[~np.isnan(data_array)]
                if len(valid_data) > 0:
                    mean_val = np.mean(valid_data)
                    std_val = np.std(valid_data)
                    min_val = np.min(valid_data)
                    max_val = np.max(valid_data)

                    typer.echo(f"   {feature_name}:")
                    typer.echo(f"     Range: [{min_val:.3f}, {max_val:.3f}]")
                    typer.echo(f"     Mean ± Std: {mean_val:.3f} ± {std_val:.3f}")
                    typer.echo(
                        f"     Valid pixels: {len(valid_data)}/{data_array.size} ({len(valid_data) / data_array.size:.1%})"
                    )

        if len(metadata["feature_names"]) > 10:
            typer.echo(
                f"   ... and {len(metadata['feature_names']) - 10} more features"
            )


if __name__ == "__main__":
    app()
