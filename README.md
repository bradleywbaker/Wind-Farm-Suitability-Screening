# Wind Farm Suitability Screening

A GIS-based screening project examining potential areas for utility-scale wind development in Tennessee.

The goal was to build a transparent, reproducible workflow using wind resource, terrain, land cover, environmental constraints, and infrastructure data. The analysis applies hard constraints first, then grades the remaining areas and combines the results into an overall suitability score.

The workflow was designed so that the approach could be extended to a larger regional study area, but the analysis presented here focuses on Tennessee.

## Study Area

The analysis covers the state of Tennessee.

The statewide study area provides a useful test case for bringing together wind resource, terrain, environmental constraints, land cover, and infrastructure accessibility within a consistent GIS workflow.

## How the Analysis Works

The workflow is organized into three main stages.

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

The final step looks beyond individual raster cells and identifies larger contiguous areas that may warrant further consideration.

Moderate and High suitability cells are grouped using 8-neighbor connectivity. Contiguous areas smaller than 5 km² are removed, and the remaining areas are summarized as candidate areas.

## Results

After applying all hard constraints, 1,060,115 cells (about 10,601 km², roughly 10% of Tennessee's land area) remained eligible for suitability scoring.

The resulting suitability scores ranged from 3.00 to 5.00, with a mean of 4.13 and a median of 4.20.

Moderate and High suitability areas covered 7,699.68 km² before the candidate-area filter was applied.

The candidate-area analysis identified 4,550 contiguous Moderate and High suitability regions. After applying the minimum 5 km² area threshold, 42 candidate areas remained, covering 1,735.51 km².

## Reproducible Workflow

The production workflow is organized into three scripts:

```text
scripts/
├── 01_prepare_data.py
├── 02_build_suitability_model.py
└── 03_create_candidates.py
```

The scripts are supported by reusable geospatial utilities in src/geo_tools/ and project criteria and grid configuration files in config/.

## Repository Structure

```
Wind-Farm-Suitability-Screening/
├── Wind_Farm_Suitability/   # ArcGIS Pro project
├── config/                   # Analysis criteria and grid configuration
├── data/                    # Data directories and project inputs
├── figures/                 # Final project figures
├── scripts/                 # Production analysis scripts
├── src/geo_tools/           # Reusable geospatial utilities
├── .gitignore
├── environment.yml          # Python environment
├── METHODS.md               # Detailed methodology
└── README.md
```

## Technical Documentation

The detailed methodology documents the datasets, screening thresholds, suitability criteria, scoring approach, candidate-area analysis, assumptions, and reproducibility considerations.

Technical Methods: See METHODS.md

## StoryMap

The interactive StoryMap presents the project results, maps, workflow, discussion, and limitations in a visual format.

[View the interactive StoryMap](https://storymaps.arcgis.com/stories/dd9c5ce1ab26404f9a0e4291397680bc)

## Limitations

This project is a regional screening analysis, not a site-selection or development feasibility study.

The results do not account for several site-specific considerations, including:

- Property ownership and parcel availability
- Detailed aviation review
- Noise requirements and setbacks
- Detailed environmental review
- Transmission capacity or interconnection feasibility
- Detailed road and construction access
- Turbine layout and engineering considerations
- Construction and operating costs
- Project economics

Candidate areas should therefore be treated as locations for further investigation rather than proposed wind development sites.

## Tools

The project uses:

- Esri ArcGIS Pro
- Python
- Rasterio
- GeoPandas
- NumPy
- Pandas
- PyYAML
- Jupyter/Python environment tools
- Git and GitHub

## Project Purpose

This project was developed as a portfolio example of applying GIS, geospatial data processing, and reproducible analytical workflows to a regional planning and environmental screening problem.

The workflow emphasizes transparent criteria, explicit constraints, reproducible processing, and clear communication of results.
