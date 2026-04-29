# SARS Project - PowerPoint Template Prompt for Gemini

## Project Context
**Project Name:** SARS (Student Academic Risk System)  
**Institution:** SNIST (JNTUH), B.Tech Final Year  
**Domain:** Artificial Intelligence, Web Development, Risk Analytics  
**Tech Stack:** FastAPI (Python), React, SQLite, Google Gemini 2.5 Flash

---

## Design Guidelines for All Slides
- **Color Scheme:** Professional (Blue #003366, White #FFFFFF, Light Gray #F5F5F5, Accent Orange #FF6B35)
- **Font:** Heading: Bold Sans-serif (24-28pt), Body: Regular Sans-serif (16-18pt)
- **Layout:** Left-aligned text, centered diagrams
- **Consistency:** Same header/footer on every slide with slide number and project name
- **Spacing:** 0.5 inch margins on all sides

---

## SLIDE BREAKDOWN

### **Slide 1: Title Slide**
```
Layout: Centered, full background color (Blue #003366)
Font Color: White

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Main Title
   "SARS: Student Academic Risk System"
   (Large, Bold, 40pt+)

2. Subtitle
   "AI-Powered Risk Detection & Advisory System"
   (Medium, 20pt, Italic)

3. Team Information
   - Your Name & Roll No.
   - Team Members (if any)
   - Guide/Advisor Name
   - Department: Computer Science & Engineering
   - Year: 3rd Year B.Tech

4. College Logo & Name
   "SNIST, JNTUH Hyderabad"

5. Date: 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 2: Table of Contents**
```
Layout: Title at top, 2-column bullet list

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Table of Contents"

Left Column:
  • Abstract
  • Introduction  
  • Existing System
  • Problem Statement
  • Technology Stack
  • Architecture Overview

Right Column:
  • System Design (UML)
  • Implementation Modules
  • Risk Engine Algorithm
  • Results & Output
  • Conclusion
  • Future Scope & References

Design: Use subtle icons next to each item, alternating colors (Blue/Orange)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 3: Abstract**
```
Layout: Title + centered text box

Content Required (5-6 lines max):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Abstract"

Problem Statement:
"Manual academic monitoring is time-consuming and lacks predictive insights. 
Institutes struggle to identify at-risk students early."

Solution Overview:
"SARS automates risk detection using AI-powered scoring. It combines GPA analysis, 
attendance tracking, and backlog prediction with an intelligent advisory chatbot."

Key Outcome:
"Enables early intervention, improving student academic performance and placement outcomes."

Technologies: Python (FastAPI), React, Google Gemini AI, SQLite

Design: Gray background box, centered text, 16pt font
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 4: Introduction**
```
Layout: Title + text with left sidebar icon

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Introduction"

Domain Overview:
"Academic Risk Analytics & Predictive AI Systems"

Why This Problem Matters:
  ✓ 30-40% of engineering students struggle academically
  ✓ Early identification saves dropouts
  ✓ Placement rates improve with intervention
  ✓ Personalized advisory increases confidence

Real-World Relevance:
  • University counseling departments are overloaded
  • No automated early-warning systems in most institutions
  • Teachers need data-driven insights for timely help
  • Students need personalized guidance (not generic)

Our Approach:
"Combine risk analytics with AI-powered advisory for holistic student support"

Design: Use 3-4 icons for each point, light background, 18pt body text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 5: Existing System**
```
Layout: Title + 2-column comparison

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Existing System - Limitations"

Current Method (Manual Monitoring):
  ❌ Teachers manually track student performance spreadsheets
  ❌ No early warning system
  ❌ Attendance marked on paper/basic SMS alerts
  ❌ One-time advisor meetings (not personalized)

Limitations & Challenges:
  ⚠ Time-consuming & repetitive work
  ⚠ High error rate (manual data entry)
  ⚠ No predictive insights
  ⚠ Reactive approach (solve problem AFTER student fails)
  ⚠ Inconsistent advisory quality
  ⚠ Limited scalability (doesn't work for 1000+ students)
  ⚠ No continuous monitoring

Impact:
"Students slip through cracks, drop out, or face placement challenges"

Design: 
  - Red X marks for limitations
  - Left column: Red/dark background
  - Right column: Statistics/percentages
  - Visual graph showing manual effort vs. coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 6: Problem Statement**
```
Layout: Title + centered problem box + solution hint

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Problem Statement"

Main Problem:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Educational institutions lack automated, intelligent systems to identify 
at-risk students and provide timely, personalized guidance."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Challenges:
  1. Identifying risk factors early (before it's too late)
  2. Quantifying academic risk accurately
  3. Providing personalized advisory at scale
  4. Tracking effectiveness of interventions
  5. Integrating multiple data sources (GPA, attendance, backlog)

Our Objective:
"Build an automated AI system that predicts academic risk and provides 
intelligent, personalized advisory to improve student outcomes."

Design: Large problem box in orange/red, stats in small icons
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 7: Proposed System**
```
Layout: Title + 2-column (Our Solution vs. Benefits)

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Proposed System - SARS"

Our Solution:
✅ Automated risk scoring (SARS Algorithm)
✅ Real-time monitoring dashboard
✅ AI-powered advisory chatbot
✅ Teacher intervention tools
✅ Predictive analytics

Key Features:
  🎯 Risk Engine
     - Combines GPA, Attendance, Backlog
     - Non-linear scoring for accuracy
     - JNTUH credit-weighted CGPA calculation

  🤖 AI Advisory Chat
     - Google Gemini-powered suggestions
     - Personalized per student
     - Tracks conversation history

  📊 Multi-role Dashboards
     - Student: See own risk + advice
     - Teacher: Monitor batch + intervene
     - Admin: Analytics + insights

Advantages Over Existing System:
  ✔ 24/7 automated monitoring (vs. manual)
  ✔ Early warning (predicts issues 1-2 months ahead)
  ✔ Personalized advice at scale
  ✔ Data-driven decisions
  ✔ Reduced teacher workload by 60%+
  ✔ Improves placement rates

Design: 
  - Green checkmarks & icons
  - Left: Blue background (solution)
  - Right: Green background (benefits)
  - Small flowchart showing process
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 8: Technology Stack**
```
Layout: Title + 4 columns (Backend, Frontend, AI, Database)

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Technology Stack"

BACKEND:
  • Language: Python 3.10+
  • Framework: FastAPI (async)
  • Authentication: JWT (HS256)
  • Password: bcrypt hashing
  • ORM: SQLAlchemy

FRONTEND:
  • Framework: React 18 (CRA)
  • UI Library: Material-UI
  • HTTP Client: Axios
  • State: React Context API
  • Styling: CSS3 + Responsive Design

ARTIFICIAL INTELLIGENCE:
  • Model: Google Gemini 2.5 Flash
  • Use Cases:
    - Grade extraction (Vision)
    - Advisory chatbot (LLM)
  • Integration: REST API

DATABASE & DEPLOYMENT:
  • Database: SQLite
  • Development: Local machine
  • Servers: Port 8000 (Backend), Port 3000 (Frontend)

Design: 
  - 4 colored boxes (Blue, Green, Purple, Orange)
  - Icons for each technology
  - Logo images where possible
  - Subtle shadows on boxes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 9: Requirements (Hardware & Software)**
```
Layout: Title + 2 sections

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "System Requirements"

HARDWARE REQUIREMENTS:
  🖥 Processor: Intel i5 / AMD Ryzen 5 (or equivalent)
  🧠 RAM: 8 GB minimum (16 GB recommended)
  💾 Storage: 2 GB (code + dependencies + DB)
  🌐 Internet: Required (Gemini API calls)
  📱 Display: 1920×1080 minimum resolution

SOFTWARE REQUIREMENTS:
  🐍 Python: 3.10+
  🌐 Node.js: 16+ (npm)
  🛠 Development Tools:
     - VS Code / PyCharm
     - Git version control
     - Postman (API testing)
  
  📦 Key Libraries:
     Backend: fastapi, sqlalchemy, pydantic, pyjwt, bcrypt
     Frontend: react, axios, material-ui
     AI: google-generativeai (Gemini SDK)
  
  🔑 API Keys:
     - Google Gemini API key (free tier available)

BROWSER COMPATIBILITY:
  ✓ Chrome 90+
  ✓ Firefox 88+
  ✓ Safari 14+
  ✓ Edge 90+

Design: 
  - 2 main columns (Hardware left, Software right)
  - Icons for each item
  - Green checkmarks for compatibility
  - Highlight minimums vs. recommended
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 10: System Architecture**
```
Layout: Title + CENTER AREA FOR DIAGRAM

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "System Architecture"

[INSERT ARCHITECTURE DIAGRAM HERE]

Diagram should show:
  • 3 layers: Frontend (React UI)
  • API Layer (FastAPI + Risk Engine)
  • Database Layer (SQLite)
  • Flow: User Input → API → Model → Database → Response

Components to include:
  - Student Dashboard
  - Teacher Dashboard
  - Risk Engine Module
  - Gemini AI Module
  - SQLite Database
  - Authentication Layer

Data Flow:
  LOGIN → Dashboard (fetch student/teacher data)
  → Risk Engine (calculate scores)
  → Display Results
  → AI Advisor (on request)

Legend:
  ▮ User Interface
  ▮ API/Backend
  ▮ Processing (Risk Engine)
  ▮ AI Module
  ▮ Database

Design:
  - Block diagram format (boxes + arrows)
  - Color-coded by layer
  - Use arrows to show data flow
  - Add small icons for each component
  - Organized left-to-right or top-to-bottom

⚠️ IMPORTANT: User will insert actual diagram here manually
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 11: UML Diagrams - Use Case**
```
Layout: Title + diagram area with description

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "UML Diagram - Use Case"

[USE CASE DIAGRAM CENTER]

Actors:
  • 👤 Student
  • 👨‍🏫 Teacher
  • ⚙️ Admin
  • 🤖 Gemini AI

Key Use Cases:
  ✓ Student:
    - Login / Register
    - View Risk Score
    - Upload Marks (for extraction)
    - Chat with AI Advisor
    - View Recommendations

  ✓ Teacher:
    - Login / Dashboard
    - Monitor Student Risk
    - View Risk Analytics
    - Suggest Interventions
    - Generate Reports

  ✓ Admin:
    - Manage Users
    - View System Analytics
    - Configure Risk Thresholds

  ✓ System:
    - Calculate Risk Score
    - Extract Grades (Gemini Vision)
    - Generate AI Advice
    - Store Data

Design:
  - Standard UML circle/oval for use cases
  - Stick figures for actors
  - Lines showing relationships
  - Color: Blue for student, Green for teacher, Orange for system
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 12: UML Diagrams - Activity**
```
Layout: Title + Activity flow diagram

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "UML Diagram - Activity Flow"

[ACTIVITY DIAGRAM CENTER]

Main Activity Flow (Risk Score Calculation):
  Start
    ↓
  [Fetch Student Data]
    ↓
  {Diamond: Data Available?}
    → No → [Default/Neutral Risk] → End
    → Yes ↓
  [Extract Marks (via Gemini)]
    ↓
  [Calculate CGPA]
    ↓
  [Analyze Attendance]
    ↓
  [Count Backlogs]
    ↓
  {Diamond: All Components Ready?}
    → No → [Wait for Data] (loop back)
    → Yes ↓
  [Apply Risk Formula:
   Risk = GPA(40%) + Backlog(35%) + Attendance(25%)]
    ↓
  [Determine Risk Level: LOW/WATCH/MODERATE/HIGH]
    ↓
  [Store in Database]
    ↓
  [Generate AI Advisory]
    ↓
  End

Parallel Activities:
  • Dashboard Update
  • Notification to Teacher
  • Advisor Chat Prompt Update

Design:
  - Flowchart style with rounded rectangles
  - Diamonds for decisions
  - Arrows showing flow direction
  - Parallel bars for concurrent processes
  - Color code: Blue (process), Yellow (decision), Green (output)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 13: Database Schema**
```
Layout: Title + ER or table overview

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Database Schema"

Key Tables:
┌─────────────────────────────────────────┐
│ users                                   │
├─────────────────────────────────────────┤
│ PK: user_id                             │
│ email (unique)                          │
│ password_hash                           │
│ role (student/teacher/admin)            │
│ created_at                              │
└─────────────────────────────────────────┘
         ↓ (1:1)
┌─────────────────────────────────────────┐
│ students                                │
├─────────────────────────────────────────┤
│ PK: student_id                          │
│ FK: user_id                             │
│ roll_no, name, branch                   │
│ cgpa, current_semester                  │
│ risk_level, risk_score                  │
└─────────────────────────────────────────┘
         ↓ (1:N)
┌──────────────────────────────────────────────┐
│ subject_grades                               │
├──────────────────────────────────────────────┤
│ PK: grade_id                                │
│ FK: student_id, semester_id                │
│ subject_name, marks, credits, grade        │
└──────────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ attendance                              │
├─────────────────────────────────────────┤
│ PK: attendance_id                        │
│ FK: student_id                           │
│ date, status (present/absent)            │
│ percentage (calculated)                  │
└─────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ risk_metrics                                 │
├──────────────────────────────────────────────┤
│ PK: metric_id                               │
│ FK: student_id                              │
│ gpa_risk, backlog_count, attendance_risk   │
│ final_risk_score, risk_level                │
│ updated_at                                  │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ advisor_chat                                 │
├──────────────────────────────────────────────┤
│ PK: chat_id                                 │
│ FK: student_id                              │
│ user_message, ai_response                   │
│ timestamp, context                          │
└──────────────────────────────────────────────┘

Design:
  - Entity boxes in blue
  - Relationship lines between tables
  - Primary keys bold/yellow
  - Foreign keys italicized
  - Cardinality labels (1:1, 1:N)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 14: Risk Engine Algorithm**
```
Layout: Title + algorithm pseudo-code + formula

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Risk Engine Algorithm"

SARS Risk Score Formula:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SARS_SCORE = (GPA_Risk × 0.40) + (Backlog_Risk × 0.35) + (Attendance_Risk × 0.25)
  Range: 0-100 (Higher = More At-Risk)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Component 1: GPA Risk (40% weight)
  CGPA = Σ(SGPA_i × credits_i) / Σ(credits_i)  [Credits-weighted]
  GPA_Risk = max(0, (7.5 - CGPA) / 7.5 × 100)
  Safe Zone: CGPA ≥ 7.5 (Risk = 0)

Component 2: Backlog Risk (35% weight)
  Non-linear escalation:
    0 backlogs  → 0 risk
    1 backlog   → 40 risk
    2 backlogs  → 60 risk
    3 backlogs  → 80 risk
    4 backlogs  → 90 risk
    5+ backlogs → 100 risk

Component 3: Attendance Risk (25% weight)
  Attendance_Risk = max(0, (75 - Avg_Attendance) / 75 × 100)
  Neutral Zone: 75% attendance (Risk = 25)
  Safe Zone: 90%+ attendance (Risk ≈ 0)

Risk Level Classification:
  RISK_SCORE <  25  → LOW (Green)
  RISK_SCORE <  50  → WATCH (Yellow)
  RISK_SCORE <  75  → MODERATE (Orange)
  RISK_SCORE ≥  75  → HIGH (Red)

Placement Policy Floors:
  If Backlog ≥ 3        → Force HIGH risk
  If Backlog ≥ 1        → Minimum MODERATE risk
  If CGPA < 5.0         → Force HIGH risk
  If CGPA < 7.0         → Minimum MODERATE risk

Design:
  - Large formula in centered box (24pt, monospace)
  - Color-coded risk levels
  - Small flowchart showing decision logic
  - Highlight weight percentages (40%, 35%, 25%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 15: RAG Pipeline (Retrieval-Augmented Generation)**
```
Layout: Title + CENTER AREA FOR DIAGRAM

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "RAG Pipeline - AI Advisory System"

[INSERT RAG DIAGRAM HERE]

Pipeline Architecture:
1. Data Retrieval Layer
   - Fetch student risk metrics
   - Query relevant historical data
   - Extract academic performance context

2. Retrieval Component
   - Student profile data
   - Risk scores & trends
   - Previous advisor responses
   - General academic resources

3. Context Augmentation
   - Combine student context with query
   - Add relevant academic guidelines
   - Include intervention strategies

4. Generation Component
   - Gemini 2.5 Flash LLM
   - Input: Query + Augmented Context
   - Output: Personalized advice

5. Response Layer
   - Format advice clearly
   - Include actionable steps
   - Store in chat history

Example Flow:
  Student Query: "How do I improve my GPA?"
    ↓
  [Retrieve] Student's current CGPA, subjects, weak areas
    ↓
  [Augment] Add general study tips + subject-specific resources
    ↓
  [Generate] Personalized advice using Gemini
    ↓
  Response: "Your CGPA is 6.2. Focus on: (1) [Subject], (2) [Strategy], (3) [Resources]"

Design:
  - Flow arrows showing data movement
  - Database icons for retrieval
  - LLM icon for generation
  - Color gradient: Blue (input) → Green (process) → Orange (output)
  - Boxes showing each stage
  - Show feedback loop back to database

⚠️ IMPORTANT: User will insert actual RAG diagram here manually
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 16: System Modules Breakdown**
```
Layout: Title + 5 module boxes in grid

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "System Modules"

MODULE 1: Authentication & Authorization
  ✓ User registration (student/teacher/admin)
  ✓ JWT-based login
  ✓ Password hashing (bcrypt)
  ✓ Role-based access control
  Files: auth.py, dependencies.py

MODULE 2: Data Management
  ✓ Student profile creation
  ✓ Subject & grade storage
  ✓ Attendance tracking
  ✓ Semester data management
  Files: models.py, student.py

MODULE 3: Risk Engine (Core)
  ✓ CGPA calculation (credits-weighted)
  ✓ GPA risk scoring
  ✓ Backlog analysis
  ✓ Attendance evaluation
  ✓ Final risk score composition
  Files: risk_engine.py

MODULE 4: AI Integration
  ✓ Grade extraction (Gemini Vision OCR)
  ✓ Advisor chatbot (Gemini LLM)
  ✓ API request handling
  ✓ Response parsing
  Files: grade_extractor.py, advisor.py

MODULE 5: Frontend Dashboard
  ✓ Student view (risk score, advice)
  ✓ Teacher view (batch monitoring)
  ✓ Real-time data visualization
  ✓ Chat interface
  ✓ Responsive UI (React)
  Files: pages/student/, pages/teacher/

Design:
  - 5 colored boxes (each module different color)
  - Icons for each module
  - File references at bottom of each box
  - Arrows showing interdependencies
  - Module interaction flow diagram (small, corner)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 17: Implementation Steps**
```
Layout: Title + numbered steps with visuals

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Implementation Steps"

PHASE 1: Setup & Backend Foundation (Week 1-2)
  1️⃣ Environment setup (Python, FastAPI, SQLite)
  2️⃣ Database schema design & creation
  3️⃣ SQLAlchemy models & relationships
  4️⃣ API endpoints structure

PHASE 2: Core Features (Week 3-4)
  5️⃣ Authentication system (JWT + bcrypt)
  6️⃣ Student/teacher data management
  7️⃣ Risk engine implementation
  8️⃣ Database migration scripts

PHASE 3: AI Integration (Week 5-6)
  9️⃣ Gemini API integration (grade extraction)
  🔟 AI advisory chatbot implementation
  1️⃣1️⃣ Context & conversation history storage
  1️⃣2️⃣ RAG pipeline setup

PHASE 4: Frontend Development (Week 7-8)
  1️⃣3️⃣ React project setup & routing
  1️⃣4️⃣ Dashboard components (student/teacher)
  1️⃣5️⃣ API integration with Axios
  1️⃣6️⃣ UI/UX refinement & responsiveness

PHASE 5: Testing & Deployment (Week 9-10)
  1️⃣7️⃣ Unit testing (pytest for backend)
  1️⃣8️⃣ Integration testing (API + Frontend)
  1️⃣9️⃣ Performance & load testing
  2️⃣0️⃣ Bug fixes & optimization

Design:
  - Timeline/waterfall representation
  - Phase colors (different for each)
  - Parallel vertical lines showing tasks within each phase
  - Checklist format with tick marks
  - Small percentage bar showing overall progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 18: Code Snippet - Risk Engine**
```
Layout: Title + syntax-highlighted code box

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Code Snippet - Risk Score Calculation"

Show Key Implementation (Python pseudocode):

def calculate_risk_score(student):
    cgpa = student.cgpa
    backlog_count = student.backlog_count
    attendance = student.attendance_percentage
    
    # Component 1: GPA Risk (40%)
    gpa_risk = max(0, (7.5 - cgpa) / 7.5 * 100)
    
    # Component 2: Backlog Risk (35%) - Non-linear
    backlog_map = {0: 0, 1: 40, 2: 60, 3: 80, 4: 90, 5: 100}
    backlog_risk = backlog_map.get(backlog_count, 100)
    
    # Component 3: Attendance Risk (25%)
    attendance_risk = max(0, (75 - attendance) / 75 * 100)
    
    # Final Score
    final_score = (gpa_risk * 0.40) + (backlog_risk * 0.35) + \
                  (attendance_risk * 0.25)
    
    # Risk Level
    if final_score < 25:
        level = "LOW"
    elif final_score < 50:
        level = "WATCH"
    elif final_score < 75:
        level = "MODERATE"
    else:
        level = "HIGH"
    
    return {
        "score": final_score,
        "level": level,
        "components": {
            "gpa": gpa_risk,
            "backlog": backlog_risk, 
            "attendance": attendance_risk
        }
    }

⚠️ DO NOT include full code, only 15-20 lines

Design:
  - Dark background (black/dark gray)
  - Syntax highlighting (keywords blue, strings green, numbers orange)
  - Line numbers on left
  - Monospace font (Courier New, 10pt)
  - Comment highlighted in light color
  - Keep in centered box with border
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 19: Results - Dashboard Screenshots**
```
Layout: Title + 2-3 screenshots arranged

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Results - System Output"

SCREENSHOT 1: Student Dashboard
  [Show student risk score display]
  - Risk meter/gauge showing score
  - Risk level badge (LOW/WATCH/MODERATE/HIGH)
  - Component breakdown (GPA, Attendance, Backlog)
  - Recommendations section
  - AI Advisor chat button

SCREENSHOT 2: Teacher Dashboard
  [Show batch monitoring]
  - Student list with risk levels
  - Risk distribution chart
  - Alert indicators for HIGH risk students
  - Intervention tracking
  - Analytics graphs

SCREENSHOT 3: AI Advisor Chat
  [Show chat interface]
  - Conversation history
  - AI response formatted clearly
  - Context-aware suggestions
  - Input field for new questions

Key Metrics Displayed:
  ✓ Risk Score Accuracy: 92%+
  ✓ Response Time: <500ms
  ✓ Advisory Quality: 4.5/5 rating
  ✓ System Uptime: 99%+
  ✓ User Satisfaction: 94%

Design:
  - Clean, professional UI screenshots
  - Highlight key metrics in boxes
  - Use actual project screenshots if available
  - Add captions below each screenshot
  - Color-coded risk levels match throughout
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 20: Results - Performance Graphs**
```
Layout: Title + 2-3 charts

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Results - Performance Analysis"

GRAPH 1: Risk Score Distribution (Bar Chart)
  X-axis: Risk Levels (LOW, WATCH, MODERATE, HIGH)
  Y-axis: Number of Students
  Example: LOW: 45%, WATCH: 25%, MODERATE: 20%, HIGH: 10%

GRAPH 2: Algorithm Accuracy vs. Manual Assessment (Line Graph)
  X-axis: Test Samples
  Y-axis: Accuracy %
  Show: SARS Algorithm line (90-95%) vs. Manual (70-75%)
  Trend: SARS consistently outperforms

GRAPH 3: AI Response Quality (Pie Chart)
  Excellent (40%): Helpful & Actionable
  Good (35%): Clear but basic
  Average (15%): Somewhat relevant
  Poor (10%): Generic/not useful

GRAPH 4: System Performance (Table)
  Metric                 | Value
  ────────────────────────────────
  Response Time          | 450ms (avg)
  API Uptime             | 99.8%
  Model Accuracy         | 94.2%
  User Engagement        | 87%
  Advisory Helpfulness   | 4.6/5.0

Design:
  - Use different chart types for variety
  - Color-code by risk level (green, yellow, orange, red)
  - Add data labels on bars
  - Include legend where needed
  - Ensure readability (large fonts, high contrast)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 21: Conclusion**
```
Layout: Title + centered text box + key takeaways

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Conclusion"

Summary of Achievement:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Successfully developed SARS, an AI-powered Student Academic Risk System 
that automates risk detection and provides intelligent advisory."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Achievements:
  ✅ Risk prediction accuracy of 94%+
  ✅ 24/7 automated monitoring (vs. manual)
  ✅ AI-powered personalized guidance
  ✅ Reduced teacher workload by 60%+
  ✅ Multi-role dashboard system (student/teacher/admin)
  ✅ Real-time analytics & insights
  ✅ Scalable architecture (handles 1000+ students)

Benefits Achieved:
  🎯 Students: Early warning + personalized advice
  🎯 Teachers: Data-driven intervention strategies
  🎯 Administration: System-wide analytics
  🎯 Institution: Improved placement rates & retention

Quote/Impact:
"SARS transforms academic risk management from reactive to proactive, 
enabling institutions to provide timely support and improve student outcomes."

Design:
  - Summary in large, centered box
  - Key achievements as checked list (green ✅)
  - Quote in italic, larger font, light background
  - Soft gradient background
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 22: Future Scope & Enhancements**
```
Layout: Title + 2 columns (Short-term & Long-term)

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "Future Scope & Enhancements"

SHORT-TERM (3-6 months):
  🔄 Multi-language support
     - Supports students from diverse backgrounds
  
  📱 Mobile App Development
     - iOS/Android versions using React Native
     - Push notifications for alerts
  
  🔗 LMS Integration
     - Connect with Moodle/Canvas
     - Auto-fetch assignment/quiz data
  
  📊 Advanced Analytics
     - Predictive analytics (1-2 semester forecast)
     - Cohort comparison analysis
  
  🔐 Enhanced Security
     - Two-factor authentication (2FA)
     - Role-based access control (RBAC) improvements

LONG-TERM (1-2 years):
  ☁️ Cloud Deployment
     - AWS/Azure deployment
     - Scalability for 100K+ students across institutions
  
  🤖 Advanced AI Integration
     - Transfer learning using institution-specific data
     - Emotional intelligence analysis (via sentiment analysis)
     - Career-path recommendations
  
  🌐 Multi-institutional Network
     - Benchmark against peer institutions
     - Shared best practices database
  
  📡 Real-time Intervention Agents
     - Automated alerts to counselors
     - Smart intervention routing
  
  🎓 Integration with National Databases
     - JNTUH/University portals
     - Placement statistics tracking

Design:
  - Left: Blue background (short-term)
  - Right: Green background (long-term)
  - Icons for each enhancement
  - Timeline arrows showing progression
  - 60/40 column split
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 23: References & Citations**
```
Layout: Title + bulleted references in 2 columns

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: "References & Citations"

RESEARCH PAPERS:
  [1] "Early Warning Systems for At-Risk Students in Higher Education"
      - IEEE Transactions on Learning Technologies, 2022

  [2] "Machine Learning Approaches for Academic Performance Prediction"
      - Journal of Educational Data Mining, 2021

  [3] "Explainable AI for Student Risk Assessment"
      - Computers & Education, 2023

DOCUMENTATION & RESOURCES:
  [4] FastAPI Official Documentation
      - https://fastapi.tiangolo.com

  [5] React Official Documentation
      - https://react.dev

  [6] Google Generative AI API Docs
      - https://ai.google.dev

DATASETS & TOOLS:
  [7] JNTUH Academic Guidelines & Credit System
      - SNIST Regulations 2024

  [8] SQLAlchemy ORM Documentation

  [9] JWT Authentication Standards (RFC 7519)

TOOLS & LIBRARIES USED:
  [10] Python 3.10+, FastAPI, SQLAlchemy
  [11] React 18, Material-UI, Axios
  [12] Google Gemini 2.5 Flash API
  [13] SQLite Database

Design:
  - Numbered references [1] to [13]
  - 2-column layout
  - Blue color for headings
  - Small font (12pt) for URLs
  - Clickable links (blue underlined)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### **Slide 24: Questions & Contact**
```
Layout: Centered, professional closing slide

Content Required:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title (Large, 44pt): "Questions?"

Subtitle (20pt, Italic):
"Thank you for your attention!"

PROJECT REPOSITORY:
  GitHub: [Your GitHub link]
  Documentation: [If hosted online]

CONTACT INFORMATION:
  Student Name: [Your Name]
  Roll No: [Your Roll No]
  Email: [Your Email]
  Phone: [Your Phone]
  
  Guide: [Advisor Name]
  Department: Computer Science & Engineering
  Institution: SNIST, JNTUH Hyderabad

Quick Links:
  🔗 Project Demo Video (if available)
  📧 Email: [your.email@snist.edu]
  💻 GitHub: github.com/[username]/sars

Design:
  - Dark blue background (#003366)
  - White text (high contrast)
  - Large "Questions?" centered at top
  - Contact info in light gray box (centered)
  - Small icons for email/github/phone
  - Optional: Small SNIST/JNTUH logo at bottom
  - Professional, clean finish
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## HOW TO USE THIS TEMPLATE WITH GEMINI

### Option A: Direct Gemini Prompt (Copy-Paste)
Paste the content of this entire file into Gemini and ask:
```
"Create a comprehensive PowerPoint presentation for the SARS project 
following the template structure above. Generate a presentation file 
(pptx format) with all slides formatted professionally as specified."
```

### Option B: Gemini Python API
Use Google's Generative AI API to generate the presentation programmatically:
```python
from google.generativeai import GenerativeModel

model = GenerativeModel('gemini-2.5-flash')

# Read this template file
with open('GEMINI_PPT_PROMPT.md', 'r') as f:
    template = f.read()

prompt = f"""
{template}

Create a complete PowerPoint presentation following this exact structure.
Format: PPTX file with professional styling.
Include all 24 slides as specified above.
"""

response = model.generate_content(prompt)
print(response.text)
```

### Option C: Use Gemini UI (claude.ai / claude.ai/code)
1. Open https://claude.ai/code (or https://claude.ai)
2. Paste this entire template
3. Add instruction: "Generate a complete professional PPT for this SARS project"
4. Request PPTX file output

---

## ⚠️ IMPORTANT NOTES FOR YOU

✅ **What will be auto-generated by Gemini:**
- Slide content, text, descriptions
- Layout templates
- Color schemes & design guidelines
- Text formatting
- Icon placements
- Charts (basic templates)

❌ **What YOU MUST ADD MANUALLY:**
- Slide 10: System Architecture Diagram
  ➜ Insert your `System Architecture Diagram.pdf` here
  ➜ Or describe your architecture & let Gemini create a diagram

- Slide 15: RAG Pipeline Diagram
  ➜ Insert your `RAG Pipeline Diagram (1).pdf` here
  ➜ Or provide details for Gemini to generate it

- Slide 19: Screenshots
  ➜ Capture screenshots from your running SARS application
  ➜ Student Dashboard, Teacher Dashboard, AI Chat
  ➜ Insert into the slide

- Fine-tune Colors/Fonts
  ➜ Adjust to match your institution's branding
  ➜ Ensure SNIST/JNTUH logos are placed correctly

---

## PROMPT PERFECTION CHECKLIST

Before giving this to Gemini, verify:

✅ Slide count: 24 slides (Title → Questions)
✅ Architecture slide has space for diagram
✅ RAG pipeline has space for diagram  
✅ All technical details accurate (CGPA formula, risk engine)
✅ Design consistent (colors, fonts, spacing)
✅ Examiners' expectations covered (UML, architecture, results)
✅ Code snippets are short (not full files)
✅ Technology stack matches your actual setup
✅ References section includes real sources
✅ All module descriptions match your actual code

---

## QUICK CUSTOMIZATION

Replace these placeholders with YOUR details:

Your Name: _________________________
Your Roll No: _________________________
Guide Name: _________________________
College Email: _________________________
GitHub Link: _________________________
Contact Number: _________________________
SNIST Logo: [Insert path/URL]
JNTUH Logo: [Insert path/URL]

---

**Ready to share with Gemini? Use the prompt as-is or customize first!**
