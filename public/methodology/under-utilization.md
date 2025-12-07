# Under-Utilization Analysis

## Overview

The Under-Utilization Analysis identifies parcels within the City of Chico that are not being used to their full potential under current zoning and market conditions. By measuring multiple dimensions of underutilization, this analysis highlights where development capacity exists, where land values exceed building values, and where zoning changes could unlock additional housing.

This analysis examines 27,133 parcels using four distinct metrics that together paint a comprehensive picture of land utilization across the city. The composite under-utilization score identifies 151 severely underutilized parcels covering 76 acres where development potential is being significantly underused.

### Why Under-Utilization Matters

Underutilized land represents a missed opportunity for cities:

- **Housing capacity**: Sites that could accommodate more units remain underdeveloped
- **Fiscal productivity**: Underutilized parcels generate less tax revenue than their potential
- **Infrastructure efficiency**: Existing infrastructure serves fewer people than it could
- **Development pressure**: Unmet housing demand pushes development to greenfield sites

Identifying underutilized parcels helps prioritize infill development, target upzoning efforts, and demonstrate that housing capacity exists within the existing urban footprint.


## Methodology Components

The Under-Utilization Index combines four distinct metrics, each measuring a different dimension of land utilization:

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| Vertical Underutilization | 20% | Building height vs. allowed height (FAR gap) |
| Improvement Underutilization | 30% | Land value exceeding building value |
| Density Underutilization | 30% | Current use vs. allowed zoning intensity |
| Upzone Underutilization | 20% | Potential from R1→R2 upzoning |


### Component 1: Vertical Underutilization (20%)

**What It Measures**

Vertical underutilization identifies parcels where buildings are significantly shorter than what zoning allows. This component compares the actual Floor Area Ratio (FAR) to the maximum permitted FAR, calculated only for medium-density and higher zones where vertical development is expected.

**Why It Matters**

In zones that permit multi-story buildings, single-story development wastes vertical capacity. A one-story strip mall in a zone permitting four stories is leaving 75% of its development potential unused.

**Calculation**

```
Vertical Score = ((Allowed FAR - Actual FAR) / Allowed FAR) × 100
```

A parcel using only 20% of its allowed FAR would score 80 on vertical underutilization.

**Applicability**

This metric applies only to parcels in CC (Community Commercial), CR (Regional Commercial), CS (Service Commercial), CN (Neighborhood Commercial), R3, and RM zones. Single-family zones are excluded because vertical development is not typically expected.

**Findings**

- Mean vertical underutilization: 3.1 (most parcels are in low-density zones)
- Median: 0.0 (reflects exclusion of single-family zones)
- Severely underutilized count (80+): 504 parcels


### Component 2: Improvement Underutilization (30%)

**What It Measures**

Improvement underutilization identifies parcels where the land value exceeds the improvement (building) value. When land is worth more than the building on it, this suggests the building is not maximizing the site's potential.

**Why It Matters**

Land value reflects location and zoning potential. Improvement value reflects what has actually been built. When land value dominates:

- The building may be obsolete or undersized for the site
- The property may be ripe for redevelopment
- The owner is paying taxes on location value but not capturing development potential

**Calculation**

The improvement ratio (improvement value / land value) is calculated for each parcel, then inverted and converted to a percentile score:

```
Improvement Score = Percentile(1 / (Improvement Value / Land Value))
```

Parcels where land value significantly exceeds improvement value score higher.

**Findings**

- Mean improvement underutilization: 50.0 (percentile-based)
- Median: 50.0
- Land exceeds improvement count: 3,837 parcels


### Component 3: Density Underutilization (30%)

**What It Measures**

Density underutilization measures the gap between a parcel's current use intensity and its zoning-allowed intensity. This is similar to the "zoning headroom" component of the Smart Growth Index but scored inversely—high headroom means high underutilization.

**Why It Matters**

A single-family home on land zoned for apartments is not using the full development capacity that zoning permits. Identifying these parcels helps:

- Target outreach to property owners about development potential
- Prioritize infrastructure investments in areas with growth capacity
- Understand where housing could be added without zoning changes

**Calculation**

Both current use and zoning are mapped to intensity levels (0-7), then headroom is calculated:

```
Density Score = ((Allowed Intensity - Current Intensity) / Allowed Intensity) × 100
```

| Intensity Level | Examples |
|-----------------|----------|
| 0 | Vacant |
| 1 | Agricultural, Open Space |
| 2 | Single-Family Detached |
| 3 | Duplex |
| 4-5 | Triplex, Small Multifamily |
| 6-7 | Large Multifamily, Commercial |

**Findings**

- Mean density underutilization: 6.1
- Median: 0.0 (most parcels are at or near zoning capacity)
- High headroom count (60+): 2,306 parcels


### Component 4: Upzone Underutilization (20%)

**What It Measures**

Upzone underutilization identifies parcels currently zoned R1 (single-family) or R2 (duplex) that could accommodate additional units if upzoned. This component specifically models R1→R2 conversion potential.

**Why It Matters**

Single-family zoning represents the majority of residential land in most American cities. Even modest upzoning (allowing duplexes on single-family lots) can dramatically increase housing capacity without changing neighborhood character significantly.

**Calculation**

For R1 parcels, potential additional units from R2 conversion are calculated based on lot size. For R2 parcels, existing capacity is noted but not scored (they're already at least R2). Results are converted to percentile scores.

```
Upzone Score = Percentile(Potential Additional Units from R1→R2)
```

**Findings**

- Eligible parcels (R1 and R2): 11,155
- Potential new units from R1→R2 upzoning: 31,896
- Mean upzone score for R1 parcels: 51.0
- Mean upzone score for R2 parcels: 43.3


## Composite Score Calculation

The Under-Utilization Index is calculated as the weighted sum of all four component scores:

```
Under-Utilization Index = (Vertical × 0.20) + (Improvement × 0.30) +
                          (Density × 0.30) + (Upzone × 0.20)
```

### Tier Classification

Parcels are classified into four tiers based on their composite score:

| Tier | Score Range | Description |
|------|-------------|-------------|
| Severe | 80 - 100 | Significantly underutilized across multiple dimensions |
| High | 60 - 79 | Substantially underutilized; strong development potential |
| Moderate | 40 - 59 | Some underutilization; may be appropriate for current use |
| Low | 0 - 39 | Relatively well-utilized under current conditions |


## Results Summary

### Aggregate Findings

| Metric | Value |
|--------|-------|
| Total Parcels Analyzed | 27,133 |
| Severely Underutilized Parcels | 151 |
| Severely Underutilized Acres | 76.0 |
| Potential Foregone Units | 31,896 |
| Potential Annual Tax Increase | $63,792,000 |

### Summary by Zone

| Zone | Parcels | Acres | Avg. Vertical | Avg. Improvement | Avg. Density | Avg. Upzone | Foregone Units |
|------|---------|-------|---------------|------------------|--------------|-------------|----------------|
| CC | 477 | 299.4 | 41.1 | 55.4 | 33.2 | 0.0 | 0 |
| CN | 90 | 27.5 | 32.2 | 57.6 | 38.7 | 0.0 | 0 |
| CR | 143 | 393.3 | 40.5 | 57.4 | 26.8 | 0.0 | 0 |
| CS | 114 | 130.2 | 49.0 | 52.5 | 28.3 | 0.0 | 0 |
| R1 | 9,696 | 2,962.3 | 0.0 | 52.6 | 0.0 | 51.0 | 27,810 |
| R2 | 1,459 | 403.6 | 0.0 | 53.4 | 48.2 | 43.3 | 4,086 |
| R3 | 995 | 421.0 | 44.4 | 44.5 | 38.7 | 0.0 | 0 |
| RM | 171 | 41.0 | 42.5 | 49.5 | 32.6 | 0.0 | 0 |
| Other | 13,988 | 6,570.6 | 0.0 | 47.9 | 1.7 | 0.0 | 0 |

### Key Talking Points

- **151 parcels (76 acres)** are significantly underutilized
- **31,896 housing units** could be built on existing infrastructure
- **$63,792,000** in potential annual tax revenue is being foregone
- **3,837 parcels** have land worth more than their buildings


## Data Sources

| Data Layer | Purpose | Source |
|------------|---------|--------|
| Parcels_Chico_CityLimits | Property boundaries, values, use codes | Butte County Assessor |
| Zoning_GP_Landuse | Zoning classifications, allowed FAR | City of Chico |
| chico_buildings | Building footprints for FAR calculation | City of Chico GIS |

All geographic data uses the California State Plane Zone 2 coordinate system (EPSG:2226).


## Methodological Notes

### Percentile Normalization

Components 2 (Improvement) and 4 (Upzone) use percentile normalization to ensure comparability:

- All parcels are ranked on the raw metric
- Ranks are converted to percentile scores (0-100)
- A score of 75 means the parcel is more underutilized than 75% of parcels

This approach handles the wide variation in raw values and ensures each component contributes meaningfully to the composite score.

### Zone-Specific Applicability

Not all components apply equally to all zones:

- **Vertical**: Only meaningful in medium+ density zones
- **Density**: Only meaningful where zoning allows more than current use
- **Upzone**: Only applicable to R1 and R2 parcels

Parcels outside the applicable zone for a component receive a score of 0 for that component, which is weighted appropriately in the composite.

### Assumptions and Limitations

1. **FAR Calculation**: Actual FAR is estimated from building footprints, not surveyed floor area. Multi-story buildings are identified through assessor data where available.

2. **Assessment Values**: Land and improvement values from assessor data may not reflect current market conditions due to Proposition 13 limitations on reassessment.

3. **Use Code Accuracy**: Current use intensity is derived from assessor use codes, which may lag actual changes in use.

4. **Development Feasibility**: High underutilization scores indicate potential, not guaranteed developability. Site-specific factors (access, utilities, environmental constraints) affect actual feasibility.


## Interpreting the Map

### High-Score Parcels

Parcels with high underutilization scores (60+) typically exhibit:

- **Vertical gap**: Single-story buildings in multi-story zones
- **Value imbalance**: Land worth more than improvements
- **Zoning headroom**: Current use well below zoning capacity
- **Upzone potential**: R1 parcels suitable for R2 development

### Patterns Across the City

- **Commercial corridors**: High vertical and improvement underutilization
- **R1 zones near services**: High upzone potential
- **Transitional areas**: Density underutilization where zoning exceeds development

### Advocacy Applications

This data supports arguments for:

- Targeted upzoning in high-opportunity areas
- By-right development approval for infill projects
- Tax incentives for intensification of underutilized parcels
- Land value taxation to encourage development of high-value land


## About This Analysis

This analysis was prepared by Smart Growth Advocates of Chico using Python geospatial analysis tools (GeoPandas, Shapely) applied to official City of Chico and Butte County GIS data. The methodology is designed to be transparent, reproducible, and grounded in established smart growth planning principles.

For questions about the methodology or to request the underlying data and code, contact Smart Growth Advocates of Chico.

*Analysis Date: December 2025*
