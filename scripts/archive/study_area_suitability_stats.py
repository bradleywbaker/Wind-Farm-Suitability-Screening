import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import geometry_mask

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

valid = (score > 0) & study_mask
values = score[valid]

print("Suitability score — study area")
print("------------------------------")
print(f"Valid cells: {len(values):,}")
print()
print(f"Minimum:    {values.min():.2f}")
print(f"Maximum:    {values.max():.2f}")
print(f"Mean:       {values.mean():.2f}")
print(f"Median:     {np.median(values):.2f}")
print(f"P10:        {np.percentile(values, 10):.2f}")
print(f"P25:        {np.percentile(values, 25):.2f}")
print(f"P75:        {np.percentile(values, 75):.2f}")
print(f"P90:        {np.percentile(values, 90):.2f}")
print(f"P95:        {np.percentile(values, 95):.2f}")