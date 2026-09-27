import geopandas as gpd
import rasterio
import numpy as np
from rasterio.features import geometry_mask

candidate_file = "data/processed/candidate_areas.gpkg"

rasters = {
    "wind": "data/processed/wind/wind_speed_100m.tif",
    "slope": "data/processed/dem/slope_percent_100m.tif",
    "transmission": "data/processed/transmission_distance_km.tif",
    "roads": "data/processed/road_distance_km.tif",
}

gdf = gpd.read_file(candidate_file)

# Store candidate IDs before updating attributes.
candidate_ids = gdf["candidate_id"].tolist()

metrics = {
    "mean_wind_ms": [],
    "mean_slope_pct": [],
    "median_trans_km": [],
    "median_road_km": [],
}

for candidate_id in candidate_ids:

    candidate = gdf[gdf["candidate_id"] == candidate_id]

    with rasterio.open(rasters["wind"]) as src:
        wind = src.read(1)
        wind_mask = geometry_mask(
            candidate.geometry,
            transform=src.transform,
            invert=True,
            out_shape=wind.shape,
        )

    with rasterio.open(rasters["slope"]) as src:
        slope = src.read(1)
        slope_mask = geometry_mask(
            candidate.geometry,
            transform=src.transform,
            invert=True,
            out_shape=slope.shape,
        )

    with rasterio.open(rasters["transmission"]) as src:
        transmission = src.read(1)
        transmission_mask = geometry_mask(
            candidate.geometry,
            transform=src.transform,
            invert=True,
            out_shape=transmission.shape,
        )

    with rasterio.open(rasters["roads"]) as src:
        roads = src.read(1)
        roads_mask = geometry_mask(
            candidate.geometry,
            transform=src.transform,
            invert=True,
            out_shape=roads.shape,
        )

    wind_values = wind[wind_mask]
    slope_values = slope[slope_mask]
    transmission_values = transmission[transmission_mask]
    road_values = roads[roads_mask]

    wind_values = wind_values[np.isfinite(wind_values)]
    slope_values = slope_values[np.isfinite(slope_values)]
    transmission_values = transmission_values[np.isfinite(transmission_values)]
    road_values = road_values[np.isfinite(road_values)]

    metrics["mean_wind_ms"].append(
        np.mean(wind_values)
    )

    metrics["mean_slope_pct"].append(
        np.mean(slope_values)
    )

    metrics["median_trans_km"].append(
        np.median(transmission_values)
    )

    metrics["median_road_km"].append(
        np.median(road_values)
    )

for field, values in metrics.items():
    gdf[field] = values

# Rewrite the existing candidate layer.
gdf.to_file(
    candidate_file,
    layer="candidate_areas",
    driver="GPKG",
)

print("Candidate metrics added")
print("-----------------------")
print(f"Candidate areas: {len(gdf):,}")
print()
print("Added fields:")
print("mean_wind_ms")
print("mean_slope_pct")
print("median_trans_km")
print("median_road_km")
print()
print(f"Updated: {candidate_file}")