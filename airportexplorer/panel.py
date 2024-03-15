from flask import Blueprint,redirect, render_template, request, url_for
from flask_login import current_user, login_required

from airportexplorer.database import get_database

bp = Blueprint("panel", __name__, url_prefix="/manage")


@bp.before_request
def _check_rights():
    """Chef if the user is admin or not. If not, redirect to home page."""
    if not current_user.is_admin:
        return redirect(url_for("home.home"))


def count_airport_of_different_size():
    pipeline = [
        {"$unwind": "$regions"},
        {"$unwind": "$regions.airports"},
        {"$group": {"_id": "$regions.airports.type", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "airportType": "$_id", "count": 1}},
    ]

    return list(get_database().countries.aggregate(pipeline))


def top_7_countries_with_high_number_of_airports():
    pipeline = [
        {"$unwind": "$regions"},
        {"$unwind": "$regions.airports"},
        {
            "$group": {
                "_id": "$code",  # Assuming "code" field represents the country code
                "country_name": {"$first": "$name"},
                "capital": {"$first": "$capital"},
                "area": {"$first": "$area"},
                "population": {"$first": "$population"},
                "totalAirports": {"$sum": 1},
            }
        },
        {"$sort": {"totalAirports": -1}},  # Sort by totalAirports in descending order
        {"$limit": 7},  # Limit the result to top 7 countries
        {
            "$project": {
                "_id": 0,
                "country_name": 1,
                "capital": 1,
                "totalAirports": 1,
                "area": 1,
                "population": 1,
            }
        },
    ]

    return list(get_database().countries.aggregate(pipeline))


@bp.route("/")
@login_required
def dashboard():
    nbre_countries = get_database().countries.count_documents({})
    nbre_regions = list(
        get_database().countries.aggregate(
            [{"$unwind": "$regions"}, {"$count": "count"}]
        )
    )
    nbre_airports = list(
        get_database().countries.aggregate(
            [
                {"$unwind": "$regions"},
                {"$unwind": "$regions.airports"},
                {"$count": "count"},
            ]
        )
    )

    # Aiport of different types
    airport_of_different_size = count_airport_of_different_size()

    # Top 7 airport with the high number of aiport
    high_number_of_airports = top_7_countries_with_high_number_of_airports()

    return render_template(
        "dashboard/dashboard.html",
        nbre_countries=nbre_countries,
        nbre_regions=nbre_regions,
        nbre_airports=nbre_airports,
        airport_of_different_size=airport_of_different_size,
        high_number_of_airports=high_number_of_airports,
    )


@bp.route("/users-list/")
@login_required
def user_list():
    users = get_database().users.find()
    return render_template("dashboard/users/user-list.html", users=users)
