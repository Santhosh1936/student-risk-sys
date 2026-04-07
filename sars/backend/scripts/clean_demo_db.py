"""
clean_demo_db.py
================
Cleans junk/test accounts and seeds missing demo attendance and interventions.

Run from sars/backend:
  python scripts/clean_demo_db.py
"""

import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import (
    AdvisorySession,
    AttendanceRecord,
    ChatMessage,
    ChatThread,
    Intervention,
    RiskScore,
    SemesterRecord,
    Student,
    SubjectGrade,
    Teacher,
    User,
)
from app.services.risk_engine import compute_risk_score


KEEP_NAMES = {
    "Kethavath Santhosh",
    "Sai Bhargavi",
    "Mittapellywar Sai Bhargavi",
}

JUNK_EMAIL_HINTS = ["test", "sample", "demo2", "dummy", "fake", "junk"]
JUNK_NAME_HINTS = ["test", "sample", "dummy", "fake", "junk", "temp"]

LOW_NAMES = {"Ravi Kumar Sharma", "Priya Lakshmi Reddy", "Priya Reddy"}
WATCH_NAMES = {"Arjun Naidu", "Sneha Patel"}
MODERATE_NAMES = {"Mohammed Farhan", "Farhan Hussain", "Lakshmi Devi"}
HIGH_NAMES = {"Venkat Suresh", "Divya Krishnamurthy", "Divya"}

rng = random.Random(42)


def is_demo_student_email(email: str) -> bool:
    return email.lower().endswith(".demo@snist.edu")


def should_keep_user(user: User, db) -> bool:
    if user.role == "teacher":
        return True
    if user.full_name in KEEP_NAMES:
        return True
    if is_demo_student_email(user.email):
        return True
    return False


def looks_like_junk(user: User) -> bool:
    email_l = (user.email or "").lower()
    name_l = (user.full_name or "").lower()

    if any(h in email_l for h in JUNK_EMAIL_HINTS):
        return True
    if any(h in name_l for h in JUNK_NAME_HINTS):
        return True
    if email_l.startswith("test") or email_l.startswith("sample"):
        return True
    return False


def delete_user_tree(user: User, db) -> None:
    student = db.query(Student).filter(Student.user_id == user.id).first()

    if student:
        thread = db.query(ChatThread).filter(ChatThread.student_id == student.id).first()
        if thread:
            db.query(ChatMessage).filter(ChatMessage.thread_id == thread.id).delete()
            db.delete(thread)

        db.query(Intervention).filter(Intervention.student_id == student.id).delete()
        db.query(AdvisorySession).filter(AdvisorySession.student_id == student.id).delete()
        db.query(RiskScore).filter(RiskScore.student_id == student.id).delete()
        db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id).delete()

        semester_ids = [
            r.id
            for r in db.query(SemesterRecord).filter(SemesterRecord.student_id == student.id).all()
        ]
        if semester_ids:
            db.query(SubjectGrade).filter(SubjectGrade.semester_record_id.in_(semester_ids)).delete(
                synchronize_session=False
            )
        db.query(SemesterRecord).filter(SemesterRecord.student_id == student.id).delete()

        db.delete(student)

    teacher = db.query(Teacher).filter(Teacher.user_id == user.id).first()
    if teacher:
        db.query(Intervention).filter(Intervention.teacher_id == teacher.id).delete()
        db.delete(teacher)

    db.delete(user)


def latest_risk_level(student_id: int, db) -> str:
    latest = (
        db.query(RiskScore)
        .filter(RiskScore.student_id == student_id)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )
    return latest.risk_level if latest else "WATCH"


def pick_percentage_bucket(risk_level: str, subject_index: int, total_subjects: int) -> float:
    if risk_level == "LOW":
        return float(rng.randint(85, 95))

    if risk_level == "WATCH":
        low_count = min(2, max(1, total_subjects // 4))
        if subject_index < low_count:
            return float(rng.randint(70, 74))
        return float(rng.randint(76, 80))

    if risk_level == "MODERATE":
        low_count = min(2, max(1, total_subjects // 3))
        if subject_index < low_count:
            return float(rng.randint(55, 65))
        return float(rng.randint(65, 72))

    # HIGH
    severe_count = min(2, max(1, total_subjects // 3))
    if subject_index < severe_count:
        return float(rng.randint(30, 45))
    return float(rng.randint(45, 60))


def seed_attendance_for_student(student: Student, db) -> int:
    semesters = (
        db.query(SemesterRecord)
        .filter(SemesterRecord.student_id == student.id)
        .order_by(SemesterRecord.semester_no.asc())
        .all()
    )
    if not semesters:
        return 0

    existing = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id).count()
    if existing > 0:
        return 0

    risk_level = latest_risk_level(student.id, db)
    created = 0

    for sem in semesters:
        subjects = (
            db.query(SubjectGrade)
            .filter(SubjectGrade.semester_record_id == sem.id)
            .order_by(SubjectGrade.subject_name.asc())
            .all()
        )
        if not subjects:
            continue

        for idx, subj in enumerate(subjects):
            pct = pick_percentage_bucket(risk_level, idx, len(subjects))
            total_classes = 60
            classes_attended = int(round(total_classes * (pct / 100.0)))
            actual_pct = round((classes_attended / total_classes) * 100.0, 2)

            db.add(
                AttendanceRecord(
                    student_id=student.id,
                    semester_no=sem.semester_no,
                    subject_name=subj.subject_name,
                    total_classes=total_classes,
                    classes_attended=classes_attended,
                    percentage=actual_pct,
                )
            )
            created += 1

    return created


def seed_interventions_for_demo_students(db) -> int:
    teacher = db.query(Teacher).order_by(Teacher.id.asc()).first()
    if not teacher:
        print("[WARN] No teacher account found. Skipping intervention seeding.")
        return 0

    demo_students = (
        db.query(Student)
        .join(User, User.id == Student.user_id)
        .filter(User.email.like("%.demo@snist.edu"))
        .all()
    )

    demo_ids = [s.id for s in demo_students]
    if demo_ids:
        db.query(Intervention).filter(Intervention.student_id.in_(demo_ids)).delete(
            synchronize_session=False
        )

    now = datetime.now(timezone.utc)
    created = 0

    for student in demo_students:
        user = db.query(User).filter(User.id == student.user_id).first()
        name = user.full_name if user else "Unknown"
        risk_level = latest_risk_level(student.id, db)

        if name in HIGH_NAMES or risk_level == "HIGH":
            db.add(
                Intervention(
                    student_id=student.id,
                    teacher_id=teacher.id,
                    intervention_type="Counseling",
                    notes=(
                        "Student called for academic counseling session. Discussed backlog "
                        "clearing strategy and study plan for upcoming supplementary exams."
                    ),
                    created_at=now - timedelta(days=30),
                    resolved_at=now - timedelta(days=25),
                    outcome=(
                        "Student acknowledged the issue. Agreed to attend supplementary exams "
                        "and submit study plan by next week."
                    ),
                )
            )
            created += 1
            print(f"[INTERVENTION] {name} - Counseling (resolved)")

            db.add(
                Intervention(
                    student_id=student.id,
                    teacher_id=teacher.id,
                    intervention_type="Parent Meeting",
                    notes=(
                        "Parent meeting scheduled due to critical academic risk level. "
                        "Student has multiple backlogs affecting placement eligibility. "
                        "Attendance is severely below 75%."
                    ),
                    created_at=now - timedelta(days=7),
                    resolved_at=None,
                    outcome=None,
                )
            )
            created += 1
            print(f"[INTERVENTION] {name} - Parent Meeting (open)")
            continue

        if name in MODERATE_NAMES or risk_level == "MODERATE":
            db.add(
                Intervention(
                    student_id=student.id,
                    teacher_id=teacher.id,
                    intervention_type="Tutoring",
                    notes=(
                        "Enrolled student in peer tutoring program for Data Structures and "
                        "Engineering Physics. Two sessions per week arranged."
                    ),
                    created_at=now - timedelta(days=45),
                    resolved_at=now - timedelta(days=30),
                    outcome=(
                        "Student completed 6 tutoring sessions. Supplementary exam attempted. "
                        "Awaiting results."
                    ),
                )
            )
            created += 1
            print(f"[INTERVENTION] {name} - Tutoring (resolved)")
            continue

        if name in WATCH_NAMES or risk_level == "WATCH":
            db.add(
                Intervention(
                    student_id=student.id,
                    teacher_id=teacher.id,
                    intervention_type="Counseling",
                    notes=(
                        "Proactive counseling scheduled for student showing declining GPA trend. "
                        "CGPA is approaching the 7.5 placement cutoff. "
                        "Early intervention to prevent further drop."
                    ),
                    created_at=now - timedelta(days=14),
                    resolved_at=None,
                    outcome=None,
                )
            )
            created += 1
            print(f"[INTERVENTION] {name} - Counseling (open)")

    return created


def print_final_summary(db) -> None:
    table_counts = {
        "users": db.query(User).count(),
        "students": db.query(Student).count(),
        "teachers": db.query(Teacher).count(),
        "semester_records": db.query(SemesterRecord).count(),
        "subject_grades": db.query(SubjectGrade).count(),
        "attendance_records": db.query(AttendanceRecord).count(),
        "risk_scores": db.query(RiskScore).count(),
        "interventions": db.query(Intervention).count(),
        "chat_threads": db.query(ChatThread).count(),
        "chat_messages": db.query(ChatMessage).count(),
        "advisory_sessions": db.query(AdvisorySession).count(),
    }

    print("\nFinal DB state summary")
    for key, value in table_counts.items():
        print(f"- {key}: {value}")

    print("\nRemaining students")
    students = db.query(Student).order_by(Student.id.asc()).all()
    for student in students:
        user = db.query(User).filter(User.id == student.user_id).first()
        name = user.full_name if user else f"Student {student.id}"

        risk = (
            db.query(RiskScore)
            .filter(RiskScore.student_id == student.id)
            .order_by(RiskScore.computed_at.desc())
            .first()
        )
        semesters = db.query(SemesterRecord).filter(SemesterRecord.student_id == student.id).count()
        attendance_present = (
            db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id).count() > 0
        )

        print(
            f"- {name} | CGPA={student.cgpa if student.cgpa is not None else 'N/A'} "
            f"| risk={risk.risk_level if risk else 'N/A'} "
            f"| semesters={semesters} "
            f"| attendance={'Yes' if attendance_present else 'No'}"
        )


def main() -> None:
    db = SessionLocal()

    try:
        print("STEP B1a - Deleting junk/test accounts")
        users = db.query(User).order_by(User.id.asc()).all()
        deleted_count = 0

        for user in users:
            if should_keep_user(user, db):
                continue
            if looks_like_junk(user):
                print(f"[DELETE] {user.full_name} <{user.email}>")
                delete_user_tree(user, db)
                deleted_count += 1

        db.commit()
        print(f"Deleted accounts: {deleted_count}")

        print("\nSTEP B1b - Seeding attendance for demo students")
        demo_students = (
            db.query(Student)
            .join(User, User.id == Student.user_id)
            .filter(User.email.like("%.demo@snist.edu"))
            .all()
        )

        attendance_created = 0
        for student in demo_students:
            semester_count = db.query(SemesterRecord).filter(SemesterRecord.student_id == student.id).count()
            if semester_count == 0:
                continue
            created = seed_attendance_for_student(student, db)
            if created > 0:
                user = db.query(User).filter(User.id == student.user_id).first()
                name = user.full_name if user else f"Student {student.id}"
                print(f"[ATTENDANCE] Seeded {created} records for {name}")
            attendance_created += created

        db.commit()
        print(f"Attendance records created: {attendance_created}")

        print("Recomputing risk scores for demo students")
        for student in demo_students:
            try:
                compute_risk_score(student.id, db)
            except Exception as exc:
                print(f"[WARN] Risk recompute failed for student_id={student.id}: {exc}")

        print("\nSTEP B1c - Seeding interventions")
        intervention_count = seed_interventions_for_demo_students(db)
        db.commit()
        print(f"Interventions created: {intervention_count}")

        print("\nSTEP B1d - Re-indexing students in RAG")
        try:
            from app.services.rag_service import index_student

            students_with_semesters = (
                db.query(Student)
                .join(SemesterRecord, SemesterRecord.student_id == Student.id)
                .distinct()
                .all()
            )
            for student in students_with_semesters:
                user = db.query(User).filter(User.id == student.user_id).first()
                name = user.full_name if user else f"Student {student.id}"
                try:
                    result = index_student(student.id, db)
                    print(
                        f"[RAG] {name} (student_id={student.id}) "
                        f"indexed {result['chunk_count']} chunks"
                    )
                except Exception as exc:
                    print(f"[WARN] RAG index failed for {name}: {exc}")
        except Exception as exc:
            print(f"[WARN] RAG indexing unavailable, skipping: {exc}")

        print("\nSTEP B1e - Final summary")
        print_final_summary(db)

    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Cleanup failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
