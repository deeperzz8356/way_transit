from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from sqlalchemy import create_engine, text


@dataclass(frozen=True)
class RouteOption:
    route_id: int
    source: str
    destination: str
    transport: str
    departure_time: str
    arrival_time: str
    price: int


@lru_cache(maxsize=1)
def _get_engine():
    database_url = os.getenv("DATABASE_URL", "sqlite:///./way_transit.db")
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
    )


def search_route_options(source: str, destination: str, limit: int = 5) -> list[RouteOption]:
    query = text(
        """
        SELECT DISTINCT 
            r.id,
            s_start.name as source,
            s_end.name as destination,
            r.mode as transport,
            st_start.departure_time,
            st_end.arrival_time,
            100 as price
        FROM routes r
        JOIN trips t ON t.route_id = r.id
        JOIN stop_times st_start ON st_start.trip_id = t.id
        JOIN stops s_start ON st_start.stop_id = s_start.id
        JOIN stop_times st_end ON st_end.trip_id = t.id
        JOIN stops s_end ON st_end.stop_id = s_end.id
        WHERE st_start.stop_sequence < st_end.stop_sequence
          AND (lower(s_start.name) LIKE lower(:source) OR lower(s_start.stop_code) = lower(:source))
          AND (lower(s_end.name) LIKE lower(:destination) OR lower(s_end.stop_code) = lower(:destination))
        LIMIT :limit
        """
    )
    with _get_engine().connect() as connection:
        rows = connection.execute(
            query,
            {"source": f"%{source.strip()}%", "destination": f"%{destination.strip()}%", "limit": limit},
        ).mappings().all()
    return [RouteOption(route_id=row["id"], source=row["source"], destination=row["destination"], transport=row["transport"], departure_time=row["departure_time"], arrival_time=row["arrival_time"], price=row["price"]) for row in rows]


def get_route_by_id(route_id: int) -> RouteOption | None:
    query = text(
        """
        SELECT 
            r.id,
            r.mode as transport,
            (SELECT s.name FROM stop_times st JOIN stops s ON st.stop_id = s.id WHERE st.trip_id = t.id ORDER BY st.stop_sequence ASC LIMIT 1) as source,
            (SELECT s.name FROM stop_times st JOIN stops s ON st.stop_id = s.id WHERE st.trip_id = t.id ORDER BY st.stop_sequence DESC LIMIT 1) as destination,
            (SELECT st.departure_time FROM stop_times st WHERE st.trip_id = t.id ORDER BY st.stop_sequence ASC LIMIT 1) as departure_time,
            (SELECT st.arrival_time FROM stop_times st WHERE st.trip_id = t.id ORDER BY st.stop_sequence DESC LIMIT 1) as arrival_time,
            100 as price
        FROM routes r
        LEFT JOIN trips t ON t.route_id = r.id
        WHERE r.id = :route_id
        LIMIT 1
        """
    )
    with _get_engine().connect() as connection:
        row = connection.execute(query, {"route_id": route_id}).mappings().first()
    return (
        RouteOption(
            route_id=row["id"],
            source=row["source"] or "Unknown",
            destination=row["destination"] or "Unknown",
            transport=row["transport"] or "bus",
            departure_time=row["departure_time"] or "08:00 AM",
            arrival_time=row["arrival_time"] or "09:00 AM",
            price=row["price"] or 100,
        )
        if row
        else None
    )


def format_route_options(routes: Iterable[RouteOption]) -> str:
    lines = []
    for route in routes:
        lines.append(
            f"route_id {route.route_id}: {route.transport} from {route.source} to {route.destination} "
            f"departing {route.departure_time}, arriving {route.arrival_time}, fare ₹{route.price}"
        )
    return "\n".join(lines)
