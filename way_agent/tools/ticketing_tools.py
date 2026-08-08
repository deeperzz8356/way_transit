"""Wallet-backed ticketing tools for the Ticketing Agent."""
from __future__ import annotations

import os
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

# Allow importing backend modules when running from way_agent
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_BACKEND = os.path.join(_ROOT, "backend")
import sys

if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from database import SessionLocal  # noqa: E402
import models  # noqa: E402
import crud  # noqa: E402
from platform_colors import normalize_mode  # noqa: E402


def _db() -> Session:
    return SessionLocal()


def _format_ticket(b: models.Booking) -> str:
    return (
        f"id={b.id} | {(b.source or '?')} -> {(b.destination or '?')} | "
        f"mode={b.mode or 'other'} | status={b.status} | "
        f"ticket_number={b.ticket_number or 'n/a'} | "
        f"qr={'yes' if b.qr_payload else 'no'} | "
        f"operator={b.operator_name or 'n/a'}"
    )


@tool
def list_wallet_tickets(user_id: int, mode: Optional[str] = None) -> str:
    """List tickets in the user's unified wallet. Optionally filter by mode: rail, metro, bus, cab, other."""
    db = _db()
    try:
        tickets, _ = crud.get_user_wallet(
            db, user_id=user_id, mode=mode if mode and mode != "all" else None
        )
        if not tickets:
            return "Wallet is empty for that filter."
        lines = [_format_ticket(t) for t in tickets[:20]]
        return "Wallet tickets:\n" + "\n".join(lines)
    finally:
        db.close()


@tool
def get_ticket(user_id: int, ticket_id: int) -> str:
    """Get one wallet ticket by id for the user."""
    db = _db()
    try:
        b = (
            db.query(models.Booking)
            .filter(models.Booking.id == ticket_id, models.Booking.user_id == user_id)
            .first()
        )
        if not b:
            return f"Ticket {ticket_id} not found in wallet."
        return "Ticket detail:\n" + _format_ticket(b)
    finally:
        db.close()


@tool
def start_journey(user_id: int, ticket_id: int) -> str:
    """Start a journey from a wallet ticket (sets status IN_PROGRESS)."""
    db = _db()
    try:
        journey, err = crud.start_journey_for_ticket(db, user_id=user_id, booking_id=ticket_id)
        if err:
            return err
        return (
            f"Journey started (journey_id={journey.id}) for ticket {ticket_id}. "
            f"Status is now IN_PROGRESS."
        )
    finally:
        db.close()


@tool
def calculate_fare(origin: str, destination: str) -> str:
    """Rough fare hint between two stations (placeholder)."""
    return f"Estimated fare from {origin} to {destination} is typically ₹10–₹50 depending on mode and distance."


@tool
def buy_pass(pass_type: str, user_id: str) -> str:
    """Guide pass purchase; does not charge payment credentials."""
    return (
        f"Open Unified Wallet → Add Pass to purchase a {pass_type} pass for user {user_id}. "
        "Payment stays inside the WAY app — never share OTP/UPI PIN/CVV here."
    )


def wallet_context_for_user(user_id: int) -> str:
    """Plain-text wallet summary injected into agent db_context."""
    db = _db()
    try:
        tickets, passes = crud.get_user_wallet(db, user_id=user_id)
        if not tickets and not passes:
            return "USER WALLET: empty."
        lines = ["USER WALLET TICKETS:"]
        for t in tickets[:15]:
            lines.append(_format_ticket(t))
        if passes:
            lines.append("USER PASSES:")
            for p in passes[:10]:
                name = p.pass_product.name if p.pass_product else "Pass"
                mode = normalize_mode(p.pass_product.mode_coverage if p.pass_product else None)
                lines.append(f"pass_id={p.id} name={name} mode={mode} status={p.status}")
        return "\n".join(lines)
    finally:
        db.close()
