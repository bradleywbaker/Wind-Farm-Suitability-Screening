from pathlib import Path

import numpy as np
import rasterio
import shapefile
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import shape, box
from shapely.ops import transform
from pyproj import CRS, Transformer


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT = Path(r"C:\GIS_Projects\Wind-Farm-Suitability-Screening")

DEM_DIR = PROJECT / "data" / "raw" / "dem"
PROCESSED_DIR = PROJECT / "data" / "processed" / "dem"

STUDY_AREA = PROCESSED_DIR / "study_area.shp"

MOSAIC = PROCESSED_DIR / "dem_mosaic.tif"
UTM_DEM = PROCESSED_DIR / "dem_utm16n.tif"
SLOPE = PROCESSED_DIR / "slope_percent.tif"

TARGET_CRS = "EPSG:32616"


# ---------------------------------------------------------
# Read study area
# ---------------------------------------------------------

print("Reading study area...")

reader = shapefile.Reader(str(STUDY_AREA))

study_geometries = [
    shape(record.__geo_interface__)
    for record in reader.shapes()
]

reader.close()

if not study_geometries:
    raise RuntimeError("No geometries found in study area shapefile.")

# Read CRS from .prj file
prj_file = STUDY_AREA.with_suffix(".prj")

with open(prj_file, "r") as f:
    study_crs_wkt = f.read()

study_crs = CRS.from_wkt(study_crs_wkt)

print(f"Study area CRS: {study_crs.to_string()}")


# Combine study area geometries
study_geometry = study_geometries[0]

for geom in study_geometries[1:]:
    study_geometry = study_geometry.union(geom)


# ---------------------------------------------------------
# Find DEM tiles intersecting study area
# ---------------------------------------------------------

print("Finding DEM tiles...")

dem_files = sorted(DEM_DIR.glob("*.tif"))

if not dem_files:
    raise RuntimeError(f"No DEM GeoTIFFs found in {DEM_DIR}")

selected_files = []

for dem_file in dem_files:

    with rasterio.open(dem_file) as src:

        dem_crs = CRS.from_user_input(src.crs)

        if dem_crs != study_crs:

            transformer = Transformer.from_crs(
                study_crs,
                dem_crs,
                always_xy=True
            )

            study_geom_dem = transform(
                transformer.transform,
                study_geometry
            )

        else:
            study_geom_dem = study_geometry

        dem_bounds = box(*src.bounds)

        if study_geom_dem.intersects(dem_bounds):
            selected_files.append(dem_file)


print(f"Found {len(selected_files)} DEM tiles intersecting study area.")

for dem_file in selected_files:
    print(f"  {dem_file.name}")

if not selected_files:
    raise RuntimeError("No DEM tiles intersect the study area.")


# ---------------------------------------------------------
# Mosaic selected DEM tiles
# ---------------------------------------------------------

print("Creating DEM mosaic...")

src_files = [rasterio.open(f) for f in selected_files]

mosaic, mosaic_transform = merge(src_files)

mosaic_meta = src_files[0].meta.copy()

mosaic_meta.update(
    {
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": mosaic_transform,
        "compress": "deflate",
        "nodata": -999999.0,
        "BIGTIFF": "YES",
    }
)

with rasterio.open(MOSAIC, "w", **mosaic_meta) as dst:
    dst.write(mosaic)

for src in src_files:
    src.close()

print(f"Saved: {MOSAIC}")


# ---------------------------------------------------------
# Reproject full mosaic to UTM Zone 16N
# ---------------------------------------------------------

print("Reprojecting DEM to UTM Zone 16N...")

with rasterio.open(MOSAIC) as src:

    transform_utm, width_utm, height_utm = calculate_default_transform(
        src.crs,
        TARGET_CRS,
        src.width,
        src.height,
        *src.bounds
    )

    utm_meta = src.meta.copy()

    utm_meta.update(
        {
            "driver": "GTiff",
            "crs": TARGET_CRS,
            "transform": transform_utm,
            "width": width_utm,
            "height": height_utm,
            "compress": "deflate",
            "BIGTIFF": "YES",
        }
    )

    with rasterio.open(UTM_DEM, "w", **utm_meta) as dst:

        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform_utm,
            dst_crs=TARGET_CRS,
            resampling=Resampling.bilinear,
            src_nodata=src.nodata,
            dst_nodata=src.nodata,
        )

print(f"Saved: {UTM_DEM}")


# ---------------------------------------------------------
# Calculate slope in percent
# ---------------------------------------------------------

print("Calculating slope in percent...")

with rasterio.open(UTM_DEM) as src:

    elevation = src.read(1).astype("float32")

    nodata = src.nodata

    if nodata is not None:
        valid = elevation != nodata
    else:
        valid = np.isfinite(elevation)

    # Pixel dimensions in meters
    x_resolution = abs(src.transform.a)
    y_resolution = abs(src.transform.e)

    # Calculate elevation gradients
    dz_dy, dz_dx = np.gradient(
        elevation,
        y_resolution,
        x_resolution
    )

    # Calculate slope as percent
    slope_percent = (
        np.sqrt(dz_dx**2 + dz_dy**2) * 100
    ).astype("float32")

    # Restore NoData
    slope_percent[~valid] = nodata

    slope_meta = src.meta.copy()

    slope_meta.update(
        {
            "driver": "GTiff",
            "dtype": "float32",
            "count": 1,
            "nodata": nodata,
            "compress": "deflate",
            "BIGTIFF": "YES",
        }
    )

    with rasterio.open(SLOPE, "w", **slope_meta) as dst:
        dst.write(slope_percent, 1)

print(f"Saved: {SLOPE}")

print("")
print("DEM processing complete.")