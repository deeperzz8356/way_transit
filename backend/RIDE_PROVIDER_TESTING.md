# Ride Provider Testing Guide

This document covers testing both mock and real (Uber) ride providers in WAY Transit.

## Quick Start

### Test Mock Provider (No Setup Required)

```bash
# 1. Start the backend
cd backend
python -m uvicorn main:app --reload

# 2. In another terminal, test the mock provider
curl -X POST http://localhost:8000/rides/products \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "mock",
    "pickup_lat": 40.7484,
    "pickup_lon": -73.9857,
    "pickup_address": "Times Square, NYC",
    "destination_lat": 40.7505,
    "destination_lon": -73.9934,
    "destination_address": "Central Park, NYC"
  }'
```

Expected response: 4 mock ride types (Economy, Premium, Bike, XL) with fares.

---

## Unit Tests

### Setup

Create `backend/test_providers.py`:

```python
"""Test suite for ride providers."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.providers.mock_provider import MockRideProvider
from services.providers.uber_provider import UberRideProvider


class TestMockProvider:
    """Mock provider tests (always pass, no network)."""

    @pytest.fixture
    def provider(self):
        return MockRideProvider()

    def test_get_products(self, provider):
        """Test fetching available products."""
        products = provider.get_products(
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            dest_lat=40.7505,
            dest_lon=-73.9934,
            distance_km=2.1,
            duration_minutes=8,
        )

        assert len(products) == 4, "Should return 4 mock products"
        assert products[0].name == "Economy"
        assert products[0].estimated_fare > 0
        assert products[0].currency == "INR"

    def test_estimate(self, provider):
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

    def test_book(self, provider):
        """Test ride booking."""
        result = provider.book(
            product_id="mock_economy",
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            pickup_address="Times Square",
            dest_lat=40.7505,
            dest_lon=-73.9934,
            dest_address="Central Park",
            user_id=123,
        )

        assert result.provider_ride_id.startswith("MOCK-")
        assert result.status == "CONFIRMED"
        assert result.provider_status == "accepted"

    def test_cancel(self, provider):
        """Test ride cancellation."""
        # First book a ride
        booking = provider.book(
            product_id="mock_economy",
            pickup_lat=40.7484,
            pickup_lon=-73.9857,
            pickup_address="Times Square",
            dest_lat=40.7505,
            dest_lon=-73.9934,
            dest_address="Central Park",
            user_id=123,
        )

        # Then cancel it
        result = provider.cancel(booking.provider_ride_id)
        assert result.success is True

    def test_get_status(self, provider):
        """Test status polling."""
        # Mock always returns CONFIRMED
        status = provider.get_status("MOCK-anything")
        assert status == "CONFIRMED"


class TestUberProvider:
    """Uber provider tests (requires mocking HTTP calls)."""

    @pytest.fixture
    def provider(self):
        return UberRideProvider()

    @patch('services.providers.uber_provider.httpx.Client')
    def test_get_products_success(self, mock_client_class, provider):
        """Test successful product fetch."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "product_estimates": [
                {
                    "product": {
                        "product_id": "uuid-1",
                        "display_name": "UberX",
                        "description": "Affordable rides",
                        "image": "https://...",
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

        assert len(products) == 1
        assert products[0].name == "UberX"
        assert products[0].estimated_fare == 12.50

    @patch('services.providers.uber_provider.httpx.Client')
    def test_book_with_surge_retry(self, mock_client_class, provider):
        """Test booking with surge pricing (409) and auto-retry."""
        # First call returns 409 (surge), second call succeeds
        surge_response = MagicMock()
        surge_response.status_code = 409
        surge_response.json.return_value = {
            "code": "surge",
            "message": "Fare is higher than normal",
            "metadata": {
                "fare_id": "new-fare-id",
                "multiplier": 1.4,
            },
        }
        surge_response.raise_for_status.side_effect = Exception("409")

        success_response = MagicMock()
        success_response.json.return_value = {
            "request_id": "req-123",
            "status": "processing",
        }

        mock_client = MagicMock()
        # First POST to estimates, then POST to book (fails with 409), then retry
        mock_client.post.side_effect = [
            success_response,  # Estimates call
            surge_response,    # First book attempt
            success_response,  # Retry after surge
        ]
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            with patch('services.providers.uber_provider.time.sleep'):  # Skip actual sleep
                result = provider.book(
                    product_id="uuid-1",
                    pickup_lat=40.7484,
                    pickup_lon=-73.9857,
                    pickup_address="Times Square",
                    dest_lat=40.7505,
                    dest_lon=-73.9934,
                    dest_address="Central Park",
                    user_id=123,
                )

        assert result.provider_ride_id == "req-123"

    @patch('services.providers.uber_provider.httpx.Client')
    def test_cancel_success(self, mock_client_class, provider):
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

    @patch('services.providers.uber_provider.httpx.Client')
    def test_cancel_not_found(self, mock_client_class, provider):
        """Test cancellation of already-cancelled ride (404)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404")

        mock_client = MagicMock()
        mock_client.delete.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        with patch('services.providers.uber_provider._get_access_token', return_value='fake-token'):
            result = provider.cancel("req-456")

        # Should gracefully handle 404 as already cancelled
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Run Tests

```bash
cd backend
pip install pytest pytest-mock
pytest test_providers.py -v
```

Expected output:
```
test_providers.py::TestMockProvider::test_get_products PASSED
test_providers.py::TestMockProvider::test_estimate PASSED
test_providers.py::TestMockProvider::test_book PASSED
test_providers.py::TestMockProvider::test_cancel PASSED
test_providers.py::TestMockProvider::test_get_status PASSED
test_providers.py::TestUberProvider::test_get_products_success PASSED
test_providers.py::TestUberProvider::test_book_with_surge_retry PASSED
test_providers.py::TestUberProvider::test_cancel_success PASSED
test_providers.py::TestUberProvider::test_cancel_not_found PASSED
test_providers.py::TestUberProvider::test_get_status_success PASSED

========== 10 passed in 0.23s ==========
```

---

## Integration Tests

### Manual API Testing

#### 1. Test Mock Provider Endpoint

```bash
curl -X POST http://localhost:8000/rides/products \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "mock",
    "pickup_lat": 40.7484,
    "pickup_lon": -73.9857,
    "pickup_address": "Times Square, NYC",
    "destination_lat": 40.7505,
    "destination_lon": -73.9934,
    "destination_address": "Central Park, NYC"
  }' | jq .
```

Expected: 4 products with fares in INR.

#### 2. Book a Mock Ride

```bash
curl -X POST http://localhost:8000/rides/book \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "mock",
    "product_id": "mock_economy",
    "pickup_lat": 40.7484,
    "pickup_lon": -73.9857,
    "pickup_address": "Times Square, NYC",
    "destination_lat": 40.7505,
    "destination_lon": -73.9934,
    "destination_address": "Central Park, NYC",
    "payment_method": "cash"
  }' | jq .
```

Expected: Ride object with `status: "CONFIRMED"` and `provider_ride_id: "MOCK-xxx"`.

#### 3. Get Ride History

```bash
curl -X GET "http://localhost:8000/rides/history?limit=5" \
  -H "Authorization: Bearer test-token" | jq .
```

Expected: Array of user's past rides.

#### 4. Get Single Ride

Save the `ride_id` from booking response, then:

```bash
curl -X GET http://localhost:8000/rides/123 \
  -H "Authorization: Bearer test-token" | jq .
```

Expected: Full ride detail with `status_history` array.

#### 5. Manually Advance Mock Ride Status (Debug)

```bash
# REQUESTED → CONFIRMED → ARRIVING → IN_PROGRESS → COMPLETED
curl -X POST "http://localhost:8000/rides/123/status?new_status=ARRIVING" \
  -H "Authorization: Bearer test-token" | jq .
```

Expected: Ride status updated to "ARRIVING".

#### 6. Cancel a Ride

```bash
curl -X POST http://localhost:8000/rides/123/cancel \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Changed my mind"}' | jq .
```

Expected: Ride status updated to "CANCELLED".

---

## Testing with Uber Provider

### Prerequisites

1. **Uber Sandbox Setup** (no real charges):
   - Go to https://developer.uber.com/dashboard
   - Create app with `guests.trips` scope
   - Enable Sandbox mode
   - Create a sandbox run, copy the run ID

2. **Configure .env**:
   ```bash
   UBER_CLIENT_ID=your_client_id
   UBER_CLIENT_SECRET=your_client_secret
   UBER_SANDBOX_MODE=true
   UBER_SANDBOX_RUN_ID=your_run_id
   ```

3. **Restart backend**:
   ```bash
   # Kill old process
   pkill -f "uvicorn main:app"
   
   # Restart
   python -m uvicorn main:app --reload
   ```

### Test Uber Provider

#### 1. Test Products Endpoint

```bash
curl -X POST http://localhost:8000/rides/products \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "uber",
    "pickup_lat": 40.7484,
    "pickup_lon": -73.9857,
    "pickup_address": "Times Square, NYC",
    "destination_lat": 40.7505,
    "destination_lon": -73.9934,
    "destination_address": "Central Park, NYC"
  }' | jq .
```

Expected: Real Uber products (UberX, UberXL, Premium, etc.) with real fares.

#### 2. Book an Uber Ride

```bash
# First, get a product_id from the products response above
PRODUCT_ID="<product_id_from_response>"

curl -X POST http://localhost:8000/rides/book \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d "{
    \"provider\": \"uber\",
    \"product_id\": \"$PRODUCT_ID\",
    \"pickup_lat\": 40.7484,
    \"pickup_lon\": -73.9857,
    \"pickup_address\": \"Times Square, NYC\",
    \"destination_lat\": 40.7505,
    \"destination_lon\": -73.9934,
    \"destination_address\": \"Central Park, NYC\",
    \"payment_method\": \"cash\"
  }" | jq .
```

Expected: Ride object with `status: "CONFIRMED"` and Uber's `request_id`.

#### 3. Poll Ride Status

```bash
RIDE_ID=<ride_id_from_booking>
curl -X GET "http://localhost:8000/rides/$RIDE_ID" \
  -H "Authorization: Bearer test-token" | jq .
```

Expected: Current status from Uber (e.g., "CONFIRMED", "ARRIVING", "IN_PROGRESS").

#### 4. Update Sandbox Driver State (Simulate Driver Behavior)

In Uber sandbox, manually advance the driver:

```bash
REQUEST_ID=<request_id_from_booking>
DRIVER_LAT=40.7490
DRIVER_LON=-73.9850

curl -X POST https://api.uber.com/v1/guests/sandbox/driver-state \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -H "x-uber-sandbox-runuuid: $UBER_SANDBOX_RUN_ID" \
  -d "{
    \"request_id\": \"$REQUEST_ID\",
    \"driver_latitude\": $DRIVER_LAT,
    \"driver_longitude\": $DRIVER_LON,
    \"driver_status\": \"arriving\"
  }"
```

Then poll `/rides/{ride_id}` again — status should be "ARRIVING".

#### 5. Cancel Uber Ride

```bash
RIDE_ID=<ride_id>
curl -X POST "http://localhost:8000/rides/$RIDE_ID/cancel" \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Changed my mind"}' | jq .
```

Expected: Status updated to "CANCELLED".

---

## Troubleshooting

### Mock Provider Issues

#### Problem: Empty products list
**Cause:** Coordinates outside service area (mock only supports anywhere)
**Solution:** Mock supports any coordinates; check backend logs.

#### Problem: "Provider not found"
**Cause:** Provider not seeded in database
**Solution:**
```bash
cd backend
python seed_db.py
```

### Uber Provider Issues

#### Problem: "Unauthorized" (401)
**Cause:** Invalid credentials or missing scope
**Solution:**
1. Verify `UBER_CLIENT_ID` and `UBER_CLIENT_SECRET` in `.env`
2. Check app dashboard — add `guests.trips` scope if missing
3. Restart backend

#### Problem: "Sandbox mode enabled but UBER_SANDBOX_RUN_ID not set"
**Cause:** Sandbox enabled without run ID
**Solution:**
1. Go to Uber dashboard → Sandbox
2. Click "Create Sandbox Run"
3. Copy run ID to `UBER_SANDBOX_RUN_ID` in `.env`
4. Restart backend

#### Problem: "Service area not supported"
**Cause:** Test coordinates outside Uber's service area
**Solution:**
- Use San Francisco (37.7749, -122.4194)
- Or New York (40.7128, -74.0060)
- Check https://www.uber.com/en/cities/

#### Problem: 409 Conflict (Surge Pricing)
**Expected Behavior:** Automatically retried with new fare_id
**To Force:** Book during high-demand times (not easily testable in sandbox)

#### Problem: Rate Limited (429)
**Expected Behavior:** Automatic exponential backoff retry
**Rate Limit:** 100 token generations per hour
**Solution:** Token caching prevents this in normal usage

---

## Performance Testing

### Benchmark Mock Provider

```python
import time
from services.providers.mock_provider import MockRideProvider

provider = MockRideProvider()
start = time.time()

for i in range(100):
    products = provider.get_products(40.7484, -73.9857, 40.7505, -73.9934, 2.1, 8)
    
elapsed = time.time() - start
print(f"100 calls in {elapsed:.2f}s = {elapsed/100*1000:.1f}ms per call")
# Expected: ~0.1-0.2ms per call (in-memory, no network)
```

### Benchmark Uber Provider

```python
import time
from services.providers.uber_provider import UberRideProvider

provider = UberRideProvider()
start = time.time()

try:
    for i in range(10):
        products = provider.get_products(40.7484, -73.9857, 40.7505, -73.9934, 2.1, 8)
        
    elapsed = time.time() - start
    print(f"10 calls in {elapsed:.2f}s = {elapsed/10*1000:.0f}ms per call")
    # Expected: 800-1200ms per call (network + auth)
except Exception as e:
    print(f"Error: {e}")
```

---

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test-providers.yml`:

```yaml
name: Test Ride Providers

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt pytest
      - run: cd backend && pytest test_providers.py -v
```

---

## Summary

| Provider | Setup | Speed | Costs | Notes |
|----------|-------|-------|-------|-------|
| **Mock** | None | ~0.2ms | $0 | Perfect for dev/testing |
| **Uber** | Credentials + Sandbox | ~1000ms | $0 (sandbox) | Real API, accurate fares |

**Start with mock for development, then test with Uber sandbox before production.**
