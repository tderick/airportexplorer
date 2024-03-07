import requests
from decouple import config
from flask import Blueprint, redirect, render_template, request, url_for, jsonify
from flask_login import login_required
from bson.objectid import ObjectId

from airportexplorer import cache
from airportexplorer.database import get_database

AIRPORTDB_URL = "https://airportdb.io/api/v1/airport/{}?apiToken=" + config(
    "AIRPORTDB_API_TOKEN"
)

bp = Blueprint("panel", __name__, url_prefix="/manage")


@bp.route("/")
@login_required
@cache.cached(timeout=50)
def dashboard():
    return render_template("dashboard/dashboard-base.html")


@bp.route("/users-list/")
@login_required
@cache.cached(timeout=50)
def user_list():
    users = get_database().users.find()
    return render_template("dashboard/users/user-list.html", users=users)


@bp.route("/airports-list/")
@login_required
@cache.cached(timeout=50)
def airport_list():
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
        }
    ]

    airports = get_database().countries.aggregate(pipeline)
    
    # # import pdb; pdb.set_trace()
    

    # airports = get_database().countries.find(
    #     {"regions.airports": {"$exists": True}},
    #     {
    #         "regions.airports.name": 1,
    #         "regions.airports.type": 1,
    #         "regions.airports.iata_code": 1,
    #         "regions.airports.icao_code": 1,
    #         "regions.airports.iso_country": 1,
    #         "regions.airports.continent": 1,
    #         "regions.airports.municipality": 1,
    #     },
    # )
    
  
    return render_template(
        "dashboard/airports/airport-list.html",
        airports=airports
    )


@bp.route("/countries-list/")
@login_required
def country_list():
    countries = get_database().countries.find(
        {},
        {
            "name": 1,
            "code": 1,
            "official_name": 1,
            "capital": 1,
            "population": 1,
            "region": 1,
            "subregion": 1,
            "area": 1,
        },
    )
    return render_template("dashboard/countries/country-list.html", countries=countries)

@bp.route("/countries/country-form/")
@login_required
def country_add_form():
    country_code = request.args.get("code")
    
    if country_code is not None:
        country = get_database().countries.find_one(
            {"code":country_code},
            {
                "name": 1,
                "code": 1,
                "official_name": 1,
                "capital": 1,
                "population": 1,
                "region": 1,
                "subregion": 1,
                "area": 1,
                "currencies": 1
            },
        )
        return render_template("dashboard/countries/country-form.html", country=country)
    else:
        return render_template("dashboard/countries/country-form.html")

@bp.route("/countries/create-or-edit", methods=['POST'])
@login_required
def create_or_edit_country():
    
    data = {
        "code": request.form.get("code"),
        "name": request.form.get("name"),
        "official_name": request.form.get("official_name"),
        "capital": request.form.get("capital"),
        "area": request.form.get("area"),
        "population": request.form.get("population"),
        "region": request.form.get("region"),
        "subregion": request.form.get("subregion")   
    }
    
    _id = request.form.get("_id")
    
    if len(_id) == 0:  
        get_database().countries.insert_one(data)
    else:    
        get_database().countries.update_one({"_id":ObjectId(_id)},{"$set": data})
        
    return redirect(url_for("panel.country_list"))


@bp.route("/region-list/")
@login_required
def region_list():
    regions = get_database().countries.find(
        {"regions": {"$exists": True}},
        {
            "regions.name": 1,
            "regions.code": 1,
             "regions.local_code": 1,
            "regions.iso_country": 1,
            "regions.continent": 1,
        },
    )
    return render_template("dashboard/regions/region-list.html", regions=regions)

@bp.route("/regions/region-form/")
@login_required
def region_add_update_form():
    region_code = request.args.get("code")
    
    if region_code is not None:
        pipeline = [
            {"$unwind": "$regions"},  # Deconstruct the array
            {"$match": {"regions.code": region_code}},  # Filter based on inner document criteria
            {"$project": {
                "_id": 0, 
                "regions.code": 1, 
                "regions.name": 1, 
                "regions.iso_country": 1, 
                "regions.local_code": 1, 
                "regions.continent": 1
            }}  
        ]

        region_cursor = get_database().countries.aggregate(pipeline)
        
        region = list(region_cursor)[0]
        
        return render_template("dashboard/regions/region-form.html", region=region['regions'])
    else:
        return render_template("dashboard/regions/region-form.html")

@bp.route("/regions/create-or-edit", methods=['POST'])
@login_required
def create_or_edit_region():
    
    data = {
        "code": request.form.get("code"),
        "name": request.form.get("name"),
        "iso_country": request.form.get("iso_country"),
        "local_code": request.form.get("local_code"),
        "continent": request.form.get("continent"),
    }
    
    old_code = request.form.get("old_code")
    iso_country = request.form.get("iso_country")
    
    if len(old_code) == 0:  
        # New
        get_database().countries.update_one(
                            {"code": iso_country}, 
                            {"$push": {"regions": data}}
                        )
    else:    
        get_database().countries.update_one(
                            {"regions.code": old_code}, 
                            {"$set": {
                                "regions.$.code": data["code"],
                                "regions.$.name": data["name"],
                                "regions.$.iso_country": data["iso_country"],
                                "regions.$.local_code": data["local_code"],
                                "regions.$.continent": data["continent"]
                                }
                             }
                        )
    return redirect(url_for("panel.region_list"))

@bp.route("/airport/airport-form/")
@login_required
def airport_add_update_form():
    # region_code = request.args.get("code")
    
    # if region_code is not None:
    #     pipeline = [
    #         {"$unwind": "$regions"},  # Deconstruct the array
    #         {"$match": {"regions.code": region_code}},  # Filter based on inner document criteria
    #         {"$project": {
    #             "_id": 0, 
    #             "regions.code": 1, 
    #             "regions.name": 1, 
    #             "regions.iso_country": 1, 
    #             "regions.local_code": 1, 
    #             "regions.continent": 1
    #         }}  
    #     ]

    #     region_cursor = get_database().countries.aggregate(pipeline)
        
    #     region = list(region_cursor)[0]
        
    #     return render_template("dashboard/regions/region-form.html", region=region['regions'])
    # else:
    return render_template("dashboard/airports/airport-form.html")
    

@bp.route("/airport/create-or-edit", methods=['POST'])
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
    
    # import pdb; pdb.set_trace()


    if len(old_ident) == 0:  
        # New
        get_database().countries.update_one(
                            {"code": country_code, "regions.code": iso_region},
                            {"$push": {"regions.$.airports": airport_data}},
                        )

    # else:    
    #     get_database().countries.update_one(
    #                         {"regions.code": old_code}, 
    #                         {"$set": {
    #                             "regions.$.code": data["code"],
    #                             "regions.$.name": data["name"],
    #                             "regions.$.iso_country": data["iso_country"],
    #                             "regions.$.local_code": data["local_code"],
    #                             "regions.$.continent": data["continent"]
    #                             }
    #                          }
    #                     )
    return redirect(url_for("panel.airport_list"))


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

            if res.status_code == 200:
                icao_code = res.json()["icao"]

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
                        return redirect(url_for("panel.airport_list"))
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

    return redirect(url_for("panel.airport_list"))


@bp.route("/airports/edit/")
def airport_edit():
    pass

@bp.route("/airports/delete/", methods=["POST"])
def airport_delete():
    if request.form.get("_method") =="delete":
        airport_id = request.args.get("airport_id")
        get_database().countries.update_one(
                            {"regions.airports.ident": airport_id},
                            {"$pull": {"regions.$[].airports":{"ident":airport_id} }} )
        
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "error"}), 400



@bp.route("/regions/delete/", methods=["POST"])
def region_delete():
    if request.form.get("_method") =="delete":
        code = request.args.get("code")
        get_database().countries.update_one(
                            {"regions.code": code},
                            {"$pull": {"regions":{"code":code} }} )
        
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "error"}), 400

@bp.route("/country/delete/", methods=["POST"])
def country_delete():
    if request.form.get("_method") =="delete":
        code = request.args.get("code")
        get_database().countries.delete_one({"code": code})
        
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "error"}), 400