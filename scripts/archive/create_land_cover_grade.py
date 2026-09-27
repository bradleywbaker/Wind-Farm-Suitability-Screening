import rasterio
import numpy as np

land_cover_raster = "data/processed/land_cover_100m.tif"
hard_constraints = "data/processed/hard_constraints.tif"
output_raster = "data/processed/land_cover_grade.tif"

with rasterio.open(land_cover_raster) as src:
    land_cover = src.read(1)
    profile = src.profile.copy()

with rasterio.open(hard_constraints) as src:
    eligible = src.read(1) == 1

grade = np.zeros(land_cover.shape, dtype="uint8")

valid = eligible & np.isfinite(land_cover)

# High suitability
grade[valid & np.isin(land_cover, [31, 71, 81, 82])] = 4

# Moderate suitability
grade[valid & (land_cover == 52)] = 2

# Low suitability
grade[valid & np.isin(land_cover, [41, 42, 43])] = 1

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(grade, 1)

print("Land-cover grading created")
print("--------------------------")
print("1 = Low")
print("2 = Moderate")
print("4 = High")
print()
print(f"Low:      {(grade == 1).sum():,}")
print(f"Moderate: {(grade == 2).sum():,}")
print(f"High:     {(grade == 4).sum():,}")
print(f"Ungraded: {(grade == 0).sum():,}")
print(f"Total:    {(grade > 0).sum():,}")