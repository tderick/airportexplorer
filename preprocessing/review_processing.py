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

data = pd.read_csv("data/airport_reviews.csv").fillna(0)

for index, row in data.iterrows():
    try:
    
        review = {
            "title": row["title"],
            "author": row["author"],
            "author_country": row["author_country"],
            "date":  row["date"],
            "content": row["content"],
            "experience_airport": row["experience_airport"],
            "date_visit": row["date_visit"],
            "type_traveller": row["type_traveller"],
            "overall_rating": row["overall_rating"],
            "queuing_rating":  row["queuing_rating"],
            "terminal_cleanliness_rating": row["terminal_cleanliness_rating"],
            "terminal_seating_rating":  row["terminal_seating_rating"],
            "terminal_signs_rating": row["terminal_signs_rating"],
            "food_beverages_rating": row["food_beverages_rating"],
            "airport_shopping_rating":  row["airport_shopping_rating"],
            "wifi_connectivity_rating": row["wifi_connectivity_rating"],
            "airport_staff_rating": row["airport_staff_rating"],
            "recommended": True if row["recommended"] == 1 else False,
            "is_public": True,
        }
        
        database.reviews.insert_one(review)

    except Exception:
        print("Error")
        continue
