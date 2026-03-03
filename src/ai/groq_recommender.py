from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from groq import Groq


@dataclass(frozen=True)
class RecommendationResult:
    raw_text: str
    json: dict[str, Any] | None


def _build_prompt(snapshot: dict[str, Any]) -> str:
    return (
        "You are an operations readiness director responsible for a Day-One opening.\n"
        "Given the current performance snapshot, produce operational recommendations.\n\n"
        "Return ONLY a single, valid JSON object — no markdown fences, no explanatory text outside the JSON.\n"
        "The JSON must have EXACTLY these top-level keys:\n"
        "- executive_summary: string\n"
        "- top_risks: array of objects {risk, impact, evidence, owner, next_action}\n"
        "- actions_next_24h: array of strings\n"
        "- actions_next_7d: array of strings\n"
        "- vendor_questions: array of strings\n"
        "- kpis_to_watch: array of objects {kpi, reason, threshold}\n"
        "- ot_signals: array of strings (OT/BMS/CCTV/Access Control alarm observations)\n"
        "- ticketing_signals: array of strings (gate scan success rate / latency observations)\n"
        "- incident_improvements: array of strings (MTTA/MTTR improvement actions)\n"
        "- vendor_flags: array of strings (per-vendor SLA breach flags)\n"
        "- assumptions: array of strings\n"
        "- confidence: number between 0 and 1\n\n"
        "Rules:\n"
        "- Be specific and grounded only in the provided snapshot data — do not invent facts.\n"
        "- ot_signals and ticketing_signals MUST include at least one string (use 'No signals detected' if none).\n"
        "- incident_improvements and vendor_flags MUST include at least one string.\n"
        "- Prefer operational actions (runbooks, drills, escalation, monitoring, retest).\n"
        "- If something is missing, call it out as an assumption.\n"
        "- STRICT JSON ONLY: no code blocks, no markdown, no trailing commas.\n\n"
        f"SNAPSHOT:\n{snapshot}"
    )


class GroqRecommender:
    def __init__(self, api_key: str, model: str, temperature: float = 0.2, max_output_tokens: int = 1024):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def recommend_stream(self, snapshot: dict[str, Any]) -> Iterable[str]:
        """Yield text chunks via Groq streaming."""
        prompt = _build_prompt(snapshot)
        client = Groq(api_key=self.api_key)
        stream = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            txt = getattr(delta, "content", None)
            if txt:
                yield txt

    def recommend_once(self, snapshot: dict[str, Any]) -> str:
        prompt = _build_prompt(snapshot)
        client = Groq(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            stream=False,
        )
        return resp.choices[0].message.content or ""
