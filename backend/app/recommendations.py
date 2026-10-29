"""
recommendations.py
Evidence-based AI Personalized Recommendation Engine.
Produces targeted, actionable lifestyle and academic coping interventions
tailored to specific risk drivers and burnout severity.
"""

from typing import Dict, Any, List

def generate_recommendations(risk_level: str, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates structured, tailored recommendations based on risk level and individual feature deficits.
    """
    recommendations = []

    sleep = float(input_data.get("sleep_hours_per_night", 7))
    sleep_q = int(input_data.get("sleep_quality", 5))
    stress = int(input_data.get("self_reported_stress", 5))
    overwhelmed = int(input_data.get("feeling_overwhelmed", 5))
    screen = float(input_data.get("screen_time_hours", 5))
    exercise = int(input_data.get("exercise_days", 2))
    social = int(input_data.get("social_support", 5))
    exam_pressure = int(input_data.get("exam_pressure", 3))
    workload = int(input_data.get("academic_workload", 5))

    # 1. Mandatory Intervention for High Risk
    if risk_level == "High":
        recommendations.append({
            "title": "Campus Human Counseling & Crisis Support",
            "category": "Mental Health",
            "priority": "High",
            "icon": "shield-alert",
            "action_steps": [
                "Schedule a confidential 1-on-1 session with a campus psychologist or academic counselor.",
                "Reach out to your faculty academic advisor to discuss deadline adjustments or course accommodations.",
                "If experiencing acute distress, call or text the 24/7 Mental Health Helpline: 988 (US) or 14416 (Tele-MANAS)."
            ]
        })

    # 2. Sleep Optimization
    if sleep < 6.5 or sleep_q <= 5:
        recommendations.append({
            "title": "Sleep Hygiene & Circadian Recovery",
            "category": "Sleep",
            "priority": "High" if sleep < 5.5 else "Moderate",
            "icon": "moon",
            "action_steps": [
                f"Aim to incrementally extend sleep by 45 minutes; current duration ({sleep}h) is below the 7-9h optimal cognitive recovery zone.",
                "Implement a 30-minute 'digital sunset' before bed: turn off blue-light devices to trigger natural melatonin release.",
                "Avoid caffeine and energy drinks after 2:00 PM to improve deep restorative sleep phases."
            ]
        })

    # 3. Academic Workload & Exam Stress Management
    if exam_pressure >= 6 or workload >= 7 or overwhelmed >= 7:
        recommendations.append({
            "title": "Cognitive Load Pacing & Exam Strategy",
            "category": "Academic",
            "priority": "High" if overwhelmed >= 8 else "Moderate",
            "icon": "book-open",
            "action_steps": [
                "Utilize the 25/5 Pomodoro Technique: 25 minutes of single-task focus followed by a 5-minute cognitive reset.",
                "Apply the Eisenhower Matrix: Break assignments into 'Urgent/Important' vs non-essential tasks to prevent paralysis.",
                "Attend professor or teaching assistant office hours early rather than cramming before deadlines."
            ]
        })

    # 4. Digital Screen Fatigue
    if screen >= 8.0:
        recommendations.append({
            "title": "Digital Detox & Visual Reset",
            "category": "Digital Detox",
            "priority": "Moderate",
            "icon": "smartphone",
            "action_steps": [
                f"Current non-study screen time ({screen}h) elevates neural exhaustion and eye strain.",
                "Apply the 20-20-20 rule: Every 20 minutes of screen work, look at an object 20 feet away for 20 seconds.",
                "Set screen time limits on non-essential social media apps during active study blocks."
            ]
        })

    # 5. Physical Activity & Movement
    if exercise <= 1:
        recommendations.append({
            "title": "Physical Movement & Stress Release",
            "category": "Physical",
            "priority": "Moderate",
            "icon": "activity",
            "action_steps": [
                "Engage in a 20-minute brisk walk across campus or light cardiovascular exercise at least 3 days a week.",
                "Physical movement lowers circulating cortisol (stress hormone) and promotes neuroplasticity for learning.",
                "Incorporate simple 5-minute desk stretching sessions between long study blocks."
            ]
        })

    # 6. Social & Emotional Buffering
    if social <= 4:
        recommendations.append({
            "title": "Peer Support & Social Buffering",
            "category": "Social",
            "priority": "Moderate",
            "icon": "users",
            "action_steps": [
                "Join a campus study group or peer mentorship circle to share course workload perspectives.",
                "Schedule one intentional offline social lunch or coffee with a friend or family member this week.",
                "Remember that academic stress is shared; talking openly reduces isolation and cognitive burden."
            ]
        })

    # 7. Low-Risk Maintenance Strategy
    if risk_level == "Low" and len(recommendations) == 0:
        recommendations.append({
            "title": "Resilience & Wellness Maintenance",
            "category": "General",
            "priority": "General",
            "icon": "smile",
            "action_steps": [
                "Maintain your balanced routine: your current sleep, activity, and workload habits are protective.",
                "Continue weekly well-being check-ins to catch early signs of exam-cycle fatigue before it escalates.",
                "Support peers who may be navigating difficult academic periods."
            ]
        })

    return recommendations[:4]
