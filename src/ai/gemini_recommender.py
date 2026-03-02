from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from google import genai
from google.genai import types


@dataclass(frozen=True)
class RecommendationResult:
    raw_text: str
    json: dict[str, Any] | None


def _build_prompt(snapshot: dict[str, Any]) -> str:
    return (
        "You are an operations readiness director responsible for a Day-One opening.\n"
        "Given the current performance snapshot, produce operational recommendations.\n\n"
        "Return ONLY a single JSON object with the following keys:\n"
        "- executive_summary: string\n"
        "- top_risks: array of objects {risk, impact, evidence, owner, next_action}\n"
        "- actions_next_24h: array of strings\n"
        "- actions_next_7d: array of strings\n"
        "- vendor_questions: array of strings\n"
        "- kpis_to_watch: array of objects {kpi, reason, threshold}\n"
        "- assumptions: array of strings\n"
        "- confidence: number between 0 and 1\n\n"
        "Rules:\n"
        "- Be specific and evidence-linked.\n"
        "- Prefer operational actions (runbooks, drills, escalation, monitoring, retest).\n"
        "- If something is missing, call it out as an assumption.\n\n"
        f"SNAPSHOT:\n{snapshot}"
    )


class GeminiRecommender:
    def __init__(self, api_key: str, model: str, temperature: float = 0.2, max_output_tokens: int = 1024):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def recommend_stream(self, snapshot: dict[str, Any]) -> Iterable[str]:
        """Yield text chunks."""
        prompt = _build_prompt(snapshot)
        client = genai.Client(api_key=self.api_key)
        cfg = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )
        for chunk in client.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=cfg,
        ):
            # chunk.text is the simplest stable property in official examples
            txt = getattr(chunk, "text", None)
            if txt:
                yield txt

    def recommend_once(self, snapshot: dict[str, Any]) -> str:
        prompt = _build_prompt(snapshot)
        client = genai.Client(api_key=self.api_key)
        cfg = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )
        resp = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=cfg,
        )
        return getattr(resp, "text", "") or ""
