# Data Source Credentials and Rate Limits

**Last Updated:** October 28, 2025
**Purpose:** Quick reference for credential URLs and API rate limits

---

## 🔐 Credential URLs

### ERA5 Climate Data (Copernicus CDS)

**Status:** ⚠️ Requires free account

#### Registration & Setup
- **Sign Up URL:** https://cds.climate.copernicus.eu/#!/home
- **Login URL:** https://cds.climate.copernicus.eu/user/login
- **API Documentation:** https://cds.climate.copernicus.eu/how-to-api
- **API Endpoint:** https://cds.climate.copernicus.eu/api/v2

#### Quick Steps
1. Register at: https://cds.climate.copernicus.eu/#!/home
2. Verify email
3. Log in and navigate to profile: https://cds.climate.copernicus.eu/user
4. Copy UID and API key from "API key" section
5. Create `~/.cdsapirc` file:
   ```
   url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR-UID:YOUR-API-KEY
   ```

#### Support
- **Forum:** https://forum.ecmwf.int/
- **Documentation:** https://confluence.ecmwf.int/display/CKB/Climate+Data+Store+(CDS)+documentation
- **User Guide:** https://cds.climate.copernicus.eu/user-guide

---

### MODIS Vegetation Data (NASA EarthData)

**Status:** ⚠️ Requires free account

#### Registration & Setup
- **Sign Up URL:** https://urs.earthdata.nasa.gov/users/new
- **Login URL:** https://urs.earthdata.nasa.gov/
- **Profile/Apps:** https://urs.earthdata.nasa.gov/profile
- **Data Portal:** https://e4ftl01.cr.usgs.gov/

#### Quick Steps
1. Register at: https://urs.earthdata.nasa.gov/users/new
2. Verify email
3. Log in and approve applications:
   - Go to: https://urs.earthdata.nasa.gov/profile
   - Navigate to "Applications → Authorized Apps"
   - Approve: MODIS, LP DAAC, NASA EarthData
4. Use credentials in application

#### Support
- **Forum:** https://forum.earthdata.nasa.gov/
- **Developer Portal:** https://earthdata.nasa.gov/collaborate/open-data-services-and-software/api
- **MODIS Info:** https://modis.gsfc.nasa.gov/

---

## 📊 Rate Limits & Usage Policies

### ERA5 (Copernicus CDS)

#### Current Rate Limits (2025)

**Request Size Limits:**
- **ERA5 Hourly Data:** 120,000 fields per request
- **ERA5 Monthly Data:** 10,000 fields per request
- **Field Calculation:** Variables × Time Steps × Grid Points

**Example Field Calculation:**
```
Request: 4 variables, 7 days (168 hours), 100×100 grid
Fields = 4 × 168 × 10,000 = 6,720,000 fields
Status: ❌ EXCEEDS LIMIT (reduce variables, time, or area)
```

**Concurrent Requests:**
- Limited per user (exact number not published)
- Varies dynamically based on system load
- Requests exceeding limits are queued automatically

**Best Practices:**
- ✅ Submit small, targeted requests
- ✅ Use 6-hourly data instead of hourly when possible
- ✅ Request smaller geographic areas
- ✅ Download data in monthly batches for large date ranges
- ❌ Avoid very large single requests (penalized in queue)

**Queue System:**
- Requests are automatically queued if limits exceeded
- Queue priority based on request size and type
- Smaller requests processed faster

**System Status:**
- Check current status: https://cds.climate.copernicus.eu/live
- System upgraded September 2024 (new CDS infrastructure)

**Important Notes:**
- Rate limits are **dynamic** and adjusted based on system load
- No fixed "requests per minute" limit
- Focus on request size rather than request frequency
- Fair usage policy applies

---

### MODIS (NASA EarthData)

#### Current Rate Limits (2025)

**FIRMS API (Fire Data):**
- **Limit:** 5,000 transactions per 10-minute interval
- **Note:** Large requests count as multiple transactions
- **Example:** Requesting 7 days of data may count as multiple transactions

**CMR API (Common Metadata Repository):**
- **Type:** Dynamic throttling
- **Trigger:** High volume of similar queries across all users
- **Response:** HTTP 429 (Too Many Requests) when throttled
- **Not User-Specific:** Based on aggregate query patterns

**General Guidelines:**
- **Typical Safe Usage:** ~300-400 requests per hour
- **Daily Usage:** ~2,000-3,000 requests per day
- **Best Practice:** Implement exponential backoff for 429 responses

**Data Download:**
- **Per-File Downloads:** No strict published limit
- **Recommended:** Use connection pooling and parallel downloads (4-8 threads)
- **Timeout:** Set reasonable timeouts (300-600 seconds per file)

**Best Practices:**
- ✅ Implement retry logic with exponential backoff
- ✅ Cache downloaded tiles locally
- ✅ Use NASA Earthdata Cloud when available (faster, better limits)
- ✅ Batch requests for multiple tiles
- ❌ Avoid rapid-fire sequential requests

**Recent Updates:**
- **September 2025:** Legacy OPeNDAP retired
- **Current:** Earthdata Cloud OPeNDAP recommended
- **Collections:** Using MODIS Collection 6.1

**System Resources:**
- **Developer Portal:** https://earthdata.nasa.gov/collaborate/open-data-services-and-software/api
- **Rate Limit Forum:** https://forum.earthdata.nasa.gov/viewtopic.php?t=4273

---

### CHIRPS (No Authentication Required)

#### Rate Limits

**Status:** ✅ Open access, no authentication

**Server:** https://data.chc.ucsb.edu/products/CHIRPS-2.0

**Usage Policy:**
- **No published rate limits**
- **Fair use expected**
- **Server bandwidth:** Shared resource

**Best Practices:**
- ✅ Implement reasonable delays between requests
- ✅ Use connection pooling
- ✅ Cache downloaded files locally
- ✅ Parallel downloads (5-8 threads recommended)
- ❌ Avoid hammering server with rapid requests

**File Sizes:**
- Daily global: ~3-5 MB
- Monthly global: ~3-5 MB
- Regional subsets: Smaller

**Recommended Approach:**
```python
# Client already implements ThreadPoolExecutor with 5 workers
client = CHIRPSClient(Settings())
# This is optimal for CHIRPS server
```

---

### MAP (Malaria Atlas Project - No Authentication Required)

#### Rate Limits

**Status:** ✅ Open access, no authentication

**Server:** https://data.malariaatlas.org

**Usage Policy:**
- **No published rate limits**
- **Reasonable use expected**
- **API is research-focused**

**Best Practices:**
- ✅ Cache data locally (annual updates)
- ✅ Reasonable request spacing
- ✅ Use R package when possible (optimized access)

**Data Characteristics:**
- **Update Frequency:** Annual for most datasets
- **File Sizes:** Vary by product (1-50 MB)
- **Recommended:** Download once, cache locally

---

### WorldPop (No Authentication Required)

#### Rate Limits

**Status:** ✅ Open access, no authentication

**Server:** https://data.worldpop.org

**Usage Policy:**
- **No published rate limits**
- **Academic/research use encouraged**
- **Fair use policy**

**Best Practices:**
- ✅ Use REST API (HTTPS only)
- ✅ Cache population data locally (annual updates)
- ✅ Parallel downloads for multiple countries (3-4 threads)

**File Sizes:**
- 100m resolution: 10-100 MB per country
- 1km resolution: 1-10 MB per country

**Security Note:**
- ✅ FTP removed from client (insecure)
- ✅ HTTPS only (secure)

---

## 💡 General Best Practices

### For All Data Sources

1. **Implement Caching**
   - Store downloaded files locally
   - Check if file exists before re-downloading
   - Use file modification times for update checks

2. **Retry Logic**
   ```python
   import time

   max_retries = 3
   for attempt in range(max_retries):
       try:
           # Download attempt
           break
       except Exception as e:
           if attempt < max_retries - 1:
               wait_time = 2 ** attempt * 60  # Exponential backoff
               time.sleep(wait_time)
           else:
               raise
   ```

3. **Rate Limit Handling**
   ```python
   from time import sleep

   # Add delays between requests
   sleep(1)  # 1 second between requests

   # Handle 429 responses
   if response.status_code == 429:
       retry_after = int(response.headers.get('Retry-After', 60))
       sleep(retry_after)
   ```

4. **Connection Pooling**
   ```python
   import requests

   session = requests.Session()
   # Reuse connection across multiple requests
   ```

5. **Progress Monitoring**
   - Log download progress
   - Track failed requests
   - Monitor queue times (ERA5)

---

## 🔧 Implementation Examples

### ERA5 - Respecting Rate Limits

```python
from malaria_predictor.services.era5_client import ERA5Client
from datetime import date

client = ERA5Client(Settings())

# ✅ GOOD: Small request
result = client.download_temperature_data(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 7),  # 7 days
    area_bounds=[10, -5, 0, 5]  # Small region
)

# ⚠️ BETTER: Break large requests into chunks
for month in range(1, 13):
    result = client.download_temperature_data(
        start_date=date(2024, month, 1),
        end_date=date(2024, month, 28),
        area_bounds=[10, -5, 0, 5]
    )
```

### MODIS - Handling Rate Limits

```python
from malaria_predictor.services.modis_client import MODISClient
import time

client = MODISClient(Settings())
client.authenticate(username="user", password="pass")

# ✅ Implement retry with backoff
def download_with_retry(client, **kwargs):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            result = client.download_vegetation_indices(**kwargs)
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt * 60
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## 📞 Support Contacts

### ERA5
- **Forum:** https://forum.ecmwf.int/
- **Support Email:** Available through user portal

### MODIS
- **Forum:** https://forum.earthdata.nasa.gov/
- **LP DAAC Support:** https://lpdaac.usgs.gov/resources/e-learning/

### CHIRPS
- **Contact:** Via UCSB Climate Hazards Center website
- **Documentation:** https://www.chc.ucsb.edu/data/chirps

### MAP
- **Website:** https://malariaatlas.org/
- **Research Inquiries:** Available on website

### WorldPop
- **Website:** https://www.worldpop.org/
- **Contact Form:** Available on website

---

## 🎯 Quick Reference Summary

| Data Source | Auth Required | Rate Limit Type | Limit Details |
|------------|---------------|-----------------|---------------|
| **ERA5** | ✅ Yes | Request size | 120K fields (hourly), 10K (monthly) |
| **MODIS** | ✅ Yes | Dynamic | ~300-400/hour, 429 on throttle |
| **CHIRPS** | ❌ No | Fair use | No published limit, be reasonable |
| **MAP** | ❌ No | Fair use | No published limit, annual data |
| **WorldPop** | ❌ No | Fair use | No published limit, annual data |

---

## ✅ Implementation Status

All clients in this codebase already implement best practices:
- ✅ Connection pooling
- ✅ Retry logic (ERA5)
- ✅ Reasonable delays
- ✅ Parallel downloads (optimized thread counts)
- ✅ Error handling
- ✅ Logging

**No additional rate limiting code needed** - the implementations are production-ready.

---

*This document is based on official API documentation and forum discussions as of October 2025. Rate limits may change; always refer to official documentation for the most current information.*
