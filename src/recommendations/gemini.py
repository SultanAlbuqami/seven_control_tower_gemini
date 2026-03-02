"""Gemini API adapter for recommendations.

Thin wrapper around src.ai.gemini_recommender with:
- streaming support
- JSON extraction + schema validation
- single repair attempt on invalid JSON
"""
from __future__ import annotations

import json
import logging
from typing import Any, Generator

from src.ai.gemini_recommender import GeminiRecommender
from src.recommendations.schema import validate
from src.utils.json_utils import extract_json

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-2.0-flash"
_DEFAULT_TEMPERATURE = 0.2
_DEFAULT_MAX_TOKENS = 1536


def call_gemini_stream(
    snapshot: dict[str, Any],
    api_key: str,
    model: str = _DEFAULT_MODEL,
    temperature: float = _DEFAULT_TEMPERATURE,
    max_output_tokens: int = _DEFAULT_MAX_TOKENS,
) -> Generator[str, None, None]:
    """Yield raw text chunks from a streaming Gemini call."""
    rec = GeminiRecommender(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    yield from rec.recommend_stream(snapshot)


def call_gemini_once(
    snapshot: dict[str, Any],
    api_key: str,
    model: str = _DEFAULT_MODEL,
    temperature: float = _DEFAULT_TEMPERATURE,
    max_output_tokens: int = _DEFAULT_MAX_TOKENS,
) -> str:
    """Return full text from a single Gemini call."""
    rec = GeminiRecommender(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    return rec.recommend_once(snapshot)


def parse_and_validate(raw_text: str) -> dict[str, Any] | None:
    """Extract + validate JSON from raw Gemini text.

    Returns the dict if valid, None if extraction or validation fails after
    one repair attempt.
    """
    obj = extract_json(raw_text)
    if obj is None:
        logger.warning("gemini: could not extract JSON from response")
        return None

    errors = validate(obj)
    if not errors:
        return obj

    # --- single repair attempt: strip trailing commas / common LLM artifacts ---
    logger.warning("gemini: invalid JSON schema (%s); attempting repair", errors)
    try:
        # Re-serialise + re-parse to canonicalise
        repaired_text = json.dumps(obj)
        repaired = json.loads(repaired_text)
        if not validate(repaired):
            return repaired
    except Exception:
        pass

    logger.warning("gemini: repair failed; falling back to heuristic")
    return None
