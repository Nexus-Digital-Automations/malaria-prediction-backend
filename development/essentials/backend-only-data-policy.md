# Backend-Only Data Policy
**PROJECT MANDATE: COMPREHENSIVE BACKEND DATA USAGE**

## 🚨 CRITICAL DATA ARCHITECTURE REQUIREMENT

### ABSOLUTE PROHIBITION OF MOCK DATA
**ALL frontend data MUST originate from the backend API - ZERO exceptions for malaria-related information**

### COMPREHENSIVE BACKEND UTILIZATION MANDATE

#### 📋 FRONTEND DATA REQUIREMENTS

**✅ REQUIRED DATA SOURCES:**
- **Malaria Prediction Data**: Backend API endpoints only (`/predict/*`)
- **Environmental Data**: Backend-processed ERA5, CHIRPS, MODIS, WorldPop data
- **Risk Assessments**: Backend-calculated risk scores and uncertainty quantification
- **Historical Data**: Backend-aggregated time series and trends
- **Geospatial Data**: Backend spatial analysis and clustering results
- **Model Outputs**: Backend ML model predictions (LSTM, Transformer, Ensemble)
- **Health Metrics**: Backend system health and monitoring data
- **User Authentication**: Backend JWT tokens and permission validation

**❌ ABSOLUTELY PROHIBITED:**
- Mock malaria risk data
- Hardcoded prediction values
- Static environmental datasets
- Fake coordinates or location data
- Simulated health outcomes
- Dummy model responses
- Test malaria statistics (except in dedicated test environments)
- Placeholder risk assessments

#### 🔧 IMPLEMENTATION STANDARDS

**FLUTTER FRONTEND REQUIREMENTS:**
- All HTTP requests must target actual backend endpoints
- No local data generation for malaria-related features
- Implement proper error handling for backend failures
- Use backend configuration for all application settings
- Validate all data received from backend APIs

**API INTEGRATION STANDARDS:**
```dart
// ✅ CORRECT - Backend API calls
final response = await http.get(
  Uri.parse('${backendUrl}/predict/single'),
  headers: {'Authorization': 'Bearer $token'}
);

// ❌ PROHIBITED - Mock data
final mockRiskScore = 0.75; // NEVER DO THIS
```

**STATE MANAGEMENT WITH BACKEND DATA:**
```dart
// ✅ CORRECT - BLoC with backend integration
class PredictionBloc extends Bloc<PredictionEvent, PredictionState> {
  final MalariaPredictionService _service;
  
  PredictionBloc(this._service) : super(PredictionInitial()) {
    on<RequestPrediction>(_onRequestPrediction);
  }
  
  Future<void> _onRequestPrediction(
    RequestPrediction event,
    Emitter<PredictionState> emit,
  ) async {
    emit(PredictionLoading());
    try {
      final result = await _service.getPrediction(
        latitude: event.latitude,
        longitude: event.longitude,
        date: event.date,
      );
      emit(PredictionLoaded(result));
    } catch (e) {
      emit(PredictionError(e.toString()));
    }
  }
}
```

#### 🛡️ ENFORCEMENT PROTOCOLS

**DEVELOPMENT STANDARDS:**
- All PRs must demonstrate backend API integration
- Code reviews must verify no mock malaria data exists
- Testing environments must use dedicated test backends
- Production builds must have zero hardcoded malaria data

**VALIDATION CHECKPOINTS:**
1. **Code Review**: Verify all malaria data comes from backend APIs
2. **Build Process**: Automated checks for mock data patterns
3. **Testing**: End-to-end tests must use actual backend services
4. **Deployment**: Production verification of backend connectivity

**BACKEND API COVERAGE REQUIREMENTS:**
- Single location predictions: `/predict/single`
- Batch predictions: `/predict/batch`
- Time series analysis: `/predict/time-series`
- Risk mapping: `/predict/risk-map`
- Historical trends: `/predict/historical`
- Model performance: `/health/models`
- System metrics: `/health/metrics`

#### 📊 BACKEND SERVICE ARCHITECTURE

**MANDATORY BACKEND SERVICES:**
```python
# Malaria Prediction API Endpoints
@app.post("/predict/single")
async def predict_single_location(request: PredictionRequest) -> PredictionResponse:
    """Real-time malaria risk prediction for single location"""
    
@app.post("/predict/batch")
async def predict_batch_locations(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """Batch processing for multiple locations"""
    
@app.post("/predict/time-series")
async def predict_time_series(request: TimeSeriesRequest) -> TimeSeriesResponse:
    """Historical and forecast time series analysis"""
```

**COMPREHENSIVE DATA PROCESSING:**
- Real-time environmental data ingestion
- ML model inference and uncertainty quantification
- Spatial analysis and risk clustering
- Temporal trend analysis
- Performance monitoring and logging

#### 🚨 VIOLATION CONSEQUENCES

**IMMEDIATE ACTIONS FOR POLICY VIOLATIONS:**
1. **Code Rejection**: Any PR with mock malaria data is rejected immediately
2. **Refactoring Requirement**: Existing mock data must be replaced with backend calls
3. **Testing Failure**: Applications failing to connect to backend cannot be deployed
4. **Documentation Update**: All mock data usage must be documented and scheduled for removal

#### 💡 IMPLEMENTATION STRATEGY

**PHASE 1: BACKEND API COMPLETION**
- Ensure all required endpoints are implemented and tested
- Validate data accuracy and performance
- Implement proper error handling and fallback mechanisms

**PHASE 2: FRONTEND INTEGRATION**
- Replace all mock data with backend API calls
- Implement comprehensive error handling
- Add loading states and user feedback for API operations

**PHASE 3: VALIDATION AND TESTING**
- End-to-end testing with real backend services
- Performance optimization for API communication
- User acceptance testing with actual malaria prediction data

#### 📋 COMPLIANCE CHECKLIST

**BEFORE EVERY DEPLOYMENT:**
- [ ] All malaria predictions come from backend ML models
- [ ] Environmental data sourced from backend processing services
- [ ] User authentication handled by backend JWT system
- [ ] System health metrics retrieved from backend monitoring
- [ ] No hardcoded malaria risk values in frontend code
- [ ] All API endpoints properly integrated and tested
- [ ] Error handling implemented for backend failures
- [ ] Loading states provided for all async operations

#### 🎯 SUCCESS CRITERIA

**DEFINITION OF COMPLIANCE:**
- 100% of malaria-related data originates from backend APIs
- Zero mock data related to health, risk, or prediction outcomes
- Comprehensive backend utilization across all application features
- Robust error handling and user experience for API interactions
- Real-time integration with environmental data sources
- Accurate ML model predictions displayed to users

---

**POLICY AUTHORITY**: This policy is mandatory for all development work and cannot be overridden without explicit project management approval.

**REVIEW SCHEDULE**: Monthly compliance audits and backend integration assessments.

**CONTACT**: All questions regarding this policy should be directed to the technical lead and backend development team.