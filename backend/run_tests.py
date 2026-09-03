"""Endpoint integration tests — run with: python run_tests.py"""
import sys, os
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from routes.search import router
from fastapi import FastAPI

app2 = FastAPI()
app2.include_router(router)
client = TestClient(app2)

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
errors = 0

def check(label, condition, detail=""):
    global errors
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} FAIL: {label}  {detail}")
        errors += 1

print("\n=== GET /search/stops ===")
r = client.get("/search/stops?q=Thane&mode=train")
check("status 200", r.status_code == 200)
d = r.json()
check("returns list", isinstance(d, list))
check("has results", len(d) > 0)
thane = d[0]
check("has id", "id" in thane)
check("has stop_code", "stop_code" in thane)
check("has name", thane.get("name") == "Thane")
check("mode=train", thane.get("mode") == "train")
check("has operator_id", "operator_id" in thane)
thane_id = thane["id"]

r2 = client.get("/search/stops?q=Panvel&mode=train")
panvel = r2.json()[0]
panvel_id = panvel["id"]
check("Panvel found", panvel.get("name") == "Panvel")

# Partial search
rp = client.get("/search/stops?q=Tha")
check("partial 'Tha' finds results", len(rp.json()) > 0)

# Empty query
re_ = client.get("/search/stops?q=")
check("empty q returns []", re_.json() == [])

print("\n=== POST /search/trips — Thane → Panvel ===")
r3 = client.post("/search/trips", json={"source_stop_id": thane_id, "destination_stop_id": panvel_id})
check("status 200", r3.status_code == 200)
j3 = r3.json()
check("success=true", j3.get("success") is True)
check("has results", len(j3["results"]) > 0, f"got {len(j3['results'])}")
t = j3["results"][0]
check("has trip_code", "trip_code" in t)
check("has trip_name", "trip_name" in t)
check("has source", "source" in t)
check("has destination", "destination" in t)
check("src dep_time present", t["source"]["departure_time"] != "")
check("dst arr_time present", t["destination"]["arrival_time"] != "")
check("src_seq < dst_seq", t["source"]["stop_sequence"] < t["destination"]["stop_sequence"],
      f"{t['source']['stop_sequence']} vs {t['destination']['stop_sequence']}")
fwd_trips = {x["trip_code"] for x in j3["results"]}

print("\n=== POST /search/trips — Panvel → Thane (reverse) ===")
r4 = client.post("/search/trips", json={"source_stop_id": panvel_id, "destination_stop_id": thane_id})
check("status 200", r4.status_code == 200)
j4 = r4.json()
check("has results", len(j4["results"]) > 0)
rev_trips = {x["trip_code"] for x in j4["results"]}
check("reverse trips differ from forward", fwd_trips != rev_trips,
      f"fwd={list(fwd_trips)[:2]} rev={list(rev_trips)[:2]}")
t4 = j4["results"][0]
check("src_seq < dst_seq (reverse)", t4["source"]["stop_sequence"] < t4["destination"]["stop_sequence"])

print("\n=== POST /search/trips — Same station ===")
r5 = client.post("/search/trips", json={"source_stop_id": thane_id, "destination_stop_id": thane_id})
check("status 400", r5.status_code == 400)

print("\n=== POST /search/trips — Non-existent stop ===")
r6 = client.post("/search/trips", json={"source_stop_id": 99999, "destination_stop_id": panvel_id})
check("status 404", r6.status_code == 404)

print("\n=== POST /search/trips — No direct route ===")
# Dockyard Road (Harbour Line) → Thane (Trans Harbour) — no direct service
rdr = client.get("/search/stops?q=Dockyard")
if rdr.json():
    dock_id = rdr.json()[0]["id"]
    r7 = client.post("/search/trips", json={"source_stop_id": dock_id, "destination_stop_id": thane_id})
    check("status 200", r7.status_code == 200)
    j7 = r7.json()
    check("success=true", j7.get("success") is True)
    check("results=[]", len(j7["results"]) == 0)
    check("has message", len(j7.get("message", "")) > 0)

print("\n=== Bus data untouched ===")
from database import SessionLocal
import models
db = SessionLocal()
bus_count = db.query(models.Stop).filter_by(mode="bus").count()
train_count = db.query(models.Stop).filter_by(mode="train").count()
db.close()
check("bus stops intact (>0)", bus_count > 0, f"got {bus_count}")
check("train stops = 124", train_count == 124, f"got {train_count}")

print(f"\n{'='*40}")
if errors == 0:
    print(f"\033[92mALL TESTS PASSED\033[0m")
else:
    print(f"\033[91m{errors} TEST(S) FAILED\033[0m")
print('='*40)
sys.exit(errors)
