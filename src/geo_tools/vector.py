from pathlib import Path
import sys

import geopandas as gpd


def process_vector(input_path, output_path, target_crs="EPSG:5070", layer=None):
    """
    Reproject and validate a vector dataset.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    if layer:
        gdf = gpd.read_file(input_path, layer=layer)
    else:
        gdf = gpd.read_file(input_path)

    # Remove null geometries
    gdf = gdf[gdf.geometry.notna()].copy()

    # Repair invalid geometries where possible
    invalid = ~gdf.geometry.is_valid

    if invalid.any():
        gdf.loc[invalid, "geometry"] = gdf.loc[invalid, "geometry"].make_valid()

    # Reproject
    gdf = gdf.to_crs(target_crs)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    gdf.to_file(
        output_path,
        layer=output_path.stem,
        driver="GPKG",
    )

    print("Vector processed")
    print("----------------")
    print(f"Input:       {input_path}")
    if layer:
        print(f"Layer:       {layer}")
    print(f"Output:      {output_path}")
    print(f"CRS:         {gdf.crs}")
    print(f"Features:    {len(gdf)}")
    print(f"Geometry:    {gdf.geom_type.value_counts().to_dict()}")
    print(f"Valid:       {gdf.geometry.is_valid.all()}")


if __name__ == "__main__":

    if len(sys.argv) not in (3, 4):
        print(
            "Usage:\n"
            "python src\\geo_tools\\vector.py "
            "<input> <output> [layer]"
        )
        sys.exit(1)

    process_vector(
        input_path=sys.argv[1],
        output_path=sys.argv[2],
        layer=sys.argv[3] if len(sys.argv) == 4 else None,
    )