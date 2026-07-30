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

st.title("Machine Learning Financial Forecasting")
st.markdown("Forecasting module (Prophet, ARIMA, XGBoost champion model selection).")

st.markdown(
    """
    <div class="hud-card">
        <h3 style="color:#2563EB;">Projections Engine Preview</h3>
        <p style="color:#475569; line-height: 1.6;">
            Once sufficient financial transactions are logged, the Champion/Challenger Model Selector evaluates Prophet, ARIMA, XGBoost, and LightGBM models to project 6-month, 1-year, and 3-year net worth trajectories.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
