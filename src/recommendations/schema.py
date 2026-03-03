"""JSON schema definition and stdlib validation for recommendation output.

No external dependencies — pure stdlib + duck typing.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Canonical schema description (reference only; used in docstrings & prompts)
# ---------------------------------------------------------------------------
SCHEMA_DESCRIPTION = """
{
  "executive_summary": "<string>",
  "top_risks": [
    {
      "risk": "<string>",
      "impact": "<string>",
      "evidence": "<string>",
      "owner": "<string>",
      "next_action": "<string>"
    }
  ],
  "actions_next_24h": ["<string>"],
  "actions_next_7d": ["<string>"],
  "vendor_questions": ["<string>"],
  "kpis_to_watch": [
    {"kpi": "<string>", "reason": "<string>", "threshold": "<string>"}
  ],
  "ot_signals": ["<string>"],
  "ticketing_signals": ["<string>"],
  "incident_improvements": ["<string>"],
  "vendor_flags": ["<string>"],
  "assumptions": ["<string>"],
  "confidence": 0.0
}
"""

REQUIRED_KEYS = {
    "executive_summary",
    "top_risks",
    "actions_next_24h",
    "actions_next_7d",
    "vendor_questions",
    "kpis_to_watch",
    "ot_signals",
    "ticketing_signals",
    "incident_improvements",
    "vendor_flags",
    "assumptions",
    "confidence",
}

_TOP_RISK_KEYS = {"risk", "impact", "evidence", "owner", "next_action"}
_KPI_WATCH_KEYS = {"kpi", "reason", "threshold"}

# Arrays that must simply be lists (content is strings)
_ARRAY_KEYS = (
    "actions_next_24h", "actions_next_7d", "vendor_questions",
    "ot_signals", "ticketing_signals", "incident_improvements",
    "vendor_flags", "assumptions",
)


def validate(obj: Any) -> list[str]:
    """Return a list of validation errors (empty = valid)."""
    errors: list[str] = []

    if not isinstance(obj, dict):
        return ["Root must be a JSON object"]

    missing = REQUIRED_KEYS - obj.keys()
    if missing:
        errors.append(f"Missing required keys: {sorted(missing)}")

    if "executive_summary" in obj and not isinstance(obj["executive_summary"], str):
        errors.append("executive_summary must be a string")

    if "top_risks" in obj:
        if not isinstance(obj["top_risks"], list):
            errors.append("top_risks must be an array")
        else:
            for i, r in enumerate(obj["top_risks"]):
                if not isinstance(r, dict):
                    errors.append(f"top_risks[{i}] must be an object")
                else:
                    mk = _TOP_RISK_KEYS - r.keys()
                    if mk:
                        errors.append(f"top_risks[{i}] missing keys: {sorted(mk)}")

    for key in _ARRAY_KEYS:
        if key in obj and not isinstance(obj[key], list):
            errors.append(f"{key} must be an array")

    if "kpis_to_watch" in obj:
        if not isinstance(obj["kpis_to_watch"], list):
            errors.append("kpis_to_watch must be an array")
        else:
            for i, k in enumerate(obj["kpis_to_watch"]):
                if not isinstance(k, dict):
                    errors.append(f"kpis_to_watch[{i}] must be an object")
                else:
                    mk = _KPI_WATCH_KEYS - k.keys()
                    if mk:
                        errors.append(f"kpis_to_watch[{i}] missing keys: {sorted(mk)}")

    if "confidence" in obj:
        try:
            c = float(obj["confidence"])
            if not (0.0 <= c <= 1.0):
                errors.append("confidence must be between 0 and 1")
        except (TypeError, ValueError):
            errors.append("confidence must be a number")

    return errors


def is_valid(obj: Any) -> bool:
    return not validate(obj)


def is_valid(obj: Any) -> bool:
    return len(validate(obj)) == 0
