"""
models.py
SQLAlchemy ORM Entities for User management, Student profiles,
Surveys, Risk Assessments, Counselor Alerts, and Case Notes.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base

import hashlib
import os

def utc_now():
    return datetime.now(timezone.utc)

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed: str) -> bool:
    if not hashed:
        return False
    if "$" not in hashed:
        return plain_password == hashed
    try:
        salt, key_hex = hashed.split("$", 1)
        test_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), bytes.fromhex(salt), 100000)
        return test_key.hex() == key_hex
    except Exception:
        return False

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(50), default="student")  # 'student' or 'counselor'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id_number = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100), default="Computer Science & Engineering")
    year_of_study = Column(Integer, default=3)
    avatar_color = Column(String(20), default="#4F46E5")
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    surveys = relationship("SurveyCheckIn", back_populates="student", order_by="desc(SurveyCheckIn.created_at)")
    alerts = relationship("CounselorAlert", back_populates="student", order_by="desc(CounselorAlert.created_at)")

class SurveyCheckIn(Base):
    __tablename__ = "survey_check_ins"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    
    # Academic Factors
    gpa = Column(Float, nullable=False)
    study_hours_per_day = Column(Float, nullable=False)
    academic_workload = Column(Integer, nullable=False)  # 1-10
    exam_pressure = Column(Integer, nullable=False)      # 0-10
    attendance_percentage = Column(Float, nullable=False)# 0-100%

    # Lifestyle Factors
    sleep_hours_per_night = Column(Float, nullable=False)
    sleep_quality = Column(Integer, nullable=False)      # 1-10
    screen_time_hours = Column(Float, nullable=False)
    exercise_days = Column(Integer, nullable=False)      # 0-7
    social_support = Column(Integer, nullable=False)     # 1-10

    # Psychological Factors
    mood_energy = Column(Integer, nullable=False)        # 1-10
    self_reported_stress = Column(Integer, nullable=False)# 1-10
    feeling_overwhelmed = Column(Integer, nullable=False)# 1-10
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    student = relationship("StudentProfile", back_populates="surveys")
    assessment = relationship("RiskAssessment", back_populates="survey", uselist=False)

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("survey_check_ins.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    
    risk_score = Column(Float, nullable=False)          # 0.0 - 100.0%
    risk_level = Column(String(20), nullable=False)      # 'Low', 'Moderate', 'High'
    risk_color = Column(String(20), default="#10B981")
    top_drivers = Column(Text, nullable=True)           # JSON string list
    protective_factors = Column(Text, nullable=True)    # JSON string list
    model_version = Column(String(100), default="XGBoost / Random Forest Classifier")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    survey = relationship("SurveyCheckIn", back_populates="assessment")
    alert = relationship("CounselorAlert", back_populates="assessment", uselist=False)

class CounselorAlert(Base):
    __tablename__ = "counselor_alerts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    risk_assessment_id = Column(Integer, ForeignKey("risk_assessments.id"), nullable=True)
    
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    status = Column(String(50), default="NEW")  # 'NEW', 'IN_REVIEW', 'CONTACTED', 'RESOLVED'
    alert_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    student = relationship("StudentProfile", back_populates="alerts")
    assessment = relationship("RiskAssessment", back_populates="alert")
    notes = relationship("CounselorNote", back_populates="alert", order_by="desc(CounselorNote.created_at)")

class CounselorNote(Base):
    __tablename__ = "counselor_notes"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("counselor_alerts.id"), nullable=False)
    counselor_name = Column(String(100), default="Campus Counseling Team")
    note_content = Column(Text, nullable=False)
    action_taken = Column(String(100), default="Initial Consultation Scheduled")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    alert = relationship("CounselorAlert", back_populates="notes")
