from enum import Enum
import numpy as np


class RouteStops(Enum):
    # number of stops
    SHORT = 3
    MEDIUM = 6
    LONG = 10
    EXTRA_LONG = 15


class RouteLengths(Enum):
    # length of the route in miles
    SHORT = 0, 10  # Will be a short drive, can be long if there is traffic
    MEDIUM = 11, 50
    LONG = 51, 500
    # Will be a long drive, can be long if there is traffic
    EXTRA_LONG = 500, np.inf

    @staticmethod
    def get_length_range(route_length: float) -> 'RouteLengths':
        """
        Get the route length range based on the given route length.
        :param route_length: The length of the route in miles.
        :return: The corresponding RouteLengths enum value.
        """
        for length in RouteLengths:
            if length.value[0] <= route_length < length.value[1]:
                return length

        # Default to EXTRA_LONG if no match found
        return RouteLengths.EXTRA_LONG


ROUTE_LENGTHS = []
