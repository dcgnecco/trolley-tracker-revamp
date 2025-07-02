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
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import Trolley

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
# STATIC META: Active Trolley Ids, Stops, Routes, Paths
# ----------------------------

# !!!!!!!!!!! IMPORTANT: List of integer ids of active trolleys being tracked !!!!!!!!!!
ACTIVE_TROLLEY_IDS = [180, 181, 182, 183, 184, 185, 186, 187, 188, 189]

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
            {"lat": 33.41471152728806, "lng": -111.93731760460068},
            {"lat": 33.41478652897446, "lng": -111.93774541693855},
            {"lat": 33.414882799700884, "lng": -111.93804984766174},
            {"lat": 33.41498914514669, "lng": -111.93831672745873},
            {"lat": 33.41524245288249, "lng": -111.93875248740642},
            {"lat": 33.41546745637178, "lng": -111.93904350708453},
            {"lat": 33.41564096612709, "lng": -111.93922455619304},
            {"lat": 33.41583462499299, "lng": -111.9394149930331},
            {"lat": 33.4162273736864, "lng": -111.93965804300423},
            {"lat": 33.416573628903414, "lng": -111.9398115330761},
            {"lat": 33.41681430056655, "lng": -111.93989334045105},
            {"lat": 33.41724780818715, "lng": -111.93992949239569},
            {"lat": 33.41777744027617, "lng": -111.93992368411551},
            {"lat": 33.41851959454649, "lng": -111.93993843649152},
            {"lat": 33.41889122776191, "lng": -111.9399545297456},
            {"lat": 33.41937797088634, "lng": -111.93994916532758},
            {"lat": 33.4199285500109, "lng": -111.93996794079068},
            {"lat": 33.42038782350175, "lng": -111.93996257637265},
            {"lat": 33.421072548282694, "lng": -111.93998403404477},
            {"lat": 33.42152876557559, "lng": -111.9399959387079},
            {"lat": 33.42963353809141, "lng": -111.94003318916191},
            {"lat": 33.42972307694576, "lng": -111.93921779762138},
            {"lat": 33.42983052344905, "lng": -111.93874572883476},
            {"lat": 33.429982739101, "lng": -111.9383916772448},
            {"lat": 33.43012513117248, "lng": -111.93817377090454},
            {"lat": 33.43030737393965, "lng": -111.9379104154135},
            {"lat": 33.430403627457075, "lng": -111.93762073683989},
            {"lat": 33.43055768551716, "lng": -111.93714408355024},
            {"lat": 33.43062483895153, "lng": -111.9366505570915},
            {"lat": 33.43062483895153, "lng": -111.93632869200971},
            {"lat": 33.43060021603163, "lng": -111.93607656436231},
            {"lat": 33.43052187033088, "lng": -111.93569032626417},
            {"lat": 33.430353986448296, "lng": -111.93527458386686},
            {"lat": 33.430080411409705, "lng": -111.93481015644007},
            {"lat": 33.4298655188888, "lng": -111.93451779565744},
            {"lat": 33.429697633736644, "lng": -111.93426030359201},
            {"lat": 33.429552133008805, "lng": -111.93397867164545},
            {"lat": 33.42943125529553, "lng": -111.93362998447351},
            {"lat": 33.42937753181339, "lng": -111.93323301753931},
            {"lat": 33.42936852845058, "lng": -111.93270206451416},
            {"lat": 33.4293200, "lng": -111.9327200},    
        ]

SOUTHBOUND_PATH_COORDS = [
            {"lat": 33.4293200, "lng": -111.9327200},
            {"lat": 33.42945825139364, "lng": -111.9335934955798},
            {"lat": 33.42953100186674, "lng": -111.93383623549565},
            {"lat": 33.42962054082687, "lng": -111.93407092878445},
            {"lat": 33.42978757531599, "lng": -111.93435218452409},
            {"lat": 33.4299778449334, "lng": -111.93462308763459},
            {"lat": 33.430165875674916, "lng": -111.93490471958116},
            {"lat": 33.430344952192925, "lng": -111.93521049140885},
            {"lat": 33.43049097787063, "lng": -111.93558375147781},
            {"lat": 33.43054022376546, "lng": -111.93573931960067},
            {"lat": 33.43058275428849, "lng": -111.93589488772353},
            {"lat": 33.43061633100249, "lng": -111.93608800677261},
            {"lat": 33.430636477024656, "lng": -111.93627844361266},
            {"lat": 33.43064990770349, "lng": -111.93644205836257},
            {"lat": 33.430647669257176, "lng": -111.93663785962066},
            {"lat": 33.4306275232376, "lng": -111.9368604829689},
            {"lat": 33.430591708080144, "lng": -111.93705091980895},
            {"lat": 33.43055141601037, "lng": -111.93731645850143},
            {"lat": 33.43043991559499, "lng": -111.93759551045517},
            {"lat": 33.43037961716983, "lng": -111.93779917587062},
            {"lat": 33.4302341175852, "lng": -111.93805130351802},
            {"lat": 33.430041610067654, "lng": -111.93841876615306},
            {"lat": 33.42987820218863, "lng": -111.93865211833736},
            {"lat": 33.429811048176546, "lng": -111.9389122926118},
            {"lat": 33.42976180186799, "lng": -111.939126869333},
            {"lat": 33.429728224823435, "lng": -111.93946750987789},
            {"lat": 33.42965434315988, "lng": -111.93992089033506},
            {"lat": 33.42959166592191, "lng": -111.94042246342084},
            {"lat": 33.429535704064044, "lng": -111.94101254940412},
            {"lat": 33.42948869607553, "lng": -111.94170187712095},
            {"lat": 33.42946091927352, "lng": -111.94182993303215},
            {"lat": 33.42947373691616, "lng": -111.94200664758682},
            {"lat": 33.42941614972267, "lng": -111.9423610104171},
            {"lat": 33.4293557107924, "lng": -111.94247366319573},
            {"lat": 33.42929079485746, "lng": -111.94259168039238},
            {"lat": 33.429228117356956, "lng": -111.94263996015465},
            {"lat": 33.429163201326574, "lng": -111.94262923131859},
            {"lat": 33.42910032763656, "lng": -111.94261521801103},
            {"lat": 33.429024219070186, "lng": -111.94258034929383},
            {"lat": 33.42894139496623, "lng": -111.94255084499467},
            {"lat": 33.42887424022936, "lng": -111.94252670511354},
            {"lat": 33.428784700499364, "lng": -111.9425025652324},
            {"lat": 33.42871306864887, "lng": -111.94249183639634},
            {"lat": 33.42863024424803, "lng": -111.94248647197831},
            {"lat": 33.4285563737698, "lng": -111.94247842535127},
            {"lat": 33.428480264726474, "lng": -111.94247037872422},
            {"lat": 33.428408632624716, "lng": -111.94247574314225},
            {"lat": 33.428334761957885, "lng": -111.94247574314225},
            {"lat": 33.42822059807638, "lng": -111.94248110756028},
            {"lat": 33.428151204271124, "lng": -111.94249183639634},
            {"lat": 33.427944196056586, "lng": -111.94254279836763},
            {"lat": 33.42782779314234, "lng": -111.94259376033891},
            {"lat": 33.427722582681724, "lng": -111.94264472231019},
            {"lat": 33.427639757335754, "lng": -111.94269300207246},
            {"lat": 33.427559170436815, "lng": -111.94276005729783},
            {"lat": 33.42748529904706, "lng": -111.94281101926912},
            {"lat": 33.42739351935403, "lng": -111.9428995321666},
            {"lat": 33.42731548030475, "lng": -111.94296904706228},
            {"lat": 33.42723489310475, "lng": -111.94302537345159},
            {"lat": 33.4271677370476, "lng": -111.94307365321386},
            {"lat": 33.4270849111722, "lng": -111.94312997960317},
            {"lat": 33.42697298418803, "lng": -111.94319435261953},
            {"lat": 33.42684986433875, "lng": -111.94324531459081},
            {"lat": 33.42678942362157, "lng": -111.94326677226293},
            {"lat": 33.426681973353766, "lng": -111.94329359435308},
            {"lat": 33.42656333019524, "lng": -111.94331773423421},
            {"lat": 33.42490697850245, "lng": -111.94334693452191},
            {"lat": 33.42468759597367, "lng": -111.94333084126782},
            {"lat": 33.42451746220231, "lng": -111.94330401917767},
            {"lat": 33.42430255590928, "lng": -111.94324501057935},
            {"lat": 33.42415480752423, "lng": -111.94318600198102},
            {"lat": 33.42405630846115, "lng": -111.94309480687451},
            {"lat": 33.42396157071967, "lng": -111.94302597079506},
            {"lat": 33.42382725348881, "lng": -111.94294014010659},
            {"lat": 33.42371979955448, "lng": -111.94282748732796},
            {"lat": 33.42355414114517, "lng": -111.94273092780342},
            {"lat": 33.42342430054935, "lng": -111.94268801245919},
            {"lat": 33.42327655066959, "lng": -111.94258072409859},
            {"lat": 33.423061641304706, "lng": -111.94250025782814},
            {"lat": 33.422855685997526, "lng": -111.94242515597573},
            {"lat": 33.422712412452164, "lng": -111.94239833388558},
            {"lat": 33.42247959243669, "lng": -111.94240369830361},
            {"lat": 33.42236180531355, "lng": -111.94251894950867},
            {"lat": 33.422287067721534, "lng": -111.94237687621346},
            {"lat": 33.422148270569025, "lng": -111.94236078295937},
            {"lat": 33.42201395053274, "lng": -111.94237687621346},
            {"lat": 33.42189753966652, "lng": -111.94237151179543},
            {"lat": 33.42191097169752, "lng": -111.94010236296883},
            {"lat": 33.42180132869863, "lng": -111.94003671886095},
            {"lat": 33.42164014398606, "lng": -111.94004208327898},
            {"lat": 33.42111629160355, "lng": -111.94002062560686},
            {"lat": 33.42055213934921, "lng": -111.94002062560686},
            {"lat": 33.41974997797302, "lng": -111.94000117901741},
            {"lat": 33.41759629552683, "lng": -111.93997435692727},
            {"lat": 33.4172694326075, "lng": -111.93995826367318},
            {"lat": 33.41696047885403, "lng": -111.93996899250924},
            {"lat": 33.41675898668346, "lng": -111.93990461949288},
            {"lat": 33.41658883737537, "lng": -111.93985097531258},
            {"lat": 33.41647241923563, "lng": -111.9398187888044},
            {"lat": 33.416329135157056, "lng": -111.93977050904213},
            {"lat": 33.41616346264654, "lng": -111.93970077160775},
            {"lat": 33.41602913335191, "lng": -111.93964176300942},
            {"lat": 33.415961968626675, "lng": -111.939566661157},
            {"lat": 33.41585898261376, "lng": -111.93948083046853},
            {"lat": 33.41575599647869, "lng": -111.93940572861611},
            {"lat": 33.41564853255539, "lng": -111.93933062676369},
            {"lat": 33.415567934525626, "lng": -111.9392233384031},
            {"lat": 33.41544703734075, "lng": -111.93913750771462},
            {"lat": 33.4153306176703, "lng": -111.93896048191964},
            {"lat": 33.41523245464974, "lng": -111.93881371467263},
            {"lat": 33.41513506488778, "lng": -111.93864741771371},
            {"lat": 33.41506789947106, "lng": -111.938518671681},
            {"lat": 33.41500745055161, "lng": -111.93841004221589},
            {"lat": 33.41494588216444, "lng": -111.9382665440336},
            {"lat": 33.414896627423296, "lng": -111.93815657346398},
            {"lat": 33.414822745259194, "lng": -111.93797418325097},
            {"lat": 33.41477572930387, "lng": -111.937799839665},
            {"lat": 33.41474214646305, "lng": -111.93763354270608},
            {"lat": 33.41470632475185, "lng": -111.9374565169111},
            {"lat": 33.41467498074245, "lng": -111.93714806287439},
            {"lat": 33.4146458755807, "lng": -111.93687447755487},
            {"lat": 33.41465035329853, "lng": -111.93661966769845},
            {"lat": 33.414658282700145, "lng": -111.93597085862032},
            {"lat": 33.41468369331868, "lng": -111.93345539763263},
            {"lat": 33.414720926354406, "lng": -111.92950739966484},
            {"lat": 33.414760840958145, "lng": -111.92584156061946},
            {"lat": 33.41474069125175, "lng": -111.92023976709186},
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

def fetch_trolley_location(vehicle_id):
    """
    Fetch the live location of the trolley from the Firebase endpoint.

    Args:
        Integer for the vehicle id number (currently 181-185)

    Returns:
        Dict with keys 'lat' and 'lng' if successful,
        or None if data unavailable or malformed.
    """
    url = "https://fir-realtimedata-9fab9-default-rtdb.firebaseio.com/vehicles/"+str(vehicle_id)+".json"
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

def fetch_trolley_locations_from_VM(vehicle_id):
    """
    Fetch the live location of the trolley from the Valley Metro API

    Args:
        Integer for the vehicle id number (currently 181-185)

    Returns:
        Dict with keys 'lat' and 'lng' if successful,
        or None if data unavailable or malformed.
    """
    url = "https://mna.mecatran.com/utw/ws/gtfsfeed/vehicles/valleymetro?apiKey=4f22263f69671d7f49726c3011333e527368211f&asJson=true"
    try:
        resp = requests.get(url)
        data = resp.json()
    except Exception:
        # Could not fetch or decode JSON data
        return None

    if data:
        trolleys = []
        for e in data["entity"]:
            vehicle_id = int(e["vehicle"]["vehicle"]["id"])
            #if vehicle_id in ACTIVE_TROLLEY_IDS
            if vehicle_id > 180 and vehicle_id < 190:
                trolleys.append({"id": vehicle_id,
                                 "lat": e["vehicle"]["position"]["latitude"],
                                 "lng": e["vehicle"]["position"]["longitude"],
                                 "dir": e["vehicle"]["trip"]["directionId"]})
        return trolleys

    #if data and "latitude" in data and "longitude" in data:
        #try:
            #return {
                #"lat": float(data["latitude"]),
                #"lng": float(data["longitude"])
            #}
        #except (ValueError, TypeError):
            #return None
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
    if eta_sec == 60:
        eta_sec = 0
        eta_min = eta_min + 1

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
    trolley_location = fetch_trolley_location() # FOR TESTING: {"lat": 33.421072548282694, "lng": -111.93998403404477} 
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
@app.route('/api/active_trolley_locations', methods=['GET'])
def api_active_trolley_locations():
    """
    REST API endpoint to get the real-time locations of all active trolleys.

    Returns:
        JSON array of 'id', 'lat', and 'lng' values for each active trolley
    """
    trolleys = []

    for id in ACTIVE_TROLLEY_IDS:
        location = fetch_trolley_location(id)
        if location:    
            trolleys.append({"id": id, "lat": location["lat"], "lng": location["lng"]})
        
    return jsonify(trolleys)

# !!!!! !!!!!
@app.route('/api/trolley_locations_VM', methods=['GET'])
def api_trolley_locations_VM():
    """
    REST API endpoint to get the real-time locations of all active trolleys.

    Returns:
        JSON array of 'id', 'lat', and 'lng' values for each active trolley
    """
    trolleys = fetch_trolley_locations_from_VM(1)

    #for id in ACTIVE_TROLLEY_IDS:
        #location = fetch_trolley_location(id)
        #if location:    
            #trolleys.append({"id": id, "lat": location["lat"], "lng": location["lng"]})
        
    return jsonify(trolleys)

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
    trolley_location = fetch_trolley_location() # FOR TESTING: {"lat": 33.421072548282694, "lng": -111.93998403404477} 
    if not trolley_location:
        return jsonify({"error": "Trolley location unavailable."}), 503
    return jsonify(trolley_location)


if __name__ == "__main__":
    app.run(debug=True)