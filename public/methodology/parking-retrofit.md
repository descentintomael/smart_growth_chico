# Parking Lot Retrofit Analysis

## Overview

The Parking Lot Retrofit Analysis identifies surface parking lots within the City of Chico that could be redeveloped into productive mixed-use buildings. Surface parking represents one of the least productive land uses in urban areas—generating minimal tax revenue while consuming valuable land in prime locations.

This analysis examines 142 parking lot parcels totaling 96.6 acres. These parcels currently generate $2.4 million in annual property tax revenue but could generate $3.9 million if redeveloped—representing $1.5 million in forgone annual tax revenue that Chico loses by maintaining surface parking in urban locations.

### Why Parking Retrofit Matters

Surface parking lots are ubiquitous in American cities, yet they represent a profound waste of urban land:

- **Fiscal drain**: Parking lots generate a fraction of the tax revenue of buildings
- **Heat islands**: Asphalt surfaces increase urban temperatures and stormwater runoff
- **Pedestrian barriers**: Large parking areas break up the urban fabric and discourage walking
- **Opportunity cost**: Prime urban land devoted to car storage instead of housing and commerce

Every acre of surface parking in a downtown or commercial corridor is an acre that could house residents, support businesses, and generate tax revenue. Parking retrofit transforms these fiscal liabilities into community assets.


## Case Study Background

### Hartford, Connecticut: Parking Reform Analysis

This analysis is informed by parking reform research from Hartford, Connecticut, which quantified the fiscal impact of surface parking in urban areas.

**Key findings from the Hartford model:**

- **$50 million per year** in property tax revenue forgone by maintaining surface parking in downtown Hartford
- Surface parking generates approximately $6,000-10,000 per acre in property taxes
- Mixed-use development on the same land generates $40,000-80,000 per acre
- Parking minimums in zoning codes create and perpetuate this fiscal drain

The Hartford analysis demonstrated that surface parking isn't just an aesthetic problem—it's a significant drain on municipal finances, forcing higher tax rates on productive properties to compensate for the revenue lost to parking lots.


## Methodology

### Development Assumptions

The analysis applies standardized development assumptions to estimate the potential yield from parking lot redevelopment:

| Parameter | Value | Source |
|-----------|-------|--------|
| Development Type | 3-story mixed-use | Industry standard |
| Units per Acre | 25 | Moderate density assumption |
| Persons per Household | 2.3 | Census Bureau average |
| Potential Tax per Acre | $40,380 | Chico downtown median |

### Parcel Identification

Parking lots are identified through:

1. **Use codes**: Assessor codes indicating parking use
2. **Building coverage**: Parcels with zero or minimal building footprint
3. **Improvement ratio**: Parcels where land value significantly exceeds improvement value
4. **Manual review**: Verification through aerial imagery

### Calculations

**Current tax per acre:**
```
Current Tax/Acre = Annual Property Tax / Parcel Acres
```

**Potential tax revenue:**
```
Potential Tax = Parcel Acres × $40,380/acre
```

**Forgone tax revenue:**
```
Forgone Tax = Potential Tax - Current Tax
```

Note: Parcels where current tax exceeds potential tax have negative forgone revenue, indicating they are already performing above the mixed-use benchmark (possibly due to high-value improvements not reflected in building footprint).

**Potential housing units:**
```
Units = Parcel Acres × 25 units/acre
```

**Potential residents:**
```
Residents = Units × 2.3 persons/household
```


## Results Summary

### Aggregate Findings

| Metric | Value |
|--------|-------|
| Parking Lot Parcels | 142 |
| Total Parking Acres | 96.6 |
| Current Tax Revenue | $2,367,010 |
| Potential Tax Revenue | $3,899,521 |
| **Forgone Tax Revenue** | **$1,532,511** |
| Potential Housing Units | 2,357 |
| Potential Residents | 5,353 |

### Key Metrics

| Metric | Value |
|--------|-------|
| Average Current Tax/Acre | $24,511 |
| Average Forgone Tax/Acre | $15,869 |
| Tax Ratio (Potential/Current) | 1.6x |

On average, parking lots generate 60% less tax revenue per acre than the mixed-use development potential of the same land.


## Parcel Analysis

### High-Opportunity Parcels

The analysis identifies parcels where the gap between current and potential tax revenue is greatest. These parcels typically exhibit:

- Large acreage (economies of scale for redevelopment)
- Low current tax per acre (minimal improvements)
- Prime location (downtown, commercial corridors)
- Compatible zoning (allowing mixed-use development)

### Already-Productive Parcels

Some parcels coded as parking show negative forgone revenue—their current taxes exceed the mixed-use potential estimate. These may include:

- Parking structures (improvements not visible in aerial view)
- High-value parcels with Proposition 13 reassessment from recent sales
- Parcels with additional uses beyond parking


## Data Sources

| Data Layer | Purpose | Source |
|------------|---------|--------|
| Parcels_Chico_CityLimits | Property boundaries, use codes, tax assessments | Butte County Assessor |
| Zoning_GP_Landuse | Zoning classifications | City of Chico |
| chico_buildings | Building footprints for verification | City of Chico GIS |

All geographic data uses the California State Plane Zone 2 coordinate system (EPSG:2226).


## Methodological Notes

### Assumptions and Limitations

1. **Development Potential**: The $40,380/acre benchmark assumes 3-story mixed-use development is feasible. Actual development potential depends on zoning, market conditions, and parcel characteristics.

2. **Parking Demand**: This analysis does not address where displaced parking demand would go. Parking management strategies, shared parking, and reduced parking requirements may be necessary to enable retrofit.

3. **Ownership Patterns**: Many parking lots serve adjacent buildings under common ownership. Redevelopment may require coordination across multiple parcels or reconfiguration of remaining parking.

4. **Existing Uses**: Some parking lots serve critical functions (hospital parking, event venues) where replacement parking would be required before retrofit.

5. **Assessment Timing**: Proposition 13 limits reassessment to change of ownership or new construction. Actual tax increases from redevelopment depend on assessment timing and base-year values.

### Tax Revenue Calculation

Annual property tax is derived from the Tax_Amnt field in the assessor database. This represents the total tax bill including all direct levies and voter-approved measures. The comparison assumes similar tax treatment for new development, though actual rates may vary.

### Forgone Revenue Concept

"Forgone revenue" represents the difference between what the city receives from surface parking and what it could receive from productive development. This is not a loss in the accounting sense but an opportunity cost—the value of choosing parking over alternative uses.


## Interpreting the Map

### High-Priority Retrofit Sites

The most promising parking retrofit opportunities typically exhibit:

- **Large contiguous parcels**: Economies of scale for development
- **Low current tax productivity**: Greatest potential improvement
- **Central location**: Walkable areas where parking is most costly
- **Compatible zoning**: Mixed-use or commercial designations

### Downtown Concentration

Downtown Chico contains numerous surface parking lots that represent significant retrofit potential. These sites are:

- Walking distance from employment and entertainment
- Served by existing infrastructure
- Appropriate for higher-density development
- Critical for creating a cohesive urban fabric

### Advocacy Applications

This data supports arguments for:

- Eliminating parking minimums in downtown and commercial zones
- Creating parking maximum regulations for new development
- Establishing parking benefit districts that price on-street parking
- Offering incentives for parking lot redevelopment (density bonuses, fee waivers)
- Implementing land value taxation that would increase costs of holding unimproved land


## Relationship to Other Analyses

The Parking Retrofit Analysis complements other Smart Growth Advocates layers:

- **Commercial Retrofit**: Identifies commercial parcels with excessive parking
- **Vacant Infill**: Identifies parcels with no improvements (parking lots may be subset)
- **Under-Utilization**: Parking lots score high on improvement-ratio underutilization
- **Smart Growth Index**: Parking lots typically score low on fiscal productivity


## About This Analysis

This analysis was prepared by Smart Growth Advocates of Chico using Python geospatial analysis tools (GeoPandas, Shapely) applied to official City of Chico and Butte County GIS data. The methodology is designed to be transparent, reproducible, and grounded in established smart growth planning principles.

For questions about the methodology or to request the underlying data and code, contact Smart Growth Advocates of Chico.

*Analysis Date: December 2025*
