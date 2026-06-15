import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.featureutils import iter_features


nuts_version = "2024"
nuts_lvl = "3"
su = iter_features(f"/home/juju/geodata/gisco/CNTR_RG_100K_{nuts_version}_3035.gpkg", where="STAT_LEVL_CODE = " + str(nuts_lvl))

su = list(su)
print("Number of features: ", len(su))

