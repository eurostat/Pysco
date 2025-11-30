import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from utils.dasymetric_mapping import dasymetric_disaggregation_step_1, dasymetric_aggregation_step_2


#TODO forbid cas_l_1_1 age_g_1 age_g_1 and cas_l_1_1 age_g_3

#TODO GHSL: improve, with probability?
#TODO OSM buildings ?


w = '/home/juju/gisco/census_2021_iceland/'
pop_structure = { "sex" : ["sex_1", "sex_2"],
                 "age_g" : ["age_g_1","age_g_2","age_g_3"],
                 "pob_l" : ["pob_l_1","pob_l_2_1","pob_l_2_2"],
                 "roy" : ["roy_1","roy_2_1","roy_2_2"],
                 "cas_l" : [ "cas_l_1_1", "cas_l_1_2" ]
                }
resolution = 1000

print("Dasymetric disaggregation step 1")
dasymetric_disaggregation_step_1(
    w+"IS_pop_grid_surf_3035.gpkg",
    input_dasymetric_gpkg = None,
    output_gpkg= w+"out/disag_area.gpkg",
    output_synthetic_population_gpkg= w+"out/disag_point.gpkg",
    tot_pop_att= "sex_0",
    pop_structure= pop_structure,
    pop_grouping_threshold= 10,
)
dasymetric_disaggregation_step_1(
    w+"IS_pop_grid_surf_3035_land.gpkg",
    input_dasymetric_gpkg = w+"strandlina_flakar_3035_decomposed.gpkg",
    output_gpkg= w+"out/disag_area_land.gpkg",
    output_synthetic_population_gpkg= w+"out/disag_point_land.gpkg",
    tot_pop_att= "sex_0",
    pop_structure= pop_structure,
    pop_grouping_threshold= 10,
)
dasymetric_disaggregation_step_1(
    w+"IS_pop_grid_surf_3035_land.gpkg",
    input_dasymetric_gpkg = w+"ghsl_land_3035.gpkg",
    output_gpkg= w+"out/disag_area_ghsl_land.gpkg",
    output_synthetic_population_gpkg= w+"out/disag_point_ghsl_land.gpkg",
    tot_pop_att= "sex_0",
    pop_structure= pop_structure,
    pop_grouping_threshold= 10,
)

print("Dasymetric aggregation step 2")
dasymetric_aggregation_step_2(w+"out/disag_area.gpkg", w+"out/area_weighted.gpkg",
                              tot_pop_att = "sex_0", pop_structure=pop_structure, resolution=resolution)
dasymetric_aggregation_step_2(w+"out/disag_area_land.gpkg", w+"out/dasymetric_land.gpkg",
                              tot_pop_att = "sex_0", pop_structure=pop_structure, resolution=resolution)
dasymetric_aggregation_step_2(w+"out/disag_area_ghsl_land.gpkg", w+"out/dasymetric_GHSL_land.gpkg",
                              tot_pop_att = "sex_0", pop_structure=pop_structure, resolution=resolution)

print("Dasymetric aggregation step 2 from points")
dasymetric_aggregation_step_2(w+"out/disag_point.gpkg", w+"out/area_weighted_rounded.gpkg",
                              tot_pop_att = "sex_0", pop_structure=pop_structure, type='population', resolution=resolution)
dasymetric_aggregation_step_2(w+"out/disag_point_land.gpkg", w+"out/dasymetric_land_rounded.gpkg",
                              tot_pop_att = "sex_0", pop_structure=pop_structure, type='population', resolution=resolution)
dasymetric_aggregation_step_2(w+"out/disag_point_ghsl_land.gpkg", w+"out/dasymetric_GHSL_land_rounded.gpkg",
                              tot_pop_att = "sex_0", pop_structure=pop_structure, type='population', resolution=resolution)

print("Nearest neighbour")
dasymetric_aggregation_step_2(w+"IS_pop_grid_point_3035.gpkg", w+"out/nearest_neighbour.gpkg",
                              tot_pop_att = "sex_0", pop_structure=pop_structure, type='point', resolution=resolution)

