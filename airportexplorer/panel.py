from flask import (Blueprint, render_template)
from flask_login import login_required

bp = Blueprint("panel", __name__, url_prefix="/manage")

@bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard/dashboard-base.html")

