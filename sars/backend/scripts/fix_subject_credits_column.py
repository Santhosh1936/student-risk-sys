"""
fix_subject_credits_column.py  — run once from sars/backend/
Migrates subject_grades.credits from INTEGER to REAL so that
half-credit subjects (1.5 cr labs) are stored correctly.
"""
import sqlite3, os, sys

db_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sars.db"
)
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur  = conn.cursor()

try:
    cur.execute("PRAGMA table_info(subject_grades)")
    cols = {row[1]: row[2] for row in cur.fetchall()}
    print("Current subject_grades column types:", cols)

    cr_type = cols.get("credits", "").upper()
    if cr_type in ("REAL", "FLOAT", "DOUBLE", "NUMERIC"):
        print("[OK] credits already REAL — no migration needed.")
        conn.close()
        sys.exit(0)

    print("Migrating subject_grades.credits to REAL...")
    cur.execute("ALTER TABLE subject_grades RENAME TO subject_grades_old")
    cur.execute("""
        CREATE TABLE subject_grades (
            id                  INTEGER PRIMARY KEY,
            semester_record_id  INTEGER NOT NULL,
            subject_name        TEXT    NOT NULL,
            subject_code        TEXT,
            marks_obtained      REAL,
            max_marks           REAL DEFAULT 100,
            grade_letter        TEXT,
            grade_points        REAL,
            credits             REAL,
            is_backlog          BOOLEAN DEFAULT 0,
            FOREIGN KEY(semester_record_id)
              REFERENCES semester_records(id)
        )
    """)
    cur.execute("""
        INSERT INTO subject_grades
        SELECT id, semester_record_id, subject_name, subject_code,
               marks_obtained, max_marks, grade_letter, grade_points,
               CAST(credits AS REAL),
               is_backlog
        FROM subject_grades_old
    """)
    cur.execute("DROP TABLE subject_grades_old")
    conn.commit()
    print("[OK] Migration complete — subject_grades.credits is now REAL.")
except Exception as e:
    conn.rollback()
    print(f"[ERR] Migration failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
finally:
    conn.close()
