"""
api/predict.py
FastAPI Router for Real-time AI Risk Inference and Model Introspection.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from ..schemas import SurveyInputSchema, RiskAssessmentResponse, RecommendationItem
from ..recommendations import generate_recommendations
from ml.predictor import get_predictor

router = APIRouter(prefix="/api/predict", tags=["AI Risk Prediction"])

@router.post("/evaluate", response_model=RiskAssessmentResponse)
def evaluate_risk(input_data: SurveyInputSchema):
    """
    Simulates or directly calculates student burnout risk on-the-fly without database commitment.
    Used for instant calculator and sensitivity exploration.
    """
    try:
        predictor = get_predictor()
        pred_result = predictor.predict(input_data.model_dump())
        recs_raw = generate_recommendations(pred_result["risk_level"], input_data.model_dump())
        
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
            risk_level=pred_result["risk_level"],
            risk_score=pred_result["risk_score"],
            risk_color=pred_result["risk_color"],
            probabilities=pred_result["probabilities"],
            primary_drivers=pred_result["primary_drivers"],
            protective_factors=pred_result["protective_factors"],
            model_used=pred_result["model_used"],
            recommendations=recs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction evaluation failed: {str(e)}")

@router.get("/model-info")
def get_model_benchmark():
    """
    Retrieves comparative metrics across Logistic Regression, Random Forest,
    XGBoost, and SVM, as well as feature importance rankings.
    """
    metrics_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml", "saved_models", "model_metrics.json")
    if not os.path.exists(metrics_path):
        # Auto-train if not yet created
        from ml.train_models import train_and_evaluate_all
        metrics_summary = train_and_evaluate_all()
        return metrics_summary

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
