import rasterio
import numpy as np

input_raster = "data/processed/wind/wind_speed_100m.tif"
output_raster = "data/processed/wind/wind_constraint.tif"

with rasterio.open(input_raster) as src:
    wind = src.read(1)
    profile = src.profile.copy()

eligible = np.isfinite(wind) & (wind >= 6.5)

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(eligible.astype("uint8"), 1)

print("Wind constraint created")
print("-----------------------")
print(f"Threshold:   6.5 m/s")
print(f"Eligible:    {eligible.sum():,} pixels")
print(f"Excluded:    {(~eligible).sum():,} pixels")