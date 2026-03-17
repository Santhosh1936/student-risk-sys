"""
add_indexes.py
==============
Creates missing indexes on FK columns.
Safe to run multiple times (IF NOT EXISTS).
Run from sars/backend/:
  python scripts/add_indexes.py
"""
import sqlite3, os

db_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "sars.db"
)

conn = sqlite3.connect(db_path)
indexes = [
    ("ix_semester_records_student_id",   "semester_records",  "student_id"),
    ("ix_subject_grades_sr_id",          "subject_grades",    "semester_record_id"),
    ("ix_attendance_records_student_id", "attendance_records","student_id"),
    ("ix_risk_scores_student_id",        "risk_scores",       "student_id"),
    ("ix_interventions_student_id",      "interventions",     "student_id"),
    ("ix_interventions_teacher_id",      "interventions",     "teacher_id"),
    ("ix_chat_threads_student_id",       "chat_threads",      "student_id"),
    ("ix_chat_messages_thread_id",       "chat_messages",     "thread_id"),
]
created = 0
for name, table, col in indexes:
    try:
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS {name} ON {table}({col})"
        )
        print(f"[OK] {name}")
        created += 1
    except Exception as e:
        print(f"[WARN] {name}: {e}")
conn.commit()
conn.close()
print(f"\nDone. {created}/{len(indexes)} indexes created.")
