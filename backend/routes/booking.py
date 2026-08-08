"""Booking + unified ticket ingest (upload, live-tail SSE, confirm, journey, wallet)."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import SessionLocal
from dependencies import get_current_user
from platform_colors import color_for_mode, normalize_mode, infer_mode_from_operator
from ticket_extract import extract_ticket_info

router = APIRouter(prefix="/booking", tags=["booking"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "tickets"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
        ticket_number = result.get("ticket_number")
        qr_payload = result.get("qr_payload")
        mode = result.get("mode") or infer_mode_from_operator(operator, raw_text)
        class_name = result.get("class_name")
        fare = result.get("fare")

        if qr_payload:
            _append_event(job_id, "qr_decoded", message="QR payload decoded from image", qr_payload=qr_payload)

        crud.update_ticket_ingest_job(
            db,
            job,
            status="extracted",
            source=source,
            destination=destination,
            operator=operator,
            travel_date=travel_date,
            ticket_number=ticket_number,
            qr_payload=qr_payload,
            mode=mode,
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
            ticket_number=ticket_number,
            qr_payload=qr_payload,
            mode=mode,
            class_name=class_name,
            fare=fare,
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


def _ticket_kwargs_from_body(data) -> dict:
    operator_name = getattr(data, "operator_name", None) or getattr(data, "operator", None)
    mode = getattr(data, "mode", None) or infer_mode_from_operator(operator_name)
    return {
        "source": data.source,
        "destination": data.destination,
        "image_url": getattr(data, "image_url", None),
        "ticket_number": getattr(data, "ticket_number", None),
        "qr_payload": getattr(data, "qr_payload", None),
        "mode": mode,
        "operator_name": operator_name,
        "travel_date": getattr(data, "travel_date", None),
        "class_name": getattr(data, "class_name", None),
        "fare": getattr(data, "fare", None),
        "source_type": getattr(data, "source_type", None) or "manual",
    }


@router.post("/add-ticket", response_model=schemas.BookingResponse)
def add_ticket(
    data: schemas.TicketAddRequest,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a ticket/pass to the unified wallet (manual entry)."""
    kwargs = _ticket_kwargs_from_body(data)
    dup = crud.find_duplicate_ticket(
        db, user_id, kwargs.get("ticket_number"), kwargs.get("mode")
    )
    if dup:
        raise HTTPException(
            status_code=409,
            detail={"message": "Already in wallet", "booking_id": dup.id},
        )
    return crud.create_unified_ticket(db=db, user_id=user_id, **kwargs)


@router.post("/upload-ticket", response_model=schemas.TicketUploadResponse)
async def upload_ticket(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
    job = crud.get_ticket_ingest_job(db, job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ticket job not found")

    async def event_generator():
        idx = 0
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
            if idle_rounds > 200:
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
    job = crud.get_ticket_ingest_job(db, job_id=job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ticket job not found")
    if job.booking_id:
        booking = db.query(models.Booking).filter(models.Booking.id == job.booking_id).first()
        if booking:
            return booking

    operator_name = data.operator_name or data.operator or job.operator
    mode = data.mode or job.mode or infer_mode_from_operator(operator_name, job.raw_text)
    ticket_number = data.ticket_number or job.ticket_number
    qr_payload = data.qr_payload or job.qr_payload

    dup = crud.find_duplicate_ticket(db, user_id, ticket_number, mode)
    if dup:
        raise HTTPException(
            status_code=409,
            detail={"message": "Already in wallet", "booking_id": dup.id},
        )

    booking = crud.create_unified_ticket(
        db=db,
        user_id=user_id,
        source=data.source,
        destination=data.destination,
        image_url=job.image_url,
        ticket_number=ticket_number,
        qr_payload=qr_payload,
        mode=mode,
        operator_name=operator_name,
        travel_date=data.travel_date or job.travel_date,
        class_name=data.class_name,
        fare=data.fare,
        source_type="scan",
    )
    crud.update_ticket_ingest_job(
        db,
        job,
        status="confirmed",
        source=data.source,
        destination=data.destination,
        operator=operator_name,
        travel_date=data.travel_date or job.travel_date,
        ticket_number=ticket_number,
        qr_payload=qr_payload,
        mode=mode,
        booking_id=booking.id,
    )
    _append_event(
        job_id,
        "saved",
        message="Ticket saved to wallet",
        booking_id=booking.id,
        source=data.source,
        destination=data.destination,
        ticket_number=ticket_number,
        mode=mode,
    )
    _job_done[job_id] = True
    return booking


@router.get("/my-bookings", response_model=list[schemas.BookingResponse])
def get_my_bookings(
    mode: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tickets, _ = crud.get_user_wallet(db, user_id=user_id, mode=mode)
    return tickets


@router.get("/wallet", response_model=schemas.WalletResponse)
def get_wallet(
    mode: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.ensure_demo_pass_products(db)
    tickets, passes = crud.get_user_wallet(db, user_id=user_id, mode=mode)
    pass_out = []
    for up in passes:
        product = up.pass_product
        mode_c = normalize_mode(product.mode_coverage if product else None)
        op_color = None
        if product and product.operator:
            op_color = product.operator.color_hex
        pass_out.append(
            schemas.UserPassResponse(
                id=up.id,
                pass_id=up.pass_id,
                name=product.name if product else None,
                mode_coverage=mode_c,
                color_hex=color_for_mode(mode_c, op_color),
                valid_until=up.valid_until,
                status=up.status,
                price=product.price if product else None,
            )
        )
    return schemas.WalletResponse(tickets=tickets, passes=pass_out)


@router.get("/tickets/{ticket_id}", response_model=schemas.BookingResponse)
def get_ticket(
    ticket_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.id == ticket_id, models.Booking.user_id == user_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return booking


@router.delete("/tickets/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok, err = crud.delete_ticket(db, user_id=user_id, booking_id=ticket_id)
    if not ok:
        raise HTTPException(status_code=404, detail=err)
    return {"ok": True, "deleted_id": ticket_id}


@router.post("/tickets/{ticket_id}/start-journey", response_model=schemas.JourneyResponse)
def start_journey(
    ticket_id: int,
    data: schemas.JourneyStartRequest = Body(default_factory=schemas.JourneyStartRequest),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    journey, err = crud.start_journey_for_ticket(
        db,
        user_id=user_id,
        booking_id=ticket_id,
        start_time=data.start_time,
        estimated_end_time=data.estimated_end_time,
        make_active=data.make_active,
    )
    if err:
        status = 404 if err == "Ticket not found" else 400
        raise HTTPException(status_code=status, detail=err)
    booking = db.query(models.Booking).filter(models.Booking.id == ticket_id).first()
    return schemas.JourneyResponse(
        id=journey.id,
        user_id=journey.user_id,
        booking_id=journey.booking_id,
        from_stop_id=journey.from_stop_id,
        to_stop_id=journey.to_stop_id,
        status=journey.status,
        started_at=journey.started_at,
        estimated_end_at=journey.estimated_end_at,
        created_at=journey.created_at,
        source=booking.source if booking else None,
        destination=booking.destination if booking else None,
        mode=booking.mode if booking else None,
        color_hex=color_for_mode(booking.mode if booking else None),
        is_active=True,
    )


@router.post("/tickets/{ticket_id}/complete", response_model=schemas.BookingResponse)
def complete_journey(
    ticket_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking, err = crud.complete_ticket_journey(db, user_id=user_id, booking_id=ticket_id)
    if err:
        raise HTTPException(status_code=404, detail=err)
    return booking


@router.get("/passes", response_model=list[schemas.UserPassResponse])
def list_pass_products(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.ensure_demo_pass_products(db)
    products = db.query(models.Pass).filter(models.Pass.is_active == True).all()  # noqa: E712
    out = []
    for p in products:
        mode_c = normalize_mode(p.mode_coverage)
        op_color = p.operator.color_hex if p.operator else None
        out.append(
            schemas.UserPassResponse(
                id=p.id,
                pass_id=p.id,
                name=p.name,
                mode_coverage=mode_c,
                color_hex=color_for_mode(mode_c, op_color),
                valid_until=None,
                status="available",
                price=p.price,
            )
        )
    return out


@router.post("/passes/{pass_id}/add", response_model=schemas.UserPassResponse)
def add_pass_to_wallet(
    pass_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    up = crud.add_user_pass(db, user_id=user_id, pass_id=pass_id)
    if not up:
        raise HTTPException(status_code=404, detail="Pass not found")
    product = up.pass_product
    mode_c = normalize_mode(product.mode_coverage if product else None)
    return schemas.UserPassResponse(
        id=up.id,
        pass_id=up.pass_id,
        name=product.name if product else None,
        mode_coverage=mode_c,
        color_hex=color_for_mode(mode_c),
        valid_until=up.valid_until,
        status=up.status,
        price=product.price if product else None,
    )
