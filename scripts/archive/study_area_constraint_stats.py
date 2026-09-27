import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import geometry_mask

constraint = "data/processed/hard_constraints.tif"
study = "data/processed/vectors/study_area.gpkg"

gdf = gpd.read_file(study)

with rasterio.open(constraint) as src:
    data = src.read(1)

    study_mask = geometry_mask(
        gdf.geometry,
        transform=src.transform,
        invert=True,
        out_shape=data.shape,
    )

eligible = (data == 1) & study_mask
excluded = (data == 0) & study_mask

eligible_pixels = eligible.sum()
excluded_pixels = excluded.sum()
total_pixels = eligible_pixels + excluded_pixels

pixel_area_km2 = 100 * 100 / 1_000_000
eligible_area = eligible_pixels * pixel_area_km2
excluded_area = excluded_pixels * pixel_area_km2
total_area = total_pixels * pixel_area_km2

eligible_pct = eligible_pixels / total_pixels * 100
excluded_pct = excluded_pixels / total_pixels * 100

print("Hard-constraint results — study area")
print("-------------------------------------")
print(f"Total pixels:    {total_pixels:,}")
print(f"Eligible pixels: {eligible_pixels:,}")
print(f"Excluded pixels: {excluded_pixels:,}")
print()
print(f"Eligible area:   {eligible_area:,.2f} km²")
print(f"Excluded area:   {excluded_area:,.2f} km²")
print(f"Total area:      {total_area:,.2f} km²")
print()
print(f"Eligible:        {eligible_pct:.2f}%")
print(f"Excluded:        {excluded_pct:.2f}%")