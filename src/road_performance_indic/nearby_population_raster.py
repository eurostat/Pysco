# compute nearby population from raster data, using (fast) convolution

import numpy as np
import rasterio
import sys
import os
from scipy import ndimage
from skimage.morphology import disk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.geotiff import geotiff_mask_by_countries, rasterise_tesselation_gpkg, combine_geotiffs


#TODO correct 2018
#TODO: try 100m resolution ? disaggregate 2018
#TODO handle peloponese ? connect it ?



def circular_kernel_sum(
    input_tiff,
    output_tiff,
    radius_m=120000,
    dtype=rasterio.float32,
    compress=None,
):
    with rasterio.open(input_tiff) as src:
        data = src.read(1)
        profile = src.profile
        nodata = src.nodata
        pixel_size, pixel_size_y = src.res
        assert pixel_size == pixel_size_y, "Pixels must be square."

    if nodata is not None:
        data = np.where((data == nodata) | (data < 0), 0, data)
    else:
        data = np.clip(data, 0, None)

    data = data.astype(dtype)

    radius_px = int(radius_m / pixel_size)
    kernel = disk(radius_px).astype(dtype)

    data = ndimage.convolve(data, kernel, mode='constant', cval=0)
    #TODO test that - it may be faster !
    #from scipy.signal import fftconvolve
    #data = fftconvolve(data, kernel, mode='same')

    profile.update(dtype=dtype)
    profile.pop("nodata", None)
    #profile.update(nodata=None)
    if compress is not None:
        profile.update(compress=compress)

    with rasterio.open(output_tiff, "w", **profile) as dst:
        dst.write(data, 1)



# compute circular kernel sum of band 1, but only for pixel values with same band 2 values
# use it for example, to compute neerby population in the same land mass / island
def circular_kernel_sum_per_code(
    input_tiff, # band 1: population. band 2: codes
    output_tiff,
    radius_m=120000,
    dtype=rasterio.float32,
    compress=None,
):
    with rasterio.open(input_tiff) as src:
        values = src.read(1)
        codes = src.read(2)
        profile = src.profile
        nodata = src.nodata
        pixel_size = src.res[0]

    print(nodata)

    # Prepare output with nodata everywhere
    output = np.full_like(values, nodata, dtype=dtype)

    # Prepare kernel
    radius_px = int(radius_m / pixel_size)
    kernel = disk(radius_px).astype(dtype)

    # Determine unique codes (excluding nodata)
    unique_codes = np.unique(codes)
    unique_codes = unique_codes[unique_codes != nodata]

    print(len(unique_codes), "codes")

    for code in unique_codes:
        print(f"Processing code: {code}")

        # Create mask for this code
        mask = (codes == code)
        if not np.any(mask): continue

        # Get bounds of mask: min and max rows/cols where mask is True
        rows, cols = np.where(mask)
        row_min, row_max = rows.min(), rows.max()
        col_min, col_max = cols.min(), cols.max()

        # Compute window boundaries, clamped within raster
        row_start = max(row_min, 0)
        row_stop  = min(row_max + 1, values.shape[0])
        col_start = max(col_min, 0)
        col_stop  = min(col_max + 1, values.shape[1])

        print(f"   Subregion size: {(row_stop-row_start)*(col_stop-col_start)} pixels")

        # Extract subarrays
        values_sub = values[row_start:row_stop, col_start:col_stop]
        codes_sub  = codes[row_start:row_stop, col_start:col_stop]

        # Prepare values for convolution following rules:
        # - if code == nodata → nodata (we keep that outside the conv mask)
        # - if code != nodata and values == nodata → 0
        # - else: use the value
        values_sub_for_conv = np.where(
            (codes_sub != nodata) & (values_sub != nodata),
            values_sub,
            0
        ).astype(dtype)

        # Apply convolution
        summed_sub = ndimage.convolve(values_sub_for_conv, kernel, mode='constant', cval=0)

        # Write results back only where mask_sub is True (i.e. code == current code)
        mask_sub   = mask[row_start:row_stop, col_start:col_stop]
        rows_mask, cols_mask = np.where(mask_sub)
        output[row_start:row_stop, col_start:col_stop][rows_mask, cols_mask] = summed_sub[rows_mask, cols_mask]

    # Update profile
    profile.update(dtype=dtype, count=1, nodata=nodata)
    if compress is not None:
        profile.update(compress=compress)

    # Write result
    with rasterio.open(output_tiff, 'w', **profile) as dst:
        dst.write(output, 1)





folder = "/home/juju/gisco/road_transport_performance/"

pop = {
    "2018" : "/home/juju/geodata/census/2018/JRC_1K_POP_2018_clean.tif",
    "2021" : "/home/juju/geodata/census/2021/ESTAT_OBS-VALUE-T_2021_V2_clean.tiff",
}

for resolution in [1000]: #100
    '''
    print("rasterise land mass index")
    rasterise_tesselation_gpkg(
        folder + "land_mass_gridded.gpkg",
        folder + "land_mass_gridded.tiff",
        fieldname='code',
        resolution=resolution,
        compression='deflate',
        nodata_value=-9999,
        dtype=np.int32,
        all_touched = True
    )
    '''
    for year in ["2018"]: #"2021", 
        print(year)
        '''
        # apply fast convolution - without taking into account land mass index
        print("convolution (fast)", year)
        circular_kernel_sum(
            pop[year],
            folder + "nearby_population_"+year+"_fast.tiff",
            120000,
            rasterio.uint32,
            compress="deflate",
        )
        print("combine population + land mass index")
        combine_geotiffs(
            [
                pop[year],
                folder + "land_mass_gridded.tiff",
            ],
            folder + "pop_"+year+"_lmi.tiff",
            compress="deflate",
            nodata_value=-9999,
            dtype=np.int64,
        )
        '''

        print("compute convolution")
        circular_kernel_sum_per_code(
            folder + "pop_"+year+"_lmi.tiff",
            folder + "nearby_population_"+year+".tiff",
            radius_m=120000,
            dtype=rasterio.int64,
            compress="deflate",
        )

