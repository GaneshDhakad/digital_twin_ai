import streamlit as st

def render_sidebar():
    """
    Renders a premium Apple + Stripe + Notion inspired SaaS Navigation Sidebar.
    Contains Application logo, Navigation menu indicator, Icons, User profile card,
    Theme information, Settings section, and an interactive Help drawer.
    """
    with st.sidebar:
        # 1. Application Logo & Version Badge
        st.markdown(
            """
            <div style="padding: 16px 8px 20px 8px; border-bottom: 1px solid #E5E7EB; text-align: left;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <h2 style="font-family: 'Manrope', sans-serif; font-size: 1.45rem; font-weight: 800; color: #111827; margin: 0;">
                        TWIN<span style="color: #2563EB;">.OS</span>
                    </h2>
                    <span style="background: rgba(37, 99, 235, 0.1); color: #2563EB; font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 9999px;">
                        SaaS v2.0
                    </span>
                </div>
                <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600; margin-top: 4px;">
                    Digital Twin Decision Engine
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. User Profile Card
        user = st.session_state.get("user", {})
        name = user.get("name", "Operator") if isinstance(user, dict) else "Operator"
        email = user.get("email", "operator@twinos.ai") if isinstance(user, dict) else "operator@twinos.ai"
        occupation = user.get("occupation", "Systems Architect") if isinstance(user, dict) else "Systems Architect"
        initials = "".join([part[0].upper() for part in name.split()[:2]]) if name else "OP"

        st.markdown(
            f"""
            <div class="sidebar-user-card" style="display: flex; align-items: center; gap: 12px; margin-top: 18px;">
                <div style="width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%); color: #FFFFFF; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 0.95rem; flex-shrink: 0;">
                    {initials}
                </div>
                <div style="overflow: hidden;">
                    <div style="font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 0.9rem; color: #111827; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {name}
                    </div>
                    <div style="font-size: 0.75rem; color: #6B7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {email}
                    </div>
                    <div style="margin-top: 4px; font-size: 0.72rem; color: #10B981; font-weight: 700; display: flex; align-items: center;">
                        <span class="status-pip-online"></span> ONLINE &bull; {occupation}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 3. Navigation Indicator & Domain Icons
        st.markdown(
            """
            <div style="margin: 20px 0 10px 0;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
                    WORKSPACE NAVIGATION
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 0.85rem; color: #111827; font-weight: 600;">
                    <div style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 8px; background: rgba(37,99,235,0.06); color: #2563EB;">
                        <span>📊</span> <span>Executive Dashboard</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 8px; color: #6B7280;">
                        <span>💳</span> <span>Financial Ledger & Net Worth</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 8px; color: #6B7280;">
                        <span>📚</span> <span>Study & Academic Focus</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 8px; color: #6B7280;">
                        <span>🏋️</span> <span>Habits & Physical Fitness</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 8px; color: #6B7280;">
                        <span>🔮</span> <span>Monte-Carlo Decision Engine</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")

        # 4. Theme Information Badge
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E5E7EB; border-radius: 12px; padding: 12px; margin: 12px 0;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #111827; display: flex; align-items: center; justify-content: space-between;">
                    <span>🎨 Theme Information</span>
                    <span style="color: #2563EB;">Apple/Stripe Light</span>
                </div>
                <div style="font-size: 0.72rem; color: #6B7280; margin-top: 4px;">
                    16px border-radius &bull; #F8FAFC canvas &bull; Soft elevation shadows
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 5. Settings Section (Interactive Expander)
        with st.expander("⚙️ System Settings", expanded=False):
            st.checkbox("⚡ Real-time Twin Auto-Sync", value=True, key="setting_auto_sync", help="Synchronize twin state on every database transaction.")
            st.checkbox("🚀 Monte-Carlo GPU Acceleration", value=True, key="setting_gpu_mode", help="Use multi-core background tasks for 5-way simulation.")
            st.checkbox("🔔 Alert Notifications", value=True, key="setting_notifications", help="Show toast notifications when anomalies are detected.")

        # 6. Help Button & Interactive Support Modal/Drawer
        with st.expander("❓ Help & Documentation", expanded=False):
            st.markdown(
                """
                <div style="font-size: 0.82rem; color: #4B5563; line-height: 1.6;">
                    <b>Quick Links:</b><br>
                    &bull; <a href="http://localhost:8000/docs" target="_blank" style="color: #2563EB; font-weight: 600;">REST API Docs (Swagger)</a><br>
                    &bull; <a href="http://localhost:8000/" target="_blank" style="color: #2563EB; font-weight: 600;">Showcase Landing Website</a><br>
                    &bull; <a href="http://localhost:8000/redoc" target="_blank" style="color: #2563EB; font-weight: 600;">ReDoc Specification</a><br><br>
                    <b>Keyboard Shortcuts:</b><br>
                    &bull; <code style="background:#F1F5F9; padding:2px 4px; border-radius:4px;">R</code> : Refresh Data<br>
                    &bull; <code style="background:#F1F5F9; padding:2px 4px; border-radius:4px;">C</code> : Clear Cache
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout of Twin.OS", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()
