import random
from urllib.parse import quote_plus

import pandas as pd
import requests
from decouple import config
from pymongo.mongo_client import MongoClient

MONGO_USERNAME = config("MONGO_USERNAME", default="")
MONGO_PASSWORD = config("MONGO_PASSWORD", default="")
MONGO_DATABASE = config("MONGO_DATABASE", default="airportexplorer")
username = quote_plus(MONGO_USERNAME)
password = quote_plus(MONGO_PASSWORD)

MONGODB_URI = (
    "mongodb://"
    + username
    + ":"
    + password
    + "@172.232.220.157:27017,172.232.217.83:27017,172.232.217.81:27017/airportexplorer?authSource=admin&replicaSet=rs0&retryWrites=true&w=3&r=2"
)


mongoclient = MongoClient(MONGODB_URI)
database = mongoclient.get_database(MONGO_DATABASE)


# result = database.countries.update_many(
#     {},  # Empty filter matches all documents
#     {"$unset": {"regions.$[].airports.$[].reviews": ""}}
# )

# print("Number of documents modified:", result.modified_count)


reviews = database.reviews.find()
for review in reviews:

    try:
        name = review["title"].replace("Airport customer review", "")

        # Update operation
        # update_result = database.countries.update_many(
        #     {"regions.airports.name": {"$regex": name, "$options": 'i'}},
        #     {"$push": {"regions.$[].airports.$[].reviews": review['_id']}}
        # )
        # update_result = database.countries.update_many(
        #     {"regions.airports.name": {"$regex": name, "$options": "i"}},
        #     {"$unset": {"regions.$[].airports.$[].reviews": ""}},
        # )

        # print("Matched:", update_result.matched_count)
        # print("Modified:", update_result.modified_count)

        print(name)
        pipeline = [
            {"$unwind": "$regions"},
            {"$unwind": "$regions.airports"},
            {
                "$project": {
                    "_id": 0,
                    "ident": "$regions.airports.ident",
                    "name": "$regions.airports.name",
                }
            },
            {"$match": {"name": {"$regex": name, "$options": "i"}}},
        ]
        airport = list(database.countries.aggregate(pipeline))

        if len(airport) == 0:
            continue
        else:
            database.reviews.update_one(
                {"_id": review["_id"]},
                {
                    "$set": {
                        "airport": airport[0].get("ident"),
                        "airport_name": airport[0].get("name"),
                        "likes": random.randint(0, 150),
                    }
                },
            )

    except Exception as e:
        print(e)
        continue
