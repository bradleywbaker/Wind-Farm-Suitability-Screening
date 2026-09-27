import rasterio
import numpy as np

input_raster = "data/processed/suitability_score.tif"
output_raster = "data/processed/suitability_class.tif"

with rasterio.open(input_raster) as src:
    score = src.read(1)
    profile = src.profile.copy()

classification = np.zeros(score.shape, dtype="uint8")

# Final suitability classes
# 1 = Very Low
# 2 = Low
# 3 = Moderate
# 4 = High

valid = score > 0

classification[valid & (score < 3.50)] = 1
classification[valid & (score >= 3.50) & (score < 4.00)] = 2
classification[valid & (score >= 4.00) & (score < 4.50)] = 3
classification[valid & (score >= 4.50)] = 4

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(classification, 1)

print("Suitability classification created")
print("-----------------------------------")
print("1 = Very Low")
print("2 = Low")
print("3 = Moderate")
print("4 = High")
print()
print(f"Very Low: {(classification == 1).sum():,}")
print(f"Low:      {(classification == 2).sum():,}")
print(f"Moderate: {(classification == 3).sum():,}")
print(f"High:     {(classification == 4).sum():,}")
print(f"Unclassified: {(classification == 0).sum():,}")