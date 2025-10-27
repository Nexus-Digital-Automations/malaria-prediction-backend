# Data Sources Troubleshooting

> **Common issues and solutions**

## ERA5 Issues

### Authentication Failed

**Error**: `Invalid API key`

**Solution**:
```bash
# Verify credentials
echo $ECMWF_API_KEY

# Re-register if needed
# https://cds.climate.copernicus.eu/user/register
```

### Request Timeout

**Error**: `Request timed out after 60 seconds`

**Solution**:
- ERA5 requests are queued - check status at CDS portal
- Reduce spatial/temporal extent
- Use cached data when available

## CHIRPS Issues

### Download Failed

**Error**: `HTTP 404 Not Found`

**Solution**:
```python
# Verify date range is valid (1981-present)
# Check URL format
url = f"https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/tifs/p05/{year}/chirps-v2.0.{date}.tif"
```

## MODIS Issues

### Authentication Required

**Error**: `Unauthorized`

**Solution**:
```bash
# Create .netrc file for Earthdata
cat > ~/.netrc << EOF
machine urs.earthdata.nasa.gov
login YOUR_USERNAME
password YOUR_PASSWORD
EOF

chmod 600 ~/.netrc
```

### Data Not Available

**Error**: `No data for requested period`

**Solution**:
- MODIS data has 3-day processing lag
- Check for cloud cover (use quality flags)
- Try adjacent dates

## General Issues

### Memory Errors

**Error**: `MemoryError: Unable to allocate array`

**Solution**:
```python
# Process data in chunks
for chunk in data.chunks({'time': 10}):
    process_chunk(chunk)

# Or use Dask for lazy loading
import dask.array as da
data_lazy = da.from_array(data, chunks=(10, 100, 100))
```

### Slow Performance

**Solution**:
1. Use caching
2. Parallelize downloads
3. Use cloud-optimized formats (COG, Zarr)

```python
# Parallel downloads
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(download_date, date) for date in dates]
    results = [f.result() for f in futures]
```

---

**Last Updated**: October 27, 2025
