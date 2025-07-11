import numpy as np
import pandas as pd

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.convert import parquet_grid_to_geotiff


df = pd.read_csv("/home/juju/gisco/road_transport_performance/grid_network_perf_2011_2019_2021_c.csv")
#x,y,grd_id,pop120km_2011,pop90m_2011,pop90m_u120_2011,pop120km_2018,pop90m_2019,pop90m_u120_2019,pop120km_2021,pop90m_2022,pop90m_u120_2022
df = df.drop(columns=["x", "y"])
# Sauvegarder en fichier Parquet
df.to_parquet("/home/juju/gisco/road_transport_performance/grid_network_perf_2011_2019_2021_c.parquet", index=False)

parquet_grid_to_geotiff(
    ["/home/juju/gisco/road_transport_performance/grid_network_perf_2011_2019_2021_c.parquet"],
    "/home/juju/gisco/road_transport_performance/grid_network_perf_2011_2019_2021_c.tif",
    grid_id_field="grd_id",
    #attributes=[""]
    dtype=np.int64,
    compress="deflate",
    )
