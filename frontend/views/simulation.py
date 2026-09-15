import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme, render_theme_switcher, apply_saas_plotly_layout
from frontend.components.sidebar import render_sidebar
from frontend.components.metrics_card import render_kpi_card
from frontend.components.alerts import render_alert
from frontend.utils.api_client import APIClient

# Apply theme
apply_stitch_theme()

if not st.session_state.get("authenticated"):
    st.warning("Authentication required. Redirecting to login...")
    st.rerun()

render_sidebar()

# Top Header with Theme Switcher at Top Corner
render_theme_switcher()

st.markdown(
    """
    <div class="saas-hero">
        <div class="saas-hero-badge">⚡ MULTI-HORIZON DECISION ENGINE</div>
        <h1>Decision Simulator</h1>
        <p>Model decision trajectories, evaluate trade-offs, and stress-test projected impacts across your Financial, Forecasting, Academic, and Lifestyle dimensions over 5 time horizons.</p>
        <div class="saas-hero-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# 1. DOMAIN SUB-OPTIONS
# ============================================================================
st.markdown("#### 1. Select Simulation Domain")
domain_options = ["Financial", "Forecasting", "Academic", "Lifestyle"]
domain_icons = {
    "Financial": "💳 Financial Health",
    "Forecasting": "📈 Spending Forecast",
    "Academic": "🎓 Academic Performance",
    "Lifestyle": "🧘 Lifestyle & Vitality",
}

sel_domain = st.radio(
    "Simulation Domain",
    domain_options,
    format_func=lambda d: domain_icons[d],
    horizontal=True,
    label_visibility="collapsed",
    key="decision_sim_active_domain",
)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ============================================================================
# 2. TIME HORIZON SUB-OPTIONS (For Each Domain)
# ============================================================================
st.markdown(f"#### 2. Select Time Horizon Impact ({sel_domain})")
horizon_options = ["7_days", "1_month", "3_months", "1_year", "2_years"]
horizon_labels = {
    "7_days": "⚡ Next 7 Days",
    "1_month": "📅 1 Month",
    "3_months": "📊 3 Months",
    "1_year": "🎯 1 Year",
    "2_years": "🚀 2 Years",
}

sel_horizon = st.radio(
    "Impact Time Horizon",
    horizon_options,
    format_func=lambda h: horizon_labels[h],
    horizontal=True,
    label_visibility="collapsed",
    key=f"active_sim_horizon_{sel_domain.lower()}",
)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ============================================================================
# 3. INTERACTIVE SIMULATOR CONTROLS & PRESETS
# ============================================================================
col_ctrl, col_display = st.columns([1, 1.4], gap="large")

with col_ctrl:
    st.markdown(
        f"""
        <div class="saas-card" style="padding: 20px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                SIMULATION PARAMETERS
            </div>
            <div style="font-size: 1.15rem; font-weight: 800; color: var(--text-primary); margin-bottom: 12px;">
                {sel_domain} Decision Driver
            </div>
        """,
        unsafe_allow_html=True,
    )

    sim_params = {"time_horizon": sel_horizon}

    if sel_domain == "Financial":
        st.caption("Adjust your savings and expense levers to model net wealth impacts.")
        
        # Preset buttons
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            if st.button("💰 +$500/mo", key="preset_fin_agg", use_container_width=True, help="Aggressive savings allocation"):
                st.session_state["fin_savings_val"] = 500.0
                st.session_state["fin_extra_cost"] = 0.0
        with p_col2:
            if st.button("⚖️ +$250/mo", key="preset_fin_bal", use_container_width=True, help="Balanced investment plan"):
                st.session_state["fin_savings_val"] = 250.0
                st.session_state["fin_extra_cost"] = 0.0
        with p_col3:
            if st.button("✂️ Trim $150", key="preset_fin_trim", use_container_width=True, help="Expense trim"):
                st.session_state["fin_savings_val"] = 150.0
                st.session_state["fin_extra_cost"] = 0.0

        savings_delta = st.number_input(
            "Monthly Savings / Investment Shift ($)",
            min_value=-2000.0,
            max_value=5000.0,
            value=st.session_state.get("fin_savings_val", 300.0),
            step=50.0,
            key="fin_savings_input",
            help="Positive values allocate additional monthly capital toward savings/investments.",
        )
        extra_expense = st.number_input(
            "Extra Recurring Expense ($)",
            min_value=0.0,
            max_value=3000.0,
            value=st.session_state.get("fin_extra_cost", 0.0),
            step=50.0,
            key="fin_expense_input",
            help="Additional recurring liabilities or subscription obligations.",
        )
        sim_params["savings_delta"] = savings_delta
        sim_params["extra_expense"] = extra_expense
        sim_params["impact"] = savings_delta

    elif sel_domain == "Forecasting":
        st.caption("Simulate shifts in discretionary spending behavior and macro inflation rate.")

        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            if st.button("📉 -15% Spend", key="preset_fore_frugal", use_container_width=True):
                st.session_state["fore_spend_pct"] = -15.0
        with p_col2:
            if st.button("📈 +4% Shift", key="preset_fore_steady", use_container_width=True):
                st.session_state["fore_spend_pct"] = 4.0
        with p_col3:
            if st.button("🏖️ +20% Spend", key="preset_fore_upgrade", use_container_width=True):
                st.session_state["fore_spend_pct"] = 20.0

        spend_pct = st.slider(
            "Discretionary Spending Shift (%)",
            min_value=-35.0,
            max_value=40.0,
            value=st.session_state.get("fore_spend_pct", -10.0),
            step=1.0,
            key="fore_spend_input",
            help="Percentage change in variable consumption and lifestyle expenses.",
        )
        inflation_rate = st.slider(
            "Annual Inflation / Price Escalation Rate (%)",
            min_value=1.0,
            max_value=12.0,
            value=3.2,
            step=0.2,
            key="fore_inflation_input",
        )
        sim_params["spending_shift_pct"] = spend_pct
        sim_params["inflation_rate"] = inflation_rate
        sim_params["impact"] = spend_pct

    elif sel_domain == "Academic":
        st.caption("Model how daily focus time and active recall adjustments compound across academic terms.")

        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            if st.button("⚡ +2.5h Sprint", key="preset_acad_sprint", use_container_width=True):
                st.session_state["acad_hrs_val"] = 2.5
        with p_col2:
            if st.button("📚 +1.0h Daily", key="preset_acad_habit", use_container_width=True):
                st.session_state["acad_hrs_val"] = 1.0
        with p_col3:
            if st.button("🧠 Recall Focus", key="preset_acad_recall", use_container_width=True):
                st.session_state["acad_hrs_val"] = 0.5
                st.session_state["acad_focus_val"] = 18.0

        study_hours = st.slider(
            "Daily Focus / Study Hours Delta (+/- hrs)",
            min_value=-2.0,
            max_value=5.0,
            value=st.session_state.get("acad_hrs_val", 1.5),
            step=0.5,
            key="acad_hours_input",
        )
        focus_boost = st.slider(
            "Focus Quality & Retention Boost (%)",
            min_value=0.0,
            max_value=30.0,
            value=st.session_state.get("acad_focus_val", 10.0),
            step=2.0,
            key="acad_focus_input",
        )
        sim_params["study_hours_delta"] = study_hours
        sim_params["focus_boost"] = focus_boost
        sim_params["impact"] = study_hours

    elif sel_domain == "Lifestyle":
        st.caption("Simulate circadian sleep stability, habit consistency, and workout frequency.")

        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            if st.button("🛌 +1.5h Sleep", key="preset_life_recovery", use_container_width=True):
                st.session_state["life_sleep_val"] = 1.5
                st.session_state["life_workout_val"] = 4
        with p_col2:
            if st.button("⚖️ 3 Workouts", key="preset_life_balanced", use_container_width=True):
                st.session_state["life_sleep_val"] = 1.0
                st.session_state["life_workout_val"] = 3
        with p_col3:
            if st.button("🧘 Stress Reset", key="preset_life_stress", use_container_width=True):
                st.session_state["life_sleep_val"] = 2.0
                st.session_state["life_workout_val"] = 2

        sleep_delta = st.slider(
            "Target Daily Sleep Delta (Hours)",
            min_value=-2.5,
            max_value=3.0,
            value=st.session_state.get("life_sleep_val", 1.0),
            step=0.5,
            key="life_sleep_input",
        )
        workout_days = st.slider(
            "Weekly Workout Frequency (Days / Week)",
            min_value=0,
            max_value=7,
            value=st.session_state.get("life_workout_val", 4),
            step=1,
            key="life_workout_input",
        )
        sim_params["sleep_delta"] = sleep_delta
        sim_params["workout_days"] = workout_days
        sim_params["impact"] = sleep_delta

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    btn_clicked = st.button("⚡ Run Decision Simulation", use_container_width=True, key=f"run_sim_btn_{sel_domain.lower()}")
    if btn_clicked:
        with st.spinner(f"Running multi-horizon simulation for {sel_domain}..."):
            req_payload = {
                "decision_type": sel_domain,
                "input_parameters": sim_params,
            }
            resp = APIClient.post("/simulations", data=req_payload)
            if resp and "error" not in resp:
                st.session_state[f"sim_cache_{sel_domain.lower()}"] = resp
                st.session_state["last_sim"] = resp
                st.success("Simulation Complete!")
            else:
                st.error(f"Simulation failed: {resp.get('error') if resp else 'Unknown error'}")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# 4. SIMULATED IMPACT RESULTS DISPLAY (Selected Horizon)
# ============================================================================
active_sim = st.session_state.get(f"sim_cache_{sel_domain.lower()}")

# If no cached simulation in session yet, attempt to fetch latest from backend or auto-run baseline
if not active_sim:
    history = APIClient.get("/simulations", params={"limit": 10})
    if isinstance(history, list) and len(history) > 0:
        for item in history:
            if item.get("decision_type", "").lower() == sel_domain.lower():
                active_sim = item
                st.session_state[f"sim_cache_{sel_domain.lower()}"] = item
                break

    # If still not found, execute a baseline simulation
    if not active_sim:
        baseline_req = {
            "decision_type": sel_domain,
            "input_parameters": sim_params,
        }
        res_init = APIClient.post("/simulations", data=baseline_req)
        if res_init and "error" not in res_init:
            active_sim = res_init
            st.session_state[f"sim_cache_{sel_domain.lower()}"] = res_init

with col_display:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
            <div>
                <span style="font-size: 0.85rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.05em;">
                    PROJECTED IMPACT &bull; {horizon_labels.get(sel_horizon, sel_horizon)}
                </span>
                <h3 style="margin: 0; font-family: 'Manrope', sans-serif;">{sel_domain} Impact Analysis</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if active_sim:
        sim_res = active_sim.get("simulation_result") or {}
        horizon_impacts = sim_res.get("horizon_impacts") or {}
        outcomes = active_sim.get("predicted_outcome") or {}

        # Extract horizon data
        h_data = horizon_impacts.get(sel_horizon)
        if not h_data and horizon_impacts:
            h_data = list(horizon_impacts.values())[0]

        unit = h_data.get("unit", "") if h_data else ""
        baseline_val = h_data.get("baseline", 0.0) if h_data else 0.0
        expected_val = h_data.get("expected", 0.0) if h_data else 0.0
        delta_val = h_data.get("delta", 0.0) if h_data else 0.0
        risk_status = "Low Risk" if delta_val >= 0 else "High Risk"
        trend_dir = "up" if delta_val >= 0 else "down"

        # Format strings
        if unit == "$":
            disp_base = f"${baseline_val:,.0f}"
            disp_exp = f"${expected_val:,.0f}"
            disp_delta = f"{'+' if delta_val >= 0 else ''}${delta_val:,.0f}"
        else:
            disp_base = f"{baseline_val:.1f} {unit}"
            disp_exp = f"{expected_val:.1f} {unit}"
            disp_delta = f"{'+' if delta_val >= 0 else ''}{delta_val:.1f} {unit}"

        # 4 KPI Cards in a 2x2 grid
        kpi_c1, kpi_c2 = st.columns(2)
        with kpi_c1:
            render_kpi_card(
                title=f"Current Path ({horizon_labels.get(sel_horizon)})",
                value=disp_base,
                subtitle="Baseline Trajectory",
                change="Baseline",
                trend="neutral",
                icon="🧭",
            )
        with kpi_c2:
            render_kpi_card(
                title=f"Projected Outcome ({horizon_labels.get(sel_horizon)})",
                value=disp_exp,
                subtitle=f"Net Delta: {disp_delta}",
                change=disp_delta,
                trend=trend_dir,
                icon="🎯",
            )

        # Check for guardrail warnings across scenarios
        for sc_name, sc_info in outcomes.items():
            warnings = sc_info.get("warnings", [])
            for w in warnings:
                render_alert(f"<b>[{sc_name}]</b> {w}", type_="warning" if "Guardrail" in w else "info")

    else:
        st.info("Run a simulation above to view projected impacts.")

# ============================================================================
# 5. MULTI-HORIZON TRAJECTORY CHART (7 Days -> 1 Mo -> 3 Mo -> 1 Yr -> 2 Yr)
# ============================================================================
st.markdown("---")
st.subheader("📈 Multi-Horizon Impact Trajectory")
st.caption(
    "Visualizing decision outcomes unfolding across Next 7 Days, 1 Month, 3 Months, 1 Year, and 2 Years."
)

if active_sim and "simulation_result" in active_sim:
    horizon_impacts = active_sim["simulation_result"].get("horizon_impacts", {})

    if horizon_impacts:
        h_keys = ["7_days", "1_month", "3_months", "1_year", "2_years"]
        labels = [horizon_labels[k] for k in h_keys]
        bases = [horizon_impacts[k]["baseline"] for k in h_keys]
        expecteds = [horizon_impacts[k]["expected"] for k in h_keys]
        bests = [horizon_impacts[k]["best"] for k in h_keys]
        worsts = [horizon_impacts[k]["worst"] for k in h_keys]
        unit_str = horizon_impacts["1_month"].get("unit", "")

        fig = go.Figure()

        # Best Case boundary
        fig.add_trace(go.Scatter(
            x=labels,
            y=bests,
            mode='lines+markers',
            name='Best Case',
            line=dict(color='#10B981', width=2, dash='dash'),
            marker=dict(size=7, color='#10B981'),
        ))

        # Expected Case (Primary)
        fig.add_trace(go.Scatter(
            x=labels,
            y=expecteds,
            mode='lines+markers',
            name='Expected Case',
            line=dict(color='#3B82F6', width=4),
            marker=dict(size=9, color='#2563EB'),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.06)',
        ))

        # Baseline Current Path
        fig.add_trace(go.Scatter(
            x=labels,
            y=bases,
            mode='lines+markers',
            name='Current Path (Baseline)',
            line=dict(color='#64748B', width=2, dash='dot'),
            marker=dict(size=6, color='#64748B'),
        ))

        # Worst Case
        fig.add_trace(go.Scatter(
            x=labels,
            y=worsts,
            mode='lines+markers',
            name='Worst Case',
            line=dict(color='#EF4444', width=2, dash='dash'),
            marker=dict(size=7, color='#EF4444'),
            fill='tonexty',
            fillcolor='rgba(239, 68, 68, 0.06)',
        ))

        title_txt = f"{sel_domain} Multi-Horizon Projection Curve ({unit_str})"
        apply_saas_plotly_layout(fig, title_text=title_txt, height=400)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# 6. ALL-HORIZONS COMPARISON MATRIX
# ============================================================================
st.markdown("#### 📊 All Horizons Comparison Matrix")
if active_sim and "simulation_result" in active_sim:
    h_impacts = active_sim["simulation_result"].get("horizon_impacts", {})
    if h_impacts:
        matrix_rows = []
        for hk in ["7_days", "1_month", "3_months", "1_year", "2_years"]:
            hd = h_impacts.get(hk, {})
            u = hd.get("unit", "")
            b = hd.get("baseline", 0.0)
            e = hd.get("expected", 0.0)
            d = hd.get("delta", 0.0)
            
            val_fmt = (lambda v: f"${v:,.0f}" if u == "$" else f"{v:.1f} {u}")
            is_active = "👉 " if hk == sel_horizon else ""

            matrix_rows.append({
                "Horizon": f"{is_active}{horizon_labels.get(hk, hk)}",
                "Baseline Value": val_fmt(b),
                "Expected Value": val_fmt(e),
                "Best Case": val_fmt(hd.get("best", 0.0)),
                "Worst Case": val_fmt(hd.get("worst", 0.0)),
                "Net Impact": f"{'+' if d >= 0 else ''}{val_fmt(d)}",
                "Risk Rating": "Low" if d >= 0 else ("High" if d < -100 else "Medium"),
            })

        matrix_df = pd.DataFrame(matrix_rows)
        st.dataframe(matrix_df, use_container_width=True, hide_index=True)

# ============================================================================
# 7. 5-WAY SCENARIO BREAKDOWN (Selected Horizon)
# ============================================================================
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
with st.expander(f"🔍 5-Way Scenario Details ({horizon_labels.get(sel_horizon)})", expanded=False):
    if active_sim and "predicted_outcome" in active_sim:
        scenarios_dict = active_sim["predicted_outcome"]
        sc_cols = st.columns(len(scenarios_dict))

        for idx, (sc_title, sc_data) in enumerate(scenarios_dict.items()):
            with sc_cols[idx]:
                risk_lvl = sc_data.get("risk_level", "Low")
                risk_color = "#10B981" if risk_lvl == "Low" else ("#EF4444" if risk_lvl in ("High", "Critical") else "#F59E0B")
                outcomes_vals = sc_data.get("projected_outcomes", {})
                first_val = list(outcomes_vals.values())[0] if outcomes_vals else 0.0
                fmt_first = f"${first_val:,.0f}" if isinstance(first_val, (int, float)) and first_val > 100 else f"{first_val}"

                st.markdown(
                    f"""
                    <div style="background: var(--bg-card); border: 1px solid var(--border); border-top: 3px solid {risk_color}; border-radius: 12px; padding: 14px; text-align: center;">
                        <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;">
                            {sc_title}
                        </div>
                        <div style="font-size: 1.4rem; font-weight: 800; color: var(--text-primary); margin: 6px 0;">
                            {fmt_first}
                        </div>
                        <span style="font-size: 0.72rem; font-weight: 700; color: {risk_color}; background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 9999px;">
                            {risk_lvl} Risk
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ============================================================================
# 8. HISTORICAL SIMULATIONS
# ============================================================================
st.markdown("---")
st.subheader("📜 Historical Simulations")

history = APIClient.get("/simulations", params={"limit": 10})
if history:
    if isinstance(history, dict) and "error" in history:
        st.error(history["error"])
    elif isinstance(history, list) and len(history) > 0:
        hist_df = pd.DataFrame([{
            "Date": h.get("generated_at", "")[:10],
            "Domain": h.get("decision_type"),
            "Scenario Name": h.get("scenario_name", "—"),
            "Confidence": f"{int((h.get('confidence_score') or 0.85) * 100)}%",
            "Status": h.get("simulation_result", {}).get("status", "completed")
        } for h in history])
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.write("No historical simulations found.")
