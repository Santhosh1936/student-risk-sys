"""One-time script to index all students into the SARS RAG store."""

import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.orm import joinedload  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.models import Student  # noqa: E402
from app.services import rag_service  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        students = (
            db.query(Student)
            .options(joinedload(Student.user))
            .order_by(Student.id.asc())
            .all()
        )

        print(f"Found {len(students)} student(s) to index.\n")

        success_count = 0
        failure_count = 0

        for student in students:
            try:
                result = rag_service.index_student(student.id, db)
                status = result["status"]
                print(
                    f"{student.user.full_name}: "
                    f"{result['chunks_indexed']} chunk(s) created, "
                    f"indexed={status['indexed']}, "
                    f"chunk_count={status['chunk_count']}"
                )
                success_count += 1
            except Exception as exc:
                print(f"{student.user.full_name}: FAILED - {exc}")
                failure_count += 1

        print("\nIndexing summary")
        print(f"Successful students: {success_count}")
        print(f"Failed students: {failure_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
