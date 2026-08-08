"""Platform mode → display color for unified wallet tickets."""
from __future__ import annotations

import re
from typing import Optional

MODE_COLORS = {
    "rail": "#B45309",
    "metro": "#7C3AED",
    "bus": "#DC2626",
    "cab": "#0D9488",
    "other": "#64748B",
}

MODE_LABELS = {
    "rail": "Suburban Rail",
    "metro": "Metro",
    "bus": "Bus",
    "cab": "Cab/Auto",
    "other": "Other",
}


def normalize_mode(value: Optional[str]) -> str:
    if not value:
        return "other"
    v = value.strip().lower()
    if v in MODE_COLORS:
        return v
    return "other"


def color_for_mode(mode: Optional[str], operator_color: Optional[str] = None) -> str:
    if operator_color and re.fullmatch(r"#?[0-9A-Fa-f]{6}", operator_color.strip()):
        c = operator_color.strip()
        return c if c.startswith("#") else f"#{c}"
    return MODE_COLORS.get(normalize_mode(mode), MODE_COLORS["other"])


def infer_mode_from_operator(operator: Optional[str], raw_text: Optional[str] = None) -> str:
    blob = f"{operator or ''} {raw_text or ''}".lower()
    if any(k in blob for k in ("metro", "line 1", "line 2", "line 3", "aqua line")):
        return "metro"
    if any(k in blob for k in ("best", "bus", "b.e.s.t")):
        return "bus"
    if any(k in blob for k in ("uber", "ola", "cab", "auto", "taxi", "rapido")):
        return "cab"
    if any(
        k in blob
        for k in (
            "railway",
            "western",
            "central",
            "harbour",
            "atvm",
            "uts",
            "irctc",
            "suburban",
            "local train",
            "happy journey",
        )
    ):
        return "rail"
    return "other"
