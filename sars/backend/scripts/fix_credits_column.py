"""
fix_credits_column.py  — run once from sars/backend/
Migrates credits_attempted and credits_earned
from INTEGER to REAL in SQLite.
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
    cur.execute("PRAGMA table_info(semester_records)")
    cols = {row[1]: row[2] for row in cur.fetchall()}
    print("Current column types:", cols)

    ca_type = cols.get("credits_attempted", "").upper()
    if ca_type in ("REAL", "FLOAT", "DOUBLE", "NUMERIC"):
        print("[OK] Already REAL - no migration needed.")
        conn.close()
        sys.exit(0)

    print("Migrating credits columns to REAL...")
    cur.execute(
        "ALTER TABLE semester_records "
        "RENAME TO semester_records_old"
    )
    cur.execute("""
        CREATE TABLE semester_records (
            id                INTEGER PRIMARY KEY,
            student_id        INTEGER NOT NULL,
            semester_no       INTEGER,
            gpa               REAL,
            credits_attempted REAL,
            credits_earned    REAL,
            uploaded_at       DATETIME,
            is_confirmed      BOOLEAN DEFAULT 1,
            FOREIGN KEY(student_id)
              REFERENCES students(id)
        )
    """)
    cur.execute("""
        INSERT INTO semester_records
        SELECT id, student_id, semester_no, gpa,
               CAST(credits_attempted AS REAL),
               CAST(credits_earned AS REAL),
               uploaded_at,
               COALESCE(is_confirmed, 1)
        FROM semester_records_old
    """)
    cur.execute("DROP TABLE semester_records_old")
    conn.commit()
    print("[OK] Migration complete.")
    print("credits_attempted and credits_earned are now REAL.")
except Exception as e:
    conn.rollback()
    print(f"[ERR] Migration failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
finally:
    conn.close()
