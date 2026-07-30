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

st.markdown("### Recent Study Log")
activities = APIClient.get("/study/activities") or []
if activities:
    df_act = pd.DataFrame(activities)
    st.dataframe(df_act[["activity_id", "activity_date", "subject", "study_hours", "performance_score", "task_completion_rate"]], use_container_width=True)
