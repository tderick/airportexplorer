from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from decouple import config
from flask import (Blueprint, current_app, redirect, render_template, session,
                   url_for)
from flask_login import login_user

from airportexplorer.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")

# OAuth Configuration
oauth = OAuth(current_app)
oauth.register(
    "auth0",
    client_id=config("AUTH0_CLIENT_ID"),
    client_secret=config("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{config('AUTH0_DOMAIN')}/.well-known/openid-configuration",
)


@bp.route("/login")
def login_page():
    return render_template("auth/login.html")


@bp.route("/login/initiate/")
def login_action():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True)
    )


@bp.route("/callback", methods=["GET", "POST"])
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


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + config("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("auth.login_page", _external=True),
                "client_id": config("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
