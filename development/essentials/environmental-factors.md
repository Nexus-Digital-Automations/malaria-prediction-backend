# Environmental Factors Affecting Malaria Transmission

## Critical Environmental Factors for Tracking

### Temperature Factors (Most Important)
- **Daily mean temperature** (optimal: ~25°C)
- **Daily min/max temperatures** (transmission window: 18-34°C)
- **Temperature extremes** (<16°C or >34°C limit transmission)
- **Diurnal temperature range** (especially important in highlands)
- **Temperature anomalies** from historical norms

### Rainfall & Hydrology
- **Monthly rainfall** (80mm+ needed for transmission)
- **Seasonal rainfall patterns**
- **Post-rainfall periods** (1-2 months for peak transmission)
- **Flooding events** and receding patterns
- **Water body proximity** (risk elevated within 5km)
- **Drainage characteristics** (slope, soil type)

### Humidity
- **Relative humidity** (60%+ needed for mosquito survival)
- **Seasonal humidity patterns**
- **Microclimate humidity**

### Vegetation & Land Use
- **NDVI/EVI indices** (strong predictors)
- **Land cover types** (forest, agriculture, urban)
- **Forest fragmentation** (edges = higher risk)
- **Agricultural practices** (rice paddies = breeding sites)
- **Urban agriculture presence**

### Topographical Factors
- **Elevation** (thresholds vary by region: 1,400-2,000m)
- **Valley shape** (U-shaped > V-shaped for risk)
- **Slope gradient and aspect**
- **Topographic wetness index**

### Human-Environment Interactions
- **Population density** (non-linear relationship)
- **Housing quality** (modern materials = lower risk)
- **Water management practices**
- **Infrastructure development**

## Implementation Notes

- Use 5km resolution as standard for constituency-level predictions
- Temperature is the primary limiting factor in highland areas
- Rainfall creates breeding sites but relationship is non-linear
- Combine multiple factors for accurate risk assessment
