"""
gtfs_import/validators.py
==========================
Row-level validators for each GTFS file.

Each validator returns (ok: bool, error_message: str).
Validators do NOT raise exceptions — they return False so the importer
can log and skip individual bad rows without aborting the whole feed.
"""

from __future__ import annotations

from typing import Any

from gtfs_import.utils import validate_coord, normalize_gtfs_time


# ---------------------------------------------------------------------------
# agency.txt
# ---------------------------------------------------------------------------

def validate_agency(row: dict[str, str]) -> tuple[bool, str]:
    """Validate a single row from agency.txt."""
    agency_id = row.get("agency_id", "").strip()
    agency_name = row.get("agency_name", "").strip()

    if not agency_id:
        return False, "agency_id is empty"
    if not agency_name:
        return False, f"agency_name is empty for agency_id={agency_id!r}"
    return True, ""


# ---------------------------------------------------------------------------
# routes.txt
# ---------------------------------------------------------------------------

def validate_route(
    row: dict[str, str],
    known_agency_ids: set[str],
) -> tuple[bool, str]:
    """Validate a single row from routes.txt."""
    route_id = row.get("route_id", "").strip()
    agency_id = row.get("agency_id", "").strip()

    if not route_id:
        return False, "route_id is empty"
    if not agency_id:
        return False, f"agency_id is empty for route_id={route_id!r}"
    if known_agency_ids and agency_id not in known_agency_ids:
        return False, f"agency_id={agency_id!r} not in imported agencies for route_id={route_id!r}"
    return True, ""


# ---------------------------------------------------------------------------
# stops.txt
# ---------------------------------------------------------------------------

def validate_stop(row: dict[str, str]) -> tuple[bool, str]:
    """Validate a single row from stops.txt."""
    stop_id = row.get("stop_id", "").strip()
    stop_name = row.get("stop_name", "").strip()
    lat_s = row.get("stop_lat", "").strip()
    lon_s = row.get("stop_lon", "").strip()

    if not stop_id:
        return False, "stop_id is empty"
    if not stop_name:
        return False, f"stop_name is empty for stop_id={stop_id!r}"
    if not lat_s or not lon_s:
        return False, f"missing lat/lon for stop_id={stop_id!r}"

    try:
        lat, lon = float(lat_s), float(lon_s)
    except ValueError:
        return False, f"non-numeric lat/lon for stop_id={stop_id!r}: lat={lat_s!r} lon={lon_s!r}"

    if not validate_coord(lat, lon):
        return False, (
            f"coordinates out of range for stop_id={stop_id!r}: "
            f"lat={lat} lon={lon}"
        )
    return True, ""


# ---------------------------------------------------------------------------
# calendar.txt
# ---------------------------------------------------------------------------

def validate_calendar(row: dict[str, str]) -> tuple[bool, str]:
    """Validate a single row from calendar.txt."""
    service_id = row.get("service_id", "").strip()
    if not service_id:
        return False, "service_id is empty"

    for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
        val = row.get(day, "").strip()
        if val not in ("0", "1"):
            return False, f"invalid {day} value={val!r} for service_id={service_id!r}"

    start = row.get("start_date", "").strip()
    end = row.get("end_date", "").strip()
    if not start or not end:
        return False, f"missing start_date/end_date for service_id={service_id!r}"
    return True, ""


# ---------------------------------------------------------------------------
# trips.txt
# ---------------------------------------------------------------------------

def validate_trip(
    row: dict[str, str],
    known_route_ids: set[str],
    known_service_ids: set[str],
) -> tuple[bool, str]:
    """Validate a single row from trips.txt."""
    trip_id = row.get("trip_id", "").strip()
    route_id = row.get("route_id", "").strip()
    service_id = row.get("service_id", "").strip()

    if not trip_id:
        return False, "trip_id is empty"
    if not route_id:
        return False, f"route_id is empty for trip_id={trip_id!r}"
    if not service_id:
        return False, f"service_id is empty for trip_id={trip_id!r}"

    if known_route_ids and route_id not in known_route_ids:
        return False, f"route_id={route_id!r} not in imported routes for trip_id={trip_id!r}"
    if known_service_ids and service_id not in known_service_ids:
        return False, (
            f"service_id={service_id!r} not in imported service_calendar "
            f"for trip_id={trip_id!r}"
        )
    return True, ""


# ---------------------------------------------------------------------------
# stop_times.txt
# ---------------------------------------------------------------------------

def validate_stop_time(
    row: dict[str, str],
    known_trip_codes: set[str],
    known_stop_codes: set[str],
) -> tuple[bool, str]:
    """Validate a single row from stop_times.txt."""
    trip_id = row.get("trip_id", "").strip()
    stop_id = row.get("stop_id", "").strip()
    stop_seq_s = row.get("stop_sequence", "").strip()
    arr = row.get("arrival_time", "").strip()
    dep = row.get("departure_time", "").strip()

    if not trip_id:
        return False, "trip_id is empty"
    if not stop_id:
        return False, f"stop_id is empty for trip_id={trip_id!r}"

    if known_trip_codes and trip_id not in known_trip_codes:
        return False, f"trip_id={trip_id!r} not in imported trips"
    if known_stop_codes and stop_id not in known_stop_codes:
        return False, f"stop_id={stop_id!r} not in imported stops (trip={trip_id!r})"

    if not stop_seq_s:
        return False, f"stop_sequence is empty for trip={trip_id!r} stop={stop_id!r}"
    try:
        seq = int(stop_seq_s)
        if seq < 0:
            return False, f"stop_sequence={seq} is negative for trip={trip_id!r}"
    except ValueError:
        return False, f"stop_sequence={stop_seq_s!r} is not numeric for trip={trip_id!r}"

    if not arr:
        return False, f"arrival_time is empty for trip={trip_id!r} seq={stop_seq_s}"
    if not dep:
        return False, f"departure_time is empty for trip={trip_id!r} seq={stop_seq_s}"

    if normalize_gtfs_time(arr) is None:
        return False, f"invalid arrival_time={arr!r} for trip={trip_id!r} seq={stop_seq_s}"
    if normalize_gtfs_time(dep) is None:
        return False, f"invalid departure_time={dep!r} for trip={trip_id!r} seq={stop_seq_s}"

    return True, ""


# ---------------------------------------------------------------------------
# calendar_dates.txt (optional)
# ---------------------------------------------------------------------------

def validate_calendar_exception(row: dict[str, str]) -> tuple[bool, str]:
    """Validate a row from calendar_dates.txt."""
    service_id = row.get("service_id", "").strip()
    ex_date = row.get("date", "").strip()
    ex_type = row.get("exception_type", "").strip()

    if not service_id:
        return False, "service_id is empty"
    if not ex_date:
        return False, f"date is empty for service_id={service_id!r}"
    if ex_type not in ("1", "2"):
        return False, (
            f"exception_type={ex_type!r} must be 1 or 2 for service_id={service_id!r}"
        )
    return True, ""


# ---------------------------------------------------------------------------
# transfers.txt (optional)
# ---------------------------------------------------------------------------

def validate_transfer(
    row: dict[str, str],
    known_stop_codes: set[str],
) -> tuple[bool, str]:
    """Validate a row from transfers.txt."""
    from_stop = row.get("from_stop_id", "").strip()
    to_stop = row.get("to_stop_id", "").strip()
    t_type = row.get("transfer_type", "").strip()

    if not from_stop:
        return False, "from_stop_id is empty"
    if not to_stop:
        return False, "to_stop_id is empty"
    if known_stop_codes:
        if from_stop not in known_stop_codes:
            return False, f"from_stop_id={from_stop!r} not in imported stops"
        if to_stop not in known_stop_codes:
            return False, f"to_stop_id={to_stop!r} not in imported stops"
    try:
        int(t_type)
    except ValueError:
        return False, f"transfer_type={t_type!r} is not numeric"
    return True, ""
