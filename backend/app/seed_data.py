"""
seed_data.py
Populates realistic demo accounts, student cohorts, multi-week check-ins,
and counselor alert case histories for immediate viva/project demonstration.
"""

import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from .models import User, StudentProfile, SurveyCheckIn, RiskAssessment, CounselorAlert, CounselorNote, hash_password
from ml.predictor import get_predictor

def seed_database_if_empty(db: Session):
    counselor = db.query(User).filter(User.role == "counselor").first()
    if counselor:
        return  # Database already seeded with demo cohort

    print("Seeding initial demo cohort and counselor records...")
    predictor = get_predictor()

    # 1. Create Counselor User
    counselor_user = User(
        name="Dr. Sarah Jenkins",
        email="s.jenkins@university.edu",
        hashed_password=hash_password("password123"),
        role="counselor"
    )
    db.add(counselor_user)
    db.commit()

    # 2. Student Cohort Specifications
    students_data = [
        {
            "name": "Alex Chen",
            "email": "alex.chen@student.university.edu",
            "student_id_number": "CS2024098",
            "department": "Computer Science & AI",
            "year_of_study": 3,
            "avatar_color": "#3B82F6",
            # Trajectory: starts well, deteriorates towards finals
            "surveys": [
                {"days_ago": 21, "gpa": 9.1, "study": 5.0, "workload": 5, "exams": 1, "att": 95.0, "sleep": 7.5, "sleep_q": 8, "screen": 5.0, "ex": 4, "soc": 8, "mood": 8, "stress": 3, "overwhelmed": 2},
                {"days_ago": 14, "gpa": 8.9, "study": 6.5, "workload": 6, "exams": 3, "att": 90.0, "sleep": 6.2, "sleep_q": 6, "screen": 6.5, "ex": 2, "soc": 6, "mood": 6, "stress": 6, "overwhelmed": 5},
                {"days_ago": 7,  "gpa": 8.6, "study": 8.0, "workload": 8, "exams": 5, "att": 85.0, "sleep": 5.0, "sleep_q": 4, "screen": 8.0, "ex": 1, "soc": 4, "mood": 4, "stress": 8, "overwhelmed": 7},
                {"days_ago": 1,  "gpa": 8.4, "study": 9.5, "workload": 9, "exams": 7, "att": 76.0, "sleep": 4.5, "sleep_q": 3, "screen": 9.5, "ex": 0, "soc": 2, "mood": 3, "stress": 9, "overwhelmed": 9}
            ]
        },
        {
            "name": "Priya Sharma",
            "email": "p.sharma@student.university.edu",
            "student_id_number": "DS2024142",
            "department": "Data Science & Analytics",
            "year_of_study": 2,
            "avatar_color": "#EC4899",
            "surveys": [
                {"days_ago": 10, "gpa": 9.5, "study": 4.5, "workload": 4, "exams": 1, "att": 98.0, "sleep": 8.0, "sleep_q": 9, "screen": 4.0, "ex": 5, "soc": 8, "mood": 9, "stress": 2, "overwhelmed": 2},
                {"days_ago": 2,  "gpa": 9.6, "study": 4.0, "workload": 5, "exams": 2, "att": 96.0, "sleep": 7.8, "sleep_q": 8, "screen": 4.5, "ex": 4, "soc": 8, "mood": 8, "stress": 3, "overwhelmed": 2}
            ]
        },
        {
            "name": "Marcus Vance",
            "email": "m.vance@student.university.edu",
            "student_id_number": "EE2023055",
            "department": "Electrical Engineering",
            "year_of_study": 4,
            "avatar_color": "#F59E0B",
            "surveys": [
                {"days_ago": 12, "gpa": 7.1, "study": 7.0, "workload": 8, "exams": 4, "att": 72.0, "sleep": 5.2, "sleep_q": 5, "screen": 7.5, "ex": 1, "soc": 5, "mood": 5, "stress": 7, "overwhelmed": 6},
                {"days_ago": 3,  "gpa": 7.0, "study": 8.5, "workload": 9, "exams": 6, "att": 68.0, "sleep": 4.2, "sleep_q": 3, "screen": 8.5, "ex": 0, "soc": 3, "mood": 3, "stress": 9, "overwhelmed": 8}
            ]
        },
        {
            "name": "Sophia Rodriguez",
            "email": "s.rodriguez@student.university.edu",
            "student_id_number": "ME2024019",
            "department": "Mechanical Engineering",
            "year_of_study": 3,
            "avatar_color": "#10B981",
            "surveys": [
                {"days_ago": 8, "gpa": 8.1, "study": 5.5, "workload": 6, "exams": 2, "att": 88.0, "sleep": 6.8, "sleep_q": 6, "screen": 5.5, "ex": 3, "soc": 6, "mood": 6, "stress": 5, "overwhelmed": 4},
                {"days_ago": 2, "gpa": 8.1, "study": 6.0, "workload": 6, "exams": 3, "att": 86.0, "sleep": 6.5, "sleep_q": 6, "screen": 6.0, "ex": 2, "soc": 6, "mood": 6, "stress": 5, "overwhelmed": 5}
            ]
        },
        {
            "name": "Devin Wright",
            "email": "d.wright@student.university.edu",
            "student_id_number": "BA2024310",
            "department": "Business Analytics",
            "year_of_study": 1,
            "avatar_color": "#8B5CF6",
            "surveys": [
                {"days_ago": 5, "gpa": 7.6, "study": 4.0, "workload": 5, "exams": 1, "att": 92.0, "sleep": 7.0, "sleep_q": 7, "screen": 5.0, "ex": 3, "soc": 7, "mood": 7, "stress": 4, "overwhelmed": 3}
            ]
        },
        {
            "name": "Kavita Rao",
            "email": "k.rao@student.university.edu",
            "student_id_number": "CS2023214",
            "department": "Computer Science & AI",
            "year_of_study": 4,
            "avatar_color": "#EF4444",
            "surveys": [
                {"days_ago": 4, "gpa": 6.5, "study": 9.0, "workload": 9, "exams": 8, "att": 60.0, "sleep": 3.8, "sleep_q": 2, "screen": 10.0, "ex": 0, "soc": 2, "mood": 2, "stress": 10, "overwhelmed": 10}
            ]
        }
    ]

    for s_info in students_data:
        user = User(
            name=s_info["name"],
            email=s_info["email"],
            hashed_password=hash_password("password123"),
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = StudentProfile(
            user_id=user.id,
            student_id_number=s_info["student_id_number"],
            department=s_info["department"],
            year_of_study=s_info["year_of_study"],
            avatar_color=s_info["avatar_color"]
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        # Populate surveys
        for sur in s_info["surveys"]:
            survey_time = datetime.now(timezone.utc) - timedelta(days=sur["days_ago"])
            
            sc = SurveyCheckIn(
                student_id=profile.id,
                gpa=sur["gpa"],
                study_hours_per_day=sur["study"],
                academic_workload=sur["workload"],
                exam_pressure=sur["exams"],
                attendance_percentage=sur["att"],
                sleep_hours_per_night=sur["sleep"],
                sleep_quality=sur["sleep_q"],
                screen_time_hours=sur["screen"],
                exercise_days=sur["ex"],
                social_support=sur["soc"],
                mood_energy=sur["mood"],
                self_reported_stress=sur["stress"],
                feeling_overwhelmed=sur["overwhelmed"],
                created_at=survey_time
            )
            db.add(sc)
            db.commit()
            db.refresh(sc)

            # Predict & assess
            features = {
                "gpa": sur["gpa"],
                "study_hours_per_day": sur["study"],
                "academic_workload": sur["workload"],
                "exam_pressure": sur["exams"],
                "attendance_percentage": sur["att"],
                "sleep_hours_per_night": sur["sleep"],
                "sleep_quality": sur["sleep_q"],
                "screen_time_hours": sur["screen"],
                "exercise_days": sur["ex"],
                "social_support": sur["soc"],
                "mood_energy": sur["mood"],
                "self_reported_stress": sur["stress"],
                "feeling_overwhelmed": sur["overwhelmed"]
            }
            pred_res = predictor.predict(features)

            ra = RiskAssessment(
                survey_id=sc.id,
                student_id=profile.id,
                risk_score=pred_res["risk_score"],
                risk_level=pred_res["risk_level"],
                risk_color=pred_res["risk_color"],
                top_drivers=json.dumps(pred_res["primary_drivers"]),
                protective_factors=json.dumps(pred_res["protective_factors"]),
                model_version=pred_res["model_used"],
                created_at=survey_time
            )
            db.add(ra)
            db.commit()
            db.refresh(ra)

            # If high risk and most recent check-in, create an alert
            if pred_res["risk_level"] == "High" and sur["days_ago"] <= 4:
                alert = CounselorAlert(
                    student_id=profile.id,
                    risk_assessment_id=ra.id,
                    risk_score=pred_res["risk_score"],
                    risk_level="High",
                    status="IN_REVIEW" if s_info["name"] == "Alex Chen" else "NEW",
                    alert_reason=f"Significant risk index ({pred_res['risk_score']}%) with critical sleep and stress signals.",
                    created_at=survey_time,
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)

                if s_info["name"] == "Alex Chen":
                    note = CounselorNote(
                        alert_id=alert.id,
                        counselor_name="Dr. Sarah Jenkins",
                        note_content="Reviewed check-in history. Alex is exhibiting compounding sleep debt and deadline anxiety. Sent personal outreach email to schedule a 30-minute academic de-escalation session.",
                        action_taken="Outreach Email Sent & Meeting Requested",
                        created_at=datetime.now(timezone.utc) - timedelta(hours=6)
                    )
                    db.add(note)
                    db.commit()

    print("Sample cohort and case notes successfully populated.")
