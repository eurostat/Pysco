import geopandas as gpd
import pandas as pd

def population_near_coast(df: pd.DataFrame, dist: float) -> float:
    mask = (df["DIST_COAST"] < dist) & df["CNT_ID"].astype(str).str.contains("PT", na=False)
    return df.loc[mask, "T"].sum()


def main(gpkg_path: str, output_csv: str, max: int=50000, step:int=10000, layer: str = None):
    # Read attributes only, once
    df = gpd.read_file(gpkg_path, layer=layer, ignore_geometry=True)

    # Pre-filter on country to speed up the loop
    df = df[df["CNT_ID"].astype(str).str.contains("PT", na=False)]

    thresholds = range(0, max, step)
    results = pd.DataFrame({
        "D": thresholds,
        "population": [population_near_coast(df, D) for D in thresholds],
    })

    results.to_csv(output_csv, index=False)
    print(results)

main(
    "/home/juju/geodata/gisco/grids/grid_1km_point.gpkg",
    "/home/juju/Bureau/pop_coast_PT.csv",
)
