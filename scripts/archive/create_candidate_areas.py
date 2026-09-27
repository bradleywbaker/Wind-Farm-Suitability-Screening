
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import geometry_mask, shapes
from scipy import ndimage
from shapely.geometry import shape

classification_raster = "data/processed/suitability_class.tif"
score_raster = "data/processed/suitability_score.tif"
study_area = "data/processed/vectors/study_area.gpkg"
output = "data/processed/candidate_areas.gpkg"

# ------------------------------------------------------------
# Read input data
# ------------------------------------------------------------

gdf = gpd.read_file(study_area)

with rasterio.open(classification_raster) as src:
    classification = src.read(1)
    transform = src.transform
    crs = src.crs

with rasterio.open(score_raster) as src:
    score = src.read(1)

study_mask = geometry_mask(
    gdf.geometry,
    transform=transform,
    invert=True,
    out_shape=classification.shape,
)

# ------------------------------------------------------------
# Identify High + Moderate candidate cells
# ------------------------------------------------------------

candidate = (
    ((classification == 4) | (classification == 3))
    & study_mask
)

# 8-neighbor connectivity:
# cells touching by an edge or corner are considered connected.
structure = np.ones((3, 3), dtype=np.uint8)

labeled, num_areas = ndimage.label(
    candidate,
    structure=structure,
)

# ------------------------------------------------------------
# Calculate connected-area sizes
# ------------------------------------------------------------

area_counts = np.bincount(labeled.ravel())[1:]

# Each cell is 100 m × 100 m = 0.01 km².
area_km2 = area_counts * 0.01

threshold = 5.0

selected_labels = (
    np.where(area_km2 >= threshold)[0] + 1
)

# ------------------------------------------------------------
# Calculate attributes for each selected candidate
# ------------------------------------------------------------

records = []

for candidate_id, label_id in enumerate(
    selected_labels,
    start=1,
):

    mask = labeled == label_id

    cell_count = mask.sum()
    area_km2_value = cell_count * 0.01

    candidate_scores = score[mask]
    candidate_classes = classification[mask]

    high_cells = (candidate_classes == 4).sum()
    moderate_cells = (candidate_classes == 3).sum()

    high_pct = high_cells / cell_count * 100
    moderate_pct = moderate_cells / cell_count * 100

    mean_score = candidate_scores.mean()
    min_score = candidate_scores.min()
    max_score = candidate_scores.max()

    records.append(
        {
            "label_id": int(label_id),
            "candidate_id": candidate_id,
            "area_km2": area_km2_value,
            "mean_score": mean_score,
            "min_score": min_score,
            "max_score": max_score,
            "high_pct": high_pct,
            "moderate_pct": moderate_pct,
            "cell_count": cell_count,
        }
    )

attributes = gpd.GeoDataFrame(records)

# ------------------------------------------------------------
# Convert connected raster regions to polygons
# ------------------------------------------------------------

polygon_records = []

for label_id in selected_labels:

    mask = labeled == label_id

    for geom, value in shapes(
        mask.astype("uint8"),
        mask=mask,
        transform=transform,
    ):

        polygon_records.append(
            {
                "label_id": int(label_id),
                "geometry": shape(geom),
            }
        )

polygons = gpd.GeoDataFrame(
    polygon_records,
    crs=crs,
)

# ------------------------------------------------------------
# Dissolve polygon pieces belonging to the same
# connected raster region.
# ------------------------------------------------------------

polygons = polygons.dissolve(
    by="label_id",
    as_index=False,
)

# ------------------------------------------------------------
# Join candidate attributes
# ------------------------------------------------------------

polygons = polygons.merge(
    attributes,
    on="label_id",
    how="left",
)

# Remove the raster-region label after joining.
polygons = polygons.drop(
    columns=["label_id"]
)

# Sort largest candidate areas first.
polygons = polygons.sort_values(
    "area_km2",
    ascending=False,
).reset_index(drop=True)

# Re-number candidates after sorting.
polygons["candidate_id"] = np.arange(
    1,
    len(polygons) + 1,
)

# ------------------------------------------------------------
# Write GeoPackage
# ------------------------------------------------------------

polygons.to_file(
    output,
    layer="candidate_areas",
    driver="GPKG",
)

# ------------------------------------------------------------
# Report results
# ------------------------------------------------------------

print("Candidate areas created")
print("-----------------------")
print(f"Threshold:       {threshold:.1f} km²")
print(f"Candidate areas: {len(polygons):,}")
print()
print("Area statistics")
print("----------------")
print(
    f"Largest:         "
    f"{polygons.area_km2.max():,.2f} km²"
)
print(
    f"Smallest:        "
    f"{polygons.area_km2.min():,.2f} km²"
)
print(
    f"Total area:      "
    f"{polygons.area_km2.sum():,.2f} km²"
)
print()

