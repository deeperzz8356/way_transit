# Quick Start - Environment Variables

## TL;DR Setup (60 seconds)

### Step 1: Copy Example Files
```bash
cd f:\way_transit
cp .env.example .env
cp backend\.env.example backend\.env
cp frontend\.env.example frontend\.env
```

### Step 2: Update Root .env
Edit `f:\way_transit\.env` with your actual values:
```dotenv
DATABASE_URL=postgresql://postgres:Deep@localhost:5432/way_transit
GROQ_API_KEY=your_actual_groq_key
RAZORPAY_KEY=rzp_test_xxxxx
RAZORPAY_SECRET=your_secret
```

### Step 3: Update Frontend .env
Edit `f:\way_transit\frontend\.env`:
```dotenv
VITE_GOOGLE_MAPS_API_KEY=your_actual_maps_key
```

### Step 4: Run Services
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Key Files

| Purpose | File Path | Edit? |
|---------|-----------|-------|
| Backend config | `f:/way_transit/.env` | ✏️ **YES** |
| Frontend config | `f:/way_transit/frontend/.env` | ✏️ **YES** |
| Template | `f:/way_transit/.env.example` | No |
| Documentation | `ENV_SETUP.md` | No |

## Critical Variables

**Must Fill In:**
- `DATABASE_URL` - Database connection
- `GROQ_API_KEY` - AI/OCR service
- `RAZORPAY_KEY` & `RAZORPAY_SECRET` - Payments
- `VITE_GOOGLE_MAPS_API_KEY` - Maps frontend

**Auto-Generated (Keep Safe):**
- `SECRET_KEY` - JWT token signing

## Variable Locations

```
🟢 Backend variables  → Root .env (f:/way_transit/.env)
🔵 Frontend variables → frontend/.env (f:/way_transit/frontend/.env)
   (Must start with VITE_)
```

## Verify Setup

**Backend sees all root variables:**
```bash
python backend/main.py  # If no errors, .env loaded correctly
```

**Frontend sees VITE_ variables:**
```bash
npm run dev  # If maps show up, VITE_GOOGLE_MAPS_API_KEY loaded
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Module not found" | Copy `.env.example` to `.env` |
| Groq/OCR fails | Check `GROQ_API_KEY` in root `.env` |
| Maps not showing | Check `VITE_GOOGLE_MAPS_API_KEY` in `frontend/.env` |
| Payment fails | Check `RAZORPAY_KEY` & `RAZORPAY_SECRET` in root `.env` |

## Path Reference

```
f:\way_transit\
├── .env                    ← Root (Backend reads this first)
├── backend\
│   └── .env                ← Backend overrides (optional)
└── frontend\
    └── .env                ← Frontend only (VITE_* vars)
```

That's it! You're ready to go. 🚀
