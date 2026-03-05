# SARS — Student Academic Risk Assessment System
## Goal 1: Foundation & Authentication — Setup Guide

---

## Project Structure

```
sars/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry point
│   │   ├── config.py            ← Settings (SECRET_KEY etc.)
│   │   ├── database.py          ← SQLite engine + session
│   │   ├── models/
│   │   │   └── models.py        ← ALL 8 database tables (full schema)
│   │   ├── routes/
│   │   │   ├── auth.py          ← /auth/register, /auth/login, /auth/me
│   │   │   ├── student.py       ← /student/profile (+ Goals 2-4 routes)
│   │   │   └── teacher.py       ← /teacher/profile, /teacher/students
│   │   └── services/
│   │       ├── auth_service.py  ← JWT + password hashing logic
│   │       └── dependencies.py  ← get_current_user, require_student, require_teacher
│   ├── requirements.txt
│   └── sars.db                  ← Created automatically on first run
│
└── frontend/
    ├── public/index.html
    ├── src/
    │   ├── App.jsx              ← Root router
    │   ├── index.js
    │   ├── context/
    │   │   └── AuthContext.jsx  ← Auth state (useAuth hook)
    │   ├── services/
    │   │   └── api.js           ← All API calls (Axios instance)
    │   ├── components/
    │   │   ├── ProtectedRoute.jsx
    │   │   └── DashboardLayout.jsx
    │   ├── pages/
    │   │   ├── LoginPage.jsx    ← Login + Register (tabbed)
    │   │   ├── student/
    │   │   │   └── StudentDashboard.jsx  ← 5 pages (Overview, Upload, Performance, Risk, Advisory)
    │   │   └── teacher/
    │   │       └── TeacherDashboard.jsx  ← 5 pages (Overview, Students, Risk, Interventions, Analytics)
    │   └── styles/
    │       └── global.css       ← Design tokens + global resets
    └── package.json
```

---

## Step 1: Backend Setup

```bash
cd sars/backend

# Create virtual environment (ALWAYS use venv — never install globally)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file for your secret key (IMPORTANT for production)
echo "SECRET_KEY=your-super-secret-key-change-this" > .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

The server starts at: **http://localhost:8000**
Swagger UI (API docs): **http://localhost:8000/docs** ← Test all APIs here!

The SQLite database (`sars.db`) is created automatically on first run.

---

## Step 2: Frontend Setup

```bash
cd sars/frontend

# Install packages
npm install

# Start React dev server
npm start
```

Opens at: **http://localhost:3000**

The `"proxy": "http://localhost:8000"` in package.json routes API calls automatically.

---

## Step 3: Test Checklist (Goal 1)

Run both servers, then test each item:

### ✅ Auth Tests (use Swagger at /docs OR the UI)

**Test 1: Register a student**
```json
POST /auth/register
{
  "full_name": "Santhosh Kethavath",
  "email": "student@test.com",
  "password": "password123",
  "role": "student",
  "roll_number": "2021BTCS001",
  "branch": "Computer Science Engineering",
  "enrollment_year": 2021
}
```
Expected: 201 response with `access_token`

**Test 2: Register a teacher**
```json
POST /auth/register
{
  "full_name": "Dr. Sunil Bhutada",
  "email": "teacher@test.com",
  "password": "password123",
  "role": "teacher",
  "department": "Computer Science",
  "employee_id": "FAC001"
}
```

**Test 3: Login**
```json
POST /auth/login
{"email": "student@test.com", "password": "password123"}
```
Expected: JWT token in response

**Test 4: Wrong password**
```json
POST /auth/login
{"email": "student@test.com", "password": "wrongpassword"}
```
Expected: 401 error

**Test 5: Role protection**
- Log in as student → copy token → call `GET /teacher/students` with that token
- Expected: 403 Forbidden (student cannot access teacher routes)

### ✅ Frontend Tests

- [ ] Go to http://localhost:3000 → redirects to /login
- [ ] Register as student → redirects to /student dashboard
- [ ] Register as teacher → redirects to /teacher dashboard
- [ ] Both dashboards show correct user name in sidebar
- [ ] Logout button → returns to /login, cannot navigate back
- [ ] Refresh page → stays logged in (sessionStorage token preserved)
- [ ] All 5 sidebar nav items navigate to correct pages
- [ ] Wrong role URL → auto-redirects (student visiting /teacher → goes to /student)

---

## Important Design Decisions (Read Before Coding Further)

### Why sessionStorage not localStorage?
`sessionStorage` is cleared when the browser tab closes. This is safer for academic data — a student on a shared college computer won't leave their session open accidentally. `localStorage` persists forever which is riskier.

### Why define ALL 8 tables in Goal 1?
SQLite doesn't support ALTER TABLE for adding columns easily. If we add tables later, we'd need to drop and recreate the database, losing all test data. By defining the full schema now, Goals 2-6 only INSERT data — they never touch the schema.

### Why JWT in the payload contains only `sub` (user_id) and `role`?
Never put sensitive data (email, name) in JWT payload — it's base64 encoded, not encrypted, and can be decoded by anyone. Only put the minimum needed to identify and authorize the user. Fetch everything else from the database using the user_id.

### Why separate `User` and `Student`/`Teacher` tables?
Single auth table means login works the same for both roles. Profile tables hold role-specific data. This avoids null columns (e.g., a teacher shouldn't have a roll_number column) and follows proper database normalization.

---

## Next: Goal 2 — PDF Ingestion & Grade Extraction

After all Goal 1 tests pass, move to Goal 2:
1. `pip install pymupdf python-multipart` (add to requirements.txt)
2. Add `POST /student/upload-marksheet` route to `student.py`
3. Build `app/services/pdf_extractor.py`
4. Add upload UI to `UploadMarks` component in `StudentDashboard.jsx`
