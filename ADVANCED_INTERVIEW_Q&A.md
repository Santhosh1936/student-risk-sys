# SARS Project - Advanced Interview Questions & Tricky Scenarios

**For deeper technical grilling and edge cases you might face**

---

## PART 1: ALGORITHMIC & MATHEMATICAL DEPTH

### Q1: Backlog Non-Linearity Defense

**The Question:**
"Your backlog risk uses a non-linear scale: 1→40, 2→60, 3→80, 4→90, 5+→100. This looks arbitrary. What if I told you a student with 2 backlogs should have risk 70 instead of 60? How would you justify the current formula?"

**Strong Answer:**
"The non-linearity reflects placement reality. Each additional backlog compounds placement rejection:
- 1 backlog: Some companies exclude (risk = 40%)
- 2 backlogs: Most companies exclude (risk = 60%)
- 3+ backlogs: Nearly all exclude (risk → 80%+)

The curve is not arbitrary—it approximates the cumulative rejection rate based on JNTUH placement data. If you have different data suggesting 2 backlogs = 70% risk, let's verify it. The key is the *reasoning is defensible*, not that it's perfect.

If this were production, I'd A/B test: does the 60 or 70 threshold correlate better with actual placement outcomes?"

**Weak Answer:** "It's just what I chose" or "It feels right"

---

### Q2: CGPA Weighting Edge Case

**The Question:**
"Suppose a student took extra credits in Semester 1 (35 credits) and normal credits in Semester 2 (22 credits). Their SGPA went from 7.5 to 8.5. Their CGPA barely moved. Is the formula fair?"

**Analysis & Answer:**
```
Sem 1: 7.5 × 35 = 262.5
Sem 2: 8.5 × 22 = 187
CGPA = (262.5 + 187) / (35 + 22) = 449.5 / 57 ≈ 7.88
```

Without Sem 2 high GPA, CGPA would be 7.5. With it, only 7.88. The denominator dilutes the improvement.

**Strong Answer:**
"This is actually the *correct* behavior for JNTUH policy. CGPA reflects overall performance across all credits, not semester-by-semester. A student who performs brilliantly in a light semester (22 credits) but averaged 7.5 across heavy semesters (35 credits) has strong *overall* performance (7.88), but it's not inflated artificially.

If JNTUH wanted to reward semester-specific excellence, they'd track SGPA separately. The CGPA intentionally stabilizes with heavier loads.

Is this *fair*? Arguably yes—a difficult semester (35 credits) shouldn't be erased by one good semester. The formula balances excellence with sustained performance."

**Follow-up Trap:**
"So shouldn't students who do poorly in heavy semesters be penalized more?"

**Answer:** "Actually, they ARE. A 5.0 SGPA with 35 credits pulls down CGPA more than a 5.0 SGPA with 22 credits. The math is symmetric."

---

### Q3: Risk Score Rounding & Precision

**The Question:**
"Your risk score is floating-point (e.g., 47.3, 52.1). But you classify into 4 buckets: LOW, WATCH, MODERATE, HIGH. Students at 49.99 and 50.01 get different classifications despite being essentially the same risk. How do you handle threshold sensitivity?"

**Strong Answer:**
"Great observation. In production, I'd:
1. **Confidence intervals:** Store ±2% margin around scores
2. **Threshold buffers:** Don't switch at exactly 50; add hysteresis (move up at 51, move down at 49)
3. **Manual review:** For borderline students, teacher makes final call

Currently in B.Tech version, the threshold is hard-coded for simplicity. Real impact: maybe 5% of students sit on the boundary. Ignoring it is acceptable for scope, but I'd flag it as technical debt."

**Weak Answer:** "I never thought about it" or "It's close enough"

---

### Q4: Division by Zero / Null Handling

**The Question:**
"In the CGPA formula, you divide by Σ(Credits_i). What if a student has no semesters? What if all credits are zero?"

**Answer:**
"Good catch. Current code:
```python
if not semester_records or sum(credits) == 0:
    return None  # CGPA undefined
```

Then, in risk scoring, if CGPA is None, we handle it separately (don't penalize unknown data—use neutral defaults for GPA risk).

In production, I'd add:
- Database constraint: credits_attempted > 0 per semester
- API validation: Reject zero-credit semester uploads
- Monitoring: Alert if CGPA computation returns None (data quality issue)"

---

---

## PART 2: SYSTEM DESIGN DEEP-DIVES

### Q5: Scaling to 100K Students

**The Question:**
"SARS works for 1000 students. Now imagine scaling to 100,000 students across 100 institutions. What breaks first?"

**Systematic Answer:**

| Layer | Problem | Solution |
|-------|---------|----------|
| **Database** | SQLite file exhausted; concurrent access contention | PostgreSQL with read replicas + connection pooling (PgBouncer) |
| **Risk Scoring** | Computing 100K risk scores on-demand is slow | Batch job: Compute nightly, cache in Redis; on-demand gets cached version |
| **Gemini API** | Rate limiting; quota exceeded; cost explodes | Implement queue (Celery); batch extract jobs; fallback OCR engine |
| **Storage** | 100K × 8 semesters × 10 subjects = 8M records | Index on (user_id, semester) for fast access |
| **Frontend** | Loading 100K students in risk overview crashes browser | Pagination + server-side filtering; or separate analytics microservice |
| **Advisor Chat** | ChromaDB has 100K student indices; search slows down | Move to Weaviate/Milvus; shard by institution |
| **Secrets** | `.env` file management across servers | Use HashiCorp Vault or AWS Secrets Manager |

**Weak Answer:** "Use a bigger server" or "Optimizations can wait"

---

### Q6: Data Consistency Under Concurrent Updates

**The Question:**
"Two teachers simultaneously edit the same student's attendance. First teacher sets it to 70%, second to 75%. Database gets both requests at the exact same time. What happens?"

**Answer:**
"This is an optimistic locking vs pessimistic locking question.

Current behavior (SQLite default):
```
T1: READ attendance (NULL)
T2: READ attendance (NULL)
T1: WRITE attendance = 70% → commits
T2: WRITE attendance = 75% → commits ← T1's write lost!
```

This is a **lost update**. To fix:

**Option 1: Optimistic Locking** (application-level)
```python
class Attendance(Base):
    version = Column(Integer, default=0)
    average_attendance = Column(Float)

# Before update, check version
def update_attendance(id, new_value, expected_version):
    row = db.query(Attendance).filter_by(id=id)
    if row.version != expected_version:
        raise ConflictError("Version mismatch; retry")
    row.average_attendance = new_value
    row.version += 1
    db.commit()
```

**Option 2: Pessimistic Locking** (database-level)
```python
row = db.query(Attendance).with_for_update().filter_by(id=id)
row.average_attendance = new_value
db.commit()  # Row locked during transaction
```

For B.Tech scope: Option 1. For production: Depends on contention (if rare, Option 1 is fine; if frequent, Option 2)."

**Follow-up:** "What if the second teacher's update is the correct value and should win?"

**Answer:** "Then we use Last-Write-Wins (LWW): timestamp updates, winner is whoever wrote last. Trade-off: first teacher loses their change silently. Document this in UI: 'Last change wins.'"

---

### Q7: Cascading Deletes & Referential Integrity

**The Question:**
"A teacher account is deleted. What happens to interventions they logged? Do you cascade delete? Soft delete? Leave orphaned records?"

**Strong Answer:**
"Good question about data governance. Current architecture:

```python
class Intervention(Base):
    teacher_id = Column(Integer, ForeignKey('users.id'))
```

SQLAlchemy default is no cascade. If teacher deleted, FK constraint violation.

Better approaches:
1. **Soft delete:** Add `deleted_at` timestamp; never actually delete
   ```python
   teacher.deleted_at = now()
   # Interventions remain; query filters WHERE deleted_at IS NULL
   ```
   Pro: Audit trail preserved
   Con: Data accumulates

2. **Cascade delete:** 
   ```python
   teacher_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
   ```
   Pro: Clean
   Con: Lose audit history

3. **Adopt to system user:**
   ```python
   intervention.teacher_id = SYSTEM_ADMIN_ID
   ```
   Pro: Preserves intervention history
   Con: Looks like admin made it

**Recommendation:** Soft delete for compliance (GDPR requires records). For B.Tech: implement soft delete to show I understand data governance."

---

---

## PART 3: SECURITY & EDGE CASES

### Q8: JWT Secret Rotation

**The Question:**
"Tomorrow, we realize someone compromised the JWT SECRET_KEY. We rotate it. What happens to users with tokens issued under the old key?"

**Answer:**
"Currently: They get logged out (token verification fails with new secret).

Better approach (production):
```python
JWT_SECRETS = [
    "new_secret_2026_04_26",  # Current
    "old_secret_2026_04_25",  # Previous (grace period)
]

def verify_token(token):
    for secret in JWT_SECRETS:
        try:
            return jwt.decode(token, secret)
        except InvalidSignature:
            continue
    raise InvalidToken
```

This allows 24-48 hour grace period. Old tokens still work; new tokens use new secret.

Alternative: Issue refresh tokens; compromise only forces login on next refresh cycle."

---

### Q9: SQL Injection in Search

**The Question:**
"Students can search for other students by name. I see this code:
```python
@app.get('/search')
def search(query: str):
    return db.query(User).filter(User.name.like(query)).all()
```
Is this vulnerable to SQL injection?"

**Answer:**
"NO—it's safe because of SQLAlchemy ORM. Under the hood, SQLAlchemy generates:
```sql
SELECT * FROM users WHERE name LIKE ?;
-- Parameterized query; `query` is a parameter, not SQL code
```

Even if query = `%; DROP TABLE users; --`, it's treated as literal string in the LIKE clause, not executed.

However, there's a *different* vulnerability: **LIKE injection**. If query = `%`, it returns all users. Solution:

```python
from sqlalchemy import and_
query = query.replace('%', '\\%').replace('_', '\\_')
return db.query(User).filter(User.name.like(query, escape='\\')).all()
```

Lesson: SQLAlchemy prevents SQL injection, but you still need to sanitize for the specific operation (LIKE, IN, etc.)."

---

### Q10: Attendance Validation

**The Question:**
"A teacher uploads attendance as: 150%. Does the system catch this?"

**Answer:**
"Current code:
```python
@app.post('/student/attendance')
def upload_attendance(semester_no: int, percentage: float):
    record = Attendance(semester_no=semester_no, average_attendance_percentage=percentage)
    db.add(record)
    db.commit()
```

**Vulnerability:** No validation. 150% gets stored, risk formula breaks (max(0, (75-150)/75*100) = negative → 0, but it's illogical).

Fix:
```python
def upload_attendance(semester_no: int, percentage: float):
    if not (0 <= percentage <= 100):
        raise ValueError('Attendance must be 0-100')
    record = Attendance(...)
```

Or use Pydantic:
```python
class AttendanceRequest(BaseModel):
    percentage: float = Field(..., ge=0, le=100)
```

**Lesson:** Always validate at API boundary, not just in business logic. Garbage in = garbage out."

---

### Q11: Token Expiry & Refresh

**The Question:**
"Your JWT expires after 24 hours. A student uploads a 2-hour marksheet extraction. Midway through (hour 1), token expires. Does the extraction complete or fail?"

**Answer:**
"Current behavior: Request fails with 401 Unauthorized. Backend cancels extraction.

Better UX:
```python
@app.post('/extract')
async def extract(file: UploadFile, current_user=Depends(get_current_user)):
    # If token expiring soon, issue new one
    if token_expiry < 30_min_from_now:
        new_token = create_token(current_user)
        response.headers['X-New-Token'] = new_token
    
    # Long-running job
    task_id = asyncio.create_task(extract_async(file))
    return {'task_id': task_id, 'new_token': new_token}
```

Frontend polls with new token. Extraction continues.

Or: Refresh tokens (separate, 7-day expiry). Access token (24h) + refresh token. When access expires, use refresh to get new one."

---

---

## PART 4: BUSINESS LOGIC GOTCHAS

### Q12: GPA Formula Consistency

**The Question:**
"A student's CGPA was 7.8 when they graduated. They request a transcript 6 months later. You recalculate CGPA—it's now 7.75. Did the formula change? Is this an error?"

**Possible Causes & Answer:**
1. **Data correction:** Grades were edited after graduation
2. **Floating-point precision:** Different order of summation (7.80001 vs 7.74999 rounds differently)
3. **Credits changed:** Subject credits were corrected by admin
4. **Migration bug:** A script incorrectly modified records

**Investigation:**
```python
# Recreate CGPA from scratch
semesters = db.query(SemesterRecord).filter_by(user_id=student_id).all()
weighted_sum = sum(sem.sgpa * sem.credits_earned for sem in semesters)
total_credits = sum(sem.credits_earned for sem in semesters)
recalculated_cgpa = weighted_sum / total_credits
```

**If it differs:**
- Check `git log` for migrations
- Audit table for when grades changed
- Notify student + registrar of discrepancy
- Decide: use original 7.8 (graduation time) or new 7.75 (recalculated)?

**Decision:** For B.Tech, I'd flag this as "audit everything mutable" — grades shouldn't change post-graduation."

---

### Q13: Backdated Semester Upload

**The Question:**
"A student from Semester 3 (currently Semester 5) realizes they never uploaded Sem 3 grades. They upload now. How does this affect CGPA and risk score?"

**Answer:**
"Current behavior:
1. Grades for Semester 3 inserted into DB
2. CGPA recalculated (includes Sem 3 now)
3. Risk score recalculated
4. Timestamps: Sem 3 created_at = now (not backdated to when it was actually Sem 3)

Issue: CGPA jumps retroactively, student sees "risk dropped 10 points in 2 hours." Confusing.

Better UX:
- Add `semester_date` field: when the semester actually occurred
- Sort by date, not insertion order
- Show timeline: "Sem 3 grades added on 2026-04-25"
- Email teacher: "Backdated semester detected — verify authenticity"

For B.Tech: I'd accept the simple behavior but document it as known issue: 'Backdated uploads recalculate CGPA; check audit log for suspicious timing.'"

---

### Q14: Risk Score Notification Spam

**The Question:**
"A student's risk goes 25→26 (both LOW, but crossed some internal threshold). Do you notify them? Notify teacher? Log? What about 24→75?"

**Answer:**
"Thresholds:
- 24→26 (within same bucket): No notification
- 48→52 (cross LOW→WATCH): Notification to student + teacher email
- 74→76 (cross MODERATE→HIGH): Urgent notification + flag in dashboard
- 24→75 (huge jump): Investigate data quality (likely data entry error or new semester)

```python
def notify_risk_change(student_id, old_score, new_score):
    old_level = classify_level(old_score)
    new_level = classify_level(new_score)
    
    if old_level == new_level:
        return  # No notification
    if abs(new_score - old_score) > 30:
        # Suspicious; alert admin to verify
        notify_admin(f'Large risk jump for {student_id}')
    
    notify_student(f'Risk changed: {old_level} → {new_level}')
    notify_teacher(f'Student {student_id} now {new_level} risk')
```

For B.Tech: Simple rule—notify only on bucket changes (25, 50, 75 boundaries)."

---

---

## PART 5: PRODUCTION READINESS

### Q15: Error Handling & Logging

**The Question:**
"Your frontend tries to extract a marksheet. Gemini times out. What error does the user see?"

**Current Answer (probably):**
"500 Internal Server Error" (generic)

**Better Answer:**
```python
# Backend
try:
    response = await gemini_api_call(image)
except TimeoutError:
    logger.error(f'Gemini timeout for {user_id}')
    raise HTTPException(status_code=504, detail='AI service unavailable; retry later')
except ValueError as e:
    logger.warning(f'Invalid input: {e}')
    raise HTTPException(status_code=400, detail=str(e))

# Frontend
if response.status === 504:
    show_user("AI service is slow. Please retry in 1 minute.")
elif response.status === 400:
    show_user("File format not supported. Please upload PDF/JPG.")
else:
    show_user("Something went wrong. Contact support.")
```

**Logging levels:**
- ERROR: Unrecoverable (DB crash, API down)
- WARNING: Unexpected but handled (timeout, validation fail)
- INFO: Normal events (user login, extraction started)
- DEBUG: Internal state (intermediate calculations)

For B.Tech: Implement 3-4 main error cases + log at least ERROR level."

---

### Q16: Database Backup Strategy

**The Question:**
"Your database has 1 year of grade data. It gets corrupted. Can you recover?"

**Current answer:** "No backup—B.Tech scope, can rebuild from scratch"

**Production answer:**
```
Day 1: Full backup (daily)
Day 2-30: Incremental backups (hourly)
Day 30+: Archive backups (weekly)

Restore procedure:
1. Stop backend (prevent new writes)
2. Restore SQLite from backup
3. Run transaction log (if available) to recover delta
4. Verify CGPA computations
5. Restart backend
6. Notify stakeholders
```

For B.Tech: Document this as "if data corrupted, we'd need to restore; implement backup script for demo"

---

### Q17: Monitoring & Alerting

**The Question:**
"It's 2 AM. Your system is down. How do you find out?"

**Current:** Manual check or user reports (bad)

**Production:**
```
Monitoring:
- API response time > 5s → warning
- Error rate > 5% → alert
- Database connection pool exhausted → critical
- Gemini API quota exceeded → warning

Tools:
- Prometheus: Scrape metrics from /metrics endpoint
- Grafana: Visualize dashboards
- AlertManager: Email/SMS/Slack on thresholds
- Sentry: Real-time error tracking

Alert 2 AM:
→ Slack bot wakes on-call engineer
→ Runbook: "API latency high → check database connections → pool exhausted"
→ Engineer increases pool size or restarts backend
```

For B.Tech: Document monitoring requirements; implement basic logging."

---

### Q18: Multi-Tenancy for Multiple Colleges

**The Question:**
"You want to sell SARS to 5 other colleges. How do you isolate their data?"

**Simple Approach (current):**
- Deploy separate instance per college
- Pro: Complete isolation
- Con: 5x infra cost

**Better (multi-tenant):**
```python
# Add college_id to all tables
class User(Base):
    college_id = Column(Integer, ForeignKey('colleges.id'))
    
# Middleware: Extract college from JWT/subdomain
def get_current_college():
    return decoded_jwt['college_id']

# All queries filtered
db.query(User).filter(
    and_(
        User.college_id == current_college.id,
        User.id == user_id
    )
).first()
```

**Row-level security:**
```sql
-- PostgreSQL policy
CREATE POLICY college_isolation ON users
    USING (college_id = current_setting('app.college_id'));
```

For B.Tech: Explain single-college architecture; propose multi-tenant refactor."

---

---

## PART 6: OPEN-ENDED WISDOM QUESTIONS

### Q19: Technical Debt

**The Question:**
"List 3 pieces of technical debt in SARS. How would you prioritize fixing them?"

**Strong Answer:**
1. **No rate limiting on auth endpoints** (security/DoS risk)
   - **Effort:** 2 hours
   - **Impact:** High
   - **Priority:** Fix immediately

2. **Soft delete not implemented** (data recovery, compliance)
   - **Effort:** 1 week
   - **Impact:** Medium (nice to have)
   - **Priority:** Plan for next release

3. **No end-to-end tests** (quality assurance)
   - **Effort:** 3 days
   - **Impact:** Medium
   - **Priority:** After rate limiting

**Order:** Security > Compliance > Quality

---

### Q20: What Would You Do Differently?

**The Question:**
"Build SARS from scratch today (2026). Would you choose the same tech stack?"

**Thoughtful Answer:**
- **FastAPI:** ✅ Yes (still best Python framework)
- **React:** ✅ Yes (or Vue for simplicity)
- **SQLite:** ⚠️ Start with PostgreSQL (multi-tenancy from day 1)
- **Gemini:** ✅ Yes (better for multimodal; but consider Claude 4.6 for broader market)
- **ChromaDB:** 🤔 Maybe not—Weaviate or Pinecone more production-ready

**Architecture change:**
- Separate risk-engine microservice (batch scoring)
- Message queue for Gemini extraction (reliability)
- Docker from start (easier deployment)

---

### Q21: What Surprised You?

**The Question:**
"What did you learn building SARS that you didn't expect?"

**Genuine answers:**
- "How hard it is to parse PDFs reliably—AI solved it elegantly"
- "CGPA formula complexity—seemed simple until I found edge cases"
- "How much time goes to error handling, not core features"
- "Frontend state management is harder than backend logic"

**Avoid:** "Nothing surprised me" (unconvincing)

---

---

## PART 7: FINAL CHECKPOINTS

### If Asked: "Convince Me This Deserves an 'A'"

**Argue:**
1. ✅ **Scope:** 4 goals completed (not overambitious or trivial)
2. ✅ **Integration:** Real AI (Gemini), real DB, real auth—not tutorial code
3. ✅ **Architecture:** Thoughtful design (role-based, RAG, risk engine)
4. ✅ **Problem-solving:** Non-obvious challenges solved (PDF extraction, CGPA formula, backlog non-linearity)
5. ✅ **Production awareness:** Discusses scalability, security, monitoring
6. ✅ **Polish:** UI/UX thoughtful (review-before-save, admin dashboards)
7. ✅ **Presentation:** Can explain *why* not just *what*

### If Asked: "What Didn't Work?"

**Honest:**
- ❌ No comprehensive unit tests (quick manual testing instead)
- ❌ No authentication on the frontend (hardcoded for demo)
- ❌ Advisor chat sometimes hallucinates (rare, logged)
- ❌ Scaling not stress-tested (assumed 1000 users; no load testing)

**Turn into positives:**
- "But I'd prioritize these before production based on impact analysis"
- "Testing framework is in place; adding tests is incremental"

---

## FINAL TIPS FOR THE PRESENTATION

1. **Know the numbers:**
   - Lines of code, API endpoints, database tables
   - Time spent on each goal, total dev time
   - Risk score formula (GPA 40%, Backlog 35%, Attendance 25%)

2. **Have a narrative:**
   - Problem → Solution → Demo → Impact

3. **Anticipate questions:**
   - Why this tech stack?
   - How would you scale?
   - What breaks first?
   - Any security vulnerabilities?

4. **Be humble:**
   - "That's a great question; I'd..."
   - "I didn't think of that; here's how I'd approach it..."
   - Don't pretend to know if you don't

5. **Have backup answers:**
   - If Gemini fails during demo, show extraction from cache
   - If DB is corrupted, have recovery script ready
   - Have screenshots of key flows

**Good luck! 🚀**

---

**Document Version:** 1.0  
**Date:** 2026-04-25  
**Audience:** Interview panel, guide, technical assessors
