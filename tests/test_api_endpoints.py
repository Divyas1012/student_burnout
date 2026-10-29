"""
test_api_endpoints.py
Integration tests for FastAPI REST endpoints using TestClient.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.app.main import app

class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from backend.app.database import engine, Base, SessionLocal
        from backend.app.seed_data import seed_database_if_empty
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database_if_empty(db)
        finally:
            db.close()
        cls.client = TestClient(app)

    def test_01_root_and_auth(self):
        """Tests root UI endpoint and auth user listing."""
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)

        res_users = self.client.get("/api/auth/users")
        self.assertEqual(res_users.status_code, 200)
        users = res_users.json()
        self.assertGreater(len(users), 0)
        self.assertTrue(any(u["role"] == "student" for u in users))
        self.assertTrue(any(u["role"] == "counselor" for u in users))

    def test_02_model_info(self):
        """Tests model benchmark info retrieval."""
        res = self.client.get("/api/predict/model-info")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("best_model", data)
        self.assertIn("models_benchmark", data)
        self.assertIn("Logistic Regression", data["models_benchmark"])

    def test_03_evaluate_preview(self):
        """Tests instant risk calculation endpoint."""
        payload = {
            "gpa": 3.2,
            "study_hours_per_day": 5.5,
            "academic_workload": 6,
            "exam_pressure": 3,
            "attendance_percentage": 88.0,
            "sleep_hours_per_night": 7.0,
            "sleep_quality": 7,
            "screen_time_hours": 5.0,
            "exercise_days": 3,
            "social_support": 7,
            "mood_energy": 7,
            "self_reported_stress": 4,
            "feeling_overwhelmed": 3
        }
        res = self.client.post("/api/predict/evaluate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("risk_level", data)
        self.assertIn("risk_score", data)
        self.assertIn("recommendations", data)
        self.assertIsInstance(data["recommendations"], list)

    def test_04_submit_survey_and_history(self):
        """Tests survey check-in submission and subsequent history fetching."""
        # Get first student
        users = self.client.get("/api/auth/users").json()
        student = next(u for u in users if u["role"] == "student")
        student_id = student["student_id"]

        survey_payload = {
            "gpa": 3.1,
            "study_hours_per_day": 8.5,
            "academic_workload": 8,
            "exam_pressure": 6,
            "attendance_percentage": 78.0,
            "sleep_hours_per_night": 4.5,
            "sleep_quality": 3,
            "screen_time_hours": 8.5,
            "exercise_days": 1,
            "social_support": 3,
            "mood_energy": 3,
            "self_reported_stress": 8,
            "feeling_overwhelmed": 8,
            "notes": "Preparation for system defense"
        }
        res = self.client.post(f"/api/surveys/submit/{student_id}", json=survey_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("risk_level", data)

        # Check history
        res_hist = self.client.get(f"/api/surveys/history/{student_id}")
        self.assertEqual(res_hist.status_code, 200)
        history = res_hist.json()
        self.assertGreater(len(history), 0)

    def test_05_counselor_alerts_and_workflow(self):
        """Tests counselor alert retrieval and status updates."""
        res_alerts = self.client.get("/api/counselor/alerts?status=ALL")
        self.assertEqual(res_alerts.status_code, 200)
        alerts = res_alerts.json()
        self.assertIsInstance(alerts, list)

        if len(alerts) > 0:
            first_alert = alerts[0]
            alert_id = first_alert["id"]

            # Update status
            update_payload = {
                "status": "CONTACTED",
                "counselor_name": "Dr. Sarah Jenkins",
                "note_content": "Scheduled follow-up meeting via campus email.",
                "action_taken": "Consultation Scheduled"
            }
            res_update = self.client.patch(f"/api/counselor/alerts/{alert_id}/status", json=update_payload)
            self.assertEqual(res_update.status_code, 200)
            updated_data = res_update.json()
            self.assertEqual(updated_data["status"], "CONTACTED")
            self.assertGreater(updated_data["notes_count"], 0)

    def test_06_cohort_summary_and_roster(self):
        """Tests cohort metrics and roster search."""
        res_summary = self.client.get("/api/analytics/cohort-summary")
        self.assertEqual(res_summary.status_code, 200)
        summary = res_summary.json()
        self.assertIn("total_students", summary)
        self.assertIn("high_risk_count", summary)

        res_roster = self.client.get("/api/counselor/students?risk_filter=ALL")
        self.assertEqual(res_roster.status_code, 200)
        roster = res_roster.json()
        self.assertIsInstance(roster, list)
        self.assertGreater(len(roster), 0)

    def test_07_user_registration_student(self):
        """Tests student registration with profile and baseline assessment."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        payload = {
            "name": f"Jordan Lee {uid}",
            "email": f"jordan.lee_{uid}@student.university.edu",
            "password": "SecurePassword123!",
            "role": "student",
            "student_id_number": f"CS2026_{uid}",
            "department": "Artificial Intelligence & Robotics",
            "year_of_study": 3
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["name"], f"Jordan Lee {uid}")
        self.assertEqual(data["user"]["role"], "student")
        self.assertEqual(data["user"]["student_id_number"], f"CS2026_{uid}")

    def test_08_user_registration_counselor(self):
        """Tests counselor registration without student profile."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        payload = {
            "name": f"Dr. Marcus Brody {uid}",
            "email": f"m.brody_{uid}@university.edu",
            "password": "FacultyPassword456!",
            "role": "counselor"
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["name"], f"Dr. Marcus Brody {uid}")
        self.assertEqual(data["user"]["role"], "counselor")
        self.assertNotIn("student_id", data["user"])

    def test_09_user_registration_duplicate(self):
        """Tests that duplicate email registration returns 400."""
        payload = {
            "name": "Alex Duplicate",
            "email": "alex.chen@student.university.edu",
            "password": "password123",
            "role": "student"
        }
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already exists", res.json()["detail"])

    def test_10_user_login_success(self):
        """Tests successful user login with valid credentials."""
        payload = {
            "email": "alex.chen@student.university.edu",
            "password": "password123"
        }
        res = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "alex.chen@student.university.edu")

    def test_11_user_login_invalid_password(self):
        """Tests that incorrect password returns 401."""
        payload = {
            "email": "alex.chen@student.university.edu",
            "password": "WrongPassword999!"
        }
        res = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid email or password", res.json()["detail"])

if __name__ == "__main__":
    unittest.main()

