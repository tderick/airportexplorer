from flask import Blueprint, render_template, request, url_for
from airportexplorer.database import get_database

bp = Blueprint("home", __name__, url_prefix="/")


@bp.route("/")
def home():
    return render_template("home/home.html")

@bp.route("/airport-search/")
def airport_result():
    query = request.args.get('q')
    
    # pipeline = [
    #     {"$unwind": "$regions"},
    #     {"$unwind": "$regions.airports"},
    #     {
    #         "$project": {
    #             "_id": 0,
    #             "ident": "$regions.airports.ident",
    #             "name": "$regions.airports.name",
    #             "type": "$regions.airports.type",
    #             "iata_code": "$regions.airports.iata_code",
    #             "icao_code": "$regions.airports.icao_code",
    #             "iso_country": "$regions.airports.iso_country",
    #             "continent": "$regions.airports.continent",
    #             "municipality": "$regions.airports.municipality"
    #         }
    #     },
    #     {
    #         "$match": {
    #             "$or": [
    #                 {"name": {"$regex": query, "$options": 'i'}},
    #                 {"iata_code": {"$regex": query, "$options": 'i'}},
    #                 {"icao_code": {"$regex": query, "$options": 'i'}}
    #             ]
    #         }
    #     }
    # ]
    # airports = list(get_database().countries.aggregate(pipeline))
    pageNumber = int(request.args.get("pageNumber")) if request.args.get("pageNumber") else 1
    pageSize = int(request.args.get("pageSize")) if request.args.get("pageSize")  else 10 


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
        },
        {"$facet": {
            "data": [
                {"$skip": (pageNumber - 1) * pageSize},
                {"$limit": pageSize}
            ],
            "metadata": [
                {"$group": {"_id": None, "count": {"$sum": 1}}},
                {"$project": {"_id": 0, "count": 1, "totalPages": {"$ceil": {"$divide": ["$count", pageSize]}}}}
            ]
        }}
    ]

    result = list(get_database().countries.aggregate(pipeline))

    next_url = url_for('home.airport_result', pageNumber=pageNumber+1, pageSize=pageSize, q=query) 
    prev_url = url_for('home.airport_result', pageNumber=pageNumber-1, pageSize=pageSize, q=query) 
    
    
    return render_template("home/airport-result.html", query=query, airports=result,pageNumber=pageNumber, pageSize=pageSize, next_url=next_url, prev_url=prev_url)


@bp.route("/airport-details/")
def airport_details():
    airport_ident = request.args.get("ident")
    
    pipeline = [
        {"$unwind": "$regions"},
        {"$match": {"regions.airports.ident": airport_ident}},
        {"$addFields": {
            "regions.airports": {
                "$filter": {
                    "input": "$regions.airports",
                    "as": "airport",
                    "cond": {"$eq": ["$$airport.ident", airport_ident]}
                }
            }
        }
        }
    ]
    
    airport = list(get_database().countries.aggregate(pipeline))

    return render_template("home/airport-details.html", airport=airport[0])
