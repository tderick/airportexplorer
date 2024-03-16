from flask import Blueprint, render_template, request, url_for, redirect

from airportexplorer.database import get_database

from airportexplorer.tasks import compute_reviews_and_rating

bp = Blueprint("home", __name__, url_prefix="/")

@bp.route("/")
def home():
    # compute_reviews_and_rating.delay()
    
    return render_template("home/home.html")


@bp.route("/airport-search/")
def airport_result():
    query = request.args.get("q")

    pageNumber = (
        int(request.args.get("pageNumber")) if request.args.get("pageNumber") else 1
    )
    pageSize = int(request.args.get("pageSize")) if request.args.get("pageSize") else 10

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
            "$match": {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"iata_code": {"$regex": query, "$options": "i"}},
                    {"icao_code": {"$regex": query, "$options": "i"}},
                ]
            }
        },
        {
            "$facet": {
                "data": [{"$skip": (pageNumber - 1) * pageSize}, {"$limit": pageSize}],
                "metadata": [
                    {"$group": {"_id": None, "count": {"$sum": 1}}},
                    {
                        "$project": {
                            "_id": 0,
                            "count": 1,
                            "totalPages": {"$ceil": {"$divide": ["$count", pageSize]}},
                        }
                    },
                ],
            }
        },
    ]

    result = list(get_database().countries.aggregate(pipeline))

    next_url = url_for(
        "home.airport_result", pageNumber=pageNumber + 1, pageSize=pageSize, q=query
    )
    prev_url = url_for(
        "home.airport_result", pageNumber=pageNumber - 1, pageSize=pageSize, q=query
    )

    return render_template(
        "home/airport-result.html",
        query=query,
        airports=result,
        pageNumber=pageNumber,
        pageSize=pageSize,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/airport-details/")
def airport_details():
    airport_ident = request.args.get("ident")

    pipeline = [
        {"$unwind": "$regions"},
        {"$match": {"regions.airports.ident": airport_ident}},
        {
            "$addFields": {
                "regions.airports": {
                    "$filter": {
                        "input": "$regions.airports",
                        "as": "airport",
                        "cond": {"$eq": ["$$airport.ident", airport_ident]},
                    }
                }
            }
        },
    ]

    airport = list(get_database().countries.aggregate(pipeline))
    
    if len(airport) == 0:
        return redirect(url_for("home.home"))
    
    return render_template("home/airport-details.html", airport=airport[0])

@bp.route("/airport-by-country/")
def airport_by_country():
    query = request.args.get("q") if request.args.get("q") else "Italy"

    pageNumber = (
        int(request.args.get("pageNumber")) if request.args.get("pageNumber") else 1
    )
    pageSize = int(request.args.get("pageSize")) if request.args.get("pageSize") else 10

    pipeline = [
        {"$match": {"name": {"$regex": query, "$options": "i"}}},  # Match the specified country
        {"$unwind": "$regions"},  # Unwind the regions array
        {"$group": {"_id": "$regions.name", "totalAirports": {"$sum": {"$size": "$regions.airports"}}, }},  # Group by region name and count the number of airports
         {"$sort": {"totalAirports": -1}},  # Sort by totalAirports in descending order
        {"$facet": {
            "data": [
                {"$skip": (pageNumber - 1) * pageSize},  # Skip to the specified page
                {"$limit": pageSize}  # Limit the number of results per page
            ],
            "metadata": [
                {"$count": "count"},  # Count the total number of regions
                {"$project": {
                    "_id": 0,
                    "count": 1,
                    "totalPages": {"$ceil": {"$divide": ["$count", pageSize]}}  # Calculate the total number of pages
                }}
            ]
        }}
    ]

    result = list(get_database().countries.aggregate(pipeline))
    
    
    next_url = url_for(
        "home.airport_by_country", pageNumber=pageNumber + 1, pageSize=pageSize, q=query
    )
    prev_url = url_for(
        "home.airport_by_country", pageNumber=pageNumber - 1, pageSize=pageSize, q=query
    )
    
    return render_template("home/airport-by-country.html", query=query, airports=result, pageNumber=pageNumber, pageSize=pageSize, next_url=next_url, prev_url=prev_url)
    

@bp.route("/reviews-list/")
def reviews_list():
    query = request.args.get("airport")

    pageNumber = (
        int(request.args.get("pageNumber")) if request.args.get("pageNumber") else 1
    )
    pageSize = int(request.args.get("pageSize")) if request.args.get("pageSize") else 5

    pipeline = [
        {"$match": {"airport": query}},
        {
            "$facet": {
                "data": [{"$skip": (pageNumber - 1) * pageSize}, {"$limit": pageSize}],
                "metadata": [
                    {"$group": {"_id": None, "count": {"$sum": 1}}},
                    {
                        "$project": {
                            "_id": 0,
                            "count": 1,
                            "totalPages": {"$ceil": {"$divide": ["$count", pageSize]}},
                        }
                    },
                ],
            }
        },
    ]

    result = list(get_database().reviews.aggregate(pipeline))

    next_url = url_for(
        "home.reviews_list", pageNumber=pageNumber + 1, pageSize=pageSize, airport=query
    )
    prev_url = url_for(
        "home.reviews_list", pageNumber=pageNumber - 1, pageSize=pageSize, airport=query
    )
    

    return render_template("home/reviews-list.html",
        reviews=result,
        pageNumber=pageNumber,
        pageSize=pageSize,
        next_url=next_url,
        prev_url=prev_url,
        query=query
        )


@bp.route("/like-review/")    
def like_review():
    pass