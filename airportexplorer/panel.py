import requests
from flask import (Blueprint, render_template, request,redirect,url_for)
from flask_login import login_required
from airportexplorer import cache
from decouple import config
from airportexplorer.database import get_database

AIRPORTDB_URL = "https://airportdb.io/api/v1/airport/{}?apiToken="+ config("AIRPORTDB_API_TOKEN")

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
    airports = get_database().airports.find()
    return render_template("dashboard/airports/airport-list.html", airports=airports)


@bp.route("/countries-list/")
@login_required
def country_list():
    countries = get_database().countries.find()
    return render_template("dashboard/countries/country-list.html", countries=countries)

@bp.route("/airports/quick-add/", methods=["POST"])
@login_required
def quick_airport_add():
    if request.method == "POST":
        iata_code = request.form.get("iata_code")
        icao_code = request.form.get("icao_code")
        
        if len(icao_code)> 0:
            rs = requests.get(AIRPORTDB_URL.format(icao_code))
            
            if rs.status_code == 200:
                data = rs.json()
               
                country_code = data["iso_country"]
                region_code = data['iso_region']
                
                country_count  = get_database().countries.count_documents({"code": country_code})
                
                if country_count == 0:
                    # Country Doesn't exist
                    country_info_rs = requests.get("https://restcountries.com/v3.1/alpha/{}".format(country_code)) 
                    
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
                            "regions":[
                                {
                                    "code": region_code,
                                    "name": data["region"]['name'],
                                    "local_code": data["region"]['local_code'],
                                    "iso_country": data["region"]['iso_country'],
                                    "continent": data["region"]['continent'],
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
                                    ]
                                }
                            ]
                            
                        }
                        get_database().countries.insert_one(country_data)
               
                else:
                    # Add the region
                    region_count = get_database().countries.count_documents({"regions.code": region_code})
                    if region_count == 0:
                        region_data = {
                                    "code": region_code,
                                    "name": data["region"]['name'],
                                    "local_code": data["region"]['local_code'],
                                    "iso_country": data["region"]['iso_country'],
                                    "continent": data["region"]['continent'],
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
                                    ]
                                }
                        get_database().countries.update_one({"code": country_code}, {"$push": {"regions": region_data}})
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
                            "icao_code": data["icao_code"]
                        }
                        
                        get_database().countries.update_one({"code": country_code, "regions.code": region_code}, {"$push": {"regions.$.airports": airport_data}})
                                           

        return redirect(url_for("panel.airport_list"))
                
            
        
    countries = get_database().countries.find()
    return render_template("dashboard/countries/country-list.html", countries=countries)