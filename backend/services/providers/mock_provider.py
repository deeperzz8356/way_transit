"""
backend/services/providers/mock_provider.py

Simulated ride provider for development and testing.
Returns realistic-looking data calculated from the actual route distance.
Behaves identically to what a real provider would return — so the
Flutter UI can be built and tested without any external accounts.

Fare model (INR):
  Economy:  ₹12/km  + ₹30 base  + ₹1.5/min
  Premium:  ₹18/km  + ₹60 base  + ₹2.0/min
  Bike:     ₹7/km   + ₹15 base  + ₹1.0/min
  XL (6-seat): ₹20/km + ₹80 base + ₹2.5/min
"""
from __future__ import annotations

import uuid
import math
import random
from typing import List

from services.providers.base_provider import (
    BaseRideProvider,
    BookingResult,
    CancelResult,
    RideProduct,
)


# ── Ride product definitions ───────────────────────────────────────────────────

_PRODUCTS = [
    {
        "product_id": "mock_economy",
        "name": "Economy",
        "description": "Affordable everyday rides",
        "icon": "directions_car",
        "capacity": 4,
        "base_fare": 30.0,
        "per_km": 12.0,
        "per_min": 1.5,
        "surge_range": (1.0, 1.3),
    },
    {
        "product_id": "mock_premium",
        "name": "Premium",
        "description": "Comfortable rides in top-rated cars",
        "icon": "star",
        "capacity": 4,
        "base_fare": 60.0,
        "per_km": 18.0,
        "per_min": 2.0,
        "surge_range": (1.0, 1.5),
    },
    {
        "product_id": "mock_bike",
        "name": "Bike",
        "description": "Quick & cheap bike rides",
        "icon": "two_wheeler",
        "capacity": 1,
        "base_fare": 15.0,
        "per_km": 7.0,
        "per_min": 1.0,
        "surge_range": (1.0, 1.2),
    },
    {
        "product_id": "mock_xl",
        "name": "XL",
        "description": "Spacious rides for groups up to 6",
        "icon": "airport_shuttle",
        "capacity": 6,
        "base_fare": 80.0,
        "per_km": 20.0,
        "per_min": 2.5,
        "surge_range": (1.0, 1.4),
    },
]


def _compute_fare(product: dict, distance_km: float, duration_minutes: int) -> tuple[float, float, float]:
    """Return (min_fare, max_fare, midpoint_fare) rounded to nearest rupee."""
    surge_lo, surge_hi = product["surge_range"]
    base = product["base_fare"]
    km_cost = product["per_km"] * distance_km
    min_cost = product["per_min"] * duration_minutes

    fare_lo = round((base + km_cost + min_cost) * surge_lo)
    fare_hi = round((base + km_cost + min_cost) * surge_hi)
    fare_mid = round((fare_lo + fare_hi) / 2)
    return float(fare_lo), float(fare_hi), float(fare_mid)


class MockRideProvider(BaseRideProvider):
    """
    Simulated provider — no network calls, no external accounts required.
    All responses are deterministic given the same inputs (reproducible).
    """

    @property
    def name(self) -> str:
        return "mock"

    def get_products(
        self,
        pickup_lat: float,
        pickup_lon: float,
        dest_lat: float,
        dest_lon: float,
        distance_km: float,
        duration_minutes: int,
    ) -> List[RideProduct]:
        products = []
        for p in _PRODUCTS:
            fare_min, fare_max, fare_mid = _compute_fare(p, distance_km, duration_minutes)
            # Vary ETA slightly per product type
            eta_offset = {"mock_economy": 0, "mock_premium": 2, "mock_bike": -2, "mock_xl": 3}
            eta = max(1, duration_minutes + eta_offset.get(p["product_id"], 0))
            products.append(
                RideProduct(
                    product_id=p["product_id"],
                    name=p["name"],
                    description=p["description"],
                    icon=p["icon"],
                    capacity=p["capacity"],
                    currency="INR",
                    estimated_fare_min=fare_min,
                    estimated_fare_max=fare_max,
                    estimated_fare=fare_mid,
                    estimated_duration_minutes=eta,
                    estimated_distance_km=round(distance_km, 2),
                )
            )
        return products

    def estimate(
        self,
        product_id: str,
        pickup_lat: float,
        pickup_lon: float,
        dest_lat: float,
        dest_lon: float,
        distance_km: float,
        duration_minutes: int,
    ) -> RideProduct:
        product_def = next((p for p in _PRODUCTS if p["product_id"] == product_id), None)
        if not product_def:
            raise ValueError(f"Unknown mock product_id: '{product_id}'")

        fare_min, fare_max, fare_mid = _compute_fare(product_def, distance_km, duration_minutes)
        return RideProduct(
            product_id=product_def["product_id"],
            name=product_def["name"],
            description=product_def["description"],
            icon=product_def["icon"],
            capacity=product_def["capacity"],
            currency="INR",
            estimated_fare_min=fare_min,
            estimated_fare_max=fare_max,
            estimated_fare=fare_mid,
            estimated_duration_minutes=duration_minutes,
            estimated_distance_km=round(distance_km, 2),
        )

    def book(
        self,
        product_id: str,
        pickup_lat: float,
        pickup_lon: float,
        pickup_address: str,
        dest_lat: float,
        dest_lon: float,
        dest_address: str,
        user_id: int,
    ) -> BookingResult:
        # Simulate a provider accepting the ride and issuing an external ride ID.
        # In a real provider this would be an HTTP POST that returns a ride object.
        provider_ride_id = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
        return BookingResult(
            provider_ride_id=provider_ride_id,
            status="CONFIRMED",
            provider_status="accepted",
            message="Ride confirmed by mock provider. A simulated driver is on the way.",
        )

    def cancel(
        self,
        provider_ride_id: str,
        reason: str = "Cancelled by user",
    ) -> CancelResult:
        # Mock always accepts cancellation
        return CancelResult(success=True, message=f"Ride {provider_ride_id} cancelled.")

    def get_status(self, provider_ride_id: str) -> str:
        # In a real provider this polls an external API.
        # Mock always returns CONFIRMED (driver on the way).
        return "CONFIRMED"
