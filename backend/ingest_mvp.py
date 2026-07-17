import pandas as pd
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
import models
import os

BUS_DIR = 'data/cities/mumbai/bus_mvp/'
METRO_FILE = 'data/cities/mumbai/metro/mumbai_metro_master_all_4_lines.xlsx'

def recreate_tables():
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables recreated.")

def ingest_bus(db: Session):
    print("Ingesting Bus Data...")
    
    # Create Dummy City and Operator
    city = models.City(name="Mumbai", slug="mumbai", state="Maharashtra", country="India", is_active=True)
    db.add(city)
    db.commit()
    
    operator = models.Operator(city_id=city.id, name="BEST", mode="bus")
    db.add(operator)
    db.commit()

    # 1. Routes
    routes_df = pd.read_csv(os.path.join(BUS_DIR, 'routes.txt'))
    for _, row in routes_df.iterrows():
        route = models.Route(
            id=str(row['route_id']).replace('-', ''), # simplify ID for int
            city_id=city.id,
            operator_id=operator.id,
            route_code=str(row['route_id']),
            name=str(row.get('route_long_name', str(row.get('route_short_name', '')))),
            mode="bus"
        )
        db.add(route)
    db.commit()
    print(f"Inserted {len(routes_df)} routes")

    # 2. Service Calendar
    calendar_df = pd.read_csv(os.path.join(BUS_DIR, 'calendar.txt'))
    for _, row in calendar_df.iterrows():
        # GTFS calendar start/end date are YYYYMMDD
        from datetime import datetime
        start = datetime.strptime(str(row['start_date']), '%Y%m%d').date()
        end = datetime.strptime(str(row['end_date']), '%Y%m%d').date()
        cal = models.ServiceCalendar(
            service_id=str(row['service_id']),
            monday=bool(row['monday']),
            tuesday=bool(row['tuesday']),
            wednesday=bool(row['wednesday']),
            thursday=bool(row['thursday']),
            friday=bool(row['friday']),
            saturday=bool(row['saturday']),
            sunday=bool(row['sunday']),
            start_date=start,
            end_date=end
        )
        db.add(cal)
    db.commit()
    print(f"Inserted {len(calendar_df)} calendar records")

    # 3. Trips
    trips_df = pd.read_csv(os.path.join(BUS_DIR, 'trips.txt'))
    trip_id_map = {}
    trip_id_counter = 1
    for _, row in trips_df.iterrows():
        route_id_int = str(row['route_id']).replace('-', '')
        trip = models.Trip(
            id=trip_id_counter,
            route_id=route_id_int,
            service_id=str(row['service_id']),
            direction=str(row.get('direction_id', '0')),
            trip_short_name=str(row['trip_id'])
        )
        trip_id_map[str(row['trip_id'])] = trip_id_counter
        db.add(trip)
        trip_id_counter += 1
    db.commit()
    print(f"Inserted {len(trips_df)} trips")

    # 4. Stops
    stops_df = pd.read_csv(os.path.join(BUS_DIR, 'stops.txt'))
    stop_id_map = {}
    stop_id_counter = 1
    for _, row in stops_df.iterrows():
        stop = models.Stop(
            id=stop_id_counter,
            city_id=city.id,
            operator_id=operator.id,
            stop_code=str(row['stop_id']),
            name=str(row['stop_name']),
            lat=float(row['stop_lat']),
            lon=float(row['stop_lon']),
            mode="bus"
        )
        stop_id_map[str(row['stop_id'])] = stop_id_counter
        db.add(stop)
        stop_id_counter += 1
    db.commit()
    print(f"Inserted {len(stops_df)} stops")

    # 5. Stop Times
    stop_times_df = pd.read_csv(os.path.join(BUS_DIR, 'stop_times.txt'))
    stop_times_data = []
    for _, row in stop_times_df.iterrows():
        trip_internal_id = trip_id_map.get(str(row['trip_id']))
        stop_internal_id = stop_id_map.get(str(row['stop_id']))
        if trip_internal_id and stop_internal_id:
            stop_times_data.append({
                "trip_id": trip_internal_id,
                "stop_id": stop_internal_id,
                "stop_sequence": int(row['stop_sequence']),
                "arrival_time": str(row['arrival_time']),
                "departure_time": str(row['departure_time'])
            })
    
    db.bulk_insert_mappings(models.StopTime, stop_times_data)
    db.commit()
    print(f"Inserted {len(stop_times_data)} stop times")

def ingest_metro(db: Session):
    print("\nIngesting Metro Data...")
    
    # Get city
    city = db.query(models.City).filter(models.City.slug == "mumbai").first()
    operator = models.Operator(city_id=city.id, name="Mumbai Metro", mode="metro")
    db.add(operator)
    db.commit()

    # Create dummy calendar for WD_WE_ALL
    from datetime import date
    cal = models.ServiceCalendar(
        service_id="WD_WE_ALL",
        monday=True, tuesday=True, wednesday=True, thursday=True, friday=True, saturday=True, sunday=True,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31)
    )
    db.add(cal)
    db.commit()

    # Read excel
    # Note: Use engine='openpyxl' for xlsx
    # 1. Routes
    routes_df = pd.read_excel(METRO_FILE, sheet_name='routes', engine='openpyxl')
    route_id_map = {}
    route_id_counter = 1000
    for _, row in routes_df.iterrows():
        route = models.Route(
            id=route_id_counter,
            city_id=city.id,
            operator_id=operator.id,
            route_code=str(row['route_id']),
            name=str(row['name']),
            mode="metro",
            color_hex=str(row.get('color', ''))
        )
        route_id_map[str(row['route_id'])] = route_id_counter
        db.add(route)
        route_id_counter += 1
    db.commit()
    print(f"Inserted {len(routes_df)} metro routes")

    # 2. Stops
    stops_df = pd.read_excel(METRO_FILE, sheet_name='stops', engine='openpyxl')
    stop_id_map = {}
    stop_id_counter = 10000
    for _, row in stops_df.iterrows():
        stop = models.Stop(
            id=stop_id_counter,
            city_id=city.id,
            operator_id=operator.id,
            stop_code=str(row['stop_id']),
            name=str(row['name']),
            lat=float(row['lat']),
            lon=float(row['lon']),
            mode="metro"
        )
        stop_id_map[str(row['stop_id'])] = stop_id_counter
        db.add(stop)
        stop_id_counter += 1
    db.commit()
    print(f"Inserted {len(stops_df)} metro stops")

    # 3. Trips
    trips_df = pd.read_excel(METRO_FILE, sheet_name='trips', engine='openpyxl')
    trip_id_map = {}
    trip_id_counter = 10000
    for _, row in trips_df.iterrows():
        trip = models.Trip(
            id=trip_id_counter,
            route_id=route_id_map.get(str(row['route_id'])),
            service_id="WD_WE_ALL",
            direction=str(row.get('direction', '0')),
            trip_short_name=str(row['trip_id'])
        )
        trip_id_map[str(row['trip_id'])] = trip_id_counter
        db.add(trip)
        trip_id_counter += 1
    db.commit()
    print(f"Inserted {len(trips_df)} metro trips")

    # 4. Stop Times
    stop_times_df = pd.read_excel(METRO_FILE, sheet_name='stop_times', engine='openpyxl')
    stop_times_data = []
    for _, row in stop_times_df.iterrows():
        t_id = trip_id_map.get(str(row['trip_id']))
        s_id = stop_id_map.get(str(row['stop_id']))
        if t_id and s_id:
            stop_times_data.append({
                "trip_id": t_id,
                "stop_id": s_id,
                "stop_sequence": int(row['sequence']),
                "arrival_time": str(row['arrival_time']),
                "departure_time": str(row['departure_time'])
            })
    db.bulk_insert_mappings(models.StopTime, stop_times_data)
    db.commit()
    print(f"Inserted {len(stop_times_data)} metro stop times")

    # 5. Fare Rules -> FareMatrix
    fare_df = pd.read_excel(METRO_FILE, sheet_name='fare_rules', engine='openpyxl')
    fare_data = []
    for _, row in fare_df.iterrows():
        from_id = stop_id_map.get(str(row['origin_stop']))
        to_id = stop_id_map.get(str(row['destination_stop']))
        if from_id and to_id:
            fare_data.append({
                "operator_id": operator.id,
                "from_stop_id": from_id,
                "to_stop_id": to_id,
                "price": float(row['price'])
            })
    db.bulk_insert_mappings(models.FareMatrix, fare_data)
    db.commit()
    print(f"Inserted {len(fare_data)} metro fare matrix rules")

if __name__ == "__main__":
    recreate_tables()
    db = SessionLocal()
    try:
        ingest_bus(db)
        ingest_metro(db)
        print("\nIngestion Complete! Database is populated and ready for MVP.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
