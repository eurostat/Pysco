

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tesselation_validation.validation import validate_polygonal_tesselation


folder = "/home/juju/geodata/eurogeographics/EBM/"
version = "2026"
out_folder = "/home/juju/Bureau/EBM_"+version+"_validation/"
os.makedirs(out_folder, exist_ok=True)


for case in ["A", "NUTS_1", "NUTS_2", "NUTS_3", "LAU"]:
    print("*******", case)

    '''
    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+"_check_ogc_validity.gpkg",
                check_ogc_validity=True,
                )

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+"_check_intersection.gpkg",
                check_intersection=True,
                )
    '''

    '''
    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+"_check_microscopic_segments.gpkg",
                check_microscopic_segments=True,
                microscopic_segment_threshold=0.1,
                )

    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+"_check_noding_issues.gpkg",
                check_noding_issues=True,
                node_to_segment_distance_threshold=0.5,
                )
    '''
                
    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+"_check_thin_parts.gpkg",
                check_thin_parts=True,
                thin_part_threshold=0.1,
                )
    validate_polygonal_tesselation(
                folder + "EBM_"+case+"_"+version+".gpkg",
                out_folder + "issues_"+case+"_"+version+"_check_polygonisation.gpkg",
                check_polygonisation=True,
                polygonation_check_distance_threshold=1,
                )
