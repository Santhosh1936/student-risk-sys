"""
reset_chat_threads.py
=====================
One-time script. Resets all existing chat threads so that
the next message from each student triggers a fresh context
injection using the fixed _build_student_context() output.

Run once from the backend folder:
  python scripts/reset_chat_threads.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import ChatThread

db = SessionLocal()
try:
    threads = db.query(ChatThread).all()
    count = 0
    for thread in threads:
        thread.context_set  = False
        thread.data_updated = True
        count += 1
    db.commit()
    print(f"✅ Reset {count} chat thread(s).")
    print("   Each student's next message will re-inject full context.")
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()
