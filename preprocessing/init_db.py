from urllib.parse import quote_plus

import pandas as pd
import requests
from decouple import config
from pymongo.mongo_client import MongoClient

MONGO_USERNAME = config("MONGO_USERNAME", default="")
MONGO_PASSWORD = config("MONGO_PASSWORD", default="")
MONGO_DATABASE = config("MONGO_DATABASE", default="airportexplorer")
username = quote_plus(MONGO_USERNAME)
password = quote_plus(MONGO_PASSWORD)

MONGODB_URI = (
    "mongodb://"
    + username
    + ":"
    + password
    + "@172.232.220.157:27017,172.232.217.83:27017,172.232.217.81:27017/airportexplorer?authSource=admin&replicaSet=rs0&retryWrites=true&w=3&r=2"
)

AIRPORTDB_URL = "https://airportdb.io/api/v1/airport/{}?apiToken=" + config(
    "AIRPORTDB_API_TOKEN"
)

mongoclient = MongoClient(MONGODB_URI)
database = mongoclient.get_database(MONGO_DATABASE)

data = pd.read_csv("data/airports.csv", usecols=["ident"])

for datum in data["ident"]:
    try:
        print(datum)
        rs = requests.get(AIRPORTDB_URL.format(datum))

        if rs.status_code == 200:
            data = rs.json()

            country_code = data["iso_country"]
            region_code = data["iso_region"]

            country_count = database.countries.count_documents({"code": country_code})

            if country_count == 0:
                # Country Doesn't exist
                country_info_rs = requests.get(
                    "https://restcountries.com/v3.1/alpha/{}".format(country_code)
                )

                if country_info_rs.status_code == 200:
                    country_info = country_info_rs.json()[0]
                    country_data = {
                        "code": country_code,
                        "name": country_info["name"]["common"],
                        "official_name": country_info["name"]["official"],
                        "capital": country_info["capital"][0],
                        "area": country_info["area"],
                        "population": country_info["population"],
                        "region": country_info["region"],
                        "subregion": country_info["subregion"],
                        "flag": country_info["flag"],
                        "currencies": country_info["currencies"],
                        "languages": country_info["languages"],
                        "timezones": country_info["timezones"],
                        "regions": [
                            {
                                "code": region_code,
                                "name": data["region"]["name"],
                                "local_code": data["region"]["local_code"],
                                "iso_country": data["region"]["iso_country"],
                                "continent": data["region"]["continent"],
                                "airports": [
                                    {
                                        "ident": data["ident"],
                                        "type": data["type"],
                                        "name": data["name"],
                                        "latitude_deg": data["latitude_deg"],
                                        "longitude_deg": data["longitude_deg"],
                                        "elevation_ft": data["elevation_ft"],
                                        "continent": data["continent"],
                                        "iso_country": data["iso_country"],
                                        "iso_region": data["iso_region"],
                                        "municipality": data["municipality"],
                                        "gps_code": data["gps_code"],
                                        "iata_code": data["iata_code"],
                                        "local_code": data["local_code"],
                                        "home_link": data["home_link"],
                                        "icao_code": data["icao_code"],
                                    }
                                ],
                            }
                        ],
                    }
                    database.countries.insert_one(country_data)
            else:
                # Add the region
                region_count = database.countries.count_documents(
                    {"regions.code": region_code}
                )
                if region_count == 0:
                    region_data = {
                        "code": region_code,
                        "name": data["region"]["name"],
                        "local_code": data["region"]["local_code"],
                        "iso_country": data["region"]["iso_country"],
                        "continent": data["region"]["continent"],
                        "airports": [
                            {
                                "ident": data["ident"],
                                "type": data["type"],
                                "name": data["name"],
                                "latitude_deg": data["latitude_deg"],
                                "longitude_deg": data["longitude_deg"],
                                "elevation_ft": data["elevation_ft"],
                                "continent": data["continent"],
                                "iso_country": data["iso_country"],
                                "iso_region": data["iso_region"],
                                "municipality": data["municipality"],
                                "gps_code": data["gps_code"],
                                "iata_code": data["iata_code"],
                                "local_code": data["local_code"],
                                "home_link": data["home_link"],
                                "icao_code": data["icao_code"],
                            }
                        ],
                    }
                    database.countries.update_one(
                        {"code": country_code}, {"$push": {"regions": region_data}}
                    )
                else:
                    # Add the airport

                    airport_data = {
                        "ident": data["ident"],
                        "type": data["type"],
                        "name": data["name"],
                        "latitude_deg": data["latitude_deg"],
                        "longitude_deg": data["longitude_deg"],
                        "elevation_ft": data["elevation_ft"],
                        "continent": data["continent"],
                        "iso_country": data["iso_country"],
                        "iso_region": data["iso_region"],
                        "municipality": data["municipality"],
                        "gps_code": data["gps_code"],
                        "iata_code": data["iata_code"],
                        "local_code": data["local_code"],
                        "home_link": data["home_link"],
                        "icao_code": data["icao_code"],
                    }

                    database.countries.update_one(
                        {"code": country_code, "regions.code": region_code},
                        {"$push": {"regions.$.airports": airport_data}},
                    )
    except Exception:
        print("Error")
        continue
