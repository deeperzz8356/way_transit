import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from groq import Groq

from database import SessionLocal
import models
import schemas
from dependencies import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize Groq client
# Make sure GROQ_API_KEY is set in your environment variables
client = Groq()

@router.post("/chat", response_model=schemas.ChatResponse)
def chat_with_agent(
    chat_request: schemas.ChatRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 1. Fetch User Data
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2. Fetch User's Bookings
        bookings = db.query(models.Booking).filter(models.Booking.user_id == user_id).all()
        booking_details = []
        for b in bookings:
            route = db.query(models.Route).filter(models.Route.id == b.route_id).first()
            if route:
                booking_details.append(f"Booking ID: {b.id}, Route: {route.source} to {route.destination} via {route.transport}, Status: {b.status}")
        
        # 3. Fetch All Available Routes (for general awareness)
        all_routes = db.query(models.Route).all()
        route_list = [f"Route ID: {r.id}, {r.source} -> {r.destination} via {r.transport}" for r in all_routes]
        
        # Construct context strings
        bookings_context = "\n".join(booking_details) if booking_details else "No current bookings."
        routes_context = "\n".join(route_list) if route_list else "No routes available."

        # 4. Construct System Prompt
        system_prompt = f"""
You are the Way Transit AI Assistant. Your role is to help users manage their transit bookings, find available routes, and answer questions about the Way Transit service.
You are helpful, concise, and friendly.

Here is the data context you have access to:
---
CURRENT USER:
Email: {user.email}
User ID: {user.id}

USER'S CURRENT BOOKINGS:
{bookings_context}

ALL AVAILABLE TRANSIT ROUTES IN THE DATABASE:
{routes_context}
---
Use this context to accurately answer the user's queries. If they ask about their bookings, refer to the data above. If they ask about available routes, use the routes listed above. Do not make up routes or bookings that do not exist in the context.
"""

        # 5. Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": chat_request.message
                }
            ],
            model="llama3-8b-8192", # Defaulting to a fast open-source model available on Groq
            temperature=0.5,
            max_tokens=1024,
        )

        agent_response = chat_completion.choices[0].message.content

        return schemas.ChatResponse(response=agent_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
