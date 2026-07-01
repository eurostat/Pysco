import json
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from accessibility.step1_grid_computation import compute_accessibility_grids
from accessibility.step2_combine_to_geotiff import combine_to_geotiff
#from  import compute_accessibility_grids
#from 2_combine_to_geotiff import combine_to_geotiff

# TODO
# accessibility to schools by walking
# secondary education services accessibility

# Load parameters from JSON file
params_file = '/home/juju/workspace/Pysco/src/accessibility/params_julien.json'
with open(params_file, 'r') as f: params = json.load(f)

# 1
compute_accessibility_grids(params)

# 2
combine_to_geotiff(params, do_combination=True, resolutions=[100])

