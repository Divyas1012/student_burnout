# MindPulse AI: Student Burnout & Mental Health Risk Prediction System

> **A Proactive Early-Warning Screening & Clinical Decision-Support Framework for Higher Education**

[![Python 3.12](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn%20%7C%20XGBoost-orange.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Project Overview

**MindPulse AI** is an AI-powered early-warning risk screening system that predicts student burnout and mental health risk. By synthesizing 10 multi-dimensional academic, lifestyle, and psychological indicators, it classifies risk into three actionable tiers:

- 🟢 **Low Risk (Normal)**: Balanced lifestyle and stress indicators.
- 🟡 **Moderate Risk (Warning)**: Early warning indicators detected; actionable self-care routines recommended.
- 🔴 **High Risk (Intervention)**: Significant risk trajectory; automated counselor notification and crisis support escalation.

The system is strictly designed with **human-in-the-loop oversight** and **ethical non-diagnostic safeguards**.

---

## 🚀 Key Features

1. **Multi-Dimensional Surveillance**:
   - **Academic**: GPA, study hours, academic workload perception, exam pressure, attendance.
   - **Lifestyle**: Sleep duration, sleep quality rating, screen time, exercise frequency, social support.
   - **Psychological**: Perceived stress, mood & daytime vitality, feeling overwhelmed.
2. **Machine Learning Benchmarking**:
   - Evaluates 4 candidate models: **Logistic Regression (Baseline)**, **Random Forest**, **XGBoost**, and **Support Vector Machine (SVM)**.
   - Automatic 5-Fold Stratified Cross-Validation with weighted F1 scoring.
3. **Explainable AI (XAI)**:
   - Identifies top contributing risk drivers (e.g. *"Severe Sleep Deprivation (< 5h/night)"*) and positive protective buffers.
4. **Contextual Recommendation Engine**:
   - Personalized evidence-based action cards (Sleep Hygiene, Pomodoro workload pacing, Digital detox, Movement).
5. **Dual-Role Web Dashboard**:
   - **Student Portal**: Interactive sliders, instant simulator preview, longitudinal trend graphs, lifestyle balance radar.
   - **Counselor / Admin Portal**: Cohort analytics, high-risk alert queue, status triage (New, In Review, Contacted, Resolved), clinical case notes, and exportable audit report.
6. **Ethical & Safety Safeguards**:
   - Prominent non-diagnostic disclaimer and 24/7 crisis hotline access (988 Lifeline, Tele-MANAS, Crisis Text Line 741741).

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, SQLAlchemy ORM, Pydantic v2
- **Machine Learning**: Scikit-Learn, XGBoost, Pandas, NumPy, Joblib
- **Database**: SQLite (default, zero-configuration) / PostgreSQL / MySQL
- **Frontend**: HTML5, Tailwind CSS, Chart.js, Modular ES6 JavaScript
- **Testing**: Python `unittest`, FastAPI `TestClient`

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- Git (optional)

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Run the Application
```bash
python run.py
```

The system will:
1. Check/train the ML models and generate benchmark metrics.
2. Initialize the SQLite database with demonstration student cohorts.
3. Boot the web server at:
   - **Web UI Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Running Automated Tests

Run the full automated test suite (Unit tests + Integration tests):

```bash
python -m unittest discover tests
```

Expected result:
```text
Ran 10 tests in ~5s
OK
```

---

## 📁 Project Directory Structure

```text
BURNOUT/
├── backend/
│   └── app/
│       ├── api/
│       │   ├── auth.py          # Demo user switching & profiles
│       │   ├── predict.py       # Real-time inference & model info
│       │   ├── surveys.py       # Check-in submissions & trend history
│       │   ├── counselor.py     # Counselor alerts, triage & notes
│       │   └── analytics.py     # Cohort KPI summaries
│       ├── database.py          # SQLAlchemy database engine
│       ├── models.py            # Relational database models
│       ├── schemas.py           # Pydantic validation schemas
│       ├── recommendations.py   # Contextual intervention engine
│       ├── seed_data.py         # Realistic demo student cohorts
│       └── main.py              # FastAPI app & static file router
├── frontend/
│   └── static/
│       ├── css/styles.css       # Custom styles, badges & print layout
│       ├── js/
│       │   ├── api.js           # REST API client
│       │   ├── charts.js        # Chart.js trend, radar & doughnut graphs
│       │   └── app.js           # Main UI controller & modal workflows
│       └── index.html           # Single-page dashboard application
├── ml/
│   ├── data/                    # Generated student dataset CSV
│   ├── saved_models/            # Trained .joblib model & metrics JSON
│   ├── dataset_generator.py     # Synthetic data generator (MBI-SS & PSS)
│   ├── train_models.py          # Model training & comparative benchmark
│   └── predictor.py             # Inference & feature attribution engine
├── docs/
│   ├── PROJECT_REPORT.md        # Academic final-year project report
│   └── PRESENTATION_GUIDE.md    # Viva & presentation slide-by-slide guide
├── tests/
│   ├── test_pipeline.py         # ML pipeline & model unit tests
│   └── test_api_endpoints.py    # FastAPI REST API integration tests
├── requirements.txt             # Python dependencies
├── run.py                       # Single-command application launcher
└── README.md                    # Project documentation
```

---

## 📊 Model Comparison Summary

| Model | Accuracy | Weighted F1 | 5-Fold CV F1 |
| :--- | :---: | :---: | :---: |
| **Logistic Regression (Champion)** | **88.75%** | **88.62%** | **86.60% (±2.27%)** |
| **Support Vector Machine (RBF)** | 86.50% | 86.29% | 86.40% (±1.11%) |
| **Random Forest (200 Trees)** | 85.50% | 85.14% | 83.88% (±1.79%) |
| **XGBoost Classifier** | 85.25% | 84.77% | 84.49% (±1.81%) |

---

## 🎓 Academic Documents for College Submission

- [Comprehensive Project Report](docs/PROJECT_REPORT.md)
- [Final Year Viva & Seminar Defense Guide](docs/PRESENTATION_GUIDE.md)

---

## 📜 License & Ethical Notice
This project is licensed under the MIT License. MindPulse AI is designed exclusively as an educational risk screening tool and does not provide medical or psychiatric diagnoses.
