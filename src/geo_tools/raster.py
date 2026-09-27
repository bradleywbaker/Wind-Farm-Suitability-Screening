from pathlib import Path
import sys

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


def process_raster(
    input_path,
    output_path,
    reference_grid,
    resampling_method="bilinear",
):
    """
    Reproject and align a raster to the project reference grid.

    Resampling methods:
        bilinear = continuous data
        nearest  = categorical data
    """

    input_path = Path(input_path)
    output_path = Path(output_path)
    reference_grid = Path(reference_grid)

    resampling = getattr(Resampling, resampling_method)

    with rasterio.open(reference_grid) as ref:
        ref_crs = ref.crs
        ref_transform = ref.transform
        ref_width = ref.width
        ref_height = ref.height

    with rasterio.open(input_path) as src:

        nodata = src.nodata

        if nodata is None:
            nodata = -9999

        output = np.full(
            (ref_height, ref_width),
            nodata,
            dtype=np.float32,
        )

        reproject(
            source=rasterio.band(src, 1),
            destination=output,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            dst_nodata=nodata,
            resampling=resampling,
        )

        profile = src.profile.copy()

        profile.update(
            driver="GTiff",
            width=ref_width,
            height=ref_height,
            crs=ref_crs,
            transform=ref_transform,
            dtype="float32",
            nodata=nodata,
            compress="lzw",
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(output, 1)

    print("Raster processed")
    print("----------------")
    print(f"Input:       {input_path}")
    print(f"Output:      {output_path}")
    print(f"CRS:         {ref_crs}")
    print(f"Cell size:   {ref_transform.a} m")
    print(f"Dimensions:  {ref_width} x {ref_height}")
    print(f"Resampling:  {resampling_method}")


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print(
            "Usage:\n"
            "python src\\geo_tools\\raster.py "
            "<input> <output> <resampling>"
        )
        sys.exit(1)

    process_raster(
        input_path=sys.argv[1],
        output_path=sys.argv[2],
        reference_grid="data/processed/reference_grid.tif",
        resampling_method=sys.argv[3],
    )