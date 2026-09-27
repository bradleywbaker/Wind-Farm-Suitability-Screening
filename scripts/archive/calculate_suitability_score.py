import rasterio
import numpy as np

inputs = {
    "wind": "data/processed/wind/wind_grade.tif",
    "slope": "data/processed/dem/slope_grade.tif",
    "land_cover": "data/processed/land_cover_grade.tif",
    "transmission": "data/processed/transmission_grade.tif",
    "roads": "data/processed/road_grade.tif",
}

output_raster = "data/processed/suitability_score.tif"

arrays = {}
profile = None

for name, path in inputs.items():
    with rasterio.open(path) as src:
        arrays[name] = src.read(1)
        if profile is None:
            profile = src.profile.copy()

# Convert all criteria to a common 1–5 scale.
# 0 remains ungraded/excluded.

wind = arrays["wind"].astype("float32")
wind[(wind == 2)] = 3
wind[(wind == 3)] = 4
wind[(wind == 4)] = 5

slope = arrays["slope"].astype("float32")
slope[(slope == 1)] = 2
slope[(slope == 2)] = 3
slope[(slope == 3)] = 4
slope[(slope == 4)] = 5

land_cover = arrays["land_cover"].astype("float32")
land_cover[(land_cover == 1)] = 2
land_cover[(land_cover == 2)] = 3
land_cover[(land_cover == 4)] = 5

transmission = arrays["transmission"].astype("float32")
roads = arrays["roads"].astype("float32")

# Only cells with a valid grade for every criterion receive a score.
valid = (
    (wind > 0)
    & (slope > 0)
    & (land_cover > 0)
    & (transmission > 0)
    & (roads > 0)
)

score = np.zeros(wind.shape, dtype="float32")

score[valid] = (
    wind[valid]
    + slope[valid]
    + land_cover[valid]
    + transmission[valid]
    + roads[valid]
) / 5.0

profile.update(
    dtype="float32",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(score, 1)

valid_scores = score[score > 0]

print("Suitability score created")
print("-------------------------")
print("Method: Equal-weight mean of five criteria")
print("Scale: 1–5")
print()
print(f"Valid cells: {len(valid_scores):,}")
print(f"Minimum:    {valid_scores.min():.2f}")
print(f"Maximum:    {valid_scores.max():.2f}")
print(f"Mean:       {valid_scores.mean():.2f}")
print(f"Median:     {np.median(valid_scores):.2f}")
print(f"P10:        {np.percentile(valid_scores, 10):.2f}")
print(f"P25:        {np.percentile(valid_scores, 25):.2f}")
print(f"P75:        {np.percentile(valid_scores, 75):.2f}")
print(f"P90:        {np.percentile(valid_scores, 90):.2f}")