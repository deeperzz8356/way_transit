---
name: way-transit-rules
description: "Project specific guidelines for WAY Transit MVP"
trigger: always_on
glob: "*"
---

# WAY Transit MVP Project Rules

## Tech Stack Overrides
- **Backend**: While global rules mention `asyncpg` and `no ORMs`, THIS project explicitly uses **FastAPI with SQLAlchemy** (ORM) and SQLite by default (PostgreSQL in production). Stick to SQLAlchemy `models.py` and `crud.py` patterns used here.
- **Frontend**: While global rules mention `React Native + Expo`, THIS project is a web app using **React + Vite** with Javascript/JSX. Use the existing `index.css` and functional React components in `frontend/src`.

## Architecture & Code Organization
- **Backend Structure**:
  - `backend/main.py`: App entry point
  - `backend/models.py`: SQLAlchemy ORM models
  - `backend/schemas.py`: Pydantic models (validation)
  - `backend/crud.py`: Database queries
  - `backend/routes/`: Router endpoints separated by domain (`user.py`, `search.py`, `booking.py`)
- **Frontend Structure**:
  - `frontend/src/pages/`: Page components
  - `frontend/src/App.jsx`: Main routing
  - Use `fetch` or `axios` for API calls to backend (running on `http://localhost:8000` locally). Store JWT token in `localStorage`.

## Development Commands
- Backend: `uvicorn backend.main:app --reload` (run from root)
- Frontend: `npm run dev` in `frontend/` folder
- Database Reset: Delete `backend/way_transit.db` and run `python backend/seed_db.py`

## Features Scope (MVP)
- Do not implement real payment processing (mock only).
- Do not add map visualization (use static text).
- Keep features minimal as defined in MVP goals. Do not build outside the scope unless explicitly requested.
