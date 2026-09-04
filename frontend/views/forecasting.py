import streamlit as st
import sys
from pathlib import Path


# ============================================================================
# PROJECT ROOT
# ============================================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ============================================================================
# IMPORTS
# ============================================================================

from frontend.theme.styles import apply_stitch_theme
from frontend.utils.api_client import APIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.alerts import render_alert


# ============================================================================
# THEME
# ============================================================================

apply_stitch_theme()


# ============================================================================
# AUTHENTICATION
# ============================================================================

if not st.session_state.get("authenticated"):
    st.warning("Authentication required. Redirecting to login...")
    st.rerun()


# ============================================================================
# SIDEBAR
# ============================================================================

render_sidebar()


# ============================================================================
# PAGE HEADER
# ============================================================================

st.title("AI Forecasting")

st.markdown(
    "What is likely to happen? Your cross-domain predictions and likely future states based on historical data."
)

st.markdown("---")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_numeric_prediction(value):
    """
    Safely extract a numeric prediction from different possible API formats.

    Supported examples:

        87.5
        "87.5"
        {"value": 87.5}
        {"prediction": 87.5}
        {"value": "87.5"}

    Returns:
        float | None
    """

    if value is None:
        return None

    # Already numeric
    if isinstance(value, (int, float)):
        return float(value)

    # String containing a number
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None

    # Dictionary returned by API
    if isinstance(value, dict):

        # Most likely formats
        for key in ("value", "prediction", "score", "result"):

            if key in value:
                result = extract_numeric_prediction(value[key])

                if result is not None:
                    return result

        return None

    return None


def get_timestamp(data):
    """Safely get a date portion from an API timestamp."""

    if not isinstance(data, dict):
        return "—"

    timestamp = data.get("timestamp")

    if timestamp is None:
        return "—"

    return str(timestamp)[:10]


# ============================================================================
# LIVE MODEL STATUS
# ============================================================================

with st.expander("🔧 Model Status", expanded=False):

    status = APIClient.get("/ml/models")

    if status:

        cols = st.columns(4)

        domains = [
            "academic",
            "lifestyle",
            "financial",
            "forecasting",
        ]

        for i, domain in enumerate(domains):

            with cols[i]:

                info = status.get(domain, {})

                if not isinstance(info, dict):
                    info = {}

                available = info.get("available", False)

                icon = "🟢" if available else "🔴"

                st.markdown(
                    f"**{icon} {domain.title()}**"
                )

                if available:

                    st.caption(
                        f"Model: {info.get('model', 'Unknown')}"
                    )

                    st.caption(
                        f"Target: {info.get('target', '—')}"
                    )

                else:

                    st.caption("Not available")

    else:

        st.warning(
            "Unable to retrieve model status from the backend."
        )


# ============================================================================
# DIGITAL TWIN STATE
# ============================================================================

st.markdown("---")

st.subheader("🔮 Cross-Domain Forecasting")

st.markdown(
    "Likely future outcomes across your life domains."
)


# ============================================================================
# GET DIGITAL TWIN
# ============================================================================

twin_state = APIClient.get("/ml/digital-twin")


if not twin_state:
    twin_state = {}

if not isinstance(twin_state, dict):
    st.error("Invalid Digital Twin response received from backend.")
    twin_state = {}

ml_preds = twin_state.get("ml_predictions", {})

# ============================================================================
# TWO-COLUMN LAYOUT
# ============================================================================

col1, col2 = st.columns(2)


# ============================================================================
# LEFT COLUMN
# ============================================================================

with col1:

    # ========================================================================
    # ACADEMIC
    # ========================================================================

    acad = ml_preds.get("academic")

    st.markdown(
        '<div class="hud-card">',
        unsafe_allow_html=True
    )

    st.markdown("#### 🎓 Academic")

    if acad and isinstance(acad, dict):

        raw_prediction = acad.get("prediction")

        score = extract_numeric_prediction(raw_prediction)

        # ---------------------------------------------------------------
        # Valid prediction
        # ---------------------------------------------------------------

        if score is not None:

            # Keep score within sensible exam-score range
            # without modifying the actual model prediction.
            display_score = max(0.0, min(100.0, score))

            grade = (
                "A+" if display_score >= 90
                else "A" if display_score >= 80
                else "B" if display_score >= 70
                else "C" if display_score >= 60
                else "D"
            )

            st.metric(
                "Predicted Exam Score",
                f"{display_score:.1f}%",
                delta=f"Grade: {grade}"
            )

        # ---------------------------------------------------------------
        # Invalid / missing prediction
        # ---------------------------------------------------------------

        else:
            status = acad.get("status")
            if status == "insufficient_data":
                render_alert("Insufficient data to generate prediction. Please add more profile data.", "info")
            elif status == "model_unavailable":
                render_alert("Model is currently unavailable.", "warning")
            else:
                st.error("Academic prediction could not be converted to a number.")
                st.caption(f"Backend returned: {raw_prediction!r}")

        if acad.get("status") == "available":
            st.caption(
                f"Model: {acad.get('model_name', '—')} · "
                f"{get_timestamp(acad)}"
            )

    else:

        render_alert(
            "No academic prediction yet. "
            "Run a prediction from the Study page.",
            "info"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    # ========================================================================
    # FINANCIAL
    # ========================================================================

    fin = ml_preds.get("financial")

    st.markdown(
        '<div class="hud-card">',
        unsafe_allow_html=True
    )

    st.markdown("#### 💰 Financial")

    if fin and isinstance(fin, dict):

        raw_income = fin.get("prediction")

        income = extract_numeric_prediction(raw_income)

        if income is not None:

            st.metric(
                "Expected Disposable Income",
                f"${income:,.0f}"
            )

        else:
            status = fin.get("status")
            if status == "insufficient_data":
                render_alert("Insufficient data to generate prediction.", "info")
            elif status == "model_unavailable":
                render_alert("Model is currently unavailable.", "warning")
            else:
                st.error("Financial prediction could not be converted to a number.")
                st.caption(f"Backend returned: {raw_income!r}")

        if fin.get("status") == "available":
            st.caption(
                f"Model: {fin.get('model_name', '—')} · "
                f"{get_timestamp(fin)}"
            )

    else:

        render_alert(
            "No financial prediction yet. "
            "Use the Financial page AI tab.",
            "info"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================================
# RIGHT COLUMN
# ============================================================================

with col2:

    # ========================================================================
    # LIFESTYLE
    # ========================================================================

    life = ml_preds.get("lifestyle")

    st.markdown(
        '<div class="hud-card">',
        unsafe_allow_html=True
    )

    st.markdown("#### 😴 Lifestyle / Sleep")

    if life and isinstance(life, dict):

        status = life.get("status")
        if status == "insufficient_data":
            render_alert("Insufficient data to generate prediction.", "info")
        elif status == "model_unavailable":
            render_alert("Model is currently unavailable.", "warning")
        else:
            raw_disorder = life.get("prediction", "—")
            disorder = str(raw_disorder)

            # Handle common representations of no disorder
            no_disorder_values = {
                "none", "no", "no disorder", "no_disorder", "false", "0",
            }

            icon = "✅" if disorder.strip().lower() in no_disorder_values else "⚠️"
            st.metric("Projected Sleep Disorder Risk", f"{icon} {disorder}")

        if life.get("status") == "available":
            st.caption(
                f"Model: {life.get('model_name', '—')} · "
                f"{get_timestamp(life)}"
            )

    else:

        render_alert(
            "No lifestyle prediction yet. "
            "Use the Habits page AI tab.",
            "info"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


    # ========================================================================
    # FORECASTING
    # ========================================================================

    fore = ml_preds.get("forecasting")

    st.markdown(
        '<div class="hud-card-violet">',
        unsafe_allow_html=True
    )

    st.markdown("#### 📈 Spending Forecast")

    if fore and isinstance(fore, dict):

        raw_spending = fore.get("prediction")

        spending = extract_numeric_prediction(raw_spending)

        if spending is not None:

            st.metric(
                "Projected Next Month Spending",
                f"${spending:,.0f}"
            )

        else:
            status = fore.get("status")
            if status == "insufficient_data":
                render_alert("Insufficient data to generate forecast.", "info")
            elif status == "model_unavailable":
                render_alert("Model is currently unavailable.", "warning")
            else:
                st.error("Forecasting prediction could not be converted to a number.")
                st.caption(f"Backend returned: {raw_spending!r}")

        if fore.get("status") == "available":
            st.caption(
                f"Model: {fore.get('model_name', '—')} · "
                f"{get_timestamp(fore)}"
            )

    else:

        render_alert(
            "No forecast yet. "
            "Use the Financial page Forecast AI tab.",
            "info"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )




# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")

st.caption(
    "Predictions are cached for 24h (12h for forecasting). "
    "Run new predictions from their respective pages to refresh."
)