"""
api/auth.py
Authentication, Registration, and User Session management.
Supports Sign Up, Login, and zero-friction role switching.
"""

import secrets
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, StudentProfile, SurveyCheckIn, RiskAssessment, hash_password, verify_password
from ..schemas import UserRegisterRequest, UserLoginRequest, AuthResponse
from ml.predictor import get_predictor
from ..recommendations import generate_recommendations

router = APIRouter(prefix="/api/auth", tags=["Authentication & Profiles"])

@router.post("/register", response_model=AuthResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new student or counselor account."""
    existing_user = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    role = req.role.strip().lower()
    if role not in ["student", "counselor"]:
        role = "student"

    new_user = User(
        name=req.name.strip(),
        email=req.email.strip().lower(),
        hashed_password=hash_password(req.password),
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    student_profile = None
    if role == "student":
        # Generate or format student ID number
        student_id_num = req.student_id_number.strip() if req.student_id_number else f"STU{new_user.id:04d}"
        
        # Check uniqueness of student ID number
        existing_profile = db.query(StudentProfile).filter(StudentProfile.student_id_number == student_id_num).first()
        if existing_profile:
            student_id_num = f"{student_id_num}_{new_user.id}"

        student_profile = StudentProfile(
            user_id=new_user.id,
            student_id_number=student_id_num,
            department=req.department.strip() if req.department else "Computer Science & Engineering",
            year_of_study=req.year_of_study or 3,
            avatar_color="#355f4d"
        )
        db.add(student_profile)
        db.commit()
        db.refresh(student_profile)

        # Note: No default/fake survey check-in created here.
        # Genuine student telemetry is captured when the user completes their initial assessment.

    token = secrets.token_urlsafe(32)
    user_payload = {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
    }
    if student_profile:
        user_payload["student_id"] = student_profile.id
        user_payload["student_id_number"] = student_profile.student_id_number
        user_payload["department"] = student_profile.department
        user_payload["year_of_study"] = student_profile.year_of_study

    return AuthResponse(access_token=token, token_type="bearer", user=user_payload)

@router.post("/login", response_model=AuthResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates a user by email and password."""
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Check password: support hashed password or fallback default demo password
    valid = False
    if user.hashed_password:
        valid = verify_password(req.password, user.hashed_password)
    else:
        # If legacy seeded user without hash, verify with default demo password
        if req.password == "password123":
            valid = True
            # Update user with hashed password
            user.hashed_password = hash_password(req.password)
            db.commit()

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = secrets.token_urlsafe(32)
    user_payload = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }
    if user.role == "student" and user.student_profile:
        user_payload["student_id"] = user.student_profile.id
        user_payload["student_id_number"] = user.student_profile.student_id_number
        user_payload["department"] = user.student_profile.department
        user_payload["year_of_study"] = user.student_profile.year_of_study

    return AuthResponse(access_token=token, token_type="bearer", user=user_payload)

@router.get("/users")
def list_demo_users(db: Session = Depends(get_db)):
    """Returns available demo accounts for 1-click role selection."""
    users = db.query(User).all()
    res = []
    for u in users:
        item = {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
        }
        if u.role == "student" and u.student_profile:
            item["student_id"] = u.student_profile.id
            item["student_id_number"] = u.student_profile.student_id_number
            item["department"] = u.student_profile.department
            item["year_of_study"] = u.student_profile.year_of_study
        res.append(item)
    return res

@router.get("/current-user/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Fetches details of the selected user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at
    }
    if user.role == "student" and user.student_profile:
        data["student_id"] = user.student_profile.id
        data["student_id_number"] = user.student_profile.student_id_number
        data["department"] = user.student_profile.department
        data["year_of_study"] = user.student_profile.year_of_study
    return data
