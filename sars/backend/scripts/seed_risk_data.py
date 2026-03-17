"""
seed_risk_data.py
=================
Seeds semester records, subject grades, and risk scores for demo purposes.

Assigns:
  students 2,3 -> HIGH risk   (SARS score ~82.5)
  students 4,5 -> MODERATE    (SARS score ~58.3)
  students 6,7 -> WATCH       (SARS score ~32.1)
  students 1,10,11,12 -> untouched (real data kept)

Run from sars/backend/:
  python scripts/seed_risk_data.py
"""
import sys, os, json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import Student, User, SemesterRecord, SubjectGrade, RiskScore

db = SessionLocal()

# ── Subject data per risk tier ─────────────────────────────────────────────────

HIGH_SEMS = [
    {
        "semester_no": 1,
        "gpa": 5.8,
        "credits_attempted": 17.5,
        "credits_earned": 14.0,
        "subjects": [
            ("Engineering Chemistry",   "9HC04", "C",  5,  3.0, False),
            ("English Language Skills", "9HC01", "D",  4,  2.0, False),
            ("Matrix Algebra",          "9FC11", "F",  0,  3.0, True),
            ("Problem Solving C",       "9FC01", "D",  4,  3.0, False),
            ("Chemistry Lab",           "9HC64", "C",  5,  1.5, False),
            ("Oral Comm Lab",           "9FC61", "D",  4,  1.0, False),
            ("C Lab",                   "9FC62", "F",  0,  1.5, True),
            ("Workshop Lab",            "9BC61", "D",  4,  2.5, False),
        ],
    },
    {
        "semester_no": 2,
        "gpa": 4.2,
        "credits_attempted": 19.5,
        "credits_earned": 13.5,
        "subjects": [
            ("Advanced Calculus",       "9HC12", "D",  4,  3.0, False),
            ("Basic Elec Electronics",  "9AC48", "F",  0,  3.0, True),
            ("Data Structures",         "9EC01", "D",  4,  3.0, False),
            ("Engineering Graphics",    "9BC01", "F",  0,  3.0, True),
            ("Engineering Physics",     "9HC07", "D",  4,  3.0, False),
            ("DS Using C Lab",          "9EC61", "C",  5,  1.5, False),
            ("Physics Lab",             "9HC66", "D",  4,  1.5, False),
            ("Oral Comm Lab II",        "9HC62", "D",  4,  1.5, False),
        ],
    },
]

MODERATE_SEMS = [
    {
        "semester_no": 1,
        "gpa": 6.8,
        "credits_attempted": 17.5,
        "credits_earned": 16.0,
        "subjects": [
            ("Engineering Chemistry",   "9HC04", "B",  6,  3.0, False),
            ("English Language Skills", "9HC01", "B",  6,  2.0, False),
            ("Matrix Algebra",          "9FC11", "B+", 7,  3.0, False),
            ("Problem Solving C",       "9FC01", "C",  5,  3.0, False),
            ("Chemistry Lab",           "9HC64", "B",  6,  1.5, False),
            ("Oral Comm Lab",           "9FC61", "B",  6,  1.0, False),
            ("C Lab",                   "9FC62", "B+", 7,  1.5, False),
            ("Workshop Lab",            "9BC61", "B",  6,  2.5, False),
        ],
    },
    {
        "semester_no": 2,
        "gpa": 5.4,
        "credits_attempted": 19.5,
        "credits_earned": 16.0,
        "subjects": [
            ("Advanced Calculus",       "9HC12", "B",  6,  3.0, False),
            ("Basic Elec Electronics",  "9AC48", "C",  5,  3.0, False),
            ("Data Structures",         "9EC01", "F",  0,  3.0, True),
            ("Engineering Graphics",    "9BC01", "B",  6,  3.0, False),
            ("Engineering Physics",     "9HC07", "F",  0,  3.0, True),
            ("DS Using C Lab",          "9EC61", "B",  6,  1.5, False),
            ("Physics Lab",             "9HC66", "C",  5,  1.5, False),
            ("Oral Comm Lab II",        "9HC62", "B",  6,  1.5, False),
        ],
    },
]

WATCH_SEMS = [
    {
        "semester_no": 1,
        "gpa": 7.8,
        "credits_attempted": 17.5,
        "credits_earned": 17.5,
        "subjects": [
            ("Engineering Chemistry",   "9HC04", "B+", 7,  3.0, False),
            ("English Language Skills", "9HC01", "B",  6,  2.0, False),
            ("Matrix Algebra",          "9FC11", "A",  8,  3.0, False),
            ("Problem Solving C",       "9FC01", "B",  6,  3.0, False),
            ("Chemistry Lab",           "9HC64", "B+", 7,  1.5, False),
            ("Oral Comm Lab",           "9FC61", "B+", 7,  1.0, False),
            ("C Lab",                   "9FC62", "A",  8,  1.5, False),
            ("Workshop Lab",            "9BC61", "B+", 7,  2.5, False),
        ],
    },
    {
        "semester_no": 2,
        "gpa": 6.9,
        "credits_attempted": 19.5,
        "credits_earned": 18.0,
        "subjects": [
            ("Advanced Calculus",       "9HC12", "B+", 7,  3.0, False),
            ("Basic Elec Electronics",  "9AC48", "B",  6,  3.0, False),
            ("Data Structures",         "9EC01", "B+", 7,  3.0, False),
            ("Engineering Graphics",    "9BC01", "F",  0,  3.0, True),
            ("Engineering Physics",     "9HC07", "B",  6,  3.0, False),
            ("DS Using C Lab",          "9EC61", "A",  8,  1.5, False),
            ("Physics Lab",             "9HC66", "B+", 7,  1.5, False),
            ("Oral Comm Lab II",        "9HC62", "B+", 7,  1.5, False),
        ],
    },
]

ADVISORIES = {
    "HIGH": (
        "You are at HIGH academic risk. You have multiple backlogs and a "
        "declining CGPA. Please meet your academic advisor immediately and "
        "create a backlog clearing plan."
    ),
    "MODERATE": (
        "You are at moderate academic risk. Your CGPA has declined and "
        "you have active backlogs. Immediate action is recommended."
    ),
    "WATCH": (
        "Your performance needs attention. Your GPA is declining slightly. "
        "Small improvements now will prevent bigger problems later."
    ),
    "LOW": "Your academic performance is on track. Keep it up!",
}

# ── Seed assignments (IDs chosen to avoid overwriting real student data) ───────

ASSIGNMENTS = [
    # (student_id, sems_data, cgpa, sars_score, risk_level, confidence)
    (2, HIGH_SEMS,     4.8,  82.5, "HIGH",     0.75),
    (3, HIGH_SEMS,     4.8,  82.5, "HIGH",     0.75),
    (4, MODERATE_SEMS, 5.9,  58.3, "MODERATE", 0.75),
    (5, MODERATE_SEMS, 5.9,  58.3, "MODERATE", 0.75),
    (6, WATCH_SEMS,    7.2,  32.1, "WATCH",    0.75),
    (7, WATCH_SEMS,    7.2,  32.1, "WATCH",    0.75),
]


def seed_student(student_id, sems_data, cgpa_val,
                 sars_score, risk_level, confidence):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        print(f"  [SKIP] Student {student_id} not found in DB.")
        return

    user = db.query(User).filter(User.id == student.user_id).first()
    name = user.full_name if user else f"id={student_id}"

    # Delete old semester data for this student
    existing = db.query(SemesterRecord).filter(
        SemesterRecord.student_id == student_id
    ).all()
    for rec in existing:
        db.query(SubjectGrade).filter(
            SubjectGrade.semester_record_id == rec.id
        ).delete()
    db.query(SemesterRecord).filter(
        SemesterRecord.student_id == student_id
    ).delete()

    # Insert semester records + subjects
    for sem in sems_data:
        rec = SemesterRecord(
            student_id=student_id,
            semester_no=sem["semester_no"],
            gpa=sem["gpa"],
            credits_attempted=sem["credits_attempted"],
            credits_earned=sem["credits_earned"],
        )
        db.add(rec)
        db.flush()

        for (name_, code, grade, pts, creds, backlog) in sem["subjects"]:
            db.add(SubjectGrade(
                semester_record_id=rec.id,
                subject_name=name_,
                subject_code=code,
                grade_letter=grade,
                grade_points=pts,
                credits=creds,
                is_backlog=backlog,
            ))

    # Update student profile
    student.cgpa = cgpa_val
    student.current_semester = len(sems_data) + 1
    if not student.branch:
        student.branch = "COMPUTER SCIENCE AND ENGINEERING"

    # Counts
    total_backlogs = sum(
        1 for sem in sems_data
        for subj in sem["subjects"]
        if subj[5]
    )

    # Factor breakdown
    gpa_risk      = round(max(0.0, (7.0 - cgpa_val) / 7.0 * 100), 2)
    backlog_risk  = round(min(100.0, total_backlogs * 20.0), 2)
    att_risk      = 25.0
    gpa_comp      = round(gpa_risk     * 0.40, 2)
    bl_comp       = round(backlog_risk  * 0.35, 2)
    att_comp      = round(att_risk      * 0.25, 2)

    breakdown = {
        "gpa_risk":              gpa_risk,
        "backlog_risk":          backlog_risk,
        "attendance_risk":       att_risk,
        "gpa_component":         gpa_comp,
        "backlog_component":     bl_comp,
        "attendance_component":  att_comp,
        "sars_score":            sars_score,
        "risk_level":            risk_level,
        "confidence":            confidence,
        "semesters_analyzed":    len(sems_data),
        "total_backlogs":        total_backlogs,
        "cgpa":                  cgpa_val,
        "avg_attendance":        None,
        "trend_direction":       "declining",
        "trend_bonus":           5.0,
    }

    # Replace risk score
    db.query(RiskScore).filter(
        RiskScore.student_id == student_id
    ).delete()
    db.add(RiskScore(
        student_id=student_id,
        computed_at=datetime.now(timezone.utc),
        sars_score=sars_score,
        risk_level=risk_level,
        confidence=confidence,
        factor_breakdown=json.dumps(breakdown),
        advisory_text=ADVISORIES[risk_level],
    ))

    db.commit()
    print(
        f"  [OK] {name} (id={student_id}) -> "
        f"CGPA:{cgpa_val} | Backlogs:{total_backlogs} | "
        f"SARS:{sars_score} | {risk_level}"
    )


try:
    print("=" * 60)
    print("SARS Risk Data Seeder")
    print("=" * 60)

    print("\nAll students in DB:")
    for s in db.query(Student).order_by(Student.id).all():
        u = db.query(User).filter(User.id == s.user_id).first()
        print(f"  id={s.id} | {u.full_name if u else '?'} | "
              f"CGPA={s.cgpa} | {s.branch}")

    print("\nSeeding HIGH risk -> student IDs 2, 3")
    print("Seeding MODERATE  -> student IDs 4, 5")
    print("Seeding WATCH     -> student IDs 6, 7")
    print("Skipping real students: 1, 10, 11, 12\n")

    for args in ASSIGNMENTS:
        seed_student(*args)

    print("\n[DONE] Seeding complete.")
    print("Restart backend (or it will pick up via --reload).")
    print("Open Risk Monitor in browser to see results.")

except Exception as e:
    db.rollback()
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
