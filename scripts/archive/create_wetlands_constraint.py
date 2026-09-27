import geopandas as gpd
import rasterio
from rasterio.features import rasterize

input_vector = "data/processed/vectors/wetlands.gpkg"
output_raster = "data/processed/wetlands_constraint.tif"

with rasterio.open("data/processed/reference_grid.tif") as ref:
    profile = ref.profile.copy()
    transform = ref.transform
    shape = (ref.height, ref.width)
    crs = ref.crs

g = gpd.read_file(input_vector)
g = g.to_crs(crs)

arr = rasterize(
    ((geom, 1) for geom in g.geometry if geom is not None),
    out_shape=shape,
    transform=transform,
    fill=0,
    dtype="uint8",
)

eligible = (arr == 0)

profile.update(
    dtype="uint8",
    count=1,
    nodata=0,
    compress="lzw",
)

with rasterio.open(output_raster, "w", **profile) as dst:
    dst.write(eligible.astype("uint8"), 1)

print("Wetlands constraint created")
print("----------------------------")
print("Exclusion:   All mapped wetland/water features")
print(f"Features:    {len(g):,}")
print(f"Eligible:    {eligible.sum():,} pixels")
print(f"Excluded:    {(~eligible).sum():,} pixels")