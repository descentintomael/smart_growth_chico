# Fire Risk Index

## Overview

The Fire Risk Index provides a parcel-level assessment of wildfire risk across the Chico Planning Area. This analysis combines multiple risk factors including CAL FIRE hazard zones, terrain slope, Wildland-Urban Interface status, historical fire proximity, and vegetation fuel loads to create a composite risk score for each parcel.

This analysis examines 29,333 parcels, identifying areas where fire risk is elevated and supporting smart growth policies that prioritize infill development over expansion into fire-prone areas.

### Why Fire Risk Matters for Smart Growth

Fire risk analysis supports smart growth advocacy in several ways:

- **Development patterns**: Sprawl development pushes housing into fire-prone wildland areas
- **Infrastructure costs**: Firefighting and emergency services are more expensive at the urban fringe
- **Insurance impacts**: Increasing fire risk is driving up insurance costs and causing non-renewals
- **Regulatory requirements**: California's SB 9 exempts High/Very High FHSZ parcels from some ADU provisions
- **Climate adaptation**: Smart growth concentrates development away from fire-prone areas


## Data Sources

The Fire Risk Index integrates data from multiple authoritative sources:

| Data Source | Provider | Description |
|-------------|----------|-------------|
| Fire Hazard Severity Zones | CAL FIRE | Official state classification of fire hazard severity |
| Digital Elevation Model | USGS 1/3 Arc-Second | High-resolution terrain elevation for slope calculation |
| WUI Classification | SILVIS Lab (University of Wisconsin) | Wildland-Urban Interface boundaries and density classes |
| Historical Fire Perimeters | CAL FIRE FRAP | Fire perimeters from 1878-2024 |
| Parcel Boundaries | Butte County Assessor | Parcel geometry and attributes |


## Methodology Components

The Fire Risk Index combines five weighted components to create a composite score (0-100) for each parcel. Higher scores indicate greater fire risk.

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| FHSZ Zone | 35% | CAL FIRE hazard severity classification |
| Slope Risk | 20% | Terrain slope from DEM |
| WUI Classification | 20% | Wildland-Urban Interface status |
| Historical Fire Proximity | 15% | Distance to fires in last 30 years |
| Vegetation Fuel | 10% | Fuel load risk |


### Component 1: FHSZ Zone (35%)

**What It Measures**

The Fire Hazard Severity Zone classification from CAL FIRE represents the official state assessment of fire hazard potential. FHSZ zones are based on fuel loading, slope, fire weather, and other environmental factors.

**Why It's Weighted Highest**

FHSZ is the most authoritative and legally significant measure of fire hazard. It affects building codes, insurance availability, and development regulations. Zones classified as High or Very High face additional requirements.

**Scoring**

| FHSZ Class | Score |
|------------|-------|
| Very High | 100 |
| High | 75 |
| Moderate | 50 |
| Non-FHSZ (Urban) | 0 |


### Component 2: Slope Risk (20%)

**What It Measures**

Terrain slope affects fire behavior significantly. Fire spreads faster uphill due to flame preheating of fuels above. Steep slopes also make firefighting access more difficult.

**Calculation**

Slope is derived from the USGS 1/3 arc-second Digital Elevation Model and calculated for each parcel's centroid. Slopes are converted to a 0-100 score using a linear scale where 45 degrees equals 100.

**Why It Matters**

Steep terrain amplifies fire spread rates and intensity. A fire burning uphill on a 30% slope may spread twice as fast as on flat ground.


### Component 3: WUI Classification (20%)

**What It Measures**

The Wildland-Urban Interface is where homes and wildland vegetation meet or intermix. The SILVIS Lab classification identifies parcels as Interface (housing adjacent to wildland), Intermix (housing interspersed with wildland), or Non-WUI.

**Scoring**

| WUI Class | Score |
|-----------|-------|
| Intermix | 100 |
| Interface | 100 |
| Non-WUI | 0 |

**Why It Matters**

WUI areas face the highest risk of structure loss in wildfires. In Chico, 53.1% of parcels are within the WUI, highlighting the extent of development at the wildland edge.


### Component 4: Historical Fire Proximity (15%)

**What It Measures**

Distance to historical fire perimeters from the past 30 years (1994-2024). Parcels closer to areas that have burned face elevated risk from fire regime patterns.

**Calculation**

Distance to the nearest fire perimeter is measured and converted to a 0-100 score. Parcels within 0.5 miles score 100; parcels beyond 10 miles score 0.

**Why It Matters**

Historical fire patterns indicate areas with fire-prone conditions. Nearby fires also affect vegetation recovery and accumulated fuels.


### Component 5: Vegetation Fuel (10%)

**What It Measures**

Fuel loading based on vegetation type and density. This component estimates the amount of burnable material present.

**Why It's Weighted Lowest**

While important, fuel loading is the most dynamic factor and can be modified through vegetation management. It receives lower weight than more permanent factors like FHSZ classification and slope.


## Tier Classification

Parcels are classified into four risk tiers based on their composite Fire Risk score:

| Tier | Score Range | Interpretation |
|------|-------------|----------------|
| Extreme | 80-100 | Multiple high-risk factors present; highest priority for mitigation |
| High | 60-79 | Elevated risk from combination of factors |
| Moderate | 40-59 | Some risk factors present; typical urban-edge conditions |
| Low | 0-39 | Limited fire risk factors; urban core areas |


## Key Findings

### Summary Statistics

| Metric | Value |
|--------|-------|
| Total Parcels Analyzed | 29,333 |
| Mean Fire Risk Score | 32.7 |
| Median Fire Risk Score | 35.5 |
| Score Range | 9 - 91 |

### Tier Distribution

| Tier | Count | Percentage |
|------|-------|------------|
| Low | 16,721 | 57.0% |
| Moderate | 12,601 | 43.0% |
| High | 1 | 0.0% |
| Extreme | 10 | 0.0% |

### WUI Statistics

| Metric | Value |
|--------|-------|
| Parcels in WUI | 15,567 |
| Percent in WUI | 53.1% |


## Advocacy Applications

These findings support smart growth advocacy by highlighting fire risk associated with sprawl development patterns:

1. **Fire risk is concentrated at the urban fringe**, supporting policies that prioritize infill development over greenfield expansion

2. **Over half of Chico's parcels are in the WUI**, demonstrating the extent of development at the wildland interface

3. **High/Extreme risk is rare in the urban core**, showing that infill locations offer lower fire risk than peripheral development

4. **FHSZ classifications affect development rights**, with Very High zones facing restrictions on certain housing types under California law


## Technical Notes

### Processing Steps

1. Parcel centroids extracted from Butte County parcel boundaries
2. FHSZ classification joined by spatial intersection
3. Slope calculated from USGS DEM using rasterio/rasterstats zonal statistics
4. WUI classification joined from SILVIS Lab dataset
5. Historical fire proximity calculated using nearest neighbor to fire perimeters
6. Component scores normalized to 0-100 scale
7. Weighted average computed for composite score
8. Tier classification applied based on score thresholds

### Tools & Software

- Python 3.11
- GeoPandas for spatial analysis
- rasterio/rasterstats for raster processing
- QGIS for visualization and validation

### Limitations

- Fire risk is inherently dynamic and changes with weather, fuel conditions, and fire suppression activities
- This index represents relative risk based on available data, not absolute probability of fire occurrence
- Vegetation data may not reflect recent clearing or growth
- Some parcels may lack complete data for all components
