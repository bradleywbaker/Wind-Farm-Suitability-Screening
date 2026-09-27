import rasterio
import numpy as np

wind_raster = "data/processed/wind/wind_speed_100m.tif"
hard_constraints = "data/processed/hard_constraints.tif"
output_raster = "data/processed/wind/wind_grade.tif"

with rasterio.open(wind_raster) as src:
    wind = src.read(1)
    profile = src.profile.copy()

with rasterio.open(hard_constraints) as src:
    eligible = src.read(1) == 1

grade = np.zeros(wind.shape, dtype="uint8")

valid = eligible & np.isfinite(wind)

grade[valid & (wind >= 6.5) & (wind < 7.0)] = 2
grade[valid & (wind >= 7.0) & (wind < 7.5)] = 3
grade[valid & (wind >= 7.5)] = 4

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(grade, 1)

print("Wind grading created")
print("--------------------")
print("2 = Moderate")
print("3 = Good")
print("4 = High")
print()
print(f"Moderate: {(grade == 2).sum():,}")
print(f"Good:     {(grade == 3).sum():,}")
print(f"High:     {(grade == 4).sum():,}")
print(f"Total:    {(grade > 0).sum():,}")