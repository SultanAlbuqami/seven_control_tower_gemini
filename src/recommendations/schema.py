from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

STATUS_VALUES = {"OK", "WARN", "CRIT"}
GO_NO_GO_VALUES = {"GO", "HOLD"}

REQUIRED_KEYS = {
    "summary",
    "top_risks",
    "next_actions",
    "incident_improvements",
    "vendor_flags",
    "ot_signals",
    "ticketing_signals",
}

SUMMARY_KEYS = {"headline", "status", "go_no_go", "confidence", "rationale"}
TOP_RISK_KEYS = {"title", "status", "impact", "owner", "evidence", "trace_refs"}
NEXT_ACTION_KEYS = {"window", "owner", "action", "expected_outcome", "trace_refs"}
INCIDENT_IMPROVEMENT_KEYS = {"title", "status", "detail", "metric"}
VENDOR_FLAG_KEYS = {"vendor", "status", "detail", "trace_refs"}
SIGNAL_KEYS = {"signal", "status", "detail", "trace_refs"}

SCHEMA_DESCRIPTION = """
{
  "summary": {
    "headline": "string",
    "status": "OK | WARN | CRIT",
    "go_no_go": "GO | HOLD",
    "confidence": 0.0,
    "rationale": ["string"]
  },
  "top_risks": [
    {
      "title": "string",
      "status": "OK | WARN | CRIT",
      "impact": "string",
      "owner": "string",
      "evidence": "string",
      "trace_refs": ["string"]
    }
  ],
  "next_actions": [
    {
      "window": "0-24h | 2-7d",
      "owner": "string",
      "action": "string",
      "expected_outcome": "string",
      "trace_refs": ["string"]
    }
  ],
  "incident_improvements": [
    {
      "title": "string",
      "status": "OK | WARN | CRIT",
      "detail": "string",
      "metric": "string"
    }
  ],
  "vendor_flags": [
    {
      "vendor": "string",
      "status": "OK | WARN | CRIT",
      "detail": "string",
      "trace_refs": ["string"]
    }
  ],
  "ot_signals": [
    {
      "signal": "string",
      "status": "OK | WARN | CRIT",
      "detail": "string",
      "trace_refs": ["string"]
    }
  ],
  "ticketing_signals": [
    {
      "signal": "string",
      "status": "OK | WARN | CRIT",
      "detail": "string",
      "trace_refs": ["string"]
    }
  ]
}
""".strip()


def empty_response() -> dict[str, Any]:
    return {
        "summary": {
            "headline": "No recommendation data available.",
            "status": "WARN",
            "go_no_go": "HOLD",
            "confidence": 0.0,
            "rationale": [],
        },
        "top_risks": [],
        "next_actions": [],
        "incident_improvements": [],
        "vendor_flags": [],
        "ot_signals": [],
        "ticketing_signals": [],
    }


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _validate_item_keys(section: str, item: Any, required_keys: set[str], index: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(item, dict):
        return [f"{section}[{index}] must be an object"]
    missing = required_keys - item.keys()
    if missing:
        errors.append(f"{section}[{index}] missing keys: {sorted(missing)}")
    status = item.get("status")
    if "status" in required_keys and status not in STATUS_VALUES:
        errors.append(f"{section}[{index}].status must be one of {sorted(STATUS_VALUES)}")
    trace_refs = item.get("trace_refs")
    if "trace_refs" in required_keys and not _is_string_list(trace_refs):
        errors.append(f"{section}[{index}].trace_refs must be an array of strings")
    return errors


def validate(obj: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(obj, dict):
        return ["Root must be a JSON object"]

    missing = REQUIRED_KEYS - obj.keys()
    if missing:
        errors.append(f"Missing required keys: {sorted(missing)}")

    summary = obj.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
    else:
        missing_summary = SUMMARY_KEYS - summary.keys()
        if missing_summary:
            errors.append(f"summary missing keys: {sorted(missing_summary)}")
        if summary.get("status") not in STATUS_VALUES:
            errors.append(f"summary.status must be one of {sorted(STATUS_VALUES)}")
        if summary.get("go_no_go") not in GO_NO_GO_VALUES:
            errors.append(f"summary.go_no_go must be one of {sorted(GO_NO_GO_VALUES)}")
        if not _is_string_list(summary.get("rationale")):
            errors.append("summary.rationale must be an array of strings")
        try:
            confidence = float(summary.get("confidence"))
            if not (0.0 <= confidence <= 1.0):
                errors.append("summary.confidence must be between 0 and 1")
        except (TypeError, ValueError):
            errors.append("summary.confidence must be a number")

    section_rules = {
        "top_risks": TOP_RISK_KEYS,
        "next_actions": NEXT_ACTION_KEYS,
        "incident_improvements": INCIDENT_IMPROVEMENT_KEYS,
        "vendor_flags": VENDOR_FLAG_KEYS,
        "ot_signals": SIGNAL_KEYS,
        "ticketing_signals": SIGNAL_KEYS,
    }
    for section, required_keys in section_rules.items():
        value = obj.get(section)
        if not isinstance(value, list):
            errors.append(f"{section} must be an array")
            continue
        for index, item in enumerate(value):
            errors.extend(_validate_item_keys(section, item, required_keys, index))

    return errors


def is_valid(obj: Any) -> bool:
    return not validate(obj)


def _coerce_trace_refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _coerce_summary(value: Any) -> dict[str, Any]:
    baseline = empty_response()["summary"]
    if isinstance(value, str):
        baseline["headline"] = value.strip() or baseline["headline"]
        return baseline
    if not isinstance(value, dict):
        return baseline
    baseline["headline"] = str(value.get("headline", value.get("summary", baseline["headline"]))).strip() or baseline["headline"]
    status = str(value.get("status", "WARN")).upper()
    baseline["status"] = status if status in STATUS_VALUES else "WARN"
    go_no_go = str(value.get("go_no_go", "HOLD")).upper()
    baseline["go_no_go"] = go_no_go if go_no_go in GO_NO_GO_VALUES else "HOLD"
    try:
        baseline["confidence"] = min(1.0, max(0.0, float(value.get("confidence", 0.0))))
    except (TypeError, ValueError):
        baseline["confidence"] = 0.0
    baseline["rationale"] = _coerce_string_list(value.get("rationale"))
    return baseline


def _coerce_top_risk(item: Any) -> dict[str, Any]:
    if isinstance(item, str):
        return {
            "title": item,
            "status": "WARN",
            "impact": "",
            "owner": "Unassigned",
            "evidence": "",
            "trace_refs": [],
        }
    if not isinstance(item, dict):
        return {
            "title": "Risk item",
            "status": "WARN",
            "impact": "",
            "owner": "Unassigned",
            "evidence": "",
            "trace_refs": [],
        }
    status = str(item.get("status", "WARN")).upper()
    return {
        "title": str(item.get("title", item.get("risk", "Risk item"))),
        "status": status if status in STATUS_VALUES else "WARN",
        "impact": str(item.get("impact", "")),
        "owner": str(item.get("owner", "Unassigned")),
        "evidence": str(item.get("evidence", "")),
        "trace_refs": _coerce_trace_refs(item.get("trace_refs")),
    }


def _coerce_next_action(item: Any) -> dict[str, Any]:
    if isinstance(item, str):
        return {
            "window": "0-24h",
            "owner": "Ops Readiness Lead",
            "action": item,
            "expected_outcome": "",
            "trace_refs": [],
        }
    if not isinstance(item, dict):
        return {
            "window": "0-24h",
            "owner": "Ops Readiness Lead",
            "action": "Review readiness posture",
            "expected_outcome": "",
            "trace_refs": [],
        }
    return {
        "window": str(item.get("window", "0-24h")),
        "owner": str(item.get("owner", "Ops Readiness Lead")),
        "action": str(item.get("action", item.get("next_action", "Review readiness posture"))),
        "expected_outcome": str(item.get("expected_outcome", item.get("impact", ""))),
        "trace_refs": _coerce_trace_refs(item.get("trace_refs")),
    }


def _coerce_incident_improvement(item: Any) -> dict[str, Any]:
    if isinstance(item, str):
        return {
            "title": item,
            "status": "WARN",
            "detail": "",
            "metric": "Incident discipline",
        }
    if not isinstance(item, dict):
        return {
            "title": "Incident discipline",
            "status": "WARN",
            "detail": "",
            "metric": "Incident discipline",
        }
    status = str(item.get("status", "WARN")).upper()
    return {
        "title": str(item.get("title", "Incident discipline")),
        "status": status if status in STATUS_VALUES else "WARN",
        "detail": str(item.get("detail", item.get("reason", ""))),
        "metric": str(item.get("metric", "Incident discipline")),
    }


def _coerce_vendor_flag(item: Any) -> dict[str, Any]:
    if isinstance(item, str):
        return {"vendor": "Vendor", "status": "WARN", "detail": item, "trace_refs": []}
    if not isinstance(item, dict):
        return {"vendor": "Vendor", "status": "WARN", "detail": "", "trace_refs": []}
    status = str(item.get("status", "WARN")).upper()
    return {
        "vendor": str(item.get("vendor", "Vendor")),
        "status": status if status in STATUS_VALUES else "WARN",
        "detail": str(item.get("detail", item.get("impact", ""))),
        "trace_refs": _coerce_trace_refs(item.get("trace_refs")),
    }


def _coerce_signal(item: Any) -> dict[str, Any]:
    if isinstance(item, str):
        return {"signal": item, "status": "WARN", "detail": "", "trace_refs": []}
    if not isinstance(item, dict):
        return {"signal": "Signal", "status": "WARN", "detail": "", "trace_refs": []}
    status = str(item.get("status", "WARN")).upper()
    return {
        "signal": str(item.get("signal", item.get("title", "Signal"))),
        "status": status if status in STATUS_VALUES else "WARN",
        "detail": str(item.get("detail", item.get("reason", ""))),
        "trace_refs": _coerce_trace_refs(item.get("trace_refs")),
    }


def repair_response(obj: Any) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        return None

    repaired = deepcopy(empty_response())
    repaired["summary"] = _coerce_summary(obj.get("summary", obj.get("executive_summary")))

    coercers: dict[str, Callable[[Any], dict[str, Any]]] = {
        "top_risks": _coerce_top_risk,
        "next_actions": _coerce_next_action,
        "incident_improvements": _coerce_incident_improvement,
        "vendor_flags": _coerce_vendor_flag,
        "ot_signals": _coerce_signal,
        "ticketing_signals": _coerce_signal,
    }

    aliases = {
        "next_actions": obj.get("next_actions", obj.get("actions_next_24h")),
        "vendor_flags": obj.get("vendor_flags"),
        "incident_improvements": obj.get("incident_improvements"),
        "ot_signals": obj.get("ot_signals"),
        "ticketing_signals": obj.get("ticketing_signals"),
        "top_risks": obj.get("top_risks"),
    }

    for section, coercer in coercers.items():
        source = aliases.get(section)
        if source is None and section == "next_actions":
            later_actions = obj.get("actions_next_7d")
            if later_actions:
                source = later_actions
        if source is None:
            repaired[section] = []
            continue
        values = source if isinstance(source, list) else [source]
        repaired[section] = [coercer(item) for item in values]

    return repaired if is_valid(repaired) else None
