# SARS Project - Presentation Cheat Sheet

**Quick Reference for Presenters | Keep Handy During Demo**

---

## 🎯 60-SECOND PITCH

**What is SARS?**

"SARS is an intelligent system that identifies at-risk students using AI and multi-factor analysis. It combines automated grade extraction, real-time risk scoring, and AI-powered advising to help students and teachers act early. Built with FastAPI + React + Google Gemini."

---

## 📊 KEY NUMBERS

| Metric | Value |
|--------|-------|
| Backend lines of code | ~2000 |
| Frontend lines of code | ~1500 |
| Database tables | 6+ |
| API endpoints | 20+ |
| Risk components | 3 (GPA, Backlog, Attendance) |
| Time to build | ~7 weeks |
| Tech stack items | 5 core (FastAPI, React, SQLite, Gemini, ChromaDB) |

---

## ⚙️ CORE FORMULAS (Memorize These)

### SARS Score (0-100, higher = more at-risk)
```
SARS = (GPA_Risk × 0.40) + (Backlog_Risk × 0.35) + (Attendance_Risk × 0.25)
```

### GPA Risk
```
GPA_Risk = max(0, (7.5 - CGPA) / 7.5 * 100)
Threshold: CGPA ≥ 7.5 = safe
```

### Attendance Risk
```
Attendance_Risk = max(0, (75 - Attendance%) / 75 * 100)
Threshold: Attendance ≥ 75% = safe
```

### Backlog Risk (Non-linear)
```
0 backlogs → 0
1 backlog  → 40
2 backlogs → 60
3 backlogs → 80
4 backlogs → 90
5+ backlogs → 100
```

### CGPA (Credits-Weighted)
```
CGPA = Σ(SGPA_i × Credits_i) / Σ(Credits_i)
NOT simple average—credits matter!
```

### Risk Levels
```
0-24   = LOW (green)
25-49  = WATCH (yellow)
50-74  = MODERATE (orange)
75+    = HIGH (red)
```

---

## 🏗️ ARCHITECTURE AT A GLANCE

```
Frontend          Backend           Database      AI
(React 3000)  → (FastAPI 8000)  → (SQLite)   ← (Gemini)
                  Risk Engine
                  Grade Extractor
                  RAG Advisor
                  Auth
```

### Key API Endpoints (Show if Asked)

**Auth:**
- POST /auth/register
- POST /auth/login
- GET /auth/me

**Student:**
- POST /student/extract-marksheet
- POST /student/confirm-marksheet
- GET /student/risk-score
- POST /student/advisor/chat
- GET /student/semesters

**Teacher:**
- GET /teacher/risk-overview
- GET /teacher/students/{id}/profile
- POST /teacher/interventions
- GET /teacher/analytics

---

## 🔑 KEY FEATURES (Talking Points)

| Feature | Why It Matters |
|---------|---------------|
| **AI Marksheet Extraction** | Saves hours of manual data entry; handles PDFs from any college layout |
| **SARS Risk Engine** | Combines 3 factors intelligently; reflects placement policy |
| **RAG-Backed Advisor** | Advice grounded in student's actual data, not generic |
| **Teacher Dashboards** | Early visibility into class trends; enables intervention |
| **Role-Based Auth** | Students & teachers see only their own data |

---

## 🎬 DEMO FLOW (Quick Reference)

### Part 1: Student (5 min)
1. Login: `student@example.com` / `password123`
2. Show: Dashboard with risk score (e.g., 45 = WATCH)
3. Upload: Sample marksheet PDF
4. Show: Real-time extraction (talk while Gemini works)
5. Confirm: Extracted data (show review-before-save)
6. Chat: Ask advisor "Why am I at WATCH risk?"
7. Show: Personalized response (not generic)

### Part 2: Teacher (5 min)
1. Logout & Login: `teacher@example.com` / `teacherpass123`
2. Show: Risk overview (all students sorted by SARS score)
3. Click: Student we just uploaded marks for
4. Show: Grades breakdown + trend + CGPA
5. Log: Intervention (e.g., "Tutoring scheduled")
6. Analytics: Show class average, backlog distribution, trends

**Key talking points during demo:**
- "Extraction took X seconds vs. manual entry would take 10 minutes"
- "Risk score automatically updated after grades"
- "Advisor is not generic—it knows this student's specific situation"
- "Teachers can track intervention effectiveness"

---

## 💡 Why This Tech Stack

| Choice | Why |
|--------|-----|
| **FastAPI** | Async-first; handles concurrent Gemini calls without blocking |
| **React** | SPA (single-page app); snappy UX; component reusability |
| **SQLite** | Serverless; sufficient for B.Tech scope; scales to 1000+ students |
| **Gemini 2.5 Flash** | Vision API for PDF OCR; Chat API for advisor; multimodal |
| **ChromaDB** | Vector embeddings for RAG; finds relevant student context fast |

---

## 🎓 Problem Statement (If Asked)

**The Challenge:**
- ❌ Manual tracking of student performance is tedious
- ❌ Risk identification happens too late (after grades finalized)
- ❌ Teachers lack visibility into trends
- ❌ Students don't get personalized guidance at scale
- ❌ Data entry for marksheets is error-prone

**SARS Solution:**
- ✅ Automated risk identification
- ✅ AI-extracted marksheets
- ✅ Early warnings
- ✅ Personalized advisor
- ✅ Teacher monitoring dashboards

---

## 🔐 Security Highlights (If Challenged)

| Concern | Solution |
|---------|----------|
| Password security | Hashed with bcrypt (one-way, not reversible) |
| API authentication | JWT tokens (signed server-side, 24h expiry) |
| Data isolation | Every query filtered by `user_id` from JWT |
| XSS | React auto-escapes JSX; no user HTML in DOM |
| SQL Injection | SQLAlchemy ORM uses parameterized queries |
| .env secrets | Not committed to git; listed in .gitignore |

---

## 📈 Scalability (If Asked "What's Next?")

**Current:** Works for 1000 students at one college  
**To scale to 100K students across 100 colleges:**

1. **Database:** SQLite → PostgreSQL (multi-tenant)
2. **Risk scoring:** Batch job (nightly); cache in Redis
3. **Gemini API:** Queue system (Celery); fallback extraction
4. **Vector DB:** ChromaDB → Weaviate (sharding by institution)
5. **Frontend:** Pagination + server-side filtering
6. **Infra:** Docker + Kubernetes for multi-instance deployment

---

## 🚨 Known Limitations (Be Honest)

| Limitation | Why | Fix |
|-----------|-----|-----|
| No unit tests | Time pressure | Would add before production |
| Single-college setup | B.Tech scope | Multi-tenant refactor needed |
| No rate limiting | Demo code | Add middleware for auth endpoints |
| Soft delete not implemented | Not required for scope | Add for compliance later |
| No backup strategy | File-based demo | Implement daily snapshots for production |

**Frame it:** "These are intentional trade-offs for B.Tech scope; I'd prioritize them based on impact if taking to production."

---

## 🎯 Possible Interview Questions (Prepare Answers)

### **Q: Why not use [other technology]?**
**Answer:** "I evaluated [tech], but it adds complexity we don't need. FastAPI/React/SQLite are sufficient for scope while being industry-standard. If requirements change [specific scenario], I'd revisit."

### **Q: What if the database gets corrupted?**
**Answer:** "Currently no automated backup—B.Tech demo assumption. In production, I'd implement daily SQLite backups + transaction logs. Recovery: restore from backup + apply transaction log delta."

### **Q: How do you handle concurrent uploads?**
**Answer:** "FastAPI's async endpoints don't block each other. SQLAlchemy transactions ensure atomic operations. SQLite's default isolation handles conflicts. For 100K concurrent users, I'd use PostgreSQL's explicit locking."

### **Q: Can students see each other's grades?**
**Answer:** "No. Every endpoint verifies JWT user_id and filters queries by that user_id. Teachers see only students (would need class_id FK in current design; simplified for scope)."

### **Q: What if Gemini API is down?**
**Answer:** "Marksheet extraction fails with retry option. Advisor chat falls back to full-context prompt (slower, but works). Risk scoring is fully local—never depends on Gemini."

### **Q: How would you deploy this?**
**Answer:** "Frontend: Vercel/Netlify (CI/CD on git push). Backend: Railway/Heroku or AWS Lambda. Database: PostgreSQL on RDS (production). Secrets: Environment variables. Monitoring: Sentry for errors, Prometheus for metrics."

### **Q: What surprised you most?**
**Answer:** "[Pick one: PDF parsing complexity, CGPA formula edge cases, AI hallucinations, state management difficulty, etc.] I initially thought it would be [assumption], but learned [lesson]."

---

## 📋 Checklist Before Presentation

- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend running on `http://localhost:3000`
- ✅ `.env` has valid `GEMINI_API_KEY`
- ✅ Sample student + teacher accounts exist in DB
- ✅ Sample marksheet PDF ready to upload
- ✅ Test accounts have actual grade data (for meaningful dashboard)
- ✅ All 3 risk levels represented in test data (LOW, MODERATE, HIGH)
- ✅ Backup: Screenshots of extraction if Gemini times out
- ✅ Backup: Pre-cached advisor responses if chat fails
- ✅ Laptop charger handy
- ✅ Have this cheat sheet printed or on second monitor

---

## 💬 Sample Responses (Delivery)

### **Opening (30 seconds):**
"SARS is an intelligent risk management system for academic institutions. It combines AI-powered marksheet extraction, multi-factor risk scoring, and personalized student advising to identify at-risk students early. This enables teachers to intervene before students fail. We built it with FastAPI, React, and Google Gemini over 7 weeks."

### **Problem Statement (1 minute):**
"The problem we're solving: academic risk identification happens too late. By the time semester-end grades are in, it's too late for intervention. SARS gives real-time visibility into risk across three factors—GPA trend, backlogs, and attendance—using a formula grounded in JNTUH placement policy."

### **Architecture (1 minute):**
"The system has three layers. Frontend: React SPA lets students upload marks and chat with an advisor, while teachers monitor risk dashboards. Backend: FastAPI handles authentication, risk computation, and AI integration. Database: SQLite stores grades, attendance, and chat history. AI: Google Gemini extracts marksheets from PDFs and powers the advisory chatbot."

### **Key Innovation (1 minute):**
"The main innovation is the RAG-backed advisor. Instead of generic advice, it retrieves the student's actual grades, attendance, backlog history, and past advisor conversations, then generates personalized recommendations grounded in data. This scales advising across hundreds of students."

### **Closing (30 seconds):**
"SARS demonstrates full-stack development, AI integration, thoughtful architecture, and security awareness. It's production-ready in core logic and would need scaling work for 100K+ students, but the design supports it."

---

## 🎯 If Time is Running Out

**Compress to 5 min:**
1. Show login screen (5 sec)
2. Upload marksheet (30 sec—talk while extracting)
3. Show risk dashboard (30 sec)
4. Ask advisor a question (30 sec—show RAG magic)
5. Switch to teacher view (30 sec)
6. Show intervention logging (30 sec)
7. Show analytics (30 sec)
8. Sum up: "Automated extraction + intelligent risk scoring + AI advising + teacher monitoring = early intervention" (1 min)

**Compress to 2 min (elevator pitch):**
"SARS identifies at-risk students using AI and multi-factor analysis. Upload a marksheet → Gemini extracts grades → SARS computes risk score combining GPA, backlogs, and attendance → students get personalized advice from an AI advisor → teachers see dashboard. Increases placement success by enabling early intervention."

---

## 🎁 Final Words

**Confidence:** You built a non-trivial system that works. Own it.  
**Honesty:** Acknowledge trade-offs ("B.Tech scope" is your friend).  
**Curiosity:** When asked something you don't know, say "I'd approach it like this..." instead of guessing.  
**Clarity:** Explain *why*, not just *what*. ("Why weights 40/35/25?" is better answered with placement policy justification than "just seemed right.")

**You've got this! 🚀**

---

**Version:** 1.0  
**Last Updated:** 2026-04-25  
**Presenter:** [Your Name]  
**Team Members:** [Friends' Names]
