import streamlit as st
import pandas as pd
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme
from frontend.utils.api_client import APIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.metrics_card import render_metric_card
from frontend.components.alerts import render_alert

apply_stitch_theme()

if not st.session_state.get("authenticated"):
    st.warning("Authentication required. Redirecting to login...")
    st.switch_page("views/login.py")

render_sidebar()

st.title("Habit Tracking & Lifestyle Analytics")
st.markdown("Monitor daily discipline, habit streaks, workout sessions, and get AI-powered sleep risk analysis.")

habit_analytics = APIClient.get("/habits/analytics") or {}
fitness_summary = APIClient.get("/fitness/summary") or {}

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Habit Streak", f"{habit_analytics.get('current_streak', 0)} Days", "Consecutive days")
with c2:
    render_metric_card("Completion Rate", f"{habit_analytics.get('overall_completion_rate', 0.0)}%", "Threshold ≥ 60%", is_violet=True)
with c3:
    render_metric_card("Workouts / Wk", str(fitness_summary.get('weekly_activity_count', 0)), "Weekly frequency")
with c4:
    render_metric_card("Total Calories", f"{fitness_summary.get('total_calories', 0.0):,.0f} kcal", "Burned", is_violet=True)

tab_habits, tab_workout, tab_ai = st.tabs(["📋 HABIT LOG", "🏋️ WORKOUT LOG", "🤖 AI SLEEP RISK PREDICTION"])

with tab_habits:
    col_habits, col_at_risk = st.columns(2)

    with col_habits:
        st.markdown('<div class="hud-card">', unsafe_allow_html=True)
        st.subheader("Log Habit Status")
        with st.form("habit_form"):
            h_name = st.text_input("Habit Name", placeholder="e.g. Daily Meditation / 30m Reading")
            h_status = st.selectbox("Status", ["completed", "missed"])
            h_impact = st.selectbox("Impact Level", ["High", "Medium", "Low"])

            sub_h = st.form_submit_button("LOG HABIT ENTRY")
            if sub_h:
                if not h_name:
                    render_alert("Habit name is required.", "warning")
                else:
                    payload = {"habit_name": h_name, "status": h_status, "impact_level": h_impact}
                    res = APIClient.post("/habits", data=payload)
                    if isinstance(res, dict) and "habit_id" in res:
                        render_alert("Habit status logged!", "success")
                        st.rerun()
                    else:
                        render_alert("Failed to log habit.", "error")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_at_risk:
        st.markdown('<div class="hud-card-violet">', unsafe_allow_html=True)
        st.subheader("At-Risk Habits")
        at_risk = habit_analytics.get("at_risk_habits", [])
        if at_risk:
            st.markdown("##### ⚠️ Habits needing attention")
            for ar in at_risk:
                st.markdown(
                    f'<div style="background-color: #FEF2F2; color: #991B1B; padding: 12px; border-radius: 8px; border-left: 4px solid #EF4444; margin-bottom: 8px; font-weight: 500;">'
                    f'{ar} completion rate is below the 60% target.'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            render_alert("All habits are currently on track!", "success")
        st.markdown('</div>', unsafe_allow_html=True)

with tab_workout:
    st.markdown('<div class="hud-card-violet">', unsafe_allow_html=True)
    st.subheader("Log Workout Session")
    with st.form("fitness_form"):
        f_type = st.selectbox("Activity Type", ["Running", "Gym Workout", "Yoga", "Cycling", "Swimming", "Walking"])
        f_dur = st.number_input("Duration (Minutes)", min_value=5.0, step=5.0, value=45.0)
        f_cal = st.number_input("Calories Burned (kcal)", min_value=0.0, step=10.0, value=350.0)

        sub_f = st.form_submit_button("LOG WORKOUT")
        if sub_f:
            payload = {"activity_type": f_type, "duration": float(f_dur), "calories_burned": float(f_cal)}
            res = APIClient.post("/fitness/activities", data=payload)
            if isinstance(res, dict) and "fitness_id" in res:
                render_alert("Workout logged!", "success")
                st.rerun()
            else:
                render_alert("Failed to log workout.", "error")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Recent Fitness Activity Log")
    fitness_list = APIClient.get("/fitness/activities") or []
    if fitness_list:
        st.dataframe(pd.DataFrame(fitness_list)[["fitness_id", "activity_date", "activity_type", "duration", "calories_burned"]], use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# AI SLEEP DISORDER PREDICTION TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_ai:
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.subheader("😴 Sleep Disorder Risk Predictor")
    st.markdown(
        "The **GradientBoostingClassifier** lifestyle model analyses your health profile and classifies your "
        "sleep-disorder risk into one of three categories: **Normal**, **Insomnia**, or **Sleep Apnea**. "
        "This is a **model prediction**, not a clinical diagnosis. Consult a healthcare professional for medical advice."
    )

    with st.form("lifestyle_predict_form"):
        st.markdown("#### 👤 Personal Profile")
        col1, col2 = st.columns(2)
        with col1:
            ls_gender = st.selectbox("Gender", ["Male", "Female"])
            ls_age = st.number_input("Age", min_value=18, max_value=100, value=30)
            ls_occupation = st.selectbox("Occupation", [
                "Software Engineer", "Doctor", "Teacher", "Nurse", "Engineer",
                "Accountant", "Manager", "Salesperson", "Student", "Other"
            ])
            ls_bmi_category = st.selectbox("BMI Category", ["Underweight", "Normal", "Overweight", "Obese"])
            ls_blood_pressure = st.text_input("Blood Pressure", value="120/80", help="Format: systolic/diastolic e.g. 120/80")
        with col2:
            ls_heart_rate = st.number_input("Resting Heart Rate (BPM)", min_value=40.0, max_value=200.0, value=75.0)
            ls_daily_steps = st.number_input("Daily Steps", min_value=0.0, max_value=50000.0, value=6000.0, step=500.0)

        st.markdown("#### 😴 Sleep & Wellness")
        col3, col4 = st.columns(2)
        with col3:
            ls_sleep_hours = st.number_input("Sleep Hours/Night", min_value=0.0, max_value=24.0, value=6.5, step=0.5)
            ls_sleep_quality = st.slider("Sleep Quality (1–10)", 1, 10, 6)
            ls_stress_level = st.slider("Stress Level (1–10)", 1, 10, 7)
        with col4:
            ls_physical_activity_level = st.slider("Physical Activity Level (0–100)", 0, 100, 45)
            ls_activity_sleep_balance = st.slider("Activity-Sleep Balance (0–100)", 0, 100, 55)
            ls_lifestyle_risk_score = st.slider("Lifestyle Risk Score (0–100)", 0, 100, 42)

        ls_predict_btn = st.form_submit_button("🔍 ANALYSE SLEEP RISK", use_container_width=True)

    if ls_predict_btn:
        payload = {
            "gender": ls_gender, "age": float(ls_age), "occupation": ls_occupation,
            "sleep_hours": ls_sleep_hours, "sleep_quality": float(ls_sleep_quality),
            "physical_activity_level": float(ls_physical_activity_level),
            "stress_level": float(ls_stress_level), "bmi_category": ls_bmi_category,
            "blood_pressure": ls_blood_pressure, "heart_rate": ls_heart_rate,
            "daily_steps": ls_daily_steps,
            "activity_sleep_balance": float(ls_activity_sleep_balance),
            "lifestyle_risk_score": float(ls_lifestyle_risk_score),
        }
        with st.spinner("Analysing lifestyle profile..."):
            result = APIClient.post("/ml/lifestyle/predict", data=payload)

        if result and "prediction" in result:
            disorder = result["prediction"]  # One of: Normal | Insomnia | Sleep Apnea

            # Determine display properties for each 3-class outcome
            if disorder == "Normal":
                color = "#059669"
                icon = "✅"
                label = "Normal — No Sleep Disorder Detected"
            elif disorder == "Insomnia":
                color = "#D97706"
                icon = "⚠️"
                label = "Insomnia"
            elif disorder == "Sleep Apnea":
                color = "#DC2626"
                icon = "🚨"
                label = "Sleep Apnea"
            else:
                # Graceful fallback for any unexpected value
                color = "#6B7280"
                icon = "ℹ️"
                label = disorder

            # Advice per classification — these are lifestyle suggestions, not medical advice
            advice_map = {
                "Normal": (
                    "Great! The model classifies your profile as Normal. "
                    "Keep maintaining your current sleep routine and lifestyle habits."
                ),
                "Insomnia": (
                    "The model classifies your profile as consistent with an insomnia-related pattern. "
                    "Consider a consistent sleep schedule, reducing screen time before bed, and limiting "
                    "caffeine after 2 PM. If symptoms persist, consult a healthcare professional."
                ),
                "Sleep Apnea": (
                    "The model classifies your profile as consistent with a sleep apnea-related pattern. "
                    "Consider consulting a physician for a sleep study. Weight management and "
                    "positional therapy may help. This is a model prediction, not a diagnosis."
                ),
            }
            advice = advice_map.get(
                disorder,
                "Please consult a healthcare professional for personalised advice."
            )

            model_name = result.get("model_name", "Lifestyle Model")
            model_version = result.get("model_version", "")
            version_str = f" v{model_version}" if model_version else ""

            st.markdown(f"""
                <div style="background: {color}15; border: 2px solid {color}40; border-radius: 16px;
                     padding: 28px; text-align: center; margin: 16px 0;">
                    <div style="font-size: 40px; margin-bottom: 8px;">{icon}</div>
                    <div style="font-size: 14px; color: #64748B; letter-spacing: 2px; margin-bottom: 6px;">
                        SLEEP-DISORDER CLASSIFICATION — MODEL PREDICTION
                    </div>
                    <div style="font-size: 36px; font-weight: 900; color: {color};">{label}</div>
                    <div style="font-size: 12px; color: #94A3B8; margin-top: 4px;">
                        {model_name}{version_str} prediction &nbsp;|&nbsp; Not a clinical diagnosis
                    </div>
                    <div style="font-size: 14px; color: #475569; margin-top: 16px; max-width: 520px;
                         margin-left: auto; margin-right: auto; line-height: 1.6;">
                        <b>Main contributing factors based on your profile:</b><br>
                        • Sleep Duration: {ls_sleep_hours} hrs/night<br>
                        • Physical Activity Level: {ls_physical_activity_level}/100<br>
                        • Stress Level: {ls_stress_level}/10<br><br>
                        <i>{advice}</i>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            err = result.get("error", "Prediction failed") if isinstance(result, dict) else "Prediction failed"
            render_alert(f"❌ {err}", "error")

    st.markdown('</div>', unsafe_allow_html=True)
