import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme
from frontend.components.sidebar import render_sidebar

apply_stitch_theme()

if not st.session_state.get("authenticated"):
    st.warning("Authentication required. Redirecting to login...")
    st.rerun()

render_sidebar()

st.title("Decision Simulation Engine")
st.markdown("9-Category decision simulator with 5-way scenario projection (Current Path, Best, Expected, Worst, Risk).")

st.markdown(
    """
    <div class="hud-card-violet">
        <h3 style="color:#7C3AED;">What-If Simulation Suite</h3>
        <p style="color:#475569; line-height: 1.6;">
            Simulate life decisions across Financial, Career, Study, Fitness, Investment, and Lifestyle domains. Monte-Carlo risk assessment runs within 5 seconds.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
