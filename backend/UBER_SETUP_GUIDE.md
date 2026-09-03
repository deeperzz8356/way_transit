# Uber Guest Rides API Integration Guide

This guide covers setting up the Uber provider for WAY Transit's ride-booking system.

## Overview

The Uber provider integrates with Uber's **Guest Rides API**, allowing WAY Transit to:
- List available ride types and real-time fares
- Book rides without requiring users to have Uber accounts
- Track ride status in real-time
- Cancel rides programmatically

## Prerequisites

1. **Uber Developer Account** (free)
   - Sign up at https://developer.uber.com/
   - Create an app in the dashboard

2. **Environment & Tools**
   - Python 3.9+
   - Virtual environment with dependencies installed
   - `.env` file in the project root

3. **Network**
   - Outbound HTTPS access to `api.uber.com` and `auth.uber.com`

---

## Step 1: Create an Uber Developer App

1. Go to https://developer.uber.com/dashboard
2. Sign in or create an account
3. Click **"Create New App"**
4. Fill in:
   - **App Name**: "WAY Transit" (or your app name)
   - **App Description**: "Ride booking platform for transit travelers"
   - **Intended Use**: Select "Ride-hailing" or "Transportation"
5. Accept terms and click **Create App**

### Grant Scopes

After creating the app:

1. In the dashboard, go to your app's **Settings** page
2. Scroll to **"Scopes"** or **"Permissions"**
3. Add or enable these scopes:
   - `guests.trips` — Required for Guest Rides API

The app is now restricted to the sandbox environment by default.

---

## Step 2: Get Credentials

1. In your app dashboard, find the **"Credentials"** or **"OAuth"** section
2. Copy:
   - **Client ID** (treat like username)
   - **Client Secret** (treat like password — keep secret!)

### Example:
```
Client ID:     abc123def456ghi789
Client Secret: xyz789uvw456rst123opq
```

---

## Step 3: Configure Environment Variables

Add the following to your `.env` file in the project root:

```bash
# Uber Guest Rides API Credentials
UBER_CLIENT_ID=abc123def456ghi789
UBER_CLIENT_SECRET=xyz789uvw456rst123opq

# Sandbox Mode (for testing, set to false for production)
# UBER_SANDBOX_MODE=false
# UBER_SANDBOX_RUN_ID=   # Leave blank for production

# Optional: OpenRouteService for accurate distance/ETA
ORS_API_KEY=your_ors_api_key_here  # Get free key at https://openrouteservice.org/
```

**Important:**
- Never commit `.env` to git — add it to `.gitignore`
- Use a secrets manager (e.g., AWS Secrets Manager, Vault) in production
- Rotate `UBER_CLIENT_SECRET` periodically in the Uber dashboard

---

## Step 4: Enable Uber Provider in Database

Run the seed script to register Uber as a provider:

```bash
cd backend
python seed_db.py
```

This creates two providers:
- **mock** — Simulated provider (always available)
- **uber** — Real Uber (initially inactive)

To activate Uber, set `is_active = true` in the database:

```sql
UPDATE ride_providers SET is_active = true WHERE name = 'uber';
```

---

## Step 5: Test the Integration

### Test with Mock Provider First

```bash
curl -X POST http://localhost:8000/rides/products \
  -H "Authorization: Bearer <YOUR_USER_TOKEN>" \
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

### Test with Uber Provider

```bash
curl -X POST http://localhost:8000/rides/products \
  -H "Authorization: Bearer <YOUR_USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "uber",
    "pickup_lat": 40.7484,
    "pickup_lon": -73.9857,
    "pickup_address": "Times Square, NYC",
    "destination_lat": 40.7505,
    "destination_lon": -73.9934,
    "destination_address": "Central Park, NYC"
  }'
```

Expected response:
```json
{
  "provider": "uber",
  "distance_km": 2.1,
  "duration_minutes": 8,
  "routing_source": "ors",
  "products": [
    {
      "product_id": "a1111c8c-c720-46c3-8534-2fcdd730040d",
      "name": "UberX",
      "description": "Affordable rides, all to yourself",
      "capacity": 4,
      "estimated_fare": 12.50,
      "estimated_fare_min": 11.00,
      "estimated_fare_max": 14.00,
      "currency": "USD",
      "estimated_distance_km": 2.1,
      "estimated_duration_minutes": 8
    },
    ...
  ]
}
```

---

## Step 6: Sandbox Mode (Optional - for Testing)

To test rides without using real credits, Uber provides a sandbox environment.

### Enable Sandbox Mode:

1. In your Uber app dashboard, go to **"Sandbox"** tab
2. Click **"Create Sandbox Run"**
3. Note the **Run ID** (e.g., `abc123-def456-ghi789`)

### Configure WAY Transit:

Update `.env`:
```bash
UBER_SANDBOX_MODE=true
UBER_SANDBOX_RUN_ID=abc123-def456-ghi789
```

### Use Sandbox API:

All requests automatically include the sandbox header `x-uber-sandbox-runuuid: abc123-def456-ghi789`.

You can manually update driver state:
```bash
curl -X POST https://api.uber.com/v1/guests/sandbox/driver-state \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "e249c871-7711-4c26-b06c-679cbad6a7c2",
    "driver_latitude": 40.754,
    "driver_longitude": -73.984,
    "driver_status": "in_progress"
  }'
```

---

## API Endpoints

The WAY Transit backend exposes these ride-booking endpoints:

### 1. Get Available Products & Estimates
```
POST /rides/products
```
Returns all available Uber ride types with fares for the given route.

### 2. Book a Ride
```
POST /rides/book
```
Request a ride with a specific product.

### 3. Get Ride History
```
GET /rides/history?status=COMPLETED&limit=10
```
Retrieve user's ride history (filterable by status).

### 4. Get Single Ride
```
GET /rides/{ride_id}
```
Fetch full ride details including status history.

### 5. Cancel a Ride
```
POST /rides/{ride_id}/cancel
```
Cancel a ride (only works if status is REQUESTED, CONFIRMED, or ARRIVING).

### 6. Get Ride Status (Debug)
```
POST /rides/{ride_id}/status?new_status=ARRIVING
```
Manually update ride status (debug only; remove `include_in_schema=False` to hide).

---

## Troubleshooting

### Issue: "Unauthorized" Error
**Cause:** Invalid or missing credentials
**Solution:**
1. Verify `UBER_CLIENT_ID` and `UBER_CLIENT_SECRET` in `.env`
2. Check credentials in Uber dashboard (Settings → Credentials)
3. Ensure the app has `guests.trips` scope enabled

### Issue: "Invalid Scope" Error
**Cause:** App doesn't have `guests.trips` scope
**Solution:**
1. Go to your app dashboard
2. Click **Settings** → **Scopes**
3. Add `guests.trips` if missing
4. Restart the backend

### Issue: Sandbox Run Expired
**Cause:** Sandbox runs expire after 24 hours
**Solution:**
1. Go to Uber dashboard → **Sandbox** tab
2. Create a new sandbox run
3. Update `UBER_SANDBOX_RUN_ID` in `.env`

### Issue: Rate Limited (Too Many Token Requests)
**Cause:** Exceeded 100 token generations per hour
**Solution:**
- Tokens are cached for 30 days; this should only happen in dev/testing
- Restart the backend to reset the cache
- Consider using JWT tokens instead of client credentials in production

### Issue: "Service Area Not Supported"
**Cause:** Pickup/dropoff location is outside Uber's service area
**Solution:**
- Test with coordinates in a supported city (e.g., San Francisco, New York)
- Check https://www.uber.com/en/cities/ for supported locations

---

## Production Deployment Checklist

- [ ] Set `UBER_SANDBOX_MODE=false` in production `.env`
- [ ] Use AWS Secrets Manager, HashiCorp Vault, or similar for credentials
- [ ] Enable HTTPS for all API calls (auto via `httpx`)
- [ ] Set up rate limiting on `/rides/*` endpoints
- [ ] Add request signing/validation if needed
- [ ] Monitor token refresh failures and alert on issues
- [ ] Set up CloudWatch/Prometheus logs for API errors
- [ ] Add retry logic for transient failures
- [ ] Test with real Uber rides in a staging environment
- [ ] Document API costs and set up usage alerts
- [ ] Ensure guest info (phone, email) is validated and stored securely

---

## Architecture Notes

### Token Caching
- Tokens are cached in-memory and refreshed 5 minutes before expiry
- For distributed systems (microservices), use Redis instead:
  ```python
  import redis
  cache = redis.Redis(host='localhost', port=6379)
  _cached_token = cache.get('uber_token')
  cache.setex('uber_token', 2592000, token_value)
  ```

### Error Handling
- 409 Conflict (surge pricing): Automatically retried with new fare_id
- 404 Not Found: Trip may have expired or been cancelled
- 5xx errors: Exponential backoff retry (not yet implemented)

### Future Enhancements
- [ ] Real-time driver location tracking via webhooks
- [ ] Ola, Rapido, and other provider integrations
- [ ] Payment integration (Stripe, Razorpay, UPI)
- [ ] Driver ratings & feedback system
- [ ] Loyalty rewards & promo codes
- [ ] Multi-stop routing (waypoints support)

---

## Support & References

- **Uber API Docs:** https://developer.uber.com/docs/guest-rides/all-spec
- **OAuth Guide:** https://developer.uber.com/docs/guest-rides/guides/authentication
- **Status Codes:** https://developer.uber.com/docs/guest-rides/references/errors

---

**Last Updated:** August 2026  
**Provider Version:** Uber Guest Rides API v1  
**WAY Transit Version:** Phase 4
