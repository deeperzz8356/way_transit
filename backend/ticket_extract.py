"""Ticket image OCR + field extraction for unified wallet ingest.

Engine order:
  1. Groq vision LLM (primary)
  2. Google Cloud Vision (fallback)
  3. Tesseract (offline last resort)
"""
from __future__ import annotations

import os
import re
from typing import Optional

try:
    from dotenv import load_dotenv

    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_root, ".env"))
except Exception:
    pass

_LAST_GROQ_ERROR: Optional[str] = None
_LAST_GOOGLE_ERROR: Optional[str] = None
_LAST_TESSERACT_ERROR: Optional[str] = None


def _ocr_with_groq_vision(image_path: str) -> Optional[str]:
    """Primary: vision LLM when GROQ_API_KEY is set."""
    global _LAST_GROQ_ERROR
    _LAST_GROQ_ERROR = None
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        _LAST_GROQ_ERROR = "GROQ_API_KEY missing in .env"
        return None
    try:
        import base64
        from groq import Groq

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower().lstrip(".") or "jpeg"
        mime = "image/png" if ext == "png" else "image/jpeg"

        model = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Read the transit ticket in the image carefully. "
                                "Extract the real origin, destination, ticket/UTS/PNR number, and operator. "
                                "Output ONLY these lines, using the real values from the image. "
                                "If a value is not visible, omit that line entirely. "
                                "Do NOT output angle brackets, placeholders, or the words station/name/date alone.\n"
                                "From: \n"
                                "To: \n"
                                "TicketNumber: \n"
                                "Operator: \n"
                                "Date: \n"
                                "Mode: rail|metro|bus|cab|other\n"
                                "Class: \n"
                                "Fare: "                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=800,
        )
        text = completion.choices[0].message.content
        if not text:
            _LAST_GROQ_ERROR = "Groq returned empty content"
            return None
        # Qwen-style models may wrap reasoning in <think>...</think>
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        return text if text else None
    except Exception as exc:
        _LAST_GROQ_ERROR = str(exc)
        return None


def _ocr_with_google_vision(image_path: str) -> Optional[str]:
    """Fallback: Google Cloud Vision OCR (API key or ADC service account)."""
    global _LAST_GOOGLE_ERROR
    _LAST_GOOGLE_ERROR = None
    api_key = (
        os.getenv("GOOGLE_VISION_API_KEY")
        or os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )

    # Prefer REST + API key (no extra SDK required)
    if api_key:
        try:
            import base64
            import json
            import urllib.request

            with open(image_path, "rb") as f:
                content = base64.b64encode(f.read()).decode("utf-8")

            body = json.dumps(
                {
                    "requests": [
                        {
                            "image": {"content": content},
                            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                        }
                    ]
                }
            ).encode("utf-8")

            url = (
                "https://vision.googleapis.com/v1/images:annotate"
                f"?key={api_key}"
            )
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))

            responses = payload.get("responses") or []
            if not responses:
                return None
            first = responses[0]
            if first.get("error"):
                _LAST_GOOGLE_ERROR = str(first.get("error"))
                return None
            full = first.get("fullTextAnnotation") or {}
            text = full.get("text")
            if text and text.strip():
                return text.strip()
            annotations = first.get("textAnnotations") or []
            if annotations and annotations[0].get("description"):
                return annotations[0]["description"].strip()
            return None
        except Exception as exc:
            _LAST_GOOGLE_ERROR = str(exc)
            return None

    # Optional: google-cloud-vision with Application Default Credentials
    try:
        from google.cloud import vision  # type: ignore

        client = vision.ImageAnnotatorClient()
        with open(image_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)
        if response.error.message:
            _LAST_GOOGLE_ERROR = response.error.message
            return None
        text = response.full_text_annotation.text if response.full_text_annotation else None
        return text.strip() if text and text.strip() else None
    except Exception as exc:
        _LAST_GOOGLE_ERROR = str(exc)
        return None


def _ocr_with_tesseract(image_path: str) -> Optional[str]:
    """Last resort: local Tesseract when installed."""
    global _LAST_TESSERACT_ERROR
    _LAST_TESSERACT_ERROR = None
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        _LAST_TESSERACT_ERROR = "pytesseract not installed"
        return None

    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip() if text and text.strip() else None
    except Exception as exc:
        _LAST_TESSERACT_ERROR = str(exc)
        return None


def _clean_field(value: Optional[str]) -> Optional[str]:
    """Drop empty values and LLM prompt placeholders."""
    if value is None:
        return None
    cleaned = value.strip().strip("\"'`")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    lowered = cleaned.lower()
    # Reject angle-bracket placeholders and obvious template tokens
    if re.fullmatch(r"<[^>]+>", cleaned) or (cleaned.startswith("<") and cleaned.endswith(">")):
        return None
    if lowered in {
        "<station>",
        "station",
        "<name>",
        "name",
        "<date>",
        "date",
        "station_name",
        "n/a",
        "na",
        "none",
        "null",
        "...",
        "unknown",
    }:
        return None
    return cleaned


def _first_match(patterns: list[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            value = _clean_field(match.group(1).strip(" :-|\t"))
            if value:
                return value
    return None


def parse_ticket_text(text: str) -> dict:
    """Parse source/destination/operator/date/ticket number from OCR or vision text."""
    from platform_colors import infer_mode_from_operator, normalize_mode

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
            r"\b(IRCTC|Indian Railways|Western Railway|Central Railway|Harbour|Metro|BMTC|DTC|BEST|Uber|Ola)\b",
            r"\b(ATVM[-\s]?Generated)\b",
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
    ticket_number = _first_match(
        [
            r"(?:ticket\s*(?:no|number|#)|uts|pnr|booking\s*id|ticketnumber)\s*[:\-]?\s*([A-Za-z0-9\-/]{4,40})",
            r"\b(?:UTS|PNR)[\s:#\-]*([A-Za-z0-9\-/]{4,40})\b",
            r"\b([0-9]{8,16})\b",
        ],
        cleaned,
    )
    mode_raw = _first_match(
        [r"(?:mode|platform)\s*[:\-]\s*(rail|metro|bus|cab|other)"],
        cleaned,
    )
    class_name = _first_match(
        [
            r"(?:class)\s*[:\-]\s*(.+)",
            r"\b(I{1,3}\s*ORD|II\s*ORD|I\s*ORD|FIRST|SECOND)\b",
        ],
        cleaned,
    )
    fare_raw = _first_match(
        [
            r"(?:fare|amount|rs\.?|₹)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)",
        ],
        cleaned,
    )

    # Fallback: "A to B" / "A TO B" on a single line (common on ATVM tickets)
    if not source or not destination:
        for line in cleaned.splitlines():
            line = line.strip()
            m = re.match(
                r"^([A-Za-z0-9 .'-]{2,40})\s+(?:➔|→|->|to)\s+([A-Za-z0-9 .'-]{2,40})$",
                line,
                flags=re.IGNORECASE,
            )
            if m:
                source = source or _clean_field(m.group(1))
                destination = destination or _clean_field(m.group(2))
                break

    operator_clean = _clean_field(operator)
    mode = normalize_mode(mode_raw) if mode_raw else infer_mode_from_operator(operator_clean, cleaned)
    fare = None
    if fare_raw:
        try:
            fare = float(fare_raw)
        except ValueError:
            fare = None

    return {
        "source": _clean_field(source),
        "destination": _clean_field(destination),
        "operator": operator_clean,
        "travel_date": _clean_field(travel_date),
        "ticket_number": _clean_field(ticket_number),
        "mode": mode,
        "class_name": _clean_field(class_name),
        "fare": fare,
        "qr_payload": None,
        "raw_text": cleaned[:4000] if cleaned else None,
    }


def _decode_qr_from_image(image_path: str) -> Optional[str]:
    """Best-effort QR decode; skip silently if libs unavailable."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as zbar_decode

        img = Image.open(image_path)
        results = zbar_decode(img)
        for r in results:
            data = r.data.decode("utf-8", errors="ignore").strip()
            if data:
                return data
    except Exception:
        pass
    try:
        import cv2

        img = cv2.imread(image_path)
        if img is None:
            return None
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        if data and data.strip():
            return data.strip()
    except Exception:
        pass
    return None


def extract_ticket_info(image_path: str) -> dict:
    """
    Run vision/OCR then parse fields.
    Order: Groq vision → Google Cloud Vision → Tesseract.
    Always returns a dict; missing fields are None so the client can edit.
    """
    text = None
    engine = None

    text = _ocr_with_groq_vision(image_path)
    if text:
        engine = "groq_vision"
    else:
        text = _ocr_with_google_vision(image_path)
        if text:
            engine = "google_vision"
        else:
            text = _ocr_with_tesseract(image_path)
            if text:
                engine = "tesseract"

    if not text:
        details = []
        if _LAST_GROQ_ERROR:
            details.append(f"Groq: {_LAST_GROQ_ERROR}")
        elif not os.getenv("GROQ_API_KEY"):
            details.append("Groq: GROQ_API_KEY missing in F:/way_transit/.env")
        if _LAST_GOOGLE_ERROR:
            details.append(f"Google Vision: {_LAST_GOOGLE_ERROR}")
        if _LAST_TESSERACT_ERROR:
            details.append(f"Tesseract: {_LAST_TESSERACT_ERROR}")
        hint = "; ".join(details) if details else "no engines available"
        qr_payload = _decode_qr_from_image(image_path)
        return {
            "source": None,
            "destination": None,
            "operator": None,
            "travel_date": None,
            "ticket_number": None,
            "mode": None,
            "class_name": None,
            "fare": None,
            "qr_payload": qr_payload,
            "raw_text": None,
            "ocr_engine": None,
            "message": f"OCR failed ({hint}). Enter stations manually.",
        }

    parsed = parse_ticket_text(text)
    qr_payload = _decode_qr_from_image(image_path)
    if qr_payload:
        parsed["qr_payload"] = qr_payload
        if not parsed.get("ticket_number"):
            parsed["ticket_number"] = qr_payload[:40]
    parsed["ocr_engine"] = engine
    parsed["message"] = f"Fields extracted via {engine}; review before saving."
    return parsed
