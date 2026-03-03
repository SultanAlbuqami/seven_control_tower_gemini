from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

STATUS_COLORS = {
  "GREEN": "#16a34a",
  "AMBER": "#f59e0b",
  "RED": "#dc2626",
  "OK": "#16a34a",
  "WARN": "#f59e0b",
  "CRIT": "#dc2626",
}

SEVERITY_COLORS = {
  1: "#991b1b",
  2: "#dc2626",
  3: "#f97316",
  4: "#f59e0b",
}


def readiness_scale() -> list[list[float | str]]:
  return [
    [0.00, "#e5e7eb"],
    [0.25, "#e5e7eb"],
    [0.25, STATUS_COLORS["RED"]],
    [0.50, STATUS_COLORS["RED"]],
    [0.50, STATUS_COLORS["AMBER"]],
    [0.75, STATUS_COLORS["AMBER"]],
    [0.75, STATUS_COLORS["GREEN"]],
    [1.00, STATUS_COLORS["GREEN"]],
  ]


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
          .block-container {
            padding-top: 1.25rem;
            padding-bottom: 1.5rem;
            max-width: 1450px;
          }
          [data-testid="stMetric"] {
            border: 1px solid rgba(49, 51, 63, 0.15);
            border-radius: 14px;
            padding: 0.75rem 1rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(248,250,252,0.92) 100%);
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.06);
          }
          [data-testid="stMetricLabel"] {
            font-weight: 600;
          }
          [data-testid="stHorizontalBlock"] > div:has(> [data-testid="stDataFrame"]) {
            border: 1px solid rgba(49, 51, 63, 0.14);
            border-radius: 14px;
            padding: 0.25rem;
            background: #ffffff;
          }
          [data-baseweb="tab-list"] {
            gap: 0.35rem;
          }
          [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 0.35rem 0.8rem;
            border: 1px solid rgba(49, 51, 63, 0.2);
          }
          [data-baseweb="tab"][aria-selected="true"] {
            background: #eef4ff;
            border-color: #84a9ff;
          }
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            line-height: 1.4;
          }
          [data-testid="stExpander"] {
            border-radius: 10px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_plotly(fig: go.Figure, *, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=14, r=14, t=56, b=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title=dict(x=0.02),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.25)")
    return fig
