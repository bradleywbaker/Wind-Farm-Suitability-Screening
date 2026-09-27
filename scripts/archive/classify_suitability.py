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

# Proposed composite-score classes
high = values >= 4.50
moderate = (values >= 4.00) & (values < 4.50)
low = (values >= 3.50) & (values < 4.00)
very_low = values < 3.50

total = len(values)

print("Suitability classification — study area")
print("----------------------------------------")
print("Proposed score classes:")
print("4.50–5.00  = High")
print("4.00–<4.50 = Moderate")
print("3.50–<4.00 = Low")
print("<3.50       = Very Low")
print()

for name, mask in [
    ("High", high),
    ("Moderate", moderate),
    ("Low", low),
    ("Very Low", very_low),
]:
    count = mask.sum()
    percent = count / total * 100

    print(
        f"{name:10} {count:>8,} cells "
        f"({percent:6.2f}%)"
    )