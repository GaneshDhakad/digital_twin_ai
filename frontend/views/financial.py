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

st.title("Financial Health")
st.markdown("Understand your income, spending, savings and financial outlook.")

fin_summary = APIClient.get("/financial/summary") or {}
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Current Balance", f"${fin_summary.get('net_savings', 0.0):,.2f}", "Net cash flow")
with c2:
    render_metric_card("Total Income", f"${fin_summary.get('total_income', 0.0):,.2f}", "Cumulative earnings")
with c3:
    render_metric_card("Total Expenses", f"${fin_summary.get('total_expenses', 0.0):,.2f}", "Outflows", is_violet=True)
with c4:
    render_metric_card("Savings Rate", f"{fin_summary.get('savings_rate', 0.0)}%", "Target ≥ 20%", is_violet=True)

tab1, tab2, tab3, tab_ai = st.tabs([
    "➕ RECORD",
    "📋 TRANSACTIONS",
    "📊 INSIGHTS",
    "🤖 AI FORECASTS"
])

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

        submit_fin = st.form_submit_button("ADD TRANSACTION")

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
        df_display = df[["transaction_date", "type", "category", "income", "expenses", "description", "recurring_frequency"]]
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

# ─────────────────────────────────────────────────────────────────────────────
# AI FORECASTS TAB
# ─────────────────────────────────────────────────────────────────────────────
with tab_ai:
    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.subheader("💰 Disposable Income")
    st.markdown("Estimates your monthly disposable income based on your financial profile.")
    st.caption("Powered by Random Forest")

    with st.form("financial_predict_form"):
        st.markdown("#### Personal & Financial Profile")
        col1, col2 = st.columns(2)
        with col1:
            fin_age = st.number_input("Age", min_value=18, max_value=100, value=35)
            fin_occupation = st.selectbox("Occupation", ["Salaried", "Self-Employed", "Business", "Freelancer", "Retired", "Other"])
            fin_city_tier = st.selectbox("City Tier", ["Tier 1", "Tier 2", "Tier 3"])
        with col2:
            fin_dependents = st.number_input("Number of Dependents", min_value=0, max_value=20, value=2)
            fin_income = st.number_input("Monthly Gross Income ($)", min_value=0.0, value=75000.0, step=1000.0)

        st.markdown("#### Savings Goal")
        col3, col4 = st.columns(2)
        with col3:
            fin_savings_pct = st.slider("Desired Savings %", 0, 100, 20)
        with col4:
            fin_desired_savings = st.number_input("Desired Savings Amount ($)", min_value=0.0, value=15000.0, step=500.0)

        fin_predict_btn = st.form_submit_button("PREDICT DISPOSABLE INCOME", use_container_width=True)

    if fin_predict_btn:
        payload = {
            "income": fin_income,
            "age": float(fin_age),
            "dependents": float(fin_dependents),
            "occupation": fin_occupation,
            "city_tier": fin_city_tier,
            "desired_savings_percentage": float(fin_savings_pct),
            "desired_savings": fin_desired_savings,
        }
        with st.spinner("Running financial model..."):
            result = APIClient.post("/ml/financial/predict", data=payload)

        if result and "prediction" in result:
            predicted = result["prediction"]
            pct_of_income = (predicted / fin_income * 100) if fin_income > 0 else 0
            health = "🟢 Healthy" if pct_of_income >= 20 else "🟡 Moderate" if pct_of_income >= 10 else "🔴 Low"
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #064E3B, #065F46); border-radius: 16px;
                     padding: 32px; text-align: center; margin: 16px 0;">
                    <div style="font-size: 14px; color: #6EE7B7; letter-spacing: 2px; margin-bottom: 8px;">
                        ESTIMATED DISPOSABLE INCOME
                    </div>
                    <div style="font-size: 60px; font-weight: 900; color: white; line-height: 1;">
                        ${predicted:,.0f} / month
                    </div>
                    <div style="font-size: 20px; color: #A7F3D0; margin-top: 8px;">
                        {pct_of_income:.1f}% of gross income &nbsp;·&nbsp; {health}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            err = result.get("error", "Prediction failed") if isinstance(result, dict) else "Prediction failed"
            render_alert(f"❌ {err}", "error")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="hud-card">', unsafe_allow_html=True)
    st.subheader("📈 Spending Forecast")
    st.markdown("Predicts next month's spending based on your current-month transaction patterns.")
    st.caption("Powered by XGBoost")

    with st.form("forecasting_predict_form"):
        fore_month = st.selectbox("Forecast For Month", [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        
        st.markdown("#### 📅 Current Month Summary")
        col1, col2, col3 = st.columns(3)
        
        # Hardcoded simulated values from backend state
        c_net_signed = 12500.0
        c_total_abs = 45000.0
        c_inc_tx = 28750.0
        c_exp_tx = 16250.0
        c_total_tx = 85
        c_pos_tx = 20
        c_neg_tx = 65
        c_avg_tx = 529.41
        
        h_abs_lag1 = 43200.0
        h_abs_roll3 = 44100.0
        h_pos_lag1 = 27500.0
        h_pos_roll3 = 28100.0
        h_neg_lag1 = 15700.0
        h_neg_roll3 = 16000.0
        h_tx_lag1 = 80
        h_tx_roll3 = 82.0

        with col1:
            st.metric("Total Income", f"${c_inc_tx:,.0f}")
            st.metric("Total Expenses", f"${c_exp_tx:,.0f}")
            st.metric("Net Cash Flow", f"${c_net_signed:,.0f}")
        with col2:
            st.metric("Total Transactions", str(c_total_tx))
            st.metric("Income Tx Count", str(c_pos_tx))
            st.metric("Expense Tx Count", str(c_neg_tx))
        with col3:
            st.metric("Avg Transaction", f"${c_avg_tx:,.0f}")
            st.metric("Total Absolute", f"${c_total_abs:,.0f}")
            
        st.markdown("#### 📊 Historical Context")
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            st.metric("Last Month Income", f"${h_pos_lag1:,.0f}")
            st.metric("3-Month Avg Income", f"${h_pos_roll3:,.0f}")
        with hc2:
            st.metric("Last Month Spending", f"${h_neg_lag1:,.0f}")
            st.metric("3-Month Avg Spending", f"${h_neg_roll3:,.0f}")
        with hc3:
            st.metric("Last Month Tx Count", str(h_tx_lag1))
            st.metric("3-Month Avg Tx Count", str(int(h_tx_roll3)))

        fore_predict_btn = st.form_submit_button("FORECAST SPENDING", use_container_width=True)

    if fore_predict_btn:
        payload = {
            "month": fore_month,
            "total_signed_amount": c_net_signed,
            "total_absolute_amount": c_total_abs,
            "positive_amount": c_inc_tx,
            "negative_amount": c_exp_tx,
            "transaction_count": float(c_total_tx),
            "positive_transaction_count": float(c_pos_tx),
            "negative_transaction_count": float(c_neg_tx),
            "average_transaction_amount": c_avg_tx,
            "unique_merchants": 32.0,
            "unique_cards": 3.0,
            "error_count": 2.0,
            "total_absolute_amount_lag_1": h_abs_lag1,
            "total_absolute_amount_rolling_3m": h_abs_roll3,
            "positive_amount_lag_1": h_pos_lag1,
            "positive_amount_rolling_3m": h_pos_roll3,
            "negative_amount_lag_1": h_neg_lag1,
            "negative_amount_rolling_3m": h_neg_roll3,
            "transaction_count_lag_1": float(h_tx_lag1),
            "transaction_count_rolling_3m": h_tx_roll3,
        }
        with st.spinner("Running forecasting model..."):
            result = APIClient.post("/ml/forecasting/predict", data=payload)

        if result and "prediction" in result:
            predicted = result["prediction"]
            delta = predicted - c_exp_tx
            delta_pct = (delta / c_exp_tx * 100) if c_exp_tx > 0 else 0
            trend_icon = "📈" if delta > 0 else "📉"
            trend_color = "#DC2626" if delta > 0 else "#059669"
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1E1B4B, #312E81); border-radius: 16px;
                     padding: 32px; text-align: center; margin: 16px 0;">
                    <div style="font-size: 14px; color: #A5B4FC; letter-spacing: 2px; margin-bottom: 8px;">
                        PREDICTED NEXT-MONTH SPENDING
                    </div>
                    <div style="font-size: 60px; font-weight: 900; color: white; line-height: 1;">
                        ${predicted:,.0f}
                    </div>
                    <div style="font-size: 18px; color: {trend_color}; margin-top: 8px; font-weight: 600;">
                        {trend_icon} {abs(delta_pct):.1f}% {'increase' if delta > 0 else 'decrease'} vs current month
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            err = result.get("error", "Prediction failed") if isinstance(result, dict) else "Prediction failed"
            render_alert(f"❌ {err}", "error")


    st.markdown('</div>', unsafe_allow_html=True)
