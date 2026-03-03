"""Recommendation service: public entry point.

Tries Groq if an API key is available; falls back to heuristic on any error.
Never raises — always returns a valid recommendation dict.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Generator

from src.recommendations import heuristic
from src.recommendations import groq_adapter as _groq
from src.recommendations.schema import is_valid

logger = logging.getLogger(__name__)

_FALLBACK_NOTE = (
    "⚠️ Groq recommendations unavailable (offline mode or API error). "
    "Using heuristic recommendations based on current data."
)


def _get_api_key() -> str | None:
    """Return API key from env; never from secrets (UI layer handles st.secrets)."""
    return os.environ.get("GROQ_API_KEY", "").strip() or None


def recommend(
    snapshot: dict[str, Any],
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.2,
    max_output_tokens: int = 1536,
    stream: bool = False,
) -> tuple[dict[str, Any], str | None]:
    """Return (recommendation_dict, warning_message_or_None).

    - recommendation_dict always satisfies the canonical schema.
    - warning_message is set when heuristic fallback was used.
    """
    resolved_key = api_key or _get_api_key()

    if not resolved_key:
        logger.warning("No API key found in environment or secrets. Falling back to heuristic.")
        return heuristic.recommend(snapshot), _FALLBACK_NOTE

    for attempt in range(2):
        try:
            raw = _groq.call_groq_once(
                snapshot=snapshot,
                api_key=resolved_key,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            parsed = _groq.parse_and_validate(raw)
            if parsed is not None and is_valid(parsed):
                return parsed, None
            logger.warning("service: groq output invalid after repair; using heuristic")
        except Exception as exc:
            logger.warning("groq attempt %s failed (%s)", attempt + 1, exc)

    logger.exception("groq all attempts failed; falling back")
    return heuristic.recommend(snapshot), _FALLBACK_NOTE


def recommend_stream(
    snapshot: dict[str, Any],
    api_key: str | None = None,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.2,
    max_output_tokens: int = 1536,
) -> Generator[str, None, None]:
    """Yield raw text chunks from Groq streaming call.

    Raises RuntimeError if no key is available (caller should check first).
    """
    resolved_key = api_key or _get_api_key()
    if not resolved_key:
        raise RuntimeError("No API key available for streaming")
    yield from _groq.call_groq_stream(
        snapshot=snapshot,
        api_key=resolved_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
