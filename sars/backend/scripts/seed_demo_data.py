"""
seed_demo_data.py
=================
Seeds 8 realistic demo students covering all SARS
risk categories for college presentation.

Uses real SNIST JNTUH subject names and codes.
Never modifies existing real student data.
Safe to run multiple times (skips existing emails).

Run from sars/backend/:
  python scripts/seed_demo_data.py

Login credentials for all demo students:
  Password: Demo@1234

Demo students:
  1. Ravi Kumar Sharma        - LOW    (Topper, 5 sems)
  2. Priya Reddy              - LOW    (Consistent performer)
  3. Arjun Naidu              - WATCH  (Declining trend)
  4. Sneha Patel              - WATCH  (Below placement cutoff)
  5. Mohammed Farhan          - MODERATE (2 backlogs)
  6. Lakshmi Devi             - MODERATE (Struggling, 1 backlog)
  7. Venkat Suresh            - HIGH   (4 backlogs, low CGPA)
  8. Divya Krishnamurthy      - HIGH   (Critical, 6 backlogs)
"""

import sys
import os
import json
import bcrypt
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import (
    User, Student, SemesterRecord,
    SubjectGrade, RiskScore
)

db = SessionLocal()

# ── HELPERS ───────────────────────────────────────────────────

def hash_pw(password: str) -> str:
    pw_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(
        pw_bytes, bcrypt.gensalt(rounds=12)
    ).decode('utf-8')

def get_grade_points(grade: str) -> int:
    return {
        "O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6,
        "C": 5, "D": 4, "F": 0, "AB": 0,
        "S*": 0, "NS": 0, "NS*": 0,
    }.get(grade.upper(), 0)

def is_backlog(grade: str) -> bool:
    return grade.upper() in ("F", "AB", "NS", "NS*")

def compute_cgpa(sems: list) -> float:
    total_pts = sum(s["sgpa"] * s["credits"] for s in sems
                    if s["credits"] > 0)
    total_cr  = sum(s["credits"] for s in sems
                    if s["credits"] > 0)
    return round(total_pts / total_cr, 2) if total_cr else 0.0

def make_advisory(risk_level, cgpa, backlogs,
                  trend, semesters):
    lines = []
    if risk_level == "LOW":
        lines.append(
            "Your academic performance is on track. "
            "Keep it up!"
        )
    elif risk_level == "WATCH":
        lines.append(
            "Your performance needs attention. "
            "Small improvements now will prevent "
            "bigger problems later."
        )
    elif risk_level == "MODERATE":
        lines.append(
            "You are at moderate academic risk. "
            "Immediate action is recommended."
        )
    else:
        lines.append(
            "You are at HIGH academic risk. "
            "Please meet your academic advisor "
            "immediately."
        )

    if cgpa < 5.0:
        lines.append(
            f"Your CGPA of {cgpa} is critically low. "
            "Focus on core subjects immediately."
        )
    elif cgpa < 7.0:
        lines.append(
            f"A CGPA of 7.5+ is required for most "
            f"campus placements. Your current CGPA "
            f"of {cgpa} needs improvement."
        )
    elif cgpa < 7.5:
        lines.append(
            f"Borderline for placements. Push above "
            f"7.5 CGPA to be eligible."
        )

    if backlogs >= 3:
        lines.append(
            f"You have {backlogs} backlogs. "
            "This is HIGH risk. You are completely "
            "ineligible for campus placements until "
            "all backlogs are cleared."
        )
    elif backlogs > 0:
        lines.append(
            f"You have {backlogs} backlog subject"
            f"{'s' if backlogs > 1 else ''}. "
            "Students with any backlog are not "
            "eligible for campus placements."
        )

    if trend == "declining_sharply":
        lines.append(
            "Your GPA dropped sharply. Identify "
            "weak subjects and seek help immediately."
        )
    elif trend == "declining":
        lines.append(
            "Your GPA is declining. Review your "
            "study plan and focus on weak subjects."
        )
    elif trend == "improving":
        lines.append("Your GPA is improving — great progress!")

    return " ".join(lines)

def seed_student(
    full_name, email, roll_number, branch,
    semesters_data, current_semester
):
    """
    semesters_data: list of dicts:
    {
      semester_no: int,
      sgpa: float,
      credits: float,  (credits_attempted)
      subjects: [
        (code, name, grade, credits)
      ]
    }
    """
    # Skip if already exists
    existing = db.query(User).filter(
        User.email == email.lower()
    ).first()
    if existing:
        print(f"  [SKIP] {full_name} already exists.")
        return

    # Create user
    user = User(
        email=email.lower(),
        full_name=full_name,
        roll_number=roll_number,
        role="student",
        password_hash=hash_pw("Demo@1234"),
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Compute CGPA
    cgpa = compute_cgpa(semesters_data)

    # Create student
    student = Student(
        user_id=user.id,
        branch=branch,
        enrollment_year=2022,
        current_semester=current_semester,
        cgpa=cgpa,
    )
    db.add(student)
    db.flush()

    # Create semester records + subjects
    all_backlogs = 0
    for sem in semesters_data:
        rec = SemesterRecord(
            student_id=student.id,
            semester_no=sem["semester_no"],
            gpa=sem["sgpa"],
            credits_attempted=sem["credits"],
            credits_earned=sum(
                cr for (_, _, gr, cr) in sem["subjects"]
                if not is_backlog(gr)
            ),
        )
        db.add(rec)
        db.flush()

        for (code, name, grade, cr) in sem["subjects"]:
            pts = get_grade_points(grade)
            bl  = is_backlog(grade)
            if bl:
                all_backlogs += 1
            sg = SubjectGrade(
                semester_record_id=rec.id,
                subject_code=code,
                subject_name=name,
                grade_letter=grade,
                grade_points=pts,
                credits=cr,
                is_backlog=bl,
            )
            db.add(sg)

    # Compute risk score
    gpa_risk = max(0.0, (7.5 - cgpa) / 7.5 * 100)

    # Non-linear backlog risk
    backlog_map = {0:0, 1:40, 2:60, 3:80, 4:90}
    backlog_risk = backlog_map.get(
        all_backlogs, 100 if all_backlogs >= 5 else 90
    )

    att_risk = 25.0
    gpa_comp  = round(gpa_risk  * 0.40, 2)
    bl_comp   = round(backlog_risk * 0.35, 2)
    att_comp  = round(att_risk   * 0.25, 2)
    sars_score = round(gpa_comp + bl_comp + att_comp, 2)

    # Trend detection
    if len(semesters_data) >= 2:
        diff = (semesters_data[-1]["sgpa"]
                - semesters_data[-2]["sgpa"])
        if diff < -0.8:
            trend = "declining_sharply"
            sars_score = min(100, sars_score + 10)
        elif diff < -0.2:
            trend = "declining"
            sars_score = min(100, sars_score + 5)
        elif diff > 0.5:
            trend = "improving"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Placement policy floor rules — PASS 1: CGPA-based (mirrors risk_engine.py)
    if cgpa < 5.0:
        risk_level = "HIGH"
        sars_score = max(sars_score, 75.0)
    elif cgpa < 7.0:
        risk_level = "MODERATE"
        sars_score = max(sars_score, 50.0)
    elif cgpa < 7.5:
        risk_level = "WATCH"
        sars_score = max(sars_score, 25.0)
    elif sars_score >= 75:
        risk_level = "HIGH"
    elif sars_score >= 50:
        risk_level = "MODERATE"
    elif sars_score >= 25:
        risk_level = "WATCH"
    else:
        risk_level = "LOW"

    # PASS 2: Backlog-based floors (separate — can upgrade from CGPA result)
    if all_backlogs >= 3 and risk_level != "HIGH":
        risk_level = "HIGH"
        sars_score = max(sars_score, 75.0)
    elif all_backlogs >= 1 and risk_level in ("LOW", "WATCH"):
        risk_level = "MODERATE"
        sars_score = max(sars_score, 50.0)

    confidence = 0.75 if len(semesters_data) >= 2 else 0.6

    fb = {
        "gpa_risk": round(gpa_risk, 2),
        "backlog_risk": round(backlog_risk, 2),
        "attendance_risk": att_risk,
        "gpa_component": gpa_comp,
        "backlog_component": bl_comp,
        "attendance_component": att_comp,
        "sars_score": sars_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "semesters_analyzed": len(semesters_data),
        "total_backlogs": all_backlogs,
        "cgpa": cgpa,
        "avg_attendance": None,
        "trend_direction": trend,
        "trend_bonus": (
            10 if trend == "declining_sharply"
            else 5 if trend == "declining"
            else -5 if trend == "improving"
            else 0
        ),
    }

    advisory = make_advisory(
        risk_level, cgpa, all_backlogs,
        trend, len(semesters_data)
    )

    risk_row = RiskScore(
        student_id=student.id,
        computed_at=datetime.now(timezone.utc),
        sars_score=sars_score,
        risk_level=risk_level,
        confidence=confidence,
        factor_breakdown=json.dumps(fb),
        advisory_text=advisory,
    )
    db.add(risk_row)
    db.commit()

    print(
        f"  [OK] {full_name:<30} | "
        f"CGPA:{cgpa:5.2f} | "
        f"Backlogs:{all_backlogs} | "
        f"SARS:{sars_score:5.1f} | "
        f"{risk_level}"
    )

# ══════════════════════════════════════════════════════
# STUDENT 1 — RAVI KUMAR SHARMA
# LOW risk | Topper | 5 semesters | CGPA ~9.1
# Story: Consistent excellent performer across all years
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Ravi Kumar Sharma",
    email="ravi.sharma.demo@snist.edu",
    roll_number="22311A12R1",
    branch="INFORMATION TECHNOLOGY",
    current_semester=6,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 9.5,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","O",3.0),
                ("9HC01","Essential English Language Skills","A+",2.0),
                ("9HC11","Matrix Algebra and Calculus","O",3.0),
                ("9FC01","Problem Solving Using C","A+",3.0),
                ("9HC64","Engineering Chemistry Lab","O",1.5),
                ("9HC61","Oral Communication Lab-I","O",1.0),
                ("9FC61","Problem Solving Using C Lab","O",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","O",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 9.2,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","O",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","A+",3.0),
                ("9EC01","Data Structures","O",3.0),
                ("9BC01","Engineering Graphics","A+",3.0),
                ("9HC07","Engineering Physics","A+",3.0),
                ("9EC61","Data Structures Using C Lab","O",1.5),
                ("9HC66","Engineering Physics Lab","O",1.5),
                ("9HC62","Oral Communication Lab-II","O",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 9.1,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","O",3.0),
                ("9F303","Discrete Mathematics","A+",3.0),
                ("9EC02","Object Oriented Programming Through Java","O",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","A+",3.0),
                ("9HC03","Universal Human Values","O",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","O",2.0),
                ("9CC82","Digital Electronics Lab","O",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","O",2.0),
            ]
        },
        {
            "semester_no": 4, "sgpa": 9.0,
            "credits": 23.5,
            "subjects": [
                ("9ZC01","Business Economics and Financial Analysis","A+",3.0),
                ("9CC54","Computer Organization","O",3.0),
                ("9FC04","Database Management Systems","O",3.0),
                ("9HC05","Environmental Science","A+",0.0),
                ("9HC15","Probability and Statistics","O",3.0),
                ("9FC02","Python Programming","O",3.0),
                ("9FC63","Database Management Systems Lab","O",1.5),
                ("9FC64","IT Workshop and Computer Organization Lab","O",2.0),
                ("9FC62","Python Programming Lab","O",2.0),
                ("9HC63","Soft Skills Lab","O",2.0),
                ("9F484","Technical Seminar","O",1.0),
            ]
        },
        {
            "semester_no": 5, "sgpa": 9.0,
            "credits": 23.0,
            "subjects": [
                ("9EC05","Computer Networks","A+",3.0),
                ("9FC05","Data Warehousing and Data Mining","O",3.0),
                ("9EC04","Design and Analysis of Algorithms","A+",3.0),
                ("9ZC10","Entrepreneurship and Business Design","A+",3.0),
                ("9EC10","Introduction to Data Science","O",3.0),
                ("9EC03","Software Engineering","O",2.0),
                ("9EC64","Computer Networks and DAA Lab","O",2.0),
                ("9FC65","Data Warehousing and Data Mining Lab","O",1.5),
                ("9EC63","Software Engineering Lab","O",1.5),
                ("9F585","Summer Industry Internship-I","O",1.0),
                ("9IC04","Intellectual Property Rights","S*",0.0),
            ]
        },
    ]
)

# ══════════════════════════════════════════════════════
# STUDENT 2 — PRIYA LAKSHMI REDDY
# LOW risk | Good consistent student | 4 semesters
# Story: Good grades, placement eligible, improving
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Priya Lakshmi Reddy",
    email="priya.reddy.demo@snist.edu",
    roll_number="22311A12R2",
    branch="INFORMATION TECHNOLOGY",
    current_semester=5,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 8.2,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","A+",3.0),
                ("9HC01","Essential English Language Skills","A",2.0),
                ("9HC11","Matrix Algebra and Calculus","A+",3.0),
                ("9FC01","Problem Solving Using C","A",3.0),
                ("9HC64","Engineering Chemistry Lab","O",1.5),
                ("9HC61","Oral Communication Lab-I","A+",1.0),
                ("9FC61","Problem Solving Using C Lab","O",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","A+",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 8.4,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","A+",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","A",3.0),
                ("9EC01","Data Structures","A+",3.0),
                ("9BC01","Engineering Graphics","A",3.0),
                ("9HC07","Engineering Physics","A",3.0),
                ("9EC61","Data Structures Using C Lab","O",1.5),
                ("9HC66","Engineering Physics Lab","O",1.5),
                ("9HC62","Oral Communication Lab-II","O",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 8.6,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","A+",3.0),
                ("9F303","Discrete Mathematics","A",3.0),
                ("9EC02","Object Oriented Programming Through Java","A+",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","A",3.0),
                ("9HC03","Universal Human Values","O",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","O",2.0),
                ("9CC82","Digital Electronics Lab","O",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","O",2.0),
            ]
        },
        {
            "semester_no": 4, "sgpa": 8.8,
            "credits": 23.5,
            "subjects": [
                ("9ZC01","Business Economics and Financial Analysis","A",3.0),
                ("9CC54","Computer Organization","A+",3.0),
                ("9FC04","Database Management Systems","A+",3.0),
                ("9HC05","Environmental Science","O",0.0),
                ("9HC15","Probability and Statistics","A+",3.0),
                ("9FC02","Python Programming","A+",3.0),
                ("9FC63","Database Management Systems Lab","O",1.5),
                ("9FC64","IT Workshop and Computer Organization Lab","O",2.0),
                ("9FC62","Python Programming Lab","O",2.0),
                ("9HC63","Soft Skills Lab","O",2.0),
                ("9F484","Technical Seminar","O",1.0),
            ]
        },
    ]
)

# ══════════════════════════════════════════════════════
# STUDENT 3 — ARJUN VENKATA NAIDU
# WATCH risk | Declining trend | 4 semesters
# Story: Started well, GPA dropping each semester,
#        no backlogs but CGPA approaching 7.5 cutoff
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Arjun Venkata Naidu",
    email="arjun.naidu.demo@snist.edu",
    roll_number="22311A12R3",
    branch="INFORMATION TECHNOLOGY",
    current_semester=5,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 8.3,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","A+",3.0),
                ("9HC01","Essential English Language Skills","A",2.0),
                ("9HC11","Matrix Algebra and Calculus","A+",3.0),
                ("9FC01","Problem Solving Using C","A",3.0),
                ("9HC64","Engineering Chemistry Lab","O",1.5),
                ("9HC61","Oral Communication Lab-I","A+",1.0),
                ("9FC61","Problem Solving Using C Lab","A+",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","A",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 7.8,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","A",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","B+",3.0),
                ("9EC01","Data Structures","A+",3.0),
                ("9BC01","Engineering Graphics","B+",3.0),
                ("9HC07","Engineering Physics","B",3.0),
                ("9EC61","Data Structures Using C Lab","O",1.5),
                ("9HC66","Engineering Physics Lab","A",1.5),
                ("9HC62","Oral Communication Lab-II","A+",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 7.2,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","B",3.0),
                ("9F303","Discrete Mathematics","C",3.0),
                ("9EC02","Object Oriented Programming Through Java","A",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","B",3.0),
                ("9HC03","Universal Human Values","B+",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","A+",2.0),
                ("9CC82","Digital Electronics Lab","O",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","A+",2.0),
            ]
        },
        {
            "semester_no": 4, "sgpa": 6.8,
            "credits": 23.5,
            "subjects": [
                ("9ZC01","Business Economics and Financial Analysis","B",3.0),
                ("9CC54","Computer Organization","C",3.0),
                ("9FC04","Database Management Systems","B+",3.0),
                ("9HC05","Environmental Science","B",0.0),
                ("9HC15","Probability and Statistics","C",3.0),
                ("9FC02","Python Programming","B",3.0),
                ("9FC63","Database Management Systems Lab","A+",1.5),
                ("9FC64","IT Workshop and Computer Organization Lab","O",2.0),
                ("9FC62","Python Programming Lab","A",2.0),
                ("9HC63","Soft Skills Lab","A+",2.0),
                ("9F484","Technical Seminar","O",1.0),
            ]
        },
    ]
)

# ══════════════════════════════════════════════════════
# STUDENT 4 — SNEHA ANJALI PATEL
# WATCH risk | Placement borderline | CGPA 7.3
# Story: Just below 7.5 placement cutoff, stable but
#        needs to push hard to become eligible
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Sneha Anjali Patel",
    email="sneha.patel.demo@snist.edu",
    roll_number="22311A12R4",
    branch="INFORMATION TECHNOLOGY",
    current_semester=5,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 7.6,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","B+",3.0),
                ("9HC01","Essential English Language Skills","A",2.0),
                ("9HC11","Matrix Algebra and Calculus","B+",3.0),
                ("9FC01","Problem Solving Using C","B",3.0),
                ("9HC64","Engineering Chemistry Lab","A+",1.5),
                ("9HC61","Oral Communication Lab-I","O",1.0),
                ("9FC61","Problem Solving Using C Lab","A+",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","A",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 7.4,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","B+",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","B",3.0),
                ("9EC01","Data Structures","B+",3.0),
                ("9BC01","Engineering Graphics","B+",3.0),
                ("9HC07","Engineering Physics","B",3.0),
                ("9EC61","Data Structures Using C Lab","A+",1.5),
                ("9HC66","Engineering Physics Lab","O",1.5),
                ("9HC62","Oral Communication Lab-II","A",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 7.3,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","B+",3.0),
                ("9F303","Discrete Mathematics","B",3.0),
                ("9EC02","Object Oriented Programming Through Java","B+",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","B+",3.0),
                ("9HC03","Universal Human Values","A",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","O",2.0),
                ("9CC82","Digital Electronics Lab","A+",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","O",2.0),
            ]
        },
        {
            "semester_no": 4, "sgpa": 7.2,
            "credits": 23.5,
            "subjects": [
                ("9ZC01","Business Economics and Financial Analysis","B+",3.0),
                ("9CC54","Computer Organization","B",3.0),
                ("9FC04","Database Management Systems","B+",3.0),
                ("9HC05","Environmental Science","B+",0.0),
                ("9HC15","Probability and Statistics","B",3.0),
                ("9FC02","Python Programming","B+",3.0),
                ("9FC63","Database Management Systems Lab","A",1.5),
                ("9FC64","IT Workshop and Computer Organization Lab","O",2.0),
                ("9FC62","Python Programming Lab","A+",2.0),
                ("9HC63","Soft Skills Lab","O",2.0),
                ("9F484","Technical Seminar","A+",1.0),
            ]
        },
    ]
)

# ══════════════════════════════════════════════════════
# STUDENT 5 — MOHAMMED FARHAN HUSSAIN
# MODERATE risk | 2 backlogs | CGPA 6.5
# Story: Failed Data Structures and Engineering Physics,
#        placement ineligible, needs immediate action
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Mohammed Farhan Hussain",
    email="farhan.hussain.demo@snist.edu",
    roll_number="22311A12R5",
    branch="INFORMATION TECHNOLOGY",
    current_semester=4,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 7.2,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","B",3.0),
                ("9HC01","Essential English Language Skills","B+",2.0),
                ("9HC11","Matrix Algebra and Calculus","B+",3.0),
                ("9FC01","Problem Solving Using C","B",3.0),
                ("9HC64","Engineering Chemistry Lab","A",1.5),
                ("9HC61","Oral Communication Lab-I","A+",1.0),
                ("9FC61","Problem Solving Using C Lab","A",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","A+",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 5.8,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","B",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","C",3.0),
                ("9EC01","Data Structures","F",3.0),
                ("9BC01","Engineering Graphics","B",3.0),
                ("9HC07","Engineering Physics","F",3.0),
                ("9EC61","Data Structures Using C Lab","B",1.5),
                ("9HC66","Engineering Physics Lab","C",1.5),
                ("9HC62","Oral Communication Lab-II","B+",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 6.4,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","B",3.0),
                ("9F303","Discrete Mathematics","B+",3.0),
                ("9EC02","Object Oriented Programming Through Java","B",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","B",3.0),
                ("9HC03","Universal Human Values","B+",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","A",2.0),
                ("9CC82","Digital Electronics Lab","A+",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","O",2.0),
            ]
        },
    ]
)

# ══════════════════════════════════════════════════════
# STUDENT 6 — LAKSHMI SRAVANI DEVI
# MODERATE risk | Struggling | 1 backlog | CGPA 5.8
# Story: Sharp decline in Year 2, failed Computer
#        Organization, attendance issues (risk 25%)
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Lakshmi Sravani Devi",
    email="lakshmi.devi.demo@snist.edu",
    roll_number="22311A12R6",
    branch="INFORMATION TECHNOLOGY",
    current_semester=4,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 7.0,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","B",3.0),
                ("9HC01","Essential English Language Skills","B+",2.0),
                ("9HC11","Matrix Algebra and Calculus","B",3.0),
                ("9FC01","Problem Solving Using C","B+",3.0),
                ("9HC64","Engineering Chemistry Lab","A",1.5),
                ("9HC61","Oral Communication Lab-I","A",1.0),
                ("9FC61","Problem Solving Using C Lab","A+",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","A",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 6.2,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","C",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","B",3.0),
                ("9EC01","Data Structures","B",3.0),
                ("9BC01","Engineering Graphics","C",3.0),
                ("9HC07","Engineering Physics","B",3.0),
                ("9EC61","Data Structures Using C Lab","A",1.5),
                ("9HC66","Engineering Physics Lab","B+",1.5),
                ("9HC62","Oral Communication Lab-II","A",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 4.8,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","C",3.0),
                ("9F303","Discrete Mathematics","D",3.0),
                ("9EC02","Object Oriented Programming Through Java","C",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","D",3.0),
                ("9HC03","Universal Human Values","B",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","B",2.0),
                ("9CC82","Digital Electronics Lab","A",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","B+",2.0),
            ]
        },
        {
            "semester_no": 4, "sgpa": 4.9,
            "credits": 23.5,
            "subjects": [
                ("9ZC01","Business Economics and Financial Analysis","C",3.0),
                ("9CC54","Computer Organization","F",3.0),
                ("9FC04","Database Management Systems","D",3.0),
                ("9HC05","Environmental Science","B",0.0),
                ("9HC15","Probability and Statistics","D",3.0),
                ("9FC02","Python Programming","C",3.0),
                ("9FC63","Database Management Systems Lab","B+",1.5),
                ("9FC64","IT Workshop and Computer Organization Lab","A",2.0),
                ("9FC62","Python Programming Lab","A",2.0),
                ("9HC63","Soft Skills Lab","B+",2.0),
                ("9F484","Technical Seminar","B",1.0),
            ]
        },
    ]
)

# ══════════════════════════════════════════════════════
# STUDENT 7 — VENKAT SURESH BOYAPATI
# HIGH risk | 4 backlogs | CGPA 4.9
# Story: Multiple failures across 3 semesters,
#        completely placement ineligible,
#        risk score 80+
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Venkat Suresh Boyapati",
    email="venkat.suresh.demo@snist.edu",
    roll_number="22311A12R7",
    branch="INFORMATION TECHNOLOGY",
    current_semester=4,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 6.2,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","B",3.0),
                ("9HC01","Essential English Language Skills","C",2.0),
                ("9HC11","Matrix Algebra and Calculus","F",3.0),
                ("9FC01","Problem Solving Using C","D",3.0),
                ("9HC64","Engineering Chemistry Lab","B+",1.5),
                ("9HC61","Oral Communication Lab-I","B",1.0),
                ("9FC61","Problem Solving Using C Lab","B+",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","B",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 4.5,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","F",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","D",3.0),
                ("9EC01","Data Structures","D",3.0),
                ("9BC01","Engineering Graphics","F",3.0),
                ("9HC07","Engineering Physics","C",3.0),
                ("9EC61","Data Structures Using C Lab","B",1.5),
                ("9HC66","Engineering Physics Lab","C",1.5),
                ("9HC62","Oral Communication Lab-II","B",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 5.1,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","C",3.0),
                ("9F303","Discrete Mathematics","F",3.0),
                ("9EC02","Object Oriented Programming Through Java","D",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","C",3.0),
                ("9HC03","Universal Human Values","B",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","B+",2.0),
                ("9CC82","Digital Electronics Lab","A",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","B",2.0),
            ]
        },
    ]
)

# ══════════════════════════════════════════════════════
# STUDENT 8 — DIVYA SREE KRISHNAMURTHY
# HIGH risk | 6 backlogs | CGPA 4.2
# Story: Critical case — Year 2 near-total failure,
#        6 subjects failed across 2 semesters,
#        requires immediate intervention by faculty
# ══════════════════════════════════════════════════════
seed_student(
    full_name="Divya Sree Krishnamurthy",
    email="divya.krishna.demo@snist.edu",
    roll_number="22311A12R8",
    branch="INFORMATION TECHNOLOGY",
    current_semester=3,
    semesters_data=[
        {
            "semester_no": 1, "sgpa": 6.8,
            "credits": 17.5,
            "subjects": [
                ("9HC04","Engineering Chemistry","B",3.0),
                ("9HC01","Essential English Language Skills","B+",2.0),
                ("9HC11","Matrix Algebra and Calculus","B+",3.0),
                ("9FC01","Problem Solving Using C","B",3.0),
                ("9HC64","Engineering Chemistry Lab","A",1.5),
                ("9HC61","Oral Communication Lab-I","A+",1.0),
                ("9FC61","Problem Solving Using C Lab","A",1.5),
                ("9BC61","Workshop Manufacturing Processes Lab","B+",2.5),
                ("9HC18","Induction Program","S*",0.0),
            ]
        },
        {
            "semester_no": 2, "sgpa": 3.8,
            "credits": 19.5,
            "subjects": [
                ("9HC12","Advanced Calculus","F",3.0),
                ("9AC48","Basic Electrical and Electronics Engineering","F",3.0),
                ("9EC01","Data Structures","D",3.0),
                ("9BC01","Engineering Graphics","F",3.0),
                ("9HC07","Engineering Physics","F",3.0),
                ("9EC61","Data Structures Using C Lab","C",1.5),
                ("9HC66","Engineering Physics Lab","D",1.5),
                ("9HC62","Oral Communication Lab-II","B",1.5),
            ]
        },
        {
            "semester_no": 3, "sgpa": 4.0,
            "credits": 20.5,
            "subjects": [
                ("9CC51","Digital Electronics","F",3.0),
                ("9F303","Discrete Mathematics","D",3.0),
                ("9EC02","Object Oriented Programming Through Java","F",3.0),
                ("9HC16","Quantitative Aptitude and Logical Reasoning","D",3.0),
                ("9HC03","Universal Human Values","C",3.0),
                ("9AC95","Basic Electrical and Electronics Engineering Lab","B",2.0),
                ("9CC82","Digital Electronics Lab","B+",1.5),
                ("9EC62","Object Oriented Programming Through Java Lab","C",2.0),
            ]
        },
    ]
)

print("\n" + "="*60)
print("DEMO DATA SEED COMPLETE")
print("="*60)
print("""
All demo students use password: Demo@1234

RISK DISTRIBUTION FOR DEMO:
  [LOW]      Ravi Kumar Sharma      (Topper, CGPA ~9.1)
  [LOW]      Priya Lakshmi Reddy   (Good student, CGPA ~8.6)
  [WATCH]    Arjun Venkata Naidu   (Declining trend)
  [WATCH]    Sneha Anjali Patel    (Below 7.5 cutoff)
  [MODERATE] Mohammed Farhan Hussain (2 backlogs)
  [MODERATE] Lakshmi Sravani Devi  (Struggling, 1 backlog)
  [HIGH]     Venkat Suresh Boyapati (4 backlogs)
  [HIGH]     Divya Sree Krishnamurthy (6 backlogs, critical)

HOW TO PRESENT TO GUIDE:
  1. Teacher dashboard -> Risk Monitor
     Show all 8 students sorted by risk score
  2. Click Divya (HIGH) -> show all 5 tabs
     -- 6 red F grades visible in Grades tab
     -- Risk tab: score 75+, all factors explained
     -- Interventions: log a counseling session live
  3. Click Sneha (WATCH) -> show she is borderline
     -- CGPA 7.3, just below 7.5 placement cutoff
     -- Advisory explains placement risk clearly
  4. Analytics page -> show class distribution
  5. Student view as Ravi -> show low risk, AI chat
""")

db.close()
