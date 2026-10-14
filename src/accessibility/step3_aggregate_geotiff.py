



def aggregate_geotiff(params, services, years):
    # TODO
    for service in services:
        for year in years:
            print(datetime.now(), service, year)
            combine_to_geotiff(
                params=params,
                services=[service],
                years=[year],
                do_combination=False,
                do_aggregation=True
            )
