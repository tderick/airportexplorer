import requests
from decouple import config
from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import login_required

from airportexplorer.database import get_database

AIRPORTDB_URL = "https://airportdb.io/api/v1/airport/{}?apiToken=" + config(
    "AIRPORTDB_API_TOKEN"
)

bp = Blueprint("airport", __name__, url_prefix="/manage")


@bp.route("/airport/airport-form/")
@login_required
def airport_add_update_form():
    airport_ident = request.args.get("ident")

    countries = get_database().countries.find({}, {"_id": 0, "name": 1, "code": 1})
    regions = get_all_regions()

    if airport_ident is not None:
        # pipeline = [
        #     {"$unwind": "$regions"},  # Deconstruct the regions array
        #     {
        #         "$project": {
        #             "filteredValue": {
        #                 "$filter": {
        #                     "input": "$regions.airports",
        #                     "as": "airport",
        #                     "cond": {"$eq": ["$$airport.ident", airport_ident]},
        #                 }
        #             }
        #         }
        #     },
        # ]
        pipeline = [
            {"$unwind": "$regions"},
            {"$unwind": "$regions.airports"},
            {
                "$project": {
                    "_id": 0,
                    "ident": "$regions.airports.ident",
                    "name": "$regions.airports.name",
                    "type": "$regions.airports.type",
                    "iata_code": "$regions.airports.iata_code",
                    "icao_code": "$regions.airports.icao_code",
                    "iso_country": "$regions.airports.iso_country",
                    "continent": "$regions.airports.continent",
                    "municipality": "$regions.airports.municipality",
                    "latitude_deg": "$regions.airports.latitude_deg",
                    "longitude_deg": "$regions.airports.longitude_deg",
                    "elevation_ft": "$regions.airports.elevation_ft",
                    "home_link": "$regions.airports.home_link",
                    "gps_code": "$regions.airports.gps_code",
                    "local_code": "$regions.airports.local_code",
                    "iso_region": "$regions.airports.iso_region",
                }
            },
            {"$match": {"ident": airport_ident}},
        ]
        airport = list(get_database().countries.aggregate(pipeline))

        return render_template(
            "dashboard/airports/airport-form.html",
            airport=airport[0],
            countries=countries,
            regions=regions,
        )
    else:
        return render_template(
            "dashboard/airports/airport-form.html", countries=countries, regions=regions
        )


@bp.route("/airport/create-or-edit", methods=["POST"])
@login_required
def create_or_edit_airport():

    airport_data = {
        "ident": request.form.get("ident"),
        "type": request.form.get("type"),
        "name": request.form.get("name"),
        "latitude_deg": request.form.get("latitude_deg"),
        "longitude_deg": request.form.get("longitude_deg"),
        "elevation_ft": request.form.get("elevation_ft"),
        "continent": request.form.get("continent"),
        "iso_country": request.form.get("iso_country"),
        "iso_region": request.form.get("iso_region"),
        "municipality": request.form.get("municipality"),
        "gps_code": request.form.get("gps_code"),
        "iata_code": request.form.get("iata_code"),
        "local_code": request.form.get("local_code"),
        "home_link": request.form.get("home_link"),
        "icao_code": request.form.get("icao_code"),
    }

    iso_region = request.form.get("iso_region")
    country_code = request.form.get("iso_country")
    old_ident = request.form.get("old_ident")

    if len(old_ident) == 0:
        # New
        get_database().countries.update_one(
            {"code": country_code, "regions.code": iso_region},
            {"$push": {"regions.$.airports": airport_data}},
        )
    else:
        get_database().countries.update_one(
            {"regions.airports.ident": old_ident},
            {"$set": {"regions.$[].airports.$[xxx]": airport_data}},
            array_filters=[{"xxx.ident": old_ident}],
        )
    return redirect(url_for("airport.airport_list", q=request.form.get("ident")))


@bp.route("/airports/quick-add/", methods=["POST"])
@login_required
def quick_airport_add():
    if request.method == "POST":
        iata_code = request.form.get("iata_code")
        icao_code = request.form.get("icao_code")

        if iata_code is not None:
            res = requests.get(
                "https://www.airport-data.com/api/ap_info.json?iata={}".format(
                    iata_code.upper()
                ),
                verify=False,
            )

            if res.status_code == 200 and "icao" in res.json():
                icao_code = res.json()["icao"]
            else:
                flash("Test")
                return redirect(
                    url_for("airport.airport_list"),
                )

        if len(icao_code) > 0:
            rs = requests.get(AIRPORTDB_URL.format(icao_code.upper()))

            if rs.status_code == 200:
                data = rs.json()

                country_code = data["iso_country"]
                region_code = data["iso_region"]

                country_count = get_database().countries.count_documents(
                    {"code": country_code}
                )

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
                            "flags": country_info["flags"],
                            "currencies": country_info["currencies"],
                            "languages": country_info["languages"],
                            "borders": country_info["borders"],
                            "timezones": country_info["timezones"],
                            "tld": country_info["tld"],
                            "altSpellings": country_info["altSpellings"],
                            "latlng": country_info["latlng"],
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
                        get_database().countries.insert_one(country_data)
                        return redirect(url_for("airport.airport_list"))
                else:
                    # Add the region
                    region_count = get_database().countries.count_documents(
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
                        get_database().countries.update_one(
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

                        get_database().countries.update_one(
                            {"code": country_code, "regions.code": region_code},
                            {"$push": {"regions.$.airports": airport_data}},
                        )

    return redirect(url_for("airport.airport_list"))


@bp.route("/airports/delete/", methods=["POST"])
def airport_delete():
    if request.form.get("_method") == "delete":
        airport_id = request.args.get("airport_id")
        get_database().countries.update_one(
            {"regions.airports.ident": airport_id},
            {"$pull": {"regions.$[].airports": {"ident": airport_id}}},
        )

        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error"}), 400


@bp.route("/airports-list/")
@login_required
def airport_list():

    search = request.args.get("q")

    pageNumber = (
        int(request.args.get("pageNumber")) if request.args.get("pageNumber") else 1
    )
    pageSize = int(request.args.get("pageSize")) if request.args.get("pageSize") else 10

    if search is not None:
        pipeline = [
            {"$unwind": "$regions"},
            {"$unwind": "$regions.airports"},
            {
                "$match": {
                    "$or": [
                        {"regions.airports.ident": {"$regex": search, "$options": "i"}},
                        {"regions.airports.name": {"$regex": search, "$options": "i"}},
                        {"regions.airports.type": {"$regex": search, "$options": "i"}},
                        {
                            "regions.airports.iata_code": {
                                "$regex": search,
                                "$options": "i",
                            }
                        },
                        {
                            "regions.airports.icao_code": {
                                "$regex": search,
                                "$options": "i",
                            }
                        },
                        {
                            "regions.airports.iso_country": {
                                "$regex": search,
                                "$options": "i",
                            }
                        },
                        {
                            "regions.airports.continent": {
                                "$regex": search,
                                "$options": "i",
                            }
                        },
                        {
                            "regions.airports.municipality": {
                                "$regex": search,
                                "$options": "i",
                            }
                        },
                    ]
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "ident": "$regions.airports.ident",
                    "name": "$regions.airports.name",
                    "type": "$regions.airports.type",
                    "iata_code": "$regions.airports.iata_code",
                    "icao_code": "$regions.airports.icao_code",
                    "iso_country": "$regions.airports.iso_country",
                    "continent": "$regions.airports.continent",
                    "municipality": "$regions.airports.municipality",
                }
            },
            {
                "$facet": {
                    "metadata": [
                        {"$group": {"_id": None, "count": {"$sum": 1}}},
                        {
                            "$project": {
                                "_id": 0,
                                "count": 1,
                                "totalPages": {
                                    "$ceil": {"$divide": ["$count", pageSize]}
                                },
                            }
                        },
                    ],
                    "data": [
                        {"$skip": (pageNumber - 1) * pageSize},
                        {"$limit": pageSize},
                    ],
                }
            },
        ]

    else:
        pipeline = [
            {"$unwind": "$regions"},
            {"$unwind": "$regions.airports"},
            {
                "$project": {
                    "_id": 0,
                    "ident": "$regions.airports.ident",
                    "name": "$regions.airports.name",
                    "type": "$regions.airports.type",
                    "iata_code": "$regions.airports.iata_code",
                    "icao_code": "$regions.airports.icao_code",
                    "iso_country": "$regions.airports.iso_country",
                    "continent": "$regions.airports.continent",
                    "municipality": "$regions.airports.municipality",
                }
            },
            {
                "$facet": {
                    "metadata": [
                        {"$group": {"_id": None, "count": {"$sum": 1}}},
                        {
                            "$project": {
                                "_id": 0,
                                "count": 1,
                                "totalPages": {
                                    "$ceil": {"$divide": ["$count", pageSize]}
                                },
                            }
                        },
                    ],
                    "data": [
                        {"$skip": (pageNumber - 1) * pageSize},
                        {"$limit": pageSize},
                    ],
                }
            },
        ]

    result = list(get_database().countries.aggregate(pipeline))

    next_url = url_for(
        "airport.airport_list", pageNumber=pageNumber + 1, pageSize=pageSize
    )
    prev_url = url_for(
        "airport.airport_list", pageNumber=pageNumber - 1, pageSize=pageSize
    )

    return render_template(
        "dashboard/airports/airport-list.html",
        airports=result,
        pageNumber=pageNumber,
        pageSize=pageSize,
        next_url=next_url,
        prev_url=prev_url,
    )


def get_all_regions():
    pipeline = [
        {"$unwind": "$regions"},
        {
            "$project": {
                "_id": 0,
                "region_name": "$regions.name",
                "region_code": "$regions.code",
            }
        },
    ]
    return list(get_database().countries.aggregate(pipeline))
