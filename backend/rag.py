from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy.orm import Session
import models

# Global variables for RAG
vector_store = None
# This will download the model to your local machine the first time it runs
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def _get_route_texts(db: Session) -> tuple[list[str], list[dict]]:
    routes = db.query(models.Route).all()
    texts = []
    metadatas = []
    for r in routes:
        text = f"Route {r.id}: From {r.source} to {r.destination} using {r.transport}. Departs at {r.departure_time} and arrives at {r.arrival_time}. Fare is {r.price} INR."
        texts.append(text)
        metadatas.append({"type": "route", "route_id": r.id})
    return texts, metadatas


def _get_realtime_texts(db: Session) -> tuple[list[str], list[dict]]:
    texts = []
    metadatas = []
    vps = db.query(models.VehiclePosition).all()
    for vp in vps:
        route_name = vp.route.name if vp.route else "Unknown Route"
        text = f"Vehicle {vp.vehicle_id} on route {route_name} (ID: {vp.route_id}) is currently at latitude {vp.lat}, longitude {vp.lon} traveling at {vp.speed_kmh} km/h with bearing {vp.bearing}° (Recorded at: {vp.recorded_at})."
        texts.append(text)
        metadatas.append({"type": "vehicle_position", "route_id": vp.route_id or 0})

    alerts = db.query(models.Alert).filter(models.Alert.is_active == True).all()
    for a in alerts:
        route_name = a.route.name if a.route else "System-wide"
        text = f"Alert (ID: {a.id}): Active transit disruption on route {route_name} due to {a.cause}. Effect: {a.effect}. Header: {a.header}. Description: {a.description} (Starts: {a.starts_at}, Ends: {a.ends_at})."
        texts.append(text)
        metadatas.append({"type": "alert", "route_id": a.route_id or 0})
    return texts, metadatas


def _get_stop_and_schedule_texts(db: Session) -> tuple[list[str], list[dict]]:
    texts = []
    metadatas = []
    stops = db.query(models.Stop).all()
    for s in stops:
        text = f"Stop: {s.name} (Code: {s.stop_code}, Mode: {s.mode}) is located at latitude {s.lat}, longitude {s.lon}."
        texts.append(text)
        metadatas.append({"type": "stop", "stop_id": s.id})
    query = (
        db.query(models.Route.id, models.Route.name, models.Stop.id, models.Stop.name, models.StopTime.departure_time)
        .join(models.Trip, models.Trip.route_id == models.Route.id)
        .join(models.StopTime, models.StopTime.trip_id == models.Trip.id)
        .join(models.Stop, models.StopTime.stop_id == models.Stop.id)
        .order_by(models.Route.id, models.Stop.id, models.StopTime.departure_time)
    )
    schedule_map = {}
    for r_id, r_name, s_id, s_name, dep_time in query.all():
        key = (r_id, r_name, s_id, s_name)
        if key not in schedule_map:
            schedule_map[key] = []
        schedule_map[key].append(dep_time)
    for (r_id, r_name, s_id, s_name), times in schedule_map.items():
        unique_times = sorted(list(set(times)))
        times_str = ", ".join(unique_times)
        text = f"Schedule/Time: Route {r_name} (ID: {r_id}) departs from stop {s_name} (ID: {s_id}) at these times: {times_str}."
        texts.append(text)
        metadatas.append({"type": "schedule", "route_id": r_id, "stop_id": s_id})
    return texts, metadatas


def sync_db_to_vectorstore(db: Session):
    global vector_store
    r_texts, r_metadatas = _get_route_texts(db)
    rt_texts, rt_metadatas = _get_realtime_texts(db)
    s_texts, s_metadatas = _get_stop_and_schedule_texts(db)
    texts = r_texts + rt_texts + s_texts
    metadatas = r_metadatas + rt_metadatas + s_metadatas
    texts.append(
        "WAY Transit General Policy: We support trains, buses, and metro lines. "
        "All bookings are strictly non-refundable once confirmed unless there is a service disruption. "
        "Please arrive 10 minutes before departure time. Emergency helpline is 1800-WAY-SAFE."
    )
    metadatas.append({"type": "policy", "route_id": 0})
    if texts:
        vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        print("Successfully synced Postgres routes into FAISS Vector Store.")
    else:
        print("No data found to build the vector store.")

def retrieve_context(query: str, k: int = 3) -> str:
    global vector_store
    if not vector_store:
        return "Knowledge base not initialized."
    
    # Find the top k most relevant routes/policies based on the user's message
    docs = vector_store.similarity_search(query, k=k)
    
    context = "\n".join([doc.page_content for doc in docs])
    return context
