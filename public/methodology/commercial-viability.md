# Commercial Viability Analysis

## Overview

The Commercial Viability Analysis evaluates the potential for neighborhood-serving retail and services at City of Chico opportunity sites. Using established retail gravity models, this analysis determines what types of businesses could be supported based on the population within walking distance of each site—both current population and projected population under upzoning scenarios.

This analysis examines 15 city-designated opportunity sites and calculates supportable business counts for 27 different retail and service categories, from coffee shops and hair salons to grocery stores and fitness centers.

### Why Commercial Viability Matters

Walkable neighborhoods require more than just housing. Residents need convenient access to daily goods and services—coffee, groceries, dry cleaning, restaurants, healthcare. When these amenities are within walking distance, residents drive less, neighborhoods become more vibrant, and local businesses thrive.

However, neighborhood retail only succeeds when sufficient population exists within the catchment area. This analysis identifies which opportunity sites have (or could have) the population density to support various business types, enabling informed decisions about land use and development patterns.


## Methodology Framework

### Retail Gravity Model

This analysis uses a retail gravity model based on research from the Urban Land Institute (ULI) and International Council of Shopping Centers (ICSC). The fundamental principle:

> **Each business type requires a minimum population within its catchment area to be economically viable.**

The model calculates supportable business counts using a population divisor:

```
Supportable Businesses = floor(Catchment Population / Population Threshold)
```

For example, if a site has 5,000 people within a quarter mile and coffee shops require 2,500 people each, the site can support 2 coffee shops.

### Catchment Distances

Three standard catchment distances are used, corresponding to different shopping trip types:

| Catchment | Distance (feet) | Distance (miles) | Trip Type |
|-----------|-----------------|------------------|-----------|
| Quarter Mile | 1,320 | 0.25 | Daily walking trip (~5 minutes) |
| Half Mile | 2,640 | 0.50 | Frequent walking trip (~10 minutes) |
| One Mile | 5,280 | 1.00 | Occasional walking or quick driving trip |

Different business types are assigned to different catchment distances based on trip frequency:

- **Quarter mile**: Daily needs (coffee, convenience stores, hair salons)
- **Half mile**: Weekly needs (groceries, pharmacies, restaurants)
- **One mile**: Occasional needs (fitness centers, hardware stores)


## Business Categories and Thresholds

### Food & Beverage

| Business Type | Population Threshold | Catchment | Notes |
|---------------|---------------------|-----------|-------|
| Coffee Shop | 2,500 | Quarter mile | High frequency, walkable |
| Bakery | 3,000 | Quarter mile | Daily purchase potential |
| Small Restaurant | 4,000 | Quarter mile | Neighborhood dining |
| Ice Cream / Dessert | 4,000 | Quarter mile | Impulse purchase |
| Pizza / Delivery | 5,000 | Half mile | Delivery extends catchment |
| Quick Service Restaurant | 5,500 | Half mile | Lunch traffic |
| Full Service Restaurant | 8,000 | One mile | Destination dining |
| Brewpub / Winery | 12,000 | One mile | Entertainment destination |

### Retail

| Business Type | Population Threshold | Catchment | Notes |
|---------------|---------------------|-----------|-------|
| Convenience Store | 3,000 | Quarter mile | Daily essentials |
| Liquor Store | 5,000 | Half mile | Regulated retail |
| Neighborhood Grocery | 6,500 | Half mile | Weekly shopping |
| Florist | 8,000 | Half mile | Occasional purchase |
| Medium Grocery | 12,500 | One mile | Full-service grocery |
| Pet Store | 15,000 | One mile | Specialty retail |
| Hardware Store | 20,000 | One mile | Project-based shopping |

### Health

| Business Type | Population Threshold | Catchment | Notes |
|---------------|---------------------|-----------|-------|
| Dental Office | 5,000 | Half mile | Regular appointments |
| Pharmacy | 7,500 | Half mile | Prescription pickup |
| Urgent Care | 10,000 | Half mile | Emergency services |

### Services

| Business Type | Population Threshold | Catchment | Notes |
|---------------|---------------------|-----------|-------|
| Hair Salon / Barber | 2,000 | Quarter mile | Regular service |
| Nail Salon | 3,500 | Quarter mile | Personal care |
| Dry Cleaner | 4,500 | Quarter mile | Drop-off convenience |
| Daycare Center | 6,000 | Half mile | Working families |
| Bank Branch | 8,000 | Half mile | Financial services |
| Auto Service | 10,000 | One mile | Car-dependent |
| Yoga / Pilates Studio | 10,000 | One mile | Fitness destination |
| Tutoring / Learning Center | 12,000 | One mile | Education services |
| Fitness Center | 15,000 | One mile | Membership-based |


## Calculation Methodology

### Population Estimation

For each opportunity site, population is calculated within each catchment distance:

1. **Create buffer zones** at quarter-mile, half-mile, and one-mile radii from each site
2. **Identify parcels** that intersect each buffer zone
3. **Calculate housing units** from assessor data and building footprints
4. **Apply persons-per-household factor** (2.3) to estimate population

```
Catchment Population = Housing Units in Buffer × 2.3
```

### Current vs. Upzone Scenarios

The analysis calculates commercial viability under two scenarios:

1. **Current population**: Based on existing housing units
2. **Post-upzone population**: Based on housing units after implementing the Upzone Scenario analysis

This shows how increased density from upzoning could enable new neighborhood-serving businesses that aren't viable today.

### Supportable Business Calculation

For each business type at each site:

```
Supportable Count = floor(Catchment Population / Population Threshold)
```

A site with 6,000 people in the quarter-mile catchment could support:
- 3 hair salons (6,000 / 2,000 = 3)
- 2 coffee shops (6,000 / 2,500 = 2)
- 2 bakeries (6,000 / 3,000 = 2)
- 1 small restaurant (6,000 / 4,000 = 1)


## Data Sources

| Data Layer | Purpose | Source |
|------------|---------|--------|
| OpportunitySites | Site boundaries for analysis | City of Chico |
| Parcels_Chico_CityLimits | Housing unit counts | Butte County Assessor |
| chico_buildings | Building footprints for unit estimation | City of Chico GIS |
| Upzone Scenario data | Projected units under upzoning | Smart Growth Advocates analysis |

All geographic data uses the California State Plane Zone 2 coordinate system (EPSG:2226).


## Methodological Notes

### Threshold Sources

Population thresholds are derived from:

- Urban Land Institute (ULI) retail development guidelines
- International Council of Shopping Centers (ICSC) research
- Industry rule-of-thumb standards for various retail categories

These thresholds represent typical viability benchmarks; actual performance varies based on competition, site characteristics, and operator quality.

### Assumptions and Limitations

1. **Population Estimation**: Housing unit counts from assessor data may not reflect actual occupancy. Some units may be vacant, and some households may be larger or smaller than the 2.3 average.

2. **Competition**: The model does not account for existing businesses. A site that can "support" 2 coffee shops may already have 3 coffee shops nearby, indicating saturation rather than opportunity.

3. **Income and Demographics**: The model uses raw population counts. Higher-income populations may support more businesses at lower population thresholds; lower-income populations may require higher thresholds.

4. **Daytime Population**: The model focuses on residential population. Sites near employment centers may have significant daytime population that increases commercial viability.

5. **Site Characteristics**: Visibility, access, parking, and other site-specific factors affect commercial success beyond population catchment.

### Floor Function

The floor function (rounding down) is used for supportable business counts:

```
floor(4,999 / 2,500) = 1, not 2
```

This conservative approach ensures that calculated business counts represent fully supported establishments rather than marginal viability.


## Interpreting the Results

### High-Viability Sites

Sites with strong commercial viability typically exhibit:

- **High catchment population**: More people within walking distance
- **Diverse supportable uses**: Multiple business categories viable
- **Improvement under upzoning**: Significant new businesses enabled by density increases

### Threshold Sites

Some sites fall just below thresholds for key business types. These sites may benefit from:

- Targeted infill development to increase catchment population
- Upzoning to enable additional housing
- Shared-use arrangements with adjacent sites

### Advocacy Applications

This data supports arguments for:

- Permitting neighborhood retail in residential zones
- Requiring ground-floor retail in mixed-use developments at viable sites
- Prioritizing density increases near sites that are close to retail thresholds
- Creating neighborhood commercial nodes through zoning overlay districts


## About This Analysis

This analysis was prepared by Smart Growth Advocates of Chico using Python geospatial analysis tools (GeoPandas, Shapely) applied to official City of Chico and Butte County GIS data. The methodology is designed to be transparent, reproducible, and grounded in established retail planning principles.

For questions about the methodology or to request the underlying data and code, contact Smart Growth Advocates of Chico.

*Analysis Date: December 2025*
