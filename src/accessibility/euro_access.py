import json
#from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from accessibility.step1_grid_computation import compute_accessibility_grids
from accessibility.step2_combine_to_geotiff import combine_to_geotiff
from accessibility.step3_gridviz_grids import gridviz_tiling
from accessibility.step4_gridviz_service_points import gridviz_tiling_points
from accessibility.step5_compute_stats import compute_statistics

# TODO
# review move
# stats: add version code !
# accessibility to schools by walking
# secondary education services accessibility
# stats compute stats with 100m resolution ?

# Load parameters from JSON file
params_file = sys.argv[1]
#params_file = '/home/juju/workspace/Pysco/src/accessibility/params_julien.json'
with open(params_file, 'r') as f: params = json.load(f)

# 1
#compute_accessibility_grids(params)
# 2
#combine_to_geotiff(params, do_combination=True, resolutions=[100])
# 3
#gridviz_tiling(params, aggregate=True, tiling=True, zip_move=True)
# 4
#gridviz_tiling_points(params, services=["evrp"])
# 5
compute_statistics(params, decompose_timeseries=True, compute_percentages=True,
                   services=["evrp"]
                   )
