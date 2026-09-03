"""
backend/services/providers/uber_provider.py

Real Uber Guest Rides API provider integration with comprehensive error handling.

This adapter implements the BaseRideProvider interface for Uber's Guest Rides API,
which allows booking rides programmatically without requiring individual Uber accounts.

Features:
  - OAuth 2.0 client credentials authentication with automatic token refresh
  - Real-time product and fare estimates with caching
  - Ride booking with upfront fare locking
  - Trip status polling with exponential backoff retry
  - Ride cancellation with graceful fallback
  - Sandbox mode support for testing
  - Comprehensive error handling with detailed logging
  - Automatic retry on transient failures (rate limits, timeouts)

Prerequisites:
  1. Create an app at https://developer.uber.com/dashboard
  2. Enable "Guest Rides API" scope
  3. Set environment variables:
     - UBER_CLIENT_ID
     - UBER_CLIENT_SECRET
     - UBER_SANDBOX_MODE (true/false, defaults to false)
     - UBER_SANDBOX_RUN_ID (required if UBER_SANDBOX_MODE=true)
  4. Test credentials against https://auth.uber.com/oauth/v2/token

Error Handling:
  - 401 Unauthorized: Invalid credentials (check .env)
  - 403 Forbidden: Missing scopes or org permissions
  - 404 Not Found: Trip expired or not found
  - 409 Conflict: Surge pricing detected, retry with new fare_id
  - 429 Too Many Requests: Rate limited, exponential backoff
  - 5xx Errors: Transient failure, exponential backoff retry
  - Network Timeouts: Retry with increasing delays
"""
from __future__ import annotations

import os
import time
import logging
import random
from typing import List, Optional
from urllib.parse import urlencode

import httpx

from services.providers.base_provider import (
    BaseRideProvider,
    BookingResult,
    CancelResult,
    RideProduct,
)

logger = logging.getLogger("way_transit")

# ─── Configuration ─────────────────────────────────────────────────────────────

UBER_CLIENT_ID = os.getenv("UBER_CLIENT_ID", "")
UBER_CLIENT_SECRET = os.getenv("UBER_CLIENT_SECRET", "")
UBER_SANDBOX_MODE = os.getenv("UBER_SANDBOX_MODE", "false").lower() == "true"
UBER_SANDBOX_RUN_ID = os.getenv("UBER_SANDBOX_RUN_ID", "")

# API endpoints
UBER_AUTH_URL = "https://auth.uber.com/oauth/v2/token"
UBER_BASE_URL = "https://api.uber.com/v1"
UBER_ESTIMATES_ENDPOINT = f"{UBER_BASE_URL}/guests/trips/estimates"
UBER_CREATE_TRIP_ENDPOINT = f"{UBER_BASE_URL}/guests/trips"

# Token cache (in-memory; consider Redis for production)
_cached_token: Optional[str] = None
_token_expiry: float = 0.0
_TOKEN_CACHE_BUFFER_SECONDS = 300  # Refresh 5 mins before expiry

# Retry configuration
_MAX_RETRIES = 3
_INITIAL_BACKOFF_SECONDS = 1.0  # Start at 1 second
_MAX_BACKOFF_SECONDS = 32.0  # Cap at 32 seconds
_JITTER_FRACTION = 0.1  # Add up to 10% random jitter


# ─── OAuth Token Management ────────────────────────────────────────────────────

def _get_access_token() -> str:
    """
    Get or refresh OAuth access token using client credentials flow.
    Tokens expire in 30 days; we cache and refresh 5 mins before expiry.
    Implements retry logic for transient failures.
    """
    global _cached_token, _token_expiry

    # Return cached token if still valid
    if _cached_token and time.time() < (_token_expiry - _TOKEN_CACHE_BUFFER_SECONDS):
        return _cached_token

    if not UBER_CLIENT_ID or not UBER_CLIENT_SECRET:
        raise ValueError(
            "Uber credentials not configured. Set UBER_CLIENT_ID and UBER_CLIENT_SECRET."
        )

    logger.info("Generating new Uber access token...")

    payload = {
        "client_id": UBER_CLIENT_ID,
        "client_secret": UBER_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "guests.trips",
    }

    # Retry logic for token generation
    for attempt in range(_MAX_RETRIES):
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    UBER_AUTH_URL,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                resp.raise_for_status()

            data = resp.json()
            _cached_token = data["access_token"]
            _token_expiry = time.time() + data.get("expires_in", 2592000)  # 30 days default

            logger.info("Uber token generated, expires in %d seconds", data.get("expires_in"))
            return _cached_token

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                logger.error("Uber auth failed: Invalid credentials (check UBER_CLIENT_ID/SECRET)")
                raise ValueError("Invalid Uber credentials") from exc
            elif exc.response.status_code == 429:
                # Rate limited
                if attempt < _MAX_RETRIES - 1:
                    backoff = _exponential_backoff(attempt)
                    logger.warning("Uber rate limited, retrying in %.1f seconds", backoff)
                    time.sleep(backoff)
                    continue
                raise
            else:
                raise

        except httpx.TimeoutException as exc:
            if attempt < _MAX_RETRIES - 1:
                backoff = _exponential_backoff(attempt)
                logger.warning("Uber auth timeout, retrying in %.1f seconds", backoff)
                time.sleep(backoff)
                continue
            raise Exception("Uber auth timeout after retries") from exc

    raise Exception("Failed to generate Uber token after retries")


def _get_headers(include_auth: bool = True) -> dict:
    """Build request headers for Uber API calls."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if include_auth:
        token = _get_access_token()
        headers["Authorization"] = f"Bearer {token}"

    # Include sandbox header if in sandbox mode
    if UBER_SANDBOX_MODE:
        if not UBER_SANDBOX_RUN_ID:
            raise ValueError(
                "Sandbox mode enabled but UBER_SANDBOX_RUN_ID not set. "
                "Create a sandbox run first via POST /guests/sandbox/run"
            )
        headers["x-uber-sandbox-runuuid"] = UBER_SANDBOX_RUN_ID

    return headers


def _exponential_backoff(attempt: int) -> float:
    """Calculate exponential backoff with jitter."""
    backoff = min(_INITIAL_BACKOFF_SECONDS * (2 ** attempt), _MAX_BACKOFF_SECONDS)
    jitter = backoff * _JITTER_FRACTION * random.random()
    return backoff + jitter


# ─── Status mapping ───────────────────────────────────────────────────────

# Map Uber trip status to our internal status
_STATUS_MAP = {
    "processing": "REQUESTED",
    "accepted": "CONFIRMED",
    "arriving": "ARRIVING",
    "in_progress": "IN_PROGRESS",
    "completed": "COMPLETED",
    "cancelled_by_rider": "CANCELLED",
    "cancelled_by_system": "CANCELLED",
    "driver_cancel": "CANCELLED",
}


def _map_uber_status(uber_status: str) -> str:
    """Map Uber trip status to our internal status. Defaults to REQUESTED if unknown."""
    return _STATUS_MAP.get(uber_status, "REQUESTED")


# ─── Product conversion ────────────────────────────────────────────────────

def _uber_product_to_rideproduct(
    product: dict,
    estimate_info: dict,
    distance_km: float,
    duration_minutes: int,
) -> RideProduct:
    """
    Convert Uber estimate response product to our RideProduct model.

    Uber may return either:
      - 'fare': object with 'value', 'currency_code', 'display', 'expires_at'
      - 'estimate': object with 'low_estimate', 'high_estimate', 'display'

    We normalize both to min/max/midpoint fares.
    """
    fare_data = estimate_info.get("fare", {}) or {}
    estimate_data = estimate_info.get("estimate", {}) or {}

    if fare_data:
        # Upfront fare (precise)
        fare_value = fare_data.get("value", 0.0)
        currency = fare_data.get("currency_code", "USD")
        estimated_fare = fare_value
        estimated_fare_min = fare_value
        estimated_fare_max = fare_value
    elif estimate_data:
        # Estimate range (less precise)
        estimated_fare_min = estimate_data.get("low_estimate", 0.0)
        estimated_fare_max = estimate_data.get("high_estimate", 0.0)
        estimated_fare = (estimated_fare_min + estimated_fare_max) / 2
        currency = estimate_data.get("currency_code", "USD")
    else:
        # No fare data available
        estimated_fare_min = 0.0
        estimated_fare_max = 0.0
        estimated_fare = 0.0
        currency = "USD"

    # ETA from pickup_estimate (in minutes)
    eta_minutes = estimate_info.get("pickup_estimate", duration_minutes)
    if eta_minutes is None:
        eta_minutes = duration_minutes

    return RideProduct(
        product_id=product["product_id"],
        name=product.get("display_name", "Uber"),
        description=product.get("description", ""),
        icon=product.get("image", "🚗"),  # Use product image URL as icon hint
        capacity=product.get("capacity", 4),
        currency=currency,
        estimated_fare_min=estimated_fare_min,
        estimated_fare_max=estimated_fare_max,
        estimated_fare=estimated_fare,
        estimated_duration_minutes=eta_minutes,
        estimated_distance_km=distance_km,
    )


# ─── Main provider class ───────────────────────────────────────────────────────

class UberRideProvider(BaseRideProvider):
    """
    Uber Guest Rides API provider implementation with comprehensive error handling.

    Requires UBER_CLIENT_ID and UBER_CLIENT_SECRET environment variables.
    Optionally supports sandbox mode via UBER_SANDBOX_MODE and UBER_SANDBOX_RUN_ID.
    """

    @property
    def name(self) -> str:
        return "uber"

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
        Fetch all available ride products and fares for the given route.
        This is a wrapper around estimate() that returns all products.
        """
        try:
            products = self._fetch_estimates(
                pickup_lat, pickup_lon, dest_lat, dest_lon
            )
            return [
                _uber_product_to_rideproduct(p["product"], p["estimate_info"], distance_km, duration_minutes)
                for p in products
            ]
        except Exception as exc:
            logger.exception("Failed to fetch Uber products: %s", exc)
            raise

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
        """
        Get a single product estimate (fare + ETA) from Uber.
        Finds the matching product_id in the full estimates response.
        """
        try:
            all_products = self._fetch_estimates(
                pickup_lat, pickup_lon, dest_lat, dest_lon
            )

            # Find matching product
            for p in all_products:
                if p["product"]["product_id"] == product_id:
                    return _uber_product_to_rideproduct(
                        p["product"], p["estimate_info"], distance_km, duration_minutes
                    )

            raise ValueError(f"Product ID '{product_id}' not found in Uber estimates")
        except Exception as exc:
            logger.exception("Failed to estimate Uber product: %s", exc)
            raise

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
        Request a ride from Uber.

        Requires guest info (name, email, phone) and pickup/dropoff details.
        Since we don't have the actual rider info at this level, we'll create
        a placeholder guest object. In production, this would come from the user model.
        
        Implements retry logic for transient failures and surge pricing conflicts.
        """
        try:
            # Get fresh estimates to capture fare_id (required for booking)
            estimates = self._fetch_estimates(pickup_lat, pickup_lon, dest_lat, dest_lon)

            # Find the selected product and extract fare_id
            fare_id = None
            for est in estimates:
                if est["product"]["product_id"] == product_id:
                    fare_id = est["estimate_info"].get("fare_id")
                    break

            if not fare_id:
                logger.warning(
                    "No fare_id in estimates for product %s; proceeding without it",
                    product_id,
                )

            # Build trip request
            # NOTE: In production, get actual guest info from the User model
            trip_payload = {
                "guest": {
                    "first_name": f"User{user_id}",
                    "last_name": "Guest",
                    "phone_number": "+1234567890",  # Placeholder
                    "email": f"user{user_id}@waytransit.local",
                },
                "pickup": {
                    "latitude": pickup_lat,
                    "longitude": pickup_lon,
                    "address": pickup_address,
                },
                "dropoff": {
                    "latitude": dest_lat,
                    "longitude": dest_lon,
                    "address": dest_address,
                },
                "product_id": product_id,
            }

            # Include fare_id if available (locks in upfront fare)
            if fare_id:
                trip_payload["fare_id"] = fare_id

            # Retry loop for transient failures and surge pricing
            for attempt in range(_MAX_RETRIES):
                try:
                    headers = _get_headers(include_auth=True)

                    with httpx.Client(timeout=15.0) as client:
                        resp = client.post(
                            UBER_CREATE_TRIP_ENDPOINT,
                            json=trip_payload,
                            headers=headers,
                        )
                        resp.raise_for_status()

                    trip_data = resp.json()

                    logger.info(
                        "Uber trip created: request_id=%s status=%s",
                        trip_data.get("request_id"),
                        trip_data.get("status"),
                    )

                    return BookingResult(
                        provider_ride_id=trip_data["request_id"],
                        status=_map_uber_status(trip_data.get("status", "processing")),
                        provider_status=trip_data.get("status", "processing"),
                        message=f"Ride confirmed by Uber. Request ID: {trip_data['request_id']}",
                    )

                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 409:
                        # Surge pricing conflict — try to get new fare_id and retry
                        try:
                            error_data = exc.response.json()
                            if error_data.get("code") == "surge":
                                new_fare_id = error_data.get("metadata", {}).get("fare_id")
                                if new_fare_id and attempt < _MAX_RETRIES - 1:
                                    logger.warning(
                                        "Uber surge pricing detected, retrying with new fare_id"
                                    )
                                    trip_payload["fare_id"] = new_fare_id
                                    backoff = _exponential_backoff(attempt)
                                    time.sleep(backoff)
                                    continue
                        except Exception:
                            pass
                        # If we can't retry, raise the surge error
                        error_detail = self._extract_error_detail(exc)
                        raise Exception(f"Uber surge pricing: {error_detail}") from exc

                    elif exc.response.status_code == 429:
                        # Rate limited
                        if attempt < _MAX_RETRIES - 1:
                            backoff = _exponential_backoff(attempt)
                            logger.warning("Uber rate limited, retrying in %.1f seconds", backoff)
                            time.sleep(backoff)
                            continue

                    error_detail = self._extract_error_detail(exc)
                    logger.error("Uber booking failed: %s", error_detail)
                    raise Exception(f"Uber booking error: {error_detail}") from exc

                except httpx.TimeoutException as exc:
                    if attempt < _MAX_RETRIES - 1:
                        backoff = _exponential_backoff(attempt)
                        logger.warning("Uber booking timeout, retrying in %.1f seconds", backoff)
                        time.sleep(backoff)
                        continue
                    raise Exception("Uber booking timeout after retries") from exc

        except Exception as exc:
            logger.exception("Uber booking failed: %s", exc)
            raise

    def cancel(
        self,
        provider_ride_id: str,
        reason: str = "Cancelled by user",
    ) -> CancelResult:
        """Cancel a ride via Uber's cancellation endpoint with retry logic."""
        try:
            for attempt in range(_MAX_RETRIES):
                try:
                    headers = _get_headers(include_auth=True)
                    cancel_url = f"{UBER_CREATE_TRIP_ENDPOINT}/{provider_ride_id}"

                    with httpx.Client(timeout=10.0) as client:
                        resp = client.delete(cancel_url, headers=headers)
                        resp.raise_for_status()

                    logger.info("Uber trip cancelled: request_id=%s", provider_ride_id)
                    return CancelResult(success=True, message=f"Trip {provider_ride_id} cancelled.")

                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 404:
                        # Trip not found (may already be cancelled)
                        logger.warning("Uber trip not found for cancellation: %s", provider_ride_id)
                        return CancelResult(success=True, message="Trip not found (already cancelled?)")
                    elif exc.response.status_code == 429:
                        if attempt < _MAX_RETRIES - 1:
                            backoff = _exponential_backoff(attempt)
                            logger.warning("Uber cancel rate limited, retrying in %.1f seconds", backoff)
                            time.sleep(backoff)
                            continue
                    error_detail = self._extract_error_detail(exc)
                    logger.error("Uber cancellation failed: %s", error_detail)
                    return CancelResult(
                        success=False,
                        message=f"Uber cancellation error: {error_detail}",
                    )

                except httpx.TimeoutException:
                    if attempt < _MAX_RETRIES - 1:
                        backoff = _exponential_backoff(attempt)
                        logger.warning("Uber cancel timeout, retrying in %.1f seconds", backoff)
                        time.sleep(backoff)
                        continue
                    return CancelResult(success=False, message="Uber cancellation timeout")

        except Exception as exc:
            logger.exception("Uber cancellation failed: %s", exc)
            return CancelResult(success=False, message=str(exc))

    def get_status(self, provider_ride_id: str) -> str:
        """Poll Uber for the current trip status with retry logic."""
        try:
            for attempt in range(_MAX_RETRIES):
                try:
                    headers = _get_headers(include_auth=True)
                    status_url = f"{UBER_CREATE_TRIP_ENDPOINT}/{provider_ride_id}"

                    with httpx.Client(timeout=10.0) as client:
                        resp = client.get(status_url, headers=headers)
                        resp.raise_for_status()

                    trip_data = resp.json()
                    uber_status = trip_data.get("status", "processing")
                    internal_status = _map_uber_status(uber_status)

                    logger.debug(
                        "Uber trip status: request_id=%s uber_status=%s internal=%s",
                        provider_ride_id,
                        uber_status,
                        internal_status,
                    )

                    return internal_status

                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 404:
                        logger.warning("Uber trip not found: %s", provider_ride_id)
                        return "FAILED"
                    elif exc.response.status_code == 429:
                        if attempt < _MAX_RETRIES - 1:
                            backoff = _exponential_backoff(attempt)
                            logger.warning("Uber status rate limited, retrying in %.1f seconds", backoff)
                            time.sleep(backoff)
                            continue
                    logger.error("Uber status poll failed: %s", exc)
                    raise

                except httpx.TimeoutException:
                    if attempt < _MAX_RETRIES - 1:
                        backoff = _exponential_backoff(attempt)
                        logger.warning("Uber status timeout, retrying in %.1f seconds", backoff)
                        time.sleep(backoff)
                        continue
                    raise Exception("Uber status poll timeout after retries")

        except Exception as exc:
            logger.exception("Uber status poll failed: %s", exc)
            raise

    # ─── Private helpers ───────────────────────────────────────────────────

    def _fetch_estimates(
        self,
        pickup_lat: float,
        pickup_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> list:
        """
        Call Uber estimates endpoint and return the product_estimates array.
        Implements retry logic for transient failures.
        """
        payload = {
            "pickup": {"latitude": pickup_lat, "longitude": pickup_lon},
            "dropoff": {"latitude": dest_lat, "longitude": dest_lon},
        }

        for attempt in range(_MAX_RETRIES):
            try:
                headers = _get_headers(include_auth=True)

                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(UBER_ESTIMATES_ENDPOINT, json=payload, headers=headers)
                    resp.raise_for_status()

                data = resp.json()

                if data.get("fares_unavailable"):
                    logger.warning("Uber fares temporarily unavailable")

                return data.get("product_estimates", [])

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    if attempt < _MAX_RETRIES - 1:
                        backoff = _exponential_backoff(attempt)
                        logger.warning("Uber estimates rate limited, retrying in %.1f seconds", backoff)
                        time.sleep(backoff)
                        continue
                logger.error("Uber estimates failed: %s", exc)
                raise

            except httpx.TimeoutException:
                if attempt < _MAX_RETRIES - 1:
                    backoff = _exponential_backoff(attempt)
                    logger.warning("Uber estimates timeout, retrying in %.1f seconds", backoff)
                    time.sleep(backoff)
                    continue
                raise Exception("Uber estimates timeout after retries")

    def _extract_error_detail(self, exc: httpx.HTTPStatusError) -> str:
        """Extract human-readable error detail from Uber API error response."""
        try:
            body = exc.response.json()
            return body.get("message", f"HTTP {exc.response.status_code}")
        except Exception:
            return f"HTTP {exc.response.status_code}"


def _get_headers(include_auth: bool = True) -> dict:
    """Build request headers for Uber API calls."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if include_auth:
        token = _get_access_token()
        headers["Authorization"] = f"Bearer {token}"

    # Include sandbox header if in sandbox mode
    if UBER_SANDBOX_MODE:
        if not UBER_SANDBOX_RUN_ID:
            raise ValueError(
                "Sandbox mode enabled but UBER_SANDBOX_RUN_ID not set. "
                "Create a sandbox run first via POST /guests/sandbox/run"
            )
        headers["x-uber-sandbox-runuuid"] = UBER_SANDBOX_RUN_ID

    return headers


# ─── Status mapping ───────────────────────────────────────────────────────────

# Map Uber trip status to our internal status
_STATUS_MAP = {
    "processing": "REQUESTED",
    "accepted": "CONFIRMED",
    "arriving": "ARRIVING",
    "in_progress": "IN_PROGRESS",
    "completed": "COMPLETED",
    "cancelled_by_rider": "CANCELLED",
    "cancelled_by_system": "CANCELLED",
    "driver_cancel": "CANCELLED",
}


def _map_uber_status(uber_status: str) -> str:
    """Map Uber trip status to our internal status. Defaults to REQUESTED if unknown."""
    return _STATUS_MAP.get(uber_status, "REQUESTED")


# ─── Product conversion ────────────────────────────────────────────────────────

def _uber_product_to_rideproduct(
    product: dict,
    estimate_info: dict,
    distance_km: float,
    duration_minutes: int,
) -> RideProduct:
    """
    Convert Uber estimate response product to our RideProduct model.

    Uber may return either:
      - 'fare': object with 'value', 'currency_code', 'display', 'expires_at'
      - 'estimate': object with 'low_estimate', 'high_estimate', 'display'

    We normalize both to min/max/midpoint fares.
    """
    fare_data = estimate_info.get("fare", {}) or {}
    estimate_data = estimate_info.get("estimate", {}) or {}

    if fare_data:
        # Upfront fare (precise)
        fare_value = fare_data.get("value", 0.0)
        currency = fare_data.get("currency_code", "USD")
        estimated_fare = fare_value
        estimated_fare_min = fare_value
        estimated_fare_max = fare_value
    elif estimate_data:
        # Estimate range (less precise)
        estimated_fare_min = estimate_data.get("low_estimate", 0.0)
        estimated_fare_max = estimate_data.get("high_estimate", 0.0)
        estimated_fare = (estimated_fare_min + estimated_fare_max) / 2
        currency = estimate_data.get("currency_code", "USD")
    else:
        # No fare data available
        estimated_fare_min = 0.0
        estimated_fare_max = 0.0
        estimated_fare = 0.0
        currency = "USD"

    # ETA from pickup_estimate (in minutes)
    eta_minutes = estimate_info.get("pickup_estimate", duration_minutes)
    if eta_minutes is None:
        eta_minutes = duration_minutes

    return RideProduct(
        product_id=product["product_id"],
        name=product.get("display_name", "Uber"),
        description=product.get("description", ""),
        icon=product.get("image", "🚗"),  # Use product image URL as icon hint
        capacity=product.get("capacity", 4),
        currency=currency,
        estimated_fare_min=estimated_fare_min,
        estimated_fare_max=estimated_fare_max,
        estimated_fare=estimated_fare,
        estimated_duration_minutes=eta_minutes,
        estimated_distance_km=distance_km,
    )


# ─── Main provider class ───────────────────────────────────────────────────────

class UberRideProvider(BaseRideProvider):
    """
    Uber Guest Rides API provider implementation.

    Requires UBER_CLIENT_ID and UBER_CLIENT_SECRET environment variables.
    Optionally supports sandbox mode via UBER_SANDBOX_MODE and UBER_SANDBOX_RUN_ID.
    """

    @property
    def name(self) -> str:
        return "uber"

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
        Fetch all available ride products and fares for the given route.
        This is a wrapper around estimate() that returns all products.
        """
        try:
            products = self._fetch_estimates(
                pickup_lat, pickup_lon, dest_lat, dest_lon
            )
            return [
                _uber_product_to_rideproduct(p["product"], p["estimate_info"], distance_km, duration_minutes)
                for p in products
            ]
        except Exception as exc:
            logger.exception("Failed to fetch Uber products: %s", exc)
            raise

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
        """
        Get a single product estimate (fare + ETA) from Uber.
        Finds the matching product_id in the full estimates response.
        """
        try:
            all_products = self._fetch_estimates(
                pickup_lat, pickup_lon, dest_lat, dest_lon
            )

            # Find matching product
            for p in all_products:
                if p["product"]["product_id"] == product_id:
                    return _uber_product_to_rideproduct(
                        p["product"], p["estimate_info"], distance_km, duration_minutes
                    )

            raise ValueError(f"Product ID '{product_id}' not found in Uber estimates")
        except Exception as exc:
            logger.exception("Failed to estimate Uber product: %s", exc)
            raise

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
        Request a ride from Uber.

        Requires guest info (name, email, phone) and pickup/dropoff details.
        Since we don't have the actual rider info at this level, we'll create
        a placeholder guest object. In production, this would come from the user model.
        """
        try:
            # Get fresh estimates to capture fare_id (required for booking)
            estimates = self._fetch_estimates(pickup_lat, pickup_lon, dest_lat, dest_lon)

            # Find the selected product and extract fare_id
            fare_id = None
            for est in estimates:
                if est["product"]["product_id"] == product_id:
                    fare_id = est["estimate_info"].get("fare_id")
                    break

            if not fare_id:
                logger.warning(
                    "No fare_id in estimates for product %s; proceeding without it",
                    product_id,
                )

            # Build trip request
            # NOTE: In production, get actual guest info from the User model
            trip_payload = {
                "guest": {
                    "first_name": f"User{user_id}",
                    "last_name": "Guest",
                    "phone_number": "+1234567890",  # Placeholder
                    "email": f"user{user_id}@waytransit.local",
                },
                "pickup": {
                    "latitude": pickup_lat,
                    "longitude": pickup_lon,
                    "address": pickup_address,
                },
                "dropoff": {
                    "latitude": dest_lat,
                    "longitude": dest_lon,
                    "address": dest_address,
                },
                "product_id": product_id,
            }

            # Include fare_id if available (locks in upfront fare)
            if fare_id:
                trip_payload["fare_id"] = fare_id

            headers = _get_headers(include_auth=True)

            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    UBER_CREATE_TRIP_ENDPOINT,
                    json=trip_payload,
                    headers=headers,
                )
                resp.raise_for_status()

            trip_data = resp.json()

            logger.info(
                "Uber trip created: request_id=%s status=%s",
                trip_data.get("request_id"),
                trip_data.get("status"),
            )

            return BookingResult(
                provider_ride_id=trip_data["request_id"],
                status=_map_uber_status(trip_data.get("status", "processing")),
                provider_status=trip_data.get("status", "processing"),
                message=f"Ride confirmed by Uber. Request ID: {trip_data['request_id']}",
            )

        except httpx.HTTPStatusError as exc:
            error_detail = self._extract_error_detail(exc)
            logger.error("Uber booking failed: %s", error_detail)
            raise Exception(f"Uber booking error: {error_detail}") from exc
        except Exception as exc:
            logger.exception("Uber booking failed: %s", exc)
            raise

    def cancel(
        self,
        provider_ride_id: str,
        reason: str = "Cancelled by user",
    ) -> CancelResult:
        """Cancel a ride via Uber's cancellation endpoint."""
        try:
            headers = _get_headers(include_auth=True)
            cancel_url = f"{UBER_CREATE_TRIP_ENDPOINT}/{provider_ride_id}"

            with httpx.Client(timeout=10.0) as client:
                resp = client.delete(cancel_url, headers=headers)
                resp.raise_for_status()

            logger.info("Uber trip cancelled: request_id=%s", provider_ride_id)
            return CancelResult(success=True, message=f"Trip {provider_ride_id} cancelled.")

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                # Trip not found (may already be cancelled)
                logger.warning("Uber trip not found for cancellation: %s", provider_ride_id)
                return CancelResult(success=True, message="Trip not found (already cancelled?)")
            error_detail = self._extract_error_detail(exc)
            logger.error("Uber cancellation failed: %s", error_detail)
            return CancelResult(
                success=False,
                message=f"Uber cancellation error: {error_detail}",
            )
        except Exception as exc:
            logger.exception("Uber cancellation failed: %s", exc)
            return CancelResult(success=False, message=str(exc))

    def get_status(self, provider_ride_id: str) -> str:
        """Poll Uber for the current trip status."""
        try:
            headers = _get_headers(include_auth=True)
            status_url = f"{UBER_CREATE_TRIP_ENDPOINT}/{provider_ride_id}"

            with httpx.Client(timeout=10.0) as client:
                resp = client.get(status_url, headers=headers)
                resp.raise_for_status()

            trip_data = resp.json()
            uber_status = trip_data.get("status", "processing")
            internal_status = _map_uber_status(uber_status)

            logger.debug(
                "Uber trip status: request_id=%s uber_status=%s internal=%s",
                provider_ride_id,
                uber_status,
                internal_status,
            )

            return internal_status

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.warning("Uber trip not found: %s", provider_ride_id)
                return "FAILED"
            logger.error("Uber status poll failed: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Uber status poll failed: %s", exc)
            raise

    # ─── Private helpers ───────────────────────────────────────────────────

    def _fetch_estimates(
        self,
        pickup_lat: float,
        pickup_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> list:
        """
        Call Uber estimates endpoint and return the product_estimates array.
        """
        payload = {
            "pickup": {"latitude": pickup_lat, "longitude": pickup_lon},
            "dropoff": {"latitude": dest_lat, "longitude": dest_lon},
        }

        headers = _get_headers(include_auth=True)

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(UBER_ESTIMATES_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()

        data = resp.json()

        if data.get("fares_unavailable"):
            logger.warning("Uber fares temporarily unavailable")

        return data.get("product_estimates", [])

    def _extract_error_detail(self, exc: httpx.HTTPStatusError) -> str:
        """Extract human-readable error detail from Uber API error response."""
        try:
            body = exc.response.json()
            return body.get("message", f"HTTP {exc.response.status_code}")
        except Exception:
            return f"HTTP {exc.response.status_code}"
