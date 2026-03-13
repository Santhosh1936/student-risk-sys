"""
advisor.py — SARS AI Advisory Chat Service
===========================================
Powers the per-student isolated advisory chat.
Uses Google Gemini 2.5 Flash for responses.

Architecture:
  - Each student has one ChatThread (created on first message)
  - Full academic context injected ONCE as seed on first message
  - Last 10 messages sent as conversation history on every call
  - When new semester uploaded, data_updated=True flag set
  - On next message after update, refresh context injected automatically
  - Student data never mixed between different students
"""

import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import requests

from ..config import settings
from ..models.models import (
    Student, User, SemesterRecord, SubjectGrade,
    AttendanceRecord, RiskScore, ChatThread, ChatMessage
)

logger = logging.getLogger(__name__)

HISTORY_WINDOW = 10   # how many past messages to send to Gemini


# ══════════════════════════════════════════════════════════════════════
# STUDENT CONTEXT BUILDER
# ══════════════════════════════════════════════════════════════════════

def _build_student_context(student_id: int, db: Session) -> str:
    """
    Build complete academic profile for a student as a structured string.
    This is sent to Gemini as context — either on first message (seed)
    or when data has been updated (refresh).
    Contains: identity, all semester grades, risk score, backlogs.
    """
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()
    user = db.query(User).filter(
        User.id == student.user_id
    ).first()

    # Semester records
    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student_id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )

    semesters_data = []
    all_backlogs = []

    for rec in records:
        subjects = (
            db.query(SubjectGrade)
            .filter(SubjectGrade.semester_record_id == rec.id)
            .all()
        )
        subject_list = []
        for s in subjects:
            subject_list.append({
                "code": s.subject_code,
                "name": s.subject_name,
                "grade": s.grade_letter,
                "points": s.grade_points,
                "credits": s.credits,
                "backlog": s.is_backlog,
            })
            if s.is_backlog:
                all_backlogs.append(
                    f"{s.subject_name} (Sem {rec.semester_no})"
                )
        semesters_data.append({
            "semester_no": rec.semester_no,
            "sgpa": rec.gpa,
            "credits_attempted": rec.credits_attempted,
            "credits_earned": rec.credits_earned,
            "subjects": subject_list,
        })

    # Build a flat, human-readable subject table for easier AI parsing
    flat_subjects_lines = []
    for sem in semesters_data:
        flat_subjects_lines.append(f"  Semester {sem['semester_no']} (SGPA: {sem['sgpa']})")
        for subj in sem["subjects"]:
            backlog_marker = " ← BACKLOG" if subj["backlog"] else ""
            flat_subjects_lines.append(
                f"    • {subj['name']} ({subj['code'] or 'N/A'}): "
                f"Grade {subj['grade']} | {subj['points']} pts | {subj['credits']} credits{backlog_marker}"
            )
    flat_subjects_text = "\n".join(flat_subjects_lines) if flat_subjects_lines else "No subjects uploaded yet."

    # Attendance
    attendance = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .all()
    )
    attendance_data = [
        {"subject": a.subject_name,
         "semester": a.semester_no,
         "attended": a.classes_attended,
         "total": a.total_classes,
         "percentage": a.percentage}
        for a in attendance
    ]

    # Risk score
    risk = (
        db.query(RiskScore)
        .filter(RiskScore.student_id == student_id)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )
    risk_data = {}
    if risk:
        risk_data = {
            "sars_score": risk.sars_score,
            "risk_level": risk.risk_level,
            "confidence": risk.confidence,
            "advisory": risk.advisory_text,
        }
        try:
            fb = risk.factor_breakdown
            if isinstance(fb, dict):
                risk_data["breakdown"] = fb
            elif isinstance(fb, str):
                risk_data["breakdown"] = json.loads(fb)
        except Exception:
            pass

    context = f"""
STUDENT ACADEMIC PROFILE — SARS ADVISORY SYSTEM
================================================
Name          : {user.full_name if user else 'Unknown'}
Roll Number   : {user.roll_number if user else 'N/A'}
Branch        : {student.branch or 'N/A'}
Current Sem   : {student.current_semester or 'N/A'}
CGPA          : {student.cgpa or 'N/A'}
Total Backlogs: {len(all_backlogs)}
Backlog List  : {', '.join(all_backlogs) if all_backlogs else 'None'}

COMPLETE SUBJECT LIST (ALL SEMESTERS — USE THESE EXACT NAMES):
{flat_subjects_text}

SEMESTER-WISE ACADEMIC RECORD (DETAILED JSON):
{json.dumps(semesters_data, indent=2)}

ATTENDANCE DATA:
{json.dumps(attendance_data, indent=2) if attendance_data
 else 'No attendance data uploaded yet.'}

SARS RISK ASSESSMENT:
{json.dumps(risk_data, indent=2) if risk_data
 else 'Risk score not yet computed.'}

JNTUH GRADING SCALE:
O=10pts A+=9pts A=8pts B+=7pts B=6pts C=5pts D=4pts F=0pts(backlog)
Minimum passing: D grade (4 points). CGPA below 5.0 = academic probation.
================================================
"""
    return context.strip()


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════

def _build_system_prompt(student_context: str) -> str:
    return f"""You are SARS Advisor — an AI academic counselor for engineering \
students at SNIST (Sreenidhi Institute of Science and Technology), Hyderabad.
You are speaking directly with the student whose profile is below.

YOUR CAPABILITIES:
1. What-If Predictions: When student asks "what if my CGPA becomes X" or
   "what grade do I need in semester N to reach CGPA Y" — calculate it
   precisely using the JNTUH CGPA formula:
   CGPA = (Sum of all semester SGPAs × credits) / Total credits attempted
   Show step-by-step working.

2. Subject-Specific Advice: Based on their ACTUAL uploaded subject names and grades:
   - Identify weak subjects (grades C, D, F) and give targeted improvement strategies.
   - For students with good grades, identify which of their actual subjects are
     most important for placements, higher studies, or core engineering skills.
   - ALWAYS name the specific subjects from the student's transcript.

3. Risk-Level Guidance: Use their SARS score and risk level to give
   proportionate urgency. HIGH risk = strong action plan. LOW = encouragement.

4. Backlog Strategy: If they have backlogs, give a prioritized clearing
   plan based on credits and subject difficulty.

5. General Academic Guidance: Study tips, time management, exam strategies
   specific to their semester and branch.

RULES:
- Always use the student's ACTUAL data from the profile below.
- Never invent grades or scores that aren't in the profile.
- When asked about subjects (e.g., "which subjects to focus on", "name subjects",
  "what to study", "subjects for placements/interviews") — ALWAYS list the student's
  ACTUAL subject names from their uploaded transcripts, semester by semester.
  Never use generic CS subject names that are not in the profile.
- If the student has no weak grades, identify which uploaded subjects are most
  relevant for placements, internships, or their branch's core skills.
- If asked about a semester not yet uploaded, say so clearly.
- Keep responses focused, practical, and encouraging.
- For What-If calculations, always show the math.
- If attendance data is missing, note it but don't block advice.
- Always address the student by their first name.
- Respond in clear English. Keep responses concise (max 400 words)
  unless a detailed calculation is needed.

STUDENT PROFILE:
{student_context}
"""


# ══════════════════════════════════════════════════════════════════════
# THREAD MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def _get_or_create_thread(student_id: int, db: Session) -> ChatThread:
    """Get existing thread or create new one for this student."""
    thread = db.query(ChatThread).filter(
        ChatThread.student_id == student_id
    ).first()
    if not thread:
        thread = ChatThread(
            student_id=student_id,
            data_updated=False,
            context_set=False,
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
    return thread


def _get_recent_history(thread_id: int, db: Session) -> list:
    """
    Fetch last HISTORY_WINDOW messages for Gemini conversation history.
    Excludes context_seed messages (those were system setup, not chat).
    Returns list of {role, parts} dicts for Gemini SDK format.
    """
    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.thread_id == thread_id,
            ChatMessage.message_type != "context_seed"
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_WINDOW)
        .all()
    )
    messages = list(reversed(messages))

    history = []
    for msg in messages:
        history.append({
            "role": msg.role,
            "parts": [{"text": msg.content}]
        })
    return history


def _save_message(
    thread_id: int,
    role: str,
    content: str,
    message_type: str,
    db: Session
) -> None:
    """Save a message to chat_messages table."""
    msg = ChatMessage(
        thread_id=thread_id,
        role=role,
        content=content,
        message_type=message_type,
    )
    db.add(msg)
    db.commit()


# ══════════════════════════════════════════════════════════════════════
# GEMINI CALL
# ══════════════════════════════════════════════════════════════════════

def _call_gemini(
    system_prompt: str,
    history: list,
    user_message: str
) -> str:
    """
    Call Gemini 2.5 Flash via REST API with system prompt + conversation history.
    history: list of {role, parts} — previous messages in this thread.
    Returns AI response text.
    Uses direct REST API: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    # Convert history to Gemini API format and add current user message
    contents = []

    # Add history messages
    for msg in history:
        contents.append({
            "role": msg["role"],
            "parts": msg["parts"]
        })

    # Add current user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    # Prepare request payload
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
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

    if response.status_code == 200:
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    else:
        # Parse error
        err_json = response.json() if response.text else {}
        err_msg = err_json.get("error", {}).get("message", response.text)
        raise ValueError(f"Gemini API error ({response.status_code}): {err_msg}")


# ══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

def send_message(
    student_id: int,
    user_message: str,
    db: Session
) -> dict:
    """
    Main entry point. Called from POST /student/advisor/chat.

    Flow:
      1. Get or create chat thread for this student
      2. If first message ever (context_set=False):
           Build full profile -> inject as system prompt seed
           Save as context_seed message, set context_set=True
      3. If data_updated=True (new semester uploaded since last chat):
           Inject refresh message with updated profile
           Save as data_refresh message, set data_updated=False
      4. Fetch last 10 messages as conversation history
      5. Call Gemini with system prompt + history + user message
      6. Save user message + AI response to DB
      7. Update thread.last_active
      8. Return AI response + thread metadata

    Returns:
      {
        "response": "<AI text>",
        "thread_id": <int>,
        "message_count": <int>,
        "data_was_refreshed": <bool>
      }
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not configured. "
            "Add it to backend/.env"
        )

    thread = _get_or_create_thread(student_id, db)
    data_was_refreshed = False

    # Build current student context
    student_context = _build_student_context(student_id, db)
    system_prompt   = _build_system_prompt(student_context)

    # ── First message ever: save context seed ─────────────────────────
    if not thread.context_set:
        _save_message(
            thread.id,
            role="user",
            content=f"[CONTEXT SEED]\n{student_context}",
            message_type="context_seed",
            db=db
        )
        _save_message(
            thread.id,
            role="model",
            content=(
                "I have your complete academic profile loaded. "
                "I'm ready to help you with your studies, "
                "risk analysis, what-if predictions, and "
                "subject-specific advice. What would you like to know?"
            ),
            message_type="context_seed",
            db=db
        )
        thread.context_set = True
        db.commit()

    # ── Data updated since last chat: inject refresh ──────────────────
    if thread.data_updated:
        refresh_msg = (
            f"SYSTEM UPDATE: This student has uploaded new academic data. "
            f"Updated profile:\n{student_context}\n"
            f"All future responses must reflect this updated data. "
            f"Integrate this with everything discussed previously."
        )
        _save_message(
            thread.id,
            role="user",
            content=refresh_msg,
            message_type="data_refresh",
            db=db
        )
        _save_message(
            thread.id,
            role="model",
            content=(
                "I've updated my knowledge with your latest academic data. "
                "My advice will now reflect your most recent grades and "
                "risk assessment."
            ),
            message_type="data_refresh",
            db=db
        )
        thread.data_updated = False
        db.commit()
        data_was_refreshed = True

    # ── Fetch recent history for Gemini ──────────────────────────────
    history = _get_recent_history(thread.id, db)

    # ── Call Gemini ───────────────────────────────────────────────────
    try:
        ai_response = _call_gemini(system_prompt, history, user_message)
    except Exception as e:
        logger.error(f"Gemini advisory call failed: {e}")
        raise ValueError(f"AI advisor unavailable: {e}")

    # ── Save this exchange to DB ──────────────────────────────────────
    _save_message(thread.id, "user", user_message, "normal", db)
    _save_message(thread.id, "model", ai_response, "normal", db)

    # ── Update thread last_active ─────────────────────────────────────
    thread.last_active = datetime.now(timezone.utc)
    db.commit()

    # Count total user messages in thread
    msg_count = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.thread_id == thread.id,
            ChatMessage.role == "user",
            ChatMessage.message_type == "normal"
        )
        .count()
    )

    return {
        "response": ai_response,
        "thread_id": thread.id,
        "message_count": msg_count,
        "data_was_refreshed": data_was_refreshed,
    }


def get_chat_history(student_id: int, db: Session) -> list:
    """
    Fetch full chat history for display in frontend.
    Returns only normal messages (excludes seeds and refreshes).
    Used by GET /student/advisor/history.
    """
    thread = db.query(ChatThread).filter(
        ChatThread.student_id == student_id
    ).first()
    if not thread:
        return []

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.thread_id == thread.id,
            ChatMessage.message_type == "normal"
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat()
                          if m.created_at else None,
        }
        for m in messages
    ]


def mark_data_updated(student_id: int, db: Session) -> None:
    """
    Called automatically when student confirms a new semester upload.
    Sets data_updated=True on their chat thread so next message
    triggers a context refresh injection.
    Safe to call even if thread doesn't exist yet.
    """
    thread = db.query(ChatThread).filter(
        ChatThread.student_id == student_id
    ).first()
    if thread:
        thread.data_updated = True
        db.commit()
        logger.info(
            f"Chat thread marked for data refresh: student_id={student_id}"
        )
