import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import geometry_mask
from scipy import ndimage

classification_raster = "data/processed/suitability_class.tif"
study_area = "data/processed/vectors/study_area.gpkg"

gdf = gpd.read_file(study_area)

with rasterio.open(classification_raster) as src:
    classification = src.read(1)

    study_mask = geometry_mask(
        gdf.geometry,
        transform=src.transform,
        invert=True,
        out_shape=classification.shape,
    )

# High + Moderate suitability only.
candidate = (
    (classification == 4) | (classification == 3)
) & study_mask

# 8-neighbor connectivity.
structure = np.ones((3, 3), dtype=np.uint8)

labeled, num_areas = ndimage.label(
    candidate,
    structure=structure,
)

area_counts = np.bincount(labeled.ravel())[1:]

# 100 m × 100 m = 0.01 km².
area_km2 = area_counts * 0.01

total_candidate_area = area_km2.sum()

# Apply the 5 km² candidate-area threshold.
threshold = 5.0
selected = area_km2 >= threshold

selected_count = selected.sum()
selected_area = area_km2[selected].sum()

print("Candidate-area analysis — High + Moderate")
print("------------------------------------------")
print(f"Candidate cells:       {candidate.sum():,}")
print(f"Candidate area:        {total_candidate_area:,.2f} km²")
print(f"Contiguous areas:       {num_areas:,}")
print()
print(f"Minimum area threshold: {threshold:.1f} km²")
print(f"Candidate areas >= 5 km²: {selected_count:,}")
print(f"Area retained:          {selected_area:,.2f} km²")
print(
    f"Percent of candidate area retained: "
    f"{selected_area / total_candidate_area * 100:.2f}%"
)
print()

print("Largest candidate areas")
print("-----------------------")

sorted_areas = np.sort(area_km2)[::-1]

for i, area in enumerate(sorted_areas[:20], start=1):
    print(f"{i:2}. {area:,.2f} km²")