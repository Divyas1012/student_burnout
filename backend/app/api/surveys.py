"""
api/surveys.py
Endpoints for submitting well-being surveys, logging AI risk assessments,
auto-triggering counselor alerts on high-risk scores, and fetching survey history.
"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import StudentProfile, SurveyCheckIn, RiskAssessment, CounselorAlert
from ..schemas import (
    SurveyInputSchema, RiskAssessmentResponse, SurveyHistoryResponse, RecommendationItem
)
from ..recommendations import generate_recommendations
from ml.predictor import get_predictor

router = APIRouter(prefix="/api/surveys", tags=["Surveys & Assessments"])

@router.post("/submit/{student_id}", response_model=RiskAssessmentResponse)
def submit_survey(student_id: int, input_data: SurveyInputSchema, db: Session = Depends(get_db)):
    """
    Persists student check-in survey, executes AI model inference,
    stores the assessment record, and triggers an automated Counselor Alert if High Risk.
    """
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # 1. Create Survey record
    survey_record = SurveyCheckIn(
        student_id=student.id,
        gpa=input_data.gpa,
        study_hours_per_day=input_data.study_hours_per_day,
        academic_workload=input_data.academic_workload,
        exam_pressure=input_data.exam_pressure,
        attendance_percentage=input_data.attendance_percentage,
        sleep_hours_per_night=input_data.sleep_hours_per_night,
        sleep_quality=input_data.sleep_quality,
        screen_time_hours=input_data.screen_time_hours,
        exercise_days=input_data.exercise_days,
        social_support=input_data.social_support,
        mood_energy=input_data.mood_energy,
        self_reported_stress=input_data.self_reported_stress,
        feeling_overwhelmed=input_data.feeling_overwhelmed,
        notes=input_data.notes,
        created_at=datetime.now(timezone.utc)
    )
    db.add(survey_record)
    db.commit()
    db.refresh(survey_record)

    # 2. Run AI Model Inference
    predictor = get_predictor()
    pred_result = predictor.predict(input_data.model_dump())
    recs_raw = generate_recommendations(pred_result["risk_level"], input_data.model_dump())

    # 3. Create RiskAssessment record
    assessment_record = RiskAssessment(
        survey_id=survey_record.id,
        student_id=student.id,
        risk_score=pred_result["risk_score"],
        risk_level=pred_result["risk_level"],
        risk_color=pred_result["risk_color"],
        top_drivers=json.dumps(pred_result["primary_drivers"]),
        protective_factors=json.dumps(pred_result["protective_factors"]),
        model_version=pred_result["model_used"],
        created_at=datetime.now(timezone.utc)
    )
    db.add(assessment_record)
    db.commit()
    db.refresh(assessment_record)

    # 4. Automated Early Warning Alert for High Risk
    if pred_result["risk_level"] == "High":
        alert = CounselorAlert(
            student_id=student.id,
            risk_assessment_id=assessment_record.id,
            risk_score=pred_result["risk_score"],
            risk_level="High",
            status="NEW",
            alert_reason=f"Significant Burnout/Stress Risk ({pred_result['risk_score']}%) detected via check-in.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(alert)
        db.commit()

    recs = [
        RecommendationItem(
            title=r["title"],
            category=r["category"],
            priority=r["priority"],
            action_steps=r["action_steps"],
            icon=r["icon"]
        )
        for r in recs_raw
    ]

    return RiskAssessmentResponse(
        id=assessment_record.id,
        risk_level=pred_result["risk_level"],
        risk_score=pred_result["risk_score"],
        risk_color=pred_result["risk_color"],
        probabilities=pred_result["probabilities"],
        primary_drivers=pred_result["primary_drivers"],
        protective_factors=pred_result["protective_factors"],
        model_used=pred_result["model_used"],
        recommendations=recs,
        created_at=assessment_record.created_at
    )

@router.get("/history/{student_id}", response_model=list[SurveyHistoryResponse])
def get_survey_history(student_id: int, db: Session = Depends(get_db)):
    """Retrieves chronological survey check-ins and risk scores for trend graphs."""
    surveys = (
        db.query(SurveyCheckIn)
        .filter(SurveyCheckIn.student_id == student_id)
        .order_by(SurveyCheckIn.created_at.asc())
        .all()
    )

    history = []
    for s in surveys:
        item = SurveyHistoryResponse(
            id=s.id,
            created_at=s.created_at,
            gpa=s.gpa,
            study_hours_per_day=s.study_hours_per_day,
            sleep_hours_per_night=s.sleep_hours_per_night,
            self_reported_stress=s.self_reported_stress,
            risk_score=s.assessment.risk_score if s.assessment else None,
            risk_level=s.assessment.risk_level if s.assessment else None,
            risk_color=s.assessment.risk_color if s.assessment else None,
        )
        history.append(item)
    return history
