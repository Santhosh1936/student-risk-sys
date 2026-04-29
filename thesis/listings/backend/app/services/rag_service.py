"""
rag_service.py
==============
RAG engine for SARS advisor.

Vector DB choice: ChromaDB (persistent local storage, good Windows support,
no external server, and simple metadata filtering for student-scoped retrieval).
Orchestration choice: direct Gemini + Chroma calls (simpler than LangChain for
this project size and aligns with existing direct SDK/REST patterns).
"""

import json
import logging
from datetime import datetime
from typing import Dict, List

import chromadb
try:
    import google.generativeai as genai
except ImportError:
    genai = None
from sqlalchemy.orm import Session

from ..config import settings
from ..models.models import (
    AttendanceRecord,
    RiskScore,
    SemesterRecord,
    Student,
    SubjectGrade,
    User,
)

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "student_rag_chunks"
_gemini_configured = False
_client = None
_collection = None


def _configure_gemini_once() -> None:
    global _gemini_configured
    if _gemini_configured:
        return
    if genai is None:
        logger.warning("google-generativeai not installed; RAG/embedding features disabled")
        return
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _gemini_configured = True


def _extract_embedding(embed_result) -> List[float]:
    if isinstance(embed_result, dict):
        if "embedding" in embed_result:
            emb = embed_result["embedding"]
            if isinstance(emb, dict):
                values = emb.get("values")
                if isinstance(values, list):
                    return values
            if isinstance(emb, list):
                return emb
        if "embeddings" in embed_result and embed_result["embeddings"]:
            first = embed_result["embeddings"][0]
            if isinstance(first, dict):
                values = first.get("values")
                if isinstance(values, list):
                    return values

    emb_obj = getattr(embed_result, "embedding", None)
    if isinstance(emb_obj, list):
        return emb_obj
    if isinstance(emb_obj, dict) and isinstance(emb_obj.get("values"), list):
        return emb_obj["values"]

    raise ValueError("Unexpected embedding response format from Gemini")


def _embed_text(content: str, task_type: str) -> List[float]:
    if genai is None:
        raise ValueError("google-generativeai not installed; cannot generate embeddings")
    try:
        embed_result = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            content=content,
            task_type=task_type,
        )
    except Exception as exc:
        message = str(exc)
        if "API key expired" in message or "API_KEY_INVALID" in message:
            raise ValueError(
                "Gemini embedding failed because GEMINI_API_KEY is expired or invalid."
            ) from exc
        if "not found" in message and settings.GEMINI_EMBEDDING_MODEL in message:
            raise ValueError(
                f"Gemini embedding model '{settings.GEMINI_EMBEDDING_MODEL}' is not available "
                "for this SDK/API version."
            ) from exc
        raise

    return _extract_embedding(embed_result)


def get_vector_store():
    global _client, _collection
    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
    _collection = _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def _load_factor_breakdown(risk: RiskScore) -> Dict:
    if not risk or not risk.factor_breakdown:
        return {}
    if isinstance(risk.factor_breakdown, dict):
        return risk.factor_breakdown
    if isinstance(risk.factor_breakdown, str):
        try:
            return json.loads(risk.factor_breakdown)
        except Exception:
            return {}
    return {}


def _placement_statement(cgpa: float, total_backlogs: int) -> str:
    cgpa_ok = (cgpa or 0.0) >= 7.5
    backlog_ok = total_backlogs == 0
    if cgpa_ok and backlog_ok:
        return "Placement eligibility: ELIGIBLE (CGPA >= 7.5 and no backlogs)."

    blockers = []
    if not cgpa_ok:
        blockers.append("CGPA below 7.5 cutoff")
    if not backlog_ok:
        blockers.append(f"{total_backlogs} active backlog(s)")

    needed = []
    if not cgpa_ok:
        needed.append("raise CGPA to at least 7.5")
    if not backlog_ok:
        needed.append("clear all backlog subjects")

    return (
        "Placement eligibility: NOT ELIGIBLE. "
        f"Current blockers: {', '.join(blockers)}. "
        f"To become eligible: {', '.join(needed)}."
    )


def _cgpa_trajectory_text(records: List[SemesterRecord], subjects_by_record: Dict[int, List[SubjectGrade]]) -> str:
    if not records:
        return "No semester data available to compute CGPA trajectory."

    total_points = 0.0
    total_credits = 0.0
    lines = ["CGPA trajectory (chronological):"]

    previous_sgpa = None
    for rec in records:
        sgpa = float(rec.gpa) if rec.gpa is not None else 0.0
        credits = float(rec.credits_attempted) if rec.credits_attempted is not None else 0.0
        if credits > 0:
            total_points += sgpa * credits
            total_credits += credits
        running_cgpa = round(total_points / total_credits, 2) if total_credits > 0 else None

        trend_note = ""
        if previous_sgpa is not None:
            diff = sgpa - previous_sgpa
            if diff > 0.5:
                trend_note = " (improving strongly)"
            elif diff > 0.0:
                trend_note = " (improving)"
            elif diff < -0.5:
                trend_note = " (declining sharply)"
            elif diff < 0.0:
                trend_note = " (declining)"
            else:
                trend_note = " (stable)"
        previous_sgpa = sgpa

        lines.append(
            f"- Semester {rec.semester_no}: SGPA {sgpa:.2f}, "
            f"CGPA after semester {rec.semester_no}: {running_cgpa if running_cgpa is not None else 'N/A'}{trend_note}."
        )

    max_sem = max(r.semester_no for r in records)
    total_semesters_program = 8
    remaining_semesters = max(0, total_semesters_program - max_sem)
    avg_credits = (total_credits / len(records)) if records else 20.0
    remaining_credits = round(remaining_semesters * avg_credits, 2)

    current_cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    lines.append(f"Current CGPA after semester {max_sem}: {current_cgpa}.")

    def target_line(target: float) -> str:
        if remaining_credits <= 0:
            if current_cgpa >= target:
                return f"- Target {target:.1f}: already achieved with no remaining semesters."
            return f"- Target {target:.1f}: not achievable now (no remaining semesters)."

        required_avg = (
            (target * (total_credits + remaining_credits)) - total_points
        ) / remaining_credits

        if required_avg > 10.0:
            return (
                f"- Target {target:.1f}: not realistically achievable. "
                f"Required average SGPA in remaining semesters is {required_avg:.2f}."
            )
        if required_avg <= 0:
            return f"- Target {target:.1f}: already secured even with low SGPA in remaining semesters."

        return (
            f"- Target {target:.1f}: need average SGPA {required_avg:.2f} "
            f"across remaining {remaining_semesters} semester(s)."
        )

    lines.append("CGPA targets for remaining semesters:")
    lines.append(target_line(7.5))
    lines.append(target_line(8.0))
    lines.append(target_line(9.0))
    return "\n".join(lines)


def build_chunks(student_id: int, db: Session) -> List[Dict]:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student id={student_id} not found")

    user = db.query(User).filter(User.id == student.user_id).first()
    student_name = user.full_name if user and user.full_name else "Unknown Student"

    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student_id)
        .order_by(SemesterRecord.semester_no.asc())
        .all()
    )

    subjects_by_record: Dict[int, List[SubjectGrade]] = {}
    all_backlogs = []

    for rec in records:
        subjects = (
            db.query(SubjectGrade)
            .filter(SubjectGrade.semester_record_id == rec.id)
            .order_by(SubjectGrade.subject_name.asc())
            .all()
        )
        subjects_by_record[rec.id] = subjects
        for sub in subjects:
            if sub.is_backlog:
                all_backlogs.append(
                    {
                        "semester_no": rec.semester_no,
                        "subject_name": sub.subject_name,
                        "subject_code": sub.subject_code or "N/A",
                    }
                )

    risk = (
        db.query(RiskScore)
        .filter(RiskScore.student_id == student_id)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )
    breakdown = _load_factor_breakdown(risk) if risk else {}

    attendance_records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .order_by(AttendanceRecord.semester_no.asc(), AttendanceRecord.subject_name.asc())
        .all()
    )

    total_backlogs = len(all_backlogs)
    cgpa_value = float(student.cgpa) if student.cgpa is not None else 0.0
    placement_text = _placement_statement(cgpa_value, total_backlogs)

    chunks: List[Dict] = []

    chunks.append(
        {
            "id": f"s{student_id}_identity",
            "text": (
                f"Student identity profile: Name {student_name}. "
                f"Roll number {user.roll_number if user else 'N/A'}. "
                f"Branch {student.branch or 'N/A'}. Current semester {student.current_semester or 'N/A'}. "
                f"CGPA {student.cgpa if student.cgpa is not None else 'N/A'}. "
                f"Enrollment year {student.enrollment_year if student.enrollment_year is not None else 'N/A'}. "
                f"Total backlog count {total_backlogs}."
            ),
            "metadata": {
                "student_id": str(student_id),
                "chunk_type": "identity",
                "student_name": student_name,
            },
        }
    )

    risk_summary_lines = [
        "Risk summary:",
        f"- SARS score: {risk.sars_score if risk else 'N/A'}",
        f"- Risk level: {risk.risk_level if risk else 'N/A'}",
        f"- Confidence: {risk.confidence if risk else 'N/A'}",
    ]
    if breakdown:
        risk_summary_lines.append("- Factor breakdown values:")
        for key in sorted(breakdown.keys()):
            risk_summary_lines.append(f"  - {key}: {breakdown[key]}")
    risk_summary_lines.append(f"- Advisory text: {risk.advisory_text if risk else 'N/A'}")
    risk_summary_lines.append(f"- {placement_text}")

    chunks.append(
        {
            "id": f"s{student_id}_risk_summary",
            "text": "\n".join(risk_summary_lines),
            "metadata": {
                "student_id": str(student_id),
                "chunk_type": "risk_summary",
                "student_name": student_name,
            },
        }
    )

    for rec in records:
        uploaded_str = (
            rec.uploaded_at.strftime("%b %Y")
            if isinstance(rec.uploaded_at, datetime)
            else "Unknown Date"
        )
        subjects = subjects_by_record.get(rec.id, [])
        subject_bits = []
        sem_backlogs = []
        for sub in subjects:
            subject_bits.append(
                f"{sub.subject_name} Grade {sub.grade_letter or 'N/A'} Credits {sub.credits if sub.credits is not None else 'N/A'}"
            )
            if sub.is_backlog:
                sem_backlogs.append(sub.subject_name)

        semester_text = (
            f"Semester {rec.semester_no} ({uploaded_str}): "
            f"SGPA {rec.gpa if rec.gpa is not None else 'N/A'}, "
            f"Credits {rec.credits_attempted if rec.credits_attempted is not None else 'N/A'}. "
            f"Subjects: {', '.join(subject_bits) if subject_bits else 'No subjects available'}. "
            f"Backlogs this semester: {', '.join(sem_backlogs) if sem_backlogs else 'None'}."
        )

        chunks.append(
            {
                "id": f"s{student_id}_semester_{rec.semester_no}",
                "text": semester_text,
                "metadata": {
                    "student_id": str(student_id),
                    "chunk_type": f"semester_{rec.semester_no}",
                    "student_name": student_name,
                },
            }
        )

    if total_backlogs > 0:
        backlog_lines = [
            f"Backlog analysis for {student_name}: total backlogs {total_backlogs}.",
            "All backlog subjects with semester number and code:",
        ]
        for bl in all_backlogs:
            backlog_lines.append(
                f"- Semester {bl['semester_no']}: {bl['subject_name']} ({bl['subject_code']})"
            )
        backlog_lines.append(
            "Clearing priority advice: clear oldest and core subjects first, then high-credit subjects. "
            "Placement impact: any active backlog blocks campus placement eligibility."
        )

        chunks.append(
            {
                "id": f"s{student_id}_backlogs",
                "text": "\n".join(backlog_lines),
                "metadata": {
                    "student_id": str(student_id),
                    "chunk_type": "backlogs",
                    "student_name": student_name,
                },
            }
        )

    if attendance_records:
        percentages = [a.percentage for a in attendance_records if a.percentage is not None]
        avg_pct = round(sum(percentages) / len(percentages), 2) if percentages else None

        att_lines = [
            f"Attendance summary for {student_name}: average percentage {avg_pct if avg_pct is not None else 'N/A'}.",
            "Per-subject attendance details:",
        ]
        below_75 = []
        for att in attendance_records:
            pct = att.percentage if att.percentage is not None else 0.0
            att_lines.append(
                f"- Semester {att.semester_no}: {att.subject_name} {pct:.2f}% "
                f"({att.classes_attended}/{att.total_classes})"
            )
            if pct < 75.0:
                below_75.append(f"{att.subject_name} (Sem {att.semester_no}, {pct:.2f}%)")

        att_lines.append(
            "Subjects below 75%: "
            + (", ".join(below_75) if below_75 else "None")
        )
        att_lines.append(
            "Exam eligibility impact: subjects below 75% may affect exam eligibility per policy."
        )

        chunks.append(
            {
                "id": f"s{student_id}_attendance",
                "text": "\n".join(att_lines),
                "metadata": {
                    "student_id": str(student_id),
                    "chunk_type": "attendance",
                    "student_name": student_name,
                },
            }
        )

    chunks.append(
        {
            "id": f"s{student_id}_cgpa_trajectory",
            "text": _cgpa_trajectory_text(records, subjects_by_record),
            "metadata": {
                "student_id": str(student_id),
                "chunk_type": "cgpa_trajectory",
                "student_name": student_name,
            },
        }
    )

    placement_lines = [
        f"Placement eligibility analysis for {student_name}.",
        placement_text,
        (
            "Detailed conditions: CGPA cutoff is 7.5 for most campus placements and "
            "students must clear all active backlogs."
        ),
    ]

    if cgpa_value < 7.5:
        placement_lines.append(
            f"Current CGPA is {cgpa_value:.2f}; needs improvement to reach at least 7.5."
        )
    if total_backlogs > 0:
        placement_lines.append(
            f"Current active backlogs: {total_backlogs}; all must be cleared for eligibility."
        )

    chunks.append(
        {
            "id": f"s{student_id}_placement_eligibility",
            "text": "\n".join(placement_lines),
            "metadata": {
                "student_id": str(student_id),
                "chunk_type": "placement_eligibility",
                "student_name": student_name,
            },
        }
    )

    return chunks


def delete_student_index(student_id: int) -> None:
    collection = get_vector_store()
    collection.delete(where={"student_id": str(student_id)})


def index_student(student_id: int, db: Session) -> Dict:
    _configure_gemini_once()
    collection = get_vector_store()

    chunks = build_chunks(student_id, db)
    delete_student_index(student_id)

    ids = []
    documents = []
    metadatas = []
    embeddings = []

    for chunk in chunks:
        emb = _embed_text(
            content=chunk["text"],
            task_type="retrieval_document",
        )

        ids.append(chunk["id"])
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        embeddings.append(emb)

    if ids:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    logger.info("Indexed %s RAG chunks for student_id=%s", len(chunks), student_id)

    return {
        "chunk_count": len(chunks),
        "chunk_types": sorted({c["metadata"]["chunk_type"] for c in chunks}),
    }


def retrieve(student_id: int, query: str, n_results: int = 4) -> List[Dict]:
    _configure_gemini_once()
    collection = get_vector_store()

    query_embedding = _embed_text(
        content=query,
        task_type="retrieval_query",
    )

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"student_id": str(student_id)},
        include=["documents", "metadatas", "distances"],
    )

    docs = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    chunks = []
    for doc, meta, dist in zip(docs, metadatas, distances):
        distance = float(dist)
        if distance < 0.3:
            relevance = "HIGH"
        elif distance < 0.6:
            relevance = "MEDIUM"
        else:
            relevance = "LOW"

        chunks.append(
            {
                "text": doc,
                "chunk_type": (meta or {}).get("chunk_type", "unknown"),
                "distance": distance,
                "relevance": relevance,
            }
        )

    return chunks


def get_rag_status(student_id: int) -> Dict:
    collection = get_vector_store()
    data = collection.get(where={"student_id": str(student_id)}, include=["metadatas"])

    ids = data.get("ids") or []
    metadatas = data.get("metadatas") or []
    chunk_types = sorted({m.get("chunk_type") for m in metadatas if isinstance(m, dict) and m.get("chunk_type")})

    return {
        "indexed": len(ids) > 0,
        "chunk_count": len(ids),
        "chunk_types": chunk_types,
    }
