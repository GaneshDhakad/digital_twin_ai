import streamlit as st

def render_alert(message: str, type_: str = "info"):
    theme_mode = st.session_state.get("theme_mode", "light")
    is_dark = (theme_mode == "dark")

    if is_dark:
        color_map = {
            "success": ("#10B981", "rgba(16, 185, 129, 0.18)", "#34D399"),
            "error": ("#EF4444", "rgba(239, 68, 68, 0.18)", "#F87171"),
            "warning": ("#F59E0B", "rgba(245, 158, 11, 0.18)", "#FBBF24"),
            "info": ("#3B82F6", "rgba(59, 130, 246, 0.18)", "#93C5FD"),
        }
    else:
        color_map = {
            "success": ("#10B981", "#ECFDF5", "#065F46"),
            "error": ("#EF4444", "#FEF2F2", "#991B1B"),
            "warning": ("#F59E0B", "#FFFBEB", "#92400E"),
            "info": ("#2563EB", "#EFF6FF", "#1E40AF"),
        }

    border_color, bg_color, text_color = color_map.get(type_, color_map["info"])
    
    st.markdown(
        f"""
        <div style="background: {bg_color}; border: 1px solid {border_color}; border-left: 4px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; color: {text_color}; font-weight: 600;">
            {message}
        </div>
        """,
        unsafe_allow_html=True
    )
