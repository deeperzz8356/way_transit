"""
backend/services/providers/base_provider.py

Abstract interface every ride provider must implement.
Adding a new provider (Uber, Ola, Rapido) means:
  1. Create a new file in this directory
  2. Subclass BaseRideProvider
  3. Register it in get_provider() below
The core ride-booking logic (routes/rides.py, crud.py) never
changes when a new provider is added.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


# ─── Data transfer objects ─────────────────────────────────────────────────────

@dataclass
class RideProduct:
    """A single ride type/category offered by a provider."""
    product_id: str          # provider-specific ID, e.g. "mock_economy"
    name: str                # display name, e.g. "Economy"
    description: str         # short description
    icon: str                # emoji or asset hint, e.g. "🚗"
    capacity: int            # max passengers
    currency: str            # "INR"
    estimated_fare_min: float
    estimated_fare_max: float
    estimated_fare: float    # midpoint / recommended display value
    estimated_duration_minutes: int
    estimated_distance_km: float


@dataclass
class BookingResult:
    """Returned by the provider after successfully requesting a ride."""
    provider_ride_id: str    # provider's unique ride reference
    status: str              # our internal status (e.g. "CONFIRMED")
    provider_status: str     # raw string from the provider
    message: str = ""        # optional human-readable note


@dataclass
class CancelResult:
    """Returned by the provider after cancelling a ride."""
    success: bool
    message: str = ""


# ─── Abstract base class ───────────────────────────────────────────────────────

class BaseRideProvider(ABC):
    """
    Contract every ride provider must fulfil.
    All methods are synchronous; wrap in asyncio.to_thread if needed
    for providers with blocking HTTP clients.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Slug identifier, e.g. 'mock', 'uber'. Matches ride_providers.name."""

    @abstractmethod
    def get_products(
        self,
        pickup_lat: float,
        pickup_lon: float,
        dest_lat: float,
        dest_lon: float,
        distance_km: float,
        duration_minutes: int,
    ) -> List[RideProduct]:
        """
        Return all available ride products for this pickup→destination pair.
        The routing data (distance_km, duration_minutes) is pre-computed by
        routing_service so every provider benefits from the same source.
        """

    @abstractmethod
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
        """Return a single-product estimate (fare + ETA)."""

    @abstractmethod
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
        """
        Request a ride from the provider.
        Returns a BookingResult with the provider's ride ID.
        """

    @abstractmethod
    def cancel(
        self,
        provider_ride_id: str,
        reason: str = "Cancelled by user",
    ) -> CancelResult:
        """Cancel an existing ride."""

    @abstractmethod
    def get_status(self, provider_ride_id: str) -> str:
        """
        Poll the provider for the current ride status.
        Returns our internal status string:
        REQUESTED | CONFIRMED | ARRIVING | IN_PROGRESS | COMPLETED |
        CANCELLED | FAILED
        """


# ─── Provider registry ─────────────────────────────────────────────────────────

def get_provider(name: str) -> BaseRideProvider:
    """
    Factory: return a provider instance by slug name.
    Import here (not at module level) to avoid circular imports.

    To add a new provider:
      1. Create backend/services/providers/my_provider.py
      2. Add an entry to the dict below.
    """
    from services.providers.mock_provider import MockRideProvider
    from services.providers.uber_provider import UberRideProvider

    registry: dict[str, BaseRideProvider] = {
        "mock": MockRideProvider(),
        "uber": UberRideProvider(),
        # "ola":  OlaRideProvider(),    ← future
    }

    if name not in registry:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {list(registry.keys())}"
        )
    return registry[name]
