from flask import (Blueprint, render_template, current_app)
from flask_login import login_required
from airportexplorer import cache

bp = Blueprint("panel", __name__, url_prefix="/manage")


@bp.route("/")
@login_required
@cache.cached(timeout=50)
def dashboard():
    return render_template("dashboard/dashboard-base.html")

