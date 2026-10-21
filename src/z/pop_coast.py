import geopandas as gpd
import pandas as pd

def population_near_coast(df: pd.DataFrame, dist: float) -> float:
    print(f"Computing population within {dist} m of the coast...")
    mask = (df["DIST_COAST"] < dist)
    return df.loc[mask, "T"].sum()


def main(gpkg_path: str, output_csv: str, max: int=50000, step:int=10000, layer: str = None):
    print("Loading points from GeoPackage...")

    df = gpd.read_file(gpkg_path, layer=layer, ignore_geometry=True)
    print(f"Loaded {len(df)} points from {gpkg_path}")

    # Pre-filter on country to speed up the loop
    df = df[df["CNTR_ID"].astype(str).str.contains("PT", na=False)]
    print(f"Loaded {len(df)} points for Portugal from {gpkg_path}")

    thresholds = range(0, max, step)
    results = pd.DataFrame({
        "dist_to_coast_km": thresholds/1000,
        "population": [population_near_coast(df, dist) for dist in thresholds],
    })

    results.to_csv(output_csv, index=False)
    print(results)

main(
    "/home/juju/geodata/gisco/grids/grid_1km_point.gpkg",
    "/home/juju/Bureau/pop_coast_PT.csv",
)
