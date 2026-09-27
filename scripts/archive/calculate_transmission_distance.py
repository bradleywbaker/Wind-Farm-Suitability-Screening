import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt

ref = "data/processed/reference_grid.tif"
trans = "data/processed/vectors/transmission.gpkg"
mask = "data/processed/transmission_100kv_mask.tif"
dist = "data/processed/transmission_distance_km.tif"

with rasterio.open(ref) as src:
    profile = src.profile.copy()
    transform = src.transform
    shape = (src.height, src.width)
    crs = src.crs

g = gpd.read_file(trans)
g = g[g["VOLTAGE"] >= 100].copy()
g = g.to_crs(crs)

arr = rasterize(
    ((geom, 1) for geom in g.geometry if geom is not None),
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

with rasterio.open(mask, "w", **profile) as dst:
    dst.write(arr, 1)

dist_arr = distance_transform_edt(arr == 0) * 100 / 1000

profile.update(
    dtype="float32",
    nodata=np.nan,
)

with rasterio.open(dist, "w", **profile) as dst:
    dst.write(dist_arr.astype("float32"), 1)

print("Transmission distance raster created")
print("-------------------------------------")
print(f"Qualifying features: {len(g)}")
print(f"Max distance: {dist_arr.max():.2f} km")
print(f"P50: {np.percentile(dist_arr, 50):.2f} km")
print(f"P75: {np.percentile(dist_arr, 75):.2f} km")
print(f"P90: {np.percentile(dist_arr, 90):.2f} km")
print(f"P95: {np.percentile(dist_arr, 95):.2f} km")