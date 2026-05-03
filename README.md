# SARS

Student Academic Risk Assessment System for SNIST/JNTUH-style academic records.

This app combines semester record management, AI-assisted marksheet extraction, risk scoring, attendance tracking, a student advisory chat, and teacher-side monitoring tools in one FastAPI + React project.

## Current Features

- Role-based authentication for students and teachers
- AI extraction of semester marksheets from PDF, JPG, JPEG, and PNG files
- Review-before-save workflow for extracted subject data
- Automatic CGPA recomputation using a credits-weighted JNTUH formula
- SARS risk scoring based on CGPA trend, backlog count, and attendance
- Student attendance upload and per-semester tracking
- RAG-backed advisor chat grounded in each student's own records
- Teacher views for risk overview, student drill-down, interventions, and class analytics
- Standalone reusable extractor script at `../shareable_grade_extractor.py`

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, Pydantic
- Frontend: React, React Router, Axios
- AI services: Google Gemini 2.5 Flash, Gemini embeddings, ChromaDB

## Project Layout

```text
sars/
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- config.py
|   |   |-- routes/
|   |   |   |-- auth.py
|   |   |   |-- student.py
|   |   |   `-- teacher.py
|   |   |-- services/
|   |   |   |-- grade_extractor.py
|   |   |   |-- risk_engine.py
|   |   |   |-- advisor.py
|   |   |   `-- rag_service.py
|   |   `-- models/
|   |-- requirements.txt
|   `-- sars.db
`-- frontend/
    |-- package.json
    `-- src/
        |-- App.jsx
        |-- services/api.js
        `-- pages/
            |-- student/
            `-- teacher/
```

## Backend Setup

```bash
cd sars/backend
python -m venv venv
```

Activate the environment:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install pymupdf
```

`PyMuPDF` is required for PDF marksheet uploads because the extractor renders the first PDF page before sending it to Gemini.

Create `backend/.env`:

```env
SECRET_KEY=replace_with_a_secure_32_plus_char_secret
GEMINI_API_KEY=your_google_ai_studio_key
TEACHER_INVITE_CODE=set_your_own_teacher_code
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ENVIRONMENT=development
DEBUG=true
```

Generate a strong secret if needed:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Useful URLs:

- API root: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

Notes:

- The backend refuses to start if `SECRET_KEY` is missing, too short, or still using an insecure default.
- `sars.db` is created automatically in `sars/backend/`.
- AI extraction, advisor chat, and RAG indexing require a valid `GEMINI_API_KEY`.

## Frontend Setup

```bash
cd sars/frontend
npm install
npm start
```

The React app runs on `http://localhost:3000`.

If you want to override the backend URL, create `frontend/.env`:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

## Main User Flows

### Student

1. Register or log in.
2. Upload a marksheet through `Upload Marks`.
3. Let Gemini extract the document.
4. Review and correct the extracted fields.
5. Confirm the semester to save grades and recompute CGPA.
6. View risk score, attendance, and advisor insights.

### Teacher

1. Register with the configured teacher invite code.
2. Review students sorted by risk level.
3. Open full student profiles.
4. Log or resolve interventions.
5. Use analytics to inspect CGPA, backlog, attendance, and risk trends.

## Important API Areas

### Authentication

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Student

- `GET /student/profile`
- `PATCH /student/profile`
- `GET /student/extraction-status`
- `POST /student/extract-marksheet`
- `POST /student/confirm-marksheet`
- `GET /student/semesters`
- `DELETE /student/semesters/{semester_no}`
- `POST /student/attendance`
- `GET /student/attendance`
- `DELETE /student/attendance/{semester_no}`
- `POST /student/compute-risk`
- `GET /student/risk-score`
- `POST /student/advisor/chat`
- `GET /student/advisor/history`
- `GET /student/rag-status`

### Teacher

- `GET /teacher/profile`
- `GET /teacher/students`
- `GET /teacher/risk-overview`
- `GET /teacher/students/{student_id}/risk`
- `GET /teacher/students/{student_id}/profile`
- `POST /teacher/interventions`
- `PATCH /teacher/interventions/{intervention_id}/resolve`
- `GET /teacher/interventions`
- `GET /teacher/analytics`

## Standalone Grade Extractor

The repo root also contains a shareable extractor that can be reused outside the FastAPI app:

- File: `../shareable_grade_extractor.py`
- Entry points:
  - `extract_from_file(file_path, api_key=None)`
  - `get_gemini_status(api_key=None)`

Example:

```python
from shareable_grade_extractor import extract_from_file

result = extract_from_file("test_grade_sheet.pdf", api_key="YOUR_GEMINI_KEY")
print(result["student_name"])
print(result["subjects"][0])
```

If `api_key` is omitted, the script reads `GEMINI_API_KEY` from the environment.

## Risk Model Summary

The current SARS score uses three weighted components:

- GPA risk: 40%
- Backlog risk: 35%
- Attendance risk: 25%

The engine also applies placement-oriented floors:

- CGPA below 7.5 raises risk sensitivity
- Any active backlog affects placement eligibility
- Three or more backlogs force a high-risk outcome

## Local Storage Used by the App

- SQLite database: `sars/backend/sars.db`
- Uploaded files: temporary files under `backend/uploads/`
- Chroma vector store: path from `CHROMA_DB_PATH` (defaults to `./chroma_db`)

## Development Notes

- Student sessions are stored in `sessionStorage`.
- The advisor chat keeps student conversations isolated by thread.
- RAG is refreshed automatically after profile, marksheet, and attendance updates.
- If Gemini is unavailable, the advisor falls back to a non-RAG full-context prompt path.
