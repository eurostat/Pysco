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

if "steps" in params and 1 in params["steps"]:
    compute_accessibility_grids(params, services=params["services"], years=params["years"])

if "steps" in params and 2 in params["steps"]:
    compute_accessibility_grids(params, services=params["services"], years=params["years"])

if "steps" in params and 3 in params["steps"]:
    combine_to_geotiff(params, services=params["services"], years=params["years"], do_combination=True)

if "steps" in params and 4 in params["steps"]:
    gridviz_tiling(params, services=params["services"], aggregate=True, tiling=True, deploy=True)

if "steps" in params and 5 in params["steps"]:
    gridviz_tiling_points(params, services=params["services"], years=params["years"])

if "steps" in params and 6 in params["steps"]:
    compute_statistics(params, services=params["services"], decompose_timeseries=True, compute_percentages=True )

