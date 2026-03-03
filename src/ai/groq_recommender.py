from __future__ import annotations

import json
from typing import Any, Iterable

from groq import Groq

from src.recommendations.schema import SCHEMA_DESCRIPTION


def _snapshot_block(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, sort_keys=True)


def _preview_prompt(snapshot: dict[str, Any]) -> str:
    return (
        "You are drafting a fast executive preview for an operations readiness control tower.\n"
        "Summarize the situation in short plain text only.\n"
        "Rules:\n"
        "- Use a short heading line, then 4 to 6 concise bullets.\n"
        "- Mark the posture as OK, WARN, or CRIT.\n"
        "- Mention readiness, incidents, OT, ticketing, and vendors if relevant.\n"
        "- Do not output JSON.\n"
        "- Do not use markdown tables.\n\n"
        f"SNAPSHOT:\n{_snapshot_block(snapshot)}"
    )


def _final_prompt(snapshot: dict[str, Any]) -> str:
    return (
        "You are the authoritative recommendation engine for an operations readiness control tower.\n"
        "Return a single valid JSON object only. No markdown. No prose before or after the JSON.\n"
        "Use the exact schema below and do not add extra top-level keys.\n\n"
        f"{SCHEMA_DESCRIPTION}\n\n"
        "Rules:\n"
        "- Ground every statement in the provided snapshot only.\n"
        "- Use statuses OK, WARN, or CRIT only.\n"
        "- Use GO or HOLD only for summary.go_no_go.\n"
        "- Keep trace_refs concise and specific.\n"
        "- If a section has no issues, it may be an empty array.\n"
        "- summary.rationale must still explain the posture.\n"
        "- JSON only.\n\n"
        f"SNAPSHOT:\n{_snapshot_block(snapshot)}"
    )


class GroqRecommender:
    def __init__(self, api_key: str, model: str, *, temperature: float = 0.1, max_output_tokens: int = 1400):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def _client(self) -> Groq:
        return Groq(api_key=self.api_key)

    def stream_preview(self, snapshot: dict[str, Any]) -> Iterable[str]:
        stream = self._client().chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": _preview_prompt(snapshot)}],
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

    def request_final_json(self, snapshot: dict[str, Any]) -> str:
        response = self._client().chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": _final_prompt(snapshot)}],
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            stream=False,
        )
        return response.choices[0].message.content or ""
