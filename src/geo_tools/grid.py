import json
from pathlib import Path

import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import shape
from shapely.ops import transform


def create_reference_grid(config_path, output_path):
    config_path = Path(config_path)
    output_path = Path(output_path)

    with open(config_path, "r") as f:
        config = json.load(f)

    target_crs = CRS.from_user_input(config["crs"])
    cell_size = config["cell_size"]

    study_area_path = config_path.parent.parent / config["extent_source"]

    reader = shapefile.Reader(str(study_area_path))

    geometries = [
        shape(record.shape.__geo_interface__)
        for record in reader.iterShapeRecords()
    ]

    source_crs = CRS.from_epsg(4326)

    transformer = Transformer.from_crs(
        source_crs,
        target_crs,
        always_xy=True
    )

    projected = [
        transform(transformer.transform, geom)
        for geom in geometries
    ]

    bounds = projected[0].bounds

    for geom in projected[1:]:
        minx, miny, maxx, maxy = geom.bounds
        bounds = (
            min(bounds[0], minx),
            min(bounds[1], miny),
            max(bounds[2], maxx),
            max(bounds[3], maxy),
        )

    minx, miny, maxx, maxy = bounds

    width = int((maxx - minx) / cell_size) + 1
    height = int((maxy - miny) / cell_size) + 1

    print("Reference grid")
    print("----------------")
    print(f"CRS:       {target_crs.to_string()}")
    print(f"Cell size: {cell_size} m")
    print(f"Width:     {width}")
    print(f"Height:    {height}")
    print(f"Extent:    {minx}, {miny}, {maxx}, {maxy}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            {
                "crs": config["crs"],
                "cell_size": cell_size,
                "width": width,
                "height": height,
                "extent": [minx, miny, maxx, maxy]
            },
            f,
            indent=4
        )

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    create_reference_grid(
        "config/analysis_grid.json",
        "data/processed/reference_grid.json"
    )