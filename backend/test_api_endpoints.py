"""
Tests the search API endpoint logic directly by calling the FastAPI
route functions, bypassing HTTP — same code path as a real request.
"""
from database import SessionLocal
import schemas
import models
from routes.search import search_stops, search_trips
from unittest.mock import MagicMock

db = SessionLocal()
errors = []

def check(label, cond, detail=""):
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        errors.append(label)

# ── Test 1: search_stops autocomplete ─────────────────────────────────────
print("\n=== 1. search_stops: 'kalyan' ===")
stops = search_stops(q="kalyan", mode=None, limit=10, db=db)
print(f"  Results: {[(s.id, s.name, s.mode) for s in stops]}")
train_stop = next((s for s in stops if s.mode == 'train'), None)
check("kalyan autocomplete finds train stop", train_stop is not None)
check("result has id/name/mode", train_stop and train_stop.id and train_stop.name)

print("\n=== 2. search_stops: 'csmt' ===")
stops2 = search_stops(q="csmt", mode=None, limit=10, db=db)
print(f"  Results: {[(s.id, s.name, s.mode) for s in stops2]}")
csmt_stop = next((s for s in stops2 if s.mode == 'train'), None)
check("csmt autocomplete finds train stop", csmt_stop is not None)

print("\n=== 3. search_stops: mode filter train only ===")
stops3 = search_stops(q="kalyan", mode="train", limit=10, db=db)
print(f"  Results: {[(s.id, s.name, s.mode) for s in stops3]}")
check("all results are mode=train", all(s.mode == 'train' for s in stops3))
check("Kalyan appears in train-filtered results",
      any(s.name == 'Kalyan' for s in stops3))

print("\n=== 4. search_stops: empty query ===")
stops4 = search_stops(q="", mode=None, limit=10, db=db)
check("empty query returns []", stops4 == [])

print("\n=== 5. search_trips: Kalyan → CSMT ===")
if train_stop and csmt_stop:
    req = schemas.TripSearchRequest(
        source_stop_id=train_stop.id,
        destination_stop_id=csmt_stop.id,
    )
    resp = search_trips(body=req, db=db)
    print(f"  success={resp.success}  message={resp.message!r}")
    print(f"  result count: {len(resp.results)}")
    check("success=True", resp.success)
    check("results not empty", len(resp.results) > 0,
          f"got {len(resp.results)}")
    if resp.results:
        r = resp.results[0]
        print(f"  First result: trip_id={r.trip_id} name={r.trip_name!r}")
        print(f"    dep={r.source.departure_time} arr={r.destination.arrival_time}")
        print(f"    src_seq={r.source.stop_sequence} dst_seq={r.destination.stop_sequence}")
        check("source stop is Kalyan", r.source.name == 'Kalyan',
              f"got {r.source.name!r}")
        check("destination stop is CSMT", r.destination.name == 'CSMT',
              f"got {r.destination.name!r}")
        check("src_seq < dst_seq",
              r.source.stop_sequence < r.destination.stop_sequence,
              f"{r.source.stop_sequence} vs {r.destination.stop_sequence}")
        check("mode=train", r.mode == 'train', f"got {r.mode!r}")
        check("operator_name present", r.operator_name is not None)
        check("departure_time present", bool(r.source.departure_time))
        check("arrival_time present", bool(r.destination.arrival_time))
else:
    print("  SKIP: stops not found in autocomplete")

print("\n=== 6. search_trips: CSMT → Kalyan (reverse) ===")
if train_stop and csmt_stop:
    req_rev = schemas.TripSearchRequest(
        source_stop_id=csmt_stop.id,
        destination_stop_id=train_stop.id,
    )
    resp_rev = search_trips(body=req_rev, db=db)
    print(f"  result count: {len(resp_rev.results)}")
    check("CSMT→Kalyan returns results", len(resp_rev.results) > 0)
    if resp_rev.results:
        r2 = resp_rev.results[0]
        check("src_seq < dst_seq (reverse)",
              r2.source.stop_sequence < r2.destination.stop_sequence)

print("\n=== 7. search_trips: same stop (should raise 400) ===")
if train_stop:
    from fastapi import HTTPException
    raised = False
    try:
        search_trips(
            body=schemas.TripSearchRequest(
                source_stop_id=train_stop.id,
                destination_stop_id=train_stop.id,
            ),
            db=db,
        )
    except HTTPException as e:
        raised = True
        check("same-stop raises HTTP 400", e.status_code == 400,
              f"got {e.status_code}")
    check("exception was raised", raised)

print("\n=== 8. search_trips: invalid stop id ===")
from fastapi import HTTPException as FHE
try:
    search_trips(
        body=schemas.TripSearchRequest(source_stop_id=999999, destination_stop_id=999998),
        db=db,
    )
    check("invalid id raises 404", False, "no exception raised")
except FHE as e:
    check("invalid id raises 404", e.status_code == 404, f"got {e.status_code}")

print("\n=== 9. search_trips: no direct service ===")
# Andheri (train) → Kalyan Fata (bus) — cross-mode, should return clean empty
andheri = db.query(models.Stop).filter(
    models.Stop.name == 'Andheri', models.Stop.mode == 'train'
).first()
kalyan_fata_bus = db.query(models.Stop).filter(
    models.Stop.name.ilike('%kalyan fata%'), models.Stop.mode.ilike('%bus%')
).first()
if andheri and kalyan_fata_bus:
    resp9 = search_trips(
        body=schemas.TripSearchRequest(
            source_stop_id=andheri.id,
            destination_stop_id=kalyan_fata_bus.id,
        ),
        db=db,
    )
    print(f"  message={resp9.message!r}")
    check("cross-mode returns success=True with empty results",
          resp9.success and len(resp9.results) == 0)
else:
    print("  SKIP (stops not found)")

print("\n=== 10. search_trips: Kalyan → Dombivli ===")
dombivli = db.query(models.Stop).filter(
    models.Stop.name == 'Dombivli', models.Stop.mode == 'train'
).first()
if train_stop and dombivli:
    resp10 = search_trips(
        body=schemas.TripSearchRequest(
            source_stop_id=train_stop.id,
            destination_stop_id=dombivli.id,
        ),
        db=db,
    )
    print(f"  result count: {len(resp10.results)}")
    check("Kalyan→Dombivli returns trips", len(resp10.results) > 0)
else:
    print("  SKIP (stops not found)")

db.close()

print("\n=== SUMMARY ===")
if errors:
    print(f"FAILED ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
    import sys; sys.exit(1)
else:
    print(f"ALL TESTS PASSED")
