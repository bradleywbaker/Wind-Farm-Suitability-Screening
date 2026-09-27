import sys
from pathlib import Path

# Add project root to Python path so scripts can be
# run directly from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask, shapes
from scipy import ndimage
from shapely.geometry import shape


PROCESSED = Path("data/processed")
CLASSIFICATION_RASTER = PROCESSED / "suitability_class.tif"
SCORE_RASTER = PROCESSED / "suitability_score.tif"
STUDY_AREA = PROCESSED / "vectors/study_area.gpkg"
OUTPUT = PROCESSED / "candidate_areas.gpkg"

MIN_AREA_KM2 = 5.0
CELL_AREA_KM2 = 0.01


def main():
    print("Wind Farm Suitability Screening")
    print("================================")
    print("Stage 3: Create candidate areas")

    # --------------------------------------------------------
    # Read input data
    # --------------------------------------------------------

    print("\n=== Reading inputs ===")

    gdf = gpd.read_file(STUDY_AREA)

    with rasterio.open(CLASSIFICATION_RASTER) as src:
        classification = src.read(1)
        transform = src.transform
        crs = src.crs

    with rasterio.open(SCORE_RASTER) as src:
        score = src.read(1)

    study_mask = geometry_mask(
        gdf.geometry,
        transform=transform,
        invert=True,
        out_shape=classification.shape,
    )

    # --------------------------------------------------------
    # Identify High + Moderate candidate cells
    # --------------------------------------------------------

    print("\n=== Identifying candidate cells ===")

    candidate = (
        ((classification == 4) | (classification == 3))
        & study_mask
    )

    candidate_cells = int(candidate.sum())
    candidate_area_km2 = (
        candidate_cells * CELL_AREA_KM2
    )

    print("Included classes: 3 = Moderate, 4 = High")
    print(f"Candidate cells:   {candidate_cells:,}")
    print(f"Candidate area:    {candidate_area_km2:,.2f} km²")

    # --------------------------------------------------------
    # Identify contiguous candidate regions
    # --------------------------------------------------------

    print("\n=== Identifying contiguous regions ===")

    # 8-neighbor connectivity:
    # cells touching by an edge or corner are connected.
    structure = np.ones(
        (3, 3),
        dtype=np.uint8,
    )

    labeled, num_areas = ndimage.label(
        candidate,
        structure=structure,
    )

    area_counts = np.bincount(
        labeled.ravel()
    )[1:]

    area_km2 = (
        area_counts * CELL_AREA_KM2
    )

    print(f"Contiguous regions: {num_areas:,}")

    # --------------------------------------------------------
    # Apply minimum area threshold
    # --------------------------------------------------------

    print("\n=== Applying minimum-area threshold ===")

    selected_labels = (
        np.where(
            area_km2 >= MIN_AREA_KM2
        )[0] + 1
    )

    print(
        f"Minimum area:      "
        f"{MIN_AREA_KM2:.1f} km²"
    )
    print(
        f"Qualifying regions: "
        f"{len(selected_labels):,}"
    )

    if len(selected_labels) == 0:
        print("\nNo candidate areas meet the minimum threshold.")
        return

    selected_area = (
        area_km2[selected_labels - 1].sum()
    )

    print(
        f"Area retained:     "
        f"{selected_area:,.2f} km²"
    )

    print(
        f"Percent retained:  "
        f"{selected_area / candidate_area_km2 * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Calculate candidate attributes
    # --------------------------------------------------------

    print("\n=== Calculating candidate metrics ===")

    records = []

    for candidate_id, label_id in enumerate(
        selected_labels,
        start=1,
    ):
        mask = labeled == label_id

        cell_count = int(mask.sum())
        area_value = (
            cell_count * CELL_AREA_KM2
        )

        candidate_scores = score[mask]
        candidate_classes = classification[mask]

        high_cells = int(
            (candidate_classes == 4).sum()
        )
        moderate_cells = int(
            (candidate_classes == 3).sum()
        )

        high_pct = (
            high_cells / cell_count * 100
        )
        moderate_pct = (
            moderate_cells / cell_count * 100
        )

        records.append(
            {
                "label_id": int(label_id),
                "candidate_id": candidate_id,
                "area_km2": area_value,
                "mean_score": float(
                    candidate_scores.mean()
                ),
                "min_score": float(
                    candidate_scores.min()
                ),
                "max_score": float(
                    candidate_scores.max()
                ),
                "high_pct": high_pct,
                "moderate_pct": moderate_pct,
                "cell_count": cell_count,
            }
        )

    attributes = gpd.GeoDataFrame(records)

    # --------------------------------------------------------
    # Convert selected raster regions to polygons
    # --------------------------------------------------------

    print("\n=== Polygonizing candidate areas ===")

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

    # --------------------------------------------------------
    # Dissolve pieces belonging to each region
    # --------------------------------------------------------

    polygons = polygons.dissolve(
        by="label_id",
        as_index=False,
    )

    # --------------------------------------------------------
    # Join candidate attributes
    # --------------------------------------------------------

    polygons = polygons.merge(
        attributes,
        on="label_id",
        how="left",
    )

    polygons = polygons.drop(
        columns=["label_id"]
    )

    # Largest candidates first.
    polygons = polygons.sort_values(
        "area_km2",
        ascending=False,
    ).reset_index(drop=True)

    # Renumber after sorting.
    polygons["candidate_id"] = np.arange(
        1,
        len(polygons) + 1,
    )

    # --------------------------------------------------------
    # Write GeoPackage
    # --------------------------------------------------------

    print("\n=== Writing candidate areas ===")

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    polygons.to_file(
        OUTPUT,
        layer="candidate_areas",
        driver="GPKG",
    )

    # --------------------------------------------------------
    # Report results
    # --------------------------------------------------------

    print("\nCandidate areas created")
    print("-----------------------")
    print(f"Output:            {OUTPUT}")
    print(f"Candidate areas:   {len(polygons):,}")
    print(
        f"Largest:           "
        f"{polygons.area_km2.max():,.2f} km²"
    )
    print(
        f"Smallest:          "
        f"{polygons.area_km2.min():,.2f} km²"
    )
    print(
        f"Total candidate:   "
        f"{polygons.area_km2.sum():,.2f} km²"
    )

    print("\nLargest candidate areas")
    print("-----------------------")

    for _, row in polygons.head(10).iterrows():
        print(
            f"{int(row.candidate_id):2}. "
            f"{row.area_km2:,.2f} km² "
            f"(mean score: {row.mean_score:.2f})"
        )

    print("\nStage 3 complete.")


if __name__ == "__main__":
    main()
