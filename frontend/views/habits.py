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

st.title("Habit Tracking & Fitness Analytics")
st.markdown("Monitor daily discipline, habit streaks, and workout calories.")

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

col_habits, col_fitness = st.columns(2)

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
    
    st.markdown("#### At-Risk Habits")
    at_risk = habit_analytics.get("at_risk_habits", [])
    if at_risk:
        for ar in at_risk:
            render_alert(f"⚠️ <b>{ar}</b> completion rate is below 60% threshold!", "warning")
    else:
        render_alert("All habits are currently on track!", "success")

    st.markdown('</div>', unsafe_allow_html=True)

with col_fitness:
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
