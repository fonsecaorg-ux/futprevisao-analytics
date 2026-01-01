from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from dateutil import parser

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s

def keyify(s: str) -> str:
    s = normalize_text(s).lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    s = s.replace(" ", "")
    return s

def parse_date_safe(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s:
        return None
    # football-data: dd/mm/yyyy
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    try:
        return parser.parse(s, dayfirst=True)
    except Exception:
        return None

def safe_float(x, default=0.0) -> float:
    try:
        if x is None: 
            return default
        if isinstance(x, str) and not x.strip():
            return default
        return float(x)
    except Exception:
        return default

def safe_int(x, default=0) -> int:
    try:
        if x is None:
            return default
        if isinstance(x, str) and not x.strip():
            return default
        return int(float(x))
    except Exception:
        return default
