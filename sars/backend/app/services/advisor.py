import logging
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

from ..config import settings
from ..models.models import ChatMessage, ChatThread, Student
from . import rag_service

logger = logging.getLogger(__name__)

HISTORY_WINDOW = 6
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)


def _get_or_create_thread(student_id: int, db: Session) -> ChatThread:
    thread = db.query(ChatThread).filter(ChatThread.student_id == student_id).first()
    if not thread:
        thread = ChatThread(student_id=student_id, data_updated=False, context_set=False)
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
    messages.reverse()
    return [{"role": message.role, "parts": [{"text": message.content}]} for message in messages]


def _save_message(thread_id: int, role: str, content: str, message_type: str, db: Session) -> None:
    db.add(
        ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            message_type=message_type,
        )
    )
    db.commit()


def _call_gemini(system_prompt: str, history: list, user_message: str) -> str:
    contents = list(history)
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    response = requests.post(
        GEMINI_URL,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        },
        json={
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048,
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["candidates"][0]["content"]["parts"][0]["text"].strip()


def _build_system_prompt(student_name: str, retrieved_chunks: list) -> str:
    retrieved_context = "\n\n".join(
        f"[{chunk['metadata']['chunk_type']}]\n{chunk['content']}" for chunk in retrieved_chunks
    )
    if not retrieved_context:
        retrieved_context = "No retrieved academic records were available."

    return (
        f"You are SARS Advisor for {student_name}.\n"
        "Use ONLY the following retrieved information to answer. "
        "Do not use knowledge outside what is provided below.\n\n"
        "Retrieved context:\n"
        "---\n"
        f"{retrieved_context}\n"
        "---\n\n"
        "If the answer is not in the retrieved context, say: "
        "I don't have enough information about that in your academic records.\n\n"
        "Be supportive, accurate, and specific. Quote exact numbers from the retrieved data when available."
    )


def _source_payload(retrieved_chunks: list) -> list:
    sources = []
    for chunk in retrieved_chunks:
        relevance_score = round(float(chunk.get("relevance_score", 0.0)), 4)
        if relevance_score >= 0.8:
            relevance = "HIGH"
        elif relevance_score >= 0.55:
            relevance = "MEDIUM"
        else:
            relevance = "LOW"

        preview = chunk["content"][:100]
        sources.append(
            {
                "chunk_type": chunk["metadata"]["chunk_type"],
                "relevance_score": relevance_score,
                "relevance": relevance,
                "preview": preview,
            }
        )
    return sources


def send_message(student_id: int, user_message: str, db: Session) -> dict:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured. Add it to backend/.env.")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError("Student profile not found.")

    thread = _get_or_create_thread(student_id, db)
    data_was_refreshed = False

    rag_status = rag_service.get_rag_status(student_id, db)
    if not rag_status["indexed"]:
        rag_service.index_student(student_id, db)

    if thread.data_updated:
        rag_service.index_student(student_id, db)
        thread.data_updated = False
        data_was_refreshed = True
        db.commit()

    retrieved_chunks = rag_service.retrieve(student_id, user_message, n=4)
    system_prompt = _build_system_prompt(student.user.full_name, retrieved_chunks)
    history = _get_recent_history(thread.id, db)

    try:
        ai_response = _call_gemini(system_prompt, history, user_message)
    except requests.RequestException as exc:
        logger.error("Gemini advisory call failed: %s", exc)
        raise ValueError("AI advisor unavailable right now.") from exc
    except Exception as exc:
        logger.error("Gemini advisory call failed: %s", exc)
        raise ValueError(f"AI advisor unavailable: {exc}") from exc

    _save_message(thread.id, "user", user_message, "normal", db)
    _save_message(thread.id, "model", ai_response, "normal", db)

    thread.last_active = datetime.now(timezone.utc)
    if not thread.context_set:
        thread.context_set = True
    db.commit()

    message_count = (
        db.query(ChatMessage)
        .filter(ChatMessage.thread_id == thread.id, ChatMessage.message_type == "normal")
        .count()
    )

    return {
        "response": ai_response,
        "thread_id": thread.id,
        "message_count": message_count,
        "data_was_refreshed": data_was_refreshed,
        "rag_active": True,
        "sources": _source_payload(retrieved_chunks),
    }


def get_chat_history(student_id: int, db: Session) -> list:
    thread = db.query(ChatThread).filter(ChatThread.student_id == student_id).first()
    if not thread:
        return []

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.thread_id == thread.id, ChatMessage.message_type == "normal")
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
        for message in messages
    ]
