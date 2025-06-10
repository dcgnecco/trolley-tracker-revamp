"""
Valley Metro Street Car Tracker - Python Backend
Implements all ETA, routing, trolley tracking, and route logic
from the provided HTML/JS code, adapted for backend/data analysis.

Features:
- Trolley position fetching (from FireBase endpoint)
- Stop, route, and path metadata
- ETA calculation to any stop, for any direction
- Direction (Northbound/Southbound) detection
- Suitable for backend use: as a RESTful API or CLI tool
- Fully annotated for clarity

Authors: Team Trolley Tracker
"""

import math
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# ----------------------------
# CONSTANTS
# ----------------------------

SPEED_MPH = 9.3
SPEED_MPS = SPEED_MPH * 0.44704    # Convert miles/hour -> meters/second

ZONES = {
    "ARRIVING": 0.2,      # miles - within this distance, trolley is considered arriving
    "NEARBY": 0.5,        # miles - within this distance, trolley is nearby
    "APPROACHING": 1.0    # miles - within this distance, trolley is approaching
}

# ----------------------------
# STATIC META: Stops, Routes, Paths
# ----------------------------

# List of stops in fixed order with unique id, name, and geographic coordinates (latitude, longitude)
STOPS_IN_ORDER = [
    {"id": 1,  "name": "Dorsey Ln/Apache Blvd",       "lat": 33.4146300,  "lng": -111.9169900},
    {"id": 2,  "name": "Rural Rd/Apache Blvd",         "lat": 33.4147800,  "lng": -111.9252400},
    {"id": 3,  "name": "Paseo Del Saber/Apache Blvd",  "lat": 33.4147500,  "lng": -111.9293900},
    {"id": 4,  "name": "College Ave/Apache Blvd",      "lat": 33.4146800,  "lng": -111.9352600},
    {"id": 5,  "name": "Eleventh St/Mill",             "lat": 33.4181001,  "lng": -111.9399347},
    {"id": 6,  "name": "Ninth St/Mill",                "lat": 33.4209400,  "lng": -111.9399600},
    {"id": 7,  "name": "Sixth St/Mill",                "lat": 33.4248548,  "lng": -111.9398734},
    {"id": 8,  "name": "Third St/Mill",                "lat": 33.4279434,  "lng": -111.9399252},
    {"id": 9,  "name": "Hayden Ferry",                 "lat": 33.4301000,  "lng": -111.9381700},
    {"id": 10, "name": "Marina Heights",               "lat": 33.4293200,  "lng": -111.9327200},
    {"id": 11, "name": "Tempe Beach Park",             "lat": 33.4295000,  "lng": -111.9419600},
    {"id": 12, "name": "3rd St/Ash Ave",               "lat": 33.4274800,  "lng": -111.9430800},
    {"id": 13, "name": "5th St/Ash Ave",               "lat": 33.4251200,  "lng": -111.9434700},
    {"id": 14, "name": "University Dr/Ash Ave",        "lat": 33.4223700,  "lng": -111.9425400},
]

# Dictionary mapping stop names to stop data for fast lookup by name
ALL_STOPS = {stop["name"]: stop for stop in STOPS_IN_ORDER}

# Ordered list of stop names for the Northbound route
NORTHBOUND_ROUTE = [
    "Dorsey Ln/Apache Blvd", "Rural Rd/Apache Blvd", "Paseo Del Saber/Apache Blvd",
    "College Ave/Apache Blvd", "Eleventh St/Mill", "Ninth St/Mill",
    "Sixth St/Mill", "Third St/Mill", "Hayden Ferry", "Marina Heights"
]

# Ordered list of stop names for the Southbound route
SOUTHBOUND_ROUTE = [
    "Marina Heights", "Hayden Ferry", "Tempe Beach Park", "3rd St/Ash Ave",
    "5th St/Ash Ave", "University Dr/Ash Ave", "Ninth St/Mill",
    "Eleventh St/Mill", "College Ave/Apache Blvd", "Paseo Del Saber/Apache Blvd",
    "Rural Rd/Apache Blvd", "Dorsey Ln/Apache Blvd"
]

# The "path" arrays are sequences of lat/lng points approximating the trolley track for each direction.
# For demonstration, only a subset of points is included here.
NORTHBOUND_PATH_COORDS = [
    {"lat": 33.4146300, "lng": -111.9169900},
    {"lat": 33.41473867350939, "lng": -111.91691110472115},
    {"lat": 33.41468270207691, "lng": -111.93685433565464},
    # ... (continued, fill from JS)
    {"lat": 33.4293200, "lng": -111.9327200},
]

SOUTHBOUND_PATH_COORDS = [
    {"lat": 33.4293200, "lng": -111.9327200},
    # ... (continued, fill from JS)
    {"lat": 33.4146300, "lng": -111.9169900}
]

# For production use, fill the path arrays with all points from the original JS data.

# ----------------------------
# BACKEND UTILITIES
# ----------------------------

def get_distance_in_miles(lat1, lng1, lat2, lng2):
    """
    Calculate the great-circle (haversine) distance between two latitude/longitude points.

    Args:
        lat1, lng1: Latitude and longitude of the first point in decimal degrees.
        lat2, lng2: Latitude and longitude of the second point in decimal degrees.

    Returns:
        Distance between the two points in miles.
    """
    R = 3958.8  # Earth radius in miles

    def to_rad(deg):
        return deg * (math.pi / 180)

    dlat = to_rad(lat2 - lat1)
    dlng = to_rad(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(to_rad(lat1)) * math.cos(to_rad(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_distance_along_path(trolley_loc, stop_loc, path_coords):
    """
    Compute the total distance along the route path from the trolley location to the stop location.

    This function finds the closest points on the path to the trolley and the stop,
    then sums the distances between those points along the path.

    Args:
        trolley_loc: Dict with 'lat' and 'lng' for trolley current position.
        stop_loc: Dict with 'lat' and 'lng' for stop position.
        path_coords: List of dicts with 'lat' and 'lng' representing the path coordinates.

    Returns:
        Distance in miles along the path from trolley to stop.
        Returns float('inf') if the stop is behind the trolley along the path.
    """
    min_start_dist = float('inf')
    min_end_dist = float('inf')
    start_idx = 0
    end_idx = len(path_coords) - 1

    # Find closest path index to trolley location and stop location
    for i, p in enumerate(path_coords):
        d_start = get_distance_in_miles(trolley_loc['lat'], trolley_loc['lng'], p['lat'], p['lng'])
        if d_start < min_start_dist:
            min_start_dist = d_start
            start_idx = i

        d_end = get_distance_in_miles(stop_loc['lat'], stop_loc['lng'], p['lat'], p['lng'])
        if d_end < min_end_dist:
            min_end_dist = d_end
            end_idx = i

    # If stop is before trolley on path, return infinite distance (stop behind trolley)
    if end_idx < start_idx:
        return float('inf')

    # Sum distances between consecutive path points from trolley to stop
    total = 0
    for i in range(start_idx, end_idx):
        total += get_distance_in_miles(
            path_coords[i]['lat'], path_coords[i]['lng'],
            path_coords[i+1]['lat'], path_coords[i+1]['lng']
        )
    return total


def get_route_and_path(direction):
    """
    Get the route and path coordinates for a given direction.

    Args:
        direction: String, expected 'Northbound' or 'Southbound' (case-insensitive).

    Returns:
        Tuple of (route list, path coordinates list).
    """
    if direction.lower() == "northbound":
        return NORTHBOUND_ROUTE, NORTHBOUND_PATH_COORDS
    else:
        return SOUTHBOUND_ROUTE, SOUTHBOUND_PATH_COORDS


def find_closest_stop_index(pos, route, all_stops):
    """
    Find the index of the stop in the given route that is closest to the specified position.

    Args:
        pos: Dict with 'lat' and 'lng' for the position.
        route: List of stop names in route order.
        all_stops: Dict mapping stop names to stop data.

    Returns:
        Index (int) of the closest stop in the route list.
        Returns -1 if route is empty or stops not found.
    """
    closest_index = -1
    min_dist = float('inf')
    for i, stop_name in enumerate(route):
        stop = all_stops.get(stop_name)
        if not stop:
            continue
        dist = get_distance_in_miles(pos['lat'], pos['lng'], stop['lat'], stop['lng'])
        if dist < min_dist:
            min_dist = dist
            closest_index = i
    return closest_index


def get_auto_direction_from_stops(prev_pos, curr_pos, direction, all_stops):
    """
    Infer the direction the trolley is traveling based on changes in closest stop indices.

    Args:
        prev_pos: Dict with 'lat' and 'lng' of previous trolley position.
        curr_pos: Dict with 'lat' and 'lng' of current trolley position.
        direction: Current assumed direction ('Northbound' or 'Southbound').
        all_stops: Dict mapping stop names to stop data.

    Returns:
        String: 'Northbound', 'Southbound', or 'Unknown' based on movement.
    """
    route, _ = get_route_and_path(direction)
    closest_idx = find_closest_stop_index(curr_pos, route, all_stops)
    prev_closest_idx = find_closest_stop_index(prev_pos, route, all_stops)

    if closest_idx == -1 or prev_closest_idx == -1:
        return "Unknown"

    if closest_idx > prev_closest_idx:
        return "Northbound"
    elif closest_idx < prev_closest_idx:
        return "Southbound"
    else:
        return "Unknown"


def zone_label(distance_miles):
    """
    Determine the zone label based on the distance to a stop.

    Args:
        distance_miles: Distance in miles to the stop.

    Returns:
        String label: "Arriving", "Nearby", or "Approaching".
    """
    if distance_miles <= ZONES["ARRIVING"]:
        return "Arriving"
    elif distance_miles <= ZONES["NEARBY"]:
        return "Nearby"
    else:
        return "Approaching"


# ----------------------------
# TROLLEY DATA FETCHING
# ----------------------------

def fetch_trolley_location():
    """
    Fetch the live location of the trolley from the Firebase endpoint.

    Returns:
        Dict with keys 'lat' and 'lng' if successful,
        or None if data unavailable or malformed.
    """
    url = "https://fir-realtimedata-9fab9-default-rtdb.firebaseio.com/vehicles/184.json"
    try:
        resp = requests.get(url)
        data = resp.json()
    except Exception:
        # Could not fetch or decode JSON data
        return None

    if data and "latitude" in data and "longitude" in data:
        try:
            return {
                "lat": float(data["latitude"]),
                "lng": float(data["longitude"])
            }
        except (ValueError, TypeError):
            return None
    return None


# ----------------------------
# ETA and Tracker Logic
# ----------------------------

def calc_eta_to_stop(
        trolley_location,
        stop_name,
        direction="Northbound",
        all_stops=ALL_STOPS,
        prev_location=None):
    """
    Calculate the estimated time of arrival (ETA) from the trolley to a specified stop.

    Args:
        trolley_location: Dict with 'lat' and 'lng' for trolley current position.
        stop_name: Name of the stop to calculate ETA to.
        direction: Direction of travel, "Northbound" or "Southbound" (default "Northbound").
        all_stops: Dict mapping stop names to stop data.
        prev_location: Optional dict with previous trolley position for direction inference.

    Returns:
        Dict with ETA details including:
            - stop: stop_name
            - direction: direction string
            - eta_min: ETA minutes part (int)
            - eta_sec: ETA seconds part (int)
            - zone: zone label string (Arriving/Nearby/Approaching)
            - distance_miles: distance in miles (float)
            - distance_meters: distance in meters (float)
            - warning: optional warning string if direction mismatch detected
        Or dict with 'error' key describing any issues.
    """
    route, path_coords = get_route_and_path(direction)
    if stop_name not in all_stops:
        return {"error": f"Stop '{stop_name}' not found."}
    stop_coord = all_stops[stop_name]

    if not path_coords or len(path_coords) < 2:
        return {"error": "Route path not loaded yet."}

    # Calculate distance along the path from trolley to stop
    distance_miles = get_distance_along_path(trolley_location, stop_coord, path_coords)
    distance_meters = distance_miles * 1609.34  # Convert miles to meters
    speed_mps = SPEED_MPS

    # Validate distance and speed for ETA calculation
    if not math.isfinite(distance_meters) or distance_meters <= 0 or speed_mps < 0.5:
        return {"error": "ETA unavailable or stop behind trolley."}

    # Compute ETA in seconds, then split to minutes and seconds
    eta_seconds = distance_meters / speed_mps
    eta_min = int(eta_seconds // 60)
    eta_sec = int(round(eta_seconds % 60))
    zone = zone_label(distance_miles)

    auto_dir = None
    warning = None
    # If previous location provided, infer actual trolley direction and warn if mismatched
    if prev_location:
        auto_dir = get_auto_direction_from_stops(prev_location, trolley_location, direction, all_stops)
        if auto_dir != direction and auto_dir != "Unknown":
            warning = f"Trolley is moving {auto_dir}, but you're tracking {direction}"

    return {
        "stop": stop_name,
        "direction": direction,
        "eta_min": eta_min,
        "eta_sec": eta_sec,
        "zone": zone,
        "distance_miles": distance_miles,
        "distance_meters": distance_meters,
        "warning": warning
    }

# ----------------------------
# REST API (Flask)
# ----------------------------
app = Flask(__name__)
CORS(app)

# !!!!! !!!!!
@app.route('/api/eta', methods=['POST'])
def api_eta():
    """
    REST API endpoint to get ETA to a specified stop and direction.

    Query parameters:
        stop: Name of the stop (required)
        direction: Direction "Northbound" or "Southbound" (optional, default "Northbound")

    Returns:
        JSON response with ETA details or error message.
    """
    data = request.get_json()
    stop = data.get("stop")
    direction = data.get("route")

    # Fetch the current trolley location
    trolley_location = {"lat": 33.421072548282694, "lng": -111.93998403404477} # HARDCODED FOR TESTING, USE fetch_trolley_location()
    prev_location = None

    if not trolley_location:
        return jsonify({"error": "Trolley location unavailable."}), 503

    # Simulate previous location slightly behind current for direction inference
    prev_location = {"lat": trolley_location["lat"] - 0.0005, "lng": trolley_location["lng"]}

    result = calc_eta_to_stop(
        trolley_location,
        stop,
        direction=direction,
        prev_location=prev_location
    )
    return jsonify(result)

# !!!!! !!!!!
@app.route('/api/stops', methods=['GET'])
def api_stops():
    """
    REST API endpoint to list all available stops.

    Returns:
        JSON array of stop names.
    """
    return jsonify(list(ALL_STOPS.keys()))

# !!!!! !!!!!
@app.route('/api/route', methods=['GET'])
def api_route():
    """
    REST API endpoint to get the route stop list for a given direction.

    Query parameters:
        direction: "Northbound" or "Southbound" (optional, default "Northbound")

    Returns:
        JSON array of stop names in order for the route.
    """
    direction = request.args.get('direction', 'Northbound')
    route, _ = get_route_and_path(direction)
    return jsonify(route)

# !!!!! !!!!!
@app.route('/api/trolley_location', methods=['GET'])
def api_trolley_location():
    """
    REST API endpoint to get the real-time trolley location.

    Returns:
        JSON object with 'lat' and 'lng' or error message.
    """
    trolley_location = {"lat": 33.421072548282694, "lng": -111.93998403404477} #fetch_trolley_location()
    if not trolley_location:
        return jsonify({"error": "Trolley location unavailable."}), 503
    return jsonify(trolley_location)


if __name__ == "__main__":
    app.run(debug=True)