import rasterio
import numpy as np

input_raster = "data/processed/dem/slope_percent_100m.tif"
output_raster = "data/processed/dem/slope_constraint.tif"

with rasterio.open(input_raster) as src:
    slope = src.read(1)
    profile = src.profile.copy()

eligible = np.isfinite(slope) & (slope <= 20)

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(eligible.astype("uint8"), 1)

print("Slope constraint created")
print("------------------------")
print("Threshold:   <= 20%")
print(f"Eligible:    {eligible.sum():,} pixels")
print(f"Excluded:    {(~eligible).sum():,} pixels")