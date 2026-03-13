"""
grade_extractor.py — Google Gemini Vision Extraction
=====================================================
Uses Google Gemini 2.0 Flash (free tier) to extract SNIST JNTUH
grade sheet data from uploaded PDF or image files.

Free tier: 15 requests/min, 1500 requests/day
No local model. No RAM hanging. Response in 3-8 seconds.
Get API key free: https://aistudio.google.com/app/apikey
"""

import os
import re
import json
import base64
import logging
from io import BytesIO

import fitz                         # PyMuPDF — PDF to image
from PIL import Image, ImageEnhance
import requests

from ..config import settings

logger = logging.getLogger(__name__)

# ── JNTUH grade points lookup ─────────────────────────────────────────────────
GRADE_POINTS = {
    "O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6,
    "C": 5,  "D": 4,  "P": 4, "F": 0,  "AB": 0,
    "S": 0,  "S*": 0, "NS": 0, "NS*": 0,
}


# ══════════════════════════════════════════════════════
# IMAGE PREPARATION
# ══════════════════════════════════════════════════════

def _prepare_image(file_path: str) -> tuple:
    """
    Convert uploaded file to JPEG bytes for Gemini.
    PDF: renders first page at 3x zoom (~216 DPI).
    Image: upscales to min 2500px on longest side.
    Returns (jpeg_bytes, mime_type).
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        doc = fitz.open(file_path)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0), alpha=False)
        doc.close()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"):
        img = Image.open(file_path).convert("RGB")
        w, h = img.size
        if max(w, h) < 2500:
            scale = 2500 / max(w, h)
            img = img.resize(
                (int(w * scale), int(h * scale)), Image.LANCZOS
            )
    else:
        raise ValueError(
            f"Unsupported file type: {ext}. Use PDF, JPG, or PNG."
        )

    # Enhance for better OCR on phone photos
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Sharpness(img).enhance(1.5)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue(), "image/jpeg"


# ══════════════════════════════════════════════════════
# EXTRACTION PROMPT
# ══════════════════════════════════════════════════════

EXTRACTION_PROMPT = """You are reading a JNTUH autonomous institution grade 
sheet from SNIST (Sreenidhi Institute of Science and Technology), Hyderabad.

Extract ALL information from this grade sheet image.
Return ONLY a valid JSON object. No explanation, no markdown, no code fences.
Start your response directly with { and end with }.

JSON structure to use:
{
  "hall_ticket_no": "alphanumeric e.g. 22311A12P9",
  "serial_no": "long number e.g. 2401092132795",
  "memo_no": "short code e.g. S362912",
  "student_name": "full student name",
  "father_name": "father/mother name",
  "branch": "e.g. INFORMATION TECHNOLOGY",
  "examination": "e.g. B.Tech I Year II Semester - A22 Regular",
  "semester_no": 2,
  "exam_month_year": "e.g. AUGUST 2023",
  "sgpa": 8.92,
  "cgpa": 8.92,
  "total_credits_this_semester": 19.5,
  "cumulative_credits": 37.0,
  "subjects_registered": 8,
  "subjects_appeared": 8,
  "subjects_passed": 8,
  "subjects": [
    {
      "sno": 1,
      "subject_code": "9HC12",
      "subject_name": "Advanced Calculus",
      "grade_letter": "A+",
      "grade_points": 9,
      "credits": 3.0,
      "is_backlog": false,
      "result": "P"
    }
  ]
}

Rules:
1. semester_no from examination text:
   I Year I Sem=1, I Year II Sem=2, II Year I Sem=3,
   II Year II Sem=4, III Year I Sem=5, III Year II Sem=6,
   IV Year I Sem=7, IV Year II Sem=8

2. grade_points — JNTUH 10-point scale:
   O=10, A+=9, A=8, B+=7, B=6, C=5, D=4, F=0, AB=0, S*=0

3. is_backlog: true ONLY for F, AB, NS, NS* grades

4. Include ALL subjects — even Induction Program (S* grade, 0 credits)

5. credits: exact value from CREDITS column (0, 1, 1.5, 2, 2.5, 3)

6. Use null for any field not visible in the image

Return ONLY the JSON. Nothing before {, nothing after }."""


# ══════════════════════════════════════════════════════
# GEMINI API CALL
# ══════════════════════════════════════════════════════

# Models to try in order (first with available free-tier quota wins)
_GEMINI_MODELS = [
    "gemini-2.5-flash",
    # "gemini-2.0-flash",
    # "gemini-2.0-flash-lite",
    # "gemini-2.0-flash-001",
    # "gemini-2.0-flash-lite-001",
]


def _call_gemini(image_bytes: bytes, mime_type: str) -> tuple:
    """
    Send image to Gemini Vision via REST API and return (raw_text, model_used).
    Tries models in order, skipping any that hit quota/404 errors.
    Uses direct REST API: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not set in .env file. "
            "Get your free key from https://aistudio.google.com/app/apikey "
            "then add to backend/.env: GEMINI_API_KEY=your_key_here"
        )

    # Convert image bytes to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    last_error = None
    for model_name in _GEMINI_MODELS:
        try:
            # Construct REST API URL
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

            # Prepare request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": EXTRACTION_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 8192
                }
            }

            # Make REST API call
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": settings.GEMINI_API_KEY
                },
                timeout=30
            )

            # Handle response
            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                logger.info(f"Gemini extraction succeeded with model: {model_name}")
                return text.strip(), model_name
            else:
                # Parse error
                err_json = response.json() if response.text else {}
                err_msg = err_json.get("error", {}).get("message", response.text)

                # Skip quota-exhausted or model-not-found errors and try next model
                if response.status_code in (429, 404) or "quota" in err_msg.lower():
                    logger.warning(f"Model {model_name} unavailable ({response.status_code}: {err_msg[:80]}), trying next...")
                    last_error = f"{response.status_code}: {err_msg}"
                    continue
                # Any other error (auth, network) — raise immediately
                raise ValueError(f"Gemini API error ({response.status_code}): {err_msg}")

        except requests.exceptions.RequestException as e:
            # Network error
            raise ValueError(f"Network error calling Gemini API: {e}")
        except Exception as e:
            # Unexpected error
            err_str = str(e)
            if "429" in err_str or "404" in err_str or "quota" in err_str.lower():
                logger.warning(f"Model {model_name} error ({err_str[:80]}), trying next...")
                last_error = e
                continue
            raise

    raise ValueError(
        f"All Gemini models hit quota limits. Try a different API key or wait a minute. "
        f"Get a fresh free key at https://aistudio.google.com/app/apikey "
        f"Last error: {last_error}"
    )


# ══════════════════════════════════════════════════════
# RESPONSE PARSING
# ══════════════════════════════════════════════════════

def _parse_response(raw: str) -> dict:
    """
    Parse Gemini's text response into Python dict.
    Strips any accidental markdown fences.
    Finds JSON by locating first { to last }.
    """
    # Strip markdown fences
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(
            l for l in lines
            if not l.strip().startswith("```")
        ).strip()

    # Extract JSON object
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    return json.loads(raw)


def _normalize(parsed: dict) -> dict:
    """
    Post-process:
    - Fix grade_points using our lookup table
    - Fix is_backlog flags
    - Validate semester_no range
    """
    for s in parsed.get("subjects", []):
        grade = str(s.get("grade_letter", "")).strip().upper()
        s["grade_letter"] = grade
        s["grade_points"] = GRADE_POINTS.get(grade, 0)
        s["is_backlog"] = grade in ("F", "AB", "NS", "NS*")

    sem = parsed.get("semester_no")
    if not isinstance(sem, int) or not (1 <= sem <= 8):
        exam = parsed.get("examination", "")
        parsed["semester_no"] = _detect_semester(exam)

    return parsed


def _detect_semester(text: str) -> int:
    """Parse semester number from examination field text."""
    text = text.upper()
    roman = {"I": 1, "II": 2, "III": 3, "IV": 4}
    m = re.search(
        r'(I{1,3}V?|IV)\s*YEAR\s*(I{1,3}|II?)\s*SEM', text
    )
    if m:
        yr = roman.get(m.group(1).strip(), 1)
        sm = roman.get(m.group(2).strip(), 1)
        return (yr - 1) * 2 + sm
    return 1


# ══════════════════════════════════════════════════════
# STATUS CHECK
# ══════════════════════════════════════════════════════

def get_gemini_status() -> dict:
    """
    Returns Gemini API configuration status.
    Called by GET /student/extraction-status endpoint.
    """
    key_set = bool(settings.GEMINI_API_KEY)
    return {
        "engine": "Google Gemini 2.5 Flash",
        "api_key_configured": key_set,
        "free_tier": "15 requests/min · 1500 requests/day",
        "recommendation": (
            "Ready! Gemini Vision active."
            if key_set else
            "Add GEMINI_API_KEY to backend/.env — "
            "get free key at https://aistudio.google.com/app/apikey"
        )
    }


# ══════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════

def extract_from_file(file_path: str) -> dict:
    """
    Main entry point. Called from POST /student/extract-marksheet.

    1. Validate file type
    2. Convert to high-quality JPEG
    3. Send to Gemini Vision (tries multiple free models)
    4. Parse JSON response
    5. Normalize grade points
    6. Return structured dict for frontend review

    Always returns a dict. Even partial extraction is fine because
    the frontend review step lets students fix any errors.
    """
    ext = os.path.splitext(file_path)[1].lower()
    allowed = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    if ext not in allowed:
        raise ValueError(
            f"File type '{ext}' not supported. Use PDF, JPG, or PNG."
        )

    # Prepare image
    try:
        image_bytes, mime_type = _prepare_image(file_path)
    except Exception as e:
        raise ValueError(f"Could not read file: {e}")

    # Call Gemini (tries multiple models with fallback)
    try:
        raw_response, model_used = _call_gemini(image_bytes, mime_type)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Gemini API call failed: {e}")

    # Parse response
    try:
        parsed = _parse_response(raw_response)
    except json.JSONDecodeError:
        logger.error(
            f"Gemini returned invalid JSON. "
            f"First 300 chars: {raw_response[:300]}"
        )
        parsed = {}

    # Normalize
    parsed = _normalize(parsed)

    # Add metadata
    parsed["_extraction_method"] = f"Google Gemini ({model_used})"
    parsed["_subjects_found"] = len(parsed.get("subjects", []))

    if not parsed.get("subjects"):
        parsed["_warning"] = (
            "No subjects extracted automatically. "
            "Please fill in your grades manually using the form below."
        )

    return parsed
