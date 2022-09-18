from flask import Flask, render_template, request, url_for, flash, redirect
from math import radians, cos, sin, asin, sqrt
import requests
import json
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# Function for calculating distance between long/lat points


def distance(lat1, lat2, lon1, lon2):
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    # calculate the result
    return (c * r)


def zipcodeFromCoords(lat, lon):
    endpoint = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={os.getenv("GOOGLE_KEY")}'
    response = requests.get(endpoint)
    place = json.loads(response.text)["results"]
    zip = place[0]["formatted_address"].split(",")[2].split()[1]
    return zip


@app.route('/listStations', methods=['POST'])
def index():
    coords = request.data.decode("UTF-8").split(",")
    zip = zipcodeFromCoords(coords[0], coords[1])
    limit = 100
    url = f'https://developer.nrel.gov/api/alt-fuel-stations/v1.json?limit={limit}&api_key={os.getenv("API_KEY")}&zip={zip}&fuel_type=ELEC'
    response = requests.get(url)
    stations = json.loads(response.text)["fuel_stations"]

    # Initialize response data dict
    responseData = {"stations": []}
    for i in range(len(stations)):

        # Parse response data
        responseData["stations"].append({})
        responseData["stations"][i]["longitude"] = stations[i]["longitude"]
        responseData["stations"][i]["latitude"] = stations[i]["latitude"]
        responseData["stations"][i]["station_name"] = stations[i][
            "station_name"]
        responseData["stations"][i]["street_address"] = stations[i][
            "street_address"]
        responseData["stations"][i]["city"] = stations[i]["city"]
        responseData["stations"][i]["ev_network"] = stations[i]["ev_network"]
        responseData["stations"][i]["ev_pricing"] = stations[i]["ev_pricing"]

    # Determine closest stations
    userLat = float(coords[0])
    userLon = float(coords[1])
    podium = [{
        "name": None,
        "dist": None,
        "address": None,
        "city": None,
        "state": None,
        "ev_network": None
    }, {
        "name": None,
        "dist": None,
        "address": None,
        "city": None,
        "state": None,
        "ev_network": None
    }, {
        "name": None,
        "dist": None,
        "address": None,
        "city": None,
        "state": None,
        "ev_network": None
    }]
    for station in stations:
        dist = distance(station["latitude"], userLat, station["longitude"],
                        userLon)
        for place in podium:
            if not place["name"] or dist < place["dist"]:
                place["name"] = station["station_name"]
                place["dist"] = dist
                place["address"] = station["street_address"]
                place["city"] = station["city"]
                place["state"] = station["state"]
                place["ev_network"] = station["ev_network"]
                break
    print(responseData)
    print("--------------")
    print(podium)
    return json.dumps({"all": responseData, "podium": podium}, indent=4)


@app.route("/")
def home():
    return render_template("main.html")


if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', debug=True, port=8080)
