import rasterio
import numpy as np

distance_raster = "data/processed/transmission_distance_km.tif"
hard_constraints = "data/processed/hard_constraints.tif"
output_raster = "data/processed/transmission_grade.tif"

with rasterio.open(distance_raster) as src:
    distance = src.read(1)
    profile = src.profile.copy()

with rasterio.open(hard_constraints) as src:
    eligible = src.read(1) == 1

grade = np.zeros(distance.shape, dtype="uint8")

valid = eligible & np.isfinite(distance)

# High: 0–2 km
grade[valid & (distance <= 2)] = 5

# Good: >2–5 km
grade[valid & (distance > 2) & (distance <= 5)] = 4

# Moderate: >5–10 km
grade[valid & (distance > 5) & (distance <= 10)] = 3

# Low: >10–15 km
grade[valid & (distance > 10) & (distance <= 15)] = 2

# Very Low: >15 km
grade[valid & (distance > 15)] = 1

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(grade, 1)

print("Transmission grading created")
print("-----------------------------")
print("1 = Very Low")
print("2 = Low")
print("3 = Moderate")
print("4 = Good")
print("5 = High")
print()
print(f"Very Low: {(grade == 1).sum():,}")
print(f"Low:      {(grade == 2).sum():,}")
print(f"Moderate: {(grade == 3).sum():,}")
print(f"Good:     {(grade == 4).sum():,}")
print(f"High:     {(grade == 5).sum():,}")
print(f"Ungraded: {(grade == 0).sum():,}")
print(f"Total:    {(grade > 0).sum():,}")