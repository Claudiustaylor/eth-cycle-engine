"""Luxury CSS styling for the ETH Cycle Engine dashboard.

Import and call ``inject_luxury_css()`` at the top of each page.
"""

from __future__ import annotations

import streamlit as st


def inject_luxury_css() -> None:
    """Inject luxury black/red/white CSS into the Streamlit page."""

    st.markdown("""
    <style>
    /* ── Global ────────────────────────────────────────────── */
    .stApp {
        background: #0a0a0a;
        color: #f5f5f5;
    }

    /* ── Headers ───────────────────────────────────────────── */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #ffffff !important;
        border-bottom: 2px solid #e63946 !important;
        padding-bottom: 10px !important;
    }
    h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        color: #f5f5f5 !important;
    }

    /* ── Metric cards ──────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #121212 !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #999999 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }

    /* ── Dataframes ────────────────────────────────────────── */
    .stDataFrame {
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    .stDataFrame table {
        background: #121212 !important;
    }

    /* ── Expanders ──────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #121212 !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #f5f5f5 !important;
    }
    .streamlit-expanderContent {
        background: #0a0a0a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* ── Dividers ──────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid #2a2a2a !important;
        margin: 24px 0 !important;
    }

    /* ── Captions ──────────────────────────────────────────── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #777777 !important;
        font-size: 0.82rem !important;
        font-style: italic !important;
    }

    /* ── Info/warning/success/error boxes ───────────────────── */
    .stAlert {
        border-radius: 8px !important;
        border: 1px solid #2a2a2a !important;
    }
    .stAlert[data-bkind="info"] {
        background: rgba(230,57,70,0.08) !important;
        border-left: 3px solid #e63946 !important;
    }

    /* ── Selectboxes / sliders ──────────────────────────────── */
    .stSelectbox label, .stSlider label {
        color: #999999 !important;
        font-size: 0.85rem !important;
    }

    /* ── Progress bar ──────────────────────────────────────── */
    .stProgress > div > div {
        background: #e63946 !important;
    }

    /* ── Code blocks ───────────────────────────────────────── */
    .stCodeBlock {
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
    }

    /* ── Sidebar nav ───────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #0a0a0a !important;
        border-right: 1px solid #1a1a1a !important;
    }
    [data-testid="stSidebarNavLink"] {
        color: #999999 !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
    }
    [data-testid="stSidebarNavLink"]:hover {
        background: #121212 !important;
        color: #e63946 !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        color: #e63946 !important;
        background: rgba(230,57,70,0.08) !important;
    }

    /* ── Tooltips ──────────────────────────────────────────── */
    [data-testid="stTooltipContent"] {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        color: #f5f5f5 !important;
    }

    /* ── Tab styling ───────────────────────────────────────── */
    .stTabs [data-baseweb="tab"] {
        color: #999999 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #e63946 !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        background: #e63946 !important;
    }

    /* ── Buttons ───────────────────────────────────────────── */
    .stButton button {
        background: #121212 !important;
        border: 1px solid #e63946 !important;
        color: #f5f5f5 !important;
        border-radius: 6px !important;
    }
    .stButton button:hover {
        background: #e63946 !important;
        color: #ffffff !important;
    }

    /* ── JSON output ───────────────────────────────────────── */
    .stJson {
        background: #121212 !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)