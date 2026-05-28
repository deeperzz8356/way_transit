# WAY Transit - Frontend

React + Vite frontend for WAY Transit booking system.

## Setup

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

Frontend runs on `http://localhost:5173`  
Make sure backend is running on `http://localhost:8000`

## Build

```bash
npm run build
```

## Features

- ✅ User signup/login with JWT
- ✅ Search routes by source/destination
- ✅ Book routes with validation
- ✅ View my bookings
- ✅ Logout

## API Integration

Backend should run on `http://localhost:8000` and expose CORS headers for `http://localhost:5173`.

Add to your FastAPI backend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
