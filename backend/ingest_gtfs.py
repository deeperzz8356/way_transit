import os
import pandas as pd
from datetime import date, datetime
from sqlalchemy import insert
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
import models

def init_tables():
    Base.metadata.create_all(bind=engine)

def get_mumbai_city(db: Session):
    city = db.query(models.City).filter(models.City.slug == "mumbai").first()
    if not city:
        city = models.City(
            name="Mumbai",
            slug="mumbai",
            state="Maharashtra",
            country="India",
            center_lat=19.0760,
            center_lon=72.8777
        )
        db.add(city)
        db.commit()
        db.refresh(city)
    return city

def get_operator(db: Session, city_id: int, name: str, mode: str):
    op = db.query(models.Operator).filter(
        models.Operator.city_id == city_id,
        models.Operator.name == name
    ).first()
    if not op:
        op = models.Operator(
            city_id=city_id,
            name=name,
            short_name=name[:5].upper(),
            mode=mode,
            color_hex="#8B9DFF"
        )
        db.add(op)
        db.commit()
        db.refresh(op)
    return op

def load_bus_calendar(db: Session, path: str):
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    records = []
    for _, row in df.iterrows():
        start = datetime.strptime(str(row["start_date"]), "%Y%m%d").date()
        end = datetime.strptime(str(row["end_date"]), "%Y%m%d").date()
        records.append({
            "service_id": str(row["service_id"]),
            "monday": int(row.get("monday", 1)) == 1,
            "tuesday": int(row.get("tuesday", 1)) == 1,
            "wednesday": int(row.get("wednesday", 1)) == 1,
            "thursday": int(row.get("thursday", 1)) == 1,
            "friday": int(row.get("friday", 1)) == 1,
            "saturday": int(row.get("saturday", 1)) == 1,
            "sunday": int(row.get("sunday", 1)) == 1,
            "start_date": start,
            "end_date": end
        )
    if records:
        db.execute(insert(models.ServiceCalendar), records)
        db.commit()
    return {str(r["service_id"]): str(r["service_id"]) for r in records}

def load_bus_stops(db: Session, path: str, city_id: int, operator_id: int):
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    records = []
    for _, row in df.iterrows():
        records.append({
            "city_id": city_id,
            "operator_id": operator_id,
            "stop_code": str(row["stop_id"]),
            "name": str(row["stop_name"]),
            "lat": float(row["stop_lat"]),
            "lon": float(row["stop_lon"]),
            "mode": "bus",
            "is_active": True
        })
    if records:
        db.execute(insert(models.Stop), records)
        db.commit()
    return {s.stop_code: s.id for s in db.query(models.Stop).filter(models.Stop.operator_id == operator_id).all()}

def load_bus_routes(db: Session, path: str, city_id: int, operator_id: int):
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    records = []
    for _, row in df.iterrows():
        records.append({
            "city_id": city_id,
            "operator_id": operator_id,
            "route_code": str(row["route_id"]),
            "name": str(row["route_long_name"]),
            "mode": "bus",
            "is_active": True
        })
    if records:
        db.execute(insert(models.Route), records)
        db.commit()
    return {r.route_code: r.id for r in db.query(models.Route).filter(models.Route.operator_id == operator_id).all()}

def load_bus_trips(db: Session, path: str, route_map: dict, service_map: dict):
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path)
    records = []
    for _, row in df.iterrows():
        r_id = route_map.get(str(row["route_id"]))
        s_id = service_map.get(str(row["service_id"]))
        if r_id and s_id:
            records.append({
                "route_id": r_id,
                "service_id": s_id,
                "direction": str(row.get("direction_id", "0")),
                "trip_short_name": str(row.get("trip_headsign", "")),
                "trip_code": str(row["trip_id"])
            })
    if records:
        # Batch insert trips
        for i in range(0, len(records), 20000):
            db.execute(insert(models.Trip), records[i:i+20000])
        db.commit()
    return {t.trip_code: t.id for t in db.query(models.Trip).all()}

def load_bus_stop_times(db: Session, path: str, trip_map: dict, stop_map: dict):
    if not os.path.exists(path):
        return
    for chunk in pd.read_csv(path, chunksize=50000):
        records = []
        for _, row in chunk.iterrows():
            t_id = trip_map.get(str(row["trip_id"]))
            s_id = stop_map.get(str(row["stop_id"]))
            if t_id and s_id:
                records.append({
                    "trip_id": t_id,
                    "stop_id": s_id,
                    "stop_sequence": int(row["stop_sequence"]),
                    "arrival_time": str(row["arrival_time"]),
                    "departure_time": str(row["departure_time"])
                })
        if records:
            db.execute(insert(models.StopTime), records)
            db.commit()

def load_metro_excel(db: Session, path: str, city_id: int, operator_id: int):
    if not os.path.exists(path):
        return
    xl = pd.ExcelFile(path)
    
    # 1. Calendar
    df_cal = xl.parse("calendar")
    cal_map = {}
    for _, row in df_cal.iterrows():
        start = datetime.strptime(str(int(row["start_date"])), "%Y%m%d").date()
        end = datetime.strptime(str(int(row["end_date"])), "%Y%m%d").date()
        sc = models.ServiceCalendar(
            service_id=str(row["service_id"]),
            monday=int(row["monday"]) == 1,
            tuesday=int(row["tuesday"]) == 1,
            wednesday=int(row["wednesday"]) == 1,
            thursday=int(row["thursday"]) == 1,
            friday=int(row["friday"]) == 1,
            saturday=int(row["saturday"]) == 1,
            sunday=int(row["sunday"]) == 1,
            start_date=start,
            end_date=end
        )
        db.add(sc)
        cal_map[str(row["service_id"])] = str(row["service_id"])
    db.commit()

    # 2. Stops
    df_stops = xl.parse("stops")
    stop_map = {}
    for _, row in df_stops.iterrows():
        stop = models.Stop(
            city_id=city_id,
            operator_id=operator_id,
            stop_code=str(row["stop_id"]),
            name=str(row["name"]),
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            mode="metro",
            is_active=True,         # required so GET /search/stops returns them
        )
        db.add(stop)
    db.commit()
    stop_map = {s.stop_code: s.id for s in db.query(models.Stop).filter(models.Stop.operator_id == operator_id).all()}

    # 3. Routes
    df_routes = xl.parse("routes")
    route_map = {}
    for _, row in df_routes.iterrows():
        route = models.Route(
            city_id=city_id,
            operator_id=operator_id,
            route_code=str(row["route_id"]),
            name=str(row["name"]),
            mode="metro",
            color_hex=str(row.get("color", "")),
            is_active=True,
        )
        db.add(route)
    db.commit()
    route_map = {r.route_code: r.id for r in db.query(models.Route).filter(models.Route.operator_id == operator_id).all()}

    # 4. Trips
    df_trips = xl.parse("trips")
    trip_map = {}
    for _, row in df_trips.iterrows():
        r_id = route_map.get(str(row["route_id"]))
        # Metro trips default to the single calendar record WD_WE_ALL
        s_id = "WD_WE_ALL"
        trip = models.Trip(
            route_id=r_id,
            service_id=s_id,
            direction="0" if str(row.get("direction")) == "UP" else "1",
            trip_short_name=str(row.get("trip_id")),
            trip_code=str(row["trip_id"])
        )
        db.add(trip)
    db.commit()
    trip_map = {t.trip_code: t.id for t in db.query(models.Trip).filter(models.Trip.route.has(operator_id=operator_id)).all()}

    # 5. Stop Times
    df_st = xl.parse("stop_times")
    records_st = []
    for _, row in df_st.iterrows():
        t_id = trip_map.get(str(row["trip_id"]))
        s_id = stop_map.get(str(row["stop_id"]))
        if t_id and s_id:
            records_st.append({
                "trip_id": t_id,
                "stop_id": s_id,
                "stop_sequence": int(row["sequence"]),
                "arrival_time": str(row["arrival_time"]),
                "departure_time": str(row["departure_time"])
            })
    if records_st:
        db.execute(insert(models.StopTime), records_st)
        db.commit()

    # 6. Fare Matrix
    df_fare = xl.parse("fare_rules")
    records_fare = []
    for _, row in df_fare.iterrows():
        o_id = stop_map.get(str(row["origin_stop"]))
        d_id = stop_map.get(str(row["destination_stop"]))
        if o_id and d_id:
            records_fare.append({
                "from_stop_id": o_id,
                "to_stop_id": d_id,
                "price": float(row["price"])
            })
    if records_fare:
        db.execute(insert(models.FareMatrix), records_fare)
        db.commit()

def clear_db(db: Session):
    # Truncate tables for fresh seed
    db.query(models.FareMatrix).delete()
    db.query(models.StopTime).delete()
    db.query(models.Trip).delete()
    db.query(models.Route).delete()
    db.query(models.Stop).delete()
    db.query(models.ServiceCalendar).delete()
    db.query(models.Operator).delete()
    db.query(models.City).delete()
    db.commit()

def main():
    print("Using DB URL:", engine.url)
    init_tables()
    db = SessionLocal()
    try:
        clear_db(db)
        city = get_mumbai_city(db)
        
        # Ingest Mumbai Bus
        bus_dir = "data/cities/mumbai/bus"
        if os.path.exists(bus_dir):
            print("Ingesting Mumbai Bus...")
            op_bus = get_operator(db, city.id, "BEST Bus Operator", "bus")
            cal_map = load_bus_calendar(db, os.path.join(bus_dir, "calendar.txt"))
            stop_map = load_bus_stops(db, os.path.join(bus_dir, "stops.txt"), city.id, op_bus.id)
            route_map = load_bus_routes(db, os.path.join(bus_dir, "routes.txt"), city.id, op_bus.id)
            trip_map = load_bus_trips(db, os.path.join(bus_dir, "trips.txt"), route_map, cal_map)
            load_bus_stop_times(db, os.path.join(bus_dir, "stop_times.txt"), trip_map, stop_map)
            print("Mumbai Bus ingestion complete!")

        # Ingest Mumbai Metro
        metro_path = "data/cities/mumbai/metro/mumbai_metro_master_all_4_lines.xlsx"
        if os.path.exists(metro_path):
            print("Ingesting Mumbai Metro...")
            op_metro = get_operator(db, city.id, "Mumbai Metro Operator", "metro")
            load_metro_excel(db, metro_path, city.id, op_metro.id)
            print("Mumbai Metro ingestion complete!")

    finally:
        db.close()

if __name__ == "__main__":
    main()
