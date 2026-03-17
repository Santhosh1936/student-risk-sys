import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models.models import (
    User, Student, Teacher, SemesterRecord, SubjectGrade,
    AttendanceRecord, RiskScore, Intervention,
)
from ..services.dependencies import require_teacher
from ..services.risk_engine import get_student_risk

router = APIRouter(prefix="/teacher", tags=["Teacher"])

# ── Teacher dependency helper ─────────────────────────────────────────────────

def get_teacher_or_404(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
) -> Teacher:
    t = db.query(Teacher).filter(
        Teacher.user_id == current_user.id
    ).first()
    if not t:
        raise HTTPException(404, "Teacher profile not found.")
    return t

# ── Pydantic Schemas ───────────────────────────────────────────────────────────

class StudentSummary(BaseModel):
    user_id: int
    full_name: str
    roll_number: Optional[str]
    branch: Optional[str]
    current_semester: int
    cgpa: Optional[float]
    class Config:
        from_attributes = True


class LogInterventionRequest(BaseModel):
    student_id: int
    intervention_type: str
    notes: str


class ResolveInterventionRequest(BaseModel):
    outcome: str


# ── EXISTING Endpoints (unchanged) ────────────────────────────────────────────

@router.get("/profile")
def get_teacher_profile(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(
        Teacher.user_id == current_user.id
    ).first()
    if not teacher:
        raise HTTPException(404, "Teacher profile not found.")
    total_students = db.query(Student).count()
    return {
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "department": getattr(teacher, "department", None) or "",
        "employee_id": getattr(teacher, "employee_id", None) or "—",
        "total_students": total_students,
        "role": "teacher",
    }


@router.get("/students", response_model=List[StudentSummary])
def get_all_students(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    result = []
    for s in db.query(Student).all():
        user = db.query(User).filter(User.id == s.user_id).first()
        if user:
            result.append(StudentSummary(
                user_id=user.id,
                full_name=user.full_name,
                roll_number=user.roll_number,
                branch=s.branch,
                current_semester=s.current_semester,
                cgpa=s.cgpa,
            ))
    return result


@router.get("/risk-overview")
def get_risk_overview(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Returns ALL students ranked by SARS score (highest risk first).
    Used by Teacher Risk Monitor dashboard.
    Supports pagination via skip/limit query params.
    """
    students = db.query(Student).offset(skip).limit(limit).all()
    result = []

    all_users = {u.id: u for u in db.query(User).all()}
    # Map student_id -> latest risk score (bulk fetch)
    all_student_ids = [s.id for s in students]
    all_risks: dict = {}
    for risk in (
        db.query(RiskScore)
        .filter(RiskScore.student_id.in_(all_student_ids))
        .order_by(RiskScore.computed_at.desc())
        .all()
    ):
        if risk.student_id not in all_risks:
            all_risks[risk.student_id] = risk

    for student in students:
        user = all_users.get(student.user_id)
        risk_row = all_risks.get(student.id)
        risk_data = None
        if risk_row:
            risk_data = {
                "sars_score": risk_row.sars_score,
                "risk_level": risk_row.risk_level,
                "confidence": risk_row.confidence,
                "computed_at": risk_row.computed_at.isoformat() if risk_row.computed_at else None,
                "advisory_text": risk_row.advisory_text,
            }
        result.append({
            "student_id": student.id,
            "user_id": student.user_id,
            "full_name": user.full_name if user else "Unknown",
            "roll_number": user.roll_number if user else None,
            "branch": student.branch,
            "current_semester": student.current_semester,
            "cgpa": student.cgpa,
            "sars_score": risk_data["sars_score"] if risk_data else None,
            "risk_level": risk_data["risk_level"] if risk_data else "UNKNOWN",
            "confidence": risk_data["confidence"] if risk_data else None,
            "computed_at": risk_data["computed_at"] if risk_data else None,
            "advisory_text": risk_data["advisory_text"] if risk_data else None,
        })

    risk_order = {
        "HIGH": 0, "MODERATE": 1,
        "WATCH": 2, "LOW": 3, "UNKNOWN": 4,
    }
    result.sort(key=lambda x: risk_order.get(x["risk_level"], 4))
    return result


@router.get("/students/{student_id}/risk")
def get_student_risk_detail(
    student_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Returns full risk breakdown for a specific student.
    """
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()
    if not student:
        raise HTTPException(404, "Student not found.")

    user = db.query(User).filter(User.id == student.user_id).first()
    risk = get_student_risk(student.id, db)

    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student_id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )
    semester_gpas = [
        {"semester_no": r.semester_no, "gpa": r.gpa}
        for r in records
    ]

    return {
        "student_id": student_id,
        "full_name": user.full_name if user else "Unknown",
        "roll_number": user.roll_number if user else None,
        "branch": student.branch,
        "cgpa": student.cgpa,
        "current_semester": student.current_semester,
        "risk": risk,
        "semester_gpas": semester_gpas,
    }


# ── NEW Endpoints — Goal 5 ─────────────────────────────────────────────────────

@router.get("/students/{student_id}/profile")
def get_student_full_profile(
    student_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Full academic profile of one student.
    Includes: identity, all semesters with subjects,
    attendance per semester, risk score with breakdown,
    and full intervention history.
    """
    student = db.query(Student).filter(
        Student.id == student_id
    ).first()
    if not student:
        raise HTTPException(404, "Student not found.")

    user = db.query(User).filter(
        User.id == student.user_id
    ).first()

    # ── Semester records + subjects ───────────────────────────
    records = (
        db.query(SemesterRecord)
        .options(joinedload(SemesterRecord.subjects))
        .filter(SemesterRecord.student_id == student_id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )

    semesters = []
    total_backlogs = 0
    for rec in records:
        subjects = rec.subjects
        backlogs_this_sem = [s for s in subjects if s.is_backlog]
        total_backlogs += len(backlogs_this_sem)

        semesters.append({
            "semester_no": rec.semester_no,
            "sgpa": rec.gpa,
            "credits_attempted": rec.credits_attempted,
            "credits_earned": rec.credits_earned,
            "subject_count": len(subjects),
            "backlog_count": len(backlogs_this_sem),
            "subjects": [
                {
                    "subject_code": s.subject_code,
                    "subject_name": s.subject_name,
                    "grade_letter": s.grade_letter,
                    "grade_points": s.grade_points,
                    "credits": s.credits,
                    "is_backlog": s.is_backlog,
                }
                for s in subjects
            ],
        })

    # ── Attendance ────────────────────────────────────────────
    att_records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .order_by(
            AttendanceRecord.semester_no,
            AttendanceRecord.subject_name,
        )
        .all()
    )
    att_by_sem = {}
    for a in att_records:
        sem = a.semester_no
        if sem not in att_by_sem:
            att_by_sem[sem] = []
        att_by_sem[sem].append({
            "subject_name": a.subject_name,
            "classes_attended": a.classes_attended,
            "total_classes": a.total_classes,
            "percentage": a.percentage,
        })

    overall_att = None
    if att_records:
        pcts = [a.percentage for a in att_records
                if a.percentage is not None]
        overall_att = round(sum(pcts) / len(pcts), 2) if pcts else None

    # ── Risk score ────────────────────────────────────────────
    risk = (
        db.query(RiskScore)
        .filter(RiskScore.student_id == student_id)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )
    risk_data = None
    if risk:
        fb = risk.factor_breakdown
        if isinstance(fb, str):
            try:
                fb = json.loads(fb)
            except Exception:
                fb = {}
        risk_data = {
            "sars_score": risk.sars_score,
            "risk_level": risk.risk_level,
            "confidence": risk.confidence,
            "computed_at": (
                risk.computed_at.isoformat()
                if risk.computed_at else None
            ),
            "advisory_text": risk.advisory_text,
            "factor_breakdown": fb or {},
        }

    # ── Interventions ─────────────────────────────────────────
    interventions = (
        db.query(Intervention)
        .filter(Intervention.student_id == student_id)
        .order_by(Intervention.created_at.desc())
        .all()
    )
    intervention_list = [
        {
            "id": i.id,
            "intervention_type": i.intervention_type,
            "notes": i.notes,
            "status": "resolved" if i.resolved_at else "open",
            "created_at": (
                i.created_at.isoformat() if i.created_at else None
            ),
            "resolved_at": (
                i.resolved_at.isoformat() if i.resolved_at else None
            ),
            "outcome": i.outcome,
        }
        for i in interventions
    ]

    return {
        "student_id": student_id,
        "full_name": user.full_name if user else "Unknown",
        "email": user.email if user else None,
        "roll_number": user.roll_number if user else None,
        "branch": student.branch,
        "current_semester": student.current_semester,
        "cgpa": student.cgpa,
        "total_backlogs": total_backlogs,
        "semesters_uploaded": len(semesters),
        "overall_attendance": overall_att,
        "semesters": semesters,
        "attendance_by_semester": att_by_sem,
        "risk": risk_data,
        "interventions": intervention_list,
        "intervention_summary": {
            "total": len(intervention_list),
            "open": sum(
                1 for i in intervention_list
                if i["status"] == "open"
            ),
            "resolved": sum(
                1 for i in intervention_list
                if i["status"] == "resolved"
            ),
        },
    }


@router.post("/interventions", status_code=201)
def log_intervention(
    request: LogInterventionRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Log a new intervention for a student.
    Types: Counseling, Tutoring, Parent Meeting,
           Written Warning, Academic Probation, Other
    """
    teacher = db.query(Teacher).filter(
        Teacher.user_id == current_user.id
    ).first()
    if not teacher:
        raise HTTPException(404, "Teacher profile not found.")

    student = db.query(Student).filter(
        Student.id == request.student_id
    ).first()
    if not student:
        raise HTTPException(404, "Student not found.")

    valid_types = [
        "Counseling", "Tutoring", "Parent Meeting",
        "Written Warning", "Academic Probation", "Other",
    ]
    if request.intervention_type not in valid_types:
        raise HTTPException(
            400,
            f"Invalid type. Must be one of: {', '.join(valid_types)}",
        )
    if not request.notes or not request.notes.strip():
        raise HTTPException(400, "Notes cannot be empty.")

    intervention = Intervention(
        student_id=request.student_id,
        teacher_id=teacher.id,
        intervention_type=request.intervention_type,
        notes=request.notes.strip(),
        created_at=datetime.now(timezone.utc),
        resolved_at=None,
        outcome=None,
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)

    return {
        "message": "Intervention logged successfully.",
        "intervention_id": intervention.id,
        "student_id": request.student_id,
        "intervention_type": request.intervention_type,
        "created_at": intervention.created_at.isoformat(),
    }


@router.patch("/interventions/{intervention_id}/resolve")
def resolve_intervention(
    intervention_id: int,
    request: ResolveInterventionRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Mark an open intervention as resolved with an outcome."""
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if not intervention:
        raise HTTPException(404, "Intervention not found.")

    teacher = db.query(Teacher).filter(
        Teacher.user_id == current_user.id
    ).first()
    if not teacher:
        raise HTTPException(404, "Teacher profile not found.")
    if intervention.teacher_id != teacher.id:
        raise HTTPException(
            403,
            "You can only resolve your own interventions.",
        )

    if intervention.resolved_at is not None:
        raise HTTPException(400, "Already resolved.")
    if not request.outcome or not request.outcome.strip():
        raise HTTPException(400, "Outcome cannot be empty.")

    intervention.resolved_at = datetime.now(timezone.utc)
    intervention.outcome = request.outcome.strip()
    db.commit()

    return {
        "message": "Intervention resolved.",
        "intervention_id": intervention_id,
        "resolved_at": intervention.resolved_at.isoformat(),
        "outcome": intervention.outcome,
    }


@router.get("/interventions")
def get_all_interventions(
    status: Optional[str] = None,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Get all interventions across all students.
    Optional filter: ?status=open or ?status=resolved
    """
    query = db.query(Intervention)
    if status == "open":
        query = query.filter(Intervention.resolved_at == None)  # noqa: E711
    elif status == "resolved":
        query = query.filter(Intervention.resolved_at != None)  # noqa: E711

    interventions = query.order_by(
        Intervention.created_at.desc()
    ).all()

    result = []
    student_map = {s.id: s for s in db.query(Student).all()}
    user_map = {u.id: u for u in db.query(User).all()}
    for i in interventions:
        student = student_map.get(i.student_id)
        if not student:
            continue  # Skip orphaned interventions
        user = user_map.get(student.user_id)

        result.append({
            "id": i.id,
            "student_id": i.student_id,
            "student_name": user.full_name if user else "Unknown",
            "roll_number": user.roll_number if user else None,
            "branch": student.branch if student else None,
            "intervention_type": i.intervention_type,
            "notes": i.notes,
            "status": "resolved" if i.resolved_at else "open",
            "created_at": (
                i.created_at.isoformat() if i.created_at else None
            ),
            "resolved_at": (
                i.resolved_at.isoformat() if i.resolved_at else None
            ),
            "outcome": i.outcome,
        })

    return {
        "total": len(result),
        "open": sum(1 for i in result if i["status"] == "open"),
        "resolved": sum(
            1 for i in result if i["status"] == "resolved"
        ),
        "interventions": result,
    }


@router.get("/analytics")
def get_analytics(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Class-wide analytics for the teacher dashboard.
    7 sections: CGPA distribution, risk breakdown,
    top backlog subjects, semester SGPA trend,
    branch-wise CGPA, attendance summary,
    intervention summary.
    """
    students = db.query(Student).all()
    total_students = len(students)

    if total_students == 0:
        return {"total_students": 0, "message": "No students yet."}

    # ── 1. CGPA Distribution ──────────────────────────────────
    cgpa_buckets = {
        "9.0 - 10.0": 0, "8.0 - 8.99": 0,
        "7.0 - 7.99": 0, "6.0 - 6.99": 0,
        "Below 6.0":  0, "No data":    0,
    }
    for s in students:
        c = float(s.cgpa) if s.cgpa else None
        if c is None:       cgpa_buckets["No data"]     += 1
        elif c >= 9.0:      cgpa_buckets["9.0 - 10.0"]  += 1
        elif c >= 8.0:      cgpa_buckets["8.0 - 8.99"]  += 1
        elif c >= 7.0:      cgpa_buckets["7.0 - 7.99"]  += 1
        elif c >= 6.0:      cgpa_buckets["6.0 - 6.99"]  += 1
        else:               cgpa_buckets["Below 6.0"]   += 1

    # ── 2. Risk Level Breakdown ───────────────────────────────
    risk_counts = {
        "HIGH": 0, "MODERATE": 0,
        "WATCH": 0, "LOW": 0, "NOT COMPUTED": 0,
    }
    # Bulk load for N+1 prevention
    all_risk_map: dict = {}
    for risk in db.query(RiskScore).order_by(RiskScore.computed_at.desc()).all():
        if risk.student_id not in all_risk_map:
            all_risk_map[risk.student_id] = risk

    all_att_map: dict = {}
    for att in db.query(AttendanceRecord).all():
        if att.student_id not in all_att_map:
            all_att_map[att.student_id] = []
        all_att_map[att.student_id].append(att)

    for s in students:
        risk = all_risk_map.get(s.id)
        level = risk.risk_level if risk else "NOT COMPUTED"
        risk_counts[level] = risk_counts.get(level, 0) + 1

    # ── 3. Top Backlog Subjects ───────────────────────────────
    backlogs = (
        db.query(SubjectGrade)
        .filter(SubjectGrade.is_backlog == True)  # noqa: E712
        .all()
    )
    backlog_counter: dict = {}
    for g in backlogs:
        name = g.subject_name or "Unknown"
        backlog_counter[name] = backlog_counter.get(name, 0) + 1

    top_backlogs = sorted(
        [{"subject": k, "count": v} for k, v in backlog_counter.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:5]

    # ── 4. Semester-wise Average SGPA Trend ──────────────────
    sem_data: dict = {}
    for rec in db.query(SemesterRecord).all():
        if rec.gpa is not None:
            sem = rec.semester_no
            if sem not in sem_data:
                sem_data[sem] = []
            sem_data[sem].append(float(rec.gpa))

    semester_trend = [
        {
            "semester_no": sem,
            "avg_sgpa": round(sum(v) / len(v), 2),
            "student_count": len(v),
        }
        for sem, v in sorted(sem_data.items())
    ]

    # ── 5. Branch-wise Average CGPA ──────────────────────────
    branch_data: dict = {}
    for s in students:
        branch = s.branch or "Unknown"
        c = float(s.cgpa) if s.cgpa else None
        if c is not None:
            if branch not in branch_data:
                branch_data[branch] = []
            branch_data[branch].append(c)

    branch_cgpa = sorted(
        [
            {
                "branch": b,
                "avg_cgpa": round(sum(v) / len(v), 2),
                "student_count": len(v),
            }
            for b, v in branch_data.items()
        ],
        key=lambda x: x["avg_cgpa"],
        reverse=True,
    )

    # ── 6. Attendance Summary ─────────────────────────────────
    att_students = {"above_75": 0, "below_75": 0, "no_data": 0}
    for s in students:
        recs = all_att_map.get(s.id, [])
        if not recs:
            att_students["no_data"] += 1
        else:
            pcts = [r.percentage for r in recs
                    if r.percentage is not None]
            avg = sum(pcts) / len(pcts) if pcts else 0
            if avg >= 75:
                att_students["above_75"] += 1
            else:
                att_students["below_75"] += 1

    # ── 7. Intervention Summary ───────────────────────────────
    all_interventions = db.query(Intervention).all()
    intervention_summary = {
        "total": len(all_interventions),
        "open": sum(
            1 for i in all_interventions if i.resolved_at is None
        ),
        "resolved": sum(
            1 for i in all_interventions if i.resolved_at is not None
        ),
        "by_type": {},
    }
    for i in all_interventions:
        t = i.intervention_type
        intervention_summary["by_type"][t] = (
            intervention_summary["by_type"].get(t, 0) + 1
        )

    return {
        "total_students": total_students,
        "cgpa_distribution": cgpa_buckets,
        "risk_breakdown": risk_counts,
        "top_backlog_subjects": top_backlogs,
        "semester_trend": semester_trend,
        "branch_cgpa": branch_cgpa,
        "attendance_summary": att_students,
        "intervention_summary": intervention_summary,
    }
