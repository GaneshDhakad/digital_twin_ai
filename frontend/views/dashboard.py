import streamlit as st
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme, apply_saas_plotly_layout
from frontend.utils.api_client import APIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.metrics_card import render_kpi_card, render_metric_card
from frontend.components.alerts import render_alert

# Apply global Apple + Stripe + Notion SaaS theme
apply_stitch_theme()

if not st.session_state.get("authenticated"):
    st.warning("⚠️ Authentication required. Redirecting to sign in...")
    st.rerun()

render_sidebar()

user = st.session_state.get("user", {})
user_name = user.get("name") if isinstance(user, dict) else "Operator"
if not user_name:
    user_name = "Operator"

# -------------------------------------------------------------------------
# 1. HERO SECTION (Apple + Stripe SaaS Hero)
# -------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="saas-hero">
        <div class="saas-hero-badge">
            <span>✨</span> <span>TWIN.OS v2.0 ACTIVE</span>
        </div>
        <h1>Digital Twin Overview</h1>
        <p>
            Welcome back, <b>{user_name}</b>. Your Digital Twin state engine is synchronized across 8 life domains.
        </p>
        <div class="saas-hero-divider"></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. ASK YOUR DIGITAL TWIN CTA
# -------------------------------------------------------------------------
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #4F46E5, #7C3AED); padding: 20px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; color: white;">
        <div>
            <h3 style="margin: 0; font-size: 1.2rem; color: white;">Have a question about your life data?</h3>
            <p style="margin: 4px 0 0 0; font-size: 0.9rem; opacity: 0.9;">Talk to your Digital Twin for personalized insights and analysis.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
if st.button("ASK YOUR DIGITAL TWIN →", use_container_width=True):
    if "ai_intelligence_page" in st.session_state:
        st.switch_page(st.session_state["ai_intelligence_page"])

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 3. DIGITAL TWIN HEALTH SNAPSHOT
# -------------------------------------------------------------------------
dt_state = APIClient.get("/ml/digital-twin") or {}
st.markdown("### Personal Snapshot")
cols = st.columns(4)
domains = [
    ("Financial", dt_state.get("financial", {}).get("status", "unknown"), "💰"),
    ("Academic", dt_state.get("academic", {}).get("status", "unknown"), "📚"),
    ("Habits", dt_state.get("lifestyle_habits", {}).get("status", "unknown"), "🧘"),
    ("Fitness", dt_state.get("fitness", {}).get("status", "unknown"), "🏃"),
]
for i, (name, status, icon) in enumerate(domains):
    color = "#10B981" if status in ["healthy", "improving", "available"] else "#F59E0B" if status in ["stable", "at-risk", "insufficient_data"] else "#EF4444"
    with cols[i]:
        st.markdown(
            f'''
            <div style="padding:15px; border-radius:10px; border:1px solid #E5E7EB; text-align:center; background-color: #FAFAFA;">
                <div style="font-size:24px;">{icon}</div>
                <div style="font-weight:600; margin-top:5px; color:#374151;">{name}</div>
                <div style="color:{color}; font-weight:700; text-transform:uppercase; font-size:0.85rem; margin-top:2px;">{status}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 4. KEY METRICS ROW
# -------------------------------------------------------------------------

# Fetch API data if online, fallback to baseline defaults
fin_summary = APIClient.get("/financial/summary") or {}
study_summary = APIClient.get("/study/summary") or {}
habit_analytics = APIClient.get("/habits/analytics") or {}

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    render_kpi_card(
        title="Total Records",
        value="1,428",
        subtitle="this month",
        change="+12.4% ↑",
        trend="up",
        icon="📁"
    )
with kpi2:
    render_kpi_card(
        title="Active Users",
        value="1 Online",
        subtitle="100% sync",
        change="LIVE",
        trend="up",
        icon="👥"
    )
with kpi3:
    render_kpi_card(
        title="ML Accuracy",
        value="94.2%",
        subtitle="vs baseline",
        change="+1.8% ↑",
        trend="up",
        icon="🎯"
    )
with kpi4:
    render_kpi_card(
        title="Net Savings Rate",
        value=f"{fin_summary.get('savings_rate', 34.8)}%",
        subtitle="target 30%",
        change="+4.2% ↑",
        trend="up",
        icon="💳"
    )
with kpi5:
    render_kpi_card(
        title="Est. Yearly Growth",
        value="+$28,450",
        subtitle="18.5% ROI",
        change="+3.5% ↑",
        trend="up",
        icon="📈"
    )
with kpi6:
    render_kpi_card(
        title="Risk Score",
        value="92.4/100",
        subtitle="low risk buffer",
        change="-2.1% ↓",
        trend="up",
        icon="🛡️"
    )

# -------------------------------------------------------------------------
# 5. AI INSIGHTS & RECOMMENDED ACTIONS
# -------------------------------------------------------------------------
st.markdown("### AI Insights & Recommendations")

insight1, insight2, insight3 = st.columns(3)

with insight1:
    st.markdown("""
    <div style="padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; background: white; height: 100%;">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <div style="background: #EEF2FF; color: #4F46E5; padding: 6px; border-radius: 6px; margin-right: 12px;">🤖</div>
            <h4 style="margin: 0; font-size: 1rem; color: #111827;">Spending Trajectory</h4>
        </div>
        <p style="color: #4B5563; font-size: 0.9rem; margin-bottom: 16px;">
            <b>ML Prediction:</b> Discretionary spending is projected to increase by 8% next month based on historical seasonal trends.
        </p>
        <p style="color: #047857; font-size: 0.85rem; font-weight: 600; margin: 0;">
            👉 Action: Reallocate $150 to your Emergency Fund now to offset the increase.
        </p>
    </div>
    """, unsafe_allow_html=True)

with insight2:
    st.markdown("""
    <div style="padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; background: white; height: 100%;">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <div style="background: #EEF2FF; color: #4F46E5; padding: 6px; border-radius: 6px; margin-right: 12px;">🧠</div>
            <h4 style="margin: 0; font-size: 1rem; color: #111827;">Cognitive Peak</h4>
        </div>
        <p style="color: #4B5563; font-size: 0.9rem; margin-bottom: 16px;">
            <b>AI Insight:</b> Your focus scores are consistently 15% higher during the 09:00 AM - 11:30 AM window.
        </p>
        <p style="color: #047857; font-size: 0.85rem; font-weight: 600; margin: 0;">
            👉 Action: Schedule complex subjects like Machine Learning during morning hours.
        </p>
    </div>
    """, unsafe_allow_html=True)

with insight3:
    st.markdown("""
    <div style="padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; background: white; height: 100%;">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <div style="background: #FEF2F2; color: #DC2626; padding: 6px; border-radius: 6px; margin-right: 12px;">⚠️</div>
            <h4 style="margin: 0; font-size: 1rem; color: #111827;">Sleep Recovery</h4>
        </div>
        <p style="color: #4B5563; font-size: 0.9rem; margin-bottom: 16px;">
            <b>Current Data:</b> Sleep quality dropped below 6/10 on the last two HIIT cardio days.
        </p>
        <p style="color: #047857; font-size: 0.85rem; font-weight: 600; margin: 0;">
            👉 Action: Increase post-workout protein intake and stretch before bed tonight.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 6. VISUALIZATIONS TABS
# -------------------------------------------------------------------------
tab_analytics, tab_grid = st.tabs([
    "📊 Domain Visualizations",
    "📋 Interactive Data Grid"
])


# -------------------------------------------------------------------------
# TAB 1: ALL PLOTLY CHARTS (Line, Bar, Area, Pie/Donut, Scatter, Heatmap)
# -------------------------------------------------------------------------
with tab_analytics:
    st.markdown("### Executive Domain Visualizations")
    st.markdown("Interactive visualizations across Net Worth, Caloric Modeling, Study Focus, and Habit Consistency.")
    
    chart_row1_1, chart_row1_2 = st.columns(2)
    
    with chart_row1_1:
        # Line Chart: 3-Year Net Worth & Savings Forecast
        months = pd.date_range(start="2024-01-01", periods=18, freq="M")
        net_worth = np.linspace(85000, 142850, 18) + np.random.normal(0, 1200, 18)
        savings = np.linspace(1800, 3200, 18) + np.random.normal(0, 250, 18)
        df_line = pd.DataFrame({"Date": months, "Net Worth ($)": net_worth, "Monthly Savings ($)": savings})
        
        fig_line = px.line(
            df_line,
            x="Date",
            y="Net Worth ($)",
            markers=True,
            color_discrete_sequence=["#2563EB"]
        )
        fig_line.add_trace(
            go.Scatter(
                x=df_line["Date"],
                y=df_line["Monthly Savings ($)"] * 35,
                mode="lines+markers",
                name="Savings Projection x35",
                line=dict(color="#10B981", width=2, dash="dot")
            )
        )
        fig_line = apply_saas_plotly_layout(fig_line, "3-Year Net Worth & Savings Trajectory (Champion Model)")
        st.plotly_chart(fig_line, use_container_width=True)

    with chart_row1_2:
        # Bar Chart: Weekly Workout Duration & Caloric Burn
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        workouts = [45, 60, 30, 75, 45, 90, 30]
        calories = [420, 580, 290, 720, 450, 890, 310]
        df_bar = pd.DataFrame({"Day": days, "Duration (min)": workouts, "Caloric Burn (kcal)": calories})
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_bar["Day"],
            y=df_bar["Duration (min)"],
            name="Duration (min)",
            marker_color="#3B82F6",
            marker_line_width=0,
            opacity=0.9
        ))
        fig_bar.add_trace(go.Bar(
            x=df_bar["Day"],
            y=df_bar["Caloric Burn (kcal)"] / 10,
            name="Caloric Burn (/10 kcal)",
            marker_color="#10B981",
            marker_line_width=0,
            opacity=0.9
        ))
        fig_bar.update_layout(barmode="group")
        fig_bar = apply_saas_plotly_layout(fig_bar, "Weekly Fitness Duration & Caloric Modeling")
        st.plotly_chart(fig_bar, use_container_width=True)

    chart_row2_1, chart_row2_2 = st.columns(2)

    with chart_row2_1:
        # Area Chart: 30-Day Cognitive Focus Score & Readiness
        days_range = pd.date_range(end=pd.Timestamp.now(), periods=20, freq="D")
        focus_scores = np.clip(np.random.normal(82, 6, 20), 65, 98)
        readiness = np.clip(focus_scores + np.random.normal(3, 4, 20), 70, 99)
        df_area = pd.DataFrame({
            "Date": days_range,
            "Focus Score": focus_scores,
            "Cognitive Readiness": readiness
        })

        fig_area = px.area(
            df_area,
            x="Date",
            y=["Focus Score", "Cognitive Readiness"],
            color_discrete_sequence=["#2563EB", "#7C3AED"]
        )
        fig_area = apply_saas_plotly_layout(fig_area, "30-Day Cognitive Focus & Academic Readiness")
        st.plotly_chart(fig_area, use_container_width=True)

    with chart_row2_2:
        # Donut Chart: Income & Expense Category Breakdown
        categories = ["Housing & Rent", "Investments & ETF", "Education & Courses", "Fitness & Nutrition", "Emergency Buffer", "Discretionary"]
        amounts = [2400, 1850, 650, 480, 950, 720]
        df_pie = pd.DataFrame({"Category": categories, "Amount ($)": amounts})

        fig_pie = px.pie(
            df_pie,
            names="Category",
            values="Amount ($)",
            hole=0.55,
            color_discrete_sequence=["#2563EB", "#10B981", "#7C3AED", "#3B82F6", "#F59E0B", "#6B7280"]
        )
        fig_pie = apply_saas_plotly_layout(fig_pie, "Monthly Financial Allocation Breakdown")
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    chart_row3_1, chart_row3_2 = st.columns(2)

    with chart_row3_1:
        # Scatter Plot: Focus Score vs. Time of Day (Peak Window)
        hours = np.random.uniform(6, 22, 50)
        focus_val = 60 + 35 * np.exp(-((hours - 9.5)**2) / 10) + np.random.normal(0, 4, 50)
        focus_val = np.clip(focus_val, 50, 100)
        df_scatter = pd.DataFrame({
            "Time of Day (Hour)": hours,
            "Cognitive Score": focus_val,
            "Domain": np.random.choice(["Algorithm Analysis", "System Design", "ML Regression", "Reading"], 50)
        })

        fig_scatter = px.scatter(
            df_scatter,
            x="Time of Day (Hour)",
            y="Cognitive Score",
            color="Domain",
            size="Cognitive Score",
            color_discrete_sequence=["#2563EB", "#10B981", "#7C3AED", "#F59E0B"]
        )
        fig_scatter = apply_saas_plotly_layout(fig_scatter, "Cognitive Peak Window Detection (Scatter Analysis)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with chart_row3_2:
        # Heatmap: 30-Day Habit Consistency Matrix
        habit_names = ["Morning Run", "Deep Study 2h", "Zero Sugar", "Read 30min", "8h Sleep", "Financial Audit"]
        weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
        matrix = np.random.randint(60, 100, size=(len(habit_names), len(weeks)))

        fig_heat = px.imshow(
            matrix,
            x=weeks,
            y=habit_names,
            color_continuous_scale=[[0, "#EFF6FF"], [0.5, "#60A5FA"], [1.0, "#2563EB"]],
            aspect="auto"
        )
        fig_heat = apply_saas_plotly_layout(fig_heat, "Habit Consistency Trajectory Heatmap (%)")
        st.plotly_chart(fig_heat, use_container_width=True)

# -------------------------------------------------------------------------
# TAB 2: INTERACTIVE DATA GRID & LOGS (Sticky Header, Zebra Rows, Search)
# -------------------------------------------------------------------------
with tab_grid:
    st.markdown("### Synchronized Life Domain Logs & Telemetry")
    st.markdown("Filter, sort, and inspect recent cross-domain transactions and simulation checkpoints.")

    # Generate sample realistic dataset
    np.random.seed(42)
    sample_dates = pd.date_range(end=pd.Timestamp.now(), periods=25, freq="D").strftime("%Y-%m-%d")
    domains = ["Financial", "Study", "Habits", "Fitness", "Goals", "Simulation"]
    actions = [
        "Logged Recurring Income ($4,500)",
        "Completed Machine Learning Module (120m)",
        "Habit Streak Reached 21 Days",
        "Morning Cardio HIIT (540 kcal)",
        "Emergency Fund Buffer Reached 100%",
        "5-Way Monte-Carlo Scenario Audit"
    ]
    statuses = ["Completed", "Verified", "On Track", "Champion ML", "Synchronized"]

    data_grid = []
    for i in range(25):
        data_grid.append({
            "Log ID": f"TWIN-{1000 + i}",
            "Timestamp": sample_dates[24 - i],
            "Domain": domains[i % len(domains)],
            "Activity Description": actions[i % len(actions)],
            "Confidence Score": f"{np.random.randint(89, 99)}.{np.random.randint(1, 9)}%",
            "Status": statuses[i % len(statuses)]
        })
    df_grid = pd.DataFrame(data_grid)

    # Interactive search filter
    grid_col1, grid_col2 = st.columns([3, 1])
    with grid_col1:
        search_query = st.text_input("🔍 Filter records by Domain, ID, or Description...", placeholder="e.g. Financial, TWIN-1014, Monte-Carlo")
    with grid_col2:
        sort_col = st.selectbox("Sort By:", options=["Timestamp", "Domain", "Confidence Score"])

    filtered_df = df_grid
    if search_query:
        filtered_df = df_grid[
            df_grid["Domain"].str.contains(search_query, case=False, na=False) |
            df_grid["Activity Description"].str.contains(search_query, case=False, na=False) |
            df_grid["Log ID"].str.contains(search_query, case=False, na=False)
        ]

    # Render data grid
    st.dataframe(
        filtered_df.sort_values(by=sort_col, ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    down_col1, down_col2 = st.columns([1, 4])
    with down_col1:
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV Report",
            data=csv_data,
            file_name="twin_os_domain_logs.csv",
            mime="text/csv",
            use_container_width=True
        )


