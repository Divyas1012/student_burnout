"""
api/counselor.py
Counselor & Administrator Case Management Endpoints:
- High-Risk Early Warning Alerts
- Case note logging and workflow status updates
- Student cohort roster and individual drill-down
"""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import StudentProfile, CounselorAlert, CounselorNote, RiskAssessment, SurveyCheckIn
from ..schemas import (
    CounselorAlertResponse, AlertStatusUpdateSchema, CounselorNoteResponse,
    StudentDetailResponse, RiskAssessmentResponse, SurveyHistoryResponse, RecommendationItem
)
from ..recommendations import generate_recommendations

router = APIRouter(prefix="/api/counselor", tags=["Counselor Portal"])

@router.get("/alerts", response_model=List[CounselorAlertResponse])
def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status: NEW, IN_REVIEW, CONTACTED, RESOLVED"),
    db: Session = Depends(get_db)
):
    """Fetches high-risk alert queue for counselor triage."""
    query = db.query(CounselorAlert).order_by(CounselorAlert.created_at.desc())
    if status and status.upper() != "ALL":
        query = query.filter(CounselorAlert.status == status.upper())

    alerts = query.all()
    results = []
    for a in alerts:
        student = a.student
        user = student.user if student else None
        
        notes_list = [
            CounselorNoteResponse(
                id=n.id,
                counselor_name=n.counselor_name,
                note_content=n.note_content,
                action_taken=n.action_taken,
                created_at=n.created_at
            )
            for n in a.notes
        ]

        item = CounselorAlertResponse(
            id=a.id,
            student_id=a.student_id,
            student_name=user.name if user else "Unknown Student",
            student_id_number=student.student_id_number if student else "N/A",
            department=student.department if student else "General",
            risk_score=a.risk_score,
            risk_level=a.risk_level,
            status=a.status,
            alert_reason=a.alert_reason,
            created_at=a.created_at,
            updated_at=a.updated_at,
            notes_count=len(a.notes),
            recent_notes=notes_list
        )
        results.append(item)
    return results

@router.patch("/alerts/{alert_id}/status", response_model=CounselorAlertResponse)
def update_alert_status(alert_id: int, payload: AlertStatusUpdateSchema, db: Session = Depends(get_db)):
    """Updates the status of an alert (e.g. from NEW to CONTACTED or RESOLVED) and optionally records a note."""
    alert = db.query(CounselorAlert).filter(CounselorAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    valid_statuses = ["NEW", "IN_REVIEW", "CONTACTED", "RESOLVED"]
    if payload.status.upper() not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {valid_statuses}")

    alert.status = payload.status.upper()
    alert.updated_at = datetime.now(timezone.utc)

    # If note content provided, add a counselor note
    if payload.note_content and payload.note_content.strip():
        note = CounselorNote(
            alert_id=alert.id,
            counselor_name=payload.counselor_name or "Campus Counselor",
            note_content=payload.note_content.strip(),
            action_taken=payload.action_taken or f"Status set to {alert.status}",
            created_at=datetime.now(timezone.utc)
        )
        db.add(note)

    db.commit()
    db.refresh(alert)

    student = alert.student
    user = student.user if student else None

    notes_list = [
        CounselorNoteResponse(
            id=n.id,
            counselor_name=n.counselor_name,
            note_content=n.note_content,
            action_taken=n.action_taken,
            created_at=n.created_at
        )
        for n in alert.notes
    ]

    return CounselorAlertResponse(
        id=alert.id,
        student_id=alert.student_id,
        student_name=user.name if user else "Unknown Student",
        student_id_number=student.student_id_number if student else "N/A",
        department=student.department if student else "General",
        risk_score=alert.risk_score,
        risk_level=alert.risk_level,
        status=alert.status,
        alert_reason=alert.alert_reason,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        notes_count=len(alert.notes),
        recent_notes=notes_list
    )

@router.get("/students")
def list_students(
    risk_filter: Optional[str] = Query(None, description="Low, Moderate, High, or All"),
    search: Optional[str] = Query(None, description="Search by name or student ID"),
    db: Session = Depends(get_db)
):
    """Returns student cohort roster with their latest risk classification and vital indicators."""
    students = db.query(StudentProfile).all()
    results = []

    for s in students:
        user = s.user
        latest_survey = s.surveys[0] if s.surveys else None
        latest_assessment = latest_survey.assessment if (latest_survey and latest_survey.assessment) else None

        current_risk_level = latest_assessment.risk_level if latest_assessment else "Unassessed"
        current_risk_score = latest_assessment.risk_score if latest_assessment else 0.0
        current_risk_color = latest_assessment.risk_color if latest_assessment else "#9CA3AF"

        # Filters
        if risk_filter and risk_filter.upper() != "ALL":
            if current_risk_level.upper() != risk_filter.upper():
                continue

        if search:
            q = search.lower()
            name_match = user and (q in user.name.lower())
            id_match = q in s.student_id_number.lower()
            dept_match = q in s.department.lower()
            if not (name_match or id_match or dept_match):
                continue

        results.append({
            "id": s.id,
            "user_id": s.user_id,
            "name": user.name if user else "Student",
            "email": user.email if user else "",
            "student_id_number": s.student_id_number,
            "department": s.department,
            "year_of_study": s.year_of_study,
            "latest_risk_level": current_risk_level,
            "latest_risk_score": current_risk_score,
            "latest_risk_color": current_risk_color,
            "sleep_hours": latest_survey.sleep_hours_per_night if latest_survey else None,
            "stress_level": latest_survey.self_reported_stress if latest_survey else None,
            "last_check_in": latest_survey.created_at.strftime("%Y-%m-%d %H:%M") if latest_survey else "Never"
        })

    return results

@router.get("/students/{student_id}", response_model=StudentDetailResponse)
def get_student_detail(student_id: int, db: Session = Depends(get_db)):
    """Deep-dive profile of an individual student including historical trend and open alerts."""
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    user = student.user
    surveys = student.surveys
    latest_survey = surveys[0] if surveys else None
    latest_assessment = latest_survey.assessment if (latest_survey and latest_survey.assessment) else None

    # Format latest assessment
    latest_resp = None
    if latest_assessment and latest_survey:
        drivers = json.loads(latest_assessment.top_drivers) if latest_assessment.top_drivers else []
        protective = json.loads(latest_assessment.protective_factors) if latest_assessment.protective_factors else []
        
        survey_dict = {
            "sleep_hours_per_night": latest_survey.sleep_hours_per_night,
            "sleep_quality": latest_survey.sleep_quality,
            "self_reported_stress": latest_survey.self_reported_stress,
            "feeling_overwhelmed": latest_survey.feeling_overwhelmed,
            "screen_time_hours": latest_survey.screen_time_hours,
            "exercise_days": latest_survey.exercise_days,
            "social_support": latest_survey.social_support,
            "exam_pressure": latest_survey.exam_pressure,
            "academic_workload": latest_survey.academic_workload,
        }
        recs_raw = generate_recommendations(latest_assessment.risk_level, survey_dict)
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

        latest_resp = RiskAssessmentResponse(
            id=latest_assessment.id,
            risk_level=latest_assessment.risk_level,
            risk_score=latest_assessment.risk_score,
            risk_color=latest_assessment.risk_color,
            probabilities={},
            primary_drivers=drivers,
            protective_factors=protective,
            model_used=latest_assessment.model_version,
            recommendations=recs,
            created_at=latest_assessment.created_at
        )

    # Format history
    history_resp = [
        SurveyHistoryResponse(
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
        for s in reversed(surveys)
    ]

    # Format alerts
    alerts_resp = []
    for a in student.alerts:
        notes_list = [
            CounselorNoteResponse(
                id=n.id,
                counselor_name=n.counselor_name,
                note_content=n.note_content,
                action_taken=n.action_taken,
                created_at=n.created_at
            )
            for n in a.notes
        ]
        alerts_resp.append(CounselorAlertResponse(
            id=a.id,
            student_id=a.student_id,
            student_name=user.name if user else "Student",
            student_id_number=student.student_id_number,
            department=student.department,
            risk_score=a.risk_score,
            risk_level=a.risk_level,
            status=a.status,
            alert_reason=a.alert_reason,
            created_at=a.created_at,
            updated_at=a.updated_at,
            notes_count=len(a.notes),
            recent_notes=notes_list
        ))

    return StudentDetailResponse(
        id=student.id,
        name=user.name if user else "Student",
        email=user.email if user else "",
        student_id_number=student.student_id_number,
        department=student.department,
        year_of_study=student.year_of_study,
        latest_assessment=latest_resp,
        history=history_resp,
        alerts=alerts_resp
    )
