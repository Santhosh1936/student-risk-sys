from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)           # "student" or "teacher"
    full_name = Column(String, nullable=False)
    roll_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    branch = Column(String, nullable=True)
    enrollment_year = Column(Integer, nullable=True)
    current_semester = Column(Integer, default=1)
    cgpa = Column(Float, nullable=True)
    user = relationship("User", back_populates="student_profile")
    semester_records = relationship("SemesterRecord", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    risk_scores = relationship("RiskScore", back_populates="student")
    advisory_sessions = relationship("AdvisorySession", back_populates="student")
    chat_thread = relationship("ChatThread", back_populates="student", uselist=False)

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department = Column(String, nullable=True)
    employee_id = Column(String, nullable=True)
    user = relationship("User", back_populates="teacher_profile")
    interventions = relationship("Intervention", back_populates="teacher")

class SemesterRecord(Base):
    __tablename__ = "semester_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    semester_no = Column(Integer, nullable=False)
    gpa = Column(Float, nullable=True)
    credits_attempted = Column(Integer, nullable=True)
    credits_earned = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_confirmed = Column(Boolean, default=False)
    student = relationship("Student", back_populates="semester_records")
    subject_grades = relationship("SubjectGrade", back_populates="semester_record")

class SubjectGrade(Base):
    __tablename__ = "subject_grades"
    id = Column(Integer, primary_key=True, index=True)
    semester_record_id = Column(Integer, ForeignKey("semester_records.id"), nullable=False)
    subject_name = Column(String, nullable=False)
    subject_code = Column(String, nullable=True)
    marks_obtained = Column(Float, nullable=True)
    max_marks = Column(Float, default=100)
    grade_letter = Column(String, nullable=True)    # O, A+, A, B+, B, C, D, F
    grade_points = Column(Float, nullable=True)     # 10, 9, 8, 7, 6, 5, 4, 0
    credits = Column(Integer, nullable=True)
    is_backlog = Column(Boolean, default=False)
    semester_record = relationship("SemesterRecord", back_populates="subject_grades")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    semester_no = Column(Integer, nullable=False)
    subject_name = Column(String, nullable=False)
    classes_attended = Column(Integer, default=0)
    total_classes = Column(Integer, default=0)
    percentage = Column(Float, nullable=True)
    student = relationship("Student", back_populates="attendance_records")

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    sars_score = Column(Float, nullable=False)         # 0.0 to 1.0
    risk_level = Column(String, nullable=False)        # LOW, WATCH, MODERATE, HIGH
    confidence = Column(Float, nullable=True)
    factor_breakdown = Column(JSON, nullable=True)
    advisory_text = Column(Text, nullable=True)
    student = relationship("Student", back_populates="risk_scores")

class Intervention(Base):
    __tablename__ = "interventions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    intervention_type = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String, nullable=True)
    teacher = relationship("Teacher", back_populates="interventions")

class AdvisorySession(Base):
    __tablename__ = "advisory_sessions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    query = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    student = relationship("Student", back_populates="advisory_sessions")


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id          = Column(Integer, primary_key=True, index=True)
    student_id  = Column(Integer, ForeignKey("students.id"),
                         unique=True, nullable=False)
    created_at  = Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc))
    data_updated = Column(Boolean, default=False)
    context_set  = Column(Boolean, default=False)

    student  = relationship("Student", back_populates="chat_thread")
    messages = relationship("ChatMessage", back_populates="thread",
                            order_by="ChatMessage.created_at",
                            cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id           = Column(Integer, primary_key=True, index=True)
    thread_id    = Column(Integer, ForeignKey("chat_threads.id"),
                          nullable=False)
    role         = Column(String, nullable=False)   # "user" or "model"
    content      = Column(Text, nullable=False)
    created_at   = Column(DateTime(timezone=True),
                          default=lambda: datetime.now(timezone.utc))
    message_type = Column(String, default="normal")
                          # "normal", "context_seed", "data_refresh"

    thread = relationship("ChatThread", back_populates="messages")
