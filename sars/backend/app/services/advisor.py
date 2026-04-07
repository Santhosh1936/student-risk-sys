"""
advisor.py - SARS AI Advisory Chat Service
==========================================
RAG-first advisory chat for per-student isolated conversations.

Flow summary:
  - Keep one ChatThread per student and persist all normal messages.
  - Build/rebuild student vector index as needed.
  - Retrieve only relevant chunks for each query.
  - Generate answer grounded in retrieved evidence.
  - If RAG fails, fall back to legacy full-context prompt stuffing safely.
"""

import json
import logging
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from ..config import settings
from ..models.models import (
    AttendanceRecord,
    ChatMessage,
    ChatThread,
    RiskScore,
    SemesterRecord,
    Student,
    SubjectGrade,
    User,
)
from .rag_service import get_rag_status, index_student, retrieve

logger = logging.getLogger(__name__)

HISTORY_WINDOW = 6


def _legacy_build_student_context(student_id: int, db: Session) -> str:
    """Legacy fallback context builder used only when RAG fails."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return "Student profile not found."

    user = db.query(User).filter(User.id == student.user_id).first()

    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student_id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )

    lines = []
    all_backlogs = []
    for rec in records:
        subjects = (
            db.query(SubjectGrade)
            .filter(SubjectGrade.semester_record_id == rec.id)
            .all()
        )
        lines.append(f"Semester {rec.semester_no} SGPA {rec.gpa}")
        for s in subjects:
            backlog_marker = " BACKLOG" if s.is_backlog else ""
            lines.append(
                f"- {s.subject_name} ({s.subject_code or 'N/A'}): "
                f"Grade {s.grade_letter}, Credits {s.credits}{backlog_marker}"
            )
            if s.is_backlog:
                all_backlogs.append(f"{s.subject_name} (Sem {rec.semester_no})")

    attendance = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .all()
    )
    attendance_data = [
        {
            "subject": a.subject_name,
            "semester": a.semester_no,
            "percentage": a.percentage,
        }
        for a in attendance
    ]

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
            if isinstance(risk.factor_breakdown, dict):
                risk_data["breakdown"] = risk.factor_breakdown
            elif isinstance(risk.factor_breakdown, str):
                risk_data["breakdown"] = json.loads(risk.factor_breakdown)
        except Exception:
            pass

    return (
        "STUDENT PROFILE\n"
        f"Name: {user.full_name if user else 'Unknown'}\n"
        f"Roll: {user.roll_number if user else 'N/A'}\n"
        f"Branch: {student.branch or 'N/A'}\n"
        f"Current Semester: {student.current_semester or 'N/A'}\n"
        f"CGPA: {student.cgpa if student.cgpa is not None else 'N/A'}\n"
        f"Total Backlogs: {len(all_backlogs)}\n"
        f"Backlog List: {', '.join(all_backlogs) if all_backlogs else 'None'}\n\n"
        f"Subject Records:\n{chr(10).join(lines) if lines else 'No records yet'}\n\n"
        f"Attendance:\n{json.dumps(attendance_data, indent=2) if attendance_data else 'No attendance uploaded'}\n\n"
        f"Risk:\n{json.dumps(risk_data, indent=2) if risk_data else 'No risk score yet'}"
    )


def _legacy_build_system_prompt(student_context: str) -> str:
    return (
        "You are SARS Advisor for SNIST students. Use only the provided student data. "
        "Never invent grades or records. Give practical, concise guidance.\n\n"
        f"Student profile:\n{student_context}"
    )


def _build_rag_system_prompt(student_name: str, chunks: list) -> str:
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        context_blocks.append(f"[{idx}] {chunk['text']}")

    retrieved_text = "\n---\n".join(context_blocks) if context_blocks else "No retrieved context available."

    return (
        f"You are SARS Advisor for {student_name}. "
        "Answer using ONLY the information below. "
        "Do not use knowledge outside what is provided. "
        "If the answer is not in the context below, say: "
        "I don't have enough information about that in your academic records.\n\n"
        "Retrieved context:\n"
        "---\n"
        f"{retrieved_text}\n"
        "---"
    )


def _get_student_name(student_id: int, db: Session) -> str:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return "Student"
    user = db.query(User).filter(User.id == student.user_id).first()
    return user.full_name if user and user.full_name else "Student"


def _get_or_create_thread(student_id: int, db: Session) -> ChatThread:
    thread = db.query(ChatThread).filter(ChatThread.student_id == student_id).first()
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
    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.thread_id == thread_id,
            ChatMessage.message_type.notin_(["context_seed", "data_refresh"]),
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(HISTORY_WINDOW)
        .all()
    )
    messages = list(reversed(messages))

    history = []
    for msg in messages:
        history.append({"role": msg.role, "parts": [{"text": msg.content}]})
    return history


def _save_message(thread_id: int, role: str, content: str, message_type: str, db: Session) -> None:
    msg = ChatMessage(
        thread_id=thread_id,
        role=role,
        content=content,
        message_type=message_type,
    )
    db.add(msg)
    db.commit()


def _call_gemini(system_prompt: str, history: list, user_message: str) -> str:
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    contents = []
    for msg in history:
        contents.append({"role": msg["role"], "parts": msg["parts"]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        },
        timeout=30,
    )

    if response.status_code == 200:
        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()

    err_json = response.json() if response.text else {}
    err_msg = err_json.get("error", {}).get("message", response.text)
    raise ValueError(f"Gemini API error ({response.status_code}): {err_msg}")


def send_message(student_id: int, user_message: str, db: Session) -> dict:
    """Main entry point for POST /student/advisor/chat."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured. Add it to backend/.env")

    thread = _get_or_create_thread(student_id, db)
    data_was_refreshed = False
    rag_active = True
    chunks = []

    history = _get_recent_history(thread.id, db)
    student_name = _get_student_name(student_id, db)

    try:
        status = get_rag_status(student_id)
        if not status["indexed"]:
            index_student(student_id, db)

        if thread.data_updated:
            index_student(student_id, db)
            thread.data_updated = False
            db.commit()
            data_was_refreshed = True

        chunks = retrieve(student_id, user_message, n_results=4)
        system_prompt = _build_rag_system_prompt(student_name, chunks)
        ai_response = _call_gemini(system_prompt, history, user_message)

    except Exception as rag_error:
        logger.warning("RAG flow failed for student_id=%s: %s", student_id, rag_error)
        rag_active = False

        if thread.data_updated:
            thread.data_updated = False
            db.commit()
            data_was_refreshed = True

        student_context = _legacy_build_student_context(student_id, db)
        fallback_prompt = _legacy_build_system_prompt(student_context)

        try:
            ai_response = _call_gemini(fallback_prompt, history, user_message)
        except Exception as gemini_error:
            logger.error("Gemini advisory call failed: %s", gemini_error)
            raise ValueError(f"AI advisor unavailable: {gemini_error}")

    _save_message(thread.id, "user", user_message, "normal", db)
    _save_message(thread.id, "model", ai_response, "normal", db)

    thread.last_active = datetime.now(timezone.utc)
    db.commit()

    msg_count = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.thread_id == thread.id,
            ChatMessage.role == "user",
            ChatMessage.message_type == "normal",
        )
        .count()
    )

    return {
        "response": ai_response,
        "thread_id": thread.id,
        "message_count": msg_count,
        "data_was_refreshed": data_was_refreshed,
        "rag_active": rag_active,
        "sources": [
            {
                "chunk_type": c["chunk_type"],
                "relevance": c["relevance"],
                "preview": (c["text"][:120] + "...") if len(c["text"]) > 120 else c["text"],
            }
            for c in chunks
        ],
    }


def get_chat_history(student_id: int, db: Session) -> list:
    thread = db.query(ChatThread).filter(ChatThread.student_id == student_id).first()
    if not thread:
        return []

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.thread_id == thread.id,
            ChatMessage.message_type == "normal",
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


def mark_data_updated(student_id: int, db: Session) -> None:
    thread = db.query(ChatThread).filter(ChatThread.student_id == student_id).first()
    if thread:
        thread.data_updated = True
        db.commit()
        logger.info("Chat thread marked for data refresh: student_id=%s", student_id)
