from __future__ import annotations

import logging
from typing import Any, Generator

from src.ai.openai_recommender import OpenAIRecommender
from src.recommendations.schema import is_valid, repair_response
from src.utils.json_utils import extract_json

logger = logging.getLogger(__name__)

DEFAULT_PREVIEW_MODEL = "gpt-4.1-mini"
DEFAULT_FINAL_MODEL = "gpt-4.1"


def stream_draft_preview(
    snapshot: dict[str, Any],
    *,
    api_key: str,
    model: str = DEFAULT_PREVIEW_MODEL,
    temperature: float = 0.2,
    max_output_tokens: int = 420,
) -> Generator[str, None, None]:
    recommender = OpenAIRecommender(
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
    recommender = OpenAIRecommender(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    return recommender.request_final_json(snapshot)


def parse_and_validate(raw_text: str) -> dict[str, Any] | None:
    payload = extract_json(raw_text)
    if payload is None:
        logger.warning("OpenAI final response did not contain extractable JSON.")
        return None
    if is_valid(payload):
        return payload

    repaired = repair_response(payload)
    if repaired is not None:
        logger.warning("OpenAI response required one local repair pass before validation.")
        return repaired

    logger.warning("OpenAI response failed schema validation after one repair attempt.")
    return None
