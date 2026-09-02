import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme
from frontend.components.sidebar import render_sidebar
from frontend.utils.api_client import APIClient

apply_stitch_theme()

if not st.session_state.get("authenticated"):
    st.warning("Authentication required. Redirecting to login...")
    st.rerun()

render_sidebar()

st.title("Decision Simulation Engine")
st.markdown("9-Category decision simulator with 5-way scenario projection (Current Path, Best, Expected, Worst, Risk).")

categories = ["Financial", "Study", "Career", "Fitness", "Lifestyle", "Investment", "Loan", "Emergency Scenario", "Custom Scenario"]

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("New Simulation")
    sel_cat = st.selectbox("Decision Category", categories)
    
    impact = st.number_input("Estimated Impact (Score / $ / Hours)", value=50)
    extra_param = st.text_input("Additional Parameters (optional)")
    
    if st.button("🔮 Run Simulation", use_container_width=True):
        with st.spinner("Running Monte Carlo Simulation..."):
            req_data = {
                "decision_type": sel_cat,
                "input_parameters": {"impact": impact, "extra": extra_param, "extra_expense": impact if sel_cat == "Financial" else 0}
            }
            res = APIClient.post("/simulations", data=req_data)
            if res and "error" not in res:
                st.session_state["last_sim"] = res
                st.success("Simulation Complete!")
            else:
                st.error(f"Simulation failed: {res.get('error') if res else 'Unknown'}")

with col2:
    st.subheader("Simulation Results")
    last_sim = st.session_state.get("last_sim")
    if last_sim:
        st.markdown(f"**Category:** {last_sim.get('decision_type')} | **Confidence:** {last_sim.get('confidence_score')}")
        outcomes = last_sim.get("predicted_outcome", {})
        
        # Render 5-way scenarios
        if outcomes:
            df_data = []
            for sc_name, sc_data in outcomes.items():
                val = list(sc_data.get("projected_outcomes", {}).values())[0] if sc_data.get("projected_outcomes") else 0
                df_data.append({"Scenario": sc_name, "Value": val, "Risk": sc_data.get("risk_level")})
                
                # Show warnings
                warnings = sc_data.get("warnings", [])
                for w in warnings:
                    st.warning(f"[{sc_name}] {w}")
            
            df = pd.DataFrame(df_data)
            
            # Simple bar chart
            fig = px.bar(df, x="Scenario", y="Value", color="Risk", title="5-Way Scenario Projection")
            st.plotly_chart(fig, use_container_width=True)
            
            # Table view
            st.dataframe(df, use_container_width=True)
    else:
        st.info("Run a simulation to view results.")

st.markdown("---")
st.subheader("Historical Simulations")
history = APIClient.get("/simulations", params={"limit": 10})
if history:
    if isinstance(history, dict) and "error" in history:
        st.error(history["error"])
    elif isinstance(history, list) and len(history) > 0:
        hist_df = pd.DataFrame([{
            "Date": h.get("generated_at", "")[:10],
            "Category": h.get("decision_type"),
            "Status": h.get("simulation_result", {}).get("status", "unknown")
        } for h in history])
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.write("No historical simulations found.")
