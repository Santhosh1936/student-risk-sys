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

    # -- Compute CGPA as mean of all available SGPAs --------------------------
    valid_gpas = [float(r.gpa) for r in records if r.gpa is not None]
    if valid_gpas:
        cgpa = sum(valid_gpas) / len(valid_gpas)
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

    gpa_risk = max(0.0, (7.0 - cgpa) / 7.0) * 100.0

    # GPA trend bonus/deduction
    trend_direction = "stable"
    trend_bonus = 0.0

    if semesters_analyzed >= 2:
        latest_gpa = float(records[-1].gpa) if records[-1].gpa else cgpa
        prev_gpa = float(records[-2].gpa) if records[-2].gpa else cgpa
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

    backlog_risk = min(100.0, float(total_backlogs) * 20.0)

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
    # Delete previous score and insert fresh one
    db.query(RiskScore).filter(
        RiskScore.student_id == student_id
    ).delete()

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
            f"Your CGPA of {cgpa:.2f} is below the minimum "
            "threshold. Focus on core subjects immediately."
        )
    elif cgpa < 6.5:
        lines.append(
            f"Your CGPA of {cgpa:.2f} needs improvement. "
            "Aim to score above 7.0 in upcoming semesters."
        )

    if backlogs > 0:
        lines.append(
            f"You have {backlogs} backlog subject"
            f"{'s' if backlogs > 1 else ''}. "
            "Clearing backlogs should be your top priority."
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
