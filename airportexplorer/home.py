from flask import Blueprint, render_template, request

bp = Blueprint("home", __name__, url_prefix="/")


@bp.route("/")
def home():
    return render_template("home/home.html")

@bp.route("/airport-search/")
def airport_result():
    query = request.args.get('q')
    
    # result = [{"name": "John F. Kennedy International Airport", "city": "New York", "country": "United States", "iata": "JFK", "icao": "KJFK", "latitude": "40.63980103", "longitude": "-73.77890015", "altitude": "13", "timezone": "America/New_York"}]
    result = []
    return render_template("home/airport-result.html", query=query, result=result)
