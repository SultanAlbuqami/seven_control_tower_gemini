from __future__ import annotations

import json
import re
from typing import Any


_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_FIRST_OBJ_RE = re.compile(r"(\{.*\})", re.DOTALL)


def extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort extraction of a JSON object from model output."""
    if not text:
        return None

    m = _JSON_BLOCK_RE.search(text)
    if m:
        candidate = m.group(1).strip()
        return _loads(candidate)

    m2 = _FIRST_OBJ_RE.search(text)
    if m2:
        candidate = m2.group(1).strip()
        return _loads(candidate)

    return None


def _loads(candidate: str) -> dict[str, Any] | None:
    try:
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            return obj
        return None
    except Exception:
        return None
