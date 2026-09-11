# 🚀 Uber Provider - Quick Start (5 Minutes)

## TL;DR

Get Uber rides working in WAY Transit in 5 quick steps.

---

## Step 1: Get Credentials (2 min)

1. Go to https://developer.uber.com/dashboard
2. Click "Create New App" → name it "WAY Transit"
3. Go to Settings → Scopes → Add **`guests.trips`**
4. Go to Credentials → Copy **Client ID** and **Client Secret**

---

## Step 2: Configure .env (1 min)

Edit `backend/.env`:

```bash
UBER_CLIENT_ID=abc123def456ghi789
UBER_CLIENT_SECRET=xyz789uvw456rst123opq
```

---

## Step 3: Seed Database (1 min)

```bash
cd backend
python seed_db.py
```

This registers the Uber provider in your database.

---

## Step 4: Activate Uber Provider (30 sec)

```sql
UPDATE ride_providers SET is_active = true WHERE name = 'uber';
```

---

## Step 5: Test (1 min)

```bash
# Start backend
python -m uvicorn main:app --reload

# In another terminal, test:
curl -X POST http://localhost:8000/rides/products \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "uber",
    "pickup_lat": 40.7128,
    "pickup_lon": -74.0060,
    "destination_lat": 40.7580,
    "destination_lon": -73.9855
  }' | jq .
```

**Expected:** Real Uber products with actual fares! 🎉

---

## Common Issues

| Problem | Solution |
|---------|----------|
| 401 Unauthorized | Double-check CLIENT_ID/SECRET in .env |
| Invalid Scope Error | Add `guests.trips` scope in Uber dashboard |
| No products returned | Use NYC/SF coordinates (Uber service areas) |
| Database not seeded | Run `python seed_db.py` |

---

## Next: Full Documentation

For detailed setup, testing, troubleshooting:

👉 **See `UBER_SETUP_GUIDE.md`**

For testing procedures and examples:

👉 **See `RIDE_PROVIDER_TESTING.md`**

For complete architecture and implementation:

👉 **See `PHASE_4_IMPLEMENTATION_SUMMARY.md`**

---

## Want to Test Without Real Charges?

Enable sandbox mode in `backend/.env`:

```bash
UBER_SANDBOX_MODE=true
UBER_SANDBOX_RUN_ID=your-run-id-from-uber-dashboard
```

All test requests go to Uber sandbox (no real charges).

---

## Need Help?

Check troubleshooting in `UBER_SETUP_GUIDE.md` → "Troubleshooting" section.

Or run the test suite:

```bash
pytest backend/test_providers.py -v
```

---

**Status:** ✅ Phase 4 Complete  
**Ready for:** Development, Testing, Staging, Production
