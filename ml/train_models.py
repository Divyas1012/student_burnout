"""
train_models.py
Trains and rigorously benchmarks 4 Machine Learning models for Student Burnout Risk Prediction:
1. Logistic Regression (Baseline)
2. Random Forest Classifier (Ensemble & Interpretable)
3. XGBoost Classifier (Gradient Boosting Tabular SOTA)
4. Support Vector Machine (Kernel Margin Classifier)

Saves the best-performing model pipeline and detailed comparison metrics.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    from .dataset_generator import generate_student_burnout_dataset
except ImportError:
    from dataset_generator import generate_student_burnout_dataset

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

TARGET_COL = "risk_level"
LABEL_NAMES = ["Low", "Moderate", "High"]

def train_and_evaluate_all():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    models_dir = os.path.join(base_dir, "saved_models")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    
    csv_path = os.path.join(data_dir, "student_burnout_dataset.csv")
    if not os.path.exists(csv_path):
        print("Dataset not found. Generating fresh dataset...")
        df = generate_student_burnout_dataset(num_samples=2000, random_seed=42)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    # Stratified Train-Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Preprocessing Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Models dictionary
    candidate_models = {
        "Logistic Regression": {
            "model": LogisticRegression(max_iter=1000, random_state=42),
            "use_scaled": True
        },
        "Random Forest": {
            "model": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
            "use_scaled": False
        },
        "Support Vector Machine": {
            "model": SVC(probability=True, kernel="rbf", C=1.5, random_state=42),
            "use_scaled": True
        }
    }

    if XGB_AVAILABLE:
        candidate_models["XGBoost"] = {
            "model": XGBClassifier(
                n_estimators=180,
                max_depth=5,
                learning_rate=0.08,
                eval_metric="mlogloss",
                random_state=42,
                n_jobs=-1
            ),
            "use_scaled": False
        }

    results = {}
    best_model_name = None
    best_f1 = -1.0
    best_artifacts = None
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print("\n" + "="*70)
    print("        STUDENT BURNOUT ML BENCHMARK & MODEL TRAINING")
    print("="*70)

    for name, config in candidate_models.items():
        clf = config["model"]
        use_scaled = config["use_scaled"]
        
        X_tr = X_train_scaled if use_scaled else X_train
        X_te = X_test_scaled if use_scaled else X_test

        # 5-Fold Cross Validation
        cv_scores = cross_val_score(clf, X_tr, y_train, cv=cv, scoring="f1_weighted")
        
        # Fit on training set
        clf.fit(X_tr, y_train)
        y_pred = clf.predict(X_te)
        
        # Performance Metrics
        acc = float(accuracy_score(y_test, y_pred))
        p_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
        r_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
        f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
        f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
        cm = confusion_matrix(y_test, y_pred).tolist()

        # Feature Importance (if applicable)
        feat_importance = None
        if hasattr(clf, "feature_importances_"):
            importances = clf.feature_importances_
            feat_importance = {
                feat: round(float(imp), 4)
                for feat, imp in sorted(zip(FEATURE_COLS, importances), key=lambda x: x[1], reverse=True)
            }
        elif hasattr(clf, "coef_"):
            coef_mean = np.mean(np.abs(clf.coef_), axis=0)
            feat_importance = {
                feat: round(float(imp), 4)
                for feat, imp in sorted(zip(FEATURE_COLS, coef_mean), key=lambda x: x[1], reverse=True)
            }

        results[name] = {
            "accuracy": round(acc, 4),
            "precision_macro": round(p_macro, 4),
            "recall_macro": round(r_macro, 4),
            "f1_macro": round(f1_macro, 4),
            "f1_weighted": round(f1_weighted, 4),
            "cv_f1_mean": round(float(np.mean(cv_scores)), 4),
            "cv_f1_std": round(float(np.std(cv_scores)), 4),
            "confusion_matrix": cm,
            "feature_importances": feat_importance
        }

        print(f"\nModel: {name}")
        print(f"  -> Accuracy:     {acc*100:.2f}%")
        print(f"  -> Macro F1:     {f1_macro*100:.2f}%")
        print(f"  -> Weighted F1:  {f1_weighted*100:.2f}%")
        print(f"  -> 5-Fold CV F1: {np.mean(cv_scores)*100:.2f}% (+/- {np.std(cv_scores)*100:.2f}%)")

        if f1_weighted > best_f1:
            best_f1 = f1_weighted
            best_model_name = name
            best_artifacts = {
                "model_name": name,
                "model": clf,
                "scaler": scaler,
                "use_scaled": use_scaled,
                "feature_cols": FEATURE_COLS,
                "label_names": LABEL_NAMES,
                "metrics": results[name]
            }

    print("\n" + "="*70)
    print(f"CHAMPION MODEL SELECTED: {best_model_name} (Weighted F1: {best_f1*100:.2f}%)")
    print("="*70)

    # Save best model
    model_save_path = os.path.join(models_dir, "burnout_model.joblib")
    joblib.dump(best_artifacts, model_save_path)
    print(f"Champion model saved to: {model_save_path}")

    # Save metrics JSON for frontend / reports / presentation
    metrics_summary = {
        "best_model": best_model_name,
        "feature_names": FEATURE_COLS,
        "class_labels": LABEL_NAMES,
        "models_benchmark": results
    }
    metrics_json_path = os.path.join(models_dir, "model_metrics.json")
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"Benchmark metrics saved to: {metrics_json_path}")

    return metrics_summary

if __name__ == "__main__":
    train_and_evaluate_all()
