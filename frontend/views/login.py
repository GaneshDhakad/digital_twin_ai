import streamlit as st
import requests
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme
from frontend.utils.api_client import APIClient, API_BASE_URL
from frontend.components.alerts import render_alert

apply_stitch_theme()

st.markdown(
    """
    <div style="text-align: center; padding: 40px 0 20px 0;">
        <h1 style="font-size: 3rem; color: #2563EB; font-weight: 800; margin-bottom: 8px;">DIGITAL TWIN <span style="color:#7C3AED;">AI</span></h1>
        <p style="color: #475569; font-size: 1.15rem; max-width: 650px; margin: 0 auto; line-height: 1.6;">
            Personal Life Simulation & Autonomous Decision Intelligence System.
            <br><span style="font-size: 0.95rem; color: #64748B;">Sign in or create a new account to enter your personalized Digital Twin.</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])

with col_center:
    tab_login, tab_register = st.tabs(["SIGN IN TO TWIN.OS", "CREATE ACCOUNT"])

    with tab_login:
        st.markdown('<div class="hud-card">', unsafe_allow_html=True)
        with st.form("login_form"):
            st.subheader("Account Credentials")
            login_email = st.text_input("Email Address", placeholder="user@example.com")
            login_pass = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("AUTHENTICATE & ENTER", use_container_width=True)

            if submit_login:
                if not login_email or not login_pass:
                    render_alert("Please enter both email and password.", "warning")
                else:
                    res = APIClient.post("/auth/login", data={"username": login_email, "password": login_pass})
                    token = None
                    user = None
                    if isinstance(res, dict) and "access_token" in res:
                        token = res["access_token"]
                        user = res.get("user", {})
                    else:
                        # Fallback for FastAPI OAuth2 Form
                        try:
                            form_res = requests.post(f"{API_BASE_URL}/auth/login", data={"username": login_email, "password": login_pass})
                            if form_res.status_code == 200:
                                data = form_res.json()
                                token = data["access_token"]
                                user = data.get("user", {})
                            else:
                                err_msg = form_res.json().get("detail", "Invalid email or password")
                                render_alert(f"Authentication Failed: {err_msg}", "error")
                        except Exception as ex:
                            render_alert(f"Connection Error: {ex}", "error")

                    if token:
                        st.session_state["authenticated"] = True
                        st.session_state["token"] = token
                        st.session_state["user"] = user or {"email": login_email, "name": "Operator"}
                        render_alert("Authentication successful! Loading Digital Twin...", "success")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_register:
        st.markdown('<div class="hud-card-violet">', unsafe_allow_html=True)
        with st.form("register_form"):
            st.subheader("New Operator Registration")
            reg_name = st.text_input("Full Name", placeholder="Ganesh Dhakad")
            reg_email = st.text_input("Email Address", placeholder="ganesh@example.com")
            reg_pass = st.text_input("Password (min 8 characters)", type="password")
            reg_age = st.number_input("Age", min_value=13, max_value=100, value=22)
            reg_occ = st.text_input("Occupation", placeholder="Software Engineer / Student")
            submit_reg = st.form_submit_button("REGISTER OPERATOR & ENTER", use_container_width=True)

            if submit_reg:
                if not reg_name or not reg_email or not reg_pass:
                    render_alert("Name, email, and password are required.", "warning")
                elif len(reg_pass) < 8:
                    render_alert("Password must be at least 8 characters.", "warning")
                else:
                    reg_payload = {
                        "name": reg_name,
                        "email": reg_email,
                        "password": reg_pass,
                        "age": int(reg_age),
                        "occupation": reg_occ,
                    }
                    res = APIClient.post("/auth/register", data=reg_payload)
                    if isinstance(res, dict) and "access_token" in res:
                        st.session_state["authenticated"] = True
                        st.session_state["token"] = res["access_token"]
                        st.session_state["user"] = res.get("user", {})
                        render_alert("Registration successful! Initializing Digital Twin...", "success")
                        st.rerun()
                    else:
                        err_detail = res.get("error", "Registration failed.") if isinstance(res, dict) else "Registration failed."
                        render_alert(f"Registration Error: {err_detail}", "error")
        st.markdown('</div>', unsafe_allow_html=True)
