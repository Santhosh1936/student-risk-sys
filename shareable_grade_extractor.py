"""
Standalone grade extractor using Google Gemini Vision.

This version is shareable across projects because it does not depend on
your app's internal settings module. The API key can be passed directly
or provided through the GEMINI_API_KEY environment variable.
"""

import base64
import json
import logging
import os
import re
from io import BytesIO
from typing import Optional, Tuple

import requests
from PIL import Image, ImageEnhance

try:
    import fitz  # PyMuPDF - PDF to image
except ImportError:
    fitz = None


logger = logging.getLogger(__name__)

GRADE_POINTS = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
    "D": 4,
    "P": 4,
    "F": 0,
    "AB": 0,
    "S": 0,
    "S*": 0,
    "NS": 0,
    "NS*": 0,
}

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

2. grade_points - JNTUH 10-point scale:
   O=10, A+=9, A=8, B+=7, B=6, C=5, D=4, F=0, AB=0, S*=0

3. is_backlog: true ONLY for F, AB, NS, NS* grades

4. Include ALL subjects - even Induction Program (S* grade, 0 credits)

5. credits: exact value from CREDITS column (0, 1, 1.5, 2, 2.5, 3)

6. Use null for any field not visible in the image

Return ONLY the JSON. Nothing before {, nothing after }."""

GEMINI_MODELS = [
    "gemini-2.5-flash",
]


def _get_api_key(api_key: Optional[str] = None) -> str:
    value = api_key or os.getenv("GEMINI_API_KEY", "")
    if not value:
        raise ValueError(
            "GEMINI_API_KEY is not set. Pass api_key='your_key' or set the "
            "GEMINI_API_KEY environment variable."
        )
    return value


def _prepare_image(file_path: str) -> Tuple[bytes, str]:
    """
    Convert a PDF or image into JPEG bytes for Gemini input.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        if fitz is None:
            raise ValueError(
                "PDF support requires PyMuPDF. Install with: pip install PyMuPDF"
            )
        doc = fitz.open(file_path)
        try:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0), alpha=False)
        finally:
            doc.close()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    elif ext in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}:
        img = Image.open(file_path).convert("RGB")
        w, h = img.size
        if max(w, h) < 2500:
            scale = 2500 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    else:
        raise ValueError(
            f"Unsupported file type: {ext}. Use PDF, JPG, PNG, BMP, TIFF, or WEBP."
        )

    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = ImageEnhance.Sharpness(img).enhance(1.5)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue(), "image/jpeg"


def _call_gemini(
    image_bytes: bytes,
    mime_type: str,
    api_key: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Send the prepared image to Gemini Vision and return (raw_text, model_used).
    """
    resolved_api_key = _get_api_key(api_key)
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    last_error = None

    for model_name in GEMINI_MODELS:
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent"
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": EXTRACTION_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_base64,
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 8192,
                },
            }

            response = requests.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": resolved_api_key,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("Gemini extraction succeeded with model: %s", model_name)
                return text.strip(), model_name

            try:
                err_json = response.json() if response.text else {}
            except ValueError:
                err_json = {}
            err_msg = err_json.get("error", {}).get("message", response.text)

            if response.status_code in (429, 404) or "quota" in err_msg.lower():
                logger.warning(
                    "Model %s unavailable (%s: %s), trying next...",
                    model_name,
                    response.status_code,
                    err_msg[:80],
                )
                last_error = f"{response.status_code}: {err_msg}"
                continue

            raise ValueError(f"Gemini API error ({response.status_code}): {err_msg}")

        except requests.exceptions.RequestException as exc:
            raise ValueError(f"Network error calling Gemini API: {exc}") from exc
        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "404" in err_str or "quota" in err_str.lower():
                logger.warning(
                    "Model %s error (%s), trying next...",
                    model_name,
                    err_str[:80],
                )
                last_error = err_str
                continue
            raise

    raise ValueError(
        "All Gemini models hit quota limits. Try another API key or wait a "
        f"minute. Last error: {last_error}"
    )


def _parse_response(raw: str) -> dict:
    """
    Parse Gemini text into a Python dictionary.
    """
    if "```" in raw:
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()

    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    return json.loads(raw)


def _detect_semester(text: str) -> int:
    """
    Infer semester number from examination text.
    """
    text = text.upper()
    roman = {"I": 1, "II": 2, "III": 3, "IV": 4}
    match = re.search(r"(I{1,3}V?|IV)\s*YEAR\s*(I{1,3}|II?)\s*SEM", text)
    if match:
        year = roman.get(match.group(1).strip(), 1)
        sem = roman.get(match.group(2).strip(), 1)
        return (year - 1) * 2 + sem
    return 1


def _normalize(parsed: dict) -> dict:
    """
    Normalize extracted fields for downstream usage.
    """
    for subject in parsed.get("subjects", []):
        grade = str(subject.get("grade_letter", "")).strip().upper()
        subject["grade_letter"] = grade
        subject["grade_points"] = GRADE_POINTS.get(grade, 0)
        subject["is_backlog"] = grade in {"F", "AB", "NS", "NS*"}

    semester = parsed.get("semester_no")
    if not isinstance(semester, int) or not (1 <= semester <= 8):
        parsed["semester_no"] = _detect_semester(parsed.get("examination", ""))

    return parsed


def get_gemini_status(api_key: Optional[str] = None) -> dict:
    """
    Return a simple readiness payload for UI or debugging.
    """
    key_set = bool(api_key or os.getenv("GEMINI_API_KEY", ""))
    return {
        "engine": "Google Gemini 2.5 Flash",
        "api_key_configured": key_set,
        "free_tier": "15 requests/min · 1500 requests/day",
        "recommendation": (
            "Ready! Gemini Vision active."
            if key_set
            else "Set GEMINI_API_KEY or pass api_key to extract_from_file()."
        ),
    }


def extract_from_file(file_path: str, api_key: Optional[str] = None) -> dict:
    """
    Extract structured grade data from a PDF or image file.
    """
    ext = os.path.splitext(file_path)[1].lower()
    allowed = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    if ext not in allowed:
        raise ValueError(
            f"File type '{ext}' not supported. Use PDF, JPG, or PNG."
        )

    try:
        image_bytes, mime_type = _prepare_image(file_path)
    except Exception as exc:
        raise ValueError(f"Could not read file: {exc}") from exc

    try:
        raw_response, model_used = _call_gemini(image_bytes, mime_type, api_key=api_key)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Gemini API call failed: {exc}") from exc

    try:
        parsed = _parse_response(raw_response)
    except json.JSONDecodeError:
        logger.error(
            "Gemini returned invalid JSON. First 300 chars: %s",
            raw_response[:300],
        )
        parsed = {}

    parsed = _normalize(parsed)
    parsed["_extraction_method"] = f"Google Gemini ({model_used})"
    parsed["_subjects_found"] = len(parsed.get("subjects", []))

    if not parsed.get("subjects"):
        parsed["_warning"] = (
            "No subjects extracted automatically. Please fill in grades manually."
        )

    return parsed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_path = "sample_gradesheet.pdf"

    print("Standalone Gemini grade extractor")
    print("Usage example:")
    print("  result = extract_from_file('sample_gradesheet.pdf', api_key='YOUR_KEY')")
    print(f"  Default demo path: {sample_path}")
