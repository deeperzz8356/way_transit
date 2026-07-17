import pandas as pd
import os

# Paths
INPUT_DIR = 'data/cities/mumbai/bus/'
OUTPUT_DIR = 'data/cities/mumbai/bus_mvp/'

def process_mvp_data():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("--- MUMBAI BUS GTFS DATA ENGINEERING ---")
    
    # 1. Routes
    routes_file = os.path.join(INPUT_DIR, 'routes.txt')
    routes = pd.read_csv(routes_file)
    print(f"Original Routes: {len(routes)}")
    
    # Select just 5 routes for MVP
    # Let's pick 5 routes, making sure they are distinct
    mvp_routes = routes.head(5)
    mvp_route_ids = set(mvp_routes['route_id'])
    
    mvp_routes.to_csv(os.path.join(OUTPUT_DIR, 'routes.txt'), index=False)
    print(f"MVP Routes saved: {len(mvp_routes)}")

    # 2. Trips
    trips_file = os.path.join(INPUT_DIR, 'trips.txt')
    trips = pd.read_csv(trips_file)
    print(f"Original Trips: {len(trips)}")
    
    mvp_trips = trips[trips['route_id'].isin(mvp_route_ids)]
    mvp_trip_ids = set(mvp_trips['trip_id'])
    
    mvp_trips.to_csv(os.path.join(OUTPUT_DIR, 'trips.txt'), index=False)
    print(f"MVP Trips saved: {len(mvp_trips)}")
    
    # 3. Stop Times (Chunked)
    stop_times_file = os.path.join(INPUT_DIR, 'stop_times.txt')
    print("Processing Stop Times... (this may take a moment)")
    
    mvp_stop_times_list = []
    chunk_size = 50000
    total_original_stop_times = 0
    
    for chunk in pd.read_csv(stop_times_file, chunksize=chunk_size):
        total_original_stop_times += len(chunk)
        filtered_chunk = chunk[chunk['trip_id'].isin(mvp_trip_ids)]
        if not filtered_chunk.empty:
            mvp_stop_times_list.append(filtered_chunk)
            
    if mvp_stop_times_list:
        mvp_stop_times = pd.concat(mvp_stop_times_list)
    else:
        mvp_stop_times = pd.DataFrame()
        
    mvp_stop_ids = set(mvp_stop_times['stop_id']) if not mvp_stop_times.empty else set()
    
    mvp_stop_times.to_csv(os.path.join(OUTPUT_DIR, 'stop_times.txt'), index=False)
    print(f"Original Stop Times: {total_original_stop_times}")
    print(f"MVP Stop Times saved: {len(mvp_stop_times)}")
    
    # 4. Stops
    stops_file = os.path.join(INPUT_DIR, 'stops.txt')
    stops = pd.read_csv(stops_file)
    print(f"Original Stops: {len(stops)}")
    
    mvp_stops = stops[stops['stop_id'].isin(mvp_stop_ids)]
    mvp_stops.to_csv(os.path.join(OUTPUT_DIR, 'stops.txt'), index=False)
    print(f"MVP Stops saved: {len(mvp_stops)}")
    
    # 5. Calendar
    calendar_file = os.path.join(INPUT_DIR, 'calendar.txt')
    calendar = pd.read_csv(calendar_file)
    # We can just keep the whole calendar since it's tiny
    calendar.to_csv(os.path.join(OUTPUT_DIR, 'calendar.txt'), index=False)
    
    print("\n✅ Data Engineering Complete! MVP GTFS saved to: data/cities/mumbai/bus_mvp/")

if __name__ == "__main__":
    process_mvp_data()
