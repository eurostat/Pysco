import geopandas as gpd
import pandas as pd

def population_near_coast(df: pd.DataFrame, att:str, dist: float) -> float:
    print(f"Computing population {att} within {dist} m of the coast...")
    mask = (df["DIST_COAST"] < dist)
    return df.loc[mask, att].sum()


def main(gpkg_path: str, output_csv: str, max: int=50000, step:int=5000, layer: str = None):
    print("Loading points from GeoPackage...")
    df = gpd.read_file(gpkg_path, layer=layer, ignore_geometry=True)
    print(f"Loaded {len(df)} points from {gpkg_path}")

    df = df[df["CNTR_ID"].astype(str).str.contains("PT", na=False)]
    print(f"Kept {len(df)} points for Portugal from {gpkg_path}")

    thresholds = range(0, max, step)
    results = pd.DataFrame({
        "dist_to_coast_km": [dist/1000 for dist in thresholds],
        "T": [population_near_coast(df, "T", dist) for dist in thresholds],
        "Y_LT15": [population_near_coast(df, "Y_LT15", dist) for dist in thresholds],
        "Y_1564": [population_near_coast(df, "Y_1564", dist) for dist in thresholds],
        "Y_GE65": [population_near_coast(df, "Y_GE65", dist) for dist in thresholds],
    })

    results.to_csv(output_csv, index=False)
    print(results)

main(
    "/home/juju/Bureau/PT.gpkg",
    "/home/juju/Bureau/pop_coast_PT.csv",
    max = 250000,
    step = 1000
)
