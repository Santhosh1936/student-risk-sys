"""
RAG engine for SARS.

Engineering decisions:
- ChromaDB over FAISS: Chroma is the better fit here because it is Windows-friendly,
  persists locally across restarts without extra glue code, runs fully in-process,
  needs no external service, and is more than sufficient for the small per-student
  corpus size in this project.
- Direct Gemini/Chroma integration over LangChain: the project has no LangChain
  dependency today, and direct integration keeps the data flow explicit, easier to
  debug, and easier for future contributors to maintain.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from sqlalchemy.orm import Session, joinedload

try:
    import chromadb
except ImportError:  # pragma: no cover - handled at runtime
    chromadb = None

from ..config import settings
from ..models.models import AttendanceRecord, RiskScore, SemesterRecord, Student, SubjectGrade

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
)
COLLECTION_NAME = "sars_student_chunks"
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent"
)
TOTAL_PROGRAM_SEMESTERS = 8

_client = None
_collection = None


def get_vector_store():
    global _client, _collection

    if chromadb is None:
        raise ImportError("ChromaDB is not installed. Add 'chromadb' to requirements.txt.")

    if _collection is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    return _collection


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_float(value: Optional[float], digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def _embed_text(text: str) -> List[float]:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")

    response = requests.post(
        EMBEDDING_API_URL,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        },
        json={
            "content": {
                "parts": [{"text": text}],
            }
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["embedding"]["values"]


def _load_student(student_id: int, db: Session) -> Student:
    student = (
        db.query(Student)
        .options(
            joinedload(Student.user),
            joinedload(Student.semester_records).joinedload(SemesterRecord.subjects),
            joinedload(Student.attendance_records),
            joinedload(Student.risk_scores),
        )
        .filter(Student.id == student_id)
        .first()
    )
    if not student:
        raise ValueError(f"Student {student_id} not found")
    return student


def _sorted_semesters(student: Student) -> List[SemesterRecord]:
    return sorted(
        [record for record in student.semester_records if record.is_confirmed],
        key=lambda record: record.semester_no,
    )


def _sorted_attendance(student: Student) -> List[AttendanceRecord]:
    return sorted(
        student.attendance_records,
        key=lambda record: (record.semester_no, record.subject_name.lower()),
    )


def _all_backlogs(semester_records: List[SemesterRecord]) -> List[tuple[int, SubjectGrade]]:
    backlog_rows: List[tuple[int, SubjectGrade]] = []
    for record in semester_records:
        for subject in sorted(record.subjects, key=lambda item: (item.subject_name or "").lower()):
            if subject.is_backlog:
                backlog_rows.append((record.semester_no, subject))
    return backlog_rows


def _compute_cgpa_points(semester_records: List[SemesterRecord]) -> List[Dict[str, float]]:
    progression: List[Dict[str, float]] = []
    weighted_points = 0.0
    total_credits = 0.0

    for record in semester_records:
        if record.gpa is None:
            continue
        credits = record.credits_attempted or record.credits_earned or 0.0
        if credits <= 0:
            continue
        weighted_points += record.gpa * credits
        total_credits += credits
        progression.append(
            {
                "semester_no": record.semester_no,
                "sgpa": record.gpa,
                "credits": credits,
                "cgpa": weighted_points / total_credits,
            }
        )

    return progression


def _trend_from_progression(progression: List[Dict[str, float]]) -> str:
    if len(progression) < 2:
        return "insufficient data"

    previous = progression[-2]["sgpa"]
    current = progression[-1]["sgpa"]
    if current > previous + 0.2:
        return "improving"
    if current < previous - 0.2:
        return "declining"
    return "stable"


def _target_cgpa_guidance(
    student: Student,
    progression: List[Dict[str, float]],
) -> str:
    if not progression:
        return "Need at least one confirmed semester before projecting future CGPA targets."

    current_semester = max(student.current_semester or progression[-1]["semester_no"], progression[-1]["semester_no"])
    remaining_semesters = max(TOTAL_PROGRAM_SEMESTERS - current_semester, 0)
    if remaining_semesters == 0:
        return "No remaining semesters in the 8-semester plan, so the CGPA is effectively finalized."

    total_credits = sum(item["credits"] for item in progression)
    weighted_points = sum(item["sgpa"] * item["credits"] for item in progression)
    avg_credits_per_semester = total_credits / len(progression)
    future_credits = remaining_semesters * avg_credits_per_semester

    if future_credits <= 0:
        return "Not enough credit information is available to estimate future CGPA targets."

    statements = []
    for target in (7.5, 8.0, 9.0):
        needed = ((target * (total_credits + future_credits)) - weighted_points) / future_credits
        if needed <= 0:
            statements.append(f"Target {target:.1f}: already secured if current performance is maintained.")
        elif needed > 10:
            statements.append(f"Target {target:.1f}: not realistically reachable because it would require SGPA {needed:.2f}.")
        else:
            statements.append(f"Target {target:.1f}: need average SGPA {needed:.2f} across the remaining {remaining_semesters} semester(s).")
    return " ".join(statements)


def _chunk_metadata(student: Student, chunk_type: str, updated_at: str) -> Dict[str, str]:
    return {
        "student_id": str(student.id),
        "chunk_type": chunk_type,
        "student_name": student.user.full_name,
        "updated_at": updated_at,
    }


def build_chunks(student_id: int, db: Session) -> List[Dict]:
    student = _load_student(student_id, db)
    semester_records = _sorted_semesters(student)
    attendance_records = _sorted_attendance(student)
    backlog_rows = _all_backlogs(semester_records)
    total_backlogs = len(backlog_rows)
    latest_risk = (
        max(student.risk_scores, key=lambda item: item.computed_at or datetime.min.replace(tzinfo=timezone.utc))
        if student.risk_scores
        else None
    )
    progression = _compute_cgpa_points(semester_records)
    trend_direction = _trend_from_progression(progression)
    updated_at = _iso_now()

    chunks: List[Dict] = []

    identity_content = (
        f"Student identity record for {student.user.full_name}. "
        f"Roll number: {student.user.roll_number or 'N/A'}. "
        f"Branch: {student.branch or 'N/A'}. "
        f"Current semester: {student.current_semester}. "
        f"CGPA: {_format_float(student.cgpa)}. "
        f"Enrollment year: {student.enrollment_year or 'N/A'}. "
        f"Total backlog count: {total_backlogs}."
    )
    chunks.append(
        {
            "id": f"s{student.id}_identity",
            "content": identity_content,
            "metadata": _chunk_metadata(student, "identity", updated_at),
        }
    )

    if latest_risk:
        factor_breakdown = latest_risk.factor_breakdown or {}
        placement_eligible = (student.cgpa or 0.0) >= 7.5 and total_backlogs == 0
        risk_content = (
            f"Risk summary for {student.user.full_name}. "
            f"SARS score: {_format_float(latest_risk.sars_score)}. "
            f"Risk level: {latest_risk.risk_level}. "
            f"Confidence: {_format_float(latest_risk.confidence)}. "
            f"GPA risk value: {factor_breakdown.get('gpa_risk', 'N/A')}. "
            f"Backlog risk value: {factor_breakdown.get('backlog_risk', 'N/A')}. "
            f"Attendance risk value: {factor_breakdown.get('attendance_risk', 'N/A')}. "
            f"Trend direction: {trend_direction}. "
            f"Advisory text: {latest_risk.advisory_text or 'No advisory available.'} "
            f"Placement eligibility using the 7.5 CGPA cutoff and backlog rule: "
            f"{'eligible' if placement_eligible else 'not eligible'}."
        )
        chunks.append(
            {
                "id": f"s{student.id}_risk_summary",
                "content": risk_content,
                "metadata": _chunk_metadata(student, "risk_summary", updated_at),
            }
        )

    for record in semester_records:
        when = record.uploaded_at.strftime("%B %Y") if record.uploaded_at else "Unknown month"
        subject_bits = []
        backlog_names = []
        for subject in sorted(record.subjects, key=lambda item: (item.subject_name or "").lower()):
            subject_bits.append(
                f"{subject.subject_name} {subject.grade_letter or 'N/A'} {_format_float(subject.credits)} credits"
            )
            if subject.is_backlog:
                backlog_names.append(subject.subject_name)
        semester_content = (
            f"Semester {record.semester_no} ({when}): "
            f"SGPA {_format_float(record.gpa)}, "
            f"Credits attempted {_format_float(record.credits_attempted)}, "
            f"Credits earned {_format_float(record.credits_earned)}. "
            f"Subjects: {', '.join(subject_bits) if subject_bits else 'None'}. "
            f"Backlogs this semester: {', '.join(backlog_names) if backlog_names else 'None'}."
        )
        chunk_type = f"semester_{record.semester_no}"
        chunks.append(
            {
                "id": f"s{student.id}_{chunk_type}",
                "content": semester_content,
                "metadata": _chunk_metadata(student, chunk_type, updated_at),
            }
        )

    if backlog_rows:
        backlog_lines = []
        for semester_no, subject in backlog_rows:
            backlog_lines.append(
                f"{subject.subject_name} (semester {semester_no}, subject code {subject.subject_code or 'N/A'})"
            )
        backlog_content = (
            f"Backlog record for {student.user.full_name}. "
            f"All current backlogs: {', '.join(backlog_lines)}. "
            f"Clearing priority recommendation: clear the oldest backlogs first, then any high-credit subjects. "
            f"Placement impact statement: placements remain blocked until backlog count reaches zero."
        )
        chunks.append(
            {
                "id": f"s{student.id}_backlogs",
                "content": backlog_content,
                "metadata": _chunk_metadata(student, "backlogs", updated_at),
            }
        )

    if attendance_records:
        valid_percentages = [record.percentage for record in attendance_records if record.percentage is not None]
        average_attendance = sum(valid_percentages) / len(valid_percentages) if valid_percentages else 0.0
        per_subject = [
            f"Semester {record.semester_no} {record.subject_name}: {_format_float(record.percentage)}%"
            for record in attendance_records
        ]
        below_threshold = [
            f"Semester {record.semester_no} {record.subject_name}"
            for record in attendance_records
            if (record.percentage or 0.0) < 75.0
        ]
        attendance_content = (
            f"Attendance summary for {student.user.full_name}. "
            f"Average attendance percentage: {average_attendance:.2f}%. "
            f"Per-subject attendance details: {'; '.join(per_subject)}. "
            f"Subjects below 75% threshold: {', '.join(below_threshold) if below_threshold else 'None'}. "
            f"Exam eligibility impact: "
            f"{'at risk in subjects below 75% attendance' if below_threshold else 'no known attendance-based exam eligibility risk'}."
        )
        chunks.append(
            {
                "id": f"s{student.id}_attendance",
                "content": attendance_content,
                "metadata": _chunk_metadata(student, "attendance", updated_at),
            }
        )

    if progression:
        sgpa_path = ", ".join(
            f"Semester {item['semester_no']}: SGPA {item['sgpa']:.2f}" for item in progression
        )
        cgpa_path = ", ".join(
            f"after semester {item['semester_no']} CGPA {item['cgpa']:.2f}" for item in progression
        )
        trajectory_content = (
            f"CGPA trajectory for {student.user.full_name}. "
            f"Semester-by-semester SGPA values in chronological order: {sgpa_path}. "
            f"CGPA after each semester: {cgpa_path}. "
            f"Trend analysis: {trend_direction}. "
            f"{_target_cgpa_guidance(student, progression)}"
        )
        chunks.append(
            {
                "id": f"s{student.id}_cgpa_trajectory",
                "content": trajectory_content,
                "metadata": _chunk_metadata(student, "cgpa_trajectory", updated_at),
            }
        )

    logger.info("Built %s chunks for student %s", len(chunks), student_id)
    return chunks


def index_student(student_id: int, db: Session) -> Dict:
    chunks = build_chunks(student_id, db)
    collection = get_vector_store()

    try:
        collection.delete(where={"student_id": str(student_id)})
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not clear old chunks for student %s: %s", student_id, exc)

    ids: List[str] = []
    embeddings: List[List[float]] = []
    documents: List[str] = []
    metadatas: List[Dict[str, str]] = []

    for chunk in chunks:
        embedding = _embed_text(chunk["content"])
        ids.append(chunk["id"])
        embeddings.append(embedding)
        documents.append(chunk["content"])
        metadatas.append(chunk["metadata"])

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    status = get_rag_status(student_id, db)
    result = {
        "success": True,
        "chunks_indexed": len(ids),
        "chunk_types": [item["metadata"]["chunk_type"] for item in chunks],
        "status": status,
        "error": None,
    }
    logger.info("Indexed %s chunks for student %s", len(ids), student_id)
    return result


def retrieve(student_id: int, query: str, n: int = 4) -> List[Dict]:
    collection = get_vector_store()
    query_embedding = _embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        where={"student_id": str(student_id)},
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved: List[Dict] = []
    for idx, chunk_id in enumerate(ids):
        distance = distances[idx] if idx < len(distances) else 1.0
        relevance_score = max(0.0, min(1.0, 1.0 - float(distance)))
        retrieved.append(
            {
                "id": chunk_id,
                "content": documents[idx],
                "metadata": metadatas[idx],
                "relevance_score": relevance_score,
            }
        )
    return retrieved


def get_rag_status(student_id: int, db: Session) -> Dict:
    collection = get_vector_store()
    results = collection.get(where={"student_id": str(student_id)}, include=["metadatas"])
    ids = results.get("ids", [])
    metadatas = results.get("metadatas", [])

    timestamps = [meta.get("updated_at") for meta in metadatas if meta and meta.get("updated_at")]
    chunk_types = [meta.get("chunk_type") for meta in metadatas if meta and meta.get("chunk_type")]

    return {
        "indexed": len(ids) > 0,
        "chunk_count": len(ids),
        "last_indexed": max(timestamps) if timestamps else None,
        "chunk_types": sorted(chunk_types),
    }


def delete_student_index(student_id: int) -> None:
    collection = get_vector_store()
    collection.delete(where={"student_id": str(student_id)})
    logger.info("Deleted RAG index for student %s", student_id)
