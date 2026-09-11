"""
backend/services/routing_service.py

Computes driving distance, duration and route polyline between two coordinates.

Primary source: OpenRouteService (ORS) — free tier, 2 000 req/day.
Fallback:       Haversine straight-line estimate (no network, always works).

To enable ORS:
  1. Sign up at https://openrouteservice.org/  (free, no credit card)
  2. Copy your API key to .env:
         ORS_API_KEY=your_key_here
  3. Restart uvicorn. The service auto-detects the key.

Architecture note:
  The interface (get_route) is intentionally simple.
  To swap to Google Directions API later:
    - Change only this file's _fetch_ors_route() implementation.
    - The rest of the application is unaffected.
"""
from __future__ import annotations

import logging
import math
import os
from typing import Optional

import httpx

logger = logging.getLogger("way_transit")

ORS_API_KEY: str = os.getenv("ORS_API_KEY", "")
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

# Average driving speed used for haversine fallback (km/h)
_AVG_SPEED_KMH = 30.0


# ─── Public interface ──────────────────────────────────────────────────────────

class RouteInfo:
    """Routing result returned to callers."""
    __slots__ = ("distance_km", "duration_minutes", "polyline", "source")

    def __init__(
        self,
        distance_km: float,
        duration_minutes: int,
        polyline: Optional[str],
        source: str,
    ):
        self.distance_km = distance_km
        self.duration_minutes = duration_minutes
        self.polyline = polyline          # ORS encoded polyline or None
        self.source = source              # "ors" | "haversine"


def get_route(
    pickup_lat: float,
    pickup_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> RouteInfo:
    """
    Return driving distance, ETA, and optional polyline.
    Uses ORS if ORS_API_KEY is set; falls back to haversine otherwise.
    """
    if ORS_API_KEY:
        try:
            return _fetch_ors_route(pickup_lat, pickup_lon, dest_lat, dest_lon)
        except Exception as exc:
            logger.warning("ORS request failed (%s); falling back to haversine.", exc)

    return _haversine_estimate(pickup_lat, pickup_lon, dest_lat, dest_lon)


# ─── ORS implementation ────────────────────────────────────────────────────────

def _fetch_ors_route(
    pickup_lat: float,
    pickup_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> RouteInfo:
    """Call ORS Directions API (synchronous, runs in uvicorn worker thread)."""
    payload = {
        "coordinates": [
            [pickup_lon, pickup_lat],   # ORS uses [lon, lat]
            [dest_lon, dest_lat],
        ],
        "instructions": False,
        "geometry": True,
    }
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    with httpx.Client(timeout=10.0) as client:
        resp = client.post(ORS_BASE_URL, json=payload, headers=headers)
        resp.raise_for_status()

    data = resp.json()
    route = data["routes"][0]
    summary = route["summary"]

    distance_km = round(summary["distance"] / 1000, 2)       # metres → km
    duration_min = max(1, int(summary["duration"] / 60))      # seconds → min
    # ORS returns an encoded polyline string under geometry when geometry=True
    polyline = route.get("geometry")

    logger.info(
        "ORS route: %.2f km, %d min",
        distance_km,
        duration_min,
    )
    return RouteInfo(
        distance_km=distance_km,
        duration_minutes=duration_min,
        polyline=polyline,
        source="ors",
    )


# ─── Haversine fallback ────────────────────────────────────────────────────────

def _haversine_estimate(
    pickup_lat: float,
    pickup_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> RouteInfo:
    """
    Straight-line distance with a road-factor multiplier (1.35).
    Used when no ORS key is configured.
    """
    R = 6371.0  # Earth radius in km

    lat1, lon1 = math.radians(pickup_lat), math.radians(pickup_lon)
    lat2, lon2 = math.radians(dest_lat),   math.radians(dest_lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    straight_km = R * c
    # Roads are ~35 % longer than straight-line distance on average
    road_km = round(straight_km * 1.35, 2)
    duration_min = max(1, int((road_km / _AVG_SPEED_KMH) * 60))

    logger.debug("Haversine estimate: %.2f km (road), %d min", road_km, duration_min)
    return RouteInfo(
        distance_km=road_km,
        duration_minutes=duration_min,
        polyline=None,
        source="haversine",
    )
