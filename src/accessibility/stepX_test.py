import pandas as pd
from datetime import datetime
import shutil

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.grid2stat import grid2stat_weighted_average
from utils.csvutils import hypercube_csv_to_timeseries_csv



df = grid2stat_weighted_average(
    indic_path = "/home/juju/gisco/accessibility/euro_access_education_2023_1000m_v2026_04.tif",
    weight_path = "/home/juju/gisco/census_2021_v3_production/ESTAT_Census_2021_V3.tiff",

    indic_band = 1,
    weight_band = 1,

    region_path = "/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg",
    region_id_att = "NUTS_ID",
    region_filter = None,

    #masks: list = None,
)

print(df)
df.to_csv("/home/juju/Bureau/output.csv", index=False)

