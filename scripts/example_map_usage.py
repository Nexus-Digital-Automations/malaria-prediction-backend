#!/usr/bin/env python3
"""Example script demonstrating MAP client usage.

This script shows how to:
1. Download parasite rate data from MAP
2. Validate the downloaded files
3. Process the data and extract statistics
4. Download vector occurrence data
5. Clean up old files

Run this script from the project root:
    python scripts/example_map_usage.py
"""

import sys
from datetime import date
from pathlib import Path

# Add project root to path before other imports to avoid import errors
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification
from malaria_predictor.services.map_client import MAPClient  # noqa: E402


def main():
    """Demonstrate MAP client functionality."""
    print("=== MAP Client Example ===\n")

    # Initialize client
    client = MAPClient()
    print(f"Download directory: {client.download_directory}")
    print(f"R integration available: {client._r_available}\n")

    # Get data year (MAP typically has 2-year delay)
    current_year = date.today().year
    data_year = current_year - 2

    # 1. Download parasite rate surface
    print(f"1. Downloading P. falciparum parasite rate for {data_year}...")
    pr_result = client.download_parasite_rate_surface(
        year=data_year,
        species="Pf",
        resolution="5km",
        area_bounds=(-10, -20, 10, 0),  # Small area for demo
    )

    if pr_result.success:
        print(f"   ✓ Downloaded {len(pr_result.file_paths)} file(s)")
        print(f"   Total size: {pr_result.total_size_bytes / 1024 / 1024:.2f} MB")
        print(f"   Duration: {pr_result.download_duration_seconds:.1f} seconds")

        # 2. Validate the downloaded file
        if pr_result.file_paths:
            file_path = pr_result.file_paths[0]
            print(f"\n2. Validating {file_path.name}...")

            validation = client.validate_raster_file(file_path)
            print(f"   File valid: {validation['success']}")

            if validation["success"]:
                print(f"   Resolution: {validation.get('resolution', 'N/A')}")
                print(f"   CRS: {validation.get('crs', 'N/A')}")

                if validation.get("data_range"):
                    dr = validation["data_range"]
                    print(f"   PR range: {dr['min']:.1f}% - {dr['max']:.1f}%")
                    print(f"   Mean PR: {dr['mean']:.1f}% ± {dr['std']:.1f}%")

            # 3. Process the data
            print("\n3. Processing parasite rate data...")
            pr_data = client.process_parasite_rate_data(file_path)

            if pr_data is not None:
                import numpy as np

                valid_data = pr_data[~np.isnan(pr_data)]
                print(f"   Valid pixels: {len(valid_data):,}")
                print(f"   Area with >10% PR: {(valid_data > 10).sum():,} pixels")
    else:
        print(f"   ✗ Download failed: {pr_result.error_message}")

    # 4. Download vector occurrence data
    print("\n4. Downloading Anopheles gambiae occurrence data...")
    vector_result = client.download_vector_occurrence_data(
        species_complex="gambiae",
        start_year=data_year - 5,
        end_year=data_year,
        area_bounds=(-10, -20, 10, 0),
    )

    if vector_result.success:
        print("   ✓ Downloaded vector data")
        print(f"   Files: {len(vector_result.file_paths)}")

        # Read CSV file
        if vector_result.file_paths:
            csv_file = vector_result.file_paths[0]
            try:
                import pandas as pd

                df = pd.read_csv(csv_file)
                print(f"   Records: {len(df)}")
                print(f"   Columns: {list(df.columns)}")
            except ImportError:
                print("   (Install pandas to view CSV data)")
    else:
        print(f"   ✗ Download failed: {vector_result.error_message}")

    # 5. Download intervention coverage (example)
    print(f"\n5. Downloading ITN coverage for {data_year}...")
    itn_result = client.download_intervention_coverage(
        intervention_type="ITN", year=data_year, area_bounds=(-10, -20, 10, 0)
    )

    if itn_result.success:
        print("   ✓ Downloaded ITN coverage data")
        print(f"   Files: {len(itn_result.file_paths)}")
    else:
        print(f"   ✗ Download failed: {itn_result.error_message}")

    # 6. List all downloaded files
    print("\n6. All downloaded MAP files:")
    all_files = list(client.download_directory.glob("*"))
    for f in sorted(all_files)[:10]:  # Show first 10
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"   - {f.name} ({size_mb:.2f} MB)")

    if len(all_files) > 10:
        print(f"   ... and {len(all_files) - 10} more files")

    # 7. Clean up old files (demonstration only)
    print("\n7. Cleanup demonstration (not executed)")
    print("   To clean files older than 30 days:")
    print("   deleted_count = client.cleanup_old_files(days_to_keep=30)")

    # Close client
    client.close()
    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
