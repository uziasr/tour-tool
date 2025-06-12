from typing import List

type Coordinate = List[float]  # [longitude, latitude]
type Coordinates = List[Coordinate]  # List of [longitude, latitude] pairs

DEFAULT_RADIUS = 10000  # Default radius in meters for OpenTrip API requests


KIND_SCORES = {
    "museums": 9,
    "science_museums": 8,
    "art_galleries": 8,
    "historic": 10,
    "historic_architecture": 9,
    "monuments_and_memorials": 9,
    "cultural": 7,
    "churches": 6,
    "temples": 6,
    "view_points": 5,  # less relevant but still nice
    "destroyed_objects": -100,
    "theatres_and_entertainments": -100,
    "cemeteries": -100,
}

DIRECTION_FILE_NAME = "directions.json"
POI_FILE_NAME = "pois.json"
