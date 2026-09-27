import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import geometry_mask

dist = "data/processed/road_distance_km.tif"
study = "data/processed/vectors/study_area.gpkg"

s = gpd.read_file(study)

with rasterio.open(dist) as src:
    a = src.read(1)
    mask = geometry_mask(
        s.geometry,
        transform=src.transform,
        invert=True,
        out_shape=a.shape,
    )

v = a[mask & np.isfinite(a)]

print("Road distance statistics — study area")
print("---------------------------------------")
print(f"Valid pixels: {len(v)}")
print(f"Min: {v.min():.2f} km")
print(f"Max: {v.max():.2f} km")
print(f"P50: {np.percentile(v, 50):.2f} km")
print(f"P75: {np.percentile(v, 75):.2f} km")
print(f"P90: {np.percentile(v, 90):.2f} km")
print(f"P95: {np.percentile(v, 95):.2f} km")