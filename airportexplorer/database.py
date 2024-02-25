from urllib.parse import quote_plus

from decouple import config
from flask import g
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


def get_database():
    # Database
    MONGO_USERNAME = config("MONGO_USERNAME", default="")
    MONGO_PASSWORD = config("MONGO_PASSWORD", default="")
    MONGO_DATABASE = config("MONGO_DATABASE", default="airportexplorer")
    username = quote_plus(MONGO_USERNAME)
    password = quote_plus(MONGO_PASSWORD)

    MONGODB_URI = (
        "mongodb+srv://"
        + username
        + ":"
        + password
        + "@airportexplorer.v0ampl7.mongodb.net/?retryWrites=true&w=majority&appName=airportexplorer"
    )

    if 'database' not in g:     
        mongoclient = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
        g.database = mongoclient.get_database(MONGO_DATABASE)

    return g.database
