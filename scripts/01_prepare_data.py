import sys
from pathlib import Path

# Add project root to Python path so src/ imports work when
# this script is run directly from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt

from src.geo_tools.raster import process_raster
from src.geo_tools.terrain import calculate_slope
from src.geo_tools.vector import process_vector


RAW = Path("data/raw")
PROCESSED = Path("data/processed")
REFERENCE_GRID = PROCESSED / "reference_grid.tif"
VECTORS = PROCESSED / "vectors"


def prepare_rasters():
    print("\n=== Raster preparation ===")

    process_raster(
        RAW / "land_cover" /
        "Annual_NLCD_LndCov_2025_CU_C1V2" /
        "Annual_NLCD_LndCov_2025_CU_C1V2.tif",
        PROCESSED / "land_cover_100m.tif",
        REFERENCE_GRID,
        "nearest",
    )

    process_raster(
        PROCESSED / "dem" / "dem_mosaic.tif",
        PROCESSED / "dem" / "dem_100m.tif",
        REFERENCE_GRID,
        "bilinear",
    )

    calculate_slope(
        PROCESSED / "dem" / "dem_100m.tif",
        PROCESSED / "dem" / "slope_percent_100m.tif",
    )

    process_raster(
        RAW / "wind" / "USA_wind-speed_100m.tif",
        PROCESSED / "wind" / "wind_speed_100m.tif",
        REFERENCE_GRID,
        "bilinear",
    )


def prepare_vectors():
    print("\n=== Vector preparation ===")

    process_vector(
        RAW / "pad_us" / "study_area_protectedAreas.geojson",
        VECTORS / "protected_areas.gpkg",
    )

    process_vector(
        RAW / "military" / "dod_areas.gpkg",
        VECTORS / "military.gpkg",
    )

    process_vector(
        RAW / "wetlands" / "TN_geopackage_wetlands" /
        "TN_geopackage_wetlands.gpkg",
        VECTORS / "wetlands.gpkg",
        layer="TN_Wetlands",
    )

    process_vector(
        RAW / "transmission" / "transmission_lines.gpkg",
        VECTORS / "transmission.gpkg",
    )

    process_vector(
        RAW / "roads" / "tennessee_road_centerlines" /
        "Tennessee_NG911_Road_Centerlines.shp",
        VECTORS / "roads.gpkg",
    )

    process_vector(
        RAW / "census" / "tl_2020_47_tabblock20.shp",
        VECTORS / "census_blocks.gpkg",
    )

    prepare_airports()


def prepare_airports():
    print("\n=== FAA airport preparation ===")

    input_file = RAW / "airports" / "APT_BASE.csv"
    output_file = VECTORS / "airports.gpkg"

    df = pd.read_csv(input_file)

    df = df[
        df["LAT_DECIMAL"].notna()
        & df["LONG_DECIMAL"].notna()
    ].copy()

    airports = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["LONG_DECIMAL"],
            df["LAT_DECIMAL"],
        ),
        crs="EPSG:4326",
    )

    airports = airports.to_crs("EPSG:5070")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    airports.to_file(
        output_file,
        layer="airports",
        driver="GPKG",
    )

    print(f"Features: {len(airports):,}")
    print(f"Output:   {output_file}")


def calculate_distance_raster(
    vector_file,
    output_mask,
    output_distance,
    filter_function,
):
    with rasterio.open(REFERENCE_GRID) as src:
        profile = src.profile.copy()
        transform = src.transform
        shape = (src.height, src.width)
        crs = src.crs

    g = gpd.read_file(vector_file)
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

    profile.update(
        dtype="uint8",
        count=1,
        nodata=0,
        compress="lzw",
    )

    with rasterio.open(output_mask, "w", **profile) as dst:
        dst.write(arr, 1)

    distance_km = (
        distance_transform_edt(arr == 0)
        * 100
        / 1000
    )

    profile.update(
        dtype="float32",
        nodata=np.nan,
    )

    with rasterio.open(output_distance, "w", **profile) as dst:
        dst.write(distance_km.astype("float32"), 1)

    return len(g)


def prepare_transmission():
    print("\n=== Transmission distance ===")

    def qualifying(g):
        return g[g["VOLTAGE"] >= 100].copy()

    count = calculate_distance_raster(
        VECTORS / "transmission.gpkg",
        PROCESSED / "transmission_100kv_mask.tif",
        PROCESSED / "transmission_distance_km.tif",
        qualifying,
    )

    print(f"Qualifying features: {count:,}")


def prepare_roads():
    print("\n=== Road access distance ===")

    def access_network(g):
        g = g[g["CFCC"].notna()].copy()
        return g[
            g["CFCC"].str.startswith(
                ("A1", "A2", "A3", "A4", "A5")
            )
        ].copy()

    count = calculate_distance_raster(
        VECTORS / "roads.gpkg",
        PROCESSED / "roads_access_mask.tif",
        PROCESSED / "road_distance_km.tif",
        access_network,
    )

    print(f"Access-network features: {count:,}")


def main():
    if not REFERENCE_GRID.exists():
        raise FileNotFoundError(
            f"Reference grid not found: {REFERENCE_GRID}"
        )

    print("Wind Farm Suitability Screening")
    print("================================")
    print("Stage 1: Prepare and standardize data")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    VECTORS.mkdir(parents=True, exist_ok=True)

    prepare_rasters()
    prepare_vectors()
    prepare_transmission()
    prepare_roads()

    print("\nStage 1 complete.")


if __name__ == "__main__":
    main()

