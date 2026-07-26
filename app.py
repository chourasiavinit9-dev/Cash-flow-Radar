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

try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    GROQ_SDK_AVAILABLE = False


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
    @import url('https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.31.0/dist/tabler-icons.min.css');

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
        /* ── Liquid Glass tokens ── */
        --specular:     rgba(255, 255, 255, 0.50);
        --inset-glow:   inset 0 1px 1px rgba(255, 255, 255, 0.40);
        --liquid-blur:  blur(20px) saturate(180%);
    }

    /* ── Ambient background blob keyframes ── */
    @keyframes blobDrift1 {
        0%   { transform: translate(0%,  0%) scale(1);    }
        33%  { transform: translate(3%, -4%) scale(1.04); }
        66%  { transform: translate(-2%, 3%) scale(0.97); }
        100% { transform: translate(0%,  0%) scale(1);    }
    }
    @keyframes blobDrift2 {
        0%   { transform: translate(0%,  0%) scale(1);    }
        40%  { transform: translate(-4%, 2%) scale(1.03); }
        75%  { transform: translate(3%, -3%) scale(0.98); }
        100% { transform: translate(0%,  0%) scale(1);    }
    }
    @keyframes blobDrift3 {
        0%   { transform: translate(0%,  0%) scale(1);    }
        50%  { transform: translate(2%,  4%) scale(1.02); }
        100% { transform: translate(0%,  0%) scale(1);    }
    }

    /* ── Ambient blobs: blob 1 (candy-blue, top-left) & blob 2 (orchid, bottom-right) ── */
    .stApp::before,
    .stApp::after {
        content: '';
        position: fixed;
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
        filter: blur(80px);
        will-change: transform;
    }
    .stApp::before {
        width: 520px; height: 520px;
        top: -80px; left: -100px;
        background: radial-gradient(circle, rgba(178,213,229,0.22) 0%, transparent 70%);
        animation: blobDrift1 28s ease-in-out infinite;
    }
    .stApp::after {
        width: 440px; height: 440px;
        bottom: -60px; right: -80px;
        background: radial-gradient(circle, rgba(229,189,223,0.18) 0%, transparent 70%);
        animation: blobDrift2 34s ease-in-out infinite;
    }

    /* ── Ambient blob 3: deep-blue, mid-screen ── */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        width: 360px; height: 360px;
        top: 40%; left: 55%;
        background: radial-gradient(circle, rgba(111,168,192,0.11) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
        filter: blur(70px);
        animation: blobDrift3 22s ease-in-out infinite;
        will-change: transform;
    }

    /* ── Global reset (scoped to app view container, excluding popovers/menus) ── */
    html, body, [data-testid="stAppViewContainer"] {
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
        position: relative;
        z-index: 1;
    }

    /* ── Sidebar — Liquid Glass ── */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.78) !important;
        backdrop-filter: var(--liquid-blur) !important;
        -webkit-backdrop-filter: var(--liquid-blur) !important;
        border-right: 1.5px solid var(--glass-border) !important;
        border-top: 1px solid var(--specular) !important;
        box-shadow: var(--shadow-md), var(--inset-glow) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.8rem;
    }

    /* ── Glass Card base — Liquid Glass ── */
    .glass-card, [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--glass-bg) !important;
        backdrop-filter: var(--liquid-blur) !important;
        -webkit-backdrop-filter: var(--liquid-blur) !important;
        border: 1.5px solid var(--glass-border) !important;
        border-top-color: rgba(255,255,255,0.55) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-md), var(--inset-glow) !important;
        padding: 1.4rem 1.6rem !important;
        margin-bottom: 1rem !important;
        transition: box-shadow 0.25s ease, transform 0.25s ease, backdrop-filter 0.25s ease !important;
        position: relative;
        overflow: hidden;
    }
    /* Specular top-edge shimmer on glass cards */
    .glass-card::before, [data-testid="stVerticalBlockBorderWrapper"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.60) 40%, rgba(255,255,255,0.60) 60%, transparent 100%);
        pointer-events: none;
        z-index: 2;
    }
    .glass-card:hover, [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: var(--shadow-lg), inset 0 1px 2px rgba(255,255,255,0.50) !important;
        transform: translateY(-2px);
        backdrop-filter: blur(24px) saturate(200%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(200%) !important;
    }
    .glass-card:empty, .risk-card:empty,
    [data-testid="stVerticalBlockBorderWrapper"]:empty {
        display: none !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        box-shadow: none !important;
        height: 0 !important;
    }

    /* ── KPI metric cards — Liquid Glass ── */
    .kpi-card {
        background: var(--glass-bg);
        backdrop-filter: var(--liquid-blur);
        -webkit-backdrop-filter: var(--liquid-blur);
        border: 1.5px solid var(--glass-border);
        border-top-color: rgba(255,255,255,0.60);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm), var(--inset-glow);
        padding: 1.1rem 1.4rem;
        text-align: left;
        min-height: 90px;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    /* Specular top-edge shimmer on KPI cards */
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.55) 35%, rgba(255,255,255,0.55) 65%, transparent 100%);
        pointer-events: none;
        z-index: 2;
    }
    .kpi-card:hover {
        box-shadow: var(--shadow-md), inset 0 1px 2px rgba(255,255,255,0.50);
        transform: translateY(-2px);
        backdrop-filter: blur(24px) saturate(200%);
        -webkit-backdrop-filter: blur(24px) saturate(200%);
    }
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

    /* ── Hero balance card — Liquid Glass ── */
    .hero-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.88) 0%, rgba(240,246,250,0.92) 100%);
        backdrop-filter: var(--liquid-blur);
        -webkit-backdrop-filter: var(--liquid-blur);
        border: 1.5px solid var(--glass-border);
        border-top-color: rgba(255,255,255,0.65);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg), var(--inset-glow);
        padding: 2rem 2.2rem;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.25s ease, transform 0.25s ease;
    }
    .hero-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.70) 30%, rgba(255,255,255,0.70) 70%, transparent 100%);
        pointer-events: none;
        z-index: 2;
    }
    .hero-card:hover {
        box-shadow: var(--shadow-lg), inset 0 1px 2px rgba(255,255,255,0.55);
        transform: translateY(-2px);
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

    /* ── Risk Score gauge card — Liquid Glass ── */
    .risk-card {
        background: linear-gradient(160deg, rgba(229,189,223,0.20) 0%, rgba(255,255,255,0.82) 100%);
        backdrop-filter: var(--liquid-blur);
        -webkit-backdrop-filter: var(--liquid-blur);
        border: 1.5px solid rgba(229,189,223,0.42);
        border-top-color: rgba(255,255,255,0.60);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-md), var(--inset-glow);
        padding: 1.6rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.25s ease, transform 0.25s ease;
    }
    .risk-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.62) 40%, rgba(255,255,255,0.62) 60%, transparent 100%);
        pointer-events: none;
        z-index: 2;
    }
    .risk-card:hover {
        box-shadow: var(--shadow-lg), inset 0 1px 2px rgba(255,255,255,0.50);
        transform: translateY(-2px);
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

    /* ── Buttons (scoped to standard Streamlit button containers) ── */
    [data-testid="stElementContainer"] > div.stButton > button {
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
    [data-testid="stElementContainer"] > div.stButton > button:hover {
        background: var(--candy-blue) !important;
        border-color: var(--deep-blue) !important;
        color: #fff !important;
        box-shadow: 0 4px 16px rgba(111,168,192,0.30) !important;
    }
    [data-testid="stElementContainer"] > div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--candy-blue), var(--deep-blue)) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 16px rgba(111,168,192,0.35) !important;
    }

    /* ── Protect Streamlit Dataframe Column Menus & Popovers ── */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="popover"] *,
    [data-testid="stDataFrame"] *,
    div[class*="glide-data-grid"] * {
        box-sizing: border-box;
    }
    [data-baseweb="popover"] button,
    [data-testid="stDataFrame"] button {
        background: unset !important;
        border: unset !important;
        border-radius: unset !important;
        padding: unset !important;
        box-shadow: unset !important;
    }

    /* ── Plotly chart background ── */
    .js-plotly-plot .plotly, .js-plotly-plot .plotly .gl-container {
        background: transparent !important;
    }
    .stPlotlyChart { border-radius: var(--radius-md); overflow: hidden; }

    /* ── Dividers ── */
    hr { border-color: rgba(178,213,229,0.25) !important; margin: 1.2rem 0 !important; }

    /* ── Streamlit metric override — Liquid Glass ── */
    [data-testid="stMetric"] {
        background: var(--glass-bg);
        backdrop-filter: var(--liquid-blur);
        -webkit-backdrop-filter: var(--liquid-blur);
        border: 1.5px solid var(--glass-border);
        border-top-color: rgba(255,255,255,0.55);
        border-radius: var(--radius-md);
        padding: 1rem 1.2rem;
        box-shadow: var(--shadow-sm), var(--inset-glow);
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
        transition: all 0.18s ease;
    }
    .nav-item:hover  { background: rgba(178,213,229,0.18); color: var(--onyx); }
    .nav-item.active { background: rgba(178,213,229,0.30); color: var(--onyx); font-weight: 600; box-shadow: inset 3px 0 0 var(--deep-blue); }

    /* ── Nav icon — Tabler icon font ── */
    .nav-ti {
        font-family: 'tabler-icons' !important;
        font-style: normal;
        font-size: 1.15rem;
        line-height: 1;
        width: 22px; height: 22px;
        display: inline-flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        color: var(--slate);
        transition: color 0.18s ease;
    }
    .nav-item:hover .nav-ti,
    .nav-item.active .nav-ti { color: var(--deep-blue); }


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
    /* Keep sidebar pinned open */
    [data-testid="stSidebar"] { display: block !important; transform: none !important; }

    /* ── Sidebar nav BUTTONS — transparent overlay on top of .nav-inactive div ── */
    [data-testid="stSidebar"] .stButton > button {
        display: flex !important;
        align-items: center !important;
        height: 42px !important;
        min-height: 42px !important;
        padding: 0 0.8rem !important;
        border-radius: 10px !important;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        width: 100% !important;
        cursor: pointer !important;
        opacity: 0 !important;
        margin-top: -42px !important;
        margin-bottom: 2px !important;
        position: relative !important;
        z-index: 10 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:focus:not(:active) {
        box-shadow: none !important;
        outline: none !important;
        background: transparent !important;
    }
    /* Nav inactive HTML div — visual only */
    .nav-inactive {
        pointer-events: none;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] {
        margin-bottom: 0 !important;
    }


    /* ── Stat cards (Accounts view) — Liquid Glass ── */
    .stat-card {
        background: var(--glass-bg);
        backdrop-filter: var(--liquid-blur);
        -webkit-backdrop-filter: var(--liquid-blur);
        border: 1.5px solid var(--glass-border);
        border-top-color: rgba(255,255,255,0.55);
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm), var(--inset-glow);
        padding: 1rem 1.2rem;
        text-align: center;
        margin-bottom: 0.6rem;
        transition: box-shadow 0.25s ease, transform 0.25s ease;
    }
    .stat-card:hover {
        box-shadow: var(--shadow-md), inset 0 1px 2px rgba(255,255,255,0.50);
        transform: translateY(-2px);
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


def get_currency_symbol() -> str:
    return st.session_state.get("currency_symbol", "$")


def get_safety_buffer() -> float:
    return float(st.session_state.get("safety_buffer", 1000.0))


def fmt_curr(val: float, decimals: int = 0) -> str:
    sym = get_currency_symbol()
    if val < 0:
        return f"-{sym}{abs(val):,.{decimals}f}"
    return f"{sym}{val:,.{decimals}f}"


def compute_dynamic_risk(risk_data: dict | None, forecast_df: pd.DataFrame | None = None) -> tuple[float, str, str, str, str]:
    safety_buffer = get_safety_buffer()
    base_score = float(risk_data.get("score", 26.1)) if risk_data else 26.1
    
    if forecast_df is not None and "projected_balance" in forecast_df.columns:
        min_proj = float(forecast_df["projected_balance"].min())
        diff = min_proj - safety_buffer
        if diff >= 700:
            score = max(10.0, min(39.0, 26.1 - (diff - 781.95) / 100.0))
        elif diff >= 0:
            score = 35.0 + (1000 - diff) / 1000.0 * 10.0
        elif diff >= -1500:
            score = 45.0 + (abs(diff) / 1500.0) * 25.0
        else:
            score = min(98.0, 70.0 + (abs(diff + 1500) / 2000.0) * 28.0)
    else:
        # Adjustment relative to standard $1000 buffer baseline
        diff = 1000.0 - safety_buffer
        score = max(5.0, min(95.0, base_score - diff / 100.0))

    score = round(score, 1)
    if score < 40:
        badge_cls, badge_lbl, score_color = "low", "Healthy", "#5BB896"
        expl = f"Healthy cash flow. Projected balance stays comfortably above your {fmt_curr(safety_buffer)} safety buffer over the next 30 days."
    elif score < 70:
        badge_cls, badge_lbl, score_color = "medium", "Moderate Risk", "#F0A04B"
        expl = f"Moderate risk detected. Projected balance comes close to or dips slightly below your {fmt_curr(safety_buffer)} safety buffer."
    else:
        badge_cls, badge_lbl, score_color = "high", "High Risk", "#E07070"
        expl = f"High risk alert! Projected balance falls significantly below your {fmt_curr(safety_buffer)} safety buffer over the next 30 days."

    return score, badge_cls, badge_lbl, score_color, expl


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
                        box-shadow:0 4px 12px rgba(178,213,229,0.4);">
                <i class='ti ti-radar-2' style='font-size:1.3rem;color:#1D1D1D;'></i>
            </div>
            <div>
                <div style="font-size:1.0rem;font-weight:700;color:#1D1D1D;letter-spacing:-0.02em;">CashFlow Radar</div>
                <div style="font-size:0.68rem;color:#8FA8B8;font-weight:500;">Financial Intelligence</div>
            </div>
        </div>
        """, unsafe_allow_html=True)



        # ── Navigation — Tabler Icons only (no base64, fast, reliable clicks) ──
        NAV_ITEMS = [
            ("ti-layout-dashboard",  "Dashboard"),
            ("ti-credit-card",       "Accounts"),
            ("ti-arrows-exchange",   "Transactions"),
            ("ti-chart-bar",         "Analytics"),
            ("ti-target",            "Budgets"),
            ("ti-adjustments-horizontal", "Simulator"),
            ("ti-file-analytics",    "Reports"),
            ("ti-settings",          "Settings"),
        ]

        def _switch_view(view_name: str):
            st.session_state.current_view = view_name

        current = st.session_state.get("current_view", "Dashboard")
        for ti_class, label in NAV_ITEMS:
            icon_html = f'<i class="ti {ti_class}" style="font-size:1.15rem;width:22px;flex-shrink:0;color:inherit;"></i>'
            if current == label:
                st.markdown(
                    f'<div class="nav-item active">{icon_html}<span>{label}</span></div>',
                    unsafe_allow_html=True
                )
            else:
                # Use markdown for inactive too — wrap a full clickable nav item
                # with an overlapping transparent Streamlit button on top for click handling
                st.markdown(
                    f'<div class="nav-item nav-inactive" id="nav-{label}">{icon_html}<span>{label}</span></div>',
                    unsafe_allow_html=True
                )
                st.button(
                    label,
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


def generate_insight_fallback(query: str, curr_bal: float, score: float, badge_lbl: str, expl: str, min_proj: float) -> str:
    import re
    safety = get_safety_buffer()
    match = re.search(r'\$?(\d+[\d,.]*)', query)
    if match:
        try:
            amt = float(match.group(1).replace(',', ''))
            remaining_after = min_proj - amt
            if remaining_after >= safety:
                return (f"Based on your current balance of {fmt_curr(curr_bal)} and 30-day projected balance minimum of {fmt_curr(min_proj)}, "
                        f"you can comfortably afford this {fmt_curr(amt)} purchase while maintaining your {fmt_curr(safety)} safety buffer. "
                        f"Your overall cash flow remains healthy with a risk score of {score}/100 ({badge_lbl}).")
            else:
                shortfall = safety - remaining_after
                return (f"Caution advised: a {fmt_curr(amt)} purchase would bring your projected balance down to {fmt_curr(remaining_after)}, "
                        f"which is {fmt_curr(shortfall)} below your {fmt_curr(safety)} safety buffer. "
                        f"Your current risk score is {score}/100 ({badge_lbl}).")
        except Exception:
            pass
    return (f"Your portfolio balance is currently {fmt_curr(curr_bal)} with a 30-day risk score of {score}/100 ({badge_lbl}). "
            f"{expl} Keep an eye on upcoming recurring expenses and anomaly alerts before making large discretionary purchases.")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: MONEY WEATHER FORECAST CARD
# ─────────────────────────────────────────────────────────────────────────────

def render_money_weather(risk_data: dict | None, forecast_df: "pd.DataFrame | None"):
    """Single-glance weather-metaphor card — reuses compute_dynamic_risk + forecast_df."""
    score, _, _, _, _ = compute_dynamic_risk(risk_data, forecast_df)

    # Check for first negative balance day in forecast
    negative_day = None
    if forecast_df is not None and "projected_balance" in forecast_df.columns and "date" in forecast_df.columns:
        neg_rows = forecast_df[forecast_df["projected_balance"] < 0]
        if not neg_rows.empty:
            negative_day = neg_rows.iloc[0]["date"]

    # Determine weather state
    if negative_day is not None or score > 70:
        if negative_day:
            headline = f"⛈️ Cash Storm — negative balance projected on {negative_day}"
        else:
            headline = "⛈️ Cash Storm — high risk of negative balance ahead"
        weather_color = "#E07070"
        bg_color = "rgba(224,112,112,0.10)"
        border_color = "rgba(224,112,112,0.30)"
        bar_pct = min(int(score), 100)
        bar_color = "#E07070"
    elif score >= 50:
        headline = "🌧️ Heavy Spending — watch your cash closely"
        weather_color = "#F0A04B"
        bg_color = "rgba(240,160,75,0.10)"
        border_color = "rgba(240,160,75,0.30)"
        bar_pct = int(score)
        bar_color = "#F0A04B"
    elif score >= 30:
        headline = "🌤️ Slight Risk — possible tight days ahead"
        weather_color = "#6FA8C0"
        bg_color = "rgba(111,168,192,0.10)"
        border_color = "rgba(178,213,229,0.40)"
        bar_pct = int(score)
        bar_color = "#6FA8C0"
    else:
        headline = "☀️ Sunny — cash flow is healthy"
        weather_color = "#5BB896"
        bg_color = "rgba(91,184,150,0.10)"
        border_color = "rgba(91,184,150,0.30)"
        bar_pct = int(score)
        bar_color = "#5BB896"

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1.2rem;
                padding:1rem 1.3rem;
                background:{bg_color};
                border:1.5px solid {border_color};
                border-radius:16px;
                margin-bottom:0.2rem;">
        <div style="font-size:2.4rem;line-height:1;">{headline.split()[0]}</div>
        <div style="flex:1;">
            <div style="font-size:1.0rem;font-weight:700;color:{weather_color};letter-spacing:-0.01em;">
                {headline}
            </div>
            <div style="margin-top:6px;background:rgba(0,0,0,0.08);border-radius:6px;height:5px;width:100%;">
                <div style="width:{bar_pct}%;height:5px;border-radius:6px;
                            background:{bar_color};transition:width 0.4s;"></div>
            </div>
            <div style="font-size:0.73rem;color:#8FA8B8;margin-top:4px;">
                Risk score: {score}/100
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: AI CASH FLOW STORY CARD
# ─────────────────────────────────────────────────────────────────────────────

def render_cash_flow_story(summary_df: "pd.DataFrame | None", risk_data: dict | None, forecast_df: "pd.DataFrame | None"):
    """Gemini-generated 3–4 sentence narrative — reuses existing Gemini client setup."""
    # ── Derive context from existing loaded data ──
    score, _, badge_lbl, _, expl = compute_dynamic_risk(risk_data, forecast_df)

    total_income = 0.0
    total_expense = 0.0
    top_category = "Misc"
    if summary_df is not None:
        if "Income" in summary_df.columns:
            total_income = float(summary_df["Income"].sum())
        if "total_spend" in summary_df.columns:
            total_expense = float(summary_df["total_spend"].sum())
        cat_cols = [c for c in ["Food","Hardware","Misc","Rent","Software"] if c in summary_df.columns]
        if cat_cols:
            top_category = summary_df[cat_cols].sum().idxmax()

    # First negative forecast day (if any)
    negative_day = None
    if forecast_df is not None and "projected_balance" in forecast_df.columns and "date" in forecast_df.columns:
        neg_rows = forecast_df[forecast_df["projected_balance"] < 0]
        if not neg_rows.empty:
            negative_day = neg_rows.iloc[0]["date"]

    negative_day_str = f"The first projected negative balance falls on {negative_day}." if negative_day else "No negative balance is projected in the 30-day window."

    # ── Groq API key (same pattern as render_insight_panel) ──
    api_key = None
    try:
        if hasattr(st, "secrets") and st.secrets:
            if "GROQ_API_KEY" in st.secrets:
                api_key = str(st.secrets["GROQ_API_KEY"])
            elif "secrets" in st.secrets and "GROQ_API_KEY" in st.secrets["secrets"]:
                api_key = str(st.secrets["secrets"]["GROQ_API_KEY"])
    except Exception:
        api_key = None
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY", "")

    story_text = None
    if GROQ_SDK_AVAILABLE and api_key and api_key.strip():
        try:
            _client = Groq(api_key=api_key.strip())
            prompt = f"""You are a friendly personal finance assistant. Write a 3-4 sentence narrative summary of this person's cash flow situation in plain, conversational language — no bullet points, no headers.

Financial context:
- Total income tracked: ${total_income:,.0f}
- Total expenses tracked: ${total_expense:,.0f}
- Biggest expense category: {top_category}
- Cash-flow risk score: {score}/100 ({badge_lbl})
- Risk explanation: {expl}
- Forecast note: {negative_day_str}

Keep it warm, honest, and actionable. Do not use bullet points."""
            res = _client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a financial assistant. Answer ONLY using the provided data."},
                    {"role": "user", "content": prompt},
                ],
            )
            story_text = res.choices[0].message.content.strip()
        except Exception:
            story_text = None

    # ── Fallback f-string narrative (always has real numbers) ──
    if story_text is None:
        net = total_income - total_expense
        net_str = f"a net {'surplus' if net >= 0 else 'deficit'} of ${abs(net):,.0f}"
        story_text = (
            f"Over the tracked period, your portfolio recorded ${total_income:,.0f} in income against "
            f"${total_expense:,.0f} in expenses, leaving {net_str}. "
            f"Your biggest spend area is {top_category}, which is worth keeping an eye on. "
            f"With a risk score of {score}/100 ({badge_lbl}), your cash flow is {badge_lbl.lower()} right now. "
            f"{negative_day_str}"
        )

    st.markdown(f"""
    <div style="padding:0 0 0.6rem 0;">
        <div style="font-size:0.72rem;font-weight:700;color:#6FA8C0;text-transform:uppercase;
                    letter-spacing:0.07em;margin-bottom:0.5rem;">📖 Your Cash Flow Story</div>
        <div style="font-size:0.88rem;line-height:1.65;color:#2C3E50;">
            {story_text}
        </div>
        <div style="font-size:0.68rem;color:#B0C4D0;margin-top:0.6rem;text-align:right;">
            ✨ {'AI-generated by Groq' if (GROQ_SDK_AVAILABLE and api_key and story_text) else 'Smart summary'}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: HIDDEN MONEY FINDER CARD
# ─────────────────────────────────────────────────────────────────────────────

def render_hidden_money_finder(anomalies_df: "pd.DataFrame | None"):
    """Surfaces anomalies reframed as savings opportunities — reuses anomalies_df, no re-detection."""
    if anomalies_df is None or anomalies_df.empty:
        st.markdown("""
        <div style="padding:1rem;text-align:center;color:#8FA8B8;font-size:0.85rem;">
            💰 No anomalies detected yet — your spending looks clean!
        </div>""", unsafe_allow_html=True)
        return

    df = anomalies_df.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["abs_amount"] = df["amount"].abs()

    # Classify each row: "duplicate" if reason contains duplicate, else "vendor_spike"
    def _classify(reason: str) -> str:
        r = str(reason).lower()
        if "duplicate" in r:
            return "duplicate"
        return "vendor_spike"

    df["anom_type"] = df["reason"].apply(_classify)

    # Savings calculation per spec:
    # - duplicate: full amount
    # - vendor_spike: 30% of amount as "delta above baseline" estimate (no baseline column exists)
    dup_df = df[df["anom_type"] == "duplicate"]
    spike_df = df[df["anom_type"] == "vendor_spike"]

    dup_savings = dup_df["abs_amount"].sum()
    spike_savings = (spike_df["abs_amount"] * 0.30).sum()
    total_savings = dup_savings + spike_savings

    # Build human-readable finding lines
    findings = []
    for _, row in df.iterrows():
        merchant = str(row.get("merchant", "Unknown vendor")).replace("_", " ").title()
        date_str = str(row.get("date", ""))
        amt = row["abs_amount"]
        cat = str(row.get("category", ""))
        if row["anom_type"] == "duplicate":
            findings.append(f"<li><b>{merchant}</b> charged twice on {date_str} — possible duplicate, <b>${amt:,.2f}</b></li>")
        else:
            above = amt * 0.30
            findings.append(f"<li><b>{merchant}</b> ({cat}) on {date_str} — unusually high, ~<b>${above:,.2f}</b> above typical spend</li>")

    findings_html = "<ul style='margin:0.5rem 0 0 0;padding-left:1.2rem;'>" + "".join(findings) + "</ul>"

    st.markdown(f"""
    <div>
        <div style="font-size:0.72rem;font-weight:700;color:#6FA8C0;text-transform:uppercase;
                    letter-spacing:0.07em;margin-bottom:0.5rem;">💰 Hidden Money Finder</div>
        <div style="font-size:1.35rem;font-weight:800;color:#5BB896;letter-spacing:-0.02em;margin-bottom:0.2rem;">
            We found ${total_savings:,.2f} you could save this month
        </div>
        <div style="font-size:0.82rem;color:#2C3E50;line-height:1.7;">
            {findings_html}
        </div>
        <div style="font-size:0.7rem;color:#B0C4D0;margin-top:0.7rem;">
            Based on {len(df)} flagged transaction{'s' if len(df) != 1 else ''} · Duplicates refundable · Spike savings estimated at 30% above baseline
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_insight_panel(summary_df: pd.DataFrame | None, risk_data: dict | None, forecast_df: pd.DataFrame | None, anomalies_df: pd.DataFrame | None):
    # Extract financial context from existing loaded data objects
    curr_bal = float(summary_df["running_balance"].dropna().iloc[-1]) if summary_df is not None and "running_balance" in summary_df.columns and not summary_df["running_balance"].dropna().empty else 0.0
    score, badge_cls, badge_lbl, score_color, expl = compute_dynamic_risk(risk_data, forecast_df)
    min_proj = float(forecast_df["projected_balance"].min()) if forecast_df is not None and "projected_balance" in forecast_df.columns and not forecast_df.empty else curr_bal
    
    fc_snippet = forecast_df[["date", "projected_balance"]].head(3).to_string(index=False) if forecast_df is not None and not forecast_df.empty else "N/A"
    anom_snippet = anomalies_df[["date", "merchant", "amount", "reason"]].head(4).to_string(index=False) if anomalies_df is not None and not anomalies_df.empty else "None"

    with st.container(border=True):
        col_hdr, col_badge = st.columns([1, 0.4])
        with col_hdr:
            st.markdown(section_header("CashFlow Insight", "🤖"), unsafe_allow_html=True)
        with col_badge:
            st.markdown(
                '<div style="text-align:right;margin-top:2px;">'
                '<span style="font-size:0.72rem;background:rgba(178,213,229,0.25);color:#1D1D1D;'
                'padding:3px 10px;border-radius:12px;border:1px solid rgba(178,213,229,0.4);font-weight:500;">'
                '✨ Powered by Groq</span></div>',
                unsafe_allow_html=True
            )

        user_query = st.text_input(
            "Ask your AI Financial Advisor",
            placeholder="e.g. Can I afford a $500 laptop next month? or What should I watch out for?",
            key="insight_user_input"
        )
        ask_btn = st.button("💬 Ask Radar", type="primary", key="insight_ask_btn")

        # Only run when user explicitly clicks Ask or presses Enter (query changed)
        _last_q   = st.session_state.get("_insight_last_q", "")
        _new_q    = (user_query or "").strip()
        _triggered = ask_btn or (_new_q and _new_q != _last_q)

        if _new_q and _triggered:
            st.session_state["_insight_last_q"] = _new_q  # update after triggering

            api_key = None
            try:
                if hasattr(st, "secrets") and st.secrets:
                    if "GROQ_API_KEY" in st.secrets:
                        api_key = str(st.secrets["GROQ_API_KEY"])
                    elif "secrets" in st.secrets and "GROQ_API_KEY" in st.secrets["secrets"]:
                        api_key = str(st.secrets["secrets"]["GROQ_API_KEY"])
            except Exception:
                api_key = None
            if not api_key:
                api_key = os.environ.get("GROQ_API_KEY", "")

            insight_answer = None
            groq_error     = None
            groq_attempted = False
            raw_response   = None

            if GROQ_SDK_AVAILABLE and api_key and api_key.strip():
                groq_attempted = True
                try:
                    with st.spinner("🤖 Thinking with Groq LLaMA 3.3..."):
                        _client = Groq(api_key=api_key.strip())
                        prompt = f"""You are CashFlow Insight, an AI financial advisor for CashFlow Radar.
Answer the user's question grounded ONLY in the financial context provided below.
Provide a clear, direct answer in 2 to 3 sentences in plain language.

[FINANCIAL CONTEXT]
- Current Portfolio Balance: {fmt_curr(curr_bal)}
- Cash-Flow Risk Score: {score}/100 ({badge_lbl}) — {expl}
- 30-Day Projected Balance (Next 3 Days):
{fc_snippet}
- Recent Flagged Anomalies:
{anom_snippet}

[USER QUESTION]
"{_new_q}"
"""
                        res = _client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "You are a financial assistant. Answer ONLY using the provided data."},
                                {"role": "user", "content": prompt},
                            ],
                        )
                        raw_response   = res.choices[0].message.content
                        insight_answer = raw_response.strip()
                except Exception as e:
                    # Use repr() so even empty-message exceptions produce a non-empty string
                    groq_error = repr(e) if repr(e) else f"{type(e).__name__}: (no message)"
                    insight_answer = None

            # Debug expander — always visible so we can inspect every call
            _key_loaded_display = "Yes" if api_key else "No"
            with st.expander("🔍 Debug info", expanded=False):
                st.markdown(f"**Question received:** `{_new_q}`")
                st.markdown(f"**SDK available:** `{GROQ_SDK_AVAILABLE}` &nbsp; | &nbsp; **Key loaded:** `{_key_loaded_display}`")
                st.markdown(f"**Groq call attempted:** `{groq_attempted}`")
                if groq_attempted and groq_error is None:
                    st.success(f"✅ Groq call succeeded")
                    st.code(raw_response or "(empty response)", language="text")
                elif groq_error:
                    st.error(f"❌ Groq exception: {groq_error}")
                else:
                    st.warning("⚠️ Groq not attempted (no key or SDK missing) — using rule-based fallback")

            # Fallback if Groq wasn't called or failed
            if insight_answer is None:
                insight_answer = generate_insight_fallback(_new_q, curr_bal, score, badge_lbl, expl, min_proj)

            # Error banner — guaranteed to show because groq_error is always non-empty on failure
            if groq_error:
                st.warning(f"⚠️ Groq API error — showing rule-based answer instead. Error: `{groq_error[:300]}`")

            # Cache answer in session_state so it persists across re-renders without re-calling API
            st.session_state["_insight_answer"] = insight_answer
            st.session_state["_insight_displayed_q"] = _new_q

        # Display the cached answer (persists across reruns without re-firing API)
        _cached_answer = st.session_state.get("_insight_answer")
        _cached_q      = st.session_state.get("_insight_displayed_q", "")
        if _cached_answer:
            st.markdown(f"""
            <div style="margin-top:0.8rem;padding:0.9rem 1.1rem;background:rgba(178,213,229,0.12);
                        border:1px solid rgba(178,213,229,0.35);border-radius:12px;font-size:0.86rem;
                        line-height:1.55;color:#1D1D1D;">
                <div style="font-weight:600;color:#6FA8C0;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:0.3rem;">💡 CashFlow Insight Response</div>
                {_cached_answer}
            </div>""", unsafe_allow_html=True)


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
        bal_str = fmt_curr(last_bal)
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

    # KPI 3: Monthly spend change (normalized per calendar month)
    if summary_df is not None and "total_spend" in summary_df.columns:
        df_tmp = summary_df.copy()
        df_tmp["date"] = pd.to_datetime(df_tmp["date"])
        df_tmp = df_tmp.sort_values("date")
        df_tmp["month"] = df_tmp["date"].dt.to_period("M")
        m_grouped = df_tmp.groupby("month")
        if len(m_grouped) >= 2:
            months = list(m_grouped.groups.keys())
            prev_df = m_grouped.get_group(months[-2])
            curr_df = m_grouped.get_group(months[-1])
            prev_daily = prev_df["total_spend"].sum() / max(len(prev_df), 1)
            curr_daily = curr_df["total_spend"].sum() / max(len(curr_df), 1)
            pct_change = ((curr_daily - prev_daily) / max(prev_daily, 0.01)) * 100
            chg_str   = f"{pct_change:+.1f}%"
            chg_dir   = "down" if pct_change > 0 else "up"   # more spend = bad
            chg_delta = "vs prior month"
        elif len(df_tmp) >= 30:
            avg_daily = df_tmp["total_spend"].mean()
            chg_str, chg_dir, chg_delta = f"{fmt_curr(avg_daily*30.4)}/mo", "flat", "monthly avg"
        else:
            chg_str, chg_dir, chg_delta = "N/A", "flat", "< 30 days data"
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
        avg_str   = fmt_curr(avg_spend)
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
            sym = get_currency_symbol()

            st.markdown(f"""
            <div class="hero-card">
                <div class="hero-label">Total Portfolio Balance</div>
                <div class="hero-amount" style="color:{bal_color}">{fmt_curr(last_bal, 2)}</div>
                <div class="hero-sub">{'Available Now' if last_bal > 0 else 'Deficit — Action Required'} &nbsp;•&nbsp; {sym}</div>
                <div style="margin-top:1.2rem;">
                    <span class="hero-badge">🕐 Last updated: {last_date}</span>
                    &nbsp;&nbsp;
                    <span class="hero-badge">📤 Daily spend: {fmt_curr(last_spend)}</span>
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
                    showlegend=False, hovertemplate=f"{sym}%{{y:,.0f}}<extra></extra>"
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
            score, badge_cls, badge_lbl, score_color, expl = compute_dynamic_risk(risk_data, forecast_df)

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
                with st.container(border=True):
                    st.markdown(f'<div class="section-header"><span class="dot" style="background:#E5BDDF;"></span>Cash-Flow Risk Score</div>', unsafe_allow_html=True)
                    st.plotly_chart(fig_gauge, width="stretch", config={"displayModeBar": False})
                    st.markdown(f'<div style="text-align:center;"><span class="risk-badge {badge_cls}">{badge_lbl}</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:0.75rem;color:#8FA8B8;text-align:center;margin-top:0.7rem;line-height:1.5;">{expl[:160]}{"…" if len(expl) > 160 else ""}</div>', unsafe_allow_html=True)
            else:
                # Plotly not available — render plain-text risk card (no empty gap)
                with st.container(border=True):
                    st.markdown(f'<div class="section-header"><span class="dot" style="background:#E5BDDF;"></span>Cash-Flow Risk Score</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="text-align:center;font-size:2.8rem;font-weight:700;color:{score_color};margin:0.8rem 0;">{score:.0f}<span style="font-size:1rem;color:#8FA8B8;">/100</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="text-align:center;"><span class="risk-badge {badge_cls}">{badge_lbl}</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:0.75rem;color:#8FA8B8;text-align:center;margin-top:0.7rem;line-height:1.5;">{expl[:160]}{"…" if len(expl) > 160 else ""}</div>', unsafe_allow_html=True)
        else:
            with st.container(border=True):
                st.markdown(no_data("🛡️", "No Risk Score", "Drop `risk_score.json` into `./data/`"), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION: FORECAST CHART
# ─────────────────────────────────────────────────────────────────────────────

def render_forecast(forecast_df: pd.DataFrame | None):
    st.markdown(section_header("30-Day Cash Flow Forecast", "📈"), unsafe_allow_html=True)

    if forecast_df is None:
        st.markdown(no_data("📈", "No Forecast Data", "Drop `forecast.csv` into `./data/`"), unsafe_allow_html=True)
        return

    fc = forecast_df.copy()
    sb_val = int(get_safety_buffer())
    sym = get_currency_symbol()
    safety_buffer = st.slider(
        f"Safety Buffer ({sym})", min_value=0, max_value=10000, value=sb_val, step=500,
        help="Minimum balance threshold — shown as a reference line on the chart",
        key="fc_safety_slider"
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
            hovertemplate=f"Lower: {sym}%{{y:,.0f}}<extra></extra>"
        ))
        # Main projected line
        fig.add_trace(go.Scatter(
            x=fc["date"], y=fc["projected_balance"],
            mode="lines+markers",
            line=dict(color=DEEP_BLUE, width=3, shape="spline"),
            marker=dict(size=5, color=ORCHID, line=dict(color=DEEP_BLUE, width=1.5)),
            name="Projected Balance",
            hovertemplate=f"<b>%{{x|%b %d}}</b><br>{sym}%{{y:,.0f}}<extra></extra>"
        ))
        # Safety buffer line
        fig.add_hline(
            y=safety_buffer,
            line_dash="dot", line_color="#E07070", line_width=1.8,
            annotation_text=f"  Safety Buffer {fmt_curr(safety_buffer)}",
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
                tickprefix=sym, tickformat=",.0f"
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
    if summary_df is None or summary_df.empty:
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
        with st.container(border=True):
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

    with col_cat:
        with st.container(border=True):
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

    st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

    # ── Row 2: Spending highlights callout + 7-day rolling ──
    col_hi, col_roll = st.columns([1, 1.5], gap="large")

    with col_hi:
        with st.container(border=True):
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

    with col_roll:
        with st.container(border=True):
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


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: BUDGETS
# ─────────────────────────────────────────────────────────────────────────────

def render_view_budgets(summary_df: pd.DataFrame | None):
    if summary_df is None or summary_df.empty:
        st.markdown(no_data("🎯", "No Budget Data", "Drop `daily_summary.csv` into `./data/`"), unsafe_allow_html=True)
        return


    df = summary_df.copy()
    meta = {"date", "total_spend", "running_balance", "rolling_7d_spend", "rolling_30d_spend"}
    cat_cols = [c for c in df.columns
                if c not in meta
                and pd.api.types.is_numeric_dtype(df[c])
                and df[c].sum() > 0]

    if not cat_cols:
        st.warning("No category columns detected in `daily_summary.csv`.")
        return

    days = len(df) if len(df) > 0 else 30
    actual_monthly = {cat: (df[cat].sum() / days * 30.4) for cat in cat_cols}
    default_targets = {"Food": 1500, "Hardware": 2000, "Software": 1200, "Rent": 2500, "Misc": 1000}
    cat_icons = {"Food": "🍔", "Software": "💻", "Hardware": "🖥️", "Rent": "🏠", "Misc": "📦"}
    sym = get_currency_symbol()

    # ── Budget sliders ──────────────────────────────────────────────────────────
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(section_header("Set Monthly Budget Targets", "🎛️"), unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:0.82rem;color:{SLATE};margin-bottom:1rem;">'
        'Drag sliders to set your monthly target per category. '
        'Spend is normalised to a 30-day equivalent from your tracking period.</p>',
        unsafe_allow_html=True,
    )
    budgets = {}
    ncols = min(3, len(cat_cols)) if cat_cols else 1
    slider_cols = st.columns(ncols)
    for i, cat in enumerate(cat_cols):
        icon = cat_icons.get(cat, "📌")
        with slider_cols[i % ncols]:
            budgets[cat] = st.slider(
                f"{icon} {cat}",
                0, 10000, default_targets.get(cat, 1500), 50,
                key=f"budget_{cat}",
            )
    st.markdown("</div>", unsafe_allow_html=True)

    over_budget = [(c, actual_monthly[c], budgets[c]) for c in cat_cols if actual_monthly.get(c, 0) > budgets[c]]

    # ── Over-budget alerts ──────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    if over_budget:
        with st.container(border=True):
            st.markdown(section_header(f"Over-Budget Categories ({len(over_budget)})", "⚠️"), unsafe_allow_html=True)
            for cat, actual, target in over_budget:
                icon = cat_icons.get(cat, "📌")
                overage = actual - target
                pct = int((actual / target) * 100) if target > 0 else 0
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;padding:0.6rem 0;border-bottom:1px solid rgba(224,112,112,0.12);">
                    <div style="width:36px;height:36px;border-radius:10px;background:rgba(224,112,112,0.15);display:flex;align-items:center;justify-content:center;">{icon}</div>
                    <div style="flex:1;">
                        <div style="font-weight:600;color:{ONYX};">{cat}</div>
                        <div style="font-size:0.72rem;color:{SLATE};">Monthly avg: {fmt_curr(actual)} &nbsp;&middot;&nbsp; Budget: {fmt_curr(target)}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-weight:700;color:{DANGER};">+{fmt_curr(overage)} over</div>
                        <div style="font-size:0.72rem;color:{DANGER};">{pct}% of budget used</div>
                    </div>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="glass-card" style="border-color:rgba(91,184,150,0.4);background:rgba(91,184,150,0.04);text-align:center;padding:1.4rem;">
            <div style="font-size:1.8rem;margin-bottom:0.3rem;">✅</div>
            <div style="font-weight:600;color:{SUCCESS};font-size:1rem;">All categories within budget!</div>
            <div style="font-size:0.8rem;color:{SLATE};margin-top:0.25rem;">Great financial discipline.</div>
        </div>""", unsafe_allow_html=True)

    # ── Donut + progress bars ───────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    col_donut, col_progress = st.columns([1, 1.2], gap="large")

    with col_donut:
        with st.container(border=True):
            st.markdown(section_header("Monthly Spend Allocation", "🍩"), unsafe_allow_html=True)
            if PLOTLY_AVAILABLE:
                palette = [CANDY_BLUE, ORCHID, SUCCESS, WARNING_CLR, DANGER, DEEP_BLUE]
                donut_vals  = [actual_monthly[c] for c in cat_cols]
                total_spend = sum(donut_vals)
                fig_donut = go.Figure(go.Pie(
                    labels=cat_cols, values=donut_vals, hole=0.58,
                    marker=dict(colors=palette[:len(cat_cols)]),
                    textfont=dict(family="Inter", size=11),
                    hovertemplate=f"<b>%{{label}}</b><br>{sym}%{{value:,.0f}}/mo<br>%{{percent}}<extra></extra>",
                ))
                fig_donut.update_layout(
                    height=270, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
                    legend=dict(font=dict(size=11, family="Inter"), orientation="v"),
                    annotations=[dict(
                        text=f"<b>{fmt_curr(total_spend)}</b><br>/mo",
                        x=0.5, y=0.5, showarrow=False, font=dict(size=13, family="Inter", color=ONYX),
                    )],
                )
                st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    with col_progress:
        with st.container(border=True):
            st.markdown(section_header("Budget vs. Actual (monthly avg)", "📊"), unsafe_allow_html=True)
            for cat in cat_cols:
                actual = actual_monthly.get(cat, 0)
                target = budgets[cat]
                pct    = min(100, int((actual / target) * 100)) if target > 0 else 0
                icon   = cat_icons.get(cat, "📌")
                over   = actual > target
                bar_color = DANGER if over else SUCCESS
                status    = f"+{fmt_curr(actual - target)} over" if over else f"{fmt_curr(target - actual)} remaining"
                st.markdown(f"""
                <div style="margin-bottom:1rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
                        <span style="font-weight:500;font-size:0.85rem;">{icon} {cat}</span>
                        <span style="font-size:0.74rem;color:{DANGER if over else SUCCESS};font-weight:600;">{status}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:{SLATE};margin-bottom:4px;">
                        <span>Spent: {fmt_curr(actual)}/mo</span><span>Budget: {fmt_curr(target)}/mo</span>
                    </div>
                    <div style="background:rgba(178,213,229,0.2);border-radius:6px;height:8px;overflow:hidden;">
                        <div style="width:{pct}%;background:{bar_color};height:100%;border-radius:6px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

def render_view_settings(summary_df):
    curr_sym_idx = ["$", "€", "£", "₹"].index(st.session_state.get("currency_symbol", "$")) if st.session_state.get("currency_symbol", "$") in ["$", "€", "£", "₹"] else 0
    curr_buffer  = int(st.session_state.get("safety_buffer", 1000.0))

    col_s1, col_s2 = st.columns([1, 1], gap="large")

    with col_s1:
        with st.container(border=True):
            st.markdown('<div class="settings-section-title">📊 Display Preferences</div>', unsafe_allow_html=True)
            new_curr = st.selectbox(
                "Currency Symbol", ["$", "€", "£", "₹"],
                index=curr_sym_idx,
                help="Symbol prepended to all monetary values across the dashboard.",
                key="settings_curr_sym"
            )
            st.selectbox("Date Format", ["MMM DD, YYYY", "DD/MM/YYYY", "YYYY-MM-DD"], disabled=True)
            st.selectbox("Fiscal Year Start", ["January", "April", "July", "October"], disabled=True)
            st.toggle("Dark Mode", value=False, disabled=True)

    with col_s2:
        with st.container(border=True):
            st.markdown('<div class="settings-section-title">🛡️ Risk & Alerts</div>', unsafe_allow_html=True)
            new_buffer = st.number_input(
                f"Safety Buffer ({new_curr})",
                value=curr_buffer, min_value=0, max_value=50000, step=500,
                help="Minimum balance threshold used to compute risk scores and forecast alerts.",
                key="settings_safety_buffer"
            )
            st.slider("Anomaly Sensitivity", min_value=0, max_value=100, value=70, disabled=True)
            st.selectbox("Alert Method", ["Dashboard Only", "Email", "Slack"], disabled=True)

    st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)
    col_s3, col_s4 = st.columns([1, 1], gap="large")

    with col_s3:
        with st.container(border=True):
            st.markdown('<div class="settings-section-title">🔄 Data Pipeline</div>', unsafe_allow_html=True)
            st.text_input("Data Directory", value="./data/", disabled=True)
            st.number_input("Cache TTL (seconds)", value=60, disabled=True)

    with col_s4:
        with st.container(border=True):
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

    st.markdown("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
    bcol1, bcol2, _ = st.columns([0.25, 0.28, 0.47])
    with bcol1:
        if st.button("💾  Save Settings", use_container_width=True, type="primary"):
            st.session_state["currency_symbol"] = new_curr
            st.session_state["safety_buffer"]   = float(new_buffer)
            st.toast("✅ Settings saved successfully! Currency & Risk Score updated.", icon="✅")
            st.rerun()

    with bcol2:
        if st.button("🔄  Reset to Defaults", use_container_width=True):
            st.session_state["currency_symbol"] = "$"
            st.session_state["safety_buffer"]   = 1000.0
            st.toast("🔄 Settings reset to defaults ($ / $1,000 buffer).", icon="🔄")
            st.rerun()

    # ── Add Transaction Manually ─────────────────────────────────────────────
    st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="settings-section-title">➕ Add Transaction Manually</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.78rem;color:#8FA8B8;margin-bottom:0.9rem;padding:0.5rem 0.8rem;'
            'background:rgba(240,160,75,0.10);border:1px solid rgba(240,160,75,0.30);border-radius:8px;">'
            '⚠️ <b>Session-only</b> — added transactions are held in memory and reset on page refresh, '
            'consistent with other session settings. They will NOT be written to disk.</div>',
            unsafe_allow_html=True
        )

        # Derive categories from loaded data (mirrors Simulator logic — no duplication)
        _meta_cols = {"date", "total_spend", "running_balance", "rolling_7d_spend", "rolling_30d_spend"}
        if summary_df is not None and not summary_df.empty:
            _cat_cols = [
                c for c in summary_df.columns
                if c not in _meta_cols
                and pd.api.types.is_numeric_dtype(summary_df[c])
                and summary_df[c].sum() > 0
            ]
        else:
            _cat_cols = []
        _all_cats = _cat_cols if _cat_cols else ["Food", "Software", "Hardware", "Rent", "Travel", "Utilities", "Entertainment", "Misc"]

        import datetime
        tf_col1, tf_col2 = st.columns([1, 1], gap="medium")
        with tf_col1:
            txn_date = st.date_input(
                "Date", value=datetime.date.today(),
                key="manual_txn_date",
                help="Date of the transaction"
            )
            txn_merchant = st.text_input(
                "Merchant / Description",
                placeholder="e.g. Amazon, Starbucks",
                key="manual_txn_merchant"
            )
        with tf_col2:
            txn_category = st.selectbox(
                "Category", _all_cats,
                key="manual_txn_category",
                help="Category column the spend will be added to"
            )
            txn_amount = st.number_input(
                f"Amount ({get_currency_symbol()})",
                min_value=0.01, value=50.0, step=1.0,
                key="manual_txn_amount",
                help="Positive value = expense / spend"
            )

        if st.button("➕ Add Transaction", type="primary", key="manual_txn_submit"):
            if not txn_merchant.strip():
                st.warning("Please enter a merchant name.")
            else:
                if "manual_txns" not in st.session_state:
                    st.session_state["manual_txns"] = []
                st.session_state["manual_txns"].append({
                    "date":     str(txn_date),
                    "merchant": txn_merchant.strip(),
                    "category": txn_category,
                    "amount":   float(txn_amount),
                })
                st.toast(f"✅ {txn_merchant.strip()} ({get_currency_symbol()}{txn_amount:,.2f}) added to session.", icon="✅")
                st.rerun()

        # Show session transactions table if any exist
        _manual_txns = st.session_state.get("manual_txns", [])
        if _manual_txns:
            st.markdown(
                f'<div style="font-size:0.76rem;color:#6FA8C0;font-weight:600;margin-top:0.8rem;">'
                f'📋 {len(_manual_txns)} session transaction(s) added this session:</div>',
                unsafe_allow_html=True
            )
            _txn_df = pd.DataFrame(_manual_txns)[["date", "merchant", "category", "amount"]]
            _txn_df.columns = ["Date", "Merchant", "Category", f"Amount ({get_currency_symbol()})"]
            st.dataframe(_txn_df, use_container_width=True, hide_index=True)
            if st.button("🗑️  Clear Session Transactions", key="manual_txn_clear"):
                st.session_state["manual_txns"] = []
                st.toast("🗑️ Session transactions cleared.", icon="🗑️")
                st.rerun()

    # ── Upload Transaction CSV ───────────────────────────────────────────────
    st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="settings-section-title">📂 Upload Transaction CSV</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.78rem;color:#8FA8B8;margin-bottom:0.9rem;padding:0.5rem 0.8rem;'
            'background:rgba(240,160,75,0.10);border:1px solid rgba(240,160,75,0.30);border-radius:8px;">'
            '⚠️ <b>Session-only</b> — uploaded transactions are held in memory and reset on page refresh, '
            'consistent with manual entry. They will NOT be written to disk.</div>',
            unsafe_allow_html=True
        )

        # Schema hint for users
        st.markdown(
            '<div style="font-size:0.76rem;color:#8FA8B8;margin-bottom:0.8rem;">'
            '📋 <b>Required columns:</b> '
            '<code>date</code>, <code>merchant</code>, <code>category</code>, '
            '<code>amount</code>, <code>account_balance_after</code>'
            '</div>',
            unsafe_allow_html=True
        )

        _REQUIRED_COLS = {"date", "merchant", "category", "amount", "account_balance_after"}

        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            key="csv_upload",
            help="CSV must contain columns: date, merchant, category, amount, account_balance_after",
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            try:
                _upload_df = pd.read_csv(uploaded_file)

                # ── Column validation ────────────────────────────────────────
                _missing = _REQUIRED_COLS - set(_upload_df.columns.str.strip().str.lower())
                if _missing:
                    st.error(
                        f"❌ **Schema mismatch** — the uploaded CSV is missing "
                        f"{'column' if len(_missing) == 1 else 'columns'}: "
                        f"`{'`, `'.join(sorted(_missing))}`\n\n"
                        f"Please check your file and ensure all required columns are present."
                    )
                else:
                    # Normalise column names to lowercase-stripped
                    _upload_df.columns = _upload_df.columns.str.strip().str.lower()

                    # Preview the data before importing
                    st.markdown(
                        f'<div style="font-size:0.76rem;color:#6FA8C0;font-weight:600;margin-bottom:0.4rem;">'
                        f'👁️ Preview — {len(_upload_df)} row(s) detected:</div>',
                        unsafe_allow_html=True
                    )
                    st.dataframe(
                        _upload_df[["date", "merchant", "category", "amount", "account_balance_after"]].head(10),
                        use_container_width=True,
                        hide_index=True,
                    )
                    if len(_upload_df) > 10:
                        st.caption(f"Showing first 10 of {len(_upload_df)} rows.")

                    # ── Import button ────────────────────────────────────────
                    if st.button("📥 Import into Session", type="primary", key="csv_import_btn"):
                        if "manual_txns" not in st.session_state:
                            st.session_state["manual_txns"] = []

                        _imported = 0
                        _skipped  = 0
                        for _, _row in _upload_df.iterrows():
                            try:
                                # Reuse the exact same dict schema as manual entry
                                st.session_state["manual_txns"].append({
                                    "date":     str(_row["date"]).strip(),
                                    "merchant": str(_row["merchant"]).strip(),
                                    "category": str(_row["category"]).strip(),
                                    "amount":   float(_row["amount"]),
                                })
                                _imported += 1
                            except (ValueError, KeyError):
                                _skipped += 1

                        _msg = f"✅ {_imported} transaction(s) imported into session."
                        if _skipped:
                            _msg += f" ({_skipped} row(s) skipped due to invalid values.)"
                        st.toast(_msg, icon="✅")
                        st.rerun()

            except Exception as _e:
                st.error(
                    f"❌ **Could not read the file**: {_e}\n\n"
                    "Please ensure it is a valid UTF-8 encoded CSV file."
                )


# ─────────────────────────────────────────────────────────────────────────────
# PROTOTYPE: SCENARIO SIMULATOR  (NEW)
# ─────────────────────────────────────────────────────────────────────────────

def render_view_simulator(summary_df, forecast_df):
    col_sliders, col_chart = st.columns([1, 1.8], gap="large")
    sym = get_currency_symbol()

    with col_sliders:
        with st.container(border=True):
            st.markdown(section_header("Adjust Assumptions", "🎛️"), unsafe_allow_html=True)

            income_delta = st.slider(
                f"💰 Monthly Income Change ({sym})",
                -5000, 5000, 0, 100,
                help="Positive = income boost, Negative = income cut",
                key="sim_income",
            )

            if summary_df is not None:
                meta = {"date", "total_spend", "running_balance", "rolling_7d_spend", "rolling_30d_spend"}
                cat_cols = [c for c in summary_df.columns
                            if c not in meta
                            and pd.api.types.is_numeric_dtype(summary_df[c])
                            and summary_df[c].sum() > 0]
            else:
                cat_cols = ["Food", "Software", "Rent", "Hardware", "Misc"]

            cat_icons = {"Food": "🍔", "Software": "💻", "Hardware": "🖥️", "Rent": "🏠", "Misc": "📦"}
            st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
            cat_deltas = {}
            for cat in cat_cols:
                icon = cat_icons.get(cat, "📌")
                cat_deltas[cat] = st.slider(
                    f"{icon} {cat} Change ({sym}/mo)",
                    -3000, 3000, 0, 50,
                    key=f"sim_{cat}",
                )

            total_monthly_delta = income_delta - sum(cat_deltas.values())
            daily_delta = total_monthly_delta / 30.0

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        impact_color = SUCCESS if total_monthly_delta >= 0 else DANGER
        impact_icon  = "📈" if total_monthly_delta >= 0 else "📉"
        impact_label = "Monthly Surplus" if total_monthly_delta >= 0 else "Monthly Deficit"
        with st.container(border=True):
            st.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size:0.72rem;font-weight:600;color:{SLATE};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.5rem;">Net Impact vs. Baseline</div>
                <div style="font-size:2.4rem;font-weight:700;color:{impact_color};letter-spacing:-0.03em;">{impact_icon} {fmt_curr(abs(total_monthly_delta))}</div>
                <div style="font-size:0.78rem;color:{SLATE};margin-top:0.25rem;">{impact_label}</div>
                <div style="font-size:0.70rem;color:{SLATE};margin-top:0.3rem;">&asymp; {fmt_curr(abs(daily_delta), 2)} / day</div>
            </div>""", unsafe_allow_html=True)

    with col_chart:
        with st.container(border=True):
            st.markdown(section_header("30-Day Forecast: Baseline vs. Scenario", "🔮"), unsafe_allow_html=True)

            if forecast_df is not None and not forecast_df.empty:
                fc = forecast_df.copy()
                fc["date"] = pd.to_datetime(fc["date"])
                fc = fc.sort_values("date").reset_index(drop=True)
                fc["scenario_balance"] = fc["projected_balance"] + [i * daily_delta for i in range(len(fc))]

                if PLOTLY_AVAILABLE:
                    fig = go.Figure()
                    if "upper_bound" in fc.columns and "lower_bound" in fc.columns:
                        fig.add_trace(go.Scatter(
                            x=pd.concat([fc["date"], fc["date"][::-1]]),
                            y=pd.concat([fc["upper_bound"], fc["lower_bound"][::-1]]),
                            fill="toself", fillcolor="rgba(178,213,229,0.15)",
                            line=dict(color="rgba(0,0,0,0)"),
                            name="Baseline Confidence",
                        ))
                    fig.add_trace(go.Scatter(
                        x=fc["date"], y=fc["projected_balance"],
                        mode="lines",
                        line=dict(color=CANDY_BLUE, width=2, dash="dot"),
                        name="Baseline",
                        hovertemplate=f"<b>Baseline</b><br>%{{x|%b %d}}: {sym}%{{y:,.0f}}<extra></extra>",
                    ))
                    sc_color = SUCCESS if total_monthly_delta >= 0 else DANGER
                    fig.add_trace(go.Scatter(
                        x=fc["date"], y=fc["scenario_balance"],
                        mode="lines+markers",
                        line=dict(color=sc_color, width=2.5),
                        marker=dict(size=5, color=sc_color),
                        name="Your Scenario",
                        hovertemplate=f"<b>Scenario</b><br>%{{x|%b %d}}: {sym}%{{y:,.0f}}<extra></extra>",
                    ))
                    fig.update_layout(
                        height=340, margin=dict(l=0, r=0, t=10, b=0),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(178,213,229,0.04)",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                    font=dict(size=11, family="Inter"), bgcolor="rgba(0,0,0,0)"),
                        hovermode="x unified",
                        xaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=11, color=SLATE)),
                        yaxis=dict(showgrid=True, gridcolor="rgba(178,213,229,0.20)",
                                   tickprefix=sym, tickformat=",.0f",
                                   tickfont=dict(family="Inter", size=11, color=SLATE), zeroline=False),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                baseline_end = fc["projected_balance"].iloc[-1]
                scenario_end = fc["scenario_balance"].iloc[-1]
                diff = scenario_end - baseline_end
                k1, k2, k3 = st.columns(3)
                with k1:
                    st.markdown(kpi_html("Baseline End", fmt_curr(baseline_end), "30-day projection", "flat",
                                         "📍", "rgba(178,213,229,0.25)"), unsafe_allow_html=True)
                with k2:
                    dir2 = "up" if scenario_end >= baseline_end else "down"
                    st.markdown(kpi_html("Scenario End", fmt_curr(scenario_end), "Under your assumptions", dir2,
                                         "🎯", "rgba(91,184,150,0.25)"), unsafe_allow_html=True)
                with k3:
                    dir3 = "up" if diff >= 0 else "down"
                    st.markdown(kpi_html("30-Day Δ", fmt_curr(diff), "vs. baseline", dir3,
                                         "📊", "rgba(229,189,223,0.25)"), unsafe_allow_html=True)
            else:
                st.markdown(no_data("🔮", "No Forecast Data", "Drop `forecast.csv` into `./data/`"), unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PROTOTYPE: REPORT GENERATOR  (NEW)
# ─────────────────────────────────────────────────────────────────────────────

def render_view_reports(summary_df, risk_data, forecast_df, anomalies_df):
    # ── Download row ───────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(section_header("Export & Download", "📤"), unsafe_allow_html=True)
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            if summary_df is not None:
                st.download_button(
                    "📊 Daily Summary CSV",
                    summary_df.to_csv(index=False).encode("utf-8"),
                    "cashflow_daily_summary.csv", "text/csv",
                    use_container_width=True, key="dl_summary",
                )
        with dl2:
            if anomalies_df is not None:
                st.download_button(
                    "⚠️ Anomalies CSV",
                    anomalies_df.to_csv(index=False).encode("utf-8"),
                    "cashflow_anomalies.csv", "text/csv",
                    use_container_width=True, key="dl_anomalies",
                )
        with dl3:
            frames = []
            if summary_df is not None:
                s = summary_df.copy(); s["_source"] = "daily_summary"; frames.append(s)
            if anomalies_df is not None:
                a = anomalies_df.copy(); a["_source"] = "anomaly"; frames.append(a)
            if frames:
                merged = pd.concat(frames, ignore_index=True)
                st.download_button(
                    "📦 Full Dataset CSV",
                    merged.to_csv(index=False).encode("utf-8"),
                    "cashflow_full_export.csv", "text/csv",
                    use_container_width=True, key="dl_full",
                )

    # ── Snapshot + Risk ─────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.5, 1], gap="large")

    with col_left:
        with st.container(border=True):
            st.markdown(section_header("Financial Snapshot", "📋"), unsafe_allow_html=True)
            if summary_df is not None and not summary_df.empty:
                last_bal  = summary_df["running_balance"].iloc[-1] if "running_balance" in summary_df.columns else 0
                last_date = pd.to_datetime(summary_df["date"].iloc[-1]).strftime("%B %d, %Y")
                total_sp  = summary_df["total_spend"].sum()  if "total_spend" in summary_df.columns else 0
                avg_daily = summary_df["total_spend"].mean() if "total_spend" in summary_df.columns else 0
                days      = len(summary_df)
                anom_cnt  = len(anomalies_df) if anomalies_df is not None else 0
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(kpi_html("Current Balance", f"${last_bal:,.2f}", f"As of {last_date}",
                                         "up" if last_bal >= 0 else "down", "💰", "rgba(91,184,150,0.18)"),
                                unsafe_allow_html=True)
                    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
                    st.markdown(kpi_html("Total Spend", f"${total_sp:,.0f}", f"{days} days tracked",
                                         "flat", "📊", "rgba(178,213,229,0.25)"), unsafe_allow_html=True)
                with c2:
                    st.markdown(kpi_html("Avg Daily Spend", f"${avg_daily:,.0f}", "per day",
                                         "flat", "📅", "rgba(229,189,223,0.25)"), unsafe_allow_html=True)
                    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
                    st.markdown(kpi_html("Anomalies", str(anom_cnt), "Flagged transactions",
                                         "down" if anom_cnt > 0 else "flat", "⚠️", "rgba(240,160,75,0.18)"),
                                unsafe_allow_html=True)
            else:
                st.markdown(no_data("📊", "No Data", "No daily summary available."), unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(section_header("30-Day Forecast Summary", "🔮"), unsafe_allow_html=True)
            if forecast_df is not None and not forecast_df.empty:
                fc_disp = forecast_df.copy()
                fc_disp["date"] = pd.to_datetime(fc_disp["date"]).dt.strftime("%b %d, %Y")
                fc_disp = fc_disp.rename(columns={
                    "projected_balance": "Projected ($)",
                    "lower_bound": "Lower ($)",
                    "upper_bound": "Upper ($)",
                    "date": "Date",
                })
                st.dataframe(fc_disp, use_container_width=True, hide_index=True)
            else:
                st.markdown(no_data("🔮", "No Forecast", "No forecast.csv found."), unsafe_allow_html=True)

    with col_right:
        with st.container(border=True):
            st.markdown(section_header("Risk Assessment", "🎯"), unsafe_allow_html=True)
            if risk_data and PLOTLY_AVAILABLE:
                score = risk_data.get("score", 0)
                expl  = risk_data.get("explanation", "")
                badge_cls = "low" if score < 40 else ("medium" if score < 70 else "high")
                badge_txt = "Low Risk" if score < 40 else ("Medium Risk" if score < 70 else "High Risk")
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=score,
                    gauge=dict(
                        axis=dict(range=[0, 100], tickwidth=1, tickcolor="rgba(0,0,0,0.2)"),
                        bar=dict(color=CANDY_BLUE, thickness=0.25),
                        bgcolor="rgba(0,0,0,0)", borderwidth=0,
                        steps=[
                            dict(range=[0, 40],  color="rgba(91,184,150,0.12)"),
                            dict(range=[40, 70], color="rgba(240,160,75,0.12)"),
                            dict(range=[70, 100], color="rgba(224,112,112,0.12)"),
                        ],
                    ),
                    number=dict(font=dict(size=38, color=ONYX, family="Inter")),
                ))
                fig_g.update_layout(
                    height=180, margin=dict(l=20, r=20, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
                )
                st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})
                st.markdown(f'<div style="text-align:center;"><span class="risk-badge {badge_cls}">{badge_txt}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.75rem;color:{SLATE};text-align:center;margin-top:0.7rem;line-height:1.5;">{expl}</div>', unsafe_allow_html=True)
            else:
                st.markdown(no_data("🎯", "No Risk Score", "No risk_score.json found."), unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(section_header("Flagged Anomalies", "⚠️"), unsafe_allow_html=True)
            if anomalies_df is not None and not anomalies_df.empty:
                st.dataframe(anomalies_df, use_container_width=True, hide_index=True)
            else:
                st.markdown(no_data("✅", "No Anomalies", "No flagged transactions found."), unsafe_allow_html=True)

    # ── HTML Report Generator ────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(section_header("HTML Report Generator", "📄"), unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.82rem;color:#8FA8B8;margin-bottom:1rem;">Generate a printable, standalone HTML report with all your financial data.</p>',
                    unsafe_allow_html=True)
        if st.button("⚡ Generate HTML Report", type="primary", key="gen_html_btn"):
            bal       = summary_df["running_balance"].iloc[-1] if summary_df is not None and "running_balance" in summary_df.columns else 0
            date_str  = pd.to_datetime(summary_df["date"].iloc[-1]).strftime("%B %d, %Y") if summary_df is not None else "N/A"
            score_val = risk_data.get("score", "N/A") if risk_data else "N/A"
            expl_val  = risk_data.get("explanation", "") if risk_data else ""
            anom_cnt  = len(anomalies_df) if anomalies_df is not None else 0
            anom_rows_html = ""
            if anomalies_df is not None and not anomalies_df.empty:
                for _, r in anomalies_df.iterrows():
                    anom_rows_html += (
                        f"<tr><td>{r.get('date','')}</td>"
                        f"<td>{r.get('merchant','')}</td>"
                        f"<td>{r.get('category','')}</td>"
                        f"<td>${abs(r.get('amount', 0)):,.2f}</td>"
                        f"<td>{r.get('severity','')}</td></tr>"
                    )
            gen_time = pd.Timestamp.now().strftime("%B %d, %Y %H:%M")
            html_out = (
                "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
                "<meta charset='UTF-8'>\n<title>CashFlow Radar Report</title>\n"
                "<style>\n"
                "  body{font-family:'Segoe UI',sans-serif;background:#EAF3F9;color:#1D1D1D;margin:0;padding:2rem;}\n"
                "  h1{font-size:2rem;font-weight:700;margin-bottom:0.2rem;}\n"
                "  .sub{color:#8FA8B8;font-size:0.85rem;margin-bottom:2rem;}\n"
                "  .card{background:rgba(255,255,255,0.92);border:1.5px solid rgba(178,213,229,0.5);border-radius:16px;padding:1.5rem;margin-bottom:1.5rem;}\n"
                "  .kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1rem;}\n"
                "  .kpi{background:rgba(178,213,229,0.12);border-radius:12px;padding:1rem;}\n"
                "  .kpi-l{font-size:0.68rem;font-weight:600;color:#8FA8B8;text-transform:uppercase;letter-spacing:0.05em;}\n"
                "  .kpi-v{font-size:1.4rem;font-weight:700;margin-top:0.25rem;}\n"
                "  table{width:100%;border-collapse:collapse;font-size:0.85rem;margin-top:0.75rem;}\n"
                "  th{background:rgba(178,213,229,0.2);padding:0.55rem 1rem;text-align:left;font-size:0.72rem;font-weight:600;text-transform:uppercase;color:#8FA8B8;}\n"
                "  td{padding:0.55rem 1rem;border-bottom:1px solid rgba(178,213,229,0.18);}\n"
                "  .footer{text-align:center;font-size:0.72rem;color:#8FA8B8;margin-top:2rem;border-top:1px solid rgba(178,213,229,0.2);padding-top:1rem;}\n"
                "</style>\n</head>\n<body>\n"
                f"<h1>&#128225; CashFlow Radar &#8212; Financial Report</h1>\n"
                f"<div class='sub'>Generated {gen_time} &nbsp;&middot;&nbsp; GenAI APAC Hackathon</div>\n"
                "<div class='card'>\n"
                "  <h2 style='font-size:1.1rem;margin:0 0 0.5rem;'>Financial Snapshot</h2>\n"
                "  <div class='kpi-grid'>\n"
                f"    <div class='kpi'><div class='kpi-l'>Balance</div><div class='kpi-v'>${bal:,.2f}</div><div style='font-size:0.72rem;color:#8FA8B8;'>{date_str}</div></div>\n"
                f"    <div class='kpi'><div class='kpi-l'>Risk Score</div><div class='kpi-v'>{score_val}/100</div></div>\n"
                f"    <div class='kpi'><div class='kpi-l'>Anomalies</div><div class='kpi-v'>{anom_cnt}</div></div>\n"
                "  </div>\n"
                f"  <p style='font-size:0.84rem;color:#8FA8B8;margin-top:1rem;'>{expl_val}</p>\n"
                "</div>\n"
                "<div class='card'>\n"
                "  <h2 style='font-size:1.1rem;margin:0;'>Flagged Anomalies</h2>\n"
                "  <table><tr><th>Date</th><th>Merchant</th><th>Category</th><th>Amount</th><th>Severity</th></tr>\n"
                + (anom_rows_html if anom_rows_html else "  <tr><td colspan='5' style='text-align:center;color:#8FA8B8;'>No anomalies detected</td></tr>\n")
                + "  </table>\n</div>\n"
                "<div class='footer'>&#128225; CashFlow Radar &nbsp;&middot;&nbsp; GenAI APAC Hackathon &nbsp;&middot;&nbsp; RAPIDS cuDF &amp; cuML</div>\n"
                "</body>\n</html>"
            )
            st.download_button(
                "📥 Download HTML Report",
                html_out.encode("utf-8"),
                "cashflow_radar_report.html",
                "text/html",
                key="dl_html_btn",
            )
            st.success("✅ HTML report ready! Click above to download.")


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
        "Simulator":    ("Cash-Flow Scenario Simulator", "CashFlow Radar › Simulator",
                         "Adjust income and spending assumptions to see how your 30-day projected balance changes."),
        "Reports":      ("Financial Report",             "CashFlow Radar › Reports",
                         "Export a full financial snapshot as CSV or a styled HTML report."),
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

    # ── Merge any session-added transactions into summary_df before dispatch ──
    # This ensures compute_dynamic_risk(), render_kpi_strip(), all charts, etc.
    # automatically reflect new rows without duplicating any calculation logic.
    manual_txns = st.session_state.get("manual_txns", [])
    if manual_txns and summary_df is not None:
        _extra_rows = []
        for txn in manual_txns:
            row = {c: 0.0 for c in summary_df.columns}
            row["date"] = txn["date"]
            if txn["category"] in summary_df.columns:
                row[txn["category"]] = float(txn["amount"])
            if "total_spend" in summary_df.columns:
                row["total_spend"] = float(txn["amount"])
            if "running_balance" in summary_df.columns:
                last_bal = float(summary_df["running_balance"].dropna().iloc[-1])
                row["running_balance"] = last_bal - float(txn["amount"])
            _extra_rows.append(row)
        if _extra_rows:
            summary_df = pd.concat([summary_df, pd.DataFrame(_extra_rows)], ignore_index=True)

    # ── View dispatch ──
    if view == "Dashboard":

        render_kpi_strip(summary_df, risk_data)
        st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

        # 1. MONEY WEATHER — fastest-read card, top of dashboard
        render_money_weather(risk_data, forecast_df)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

        render_hero_and_risk(summary_df, risk_data, forecast_df)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

        # 2 & 3. CASH FLOW STORY + HIDDEN MONEY FINDER — side by side
        col_story, col_money = st.columns([1.4, 1], gap="large")
        with col_story:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            render_cash_flow_story(summary_df, risk_data, forecast_df)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_money:
            st.markdown('<div class="glass-card" style="height:100%;">', unsafe_allow_html=True)
            render_hidden_money_finder(anomalies_df)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

        # Existing: CashFlow Insight
        render_insight_panel(summary_df, risk_data, forecast_df, anomalies_df)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

        # Existing: Forecast chart + Anomaly alerts
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

        # Existing: Spend breakdown + Benchmark
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

    elif view == "Simulator":
        render_view_simulator(summary_df, forecast_df)

    elif view == "Reports":
        render_view_reports(summary_df, risk_data, forecast_df, anomalies_df)

    elif view == "Settings":
        render_view_settings(summary_df)

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
