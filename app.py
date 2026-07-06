"""
CashFlow Radar — Premium Glassmorphism Dashboard
=================================================
Reads pre-computed result files from ./data/ and renders a
Wirely-inspired, frosted-glass fintech dashboard.

Run:  streamlit run app.py
"""

import os
import json
import datetime
import pandas as pd
import numpy as np
import streamlit as st

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────
# Candy Blue  : #B2D5E5   – primary accent, highlights, active nav
# Orchid      : #E5BDDF   – secondary accent, anomaly badges, GPU bars
# Onyx        : #1D1D1D   – primary text, dark elements
# Ice White   : #F0F6FA   – card backgrounds
# Glass Border: rgba(178,213,229,0.35)  – card borders
# ─────────────────────────────────────────────────────────────────────────────

CANDY_BLUE  = "#B2D5E5"
ORCHID      = "#E5BDDF"
ONYX        = "#1D1D1D"
ICE_WHITE   = "#F0F6FA"
DEEP_BLUE   = "#6FA8C0"
SLATE       = "#8FA8B8"
SUCCESS     = "#5BB896"
WARNING_CLR = "#F0A04B"
DANGER      = "#E07070"


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CashFlow Radar",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Glassmorphism fintech theme
# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM STYLE GOES HERE ↓  (drop your own font, radius, shadow overrides here)
def inject_css():
    st.markdown("""
    <style>
    /* ── Google Fonts: Inter + Material Icons (fallback) ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    /* ── Material Symbols class (used by Streamlit's own UI elements) ── */
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: inherit !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        direction: ltr !important;
        font-feature-settings: 'liga' !important;
        -webkit-font-feature-settings: 'liga' !important;
        -webkit-font-smoothing: antialiased !important;
    }

    /* ── Root Variables (CUSTOM COLOR PALETTE) ── */
    :root {
        --candy-blue:   #B2D5E5;
        --orchid:       #E5BDDF;
        --onyx:         #1D1D1D;
        --ice-white:    #F0F6FA;
        --deep-blue:    #6FA8C0;
        --slate:        #8FA8B8;
        --bg-gradient:  linear-gradient(135deg, #dceef7 0%, #eaf3f9 40%, #f5eefa 100%);
        --glass-bg:     rgba(255, 255, 255, 0.72);
        --glass-border: rgba(178, 213, 229, 0.45);
        --shadow-sm:    0 2px 12px rgba(110, 160, 190, 0.10);
        --shadow-md:    0 6px 28px rgba(110, 160, 190, 0.16);
        --shadow-lg:    0 12px 48px rgba(110, 160, 190, 0.22);
        --radius-sm:    10px;
        --radius-md:    16px;
        --radius-lg:    22px;
        --font:         'Inter', sans-serif;
    }

    /* ── Global reset ── */
    html, body, [class*="css"], [class*="st-"] {
        font-family: var(--font) !important;
        color: var(--onyx);
    }

    /* ── Page background ── */
    .stApp {
        background: var(--bg-gradient) !important;
        background-attachment: fixed !important;
    }
    .block-container {
        padding: 1.5rem 2rem 2rem 2rem !important;
        max-width: 1600px !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.82) !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
        border-right: 1.5px solid var(--glass-border) !important;
        box-shadow: var(--shadow-md) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.8rem;
    }

    /* ── Glass Card base ── */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1.5px solid var(--glass-border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-md);
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .glass-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-1px);
    }

    /* ── KPI metric cards ── */
    .kpi-card {
        background: var(--glass-bg);
        backdrop-filter: blur(14px);
        border: 1.5px solid var(--glass-border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        padding: 1.1rem 1.4rem;
        text-align: left;
        min-height: 90px;
        transition: all 0.2s ease;
    }
    .kpi-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--slate);
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: var(--onyx);
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .kpi-delta {
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 0.3rem;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .kpi-delta.up   { color: #5BB896; }
    .kpi-delta.down { color: #E07070; }
    .kpi-delta.flat { color: var(--slate); }
    .kpi-icon {
        width: 32px; height: 32px;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }

    /* ── Hero balance card ── */
    .hero-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.85) 0%, rgba(240,246,250,0.90) 100%);
        backdrop-filter: blur(18px);
        border: 1.5px solid var(--glass-border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        padding: 2rem 2.2rem;
    }
    .hero-label { font-size: 0.8rem; font-weight: 500; color: var(--slate); letter-spacing: 0.05em; text-transform: uppercase; }
    .hero-amount { font-size: 2.8rem; font-weight: 700; color: var(--onyx); letter-spacing: -0.04em; margin: 0.2rem 0; }
    .hero-sub { font-size: 0.82rem; color: var(--slate); font-weight: 400; }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(178,213,229,0.22);
        border: 1px solid rgba(178,213,229,0.5);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.75rem; font-weight: 500; color: var(--deep-blue);
        margin-top: 1rem;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--onyx);
        letter-spacing: -0.01em;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-header .dot {
        width: 8px; height: 8px;
        background: var(--candy-blue);
        border-radius: 50%;
        display: inline-block;
    }

    /* ── Risk Score gauge card ── */
    .risk-card {
        background: linear-gradient(160deg, rgba(229,189,223,0.18) 0%, rgba(255,255,255,0.80) 100%);
        backdrop-filter: blur(16px);
        border: 1.5px solid rgba(229,189,223,0.40);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md);
        padding: 1.6rem;
        text-align: center;
    }
    .risk-score-number {
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        line-height: 1;
        margin: 0.5rem 0 0.2rem;
    }
    .risk-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin-top: 0.5rem;
    }
    .risk-badge.low    { background: rgba(91,184,150,0.18); color: #3a9e77; border: 1px solid rgba(91,184,150,0.4); }
    .risk-badge.medium { background: rgba(240,160,75,0.18);  color: #c07830; border: 1px solid rgba(240,160,75,0.4);  }
    .risk-badge.high   { background: rgba(224,112,112,0.18); color: #c04040; border: 1px solid rgba(224,112,112,0.4); }

    /* ── Transaction / anomaly table styling ── */
    .txn-row {
        display: flex; align-items: center;
        padding: 0.65rem 0;
        border-bottom: 1px solid rgba(178,213,229,0.20);
        gap: 12px;
        font-size: 0.85rem;
    }
    .txn-row:last-child { border-bottom: none; }
    .txn-avatar {
        width: 34px; height: 34px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.9rem;
        flex-shrink: 0;
    }
    .txn-merchant { font-weight: 500; color: var(--onyx); }
    .txn-date     { font-size: 0.72rem; color: var(--slate); margin-top: 1px; }
    .txn-amount   { font-weight: 600; margin-left: auto; }
    .txn-amount.debit  { color: #E07070; }
    .txn-amount.credit { color: #5BB896; }
    .txn-badge {
        font-size: 0.65rem; font-weight: 600;
        padding: 2px 8px; border-radius: 12px;
        letter-spacing: 0.04em;
    }
    .badge-anomaly { background: rgba(229,189,223,0.3); color: #9060A0; border: 1px solid rgba(229,189,223,0.5); }
    .badge-normal  { background: rgba(178,213,229,0.3); color: #4A88A8; border: 1px solid rgba(178,213,229,0.5); }
    .badge-warning { background: rgba(240,160,75,0.2);  color: #C07830; border: 1px solid rgba(240,160,75,0.4);  }

    /* ── Search/filter input ── */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.7) !important;
        border: 1.5px solid var(--glass-border) !important;
        border-radius: 10px !important;
        font-family: var(--font) !important;
        font-size: 0.85rem !important;
        color: var(--onyx) !important;
        padding: 0.5rem 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--deep-blue) !important;
        box-shadow: 0 0 0 3px rgba(178,213,229,0.25) !important;
    }
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.7) !important;
        border: 1.5px solid var(--glass-border) !important;
        border-radius: 10px !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: var(--glass-bg) !important;
        border: 1.5px solid var(--glass-border) !important;
        border-radius: 10px !important;
        color: var(--onyx) !important;
        font-family: var(--font) !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        padding: 0.45rem 1.2rem !important;
        transition: all 0.18s ease !important;
    }
    .stButton > button:hover {
        background: var(--candy-blue) !important;
        border-color: var(--deep-blue) !important;
        color: #fff !important;
        box-shadow: 0 4px 16px rgba(111,168,192,0.30) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--candy-blue), var(--deep-blue)) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 16px rgba(111,168,192,0.35) !important;
    }

    /* ── Plotly chart background ── */
    .js-plotly-plot .plotly, .js-plotly-plot .plotly .gl-container {
        background: transparent !important;
    }
    .stPlotlyChart { border-radius: var(--radius-md); overflow: hidden; }

    /* ── Dividers ── */
    hr { border-color: rgba(178,213,229,0.25) !important; margin: 1.2rem 0 !important; }

    /* ── Streamlit metric override ── */
    [data-testid="stMetric"] {
        background: var(--glass-bg);
        border: 1.5px solid var(--glass-border);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        box-shadow: var(--shadow-sm);
    }
    [data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: var(--slate) !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700 !important; }

    /* ── Dataframe / table ── */
    [data-testid="stDataFrame"] {
        border-radius: var(--radius-md) !important;
        overflow: hidden;
        border: 1.5px solid var(--glass-border) !important;
    }
    .stDataFrame thead tr th {
        background: rgba(178,213,229,0.15) !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.04em !important;
        color: var(--slate) !important;
        text-transform: uppercase !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] button {
        font-family: var(--font) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: var(--slate) !important;
        border-radius: 8px 8px 0 0 !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--onyx) !important;
        border-bottom: 2.5px solid var(--candy-blue) !important;
    }

    /* ── Sidebar nav items ── */
    .nav-item {
        display: flex; align-items: center; gap: 10px;
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
        font-size: 0.87rem; font-weight: 500;
        color: var(--slate);
        cursor: pointer;
        margin-bottom: 2px;
        transition: all 0.15s;
    }
    .nav-item:hover  { background: rgba(178,213,229,0.18); color: var(--onyx); }
    .nav-item.active { background: rgba(178,213,229,0.30); color: var(--onyx); font-weight: 600; }

    /* ── Benchmark highlight ── */
    .speedup-pill {
        display: inline-flex; align-items: center; gap: 5px;
        background: linear-gradient(135deg, rgba(178,213,229,0.3), rgba(229,189,223,0.3));
        border: 1px solid rgba(178,213,229,0.5);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.8rem; font-weight: 700;
        color: var(--onyx);
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(178,213,229,0.5); border-radius: 10px; }

    /* ── Info / placeholder boxes ── */
    .no-data-box {
        background: rgba(255,255,255,0.55);
        border: 1.5px dashed rgba(178,213,229,0.6);
        border-radius: var(--radius-md);
        padding: 2.5rem;
        text-align: center;
        color: var(--slate);
        font-size: 0.88rem;
    }
    .no-data-box .no-data-icon { font-size: 2rem; margin-bottom: 0.6rem; }
    .no-data-box .no-data-title { font-weight: 600; color: var(--onyx); margin-bottom: 0.3rem; }

    /* ── Hide Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }

    /* ── Hide Streamlit's native sidebar collapse/expand button ──
       Covers every known selector variant across Streamlit versions.
       The button shows raw text "keyboard_double_arrow_right" when the
       Material Symbols font isn't loaded; we remove it entirely. ── */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="baseButton-headerNoPadding"],
    button[kind="header"],
    button[title*="sidebar" i],
    button[aria-label*="sidebar" i],
    button[aria-label*="collapse" i],
    button[aria-label*="Collapse" i],
    section[data-testid="stSidebar"] > div:first-child > button,
    [data-testid="stSidebar"] > div:first-child > div:first-child > button {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        pointer-events: none !important;
    }
    /* Keep sidebar pinned open — disable Streamlit's responsive auto-collapse */
    [data-testid="stSidebar"] { display: block !important; transform: none !important; }

    /* ── Sidebar nav BUTTONS — override Streamlit defaults to match .nav-item style ── */
    [data-testid="stSidebar"] .stButton > button {
        display: flex !important;
        align-items: center !important;
        padding: 0.6rem 0.8rem !important;
        border-radius: 10px !important;
        font-size: 0.87rem !important;
        font-weight: 500 !important;
        color: var(--slate) !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important;
        transition: background 0.15s, color 0.15s !important;
        margin-bottom: 2px !important;
        letter-spacing: 0 !important;
        cursor: pointer !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(178,213,229,0.18) !important;
        color: var(--onyx) !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:focus:not(:active) {
        box-shadow: none !important;
        outline: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] {
        margin-bottom: 0 !important;
    }

    /* ── Stat cards (Accounts view) ── */
    .stat-card {
        background: var(--glass-bg);
        border: 1.5px solid var(--glass-border);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        padding: 1rem 1.2rem;
        text-align: center;
        margin-bottom: 0.6rem;
    }
    .stat-label { font-size: 0.72rem; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; color: var(--slate); margin-bottom: 0.3rem; }
    .stat-value { font-size: 1.4rem; font-weight: 700; color: var(--onyx); letter-spacing: -0.03em; }
    .stat-value.positive { color: #5BB896; }
    .stat-value.negative { color: #E07070; }

    /* ── Budget progress bars (Budgets view) ── */
    .budget-row {
        display: flex; align-items: center; gap: 14px;
        padding: 0.7rem 0;
        border-bottom: 1px solid rgba(178,213,229,0.15);
    }
    .budget-row:last-child { border-bottom: none; }
    .budget-cat { font-size: 0.84rem; font-weight: 500; color: var(--onyx); min-width: 150px; }
    .budget-bar-wrap { flex: 1; height: 8px; background: rgba(178,213,229,0.20); border-radius: 10px; overflow: hidden; }
    .budget-bar { height: 100%; border-radius: 10px; transition: width 0.4s ease; }
    .budget-amounts { font-size: 0.78rem; color: var(--slate); white-space: nowrap; min-width: 140px; text-align: right; }

    /* ── Callout highlight box (Analytics view) ── */
    .callout-box {
        background: linear-gradient(135deg, rgba(229,189,223,0.15), rgba(178,213,229,0.12));
        border: 1.5px solid rgba(229,189,223,0.35);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        margin-top: 0.6rem;
        display: flex; align-items: center; gap: 1rem;
    }
    .callout-icon { font-size: 1.8rem; flex-shrink: 0; }
    .callout-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: var(--slate); margin-bottom: 0.15rem; }
    .callout-value { font-size: 1.35rem; font-weight: 700; color: var(--onyx); letter-spacing: -0.03em; }
    .callout-sub { font-size: 0.76rem; color: var(--slate); margin-top: 0.1rem; }

    /* ── Settings form sections ── */
    .settings-section-title {
        font-size: 0.75rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.07em;
        color: var(--slate); margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(178,213,229,0.25);
    }
    </style>
    """, unsafe_allow_html=True)

    # JS fallback: hide the collapse button by its visible text content.
    # This catches it regardless of class/data-testid (which change per Streamlit version).
    # Runs immediately AND on a short interval to catch React re-renders.
    st.markdown("""
    <script>
    (function hideSidebarToggle() {
        function remove() {
            document.querySelectorAll('button, span').forEach(function(el) {
                var t = el.textContent.trim();
                if (t === 'keyboard_double_arrow_right' ||
                    t === 'keyboard_double_arrow_left'  ||
                    t === 'chevron_left' || t === 'chevron_right') {
                    var btn = el.closest('button') || el;
                    btn.style.cssText = 'display:none!important;visibility:hidden!important;width:0!important;height:0!important';
                }
            });
        }
        remove();
        var _interval = setInterval(remove, 500);
        // Stop after 30s to avoid running forever
        setTimeout(function(){ clearInterval(_interval); }, 30000);
    })();
    </script>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — HTML components
# ─────────────────────────────────────────────────────────────────────────────


def no_data(icon: str, title: str, body: str) -> str:
    return f"""
    <div class="no-data-box">
        <div class="no-data-icon">{icon}</div>
        <div class="no-data-title">{title}</div>
        <div>{body}</div>
    </div>"""

def kpi_html(label: str, value: str, delta: str = "", delta_dir: str = "flat", icon: str = "📊", icon_bg: str = "rgba(178,213,229,0.25)") -> str:
    delta_html = ""
    if delta:
        arrows = {"up": "↑", "down": "↓", "flat": "→"}
        arrow = arrows.get(delta_dir, "")
        delta_html = f'<div class="kpi-delta {delta_dir}">{arrow} {delta}</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon" style="background:{icon_bg}">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>"""

def section_header(title: str, icon: str = "") -> str:
    return f'<div class="section-header"><span class="dot"></span>{icon} {title}</div>'


# ─────────────────────────────────────────────────────────────────────────────
# DATA DIRECTORY
# ─────────────────────────────────────────────────────────────────────────────

def get_data_dir() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    for d in [os.path.join(base, "data"), os.path.join(base, ":data"), "/data"]:
        if os.path.isdir(d) and any(
            f.endswith((".csv", ".json", ".parquet")) for f in os.listdir(d)
        ):
            return d
    return os.path.join(base, "data")


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADERS  (graceful missing-file handling)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_csv(filename: str) -> pd.DataFrame | None:
    path = os.path.join(get_data_dir(), filename)
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error reading `{filename}`: {e}")
        return None


@st.cache_data(ttl=60)
def load_json(filename: str) -> dict | None:
    path = os.path.join(get_data_dir(), filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error reading `{filename}`: {e}")
        return None


@st.cache_data(ttl=60)
def load_benchmark() -> pd.DataFrame | None:
    path = os.path.join(get_data_dir(), "benchmark.json")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_json(path)
    except Exception:
        try:
            with open(path) as f:
                raw = json.load(f)
            df = pd.DataFrame(raw) if isinstance(raw, list) else pd.DataFrame.from_dict(raw)
        except Exception as e2:
            st.error(f"benchmark.json error: {e2}")
            return None
    col_map = {}
    for c in df.columns:
        cl = str(c).lower()
        if   any(k in cl for k in ["size", "row"]):         col_map[c] = "Size"
        elif any(k in cl for k in ["cpu", "pandas"]):        col_map[c] = "Pandas (s)"
        elif any(k in cl for k in ["gpu", "cudf"]):          col_map[c] = "cuDF (s)"
        elif any(k in cl for k in ["speedup", "factor"]):    col_map[c] = "Speedup"
    return df.rename(columns=col_map)



# ─────────────────────────────────────────────────────────────────────────────
# SECTION: SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar(data_dir: str):
    with st.sidebar:
        # Logo / brand
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:0 0.2rem 1.4rem;">
            <div style="width:36px;height:36px;border-radius:10px;
                        background:linear-gradient(135deg,#B2D5E5,#E5BDDF);
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.1rem;box-shadow:0 4px 12px rgba(178,213,229,0.4);">📡</div>
            <div>
                <div style="font-size:1.0rem;font-weight:700;color:#1D1D1D;letter-spacing:-0.02em;">CashFlow Radar</div>
                <div style="font-size:0.68rem;color:#8FA8B8;font-weight:500;">Financial Intelligence</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation buttons (session_state-based view switching) ──
        nav_items = [
            ("📊", "Dashboard"),
            ("💳", "Accounts"),
            ("↔️", "Transactions"),
            ("📈", "Analytics"),
            ("🎯", "Budgets"),
            ("⚙️", "Settings"),
        ]
        def _switch_view(view_name: str):
            st.session_state.current_view = view_name

        current = st.session_state.get("current_view", "Dashboard")
        for icon, label in nav_items:
            if current == label:
                # Active item: styled div (no button chrome needed)
                st.markdown(
                    f'<div class="nav-item active">{icon}&nbsp;&nbsp;{label}</div>',
                    unsafe_allow_html=True
                )
            else:
                # Inactive: real button styled to match .nav-item
                st.button(
                    f"{icon}  {label}",
                    key=f"nav__{label}",
                    on_click=_switch_view,
                    args=(label,),
                    use_container_width=True,
                )

        st.markdown("<div style='margin:1.4rem 0 0.4rem;'>", unsafe_allow_html=True)
        st.markdown("---")

        # Data source status
        st.markdown('<div style="font-size:0.75rem;font-weight:600;color:#8FA8B8;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.7rem;">Data Sources</div>', unsafe_allow_html=True)
        files = {
            "daily_summary.csv":  "Spend Summary",
            "anomalies.csv":      "Anomaly Alerts",
            "forecast.csv":       "30-Day Forecast",
            "risk_score.json":    "Risk Score",
            "benchmark.json":     "GPU Benchmark",
        }
        for fname, label in files.items():
            exists = os.path.exists(os.path.join(data_dir, fname))
            dot_color = "#5BB896" if exists else "#E07070"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;font-size:0.8rem;padding:3px 0;">'
                f'<div style="width:7px;height:7px;border-radius:50%;background:{dot_color};flex-shrink:0;"></div>'
                f'<span style="color:#1D1D1D;">{label}</span></div>',
                unsafe_allow_html=True
            )




# ─────────────────────────────────────────────────────────────────────────────
# SECTION: TOP KPI STRIP
# ─────────────────────────────────────────────────────────────────────────────

def render_kpi_strip(summary_df: pd.DataFrame | None, risk_data: dict | None):
    """4 KPI cards across the top — Transactions · Balance · Monthly Change · Avg Spend"""
    cols = st.columns(4, gap="small")

    # KPI 1: Total transactions
    total_txn = f"{len(summary_df):,}" if summary_df is not None else "—"
    with cols[0]:
        st.markdown(kpi_html(
            "Total Days Tracked", total_txn,
            delta="Active pipeline" if summary_df is not None else "",
            delta_dir="flat", icon="🗓️",
            icon_bg="rgba(178,213,229,0.25)"
        ), unsafe_allow_html=True)

    # KPI 2: Current balance (last row of daily_summary)
    if summary_df is not None and "running_balance" in summary_df.columns:
        last_bal = summary_df["running_balance"].dropna().iloc[-1] if len(summary_df) > 0 else 0
        bal_str = f"${last_bal:,.0f}"
        bal_dir = "up" if last_bal > 0 else "down"
        bal_delta = "Positive" if last_bal > 0 else "Negative"
    else:
        bal_str, bal_dir, bal_delta = "—", "flat", ""
    with cols[1]:
        st.markdown(kpi_html(
            "Current Balance", bal_str,
            delta=bal_delta, delta_dir=bal_dir, icon="💰",
            icon_bg="rgba(91,184,150,0.18)"
        ), unsafe_allow_html=True)

    # KPI 3: Monthly spend change
    if summary_df is not None and "total_spend" in summary_df.columns:
        df_tmp = summary_df.copy()
        df_tmp["date"] = pd.to_datetime(df_tmp["date"])
        df_tmp = df_tmp.sort_values("date")
        if len(df_tmp) >= 60:
            prev_30 = df_tmp.iloc[-60:-30]["total_spend"].sum()
            last_30 = df_tmp.iloc[-30:]["total_spend"].sum()
            pct_change = ((last_30 - prev_30) / max(prev_30, 1)) * 100
            chg_str   = f"{pct_change:+.1f}%"
            chg_dir   = "down" if pct_change > 0 else "up"   # more spend = bad
            chg_delta = "vs prior 30d"
        else:
            chg_str, chg_dir, chg_delta = "N/A", "flat", "< 60 days data"
    else:
        chg_str, chg_dir, chg_delta = "—", "flat", ""
    with cols[2]:
        st.markdown(kpi_html(
            "Monthly Spend Δ", chg_str,
            delta=chg_delta, delta_dir=chg_dir, icon="📉",
            icon_bg="rgba(240,160,75,0.18)"
        ), unsafe_allow_html=True)

    # KPI 4: Avg daily spend
    if summary_df is not None and "total_spend" in summary_df.columns:
        avg_spend = summary_df["total_spend"].mean()
        avg_str   = f"${avg_spend:,.0f}"
        avg_delta = "per day (avg)"
    else:
        avg_str, avg_delta = "—", ""
    with cols[3]:
        st.markdown(kpi_html(
            "Avg Daily Spend", avg_str,
            delta=avg_delta, delta_dir="flat", icon="📊",
            icon_bg="rgba(229,189,223,0.25)"
        ), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: HERO BALANCE + RISK SCORE (side by side)
# ─────────────────────────────────────────────────────────────────────────────

def render_hero_and_risk(summary_df: pd.DataFrame | None, risk_data: dict | None, forecast_df: pd.DataFrame | None):
    col_hero, col_risk = st.columns([1.7, 1], gap="medium")

    # ── Hero Balance Card ──
    with col_hero:
        if summary_df is not None and "running_balance" in summary_df.columns:
            df_s = summary_df.copy()
            df_s["date"] = pd.to_datetime(df_s["date"])
            df_s = df_s.sort_values("date")
            last_bal   = float(df_s["running_balance"].dropna().iloc[-1])
            last_date  = df_s["date"].iloc[-1].strftime("%b %d, %Y")
            last_spend = float(df_s["total_spend"].iloc[-1]) if "total_spend" in df_s.columns else 0
            bal_color  = "#5BB896" if last_bal > 0 else "#E07070"

            st.markdown(f"""
            <div class="hero-card">
                <div class="hero-label">Total Portfolio Balance</div>
                <div class="hero-amount" style="color:{bal_color}">${abs(last_bal):,.2f}</div>
                <div class="hero-sub">{'Available Now' if last_bal > 0 else 'Deficit — Action Required'} &nbsp;•&nbsp; 🔵 USD</div>
                <div style="margin-top:1.2rem;">
                    <span class="hero-badge">🕐 Last updated: {last_date}</span>
                    &nbsp;&nbsp;
                    <span class="hero-badge">📤 Daily spend: ${last_spend:,.0f}</span>
                </div>
            </div>""", unsafe_allow_html=True)

            # Mini forecast sparkline inside hero
            if forecast_df is not None and PLOTLY_AVAILABLE:
                fc = forecast_df.copy()
                fc["date"] = pd.to_datetime(fc["date"])
                fig_spark = go.Figure()
                fig_spark.add_trace(go.Scatter(
                    x=fc["date"], y=fc["upper_bound"],
                    mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"
                ))
                fig_spark.add_trace(go.Scatter(
                    x=fc["date"], y=fc["lower_bound"],
                    mode="lines", line=dict(width=0),
                    fill="tonexty", fillcolor="rgba(178,213,229,0.20)",
                    showlegend=False, hoverinfo="skip"
                ))
                fig_spark.add_trace(go.Scatter(
                    x=fc["date"], y=fc["projected_balance"],
                    mode="lines",
                    line=dict(color=DEEP_BLUE, width=2.5, shape="spline"),
                    showlegend=False, hovertemplate="$%{y:,.0f}<extra></extra>"
                ))
                fig_spark.update_layout(
                    height=90, margin=dict(l=0, r=0, t=12, b=0),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_spark, width="stretch", config={"displayModeBar": False})
        else:
            st.markdown(no_data("💳", "No Balance Data", "Drop `daily_summary.csv` into `./data/`"), unsafe_allow_html=True)

    # ── Risk Score Card ──
    with col_risk:
        if risk_data is not None:
            score = float(risk_data.get("score", 50))
            expl  = risk_data.get("explanation", "")
            if   score < 40:  badge_cls, badge_lbl, score_color = "low",    "Healthy",      "#5BB896"
            elif score < 70: badge_cls, badge_lbl, score_color = "medium", "Moderate Risk", "#F0A04B"
            else:            badge_cls, badge_lbl, score_color = "high",   "High Risk",     "#E07070"

            # Semi-circular gauge
            if PLOTLY_AVAILABLE:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    number={"suffix": "", "font": {"size": 38, "family": "Inter", "color": score_color}},
                    domain={"x": [0, 1], "y": [0, 1]},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)", "showticklabels": False},
                        "bar":  {"color": score_color, "thickness": 0.22},
                        "bgcolor": "rgba(0,0,0,0)",
                        "borderwidth": 0,
                        "steps": [
                            {"range": [0,   40],  "color": "rgba(91,184,150,0.12)"},
                            {"range": [40,  70],  "color": "rgba(240,160,75,0.12)"},
                            {"range": [70,  100], "color": "rgba(224,112,112,0.12)"},
                        ],
                    }
                ))
                fig_gauge.update_layout(
                    height=180,
                    margin=dict(l=20, r=20, t=30, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"family": "Inter"},
                )
                st.markdown('<div class="risk-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="section-header"><span class="dot" style="background:#E5BDDF;"></span>Cash-Flow Risk Score</div>', unsafe_allow_html=True)
                st.plotly_chart(fig_gauge, width="stretch", config={"displayModeBar": False})
                st.markdown(f'<div style="text-align:center;"><span class="risk-badge {badge_cls}">{badge_lbl}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.75rem;color:#8FA8B8;text-align:center;margin-top:0.7rem;line-height:1.5;">{expl[:160]}{"…" if len(expl) > 160 else ""}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="risk-card">' + no_data("🛡️", "No Risk Score", "Drop `risk_score.json` into `./data/`") + '</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: FORECAST CHART
# ─────────────────────────────────────────────────────────────────────────────

def render_forecast(forecast_df: pd.DataFrame | None):
    st.markdown(section_header("30-Day Cash Flow Forecast", "📈"), unsafe_allow_html=True)

    if forecast_df is None:
        st.markdown(no_data("📈", "No Forecast Data", "Drop `forecast.csv` into `./data/`"), unsafe_allow_html=True)
        return

    fc = forecast_df.copy()
    fc["date"] = pd.to_datetime(fc["date"])

    safety_buffer = st.slider(
        "Safety Buffer ($)", min_value=0, max_value=10000, value=2000, step=500,
        help="Minimum balance threshold — shown as a reference line on the chart"
    )

    if PLOTLY_AVAILABLE:
        fig = go.Figure()
        # Confidence band fill
        fig.add_trace(go.Scatter(
            x=fc["date"], y=fc["upper_bound"],
            mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip", name="upper"
        ))
        fig.add_trace(go.Scatter(
            x=fc["date"], y=fc["lower_bound"],
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(178,213,229,0.22)",
            name="Confidence Band",
            hovertemplate="Lower: $%{y:,.0f}<extra></extra>"
        ))
        # Main projected line
        fig.add_trace(go.Scatter(
            x=fc["date"], y=fc["projected_balance"],
            mode="lines+markers",
            line=dict(color=DEEP_BLUE, width=3, shape="spline"),
            marker=dict(size=5, color=ORCHID, line=dict(color=DEEP_BLUE, width=1.5)),
            name="Projected Balance",
            hovertemplate="<b>%{x|%b %d}</b><br>$%{y:,.0f}<extra></extra>"
        ))
        # Safety buffer line
        fig.add_hline(
            y=safety_buffer,
            line_dash="dot", line_color="#E07070", line_width=1.8,
            annotation_text=f"  Safety Buffer ${safety_buffer:,}",
            annotation_font=dict(size=11, color="#E07070"),
            annotation_position="top left"
        )
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11, family="Inter"), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(
                showgrid=False, showline=False,
                tickfont=dict(family="Inter", size=11, color=SLATE),
            ),
            yaxis=dict(
                showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                zeroline=False, showline=False,
                tickfont=dict(family="Inter", size=11, color=SLATE),
                tickprefix="$", tickformat=",.0f"
            ),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    else:
        st.line_chart(fc.set_index("date")[["projected_balance", "lower_bound", "upper_bound"]])


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: SPEND BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────

def render_spend_breakdown(summary_df: pd.DataFrame | None):
    st.markdown(section_header("Spend Breakdown by Category", "📊"), unsafe_allow_html=True)

    if summary_df is None:
        st.markdown(no_data("📊", "No Spend Data", "Drop `daily_summary.csv` into `./data/`"), unsafe_allow_html=True)
        return

    df = summary_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    meta = {"date", "total_spend", "running_balance", "rolling_7d_spend", "rolling_30d_spend"}
    cat_cols = [c for c in df.columns
                if c not in meta
                and pd.api.types.is_numeric_dtype(df[c])
                and df[c].sum() > 0]

    ctrl1, ctrl2 = st.columns(2, gap="small")
    with ctrl1:
        view = st.radio("Timeframe", ["Daily", "Weekly"], horizontal=True, key="sb_view")
    with ctrl2:
        chart_t = st.radio("Chart Type", ["Area", "Bar"], horizontal=True, key="sb_type")

    plot_df = df.copy()
    if view == "Weekly" and cat_cols:
        plot_df = df.set_index("date")[cat_cols].resample("W").sum().reset_index()

    if not cat_cols:
        st.warning("No category columns detected in `daily_summary.csv`.")
        return

    # Pastel palette matching the design system
    palette = [CANDY_BLUE, ORCHID, DEEP_BLUE, "#A8D5B5", "#F0C8A0", "#C8B8E0", "#8FC8D8", "#E0B8C8"]

    if PLOTLY_AVAILABLE:
        if chart_t == "Bar":
            fig = px.bar(plot_df, x="date", y=cat_cols,
                         color_discrete_sequence=palette)
            fig.update_layout(barmode="stack")
        else:
            fig = px.area(plot_df, x="date", y=cat_cols,
                          color_discrete_sequence=palette)
            fig.update_traces(line=dict(width=1.2))

        fig.update_layout(
            height=260,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=10, family="Inter"), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=10, color=SLATE)),
            yaxis=dict(
                showgrid=True, gridcolor="rgba(178,213,229,0.18)",
                tickfont=dict(family="Inter", size=10, color=SLATE),
                tickprefix="$", zeroline=False
            ),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    else:
        if "date" in plot_df.columns:
            plot_df = plot_df.set_index("date")
        st.area_chart(plot_df[cat_cols])


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: ANOMALY ALERTS
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_EMOJIS = {
    "software":              "💻",
    "food & dining":         "🍔",
    "cloud & hosting":       "☁️",
    "marketing":             "📣",
    "travel":                "✈️",
    "professional services": "💼",
    "utilities":             "⚡",
    "office & supplies":     "🖊️",
}

def render_anomaly_alerts(anomalies_df: pd.DataFrame | None):
    st.markdown(section_header("Anomaly Alerts", "🚨"), unsafe_allow_html=True)

    if anomalies_df is None:
        st.markdown(no_data("🚨", "No Anomaly Data", "Drop `anomalies.csv` into `./data/`"), unsafe_allow_html=True)
        return

    df = anomalies_df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Filters
    f1, f2 = st.columns([1, 1.5], gap="small")
    with f1:
        cats = ["All"] + (sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else [])
        sel_cat = st.selectbox("Category", cats, key="anom_cat_filter")
    with f2:
        search = st.text_input("🔍 Search", placeholder="Merchant, reason...", key="anom_search_box")

    fdf = df.copy()
    if sel_cat != "All" and "category" in fdf.columns:
        fdf = fdf[fdf["category"] == sel_cat]
    if search:
        mask = fdf.astype(str).apply(lambda r: r.str.contains(search, case=False).any(), axis=1)
        fdf = fdf[mask]

    # Custom transaction rows
    st.markdown(f'<div style="font-size:0.75rem;color:{SLATE};margin-bottom:0.5rem;">{len(fdf)} flagged transactions</div>', unsafe_allow_html=True)

    for _, row in fdf.head(8).iterrows():
        merchant  = str(row.get("merchant", "Unknown"))
        category  = str(row.get("category", ""))
        amount    = row.get("amount", 0)
        date_val  = row.get("date", "")
        reason    = str(row.get("reason", "Anomaly detected"))
        score     = row.get("anomaly_score", -1)

        emoji = CATEGORY_EMOJIS.get(category.lower(), "🔴")
        date_str = date_val.strftime("%b %d, %Y %H:%M") if hasattr(date_val, "strftime") else str(date_val)[:16]

        # Severity badge
        if score is not None and not (isinstance(score, float) and np.isnan(score)):
            sev = float(score)
            if sev < -0.85:  badge_txt, badge_cls = "Critical", "badge-anomaly"
            elif sev < -0.70: badge_txt, badge_cls = "Warning",  "badge-warning"
            else:             badge_txt, badge_cls = "Flagged",  "badge-normal"
        else:
            badge_txt, badge_cls = "Flagged", "badge-normal"

        # Avatar bg
        bg_colors = {
            "badge-anomaly": "rgba(229,189,223,0.3)",
            "badge-warning": "rgba(240,160,75,0.2)",
            "badge-normal":  "rgba(178,213,229,0.3)",
        }
        bg = bg_colors.get(badge_cls, "rgba(178,213,229,0.25)")

        st.markdown(f"""
        <div class="txn-row">
            <div class="txn-avatar" style="background:{bg};">{emoji}</div>
            <div style="flex:1;min-width:0;">
                <div class="txn-merchant">{merchant}
                    &nbsp;<span class="txn-badge {badge_cls}">{badge_txt}</span>
                </div>
                <div class="txn-date">{date_str} &nbsp;·&nbsp; {category}</div>
                <div style="font-size:0.72rem;color:#8FA8B8;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{reason[:85]}{"…" if len(reason) > 85 else ""}</div>
            </div>
            <div class="txn-amount debit" style="margin-left:0.8rem;white-space:nowrap;">${amount:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    if len(fdf) > 8:
        st.caption(f"Showing 8 of {len(fdf)} — use filters above to narrow results.")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: GPU BENCHMARK
# ─────────────────────────────────────────────────────────────────────────────

def render_benchmark(bench_df: pd.DataFrame | None):
    st.markdown("---")
    st.markdown(section_header("GPU vs CPU Acceleration Benchmark", "⚡"), unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.82rem;color:#8FA8B8;margin-bottom:1rem;">'
        'Performance comparison of the full financial data pipeline on CPU <b style="color:#1D1D1D;">(pandas)</b> '
        'vs. NVIDIA GPU <b style="color:#1D1D1D;">(RAPIDS cuDF)</b> at increasing data scales.'
        '</div>', unsafe_allow_html=True
    )

    if bench_df is None:
        st.markdown(no_data("⚡", "No Benchmark Data", "Drop `benchmark.json` into `./data/`"), unsafe_allow_html=True)
        return

    # Identify columns
    size_col    = next((c for c in bench_df.columns if "size" in c.lower()), bench_df.columns[0])
    pandas_col  = next((c for c in bench_df.columns if "pandas" in c.lower()), None)
    cudf_col    = next((c for c in bench_df.columns if "cudf"   in c.lower()), None)
    speedup_col = next((c for c in bench_df.columns if "speedup" in c.lower()), None)

    # KPI banner
    if speedup_col:
        max_sp = bench_df[speedup_col].max()
        k1, k2, k3 = st.columns(3, gap="small")
        with k1:
            st.markdown(kpi_html("Peak Speedup",   f"{max_sp:.1f}×",
                                 "RAPIDS cuDF", "up", "🚀", "rgba(229,189,223,0.25)"), unsafe_allow_html=True)
        with k2:
            max_rows = bench_df[size_col].max()
            st.markdown(kpi_html("Largest Dataset", f"{int(max_rows):,}",
                                 "Rows processed", "flat", "📦", "rgba(178,213,229,0.25)"), unsafe_allow_html=True)
        with k3:
            st.markdown(kpi_html("Accelerator",    "NVIDIA RAPIDS",
                                 "cuDF + cuML", "flat", "🖥️", "rgba(91,184,150,0.18)"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1rem;'>", unsafe_allow_html=True)
    col_tbl, col_chart = st.columns([1, 1.5], gap="large")

    with col_tbl:
        st.markdown(section_header("Performance Table"), unsafe_allow_html=True)
        disp = bench_df.copy()
        for c in disp.columns:
            if c == size_col:
                disp[c] = disp[c].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else x)
            elif c == speedup_col:
                disp[c] = disp[c].apply(lambda x: f"{x:.1f}×" if pd.notnull(x) else x)
            elif pd.api.types.is_numeric_dtype(disp[c]):
                disp[c] = disp[c].apply(lambda x: f"{x:.3f}s" if pd.notnull(x) else x)
        st.dataframe(disp, width="stretch", hide_index=True)

    with col_chart:
        st.markdown(section_header("Execution Time (lower = better)"), unsafe_allow_html=True)
        if PLOTLY_AVAILABLE and pandas_col and cudf_col:
            melted = bench_df.melt(
                id_vars=[size_col], value_vars=[pandas_col, cudf_col],
                var_name="Engine", value_name="Time (s)"
            )
            size_labels = bench_df[size_col].apply(
                lambda x: f"{int(x)//1_000_000}M" if int(x) >= 1_000_000 else f"{int(x)//1_000}K"
            ).tolist()
            label_map = dict(zip(bench_df[size_col].tolist(), size_labels))
            melted["Label"] = melted[size_col].map(label_map)

            fig_bench = px.bar(
                melted, x="Label", y="Time (s)", color="Engine", barmode="group",
                color_discrete_map={pandas_col: ONYX, cudf_col: CANDY_BLUE},
                text_auto=".3f",
            )
            fig_bench.update_traces(marker_cornerradius=4, textfont=dict(size=10, family="Inter"))
            fig_bench.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=11, family="Inter"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=11, color=SLATE), title=""),
                yaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                           tickfont=dict(family="Inter", size=11, color=SLATE),
                           ticksuffix="s", zeroline=False, title=""),
                bargap=0.22, bargroupgap=0.06,
            )
            st.plotly_chart(fig_bench, width="stretch", config={"displayModeBar": False})

            # Speedup pills
            if speedup_col:
                st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:0.4rem;">', unsafe_allow_html=True)
                for _, row in bench_df.iterrows():
                    lbl = label_map.get(row[size_col], str(row[size_col]))
                    sp  = row.get(speedup_col)
                    if sp is not None and not (isinstance(sp, float) and np.isnan(sp)):
                        st.markdown(f'<span class="speedup-pill">🚀 {lbl} — {float(sp):.1f}× faster</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            if pandas_col and cudf_col:
                st.bar_chart(bench_df.set_index(size_col)[[pandas_col, cudf_col]])


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: ACCOUNTS
# ─────────────────────────────────────────────────────────────────────────────

def render_view_accounts(summary_df: pd.DataFrame | None):
    st.markdown(section_header("Account Overview", "💳"), unsafe_allow_html=True)

    if summary_df is None:
        st.markdown(no_data("💳", "No Account Data", "Drop `daily_summary.csv` into `./data/`"), unsafe_allow_html=True)
        return

    df = summary_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    if "running_balance" not in df.columns:
        st.warning("No `running_balance` column found in `daily_summary.csv`.")
        return

    start_bal  = df["running_balance"].iloc[0]
    end_bal    = df["running_balance"].iloc[-1]
    net_change = end_bal - start_bal
    peak_bal   = df["running_balance"].max()
    peak_date  = df.loc[df["running_balance"].idxmax(), "date"].strftime("%b %d")
    low_bal    = df["running_balance"].min()
    low_date   = df.loc[df["running_balance"].idxmin(), "date"].strftime("%b %d")
    net_cls    = "positive" if net_change >= 0 else "negative"
    net_str    = f"+${net_change:,.0f}" if net_change >= 0 else f"-${abs(net_change):,.0f}"

    # ── 4 stat cards ──
    c1, c2, c3, c4 = st.columns(4, gap="small")
    for col, lbl, val, vcls in [
        (c1, "Starting Balance",  f"${start_bal:,.0f}",  ""),
        (c2, "Current Balance",   f"${end_bal:,.0f}",    "positive" if end_bal >= 0 else "negative"),
        (c3, "Net Change",        net_str,                net_cls),
        (c4, "Peak Balance",      f"${peak_bal:,.0f}",   "positive"),
    ]:
        vcls_attr = f' {vcls}' if vcls else ''
        with col:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-label">{lbl}</div>'
                f'<div class="stat-value{vcls_attr}">{val}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

    # ── Balance over time chart ──
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(section_header("Balance Over Time", "📈"), unsafe_allow_html=True)

    if PLOTLY_AVAILABLE:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["running_balance"],
            mode="lines",
            line=dict(color=DEEP_BLUE, width=2.5, shape="spline"),
            fill="tozeroy", fillcolor="rgba(111,168,192,0.10)",
            name="Balance",
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Balance: $%{y:,.0f}<extra></extra>"
        ))
        for date_pt, bal_pt, lbl_pt, clr_pt in [
            (df.loc[df["running_balance"].idxmax(), "date"], peak_bal, f"Peak {peak_date}", SUCCESS),
            (df.loc[df["running_balance"].idxmin(), "date"], low_bal,  f"Low {low_date}",  DANGER),
        ]:
            fig.add_annotation(
                x=date_pt, y=bal_pt, text=lbl_pt,
                showarrow=True, arrowhead=2, arrowcolor=clr_pt, arrowwidth=1.5,
                font=dict(size=11, color=clr_pt, family="Inter"),
                bgcolor="rgba(255,255,255,0.88)", bordercolor=clr_pt,
                borderwidth=1, borderpad=4
            )
        fig.update_layout(
            height=320, margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified", showlegend=False,
            xaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=11, color=SLATE)),
            yaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)", zeroline=True,
                       zerolinecolor="rgba(224,112,112,0.25)",
                       tickfont=dict(family="Inter", size=11, color=SLATE),
                       tickprefix="$", tickformat=",.0f"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.line_chart(df.set_index("date")["running_balance"])

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Key dates table + distribution histogram ──
    col_tbl, col_hist = st.columns([1, 1.2], gap="large")
    with col_tbl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(section_header("Account Summary"), unsafe_allow_html=True)
        for row_lbl, row_val in [
            ("📅 Period Start",   df["date"].iloc[0].strftime("%b %d, %Y")),
            ("📅 Period End",     df["date"].iloc[-1].strftime("%b %d, %Y")),
            ("🟢 Peak Balance",   f"${peak_bal:,.0f}  ({peak_date})"),
            ("🔴 Lowest Balance", f"${low_bal:,.0f}  ({low_date})"),
            ("📊 Days Tracked",   str(len(df))),
            ("💰 Avg Balance",    f"${df['running_balance'].mean():,.0f}"),
        ]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.45rem 0;'
                f'border-bottom:1px solid rgba(178,213,229,0.18);font-size:0.84rem;">'
                f'<span style="color:{SLATE};">{row_lbl}</span>'
                f'<span style="font-weight:600;color:{ONYX};">{row_val}</span></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_hist:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(section_header("Balance Distribution"), unsafe_allow_html=True)
        if PLOTLY_AVAILABLE:
            fig_h = go.Figure(go.Histogram(
                x=df["running_balance"], nbinsx=18,
                marker_color=CANDY_BLUE, opacity=0.85,
                hovertemplate="$%{x:,.0f} — %{y} days<extra></extra>"
            ))
            fig_h.update_layout(
                height=210, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickprefix="$", tickformat=",.0f",
                           tickfont=dict(family="Inter", size=10, color=SLATE)),
                yaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                           tickfont=dict(family="Inter", size=10, color=SLATE), title=""),
                showlegend=False,
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})
        else:
            st.bar_chart(df["running_balance"].value_counts().sort_index())
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────

def render_view_transactions(summary_df: pd.DataFrame | None, anomalies_df: pd.DataFrame | None):
    st.markdown(section_header("Transactions", "↔️"), unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🚨  Flagged Transactions", "📅  Daily Totals"])

    with tab1:
        if anomalies_df is None:
            st.markdown(no_data("🚨", "No Transaction Data", "Drop `anomalies.csv` into `./data/`"), unsafe_allow_html=True)
        else:
            df = anomalies_df.copy()
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.sort_values("date", ascending=False)

            col_f1, col_f2, col_f3 = st.columns([1, 1, 2], gap="small")
            with col_f1:
                cats = ["All"] + (sorted(df["category"].dropna().unique().tolist())
                                  if "category" in df.columns else [])
                sel_cat = st.selectbox("Category", cats, key="txn_cat")
            with col_f2:
                sort_opts = ["Date ↓ (newest)", "Date ↑ (oldest)",
                             "Amount ↓ (highest)", "Amount ↑ (lowest)"]
                sort_by = st.selectbox("Sort by", sort_opts, key="txn_sort")
            with col_f3:
                search = st.text_input("🔍 Search merchant, reason, category…", key="txn_search")

            fdf = df.copy()
            if sel_cat != "All" and "category" in fdf.columns:
                fdf = fdf[fdf["category"] == sel_cat]
            if search:
                mask = fdf.astype(str).apply(
                    lambda r: r.str.contains(search, case=False, na=False).any(), axis=1)
                fdf = fdf[mask]
            if "date" in fdf.columns and "amount" in fdf.columns:
                if   sort_by.startswith("Date ↓"):   fdf = fdf.sort_values("date",   ascending=False)
                elif sort_by.startswith("Date ↑"):   fdf = fdf.sort_values("date",   ascending=True)
                elif sort_by.startswith("Amount ↓"):  fdf = fdf.sort_values("amount", ascending=False)
                elif sort_by.startswith("Amount ↑"):  fdf = fdf.sort_values("amount", ascending=True)

            st.markdown(
                f'<div style="font-size:0.75rem;color:{SLATE};margin:0.5rem 0;">'
                f'{len(fdf)} transaction{"s" if len(fdf) != 1 else ""} shown</div>',
                unsafe_allow_html=True
            )
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            for _, row in fdf.iterrows():
                merchant = str(row.get("merchant", "Unknown"))
                category = str(row.get("category", ""))
                amount   = row.get("amount", 0)
                date_val = row.get("date", "")
                reason   = str(row.get("reason", ""))
                score    = row.get("anomaly_score", None)

                emoji    = CATEGORY_EMOJIS.get(category.lower(), "💳")
                date_str = date_val.strftime("%b %d, %Y") if hasattr(date_val, "strftime") else str(date_val)[:10]

                if score is not None and not (isinstance(score, float) and np.isnan(score)):
                    sev = float(score)
                    if   sev < -0.85: badge_txt, badge_cls = "Critical", "badge-anomaly"
                    elif sev < -0.70: badge_txt, badge_cls = "Warning",  "badge-warning"
                    else:             badge_txt, badge_cls = "Flagged",  "badge-normal"
                else:
                    badge_txt, badge_cls = "Flagged", "badge-normal"
                bg_map = {"badge-anomaly": "rgba(229,189,223,0.3)",
                          "badge-warning":  "rgba(240,160,75,0.2)",
                          "badge-normal":   "rgba(178,213,229,0.3)"}
                bg = bg_map.get(badge_cls, "rgba(178,213,229,0.25)")

                st.markdown(f"""
                <div class="txn-row">
                    <div class="txn-avatar" style="background:{bg};">{emoji}</div>
                    <div style="flex:1;min-width:0;">
                        <div class="txn-merchant">{merchant}
                            &nbsp;<span class="txn-badge {badge_cls}">{badge_txt}</span>
                        </div>
                        <div class="txn-date">{date_str} &nbsp;·&nbsp; {category}</div>
                        <div style="font-size:0.72rem;color:#8FA8B8;margin-top:2px;">
                            {reason[:100]}{"…" if len(reason) > 100 else ""}
                        </div>
                    </div>
                    <div class="txn-amount debit" style="margin-left:0.8rem;white-space:nowrap;">${amount:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        if summary_df is None:
            st.markdown(no_data("📅", "No Daily Data", "Drop `daily_summary.csv` into `./data/`"), unsafe_allow_html=True)
        else:
            df2 = summary_df.copy()
            if "date" in df2.columns:
                df2["date"] = pd.to_datetime(df2["date"], errors="coerce")
                df2 = df2.sort_values("date", ascending=False)
            st.caption("Daily aggregate totals from daily_summary.csv — one row per day, not individual transactions.")
            search2 = st.text_input("🔍 Filter by date…", key="txn_daily_search")
            if search2:
                mask2 = df2.astype(str).apply(
                    lambda r: r.str.contains(search2, case=False, na=False).any(), axis=1)
                df2 = df2[mask2]
            disp2 = df2.copy()
            if "date" in disp2.columns:
                disp2["date"] = disp2["date"].dt.strftime("%Y-%m-%d")
            for c in disp2.columns:
                if c != "date" and pd.api.types.is_numeric_dtype(disp2[c]):
                    disp2[c] = disp2[c].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "—")
            st.dataframe(disp2, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

def render_view_analytics(summary_df: pd.DataFrame | None):
    st.markdown(section_header("Analytics", "📈"), unsafe_allow_html=True)

    if summary_df is None:
        st.markdown(no_data("📈", "No Data", "Drop `daily_summary.csv` into `./data/`"), unsafe_allow_html=True)
        return

    df = summary_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    meta = {"date", "total_spend", "running_balance", "rolling_7d_spend", "rolling_30d_spend"}
    cat_cols = [c for c in df.columns
                if c not in meta
                and pd.api.types.is_numeric_dtype(df[c])
                and df[c].sum() > 0]
    palette  = [CANDY_BLUE, ORCHID, DEEP_BLUE, "#A8D5B5", "#F0C8A0", "#C8B8E0", "#8FC8D8", "#E0B8C8"]

    # Compute rolling_7d on-the-fly if not in the file
    if "rolling_7d_spend" not in df.columns and "total_spend" in df.columns:
        df["rolling_7d_spend"] = df["total_spend"].rolling(7, min_periods=1).mean()

    # ── Row 1: Monthly trend + Category ranking ──
    col_mom, col_cat = st.columns([1.4, 1], gap="large")

    with col_mom:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(section_header("Monthly Spend Trend", "📅"), unsafe_allow_html=True)
        if "total_spend" in df.columns:
            df["month_str"] = df["date"].dt.to_period("M").dt.strftime("%b %Y")
            monthly = df.groupby("month_str", sort=False)["total_spend"].sum().reset_index()
            # Re-sort chronologically
            monthly["_sort"] = pd.to_datetime(monthly["month_str"], format="%b %Y")
            monthly = monthly.sort_values("_sort").drop(columns=["_sort"])
            if PLOTLY_AVAILABLE:
                bar_colors = []
                for i in range(len(monthly)):
                    if i == 0:
                        bar_colors.append(CANDY_BLUE)
                    elif monthly["total_spend"].iloc[i] <= monthly["total_spend"].iloc[i - 1]:
                        bar_colors.append(SUCCESS)
                    else:
                        bar_colors.append(DANGER)
                fig_mom = go.Figure(go.Bar(
                    x=monthly["month_str"], y=monthly["total_spend"],
                    marker_color=bar_colors,
                    text=monthly["total_spend"].apply(lambda x: f"${x:,.0f}"),
                    textposition="outside", textfont=dict(family="Inter", size=10),
                    hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
                ))
                fig_mom.update_layout(
                    height=260, margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=11, color=SLATE)),
                    yaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                               tickprefix="$", tickformat=",.0f",
                               tickfont=dict(family="Inter", size=11, color=SLATE), zeroline=False),
                    showlegend=False,
                )
                st.plotly_chart(fig_mom, use_container_width=True, config={"displayModeBar": False})
            else:
                st.bar_chart(monthly.set_index("month_str")["total_spend"])
        else:
            st.info("No `total_spend` column found.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_cat:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(section_header("Category Ranking", "🏆"), unsafe_allow_html=True)
        if cat_cols:
            totals_s = pd.Series({c: df[c].sum() for c in cat_cols}).sort_values(ascending=True)
            if PLOTLY_AVAILABLE:
                fig_cat = go.Figure(go.Bar(
                    x=totals_s.values, y=totals_s.index, orientation="h",
                    marker_color=palette[:len(totals_s)],
                    text=[f"${v:,.0f}" for v in totals_s.values],
                    textposition="inside", textfont=dict(family="Inter", size=10, color="white"),
                    hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
                ))
                fig_cat.update_layout(
                    height=260, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                               tickprefix="$", tickformat=",.0f",
                               tickfont=dict(family="Inter", size=10, color=SLATE), zeroline=False),
                    yaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=10, color=ONYX)),
                    showlegend=False,
                )
                st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
            else:
                st.bar_chart(pd.DataFrame({"Total": totals_s}))
        else:
            st.info("No category columns detected.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

    # ── Row 2: Spending highlights callout + 7-day rolling ──
    col_hi, col_roll = st.columns([1, 1.5], gap="large")

    with col_hi:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(section_header("Spending Highlights", "⚡"), unsafe_allow_html=True)
        if "total_spend" in df.columns and len(df) > 0:
            max_idx   = df["total_spend"].idxmax()
            min_idx   = df["total_spend"].idxmin()
            max_day   = df.loc[max_idx, "date"].strftime("%B %d, %Y")
            max_spend = df.loc[max_idx, "total_spend"]
            min_day   = df.loc[min_idx, "date"].strftime("%B %d, %Y")
            min_spend = df.loc[min_idx, "total_spend"]
            avg_spend = df["total_spend"].mean()
            for ic, lb, vl, sb in [
                ("🔥", "Highest Spend Day", f"${max_spend:,.0f}", max_day),
                ("💚", "Lowest Spend Day",  f"${min_spend:,.0f}", min_day),
                ("📊", "Daily Average",     f"${avg_spend:,.0f}", f"Over {len(df)} days"),
            ]:
                st.markdown(f"""
                <div class="callout-box">
                    <div class="callout-icon">{ic}</div>
                    <div>
                        <div class="callout-label">{lb}</div>
                        <div class="callout-value">{vl}</div>
                        <div class="callout-sub">{sb}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_roll:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        roll_lbl = "7-Day Rolling Spend" if "rolling_7d_spend" in df.columns else "Daily Spend Trend"
        st.markdown(section_header(roll_lbl, "📉"), unsafe_allow_html=True)
        roll_col = ("rolling_7d_spend" if "rolling_7d_spend" in df.columns
                    else ("total_spend" if "total_spend" in df.columns else None))
        if roll_col and PLOTLY_AVAILABLE:
            roll_df = df[["date", roll_col]].dropna()
            fig_roll = go.Figure(go.Scatter(
                x=roll_df["date"], y=roll_df[roll_col],
                mode="lines",
                line=dict(color=ORCHID, width=2.5, shape="spline"),
                fill="tozeroy", fillcolor="rgba(229,189,223,0.12)",
                hovertemplate="<b>%{x|%b %d}</b><br>$%{y:,.0f}<extra></extra>"
            ))
            fig_roll.update_layout(
                height=300, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=11, color=SLATE)),
                yaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                           tickprefix="$", tickformat=",.0f",
                           tickfont=dict(family="Inter", size=11, color=SLATE), zeroline=False),
            )
            st.plotly_chart(fig_roll, use_container_width=True, config={"displayModeBar": False})
        elif roll_col:
            st.line_chart(df.set_index("date")[roll_col])
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: BUDGETS
# ─────────────────────────────────────────────────────────────────────────────

def render_view_budgets(summary_df: pd.DataFrame | None):
    st.markdown(section_header("Budgets", "🎯"), unsafe_allow_html=True)

    if summary_df is None:
        st.markdown(no_data("🎯", "No Budget Data", "Drop `daily_summary.csv` into `./data/`"), unsafe_allow_html=True)
        return

    df = summary_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    meta = {"date", "total_spend", "running_balance", "rolling_7d_spend", "rolling_30d_spend"}
    cat_cols = [c for c in df.columns
                if c not in meta
                and pd.api.types.is_numeric_dtype(df[c])
                and df[c].sum() > 0]

    if not cat_cols:
        st.warning("No category columns detected in `daily_summary.csv`.")
        return

    st.markdown("""
    <div style="display:flex;align-items:flex-start;gap:10px;padding:0.8rem 1rem;
                background:rgba(178,213,229,0.10);border:1px solid rgba(178,213,229,0.30);
                border-radius:10px;font-size:0.82rem;color:#6FA8C0;margin-bottom:1.4rem;">
        💡 <span><b>Auto-suggested budgets</b> are computed from your historical daily average × 30.4 days.
        This reflects your actual spend pattern — it is not a user-configured budget.</span>
    </div>
    """, unsafe_allow_html=True)

    # Compute suggested (historical avg × 30.4) and actual (last 30 days)
    last_30   = df.tail(30)
    suggested = {c: df[c].mean() * 30.4 for c in cat_cols}
    actual_30 = {c: last_30[c].sum()     for c in cat_cols}

    total_sug = sum(suggested.values())
    total_act = sum(actual_30.values())
    util_pct  = (total_act / total_sug * 100) if total_sug > 0 else 0

    kc1, kc2, kc3 = st.columns(3, gap="small")
    for col, lbl, val, delta, ddir, ic, bg in [
        (kc1, "Suggested Monthly",  f"${total_sug:,.0f}", "Historical avg × 30.4d", "flat",                                     "🎯", "rgba(178,213,229,0.25)"),
        (kc2, "Actual Last 30 Days", f"${total_act:,.0f}", "All categories",         "down" if total_act > total_sug else "flat", "💳", "rgba(240,160,75,0.18)"),
        (kc3, "Budget Utilization",  f"{util_pct:.0f}%",   "vs suggested",           "down" if util_pct > 100 else "up",          "📊", "rgba(91,184,150,0.18)"),
    ]:
        with col:
            st.markdown(kpi_html(lbl, val, delta, ddir, ic, bg), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

    col_bars, col_chart = st.columns([1.1, 1], gap="large")

    with col_bars:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(section_header("Actual vs Suggested per Category", "📊"), unsafe_allow_html=True)
        for cat in sorted(cat_cols, key=lambda c: actual_30[c], reverse=True):
            sug = suggested[cat]
            act = actual_30[cat]
            if sug <= 0:
                continue
            pct       = act / sug * 100
            over      = pct > 100
            bar_width = min(pct, 100)
            bar_color = (f"linear-gradient(90deg,{DANGER},#ff9090)"
                         if over else
                         f"linear-gradient(90deg,{SUCCESS},#8ed8bb)")
            st.markdown(f"""
            <div class="budget-row">
                <div class="budget-cat">{cat.replace("_"," ").title()}</div>
                <div class="budget-bar-wrap">
                    <div class="budget-bar" style="width:{bar_width:.1f}%;background:{bar_color};"></div>
                </div>
                <div class="budget-amounts">
                    ${act:,.0f} / ${sug:,.0f} {"⚠️" if over else "✅"}
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chart:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(section_header("Side-by-Side Comparison", "📈"), unsafe_allow_html=True)
        if PLOTLY_AVAILABLE:
            cats_s = sorted(cat_cols, key=lambda c: actual_30[c], reverse=True)
            fig_b = go.Figure(data=[
                go.Bar(name="Suggested", x=cats_s, y=[suggested[c] for c in cats_s],
                       marker_color=CANDY_BLUE, opacity=0.75,
                       hovertemplate="%{x}<br>Suggested: $%{y:,.0f}<extra></extra>"),
                go.Bar(name="Actual 30d", x=cats_s, y=[actual_30[c] for c in cats_s],
                       marker_color=ORCHID,
                       hovertemplate="%{x}<br>Actual: $%{y:,.0f}<extra></extra>"),
            ])
            fig_b.update_layout(
                barmode="group", height=300,
                margin=dict(l=10, r=10, t=10, b=65),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=11, family="Inter"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(showgrid=False, tickangle=-35,
                           tickfont=dict(family="Inter", size=10, color=SLATE)),
                yaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                           tickprefix="$", tickformat=",.0f",
                           tickfont=dict(family="Inter", size=11, color=SLATE), zeroline=False),
                bargap=0.22, bargroupgap=0.06,
            )
            st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

def render_view_settings():
    st.markdown(section_header("Settings", "⚙️"), unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:0.8rem 1rem;
                background:rgba(240,160,75,0.08);border:1px solid rgba(240,160,75,0.28);
                border-radius:10px;font-size:0.82rem;color:#c07830;margin-bottom:1.8rem;">
        ⚠️ <span>Settings are <b>read-only in this demo</b>. Values shown are the defaults used by the dashboard.</span>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([1, 1], gap="large")

    with col_s1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="settings-section-title">📊 Display Preferences</div>', unsafe_allow_html=True)
        st.text_input("Currency Symbol", value="$", disabled=True,
                      help="Symbol prepended to all monetary values.")
        st.selectbox("Date Format",
                     ["MMM DD, YYYY", "DD/MM/YYYY", "YYYY-MM-DD"], disabled=True)
        st.selectbox("Fiscal Year Start",
                     ["January", "April", "July", "October"], disabled=True)
        st.toggle("Dark Mode", value=False, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_s2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="settings-section-title">🛡️ Risk & Alerts</div>', unsafe_allow_html=True)
        st.number_input("Safety Buffer ($)", value=2000, min_value=0,
                        max_value=50000, step=500, disabled=True,
                        help="Minimum balance threshold on the forecast chart.")
        st.slider("Anomaly Sensitivity", min_value=0, max_value=100, value=70,
                  disabled=True, help="Threshold for flagging transactions as anomalous.")
        st.selectbox("Alert Method", ["Dashboard Only", "Email", "Slack"], disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)
    col_s3, col_s4 = st.columns([1, 1], gap="large")

    with col_s3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="settings-section-title">🔄 Data Pipeline</div>', unsafe_allow_html=True)
        st.text_input("Data Directory", value="./data/", disabled=True,
                      help="Directory where CSV/JSON data files are read from.")
        st.number_input("Cache TTL (seconds)", value=60, disabled=True,
                        help="How frequently the dashboard re-reads data from disk.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_s4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="settings-section-title">📑 About</div>', unsafe_allow_html=True)
        for lbl, val in [
            ("App",       "CashFlow Radar"),
            ("Version",   "1.0.0"),
            ("Built for", "GenAI APAC Hackathon"),
            ("Engine",    "RAPIDS cuDF + cuML"),
            ("UI",        "Streamlit + Plotly"),
        ]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.4rem 0;'
                f'border-bottom:1px solid rgba(178,213,229,0.15);font-size:0.83rem;">'
                f'<span style="color:{SLATE};">{lbl}</span>'
                f'<span style="font-weight:600;color:{ONYX};">{val}</span></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
    col_btn, _ = st.columns([0.28, 0.72])
    with col_btn:
        if st.button("💾  Save Settings", use_container_width=True, type="primary"):
            st.info("Settings are read-only in this demo — no changes were saved.", icon="ℹ️")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Layout Assembly  (session_state view dispatch)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.markdown('''
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
''', unsafe_allow_html=True)
    inject_css()

    # Initialise view state
    if "current_view" not in st.session_state:
        st.session_state.current_view = "Dashboard"
    view = st.session_state.current_view

    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)

    # Sidebar (always rendered regardless of active view)
    render_sidebar(data_dir)

    # Load all data once (cached, TTL=60s)
    summary_df   = load_csv("daily_summary.csv")
    anomalies_df = load_csv("anomalies.csv")
    forecast_df  = load_csv("forecast.csv")
    risk_data    = load_json("risk_score.json")
    bench_df     = load_benchmark()

    # ── Dynamic page header ──
    view_subtitles = {
        "Dashboard":    ("My Dashboard",   "CashFlow Radar › Overview",
                         "GPU-accelerated financial intelligence &amp; anomaly detection."),
        "Accounts":     ("Accounts",       "CashFlow Radar › Accounts",
                         "Single-account balance history and statistics."),
        "Transactions": ("Transactions",   "CashFlow Radar › Transactions",
                         "Flagged transactions and daily aggregates from your data pipeline."),
        "Analytics":    ("Analytics",      "CashFlow Radar › Analytics",
                         "Monthly trends, category rankings, and spend highlights."),
        "Budgets":      ("Budgets",        "CashFlow Radar › Budgets",
                         "Auto-suggested monthly budgets based on your historical spend pattern."),
        "Settings":     ("Settings",       "CashFlow Radar › Settings",
                         "Dashboard configuration (read-only in this demo)."),
    }
    h1, breadcrumb, subtitle = view_subtitles.get(view, (view, f"CashFlow Radar › {view}", ""))
    st.markdown(f"""
    <div style="display:flex;align-items:baseline;gap:14px;margin-bottom:0.2rem;">
        <h1 style="font-size:1.8rem;font-weight:700;letter-spacing:-0.04em;color:#1D1D1D;margin:0;">
            {h1}
        </h1>
        <span style="font-size:0.8rem;color:#8FA8B8;font-weight:500;">{breadcrumb}</span>
    </div>
    <div style="font-size:0.82rem;color:#8FA8B8;margin-bottom:1.4rem;">{subtitle}</div>
    """, unsafe_allow_html=True)

    # ── View dispatch ──
    if view == "Dashboard":
        render_kpi_strip(summary_df, risk_data)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
        render_hero_and_risk(summary_df, risk_data, forecast_df)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
        col_fc, col_anom = st.columns([1.6, 1], gap="large")
        with col_fc:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_forecast(forecast_df)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_anom:
            st.markdown('<div class="glass-card" style="height:100%;">', unsafe_allow_html=True)
            render_anomaly_alerts(anomalies_df)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_spend_breakdown(summary_df)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_benchmark(bench_df)
        st.markdown('</div>', unsafe_allow_html=True)

    elif view == "Accounts":
        render_view_accounts(summary_df)

    elif view == "Transactions":
        render_view_transactions(summary_df, anomalies_df)

    elif view == "Analytics":
        render_view_analytics(summary_df)

    elif view == "Budgets":
        render_view_budgets(summary_df)

    elif view == "Settings":
        render_view_settings()

    # ── Footer (shown on all views) ──
    st.markdown("""
    <div style="text-align:center;font-size:0.73rem;color:#8FA8B8;
                padding:1.5rem 0 0.5rem;margin-top:2rem;
                border-top:1px solid rgba(178,213,229,0.2);">
        📡 <b>CashFlow Radar</b> &nbsp;·&nbsp; Built for GenAI APAC Hackathon &nbsp;·&nbsp;
        Powered by RAPIDS cuDF &amp; cuML &nbsp;·&nbsp; Dashboard by Streamlit
    </div>
    """, unsafe_allow_html=True)



# ── Auto-launch if run directly (python app.py) ──
if __name__ == "__main__":
    is_streamlit = False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        is_streamlit = get_script_run_ctx() is not None
    except Exception:
        pass

    if not is_streamlit:
        import sys
        try:
            from streamlit.web import cli as stcli
            sys.argv = ["streamlit", "run", os.path.abspath(__file__)] + sys.argv[1:]
            sys.exit(stcli.main())
        except Exception as e:
            print(f"Run: streamlit run app.py  ({e})")
    else:
        main()
