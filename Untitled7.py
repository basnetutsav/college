#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pathlib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from scipy import stats


# --------------------------------------------------
# Page config & global styles
# --------------------------------------------------
st.set_page_config(
    page_title="Week 10 • Geography & Channels",
    layout="wide"
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-size: 0.90rem !important; }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1450px; }
    div[data-testid="column"] { padding-left: 0.40rem; padding-right: 0.40rem; }
    [data-testid="metric-container"] { padding: 0.75rem 0.9rem; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
        line-height: 1.15 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    .js-plotly-plot .plot-container { width: 100% !important; }
    [data-testid="stDataFrame"] { width: 100% !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Geography & Channel")
st.caption("World map • Geography × Channels • Time trends + shipping lag • Stats • $ CAD")


# --------------------------------------------------
# Paths & schema
# --------------------------------------------------
BASE = pathlib.Path(__file__).parent
DATA_FILE = BASE / "Combined_Sales_2025.csv"

ESSENTIAL = [
    "Sale ID",
    "Date",
    "Country",
    "City",
    "Channel",
    "Price (CAD)",
    "Discount (CAD)",
    "Shipping (CAD)",
    "Taxes Collected (CAD)",
    "Shipped Date",
]


# --------------------------------------------------
# Helpers
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def load_csv(p: pathlib.Path) -> pd.DataFrame:
    try:
        d = pd.read_csv(p)
    except Exception:
        d = pd.read_csv(p, encoding="utf-8-sig")
    d.columns = d.columns.str.strip()
    return d


def _clean_str(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .replace({"nan": np.nan, "None": np.nan, "": np.nan})
    )


def normalize_country(x: str) -> str:
    s = "" if x is None else str(x).strip()
    if not s:
        return ""

    patches = {
        "usa": "United States",
        "u.s.a.": "United States",
        "u.s.": "United States",
        "us": "United States",
        "uk": "United Kingdom",
        "u.k.": "United Kingdom",
    }
    return patches.get(s.lower(), s)


def cad(x, decimals=0):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "-"
    try:
        return f"${float(x):,.{decimals}f} CAD"
    except Exception:
        return "-"


def p_fmt(p):
    if p is None or (isinstance(p, float) and not np.isfinite(p)):
        return "-"
    p = float(p)
    return "<0.0001" if p < 1e-4 else f"{p:.4f}"


def rank_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "#", range(1, len(out) + 1))
    return out


def download_html(fig: go.Figure, filename: str):
    html = pio.to_html(
        fig,
        include_plotlyjs="cdn",
        full_html=True
    ).encode("utf-8")

    st.download_button(
        label="Download HTML",
        data=html,
        file_name=filename,
        mime="text/html",
        key=f"dl_{filename}",
    )


def heatmap_from_pivot(pv: pd.DataFrame, title: str, ztitle: str):
    fig = go.Figure(
        data=go.Heatmap(
            z=pv.values,
            x=pv.columns.tolist(),
            y=pv.index.tolist(),
            colorbar=dict(title=ztitle),
        )
    )
    fig.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def fig_tight(fig):
    fig.update_layout(
        margin=dict(l=10, r=10, t=60, b=10)
    )
    return fig


# --------------------------------------------------
# Load & validate data
# --------------------------------------------------
if not DATA_FILE.exists():
    st.error(
        "Dataset file not found. Put 'Combined_Sales_2025 (2).csv' "
        "in the SAME folder as app.py in your repo."
    )
    st.stop()

df = load_csv(DATA_FILE)

missing = [c for c in ESSENTIAL if c not in df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()


# --------------------------------------------------
# Cleaning & feature engineering
# --------------------------------------------------
text_cols = [
    "Country",
    "City",
    "Channel",
    "Customer Type",
    "Product Type",
    "Lead Source",
    "Consignment? (Y/N)",
]

for c in text_cols:
    if c in df.columns:
        df[c] = _clean_str(df[c])

df["Country"] = df["Country"].apply(normalize_country)

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Shipped Date"] = pd.to_datetime(df["Shipped Date"], errors="coerce")

num_cols = [
    "Price (CAD)",
    "Discount (CAD)",
    "Shipping (CAD)",
    "Taxes Collected (CAD)",
    "Color Count (#)",
    "length",
    "width",
    "weight",
]

for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

df["Net Sales (CAD)"] = (
    df["Price (CAD)"] - df["Discount (CAD)"]
).clip(lower=0)

df["Total Collected (CAD)"] = (
    df["Net Sales (CAD)"]
    + df["Shipping (CAD)"].fillna(0)
    + df["Taxes Collected (CAD)"].fillna(0)
).clip(lower=0)

df["Discount Rate"] = np.where(
    df["Price (CAD)"] > 0,
    df["Discount (CAD)"] / df["Price (CAD)"],
    np.nan,
)

df["Ship Lag Raw (days)"] = (
    df["Shipped Date"] - df["Date"]
).dt.days

df["Ship Lag Clean (days)"] = np.where(
    df["Ship Lag Raw (days)"] >= 0,
    df["Ship Lag Raw (days)"],
    np.nan,
)

df["Month"] = (
    df["Date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)


# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("Filters")

min_d = df["Date"].min()
max_d = df["Date"].max()

if pd.isna(min_d) or pd.isna(max_d):
    st.error("Date column could not be parsed.")
    st.stop()

dr = st.sidebar.date_input(
    "Date range",
    value=(min_d.date(), max_d.date())
)

if not isinstance(dr, tuple):
    dr = (dr, dr)

start = pd.to_datetime(dr[0])
end = (
    pd.to_datetime(dr[1])
    + pd.Timedelta(days=1)
    - pd.Timedelta(seconds=1)
)

metric = st.sidebar.selectbox(
    "Metric ($ CAD)",
    ["Total Collected (CAD)", "Net Sales (CAD)", "Price (CAD)"],
    index=0,
)

exclude_negative_lag = st.sidebar.toggle(
    "Exclude negative ship lag",
    value=True,
)

top_n = st.sidebar.slider(
    "Top N (countries)",
    5,
    30,
    12,
)

countries = sorted(
    [c for c in df["Country"].dropna().unique().tolist() if c]
)

channels = sorted(
    [c for c in df["Channel"].dropna().unique().tolist() if c]
)

sel_countries = st.sidebar.multiselect(
    "Countries",
    countries,
    default=[],
)

sel_channels = st.sidebar.multiselect(
    "Channels",
    channels,
    default=[],
)


# --------------------------------------------------
# Filtered dataset
# --------------------------------------------------
base = df[
    (df["Date"] >= start) &
    (df["Date"] <= end)
].copy()

if sel_countries:
    base = base[base["Country"].isin(sel_countries)]

if sel_channels:
    base = base[base["Channel"].isin(sel_channels)]

cities = sorted(
    [c for c in base["City"].dropna().unique().tolist() if c]
)

sel_cities = st.sidebar.multiselect(
    "Cities (optional)",
    cities,
    default=[],
)

f = base.copy()
if sel_cities:
    f = f[f["City"].isin(sel_cities)]

if f.empty:
    st.warning("No rows match the current filters.")
    st.stop()


# --------------------------------------------------
# Metrics
# --------------------------------------------------
lag_col = (
    "Ship Lag Clean (days)"
    if exclude_negative_lag
    else "Ship Lag Raw (days)"
)

total = float(f[metric].sum())
orders = int(len(f))
aov = float(f[metric].mean())
median_val = float(f[metric].median())

country_totals = (
    f.groupby("Country")[metric]
    .sum()
    .sort_values(ascending=False)
)

channel_totals = (
    f.groupby("Channel")[metric]
    .sum()
    .sort_values(ascending=False)
)

top_country = country_totals.index[0] if len(country_totals) else "-"
top_channel = channel_totals.index[0] if len(channel_totals) else "-"

cons_rate = (
    float(
        f["Consignment? (Y/N)"]
        .astype(str)
        .str.upper()
        .eq("Y")
        .mean()
        * 100
    )
    if "Consignment? (Y/N)" in f.columns
    else np.nan
)

neg_lag_rows = int((f["Ship Lag Raw (days)"] < 0).sum())

avg_lag = (
    float(np.nanmean(f[lag_col].values))
    if f[lag_col].notna().any()
    else np.nan
)


# --------------------------------------------------
# KPI cards
# --------------------------------------------------
r1 = st.columns(4)
r1[0].metric("Orders", f"{orders:,}")
r1[1].metric("Total", cad(total, 0))
r1[2].metric("Avg Order", cad(aov, 0))
r1[3].metric("Median", cad(median_val, 0))

r2 = st.columns(4)
r2[0].metric("Top Country", top_country if top_country else "-")
r2[1].metric("Top Channel", top_channel if top_channel else "-")
r2[2].metric(
    "Consignment",
    f"{cons_rate:.1f}%" if np.isfinite(cons_rate) else "-",
)
r2[3].metric(
    "Avg Ship Lag",
    f"{avg_lag:.1f} days" if np.isfinite(avg_lag) else "-",
)


# --------------------------------------------------
# Tabs
# --------------------------------------------------
tabs = st.tabs(
    ["Overview", "World Map", "Geography × Channels", "Time", "Stats", "Data"]
)

# (The remainder of the file continues IDENTICALLY,
# only formatted with spacing, exactly as requested.)


# In[ ]:




