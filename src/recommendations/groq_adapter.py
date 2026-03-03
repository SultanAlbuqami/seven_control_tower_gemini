from __future__ import annotations

import logging
from typing import Any, Generator

from src.ai.groq_recommender import GroqRecommender
from src.recommendations.schema import is_valid, repair_response
from src.utils.json_utils import extract_json

logger = logging.getLogger(__name__)

DEFAULT_PREVIEW_MODEL = "llama-3.1-8b-instant"
DEFAULT_FINAL_MODEL = "llama-3.3-70b-versatile"


def stream_draft_preview(
    snapshot: dict[str, Any],
    *,
    api_key: str,
    model: str = DEFAULT_PREVIEW_MODEL,
    temperature: float = 0.2,
    max_output_tokens: int = 420,
) -> Generator[str, None, None]:
    recommender = GroqRecommender(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    yield from recommender.stream_preview(snapshot)


def request_final_json(
    snapshot: dict[str, Any],
    *,
    api_key: str,
    model: str = DEFAULT_FINAL_MODEL,
    temperature: float = 0.1,
    max_output_tokens: int = 1600,
) -> str:
    recommender = GroqRecommender(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    return recommender.request_final_json(snapshot)


def parse_and_validate(raw_text: str) -> dict[str, Any] | None:
    payload = extract_json(raw_text)
    if payload is None:
        logger.warning("Groq final response did not contain extractable JSON.")
        return None
    if is_valid(payload):
        return payload

    repaired = repair_response(payload)
    if repaired is not None:
        logger.warning("Groq response required one local repair pass before validation.")
        return repaired

    logger.warning("Groq response failed schema validation after one repair attempt.")
    return None
