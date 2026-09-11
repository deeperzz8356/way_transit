"""
Direct tests of search logic without importing main.py or RAG.
Tests the exact same SQL/ORM logic used by the API endpoints.
"""
from database import SessionLocal
from sqlalchemy import text
from sqlalchemy.orm import aliased
import models
import schemas
import sys

db = SessionLocal()
errors = []

def check(label, cond, detail=""):
    symbol = "PASS" if cond else "FAIL"
    print(f"  {symbol}  {label}" + (f"  [{detail}]" if detail else ""))
    if not cond:
        errors.append(label)

# ── Replicate search_stops logic ──────────────────────────────────────────
def do_search_stops(q, mode=None, limit=10):
    q = (q or "").strip()
    if not q:
        return []
    query = (
        db.query(models.Stop)
        .filter(models.Stop.name.ilike(f"%{q}%"))
        .filter(models.Stop.is_active == True)
    )
    if mode:
        query = query.filter(models.Stop.mode == mode.lower())
    return query.order_by(models.Stop.name).limit(max(1, min(limit, 50))).all()

# ── Replicate search_trips logic ──────────────────────────────────────────
def do_search_trips(src_id, dst_id, mode=None):
    src_stop = db.query(models.Stop).filter(models.Stop.id == src_id).first()
    dst_stop = db.query(models.Stop).filter(models.Stop.id == dst_id).first()
    if not src_stop or not dst_stop:
        return None, "stop not found"

    if src_stop.mode and dst_stop.mode and src_stop.mode != dst_stop.mode:
        return [], f"cross-mode: {src_stop.mode} vs {dst_stop.mode}"

    effective_mode = mode or src_stop.mode or dst_stop.mode
    StopTimeSrc = aliased(models.StopTime, name="st_src")
    StopTimeDst = aliased(models.StopTime, name="st_dst")

    q = (
        db.query(models.Trip, StopTimeSrc, StopTimeDst)
        .join(StopTimeSrc, StopTimeSrc.trip_id == models.Trip.id)
        .join(StopTimeDst, StopTimeDst.trip_id == models.Trip.id)
        .join(models.Route, models.Route.id == models.Trip.route_id)
        .filter(
            StopTimeSrc.stop_id == src_id,
            StopTimeDst.stop_id == dst_id,
            StopTimeSrc.stop_sequence < StopTimeDst.stop_sequence,
        )
    )
    if effective_mode:
        q = q.filter(models.Route.mode == effective_mode)
    q = q.order_by(StopTimeSrc.departure_time)
    rows = q.all()
    return rows, f"{len(rows)} rows"

print("\n=== 1. Autocomplete 'kalyan' ===")
stops = do_search_stops("kalyan")
print(f"  {[(s.id, s.name, s.mode) for s in stops[:5]]}")
kalyan = next((s for s in stops if s.mode == 'train' and s.name == 'Kalyan'), None)
check("'kalyan' finds Kalyan train stop", kalyan is not None)

print("\n=== 2. Autocomplete 'csmt' ===")
stops2 = do_search_stops("csmt")
print(f"  {[(s.id, s.name, s.mode) for s in stops2[:5]]}")
csmt = next((s for s in stops2 if s.mode == 'train'), None)
check("'csmt' finds a train CSMT stop", csmt is not None)

print("\n=== 3. Autocomplete case-insensitive: 'KALY' ===")
stops3 = do_search_stops("KALY")
kalyan3 = next((s for s in stops3 if s.name == 'Kalyan'), None)
check("'KALY' (uppercase) still finds Kalyan", kalyan3 is not None)

print("\n=== 4. Autocomplete mode filter ===")
train_only = do_search_stops("kalyan", mode="train")
check("mode=train filter: all results are train",
      all(s.mode == 'train' for s in train_only),
      f"{[(s.name, s.mode) for s in train_only]}")

print("\n=== 5. Kalyan → CSMT trips ===")
if kalyan and csmt:
    rows, msg = do_search_trips(kalyan.id, csmt.id)
    print(f"  {msg}")
    check("returns results", rows is not None and len(rows) > 0, msg)
    if rows:
        trip, st_src, st_dst = rows[0]
        print(f"  First: trip={trip.trip_code!r} name={trip.trip_short_name!r}")
        print(f"    dep={st_src.departure_time}  arr={st_dst.arrival_time}")
        print(f"    src_seq={st_src.stop_sequence}  dst_seq={st_dst.stop_sequence}")
        check("src_seq < dst_seq", st_src.stop_sequence < st_dst.stop_sequence)
        check("all src_seq < dst_seq", all(r[1].stop_sequence < r[2].stop_sequence for r in rows))
        route = db.query(models.Route).filter(models.Route.id == trip.route_id).first()
        check("route mode=train", route and route.mode == 'train', f"got {route.mode if route else None}")
        operator = db.query(models.Operator).filter(models.Operator.id == route.operator_id).first() if route else None
        check("operator is CR/WR", operator and 'CR' in operator.name, f"got {operator.name if operator else None}")

print("\n=== 6. CSMT → Kalyan (reverse direction) ===")
if kalyan and csmt:
    rows_rev, msg = do_search_trips(csmt.id, kalyan.id)
    print(f"  {msg}")
    check("reverse direction has results", rows_rev and len(rows_rev) > 0, msg)
    if rows_rev:
        check("all reverse src_seq < dst_seq",
              all(r[1].stop_sequence < r[2].stop_sequence for r in rows_rev))

print("\n=== 7. Same stop returns no rows (API would 400) ===")
if kalyan:
    rows_same, _ = do_search_trips(kalyan.id, kalyan.id)
    check("same stop: 0 trips (seq< never true)", rows_same is not None and len(rows_same) == 0)

print("\n=== 8. Non-existent stop ===")
rows_bad, msg_bad = do_search_trips(999999, 999998)
check("non-existent stops: returns None", rows_bad is None, msg_bad)

print("\n=== 9. Cross-mode returns empty ===")
andheri_train = db.query(models.Stop).filter(
    models.Stop.name == 'Andheri', models.Stop.mode == 'train'
).first()
kalyan_fata_bus = db.query(models.Stop).filter(
    models.Stop.name.ilike('%kalyan fata%')
).first()
if andheri_train and kalyan_fata_bus:
    rows_cross, msg_cross = do_search_trips(andheri_train.id, kalyan_fata_bus.id)
    print(f"  msg={msg_cross!r}")
    check("cross-mode returns [] not None", isinstance(rows_cross, list) and len(rows_cross) == 0, msg_cross)

print("\n=== 10. Kalyan → Dombivli ===")
dombivli = db.query(models.Stop).filter(
    models.Stop.name == 'Dombivli', models.Stop.mode == 'train'
).first()
if kalyan and dombivli:
    rows_dom, msg_dom = do_search_trips(kalyan.id, dombivli.id)
    print(f"  {msg_dom}")
    check("Kalyan→Dombivli returns trips", rows_dom and len(rows_dom) > 0, msg_dom)
    if rows_dom:
        print(f"  First: dep={rows_dom[0][1].departure_time}  arr={rows_dom[0][2].arrival_time}")

print("\n=== 11. Autocomplete empty query ===")
empty = do_search_stops("")
check("empty query returns []", empty == [])

print("\n=== 12. Autocomplete non-existent station ===")
nope = do_search_stops("xyznonexistent999")
check("nonsense query returns []", nope == [])

db.close()

print("\n" + "="*50)
if errors:
    print(f"FAILED ({len(errors)}):")
    for e in errors: print(f"  - {e}")
    sys.exit(1)
else:
    print(f"ALL {12} TESTS PASSED")
