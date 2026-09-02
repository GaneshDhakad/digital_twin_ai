import streamlit as st
import pandas as pd
import plotly.express as px
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
    st.rerun()

render_sidebar()

st.title("Study Activities & Academic Intelligence")
st.markdown("Log study sessions, focus metrics, and analyze subject performance.")

study_summary = APIClient.get("/study/summary") or {}

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Total Study Hours", f"{study_summary.get('total_hours', 0.0)} hrs", "Logged time")
with c2:
    render_metric_card("Avg Focus Score", f"{study_summary.get('avg_focus_score', 0.0)}/100", "Cognitive efficiency", is_violet=True)
with c3:
    render_metric_card("Task Completion", f"{study_summary.get('task_completion_rate', 0.0)}%", "Syllabus progress")
with c4:
    render_metric_card("Peak Hours", study_summary.get("peak_hours", "Morning"), "Optimal window", is_violet=True)

tab_log, tab_chart, tab_ai = st.tabs(["📝 LOG SESSION", "📊 SUBJECT BREAKDOWN", "🤖 AI EXAM SCORE PREDICTION"])

with tab_log:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<div class="hud-card">', unsafe_allow_html=True)
        st.subheader("Log Study Session")
        with st.form("study_form"):
            subject = st.text_input("Subject / Course", placeholder="e.g. Machine Learning / Data Structures")
            hours = st.number_input("Study Duration (Hours)", min_value=0.5, step=0.5, value=2.0)
            focus = st.slider("Focus Score (1-100)", min_value=1, max_value=100, value=85)
            completion = st.slider("Task Completion %", min_value=0, max_value=100, value=90)

            submit_study = st.form_submit_button("LOG STUDY SESSION")
            if submit_study:
                if not subject:
                    render_alert("Subject is required.", "warning")
                else:
                    payload = {
                        "subject": subject,
                        "study_hours": float(hours),
                        "performance_score": float(focus),
                        "task_completion_rate": float(completion),
                    }
                    res = APIClient.post("/study/activities", data=payload)
                    if isinstance(res, dict) and "activity_id" in res:
                        render_alert("Study session logged!", "success")
                        st.rerun()
                    else:
                        err = res.get("error", "Error logging study session") if isinstance(res, dict) else "Error"
                        render_alert(f"Failed to log: {err}", "error")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="hud-card-violet">', unsafe_allow_html=True)
        st.subheader("Recent Study Log")
        activities = APIClient.get("/study/activities") or []
        if activities:
            df_act = pd.DataFrame(activities)
            st.dataframe(df_act[["activity_id", "activity_date", "subject", "study_hours", "performance_score", "task_completion_rate"]], use_container_width=True)
        else:
            render_alert("No study activity logged yet.", "info")
        st.markdown('</div>', unsafe_allow_html=True)

with tab_chart:
    st.markdown('<div class="hud-card-violet">', unsafe_allow_html=True)
    st.subheader("Subject Time Allocation")
    subj_data = study_summary.get("subject_breakdown", {})
    if subj_data:
        df_subj = pd.DataFrame([{"Subject": k, "Hours": v} for k, v in subj_data.items()])
        fig = px.bar(df_subj, x="Subject", y="Hours", color="Hours", title="Hours by Subject", color_continuous_scale="Blues")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#0F172A")
        st.plotly_chart(fig, use_container_width=True)
    else:
        render_alert("No study activity logged yet.", "info")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AI EXAM SCORE PREDICTION TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_ai:
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.subheader("🎓 Academic Exam Score Predictor")
    st.markdown("Fill in your academic profile. The **GradientBoostingRegressor** model will predict your expected exam score.")

    with st.form("academic_predict_form"):
        st.markdown("#### 📚 Academic Profile")
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input("Age", min_value=13, max_value=35, value=21)
            gender = st.selectbox("Gender", ["Male", "Female"])
            major = st.selectbox("Major", ["Engineering", "Computer Science", "Arts", "Business", "Medicine", "Science", "Law", "Education"])
            semester = st.slider("Current Semester", 1, 10, 4)
            previous_gpa = st.number_input("Previous GPA (0–4)", min_value=0.0, max_value=4.0, value=3.2, step=0.1)
        with col2:
            study_hours_per_day = st.number_input("Study Hours/Day", 0.0, 24.0, 5.0, 0.5)
            attendance_percentage = st.slider("Attendance %", 0, 100, 88)
            sleep_hours = st.number_input("Sleep Hours/Night", 0.0, 24.0, 7.0, 0.5)
            exercise_frequency = st.slider("Exercise Days/Week", 0, 7, 3)
            mental_health_rating = st.slider("Mental Health (1–10)", 1, 10, 7)
        with col3:
            stress_level = st.slider("Stress Level (1–10)", 1, 10, 5)
            motivation_level = st.slider("Motivation (1–10)", 1, 10, 8)
            exam_anxiety_score = st.slider("Exam Anxiety (1–10)", 1, 10, 5)
            time_management_score = st.slider("Time Management (1–10)", 1, 10, 7)
            parental_support_level = st.slider("Parental Support (1–10)", 1, 10, 7)

        st.markdown("#### 🌐 Lifestyle & Environment")
        col4, col5 = st.columns(2)
        with col4:
            social_media_hours = st.number_input("Social Media Hours/Day", 0.0, 24.0, 2.0, 0.5)
            netflix_hours = st.number_input("Netflix Hours/Day", 0.0, 24.0, 1.5, 0.5)
            screen_time = st.number_input("Total Screen Time/Day", 0.0, 24.0, 4.0, 0.5)
            digital_distraction_hours = st.number_input("Digital Distraction Hours/Day", 0.0, 24.0, 2.0, 0.5)
            social_activity = st.slider("Social Activity (0–10)", 0, 10, 5)
            wellbeing_score = st.slider("Wellbeing Score (0–10)", 0, 10, 7)
            study_efficiency = st.slider("Study Efficiency (0–10)", 0, 10, 7)
        with col5:
            part_time_job = st.selectbox("Part-Time Job", ["No", "Yes"])
            diet_quality = st.selectbox("Diet Quality", ["Poor", "Average", "Good"])
            internet_quality = st.selectbox("Internet Quality", ["Poor", "Average", "Good", "Excellent"])
            parental_education_level = st.selectbox("Parental Education", ["High School", "Bachelor", "Master", "PhD"])
            extracurricular_participation = st.selectbox("Extracurricular", ["No", "Yes"])
            dropout_risk = st.selectbox("Dropout Risk", ["Low", "Medium", "High"])
            study_environment = st.selectbox("Study Environment", ["Home", "Library", "Cafe", "Dorm"])
            access_to_tutoring = st.selectbox("Access to Tutoring", ["No", "Yes"])
            family_income_range = st.selectbox("Family Income", ["Low", "Medium", "High"])
            learning_style = st.selectbox("Learning Style", ["Visual", "Auditory", "Reading", "Kinesthetic"])

        predict_btn = st.form_submit_button("🚀 PREDICT EXAM SCORE", use_container_width=True)

    if predict_btn:
        payload = {
            "age": float(age), "gender": gender, "major": major,
            "study_hours_per_day": study_hours_per_day, "social_media_hours": social_media_hours,
            "netflix_hours": netflix_hours, "part_time_job": part_time_job,
            "attendance_percentage": float(attendance_percentage), "sleep_hours": sleep_hours,
            "diet_quality": diet_quality, "exercise_frequency": float(exercise_frequency),
            "parental_education_level": parental_education_level, "internet_quality": internet_quality,
            "mental_health_rating": float(mental_health_rating),
            "extracurricular_participation": extracurricular_participation,
            "previous_gpa": previous_gpa, "semester": float(semester),
            "stress_level": float(stress_level), "dropout_risk": dropout_risk,
            "social_activity": float(social_activity), "screen_time": screen_time,
            "study_environment": study_environment, "access_to_tutoring": access_to_tutoring,
            "family_income_range": family_income_range,
            "parental_support_level": float(parental_support_level),
            "motivation_level": float(motivation_level),
            "exam_anxiety_score": float(exam_anxiety_score),
            "learning_style": learning_style,
            "time_management_score": float(time_management_score),
            "study_efficiency": float(study_efficiency),
            "digital_distraction_hours": digital_distraction_hours,
            "wellbeing_score": float(wellbeing_score),
        }
        with st.spinner("Running prediction model..."):
            result = APIClient.post("/ml/academic/predict", data=payload)

        if result and "prediction" in result:
            score = result["prediction"]
            grade = "A+" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "C" if score >= 60 else "D"
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1E40AF, #7C3AED); border-radius: 16px;
                     padding: 32px; text-align: center; margin: 16px 0;">
                    <div style="font-size: 14px; color: #BAE6FD; letter-spacing: 2px; margin-bottom: 8px;">
                        PREDICTED EXAM SCORE
                    </div>
                    <div style="font-size: 64px; font-weight: 900; color: white; line-height: 1;">
                        {score:.1f}
                    </div>
                    <div style="font-size: 28px; color: #FDE68A; font-weight: 700; margin-top: 4px;">
                        Grade: {grade}
                    </div>
                    <div style="font-size: 12px; color: #CBD5E1; margin-top: 12px;">
                        Model: {result.get('model_name', 'GradientBoostingRegressor')} &middot; v{result.get('model_version', '1.0')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            err = result.get("error", "Prediction failed") if isinstance(result, dict) else "Prediction failed"
            render_alert(f"❌ {err}", "error")

    st.markdown('</div>', unsafe_allow_html=True)
