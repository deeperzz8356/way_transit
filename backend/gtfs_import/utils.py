"""
gtfs_import/utils.py
====================
Pure utility helpers for the WAY_TRANSIT GTFS importer.

Key design decisions:
- GTFS times (arrival_time, departure_time) are stored as plain strings.
  The GTFS spec allows extended service-day hours like "43:20:00".
  Python's datetime.time only accepts 0-23, so we NEVER parse these to time.
- Coordinates are validated but stored as floats, not rounded.
- City/operator lookups are idempotent (get-or-create by slug/short_name).
"""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Generator, Optional

log = logging.getLogger("gtfs_import.utils")


# ---------------------------------------------------------------------------
# GTFS time helpers
# ---------------------------------------------------------------------------

def is_valid_gtfs_time(s: str) -> bool:
    """
    Validate a GTFS time string (HH:MM:SS).

    GTFS allows hours >= 24 for trips crossing midnight:
    e.g. "25:30:00" = 1:30 AM next service day.
    We accept any HH:MM:SS where HH >= 0, MM 0-59, SS 0-59.
    """
    if not s or not isinstance(s, str):
        return False
    parts = s.strip().split(":")
    if len(parts) != 3:
        return False
    try:
        h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
        return h >= 0 and 0 <= m <= 59 and 0 <= sec <= 59
    except (ValueError, TypeError):
        return False


def normalize_gtfs_time(s: str) -> Optional[str]:
    """
    Return a normalized GTFS time string, or None if invalid.
    Strips whitespace; does NOT clamp hours to < 24.
    """
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if is_valid_gtfs_time(s):
        return s
    return None


# ---------------------------------------------------------------------------
# GTFS date helpers
# ---------------------------------------------------------------------------

def parse_gtfs_date(s: str) -> Optional[date]:
    """Parse a GTFS date string (YYYYMMDD) to a Python date, or None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Coordinate validation
# ---------------------------------------------------------------------------

def validate_coord(lat: Any, lon: Any) -> bool:
    """Return True if lat/lon are within valid WGS84 ranges."""
    try:
        flat, flon = float(lat), float(lon)
        return -90.0 <= flat <= 90.0 and -180.0 <= flon <= 180.0
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# CSV streaming
# ---------------------------------------------------------------------------

def stream_csv(path: Path) -> Generator[dict[str, str], None, None]:
    """
    Lazily yield rows from a CSV file as dicts.

    Uses Python's csv.DictReader for memory efficiency.
    Does NOT load the entire file into memory.
    Strips leading/trailing whitespace from all field values.
    """
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Strip whitespace from keys and values
            yield {k.strip(): (v.strip() if v else "") for k, v in row.items()}


def count_csv_rows(path: Path) -> int:
    """Count data rows (excluding header) in a CSV file efficiently."""
    count = 0
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        for _ in reader:
            count += 1
    return count


# ---------------------------------------------------------------------------
# City config for this specific feed
# ---------------------------------------------------------------------------

# Deterministic agency_id -> city config mapping for the provided feed.
# Adjust if the actual database has different names/slugs.
AGENCY_CITY_MAP: dict[str, dict[str, Any]] = {
    "BEST": {
        "name": "Mumbai",
        "slug": "mumbai",
        "state": "Maharashtra",
        "country": "India",
        "center_lat": 19.0760,
        "center_lon": 72.8777,
    },
    "KDMT": {
        "name": "Kalyan-Dombivli",
        "slug": "kalyan-dombivli",
        "state": "Maharashtra",
        "country": "India",
        "center_lat": 19.2403,
        "center_lon": 73.1305,
    },
    "TMT": {
        "name": "Thane",
        "slug": "thane",
        "state": "Maharashtra",
        "country": "India",
        "center_lat": 19.2183,
        "center_lon": 72.9781,
    },
    "VVMT": {
        "name": "Vasai-Virar",
        "slug": "vasai-virar",
        "state": "Maharashtra",
        "country": "India",
        "center_lat": 19.3872,
        "center_lon": 72.8490,
    },
}


def get_or_create_city(db, models, agency_id: str) -> Any:
    """
    Get or create a City row for the given agency_id.

    Uses the AGENCY_CITY_MAP for deterministic city resolution.
    Falls back to a generic city using agency_id if unknown.
    """
    cfg = AGENCY_CITY_MAP.get(agency_id)
    if cfg is None:
        log.warning("Unknown agency_id '%s'; using generic city entry.", agency_id)
        cfg = {
            "name": agency_id,
            "slug": agency_id.lower(),
            "state": "Unknown",
            "country": "India",
            "center_lat": None,
            "center_lon": None,
        }

    city = db.query(models.City).filter(models.City.slug == cfg["slug"]).first()
    if not city:
        city = models.City(
            name=cfg["name"],
            slug=cfg["slug"],
            state=cfg["state"],
            country=cfg["country"],
            center_lat=cfg.get("center_lat"),
            center_lon=cfg.get("center_lon"),
            is_active=True,
        )
        db.add(city)
        db.flush()
        log.info("Created city: %s (slug=%s)", city.name, city.slug)
    return city


# ---------------------------------------------------------------------------
# Logging / summary helpers
# ---------------------------------------------------------------------------

class ImportStats:
    """Track loaded/updated/skipped/failed counts per file."""

    def __init__(self, label: str):
        self.label = label
        self.loaded = 0
        self.updated = 0
        self.skipped = 0
        self.failed = 0
        self.errors: list[str] = []

    def add_error(self, row_num: int, identifier: str, error: str, action: str = "skipped"):
        msg = (
            f"  row {row_num} | id={identifier!r} | error={error} | action={action}"
        )
        self.errors.append(msg)
        if action == "skipped":
            self.skipped += 1
        else:
            self.failed += 1

    def print_summary(self):
        print(
            f"  {self.label}: loaded={self.loaded} updated={self.updated} "
            f"skipped={self.skipped} failed={self.failed}"
        )
        if self.errors:
            print(f"  Errors/warnings ({len(self.errors)}):")
            for e in self.errors[:20]:  # cap at 20 for readability
                print(e)
            if len(self.errors) > 20:
                print(f"  ... and {len(self.errors) - 20} more (see log for details)")
