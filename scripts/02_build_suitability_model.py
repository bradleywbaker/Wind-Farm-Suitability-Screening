import sys
from pathlib import Path

# Add project root to Python path so src/ imports work when
# this script is run directly from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize


PROCESSED = Path("data/processed")
REFERENCE_GRID = PROCESSED / "reference_grid.tif"
VECTORS = PROCESSED / "vectors"


def write_raster(output_raster, array, profile, dtype):
    """Write a single-band raster using the supplied profile."""
    output_raster.parent.mkdir(parents=True, exist_ok=True)

    profile = profile.copy()
    profile.update(
        dtype=dtype,
        count=1,
        nodata=0,
        compress="lzw",
    )

    with rasterio.open(output_raster, "w", **profile) as dst:
        dst.write(array.astype(dtype), 1)


def create_wind_constraint():
    print("\n=== Wind constraint ===")

    input_raster = PROCESSED / "wind" / "wind_speed_100m.tif"
    output_raster = PROCESSED / "wind" / "wind_constraint.tif"

    with rasterio.open(input_raster) as src:
        wind = src.read(1)
        profile = src.profile.copy()

    eligible = np.isfinite(wind) & (wind >= 6.5)

    write_raster(
        output_raster,
        eligible.astype("uint8"),
        profile,
        "uint8",
    )

    print("Threshold:   6.5 m/s")
    print(f"Eligible:    {eligible.sum():,} pixels")
    print(f"Excluded:    {(~eligible).sum():,} pixels")


def create_slope_constraint():
    print("\n=== Slope constraint ===")

    input_raster = PROCESSED / "dem" / "slope_percent_100m.tif"
    output_raster = PROCESSED / "dem" / "slope_constraint.tif"

    with rasterio.open(input_raster) as src:
        slope = src.read(1)
        profile = src.profile.copy()

    eligible = np.isfinite(slope) & (slope <= 20)

    write_raster(
        output_raster,
        eligible.astype("uint8"),
        profile,
        "uint8",
    )

    print("Threshold:   <= 20%")
    print(f"Eligible:    {eligible.sum():,} pixels")
    print(f"Excluded:    {(~eligible).sum():,} pixels")


def create_land_cover_constraint():
    print("\n=== Land-cover constraint ===")

    input_raster = PROCESSED / "land_cover_100m.tif"
    output_raster = PROCESSED / "land_cover_constraint.tif"

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

    write_raster(
        output_raster,
        eligible.astype("uint8"),
        profile,
        "uint8",
    )

    print("Excluded classes: 11, 21-24, 90, 95")
    print(f"Eligible:    {eligible.sum():,} pixels")
    print(f"Excluded:    {excluded.sum():,} pixels")


def create_vector_constraint(
    input_vector,
    output_raster,
    description,
    filter_function=None,
):
    """Rasterize excluded vector features and create an eligibility raster."""

    with rasterio.open(REFERENCE_GRID) as ref:
        profile = ref.profile.copy()
        transform = ref.transform
        shape = (ref.height, ref.width)
        crs = ref.crs

    g = gpd.read_file(input_vector)

    if filter_function is not None:
        g = filter_function(g)

    g = g.to_crs(crs)

    arr = rasterize(
        (
            (geom, 1)
            for geom in g.geometry
            if geom is not None
        ),
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype="uint8",
    )

    eligible = arr == 0

    write_raster(
        output_raster,
        eligible.astype("uint8"),
        profile,
        "uint8",
    )

    print(f"Exclusion:   {description}")
    print(f"Features:    {len(g):,}")
    print(f"Eligible:    {eligible.sum():,} pixels")
    print(f"Excluded:    {(~eligible).sum():,} pixels")


def create_protected_constraint():
    print("\n=== Protected-area constraint ===")

    def qualifying(g):
        return g[g["GAP_Sts"].isin(["1", "2", "3"])].copy()

    create_vector_constraint(
        VECTORS / "protected_areas.gpkg",
        PROCESSED / "protected_areas_constraint.tif",
        "GAP 1-3",
        qualifying,
    )


def create_military_constraint():
    print("\n=== Military constraint ===")

    create_vector_constraint(
        VECTORS / "military.gpkg",
        PROCESSED / "military_constraint.tif",
        "DoD facility footprint",
    )

    print("Buffer:      None")


def create_wetlands_constraint():
    print("\n=== Wetlands constraint ===")

    create_vector_constraint(
        VECTORS / "wetlands.gpkg",
        PROCESSED / "wetlands_constraint.tif",
        "All mapped wetland/water features",
    )


def create_airport_constraint():
    print("\n=== Airport constraint ===")

    create_vector_constraint(
        VECTORS / "airports.gpkg",
        PROCESSED / "airports_constraint.tif",
        "FAA facility location",
    )

    print("Buffer:      None")


def combine_hard_constraints():
    print("\n=== Combining hard constraints ===")

    inputs = {
        "wind": PROCESSED / "wind" / "wind_constraint.tif",
        "slope": PROCESSED / "dem" / "slope_constraint.tif",
        "protected": PROCESSED / "protected_areas_constraint.tif",
        "military": PROCESSED / "military_constraint.tif",
        "wetlands": PROCESSED / "wetlands_constraint.tif",
        "land_cover": PROCESSED / "land_cover_constraint.tif",
        "airports": PROCESSED / "airports_constraint.tif",
    }

    arrays = {}
    profile = None

    for name, path in inputs.items():
        with rasterio.open(path) as src:
            arrays[name] = src.read(1)

            if profile is None:
                profile = src.profile.copy()

    # A cell is eligible only if it passes every hard constraint.
    eligible = np.ones_like(
        next(iter(arrays.values())),
        dtype=bool,
    )

    for array in arrays.values():
        eligible &= array == 1

    output_raster = PROCESSED / "hard_constraints.tif"

    write_raster(
        output_raster,
        eligible.astype("uint8"),
        profile,
        "uint8",
    )

    for name, array in arrays.items():
        print(f"{name:12} excluded: {(array == 0).sum():,}")

    print()
    print(f"Eligible:    {eligible.sum():,} pixels")
    print(f"Excluded:    {(~eligible).sum():,} pixels")


def create_wind_grade():
    print("\n=== Wind grading ===")

    wind_raster = PROCESSED / "wind" / "wind_speed_100m.tif"
    hard_constraints = PROCESSED / "hard_constraints.tif"
    output_raster = PROCESSED / "wind" / "wind_grade.tif"

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

    write_raster(output_raster, grade, profile, "uint8")

    print("2 = Moderate")
    print("3 = Good")
    print("4 = High")
    print()
    print(f"Moderate: {(grade == 2).sum():,}")
    print(f"Good:     {(grade == 3).sum():,}")
    print(f"High:     {(grade == 4).sum():,}")
    print(f"Total:    {(grade > 0).sum():,}")


def create_slope_grade():
    print("\n=== Slope grading ===")

    slope_raster = PROCESSED / "dem" / "slope_percent_100m.tif"
    hard_constraints = PROCESSED / "hard_constraints.tif"
    output_raster = PROCESSED / "dem" / "slope_grade.tif"

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

    write_raster(output_raster, grade, profile, "uint8")

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


def create_land_cover_grade():
    print("\n=== Land-cover grading ===")

    land_cover_raster = PROCESSED / "land_cover_100m.tif"
    hard_constraints = PROCESSED / "hard_constraints.tif"
    output_raster = PROCESSED / "land_cover_grade.tif"

    with rasterio.open(land_cover_raster) as src:
        land_cover = src.read(1)
        profile = src.profile.copy()

    with rasterio.open(hard_constraints) as src:
        eligible = src.read(1) == 1

    grade = np.zeros(land_cover.shape, dtype="uint8")
    valid = eligible & np.isfinite(land_cover)

    # High suitability
    grade[
        valid
        & np.isin(land_cover, [31, 71, 81, 82])
    ] = 4

    # Moderate suitability
    grade[valid & (land_cover == 52)] = 2

    # Low suitability
    grade[
        valid
        & np.isin(land_cover, [41, 42, 43])
    ] = 1

    write_raster(output_raster, grade, profile, "uint8")

    print("1 = Low")
    print("2 = Moderate")
    print("4 = High")
    print()
    print(f"Low:      {(grade == 1).sum():,}")
    print(f"Moderate: {(grade == 2).sum():,}")
    print(f"High:     {(grade == 4).sum():,}")
    print(f"Ungraded: {(grade == 0).sum():,}")
    print(f"Total:    {(grade > 0).sum():,}")


def create_transmission_grade():
    print("\n=== Transmission grading ===")

    distance_raster = PROCESSED / "transmission_distance_km.tif"
    hard_constraints = PROCESSED / "hard_constraints.tif"
    output_raster = PROCESSED / "transmission_grade.tif"

    with rasterio.open(distance_raster) as src:
        distance = src.read(1)
        profile = src.profile.copy()

    with rasterio.open(hard_constraints) as src:
        eligible = src.read(1) == 1

    grade = np.zeros(distance.shape, dtype="uint8")
    valid = eligible & np.isfinite(distance)

    # High: 0-2 km
    grade[valid & (distance <= 2)] = 5

    # Good: >2-5 km
    grade[valid & (distance > 2) & (distance <= 5)] = 4

    # Moderate: >5-10 km
    grade[valid & (distance > 5) & (distance <= 10)] = 3

    # Low: >10-15 km
    grade[valid & (distance > 10) & (distance <= 15)] = 2

    # Very Low: >15 km
    grade[valid & (distance > 15)] = 1

    write_raster(output_raster, grade, profile, "uint8")

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


def create_road_grade():
    print("\n=== Road grading ===")

    distance_raster = PROCESSED / "road_distance_km.tif"
    hard_constraints = PROCESSED / "hard_constraints.tif"
    output_raster = PROCESSED / "road_grade.tif"

    with rasterio.open(distance_raster) as src:
        distance = src.read(1)
        profile = src.profile.copy()

    with rasterio.open(hard_constraints) as src:
        eligible = src.read(1) == 1

    grade = np.zeros(distance.shape, dtype="uint8")
    valid = eligible & np.isfinite(distance)

    # High: 0-1 km
    grade[valid & (distance <= 1)] = 5

    # Good: >1-5 km
    grade[valid & (distance > 1) & (distance <= 5)] = 4

    # Moderate: >5-10 km
    grade[valid & (distance > 5) & (distance <= 10)] = 3

    # Low: >10-20 km
    grade[valid & (distance > 10) & (distance <= 20)] = 2

    # Very Low: >20 km
    grade[valid & (distance > 20)] = 1

    write_raster(output_raster, grade, profile, "uint8")

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


def calculate_suitability_score():
    print("\n=== Suitability scoring ===")

    inputs = {
        "wind": PROCESSED / "wind" / "wind_grade.tif",
        "slope": PROCESSED / "dem" / "slope_grade.tif",
        "land_cover": PROCESSED / "land_cover_grade.tif",
        "transmission": PROCESSED / "transmission_grade.tif",
        "roads": PROCESSED / "road_grade.tif",
    }

    output_raster = PROCESSED / "suitability_score.tif"

    arrays = {}
    profile = None

    for name, path in inputs.items():
        with rasterio.open(path) as src:
            arrays[name] = src.read(1)

            if profile is None:
                profile = src.profile.copy()

    # Convert all criteria to a common 1-5 scale.
    # 0 remains ungraded/excluded.

    wind = arrays["wind"].astype("float32")
    wind[wind == 2] = 3
    wind[wind == 3] = 4
    wind[wind == 4] = 5

    slope = arrays["slope"].astype("float32")
    slope[slope == 1] = 2
    slope[slope == 2] = 3
    slope[slope == 3] = 4
    slope[slope == 4] = 5

    land_cover = arrays["land_cover"].astype("float32")
    land_cover[land_cover == 1] = 2
    land_cover[land_cover == 2] = 3
    land_cover[land_cover == 4] = 5

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

    write_raster(
        output_raster,
        score,
        profile,
        "float32",
    )

    valid_scores = score[score > 0]

    print("Method: Equal-weight mean of five criteria")
    print("Scale: 1-5")
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


def create_suitability_class():
    print("\n=== Suitability classification ===")

    input_raster = PROCESSED / "suitability_score.tif"
    output_raster = PROCESSED / "suitability_class.tif"

    with rasterio.open(input_raster) as src:
        score = src.read(1)
        profile = src.profile.copy()

    classification = np.zeros(
        score.shape,
        dtype="uint8",
    )

    # Final suitability classes:
    # 1 = Very Low
    # 2 = Low
    # 3 = Moderate
    # 4 = High

    valid = score > 0

    classification[
        valid & (score < 3.50)
    ] = 1

    classification[
        valid
        & (score >= 3.50)
        & (score < 4.00)
    ] = 2

    classification[
        valid
        & (score >= 4.00)
        & (score < 4.50)
    ] = 3

    classification[
        valid & (score >= 4.50)
    ] = 4

    write_raster(
        output_raster,
        classification,
        profile,
        "uint8",
    )

    print("1 = Very Low")
    print("2 = Low")
    print("3 = Moderate")
    print("4 = High")
    print()
    print(f"Very Low:    {(classification == 1).sum():,}")
    print(f"Low:         {(classification == 2).sum():,}")
    print(f"Moderate:    {(classification == 3).sum():,}")
    print(f"High:        {(classification == 4).sum():,}")
    print(f"Unclassified: {(classification == 0).sum():,}")


def main():
    if not REFERENCE_GRID.exists():
        raise FileNotFoundError(
            f"Reference grid not found: {REFERENCE_GRID}"
        )

    print("Wind Farm Suitability Screening")
    print("================================")
    print("Stage 2: Build suitability model")

    PROCESSED.mkdir(
        parents=True,
        exist_ok=True,
    )

    create_wind_constraint()
    create_slope_constraint()
    create_land_cover_constraint()
    create_protected_constraint()
    create_military_constraint()
    create_wetlands_constraint()
    create_airport_constraint()

    combine_hard_constraints()

    create_wind_grade()
    create_slope_grade()
    create_land_cover_grade()
    create_transmission_grade()
    create_road_grade()

    calculate_suitability_score()
    create_suitability_class()

    print("\nStage 2 complete.")


if __name__ == "__main__":
    main()
