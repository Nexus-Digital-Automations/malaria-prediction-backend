# ADR-004: Multi-Source Environmental Data Integration

## Status
Accepted

## Context

Accurate malaria prediction requires diverse environmental data:
- **Climate Data**: Temperature, humidity, precipitation affect mosquito breeding
- **Vegetation Data**: NDVI correlates with mosquito habitat suitability
- **Population Data**: Human density affects transmission dynamics
- **Historical Malaria Data**: Past outbreaks inform future predictions

Challenges:
- Different data sources have varying formats, resolutions, and update frequencies
- API rate limits and authentication requirements differ per source
- Data quality varies significantly across sources
- Need to harmonize data to a common spatial and temporal resolution

## Decision

We implemented a **Multi-Source Data Integration Architecture** with five primary sources:

### Data Sources

| Source | Data Type | Resolution | Update | API |
|--------|-----------|------------|--------|-----|
| **ERA5** | Climate (temp, humidity, precipitation) | 31km | Daily | CDS API |
| **CHIRPS** | High-res precipitation | 5.5km | Daily | HTTP/FTP |
| **MODIS** | Vegetation (NDVI, EVI, LST) | 250m-1km | 16-day | NASA Earthdata |
| **WorldPop** | Population density | 100m-1km | Annual | HTTP |
| **MAP** | Malaria prevalence, interventions | Variable | Monthly | API/R |

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Client Layer                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ERA5Client│ │CHIRPSClient│ │MODISClient│ │WorldPopClient │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬─────────┘ │
│       │            │            │              │            │
│       └────────────┴────────────┴──────────────┘            │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Harmonization Layer                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ UnifiedDataHarmonizer                                   ││
│  │  • Spatial alignment (reproject to common grid)         ││
│  │  • Temporal alignment (resample to daily)               ││
│  │  • Missing value interpolation                          ││
│  │  • Quality score calculation                            ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Feature Engineering Layer                  │
│  • Rolling statistics (7-day, 30-day averages)              │
│  • Lag features (1-week, 2-week, 1-month lags)              │
│  • Interaction features (temp × humidity)                    │
│  • Seasonal encodings (month, day of year)                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Data Clients**: Source-specific clients handling authentication, rate limiting, and format parsing

2. **Cache Layer**: Redis caching with configurable TTL to reduce API calls

3. **Data Harmonizer**: Unifies data to common resolution (0.1° grid, daily frequency)

4. **Quality Validation**: Automated checks for data completeness, range validity, and temporal consistency

## Consequences

### Positive
- Comprehensive environmental coverage for predictions
- Resilience through multiple data sources
- Standardized interface for ML pipeline
- Cached data reduces external API dependencies
- Quality scoring enables confidence assessment

### Negative
- Complex integration with 5+ external APIs
- Rate limiting requires careful request management
- Data source outages can affect predictions
- Storage requirements for historical data

### Mitigations
- Exponential backoff retry logic for API failures
- Fallback to cached data when sources unavailable
- Parallel data fetching with async clients
- Automated data quality monitoring

## References

- [Data Sources Overview](../../data-sources/overview.md)
- [ERA5 Integration](../../data-sources/era5-integration.md)
- [CHIRPS Integration](../../data-sources/chirps-integration.md)
- [MODIS Integration](../../data-sources/modis-integration.md)
- [Data Quality Validation](../../data-sources/data-quality-validation.md)
