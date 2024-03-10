from flask import Blueprint, render_template, request
from airportexplorer.database import get_database

bp = Blueprint("home", __name__, url_prefix="/")


@bp.route("/")
def home():
    return render_template("home/home.html")

@bp.route("/airport-search/")
def airport_result():
    query = request.args.get('q')
    
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
                "municipality": "$regions.airports.municipality"
            }
        },
        {
            "$match": {
                "$or": [
                    {"name": {"$regex": query, "$options": 'i'}},
                    {"iata_code": {"$regex": query, "$options": 'i'}},
                    {"icao_code": {"$regex": query, "$options": 'i'}}
                ]
            }
        }
    ]
    airports = list(get_database().countries.aggregate(pipeline))
    
    return render_template("home/airport-result.html", query=query, airports=airports)
