
# define country codes for the countries covered, depending on the country and the year
def get_countries_covered(service:str, year:str):
    cnts = ["AT", "BE", "BG", "HR", "CY", "CZ", "DE", "DK", "EE", "FI", "FR",
            "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO" ]
    #exclude: ["CH", "RS", "BA", "MK", "AL", "ME", "MD"],
    if service == "healthcare": cnts.append("CH")
    if year == "2023": cnts.append("AL")
    return cnts
