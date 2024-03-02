from flask import (Blueprint, render_template)
from flask_login import login_required
from airportexplorer import cache

from airportexplorer.database import get_database


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
@cache.cached(timeout=50)
def country_list():
    countries = get_database().countries.find()
    return render_template("dashboard/countries/country-list.html", countries=countries)