import streamlit as st

def render_metric_card(title: str, value: str, subtitle: str = "", is_violet: bool = False):
    """Renders a standard HUD card (backward compatible)."""
    card_class = "hud-card-violet" if is_violet else "hud-card"
    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="hud-metric-label">{title}</div>
            <div class="hud-metric-val">{value}</div>
            <div class="hud-metric-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    change: str = "",
    trend: str = "up",
    icon: str = "📊"
):
    """
    Renders an Apple + Stripe + Notion inspired SaaS KPI card.
    Features:
      - 16px border-radius white container with soft shadow and hover elevation
      - Colored icon indicator badge
      - Large bold numeric value
      - Trend indicator badge (green 'up', red 'down', blue 'neutral')
      - Secondary descriptive label
    """
    trend_class = trend.lower()
    if trend_class not in ("up", "down", "neutral"):
        trend_class = "neutral"

    trend_html = f'<span class="kpi-trend {trend_class}">{change}</span>' if change else ""
    subtitle_html = f'<span class="kpi-sub">{subtitle}</span>' if subtitle else ""

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                <span>{title}</span>
                <span style="font-size: 1.1rem;">{icon}</span>
            </div>
            <div class="kpi-val">{value}</div>
            <div style="display: flex; align-items: center; margin-top: 6px;">
                {trend_html}
                {subtitle_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
