from urllib.parse import quote_plus

from auth0.authentication import Database, GetToken
from decouple import config
from pymongo.mongo_client import MongoClient

auth0_database = Database(config("AUTH0_DOMAIN"), config("AUTH0_CLIENT_ID"))


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

reviews = database.reviews.find()
for review in reviews:

    try:

        fullname = review["author"]
        email = fullname.split(" ")[0].lower() + "@gmail.com"
        auth0_database.signup(
            email=email,
            password=config("USER_PASSWORD"),
            connection="Username-Password-Authentication",
        )
        token = GetToken(
            config("AUTH0_DOMAIN"),
            config("AUTH0_CLIENT_ID"),
            client_secret=config("AUTH0_CLIENT_SECRET"),
        )

        token.login(
            username=email,
            password=config("USER_PASSWORD"),
            realm="Username-Password-Authentication",
        )

        import pdb

        pdb.set_trace()

        sub = None
        document = {
            "email": email,
            "sub": sub,
            "nickname": fullname.split(" ")[0].lower(),
            "email_verified": False,
            "is_onboarding_complete": True,
            "is_admin": False,
            "first_name": fullname.split(" ")[0],
            "last_name": fullname.split(" ")[1] if len(fullname.split(" ")) > 1 else "",
        }

    except Exception as e:
        print(e)
        continue
