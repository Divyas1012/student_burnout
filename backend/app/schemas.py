"""
schemas.py
Pydantic Models for Input Validation, Data Serialization, and API responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SurveyInputSchema(BaseModel):
    # Academic
    gpa: float = Field(..., ge=0.0, le=10.0, description="Current Cumulative Grade Point Average (CGPA 0.0 - 10.0)")
    study_hours_per_day: float = Field(..., ge=0.0, le=18.0, description="Average daily study hours")
    academic_workload: int = Field(..., ge=1, le=10, description="Perceived course workload (1-10)")
    exam_pressure: int = Field(..., ge=0, le=10, description="Immediate exams or major deadlines (0-10)")
    attendance_percentage: float = Field(..., ge=0.0, le=100.0, description="Class attendance percentage")

    # Lifestyle
    sleep_hours_per_night: float = Field(..., ge=1.0, le=14.0, description="Average night sleep duration in hours")
    sleep_quality: int = Field(..., ge=1, le=10, description="Subjective sleep quality rating (1-10)")
    screen_time_hours: float = Field(..., ge=0.0, le=20.0, description="Daily leisure/total screen exposure")
    exercise_days: int = Field(..., ge=0, le=7, description="Days of moderate-to-vigorous physical exercise")
    social_support: int = Field(..., ge=1, le=10, description="Sense of peer and community support (1-10)")

    # Psychological
    mood_energy: int = Field(..., ge=1, le=10, description="Overall vitality and emotional mood (1-10)")
    self_reported_stress: int = Field(..., ge=1, le=10, description="Perceived stress level (1-10)")
    feeling_overwhelmed: int = Field(..., ge=1, le=10, description="Frequency of feeling overwhelmed (1-10)")

    notes: Optional[str] = Field(None, description="Optional personal reflection notes")

class RecommendationItem(BaseModel):
    title: str
    category: str  # 'Sleep', 'Academic', 'Digital Detox', 'Mental Health', 'Physical'
    priority: str  # 'High', 'Moderate', 'General'
    action_steps: List[str]
    icon: str

class RiskAssessmentResponse(BaseModel):
    id: Optional[int] = None
    risk_level: str
    risk_score: float
    risk_color: str
    probabilities: Dict[str, float]
    primary_drivers: List[str]
    protective_factors: List[str]
    model_used: str
    recommendations: List[RecommendationItem]
    created_at: Optional[datetime] = None

class SurveyHistoryResponse(BaseModel):
    id: int
    created_at: datetime
    gpa: float
    study_hours_per_day: float
    sleep_hours_per_night: float
    self_reported_stress: int
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_color: Optional[str] = None

class CounselorNoteResponse(BaseModel):
    id: int
    counselor_name: str
    note_content: str
    action_taken: str
    created_at: datetime

class CounselorAlertResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    student_id_number: str
    department: str
    risk_score: float
    risk_level: str
    status: str
    alert_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    notes_count: int
    recent_notes: List[CounselorNoteResponse] = []

class AlertStatusUpdateSchema(BaseModel):
    status: str = Field(..., description="'NEW', 'IN_REVIEW', 'CONTACTED', 'RESOLVED'")
    counselor_name: Optional[str] = "Campus Counselor"
    note_content: Optional[str] = None
    action_taken: Optional[str] = None

class CohortStatsResponse(BaseModel):
    total_students: int
    low_risk_count: int
    moderate_risk_count: int
    high_risk_count: int
    active_alerts: int
    average_stress: float
    average_sleep: float
    average_burnout_score: float

class StudentDetailResponse(BaseModel):
    id: int
    name: str
    email: str
    student_id_number: str
    department: str
    year_of_study: int
    latest_assessment: Optional[RiskAssessmentResponse] = None
    history: List[SurveyHistoryResponse] = []
    alerts: List[CounselorAlertResponse] = []

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field("student", description="'student' or 'counselor'")
    # Student specific fields
    student_id_number: Optional[str] = None
    department: Optional[str] = "Computer Science & Engineering"
    year_of_study: Optional[int] = 3

class UserLoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

