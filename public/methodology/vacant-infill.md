# Vacant Parcel Infill Analysis

## Overview

The Vacant Parcel Infill Analysis identifies vacant and underutilized parcels within the City of Chico that represent opportunities for infill development. By focusing development on these existing vacant sites, the city can accommodate growth while leveraging existing infrastructure, reducing sprawl, and maximizing tax revenue from land already served by public services.

This analysis examines 362 vacant parcels, of which 267 are classified as buildable based on size and zoning criteria. Together, these buildable parcels represent 459 acres of development potential capable of accommodating over 11,000 housing units.

### Why Infill Development Matters

Vacant parcels within existing neighborhoods represent a significant missed opportunity for cities. These sites:

- Already have access to roads, water, sewer, and other utilities
- Generate minimal tax revenue despite requiring city services
- Often become nuisance properties requiring code enforcement attention
- Represent gaps in the urban fabric that reduce walkability and neighborhood cohesion

Converting vacant lots to productive use generates tax revenue, provides housing, and strengthens neighborhoods without extending infrastructure to greenfield sites.


## Case Study Background

### South Bend, Indiana: Scattered-Site Infill Model

This analysis is informed by the South Bend, Indiana scattered-site infill program, which demonstrated that coordinated infill development on vacant lots can achieve significant cost savings compared to greenfield development.

**Key findings from the South Bend model:**

- **75% cost savings** on infrastructure compared to greenfield development
- Scattered-site infill leverages existing water, sewer, and road infrastructure
- Neighborhood stabilization benefits from filling vacant lots
- Incremental development approach allows for market-responsive growth

The South Bend approach showed that even small, scattered vacant parcels can be developed efficiently when aggregated across a program, making infill financially competitive with edge development despite smaller parcel sizes.


## Methodology

### Development Assumptions

The analysis applies standardized development assumptions to estimate the potential yield from vacant parcels:

| Parameter | Value | Source |
|-----------|-------|--------|
| Development Type | 3-story mixed-use | Industry standard |
| Units per Acre | 25 | Moderate density assumption |
| Persons per Household | 2.3 | Census Bureau average |
| Potential Tax per Acre | $40,380 | Chico downtown median |
| Minimum Parcel Size | 0.1 acres | Practical development threshold |

### Parcel Selection Criteria

**Included parcels:**
- Parcels with vacant use codes in the assessor database
- Parcels within Chico city limits
- Parcels of at least 0.1 acres (4,356 square feet)
- Parcels in zones permitting residential or mixed-use development

**Excluded parcels:**
- Parcels smaller than 0.1 acres (impractical for development)
- Parcels in agricultural or open space zones designated for preservation
- Parcels with environmental constraints (wetlands, flood zones)
- Parcels already under active development applications

### Size Categories

Parcels are classified into three size categories to aid in prioritization:

| Category | Size Range | Count | Total Acres | Characteristics |
|----------|------------|-------|-------------|-----------------|
| Small | < 0.25 acres | 105 | 17.5 | Single-family or small multifamily; may require lot aggregation |
| Medium | 0.25 - 1 acre | 84 | 41.1 | Ideal for small apartment or townhouse developments |
| Large | > 1 acre | 78 | 400.5 | Suitable for larger multifamily or mixed-use projects |

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
| Total Vacant Parcels Analyzed | 362 |
| Buildable Parcels | 267 |
| Excluded Parcels | 82 |
| Total Buildable Acres | 459.0 |
| Current Tax Revenue | $2,731,169 |
| Potential Tax Revenue | $18,535,399 |
| **Tax Increase Potential** | **$15,804,230** |
| Potential Housing Units | 11,375 |
| Potential Residents | 26,036 |

### Distribution by Size

| Size Category | Parcels | Acres | Potential Units | Tax Increase |
|---------------|---------|-------|-----------------|--------------|
| Small (< 0.25 ac) | 105 | 17.5 | 396 | $392,025 |
| Medium (0.25-1 ac) | 84 | 41.1 | 995 | $1,065,022 |
| Large (> 1 ac) | 78 | 400.5 | 9,984 | $14,347,182 |

Large parcels represent the greatest opportunity for housing production, while small and medium parcels may be priorities for neighborhood stabilization.


## Adoption Scenarios

Not all vacant parcels will be developed simultaneously. These scenarios model different adoption rates:

| Adoption Rate | Parcels | Acres | Housing Units | New Residents | Annual Tax Increase |
|---------------|---------|-------|---------------|---------------|---------------------|
| 10% | 26 | 45.9 | 1,137 | 2,603 | $1,580,423 |
| 25% | 66 | 114.8 | 2,843 | 6,509 | $3,951,057 |
| 50% | 133 | 229.5 | 5,687 | 13,018 | $7,902,115 |
| 100% | 267 | 459.0 | 11,375 | 26,036 | $15,804,230 |

A 25% adoption rate (66 parcels) would produce nearly 2,900 housing units and generate nearly $4 million in additional annual property tax revenue.


## Data Sources

| Data Layer | Purpose | Source |
|------------|---------|--------|
| Parcels_Chico_CityLimits | Property boundaries, use codes, tax assessments | Butte County Assessor |
| Zoning_GP_Landuse | Zoning classifications | City of Chico |
| Building Footprints | Verify vacant status | City of Chico GIS |

All geographic data uses the California State Plane Zone 2 coordinate system (EPSG:2226).


## Methodological Notes

### Assumptions and Limitations

1. **Development Density**: The 25 units/acre assumption represents moderate-density development. Actual densities will vary based on zoning, market conditions, and specific parcel characteristics.

2. **Tax Revenue Projections**: The $40,380/acre potential tax figure is based on downtown Chico median values. Actual tax revenue will depend on development type, assessed value, and Proposition 13 base-year values.

3. **Development Feasibility**: Not all vacant parcels are equally developable. Some may have title issues, environmental constraints, or market conditions that affect viability. This analysis identifies potential; actual development requires site-specific due diligence.

4. **Infrastructure Capacity**: While infill sites generally have infrastructure access, some areas may require capacity upgrades for water, sewer, or traffic.

5. **Parcel Aggregation**: Some small parcels may only be developable if aggregated with adjacent parcels. This analysis treats each parcel individually.

### Use Code Identification

Vacant parcels are identified using assessor use codes that indicate no improvements or minimal improvements. Parcels coded as parking lots or with minimal structures may also represent infill opportunities but are analyzed separately in the Parking Retrofit layer.


## Interpreting the Map

### High-Priority Infill Sites

The most promising infill opportunities typically exhibit:

- **Larger parcel size**: Economies of scale for development
- **Central location**: Access to services, transit, and employment
- **Compatible zoning**: Residential or mixed-use designations
- **Infrastructure proximity**: Direct utility connections available

### Neighborhood Stabilization Sites

Smaller vacant parcels in established neighborhoods may be priorities for:

- Community land trusts or affordable housing programs
- Accessory dwelling unit (ADU) development
- Small-scale missing middle housing

### Advocacy Applications

This data supports arguments for:

- Prioritizing infill over greenfield development
- Reducing minimum lot sizes to enable small-lot development
- Creating infill incentive programs (fee waivers, expedited review)
- Addressing land banking and speculation through vacancy taxes


## About This Analysis

This analysis was prepared by Smart Growth Advocates of Chico using Python geospatial analysis tools (GeoPandas, Shapely) applied to official City of Chico and Butte County GIS data. The methodology is designed to be transparent, reproducible, and grounded in established smart growth planning principles.

For questions about the methodology or to request the underlying data and code, contact Smart Growth Advocates of Chico.

*Analysis Date: December 2025*
