from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

# ── Professional Control Tower Palette ────────────────────────────────────────
# Deep navy primary, vivid teal accent, clean grays, status colors with depth

STATUS_COLORS = {
  "GREEN": "#059669",
  "AMBER": "#d97706",
  "RED": "#dc2626",
  "OK": "#059669",
  "WARN": "#d97706",
  "CRIT": "#dc2626",
}

SEVERITY_COLORS = {
  1: "#991b1b",
  2: "#dc2626",
  3: "#ea580c",
  4: "#d97706",
}

# Brand palette — enterprise control tower theme
BRAND = {
  "primary": "#0f172a",       # Slate-900 — deep navy
  "primary_mid": "#1e293b",   # Slate-800
  "accent": "#0d9488",        # Teal-600 — vivid teal accent
  "accent_light": "#5eead4",  # Teal-300
  "accent_bg": "#f0fdfa",     # Teal-50
  "bg": "#f8fafc",            # Slate-50 — clean background
  "surface": "#ffffff",       # Card surface
  "muted": "#64748b",         # Slate-500
  "muted_light": "#94a3b8",   # Slate-400
  "border": "rgba(15, 23, 42, 0.08)",
  "highlight": "#3b82f6",     # Blue-500 — info accent
  "success": "#059669",       # Emerald-600
  "warning": "#d97706",       # Amber-600
  "danger": "#dc2626",        # Red-600
}

# Chart color palette — professional and distinct
CHART_PALETTE = [
  "#0d9488",   # Teal-600
  "#3b82f6",   # Blue-500
  "#8b5cf6",   # Violet-500
  "#f59e0b",   # Amber-500
  "#ef4444",   # Red-500
  "#06b6d4",   # Cyan-500
  "#ec4899",   # Pink-500
  "#10b981",   # Emerald-500
]

FONT_STACK = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"


def render_color_legend() -> None:
  cols = st.columns(6)
  labels = [
    ("GREEN", "Services OK"),
    ("AMBER", "Attention"),
    ("RED", "Critical"),
    ("OK", "Metric OK"),
    ("WARN", "Metric Warn"),
    ("CRIT", "Metric Crit"),
  ]
  for col, (k, txt) in zip(cols, labels):
    col.markdown(
      f"<div style='display:flex;align-items:center;gap:8px;padding:4px 0'>"
      f"<div style='width:12px;height:12px;border-radius:3px;background:{STATUS_COLORS[k]};box-shadow:0 0 0 2px {STATUS_COLORS[k]}22;'></div>"
      f"<div style='color:{BRAND['muted']};font-size:12px;font-weight:500;letter-spacing:0.01em'>{txt}</div>"
      f"</div>",
      unsafe_allow_html=True,
    )


def render_theme_settings() -> None:
  """Render theme selector in the sidebar and persist choice to session state."""
  if "theme_choice" not in st.session_state:
    st.session_state["theme_choice"] = "Light"

  with st.sidebar:
    st.subheader("Theme")
    choice = st.selectbox("UI Theme", ["Light", "Dark", "Brand Blue"], index=["Light", "Dark", "Brand Blue"].index(st.session_state["theme_choice"]))
    if choice != st.session_state["theme_choice"]:
      st.session_state["theme_choice"] = choice
      apply_global_styles()


ICONS = {
  "check": "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M20 6L9 17L4 12' stroke='white' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/></svg>",
  "alert": "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z' fill='white' stroke='none'/><path d='M12 9v4' stroke='rgba(0,0,0,0.7)' stroke-width='2' stroke-linecap='round'/><circle cx='12' cy='17' r='1' fill='rgba(0,0,0,0.7)'/></svg>",
  "doc": "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' fill='white' stroke='none'/><path d='M14 2v6h6' stroke='rgba(0,0,0,0.3)' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/><path d='M8 13h8M8 17h6' stroke='rgba(0,0,0,0.35)' stroke-width='1.5' stroke-linecap='round'/></svg>",
  "trend_up": "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M23 6l-9.5 9.5-5-5L1 18' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/><path d='M17 6h6v6' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>",
  "shield": "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z' fill='white' stroke='none'/><path d='M9 12l2 2 4-4' stroke='rgba(0,0,0,0.5)' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>",
}

# KPI card icon background gradients
_ICON_GRADIENTS = {
    "#fff4f4": "linear-gradient(135deg, #fecaca 0%, #fca5a5 100%)",  # Red tones
    "#fff7e6": "linear-gradient(135deg, #fde68a 0%, #fbbf24 100%)",  # Amber tones
    "#effff4": "linear-gradient(135deg, #a7f3d0 0%, #6ee7b7 100%)",  # Green tones
    "#eef6ff": "linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%)",  # Blue tones
    "#fff7f0": "linear-gradient(135deg, #fed7aa 0%, #fdba74 100%)",  # Orange tones
    "#ffe9e9": "linear-gradient(135deg, #fecaca 0%, #f87171 100%)",  # Deep red
}


def render_kpi_card(title: str, value: str | int | float, *, delta: str | None = None, icon: str | None = None, color: str | None = None) -> None:
  """Render a modern KPI card with gradient icon background and optional delta."""
  icon_html = ICONS.get(icon, "") if icon else ""
  delta_html = ""
  if delta:
    delta_color = BRAND["danger"] if "⚠" in str(delta) else BRAND["muted"]
    delta_html = f"<div style='color:{delta_color};font-size:11px;font-weight:600;letter-spacing:0.02em;margin-top:2px'>{delta}</div>"

  icon_gradient = _ICON_GRADIENTS.get(color, f"linear-gradient(135deg, {BRAND['accent']}44 0%, {BRAND['accent']}88 100%)") if color else f"linear-gradient(135deg, {BRAND['accent']}44 0%, {BRAND['accent']}88 100%)"

  st.markdown(
    f"<div class='kpi-card' style='"
    f"display:flex;align-items:center;gap:14px;padding:14px 16px;"
    f"border-radius:12px;border:1px solid {BRAND['border']};"
    f"background:{BRAND['surface']};"
    f"box-shadow:0 1px 3px rgba(15,23,42,0.04),0 4px 12px rgba(15,23,42,0.03);'>"
    f"<div style='"
    f"width:42px;height:42px;border-radius:10px;"
    f"display:flex;align-items:center;justify-content:center;"
    f"background:{icon_gradient};flex-shrink:0;"
    f"box-shadow:0 2px 6px rgba(15,23,42,0.08);'>"
    f"{icon_html}"
    f"</div>"
    f"<div style='display:flex;flex-direction:column;min-width:0'>"
    f"<div style='font-size:11.5px;color:{BRAND['muted']};font-weight:600;text-transform:uppercase;letter-spacing:0.04em;line-height:1.2'>{title}</div>"
    f"<div style='font-size:22px;color:{BRAND['primary']};font-weight:700;line-height:1.3;letter-spacing:-0.01em'>{value}</div>"
    f"{delta_html}"
    f"</div>"
    f"</div>",
    unsafe_allow_html=True,
  )

def readiness_scale() -> list[list[float | str]]:
  return [
    [0.00, "#e2e8f0"],
    [0.25, "#e2e8f0"],
    [0.25, "#ef4444"],
    [0.50, "#ef4444"],
    [0.50, "#f59e0b"],
    [0.75, "#f59e0b"],
    [0.75, "#059669"],
    [1.00, "#059669"],
  ]


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

          :root {
            --brand-primary: %(primary)s;
            --brand-primary-mid: %(primary_mid)s;
            --brand-accent: %(accent)s;
            --brand-accent-light: %(accent_light)s;
            --brand-muted: %(muted)s;
            --brand-bg: %(bg)s;
            --brand-surface: %(surface)s;
            --brand-border: %(border)s;
          }

          .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1480px;
            font-family: %(font)s;
            background: var(--brand-bg);
          }

          /* Titles */
          h1 {
            color: var(--brand-primary) !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
          }
          h2, h3 {
            color: var(--brand-primary) !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em !important;
          }

          /* KPI Cards */
          .kpi-card {
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .kpi-card:hover {
            box-shadow: 0 4px 16px rgba(15,23,42,0.08), 0 8px 24px rgba(15,23,42,0.04) !important;
            transform: translateY(-1px);
          }

          /* Native Streamlit Metric Cards */
          [data-testid="stMetric"] {
            border: 1px solid var(--brand-border);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            background: var(--brand-surface);
            box-shadow: 0 1px 3px rgba(15,23,42,0.04), 0 4px 12px rgba(15,23,42,0.03);
            transition: all 0.2s ease;
          }
          [data-testid="stMetric"]:hover {
            box-shadow: 0 4px 16px rgba(15,23,42,0.08);
          }
          [data-testid="stMetricLabel"] {
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--brand-muted);
          }
          [data-testid="stMetricValue"] {
            font-weight: 700;
            color: var(--brand-primary);
          }

          /* Data frames */
          [data-testid="stHorizontalBlock"] > div:has(> [data-testid="stDataFrame"]) {
            border: 1px solid var(--brand-border);
            border-radius: 12px;
            padding: 2px;
            background: var(--brand-surface);
            box-shadow: 0 1px 3px rgba(15,23,42,0.04);
          }

          /* Tabs */
          [data-baseweb="tab-list"] {
            gap: 0.4rem;
          }
          [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.35rem 0.85rem;
            border: 1px solid var(--brand-border);
            font-weight: 500;
            transition: all 0.15s ease;
          }
          [data-baseweb="tab"][aria-selected="true"] {
            background: var(--brand-accent) !important;
            border-color: var(--brand-accent) !important;
            color: white !important;
            box-shadow: 0 2px 8px %(accent)s44;
          }

          /* Sidebar refinement */
          [data-testid="stSidebar"] {
            background: linear-gradient(180deg, %(primary)s 0%%, %(primary_mid)s 100%%);
          }
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
            color: #cbd5e1 !important;
            line-height: 1.5;
          }
          [data-testid="stSidebar"] h1,
          [data-testid="stSidebar"] h2,
          [data-testid="stSidebar"] h3 {
            color: #f1f5f9 !important;
          }
          [data-testid="stSidebar"] label {
            color: #94a3b8 !important;
          }

          /* Expanders */
          [data-testid="stExpander"] {
            border-radius: 12px;
            border: 1px solid var(--brand-border);
            background: var(--brand-surface);
          }

          /* Buttons */
          .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, %(accent)s 0%%, #0f766e 100%%);
            border: none;
            border-radius: 10px;
            font-weight: 600;
            letter-spacing: 0.01em;
            box-shadow: 0 2px 8px %(accent)s44;
            transition: all 0.2s ease;
          }
          .stButton > button[kind="primary"]:hover {
            box-shadow: 0 4px 16px %(accent)s66;
            transform: translateY(-1px);
          }

          /* Info/Warning/Error banners */
          [data-testid="stAlert"] {
            border-radius: 10px;
            border-left: 4px solid;
          }

          /* Dividers */
          hr {
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, var(--brand-border), transparent);
            margin: 1.5rem 0;
          }

          /* Progress bars */
          .stProgress > div > div > div {
            background: linear-gradient(90deg, %(accent)s, %(accent_light)s) !important;
            border-radius: 4px;
          }

          /* Selectbox / inputs */
          .stSelectbox > div > div,
          .stTextInput > div > div {
            border-radius: 8px !important;
          }
        </style>
        """ % {
            "primary": BRAND["primary"],
            "primary_mid": BRAND["primary_mid"],
            "accent": BRAND["accent"],
            "accent_light": BRAND["accent_light"],
            "muted": BRAND["muted"],
            "bg": BRAND["bg"],
            "surface": BRAND["surface"],
            "border": BRAND["border"],
            "font": FONT_STACK,
        },
        unsafe_allow_html=True,
    )


def style_plotly(fig: go.Figure, *, height: int = 380) -> go.Figure:
    """Apply professional Control Tower styling to any Plotly figure."""
    fig.update_layout(
        template="plotly_white",
        colorway=CHART_PALETTE,
        height=height,
        margin=dict(l=16, r=16, t=56, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=BRAND["muted"]),
            bgcolor="rgba(255,255,255,0)",
        ),
        title=dict(
            x=0.02,
            font=dict(size=14, color=BRAND["primary"], family=FONT_STACK),
        ),
        font=dict(family=FONT_STACK, color=BRAND["muted"], size=11),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor=BRAND["primary"],
            font_size=12,
            font_family=FONT_STACK,
            font_color="white",
            bordercolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor="rgba(148, 163, 184, 0.2)",
        tickfont=dict(size=10, color=BRAND["muted_light"]),
    )
    fig.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.12)",
        linecolor="rgba(148, 163, 184, 0.2)",
        tickfont=dict(size=10, color=BRAND["muted_light"]),
    )
    return fig
