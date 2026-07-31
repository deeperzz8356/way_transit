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
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                    """
                )
            )
