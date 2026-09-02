import streamlit as st

def render_alert(message: str, type_: str = "info"):
    color_map = {
        "success": ("#10B981", "#ECFDF5", "#065F46"),
        "error": ("#EF4444", "#FEF2F2", "#991B1B"),
        "warning": ("#F59E0B", "#FFFBEB", "#92400E"),
        "info": ("#2563EB", "#EFF6FF", "#1E40AF")
    }
    border_color, bg_color, text_color = color_map.get(type_, color_map["info"])
    
    st.markdown(
        f"""
        <div style="background: {bg_color}; border: 1px solid {border_color}; border-left: 4px solid {border_color}; border-radius: 6px; padding: 12px 16px; margin: 10px 0; color: {text_color}; font-weight: 500;">
            {message}
        </div>
        """,
        unsafe_allow_html=True
    )
