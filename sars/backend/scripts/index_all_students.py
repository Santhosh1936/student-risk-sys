"""
index_all_students.py
=====================
Indexes all students with semester data into the RAG vector store.
Safe to run multiple times (per-student index is rebuilt fresh).

Run from sars/backend:
  python scripts/index_all_students.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import SemesterRecord, Student, User
from app.services.rag_service import index_student


def main() -> None:
    db = SessionLocal()
    try:
        students = db.query(Student).order_by(Student.id.asc()).all()
        print(f"Found {len(students)} student records.")

        indexed = 0
        skipped = 0

        for student in students:
            has_semesters = (
                db.query(SemesterRecord)
                .filter(SemesterRecord.student_id == student.id)
                .count()
            ) > 0

            user = db.query(User).filter(User.id == student.user_id).first()
            name = user.full_name if user else f"Student {student.id}"

            if not has_semesters:
                skipped += 1
                print(f"[SKIP] {name} (student_id={student.id}) - no semester data")
                continue

            try:
                result = index_student(student.id, db)
                indexed += 1
                print(
                    f"[OK] {name} (student_id={student.id}) - "
                    f"chunks={result['chunk_count']} status=indexed"
                )
            except Exception as exc:
                print(
                    f"[WARN] {name} (student_id={student.id}) - "
                    f"index failed: {exc}"
                )

        print("\nIndexing summary")
        print(f"- Indexed: {indexed}")
        print(f"- Skipped (no semesters): {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
