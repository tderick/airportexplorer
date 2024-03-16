from urllib.parse import quote_plus

import redis
from decouple import config
from flask import g
from pymongo.mongo_client import MongoClient


def get_database():
    # Database
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
        + "@"
        + config("CONNEXION_STRING")
        + "&authSource=admin&retryWrites=true"
    )

    if "database" not in g:
        mongoclient = MongoClient(MONGODB_URI)
        g.database = mongoclient.get_database(MONGO_DATABASE)

    return g.database


def get_redis():
    if "redis" not in g:
        g.redis = redis.StrictRedis.from_url(
            config("REDIS_URL", default="redis://localhost:6379/0")
        )

    return g.redis
