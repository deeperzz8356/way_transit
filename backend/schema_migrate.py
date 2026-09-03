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


def ensure_gtfs_schema():
    """Add GTFS-specific columns and performance indexes (safe to call multiple times)."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        # --- Add gtfs_route_short_name to routes ---
        if "routes" in tables:
            rcols = {c["name"] for c in inspector.get_columns("routes")}
            _add_col(conn, "routes", rcols, "gtfs_route_short_name", "gtfs_route_short_name VARCHAR")

        # --- Create performance indexes (IF NOT EXISTS) ---
        # Determine dialect: PostgreSQL supports IF NOT EXISTS on CREATE INDEX
        is_pg = engine.dialect.name == "postgresql"

        def _create_index(conn, idx_name: str, table: str, columns: str):
            if is_pg:
                conn.execute(text(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})"
                ))
            else:
                # SQLite: wrap in try/except since IF NOT EXISTS isn't supported for indexes in all versions
                try:
                    conn.execute(text(
                        f"CREATE INDEX {idx_name} ON {table} ({columns})"
                    ))
                except Exception:
                    pass  # Index already exists

        if "routes" in tables:
            _create_index(conn, "ix_routes_route_code_op", "routes", "route_code, operator_id")
            _create_index(conn, "ix_routes_mode_op", "routes", "mode, operator_id")
            _create_index(conn, "ix_routes_gtfs_short_name", "routes", "gtfs_route_short_name")

        if "stops" in tables:
            _create_index(conn, "ix_stops_stop_code_op", "stops", "stop_code, operator_id")
            _create_index(conn, "ix_stops_mode_op", "stops", "mode, operator_id")

        if "trips" in tables:
            _create_index(conn, "ix_trips_trip_code", "trips", "trip_code")
            _create_index(conn, "ix_trips_route_svc", "trips", "route_id, service_id")

        if "stop_times" in tables:
            _create_index(conn, "ix_stop_times_trip_seq", "stop_times", "trip_id, stop_sequence")
            _create_index(conn, "ix_stop_times_stop_id", "stop_times", "stop_id")

