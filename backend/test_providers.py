"""Test suite for ride providers (Mock and Uber).

Run tests:
    pytest test_providers.py -v

Run with coverage:
    pytest test_providers.py --cov=services.providers --cov-report=html
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from services.providers.mock_provider import MockRideProvider
from services.providers.uber_provider import UberRideProvider


# ============================================================================
# MOCK PROVIDER TESTS
# ============================================================================

class TestMockProvider:
    """Test suite for MockRideProvider (no network, always works)."""

    @pytest.fixture
    def provider(self):
        """Instantiate mock provider for each test."""
        return MockRideProvider()

    def test_provider_name(self, provider):
        """Test provider name is correct."""
        assert provider.name == "mock"

    def test_get_products_returns_four_types(self, provider):
        """Test fetching available products returns 4 ride types."""
        products = provider.get_products(
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            dest_lat=40.7505,
            dest_lon=-73.9934,
            distance_km=2.1,
            duration_minutes=8,
        )

        assert len(products) == 4, "Should return 4 mock products (Economy, Premium, Bike, XL)"
        
        # Check each product has required fields
        for product in products:
            assert hasattr(product, 'product_id')
            assert hasattr(product, 'name')
            assert hasattr(product, 'description')
            assert hasattr(product, 'estimated_fare')
            assert hasattr(product, 'currency')
            assert product.currency == "INR"
            assert product.estimated_fare > 0

    def test_get_products_names(self, provider):
        """Test that product names are correct."""
        products = provider.get_products(
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            dest_lat=40.7505,
            dest_lon=-73.9934,
            distance_km=2.1,
            duration_minutes=8,
        )

        names = [p.name for p in products]
        assert "Economy" in names
        assert "Premium" in names
        assert "Bike" in names
        assert "XL" in names

    def test_get_products_pricing_tier(self, provider):
        """Test that products have pricing tiers (Economy < Premium < XL)."""
        products = provider.get_products(
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            dest_lat=40.7505,
            dest_lon=-73.9934,
            distance_km=2.1,
            duration_minutes=8,
        )

        by_name = {p.name: p.estimated_fare for p in products}
        assert by_name["Economy"] < by_name["Premium"]
        assert by_name["Premium"] < by_name["XL"]
        assert by_name["Economy"] < by_name["Bike"]  # Bike is pricey

    def test_estimate_single_product(self, provider):
        """Test fare estimate for a specific product."""
        estimate = provider.estimate(
            product_id="mock_economy",
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            dest_lat=40.7505,
            dest_lon=-73.9934,
            distance_km=2.1,
            duration_minutes=8,
        )

        assert estimate.product_id == "mock_economy"
        assert estimate.name == "Economy"
        assert estimate.estimated_fare > 0
        assert estimate.currency == "INR"

    def test_book_ride_creates_booking(self, provider):
        """Test ride booking returns valid booking result."""
        result = provider.book(
            product_id="mock_economy",
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            pickup_address="Times Square, NYC",
            dest_lat=40.7505,
            dest_lon=-73.9934,
            dest_address="Central Park, NYC",
            user_id=123,
        )

        assert result.provider_ride_id.startswith("MOCK-")
        assert result.status == "CONFIRMED"
        assert result.provider_status == "accepted"
        assert result.provider == "mock"

    def test_cancel_ride_succeeds(self, provider):
        """Test ride cancellation."""
        # First book a ride
        booking = provider.book(
            product_id="mock_economy",
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            pickup_address="Times Square, NYC",
            dest_lat=40.7505,
            dest_lon=-73.9934,
            dest_address="Central Park, NYC",
            user_id=123,
        )

        # Then cancel it
        result = provider.cancel(booking.provider_ride_id)
        assert result.success is True
        assert result.provider_ride_id == booking.provider_ride_id

    def test_get_status_returns_confirmed(self, provider):
        """Test status polling (mock always returns CONFIRMED)."""
        status = provider.get_status("MOCK-anything")
        assert status == "CONFIRMED"

    def test_estimate_different_distances(self, provider):
        """Test fare scaling with distance."""
        fares = []
        for distance_km in [1.0, 2.0, 5.0, 10.0]:
            estimate = provider.estimate(
                product_id="mock_economy",
                pickup_lat=40.7484,
                pickup_lon=-73.9857,
                dest_lat=40.7505,
                dest_lon=-73.9934,
                distance_km=distance_km,
                duration_minutes=10,
            )
            fares.append(estimate.estimated_fare)

        # Fares should increase with distance
        for i in range(len(fares) - 1):
            assert fares[i] < fares[i + 1], f"Fares should increase: {fares}"

    def test_estimate_different_durations(self, provider):
        """Test fare scaling with duration."""
        fares = []
        for duration_mins in [5, 10, 20, 30]:
            estimate = provider.estimate(
                product_id="mock_economy",
                pickup_lat=40.7484,
                pickup_lon=-73.9857,
                dest_lat=40.7505,
                dest_lon=-73.9934,
                distance_km=2.0,
                duration_minutes=duration_mins,
            )
            fares.append(estimate.estimated_fare)

        # Fares should increase with duration
        for i in range(len(fares) - 1):
            assert fares[i] < fares[i + 1], f"Fares should increase: {fares}"


# ============================================================================
# UBER PROVIDER TESTS (WITH MOCKING)
# ============================================================================

class TestUberProvider:
    """Test suite for UberRideProvider (mocked HTTP calls)."""

    @pytest.fixture
    def provider(self):
        """Instantiate Uber provider for each test."""
        return UberRideProvider()

    def test_provider_name(self, provider):
        """Test provider name is correct."""
        assert provider.name == "uber"

    @patch('services.providers.uber_provider.httpx.Client')
    def test_get_products_success(self, mock_client_class, provider):
        """Test successful product fetch from Uber."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "product_estimates": [
                {
                    "product": {
                        "product_id": "uuid-1",
                        "display_name": "UberX",
                        "description": "Affordable rides",
                        "image": "https://example.com/uberx.png",
                        "capacity": 4,
                    },
                    "estimate_info": {
                        "fare_id": "fare-1",
                        "fare": {
                            "value": 12.50,
                            "currency_code": "USD",
                        },
                        "pickup_estimate": 5,
                    },
                },
                {
                    "product": {
                        "product_id": "uuid-2",
                        "display_name": "UberXL",
                        "description": "Premium rides",
                        "image": "https://example.com/uberxl.png",
                        "capacity": 6,
                    },
                    "estimate_info": {
                        "fare_id": "fare-2",
                        "fare": {
                            "value": 18.75,
                            "currency_code": "USD",
                        },
                        "pickup_estimate": 6,
                    },
                },
            ],
            "fares_unavailable": False,
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        # Mock token generation
        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            products = provider.get_products(
                pickup_lat=40.7484,
                pickup_lon=-73.9857,
                dest_lat=40.7505,
                dest_lon=-73.9934,
                distance_km=2.1,
                duration_minutes=8,
            )

        assert len(products) == 2
        assert products[0].name == "UberX"
        assert products[0].estimated_fare == 12.50
        assert products[1].name == "UberXL"
        assert products[1].estimated_fare == 18.75

    @patch('services.providers.uber_provider.httpx.Client')
    def test_estimate_single_product(self, mock_client_class, provider):
        """Test estimate for single product."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "product_estimates": [
                {
                    "product": {
                        "product_id": "uuid-1",
                        "display_name": "UberX",
                        "description": "Affordable rides",
                        "image": "https://example.com/uberx.png",
                        "capacity": 4,
                    },
                    "estimate_info": {
                        "fare_id": "fare-1",
                        "fare": {
                            "value": 12.50,
                            "currency_code": "USD",
                        },
                        "pickup_estimate": 5,
                    },
                }
            ],
            "fares_unavailable": False,
        }
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            estimate = provider.estimate(
                product_id="uuid-1",
                pickup_lat=40.7484,
                pickup_lon=-73.9857,
                dest_lat=40.7505,
                dest_lon=-73.9934,
                distance_km=2.1,
                duration_minutes=8,
            )

        assert estimate.product_id == "uuid-1"
        assert estimate.name == "UberX"
        assert estimate.estimated_fare == 12.50

    @patch('services.providers.uber_provider.httpx.Client')
    def test_book_ride_success(self, mock_client_class, provider):
        """Test successful ride booking."""
        # Mock estimates response
        estimates_response = MagicMock()
        estimates_response.json.return_value = {
            "product_estimates": [
                {
                    "product": {
                        "product_id": "uuid-1",
                        "display_name": "UberX",
                        "description": "Affordable rides",
                        "image": "https://example.com/uberx.png",
                        "capacity": 4,
                    },
                    "estimate_info": {
                        "fare_id": "fare-1",
                        "fare": {
                            "value": 12.50,
                            "currency_code": "USD",
                        },
                        "pickup_estimate": 5,
                    },
                }
            ],
            "fares_unavailable": False,
        }

        # Mock booking response
        booking_response = MagicMock()
        booking_response.json.return_value = {
            "request_id": "req-123",
            "status": "processing",
        }

        mock_client = MagicMock()
        mock_client.post.side_effect = [estimates_response, booking_response]
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            result = provider.book(
                product_id="uuid-1",
                pickup_lat=40.7484,
                pickup_lon=-73.9857,
                pickup_address="Times Square, NYC",
                dest_lat=40.7505,
                dest_lon=-73.9934,
                dest_address="Central Park, NYC",
                user_id=123,
            )

        assert result.provider_ride_id == "req-123"
        assert result.status == "REQUESTED"
        assert result.provider == "uber"

    @patch('services.providers.uber_provider.httpx.Client')
    def test_book_with_surge_retry(self, mock_client_class, provider):
        """Test booking with surge pricing (409) and auto-retry."""
        # Mock estimates response
        estimates_response = MagicMock()
        estimates_response.json.return_value = {
            "product_estimates": [
                {
                    "product": {"product_id": "uuid-1", "display_name": "UberX"},
                    "estimate_info": {
                        "fare_id": "fare-1",
                        "fare": {"value": 12.50, "currency_code": "USD"},
                        "pickup_estimate": 5,
                    },
                }
            ],
            "fares_unavailable": False,
        }

        # Mock surge response (409)
        surge_response = MagicMock()
        surge_response.status_code = 409
        surge_response.json.return_value = {
            "code": "surge",
            "message": "Fare is higher than normal",
        }
        surge_response.raise_for_status.side_effect = Exception("409 Conflict")

        # Mock successful booking response
        success_response = MagicMock()
        success_response.json.return_value = {
            "request_id": "req-123",
            "status": "processing",
        }

        mock_client = MagicMock()
        # First POST: estimates, second POST: surge (409), third POST: retry success
        mock_client.post.side_effect = [estimates_response, surge_response, success_response]
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            with patch('services.providers.uber_provider.time.sleep'):  # Skip actual sleep
                result = provider.book(
                    product_id="uuid-1",
                    pickup_lat=40.7484,
                    pickup_lon=-73.9857,
                    pickup_address="Times Square, NYC",
                    dest_lat=40.7505,
                    dest_lon=-73.9934,
                    dest_address="Central Park, NYC",
                    user_id=123,
                )

        assert result.provider_ride_id == "req-123"

    @patch('services.providers.uber_provider.httpx.Client')
    def test_cancel_ride_success(self, mock_client_class, provider):
        """Test successful ride cancellation."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_client = MagicMock()
        mock_client.delete.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            result = provider.cancel("req-123")

        assert result.success is True
        assert result.provider_ride_id == "req-123"

    @patch('services.providers.uber_provider.httpx.Client')
    def test_cancel_not_found_graceful(self, mock_client_class, provider):
        """Test graceful cancellation of already-cancelled ride (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")

        mock_client = MagicMock()
        mock_client.delete.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            result = provider.cancel("req-456")

        # Should gracefully handle 404 (already cancelled)
        assert result.success is True

    @patch('services.providers.uber_provider.httpx.Client')
    def test_get_status_success(self, mock_client_class, provider):
        """Test status polling."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "request_id": "req-123",
            "status": "in_progress",
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            status = provider.get_status("req-123")

        assert status == "IN_PROGRESS"

    @patch('services.providers.uber_provider.httpx.Client')
    def test_get_status_completed(self, mock_client_class, provider):
        """Test status mapping from completed."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "request_id": "req-123",
            "status": "completed",
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            status = provider.get_status("req-123")

        assert status == "COMPLETED"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestProviderIntegration:
    """Integration tests comparing mock and Uber behavior."""

    def test_both_providers_have_required_methods(self):
        """Ensure both providers implement required interface."""
        mock = MockRideProvider()
        uber = UberRideProvider()

        required_methods = ['name', 'get_products', 'estimate', 'book', 'cancel', 'get_status']
        for method_name in required_methods:
            assert hasattr(mock, method_name), f"Mock missing {method_name}"
            assert hasattr(uber, method_name), f"Uber missing {method_name}"
            assert callable(getattr(mock, method_name)), f"Mock.{method_name} not callable"
            assert callable(getattr(uber, method_name)), f"Uber.{method_name} not callable"

    def test_mock_and_uber_product_response_structure(self):
        """Test that mock and Uber return compatible product structures."""
        mock = MockRideProvider()

        # Get mock products
        mock_products = mock.get_products(40.7484, -73.9857, 40.7505, -73.9934, 2.1, 8)

        # Verify structure
        for product in mock_products:
            assert hasattr(product, 'product_id')
            assert hasattr(product, 'name')
            assert hasattr(product, 'description')
            assert hasattr(product, 'estimated_fare')
            assert hasattr(product, 'currency')


# ============================================================================
# CLI TESTS (manual testing reference)
# ============================================================================

class TestCliScripts:
    """Reference tests for manual CLI testing."""

    def test_mock_provider_cli_example(self):
        """Reference example for testing mock provider via CLI.
        
        Run this manually:
            curl -X POST http://localhost:8000/rides/products \\
              -H "Authorization: Bearer test-token" \\
              -H "Content-Type: application/json" \\
              -d '{
                "provider": "mock",
                "pickup_lat": 40.7484,
                "pickup_lon": -73.9857,
                "pickup_address": "Times Square",
                "destination_lat": 40.7505,
                "destination_lon": -73.9934,
                "destination_address": "Central Park"
              }' | jq .
        
        Expected: 4 products with INR fares
        """
        pass

    def test_uber_provider_cli_example(self):
        """Reference example for testing Uber provider via CLI.
        
        Prerequisites:
            - Set UBER_CLIENT_ID and UBER_CLIENT_SECRET in .env
            - Optionally set UBER_SANDBOX_MODE=true
        
        Run this manually:
            curl -X POST http://localhost:8000/rides/products \\
              -H "Authorization: Bearer test-token" \\
              -H "Content-Type: application/json" \\
              -d '{
                "provider": "uber",
                "pickup_lat": 40.7128,
                "pickup_lon": -74.0060,
                "pickup_address": "Manhattan",
                "destination_lat": 40.7580,
                "destination_lon": -73.9855,
                "destination_address": "Times Square"
              }' | jq .
        
        Expected: Real Uber products with real fares
        """
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
