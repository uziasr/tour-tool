from typing import List, Dict, Any
from requests import get
import os
from dotenv import load_dotenv

from contants import KIND_SCORES, Coordinate, Coordinates, DEFAULT_RADIUS
import numpy as np


load_dotenv()
API_KEY = os.environ.get('OPEN_TRIP_API_KEY')
BASE_PATH = os.environ.get('OPEN_TRIP_BASE_URL')


def construct_url(coord: Coordinate, radius: int = DEFAULT_RADIUS) -> str:
    """
    Constructs the URL for the OpenTrip API request.
    :param coord: A coordinate in the format [longitude, latitude].
    :param radius: The radius in meters to search around the coordinate.
    :return: The complete URL for the API request.
    """

    lat, lon = coord
    return (
        f'{BASE_PATH}radius?radius={radius}&lon={lon}'
        f'&lat={lat}&apikey={API_KEY}'
    )


def call_api(
        coord: Coordinate,
        radius: int = DEFAULT_RADIUS
) -> List[Dict[str, Any]]:
    """
    Calls the OpenTrip API to get places around a coordinate.
    :param coord: A coordinate in the format [longitude, latitude].
    :param radius: The radius in meters to search around the coordinate.
    :return: A list of places with their details.
    """
    url = construct_url(coord, radius)
    response = get(url)
    print(url)
    if response.status_code != 200:
        raise Exception(
            f"Error fetching data from OpenTrip API: {response.status_code}")

    return response.json().get('features', [])


def score_poi(poi, kind_scores=KIND_SCORES):
    """
    Scores a POI based on its 'kinds' tags.
    Higher scores mean more interesting/relevant for road trip stops.
    """
    kinds = poi.get("kinds", "")
    tags = kinds.split(',')
    # calculates score based on the kind and weight it has
    base_score = sum(kind_scores.get(tag.strip(), 0) for tag in tags)
    # popularity will increase the score
    popularity = poi.get("rate", 0)
    summary_bonus = 5 if poi.get("wikidata") else 0

    # Sum all known tag scores (or default to 0)
    return base_score + (2 * popularity) + summary_bonus


def get_top_pois(pois, top_n=10):
    """
    Takes a list of POIs and returns the top N by quality score.
    """
    scored = [
        {**poi, "score": score_poi(poi['properties'])} for poi in pois
    ]

    # Sort by score descending
    top = sorted(scored, key=lambda x: x["score"], reverse=True)
    top_poi = []
    for poi in top:
        if len(top_poi) == top_n:
            return top_poi
        elif poi['properties'].get('name') == '':
            continue
        top_poi.append(poi)

    return top_poi


def get_wikipedia_data(poi_title: str):
    """
    Fetches Wikipedia data for a given POI title.
    :param poi_title: The title of the POI to fetch data for.
    :return: A dictionary containing the Wikipedia data.
    """
    url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{poi_title}'
    response = get(url)
    if response.status_code != 200:
        return None
    return response.json()


class OpenTripInterface:
    """
    A class to interact with the OpenTrip API to get trip information
    based on coordinates.
    """

    def __init__(self, coords: Coordinates, hash: str = None):
        """
        Initializes the NominatimInterface with coordinates.
        :param coords: A list of coordinates where each coordinate is a list
        of [longitude, latitude].
        """
        # Contains the coordinates of the stops
        self.coords = coords

    def get_places(self, radius: int = DEFAULT_RADIUS) -> List[Dict[str, Any]]:
        all_pois = []
        for coord in self.coords:
            pois = call_api(coord, radius)
            # gets the top POIs based on their quality score
            top_pois = get_top_pois(pois)
            for poi in top_pois:
                poi['source_coord'] = coord
            all_pois.extend(top_pois)

        # Get median score for all POIs
        median = np.median([poi['score'] for poi in all_pois])
        # Filter out POIs that are below the median score
        all_pois = [poi for poi in all_pois if poi['score'] >= median]
        all_pois_sorted = sorted(
            all_pois, key=lambda x: x['score'], reverse=True)

        count = 0
        for poi in all_pois_sorted:
            poi['properties']['wikipedia'] = None
            if 'name' in poi['properties']:
                # Fetch Wikipedia data for the POI
                wiki_data = get_wikipedia_data(poi['properties']['name'])
                if wiki_data:
                    poi['properties']['wikipedia'] = wiki_data

                    count += 1
            if count >= 10:
                break

        return all_pois


# def new_test():
#     from tools.open_route import test
#     dist = test()
#     dist.get_coords_based_on_interval()

#     trip_interface = OpenTripInterface(dist.stop_coordinates)
#     trip_interface.get_places()
