from __future__ import annotations

import logging
import os
from typing import Any, Generator

from src.recommendations import heuristic
from src.recommendations import openai_adapter

logger = logging.getLogger(__name__)

NO_KEY_WARNING = (
    "Final authoritative recommendations are running in deterministic heuristic mode because "
    "no OpenAI API key is available."
)

FINAL_CALL_FAILED_WARNING = (
    "Final authoritative recommendations are staying on the deterministic heuristic baseline "
    "because the OpenAI final JSON call failed."
)


def _get_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY", "").strip() or None


def recommend(
    snapshot: dict[str, Any],
    *,
    api_key: str | None = None,
    final_model: str = openai_adapter.DEFAULT_FINAL_MODEL,
    temperature: float = 0.1,
    max_output_tokens: int = 1600,
) -> tuple[dict[str, Any], str | None, str]:
    resolved_key = api_key or _get_api_key()
    if not resolved_key:
        logger.info("No API key available. Using heuristic recommendations.")
        return heuristic.recommend(snapshot), NO_KEY_WARNING, "fallback_no_key"

    try:
        raw_text = openai_adapter.request_final_json(
            snapshot,
            api_key=resolved_key,
            model=final_model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        parsed = openai_adapter.parse_and_validate(raw_text)
        if parsed is not None:
            return parsed, None, "openai_final"
        logger.warning("OpenAI final response was invalid after one repair pass. Falling back to heuristic.")
    except Exception as exc:  # pragma: no cover - exercised in integration tests
        logger.warning("OpenAI final request failed: %s", exc)

    return heuristic.recommend(snapshot), FINAL_CALL_FAILED_WARNING, "fallback_error"


def stream_draft_preview(
    snapshot: dict[str, Any],
    *,
    api_key: str | None,
    preview_model: str = openai_adapter.DEFAULT_PREVIEW_MODEL,
    temperature: float = 0.2,
    max_output_tokens: int = 420,
) -> Generator[str, None, None]:
    resolved_key = api_key or _get_api_key()
    if not resolved_key:
        raise RuntimeError("No API key available for draft preview streaming.")
    yield from openai_adapter.stream_draft_preview(
        snapshot,
        api_key=resolved_key,
        model=preview_model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
