# WAY Transit MVP 🚌
uvicorn main:app --reload
A complete transit/booking system MVP built with FastAPI (backend) + React (frontend).

**Status:** ✅ MVP Complete - Ready to test end-to-end

## 🎯 What's Included

✅ **Backend (FastAPI)**
- User authentication (signup/login with JWT)
- Route search API
- Booking system
- Database with proper relationships
- CORS enabled for frontend

✅ **Frontend (React + Vite)**
- Login/signup pages
- Route search interface
- Booking confirmation
- My bookings view
- Clean, responsive UI

✅ **Database**
- Users (with email unique constraint)
- Routes (with times, transport, price)
- Bookings (with user↔booking↔route relationships)

✅ **Sample Data**
- 5 pre-loaded routes (Mumbai↔Pune, Delhi, Bangalore)

## 🚀 Quick Start (2 minutes)

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- Git

### Setup & Run

**Option 1: Manual (Recommended for first time)**

```bash
# Terminal 1 - Backend
pip install -r requirements.txt
python backend/seed_db.py
uvicorn backend.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

**Option 2: Auto Setup**
```bash
# Windows
./start.bat

# macOS/Linux
./start.sh
```

## 📍 Access

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 🧪 Test the Full Flow

1. **Go to http://localhost:5173**
2. **Sign up** with any email (e.g., `user@example.com` / `password123`)
3. **Search routes** - Try: `Mumbai` → `Pune`
4. **Book a route** - Click book on any result
5. **View bookings** - Click "My Bookings" in navbar

## 📁 Project Structure

```
way_transit/
├── backend/
│   ├── main.py              ← FastAPI app entry point
│   ├── models.py            ← SQLAlchemy ORM models
│   ├── schemas.py           ← Pydantic request/response models
│   ├── crud.py              ← Database operations
│   ├── auth.py              ← JWT + password hashing
│   ├── database.py          ← DB connection (SQLite by default)
│   ├── dependencies.py      ← JWT validation dependency
│   ├── seed_db.py           ← Sample data loader
│   └── routes/
│       ├── user.py          ← /user/* endpoints
│       ├── search.py        ← /search/* endpoints
│       └── booking.py       ← /booking/* endpoints
│
├── frontend/                ← React + Vite project
│   ├── src/
│   │   ├── App.jsx          ← Main router component
│   │   ├── pages/           ← Page components
│   │   │   ├── LoginPage.jsx
│   │   │   ├── SearchPage.jsx
│   │   │   ├── BookingPage.jsx
│   │   │   └── MyBookingsPage.jsx
│   │   └── index.css        ← Global styles
│   └── package.json
│
├── requirements.txt         ← Python dependencies
├── .env.example            ← Environment variables template
├── SETUP_GUIDE.md          ← Detailed setup guide
└── README.md               ← This file
```

## 🔌 API Endpoints

### Authentication
```http
POST /user/signup
POST /user/login
GET  /user/me
```

### Routes
```http
GET /search/routes?source=Mumbai&destination=Pune
```

### Bookings (🔒 protected)
```http
POST /booking/book
GET  /booking/my-bookings
```

## 🔐 How Auth Works

1. User signs up → password hashed with bcrypt
2. User logs in → receives JWT token (30 min expiry)
3. Frontend stores token in localStorage
4. All API requests include: `Authorization: Bearer <token>`
5. Backend validates token on protected routes

## 📊 Sample Data

Run `python backend/seed_db.py` to load:

| From | To | Transport | Price |
|------|----------|-----------|-------|
| Mumbai | Pune | Bus | ₹300 |
| Mumbai | Pune | Cab | ₹800 |
| Mumbai | Bangalore | Flight | ₹3000 |
| Pune | Delhi | Train | ₹1200 |
| Delhi | Bangalore | Flight | ₹2500 |

## 🛠️ Development

### Backend
```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest  # for testing

# Run with auto-reload
uvicorn backend.main:app --reload

# Run tests (optional)
pytest backend/
```

### Frontend
```bash
cd frontend

# Dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🚨 Troubleshooting

**Backend won't start?**
```bash
# Make sure you're in project root
# Kill any process on port 8000
lsof -ti:8000 | xargs kill  # macOS/Linux
netstat -ano | findstr :8000  # Windows (then taskkill /PID xxx)
```

**Frontend can't connect?**
- Ensure backend is running: `curl http://localhost:8000`
- Check CORS is enabled in `main.py`
- Clear browser cache/localStorage if token is stale

**Database errors?**
```bash
# Reinitialize database
rm backend/way_transit.db  # or equivalent
python backend/seed_db.py
```

## 🗄️ Database Options

### Default (SQLite)
Perfect for MVP - no setup needed!
```
DATABASE_URL=sqlite:///./way_transit.db
```

### PostgreSQL
For production:
```bash
# Install PostgreSQL
# Create database
createdb way_transit

# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/way_transit

# Run migrations
python backend/seed_db.py
```

## 📈 Next Steps (Post-MVP)

1. **Real Payments** - Razorpay/UPI integration
2. **Live Tracking** - Maps + GPS tracking
3. **Notifications** - Email/SMS alerts
4. **Admin Panel** - Manage routes/bookings
5. **Deployment** - Docker + AWS/Heroku
6. **Testing** - Unit tests + integration tests

## 🐛 Known Limitations (MVP)

- No real payment processing (mock only)
- No map visualization (static text)
- No user profile editing
- No booking cancellation
- Single region (India prices/routes)
- No driver/vehicle management

## 📝 License

This is a demo MVP project. Use freely for learning.

## 💬 Support

Check `SETUP_GUIDE.md` for detailed troubleshooting.

---

**Built with ❤️ for learning purposes**

Start with: `uvicorn backend.main:app --reload` + `npm run dev`

Good luck! 🚀
