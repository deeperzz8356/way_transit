# API Testing Guide

Quick reference for testing WAY Transit API.

## 🧪 Test Scenarios

### 1. User Signup
```bash
curl -X POST "http://localhost:8000/user/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "secure123"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "john@example.com"
}
```

---

### 2. User Login
```bash
curl -X POST "http://localhost:8000/user/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "secure123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save this token for next requests!**

---

### 3. Search Routes
Replace `{token}` with actual JWT from login:

```bash
curl -X GET "http://localhost:8000/search/routes?source=Mumbai&destination=Pune" \
  -H "Authorization: Bearer {token}"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "source": "Mumbai",
    "destination": "Pune",
    "transport": "bus",
    "departure_time": "06:00 AM",
    "arrival_time": "10:00 AM",
    "price": 300
  },
  {
    "id": 2,
    "source": "Mumbai",
    "destination": "Pune",
    "transport": "cab",
    "departure_time": "07:00 AM",
    "arrival_time": "10:30 AM",
    "price": 800
  }
]
```

---

### 4. Book a Route
```bash
curl -X POST "http://localhost:8000/booking/book" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "route_id": 1
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "route_id": 1,
  "status": "CONFIRMED",
  "created_at": "2024-01-15T10:30:00",
  "route": {
    "id": 1,
    "source": "Mumbai",
    "destination": "Pune",
    "transport": "bus",
    "departure_time": "06:00 AM",
    "arrival_time": "10:00 AM",
    "price": 300
  }
}
```

---

### 5. Get My Bookings
```bash
curl -X GET "http://localhost:8000/booking/my-bookings" \
  -H "Authorization: Bearer {token}"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "route_id": 1,
    "status": "CONFIRMED",
    "created_at": "2024-01-15T10:30:00",
    "route": { ... }
  }
]
```

---

## ✅ Test Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Database seeded with sample routes
- [ ] Can sign up new user
- [ ] Can login and get JWT token
- [ ] Can search routes
- [ ] Can book a route
- [ ] Can view my bookings
- [ ] Frontend connects without errors

---

## 🔗 Interactive API Docs

Visit: **http://localhost:8000/docs**

This is Swagger UI - try all endpoints directly in browser!

---

## 📋 Test Routes

### Test 1: New User Flow
1. Signup → john@example.com / pass123
2. Login → get token
3. Search → Mumbai → Pune
4. Book → route ID 1
5. My Bookings → see booking

### Test 2: Search Combinations
- Mumbai → Pune (2 results)
- Mumbai → Bangalore (1 result)
- Pune → Delhi (1 result)
- Delhi → Bangalore (1 result)
- Invalid → Invalid (0 results)

### Test 3: Error Cases
- Duplicate signup (same email)
- Wrong password
- Non-existent route ID
- Duplicate booking (same route twice)
- Missing auth token

---

## 🐛 Debug Mode

Check logs in backend:
```bash
# See detailed request logs
uvicorn backend.main:app --reload --log-level debug
```

Browser console:
- Open DevTools (F12)
- Check Console tab for JS errors
- Check Network tab for API responses

---

## 🚀 Automated Testing (Optional)

```python
# backend/test_api.py
import requests

BASE_URL = "http://localhost:8000"

# Test signup
resp = requests.post(f"{BASE_URL}/user/signup", json={
    "email": "test@example.com",
    "password": "test123"
})
print(resp.json())  # Should return user ID

# Test login
resp = requests.post(f"{BASE_URL}/user/login", json={
    "email": "test@example.com",
    "password": "test123"
})
token = resp.json()["access_token"]
print(f"Token: {token}")

# Test search
resp = requests.get(
    f"{BASE_URL}/search/routes?source=Mumbai&destination=Pune",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"Routes found: {len(resp.json())}")

# Test book
resp = requests.post(
    f"{BASE_URL}/booking/book",
    headers={"Authorization": f"Bearer {token}"},
    json={"route_id": 1}
)
print(f"Booking: {resp.json()['status']}")
```

Run: `python backend/test_api.py`

---

**All tests passing = MVP ready! ✅**
