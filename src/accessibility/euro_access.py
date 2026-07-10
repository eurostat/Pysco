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
# params stats versions
# review zip deploy
# stats: add version code !
# accessibility to schools by walking
# secondary education services accessibility
# stats compute stats with 100m resolution ?

# Load parameters from JSON file
params_paths_file = sys.argv[1]
params_output_file = sys.argv[2]

with open(params_paths_file, 'r') as f: params = json.load(f)
with open(params_output_file, 'r') as f:
    params_ = json.load(f)
    for k in params_.keys(): params[k] = params_[k]

# 1
compute_accessibility_grids(params, services=params["services"], years=params["years"])
# 2
combine_to_geotiff(params, services=params["services"], years=params["years"], do_combination=True)
# 3
gridviz_tiling(params, services=params["services"], aggregate=True, tiling=True, deploy=True)
# 4
gridviz_tiling_points(params, services=params["services"], years=params["years"])
# 5
compute_statistics(params, services=params["services"], decompose_timeseries=True, compute_percentages=True )

