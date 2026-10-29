"""
predictor.py
Inference & Explainable AI (XAI) Engine for Student Burnout Risk Prediction.
Loads champion model, performs real-time risk assessment, and computes key contributing risk drivers.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

FEATURE_COLS = [
    "gpa",
    "study_hours_per_day",
    "academic_workload",
    "exam_pressure",
    "attendance_percentage",
    "sleep_hours_per_night",
    "sleep_quality",
    "screen_time_hours",
    "exercise_days",
    "social_support",
    "mood_energy",
    "self_reported_stress",
    "feeling_overwhelmed"
]

class BurnoutPredictor:
    def __init__(self, model_path: str = None):
        if model_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, "saved_models", "burnout_model.joblib")
        
        self.model_path = model_path
        self.artifacts = None
        self._load_or_train()

    def _load_or_train(self):
        if not os.path.exists(self.model_path):
            print(f"Model file not found at {self.model_path}. Auto-training models...")
            from .train_models import train_and_evaluate_all
            train_and_evaluate_all()
        
        self.artifacts = joblib.load(self.model_path)
        self.model = self.artifacts["model"]
        self.scaler = self.artifacts.get("scaler")
        self.use_scaled = self.artifacts.get("use_scaled", False)
        self.model_name = self.artifacts.get("model_name", "ML Classifier")
        self.label_names = self.artifacts.get("label_names", ["Low", "Moderate", "High"])

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs burnout risk assessment on raw student input features.
        
        Returns:
            Dict containing:
                - risk_level: 'Low', 'Moderate', 'High'
                - risk_score: float (0.0 to 100.0)
                - probabilities: dict of class probabilities
                - risk_color: '#10B981' (green), '#F59E0B' (yellow), '#EF4444' (red)
                - primary_drivers: list of top contributing risk factors
                - protective_factors: list of positive buffering factors
                - model_used: name of model
        """
        # Validate & extract feature vector in exact order
        row_values = []
        for col in FEATURE_COLS:
            val = input_data.get(col)
            if val is None:
                raise ValueError(f"Missing required feature: {col}")
            row_values.append(float(val))

        X_input = pd.DataFrame([row_values], columns=FEATURE_COLS)

        if self.use_scaled and self.scaler is not None:
            X_model = self.scaler.transform(X_input)
        else:
            X_model = X_input

        # Predict class & probability distribution
        predicted_class_idx = int(self.model.predict(X_model)[0])
        
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X_model)[0]
        else:
            # Fallback if model doesn't support predict_proba
            probs = [0.0, 0.0, 0.0]
            probs[predicted_class_idx] = 1.0

        prob_dict = {
            self.label_names[i]: round(float(probs[i]), 4)
            for i in range(len(self.label_names))
        }

        # Expected risk score on 0-100 scale: weighted probability index
        # 0.0*p_low + 50.0*p_mod + 100.0*p_high
        weighted_score = (prob_dict.get("Low", 0.0) * 15.0) + \
                         (prob_dict.get("Moderate", 0.0) * 55.0) + \
                         (prob_dict.get("High", 0.0) * 95.0)
        risk_score = round(float(np.clip(weighted_score, 5.0, 99.0)), 1)

        risk_level = self.label_names[predicted_class_idx]

        # Dynamic risk color code
        color_map = {
            "Low": "#10B981",       # Emerald green
            "Moderate": "#F59E0B",  # Amber
            "High": "#EF4444"       # Rose red
        }
        risk_color = color_map.get(risk_level, "#6B7280")

        # Explainability: Identify Top Risk Drivers & Protective Buffers
        drivers, protective = self._extract_risk_drivers(input_data)

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "probabilities": prob_dict,
            "risk_color": risk_color,
            "primary_drivers": drivers,
            "protective_factors": protective,
            "model_used": self.model_name
        }

    def _extract_risk_drivers(self, data: Dict[str, Any]):
        """
        Domain-grounded heuristic factor attribution for immediate student & counselor transparency.
        """
        drivers = []
        protective = []

        sleep = float(data.get("sleep_hours_per_night", 7))
        sleep_q = int(data.get("sleep_quality", 5))
        stress = int(data.get("self_reported_stress", 5))
        overwhelmed = int(data.get("feeling_overwhelmed", 5))
        screen = float(data.get("screen_time_hours", 5))
        exercise = int(data.get("exercise_days", 2))
        social = int(data.get("social_support", 5))
        exam_pressure = int(data.get("exam_pressure", 3))
        workload = int(data.get("academic_workload", 5))
        attendance = float(data.get("attendance_percentage", 85))
        mood = int(data.get("mood_energy", 5))

        # Check negative drivers
        if sleep < 6.0:
            drivers.append(f"Severe Sleep Deprivation ({sleep}h/night; healthy target: 7-9h)")
        if sleep_q <= 4:
            drivers.append(f"Poor Sleep Quality ({sleep_q}/10 restorative rating)")
        if stress >= 7:
            drivers.append(f"Elevated Self-Perceived Stress Level ({stress}/10)")
        if overwhelmed >= 7:
            drivers.append(f"Cognitive & Emotional Overwhelm ({overwhelmed}/10)")
        if exam_pressure >= 7:
            drivers.append(f"High Immediate Exam & Deadline Pressure ({exam_pressure} active assessments)")
        if workload >= 8:
            drivers.append(f"High Academic Course Load Strain ({workload}/10)")
        if screen >= 8.5:
            drivers.append(f"Excessive Screen Time Fatigue ({screen}h daily)")
        if exercise == 0:
            drivers.append("Sedentary Routine (0 days physical activity/week)")
        if social <= 3:
            drivers.append(f"Low Social Support & Peer Connection ({social}/10)")
        if attendance < 70.0:
            drivers.append(f"Attendance Vulnerability ({attendance}% attended)")

        # Check positive protective buffers
        if sleep >= 7.5:
            protective.append(f"Sufficient Restful Sleep ({sleep}h/night)")
        if exercise >= 3:
            protective.append(f"Consistent Physical Activity ({exercise} days/week)")
        if social >= 7:
            protective.append(f"Strong Peer & Social Support Network ({social}/10)")
        if mood >= 7:
            protective.append(f"Positive Baseline Energy & Mood ({mood}/10)")
        if attendance >= 85.0:
            protective.append(f"High Academic Attendance & Class Engagement ({attendance}%)")

        if not drivers:
            drivers.append("All primary academic and lifestyle metrics within balanced ranges.")

        if not protective:
            protective.append("Opportunity to establish proactive exercise and sleep routines.")

        return drivers[:4], protective[:3]

# Global singleton helper
_predictor_instance = None

def get_predictor() -> BurnoutPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = BurnoutPredictor()
    return _predictor_instance
