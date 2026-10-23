import pandas as pd
from datetime import datetime
import shutil

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.grid2stat import grid2stat_weighted_average
from utils.csvutils import hypercube_csv_to_timeseries_csv



def filter_hypercube(input_path: str, country_codes: list[str], output_path: str):
    """
    Filter a hypercube CSV based on country membership and year.

    - Rows whose GEO country code (first 2 letters) is in `country_codes`
      are kept only if TIME == 2026.
    - Rows whose GEO country code is NOT in `country_codes`
      are kept only if TIME == 2023.

    The filtered data is saved to `output_path` and also returned.
    """
    df = pd.read_csv(input_path, dtype={"GEO": str})

    # Normalize the country list for case-insensitive matching
    codes = {c.strip().upper() for c in country_codes}

    # Country code = first 2 letters of GEO
    geo_country = df["GEO"].astype(str).str[:2].str.upper()
    in_list = geo_country.isin(codes)

    # Make sure TIME is numeric so comparisons with 2026 / 2023 work
    time = pd.to_numeric(df["TIME"], errors="coerce")

    # Keep rows that satisfy the rules (the complement of the removal conditions)
    keep = (in_list & (time == 2026)) | (~in_list & (time == 2023))

    result = df[keep]
    result.to_csv(output_path, index=False)



"""
df = grid2stat_weighted_average(
    indic_path = "/home/juju/gisco/accessibility/euro_access_education_2023_1000m_v2026_10.tif",
    weight_path = "/home/juju/gisco/census_2021_v3_production/ESTAT_Census_2021_V3.tiff",
    #region_path="/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg",
    region_path="/home/juju/geodata/gisco/LAU_RG_100K_2024_3035.gpkg",
    #region_id_att="NUTS_ID",
    region_id_att="GISCO_ID",
    region_filter=None,
    indic_band = 1,
    weight_band = 1,
    masks=None,
)

print(df)
df.to_csv("/home/juju/Bureau/output.csv", index=False)
"""
