import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import geometry_mask
from scipy import ndimage

score_raster = "data/processed/suitability_score.tif"
study_area = "data/processed/vectors/study_area.gpkg"

gdf = gpd.read_file(study_area)

with rasterio.open(score_raster) as src:
    score = src.read(1)

    study_mask = geometry_mask(
        gdf.geometry,
        transform=src.transform,
        invert=True,
        out_shape=score.shape,
    )

eligible = (score > 0) & study_mask

# 8-neighbor connectivity
structure = np.ones((3, 3), dtype=np.uint8)

labeled, num_areas = ndimage.label(
    eligible,
    structure=structure,
)

area_counts = np.bincount(labeled.ravel())[1:]

# Each cell is 100 m × 100 m = 0.01 km².
area_km2 = area_counts * 0.01

total_area = area_km2.sum()

print("Contiguous-area threshold analysis")
print("----------------------------------")
print(f"Eligible cells:   {eligible.sum():,}")
print(f"Eligible area:    {total_area:,.2f} km²")
print(f"Contiguous areas: {num_areas:,}")
print()

print(
    f"{'Threshold':>12} "
    f"{'Patches':>10} "
    f"{'Area km²':>12} "
    f"{'% Area':>10} "
    f"{'% Patches':>12}"
)

print("-" * 60)

for threshold in [0.5, 1, 2, 5, 10, 20]:
    selected = area_km2 >= threshold

    patch_count = selected.sum()
    retained_area = area_km2[selected].sum()

    area_pct = retained_area / total_area * 100
    patch_pct = patch_count / num_areas * 100

    print(
        f"{threshold:>10.2f} km² "
        f"{patch_count:>10,} "
        f"{retained_area:>12,.2f} "
        f"{area_pct:>9.2f}% "
        f"{patch_pct:>11.2f}%"
    )