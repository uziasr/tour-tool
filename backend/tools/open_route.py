import requests
from typing import Union
from dotenv import load_dotenv
import os
import json
from haversine import haversine, Unit

from typing import NoReturn
from tools.general import meters_to_miles
from tools.route_classifier import RouteLengths, RouteStops
from requests import get

DIRECTIONS = 'directions'
TRANSPORTATION_MODE = 'driving-car'

load_dotenv()
API_KEY = os.environ.get('OPEN_ROUTE_API_KEY')
BASE_API_URL = os.environ.get('OPEN_ROUTE_BASE_URL')


def format_coordinates_query_parameter(
        start_latitude: Union[str, float],
        start_longitude: Union[str, float],
        end_latitude: Union[str, float],
        end_longitude: Union[str, float]
) -> str:
    """
        Formats the coordinates into a query parameter string for the
        OpenRouteService API.
        :param start_latitude: Latitude of the starting point.
        :param start_longitude: Longitude of the starting point.
        :param end_latitude: Latitude of the ending point.
        :param end_longitude: Longitude of the ending point.
        :return: A string formatted as 'start=lat,long&end=lat,long'.
    """
    return (
        f'start={start_latitude},{start_longitude}&'
        f'end={end_latitude},{end_longitude}'
    )


def get_coords(place: str, user_agent="my-roadtrip-app/0.1 (your@email.com)"):
    """
    Get the latitude and longitude of a place using Nominatim.

    Args:
        place (str): Place name (e.g. "Toronto, Canada")
        user_agent (str): A valid user agent with contact info

    Returns:
        (lat, lon) as floats if found, otherwise None
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": user_agent
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates: {e}")
        return None


def call_api(location_start: str, location_end: str):
    start_coords = get_coords(location_start)
    end_coords = get_coords(location_end)
    coords = format_coordinates_query_parameter(
        start_coords[1], start_coords[0],
        end_coords[1], end_coords[0]
    )
    url = construct_url(coords)
    response = get(url)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()


def construct_url(coords: str) -> str:
    """"
    Constructs the URL for the OpenRouteService API request.
    :param coords: The formatted coordinates query parameter.
    :return: The complete URL for the API request.
    """
    return (
        f'{BASE_API_URL}{DIRECTIONS}/{TRANSPORTATION_MODE}'
        f'?{coords}&api_key={API_KEY}'
    )


class OpenRouteDirections:
    """
    A class to interact with the OpenRouteService API to get directions.
    """

    def __init__(self, payload: dict):
        """
        Initializes the OpenRouteDirections with a payload.
        :param payload: A dictionary containing
        the coordinates and other parameters.
        """
        # The payload should contain the response from the OpenRouteService API
        # Includes the directions, geometry, and summary of the route
        self.payload = payload

        self.length = self.get_length()  # Length of the route in miles

        # Determine the type of route based on its length
        self.route_type = RouteLengths.get_length_range(self.length)
        # Set the number of stops based on the route type
        self.stops = getattr(RouteStops, self.route_type.name).value

        # Sets the route interval based on the length and number of stops
        self.stop_interval = self.length / self.stops if self.stops > 0 else 0
        self.stop_coordinates = []  # will contain the coordinates of the stops

    def get_length(self) -> float:
        """
        Returns the length of the route in meters.
        :return: The length of the route in meters.
        """
        return meters_to_miles(
            self.payload['features'][0]['properties']['summary']['distance']
        )

    def get_stops_based_on_geometry(self) -> int:
        """
        Returns the number of stops based on the geometry of the route.
        :return: The number of stops.
        """
        return len(self.payload['features'][0]['geometry']['coordinates'])

    def get_coords_based_on_interval(self) -> NoReturn:
        """
        Populates the stop_coordinates
        list with coordinates at regular intervals
        """
        coords = self.payload['features'][0]['geometry']['coordinates']

        if coords is None or len(coords) <= 1:
            return coords[::-1] if coords else []

        miles_accumulated = 0

        curr = 1
        for prev_idx in range(len(coords) - 1):
            prev = coords[prev_idx]
            next_coord = coords[curr]

            # Calculate the distance between the previous and next coordinates
            distance = haversine(
                (prev[1], prev[0]), (next_coord[1], next_coord[0]),
                unit=Unit.MILES
            )

            miles_accumulated += distance

            if miles_accumulated >= self.stop_interval:
                # Append in (lat, long) format
                self.stop_coordinates.append(next_coord[::-1])
                miles_accumulated = 0

            curr += 1


def test() -> OpenRouteDirections:
    with open('./tools/directions.json', 'r') as file:
        data = json.load(file)

        directions = OpenRouteDirections(data)
        return directions


if __name__ == '__main__':
    test()
