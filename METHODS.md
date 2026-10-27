# Wind Farm Suitability Screening — Methods

## Overview

This project uses a GIS-based screening workflow to identify areas in Tennessee that may warrant further investigation for utility-scale wind development.

The workflow combines wind resource, terrain, land cover, environmental constraints, and infrastructure access. Hard constraints are applied first to remove areas that do not meet minimum screening requirements. The remaining areas are then evaluated using five suitability criteria and combined into an overall suitability score.

The workflow is designed to be transparent and reproducible and can be extended to additional geographic areas and datasets.

## Study Area

The analysis covers the state of Tennessee.

All input datasets were standardized to a common 100-meter analysis grid so that each location could be evaluated consistently across the study area.

## Analysis Framework

The workflow consists of three production stages:

1. Prepare and standardize input data
2. Apply hard constraints and build the suitability model
3. Identify contiguous candidate areas

### Stage 1 — Data Preparation

Source datasets were processed into standardized raster and vector inputs suitable for analysis.

This stage included:

- Standardizing raster datasets to the common analysis grid
- Calculating slope from elevation
- Preparing environmental constraint layers
- Selecting qualifying transmission lines
- Selecting qualifying roads
- Calculating distance-to-transmission rasters
- Calculating distance-to-road rasters

### Stage 2 — Hard Constraints and Suitability Scoring

Hard constraints were applied before suitability scoring.

Areas were excluded when they failed the minimum wind-resource requirement, exceeded the maximum slope threshold, or intersected specified environmental, land-cover, military, wetland, water, or airport constraints.

Only areas that passed all hard constraints were assigned suitability grades.

### Stage 3 — Candidate Areas

Moderate and High suitability cells were grouped using 8-neighbor connectivity.

Contiguous regions smaller than 5 km² were removed. The remaining regions were retained as candidate areas for further investigation.

## Hard Constraints

### Wind Resource

Areas with wind speeds below 6.5 m/s were excluded.

### Slope

Areas with slope greater than 20 percent were excluded.

### Land Cover

The following NLCD 2025 classes were excluded:

- 11 — Open Water
- 21 — Developed, Open Space
- 22 — Developed, Low Intensity
- 23 — Developed, Medium Intensity
- 24 — Developed, High Intensity
- 90 — Woody Wetlands
- 95 — Emergent Herbaceous Wetlands

### Protected Areas

Protected areas with GAP Status Codes 1, 2, or 3 were excluded.

### Military Areas

Areas within Department of Defense facility footprints were excluded.

No additional buffer was applied.

### Wetlands and Water

Mapped wetland and water features were excluded from consideration.

### Airports

FAA airport facility locations were excluded.

No additional buffer was applied.

## Suitability Criteria

Areas that passed the hard constraints were evaluated using five criteria:

| Criterion | Measure |
|---|---|
| Wind resource | 100 m wind speed |
| Slope | Percent slope |
| Land cover | NLCD 2025 class |
| Transmission access | Distance to qualifying transmission |
| Road access | Distance to qualifying roads |

Each criterion was converted to a common 1–5 scale before calculating the overall suitability score.

## Wind Resource Grading

| Wind Speed | Grade | Description |
|---|---:|---|
| 6.5–<7.0 m/s | 2 | Moderate |
| 7.0–<7.5 m/s | 3 | Good |
| ≥7.5 m/s | 4 | High |

## Slope Grading

| Slope | Grade | Description |
|---|---:|---|
| ≤5% | 4 | High |
| >5–10% | 3 | Good |
| >10–15% | 2 | Moderate |
| >15–20% | 1 | Low |

## Land Cover Grading

| NLCD Class | Grade | Description |
|---|---:|---|
| 31, 71, 81, 82 | 4 | High |
| 52 | 2 | Moderate |
| 41, 42, 43 | 1 | Low |

Excluded land-cover classes remain excluded from the analysis.

## Transmission Access Grading

Only transmission lines with a voltage of at least 100 kV were included.

| Distance | Grade | Description |
|---|---:|---|
| 0–2 km | 5 | High |
| >2–5 km | 4 | Good |
| >5–10 km | 3 | Moderate |
| >10–15 km | 2 | Low |
| >15 km | 1 | Very Low |

## Road Access Grading

Road access was evaluated using qualifying roads from the Tennessee NG911 road network. Roads with CFCC codes beginning with A1, A2, A3, A4, or A5 were included.

| Distance | Grade | Description |
|---|---:|---|
| 0–1 km | 5 | High |
| >1–5 km | 4 | Good |
| >5–10 km | 3 | Moderate |
| >10–20 km | 2 | Low |
| >20 km | 1 | Very Low |

## Suitability Score

The five criteria were standardized to a common 1–5 scale and combined using an equal-weight mean.

The standardized scores were:

- Wind resource: grades 2–4 converted to 3–5
- Slope: grades 1–4 converted to 2–5
- Land cover: grades 1, 2, and 4 converted to 2, 3, and 5
- Transmission access: grades 1–5 retained
- Road access: grades 1–5 retained

Only cells with valid scores for all five criteria received an overall suitability score.

The overall score was calculated as:

Suitability Score = (Wind + Slope + Land Cover + Transmission + Roads) / 5

## Final Suitability Classes

| Score | Class |
|---|---|
| <3.50 | Very Low |
| 3.50–<4.00 | Low |
| 4.00–<4.50 | Moderate |
| ≥4.50 | High |

## Candidate Area Analysis

Moderate and High suitability cells were selected for candidate-area analysis.

Cells were grouped using 8-neighbor connectivity to identify contiguous regions. Regions smaller than 5 km² were removed.

The remaining regions were converted to polygons and summarized as candidate areas.

## Production Workflow

The production workflow is implemented through three scripts:

```text
scripts/
├── 01_prepare_data.py
├── 02_build_suitability_model.py
└── 03_create_candidates.py
```

The scripts use project configuration files and reusable geospatial utilities to support a consistent, reproducible analysis workflow.

## Results Summary

The statewide analysis evaluated 19,390,085 cells on the 100-meter analysis grid.

After application of all hard constraints, 1,060,115 cells remained eligible for suitability scoring.

Suitability scores ranged from 3.00 to 5.00, with a mean of 4.13 and a median of 4.20.

Moderate and High suitability areas covered 7,699.68 km² before candidate-area filtering.

The candidate-area analysis identified 4,550 contiguous Moderate and High suitability regions. After applying the 5 km² minimum area threshold, 42 candidate areas remained, covering 1,735.51 km².

## Limitations and Assumptions

This analysis is a regional screening exercise rather than a site-selection or development feasibility study.

The results depend on the datasets, thresholds, classifications, and assumptions used in the model. Site-specific factors such as property ownership, detailed environmental review, aviation requirements, noise setbacks, transmission capacity, engineering feasibility, construction access, and project economics were not evaluated.

Candidate areas therefore represent locations for further investigation rather than proposed development sites.
