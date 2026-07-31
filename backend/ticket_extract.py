"""Ticket image OCR + field extraction for unified wallet ingest."""
from __future__ import annotations

import os
import re
from typing import Optional


def _ocr_with_tesseract(image_path: str) -> Optional[str]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return None

    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip() if text and text.strip() else None
    except Exception:
        return None


def _ocr_with_groq_vision(image_path: str) -> Optional[str]:
    """Optional vision pass when GROQ_API_KEY is set."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        import base64
        from groq import Groq

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower().lstrip(".") or "jpeg"
        mime = "image/png" if ext == "png" else "image/jpeg"

        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract transit ticket text. Prefer lines with From/To, "
                                "Source/Destination, Origin/Destination, stations, operator, date. "
                                "Return plain text only."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=500,
        )
        text = completion.choices[0].message.content
        return text.strip() if text else None
    except Exception:
        return None


def _first_match(patterns: list[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip(" :-|\t")
            value = re.sub(r"\s+", " ", value).strip()
            if value:
                return value
    return None


def parse_ticket_text(text: str) -> dict:
    """Parse source/destination/operator/date from OCR or vision text."""
    cleaned = text.replace("\r", "\n")
    source = _first_match(
        [
            r"(?:from|source|origin|boarding|dep(?:arture)?(?:\s*station)?)\s*[:\-]\s*(.+)",
            r"from\s+([A-Za-z0-9 .'-]{2,60}?)\s+to\b",
        ],
        cleaned,
    )
    destination = _first_match(
        [
            r"(?:to|destination|arrival|arr(?:iving)?(?:\s*station)?)\s*[:\-]\s*(.+)",
            r"\bto\s+([A-Za-z0-9 .'-]{2,60})(?:\n|$|,)",
        ],
        cleaned,
    )
    operator = _first_match(
        [
            r"(?:operator|agency|carrier|service)\s*[:\-]\s*(.+)",
            r"\b(IRCTC|Indian Railways|Metro|BMTC|DTC|BEST|Uber|Ola)\b",
        ],
        cleaned,
    )
    travel_date = _first_match(
        [
            r"(?:date|travel\s*date|journey\s*date|dep(?:arture)?\s*date)\s*[:\-]\s*(.+)",
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})\b",
        ],
        cleaned,
    )

    # Fallback: "A to B" on a single line
    if not source or not destination:
        for line in cleaned.splitlines():
            line = line.strip()
            m = re.match(
                r"^([A-Za-z0-9 .'-]{2,40})\s+(?:➔|→|->|to)\s+([A-Za-z0-9 .'-]{2,40})$",
                line,
                flags=re.IGNORECASE,
            )
            if m:
                source = source or m.group(1).strip()
                destination = destination or m.group(2).strip()
                break

    return {
        "source": source,
        "destination": destination,
        "operator": operator,
        "travel_date": travel_date,
        "raw_text": cleaned[:4000] if cleaned else None,
    }


def extract_ticket_info(image_path: str) -> dict:
    """
    Run OCR/vision then parse fields.
    Always returns a dict; missing fields are None so the client can edit.
    """
    text = _ocr_with_tesseract(image_path)
    engine = "tesseract" if text else None

    if not text:
        text = _ocr_with_groq_vision(image_path)
        engine = "groq_vision" if text else None

    if not text:
        return {
            "source": None,
            "destination": None,
            "operator": None,
            "travel_date": None,
            "raw_text": None,
            "ocr_engine": None,
            "message": "No OCR engine available or no text found; enter stations manually.",
        }

    parsed = parse_ticket_text(text)
    parsed["ocr_engine"] = engine
    parsed["message"] = "Fields extracted; review before saving."
    return parsed
