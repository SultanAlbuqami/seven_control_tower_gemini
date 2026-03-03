from __future__ import annotations

from typing import Any, Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.system_landscape import CORE_BADGE_CATEGORIES, DISCLAIMER

APP_TITLE = "Al Hamra — Operations Readiness Control Tower"
APP_PURPOSE = (
    "Executive control tower for Day-One readiness across ORR gates, evidence, incidents, "
    "vendor commitments, OT alarms, and guest-entry performance."
)
DEMO_MODE_NOTE = (
    "Demo Mode: deterministic synthetic data is auto-generated when any required CSV is missing."
)

THEME = {
    "ink": "#1E252F",
    "ink_soft": "#5C6878",
    "background": "#F5F1EA",
    "surface": "#FFFDFC",
    "surface_alt": "#F0E8DB",
    "border": "#D9CDBB",
    "accent": "#8C5A37",
    "accent_soft": "#E7D6C4",
    "teal": "#2F6F6C",
    "ok": "#1F7A4D",
    "warn": "#B76A16",
    "crit": "#B43C2F",
}

STATUS_COLORS = {
    "GREEN": THEME["ok"],
    "AMBER": THEME["warn"],
    "RED": THEME["crit"],
    "OK": THEME["ok"],
    "WARN": THEME["warn"],
    "CRIT": THEME["crit"],
}

SEVERITY_COLORS = {
    1: "#7F1D1D",
    2: THEME["crit"],
    3: THEME["warn"],
    4: "#C68C39",
}

GUIDE_STEPS = [
    "Overview: establish overall posture and Go/No-Go threshold.",
    "Readiness heatmap: isolate RED gates and ownership.",
    "Evidence pack: chase missing approvals and document refs.",
    "Incidents: review MTTA, MTTR, and SLA discipline.",
    "OT Events: surface unacknowledged critical alarms.",
    "Ticketing KPIs: show scan success, latency, and throughput.",
    "Recommendations: compare Draft preview with Final authoritative output.",
]


def configure_page(page_name: str, *, icon: str = ":material/dashboard:") -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_global_styles()
    render_sidebar(page_name)


def apply_global_styles() -> None:
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

          :root {{
            --ink: {THEME["ink"]};
            --ink-soft: {THEME["ink_soft"]};
            --bg: {THEME["background"]};
            --surface: {THEME["surface"]};
            --surface-alt: {THEME["surface_alt"]};
            --border: {THEME["border"]};
            --accent: {THEME["accent"]};
            --accent-soft: {THEME["accent_soft"]};
            --teal: {THEME["teal"]};
            --ok: {THEME["ok"]};
            --warn: {THEME["warn"]};
            --crit: {THEME["crit"]};
          }}

          html, body, [data-testid="stAppViewContainer"], .stApp {{
            background:
              radial-gradient(circle at top right, rgba(140, 90, 55, 0.10), transparent 28%),
              linear-gradient(180deg, #f8f5ef 0%, var(--bg) 55%, #efe7da 100%);
            color: var(--ink);
            font-family: "IBM Plex Sans", "Aptos", sans-serif;
          }}

          .block-container {{
            padding-top: 1.1rem;
            padding-bottom: 2rem;
            max-width: 1480px;
          }}

          h1, h2, h3 {{
            color: var(--ink) !important;
            letter-spacing: -0.02em;
          }}

          [data-testid="stSidebar"] {{
            background:
              linear-gradient(180deg, rgba(30, 37, 47, 0.98) 0%, rgba(49, 57, 69, 0.98) 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
          }}

          [data-testid="stSidebar"] * {{
            color: #F6F1E8 !important;
          }}

          [data-testid="stAlert"] {{
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.7);
          }}

          [data-testid="stMetric"], .kpi-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(255,252,248,0.97) 100%);
            border: 1px solid rgba(140, 90, 55, 0.16);
            border-radius: 16px;
            box-shadow: 0 10px 28px rgba(30, 37, 47, 0.06);
          }}

          [data-testid="stDataFrame"] {{
            border-radius: 16px;
            border: 1px solid rgba(140, 90, 55, 0.16);
            overflow: hidden;
          }}

          [data-testid="stExpander"] {{
            border: 1px solid rgba(140, 90, 55, 0.16);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.82);
          }}

          .section-header {{
            margin: 0.2rem 0 0.85rem 0;
          }}

          .section-header .eyebrow {{
            color: var(--teal);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
          }}

          .section-header .title {{
            margin-top: 0.1rem;
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 700;
          }}

          .section-header .subtitle {{
            color: var(--ink-soft);
            font-size: 0.92rem;
            margin-top: 0.1rem;
          }}

          .hero {{
            padding: 1.35rem 1.5rem;
            border-radius: 24px;
            border: 1px solid rgba(140, 90, 55, 0.18);
            background:
              linear-gradient(120deg, rgba(255,255,255,0.98) 0%, rgba(248,241,231,0.96) 48%, rgba(231,214,196,0.72) 100%);
            box-shadow: 0 16px 44px rgba(30, 37, 47, 0.08);
            margin-bottom: 1rem;
          }}

          .hero .label {{
            color: var(--teal);
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-weight: 700;
            font-size: 0.78rem;
          }}

          .hero .page {{
            color: var(--ink);
            font-size: 2rem;
            line-height: 1.1;
            font-weight: 700;
            margin-top: 0.2rem;
          }}

          .hero .purpose {{
            color: var(--ink-soft);
            font-size: 0.98rem;
            margin-top: 0.45rem;
            max-width: 68rem;
          }}

          .hero .meta {{
            margin-top: 0.85rem;
            color: var(--ink-soft);
            font-size: 0.84rem;
          }}

          .badge-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 0.9rem;
          }}

          .badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.45rem 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(47, 111, 108, 0.16);
            background: rgba(47, 111, 108, 0.08);
            color: var(--ink);
            font-size: 0.84rem;
            font-weight: 600;
          }}

          .badge .dot {{
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 999px;
            background: var(--teal);
          }}

          .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.38rem 0.68rem;
            border-radius: 999px;
            border: 1px solid rgba(0,0,0,0.08);
            font-size: 0.82rem;
            font-weight: 700;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
            background: rgba(255,255,255,0.86);
          }}

          .status-pill .status-dot {{
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 999px;
          }}

          .kpi-card {{
            padding: 1rem 1.05rem;
            min-height: 8rem;
          }}

          .kpi-title {{
            color: var(--ink-soft);
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
          }}

          .kpi-value {{
            color: var(--ink);
            font-size: 1.9rem;
            font-weight: 700;
            margin-top: 0.45rem;
          }}

          .kpi-subtitle {{
            color: var(--ink-soft);
            font-size: 0.86rem;
            margin-top: 0.45rem;
            line-height: 1.35;
          }}

          .stButton button {{
            border-radius: 999px;
            border: 1px solid rgba(140, 90, 55, 0.28);
            background: linear-gradient(180deg, #9a6540 0%, #7f5130 100%);
            color: #fff !important;
            font-weight: 700;
            box-shadow: 0 8px 20px rgba(140, 90, 55, 0.18);
          }}

          .stDownloadButton button {{
            border-radius: 999px;
          }}

          code, pre {{
            font-family: "IBM Plex Mono", monospace !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(page_name: str) -> None:
    with st.sidebar:
        st.markdown(f"### {APP_TITLE}")
        st.caption(page_name)
        st.info(DEMO_MODE_NOTE)
        st.caption(DISCLAIMER)
        st.markdown("#### 3-minute interview demo")
        for index, step in enumerate(GUIDE_STEPS, start=1):
            st.markdown(f"{index}. {step}")


def render_page_header(page_name: str, description: str) -> None:
    st.markdown(
        f"""
        <section class="hero">
          <div class="label">{APP_TITLE}</div>
          <div class="page">{page_name}</div>
          <div class="purpose">{description}</div>
          <div class="meta">{APP_PURPOSE}</div>
          <div class="meta">{DEMO_MODE_NOTE} {DISCLAIMER}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_landscape_badges()


def render_landscape_badges() -> None:
    badges = "".join(
        f"<div class='badge'><span class='dot'></span><span>{category.badge_label}</span></div>"
        for category in CORE_BADGE_CATEGORIES
    )
    st.markdown(f"<div class='badge-row'>{badges}</div>", unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f"<div class='subtitle'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-header">
          <div class="eyebrow">Control Tower View</div>
          <div class="title">{title}</div>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badges(items: Iterable[dict[str, str] | tuple[str, str]]) -> None:
    chunks: list[str] = []
    for item in items:
        if isinstance(item, dict):
            label = str(item.get("label", "")).strip()
            status = str(item.get("status", "OK")).strip().upper()
        else:
            label, status = str(item[0]).strip(), str(item[1]).strip().upper()
        color = STATUS_COLORS.get(status, THEME["teal"])
        chunks.append(
            "<span class='status-pill'>"
            f"<span class='status-dot' style='background:{color}'></span>"
            f"<span>{label}: {status}</span>"
            "</span>"
        )
    if chunks:
        st.markdown("".join(chunks), unsafe_allow_html=True)


def render_kpi_cards(cards: list[dict[str, Any]]) -> None:
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        status = str(card.get("status", "OK")).upper()
        accent = STATUS_COLORS.get(status, THEME["teal"])
        subtitle = card.get("subtitle", "")
        column.markdown(
            f"""
            <div class="kpi-card" style="border-top: 4px solid {accent};">
              <div class="kpi-title">{card.get("title", "")}</div>
              <div class="kpi-value">{card.get("value", "")}</div>
              <div class="kpi-subtitle">{subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_download_buttons(items: list[dict[str, Any]]) -> None:
    if not items:
        return
    columns = st.columns(len(items))
    for column, item in zip(columns, items):
        with column:
            st.download_button(
                label=str(item["label"]),
                data=item["data"],
                file_name=str(item["file_name"]),
                mime=str(item.get("mime", "text/plain")),
            )


def render_lineage_panel(df: pd.DataFrame, *, title: str, trace_fields: list[str]) -> None:
    render_section_header(title, "Source labels and trace references used on this page.")
    if df.empty:
        st.info("No records available for lineage.")
        return
    columns = [column for column in ["source_system", *trace_fields] if column in df.columns]
    lineage = df[columns].drop_duplicates().head(8).copy()
    st.dataframe(format_table(lineage), use_container_width=True, hide_index=True)
    traces: list[str] = []
    for column in trace_fields:
        if column in df.columns:
            values = [str(value) for value in df[column].dropna().astype(str).head(5).tolist() if str(value).strip()]
            if values:
                traces.append(f"{column}: {', '.join(values)}")
    if traces:
        st.code("\n".join(traces), language="text")


def format_timestamp(value: Any) -> str:
    if pd.isna(value):
        return "-"
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return str(value)
    return ts.tz_convert("UTC").strftime("%Y-%m-%d %H:%M UTC")


def format_percent(value: Any, *, digits: int = 1, assume_ratio: bool = False) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value)
    if assume_ratio:
        numeric *= 100.0
    return f"{numeric:.{digits}f}%"


def format_minutes(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.0f} min"


def format_table(df: pd.DataFrame) -> pd.DataFrame:
    formatted = df.copy()
    for column in formatted.columns:
        if pd.api.types.is_datetime64_any_dtype(formatted[column]):
            formatted[column] = formatted[column].map(format_timestamp)
    return formatted


def readiness_scale() -> list[list[float | str]]:
    return [
        [0.00, "#F3D7D3"],
        [0.33, "#F3D7D3"],
        [0.33, "#F2D9B4"],
        [0.66, "#F2D9B4"],
        [0.66, "#C8E2D4"],
        [1.00, "#C8E2D4"],
    ]


def style_plotly(fig: go.Figure, *, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.18)",
        margin=dict(l=24, r=24, t=60, b=24),
        font=dict(family="IBM Plex Sans, Aptos, sans-serif", color=THEME["ink_soft"], size=12),
        title=dict(x=0.01, font=dict(color=THEME["ink"], size=15)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(30,37,47,0.12)")
    fig.update_yaxes(gridcolor="rgba(30,37,47,0.08)", linecolor="rgba(30,37,47,0.12)")
    return fig
