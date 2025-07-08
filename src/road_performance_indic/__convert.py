import pandas as pd



df = pd.read_csv("/home/juju/gisco/road_transport_performance/grid_network_perf_2011_2019_2021_c.csv")
#x,y,grd_id,pop120km_2011,pop90m_2011,pop90m_u120_2011,pop120km_2018,pop90m_2019,pop90m_u120_2019,pop120km_2021,pop90m_2022,pop90m_u120_2022
df = df.drop(columns=["x", "y"])
# Sauvegarder en fichier Parquet
df.to_parquet("/home/juju/gisco/road_transport_performance/grid_network_perf_2011_2019_2021_c.parquet", index=False)



# open csv.
# select columns
# save as parquet
# convert to geotiff
'''
def parquet_grid_to_geotiff(
    input_parquet_files,
    output_tiff,
    grid_id_field='GRD_ID',
    attributes=None,
    bbox=None,
    parquet_nodata_values=None,
    tiff_nodata_value=-9999,
    dtype=np.int16,
    value_fun=None,
    compress='none'
):
'''
