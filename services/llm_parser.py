"""
Gemini-powered syllabus parser (free tier via Google AI Studio).

Takes raw PDF text from a syllabus and asks Gemini to pull out
structured assignment/due-date data as JSON.
"""

from __future__ import annotations

import json
import os
from typing import Any

from google import genai
from google.genai import types

_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
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


def _client() -> genai.Client:
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def parse_syllabus(text: str) -> dict[str, Any]:
    """Return a dict of {course_name, course_code, assignments:[...]}."""
    if not text.strip():
        return {"course_name": "", "course_code": "", "assignments": []}

    client = _client()
    resp = client.models.generate_content(
        model=_MODEL,
        contents=f"Parse this syllabus and return ONLY JSON:\n\n{text[:40000]}",
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            max_output_tokens=_MAX_TOKENS,
            response_mime_type="application/json",
        ),
    )

    raw = (resp.text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "course_name": "",
            "course_code": "",
            "assignments": [],
            "_parse_error": "Gemini returned non-JSON",
            "_raw": raw[:500],
        }
