import json
from pathlib import Path
import numpy as np

import rasterio
from rasterio.transform import from_origin


CONFIG = Path("config/analysis_grid.json")
GRID = Path("data/processed/reference_grid.json")
OUTPUT = Path("data/processed/reference_grid.tif")


with open(CONFIG) as f:
    config = json.load(f)

with open(GRID) as f:
    grid = json.load(f)

width = grid["width"]
height = grid["height"]
minx, miny, maxx, maxy = grid["extent"]
cell_size = config["cell_size"]

transform = from_origin(
    minx,
    maxy,
    cell_size,
    cell_size
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with rasterio.open(
    OUTPUT,
    "w",
    driver="GTiff",
    width=width,
    height=height,
    count=1,
    dtype="uint8",
    crs=config["crs"],
    transform=transform,
    nodata=0,
    compress="lzw"
) as dst:
    dst.write(np.ones((height, width), dtype="uint8"), 1)

print("Reference raster created")
print("------------------------")
print(f"Output:    {OUTPUT}")
print(f"CRS:       {config['crs']}")
print(f"Cell size: {cell_size} m")
print(f"Width:     {width}")
print(f"Height:    {height}")
print(f"Bounds:    {dst.bounds}")