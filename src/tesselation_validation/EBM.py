

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tesselation_validation.validation import validate_polygonal_tesselation


folder = "/home/juju/geodata/eurogeographics/EBM/"
out_folder = "/home/juju/Bureau/"
version = "2025_2"
for case in ["A"]: #"NUTS_1", "NUTS_2", "NUTS_3", "LAU"
    print("*******", case)

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+".gpkg",
                epsilon = 0.01,
                check_ogc_validity=True,
                )

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+".gpkg",
                epsilon = 0.01,
                check_thin_parts=True,
                )

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+".gpkg",
                epsilon = 0.01,
                check_intersection=True,
                )

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+".gpkg",
                epsilon = 0.01,
                check_polygonisation=True,
                )

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+".gpkg",
                epsilon = 0.01,
                check_microscopic_segments=True,
                )

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+".gpkg",
                epsilon = 0.01,
                check_noding_issues=True,
                )


