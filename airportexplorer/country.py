from bson.objectid import ObjectId
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from airportexplorer.database import get_database

bp = Blueprint("country", __name__, url_prefix="/manage")


@bp.route("/countries-list/")
@login_required
def country_list():

    search = request.args.get("q")

    pageNumber = (
        int(request.args.get("pageNumber")) if request.args.get("pageNumber") else 1
    )
    pageSize = int(request.args.get("pageSize")) if request.args.get("pageSize") else 10

    if search is not None:
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"name": {"$regex": search, "$options": "i"}},
                        {"code": {"$regex": search, "$options": "i"}},
                        {"official_name": {"$regex": search, "$options": "i"}},
                        {"capital": {"$regex": search, "$options": "i"}},
                        {"region": {"$regex": search, "$options": "i"}},
                        {"subregion": {"$regex": search, "$options": "i"}},
                    ]
                }
            },
            {
                "$project": {
                    "name": 1,
                    "code": 1,
                    "official_name": 1,
                    "capital": 1,
                    "population": 1,
                    "region": 1,
                    "subregion": 1,
                    "area": 1,
                }
            },
            {
                "$facet": {
                    "data": [
                        {"$skip": (pageNumber - 1) * pageSize},
                        {"$limit": pageSize},
                    ],
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
                }
            },
        ]
    else:

        pipeline = [
            {
                "$project": {
                    "name": 1,
                    "code": 1,
                    "official_name": 1,
                    "capital": 1,
                    "population": 1,
                    "region": 1,
                    "subregion": 1,
                    "area": 1,
                }
            },
            {
                "$facet": {
                    "data": [
                        {"$skip": (pageNumber - 1) * pageSize},
                        {"$limit": pageSize},
                    ],
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
                }
            },
        ]

    result = list(get_database().countries.aggregate(pipeline))

    next_url = url_for(
        "country.country_list", pageNumber=pageNumber + 1, pageSize=pageSize
    )
    prev_url = url_for(
        "country.country_list", pageNumber=pageNumber - 1, pageSize=pageSize
    )

    return render_template(
        "dashboard/countries/country-list.html",
        countries=result,
        pageNumber=pageNumber,
        pageSize=pageSize,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/countries/country-form/")
@login_required
def country_add_form():
    country_code = request.args.get("code")

    if country_code is not None:
        country = get_database().countries.find_one(
            {"code": country_code},
            {
                "name": 1,
                "code": 1,
                "official_name": 1,
                "capital": 1,
                "population": 1,
                "region": 1,
                "subregion": 1,
                "area": 1,
                "currencies": 1,
            },
        )
        return render_template("dashboard/countries/country-form.html", country=country)
    else:
        return render_template("dashboard/countries/country-form.html")


@bp.route("/countries/create-or-edit", methods=["POST"])
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
        "subregion": request.form.get("subregion"),
    }

    _id = request.form.get("_id")

    if len(_id) == 0:
        get_database().countries.insert_one(data)
    else:
        get_database().countries.update_one({"_id": ObjectId(_id)}, {"$set": data})

    return redirect(url_for("country.country_list", q=request.form.get("code")))


@bp.route("/country/delete/", methods=["POST"])
def country_delete():
    if request.form.get("_method") == "delete":
        code = request.args.get("code")
        get_database().countries.delete_one({"code": code})

        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error"}), 400
