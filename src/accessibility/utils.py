
# folders where to store the outputs
out_folder = '/home/juju/gisco/accessibility/'


# input data: pois and road network
pois_datasets = {
    "healthcare": {"2023":"/home/juju/geodata/gisco/basic_services/healthcare_2023_3035_20260421.gpkg",
                   "2020":"/home/juju/geodata/gisco/basic_services/healthcare_2020_3035_20260421.gpkg"},
    "education": {"2023":"/home/juju/geodata/gisco/basic_services/education_2023_3035_20260421.gpkg",
                  "2020":"/home/juju/geodata/gisco/basic_services/education_2020_3035_20260421.gpkg"},
    "evrp": {"2023":"/home/juju/geodata/gisco/recharging_points/evrp_2023_3035.gpkg",
             "2024":"/home/juju/geodata/gisco/recharging_points/evrp_2024_3035.gpkg",
             "2025":"/home/juju/geodata/gisco/recharging_points/evrp_2025_3035.gpkg"}
}

dataset_versions = {
    "education": {"2020":"v2026_04", "2023":"v2026_04"},
    "healthcare": {"2020":"v2026_04", "2023":"v2026_04"},
    "evrp":  {"2023":"v2026_05", "2024":"v2026_05", "2025":"v2026_06"},
}


tomtom_data_folder = "/home/juju/geodata/tomtom/"
tomtom_datasets = {
    "2020": tomtom_data_folder + "tomtom201912.gpkg",
    "2023": tomtom_data_folder + "tomtom202312.gpkg",
    "2024": tomtom_data_folder + "tomtom202312.gpkg",
    "2025": tomtom_data_folder + "tomtom202512.gpkg"
}


# define output bounding box
# whole europe
bbox = [ 900000, 900000, 6600000, 5500000 ]
#luxembourg
#bbox = [4030000, 2930000, 4060000, 2960000]
#greece
#bbox = [ 5000000, 1500000, 5500000, 2000000 ]

country_gpkg = '/home/juju/geodata/gisco/CNTR_RG_100K_2024_3035.gpkg'
nuts_gpkg = '/home/juju/geodata/gisco/NUTS_RG_100K_2024_3035.gpkg'



# define country codes for the countries covered, depending on the country and the year
def get_countries_covered(service:str, year:str):
    cnts = ["AT", "BE", "BG", "HR", "CY", "CZ", "DE", "DK", "EE", "FI", "FR",
            "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO" ]
    #exclude: ["CH", "RS", "BA", "MK", "AL", "ME", "MD"],
    if service == "healthcare": cnts.append("CH")
    if year == "2023": cnts.append("AL")
    return cnts


# folder where to copy the results for deployment
target_folder = "/home/juju/pCloudDrive"
