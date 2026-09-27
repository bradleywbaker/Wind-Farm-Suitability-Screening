import rasterio
import numpy as np

input_raster = "data/processed/land_cover_100m.tif"
output_raster = "data/processed/land_cover_constraint.tif"

excluded_classes = {
    11,  # Open Water
    21,  # Developed, Open Space
    22,  # Developed, Low Intensity
    23,  # Developed, Medium Intensity
    24,  # Developed, High Intensity
    90,  # Woody Wetlands
    95,  # Emergent Herbaceous Wetlands
}

with rasterio.open(input_raster) as src:
    land_cover = src.read(1)
    profile = src.profile.copy()

excluded = np.isin(land_cover, list(excluded_classes))
eligible = ~excluded

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(eligible.astype("uint8"), 1)

print("Land-cover constraint created")
print("-----------------------------")
print("Excluded classes: 11, 21-24, 90, 95")
print(f"Eligible:    {eligible.sum():,} pixels")
print(f"Excluded:    {excluded.sum():,} pixels")