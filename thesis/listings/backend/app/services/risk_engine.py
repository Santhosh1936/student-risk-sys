"""
risk_engine.py -- SARS Risk Score Computation Engine
=====================================================
Computes the SARS score (0-100) for a given student using:
  GPA Trend      40%
  Backlog Count  35%
  Attendance     25%

Called automatically when student confirms a grade upload.
Also callable manually via POST /student/compute-risk.
Stores result in risk_scores table.
"""

import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.models import (
    Student, SemesterRecord, SubjectGrade,
    AttendanceRecord, RiskScore
)

logger = logging.getLogger(__name__)


def compute_cgpa(student_id: int, db: Session):
    """
    Compute CGPA using the official JNTUH credits-weighted formula:
      CGPA = Σ(SGPA_i × credits_attempted_i) / Σ(credits_attempted_i)

    Returns None if no semester records exist or all records lack
    credit data. Returns a float rounded to 2 decimal places.

    This is the ONLY correct way to compute CGPA for JNTUH students.
    Simple average of SGPAs is WRONG because semesters have
    different credit loads (labs = 1.5cr, theory = 3cr etc.)
    """
    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student_id)
        .all()
    )

    if not records:
        return None

    total_weighted_points = 0.0
    total_credits = 0.0

    for rec in records:
        sgpa = float(rec.gpa) if rec.gpa is not None else None
        credits = (
            float(rec.credits_attempted)
            if rec.credits_attempted is not None
            else None
        )

        # Skip semesters with missing data
        if sgpa is None or credits is None or credits == 0:
            continue

        total_weighted_points += sgpa * credits
        total_credits += credits

    if total_credits == 0:
        return None

    return round(total_weighted_points / total_credits, 2)


def compute_risk_score(student_id: int, db: Session) -> dict:
    """
    Compute SARS risk score for a student and save to risk_scores table.
    Returns the full factor breakdown dict.
    Called after every confirmed grade upload and on demand.
    """

    # -- Fetch student --------------------------------------------------------
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student id={student_id} not found")

    # -- Fetch all semester records ordered by semester number ----------------
    records = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student_id)
        .order_by(SemesterRecord.semester_no)
        .all()
    )
    semesters_analyzed = len(records)

    # -- Compute CGPA using credits-weighted JNTUH formula --------------------
    computed_cgpa = compute_cgpa(student_id, db)
    if computed_cgpa is not None:
        cgpa = computed_cgpa
    else:
        cgpa = float(student.cgpa) if student.cgpa else 0.0

    # -- Fetch all subject grades to count backlogs ---------------------------
    all_grades = []
    for rec in records:
        grades = (
            db.query(SubjectGrade)
            .filter(SubjectGrade.semester_record_id == rec.id)
            .all()
        )
        all_grades.extend(grades)

    total_backlogs = sum(1 for g in all_grades if g.is_backlog)

    # -- Fetch attendance records ---------------------------------------------
    attendance_records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .all()
    )
    has_attendance = len(attendance_records) > 0

    # =========================================================================
    # COMPONENT 1 -- GPA Risk (40%)
    # =========================================================================

    gpa_risk = max(0.0, (7.5 - cgpa) / 7.5) * 100.0

    # GPA trend bonus/deduction
    trend_direction = "stable"
    trend_bonus = 0.0

    if semesters_analyzed >= 2:
        latest_gpa = float(records[-1].gpa) if records[-1].gpa is not None else cgpa
        prev_gpa = float(records[-2].gpa) if records[-2].gpa is not None else cgpa
        trend = latest_gpa - prev_gpa

        if trend < -0.5:
            trend_direction = "declining_sharply"
            trend_bonus = 10.0
        elif trend < 0.0:
            trend_direction = "declining"
            trend_bonus = 5.0
        elif trend > 0.5:
            trend_direction = "improving"
            trend_bonus = -5.0
        else:
            trend_direction = "stable"
            trend_bonus = 0.0

    gpa_risk = min(100.0, max(0.0, gpa_risk + trend_bonus))

    # =========================================================================
    # COMPONENT 2 -- Backlog Risk (35%)
    # =========================================================================

    # Non-linear backlog risk: steeper penalty as backlog count grows
    # 0→0, 1→40, 2→60, 3→80, 4→90, 5+→100
    if total_backlogs == 0:
        backlog_risk = 0.0
    elif total_backlogs == 1:
        backlog_risk = 40.0
    elif total_backlogs == 2:
        backlog_risk = 60.0
    elif total_backlogs == 3:
        backlog_risk = 80.0
    elif total_backlogs == 4:
        backlog_risk = 90.0
    else:
        backlog_risk = 100.0

    # =========================================================================
    # COMPONENT 3 -- Attendance Risk (25%)
    # =========================================================================

    avg_attendance = None

    if has_attendance:
        percentages = [
            float(a.percentage)
            for a in attendance_records
            if a.percentage is not None
        ]
        if percentages:
            avg_attendance = sum(percentages) / len(percentages)
            attendance_risk = max(
                0.0,
                (75.0 - avg_attendance) / 75.0 * 100.0
            )
        else:
            attendance_risk = 25.0
    else:
        # No data -- apply neutral penalty
        attendance_risk = 25.0

    # =========================================================================
    # FINAL SARS SCORE
    # =========================================================================

    gpa_component        = round(gpa_risk * 0.40, 4)
    backlog_component    = round(backlog_risk * 0.35, 4)
    attendance_component = round(attendance_risk * 0.25, 4)

    sars_score = round(
        gpa_component + backlog_component + attendance_component, 2
    )

    # -- Risk Level -----------------------------------------------------------
    if sars_score < 25.0:
        risk_level = "LOW"
    elif sars_score < 50.0:
        risk_level = "WATCH"
    elif sars_score < 75.0:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    # -- Placement-policy floors (SNIST placement cutoff: CGPA 7.5) -----------
    # CGPA-based floors
    if cgpa < 5.0 and risk_level != "HIGH":
        risk_level = "HIGH"
    elif cgpa < 7.0 and risk_level in ("LOW", "WATCH"):
        risk_level = "MODERATE"
    elif cgpa < 7.5 and risk_level == "LOW":
        risk_level = "WATCH"

    # Backlog-based floors: 1-2 → MODERATE, 3+ → HIGH
    if total_backlogs >= 3 and risk_level != "HIGH":
        risk_level = "HIGH"
    elif total_backlogs >= 1 and risk_level in ("LOW", "WATCH"):
        risk_level = "MODERATE"

    # -- Confidence -----------------------------------------------------------
    if semesters_analyzed >= 2 and has_attendance:
        confidence = 1.0
    elif semesters_analyzed >= 2:
        confidence = 0.75
    elif semesters_analyzed == 1:
        confidence = 0.6
    else:
        confidence = 0.4

    # -- Factor Breakdown -----------------------------------------------------
    factor_breakdown = {
        "gpa_risk": round(gpa_risk, 2),
        "backlog_risk": round(backlog_risk, 2),
        "attendance_risk": round(attendance_risk, 2),
        "gpa_component": round(gpa_component, 2),
        "backlog_component": round(backlog_component, 2),
        "attendance_component": round(attendance_component, 2),
        "sars_score": sars_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "semesters_analyzed": semesters_analyzed,
        "total_backlogs": total_backlogs,
        "cgpa": round(cgpa, 2),
        "avg_attendance": round(avg_attendance, 2) if avg_attendance else None,
        "trend_direction": trend_direction,
        "trend_bonus": trend_bonus,
    }

    # -- Advisory Text --------------------------------------------------------
    advisory_text = _generate_advisory_text(
        risk_level, cgpa, total_backlogs,
        avg_attendance, trend_direction, semesters_analyzed
    )

    # -- Sync computed CGPA back to student profile ---------------------------
    student.cgpa = round(cgpa, 2)

    # -- Save to risk_scores table --------------------------------------------
    # Insert new risk score row (history is preserved)
    risk_row = RiskScore(
        student_id=student_id,
        computed_at=datetime.now(timezone.utc),
        sars_score=sars_score,
        risk_level=risk_level,
        confidence=confidence,
        factor_breakdown=json.dumps(factor_breakdown),
        advisory_text=advisory_text,
    )
    db.add(risk_row)
    db.commit()

    logger.info(
        f"Risk computed for student_id={student_id}: "
        f"score={sars_score}, level={risk_level}"
    )

    return factor_breakdown


def _generate_advisory_text(
    risk_level: str,
    cgpa: float,
    backlogs: int,
    attendance,
    trend: str,
    semesters: int
) -> str:
    """
    Generate a plain-English advisory message based on risk factors.
    This is a rule-based summary shown under the risk score card.
    Goal 4 will replace this with full AI advisory chatbot.
    """
    lines = []

    if risk_level == "LOW":
        lines.append(
            "Your academic performance is on track. Keep it up!"
        )
    elif risk_level == "WATCH":
        lines.append(
            "Your performance needs attention. Small improvements "
            "now will prevent bigger problems later."
        )
    elif risk_level == "MODERATE":
        lines.append(
            "You are at moderate academic risk. Immediate action "
            "is recommended to improve your standing."
        )
    else:
        lines.append(
            "You are at HIGH academic risk. Please meet your "
            "academic advisor as soon as possible."
        )

    if cgpa < 5.0:
        lines.append(
            f"Your CGPA of {cgpa:.2f} is critically low. "
            "Focus on core subjects immediately."
        )
    elif cgpa < 7.0:
        lines.append(
            f"Your CGPA of {cgpa:.2f} needs significant improvement. "
            "A CGPA of 7.5+ is required for most campus placements."
        )
    elif cgpa < 7.5:
        lines.append(
            f"Your CGPA of {cgpa:.2f} is borderline for placements. "
            "Aim to push above 7.5 to unlock full placement eligibility."
        )

    if backlogs >= 3:
        lines.append(
            f"You have {backlogs} active backlog subjects — this is HIGH risk. "
            "You are completely ineligible for campus placements until all backlogs are cleared. "
            "Meet your academic advisor immediately."
        )
    elif backlogs > 0:
        lines.append(
            f"You have {backlogs} active backlog subject{'s' if backlogs > 1 else ''}. "
            "Students with any backlog are not eligible for campus placements. "
            "Clearing all backlogs must be your top priority."
        )

    if trend == "declining_sharply":
        lines.append(
            "Your GPA dropped sharply compared to the previous "
            "semester. Identify the weak subjects and seek help."
        )
    elif trend == "declining":
        lines.append(
            "Your GPA is declining. Review your study plan and "
            "focus on subjects where you scored below B+."
        )
    elif trend == "improving":
        lines.append(
            "Your GPA is improving -- great progress! "
            "Maintain this momentum."
        )

    if attendance is not None and attendance < 75.0:
        lines.append(
            f"Your attendance of {attendance:.1f}% is below the "
            "required 75%. Low attendance affects exam eligibility."
        )

    if semesters < 2:
        lines.append(
            "Upload more semester marksheets for a more accurate "
            "risk assessment."
        )

    return " ".join(lines)


def get_student_risk(student_id: int, db: Session):
    """
    Fetch the latest stored risk score for a student.
    Returns None if not yet computed.
    """
    risk = (
        db.query(RiskScore)
        .filter(RiskScore.student_id == student_id)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )
    if not risk:
        return None

    breakdown = {}
    try:
        breakdown = json.loads(risk.factor_breakdown or "{}")
    except Exception:
        pass

    return {
        "sars_score": risk.sars_score,
        "risk_level": risk.risk_level,
        "confidence": risk.confidence,
        "computed_at": risk.computed_at.isoformat()
                       if risk.computed_at else None,
        "advisory_text": risk.advisory_text,
        "factor_breakdown": breakdown,
    }
