"""
POST /api/syllabus/parse

Accepts a PDF upload, extracts text, asks Claude to extract
structured assignment data, and upserts the assignments to Supabase.
"""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.deps import current_user_id
from db.supabase import get_supabase_client
from services import pdf_extractor
from services.claude_parser import parse_syllabus

router = APIRouter(prefix="/api/syllabus", tags=["syllabus"])

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/parse")
async def parse_syllabus_upload(
    file: UploadFile = File(...),
    user_id: str = Depends(current_user_id),
):
    # Validate
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    blob = await file.read()
    if len(blob) > MAX_PDF_BYTES:
        raise HTTPException(400, "PDF too large (>10MB)")
    if not blob:
        raise HTTPException(400, "Empty file")

    # Extract
    try:
        text = pdf_extractor.extract_text(blob)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"PDF extraction failed: {e}")

    if len(text.strip()) < 40:
        raise HTTPException(400, "No readable text in PDF")

    # Parse with Claude
    parsed = parse_syllabus(text)
    if parsed.get("_parse_error"):
        raise HTTPException(502, parsed["_parse_error"])

    sb = get_supabase_client()

    # Create the course row
    course_row = (
        sb.table("courses")
        .upsert(
            {
                "user_id": user_id,
                "name": parsed.get("course_name") or "Untitled course",
                "course_code": parsed.get("course_code", ""),
            },
        )
        .execute()
    )
    course_id = course_row.data[0]["id"] if course_row.data else None

    # Insert assignments
    rows = []
    for a in parsed.get("assignments", []):
        due_iso = a.get("due_at")
        # Sanity-check the datetime
        if due_iso:
            try:
                datetime.fromisoformat(due_iso.replace("Z", "+00:00"))
            except ValueError:
                due_iso = None
        rows.append(
            {
                "user_id": user_id,
                "course_id": course_id,
                "title": a.get("title", "Untitled"),
                "description": (a.get("description") or "")[:2000],
                "due_at": due_iso,
                "points_possible": a.get("points_possible"),
            }
        )

    if rows:
        sb.table("assignments").insert(rows).execute()

    return {
        "course": {
            "id": course_id,
            "name": parsed.get("course_name"),
            "code": parsed.get("course_code"),
        },
        "assignments_count": len(rows),
    }
