import streamlit as st
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

st.title("User Profile & Behavioral Parameters")
st.markdown("Manage your operator profile demographics and view Digital Twin state indicators.")

profile = APIClient.get("/users/profile") or {}

col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.subheader("Edit Profile Information")
    with st.form("edit_profile_form"):
        p_name = st.text_input("Full Name", value=profile.get("name", ""))
        p_email = st.text_input("Email Address", value=profile.get("email", ""), disabled=True)
        p_age = st.number_input("Age", min_value=13, max_value=100, value=profile.get("age") or 22)
        p_occ = st.text_input("Occupation", value=profile.get("occupation", ""))
        
        save_btn = st.form_submit_button("SAVE PROFILE CHANGES")
        if save_btn:
            res = APIClient.put("/users/profile", data={"name": p_name, "age": int(p_age), "occupation": p_occ})
            if isinstance(res, dict) and "user_id" in res:
                st.session_state["user"] = res
                render_alert("Profile successfully updated!", "success")
                st.rerun()
            else:
                err = res.get("error", "Update failed") if isinstance(res, dict) else "Update failed"
                render_alert(f"Failed to update profile: {err}", "error")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Active Goals Summary")
    goals = APIClient.get("/goals") or []
    if not goals:
        render_alert("No active goals logged yet. You can log new target milestones in your profile.", "info")
    else:
        for g in goals:
            pct = g.get("progress_percentage", 0.0) / 100.0
            status_color = "#2563EB" if g.get("status") == "On Track" else "#7C3AED"
            st.markdown(
                f"""
                <div class="hud-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; color:#0F172A;">{g.get('goal_name')} ({g.get('category')})</h4>
                        <span style="color:{status_color}; font-family:'Sora'; font-weight:700;">{g.get('status')}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#475569; margin: 6px 0;">Target Date: {str(g.get('target_date', ''))[:10]} | Target Value: ${g.get('target_value', 0):,.2f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.progress(pct)

with col_right:
    st.markdown('<div class="hud-card-violet">', unsafe_allow_html=True)
    st.subheader("Behavioral Profile")
    
    render_metric_card("Active Goals", str(profile.get("active_goals_count", 0)), "Tracked targets")
    render_metric_card("Habit Streak", f"{profile.get('habit_streak', 0)} Days", "Daily consistency", is_violet=True)

    st.markdown("#### Digital Twin State")
    st.markdown(
        """
        <div style="font-size: 0.85rem; color: #334155; line-height: 1.8;">
            &bull; <b>Financial Discipline</b>: <span style="color:#2563EB;">High (88%)</span><br>
            &bull; <b>Study Consistency</b>: <span style="color:#2563EB;">Optimal</span><br>
            &bull; <b>Fitness Activity</b>: <span style="color:#7C3AED;">Moderate</span><br>
            &bull; <b>Risk Profile</b>: <span style="color:#2563EB;">Low Risk</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
