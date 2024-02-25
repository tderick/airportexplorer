import json
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from decouple import config
from flask import Flask, redirect, render_template, session, url_for

app = Flask(__name__, static_folder="static", template_folder="templates")

app.secret_key = config("APP_SECRET_KEY")


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


@app.route("/")
def hello_world():
    # return render_template('dashboard/dashboard-base.html')
    return render_template("index.html")

@app.route('/login')
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
    session["user"] = token
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + config("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
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


if __name__ == "__main__":
    app.run(debug=True, port=8000)
