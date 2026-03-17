"""
fix_cgpa.py
===========
One-time script. Recalculates CGPA for every student using the
correct JNTUH credits-weighted formula and recomputes their risk
scores so the stored values match the fixed calculation.

Run once from the backend folder:
  python scripts/fix_cgpa.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import Student
from app.services.risk_engine import compute_cgpa, compute_risk_score

db = SessionLocal()
try:
    students = db.query(Student).all()
    print(f"Found {len(students)} student(s). Fixing CGPA...")
    print("-" * 60)

    for student in students:
        old_cgpa = student.cgpa

        # Fix CGPA with correct credits-weighted formula
        correct_cgpa = compute_cgpa(student.id, db)
        if correct_cgpa is not None:
            student.cgpa = correct_cgpa
            db.commit()

            # Recompute risk score with corrected CGPA
            try:
                result = compute_risk_score(student.id, db)
                print(
                    f"[OK] Student {student.id}: "
                    f"CGPA {old_cgpa} -> {correct_cgpa} | "
                    f"Risk: {result['risk_level']} "
                    f"(score={result['sars_score']})"
                )
            except Exception as e:
                print(
                    f"[WARN] Student {student.id}: "
                    f"CGPA fixed ({old_cgpa} -> {correct_cgpa}) "
                    f"but risk recompute failed: {e}"
                )
        else:
            print(
                f"[SKIP] Student {student.id}: "
                "No semester data with credit info -- skipped."
            )

    print("-" * 60)
    print("CGPA fix complete.")
except Exception as e:
    db.rollback()
    print(f"[ERROR] {e}")
finally:
    db.close()
