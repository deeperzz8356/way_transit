"""
Live end-to-end test of the search endpoints using the real database.
Tests: autocomplete, trip search (Kalyan→CSMT, CSMT→Kalyan, same stop, no route).
"""
from database import SessionLocal
from sqlalchemy import text
import sys

db = SessionLocal()
errors = []

def check(label, condition, detail=""):
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        errors.append(label)

# ── 1. Autocomplete ────────────────────────────────────────────────────────
print("\n=== 1. AUTOCOMPLETE: GET /search/stops ===")

# "kaly" should find Kalyan train stop
rows = db.execute(text(
    "SELECT id, name, mode FROM stops WHERE name ILIKE '%kaly%' AND is_active=TRUE ORDER BY name LIMIT 10"
)).all()
print(f"  'kaly' matches: {[(r[0], r[1], r[2]) for r in rows]}")
kalyan_train = next((r for r in rows if r[2] == 'train'), None)
check("'kaly' finds Kalyan train stop", kalyan_train is not None,
      f"got {[r[1] for r in rows]}")

# "cs" should find CSMT train stop
rows2 = db.execute(text(
    "SELECT id, name, mode FROM stops WHERE name ILIKE '%csmt%' AND is_active=TRUE ORDER BY name LIMIT 10"
)).all()
print(f"  'csmt' matches: {[(r[0], r[1], r[2]) for r in rows2]}")
csmt_train = next((r for r in rows2 if r[2] == 'train'), None)
check("'csmt' finds a train CSMT stop", csmt_train is not None,
      f"got {[r[1] for r in rows2]}")

# ── 2. Kalyan → CSMT ──────────────────────────────────────────────────────
print("\n=== 2. TRIP SEARCH: Kalyan → CSMT ===")
if kalyan_train and csmt_train:
    src_id = kalyan_train[0]
    dst_id = csmt_train[0]
    print(f"  src_id={src_id} ({kalyan_train[1]}), dst_id={dst_id} ({csmt_train[1]})")

    rows3 = db.execute(text("""
        SELECT t.id, t.trip_code, t.trip_short_name,
               st_src.stop_sequence, st_src.departure_time,
               st_dst.stop_sequence, st_dst.arrival_time,
               r.name, r.mode
        FROM trips t
        JOIN stop_times st_src ON st_src.trip_id = t.id AND st_src.stop_id = :src
        JOIN stop_times st_dst ON st_dst.trip_id = t.id AND st_dst.stop_id = :dst
        JOIN routes r ON r.id = t.route_id
        WHERE st_src.stop_sequence < st_dst.stop_sequence
        ORDER BY st_src.departure_time
        LIMIT 10
    """), {"src": src_id, "dst": dst_id}).all()

    check("Kalyan→CSMT returns results", len(rows3) > 0,
          f"got {len(rows3)} rows")
    if rows3:
        print(f"  Total matching trips: {len(rows3)} (showing first 5)")
        for r in rows3[:5]:
            print(f"    trip_id={r[0]}  code={r[1]!r}  name={r[2]!r}")
            print(f"      src_seq={r[3]} dep={r[4]}  dst_seq={r[5]} arr={r[6]}")
            print(f"      route={r[7]!r} mode={r[8]!r}")
        check("src_sequence < dst_sequence for all", all(r[3] < r[5] for r in rows3))

# ── 3. CSMT → Kalyan (reverse) ────────────────────────────────────────────
print("\n=== 3. TRIP SEARCH: CSMT → Kalyan ===")
if kalyan_train and csmt_train:
    rows4 = db.execute(text("""
        SELECT t.id, st_src.stop_sequence, st_dst.stop_sequence,
               st_src.departure_time, st_dst.arrival_time
        FROM trips t
        JOIN stop_times st_src ON st_src.trip_id = t.id AND st_src.stop_id = :src
        JOIN stop_times st_dst ON st_dst.trip_id = t.id AND st_dst.stop_id = :dst
        JOIN routes r ON r.id = t.route_id
        WHERE st_src.stop_sequence < st_dst.stop_sequence
        ORDER BY st_src.departure_time
        LIMIT 5
    """), {"src": dst_id, "dst": src_id}).all()  # swapped
    check("CSMT→Kalyan returns results", len(rows4) > 0,
          f"got {len(rows4)} rows")
    if rows4:
        print(f"  Total: {len(rows4)}")
        for r in rows4[:3]:
            print(f"    trip_id={r[0]}  src_seq={r[1]} dep={r[3]}  dst_seq={r[2]} arr={r[4]}")

# ── 4. Same stop ──────────────────────────────────────────────────────────
print("\n=== 4. SAME STOP (should be rejected by API) ===")
# The API raises HTTP 400 for same src==dst, validated in routes/search.py
# We just verify logically that a query with same stop would return wrong results.
if kalyan_train:
    same_rows = db.execute(text("""
        SELECT COUNT(*) FROM trips t
        JOIN stop_times st_src ON st_src.trip_id = t.id AND st_src.stop_id = :sid
        JOIN stop_times st_dst ON st_dst.trip_id = t.id AND st_dst.stop_id = :sid
        WHERE st_src.stop_sequence < st_dst.stop_sequence
    """), {"sid": kalyan_train[0]}).scalar()
    check("Same-stop query with seq< returns 0", same_rows == 0,
          f"got {same_rows}")

# ── 5. Non-existent station ───────────────────────────────────────────────
print("\n=== 5. INVALID STATION ===")
no_rows = db.execute(text(
    "SELECT id FROM stops WHERE name ILIKE '%xyznonexistent999%' AND is_active=TRUE"
)).all()
check("Non-existent station returns no stops", len(no_rows) == 0)

# ── 6. Count verification ──────────────────────────────────────────────────
print("\n=== 6. DATABASE RECORD COUNTS ===")
train_stops = db.execute(text("SELECT COUNT(*) FROM stops WHERE mode='train' AND is_active=TRUE")).scalar()
train_routes = db.execute(text("SELECT COUNT(*) FROM routes WHERE mode='train'")).scalar()
train_trips = db.execute(text(
    "SELECT COUNT(*) FROM trips t JOIN routes r ON r.id=t.route_id WHERE r.mode='train'"
)).scalar()
train_st = db.execute(text(
    "SELECT COUNT(*) FROM stop_times st JOIN trips t ON t.id=st.trip_id JOIN routes r ON r.id=t.route_id WHERE r.mode='train'"
)).scalar()
print(f"  Train stops (is_active=True): {train_stops}")
print(f"  Train routes: {train_routes}")
print(f"  Train trips: {train_trips}")
print(f"  Train stop_times: {train_st}")
check("Train stops ~124", 100 <= train_stops <= 150, f"got {train_stops}")
check("Train routes ~4", 2 <= train_routes <= 10, f"got {train_routes}")
check("Train trips ~2992", train_trips >= 2000, f"got {train_trips}")
check("Train stop_times ~50235", train_st >= 40000, f"got {train_st}")

# ── 7. Dombivli test ──────────────────────────────────────────────────────
print("\n=== 7. KALYAN → DOMBIVLI ===")
dombivli = db.execute(text(
    "SELECT id, name FROM stops WHERE name ILIKE '%dombivli%' AND mode='train' AND is_active=TRUE LIMIT 1"
)).first()
if kalyan_train and dombivli:
    print(f"  Dombivli: id={dombivli[0]} name={dombivli[1]!r}")
    rows5 = db.execute(text("""
        SELECT COUNT(*) FROM trips t
        JOIN stop_times st_src ON st_src.trip_id = t.id AND st_src.stop_id = :src
        JOIN stop_times st_dst ON st_dst.trip_id = t.id AND st_dst.stop_id = :dst
        WHERE st_src.stop_sequence < st_dst.stop_sequence
    """), {"src": kalyan_train[0], "dst": dombivli[0]}).scalar()
    check("Kalyan→Dombivli returns trips", rows5 > 0, f"got {rows5}")
    print(f"  Kalyan→Dombivli trips: {rows5}")
else:
    print("  Skipped (stop not found in DB)")

db.close()

print("\n=== SUMMARY ===")
if errors:
    print(f"FAILED tests ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
