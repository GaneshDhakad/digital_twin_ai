import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme
from frontend.utils.api_client import APIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.metrics_card import render_metric_card
from frontend.components.alerts import render_alert

apply_stitch_theme()

if not st.session_state.get("authenticated"):
    st.warning("Authentication required. Redirecting to login...")
    st.rerun()

render_sidebar()

st.title("Financial Data Management & Health Ledger")
st.markdown("Record transactions, review income/expense breakdown, and analyze net savings rate.")

fin_summary = APIClient.get("/financial/summary") or {}
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Total Income", f"${fin_summary.get('total_income', 0.0):,.2f}", "Cumulative earnings")
with c2:
    render_metric_card("Total Expenses", f"${fin_summary.get('total_expenses', 0.0):,.2f}", "Outflows", is_violet=True)
with c3:
    render_metric_card("Net Savings", f"${fin_summary.get('net_savings', 0.0):,.2f}", "Retained capital")
with c4:
    render_metric_card("Savings Rate", f"{fin_summary.get('savings_rate', 0.0)}%", "Target ≥ 20%", is_violet=True)

tab1, tab2, tab3 = st.tabs(["ADD NEW RECORD", "TRANSACTION TABLE", "SPENDING INSIGHTS"])

with tab1:
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.subheader("Log Financial Entry")
    with st.form("financial_entry_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            rec_type = st.selectbox("Record Type", ["expense", "income"])
            amount = st.number_input("Amount ($)", min_value=0.01, step=10.0, value=150.0)
            category = st.selectbox(
                "Category",
                ["Housing", "Food", "Transport", "Education", "Entertainment", "Healthcare", "Investment", "Salary", "Freelance", "Other"]
            )
        with col_b:
            description = st.text_input("Description", placeholder="e.g. Monthly Grocery / Salary deposit")
            recurring = st.selectbox("Recurring Frequency", ["None", "Daily", "Weekly", "Monthly", "Annual"])

        submit_fin = st.form_submit_button("SUBMIT TRANSACTION")

        if submit_fin:
            payload = {
                "type": rec_type,
                "amount": float(amount),
                "category": category,
                "description": description,
                "recurring_frequency": recurring,
            }
            res = APIClient.post("/financial/records", data=payload)
            if isinstance(res, dict) and "record_id" in res:
                render_alert("Transaction logged successfully!", "success")
                st.rerun()
            else:
                err = res.get("error", "Error saving record") if isinstance(res, dict) else "Error saving record"
                render_alert(f"Failed to log transaction: {err}", "error")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.subheader("Financial Records Table")
    
    records = APIClient.get("/financial/records") or []
    if not records:
        render_alert("No financial records found. Add your first record in the tab above!", "info")
    else:
        df = pd.DataFrame(records)
        df_display = df[["record_id", "transaction_date", "type", "category", "income", "expenses", "description", "recurring_frequency"]]
        st.dataframe(df_display, use_container_width=True)

        st.markdown("#### Delete Record")
        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            record_to_del = st.selectbox("Select Record ID to Delete", [r["record_id"] for r in records])
        with del_col2:
            st.write("")
            st.write("")
            if st.button("DELETE RECORD"):
                res = APIClient.delete(f"/financial/records/{record_to_del}")
                render_alert("Record deleted!", "success")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="hud-card-violet">', unsafe_allow_html=True)
    st.subheader("Category Breakdown & Monthly Trend")
    cat_data = fin_summary.get("category_breakdown", {})
    if cat_data:
        cat_df = pd.DataFrame([{"Category": k, "Expenses": v} for k, v in cat_data.items()])
        fig = px.pie(cat_df, values="Expenses", names="Category", title="Expense Category Distribution", hole=0.4, color_discrete_sequence=px.colors.sequential.Blues)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#0F172A")
        st.plotly_chart(fig, use_container_width=True)
    else:
        render_alert("Insufficient data for category chart.", "info")
    st.markdown('</div>', unsafe_allow_html=True)
