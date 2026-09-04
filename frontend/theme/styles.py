import streamlit as st

def apply_stitch_theme():
    """
    Applies an Apple + Stripe + Notion inspired Light Theme SaaS Dashboard Design System.
    Enforces 16px border radii, soft shadows, gradient pill buttons, input focus rings,
    and responsive, uncluttered card aesthetics.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');

        :root {
            --bg-main: #F8FAFC;
            --bg-card: #FFFFFF;
            --primary: #2563EB;
            --secondary: #3B82F6;
            --success: #10B981;
            --warning: #F59E0B;
            --error: #EF4444;
            --text-primary: #111827;
            --text-secondary: #6B7280;
            --border: #E5E7EB;
            --shadow-soft: 0 10px 30px rgba(0, 0, 0, 0.06);
            --shadow-hover: 0 15px 35px rgba(0, 0, 0, 0.09);
            --radius-default: 16px;
            --radius-pill: 9999px;
            --transition: all 0.3s ease;
        }

        /* 1. Global Container & Background */
        .stApp {
            background-color: var(--bg-main) !important;
            color: var(--text-primary) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        .stApp, .stApp p, .stApp div, .stApp span, .stApp label {
            color: var(--text-primary);
        }

        /* 2. Typography Hierarchy */
        h1, h2, h3, h4, h5, h6,
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4,
        div[data-testid="stMarkdownContainer"] h5,
        div[data-testid="stMarkdownContainer"] h6 {
            font-family: 'Manrope', 'Inter', sans-serif !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.025em !important;
            font-weight: 800 !important;
        }

        /* 3. Buttons (Gradient Pill Design with Scale Animation) */
        .stButton > button {
            background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important;
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            border: none !important;
            border-radius: var(--radius-pill) !important;
            padding: 12px 28px !important;
            transition: var(--transition) !important;
            letter-spacing: 0.01em !important;
            box-shadow: 0 6px 20px -4px rgba(37, 99, 235, 0.35) !important;
            cursor: pointer !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 12px 28px -6px rgba(37, 99, 235, 0.45) !important;
            filter: brightness(1.08) !important;
        }

        .stButton > button:active {
            transform: translateY(0) scale(0.99) !important;
        }

        /* Secondary Button Style overrides when marked */
        .stButton button[kind="secondary"] {
            background: #FFFFFF !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
        }

        .stButton button[kind="secondary"]:hover {
            background: #F8FAFC !important;
            border-color: var(--text-secondary) !important;
        }

        /* 4. Form Elements & Inputs (16px Radius + Focus Ring) */
        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stDateInput input, .stTimeInput input {
            background-color: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            padding: 10px 14px !important;
            transition: var(--transition) !important;
        }

        /* Ensure entered/selected values inside inputs are always visible */
        .stTextInput input, .stNumberInput input {
            color: var(--text-primary) !important;
        }

        /* Selectbox: ensure selected option text is visible */
        .stSelectbox div[data-baseweb="select"] span,
        .stSelectbox div[data-baseweb="select"] div,
        .stSelectbox [data-baseweb="select"] [data-value],
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] span {
            color: var(--text-primary) !important;
        }

        /* Number input: ensure the value text is visible */
        .stNumberInput div[data-baseweb="input"] input {
            color: var(--text-primary) !important;
            background: var(--bg-card) !important;
        }

        /* Text input value text */
        .stTextInput div[data-baseweb="input"] input {
            color: var(--text-primary) !important;
        }

        /* Slider value label */
        div[data-testid="stSlider"] span {
            color: var(--text-primary) !important;
        }


        .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus,
        .stSelectbox div[data-baseweb="select"] > div:focus-within,
        .stMultiSelect div[data-baseweb="select"] > div:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
            outline: none !important;
        }

        .stTextInput label, .stNumberInput label, .stSelectbox label,
        .stSlider label, .stMultiSelect label, .stTextArea label,
        .stDateInput label, .stCheckbox label, .stRadio label {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            margin-bottom: 4px !important;
        }

        /* File Uploader Container */
        div[data-testid="stFileUploader"] {
            background: var(--bg-card) !important;
            border: 2px dashed var(--border) !important;
            border-radius: var(--radius-default) !important;
            padding: 20px !important;
            transition: var(--transition) !important;
        }

        div[data-testid="stFileUploader"]:hover {
            border-color: var(--primary) !important;
            background: rgba(37, 99, 235, 0.02) !important;
        }

        /* 5. SaaS Cards & KPI Cards (16px Radius + Elevation Hover) */
        .saas-card, .kpi-card, .hud-card, .hud-card-violet {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            padding: 24px !important;
            margin-bottom: 20px !important;
            box-shadow: var(--shadow-soft) !important;
            transition: var(--transition) !important;
            position: relative;
            overflow: hidden;
        }

        .saas-card:hover, .kpi-card:hover, .hud-card:hover, .hud-card-violet:hover {
            transform: translateY(-4px) !important;
            box-shadow: var(--shadow-hover) !important;
            border-color: rgba(37, 99, 235, 0.3) !important;
        }

        /* Top colored indicator bars for card varieties */
        .hud-card { border-top: 4px solid var(--primary) !important; }
        .hud-card-violet { border-top: 4px solid #7C3AED !important; }

        /* KPI Metric Typography */
        .kpi-title {
            font-size: 0.825rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .kpi-val {
            font-family: 'Manrope', sans-serif;
            font-size: 2.1rem;
            font-weight: 800;
            color: var(--text-primary);
            line-height: 1.1;
            margin-bottom: 8px;
        }

        .kpi-trend {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: var(--radius-pill);
        }

        .kpi-trend.up {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }

        .kpi-trend.down {
            background: rgba(239, 68, 68, 0.1);
            color: var(--error);
        }

        .kpi-trend.neutral {
            background: rgba(59, 130, 246, 0.1);
            color: var(--primary);
        }

        .kpi-sub {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-left: 6px;
        }

        /* 6. Dashboard Hero Section */
        .saas-hero {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-default);
            padding: 32px 36px;
            box-shadow: var(--shadow-soft);
            margin-bottom: 28px;
            position: relative;
        }

        .saas-hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(37, 99, 235, 0.08);
            color: var(--primary);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: var(--radius-pill);
            margin-bottom: 12px;
        }

        .saas-hero h1 {
            font-size: 2.4rem !important;
            margin-bottom: 10px !important;
        }

        .saas-hero p {
            font-size: 1.05rem;
            color: var(--text-secondary);
            max-width: 780px;
            margin-bottom: 20px;
        }

        .saas-hero-divider {
            height: 3px;
            width: 100%;
            background: linear-gradient(90deg, #2563EB 0%, #3B82F6 50%, #10B981 100%);
            border-radius: var(--radius-pill);
            margin-top: 20px;
        }

        /* 7. Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid var(--border) !important;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.03) !important;
        }

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: var(--text-primary) !important;
        }

        .sidebar-user-card {
            background: var(--bg-main);
            border: 1px solid var(--border);
            border-radius: var(--radius-default);
            padding: 14px;
            margin: 16px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            transition: var(--transition);
        }

        .sidebar-user-card:hover {
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
        }

        .status-pip-online {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 8px var(--success);
        }

        /* 8. Tables / Dataframes (Zebra rows & Sticky Headers) */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            overflow: hidden !important;
            background: #FFFFFF !important;
            box-shadow: var(--shadow-soft) !important;
        }

        div[data-testid="stDataFrame"] table {
            border-collapse: collapse !important;
            width: 100% !important;
        }

        div[data-testid="stDataFrame"] th {
            background-color: #F1F5F9 !important;
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            border-bottom: 2px solid var(--border) !important;
            padding: 12px 16px !important;
            position: sticky !important;
            top: 0 !important;
            z-index: 10 !important;
        }

        div[data-testid="stDataFrame"] tr:nth-child(even) {
            background-color: #F8FAFC !important;
        }

        div[data-testid="stDataFrame"] tr:hover {
            background-color: rgba(37, 99, 235, 0.04) !important;
        }

        /* 9. Tabs & Expanders */
        button[data-baseweb="tab"] {
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 10px 20px !important;
            transition: var(--transition) !important;
            border-radius: var(--radius-default) var(--radius-default) 0 0 !important;
        }

        button[data-baseweb="tab"]:hover {
            color: var(--primary) !important;
            background: rgba(37, 99, 235, 0.04) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--primary) !important;
            border-bottom: 3px solid var(--primary) !important;
            font-weight: 700 !important;
        }

        div[data-testid="stExpander"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-default) !important;
            box-shadow: var(--shadow-soft) !important;
            overflow: hidden !important;
        }

        div[data-testid="stExpander"] summary {
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            padding: 16px 20px !important;
        }

        /* 10. Alerts & Notifications */
        div[data-testid="stAlert"] {
            border-radius: var(--radius-default) !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04) !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

def apply_saas_plotly_layout(fig, title_text="", height=360):
    """Applies a clean Apple/Stripe light theme to Plotly figures."""
    fig.update_layout(
        title={
            "text": f"<b>{title_text}</b>" if title_text else "",
            "font": {"family": "Manrope, sans-serif", "size": 16, "color": "#111827"},
            "x": 0.02,
            "y": 0.95
        },
        height=height,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": "Inter, sans-serif", "color": "#4B5563", "size": 12},
        margin=dict(l=40, r=30, t=55, b=40),
        hoverlabel=dict(
            bgcolor="#111827",
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="#FFFFFF"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F1F5F9",
        linecolor="#E5E7EB",
        zerolinecolor="#E5E7EB"
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F1F5F9",
        linecolor="#E5E7EB",
        zerolinecolor="#E5E7EB"
    )
    return fig

