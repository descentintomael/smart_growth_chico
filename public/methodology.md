# Smart Growth Value Index

## Overview

The Smart Growth Value Index is a composite measure that evaluates every parcel within the City of Chico according to principles of fiscally sustainable, infrastructure-efficient development. The index assigns each parcel a score from 0 to 100, where higher scores indicate stronger alignment with smart growth principles.

This analysis examines 27,425 parcels using official City of Chico and Butte County geographic data. The index is designed to help residents, policymakers, and planners understand which areas of the city are performing well from a fiscal and infrastructure standpoint, and where opportunities exist for sustainable infill development.

### What Is Smart Growth?

Smart growth is a planning philosophy that prioritizes development patterns which:

- Generate sufficient tax revenue to maintain the infrastructure they require
- Make efficient use of existing infrastructure investments
- Reduce automobile dependence through walkable, bikeable design
- Concentrate development in areas already served by public facilities
- Preserve open space by directing growth to appropriate locations

The Smart Growth Value Index quantifies these principles using measurable data for every parcel in the city.


## Index Components

The index combines five components, each measuring a distinct aspect of smart growth performance. Components are weighted according to their relative importance and combined into a single composite score.

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| Fiscal Productivity | 30% | Tax revenue generated per acre |
| Land Utilization | 25% | Efficiency of land use |
| Infrastructure Accessibility | 20% | Access to public facilities |
| Zoning Capacity Headroom | 15% | Potential for infill development |
| Location Efficiency | 10% | Strategic positioning |

### Component 1: Fiscal Productivity (30%)

**What It Measures**

Fiscal productivity quantifies the property tax revenue a parcel generates relative to its land area. This metric addresses a fundamental question of municipal finance: does the tax revenue from a property cover the cost of providing services and maintaining infrastructure to that property?

**Why It Matters**

Research by organizations including Strong Towns has demonstrated that low-density development patterns often fail to generate sufficient tax revenue to cover their long-term infrastructure costs. Downtown and higher-density areas typically generate substantially more revenue per acre than suburban edge development, even when individual property values are lower.

In Chico, downtown parcels generate approximately $40,000 to $90,000 per acre annually in property tax revenue, while edge development generates approximately $15,000 to $20,000 per acre.

**Calculation**

The fiscal productivity score is calculated as follows:

1. Divide annual property tax by lot acreage for each parcel
2. Exclude extreme outliers at the 1st and 99th percentiles to prevent distortion
3. Rank all parcels by tax revenue per acre
4. Convert rankings to a percentile score (0-100)

A parcel scoring 75 on this component generates more tax revenue per acre than 75% of all parcels in the city.

**Data Source**: Butte County Assessor Parcel Data (Tax_Amnt, Lt_Acre fields)

### Component 2: Land Utilization (25%)

**What It Measures**

Land utilization assesses how efficiently a parcel uses its available land area. This component combines two sub-metrics:

- **Building Coverage Ratio** (50% of component): The proportion of the lot covered by building footprints
- **Improvement Intensity** (50% of component): The ratio of improvement value (buildings and structures) to land value

**Why It Matters**

Parcels that make efficient use of their land area require less total land to accommodate the same number of residents, businesses, or activities. This efficiency reduces the geographic extent of development, lowering infrastructure costs and preserving undeveloped land for agriculture, recreation, or natural habitat.

A single-family home on a quarter-acre lot uses land less efficiently than a duplex or small apartment building on the same lot. Commercial buildings that occupy most of their lot are more efficient than those surrounded by large parking areas.

**Calculation**

1. Calculate building coverage ratio (total building footprint area divided by lot area)
2. Calculate improvement-to-land value ratio (assessed improvement value divided by land value)
3. Convert each sub-metric to a percentile rank (0-100)
4. Average the two percentile ranks

**Data Sources**: Butte County Assessor Parcel Data, Building Footprints GIS layer

### Component 3: Infrastructure Accessibility (20%)

**What It Measures**

Infrastructure accessibility evaluates how well a parcel is served by existing public infrastructure. This component examines three factors:

| Sub-metric | Weight | Description |
|------------|--------|-------------|
| Park Proximity | 40% | Distance to nearest public park |
| Bike Facility Proximity | 40% | Distance to nearest bike lane or path |
| Complete Streets | 20% | Presence of curb and gutter |

**Why It Matters**

Development in areas already served by infrastructure leverages past public investments rather than requiring new expenditures. Proximity to parks and bike facilities supports active transportation and reduces automobile dependence. The presence of curb and gutter indicates a complete street design that supports pedestrian safety and stormwater management.

**Calculation**

Distance-based scores use a benchmark of 2,640 feet, representing approximately a 10-minute walk:

- Parcels within 0 feet of an amenity receive a score of 100
- Parcels at 2,640 feet receive a score of 50
- Parcels beyond 5,280 feet receive a score of 0

The curb and gutter component is binary: parcels with complete street infrastructure receive 100; those without receive 0.

The final infrastructure score is the weighted average of all three sub-metrics.

**Data Sources**: City of Chico Parks and Recreation GIS layer, Bike Facilities GIS layer, Lack of Curb/Gutter GIS layer

### Component 4: Zoning Capacity Headroom (15%)

**What It Measures**

Zoning capacity headroom quantifies the gap between a parcel's current use and the maximum development intensity permitted under its zoning designation. This component identifies parcels where additional development is legally permitted under existing regulations.

**Why It Matters**

Parcels with high headroom represent opportunities for infill development without requiring zoning changes or variances. A single-family home on land zoned for multifamily housing has significant headroom; a high-rise on commercially zoned land has little headroom.

Focusing development on parcels with available capacity directs growth to locations the city has already designated as appropriate for higher intensity uses.

**Calculation**

Both current use and zoning allowance are mapped to an intensity scale of 0 to 7:

| Intensity Level | Current Use Examples | Zoning Examples |
|-----------------|---------------------|-----------------|
| 0 | Vacant | - |
| 1 | Agricultural, Open Space | AG, AR |
| 2 | Single-Family Detached | R1, RS |
| 3 | Duplex | R2 |
| 4-5 | Triplex through Small Multifamily | R3, R4, RM |
| 6-7 | Large Multifamily, Commercial | CC, CR, CS, Mixed-Use |

Headroom is calculated as:

```
Headroom = (Allowed Intensity - Current Intensity) / Allowed Intensity x 100
```

A single-family home (intensity 2) on R3-zoned land (intensity 5) would have headroom of 60%.

**Interpretation Note**: High headroom scores indicate opportunity, not deficiency. A parcel scoring high on this component is not underperforming; rather, it represents a location where the city has planned for and permitted additional development.

**Data Sources**: City of Chico Assessor Parcel Data (Use_Code field), Zoning and General Plan GIS layer

### Component 5: Location Efficiency (10%)

**What It Measures**

Location efficiency evaluates a parcel's strategic position within the city based on two factors:

- **Opportunity Site Proximity** (50% of component): Distance to city-designated opportunity sites identified in planning documents
- **Core Proximity** (50% of component): Distance from the geographic center of the city

**Why It Matters**

Development in central, strategically-located areas benefits from existing infrastructure networks and reduces the need for service extensions. The city has identified specific opportunity sites as priorities for development or redevelopment; proximity to these areas indicates alignment with adopted planning goals.

**Calculation**

Both sub-metrics use distance-based scoring:

- Opportunity site proximity uses a 2,640-foot benchmark
- Core proximity uses a 3-mile benchmark

Scores decrease linearly with distance, with parcels at or beyond the benchmark distance receiving the minimum score.

**Data Sources**: City of Chico Opportunity Sites GIS layer, City Boundaries GIS layer

## Composite Score Calculation

The Smart Growth Value Index is calculated as the weighted sum of all five component scores:

```
Smart Growth Index = (Fiscal x 0.30) + (Utilization x 0.25) +
                     (Infrastructure x 0.20) + (Headroom x 0.15) +
                     (Location x 0.10)
```

### Tier Classification

Parcels are classified into four tiers based on their composite score:

| Tier | Score Range | Description |
|------|-------------|-------------|
| Excellent | 80 - 100 | Strong alignment with smart growth principles across multiple dimensions |
| Good | 60 - 79 | Above-average performance; solid smart growth characteristics |
| Moderate | 40 - 59 | Average performance; some smart growth strengths and weaknesses |
| Low | 0 - 39 | Below-average performance; limited smart growth characteristics |

### Redevelopment Opportunity Flag

Parcels meeting both of the following criteria are flagged as redevelopment opportunities:

- Zoning Capacity Headroom score of 60 or higher
- Location Efficiency score of 50 or higher

These parcels combine significant development capacity under existing zoning with favorable strategic locations, making them prime candidates for infill development.

## Data Sources

This analysis uses official City of Chico geographic information system (GIS) data:

| Data Layer | Contents | Record Count |
|------------|----------|--------------|
| Parcels_Chico_CityLimits | Property boundaries, tax assessments, use codes | 29,333 |
| Zoning_GP_Landuse | Zoning classifications, General Plan designations | 32,228 |
| chico_buildings | Building footprints | 31,715 |
| CITYOFCHICOPARKSANDRECREATION | Public park boundaries | 39 |
| BikeFacilities | Bike lanes and paths | 214 |
| OpportunitySites | City-designated development opportunity areas | 15 |
| LackofCurbGutter | Streets lacking complete infrastructure | 914 |

All geographic data uses the California State Plane Zone 2 coordinate system (EPSG:2226).

## Methodological Notes

### Percentile Ranking

Most components use percentile ranking rather than raw values. This approach offers several advantages:

- **Comparability**: All scores use the same 0-100 scale regardless of the underlying metric
- **Interpretability**: A score of 75 means the parcel outperforms 75% of all parcels
- **Outlier Resistance**: Extreme values do not compress the distribution for typical parcels

### Winsorization

For the fiscal productivity component, values at the 1st and 99th percentiles are capped before ranking. This prevents a small number of extreme outliers from distorting the distribution. A parcel with anomalously high tax revenue (potentially due to data issues or unique circumstances) does not artificially compress scores for all other parcels.

### Distance Calculations

All distance measurements are calculated from the centroid (geometric center) of each parcel to the nearest point of the target feature (park boundary, bike facility line, etc.). Distances are measured in feet using the projected coordinate system.

### Parcel Exclusions

Two categories of parcels are excluded from the analysis to ensure accurate and meaningful comparisons:

**Tax-Exempt Parcels (803 parcels excluded)**

Parcels with $0 in annual property tax are excluded from the analysis. These typically include government-owned properties, public facilities, schools, churches, and other tax-exempt land. Because these parcels are not subject to market-based development decisions and do not generate property tax revenue, including them would distort the fiscal productivity calculations and introduce parcels that are not candidates for private development.

**Condominium Unit Parcels (1,105 parcels excluded)**

Parcels smaller than 0.05 acres (approximately 2,178 square feet) are excluded. The majority of these parcels are individual condominium units, which are recorded in the assessor database as separate parcels with the unit footprint listed as the lot size.

This recording practice creates artificially inflated tax-per-acre calculations. For example, a condominium unit with 871 square feet of floor area paying $2,000 per year in property taxes would calculate to over $100,000 per acre, compared to the citywide median of approximately $21,000 per acre for standard parcels. This inflation does not reflect actual land productivity; rather, it reflects the accounting treatment of shared-ownership properties.

Condominium buildings remain represented in the analysis through their common area parcels, which reflect the actual land footprint of the development.

| Exclusion Category | Parcels Excluded | Reason |
|-------------------|------------------|--------|
| Tax-exempt ($0 tax) | 803 | Not subject to market development |
| Micro parcels (<0.05 acres) | 1,105 | Primarily condo units with distorted metrics |
| **Total Excluded** | **1,908** | **6.5% of original dataset** |

### Limitations

Users should be aware of the following limitations:

1. **Aggregate Measure**: The index combines multiple factors into a single score. Two parcels with identical scores may have very different component profiles.

2. **Current Conditions**: The index reflects conditions at the time of data collection. Property values, infrastructure, and zoning may change.

3. **Policy Neutrality**: The index measures alignment with smart growth principles but does not prescribe specific policy actions. Low-scoring parcels are not inherently problematic; they may serve important purposes (agriculture, open space) that are not captured by this framework.

4. **Parcel-Level Analysis**: The index evaluates individual parcels. Neighborhood-level patterns may differ from parcel-level scores.

5. **Data Completeness**: Approximately 53% of parcels successfully matched to zoning data. Parcels without zoning matches use default intensity assumptions.

## Interpreting the Map

### High-Scoring Areas

Parcels scoring in the Excellent (80+) or Good (60-79) tiers typically exhibit several of the following characteristics:

- Located in or near downtown Chico
- Generate substantial tax revenue relative to land area
- Well-served by parks, bike facilities, and complete streets
- Buildings that efficiently use available lot area
- Near city-designated opportunity sites

### Low-Scoring Areas

Parcels scoring in the Low tier (below 40) typically exhibit several of the following characteristics:

- Located at the city's edges
- Lower tax revenue per acre
- Greater distances from parks and bike facilities
- Lower building coverage ratios
- Already developed to their zoning capacity (limited headroom)

### Individual Parcel Interpretation

The index is most useful for identifying patterns across the city rather than evaluating individual properties. A single parcel's score reflects a combination of factors, some of which (location, zoning) are beyond the property owner's control.

Residents viewing their own property's score should consider which components contribute most to their rating. A low score on fiscal productivity may simply reflect that the property is residential rather than commercial; a low infrastructure score may reflect distance from amenities rather than any deficiency of the property itself.

## About This Analysis

This analysis was prepared by Smart Growth Advocates of Chico using Python geospatial analysis tools (GeoPandas, Shapely) applied to official City of Chico and Butte County GIS data. The methodology is designed to be transparent, reproducible, and grounded in established smart growth planning principles.

For questions about the methodology or to request the underlying data and code, contact Smart Growth Advocates of Chico.

*Analysis Date: December 2025*
