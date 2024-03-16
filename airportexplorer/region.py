from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)
from flask_login import login_required

from airportexplorer.database import get_database

bp = Blueprint("region", __name__, url_prefix="/manage")


@bp.route("/region-list/")
@login_required
def region_list():

    search = request.args.get("q")

    pageNumber = (
        int(request.args.get("pageNumber")) if request.args.get("pageNumber") else 1
    )
    pageSize = int(request.args.get("pageSize")) if request.args.get("pageSize") else 10

    if search is not None:
        pipeline = [
            {"$unwind": "$regions"},
            {"$match": {"regions.name": {"$regex": search, "$options": "i"}}},
            {
                "$project": {
                    "_id": 0,
                    "name": "$regions.name",
                    "code": "$regions.code",
                    "local_code": "$regions.local_code",
                    "iso_country": "$regions.iso_country",
                    "continent": "$regions.continent",
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
            {"$match": {"regions": {"$exists": True}}},
            {"$unwind": "$regions"},
            {
                "$project": {
                    "_id": 0,
                    "name": "$regions.name",
                    "code": "$regions.code",
                    "local_code": "$regions.local_code",
                    "iso_country": "$regions.iso_country",
                    "continent": "$regions.continent",
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
        "region.region_list", pageNumber=pageNumber + 1, pageSize=pageSize
    )
    prev_url = url_for(
        "region.region_list", pageNumber=pageNumber - 1, pageSize=pageSize
    )

    return render_template(
        "dashboard/regions/region-list.html",
        regions=result,
        pageNumber=pageNumber,
        pageSize=pageSize,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/regions/region-form/")
@login_required
def region_add_update_form():
    region_code = request.args.get("code")

    countries = get_database().countries.find({}, {"_id": 0, "name": 1, "code": 1})

    if region_code is not None:
        pipeline = [
            {"$unwind": "$regions"},  # Deconstruct the array
            {
                "$match": {"regions.code": region_code}
            },  # Filter based on inner document criteria
            {
                "$project": {
                    "_id": 0,
                    "regions.code": 1,
                    "regions.name": 1,
                    "regions.iso_country": 1,
                    "regions.local_code": 1,
                    "regions.continent": 1,
                }
            },
        ]

        region_cursor = get_database().countries.aggregate(pipeline)

        region = list(region_cursor)[0]

        return render_template(
            "dashboard/regions/region-form.html",
            region=region["regions"],
            countries=countries,
        )
    else:
        return render_template(
            "dashboard/regions/region-form.html", countries=countries
        )


@bp.route("/regions/create-or-edit", methods=["POST"])
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
            {"code": iso_country}, {"$push": {"regions": data}}
        )
    else:
        get_database().countries.update_one(
            {"regions.code": old_code},
            {
                "$set": {
                    "regions.$.code": data["code"],
                    "regions.$.name": data["name"],
                    "regions.$.iso_country": data["iso_country"],
                    "regions.$.local_code": data["local_code"],
                    "regions.$.continent": data["continent"],
                }
            },
        )
    return redirect(url_for("region.region_list", q=request.form.get("name")))


@bp.route("/regions/delete/", methods=["POST"])
def region_delete():
    if request.form.get("_method") == "delete":
        code = request.args.get("code")
        get_database().countries.update_one(
            {"regions.code": code}, {"$pull": {"regions": {"code": code}}}
        )

        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error"}), 400
