"""
run.py
Single entry-point runner for the Student Burnout & Mental Health Risk Prediction System.
Checks environment, verifies/trains ML models, initializes SQLite database with demo data,
and boots up the FastAPI application.
"""

import os
import sys
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

def bootstrap():
    print("=" * 70)
    print("   AI-BASED STUDENT BURNOUT & MENTAL HEALTH RISK PREDICTION SYSTEM")
    print("=" * 70)

    # 1. Verify ML Model
    model_path = os.path.join(BASE_DIR, "ml", "saved_models", "burnout_model.joblib")
    if not os.path.exists(model_path):
        print("\n[Step 1/3] Training & Benchmarking ML Models (Logistic Regression, RF, XGBoost, SVM)...")
        from ml.train_models import train_and_evaluate_all
        train_and_evaluate_all()
    else:
        print("\n[Step 1/3] Trained ML models verified.")

    # 2. Verify Database & Seed Data
    print("\n[Step 2/3] Checking database schema & demonstration accounts...")
    from backend.app.database import engine, Base, SessionLocal
    from backend.app.seed_data import seed_database_if_empty
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database_if_empty(db)
    finally:
        db.close()
    print("           Database ready.")

    # 3. Launch Web Server
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n[Step 3/3] Starting web server at http://{host}:{port}")
    print(f"           - Web UI Application: http://{host}:{port}")
    print(f"           - API Documentation:  http://{host}:{port}/docs")
    print("=" * 70 + "\n")

    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    bootstrap()
