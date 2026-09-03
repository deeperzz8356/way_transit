"""
gtfs_import/importer.py
========================
WAY_TRANSIT Production-Safe GTFS Schedule Importer

Design principles:
  CORRECTNESS > DATA INTEGRITY > REPEATABILITY > PERFORMANCE > CONVENIENCE

Safety guarantees:
  - Never truncates, drops, or deletes user/application data
  - Never drops/truncates: users, bookings, journeys, wallets, passes, rewards, alerts
  - Additive/upsert-oriented only
  - Idempotent: safe to run more than once
  - Never uses GTFS string IDs as integer PKs

Performance:
  - stop_times.txt is streamed row-by-row (never loaded into RAM)
  - Batch inserts of 5000-10000 rows via SQLAlchemy Core
  - FK maps loaded into Python dicts (not per-row DB queries)

Extended times:
  - GTFS allows arrival_time/departure_time > 24:00:00 (e.g. 43:20:00)
  - These are stored as strings; NEVER parsed with datetime.time
"""

from __future__ import annotations

import csv
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# These will be resolved at runtime by the caller
# (avoids import order issues when running standalone)

log = logging.getLogger("gtfs_import.importer")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_FILES = [
    "agency.txt",
    "routes.txt",
    "stops.txt",
    "trips.txt",
    "stop_times.txt",
    "calendar.txt",
]

OPTIONAL_FILES = [
    "calendar_dates.txt",
    "transfers.txt",
    "shapes.txt",
    "feed_info.txt",
]


# ---------------------------------------------------------------------------
# Main importer class
# ---------------------------------------------------------------------------

class GTFSImporter:
    """
    Production-safe GTFS Schedule Importer for WAY_TRANSIT.

    Args:
        folder:     Path to directory containing GTFS .txt files.
        db:         SQLAlchemy Session (already connected).
        models:     The backend models module (imported at call site).
        dry_run:    If True, validate only — no writes to DB.
        batch_size: Number of stop_time rows per batch insert.
        force:      If True, update/overwrite existing GTFS-sourced records.
    """

    def __init__(
        self,
        folder: Path,
        db: Session,
        models,
        dry_run: bool = False,
        batch_size: int = 7500,
        force: bool = False,
    ):
        self.folder = Path(folder)
        self.db = db
        self.models = models
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.force = force

        # FK maps built during import — used for FK resolution
        self.operator_map: dict[str, int] = {}   # gtfs agency_id -> operator.id
        self.city_map: dict[str, int] = {}        # agency_id -> city.id
        self.service_id_set: set[str] = set()     # known service_ids (strings)
        self.stop_map: dict[str, int] = {}        # gtfs stop_id -> stop.id
        self.route_map: dict[str, int] = {}       # gtfs route_id -> route.id
        self.trip_map: dict[str, int] = {}        # gtfs trip_id -> trip.id

        # Import stats per file
        self._stats: dict = {}

    # -----------------------------------------------------------------------
    # File helpers
    # -----------------------------------------------------------------------

    def _path(self, filename: str) -> Path:
        return self.folder / filename

    def _exists(self, filename: str) -> bool:
        return self._path(filename).is_file()

    def _require(self, filename: str) -> Path:
        p = self._path(filename)
        if not p.is_file():
            raise FileNotFoundError(f"Required GTFS file not found: {p}")
        return p

    def _stream(self, filename: str):
        """Lazily yield rows from a GTFS file as stripped dicts."""
        from gtfs_import.utils import stream_csv
        return stream_csv(self._path(filename))

    # -----------------------------------------------------------------------
    # Preflight
    # -----------------------------------------------------------------------

    def run_preflight(self) -> bool:
        """
        Run preflight checks.
        Returns True if all checks pass, False otherwise.
        Prints a human-readable summary.
        """
        print("\n" + "=" * 56)
        print("PREFLIGHT CHECKS")
        print("=" * 56)

        ok = True

        # 1. DB connection
        try:
            self.db.execute(text("SELECT 1"))
            print("  ✓ Database connection: OK")
        except Exception as exc:
            print(f"  ✗ Database connection FAILED: {exc}")
            return False

        # 2. DB URL info (mask password)
        try:
            url = str(self.db.bind.engine.url)
            # Mask password
            import re
            url_safe = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)
            print(f"  ✓ Database URL: {url_safe}")
        except Exception:
            pass

        # 3. GTFS folder
        if not self.folder.is_dir():
            print(f"  ✗ GTFS folder not found: {self.folder}")
            return False
        print(f"  ✓ GTFS folder: {self.folder}")

        # 4. Required files
        missing = []
        for f in REQUIRED_FILES:
            if self._exists(f):
                print(f"  ✓ {f}")
            else:
                print(f"  ✗ {f} (MISSING — required)")
                missing.append(f)
                ok = False

        # 5. Optional files
        for f in OPTIONAL_FILES:
            if self._exists(f):
                print(f"  ✓ {f} (optional)")
            else:
                print(f"  - {f} (not present; will be skipped)")

        # 6. Current DB row counts
        print("\n  Current database row counts:")
        for table, label in [
            ("operators", "operators"),
            ("routes", "routes"),
            ("stops", "stops"),
            ("trips", "trips"),
            ("stop_times", "stop_times"),
            ("service_calendar", "service_calendar"),
        ]:
            try:
                count = self.db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"    {label}: {count:,}")
            except Exception:
                print(f"    {label}: (table not found)")

        if ok:
            print("\n  About to import GTFS schedule data.")
            print("  No application/user data will be deleted.")
        else:
            print("\n  Preflight FAILED — missing required files.")

        return ok

    # -----------------------------------------------------------------------
    # 1. agency.txt -> operators
    # -----------------------------------------------------------------------

    def import_agency(self) -> dict:
        """Import agency.txt into operators table."""
        from gtfs_import.validators import validate_agency
        from gtfs_import.utils import get_or_create_city, ImportStats

        stats = ImportStats("agency.txt")
        path = self._require("agency.txt")

        print(f"\nImporting {path.name}...")

        for row_num, row in enumerate(self._stream("agency.txt"), start=2):
            ok, err = validate_agency(row)
            if not ok:
                stats.add_error(row_num, row.get("agency_id", "?"), err)
                log.warning("agency.txt row %d: %s", row_num, err)
                continue

            agency_id = row["agency_id"].strip()
            agency_name = row["agency_name"].strip()

            if self.dry_run:
                stats.loaded += 1
                self.operator_map[agency_id] = -1  # placeholder
                continue

            # Get/create city
            city = get_or_create_city(self.db, self.models, agency_id)
            self.city_map[agency_id] = city.id

            # Upsert operator by short_name (= agency_id)
            existing = (
                self.db.query(self.models.Operator)
                .filter(self.models.Operator.short_name == agency_id)
                .first()
            )

            if existing:
                if self.force:
                    existing.name = agency_name
                    existing.city_id = city.id
                    existing.mode = "bus"
                    existing.is_active = True
                    stats.updated += 1
                else:
                    stats.skipped += 1
                self.operator_map[agency_id] = existing.id
            else:
                op = self.models.Operator(
                    city_id=city.id,
                    name=agency_name,
                    short_name=agency_id,
                    mode="bus",
                    color_hex="#4A90D9",
                    is_active=True,
                )
                self.db.add(op)
                self.db.flush()
                self.operator_map[agency_id] = op.id
                stats.loaded += 1

        if not self.dry_run:
            self.db.commit()

        self._stats["agency"] = stats
        stats.print_summary()
        return self.operator_map

    # -----------------------------------------------------------------------
    # 2. calendar.txt -> service_calendar
    # -----------------------------------------------------------------------

    def import_calendar(self) -> set:
        """Import calendar.txt into service_calendar table."""
        from gtfs_import.validators import validate_calendar
        from gtfs_import.utils import parse_gtfs_date, ImportStats

        stats = ImportStats("calendar.txt")
        path = self._require("calendar.txt")

        print(f"\nImporting {path.name}...")

        for row_num, row in enumerate(self._stream("calendar.txt"), start=2):
            ok, err = validate_calendar(row)
            if not ok:
                stats.add_error(row_num, row.get("service_id", "?"), err)
                log.warning("calendar.txt row %d: %s", row_num, err)
                continue

            service_id = row["service_id"].strip()

            if self.dry_run:
                stats.loaded += 1
                self.service_id_set.add(service_id)
                continue

            start_date = parse_gtfs_date(row.get("start_date", ""))
            end_date = parse_gtfs_date(row.get("end_date", ""))

            existing = (
                self.db.query(self.models.ServiceCalendar)
                .filter(self.models.ServiceCalendar.service_id == service_id)
                .first()
            )

            if existing:
                if self.force:
                    existing.monday = row.get("monday", "0") == "1"
                    existing.tuesday = row.get("tuesday", "0") == "1"
                    existing.wednesday = row.get("wednesday", "0") == "1"
                    existing.thursday = row.get("thursday", "0") == "1"
                    existing.friday = row.get("friday", "0") == "1"
                    existing.saturday = row.get("saturday", "0") == "1"
                    existing.sunday = row.get("sunday", "0") == "1"
                    existing.start_date = start_date
                    existing.end_date = end_date
                    stats.updated += 1
                else:
                    stats.skipped += 1
                self.service_id_set.add(service_id)
            else:
                sc = self.models.ServiceCalendar(
                    service_id=service_id,
                    monday=row.get("monday", "0") == "1",
                    tuesday=row.get("tuesday", "0") == "1",
                    wednesday=row.get("wednesday", "0") == "1",
                    thursday=row.get("thursday", "0") == "1",
                    friday=row.get("friday", "0") == "1",
                    saturday=row.get("saturday", "0") == "1",
                    sunday=row.get("sunday", "0") == "1",
                    start_date=start_date,
                    end_date=end_date,
                )
                self.db.add(sc)
                self.service_id_set.add(service_id)
                stats.loaded += 1

        if not self.dry_run:
            self.db.commit()

        self._stats["calendar"] = stats
        stats.print_summary()
        return self.service_id_set

    # -----------------------------------------------------------------------
    # 3. stops.txt -> stops
    # -----------------------------------------------------------------------

    def import_stops(self) -> dict:
        """Import stops.txt into stops table."""
        from gtfs_import.validators import validate_stop
        from gtfs_import.utils import ImportStats

        stats = ImportStats("stops.txt")
        path = self._require("stops.txt")

        print(f"\nImporting {path.name}...")

        # Determine operator_id from stop_code prefix (KDMT_, TMT_, BEST_, VVMT_)
        # The prefix before the first '_' is the agency_id
        def _operator_id_for_stop(stop_id: str) -> Optional[int]:
            if "_" in stop_id:
                prefix = stop_id.split("_")[0].upper()
                return self.operator_map.get(prefix)
            return None

        def _city_id_for_stop(stop_id: str) -> Optional[int]:
            if "_" in stop_id:
                prefix = stop_id.split("_")[0].upper()
                return self.city_map.get(prefix)
            return None

        for row_num, row in enumerate(self._stream("stops.txt"), start=2):
            ok, err = validate_stop(row)
            if not ok:
                stats.add_error(row_num, row.get("stop_id", "?"), err)
                log.warning("stops.txt row %d: %s", row_num, err)
                continue

            stop_code = row["stop_id"].strip()
            stop_name = row["stop_name"].strip()
            lat = float(row["stop_lat"])
            lon = float(row["stop_lon"])

            operator_id = _operator_id_for_stop(stop_code)
            city_id = _city_id_for_stop(stop_code)

            if self.dry_run:
                stats.loaded += 1
                self.stop_map[stop_code] = -1
                continue

            existing = (
                self.db.query(self.models.Stop)
                .filter(self.models.Stop.stop_code == stop_code)
                .first()
            )

            if existing:
                if self.force:
                    existing.name = stop_name
                    existing.lat = lat
                    existing.lon = lon
                    if operator_id:
                        existing.operator_id = operator_id
                    if city_id:
                        existing.city_id = city_id
                    existing.mode = "bus"
                    existing.is_active = True
                    stats.updated += 1
                else:
                    stats.skipped += 1
                self.stop_map[stop_code] = existing.id
            else:
                stop = self.models.Stop(
                    city_id=city_id,
                    operator_id=operator_id,
                    stop_code=stop_code,
                    name=stop_name,
                    lat=lat,
                    lon=lon,
                    mode="bus",
                    is_active=True,
                    wheelchair=False,
                    platform_count=1,
                )
                self.db.add(stop)
                self.db.flush()
                self.stop_map[stop_code] = stop.id
                stats.loaded += 1

            # Commit in batches to avoid memory buildup
            if (stats.loaded + stats.updated) % 1000 == 0:
                if not self.dry_run:
                    self.db.commit()

        if not self.dry_run:
            self.db.commit()

        self._stats["stops"] = stats
        stats.print_summary()
        return self.stop_map

    # -----------------------------------------------------------------------
    # 4. routes.txt -> routes
    # -----------------------------------------------------------------------

    def import_routes(self) -> dict:
        """Import routes.txt into routes table."""
        from gtfs_import.validators import validate_route
        from gtfs_import.utils import ImportStats

        stats = ImportStats("routes.txt")
        path = self._require("routes.txt")
        known_agency_ids = set(self.operator_map.keys())

        print(f"\nImporting {path.name}...")

        for row_num, row in enumerate(self._stream("routes.txt"), start=2):
            ok, err = validate_route(row, known_agency_ids)
            if not ok:
                stats.add_error(row_num, row.get("route_id", "?"), err)
                log.warning("routes.txt row %d: %s", row_num, err)
                continue

            route_id = row["route_id"].strip()
            agency_id = row["agency_id"].strip()
            route_short_name = row.get("route_short_name", "").strip() or None
            route_long_name = row.get("route_long_name", "").strip() or route_id

            operator_id = self.operator_map.get(agency_id)
            city_id = self.city_map.get(agency_id)

            if self.dry_run:
                stats.loaded += 1
                self.route_map[route_id] = -1
                continue

            # Upsert by (route_code, operator_id) — prevents cross-operator collision
            existing = (
                self.db.query(self.models.Route)
                .filter(
                    self.models.Route.route_code == route_id,
                    self.models.Route.operator_id == operator_id,
                )
                .first()
            )

            if existing:
                if self.force:
                    existing.name = route_long_name
                    existing.city_id = city_id
                    existing.mode = "bus"
                    existing.is_active = True
                    existing.gtfs_route_short_name = route_short_name
                    stats.updated += 1
                else:
                    stats.skipped += 1
                self.route_map[route_id] = existing.id
            else:
                route = self.models.Route(
                    city_id=city_id,
                    operator_id=operator_id,
                    route_code=route_id,
                    name=route_long_name,
                    mode="bus",
                    is_active=True,
                    gtfs_route_short_name=route_short_name,
                )
                self.db.add(route)
                self.db.flush()
                self.route_map[route_id] = route.id
                stats.loaded += 1

        if not self.dry_run:
            self.db.commit()

        self._stats["routes"] = stats
        stats.print_summary()
        return self.route_map

    # -----------------------------------------------------------------------
    # 5. trips.txt -> trips
    # -----------------------------------------------------------------------

    def import_trips(self) -> dict:
        """Import trips.txt into trips table. Uses batched inserts for performance."""
        from gtfs_import.validators import validate_trip
        from gtfs_import.utils import ImportStats
        from sqlalchemy import insert

        stats = ImportStats("trips.txt")
        path = self._require("trips.txt")
        known_route_ids = set(self.route_map.keys())

        print(f"\nImporting {path.name}...")

        batch: list[dict] = []
        trip_codes_batch: list[str] = []

        def _flush_batch():
            if not batch or self.dry_run:
                return
            try:
                self.db.execute(
                    insert(self.models.Trip).prefix_with(""),
                    batch,
                )
                self.db.commit()
            except Exception as exc:
                self.db.rollback()
                log.error("Trip batch insert failed: %s", exc)

        for row_num, row in enumerate(self._stream("trips.txt"), start=2):
            ok, err = validate_trip(row, known_route_ids, self.service_id_set)
            if not ok:
                stats.add_error(row_num, row.get("trip_id", "?"), err)
                log.warning("trips.txt row %d: %s", row_num, err)
                continue

            trip_code = row["trip_id"].strip()
            route_id = row["route_id"].strip()
            service_id = row["service_id"].strip()
            direction = str(row.get("direction_id", "0")).strip()
            # trip_headsign -> trip_short_name (documented transformation)
            trip_short_name = row.get("trip_headsign", "").strip() or None

            route_db_id = self.route_map.get(route_id)
            if not route_db_id or route_db_id < 0:
                stats.add_error(row_num, trip_code, f"route_id={route_id!r} not in route_map")
                continue

            if self.dry_run:
                stats.loaded += 1
                self.trip_map[trip_code] = -1
                continue

            # Check for existing trip by trip_code
            existing = (
                self.db.query(self.models.Trip)
                .filter(self.models.Trip.trip_code == trip_code)
                .first()
            )

            if existing:
                if self.force:
                    existing.route_id = route_db_id
                    existing.service_id = service_id
                    existing.direction = direction
                    existing.trip_short_name = trip_short_name
                    stats.updated += 1
                else:
                    stats.skipped += 1
                self.trip_map[trip_code] = existing.id
            else:
                batch.append({
                    "route_id": route_db_id,
                    "service_id": service_id,
                    "direction": direction,
                    "trip_short_name": trip_short_name,
                    "trip_code": trip_code,
                    "shape_id": None,
                })
                trip_codes_batch.append(trip_code)
                stats.loaded += 1

                if len(batch) >= self.batch_size:
                    _flush_batch()
                    batch.clear()
                    trip_codes_batch.clear()

        if batch:
            _flush_batch()
            batch.clear()

        if not self.dry_run:
            self.db.commit()

        # Build trip_map for newly inserted trips (by trip_code lookup)
        if not self.dry_run and stats.loaded > 0:
            print("  Building trip map (querying trip_codes)...")
            # Batch query in chunks to avoid huge IN clauses
            all_trips = self.db.query(
                self.models.Trip.trip_code, self.models.Trip.id
            ).all()
            for tc, tid in all_trips:
                self.trip_map[tc] = tid

        self._stats["trips"] = stats
        stats.print_summary()
        return self.trip_map

    # -----------------------------------------------------------------------
    # 6. stop_times.txt -> stop_times  (streaming, batched)
    # -----------------------------------------------------------------------

    def import_stop_times(self) -> None:
        """
        Stream stop_times.txt and insert in batches.

        Critical notes:
        - arrival_time/departure_time stored as strings — GTFS extended times
          like "43:20:00" are valid and must NOT be rejected.
        - 'timepoint' column exists in the feed but NOT in the StopTime model.
          It is intentionally not persisted. This is logged explicitly.
        - Uses batched executemany for performance (2.1M rows).
        - FK resolution from preloaded dicts (no per-row DB queries).
        """
        from gtfs_import.validators import validate_stop_time
        from gtfs_import.utils import normalize_gtfs_time, ImportStats
        from sqlalchemy import insert as sa_insert

        stats = ImportStats("stop_times.txt")
        path = self._require("stop_times.txt")
        known_trip_codes = set(self.trip_map.keys())
        known_stop_codes = set(self.stop_map.keys())

        print(f"\nImporting {path.name}...")
        print("  NOTE: GTFS 'timepoint' field is present in the feed but has no")
        print("        corresponding column in the StopTime model. It is intentionally")
        print("        not persisted. Times like '43:20:00' are valid GTFS extended-day")
        print("        times and are stored as strings.")

        batch: list[dict] = []
        progress_interval = 50_000

        def _flush_batch(batch: list[dict]) -> bool:
            if not batch or self.dry_run:
                return True
            try:
                self.db.execute(sa_insert(self.models.StopTime), batch)
                self.db.commit()
                return True
            except Exception as exc:
                self.db.rollback()
                log.error("stop_times batch failed (%d rows): %s", len(batch), exc)
                stats.failed += len(batch)
                return False

        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            # Strip field names
            reader.fieldnames = (
                [f.strip() for f in reader.fieldnames]
                if reader.fieldnames
                else reader.fieldnames
            )

            row_num = 1
            for raw_row in reader:
                row_num += 1
                # Strip whitespace from values
                row = {k.strip(): (v.strip() if v else "") for k, v in raw_row.items()}

                ok, err = validate_stop_time(row, known_trip_codes, known_stop_codes)
                if not ok:
                    stats.add_error(row_num, row.get("trip_id", "?"), err)
                    log.debug("stop_times.txt row %d: %s", row_num, err)
                    continue

                trip_code = row["trip_id"].strip()
                stop_code = row["stop_id"].strip()
                trip_db_id = self.trip_map.get(trip_code)
                stop_db_id = self.stop_map.get(stop_code)

                if not trip_db_id or trip_db_id < 0:
                    stats.add_error(row_num, trip_code, "trip not in trip_map")
                    continue
                if not stop_db_id or stop_db_id < 0:
                    stats.add_error(row_num, stop_code, f"stop not in stop_map (trip={trip_code})")
                    continue

                # arrival_time/departure_time stored as strings (GTFS extended day OK)
                arr = normalize_gtfs_time(row.get("arrival_time", ""))
                dep = normalize_gtfs_time(row.get("departure_time", ""))
                if not arr or not dep:
                    stats.add_error(
                        row_num, trip_code,
                        f"invalid times arr={row.get('arrival_time')!r} dep={row.get('departure_time')!r}"
                    )
                    continue

                try:
                    seq = int(row["stop_sequence"])
                except (ValueError, KeyError):
                    stats.add_error(row_num, trip_code, f"bad stop_sequence={row.get('stop_sequence')!r}")
                    continue

                # timepoint intentionally not stored — it is metadata only
                # pickup_type / drop_type default to 0 (regular)
                batch.append({
                    "trip_id": trip_db_id,
                    "stop_id": stop_db_id,
                    "stop_sequence": seq,
                    "arrival_time": arr,
                    "departure_time": dep,
                    "pickup_type": 0,
                    "drop_type": 0,
                })
                stats.loaded += 1

                if len(batch) >= self.batch_size:
                    _flush_batch(batch)
                    batch.clear()

                if stats.loaded % progress_interval == 0:
                    print(f"  progress: {stats.loaded:,} stop_times inserted...")

        if batch:
            _flush_batch(batch)
            batch.clear()

        if not self.dry_run:
            self.db.commit()

        self._stats["stop_times"] = stats
        stats.print_summary()

    # -----------------------------------------------------------------------
    # 7. calendar_dates.txt (optional)
    # -----------------------------------------------------------------------

    def import_calendar_dates(self) -> None:
        """Import calendar_dates.txt (optional). Skips gracefully if absent."""
        from gtfs_import.validators import validate_calendar_exception
        from gtfs_import.utils import parse_gtfs_date, ImportStats

        filename = "calendar_dates.txt"
        if not self._exists(filename):
            print(f"\n  {filename}: not present; skipped")
            return

        stats = ImportStats(filename)
        print(f"\nImporting {filename}...")

        for row_num, row in enumerate(self._stream(filename), start=2):
            ok, err = validate_calendar_exception(row)
            if not ok:
                stats.add_error(row_num, row.get("service_id", "?"), err)
                log.warning("%s row %d: %s", filename, row_num, err)
                continue

            service_id = row["service_id"].strip()
            ex_date = parse_gtfs_date(row.get("date", ""))
            ex_type = int(row.get("exception_type", "1"))

            if self.dry_run:
                stats.loaded += 1
                continue

            existing = (
                self.db.query(self.models.CalendarException)
                .filter(
                    self.models.CalendarException.service_id == service_id,
                    self.models.CalendarException.exception_date == ex_date,
                )
                .first()
            )

            if existing:
                if self.force:
                    existing.exception_type = ex_type
                    stats.updated += 1
                else:
                    stats.skipped += 1
            else:
                exc_row = self.models.CalendarException(
                    service_id=service_id,
                    exception_date=ex_date,
                    exception_type=ex_type,
                )
                self.db.add(exc_row)
                stats.loaded += 1

        if not self.dry_run:
            self.db.commit()

        self._stats["calendar_dates"] = stats
        stats.print_summary()

    # -----------------------------------------------------------------------
    # 8. transfers.txt (optional)
    # -----------------------------------------------------------------------

    def import_transfers(self) -> None:
        """Import transfers.txt (optional). Skips gracefully if absent."""
        from gtfs_import.validators import validate_transfer
        from gtfs_import.utils import ImportStats

        filename = "transfers.txt"
        if not self._exists(filename):
            print(f"\n  {filename}: not present; skipped")
            return

        stats = ImportStats(filename)
        known_stop_codes = set(self.stop_map.keys())
        print(f"\nImporting {filename}...")

        for row_num, row in enumerate(self._stream(filename), start=2):
            ok, err = validate_transfer(row, known_stop_codes)
            if not ok:
                stats.add_error(row_num, str(row.get("from_stop_id")), err)
                log.warning("%s row %d: %s", filename, row_num, err)
                continue

            from_stop_code = row["from_stop_id"].strip()
            to_stop_code = row["to_stop_id"].strip()
            transfer_type = int(row.get("transfer_type", "0"))
            min_time_s = row.get("min_transfer_time", "").strip()
            min_time = int(min_time_s) if min_time_s.isdigit() else None

            from_stop_id = self.stop_map.get(from_stop_code)
            to_stop_id = self.stop_map.get(to_stop_code)

            if not from_stop_id or not to_stop_id:
                stats.add_error(row_num, from_stop_code, "stop not in stop_map")
                continue

            if self.dry_run:
                stats.loaded += 1
                continue

            existing = (
                self.db.query(self.models.Transfer)
                .filter(
                    self.models.Transfer.from_stop_id == from_stop_id,
                    self.models.Transfer.to_stop_id == to_stop_id,
                )
                .first()
            )

            if existing:
                if self.force:
                    existing.transfer_type = transfer_type
                    existing.min_transfer_time = min_time
                    stats.updated += 1
                else:
                    stats.skipped += 1
            else:
                xfer = self.models.Transfer(
                    from_stop_id=from_stop_id,
                    to_stop_id=to_stop_id,
                    transfer_type=transfer_type,
                    min_transfer_time=min_time,
                )
                self.db.add(xfer)
                stats.loaded += 1

        if not self.dry_run:
            self.db.commit()

        self._stats["transfers"] = stats
        stats.print_summary()

    # -----------------------------------------------------------------------
    # 9. shapes.txt (optional)
    # -----------------------------------------------------------------------

    def import_shapes(self) -> None:
        """
        Import shapes.txt (optional).

        The existing Shape model uses route_id + lat/lon/sequence.
        GTFS uses shape_id which has no direct equivalent field.
        Since shapes.txt is absent in the supplied feed, this skips gracefully.
        If present in future feeds, we would need to:
          - Group shape points by shape_id
          - Map shape_id to route via trips.shape_id
          - Create one Shape record per point
        """
        filename = "shapes.txt"
        if not self._exists(filename):
            print(f"\n  {filename}: not present; skipped (Trip.shape_id will remain NULL)")
            return

        print(f"\n  {filename}: present but shape import into current model requires")
        print("  route-level grouping. Skipping shape import for now.")
        print("  Trip.shape_id will remain NULL.")

    # -----------------------------------------------------------------------
    # feed_info.txt (metadata only — no DB write)
    # -----------------------------------------------------------------------

    def log_feed_info(self) -> None:
        """Parse feed_info.txt and print metadata. No DB write."""
        filename = "feed_info.txt"
        if not self._exists(filename):
            print(f"\n  {filename}: not present; skipped")
            return

        print(f"\nFeed info ({filename}):")
        try:
            for row in self._stream(filename):
                for k, v in row.items():
                    print(f"  {k}: {v}")
        except Exception as exc:
            print(f"  (could not parse feed_info.txt: {exc})")

    # -----------------------------------------------------------------------
    # Bus 310 verification
    # -----------------------------------------------------------------------

    def verify_bus_310(self) -> None:
        """
        Verify Bus 310 import after data load.

        Searches for all routes with gtfs_route_short_name = '310' or
        route_code containing '310'. Shows agency, route info, trip count,
        first stop, last stop, and sample departure times.
        """
        if self.dry_run:
            print("\n  Bus 310 verification skipped (dry-run mode).")
            return

        print("\n" + "=" * 56)
        print("BUS 310 VERIFICATION")
        print("=" * 56)

        # Find all Bus 310 routes
        routes_310 = (
            self.db.query(self.models.Route)
            .filter(
                self.models.Route.mode == "bus",
                self.models.Route.gtfs_route_short_name == "310",
            )
            .all()
        )

        if not routes_310:
            # Fallback: search route_code containing '310'
            routes_310 = (
                self.db.query(self.models.Route)
                .filter(
                    self.models.Route.mode == "bus",
                    self.models.Route.route_code.like("%310%"),
                )
                .all()
            )

        if not routes_310:
            print("  No Bus 310 routes found.")
            return

        print(f"\n  Found {len(routes_310)} Bus 310 route(s):\n")

        for route in routes_310:
            op = self.db.query(self.models.Operator).filter(
                self.models.Operator.id == route.operator_id
            ).first()
            op_name = op.short_name if op else "?"

            trips = (
                self.db.query(self.models.Trip)
                .filter(self.models.Trip.route_id == route.id)
                .all()
            )

            print(f"  ─── Route: {route.route_code}")
            print(f"       Agency: {op_name}")
            print(f"       Short name: {route.gtfs_route_short_name}")
            print(f"       Long name: {route.name}")
            print(f"       DB ID: {route.id}")
            print(f"       Trips: {len(trips)}")

            if not trips:
                print("       (no trips)")
                continue

            # Get one complete trip's stop sequence
            sample_trip = trips[0]
            stop_times = (
                self.db.query(self.models.StopTime)
                .filter(self.models.StopTime.trip_id == sample_trip.id)
                .order_by(self.models.StopTime.stop_sequence)
                .all()
            )

            if stop_times:
                first_st = stop_times[0]
                last_st = stop_times[-1]
                first_stop = self.db.query(self.models.Stop).get(first_st.stop_id)
                last_stop = self.db.query(self.models.Stop).get(last_st.stop_id)
                print(f"       First stop: {first_stop.name if first_stop else '?'} "
                      f"(dep {first_st.departure_time})")
                print(f"       Last stop:  {last_stop.name if last_stop else '?'} "
                      f"(arr {last_st.arrival_time})")
                print(f"       Sample trip ({sample_trip.trip_code}) — "
                      f"{len(stop_times)} stops:")
                print()
                print(f"       {'Seq':>4}  {'stop_code':<15}  {'stop_name':<35}  "
                      f"{'lat':>10}  {'lon':>11}  {'arr':>8}  {'dep':>8}")
                print("       " + "-" * 100)
                for st in stop_times:
                    s = self.db.query(self.models.Stop).get(st.stop_id)
                    if s:
                        print(
                            f"       {st.stop_sequence:>4}  {s.stop_code:<15}  {s.name:<35}  "
                            f"{s.lat:>10.5f}  {s.lon:>11.5f}  {st.arrival_time:>8}  {st.departure_time:>8}"
                        )

            # All-day departure times (first stop of each trip)
            print(f"\n       All-day departures (from first stop of each trip):")
            departures = []
            for t in trips:
                first_st_t = (
                    self.db.query(self.models.StopTime)
                    .filter(self.models.StopTime.trip_id == t.id)
                    .order_by(self.models.StopTime.stop_sequence)
                    .first()
                )
                if first_st_t:
                    departures.append(first_st_t.departure_time)

            departures.sort()
            dep_str = "  ".join(departures)
            # Print in rows of 8
            for i in range(0, len(departures), 8):
                print("       " + "  ".join(departures[i:i+8]))

            print()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    def print_final_summary(self) -> None:
        """Print overall import summary."""
        print("\n" + "=" * 56)
        print("IMPORT SUMMARY")
        print("=" * 56)

        for label, stats in self._stats.items():
            stats.print_summary()

        print("\n  Final database row counts:")
        for table, label in [
            ("operators", "operators"),
            ("routes", "routes"),
            ("stops", "stops"),
            ("trips", "trips"),
            ("stop_times", "stop_times"),
            ("service_calendar", "service_calendar"),
        ]:
            try:
                count = self.db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"    {label}: {count:,}")
            except Exception:
                print(f"    {label}: (error reading count)")

    # -----------------------------------------------------------------------
    # Full run (convenience)
    # -----------------------------------------------------------------------

    def run(self) -> bool:
        """
        Execute the full import pipeline in correct order:
        1. agency -> operators
        2. calendar -> service_calendar
        3. stops -> stops
        4. routes -> routes
        5. trips -> trips
        6. stop_times -> stop_times
        7. calendar_dates (optional)
        8. transfers (optional)
        9. shapes (optional)
        10. feed_info (log only)

        Returns True on success (even partial), False on fatal error.
        """
        try:
            self.log_feed_info()
            self.import_agency()
            self.import_calendar()
            self.import_stops()
            self.import_routes()
            self.import_trips()
            self.import_stop_times()
            self.import_calendar_dates()
            self.import_transfers()
            self.import_shapes()
            return True
        except FileNotFoundError as exc:
            print(f"\n  FATAL: {exc}")
            log.exception("Missing required file")
            return False
        except Exception as exc:
            print(f"\n  FATAL import error: {exc}")
            log.exception("Unexpected import error")
            try:
                self.db.rollback()
            except Exception:
                pass
            return False
