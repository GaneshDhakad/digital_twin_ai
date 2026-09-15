import streamlit as st

def apply_stitch_theme():
    """
    Applies an Apple + Stripe + Notion inspired Light or Dark Theme SaaS Dashboard Design System.
    Dynamically responds to st.session_state['theme_mode'] ('light' or 'dark').
    Guarantees crisp, high-contrast text visibility across all widgets and cards in both modes.
    """
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "light"

    theme_mode = st.session_state.get("theme_mode", "light")
    is_dark = (theme_mode == "dark")

    if is_dark:
        bg_main = "#0B0F19"
        bg_card = "#161F30"
        bg_card_alt = "#1E293B"
        border = "#26354A"
        border_hover = "rgba(59, 130, 246, 0.5)"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        text_muted = "#64748B"
        primary = "#3B82F6"
        secondary = "#60A5FA"
        shadow_soft = "0 10px 30px rgba(0, 0, 0, 0.35)"
        shadow_hover = "0 15px 35px rgba(0, 0, 0, 0.5)"
        sidebar_bg = "#101726"
        df_header_bg = "#1E293B"
        df_row_alt = "#111827"
    else:
        bg_main = "#F8FAFC"
        bg_card = "#FFFFFF"
        bg_card_alt = "#F1F5F9"
        border = "#E2E8F0"
        border_hover = "rgba(37, 99, 235, 0.35)"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        text_muted = "#64748B"
        primary = "#2563EB"
        secondary = "#3B82F6"
        shadow_soft = "0 10px 30px rgba(0, 0, 0, 0.06)"
        shadow_hover = "0 15px 35px rgba(0, 0, 0, 0.09)"
        sidebar_bg = "#FFFFFF"
        df_header_bg = "#F1F5F9"
        df_row_alt = "#F8FAFC"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');

        :root {{
            --bg-main: {bg_main};
            --bg-card: {bg_card};
            --bg-card-alt: {bg_card_alt};
            --primary: {primary};
            --secondary: {secondary};
            --success: #10B981;
            --warning: #F59E0B;
            --error: #EF4444;
            --text-primary: {text_primary};
            --text-secondary: {text_secondary};
            --text-muted: {text_muted};
            --border: {border};
            --shadow-soft: {shadow_soft};
            --shadow-hover: {shadow_hover};
            --radius-default: 16px;
            --radius-pill: 9999px;
            --transition: all 0.3s ease;
        }}

        /* 1. Global Container & Background */
        .stApp {{
            background-color: var(--bg-main) !important;
            color: var(--text-primary) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }}

        .stApp, .stApp p, .stApp div, .stApp span, .stApp label {{
            color: var(--text-primary);
        }}

        /* 2. Typography Hierarchy */
        h1, h2, h3, h4, h5, h6,
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4,
        div[data-testid="stMarkdownContainer"] h5,
        div[data-testid="stMarkdownContainer"] h6 {{
            font-family: 'Manrope', 'Inter', sans-serif !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.025em !important;
            font-weight: 800 !important;
        }}

        div[data-testid="stMarkdownContainer"] p {{
            color: var(--text-secondary) !important;
            line-height: 1.6;
        }}

        /* 3. Buttons (Gradient Pill Design with Scale Animation) */
        .stButton > button {{
            background: linear-gradient(135deg, {primary} 0%, {secondary} 100%) !important;
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            border: none !important;
            border-radius: var(--radius-pill) !important;
            padding: 10px 24px !important;
            transition: var(--transition) !important;
            letter-spacing: 0.01em !important;
            box-shadow: 0 6px 20px -4px rgba(37, 99, 235, 0.35) !important;
            cursor: pointer !important;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 12px 28px -6px rgba(37, 99, 235, 0.45) !important;
            filter: brightness(1.08) !important;
        }}

        .stButton > button:active {{
            transform: translateY(0) scale(0.99) !important;
        }}

        /* Secondary Button Style */
        .stButton button[kind="secondary"] {{
            background: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
        }}

        .stButton button[kind="secondary"]:hover {{
            background: var(--bg-card-alt) !important;
            border-color: var(--primary) !important;
            color: var(--primary) !important;
        }}

        /* 4. Form Elements & Inputs (16px Radius + High Contrast) */
        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stDateInput input, .stTimeInput input {{
            background-color: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            padding: 10px 14px !important;
            transition: var(--transition) !important;
        }}

        .stTextInput input, .stNumberInput input {{
            color: var(--text-primary) !important;
        }}

        /* Selectbox popover and items */
        div[data-baseweb="popover"], div[data-baseweb="popover"] ul {{
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
        }}

        div[data-baseweb="popover"] li {{
            background-color: var(--bg-card) !important;
            color: var(--text-primary) !important;
        }}

        div[data-baseweb="popover"] li:hover {{
            background-color: var(--bg-card-alt) !important;
            color: var(--primary) !important;
        }}

        .stSelectbox div[data-baseweb="select"] span,
        .stSelectbox div[data-baseweb="select"] div,
        .stSelectbox [data-baseweb="select"] [data-value],
        div[data-baseweb="popover"] span {{
            color: var(--text-primary) !important;
        }}

        .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus,
        .stSelectbox div[data-baseweb="select"] > div:focus-within,
        .stMultiSelect div[data-baseweb="select"] > div:focus-within {{
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
            outline: none !important;
        }}

        .stTextInput label, .stNumberInput label, .stSelectbox label,
        .stSlider label, .stMultiSelect label, .stTextArea label,
        .stDateInput label, .stCheckbox label, .stRadio label {{
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            margin-bottom: 4px !important;
        }}

        /* Radio & Slider text visibility */
        div[data-testid="stRadio"] label span,
        div[data-testid="stRadio"] div[role="radiogroup"] span,
        div[data-testid="stSlider"] span {{
            color: var(--text-primary) !important;
        }}

        /* 5. SaaS Cards & KPI Cards */
        .saas-card, .kpi-card, .hud-card, .hud-card-violet {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            padding: 22px !important;
            margin-bottom: 18px !important;
            box-shadow: var(--shadow-soft) !important;
            transition: var(--transition) !important;
            position: relative;
            overflow: hidden;
        }}

        .saas-card:hover, .kpi-card:hover, .hud-card:hover, .hud-card-violet:hover {{
            transform: translateY(-4px) !important;
            box-shadow: var(--shadow-hover) !important;
            border-color: {border_hover} !important;
        }}

        .hud-card {{ border-top: 4px solid var(--primary) !important; }}
        .hud-card-violet {{ border-top: 4px solid #8B5CF6 !important; }}

        .kpi-title {{
            font-size: 0.825rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .kpi-val {{
            font-family: 'Manrope', sans-serif;
            font-size: 2.1rem;
            font-weight: 800;
            color: var(--text-primary);
            line-height: 1.1;
            margin-bottom: 8px;
        }}

        .kpi-trend {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: var(--radius-pill);
        }}

        .kpi-trend.up {{
            background: rgba(16, 185, 129, 0.15);
            color: #10B981;
        }}

        .kpi-trend.down {{
            background: rgba(239, 68, 68, 0.15);
            color: #EF4444;
        }}

        .kpi-trend.neutral {{
            background: rgba(59, 130, 246, 0.15);
            color: var(--primary);
        }}

        .kpi-sub {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-left: 6px;
        }}

        /* 6. Dashboard Hero Section */
        .saas-hero {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-default);
            padding: 28px 32px;
            box-shadow: var(--shadow-soft);
            margin-bottom: 24px;
            position: relative;
        }}

        .saas-hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(59, 130, 246, 0.12);
            color: var(--primary);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: var(--radius-pill);
            margin-bottom: 12px;
        }}

        .saas-hero h1 {{
            font-size: 2.3rem !important;
            margin-bottom: 8px !important;
            color: var(--text-primary) !important;
        }}

        .saas-hero p {{
            font-size: 1.02rem;
            color: var(--text-secondary) !important;
            max-width: 780px;
            margin-bottom: 16px;
        }}

        .saas-hero-divider {{
            height: 3px;
            width: 100%;
            background: linear-gradient(90deg, {primary} 0%, #8B5CF6 50%, #10B981 100%);
            border-radius: var(--radius-pill);
            margin-top: 16px;
        }}

        /* 7. Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid var(--border) !important;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.05) !important;
        }}

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color: var(--text-primary) !important;
        }}

        .sidebar-user-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-default);
            padding: 14px;
            margin: 16px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            transition: var(--transition);
        }}

        .sidebar-user-card:hover {{
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }}

        .status-pip-online {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 8px var(--success);
        }}

        /* 8. Tables / Dataframes */
        div[data-testid="stDataFrame"] {{
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            overflow: hidden !important;
            background: var(--bg-card) !important;
            box-shadow: var(--shadow-soft) !important;
        }}

        div[data-testid="stDataFrame"] table {{
            border-collapse: collapse !important;
            width: 100% !important;
        }}

        div[data-testid="stDataFrame"] th {{
            background-color: {df_header_bg} !important;
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            border-bottom: 2px solid var(--border) !important;
            padding: 12px 16px !important;
            position: sticky !important;
            top: 0 !important;
            z-index: 10 !important;
        }}

        div[data-testid="stDataFrame"] td {{
            color: var(--text-primary) !important;
            border-bottom: 1px solid var(--border) !important;
        }}

        div[data-testid="stDataFrame"] tr:nth-child(even) {{
            background-color: {df_row_alt} !important;
        }}

        /* 9. Tabs & Expanders */
        button[data-baseweb="tab"] {{
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 10px 20px !important;
            transition: var(--transition) !important;
            border-radius: var(--radius-default) var(--radius-default) 0 0 !important;
        }}

        button[data-baseweb="tab"]:hover {{
            color: var(--primary) !important;
            background: rgba(59, 130, 246, 0.08) !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--primary) !important;
            border-bottom: 3px solid var(--primary) !important;
            font-weight: 700 !important;
        }}

        div[data-testid="stExpander"] {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            box-shadow: var(--shadow-soft) !important;
            overflow: hidden !important;
        }}

        div[data-testid="stExpander"] summary {{
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            padding: 16px 20px !important;
        }}

        /* 10. Alerts & Notifications */
        div[data-testid="stAlert"] {{
            border-radius: var(--radius-default) !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        }}

        /* Horizon pill button row */
        .horizon-pill-active {{
            background: {primary} !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            border-radius: var(--radius-pill) !important;
            padding: 6px 14px !important;
            display: inline-block;
        }}

        .horizon-pill-inactive {{
            background: var(--bg-card-alt) !important;
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            border-radius: var(--radius-pill) !important;
            padding: 6px 14px !important;
            display: inline-block;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_theme_switcher():
    """
    Renders an interactive theme switcher button at the top corner of the view.
    Allows seamlessly toggling between Light and Dark modes.
    """
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "light"

    current_mode = st.session_state.get("theme_mode", "light")
    is_dark = (current_mode == "dark")

    # Corner container with right-aligned button
    c1, c2 = st.columns([8, 2])
    with c2:
        btn_label = "☀️ Light Theme" if is_dark else "🌙 Dark Theme"
        if st.button(
            btn_label,
            key="header_theme_toggle_btn",
            use_container_width=True,
            help="Switch application theme between Light and Dark mode",
        ):
            st.session_state["theme_mode"] = "light" if is_dark else "dark"
            st.rerun()


def apply_saas_plotly_layout(fig, title_text="", height=360):
    """
    Applies a clean SaaS layout to Plotly figures adapting dynamically
    to Light and Dark themes.
    """
    theme_mode = st.session_state.get("theme_mode", "light")
    is_dark = (theme_mode == "dark")

    if is_dark:
        paper_bg = "#161F30"
        plot_bg = "#161F30"
        title_color = "#F8FAFC"
        font_color = "#94A3B8"
        grid_color = "#26354A"
        line_color = "#334155"
        hover_bg = "#0F172A"
        hover_font = "#F8FAFC"
    else:
        paper_bg = "#FFFFFF"
        plot_bg = "#FFFFFF"
        title_color = "#111827"
        font_color = "#4B5563"
        grid_color = "#F1F5F9"
        line_color = "#E5E7EB"
        hover_bg = "#111827"
        hover_font = "#FFFFFF"

    fig.update_layout(
        title={
            "text": f"<b>{title_text}</b>" if title_text else "",
            "font": {"family": "Manrope, sans-serif", "size": 16, "color": title_color},
            "x": 0.02,
            "y": 0.95,
        },
        height=height,
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        font={"family": "Inter, sans-serif", "color": font_color, "size": 12},
        margin=dict(l=40, r=30, t=55, b=40),
        hoverlabel=dict(
            bgcolor=hover_bg,
            font_size=13,
            font_family="Inter, sans-serif",
            font_color=hover_font,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=font_color),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=grid_color,
        linecolor=line_color,
        zerolinecolor=line_color,
        tickfont=dict(color=font_color),
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=grid_color,
        linecolor=line_color,
        zerolinecolor=line_color,
        tickfont=dict(color=font_color),
    )
    return fig
