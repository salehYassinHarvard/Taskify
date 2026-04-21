"""
Claude-powered syllabus parser.

Takes raw PDF text from a syllabus and asks Claude to pull out
structured assignment/due-date data as JSON.
"""

from __future__ import annotations

import json
import os
from typing import Any

from anthropic import Anthropic

_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
_MAX_TOKENS = 4000


_SYSTEM_PROMPT = """You are a precise syllabus parser. Given a course syllabus, \
extract every assignment, quiz, exam, project, and reading with a due date.

Output STRICT JSON matching this schema (no prose, no markdown fences):
{
  "course_name": "string",
  "course_code": "string or empty",
  "assignments": [
    {
      "title": "string",
      "description": "string (brief, <200 chars)",
      "due_at": "ISO 8601 datetime or null",
      "points_possible": number or null,
      "type": "assignment|quiz|exam|project|reading|other"
    }
  ]
}

Rules:
- If a year is not given, assume the current academic year.
- Use null, not the string "null".
- If a date has no time, use 23:59 local (student-friendly default).
- Do NOT invent assignments that aren't clearly stated.
- Times with no timezone -> treat as local/naive (omit timezone in ISO)."""


def _extract_client() -> Anthropic:
    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def parse_syllabus(text: str) -> dict[str, Any]:
    """Return a dict of {course_name, course_code, assignments:[...]}."""
    if not text.strip():
        return {"course_name": "", "course_code": "", "assignments": []}

    client = _extract_client()
    msg = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Parse this syllabus and return ONLY JSON:\n\n{text[:40000]}",
            }
        ],
    )

    # Claude returns a list of content blocks; grab first text block
    raw = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            raw = block.text
            break

    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Graceful fallback — don't crash the caller
        return {
            "course_name": "",
            "course_code": "",
            "assignments": [],
            "_parse_error": "Claude returned non-JSON",
            "_raw": raw[:500],
        }
