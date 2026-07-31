"""Booking + unified ticket ingest (upload, live-tail SSE, confirm)."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import SessionLocal
from dependencies import get_current_user
from ticket_extract import extract_ticket_info

router = APIRouter(prefix="/booking", tags=["booking"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "tickets"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In-memory live-tail buffers: job_id -> list of event dicts
_job_events: dict[int, list[dict[str, Any]]] = {}
_job_done: dict[int, bool] = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _append_event(job_id: int, event: str, **payload):
    entry = {
        "event": event,
        "job_id": job_id,
        "ts": datetime.utcnow().isoformat() + "Z",
        **payload,
    }
    _job_events.setdefault(job_id, []).append(entry)
    return entry


def _process_ticket_job(job_id: int, image_path: str):
    """Background pipeline: OCR → extract → update job; emits live-tail events."""
    db = SessionLocal()
    try:
        job = db.query(models.TicketIngestJob).filter(models.TicketIngestJob.id == job_id).first()
        if not job:
            _append_event(job_id, "error", message="Job not found")
            _job_done[job_id] = True
            return

        crud.update_ticket_ingest_job(db, job, status="processing")
        _append_event(job_id, "ocr_started", message="Starting information extraction")

        result = extract_ticket_info(image_path)

        _append_event(
            job_id,
            "ocr_done",
            message=result.get("message") or "OCR finished",
            ocr_engine=result.get("ocr_engine"),
        )

        source = result.get("source")
        destination = result.get("destination")
        operator = result.get("operator")
        travel_date = result.get("travel_date")
        raw_text = result.get("raw_text")

        crud.update_ticket_ingest_job(
            db,
            job,
            status="extracted",
            source=source,
            destination=destination,
            operator=operator,
            travel_date=travel_date,
            raw_text=raw_text,
            error_message=None,
        )

        _append_event(
            job_id,
            "extracted",
            message="Ticket fields ready for review",
            source=source,
            destination=destination,
            operator=operator,
            travel_date=travel_date,
        )
        _append_event(job_id, "ready", message="Awaiting user confirm")
    except Exception as exc:
        try:
            job = db.query(models.TicketIngestJob).filter(models.TicketIngestJob.id == job_id).first()
            if job:
                crud.update_ticket_ingest_job(
                    db, job, status="error", error_message=str(exc)
                )
        except Exception:
            pass
        _append_event(job_id, "error", message=str(exc))
    finally:
        _job_done[job_id] = True
        db.close()


@router.post("/add-ticket", response_model=schemas.BookingResponse)
def add_ticket(
    data: schemas.TicketAddRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a ticket/pass to the unified wallet (manual entry or confirmed fields)."""
    return crud.create_unified_ticket(
        db=db,
        user_id=user_id,
        source=data.source,
        destination=data.destination,
        image_url=data.image_url,
    )


@router.post("/upload-ticket", response_model=schemas.TicketUploadResponse)
async def upload_ticket(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Multipart ticket image upload; starts async extract with live-tail events."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}:
        ext = ".jpg"

    filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = UPLOAD_DIR / filename
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    dest_path.write_bytes(content)

    image_url = f"/uploads/tickets/{filename}"
    job = crud.create_ticket_ingest_job(db, user_id=user_id, image_url=image_url)

    _job_events[job.id] = []
    _job_done[job.id] = False
    _append_event(job.id, "uploaded", message="Ticket image saved", image_url=image_url)

    background_tasks.add_task(_process_ticket_job, job.id, str(dest_path))

    return schemas.TicketUploadResponse(
        job_id=job.id,
        status=job.status,
        image_url=image_url,
        events_url=f"/booking/ticket-jobs/{job.id}/events",
    )


@router.get("/ticket-jobs/{job_id}", response_model=schemas.TicketJobResponse)
def get_ticket_job(
    job_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = crud.get_ticket_ingest_job(db, job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ticket job not found")
    return job


@router.get("/ticket-jobs/{job_id}/events")
async def ticket_job_events(
    job_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE live-tail of upload → OCR → extract progress."""
    job = crud.get_ticket_ingest_job(db, job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ticket job not found")

    async def event_generator():
        idx = 0
        # Replay any events already buffered
        idle_rounds = 0
        while True:
            events = _job_events.get(job_id, [])
            while idx < len(events):
                payload = json.dumps(events[idx])
                yield f"data: {payload}\n\n"
                idx += 1
                idle_rounds = 0

            if _job_done.get(job_id, False) and idx >= len(_job_events.get(job_id, [])):
                yield f"data: {json.dumps({'event': 'done', 'job_id': job_id})}\n\n"
                break

            idle_rounds += 1
            if idle_rounds > 200:  # ~60s safety timeout
                yield f"data: {json.dumps({'event': 'timeout', 'job_id': job_id})}\n\n"
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ticket-jobs/{job_id}/confirm", response_model=schemas.BookingResponse)
def confirm_ticket_job(
    job_id: int,
    data: schemas.TicketConfirmRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Finalize extracted (or edited) fields into a confirmed wallet booking."""
    job = crud.get_ticket_ingest_job(db, job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ticket job not found")
    if job.booking_id:
        booking = db.query(models.Booking).filter(models.Booking.id == job.booking_id).first()
        if booking:
            return booking

    booking = crud.create_unified_ticket(
        db=db,
        user_id=user_id,
        source=data.source,
        destination=data.destination,
        image_url=job.image_url,
    )
    crud.update_ticket_ingest_job(
        db,
        job,
        status="confirmed",
        source=data.source,
        destination=data.destination,
        operator=data.operator,
        travel_date=data.travel_date,
        booking_id=booking.id,
    )
    _append_event(
        job_id,
        "saved",
        message="Ticket saved to wallet",
        booking_id=booking.id,
        source=data.source,
        destination=data.destination,
    )
    _job_done[job_id] = True
    return booking


@router.get("/my-bookings", response_model=list[schemas.BookingResponse])
def get_my_bookings(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tickets/passes in the unified wallet for current user."""
    return (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user_id)
        .order_by(models.Booking.booked_at.desc())
        .all()
    )
