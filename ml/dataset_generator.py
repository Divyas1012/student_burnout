"""
dataset_generator.py
Synthetic Student Burnout and Mental Health Risk Dataset Generator

Grounded in psychometric research (Maslach Burnout Inventory - Student Survey [MBI-SS]
and Cohen's Perceived Stress Scale [PSS-10]). Generates realistic, multifaceted student
academic, lifestyle, and psychological metrics with realistic covariance and non-linear interactions.
"""

import os
import numpy as np
import pandas as pd

def generate_student_burnout_dataset(num_samples: int = 1600, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a synthetic cohort of students with academic, lifestyle, and psychological features.
    
    Returns:
        pd.DataFrame: Processed dataframe containing all features, continuous burnout index, and categorical risk level.
    """
    np.random.seed(random_seed)
    
    # 1. Academic Features
    # GPA centered around 7.8 on a 10-point scale with realistic bounds [3.0, 10.0]
    gpa = np.clip(np.random.normal(loc=7.8, scale=1.1, size=num_samples), 3.0, 10.0)
    
    # Study hours per day centered around 4.5h [1.0 to 12.0]
    study_hours = np.clip(np.random.normal(loc=4.5, scale=2.0, size=num_samples), 1.0, 12.0)
    
    # Academic workload perception (1-10)
    academic_workload = np.clip(np.round(np.random.normal(loc=6.0, scale=2.0, size=num_samples)), 1, 10)
    
    # Upcoming exams and major assignments in next 14 days (0 to 10)
    exam_pressure = np.clip(np.random.poisson(lam=3.5, size=num_samples), 0, 10)
    
    # Attendance percentage [45% to 100%]
    attendance = np.clip(np.random.beta(a=7, b=2, size=num_samples) * 100, 45.0, 100.0)
    
    # 2. Lifestyle Features
    # Sleep hours per night [3.0 to 10.0] - partially correlated with study hours & workload
    base_sleep = np.random.normal(loc=7.0, scale=1.3, size=num_samples)
    sleep_debt = (study_hours - 4.5) * 0.25 + (academic_workload - 5.0) * 0.15
    sleep_hours = np.clip(base_sleep - sleep_debt, 3.0, 10.0)
    
    # Sleep quality (1 to 10)
    sleep_quality = np.clip(np.round((sleep_hours / 10.0) * 8 + np.random.normal(0, 1.2, size=num_samples)), 1, 10)
    
    # Screen time hours (non-study + leisure devices) [2.0 to 14.0]
    screen_time = np.clip(np.random.normal(loc=6.0, scale=2.2, size=num_samples), 1.5, 14.0)
    
    # Physical activity / exercise days per week [0 to 7]
    exercise_days = np.clip(np.round(np.random.binomial(n=7, p=0.38, size=num_samples)), 0, 7)
    
    # Social activity / peer support rating (1 to 10)
    social_support = np.clip(np.round(np.random.normal(loc=6.2, scale=2.1, size=num_samples)), 1, 10)
    
    # 3. Psychological / Subjective Well-being
    # Mood and energy levels (1 to 10, 10 is vibrant/energized)
    mood_energy = np.clip(np.round(
        (sleep_quality * 0.35) + 
        (exercise_days * 0.4) + 
        (social_support * 0.25) - 
        (academic_workload * 0.2) + 
        np.random.normal(1.5, 1.3, size=num_samples)
    ), 1, 10)
    
    # Self-reported stress (1 to 10, 10 is extreme stress)
    stress_base = (
        (academic_workload * 0.28) + 
        (exam_pressure * 0.25) + 
        ((10 - sleep_hours) * 0.22) + 
        ((10 - social_support) * 0.15) - 
        (exercise_days * 0.2) + 
        np.random.normal(0.5, 1.1, size=num_samples)
    )
    self_reported_stress = np.clip(np.round(stress_base), 1, 10)
    
    # Feeling overwhelmed (1 to 10)
    feeling_overwhelmed = np.clip(np.round(
        0.55 * self_reported_stress + 
        0.25 * exam_pressure + 
        0.2 * (10 - mood_energy) + 
        np.random.normal(0, 0.9, size=num_samples)
    ), 1, 10)

    # 4. Burnout Risk Index Formulation (0 to 100 scale)
    # Combining exhaustion, cognitive overload, sleep deficits, and compensatory buffering
    exhaustion_component = (
        ((10.0 - sleep_hours) / 7.0) * 22.0 +
        ((10.0 - sleep_quality) / 9.0) * 12.0 +
        (screen_time / 14.0) * 10.0
    )
    
    workload_overload = (
        (academic_workload / 10.0) * 16.0 +
        (exam_pressure / 10.0) * 14.0 +
        (study_hours / 12.0) * 8.0
    )
    
    psychological_strain = (
        (self_reported_stress / 10.0) * 18.0 +
        (feeling_overwhelmed / 10.0) * 16.0 +
        ((10.0 - mood_energy) / 9.0) * 10.0
    )
    
    buffering_credits = (
        (exercise_days / 7.0) * 10.0 +
        (social_support / 10.0) * 12.0 +
        (attendance / 100.0) * 6.0
    )
    
    # Non-linear interaction: Severe sleep deprivation (<5h) combined with high stress multiplies risk
    vulnerability_interaction = np.where((sleep_hours < 5.0) & (self_reported_stress >= 7.0), 10.0, 0.0)
    
    raw_burnout_index = (
        exhaustion_component + 
        workload_overload + 
        psychological_strain - 
        buffering_credits + 
        vulnerability_interaction + 
        np.random.normal(0, 4.5, size=num_samples)
    )
    
    burnout_index = np.clip(np.round(raw_burnout_index, 1), 5.0, 98.0)
    
    # 5. Risk Classification:
    # 0 = Low (0-38%) -> Normal stress indicators
    # 1 = Moderate (39-68%) -> Early warning signs
    # 2 = High (69-100%) -> Significant risk requiring intervention/support
    risk_level = np.select(
        [burnout_index < 39.0, (burnout_index >= 39.0) & (burnout_index < 69.0), burnout_index >= 69.0],
        [0, 1, 2],
        default=1
    )
    
    risk_label = np.select(
        [risk_level == 0, risk_level == 1, risk_level == 2],
        ["Low", "Moderate", "High"],
        default="Moderate"
    )
    
    df = pd.DataFrame({
        "gpa": np.round(gpa, 2),
        "study_hours_per_day": np.round(study_hours, 1),
        "academic_workload": academic_workload.astype(int),
        "exam_pressure": exam_pressure.astype(int),
        "attendance_percentage": np.round(attendance, 1),
        "sleep_hours_per_night": np.round(sleep_hours, 1),
        "sleep_quality": sleep_quality.astype(int),
        "screen_time_hours": np.round(screen_time, 1),
        "exercise_days": exercise_days.astype(int),
        "social_support": social_support.astype(int),
        "mood_energy": mood_energy.astype(int),
        "self_reported_stress": self_reported_stress.astype(int),
        "feeling_overwhelmed": feeling_overwhelmed.astype(int),
        "burnout_index": burnout_index,
        "risk_level": risk_level,
        "risk_label": risk_label
    })
    
    return df

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "student_burnout_dataset.csv")
    
    print("Generating psychometrically aligned student burnout dataset...")
    df = generate_student_burnout_dataset(num_samples=2000, random_seed=42)
    df.to_csv(csv_path, index=False)
    
    print(f"Dataset successfully saved to: {csv_path}")
    print(f"Total records: {len(df)}")
    print("Class distribution:")
    print(df["risk_label"].value_counts(normalize=True).round(3) * 100)
    print("\nSummary Statistics:")
    print(df.describe().round(2).T[["mean", "std", "min", "50%", "max"]])
