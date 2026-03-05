# backend/app/services/grade_extractor.py
#
# Core OCR/PDF extraction service for JNTUH SNIST grade sheets.
# Supports: PDF (via PyMuPDF), JPG/PNG (via Pillow + Tesseract OCR).
#
import re
import os
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# ── Configure Tesseract binary path (Windows) ────────────────────────────
tesseract_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
]
for _path in tesseract_paths:
    if os.path.exists(_path):
        pytesseract.pytesseract.tesseract_cmd = _path
        break

# ── JNTUH grade → grade points ────────────────────────────────────────────
GRADE_POINTS = {
    "O":   10,
    "A+":  9,
    "A":   8,
    "B+":  7,
    "B":   6,
    "C":   5,
    "D":   4,
    "P":   4,
    "F":   0,
    "AB":  0,
    "S":   0,
    "S*":  0,
    "NS":  0,
    "NS*": 0,
}

# ── Semester number lookup ────────────────────────────────────────────────
SEMESTER_MAP = {
    ("I",   "I"):  1, ("I",   "II"): 2,
    ("II",  "I"):  3, ("II",  "II"): 4,
    ("III", "I"):  5, ("III", "II"): 6,
    ("IV",  "I"):  7, ("IV",  "II"): 8,
}


# ─────────────────────────────────────────────────────────────────────────────
# Image preprocessing + OCR
# ─────────────────────────────────────────────────────────────────────────────

def _ocr_image(file_path: str) -> str:
    """
    Robust OCR for phone-photographed grade sheets.
    Applies: EXIF auto-rotation, upscale, grayscale, adaptive threshold,
    sharpening, then Tesseract with auto-OSD.
    """
    from PIL import ImageFilter, ImageEnhance, ImageOps
    import io

    img = Image.open(file_path)

    # 1. Auto-rotate based on EXIF orientation (phone photos are often rotated)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # 2. Convert to RGB then grayscale
    img = img.convert("RGB").convert("L")

    # 3. Upscale to at least 3000px wide for better OCR accuracy
    w, h = img.size
    if w < 3000:
        scale = 3000 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 4. Enhance contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # 5. Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    img = img.filter(ImageFilter.SHARPEN)

    # 6. Binarize with Otsu-like threshold using point()
    img = img.point(lambda x: 255 if x > 150 else 0, "L")

    # 7. Run Tesseract — try psm 1 (auto-OSD) first, fallback to psm 3 and psm 6
    configs = [
        "--oem 3 --psm 1",   # auto orientation + layout
        "--oem 3 --psm 3",   # fully automatic page segmentation
        "--oem 3 --psm 6",   # uniform block of text
    ]
    best_text = ""
    for cfg in configs:
        try:
            text = pytesseract.image_to_string(img, config=cfg)
            # Pick longest result (more text = better parse)
            if len(text.strip()) > len(best_text.strip()):
                best_text = text
        except Exception:
            continue

    return best_text


# ─────────────────────────────────────────────────────────────────────────────
# Text extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from a PDF or image file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        parts = []
        doc = fitz.open(file_path)
        for page in doc:
            parts.append(page.get_text())
        doc.close()
        return "\n".join(parts)

    elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
        return _ocr_image(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF, JPG, or PNG.")


# ─────────────────────────────────────────────────────────────────────────────
# Semester detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_semester_number(examination_text: str) -> int:
    """Parse semester number from JNTUH examination field string."""
    text = examination_text.upper()

    roman_map = {
        "I": 1, "II": 2, "III": 3, "IV": 4,
        "1ST": 1, "2ND": 2, "3RD": 3, "4TH": 4,
        "1": 1, "2": 2, "3": 3, "4": 4,
    }

    year_match = re.search(
        r'(I{1,3}V?|IV|[1-4](?:ST|ND|RD|TH)?)\s*YEAR\s*(I{1,3}V?|IV|[1-2](?:ST|ND)?)\s*SEM',
        text
    )
    if year_match:
        year_str = year_match.group(1).strip()
        sem_str  = year_match.group(2).strip()
        year_num = roman_map.get(year_str, 1)
        sem_num  = roman_map.get(sem_str,  1)
        return (year_num - 1) * 2 + sem_num

    # Fallback: direct semester number in string
    sem_match = re.search(r'SEM(?:ESTER)?\s*[:\-]?\s*([1-8])', text)
    if sem_match:
        return int(sem_match.group(1))

    return 1


# ─────────────────────────────────────────────────────────────────────────────
# Grade sheet parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_grade_sheet(text: str) -> dict:
    """
    Parse raw OCR/PDF text into structured dict.
    Handles SNIST JNTUH autonomous format.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    full_text = "\n".join(lines)

    result = {
        "hall_ticket_no":    None,
        "serial_no":         None,
        "student_name":      None,
        "branch":            None,
        "examination":       None,
        "semester_no":       None,
        "exam_month_year":   None,
        "sgpa":              None,
        "cgpa":              None,
        "total_credits":     None,
        "subjects_registered": None,
        "subjects_passed":   None,
        "subjects":          [],
    }

    # ── Hall Ticket Number ─────────────────────────────────────────────────
    ht_match = re.search(
        r'(?:HALL\s*TICKET\s*(?:NO\.?|NUMBER)[.\s:]*|HT\s*[.\s]*NO[.\s:]*)'
        r'([A-Z0-9]{8,15})',
        full_text, re.IGNORECASE
    )
    if ht_match:
        result["hall_ticket_no"] = ht_match.group(1).strip()
    else:
        # Bare hall ticket like "22311A12P9" or "21311A0501"
        ht_bare = re.search(r'\b([1-9][0-9]{3}[A-Z][0-9A-Z]{4,8})\b', full_text)
        if ht_bare:
            result["hall_ticket_no"] = ht_bare.group(1)

    # ── Serial Number ──────────────────────────────────────────────────────
    serial_match = re.search(
        r'(?:SERIAL\s*NO[.\s:]*|S\.NO[.\s:]*)\s*([0-9]{10,16})',
        full_text, re.IGNORECASE
    )
    if serial_match:
        result["serial_no"] = serial_match.group(1).strip()

    # ── Student Name ───────────────────────────────────────────────────────
    name_match = re.search(
        r"STUDENT['\u2019]?S?\s*NAME\s*[:\-]?\s*([A-Z][A-Z\s]{3,40}?)(?:\n|FATHER)",
        full_text, re.IGNORECASE
    )
    if name_match:
        result["student_name"] = name_match.group(1).strip().title()

    # ── Branch ─────────────────────────────────────────────────────────────
    branch_match = re.search(
        r'BRANCH\s*[:\-]?\s*([A-Z][A-Z\s&]{3,50}?)(?:\n|STUDENT|MEMO)',
        full_text, re.IGNORECASE
    )
    if branch_match:
        result["branch"] = branch_match.group(1).strip().title()

    # ── Examination / Semester ─────────────────────────────────────────────
    exam_match = re.search(
        r'EXAMINATION\s*[:\-]?\s*([^\n]{5,80})',
        full_text, re.IGNORECASE
    )
    if exam_match:
        result["examination"] = exam_match.group(1).strip()
        result["semester_no"] = detect_semester_number(result["examination"])
    else:
        # Try to detect semester from anywhere in text
        sem_anywhere = re.search(
            r'(I{1,3}V?|IV|[1-4])\s*(?:ST|ND|RD|TH)?\s*YEAR\s*(I{1,2}|[1-2])\s*(?:ST|ND)?\s*SEM',
            full_text, re.IGNORECASE
        )
        if sem_anywhere:
            result["examination"] = sem_anywhere.group(0).strip()
            result["semester_no"] = detect_semester_number(result["examination"])

    # ── Month & Year ───────────────────────────────────────────────────────
    month_match = re.search(
        r'(?:MONTH\s*[&AND]*\s*YEAR\s*OF\s*EXAM\s*[:\-]?\s*)'
        r'([A-Z]+\s*[0-9]{4})',
        full_text, re.IGNORECASE
    )
    if month_match:
        result["exam_month_year"] = month_match.group(1).strip()

    # ── SGPA ──────────────────────────────────────────────────────────────
    sgpa_match = re.search(
        r'S\.?G\.?P\.?A\.?\s*[:\-]?\s*([0-9]+\.[0-9]{1,2})',
        full_text, re.IGNORECASE
    )
    if sgpa_match:
        result["sgpa"] = float(sgpa_match.group(1))

    # ── CGPA ──────────────────────────────────────────────────────────────
    cgpa_match = re.search(
        r'C\.?G\.?P\.?A\.?\s*[:\-]?\s*([0-9]+\.[0-9]{1,2})',
        full_text, re.IGNORECASE
    )
    if cgpa_match:
        result["cgpa"] = float(cgpa_match.group(1))

    # ── Total Credits ──────────────────────────────────────────────────────
    credits_match = re.search(
        r'(?:CUMULATIVE|TOTAL)[^0-9]*([0-9]+(?:\.[0-9])?)\s*(?:CREDITS?)?',
        full_text, re.IGNORECASE
    )
    if credits_match:
        result["total_credits"] = float(credits_match.group(1))

    # ── Subjects Registered / Passed ──────────────────────────────────────
    reg_match = re.search(r'Subjects\s+Registered\s*[:\-]?\s*([0-9]+)', full_text, re.IGNORECASE)
    if reg_match:
        result["subjects_registered"] = int(reg_match.group(1))

    passed_match = re.search(r'Passed\s*[:\-]?\s*([0-9]+)', full_text, re.IGNORECASE)
    if passed_match:
        result["subjects_passed"] = int(passed_match.group(1))

    # ── Subject Rows (regex) ───────────────────────────────────────────────
    subject_pattern = re.compile(
        r'(\d{1,2})\s+'                                     # S.No
        r'([A-Z0-9]{3,12})\s+'                             # Subject Code
        r'([A-Z][A-Z0-9\s&\-\(\)/,\.]{2,60}?)\s+'         # Subject Name
        r'(O|A\+|A|B\+|B|C|D|P|F|AB|S\*?|NS\*?)\s+'       # Grade
        r'(\d+(?:\.\d)?)\s+'                               # Credits
        r'(P|F|AB)',                                        # Result
        re.IGNORECASE
    )
    for m in subject_pattern.finditer(full_text):
        sno, code, name, grade, credits, res_val = m.groups()
        grade_upper = grade.strip().upper()
        grade_pts   = GRADE_POINTS.get(grade_upper, 0)
        is_backlog  = grade_upper in ("F", "AB", "NS", "NS*") or res_val.upper() == "F"
        result["subjects"].append({
            "sno":          int(sno),
            "subject_code": code.strip(),
            "subject_name": name.strip().title(),
            "grade_letter": grade_upper,
            "grade_points": grade_pts,
            "credits":      float(credits),
            "is_backlog":   is_backlog,
            "result":       res_val.upper(),
        })

    # ── Fallback: line-by-line if fewer than 3 subjects found ─────────────
    if len(result["subjects"]) < 3:
        result["subjects"] = _fallback_subject_parse(lines)

    return result


def _fallback_subject_parse(lines: list) -> list:
    """
    Line-by-line fallback: looks for lines starting with row-number + subject-code.
    """
    subjects = []
    valid_grades = {"O", "A+", "A", "B+", "B", "C", "D", "P", "F", "AB", "S", "S*", "NS", "NS*"}

    for line in lines:
        m = re.match(r'^(\d{1,2})\s+([A-Z0-9]{4,8})\s+(.+)', line)
        if not m:
            continue
        sno_str, code, rest = m.groups()
        parts = rest.split()
        if len(parts) < 3:
            continue

        grade     = None
        credits   = None
        res_val   = "P"

        for j in range(len(parts) - 1, -1, -1):
            p = parts[j].upper()
            if p in ("P", "F", "AB") and res_val == "P":
                res_val = p
            elif p in valid_grades and grade is None:
                grade = p
            elif re.match(r'^\d+(\.\d)?$', p) and credits is None:
                credits = float(p)

        if grade and credits is not None:
            name_end_idx = max(len(parts) - 3, 1)
            name = " ".join(parts[:name_end_idx]).title()
            grade_pts = GRADE_POINTS.get(grade, 0)
            subjects.append({
                "sno":          int(sno_str),
                "subject_code": code.strip(),
                "subject_name": name,
                "grade_letter": grade,
                "grade_points": grade_pts,
                "credits":      credits,
                "is_backlog":   grade in ("F", "AB"),
                "result":       res_val,
            })

    return subjects


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def extract_from_file(file_path: str) -> dict:
    """
    Extract text from file, parse grade sheet, return structured dict.
    Raises ValueError with user-friendly message on failure.
    """
    raw_text = extract_text_from_file(file_path)

    if not raw_text or len(raw_text.strip()) < 50:
        raise ValueError(
            "Could not extract readable text from file. "
            "Ensure the image is clear and well-lit, or upload a text-based PDF."
        )

    parsed = parse_grade_sheet(raw_text)

    # Consider parsing successful if ANY key field was found
    has_data = (
        parsed["sgpa"]
        or parsed["subjects"]
        or parsed["hall_ticket_no"]
        or parsed["student_name"]
        or parsed["examination"]
        or parsed["cgpa"]
    )
    if not has_data:
        raise ValueError(
            "Could not parse grade data. "
            "Ensure this is a valid JNTUH grade sheet and the text is readable."
        )

    return parsed
