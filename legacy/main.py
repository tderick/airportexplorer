import json
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from decouple import config
from flask import Flask, redirect, render_template, session, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = Flask(__name__, static_folder="static", template_folder="templates")

app.secret_key = config("APP_SECRET_KEY")

# Database
MONGO_USERNAME = config("MONGO_USERNAME", default="")
MONGO_PASSWORD = config("MONGO_PASSWORD", default="")
username = quote_plus(MONGO_USERNAME)
password = quote_plus(MONGO_PASSWORD)

MONGODB_URI = (
    "mongodb+srv://"
    + username
    + ":"
    + password
    + "@airportexplorer.v0ampl7.mongodb.net/?retryWrites=true&w=majority&appName=airportexplorer"
)

mongoclient = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
database = mongoclient.get_database("airportexplorer")

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=config("AUTH0_CLIENT_ID"),
    client_secret=config("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{config('AUTH0_DOMAIN')}/.well-known/openid-configuration",
)


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_email(user_id)


@app.route("/dashboard/")
@login_required
def dashboard():
    return render_template("dashboard/dashboard-base.html")


@app.route("/login")
def login_page():
    return render_template("auth/login.html")


@app.route("/login/initiate/")
def login_action():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    nickname = token["userinfo"]["nickname"]
    email = token["userinfo"]["email"]
    sub = token["userinfo"]["sub"]
    email_verified = token["userinfo"]["email_verified"]

    user = User.get_by_email(email)
    if user is None:
        User.register(
            nickname=nickname, email=email, sub=sub, email_verified=email_verified
        )
        user = User.get_by_email(email)

    login_user(user)
    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + config("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("login_page", _external=True),
                "client_id": config("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/")
def home():
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


class User(UserMixin):

    def __init__(self, username, email, _id=None, nickname=None):
        self.username = email
        self.email = email
        self._id = _id
        self.nickname = nickname

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self._id

    @classmethod
    def get_by_username(cls, username):
        result = database.users.find_one({"email": username})
        if result is not None:
            return cls(
                username=result["email"],
                email=result["email"],
                _id=result["email"],
                nickname=result["nickname"],
            )
        else:
            return None

    @classmethod
    def get_by_email(cls, email):
        result = database.users.find_one({"email": email})
        if result is not None:
            return cls(
                username=result["email"],
                email=result["email"],
                _id=result["email"],
                nickname=result["nickname"],
            )
        else:
            return None

    @classmethod
    def get_by_id(cls, _id):
        result = database.users.find_one({"sub": _id})
        if result is not None:
            return cls(
                username=result["email"],
                email=result["email"],
                _id=result["sub"],
                nickname=result["nickname"],
            )
        else:
            return None

    @staticmethod
    def login_valid(email, password):
        return False

    @classmethod
    def register(cls, email, sub, nickname, email_verified=None):
        user = cls.get_by_email(email)
        if user is None:
            document = {
                "email": email,
                "sub": sub,
                "nickname": nickname,
                "email_verified": email_verified,
            }
            database.users.insert_one(document)
            return True
        else:
            return False

    def json(self):
        return {
            "username": self.username,
            "email": self.email,
            "_id": self._id,
            "password": self.password,
        }


if __name__ == "__main__":
    app.run(debug=True, port=8000)
