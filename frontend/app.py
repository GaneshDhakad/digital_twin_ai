import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from theme.styles import apply_stitch_theme

st.set_page_config(
    page_title="Digital Twin AI - Personal Life Simulation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global theme
apply_stitch_theme()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None

# Define Pages
login_page = st.Page("views/login.py", title="Sign In / Register", icon="🔐")
dashboard_page = st.Page("views/dashboard.py", title="Dashboard", icon="📊", default=True)
profile_page = st.Page("views/profile.py", title="My Profile", icon="👤")
financial_page = st.Page("views/financial.py", title="Financial Health", icon="💳")
study_page = st.Page("views/study.py", title="Study & Academics", icon="📚")
habits_page = st.Page("views/habits.py", title="Habits & Fitness", icon="🏋️")
ai_intelligence_page = st.Page("views/ai_intelligence.py", title="AI Intelligence", icon="🤖")
forecasting_page = st.Page("views/forecasting.py", title="AI Forecasting", icon="📈")
simulation_page = st.Page("views/simulation.py", title="Decision Simulation", icon="🔮")

st.session_state["login_page"] = login_page
st.session_state["dashboard_page"] = dashboard_page
st.session_state["profile_page"] = profile_page
st.session_state["financial_page"] = financial_page
st.session_state["study_page"] = study_page
st.session_state["habits_page"] = habits_page
st.session_state["ai_intelligence_page"] = ai_intelligence_page
st.session_state["forecasting_page"] = forecasting_page
st.session_state["simulation_page"] = simulation_page

if not st.session_state["authenticated"]:
    pg = st.navigation([login_page], position="hidden")
else:
    pg = st.navigation({
        "Overview": [dashboard_page, profile_page],
        "Life": [financial_page, study_page, habits_page],
        "Intelligence": [ai_intelligence_page, forecasting_page, simulation_page]
    })

pg.run()

