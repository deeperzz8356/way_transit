#!/usr/bin/env python3
"""
import_trains.py
================
WAY TRANSIT — Mumbai Train Timetable Importer

Imports all 54 CSV timetable files into the EXISTING way_transit database
using the EXISTING tables: stops, routes, trips, stop_times, service_calendar.

NO new tables are created.
Existing bus / metro data is NEVER touched.

Usage (run from project root or backend/):
    python backend/import_trains.py
    python backend/import_trains.py --dry-run
    python backend/import_trains.py --reset-trains
    python backend/import_trains.py --data-dir backend/data
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Ensure the backend directory is on sys.path
# ---------------------------------------------------------------------------
_BACKEND = Path(__file__).parent.resolve()
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("import_trains")

# ===========================================================================
# STATION KNOWLEDGE BASE
# Maps every abbreviated code found in the CSVs to a human-readable name.
# ===========================================================================
STATION_NAMES: Dict[str, str] = {
    # Trans-Harbour Line codes (short)
    "TNA": "Thane",
    "THANE": "Thane",
    "DIGH": "Dighoda",
    "AIRL": "Airoli",
    "RABE": "Rabale",
    "GNSL": "Ghansoli",
    "KPHN": "Koparkhairane",
    "TUH": "Turbhe",
    "SNPD": "Sanpada",
    "VSH": "Vashi",
    "JNJ": "Juinagar",
    "NEU": "Nerul",
    "SWDV": "Seawood Darave",
    "BEPR": "Belapur CBD",
    "KHAG": "Kharghar",
    "MANR": "Mansarovar",
    "KNDS": "Khandeshwar",
    "PNVL": "Panvel",
    # Uran Line full names (as they appear in CSVs)
    "NERUL": "Nerul",
    "SEAWOODS DARAVE": "Seawood Darave",
    "BELAPUR": "Belapur CBD",
    "BAMANDONGRI": "Bamandongri",
    "KHARKOPAR": "Kharkopar",
    "SHEMATIKHAR": "Shematikhar",
    "NHAVE-SHEVA": "Nhave Sheva",
    "DRONAGIRI": "Dronagiri",
    "URAN": "Uran",
    # Harbour / Western full-name normalisations
    "MUMBAI CSMT": "Mumbai CSMT",
    "M'BAI CENTRAL": "Mumbai Central",
    "M'BAI CENTRAL (L)": "Mumbai Central",
    "M'BAI CENTRAL(L": "Mumbai Central",
    "M'BAI CENTRAL(L)": "Mumbai Central",
    "M'BAI CENTRAL(L,": "Mumbai Central",
    "CHURCHGATE": "Churchgate",
    "DADAR": "Dadar",
    "BANDRA": "Bandra",
    "ANDHERI": "Andheri",
    "BORIVALI": "Borivali",
    "VIRAR": "Virar",
    "VASAI ROAD": "Vasai Road",
    "BHAYANDAR": "Bhayandar",
    "DAHANU ROAD": "Dahanu Road",
    "SAPHALE": "Saphale",
    "PALGHAR": "Palghar",
    "BOISAR": "Boisar",
}

# ---------------------------------------------------------------------------
# Coordinates for known stations  (lat, lon)
# ---------------------------------------------------------------------------
STATION_COORDS: Dict[str, Tuple[float, float]] = {
    # Trans-Harbour
    "Thane": (19.1896, 72.9656),
    "Dighoda": (19.1578, 73.0134),
    "Airoli": (19.1528, 72.9979),
    "Rabale": (19.1419, 72.9987),
    "Ghansoli": (19.1289, 73.0006),
    "Koparkhairane": (19.1143, 73.0092),
    "Turbhe": (19.0919, 73.0152),
    "Sanpada": (19.0726, 73.0100),
    "Vashi": (19.0755, 72.9989),
    "Juinagar": (19.0624, 73.0063),
    "Nerul": (19.0374, 73.0170),
    "Seawood Darave": (19.0160, 73.0280),
    "Belapur CBD": (19.0179, 73.0408),
    "Kharghar": (19.0467, 73.0685),
    "Mansarovar": (19.0283, 73.0784),
    "Khandeshwar": (19.0103, 73.0882),
    "Panvel": (18.9894, 73.1175),
    # Uran Line
    "Bamandongri": (18.9748, 73.0512),
    "Kharkopar": (18.9573, 73.0466),
    "Shematikhar": (18.9296, 73.0387),
    "Nhave Sheva": (18.9143, 73.0255),
    "Dronagiri": (18.8943, 73.0168),
    "Uran": (18.8787, 72.9989),
    # Harbour Line
    "Mumbai CSMT": (18.9398, 72.8354),
    "Masjid": (18.9456, 72.8339),
    "Sandhurst Road": (18.9497, 72.8321),
    "Dockyard Road": (18.9548, 72.8314),
    "Reay Road": (18.9596, 72.8314),
    "Cotton Green": (18.9640, 72.8330),
    "Sewri": (18.9701, 72.8426),
    "Vadala Road": (18.9823, 72.8505),
    "GTB Nagar": (18.9990, 72.8612),
    "Chunabhatti": (19.0033, 72.8668),
    "Kurla": (19.0654, 72.8793),
    "Tilaknagar": (19.0733, 72.8893),
    "Chembur": (19.0616, 72.8995),
    "Govandi": (19.0549, 72.9194),
    "Mankhurd": (19.0463, 72.9378),
    "King's Circle": (19.0206, 72.8553),
    "Mahim Jn": (19.0405, 72.8416),
    "Mahim Jn.": (19.0405, 72.8416),
    "Bandra": (19.0542, 72.8395),
    "Khar Road": (19.0651, 72.8363),
    "Santacruz": (19.0807, 72.8390),
    "Santa Cruz": (19.0807, 72.8390),
    "Vileparle": (19.0997, 72.8490),
    "Vile Parle": (19.0997, 72.8490),
    "Andheri": (19.1193, 72.8482),
    "Jogeshwari": (19.1355, 72.8493),
    "Ramnagar": (19.1474, 72.8499),
    "Ram Mandir": (19.1474, 72.8499),
    "Goregaon": (19.1601, 72.8491),
    # Western Railway
    "Churchgate": (18.9355, 72.8258),
    "Marine Lines": (18.9431, 72.8243),
    "Charni Road": (18.9519, 72.8201),
    "Grant Road": (18.9639, 72.8148),
    "Mumbai Central": (18.9698, 72.8191),
    "Mahalakshmi": (18.9842, 72.8174),
    "Lower Parel": (19.0002, 72.8183),
    "Prabhadevi": (19.0108, 72.8246),
    "Dadar": (19.0182, 72.8430),
    "Matunga Road": (19.0291, 72.8440),
    "Malad": (19.1869, 72.8483),
    "Kandivli": (19.2067, 72.8502),
    "Borivali": (19.2306, 72.8567),
    "Dahisar": (19.2504, 72.8589),
    "Mira Road": (19.2842, 72.8715),
    "Bhayandar": (19.3066, 72.8591),
    "Naigaon": (19.3579, 72.8563),
    "Vasai Road": (19.3783, 72.8316),
    "Nalla Sopara": (19.4162, 72.8106),
    "Nallasopara": (19.4162, 72.8106),
    "Virar": (19.4640, 72.8025),
    "Vaiterna": (19.5031, 72.7948),
    "Saphale": (19.5406, 72.7801),
    "Kelve Road": (19.6058, 72.7438),
    "Palghar": (19.6975, 72.7650),
    "Umroli": (19.7571, 72.7545),
    "Boisar": (19.8029, 72.7613),
    "Vangaon": (19.8891, 72.7421),
    "Dahanu Road": (19.9779, 72.7203),
}

# ---------------------------------------------------------------------------
# Rows / cell values that are NEVER real station names
# ---------------------------------------------------------------------------
_SKIP_ROW_PREFIXES_UPPER = (
    "$", "*", "X_NOT", "X NOT",
    "AIR CONDITIONED",
    "NOT ON SUN", "NOT ON HOLIDAY",
    "LADIES SPL", "LADIES SPECIAL",
    "GRANT_ROAD_CHARNI", "HARBOUR_MUMBAI", "HARBOUR_PANVEL",
    "W.E.F", "PUBLIC TIME",
)

_ANNOTATION_KEYWORDS_UPPER = (
    "*LADIES SPL", "$ TNA",
)

# Rows whose first non-empty cell matches one of these → skip
_SKIP_EXACT_UPPER = {
    "TRAIN NO. TRAIN CODE", "TR.NO TR.CODE",
    "STATIONS", "STATION",
    "STATIONS DN TRAINS", "STATIONS UP TRAINS",
    "UP TRAINS STATIONS", "DN TRAINS STATIONS",
    "TRAIN NO TRAIN CODE",
    "AIR CONDITIONED SERVICES",
}

# ===========================================================================
# TIME HELPERS
# ===========================================================================
_TIME_RE = re.compile(r'^\d{1,2}:\d{2}$')


def is_valid_time(val: str) -> bool:
    val = val.strip()
    if not _TIME_RE.match(val):
        return False
    h, m = val.split(':')
    return 0 <= int(h) <= 28 and 0 <= int(m) <= 59


def normalise_time(val: str) -> str:
    h, m = val.strip().split(':')
    return f"{int(h):02d}:{int(m):02d}"


# ===========================================================================
# STATION NAME HELPERS
# ===========================================================================
def normalise_station_name(raw: str) -> str:
    """
    Convert a raw CSV cell to a canonical station name.
    Returns '' if the cell is not a genuine station.
    """
    raw = raw.strip()
    if not raw:
        return ""

    up = raw.upper()

    # Quick exact-match skip
    if up in _SKIP_EXACT_UPPER:
        return ""

    # Prefix-based skip
    for prefix in _SKIP_ROW_PREFIXES_UPPER:
        if up.startswith(prefix):
            return ""

    # Annotation keywords
    for kw in _ANNOTATION_KEYWORDS_UPPER:
        if up.startswith(kw):
            return ""

    # Starts with "$"
    if raw.startswith("$") or raw.startswith("*"):
        return ""

    # Looks like a train number (5 leading digits)
    if re.match(r'^\d{5}', raw):
        return ""

    # Looks like "BSR 90065 12 CAR" — a train column header leaked in
    if re.match(r'^[A-Z]{1,5}\s+\d{4,6}(\s|$)', up):
        return ""

    # Lookup table (exact match on upper)
    if up in STATION_NAMES:
        return STATION_NAMES[up]

    # Partial lookup for truncated keys like "M'BAI CENTRAL(L"
    for key, name in STATION_NAMES.items():
        if len(key) >= 8 and key in up:
            return name

    # Remove pandas dedup suffix ".1", ".2" etc.
    clean = re.sub(r'\.\d+$', '', raw).strip()

    # Skip if the whole name looks like a route-description combo
    # (≥3 words, ≥2 route keywords)
    _ROUTE_KW = frozenset(
        ("PANVEL", "GOREGAON", "CHURCHGATE", "VIRAR", "DAHANU",
         "CSMT", "HARBOUR", "WESTERN", "BOISAR", "LINE")
    )
    words = clean.split()
    if len(words) >= 3:
        hits = sum(1 for w in words if w.upper() in _ROUTE_KW)
        if hits >= 2:
            return ""

    # Skip generic annotation words that appear alone
    _JUNK = frozenset((
        "AIR", "CONDITION", "NOT", "SUN", "ONLY", "HOLIDAY",
        "LADIES", "GENERAL", "COACH", "COACHES", "RESERVED",
        "NON", "AC", "ON", "SAT", "&", "AND", "SUN.", "--",
        "T", "P",   # single-letter placeholders
    ))
    if clean.upper() in _JUNK:
        return ""

    # What remains is treated as a genuine station name
    return clean


def station_stop_code(name: str) -> str:
    """Stable stop_code derived from station name."""
    return re.sub(r'[^A-Z0-9]', '_', name.upper()).strip('_')


# ===========================================================================
# TRAIN NUMBER / LINE HELPERS
# ===========================================================================
def extract_train_number(raw: str) -> str:
    """
    Pull the 4-6 digit numeric train number from any header string.
    Works for: '99001 Thane - Panvel Local 1', 'BSR 90065 12 CAR', 'VR 92017 12 CAR.1'
    """
    raw = re.sub(r'\.\d+$', '', raw).strip()   # strip pandas dedup suffix
    m = re.search(r'\b(\d{4,6})\b', raw)
    return m.group(1) if m else raw


def infer_line(train_no: str) -> Tuple[str, str, str]:
    """
    Returns (line_key, route_code, route_name) from a train number.
      99xxx → Trans-Harbour Line
      98xxx → Harbour Line
      93xxx → Western Railway (Dahanu fast)
      90/91/92/94xxx → Western Railway
    """
    digits = re.sub(r'\D', '', train_no)[:5]
    if not digits:
        return ("UNKNOWN", "UNKNOWN", "Unknown Line")
    prefix = int(digits[:2])
    if prefix == 99:
        return ("TRANS_HARBOUR", "TRANS_HARBOUR", "Trans-Harbour Line")
    elif prefix == 98:
        return ("HARBOUR", "HARBOUR_LINE", "Harbour Line")
    elif prefix in (90, 91, 92, 93, 94):
        return ("WESTERN", "WESTERN_LINE", "Western Railway Line")
    elif prefix in (95, 96, 97):
        return ("CENTRAL", "CENTRAL_LINE", "Central Railway Line")
    else:
        return ("CENTRAL", "CENTRAL_LINE", "Central Railway Line")


def extract_service_flags(raw: str) -> Tuple[bool, bool, bool, bool, bool, bool, bool]:
    """
    Parse day-of-service restrictions.  Returns (mon..sun).
    Default: runs every day.
    """
    up = raw.upper()
    sun = True
    if "NOT ON SUN" in up or "WILL NOT RUN ON SUNDAY" in up or "NOT ON SUNDAY" in up:
        sun = False
    return True, True, True, True, True, True, sun


# ===========================================================================
# ROW CLASSIFICATION
# ===========================================================================
def is_blank_or_annotation_row(values: List[str]) -> bool:
    """True if the row carries no timetable data (empty or annotation)."""
    non_empty = [v.strip() for v in values if v.strip()]
    if not non_empty:
        return True
    v0 = non_empty[0].upper()

    for prefix in _SKIP_ROW_PREFIXES_UPPER:
        if v0.startswith(prefix):
            return True
    for kw in _ANNOTATION_KEYWORDS_UPPER:
        if v0.startswith(kw):
            return True
    if non_empty[0].startswith("$") or non_empty[0].startswith("*"):
        return True
    return False


def is_combined_section_and_train_header(values: List[str]) -> bool:
    """
    Western Railway files put section marker AND train columns on the same row:
    e.g. "STATIONS DN TRAINS, BSR 90065 12 CAR, VR 90067 12 CAR, ..."
         "STATIONS UP TRAINS, VR 94036 12 CAR, ..."
         "UP TRAINS STATIONS, VR 94036 12 CAR, ..."
    Returns True only when the row has BOTH a section marker AND train columns.
    """
    if not values or not values[0]:
        return False
    v0 = values[0].strip().upper()
    MARKERS = (
        "STATIONS DN TRAINS", "STATIONS UP TRAINS",
        "UP TRAINS STATIONS", "DN TRAINS STATIONS",
    )
    for m in MARKERS:
        if v0 == m or v0.startswith(m):
            rest = [v.strip() for v in values[1:] if v.strip()]
            train_like = [
                v for v in rest
                if re.match(r'^[A-Z]{1,5}\s+\d{4,6}', v.upper())
                or re.match(r'^\d{4,6}', v)
            ]
            return len(train_like) >= 1
    return False


def is_section_header_row(values: List[str]) -> bool:
    """
    Pure section dividers that do NOT contain train column data.
    e.g. repeated timetable title rows, "Trans Harbour Line…", "W.e.f…"
    """
    if not values or not values[0]:
        return False
    v0 = values[0].strip()
    v0u = v0.upper()

    # Combined headers are handled separately — don't double-trigger
    if is_combined_section_and_train_header(values):
        return False

    PURE_MARKERS = (
        "TRANS HARBOUR LINE", "HARBOUR (MUMBAI",
        "W.E.F", "PUBLIC TIME TABLE",
    )
    for m in PURE_MARKERS:
        if m in v0u:
            return True

    # Repeated pandas-dedup title: "Title", "Title.1", "Title.2", …
    non_empty = [v.strip() for v in values if v.strip()]
    if len(non_empty) >= 2:
        base = re.sub(r'\.\d+$', '', non_empty[0].strip())
        if len(base) > 10 and all(
            re.sub(r'\.\d+$', '', v.strip()) == base
            for v in non_empty
        ):
            return True

    return False


def is_train_header_row(values: List[str]) -> bool:
    """
    Detect a standalone train-header row (separate from section header).
    e.g. "Train No. Train Code, 99001 Thane…, 99003 Thane…"
    Also handles Trans-Harbour "TR.NO TR.CODE" style.
    """
    if not values or not values[0]:
        return False

    # Already captured by combined check
    if is_combined_section_and_train_header(values):
        return False

    v0 = values[0].strip().upper()
    if v0 in ("TRAIN NO. TRAIN CODE", "TR.NO TR.CODE", "TRAIN NO TRAIN CODE"):
        return True

    # Row where ≥50 % of non-empty non-first cells look like train numbers
    non_empty = [v.strip() for v in values[1:] if v.strip()]
    if non_empty:
        train_like = sum(
            1 for v in non_empty
            if re.match(r'^\d{4,6}', v)
            or re.match(r'^[A-Z]{1,5}\s+\d{4,6}', v.upper())
        )
        if train_like >= max(1, len(non_empty) * 0.5):
            return True
    return False


# ===========================================================================
# TRAIN COLUMN HEADER PARSER
# ===========================================================================
def parse_train_columns(values: List[str]) -> List[Tuple[int, str]]:
    """
    From a header row, return list of (col_index, raw_header) for every
    column that represents a train service.
    Skips: empty, the station-label column (index 0 label), "12 CAR", etc.
    """
    result: List[Tuple[int, str]] = []
    for i, v in enumerate(values):
        v_raw = v.strip()
        if not v_raw:
            continue
        # Remove pandas dedup suffix
        v_clean = re.sub(r'\.\d+$', '', v_raw).strip()
        v_up = v_clean.upper()

        # Skip the station-label column at index 0 (or index 0+1 in file 50)
        if i == 0:
            continue

        # Skip generic car-count headers like "12 CAR", "15 CAR"
        if re.match(r'^\d+ CAR$', v_up):
            continue
        # Skip blanks / junk after cleanup
        if not v_clean:
            continue
        # Skip section-marker labels
        if v_up in _SKIP_EXACT_UPPER:
            continue

        # Accept: starts with 4-6 digits  (e.g. "99001 Thane…", "93001 VR DRD")
        if re.match(r'^\d{4,6}', v_clean):
            result.append((i, v_clean))
            continue

        # Accept: dest-code + 5-digit number  (e.g. "BSR 90065", "VR 92017")
        if re.match(r'^[A-Z]{1,5}\s+\d{4,6}', v_up):
            result.append((i, v_clean))
            continue

    return result


# ===========================================================================
# MAIN CSV PARSER
# ===========================================================================
def parse_csv_file(filepath: Path) -> List[dict]:
    """
    Parse one timetable CSV.  Returns a list of trip dicts:
    {
      'train_number': str,
      'train_name':   str,
      'line_key':     str,
      'route_code':   str,
      'route_name':   str,
      'direction':    str,   # 'DN' | 'UP' | ''
      'service':      (mon, tue, wed, thu, fri, sat, sun),
      'stops': [{'station': str, 'time': str, 'sequence': int}, …]
    }
    """
    results: List[dict] = []

    try:
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            raw_rows = list(csv.reader(f))
    except Exception as e:
        log.warning(f"Could not read {filepath.name}: {e}")
        return results

    if not raw_rows:
        return results

    # ── State machine ────────────────────────────────────────────────────────
    current_direction: str = ""
    current_train_cols: List[Tuple[int, str]] = []
    current_data: Dict[int, List[Tuple[str, str]]] = {}
    in_data_section: bool = False

    def flush_section() -> None:
        nonlocal current_train_cols, current_data, in_data_section
        for col_idx, header_raw in current_train_cols:
            stops_raw = current_data.get(col_idx, [])
            valid = [(s, t) for s, t in stops_raw if is_valid_time(t)]
            if len(valid) < 2:
                continue
            train_num = extract_train_number(header_raw)
            line_key, route_code, route_name = infer_line(train_num)
            svc = extract_service_flags(header_raw)
            results.append({
                'train_number': train_num,
                'train_name':   header_raw,
                'line_key':     line_key,
                'route_code':   route_code,
                'route_name':   route_name,
                'direction':    current_direction,
                'service':      svc,
                'stops': [
                    {'station': s, 'time': normalise_time(t), 'sequence': seq}
                    for seq, (s, t) in enumerate(valid, start=1)
                ],
            })
        current_train_cols.clear()
        current_data.clear()
        in_data_section = False

    def start_train_section(values: List[str], direction: str) -> None:
        nonlocal current_direction, current_train_cols, current_data, in_data_section
        flush_section()
        current_direction = direction
        current_train_cols = parse_train_columns(values)
        current_data = {col: [] for col, _ in current_train_cols}
        in_data_section = True

    def detect_direction(values: List[str]) -> str:
        combined = " ".join(values).upper()
        if "DN TRAINS" in combined or " DN " in combined:
            return "DN"
        if "UP TRAINS" in combined or " UP " in combined:
            return "UP"
        return current_direction   # keep previous

    # ── Process each row ─────────────────────────────────────────────────────
    for row in raw_rows:
        values = [str(v).strip() for v in row]

        if is_blank_or_annotation_row(values):
            continue

        # Priority 1: combined section+train header (Western Railway style)
        if is_combined_section_and_train_header(values):
            direction = detect_direction(values)
            start_train_section(values, direction)
            continue

        # Priority 2: pure section separator (no train columns)
        if is_section_header_row(values):
            flush_section()
            combined = " ".join(values).upper()
            if "DN TRAINS" in combined or " DN " in combined:
                current_direction = "DN"
            elif "UP TRAINS" in combined or " UP " in combined:
                current_direction = "UP"
            continue

        # Priority 3: standalone train-header row
        if is_train_header_row(values):
            direction = detect_direction(values)
            start_train_section(values, direction)
            continue

        # Priority 4: data row (station + times)
        if in_data_section and current_train_cols:
            # File 50 has station name repeated in col 0 and col 1
            station_raw = values[0] if values else ""
            station = normalise_station_name(station_raw)
            if not station:
                # Try col 1 (File-50 style)
                station = normalise_station_name(values[1]) if len(values) > 1 else ""
            if not station:
                continue

            for col_idx, _ in current_train_cols:
                if col_idx < len(values):
                    t = values[col_idx].strip()
                    if t and is_valid_time(t):
                        current_data[col_idx].append((station, t))

    flush_section()
    return results


# ===========================================================================
# DATABASE IMPORT
# ===========================================================================
def run_import(data_dir: Path, dry_run: bool, reset_trains: bool) -> None:

    from database import SessionLocal, Base, engine
    import models
    from schema_migrate import ensure_ticket_schema, ensure_gtfs_schema

    # ── Schema migration ──────────────────────────────────────────────────────
    log.info("Applying schema migrations...")
    Base.metadata.create_all(bind=engine)
    ensure_ticket_schema()
    ensure_gtfs_schema()
    log.info("Schema migrations: OK")

    db = SessionLocal()

    stats = {
        'files_processed':     0,
        'trips_parsed':        0,
        'routes_inserted':     0,
        'trips_inserted':      0,
        'stops_inserted':      0,
        'stops_reused':        0,
        'stop_times_inserted': 0,
        'duplicates_skipped':  0,
        'invalid_skipped':     0,
        'errors':              0,
    }

    try:
        # ── Optional reset (train data only) ──────────────────────────────────
        if reset_trains and not dry_run:
            log.info("[RESET] Deleting previous train stop_times...")
            db.query(models.StopTime).filter(
                models.StopTime.trip_id.in_(
                    db.query(models.Trip.id)
                    .join(models.Route)
                    .filter(models.Route.mode == 'train')
                    .scalar_subquery()
                )
            ).delete(synchronize_session=False)

            log.info("[RESET] Deleting previous train trips...")
            db.query(models.Trip).filter(
                models.Trip.route_id.in_(
                    db.query(models.Route.id)
                    .filter(models.Route.mode == 'train')
                    .scalar_subquery()
                )
            ).delete(synchronize_session=False)

            log.info("[RESET] Deleting previous train routes...")
            db.query(models.Route).filter(models.Route.mode == 'train').delete(
                synchronize_session=False)

            log.info("[RESET] Deleting previous train stops...")
            db.query(models.Stop).filter(models.Stop.mode == 'train').delete(
                synchronize_session=False)

            db.commit()
            log.info("[RESET] Done.\n")

        # ── Ensure Mumbai city ────────────────────────────────────────────────
        city = db.query(models.City).filter(models.City.slug == "mumbai").first()
        if not city:
            city = models.City(
                name="Mumbai", slug="mumbai",
                state="Maharashtra", country="India",
                center_lat=19.0760, center_lon=72.8777, is_active=True,
            )
            if not dry_run:
                db.add(city)
                db.commit()
                db.refresh(city)
            log.info("Created Mumbai city record.")
        city_id = city.id if not dry_run else 0

        # ── Ensure train operator ─────────────────────────────────────────────
        operator = (
            db.query(models.Operator)
            .filter(models.Operator.city_id == city_id,
                    models.Operator.mode == 'train')
            .first()
        )
        if not operator:
            operator = models.Operator(
                city_id=city_id,
                name="CR / WR Mumbai Suburban",
                short_name="CR/WR",
                mode="train",
                color_hex="#E60000",
                is_active=True,
            )
            if not dry_run:
                db.add(operator)
                db.commit()
                db.refresh(operator)
            log.info("Created train operator.")
        operator_id = operator.id if not dry_run else 0

        # ── Service calendar entries ───────────────────────────────────────────
        SVC_ALL   = "TRAIN_ALL_DAYS"
        SVC_NOSUN = "TRAIN_NO_SUNDAY"
        for svc_id, run_sun in ((SVC_ALL, True), (SVC_NOSUN, False)):
            if not db.query(models.ServiceCalendar).filter_by(service_id=svc_id).first():
                svc = models.ServiceCalendar(
                    service_id=svc_id,
                    monday=True, tuesday=True, wednesday=True,
                    thursday=True, friday=True, saturday=True,
                    sunday=run_sun,
                    start_date=date(2024, 1, 1),
                    end_date=date(2026, 12, 31),
                )
                if not dry_run:
                    db.add(svc)
                    db.commit()
            log.info(f"Service calendar '{svc_id}' ready.")

        # ── In-memory caches (avoid repeated DB round-trips) ───────────────────
        stop_cache:  Dict[str, int] = {}
        route_cache: Dict[str, int] = {}
        trip_cache:  Dict[str, int] = {}
        st_dedup:    Set[Tuple[int, int, int]] = set()

        if not dry_run:
            stop_cache = {
                s.stop_code: s.id
                for s in db.query(models.Stop)
                .filter(models.Stop.mode == 'train').all()
            }
            route_cache = {
                r.route_code: r.id
                for r in db.query(models.Route)
                .filter(models.Route.mode == 'train').all()
            }
            trip_cache = {
                t.trip_code: t.id
                for t in db.query(models.Trip)
                .join(models.Route)
                .filter(models.Route.mode == 'train').all()
            }

        log.info(
            f"Caches loaded: {len(stop_cache)} stops, "
            f"{len(route_cache)} routes, {len(trip_cache)} trips."
        )

        # ── Find and parse all CSV files ──────────────────────────────────────
        csv_files = sorted(
            data_dir.glob("Table - *.csv"),
            key=lambda p: int(re.search(r'\d+', p.stem).group()),
        )
        if not csv_files:
            log.error(f"No 'Table - *.csv' files found in {data_dir}")
            return

        log.info(f"Found {len(csv_files)} CSV files.\n")

        all_trips: List[dict] = []
        for csv_path in csv_files:
            parsed = parse_csv_file(csv_path)
            all_trips.extend(parsed)
            stats['files_processed'] += 1
            log.info(
                f"  [{stats['files_processed']:02d}/{len(csv_files)}] "
                f"{csv_path.name}: {len(parsed)} services"
            )

        stats['trips_parsed'] = len(all_trips)
        log.info(f"\nTotal parsed: {stats['trips_parsed']} train services\n")

        # ── Write to DB ───────────────────────────────────────────────────────
        log.info("Writing to database...")

        for trip_data in all_trips:
            train_number = trip_data['train_number']
            train_name   = trip_data['train_name']
            route_code   = trip_data['route_code']
            route_name   = trip_data['route_name']
            direction    = trip_data['direction']
            service_flags = trip_data['service']
            stops        = trip_data['stops']

            if len(stops) < 2:
                stats['invalid_skipped'] += 1
                continue

            # service_id
            service_id = SVC_NOSUN if not service_flags[6] else SVC_ALL

            # ── Route (get or create) ─────────────────────────────────────────
            if route_code not in route_cache:
                if not dry_run:
                    r = models.Route(
                        city_id=city_id, operator_id=operator_id,
                        route_code=route_code, name=route_name,
                        mode='train', color_hex='#E60000', is_active=True,
                    )
                    db.add(r)
                    db.flush()
                    route_cache[route_code] = r.id
                else:
                    route_cache[route_code] = -(len(route_cache) + 1)
                stats['routes_inserted'] += 1

            route_id = route_cache[route_code]

            # ── Trip (get or create) ──────────────────────────────────────────
            trip_code = f"TRAIN_{train_number}"
            if trip_code in trip_cache:
                stats['duplicates_skipped'] += 1
                continue

            if not dry_run:
                t = models.Trip(
                    route_id=route_id, service_id=service_id,
                    direction=direction,
                    trip_short_name=train_name[:200],
                    trip_code=trip_code,
                )
                db.add(t)
                db.flush()
                trip_id = t.id
            else:
                trip_id = -(len(trip_cache) + 1)
            trip_cache[trip_code] = trip_id
            stats['trips_inserted'] += 1

            # ── Stops & stop_times ────────────────────────────────────────────
            for stop_info in stops:
                station = stop_info['station'].strip()
                if not station:
                    continue
                time_str = stop_info['time']
                seq      = stop_info['sequence']
                scode    = station_stop_code(station)

                # get or create stop
                if scode not in stop_cache:
                    lat, lon = STATION_COORDS.get(station, (0.0, 0.0))
                    if lat == 0.0:
                        for known, coords in STATION_COORDS.items():
                            if (known.upper() in station.upper() or
                                    station.upper() in known.upper()):
                                lat, lon = coords
                                break
                    if lat == 0.0:
                        lat, lon = 19.0760, 72.8777   # Mumbai fallback

                    if not dry_run:
                        s = models.Stop(
                            city_id=city_id, operator_id=operator_id,
                            stop_code=scode, name=station,
                            lat=lat, lon=lon,
                            mode='train', is_active=True,
                            is_interchange=False,
                            wheelchair=False, platform_count=2,
                        )
                        db.add(s)
                        db.flush()
                        stop_cache[scode] = s.id
                    else:
                        stop_cache[scode] = -(len(stop_cache) + 1)
                    stats['stops_inserted'] += 1
                else:
                    stats['stops_reused'] += 1

                stop_id = stop_cache[scode]

                # dedup stop_time
                if trip_id > 0 and stop_id > 0:
                    key = (trip_id, stop_id, seq)
                    if key in st_dedup:
                        stats['duplicates_skipped'] += 1
                        continue
                    st_dedup.add(key)

                if not dry_run and trip_id > 0 and stop_id > 0:
                    db.add(models.StopTime(
                        trip_id=trip_id, stop_id=stop_id,
                        stop_sequence=seq,
                        arrival_time=time_str,
                        departure_time=time_str,
                        pickup_type=0, drop_type=0,
                    ))
                    stats['stop_times_inserted'] += 1

            # Commit in batches
            if not dry_run and stats['trips_inserted'] % 200 == 0:
                db.commit()

        if not dry_run:
            db.commit()
            log.info("Final commit done.")

    except Exception as e:
        log.error(f"Import failed: {e}", exc_info=True)
        if not dry_run:
            db.rollback()
        stats['errors'] += 1
    finally:
        db.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 62)
    print("  WAY TRANSIT — TRAIN IMPORT SUMMARY")
    print("=" * 62)
    print(f"  Mode:                     {'DRY RUN (no writes)' if dry_run else 'LIVE'}")
    print(f"  Files processed:          {stats['files_processed']}")
    print(f"  Train services parsed:    {stats['trips_parsed']}")
    print(f"  Routes inserted:          {stats['routes_inserted']}")
    print(f"  Trips inserted:           {stats['trips_inserted']}")
    print(f"  Train stations inserted:  {stats['stops_inserted']}")
    print(f"  Existing stations reused: {stats['stops_reused']}")
    print(f"  Stop_times inserted:      {stats['stop_times_inserted']}")
    print(f"  Duplicates skipped:       {stats['duplicates_skipped']}")
    print(f"  Invalid rows skipped:     {stats['invalid_skipped']}")
    print(f"  Errors:                   {stats['errors']}")
    print("=" * 62)
    if stats['errors'] == 0:
        print("  ✅  COMPLETE")
    else:
        print("  ⚠️   COMPLETED WITH ERRORS — check logs above.")
    print("=" * 62)
    print()


# ===========================================================================
# CLI
# ===========================================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="WAY TRANSIT — Mumbai Train Timetable Importer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--data-dir", type=Path, default=_BACKEND / "data",
        help="Directory with Table - 1.csv … Table - 54.csv  (default: backend/data)",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Parse and count without writing to the database.",
    )
    p.add_argument(
        "--reset-trains", action="store_true",
        help=(
            "DELETE all existing mode='train' data before importing. "
            "Bus and Metro data are NEVER touched."
        ),
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = args.data_dir.resolve()

    print()
    print("=" * 62)
    print("  WAY TRANSIT — MUMBAI TRAIN TIMETABLE IMPORTER")
    print("=" * 62)
    print(f"  Data directory : {data_dir}")
    print(f"  Dry run        : {args.dry_run}")
    print(f"  Reset trains   : {args.reset_trains}")
    print()

    if not data_dir.exists():
        print(f"  ERROR: Directory not found: {data_dir}")
        return 1

    if args.reset_trains and not args.dry_run:
        print("  ⚠️  --reset-trains will DELETE all mode='train' data.")
        print("     Bus / Metro data is NOT affected.")
        print("  Press Enter to continue, Ctrl-C to abort...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\n  Aborted.")
            return 1

    run_import(data_dir=data_dir, dry_run=args.dry_run, reset_trains=args.reset_trains)
    return 0


if __name__ == "__main__":
    sys.exit(main())
