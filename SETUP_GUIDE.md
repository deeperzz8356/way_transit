# WAY Transit MVP - Complete Setup Guide

## 🚀 Quick Start (5 minutes)

### 1. Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Seed database with sample routes
python backend/seed_db.py

# Run backend (from project root)
uvicorn backend.main:app --reload --port 8000
```

Backend runs on: `http://localhost:8000`

### 2. Frontend Setup (in new terminal)

```bash
# Install dependencies
cd frontend
npm install

# Run dev server
npm run dev
```

Frontend runs on: `http://localhost:5173`

---

## 🧪 Testing the Full Flow

### 1. **Sign Up**
- Navigate to http://localhost:5173
- Click "Sign Up"
- Enter: `user@example.com` / `password123`
- Click "Sign Up"

### 2. **Log In**
- Click "Login"
- Same credentials
- Get JWT token

### 3. **Search Routes**
- Try: `Mumbai` → `Pune`
- Should see 2 results (bus & cab)
- Or: `Mumbai` → `Bangalore` (flight)
- Or: `Pune` → `Delhi` (train)

### 4. **Book a Route**
- Click "Book" on any route
- Click "Confirm Booking"
- Success! ✓

### 5. **View My Bookings**
- Click "My Bookings"
- See all your confirmed bookings

---

## 📁 Project Structure

```
way_transit/
├── backend/
│   ├── main.py              (FastAPI app + CORS)
│   ├── models.py            (DB models: User, Route, Booking)
│   ├── schemas.py           (Pydantic schemas for API)
│   ├── crud.py              (Database operations)
│   ├── auth.py              (JWT + password hashing)
│   ├── database.py          (SQLAlchemy config)
│   ├── dependencies.py      (JWT validation)
│   ├── seed_db.py           (Sample data)
│   └── routes/
│       ├── user.py          (signup, login)
│       ├── search.py        (search routes)
│       └── booking.py       (book, my-bookings)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          (Main router)
│   │   ├── index.css        (Styles)
│   │   ├── main.jsx         (React entry)
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       ├── SearchPage.jsx
│   │       ├── BookingPage.jsx
│   │       └── MyBookingsPage.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
└── requirements.txt
```

---

## 🔌 API Endpoints

### Auth
- `POST /user/signup` - Register
- `POST /user/login` - Login & get token

### Search
- `GET /search/routes?source=X&destination=Y` - Search routes

### Booking
- `POST /booking/book` - Book a route (requires auth)
- `GET /booking/my-bookings` - Get user's bookings (requires auth)

---

## 🔐 Authentication

All protected endpoints require:
```
Authorization: Bearer <your_jwt_token>
```

Token expires after 30 minutes. Login again if needed.

---

## 📊 Sample Data

After running `seed_db.py`, you have:

| From | To | Transport | Price |
|------|-------|-----------|-------|
| Mumbai | Pune | Bus | ₹300 |
| Mumbai | Pune | Cab | ₹800 |
| Mumbai | Bangalore | Flight | ₹3000 |
| Pune | Delhi | Train | ₹1200 |
| Delhi | Bangalore | Flight | ₹2500 |

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Make sure you're in project root
# Check Python version: python --version (need 3.8+)
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend can't connect to backend
- Check backend is running on `http://localhost:8000`
- Check CORS is enabled in `main.py`
- Check no firewall blocking port 8000/5173

### Database errors
```bash
# Reset database
# Delete any existing database file/connection
python backend/seed_db.py
```

### JWT token errors
- Make sure token is in `Authorization: Bearer <token>` format
- Token expires after 30 min - login again if needed

---

## 📈 Next Steps (After MVP)

- Add real payment integration (UPI, Razorpay)
- Add live tracking with maps
- Add admin dashboard
- Add notifications (email, SMS)
- Deploy to production (Heroku, AWS, etc.)

---

## ✅ MVP Checklist

- ✅ Database with users, routes, bookings
- ✅ User signup/login with JWT
- ✅ Search routes by source/destination
- ✅ Book routes (with validation)
- ✅ View my bookings
- ✅ Frontend fully connected to backend
- ✅ CORS enabled
- ✅ Sample data seeded
- ✅ Full flow tested end-to-end

🎉 **MVP Complete!**
