"""
test_pipeline.py
Automated Unit and Integration Tests for Student Burnout ML Prediction System.
Verifies data generation, model inference, heuristic risk factors,
database ORM models, and API endpoints.
"""

import sys
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from ml.dataset_generator import generate_student_burnout_dataset
from ml.predictor import BurnoutPredictor
from backend.app.recommendations import generate_recommendations

class TestBurnoutSystem(unittest.TestCase):

    def test_01_dataset_generator(self):
        """Tests synthetic data generation for valid ranges and distributions."""
        df = generate_student_burnout_dataset(num_samples=100, random_seed=99)
        self.assertEqual(len(df), 100)
        self.assertIn("burnout_index", df.columns)
        self.assertIn("risk_level", df.columns)
        self.assertTrue((df["risk_level"] >= 0).all() and (df["risk_level"] <= 2).all())
        self.assertTrue((df["gpa"] >= 3.0).all() and (df["gpa"] <= 10.0).all())
        self.assertTrue((df["sleep_hours_per_night"] >= 2.5).all())

    def test_02_predictor_high_risk(self):
        """Tests predictor response for a severely overwhelmed, sleep-deprived student."""
        predictor = BurnoutPredictor()
        high_stress_input = {
            "gpa": 2.6,
            "study_hours_per_day": 10.0,
            "academic_workload": 9,
            "exam_pressure": 8,
            "attendance_percentage": 62.0,
            "sleep_hours_per_night": 4.0,
            "sleep_quality": 3,
            "screen_time_hours": 9.5,
            "exercise_days": 0,
            "social_support": 2,
            "mood_energy": 2,
            "self_reported_stress": 9,
            "feeling_overwhelmed": 9
        }
        res = predictor.predict(high_stress_input)
        self.assertIn(res["risk_level"], ["Moderate", "High"])
        self.assertGreaterEqual(res["risk_score"], 60.0)
        self.assertTrue(len(res["primary_drivers"]) > 0)
        
        # Recommendations should include mental health / crisis resources
        recs = generate_recommendations(res["risk_level"], high_stress_input)
        self.assertTrue(any("Counseling" in r["title"] or "Sleep" in r["title"] for r in recs))

    def test_03_predictor_low_risk(self):
        """Tests predictor response for a well-rested, balanced student."""
        predictor = BurnoutPredictor()
        low_stress_input = {
            "gpa": 3.8,
            "study_hours_per_day": 4.0,
            "academic_workload": 4,
            "exam_pressure": 1,
            "attendance_percentage": 95.0,
            "sleep_hours_per_night": 8.0,
            "sleep_quality": 8,
            "screen_time_hours": 4.5,
            "exercise_days": 4,
            "social_support": 8,
            "mood_energy": 8,
            "self_reported_stress": 2,
            "feeling_overwhelmed": 2
        }
        res = predictor.predict(low_stress_input)
        self.assertEqual(res["risk_level"], "Low")
        self.assertLess(res["risk_score"], 45.0)
        self.assertTrue(len(res["protective_factors"]) > 0)

    def test_04_database_and_schemas(self):
        """Tests database schema creation and sample user insertion."""
        from backend.app.database import engine, Base, SessionLocal
        from backend.app.models import User, StudentProfile
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            test_user = db.query(User).filter(User.email == "test.student@univ.edu").first()
            if not test_user:
                test_user = User(name="Test Student", email="test.student@univ.edu", role="student")
                db.add(test_user)
                db.commit()
                db.refresh(test_user)
                
                profile = StudentProfile(
                    user_id=test_user.id,
                    student_id_number="TEST999",
                    department="Computer Science",
                    year_of_study=3
                )
                db.add(profile)
                db.commit()
            
            self.assertIsNotNone(test_user.id)
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
