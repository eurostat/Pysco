import pandas as pd
from datetime import datetime
import shutil
import json

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


params_paths_file = sys.argv[1]
params_output_file = sys.argv[2]

with open(params_paths_file, 'r') as f: params = json.load(f)
with open(params_output_file, 'r') as f:
    params_ = json.load(f)
    for k in params_.keys(): params[k] = params_[k]



country_codes_healthcare = "AT, BE, CY, DE, DK, ES, FR, IE, IT, LV, NL, NO, PL, SE, SK".split(", ")
country_codes_education = "AT, BE, DE, DK, ES FI, FR, HR, HU, IE, IT, NL, NO, PT, RO, SE, SI, SK".split(", ")


folder = params["out_folder"] + "stats/"
output_folder = folder + "for_regio/"
os.makedirs(output_folder, exist_ok=True)


sus = params["stat_units"]
services = params["accessibility_grid_versions"].keys()

for su in sus.keys():
    region_id_att = sus[su]["id"]
    geo = su + "_" + sus[su]["version"]
    for service in services:

        country_codes = country_codes_healthcare if service == "healthcare" else country_codes_education

        for mode in params["modes_stats"][service].keys():
            grid_mode = params["modes_stats"][service][mode]["grid_mode"]
            mode_unit = params["modes_stats"][service][mode]["mode_unit"]
            coeff = params["modes_stats"][service][mode]["coeff"]

            ofo = "euro_access_" + geo + "_" + service + "_" + mode + "_" + mode_unit + "_" + params["stats_versions"][service] + ".csv"
            if not os.path.exists(folder + ofo): continue

            filter_hypercube(folder + ofo, country_codes, output_folder + ofo)



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
