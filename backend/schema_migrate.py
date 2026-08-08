"""Lightweight SQLite column/table ensure for MVP (create_all does not ALTER)."""
from sqlalchemy import inspect, text
from database import engine


def _add_col(conn, table: str, cols: set, name: str, ddl: str):
    if name not in cols:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def ensure_ticket_schema():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        if "bookings" in tables:
            cols = {c["name"] for c in inspector.get_columns("bookings")}
            _add_col(conn, "bookings", cols, "source", "source VARCHAR")
            _add_col(conn, "bookings", cols, "destination", "destination VARCHAR")
            _add_col(conn, "bookings", cols, "image_url", "image_url VARCHAR")
            _add_col(conn, "bookings", cols, "ticket_code", "ticket_code VARCHAR")
            _add_col(conn, "bookings", cols, "ticket_number", "ticket_number VARCHAR")
            _add_col(conn, "bookings", cols, "qr_payload", "qr_payload VARCHAR")
            _add_col(conn, "bookings", cols, "mode", "mode VARCHAR")
            _add_col(conn, "bookings", cols, "operator_id", "operator_id INTEGER")
            _add_col(conn, "bookings", cols, "operator_name", "operator_name VARCHAR")
            _add_col(conn, "bookings", cols, "class_name", "class_name VARCHAR")
            _add_col(conn, "bookings", cols, "fare", "fare FLOAT")
            _add_col(conn, "bookings", cols, "source_type", "source_type VARCHAR")
            _add_col(conn, "bookings", cols, "journey_started_at", "journey_started_at TIMESTAMP")
            _add_col(conn, "bookings", cols, "journey_estimated_end_at", "journey_estimated_end_at TIMESTAMP")

        if "ticket_ingest_jobs" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE ticket_ingest_jobs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        image_url VARCHAR NOT NULL,
                        status VARCHAR,
                        source VARCHAR,
                        destination VARCHAR,
                        operator VARCHAR,
                        travel_date VARCHAR,
                        ticket_number VARCHAR,
                        qr_payload VARCHAR,
                        mode VARCHAR,
                        raw_text VARCHAR,
                        error_message VARCHAR,
                        booking_id INTEGER,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                    """
                )
            )
        else:
            job_cols = {c["name"] for c in inspector.get_columns("ticket_ingest_jobs")}
            _add_col(conn, "ticket_ingest_jobs", job_cols, "ticket_number", "ticket_number VARCHAR")
            _add_col(conn, "ticket_ingest_jobs", job_cols, "qr_payload", "qr_payload VARCHAR")
            _add_col(conn, "ticket_ingest_jobs", job_cols, "mode", "mode VARCHAR")

        if "journeys" in tables:
            jcols = {c["name"] for c in inspector.get_columns("journeys")}
            _add_col(conn, "journeys", jcols, "booking_id", "booking_id INTEGER")
            _add_col(conn, "journeys", jcols, "status", "status VARCHAR")
            _add_col(conn, "journeys", jcols, "started_at", "started_at TIMESTAMP")
            _add_col(conn, "journeys", jcols, "estimated_end_at", "estimated_end_at TIMESTAMP")

        if "user_passes" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE user_passes (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER,
                        pass_id INTEGER,
                        valid_until TIMESTAMP,
                        status VARCHAR,
                        created_at TIMESTAMP
                    )
                    """
                )
            )
