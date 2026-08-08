"""Lightweight SQLite column/table ensure for MVP (create_all does not ALTER)."""
from sqlalchemy import inspect, text
from database import engine


def ensure_ticket_schema():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        if "bookings" in tables:
            cols = {c["name"] for c in inspector.get_columns("bookings")}
            if "source" not in cols:
                conn.execute(text("ALTER TABLE bookings ADD COLUMN source VARCHAR"))
            if "destination" not in cols:
                conn.execute(text("ALTER TABLE bookings ADD COLUMN destination VARCHAR"))
            if "image_url" not in cols:
                conn.execute(text("ALTER TABLE bookings ADD COLUMN image_url VARCHAR"))
            if "ticket_code" not in cols:
                conn.execute(text("ALTER TABLE bookings ADD COLUMN ticket_code VARCHAR"))

        if "ticket_ingest_jobs" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE ticket_ingest_jobs (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        image_url VARCHAR NOT NULL,
                        status VARCHAR,
                        source VARCHAR,
                        destination VARCHAR,
                        operator VARCHAR,
                        travel_date VARCHAR,
                        raw_text VARCHAR,
                        error_message VARCHAR,
                        booking_id INTEGER,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                    """
                )
            )

        if "otp_codes" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE otp_codes (
                        id INTEGER PRIMARY KEY,
                        phone VARCHAR UNIQUE NOT NULL,
                        hashed_code VARCHAR NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP,
                        last_sent_at TIMESTAMP,
                        first_requested_at TIMESTAMP,
                        request_count INTEGER DEFAULT 1,
                        failed_attempts INTEGER DEFAULT 0
                    )
                    """
                )
            )

        if "users" in tables:
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "google_id" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR"))
            if "profile_image" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN profile_image VARCHAR"))
            if "auth_provider" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR"))
            if "updated_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP"))
