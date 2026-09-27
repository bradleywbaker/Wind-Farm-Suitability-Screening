import rasterio
import numpy as np

inputs = {
    "wind": "data/processed/wind/wind_constraint.tif",
    "slope": "data/processed/dem/slope_constraint.tif",
    "protected": "data/processed/protected_areas_constraint.tif",
    "military": "data/processed/military_constraint.tif",
    "wetlands": "data/processed/wetlands_constraint.tif",
    "land_cover": "data/processed/land_cover_constraint.tif",
    "airports": "data/processed/airports_constraint.tif",
}

output_raster = "data/processed/hard_constraints.tif"

arrays = {}

for name, path in inputs.items():
    with rasterio.open(path) as src:
        arrays[name] = src.read(1)
        profile = src.profile.copy()

# A cell is eligible only if it passes every hard constraint.
eligible = np.ones_like(next(iter(arrays.values())), dtype=bool)

for array in arrays.values():
    eligible &= array == 1

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(eligible.astype("uint8"), 1)

print("Hard constraints combined")
print("--------------------------")

for name, array in arrays.items():
    print(f"{name:12} excluded: {(array == 0).sum():,}")

print()
print(f"Eligible:    {eligible.sum():,} pixels")
print(f"Excluded:    {(~eligible).sum():,} pixels")