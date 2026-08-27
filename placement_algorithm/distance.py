"""
Distance computation between student homes and schools.

The proposal (section 3.4.4, Module 3) names two possible sources for
student-school distance: the Haversine great-circle formula, or real-world
travel distance from the Google Maps Distance Matrix API. This module
implements the Haversine version as the default, working, dependency-light
option, and defines a small interface so a Google Maps-backed implementation
can be dropped in later without touching the scoring or matching code.

Per the proposal's feasibility study (3.4.2), Haversine / OpenStreetMap
routing is also the recommended fallback when the Google Maps API budget is
constrained -- so this is not just a placeholder, it's a legitimate mode of
operation for the finished system.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import radians, sin, cos, asin, sqrt
from typing import Protocol

EARTH_RADIUS_KM = 6371.0088  # mean Earth radius (IUGG value)

# Roughly the bounding box of Kenya, used by the synthetic data generator and
# for sanity-checking coordinates elsewhere in the package.
KENYA_LAT_RANGE = (-4.72, 5.03)
KENYA_LON_RANGE = (33.90, 41.91)


@dataclass(frozen=True)
class Coordinates:
    """A latitude/longitude pair in decimal degrees."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError(f"latitude out of range: {self.lat}")
        if not -180.0 <= self.lon <= 180.0:
            raise ValueError(f"longitude out of range: {self.lon}")


class DistanceProvider(Protocol):
    """Interface any distance backend (Haversine, Google Maps, OSRM, ...) must
    satisfy so it can be swapped into the scoring module without changes
    elsewhere."""

    def distance_km(self, origin: Coordinates, destination: Coordinates) -> float:
        ...


class HaversineDistanceProvider:
    """Great-circle distance in kilometres. No network calls, no API key --
    this is the default provider and what the synthetic-data demo runs use."""

    def distance_km(self, origin: Coordinates, destination: Coordinates) -> float:
        lat1, lon1, lat2, lon2 = map(
            radians, (origin.lat, origin.lon, destination.lat, destination.lon)
        )
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return EARTH_RADIUS_KM * c


class GoogleMapsDistanceProvider:
    """Stub for a real-world-road-distance backend using the Google Maps
    Distance Matrix API. Not wired up to a live API key in this codebase --
    fill in `_call_api` with an actual `googlemaps` client call when an API
    key is available, per the proposal's Module 3 technology list.

    Left deliberately unimplemented (raises NotImplementedError) rather than
    silently falling back to Haversine, so it's obvious at call time that
    this path needs an API key before it can be used.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def distance_km(self, origin: Coordinates, destination: Coordinates) -> float:
        if not self.api_key:
            raise RuntimeError(
                "GoogleMapsDistanceProvider requires an API key. "
                "Use HaversineDistanceProvider for development/testing."
            )
        return self._call_api(origin, destination)

    def _call_api(self, origin: Coordinates, destination: Coordinates) -> float:
        raise NotImplementedError(
            "Wire this up to googlemaps.Client(...).distance_matrix(...) "
            "once an API key is provisioned."
        )


def haversine_km(origin: Coordinates, destination: Coordinates) -> float:
    """Convenience function form of HaversineDistanceProvider, for callers
    that don't need the Protocol/DI machinery."""
    return HaversineDistanceProvider().distance_km(origin, destination)
