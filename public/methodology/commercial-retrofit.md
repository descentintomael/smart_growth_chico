# Commercial Corridor Retrofit Analysis

## Overview

The Commercial Corridor Retrofit Analysis identifies underutilized commercial parcels along Chico's major corridors that could be transformed into mixed-use developments. These strip malls, surface parking lots, and low-intensity commercial buildings represent significant opportunities to add housing while maintaining commercial activity on the ground floor.

This analysis examines 958 commercial parcels, of which 784 (82%) are classified as underutilized based on building coverage and improvement ratios. Together, these underutilized parcels represent 580 acres of retrofit potential capable of accommodating over 14,000 housing units.

### Why Commercial Retrofit Matters

America's postwar commercial development patterns created thousands of miles of strip corridors characterized by:

- Single-story buildings surrounded by vast parking lots
- Auto-oriented design that discourages walking and biking
- Low tax productivity relative to land area consumed
- Underperforming assets as retail shifts to e-commerce

Converting these corridors to mixed-use development creates housing in locations already served by infrastructure, generates significantly more tax revenue per acre, and creates walkable, vibrant streetscapes from underperforming auto-oriented landscapes.


## Case Study Background

### Boston Metro MAPC: Strip Mall Retrofit Study

This analysis is informed by the Metropolitan Area Planning Council (MAPC) study of Greater Boston, which found that converting just 10% of the region's strip malls and commercial corridors to mixed-use development could yield 125,000 housing units.

**Key findings from the MAPC model:**

- Strip malls and commercial corridors represent massive underutilized land resources
- Mixed-use retrofit typically increases property tax revenue by 3-5x
- Ground-floor retail can be preserved while adding residential above
- Parking requirements often force inefficient land use; reducing minimums enables retrofit

The MAPC approach demonstrated that commercial retrofit represents one of the largest untapped housing opportunities in American cities, requiring no greenfield development or displacement of existing residents.


## Methodology

### Development Assumptions

The analysis applies standardized development assumptions to estimate the potential yield from commercial retrofit:

| Parameter | Value | Source |
|-----------|-------|--------|
| Development Type | 3-story mixed-use | Industry standard |
| Units per Acre | 25 | Moderate density assumption |
| Persons per Household | 2.3 | Census Bureau average |
| Potential Tax per Acre | $40,380 | Chico downtown median |

### Underutilization Criteria

Parcels are classified as underutilized if they meet either of the following thresholds:

| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| Building Coverage | < 30% | Less than one-third of the parcel is occupied by buildings |
| Improvement Ratio | < 0.5 | Land value exceeds improvement value by 2:1 or more |

These thresholds identify parcels where buildings occupy a small portion of the land (with the rest devoted to parking or vacant) and where the land itself is worth more than the structures on it—a classic indicator of underutilization.

### Priority Classification

Underutilized parcels are classified into retrofit priority tiers based on building coverage:

| Priority | Building Coverage | Characteristics |
|----------|-------------------|-----------------|
| High | 0 - 10% | Mostly parking or vacant; easiest to retrofit |
| Medium | 10 - 20% | Small buildings with extensive parking |
| Low | 20 - 30% | Moderate building coverage; may require phased retrofit |

### Calculations

**Potential housing units:**
```
Units = Parcel Acres × 25 units/acre
```

**Potential residents:**
```
Residents = Units × 2.3 persons/household
```

**Potential tax revenue:**
```
Potential Tax = Parcel Acres × $40,380/acre
```

**Tax increase:**
```
Tax Increase = Potential Tax - Current Tax
```


## Results Summary

### Aggregate Findings

| Metric | Value |
|--------|-------|
| Total Commercial Parcels | 958 |
| Underutilized Parcels | 784 |
| Commercial Acres | 727.2 |
| Underutilized Acres | 580.7 |
| Current Tax Revenue | $10,324,351 |
| Potential Tax Revenue | $23,448,004 |
| **Tax Increase Potential** | **$13,123,652** |
| Potential Housing Units | 14,230 |
| Potential Residents | 32,348 |

### Distribution by Priority

| Priority | Parcels | Acres | Potential Units | Tax Increase | Avg. Building Coverage |
|----------|---------|-------|-----------------|--------------|------------------------|
| High | 531 | 360.6 | 8,832 | $8,679,514 | 0.8% |
| Medium | 107 | 78.0 | 1,906 | $1,755,132 | 16.0% |
| Low | 146 | 142.0 | 3,492 | $2,689,006 | 24.7% |

High-priority parcels—those with minimal existing building coverage—represent the greatest opportunity and face the fewest barriers to retrofit.


## Adoption Scenarios

Not all underutilized commercial parcels will be retrofitted simultaneously. These scenarios model different adoption rates:

| Adoption Rate | Parcels | Acres | Housing Units | New Residents | Annual Tax Increase |
|---------------|---------|-------|---------------|---------------|---------------------|
| 10% | 78 | 58.1 | 1,423 | 3,234 | $1,312,365 |
| 25% | 196 | 145.2 | 3,557 | 8,087 | $3,280,913 |
| 50% | 392 | 290.3 | 7,115 | 16,174 | $6,561,826 |
| 100% | 784 | 580.7 | 14,230 | 32,348 | $13,123,652 |

A 25% adoption rate (196 parcels) would produce over 3,500 housing units and generate $3.3 million in additional annual property tax revenue.


## Data Sources

| Data Layer | Purpose | Source |
|------------|---------|--------|
| Parcels_Chico_CityLimits | Property boundaries, use codes, tax assessments | Butte County Assessor |
| Zoning_GP_Landuse | Zoning classifications | City of Chico |
| chico_buildings | Building footprints for coverage calculation | City of Chico GIS |

All geographic data uses the California State Plane Zone 2 coordinate system (EPSG:2226).


## Methodological Notes

### Building Coverage Calculation

Building coverage is calculated as:

```
Coverage = (Building Footprint Area / Parcel Area) × 100
```

Building footprints are derived from the City of Chico GIS building layer. Where multiple buildings exist on a parcel, total footprint area is summed.

### Improvement Ratio Calculation

Improvement ratio is calculated as:

```
Improvement Ratio = Improvement Value / Land Value
```

Values are from the Butte County Assessor database. A ratio below 1.0 indicates the land is worth more than the buildings on it; a ratio below 0.5 indicates land value is at least double improvement value.

### Assumptions and Limitations

1. **Development Density**: The 25 units/acre assumption represents moderate-density development. Actual densities will vary based on zoning, market conditions, and specific parcel characteristics.

2. **Tax Revenue Projections**: The $40,380/acre potential tax figure is based on downtown Chico median values. Actual tax revenue will depend on development type, assessed value, and Proposition 13 base-year values.

3. **Existing Tenants**: This analysis does not account for existing commercial tenants or lease obligations. Retrofit projects typically require coordination with or relocation of existing businesses.

4. **Building Condition**: Some buildings with low improvement ratios may have significant improvements that are simply old and thus depreciated in assessed value. Site visits are recommended for priority parcels.

5. **Parking Requirements**: Existing parking may be required by lease agreements or perceived market demand. Parking reform may be necessary to enable retrofit at the densities modeled.


## Interpreting the Map

### High-Priority Retrofit Sites

The most promising retrofit opportunities typically exhibit:

- **Minimal building coverage**: Large parking areas with small buildings
- **Low improvement ratio**: Land value dominates total assessed value
- **Major corridor location**: Visibility and accessibility for ground-floor retail
- **Adequate parcel size**: Economies of scale for mixed-use development

### Corridor Patterns

Chico's commercial corridors show distinct patterns:

- **East Avenue/Mangrove**: Large-format retail with extensive surface parking
- **Esplanade**: Mix of older strip development and newer auto-oriented uses
- **20th Street/Forest Avenue**: Auto-oriented commercial with retrofit potential

### Advocacy Applications

This data supports arguments for:

- Eliminating or reducing parking minimums for mixed-use development
- Creating commercial corridor overlay zones permitting increased density
- Establishing tax increment financing districts for corridor improvements
- Prioritizing transit and pedestrian infrastructure along retrofit corridors


## About This Analysis

This analysis was prepared by Smart Growth Advocates of Chico using Python geospatial analysis tools (GeoPandas, Shapely) applied to official City of Chico and Butte County GIS data. The methodology is designed to be transparent, reproducible, and grounded in established smart growth planning principles.

For questions about the methodology or to request the underlying data and code, contact Smart Growth Advocates of Chico.

*Analysis Date: December 2025*
