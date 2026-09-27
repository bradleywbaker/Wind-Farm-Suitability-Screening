from pathlib import Path
import sys

import numpy as np
import rasterio


def calculate_slope(input_path, output_path):
    """
    Calculate slope in percent from a projected DEM.

    Nodata cells are excluded before calculating gradients so they
    cannot create artificial extreme slope values.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    with rasterio.open(input_path) as src:
        dem = src.read(1).astype("float32")
        profile = src.profile.copy()
        nodata = src.nodata

    valid = np.isfinite(dem)

    if nodata is not None:
        valid &= dem != nodata

    # Prevent nodata values from contaminating gradient calculations.
    dem_masked = dem.copy()
    dem_masked[~valid] = np.nan

    dzdy, dzdx = np.gradient(dem_masked, 100, 100)

    slope_percent = np.sqrt(dzdx**2 + dzdy**2) * 100

    # Cells affected by nodata remain nodata.
    slope_percent[~valid] = np.nan

    profile.update(
        dtype="float32",
        nodata=np.nan,
        compress="lzw",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(slope_percent.astype("float32"), 1)

    print("Slope calculated")
    print("----------------")
    print(f"Input:       {input_path}")
    print(f"Output:      {output_path}")
    print("Units:       percent")


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(
            "Usage:\n"
            "python src\\geo_tools\\terrain.py "
            "<input_dem> <output_slope>"
        )
        sys.exit(1)

    calculate_slope(
        input_path=sys.argv[1],
        output_path=sys.argv[2],
    )
