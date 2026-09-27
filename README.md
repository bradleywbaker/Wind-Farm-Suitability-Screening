# Wind Farm Suitability Screening

A GIS-based screening project examining potential areas for utility-scale wind development in Tennessee.

The goal was to build a transparent, reproducible workflow using wind resource, terrain, land cover, environmental constraints, and infrastructure data. The analysis applies hard constraints first, then grades the remaining areas and combines the results into an overall suitability score.

The workflow was designed so that the approach could be extended to a larger regional study area, but the analysis presented here focuses on Tennessee.

## Study Area

The analysis covers the state of Tennessee.

The statewide study area provides a useful test case for bringing together wind resource, terrain, environmental constraints, land cover, and infrastructure accessibility within a consistent GIS workflow.

## How the Analysis Works

The workflow is organized into three main stages:

### 1. Prepare the Data

The source datasets come from several different formats, projections, and spatial scales. The first stage standardizes them to a common 100 m analysis grid and prepares the layers needed for the screening.

This includes:

* Standardizing wind, elevation, and land-cover rasters
* Calculating slope from elevation
* Preparing environmental constraint layers
* Identifying qualifying transmission lines
* Identifying roads suitable for access screening
* Calculating distance-to-transmission and distance-to-road rasters

### 2. Apply Constraints and Build the Suitability Model

The analysis first applies hard constraints. Areas are excluded if they fall below the minimum wind resource, exceed the maximum slope, or intersect specified environmental, land-cover, military, or airport constraints.

Areas that remain are then graded using five criteria:

| Criterion           | What is measured                    |
| ------------------- | ----------------------------------- |
| Wind resource       | 100 m wind speed                    |
| Slope               | Percent slope                       |
| Land cover          | NLCD 2025 land-cover class          |
| Transmission access | Distance to ≥100 kV transmission    |
| Road access         | Distance to qualifying road network |

Each criterion is converted to a common 1–5 scale and combined using an equal-weight mean.

The final suitability classes are:

* Very Low: < 3.50
* Low: 3.50–< 4.00
* Moderate: 4.00–< 4.50
* High: ≥ 4.50

### 3. Identify Candidate Areas

The final step looks beyond individual raster cells and asks where there are contiguous areas large enough to warrant further consideration.

Moderate and High suitability cells are grouped using 8-neighbor connectivity. Contiguous areas smaller than 5 km² are removed, and the remaining areas are summarized as candidate regions.
