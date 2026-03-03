from __future__ import annotations

import logging
import os
from typing import Any, Generator

from src.recommendations import heuristic
from src.recommendations import groq_adapter

logger = logging.getLogger(__name__)

OFFLINE_WARNING = (
    "Final authoritative recommendations are running in deterministic heuristic mode. "
    "No Groq API key was available or the final JSON call failed."
)


def _get_api_key() -> str | None:
    return os.environ.get("GROQ_API_KEY", "").strip() or None


def recommend(
    snapshot: dict[str, Any],
    *,
    api_key: str | None = None,
    final_model: str = groq_adapter.DEFAULT_FINAL_MODEL,
    temperature: float = 0.1,
    max_output_tokens: int = 1600,
) -> tuple[dict[str, Any], str | None, str]:
    resolved_key = api_key or _get_api_key()
    if not resolved_key:
        logger.info("No API key available. Using heuristic recommendations.")
        return heuristic.recommend(snapshot), OFFLINE_WARNING, "heuristic"

    try:
        raw_text = groq_adapter.request_final_json(
            snapshot,
            api_key=resolved_key,
            model=final_model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        parsed = groq_adapter.parse_and_validate(raw_text)
        if parsed is not None:
            return parsed, None, "groq_final"
        logger.warning("Groq final response was invalid after one repair pass. Falling back to heuristic.")
    except Exception as exc:  # pragma: no cover - exercised in integration tests
        logger.warning("Groq final request failed: %s", exc)

    return heuristic.recommend(snapshot), OFFLINE_WARNING, "heuristic"


def stream_draft_preview(
    snapshot: dict[str, Any],
    *,
    api_key: str | None,
    preview_model: str = groq_adapter.DEFAULT_PREVIEW_MODEL,
    temperature: float = 0.2,
    max_output_tokens: int = 420,
) -> Generator[str, None, None]:
    resolved_key = api_key or _get_api_key()
    if not resolved_key:
        raise RuntimeError("No API key available for draft preview streaming.")
    yield from groq_adapter.stream_draft_preview(
        snapshot,
        api_key=resolved_key,
        model=preview_model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
