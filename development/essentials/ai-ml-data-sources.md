# AI/ML Data Sources for Malaria Prediction System

## 🎯 Overview

This document outlines the comprehensive data sources, processing pipelines, and integration strategies for building robust AI/ML models for malaria outbreak prediction. The system integrates 80+ environmental, epidemiological, and socioeconomic data sources to create accurate, real-time prediction capabilities.

## 🌍 Primary Environmental Data Sources

### 🌡️ Temperature Data (Critical for Model Training)

#### ERA5 Reanalysis (Primary Source)
- **Provider**: Copernicus Climate Data Store
- **Resolution**: 31km spatial, hourly temporal
- **Coverage**: Global, 1940-present (3-month delay for reanalysis)
- **API Access**: CDS API with Python client
- **AI/ML Relevance**: 
  - Primary feature for temperature-dependent mosquito development models
  - Essential for LSTM time-series prediction
  - Used in transformer attention mechanisms for seasonal patterns

```python
# ERA5 Data Integration Example
import cdsapi
from xarray import Dataset

class ERA5DataProcessor:
    def __init__(self, api_key: str):
        self.client = cdsapi.Client()
    
    def fetch_temperature_data(self, region: BoundingBox, date_range: DateRange) -> Dataset:
        """Fetch and process ERA5 temperature data for ML training"""
        request = {
            'product_type': 'reanalysis',
            'variable': ['2m_temperature', 'maximum_2m_temperature', 'minimum_2m_temperature'],
            'area': [region.north, region.west, region.south, region.east],
            'date': f"{date_range.start}/{date_range.end}",
            'time': [f"{h:02d}:00" for h in range(0, 24, 3)],  # 3-hourly data
            'format': 'netcdf'
        }
        
        # Download and process data
        dataset = self.client.retrieve('reanalysis-era5-single-levels', request)
        return self.preprocess_for_ml(dataset)
    
    def preprocess_for_ml(self, dataset: Dataset) -> Dataset:
        """Preprocess ERA5 data for ML model consumption"""
        # Calculate diurnal temperature range
        dataset['diurnal_range'] = dataset['maximum_2m_temperature'] - dataset['minimum_2m_temperature']
        
        # Calculate temperature anomalies from historical mean
        climatology = dataset.groupby('time.month').mean('time')
        dataset['temperature_anomaly'] = dataset.groupby('time.month') - climatology
        
        # Add lagged features for temporal modeling
        dataset['temp_lag_7d'] = dataset['2m_temperature'].shift(time=7)
        dataset['temp_lag_14d'] = dataset['2m_temperature'].shift(time=14)
        
        return dataset
```

#### MODIS Land Surface Temperature (High Resolution)
- **Provider**: NASA LAADS DAAC
- **Resolution**: 1km spatial, daily temporal
- **Coverage**: Global, 2000-present
- **AI/ML Application**: Fine-scale temperature modeling for urban/rural heterogeneity

### 🌧️ Precipitation Data (Critical for Breeding Site Prediction)

#### CHIRPS (Climate Hazards Group InfraRed Precipitation with Station Data)
- **Provider**: UC Santa Barbara Climate Hazards Center
- **Resolution**: 5.5km spatial, daily temporal
- **Coverage**: 50°S-50°N, 1981-present
- **Latency**: 3-week delay for quality-controlled final product
- **AI/ML Features**:
  - Primary rainfall predictor for breeding site modeling
  - Used in CNN models for spatial pattern recognition
  - Essential for RNN/LSTM temporal sequence modeling

```python
class CHIRPSProcessor:
    def __init__(self):
        self.base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/"
    
    def extract_precipitation_features(self, data: xarray.Dataset) -> Dict[str, np.ndarray]:
        """Extract ML-ready features from CHIRPS precipitation data"""
        features = {}
        
        # Cumulative precipitation (breeding site indicator)
        features['precip_7d'] = data['precip'].rolling(time=7).sum()
        features['precip_14d'] = data['precip'].rolling(time=14).sum()
        features['precip_30d'] = data['precip'].rolling(time=30).sum()
        
        # Dry spell indicators (negative predictor)
        features['dry_days'] = (data['precip'] < 1.0).astype(int)
        features['dry_spell_length'] = self.calculate_dry_spell_lengths(features['dry_days'])
        
        # Intensity measures
        features['precip_intensity'] = data['precip'] / features['precip_7d']
        features['heavy_rain_events'] = (data['precip'] > 20.0).astype(int)
        
        return features
    
    def calculate_breeding_site_suitability(self, precip_data: xarray.Dataset) -> xarray.Dataset:
        """Calculate breeding site suitability index from precipitation"""
        # Optimal range: 10-200mm monthly precipitation
        monthly_precip = precip_data['precip'].resample(time='M').sum()
        
        suitability = xarray.where(
            (monthly_precip >= 10) & (monthly_precip <= 200),
            1.0 - abs(monthly_precip - 105) / 95,  # Peak at 105mm
            0.0
        )
        
        return suitability
```

#### GPM IMERG (Global Precipitation Measurement)
- **Provider**: NASA Goddard Earth Sciences Data Information Services Center
- **Resolution**: 11km spatial, 30-minute temporal
- **Coverage**: Global, 2014-present (near real-time)
- **AI/ML Application**: Real-time precipitation monitoring for nowcasting models

### 🌱 Vegetation Indices (Habitat Quality Indicators)

#### MODIS Vegetation Indices (NDVI/EVI)
- **Provider**: NASA Land Processes DAAC
- **Resolution**: 250m-1km spatial, 16-day composite
- **Coverage**: Global, 2000-present
- **AI/ML Features**:
  - Primary vegetation health indicators
  - Used in CNN models for landscape classification
  - Critical for habitat suitability modeling

```python
class VegetationProcessor:
    def __init__(self):
        self.modis_client = MODISClient()
    
    def extract_vegetation_features(self, ndvi_data: xarray.Dataset, evi_data: xarray.Dataset) -> Dict[str, np.ndarray]:
        """Extract vegetation features for malaria prediction models"""
        features = {}
        
        # Vegetation health indicators
        features['ndvi_mean'] = ndvi_data['NDVI'].rolling(time=6).mean()  # 3-month average
        features['ndvi_std'] = ndvi_data['NDVI'].rolling(time=6).std()    # Variability
        features['ndvi_trend'] = self.calculate_trend(ndvi_data['NDVI'])
        
        # Enhanced Vegetation Index (better for dense vegetation)
        features['evi_mean'] = evi_data['EVI'].rolling(time=6).mean()
        features['evi_peak'] = evi_data['EVI'].rolling(time=12).max()     # Annual peak
        
        # Vegetation anomalies (drought/stress indicators)
        climatology = ndvi_data.groupby('time.month').mean()
        features['ndvi_anomaly'] = ndvi_data.groupby('time.month') - climatology
        
        # Habitat fragmentation (edge detection)
        features['vegetation_edges'] = self.detect_vegetation_edges(ndvi_data['NDVI'])
        
        return features
    
    def calculate_habitat_suitability(self, ndvi: np.ndarray, evi: np.ndarray) -> np.ndarray:
        """Calculate habitat suitability from vegetation indices"""
        # Optimal NDVI range for malaria vectors: 0.1-0.6
        ndvi_suitability = np.where(
            (ndvi >= 0.1) & (ndvi <= 0.6),
            1.0 - np.abs(ndvi - 0.35) / 0.25,
            0.0
        )
        
        # Combine NDVI and EVI for comprehensive assessment
        return 0.7 * ndvi_suitability + 0.3 * np.clip(evi / 0.4, 0, 1)
```

#### Sentinel-2 Multispectral Imagery
- **Provider**: European Space Agency Copernicus Programme
- **Resolution**: 10-60m spatial, 5-day revisit
- **Coverage**: Global, 2015-present
- **AI/ML Application**: High-resolution habitat classification using deep learning

## 🏥 Epidemiological Data Sources

### Malaria Atlas Project (MAP)
- **Provider**: Oxford University Big Data Institute
- **Data Types**: 
  - Historical malaria incidence maps (5km resolution)
  - Plasmodium falciparum/vivax prevalence
  - Insecticide resistance data
  - Vector occurrence records (440,000+ data points)
- **AI/ML Integration**:
  - Ground truth labels for supervised learning
  - Transfer learning base models
  - Validation datasets for model evaluation

```python
class MAPDataIntegration:
    def __init__(self, api_key: str):
        self.map_api = MAPClient(api_key)
    
    def fetch_historical_incidence(self, region: BoundingBox, years: List[int]) -> xarray.Dataset:
        """Fetch historical malaria incidence data for model training"""
        incidence_data = self.map_api.get_raster_data(
            indicator='malaria_incidence',
            region=region,
            years=years,
            resolution='5km'
        )
        
        return self.preprocess_incidence_for_ml(incidence_data)
    
    def create_training_labels(self, incidence_data: xarray.Dataset, threshold: float = 10.0) -> np.ndarray:
        """Create binary classification labels from incidence data"""
        # Binary classification: high risk (>10 cases/1000) vs low risk
        high_risk_labels = (incidence_data['incidence'] > threshold).astype(int)
        
        # Multi-class classification
        labels = xarray.where(
            incidence_data['incidence'] < 1.0, 0,    # Very low risk
            xarray.where(
                incidence_data['incidence'] < 10.0, 1,  # Low risk
                xarray.where(
                    incidence_data['incidence'] < 50.0, 2,  # Medium risk
                    3  # High risk
                )
            )
        )
        
        return labels.values
```

### WHO Global Health Observatory
- **Provider**: World Health Organization
- **Data Types**: 
  - Country-level malaria statistics
  - Treatment effectiveness data
  - Vector control intervention coverage
  - Healthcare system capacity metrics
- **Update Frequency**: Annual with quarterly updates
- **AI/ML Application**: Contextual features for country-level models

### MalariaGEN Vector Observatory
- **Provider**: Wellcome Sanger Institute
- **Data Types**:
  - Genomic data from 25,510+ mosquito specimens
  - Insecticide resistance mutations
  - Species identification and abundance
- **AI/ML Application**: Genomic feature engineering for resistance prediction

## 👥 Population & Socioeconomic Data

### WorldPop Population Datasets
- **Provider**: WorldPop Research Group, University of Southampton
- **Resolution**: 100m spatial resolution
- **Coverage**: Global, 2000-2030 (projections)
- **Data Types**:
  - Population density grids
  - Age-sex structure
  - Pregnancy estimates
  - Poverty mapping
- **AI/ML Features**: Demographic risk factors, vulnerability indicators

```python
class PopulationDataProcessor:
    def __init__(self):
        self.worldpop_api = WorldPopAPI()
    
    def extract_population_features(self, pop_data: xarray.Dataset) -> Dict[str, np.ndarray]:
        """Extract population-based features for malaria risk modeling"""
        features = {}
        
        # Basic demographic features
        features['population_density'] = pop_data['population'] / pop_data['area']
        features['child_density'] = pop_data['population_under5'] / pop_data['area']
        features['pregnancy_density'] = pop_data['pregnancies'] / pop_data['area']
        
        # Vulnerability indicators
        features['population_growth'] = self.calculate_population_growth(pop_data)
        features['urban_rural_ratio'] = pop_data['urban_pop'] / pop_data['rural_pop']
        
        # Spatial clustering metrics
        features['population_clustering'] = self.calculate_clustering_index(pop_data['population'])
        
        return features
    
    def calculate_vulnerability_index(self, pop_data: xarray.Dataset, poverty_data: xarray.Dataset) -> np.ndarray:
        """Calculate population vulnerability to malaria"""
        # Weighted combination of risk factors
        vulnerability = (
            0.3 * pop_data['children_under5'] / pop_data['total_population'] +  # Age vulnerability
            0.2 * pop_data['pregnancies'] / pop_data['total_population'] +     # Pregnancy vulnerability
            0.3 * poverty_data['poverty_rate'] +                               # Economic vulnerability
            0.2 * (1 - pop_data['urban_pop'] / pop_data['total_population'])   # Rural vulnerability
        )
        
        return np.clip(vulnerability, 0, 1)
```

### OpenStreetMap Infrastructure Data
- **Provider**: OpenStreetMap Foundation
- **Data Types**: 
  - Healthcare facility locations
  - Transportation networks
  - Water infrastructure
  - Housing quality indicators
- **AI/ML Application**: Accessibility and infrastructure features

## 🛰️ Advanced Remote Sensing Data

### Sentinel-1 Radar Data
- **Provider**: European Space Agency
- **Application**: Water body detection, flood monitoring
- **Resolution**: 10m spatial, 12-day revisit
- **AI/ML Use**: Surface water mapping for breeding site identification

### Landsat Time Series
- **Provider**: USGS/NASA
- **Application**: Long-term environmental change detection
- **Resolution**: 30m spatial, 16-day revisit
- **Coverage**: 1972-present (longest satellite record)

## 🔬 Laboratory & Clinical Data

### Drug Resistance Surveillance
- **Sources**: 
  - WWARN (WorldWide Antimalarial Resistance Network)
  - USAID President's Malaria Initiative
  - National malaria control programs
- **Data Types**: 
  - Artemisinin resistance markers
  - Treatment failure rates
  - Drug efficacy studies

### Vector Surveillance Data
- **Sources**: 
  - National vector surveillance programs
  - Research institutions
  - WHO vector surveillance networks
- **Data Types**: 
  - Vector species abundance
  - Biting behavior patterns
  - Seasonal activity cycles
  - Insecticide resistance bioassay results

## 🤖 AI/ML Data Processing Pipeline

### Data Ingestion Architecture
```python
class MalariaDataPipeline:
    def __init__(self):
        self.data_sources = {
            'era5': ERA5Client(),
            'chirps': CHIRPSClient(),
            'modis': MODISClient(),
            'map': MAPClient(),
            'worldpop': WorldPopClient()
        }
        self.feature_store = FeatureStore()
        self.ml_models = ModelRegistry()
    
    def ingest_and_process(self, region: BoundingBox, date_range: DateRange) -> FeatureMatrix:
        """Main data processing pipeline for ML model training/inference"""
        
        # Step 1: Parallel data ingestion
        raw_data = asyncio.gather(*[
            source.fetch_data(region, date_range) 
            for source in self.data_sources.values()
        ])
        
        # Step 2: Spatial alignment and temporal synchronization
        aligned_data = self.spatial_temporal_alignment(raw_data)
        
        # Step 3: Feature engineering
        features = self.feature_engineering(aligned_data)
        
        # Step 4: Data quality validation
        validated_features = self.validate_data_quality(features)
        
        # Step 5: Feature scaling and normalization
        normalized_features = self.normalize_features(validated_features)
        
        return normalized_features
    
    def feature_engineering(self, aligned_data: Dict) -> FeatureMatrix:
        """Comprehensive feature engineering for malaria prediction"""
        feature_engineers = {
            'temperature': TemperatureFeatureEngineer(),
            'precipitation': PrecipitationFeatureEngineer(),
            'vegetation': VegetationFeatureEngineer(),
            'population': PopulationFeatureEngineer(),
            'temporal': TemporalFeatureEngineer()
        }
        
        engineered_features = []
        for data_type, data in aligned_data.items():
            if data_type in feature_engineers:
                features = feature_engineers[data_type].extract_features(data)
                engineered_features.append(features)
        
        # Combine all features
        combined_features = np.concatenate(engineered_features, axis=1)
        
        return FeatureMatrix(combined_features, self.generate_feature_names())
```

### Feature Engineering Strategies

#### Temporal Features
- **Lagged Variables**: 7, 14, 30-day lags for environmental variables
- **Moving Averages**: 3, 6, 12-month rolling means
- **Seasonal Decomposition**: Trend, seasonal, and residual components
- **Anomaly Detection**: Deviations from historical norms

#### Spatial Features
- **Neighborhood Statistics**: Mean, std, min, max in surrounding areas
- **Distance Features**: Distance to water bodies, healthcare facilities
- **Elevation Derivatives**: Slope, aspect, topographic wetness index
- **Land Cover Classification**: Habitat type proportions

#### Interaction Features
- **Temperature-Precipitation Interaction**: Combined indices for breeding suitability
- **Vegetation-Climate Interaction**: Drought stress indicators
- **Population-Environment Interaction**: Human-environment risk factors

### Model Training Data Specifications

#### Training Dataset Structure
```python
class MalariaTrainingDataset:
    def __init__(self):
        self.features = [
            # Environmental features (40 variables)
            'temperature_mean', 'temperature_max', 'temperature_min', 'temperature_range',
            'precipitation_total', 'precipitation_intensity', 'dry_spell_length',
            'ndvi_mean', 'ndvi_anomaly', 'evi_peak', 'vegetation_edges',
            
            # Temporal features (20 variables)
            'temp_lag_7d', 'temp_lag_14d', 'precip_lag_7d', 'precip_lag_14d',
            'seasonal_temp', 'seasonal_precip', 'month_sin', 'month_cos',
            
            # Spatial features (15 variables)
            'elevation', 'slope', 'aspect', 'distance_water', 'distance_healthcare',
            'population_density', 'urban_rural_ratio', 'poverty_index',
            
            # Interaction features (10 variables)
            'temp_precip_interaction', 'breeding_suitability_index',
            'habitat_fragmentation', 'human_environment_risk'
        ]
        
        self.target_variables = [
            'malaria_incidence',      # Primary target
            'outbreak_probability',   # Binary classification
            'risk_category'          # Multi-class (0-3)
        ]
    
    def prepare_training_data(self, years: List[int], regions: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data with proper train/validation splits"""
        
        # Temporal split (80% train, 20% validation)
        train_years = years[:int(0.8 * len(years))]
        val_years = years[int(0.8 * len(years)):]
        
        # Spatial split (hold out specific regions for testing)
        train_regions = regions[:int(0.8 * len(regions))]
        val_regions = regions[int(0.8 * len(regions)):]
        
        X_train = self.load_features(train_years, train_regions)
        y_train = self.load_targets(train_years, train_regions)
        X_val = self.load_features(val_years, val_regions)
        y_val = self.load_targets(val_years, val_regions)
        
        return (X_train, y_train), (X_val, y_val)
```

## 📊 Data Quality & Validation

### Quality Assurance Framework
```python
class DataQualityValidator:
    def __init__(self):
        self.quality_thresholds = {
            'completeness': 0.95,        # 95% data completeness required
            'accuracy': 0.90,            # 90% accuracy for validated samples
            'timeliness': 7,              # Maximum 7-day data latency
            'consistency': 0.98          # 98% consistency across sources
        }
    
    def validate_data_quality(self, dataset: xarray.Dataset) -> QualityReport:
        """Comprehensive data quality validation"""
        report = QualityReport()
        
        # Completeness check
        report.completeness = self.check_completeness(dataset)
        
        # Accuracy validation (where ground truth available)
        report.accuracy = self.validate_accuracy(dataset)
        
        # Timeliness assessment
        report.timeliness = self.check_timeliness(dataset)
        
        # Consistency validation
        report.consistency = self.check_consistency(dataset)
        
        # Outlier detection
        report.outliers = self.detect_outliers(dataset)
        
        return report
    
    def flag_quality_issues(self, report: QualityReport) -> List[QualityFlag]:
        """Flag data quality issues for manual review"""
        flags = []
        
        if report.completeness < self.quality_thresholds['completeness']:
            flags.append(QualityFlag('INCOMPLETE_DATA', 'Data completeness below threshold'))
        
        if len(report.outliers) > 0.05 * len(report.dataset):
            flags.append(QualityFlag('EXCESSIVE_OUTLIERS', 'Too many outlier values detected'))
        
        return flags
```

### Missing Data Handling Strategy
```python
class MissingDataHandler:
    def __init__(self):
        self.imputation_strategies = {
            'temperature': 'temporal_interpolation',
            'precipitation': 'spatial_interpolation', 
            'vegetation': 'seasonal_climatology',
            'population': 'forward_fill'
        }
    
    def handle_missing_data(self, dataset: xarray.Dataset) -> xarray.Dataset:
        """Intelligent missing data imputation"""
        
        for variable in dataset.data_vars:
            missing_fraction = dataset[variable].isnull().sum() / dataset[variable].size
            
            if missing_fraction > 0.30:
                # Too much missing data - exclude variable
                dataset = dataset.drop_vars(variable)
                logging.warning(f"Dropped {variable}: {missing_fraction:.2%} missing")
            
            elif missing_fraction > 0.05:
                # Significant missing data - advanced imputation
                dataset[variable] = self.advanced_imputation(dataset[variable])
            
            else:
                # Minimal missing data - simple interpolation
                dataset[variable] = dataset[variable].interpolate_na(dim='time')
        
        return dataset
```

## 🎯 Model Performance Optimization

### Feature Selection and Engineering
```python
class FeatureOptimizer:
    def __init__(self):
        self.feature_selectors = {
            'univariate': SelectKBest(f_regression, k=50),
            'recursive': RFE(RandomForestRegressor(), n_features_to_select=40),
            'lasso': SelectFromModel(LassoCV(cv=5)),
            'mutual_info': SelectKBest(mutual_info_regression, k=45)
        }
    
    def optimize_features(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Multi-method feature selection for optimal model performance"""
        
        # Apply multiple feature selection methods
        selected_features = {}
        for method, selector in self.feature_selectors.items():
            selector.fit(X, y)
            selected_features[method] = selector.get_support()
        
        # Ensemble feature selection (features selected by majority of methods)
        feature_votes = np.sum(list(selected_features.values()), axis=0)
        final_features = feature_votes >= len(self.feature_selectors) // 2
        
        return X[:, final_features], [self.feature_names[i] for i in np.where(final_features)[0]]
```

## 📈 Real-time Data Streaming

### Streaming Data Architecture
```python
class RealTimeDataStreamer:
    def __init__(self):
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=['kafka-cluster:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        self.redis_client = redis.Redis(host='redis-cache', port=6379)
    
    async def stream_environmental_data(self):
        """Stream real-time environmental data for nowcasting"""
        
        while True:
            try:
                # Fetch latest data from sources
                current_data = await self.fetch_current_conditions()
                
                # Process for ML inference
                processed_data = self.process_for_inference(current_data)
                
                # Send to Kafka topic for model consumption
                self.kafka_producer.send('environmental_data', processed_data)
                
                # Cache in Redis for quick access
                self.redis_client.setex(
                    f"current_conditions_{datetime.now().isoformat()}",
                    3600,  # 1 hour TTL
                    json.dumps(processed_data)
                )
                
                await asyncio.sleep(300)  # 5-minute intervals
                
            except Exception as e:
                logging.error(f"Streaming error: {e}")
                await asyncio.sleep(60)  # Wait before retry
```

## 🔄 Data Update Schedules

### Automated Data Refresh Schedule
- **ERA5**: Daily updates (5-day delay for preliminary, 3-month for final)
- **CHIRPS**: Daily updates (3-week delay for final product)
- **MODIS**: 16-day composite updates
- **MAP**: Monthly updates for recent data, annual for historical
- **WorldPop**: Annual updates with mid-year revisions
- **Clinical Data**: Weekly aggregated updates from surveillance systems

### Priority Update Matrix
| Data Source | Update Frequency | Latency | ML Model Impact | Priority |
|-------------|------------------|---------|-----------------|----------|
| ERA5 Temperature | Daily | 5 days | High | Critical |
| CHIRPS Precipitation | Daily | 21 days | High | Critical |
| MODIS Vegetation | 16 days | 2 days | Medium | High |
| MAP Incidence | Monthly | 30 days | High | High |
| Population Data | Annual | 90 days | Low | Medium |
| Vector Surveillance | Weekly | 7 days | Medium | High |

This comprehensive data architecture supports the development of highly accurate, real-time malaria prediction models by integrating diverse, high-quality data sources with robust processing pipelines and quality assurance frameworks.