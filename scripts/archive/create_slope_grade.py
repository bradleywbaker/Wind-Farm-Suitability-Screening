import rasterio
import numpy as np

slope_raster = "data/processed/dem/slope_percent_100m.tif"
hard_constraints = "data/processed/hard_constraints.tif"
output_raster = "data/processed/dem/slope_grade.tif"

with rasterio.open(slope_raster) as src:
    slope = src.read(1)
    profile = src.profile.copy()

with rasterio.open(hard_constraints) as src:
    eligible = src.read(1) == 1

grade = np.zeros(slope.shape, dtype="uint8")

valid = eligible & np.isfinite(slope)

grade[valid & (slope <= 5)] = 4
grade[valid & (slope > 5) & (slope <= 10)] = 3
grade[valid & (slope > 10) & (slope <= 15)] = 2
grade[valid & (slope > 15) & (slope <= 20)] = 1

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(grade, 1)

print("Slope grading created")
print("---------------------")
print("1 = Low")
print("2 = Moderate")
print("3 = Good")
print("4 = High")
print()
print(f"Low:      {(grade == 1).sum():,}")
print(f"Moderate: {(grade == 2).sum():,}")
print(f"Good:     {(grade == 3).sum():,}")
print(f"High:     {(grade == 4).sum():,}")
print(f"Total:    {(grade > 0).sum():,}")